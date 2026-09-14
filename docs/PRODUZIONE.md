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
