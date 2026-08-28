# Il foglio del panico — rimettere in piedi Barattolo da zero

Scritto per essere letto alle due di notte, il giorno in cui il VPS —
o l'intero account Hetzner — non c'è più. Niente qui dentro richiede
il server vecchio.

## Le quattro case (dove sta cosa)

| Casa | Cosa contiene |
|---|---|
| **Carta** (i foglietti, con la chiave release) | la nsec della piattaforma, `CHIAVE_CONTENUTI_DIGITALI`, la metà segreta della chiave age |
| **Bitwarden** | le stesse tre, più URL e credenziali LNbits e il token del bot dei backup |
| **Canale Telegram dei backup** (privato) | un archivio cifrato al giorno: `satmarket.db`, `config.py`, `buste/`, `contenuti/`, Caddyfile, unit systemd e **la chiave del servizio nascosto Tor** (`sistema/tor-hidden-service/`) |
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

   **La chiave dell'onion ha una liturgia sua, e l'ordine conta.**
   `sistema/tor-hidden-service/` è la cartella che il torrc chiama
   `HiddenServiceDir`, e quella chiave *è* l'indirizzo: se non torna al
   suo posto con proprietario e permessi giusti, Tor non parte — e
   l'indirizzo .onion non si rigenera, quindi non c'è un piano B.

   **Prima si installa Tor, poi si estrae** (`apt install tor`): il
   proprietario nell'archivio è registrato per NOME, e finché l'utente
   `debian-tor` non esiste `tar` — anche da root — non può assegnarlo e
   lascia tutto a root. Fatto in quest'ordine, l'estrazione da root
   rimette owner e permessi da sola e non serve altro.

   Se l'archivio è già stato estratto prima di installare Tor (è il
   caso normale: si estrae tutto e poi ci si accorge), si rimedia a
   mano — il percorso di destinazione si legge dal `sistema/torrc`
   appena ripristinato, **non è quello dell'archivio**:

   ```bash
   grep HiddenServiceDir /etc/tor/torrc          # es. /var/lib/tor/barattolo/
   mkdir -p /var/lib/tor/barattolo               # Tor la crea al primo avvio: qui non c'è ancora
   cp -a sistema/tor-hidden-service/. /var/lib/tor/barattolo/
   chown -R debian-tor:debian-tor /var/lib/tor/barattolo
   chmod 700 /var/lib/tor/barattolo
   systemctl restart tor && sleep 5
   systemctl is-active tor                       # se non è "active", il log è `journalctl -u tor -n 30`
   cat /var/lib/tor/barattolo/hostname            # DEVE essere l'indirizzo di prima
   ```

   Il `cat` finale è la verifica vera: se l'indirizzo è cambiato, Tor
   non ha letto la chiave vecchia e **ne ha appena generata una nuova**
   — si ferma tutto, si rimette la cartella dall'archivio e si riparte,
   perché da lì in avanti l'indirizzo di prima è perso davvero.
   (Il nome utente su Debian/Ubuntu è `debian-tor`; se la distribuzione
   è un'altra, lo dice `systemctl show tor -p User`.)
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

## Il drill (da rifare a ogni cambio di chiavi, e quando nell'archivio entra qualcosa di nuovo)

Un backup mai aperto è una speranza, non un backup:

1. scaricare dal canale l'archivio di ieri;
2. `age -d` con la chiave presa **da Bitwarden** (si prova quella vera);
3. aprire la sqlite, contare annunci/ordini/utenti, e decifrare UN
   contenuto digitale con la `CHIAVE_CONTENUTI_DIGITALI` presa dal
   config RIPRISTINATO (prova che l'archivio è autosufficiente);
4. confrontare il conteggio file di `BarattoloBackup\foto\` col `du`
   del VPS;
5. **rimettere in piedi la chiave dell'onion**, non solo vederla
   nell'elenco: su una macchina di prova (o in un container) si segue
   la liturgia del passo 4 della *sequenza del disastro* qui sopra, e
   si guarda l'`hostname` che Tor scrive — se è
   l'indirizzo di sempre, la chiave nell'archivio è viva. Vederla
   comparire in `tar -tzf` dice solo che il file c'è: che sia la
   chiave giusta, e che i permessi la lascino usare, lo dice Tor.

**FATTO il 26 ago 2026, tutto verde**: le due copie (Telegram e pull
sul PC) identiche allo sha256, integrity_check ok, 300 annunci / 45
ordini / 292 utenti, un contenuto digitale + una busta + un blob su
file decifrati con la chiave letta dal config dentro l'archivio.
L'unico intoppo è a verbale qui sopra: il prefisso age mancante nella
copia Bitwarden.

⚠️ **MA QUEL DRILL NON COPRE PIÙ TUTTO L'ARCHIVIO**: il 26 agosto la
chiave dell'onion non c'era ancora — è entrata il 28 (commit
`5c7f19a`) — quindi il verde di quel giorno non dice niente su di lei.
Il 28 si è verificato che nell'archivio ci sia (`age -d … | tar -tzf -`
elenca torrc e i tre file), che è metà della domanda: **la chiave va
rimessa in piedi, non solo vista**. Finché il punto 5 qui sopra non è
stato fatto almeno una volta, sull'onion siamo dove eravamo prima del
26 agosto — un file che si presume buono perché è nell'elenco. E vale
la regola di sotto: è una promessa non ancora provata.

## Nota per chi tocca i testi

La pagina pubblica «Il pagamento protetto» dice che lo storico è
salvato ogni giorno **con copie cifrate anche fuori dal server** — la
mezza frase è tornata col drill del 26 ago 2026. Se le chiavi cambiano
e il drill non viene rifatto, quella frase torna una promessa non
provata: si rifà il drill, non si lascia la frase sulla fiducia.
