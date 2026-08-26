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
   ⚠️ La chiave INTERA comincia con `AGE-SECRET-KEY-1…` (74 caratteri):
   se `age` risponde «unknown identity type», quasi certamente manca il
   prefisso `AGE-SECRET-KEY-` — si riattacca davanti e riprova. È
   successo al primo drill (ago 2026): copiando da Bitwarden erano
   arrivati i soli 59 caratteri dal «1» in poi — la copia salvata era
   intera, a mozzarla era stato il copia-incolla. Alle due di notte si
   sbaglia uguale: controllare la LUNGHEZZA prima di incolpare la
   chiave.
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

## Il drill (da rifare dopo ogni cambio di chiavi)

Un backup mai aperto è una speranza, non un backup:

1. scaricare dal canale l'archivio di ieri;
2. `age -d` con la chiave presa **da Bitwarden** (si prova quella vera);
3. aprire la sqlite, contare annunci/ordini/utenti, e decifrare UN
   contenuto digitale con la `CHIAVE_CONTENUTI_DIGITALI` presa dal
   config RIPRISTINATO (prova che l'archivio è autosufficiente);
4. confrontare il conteggio file di `BarattoloBackup\foto\` col `du`
   del VPS.

**FATTO il 26 ago 2026, tutto verde**: le due copie (Telegram e pull
sul PC) identiche allo sha256, integrity_check ok, 300 annunci / 45
ordini / 292 utenti, un contenuto digitale + una busta + un blob su
file decifrati con la chiave letta dal config dentro l'archivio.
L'unico intoppo è a verbale qui sopra: il prefisso age mancante nella
copia Bitwarden.

## Nota per chi tocca i testi

La pagina pubblica «Il pagamento protetto» dice che lo storico è
salvato ogni giorno **con copie cifrate anche fuori dal server** — la
mezza frase è tornata col drill del 26 ago 2026. Se le chiavi cambiano
e il drill non viene rifatto, quella frase torna una promessa non
provata: si rifà il drill, non si lascia la frase sulla fiducia.
