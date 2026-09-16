## Produzione

La macchina, le procedure che si lanciano a mano e la catena del deploy
per intero. Le poche righe che cambiano il GESTO invece del contenuto —
push su main = online entro un minuto, il config del VPS che vince sul
default del codice, e MODALITA_COLLAUDO col BOT_TOKEN vero fuori dal VPS
— restano in `CLAUDE.md`. Qui c'è tutto il resto.

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
  Le righe gia' in tabella prendono lo stato alla PRIMA ripubblicazione
  del loro ordine, senza frase: l'orologio non ha visto il passaggio
  e non lo inventa.
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
- LA QUINTA DOMANDA DELLA RONDA, OGNI GIORNO: `ronda-tor.sh` +
  `nodo-tor.timer` (09:20 UTC, Persistent), copie in `deploy/nodo/`.
  Tre giudici dal namespace di mostro: la curl a check.torproject.org
  (allarme su codice diverso da 200 o `IsTor` non true — il secondo e'
  il caso peggiore, esce in chiaro), i namespace di tor e del sidecar
  che devono coincidere finche' un sidecar esiste (oggi nessuno: il
  giudice si spegne da solo), e il DROP del FORWARD nel namespace vivo
  di tor, letto con l'iptables DI TOR via `docker exec` (ripiego nsenter
  + iptables dell'host; senza, «non misurato»). Usa `curlimages/curl`
  con `--pull never`: e' gia' sul nodo dal 15 set e la ronda non deve
  dipendere dalla rete per dire che la rete non c'e'. Installazione:
  scp dei tre file, `sha256sum` da confrontare, poi
  `sudo install -m 755 ronda-tor.sh /usr/local/bin/ && sudo cp nodo-tor.service nodo-tor.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now nodo-tor.timer && sudo /usr/local/bin/ronda-tor.sh --prova`.
  Il messaggio finisce con `--- fine ronda tor`, come le altre.
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
  `cd ~/satmarket && python3 -c "import sqlite3, server;
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
  LA CATENA, in tre pezzi: 1) il job `pronto` del workflow fa avanzare
  il ref `pronto` SOLO quando prove e controllo dei segreti sono
  passati; 2) sul VPS un timer systemd chiama `deploy.sh` ogni minuto,
  che guarda se quel ref si è mosso; 3) dopo il riavvio si chiede a
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
  che è di chi ha le chiavi. Sul guasto risponde 503 e non un 200 con
  «ok: false»: chi controlla la salute guarda il CODICE, e un guasto
  travestito da risposta buona è il modo in cui un rollback non parte.
  L'unità systemd COPIA lo script in /tmp prima di eseguirlo, e non è
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
  A MANO, quando serve: `./deploy.sh --dimmi` dice a che punto sta
  senza toccare niente, `--forza` riapplica e riavvia. Il primo giro
  (installazione del timer) è in `deploy/barattolo-deploy.service` e
  `.timer`. `prove.py` difende le quattro righe che contano — il
  semaforo che aspetta i due job, il freno, l'ordine del rollback, e
  la salute che non racconta niente di sé.
  IL MINUTO SI CONTA DA QUANDO `pronto` SI MUOVE, NON DA QUANDO SI FA
  PUSH (set 2026, dal cantiere del conteggio visualizzazioni): prima
  del timer sul VPS c'è la CI remota — le prove di `prove.py`, che sono
  9500+ e crescono — e quel giro ha il suo tempo, non incluso nel
  «minuto». Verificare un deploy subito dopo il push con una richiesta
  che tocca il codice nuovo (mai solo `/api/salute`, che risponde
  identica prima e dopo) può cadere nella finestra in cui `pronto` non
  si è ancora mosso: sembra un difetto del codice ed è solo la CI
  che sta ancora girando. Aspettare di più prima di concludere che
  qualcosa non funziona, o controllare `--dimmi` da chi ha le chiavi.
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
  IL PONTE VERSO LND: `lnd-ponte.service` (socat) ascolta su
  `127.0.0.1:18080` e infila tutto nel tor del VPS verso l'hidden
  service della REST di LND sul nodo, che ha il client-auth v3: la
  chiave privata sta in `/var/lib/tor/onion_auth/lnbits.auth_private`
  (`ClientOnionAuthDir` nel torrc), la pubblica in
  `~/nodo/tor/data/lnbits/authorized_clients/vps.auth` sul nodo. Senza
  la chiave la porta non esiste. Il TLS e' end-to-end col `tls.cert`
  di LND copiato in `/opt/lnbits/data/tls.cert` (SAN `127.0.0.1`):
  SCADE IL 22 OTT 2027 — quel giorno LND lo rigenera e la copia sul
  VPS va rifatta, o LNbits smette di fidarsi del ponte con un errore
  che sa di rete. Il macaroon (`LND_REST_MACAROON` nel `.env`, 600) e'
  dedicato, `root_key_id 1`: si revoca da solo con
  `lncli deletemacaroonid 1` sul nodo. Diagnosi in tre `curl` dal VPS:
  `-k` su `https://127.0.0.1:18080/v1/getinfo` (il ponte arriva?),
  `--cacert /opt/lnbits/data/tls.cert` (il cert combacia?), con
  l'header `Grpc-Metadata-macaroon` letto da file (il macaroon
  apre?); ognuno risponde a una domanda diversa.
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
  IL CONTROLLO DEGLI ORFANI, sulle due casseforti (set 2026):
  `cd ~/satmarket && python3 orfani.py` — sola lettura, legge il
  registro di ogni cassaforte configurata con la sua invoice key e
  lo incrocia coi `payment_hash` di ordini, rilanci e pagamenti.
  Tre elenchi: ORFANI (nostro memo, nessuna riga: devono essere
  zero), FUORI POSTO (la riga dice un'altra cassaforte: zero anche
  loro) e NON NOSTRI (capitale o altro: li guarda una persona).
  Esce con 1 se c'e' da guardare, quindi puo' stare in un cron che
  tace. Ha sostituito l'`orfani.py` non tracciato del 10 ago 2026,
  che leggeva una cassaforte sola e non conosceva `pagamenti`:
  quello si cancella.
  IL CAPITALE, per dichiararlo al polso 23: `cd ~/satmarket && python3
  capitale_cassa.py` — legge i due registri e stampa un totale per
  cassaforte, il complessivo e le due righe `INSERT OR REPLACE` con le
  chiavi `capitale_saas_sats` e `capitale_nodo_sats`. Dal set 2026 il
  polso 23 e' per cassaforte e legge quelle due (la vecchia
  `capitale_nostro_sats` vale da ripiego per il solo SaaS).
  BACKUP: `/opt/lnbits` (db con backup atomico, `.env`, compose, cert,
  superuser, unit del ponte) e `onion_auth` viaggiano nell'archivio
  age; la riserva fee di LNbits e' `max(1%, 2000 sats)` per payout.
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
