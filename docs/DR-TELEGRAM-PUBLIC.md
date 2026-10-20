# Piano di Disaster Recovery — Barattolo 🫙⚡

**Data:** 20 ott 2026 · **Versione:** 1.0 · **Stato:** Attivo

Ecco il piano completo di disaster recovery di Barattolo — cosa fare se qualcosa va male.

---

## TL;DR

| Situazione | Tempo fermo | Azione |
|-----------|-----------|--------|
| Deploy nuovo non risponde | ~90 sec | **Automatico** — il bot avvisa e torna indietro |
| Deploy rifiutato dalla CI | ~5 min | Guarda il motivo nel journal, aggiusta il codice |
| Database corrotto | ~5-10 min | Ripristina da backup pre-deploy (sempre sul VPS) |
| Disco pieno | ~15 min | Pulisci i backup vecchi o espandi il disco |
| VPS perso (account hacker) | **4-6 ore** | Rebuild completo da backup cifrato |
| Tutti i backup offline | 🆘 | Escalation al team — situazione emergenziale |

---

## Come è strutturato il backup

**Sul VPS (`/srv/barattolo/backup/`):**

- `pre-deploy-*.db` — 5 backup di database, uno prima di ogni deploy (ultimi 5)
- `fuori/*.tar.gz.age` — backup giornaliero cifrato con age (creato ogni giorno alle 22:00 UTC)

**Esterno (offline, sicuro):**

- **Telegram canale privato** — il backup giornaliero arrive qui ogni notte (50 MB max per Telegram)
- **PC di Andrea** — specchio via rclone, aggiornato giornalmente

**Cosa dentro l'archivio cifrato:**

```
Database (Barattolo + LNbits)
Config (segreti: nsec, token, chiavi)
Dati sensibili (buste, contenuti)
Configurazione di sistema (Tor, systemd, Caddy)
```

**Cosa NON dentro (si ricostruisce da git):**

```
Foto (171 MB, tira Andrea via rclone se serve)
Codice (su GitHub, tags a ogni deploy)
```

---

## Scenario 1: Rollback automatico (il caso normale)

**Quando:** Il codice nuovo non risponde in `/api/salute` entro 45 secondi dal riavvio.

**Cosa succede:**

1. `deploy.sh` lo vede
2. Segna il commit come bocciato
3. Torna indietro a `HEAD~1` (commit precedente)
4. Riavvia il servizio
5. Avvisa in Telegram:
   ```
   ↩️ Deploy annullato: <nuovo> non rispondeva
   Sono tornato a <precedente> e il mercatino sta bene
   ```

**Tempo fermo:** ~90 secondi.

**La tua azione:** Leggi il motivo nel journal, aggiusta il codice, spinga un commit nuovo.

---

## Scenario 2: Deploy rifiutato (la CI non lo permette)

**Quando:** La firma SSH manca, il commit non è su main, la CI è rossa, etc.

**L'avviso in Telegram:**

```
⛔ Deploy rifiutato: <motivo>
Resta in produzione <versione vecchia>
```

**La tua azione:**

1. Leggi il motivo nel journal: `journalctl -u barattolo-deploy -n 10`
2. Aggiusta il problema (es: spinga da main, non da un ramo)
3. Spinga un commit nuovo sulla CI
4. Aspetta che la CI dica ok
5. Il deploy partirà da solo

**Tempo fermo:** 0 (il mercatino non è mai andato giù).

---

## Scenario 3: Ripristino da backup recente

**Quando serve:**

- Il rollback ha fallito (`🆘 nemmeno la versione precedente risponde`)
- Il database è corrotto (disco, bit rot, etc)
- Il disco è pieno
- Sospetti un compromesso di segreti

**Ripristino veloce (backup pre-deploy, max 1 ora fa):**

```bash
# Su VPS (Andrea ha le chiavi SSH)
cd /srv/barattolo

# 1) Ferma il servizio
systemctl stop barattolo

# 2) Scegli il backup più recente
ls -ltr backup/pre-deploy-*.db | tail -3

# 3) Ripristina
cp backup/pre-deploy-YYYYMMDD-HHMMSS-XXXXX.db satmarket.db

# 4) Verifica che sia integro
sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"

# 5) Riavvia
systemctl start barattolo
```

**Ripristino da backup cifrato (decriptato offline):**

Fai come sopra, ma il file viene da:

- Telegram canale backup (scaricato offline)
- PC di Andrea (in `~/Barattolo/backup/fuori/`)

Decripta offline con la chiave privata age (Bitwarden), estrai, e segui il passo 2 qui sopra.

**Tempo fermo:** ~5-10 minuti.

---

## Scenario 4: Rebuild da zero (il VPS è perso)

**Quando serve:** L'account Hetzner è stato hackerato, il server è cancellato, il disco è morto.

**Requisiti:**

- Una macchina Ubuntu 26.04 LTS nuova
- Un backup decriptato (Telegram o PC di Andrea)
- 30 GB di spazio su disco
- La chiave privata age (offline, Bitwarden)

**Procedura:**

La guida passo-passo è in `deploy/RIPRISTINO.md` sul repo — 10 fasi, ~4-6 ore:

1. Setup della macchina
2. Clone del codice
3. Posa del backup (decriptato)
4. Setup del servizio
5. Setup Caddy + SSL
6. Setup Tor + servizio nascosto
7. Setup LNbits (cassaforte)
8. Setup del ponte verso il nodo
9. Setup del deploy automatico
10. Verifiche finali

**Tempo fermo:** 4-6 ore.

**Contatti:**

Se il rebuild non avanza: apri un issue GitHub o chiedi a Claude Code nel progetto. Il documento è dettagliato e testato.

---

## Quello che non potremmo mai ripristinare

⚠️ **La chiave privata Tor (.onion)** — se la perdiamo:

- Il servizio nascosto si rigenerebbe con un nuovo indirizzo
- Tutti i link `.onion` salvati finirebbero mort
- Utenti da Tor non potranno raggiungerci finché non aggiornano

→ **Il backup la contiene e la protegge in modo critico.**

---

## Testing periodico (importante!)

**Una volta al mese (lunedì):**

Andrea testa il backup scaricato:

1. Scarica il backup più recente da Telegram
2. Lo decripta offline (chiave privata da Bitwarden)
3. Estrae il tar.gz
4. Verifica che il database si apra: `sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"`
5. Verifica che il config.py sia integro (tutti i segreti ci sono)
6. Segna il test con data e risultato
7. Se fallisce: urla e apriamo un issue

→ **Un backup che non si ripristina è come non avere un backup.**

---

## Il timer del deploy (quello che fa tutto)

Ogni minuto il VPS chiede:

- "C'è qualcosa di nuovo su GitHub?"
- Se c'è: "La CI dice che è ok?"
- Se ok: "Il commit è firmato?"
- Se tutto ok: tira e riavvia
- Se fallisce: rollback automatico

**Se il timer si ferma** → niente deploy automatico, ma il mercatino continua a girare con il codice vecchio.

```bash
# Controllo (Andrea su VPS)
systemctl status barattolo-deploy.timer
journalctl -u barattolo-deploy --since "1 hour ago"
```

---

## Avvisi nel Telegram

| Messaggio | Significato | Azione |
|-----------|-----------|--------|
| `🚀 Barattolo aggiornato` | Nuovo codice è in produzione | ✅ Niente, è ok |
| `↩️ Deploy annullato` | Nuovo codice non rispondeva, tornato indietro | ⚠️ Leggi journal, aggiusta |
| `⛔ Deploy rifiutato` | CI non lo permette | ⚠️ Leggi motivo, aggiusta, riprovare |
| `⏳ Deploy fermo` | CI gira ancora, aspettiamo | ✅ Aspetta qualche minuto |
| `🆘 Barattolo è GIÙ` | Niente risponde, rollback fallito | 🔴 **EMERGENZA** — Ripristino Scenario 3 |

---

## Dimmi se qualcosa non è chiaro

Questo piano è in git, aggiornabile e testato. Se manca qualcosa o se il wording non è chiaro, apri un issue o proponi un commit.

**Documenti nel repo:**

- `docs/DISASTER-RECOVERY.md` — guida completa con procedure passo-passo
- `deploy/RIPRISTINO.md` — rebuild da zero, nel dettaglio
- `deploy/utility-ripristino.sh` — script di utility per test e monitoraggio
- `deploy/backup-fuori.sh` — il backup giornaliero cifrato

**Contatti:**

- Issues GitHub: per dubbi sul piano
- Telegram: per emergenze durante un disastro

---

**Piano creato:** 20 ott 2026  
**Ultimo aggiornamento:** 20 ott 2026  
**Prossima revisione:** 20 gen 2027
