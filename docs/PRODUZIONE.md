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
- «AVVISATI N» NON VUOL DIRE ARRIVATO (17 set 2026): quella riga
  conta chi si e' PROVATO ad avvisare. L'esito sta nelle righe subito
  sotto, una per destinatario: `   📖 ↳ 700000001: telegram ok
  (messaggio 8841)` — il numero e' la ricevuta di Telegram —, oppure
  `telegram 403: non ha avviato il bot, o l'ha bloccato`, `telegram
  400: NON arrivato — …chat not found`, `DM Nostr in volo e NIENTE
  Telegram (canale scelto: «nostr»)`, `NESSUN CANALE (…)`.
  DAL CHAT ID ALL'ACCOUNT: in una chat privata il chat id E' il
  `tg_id`, quindi sul VPS, in sola lettura:
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT tg_id, nome, username, canale_notifiche, avvisi_p2p FROM utenti WHERE tg_id IN (<id1>, <id2>);"`
  — la colonna `canale_notifiche` e' quella da guardare per prima:
  `nostr` vuol dire che sul bot non arriva niente PER SCELTA.
  IL BOT E' UNO SOLO: mercatino e P2P passano dalla stessa `notifica`
  e dallo stesso `BOT_TOKEN`.
  CHI TACE LO DICE: `🔕 … ha gli avvisi P2P SPENTI (cassetto Avvisi)`
  quando a fermare un invio e' l'interruttore, `⏳ Campanello P2P: … e'
  nel gate (ultimo avviso Ns fa, pausa Ps)` quando e' la pausa.
  LA PROVA VERA DEL TRASPORTO, sul VPS:
  `cd ~/satmarket && python3 prova_notifica.py <chat_id>` — fa la
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
  e' annotata», «M ha gli avvisi P2P spenti», «l'ultimo avviso e' di Ns
  fa», «gia' 3 avvisi»). ⚠️ I «Ns dopo» dell'eco sono il NUMERO DA
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
  che è di chi ha le chiavi. L'UNICA ECCEZIONE (18 set 2026) è una
  parola sul ponte verso LND (`"ponte": "ok"`, vedi «IL GUARDIANO DEL
  PONTE» più sotto), che da fuori si vedeva già provando a comprare —
  e NON cambia il codice: col ponte giù resta 200, perché un guasto di
  tor non è una ragione per tornare alla versione di prima. Sul guasto
  del database risponde 503 e non un 200 con
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
  IL GUARDIANO DEL PONTE (18 set 2026, dopo nove ore di acquisti
  falliti senza che nessuno lo sapesse): il server fa da solo la PRIMA
  delle tre domande, ogni minuto. Al terzo «no» di fila riavvia `tor` e poi `lnd-ponte.service`,
  riguarda dopo 45 secondi e lo scrive su Telegram (il guasto prima
  del riavvio, l'esito dopo), al massimo un avviso ogni 15 minuti; una
  cura che non ha curato non si ripete prima di 15 minuti. Il perché
  di ogni numero sta in CANTIERI, «Il guardiano del ponte verso LND».
  DOVE SI LEGGE: `journalctl -u barattolo | grep 🌉` — all'avvio c'è
  sempre la riga «Guardiano del ponte verso LND: acceso» (o «spento»,
  col perché), poi solo i cambi. E da fuori `/api/salute` porta
  `"ponte"`: `ok`, `giu`, `attesa` (prima del primo controllo) o
  `spento`. A CHI SCRIVE: gli id di `GUARDIANO_PONTE_AVVISA = [...]`
  nel config, e a lista vuota (o riga assente) i moderatori. LEVA:
  `GUARDIANO_PONTE = False` + riavvio lo spegne. IL RIAVVIO RICHIEDE
  ROOT: `systemctl show barattolo -p User` deve dire `User=` vuoto o
  `root`, o la cura fallisce (e l'avviso lo dice con le parole di
  systemctl). IL DRILL, a mercatino fermo: `systemctl stop lnd-ponte`,
  e in circa tre minuti il guardiano lo deve rimettere su da solo,
  con i due avvisi. Quello che NON vede: un cert scaduto, un macaroon
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
  — hold e payout al satoshi contro `lncli`, e sul nodo `sqlite3
  <mostro.db> "SELECT * FROM barattolo_fees ORDER BY created_at DESC
  LIMIT 1"`; e uno col VPS irraggiungibile APPOSTA (`sudo systemctl
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
  P2P»). ⚠️ DA FARE: al 18 set 2026 il codice del server è su main e in
  servizio, la patch sul nodo NO — e finché non c'è valgono i soli
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
  `journalctl -u barattolo -f | grep -E "Evento P2P|Attese P2P|Riserva P2P|Libro P2P|Recapito P2P"`.
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
  LA CRONACA DI UN ORDINE, quando qualcosa non torna (in sola lettura):
  `sqlite3 ~/satmarket/satmarket.db "SELECT datetime(quando,'unixepoch'), momento, dettaglio, attore, fonte, giro FROM p2p_momenti WHERE ordine LIKE '0f3a5c1e%' ORDER BY quando"`
  e chi è stato avvisato di cosa:
  `sqlite3 ~/satmarket/satmarket.db "SELECT datetime(quando,'unixepoch'), momento, giro, tg_id, fonte FROM p2p_avvisi WHERE ordine LIKE '0f3a5c1e%' ORDER BY quando"`.
  LA PROVA A DUE TELEFONI (A compra e pubblica, B vende e prende; poi
  SUBITO un secondo scambio a parti rovesciate — è il caso che il 18 set
  ha rotto tutto): la checklist sta nel verbale in CANTIERI, e ogni riga
  ha il suo avviso atteso e chi NON deve riceverlo.
  IL ROLLBACK ha due gradini, come la 0005: togliere
  `BARATTOLO_EVENTI_URL` dal compose e `up -d` (la patch diventa inerte,
  e sul VPS svuotare `P2P_EVENTI_SEGRETO` fa tornare il libro a parlare
  subito), oppure l'immagine a `-bar3`.
