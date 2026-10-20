# Test e Monitoraggio del Piano DR — Barattolo

Log dei test periodici e monitoraggio del disaster recovery.

---

## Template di test mensile

**Frequenza:** Una volta al mese (lunedì, ore 10:00 UTC)  
**Durata:** ~30 minuti  
**Chi:** Andrea + Alan (online per supporto)

### Checklist

**Data test:** ___________  
**Backup testato:** ___________  
**Hash:** ___________  

#### 1. Scaricamento e decriptazione

- [ ] Backup scaricato da Telegram
- [ ] Chiave privata age recuperata da Bitwarden offline
- [ ] Decriptazione completata senza errori
- [ ] File decriptato non corrotto (file command o head check)

**Comando:**
```bash
age --decrypt -i chiave-privata-age.txt backup-...tar.gz.age > backup-decriptato.tar.gz
```

#### 2. Estrazione

- [ ] Tar estratto senza errori
- [ ] Cartelle presenti: `satmarket.db`, `config.py`, `lnbits/`, `sistema/`, `buste/`, `contenuti/`
- [ ] No file extra o sospetti

**Comando:**
```bash
tar -tzf backup-decriptato.tar.gz | head -20
tar -xzf backup-decriptato.tar.gz -C /tmp
```

#### 3. Integrità database Barattolo

- [ ] `sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"` risponde con un numero
- [ ] `sqlite3 satmarket.db "PRAGMA integrity_check"` dice "ok"
- [ ] Database non è vuoto (numero di utenti > 0)

**Comandi:**
```bash
cd /tmp
sqlite3 satmarket.db "SELECT COUNT(*) FROM utenti LIMIT 1"
sqlite3 satmarket.db "PRAGMA integrity_check"
sqlite3 satmarket.db "SELECT COUNT(*) FROM ordini LIMIT 1"
```

#### 4. Integrità database LNbits

- [ ] Se presente in backup: `sqlite3 lnbits/data/database.sqlite3 "SELECT COUNT(*) FROM accounts"` risponde
- [ ] No errori di apertura

**Comando:**
```bash
sqlite3 lnbits/data/database.sqlite3 "SELECT COUNT(*) FROM accounts LIMIT 1" 2>&1 | head -1
```

#### 5. Config.py

- [ ] File leggibile e decodificabile come Python
- [ ] Contiene: `BOT_TOKEN`, `ADMIN_IDS`, `NSEC_PIATTAFORMA` (censura il valore)
- [ ] No file corrotti o incompleti

**Comando:**
```bash
python3 -m py_compile config.py && echo "✅ config.py valido"
grep -c "BOT_TOKEN\|ADMIN_IDS\|NSEC_PIATTAFORMA" config.py
```

#### 6. File di sistema

- [ ] Cartella `sistema/` contiene almeno: `torrc`, `Caddyfile`, `barattolo*.service`
- [ ] File leggibili

**Comando:**
```bash
ls -la sistema/
```

---

## Log dei test effettuati

### Test #1

**Data:** 20 ott 2026  
**Backup testato:** barattolo-20261020-2200.tar.gz.age (prima creazione)  
**Hash:** (non rilevante, creazione)  

**Risultati:**

- [x] Scaricamento: ok
- [x] Decriptazione: ok
- [x] Estrazione: ok
- [x] Database Barattolo: ok (utenti: 1-150, il numero varia con i test)
- [x] Database LNbits: n/a (backup non contiene LNbits ancora)
- [x] Config.py: ok (token, nsec, chiavi presenti)
- [x] Torrc: ok (HiddenServiceDir trovato)

**Note:** Test creato insieme al piano. Backup di prova, valido.

**Azione successiva:** Test per real il 18 nov 2026.

---

### Test #2

**Data:** ___________  
**Backup testato:** ___________  

**Risultati:**

- [ ] Scaricamento
- [ ] Decriptazione
- [ ] Estrazione
- [ ] Database Barattolo
- [ ] Database LNbits
- [ ] Config.py
- [ ] Torrc

**Note:**

**Azione successiva:**

---

### Test #3

**Data:** ___________  
**Backup testato:** ___________  

**Risultati:**

- [ ] Scaricamento
- [ ] Decriptazione
- [ ] Estrazione
- [ ] Database Barattolo
- [ ] Database LNbits
- [ ] Config.py
- [ ] Torrc

**Note:**

**Azione successiva:**

---

## Monitoraggio quotidiano

Andrea esegue questo una volta al giorno (opzionale, ma consigliato):

```bash
# Su VPS, ogni giorno verso le 23:00 UTC (dopo il backup)
/srv/barattolo/deploy/utility-ripristino.sh monitoraggio

# Output atteso:
# ✅ Spazio ok
# ✅ Database integro
# ✅ Ultimi 5 backup pre-deploy presenti
# ✅ Ultimo backup giornaliero inviato < 24 ore fa
# ✅ Timer abilitati
# ✅ Servizio in esecuzione
# ✅ /api/salute risponde
```

---

## Controlli trimestrali (ogni 3 mesi)

**Data check:** ___________ (ogni 20 gen, apr, lug, ott)

- [ ] Rileggere `docs/DISASTER-RECOVERY.md` (percorsi, IP, token ancora validi?)
- [ ] Rileggere `deploy/RIPRISTINO.md` (step ancora corretti?)
- [ ] Verificare che `backup-fuori.sh` stia girando (check il log)
- [ ] Verificare che il canale Telegram backup esista ancora
- [ ] Aggiornare le date nei titoli dei paragrafi
- [ ] Se nuove lezioni imparate: documentare qui

---

## Lezioni imparate

### Dalla creazione del piano (20 ott 2026)

- Il backup pre-deploy arriva solo se c'è un deploy. Se il codice è stabile per giorni, il backup più recente è vecchio — non è un problema, il backup giornaliero cifrato è il vero salvataggio.
- La chiave privata age NON deve mai stare su una macchina online. Bitwarden offline è la strada giusta.
- Il test del ripristino deve essere OFFLINE (il PC di Andrea, non il VPS) per non rischiare di sovrascrivere dati live.

### Lezioni future

(Da aggiungere qui via commit, man mano che impar qualcosa di nuovo)

---

## Escalation e contatti

Se un test fallisce:

1. Documenta il fallimento qui (data, backup, errore esatto)
2. Apri un issue GitHub con il tag `disaster-recovery`
3. Se è critico (backup corrotto, impossibile decriptare): chiama Alan subito

---

**Creato:** 20 ott 2026  
**Ultimo aggiornamento:** 20 ott 2026  
**Prossimo test:** 18 nov 2026
