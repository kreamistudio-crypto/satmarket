# Piano di Disaster Recovery — Barattolo

Data: 20 ott 2026 · Versione: 1.0 · Stato: Attivo

Il piano di disaster recovery di Barattolo descrive **come salvare una copia integra della macchina**, **come accorgersi che qualcosa è andato male**, e **come tornare a funzionare** in quattro scenari diversi, dal più veloce al più grave. Ogni procedura è testata prima di entrare in produzione.

---

## Indice

1. [Il backup: cosa è salvato e dove](#il-backup)
2. [Come riconoscere un disastro](#come-riconoscere-un-disastro)
3. [Scenari e procedure](#scenari-e-procedure)
   - [Scenario 1: Rollback automatico (il caso normale)](#scenario-1-rollback-automatico)
   - [Scenario 2: Rollback a mano (deploy rifiutato)](#scenario-2-rollback-a-mano)
   - [Scenario 3: Ripristino da backup recente (disco, database o segreti)](#scenario-3-ripristino-da-backup-recente)
   - [Scenario 4: Rebuild da zero (VPS perso, account compromesso)](#scenario-4-rebuild-da-zero)
4. [Testing e manutenzione](#testing-e-manutenzione)
5. [Contatti e avvisi](#contatti-e-avvisi)

---

## Il backup

### Cosa viene salvato

**Piano di backup — SU VPS (prima di ogni deploy):**

- Database di Barattolo (`satmarket.db`) — copia atomica fatta dall'API di SQLite (serve che il server stia girando)
- File: `backup/pre-deploy-YYYYMMDD-HHMMSS-XXXXX.db` (ultimi 5 tenuti)
- Tempo: durante il deploy (regola 3 di `deploy.sh`)
- Quando serve: per ripristinare se il codice nuovo rompe il database durante `init_db` (migrazioni)

**Piano di backup — GIORNALIERO (ogni 22:00 UTC, cifrato):**

- Database Barattolo (backup atomico SQLite)
- Database LNbits (`/opt/lnbits/data/database.sqlite3`)
- Config di sistema:
  - `config.py` (segreti: nsec, chiavi LNbits, token bot)
  - `Caddyfile` (config HTTPS)
  - Unit systemd barattolo* e lnd-ponte*
  - Crontab root
- Tor:
  - Chiave privata del servizio nascosto (.onion) — **irrecuperabile se persa**
  - Autorizzazione client Tor per il ponte verso il nodo
- LNbits:
  - `.env` (macaroon, nomi delle leve)
  - `docker-compose.yml` (versione pinnata)
  - Data (cert TLS, file del superuser)
- Buste e contenuti (blob cifrati, ma le righe di metadati)

**Quello che NON viene salvato (e si ricostruisce da git):**

- `foto/` — download dal PC di Andrea via rclone (171 MB)
- Il codice tutto (è su GitHub, tagged at ogni deploy)
- Database giornalieri se il pre-deploy copre già il caso

**Dov'è il backup:**

| Copia | Luogo | Frequenza | Cifrato | Reachable se |
|-------|-------|-----------|---------|-------------|
| Pre-deploy | VPS `/srv/barattolo/backup/pre-deploy-*.db` | Ogni deploy (~ ogni minuto se c'è codice nuovo) | No | VPS acceso |
| Giornaliero | VPS `/srv/barattolo/backup/fuori/barattolo-YYYYMMDD-HHMM.tar.gz.age` | Una volta al giorno (22:00 UTC) | Sì (age) | VPS acceso |
| **Esterno** | **Telegram (canale privato backup)** | Una volta al giorno (22:00 UTC dopo il tar) | Sì (age) | Telegram accesso |
| Specchio PC | PC di Andrea (`~/Barattolo/backup/fuori/`, pulito settimanalmente) | Sincronizzato via rclone | Sì (age) | PC di Andrea |

**Decriptazione:**

- La chiave pubblica age (che CIFRA) sta su VPS e in questo repo
- La chiave privata age (che DECIFRA) sta su carta + Bitwarden, **mai su una macchina online**
- Al ripristino: prendi il backup da Telegram, decifra offline col tuo Bitwarden

---

## Come riconoscere un disastro

### Segnali di allarme (ordine di gravità)

**1️⃣ Avviso semplice dal bot** (il deploy ha un problema)

```
⛔ Deploy rifiutato: <motivo>
↩️ Deploy annullato: <versione> non rispondeva
⏳ Deploy fermo: in attesa da X minuti
```

**→ Azione:** Leggi il journal sul VPS (`journalctl -u barattolo-deploy -n 20`), o chiedi a Claude di leggere il log.

---

**2️⃣ Niente da bot da un'ora** (il timer non gira più)

```
journalctl -u barattolo-deploy.timer --since "2 hours ago"
```

Se non c'è niente: il timer systemd è fermo, o il VPS è offline.

**→ Azione:**
- Se il VPS risponde su SSH (Andrea ha le chiavi): `systemctl status barattolo-deploy.timer`
- Se il VPS non c'è: cloud provider è down, o l'account è stato disabilitato (vedi Scenario 4)

---

**3️⃣ Avviso SOS dal bot**

```
🆘 Barattolo è GIÙ: nemmeno <versione> risponde dopo il rollback
```

Il deploy non è andato, il rollback non ha funzionato, e il mercatino non risponde.

**→ Azione immediata:** Scenario 3 (ripristino da backup recente)

---

**4️⃣ Avviso di sicurezza** (credenziali esposte, chiave compromessa)

```
⚠️ Token GitHub ruotato / chiave .onion compromessa / ...
```

**→ Azione:** Scenario 4 (rebuild da zero + rotazione chiavi)

---

**5️⃣ Tutti i backup offline** (Telegram, VPS e PC tutti down)

Il provider è collassato, la macchina è irreparabile, e non c'è nemmeno un backup dov'è.

**→ Azione:** Escalation al team, situazione emergenziale.

---

## Scenari e procedure

### Scenario 1: Rollback automatico

**Quando succede:** Il codice nuovo non risponde in `/api/salute` entro 45 secondi dal riavvio.

**Cosa fa il sistema da solo:**

1. `deploy.sh` lo vede
2. Segna il commit come bocciato in `.deploy-bocciato`
3. Torna indietro a `git reset --hard HEAD~1`
4. Riavvia il servizio
5. Aspetta che `/api/salute` risponda (altri 45 secondi)
6. Avvisa:
   ```
   ↩️ Deploy annullato: <nuovo commit> non rispondeva
   Sono tornato a <commit precedente> e il mercatino sta bene
   Il ramo `pronto` resta avanti: guarda il journal prima di riprovare
   ```

**La tua azione:** Leggi il motivo nel journal (`journalctl -u barattolo -n 50 --no-pager`, cerca i Traceback), aggiusta il codice e spingere un commit nuovo. Non spiare `pronto` di forza, aspetta che la CI lo alzi di nuovo.

**Tempo di fermo:** 90 secondi circa.

---

### Scenario 2: Rollback a mano

**Quando serve:** Il deploy è stato rifiutato dalla CI (firma mancante, non su main, storia riscritta, etc), oppure è bocciato e vuoi riprovare con `--forza`.

**La procedura (Andrea o chi ha le chiavi SSH):**

```bash
cd /srv/barattolo

# 1) Guarda dove siamo e quale commit il giudice vuole
./deploy.sh --dimmi
# Output: qui: XXXXXXX · pronto: YYYYYYY · firma richiesta

# 2) Se pronto è avanti di TROPPO e il giudice lo rifiuta, 
#    rimetti pronto sulla punta di main
git fetch origin main:refs/remotes/origin/main
git push origin origin/main:refs/heads/pronto

# 3) Forza il deploy una sola volta
./deploy.sh --forza

# 4) Guarda se è andato
journalctl -u barattolo -n 20 --no-pager | grep -E "✅|❌|↩️"
```

**Se neanche --forza lo ripristina:** vai a Scenario 3.

---

### Scenario 3: Ripristino da backup recente

**Quando serve:**

- `/api/salute` non risponde nemmeno al rollback (Scenario 1 fallito)
- Database corrotto (accedi su SSH e vedi `database disk image is malformed`)
- VPS ha il disco pieno (sai che `df -h` dice `100%` su `/`)
- Sospetti una esposizione di segreti (token, nsec, chiavi)

**Requisiti:**

- Accesso SSH al VPS (Andrea o chi ha le chiavi)
- Uno dei backup recenti:
  - `backup/pre-deploy-*.db` (sul VPS, meno di 1 ora, non cifrato)
  - `backup/fuori/barattolo-YYYYMMDD-HHMM.tar.gz.age` (sul VPS, cifrato)
  - Telegram canale backup (cifrato)
  - PC di Andrea (cifrato)
- La chiave privata age per decriptare (in Bitwarden offline)

**La procedura:**

#### Passo A: Scegli il backup

**Se il mercatino era acceso fino a 1 ora fa:**

```bash
ls -ltr /srv/barattolo/backup/pre-deploy-*.db | tail -3
# Scegli il più recente fra questi
# Esempio: backup/pre-deploy-20261020-212003-a1b2c3d4.db
```

Vai a **Passo C**.

**Se è passato più di 1 ora, o il disco è pieno:**

Scarica il backup cifrato del giorno (o del giorno prima se è passata la mezzanotte UTC):

```bash
# Via Telegram: apri il canale backup, scarica il più recente
# barattolo-20261020-2200.tar.gz.age (o simile)

# Oppure dal PC di Andrea:
# ls -ltr ~/Barattolo/backup/fuori/*.tar.gz.age | tail -3

# Copia il file sul VPS in una cartella temporanea:
# scp ~/Barattolo/backup/fuori/barattolo-20261020-2200.tar.gz.age root@46.62.162.103:/root/ripristino-temp/
```

Vai a **Passo B**.

#### Passo B: Decripta il backup

**Serve offline (sul tuo PC, non sul VPS):**

```bash
# 1) Prendi la chiave privata age dal tuo Bitwarden offline
# (nome "Barattolo — chiave age ripristino")

# 2) Crea un file temporaneo con la chiave privata
# (non la lasciare in giro)

# 3) Decripta
cd /cartella/dove/hai/scaricato
age --decrypt -i chiave-privata-age.txt barattolo-20261020-2200.tar.gz.age > barattolo-20261020-2200.tar.gz

# 4) Estrai
tar -tzf barattolo-20261020-2200.tar.gz | head -5
# Deve mostrare: satmarket.db, config.py, buste/, etc
```

Copia il tar.gz decriptato sul VPS di nuovo:

```bash
scp barattolo-20261020-2200.tar.gz root@46.62.162.103:/root/ripristino-temp/
```

Vai a **Passo C**.

#### Passo C: Stoppa il mercatino e ripristina

**Sul VPS:**

```bash
cd /srv/barattolo

# 1) Stop del servizio
systemctl stop barattolo
systemctl stop barattolo-deploy.timer

# 2) Backup del backup corrente (nel caso serva tornare indietro)
cp satmarket.db "dati/satmarket.db.backup-prima-del-ripristino-$(date +%Y%m%d-%H%M%S)"

# 3a) Se hai un pre-deploy (non cifrato):
cp backup/pre-deploy-20261020-212003-a1b2c3d4.db satmarket.db

# 3b) Se hai un tar.gz.age decriptato:
tar -xzf /root/ripristino-temp/barattolo-20261020-2200.tar.gz -C /tmp
rm -f satmarket.db
cp /tmp/satmarket.db satmarket.db
# Ripristina anche il config se era corrotto
# cp /tmp/config.py config.py   [SOLO SE il problema era il config]

# 4) Verifica che il file sia valido prima di riavviare
sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"
# Deve rispondere con un numero (di utenti), non un errore

# 5) Riavvia
systemctl start barattolo
sleep 5
systemctl status barattolo

# 6) Riprova /api/salute
curl http://127.0.0.1:8080/api/salute

# 7) Ricomincia il deploy se tutto è ok
systemctl start barattolo-deploy.timer

# 8) Pulisci il temporaneo
rm -rf /root/ripristino-temp /tmp/barattolo-* /tmp/lnbits /tmp/sistema /tmp/contenuti /tmp/buste
```

**Se tutto sta bene:** L'avviso nel bot dirà `✅ in produzione...` al deploy successivo (entro un minuto). Finito.

**Se `sqlite3` dice un errore:** Il database è ancora corrotto. Vai a **Passo D** (esternalizza il problema).

#### Passo D: Se il ripristino non funziona

Significa che TUTTI i backup locali sono corrotti, o il problema non è il database. A questo punto:

1. **Documentalo:** `journalctl -u barattolo -n 100 >> /root/problema-ripristino-$(date +%Y%m%d-%H%M%S).log`
2. **Chiedi aiuto:** Incolla il log a Claude Code nella conversazione (senza incollare il config.py)
3. **Fallback:** Vai a **Scenario 4** (rebuild da zero)

---

### Scenario 4: Rebuild da zero

**Quando serve:** Il VPS è perso (account Hetzner disabilitato, server cancellato, disco morto), oppure il ripristino da backup ha fallito su tutti i backup (corruzione totale).

**Tempo stimato:** 4-6 ore + i tempi di approvazione/deploy.

**Cosa serve:**

- Una nuova macchina Ubuntu 26.04 LTS (o la prossima versione LTS)
- Accesso root SSH
- Un backup decriptato (Telegram, PC di Andrea)
- Il token GitHub del VPS (nuovo, o lo stesso se ancora valido)
- I secret Telegram e Nostr da `config.py` (presi dal backup decriptato)
- Il dominio `barattolo.store` disponibile e puntato al nuovo IP (cambiare A record DNS)

**La procedura è in `deploy/RIPRISTINO.md`** — un documento separato e dettagliato, passo per passo, che copre:

1. Preparazione della macchina
2. Clone del repo e checkout a una versione stabile
3. Installazione delle dipendenze (Python, nginx/Caddy, systemd, age, tor, lnd, lnbits in container)
4. Posa del backup decriptato
5. Configurazione del dominio e SSL
6. Attivazione del deploy automatico
7. Verifiche finali

---

## Testing e manutenzione

### Backup — test di ripristino mensile

**Ogni 4a lunedì del mese (calendario interno):**

1. Andrea scarica il backup più recente da Telegram
2. Lo decripta offline (col Bitwarden)
3. Estrae il tar.gz in una cartella temporanea
4. Verifica che il database si apra: `sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"`
5. Verifica che il config.py sia leggibile e completo (tutti i segreti ci sono)
6. Segna il test nel log (data, hash del backup, esito) in `docs/DISASTER-RECOVERY-TESTS.md`
7. Se fallisce: apre un issue GitHub per investigare

**Frequenza:** Mensile, non salta mai (anche se il mercatino sta perfettamente).

**Motivo:** Un backup che non si ripristina è come non avere un backup. Meglio scoprirlo quando c'è tempo per aggiustare, non quando il VPS è bruciato.

---

### Rollback automatico — test mensile

**Ogni volta che c'è un codice nuovo che tocca il database (`init_db`):**

Sul PC di Andrea, in una gabbia di test:

```bash
MODALITA_COLLAUDO=True python prove.py collaudo_migrazioni
# Simula un init_db finto che rompe il database
# Verifica che il deploy rollback automaticamente
# Verifica che il journal dica ↩️ tonnato a <hash>
```

Se fallisce: non pusciare il codice su main, aggiusta prima.

---

### Plan — meeting trimestrale

**Ogni 3 mesi (calendario interno):**

1. Rileggere questo documento
2. Controllare che i percorsi (VPS, config, token) siano ancora validi
3. Controllare che il backup sia ancora 'cifrato con age (non si cambia mai)
4. Controllare che il canale Telegram backup esista ancora
5. Aggiornare le date nei titoli dei paragrafi
6. Se c'è una lezione nuova (un disastro vero, una procedura aggiustata): aggiungere qui
7. Scrivere un `AGGIORNAMENTO` in fondo a questo documento con le date

---

## Contatti e avvisi

### Dove arrivano gli avvisi

| Evento | Dove arriva | Chi lo sa | SLA |
|--------|------------|----------|-----|
| Deploy riuscito | Telegram gruppo admin (stanza `riepiloghi`) | Tutti moderatori | — |
| Deploy fallito/rollback/SOS | Telegram gruppo admin (stanza `errori`) oppure privato | Moderatori con privato aperto | entro 10 min |
| Backup fallito | Telegram canale backup privato (messaggio di testo) | Andrea, amministratore backup | — |
| Backup assente da >3 giorni | Telegram canale backup privato | Andrea | entro 1 ora da fallita |

### I tre nomi del disastro

| Termine | Significa |
|---------|----------|
| **Rollback** | Torniamo indietro di 1 commit (automatico o manuale) |
| **Ripristino** | Copiamo un database salvato sopra il nuovo database rotto |
| **Rebuild** | Ricostruiamo l'intera macchina da zero da un backup |

### Criteri di selezione: quale scenario?

```
Il mercatino non risponde?
├─ Sì, da meno di 90 secondi → Rollback automatico in corso (Scenario 1)
├─ Sì, da più di 90 secondi, ma il codice nuovo era nel giudice → Rollback manuale (Scenario 2)
├─ Sì, il codice è vecchio e il deploy non è andato → Ripristino da backup (Scenario 3)
└─ Sì, tutti i backup sono offline o corrotti → Rebuild (Scenario 4)

Il VPS non è raggiungibile?
└─ Rebuild (Scenario 4)

I segreti sono esposti?
└─ Rebuild (Scenario 4) + rotazione delle chiavi
```

---

## Appendice A: Checklist pre-deploy (Andrea)

Prima di spingere un commit su main (o di dire a Claude di farlo):

- [ ] Le prove sono verdi (`gh workflow view prove -w`)
- [ ] I test non toccano `config.py` o `*.db`
- [ ] Se il codice tocca il database: collaudo `collaudi_ci.py` il giorno prima
- [ ] Se il codice tocca il deploy o il backup: test manuale di rollback su una copia
- [ ] Se il codice tocca segreti o permessi: verifica il log del prima (`journalctl -u barattolo --since yesterday`)

---

## Appendice B: Checklist backup esterno (Andrea)

Ogni lunedì:

- [ ] `ls -ltr ~/Barattolo/backup/fuori/*.tar.gz.age | tail -3` — ci sono almeno 3 backup del weekend?
- [ ] I file sono cifrati (finiscono con `.age`)?
- [ ] Nessun errore di rclone nel log della sincronizzazione?
- [ ] Se manca il backup di ieri: controlla il journal di barattolo-backup sul VPS (`journalctl -u barattolo-backup.timer --since "2 days ago"`)

---

## Appendice C: Come aggiungere un nuovo tipo di dato al backup

Se oggi aggiungiamo un nuovo file che vuol dire denaro o segreti (una chiave, un database, un token), va dentro `deploy/backup-fuori.sh`:

1. Apri il file
2. Trovato il paragrafo `2)` o `2b)` che copre quella categoria
3. Aggiungi una riga: `cp <file> "$TMP/"`
4. Scrivi un commento che dica PERCHÈ è critico
5. Se è uno script che lo decripta, documentalo in `deploy/RIPRISTINO.md` passo D
6. Testa localmente: `bash deploy/backup-fuori.sh` e verifica che non urli errori
7. Commit e push

---

**Data di creazione:** 20 ott 2026  
**Data ultimo aggiornamento:** 20 ott 2026  
**Prossima revisione consigliata:** 20 gen 2027
