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
- LA QUINTA DOMANDA DELLA RONDA, OGNI GIORNO: `ronda-tor.sh` +
  `nodo-tor.timer` (09:20 UTC, Persistent), copie in `deploy/nodo/`.
  Tre giudici dal namespace di mostro: la curl a check.torproject.org
  (allarme su codice diverso da 200 o `IsTor` non true — il secondo e'
  il caso peggiore, esce in chiaro), MOSTRO DENTRO MOSTRO-NET (dal 22
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
  IL CANARINO: un «LND non l'ha mai visto» si crede solo se, nello
  stesso giro, LND riconosce un hash che conosce di sicuro — uno per
  cui lui stesso ha gia' detto SUCCEEDED (timbro `lnd_canarino`, o gli
  ultimi payout usciti dal nodo). Senza canarino «assente» vale
  «muto», cioe' si aspetta. Non c'e' niente da seminare a mano: basta
  che nel database ci sia UN payout riuscito dalla cassaforte `nodo`.
  I CONTROLLI A MANO, tutti di sola lettura. Sul VPS, la coda:
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT 'ordini',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM ordini WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'rimborsi',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM rimborsi_asta WHERE payout_stato NOT IN ('','uscito') UNION ALL SELECT 'sblocchi',id,stato,payout_stato,payout_verso,payout_tentativi,payout_hash FROM pagamenti WHERE payout_stato NOT IN ('','uscito');"`
  Tutti gli hash tentati per una riga (qui l'ordine 163):
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT hash,datetime(quando,'unixepoch'),esito FROM payout_tentati WHERE tabella='ordini' AND riga_id=163;"`
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
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,stato,payout_stato,payout_tentativi,payout_errore FROM ordini WHERE COALESCE(payout_errore,'')<>'' ORDER BY id DESC LIMIT 20;"`
  «Pagamento in uscita FALLITO» adesso dice il PERCHÉ in parole
  (fattura scaduta, nessuna strada, saldo NOSTRO insufficiente, ponte
  giù, tempo scaduto per strada, rifiutata da chi riceve, fattura già
  bruciata) col testo grezzo di LNbits accanto. «Saldo nostro» e
  «ponte giù» sono gli unici due che chiedono un gesto NOSTRO, subito.
  IL CENSIMENTO: `cd ~/satmarket && python3 censimento_scadenze.py` —
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
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,stato,payout_stato,payout_verso,payout_tentativi,payout_errore FROM ordini WHERE stato='confirmed' OR (payout_verso='venditore' AND payout_stato IN ('in_volo','incerto','da_riprovare')) ORDER BY id DESC;"`
  La linea del tempo di UN ordine (sostituisci 152):
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT datetime(quando,'unixepoch','localtime'),passo,motivo,volte,datetime(ultimo,'unixepoch','localtime') FROM payout_passi WHERE tabella='ordini' AND riga_id=152 ORDER BY id;"`
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
  riserva fee di LNbits, `max(1%, 2000 sats)`), e sul nodo liquidità in
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
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,stato,payout_stato,payout_verso,cassaforte,cassaforte_payout,payout_hash,length(invoice_venditore) FROM ordini WHERE id=152;"`
  — atteso `confirmed | incerto | venditore | saas | (vuoto) | <hash> |
  <lunghezza>`. Se `payout_stato` è `in_volo` si aspetta la ronda (30
  minuti dal tentativo). Gli hash tentati, con cassaforte e scadenza:
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT hash,datetime(quando,'unixepoch'),esito,cassaforte,datetime(scade,'unixepoch') FROM payout_tentati WHERE tabella='ordini' AND riga_id=152;"`
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
  I crediti: `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,riga_id,cassaforte,pagato_da,sats,stato,datetime(deciso_il,'unixepoch','localtime'),motivo,nota FROM crediti_cassaforte;"`
  SE VA STORTO. Il pagamento dal nodo fallisce (nessuna strada, saldo):
  l'ordine torna a «serve una fattura nuova», la cassaforte d'uscita
  RESTA il nodo, e la prossima fattura che Pedro incolla si paga da lì
  da sola. Per tornare a pagare dalla cassaforte d'origine NON c'è un
  bottone (non è mai servito): si rifà il giro al contrario solo se
  quel pagamento finisce 🧊. IL ROLLBACK è il commit precedente: le
  colonne e la tabella nuove restano e non danno fastidio, ma un ordine
  GIÀ deviato e non ancora pagato tornerebbe a pagare dalla cassaforte
  d'origine — si guarda prima che non ce ne siano:
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,stato,payout_stato FROM ordini WHERE COALESCE(cassaforte_payout,'')<>'' AND stato NOT IN ('released','refunded');"`
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
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT id,stato,payout_stato,payout_verso,cassaforte,cassaforte_payout,prezzo_sats FROM ordini WHERE cassaforte='saas' AND stato NOT IN ('creato','annullato','released','refunded');"`
  1) IL #152 (P3dr0, 247.707 sats, «pending» dal 20 set). Prima: sul
  nodo devono esserci 247.707 sats nostri piu' la riserva fee di LNbits
  (max(1%, 2000) = 2.477): spostali a mano. Poi 🧊 Pagamenti da
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
  il registro: `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT riga_id,gesto,da,a,sats,deciso_da,datetime(deciso_il,'unixepoch','localtime'),motivo FROM gesti_cassaforte;"`
  IL ROLLBACK e' il commit precedente: la tabella resta e non da'
  fastidio; un ordine SPOSTATO e non ancora chiuso paga ancora dal nodo
  (il codice del 21 set legge `cassaforte_payout` per l'incasso) ma un
  suo RIMBORSO tornerebbe a uscire dal SaaS — si guarda prima che non
  ce ne siano in disputa. NON PROVATO DAL VIVO: LNbits vero sulle due
  cassaforti e il pannello sul telefono; provato tutto il resto col
  server vero, su cartone.
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
  `scp "$env:TEMP\ponte.tar" UTENTE@185.18.221.96:/tmp/`
  Poi SUL NODO: `tar -xf /tmp/ponte.tar -C /tmp && sha256sum /tmp/deploy/ponte/*`
  e SUL VPS: `sha256sum ~/satmarket/deploy/ponte/*`
  — le quattro impronte devono essere IDENTICHE sulle due macchine. Se
  una differisce, il file è arrivato storto: non si va avanti.
  PASSO 4 — SUL NODO, il tunnel e il socat:
  `sudo install -m 600 /tmp/deploy/ponte/wg0-nodo.conf /etc/wireguard/wg0.conf`
  `sudo sed -i 's|INCOLLA_QUI_LA_PUBBLICA_DEL_VPS|LA_PUBBLICA_DEL_VPS|' /etc/wireguard/wg0.conf`
  — al posto di `LA_PUBBLICA_DEL_VPS` i 44 caratteri del passo 2.
  `sudo grep -c INCOLLA_QUI /etc/wireguard/wg0.conf`
  — deve dire `0`.
  `sudo systemctl enable --now wg-quick@wg0`
  `sudo iptables -S WG-PONTE`
  — sei righe: la catena, un ACCEPT per `10.77.0.2` sulla 18080, due
  DROP, l'ACCEPT della 51820 per `46.62.162.103`, il suo DROP.
  `sudo iptables -S INPUT | head -2` — la prima regola è `-j WG-PONTE`.
  `sudo iptables -S FORWARD | head -3` — in cima i due DROP di `wg0`.
  `echo 'LND_REST=172.28.1.N:8080' | sudo tee /etc/default/lnd-rest-wg`
  — con l'IP vero del passo 0.
  `sudo install -m 644 /tmp/deploy/ponte/lnd-rest-wg.service /etc/systemd/system/`
  `sudo systemctl daemon-reload && sudo systemctl enable --now lnd-rest-wg`
  `sudo ss -lntp | grep 18080`
  — UNA riga, e l'indirizzo è `10.77.0.1:18080`. Se dice `0.0.0.0` o
  `*`: `sudo systemctl stop lnd-rest-wg` e riferisci.
  PASSO 5 — SUL VPS, il tunnel, e la prova PRIMA di toccare il ponte:
  `install -m 600 ~/satmarket/deploy/ponte/wg0-vps.conf /etc/wireguard/wg0.conf`
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
  `install -m 644 ~/satmarket/deploy/ponte/lnd-ponte.service /etc/systemd/system/lnd-ponte.service`
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
  `sqlite3 ~/nodo/mostro/mostro.db "DELETE FROM _sqlx_migrations WHERE version IN (20260913120000, 20260914120000)"`
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
  `/etc/barattolo-deploy/firmatari` — o, finché quel file non c'è, ha
  un autore dei nostri, che è una cintura di cartone (in git l'autore è
  testo libero); d) la CI è VERDE su di lui: `giudice_deploy.py` lo
  chiede alle Actions di GitHub (il giro nato da un push SU MAIN, coi
  lavori `prove` e `segreti` in `success`).
  TRE ESITI. Si tira → «🚀». RIFIUTATO → journal, «⛔ Deploy rifiutato:
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
  `cd ~/satmarket && python3 giudice_deploy.py token`
  — dice che token è. «fine-grained» va bene; «⚠️ token CLASSICO … SA
  SCRIVERE» va sostituito.
  `cd ~/satmarket && git push --dry-run origin HEAD:refs/heads/prova-permessi`
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
  `git -C ~/satmarket config --get-regexp 'credential|remote.origin.url'`
  — con `credential.helper store` è la riga di `/root/.git-credentials`
  (`https://UTENTE:TOKEN@github.com`): si apre con `nano`, si cambia il
  solo TOKEN, e `chmod 600 /root/.git-credentials`. Poi i tre controlli
  di nuovo, e il token VECCHIO si REVOCA su GitHub. Il token non si
  incolla mai in chat.
  PASSO 2 — LE DUE UNIT (la copia dello script sotto `/run`). Prima si
  guarda che sul VPS non abbiano ritocchi a mano:
  `cd ~/satmarket && for u in barattolo-deploy barattolo-backup; do git diff --no-index --stat /etc/systemd/system/$u.service deploy/$u.service; done`
  — devono cambiare SOLO le righe `RuntimeDirectory…`, `ExecStart` e i
  commenti. Se c'è altro: FERMATI e riferisci. Poi:
  `cp deploy/barattolo-deploy.service deploy/barattolo-backup.service /etc/systemd/system/ && systemctl daemon-reload`
  `systemctl start barattolo-deploy.service && journalctl -u barattolo-deploy -n 5 --no-pager`
  — nessun errore (nel caso normale non scrive niente: è in pari).
  PASSO 3 — IL CAMBIO D'UTENTE. Lo fa uno script, perché per qualche
  secondo il sito è giù e in quei secondi non si digita. PRIMA si
  guarda, e non tocca niente:
  `cd ~/satmarket && bash deploy/utente/cambio-utente.sh`
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
  `cd ~/satmarket && sudo -u barattolo python3 <script>.py`. Da root
  funzionano lo stesso, ma un file NATO da root in `dati/` o `foto/` il
  servizio non lo sa più riscrivere. Le letture (`sqlite3 -readonly`,
  i censimenti) restano come sono.
  TORNARE A ROOT, se qualcosa non gira:
  `bash ~/satmarket/deploy/utente/cambio-utente.sh --torna`
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
  `cd ~/satmarket && git -c gpg.ssh.allowedSignersFile=/etc/barattolo-deploy/firmatari.prova verify-commit -v HEAD 2>&1 | head -3`
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
  `git -C ~/satmarket log -1 --oneline` è ANCORA il commit di prima.
  POI SI RIMETTE A POSTO, o il prossimo semaforo della CI trova
  `pronto` fuori strada e diventa rosso:
  `git -C $env:TEMP\prova-pronto push --force origin origin/main:refs/heads/pronto`
  `git -C C:\Users\Andrea\Documents\GitHub\satmarket worktree remove --force $env:TEMP\prova-pronto`
  (rimettere `pronto` sulla punta di main non è un rischio: da oggi il
  VPS la CI la chiede da sé, e una punta non ancora verde aspetta.)
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
  e `sqlite3 -readonly satmarket.db "SELECT id, fonte, url_negozio,
  datetime(ultimo_giro,'unixepoch','localtime'), ultimo_errore,
  ultimo_esito FROM connettori"`. Un `variable` Woo che nel report dice
  «ha piu' varianti e non le ho potute leggere» è un lettore che non ha
  agganciato le variazioni (chiamata fuori dal lettore); «nessuna delle
  sue varianti e' in vendita» è il negozio.
- I CARRELLI TOLTI (24 set 2026): il carrello torna quello di prima —
  uno solo, di un venditore alla volta, in memoria — e con i carrelli
  per venditore se ne va il PAGAMENTO UNICO, cioè la busta in
  `pagamenti` col motivo 'carrello', in produzione da 297063d. Il
  server di adesso quella busta NON la sa più incassare
  (`_incasso_del_motivo` conosce 'banner' e 'negozio_slug'), quindi
  PRIMA del deploy si guarda, in sola lettura, che non ce ne siano:
  `sqlite3 -readonly ~/satmarket/satmarket.db "SELECT 'busta', id, stato, importo_sats, datetime(creato,'unixepoch','localtime') FROM pagamenti WHERE motivo='carrello' UNION ALL SELECT 'ordine', id, stato, pagamento_id, datetime(creato,'unixepoch','localtime') FROM ordini WHERE pagamento_id > 0;"`
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
