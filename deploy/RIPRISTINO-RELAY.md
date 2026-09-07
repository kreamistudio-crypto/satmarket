# Il foglio del panico del relay — rimettere in piedi relay.barattolo.store

Il gemello di `RIPRISTINO.md`, per l'altra macchina. Si legge il giorno
in cui il relay non c'è più.

## Prima di tutto: respira

**Il relay giù non ferma il mercatino.** Barattolo pubblica su TUTTI i
relay della sua lista e conta gli OK: finché ne risponde almeno uno,
annunci, ritiri e note escono come sempre — `_spedisci_ai_relay` non ha
nessun relay obbligatorio, e il nostro sta in coda apposta. Nessun sat è
in gioco, nessun ordine si ferma, nessuno resta chiuso fuori.

Quindi questo foglio si legge con calma, e la fretta giusta è quella di
un servizio da rimettere in piedi, non quella di un disastro.

⚠️ **La sola cosa che si perde davvero col tempo sono gli EVENTI delle
ore in cui il relay è giù** — e nemmeno quelli, se gli altri relay li
hanno presi: si riprendono col `sync` del passo 8.

## Dove sta cosa

| Casa | Cosa contiene |
|---|---|
| **Canale Telegram dei backup** (privato) | un archivio al giorno: `relay-AAAAMMGG-HHMM.tar.age` |
| **Il PC di Andrea** (`BarattoloBackup\relay\`) | lo specchio degli stessi archivi — la seconda gamba |
| **Carta + Bitwarden** | la metà segreta della chiave age **di Barattolo** |
| **Gli altri relay Nostr** | gli eventi. Non li salviamo noi: si riscaricano |

⚠️ **LE CHIAVI AGE SONO DUE.** Quella di **Barattolo** apre il VPS *e*
il relay; il **nodo** ha la sua. Se `age` risponde «no identity
matched», quasi sempre è questo — è successo al primo drill del relay
(7 set 2026). Se invece dice «unknown identity type», è l'altra
trappola: manca il prefisso `AGE-SECRET-KEY-` (la chiave intera è di
74 caratteri, vedi `RIPRISTINO.md`).

## ⚠️ Quello che vive SOLO lì dentro

Il VPS di Barattolo ha il suo codice su GitHub e l'archivio porta i
soli dati. **Il relay no**: `compose.yml`, `Dockerfile`, `strfry.conf`,
il plugin `policy/chi-scrive.py`, il `Caddyfile`, le quattro unit,
`aggiorna-chiavi.sh` e `backup-relay.sh` **non stanno in nessun repo** —
l'unica copia fuori da quella macchina è quell'archivio.

È anche il motivo per cui non è «un backup di configurazione»: è il
backup dell'unica copia del codice di quella macchina, e da lì la
macchina si ricostruisce per intero.

## La sequenza

1. **Macchina nuova** (LNVPS o qualunque altro), Debian o Ubuntu, con
   `docker` e `docker compose`.

2. **L'ultimo archivio**: dal canale Telegram, o da
   `BarattoloBackup\relay\` sul PC se Telegram non c'è.

3. **⚠️ PRIMA L'UTENTE, POI L'ESTRAZIONE.** È la stessa trappola di
   `debian-tor` sul VPS, con un giro di vite in più.

   Il proprietario dentro l'archivio è registrato **per NOME**: finché
   l'utente `barattolo` non esiste, `tar` — anche da root — non può
   assegnarlo e lascia tutto a root. Il plugin parte lo stesso e non
   riesce a leggere la sua whitelist: il relay accetta o rifiuta le
   scritture sbagliate **senza che niente fallisca**.

   E qui il nome non basta: conta anche l'**UID**, perché a leggere quei
   file è il processo dentro il container, che va per numero e non per
   nome. Ricreare `barattolo` con un UID diverso rimette a posto i
   permessi sull'host e li rompe per il container.

   L'UID vero non si tira a memoria: **lo dice l'archivio**. Si guarda
   prima di estrarre, con `--numeric-owner`, e si crea l'utente con
   quel numero:

   ```bash
   age -d -i chiave.txt relay-AAAAMMGG-HHMM.tar.age > /tmp/relay.tar
   tar tvf /tmp/relay.tar | head -20                    # i NOMI dei proprietari
   tar tv --numeric-owner -f /tmp/relay.tar | head -20  # i NUMERI: è questo che conta
   useradd -u 1001 -r -s /usr/sbin/nologin barattolo    # 1001 = quel numero
   id barattolo                                         # conferma
   ```

   Solo adesso si estrae, da root:

   ```bash
   mkdir -p /opt/relay && tar xf /tmp/relay.tar -C /opt/relay
   ls -la /opt/relay /opt/relay/policy                  # i proprietari sono giusti?
   ```

4. **Le unit al loro posto**: le quattro unit systemd stanno
   nell'archivio. Si copiano in `/etc/systemd/system/`, poi
   `systemctl daemon-reload`. Quali siano lo dice l'archivio stesso —
   `tar tf /tmp/relay.tar | grep -Ei 'service|timer'` — e non si tirano
   a memoria alle due di notte.

5. **DNS**: puntare `relay.barattolo.store` alla macchina nuova. Senza,
   Caddy non prende il certificato e il WebSocket non si apre: è il
   passo che blocca tutti quelli dopo.

6. **Su**: `docker compose up -d` dalla cartella del relay, poi Caddy.
   La prova non è che i container siano «up» — è che il relay RISPONDA:

   ```bash
   curl -s -H 'Accept: application/nostr+json' https://relay.barattolo.store/ | head -c 400
   ```

   Deve tornare il NIP-11 col nostro nome. Se torna vuoto o un errore di
   certificato, si guarda il DNS prima del resto.

7. **La whitelist si riempie da sola.** `policy/chiavi.txt` viene
   dall'archivio — quindi è quella del giorno del backup — e il timer la
   riallinea da `/api/relay/chiavi` sul VPS di Barattolo. Se il VPS è
   vivo, entro un giro è in pari da sé; se il VPS è giù, resta quella
   dell'archivio, che è il verso giusto in cui sbagliare: una whitelist
   vecchia lascia scrivere chi scriveva ieri, una vuota chiuderebbe
   fuori tutti.

   Per non aspettare il timer: `systemctl start` sulla unit delle
   chiavi, poi `wc -l policy/chiavi.txt`.

8. **Gli eventi si riscaricano dagli altri relay** — vedi la sezione qui
   sotto. Il relay è già utile prima di questo passo: da subito accetta
   le scritture nuove.

9. **Rimettere le difese**, che è il passo che si dimentica perché a
   quel punto il servizio funziona già: il **timer del backup** (03:45),
   la **ronda** (08:00) e la **chiave SSH in sola lettura** per il pull
   dal PC. Il disastro successivo non aspetta che ce lo si ricordi — e
   un relay senza backup è esattamente il punto da cui si è appena
   usciti.

## Il database degli eventi non c'è nell'archivio, ed è voluto

**Si salva ciò che non si ricostruisce.** Gli eventi Nostr vivono su
molti relay per costruzione: sono firmati, quindi nessuno può alterarli
in transito, e si riprendono da chiunque li abbia. La whitelist e la
configurazione no — quelle esistono solo qui.

Chi apre l'archivio e non trova `db/` **non ha trovato un archivio
rotto**: ha trovato la regola. Il modo di rimetterli è il sync di
strfry, che scarica da un altro relay:

```bash
docker compose exec strfry strfry sync wss://relay.damus.io --dir down
```

⚠️ Va dato **dopo** il passo 6 (il relay deve girare) e può prendere
tempo. Vale la pena restringerlo a quel che ci serve davvero — i nostri
kind e i nostri autori — invece di tirare giù mezzo Nostr: `strfry sync
--help` dice come, e la lista degli autori è `policy/chiavi.txt`, che a
quel punto è già lì.

## Cosa NON si recupera

- L'archivio **senza la chiave age**: è la ragione dei due supporti
  (carta + Bitwarden). Persa a macchina viva costa zero — se ne genera
  una nuova e si aggiorna la pubblica sulla macchina. Persa INSIEME alla
  macchina, i backup sono carta straccia.
- Le ore fra l'ultimo archivio e il disastro, per la sola
  **configurazione** (il backup è giornaliero). Gli eventi no: quelli
  tornano col sync.
- ⚠️ **Un archivio porta il mondo del giorno in cui è nato.** Se fra il
  backup e il disastro qualcosa è cambiato — una voce nella whitelist,
  una riga di `strfry.conf` — torna com'era allora, non com'era ieri
  sera. E può portarsi dietro roba che nel frattempo era stata tolta
  apposta: `strfry.conf.prima-nip11` è comparsa nel drill del 7 set 2026
  in un archivio nato prima della sua cancellazione, ed era giusto così.

## Il drill

Un backup mai aperto è una speranza, non un backup. Si rifà **a ogni
cambio di chiavi, e quando nell'archivio entra qualcosa di nuovo**:

1. scaricare dal canale l'archivio di ieri;
2. `age -d` con la chiave di **Barattolo** presa da Bitwarden (si prova
   quella vera, non una copia comoda);
3. `tar tf` e confrontare l'elenco con quello che il journal del backup
   dichiara di aver messo dentro: devono combaciare **voce per voce**,
   non «più o meno»;
4. cancellare la cartella estratta — `token.header` e `chiavi.txt`
   stanno lì in chiaro.

**FATTO il 7 set 2026, verde**: l'archivio si apre con la chiave di
Barattolo e l'elenco combacia esatto col journal, sedici voci. Il primo
tentativo era andato in «no identity matched» con la chiave del nodo —
la trappola è a verbale in cima a questo foglio.

⚠️ **QUEL CHE IL DRILL NON DICE**: che i permessi reggano. L'elenco
prova che i file ci sono e che la chiave li apre; che `barattolo` con
l'UID giusto li lasci leggere al container lo prova solo un ripristino
vero. È la stessa metà scoperta dichiarata per la chiave dell'onion in
`RIPRISTINO.md`, e vale qui parola per parola.

## Nota per chi tocca i testi

Vale la regola del fratello: qui dentro non ci sono spiegazioni, ci sono
istruzioni che qualcuno seguirà **col panico addosso**. Ogni riga o dice
un comando o dice perché quel comando serve. Se una diventa falsa — un
percorso che cambia, un timer che si sposta, una casa nuova — si
corregge **nello stesso commit** che l'ha resa falsa, non dopo.
