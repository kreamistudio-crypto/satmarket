## Produzione

La macchina, le procedure che si lanciano a mano e la catena del deploy
per intero. Le poche righe che cambiano il GESTO invece del contenuto —
push su main = online entro un minuto, il config del VPS che vince sul
default del codice, e MODALITA_COLLAUDO col BOT_TOKEN vero fuori dal VPS
— restano in `CLAUDE.md`. Qui c'è tutto il resto.

Il sito barattolo.online sta nel repo privato
kreamistudio-crypto/barattolo-online (clonato in
Documents\GitHub\barattolo-online); Vercel pubblica da solo a ogni push
su main.
LA COPIA NOSTR DEL SITO (nsite, 15 ott 2026, cantiere nsite-allineato,
richiesta di Andrea): è il sito radice (manifesto kind 15128) della
chiave di Barattolo,
npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy, e si
vede su
https://npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy.nsite.lol/
I file stanno in Documents\GitHub\barattolo-nsite, che NON è un repo
git e NON si aggiorna da sola: dopo ogni ritocco al sito va rifatta e
ripubblicata a mano. La ricetta (la stessa dell'8 ott): le pagine e
`robots.txt` presi da git (`git cat-file blob HEAD:<file>`, non dalla
cartella di lavoro, che con autocrlf ha i CRLF), con `poster="video/` e
`src="video/` riscritti a `https://www.barattolo.online/video/` (i video
su Blossom non ci vanno); niente `video/`, `vercel.json`, `sitemap.xml`;
solo le immagini che le pagine citano (37). Si pubblica con nsyte
(0.28.1, nel WSL Ubuntu), dalla cartella:
`nsyte deploy . --no-config -s https://blossom.primal.net,https://cdn.hzrd149.com -r wss://relay.barattolo.store,wss://nos.lol,wss://relay.primal.net,wss://relay.damus.io,wss://relay.nsite.lol --fallback index.html --prompt-sec`
— nsyte aggiunge da sé i relay della lista 10002 di Barattolo: il 15
ott al deploy erano anche relay.nmail.li e nostr-01.yakihonne.com (la
10002 sbagliata messa da nmail), poi la 10002 è stata rifatta (id
9dec51e5, i sei relay di Barattolo) e nsyte userà quelli; la voce «I
RELAY DI BARATTOLO: LA LISTA (`RELAY_NOSTR`) E IL KIND 10002».
COME SI AGGIORNA CON AMBER, senza nsec sul PC né in chat: 1) `nsyte ci`
nel WSL → «Scan QR Code (Nostr Connect)» → relay `wss://nos.lol` (il
default, relay.nsec.app, il 13 ott non rispondeva) → QR inquadrato con
Amber, chiave di Barattolo: stampa un `nbunksec`, lasciapassare della
sessione che non salva su disco e che in chat non va mai; 2) il deploy
qui sopra con `--dry-run` in fondo (non firma niente; l'anteprima del
manifesto finisce in `/tmp/nsyte-dry-run-*`); 3) il deploy vero,
incollando l'`nbunksec` al prompt: DUE firme su Amber, il permesso
Blossom (24242, fino a 20 file in una firma) e il manifesto (15128);
4) controllo su nsite.lol di `/`, `en.html`, `es.html`; 5) la sessione
si revoca da Amber, e l'`nbunksec` non vale più. `nsyte bunker connect`
NON serve: salva il collegamento su disco, e con `--no-config` nsyte
non lo usa («--no-config requires --sec»). Il gesto che non si disfa è
il deploy vero: il manifesto nuovo sostituisce il vecchio (si torna
indietro solo ripubblicando la cartella di prima) e i file caricati su
Blossom restano pubblici. cdn.nostrcheck.me è TOLTO dal comando (15
ott, decisione di Andrea): non prendeva i file (8 ott: 2 su 41; 15
ott: 401 «Auth event already used» e 400 «file type not detected»);
il sito vive da blossom.primal.net e cdn.hzrd149.com. Il manifesto
del 15 ott lo nomina ancora fra i server: sparisce al deploy dopo.

I PERCORSI DEL VPS SONO SCRITTI PER ESTESO (10 ott 2026, cantiere
percorsi-vps, richiesta di Andrea): la cartella del server è
`/srv/barattolo`, il config `/srv/barattolo/config.py`, il database
`/srv/barattolo/dati/satmarket.db`. `~/satmarket` porta allo stesso
posto (è un collegamento, verificato con `readlink -f`), ma la tilde
sotto `sudo -u barattolo` la espande la shell di root, e per questo qui
non compare più: ogni comando vale da qualunque utente lo lanci.
I DUE PERCORSI DEL DATABASE, tutti e due giusti (verificati da Andrea
sul VPS il 12 ott 2026 con `readlink -f`): il file VERO è
`/srv/barattolo/dati/satmarket.db`, e `/srv/barattolo/satmarket.db` è
un COLLEGAMENTO a lui — il nome che apre il server stesso, accanto al
codice (lo crea `deploy/utente/cambio-utente.sh`). Aprono lo stesso
database.
LE LETTURE DI QUESTO DOCUMENTO SONO IN PYTHON3 (12 ott 2026), dal
collegamento:
`python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); …"`
— `mode=ro` è la sola lettura: non scrive nemmeno per sbaglio — e
stampano una riga per riga trovata, coi campi separati da `|`. Le poche
SCRITTURE lo dicono in chiaro, passano da `sudo -u barattolo` e vanno
sul file vero. È una forma sola per le due macchine, non una
necessità: SUL VPS IL COMANDO `sqlite3` C'È (`/usr/bin/sqlite3`, lo usa
il backup fuori sede di `deploy/backup-fuori.sh`). SUL NODO INVECE
MANCA DAVVERO (verificato da Andrea il 12 ott 2026): lì il database si
legge solo con `sudo python3`, perché `~/nodo/mostro/mostro.db` è
leggibile solo con sudo — e sotto sudo, dentro le virgolette di python,
il percorso si scrive per esteso: `/home/debian/nodo/mostro/mostro.db`.

- La coda delle categorie si riempie da sola dopo ogni giro d'import
  (leva `RICATEGORIZZA_AUTO`, accesa di serie): nel journal la riga
  «🗂 Ricategorizzazione: N guardati, M proposte in coda», e ai
  moderatori arriva una notifica sola coi gruppi. Non cambia niente in
  vetrina finché un moderatore non approva. Per spegnerla, `False` nel
  config del VPS e riavvio.
- Le tre leve del P2P (`P2P_ATTIVO`, `MOSTRO_NPUB`, `MOSTRO_RELAY`) si
  AGGIUNGONO al config del VPS, non si «verificano» (set 2026, dal
  campo: la ricetta d'accensione diceva di controllare che npub e relay
  fossero quelli veri, e **non c'erano affatto**). Il config del VPS è
  un file suo e non eredita niente da `config_esempio.py`: una leva
  nuova lì dentro non compare mai da sola, e senza quelle due il server
  parte lo stesso e stampa la riga «P2P_ATTIVO ma MOSTRO_NPUB o
  MOSTRO_RELAY storti o assenti» — che è il primo posto da guardare se
  il P2P sembra acceso e non parla con nessuno. Vale per ogni leva
  aggiunta da un cantiere: il file d'esempio dice quale sia il valore
  giusto, non che quella riga esista di là.
- `MOSTRO_RELAY_SPECCHIO` (set 2026) e' la QUARTA leva del P2P e vale
  la stessa regola: si AGGIUNGE al config del VPS e serve un riavvio
  (la lista si legge all'import del modulo). Sono i relay da cui si
  LEGGE il libro senza parlarci — oggi `wss://relay.barattolo.store` —
  e NON si mettono in `MOSTRO_RELAY`: quella e' dove il coordinator
  ascolta, e il client la scorre anche per pubblicare le richieste di
  scambio (vedi Architettura, «LE DUE LISTE DEL P2P NON SONO UNA LISTA
  PIU' LUNGA»). Vuota o non dichiarata e' il mondo di ieri, byte per
  byte: il libro si legge dai soli relay del coordinator.
  Il pannello «⚙️ Stato delle leve» la mostra come «Specchi del
  libro», e il conto per relay di ogni lettura finisce nella console
  del client (`📖 [p2p] libro: ...=N`): e' li' che si vede uno
  specchio che ha smesso di aggiornarsi, perche' non fallisce — torna
  zero, e zero si legge come «oggi non c'e' nessun ordine».
- `MOSTRO_RELAY_CONFERMA` (12 ott 2026, voto-dopo-concluso) e' la
  QUINTA leva del P2P: i relay del coro il cui OK vale «partito». La
  pagina manda ogni messaggio per il coordinator a tutti i relay di
  `MOSTRO_RELAY`, e senza questa leva lo da' per partito al primo OK
  di chiunque — e un OK dice che quel relay ha preso l'evento, non che
  mostrod da li' lo legga. Si AGGIUNGE al config
  del VPS e serve un riavvio di barattolo (NON del nodo: il libro
  resta acceso); le voci devono stare anche in `MOSTRO_RELAY`, o non
  contano e il journal lo dice all'avvio («MOSTRO_RELAY_CONFERMA
  nomina relay che non stanno in MOSTRO_RELAY»). Il pannello «⚙️ Stato
  delle leve» la mostra come «Relay che confermano». Vuota o non
  dichiarata e' il mondo di ieri.
  COME SI SCEGLIE CHI CI VA: un relay ci sta solo se mostrod ci LEGGE,
  e si guarda in due modi — il suo journal sul nodo («Connected to
  relay …», niente «banned» o «rate-limit»), e la sonda in sola
  lettura da fuori: l'ultimo evento del coordinator su quel relay
  dev'essere di pochi minuti fa (il 38385 lo ripubblica di continuo).
  La sera del 12 ott 2026 (19:52 UTC) la sonda diceva, sulle ultime 6
  ore: `relay.mostro.network` fresco (8 ordini del libro, 99 risposte
  del coordinator, 19 richieste dei client); `relay.barattolo.store`
  uguale sul lato del coordinator ma con ZERO richieste dei client (il
  suo plugin accetta solo le chiavi in lista); `relay.damus.io` in
  parte (6 ordini, 59 risposte su 99: un limite di frequenza piu' che
  un muro — un'ora prima da qui non apriva nemmeno); `nos.lol` con le
  richieste dei client (19) ma NESSUN evento firmato dal coordinator
  piu' recente del 6 ott, di nessun tipo. ⚠️ QUEL CHE LA SONDA NON
  DICE: se mostrod da nos.lol LEGGE. Il suo journal quella sera lo
  dava collegato e accettato (17:31 UTC): un relay puo' prendere un
  evento e non conservarlo, e puo' consegnare le richieste a chi
  ascolta senza tenere le risposte. Per questo in lista va solo chi
  regge tutte e due le prove.
  LA SCELTA DI ANDREA (12 ott 2026): per ora un relay solo —
  `MOSTRO_RELAY_CONFERMA = ["wss://relay.mostro.network"]`, scritto
  identico a com'e' in `MOSTRO_RELAY`. I passi: 1) cosa c'e' gia',
  `grep -n "MOSTRO_RELAY" /srv/barattolo/config.py`; 2) la copia,
  `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-della-conferma`;
  3) la riga, `printf '\nMOSTRO_RELAY_CONFERMA = ["wss://relay.mostro.network"]\n' | sudo tee -a /srv/barattolo/config.py`;
  4) il controllo, `sudo -u barattolo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('config ok')"`;
  5) il riavvio di barattolo, e nel pannello delle leve la riga «Relay
  che confermano» accesa. ⚠️ Con un relay solo in lista, se quel relay
  cade OGNI gesto dice «Il messaggio non è partito» finche' non torna,
  anche quando un altro relay l'ha preso e a mostrod magari arriva: e'
  il verso prudente in cui sbagliare (chi legge riprova), ma va
  saputo. La seconda strada e' `relay.barattolo.store`, che oggi
  rifiuta i client: lo sistema un cantiere a parte (relay-per-mostro).
  TOGLIERE UN RELAY DAL CORO (il caso di damus, bannato per «too many
  rate-limit violations»): DUE TEMPI, e l'ordine conta. Primo, dal
  config del VPS: la riga `MOSTRO_RELAY` senza quel relay, riavvio di
  barattolo — da li' le pagine non ci mandano piu' niente e il suo OK
  non conta. Secondo, da `~/nodo/mostro/settings.toml` sul nodo, a
  LIBRO FERMO (`docker compose restart mostro` da `~/nodo`): si fa
  insieme a una salita d'immagine, non da solo.
- LE STATISTICHE DEL P2P (10 ott 2026): la sezione «🔁 Scambi P2P» in
  fondo al cruscotto `/admin` la vedono solo gli AMMINISTRATORI, e la
  leva `P2P_STATISTICHE_IDS` si AGGIUNGE al config del VPS: finche'
  manca, e' vuota o e' scritta male non la vede NESSUNO (403 a tutti,
  e all'avvio una riga `[p2p] P2P_STATISTICHE_IDS non e' una lista`
  solo se e' storta). Si guarda prima cosa c'e':
  `grep -n "P2P_STATISTICHE_IDS\|^ADMIN_IDS" /srv/barattolo/config.py`,
  poi si aggiunge la riga coi due id Telegram —
  `P2P_STATISTICHE_IDS = [id_di_andrea, id_di_alan]` — e
  `sudo systemctl restart barattolo`. Tutt'e due gli id devono stare
  ANCHE in `ADMIN_IDS`: la lista da sola non fa entrare nessuno. Il
  pannello «⚙️ Stato delle leve» dice quanti sono («Statistiche P2P:
  amministratori»), mai chi. IL REGISTRO `p2p_conti` nasce da solo al
  primo avvio (`CREATE TABLE IF NOT EXISTS`) e si riempie da solo: alla
  prima apertura della sezione e ogni ora, prima della scopa dei
  quaranta giorni. Se nel journal compare «⚠️ P2P: i conti non si sono
  consolidati» la scopa di quell'ora NON e' passata, apposta: la
  cronaca resta finche' i conti non sono in salvo, e si guarda perche'.
  IL ROUTING vuole il ponte di LND (`LND_PONTE_MACAROON_LETTURA`): senza,
  la sezione dice «non disponibile» e le commissioni nette non hanno
  una cifra. Coi perche': Architettura, «I CONTI DEL P2P».
- LA SOGLIA DELLE DISPUTE P2P (12 ott 2026): la card «⚖️ Dispute P2P»
  del cruscotto `/admin` la vedono tutti i moderatori e non vuole
  niente sul VPS. La percentuale e' sugli scambi CON LA GARANZIA
  BLOCCATA, non su tutte le prese. L'AVVISO su Telegram parte quando
  negli ultimi 30 giorni passa la leva `P2P_DISPUTE_SOGLIA_PERCENTO` (di
  serie 5) con almeno 3 dispute: uno per superamento, e si riarma
  quando la percentuale scende di un punto sotto. La riga nel config
  del VPS serve SOLO per cambiare il numero o spegnere (0): si guarda
  prima — `grep -n "P2P_DISPUTE_SOGLIA" /srv/barattolo/config.py` —, si
  scrive `P2P_DISPUTE_SOGLIA_PERCENTO = 8` e
  `sudo systemctl restart barattolo`. Una riga storta vale 5 e lo dice
  all'avvio (`[p2p] P2P_DISPUTE_SOGLIA_PERCENTO non e' un numero`). Il
  pannello «⚙️ Stato delle leve» dice il valore vivo («Soglia delle
  dispute P2P (%)»). Nel journal: «⚖️ P2P: dispute sopra la soglia,
  moderatori avvisati» quando parte; «⚠️ P2P: la soglia delle dispute
  non si è potuta guardare» se il conto alza (le attese e la scopa
  vanno avanti lo stesso). LE DISPUTE DA NON CONTARE (12 ott 2026):
  una disputa nata da un nostro bug o da una prova si toglie dalla
  percentuale e dall'avviso con la leva `P2P_DISPUTE_ESCLUSE`, che si
  AGGIUNGE al config del VPS — gli id degli ORDINI, interi o accorciati
  agli 8 caratteri del cruscotto. La prima: `ea0af71a`, la disputa nata
  dal bug delle chiavi perse su Tor. UN COMANDO ALLA VOLTA:
  1) cosa c'e' gia': `grep -n "P2P_DISPUTE" /srv/barattolo/config.py`;
  2) la copia di prima, fuori dalla cartella del servizio:
     `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-delle-escluse`;
  3) la riga in fondo (il `\n` davanti la tiene staccata dall'ultima):
     `printf '\nP2P_DISPUTE_ESCLUSE = ["ea0af71a"]\n' | sudo tee -a /srv/barattolo/config.py`
     — se al passo 1 la riga c'era gia', NON se ne aggiunge un'altra:
     si apre con `sudo nano /srv/barattolo/config.py` e si allunga la
     lista, `["ea0af71a", "altro-id"]`;
  4) che il file si legga ancora, PRIMA di riavviare:
     `sudo -u barattolo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('config ok')"`;
  5) `sudo systemctl restart barattolo`;
  6) `sudo journalctl -u barattolo --since "2 min ago" --no-pager | grep -E "P2P_DISPUTE|Traceback"`
     — NIENTE righe e' il buon segno; una riga `[p2p]
     P2P_DISPUTE_ESCLUSE non e' una lista di id d'ordine` vuol dire che
     e' scritta male e che NESSUNA disputa e' esclusa.
  Poi il pannello «⚙️ Stato delle leve» dice «Dispute P2P escluse dal
  conto: ea0af71a», e la card in fondo «Una disputa non contata per
  scelta». PER TORNARE INDIETRO:
  `sudo cp -p /root/config.py.prima-delle-escluse /srv/barattolo/config.py`
  e il riavvio. Un id piu' corto di 8 caratteri o con un carattere che
  in un id non c'e' fa cadere TUTTA la lista (si contano tutte): mai
  nascondere una disputa per sbaglio. La disputa esclusa resta per i
  moderatori dov'e' (la riga in `p2p_dispute` non si tocca).
  LA COLONNA `garanzia` DI `p2p_conti` (12 ott 2026) nasce da sola al
  riavvio dopo il deploy e si riempie da sola al primo giro dell'ora,
  per tutti gli scambi la cui cronaca c'e' ancora (quaranta giorni).
  Per guardarla, in sola lettura: `SELECT garanzia, COUNT(*) FROM
  p2p_conti WHERE esito IN ('completato','annullato','tornato') GROUP
  BY garanzia` — 1 = bloccata, 0 = no, -1 = non si sa (dedotta: sono
  quelle che la card conta in «per N scambi piu' vecchi la garanzia e'
  dedotta»). PER FARLO RISUONARE A MANO (dopo aver
  cambiato soglia, per esempio) si toglie il timbro, in sola scrittura
  di quella riga: `DELETE FROM timbri WHERE nome='soglia_dispute_p2p'`
  sul db vero (`/srv/barattolo/dati/satmarket.db`, con python3). COSA
  C'E' DENTRO, in sola lettura: `SELECT substr(ordine,1,8), giro,
  datetime(aperta_il,'unixepoch'), stato, esito, chiusa_da FROM
  p2p_dispute ORDER BY aperta_il` — se li' ci sono dispute di PROVA
  (le prove di fine settembre e della 0.19.0), contano in «da sempre»
  e nei 30 giorni finche' non ne escono: si guarda prima di fidarsi
  della percentuale. Coi perche': Architettura, «LE DISPUTE NEL
  CRUSCOTTO».
- LA MODIFICA DI PIÙ ANNUNCI INSIEME (16 ott 2026, leva
  `MODIFICA_MASSIVA_ATTIVA`; com'è fatta in ARCHITETTURA, «LA MODIFICA
  DI PIÙ ANNUNCI INSIEME»; perché in CANTIERI, «La modifica di più
  annunci insieme»). Nasce SPENTA: finché manca nel config del VPS il
  bottone «✏️ Modifica più annunci» non c'è e le quattro rotte
  `/api/me/modifica-massiva…` rispondono 404. PER ACCENDERLA, dopo la
  prova di Andrea: una riga nel `config.py` del VPS,
  `MODIFICA_MASSIVA_ATTIVA = True`, poi `sudo systemctl restart
  barattolo`. Solo `True` accende (una stringa resta spenta, e
  all'avvio il journal lo dice). La tabella del registro
  (`modifiche_massive`) nasce da sola al riavvio, niente di esistente
  toccato. Si verifica nel pannello «⚙️ Stato delle leve», riga
  «Modifica di più annunci insieme», e aprendo «📋 I tuoi annunci» da
  un account con almeno due annunci. Prima di accenderla si guarda
  che la riga non ci sia già, in sola lettura, la sola riga:
  `grep -n "^MODIFICA_MASSIVA_ATTIVA" /srv/barattolo/config.py`.
  Spegnerla = togliere la riga (o `False`) e riavviare: le modifiche
  già fatte restano, l'«↩︎ Annulla» sparisce con le rotte.
- PIÙ ACCOUNT OVUNQUE (16 ott 2026): la leva `PIU_ACCOUNT_OVUNQUE` nasce
  SPENTA nel codice e si AGGIUNGE al config del VPS solo dopo la prova di
  Andrea. Prima si guarda, in sola lettura, che non ci sia già:
  `grep -n "^PIU_ACCOUNT_OVUNQUE" /srv/barattolo/config.py`. Per accenderla
  una riga `PIU_ACCOUNT_OVUNQUE = True` nel `config.py` del VPS, poi
  `sudo systemctl restart barattolo`; per spegnerla si cancella la riga
  e si riavvia. Nessuna colonna da migrare (la tabella
  `account_insieme` nasce da sola all'avvio, vuota). Si verifica nel
  pannello «⚙️ Stato delle leve», gruppo «👥 Più account». A leva
  spenta resta il multi-account del web d'agosto, coi due guasti curati
  (la pastiglia nel Profilo e lo switch verso gli account nati con
  Nostr). Coi perché: Architettura, «PIÙ ACCOUNT OVUNQUE».
- LE LEVE DALLA PAGINA (27 ott 2026, cantiere leve-tutte): 182 leve su
  256 si cambiano dal pannello admin («⚙️ Apri la pagina delle leve»),
  e il valore scritto da lì VINCE sul `config.py` del VPS, anche dopo
  un riavvio e un deploy: chi legge il config per capire con che leve
  gira il server guarda anche la pagina (le piastrelle «✏️ Cambiate da
  qui»), o in sola lettura `sqlite3 /srv/barattolo/satmarket.db "SELECT
  chiave, valore FROM leve_pannello"`. Le 58 «mai» (segreti, indirizzi,
  serrature) restano SOLO nel config. IL FRENO A MANO, se un valore
  della pagina impedisse al server di partire: una riga
  `LEVE_PANNELLO_SPENTE = True` nel `config.py`, poi `sudo systemctl
  restart barattolo` — il server parte col solo config e la pagina dice
  che è spenta; si toglie la riga quando il valore storto è sistemato
  (dalla pagina, con «Torna al config»). Il backup delle leve è nella
  pagina (💾, file dal bot o testo) e dentro il backup cifrato del
  database. Coi perché: Cantieri, «Tutte le leve dalla pagina».
- ENTRA DAL BOT (19 ott 2026, cantiere account-doppio-bot): la leva
  `LOGIN_DAL_BOT` nasce SPENTA nel codice e si AGGIUNGE al config del VPS
  quando Andrea la vuole provare. Prima si guarda, in sola lettura, la
  sola riga: `grep -n "^LOGIN_DAL_BOT" /srv/barattolo/config.py`. Per
  accenderla una riga `LOGIN_DAL_BOT = True` nel `config.py` del VPS,
  poi `sudo systemctl restart barattolo`; per spegnerla si cancella la
  riga e si riavvia. VUOLE IL CAMPANELLO DEL BOT: con
  `TELEGRAM_WEBHOOK_SEGRETO` mancante o segnaposto la porta resta chiusa
  e sul web torna il widget (lo dice il pannello «⚙️ Stato delle leve»,
  gruppo «👥 Più account», riga «Entra dal bot»; il campanello lo dice
  la riga «🔔 Webhook Telegram» nel journal). Niente da migrare: gli
  ingressi vivono in memoria due minuti, e un riavvio perde solo quelli
  in volo (si ritocca «Entra con Telegram»). La prova dal vivo, dopo il
  deploy, sta nella voce del cantiere in CANTIERI. La stessa leva accende
  la porta anche sull'onion (lì col QR), senza altre righe. Coi perché:
  Architettura, «ENTRA DAL BOT».
- LE CARD P2P IN VETRINA (26 set 2026): la leva `P2P_IN_VETRINA` si
  AGGIUNGE al config del VPS come le altre, e finche' manca o e'
  `False` le card le vedono solo i moderatori e chi e' in
  `P2P_PROVA_IDS`. **IL GIORNO DEL LANCIO** sono due righe nel
  `config.py` del VPS, poi `sudo systemctl restart barattolo`:
  `P2P_PROVA_IDS = []` (o la riga cancellata) e
  `P2P_IN_VETRINA = True`. Tutt'e due: con qualcuno ancora nella fase
  di prova le card restano di chi prova anche a leva accesa. Solo
  `True` accende (una stringa «True» resta spenta, e all'avvio il
  journal lo dice). Si verifica nel pannello «⚙️ Stato delle leve»,
  riga «Card P2P in vetrina», e aprendo Esplora da un account qualunque.
  La fila legge `/api/p2p/libro` ogni 15 secondi (nessun relay dal
  telefono): se le card non si aggiornano, il primo posto e' la
  fotografia del server — `curl -s https://barattolo.store/api/p2p/libro
  | head -c 300` deve dire un `quando` recente — e poi il journal
  dell'orologio P2P. Un ordine nuovo compare entro 15 s se nasce da
  Barattolo (lo annuncia `/api/p2p/canale`, e il server rifa' la
  fotografia subito), entro un minuto e un quarto se nasce da un altro
  client di Mostro (il giro dell'orologio piu' quello della fila).
- GLI AVVISI DEL MERCATINO (9 ott 2026): tre leve, tutte col
  DEFAULT GIUSTO nel codice — `MERCATINO_AVVISI_NUOVI = True`,
  `MERCATINO_AVVISI_NUOVI_MINUTI = 60`, `MERCATINO_AVVISI_SEGUI_MINUTI
  = 15` — quindi sul VPS non c'è niente da aggiungere se vanno bene
  così; si AGGIUNGONO al config solo per cambiarle (riavvio: si leggono
  all'import). Il pannello «⚙️ Stato delle leve», gruppo «🆕 Avvisi del
  mercatino», le mostra vive. Nel journal un messaggio partito lascia
  «🆕 Nuovi annunci: N a <id>: mandato (…)» o «🔔 Venditore seguito: N
  annunci di <venditore> a <id>: mandato (…)»; a leva spenta non parte
  niente e le due rotte rispondono 409. La coda sta in
  `mercatino_avvisi_coda` (si pulisce da sola dopo un mese), i seguiti
  in `venditori_seguiti`.
- LA CARD «P2P IN ARRIVO» (30 set 2026): la prima card di «Da scoprire»
  dice a tutti «In arrivo il 10/10/26». La data e' la leva
  `P2P_IN_ARRIVO_FINO`, che vale «2026-10-10» NEL CODICE: col deploy la
  card c'e' senza toccare il config del VPS. **SE IL LANCIO SLITTA** si
  aggiunge al `config.py` del VPS `P2P_IN_ARRIVO_FINO = "AAAA-MM-GG"` e
  si riavvia; per toglierla, `P2P_IN_ARRIVO_FINO = None`. Una data
  storta la spegne (il journal lo dice all'avvio: «[p2p]
  P2P_IN_ARRIVO_FINO non e' una data»). **IL GIORNO DEL LANCIO NON SI
  TOCCA NIENTE IN PIU'**: con le due righe qui sopra (`P2P_PROVA_IDS =
  []` e `P2P_IN_VETRINA = True`) la card diventa da sola «Ora
  disponibile» e porta al P2P vero; 14 giorni dopo la data se ne va.
  Se la data passa col P2P ancora chiuso dice «In arrivo a breve». Si
  guarda nel pannello «⚙️ Stato delle leve», riga «Card «P2P in
  arrivo», data».
- LE PRESE DALLE 10 (9 ott 2026, la vigilia del lancio): la leva
  `P2P_PRESE_DA = "2026-10-10 10:00"` (ORA ITALIANA, Europe/Rome) si
  AGGIUNGE al `config.py` del VPS **OGGI, 9 OTT**, insieme ai tg_id in
  più in `P2P_PROVA_IDS`, poi `sudo systemctl restart barattolo`. Fino
  a quell'ora chi non è moderatore pubblica ma non prende né annulla
  (i bottoni restano, spenti, e dicono «Dalle 10:00 di domani»), e
  senza un ordine vivo suo nel libro vede il foglio «Pubblica» al posto
  del libro, con la riga «Per entrare oggi pubblica il tuo primo
  ordine». I moderatori (`ADMIN_IDS`) non la vedono: per loro tutto
  com'è oggi. PASSATA L'ORA LA LEVA È INERTE DA SOLA — l'orologio si
  legge a ogni richiesta — quindi il 10 alle 10:00 non si riavvia per
  lei: si fanno le due righe del lancio scritte sopra (`P2P_PROVA_IDS
  = []` e `P2P_IN_VETRINA = True`) e **la riga `P2P_PRESE_DA` si
  TOGLIE dal config DOPO il 10**, con comodo, al primo riavvio utile.
  Assente o vuota = nessun blocco; un'ora storta non blocca niente e il
  journal lo dice all'avvio («[p2p] P2P_PRESE_DA non e' un'ora»). Si
  guarda nel pannello «⚙️ Stato delle leve», riga «Prese P2P dalle (ora
  italiana)», che dice anche quando l'ora è passata. ⚠️ Il server non ha
  rotte di presa o annullo (take-sell, take-buy e cancel vanno dal
  browser al coordinatore): la leva viaggia nella busta delle leve
  (`preseDa`) e i bottoni li spegne il client di Barattolo — chi usasse
  un altro client di Mostro sullo stesso libro non la vedrebbe.
- LA CAMPAGNA P2P A TUTTI (9 ott 2026, la vigilia del lancio): la leva
  `P2P_CAMPAGNA_TUTTI = True` si AGGIUNGE al `config.py` del VPS insieme
  alle due righe del lancio (`P2P_PROVA_IDS = []` e `P2P_IN_VETRINA =
  True`), poi `sudo systemctl restart barattolo` — DOPO le 10:00 del 10
  ott, non prima (vedi «LE PRESE DALLE 10»). Al primo giro dell'orologio
  (pochi secondi dopo l'avvio), col P2P aperto a tutti, parte UNA volta
  sola un messaggio a ogni iscritto — Telegram o DM Nostr, il canale di
  ognuno — TRANNE chi aveva premuto «Avvisami», che riceve quello della
  campagna di sempre. Gira in sottofondo, 0,2 s di pausa a persona (mille
  iscritti ≈ 5-7 minuti): **in quei minuti non si riavvia** — un riavvio a
  metà ferma gli invii, e il timbro (scritto PRIMA del primo invio) non
  li fa ripartire. Nel journal: «🔄 Campagna P2P a tutti: parte verso N
  iscritti», una riga «saltato <id> (…)» per chi non riceve (il 403 di
  chi ha bloccato il bot è normale) e alla fine «finita — inviati N,
  saltati M». Il pannello «⚙️ Stato delle leve», riga «Campagna P2P a
  tutti», dice «già partita» quando il timbro `campagna_p2p_tutti` è
  scritto: da lì la riga nel config si toglie con comodo. Una stringa
  «True» resta spenta, e il journal lo dice all'avvio («[p2p]
  P2P_CAMPAGNA_TUTTI non e' True/False»).
- LE LEVE RGB E IL NIP-05 DI CASA (8 ott 2026, hackathon di Torino):
  `RGB_ATTIVO`, `RGB_PROVA_IDS` e `NIP05_NOMI` si AGGIUNGONO al config
  del VPS come le altre. Nel codice `RGB_ATTIVO` e' `False` e resta
  spenta FINO A TORINO: a leva spenta nessuna rotta `/api/rgb/*`
  risponde (oggi non ne esiste nessuna). `NIP05_NOMI` e' l'unica che
  serve PRIMA del 17: senza, `https://barattolo.store/.well-known/
  nostr.json` risponde `{"names": {}}` (200, non 404: e' «qui
  nessuno»). Si aggiunge `NIP05_NOMI = {"usdb": "<hex>", "tothemooon":
  "<hex>"}` con le chiavi PUBBLICHE in esadecimale minuscolo (le da'
  `node identita.mjs pubblica <nome>` nel WSL del portatile: MAI una
  nsec, MAI una npub — il NIP-05 vuole l'hex) e si riavvia; una riga
  storta si scarta all'avvio e il journal lo dice («[nip05] «nome»:
  … scartato»). Si verifica con `curl -s
  "https://barattolo.store/.well-known/nostr.json?name=usdb"` (la hex
  di usdb, `Access-Control-Allow-Origin: *`, nessun Location) e nel
  pannello «⚙️ Stato delle leve», gruppo «🪙 Punti e dollari su RGB
  (hackathon)». Il verbale: CANTIERI, «Hackathon: la chiusura della
  preparazione»; la lista: HACKATHON-SETUP §10-11. DAL 16 NOV 2026 la
  rotta non risponde più vuota anche senza la riga: i nomi `_` e
  `barattolo` (l'account ufficiale, `_@barattolo.store` nel suo campo
  nip05) stanno nel codice, `NIP05_DI_CASA`; una `NIP05_NOMI` nel
  config si AGGIUNGE a quelli e vince solo sullo stesso nome. Si guarda
  con `curl -s "https://barattolo.store/.well-known/nostr.json?name=_"`.
- LA CASSA DI RISONANZA SU X (9 ott 2026): i post di Barattolo su Nostr
  — le note kind 1 ORIGINALI della npub ufficiale, niente risposte né
  repost, mai le promo degli annunci che firma il server, mai i
  prodotti uno per uno — escono anche su X, ripubblicati dal server
  con l'API ufficiale (v2, contesto utente OAuth 1.0a). Le leve si
  AGGIUNGONO al config del VPS come le altre; nel codice nascono tutte
  spente. Il verbale: CANTIERI, «La cassa di risonanza su X».
  **I PREZZI E I LIMITI DI X**, letti su docs.x.com il 9 ott 2026
  (`x-api/getting-started/pricing`, `x-api/fundamentals/rate-limits`,
  `x-api/media/introduction`): niente piano gratuito, si comprano
  CREDITI nella Developer Console e ogni richiesta li scala;
  «Post: Create» 0,015 $ a richiesta, «Post: Create (with URL)» 0,200 $
  (tredici volte tanto: per questo i post escono SENZA link), le
  letture non ci servono; il caricamento dei media non è nel listino
  («Media Metadata» 0,005 $ è un'altra chiamata, che non facciamo). I
  limiti: POST /2/tweets 100 ogni 15 minuti per utente e 10.000 al
  giorno per app; i media 1.875 ogni 15 minuti per passo
  (initialize/append/finalize). Le foto fino a 5 MB (JPG, PNG, WEBP;
  GIF 15 MB), al più 4 per post; i video con l'upload a pezzi (pezzi
  da 4 MB, X ne accetta fino a 5), fino a 20 minuti e 8 GB per un
  account senza Premium (125 minuti e 16 GB con Premium), uno per post
  e mai insieme alle foto; qui il nostro tetto è 256 MB. Oltre i
  limiti X risponde 429 (`x-rate-limit-reset` dice quando): il server
  riprova dopo 5, 15 e 45 minuti, poi lascia la nota e va avanti.
  Prezzi «soggetti a cambiare»: si riguardano nella console
  (`console.x.com`, Billing) e nel pannello, che dice la spesa stimata
  del mese.
  **1) L'APP SU X** (console.x.com, l'ex developer.x.com): si entra con
  l'account X di Barattolo, si accetta il Developer Agreement, «Create
  App» con nome, descrizione e caso d'uso («ripubblicare i post del
  nostro progetto»). Nelle impostazioni dell'app, «User authentication
  settings»: App permissions = **Read and Write** (non serve «Direct
  Messages»), Type of App = Web App / Automated App or bot, callback
  `https://barattolo.store` e website `https://barattolo.store` (il
  callback non si usa, ma il modulo lo vuole). ⚠️ I token generati
  PRIMA di mettere Read and Write restano in sola lettura: si cambia
  il permesso e POI si generano (o rigenerano) i token.
  **2) IL CREDITO**: Billing → Payments → «Add payment method» (una
  carta), poi Billing → Credits e si compra il minimo (5 $: a 0,015 $
  a post sono trecento post). L'auto-ricarica si lascia SPENTA, e si
  mette uno **Spending limit** mensile basso (10 $): a un bug che
  pubblicasse in loop si vuole trovare la porta chiusa. Il 9 ott 2026
  la console promette un credito regalo di 20 $ alla prima carta
  salvata, «in rollout»: si guarda, non ci si conta.
  **3) LE QUATTRO CHIAVI**, da «Keys and tokens» dell'app: **API Key** e
  **API Key Secret** (la coppia «Consumer Keys») e **Access Token** e
  **Access Token Secret** (sotto «Authentication Tokens», generati per
  l'account che pubblicherà: Barattolo). Si mostrano UNA volta sola:
  si copiano subito nel config del VPS, a mano, mai in chat. Il Bearer
  Token e la coppia OAuth 2.0 (Client ID/Secret) NON servono. Nel
  `config.py` del VPS si aggiungono:
  `X_API_KEY = "INCOLLA_QUI…"`, `X_API_SECRET = "INCOLLA_QUI…"`,
  `X_ACCESS_TOKEN = "INCOLLA_QUI…"`, `X_ACCESS_SECRET = "INCOLLA_QUI…"`
  (coi valori veri al posto del segnaposto; `chmod 600` del config è
  già così). Una chiave finita in chat o in un log si RIGENERA dalla
  console (le vecchie muoiono all'istante).
  **4) PRIMA IN PROVA**: `X_RIPUBBLICA = True` e `X_PROVA = True`, `sudo
  systemctl restart barattolo`. Il journal dice «🐦 X: cassa di
  risonanza ACCESA in PROVA (X non viene chiamato)» e, al primo giro,
  «si parte da adesso — le note di prima non si ripubblicano». Si
  pubblica una nota da un client Nostr con la npub ufficiale, e entro
  cinque minuti (`X_GIRO_S`) il journal dice «🐦 [X prova] per la nota
  … avrei pubblicato (N foto, stima 0,015 $): «testo»». Si guarda il
  testo (il taglio a 280, gli URL delle foto tolti) e il pannello «⚙️
  Stato delle leve», gruppo «🐦 Cassa di risonanza su X». Una nota
  raccontata in prova resta segnata e NON esce quando si accende.
  **5) POI SI ACCENDE**: `X_PROVA = False` (o la riga via), riavvio. Il
  journal dice «ACCESA — note — senza link», e per ogni post «🐦 X:
  pubblicato il post <id> per la nota … — stima 0,015 $, totale del
  mese 0,030 $». Un no di X è una riga «🐦 X: … riprovo fra 5 min» o
  «resta su Nostr e basta: si va avanti», mai un server fermo. Per
  vedere il post: `https://x.com/i/status/<id>`.
  **LE ALTRE DUE LEVE**: `X_CON_LINK = True` aggiunge a ogni post il link
  njump alla nota (0,200 $ invece di 0,015 $: si accende sapendolo);
  `X_RIEPILOGO_GIORNO = True` manda alle 18 (ora italiana) UN post
  «🫙 Nuovi arrivi di oggi nel mercatino: N annunci» con fino a 4 foto
  e senza link — i prodotti non escono in nessun'altra forma. **PER
  SPEGNERE TUTTO**: `X_RIPUBBLICA = False` (e il riepilogo) e riavvio;
  le righe di `x_post` restano, nessun doppione quando si riaccende.
  La prima accensione non ripubblica mai il passato: la lancetta
  `x_dal` sta in `impostazioni` e per ripartire «da adesso» dopo un
  lungo spegnimento la si cancella (`DELETE FROM impostazioni WHERE
  chiave='x_dal'`) prima del riavvio.
- LE NOTIFICHE PRECISE DEL P2P (16 set 2026) non hanno una leva loro:
  girano con `P2P_ATTIVO`, dentro lo stesso orologio del campanello,
  e leggono il libro dai relay del coordinator e poi dallo specchio.
  Nel journal: `📖 Libro P2P: avvisati N [...]` quando parte una frase,
  `⚠️ Libro P2P: battito saltato (...)` se un giro muore (il prossimo
  riparte da solo), e `📖 Libro P2P: stato mai visto «...»` il giorno
  che il coordinator ripubblica uno stato che non abbiamo ancora visto
  (`expired`, `dispute`, gli esiti dell'admin): quella riga e' la
  richiesta di riguardare `_passaggio_libro_p2p` con lo stato vero
  davanti. Al primo riavvio dopo il deploy il server aggiunge da solo
  le quattro colonne a `p2p_ordini` e `avvisi_p2p` a `utenti`
  (ALTER TABLE, come tutte le colonne nuove): niente da fare a mano.
- «AVVISATI N» NON VUOL DIRE ARRIVATO (17 set 2026): quella riga
  conta chi si e' PROVATO ad avvisare. L'esito sta nelle righe subito
  sotto, una per destinatario: `   📖 ↳ 700000001: telegram ok
  (messaggio 8841)` — il numero e' la ricevuta di Telegram —, oppure
  `telegram 403: non ha avviato il bot, o l'ha bloccato`, `telegram
  400: NON arrivato — …chat not found`, `DM Nostr in volo e NIENTE
  Telegram (canale scelto: «nostr»)`, `NESSUN CANALE (…)`.
  DAL CHAT ID ALL'ACCOUNT: in una chat privata il chat id E' il
  `tg_id`, quindi sul VPS, in sola lettura:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT tg_id, nome, username, canale_notifiche, avvisi_p2p FROM utenti WHERE tg_id IN (<id1>, <id2>)\")]"`
  — la colonna `canale_notifiche` e' quella da guardare per prima:
  `nostr` vuol dire che sul bot non arriva niente PER SCELTA.
  IL BOT E' UNO SOLO: mercatino e P2P passano dalla stessa `notifica`
  e dallo stesso `BOT_TOKEN`.
  CHI TACE LO DICE: `🔕 … ha gli avvisi P2P SPENTI (cassetto Avvisi)`
  quando a fermare un invio e' l'interruttore, `⏳ Campanello P2P: … e'
  nel gate (ultimo avviso Ns fa, pausa Ps)` quando e' la pausa.
  LA PROVA VERA DEL TRASPORTO, sul VPS:
  `cd /srv/barattolo && python3 prova_notifica.py <chat_id>` — fa la
  stessa `sendMessage` del server con lo stesso token (che non stampa
  mai) e mostra la risposta di Telegram cosi' com'e'; prima dice CHI
  e' quel chat id (`getChat`: nome e username, se ha avviato il bot).
- L'OROLOGIO P2P NEL JOURNAL (17 set 2026): «non gira» e «gira a
  vuoto» adesso si distinguono, e si guarda cosi':
  `journalctl -u barattolo --since "10 min ago" | grep -E "P2P|Libro|Campanello"`.
  Le righe: `▶️ Orologio P2P partito: …` a ogni avvio, coi relay;
  `· P2P passata N: libro — … ; campanello — … (1.2s)` UNA AL MINUTO
  anche a vuoto (si spegne con `P2P_LOG_PASSATE = False` nel config),
  e fra quadre CHI HA DATO COSA: `[relay.mostro.network 0 ·
  relay.damus.io ✗ · nos.lol 2 · relay.barattolo.store 2]` — `✗` non
  ha risposto, un numero sono gli eventi che ha dato. ⚠️ UNO ZERO
  ACCANTO A UN NUMERO e' un relay che risponde ma e' rimasto indietro:
  dal 17 set non fa piu' danno (si chiede a tutti e si unisce), ma se
  dura e' da guardare sul nodo — mostrod non riesce a scriverci. Sul
  campanello lo specchio dice sempre 0: i kind 14 non li copia;
  `🔇 P2P: il relay … non risponde (…)` e `🔊 … e' tornato a
  rispondere`, al CAMBIO e non a ogni giro; `⚠️ … passata oltre 240s,
  abbandonata` e `⚠️ … battito saltato (Tipo: …)` quando una passata
  si appende o esplode — la successiva riparte dal segnalibro; e le
  due del guardiano, `💥 Orologio P2P MORTO (…): riparte adesso` e
  `⚠️ Orologio P2P FERMO da Ns: lo annullo`. ⚠️ SE PER PIU' DI DUE
  MINUTI NON C'E' NESSUNA «· P2P passata», l'orologio non gira: e' la
  domanda da fare per prima, e se capita con questo codice la riga del
  guardiano deve comparire entro dieci minuti — se non compare nemmeno
  quella, e' fermo l'intero processo e non il P2P.
  Le righe gia' in tabella prendono lo stato alla PRIMA ripubblicazione
  del loro ordine, senza frase: l'orologio non ha visto il passaggio
  e non lo inventa.
- (⚠️ DELL'ECO QUI SOTTO NON RESTA NIENTE dal 18 set 2026, patch 0007: via
  le righe «ECO del suo gesto» e «busta nata PRIMA», e le «Novità» della
  prova dal vivo. Le righe del RECAPITO restano, con un perché in più:
  «non e' una delle due parti (secondo il coordinatore | i due
  telefoni)». Vedi in fondo, «GLI AVVISI P2P DAL COORDINATORE».)
- L'ECO E IL RECAPITO NEL JOURNAL (18 set 2026, terzo giro). Cinque
  colonne nuove nascono da sole al riavvio (ALTER): `chiavi_p2p.gesto`
  e `.eco_fino`, `p2p_ordini.euro`, `.recapito_avviso` e
  `.recapito_n`. Le righe nuove: `· Campanello P2P: N, ECO del
  suo gesto (Ns dopo): non suona` — la risposta a un gesto appena fatto
  da N, che prima dava «RIMANDATO» o una «Novità»; `· Campanello P2P:
  N, busta nata Ns PRIMA del suo ultimo gesto su quello scambio: gia'
  vista`; `💶 Recapito P2P: N ha indicato dove ricevere gli euro,
  avvisato M` con sotto l'esito di Telegram; e `· Recapito P2P: da N,
  nessun avviso (perche')` — il perche' e' scritto per intero («non e'
  chi vende», «l'ordine sul libro e' …, non preso», «l'altra parte non
  e' annotata», «M ha gli avvisi P2P spenti»). Dal 7 ott 2026 il tetto
  dei dieci avvisi del recapito ha una riga SUA, `⛔ Recapito P2P: da N,
  sull'ordine …: TETTO ANTI-ABUSO: …` (`journalctl -u barattolo | grep
  "⛔ Recapito P2P"`), e la pausa fra un avviso e l'altro non c'è più:
  ogni cambio del recapito avvisa chi compra. ⚠️ I «Ns dopo» dell'eco sono il NUMERO DA
  GUARDARE: se stanno spesso vicino a 30, la finestra (`P2P_ECO_S`) e
  l'attesa del client (`P2P_ATTESA_MS`) si allungano INSIEME — una
  prova le tiene uguali.
  LA PROVA DAL VIVO, con due account (A compra e pubblica, B vende e
  prende): `journalctl -u barattolo -f | grep -E "Campanello|Libro|Recapito|📬|⏳"`.
  Deve dire: alla pubblicazione di A un «ECO» e nessuna Novità; alla
  presa `📖 Libro P2P: avvisati 2`; B apre il foglio e paga — un «ECO»
  per B, e ad A la «Novità» (dove vuoi i sats); A da' la fattura — un
  «ECO» per A, e a B la «Novità»; B indica dove ricevere gli euro —
  «💶 Recapito P2P … avvisato A», e sul telefono di A «B ti ha
  indicato dove inviare 10,00 €: tocca a te»; A segna gli euro — «ECO»
  per A, «Novità» a B; B rilascia — «ECO» per B, e il concluso a
  tutt'e due. Sui telefoni, ad app APERTA: a B dopo «vendi» il velo
  «Sto preparando la garanzia…» e poi la richiesta da pagare che si
  apre da sola; ad A, a garanzia bloccata, il foglio «dove ricevere i
  sats» che si apre da solo; ad A, a scambio attivo, il bottone «Ho
  inviato gli euro» SPENTO con «Aspetta che B ti indichi…» finche' il
  recapito non arriva, poi acceso col toast.
- (⚠️ TOLTO il 18 set 2026 dalla patch 0007: il gate, la coda e le righe
  qui sotto non esistono più. Resta a verbale com'era. Vedi in fondo,
  «GLI AVVISI P2P DAL COORDINATORE».)
- IL GATE CHE RIMANDA NEL JOURNAL (18 set 2026). Al posto del vecchio
  «e' nel gate … non suona» ci sono tre righe: `· Campanello P2P: N,
  busta gemella della frase precisa (Ns dall'evento del libro): gia'
  detta` — la busta dello stesso istante di una frase del libro, che
  non deve suonare; `⏳ Campanello P2P: N e' nel gate (ultimo avviso
  Ns fa, pausa Ps): RIMANDATO, parte fra Ns in un avviso solo`; e,
  alla scadenza, `📬 Campanello P2P: N, finita la pausa (Ps): parte
  l'avviso rimandato…` seguita dal solito «🔔 avvisati» con l'esito.
  Nella riga della passata il campanello dice `… N avvisi (M dalla
  coda), K in coda`. Le colonne nuove (`chiavi_p2p.coperto`,
  `.rimandato`) nascono da sole al riavvio (ALTER). ⚠️ UN «⏳
  RIMANDATO» SENZA IL SUO «📬» DOPO LA PAUSA (90 s con uno scambio
  preso, 600 senza) e' il difetto da guardare: la coda si scarica a
  ogni passata e l'orologio si sveglia apposta alla scadenza.
  LA PROVA DAL VIVO, con due account (come il collaudo del 17 set): A
  pubblica una VENDITA, B la prende e dà subito dove ricevere i sats,
  A blocca la garanzia, B segna «euro inviati», A rilascia. Intanto:
  `journalctl -u barattolo -f | grep -E "Campanello|Libro|📬|⏳"`.
  Deve dire: alla presa `📖 Libro P2P: avvisati 2` e due «busta
  gemella»; alla fattura di B un «⏳ … RIMANDATO» per A (e uno per B,
  l'eco del suo gesto) e poi il «📬» entro un minuto e mezzo; al
  rilascio `📖 … avvisati 2` con «Scambio concluso». Sui telefoni: B
  legge «Hai preso l'ordine di <nome di A>!», A riceve la «Novità»
  quando tocca a lui bloccare, e al concluso A legge «in tutto N sats,
  commissione compresa» e B il suo netto. Per lo SCADUTO: un ordine
  pubblicato e lasciato scadere (il tabacchino vive 48 ore) deve dare
  «⏰ Il tuo ordine è scaduto senza che la presa fosse completata».
- (⚠️ DAL 18 SET 2026, patch 0007, L'ASCOLTO PORTA IL SOLO LIBRO e lo
  specchio il kind 14 non lo copia più: `router.conf` della repo ha i
  due kind pubblici, e sulla macchina del relay va sostituito — punto
  10 di «GLI AVVISI P2P DAL COORDINATORE», in fondo. Le righe
  dell'ascolto qui sotto valgono ancora, per il 38383.)
- L'ASCOLTO P2P E IL 14 SULLO SPECCHIO (17 set 2026). Nel journal del
  VPS: `👂 Ascolto P2P: parte su …`, `👂 Ascolto P2P connesso a …`,
  `👂 Ascolto P2P CADUTO (perche'): riprovo…` e `… connesso … dopo N
  tentativi` AL CAMBIO; `⚡ P2P lampo N (dall'ascolto): …` a ogni
  mazzetto; in coda alla riga della passata `ascolto — connesso da …,
  N eventi vivi, polso Ns fa` oppure `GIU' da … (N tentativi): …`; e
  `⚠️ Ascolto P2P: … l'ha trovato il giro al minuto e NON l'ascolto`
  quando lo specchio non ha avuto un evento che i relay pubblici
  avevano. ⚠️ Un polso piu' vecchio di un minuto con lo stato
  «connesso» non deve esistere: il filo si dichiara caduto prima.
  LA RIGA SUL RELAY (macchina del relay, `/opt/relay`), una volta:
  `cd /opt/relay && cp router.conf router.conf.prima-del-14`, poi
  `sed -i 's/"kinds": \[38383, 38385\]/"kinds": [38383, 38385, 14]/' router.conf`,
  si guarda con `grep -n '"kinds"' router.conf` (una riga, tre kind,
  UN autore), e `docker compose up -d --force-recreate specchio` — COL
  NOME DEL SERVIZIO, che un `up -d` nudo ricrea anche il relay vivo.
  Poi `docker compose logs --tail 20 specchio` (le tre connessioni ai
  relay del coordinator, nessun errore di config). La copia nel repo
  (`deploy/relay/router.conf`) e' gia' aggiornata, commenti compresi.
  LA VERIFICA CHE I KIND 14 ARRIVANO, dopo il prossimo messaggio di
  mostro (una presa, una pubblicazione):
  `docker compose -f /opt/relay/compose.yml exec relay strfry scan '{"kinds":[14],"authors":["HEX"],"since":EPOCH}' | jq -r '[.created_at, .id[0:8], (.tags[]|select(.[0]=="p")|.[1][0:8])] | @tsv'`
  (HEX = la chiave del coordinator, quella di `router.conf`; EPOCH =
  `date -d '10 min ago' +%s`)
  — righe = arrivano (mai il `content`: il filtro di jq non lo
  stampa). E dal lato di chi legge, sul VPS: spariscono i «NON
  l'ascolto» sui kind 14 e compaiono i lampi con `buste portate`.
  PER TORNARE INDIETRO: `cp router.conf.prima-del-14 router.conf` e lo
  stesso `up -d --force-recreate specchio`; i kind 14 gia' copiati
  restano nel db finche' non si tolgono con `strfry delete` — e la
  pagina «I tuoi dati» va riportata alla frase di prima.
- MOSTRO SCRIVE DIRETTAMENTE SULLO SPECCHIO (17 set 2026). Tre
  macchine in un gesto solo, e **l'ORDINE CONTA**: prima la whitelist,
  poi il nodo. Al contrario mostrod si prende un «restricted: solo
  Barattolo e i suoi venditori» per ogni evento, e a dirlo c'e' solo
  il suo journal.
  **1) IL VPS DI BARATTOLO** (deploy automatico, niente da fare a
  mano): la rotta `/api/relay/chiavi` mette la chiave del coordinator
  in lista da se', letta da `MOSTRO_NPUB`. Basta che quella riga e
  `RELAY_CHIAVI_TOKEN` ci siano nel config — si guarda dal pannello
  «⚙️ Stato delle leve», che chiede al valore VIVO.
  **2) LA MACCHINA DEL RELAY**, per non aspettare il timer dei dieci
  minuti — e la verifica, che non ha bisogno di sapere la hex a
  memoria (la prende da `router.conf`, dove vive gia'):
  `sudo systemctl start barattolo-chiavi.service`
  `HEX=$(grep -o '[0-9a-f]\{64\}' /opt/relay/router.conf | head -1); wc -l < /opt/relay/policy/chiavi.txt; grep -qx "$HEX" /opt/relay/policy/chiavi.txt && echo "coordinator IN LISTA" || echo "NON c'e'"`
  Il relay NON si riavvia: il plugin rilegge il file quando cambia
  l'mtime. Se dice «NON c'e'», il guasto e' sul VPS (deploy non
  passato, o una delle due leve mancante) e
  `journalctl -u barattolo-chiavi -n 20` dice quale: `aggiorna-chiavi.sh`
  in caso di dubbio TIENE LA LISTA DI IERI e lo scrive.
  **3) IL NODO, prima di toccare niente**: che il relay risponda
  DALLA STRADA DI MOSTRO, cioe' da Tor. E' un NIP-11, una riga:
  `docker run --rm --pull never --network container:nodo-mostro-1 curlimages/curl -s -m 30 -o /dev/null -w '%{http_code} %{time_appconnect}s\n' -H 'Accept: application/nostr+json' https://relay.barattolo.store`
  200 = passa (⚠️ si guarda `time_appconnect`, che `time_connect`
  mente sotto il proxy trasparente). `000` o `403` = non si tocca
  `settings.toml`: e' la stessa forma del difetto della dev fee.
  **4) LA RIGA**, in `~/nodo/mostro/settings.toml`. Prima si guarda
  com'e' scritta oggi, che la copia nel repo non c'e':
  `grep -n -A10 '^\[nostr\]' ~/nodo/mostro/settings.toml`
  poi la copia di sicurezza — `cp settings.toml settings.toml.prima-dello-specchio`
  — e lo specchio si AGGIUNGE in testa, senza togliere niente:
  ```toml
  relays = [
      "wss://relay.barattolo.store",
      "wss://relay.mostro.network",
      "wss://relay.damus.io",
      "wss://nos.lol",
  ]
  ```
  ⚠️ IN AGGIUNTA E NON AL POSTO, ed e' una scelta: `relay.mostro.network`
  e' la piazza pubblica dove i client altrui ci trovano, e un ordine
  nato da un client esterno col nostro coordinator e' lavoro nostro
  (la hold invoice sta sul nostro nodo, l'1% lo incassiamo noi).
  Costa una connessione; toglierlo si puo' sempre, ed e' una riga.
  **5) IL RIAVVIO**, come per la patch 0004 e per i provider del
  prezzo: `cd ~/nodo && docker compose restart mostro` — dal COMPOSE,
  che `docker restart mostrod` risponde «No such container» (il
  servizio si chiama `mostro`, il container `nodo-mostro-1`). Poi
  `docker compose logs --tail 40 mostro`: «Settings correctly loaded»
  e le righe «Connected to relay», la nostra compresa.
  **6) LA PROVA CHE SCRIVE DAVVERO, e non che il libro e' arrivato**
  — sono due cose diverse, perche' il router copia gli stessi eventi e
  un 38385 fresco sullo specchio non dice da quale delle due strade e'
  entrato. Si spegne il router per il tempo della prova, e allora
  resta una strada sola. Sulla macchina del relay:
  `cd /opt/relay && docker compose stop specchio`
  poi sul nodo il riavvio del punto 5 (all'avvio mostrod ripubblica il
  suo 38385), poi di nuovo sul relay, entro un minuto:
  `docker compose -f /opt/relay/compose.yml exec relay strfry scan "{\"kinds\":[38385],\"since\":$(date -d '2 min ago' +%s)}" | jq -r '[.created_at, .id[0:8]] | @tsv'`
  Una riga = mostrod ha scritto QUI, di suo. ⚠️ NESSUNA RIGA NON E'
  ANCORA UN NO: il 38385 lo ripubblica mostrod quando decide lui
  (stessa trappola gia' scritta per `hold_invoice_cltv_delta`: «se
  dice ancora il vecchio numero, non ha ancora ripubblicato»). Prima
  si guarda il suo journal — «Connected to relay
  wss://relay.barattolo.store» dice che il filo c'e', un «restricted»
  dice che la whitelist non e' arrivata — e si riprova allargando il
  `since`. Un `no such container` o un silenzio totale sono altri due
  guasti, e non questo.
  Poi si riaccende il router: `docker compose up -d specchio` — COL
  NOME DEL SERVIZIO, che un `up -d` nudo ricrea anche il relay vivo.
  I minuti col router fermo non dovrebbero perdersi: alla riconnessione
  rifa' la REQ, che non porta nessun `since` — ma e' ricavato dal
  filtro, non misurato (vedi CANTIERI, punto 5 del «resta da
  guardare»), e in questa finestra la scrittura diretta copre comunque.
  **7) E DAL LATO DI CHI LEGGE**, nel journal del VPS: spariscono i
  «⚠️ Ascolto P2P: … NON l'ascolto» (erano il segno che lo specchio
  arrivava dopo i relay pubblici) e i lampi restano con `buste
  portate`.
  **PER TORNARE INDIETRO**: `cp settings.toml.prima-dello-specchio
  settings.toml` e lo stesso `restart mostro`. La chiave in
  `chiavi.txt` puo' restare: permette, non obbliga — e al giro dopo
  la rotta la rimette comunque.
- COME SI LEGGE COSA HA FATTO IL COORDINATOR DI UNA RICHIESTA (15 set
  2026, dal silenzio sull'ordine di Alan). Tutto in sola lettura, e in
  ORDINE: prima si cerca la richiesta, poi la risposta, poi il perché.
  1) Sulla macchina del relay (`/opt/relay`): l'evento del client è un
  kind 14 con tag `p` verso il coordinator, e la risposta è un kind 14
  FIRMATO dal coordinator. Con l'ora del tentativo in `since` (epoch),
  senza bisogno di sapere la hex:
  `docker compose -f /opt/relay/compose.yml exec relay strfry scan
  '{"kinds":[14],"since":EPOCH}' | jq -r '[.created_at, .pubkey[0:8],
  (.tags[]|select(.[0]=="p")|.[1][0:8])] | @tsv'` — la `p` più
  frequente è il coordinator; una riga con QUELLA come `pubkey` è una
  risposta. Richiesta senza risposta = il guasto è sul nodo; nessuna
  richiesta = il guasto è sul client (o sulla publish).
  2) Sul nodo (`~/nodo`, servizio `mostro`), la finestra del
  tentativo, tolto il rumore della dev fee:
  `cd ~/nodo && docker compose logs --timestamps --since
  2026-09-15T00:00:00 mostro | grep -v "unpaid dev fees\|NoAPIResponse"
  | grep -iE "order|warn|error|invalid|rate|spam|quote|yadio|signature|
  relay|connect" | tail -n 200`. Le righe che contano: «Invalid
  signature»/«verification» (busta scartata, nessuna risposta per
  scelta), «Invalid trade index» (ma quella risponde `cant-do`),
  «quote»/«yadio» con un errore (il cambio non è arrivato: su un ordine
  a prezzo di mercato mostrod NON registra e NON risponde), e le
  «Connected to relay» dopo un riavvio (se il tentativo è caduto
  prima, l'evento è passato e nessuno l'ha letto).
  3) Il cambio DAL NAMESPACE DI RETE DEL CONTAINER, cioè dalla stessa
  strada Tor che fa mostrod:
  `docker run --rm --network container:nodo-mostro-1 curlimages/curl
  -s -m 30 -o /dev/null -w '%{http_code} %{time_appconnect}s\n'
  https://api.yadio.io/exrates/EUR` — 200 sotto i 4 s è la finestra
  in cui mostrod ce la fa; 403/000 o oltre i 4 s è la stessa forma del
  difetto della dev fee (vedi CLAUDE.md), e la cura è la stessa
  conversazione upstream. ⚠️ `time_connect` MENTE sotto il proxy
  trasparente: si guarda `time_appconnect`. Dopo un giro il circuito è
  CALDO, quindi la seconda misura non dice niente sul primo tentativo.
- LA FINESTRA DELLA GARANZIA SUL NODO (15 set 2026, col tabacchino):
  `hold_invoice_cltv_delta = 576` in
  `/home/debian/nodo/mostro/settings.toml` (era 432; la copia
  `.prima-576` sta accanto). Si gira a scambi fermi, e il riavvio è
  dal compose — `cd ~/nodo && docker compose restart mostro` — poi
  «Settings correctly loaded» nei log del servizio. La verifica vale
  dal lato di chi legge, sulla macchina del RELAY:
  `docker compose -f /opt/relay/compose.yml exec relay strfry scan
  '{"kinds":[38385]}' | grep -o '"hold_invoice_cltv_delta","[0-9]*"'`.
  Se dice ancora il vecchio numero, il coordinatore non ha ancora
  ripubblicato il suo evento: si aspetta, prima di sospettare del
  riavvio. Il client legge questo numero dal 38385 (`holdBlocchi`) e
  ne ricava la finestra utile togliendo 24 blocchi di margine nostro:
  cambiarlo sul nodo cambia il cap del foglio «Pubblica» senza toccare
  niente nel codice.
- LA FINESTRA DELLA FATTURA DI CHI COMPRA SUL NODO (24 set 2026, le
  fatture da un'ora): `invoice_expiration_window = 3600` nel
  `[lightning]` di `/home/debian/nodo/mostro/settings.toml` è quanto
  una fattura deve ANCORA valere quando arriva a mostrod
  (`validate_bolt11_invoice`, v0.18.8: `expires_at < now + finestra` →
  `invalid-invoice`); è l'unico posto del nodo che guarda quella
  scadenza — al payout si controlla solo che non sia già scaduta, e se
  lo è parte il giro della fattura nuova. Con 3600 una fattura da 60
  minuti (SatsMobiBot e altri wallet) è rifiutata SEMPRE, perché
  incollata vale già meno di un'ora. Per accettarle: si guarda prima
  (`grep -n invoice_expiration_window
  /home/debian/nodo/mostro/settings.toml`), si tiene la copia
  (`cp settings.toml settings.toml.prima-600`), si porta a 600 (dieci
  minuti: quanto basta al viaggio via Tor e alla verifica; sotto i
  cinque non conviene), a scambi fermi, e il riavvio è dal compose —
  `cd ~/nodo && docker compose restart mostro` — poi «Settings
  correctly loaded» nei log. La verifica vale dal lato di chi legge,
  sulla macchina del RELAY: `docker compose -f /opt/relay/compose.yml
  exec relay strfry scan '{"kinds":[38385]}' | grep -o
  '"invoice_expiration_window","[0-9]*"'` — finché dice 3600 il
  coordinatore non ha ripubblicato. Il client legge questo numero dal
  38385 (`fattFinestra`) e ferma prima le fatture troppo corte con la
  stessa regola: cambiarlo sul nodo cambia la soglia del foglio «Dove
  ricevere i sats» senza toccare niente nel codice. Le 23 ore del
  client dal 24 set sono un consiglio, non un blocco.
- IL NAMESPACE PRESTATO NON SI RIAVVIA DA SOLO (15 set 2026, il giorno
  in cui mostro non usciva). Nel compose del nodo due servizi vivono
  nel namespace di rete di un altro: `mostro` in quello di `mostro-net`
  (il 172.28.1.5) e `tor-redirect` in quello di `tor` (il 172.28.1.3),
  dove stanno le tre REDIRECT, `ip_forward=1` e il DROP del FORWARD.
  `docker compose restart tor` rifa' il namespace di tor, e chi ci
  viveva dentro resta in quello VECCHIO, orfano e senza interfaccia:
  `docker exec nodo-tor-redirect-1 iptables -S` mostra le regole tutte
  al loro posto — in un namespace dove non passa piu' un pacchetto. Nel
  namespace vivo non c'e' niente, ip_forward e' 0, e mostro fa «000»
  su ogni host, DNS compreso (guasto CHIUSO: niente e' uscito in
  chiaro). Verificato sugli inode: tor 4026532573, redirect 4026532516.
  LA REGOLA: dopo `restart tor` sempre
  `cd ~/nodo && docker compose up -d --force-recreate tor-redirect`
  (col nome del servizio in fondo); dopo `restart mostro-net` la stessa
  cosa per `mostro`. Finche' il sidecar esiste. La cura del 15 set e'
  stata esattamente quella (10,5 s), verificata con
  `{"IsTor":true}` dal namespace di mostro e col DROP ancora nel FORWARD
  del namespace VIVO di tor:
  `docker run --rm --network container:nodo-mostro-1 curlimages/curl -s -m 40 https://check.torproject.org/api/ip`
  e `nsenter -t $(docker inspect -f '{{.State.Pid}}' nodo-tor-1) -n iptables -S FORWARD`.
  I namespace si confrontano cosi', ed e' la prova che decide:
  `for c in nodo-tor-1 nodo-tor-redirect-1 nodo-mostro-net-1 nodo-mostro-1; do printf '%-22s ' $c; sudo readlink /proc/$(docker inspect -f '{{.State.Pid}}' $c)/ns/net; done`.
- LA CURA DUREVOLE: LE REGOLE DENTRO TOR, VIA IL SIDECAR (APPLICATA
  la sera del 15 set 2026). `tor-entrypoint.sh` (copia in
  `deploy/nodo/`, sul nodo in `~/nodo/tor/`, montato `:ro` in
  `/usr/local/bin/`) riapplica a ogni avvio di tor le tre REDIRECT, il
  DROP del FORWARD e `ip6tables -A FORWARD -j DROP` (la voce aperta
  dell'audit, chiusa), poi `exec tor -f /etc/tor/torrc`: fail-closed,
  se iptables manca o una regola non entra tor non parte e lo dice. Nel
  compose il servizio `tor` ha `cap_add: [NET_ADMIN]`,
  `sysctls: {net.ipv4.ip_forward: 1}`, `entrypoint` e `command`
  espliciti; il servizio `tor-redirect` non esiste piu' (`ferri-rete`
  resta: la usa `mostro-net`), e il `depends_on` di mostro dice `tor`.
  ⚠️ QUESTA E' UNA DERIVA DEL SERVIZIO `mostro` nel compose: il
  prossimo `up -d` che lo tocchi lo RICREA (cache del prezzo azzerata,
  relay da riprendere): si fa a scambi fermi, `up -d mostro`.
  ⚠️ L'UID DI TOR E' INCHIODATO NEL DOCKERFILE (`Dockerfile.tor` in
  `deploy/nodo/`, copia di `~/nodo/tor/Dockerfile`): i dati in
  `~/nodo/tor/data` sono di `101:102`, e mettere `iptables` nella
  stessa `apt-get` aveva spostato `debian-tor` a `100:101` — «not owned
  by this user», loop di riavvii, hidden service chiusi. L'utente si
  crea PRIMA di installare tor. Il disco e' la verita', l'immagine si
  adatta a lui; mai il contrario (un `chown` sposterebbe le chiavi
  degli hidden service dietro a un numero che la prossima build puo'
  cambiare di nuovo). Prova dopo ogni build:
  `docker run --rm --entrypoint id nodo-tor debian-tor` deve dire
  `uid=101 gid=102`. Da allora `docker compose restart tor` e' un gesto
  sicuro: le regole ripartono con lui, e `authorized_clients/vps.auth`
  resta di chi era.
- LA RONDA DELLA LIQUIDITÀ E L'ENTRATA ACINQ (5 ott 2026):
  `ronda-liquidita.sh` (timer `nodo-liquidita`, una volta al giorno)
  allarma anche quando l'entrata UTILE dei canali ACINQ scende sotto
  150.000: Phoenix paga solo da lì. L'allarme scrive il ribilancio da
  fare, un comando alla volta da `~/nodo`: `addinvoice`, poi `payinvoice
  --allow_self_payment` sul `payment_request` appena avuto (chiede
  conferma: si risponde `yes`), poi `sudo /usr/local/bin/ronda-nodo.sh
  --impara <prime 8 cifre del r_hash>`. Leve da fuori, come le altre:
  `SOGLIA_ACINQ`, `PREFISSO_ACINQ`, `PEZZO_MAX`. INSTALLAZIONE (le unit
  non cambiano), dal PC in PowerShell:
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `cmd /c "git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/ronda-liquidita.sh > %TEMP%\ronda-liquidita.sh"`
  `(Get-FileHash $env:TEMP\ronda-liquidita.sh).Hash.ToLower()`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\ronda-liquidita.sh debian@vm-1937.lnvps.cloud:/tmp/`
  Poi SUL NODO: `sed -i 's/\r$//' /tmp/ronda-liquidita.sh && sha256sum /tmp/ronda-liquidita.sh`
  (stesse cifre del PC), `bash -n /tmp/ronda-liquidita.sh && echo sintassi ok`,
  `diff /usr/local/bin/ronda-liquidita.sh /tmp/ronda-liquidita.sh`
  (devono comparire solo le righe di ACINQ, più il `mktemp` di B5 se
  non era ancora stato ricopiato), `sudo cp /usr/local/bin/ronda-liquidita.sh /root/ronda-liquidita.sh.prima-5ott`,
  `sudo install -m 755 /tmp/ronda-liquidita.sh /usr/local/bin/` e
  `sudo /usr/local/bin/ronda-liquidita.sh --prova`: `PROVA liquidita:
  canali 3/3 attivi ... acinq_in=<numero>` anche su Telegram. Poi senza
  `--prova`: `liquidita ok ...` e Telegram muto (se `acinq_in` è sopra
  150.000). Ritorno indietro:
  `sudo install -m 755 /root/ronda-liquidita.sh.prima-5ott /usr/local/bin/ronda-liquidita.sh`.
  Il gemello su Barattolo («Pagamenti non arrivati» ai moderatori, due
  fatture di checkout scadute nella stessa ora) non vuole leve: parte
  col deploy.
- LA GUARDIA ORARIA DELL'ENTRATA ACINQ E LA COPERTURA DELLA CASSAFORTE
  (6 ott 2026): `ronda-liquidita.sh --acinq`, timer
  `nodo-liquidita-acinq` ai :40 di ogni ora (copie delle due unit in
  `deploy/nodo/`). Fa solo la terza domanda; tace se va bene; sotto
  `SOGLIA_ACINQ` (ora **300.000** di default) avvisa una volta ogni
  `PAUSA_ACINQ_S` (6 ore), col timbro in `/var/lib/ronda/acinq_avvisato`
  che scrive anche la ronda intera quando avvisa lei e che si toglie
  quando l'entrata risale. LE LEVE stanno in `/etc/default/ronda-liquidita`,
  righe `NOME=numero`, e valgono anche per chi lancia la ronda a mano;
  lo script NON fa `source` (gira da root): legge solo
  `SOGLIA_IN SOGLIA_ACINQ PEZZO_MAX USCITA_ACINQ_MIN PAUSA_ACINQ_S`, solo cifre.
  `USCITA_ACINQ_MIN` = quanto deve restare d'uscita ACINQ dopo un giro:
  il debito della Cassaforte nodo verso i venditori più i sats di Alan.
  Il nodo non lo sa leggere (LNbits sta sul VPS): si aggiorna A MANO
  ogni volta che si legge la Cassaforte, e sempre prima di seguire un
  ribilancio suggerito. Vuota = nessun importo; sotto i 10.000 di spazio
  = «la copertura non lascia spazio», niente giro e niente swap.
  Il debito si conta così (6 ott 2026): saldo della Cassaforte meno il
  margine nostro misurato il 1 ott (12.475). Il capitale di
  `capitale_cassa.py` NON si toglie intero: 265.000 sono lo sweep del #152,
  già uscito col suo payout.
  INSTALLAZIONE, dal PC in PowerShell, dopo il push:
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `foreach ($f in 'ronda-liquidita.sh','nodo-liquidita-acinq.service','nodo-liquidita-acinq.timer') { cmd /c "git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/$f > %TEMP%\$f"; "$f " + (Get-FileHash $env:TEMP\$f).Hash.ToLower() }`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\ronda-liquidita.sh $env:TEMP\nodo-liquidita-acinq.service $env:TEMP\nodo-liquidita-acinq.timer debian@vm-1937.lnvps.cloud:/tmp/`
  Sul nodo: `cd /tmp && sed -i 's/\r$//' ronda-liquidita.sh nodo-liquidita-acinq.* && sha256sum ronda-liquidita.sh nodo-liquidita-acinq.* && bash -n ronda-liquidita.sh && echo sintassi ok`
  (stesse cifre del PC); `diff /usr/local/bin/ronda-liquidita.sh /tmp/ronda-liquidita.sh | grep '^<'`
  (le righe che se ne vanno: soglia, commenti, il ribilancio vecchio);
  `sudo cp /usr/local/bin/ronda-liquidita.sh /root/ronda-liquidita.sh.prima-6ott`;
  `printf 'USCITA_ACINQ_MIN=<debito + Alan>\n' | sudo tee /etc/default/ronda-liquidita`;
  `sudo install -m 755 /tmp/ronda-liquidita.sh /usr/local/bin/`;
  `sudo /usr/local/bin/ronda-liquidita.sh --prova` (quadro con
  `acinq_out` e `copertura=`, anche su Telegram); poi le unit:
  `sudo install -m 644 /tmp/nodo-liquidita-acinq.service /tmp/nodo-liquidita-acinq.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now nodo-liquidita-acinq.timer`,
  e la guardia a mano: `sudo /usr/local/bin/ronda-liquidita.sh --acinq; echo rc=$?`.
  ⚠️ SU QUESTO LND `listchannels` DÀ IN `chan_id` IL CHANNEL_ID
  ESADECIMALE (BOLT 2, 64 cifre) e lo scid numerico in `scid`: ogni
  comando che vuole un canale per numero (`--outgoing_chan_id`,
  `getchaninfo`) prende `scid`. Il `feereport` usa i numeri.
  Ritorno indietro: `sudo systemctl disable --now nodo-liquidita-acinq.timer`
  e `sudo install -m 755 /root/ronda-liquidita.sh.prima-6ott /usr/local/bin/ronda-liquidita.sh`
  (il file delle leve si può lasciare: la versione vecchia non lo legge).
  LA PROVA DELL'AVVISO «PAGAMENTI NON ARRIVATI» SU TELEGRAM VERO:
  avvisa SOLO i moderatori (`notifica_admin`); un ordine creato non
  avvisa nessuno, ma tiene impegnata la quantità per i 15 minuti della
  fattura. Da un account compratore, su un annuncio NOSTRO con
  quantità 2 o più (o due annunci nostri), due «🔒 Compra in sicurezza»
  a pochi minuti l'uno dall'altro, senza pagare e senza annullare:
  l'annullo non conta. Fra 15 e 25 minuti dopo il secondo (la fattura
  vive 900 secondi, il giro è ogni ~10 minuti) arriva «⚠️ Pagamenti non
  arrivati, controllare la liquidità.» con i due ordini, e nel journal
  la riga «⚠️ Pagamenti non arrivati: avvisati i moderatori». Il costo:
  la pausa di 6 ore parte da lì, e un avviso vero in quelle ore tace.
  Si fa con la guardia oraria del nodo già accesa (copre la causa
  prima), mai il giorno del lancio, e senza toccare il database.
  Il P2P (garanzia mai pagata) non si usa per la prova: c'è di mezzo
  una controparte.
- LA GUARDIA DELLA LIQUIDITÀ, DAL SERVER (11 ott 2026; il perché in
  CANTIERI, «La guardia della liquidità»; com'è fatta in ARCHITETTURA).
  Sostituisce la guardia oraria del nodo qui sopra: guarda l'entrata
  TOTALE, chiede a LND se chi paga da Phoenix ha una strada anche fuori
  dal canale ACINQ diretto, avvisa ai cambi e al massimo una volta al
  giorno, e ogni avviso porta la grafica dei canali. NASCE SPENTA.
  `/canali` NEL BOT (solo admin) funziona appena il deploy è passato,
  anche a guardia spenta: è il modo di vedere il giudizio PRIMA di
  accenderla. Se risponde «al server manca il macaroon di lettura» o
  «non ha il permesso», si guarda «IL MACAROON DI SOLA LETTURA» più
  sotto; una voce «❔ … non l'ho potuta misurare (getinfo negato)» vuol
  dire macaroon senza `info:read`.
  ACCENDERLA, sul VPS. Prima si guarda che il config non abbia già
  righe sue (il config vince sul codice):
  `grep -n "LIQUIDITA" /srv/barattolo/config.py`
  poi nel config, a mano, UNA riga:
  `GUARDIA_LIQUIDITA = True`
  e `sudo systemctl restart barattolo`, poi
  `journalctl -u barattolo -n 300 --no-pager | grep "💧"`
  (si aspetta «💧 Guardia della liquidità: accesa — un giro ogni 60
  minuti, avvisi a …»; il primo giro parte due minuti dopo l'avvio e
  tace se va tutto bene). Le altre leve hanno già il valore giusto nel
  codice e si scrivono SOLO per cambiarle:
  `LIQUIDITA_SCAMBIO_MAX = 500000` (la garanzia più grossa: se cambia
  `max_order_amount` nel `settings.toml` del nodo, cambia qui),
  `LIQUIDITA_PHOENIX_MIN = 300000` (quanto deve poter entrare da
  Phoenix; 0 = quella domanda non si fa),
  `LIQUIDITA_USCITA_MIN = 0` (0 = nessun minimo d'uscita),
  `LIQUIDITA_USCITA_CANALE = False` (True = la quarta domanda: il
  canale con più uscita regge da solo un ordine al tetto
  `P2P_MAX_EURO`, al cambio del momento; con `P2P_MAX_EURO` a 0 è un
  «non so»),
  `LIQUIDITA_ACINQ_TETTO = False` (True = la quinta domanda: il
  tetto dei pagamenti appesi di ACINQ, 450k sul canale da 1M, lascia
  entrare `LIQUIDITA_PHOENIX_MIN`? Se no, vale la strada via LNBiG;
  si accende con la riga nel config e il riavvio, come le altre),
  `LIQUIDITA_PROMEMORIA_S = 86400`, `LIQUIDITA_OGNI_S = 3600`.
  Gli avvisi vanno agli stessi del guardiano del ponte
  (`GUARDIANO_PONTE_AVVISA`, o i moderatori).
  L'AVVISO D'USCITA (15 ott 2026, richiesta di Andrea): uscita totale
  sotto 400.000, o nessun canale che regga da solo un ordine al
  tetto. Sul VPS, prima si guarda che le righe non ci siano già (nel
  config vale l'ULTIMA riga con quel nome):
  `grep -n "^LIQUIDITA_USCITA\|^P2P_MAX_EURO\|^GUARDIA_LIQUIDITA" /srv/barattolo/config.py`
  poi, a mano, le due righe
  `LIQUIDITA_USCITA_MIN = 400000`
  `LIQUIDITA_USCITA_CANALE = True`
  e `sudo systemctl restart barattolo`. La quarta domanda vuole
  `P2P_MAX_EURO` scritto (250); gli avvisi partono solo a guardia
  accesa (`GUARDIA_LIQUIDITA = True`), e `/canali` nel bot mostra le
  due voci anche a guardia spenta. RITORNO: via le due righe e
  riavvio.
  DOVE SI LEGGE: `journalctl -u barattolo | grep "💧"` — una riga a
  ogni CAMBIO («allarme (phoenix)», «promemoria», «rientrato») e a ogni
  giro saltato («canali non letti (muto)»), più una per destinatario.
  Lo stato sta nel timbro `liquidita_stato`.
  SPEGNERLA: via la riga (o `False`) e riavvio. Il timbro resta e non
  dà fastidio; se si riaccende mesi dopo con uno stato vecchio, il
  primo giro buono manda un «tornata a posto» di troppo.
  SUL NODO, DOPO che la guardia del server si è vista funzionare (un
  `/canali` giusto e la riga «accesa» nel journal), si spegne la
  guardia oraria vecchia, un comando per riga:
  `sudo systemctl disable --now nodo-liquidita-acinq.timer`
  `systemctl list-timers --all | grep liquidita`
  (la riga della guardia oraria non c'è più; il giro di ogni giorno
  resta), e alla ronda di ogni giorno si toglie la terza domanda, che è
  la stessa soglia
  ACINQ. Prima si guarda che la leva non sia già scritta (nel file
  vale la PRIMA riga con quel nome):
  `grep -n "SOGLIA_ACINQ" /etc/default/ronda-liquidita`
  se non c'è:
  `echo 'SOGLIA_ACINQ=0' | sudo tee -a /etc/default/ronda-liquidita`
  `sudo /usr/local/bin/ronda-liquidita.sh --prova`
  (il quadro arriva su Telegram come sempre, e non parla più di ACINQ
  basso). La ronda di ogni giorno continua a dire canali spariti o
  inattivi, lease, e l'inbound totale sotto `SOGLIA_IN`. RITORNO
  INDIETRO: `sudo systemctl enable --now nodo-liquidita-acinq.timer` e
  via la riga `SOGLIA_ACINQ=0` dal file.
  LA SONDA A MANO, dal nodo, in sola lettura
  (`deploy/nodo/sonda-rotte.py`): i canali, le strade da ACINQ a noi per
  100k, 300k, 500k e 1M (libera, senza il canale diretto nel tetto di
  Phoenix, senza tetto) e da quale canale sono entrati gli ultimi
  incassi. Usa il `readonly.macaroon` che LND ha già (non sa pagare) e
  non lo stampa. Dal PC in PowerShell:
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `cmd /c "git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/sonda-rotte.py > %TEMP%\sonda-rotte.py"`
  `(Get-FileHash $env:TEMP\sonda-rotte.py).Hash.ToLower()`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\sonda-rotte.py debian@vm-1937.lnvps.cloud:/tmp/`
  sul nodo: `sha256sum /tmp/sonda-rotte.py` (le stesse cifre) e
  `python3 /tmp/sonda-rotte.py`. Le prime righe dicono dove si ferma:
  «REST …: muta (perché)» o «risponde», e per ogni macaroon trovato nel
  container «accettato» o «rifiutato» — l'11 ott quello buono era
  sotto `/root/.lnd/data/…`, e una copia vecchia in `data-annullato-2`
  veniva rifiutata. Se la REST sta su un altro indirizzo:
  `python3 /tmp/sonda-rotte.py IP:PORTA`.
  LA PROVA CHE CHIUDE LA DOMANDA «Phoenix entra solo da ACINQ?» non è
  la sonda (LND non conosce i saldi altrui): è un pagamento vero da un
  Phoenix, più grosso dell'entrata ACINQ del momento, e poi
  `lncli lookupinvoice <r_hash>` sul nodo per leggere da quale canale
  sono arrivati i pezzi (la lista `htlcs`).
- IL MARGINE DELLA CASSAFORTE (27 ott 2026, cantiere margine-cassaforte;
  perché in CANTIERI, «Il margine della cassaforte»; com'è fatto in
  ARCHITETTURA). SUL VPS NON SI AGGIUNGE NIENTE: la domanda del saldo
  prima di ogni pagamento è sempre accesa (usa la invoice key che il
  config ha già), e le due leve della sesta domanda della guardia,
  `LIQUIDITA_MARGINE_PERCENTO = 1` e `LIQUIDITA_MARGINE_MIN_SATS = 10000`,
  valgono i default del codice; la sesta domanda parla solo a guardia
  accesa (`GUARDIA_LIQUIDITA`), e in `/canali` anche a guardia spenta.
  COSA SI VEDE: un incasso che si ferma per il margine è nel journal
  «🔁 Pagamento NON CHIESTO: nella cassaforte nodo manca il margine
  (ordini#N: saldo …, servono … con la riserva di LNbits)», e nella
  stanza 💧 Liquidità «Manca margine nella cassaforte nodo» (uno ogni sei
  ore per cassaforte); l'incasso riparte da solo (1, 5, 15, 30 minuti,
  poi ogni ora) appena il margine c'è. COSA SI FA: si aggiunge capitale
  alla cassaforte (il wallet è misto: escrow di tutti più il nostro).
  I NUMERI VIVI, sola lettura, dal VPS (`cd /srv/barattolo`, come
  `barattolo`): saldo per cassaforte e incassi in attesa dal database —
  il comando sta nel rapporto del 26 ott (CANTIERI, «Lo swap intero sul
  regtest di Boltz», il margine dell'1 %). Il 27 ott: nodo 503.786 di
  saldo, 470.727 in attesa, margine 33.059 (soglia 14.707); SaaS 84.250.
- LA QUINTA DOMANDA DELLA RONDA, OGNI GIORNO: `ronda-tor.sh` +
  `nodo-tor.timer` (09:20 UTC, Persistent), copie in `deploy/nodo/`.
  Tre giudici dal namespace di mostro: la curl a check.torproject.org
  (allarme su codice diverso da 200 o `IsTor` non true — il secondo e'
  il caso peggiore, esce in chiaro; dal 9 nov 2026 un codice diverso
  da 200 si riprova UNA volta dopo 30 s, e il quadro scrive «al secondo
  tentativo (il primo: 000)»: un circuito lento non e' un guasto, IsTor
  falso invece suona subito), MOSTRO DENTRO MOSTRO-NET (dal 22
  set 2026 al posto del giudice del sidecar, che non tornera'), e il
  DROP del FORWARD nel namespace vivo
  di tor, letto con l'iptables DI TOR via `docker exec` (ripiego nsenter
  + iptables dell'host; senza, «non misurato»). Usa `curlimages/curl`
  con `--pull never`: e' gia' sul nodo dal 15 set e la ronda non deve
  dipendere dalla rete per dire che la rete non c'e'. Installazione:
  scp dei tre file, `sha256sum` da confrontare, poi
  `sudo install -m 755 ronda-tor.sh /usr/local/bin/ && sudo cp nodo-tor.service nodo-tor.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now nodo-tor.timer && sudo /usr/local/bin/ronda-tor.sh --prova`.
  Il messaggio finisce con `--- fine ronda tor`, come le altre.
- MOSTRO DENTRO MOSTRO-NET, IL SECONDO GIUDICE DI `ronda-tor.sh` (22 set
  2026). Le REDIRECT e il DROP di `tor-entrypoint.sh` valgono per
  `172.28.1.5` e basta: un mostro ricreato FUORI dal namespace di
  `mostro-net` uscirebbe da un'altra strada, e la superficie non lo
  vede. Forma fissa, niente baseline: a) `nodo-mostro-1` e
  `nodo-mostro-net-1` hanno lo stesso inode di `/proc/<pid>/ns/net`
  (se no, `NetworkMode` dice quale guasto: `container:<id di mostro-net>`
  = ORFANO di un restart di mostro-net, cura `up -d --force-recreate
  mostro`; altro = FUORI, il compose e' cambiato); b) mostro vede su di
  se' `172.28.1.5`; c) il `default via` di mostro-net e' un IP di
  `nodo-tor-1` (letto da `docker inspect`, non scritto a mano). Mostro
  FERMO si dice «FERMO» e salta curl e namespace; mostro-net fermo con
  mostro vivo ha il suo allarme. I tre pezzi a mano, se un allarme va
  guardato:
  `for c in nodo-mostro-net-1 nodo-mostro-1; do printf '%-20s ' $c; sudo readlink /proc/$(docker inspect -f '{{.State.Pid}}' $c)/ns/net; done`
  `sudo nsenter -t $(docker inspect -f '{{.State.Pid}}' nodo-mostro-1) -n ip -4 -o addr show`
  `sudo nsenter -t $(docker inspect -f '{{.State.Pid}}' nodo-mostro-net-1) -n ip -4 route show default`
  `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' nodo-tor-1`.
  INSTALLAZIONE (le unit non cambiano). Dal PC, in PowerShell — `cmd /c`
  conta: il `>` di PowerShell 5.1 riscrive i byte in UTF-16 e lo
  script non parte:
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `cmd /c "git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/ronda-tor.sh > %TEMP%\ronda-tor.sh"`
  `(Get-FileHash $env:TEMP\ronda-tor.sh).Hash.ToLower()`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\ronda-tor.sh debian@vm-1937.lnvps.cloud:/tmp/`
  Poi SUL NODO: `sed -i 's/\r$//' /tmp/ronda-tor.sh && sha256sum /tmp/ronda-tor.sh`
  (stesse cifre del PC: `git show` da' i byte del repo, gia' LF, e il
  `sed` e' la cintura), `bash -n /tmp/ronda-tor.sh && echo sintassi ok`,
  `sudo cp /usr/local/bin/ronda-tor.sh /root/ronda-tor.sh.prima-22set`,
  `sudo install -m 755 /tmp/ronda-tor.sh /usr/local/bin/` e il primo
  giro `sudo /usr/local/bin/ronda-tor.sh --prova`: deve dire
  `PROVA tor: esce da Tor (<un exit>);mostro nel namespace di mostro-net;IP 172.28.1.5;gateway 172.28.1.3 = tor;DROP del FORWARD al suo posto`
  e lo stesso arriva su Telegram, chiuso da `--- fine ronda tor`. Poi
  `sudo /usr/local/bin/ronda-tor.sh` senza `--prova`: `tor ok  ...` e
  Telegram muto. Un ALLARME al primo giro non si zittisce: o e' vero, o
  la ronda legge male l'`ip` vero (provata su un banco finto) — si
  guarda coi quattro comandi qui sopra. Ritorno indietro:
  `sudo install -m 755 /root/ronda-tor.sh.prima-22set /usr/local/bin/ronda-tor.sh`.
- LA QUARTA DOMANDA, LA SUPERFICIE: `ronda-superficie.sh`, copia in
  `deploy/nodo/` dal 22 set 2026 (prima viveva solo sul nodo). Foto di
  quel che ascolta fuori dal loopback, dei DNAT di Docker e delle regole
  dentro tor, confrontata con la baseline `/var/lib/ronda/superficie`;
  `--impara` e' un gesto. La porta del DNS interno di Docker
  (`127.0.0.11:<porta>` in DOCKER_OUTPUT/DOCKER_POSTROUTING) e' mascherata
  come `PORTA` su tutt'e due i lati, quindi la baseline di prima NON va
  rifatta. Il PONTE WIREGUARD non si impara: `WG-PONTE` in cima a INPUT
  con le sue 5 regole nell'ordine giusto, i due DROP di `wg0` in FORWARD
  e quello in DOCKER-USER, la 51820/udp chiusa su v6, `wg0` su con porta
  51820 e UNA peer — ogni pezzo mancante ha il suo allarme. Installazione
  (dal PC, cartella del repo):
  `scp -i $env:USERPROFILE\.ssh\lnvps deploy/nodo/ronda-superficie.sh debian@vm-1937.lnvps.cloud:/tmp/`
  poi SUL NODO `sha256sum /tmp/ronda-superficie.sh` contro quello del PC
  (`Get-FileHash deploy/nodo/ronda-superficie.sh`, stesse cifre in
  minuscolo), `sudo cp /usr/local/bin/ronda-superficie.sh /root/ronda-superficie.sh.prima-22set`,
  `sudo install -m 755 /tmp/ronda-superficie.sh /usr/local/bin/` e
  `sudo /usr/local/bin/ronda-superficie.sh` — deve dire
  `superficie ok  24 righe invariate` e `ponte wg ok`. Un ALLARME al
  primo giro NON si cura con `--impara`: o e' vero, o la ronda legge
  male l'`iptables -S` vero (provata solo su un banco finto) — si
  guarda prima. Rollback: il `.prima-22set` al suo posto.
  SE SUONA «DOCKER-USER: manca il DROP di wg0» (2 nov 2026, dopo un
  riavvio del nodo): la riga non e' entrata perche' il tunnel e' salito
  prima di Docker. Si rimette a mano, identica al PostUp, senza
  riavviare niente (il ponte passa dal socat sull'host, cioe' da
  INPUT, e non si taglia): copia `sudo sh -c 'iptables-save >
  /root/iptables-prima-docker-user-<data>.txt'`, poi `sudo iptables -w
  -I DOCKER-USER 1 -i wg0 -j DROP`, poi il drop-in
  `wg-quick-dopo-docker.conf` (voce «IL PONTE VIA WIREGUARD», passo 4)
  se manca, e la ronda a mano deve dire `ponte wg ok`.
- LA RONDA DEL NODO OGNI ORA, E I PAGAMENTI CHE SI RICONOSCONO DA SOLI
  (28 set 2026). Quattro file in `deploy/nodo/`, copie di quel che
  gira sul nodo: `ronda.sh` (in `~/nodo`, la chiama il timer),
  `ronda-nodo.sh` e `ronda-pagamenti.py` (in `/usr/local/bin`, da
  root via sudo), `ronda-avvisa.sh` (invariato), più il drop-in
  `nodo-ronda.timer.d/ogni-ora.conf`. OGNI ORA al minuto 5 il giro
  corto: pagamenti usciti da LND, HTLC a meno di 20 blocchi dalla
  scadenza, canali. Il PRIMO giro dalle 9 UTC è il giro lungo di prima
  (finestra, disco, RAM, superficie, backup) più il riassunto dei
  pagamenti di ieri sul canale del nodo. Un pagamento è riconosciuto se
  lo spiega mostro.db (fattura del compratore, dev fee, payout in
  volo), una riga di pagamento nei log di mostrod, un FAILED ritentato
  con successo (stessa cifra, stessa destinazione) o il VPS
  (`POST /api/nodo/pagamenti-noti`, via Tor, si'/no per hash, segreto
  `RONDA_NODO_SEGRETO`). Nessuno lo spiega → allarme SUBITO, una volta,
  con cifra, destinazione, descrizione e cosa fare. Una fonte muta (VPS
  giu', mostro.db illeggibile) → aspetta, e allarma solo dopo tre ore.
  Lo stato sta in `/var/lib/ronda/`: `pagamenti_noti` (ora «hash
  fonte»: le righe di solo hash valgono «imparato»),
  `pagamenti_in_attesa`, `pagamenti_allarmati`, `guasti`, `riassunti`;
  il giorno del giro lungo in `~/nodo/.ronda-giro-lungo`. I gesti a
  mano: `sudo /usr/local/bin/ronda-nodo.sh --impara <inizio dell'hash>`
  (solo quel pagamento; senza argomento, tutti come prima) e
  `sudo /usr/local/bin/ronda-nodo.sh --prova` (riassunto subito).
  L'ORDINE È QUESTO, UN COMANDO ALLA VOLTA: prima il codice sul VPS
  (il push: senza segreto la porta risponde 404 e non fa niente), poi
  il segreto sul VPS, poi il nodo.
  1) IL SEGRETO, sul PC: `python -c "import secrets; print(secrets.token_hex(32))"`.
  UNO SUO, non quello dello sconto né quello degli eventi. Esadecimale
  apposta: se mai finisse in un file del repo, lo scanner della CI lo
  prende come ogni esadecimale da 64. Mai nel canale del nodo, MAI in
  una chat con Claude.
  2) SUL VPS, nel `config.py`: la riga `RONDA_NODO_SEGRETO = "..."`,
  poi `sudo systemctl restart barattolo`. Il pannello «⚙️ Stato delle
  leve» deve dire accesa «Ronda del nodo — porta dei pagamenti». La
  porta dal VPS stesso, senza il segreto (non finisce nella history):
  `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8080/api/nodo/pagamenti-noti -H "Content-Type: application/json" -d '{}'`
  → `403` (aperta, e senza segreto non si entra); `404` = la riga non
  e' stata letta.
  3) SUL NODO, TRE LETTURE PRIMA DI TOCCARE: `systemctl cat nodo-ronda.timer nodo-ronda.service`
  (l'`ExecStart` deve essere `/home/debian/nodo/ronda.sh` e l'utente
  `debian`: se no ci si ferma e si manda l'uscita); `sudo -l | grep ronda`
  (la riga di `ronda-nodo.sh` NON deve finire con `""`, che vieterebbe
  `--giorno`: se finisce cosi' ci si ferma); e il formato vero dei log
  di mostrod, che il giudice legge:
  `docker logs --since 720h nodo-mostro-1 2>&1 | grep -a "Invoice with hash" | tail -2 | sed 's/\x1b\[[0-9;]*m//g'`
  — deve cominciare con l'ora, poi `INFO` o `WARN`, poi
  `mostrod::app::release: Order Id …`. Un formato diverso non e' un
  guasto: vuol dire che i payout a un Lightning address si
  riconosceranno solo dal VPS o con `--impara`, e si manda l'uscita.
  4) DAL PC, in PowerShell, i quattro file dal repo (`cmd /c` conta:
  il `>` di PowerShell 5.1 riscrive i byte in UTF-16):
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `cmd /c "for %f in (ronda-pagamenti.py ronda-nodo.sh ronda.sh) do git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/%f > %TEMP%\%f"`
  `cmd /c "git -C C:\Users\Andrea\Documents\GitHub\satmarket show origin/main:deploy/nodo/nodo-ronda.timer.d/ogni-ora.conf > %TEMP%\ogni-ora.conf"`
  `Get-FileHash $env:TEMP\ronda-pagamenti.py,$env:TEMP\ronda-nodo.sh,$env:TEMP\ronda.sh,$env:TEMP\ogni-ora.conf | ForEach-Object { $_.Hash.ToLower() + "  " + (Split-Path $_.Path -Leaf) }`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\ronda-pagamenti.py $env:TEMP\ronda-nodo.sh $env:TEMP\ronda.sh $env:TEMP\ogni-ora.conf debian@vm-1937.lnvps.cloud:/tmp/`
  5) SUL NODO, i byte: `cd /tmp && sed -i 's/\r$//' ronda-pagamenti.py ronda-nodo.sh ronda.sh ogni-ora.conf && sha256sum ronda-pagamenti.py ronda-nodo.sh ronda.sh ogni-ora.conf`
  (le stesse cifre del PC), poi `bash -n ronda-nodo.sh && sh -n ronda.sh && python3 -m py_compile ronda-pagamenti.py && echo sintassi ok`.
  6) SUL NODO, le copie per tornare indietro:
  `sudo cp /usr/local/bin/ronda-nodo.sh /root/ronda-nodo.sh.prima-28set && cp ~/nodo/ronda.sh ~/nodo/ronda.sh.prima-28set && sudo cp /var/lib/ronda/pagamenti_noti /root/pagamenti_noti.prima-28set`
  7) SUL NODO, il segreto: `sudo install -d -m 700 /etc/ronda` e poi
  `sudo nano /etc/ronda/barattolo.env` con DUE righe —
  `RONDA_URL=https://barattolo.store/api/nodo/pagamenti-noti` e
  `RONDA_SEGRETO=` seguito dal segreto del passo 1 — e infine
  `sudo chmod 600 /etc/ronda/barattolo.env`. (Tor e' di serie,
  `172.28.1.3:9050`: la riga `TOR_SOCKS=` serve solo a cambiarlo.)
  8) SUL NODO, al loro posto:
  `sudo install -m 755 /tmp/ronda-pagamenti.py /tmp/ronda-nodo.sh /usr/local/bin/ && install -m 755 /tmp/ronda.sh ~/nodo/ronda.sh`
  9) IL PRIMO GIRO A MANO: `sudo /usr/local/bin/ronda-nodo.sh` — una
  riga `ronda-pagamenti: N letti, K riconosciuti adesso (barattolo …,
  mostro …), 0 sconosciuti, 0 in attesa, …` (i pagamenti dopo
  l'`--impara` del 28 set si riconoscono adesso). Se dice `fonti mute:
  il VPS dice 403` il segreto non combacia; `404` la riga del VPS
  manca; `non risponde` Tor o il VPS. Se su Telegram arriva un
  «🚨 PAGAMENTO SCONOSCIUTO» ci si FERMA e lo si guarda: e' vero finche'
  non si dimostra il contrario. Poi `sudo /usr/local/bin/ronda-nodo.sh --prova`:
  su Telegram «(PROVA) 🧾 Pagamenti del nodo, ieri …» chiuso da
  `--- fine riassunto`, e nel terminale la riga del backup.
  10) IL TIMER, OGNI ORA:
  `sudo install -D -m 644 /tmp/ogni-ora.conf /etc/systemd/system/nodo-ronda.timer.d/ogni-ora.conf && sudo systemctl daemon-reload && sudo systemctl restart nodo-ronda.timer && systemctl list-timers nodo-ronda.timer`
  — il prossimo scatto e' a `:05` dell'ora che viene, non lunedi'.
  11) DOPO IL PRIMO SCATTO: `journalctl -u nodo-ronda --since "70 min ago" --no-pager | tail -6`
  — `ronda: giro corto …`, la riga di `ronda-pagamenti`, `--- fine
  ronda`. Il giorno dopo, alle 9:05 UTC, il giro lungo e il riassunto.
  TORNARE INDIETRO, SUL NODO (il VPS non serve toccarlo: senza chi
  chiede, la porta non fa niente; per chiuderla si toglie la riga dal
  config e si riavvia):
  `sudo rm /etc/systemd/system/nodo-ronda.timer.d/ogni-ora.conf && sudo systemctl daemon-reload && sudo systemctl restart nodo-ronda.timer`
  `sudo install -m 755 /root/ronda-nodo.sh.prima-28set /usr/local/bin/ronda-nodo.sh && install -m 755 ~/nodo/ronda.sh.prima-28set ~/nodo/ronda.sh`
  `sudo sed -i 's/ .*//' /var/lib/ronda/pagamenti_noti` — ⚠️ QUESTO
  CONTA: la ronda di prima legge la riga INTERA come hash, e «hash
  barattolo» non combacia con niente, quindi senza questo sed
  griderebbe su ogni pagamento riconosciuto nel frattempo.
- I PROVIDER DI SCORTA DEL PREZZO (15 set 2026): `settings-price.toml`
  in `deploy/nodo/` e' la sezione `[price]` da appendere a
  `~/nodo/mostro/settings.toml` (yadio + CoinGecko + currency-api +
  Blockchain.com, tutti senza chiave, timeout per provider a 30 s),
  poi `docker compose restart mostro`. Il perche' e i numeri del
  breaker stanno in testa al file. Prima di appendere, la prova che
  gli host rispondano dalla rete di mostrod (il blocco degli exit Tor e'
  per sito):
  `for u in https://api.coingecko.com/api/v3/simple/price?ids=bitcoin\&vs_currencies=eur https://currency-api.pages.dev/v1/currencies/btc.json https://blockchain.info/ticker; do docker run --rm --network container:nodo-mostro-1 curlimages/curl -s -m 30 -o /dev/null -w "%{http_code} %{time_appconnect}s $u\n" "$u"; done`.
  Un host che fa 403 non si mette in lista: un provider morto costa
  solo un tick, ma un provider che risponde male entra nella mediana.
- LO SPECCHIO GIRA SULLA MACCHINA DEL RELAY, non su questo VPS: e' il
  servizio `specchio` del `compose.yml` di `/opt/relay` (uno `strfry
  router` con `router.conf`), e si accende con `docker compose up -d
  specchio` — COL NOME DEL SERVIZIO IN FONDO, che un `up -d` nudo
  ricrea anche il relay vivo. La configurazione sta in
  `deploy/relay/`, e quella cartella e' una COPIA a mano: chi tocca un
  file su quella macchina lo riporta nel repo nello stesso giro.
- L'import aperto da Nostr si accende SOLO scrivendo
  `IMPORT_NOSTR_APERTO = True` nel config del VPS e riavviando: nel
  codice il default è False apposta (vedi Architettura). Prima di
  accenderlo vale la pena guardare il journal del primo giro — chi
  viene scoperto, quanti annunci entrano, quanti vanno in revisione —
  perché da lì partono account e DM verso persone che non ci
  conoscono. Rimettere False e riavviare è l'interruttore
  d'emergenza; gli annunci già importati restano dove sono.
- Se dall'import aperto nascono copie doppie: la diagnosi si fa in
  SOLA LETTURA prima di toccare (la query che decide è
  `SELECT COUNT(*) FROM annunci WHERE contatto_nostr!='' AND
  nostr_origine_d LIKE 'barattolo-%'`: se è >0 l'anello si è chiuso su
  noi stessi), poi si spegne l'import, poi `ripulisci_anello_nostr.py`
  — prima su una copia del database, poi su quello vero.
- I LINK TOCCABILI NELLE DESCRIZIONI si accendono ALLA RESA, non alla
  scrittura: il giudice gira in lettura e non scrive niente in colonna,
  quindi al primo deploy si accendono anche gli annunci GIÀ pubblicati
  — nessuna migrazione, e svuotare `LINK_DESCRIZIONE_AMMESSI` nel
  config li spegne tutti insieme.
  ⚠️ IL PUNTO CIECO VA GUARDATO UNA VOLTA, prima di pubblicare: gli
  avvisi 🔗 al moderatore stanno sulla SCRITTURA (annuncio nuovo,
  revisione, modifica), quindi il parco esistente si accende senza che
  nessuno riceva niente — e la popolazione dove me lo aspetto di più
  sono gli importati da Nostr, che sono descrizioni scritte per altri
  mercatini. Il censimento è in SOLA LETTURA e non tocca niente:
  `cd /srv/barattolo && python3 -c "import sqlite3, server;
  con = sqlite3.connect(server.DB); con.row_factory = sqlite3.Row;
  [print(r['id'], '·'.join(v['dominio'] for v in server.link_vivi(r['descrizione'] or '')), '|', (r['titolo'] or '')[:50])
   for r in con.execute(\"SELECT id, titolo, descrizione FROM annunci WHERE stato='attivo' AND descrizione LIKE '%https://%'\")
   if server.link_vivi(r['descrizione'] or '')]"`
  Lista corta = si guarda a occhio e si va; lista lunga o con qualcosa
  di strano = si decide prima di pubblicare, non dopo.
- Il Login Widget esige il dominio registrato: BotFather → `/setdomain`
  su @ilbarattolobot → `barattolo.store` (senza, il bottone non compare;
  su localhost non compare mai: si collauda col bottone "cookie web").
- LA CATENA DEL DEPLOY, i pezzi che CLAUDE.md non tiene (là restano
  il fatto — push su main e sei online —, il perché di sicurezza
  e il freno):
  LA CATENA, in quattro pezzi: 1) il job `pronto` del workflow fa
  avanzare il ref `pronto` quando prove e controllo dei segreti sono
  passati; 2) sul VPS un timer systemd chiama `deploy.sh` ogni minuto,
  che guarda se quel ref si è mosso; 2b) DAL 21 SET 2026 il ref mosso è
  solo il CAMPANELLO: prima di tirare, `deploy.sh` GIUDICA il commit —
  vedi più sotto «IL DEPLOY CHE SI FIDA SOLO DI MAIN»; 3) dopo il riavvio si chiede a
  `/api/salute` e, se non risponde entro 45 secondi, si torna al
  commit di prima e si riavvia ancora.
  `/api/salute` TOCCA IL DATABASE apposta (una lettura, la più piccola
  che ci sia): un uvicorn che risponde ma non sa più aprire il file
  del mercatino è esattamente il guasto che un health check sul solo
  processo NON vede — e sarebbe quello che lascia online una versione
  rotta credendola sana. È pubblica come `/api/listings`, quindi non
  dice NIENT'ALTRO: niente conteggi, versioni, percorsi o nomi di
  file, che sono tutte cose che aiutano chi guarda il server da fuori
  a sapere cosa ha davanti. Il «cosa sta girando» lo dice il journal,
  che è di chi ha le chiavi. L'UNICA ECCEZIONE (18 set 2026) è una
  parola sul ponte verso LND (`"ponte": "ok"`, vedi «IL GUARDIANO DEL
  PONTE» più sotto), che da fuori si vedeva già provando a comprare —
  e NON cambia il codice: col ponte giù resta 200, perché un guasto di
  tor non è una ragione per tornare alla versione di prima. Sul guasto
  del database risponde 503 e non un 200 con
  «ok: false»: chi controlla la salute guarda il CODICE, e un guasto
  travestito da risposta buona è il modo in cui un rollback non parte.
  L'unità systemd COPIA lo script prima di eseguirlo — dal set 2026
  in `/run/barattolo-deploy/`, una cartella di root che systemd crea a
  ogni giro (`RuntimeDirectory=`), e non più in /tmp: lì il nome era
  fisso, e un utente non-root (ora c'è: `barattolo`) poteva occuparlo
  prima e far eseguire a root un file suo. La copia non è
  una stranezza: bash legge un file mentre lo esegue, quindi se
  `git reset` lo riscrivesse a metà corsa la riga dopo sarebbe di un
  altro script. Il deploy in corso finisce col codice con cui è
  partito e la versione nuova entra in vigore al giro dopo.
  Il database si COPIA PRIMA di aggiornare (`backup/pre-deploy-*.db`,
  le ultime 5) e si copia con l'API di sqlite invece che con `cp`: il
  server sta girando, e un file copiato a caldo mentre qualcuno scrive
  è un file che al momento del bisogno non si apre. Non sostituisce il
  backup giornaliero — è la rete per i cinque minuti attorno al
  deploy, quando gira anche `init_db` con le sue migrazioni.
  IL BACKUP CHE ESCE, PRIMA DI OGNI DEPLOY (19 ott 2026, cantiere
  backup-deploy; perché in CANTIERI, «Il backup prima di ogni deploy»).
  Dopo la copia locale e prima del `git reset`, `deploy.sh` lancia
  `deploy/backup-fuori.sh --prima-del-deploy <commit>`: lo stesso
  archivio cifrato del giornaliero, sullo stesso canale e col suo bot,
  col nome `barattolo-<data>-deploy-<commit>.tar.gz.age` e «prima del
  deploy <commit>» nella didascalia. Tetto 120 secondi; se non parte il
  deploy VA AVANTI e arriva «⚠️ Il backup su Telegram prima del deploy
  non è partito» nella stanza degli errori. In `backup/fuori/` ne
  restano le ultime 10 (il canale le tiene tutte). Ogni backup, anche
  quello delle 04:30, chiede se il file è sano (dal 20 ott con
  `integrity_check` sulla copia, qui sotto): un file non sano lo dice
  SUBITO sul canale dei backup («⚠️ il database NON è sano») e la
  didascalia porta «⚠️ DATABASE NON SANO». Oltre i 45 MB
  l'archivio si spezza in parti da 45 («parte 1 di N»; si ricuciono
  con `cat`, deploy/RIPRISTINO.md). Anche la copia locale non riuscita
  ora arriva in chat.
  UNA COPIA SOLA, CHE ASPETTA (20 ott 2026, cantiere
  backup-database-occupato; perché in CANTIERI, «Il backup col database
  occupato»). Tutte le copie del database — pre-deploy, giornaliero,
  LNbits — le fa `deploy/copia-db.py`: API di backup in un passo, 30 s
  di attesa sul lucchetto, TETTO 90 s (poi rinuncia), `integrity_check`
  sulla copia. Prima del deploy l'archivio nasce dalla copia locale
  (`--copia backup/pre-deploy-….db`): il vivo si legge una volta. Il
  journal dice «💾 copia del database messa da parte, integra: <file>»;
  l'avviso nella stanza degli errori dice lo stato vero: «non è partito
  … la copia locale c'è ed è integra», «NON è integra» (database vivo
  rotto: prima di toccare si chiede a Claude), «NON è riuscita» (nessuna
  copia e nessun archivio). IL GIORNALIERO ORA PARLA NELLA STESSA
  STANZA: se cade (copia, archivio, invio, env mancante) o trova il
  database rotto, «⚠️ Il backup giornaliero …» arriva dal bot di
  Barattolo, via `deploy.sh --avvisa`. Niente da installare: il
  pre-deploy nuovo vale dal deploy DOPO quello che lo porta (il timer
  ricopia `deploy.sh` a ogni giro; il primo archivio lo fa ancora lo
  script vecchio), il giornaliero dalla notte dopo. LA PROVA: al
  secondo deploy, `journalctl -u barattolo-deploy --since "15 min ago"
  | grep -E "💾|📦"` — «integra» e «archivio cifrato mandato».
  I RITOCCHI (20 ott 2026, cantiere backup-ritocchi; CANTIERI, «I
  ritocchi del backup»): prima del deploy la copia di LNbits ha un tetto
  corto (15 s + 10 di attesa, cintura 30), così l'archivio sta nei suoi
  120 s anche con LNbits occupato; `cambio-utente.sh` copia con lo
  stesso `deploy/copia-db.py`; il giornaliero fermato dal SIGTERM dei
  600 s avvisa da solo («⚠️ Il backup giornaliero è stato fermato prima
  di finire») e lascia il segno in `backup/.giornaliero-avvisato`.
  IL GIORNALIERO FERMATO DA FUORI — DA FARE ALLA PROMOZIONE (una volta,
  da root, dopo che il commit è su main e il deploy l'ha tirato): la
  unit del backup prende `ExecStopPost=` → `deploy/backup-caduto.sh`,
  che parla quando il backup non ha potuto (SIGKILL, memoria finita) e
  tace se ha già detto. La unit sta in `/etc` e il deploy non la tocca:
  1) guardare che le differenze siano SOLO le righe nuove (il commento,
     `apt install age`, `ExecStopPost=`); altro → ci si ferma e si chiede:
     `diff /etc/systemd/system/barattolo-backup.service /srv/barattolo/deploy/barattolo-backup.service`
  2) la copia di riserva, poi la unit nuova:
     `cp -a /etc/systemd/system/barattolo-backup.service /root/barattolo-backup.service.prima-20261020`
     `cp /srv/barattolo/deploy/barattolo-backup.service /etc/systemd/system/ && systemctl daemon-reload`
  3) la prova, senza far partire un backup:
     `systemd-analyze verify /etc/systemd/system/barattolo-backup.service`
     (nessuna riga di errore) e
     `systemctl show barattolo-backup -p ExecStopPost | grep -c backup-caduto`
     (dice 1). Il timer non va toccato. Facoltativo, e manda un avviso
     VERO nella stanza degli errori: `SERVICE_RESULT=timeout
     INVOCATION_ID=prova-a-mano bash /srv/barattolo/deploy/backup-caduto.sh`.
  TORNARE INDIETRO:
  `cp /root/barattolo-backup.service.prima-20261020 /etc/systemd/system/barattolo-backup.service && systemctl daemon-reload`.
  Senza questo gesto non si rompe niente: manca solo l'ultima rete.
  (19 ott 2026) L'UNITÀ DEL DEPLOY VA RICOPIATA UNA VOLTA (il deploy non
  tocca `/etc`): `TimeoutStartSec` passa da 300 a 600 —
  `cp /srv/barattolo/deploy/barattolo-deploy.service /etc/systemd/system/ && systemctl daemon-reload`.
  LA PROVA, al primo deploy dopo questo: sul canale dei backup un
  archivio «prima del deploy …», e
  `journalctl -u barattolo-deploy --since "15 min ago" | grep "📦"`.
  A MANO, quando serve: `./deploy.sh --dimmi` dice a che punto sta
  senza toccare niente, `--forza` riapplica e riavvia. Il primo giro
  (installazione del timer) è in `deploy/barattolo-deploy.service` e
  `.timer`. `prove.py` difende le quattro righe che contano — il
  semaforo che aspetta i due job, il freno, l'ordine del rollback, e
  la salute che non racconta niente di sé.
  IL MINUTO SI CONTA DA QUANDO `pronto` SI MUOVE, NON DA QUANDO SI FA
  PUSH (set 2026, dal cantiere del conteggio visualizzazioni): prima
  del timer sul VPS c'è la CI remota — le prove di `prove.py`, che sono
  9500+ e crescono, e dal 22 set 2026 i collaudi in gabbia, una
  ventina di secondi — e quel giro ha il suo tempo, non incluso nel
  «minuto». Verificare un deploy subito dopo il push con una richiesta
  che tocca il codice nuovo (mai solo `/api/salute`, che risponde
  identica prima e dopo) può cadere nella finestra in cui `pronto` non
  si è ancora mosso: sembra un difetto del codice ed è solo la CI
  che sta ancora girando. Aspettare di più prima di concludere che
  qualcosa non funziona, o controllare `--dimmi` da chi ha le chiavi.
  ⚠️ DOPO UN COMMIT CHE TOCCA IL WORKFLOW `pronto` PUÒ RESTARE INDIETRO
  (24 set 2026, `782b70e`): `prove` e `segreti` verdi, e il job `pronto`
  rosso con «refusing to allow a GitHub App to create or update workflow
  `.github/workflows/prove.yml` without `workflows` permission» — GitHub
  non ha lasciato al token delle Actions spostare il ref. Non succede a
  ogni modifica del workflow (`c1d1fdd` e `36f61dd` erano passati), ma
  quando succede il VPS resta fermo al commit di prima, e lo si vede da
  `git ls-remote origin refs/heads/pronto refs/heads/main`: due SHA
  diversi. DUE STRADE, tutt'e due buone: aspettare il commit successivo
  con la CI verde, che porta `pronto` fino a lui (quel giorno l'ha fatto
  `fed4697`, pochi minuti dopo); oppure spostarlo A MANO, SENZA FORZARE:
  `git fetch origin` e poi `git push origin origin/main:refs/heads/pronto`
  — è un avanti veloce, e se `pronto` non fosse un antenato di quel
  commit il push si rifiuterebbe da solo invece di spostarlo di lato;
  mai `--force`. Il giudice di `deploy.sh` resta quello di sempre (su
  main, in avanti, `prove` e `segreti` in `success`, punta firmata): il
  ref spostato a mano è solo il campanello.
  DAL 13 OTT 2026 UN COLLAUDO NUOVO NON TOCCA PIÙ IL WORKFLOW (cantiere
  «pronto-libero»): era la ragione di quasi tutti questi rifiuti — ogni
  cantiere col suo collaudo aggiungeva un nome ai due elenchi dentro
  `prove.yml`, e il 13 ott `pronto` si è fermato tre volte in una
  mattina. I due elenchi ora stanno in `ci/collaudi.txt` e
  `ci/compila.txt`: un collaudo o uno script nuovo è una riga là, e il
  workflow dice solo dove leggerli. L'AVVISO DI SOPRA RESTA VERO per
  ogni altra modifica a `.github/workflows/` (una action aggiornata, un
  passo nuovo, una forma in più fra le `FORME` dei segreti): lì si
  guarda come sempre, e `pronto` si sposta a mano col via di Andrea.
- IL RUNNER DELLA CI SULLA VM-2050 (20 ott 2026, cantiere runner-vm;
  perché e limiti in CANTIERI, «Il runner della CI sulla vm-2050»). Il
  job `prove` di main può girare sulla VM di collaudo
  (`vm-2050.lnvps.cloud`) invece che su GitHub: zero minuti. `segreti` e
  `pronto` restano su GitHub. I gesti sulla VM li scrive la sessione e
  li fa uno alla volta col via di Andrea (come per il collaudo).
  LA LEVA è la variabile del repo `RUNNER_PROVE`, in GitHub → Settings →
  Secrets and variables → Actions → Variables: `vm-2050` = sulla VM,
  vuota o cancellata = su GitHub (GitHub non accetta un valore vuoto:
  «vuota» è il cestino). Si cambia SENZA commit. ⚠️ LA VARIABILE SI LEGGE
  QUANDO IL GIRO NASCE, non quando il suo job parte (visto il 20 ott
  2026: il giro di `f9b01ed`, nato alle 13:39 senza variabile, è andato
  su GitHub anche se `vm-2050` era tornata alle 13:46, prima che i suoi
  job partissero): vale per i giri CREATI dopo il cambio, e un giro già
  in coda resta dov'era destinato. Un lancio a mano su un ramo va sempre
  su GitHub.
  LA VM SPENTA (o il runner offline): il giro resta «Queued» e la coda
  tiene fermi i push dopo di lui; il giudice del VPS dice «aspetta» e
  non deploya niente. Si cancella `RUNNER_PROVE`, poi si annullano il
  giro appeso E quello in coda (Actions → il giro → Cancel workflow:
  tutt'e due nati con la variabile, tutt'e due aspetterebbero la VM), e
  si fa nascere un giro nuovo su main: un push qualunque, o il commit
  vuoto firmato «Rilascio» (`git commit --allow-empty -m "Rilascio" &&
  git push origin HEAD:main`). Un «Re-run all jobs» del giro vecchio NON
  è provato: potrebbe tenersi la variabile di quando era nato. Riaccesa
  la VM, si rimette `vm-2050`.
  COSA C'È SULLA VM (tutto fuori dal collaudo, che non si tocca):
  l'utente `ci` (senza password, senza sudo, fuori da `docker` e
  `collaudo`); il runner in `/home/ci/actions-runner` (registrato SOLO su
  questo repo, nome ed etichetta `vm-2050`, niente etichette di serie,
  si aggiorna da solo); la dispensa in `/opt/hostedtoolcache` (`ci:ci`
  750; Python 3.12.15 e Node 22.23.3, le stesse build di GitHub, nello
  stesso percorso: il Python di GitHub cerca le sue librerie lì); la
  guardia `/opt/ci-guardia/solo-main.sh` (`root:root` 755, copia di
  `deploy/ci-vm/solo-main.sh`); il servizio
  `/etc/systemd/system/ci-runner-vm-2050.service` e il suo drop-in
  `ci-runner-vm-2050.service.d/guardia-e-limiti.conf` (copie di
  `deploy/ci-vm/`, `root:root` 644: la guardia in `Environment=`, i tetti
  2 GB / 2,5 GB / 1 GB di swap, le cartelle del collaudo nascoste); lo
  swap `/swapfile` da 2 GB con `vm.swappiness=10`
  (`/etc/sysctl.d/90-swap-ci.conf`); LLMNR spento
  (`/etc/systemd/resolved.conf.d/90-niente-llmnr.conf`).
  I FILE DEL REPO E QUELLI DELLA VM si confrontano così, dal PC (a
  capo Unix, i checkout Windows sono CRLF):
  `tr -d '\r' < deploy/ci-vm/solo-main.sh | sha256sum` contro
  `sha256sum /opt/ci-guardia/solo-main.sh` sulla VM; lo stesso per i
  due file di systemd. Si copiano con `tr -d '\r'`, mai a mano.
  IL `.env` DEL RUNNER È DI ROOT E IMMUTABILE (`chattr +i`): il runner lo
  legge all'avvio e ogni sua riga vince sull'ambiente di systemd, anche
  per cancellare la guardia; la cartella è di `ci`, e senza `+i` potrebbe
  cancellarlo e rifarlo. Quando serve toccarlo (un aggiornamento che
  chiede una riga nuova, la rimozione del runner), e SOLO per quel gesto:
  `sudo chattr -i /home/ci/actions-runner/.env`, il gesto, e SUBITO
  `sudo chown root:root /home/ci/actions-runner/.env && sudo chmod 644
  /home/ci/actions-runner/.env && sudo chattr +i
  /home/ci/actions-runner/.env`, poi `sudo lsattr` (deve mostrare la `i`)
  e `sudo systemctl restart ci-runner-vm-2050`. Gli aggiornamenti
  normali del runner il `.env` non lo toccano.
  TOGLIERE IL RUNNER: GitHub → Settings → Actions → Runners → `vm-2050`
  → Remove (dà il comando col token di rimozione), poi sulla VM
  `sudo systemctl disable --now ci-runner-vm-2050`, `chattr -i` sul
  `.env` come sopra e, come `ci`, `./config.sh remove` col token letto
  da `read -rsp` (mai in chat). Il rimedio d'urgenza, se si sospetta
  la chiave del runner copiata: Remove da GitHub e basta, la chiave
  muore lì.
  LA PROVA DI ISOLAMENTO SI RIFÀ quando nasce qualcosa di nuovo del
  collaudo (la deploy key, un servizio): come `ci`, `cat` e `ls` sui
  file nuovi devono dire «Permission denied», e
  `sudo -u ci find / -xdev \( -user collaudo -o -group collaudo \)
  -readable 2>/dev/null` deve uscire vuoto.
- IL RIAVVIO DOLCE (1 ott 2026): un deploy non deve far vedere un 502.
  DUE PEZZI SUL VPS, tutt'e due fuori dalla repo come il resto della
  macchina (il drop-in ha la sua copia in `deploy/utente/`):
  1) CADDY ASPETTA IL BACKEND invece di rispondere 502. In TUTTI E DUE i
     blocchi del Caddyfile (il sito e l'onion) la riga `reverse_proxy …:8080`
     e' diventata un blocco con `lb_try_duration 30s` e
     `lb_try_interval 250ms`: col backend spento Caddy ritenta la
     connessione ogni quarto di secondo per 30 secondi, e la richiesta
     arriva quando il server e' su. Copre la PAGINA stessa, le foto, i
     font e il webhook di Telegram, che il client non puo' coprire.
     Ritenta solo quando la connessione NON e' partita, quindi una POST
     non arriva due volte al server. Copia di prima:
     `/etc/caddy/Caddyfile.prima-del-riavvio-dolce`. Si controlla con
     `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` e
     si ricarica con `systemctl reload caddy`, che non interrompe nessuno
     e con una configurazione storta tiene la vecchia.
     TORNARE INDIETRO: `cp -a /etc/caddy/Caddyfile.prima-del-riavvio-dolce
     /etc/caddy/Caddyfile && systemctl reload caddy`.
  2) IL DROP-IN `barattolo.service.d/riavvio-dolce.conf` (copia in
     `deploy/utente/barattolo-riavvio-dolce.conf`, col perche' di ogni
     riga): `TimeoutStopSec=20` e
     `Environment=UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=10`. Si posa ACCANTO
     a `utente.conf` senza toccarlo, poi `systemctl daemon-reload`; vale
     dal riavvio SUCCESSIVO (il primo deploy). Prima di posarlo:
     `python3 -m uvicorn --help | grep graceful` deve rispondere, o la
     variabile non la legge nessuno. Dopo un riavvio si vede nel processo:
     `tr '\0' '\n' < /proc/$(systemctl show -p MainPID --value barattolo)/environ | grep UVICORN`.
     TORNARE INDIETRO: `rm` del drop-in e `systemctl daemon-reload`.
  I 30 SECONDI DI CADDY VALGONO SE IL BUCO CI STA DENTRO: di solito ~1,5
  s (il journal del 30 set, cinque riavvii), ma alle 20:50 lo stop e'
  durato 90 s e systemd ha dovuto ammazzare il processo (SIGKILL). La
  cura di quello sta nel codice — il giro dei connettori si ferma allo
  spegnimento (ARCHITETTURA, «IL SERVER CHE SI RIAVVIA») — e il tetto
  dei 20 secondi e' la rete per ogni altro filo lungo.
  COME SI MISURA UN BUCO: `journalctl -u barattolo --since today -o
  short-precise | grep -E "Stopping|Started|Application startup
  complete"`; uno stop ammazzato lo dice `grep -iE "timed out|kill"`.
  POSATO IL 1 OTT 2026, tutt'e due i pezzi. LA PROVA CHE SI RIFA' (un
  riavvio vero: mai durante un deploy in corso) — 60 richieste attraverso
  Caddy con un restart nel mezzo, deve dire solo 200:
  `( for i in $(seq 1 60); do curl -s -o /dev/null -w "%{http_code}
  %{time_total}\n" --max-time 40 https://barattolo.store/api/salute;
  sleep 0.25; done > /tmp/prova-riavvio.txt ) & sleep 3; systemctl
  restart barattolo; wait; awk '{print $1}' /tmp/prova-riavvio.txt |
  sort | uniq -c; sort -k2 -n /tmp/prova-riavvio.txt | tail -3`
  (il primo giro: 60 a 200, la piu' lenta 1,6 s — quella nel buco).
  IL CONTROLLO SUL PROCESSO VIVO dopo un riavvio: `systemctl show
  barattolo -p ActiveEnterTimestamp` e la riga `tr … environ | grep
  UVICORN` qui sopra, che deve dire `UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN=10`.
- IL JOURNAL SENZA BUFFER (19 ott 2026, cantiere journal-senza-buffer,
  richiesta di Andrea): ogni `print` del server arriva SUBITO nel
  journal, anche quelle senza `flush=True`. Il 15-17 ott le righe
  «saltato» di `promo_venduto` e `promo_rimuovi` sono scattate e si sono
  perse ai riavvii (CANTIERI, «Il ✅ Venduto e il ritiro dei post»). È
  il drop-in `barattolo.service.d/journal.conf` (copia in
  `deploy/utente/barattolo-journal.conf`, col perché): una riga,
  `Environment=PYTHONUNBUFFERED=1`. Si posa ACCANTO a `utente.conf` e
  `riavvio-dolce.conf` senza toccarli, poi `systemctl daemon-reload`;
  vale dal riavvio SUCCESSIVO — il prossimo deploy lo fa da solo, o un
  `systemctl restart barattolo` (il riavvio dolce: ~1,5 s di buco che
  Caddy copre; mai durante un deploy in corso). Dopo il riavvio si vede
  nel processo:
  `tr '\0' '\n' < /proc/$(systemctl show -p MainPID --value barattolo)/environ | grep PYTHONUNBUFFERED`
  deve dire `PYTHONUNBUFFERED=1`.
  TORNARE INDIETRO: `rm` del drop-in e `systemctl daemon-reload`.
- IL COOKIE SUL TUNNEL (10 ott 2026, cantiere cookie-onion): dal `.onion`
  il login reggeva SOLO con Tor Browser, che tratta l'onion come contesto
  sicuro; Chrome, Brave e Vanadium con Orbot scartano un cookie «Secure»
  dato su http, e di là si restava in vetrina. Il server ora dà il cookie
  di sessione (e il portachiavi, suo gemello) SENZA Secure quando DUE
  testimoni dicono «tunnel»: l'Host (`ONION_HOST`, il giudice di sempre)
  e l'header `X-Barattolo-Onion` col segreto `ONION_SEGNALE`, che mette
  SOLO il blocco onion di Caddy e che il blocco pubblico CANCELLA. Tutto
  il resto del cookie è uguale (HttpOnly, SameSite=Lax, 30 giorni, `/`).
  Sul dominio pubblico non cambia niente; senza la leva nel config non
  cambia niente da nessuna parte (il perché e le prove: Architettura,
  «IL COOKIE SUL TUNNEL HA DUE TESTIMONI»). LA PROCEDURA, in ordine:
  1) il segreto, una riga da copiare in due posti: `openssl rand -hex 24`.
  2) nel config del VPS (`/srv/barattolo/config.py`, da `barattolo`), accanto
     a `ONION_HOST`: `ONION_SEGNALE = "INCOLLA_QUI_IL_SEGRETO"` (il valore vero al posto
     del segnaposto).
  3) nel Caddyfile (`/etc/caddy/Caddyfile`, da root), prima la copia:
     `cp -a /etc/caddy/Caddyfile /etc/caddy/Caddyfile.prima-del-cookie-onion`.
     Nel blocco dell'ONION (quello di `http://ckmc…onion:8081`), DENTRO il
     suo `reverse_proxy 127.0.0.1:8080 { … }` (è già un blocco dal riavvio
     dolce), la riga:
       `header_up X-Barattolo-Onion "<il segreto>"`
     Nel blocco PUBBLICO (`barattolo.store`), dentro il suo
     `reverse_proxy … { … }`, la riga:
       `header_up -X-Barattolo-Onion`
     (col MENO davanti: cancella l'header se un client da internet lo
     manda da sé). Il blocco onion deve ascoltare solo dove bussa Tor:
     `ss -ltnp | grep 8081` deve dire `127.0.0.1:8081`; se dice `*:8081`
     o `0.0.0.0:8081`, dentro quel blocco anche la riga `bind 127.0.0.1`.
  4) `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`,
     poi `systemctl reload caddy` (con una configurazione storta tiene
     la vecchia), poi `systemctl restart barattolo` (il config si legge
     all'avvio).
  5) LA CONTROPROVA: nel pannello «⚙️ Stato delle leve» dell'admin la
     leva «Cookie senza Secure sul tunnel Tor» è accesa. Dal telefono,
     Chrome con Orbot in modalità VPN — nelle impostazioni Android
     «Private DNS» su Off, o l'indirizzo `.onion` non si risolve — si
     entra con Nostr dal `.onion` e si RICARICA: si resta dentro. Su
     barattolo.store tutto com'era: login, ricarica, logout.
  FATTA IL 10 OTT 2026 ALLE 17:11 (Andrea): leva nel config, le due
  righe nel Caddyfile (validate e reload ok), restart; pubblico 200, via
  Tor 200, e dal telefono il login Nostr sul `.onion` regge alla
  ricarica. Da allora questa è la configurazione viva del VPS.
  TORNARE INDIETRO: via la riga `ONION_SEGNALE` dal config (o vuota) e
  `systemctl restart barattolo` — il cookie torna Secure ovunque anche
  con le righe di Caddy ancora lì (un testimone solo non basta); le righe
  si tolgono con la copia di prima e `systemctl reload caddy`.
- LA CSP ACCESA (10 ott 2026, cantiere csp-accesa): le pagine rispondono
  con una `Content-Security-Policy` VERA — il browser blocca script da
  host estranei, `<base>`, plugin e form verso fuori — e riferiscono
  ancora a `/api/csp-report` (journal «🛡️ CSP:», una riga al minuto per
  violazione, 120 al minuto in tutto). Lo script inline resta ammesso
  (`'unsafe-inline'`): la fase 2 è un cantiere a sé (CANTIERI, «La CSP
  accesa», lo studio). LA LEVA `CSP_ATTIVA` NASCE ACCESA NEL CODICE: non
  va aggiunta al config per accenderla. SE QUALCOSA SI ROMPE, senza
  deploy: nel config del VPS (`/srv/barattolo/config.py`, da `barattolo`)
  la riga `CSP_ATTIVA = False`, poi `sudo systemctl restart barattolo`;
  la CSP torna in sola prova (`Content-Security-Policy-Report-Only`,
  stesse direttive, stesso cestino) e il pannello «⚙️ Stato delle leve»
  la mostra spenta. Per riaccenderla: via la riga (o `True`) e riavvio.
  COSA GUARDARE PRIMA E DOPO: il journal,
  `journalctl -u barattolo --since "1 day ago" | grep "🛡️ CSP:"` — una
  riga dice direttiva, cosa è stato bloccato, `@ file:riga` e la pagina,
  più un campione fra «»; le righe da estensioni (host che non sono
  nostri, `chrome-extension`, `safari-extension`) sono rumore giusto da
  bloccare, una riga su un nostro file o su `telegram.org` va letta. E
  il Login Widget sul sito (fuori da Telegram): deve comparire e far
  entrare — i suoi fogli e il font (telegram.org/css, /fonts) sono
  ammessi apposta su `style-src` e `font-src`.
- LE SESSIONI CLOUD (24 set 2026, regola di Andrea): una sessione di
  Claude Code che gira nel cloud (claude.ai/code, o una sessione spostata
  lì dal PC) lavora su un ramo `cantiere/<nome>` e apre una PR verso
  main — MAI un push su main. È l'unica eccezione a «si pusha su main,
  mai su un ramo», e ha due perché.
  LA FIRMA: il VPS tira solo una punta FIRMATA da una chiave di
  `/etc/barattolo-deploy/firmatari` (vedi «IL DEPLOY CHE SI FIDA SOLO DI
  MAIN»), e quella chiave vive sul PC. Dal cloud un push arriverebbe
  nudo e verrebbe rifiutato — e portare la chiave lassù per farlo
  passare è proprio quel che la firma deve impedire: è la sola difesa
  che regge a un GitHub bucato, e regge finché la chiave non ci sta.
  IL BANCO: nel cloud non ci sono `config.py`, il browser col relay
  morto, il telefono, l'APK. `prove.py` e i collaudi in gabbia girano
  (la CI parte anche sulla PR: il workflow ha `pull_request:`, e il job
  `pronto` resta fermo perché vuole un push su main), le prove dal vivo
  no. Quindi la sessione cloud scrive nel suo verbale in CANTIERI cosa
  NON ha potuto provare, invece di lasciarlo intendere.
  LE PROVE DAL VIVO RESTANO ALLE SESSIONI SUL PC — config, browser col
  relay morto, app Android, telefono —, e si fanno PRIMA del merge, sul
  ramo, in un worktree suo (mai nella cartella condivisa):
  `git fetch origin`
  `git worktree add .claude/worktrees/<nome> origin/cantiere/<nome>`
  Se dal vivo esce un difetto, la cura va sul ramo: la PR si aggiorna da
  sé, e il merge aspetta.
  IL MERGE LO FA UNA PERSONA DAL PC, firmato, anche lui in un worktree:
  `git fetch origin`
  `git worktree add --detach .claude/worktrees/merge-<nome> origin/main`
  `git -C .claude/worktrees/merge-<nome> merge --no-ff -S origin/cantiere/<nome>`
  `git -C .claude/worktrees/merge-<nome> cat-file commit HEAD` — deve
  esserci la riga `gpgsig`
  `git -C .claude/worktrees/merge-<nome> push origin HEAD:main`
  `--no-ff` NON È ESTETICA: `deploy.sh` guarda la firma della sola
  PUNTA, e un avanti veloce metterebbe in punta l'ultimo commit nato nel
  cloud, che firmato non è — rifiutato. Col merge la punta è il commit
  di merge, firmato qui; i commit del ramo restano senza firma, e va
  bene così. `-S` si scrive anche se `commit.gpgsign` è acceso: su
  un'altra macchina potrebbe non esserlo. La CI verde della PR NON è
  quella che il giudice chiede: `giudice_deploy.py` vuole il giro nato
  dal push SU MAIN, che parte col push del merge — quindi fra il push e
  il deploy passa un giro intero di CI. ⚠️ MAI il bottone «Merge» del
  SITO di GitHub: quel commit lo firma GitHub, e il VPS lo rifiuta (se
  succede, un commit firmato sopra, come scritto là).
  LA PULIZIA A FINE GIRO, dopo che il push del merge è passato (GitHub
  segna la PR come «merged» da solo, perché i suoi commit ora stanno su
  main):
  `git worktree remove .claude/worktrees/merge-<nome>`
  `git worktree remove .claude/worktrees/<nome>` (se c'era il giro dal
  vivo)
  `git push origin --delete cantiere/<nome>`
  `git fetch --prune origin`
  Un ramo `cantiere/*` rimasto su origin dopo il merge è una riga di
  troppo nell'elenco, non un pericolo: il deploy non lo guarda.
- La verifica npub richiede `websocket-client` (pip) nell'ambiente del
  servizio: se manca, il server parte lo stesso e l'endpoint risponde 503.
- La pubblicazione su Nostr richiede anche `coincurve`: installarla con
  `pip install --only-binary :all: coincurve` (le versioni 20/21 senza
  wheel provano a compilare e falliscono; la 19.0.1 ha wheel ovunque).
  Se manca, o se `NOSTR_NSEC_PIATTAFORMA` resta il segnaposto, la
  funzione Nostr si spegne da sola e il resto vive normalmente.
  Anche il LOGIN Nostr dipende da coincurve (verifica Schnorr): senza,
  i suoi endpoint rispondono 503 e tutto il resto vive.
- Le notifiche via DM Nostr richiedono anche `cryptography` (ChaCha20
  per NIP-44): `pip install cryptography` nell'ambiente del servizio,
  PRIMA del restart. Se manca, il canale DM si spegne da solo (riga
  in console) e le notifiche Telegram vivono come sempre.
- Le foto HEIC degli iPhone (caricate da Android/desktop) richiedono
  `pip install pillow pillow-heif` nell'ambiente del servizio
  (entrambe hanno wheel, niente compilazioni). Se mancano, i JPEG
  vivono come sempre e solo le HEIC non convertibili si saltano.
- LA CASSAFORTE SUL NODO (set 2026): LNbits self-hosted in
  `/opt/lnbits` (Docker `docker.io` + `docker-compose-v2` di Ubuntu,
  immagine `lnbits/lnbits:v1.6.1` PINNATA nel compose — mai `latest`;
  si aggiorna cambiando il tag e `docker compose pull && up -d`, a
  ordini fermi). Ascolta SOLO su `127.0.0.1:5001`, coi numeri SCRITTI
  nel `command:` del compose: le env `HOST`/`PORT` del `.env` NON
  contano (i nomi veri sono `LNBITS_HOST`/`LNBITS_PORT`) e il primo
  avvio e' finito su 0.0.0.0:5000. Ogni futura `ports:` in bridge si
  scrive `127.0.0.1:…`, mai nuda: Docker aggira `ufw`. Il pannello si
  apre dal PC con `ssh -N -L 5001:127.0.0.1:5001 root@VPS` e poi
  `http://127.0.0.1:5001` (login «LNbits nodo» in KeePass); creazione
  di nuovi utenti spenta, solo username/password.
  IL PONTE VERSO LND — ⚠️ DAL 21 SET 2026 PASSA DA WIREGUARD (voce
  sua più sotto, «IL PONTE VIA WIREGUARD»): quel che segue è il ponte
  DI PRIMA, che dopo il trasloco resta installato e spento col nome
  `lnd-ponte-tor.service`, il piano B. Il cert, il macaroon e i tre
  `curl` valgono identici sulle due strade.
  `lnd-ponte.service` (socat) ascolta su
  `127.0.0.1:18080` e infila tutto nel tor del VPS verso l'hidden
  service della REST di LND sul nodo, che ha il client-auth v3: la
  chiave privata sta in `/var/lib/tor/onion_auth/lnbits.auth_private`
  (`ClientOnionAuthDir` nel torrc), la pubblica in
  `~/nodo/tor/data/lnbits/authorized_clients/vps.auth` sul nodo. Senza
  la chiave la porta non esiste. Il TLS e' end-to-end col `tls.cert`
  di LND copiato in `/opt/lnbits/data/tls.cert` (SAN `127.0.0.1`):
  SCADE IL 22 OTT 2027 — quel giorno LND lo rigenera e la copia sul
  VPS va rifatta, o LNbits smette di fidarsi del ponte con un errore
  che sa di rete.
  ⚠️ E LE COPIE SUL VPS SONO DUE, dal 21 set 2026: il SERVER di
  Barattolo (i pagamenti in volo, che chiedono la verità a LND) non
  legge quella di LNbits ma una copia SUA,
  `/etc/barattolo/lnd-tls.cert`, dichiarata nel config come
  `LND_PONTE_CERT` — perché da quel giorno il servizio gira da
  `barattolo` e in `/opt/lnbits/data` quell'utente non entra. Quando
  LND rigenera il suo cert, rifatta la copia di LNbits va rifatta
  ANCHE questa, o è il server a non fidarsi più del ponte mentre
  LNbits paga benissimo:
  `install -m 644 -o root -g root /opt/lnbits/data/tls.cert /etc/barattolo/lnd-tls.cert && systemctl restart barattolo`
  (644 e di root: un certificato è pubblico, `barattolo` lo deve
  leggere e non lo deve poter cambiare.) Il macaroon (`LND_REST_MACAROON` nel `.env`, 600) e'
  dedicato, `root_key_id 1`: si revoca da solo con
  `lncli deletemacaroonid 1` sul nodo. Diagnosi in tre `curl` dal VPS:
  `-k` su `https://127.0.0.1:18080/v1/getinfo` (il ponte arriva?),
  `--cacert /opt/lnbits/data/tls.cert` (il cert combacia?), con
  l'header `Grpc-Metadata-macaroon` letto da file (il macaroon
  apre?); ognuno risponde a una domanda diversa.
  IL GUARDIANO DEL PONTE (18 set 2026, dopo nove ore di acquisti
  falliti senza che nessuno lo sapesse): il server fa da solo la PRIMA
  delle tre domande, ogni minuto. Al terzo «no» di fila riavvia LA
  STRADA IN PIEDI (21 set 2026) — la chiede a systemd nell'istante
  della cura: piano B acceso (`is-active lnd-ponte-tor`) → `tor` e
  `lnd-ponte-tor`; sennò tunnel abilitato (`is-enabled wg-quick@wg0`)
  → `wg-quick@wg0` e `lnd-ponte`; sennò, su una macchina senza tunnel,
  `tor` e `lnd-ponte` come prima. Nessun ripiego automatico su tor:
  l'avviso del fallimento porta scritto il comando del piano B.
  Riguarda dopo 90 secondi (erano 45: a tor non bastavano, e l'esito
  diceva «ancora giù» di un ponte vivo un minuto dopo) e lo scrive su
  Telegram (il guasto prima
  del riavvio, l'esito dopo), al massimo un avviso ogni 15 minuti; una
  cura che non ha curato non si ripete prima di 15 minuti. Il perché
  di ogni numero sta in CANTIERI, «Il guardiano del ponte verso LND».
  DOVE SI LEGGE: `journalctl -u barattolo | grep 🌉` — all'avvio c'è
  sempre la riga «Guardiano del ponte verso LND: acceso» (o «spento»,
  col perché), poi solo i cambi. E da fuori `/api/salute` porta
  `"ponte"`: `ok`, `giu`, `attesa` (prima del primo controllo) o
  `spento`. A CHI SCRIVE: gli id di `GUARDIANO_PONTE_AVVISA = [...]`
  nel config, e a lista vuota (o riga assente) i moderatori. LEVA:
  `GUARDIANO_PONTE = False` + riavvio lo spegne. IL RIAVVIO NON
  RICHIEDE PIÙ ROOT (21 set 2026): da utente `barattolo` i quattro
  riavvii passano da `sudo -n /usr/bin/systemctl restart …`, e li
  permette `/etc/sudoers.d/barattolo-ponte` (copia in
  `deploy/utente/sudoers-barattolo-ponte`, tenuta uguale a
  `PONTE_STRADE` da una prova: chi aggiunge una strada RIMETTE il file
  sul VPS a mano, `/etc` non viaggia col deploy). Si controlla con
  `sudo -l -U barattolo` — quattro righe, nient'altro. Se la regola
  manca la cura fallisce e l'avviso lo dice con le parole di sudo («a
  password is required»). Da root (prima del cambio, o dopo un ritorno)
  il guardiano non usa sudo: guarda chi è nell'istante del comando.
  IL DRILL, a mercatino fermo: `systemctl stop lnd-ponte`
  (o, per il tunnel, `systemctl stop wg-quick@wg0`),
  e in circa tre minuti il guardiano lo deve rimettere su da solo,
  con i due avvisi. All'avvio il journal dice anche la strada che la
  cura prenderebbe: «🌉 La strada del ponte, vista da qui: …».
  Quello che NON vede: un cert scaduto, un macaroon
  che non apre, un LND bloccato che risponde — la seconda e la terza
  domanda restano a mano.
  LE LEVE DEL DOPPIO WALLET si AGGIUNGONO al config del VPS, come
  quelle del P2P: `LNBITS_NODO_URL = "http://127.0.0.1:5001"`,
  `LNBITS_NODO_INVOICE_KEY`, `LNBITS_NODO_ADMIN_KEY` (dal wallet
  «Cassaforte Barattolo», in KeePass) e `CASSAFORTE_NUOVA = True`,
  poi riavvio. All'avvio il journal dice «🔒 Cassaforte del denaro
  nuovo: nodo» — se dice `saas` con la leva True, mancano le chiavi e
  la riga sopra lo spiega. `False` e riavvio rimanda il nuovo sul
  SaaS; le righe gia' nate sul nodo continuano a chiudersi la'. Il
  SaaS si svuota e si disdice SOLO quando il polso 24 del libro mastro
  (`query_libro_mastro.sql`) da' zero righe aperte 'saas' — e non c'e'
  una data da ricordare: l'orologio fa lo stesso conto ogni dieci
  minuti (`avvisa_saas_senza_doveri`) e manda ai moderatori «🏁 Il
  SaaS non ha più doveri: si può aprire la fase 5» UNA volta, alla
  discesa a zero (timbro `saas_senza_doveri` in `timbri`: si riarma da
  solo se un dovere ricompare, e nel dubbio — un conteggio che esplode
  — non dichiara zero). Parla solo col denaro nuovo sul nodo.
  I PAGAMENTI DA VERIFICARE, il 🧊 (19 set 2026, dopo l'audit): un
  pagamento in USCITA di cui non si sa com'e' finito non lo decide
  piu' la parola di una persona. Prima di ogni decisione e di ogni
  ritentativo il server chiede la VERITA' a due fonti — LNbits (cosa
  ha chiesto al nodo) e LND (cosa e' uscito), e quando non combaciano
  ha ragione LND — su TUTTI gli hash tentati per quella riga (tabella
  `payout_tentati`). I cinque verdetti: `uscito` (si chiude come
  pagato), `fallito` e `mai_partito` (si puo' ripagare), `in_volo` e
  `ignoto` (NON PARTE NIENTE, ne' da un giro ne' da un bottone).
  COSA FA DA SOLO: l'orologio (ogni 10 minuti) richiede tutti gli
  `in_volo` E i congelati che hanno un hash. LNbits muta ma LND dice
  SUCCEEDED → chiude; LND dice FAILED → ritenta; LND non ha MAI visto
  l'hash e sono passati 15 minuti (`MAI_PARTITO_DOPO_S`) → «mai
  partito», ritenta; ancora in volo dopo 30 minuti → 🧊 e avviso ai
  moderatori. Un congelato che si chiarisce da solo manda «🧊→✅».
  COSA FA IL PANNELLO (Profilo → 🧊 Pagamenti da verificare):
  «🔎 Verifica e riprova» chiede alle fonti e poi — uscito: chiude;
  fallito o mai partito: RIPAGA SUBITO dalla strada di sempre (prima
  sbloccava e basta); in volo: rifiuta e resta 🧊; non verificabile:
  503 e resta 🧊. «✅ L'ho visto io: è uscito» vale da solo solo se le
  fonti dicono uscito; se dicono altro mostra COSA dicono e chiede una
  seconda conferma; su un pagamento in volo non passa nemmeno cosi'.
  ⚠️ UN PAGAMENTO «pending» DA ORE O GIORNI NON E' UN GUASTO: e' quasi
  sempre una HOLD INVOICE tenuta appesa da chi riceve. Si aspetta: si
  chiude da solo quando il nodo decide (al piu' tardi alla scadenza
  del CLTV). Dichiararlo «non uscito» era il modo di pagare due volte.
  DOVE SI LEGGE: `journalctl -u barattolo | grep -E "🔎|⚖️|🛬|✋"` —
  🔎 ogni verifica (riga, hash, voce di LNbits, voce di LND, verdetto),
  ⚖️ ogni decisione di un moderatore (chi, cosa ha chiesto, com'e'
  finita), 🛬 la ronda, ✋ una seconda mano respinta. All'avvio c'e'
  sempre «🔎 Verità dei pagamenti: LND ACCESO» (o SPENTO, col perche').
  IL MACAROON DI SOLA LETTURA (una volta sola). Questo server e'
  pubblico (e fino al set 2026 girava da root): una chiave che sa PAGARE qui non entra, e
  quella di LNbits resta dov'e'. Sul NODO, dalla cartella `~/nodo`:
  `docker compose exec lnd lncli bakemacaroon --root_key_id 2 --save_to /tmp/barattolo-lettura.macaroon offchain:read`
  (⚠️ dal 10 ott 2026 il macaroon vuole ANCHE `info:read`, e si rifà
  col root key 3: la procedura sta più sotto, «IL CONTROLLO DELLA
  FATTURA P2P»; questa riga resta per dire com'era)
  e poi `docker compose exec lnd xxd -p -c 9999 /tmp/barattolo-lettura.macaroon`
  (se il servizio non si chiama `lnd`, il nome giusto lo dice
  `docker compose ps`; se nel container manca `xxd`, lo stesso lo fa
  `od -An -tx1 -v FILE | tr -d ' \n'`). L'esadecimale va nel config
  del VPS:
  `LND_PONTE_MACAROON_LETTURA = "INCOLLA_QUI"`; `LND_PONTE_CERT` e
  `LND_PONTE_URL` hanno gia' i default giusti (`/opt/lnbits/data/tls.cert`
  e `https://127.0.0.1:18080`) — ⚠️ ma dal 21 set 2026 sul VPS
  `LND_PONTE_CERT` È DICHIARATO nel config e punta alla copia del
  server, `/etc/barattolo/lnd-tls.cert`: l'utente `barattolo` nel
  default non entra (vedi «SCADE IL 22 OTT 2027», qui sopra, per
  rifarla). Poi si cancella il file sul nodo e si
  riavvia `barattolo`. Si revoca da solo, senza toccare LNbits:
  `lncli deletemacaroonid 2`. Non passa MAI dal canale Telegram.
  Senza macaroon LND vale «spento»: decide LNbits da sola, come prima,
  ma con le regole nuove (pending = fermo, e i 15 minuti).
  ⚠️ «LND=n/a» NON è «LND=spento» (dal 22 set 2026): nelle righe 🔎 del
  journal e nel pannello 🧊, «n/a» vuol dire che quel pagamento è della
  cassaforte SaaS, dove un LND nostro non c'è — nessun guasto, niente
  da fare. «spento» su una riga del NODO vuol dire invece che il
  macaroon di lettura manca: quello sì si guarda. Il 20 set, sull'ordine
  #152, le due cose si scrivevano uguali e hanno fatto cercare un
  guasto che non c'era.
  IL CONTROLLO DELLA FATTURA P2P (10 ott 2026, cantiere
  controllo-fattura; il perché in CANTIERI, «Il controllo della fattura
  prima del coordinatore»). Prima che la fattura di chi compra parta
  verso il coordinatore, il server chiede al nostro LND se è pagabile:
  `GET /v1/payreq` (DecodePayReq), `GET /v1/graph/node/{pk}`
  (GetNodeInfo) e `POST /v1/graph/routes/{pk}/{sats}` (QueryRoutes),
  sullo stesso ponte e con lo stesso macaroon della verità dei
  pagamenti. ⚠️ GetNodeInfo e QueryRoutes vogliono `info:read`, e il
  macaroon del set 2026 ha solo `offchain:read`: finché non si rifà, il
  journal dice «· Fattura P2P: … nodo negato (permission denied):
  non_disponibile» e la fattura PASSA (il controllo non ferma mai quando
  non sa).
  ⚠️ FATTO IL 10 OTT 2026 (Andrea): sul nodo `lncli listmacaroonids`
  dice `0, 1, 4` — la root key 2 del macaroon di set 2026 NON ESISTE
  PIÙ, quindi la revoca `deletemacaroonid 2` non serve e non si fa; il
  macaroon nel config del VPS risponde a `GetNodeInfo` su ACINQ (la
  prova qui sotto), cioè ha `info:read`. Se un giorno si rifà: sul NODO
  da `~/nodo`, con un root key LIBERO (uno che `listmacaroonids` non
  elenca; l'1 è di LNbits), un comando per riga:
  `docker compose exec lnd lncli bakemacaroon --root_key_id 5 --save_to /tmp/barattolo-lettura.macaroon offchain:read info:read`
  `docker compose exec lnd xxd -p -c 9999 /tmp/barattolo-lettura.macaroon`
  `docker compose exec lnd rm /tmp/barattolo-lettura.macaroon`
  (l'esadecimale NON si incolla in chat né nel canale Telegram). Sul VPS,
  nel config (`/srv/barattolo/config.py`, a mano): si sostituisce il valore
  di `LND_PONTE_MACAROON_LETTURA` con l'esadecimale nuovo, e si AGGIUNGE
  la leva `P2P_TETTO_ROTTA = 0.01` (lo specchio di `max_routing_fee` nel
  `settings.toml` del nodo: se cambia là, va cambiato qui). Poi:
  `sudo systemctl restart barattolo`
  `journalctl -u barattolo -n 80 --no-pager | grep -E "🔎 Verità|⚡|Fattura P2P"`
  (si aspetta «🔎 Verità dei pagamenti: LND ACCESO»). LA VERIFICA che
  queryroutes risponda, dal VPS attraverso il ponte, col macaroon letto
  dal config senza stamparlo. La chiave pubblica di prova è quella di
  ACINQ, il nostro vicino (una strada di un salto, fee zero): sul NODO
  la dice `docker compose exec lnd lncli listchannels` alla voce
  `remote_pubkey`, e sul VPS si mette in `PK` a mano (è pubblica):
  `PK=INCOLLA_QUI_LA_REMOTE_PUBKEY`
  `MAC=$(grep -oP '^LND_PONTE_MACAROON_LETTURA\s*=\s*"\K[0-9a-f]+' /srv/barattolo/config.py)`
  `curl -s --cacert /etc/barattolo/lnd-tls.cert -H "Grpc-Metadata-macaroon: $MAC" https://127.0.0.1:18080/v1/graph/node/$PK | head -c 300; echo`
  `curl -s --cacert /etc/barattolo/lnd-tls.cert -H "Grpc-Metadata-macaroon: $MAC" -X POST -d '{"route_hints":[]}' https://127.0.0.1:18080/v1/graph/routes/$PK/1000 | head -c 400; echo`
  Col macaroon vecchio tutt'e due rispondono `"message": "permission
  denied"`; con quello nuovo il primo dà `"node": {"pub_key": …,
  "alias": "ACINQ" …}` e il secondo `"routes": [{… "total_fees": "0"
  …}]`. Se il secondo rispondesse «Not Found» o «405», la REST di quel
  LND non ha la POST su queryroutes: il controllo lo scrive come «rotte
  errore» e passa — si dice, e si cambia strada (la GET senza hint, o
  EstimateRouteFee). Il vecchio, se c'è ancora, si revoca solo DOPO il
  verde e solo dopo aver guardato chi lo usa: `lncli listmacaroonids` sul
  nodo (le root key vive), `lncli printmacaroon --macaroon_file …` sul
  macaroon di mostrod (il suo `root_key_id` dev'essere un altro), e
  LNbits è la root key 1 per costruzione; poi `lncli deletemacaroonid
  <id>`. DOVE SI LEGGE: `journalctl -u barattolo | grep "Fattura P2P"`
  — ⛔ fermata (importo, scadenza, rete, nodo assente, indirizzo), ⚠️
  avvisata col «Usa comunque» (nessuna strada, costo oltre il tetto),
  · non si è potuto controllare (col perché), ✅ ok; mai la fattura
  intera, solo l'ordine e la destinazione accorciati.
  Dal 16 ott 2026 (cantiere strada-phoenix) due righe in più, nessun
  passo sul VPS (i canali si leggono con `offchain:read`, che il
  macaroon ha già): «⚠️ … pezzo_solo» = una fattura senza MPP che
  intera non passa da nessun canale; «· … uscita_corta» col perché («a
  pezzi da N la strada c'è, ma l'uscita utilizzabile (X) non copre cifra
  + rete (Y)») = la fattura è buona, è la NOSTRA uscita a essere corta in
  quel momento: l'utente non vede niente, e se succede spesso è una
  domanda per la guardia della liquidità. «✅ … a pezzi da N, uscita M:
  ok» = la cifra intera non stava in un canale, a pezzi sì.
  I WALLET IL CUI INDIRIZZO NON PASSA (10 ott 2026, cantiere
  indirizzo-non-verificato): quando chi compra legge «Non sono riuscito
  a verificare questo indirizzo» e nel journal, lo stesso minuto, c'è
  «✅ Fattura P2P: … indirizzo …: ok», NON è un guasto nostro: il «no» è
  di mostrod, che l'indirizzo lo verifica per conto suo da dietro Tor.
  Si prova dal NODO (sola lettura, tre volte: le uscite cambiano), con
  l'indirizzo vero al posto di NOME e DOMINIO:
  `docker run --rm --pull never --network container:nodo-mostro-1 curlimages/curl -s -m 40 -A "mostro/0.19.0" -w '\nVIA TOR: http %{http_code}, tls %{time_appconnect}s, totale %{time_total}s\n' https://DOMINIO/.well-known/lnurlp/NOME`
  Passa = `http 200` con `"tag":"payRequest"`. Un 403, uno 000 o una
  pagina di sfida = quel servizio non parla con le uscite Tor: il
  dominio si AGGIUNGE alla leva nel config del VPS
  (`/srv/barattolo/config.py`, a mano; la riga SOSTITUISCE l'elenco del
  codice, quindi le voci si ripetono tutte):
  `P2P_INDIRIZZI_NON_PASSANO = {"walletofsatoshi.com": "Wallet of Satoshi", "DOMINIO": "Nome del wallet"}`
  poi `sudo systemctl restart barattolo`. Da lì — al primo caricamento
  della pagina, l'elenco viaggia con le leve del P2P — chi ha salvato
  un indirizzo di quel dominio non vede più la scorciatoia «⚡ Usa
  l'indirizzo dei tuoi incassi», e il foglio ferma PRIMA
  dell'invio («Gli indirizzi Nome del wallet qui non funzionano: incolla
  una fattura dal tuo wallet.») e nel journal resta
  `⛔ Fattura P2P: … indirizzo @DOMINIO: wallet_non_passa`. La prova in
  chiaro NON si fa dal nodo (mostrerebbe il suo IP a quel servizio): si
  fa dal PC o dal VPS.
  DOVE SI TROVANO I CANDIDATI: ogni riga «Fattura P2P» di un indirizzo
  porta il dominio accanto al tramite («indirizzo @DOMINIO», mai il
  nome prima della chiocciola), anche quando l'esito è «ok». Tutti i
  domini passati dal controllo, contati:
  `journalctl -u barattolo --since "7 days ago" | grep "Fattura P2P" | grep -o "indirizzo @[a-z0-9.-]*" | sort | uniq -c | sort -rn`
  Un dominio che torna più volte nello stesso minuto per lo stesso
  ordine, sempre «ok», è il segno di qualcuno che riprova perché il
  coordinatore gli dice di no: è il primo da provare dal nodo.
  IL CANARINO: un «LND non l'ha mai visto» si crede solo se, nello
  stesso giro, LND riconosce un hash che conosce di sicuro — uno per
  cui lui stesso ha gia' detto SUCCEEDED (timbro `lnd_canarino`, o gli
  ultimi payout usciti dal nodo). Senza canarino «assente» vale
  «muto», cioe' si aspetta. Non c'e' niente da seminare a mano: basta
  che nel database ci sia UN payout riuscito dalla cassaforte `nodo`.
  I CONTROLLI A MANO, tutti di sola lettura. Sul VPS, la coda:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT 'ordini',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM ordini WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'rimborsi',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM rimborsi_asta WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'sblocchi',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM pagamenti WHERE payout_stato NOT IN ('','uscito')\")]"`
  Tutti gli hash tentati per una riga (qui l'ordine 163):
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT hash,datetime(quando,'unixepoch'),esito FROM payout_tentati WHERE tabella='ordini' AND riga_id=163\")]"`
  La voce di LND per un hash, dal VPS attraverso il ponte (il
  macaroon sta in un file 600, NON sulla riga di comando):
  `H=<payment_hash>; B=$(python3 -c "import base64,sys;print(base64.urlsafe_b64encode(bytes.fromhex(sys.argv[1])).decode())" $H); curl -s --max-time 30 --cacert /opt/lnbits/data/tls.cert -H "Grpc-Metadata-macaroon: $(cat /root/lettura.macaroon.hex)" https://127.0.0.1:18080/v2/router/track/$B | head -c 600`
  — `"status":"SUCCEEDED"`, `"IN_FLIGHT"` o `"FAILED"`; un hash mai
  visto risponde `payment isn't initiated`. Sul nodo la stessa cosa e'
  `lncli trackpayment <payment_hash>`, e gli appesi di adesso sono
  `lncli listpayments --include_incomplete | grep -c IN_FLIGHT`. La
  voce di LNbits: il pannello (tunnel SSH sulla 5001), cercando l'hash.
  IL DRILL, a mercatino fermo e con un ordine di prova da pochi sats:
  1) riavviato il servizio, il journal dice «LND ACCESO»; 2) il `curl`
  qui sopra su un hash di un payout VECCHIO e riuscito risponde
  SUCCEEDED, e su un hash inventato (64 cifre esadecimali a caso)
  risponde `payment isn't initiated` — se risponde altro, la forma
  che il codice si aspetta e' sbagliata e va detto PRIMA di fidarsi;
  3) un ordine di prova pagato e confermato a ponte sano: si chiude
  come sempre, e nel journal NON compare nessuna riga 🔎 (una fattura
  fresca non fa il giro su tor: e' voluto); 4) un secondo ordine di
  prova — il venditore di prova deve avere un LIGHTNING ADDRESS: con
  una fattura incollata a mano, a tentativo fallito gliene si chiede
  una nuova e il giro non si chiude da solo — e
  `systemctl stop lnd-ponte` PRIMA della conferma: il payout
  non parte, il guardiano rimette su il ponte in ~3 minuti, e il
  pagamento si chiude DA SOLO — ma non subito: finche' non sono
  passati i 15 minuti un hash che LND non ha mai visto vale «in volo»,
  quindi ci vogliono due o tre battiti dell'orologio (20-30 minuti).
  Nel journal si leggono le righe 🔎 con `LND=assente` e poi la 🛬
  che ritenta; su LNbits, alla fine, UN solo pagamento riuscito e
  nessun 🧊. Quel che il drill non prova e' la hold
  invoice: si puo' fare con un wallet che le sa coniare, ed e' l'unico
  modo di vedere dal vivo il 409 «ANCORA IN VOLO».
  LE FATTURE SCADUTE (20 set 2026, ordine #152). Una fattura
  incollata ha una scadenza scritta dentro, e fra la spedizione e la
  conferma passano giorni. Prima di ogni payout il server la legge: se
  è scaduta (o le restano meno di 2 minuti) NON TENTA — su LNbits non
  nasce nessuna riga, non c'è niente da verificare — toglie la fattura
  morta, lascia l'ordine in `confirmed`, e dice al venditore «la
  fattura che avevi incollato è scaduta il …: incollane una nuova, o
  metti un Lightning address». Se il venditore un address ce l'ha, si
  paga da lì al giro dopo, da soli. Ai moderatori arriva «⌛ Pagamento
  in uscita NON TENTATO: fattura scaduta» — è un'informazione, non un
  allarme: non c'è NIENTE da fare. Alla porta: una fattura scaduta, o
  che muore entro 10 minuti, si rifiuta SUBITO e si dice perché.
  ⚠️ DAL 21 SET 2026 LA FATTURA SI INCOLLA SOLO ALL'INCASSO: prima
  della conferma la porta risponde «si incolla solo al momento
  dell'incasso… imposta il tuo Lightning address», e il foglio
  dell'ordine ha il solo campo dell'address (`FATTURA_ANTICIPATA_GIORNI`
  non esiste più). Le fatture già in colonna sugli ordini APERTI
  restano e si pagano come prima — o, se sono morte, non si tentano e
  se ne chiede una nuova: QUANTE sono lo dice il censimento qui sotto,
  e dopo questo deploy è un numero che può solo scendere.
  DOVE SI LEGGE: `journalctl -u barattolo | grep "⌛"`. Il motivo di
  ogni payout mancato sta nella riga dell'ordine:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,stato,payout_stato,payout_tentativi,payout_errore FROM ordini WHERE COALESCE(payout_errore,'')<>'' ORDER BY id DESC LIMIT 20\")]"`
  «Pagamento in uscita FALLITO» adesso dice il PERCHÉ in parole
  (fattura scaduta, nessuna strada, saldo NOSTRO insufficiente, ponte
  giù, tempo scaduto per strada, rifiutata da chi riceve, fattura già
  bruciata) col testo grezzo di LNbits accanto. «Saldo nostro» e
  «ponte giù» sono gli unici due che chiedono un gesto NOSTRO, subito.
  IL CENSIMENTO: `cd /srv/barattolo && python3 censimento_scadenze.py` —
  sola lettura, niente rete. Dice da dove veniva la fattura di ogni
  ordine pagato (incollata o Lightning address), con che margine è
  arrivata al payout, e — la parte che serve — quali ordini APERTI
  hanno in colonna una fattura già scaduta o che scade entro 7 giorni.
  ⚠️ «Verifica e riprova» (🧊) su una riga la cui fattura è scaduta NON
  ripaga: toglie il fermo, chiede la fattura nuova, e lo dice («⌛ …la
  fattura che avevamo è SCADUTA»). Un tentativo di POCHI MINUTI fa resta
  «in volo» comunque: i 15 minuti non li scavalca nessun calendario.
  LO STADIO «IN PAGAMENTO» (set 2026). Dalla conferma in poi l'ordine
  mostra «💸 In pagamento al venditore» a tutt'e due le parti, con lo
  stato vivo e la linea del tempo. COSA ASPETTARSI DA UN GUASTO NOSTRO
  (LNbits muta, ponte giù, nodo giù): a compratore e venditore NON
  arriva niente oltre ai due avvisi d'ingresso («ci pensa Barattolo»,
  «sono in arrivo»); nel journal una riga 🔁 a ogni ritentativo — a 1,
  6, 21, 51 minuti e poi ogni ora, senza tetto — e il payout che parte
  da solo quando il nodo torna. Il guardiano del ponte e l'avviso
  giornaliero «🔁 Pagamenti in uscita fermi» restano quelli di sempre;
  dopo 30 minuti IN VOLO parte il 🧊 di sempre, e in quell'istante le
  due parti leggono «ci stiamo lavorando noi».
  DOVE SI LEGGE. Gli ordini in pagamento adesso:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,stato,payout_stato,payout_verso,payout_tentativi,payout_errore FROM ordini WHERE stato='confirmed' OR (payout_verso='venditore' AND payout_stato IN ('in_volo','incerto','da_riprovare')) ORDER BY id DESC\")]"`
  La linea del tempo di UN ordine (sostituisci 152):
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT datetime(quando,'unixepoch','localtime'),passo,motivo,volte,datetime(ultimo,'unixepoch','localtime') FROM payout_passi WHERE tabella='ordini' AND riga_id=152 ORDER BY id\")]"`
  Nel journal: `journalctl -u barattolo | grep -E "🔁|🛬|🧊|⌛"`.
  IL DRILL (col venditore di prova, fattura INCOLLATA e lunga):
  `systemctl stop lnd-ponte`, si aspetta che il guardiano dica «giù»
  (la riga ⚠️ nel journal, un paio di minuti), poi il compratore
  conferma. Atteso: la pagina dice «riparte da solo», su LNbits NON
  nasce nessuna riga, la fattura resta in colonna; rimesso su il ponte,
  entro il giro dopo il payout parte da solo con la STESSA fattura e a
  chi vende arriva «Arrivati ✓». ⚠️ Se la conferma arriva PRIMA che il
  guardiano si accorga del guasto, LNbits tenta, segna `failed`, e
  quella fattura è bruciata: con un Lightning address si riparte da
  soli (dopo i 15 minuti dei pagamenti in volo), con una fattura
  incollata se ne chiede una nuova dicendo che la colpa è nostra. È la
  finestra dichiarata del cantiere.
  IL ROLLBACK è il commit precedente: la tabella `payout_passi` resta
  lì e non dà fastidio a nessuno (il codice di prima non la legge).
  PAGARE DA UN'ALTRA CASSAFORTE (21 set 2026, ordine #152). Il server
  paga sempre dalla cassaforte in cui i sats dell'ordine sono entrati.
  Quando quella cassaforte ha un pagamento APPESO che non si decide — il
  #152: 247.707 sats per Pedro, «pending» sul LNbits ospitato dal 20
  set, fattura scaduta la sera stessa — l'incasso resta 🧊 e nessuno
  può pagare chi vende dall'altra, che funziona. Pagare a mano da
  LNbits e scrivere l'hash nel database sono i gesti che l'audit ha
  vietato: la strada è il TERZO BOTTONE del pannello, «🔀 Paga da
  un'altra cassaforte» (Profilo → 🧊 Pagamenti da verificare), accanto
  a «Verifica e riprova» e «L'ho visto io: è uscito».
  COSA FA: non paga lui. Cambia DA DOVE si paga (`cassaforte_payout`
  sull'ordine; `cassaforte` NON si tocca: dice dove sono entrati i sats
  del compratore) e ripassa dalla strada d'uscita di sempre — importo,
  scadenza, verità su LNbits e LND, una sola mano, stadio, «Arrivati ✓».
  QUANDO SI PUÒ, le due guardie. 1) Il pagamento d'origine è PROVATO
  MORTO: dove c'è un LND nostro (cassaforte `nodo`) lo dice LND —
  FAILED, o `payment isn't initiated` a canarino vivo e dopo 15 minuti;
  lì il calendario non conta, e IN_FLIGHT rifiuta sempre. Dove LND non
  c'è (il SaaS): LNbits risponde, NON dice «success», e la fattura di
  quel tentativo è scaduta da almeno 60 MINUTI
  (`ALTRA_CASSAFORTE_DOPO_SCADENZA_S`). 2) Chi vende ci ha già dato un
  modo NUOVO: una fattura nuova e valida in colonna, o un Lightning
  address. Il bottone è ACCESO quando dal database il gesto ha senso;
  le guardie vere girano al tocco (chiede alle fonti) e di nuovo alla
  conferma. Rifiuti: 409 con la frase (in volo, uscito, presto, manca
  la fattura), 503 se una fonte tace. Doppio click o due moderatori:
  uno solo passa, l'altro legge «l'ha già deciso qualcun altro».
  ⚠️ IL RISCHIO CHE RESTA, e sta scritto anche nel foglio di conferma:
  una fattura scaduta NON prova che un HTLC già accettato da chi riceve
  (una hold invoice) non possa più saldarsi — può, fino al suo CLTV. Se
  succedesse, chi vende avrebbe ricevuto DUE volte. Per questo la regola
  del calendario non la usa nessun automatismo: la usa una persona, con
  le voci delle fonti davanti, e il pagamento d'origine resta
  SORVEGLIATO (sotto).
  ⚠️ I SATS ESCONO DAL SALDO DELL'ALTRA CASSAFORTE, dove ci sono i
  depositi di ALTRI ordini. Prima di premere: nella cassaforte di
  destinazione deve esserci capitale NOSTRO pari all'importo (più la
  riserva fee di LNbits, `max(1%, 10 sats)`), e sul nodo liquidità in
  USCITA sufficiente. Si guarda col polso 23 di
  `query_libro_mastro.sql` e con `python3 capitale_cassa.py`; se non
  basta si versa PRIMA capitale nostro in quel wallet, e lo si dichiara
  (`capitale_nodo_sats`). Dopo la deviazione il polso 23 mostrerà il
  SaaS «lungo» e il nodo «corto» della stessa cifra: è il credito.
  IL CREDITO DA RECUPERARE. Se alla decisione LNbits teneva ancora
  «pending» il pagamento d'origine, quei sats di là restano impegnati:
  nasce una riga in `crediti_cassaforte` (ordine, cassaforte, hash,
  sats, chi ha deciso, perché), visibile nel pannello («🔀 Crediti da
  recuperare») e gridata ogni giorno dal libro mastro («credito da
  recuperare su un'altra cassaforte») finché è aperta. Sull'ordine
  restano `cassaforte_payout`, l'hash nuovo in `payout_hash` e la frase
  in `payout_nota` («pagato dalla cassaforte X invece di Y, deciso da…
  il… motivo:…»). Un credito aperto sul SaaS è un DOVERE del SaaS:
  l'avviso «🏁 il SaaS non ha più doveri» non parte finché c'è.
  COME RECUPERARE IL CREDITO. La ronda `sorveglia_crediti` richiede
  quell'hash una volta all'ora. a) Il pagamento appeso FALLISCE (il
  supporto del SaaS lo sblocca, o l'HTLC scade da solo): i sats tornano
  nel saldo di quella cassaforte, la riga va `rientrato`, arriva «✅
  Credito rientrato» e non c'è altro da fare — quel saldo in più è
  capitale nostro rimasto di là, e rientra con lo sweep della fase 5 (o
  prima, con un prelievo a mano verso il wallet del nodo, dichiarando i
  due capitali). b) Il pagamento appeso SI SALDA: arriva «🚨 DOPPIO
  PAGAMENTO», la riga va `doppio`; i sats vanno chiesti indietro a chi
  vende da una persona, e quando sono tornati il credito si chiude dal
  pannello con una nota («✍️ Chiudi con questa nota», almeno dieci
  caratteri: chi, quando, come). c) Il SaaS rimborsa per altra via: si
  chiude a mano allo stesso modo.
  IL #152, PASSO PER PASSO (dopo il deploy; il VPS lo guarda Andrea).
  1) Lo stato di partenza, in sola lettura:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,stato,payout_stato,payout_verso,cassaforte,cassaforte_payout,payout_hash,length(invoice_venditore) FROM ordini WHERE id=152\")]"`
  — atteso `confirmed | incerto | venditore | saas | (vuoto) | <hash> |
  <lunghezza>`. Se `payout_stato` è `in_volo` si aspetta la ronda (30
  minuti dal tentativo). Gli hash tentati, con cassaforte e scadenza:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT hash,datetime(quando,'unixepoch'),esito,cassaforte,datetime(scade,'unixepoch') FROM payout_tentati WHERE tabella='ordini' AND riga_id=152\")]"`
  (`scade` a 1970 = ancora ignota: la trascrive il primo tocco del
  bottone, dalla fattura in colonna o chiedendola a LNbits).
  2) Il capitale sul nodo: vedi l'avviso qui sopra. 247.707 + ~2.500.
  3) Pannello → 🧊 → ordine #152 → «🔀 Paga da un'altra cassaforte». Se
  Pedro non ha un address e non ha ancora incollato niente, il foglio
  dice «Manca la fattura nuova» → «📨 Chiedi la fattura a chi vende»: a
  lui arriva il messaggio e nell'ordine gli si apre il campo. 4) Quando
  la incolla arriva «📥 …ha incollato la fattura nuova» — una fattura
  scade, non si aspetta. 5) Di nuovo il bottone: il foglio mostra le
  voci delle fonti, «da «saas» a [nodo]», la cifra e il rischio →
  «🔀 Sì, paga da lì». 6) Atteso: toast «✅ Pagato da «nodo»», a Pedro
  «Arrivati ✓», ai moderatori «🔀 …pagato da un'altra cassaforte», e in
  «🔀 Crediti da recuperare» la riga del #152 sul SaaS.
  DOVE SI LEGGE: `journalctl -u barattolo | grep -E "⚖️ Altra cassaforte|🔎"`.
  I crediti: `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,riga_id,cassaforte,pagato_da,sats,stato,datetime(deciso_il,'unixepoch','localtime'),motivo,nota FROM crediti_cassaforte\")]"`
  SE VA STORTO. Il pagamento dal nodo fallisce (nessuna strada, saldo):
  l'ordine torna a «serve una fattura nuova», la cassaforte d'uscita
  RESTA il nodo, e la prossima fattura che Pedro incolla si paga da lì
  da sola. Per tornare a pagare dalla cassaforte d'origine NON c'è un
  bottone (non è mai servito): si rifà il giro al contrario solo se
  quel pagamento finisce 🧊. IL ROLLBACK è il commit precedente: le
  colonne e la tabella nuove restano e non danno fastidio, ma un ordine
  GIÀ deviato e non ancora pagato tornerebbe a pagare dalla cassaforte
  d'origine — si guarda prima che non ce ne siano:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,stato,payout_stato FROM ordini WHERE COALESCE(cassaforte_payout,'')<>'' AND stato NOT IN ('released','refunded')\")]"`
  NON PROVATO DAL VIVO: LNbits vero sulle due cassaforti, la forma di
  `details.bolt11` (è un ripiego, e si crede solo se l'hash combacia),
  il bottone sul telefono. Provato: tutto il resto, su cartone.
  CHIUDERE LA CASSAFORTE SAAS (24 set 2026): i passi sul pannello, ordine
  per ordine. Il gesto e' sempre lo stesso: bottone → foglio col MOTIVO
  (almeno dieci caratteri, resta nel registro) → «Avanti» → foglio che
  rilegge ordine, cifra e motivo → conferma. Ogni gesto lascia una riga
  in `gesti_cassaforte`, una nel journal («⚖️ Cassaforte SaaS») e un
  avviso ai moderatori. NESSUN GESTO MUOVE SATS FRA LE DUE CASSAFORTI:
  quelli li sposti tu, a mano, dal SaaS al nodo, PRIMA che un ordine si
  chiuda — la vista dice quanti.
  0) Dopo il deploy: Profilo → 👑 → cassetto «🏦 Cassaforte SaaS». Leggi
  «Escono ancora dal SaaS» (dovrebbero essere 6 ordini) e «Spostati sul
  nodo» (0). Sola lettura sul VPS, per confronto:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id,stato,payout_stato,payout_verso,cassaforte,cassaforte_payout,prezzo_sats FROM ordini WHERE cassaforte='saas' AND stato NOT IN ('creato','annullato','released','refunded')\")]"`
  1) IL #152 (P3dr0, 247.707 sats, «pending» dal 20 set). Prima: sul
  nodo devono esserci 247.707 sats nostri piu' la riserva fee di LNbits
  (max(1%, 10 sats) = 2.477): spostali a mano. Poi 🧊 Pagamenti da
  verificare → ordine #152 → «💀 Dichiara morto il pagamento appeso» (e'
  acceso: la fattura e' scaduta da giorni). Motivo suggerito: «pending
  dal 20 set, nessuna preimage, saldo Spark riallineato: il SaaS
  chiude». Conferma. ATTESO: toast «💀 Pagamento appeso chiuso. A chi
  deve ricevere e' stato chiesto un modo nuovo…»; a P3dr0 il solito
  «Tocca a te: incolla una fattura di 247.707 sats, fatta adesso»; ai
  moderatori «💀 Ordine #152: pagamento appeso sul SaaS dichiarato
  morto» col promemoria del Debit; nel cassetto il #152 passa a
  «spostati sul nodo» e in «🔀 Crediti da recuperare» compare la riga
  del #152 sul SaaS, aperta. Quando P3dr0 incolla la fattura, il
  pagamento parte DA SOLO dal nodo (se ha messo un Lightning address,
  parte al gesto stesso). Se dice NO («Non si puo' dichiarare morto»):
  legge il perche' — «presto» non capita qui, «uscita» vuol dire che
  LNbits lo dice pagato (usa «Verifica e riprova»), «non_pending» che
  LNbits lo ha gia' marcato failed (lo chiude «Verifica e riprova»),
  «ignota» che LNbits non risponde (riprova fra poco).
  2) #129, #131, #134, #138 (locked, To The Mooon) e #153 (shipped,
  Steu): nel cassetto «🏦 Cassaforte SaaS», per ognuno «➡️ Sposta sulla
  cassaforte nodo», motivo («il SaaS chiude: paga dal nodo»), conferma.
  ATTESO: toast «➡️ Da adesso l'ordine #N paga (o rimborsa) dal nodo.
  Nessun sat si e' mosso…», l'ordine passa fra gli «spostati», e il
  totale «al massimo N sats da avere sul nodo» cresce del prezzo pieno:
  quella e' la cifra da spostare a mano sul nodo prima che si chiudano
  (copre anche un rimborso; l'incasso di chi vende e' scritto accanto).
  Se dice «in_corso» c'e' un pagamento appeso: prima si decide quello.
  3) Poi si aspetta che gli affari si chiudano: incasso o rimborso
  escono dal nodo, la vista scende, e quando «Escono ancora dal SaaS» e'
  a zero E i crediti sono a zero E gli altri doveri sono a zero suona il
  «🏁 il SaaS non ha piu' doveri». IL CREDITO DEL #152 resta aperto
  finche' LNbits lo tiene «pending»: a) se il SaaS lo marca `failed`
  arriva «✅ Credito rientrato … fai un Debit della stessa cifra» — fallo
  (il saldo era gia' stato riallineato col Credit); b) se mai si
  saldasse arriva «🚨 DOPPIO PAGAMENTO»: i 247.707 vanno chiesti a
  P3dr0; c) se vuoi spegnere il SaaS col credito ancora appeso, chiudilo
  a mano da «🔀 Crediti da recuperare» con una nota («SaaS disdetto il …,
  hash mai saldato»): cosi' il 🏁 puo' suonare. Poi sweep del saldo e
  disdetta, come dice «Il doppio wallet» in CANTIERI.
  DOVE SI LEGGE: `journalctl -u barattolo | grep "⚖️ Cassaforte SaaS"`;
  il registro: `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT riga_id,gesto,da,a,sats,deciso_da,datetime(deciso_il,'unixepoch','localtime'),motivo FROM gesti_cassaforte\")]"`
  IL ROLLBACK e' il commit precedente: la tabella resta e non da'
  fastidio; un ordine SPOSTATO e non ancora chiuso paga ancora dal nodo
  (il codice del 21 set legge `cassaforte_payout` per l'incasso) ma un
  suo RIMBORSO tornerebbe a uscire dal SaaS — si guarda prima che non
  ce ne siano in disputa. NON PROVATO DAL VIVO: LNbits vero sulle due
  cassaforti e il pannello sul telefono; provato tutto il resto col
  server vero, su cartone.
  IL CONTROLLO DEGLI ORFANI, sulle due casseforti (set 2026):
  `cd /srv/barattolo && python3 orfani.py` — sola lettura, legge il
  registro di ogni cassaforte configurata con la sua invoice key e
  lo incrocia coi `payment_hash` di ordini, rilanci e pagamenti.
  Tre elenchi: ORFANI (nostro memo, nessuna riga: devono essere
  zero), FUORI POSTO (la riga dice un'altra cassaforte: zero anche
  loro) e NON NOSTRI (capitale o altro: li guarda una persona).
  Esce con 1 se c'e' da guardare, quindi puo' stare in un cron che
  tace. Ha sostituito l'`orfani.py` non tracciato del 10 ago 2026,
  che leggeva una cassaforte sola e non conosceva `pagamenti`:
  quello si cancella.
  IL CAPITALE, per dichiararlo al polso 23: `cd /srv/barattolo && python3
  capitale_cassa.py` — legge i due registri e stampa un totale per
  cassaforte, il complessivo e le due righe `INSERT OR REPLACE` con le
  chiavi `capitale_saas_sats` e `capitale_nodo_sats`. Dal set 2026 il
  polso 23 e' per cassaforte e legge quelle due (la vecchia
  `capitale_nostro_sats` vale da ripiego per il solo SaaS).
  BACKUP: `/opt/lnbits` (db con backup atomico, `.env`, compose, cert,
  superuser, unit del ponte) e `onion_auth` viaggiano nell'archivio
  age; la riserva fee di LNbits e' `max(1%, 10 sats)` per payout, ed
  e' anche il `fee_limit` che LNbits passa a LND: il TETTO delle
  commissioni di instradamento dei payout del mercatino (Barattolo
  non ne passa uno suo). Il pavimento e' 10.000 msat dal 5 ott 2026;
  prima era il default di LNbits, 2.000 msat — 2 sats, non 2000:
  troppo pochi per due salti su un payout piccolo, e LND a tetto
  stretto risponde NO_ROUTE (la trappola del payout verso WoS).
  ⚠️ IL VALORE VIVE NEL PANNELLO ADMIN DI LNbits, non nel `.env`:
  con `LNBITS_ADMIN_UI=true` le impostazioni del server stanno nel
  database di LNbits e vincono sul file, quindi un
  `LNBITS_RESERVE_FEE_MIN` letto nel `.env` non e' il valore vero.
  Si legge e si cambia dal pannello (superuser), nelle impostazioni
  del server.
- IL FIREWALL (`ufw`, acceso il 16 set 2026): `deny incoming`, `allow
  outgoing`, e in entrata SOLO la porta SSH (letta dal sistema con
  `ss -tlnp | grep sshd`, non ricordata), 80/tcp, 443/tcp e 443/udp
  (HTTP/3 di Caddy). Tor, i backup, il pull del deploy e il ponte verso
  il nodo sono uscite e non lo vedono. Per una porta nuova: `ufw allow
  N/tcp` PRIMA di metterci qualcosa in ascolto, e comunque un servizio
  nuovo ascolta su 127.0.0.1 salvo motivo scritto. Se un giorno SSH
  non entra piu': dalla console Hetzner, `ufw disable` e si riguarda.
  Prima di ogni `ufw enable` futuro: la porta SSH ammessa per prima e
  una seconda sessione gia' aperta, che le connessioni vive non
  vengono tagliate.
- IL PONTE VIA WIREGUARD (21 set 2026): la strada di LNbits e del
  server verso la REST di LND non passa più da tor. Il perché — tre
  cadute in 24 ore, un singhiozzo di 40 secondi ogni ora, il tor del
  nodo che serve LND, mostro e il ponte insieme — sta in CANTIERI, «Il
  ponte via WireGuard». Tor resta per TUTTO il resto: LND verso la rete
  Lightning, mostro verso i relay e verso il VPS.
  IL DISEGNO. Il NODO ascolta (`185.18.221.96`, `51820/udp`), il VPS
  chiama: in `ufw` sul VPS non si apre niente. Rete del tunnel: nodo
  `10.77.0.1`, VPS `10.77.0.2`, una peer sola per capo e `AllowedIPs`
  di UN indirizzo. `PersistentKeepalive = 25` sul VPS. Sul VPS
  `lnd-ponte.service` resta un socat su `127.0.0.1:18080` — LNbits, la
  verità dei pagamenti e il guardiano non cambiano una riga — ma bussa
  a `10.77.0.1:18080`, dove sul nodo un socat gemello
  (`lnd-rest-wg.service`, sull'HOST) porta alla REST di LND nel suo
  container. I quattro file stanno in `deploy/ponte/`.
  LE CHIAVI nascono su ciascuna macchina (`wg genkey`) in
  `/etc/wireguard/privata.key` e NON ESCONO MAI: non stanno nemmeno in
  `wg0.conf` (le carica un `PostUp`), quindi `wg0.conf` si può copiare,
  confrontare e mettere nel backup. Si scambiano solo le PUBBLICHE, che
  possono passare anche da una chat. Il backup del VPS porta `wg0.conf`
  e il piano B, NON la chiave: a macchina rifatta si rigenera (passi 2,
  4 e 5) e nell'archivio c'è un segreto in meno.
  IL CERTIFICATO DI LND NON SI RIGENERA, ed era il passo che non si
  disfa in due comandi: i due socat spostano byte e non aprono niente,
  il TLS resta END-TO-END fra chi chiama e LND, e chi chiama bussa
  ancora a `127.0.0.1` — il nome che il `tls.cert` porta già. Niente
  `tlsextraip`, niente da ricopiare su VPS né su mostro. La scadenza
  resta il 22 OTT 2027, con la procedura di sempre (voce «IL PONTE
  VERSO LND», qui sopra). La prova è il secondo `curl` del passo 6.
  IL FIREWALL DEL NODO VIVE IN `wg0.conf`, nei `PostUp`: nasce col
  tunnel e muore con lui, nello stesso gesto (la lezione del namespace
  prestato), e se una regola non entra `wg-quick` smonta l'interfaccia
  — il tunnel senza firewall non esiste. La chiave si carica PER
  ULTIMA, quindi non c'è un istante col tunnel vivo e le regole non
  ancora montate. Catena `WG-PONTE` in cima a INPUT: dal tunnel passa
  SOLO `10.77.0.2` verso la sola `18080/tcp`; il resto del tunnel si
  butta; chi cerca `10.77.0.1` da un'ALTRA interfaccia si butta (Linux
  risponde per ogni suo indirizzo su ogni interfaccia); la `51820/udp`
  risponde al solo IP del VPS. E il FORWARD da e verso il tunnel è
  DROP, anche in `DOCKER-USER`: l'host del nodo ha `ip_forward=1` (lo
  vuole Docker), e senza quella riga chi prendesse il VPS potrebbe
  farsi inoltrare verso i container. Con lei arriva alla sola REST, coi
  due macaroon che aveva già: né più né meno di prima.
  ⚠️ LA SEQUENZA, UN COMANDO ALLA VOLTA. A mercatino quieto; fino al
  passo 6 il ponte via tor continua a lavorare e non si rompe niente.
  Le PUBBLICHE si annotano: servono all'altra macchina.
  PASSO 0 — SUL NODO, si guarda e basta (dalla cartella `~/nodo`):
  `docker compose ps --format '{{.Service}} {{.Name}}'`
  — il container di LND (atteso `nodo-lnd-1`; se ha un altro nome, quel
  nome va al posto suo qui sotto).
  `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' nodo-lnd-1`
  — l'IP di LND nella rete del compose (un `172.28.1.N`). Se esce
  VUOTO, LND vive nel namespace di un altro: FERMATI e riferisci.
  `grep -n "ipv4_address" ~/nodo/docker-compose.yml`
  — quell'IP deve comparire fra gli indirizzi FISSI. Se non c'è, al
  prossimo `up` potrebbe cambiare: FERMATI e riferisci.
  `curl -sk --max-time 10 https://172.28.1.N:8080/v1/state`
  — deve rispondere `{"state":"SERVER_ACTIVE"}`: dall'host a LND la
  strada c'è. Se la porta della REST non è 8080 lo dice
  `sudo grep -rIn "HiddenServicePort" ~/nodo/tor/ | grep -v /data/`,
  che è l'indirizzo con cui la trova tor.
  `sudo ss -lntu | grep -E ':(51820|18080) '`
  — non deve stampare NIENTE: le due porte sono libere.
  PASSO 1 — SUL NODO, il programma e la chiave:
  `sudo apt-get update && sudo apt-get install -y wireguard-tools socat`
  `sudo sh -c 'umask 077; set -C; wg genkey > /etc/wireguard/privata.key'`
  — `set -C` rifiuta di riscrivere una chiave che c'è già. Non stampa
  niente, ed è giusto: la privata non si guarda mai.
  `sudo sh -c 'wg pubkey < /etc/wireguard/privata.key'`
  — 44 caratteri che finiscono con `=`: è la PUBBLICA DEL NODO.
  PASSO 2 — SUL VPS, lo stesso:
  `apt-get update && apt-get install -y wireguard-tools socat`
  `sh -c 'umask 077; set -C; wg genkey > /etc/wireguard/privata.key'`
  `wg pubkey < /etc/wireguard/privata.key`
  — la PUBBLICA DEL VPS.
  PASSO 3 — DAL PC (PowerShell), i file verso il nodo, che la repo non
  ce l'ha. `-c core.autocrlf=false` conta: senza, su Windows l'archivio
  esce coi fine-riga di Windows e `wg-quick` non lo legge.
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket fetch origin`
  `git -c core.autocrlf=false -C C:\Users\Andrea\Documents\GitHub\satmarket archive --format=tar -o "$env:TEMP\ponte.tar" origin/main deploy/ponte`
  `scp -i $env:USERPROFILE\.ssh\lnvps "$env:TEMP\ponte.tar" debian@vm-1937.lnvps.cloud:/tmp/`
  Poi SUL NODO: `tar -xf /tmp/ponte.tar -C /tmp && sha256sum /tmp/deploy/ponte/*`
  e SUL VPS: `sha256sum /srv/barattolo/deploy/ponte/*`
  — le cinque impronte devono essere IDENTICHE sulle due macchine. Se
  una differisce, il file è arrivato storto: non si va avanti.
  PASSO 4 — SUL NODO, il tunnel e il socat:
  `sudo install -m 600 /tmp/deploy/ponte/wg0-nodo.conf /etc/wireguard/wg0.conf`
  `sudo sed -i 's|INCOLLA_QUI_LA_PUBBLICA_DEL_VPS|LA_PUBBLICA_DEL_VPS|' /etc/wireguard/wg0.conf`
  — al posto di `LA_PUBBLICA_DEL_VPS` i 44 caratteri del passo 2.
  `sudo grep -c INCOLLA_QUI /etc/wireguard/wg0.conf`
  — deve dire `0`.
  `sudo install -D -m 644 /tmp/deploy/ponte/wg-quick-dopo-docker.conf /etc/systemd/system/wg-quick@wg0.service.d/dopo-docker.conf`
  `sudo systemctl daemon-reload`
  `systemctl show -p After wg-quick@wg0 | grep -o docker.service`
  — deve stampare `docker.service`: il tunnel parte SEMPRE dopo Docker,
  sennò al riavvio la riga in DOCKER-USER non entra in silenzio, e la
  ronda lo vede solo al giro lungo del giorno dopo (successo il 1 nov
  2026: Cantieri, «Il tunnel del ponte parte dopo Docker»).
  `sudo systemctl enable --now wg-quick@wg0`
  `sudo iptables -S WG-PONTE`
  — sei righe: la catena, un ACCEPT per `10.77.0.2` sulla 18080, due
  DROP, l'ACCEPT della 51820 per `46.62.162.103`, il suo DROP.
  `sudo iptables -S INPUT | head -2` — la prima regola è `-j WG-PONTE`.
  `sudo iptables -S FORWARD | head -3` — in cima i due DROP di `wg0`.
  `sudo iptables -S DOCKER-USER` — c'è `-A DOCKER-USER -i wg0 -j DROP`.
  `echo 'LND_REST=172.28.1.N:8080' | sudo tee /etc/default/lnd-rest-wg`
  — con l'IP vero del passo 0.
  `sudo install -m 644 /tmp/deploy/ponte/lnd-rest-wg.service /etc/systemd/system/`
  `sudo systemctl daemon-reload && sudo systemctl enable --now lnd-rest-wg`
  `sudo ss -lntp | grep 18080`
  — UNA riga, e l'indirizzo è `10.77.0.1:18080`. Se dice `0.0.0.0` o
  `*`: `sudo systemctl stop lnd-rest-wg` e riferisci.
  PASSO 5 — SUL VPS, il tunnel, e la prova PRIMA di toccare il ponte:
  `install -m 600 /srv/barattolo/deploy/ponte/wg0-vps.conf /etc/wireguard/wg0.conf`
  `sed -i 's|INCOLLA_QUI_LA_PUBBLICA_DEL_NODO|LA_PUBBLICA_DEL_NODO|' /etc/wireguard/wg0.conf`
  `grep -c INCOLLA_QUI /etc/wireguard/wg0.conf` — `0`.
  `systemctl enable --now wg-quick@wg0`
  `wg show wg0`
  — entro mezzo minuto compare `latest handshake: N seconds ago`. Se
  non compare: l'UDP non passa (un firewall del provider) o una
  pubblica è sbagliata. Ci si FERMA qui: il ponte via tor non è stato
  toccato.
  `curl -sk --max-time 10 https://10.77.0.1:18080/v1/state`
  — `{"state":"SERVER_ACTIVE"}`: LND risponde dal tunnel. (`-k` perché
  qui il nome è `10.77.0.1`, che il cert non porta: è atteso, e i
  client non bussano mai a questo indirizzo.)
  PASSO 6 — SUL VPS, LO SCAMBIO (un secondo di buco):
  `cp -a /etc/systemd/system/lnd-ponte.service /etc/systemd/system/lnd-ponte-tor.service`
  — il ponte di prima, salvato col nome del piano B. Non si abilita.
  `install -m 644 /srv/barattolo/deploy/ponte/lnd-ponte.service /etc/systemd/system/lnd-ponte.service`
  `systemctl daemon-reload`
  `systemctl restart lnd-ponte`
  `systemctl status lnd-ponte --no-pager | head -12`
  — `active (running)`, e nella riga di socat c'è `10.77.0.1:18080`.
  Se dice `unknown option` o `failed`: il ROLLBACK qui sotto, subito.
  `curl -sk --max-time 10 https://127.0.0.1:18080/v1/state`
  — il ponte arriva.
  `curl -s --max-time 10 --cacert /opt/lnbits/data/tls.cert https://127.0.0.1:18080/v1/state`
  — la stessa risposta SENZA `-k`: il cert combacia, non c'era niente
  da rigenerare. La terza domanda (il macaroon) è quella di sempre.
  `docker logs --since 3m lnbits-lnbits-1 2>&1 | tail -5`
  — LNbits si riaggancia da solo, come dopo ogni cura del guardiano; se
  dopo un paio di minuti parla ancora di «Funding source»:
  `cd /opt/lnbits && docker compose restart`.
  PASSO 7 — LA CONTROPROVA DA FUORI, dal PC:
  `Test-NetConnection 185.18.221.96 -Port 18080`
  — `TcpTestSucceeded : False`. E SUL NODO `sudo iptables -L WG-PONTE -v -n`
  mostra i contatori: l'ACCEPT cresce con l'uso, i DROP dicono cosa è
  stato respinto.
  PASSO 8 — SUL NODO, la ronda settimanale alzerà la SUPERFICIE: tre
  righe nuove (`51820/udp` due volte, v4 e v6, e `10.77.0.1:18080`).
  È atteso: si guarda che siano SOLO quelle, e poi `--impara`, col
  comando che la ronda stessa scrive in fondo al messaggio.
  I CONTROLLI FINALI. `curl -s https://barattolo.store/api/salute` →
  `{"ok":true,"ponte":"ok"}`. Un acquisto di prova da pochi sats: la
  fattura nasce e il «pagato» arriva. La strada che vede il guardiano
  si legge al prossimo riavvio del servizio (ogni deploy lo fa):
  `journalctl -u barattolo | grep "La strada del ponte"` deve dire «il
  tunnel WireGuard e lnd-ponte».
  IL DRILL NUOVO, a mercatino fermo, SUL VPS:
  `systemctl stop wg-quick@wg0`
  — al terzo controllo (2-3 minuti) arriva «🌉⚠️ Ponte verso LND giù…
  Riavvio il tunnel WireGuard e lnd-ponte», e 90 secondi dopo «🌉✅
  tornato». `wg show wg0` ha di nuovo la stretta di mano. Il drill di
  prima (`systemctl stop lnd-ponte`) vale ancora, e prova l'altra metà
  della cura.
  IL ROLLBACK, DUE COMANDI SUL VPS (il nodo non si tocca: il suo hidden
  service con client-auth è rimasto dov'era):
  `systemctl disable --now lnd-ponte.service`
  `systemctl enable --now lnd-ponte-tor.service`
  Il guardiano se ne accorge da solo — a ogni cura chiede a systemd se
  il piano B è acceso, e allora riavvia tor e `lnd-ponte-tor`. Di
  corsa ne basta UNO, `systemctl start lnd-ponte-tor.service`
  (`Conflicts=` spegne l'altro), ma dura fino al prossimo riavvio
  della macchina. Per tornare sul tunnel: gli stessi due comandi coi
  nomi scambiati. Il tunnel può restare su: spento il ponte, non porta
  niente.
  FRA UNA SETTIMANA (dal giorno del passo 6), e NON prima: si decide se
  togliere il piano B — l'hidden service della REST e la sua
  client-auth sul nodo, `lnd-ponte-tor.service` e `onion_auth` sul VPS.
  Finché restano, sono una seconda porta verso LND, chiusa a chiave.
- LO SCONTO FEDELTÀ DEL P2P, la messa in servizio (patch 0005 del
  fork; il perché sta in CANTIERI, «Le commissioni per persona»).
  ✅ FATTA il 18 set 2026 — immagine `-bar3`, con la 0006 nello stesso
  giro: il verbale è in CANTIERI, «Il passo 3 delle commissioni per
  persona». La sequenza resta qui perché è la stessa di ogni patch
  futura al fork, corretta nei due punti dove il campo l'ha smentita
  (i test e il format-patch). Si fa
  a SCAMBI FERMI e in quest'ordine, che non è estetica: finché la leva
  del VPS è a 0 la porta risponde 404, quindi il nodo può salire per
  primo e fa prezzo pieno a tutti — client e coordinatore dicono la
  stessa cifra in ogni momento del giro.
  1) IL SEGRETO, generato sul PC: `python -c "import secrets;
  print(secrets.token_urlsafe(32))"`. Va in DUE posti e in nessun
  altro: la riga `P2P_SCONTO_SEGRETO` nel `config.py` del VPS, e
  `BARATTOLO_SCONTO_SEGRETO` nel compose del nodo. Mai nel canale
  Telegram del nodo — E MAI IN UNA CHAT CON CLAUDE: il 18 set 2026 il
  primo è finito incollato lì, ed è stato RUOTATO prima ancora di
  installarlo (regola 1). Nei comandi che Claude scrive c'è un
  segnaposto: lui non ha bisogno di vederlo.
  2) SUL NODO, il fork: `cd ~/nodo/mostro-src`, branch
  `barattolo/v0.18.7`; con `patch-0005-fee-per-parte.py` e
  `barattolo_fee.rs` nella stessa cartella — una cartella FUORI da
  `mostro-src` (`~/nodo/patch-bar3`), o il `git add -A` di dopo si
  porta i patcher nel commit del fork: `python3 .../patch-0005-fee-per-parte.py --secco`,
  poi senza `--secco`. I test PRIMA della build vera:
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar3 .`
  e `docker run --rm mostro-test:bar3 cargo test --release -- barattolo_fee app::take_buy app::take_sell flow app::add_invoice`
  — i cinque filtri in UN COLPO SOLO, tutti dopo `--`. La forma di
  prima (`sh -c "cargo test … && cargo test …"`) ha le virgolette
  annidate, e dal PC va lanciata dentro `ssh "…"`: PowerShell non le
  fa passare. Il 18 set 2026: 144 verdi, zero falliti.
  Verdi: UN COMMIT PER PATCH (`git add -A && git commit` dopo la 0005,
  e di nuovo dopo la 0006), poi `git format-patch -2 --start-number 5`
  — `-2` perché i commit sono due, `--start-number 5` perché senza i
  file nascerebbero `0001-` e `0002-` e nel repo pesterebbero le prime
  due patch. La copia torna nel repo con `scp`. E
  `docker build -f docker/Dockerfile -t mostro:v0.18.7-bar3 .`
  — un tag nuovo, mai sovrascritto.
  3) SUL NODO, il compose (copia prima: `cp docker-compose.yml
  docker-compose.yml.prima-bar3`): l'immagine a `mostro:v0.18.7-bar3`,
  e sotto `environment:` del servizio `mostro` le tre righe
  `BARATTOLO_SCONTO_FEE=0.005`, `BARATTOLO_SCONTO_URL=https://barattolo.store/api/p2p/sconto`,
  `BARATTOLO_SCONTO_SEGRETO=...`. In `~/nodo/mostro/settings.toml`
  (copia prima), `[mostro]`: `fee = 0.03` — col punto, è un f64.
  4) `docker compose up -d mostro` (`up -d`, NON `restart`: cambia
  l'immagine e cambia l'ambiente). Si guarda:
  `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` dice
  `-bar3`; nei log «Settings correctly loaded» e la riga
  `barattolo_fee: per-party discount 0.005 verified against https://...`
  (se dice `not configured` manca una delle tre variabili); e dal
  38385 `fee` 0.03, letto dallo specchio.
  5) SUL VPS, nel `config.py`: `P2P_SCONTO_SEGRETO`, poi
  `P2P_SCONTO_FEDELTA_PERCENTO = 0.5` e `P2P_COMMISSIONE_PERCENTO = 4`;
  `sudo systemctl restart barattolo`. Il pannello «Stato delle leve»
  deve dire accese le due righe dello sconto. La porta si prova dal
  VPS stesso: `curl -s -X POST http://127.0.0.1:8080/api/p2p/sconto -H
  "Authorization: Bearer IL_SEGRETO" -H "Content-Type: application/json"
  -d '{"pubkeys":["<64 esadecimali qualunque>"]}'` → `{"ok":true,
  "sconti":{"...":false}}`; senza l'header → 403.
  6) I DUE SCAMBI DI PROVA, piccoli: uno con UNO solo dei due scontato
  — hold e payout al satoshi contro `lncli`, e sul nodo
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT * FROM barattolo_fees ORDER BY created_at DESC LIMIT 1\")]"`;
  e uno col VPS irraggiungibile APPOSTA (`sudo systemctl
  stop barattolo` per il minuto della presa): fee piena per tutt'e due
  e nel log del nodo `discount NOT verified`.
  ⚠️ DEI DUE, IL 18 SET 2026 NON SE N'È FATTO NESSUNO NELLA FORMA
  SCRITTA QUI: lo scambio di prova (`4ed69365`) era fra DUE pionieri,
  cioè con TUTT'E DUE scontati — conto al satoshi, ma a fee uguali la
  riga di `barattolo_fees` e la colonna `order.fee` non si
  distinguono. Quello con UNO solo scontato e quello col VPS spento
  RESTANO DA FARE, e il primo è quello che prova la tabella a lato.
  IL ROLLBACK ha due gradini: togliere le tre variabili dal compose e
  `up -d` (la patch diventa inerte, upstream byte per byte), oppure
  l'immagine a `-bar2`. La `fee` e il listino si rimettono a mano.
- GLI AVVISI P2P DAL COORDINATORE, la messa in servizio (patch 0007 del
  fork; il perché sta in CANTIERI, «Mostro è l'unica fonte degli avvisi
  P2P»). ✅ IN SERVIZIO dal 19 set 2026: immagine `mostro:v0.18.7-bar4`,
  commit `9387493` sul nodo, collaudata a due telefoni lo stesso giorno;
  il `.patch` sta in `deploy/mostro/` dal 22 set (README, «RICOSTRUIRE
  IL FORK DA ZERO»). Quel che segue è la liturgia com'era al 18 set,
  buona per la prossima patch. Al 18 set il codice del server era su
  main e in servizio, la patch sul nodo NO — e finché non c'è valgono i soli
  avvisi del libro (presa, concluso, annullato, scaduto, tornato), che a
  porta chiusa partono SUBITO com'era. **Garanzia chiesta e bloccata,
  fattura data, euro inviati, disputa e pagamento fallito in quella
  finestra NON avvisano nessuno**: il campanello generico che li copriva
  non c'è più. A pagina aperta l'app segue da sola; a pagina chiusa no.
  Per questo il nodo si fa PRESTO, e a scambi fermi.
  LA SEQUENZA, la stessa liturgia della 0005 (un comando alla volta):
  1) IL SEGRETO, generato sul PC: `python -c "import secrets;
  print(secrets.token_urlsafe(32))"`. UNO NUOVO, non quello dello
  sconto: quello fa una domanda, questo fa partire avvisi a persone
  vere — due porte, due chiavi, si ruotano una alla volta. Va in DUE
  posti: `P2P_EVENTI_SEGRETO` nel `config.py` del VPS e
  `BARATTOLO_EVENTI_SEGRETO` nel compose del nodo. Mai nel canale
  Telegram del nodo, MAI in una chat con Claude (è già successo il 18
  set: nei comandi c'è un segnaposto). Se `BARATTOLO_EVENTI_SEGRETO`
  manca, mostrod usa `BARATTOLO_SCONTO_SEGRETO`: è un ripiego, non la
  forma consigliata.
  2) SUL PC, i due file al nodo (dalla cartella della repo):
  `scp deploy/mostro/patch-0007-eventi-al-server.py deploy/mostro/barattolo_eventi.rs UTENTE@NODO:nodo/patch-bar3/`
  (utente e indirizzo sono quelli con cui si entra di solito sul nodo)
  — la cartella dei patcher sta FUORI da `mostro-src`, o il `git add -A`
  di dopo se li porta nel commit del fork. Poi, sul nodo,
  `sha256sum ~/nodo/patch-bar3/barattolo_eventi.rs` contro
  `sha256sum deploy/mostro/barattolo_eventi.rs` sul PC.
  3) SUL NODO: `cd ~/nodo/mostro-src`, e `git status` deve dire branch
  `barattolo/v0.18.7` e albero pulito. A secco:
  `python3 ~/nodo/patch-bar3/patch-0007-eventi-al-server.py --secco`
  deve dire «A SECCO: 24 agganci in 13 file, tutte le ancore uniche, 13
  azioni note». Poi senza `--secco`: «FATTO: 24 agganci in 13 file».
  4) I TEST PRIMA DELLA BUILD VERA:
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar4 .`
  e poi, in UN comando solo e senza virgolette annidate (da PowerShell
  dentro `ssh "…"` non passano):
  `docker run --rm mostro-test:bar4 cargo test --release -- barattolo_eventi barattolo_fee app::take_buy app::take_sell flow app::add_invoice app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle`
  ⚠️ IL RUST DELLA 0007 NON È MAI STATO COMPILATO (sul PC non c'è
  cargo): se la build o i test si fermano, l'errore si incolla a Claude
  e si corregge NEL REPO (`barattolo_eventi.rs` o il patcher), poi sul
  nodo `git checkout -- . && rm -f src/barattolo_eventi.rs` e si
  riparte dal punto 2. Niente ritocchi a mano sul nodo: la copia nel
  repo deve restare quella vera.
  5) VERDI: `git add -A` e `git commit -m "events: tell the marketplace
  server about every order transition"`, poi
  `git format-patch -1 --start-number 7` — senza `--start-number` il
  file nascerebbe `0001-` e nel repo pesterebbe la prima patch. Il
  `.patch` torna sul PC con `scp`, in `deploy/mostro/`.
  6) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.18.7-bar4 .`
  — un tag nuovo, mai sovrascritto (`-bar3` resta sulla macchina: è il
  rollback).
  7) IL COMPOSE (`cd ~/nodo`, copia prima: `cp docker-compose.yml
  docker-compose.yml.prima-bar4`): l'immagine a `mostro:v0.18.7-bar4`, e
  sotto `environment:` del servizio `mostro` le due righe
  `BARATTOLO_EVENTI_URL=https://barattolo.store/api/p2p/evento` e
  `BARATTOLO_EVENTI_SEGRETO=...`.
  8) A LIBRO FERMO — nessuno scambio preso in corso:
  `docker compose up -d mostro` (`up -d` e NON `restart`: cambiano
  immagine e ambiente). Si guarda:
  `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` dice
  `-bar4`; e `docker compose logs mostro | grep barattolo_eventi` dice
  `barattolo_eventi: order events go to https://barattolo.store/api/p2p/evento`
  (se dice `not configured` manca una delle due variabili). Da lì in
  poi ogni passo di ogni scambio lascia UNA riga:
  `barattolo_eventi: order <id> taken: delivered (HTTP 200, 840 ms)`, o
  `NOT delivered (…), giving up` — quel che dice al server la riserva
  del libro lo recupera un minuto dopo, per i cinque momenti pubblici.
  Finché il VPS non ha il segreto la porta risponde 404, e il nodo lo
  scrive (`NOT delivered (HTTP 404), no retry`): è atteso, e non ferma
  niente — è l'opposto del fail-closed dello sconto.
  9) SUL VPS, nel `config.py`: `P2P_EVENTI_SEGRETO = "..."`, poi
  `sudo systemctl restart barattolo`. Il pannello «Stato delle leve»
  deve dire accesa «Avvisi P2P — porta del coordinatore», e il journal
  alla partenza `▶️ Orologio P2P partito: … eventi del coordinatore
  ACCESI`. La porta si prova dal VPS stesso:
  `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8080/api/p2p/evento -H "Authorization: Bearer IL_SEGRETO" -H "Content-Type: application/json" -d '{}'`
  → `400` (la porta è aperta, il corpo vuoto è rifiutato); senza
  l'header → `403`; col segreto vuoto nel config → `404`.
  10) LO SPECCHIO, quando capita (non blocca niente): il
  `router.conf` della repo non copia più i kind 14. Sulla macchina del
  relay si sostituisce il file e si riavvia il router (vedi «LO
  SPECCHIO GIRA SULLA MACCHINA DEL RELAY»). Finché resta il vecchio le
  buste continuano ad arrivare sullo specchio, e nessuno le guarda.
  NEL JOURNAL DEL VPS, le righe nuove:
  `journalctl -u barattolo -f | grep -E "Evento P2P|Attese P2P|Riserva P2P|Libro P2P|Recapito P2P|PayCode P2P"`.
  DAL 24 SET 2026 (il PayCode verso chi non riconosciamo): `🧾 PayCode
  P2P fermo: <ordine> per <tg>: esterno|ignoto|estraneo|diversa` — il
  telefono di chi vende ha chiesto PRIMA dell'invio automatico del
  PayCode e il server ha detto no, quindi non è partito niente da solo.
  `esterno` = un client Mostro esterno ha preso sul nostro coordinatore
  (chi vende vede l'avviso e il bottone a mano); `ignoto` = mostrod non
  aveva ancora nominato le parti (il telefono riprova per ~1 minuto: tre
  o quattro righe di fila sono normali, poi o tace o cambia motivo);
  `diversa` = una riga stantia sul telefono; `estraneo` = chi ha chiesto
  non è una delle due parti. Un sì non lascia righe.
  `🛰️ Evento P2P: 0f3a5c1e «fiat» da buyer (giro 1): avvisati [222]`
  con sotto l'esito di Telegram per destinatario; `🛰️ Evento P2P: …
  nessuno da avvisare (giro 1, compra 111, vende 222)` per i momenti
  che non parlano (la metà muta di una coppia, il gesto di chi è solo);
  `· Evento P2P: … ripetuto (il retry del coordinatore)`; `· Evento
  P2P: … e' gia' stato detto: non si ripete`; `🔕 Evento P2P: N ha gli
  avvisi P2P SPENTI`; `⚠️ Evento P2P rifiutato: …` (un corpo storto:
  400); `📖 Libro P2P: 1 frasi in attesa per [222] (fra 60s, se il
  coordinatore tace)`; `· Riserva P2P: … l'ha gia' raccontato il
  coordinatore: il libro tace` — la riga di TUTTI I GIORNI — e
  `⚠️ Riserva P2P: … il coordinatore NON l'ha raccontato in 60s: parla
  il libro`, che è la riga DA GUARDARE: vuol dire un POST perso, e il
  perché sta nel log del nodo (`grep barattolo_eventi`).
  DAL 24 SET 2026 (l'ordine dei fatti): `· Evento P2P: … «preso» a N e'
  superato da «tornato» di 12s dopo (fonte mostro): non parte` e
  `· Evento P2P: … «tornato» a N: la presa non gli era stata detta …:
  non parte` — presa e ritiro ravvicinati, o il POST della presa
  arrivato al retry: nessuno dei due parte, ed è voluto; `· Riserva
  P2P: … e' superata da …: il libro tace`; `· Evento P2P: … e' arrivato
  dopo un fatto piu' recente: le parti dello scambio restano quelle
  dell'ultimo`; e `⛔ Libro P2P: un 38383 da <relay> non e' firmato dal
  coordinatore: buttato` (o `⛔ Ascolto P2P: …`), che è la riga DA
  GUARDARE SUBITO: un relay che serve eventi non di mostrod; `⚠️ Libro
  P2P: coincurve non c'e'` vuol dire che il libro è fermo (pip).
  LA CRONACA DI UN ORDINE, quando qualcosa non torna (in sola lettura):
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT datetime(quando,'unixepoch'), momento, dettaglio, attore, fonte, giro FROM p2p_momenti WHERE ordine LIKE '0f3a5c1e%' ORDER BY quando\")]"`
  e chi è stato avvisato di cosa:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT datetime(quando,'unixepoch'), momento, giro, tg_id, fonte FROM p2p_avvisi WHERE ordine LIKE '0f3a5c1e%' ORDER BY quando\")]"`.
  LA PROVA A DUE TELEFONI (A compra e pubblica, B vende e prende; poi
  SUBITO un secondo scambio a parti rovesciate — è il caso che il 18 set
  ha rotto tutto): la checklist sta nel verbale in CANTIERI, e ogni riga
  ha il suo avviso atteso e chi NON deve riceverlo.
  IL ROLLBACK ha due gradini, come la 0005: togliere
  `BARATTOLO_EVENTI_URL` dal compose e `up -d` (la patch diventa inerte,
  e sul VPS svuotare `P2P_EVENTI_SEGRETO` fa tornare il libro a parlare
  subito), oppure l'immagine a `-bar3`.
- LA SALITA A MOSTRO 0.18.8, immagine `mostro:v0.18.8-bar5` (22 set
  2026; il perché sta in CANTIERI, «Mostro 0.18.8 e gli importi con i
  centesimi»). Le sette patch del fork stanno in `deploy/mostro/`
  RIFATTE sopra la `v0.18.8` (commit `e67676d`), ognuna col suo patcher
  a `--secco` (README, «I SETTE PATCHER»); la 0007 porta un aggancio in
  più, il `payout-failed` pre-claim che la 0.18.8 rende possibile.
  ⚠️ NIENTE È STATO COMPILATO SUL PC: il primo `cargo` è il punto 4.
  ⚠️ E IL ROLLBACK NON È PIÙ UNA RIGA SOLA, perché la 0.18.8 porta due
  MIGRAZIONI (una colonna nella tabella dei bond): vedi il punto 0 e il
  punto 9. Per il resto è la liturgia della `-bar4`, un comando alla
  volta, a libro fermo (nessuno scambio preso in corso).
  0) IL BACKUP PRIMA, sul nodo: `cd ~/nodo && docker compose stop mostro`
  è TROPPO (ferma il libro): basta copiare il database a caldo, che è
  SQLite: `cp ~/nodo/mostro/mostro.db ~/nodo/mostro/mostro.db.prima-bar5`
  (il percorso è quello che il compose monta sotto `/config`: si
  controlla con `docker inspect nodo-mostro-1 | grep -A3 Binds` — se il
  file ha un altro nome, vale quello). È la copia da cui si torna alla
  0.18.7 se serve (punto 9).
  1) SUL PC, i dieci file al nodo (dalla cartella della repo):
  `scp deploy/mostro/patch-000*.py deploy/mostro/barattolo_fee.rs deploy/mostro/barattolo_eventi.rs UTENTE@NODO:nodo/patch-bar5/`
  — cartella NUOVA e FUORI da `mostro-src` (`mkdir -p ~/nodo/patch-bar5`
  prima). Poi sul nodo `sha256sum ~/nodo/patch-bar5/barattolo_eventi.rs`
  contro `sha256sum deploy/mostro/barattolo_eventi.rs` sul PC (in Git
  Bash; da PowerShell `Get-FileHash -Algorithm SHA256`): devono
  combaciare — il file è LF da tutt'e due le parti.
  2) SUL NODO, il sorgente nuovo: `cd ~/nodo/mostro-src && git status`
  deve dire `barattolo/v0.18.7` e albero pulito (se non è pulito, NON si
  va avanti: si guarda cosa c'è). Poi `git fetch --tags` e
  `git switch -c barattolo/v0.18.8 v0.18.8`; `git log -1 --oneline` deve
  dire `e67676d chore: Release mostro version 0.18.8`.
  3) I SETTE PATCHER, in fila, ognuno PRIMA a secco e POI senza, con un
  commit ciascuno. A secco devono dire, nell'ordine: «A SECCO: 3
  sostituzioni in src/lnurl.rs», «2 sostituzioni in src/config/util.rs»,
  «3 sostituzioni in src/app/dev_fee.rs», «4 sostituzioni in 3 file»,
  «7 agganci in 6 file», «a secco: l'ancora c'e', UNA volta», «25 agganci
  in 13 file, tutte le ancore uniche, 13 azioni note». Un FERMO qualunque
  si incolla a Claude e non si tocca niente a mano.
  `python3 ~/nodo/patch-bar5/patch-0001-lnurl-tor-freddo.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0001-lnurl-tor-freddo.py && git add -A && git commit -m "lnurl: raise HTTP timeouts so Tor-routed coordinators can resolve LNURL"`
  `python3 ~/nodo/patch-bar5/patch-0002-dev-fee-zero.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0002-dev-fee-zero.py && git add -A && git commit -m "config: let dev_fee_percentage = 0 mean no dev fee, not an invalid value"`
  `python3 ~/nodo/patch-bar5/patch-0003-dev-fee-cappelli.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0003-dev-fee-cappelli.py && git add -A && git commit -m "dev fee: raise the resolution timeouts that cap LNURL below its own budget"`
  `python3 ~/nodo/patch-bar5/patch-0004-prezzo-mai-visto.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0004-prezzo-mai-visto.py && git add -A && git commit -m "order/take: answer PriceTooStale when no price is cached yet, instead of a silent internal error"`
  `python3 ~/nodo/patch-bar5/patch-0005-fee-per-parte.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0005-fee-per-parte.py && git add -A && git commit -m "fee: per-party fees, with the loyalty discount applied at the source"`
  `python3 ~/nodo/patch-bar5/patch-0006-perche-e-fallito.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0006-perche-e-fallito.py && git add -A && git commit -m "release: log why a payout has failed"`
  `python3 ~/nodo/patch-bar5/patch-0007-eventi-al-server.py --secco`
  `python3 ~/nodo/patch-bar5/patch-0007-eventi-al-server.py && git add -A && git commit -m "events: tell the marketplace server about every order transition"`
  Alla fine `git log --oneline v0.18.8..HEAD` deve dire SETTE righe, la
  0001 in fondo. (Strada equivalente, se i patcher dessero noia:
  `git am ~/nodo/patch-bar5/000[1-7]-*.patch` con le sette `.patch`
  copiate — stesso albero, verificato sul PC.)
  4) I TEST PRIMA DELLA BUILD VERA, ed è il primo `cargo` di questo fork
  sulla 0.18.8:
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar5 .`
  e poi, in UN comando solo:
  `docker run --rm mostro-test:bar5 cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice barattolo_eventi app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle`
  Si guarda `pre_claim_failures_by_class` fra i verdi di `barattolo_eventi`
  (è il test nuovo) e che `app::release` sia verde con i test nuovi di
  upstream (`do_payment_records_the_failure_…`). Se la build o i test si
  fermano, l'errore si incolla a Claude e si corregge NEL REPO, poi sul
  nodo `git checkout -- . && rm -f src/barattolo_fee.rs src/barattolo_eventi.rs`
  e si riparte dal commit giusto (`git reset --hard v0.18.8` per rifare
  tutto). Niente ritocchi a mano sul nodo.
  5) VERDI: `git format-patch v0.18.8..HEAD -o ~/nodo/patch-bar5/export`
  e le sette tornano sul PC con `scp`, in `deploy/mostro/`, coi nomi di
  sempre: `diff` contro quelle nel repo deve dire solo l'`index` e il
  `From` (i blob e gli hash), MAI una riga di codice — se ne dice una,
  il nodo ha un sorgente diverso dal repo e ci si ferma.
  6) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.18.8-bar5 .`
  — tag nuovo; `mostro:v0.18.7-bar4` resta sulla macchina.
  7) IL COMPOSE (`cd ~/nodo`, copia prima: `cp docker-compose.yml
  docker-compose.yml.prima-bar5`): la SOLA riga dell'immagine a
  `mostro:v0.18.8-bar5`. Le cinque variabili d'ambiente (tre della 0005,
  due della 0007) restano com'erano; `settings.toml` non si tocca.
  8) A LIBRO FERMO: `docker compose up -d mostro` (`up -d`, non
  `restart`). Poi: `docker inspect --format '{{.Config.Image}}' nodo-mostro-1`
  dice `-bar5`; `docker compose logs mostro --since 2m` dice «Settings
  correctly loaded», le DUE migrazioni applicate (righe con
  `bond_payout_recipient`), `barattolo_eventi: order events go to …` e
  `barattolo_fee` col suo battito; e il 38385 nuovo si annuncia
  `mostro_version 0.18.8` (si legge dal client, «Info P2P», o dai relay).
  9) IL ROLLBACK, se serve: la riga del compose a `mostro:v0.18.7-bar4`
  NON BASTA — un binario 0.18.7 su un database che ha le due migrazioni
  della 0.18.8 si ferma all'avvio con `VersionMissing`. Le due strade:
  (a) `docker compose stop mostro`, il database dalla copia del punto 0
  (`cp ~/nodo/mostro/mostro.db.prima-bar5 ~/nodo/mostro/mostro.db`),
  la riga del compose a `-bar4`, `docker compose up -d mostro` — si
  perde quel che il libro ha scritto fra il deploy e il rollback, ed è
  la ragione del «a libro fermo»; oppure (b) senza toccare i dati:
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('/home/debian/nodo/mostro/mostro.db', timeout=5); n=c.execute(\"DELETE FROM _sqlx_migrations WHERE version IN (20260913120000, 20260914120000)\").rowcount; c.commit(); print(n)"`
  (è l'unica SCRITTURA su quel database: niente `mode=ro`, e stampa le
  righe tolte)
  e poi la riga a `-bar4` e `up -d` (la colonna in più nei bond resta e
  non dà noia al vecchio binario). La (a) è quella pulita.
  LA PROVA A DUE TELEFONI, dopo il deploy del client (stesso giorno o il
  giorno dopo, con `barattolo.store` aggiornato): A vende sats e pubblica
  col tabacchino un ordine da **23,47 €** (il campo accetta la virgola;
  numero Amazon e scadenza a 48 ore), il foglio dice il premio
  facoltativo e la riga delle 24 ore; nel libro di B la card dice
  «23,47 €» e i sats FISSI (23,47 al cambio del momento); B prende, il
  foglio «Stai comprando sats per 23,47 €»; A vede la garanzia chiesta e
  la paga; B riceve i tre dati cifrati con «Importo: 23,47 €»; B segna
  gli euro inviati, A rilascia, i sats arrivano: il conto al satoshi
  deve combaciare con `amount` del 38383 (il client lo mostra in «Info
  P2P»), e NIENTE deve dire «23 €» da nessuna parte — se una schermata
  lo dice, è un posto che legge il `fa` senza il `pm`. Poi da un client
  Mostro altrui, se c'è (mostro-cli): l'ordine si legge «23 EUR,
  Contanti al tabacchino 23.47, N sats», senza errori. E il caso del
  libro: un secondo ordine da 5,00 € lasciato LÌ, che deve sparire dal
  libro dopo 24 ore (non 48) con l'avviso «scaduto» al venditore, che
  lo ripubblica dal suo foglio. Il journal del VPS: `grep "Evento P2P"`
  dice `taken`, `hold-invoice-paid`, `fiat-sent`, `released`, `success`
  col conto in sats. E la parola di Andrea sui NUOVI avvisi: nessuno.
  IL PRE-CLAIM si prova a parte, quando capita: B mette come recapito
  un Lightning address che non esiste (`nessuno@example.com`); al
  rilascio il nodo scrive `payout-failed` con `ADDRESS_UNRESOLVED` (o
  `INVOICE_INVALID`) nel log di `barattolo_eventi`, e il VPS lo riceve.
- IL DEPLOY CHE SI FIDA SOLO DI MAIN, E IL SERVIZIO NON ROOT (21 set
  2026, audit del 19 set: G2 e A1). IL BUCO: il VPS eseguiva entro un
  minuto, da root, qualunque commit su cui stesse il ref `pronto` — e
  su un repo privato gratuito quel ref lo sposta chiunque abbia
  scrittura (`git push origin qualunque:pronto`), senza che la CI giri.
  Un account GitHub bucato valeva il VPS, con le chiavi di LNbits.
  I QUATTRO CONTROLLI di `deploy.sh`, tutti PRIMA di toccare qualcosa:
  a) il commit STA SU MAIN (antenato di `origin/main`); b) va IN AVANTI
  rispetto a quel che gira; c) la punta è FIRMATA da una chiave di
  `/etc/barattolo-deploy/firmatari` — e se quel file non c'è, o è
  vuoto, NON SI TIRA NIENTE (dal 1 ott 2026, cura 5 del cantiere «CSP e
  le voci aperte degli audit»; prima c'era una cintura di cartone
  sull'autore della punta, che in git è testo libero: per spegnere le
  firme apposta si rimette il file, non si toglie); d) la CI è VERDE su
  di lui: `giudice_deploy.py` lo
  chiede alle Actions di GitHub (il giro nato da un push SU MAIN, coi
  lavori `prove` e `segreti` in `success`).
  TRE ESITI. Si tira → «🚀 Barattolo aggiornato (sha)», con una riga
  per commit arrivato — il solo titolo, otto righe al massimo e poi
  «…e altri N» (`novita_brevi`, dal 26 set 2026). RIFIUTATO → journal, «⛔ Deploy rifiutato:
  <motivo>» ai moderatori UNA volta (timbro `.deploy-rifiutato`), e non
  si riprova da solo. ASPETTA (la CI gira, GitHub muto, token che non
  apre) → non tira, riprova al giro dopo, e dopo 10 minuti manda «⏳
  Deploy fermo» una volta (timbro `.deploy-attesa`). `--forza` riprova
  un rifiutato ma NON salta il giudice; `./deploy.sh --dimmi` dice cosa
  ne pensa il giudice senza toccare niente.
  ⚠️ COSA FERMA E COSA NO, senza raccontarsela: a), b) e d) fermano il
  push di lato su `pronto`, il ritorno a una versione vecchia e il
  commit rosso. NON fermano chi sa scrivere su MAIN: quello riscrive
  anche il workflow, e la CI diventa verde quanto vuole. Contro un
  account GitHub compromesso regge SOLO la firma, perché la chiave non
  sta su GitHub e l'elenco dei firmatari non sta nel repo. Finché le
  firme sono spente ogni deploy lo dice nel journal («⚠️ FIRME NON
  RICHIESTE»).
  ✅ LO STATO SUL VPS, AL 21 SET 2026 (lo dice Andrea, che l'ha fatto):
  il servizio gira da `barattolo` dal 21 set; le FIRME dei commit sono
  ACCESE dallo stesso giorno, coi firmatari `andrea` e `alan`; e il
  drill del deploy RIFIUTATO è riuscito. Quindi la sequenza qui sotto
  non è più «da fare»: è la procedura per rifarla, o per una macchina
  nuova. ⚠️ UNA COSA CHE IL CAMBIO D'UTENTE SI È PORTATO DIETRO: il
  server legge il cert di LND da una copia SUA,
  `/etc/barattolo/lnd-tls.cert` (`LND_PONTE_CERT` nel config), perché
  `barattolo` non entra in `/opt/lnbits/data` — e quando LND rigenera il
  suo cert (22 ott 2027) va rifatta anche lei: il comando sta alla voce
  del ponte, «SCADE IL 22 OTT 2027».
  LA SEQUENZA PER IL VPS, un passo alla volta. Si può fermare dopo
  ogni passo: ognuno lascia la macchina in uno stato che funziona.
  PASSO 1 — IL TOKEN DEL VPS, che deve saper LEGGERE e basta. Tre
  controlli, nessuno mostra il token:
  `cd /srv/barattolo && python3 giudice_deploy.py token`
  — dice che token è. «fine-grained» va bene; «⚠️ token CLASSICO … SA
  SCRIVERE» va sostituito.
  `cd /srv/barattolo && git push --dry-run origin HEAD:refs/heads/prova-permessi`
  — DEVE FALLIRE con un 403 («Write access to repository not granted»
  o simile). `--dry-run` non scrive niente nemmeno se il permesso ci
  fosse; se invece risponde «To https://github.com/…» senza errori, il
  token SA SCRIVERE.
  `./deploy.sh --dimmi`
  — l'ultima riga dev'essere «⚖️ il giudice lo tirerebbe: la CI e'
  verde…». Se dice «⏳ … non puo' leggere le Actions», al token manca
  un permesso.
  Il terzo controllo è sulla pagina: GitHub → Settings → Developer
  settings → Personal access tokens → Fine-grained tokens → il token
  del VPS: Repository access «Only select repositories: satmarket»;
  Permissions «Contents: Read-only», «Actions: Read-only» (e
  «Metadata: Read-only», che si mette da solo). NIENT'ALTRO.
  PER SOSTITUIRLO: se ne genera uno nuovo lì, con quei permessi e una
  scadenza (alla scadenza il deploy si ferma e «⏳ … (401): scaduto o
  revocato?» lo dice); dove sta quello vecchio lo dice
  `git -C /srv/barattolo config --get-regexp 'credential|remote.origin.url'`
  — con `credential.helper store` è la riga di `/root/.git-credentials`
  (`https://UTENTE:TOKEN@github.com`): si apre con `nano`, si cambia il
  solo TOKEN, e `chmod 600 /root/.git-credentials`. Poi i tre controlli
  di nuovo, e il token VECCHIO si REVOCA su GitHub. Il token non si
  incolla mai in chat.
  PASSO 2 — LE DUE UNIT (la copia dello script sotto `/run`). Prima si
  guarda che sul VPS non abbiano ritocchi a mano:
  `cd /srv/barattolo && for u in barattolo-deploy barattolo-backup; do git diff --no-index --stat /etc/systemd/system/$u.service deploy/$u.service; done`
  — devono cambiare SOLO le righe `RuntimeDirectory…`, `ExecStart` e i
  commenti. Se c'è altro: FERMATI e riferisci. Poi:
  `cp deploy/barattolo-deploy.service deploy/barattolo-backup.service /etc/systemd/system/ && systemctl daemon-reload`
  `systemctl start barattolo-deploy.service && journalctl -u barattolo-deploy -n 5 --no-pager`
  — nessun errore (nel caso normale non scrive niente: è in pari).
  PASSO 3 — IL CAMBIO D'UTENTE. Lo fa uno script, perché per qualche
  secondo il sito è giù e in quei secondi non si digita. PRIMA si
  guarda, e non tocca niente:
  `cd /srv/barattolo && bash deploy/utente/cambio-utente.sh`
  — stampa LA FOTOGRAFIA (come gira il servizio, dove stanno
  l'interprete e le librerie, il database, il disco). Se c'è un «ALT»
  il cambio oggi non si fa: si incolla l'uscita a Claude. Se finisce
  con «nessun ALT»:
  `bash deploy/utente/cambio-utente.sh --fai`
  COSA FA: crea l'utente `barattolo` (di sistema, senza shell né
  password), posa la regola di sudoers (provata con `visudo` prima),
  controlla che `barattolo` veda le stesse librerie di root, copia il
  database in `backup/`, ferma i timer di deploy e backup — tutto a
  sito ACCESO. Poi ferma il mercatino (DA QUI IL SITO È GIÙ), sposta
  `/root/satmarket` in `/srv/barattolo` lasciando un COLLEGAMENTO al
  posto di prima (in `/root` un utente qualunque non entra; col
  collegamento ogni comando di questo file, e le unit di deploy e
  backup, valgono uguali), sposta il database in `dati/` lasciando il
  collegamento `satmarket.db` (sqlite scrive il journal ACCANTO al file
  vero, verificato su Ubuntu 26.04: la cartella del database dev'essere
  scrivibile dal servizio, quella del codice MAI), sistema i permessi,
  posa il drop-in `barattolo.service.d/utente.conf`, prova da
  `barattolo` una SCRITTURA sul database (e la annulla), riavvia e
  aspetta `/api/salute` (IL SITO È TORNATO: lo script dice per quanti
  secondi è stato giù — una decina, se il disco è lo stesso). Se un
  passo dopo lo stop fallisce, TORNA A ROOT DA SOLO.
  I PERMESSI, e la regola che li tiene: `barattolo` non scrive in
  NESSUN posto da cui root esegue — il deploy gira da root dentro
  quella cartella, e se il servizio potesse scriverci chi buca il
  servizio diventerebbe root al deploy dopo. `/srv/barattolo` è
  `root:barattolo 750`; il codice e `.git` (700) sono di root;
  `config.py` è `root:barattolo 640` (il servizio lo legge, non lo
  riscrive, nessun altro lo vede); `backup/` è `root 700`; di
  `barattolo` sono SOLO `dati/`, `foto/`, `buste/`, `contenuti/`,
  `import_tmp/`. La 8080 non chiede root (è sopra la 1024). Il token di
  GitHub (`/root/.git-credentials`, 600) e `/opt/lnbits/.env` il
  servizio non li vede più.
  I CONTROLLI DOPO:
  `systemctl show barattolo -p User -p MainPID && ps -o user=,cmd= -p $(systemctl show barattolo -p MainPID --value)`
  — `User=barattolo`, e il processo è suo.
  `sudo -l -U barattolo`
  — le quattro righe `systemctl restart` (tor, lnd-ponte,
  lnd-ponte-tor, wg-quick@wg0) e NIENT'ALTRO.
  `ls -ld /srv/barattolo /srv/barattolo/config.py /srv/barattolo/dati /srv/barattolo/.git /srv/barattolo/backup`
  `sudo -u barattolo cat /root/.git-credentials /opt/lnbits/.env`
  — DEVE dire «Permission denied» due volte.
  `journalctl -u barattolo --since "10 min ago" --no-pager | grep -E "🌉|Traceback|Permission|readonly" | head`
  — la riga «🌉 Guardiano del ponte…», e nessun Permission/readonly.
  `journalctl -u barattolo -u barattolo-deploy --since "14 days ago" | grep -ciE "github_pat_|gh[pousr]_[A-Za-z0-9]{20}|lnbc[0-9a-z]{80,}|api\.telegram\.org/bot[0-9]|macaroon"`
  — deve dare 0: il journal non stampa segreti.
  E una prova VERA di scrittura: dall'app si mette e si toglie un
  preferito, si carica una foto su un annuncio di prova.
  IL DRILL DEL GUARDIANO, in un momento calmo (è lui che usa sudo):
  `systemctl stop lnd-ponte` — in circa tre minuti arrivano i due
  avvisi 🌉 e il ponte torna su DA SOLO. Se l'esito dice «a password is
  required» manca la regola di sudoers.
  ⚠️ DA QUEL GIORNO GLI SCRIPT CHE SCRIVONO si lanciano DA LUI:
  `cd /srv/barattolo && sudo -u barattolo python3 <script>.py`. Da root
  funzionano lo stesso, ma un file NATO da root in `dati/` o `foto/` il
  servizio non lo sa più riscrivere. Le letture (in sola lettura,
  i censimenti) restano come sono.
  TORNARE A ROOT, se qualcosa non gira:
  `bash /srv/barattolo/deploy/utente/cambio-utente.sh --torna`
  — o, a mano, i due comandi che fa lui:
  `rm /etc/systemd/system/barattolo.service.d/utente.conf`
  `systemctl daemon-reload && systemctl restart barattolo`
  La cartella resta in `/srv/barattolo` col collegamento: da root non
  cambia niente, quindi non c'è nient'altro da disfare.
  QUEL CHE IL DROP-IN NON HA, ed è voluto: `NoNewPrivileges` e i suoi
  parenti (con `User=` lo sottintendono anche `ProtectKernel*`,
  `SystemCallFilter`, `RestrictNamespaces`…). Il guardiano passa da
  sudo, e sudo con quel timbro risponde «no new privileges»: il ponte
  cadrebbe senza nessuno che lo rialzi. Una prova lo difende. La strada
  che li sbloccherebbe è polkit al posto di sudoers — cantiere suo.
  PASSO 4 — LE FIRME, la sola difesa che regge a un GitHub compromesso.
  SUL PC (PowerShell), una volta:
  `ssh-keygen -t ed25519 -C "firma-barattolo-andrea" -f $env:USERPROFILE\.ssh\firma_barattolo`
  — alla domanda sulla passphrase, INVIO due volte (vuota): le sessioni
  di Claude committano da sole, e una passphrase le fermerebbe. La
  chiave vive solo su quel PC, ed è un segreto che GitHub non ha.
  `git config --global gpg.format ssh`
  `git config --global user.signingkey C:/Users/Andrea/.ssh/firma_barattolo.pub`
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket config commit.gpgsign true`
  `Get-Content $env:USERPROFILE\.ssh\firma_barattolo.pub`
  — la riga che comincia con `ssh-ed25519` è la PUBBLICA: questa sì che
  si può incollare. Si fa un commit qualunque, si pusha, si aspetta il
  🚀 (le firme sono ancora spente), e SUL VPS si guarda che la firma si
  legga PRIMA di pretenderla:
  `mkdir -p /etc/barattolo-deploy && chmod 700 /etc/barattolo-deploy`
  `nano /etc/barattolo-deploy/firmatari.prova`
  — una riga per chiave: `andrea namespaces="git" ssh-ed25519 AAAA…`
  `cd /srv/barattolo && git -c gpg.ssh.allowedSignersFile=/etc/barattolo-deploy/firmatari.prova verify-commit -v HEAD 2>&1 | head -3`
  — deve dire `Good "git" signature for andrea`. SOLO ALLORA:
  `mv /etc/barattolo-deploy/firmatari.prova /etc/barattolo-deploy/firmatari && chmod 600 /etc/barattolo-deploy/firmatari`
  `./deploy.sh --dimmi` — la prima riga ora dice «firma richiesta».
  Da lì un commit la cui PUNTA non è firmata viene rifiutato («⛔ … non
  porta la firma»). Alan manda la sua pubblica e diventa una seconda
  riga (`alan namespaces="git" ssh-ed25519 …`). ⚠️ Un merge fatto DAL
  SITO di GitHub lo firma GitHub, non noi: viene rifiutato, ed è
  giusto. Dopo un merge dal sito si spinge un commit firmato sopra
  (`git pull && git commit --allow-empty -m "Rilascio" && git push`).
  ⚠️ `git commit-tree` NON guarda `commit.gpgsign`: chi costruisce un
  commit a mano gli passa `-S`. SPEGNERE LE FIRME, se servisse:
  `mv /etc/barattolo-deploy/firmatari /etc/barattolo-deploy/firmatari.spento`.
  PASSO 5 — LA VERIFICA FINALE, tutt'e due le metà. 1) Un push normale
  su main → entro un minuto dalla CI verde arriva «🚀 Barattolo
  aggiornato», e nel journal `journalctl -u barattolo-deploy -n 3
  --no-pager` la riga «🚀 aggiornamento: … · la CI e' verde su main per
  questo commit · firma richiesta». 2) Il ref `pronto` spostato A MANO
  su un commit fuori da main → rifiutato e avvisato. DAL PC, in una
  cartella usa-e-getta (mai nella cartella di lavoro condivisa):
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket worktree add --detach $env:TEMP\prova-pronto origin/main`
  `git -C $env:TEMP\prova-pronto commit --allow-empty -m "PROVA: commit finto fuori da main"`
  `git -C $env:TEMP\prova-pronto push origin HEAD:refs/heads/pronto`
  — entro un minuto su Telegram: «⛔ Deploy rifiutato: xxxxxxxx non sta
  su main: qualcuno ha spostato «pronto» a mano». Sul VPS
  `./deploy.sh --dimmi` dice «⛔ il giudice lo RIFIUTEREBBE», e
  `git -C /srv/barattolo log -1 --oneline` è ANCORA il commit di prima.
  POI SI RIMETTE A POSTO, o il prossimo semaforo della CI trova
  `pronto` fuori strada e diventa rosso:
  `git -C $env:TEMP\prova-pronto push --force origin origin/main:refs/heads/pronto`
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket worktree remove --force $env:TEMP\prova-pronto`
  (rimettere `pronto` sulla punta di main non è un rischio: da oggi il
  VPS la CI la chiede da sé, e una punta non ancora verde aspetta.)
- LE NOTIFICHE SUL TELEFONO (web push, 14 nov 2026, cantiere
  web-push): NIENTE DA FARE SUL VPS. La leva `WEB_PUSH_ATTIVO` nel
  codice è accesa, e il timbro (la chiave VAPID) lo crea il server da
  solo nel database al primo /api/me dopo il riavvio: nel journal una
  riga sola, «📲 Notifiche sul telefono: timbro VAPID creato nel
  database». Niente pip: basta `cryptography`, già lì per i DM Nostr
  (senza, il tasto non compare e il pannello è in allarme). Nessuna
  release dell'app: la 1.5 ha già `enableNotifications: true`.
  SPEGNERLE: dal pannello «⚙️ Stato delle leve» → «📲 Notifiche sul
  telefono», o `WEB_PUSH_ATTIVO = False` nel config e riavvio. Le
  iscrizioni restano, e riaccesa si riparte.
  QUANTI TELEFONI, in sola lettura: `sqlite3 -readonly
  /srv/barattolo/dati/satmarket.db "SELECT COUNT(*), COUNT(DISTINCT
  tg_id) FROM push_iscrizioni"`. MAI stampare `push_timbro`: è la
  chiave privata. Se si perde (database rifatto da zero) se ne crea
  una nuova da sola e i telefoni vanno riattivati dal cassetto.
  I servizi push chiamati dal VPS: fcm.googleapis.com (Android/Chrome),
  updates.push.services.mozilla.com, web.push.apple.com,
  *.notify.windows.com, in https: se un giorno il firewall in uscita
  si stringe, sono questi. Un invio non riuscito lo dice il journal
  con «⚠️ Push all'utente…».
- L'APP ANDROID (TWA, ZAPSTORE) — la procedura viveva solo in
  `ARCHITETTURA.md`, che racconta com'è fatta; qui c'è cosa si BATTE, e
  in che ordine. L'app è un **involucro** (Trusted Web Activity) fatto
  con **Bubblewrap** (`@bubblewrap/cli`, 1.24.1): dentro non c'è codice
  web, tutto arriva vivo da barattolo.store — quindi un cambio al sito
  NON richiede una release, e una release serve solo per l'involucro
  (icona, splash, colori, versione).
  IN SERVIZIO: la **v1.5** (versionCode 7), pubblicata il 23 set 2026
  sui due canali — il tema dell'avvio che si disegna le barre e le barre
  vere, qui sotto. È uscita al TERZO giro: le prime due build, provate
  sul telefono, non sono state pubblicate, e una versione mai uscita si
  rifà con la STESSA versione (`--skipVersionUpgrade`, qui sotto). La
  prossima sarà la 1.6 col versionCode 8, che alza `bubblewrap update`
  da solo.
  IL PROGETTO STA FUORI DAL REPO, in
  `C:\Users\Andrea\Documents\barattolo-twa`, e ci resta (un percorso
  spezzato a metà non si cerca più): lì dentro c'è il **keystore**
  (`barattolo.keystore`, alias `barattolo`, password battute a mano da
  Andrea nel suo terminale — mai in uno script, mai in chat). Nella
  stessa cartella vivono `genera_chiave_release.py` e
  `profilo_release.py`, che non scrivono segreti su disco.
  ⚠️ **STESSO KEYSTORE O L'AGGIORNAMENTO È RIFIUTATO**, ed è la riga
  che costa di più a scoprirla tardi: Android rifiuta un APK firmato
  con una chiave diversa da quella installata, e non c'è rimedio se non
  far disinstallare e reinstallare a ogni utente. Perso il keystore,
  l'app è persa. La sua impronta —
  `2F:3F:5E:68:94:AB:A0:B8:E4:39:B7:28:9D:55:50:D5:0E:22:37:15:F3:A8:E6:4F:2C:49:38:BC:D5:A2:C2:3C`
  — è la stessa scritta in `.well-known/assetlinks.json`, ed è ciò che
  dice ad Android che l'app può aprire il dominio a tutto schermo:
  dal 22 set 2026 la coppia (pacchetto + impronta + rotta che la serve)
  ha la sua sentinella in `prove.py` (`prove_app_android`), perché un
  refuso lì non rompe niente di visibile — si vede solo sul telefono,
  come una barra del browser che ricompare.
  L'ORDINE È FERREO, e non è pignoleria: `bubblewrap update` cancella e
  riscrive proprio i file che lo script patcha.
  1. `bubblewrap update --appVersionName=X.Y` (il versionCode lo alza
     lui) — dalla cartella del progetto, con `node` nel PATH. Per
     RIFARE una versione mai pubblicata, `bubblewrap update
     --skipVersionUpgrade`: rigenera il progetto e lascia versione e
     versionCode come sono. ⚠️ E L'UPDATE NON SI SALTA MAI, nemmeno per
     rifare: lo script riconosce i suoi blocchi dal marcatore e quelli
     che trova già li SALTA, quindi su un progetto già patchato un
     blocco cambiato nel repo resterebbe quello vecchio, in silenzio;
  2. `python genera_icone_apk.py` — DAL REPO (aggiornato: `git pull`
     prima, o gira lo script di ieri), e rifà icona adattiva,
     monochrome e splash (vedi ARCHITETTURA, «Icona adattiva
     dell'APK»). PRIMA di scrivere qualunque file prepara in memoria i
     due che Bubblewrap rigenera: in `LauncherActivity.java` il
     **permesso dello splash**, l'**uscita dello splash di sistema** e
     le **barre vere**; nel manifest il **tema dell'avvio** (qui
     sotto). Se esce con «⛔ … NON lanciare `bubblewrap build`» il
     modello di Bubblewrap è cambiato: non si builda, si guarda il file;
  3. `bubblewrap build` — le password le batte Andrea;
  4. tre controlli sull'APK firmato, dalla cartella del progetto, e
     PRIMA della release, che dopo non si ritira. L'**impronta**:
     `& "$env:USERPROFILE\.bubblewrap\jdk\jdk-17.0.11+9\bin\keytool.exe" -printcert -jarfile app-release-signed.apk`
     deve dire `SHA256: 2F:3F:5E:68:…:C2:3C`, quella scritta qui sopra.
     Le **cure dentro il dex**:
     `python -c "import zipfile; z=zipfile.ZipFile('app-release-signed.apk'); d=b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex')); print('permesso:', d.count(b'permesso dello splash non concesso'), '| uscita:', d.count(b'uscita dello splash non presa'), '| barre:', d.count(b'barre non passate alla pagina'), '| libreria:', d.count(b'Failed to transfer splash image.'))"`
     deve dire **1 | 1 | 1 | 1** (sulla v1.4 dice 1 | 0 | 0 | 1). E il
     **tema nel manifest**:
     `& "$env:USERPROFILE\.bubblewrap\android_sdk\build-tools\35.0.0\aapt2.exe" dump xmltree --file AndroidManifest.xml app-release-signed.apk | Select-String "theme"`
     deve dare DUE righe: `=@0x01030010` (l'app intera, il traslucido
     di Bubblewrap, com'era) e `=@0x7f…` (LauncherActivity, il nostro);
     sulla v1.4 ne dà una sola. E le **barre disegnate dalla
     finestra**, l'unico controllo che distingue una build di oggi da
     quelle di prima con la STESSA versione:
     `& "$env:USERPROFILE\.bubblewrap\android_sdk\build-tools\35.0.0\aapt2.exe" dump resources app-release-signed.apk | Select-String "0x01010450=true"`
     deve dare DUE righe (il tema di base e la sua copia per Android
     6+): è `windowDrawsSystemBarBackgrounds`, qui sotto. Se non esce
     niente, lo script che ha girato era quello di prima;
  5. la **prova sul telefono**, PRIMA della release: USB con il debug
     attivo,
     `& "$env:USERPROFILE\.bubblewrap\android_sdk\platform-tools\adb.exe" install -r app-release-signed.apk`
     («Success»: stessa chiave, versionCode più alto, e l'app si
     aggiorna tenendo i dati). Cosa si guarda sta nel verbale del
     cantiere in CANTIERI.
  ⚠️ LA DOMANDA DEL BUILD NON RIGUARDA IL SITO, e qui era scritta male:
  «There are changes in twa-manifest.json. Would you like to apply
  them…» scatta quando `twa-manifest.json` non combacia più con
  `manifest-checksum.txt`, cioè col file dell'ultimo `update` (letto nel
  sorgente, `cmds/build.js`, `hasManifestChanged`) — il `manifest.json`
  del sito non lo guarda nessuno. A luglio l'aveva fatta scattare lo
  script, che riscriveva `backgroundColor` dal crema all'arancio.
  **Si risponde `n` lo stesso**, e dalla v1.4 con una ragione in più:
  `y` lancia un update, che cancella `app/` e con lei icone, splash E il
  permesso dello splash; se è scappato un `y`, si rifà il passo 2 PRIMA
  di ribuildare. Nel giro normale la domanda non arriva più: lo script
  riscrive `backgroundColor` solo se l'arancio campionato cambia.
  IL PERMESSO DELLO SPLASH (set 2026, v1.4). Da Chrome 152 (stabile il
  25 ago 2026) lo splash non arrivava più a Chrome: la libreria gli
  consegna il PNG con `receiveFile()`, Chrome adesso esige che anche CHI
  CONSEGNA abbia il permesso sull'URI, e chi possiede il FileProvider
  non ha un record esplicito. Risultato: «Failed to transfer splash
  image.» nel log, Chrome parte senza splash e senza spegnere
  l'animazione, e la sua finestra entra da destra SCURA per mezzo
  secondo prima della pagina. Non è un errore di configurazione
  (android-browser-helper #623, aperto): la cura è un
  `grantUriPermission` a noi stessi, READ + PERSISTABLE, prima di
  `super.onCreate()`, e la rimette lo script a ogni build. Il perché
  per intero sta in CANTIERI, «Lo splash che Chrome 152 non prende più».
  Se sul telefono la finestra scura tornasse, la domanda si fa al log
  col telefono attaccato in USB (debug USB acceso):
  `& "$env:USERPROFILE\.bubblewrap\android_sdk\platform-tools\adb.exe" logcat -s SplashScreenStrategy Barattolo`
  e si apre l'app: «Failed to transfer splash image.» vuol dire che
  Chrome rifiuta ancora, «permesso dello splash non concesso» che il
  permesso non è partito.
  I COLORI DELL'INVOLUCRO, dalla v1.4: `themeColor`, `navigationColor`
  e i divisori sono il FONDO DELLA PAGINA — `#FAF4E4` di giorno,
  `#211A10` di sera, gli stessi che `applicaTema()` scrive nel
  `theme-color` — così le barre non cambiano colore quando la pagina
  arriva. `backgroundColor` resta l'arancio CAMPIONATO `#F78F19`: è il
  fondo dello splash, e lo riscrive lo script. E
  `splashScreenFadeOutDuration` è **0**: dallo splash di Chrome al
  guscio della pagina si passa di taglio, e il guscio è disegnato
  apposta uguale allo splash.
  IL TEMA DELL'AVVIO (set 2026, v1.5). LauncherActivity ha un tema
  SUO, `BarattoloAvvio`, OPACO: col traslucido di Bubblewrap Android
  non preparava nessuna finestra di partenza, e la finestra che
  cresceva dall'icona era NERA per un fotogramma. Da Android 12 la
  finestra di partenza è lo splash del sistema, e il tema lo veste
  dello stesso arancio e dello stesso barattolo di `splash.png`; prima
  di Android 12 è il fondo della finestra, uguale. E la finestra le
  barre se le DISEGNA DA SÉ (`windowDrawsSystemBarBackgrounds`, terzo
  giro): il `Theme.NoTitleBar` dice di no, e a una finestra così
  Android le dipinge NERE, qualunque colore si scriva — era la barra
  nera di ~150 ms, dipinta da LauncherActivity fra lo splash del
  sistema e Chrome, e i colori messi nel secondo giro da soli non
  potevano curarla. Da Android 15 la barra è trasparente sull'arancio
  della finestra; prima prende il colore che le dà la libreria della
  TWA, quello che avrà Chrome. Il resto dell'app resta traslucido. Il PREZZO,
  deciso da Andrea: aprendo un link a
  barattolo.store da un'altra app mentre Barattolo è già aperta, fra
  la pagina di prima e quella del link passa un lampo arancio col
  barattolo — la libreria il tema trasparente lo raccomanda proprio
  per quel caso. Il perché per intero sta in CANTIERI, «Il nero
  all'avvio dell'APK».
  LE BARRE VERE (v1.5): da Android 11 l'APK mette nella URL di avvio
  il parametro `barre=sopra,sotto,densità` — le due barre in pixel e la
  `densityDpi` dello schermo —, e la pagina lo usa per il guscio
  (`barreDellApp`). L'indirizzo NON lo ripulisce: il primo giro lo
  faceva con un `replaceState`, e dentro l'APK la barra dell'indirizzo
  non c'è e nessuna condivisione copia `location.href`. Nei log del
  server le aperture dall'app si riconoscono da lì.
  LE DUE RIGHE PER APPVERIFIER, uguali in tre posti: le note di OGNI
  release, il README di barattolo-releases e la pagina Sicurezza del
  sito (`/sicurezza#app`). Si copiano da qui, identiche — una prova
  confronta questo blocco e quello della pagina con `assetlinks.json`:
  ```
  store.barattolo.app
  2F:3F:5E:68:94:AB:A0:B8:E4:39:B7:28:9D:55:50:D5:0E:22:37:15:F3:A8:E6:4F:2C:49:38:BC:D5:A2:C2:3C
  ```
  LA RELEASE, due canali, e la release GitHub è la fonte unica di
  verità. Prima GitHub, poi Zapstore, sempre.
  1. `barattolo-X.Y.apk` (copia rinominata di `app-release-signed.apk`)
     + il suo `.sha256`, e `gh release create vX.Y` sul repo pubblico
     `kreamistudio-crypto/barattolo-releases` (satmarket resta privato:
     Obtainium e Zapstore esigono download anonimi), con le note in
     `note-vX.Y.md` accanto al progetto: l'hash dell'APK e le due righe
     per AppVerifier qui sopra. Obtainium segue quel repo da solo;
  2. in **WSL Ubuntu** (`zsp` è solo Linux/macOS, vive in `/root/bin/zsp`
     e vuole root): `read -rs SIGN_WITH && export SIGN_WITH` col prompt
     nascosto, `zsp publish`, poi `unset SIGN_WITH`. La chiave è quella
     **dedicata e fredda** delle release
     (`npub1yjkuma9cenrzde7duj222gp44raqa88uj352z0akrtw0mvvfrhhsx8g68u`,
     nsec su due foglietti + Bitwarden «Barattolo release Nostr»): mai
     sul VPS, mai su disco, mai in chat, e **non è la chiave della
     piattaforma** — i due destini restano separati apposta.
  ⚠️ `zsp` cambia in fretta: prima di ogni publish si riguarda il README
  di `github.com/zapstore/zsp`, e la scheda è `zapstore.yaml` nella root
  di barattolo-releases.
  ⚠️ **LA PROVA NIP-C1 SCADE DOPO UN ANNO**, cioè intorno a **luglio
  2027**: è il kind 30509 che lega il certificato Android alla npub
  (`zsp identity --link-key`, col rito del `.p12` temporaneo da
  cancellare subito). Scaduta non blocca niente — le release escono lo
  stesso — ma il legame smette di essere dimostrabile. Il perché e il
  rito per esteso stanno in ARCHITETTURA, «Distribuzione dell'APK».
- DOVE SI LEGGE IL GIRO DEI NEGOZI COLLEGATI (set 2026): il giro
  dell'ora stampa una riga per annuncio nato (`🏪 Titolo — prezzo €
  [categoria]`, con ` · digitale` sui virtuali), una per consegna
  corretta (`↔ consegna corretta (digitale|del cassetto): Titolo`),
  una per spegnimento (`🗑 tolto dal negozio`) e la riga di riepilogo
  `🏪 woo #<id>: N nuovi, …, K saltati`; i SALTATI col loro perché
  NON si stampano, stanno nel JSON `connettori.ultimo_esito`
  (`saltati`, `entrati`, `consegna_corretta`), che è quello che il
  cassetto del venditore mostra. In sola lettura:
  `journalctl -u barattolo --since "48h ago" | grep -E "🏪|Connettore|↔|🗑"`
  e
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT id, fonte, url_negozio, datetime(ultimo_giro,'unixepoch','localtime'), ultimo_errore, ultimo_esito FROM connettori\")]"`.
  Un `variable` Woo che nel report dice
  «ha piu' varianti e non le ho potute leggere» è un lettore che non ha
  agganciato le variazioni (chiamata fuori dal lettore); «nessuna delle
  sue varianti e' in vendita» è il negozio.
- «DATABASE IS LOCKED» E IL GIRO DEI NEGOZI (1 ott 2026, Cantieri,
  «Database is locked»): il giro teneva una transazione di scrittura
  aperta per tutta la durata delle foto e le rotte morivano dopo 5 s.
  Da oggi le foto si scaricano fuori da ogni transazione, la riga nasce
  in due commit brevi, le sparizioni vanno a lotti di 25 e `db()` apre
  con `timeout=DB_BUSY_TIMEOUT` (15 s nel codice; la riga nel config del
  VPS NON serve, si aggiunge solo per cambiarlo). AL PRIMO GIRO DOPO IL
  DEPLOY si guarda, in sola lettura:
  `journalctl -u barattolo --since "2h ago" | grep -E "database is locked|🏪|Connettore|Timbro"`
  — la fila dei `🏪 …` e il riepilogo `🏪 woo #<id>: N nuovi, …` SENZA
  un `database is locked` in mezzo o dopo, e nessun `Timbro «…» non
  scritto`; durante il giro `satmarket.db-journal` compare e sparisce
  (commit brevi) invece di restare aperto per minuti. Se un `locked`
  ricompare, si incolla la riga PRIMA: dice chi teneva il lucchetto.
  Il WAL NON è acceso (pro e contro nel verbale): se un giorno si
  accende, prima la procedura qui (backup e ripristino con `-wal` e
  `-shm`, prova del `-readonly` a server fermo).
- I NEGOZI GRANDI (1 ott 2026, Cantieri, «I negozi grandi»): i valori
  nuovi sono i DEFAULT del codice — mille prodotti letti per giro, il
  rodaggio a cento per ventiquattro ore — e NEL CONFIG DEL VPS NON SI
  AGGIUNGE NIENTE. Ma il config vince: prima del deploy, in sola
  lettura, `grep -n "MAX_PRODOTTI_CONNETTORE\|MAX_NUOVI_CONNETTORE\|ORE_RODAGGIO\|DB_BUSY_TIMEOUT" /srv/barattolo/config.py`
  — una riga `MAX_PRODOTTI_CONNETTORE = 200` (copiata dal config
  d'esempio di prima) terrebbe il tetto a duecento: si porta a 1000 o si
  cancella, e si riavvia. Le leve si leggono vive nel pannello «⚙️ Stato
  delle leve», gruppo «🏪 Negozi collegati». AL PRIMO GIRO DOPO IL
  DEPLOY: `journalctl -u barattolo --since "2h ago" | grep -E "🏪|Connettore|database is locked"`
  — il riepilogo `🏪 woo #<id>: N nuovi, …` (cento all'ora per un
  negozio nel suo primo giorno, comunque parta il giro — un «🔄
  Aggiorna ora» subito dopo dice 0 nuovi, ed è giusto —, poi trenta a
  giro), e su un negozio lento la coda «, N con le varianti al prossimo
  giro» (la lettura a tempo: NON è un errore, il collegamento resta
  attivo e ruota). Il giro respira dopo ogni riga SCRITTA perché le
  richieste della app trovino il database libero; un `database is
  locked` non deve comparire. (1 ott 2026 sera) Le righe identiche non
  si scrivono più: nel riepilogo «N invariati» è il grosso del catalogo,
  e un giro di regime dura poco. I prodotti in bozza sul negozio non
  nascono: entrano quando il negoziante li pubblica.
- LE FAMIGLIE DI UN NEGOZIO COLLEGATO (30 set 2026): le scrive il giro
  dell'ora, quindi dopo il deploy compaiono al PRIMO giro e non prima.
  Si guardano, in sola lettura, per collegamento:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT famiglia, famiglia_titolo, stato, COUNT(*) FROM annunci WHERE connettore_id=<id> GROUP BY famiglia, stato\")]"`
  — righe con `famiglia` vuota = prodotti senza famiglia (o giro non
  ancora passato).
  NASCONDERE UN NEGOZIO DALLA VETRINA SENZA CANCELLARE NIENTE (il gesto
  del 30 set 2026 su AGORA): lo stato `revisione`, che il giro NON
  riaccende mai (lo aggiorna, lo spegne se il prodotto sparisce). È il
  ↩︎ del moderatore fatto in blocco, e lascia fuori le righe con un
  ordine vivo (anche dentro un carrello) e le aste. Prima la fotografia:
  `python3 -c "import sqlite3; s=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); d=sqlite3.connect('/root/prima-<nome>.db'); s.backup(d); d.close(); s.close()"`.
  ⚠️ LA TILDE SOTTO `sudo -u barattolo` NON È SUA: la espande la shell di
  root prima che sudo parta, quindi diventa `/root/satmarket/...`, dove
  `barattolo` non entra («unable to open database file», nessuna
  modifica). Le SCRITTURE si fanno sul file vero,
  `sudo -u barattolo python3 -c "import sqlite3; c=sqlite3.connect('/srv/barattolo/dati/satmarket.db', timeout=5); n=c.execute(\"...\").rowcount; c.commit(); print(n)"`,
  così il journal nasce suo accanto al database; le letture da root
  restano con la tilde. Il gesto non passa dal registro della
  moderazione (va scritto nel verbale) e il pallino dei moderatori
  sale: su quelle righe nessuno preme ✅.
  RIMETTERLE IN VETRINA, a famiglie scritte: prima si guarda (sopra) che
  il giro abbia riempito `famiglia`, poi
  `sudo -u barattolo python3 -c "import sqlite3; c=sqlite3.connect('/srv/barattolo/dati/satmarket.db', timeout=5); n=c.execute(\"UPDATE annunci SET stato=CASE WHEN quantita>0 THEN 'attivo' ELSE 'venduto' END WHERE connettore_id=<id> AND stato='revisione' AND famiglia!=''\").rowcount; c.commit(); print(n)"`
  (stampa quante righe ha cambiato)
  — il `CASE` tiene l'invariante di casa (venduto ⇔ zero pezzi) per le
  taglie finite nel frattempo, e `famiglia!=''` lascia in attesa ciò che
  il giro non ha ancora legato.
- I CARRELLI TOLTI (24 set 2026): il carrello torna quello di prima —
  uno solo, di un venditore alla volta, in memoria — e con i carrelli
  per venditore se ne va il PAGAMENTO UNICO, cioè la busta in
  `pagamenti` col motivo 'carrello', in produzione da 297063d. Il
  server di adesso quella busta NON la sa più incassare
  (`_incasso_del_motivo` conosce 'banner' e 'negozio_slug'), quindi
  PRIMA del deploy si guarda, in sola lettura, che non ce ne siano:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT 'busta', id, stato, importo_sats, datetime(creato,'unixepoch','localtime') FROM pagamenti WHERE motivo='carrello' UNION ALL SELECT 'ordine', id, stato, pagamento_id, datetime(creato,'unixepoch','localtime') FROM ordini WHERE pagamento_id > 0\")]"`
  Nessuna riga (o «no such column: pagamento_id», su un database che
  quella colonna non l'ha mai avuta) = si va: il 24 set 2026, prima
  del push, non ha stampato niente. Una `busta` in `creato` = una
  fattura ancora aperta che dopo il deploy nessuno incasserebbe: ci
  si ferma. Una busta chiusa (`pagato`, `annullato`, `rimborsato`)
  non blocca, ma il libro mastro la segnala per sempre, in qualunque
  stato («pagamento con un motivo che nessuno sa incassare»): si
  guarda a mano. `orfani.py` invece non la vede — riconosce l'incasso
  dal suo hash, e la riga non si cancella mai. Le righe `ordine` sono
  ordini nati da una busta: dopo il deploy vivono come ordini
  qualunque, ognuno col suo prezzo. LE COLONNE RESTANO:
  `ordini.pagamento_id` e `ordini.mai_incassato` (con l'indice) sul
  VPS ci sono e non le scrive più nessuno; niente DROP, apposta. E IL
  WORKFLOW È CAMBIATO (via `collaudo_carrelli_unico` dai due elenchi):
  se il job `pronto` si ferma con «refusing to allow a GitHub App…»,
  vale «LA CATENA DEL DEPLOY» — il ref si sposta a mano, senza
  --force, col via di Andrea.

- IL CARRELLO SALVATO (6 ott 2026): niente leva e niente config. La
  tabella `carrello_salvato` nasce da sola al primo avvio del codice
  nuovo (`init_db`, `CREATE TABLE IF NOT EXISTS`), e la scopa dei sette
  giorni gira nell'orologio. Per guardare, in sola lettura — quanti
  carrelli ci sono e il più vecchio:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT COUNT(*), datetime(MIN(aggiornato),'unixepoch','localtime') FROM carrello_salvato\")]"`
  Il più vecchio non deve superare i sette giorni (più il giro
  dell'orologio). TORNARE INDIETRO col codice di prima non chiede
  niente: quel codice la tabella non la legge né la scrive, e resta lì
  innocua; niente DROP. Il perché per intero: CANTIERI, «Il carrello
  salvato».

- IL BANNER DELLE COMMISSIONI P2P (25 set 2026): la capsula in cima al
  libro ordini («Fee P2P 2%» barrato, «BETA 1,5%», «Pionieri o Lv.5
  −0,5%») è UN FILE, `assets/p2p-banner-fee.webp`, e le sue cifre sono
  disegnate: il foglio che si apre al tocco invece legge i numeri vivi
  (fee del nodo, `P2P_COMMISSIONE_PERCENTO`, `P2P_SCONTO_FEDELTA_PERCENTO`)
  e da solo non va toccato. QUANDO FINISCE LA BETA (o cambia una cifra)
  si cambia il DISEGNO, sul PC e non sul VPS, e parte col deploy:
  1) il PNG nuovo con lo sfondo trasparente → ritaglio stretto
  sull'alpha, largo 1000 (il 3x del banner, che è 5/6 della pagina di
  un telefono da 400; fino al 26 set 2026 era 1200 — e se il PNG
  ritagliato è più stretto si INGRANDISCE fino a 1000, in alpha
  premoltiplicata, com'è successo col disegno del 26 set 2026 sera,
  955 → 1000), WebP qualità ~86,
  sotto i 50 KB, senza ICC/EXIF/XMP — la ricetta di Pillow sta nella
  voce di CANTIERI «Il banner delle commissioni nel libro P2P»;
  1b) DAL 26 SET 2026 LA CAPSULA MARRONE SI TOGLIE DAL FILE: la disegna
  il CSS col colore delle card del tema. Sul file ridotto a 1000 (col
  suo marrone) `python prepara_banner_fee.py <ridotto> <uscita.webp>`:
  misura pillole, etichetta e dischi delle frecce, ricostruisce i bordi
  dalla forma (niente aloni) e lascia il resto trasparente; se il
  disegno non e' quello atteso si FERMA. Poi `prove_banner_fee_personale`
  rimisura i contorni sull'alfa e dice i ritagli (`clip-path`) da
  riscrivere se le pillole si sono spostate;
  2) si SOSTITUISCE il file con lo STESSO NOME (la rotta
  `/assets/p2p-banner-fee.webp` e il markup non cambiano; il timbro
  `?v=` lo rifà `_timbra_asset_pagina`, quindi nessuna cache tiene il
  disegno vecchio);
  2b) DAL 9 OTT 2026 SI RIFÀ ANCHE IL RITAGLIO DELLA PRIMA VOLTA:
  `python ritaglia_banner_fee.py` riscrive
  `assets/p2p-banner-fee-senza-barra.webp` (la prima pillola senza la
  barra rossa, per la primissima animazione); le misure della barra in
  testa allo script sono quelle della `.fee-barra` del CSS, e
  `prove_banner_fee_primo_ingresso` resta rossa finché il ritaglio non
  torna col banner nuovo. Se il disegno nuovo non ha più un 2% barrato,
  la primissima va ripensata (CANTIERI, «Il banner delle commissioni, la
  prima volta»);
  3) nel `<button id="p2pFeeBanner">` di `miniapp.html` si riscrive
  l'`alt` con le cifre del disegno NUOVO (è la descrizione di
  quell'immagine, per chi legge con la voce) e, se le proporzioni sono
  cambiate, `width`/`height` coi pixel del file: `prove_banner_fee_p2p`
  li confronta col file e se non tornano dice i due numeri giusti;
  4) prove, commit firmato, push. Se la beta finisce SENZA un disegno
  nuovo, il banner si toglie (il bottone, la sua regola e la prova) —
  un disegno che dice «BETA» dopo la beta è peggio di niente, mentre
  il foglio si aggiusta da solo: a fee pari al listino smette di dire
  «beta».
- LE DISPUTE P2P (28 set 2026) — COSA C'È OGGI, e cosa manca. Da
  questo deploy, a ogni `dispute-opened` di mostrod ogni moderatore
  (`ADMIN_IDS`) riceve su Telegram l'ordine, chi l'ha aperta, le due
  persone, importo, metodo e da quando la garanzia è bloccata; la
  disputa ha la sua riga in `p2p_dispute` e ogni passo una riga in
  `p2p_dispute_registro`. Nel journal le righe cominciano con «⚖️
  Disputa P2P». ⚠️ LA SEZIONE «⚖️ Moderazione P2P» NELL'APP NON C'È
  ANCORA, e nessuna chiave di moderatore è stata aggiunta al nodo: fino
  ad allora una disputa si chiude in uno dei tre modi qui sotto.
  (Dal 29 set 2026 la sezione C'È: vedi «LA MODERAZIONE DELLE DISPUTE
  P2P: LA PROCEDURA», più sotto.)
  COME SI LEGGE UNA DISPUTA SUL NODO (sola lettura; MAI `SELECT *` su
  `orders`: porta `preimage` e `buyer_invoice`, che in una chat non ci
  vanno):
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); q=c.execute(\"SELECT d.status AS disputa, d.order_previous_status AS prima, COALESCE(d.solver_pubkey,'-') AS solver, datetime(d.created_at,'unixepoch') AS aperta, o.id AS ordine, o.kind, o.status, o.amount, o.fee, o.fiat_amount, o.fiat_code, o.payment_method, o.buyer_dispute, o.seller_dispute, datetime(o.invoice_held_at,'unixepoch') AS hold_pagata, o.hash FROM disputes d JOIN orders o ON o.id=d.order_id ORDER BY d.created_at DESC LIMIT 3\"); print(*[d[0] for d in q.description], sep='|'); [print(*r, sep='|') for r in q]"`
  (la prima riga sono i nomi delle colonne)
  poi la garanzia: `cd ~/nodo && docker compose exec lnd lncli lookupinvoice <hash>`
  (`state` `ACCEPTED` = sats bloccati; `expiry_height` dentro `htlcs`)
  e `docker compose exec lnd lncli getinfo | grep block_height`: la
  scadenza è `(expiry_height − block_height) × 10 minuti`.
  CHI HA CHIESTO L'ANNULLO, quando un «Chiedi di annullare» riceve un
  no:
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); q=c.execute(\"SELECT status, substr(seller_pubkey,1,8) AS vende, substr(buyer_pubkey,1,8) AS compra, substr(cancel_initiator_pubkey,1,8) AS annullo_chiesto_da, seller_cooperativecancel AS v_annulla, buyer_cooperativecancel AS c_annulla, buyer_dispute, seller_dispute FROM orders WHERE id LIKE '<primi 8>%'\"); print(*[d[0] for d in q.description], sep='|'); [print(*r, sep='|') for r in q]"`
  — se `annullo_chiesto_da` è la chiave di chi sta riprovando, mostrod
  risponde `invalid_pubkey`: la conferma deve venire dall'ALTRA parte.
  I log: `cd ~/nodo && docker compose logs mostro --since 4h 2>&1 | grep -i -E "<primi 8>|cant|InvalidPubkey" | tail -40`.
  I TRE MODI DI CHIUDERLA, dal più sicuro:
  1) LE PARTI SI ACCORDANO. Una tocca «Chiedi di annullare», l'altra
  «Accetta di annullare» (o «Chiedi di annullare»: per mostrod il
  secondo `cancel` è la conferma): la hold si cancella, i sats tornano
  a chi vende, la disputa si chiude come `SellerRefunded`. Oppure chi
  vende libera i sats dalla pagina dello scambio, e vanno a chi compra
  (il bottone nell'app c'è DAL 13 OTT 2026: «✅ Rilascia i sats», a
  disputa aperta, anche già presa da un moderatore — CANTIERI, «La
  disputa aperta per sbaglio»; sul nodo la disputa risulta `released`).
  Nessuna chiave di moderatore. I moderatori leggono «Disputa P2P
  chiusa dalle parti».
  2) NESSUNO FA NIENTE. Il guardiano delle scadenze di mostrod guarda
  solo `active` e `fiat-sent`: una disputa non la tocca. Alla scadenza
  dell'HTLC LND lo molla da solo e i sats tornano a chi vende; l'ordine
  resta `dispute` nel database del nodo. Dopo quella data «i sats vanno
  a chi compra» non si può più fare.
  3) IL MODERATORE DECIDE (`admin-take-dispute`, poi `admin-settle` =
  i sats a chi compra, o `admin-cancel` = i sats a chi vende): dalla
  sezione dell'app, quando ci sarà. La chiave è UNA PER MODERATORE E
  VIVE SOLO SUL SUO TELEFONO (decisione di Andrea, 28 set 2026: mai sul
  VPS, mai la nsec del nodo portata fuori); sul nodo la aggiunge Andrea
  con `admin-add-solver`, firmato dalla chiave del nodo SENZA farla
  uscire da lì (`npub` = legge e decide, `npub:read` = legge e parla
  ma non decide). La procedura per aggiungerla si scrive col resto
  della sezione.
  ⚠️ `lncli cancelinvoice <hash>` A MANO È SOLO EMERGENZA: restituisce
  i sats a chi vende scavalcando mostrod, che resta con l'ordine in
  `dispute` e il libro storto.
  L'ALLARME «chiusa SENZA una decisione a registro»: mostrod ha
  raccontato una chiusura da moderatore (`released` o `canceled` di
  `mostro` col dettaglio `admin`) e nel registro del server la
  decisione non c'è — qualcuno ha usato una chiave di moderatore senza
  passare dall'app. Finché nessuna chiave è stata aggiunta al nodo può
  venire solo dalla chiave del NODO. COSA FARE: 1) chiedere all'altro
  moderatore se è stato lui; 2) se no, sul nodo guardare chi ha preso
  la disputa (`solver` nella prima query di questa voce) e togliergli
  il ruolo. ⚠️ Un comando per TOGLIERE un solver nel protocollo non
  l'ho trovato (la pagina dice che «si possono togliere» e non dice
  come): la strada letta sul codice, MAI PROVATA, è una riga nel
  database del nodo — copia prima, con l'API `backup` di sqlite e non
  con un `cp` a caldo — `UPDATE users SET is_solver=0 WHERE pubkey='<chiave esadecimale>' AND is_solver=1;`
  (mostrod cerca il solver nel database a ogni richiesta). Si prova su
  una chiave usa-e-getta PRIMA di averne bisogno.
  IL REGISTRO, sul VPS: `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT ordine, gesto, tg_id, datetime(quando,'unixepoch','localtime'), esito, motivo FROM p2p_dispute_registro ORDER BY id DESC LIMIT 20\")]"`
  e le dispute: `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT ordine, stato, aperta_da, compratore, venditore, presa_da, esito, chiusa_da, datetime(aperta_il,'unixepoch','localtime') FROM p2p_dispute ORDER BY aperta_il DESC LIMIT 20\")]"`.
  ⚠️ UNA DISPUTA APERTA PRIMA DI QUESTO DEPLOY NON HA LA SUA RIGA (la
  riga nasce all'evento `dispute-opened`): la sua chiusura non arriva
  ai moderatori, e non è un guasto.
- LA MODERAZIONE DELLE DISPUTE P2P: LA PROCEDURA (29 set 2026). Dal
  deploy della sezione «⚖️ Moderazione P2P» la voce qui sopra («LE
  DISPUTE P2P») resta vera per le letture sul nodo e per i tre modi di
  chiudere; cade la sua riga «la sezione nell'app non c'è ancora».
  DOVE STA: in cima a «I miei scambi», una striscia che vede SOLO chi è
  moderatore (`ADMIN_IDS`), col numero delle dispute aperte; dal Profilo,
  Amministrazione → «⚖️ Moderazione P2P».
  PRIMA VOLTA, PER OGNI MODERATORE (una volta per dispositivo):
  1) nella pagina, «🔑 Crea la mia chiave di moderatore». La chiave
  nasce sul telefono e non lo lascia: al server va la sola chiave
  pubblica, che compare in fondo alla pagina sotto «Le chiavi dei
  moderatori» (`npub1…`, col suo «Copia»). Gli altri moderatori ricevono
  un avviso.
  1b) SUBITO DOPO, LA COPIA (dal 1 ott 2026): «📤 Esporta la chiave
  (cifrata)», una password di almeno 8 caratteri scritta due volte, e il
  testo `ncryptsec1…` che esce si copia nel gestore di password (o si
  scarica come file; dentro Telegram il file può non scaricarsi, il
  testo sì). La password NON si recupera: senza, la copia non vale
  niente. Senza copia, telefono perso = chiave nuova, e si riparte dal
  punto 2. SU UN TELEFONO NUOVO: «📥 Importa una chiave», si incolla il
  testo (o si carica il file) e la password; se la chiave è quella già
  registrata il nodo la riconosce e non c'è altro da fare; se sul
  telefono c'è già una chiave diversa, o quella registrata è un'altra,
  l'app lo dice e chiede prima di sostituirla (una chiave sostituita
  ovunque va aggiunta al nodo come al punto 2, se non lo era già).
  2) ANDREA LA AGGIUNGE AL NODO. ⚠️ NON col messaggio `admin-add-solver`
  da `mostro-cli` sul nodo, ed è una scelta e non una scorciatoia: quel
  messaggio è firmato dalla chiave del nodo e parte verso i relay
  pubblici, e dalla shell dell'host partirebbe dall'IP del nodo — Tor lo
  attraversano i container, non l'host — cioè i relay vedrebbero la
  chiave del coordinator arrivare da `185.18.221.96`. È la correlazione
  che tutto il nodo è fatto per non produrre. Se un giorno si vorrà il
  messaggio vero, va da un container che esce SOLO dalla SOCKS di Tor:
  cantiere suo.
  QUEL CHE IL COMANDO FA, letto su `admin_add_solver.rs` di mostrod
  0.18.8, è UNA RIGA in `users` (`is_solver = 1`, `is_admin = 0`,
  `category = 2` = legge e decide; `1` sarebbe la sola lettura), e
  mostrod la rilegge dal database a ogni richiesta (`find_solver_pubkey`):
  la riga scritta a mano vale come il messaggio. FATTA COSÌ IL 30 SET
  2026 per le chiavi di Andrea e di Alan, tre comandi con `sudo` e
  `python3` (sul nodo `sqlite3` non c'è), su `/home/debian/nodo/mostro/mostro.db`:
  a) GUARDARE, in sola lettura (`mode=ro`): `PRAGMA table_info(users)`
  (le colonne vere: pubkey, is_admin, admin_password, is_solver,
  is_banned, category, last_trade_index, total_reviews, total_rating,
  last_rating, max_rating, min_rating, created_at), il conto degli
  utenti, chi è già solver o admin, e che le chiavi NUOVE non ci siano;
  b) COPIARE con l'API `backup` di sqlite, mai `cp` a caldo (WAL):
  `sudo python3 -c "import sqlite3; s=sqlite3.connect('/home/debian/nodo/mostro/mostro.db'); d=sqlite3.connect('/home/debian/nodo/mostro/mostro.db.prima-solver-<data>'); s.backup(d); d.close(); s.close()"`
  e rileggere la copia (stesso conto di utenti);
  c) SCRIVERE con la guardia, in una transazione `BEGIN IMMEDIATE`: prima
  `SELECT COUNT(*) FROM users WHERE pubkey IN (...)` deve dare 0, poi
  `INSERT INTO users(pubkey, is_admin, is_solver, is_banned, category, created_at) VALUES(?,0,1,0,2,?)`
  per ogni chiave (esadecimale, 64 caratteri: la npub si traduce PRIMA,
  col checksum verificato), e `commit` SOLO se `rowcount` totale è il
  numero di chiavi; altrimenti `rollback`. Poi la rilettura: `SELECT
  substr(pubkey,1,8),is_admin,is_solver,category,is_banned FROM users
  WHERE is_solver=1` → `(…, 0, 1, 2, 0)` per ognuna. Nessun riavvio.
  IL RITORNO INDIETRO: `DELETE FROM users WHERE pubkey=? AND is_solver=1`
  con commit a `rowcount == 1` (stessa guardia), oppure la copia rimessa
  al posto del database a mostrod FERMO. La copia va cancellata dopo la
  prima disputa di prova riuscita: è un database intero, con dentro le
  hold invoice.
  La chiave si aggiunge CON PIENI POTERI (`category = 2`): un moderatore
  in sola lettura (`category = 1`) prende e parla ma non decide, e per
  ora non ce ne sono (decisione di Andrea).
  3) la prova che è andata: il moderatore tocca «Prendi la disputa» su
  una disputa di prova. Se la chiave non è sul nodo l'app risponde «la
  tua chiave di moderatore non è ancora stata aggiunta al nodo».
  QUANDO ARRIVA UNA DISPUTA: 1) l'avviso su Telegram dice ordine, parti,
  importo, metodo e chi l'ha aperta; 2) nella pagina si apre la disputa e
  si guarda QUANDO SCADE LA GARANZIA — dopo quella data i sats tornano a
  chi vende da soli e «a chi compra» non si può più decidere; 3) «Prendi
  la disputa»: le due parti vengono avvisate (Telegram e app) e da quel
  momento possono scrivere al moderatore; 4) si parla con TUTT'E DUE, un
  canale a testa (uno non legge l'altro), e si chiede quel che hanno:
  ora del pagamento, nome di chi ha pagato, numero della ricevuta. SOLO
  TESTO: le foto non passano, e un link a una foto è una dichiarazione,
  non una prova; 5) si scrive il MOTIVO (almeno 20 caratteri: resta nel
  registro col nome) e si tocca uno dei due gesti, «I sats vanno a chi
  compra» o «I sats tornano a chi vende», con le sue due conferme.
  LE REGOLE: non si decide una disputa di cui si è parte (l'app e il
  server lo impediscono: la prende l'altro moderatore); non si decide
  senza aver sentito tutt'e due, salvo che una non risponda entro un
  tempo detto prima nella chat; nel dubbio e senza prove, vale la regola
  di casa — i sats tornano a chi li ha bloccati — e si scrive nel motivo;
  se l'app dice «la disputa presa NON è di questo ordine» CI SI FERMA e
  si avvisa Andrea.
  SE IL GESTO NON RIESCE: «Nessuna risposta» NON vuol dire «non fatto» —
  il coordinatore risponde via Tor e può tardare. Si aspetta un minuto,
  si tocca «↻ Aggiorna» e si guarda se la disputa è passata fra le
  chiuse; solo se è ancora «Presa» si riprova. Un «no» del coordinatore
  resta a registro (`non_riuscita`).
  TELEFONO PERSO, O MODERATORE CHE ESCE: la sua chiave si toglie dal
  nodo (vedi «L'ALLARME» nella voce qui sopra: la riga SQL è letta e mai
  provata), lui ne crea una nuova da un altro dispositivo, e Andrea la
  aggiunge. Le dispute che aveva preso le riprende la chiave del nodo
  (il coordinatore lo permette alla sola chiave del nodo).
  IL REGISTRO: la query è nella voce qui sopra. I gesti che ci finiscono:
  `aperta`, `id_dichiarato`, `id_diverso`, `chiave`, `presa_chiesta`,
  `presa`, `presa_fallita`, `decisione`, `non_riuscita`, `chiusa`,
  `allarme`. Le chiavi registrate:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT tg_id, chiave, datetime(creata,'unixepoch','localtime') FROM p2p_moderatori\")]"`
  COSA NON È PROVATO: tutto quel che parla col coordinatore VERO. I
  messaggi del moderatore sono costruiti sulle pagine del protocollo e
  provati contro un coordinatore finto; che mostrod 0.18.8-bar5 li
  accetti si vede solo con la prima disputa di prova presa e decisa da
  una chiave aggiunta al nodo. Fino ad allora la strada sicura per una
  disputa vera resta l'accordo fra le parti.

- IL CONTANTI DI PERSONA (30 set 2026; perché in CANTIERI, «Il contanti
  di persona nel P2P»). IL TETTO è `P2P_CONTANTI_MAX_EURO` e vale **250
  anche senza la riga nel config del VPS**: non serve aggiungere niente
  per il lancio. Per cambiarlo, la riga nel config (`P2P_CONTANTI_MAX_
  EURO = 200`, o `0` per spegnerlo) e `sudo systemctl restart barattolo`;
  il pannello «⚙️ Stato delle leve» dice il valore VIVO («Tetto contanti
  di persona (€)»). Sta SOTTO `P2P_MAX_EURO` quando quello è acceso.
  LA TABELLA `p2p_presenze` nasce da sola al primo riavvio (`CREATE
  TABLE IF NOT EXISTS`): niente migrazione a mano. Verifica in sola
  lettura: `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute(\"SELECT sql FROM sqlite_master WHERE name='p2p_presenze'\").fetchone()[0])"`.
  IN UNA DISPUTA SUL CONTANTI il moderatore legge la riga «🤝 Incontro
  confermato…» o «Nessuna prova d'incontro» nella card della disputa;
  la regola scritta in «Info P2P» è quella di Hodl Hodl: senza prova
  d'incontro i sats tornano a chi li ha bloccati, con la prova e nessun
  rilascio vanno a chi compra. Le due firme le ha già verificate il
  server; la posizione viene dal GPS dei telefoni e si può falsificare.
  Per guardare la riga dal VPS (sola lettura):
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); [print(*r, sep='|') for r in c.execute(\"SELECT ordine, ora_mostra, ora_legge, distanza_m, posizioni, posizioni_via, caricata_da FROM p2p_presenze ORDER BY quando DESC LIMIT 20\")]"`
  — le colonne `lat_*`/`lon_*`/`acc_*` e
  `prova` sono a NULL/vuote dopo la chiusura (o dopo quindici giorni,
  dalla scopa dell'orologio: riga «🧹 P2P: N prove d'incontro
  alleggerite o tolte» nel journal). Se una disputa si apre e la riga
  ha ancora le posizioni, quelle restano finché lo scambio non si
  chiude: è voluto, servono al moderatore.
  COSA NON È PROVATO sul VPS: la rotta col coordinatore vero (le due
  chiavi arrivano da `p2p_scambi`, che le scrive la patch 0007 agli
  eventi: se un evento si è perso, la rotta risponde 409 «non ha ancora
  detto le due chiavi» e i due telefoni devono riprovare dopo un
  minuto); lo scanner di Telegram e la fotocamera dell'APK su telefoni
  veri.
- LA SALITA A MOSTRO 0.19.0, immagine `mostro:v0.19.0-bar6` (preparata
  il 30 set 2026, ✅ FATTA SUL NODO IL 1 OTT 2026 con la cauzione — com'è
  andata, e cosa è cambiato strada facendo, sta nella voce «LA SALITA A
  MOSTRO 0.19.0, COM'È ANDATA», più sotto; il perché e i numeri stanno in
  `docs/STUDIO-MOSTRO-0190-2026-09-30.md`). Le sette
  patch del fork stanno in `deploy/mostro/` RIFATTE sopra la `v0.19.0`
  (commit `d53e41d`), ognuna col suo patcher a `--secco`; la sola
  differenza dalla `-bar5` è una parola nell'ancora 11 della 0007
  (`Released`, upstream `#967`). ⚠️ NIENTE È STATO COMPILATO SUL PC: il
  primo `cargo` è il punto 4. ✅ IL ROLLBACK TORNA A ESSERE UNA RIGA: la
  0.19.0 non porta migrazioni (15 file, gli stessi della `-bar5`). Per
  il resto è la liturgia della `-bar5`, un comando alla volta.
  FASE 1 — PRIMA DI TOCCARE IL NODO, in sola lettura, tutt'e quattro:
  a) `grep -n "transport\|hold_invoice_expiration_window" ~/nodo/mostro/settings.toml`
  — `transport` o non c'è o dice `"nip44"` (⚠️ `"gift-wrap"` = la 0.19.0
  NON PARTE: si corregge prima, e sarebbe una sorpresa da capire);
  `hold_invoice_expiration_window` deve essere > 0 (300 dal template:
  a 0 la 0.19.0 non parte).
  b) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` → `mostro:v0.18.8-bar5`.
  c) `cd ~/nodo/mostro-src && git status && git log -1 --oneline` →
  `barattolo/v0.18.8`, albero pulito. Se non è pulito NON si va avanti.
  d) IL LIBRO FERMO, ed è il controllo che si rifà ANCHE al punto 8 un
  attimo prima dell'`up -d`, perché fra il punto 0 e il punto 8 passano
  i minuti della build e qualcuno può aver preso un ordine (sul nodo
  `sqlite3` non c'è: `python3` in sola lettura, `mode=ro`, la stessa
  strada della procedura del solver):
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall())"`
  Devono comparire SOLO `pending` e stati finali (`success`, `canceled`,
  `expired`, `canceled-by-admin`, `cooperatively-canceled`,
  `settled-by-admin`, `completed-by-admin`). Uno solo fra
  `waiting-payment`, `waiting-buyer-invoice`, `active`, `fiat-sent`,
  `settled-hold-invoice`, `in-progress` o `dispute` = c'è uno scambio
  in corso: si ASPETTA che finisca (un riavvio a metà presa fa scadere
  i 900 s a qualcuno, e una hold in volo la si lascia dov'è). Un
  `pending` va bene: è il libro, che riparte com'è.
  FASE 3 — LA LITURGIA, a libro fermo:
  0) IL BACKUP DEL DATABASE, anche se non ci sono migrazioni (costa un
  secondo e copre il residuo delle dispute, punto 9):
  `cp ~/nodo/mostro/mostro.db ~/nodo/mostro/mostro.db.prima-bar6`
  (il percorso è quello che il compose monta sotto `/config`:
  `docker inspect nodo-mostro-1 | grep -A3 Binds`).
  ⚠️ DAL 1 OTT 2026 LE PATCH SONO OTTO (la 0008: la cauzione di chi
  prende, solo per «Contanti» — CANTIERI, «La cauzione di chi prende»):
  `patch-000*.py` la porta gia', la stringa a secco e il commit stanno
  sotto la 0007, e nello STESSO riavvio si accende la cauzione nel
  `settings.toml` (punto 7-bis). Le righe che dicono «sette» valgono
  per le sette di prima.
  1) SUL PC, gli undici file al nodo, in una cartella NUOVA e FUORI da
  `mostro-src` (`ssh UTENTE@NODO mkdir -p nodo/patch-bar6` prima):
  `scp deploy/mostro/patch-000*.py deploy/mostro/barattolo_fee.rs deploy/mostro/barattolo_eventi.rs UTENTE@NODO:nodo/patch-bar6/`
  Poi sul nodo `sha256sum ~/nodo/patch-bar6/barattolo_eventi.rs ~/nodo/patch-bar6/barattolo_fee.rs`
  contro gli stessi sul PC (`sha256sum` in Git Bash): devono combaciare.
  2) SUL NODO, il sorgente nuovo: `cd ~/nodo/mostro-src && git fetch --tags`
  e `git switch -c barattolo/v0.19.0 v0.19.0`; `git log -1 --oneline`
  deve dire `d53e41d chore: Release mostro version 0.19.0`.
  3) I SETTE PATCHER, in fila, ognuno PRIMA a secco e POI senza, con un
  commit ciascuno. A secco devono dire, nell'ordine: «A SECCO: 3
  sostituzioni in src/lnurl.rs», «2 sostituzioni in src/config/util.rs»,
  «3 sostituzioni in src/app/dev_fee.rs», «4 sostituzioni in 3 file»,
  «7 agganci in 6 file», «a secco: l'ancora c'e', UNA volta», «25 agganci
  in 13 file, tutte le ancore uniche, 13 azioni note» — le STESSE
  stringhe della `-bar5`, verificate sul PC il 30 set — e poi, per la
  0008, «A SECCO: 20 agganci in 10 file, tutte le ancore al loro conto,
  14 azioni note, i due moduli di test in coda» (verificata sul PC il
  1 ott). Un FERMO qualunque si incolla a Claude e non si tocca niente
  a mano.
  `python3 ~/nodo/patch-bar6/patch-0001-lnurl-tor-freddo.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0001-lnurl-tor-freddo.py && git add -A && git commit -m "lnurl: raise HTTP timeouts so Tor-routed coordinators can resolve LNURL"`
  `python3 ~/nodo/patch-bar6/patch-0002-dev-fee-zero.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0002-dev-fee-zero.py && git add -A && git commit -m "config: let dev_fee_percentage = 0 mean no dev fee, not an invalid value"`
  `python3 ~/nodo/patch-bar6/patch-0003-dev-fee-cappelli.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0003-dev-fee-cappelli.py && git add -A && git commit -m "dev fee: raise the resolution timeouts that cap LNURL below its own budget"`
  `python3 ~/nodo/patch-bar6/patch-0004-prezzo-mai-visto.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0004-prezzo-mai-visto.py && git add -A && git commit -m "order/take: answer PriceTooStale when no price is cached yet, instead of a silent internal error"`
  `python3 ~/nodo/patch-bar6/patch-0005-fee-per-parte.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0005-fee-per-parte.py && git add -A && git commit -m "fee: per-party fees, with the loyalty discount applied at the source"`
  `python3 ~/nodo/patch-bar6/patch-0006-perche-e-fallito.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0006-perche-e-fallito.py && git add -A && git commit -m "release: log why a payout has failed"`
  `python3 ~/nodo/patch-bar6/patch-0007-eventi-al-server.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0007-eventi-al-server.py && git add -A && git commit -m "events: tell the marketplace server about every order transition"`
  `python3 ~/nodo/patch-bar6/patch-0008-cauzione-solo-contanti.py --secco`
  `python3 ~/nodo/patch-bar6/patch-0008-cauzione-solo-contanti.py && git add -A && git commit -m "bond: apply the anti-abuse bond only to the payment methods the policy names"`
  Alla fine `git log --oneline v0.19.0..HEAD` deve dire OTTO righe, la
  0001 in fondo. (Strada equivalente: `git am ~/nodo/patch-bar6/000[1-8]-*.patch`
  con le otto `.patch` del repo copiate: stesso albero, verificato sul
  PC il 30 set per le sette e il 1 ott per l'ottava.)
  4) I TEST PRIMA DELLA BUILD VERA, il primo `cargo` di questo fork
  sulla 0.19.0 (il filtro della `-bar5` più `publish` e `spam_gate`,
  i due moduli che la 0.19.0 tocca di più):
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar6 .`
  `docker run --rm mostro-test:bar6 cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice barattolo_eventi app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle publish spam_gate barattolo_bond toml_only_payment_methods`
  (gli ultimi due sono i test della 0008: `barattolo_bond_methods` in
  `flow.rs`, `barattolo_bond_methods_tag` in `nip33.rs` e il toml in
  `config::types`; devono comparire fra i verdi, o la patch non e'
  entrata dove credeva).
  Si guardano `pre_claim_failures_by_class` fra i verdi di
  `barattolo_eventi`, e di upstream `release_action_closes_dispute` (o
  come si chiama il test che ora aspetta `Released`) in `app::release`,
  `transport_gift_wrap_refuses_to_start_with_a_clear_reason` in `config`
  e i test di `publish`. Se la build o i test si fermano, l'errore si
  incolla a Claude e si corregge NEL REPO; sul nodo
  `git checkout -- . && rm -f src/barattolo_fee.rs src/barattolo_eventi.rs`
  e si riparte dal tag (`git reset --hard v0.19.0`). Niente ritocchi a
  mano sul nodo.
  5) VERDI: `git format-patch v0.19.0..HEAD -o ~/nodo/patch-bar6/export`
  e le otto tornano sul PC con `scp`, in `deploy/mostro/`, coi nomi di
  sempre: `diff` contro quelle nel repo deve dire solo l'`index`, il
  `From` e la `Date` (i blob, gli hash e l'ora del commit), MAI una riga
  di codice — se ne dice una, il nodo ha un sorgente diverso dal repo e
  ci si ferma.
  6) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.19.0-bar6 .`
  — tag nuovo; `mostro:v0.18.8-bar5` resta sulla macchina.
  7) IL COMPOSE (`cd ~/nodo`, copia prima: `cp docker-compose.yml
  docker-compose.yml.prima-bar6`): la SOLA riga dell'immagine a
  `mostro:v0.19.0-bar6`. Le cinque variabili d'ambiente (tre della 0005,
  due della 0007) restano com'erano (una riga `transport = "nip44"` nel
  `settings.toml`, se c'è, la 0.19.0 la accetta).
  7-bis) LA CAUZIONE, NELLO STESSO RIAVVIO (1 ott 2026, decisione di
  Andrea: tarature 3%, pavimento 1.000 sats, `take`, timeout spento,
  finestra a 900, solo «Contanti»). PRIMA la copia:
  `cp ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-bar6`
  Poi si guarda com'è, in sola lettura:
  `grep -n "anti_abuse_bond\|hold_invoice_expiration_window\|^enabled\|^apply_to\|^amount_pct\|^base_amount_sats\|only_payment_methods" ~/nodo/mostro/settings.toml`
  — `[anti_abuse_bond]` deve essere COMMENTATA (o assente) e
  `hold_invoice_expiration_window = 300`. Due modifiche con `nano
  ~/nodo/mostro/settings.toml`: a) in `[lightning]`, la riga
  `hold_invoice_expiration_window = 300` diventa
  `hold_invoice_expiration_window = 900` — nella 0.19.0 quel numero è
  SOLO la scadenza della richiesta di cauzione di chi prende
  (`taker_bond_invoice_expiry`, #999, e nient'altro in tutto il daemon:
  verificato sui byte), e 5 minuti per pagare una hold con un wallet
  esterno sono pochi; b) in FONDO al file, un blocco NUOVO (non si
  scommenta il template: si scrive quel che serve), ⚠️ dopo l'ultima
  sezione e prima di un eventuale `[cashu]` commentato non conta:
  ```
  [anti_abuse_bond]
  enabled = true
  amount_pct = 0.03
  base_amount_sats = 1000
  apply_to = "take"
  slash_on_waiting_timeout = false
  only_payment_methods = ["Contanti"]
  ```
  (`slash_node_share_pct` 0.5, `payout_claim_window_days` 15 e
  `maker_bond_payment_timeout_seconds` 900 restano ai default del
  template; `only_payment_methods` è il campo della 0008 — sulla
  `-bar5` NON esiste, ed è la ragione per cui il rollback lo toglie.)
  Poi si rilegge: `grep -n -A7 "^\[anti_abuse_bond\]" ~/nodo/mostro/settings.toml`
  e `grep -n "hold_invoice_expiration_window" ~/nodo/mostro/settings.toml`
  → il blocco di sette righe e `= 900`. ⚠️ Il blocco vale dall'`up -d`
  del punto 8: fino ad allora gira ancora la `-bar5` senza cauzione.
  8) IL LIBRO FERMO, di nuovo (la query della fase 1, punto d): se è
  fermo, `docker compose up -d mostro` (`up -d`, non `restart`). Poi:
  `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` dice
  `-bar6`; `docker compose logs mostro --since 2m` dice `Transport:
  nip44 (protocol v2, event kind 14)`, «Settings correctly loaded»,
  NESSUNA riga di migrazione, `barattolo_eventi: order events go to …`
  e `barattolo_fee` col suo battito; il 38385 nuovo dice
  `mostro_version 0.19.0` e `protocol_version 2` («Info P2P» del
  client, o dai relay) — E LA CAUZIONE: `bond_enabled true`,
  `bond_apply_to take`, `bond_amount_pct 0.03`, `bond_base_amount_sats
  1000`, `bond_slash_on_waiting_timeout false`,
  `bond_only_payment_methods Contanti`, `hold_invoice_expiration_window
  900` («Info P2P» del client, che dal 1 ott dice la voce «La cauzione
  di chi prende» a leva accesa; o i tag del 38385 letti dai relay).
  8-bis) LA LEVA DEL CLIENT, SUL VPS, solo DOPO che il 38385 dice
  `bond_enabled true`: `nano /srv/barattolo/config.py`, la riga
  `P2P_CAUZIONE = True` (solo `True` accende), poi `sudo systemctl
  restart barattolo` e il pannello «⚙️ Stato delle leve» → «Cauzione nel
  contanti di persona: acceso». Il client crede solo a tutt'e due: la
  leva E il 38385. Accesa prima del nodo, promette una cifra che il nodo
  non chiede; il nodo acceso senza la leva chiede la cauzione lo stesso
  e il client la gestisce, senza dirla prima. Nel journal, per una settimana, nessun
  `no Mostro transport for event kind`: sarebbe un client v1 che bussa
  (non un guasto nostro, ma lo si sa).
  9) IL ROLLBACK, se serve: UNA riga — nel compose l'immagine a
  `mostro:v0.18.8-bar5` e `docker compose up -d mostro`; niente
  migrazioni da disfare. ⚠️ PIU' IL `settings.toml`, dal 1 ott 2026: la
  `-bar5` non conosce `only_payment_methods`, e con `enabled = true`
  chiederebbe la cauzione su OGNI metodo — quindi PRIMA dell'`up -d`
  si rimette la copia (`cp ~/nodo/mostro/settings.toml.prima-bar6
  ~/nodo/mostro/settings.toml`), oppure a mano `enabled = false` nel
  blocco. Le cauzioni gia' bloccate tornano da sole al loro ciclo (LND
  le cancella alla scadenza, o mostrod al primo giro utile); una
  bruciata in attesa di incasso (`pending-payout`) la paga la `-bar5`
  lo stesso, che il payout ce l'ha dalla 0.18.x. Sul VPS `P2P_CAUZIONE
  = False` e riavvio, o il client promette una cauzione che non c'è.
  ⚠️ `hold_invoice_expiration_window = 900` sulla `-bar5` non fa
  niente (configurazione morta), si puo' lasciare. PRIMA, in sola lettura, il residuo:
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute(\"SELECT id, status FROM disputes WHERE status='cooperatively-canceled'\").fetchall())"`
  `[]` = rollback secco. Righe = dispute FINALI chiuse dalle parti
  sulla 0.19.0, con uno stato che mostro-core 0.14.6 non sa leggere:
  i lettori di mostrod filtrano per stati aperti e non le toccano, si
  lascia la riga com'è e si guarda il log al primo giro; la copia del
  punto 0 si rimette SOLO se nel mezzo non c'è stato nient'altro (uno
  scambio fatto sulla 0.19.0 sparirebbe con lei). `-bar5` resta sulla
  macchina: un tag non si sovrascrive mai.
  LA PROVA A DUE TELEFONI, dopo: quella della `-bar5` (23,47 € col
  tabacchino, presa, garanzia, euro inviati, rilascio, il conto al
  satoshi, il journal del VPS con `taken`/`hold-invoice-paid`/
  `fiat-sent`/`released`/`success`), più le due cose NUOVE da guardare:
  gesto e risposta più svelti di prima (è il `#992`: un relay muto non
  costa più 10 s a evento), e — col client dal 30 set — un ordine
  ripreso su un dispositivo pulito che trova la controparte dal
  coordinatore (`chiave_peer` assente dal server, `peer` che arriva
  dalla restore: la riga del diario «ripresa» lo dice).
  E LA CAUZIONE, con `P2P_PROVA_IDS` chiusa ai due telefoni (1 ott
  2026): a) un ordine Revolut preso NON riceve `pay-bond-invoice` e va
  come oggi; b) un ordine «Contanti» pubblicato da A e preso da B: su B
  «🔐 Blocca la cauzione» col foglio aperto da solo (≈3% dei sats,
  almeno 1.000), sul libro l'ordine resta `pending` finché B non paga;
  B paga → il foglio si chiude, «Cauzione bloccata», e a A arriva la
  richiesta della garanzia (o il recapito, secondo il verso); poi lo
  scambio di sempre, e al «concluso» su B «Cauzione restituita» (il
  wallet di B la vede tornare); c) una richiesta LASCIATA SCADERE
  apposta (15 minuti): l'ordine è ancora nel libro, su B la frase «La
  cauzione non è stata bloccata in tempo» col «Riprendi l'ordine», e
  `lncli lookupinvoice <hash>` dice CANCELED; d) una disputa chiusa dal
  moderatore con la spunta «Brucia la cauzione di chi compra»: su B
  «Cauzione persa», su A la riga della metà con «Incassa», il Telegram a
  tutt'e due (`bond-slashed` nel journal del VPS), A dà la fattura →
  «Fattura ricevuta» → «Cauzione incassata»; e la stessa spunta su un
  lato SENZA cauzione deve tornare «su quel lato non c'è una cauzione da
  bruciare». Nel database del nodo, in sola lettura, `SELECT role, state,
  amount_sats, slashed_reason FROM bonds` racconta le stesse cose.
- IL TEMPO DI CHI PUBBLICA, SUL VPS: LA LEVA E LE LETTURE (12 ott 2026,
  cantiere `tempo-di-chi-pubblica`; il perché in CANTIERI, «Il tempo di
  chi pubblica»). La leva è `P2P_TEMPO_DI_CHI_PUBBLICA`, nel codice
  `False`. ACCESA mette in campo: la pausa degli ordini (ricorrente e una
  volta sola, dal profilo di scambio), il badge «⚡ risponde in fretta», i
  quattro avvisi a chi pubblica (subito, a 10 minuti, a un'ora, mezz'ora
  prima della scadenza) e il «non completato» a chi pubblica e non
  risponde. ⚠️ LE ORE NON STANNO QUI: le decide il nodo
  (`maker_expiration_seconds` nel suo `settings.toml`, patch 0011) e le
  annuncia nel 38385 — e IL «NON COMPLETATO» A CHI PUBBLICA CONTA SOLO SE
  IL NODO GLI DÀ PIÙ TEMPO DI CHI PRENDE. Quindi si può accendere PRIMA
  della `-bar8`: pausa, badge e avvisi funzionano, e coi trenta minuti di
  tutti resta la regola del 10 ott («mai a chi ha pubblicato»). Dopo la
  `-bar8` la penalità scatta da sola, senza toccare altro.
  PER ACCENDERLA: `nano /srv/barattolo/config.py`, in coda la riga
  `P2P_TEMPO_DI_CHI_PUBBLICA = True` (da AGGIUNGERE), poi
  `sudo systemctl restart barattolo` e il pannello «⚙️ Stato delle leve»
  → «Tempo di chi pubblica: pausa, badge, penalità: acceso». PER
  SPEGNERLA: la riga a `False` e riavvio. Le pause salvate restano in
  `p2p_pause` e smettono di contare (gli ordini tornano tutti visibili);
  gli esiti già scritti restano.
  LE LETTURE (in `python3`, sola lettura, dal collegamento accanto al
  codice: i due percorsi del database e il perché di questa forma
  stanno in testa a questo documento). Chi ha una pausa impostata:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute('SELECT tg_id, fasce, fuso, una_fino, aggiornato FROM p2p_pause').fetchall())"`
  Le mancate risposte di chi pubblica (`senza_risposta` è il fatto nudo,
  che toglie il badge; `mancato` e `scusato` col dettaglio che comincia
  per `maker-` sono la penalità e la sua scusa):
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute(\"SELECT esito, dettaglio, COUNT(*) FROM p2p_esiti WHERE dettaglio LIKE 'maker-%' GROUP BY 1,2\").fetchall())"`
  QUANTI SCAMBI HANNO UNA PARTE FUORI DA BARATTOLO (serve a decidere se la
  pausa va portata anche nel nodo): `parti_note` si legge ACCANTO
  all'esito, mai da sola — vale 0 anche per gli ordini scaduti o
  ritirati senza una presa e per i giri precedenti di un ordine tornato
  nel libro, che parti non ne hanno:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute('SELECT esito, parti_note, COUNT(*) FROM p2p_conti GROUP BY 1,2 ORDER BY 1,2').fetchall())"`
  Contano le righe `completato`: con `parti_note` 2 tutt'e due di
  Barattolo, con 1 una sola, con 0 nessuna delle due.
  Nel journal: `journalctl -u barattolo --since today | grep "Reputazione P2P"`
  — ogni mancata risposta lascia la sua riga, anche quando NON si conta
  (in pausa, non dei nostri, già contata su quell'ordine, senza il tempo
  lungo), col perché.
- IL PARACADUTE, SUL VPS: LA LEVA E LE LETTURE (13 ott 2026, cantiere
  `paracadute`; il perché in CANTIERI, «Il paracadute»). La leva è
  `P2P_PARACADUTE`, nel codice `False`. ACCESA: nel foglio che pubblica
  un ordine P2P compare «🪂 Paracadute» (Spento · 5% · 10% · 20%); se il
  prezzo di BTC si muove oltre la soglia prima che l'ordine venga preso,
  il server lo toglie dal libro di Barattolo, avvisa chi l'aveva
  pubblicato, e il SUO telefono lo annulla alla prima apertura. Mai sugli
  ordini Barattozon. NON DIPENDE DALLE ALTRE LEVE DEL P2P né dal nodo:
  si può accendere prima o dopo la `-bar8`.
  ⚠️ VIVE DEL CAMBIO DI SFONDO: il paracadute legge il cambio che il
  server rinfresca da solo ogni `CAMBIO_RINFRESCO_S` (60 di serie). Se
  sul VPS quella riga fosse a 0 il paracadute non riceverebbe letture e
  resterebbe sempre chiuso: prima di accendere,
  `grep -n "CAMBIO_RINFRESCO_S" /srv/barattolo/config.py` (nessuna riga =
  60, va bene).
  ✅ ACCESA PER TUTTI dalla sera del 13 ott 2026 (decisione di Andrea,
  dopo la prova dal vivo col coordinatore vero: CANTIERI, «la prova dal
  vivo col coordinatore vero»). La riga nel config del VPS C'È GIÀ
  (`grep -n "^P2P_PARACADUTE" /srv/barattolo/config.py`): si cambia
  quella, non se ne aggiunge una seconda.
  PER ACCENDERLA: la copia (`sudo cp -p /srv/barattolo/config.py
  /root/config.py.prima-di-…`), poi
  `sudo sed -i 's/^P2P_PARACADUTE = False$/P2P_PARACADUTE = True/' /srv/barattolo/config.py`,
  la rilettura col `grep` qui sopra, il controllo `ast` di sempre,
  `sudo systemctl restart barattolo` e il pannello «⚙️ Stato delle leve»
  → «Paracadute degli ordini P2P: acceso». PER SPEGNERLA: lo stesso
  `sed` coi due valori scambiati, e riavvio. Le righe restano in `p2p_paracadute` e smettono di
  contare: gli ordini già usciti col paracadute tornano a vedersi, e i
  telefoni non annullano più niente.
  LE LETTURE (in `python3`, sola lettura). I paracadute, dal più nuovo:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute('SELECT ordine, tg_id, soglia, partenza, oltre, aperto, arrivo, superato FROM p2p_paracadute ORDER BY creato DESC LIMIT 20').fetchall())"`
  (`aperto` > 0 = si è aperto a quell'ora, a quel prezzo d'`arrivo`;
  `superato` > 0 = un'apertura disfatta perché l'ordine risultava preso
  un attimo prima). ⚠️ `aperto = 0` VUOL DIRE «MAI APERTO», NON «ARMATO»
  (13 ott 2026, sera, dalla prova di Andrea): la riga resta in tabella
  anche quando l'ordine è stato annullato, preso, concluso o è scaduto,
  e da lì non si apre più e non avvisa nessuno — il giro guarda solo gli
  ordini che il libro dà `pending`, senza una presa in corso e senza
  un'uscita già raccontata da mostrod, e salta il minuto in cui il libro
  non è stato letto. Per sapere se una riga è ancora viva si guarda lo
  stato dell'ordine, non `aperto`:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute('SELECT p.ordine, p.soglia, p.aperto, o.stato FROM p2p_paracadute p JOIN p2p_ordini o ON o.ordine=p.ordine ORDER BY p.creato DESC LIMIT 20').fetchall())"`
  Quelli aperti che per il libro sono ancora `pending`
  — cioè il telefono non ha ancora firmato il `cancel`:
  `python3 -c "import sqlite3; c=sqlite3.connect('file:/srv/barattolo/satmarket.db?mode=ro', uri=True); print(c.execute(\"SELECT p.ordine, p.tg_id, p.aperto FROM p2p_paracadute p JOIN p2p_ordini o ON o.ordine=p.ordine WHERE p.aperto>0 AND o.stato='pending'\").fetchall())"`
  PER PROVARLO DAL VIVO SENZA ASPETTARE IL MERCATO (fatto il 13 ott
  2026): un ordine proprio col paracadute, lasciato nel libro; si
  RILEGGE che sia `pending` con la lettura qui sopra (su uno `canceled`
  non succede niente, ed è giusto); a Barattolo chiuso si alza la sua
  `partenza` del 7% — UNA riga sola, quella dell'ordine, e solo se
  `aperto` è ancora 0. È una SCRITTURA sul database di produzione, e
  per questo qui NON c'è il comando: non è una procedura di sempre,
  si fa con Andrea, avvisando prima, nella forma delle altre scritture
  (dal file vero in `dati/`, da `barattolo`, col conto delle righe
  cambiate, che
  deve dire 1). Entro due o tre minuti arriva l'avviso su Telegram;
  alla riapertura dell'app il telefono annulla, e il registro di mostrod
  sul nodo lo dice: `docker logs --since 3h nodo-mostro-1 2>&1 | grep <prime otto cifre>`
  → «updated Nostr new Status: canceled» e «barattolo_eventi: … canceled:
  delivered (HTTP 200)».
  Nel journal (⚠️ il VPS segna l'ora UTC: `--since today`, non «40 min
  ago»): `journalctl -u barattolo --since today | grep "Paracadute P2P"`
  — «🪂 Paracadute P2P: … aperto al 5% (da … a … €/BTC): avviso …» a ogni
  apertura, «… preso a paracadute gia' aperto» e «… un attimo PRIMA
  dell'apertura» alle prese, «⚠️ Paracadute P2P: battito saltato» se il
  giro inciampa (il prossimo arriva lo stesso).

- LA SALITA ALLA 0.20.2, immagine `mostro:v0.20.2-bar9` (preparata il 29
  ott 2026, cantiere `mostro-0202`, decisione di Andrea: «fork intero
  sulla 0.20.2»; ✅ FATTA SUL NODO il 30 ott 2026, in servizio dalle
  07:37 UTC, com'è andata in fondo a questa voce, «COM'È ANDATA SUL
  NODO». Era scritta così: build e riavvio solo con l'ok esplicito di
  Andrea, un comando alla volta, a libro fermo). È la prima
  salita di VERSIONE dalla 0.19.0 (30 set): sei versioni di upstream in
  un colpo (0.19.1 → 0.20.2, tag del 28 ott, `fe2a905`), e il fork è
  RIFATTO DA CAPO sul tag nuovo coi patcher del repo — quindi porta anche
  i tre ritocchi dell'audit del 1 ott (M6, M4, B6) che il nodo non ha mai
  avuto. Cosa cambia per noi (CANTIERI, «Mostro 0.20.2», e NODO-MOSTRO,
  «LA 0.20.2 PREPARATA»): la cura #910 (il venditore che paga la
  garanzia e annulla un istante dopo non si riprende più i sats mentre al
  compratore arriva «pagato»), #923, #1095, #1090, la manutenzione da
  sola se LND resta indietro (#1065, sezione `[health]`, di serie
  accesa), l'evento di salute kind 38389 ogni 60 s, e la base per gli
  USDT (`[price.providers.pegged]`, SPENTA). Il protocollo resta il 2.
  ⚠️ TRE COSE CHE LA 0.19.0 NON AVEVA:
  a) `[anti_abuse_bond] bond_cltv_delta` è OBBLIGATORIA con la cauzione
  accesa: deve stare sopra `hold_invoice_cltv_delta + 144` e al più 864
  (col nostro 576: fra 721 e 864), sennò `mostrod` NON PARTE (#1085).
  Si mette 744: il minimo più 24 blocchi di margine — è il CLTV delle
  hold della cauzione, e più è corto meno a lungo resta bloccato il
  wallet di chi prende se qualcosa va storto (prima era 576, lo stesso
  della garanzia). Lo decide Andrea.
  b) UNDICI MIGRAZIONI al database (`payer_history`, `order_success_at`,
  le quattro della reputazione, `dev_fee_retry_backoff`,
  `bond_payout_sent_at`, `order_hold_settled_at`, `health_query_indexes`,
  `orders_master_buyer_pubkey_index`): `_sqlx_migrations` passa da 15 a
  26 righe. IL RITORNO ALLA `-bar8` VUOLE LA COPIA DEL DATABASE DI PRIMA
  (la `-bar8` rifiuta un database con migrazioni che non conosce), e gli
  ordini nati dopo il cambio si perdono: per questo la prova si fa
  SUBITO dopo.
  c) `BARATTOLO_EVENTI_SEGRETO` nel compose: col fork nuovo (M6) senza
  quella variabile gli eventi al server si SPENGONO, senza ripiego sul
  segreto dello sconto. Si guarda PRIMA (fase 1, e).
  NON C'È UN «PRIMA IL SERVER»: il VPS non deve cambiare niente per
  questa salita (il 38385 ha gli stessi tag, più `escrow_mode` e
  `escrow_deadline_margin_blocks`; il 38389 il server non lo legge).
  ✅ COMPILATA E PROVATA NEL CLOUD il 29 ott (`cargo` c'è): i numeri in
  fondo, «COM'È ANDATA NEL CLOUD». Sul nodo i test si rifanno lo stesso
  (fase 3, punto 3) e devono dire gli stessi numeri.
  Host, in cima a tutto: `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1937.lnvps.cloud`
  FASE 1 — IN SOLA LETTURA (`cd ~/nodo`), tutte e sei:
  a) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1`
  → `mostro:v0.19.0-bar8`.
  b) `git -C ~/nodo/mostro-src status --short | wc -l && git -C ~/nodo/mostro-src log --oneline v0.19.0..HEAD | wc -l`
  → `0` e `11` (albero pulito, undici commit sopra la 0.19.0). Se non è
  pulito NON si va avanti.
  c) IL LIBRO FERMO (`mode=ro`):
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall(), c.execute('SELECT COUNT(*) FROM _sqlx_migrations').fetchone())"`
  Devono comparire SOLO `pending` e stati finali, e `(15,)` migrazioni;
  uno fra `waiting-payment`, `waiting-buyer-invoice`,
  `waiting-taker-bond`, `active`, `fiat-sent`, `settled-hold-invoice`,
  `in-progress` o `dispute` = c'è uno scambio in corso: si ASPETTA.
  d) IL `settings.toml`, le righe che contano e le sezioni:
  `grep -n -E "^hold_invoice_cltv_delta|^escrow_deadline_margin_blocks|^bond_cltv_delta|^expiration_seconds|^maker_expiration_seconds|^maker_timeout_limit|^fiat_currencies_accepted|^\[" ~/nodo/mostro/settings.toml`
  → `576`, `24`, NESSUNA `bond_cltv_delta`, `1800`, `10800`, `2`,
  `['EUR']`, e `[anti_abuse_bond]` come ULTIMA sezione non commentata
  (la riga nuova si accoda in fondo al file: se dopo c'è un'altra
  sezione viva, si ferma e si chiede a Claude come metterla). `[cashu]`
  deve essere assente o commentata (la 0.20.2 ha rinominato `mint_url`
  in `mint_urls` e quella sezione rifiuta le chiavi che non conosce).
  e) IL SEGRETO DEGLI EVENTI, solo il conto: `grep -c "BARATTOLO_EVENTI_SEGRETO" ~/nodo/docker-compose.yml`
  → `1`. Se è `0` ci si ferma: va aggiunta al compose (con copia prima)
  uguale a `P2P_EVENTI_SEGRETO` del VPS, e si chiede a Claude i comandi.
  Che sia UGUALE a quella del VPS si vede senza stamparla, con otto
  lettere di impronta da confrontare a occhio — NODO:
  `grep -o "BARATTOLO_EVENTI_SEGRETO=.*" ~/nodo/docker-compose.yml | head -1 | cut -d= -f2- | tr -cd 'A-Za-z0-9_-' | sha256sum | cut -c1-8`
  e VPS (`ssh root@46.62.162.103`):
  `grep "^P2P_EVENTI_SEGRETO" /srv/barattolo/config.py | cut -d= -f2- | tr -cd 'A-Za-z0-9_-' | sha256sum | cut -c1-8`
  → le stesse otto lettere (il 29 ott: `12b649c7` da tutt'e due le
  parti). Il `tr -cd` tiene SOLO le lettere del segreto e butta apici,
  spazi e a capo: la prima stesura toglieva `' "\x27\n'` e dava due
  impronte diverse con lo stesso segreto, perché `tr` non legge `\x27`
  come un apice ma come le quattro lettere `\`, `x`, `2`, `7` — e le
  toglieva dal segreto. Se le otto lettere sono diverse, gli eventi non
  arriverebbero già oggi, e si guarda PRIMA di andare avanti.
  f) IL DISCO: `df -h / && docker system df` → almeno 6 GB liberi (la
  cucina della build ne prende 3; le immagini `mostro-test:bar2`…`bar8`
  si possono togliere PRIMA, `docker rmi mostro-test:barN` una per una,
  dopo averle contate con `docker images | grep mostro`: le immagini
  `mostro:v0.19.0-bar7` e `-bar8` NON si toccano, sono il ritorno).
  FASE 2 — IL BACKUP (costa un secondo), tre copie `.prima-0202`:
  `sudo python3 -c "import sqlite3; s=sqlite3.connect('/home/debian/nodo/mostro/mostro.db'); d=sqlite3.connect('/home/debian/nodo/mostro/mostro.db.prima-0202'); s.backup(d); print(d.execute('SELECT COUNT(*) FROM orders').fetchone(), s.execute('SELECT COUNT(*) FROM orders').fetchone())" && sudo chown --reference=/home/debian/nodo/mostro/mostro.db /home/debian/nodo/mostro/mostro.db.prima-0202 && sudo chmod 600 /home/debian/nodo/mostro/mostro.db.prima-0202 && ls -l /home/debian/nodo/mostro/mostro.db*`
  (l'API di sqlite e non `cp` su un file vivo — lezione della `-bar8`;
  i due conti devono essere uguali, e la copia con lo STESSO
  proprietario del vivo, così il ritorno la rimette senza chown).
  `cp -p ~/nodo/docker-compose.yml ~/nodo/docker-compose.yml.prima-0202`
  `cp -p ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-0202`
  FASE 3 — LA BUILD:
  1) SUL PC (PowerShell, dentro il repo sulla punta di `develop` o di
  `main` che porta questo cantiere), le undici `.patch` al nodo PRESE DA
  GIT, non dalla cartella di lavoro (dove i patcher escono CRLF — qui
  servono solo le `.patch`, LF):
  `git archive HEAD deploy/mostro --format=tar -o $env:TEMP\mostro-0202.tar`
  `scp -i $env:USERPROFILE\.ssh\lnvps $env:TEMP\mostro-0202.tar debian@vm-1937.lnvps.cloud:`
  SUL NODO: `mkdir -p ~/nodo/patch-0202 && tar xf ~/mostro-0202.tar -C ~/nodo/patch-0202 --strip-components=2 && ls ~/nodo/patch-0202/*.patch | wc -l`
  → `11`.
  2) SUL NODO, il tag nuovo e le undici patch con `git am` (è la strada
  di «RICOSTRUIRE DA ZERO» del README del fork: i patcher sono già
  girati nel cloud su questo stesso tag, e l'albero è noto):
  `cd ~/nodo/mostro-src && git fetch --tags origin && git switch -c barattolo/v0.20.2 v0.20.2`
  → `HEAD is now at fe2a905` (il branch `barattolo/v0.19.0` RESTA: è
  il ritorno del sorgente).
  `git am ~/nodo/patch-0202/00*.patch && git log --oneline v0.20.2..HEAD | wc -l && git rev-parse HEAD^{tree}`
  → `11` e `16734181e552e552f54b0c18c5ce2381764e67fe`: lo STESSO albero
  del cloud, byte per byte (è il controllo che la `-bar8` faceva con il
  `diff` delle `.patch`: qui lo fa git). Un `git am` che si ferma si
  incolla a Claude e si fa `git am --abort`.
  3) I TEST PRIMA DELLA BUILD VERA, in DUE lanci come per la `-bar7` e
  la `-bar8` (una prova di upstream legge una globale):
  `docker build -f docker/Dockerfile --target builder -t mostro-test:0202 .`
  `docker run --rm mostro-test:0202 cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice barattolo_eventi app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle publish spam_gate barattolo_bond toml_only_payment_methods barattolo_tempo nip33 find_order_by_seconds a_dispute_the_daemon_opens`
  → `730 passed; 0 failed; 1 ignored` (l'ignorata è di upstream,
  `lnurl_get_reaches_the_pinned_host_in_a_proxied_env`, che gira solo
  dentro un'altra prova). Fra i verdi le 48 prove nostre
  (`barattolo_fee`, `barattolo_eventi`, `barattolo_bond*`,
  `barattolo_tempo`), le tredici nominate dalla liturgia della `-bar8`
  (gli otto di `barattolo_tempo::tests::`, i quattro
  `reconfirm_timeout_eligibility_…`, l'unica `find_order_by_seconds…`,
  `status_tags_map_lifecycle_statuses_to_nip69_buckets`,
  `a_dispute_the_daemon_opens_is_mostros_and_says_why` e le tre
  `escrow_deadline_…` dello scheduler) e `dev_fee_zero_is_accepted_as_opt_out`.
  `docker run --rm mostro-test:0202 cargo test --release -- util::tests::`
  → `90 passed; 0 failed`.
  Numeri diversi o una rossa: l'errore si incolla a Claude, niente
  ritocchi a mano; il sorgente torna con `git switch barattolo/v0.19.0`.
  4) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.20.2-bar9 .`
  — tag nuovo; la `-bar8` resta sulla macchina. Poi
  `docker run --rm --entrypoint sh mostro:v0.20.2-bar9 -c "grep -c maker_timeout_limit /usr/local/bin/mostrod; grep -c bond_cltv_delta /usr/local/bin/mostrod"`
  → due numeri sopra zero (la 0011 nostra e la #1085 di upstream, tutt'e
  due dentro il binario).
  5) I DUE FILE DELL'ANDATA, preparati e letti PRIMA del cambio (niente
  editor):
  `cd ~/nodo && sed 's#mostro:v0.19.0-bar8#mostro:v0.20.2-bar9#' docker-compose.yml > docker-compose.yml.0202 && diff docker-compose.yml docker-compose.yml.0202; docker compose -f docker-compose.yml.0202 config -q && echo compose-ok`
  → UNA riga cambiata (l'immagine) e `compose-ok`.
  `cp -p ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.0202 && printf '# Barattolo, 29 ott 2026 (0.20.2, #1085): CLTV delle hold della cauzione, fra 721 e 864 col nostro hold_invoice_cltv_delta = 576.\nbond_cltv_delta = 744\n' >> ~/nodo/mostro/settings.toml.0202 && diff ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.0202; python3 -c "import tomllib; d=tomllib.load(open('/home/debian/nodo/mostro/settings.toml.0202','rb')); print(d['anti_abuse_bond']['bond_cltv_delta'], d['lightning']['hold_invoice_cltv_delta'], d['lightning']['escrow_deadline_margin_blocks'], d['mostro']['expiration_seconds'], d['mostro']['maker_expiration_seconds'])"`
  → due righe in più in fondo, e `744 576 24 1800 10800`: la riga nuova
  è caduta dentro `[anti_abuse_bond]` (se `tomllib` la mette altrove, o
  manca `python3`, ci si ferma e si chiede).
  FASE 4 — IL CAMBIO, UN COMANDO: conta gli scambi aperti e, se non sono
  zero, non tocca niente; se sono zero mette i due file e riavvia il
  solo container Mostro (`up -d`, non `restart`: cambia l'immagine):
  `cd ~/nodo && n=$(sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute(\"SELECT COUNT(*) FROM orders WHERE status IN ('waiting-payment','waiting-buyer-invoice','waiting-taker-bond','active','fiat-sent','settled-hold-invoice','in-progress','dispute')\").fetchone()[0])") && echo "scambi aperti: $n" && [ "$n" = 0 ] && date -u && cp -p docker-compose.yml.0202 docker-compose.yml && cp -p mostro/settings.toml.0202 mostro/settings.toml && docker compose up -d mostro && date -u`
  Il libro è fermo fra le due date (la `-bar8`: undici secondi; qui le
  migrazioni aggiungono qualche secondo).
  IL CONTROLLO, subito:
  `docker inspect --format '{{.Config.Image}}' nodo-mostro-1 && docker compose ps mostro`
  → `mostro:v0.20.2-bar9`, `running`.
  `docker compose logs mostro --since 3m | grep -i -E "migrat|Settings correctly|barattolo_|Transport|health|error|panic" | head -40`
  → «Settings correctly loaded!», `Transport: nip44`, `barattolo_fee` e
  `barattolo_eventi: order events go to …` (se quest'ultima manca, gli
  eventi sono spenti: fase 1, e), NESSUN `error`/`panic`; le migrazioni
  sqlx le applica in silenzio (il conto certo è `_sqlx_migrations`, qui
  sotto), e del `[health]` acceso di serie il registro non dice niente
  (scrive solo se è spento o se l'intervallo non è 60). Un `mostrod` che non
  parte dice il perché nel log (`bond_cltv_delta`, una chiave rifiutata,
  una migrazione): si incolla a Claude e si torna indietro (ROLLBACK).
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT COUNT(*) FROM _sqlx_migrations').fetchone())"`
  → `(26,)`.
  La versione dal binario che gira (la pagina «Info P2P» dell'app legge
  `mostro_version` ma NON la stampa): `docker compose exec mostro mostrod --version`
  → `mostro p2p 0.20.2`. Dall'app, i tempi come prima (30 minuti / 3
  ore) e la cauzione solo sui contanti. Sul VPS, nel journal, entro
  qualche minuto nessun errore nuovo del P2P:
  `journalctl -u barattolo --since "10 min ago" --no-pager | grep -i -E "p2p|mostro|evento" | grep -i -E "error|errore|traceback|403|401" | head`
  → vuoto. E QUI CI SI FERMA.
  FASE 5 — LA PROVA DAL VIVO, di Andrea con due account, SUBITO (il
  ritorno costa gli ordini nati dopo il cambio: meglio provare prima
  che ne nascano di altri). Uno scambio PICCOLO e INTERO, non solo
  pubblica-prendi-annulla come il 13 ott: A pubblica una vendita, B la
  prende, A paga la garanzia (è il passo spostato dalla 0.20.2: a B deve
  arrivare «sats in garanzia, manda gli euro», cioè l'evento
  `hold-invoice-paid` al server), B segna «ho pagato», A libera, B
  riceve. Nel registro del nodo ogni passo ha la sua riga
  `barattolo_eventi: order … delivered`; nel bot i soliti avvisi; e le
  fee per parte (0005) come prima. Poi un secondo giro pubblica-prendi e
  annullo da chi ha preso, come il 13 ott. Quel che la prova NON copre
  (e si dice): la scadenza vera di chi pubblica (FASE 5 della `-bar8`,
  ancora mai vista), la disputa automatica, la manutenzione da sola di
  LND, la cura #910 (vuole un venditore che annulla nel secondo esatto).
  FASE 6 — A `-bar9` IN SERVIZIO, tre righe di testo (si chiedono a
  Claude): il README del fork («IN SERVIZIO»), NODO-MOSTRO («LA 0.20.2
  PREPARATA» diventa «IN SERVIZIO», con l'ora del libro fermo), e la riga
  dell'immagine in `CLAUDE.md` (`mostro:v0.19.0-bar8` → `v0.20.2-bar9`,
  commit suo). E `docker rmi mostro-test:0202` quando si vuole il disco.
  ROLLBACK (solo se la `-bar9` non regge; vuole il database di prima):
  `cd ~/nodo && docker compose stop mostro && cp -p docker-compose.yml.prima-0202 docker-compose.yml && cp -p mostro/settings.toml.prima-0202 mostro/settings.toml && sudo cp -p mostro/mostro.db.prima-0202 mostro/mostro.db && docker compose up -d mostro && docker inspect --format '{{.Config.Image}}' nodo-mostro-1`
  → `-bar8`. Gli ordini pubblicati o presi DOPO il cambio non ci sono
  più (erano nel database nuovo): chi li aveva pubblicati li rifà. Il
  sorgente: `git -C ~/nodo/mostro-src switch barattolo/v0.19.0`. Sul VPS
  niente da toccare.
  COM'È ANDATA NEL CLOUD (29 ott 2026, cantiere `mostro-0202`; il nodo
  non è stato toccato): la `v0.20.2` pulita compila in 9 min 32 coi
  test; i patcher 0001-0006 entrano come sono, la 0007 si ferma
  sull'ancora di `flow.rs` (la stessa del 13 ott) e dietro di lei cinque
  ancore in tutto erano cambiate — riagganciate leggendo il diff di
  upstream (README del fork, in cima); il fork compila in 3 min 56
  senza un avviso DOPO una correzione: una riga di un test di
  `barattolo_eventi.rs` nel repo (`endpoint_from` a tre argomenti,
  avanzo della M6 del 1 ott) non compilava — mai vista perché quel file
  non era MAI stato compilato (il nodo gira il modulo di prima). Primo
  lancio dei test 730/0 (1 ignorata), secondo 90/0, la suite intera di
  `cargo` 1.991/0 (4 ignorate, di upstream), le 48 nostre cercate per
  nome; `git am` delle undici `.patch` su un clone pulito dà
  l'albero `16734181`. Controprova: la riga sbagliata rimessa fa rosso
  il compilatore (è così che si è vista).
  COM'È ANDATA SUL NODO (29-30 ott 2026, cantiere `mostro-bar9`, Andrea
  un comando alla volta, tutti incollati): la fase 1 tutta verde — il
  primo confronto delle impronte del segreto degli eventi era DIVERSO
  (`61081e84` contro `12b649c7`) per il difetto del comando del VPS
  (`\x27`, vedi fase 1, e), e la forma delle righe (64 lettere pulite da
  tutt'e due le parti) più l'impronta col `tr -cd` l'hanno chiuso. Fase
  2 e 3 il 29 ott sera: backup 378/378 alle 19:32; `git am` sul nodo con
  l'albero `16734181`, lo stesso del cloud; lo stadio `builder` in 856 s
  (14 minuti: scarica l'immagine `rust:1.94` e cuoce le dipendenze), i
  test 730/0/1 e 90/0 come nel cloud; l'immagine `-bar9` in 21 s (tutto
  dalla cache) con 6 e 9 nel binario; i due file `.0202` letti prima
  (`744 576 24 1800 10800`). Alle 20:06 UTC IL COMANDO DEL CAMBIO HA
  DETTO «scambi aperti: 1» E NON HA TOCCATO NIENTE: una vendita da
  347.801 sats (249 €, PayPal) pubblicata alle 19:48 e presa alle 19:51,
  `active`, nata mentre la cucina lavorava — il freno è fatto per
  questo, e Andrea ha scelto di riprendere il giorno dopo. Il 30 ott
  alle 07:36 il libro era fermo (385 ordini: quello scambio e altri tre
  chiusi `success`), la copia del database RIFATTA (385/385: quella
  della sera non aveva lo scambio, e il ritorno deve averlo), e il
  cambio alle 07:37:04 → 07:37:16 UTC: dodici secondi, come la `-bar8`
  (le migrazioni non si sono sentite). Il registro, nei tre minuti
  dopo: «Settings correctly loaded!», `barattolo_fee: per-party discount
  0.005 verified`, `barattolo_eventi: order events go to
  https://barattolo.store/api/p2p/evento`, `Transport: nip44 (protocol
  v2, event kind 14)`, `Published health event: status ok, seq 1` (il
  38389 nuovo), e un WARN `price: blockchain error: … blockchain.info/ticker:
  status 403 Forbidden`: uno dei quattro fornitori del prezzo rifiuta
  l'uscita Tor; gli altri tre rispondono e il prezzo c'è (da guardare se
  insiste: Cantieri, «Mostro 0.20.2», «NOTATO»). `_sqlx_migrations`
  `(26,)`; `mostrod --version` → `mostro p2p 0.20.2`; journal del VPS
  senza errori del P2P. Il sorgente sul nodo sta sul branch
  `barattolo/v0.20.2` (undici commit sopra `fe2a905`); `barattolo/v0.19.0`
  è rimasto com'era per il ritorno. L'immagine `mostro-test:0202` è
  ancora sulla macchina (`docker rmi mostro-test:0202` quando serve il
  disco: 26 GB liberi prima della salita). LA PROVA DAL VIVO (fase 5):
  alle 07:44 UTC Andrea, con due account, uno scambio intero — «funziona
  tutto, appena fatto scambio». Sette minuti dopo il cambio.
- LA SALITA ALLA `-bar8`, immagine `mostro:v0.19.0-bar8` (preparata il 12
  ott 2026, cantiere `tempo-di-chi-pubblica`; ✅ FATTA SUL NODO il 13 ott
  2026, cantiere `mostro-bar8`: in servizio dalle 11:36 UTC, e com'è
  andata sta in fondo a questa voce, «COM'È ANDATA». Era scritta così:
  build e riavvio del nodo solo con l'ok esplicito di Andrea, un comando
  alla volta, a libro fermo). Cosa cambia: la patch 0011 del fork — chi ha
  PUBBLICATO ha la sua finestra (`maker_expiration_seconds`), e se la
  lascia scadere l'ordine TORNA NEL LIBRO invece di morire, fino a
  `maker_timeout_limit` mancate risposte di fila; il 38385 annuncia i due
  numeri; l'evento al server per quel ritorno è `maker-republished`; e
  una vendita presa da un'altra app con la fattura nel take esce
  in-progress invece di restare `pending` (README del fork, «LA 0011»).
  E LA PATCH 0012, nella stessa immagine (richiesta di Andrea, 12 ott
  sera): la disputa che il coordinatore apre DA SOLO a ~92 ore dalla
  garanzia pagata (chi compra ha segnato il pagamento, nessuno ha
  liberato) adesso la racconta al server — `dispute-opened` di `mostro`,
  dettaglio `escrow-deadline` — e quindi arriva ai moderatori, alle due
  parti e alla card ⚖️ del cruscotto (README del fork, «LA 0012»).
  DUE RIGHE NUOVE nel `settings.toml` (punto 6-bis); NESSUNA migrazione:
  le mancate risposte stanno in una tabella a parte, fuori da sqlx.
  ⚠️ PRIMA IL SERVER, POI IL NODO: il VPS deve avere online il commit di
  questo cantiere PRIMA che il nodo cominci a dire `maker-republished` —
  il server di ieri la leggerebbe come un annullo, e a chi ha pubblicato
  direbbe «il tuo ordine è stato annullato» con l'ordine nel libro; e
  della disputa automatica (0012) direbbe alle due parti che l'ha aperta
  l'altro. Si
  guarda sul VPS: `git -C /srv/barattolo log -1 --oneline`. La LEVA del VPS
  invece non ha un ordine obbligato (voce qui sopra).
  ⚠️ MAI COMPILATA SUL PC (non c'è cargo): il patcher è girato a secco e
  per davvero su un clone del tag `v0.19.0` con le nove patch applicate
  (`git am`), il diff è stato riletto riga per riga, e niente altro —
  lo stesso per la 0012, sopra la 0011, e la sua `.patch` esportata si
  riapplica identica con `git am`. Il
  punto 3 qui sotto è la PRIMA compilazione: va guardato, e un errore si
  incolla a Claude senza ritocchi a mano.
  Host, in cima a tutto: `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1937.lnvps.cloud`
  FASE 1 — IN SOLA LETTURA, tutt'e tre:
  a) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1`
  → `mostro:v0.19.0-bar7`.
  b) `cd ~/nodo/mostro-src && git status && git log --oneline v0.19.0..HEAD`
  → branch `barattolo/v0.19.0`, albero PULITO, NOVE righe (la 0010 in
  cima: «bond: decide the taker bond on the payment method the taker
  declares»). Se non è pulito NON si va avanti.
  c) IL LIBRO FERMO (`mode=ro`):
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall())"`
  Devono comparire SOLO `pending` e stati finali; uno fra
  `waiting-payment`, `waiting-buyer-invoice`, `waiting-taker-bond`,
  `active`, `fiat-sent`, `settled-hold-invoice`, `in-progress` o
  `dispute` = c'è uno scambio in corso: si ASPETTA.
  FASE 2 — IL BACKUP (costa un secondo), tre copie:
  `cp ~/nodo/mostro/mostro.db ~/nodo/mostro/mostro.db.prima-bar8`
  `cp ~/nodo/docker-compose.yml ~/nodo/docker-compose.yml.prima-bar8`
  `cp ~/nodo/mostro/settings.toml ~/nodo/mostro/settings.toml.prima-bar8`
  FASE 3 — LA BUILD:
  1) SUL PC, i cinque file al nodo, in una cartella NUOVA e FUORI da
  `mostro-src` (il `.rs` deve stare ACCANTO al patcher):
  `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1937.lnvps.cloud mkdir -p nodo/patch-bar8`
  `scp -i $env:USERPROFILE\.ssh\lnvps deploy/mostro/patch-0011-tempo-di-chi-pubblica.py deploy/mostro/barattolo_tempo.rs deploy/mostro/0011-timeout-give-the-maker-a-waiting-window-of-his-own-a.patch deploy/mostro/patch-0012-disputa-automatica.py deploy/mostro/0012-events-tell-the-marketplace-server-when-the-escrow-g.patch debian@vm-1937.lnvps.cloud:nodo/patch-bar8/`
  2) SUL NODO, a secco e poi per davvero, un commit:
  `cd ~/nodo/mostro-src`
  `python3 ~/nodo/patch-bar8/patch-0011-tempo-di-chi-pubblica.py --secco`
  → deve dire «A SECCO: 13 agganci in 7 file, tutte le ancore uniche,
  piu' src/barattolo_tempo.rs. Niente scritto.» (la stessa riga del PC,
  12 ott). Un FERMO qualunque si incolla a Claude.
  `python3 ~/nodo/patch-bar8/patch-0011-tempo-di-chi-pubblica.py && git add -A && git commit -m "timeout: give the maker a waiting window of his own, and put the order back in the book when he lets a take lapse"`
  `git log --oneline v0.19.0..HEAD` → DIECI righe. (Strada equivalente:
  `git am ~/nodo/patch-bar8/0011-*.patch`: stesso albero.)
  POI LA 0012, sopra, allo stesso modo — a secco, per davvero, un commit:
  `python3 ~/nodo/patch-bar8/patch-0012-disputa-automatica.py --secco`
  → deve dire «A SECCO: 3 agganci in 2 file, tutte le ancore uniche.
  Niente scritto.»
  `python3 ~/nodo/patch-bar8/patch-0012-disputa-automatica.py && git add -A && git commit -m "events: tell the marketplace server when the escrow guardian opens a dispute by itself"`
  `git log --oneline v0.19.0..HEAD` → UNDICI righe. (Strada equivalente:
  `git am ~/nodo/patch-bar8/0012-*.patch`.)
  3) I TEST PRIMA DELLA BUILD VERA, in DUE lanci come per la `-bar7` (il
  perché dei due sta lì sotto: una prova di upstream che legge una
  globale): il primo coi filtri di ieri più quelli della 0011, il secondo
  `util::tests::` da solo.
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar8 .`
  `docker run --rm mostro-test:bar8 cargo test --release -- app::take_buy app::take_sell flow barattolo_bond toml_only_payment_methods barattolo_tempo scheduler nip33 find_order_by_seconds a_dispute_the_daemon_opens`
  `docker run --rm mostro-test:bar8 cargo test --release -- util::tests::`
  Fra i verdi devono comparire gli otto di `barattolo_tempo::tests::` —
  `the_duty_is_the_makers_in_the_two_states_upstream_cancels`,
  `without_the_key_the_maker_has_the_takers_window`,
  `each_party_is_judged_on_its_own_window`,
  `with_no_settings_loaded_the_rule_is_upstreams`,
  `the_limit_is_off_unless_it_can_put_the_order_back_at_least_once`,
  `the_info_event_carries_only_what_is_in_force`,
  `a_lapse_is_counted_once_per_waiting_episode`,
  `the_takers_duty_never_touches_the_count` —, i quattro
  `reconfirm_timeout_eligibility_…` dello scheduler, l'unica
  `find_order_by_seconds…` (è una sola, non due: contata il 13 ott) e `status_tags_map_lifecycle_statuses_to_nip69_buckets`
  (quella emendata). PER LA 0012: la sua prova
  `barattolo_eventi::tests::a_dispute_the_daemon_opens_is_mostros_and_says_why`
  e, già dentro il filtro `scheduler`, le tre di upstream che passano
  dal ramo toccato — `escrow_deadline_opens_dispute_on_fiat_sent_without_touching_escrow`,
  `escrow_deadline_resumes_a_half_completed_dispute_transition`,
  `escrow_deadline_reopens_a_dispute_the_users_resolved_themselves`.
  ⚠️ I filtri `scheduler` e `nip33` sono NUOVI in
  questa liturgia: se cade una prova che NON è fra queste, la si rilancia
  da sola (`cargo test --release -- <nome intero>`); se da sola passa è
  la globale dei test, come per la `-bar7`, e lo si scrive qui. Se la
  build o i test si fermano su una delle nostre: l'errore si incolla a
  Claude, sul nodo `git reset --hard HEAD~2` (torna alla 0010: via la
  0011 e la 0012) e niente ritocchi a mano.
  4) VERDI: `git format-patch -2 --start-number 11 -o ~/nodo/patch-bar8/export`
  e le due `.patch` tornano sul PC con `scp`: `diff` contro quelle nel
  repo deve dire solo `index`, `From` e `Date`, MAI una riga di codice.
  5) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.19.0-bar8 .`
  — tag nuovo; la `-bar7` resta sulla macchina.
  6) IL COMPOSE: `cd ~/nodo` e con `nano docker-compose.yml` la SOLA
  riga dell'immagine a `mostro:v0.19.0-bar8`.
  6-bis) IL `settings.toml`: `nano ~/nodo/mostro/settings.toml`, nel
  blocco `[mostro]`, SOTTO la riga `expiration_seconds = 1800` (che NON
  si tocca: è il tempo di chi prende), le due righe nuove:
  `maker_expiration_seconds = 10800`
  `maker_timeout_limit = 2`
  Si rilegge: `grep -n "expiration_seconds\|maker_timeout_limit" ~/nodo/mostro/settings.toml`
  → tre righe (1800, 10800, 2), tutte dentro `[mostro]`.
  FASE 4 — IL RIAVVIO DEL SOLO CONTAINER MOSTRO, e il controllo:
  7) IL LIBRO FERMO, di nuovo (la query della fase 1, c). Se è fermo:
  `docker compose up -d mostro`
  (`up -d`, non `restart`: la riga dell'immagine è cambiata).
  8) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` →
  `-bar8`; `docker compose logs mostro --since 2m` → «Settings
  correctly loaded», `Transport: nip44`, NESSUNA riga di migrazione,
  `barattolo_eventi: order events go to …`. Poi, dall'app («Info P2P» →
  «I tempi»): «chi l'ha preso, che ha 30 minuti … chi l'ha pubblicato,
  che ha 3 ore», e sotto «alla seconda presa di fila senza risposta
  l'ordine si toglie» — è il 38385 nuovo letto dal telefono
  (`maker_expiration_seconds 10800`, `maker_timeout_limit 2`); gli altri
  tag come prima (`bond_enabled true`, `bond_only_payment_methods
  Contanti`). E QUI CI SI FERMA.
  FASE 5 — LA PROVA DELLA SCADENZA, di Andrea, a due telefoni, dopo. È
  la prova che mancava da settembre (NODO-MOSTRO: «la riconsegna al
  libro» mai vista dal vivo). Una vendita piccola pubblicata dal
  telefono A, presa dal B, e A NON paga la garanzia: allo scadere delle
  ore di A l'ordine deve TORNARE nel libro (a A «Non hai risposto in
  tempo: il tuo ordine è tornato nel libro», a B «Chi aveva pubblicato
  l'ordine non ha risposto in tempo»), e alla seconda volta deve
  SPARIRE (a A «Non hai risposto a due prese di fila»). Aspettare tre ore
  per due volte è lungo: per la prova si può mettere
  `maker_expiration_seconds = 600` al punto 6-bis e riportarlo a 10800
  DOPO la prova con un `docker compose restart mostro` a libro fermo — è
  una riga del `settings.toml`, non serve ricompilare. Lo decide Andrea.
  Nel log del nodo: `docker compose logs mostro --since 4h | grep barattolo_tempo`
  → «maker lapse 1 of 2, back to the book» e poi «maker lapse 2 of 2,
  the order is removed».
  LA 0012 NON SI PROVA IN FRETTA: la disputa automatica nasce a ~92 ore
  da una garanzia pagata, col pagamento segnato e mai liberato. Il
  giorno che succede si riconosce da tre cose: nel log del nodo
  `docker compose logs mostro --since 1h | grep "dispute-opened"` →
  «barattolo_eventi: order … dispute-opened: delivered»; ai moderatori
  l'avviso «⚖️ Disputa P2P aperta … L'ha aperta il coordinatore da solo
  … va decisa adesso»; alle due parti «Lo scambio … è passato ai
  moderatori». E la card ⚖️ del cruscotto la conta come le altre.
  FASE 6 — A `-bar8` IN SERVIZIO, i due ritocchi che restano (sono righe
  di testo: si chiedono a Claude, e passano dal push come tutto):
  a) LA FRASE DELLE 88 ORE AI MODERATORI (`_testo_garanzia_mod_p2p` in
  `server.py`) dice ancora che verso le 92 ore il coordinatore «apre
  una disputa da solo che non arriva a nessuno su Telegram». Con la
  0012 arriva: finché gira la `-bar7` la frase è vera e RESTA; a `-bar8`
  in servizio si toglie «che non arriva a nessuno su Telegram».
  b) LA RIGA DELL'IMMAGINE DEL NODO in `CLAUDE.md` (`mostro:v0.19.0-bar7`
  → `-bar8`, con la 0011 e la 0012), rimandata da Andrea a quel giorno.
  ✅ FATTI TUTTI E DUE il 13 ott 2026 (cantiere `mostro-bar8`).
  DA SAPERE PER BARATTOZON (12 ott 2026, cantiere pausa-in-vista): con
  le tre ore a chi pubblica un ordine Barattozon esce dal libro 4 ORE E
  30 prima che il PayCode scada, invece di due — lo decide la pagina di
  chi PUBBLICA, leggendo il tempo dal 38385, e lo scrive nella scadenza
  dell'ordine. Quindi gli ordini Barattozon GIÀ nel libro al momento
  del riavvio tengono le due ore finché vivono (al più 72 ore): uno
  preso a ridosso della chiusura, con chi pubblica che usa tutte le sue
  tre ore, può arrivare al PayCode scaduto. Non è un guasto e non
  ferma niente: prima del riavvio si guarda se nel libro ce ne sono
  (dall'app, la pillola Barattozon del libro), e se sì lo si dice a chi
  li ha pubblicati, o si aspetta che escano.
  ROLLBACK: `cd ~/nodo`, la riga dell'immagine a `mostro:v0.19.0-bar7`
  e le due righe nuove del `settings.toml` commentate (la `-bar7` le
  ignorerebbe comunque: `[mostro]` non rifiuta le chiavi che non
  conosce), poi `docker compose up -d mostro` a libro fermo. La tabella
  `barattolo_maker_lapses` resta nel database e non dà fastidio a
  nessuno: non è una migrazione. Sul VPS non c'è niente da toccare: senza
  il tag del tempo lungo nel 38385 il «non completato» a chi pubblica si
  spegne da solo, e pausa e badge restano.
  COM'È ANDATA (13 ott 2026, cantiere `mostro-bar8`; i comandi li ha
  lanciati Andrea, uno alla volta). PRIMA: il VPS sulla punta di main
  (`3db1ef4`), il nodo sulla `-bar7`, `mostro-src` pulito con le nove
  righe, il libro fermo (14 `pending`, nessuno scambio aperto); 4
  processori, 5 GB di memoria disponibile, 18 GB di disco liberi.
  I cinque file sono partiti dal PC coi fine riga di Linux (presi da git
  con `git show`, non dalla cartella di lavoro di Windows, dove i due
  patcher escono CRLF), e sul nodo le impronte `sha256sum` erano le
  stesse. I due patcher a secco hanno detto le frasi attese; i due
  commit hanno gli stessi conti delle `.patch` del repo (8 file, 468 e
  7; 2 file, 29). LA PRIMA COMPILAZIONE è passata al primo colpo:
  `Finished release` in 6 minuti e 53, nessun avviso del compilatore.
  I TEST: primo lancio 246 passate e 0 fallite, secondo (`util::tests::`)
  79 e 0; le tredici prove nominate al punto 3 cercate una per una nel
  registro, tutte `ok`. La cucina di prova ha preso 3 GB di disco.
  IL CONFRONTO DEL PUNTO 4 HA DETTO «DIVERSA», e non era un guasto: le
  righe di codice delle due patch sono le stesse, cambiano solo le
  posizioni dei riquadri dentro `src/barattolo_eventi.rs` (`@@ -77` sul
  nodo, `@@ -80` nel repo). ⚠️ IL SORGENTE DEL NODO È PIÙ VECCHIO DEL
  REPO in due file: le 0005 e 0007 ritoccate il 1 ott 2026 per l'audit
  (`998a5d2`: M6 il segreto degli eventi senza ripiego, M4
  l'interruttore dello sconto, B6 il tetto alla risposta) non sono mai
  arrivate sul nodo — la `-bar7` e la `-bar8` hanno solo aggiunto patch
  sopra il sorgente che c'era. Visto sul nodo: `ENV_SECRET_FALLBACK`
  c'è ancora in `barattolo_eventi.rs`, `BREAKER_FAILS` in
  `barattolo_fee.rs` no. DA FARE nella build della 0.19.3, dove il fork
  si rifà da capo (decisione di Andrea: oggi solo la `-bar8`); per la M6
  va guardato PRIMA che sul nodo ci sia `BARATTOLO_EVENTI_SEGRETO`: se
  oggi vale il ripiego, senza quella gli eventi si spengono. E finché il nodo è indietro il confronto del
  punto 4 guarda le righe che cominciano per `+` e `-`, non le
  intestazioni `@@`.
  L'IMMAGINE VERA in pochi secondi (ha riusato la compilazione provata).
  Dentro `/usr/local/bin/mostrod` la parola `maker_timeout_limit`
  compare 5 volte nella `-bar8` e 0 nella `-bar7`.
  IL CAMBIO SENZA EDITOR: quattro file preparati prima e mostrati ad
  Andrea — `docker-compose.yml.prima-bar8` e
  `mostro/settings.toml.prima-bar8` (il ritorno: identici ai vivi con
  `cmp`), `docker-compose.yml.bar8` e `mostro/settings.toml.bar8`
  (l'andata: `diff` dice la riga 57 del compose e le due righe nuove
  sotto la 60, nella sezione `[mostro]`; `tomllib` legge 1800, 10800 e
  2; `docker compose -f … config -q` lo accetta). Il backup del
  database con l'API di sqlite da `python3` (`backup()`: 260 ordini
  nella copia e nel vivo) e non col `cp` della FASE 2 su un file vivo;
  la copia nasce di root e leggibile da tutti: `chown debian:debian` e
  `chmod 600` subito. Il cambio è UN comando che per prima cosa conta
  gli scambi aperti e, se non sono zero, non tocca niente; poi i due
  `cp -p` e `docker compose up -d mostro`. LIBRO FERMO dalle 11:36:00
  alle 11:36:11 UTC; Tor, LND e bitcoind `Running`. Dopo: `-bar8`,
  `running`, zero riavvii; «Settings correctly loaded!», le due righe
  `barattolo_fee` e `barattolo_eventi`, `Transport: nip44 (protocol v2,
  event kind 14)`, nessuna migrazione, nessun errore (i soli `WARN`
  sono del prezzo di valute con una fonte sola, c'erano anche prima).
  LA PROVA DAL VIVO, di Andrea con due account suoi: pubblicato, preso,
  e a chi ha pubblicato «Hai ancora 2:59:29 per bloccare i sats, poi
  l'ordine torna nel libro». Annullato dal lato di chi ha preso: nel
  registro degli esiti del VPS nessun `mancato`, nel journal nessuna
  riga «Reputazione P2P». L'annuncio agli utenti era già uscito il 12.
  DAMUS FUORI DAL `settings.toml`, con un secondo riavvio (deciso nel
  cantiere relay-per-mostro: «con la -bar8, a libro fermo»): la riga 35
  da quattro relay a tre — `relay.barattolo.store`,
  `relay.mostro.network`, `nos.lol` —, altri due file pronti
  (`settings.toml.prima-senza-damus`, `settings.toml.senza-damus`), lo
  stesso comando col conto degli scambi aperti, `docker compose restart
  mostro`. Libro fermo dalle 11:47:43 alle 11:47:53 UTC; dopo, «Sending
  Mostro relay list» e la parola `damus` zero volte nel registro.
  NOS.LOL FUORI, PRIMAL DENTRO (12 nov 2026, stessa forma): nos.lol non
  rispondeva piu' alle uscite Tor (timeout dal namespace di mostro, 200
  dal PC; ultimo prezzo accettato il 6 nov). Riga 35 oggi:
  `relays = ['wss://relay.barattolo.store', 'wss://relay.mostro.network',
  'wss://relay.primal.net']` — APICI SINGOLI, un `sed` con le doppie non
  trova niente. Copia `settings.toml.prima-senza-noslol`, file nuovo
  `settings.toml.senza-noslol` coi permessi del vero (`chmod
  --reference`: dentro c'e' la chiave di Mostro), `cp` SENZA `-p` sul
  file vero. Libro fermo 11:59:41-51 UTC. Prima di scegliere un relay si
  prova DA TOR: `docker run --rm --pull never --network
  container:nodo-mostro-1 curlimages/curl -s -m 40 -o /dev/null -w
  '%{http_code}' https://<relay>` (il 12 nov: primal, snort, damus 200;
  nostr.mom e offchain.pub 000). La prova dopo, relay per relay:
  `docker logs --since <ora del riavvio> nodo-mostro-1 2>&1 | grep
  'published exchange rates' | tail -n1 | grep -oE
  'wss://[a-z.]+"\): (Ack|"[^"]*")'` — tre `Ack`.
  NON PROVATO, e resta della FASE 5: la scadenza vera (l'ordine che
  TORNA nel libro alla prima mancata risposta e SPARISCE alla seconda,
  con le righe `barattolo_tempo` nel registro) — la prova del 13 si è
  fermata al conto alla rovescia; la disputa automatica della 0012 (~92
  ore); cosa vede chi prende da un'altra app. IL RITORNO ALLA `-bar7`
  non è stato provato dal vivo (scelta di Andrea): sono i due `cp -p`
  dai file `.prima-bar8` e `docker compose up -d mostro`. ⚠️ Il
  `settings.toml.prima-bar8` ha ancora damus: tornare alla `-bar7` con
  quel file rimette anche damus (per toglierlo di nuovo, la riga 35).
  DA FARE, non urgente: le immagini `mostro-test:bar2`…`bar7` occupano
  disco per niente (15 GB liberi dopo la build, 85% usato).
- LA SALITA ALLA `-bar7`, immagine `mostro:v0.19.0-bar7` (preparata il
  10 ott 2026 sera, cantiere `cauzione-metodo-scelto`; ✅ FATTA SUL NODO
  da Andrea, riferito il 12 ott 2026: `mostro:v0.19.0-bar7` in servizio
  con la 0010, i 17 ordini intatti, nessun errore nei log, e la leva
  `P2P_CAUZIONE_SUL_METODO` accesa sul VPS — punto 9; dal telefono, su un
  ordine misto, con SEPA la cauzione non compare e con Contanti sì; uno
  scambio vero non c'è ancora stato. Nei test del punto 3 è caduta UNA
  prova di upstream, per il filtro: vedi sotto). Cosa cambia: la patch 0010 del fork — la cauzione sul
  metodo che chi prende DICHIARA nel take (decisione di Andrea: la
  cauzione si chiede SOLO a chi sceglie i contanti; su «SEPA, Contanti»
  chi sceglie SEPA, Satispay, PayPal o il PayCode non blocca niente).
  Nessuna settings nuova, nessuna migrazione, `settings.toml` com'è; il
  38385 non cambia. ⚠️ IL CLIENT STA DIETRO UNA LEVA SPENTA
  (`P2P_CAUZIONE_SUL_METODO`, 11 ott 2026): finché è spenta manda il take
  come ieri (`Amount` sull'intervallo, niente sul normale) e promette la
  cauzione dell'ordine intero, che il nodo senza la 0010 chiede lo
  stesso — e gestisce il foglio della cauzione come oggi. Un nodo SENZA
  la 0010 che ricevesse `Payload::Order` lo ignorerebbe su un ordine
  normale (`get_fiat_amount_requested` torna `order.fiat_amount`) ma su
  un INTERVALLO risponderebbe `OutOfRangeSatsAmount` (`get_amount` legge
  solo `Amount` e `PaymentRequest`): per questo la leva si accende DOPO
  la `-bar7`, punto 9. Il rollback è la riga dell'immagine nel compose,
  a `-bar6`, e la leva di nuovo a False.
  Host, in cima a tutto (l'alias ssh può essere un altro: è quello di
  sempre del nodo di Dublino):
  `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1937.lnvps.cloud`
  FASE 1 — IN SOLA LETTURA, tutt'e tre:
  a) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1`
  → `mostro:v0.19.0-bar6`.
  b) `cd ~/nodo/mostro-src && git status && git log --oneline v0.19.0..HEAD`
  → branch `barattolo/v0.19.0`, albero PULITO, OTTO righe (la 0008 in
  cima: «bond: apply the anti-abuse bond only to the payment methods
  the policy names»). Se non è pulito NON si va avanti.
  c) IL LIBRO FERMO (la stessa query della `-bar6`, `mode=ro`):
  `sudo python3 -c "import sqlite3; c=sqlite3.connect('file:/home/debian/nodo/mostro/mostro.db?mode=ro', uri=True); print(c.execute('SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC').fetchall())"`
  Devono comparire SOLO `pending` e stati finali; uno fra
  `waiting-payment`, `waiting-buyer-invoice`, `waiting-taker-bond`,
  `active`, `fiat-sent`, `settled-hold-invoice`, `in-progress` o
  `dispute` = c'è uno scambio in corso: si ASPETTA.
  FASE 2 — IL BACKUP (costa un secondo):
  `cp ~/nodo/mostro/mostro.db ~/nodo/mostro/mostro.db.prima-bar7`
  `cp ~/nodo/docker-compose.yml ~/nodo/docker-compose.yml.prima-bar7`
  FASE 3 — LA BUILD:
  1) SUL PC, il patcher al nodo, in una cartella NUOVA e FUORI da
  `mostro-src`:
  `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1937.lnvps.cloud mkdir -p nodo/patch-bar7`
  `scp -i $env:USERPROFILE\.ssh\lnvps deploy/mostro/patch-0010-cauzione-metodo-dichiarato.py deploy/mostro/0010-bond-decide-the-taker-bond-on-the-payment-method-the.patch debian@vm-1937.lnvps.cloud:nodo/patch-bar7/`
  2) SUL NODO, a secco e poi per davvero, un commit:
  `cd ~/nodo/mostro-src`
  `python3 ~/nodo/patch-bar7/patch-0010-cauzione-metodo-dichiarato.py --secco`
  → deve dire «A SECCO: 8 agganci in 5 file, tutte le ancore al loro
  conto, il modulo di test in coda a flow.rs. Niente scritto.» (la
  stessa riga del PC, 10 ott). Un FERMO qualunque si incolla a Claude.
  `python3 ~/nodo/patch-bar7/patch-0010-cauzione-metodo-dichiarato.py && git add -A && git commit -m "bond: decide the taker bond on the payment method the taker declares"`
  `git log --oneline v0.19.0..HEAD` → NOVE righe. (Strada equivalente:
  `git am ~/nodo/patch-bar7/0010-*.patch`: stesso albero, verificato sul
  PC il 10 ott — tree `1385488c`.)
  3) I TEST PRIMA DELLA BUILD VERA (il filtro della `-bar6` con i test
  della 0010, `barattolo_bond_take`, dentro `barattolo_bond`), in DUE
  lanci:
  `docker build -f docker/Dockerfile --target builder -t mostro-test:bar7 .`
  `docker run --rm mostro-test:bar7 cargo test --release -- app::take_buy app::take_sell flow barattolo_bond toml_only_payment_methods`
  `docker run --rm mostro-test:bar7 cargo test --release -- util::tests::`
  ⚠️ PERCHÉ DUE (12 ott 2026, dalla build vera): col filtro `util` in
  coda al primo lancio — com'era scritto qui il 10 ott — è caduta
  `util::tests::connect_nostr_builds_client_with_configured_relays`
  («configured relays must be registered»), che da sola passa. NON è
  della 0010: è una prova di UPSTREAM (c'è già nel tag `v0.19.0`) che
  legge i relay dalle impostazioni GLOBALI dei test (`MOSTRO_CONFIG`, un
  `OnceLock`: la prima `set` vince e le altre non fanno niente). Il suo
  `init_globals` mette `test_settings()`, che un relay ce l'ha; ma cinque
  moduli di upstream mettono un `Settings` fatto a mano con
  `relays: vec![]` — `app/bond/flow.rs`, `app/bond/payout.rs`,
  `app/dev_fee.rs`, `app/rate_user.rs`, `lightning/mod.rs` — e il filtro
  `flow` pesca proprio `app::bond::flow`: se uno dei suoi test parte per
  primo, la globale nasce senza relay e quella prova cade. Dipende
  dall'ordine dei thread di `cargo test`, non dal codice: nelle liturgie
  fino alla `-bar6` il filtro non la pescava (`config::util` non è
  `util::tests`), e a pescarla è stato il `util` aggiunto qui. Da sola
  (`util::tests::` pesca solo `src/util.rs` e `src/config/util.rs`, che
  la globale non la tocca) vede sempre `test_settings()`. La 0010 e la
  0008 non toccano né `MOSTRO_CONFIG` né `init_globals` (zero righe nelle
  due `.patch`). Il binario non c'entra: è una prova, e l'immagine in
  servizio è quella giusta. La cura vera è di upstream (la prova non
  dovrebbe leggere una globale che altri moduli impostano diversa).
  Fra i verdi devono comparire `barattolo_bond_take::declared_method_decides_when_the_order_offers_it`,
  `…::a_declaration_the_order_does_not_offer_falls_back_to_the_order`,
  `…::an_empty_policy_still_covers_every_take` e i tre della 0008. Se la
  build o i test si fermano: l'errore si incolla a Claude, sul nodo
  `git reset --hard` al commit della 0008 (`git log` lo dice) e niente
  ritocchi a mano.
  4) VERDI: `git format-patch -1 --start-number 10 -o ~/nodo/patch-bar7/export`
  e la `.patch` torna sul PC con `scp`: `diff` contro quella nel repo
  deve dire solo `index`, `From` e `Date`, MAI una riga di codice.
  5) LA BUILD VERA: `docker build -f docker/Dockerfile -t mostro:v0.19.0-bar7 .`
  — tag nuovo; la `-bar6` resta sulla macchina.
  6) IL COMPOSE: `cd ~/nodo` e con `nano docker-compose.yml` la SOLA
  riga dell'immagine a `mostro:v0.19.0-bar7`. `settings.toml` NON si
  tocca.
  FASE 4 — IL RIAVVIO DEL SOLO CONTAINER MOSTRO, e il controllo:
  7) IL LIBRO FERMO, di nuovo (la query della fase 1, c). Se è fermo:
  `docker compose up -d mostro`
  (`up -d`, non `restart`: la riga dell'immagine è cambiata).
  8) `docker inspect --format '{{.Config.Image}}' nodo-mostro-1` →
  `-bar7`; `docker compose logs mostro --since 2m` → «Settings
  correctly loaded», `Transport: nip44`, NESSUNA riga di migrazione,
  `barattolo_eventi: order events go to …`; il 38385 come prima
  (`bond_enabled true`, `bond_only_payment_methods Contanti`). E QUI CI
  SI FERMA: la prova vera — un «SEPA, Contanti» preso scegliendo SEPA
  senza `pay-bond-invoice`, e preso scegliendo Contanti con la cauzione
  — è di Andrea, a due telefoni, dopo.
  9) LA LEVA DEL CLIENT, SUL VPS, solo DOPO il punto 8 e con la
  `-bar7` in servizio: `nano /srv/barattolo/config.py`, la riga
  `P2P_CAUZIONE_SUL_METODO = True` (da AGGIUNGERE: nel codice è False), poi
  `sudo systemctl restart barattolo` e il pannello «⚙️ Stato delle leve»
  → «Cauzione sul metodo scelto (nodo alla -bar7): acceso». Da lì il
  client manda il metodo scelto nel take e promette la cauzione solo a
  chi sceglie «Contanti». Accesa PRIMA della `-bar7` rompe le prese
  sugli intervalli (sopra): mai.
  ROLLBACK: la leva a `False` sul VPS e riavvio (basta da sola: il
  client torna a ieri e il nodo `-bar7` con `Amount` decide
  sull'ordine); e, se serve, la riga dell'immagine a
  `mostro:v0.19.0-bar6` con `docker compose up -d mostro` a libro fermo.
- LA SALITA A MOSTRO 0.19.0, COM'È ANDATA (1 ott 2026, la liturgia qui
  sopra eseguita da Andrea un comando alla volta, i comandi scritti da
  Claude; il nodo gira `mostro:v0.19.0-bar6` con le OTTO patch e la
  cauzione accesa solo per «Contanti»). In ordine:
  FASE 1 il 30 set: `transport = "nip44"`, finestra 300, `-bar5` in
  servizio, `barattolo/v0.18.8` pulito a `1489f38`, libro fermo
  (canceled 120, success 15, expired 9, cooperatively-canceled 2 — stato
  di ORDINE, terminale, non il residuo delle dispute —, pending 1,
  canceled-by-admin 1). Poi la pausa fino al push della cauzione
  (`f3d0091`), coi due controlli sul PC: la liturgia riletta da
  origin/main e gli otto patcher a secco su un checkout LF pulito di
  `v0.19.0`.
  0) Il backup con l'API `backup` di SQLite e `sudo` (mostrod acceso),
  176128 byte come l'originale, poi `debian:debian 600` come
  l'originale. 1) I dieci file (otto patcher e i due `.rs`) in
  `~/nodo/patch-bar6/`, copiati NON dalla working copy del PC — ferma a
  giorni prima, senza la 0008 — ma da un export di origin/main (LF,
  impronte uguali ai blob): le dieci impronte combaciavano. 2) Il tag
  `v0.19.0` fetchato, `barattolo/v0.19.0` da `d53e41d`, il vecchio branch
  lasciato lì. 3) Le otto stringhe a secco esattamente quelle attese,
  otto commit.
  4) IL PUNTO CHE HA MORSO, DUE VOLTE, ed era la ragione per cui il
  primo `cargo` è sul nodo: il builder compila (615 s), i test NO.
  Prima `nostr_sdk::Tag` nel modulo di test della 0008 in `nip33.rs`
  («cannot find type Tag in crate nostr_sdk»): con nostr-sdk 0.45 `Tag`
  si prende dal prelude, come fa nip33.rs stesso — corretto il patcher
  (`482bbfc`). Poi 519 verdi e UN rosso,
  `amounts_travel_only_when_the_trade_closes` della 0007: non un difetto
  della 0008 ma la sua REGOLA (una cauzione bruciata porta i suoi
  importi, e il server la segue già in `P2P_AZIONI_CON_SATS`) contro un
  test della 0007 che gira su tutto il vocabolario, ora di tredici
  azioni; la cura sta dove sta la regola, cioè nel patcher 0008, che
  emenda anche quel test — ventesimo aggancio, ancora a tre righe
  perché la stessa riga vive anche in `emit_detail`, che non cambia
  (`beb01bd`); la stringa a secco è da allora «20 agganci in 10 file».
  Ogni volta: `git reset --hard` al commit della 0007 sul nodo, il solo
  patcher nuovo via scp con la sua impronta, secco, commit, di nuovo 4a
  e 4b. ALLA FINE 520 verdi e 0 rossi (zero test nel blocco
  `cashu_mint`, che non è nostro), coi tre della 0008 e
  `pre_claim_failures_by_class` della 0007 fra i verdi.
  5) Le otto `.patch` esportate dal nodo e confrontate sul PC
  (`confronta_patch.py`, per numero): corpi IDENTICI — stat e ogni hunk,
  senza le righe `index` — e tre sole intestazioni diverse, da mettere
  a verbale perché la liturgia diceva «solo index, From e Date»: l'AUTORE
  (sul nodo i commit li firma l'utente git del nodo, nel repo
  «Barattolo»), il NUMERO nell'oggetto (`[PATCH n/8]` contro `n/7` e
  `[PATCH]`, con l'a capo dell'oggetto lungo che si sposta) e la
  VERSIONE DI GIT in coda (2.47.3 contro 2.55 di Windows). Il primo giro
  del confronto le contava come differenze e diceva «ci si ferma»: il
  giudice è stato corretto, non il verdetto.
  6) `mostro:v0.19.0-bar6` (`f65d34e397b7`), la `-bar5` lasciata in uso.
  7) SOLO la copia del compose: riga 57 e 7-bis fatti INSIEME subito
  prima dell'`up -d`, decisione di Andrea, perché nessun `compose up`
  nel mezzo potesse ricreare `mostro` con l'immagine nuova e il settings
  vecchio, o il contrario — ed è la regola da tenere: compose e
  `settings.toml` si cambiano nello stesso respiro del riavvio.
  8) Al via (il 1 ott, a cantieri dell'app fermi): libro fermo (solo
  pending e stati finali), riga 57, copia del `settings.toml`, finestra
  a 900 (riga 15) e il blocco `[anti_abuse_bond]` di sette righe in
  coda (293-299, dopo un `[cashu]` commentato), `up -d`: in servizio
  `-bar6`, nel log «Transport: nip44 (protocol v2, event kind 14)», i
  prezzi su tutti e quattro i relay, nessun error, panic o migrazione.
  Il 38385 letto dallo SPECCHIO: `mostro_version 0.19.0`,
  `protocol_version 2`, `bond_enabled true`, `bond_apply_to take`,
  `bond_amount_pct 0.03`, `bond_base_amount_sats 1000`,
  `bond_slash_on_waiting_timeout false`, `bond_only_payment_methods
  Contanti`, `hold_invoice_expiration_window 900`; `expiration_seconds`
  900 e `fee 0.03` come prima. ⚠️ Sulla macchina del relay `jq` non c'è:
  lo scan si fa con `/app/strfry` e i tag si filtrano con `python3`,
  non col `jq` scritto nella liturgia.
  8-bis) Sul VPS: online `9e3f91f` (contiene la cauzione `f6f9765` e la
  guardia del protocollo `b071030`; la CI era senza budget, ma il deploy
  di quei commit era già passato), nessun `.deploy-bocciato`;
  `P2P_CAUZIONE = True` alla riga 116 del config, riavvio dolce,
  servizio attivo e ascolto P2P sullo specchio. Il pannello delle leve:
  «Cauzione nel contanti di persona» accesa.
  LA PROVA A DUE TELEFONI (1 ott 2026, la mattina, Andrea con due
  account): in «Contanti», ordine `82231748` (vendita da 5 €), chi prende
  ha pagato la cauzione da 1.000 sats — il pavimento, perché il 3% era
  meno —, poi la garanzia, «Siamo insieme» col QR, il rilascio; la hold
  della cauzione (`387c53d5…`) risulta CANCELED, cioè restituita. Le fee
  in `barattolo_fees`: 68 + 68 sats su 6.764, l'1% a testa con
  `discount 1` per tutt'e due, 136 trattenuti dal nodo e ~134 netti dopo
  1,66 di rete. Con un altro metodo e con Barattozon NESSUNA cauzione
  chiesta: la porta per metodo della 0008 fa quel che dice. IL DIFETTO
  TROVATO: dopo la cauzione chi compra non ha ricevuto su Telegram
  «indica dove ricevere i sats» (`fattura_chiesta` da `mostro`: «nessuno
  da avvisare»), curato sul server in `1759be4`. Il pannello delle leve:
  «Cauzione nel contanti di persona» ACCESA.
  E IL DISPOSITIVO PULITO (1 ott, stesso giorno): uno scambio preso da
  un account e ripreso dallo STESSO account su un altro dispositivo
  compare con la controparte e si conclude da lì. Quale delle due fonti
  abbia dato il `peer` — il server per primo (`chiave_peer`, dagli
  eventi della 0007) o la restore del coordinatore (`counterparty_trade_pubkey`,
  la seconda) — la prova non lo distingue, e per chi scambia non conta:
  lo dice la riga «ripresa» del diario, se un giorno servisse.
  COSA RESTA: il journal di mostrod per una settimana senza `no Mostro
  transport for event kind`. IL ROLLBACK resta quello del punto 9: riga 57 a
  `mostro:v0.18.8-bar5` E `settings.toml` dalla copia `prima-bar6`, poi
  `up -d`; prima la query sulle dispute `cooperatively-canceled`; sul VPS
  `P2P_CAUZIONE = False` e riavvio.
- I LINK DENTRO TELEGRAM (10 ott 2026; perché in CANTIERI, «I link
  dentro Telegram aprono la Mini App»). La leva `TELEGRAM_MINIAPP_LINK`
  NON compare da sola nel config del VPS e nel codice è spenta: finché
  non c'è, il bottone «⚡ Apri lo scambio», il link «🫙 Apri il libro
  ordini», quello del post P2P nel canale, la riga «🫙 Apri Barattolo»
  delle tastiere e i link P2P condivisi restano barattolo.store, come
  prima. PER ACCENDERLA, in quest'ordine:
  1) BOTFATHER, e si guarda prima di scrivere: `/mybots` > @ilbarattolobot
     > Bot Settings > Configure Mini App. Se la Mini App principale è
     accesa (o la si accende lì: Enable Mini App, con l'indirizzo
     `https://barattolo.store/?v=2`, lo stesso del bottone di menu), la
     riga è `TELEGRAM_MINIAPP_LINK = "https://t.me/ilbarattolobot"`. Se
     invece si preferisce una Mini App col nome breve, la
     riga porta anche il nome: `"https://t.me/ilbarattolobot/<nome>"`.
     ⚠️ LA MINI APP COL NOME BREVE (10 ott 2026, sera): è la strada per
     riavere in chat un'anteprima con l'IMMAGINE. La sua creazione NON
     è nella documentazione ufficiale di Telegram — né il comando, né i
     campi, né le misure della foto —: la guida è BotFather stesso («type
     / in the input field to see the full list», dice la pagina dei bot).
     Di ufficiale c'è che l'app ha titolo, descrizione, una foto
     OBBLIGATORIA, un'animazione facoltativa e il nome breve, e che il
     link `t.me/<bot>/<nome>` in chat mostra quella foto con un bottone
     che apre la Mini App. Le immagini pronte, dal barattolo di casa:
     `anteprima-miniapp-grande-1280x720.jpg` (e 640x360) e
     `anteprima-miniapp-quadrata-640x640.jpg` (e 400x400), rifatte da
     `assets/barattolo-icona-sorgente.jpeg`. Con questa forma il server
     NON può chiedere a Telegram se l'app esiste (`getMe` dice solo della
     Mini App principale): all'avvio controlla il solo nome del bot, e la
     prova a mano del punto 2 va fatta sul link col nome —
     `https://t.me/ilbarattolobot/<nome>?startapp=p2p`.
  2) LA PROVA A MANO, prima del config: dal telefono, in una chat
     qualunque, toccare `https://t.me/ilbarattolobot?startapp=p2p`. Deve
     aprirsi la Mini App sul libro degli ordini. Se si apre la chat del
     bot, la Mini App principale non è accesa: NON mettere la riga.
  3) IL CONFIG: aggiungere la riga a `/srv/barattolo/config.py` (prima
     `grep -n "TELEGRAM_MINIAPP_LINK" /srv/barattolo/config.py`: non deve
     esserci già) e riavviare il servizio.
  4) IL JOURNAL, subito dopo il riavvio:
     `journalctl -u barattolo -n 80 --no-pager | grep "Link dentro Telegram"`
     — «🔗 Link dentro Telegram: accesi su …» vuol dire che Telegram ha
     confermato (il bot è questo, la Mini App principale c'è); «⚠️ Link
     dentro Telegram SPENTI: …» dice perché no, e i link restano quelli
     del sito finché non si corregge e si riavvia. Il valore VIVO sta
     nel pannello «⚙️ Stato delle leve».
     LA TERZA RIGA (11 ott 2026): «⚠️ Link dentro Telegram: getMe non ha
     risposto (…): la leva resta com'è scritta, riprovo fra N min» —
     Telegram non ha risposto o ha risposto con un errore (fra parentesi
     quale: `429 Too Many Requests…`, `500 …`, `HTTP 502, risposta non
     JSON`, `rete: ConnectError`). NON è un guasto nostro e NON spegne
     niente: i link restano quelli della Mini App e il server riprova
     da solo dopo 1, 5, 15 minuti e poi ogni ora per un giorno, senza
     riavvii. Quando Telegram risponde si legge «accesi su … (al
     tentativo N)» — oppure «SPENTI», se la risposta vera dice di no.
     Se non risponde per un giorno intero l'ultima riga è «…mi fermo
     qui. La leva resta com'è scritta; il prossimo controllo è al
     prossimo riavvio». Per vederle tutte, dall'ultimo riavvio:
     `journalctl -u barattolo --since "-2h" --no-pager | grep "Link dentro Telegram"`
  5) IL TELEFONO: far arrivare un promemoria («⚡ Apri lo scambio») e
     toccarlo; dalla Mini App, «Condividi» un ordine in una chat e
     toccare il link; mandare `/start` al bot e toccare «🫙 Apri
     Barattolo»; al primo avviso dei nuovi ordini toccare «🫙 Apri il
     libro ordini», e al primo post P2P nel canale il suo link; al primo
     avviso dei nuovi annunci «🫙 Apri Esplora» (deve aprire il reparto
     e il tetto del proprio filtro), e il lunedì «🫙 Sfoglia il
     mercatino» del riepilogo. Devono
     aprire la Mini App, già entrati, sul posto giusto. Si guarda anche
     l'ANTEPRIMA sotto l'avviso dei nuovi ordini: con la leva accesa
     non è più la miniatura del P2P ma quella che Telegram disegna per
     un link t.me.
  PER SPEGNERLA: togliere la riga (o metterla a `""`) e riavviare.


- LE HOLD DI PROVA, IL MACAROON `root_key_id 4` (10 ott 2026, cantiere
  prova-hold). I bottoni G e H di `https://barattolo.store/prova-wallet`
  coniano due hold invoice da 1 sat sul nostro LND (cltv 40 e 576) per
  capire se il wallet dell'utente si incanta sulla hold o sul CLTV
  lungo; vivono tre minuti e il server le cancella da solo (giro ogni
  mezzo minuto, e all'avvio), MAI le salda. Il server le chiede alla
  REST di LND dal ponte di sempre (`LND_PONTE_URL`, `LND_PONTE_CERT`)
  con un macaroon SUO, `LND_PONTE_MACAROON_HOLD`: ristretto per METODO,
  non per entita', cosi' SettleInvoice non c'e' proprio. Finche' la riga
  manca dal config G e H dicono «non attive» e la pagina esce lo stesso.
  LA PROCEDURA, un comando alla volta, con l'host in cima; i comandi li
  esegue Andrea, mai il server.
  Sul NODO (`~/nodo`), prima si guarda cosa c'e' — gli id gia' usati
  sono il 1 (LNbits) e quello del macaroon di lettura del server:
  `docker compose exec lnd lncli listmacaroonids`
  Se il 4 e' libero, si cuoce:
  `docker compose exec lnd lncli bakemacaroon --root_key_id 4 --save_to /tmp/barattolo-hold.macaroon uri:/invoicesrpc.Invoices/AddHoldInvoice uri:/invoicesrpc.Invoices/CancelInvoice uri:/lnrpc.Lightning/LookupInvoice`
  e si legge in esadecimale:
  `docker compose exec lnd xxd -p -c 9999 /tmp/barattolo-hold.macaroon`
  (se manca `xxd`: `od -An -tx1 -v FILE | tr -d ' \n'`). Controllo
  DOPO sul nodo: `docker compose exec lnd lncli listmacaroonids` deve
  dire anche il 4, e `docker compose exec lnd rm /tmp/barattolo-hold.macaroon`
  (la copia nel container non serve piu'). Sul VPS, controllo PRIMA:
  `grep -n "LND_PONTE_MACAROON_HOLD" /srv/barattolo/config.py` deve
  dire niente; poi la riga `LND_PONTE_MACAROON_HOLD = "<esadecimale>"`
  in coda al config (600, di `barattolo`), e `sudo systemctl restart
  barattolo`. Controllo DOPO: `journalctl -u barattolo -n 50 | grep 🧪`
  deve dire «Hold di prova (G e H di /prova-wallet): attive», e
  `curl -s https://barattolo.store/prova-wallet | grep -c 'class="b hold"'`
  deve dire 2. Si revoca da solo con `lncli deletemacaroonid 4` sul
  nodo (e la riga via dal config). Finito l'esperimento la riga puo'
  sparire: G e H tornano «non attive» senza altro da fare.
- L'INDIRIZZO LIGHTNING DI CASA (10 ott 2026; perché in CANTIERI,
  «L'indirizzo Lightning di casa: zap@barattolo.store»; com'è fatto in
  ARCHITETTURA, stesso titolo). `zap@barattolo.store`, per ricevere gli
  zap sul profilo Nostr ufficiale. Le leve NON compaiono da sole nel
  config del VPS e nel codice l'indirizzo è spento: finché non lo si
  accende, `https://barattolo.store/.well-known/lnurlp/zap` risponde
  404. PER ACCENDERLO, in quest'ordine:
  1) IL WALLET «zap», SUL PC: aprire il pannello di LNbits del nodo
     (`ssh -N -L 5001:127.0.0.1:5001 root@VPS` in un terminale, poi
     `http://127.0.0.1:5001` nel browser, login «LNbits nodo» in
     KeePass). Con lo STESSO utente della cassaforte: «Add a new
     wallet», nome `zap`. Dentro il wallet nuovo, a destra, «Node URL,
     API keys and API docs»: si copia la «Invoice/read key» — SOLO
     quella. La «Admin key» di quel wallet non si copia e non si mette
     da nessuna parte: è la chiave che spende.
  2) IL CONFIG, SUL VPS, da `barattolo`: prima si guarda che le righe
     non ci siano già — `grep -n "^ZAP_" /srv/barattolo/config.py` — poi
     si aggiungono in fondo a `/srv/barattolo/config.py` le due righe:
     la chiave, `ZAP_LNBITS_INVOICE_KEY` uguale alla invoice key copiata
     (fra virgolette), e la leva, `ZAP_ATTIVO = True`. Nient'altro:
     l'indirizzo di LNbits è quello del nodo (`LNBITS_NODO_URL`), il
     massimo è 100.000 sat (`ZAP_MAX_SATS` per cambiarlo), la npub che
     riceve è quella ufficiale (`ZAP_NPUB`). La invoice key non si
     scrive mai in chat, su GitHub o in un log.
  3) IL RIAVVIO: `sudo systemctl restart barattolo`.
  4) IL JOURNAL, subito dopo:
     `journalctl -u barattolo -n 120 --no-pager | grep "Indirizzo Lightning"`
     — «⚡ Indirizzo Lightning di casa: zap@barattolo.store ACCESO — zap
     Nostr con ricevuta firmata da …» è il verde; «SENZA zap Nostr» vuol
     dire che manca `NOSTR_NSEC_PIATTAFORMA` (l'indirizzo incassa, ma
     non firma ricevute); «spento» o la riga «⚠️ ZAP_ATTIVO e' True ma
     manca…» vuol dire che la chiave non è stata letta.
  5) IL CITOFONO, da qualunque computer:
     `curl -s https://barattolo.store/.well-known/lnurlp/zap` — deve
     tornare un JSON con `"tag":"payRequest"`, `"allowsNostr":true` e una
     `nostrPubkey`. Un `{"status":"ERROR"…}` vuol dire spento.
  6) UNA FATTURA DI PROVA, E COSA DICE IL JOURNAL. ⚠️ È LA PRIMA
     FATTURA VERA dell'indirizzo: prima del push è stato provato tutto
     con un LNbits di cartone, NON col LNbits del nodo (decisione di
     Andrea, 10 ott). Sul VPS si tiene aperto il journal:
     `journalctl -u barattolo -f | grep -i zap`. Poi, da un wallet che
     paga un Lightning address, si mandano 21 sat a
     `zap@barattolo.store`; oppure si chiede la fattura a mano, da
     qualunque computer —
     `curl -s "https://barattolo.store/api/lnurl/zap?amount=21000"`
     (l'importo è in MILLIsatoshi: 21000 = 21 sat) — e la `pr` che
     torna (`lnbc210n1…`) si incolla nel wallet e si paga.
     NEL JOURNAL, in ordine: «⚡ zap: fattura da 21 sats (pagamento
     semplice), abcd1234…» appena chiesta; entro una decina di secondi
     dal pagamento «⚡ Zap ricevuto: 21 sats (pagamento semplice),
     fattura abcd1234…». La card «⚡ Zap» di `/admin` mostra il saldo e
     la riga.
     SE INVECE il journal dice:
     · «⚠️ zap: fattura non coniata (ValueError: la fattura di LNbits
       non porta l'impronta o l'importo chiesti)»: LNbits ha coniato una
       fattura SENZA l'impronta della descrizione, e il server non l'ha
       data (il wallet riceve «Il nodo non risponde», niente è stato
       pagato). È il caso che da qui non si poteva provare: si spegne la
       leva (`ZAP_ATTIVO = False`, riavvio) e si riporta la riga com'è;
     · «⚠️ zap: fattura non coniata (…)» con un altro motivo: LNbits o il
       ponte verso LND sono giù, o la invoice key è sbagliata (401);
     · «⚠️ zap: LNbits non risponde (…): le fatture restano in attesa»:
       l'orologio non riesce a chiedere; niente scade, riprova da solo.
     Nel journal NON ci sono mai il commento, la fattura intera, la
     richiesta di zap o la chiave: la riga d'accesso di uvicorn del
     callback esce come `GET /api/lnurl/zap?… 200`, senza la query. Il
     Caddyfile del VPS non ha nessuna direttiva `log` (detto da Andrea,
     10 ott 2026), quindi un registro degli accessi di Caddy non c'è:
     se un giorno lo si accende, la query del callback va tolta anche
     lì, o i commenti finiscono in quel file.
  7) SOLO ADESSO IL PROFILO NOSTR: il campo `lud16` del kind 0 della
     npub ufficiale diventa `zap@barattolo.store`. Lo fa Andrea dal WSL,
     dove sta la chiave, con `nak` (v0.21.0; nel WSL `jq` non c'è, si usa
     `python3`), senza perdere gli altri campi: si scarica il kind 0 di
     adesso (`nak req -k 0 -a <hex della npub> <relay…> > prima.json`), si
     prende il più recente, si aggiunge `lud16` al `content` tenendo i
     `tags`, si FIRMA SENZA RELAY (`nak event < nuovo.json >
     firmato.json`, con la chiave in `NOSTR_SECRET_KEY` letta da `read
     -rs`, e `unset` subito dopo), si GUARDA che la `pubkey` del firmato
     sia quella della npub, e solo allora si pubblica il firmato
     (`nak event <relay…> < firmato.json`, che non rifirma) e si rilegge.
     ⚠️ DUE TRAPPOLE di `nak`, viste il 10 ott: senza chiave firma lo
     stesso, con una chiave «della macchina» (per questo si guarda la
     `pubkey` prima di pubblicare); `--prompt-sec` con lo stdin da un
     file resta appeso.
  8) UNO ZAP VERO, da un client Nostr, al profilo o a una nota: nel
     journal «⚡ Zap ricevuto: N sats (zap di abcd1234…)» e «🧾 zap:
     ricevuta … presa da N relay»; nel client lo zap compare sotto la
     nota. Se il journal dice «presa da 0 relay» la ricevuta resta in
     tabella e si riprova da sola altre due volte.
  COME SI SPOSTANO I SATS: a mano, dal pannello di LNbits — wallet
  «zap» > «Send» > si incolla una fattura del proprio wallet. Il server
  non può farlo (ha la sola invoice key), ed è voluto. Mai verso il
  wallet della cassaforte: i due registri restano separati.
  COSA NON TOCCARE: `NOSTR_NSEC_PIATTAFORMA`. È la chiave che firma le
  ricevute e che il citofono dichiara: cambiata, i client non contano
  più gli zap già ricevuti.
  PER SPEGNERLO: `ZAP_ATTIVO = False` (o via la riga) e riavvio; il
  citofono torna 404, e i wallet che provano l'indirizzo dicono che non
  esiste. Le fatture già coniate e non pagate non si incassano più da
  sole finché la leva è spenta: riaccesa, l'orologio le richiede a
  LNbits. Lo stato VIVO sta nel pannello «⚙️ Stato delle leve», gruppo
  «⚡ Indirizzo Lightning di casa».

- LO SWAP DAL TELEFONO: LE LEVE (20 ott 2026, tappa 3; perché in
  CANTIERI, «Lo swap dal telefono, tappa 3»; com'è fatto in
  ARCHITETTURA, «LO SWAP, TAPPA 3»). SUL VPS NON CAMBIA NIENTE:
  `SWAP_ATTIVO` resta spenta, e a leva spenta la CSP è quella di
  sempre e la pagina non scarica né i file di `/swap/` né
  `/vendor/swap.js`. La leva nuova `SWAP_RETE` NON si aggiunge al config
  del VPS: il default del codice è `bitcoin`. Le rotte nuove sono due
  file del repo: niente da copiare a mano.
  SULLA VM DI COLLAUDO, per lo swap intero sul regtest di Boltz (da
  fare): `SWAP_ATTIVO = True`, `SWAP_RETE = "regtest"`, e
  `SWAP_API_BASE` sull'API del regtest; poi riavvio (la CSP si calcola
  all'avvio e ammette la sola origine di quella base). ATTENZIONE: la
  base la chiamano DUE parti — il server (le tariffe del preventivo; in
  `MODALITA_COLLAUDO` solo se è 127.0.0.1 o localhost) e il BROWSER del
  telefono (tutto il resto, con CORS). Sulla VM va scelta una base che
  regga tutt'e due. Il controllo, in sola lettura: `grep -n
  "^SWAP_RETE\|^SWAP_API_BASE\|^SWAP_ATTIVO" /srv/barattolo/config.py`
  (la sola riga, mai le vicine).
  GLI ALTRI FORNITORI (20 ott 2026, l'instradatore): `SWAP_FORNITORI_IN_PIU`
  NON si aggiunge al config del VPS (vuota di serie: SATS Routing basta).
  Sulla VM, per provare la scelta fra due fornitori, una voce come quella
  di `config_esempio.py` puntata a un secondo cartone (`python
  cartone_satsrouting.py --porta 9078 --percento 0.3`), e riavvio.
  I file del telefono ora stanno sotto `/swap/` (`boltz.js`,
  `instradatore.js`): `/swap-telefono.js` non c'è più.
  DOVE SI LEGGE IL LOCKUP (20 ott 2026, swap-lockup): `SWAP_MEMPOOL_API`
  NON si aggiunge al config del VPS (vuota: mempool.space della rete).
  Sulla VM col regtest di Boltz VA scritta, con l'esplora del regtest, o
  il telefono non ritira (il pannello «⚙️ Stato delle leve» lo dice:
  «Swap: dove si legge il lockup»). La CSP, a swap acceso, aggiunge
  quella sola origine.
  DAL 20 OTT 2026 (swap-senza-api) da quella stessa origine il telefono
  cerca anche il lockup per indirizzo (`/address/<a>/utxo`), la fee
  (`/v1/fees/recommended`) e ci TRASMETTE il ritiro (`POST /tx`): l'esplora
  del regtest sulla VM deve rispondere a tutte e quattro, e con
  `Access-Control-Allow-Origin` (mempool.space dice `*`). Dal 20 ott
  (swap-spesa) anche a `/address/<a>/txs`, `/tx/<id>` e
  `/tx/<id>/outspend/<n>`: da lì il telefono sa chi ha speso il lockup.

- LO SWAP, TAPPA 4: LE LEVE (24 ott 2026; perché in CANTIERI, «Lo
  swap, tappa 4»; com'è fatto in ARCHITETTURA, «LO SWAP, TAPPA 4»). SUL
  VPS NON CAMBIA NIENTE: `SWAP_ATTIVO` resta spenta, e a leva spenta la
  rotta che paga risponde 403 prima di leggere il corpo. Le due leve
  nuove, `SWAP_MAX_SATS_UTENTE_GIORNO` (100.000) e `SWAP_MAX_SATS_GIORNO`
  (200.000), NON si aggiungono al config del VPS: valgono i default del
  codice, e il pannello «⚙️ Stato delle leve» le dice. La tabella
  `swap_pagamenti` nasce da sola alla prima lettura. swap@ non paga:
  nessuna chiave nuova. Sulla VM, la prova sul regtest: COLLAUDO.md §6.
  LA FEE NOSTRA RESTA 0 (26 ott 2026, decisione di Andrea):
  `SWAP_FEE_PERCENTO` NON si aggiunge al config del VPS, e se un giorno
  ci fosse va lasciata a 0. Sopra 0 la fattura dello swap e' meno di
  quel che spetta a chi vende, la porta dei pagamenti paga solo l'esatto,
  e la tappa 4 NON PAGA: ogni swap si ferma col no «fee» (nel journal
  «non si paga — fee»). Il pannello «⚙️ Stato delle leve» lo dice sulla
  riga «Swap: la nostra fee (%)». Controllo, sola riga: `grep -n
  "^SWAP_FEE_PERCENTO" /srv/barattolo/config.py` (atteso: niente, o `= 0`).

- IL CAMBIO LIBERO: LE LEVE (27 ott 2026, cantiere cambio-libero;
  perché in CANTIERI, «Il cambio libero, tappa 1/2/3»; com'è fatto in
  ARCHITETTURA, «IL CAMBIO LIBERO, TAPPA 2» e «TAPPA 3»). SUL VPS NON
  CAMBIA NIENTE finché Andrea non decide: le cinque leve sono SPENTE di
  serie e NON compaiono da sole nel config (`CAMBIO_LIBERO_ATTIVO`
  False, `CAMBIO_LIBERO_SOLO_MODERATORI` True, `CAMBIO_LIBERO_MAX_SATS`
  500.000, `CAMBIO_LIBERO_MAX_AL_GIORNO` 5, `CAMBIO_BTC_LN_ATTIVO`
  False); a `CAMBIO_LIBERO_ATTIVO` spenta la pagina «Cambio» non ha il
  tasto, e le rotte `/api/swap/cambio/*` rispondono 403. Il cancello sta
  SOPRA quello dello swap: senza `SWAP_ATTIVO` (oggi spenta in
  produzione) il cambio non c'è comunque, e a `SWAP_SOLO_MODERATORI =
  True` lo vedono solo i moderatori anche con
  `CAMBIO_LIBERO_SOLO_MODERATORI = False`. La tabella `cambi_liberi`
  nasce da sola alla prima chiamata. I file del telefono sono quelli
  dello swap (`/swap/boltz.js`, `/swap/instradatore.js`, versione
  `SWAP_TELEFONO_VER`): niente da copiare a mano.
  PER ACCENDERE (decisione di Andrea, in quest'ordine): prima
  `SWAP_ATTIVO = True` con le sue regole (sopra, «LO SWAP DAL
  TELEFONO: LE LEVE»), poi `CAMBIO_LIBERO_ATTIVO = True` nel config del
  VPS e riavvio; all'inizio si lascia `CAMBIO_LIBERO_SOLO_MODERATORI`
  a True (Andrea e Alan, cifre piccole), e si apre a tutti SOLO dopo
  il parere MiCA. Il controllo, sola riga: `grep -n "^CAMBIO_"
  /srv/barattolo/config.py` (atteso oggi: niente). Lo stato VIVO sta
  nel pannello «⚙️ Stato delle leve», gruppo dello swap, righe «Cambio
  libero: …».
  ⚠️ `CAMBIO_BTC_LN_ATTIVO` (la strada bitcoin → Lightning) aspettava
  la risposta di Massimo sulla quota partner del submarine e sui limiti
  di chiamate (la domanda l'ha fatta Andrea, 27 ott 2026). MASSIMO HA
  RISPOSTO IL 28 OTT 2026: la quota vale su tutti gli swap e si applica
  alla commissione finale; limiti di chiamate nessuno, solo il minimo e
  il massimo dell'importo. Ora si accende quando decide Andrea, dopo
  `SWAP_ATTIVO` e `CAMBIO_LIBERO_ATTIVO`: il pannello lo dice sulla sua
  riga. Prima dell'accensione,
  sul collaudo: il submarine di SATS Routing vero non è mai stato
  chiamato (solo il cartone), un wallet vero che manda dal link
  `bitcoin:` dentro Telegram, la richiesta incollata dalla WebView, il
  rimborso dallo script su una rete vera (COLLAUDO.md §6).
  PER SPEGNERE: `CAMBIO_LIBERO_ATTIVO = False` (o via la riga) e
  riavvio; i cambi già nati finiscono lo stesso dal telefono (nascita e
  annullo del biglietto non hanno cancello, il ritiro e il rimborso
  sono del telefono con le 12 parole).

- IL P2P SULL'ALTRA RETE: LE LEVE (1 nov 2026, cantiere
  presa-altra-rete, tappa 1: ordine Lightning, chi compra riceve
  on-chain; perché in CANTIERI, «Ricevere on-chain da un ordine P2P
  Lightning col cambio»; com'è fatta in ARCHITETTURA, «CHI COMPRA SU UN
  ORDINE P2P LIGHTNING RICEVE ON-CHAIN»). SUL VPS NON CAMBIA NIENTE: le
  tre leve sono spente di serie e non compaiono da sole nel config
  (`P2P_ALTRA_RETE_ATTIVO` False, `P2P_ALTRA_RETE_SOLO_MODERATORI` True,
  `P2P_ALTRA_RETE_MAX_SATS` 500.000). Il cancello sta SOPRA quello dello
  swap: senza `SWAP_ATTIVO` (oggi spenta) la scelta «₿ On-chain» non
  compare comunque. La tabella `cambi_p2p` nasce da sola. PER ACCENDERE
  (decisione di Andrea, in quest'ordine): `SWAP_ATTIVO = True` con le sue
  regole, poi `P2P_ALTRA_RETE_ATTIVO = True` e riavvio, lasciando
  `P2P_ALTRA_RETE_SOLO_MODERATORI` a True (Andrea e Alan, cifre piccole);
  a tutti solo dopo il parere MiCA. Prima, una prova sul collaudo col
  SATS Routing di cartone. Il controllo, sola lettura: `grep -n
  "^P2P_ALTRA_RETE" /srv/barattolo/config.py` (atteso oggi: niente).
  PER SPEGNERE: via la riga e riavvio; i cambi già nati finiscono dal
  telefono, e la ronda dell'avviso continua a guardarli.
  LA TAPPA 2 (1 nov 2026: sugli scambi P2P on-chain chi compra riceve in
  Lightning) sta dietro la STESSA leva, più `P2P_ONCHAIN_ATTIVO`,
  `CAMBIO_BTC_LN_ATTIVO` e l'on-chain sulla rete di SATS Routing
  (`ONCHAIN_RETE = "mainnet"`): con l'on-chain su signet resta chiusa
  anche a leve accese. Le colonne nuove di `p2p_onchain_ordini` nascono
  da sole al primo avvio.
  LA TAPPA 3 (1 nov 2026: chi prende un ordine on-chain vendendo paga il
  deposito in Lightning) sta dietro la STESSA leva, più
  `P2P_ONCHAIN_ATTIVO` e l'on-chain sulla rete di SATS Routing; non vuole
  `CAMBIO_BTC_LN_ATTIVO`. Niente colonne nuove: i biglietti stanno in
  `cambi_p2p` col nome «oc:<numero>».
  IL CASO 4 (1 nov 2026: vendere su un ordine Lightning avendo solo
  bitcoin) sta dietro la stessa leva più `CAMBIO_BTC_LN_ATTIVO`; non vuole
  l'on-chain di Barattolo. I biglietti in `cambi_p2p` si chiamano
  «presa:<ordine>».

- LA CHIAVE DI BARATTOLO DELL'ON-CHAIN (27 ott 2026, cantiere
  onchain-disputa; com'è fatta in ARCHITETTURA, «LA DISPUTA ON-CHAIN E
  LA CHIAVE DI BARATTOLO SUL VPS»). NASCE DAL PANNELLO, MAI DA UN
  DEPLOY: un admin preme «⛓️ Crea la chiave di Barattolo» nel cassetto
  omonimo, e sul VPS compare `chiavi/onchain-barattolo.json` accanto a `satmarket.db` (la cartella di `BARATTOLO_DIR`, `/root/satmarket`)
  (0600, dell'utente `barattolo`). NIENTE `ONCHAIN_XPUB` nel config
  insieme al file: sarebbero due terze chiavi e il server si ferma.
  IL BACKUP: `deploy/backup-fuori.sh` copia `chiavi/` nell'archivio age
  (pre-deploy e 04:30); il cassetto dice «È nel backup fuori sede del…»
  appena un archivio riuscito viene dopo la nascita. Fino ad allora la
  copia è UNA: il giorno della creazione conviene un backup a mano
  (o un deploy). Verifica in sola lettura, la lancia Andrea:
  `sudo ls -l /root/satmarket/chiavi/` (deve dire `-rw-------`).
  IL RIPRISTINO: dall'archivio (`age -d`), il file `chiavi/` torna
  accanto al database, proprietario `barattolo`, e il server lo rilegge
  da solo. Per firmare A MANO (server perso): le dodici parole del
  file in Sparrow come terzo firmatario di un multisig 2-di-3, con la
  strada scritta nel file (`strada`: `m/48'/1'/0'/2'` su signet,
  `m/48'/0'/0'/2'` su mainnet), coi descrittori degli ordini. Mai in
  chiaro su Telegram o in chat: le parole firmano le dispute.
  ⚠️ IL FILE DICE LA SUA RETE (`rete`, dal 30 ott 2026): con
  `ONCHAIN_RETE` su un'altra rete il server lo rifiuta (503, pannello
  «file illeggibile») e NON torna alla chiave di cartone. Sotto, «L'ON-
  CHAIN IN MAINNET».

- L'ON-CHAIN IN MAINNET: I SATS VERI, SOLO AGLI ADMIN (30 ott 2026,
  cantiere onchain-mainnet, proposta di Alan: «portarlo su main con il
  flag on-chain attivo solo per gli admin, una prova da 5 euro»; perché
  in CANTIERI, «L'on-chain in mainnet»; com'è fatto in ARCHITETTURA,
  «L'ON-CHAIN IN MAINNET: LA RETE È UNA LEVA»). Di serie il codice sta
  su signet e l'on-chain è SPENTO: la mainnet si apre SOLO con le righe
  nel config del VPS, dopo la promozione. L'ORDINE DEI GESTI CONTA,
  perché la chiave di Barattolo nasce sulla rete che il server ha in
  quel momento. Un passo alla volta, col sì di Andrea, ognuno col suo
  risultato incollato (i comandi pronti: docs/DA-FARE-ANDREA.md):
  1) embit sul VPS (sopra, «L'ON-CHAIN, TAPPA 2: EMBIT SUL VPS»): se
     `import embit` non risponde, prima quello;
  2) sola lettura: `grep -n "^ONCHAIN_" /srv/barattolo/config.py` — di
     solito nessuna riga; se c'è `ONCHAIN_RETE` o `ONCHAIN_XPUB` ci si
     ferma e si guarda; e `sudo ls -l /root/satmarket/chiavi/` deve
     dire «No such file»: un file nato su signet là NON vale su mainnet
     (si sposta via, con copia, prima del passo 4);
  3) copia del config, poi le QUATTRO righe in coda (`printf | tee -a`,
     mai nano): `ONCHAIN_RETE = "mainnet"`, `ONCHAIN_ATTIVO = True`,
     `ONCHAIN_MAX_EURO = 10` (il tetto della prova: in codice è 250),
     `ONCHAIN_SOLO_ADMIN = True` (è già il valore del codice: la riga
     dice che è una decisione); il file si rilegge con `ast.parse`;
  4) riavvio del servizio; il pannello «⚙️ Stato delle leve», gruppo
     «⛓️ Pagamento on-chain», deve dire «Rete dell'on-chain: mainnet» e la
     terza chiave in ALLARME («⚠️ di cartone su MAINNET: l'on-chain è
     FERMO»): è il verso giusto, nessun indirizzo nasce;
  5) un admin preme «⛓️ Crea la chiave di Barattolo» (cassetto «Chiave di
     Barattolo» del pannello admin): nasce `chiavi/onchain-barattolo.json`
     con `"rete": "mainnet"` e il conto `m/48'/0'/0'/2'`; il pannello
     delle leve dice «sul VPS (impronta …) — ⚠️ non ancora in un backup
     fuori sede»: SUBITO un backup a mano (`backup-fuori.sh`) o un deploy,
     finché la copia è una sola — su mainnet quella chiave vale sats;
  6) Andrea e Alan aprono la Mini App: l'on-chain si accende da solo con
     la xpub di MAINNET (le tpub del collaudo non valgono qui), e nel
     Profilo → «⛓️ On-chain» la scheda Tecnico dice in rosso «Rete
     Bitcoin (mainnet): i sats sono veri»;
  7) la prova: un oggetto di Alan sotto i 10 €, Andrea sceglie ⛓️ alla
     cassa, paga da un wallet vero su un `bc1q`, UNA conferma (dieci
     minuti o più: su mainnet il margine per la rete lo decide la
     tariffa di mempool.space), poi «🔓 Libera i sats», e il telefono
     di Alan co-firma alla prima apertura. L'explorer:
     `https://mempool.space/address/<bc1q…>`.
  PER TORNARE INDIETRO: `ONCHAIN_ATTIVO = False` (o via la riga) e
  riavvio: le rotte on-chain tornano 404 e un ordine già pagato resta
  nel suo 2-di-3 finché due telefoni non firmano (la leva spegne la
  cassa, non le chiavi). `ONCHAIN_RETE` NON si rimette su signet con
  ordini di mainnet aperti: la chiave di Barattolo sul VPS è di
  mainnet e su signet il server la rifiuterebbe. Verifica in sola
  lettura: `grep -n "^ONCHAIN_" /srv/barattolo/config.py` e il pannello.

- L'ON-CHAIN, TAPPA 2: EMBIT SUL VPS, PRIMA DELLA PROMOZIONE (20 ott
  2026, cantiere onchain-tappa2; perché in CANTIERI, «L'indirizzo
  dell'ordine on-chain»; com'è fatto in ARCHITETTURA, «IL PAGAMENTO
  ON-CHAIN, TAPPE 1-2»). SUL VPS LA LEVA NON SI TOCCA: `ONCHAIN_ATTIVO`
  resta spenta (nessuna riga nuova nel config), e a leva spenta le
  rotte `/api/onchain/*` sono 404 prima di chiedere embit. Il codice
  della tappa 2 parte anche SENZA embit (le rotte che fanno i conti
  direbbero 503); il pacchetto si mette PRIMA della promozione perché
  il pannello «⚙️ Stato delle leve» dica «Libreria del 2-di-3 (embit)»
  accesa e il giorno della leva non ci sia un passo in più.
  ⚠️ NON SI LANCIA FINCHÉ ANDREA NON LO DICE (sua regola, 20 ott 2026).
  Un passo alla volta, ognuno col suo risultato incollato:
  1) quale Python fa girare il servizio, in sola lettura:
     `systemctl show -p ExecStart barattolo --no-pager`
     — il primo percorso dopo `path=` è l'interprete (lo chiamo PY);
  2) c'è già? `sudo -u barattolo PY -c "import embit; print('embit c è')"`
     — se lo dice, ci si ferma qui;
  3) di chi è l'ambiente (lo stesso calco del seguace del collaudo):
     `stat -c %U "$(dirname "$(dirname PY)")"` — lo chiamo PADRONE;
     poi la versione della lista, con QUELL'interprete e come QUEL
     padrone (così i file nuovi restano suoi, come gli altri pacchetti
     del servizio — le righe di coincurve, cryptography e pillow qui
     sopra): `sudo -u PADRONE PY -m pip install embit==0.8.0`
     — se pip risponde «externally-managed-environment» FERMATI e
     riferisci: vuol dire che PY è il Python di sistema e la strada si
     decide insieme, non con `--break-system-packages` a occhio;
  4) il controllo: `sudo -u barattolo PY -c "from embit import bip32; from embit.descriptor import Descriptor; print('embit ok')"`.
  NIENTE RIAVVIO: lo fa il deploy della promozione, e da quel momento il
  pannello dice «Libreria del 2-di-3 (embit)» accesa. Il commit della
  tappa tocca `.github/workflows/prove.yml` (la riga pip della CI): dopo
  la promozione si guarda `git ls-remote origin refs/heads/pronto
  refs/heads/main`, e se `pronto` resta indietro lo sposta Andrea.
  TORNARE INDIETRO: `sudo -u PADRONE PY -m pip uninstall embit` (il
  server riparte lo stesso, con le rotte on-chain a 503).

- L'INDIRIZZO DELLA QUOTA: swap@barattolo.store (19 ott 2026; perché in
  CANTIERI, «L'indirizzo della quota: swap@barattolo.store»; com'è fatto
  in ARCHITETTURA, «L'INDIRIZZO DELLA QUOTA»). Dove SATS Routing manda a
  fine mese la quota di Barattolo sugli swap. Separato da zap@: wallet
  LNbits SUO («swap»), tetto per pagamento 2.000.000 sats
  (`SWAP_INDIRIZZO_MAX_SATS`; fino al 20 ott 2026 si chiamava
  `SWAP_MAX_SATS`, nome che ora e' SOLO il tetto di uno swap dei
  venditori), niente zap Nostr, e a ogni pagamento un avviso nel
  gruppo degli admin, stanza 📊 Riepiloghi: «🔄 Arrivati N sats su
  swap@barattolo.store, <giorno> alle <ora>». Nel codice nasce SPENTO:
  finché non lo si accende,
  `https://barattolo.store/.well-known/lnurlp/swap` risponde 404.
  STATO: sul VPS è ACCESO dal 20 ott 2026, e provato quel giorno con
  una fattura vera da 21 sats (parola di Andrea).
  PER ACCENDERLO, DOPO IL DEPLOY, in quest'ordine:
  1) IL WALLET «swap», SUL PC: il pannello di LNbits del nodo come per
     zap@ (`ssh -N -L 5001:127.0.0.1:5001 root@VPS` in un terminale,
     poi `http://127.0.0.1:5001` nel browser, login «LNbits nodo» in
     KeePass). Con lo STESSO utente della cassaforte: «Add a new
     wallet», nome `swap`. Dentro il wallet nuovo, «Node URL, API keys
     and API docs»: si copia la «Invoice/read key» del wallet «swap» —
     SOLO quella, e NON quella del wallet «zap» (con la stessa chiave
     l'indirizzo vale spento, ed è voluto). La «Admin key» non si copia.
  2) IL CONFIG, SUL VPS, UN COMANDO ALLA VOLTA, col `read -s` come le
     chiavi del codice partner (qui sotto, «LE CHIAVI DEL CODICE PARTNER
     DI SATS ROUTING»; riscritto il 20 ott 2026): la invoice key la
     chiede il terminale SENZA mostrarla, non finisce nella history (il
     comando contiene solo il nome della variabile) e non sta negli
     argomenti di nessun processo (`printf` è un comando interno di
     bash, e il testo arriva a `sudo tee` dallo stdin).
     a) la copia di riserva:
        `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-swap-indirizzo`
     b) le due righe non ci sono già (deve dire `0`):
        `sudo grep -c "^SWAP_LNBITS_INVOICE_KEY\|^SWAP_INDIRIZZO_ATTIVO" /srv/barattolo/config.py`
        (le altre righe `SWAP_` — `SWAP_ATTIVO`, `SWAP_REFERRAL_ID`… —
        sono lo swap dei venditori, un'altra cosa: non si toccano e qui
        non si guardano nemmeno, si contano solo queste due)
     c) la invoice key del wallet «swap», in una riga sola (chiede prima
        la password di sudo, poi la chiave, che non si vede mentre si
        incolla):
        `sudo -v && read -rsp "Invoice key del wallet swap: " K && echo && if [ -z "$K" ]; then echo "Vuota: non scrivo niente"; elif [[ "$K" == *'"'* || "$K" == *"'"* || "$K" == *'\'* ]]; then echo "Contiene virgolette o barre: non scrivo niente, chiedi a Claude"; else printf '\nSWAP_LNBITS_INVOICE_KEY = %s%s%s\n' '"' "$K" '"' | sudo tee -a /srv/barattolo/config.py > /dev/null && echo "Scritta"; fi; unset K`
        Deve dire «Scritta». (Il formato compone le virgolette a parte
        apposta: una riga di documento col nome della chiave, l'uguale
        e una virgoletta attaccata è la forma che lo scanner dei segreti
        della CI prende per una chiave vera.)
     d) la leva:
        `printf 'SWAP_INDIRIZZO_ATTIVO = True\n' | sudo tee -a /srv/barattolo/config.py > /dev/null`
     e) il file si legge ancora (deve dire `ok`):
        `sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"`
     f) le due righe ci sono, senza mostrarle (deve dire `2`):
        `sudo grep -c "^SWAP_LNBITS_INVOICE_KEY\|^SWAP_INDIRIZZO_ATTIVO" /srv/barattolo/config.py`
     Nient'altro: il tetto di serie è 2.000.000 (`SWAP_INDIRIZZO_MAX_SATS
     = …` solo per cambiarlo), l'indirizzo di LNbits è quello del nodo.
     Una chiave incollata male: la copia di riserva al suo posto
     (`sudo cp -p /root/config.py.prima-swap-indirizzo /srv/barattolo/config.py`)
     e si rifà dal passo b). La invoice key non si scrive MAI in chat
     (nemmeno con Claude), su GitHub o in un log; mai `cat`, `sed -n` o
     `grep -A/-B/-C` sul config.
  3) IL RIAVVIO: `sudo systemctl restart barattolo`.
  4) IL JOURNAL, subito dopo:
     `journalctl -u barattolo -n 120 --no-pager | grep "Indirizzo della quota"`
     — «🔄 Indirizzo della quota: swap@barattolo.store ACCESO — fino a
     2.000.000 sats a pagamento, niente zap Nostr» è il verde; «⚠️
     SWAP_INDIRIZZO_ATTIVO e' True ma manca SWAP_LNBITS_INVOICE_KEY (o
     e' quella del wallet degli zap)» vuol dire chiave non letta, o
     copiata dal wallet sbagliato.
  5) IL CITOFONO, da qualunque computer:
     `curl -s https://barattolo.store/.well-known/lnurlp/swap` — un JSON
     con `"tag":"payRequest"`, `"maxSendable":2000000000` (in
     MILLIsatoshi) e SENZA `allowsNostr`. Un `{"status":"ERROR"…}` vuol
     dire spento.
  6) UNA FATTURA DI PROVA. ⚠️ È LA PRIMA FATTURA VERA di swap@: prima
     del push è stato provato tutto con un LNbits di cartone. Sul VPS
     si tiene aperto `journalctl -u barattolo -f | grep "swap@"`, poi da
     un wallet si mandano 21 sat a `swap@barattolo.store` (o si chiede
     la fattura a mano:
     `curl -s "https://barattolo.store/api/lnurl/swap?amount=21000"` e
     si paga la `pr`). NEL JOURNAL, in ordine: «🔄 swap@: fattura da 21
     sats, abcd1234…» e, entro una decina di secondi dal pagamento,
     «🔄 swap@: arrivati 21 sats, fattura abcd1234…». NEL GRUPPO DEGLI
     ADMIN, stanza 📊 Riepiloghi, l'avviso con importo e ora. In `/admin`
     la card «🔄 Quota SATS Routing» col saldo del wallet «swap».
     Se il journal dice «⚠️ swap@: fattura non coniata (…)»: LNbits o il
     ponte sono giù, o la chiave è sbagliata (401); «non porta
     l'impronta» è lo stesso caso di zap@ (si spegne la leva e si
     riporta la riga).
  7) LA LIQUIDITÀ, PRIMA DI DARE L'INDIRIZZO: un pagamento entra solo se
     i canali del nodo hanno abbastanza spazio IN ENTRATA. Si guarda
     `/canali` nel bot (solo admin, sola lettura): la colonna «loro» di
     ogni canale è quanto può ARRIVARE da lì. Un pagamento grosso che
     chi paga non spezza in più parti deve stare tutto in UN canale;
     spezzato, si somma. Se la quota attesa supera lo spazio in entrata,
     si sposta fuori il saldo prima (sotto).
  8) SOLO ADESSO L'INDIRIZZO A SATS ROUTING: Andrea lo comunica a
     Massimo (`swap@barattolo.store`), accanto al codice partner.
  COME SI SPOSTANO I SATS: a mano, dal pannello di LNbits — wallet
  «swap» > «Send». Il server non può farlo (sola invoice key). La quota
  è un RICAVO del mercatino: conta nei conti dei ricavi netti (la parte
  di Alan), e per questo sta in un wallet suo.
  PER SPEGNERLO: `SWAP_INDIRIZZO_ATTIVO = False` (o via la riga) e
  riavvio; il citofono torna 404 (zap@ non se ne accorge). Lo stato VIVO
  sta nel pannello «⚙️ Stato delle leve», gruppo «🔄 Indirizzo della
  quota SATS Routing».

- L'AVVISO DEI DM NOSTR (11 ott 2026; perché in CANTIERI, «L'avviso dei
  DM a Barattolo su Nostr»; com'è fatto in ARCHITETTURA, «L'AVVISO DEI
  DM A BARATTOLO»). Quando qualcuno scrive un DM al profilo Nostr di
  Barattolo, ai moderatori (`ADMIN_IDS`, la chat degli altri avvisi)
  arriva «📩 Nuovo DM su Nostr da <nome> (<npub abbreviata>)» col
  bottone «🟣 Apri in un client»; dal 15 ott 2026 l'avviso dice anche
  il genere (chat «lo trovi in Amethyst», mail Nostr «es. Nmail», un
  altro tipo col suo numero). Il testo del messaggio non c'è mai: il
  server ne legge il solo tipo, in memoria (ARCHITETTURA, «DEL
  MESSAGGIO SI LEGGE IL TIPO»). Nessun passo nuovo sul VPS.
  NASCE SPENTO, e un deploy non lo accende. PER ACCENDERLO, sul VPS:
  1) si guarda che la riga non ci sia già:
     `grep -n "AVVISO_DM" /srv/barattolo/config.py`
  2) si aggiunge in fondo a `/srv/barattolo/config.py` UNA riga:
     `AVVISO_DM_NOSTR = True`
     I relay sono già quelli giusti nel codice — `wss://nos.lol` e
     `wss://relay.primal.net` (dal 12 ott 2026: prima c'era
     relay.damus.io, vedi sotto «IL KIND 10050») —, la lista DM di
     Barattolo (il suo kind 10050). Solo se un giorno quella lista
     cambia si aggiunge anche `AVVISO_DM_NOSTR_RELAY = ["wss://…",
     "wss://…"]` (al massimo sei: ognuno è un thread). ⚠️ Se quella
     riga nel config del VPS C'È GIÀ, vince lei sul codice: va cambiata
     lì, o tolta.
  3) si riavvia: `sudo systemctl restart barattolo`
  4) si guarda il journal:
     `journalctl -u barattolo --since "2 min ago" | grep "Avviso DM"`
     Devono esserci «📩 Avviso DM Nostr ACCESO: ascolto wss://nos.lol ·
     wss://relay.primal.net per <16 cifre>…» e, entro qualche secondo,
     una riga «📩 Avviso DM: in ascolto su <relay>» per ognuno dei due.
     Nessuno dei due chiede l'autenticazione; un relay che la chiede
     esce con «(autenticato, NIP-42)» in coda.
  5) LA PROVA: da un client Nostr con UN'ALTRA chiave si manda un DM
     alla npub di Barattolo. Entro una ventina di secondi arriva
     l'avviso su Telegram. Un secondo DM dalla stessa chiave entro
     dieci minuti NON avvisa subito: esce a pausa finita, in una riga
     col conto («2 nuovi DM su Nostr da …»).
  COSA DICE IL JOURNAL, e cosa vuol dire:
   · «📩 Avviso DM Nostr: spento (AVVISO_DM_NOSTR)»: la leva è False, o
     la riga non c'è.
   · «⚠️ AVVISO_DM_NOSTR accesa ma manca la chiave…: vale SPENTO»:
     manca `NOSTR_NSEC_PIATTAFORMA`, o `websocket-client`, o la lista
     dei relay è storta.
   · «📩 Avviso DM: <relay> CADUTO (…): riprovo da solo»: quel relay
     non risponde. Si riprova da solo, con un'attesa che cresce fino a
     un minuto, e l'altro relay continua a portare la posta. Una riga
     per caduta, non una per tentativo; quando torna: «in ascolto su
     <relay> dopo N tentativi».
   · «📩 Avviso DM: in ascolto su <relay> (autenticato, NIP-42)»: quel
     relay ha chiesto chi siamo e il server ha risposto firmando la sua
     sfida con la chiave della piattaforma. Non c'è niente da fare: lo
     rifà da solo a ogni riconnessione. (relay.damus.io l'ha chiesto
     alla prima accensione, l'11 ott 2026, e alla nostra risposta ha
     detto «relay needs serviceUrl to be configured before AUTH can
     work»: un difetto suo. È uscito dalla lista il 12 ott.)
   · «📩 Avviso DM: <relay> RIFIUTA (…): riprovo fra un'ora»: il relay
     ha detto NO anche dopo l'autenticazione (o ha respinto la firma, o
     la chiede senza mandare la sfida). Fra parentesi c'è la sua frase.
     È UNA riga sola: i tentativi dopo, uno all'ora, non scrivono più
     niente finché non cambia qualcosa. Gli altri relay continuano a
     portare la posta. Se resta così per giorni: quel relay non ci
     vuole, e si toglie dalla lista (`AVVISO_DM_NOSTR_RELAY` nel config,
     e dal kind 10050 di Barattolo, che è la lista che i client
     leggono per sapere DOVE scriverci).
   · «… CADUTO (RuntimeError: sottoscrizione chiusa dal relay: …)» con
     un motivo che NON parla di autenticazione (un rate-limit, un
     filtro non ammesso): resta una caduta, e si riprova ogni minuto.
   · «⚠️ Avviso DM: il filo di <relay> è FERMO…» e «💥 … MORTO: riparte
     adesso»: la guardia ha rifatto un filo. Non c'è niente da fare.
   · «📩 Avviso DM: un avviso ai moderatori»: è partito un avviso. Non
     dice da chi né cosa: nel journal non finiscono MAI il testo di un
     messaggio né chi l'ha scritto.
  I LIMITI stanno nel codice, non nel config: un avviso per mittente
  ogni 10 minuti (`AVVISO_DM_PAUSA_MITTENTE_S`); 6 avvisi in mezz'ora in
  tutto (`AVVISO_DM_TETTO`, `AVVISO_DM_FINESTRA_S`), oltre i quali esce
  un riassunto «📩 N nuovi DM su Nostr da M mittenti», senza nomi né
  bottone.
  COSA NON FA. Non mostra i DM e non risponde: si leggono in un client,
  con la chiave della piattaforma. Non avvisa della posta arrivata
  PRIMA dell'avvio del server — e quindi nemmeno di un DM arrivato nei
  secondi di un riavvio o di un deploy: lo stato vive in memoria, e a
  ogni avvio la posta che trova sui relay è «già vista». Non avvisa dei
  DM che Barattolo manda. Il bottone apre su njump.me il PROFILO di chi
  ha scritto, e da lì il client: un link che apra «quel messaggio» in
  ogni client non esiste.
  LO STATO VIVO sta nel pannello «⚙️ Stato delle leve», gruppo «🔔
  Avvisi ai moderatori»: la leva, e per ogni relay la sua parola —
  `connesso`, `giu`, `rifiutato`, `parte`.
  PER SPEGNERLO: `AVVISO_DM_NOSTR = False` (o via la riga) e riavvio.

- IL KIND 10050 DI BARATTOLO, LA LISTA DEI RELAY DEI DM (12 ott 2026;
  perché in CANTIERI, «Il secondo relay dei DM»). Il kind 10050 è il
  biglietto in cui un profilo Nostr dice ai client DOVE scrivergli i DM
  (NIP-17): senza, chi scrive alla npub riceve «DM inbox relay not
  found». DEVE DIRE GLI STESSI RELAY CHE IL SERVER ASCOLTA
  (`AVVISO_DM_NOSTR_RELAY`): un relay nel biglietto e non nella lista
  è posta che arriva e nessuno sente; uno nella lista e non nel
  biglietto è un filo che ascolta il vuoto.
  OGGI: `wss://nos.lol` e `wss://relay.primal.net`. MAI
  `relay.barattolo.store` (accetta solo le chiavi in whitelist, e una
  busta 1059 la firma una chiave usa-e-getta) e MAI un relay che dà i
  DM solo a chi si autentica senza averlo provato: relay.damus.io
  chiede l'AUTH e poi risponde «relay needs serviceUrl to be configured
  before AUTH can work».
  PER CAMBIARLO lo fa Andrea dal WSL, dove sta la chiave, con `nak`
  (v0.21.0), un comando alla volta. PRIMA il deploy del server con la
  lista nuova (journal: «in ascolto su» per ogni relay), POI il
  biglietto: nos.lol sta in tutt'e due le liste, quindi nel mezzo non
  si perde niente.
  D0) la chiave PUBBLICA, dalla npub (senza rete):
      `cd ~ && mkdir -p dm10050 && cd dm10050`
      `HEX=$(nak decode npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy)`
      `echo $HEX` — comincia per `2e7afe3f` e finisce per `fe831b`.
  D1) CONTROLLO PRIMA — cosa c'è adesso:
      `nak req -k 10050 -a $HEX wss://nos.lol wss://relay.primal.net wss://relay.damus.io < /dev/null`
      Una riga, coi tag `relay` di oggi.
  D2) LA FIRMA A SCHERMO SPENTO, senza nessun relay nel comando:
      `read -rs NOSTR_SECRET_KEY` — si incolla la nsec e Invio: non si
      vede niente, ed è giusto così.
      `export NOSTR_SECRET_KEY`
      `nak event -k 10050 -t relay=wss://nos.lol -t relay=wss://relay.primal.net -c '' < /dev/null > firmato.json`
      `unset NOSTR_SECRET_KEY`
  D3) CONTROLLO CHI FIRMA — ⚠️ senza chiave `nak` firma lo stesso, con
      una chiave «della macchina»: per questo si guarda PRIMA di
      pubblicare.
      `python3 -c "import json;e=json.load(open('firmato.json'));print('OK: firmato da Barattolo' if e['pubkey']=='$HEX' else 'NO: NON PUBBLICARE', e['kind'], [t[1] for t in e['tags']])"`
      Deve dire «OK: firmato da Barattolo 10050» e i due relay.
      `nak verify < firmato.json && echo firma valida`
  D4) PUBBLICA il già firmato (questo comando non rifirma):
      `nak event wss://nos.lol wss://relay.primal.net wss://relay.damus.io wss://nostr.mom < firmato.json`
      Per ogni relay «publishing to … success.». Va anche a damus e a
      nostr.mom: non per riceverci i DM, ma perché è lì che i client
      cercano il biglietto, e quello vecchio va sostituito ovunque.
  D5) CONTROLLO DOPO, un relay alla volta:
      `nak req -k 10050 -a $HEX wss://nos.lol < /dev/null`
      `nak req -k 10050 -a $HEX wss://relay.primal.net < /dev/null`
      `nak req -k 10050 -a $HEX wss://relay.damus.io < /dev/null`
      Ognuno deve dare UNA riga coi due relay nuovi (un 10050 nuovo
      sostituisce il vecchio: è un evento «replaceable»).
  I comandi sono stati provati come sono scritti la notte fra l'11 e
  il 12 ott 2026, su un
  `nak serve` locale e con una chiave usa-e-getta (la trappola del D3
  compresa); D1 anche sui relay veri, che è una lettura.
  PER SCEGLIERE UN RELAY NUOVO si guarda, in sola lettura: che risponda
  EOSE a `{"kinds":[1059],"#p":[<noi>]}` senza chiedere l'AUTH (o che
  la sua AUTH funzioni davvero); che tenga buste 1059 di chiavi
  DIVERSE e anche vecchie di mesi (`{"kinds":[1059],"until":…}`), che è
  la prova che le accetta da chiunque e non le butta; il NIP-11
  (`payment_required`, `auth_required`); i tempi su tre giri. La
  riserva misurata quella notte: `wss://nostr.oxtr.dev`.

- I CERTIFICATI DEI RELAY (20 ott 2026, cantiere certificati-relay;
  perché in CANTIERI, «I certificati dei relay si verificano»). Ogni
  websocket verso un relay — server e script — verifica il certificato
  sul nome del relay, con le CA del sistema (`websocket-client` non usa
  certifi: sul VPS serve il pacchetto `ca-certificates`, che c'è). Un
  certificato non valido = relay irraggiungibile, come un relay muto.
  NESSUN PASSO SUL VPS per il deploy. PRIMA DI UN RELAY NUOVO in
  `RELAY_NOSTR`, `MOSTRO_RELAY`, `AVVISO_DM_NOSTR_RELAY` (sola lettura:
  solo la stretta di mano TLS, nessun messaggio Nostr; il nome al posto
  di RELAY):
  `python3 -c 'import ssl,socket;h="RELAY";t=ssl.create_default_context().wrap_socket(socket.create_connection((h,443),timeout=8),server_hostname=h);print("OK",h,t.getpeercert()["notAfter"])'`
  — «OK» e la scadenza; un errore vuol dire che il server non lo userà.
  Il controllo del 20 ott 2026: `ca-certificates` installato, e tutti OK
  (relay.barattolo.store scade il 5 dic 2026 e lo rinnova Caddy;
  relay.primal.net, relay.nostr.net, nostr.oxtr.dev, nos.lol,
  relay.mostro.network).
  COSA DICE IL JOURNAL: «🔐 Relay <indirizzo>: certificato non valido
  (<motivo>), non lo uso», al più una volta all'ora per relay. Il motivo
  è quello di OpenSSL: «certificate has expired» (il relay non ha
  rinnovato), «self-signed certificate», «Hostname mismatch» (il
  certificato è per un altro nome), «unable to get local issuer
  certificate» (sul VPS mancano le CA: `dpkg -s ca-certificates`). Se è
  uno dei NOSTRI relay va guardato subito: per il server quel relay è
  giù finché il certificato non torna valido. Su relay.barattolo.store:
  il certificato lo prende Caddy (deploy/RIPRISTINO-RELAY.md).
  Gli script (`importa_nostr.py`, `censimento_nostr.py`,
  `presenta_release.py`) fanno lo stesso: un relay col certificato
  rotto compare fra i «non raggiungibile», o con la riga 🔐.

- GLI AVVISI A CHI NON HA UN 10050 (20 ott 2026, cantiere
  avvisi-nostr-arrivano; perché in CANTIERI, «Gli avvisi Nostr
  arrivano»; com'è fatto in ARCHITETTURA, «GLI AVVISI A CHI ENTRA SOLO
  DA NOSTR»). Chi entra SOLO da Nostr e non pubblica il kind 10050
  riceve gli avvisi come busta NIP-17 sui relay di LETTURA del suo
  10002 più i primi quattro di `RELAY_NOSTR`, e ognuno resta anche in
  «📬 I tuoi avvisi» dentro Barattolo. NESSUN PASSO SUL VPS per il
  deploy: la tabella `avvisi_app` e le tre colonne `relay_dm*` di
  `utenti` nascono da sole all'avvio. Chi ha Telegram non vede niente
  di nuovo.
  COSA DICE IL JOURNAL:
   · «📭 DM Nostr a <16 cifre>…: nessun 10050, busta NIP-17 su N/M relay
     di riserva: nel suo client potrebbe non comparire»: un avviso a chi
     non ha il 10050. È NORMALE, e c'è a ogni avviso: dice che il DM è
     partito largo e che l'avviso sta anche in 📬. «su 0/M» vuol dire
     che nessun relay l'ha preso (segue la ⚠️ di sempre, «nessun relay
     l'ha accettato»): l'avviso c'è solo dentro Barattolo.
   · «📭 DM Nostr a …: 10050 non letto (relay muti), …»: nessuno dei
     nostri relay ha risposto alla domanda. Si spedisce alla riserva lo
     stesso, e si richiede fra cinque minuti.
   · «📭 DM Nostr a …: 10050 senza relay raggiungibili, …» (dal 20 ott
     2026, cantiere filtro-10050): il suo 10050 c'è ma contiene solo
     indirizzi che il server non tocca — non wss://, localhost, una rete
     privata, un .local, un .onion (es. il relay sul telefono di Citrine,
     `ws://localhost:4869`). Si va alla riserva come senza 10050, e
     all'ingresso gli compare il cartello. La riga di /api/me dice
     «ha un 10050 coi soli relay che da qui non si raggiungono».
   · «📭 L'utente -N (solo Nostr) non pubblica un 10050: …»: l'ha visto
     la sua /api/me (al più una volta al giorno). Una riga quando lo si
     scopre, non a ogni apertura: è anche il momento in cui gli compare,
     UNA volta, il cartello «Non riceverai i messaggi su Nostr».
   · «⚠️ Avviso in app non salvato per l'utente -N: …» e «⚠️ Relay dei
     messaggi non controllati per l'utente -N: …»: un guasto (database
     occupato, una npub storta). L'avviso Nostr parte lo stesso.
  QUANTI SONO, in sola lettura (stampano solo numeri):
   `sudo -u barattolo sqlite3 -readonly /srv/barattolo/dati/satmarket.db "SELECT relay_dm, COUNT(*) FROM utenti WHERE tg_id<0 GROUP BY relay_dm"`
   — `si`/`no` = guardato, vuoto = non è ancora entrato dopo il deploy
   (o i relay non hanno risposto).
   `sudo -u barattolo sqlite3 -readonly /srv/barattolo/dati/satmarket.db "SELECT COUNT(DISTINCT tg_id) AS persone, COUNT(*) AS avvisi, SUM(letto=0) AS non_letti FROM avvisi_app"`
   `journalctl -u barattolo --since "7 days ago" | grep -c "📭 DM Nostr a"`
  I RELAY SCRITTI DA UN UTENTE SI RISOLVONO PRIMA DI BUSSARE (20 ott
  2026, cantiere relay-risolti): il server chiede il nome al DNS una
  volta, e se un indirizzo è locale o privato quel relay non si tocca (la
  riga 📭 conta solo i relay che hanno preso la busta). Nessun passo sul
  VPS, nessuna riga nuova nel journal.
  I .ONION SI SCARTANO perché dal server i DM partono diretti (Tor sul
  VPS serve al sito .onion in entrata). Se un giorno gli invii passassero
  da Tor, il giudice `relay_esterno` va cambiato. Per guardare, in sola
  lettura, che il servizio non abbia un proxy:
  `systemctl show barattolo -p Environment`
  — non deve comparire niente con `proxy` o `socks`.
  LA LEVA `DM_NIP04_RISERVA` (il vecchio DM NIP-04 di riserva) NASCE
  SPENTA, e un deploy non la accende. Accesa, a chi non ha il 10050
  parte ANCHE un DM kind 4 sugli stessi relay: Primal, Damus e altri lo
  leggono senza la lista. IL PREZZO: il testo è cifrato, ma sul relay
  resta in chiaro che la chiave di Barattolo ha scritto a quella npub, e
  quando — chiunque legga il relay sa che è un cliente di Barattolo e
  quando ha un ordine o una chat che si muove. La busta NIP-17 nasconde
  tutte e tre le cose. PER ACCENDERLA (decisione di Andrea, un comando
  alla volta):
  1) `grep -n "DM_NIP04_RISERVA" /srv/barattolo/config.py` — deve non
     stampare niente (se c'è già, vince lei: si cambia quella).
  2) si aggiunge in fondo a `/srv/barattolo/config.py` UNA riga:
     `DM_NIP04_RISERVA = True`
  3) `sudo systemctl restart barattolo`
  4) al primo avviso a chi non ha il 10050 la riga 📭 porta in coda
     «, NIP-04 su N»: `journalctl -u barattolo --since "1 hour ago" | grep "NIP-04 su"`
  PER SPEGNERLA: la riga a `False` (o via) e lo stesso riavvio.

- I RELAY DI BARATTOLO: LA LISTA (`RELAY_NOSTR`) E IL KIND 10002 (15
  ott 2026, cantiere relay-di-barattolo; perché in CANTIERI, «I relay
  di Barattolo»). La lista dei relay dove Barattolo pubblica e legge
  (annunci, ritiri, zap, reputazione, profili, la copia del profilo
  P2P) è nel codice (`RELAY_DI_SERIE`) MA SUL VPS VINCE LA RIGA
  `RELAY_NOSTR` del config (riga 84 il 15 ott, su più righe): il
  deploy da solo non cambia niente. La lista nuova, in quest'ordine
  (l'ordine conta: il primo è il relay suggerito ai client, i primi
  quattro ricevono i DM di chi non ha un 10050):
  `["wss://relay.primal.net", "wss://relay.nostr.net", "wss://nostr.oxtr.dev", "wss://nos.lol", "wss://relay.mostro.network", "wss://relay.barattolo.store"]`
  NON si toccano qui: `AVVISO_DM_NOSTR_RELAY` (il 10050, nos.lol e
  primal), `MOSTRO_RELAY*`, `RELAY_NOSTR_IMPORT`.
  ⚠️ LA REGOLA DI ANDREA (13 ott 2026): sul config solo comandi che
  stampano la riga per NOME, mai le righe intorno.
  SUL VPS, `root@satmarket`, DOPO il deploy del codice:
  R1) cosa c'è adesso, il solo valore (ast su quel solo assegnamento):
      `python3 -c "import ast;t=ast.parse(open('/srv/barattolo/config.py').read());print([ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(getattr(x,'id',None)=='RELAY_NOSTR' for x in n.targets)])"`
  R2) la copia: `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-dei-relay`
  R3) la riscrittura delle SOLE righe dell'assegnamento (le trova ast,
      anche su più righe; il resto del file non si legge a schermo):
      ```
      sudo python3 - <<'EOF'
      import ast
      p = "/srv/barattolo/config.py"
      righe = open(p).read().split("\n")
      a = [n for n in ast.parse("\n".join(righe)).body if isinstance(n, ast.Assign) and any(getattr(x, "id", None) == "RELAY_NOSTR" for x in n.targets)]
      assert len(a) == 1, "RELAY_NOSTR non c'e' o c'e' due volte: mi fermo"
      righe[a[0].lineno - 1:a[0].end_lineno] = ['RELAY_NOSTR = ["wss://relay.primal.net", "wss://relay.nostr.net", "wss://nostr.oxtr.dev", "wss://nos.lol", "wss://relay.mostro.network", "wss://relay.barattolo.store"]']
      open(p, "w").write("\n".join(righe))
      print("riscritte le righe", a[0].lineno, "-", a[0].end_lineno)
      EOF
      ```
  R4) di nuovo R1 (deve dire la lista nuova) e il controllo:
      `sudo -u barattolo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('config ok')"`
  R5) `sudo systemctl restart barattolo`; il pannello «⚙️ Stato delle
      leve» mostra la lista nuova alla voce «Relay Nostr».
  IL KIND 10002 (NIP-65) è il biglietto con cui Barattolo dice ai
  client DOVE scrive: la stessa lista, coi relay del 10050 senza
  etichetta e gli altri «write». Lo firma AMBER sul telefono, account
  Barattolo: la nsec non passa da nessuna parte. Si pubblica DOPO R5,
  così biglietto e server dicono la stessa cosa. Dal WSL del PC (dove
  c'è nostr-tools, in `~/wdk-prova`), un comando alla volta:
  K1) i due file in una cartella sotto `~/wdk-prova`:
      `mkdir -p ~/wdk-prova/relay10002 && cd ~/wdk-prova/relay10002`
      `cp /mnt/c/Users/Andrea/Documents/GitHub/satmarket/deploy/nostr/relay-di-barattolo.mjs /mnt/c/Users/Andrea/Documents/GitHub/satmarket/vendor/qrcode.js .`
      (dopo un `git pull` del checkout: lo script è quello di main).
  K2) LA PROVA A SECCO, nessun relay toccato: `node relay-di-barattolo.mjs prova`
      — una 10002 NON firmata, coi sei relay e le etichette.
  K3) COSA C'È OGGI, in sola lettura: `node relay-di-barattolo.mjs guarda`
      — il 15 ott: nessuna 10002 sui relay nuovi, una VECCHIA del 17
      lug 2026 su relay.nostr.net (nostr.mom, nos.lol,
      nostr.bitcoiner.social), il 10050 del 12 ott ovunque.
  K4) LA FIRMA: `node relay-di-barattolo.mjs firma`
      — stampa un QR (e sotto il link `nostrconnect://`). In Amber:
      account BARATTOLO, approvazione MANUALE; si inquadra il QR; si
      approva il collegamento e poi la firma del SOLO kind 10002 (è
      l'unico permesso che lo script chiede). Lo script controlla che
      a firmare sia stata la chiave di Barattolo, che sia una 10002
      con la lista giusta e che la firma regga; altrimenti «NON
      PUBBLICO» e si ferma. Poi chiede «Pubblico su 7 relay? (si/no)»:
      `si` e Invio. Pubblica sui sei della lista e su purplepag.es
      (dove i client cercano le 10002 altrui); ogni relay ✓ o ✗.
  K5) il controllo: di nuovo `node relay-di-barattolo.mjs guarda` —
      la 10002 nuova su ogni relay che l'ha presa (sostituisce la
      vecchia: è «replaceable»). Poi in Amber si toglie l'app
      «Barattolo — lista relay».
  ⚠️ NMAIL (e ogni client che al login apre «Relay setup») PUBBLICA
  UNA 10002 SUA se la si salva: il 15 ott 2026 alle 14:43 ha messo
  relay.nmail.li, nostr-01.yakihonne.com e primal, e nsyte ha seguito
  quella. Se succede: K4 di nuovo, e la stessa 10002 copiata sui relay
  di quella sbagliata (`nak req -k 10002 -a $HEX wss://nos.lol <
  /dev/null > nostra10002.json`, controllo, poi `nak event <relay> <
  nostra10002.json`: non rifirma).
  QUANDO LA LISTA CAMBIA si cambiano insieme `RELAY_DI_SERIE` (server
  e import), `config_esempio.py` e `LISTA` dello script (una prova le
  tiene uguali), poi R1-R5 e K1-K5.
  Provato il 15 ott 2026: K2 e K3 dal vivo (K3 è una lettura); K4 con
  un firmatario di cartone (`nak bunker`, chiave usa-e-getta) su un
  relay locale, con la variabile del banco: la firma passa, la 10002
  arriva sul relay; con una chiave diversa «NON PUBBLICO» e niente
  sul relay. Amber vero non è provato da qui.

- LA RONDA DEI RELAY NOSTR (15 ott 2026, cantiere relay-di-barattolo;
  com'è fatta in ARCHITETTURA, «LA RONDA DEI RELAY NOSTR»). Ogni dieci
  minuti il server chiede a ognuno dei relay di `RELAY_NOSTR` se
  risponde (una lettura minima, nessun evento scritto sui relay
  d'altri), e dal registro delle pubblicazioni VERE vede se un relay
  rifiuta gli eventi di Barattolo. Un guasto che dura da un'ora arriva
  nel gruppo degli admin, argomento Errori («⚠️ Relay Nostr di
  Barattolo»), una volta; quando passa, il ritorno («✅ … è tornato a
  posto»). Il journal lo dice al cambio: «🛰️ Ronda dei relay Nostr: …».
  NASCE SPENTA, e un deploy non la accende. PER ACCENDERLA, sul VPS:
  1) `grep -n "^RONDA_RELAY_NOSTR" /srv/barattolo/config.py` (non deve
     esserci);
  2) `printf '\nRONDA_RELAY_NOSTR = True\n' | sudo tee -a /srv/barattolo/config.py`
  3) il controllo ast come in R4, e `sudo systemctl restart barattolo`;
  4) `sudo journalctl -u barattolo --since "2 min ago" --no-pager | grep -E "Ronda dei relay Nostr|Traceback"`
     — «🛰️ Ronda dei relay Nostr ACCESA: chiedo a …», e dopo il primo
     giro la riga con lo stato di ogni relay.
  PER SPEGNERLA: `RONDA_RELAY_NOSTR = False` (riscritta al suo posto
  con `sudo sed -i 's|^RONDA_RELAY_NOSTR = .*|RONDA_RELAY_NOSTR = False|' /srv/barattolo/config.py`)
  e riavvio.

- LA BUCA DEL COORDINATORE, SUL RELAY NOSTRO (12 ott 2026, cantiere
  relay-per-mostro; perché in CANTIERI, «Il relay per Mostro»; com'è
  fatta in ARCHITETTURA, «LA BUCA DEL COORDINATORE»). Il plugin
  `chi-scrive.py` di `relay.barattolo.store` ha DUE porte: la lista di
  sempre (piattaforma, coordinatore, venditori con la chiave provata) e
  la buca delle lettere — da chiunque, ma SOLO un kind 14 con un tag
  `p` uguale al coordinatore, una scadenza entro due ore, al massimo
  16 KB e 6 tag; e tre freni al minuto: 30 per indirizzo IP, 10 per
  chiave, 600 in tutto. Tutto il resto resta rifiutato come prima,
  chat fra le parti e chat col moderatore comprese (decisione di
  Andrea).
  COME SI ENTRA NELLA MACCHINA DEL RELAY (VM1957, `185.18.221.118`), da
  PowerShell sul PC: `ssh -i $env:USERPROFILE\.ssh\lnvps debian@vm-1957.lnvps.cloud`
  (utente `debian`; i file di `/opt/relay` sono dell'UID 1001, quindi
  i comandi che li toccano vogliono `sudo`).
  ⚠️ LA MACCHINA NON TIRA DA GITHUB: il plugin ci si porta a mano, e
  IL FILE SUL PC HA I FINE RIGA DI WINDOWS — copiato com'è, la prima
  riga diventa `python3\r`, strfry non riesce a lanciarlo e il relay
  rifiuta TUTTO, piattaforma compresa. Per questo dopo la copia si
  tolgono i `\r` e si confronta l'impronta con quella del repo.
  LA PROCEDURA, un comando alla volta.
  1) PC (PowerShell, dalla cartella del repo, dopo `git pull`):
     `scp -i $env:USERPROFILE\.ssh\lnvps deploy\relay\policy\chi-scrive.py debian@vm-1957.lnvps.cloud:/tmp/chi-scrive.py`
  2) PC, l'impronta che deve tornare (quella del file com'è nel repo,
     coi fine riga giusti): `git rev-parse origin/main:deploy/relay/policy/chi-scrive.py`
  3) RELAY, via i `\r` e la stessa impronta rifatta lì:
     `sed -i 's/\r$//' /tmp/chi-scrive.py && python3 -c "import hashlib;d=open('/tmp/chi-scrive.py','rb').read();print(hashlib.sha1(b'blob %d\0'%len(d)+d).hexdigest())"`
     — deve stampare la riga del punto 2, carattere per carattere. Se
     è diversa NON si va avanti: il file non è quello del repo.
  4) RELAY, che il Python del CONTAINER lo legga (è un'Alpine, non la
     Debian di fuori): `cd /opt/relay && sudo docker compose exec -T relay python3 - < /tmp/chi-scrive.py; echo "esce $?"`
     — deve dire `esce 0` e nient'altro.
  5) RELAY, come sta il file di oggi (proprietario e permessi da
     ricopiare): `ls -ln /opt/relay/policy/`
  6) RELAY, la copia di sicurezza:
     `sudo cp -p /opt/relay/policy/chi-scrive.py /opt/relay/chi-scrive.py.prima-della-buca`
     (fuori da `policy/`, che è la cartella montata nel container).
  7) RELAY, il cambio — atomico, col proprietario e i permessi visti
     al punto 5 (di serie `1001:1001` e `755`: deve restare ESEGUIBILE):
     `sudo install -o 1001 -g 1001 -m 755 /tmp/chi-scrive.py /opt/relay/policy/chi-scrive.py.nuovo && sudo mv /opt/relay/policy/chi-scrive.py.nuovo /opt/relay/policy/chi-scrive.py`
  8) RELAY, cosa dice strfry: `sudo docker compose logs --since 3m relay | tail -30`.
     NIENTE RIAVVIO: strfry rilancia il plugin da solo quando il file
     cambia (lo guarda a ogni evento in arrivo: la riga compare al
     primo evento, e mostrod ne scrive uno ogni pochi minuti). VISTO
     il 13 ott 2026: cambio alle 13:03, «Setting up write policy
     plugin: /etc/strfry-policy/chi-scrive.py» alle 13:03:42. Se
     dopo dieci minuti il plugin vecchio risponde ancora (lo dice la
     ronda: «NON ACCETTA»), allora — AVVISANDO PRIMA —
     `sudo docker compose restart relay`: dura pochi secondi, le
     connessioni cadono e si riaprono da sole, i telefoni intanto
     passano da relay.mostro.network, e quel che mostrod scrive in
     quei secondi lo recupera lo specchio (`router.conf`). Il libro
     NON va fermato.
  9) LA PROVA la fa la ronda (voce qui sotto): con la leva accesa
     PRIMA del punto 7 il journal del VPS dice «relay.barattolo.store:
     NON ACCETTA i messaggi per il coordinatore», e dopo il punto 7
     «a posto». Sono i due stati visti dal vivo, nell'ordine giusto.
  SE VA STORTO (il relay rifiuta anche la piattaforma, o il log di
  strfry parla di plugin che non parte): si torna indietro con
  `sudo install -o 1001 -g 1001 -m 755 /opt/relay/chi-scrive.py.prima-della-buca /opt/relay/policy/chi-scrive.py`
  e si guarda con calma. Il libro intanto arriva lo stesso: lo
  specchio non passa dal plugin.
  I 16 KB SI CONFERMANO SUI MESSAGGI VERI, dopo i primi scambi passati
  di lì (i messaggi scadono in un'ora: si guarda a caldo). RELAY:
  `cd /opt/relay && M=$(sudo grep -oE '^MOSTRO = "[0-9a-f]+"' policy/chi-scrive.py | cut -d'"' -f2) && sudo docker compose exec -T relay /app/strfry scan "{\"kinds\":[14],\"#p\":[\"$M\"]}" | awk '{print length($0)}' | sort -n | tail -5`
  (la chiave del coordinatore la legge dal plugin: qui non si scrive,
  che un esadecimale lungo in un documento fa rossa la CI) — i cinque
  più grandi, in byte. Se il più grande sta sotto i 4.000
  il tetto è largo quattro volte; se un giorno un messaggio buono
  venisse rifiutato per la misura, strfry lo scrive nel log con
  «messaggio troppo grande» e il numero si alza in `BYTE_MAX`.
  LA DESCRIZIONE PUBBLICA DEL RELAY (il `description` del NIP-11 in
  `strfry.conf`) dice la regola nuova — «…accetta Barattolo, i
  venditori che hanno dimostrato la loro chiave e i messaggi per il
  suo coordinatore P2P» — nel repo E SULLA MACCHINA: applicata il 13
  ott 2026 (riga 74), repo e macchina sono in pari.
  ⚠️ DUE COSE IMPARATE QUEL GIORNO SU `strfry.conf`, che valgono per
  ogni sua modifica. 1) STRFRY RILEGGE LA SUA CONFIGURAZIONE DA SOLO:
  una riga cambiata vale subito, senza riavvio (visto col registro
  delle letture, acceso e spento così). 2) IL FILE È MONTATO NEL
  CONTAINER COME FILE SINGOLO, agganciato per identità: va riscritto
  DENTRO (`cat nuovo > strfry.conf`), mai sostituito (`sed -i`, `mv`),
  o il container continua a leggere il vecchio; `ls -li` prima e dopo
  deve dare lo stesso primo numero. La forma usata, RELAY:
  `sudo cp -p /opt/relay/strfry.conf /opt/relay/strfry.conf.prima-nip11-buca`
  poi la riga riscritta SENZA cambiare il file sotto i piedi del
  container (`strfry.conf` è montato come file singolo: un `sed -i`
  ne farebbe uno nuovo e il container continuerebbe a leggere il
  vecchio):
  `sudo sed 's|^\( *description = \).*|\1"Il relay del mercatino in sats. Lettura aperta a tutti; in scrittura accetta Barattolo, i venditori che hanno dimostrato la loro chiave e i messaggi per il suo coordinatore P2P."|' /opt/relay/strfry.conf > /tmp/strfry.nuovo && sudo sh -c 'cat /tmp/strfry.nuovo > /opt/relay/strfry.conf' && grep -n "description = " /opt/relay/strfry.conf`
  e per vederla da fuori (senza riavvio: strfry rilegge da solo):
  `curl -s -H 'Accept: application/nostr+json' https://relay.barattolo.store/ | head -c 300`
  DOPO QUALCHE GIORNO la copia `chi-scrive.py.prima-della-buca` si
  cancella: il backup delle 03:45 prende tutta `/opt/relay`, e un
  archivio che si porta dietro il plugin vecchio è la trappola già a
  verbale in `deploy/RIPRISTINO-RELAY.md`.
  MOSTROD CI LEGGE? SÌ, PROVATO il 13 ott 2026, e il modo conta
  perché la prima strada non ha funzionato. IL LOG DI MOSTROD NON LO
  DICE: a livello INFO non scrive i messaggi che butta, e al minuto
  del canarino non c'era niente (ci sono invece i cambi pubblicati
  ogni cinque minuti, con `success` sui tre relay). LO DICE IL RELAY,
  coi due registri di strfry accesi per pochi minuti (`dumpInReqs` e
  `dumpInEvents`, righe 168 e 165 di `strfry.conf`, da `false` a
  `true` e ritorno: vedi sopra come si scrive quel file). 1) Registro
  delle letture acceso, poi `sudo docker compose restart relay`
  (AVVISANDO: pochi secondi), perché mostrod la sua sottoscrizione la
  manda solo quando si collega. Quaranta secondi dopo, da un'uscita
  di Tor, una connessione ha chiesto
  `{"kinds":[14],"limit":0,"#p":[il coordinatore]}` — si cerca con
  `M=$(sudo grep -oE '^MOSTRO = "[0-9a-f]+"' policy/chi-scrive.py | cut -d'"' -f2); sudo docker compose logs --since 5m relay | grep "dumpInReq" | grep -E "#p\": ?\[\"$M"`.
  2) Che quella connessione sia mostrod e non un curioso lo dice il
  registro delle scritture: gli eventi FIRMATI dal coordinatore
  entravano tutti da lei —
  `… | grep "dumpIn" | grep -v "dumpInReq" | grep -E "\"pubkey\": ?\"$M\"" | grep -oE "\[[0-9]+\] dumpIn[A-Za-z]+" | sort | uniq -c`
  ha dato `5 [36] dumpInEvent`, e la 36 era quella della domanda.
  3) I DUE REGISTRI SI RISPENGONO SUBITO (accesi riempiono il log di
  Docker), e si guarda che lo siano:
  `sudo grep -n "dumpIn" /opt/relay/strfry.conf` — tre righe, tre
  `false`. Solo dopo questa prova `relay.barattolo.store` è entrato in
  `MOSTRO_RELAY_CONFERMA`: un suo OK avrebbe fatto «partito» un
  messaggio che mostrod non legge (il guasto del voto, a3f57b19). Va
  rifatta se mostrod cambia versione di trasporto o lista dei relay.

- LA RONDA DEI RELAY DI MOSTRO (12 ott 2026, cantiere relay-per-mostro;
  perché in CANTIERI, «Il relay per Mostro»; com'è fatta in
  ARCHITETTURA, «LA RONDA DEI RELAY DI MOSTRO»). Ogni dieci minuti il
  server chiede ai relay che confermano (`MOSTRO_RELAY_CONFERMA`; se
  la leva è vuota, a tutto `MOSTRO_RELAY`) se rispondono e se il
  coordinatore ci scrive ancora; e ogni mezz'ora manda al relay
  NOSTRO un «canarino», un messaggio di prova indirizzato al
  coordinatore, per sapere se la buca è aperta. Un guasto visto due
  giri di seguito arriva nel gruppo degli admin, argomento Errori
  («⚠️ Relay di Mostro»); quando passa arriva il ritorno («✅ … è
  tornato a posto»). Una volta per guasto, non a ogni giro.
  NASCE SPENTA, e un deploy non la accende. PER ACCENDERLA, sul VPS.
  ⚠️ LA REGOLA DI ANDREA (13 ott 2026), che vale per ogni comando sul
  config: MAI uno che stampa le righe intorno (`grep -A/-B/-C`, `cat`,
  `sed -n`) — lì dentro ci sono segreti. Solo righe precise, per NOME
  di leva. E la copia di sicurezza PRIMA di ogni modifica.
  1) cosa c'è già: `grep -n "^RONDA_RELAY\|^MOSTRO_RELAY" /srv/barattolo/config.py`
     (il 13 ott 2026: `MOSTRO_RELAY` alla riga 78, su UNA riga, con
     damus; `MOSTRO_RELAY_SPECCHIO` alla 97, col nostro relay);
  2) la copia: `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-della-ronda`;
  3) le due righe, appese senza aprire il file:
     `printf '\nRONDA_RELAY_MOSTRO = True\nRONDA_RELAY_CANARINO = ["wss://relay.barattolo.store"]\n' | sudo tee -a /srv/barattolo/config.py`
     ⚠️ nel canarino va il SOLO relay nostro: a un relay d'altri
     sarebbe spam verso il loro coordinatore di turno;
  4) il controllo: `sudo -u barattolo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('config ok')"`;
  5) `sudo systemctl restart barattolo`;
  6) `sudo journalctl -u barattolo --since "2 min ago" --no-pager | grep -E "Ronda|Traceback"`
     — «🛰️ Ronda dei relay di Mostro ACCESA: chiedo a …; il canarino
     va a wss://relay.barattolo.store», e subito dopo la riga del primo
     giro: «relay.barattolo.store: a posto · relay.mostro.network: a
     posto». Quella riga torna SOLO quando lo stato cambia.
  Il pannello «⚙️ Stato delle leve» mostra la leva con lo stato
  dell'ultimo giro.
  COSA DICONO GLI AVVISI: «non risponde» (non si apre, o apre e
  tace); «risponde, ma il coordinatore non ci scrive da N» (più di
  un'ora senza un evento del coordinatore: è il guasto di nos.lol a
  ottobre e di relay.mostro.network il 17 set); «NON ACCETTA i
  messaggi per il coordinatore» con le parole del relay (il plugin è
  tornato quello vecchio, o un freno scatta sul VPS); «non conferma i
  messaggi per il coordinatore» (il relay risponde alle letture ma
  l'OK al canarino non arriva).
  ⚠️ QUANDO SI FERMA IL NODO PER PIÙ DI UN'ORA (una salita d'immagine
  andata lunga) la ronda lo dice per OGNI relay: «il coordinatore non
  ci scrive da…». È vero, ed è atteso: passa da sé al primo evento.
  IL CORO CON DUE STRADE, di cui una nostra — dopo che la buca è
  aperta E si è visto che mostrod ci legge (voce qui sopra). Lo fa
  UNA sessione sola, questa (decisione di Andrea, 13 ott 2026: il
  cantiere del voto il config non lo tocca). Il coro deve diventare
  `MOSTRO_RELAY = ["wss://relay.mostro.network", "wss://relay.barattolo.store", "wss://nos.lol"]`
  `MOSTRO_RELAY_CONFERMA = ["wss://relay.mostro.network", "wss://relay.barattolo.store"]`
  e `MOSTRO_RELAY_SPECCHIO` RESTA COM'È, col nostro relay dentro: da
  quella lista il server prende l'ascolto dal vivo del libro e la
  pagina decide se il libro è completo. Il prezzo di averlo nelle due
  liste è una lettura del libro in più dallo stesso relay. Sul VPS:
  1) `grep -n "^MOSTRO_RELAY" /srv/barattolo/config.py` (com'è oggi, e
     se `MOSTRO_RELAY_CONFERMA` c'è già);
  2) la copia: `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-del-coro`;
  3) la riga del coro, RISCRITTA al suo posto (lo spazio prima di `=`
     tiene fuori `MOSTRO_RELAY_SPECCHIO` e `MOSTRO_RELAY_CONFERMA`):
     `sudo sed -i 's|^MOSTRO_RELAY = .*|MOSTRO_RELAY = ["wss://relay.mostro.network", "wss://relay.barattolo.store", "wss://nos.lol"]|' /srv/barattolo/config.py`
  4) la conferma — se al punto 1 NON c'era, appesa:
     `printf '\nMOSTRO_RELAY_CONFERMA = ["wss://relay.mostro.network", "wss://relay.barattolo.store"]\n' | sudo tee -a /srv/barattolo/config.py`
     se c'era, riscritta al suo posto:
     `sudo sed -i 's|^MOSTRO_RELAY_CONFERMA = .*|MOSTRO_RELAY_CONFERMA = ["wss://relay.mostro.network", "wss://relay.barattolo.store"]|' /srv/barattolo/config.py`
  5) di nuovo il punto 1 (tre righe, come scritte qui) e il controllo:
     `sudo -u barattolo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('config ok')"`;
  6) `sudo systemctl restart barattolo` (NON il nodo), e nel journal
     la riga della ronda coi due relay «a posto».
  Damus esce dal coro col punto 3 (il primo tempo di «TOGLIERE UN
  RELAY DAL CORO»); dal `settings.toml` del nodo esce con la `-bar8`,
  a libro fermo. I DM di Barattolo non c'entrano: hanno la loro lista
  (`AVVISO_DM_NOSTR_RELAY`, nos.lol e relay.primal.net). Le copie in
  `/root/` si cancellano quando il coro nuovo ha retto qualche giorno.
  PER SPEGNERLA: `RONDA_RELAY_MOSTRO = False` e riavvio. Il canarino
  smette con lei.

- IL GRUPPO DEGLI ADMIN (12 ott 2026; perché in CANTIERI, «Il gruppo
  degli admin»; com'è fatto in ARCHITETTURA, «IL GRUPPO DEGLI ADMIN»).
  Gli avvisi da admin (dispute, liquidità, pagamenti da guardare,
  moderazione, DM su Nostr, riepiloghi) in un gruppo Telegram privato
  con sei argomenti; in privato col bot restano gli avvisi da utente.
  NASCE SPENTO, e un deploy non lo accende. PER ACCENDERLO:
  A) SU TELEGRAM
  1) si crea un gruppo privato (nome a piacere) e si aggiunge
     @ilbarattolobot;
  2) nelle impostazioni del gruppo si accendono gli «Argomenti»
     (Topics): il gruppo diventa un supergruppo, e il suo numero cambia;
  3) si creano sei argomenti: ⚖️ Dispute, 💧 Liquidità, ⚠️ Errori,
     🛡️ Moderazione, 📩 DM Nostr, 📊 Riepiloghi (i nomi su Telegram
     sono liberi: contano i numeri);
  4) si fa il bot AMMINISTRATORE coi permessi al minimo: a un
     amministratore Telegram consegna i messaggi del gruppo (a un bot
     semplice membro solo i comandi scritti col suo nome,
     `/dove@ilbarattolobot`), e al bot non serve altro — non deve
     cancellare, bannare né invitare. Se Telegram vuole almeno un
     permesso acceso, «Gestisci argomenti» è il più innocuo.
     Chi dà i comandi NON deve avere «Resta anonimo» acceso: un
     anonimo arriva al bot senza nome, e il bot non gli risponde;
  5) si aggiungono Alan e i moderatori. Essere nel gruppo non dà i
     comandi: quelli restano di chi sta in `ADMIN_IDS`;
  6) dentro OGNI argomento si scrive `/dove`: il bot risponde con
     «Gruppo: -100…» (uguale in tutti) e «Argomento: N». Nel Generale
     dice che non ha un numero. Si annotano i sei numeri.
  B) SUL VPS
  1) la copia di riserva:
     `sudo cp -p /srv/barattolo/config.py /srv/barattolo/config.py.prima-gruppo-admin`
  2) si guarda che le righe non ci siano già:
     `grep -n "ADMIN_CANALE" /srv/barattolo/config.py`
  3) `sudo nano /srv/barattolo/config.py`, e in fondo DUE righe, coi
     numeri di `/dove`:
     `ADMIN_CANALE_ID = -100…`
     `ADMIN_CANALE_ARGOMENTI = {"dispute": N, "liquidita": N, "errori": N, "moderazione": N, "dm": N, "riepiloghi": N}`
  4) si guarda che il file si legga ancora:
     `sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"`
  5) `sudo systemctl restart barattolo`
  6) il journal:
     `journalctl -u barattolo --since "2 min ago" | grep "\[admin\]"`
     Deve esserci «[admin] Gruppo degli admin ACCESO: 6 argomenti su 6
     hanno la loro stanza…». Una riga «[admin] ADMIN_CANALE_ID non e'
     l'id di un gruppo con gli argomenti…» vuol dire numero sbagliato:
     la leva è rimasta SPENTA e gli avvisi arrivano in privato, come
     prima. Il pannello «⚙️ Stato delle leve» dice «Gruppo degli
     admin» acceso o spento (mai il numero).
  7) LA PROVA: nel gruppo, `/dove` dentro un argomento risponde «✅ È
     il gruppo scritto in ADMIN_CANALE_ID. Qui arrivano: …»; `/canali`
     risponde lì dentro. Un annuncio nuovo dal mercatino fa comparire
     «🆕 Nuovo annuncio» in 🛡️ Moderazione, e NON in privato.
  PER SPEGNERLO: `ADMIN_CANALE_ID = 0` (o via la riga) e riavvio. Per
  tornare indietro del tutto: la copia di riserva del punto 1.
  COSA SUCCEDE SE: il bot viene tolto dal gruppo, o il numero è
  sbagliato → gli avvisi tornano in privato da soli e a ogni moderatore
  arriva UNA volta «⚠️ Il gruppo degli admin non riceve», con la frase
  di Telegram; rimesso il bot, tornano nel gruppo senza toccare niente.
  Un argomento cancellato o col numero sbagliato → i suoi avvisi vanno
  nel Generale, e nel journal c'è «l'argomento «…» non riceve». Tanti
  avvisi in un minuto (Telegram ne lascia circa 20 al minuto per
  gruppo) → quelli in più arrivano in privato per i secondi che
  Telegram chiede. Nel journal:
  `journalctl -u barattolo --since "1 hour ago" | grep "Gruppo degli admin"`
  IL SUONO non si decide qui: il bot manda tutto col suono normale. Su
  Telegram ognuno silenzia l'argomento che vuole (si apre l'argomento,
  si tocca il suo nome in alto, poi «Silenzia» / «Notifiche»).
  LA 🔔 DEI NUOVI ORDINI DEL LIBRO P2P NON VA NEL GRUPPO (decisione
  di Andrea): è una notifica da utente, e resta in privato a chi l'ha
  accesa. Chi non la vuole in privato la spegne dal bottone 🔔 del
  libro o dal cassetto Avvisi del Profilo.
  ⚠️ `GUARDIANO_PONTE_AVVISA`, se sul VPS è compilata, col gruppo
  acceso diventa la strada di riserva: liquidità e ponte vanno nel
  gruppo, e a quegli id solo se il gruppo non riceve.
  IL GIORNO DELL'ACCENSIONE uno scambio P2P già annunciato in privato
  (una disputa aperta, una garanzia fra le 72 e le 88 ore) può essere
  ridetto una volta nel gruppo: il «già detto» è per destinatario, e
  il gruppo è un destinatario nuovo.
  LA CODA DEL GRUPPO (16 ott 2026, leva `GRUPPO_ADMIN_CODA`; com'è
  fatta in ARCHITETTURA, «LA CODA DEL GRUPPO DEGLI ADMIN»; perché in
  CANTIERI, «La coda del gruppo degli admin»). CAMBIA IL «COSA SUCCEDE
  SE» QUI SOPRA: un avviso che il gruppo non prende (rete caduta, 429,
  bot tolto) NON ripiega più subito in privato. Si riprova dopo 30
  secondi e dopo 2 minuti; poi gli URGENTI (dispute, revisioni coi
  ✅/❌, liquidità, errori) arrivano in privato come prima, gli altri
  (nuovi annunci e moderazione, banner, riepiloghi, DM) in privato
  MAI: aspettano in coda — sul database, tabella `gruppo_admin_coda`,
  quindi anche attraverso un riavvio — e arrivano nel gruppo quando
  riprende; dopo tre giorni si scartano. Un avviso che Telegram rifiuta
  per sé (troppo lungo, una foto che non scarica): l'urgente in privato
  subito, gli altri riprovati di solo testo e, se non passa, scartati.
  NON C'È NIENTE DA ACCENDERE: di serie è accesa, e la tabella nasce da
  sola al riavvio (CREATE TABLE IF NOT EXISTS, niente di esistente
  toccato). Si guarda che sul VPS non ci sia una riga che la spegne,
  in sola lettura, la sola riga:
  `grep -n "^GRUPPO_ADMIN_CODA" /srv/barattolo/config.py`
  Niente = accesa (il default del codice). `GRUPPO_ADMIN_CODA = False`
  = il comportamento di prima del 16 ott (subito in privato), e si
  toglie a mano. Il pannello «⚙️ Stato delle leve» dice «Coda del
  gruppo degli admin» accesa o spenta. Nel journal ogni passo ha la sua
  riga — in coda, tentativo non arrivato, RECUPERATO, in privato dopo i
  tentativi, SCARTATO:
  `journalctl -u barattolo --since "1 hour ago" | grep "Gruppo degli admin"`
  E quanti aspettano in coda adesso, in sola lettura:
  `sudo -u barattolo sqlite3 -readonly /srv/barattolo/dati/satmarket.db "SELECT argomento, urgente, tentativi FROM gruppo_admin_coda"`
  ⚠️ `deploy.sh` NON ha la coda: i suoi avvisi («🚀 Barattolo
  aggiornato» compreso) col gruppo muto ripiegano in privato subito,
  come prima.

- GLI AVVISI DEL DEPLOY NEL GRUPPO DEGLI ADMIN (12 ott 2026; com'è
  fatto in ARCHITETTURA, «GLI AVVISI DI `deploy.sh` NEL GRUPPO DEGLI
  ADMIN»). NON C'È NIENTE DA ACCENDERE: `deploy.sh` legge le stesse due
  righe del config che ha già acceso il gruppo (`ADMIN_CANALE_ID`,
  `ADMIN_CANALE_ARGOMENTI`). Da quando è in produzione, «🚀 Barattolo
  aggiornato» arriva in 📊 Riepiloghi, e gli altri sette avvisi del
  deploy (rifiutato, fermo, annullato, rollback, «è GIÙ») in ⚠️ Errori;
  in privato non arriva più niente.
  ⚠️ IL PRIMO È ANCORA IN PRIVATO: il deploy che porta questa modifica
  gira con lo script di prima (il servizio ne esegue una copia), quindi
  il suo «🚀 Barattolo aggiornato» arriva in privato. Dal deploy dopo,
  nel gruppo.
  SE UN AVVISO DEL DEPLOY TORNA IN PRIVATO il gruppo non ha risposto a
  `deploy.sh` (bot tolto, numero sbagliato, Telegram che rifiuta). Lo
  dice il journal del deploy:
  `journalctl -u barattolo-deploy --since "1 hour ago" | grep "gruppo degli admin"`
  Non arriva un secondo messaggio a dirlo: quell'avvertimento lo dà il
  server, al primo avviso suo che il gruppo rifiuta.
  LA PROVA è il secondo deploy dopo questo: il suo «🚀 Barattolo
  aggiornato» deve comparire in 📊 Riepiloghi e non in privato.
  GLI ALTRI CANALI NON C'ENTRANO E NON SONO CAMBIATI: il backup
  (`deploy/backup-fuori.sh`, col suo bot e il suo `CHAT_ID_BACKUP`), le
  ronde del nodo (`TG_CHAT` in `telegram.env`, sul nodo), la ronda del
  relay (`CHAT_ID` in `/opt/relay/telegram.conf`), i canali pubblici.
- LA CHAT NELLO SCAMBIO: IL FILE DELLE BUSTE (12 ott 2026, cantiere
  chat-nello-scambio; com'è fatta in ARCHITETTURA, «LA CHAT NELLO
  SCAMBIO»). AL DEPLOY NON C'È NIENTE DA FARE: la leva è accesa di
  serie anche senza la sua riga nel config (vedi in fondo a questa
  voce), e non c'è nessuna migrazione di `satmarket.db`. Alla
  prima busta il server crea da solo `chat-scambi.db` ACCANTO al
  database vero — sul VPS `/srv/barattolo/dati/chat-scambi.db`, perché
  `satmarket.db` è un collegamento a quella cartella — coi permessi
  600. Il posto NON è una leva: lo decide quello del database vero.
  ⚠️ QUEL FILE NON VA NEI BACKUP, ED È VOLUTO. Dentro ci sono le buste
  cifrate delle chat IN CORSO, che a scambio finito si cancellano. Il
  pre-deploy (`deploy.sh`) e il giornaliero (`deploy/backup-fuori.sh`)
  copiano `satmarket.db` per nome, e questo non lo toccano. NON
  aggiungerlo, e non copiare a mano la cartella dei dati intera: una
  copia farebbe sopravvivere le buste alla loro cancellazione. Una
  prova (`prove_chat_scambio`) fallisce se uno dei due script lo
  nomina.
  SE IL FILE SI PERDE (un ripristino da backup, un trasloco su un'altra
  macchina): non si recupera, e non serve. Rinasce vuoto; i telefoni
  che avevano una chat aperta se ne accorgono al primo ritiro (il
  server risponde `perso`), buttano la chiave vecchia e ripartono con
  una nuova. Si perdono i messaggi delle chat in corso, e basta: gli
  scambi non ne dipendono.
  GUARDARE, in sola lettura (il testo non c'è: sono buste chiuse):
  `ls -la /srv/barattolo/dati/chat-scambi.db`
  `sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "SELECT COUNT(*), COUNT(DISTINCT ordine) FROM buste;"`
  Quante buste, su quanti scambi: a mercato fermo deve tornare a zero.
  GLI ALLEGATI (16 ott 2026, cantiere barcode-paycode, parte C): foto e
  PDF della chat stanno nello STESSO file, tabella `allegati`, gia'
  cifrati dal telefono (il server non sa nemmeno che tipo sono). Nasce
  da sola al primo avvio, nessuna migrazione. Il file puo' crescere fino
  al tetto di 500 MB di allegati (`P2P_CHAT_ALLEGATI_CASSETTO`; oltre,
  chi manda sente «Adesso non c'è spazio per i file»); se ne vanno a
  scambio finito come le buste, e lo spazio torna libero dentro il file
  (sqlite lo riusa; il file su disco non si restringe da solo). In sola
  lettura:
  `sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "SELECT COUNT(*), COALESCE(SUM(peso),0)/1048576 FROM allegati;"`
  Nel journal una riga per file, col solo peso: «📎 Chat P2P: un
  allegato sullo scambio …, N KB». pdf.js (`vendor/pdf.min.mjs`,
  `vendor/pdf.worker.min.mjs`) viaggia col deploy come gli altri vendor.
  IL CASSETTO DA 2 GB (16 ott 2026, cantiere pdf-allegati, decisioni di
  Andrea): il PDF fino a 20 MB, le foto ridisegnate sotto i 2, dieci file
  e 40 MB per persona in ogni scambio, 2 GB di file in tutto
  (`P2P_CHAT_ALLEGATI_CASSETTO`; sul VPS il 16 ott 25 GB liberi su 38).
  DOVE STANNO: dentro `/srv/barattolo/dati/chat-scambi.db`, come blob
  cifrati. NON ENTRA NEI BACKUP, e coi 2 GB conta ancora di più: il
  pre-deploy copia solo `satmarket.db` (con l'API di sqlite, per nome) e
  il giornaliero (`deploy/backup-fuori.sh`) solo `satmarket.db`,
  `config.py`, `buste/` e `contenuti/` — `buste/` è la cartella delle
  buste di ritiro del mercatino, non la chat. Una prova fallisce se uno
  dei due script nomina il cassetto. LO SPAZIO TORNA AL DISCO: dal primo
  avvio dopo questo deploy il cassetto è `auto_vacuum = INCREMENTAL` (un
  VACUUM UNA volta sola, al primo avvio: oggi il file è piccolo; nel
  journal «🧹 Chat (scambi e ordini): il cassetto restituisce lo spazio
  dei file cancellati» — fino al 19 ott 2026 diceva «Chat P2P»), e la scopa, dopo ogni pulizia, restituisce le pagine
  libere (`PRAGMA incremental_vacuum`): il file si restringe davvero. Se
  il VACUUM non riesce lo dice («⚠️ Chat (scambi e ordini): auto_vacuum
  non acceso») e
  riprova al riavvio dopo. In sola lettura:
  `sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "PRAGMA auto_vacuum; PRAGMA freelist_count;"`
  deve dire 2 e un numero piccolo. L'AVVISO: quando i file passano l'80 %
  dei 2 GB, nel gruppo degli admin (argomento errori) «📎 Il cassetto dei
  file della chat (scambi e ordini) è quasi pieno: … MB su 2.048 MB», una
  volta (nel journal «📎 Chat (scambi e ordini): cassetto dei file
  all'80 %»); si
  riarma sotto il 60 %. Al pieno chi manda sente «Adesso non c'è spazio
  per i file». pdf-lib (`vendor/pdf-lib.min.js`) viaggia col deploy.
  NEL JOURNAL (`journalctl -u barattolo | grep "Chat P2P"`): «💬 Chat
  P2P: nuovo messaggio sullo scambio …, avvisato …» quando parte un
  avviso; «🧹 Chat P2P: lo scambio … e' finito, buste cancellate» alla
  fine di uno scambio; «🧹 … cancellate le buste di N scambi finiti»
  quando le trova la scopa del minuto (dal 19 ott 2026 le chat degli
  ordini che la stessa scopa porta via hanno la riga loro: «🧹 Chat degli
  ordini: cancellate le buste di N ordini conclusi»); «⛔ Chat P2P» se scatta il tetto
  anti-abuso degli avvisi. Una riga per busta NON c'è, apposta, e gli
  accessi riusciti alle rotte della chat non compaiono nel registro di
  uvicorn (gli errori sì).
  LA PROVA SUL CAMPO, da fare con due telefoni dopo il primo deploy:
  uno scambio preso, due messaggi per parte, l'avviso senza testo
  sull'altro telefono ad app chiusa; a scambio concluso il riquadro
  sparisce su tutti e due, e il conto qui sopra torna a zero.
  LA LEVA, PER SPEGNERE LA CHAT SENZA UN DEPLOY (12 ott 2026, sera):
  `P2P_CHAT_SCAMBIO`, accesa di serie anche senza la sua riga. Per
  spegnerla: nel config del VPS la riga `P2P_CHAT_SCAMBIO = False`, e
  riavvio del servizio (`systemctl restart barattolo`). Si guarda prima
  se la riga c'è già: `grep -n "P2P_CHAT_SCAMBIO" /srv/barattolo/config.py`.
  Da spenta la chat sparisce dalla pagina dello scambio, il pallino
  tace, e il server non accetta buste nuove né ne consegna; le buste
  che ci sono restano nel file e se ne vanno come sempre, a scambio
  finito. Riaccesa (riga a True, o tolta, e riavvio), le chat degli
  scambi ancora in corso riprendono con le loro buste e le loro chiavi.
  Lo stato vero lo dice il pannello «⚙️ Stato delle leve», voce «Chat
  nello scambio P2P».
- LA CHAT NELLO SCAMBIO: LE COPIE SIGILLATE (12 ott 2026, notte, cantiere
  chat-stesso-dispositivo; com'è fatta in ARCHITETTURA, «LA CHAT SEGUE
  LO SCAMBIO: LA COPIA SIGILLATA»). AL DEPLOY NON C'È NIENTE DA FARE:
  nessuna migrazione (`tipo` è testo, e `chiave` è un valore in più),
  nessuna leva nuova, nessuna riga da aggiungere al config. In
  `chat-scambi.db` compaiono righe con `tipo='chiave'`: sono le copie
  sigillate delle chiavi della chat, una o poche per parte, e se ne
  vanno con le altre buste a scambio finito. Il file resta FUORI dai
  backup, a maggior ragione adesso. Le chat aperte PRIMA di questo
  deploy si mettono in pari da sole, al primo ritiro del telefono che
  ha la chiave. PER GUARDARE cos'ha uno scambio (sola lettura, senza il
  contenuto delle buste):
  `sudo -u barattolo sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "SELECT ordine, giro, da, tipo, n, quando FROM buste ORDER BY n DESC LIMIT 40"`.
  Due righe `saluto` dello stesso account nello stesso scambio vogliono
  dire due chiavi presentate (un «Continua la chat qui»); una riga
  `chiave` per ogni chiave vuol dire che le copie ci sono.
- LA CHAT NEGLI ORDINI DEL MERCATINO: LA LEVA (16 ott 2026, cantiere
  chat-mercatino; com'è fatta in ARCHITETTURA, «LA CHAT NEGLI ORDINI DEL
  MERCATINO»). AL DEPLOY NON SUCCEDE NIENTE: la leva è SPENTA di serie e
  il codice non la accende da solo. Il cassetto è lo stesso della chat
  dello scambio (`/srv/barattolo/dati/chat-scambi.db`, fuori dai
  backup); la tabella nuova `chiavi_ordine` nasce da sola al primo
  avvio, nessuna migrazione di `satmarket.db`.
  PER ACCENDERLA (quando Andrea l'ha provata): prima si guarda, in sola
  lettura, che la riga non ci sia già
  `grep -n "^MERCATINO_CHAT_ORDINI" /srv/barattolo/config.py`
  poi si aggiunge in fondo al config del VPS la riga
  `MERCATINO_CHAT_ORDINI = True`
  e si riavvia (`sudo systemctl restart barattolo`). Il pannello «⚙️
  Stato delle leve» dell'admin la deve dire accesa. Per spegnerla: la
  riga a `False` (o via), e riavvio; le chat che ci sono se ne vanno
  come sempre, a ordine concluso.
  GUARDARE, in sola lettura (il testo non c'è: sono buste chiuse):
  `sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "SELECT COUNT(*), COUNT(DISTINCT ordine) FROM buste WHERE ordine GLOB 'm[1-9]*';"`
  Quante buste, su quanti ordini del mercatino in corso. NEL JOURNAL
  (dal 19 ott 2026, chat-mercatino-2) l'ordine col suo numero, e la
  sigla sua: `journalctl -u barattolo | grep "Chat degli ordini"` —
  «💬 Chat degli ordini: nuovo messaggio sull'ordine 42, avvisato …»,
  «📎 Chat degli ordini: un allegato sull'ordine 42, N KB», «🧹 Chat degli
  ordini: l'ordine 42 e' concluso, buste cancellate», e «🧹 Chat degli
  ordini: cancellate le buste di N ordini conclusi» dal giro al minuto.
  Le righe dello scambio P2P restano «Chat P2P … sullo scambio …». Mai
  il testo. Dal 20 ott 2026 (chat-dalla-notifica) anche «💬 Chat degli
  ordini: chi compra vuole scrivere sull'ordine 42, avvisato …» — il
  tocco su «🔔 Avvisa …» quando l'altra parte non ha mai aperto
  Barattolo. LA SCORTA DI LUCCHETTI sta nello stesso cassetto (solo
  chiavi pubbliche e semi; fuori dai backup come tutto il file): in sola
  lettura `sqlite3 -readonly /srv/barattolo/dati/chat-scambi.db "SELECT COUNT(DISTINCT tg_id), SUM(ordine=''), SUM(ordine<>'') FROM scorta;"`
  dice quante persone ne hanno una, quanti lucchetti aspettano e quanti
  sono bruciati per ordini aperti. Se il cassetto rinasce la scorta si
  rifa' da sola al prossimo giro dei telefoni. IL TASTO DELL'AVVISO
  porta `&chat=1`: la pagina apre l'ordine dritta sulla chat. L'avviso
  di un messaggio aspetta un secondo sguardo di 13 secondi (non piu' 21)
  se chi riceve stava guardando la chat. LA CHAT FERMA: un ordine deciso dal moderatore il cui
  pagamento non è andato a segno (`refund` o `confirmed` con
  `disputata=1`, o `confirmed` chiuso dal timer) tiene la chat in sola
  lettura finché i sats arrivano; si vede contando le buste qui sopra.
  IL MODERATORE legge la chat di un ordine in disputa SOLO con la sua
  chiave di moderatore dichiarata (quella del P2P, `p2p_moderatori`) e
  sullo stesso dispositivo: senza, la pagina dell'ordine dice «serve la
  tua chiave da moderatore su questo dispositivo».
  LA PROVA SUL CAMPO, prima di accenderla per tutti: due telefoni, un
  ordine pagato, due messaggi per parte e una foto, l'avviso col tasto
  «💬 Apri l'ordine» ad app chiusa; poi la conferma, e la riga «Chat
  chiusa» su tutti e due, e il conto qui sopra che torna a zero.
- L'AVVISO «INDICA I TUOI CORRIERI» (12 ott 2026, cantiere
  punti-ritiro): la leva `AVVISO_CORRIERI_PUNTI`, SPENTA di serie nel
  codice. Dal deploy di quel cantiere il ritiro in un punto si offre
  solo dove il venditore ha dichiarato un corriere che ai punti
  consegna (Poste Italiane, SDA, InPost); a leva accesa parte UN
  messaggio in chat, una volta sola, ai venditori con annunci a
  spedizione attivi e nessun corriere dichiarato (o solo «Altro»):
  «Indica i tuoi corrieri per offrire anche il ritiro nei punti».
  Per accenderla: nel `config.py` del VPS la riga
  `AVVISO_CORRIERI_PUNTI = True`, poi `sudo systemctl restart
  barattolo`. Si guarda prima se la riga c'è già: `grep -n
  "AVVISO_CORRIERI_PUNTI" /srv/barattolo/config.py`. Parte al primo giro
  dell'orologio dopo il riavvio, e nel journal lascia la riga
  «📦 Campagna «corrieri per i punti»: avvisati N venditori [...]» con
  gli id: è il modo di sapere a chi è arrivata. Partita una volta non
  riparte (timbro `campagna_corrieri_punti` nella tabella `timbri`), e
  rispegnerla non serve. Lo stato vero lo dice il pannello «⚙️ Stato
  delle leve», voce «Avviso «indica i tuoi corrieri»».

LE TRE DESTINAZIONI DEI POST, E LA TERZA (15 ott 2026, cantiere
fix-test-rossi). Un annuncio nuovo esce da UNA fabbrica
(`_manda_post_canale`) verso tre posti, e ognuno ha la sua leva di
PARTENZA nel config e il suo comando dal bot che la scavalca salvando
nel database:
- il canale di CASA — `TELEGRAM_CANALE_ID`, comando `/canale @nome`;
- il canale OSPITE della comunità — `TELEGRAM_CANALE_VETRINA`, comando
  `/canale vetrina @nome`; lì entrano SOLO gli annunci di chi ha un
  @username Telegram;
- **@BitcoinPodcastTelegram** — `TELEGRAM_CANALE_BITCOIN_PODCAST`,
  comando `/canale bitcoinpodcast @nome`; qui NON c'è il filtro
  dell'@username (quel pubblico è di bitcoiner, e la menzione Telegram
  non è la maniglia che si aspetta).
Il riepilogo del lunedì ha un canale suo a parte
(`TELEGRAM_CANALE_RIEPILOGO`, `/canale riepilogo @nome`), e il vuoto lì
RIPIEGA sul canale di casa — a differenza degli altri due, dove il
vuoto vuol dire «non ci andiamo» e non esiste nessun ripiego: sono
canali di qualcun ALTRO.
IL BOT DEV'ESSERE AMMINISTRATORE di ogni canale a cui parla, col
permesso di pubblicare E di modificare i propri messaggi (serve al
✅ Venduto, che rieèdita il post già fatto). Il comando si prova prima
di crederci: manda un messaggio di saluto e salva solo se Telegram
risponde ok, sennò dice il motivo che Telegram ha dato.
PERCHÉ QUESTA VOCE ESISTE: la terza destinazione è nata (15 ott 2026)
senza la sua riga nel config d'esempio — l'unica dei quattro — e con lo
`""` cablato al posto del valore di partenza. Si poteva accendere solo
dal bot, e un VPS appena rifatto la dimenticava in silenzio.
DOVE SONO IN USO ADESSO lo dice `/canale` senza argomenti, che le elenca
tutte e tre (e dice «BitcoinPodcast è spento» quando è vuoto). Il
pannello «⚙️ Stato delle leve» NON basta: nomina il solo canale di casa
(`TELEGRAM_CANALE_ID`) — né l'ospite né il BitcoinPodcast ci compaiono,
e cercarli là non dà risposta.
- LE CHIAVI DEL CODICE PARTNER DI SATS ROUTING (19 ott 2026, cantiere
  swap-chiavi-referral; perché in CANTIERI, «Le chiavi della quota di
  SATS Routing»). Tre righe nel `config.py` del VPS: `SWAP_REFERRAL_ID`
  (il codice partner, «barattolo», NON segreto) e le due chiavi per
  leggere la quota da `/v2/referral/fees` (SEGRETE). SI LANCIA QUANDO
  la tappa che legge la quota sarà sul VPS: prima nessuna rotta le
  legge, e una chiave scritta senza servire è solo una chiave in più da
  custodire. Le chiavi le chiede il terminale SENZA mostrarle
  (`read -s`): non passano dalla chat, non finiscono nella history (il
  comando contiene solo i nomi delle variabili), e non stanno negli
  argomenti di nessun processo (`printf` è un comando interno di bash,
  e il testo arriva a `sudo tee` dallo stdin). UN COMANDO ALLA VOLTA,
  da bash sul VPS:
  1) la copia di riserva:
     `sudo cp -p /srv/barattolo/config.py /srv/barattolo/config.py.prima-referral`
  2) le righe non ci sono già (deve dire `0`):
     `sudo grep -c "^SWAP_REFERRAL" /srv/barattolo/config.py`
  3) il codice partner, che non è un segreto:
     `printf '\nSWAP_REFERRAL_ID = "barattolo"\n' | sudo tee -a /srv/barattolo/config.py > /dev/null`
  4) le due chiavi, in una riga sola (chiede prima la password di sudo,
     poi le due chiavi, che non si vedono mentre si incollano):
     `sudo -v && read -rsp "API key di SATS Routing: " K && echo && read -rsp "API secret di SATS Routing: " S && echo && if [ -z "$K" ] || [ -z "$S" ]; then echo "Una e' vuota: non scrivo niente"; elif [[ "$K$S" == *'"'* || "$K$S" == *"'"* || "$K$S" == *'\'* ]]; then echo "Contengono virgolette o barre: non scrivo niente, chiedi a Claude"; else printf 'SWAP_REFERRAL_API_KEY = %s%s%s\nSWAP_REFERRAL_API_SECRET = %s%s%s\n' '"' "$K" '"' '"' "$S" '"' | sudo tee -a /srv/barattolo/config.py > /dev/null && echo "Scritte"; fi; unset K S`
     Deve dire «Scritte». (Il formato compone le virgolette a parte
     apposta: una riga di documento col nome della chiave, l'uguale e
     una virgoletta attaccata è la forma che lo scanner dei segreti della
     CI prende per una chiave vera.)
  5) il file si legge ancora (deve dire `ok`):
     `sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"`
  6) le righe ci sono, senza mostrarle (deve dire `3`):
     `sudo grep -c "^SWAP_REFERRAL" /srv/barattolo/config.py`
  7) `sudo systemctl restart barattolo`, poi il pannello «⚙️ Stato delle
     leve», gruppo «🔄 Swap»: «Chiavi per leggere la quota (SATS
     Routing)» ACCESA e «Codice partner di SATS Routing» = barattolo. Il
     pannello non mostra mai le chiavi, solo che ci sono.
  Una chiave incollata male: la copia di riserva al suo posto
  (`sudo cp -p /srv/barattolo/config.py.prima-referral /srv/barattolo/config.py`)
  e si rifà dal passo 3. MAI le chiavi in chat (nemmeno con Claude), nel
  canale del nodo o in un file del repo; mai `cat`, `sed -n` o
  `grep -A/-B/-C` sul config (si guarda solo la riga, e qui nemmeno
  quella: si contano). Se una chiave esce da qualche parte va RUOTATA:
  si chiede a Massimo una coppia nuova e si rifà dal passo 1.

LE SESSIONI CHIUSE, IN SOLA LETTURA (19 ott 2026, cantiere logout-apk;
perché in CANTIERI, «Il falso logout dell'APK»). Una sessione chiusa nel
database non lascia la riga (è un DELETE), quindi il PERCHÉ sta nel
journal: dal deploy di questo cantiere ogni porta che chiude scrive
«🔑 Sessioni chiuse: N (motivo)», coi cinque motivi `logout`,
`logout tutti`, `rientro`, `tetto`, `scaduta` — mai token, hash, id o
nomi. Il comando qui sotto legge TRE cose e stampa solo conteggi: il
database VERO (`/srv/barattolo/dati/satmarket.db`, `mode=ro`: non
scrive nemmeno per sbaglio; tabella `sessioni`, colonne `tg_id`,
`creato`, `scade`, mai `token_hash`), le righe della traccia, e le
righe d'accesso di uvicorn delle rotte di login e logout (senza IP:
`grep -o` tiene solo il pezzo fra virgolette). Si lancia così com'è,
da root, ed è sicuro anche incollato a metà:
```
python3 -c "import sqlite3,time;c=sqlite3.connect('file:/srv/barattolo/dati/satmarket.db?mode=ro',uri=True);t=int(time.time());d=t-172800;q=lambda s,*a:c.execute(s,a).fetchone()[0];print('sessioni vive:',q('SELECT COUNT(*) FROM sessioni WHERE scade>?',t));print('aperte nelle 48h e ancora vive:',q('SELECT COUNT(*) FROM sessioni WHERE creato>?',d));print('account con 2+ sessioni aperte nelle 48h:',q('SELECT COUNT(*) FROM (SELECT tg_id FROM sessioni WHERE creato>? GROUP BY tg_id HAVING COUNT(*)>1)',d))"
journalctl -u barattolo --since "48 hours ago" -o cat | grep -oE '🔑 Sessioni chiuse: [0-9]+ \([a-z ]+\)' | awk '{m=substr($0,index($0,"(")); n[m]+=$4} END{for(m in n) print "chiuse", n[m], m}'
journalctl -u barattolo --since "48 hours ago" -o cat | grep -oE '"(GET|POST) /api/(logout(/tutti)?|login/[a-z/]+|me) HTTP/[0-9.]+" [0-9]{3}' | sed 's/^"//; s/ HTTP\/[0-9.]*"//' | sort | uniq -c | sort -rn
echo "riavvii: $(journalctl -u barattolo --since '48 hours ago' -o cat | grep -c 'Application startup complete')"
```
COME SI LEGGE: le righe «chiuse N (motivo)» sono la risposta (per le
ore PRIMA del deploy del cantiere non esistono: lì restano i conteggi
delle rotte). `POST /api/logout 200` è un'uscita voluta; tanti
`POST /api/login/nostr 200` contro poche «aperte nelle 48h» vuol dire
sessioni aperte e già chiuse (rientro o tetto); i `GET /api/me 401`
contano anche i visitatori anonimi della vetrina, quindi da soli non
dicono niente. «riavvii» è quante volte un deploy ha fermato il server:
è il momento in cui, prima di questo cantiere, una riapertura dell'app
poteva finire nella vetrina anonima (il falso logout) e un login Nostr
a metà perdeva la sfida.

L'ASSISTENTE DEL BOT: LA CHIAVE E LE LEVE (28 ott 2026, cantiere
bot-assistente; perché in CANTIERI, «L'assistente del bot»). Di serie è
SPENTO e senza chiave: dopo il deploy il bot è quello di ieri. Per
accenderlo, in quest'ordine, UN COMANDO ALLA VOLTA:
  1) LA CHIAVE, NELLA CONSOLE DI ANTHROPIC (dal PC, nel browser):
     un workspace apposta («barattolo-bot») col suo LIMITE DI SPESA
     mensile (per cominciare 10-20 $), e dentro una chiave nuova
     («assistente-bot»). Una chiave SOLO per l'assistente: si revoca da
     sola senza toccare la moderazione (`ANTHROPIC_API_KEY`), e la
     Console dice quanto spende lei. La chiave si copia una volta e va
     in KeePass; MAI in chat (nemmeno con Claude), su GitHub o in un log.
  2) IL CONFIG, SUL VPS, col `read -s` come le chiavi di SATS Routing
     (qui sopra, «LE CHIAVI DEL CODICE PARTNER DI SATS ROUTING»):
     a) la copia di riserva:
        `sudo cp -p /srv/barattolo/config.py /root/config.py.prima-assistente`
     b) le righe non ci sono già (deve dire `0`):
        `sudo grep -c "^ASSISTENTE_" /srv/barattolo/config.py`
     c) la chiave, in una riga sola (chiede prima la password di sudo,
        poi la chiave, che non si vede mentre si incolla):
        `sudo -v && read -rsp "Chiave dell'assistente: " K && echo && if [ -z "$K" ]; then echo "Vuota: non scrivo niente"; elif [[ "$K" == *'"'* || "$K" == *"'"* || "$K" == *'\'* ]]; then echo "Contiene virgolette o barre: non scrivo niente, chiedi a Claude"; else printf '\nASSISTENTE_API_KEY = %s%s%s\n' '"' "$K" '"' | sudo tee -a /srv/barattolo/config.py > /dev/null && echo "Scritta"; fi; unset K`
        Deve dire «Scritta».
     d) la leva (resta a solo-moderatori, di serie):
        `printf 'ASSISTENTE_AI_ATTIVO = True\n' | sudo tee -a /srv/barattolo/config.py > /dev/null`
     e) il file si legge ancora (deve dire `ok`):
        `sudo python3 -c "import ast; ast.parse(open('/srv/barattolo/config.py').read()); print('ok')"`
     f) le due righe ci sono, senza mostrarle (deve dire `2`):
        `sudo grep -c "^ASSISTENTE_" /srv/barattolo/config.py`
  3) IL RIAVVIO: `sudo systemctl restart barattolo`.
  4) LA PROVA, da admin: una frase qualunque al bot («come funziona il
     deposito di garanzia?»). Risponde con «🤖 Sono l'assistente
     automatico…» e il bottone «🙋 Parla con una persona». Nel journal
     una riga «🤖 Assistente del bot: una risposta (token: …)», mai la
     domanda: `journalctl -u barattolo --since "5 min ago" | grep -c "Assistente del bot"`.
     Un utente qualunque, finché solo-moderatori è acceso, ha ancora il
     bot di ieri.
  5) A TUTTI, quando Andrea decide: `ASSISTENTE_SOLO_MODERATORI` a
     False dal pannello «⚙️ Stato delle leve», gruppo «🤖 Assistente del
     bot» (o una riga nel config). Dallo stesso gruppo si spegne
     l'assistente in un tocco; la chiave da lì non si vede né si scrive.
  L'ARGOMENTO «🙋 ASSISTENZA» NEL GRUPPO DEGLI ADMIN: senza il suo numero
  gli avvisi «Chiede una persona» vanno nel Generale (funziona, ma si
  mescolano). Per dargli la sua stanza: nel gruppo un argomento nuovo
  «🙋 Assistenza», dentro `/dove` per il numero. Sul VPS la copia di
  riserva, poi la riga di oggi (non è un segreto, sono numeri):
  `grep -n "^ADMIN_CANALE_ARGOMENTI" /srv/barattolo/config.py`
  e in fondo una riga NUOVA intera, coi numeri di quella più
  `"assistenza": N` (l'ultima riga vince, la vecchia può restare):
  `printf '\nADMIN_CANALE_ARGOMENTI = {…i numeri di prima…, "assistenza": N}\n' | sudo tee -a /srv/barattolo/config.py > /dev/null`
  Poi `ast.parse` come al passo 2e e il riavvio; il journal all'avvio
  dice «[admin] … 7 argomenti su 7» (procedura del gruppo qui sopra,
  «IL GRUPPO DEGLI ADMIN»).
  IL LIBRO DEL SAPERE è `assistente/sapere.md` nel repo, e viaggia col
  deploy: si corregge con un commit, non sul VPS. Senza il file
  l'assistente resta spento da solo (riga «⚠️ Assistente del bot: il
  libro del sapere non si legge» nel journal).
  SE QUALCOSA VA STORTO: l'interruttore dal pannello, o
  `printf 'ASSISTENTE_AI_ATTIVO = False\n' | sudo tee -a /srv/barattolo/config.py > /dev/null`
  e riavvio (l'ultima riga vince). Una chiave esposta si REVOCA dalla
  Console e se ne fa un'altra (regola ferrea 1).
