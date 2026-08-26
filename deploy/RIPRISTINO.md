# Il foglio del panico — rimettere in piedi Barattolo da zero

Scritto per essere letto alle due di notte, il giorno in cui il VPS —
o l'intero account Hetzner — non c'è più. Niente qui dentro richiede
il server vecchio.

## Le quattro case (dove sta cosa)

| Casa | Cosa contiene |
|---|---|
| **Carta** (i foglietti, con la chiave release) | la nsec della piattaforma, `CHIAVE_CONTENUTI_DIGITALI`, la metà segreta della chiave age |
| **Bitwarden** | le stesse tre, più URL e credenziali LNbits e il token del bot dei backup |
| **Canale Telegram dei backup** (privato) | un archivio cifrato al giorno: `satmarket.db`, `config.py`, `buste/`, `contenuti/`, Caddyfile e unit systemd |
| **Il PC di Andrea** (`C:\Users\Andrea\BarattoloBackup\`) | lo specchio di `foto/` e degli ultimi archivi — la seconda gamba, se Telegram non c'è |
| **GitHub** (repo privato) | tutto il codice, `deploy/` compreso. Si clona e basta |

I sats dell'escrow NON dipendono da niente di tutto questo: LNbits gira
su Spark (remoto) e la seed sono le 24 parole offline. Ma **senza il
database non si sa più di chi sono**: i `payment_hash` che legano ogni
pagamento al suo ordine vivono solo lì. È il motivo per cui questo
foglio esiste.

## La sequenza del disastro

1. **VPS nuovo** (qualunque fornitore), Ubuntu, Caddy, Python come da
   CLAUDE.md. `git clone` del repo.
2. **L'ultimo archivio**: dal canale Telegram (o da
   `BarattoloBackup\fuori\` sul PC, se Telegram non c'è).
3. **Decifrare**: la chiave age da Bitwarden (o dal foglietto) in un
   file `chiave.txt`, poi
   `age -d -i chiave.txt barattolo-XXXX.tar.gz.age | tar xz`.
4. **Rimettere i pezzi**: `satmarket.db`, `config.py`, `buste/`,
   `contenuti/` nella cartella dell'app; `sistema/Caddyfile` e le unit
   in `/etc`; `foto/` dal PC (`BarattoloBackup\foto\`).
5. **DNS**: puntare `barattolo.store` al server nuovo (registrar).
6. **Il webhook del bot si registra da solo** al primo avvio
   (`setWebhook` in startup); avviare il servizio e guardare
   `/api/salute`.
7. **Rimettere il timer dei backup** (vedi `barattolo-backup.service`)
   e la chiave SSH del pull sul server nuovo — il disastro successivo
   non aspetta che ce lo si ricordi.

## Cosa NON si recupera

- Gli archivi di Telegram **senza la chiave age**: è la ragione dei due
  supporti (carta + Bitwarden). Persa la chiave a macchina viva, costa
  zero: se ne genera una nuova e si aggiorna `AGE_PUBBLICA` sul server.
  Persa INSIEME alla macchina, i backup sono carta straccia.
- I contenuti digitali dentro il db **senza
  `CHIAVE_CONTENUTI_DIGITALI`**: un backup del database senza quella
  chiave è mezzo backup.
- Le ore fra l'ultimo archivio e il disastro (il backup è giornaliero).

## Il drill (fatto una volta, da rifare dopo ogni cambio di chiavi)

Un backup mai aperto è una speranza, non un backup:

1. scaricare dal canale l'archivio di ieri;
2. `age -d` con la chiave presa **da Bitwarden** (si prova quella vera);
3. aprire la sqlite, contare annunci/ordini/utenti, e decifrare UN
   contenuto digitale con la `CHIAVE_CONTENUTI_DIGITALI` dal foglietto;
4. confrontare il conteggio file di `BarattoloBackup\foto\` col `du`
   del VPS.

## Nota per chi tocca i testi

La pagina pubblica «Il pagamento protetto» dice che lo storico è
«salvato ogni giorno». Quando il drill qui sopra è passato, quella
frase può tornare a dire anche che le copie stanno **fuori dal
server** — prima no: la pagina non deve promettere un backup che
nessuno ha mai aperto.
