# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Architettura

- `server.py` — backend FastAPI + SQLite (`satmarket.db`), un solo file.
  Escrow LNbits (invoice key incassa, admin key paga), commissione
  SOSPESA (COMMISSIONE_PERCENTO=0 nel config, cifra da decidere:
  quando si accenderà vanno rimessi i testi con la cifra — l'elenco
  dei punti è nel commit del lug 2026 che l'ha azzerata),
  notifiche via bot Telegram, ricerca AI (Haiku), orologio asyncio per gli
  sblocchi automatici (72h dalla consegna, 10gg dalla spedizione).
  `/api/listings` è PUBBLICA (vetrina anche senza Telegram) ma serve solo
  la whitelist esplicita `CAMPI_VETRINA`: `venditore_id` esce solo alle
  richieste autenticate. La ricerca AI resta riservata agli autenticati
  (pubblica sarebbe credito API regalato ai bot). Tutto il resto è
  autenticato via `verifica_utente`. Moderazione a tre strati su
  `pubblica()`: filtro `PAROLE_VIETATE` (parole intere su testo
  normalizzato), parere AI opzionale (fail-open se la chiave manca o
  la chiamata fallisce), notifica agli admin di ogni annuncio +
  endpoint admin di rimozione e di statistiche (`/api/admin/stats`:
  card 📊 + lista utenti in fondo al Profilo, solo moderatori;
  `utenti.registrato` è la data del primo accesso, "—" per chi
  c'era prima della colonna). I casi ambigui (cannabis
  light, pistola sparachiodi...) NON vanno nella lista parole: li
  valuta l'AI.
  Terza via della moderazione (lug 2026, decisione di Andrea: basta
  blocchi a priori — l'AI segnala, l'ADMIN decide): il prompt ha TRE
  verdetti — VIETATO solo per i casi netti (armi, droghe, sesso...),
  DUBBIO per i grigi (servizi non palesemente vietati, buoni
  riscattabili presso il venditore stesso; l'«ambiguo ma
  plausibilmente lecito» resta OK). `_leggi_verdetto` è il giudice
  unico (singolo e lotto): a leva `MODERAZIONE_REVISIONE` spenta il
  dubbio torna vietato (binario di ieri). Col dubbio l'annuncio nasce
  (o la modifica lo manda) in `stato='revisione'`: invisibile al
  pubblico per costruzione (i filtri stato='attivo' non si toccano),
  visibile al proprietario in /miei col badge ⏳ (riga spenta, niente
  Modifica, resta il ritiro), scudo anti-doppione allargato
  ('attivo','revisione'), ganci TRATTENUTI (niente Nostr/promo/match/
  distintivi — `_dati_distintivi` esclude la revisione). Risposta col
  flag `{revisione:true, attesa_ore}` (leva REVISIONE_ATTESA_ORE, solo
  testi onesti: «di solito entro N ore», mai un silenzio). Circuito:
  `avvisa_revisione` manda ai moderatori la notifica con tastiera
  inline ✅/❌ via bot_api (notifica() non porta reply_markup;
  callback_data `rev:ok|no:{id}`, NIENTE token in memoria: deve
  sopravvivere ai riavvii, autorizza `e_admin` sul mittente) +
  sezione «⏳ In revisione» sopra le stats admin del Profilo
  (`rigaRevisione`/`decidiRevisione`) + pallino `.off-dot` sul tappo
  (conteggio `in_revisione` in /api/me solo admin). Il cuore unico è
  `decidi_revisione` (UPDATE condizionato sullo stato: il secondo
  moderatore trova il 409, mai doppi ganci): ✅ = attivo + partono i
  ganci trattenuti (Nostr con `solo_aggiornamento` se l'evento
  esisteva già — il caso modifica — e promo solo senza post_canale_id;
  accoda_match è sempre innocuo per il dedup persistente); ❌ =
  'rimosso' + messaggio gentile al venditore + ritiro da Nostr e dal
  canale (serve da quando esiste il ripensamento: prima si poteva dare
  per scontato che un annuncio in revisione non fosse MAI stato
  online, e per un riaperto non è vero).
  LA DECISIONE È REVERSIBILE (lug 2026, decisione di Andrea): terzo
  esito `riapri` di `decidi_revisione` — da 'attivo' o 'rimosso' si
  torna in 'revisione'. Senza, l'unico rimedio a un rifiuto sbagliato
  sarebbe chiedere al venditore di ripubblicare. Riaprire vuol dire
  fuori da OGNI vetrina, non solo dalla nostra: ritiro NIP-09 + post
  di canale cancellato + ordini 'creato' annullati, e la guardia degli
  affari in corso della rimozione admin (con sats in cassaforte prima
  si chiude l'ordine). E perché il ripensamento esista davvero dev'essere
  RITROVABILE: `GET /api/admin/revisione?decisi=1` dà le ultime 20
  decisioni degli ultimi `GIORNI_RIPENSAMENTO` (7) — l'ULTIMA per
  annuncio, via MAX(id) sul registro — e nel Profilo admin c'è la
  sezione «↩︎ Decisi di recente» (`rigaDecisa`) col bottone. Si chiede
  SEMPRE, anche a coda vuota: è quando la coda è vuota che uno si
  accorge di aver sbagliato a svuotarla. La risposta resta un array in
  entrambi i casi, così un client vecchio in cache vede la coda di
  sempre. Il motivo mostrato pesca `esito IN ('dubbio','vietato')`:
  dall'import aperto anche il «vietato» dell'AI mette in coda, e
  guardare il solo dubbio lascerebbe metà coda senza spiegazione.
  La modifica firmata
  degli importati resta bloccante anche sul dubbio (dichiarato:
  l'import orario riporterebbe dentro). Import CSV: righe dubbie
  CREATE in revisione (contatore `in_revisione_n` nel report, fuori
  da Nostr/promo, niente tastiera per riga). Orologio
  `sollecita_revisioni` (leva REVISIONE_SOLLECITO_GIORNI, 2): UNA
  notifica aggregata al giorno, ma l'annuncio RESTA in attesa — mai
  online da solo, gemello del «prompt mai auto-modificato». REGISTRO
  `moderazione_log` (append-only, `registra_moderazione` fail-open):
  ogni esito di parole/AI/lotto/admin con motivo e deciso_da;
  `/api/admin/stats.moderazione` = in_revisione + riepilogo 30gg +
  motivi frequenti + ultime 20 righe, sezione «🛡 Registro
  moderazione» nel Profilo admin — è con QUESTI dati che il prompt si
  corregge A MANO: la macchina raccoglie, l'umano decide.
  Scudo anti-doppione (lug 2026, nato da un bug vero: 5 annunci
  identici da un solo utente): `pubblica()` risponde in modo
  IDEMPOTENTE — stesso venditore + stesso titolo + stesso
  prezzo_sats su un annuncio ATTIVO nato entro
  `FINESTRA_ANTIDOPPIONE` (30s) = retry, si ritorna l'id già
  esistente senza creare nulla (niente await tra controllo e INSERT:
  nel server mono-processo il blocco è atomico, para anche i submit
  concorrenti). Nel client `publish()` passa da `bottoneInAttesa`
  (bottone spento + overlay fino alla risposta): la causa prima era
  il fetch lento (foto base64 + moderazione AI) col dito che ritocca.
  L'ANNULLO VERO E LE LAPIDI (ago 2026, giro urgente dal campo — tre
  problemi riprodotti prima di toccare). 1) IL QR DEL PAYSHEET ERA
  FINTO: un pattern CSS decorativo che non codificava niente
  (verificato con uno scanner). Ora `mostraQr()` disegna un QR VERO —
  `lightning:<bolt11>` TUTTO MAIUSCOLO, che entra nella modalità
  alfanumerica (codice più rado, più facile da inquadrare: il formato
  dei wallet) — su canvas scuro-su-bianco FISSO nei due temi (il patto
  dell'etichetta prezzo: un codice si legge col contrasto, non col
  tema), zona quieta doppia (padding + 4 moduli nel canvas). Libreria
  `vendor/qrcode.js` (qrcode-generator 1.5.2, MIT) committata a
  versione bloccata e servita da rotta esplicita, MAI CDN — il patto
  di nostr.bundle.js: il QR dice al wallet dove mandare i sats.
  Caricamento pigro alla prima invoice; in DEMO niente QR (la stringa
  è finta, mai un QR bugiardo); in dispensa PWA (sw.js VERSIONE v3).
  Vale per ordini, set e puntate: il paySheet è uno.
  2) L'ANNULLA DEL FOGLIO ANNULLA DAVVERO (`annullaPagamento()`, con
  la conferma «se hai già pagato, NON annullare»); chiusura, velo,
  Esc e gesto indietro NON annullano mai — chi inquadra il QR esce
  verso il wallet e torna. La liturgia server (`annulla_ordine`,
  gemello `annulla_rilancio`): pagamento controllato PRIMA (la
  invoice può essere viva nel wallet, a differenza del reaper che
  agisce a fattura morta), CAS sullo stato, e la riga diventa LAPIDE
  'annullato' — MAI DELETE: un saldo atterrato nella corsa
  annulla-vs-saldo deve avere una riga su cui posarsi. Il RIACCIUFFO
  è `controlla_annullati` nell'orologio: lapide-ordine pagata →
  torna 'creato' (timbro fresco, il reaper non se la mangia) e passa
  da `_incassa_ordine` — chi paga ha comprato, la regola di
  verifica_pagamento (e un avviso ai moderatori); lapide-rilancio
  pagata → binario del fuori-tempo («Da riscuotere»). CONFLITTO
  DICHIARATO (provato in CI e su DB usa-e-getta): se nel frattempo
  l'oggetto e' andato a un altro, il riacciuffo porta COMUNQUE
  l'ordine a locked — lo stock non va mai negativo (il MAX del corner
  del reaper, da cui passa per costruzione), l'annuncio resta
  'venduto', e il doppio escrow e' il caso da moderatore di sempre:
  l'avviso ⚠️ ai moderatori parte proprio per questo. La purga vive
  nel reaper: lapidi-ordine a 1h dall'annullo, lapidi-rilancio con la
  soglia dei rilanci — sempre DOPO che la fattura non può più essere
  pagata. `_incassa_ordine` è il ramo pagato di verifica_pagamento
  ESTRATTO (serve al riacciuffo): CAS 'creato'→'locked', stock,
  offerte, notifiche — non ricontrolla la invoice, il chiamante l'ha
  appena fatto. 3) LA RIPRESA DEL PENTITO in compra(): lo stesso
  compratore che ritenta sullo stesso annuncio NON è un rivale — se
  ha un ordine 'creato' suo con fattura viva (colonna
  `ordini.invoice`, nuova; soglia `RIPRESA_INVOICE_S` 720s) e
  richiesta identica gli si RIPRESENTA la sua (flag `ripresa`, mai
  ordini gemelli); vecchia o richiesta diversa = lapide e rinnovo;
  già pagata = si incassa e 409 «l'oggetto è già tuo». Il messaggio
  d'attesa «qualcun altro sta pagando» resta SOLO per gli altri: è
  l'anti-doppio-acquisto, giusto così. (Il blocco della scelta
  consegna in compra() sta ora PRIMA del fail-fast dello stock: la
  ripresa confronta la scelta.) I set restano fuori dalla ripresa,
  dichiarato.
  IL RITIRO SI CONFERMA DA 'LOCKED' (ago 2026, dal campo: il
  compratore non trovava il bottone). Il server accettava già la
  conferma da locked — mancava nel CLIENT: ora a locked-ritiro il
  compratore ha nota 🤝 e «✅ L'ho ritirato — libera i sats», senza
  aspettare che il venditore segni nulla (rischia solo lui: la
  semantica del deposito; per la spedizione il bottone resta da
  shipped, dichiarato). E il ritiro mai concluso non ha NESSUN timer
  che corre (riprodotto: l'auto-sblocco parte dalle DICHIARAZIONI,
  e lì nessuno ha dichiarato niente — senza dichiarazioni i sats non
  si muovono MAI da soli): la cura è `sollecita_ritiri_fermi`
  nell'orologio — promemoria alle DUE parti (il compratore può
  confermare, il venditore può segnare la consegna e da lì parte la
  sua protezione), colonne sue `sollecito_ritiro_il`/
  `solleciti_ritiro` (NON quelle del sollecito incassi: vivono su
  'confirmed' e un contatore ereditato salterebbe al tetto), stesse
  leve SOLLECITO_INCASSO_*, al tetto 🧊 ai moderatori e poi silenzio.
  Categorie (lug 2026): catalogo unico `CATEGORIE` in server.py, 27
  voci — le 9 di sempre (Elettronica · Casa e giardino ·
  Abbigliamento · Sport e hobby · Motori · Bambini · Animali · Libri e
  media · Altro) più le 16 del catalogo largo (Informatica ·
  Telefonia · Audio e video · Console e videogiochi · Foto e ottica ·
  Bitcoin · Elettrodomestici · Fai da te e utensili · Alimenti e
  bevande · Scarpe e accessori · Orologi e gioielli · Biciclette ·
  Musica e film · Strumenti musicali · Collezionismo · Arte e
  artigianato), più «Bellezza e benessere» (lug 2026, 🧴): cosmetici,
  creme, profumi, saponi, oli essenziali, integratori e cura della
  persona, che prima si spartivano fra «Alimenti e bevande» (le
  tisane, gli integratori) e «Altro», e nessuna delle due era giusta.
  È la seconda voce delle CATEGORIE_SENZA_CONDIZIONE, per la stessa
  ragione degli alimenti (vedi sotto).
  Più «Buoni ed esperienze» (ago 2026, 🎟️ — il biglietto dice il
  reparto, il 🎁 direbbe un'occasione): gift card, buoni acquisto,
  voucher per soggiorni e cene — i due annunci veri che morivano in
  «Altro» (il pacchetto B&B, i buoni Zalando). È una famiglia di
  MERCE, non un modo di consegnare: la strada «Prodotti digitali» è
  stata valutata e scartata perché avrebbe detto il COME invece del
  COSA — i buoni Zalando veri hanno consegna=entrambe, la tessera si
  SPEDISCE, e una categoria «Digitale» con spedizione fisica è una
  contraddizione in vetrina. Ortogonale per costruzione al filtro
  «💾 Codice online»: la categoria dice cosa compri, il filtro come
  arriva. I SERVIZI restano fuori (decisione presa: un buono per una
  notte è una cosa che esiste, «ti sviluppo un bot» no) e la
  moderazione non cambia — i buoni riscattabili presso il venditore
  stesso restano DUBBIO. Terza voce delle CATEGORIE_SENZA_CONDIZIONE:
  un buono è nuovo per definizione, anche la tessera fisica. Le due
  righe-voucher del MODELLO_IMPORT traslocano lì e perdono la cella
  condizione (insegnerebbe una cosa falsa, la regola del miele).
  "Tutto" è solo la vista del
  frontend, non una categoria. «Bitcoin» è l'unica di casa nostra e non dei mercatini
  generalisti: su un mercatino che incassa in sats, Jade e BitBox02
  sono merce di casa. In vetrina il catalogo resta PIATTO, ma dal
  (ago 2026) l'albero delle SOTTOCATEGORIE esiste DORMIENTE nel
  codice — vedi la voce sua, più sotto.
  SI AGGIUNGE, NON SI RINOMINA (lug 2026, decisione di Andrea, ed è la
  regola da non rovesciare): le voci esistenti restano tutte con lo
  stesso nome. Il cantiere del catalogo largo proponeva di rinominarne
  tre (Casa e arredamento, Sport, Libri e riviste) con la sua
  migrazione; è stato scartato perché quei tre non erano voci nuove ma
  nomi nuovi per voci esistenti, e due nomi per la stessa cosa non
  sono più scelta ma un bivio senza risposta giusta davanti a chi
  pubblica. Conseguenza: NESSUNA migrazione di categoria da scrivere —
  nessun annuncio cambia casella, nessun venditore ritrova il suo
  oggetto dove non l'ha messo. Per la stessa ragione il fai-da-te è
  entrato come «Fai da te e utensili» e non «Giardino e fai da te»: il
  giardino ce l'ha già Casa e giardino.
  `categoria_valida`
  normalizza i payload (sconosciuta → Altro: il client non decide il
  catalogo); resta solo la migrazione VECCHIA in `init_db` (Sport →
  Sport e hobby ecc. con COLLATE NOCASE, che raddrizza le maiuscole
  storte dei vecchi import, 'casa'). La lista entra nel
  prompt della ricerca AI; nel NIP-99 il tag `t` è la prima parola
  minuscola ("Casa e giardino" → "casa": un hashtag non ha spazi).
  LE ICONE (`EMOJI_CAT` nel client) dicono il REPARTO, non un
  prodotto: 🍳 Elettrodomestici (il cesto 🧺 e' dove finisce il bucato,
  non un elettrodomestico), 🍎 Alimenti e bevande (il vasetto 🍯 diceva
  un prodotto solo, e per giunta somiglia al 🫙 dei preferiti, che non
  deve avere sosia), 🚗 Motori (lo scooter e' un pezzo del reparto),
  🏡 Casa e giardino (la sedia ne diceva meta'), 🧴 Bellezza e
  benessere (il flacone e' il ripiano intero — creme, oli, saponi,
  shampoo —, mentre il rossetto 💄 direbbe il solo trucco e lascerebbe
  fuori integratori e saponi, e il sapone 🧼 e' un prodotto solo).
  ₿ Bitcoin resta un
  glifo di TESTO e non un'emoji a colori — nel foglio stona un po'
  con le vicine, ed e' voluto: il simbolo vince sull'uniformita'.
  Guardate e tenute come sono: 🏺 Collezionismo (tira
  sull'antiquariato, ma non c'e' di meglio) e 📦 Altro (e' anche il
  pacco della spedizione: convivono senza confondersi).
  AGGIUNGERE UNA CATEGORIA TOCCA SETTE POSTI: `CATEGORIE` e
  `SINONIMI_CATEGORIA` e `MODELLO_IMPORT` in server.py, `<select
  id="sellCat">` e `EMOJI_CAT` e `CATS` in miniapp.html, più
  l'ILLUSTRAZIONE in `assets/categorie/{slug}.webp` (il settimo, lug
  2026, nato con la pagina Sfoglia) — e `CATEGORIE_SENZA_CONDIZIONE`
  col suo gemello `CAT_SENZA_COND`, se la voce nuova è di quelle dove
  la condizione non vuol dire niente.
  Non serve
  ricordarseli: `prove.py` li incrocia tutti e sette e fallisce se
  divergono (il sesto, il modello CSV, è entrato dopo essersi fatto
  dimenticare per davvero).
  L'ALBERO DELLE SOTTOCATEGORIE (ago 2026): definito ora, mostrato
  MAI — catalogo `SOTTOCATEGORIE` in server.py (86 sottovoci su 26
  categorie, disegnato sui 46 annunci veri di produzione), DORMIENTE:
  niente form, niente filtri, niente Sfoglia finché non si deciderà
  di accenderlo. Il patto, scritto anche nel commento del catalogo:
  id kebab-case PER SEMPRE e unici in TUTTO l'albero (un filtro senza
  categoria non dev'essere ambiguo), etichette ritoccabili senza
  migrazioni (pattern CONDIZIONI), ordine delle tuple = ordine di
  presentazione, SI AGGIUNGE NON SI RINOMINA anche qui, NIENTE voci
  «Altro X» (il fallback è '', un secondo cimitero per categoria
  sarebbe il vizio di «Altro» moltiplicato per ventisei), chiave
  assente = categoria piatta (oggi solo «Altro», per forza: «Altro»
  con sottovoci non è più «Altro»), e le regole — senza_condizione e
  simili — si EREDITANO dalla categoria: la sottovoce è un'etichetta
  di scaffale, non un secondo asse di regole. Giudici:
  `sottocategoria_valida(categoria, s)` ('' su sconosciuta o fuori
  categoria — il client non decide il catalogo) e
  `sottocategoria_tollerante` per il CSV (accetta id O etichetta,
  storta = '' mai uno scarto). La colonna `annunci.sottocategoria`
  nasce già ('' = non dichiarata, lecito per sempre) e i payload che
  la portano la scrivono: pubblica(), modifica() (assenza = CONSERVA,
  il pattern dello stock; cambio categoria = il giudice azzera da
  solo) e la cella facoltativa `sottocategoria` del CSV d'import. MAI
  nella modifica firmata degli importati né dall'import Nostr
  (l'evento non la porta), FUORI da CAMPI_VETRINA e dal modello CSV
  scaricabile (pubblicizzarla sarebbe mostrarla — nelle rotte
  autenticate con `a.*` esce gratis, innocuo e dichiarato).
  LE REGOLE DI CONFINE, decise sui casi veri e scritte nel commento
  del catalogo (entreranno nel prompt della ricategorizzazione AI
  all'accensione): smartwatch → Orologi e gioielli (il nome della
  sottovoce «Orologi e smartwatch» È la regola); cuffie e auricolari
  → Audio e video, Telefonia tiene «Cover e accessori»; stampanti da
  ufficio → Informatica, stampa 3D → Elettronica; droni e modellismo
  RC → Elettronica (non Foto e ottica); caschi moto → Motori; la roba
  da bimbi — vestiti, giocattoli, attrezzatura — sta in Bambini
  (regola d'oro, decisione di Andrea: Abbigliamento è adulti,
  Donna/Uomo), ma le bici VERE da bimbo in Biciclette e i giochi da
  tavolo per famiglie in Sport e hobby; l'artigianale si classifica
  per FUNZIONE (le tazze al tornio in Cucina e tavola, i saponi in
  Bellezza), Arte e artigianato è l'oggetto d'arte; Collezionismo =
  valore da collezione (numerato, raro, sealed), non il semplicemente
  vecchio; per ASCOLTARE → Audio e video, per SUONARE → Strumenti.
  ELETTRONICA È RESTATA con un contenuto SUO (decisione di Andrea: in
  produzione aveva ZERO annunci dopo gli scorpori, ma chiuderla
  avrebbe spostato il residuo in «Altro» e tolto LA parola che un
  venditore normale cerca): droni/modellismo, stampa 3D, smart home,
  componenti maker, strumenti di misura — con le sottovoci nitide
  sparisce anche l'esitazione col laptop. NON rinominata: la regola
  «si aggiunge, non si rinomina» tiene, e lo scaffale dice il
  contenuto meglio di un nome nuovo.
  IL GIUDICE SILENZIOSO (ago 2026, idea di Andrea): la colonna si
  riempie DA SOLA, senza AI e senza che nessuno veda nulla — parole
  chiave dentro la categoria GIÀ scelta, il pattern SINONIMI_CATEGORIA
  un piano più in basso. Catalogo `SINONIMI_SOTTOCATEGORIA` +
  `sottocategoria_indovina(categoria, titolo, descrizione)` in
  server.py accanto all'albero: parole intere normalizzate, prefisso
  solo da 5 lettere in su («auto» non prende «autoradio»), titolo pesa
  2 e descrizione 1, assegna solo il vincitore UNICO — il pareggio è
  un dubbio e il dubbio resta ''. MISURATO sui dati veri prima di
  accenderlo: 45/46 giusti in produzione più il NON SO voluto del Telo
  d'Amare, 12/15 fuori campione, ZERO sbagliati nei due giri — quando
  non ce la fa SI ASTIENE, mai un'assegnazione tirata a indovinare, ed
  è strutturale: dentro una categoria i vocabolari delle voci quasi
  non si sovrappongono. Zero rete e zero await (il patto anti-doppione
  di pubblica non si tocca). Si aggancia dove il payload non porta una
  sottovoce valida: pubblica(), modifica() (che ci RIPROVA sui testi
  nuovi quando la colonna è vuota — il ritocco può aver aggiunto la
  parola che mancava — ma non rigiudica MAI un valore scritto),
  l'import CSV, e il dopo-import Nostr (ogni giro, solo righe vuote:
  così quando la coda delle categorie sposta un annuncio fuori da
  «Altro», la sottovoce arriva da sola al giro dopo). Il dizionario è
  UNO e vive in server.py — la proposta in proposte/ è morta lì
  dentro, la lezione del prompt in due copie — e si arricchisce coi
  dati veri: `python assegna_sottocategorie.py --conta` sul VPS dice
  quante righe sono assegnate e DOVE il giudice si astiene di più, coi
  titoli d'esempio (SOLO gli attivi: il conto a tre stati pescava i
  venduti delle prove di rodaggio e misurava fantasmi — la passata
  --scrivi invece tiene anche revisione e venduto, che possono tornare
  in vetrina); si impara dai NON SO, mai dagli sbagli.
  IL TERMOMETRO SUONA DA SOLO (ago 2026, «il --conta lo dimenticherò
  di sicuro»): `termometro_sottocategorie` nell'orologio — il LUNEDÌ,
  UNA notifica aggregata agli admin con totale e le 3 categorie più
  scoperte, più il conto dei vuoti che il dizionario di OGGI
  coprirebbe già (= serve solo un rilancio dello script: chiude anche
  il secondo modo di dimenticarsene). L'ancora è il CALENDARIO e non
  un conteggio in memoria, ed è deliberato: il gate in RAM muore a
  ogni deploy e un «ogni 7 giorni» contato da lì suonerebbe a ogni
  riavvio — col lunedì, un riavvio può al più far suonare due volte
  quel lunedì. Conta come il --conta (soli attivi, «Altro» escluso:
  è piatta per forza, non è «scoperta»); tace sotto
  TERMOMETRO_SOTTOCATEGORIE_MINIMO (5), tace a vetrina piena, e la
  leva TERMOMETRO_SOTTOCATEGORIE (True di serie) la spegne — una coda
  ferma non suona, il patto dei solleciti. Lo stesso
  script fa la passata sul pregresso (anteprima di serie, `--scrivi`
  per farla, un percorso di database per la prova generale su una
  copia — pattern ripulisci_anello): tocca solo righe VUOTE in stati
  attivo/revisione/venduto, idempotente, e legge il giudice dal TESTO
  di server.py senza importarlo (la lezione di ricategorizza: l'import
  farebbe partire init_db, e in CI il config non esiste). NIENTE coda
  admin per queste assegnazioni, ed è deciso: il dato non esce da
  nessuna parte finché l'albero dorme, e correggere un'assegnazione il
  giorno dell'accensione costerà un rilancio dello script.
  ALL'ACCENSIONE (documentato, non costruito): foglio-picker in Vendi
  dipendente dalla categoria (pattern PICKER) — che il giudice potrà
  PRESELEZIONARE, con l'utente ultimo giudice —, param `sotto` su
  /api/listings ('' storici fuori dal filtro, il patto del dato
  dichiarato), chips dentro la vetrina di categoria in Sfoglia
  (nessuna piastrella nuova), prompt AI con albero e confini per il
  residuo delle astensioni, eventuale secondo tag `t` NIP-99 — sarà
  solo frontend + un parametro, e il catalogo sarà già catalogato
  invece che vuoto. `prove.py` difende il patto: chiavi ∈ CATEGORIE,
  id unici e kebab, niente «altro», i giudici nei loro casi, il
  dizionario allineato all'albero voce per voce.
  LA PAGINA «SFOGLIA» (lug 2026): le categorie come vetrina, quarta
  radice della nav — griglia a due colonne di piastrelle illustrate,
  modello Vinted. Vista `view-sfoglia` (niente header, come Ordini e
  Profilo; niente barra di ricerca, che vive in Esplora e duplicarla
  sarebbe un secondo posto da tenere allineato per sempre).
  `renderSfoglia` disegna le voci del catalogo (27 dall'ago 2026) in ordine FISSO, mai
  per numero (una mappa che si riordina ogni giorno non si impara), e
  la griglia è STATICA: si disegna UNA volta sola, e per questo non
  serve nessun dato dal server — zero endpoint nuovi e nessun
  conteggio da rileggere. Il nome va in `data-cat` e mai dentro la
  stringa JS dell'onclick — la lezione di «Valle d'Aosta» sul picker.
  LE CATEGORIE VUOTE SONO PIASTRELLE NORMALI (lug 2026, deciso da
  Andrea guardando la pagina vera). Erano nate spente a metà opacità,
  con i conteggi di `conteggiServer` a decidere chi lo fosse; ma in
  rodaggio le vuote sono la maggioranza — 17 su 26 — e la griglia
  sembrava mezza rotta. Chi ne apre una vuota trova la vetrina col suo
  «🔔 Avvisami se arriva», che è il posto giusto per dirlo: meglio
  dopo, con una via d'uscita in mano, che prima con un colore.
  DUE DETTAGLI DEL PASSAGGIO A ESPLORA, tutti e due nati da un tester
  che li ha visti: `apriCategoria` SVUOTA la griglia prima di partire
  (setCat ricarica dal server e la risposta arriva mezzo secondo dopo:
  senza, si atterra vedendo per un attimo gli annunci della categoria
  di prima, che è la cosa più sbagliata da mostrare a chi ne ha appena
  scelta un'altra); e il tasto Esplora della barra passa da
  `vaiEsplora()`, che riporta ad activeCat='Tutto' — NON è go('esplora'),
  che serve anche a tornare da una scheda e lì il filtro deve restare.
  Chi tocca il nome del tab si aspetta tutto il mercatino, non la
  categoria in cui era entrato da Sfoglia mezz'ora prima.
  MA LA NAV MENTIVA (lug 2026, bug vero visto da Andrea): entrando da
  una piastrella si accendeva «Esplora», e quel che si vedeva era una
  vetrina FILTRATA con pochi oggetti — chi guardava credeva fosse tutto
  il mercatino, e lo trovava vuoto. La vetrina resta UNA (duplicarla
  per Sfoglia sarebbe stato due posti da tenere allineati per sempre):
  a cambiare è solo la RADICE da cui la si guarda, che ora ha un nome —
  `ramoVetrina` ('esplora' | 'sfoglia'). Il giudice unico è `voceNav()`,
  dove viveva già la mappa delle viste interne (dettaglio, negozio e
  sicurezza rispondono alla vetrina; l'ordine agli Ordini) — e per la
  stessa ragione una scheda aperta DENTRO un reparto resta nel ramo: la
  nav dice dove sei, e «dove sei» è la strada che hai fatto, che è
  anche quella che l'indietro ripercorre.
  Il ramo si accende in `apriCategoria` e si spegne in `setCat('Tutto')`
  — cioè quando si torna al catalogo intero da QUALUNQUE strada (il tab
  Esplora, la pillola «Tutto», il ritorno dopo una pubblicazione): un
  posto solo, e il ramo non può sopravvivere al filtro che lo
  giustifica, o resterebbe acceso «Sfoglia» davanti a tutto il
  mercatino — la stessa bugia al contrario. `vaiEsplora` lo chiude
  comunque, anche a categoria già Tutto: il tocco sul nome del tab è
  sempre un ritorno alla radice e non deve dipendere dallo stato di
  un'altra variabile per esserlo. Il ramo NON vive nella cronologia (è
  una variabile, non una entry): un «avanti» del browser dentro un
  reparto ricostruisce la vista ma non il filtro — è la stessa
  imperfezione dichiarata del motore di navigazione, non una nuova.
  CONSEGUENZA sul resto: `renderChips` non riporta più a «Tutto» la
  categoria attiva rimasta senza annunci. Quella scorciatoia era nata
  contro i filtri fantasma, ma con Sfoglia diventava una bugia — si
  tocca «Informatica», che è vuota, e si finisce davanti alla vetrina
  intera senza che nulla lo dica. Ora la categoria scelta resta in
  elenco anche a zero annunci, in TESTA (la fila scorre di lato, e una
  pillola accesa in fondo non la vedrebbe nessuno): è la regola della
  regione nel pannello Filtri, «il campo non deve mentire».
  NAV A CINQUE POSTI: il tondo del Vendi resta al centro ESATTO
  (verificato: 180.0 su 180.0 a 360px) perché le voci sono quattro ma
  gli slot cinque — `.nav-vuoto`, uno spaziatore elastico che tiene il
  quinto posto, vuoto di proposito e già destinato a qualcos'altro. In
  topbar desktop sparisce (lì i bottoni sono `flex:0 0 auto`).
  L'ORDINE è [Esplora][Sfoglia](+)[vuoto][Ordini] (lug 2026): il posto
  vuoto sta IN MEZZO, fra Vendi e Ordini, non in coda — così gli Ordini
  restano all'estrema destra, dove il pollice li trova senza guardare.
  Spostarlo è solo uno scambio di posto nel markup: voci e spaziatore
  sono tutti `flex:1`, quindi il Vendi resta il terzo di cinque slot
  uguali e nessuna regola CSS si tocca (misurato: centro invariato,
  nav 61,2px, e da desktop lo spaziatore è già `display:none`).
  LE ICONE SONO NOSTRE (lug 2026): tre SVG al posto delle emoji
  🛍️🗂️🤝, che cambiavano forma da un telefono all'altro e non
  seguivano i token del tema — LENTE per Esplora, PIASTRELLE per
  Sfoglia (la sua pagina in miniatura), PACCO di tre quarti per gli
  Ordini. Inline nel markup, non da JS: nessun lampo all'avvio e la
  barra esiste prima che il primo script giri. Disegnate sulla griglia
  da 24 con la mano di `tagliaSVG` e `jarSVG` — tratto a currentColor,
  capi tondi, velo al 12% (classe `.velo`) che dà corpo — e fuori
  squadra di un pelo, che è la personalità delle illustrazioni delle
  categorie portata dove un'immagine non può arrivare.
  LA VOCE ATTIVA SI ILLUMINA E BASTA (modello Vinted e Subito): via la
  pillola pesca sotto l'icona e il suo anello, resta il colore —
  `--sats-deep` di giorno, `--sats-text` di sera (sul bruno l'arancio
  del giorno rende 4,8, quello della sera 8,5: si abbassa la LUCE, non
  si cambia il segno — la regola della spedizione gratuita). Icona ed
  etichetta si accendono INSIEME senza una riga di codice: il colore lo
  dà il bottone, l'icona lo eredita con currentColor. È tutto ciò che
  rende possibile l'accensione, ed è il motivo per cui qui non possono
  esserci immagini. Niente transizioni, quindi
  `prefers-reduced-motion` non ha nulla da spegnere.
  MISURA 26px, ed è un TETTO: è quanto occupavano le emoji col loro
  respiro (20 di glifo + 3+3 di padding), quindi la nav resta 61px e
  l'invariante con `#barraCompra` è salva. Per crescere ancora
  servirebbe una barra più alta, e quella non si tocca. Il resto della
  presenza si prende dove non costa nulla: il viewBox è `2 2 20 20` e
  non `0 0 24 24` — la stessa griglia RITAGLIATA sul margine che
  avanzava attorno all'inchiostro (le tre stanno fra 2,65 e 21,35 col
  tratto compreso: verificato, il ritaglio non taglia). Il disegno
  cresce del 30% dentro la stessa scatola e il tratto scende a 1.5
  perché ingrandito con lui torna a rendere 1,95px: stesso peso, figura
  più grande. È il gemello del ritaglio che `ritaglia_categorie.py` fa
  alle illustrazioni — il margine trasparente è spazio buttato. Chi
  ridisegna un'icona tenga l'inchiostro dentro [2,22], o il ritaglio
  gliela taglia. In topbar desktop stanno a 22px e la voce attiva torna
  una pillola: lì non è una tab bar da pollice ma una fila di
  linguette, e la pillola è il suo idioma.
  TRE STRADE PROVATE E SCARTATE, coi motivi, che è la parte che serve
  fra sei mesi: 1) il PACCO PIATTO — quadro più riga del coperchio, cioè
  la famiglia di `tagliaSVG` — a 24px si legge come un portafoglio, e
  col nastro verticale intero come una finestra a quattro riquadri; di
  tre quarti è un pacco e basta, e la parentela con le taglie si perde
  ma si guadagna un'icona che si riconosce. 2) IL BARATTOLO del logo,
  chiesto da Andrea, disegnato e guardato acceso: funziona, ma nella
  STESSA schermata quella forma farebbe tre mestieri — marchio in
  testata, «l'ho messo via» sulle card (dove per giunta è pieno o vuoto
  e racconta un livello), «dove sono» in barra — e i primi due si
  vedono insieme, uno sopra l'altro, in ogni vetrina. La lente invece
  non dice niente altrove: è libera. 3) LE ILLUSTRAZIONI delle
  categorie rimpicciolite a 24px: a quella misura il disegno diventa
  una macchia calda, e soprattutto un'immagine NON PUÒ ACCENDERSI — il
  meglio che si può fare per spegnerla è sbiadirla (grigio più
  opacità), che la fa sembrare rotta, non spenta. Guardate a schermo
  tutte e tre prima di decidere; non riproporle senza un motivo nuovo.
  IL GESTO INDIETRO ha qui la sua UNICA eccezione, ed è dichiarata: il
  tocco su una piastrella porta a Esplora, che è una radice — ma non è
  un cambio di tab, è una DISCESA, e l'indietro deve riportare allo
  scaffale. `navSpingi` è una bandierina alzata da `apriCategoria` e
  letta-e-azzerata in cima a `navRiflette` (prima di ogni via d'uscita,
  o si scaricherebbe su una navigazione che non l'ha chiesta).
  LE ILLUSTRAZIONI: 27 WebP in `assets/categorie/{slug}.webp`, nome
  calcolato da `slug_categoria` (server) e `slugCat` (client) — nessun
  elenco doppio. Sono SCONTORNATE su trasparenza, non su un fondo:
  quindi il colore della piastrella è una scelta nostra, ed è un BRUNO
  di casa (`--cat-fondo`), scuro perché i disegni sono in tinte calde e
  sabbiose — misurato sui file veri: su un `--carton` chiaro
  venticinque su ventisei scenderebbero sotto 3:1 (media 1,85), cioè
  sparirebbero. Di sera sale di un gradino, che la pagina è già bruna e
  la piastrella deve staccarsene; un gradino più chiaro di giorno è
  stato provato a schermo e rimesso indietro (decisione di Andrea).
  LA PIASTRELLA È UNA COLONNA FLEX, e questa è la parte che vale: nome
  sopra a quota propria, illustrazione sotto che si prende TUTTO il
  resto. Finché erano due strati sovrapposti, ogni pixel dato al
  disegno andava misurato contro la riga di testo — e il tetto restava
  56px, perché le illustrazioni hanno zone quasi bianche e il nome in
  crema ci faceva 1,00:1, cioè spariva. Un velo scuro sfumato sotto il
  nome, provato, salvava il testo ma spegneva il 55% dei disegni: cura
  un male causandone un altro. Col flex non possono pestarsi PER
  COSTRUZIONE e il disegno arriva a 73px. Perché siano TUTTI della
  stessa altezza serve che nessun nome vada a capo: 14px col margine a
  9 è la taratura che fa stare in una riga anche il più lungo
  («Console e videogiochi»: ne chiede 140 e ne ha 141, a 360px). Chi
  alza il corpo del testo rimette quelle voci su due righe, e quelle
  piastrelle avranno il disegno più piccolo delle altre.
  MA L'ALTEZZA UGUALE NON BASTA, e questa è la lezione che si paga
  guardando tutte e 26 insieme invece che una alla volta. Prima
  scappano le LARGHEZZE (la scarpa faceva 122×72 contro l'orologio
  47×72), e a quello risponde il TETTO alla larghezza del riquadro,
  54% della piastrella. Ma anche a rettangoli pari le icone non
  sembrano uguali: un pallone e una chitarra possono occupare lo
  stesso rettangolo, ma il pallone è pieno e la chitarra è un filo —
  a pesare è l'INCHIOSTRO, cioè quanti pixel pieni il disegno copre.
  Misurato: le sei che Andrea ha indicato «troppo grosse» erano le
  sei più cariche d'inchiostro, e la chitarra «troppo piccola» era la
  più leggera. Il rettangolo non lo diceva; l'inchiostro sì.
  Il pareggio lo fa `ritaglia_categorie.py`, che mette un TETTO
  sull'inchiostro reso (1,05× la mediana) e dà un bordo trasparente a
  chi lo supera — il disegno non si tocca, si rende più piccolo in
  pagina. Il contrario non si può: i più leggeri sono già al massimo
  che la piastrella concede, quindi la chitarra resta la più leggera,
  ed è un limite dichiarato. Per questo l'immagine è CENTRATA nel suo
  riquadro (`object-position:50% 50%`): coi bordi del pareggio,
  ancorarla a un angolo l'avrebbe allontanata chi più chi meno.
  Normalizzare l'AREA del rettangolo è stato provato e scartato: per
  far stare gli estremi ogni disegno scende sui 57px e le piastrelle
  si svuotano — si perde su tutte per pareggiare due casi.
  `ritaglia_categorie.py` toglie il margine trasparente che le
  illustrazioni hanno di fabbrica (~30%): senza, un terzo dello spazio
  della piastrella sarebbe vuoto e il disegno si vedrebbe piccolo. È
  idempotente e va rilanciato quando si aggiunge o si rifà
  un'illustrazione; `prove.py` verifica che i file siano tirati, che è
  l'invariante su cui il CSS poggia.
  L'ALPHA SI GUARDA SOPRA UNA SOGLIA (8 su 255), non sopra lo zero, e
  la ragione è un caso vero: «Bellezza e benessere» arrivava con una
  velatura quasi invisibile stesa su TUTTA la tela, quindi col
  confronto a zero risultava già tirata — il ritaglio non la toccava e
  il disegno vero, 329×236 dentro un quadrato da 512, si vedeva molto
  più piccolo degli altri. Sugli altri 25 file la soglia sposta il
  riquadro di 4px in tutto. La stessa soglia sta nella prova, o
  lascerebbe passare proprio il caso che deve prendere. Lo script non
  riscrive per scarti sotto il 2%: così rilanciarlo non ricomprime
  ogni volta tutto (i file sono lossy, e la regola della compressione
  unica vale anche qui).
  MISURE tarate su QUANTE piastrelle stanno in una schermata: dieci,
  come nel riferimento (decisione di Andrea). A 360×760 restano 630px
  fra l'etichetta e la nav, cioè cinque righe da 120 — piastrella 110 e
  gap 10, che con la larghezza 159 fa `aspect-ratio:1.445`. Per questo
  l'etichetta non porta il `padding-top` maggiorato delle altre viste e
  la griglia ha 8px di respiro invece di 12: sono i pixel della quinta
  riga. 3 colonne da 768px, 4 da 1024.
  NEL PICKER DI VENDI ci sono le ILLUSTRAZIONI (lug 2026: prima le
  emoji, poi la prova a schermo ha convinto Andrea del contrario).
  `icoCategoria()` le rende nude a 30px, nelle voci del foglio e nel
  campo chiuso, e il file è il FRANCOBOLLO `{slug}-mini.webp` da 128px
  — non quello pieno: 181 KB in tutto invece di 787, e 1,4 MB di
  bitmap invece di 13, per un menu che si apre in due secondi. Li fa
  `ritaglia_categorie.py` dai file già pareggiati, così le proporzioni
  del menu sono quelle della griglia senza un secondo posto da tarare;
  la rotta `/assets/categorie/{nome}` accetta il suffisso passando
  dalla stessa whitelist, e `prove.py` controlla che ci siano tutti e
  26 (manca solo lì dentro, e il ripiego a emoji fa sembrare che vada
  tutto bene). Classe `.cat-ico` e non `.p-ico`, che è condivisa con
  le taglie del pacco.
  IMPERFEZIONE DICHIARATA, ed è il prezzo della resa nuda: il foglio
  in tema chiaro è BIANCO, e questi disegni usano il crema come colore
  del CORPO — così il barattolo di crema ci perde il corpo (restano
  coperchio e contagocce a mezz'aria) e il telefono e il ciak si
  assottigliano. Gli altri 23 reggono, e in tema scuro reggono tutti.
  La pastiglia scura sotto l'icona è stata provata e SCARTA­TA: dava
  contrasto a tutti e rendeva identici i due temi, ma trasformava una
  lista da scorrere in un cassetto di app. Se un giorno si vorrà
  chiudere quel buco, la strada non è il CSS: è rifare quei tre
  disegni con un corpo che non sia quasi-bianco.
  `categoria_automatica` di importa_nostr.py NON ESISTE PIÙ (lug
  2026): indovinare la categoria dal titolo sbagliava in silenzio — lo
  «Sparkling Sake» finiva fra gli arredi perché quella categoria
  pescava «cucina» — e sugli importati nessuno se ne accorgeva. Gli
  annunci da Nostr nascono in «Altro» e a collocarli è il VENDITORE,
  che è l'unico a saperlo; l'import non ricopre mai una categoria già
  scelta, quindi la sua resta per sempre, e a chiederglielo c'è il DM
  di completamento (vedi import aperto).
  Frontend: pillole ordinate per numero di annunci ATTIVI
  (decrescente), "Tutto" sempre prima, le vuote non compaiono proprio
  (Tutto e la ricerca coprono la scoperta); conteggi dai listings
  caricati, rifatti a ogni giro in `renderChips()` (chiamata da
  `loadListings` e `avviaVetrina`); se la categoria attiva resta
  senza annunci si torna su Tutto. Vale per vetrina autenticata,
  anonima e DEMO (dati finti già rimappati). Dal cantiere «tenuta al
  volume» (sotto) i conteggi delle pillole coi dati vivi vengono dal
  server (`conteggi` in prima pagina), il locale resta per la demo.
  Condizioni dell'oggetto (lug 2026): scala a 5 livelli — catalogo
  `CONDIZIONI` in server.py (nuovo | come_nuovo | buono | accettabile |
  da_sistemare, id → etichetta breve; il catalogo JS `CONDIZIONI` del
  client porta anche la `desc` breve del foglio di scelta, e le
  <option> del form — ormai un deposito nascosto, vedi il
  foglio-picker — le etichette lunghe). Colonna `annunci.condizione`
  ('' = storici e importati, nessun obbligo retroattivo), OBBLIGATORIA
  client E SERVER (dal lug 2026, deciso: `guardia_zona_condizione` — giudice
  unico di pubblica e modifica — risponde 400 su assente o
  sconosciuta; gli storici si mettono in regola al primo ritocco; MAI
  nella modifica firmata degli importati, l'evento NIP-99 non la porta
  e il campo si nasconde, e la guardia in modifica scatta DOPO i
  controlli di proprietà/stato: chi tocca un annuncio in revisione
  deve sentirsi dire quello. L'import CSV resta tollerante:
  `condizione_tollerante`, colonna facoltativa). In
  CAMPI_VETRINA (search e miei gratis via a.*); param `condizione` su
  /api/listings (dichiarata soltanto: gli storici '' restano fuori,
  valore storto = nessun filtro) + scelta nel pannello Filtri (in DEMO
  client-side; dal lug 2026 anche lei un foglio-picker, con le pillole
  NUDE senza le descrizioni e la voce «Qualsiasi condizione»).
  IL SEGNO (lug 2026, dopo il feedback di Andrea): PILLOLA TESTUALE
  COLORATA `condPill()` — forma delle pillole di zona e categoria, la
  scala parla col COLORE (classi `.pill.cond-*`: verde pieno
  `--trust-deep` → verde tenue `--trust-soft` → ambra oro → arancio
  `--sats-soft` → grigio `--off-bg`, coppie della palette con
  contrasto AA misurato nei due temi; l'oro resta chiaro di sera come
  l'etichetta prezzo, e due override `html[data-tema="scuro"]` dove la
  coppia chiara non regge al buio). Vive nel dettaglio e nel
  foglio-picker del form, MAI in card: la vetrina resta pulita (le
  emoji ✨🌟👍🆗🔧 non comunicavano una gradazione; i pallini graduati
  ●●●○○ provati al loro posto si confondevano con le stelle delle
  recensioni — bocciati, non riproporli). Riga «— condizione:
  …» nel content NIP-99 (nessun tag: la spec non ne ha uno, pattern
  della spedizione) e nel catalogo della ricerca AI; colonna
  facoltativa `condizione` nel CSV d'import con `condizione_tollerante`
  (SINONIMI_CONDIZIONE: «ottimo» → come_nuovo, «da riparare» →
  da_sistemare…, sconosciuta = non dichiarata, mai uno scarto).
  DOVE LA CONDIZIONE NON VUOL DIRE NIENTE (lug 2026, decisione di
  Andrea): una marmellata è nuova per definizione, e chiederlo è una
  domanda senza risposte sbagliate — cioè una domanda inutile. La leva
  è `CATEGORIE_SENZA_CONDIZIONE` (frozenset accanto a CATEGORIE:
  «Alimenti e bevande» e «Bellezza e benessere» — creme, profumi e
  integratori si vendono nuovi, e un cosmetico già usato non è merce
  di seconda mano, è una cosa che non si vende — e dall'ago 2026
  «Buoni ed esperienze»: un buono è nuovo per definizione, anche la
  tessera fisica) e il giudice unico è
  `senza_condizione(categoria, consegna)`, da cui passano form,
  dettaglio, vetrina, NIP-99, ricerca AI e import — o divergono. Il
  secondo asse è la CONSEGNA: un codice Zalando è nuovo per
  definizione come la marmellata, ma vale solo per il digitale
  ESCLUSIVO (`consegna=='digitale'`) — sulla combo la merce fisica c'è
  e una condizione ce l'ha, quindi si guarda quella colonna e MAI
  `anche_digitale`. NON ci entrano «Arte e artigianato» (ci finisce
  anche l'arte usata, e un quadro di seconda mano può essere rovinato)
  né «Bitcoin» (le Jade di seconda mano sono merce vera).
  Tre conseguenze, e sono la parte da ricordare: 1) in SCRITTURA si
  azzera — `guardia_zona_condizione` non la chiede più e butta quella
  che arriva, così il database si pulisce da solo un annuncio alla
  volta invece che con una migrazione (e se domani quell'annuncio
  cambia categoria, la condizione gliela si chiede lì, che è quando
  serve: lo stesso patto della zona storta); 2) gli alimentari di
  IERI, che in colonna una condizione ce l'hanno, NON si migrano — il
  dato non si perde mai, come la zona resta intera nel database mentre
  in vetrina si mostra il solo comune — e a nasconderla è
  `condizione_da_mostrare` in uscita (lato client il gate è
  `titoloConCondizione`, l'unico posto dove la pillola si disegna:
  così vale anche per la DEMO, che non passa da mapListing); 3) il
  FILTRO condizione li lascia fuori (patto degli storici: il filtro
  promette una condizione dichiarata), e il vecchio con la colonna
  piena lo escludono le due clausole aggiunte alla query — o
  pescherebbe una condizione che la scheda non mostra più. In vetrina
  la riga «Condizione» del pannello Filtri sparisce sulle categorie
  esenti e il filtro DORME (`condFiltrabile()` toglie il parametro):
  non si azzera, o si romperebbe il patto dei filtri di sessione che
  sopravvivono al cambio categoria. Gemello client `CAT_SENZA_COND` +
  `senzaCondizione()`, e `prove.py` fallisce se i due elenchi
  divergono. Nel form il campo compare e sparisce da
  `aggiornaCondizioneForm()`, chiamata dal `poi` del picker categoria
  e da `aggiornaConsegnaForm()` (i due soli ingressi che la cambiano).
  Foglio-picker al posto delle tendine native (lug 2026): la
  `<select>` del sistema operativo non si può vestire da Barattolo, e
  TUTTE le tendine dell'app sono passate al nostro foglio — categoria,
  condizioni e taglia del pacco nel form Vendi, condizioni nel
  pannello Filtri, ordinamento della vetrina. Il MOTIVO per cui non è
  una riscrittura: la select resta in pagina come DEPOSITO del valore
  (attributo `hidden`), e tutto il JS di prima continua a leggerla e
  scriverla (`el('sellCond').value`) — publish, modifica, reset,
  filtri e validazioni intonsi. A parlare col dito è il campo-bottone
  `.campo-scelta` (`#{id}Btn`, veste da select con la freccia ▾) che
  apre `#pickerSheet` col pattern dei fogli di sempre: `PICKER` è il
  catalogo, e ogni voce dichiara `titolo`, `voci()` (val + resa nel
  foglio), `campo(v)` (resa nel campo-bottone) e un `poi` facoltativo
  — l'azione che prima stava sull'`onchange`, indispensabile
  all'ordinamento (`setOrdina`), che con la select nascosta non riceve
  più l'evento. `apriPicker` disegna e mette a fuoco la voce scelta,
  `scegliPicker` scrive nel select, chiude ed esegue `poi`;
  `aggiornaPicker(id)` riallinea il campo al valore e VA RICHIAMATA da
  chiunque tocchi il select via JS (`aggiornaPickerVendi()` fa i tre
  del form in blocco, così non se ne dimentica uno: è in editListing,
  annullaModifica e publish; più setOrdina, toggleFiltri e
  azzeraFiltri per gli altri due). Le stesse condizioni si rendono in
  DUE modi secondo il posto: col form la pillola + la descrizione (che
  aiuta a scegliere), nel filtro le pillole NUDE (lì non si impara la
  scala, si sceglie). Accessibilità: `role="dialog"`/`radiogroup`, Esc
  chiude, frecce ↑↓ scorrono, e `pickerTrigger` riporta il focus al
  campo per OGNI strada di chiusura — un campo-bottone `display:none`
  però non può prenderlo (succede solo forzando il picker da codice su
  un campo nascosto, come la taglia senza Spedizione spuntata).
  CHIUSURA CHE NON FA CATENA (lezione del secondo giro): `scegliPicker`
  chiamava `closeSheet()`, che spegne TUTTA la pila di fogli e azzera
  il `pollTimer`. Invisibile finché il picker si apre da una vista o
  dal pannello Filtri (che è markup in pagina, non un foglio: finisce
  sotto il velo e resta aperto dopo la scelta), ma aperto da DENTRO un
  foglio avrebbe chiuso anche quello sotto — e sopra il paySheet
  avrebbe ucciso il polling del pagamento. Quindi `chiudiPicker()`
  spegne solo il picker e tiene il velo se `altroFoglioAperto()`, e
  `tapFuoriSheet()` sul velo chiude il foglio più in ALTO invece della
  pila (`closeSheet` resta il catch-all). Il picker si può quindi
  aprire dentro un foglio senza pensarci. Cintura in CSS:
  `select[hidden]{display:none !important}`, perché le nostre select
  si pescano per tag (`.field select`, `.strumenti select`) e una
  futura regola col `display` farebbe ricomparire la tendina di
  sistema. Tre vestiti per tre contesti, stesso markup:
  `.campo-scelta` è la misura da campo di form, `.strumenti
  .campo-scelta` la ritara a pillola come il bottone Filtri (con
  l'etichetta che si accorcia coi puntini, vedi il contatore dei
  pionieri più sotto), `.filtri-riga .campo-scelta` la veste come gli
  input di accanto. Dal primo giro: `prefers-reduced-motion` ora
  ferma la scivolata di TUTTI i fogli (`.sheet{transition:none}`),
  che mancava da sempre.
  Tenuta al volume (lug 2026): la vetrina va a PAGINE col cursore
  keyset. `/api/listings`, `/api/negozio/{chi}` e `/api/listings/miei`
  accettano `limit` (clampato a 100) e `cursore` = '{creato}_{id}'
  dell'ultima riga (ordine `creato DESC, id DESC`; cursore storto =
  prima pagina, mai 400; helper unico `pagina_annunci`). Il
  discriminatore è retro-compatibile nei DUE sensi: SENZA `limit` la
  risposta è l'array di sempre col tetto di sicurezza 500 (un JS
  vecchio in cache vive felice), CON `limit` è la busta
  `{annunci, cursore}` + SOLO in prima pagina `totale` (della vista:
  rispetta cat/q) e `conteggi` (globali per categoria); il negozio
  AGGIUNGE le chiavi al dict di sempre; un server vecchio col JS
  nuovo = array letto come pagina unica (`leggiPagina`). Indici
  `idx_annunci_vetrina/categoria/venditore` in `init_db`. Param `q`
  su /api/listings = ricerca semplice LIKE (titolo/descrizione/zona)
  per la vetrina ANONIMA, componibile con cat+cursore. Ordinamento e
  filtro prezzo (lug 2026): param `ordina` (vuoto = più recenti |
  prezzo_su | prezzo_giu; catalogo `ORDINAMENTI`, keyset su
  (prezzo_sats, id) con `idx_annunci_prezzo`; sconosciuto = default,
  mai errore) e `prezzo_min`/`prezzo_max` + `valuta_filtro` (eur =
  conversione LATO SERVER con `cambio_btc_eur`, 503 se il cambio
  manca; il confronto è sempre su prezzo_sats, che per i listini EUR
  è l'equivalente al cambio di pubblicazione — dichiarato). Frontend:
  select discreto + pannello «Filtri» sotto l'etichetta della griglia
  (`.strumenti`, `setOrdina`/`applicaFiltri`/`azzeraFiltri`), filtro
  nella valuta del toggle attivo al momento di Applica, stato per
  SESSIONE (mai localStorage) che sopravvive al cambio categoria
  (patto delle app di mercatino), in DEMO client-side sui dati finti.
  La ricerca AI coi vincoli scritti resta separata da questi filtri
  di navigazione. Le MINIATURE dal lug 2026 sono QUADRATE
  (ImageOps.fit al centro, 640 q87 LANCZOS, `MINIATURA_LATO/QUALITA`):
  la card 1:1 col cover ingrandiva il lato corto delle vecchie
  rettangolari (la sgranatura); il backfill rifà da solo quelle di
  ricette vecchie confrontando le intestazioni col lato CORTO della
  foto piena. Nasce
  `GET /api/listings/{id}` (registrato DOPO /miei: l'ordine delle
  rotte conta) per il deep-link /annuncio/{id} oltre le pagine
  caricate. La ricerca AI legge una SHORTLIST (`TETTO_CATALOGO_AI`
  300): match LIKE sulle parole della query + i più recenti a
  riempire — compromesso dichiarato: il sinonimo puro fuori dai 300
  più freschi può sfuggire. FOTO: accanto a ogni JPEG pieno nasce
  `a{id}_{i}{ver}_min.jpg` (vedi ricetta miniature più sotto) — nel DB
  restano SOLO i nomi pieni, `_min` è convenzione che il frontend
  deriva (`fotoMini`); backfill idempotente all'avvio
  (`genera_miniature_mancanti`), la modifica cancella anche la
  gemella, Cache-Control di 1 giorno su /foto (i nomi sono
  versionati). Frontend: prima pagina da 30 (`LIMITE_PAGINA`) e
  scroll infinito con sentinelle + IntersectionObserver (vetrina,
  negozio, tuoi annunci; guardie DENTRO le callback: demo, ricerca
  AI, fine lista). ATTENZIONE alla separazione: `vetrina` = pagine
  accumulate, ciò che la griglia disegna; `listings` = CATALOGO per
  openDetail, ci confluiscono negozio/risultati AI/deep-link SENZA
  sversare in griglia (`inCatalogo` update-or-push; in DEMO stesso
  array, e chi riassegna `listings` in demo deve riallineare
  `vetrina`). Append con insertAdjacentHTML (niente flicker); i
  rebuild pieni di valuta/cambio ridisegnano l'accumulato; categoria
  e ricerca ripartono dalla prima pagina (setCat/doSearch rifanno
  `loadListings`). Le card montano la `_min` con ripiego `data-full`
  sull'originale via onerror + dataset (MAI l'URL dentro una stringa
  JS interpolata: è il patto anti-XSS del filtro-alfabeto); galleria
  del dettaglio lazy dopo la prima foto.
  IL GIRO DELLA VETRINA (lug 2026, da un bug vero: entrando in una
  categoria da Sfoglia ogni annuncio compariva DUE volte). Non era la
  griglia disegnata due volte — `renderGrid` riscrive sempre
  l'`innerHTML` — ma la PAGINA DOPO che arriva in ritardo e si
  appiccica in fondo a una griglia già rifatta da un'altra vista:
  `apriCategoria` svuota la griglia, quindi la sentinella si SCOPRE e
  chiede la pagina successiva col cursore della vista PRECEDENTE mentre
  la prima pagina della categoria è ancora per strada. E su una
  categoria piccola quella «pagina dopo» è ESATTAMENTE la prima — il
  cursore globale è più recente di tutti i suoi annunci, quindi il
  `creato <` li prende tutti. Il rimedio è `vetrinaGiro`, un numero che
  avanza a ogni ricarica di PRIMA pagina: `loadListings` lo fa avanzare
  e azzera SUBITO `vetrinaCursore` (la sentinella scoperta non ha più
  niente da chiedere e tace da sola), e tutte e due le funzioni buttano
  la propria risposta se il giro è cambiato — il che para anche i due
  tocchi svelti su due categorie: vince l'ultima, senza mescolare.
  REGOLA: chi aggiunge una vista paginata (negozio, miei) e la svuota
  prima di ricaricarla deve darle il suo giro, o si ricompra questo bug.
  Modifica annuncio (lug 2026): `POST /api/listings/{id}/modifica` —
  solo il proprietario su annunci attivi, 400 se esiste un ordine NON
  terminale (anche `creato`: chi sta pagando deve trovare l'annuncio
  com'era) e per gli annunci importati da Nostr (contatto_nostr pieno:
  l'import orario li sovrascriverebbe). Ripassa TUTTI gli strati di
  moderazione come una pubblicazione nuova (notifiche admin «✏️»);
  foto sostituite in blocco solo se il campo `foto` arriva (nomi
  versionati col timestamp anti-cache del browser, file vecchi
  cancellati dal disco), altrimenti restano; ripubblica su Nostr con
  `solo_aggiornamento=True` (il tag `d` stabile sostituisce l'evento).
  Frontend: form di Vendi riusato e precompilato (banner «Stai
  modificando» + bottone che diventa «Salva le modifiche»), bottone
  ✏️ nel dettaglio e badge nei tuoi annunci; le foto attuali si
  tengono o si sostituiscono tutte, mai a pezzi.
  Modifica FIRMATA degli importati (lug 2026): il doppio cittadino con
  `npub_accesso` ≡ `contatto_nostr` modifica anche gli annunci
  importati — Barattolo fa da client Nostr, la nsec resta nel browser
  (regola 2). Due fasi: `POST /api/listings/{id}/modifica-firmata/
  prepara` (stesse guardie di modifica + moderazione COMPLETA prima
  della firma — dopo sarebbe teatro, l'import riporterebbe dentro —
  chiavi sempre confrontate via `npub_to_hex` sui due lati) risponde
  `{biglietto, evento, relays, collaudo}`: evento NIP-99 NON firmato,
  senza pubkey, `d` = `annunci.nostr_origine_d` (sostituzione NIP-99),
  `image` verbatim da `nostr_origine_foto` (ripiego `_foto_url_nostr`),
  content = descrizione PURA (MAI il footer promozionale: rientrerebbe
  in descrizione al giro d'import); biglietto in
  `BIGLIETTI_MODIFICA_NOSTR` (TTL 10 min: l'auth_url del bunker è
  lento). Il client: firma SENZA rituale quando può (lug 2026) —
  ordine: sessione bunker conservata → estensione `window.nostr` →
  foglio (`apriNostrSheet(scopo)` / `scopoFirmatario`, titolo «Firma
  con la tua chiave») solo come ultima porta o quando la strada
  automatica è morta/ha un'altra chiave (mismatch in auto = si
  ripassa dal foglio, non è un errore dell'utente). La sessione
  NIP-46 (URI bunker + chiave del CLIENT) vive in
  `localStorage['barattolo_bunker']` (`ricordaBunker`/`bunkerSalvato`/
  `scordaBunker`, salvata a ogni connect riuscito, scordata se il
  bunker non risponde): EQUIVALENZA DICHIARATA col secret NWC già
  conservato — pari grado, può chiedere firme al bunker (che può
  sempre negarle o revocare la sessione), MAI derivare la chiave
  dell'utente, mai sul server. La nsec incollata resta il rito di
  sempre (mai conservata, by design; il foglio suggerisce il bunker).
  I passi comuni vivono in `firmaEConsegna`: pubkey controllata PRIMA
  di firmare (la nsec si azzera dopo UNA firma), id ricontrollato in
  pagina (firmatario che altera = stop), pubblicazione dal browser
  (`pubblicaEventoSuRelay`, serve ≥1 OK, relay = quelli dell'IMPORT
  col relay personale del venditore, non RELAYS_VERIFICA) e SOLO poi
  `POST …/modifica-firmata` con `{biglietto, pubkey, sig}`: il server
  RICOSTRUISCE l'evento dal biglietto (divergenza impossibile),
  verifica Schnorr, ri-esegue le guardie economiche (TOCTOU) ma non la
  moderazione, aggiorna la copia locale dal payload del biglietto e
  rispedisce l'evento come backstop. Relay muti → niente POST, nulla
  cambia; POST fallito dopo i relay → messaggio onesto, l'import
  orario riconcilia entro un'ora (per gli importati i relay SONO la
  fonte di verità). Foto immutabili (v1, il form lo dice), solo kind
  30402, Telegram-only senza chiave → 400 di sempre. In collaudo anche
  il BROWSER simula la pubblicazione (flag `collaudo` da prepara:
  imparato quando il primo collaudo ha pubblicato sui relay veri).
  L'import (importa_nostr.py) per questo RICORDA le coordinate:
  colonne `annunci.nostr_origine_d` e `nostr_origine_foto` (URL image
  originali) scritte su INSERT e UPDATE, e il match verso il DB è
  PRIMA per tag `d` (sopravvive ai titoli cambiati: prima duplicava),
  poi per titolo ma solo su righe non ancora battezzate
  (`nostr_origine_d=''`); scudo anti-resurrezione (lug 2026, da un
  bug vissuto in produzione): se la coordinata (o il titolo) matcha
  una riga NON attiva — rimossa o venduta su Barattolo — l'annuncio
  NON si ricrea (skip con riga ⛔ nel journal): prima il match
  guardava solo gli attivi e l'evento ancora vivo sui relay rifaceva
  l'INSERT a ogni giro; un tag `d` diverso resta un annuncio nuovo.
  Cantiere cancellazioni COMPLETO (lug 2026, tappe 2-3): `interroga`
  chiede anche i kind 5 (NIP-09) del venditore e li rispetta —
  cancellazione vista su QUALUNQUE relay = riga locale spenta
  ('rimosso', ordini 'creato' annullati via `spegni_annuncio`,
  gemello della rimozione Mini App, riga 🪦 nel journal) e LAPIDE
  nella tabella `nostr_lapidi` (PK hexkey+d+event_id, creata
  dall'import), riletta TUTTA a ogni giro: vale per sempre anche
  quando i relay scordano il kind 5, e rispegne perfino una riga
  riaccesa da un rimborso (per questo niente return secco a mani
  vuote). Tag `a` per coordinata (solo 30402/30018 della SUA chiave),
  tag `e` per id: risolto in coordinata se l'evento è tra i letti,
  altrimenti matcha la colonna `annunci.nostr_origine_id` (scritta a
  ogni INSERT/UPDATE). Sotto lapide non si re-importa MAI più,
  nemmeno ripubblicando lo stesso `d` (imperfezione dichiarata: per
  tornare serve un `d` nuovo). Lo status sold di un evento
  aggiornato SPEGNE la riga come 'venduto' (riga 🏷️; prima restava
  attiva e COMPRABILE) — niente lapide, ma lo scudo la tiene spenta
  anche se lo status tornasse active (dichiarato, stesso rimedio);
  sul match aggiorna anche
  titolo/descrizione/zona e valuta/prezzo_eur dal tag price (EUR →
  doppia valuta anche per gli importati), MAI la categoria
  (categoria_automatica ricoprirebbe la scelta del form); foto
  invariate (stessi URL di `nostr_origine_foto`) = niente ri-download
  orario.
  Deduplica dei doppioni su Nostr (lug 2026): il doppio cittadino può
  avere lo stesso oggetto DUE volte sui relay — l'importato firmato da
  LUI e il nativo ripubblicato dalla piattaforma (invariante:
  `contatto_nostr` e `nostr_event_id` mai sulla stessa riga).
  `trova_doppioni_nostr` (guardia EXISTS: chi non ha importati esce
  subito, e quasi nessuno li ha) rileva le coppie con match STRETTO,
  mai fuzzy: impronta del titolo identica (token di `normalizza`
  ordinati alfabeticamente: maiuscole, accenti e ordine parole non
  contano) + prezzo compatibile (EUR vs EUR scarto ≤10%; altrimenti
  sats ≤30%, largo perché l'import riconverte l'importato a ogni giro
  mentre il nativo resta al cambio di pubblicazione). Pochi match
  certi: il falso positivo residuo (due esemplari genuini identici) è
  coperto dalla conferma esplicita e dall'archivio. Le coppie escono
  in `/api/me.doppioni_nostr` → cassetto «🔁 Doppioni su Nostr» nel
  Profilo (`renderDoppioni`, sparisce se vuoto/DEMO/VETRINA); dopo la
  fusione il messaggio del bot CONTA i doppioni trovati invece del
  sospetto generico. «Non è un doppione» = riga in
  `doppioni_ignorati` (server-side: mai riproporlo vale su ogni
  dispositivo, non è roba da localStorage). Il ritiro
  (`POST /api/me/doppioni/{id_nativo}/ritira`, conferma esplicita,
  MAI automatico) manda la NIP-09 della PIATTAFORMA sul SUO evento —
  gli eventi dell'utente non si toccano mai — via
  `ritira_da_nostr(esigi_ok=True)`: senza ≥1 relay OK non cambia
  NULLA (502 onesto, si riprova); col successo `nostr_event_id` si
  svuota, il che spegne ogni ripubblicazione (i ganci sono tutti
  `solo_aggiornamento=True`) e fa sparire la coppia da sola
  (derivata dai dati veri, niente stato sul successo). L'annuncio su
  Barattolo resta attivo, solo-locale. Il ritiro fire-and-forget di
  rimozione/admin usa la stessa funzione col default di sempre
  (azzera comunque).
  Formati foto: la miniapp converte in JPEG 1200px via canvas tutto
  ciò che il browser decodifica (WebP ovunque, HEIC su iPhone).
  FILIERA A UNA SOLA COMPRESSIONE (lug 2026): il JPEG del canvas
  (imageSmoothingQuality 'high' + qualità 0.9 — senza il filtro
  'high' il resize mangiava ~1/4 del dettaglio) viene salvato da
  `salva_foto` COSÌ COM'È, mai riconvertito; i formati che passano
  dal server (`converti_in_jpeg`: LANCZOS, quality 88 +
  `ImageOps.exif_transpose`, che il canvas fa da solo e Pillow no)
  subiscono anche loro UNA sola compressione. Chi tocca la filiera
  non deve MAI aggiungere un passaggio JPEG→JPEG sul file pieno
  (~-2dB a giro); la `_min` deriva dal pieno salvato ed è l'unica
  seconda generazione ammessa (è un francobollo). Ciò
  che non sa leggere (HEIC su Android/desktop) parte grezzo in base64
  (max 15MB; MIME normalizzato a image/heic se il sistema non lo
  dichiara — Pillow riconosce comunque i byte) e va SUBITO a
  `POST /api/foto/anteprima`: endpoint autenticato e STATELESS
  (niente disco né database prima della pubblicazione) che converte
  con Pillow e restituisce il JPEG — anteprima VERA appena scelta la
  foto, ed è lo stesso identico JPEG che poi si pubblica, già
  leggero. Se il server non può (Pillow assente, rete giù), resta
  l'originale col segnaposto 📷 «verrà convertita» e ci pensa
  `salva_foto` alla pubblicazione, con Pillow+pillow-heif, dentro
  `asyncio.to_thread` e fuori dalla transazione SQLite: secondi di
  CPU che non devono congelare il server mono-processo. La strada
  libheif-WASM in pagina è stata valutata e scartata: ~1MB di blob
  inauditabile nel repo per un caso raro, contro 25 righe che
  riusano `converti_in_jpeg`. Import
  fail-open: senza `pillow` tutto come prima (JPEG passano, limite
  2.5MB), senza `pillow-heif` le HEIC si saltano con una riga in
  console. Con Pillow anche i PNG/WebP grezzi diventano JPEG veri.
  Badge Nostr: colonna `utenti.npub` auto-dichiarata via `/api/me/npub`
  (formato bech32, rifiuta le nsec) + verifica con NOTA PUBBLICA:
  `/api/me/npub/verifica-avvia` genera un codice (vale 1h), l'utente lo
  pubblica in una nota kind-1 dal SUO client, `verifica-controlla`
  interroga 4 relay (websocket-client è sincrono: gira dentro
  `asyncio.to_thread`, relay in parallelo) → `utenti.npub_verificata`,
  badge 🟣. Dal lug 2026 il badge pubblico (card, dettaglio, negozio)
  esiste SOLO con la npub verificata, come 🟣 semplice senza ✓ (il
  non-verificato non compare in pubblico, quindi la spunta non
  distingue più nulla); la npub dichiarata ma non verificata la vede
  solo il proprietario nel suo Profilo, con l'invito a verificarla.
  Cambiare o rimuovere la npub azzera la verifica.
  Rimozione della npub (lug 2026): `salva_npub` con stringa vuota è
  l'unica strada; nel cassetto Identità c'è il bottone esplicito
  «🗑 Rimuovi la npub dal profilo» (confirm SEMPRE, con l'avviso in
  più se la chiave era anche npub_accesso; il campo svuotato + Salva
  delega lì). La rimozione toglie npub, verifica e — se coincideva —
  npub_accesso (solo tg_id>0, com'era già); il NATIVO Nostr (tg_id<0)
  con badge ≡ npub_accesso è BLOCCATO con 400 «è il tuo unico modo di
  entrare: collega prima Telegram» (guardia doppia frontend+server);
  se il badge del nativo è DIVERSO dalla chiave d'ingresso, la
  rimozione del badge è lecita e l'accesso resta. Dopo ogni
  cambio/rimozione che lascia l'utente senza destinazione Nostr (né
  accesso né badge verificato), `canale_notifiche` in
  ('nostr','entrambi') torna '' automatico — il cassetto Avvisi non
  deve mentire — e la risposta porta `canale_azzerato` (il 'telegram'
  esplicito non si tocca). Reinserire una npub, anche la stessa,
  riparte SEMPRE da non verificata. Le due leve del cassetto hanno il
  sottotesto che le distingue: «Disabilita l'accesso» chiude solo la
  porta del login (npub, badge 🟣 e ponte restano), «Rimuovi la npub»
  toglie tutto da ovunque; NIENTE terzo bottone «Scollega tutto» —
  Rimuovi fa già entrambe quando l'accesso è attivo, un doppione
  rimetterebbe la confusione che i sottotesti tolgono.
  `venditore_npub` e `venditore_npub_verificata` sono in `CAMPI_VETRINA`
  (pubblici per natura) e nelle SELECT di `/api/search` e
  `/api/listings/miei`.
  Avatar dal social di provenienza (lug 2026): colonne `utenti.avatar`
  (nome file, '' = iniziale), `avatar_aggiornato` e `avatar_scelta`
  ('' = automatico, la catena; oppure telegram | nostr | nessuna —
  la levetta binaria `avatar_visibile` è vissuta solo nei DB di
  collaudo, migrata e lasciata inerte). MAI link agli originali (gli URL del Bot API
  portano il TOKEN e scadono in un'ora; quelli Nostr regalerebbero
  l'IP di ogni visitatore a host terzi): si scarica la NOSTRA copia —
  francobollo 128px q85 (`_salva_avatar`, seconda generazione ammessa
  dal patto della filiera come le `_min`) in foto/ come
  `av_{negozio}_{ts}.jpg` (chiave = codice negozio pubblico, MAI il
  tg_id; nome versionato → la cache 1g di /foto lavora gratis, il
  file vecchio si spazza in `_scrivi_avatar`). `aggiorna_avatar`
  rispetta `avatar_scelta`: con '' vale la catena dei doppi cittadini
  — prima la foto Telegram (getUserProfilePhotos→getFile; chi la
  nasconde ai non-contatti resta con l'iniziale, ed è il suo modo di
  dire no), poi la picture del kind-0 dai 4 relay ma SOLO da chiave
  dal possesso dimostrato (npub_accesso o badge verificato: la regola
  di `notifica()`), scaricata con `url_foto_ammesso` + tetto 8MB —
  con telegram/nostr espliciti SOLO quella gamba senza ripiego (la
  scelta si rispetta: social senza foto = iniziale), con 'nessuna'
  non si scarica proprio; senza nulla la colonna si svuota e torna
  l'iniziale (foto sparita dal social = sparita anche da noi;
  imperfezione dichiarata: anche l'errore transitorio di rete svuota,
  ripara il rinfresco successivo). Rinfresco opportunistico in
  `/api/me` (diventato async per questo): al più ogni `GIORNI_AVATAR`
  (7), mai con 'nessuna', in create_task fail-open con anti-valanga
  `_AVATAR_IN_CORSO`; in collaudo la gamba Telegram esce None da
  bot_api simulato, quella Nostr legge i relay veri. Selettore «La
  tua foto» nel cassetto Identità (`POST /api/me/avatar-scelta`,
  pattern canale-notifiche: si accetta solo una sorgente che esiste,
  e ogni cambio ≠ nessuna rifà subito il francobollo): pillole solo
  per le sorgenti vere (mono-canale = la sua + «Nessuna», il
  selettore pieno è dei doppi cittadini), attiva = sorgente EFFETTIVA
  con «(automatico)» quando la scelta è vuota — l'automatico si
  mostra come Telegram anche quando la catena è ripiegata su Nostr,
  semplificazione dichiarata. «Nessuna» = iniziale ovunque per il
  pubblico, reversibile: `venditore_avatar` in
  CAMPI_VETRINA/CAMPI_MIEI/search e `avatar` nel profilo di
  /api/negozio escono col CASE su 'nessuna' (il nome file non lascia
  il server, il file resta in dispensa) — mentre tappo e testata del
  Profilo mostrano sempre la PROPRIA foto (vista privata, `avatar`
  da /api/me). Frontend: `avatarImg()` (filtro-alfabeto sul nome file)
  posa l'<img> sopra l'iniziale nei cerchi `.avatar` di dettaglio,
  negozio e Profilo (onerror la toglie: mai un'immagine rotta);
  `renderAvatar()` mette la faccia nel tappo (`.con-foto` spegne
  l'iniziale, onerror ripiega sul tappo di sempre e poi
  sull'iniziale). Ordini e card della griglia SENZA avatar (deciso);
  in DEMO iniziali e basta.
  Presenza Nostr della piattaforma: `NOSTR_NSEC_PIATTAFORMA` in config
  (segnaposto = funzione spenta, fail-open). Alla pubblicazione il
  server firma un evento NIP-99 (kind 30402, tag `d` stabile
  `barattolo-{id}`) con coincurve (Schnorr BIP-340) e lo manda ai 4
  relay (stesso pattern sync→`asyncio.to_thread` della verifica);
  venduto (ordine locked) → ripubblica `status sold`, rimborso →
  di nuovo `active`, rimosso → deletion NIP-09 (kind 5). La colonna
  `annunci.nostr_event_id` traccia l'ultimo evento; i ganci di
  aggiornamento agiscono solo se è valorizzata, così gli annunci
  importati (contatto_nostr pieno) restano fuori. Tutto in
  `asyncio.create_task`: mai errori né attese per l'utente. In
  collaudo gli eventi si firmano ma si stampano soltanto
  (`🟣 [nostr simulato]`).
  Post automatici (lug 2026): la piattaforma racconta i fatti — ogni
  nuovo annuncio in vetrina esce da solo come nota Nostr kind-1
  (chiave piattaforma, tag `t=barattolo`, foto come URL nel content)
  e post nel canale Telegram (`TELEGRAM_CANALE_ID` in config, il bot
  deve esserne ADMIN; vuoto = solo Nostr). Leve in config:
  `POST_AUTOMATICI` (default TRUE, deciso: canali giovani, collaudo
  in produzione) e `POST_MAX_ORA` (6). Anti-spam: `accoda_promo` +
  drenatore a finestra (`_drena_promo`: 90s, 5s in collaudo) — fino a
  3 annunci con budget orario capiente = post singoli (pausa 2s),
  altrimenti UN solo aggregato «📦 N nuovi annunci» (la valvola:
  passa sempre, non nomina nessuno, niente ciclo di vita). Il
  drenatore RILEGGE dal DB: rimossi/venduti in finestra e importati
  (`contatto_nostr` pieno) non escono mai; l'import CSV accoda tutto
  INSIEME a fine creazione = sempre un aggregato solo. NON si
  annunciano: ordini e vendite (privacy delle parti), annunci
  importati (l'originale è già sui relay), modifiche. Ciclo di vita
  dei post singoli (colonne `annunci.post_canale_id`/`post_nostr_id`):
  venduto = edit del post Telegram col «✅ Venduto» (caption
  RICOSTRUITA da `_caption_canale`, mai salvata; al rimborso il ✅
  sparisce — il post non deve mentire), la nota Nostr resta (è storia
  vera); rimosso = deleteMessage + NIP-09 kind-5 sulla nota e colonne
  azzerate. Il ciclo di vita ignora la leva: agisce solo su post già
  fatti. `bot_api` ora RESTITUISCE il JSON della risposta (serve il
  message_id; in collaudo un finto id negativo da contatore, così
  anche edit e delete si collaudano). Fail-open totale, ganci DOPO i
  commit, coda in memoria (un riavvio la perde, accettato).
  Negozio del venditore: colonna `utenti.negozio` = codice pubblico
  casuale di 8 caratteri (migrazione per chi c'era, `verifica_utente`
  per i nuovi; stabile per sempre, NON deriva dal tg_id).
  `GET /api/negozio/{chi}` risolve `chi` prima come username Telegram
  (case-insensitive), poi come codice → `{venditore, annunci attivi}`,
  auth facoltativa stile vetrina (`venditore_id` solo agli autenticati,
  il tg_id non esce mai). `venditore_negozio` è in `CAMPI_VETRINA` e
  nelle SELECT di `/api/search` e `/api/listings/miei`. La route
  `GET /negozio/{chi}` serve la solita miniapp.html (no-cache): è il
  link condivisibile barattolo.store/negozio/{username|codice}.
  Login web dal browser: `POST /api/login/telegram` riceve i dati
  firmati dal Login Widget ufficiale e apre una sessione — tabella
  `sessioni` (in DB SOLO l'hash SHA-256 del token), cookie
  `barattolo_sessione` HttpOnly + Secure (fuori collaudo) +
  SameSite=Lax, 30 giorni (`GIORNI_SESSIONE_WEB`), purga
  nell'orologio. ATTENZIONE, due derivazioni di chiave DIVERSE:
  widget = `SHA256(BOT_TOKEN)` (`verifica_login_widget`, auth_date
  entro 5 min), Mini App = `HMAC("WebAppData", BOT_TOKEN)`.
  `verifica_utente(init_data, sessione)` cade sul cookie SOLO a
  header vuoto (initData invalido resta 401); ogni endpoint dichiara
  `barattolo_sessione: str = Cookie("")` esplicitamente — niente
  middleware che concede auth. `guardia_csrf` (middleware) può solo
  NEGARE: sui metodi non-sicuri via cookie esige Origin ≡ Host
  (tutte le rotte `/api/login/*` incluse). `POST /api/logout` chiude
  solo la sessione del browser corrente. Il ramo collaudo di
  `/api/login/telegram` (`{"collaudo": true}`) vale solo con
  MODALITA_COLLAUDO.
  Login web con Nostr: `GET /api/login/nostr/sfida` emette una sfida
  monouso (dict in memoria, TTL 5 min: uvicorn è mono-processo);
  `POST /api/login/nostr` verifica un evento kind-22242 stile NIP-42
  con `verifica_evento_login` (sfida bruciata PRIMA della firma, tag
  `relay` ≡ Host, id ricalcolato NIP-01, Schnorr con `PublicKeyXOnly`
  di coincurve — 503 se il pacchetto manca) e apre la STESSA sessione
  cookie del login Telegram. Anagrafica: l'utente Nostr ha `tg_id`
  NEGATIVO derivato dalla pubkey (Telegram usa solo id positivi:
  tutto il resto funziona invariato; `notifica()` salta gli id
  negativi) e c'è la colonna `utenti.npub_accesso` = la chiave che
  può entrare in quella riga (credenziale, distinta dal badge `npub`
  che è una dichiarazione; indice unico parziale; è il terreno della
  futura doppia cittadinanza). Ordine di ricerca al login:
  npub_accesso → npub già VERIFICATA su UN solo account Telegram
  libero (proposta di collegamento con biglietto monouso,
  `POST /api/login/nostr/collega`; rifiuto = login annullato, mai
  doppioni) → account nativo nuovo (nome = npub abbreviata, badge
  🟣 da subito: la firma Schnorr dimostra il possesso). Un badge
  NON verificato non dà MAI accesso all'account che lo dichiara.
  `hex_to_npub` (bech32 con checksum vero) è il gemello speculare di
  `npub_to_hex`. `vendor/nostr.bundle.js` = nostr-tools 2.23.12
  committato a versione bloccata e servito da `GET /vendor/nostr.js`
  (file singolo, MAI CDN: nessun terzo deve poter cambiare la pagina
  dove si può incollare una nsec).
  Doppia cittadinanza (lug 2026): le due direzioni del collegamento.
  Telegram→Nostr: `POST /api/me/npub/abilita-accesso` promuove il
  badge VERIFICATO a `npub_accesso` (indice unico = giudice: 409 se
  la chiave apre già un altro account, e il messaggio indirizza alla
  fusione); `disabilita-accesso` è il contrario ma RIFIUTA i tg_id
  negativi (un nativo si chiuderebbe fuori); `salva_npub` che cambia
  o rimuove il badge azzera anche `npub_accesso` se coincideva (solo
  su tg_id>0, stessa ragione). Nostr→Telegram: il bot per la prima
  volta ASCOLTA — webhook `POST /api/telegram/aggiornamenti`
  (`TELEGRAM_WEBHOOK_SEGRETO` in config, segnaposto = spento;
  confronto `hmac.compare_digest` sull'header
  X-Telegram-Bot-Api-Secret-Token; si registra da solo all'avvio con
  setWebhook, MAI in collaudo: un test locale col token vero non deve
  rubare il campanello alla produzione). Flusso: dal web
  `POST /api/me/collega-telegram` (solo id negativi) emette un codice
  monouso TTL 5 min (`CODICI_FUSIONE` in memoria), il frontend apre
  t.me/ilbarattolobot?start=CODICE, il bot risponde con la CONFERMA a
  tastiera inline (token in `CONFERME_FUSIONE`, valido solo per quel
  from.id: il codice è un bearer token, se il link trapela serve
  comunque il tocco giusto), e `esegui_fusione` fonde l'account
  nativo in quello Telegram in UNA transazione `BEGIN IMMEDIATE`:
  annunci+ordini+sessioni+feedback migrano (il browser Nostr resta
  loggato), la riga negativa MUORE PRIMA che `npub_accesso` si accenda
  sulla positiva (indice unico), contatori sommati, rating ricalcolato
  dai feedback migrati. `_guardie_fusione` (ricontrollate DENTRO la
  transazione) rifiutano: P già collegato, P con badge verificato
  DIVERSO, affari ancora aperti tra i due (auto-ordine in escrow).
  `bot_api()` è il gemello completo di `notifica()` ma in collaudo
  simula SEMPRE (`🤖 [telegram simulato]`); il webhook in collaudo
  accetta il segreto fisso "collaudo" per suonarlo con curl.
  `gestisci_update` fa `upsert_utente` sul mittente (che può non
  aver mai aperto la Mini App) e risponde con garbo a /start nudo
  e ai messaggi qualsiasi.
  Notifiche multi-canale (lug 2026): `notifica()` legge
  `utenti.canale_notifiche` ('' = automatico: Telegram se tg_id>0,
  DM Nostr per i nativi; oppure telegram | nostr | entrambi, scelta
  via `POST /api/me/canale-notifiche` che accetta solo canali
  raggiungibili). Il DM è NIP-17 (scelto su NIP-04, deprecato e coi
  metadati in chiaro: nel 2026 Amethyst, Damus, Primal, 0xchat & co.
  parlano tutti NIP-17): rumor kind 14 NON firmato → sigillo kind 13
  firmato dalla piattaforma → pacco kind 1059 firmato da una chiave
  effimera nuova per messaggio, date arretrate a caso ≤2gg. Cifratura
  NIP-44 v2 in `nip44_cifra`: ECDH con la coordinata X NUDA via
  `ChiavePubblicaCompleta.multiply` (MAI `PrivateKey.ecdh()` di
  coincurve, che la hasherebbe), HKDF con hmac/hashlib, ChaCha20 dal
  pacchetto `cryptography` (import fail-open: senza, canale spento).
  La npub di DESTINAZIONE è solo dal possesso dimostrato:
  `npub_accesso`, o il badge `npub` se VERIFICATO — mai un badge
  nudo (i dettagli degli ordini di Tizio finirebbero nella inbox di
  Caio). Consegna ai relay del kind 10050 del destinatario (cache
  1h in memoria) con ripiego sui 4 standard; il ramo Nostr gira in
  `asyncio.create_task` (mai bloccare: notifica() vive anche
  nell'orologio) con ripiego Telegram se il DM non parte e la chat
  c'è. `spoglia_html` toglie i tag Telegram dal testo del DM. In
  collaudo il pacco si cifra davvero ma si stampa (`💌 [dm nostr
  simulato]`). Frontend: cassetto «🔔 Avvisi» nel Profilo
  (`renderAvvisi`); il sottotitolo dice SEMPRE il canale effettivo
  («Ricevi gli avvisi su: …», con «(automatico)» quando è il
  default), pillole di scelta solo se entrambi i canali sono
  disponibili, testo statico altrimenti; senza canali raggiungibili
  sparisce l'intero cassetto.
  Ponti di contatto tra le parti (lug 2026): NON una chat — bottoni
  verso i canali che esistono. Pagina del NEGOZIO e dettaglio ordine
  mostrano «✈️ Scrivi su Telegram» (t.me/username) e/o «🟣 Scrivi su
  Nostr» (profilo su njump.me: il DM parte dal client dell'utente)
  secondo l'identità della controparte; il doppio cittadino li ha
  entrambi, senza canali resta la riga onesta «le trattative non sono
  necessarie: l'escrow protegge» (solo nell'ordine). Dal DETTAGLIO
  ANNUNCIO i ponti sono USCITI con le rifiniture del riordino (lug
  2026): ci si arriva entrando nella scheda del venditore, e il
  riquadro nel dettaglio resta solo anagrafica. La npub del ponte è
  SOLO dal
  possesso dimostrato — npub_accesso o badge verificato, la regola di
  `notifica()`; per l'ordine `/api/orders` aggiunge
  `compratore_nostr`/`venditore_nostr` (CASE in SQL, escono solo alle
  parti e all'admin come il resto dell'ordine). Helper frontend
  `pontiContatto`/`pontiOrdine` (il vecchio `bottoneChat` non esiste
  più); username e npub negli onclick passano dal solito
  filtro-alfabeto.
  Avvisi di ricerca (lug 2026): «dimmi quando esce quello che cerco» —
  tabella `avvisi_ricerca` (max 5 per utente, `MAX_AVVISI_UTENTE`:
  categorie serializzate '|A|B|' coi pipe ai bordi per il LIKE,
  comune+raggio 10/25/50/100 km, prezzo max in sats O in eur mai
  entrambi, parole normalizzate al salvataggio, `attivo` per la
  pausa) + `avvisi_notificati` (dedup PERSISTENTE: lo stesso annuncio
  non suona mai due volte per lo stesso utente, nemmeno dopo un
  riavvio o una modifica; purga a 30gg nell'orologio,
  `pulisci_avvisi`). GEOGRAFIA: `dati/comuni.csv` committato (~7.900
  comuni ISTAT con lat/lon del centro, 258KB; fonte opendatasicilia,
  una tantum) letto in RAM da `carica_comuni()` — MAI Nominatim:
  zero rete nel percorso caldo di pubblica(), file assente =
  funzione geografica spenta e tutto il resto vive. Chiavi via
  `normalizza()`; i ~7 nomi contesi d'Italia (Castro, Peglio...)
  entrano solo come 'castro bg' (la chiave nuda ambigua si scarta);
  alias senza PREPOSIZIONI_COMUNI ('reggio emilia' ≡ «Reggio
  nell'Emilia», i nomi veri vincono sempre sugli alias); stoplist
  COMUNI_PAROLA (Paese, Vita, Sale, Calcio...) = matchano solo se la
  zona è ESATTAMENTE quel nome. `coordinate_da_zona` scandisce gli
  n-grammi del testo libero dal più lungo al più corto, a parità
  vince il primo nel testo («tra Pavia e Milano» → Pavia; «vicino
  Milano» → Milano, il raggio assorbe il vicino), secondo giro senza
  preposizioni («Cassano allo Ionio» trova «Cassano all'Ionio»).
  Colonne `annunci.lat/lon` ((0,0) = zona non riconosciuta: matcha
  solo i criteri non geografici, imperfezione dichiarata) scritte UNA
  volta in pubblica/modifica/modifica firmata/import CSV, ricalcolate
  per gli importati a ogni giro orario (le zone possono cambiare sui
  relay); `backfill_coordinate()` a ogni avvio (idempotente, solo
  righe a (0,0)); `distanza_km` = haversine. Il comune dell'UTENTE
  viene SEMPRE dal dataset (`GET /api/comuni` autocomplete + 400 sul
  nome sconosciuto: l'avviso ha sempre coordinate buone, il testo
  libero resta solo dal lato annunci).
  Città vere in Vendi (lug 2026): il campo Zona resta testo LIBERO ma
  suggerisce i comuni mentre si digita — datalist `zonaList` su
  /api/comuni (debounce 250ms, pattern avvisi) col valore nel formato
  «Comune (SIGLA)» («Carmagnola (TO)»: distingue gli omonimi, e
  normalizza('Pavia (PV)') = 'pavia pv' è una chiave GIÀ registrata
  da carica_comuni, riconosciuta senza codice nuovo; il valore si
  salva e si mostra così com'è). Al blur passa da
  `GET /api/zona-controlla` (autenticato): comune riconoscibile nel
  testo = silenzio; nulla di riconoscibile = riga `#zonaHint` col
  «forse Pavia (PV)?» quando il fuzzy ha un candidato, e la via
  d'uscita giusta secondo il caso ([Usa «Pavia (PV)»], oppure
  [lascia il campo vuoto] senza ritiro); il nome suggerito vive nella
  variabile `zonaSuggerita` e mai dentro l'onclick (gli apostrofi di
  Sant'Angelo). LA ZONA DEV'ESSERE UN LUOGO (lug 2026): il campo
  resta TESTO LIBERO, ma deve CONTENERE un comune riconosciuto —
  frazioni ok per costruzione («Frazione Salsasio, Carmagnola (TO)»
  passa: gli n-grammi trovano il comune), «Pvia» e «Spedisco in tutta
  Italia» no. Due severità: col RITIRO ('ritiro'/'entrambe') la zona
  è anche OBBLIGATORIA (chi viene a ritirare deve sapere dove);
  SENZA ritiro resta FACOLTATIVA — chi spedisce e basta la lascia
  vuota, e in card lo dice già il 🚚 — ma se la compila dev'essere
  vera. Fino al lug 2026 qui c'era solo un avviso MORBIDO col
  «Lascia così», e il campo Zona diventava un secondo posto dove
  scrivere la spedizione: è da lì che nascono le zone non-luogo che
  la vetrina deve poi nascondere. La regola vive in
  `guardia_zona_condizione` (giudice unico di pubblica e modifica;
  400 con `messaggio_zona_storta`, il messaggio UNICO che form,
  import e client dicono uguale; senza dataset si spegne, fail-open),
  nell'anteprima dell'import CSV (SCARTO con numero di riga e
  suggerimento, non più un avviso) e nel client (campo vuoto col
  ritiro fermato in publish(), che poi richiama `controllaZona()` e
  guarda `zonaStorta` — così l'errore arriva PRIMA del viaggio con le
  foto in base64; label dinamica «obbligatorio per il ritiro» da
  aggiornaConsegnaForm). CONSEGUENZA DICHIARATA: un annuncio storico
  con la zona storta viene fermato alla PRIMA MODIFICA finché non la
  sistema — lo stesso patto della condizione obbligatoria. Le
  migrazioni d'avvio invece non toccano nulla. Resta APERTA una sola
  porta, e non si può chiudere: l'import Nostr, che prende il tag
  `location` verbatim e lo riscrive DAI RELAY ogni ora — lì i relay
  sono la fonte di verità. Per questo il
  filtro giusto sta in VISUALIZZAZIONE, vedi «La zona si mostra solo
  se è un luogo» qui sotto. `suggerisci_comune` = difflib a
  soglia 0.8 sugli n-grammi (lunghi prima, primo nel testo a parità,
  come coordinate_da_zona), stoplist `PAROLE_ZONA` (senza, «spedisco»
  suggeriva Sedico BL — successo davvero), cache pigra `_comuni_fuzzy`
  («Nome (SIGLA)») solo sui nomi che coordinate_da_zona sa poi
  riconoscere (i contesi
  tipo Castro non si suggeriscono mai: sarebbe un vicolo cieco).
  Import CSV: righe col ritiro e zona vuota o irriconoscibile =
  SCARTO in anteprima («forse Pavia (PV)?»), senza ritiro resta
  l'AVVISO morbido. Dataset assente = tutto riconosciuto, la funzione
  si spegne in silenzio come il resto della geografia.
  La sigla in vetrina c'è SEMPRE (lug 2026): `arricchisci_zona`
  normalizza AL SALVATAGGIO (pubblica/modifica/import CSV) — se il
  testo contiene un comune riconosciuto senza ambiguità e la sigla
  manca, la aggiunge accanto al comune DENTRO il testo («Frazione
  Salsasio, Carmagnola» → «…, Carmagnola (TO)»), così il dato è pulito
  ovunque (vetrina, dettaglio, NIP-99, avvisi) senza rimedi in
  visualizzazione. MAI inventare: contesi nudi (Castro) e alias
  (Reggio Emilia) restano com'erano, chi ha la sigla non si tocca
  (idempotente), e il match che passerebbe solo dal secondo giro
  senza preposizioni («Cassano allo Ionio») non si arricchisce — lo
  span nel testo non sarebbe più suo, imperfezione dichiarata.
  Migrazione morbida `arricchisci_zone_esistenti` a ogni avvio
  (gemella del backfill coordinate, idempotente): solo i
  riconoscibili, MAI gli importati da Nostr (contatto_nostr pieno:
  la loro zona la riscrive l'import orario dai relay).
  Si mostra SOLO IL COMUNE riconosciuto (lug 2026), mai il testo
  intero, e se un comune non c'è non si mostra NIENTE. Vale in TUTTI
  i posti che il luogo lo mostrano: card, pillola del dettaglio,
  righe di «📋 I tuoi annunci» e «🫙 Nel tuo barattolo». Quindi
  «Frazione Salsasio, Carmagnola (TO) — spedisco ovunque» diventa
  «Carmagnola (TO)», «vicino Milano (MI)» diventa «Milano (MI)», e
  «Spedisco in tutta Italia» o «Nord Italia» non lasciano NULLA al
  loro posto — la strada di consegna la dicono già le icone accanto,
  e il vecchio ripiego `luogoMeta` «📦 Spedizione»/«💾 Online»/«📍 —»
  non esiste più. `luogoTesto` dice la regola, `luogoRiga` (riga
  discreta sotto il titolo del dettaglio — era `luogoPill`, la
  pillola è morta col riordino del dettaglio, vedi sotto) e
  `luogoPunto` (coda « · 📍 X» delle righe elenco,
  col separatore che sparisce insieme al luogo: mai un puntino
  orfano) la vestono — tre rese che non possono divergere, la stessa
  idea del cuore unico qui sotto. Il dato NON si perde: la zona resta
  intera nel database, il form di modifica la mostra per intero, e
  continua a servire per le coordinate e gli avvisi.
  IL TESTO INTERO NEL DETTAGLIO È DURATO UN GIORNO — e vale la pena
  dire perché non era tenibile, che è utile quanto la regola. La
  scelta di partenza era ragionevole: la card come INDICE (nomi
  confrontabili a colpo d'occhio) e la scheda come DICHIARAZIONE del
  venditore, col testo intero, per non perdere le frazioni —
  «Frazione Salsasio» serve a chi va a ritirare. Non regge, perché
  la frazione e la frase-spazzatura SONO LA STESSA COSA: testo
  libero attorno a un comune. Il «resto» di «Torino (TO) spedisco in
  tutta Italia» è esattamente ciò che si vuole nascondere, e non
  esiste modo di tenere l'uno senza l'altro. La via di mezzo —
  mostrare il testo intero solo con il RITIRO attivo, dove la
  frazione serve davvero — è stata valutata e scartata due volte:
  un annuncio col ritiro può avere lo stesso la frase-spazzatura
  nella zona, e una regola condizionale sulla modalità di consegna
  sarebbe impossibile da ricordare fra sei mesi. Chi ci tiene alla
  frazione la scrive in DESCRIZIONE, che nel dettaglio si legge
  tutta due righe più sotto e che il venditore controlla; e il punto
  d'incontro di un ritiro si concorda comunque tra le parti (ponti
  di contatto, poi il pannello dell'ordine): un indirizzo Barattolo
  non l'ha mai pubblicato. Dal compratore, in vetrina, la domanda è
  «è vicino a me?», non «in che via?».
  Il nome esce nella forma UFFICIALE del dataset, il che raddrizza
  gratis le maiuscole storte («torino (TO)» → «Torino (TO)») e dà la
  sigla anche agli alias che `arricchisci_zona` non sapeva servire
  («Reggio Emilia» → «Reggio nell'Emilia (RE)»).
  IL CUORE È UNO SOLO — `_chiave_comune` — e questo è il vincolo che
  ha guidato il disegno: `coordinate_da_zona` (le coordinate) e
  `comune_da_zona` (il nome per la vetrina) DEVONO dire la stessa
  cosa, o la card mostrerebbe un luogo per cui il filtro geografico
  degli avvisi non trova nulla, o viceversa. Un solo scanner a
  n-grammi, quindi, e le due funzioni ci si appoggiano entrambe;
  verificato sull'intero dataset (7.904 comuni × 3 forme, zero
  divergenze). `arricchisci_zona` invece NON passa di lì e tiene il
  suo giro: a lei serve la POSIZIONE del comune nel testo, che il
  secondo passaggio senza preposizioni perde. Il nome lo dà
  `_comuni_nome()`, gemello LARGO di `_comuni_fuzzy` (che tiene i
  soli nomi nudi perché lì sono i candidati del difflib): qui
  servono anche la chiave nome+sigla e gli alias, o il comune
  riconosciuto resterebbe senza un nome da mostrare.
  API: `CAMPI_VETRINA` espone `zona_comune` (il nome, '' = la zona
  non è un luogo) — che è ANCHE il flag «mostro il 📍?», quindi UN
  campo invece di due: il breve `zona_riconosciuta` (0/1 da
  `a.lat!=0 OR a.lon!=0`) è vissuto un giorno solo ed è stato
  assorbito da questo, che dice la stessa cosa e in più porta il
  nome. Si calcola in Python dentro `arricchisci_righe_vetrina` e
  non in SQL — il dizionario dei ~7.900 comuni vive in RAM, non nel
  database — ed è per riga una manciata di lookup su un dict: nulla,
  anche sulle 300 righe della shortlist AI.
  ATTENZIONE, e vale per ogni campo derivato che verrà dopo:
  `arricchisci_righe_vetrina` (si chiamava `espandi_distintivi_
  vetrina` finché faceva una cosa sola) è il COLLO DI BOTTIGLIA da
  cui passano tutte e sei le rotte che diventano card — vetrina,
  negozio, singolo, miei, ricerca AI, preferiti. È lì che si
  aggiungono i campi derivati, ed è per questo che `zona_comune` non
  ha bisogno di nessun ripiego lato client: le rotte che servono
  l'annuncio INTERO (`/api/search`, `/api/listings/miei`) passano da
  `a.*` e non avrebbero un alias SQL, ma passano di lì anche loro.
  In DEMO non c'è server che estragga il comune e l'approssimazione
  onesta è `comuneDemo` (il pezzo di testo che porta la sigla, che
  nel campo Zona è il formato suggerito).
  La REGIONE è DERIVATA (lug 2026): non è un campo del form e non si
  chiede MAI al venditore — si ricava dalla sigla che `arricchisci_zona`
  ha già messo nella zona. `regione_da_zona` prende la PRIMA sigla
  valida del testo (regola di coordinate_da_zona: «Roma (RM) o Milano
  (MI)» → Lazio; un «(kg)» non è una sigla e si ignora) contro la mappa
  fissa `REGIONI` (20 regioni → le 107 sigle, scritta per regione:
  `SIGLE_REGIONE` si deriva da lei, una sola fonte di verità —
  verificata contro dati/comuni.csv, zero buchi). Colonna
  `annunci.regione` ('' = sigla assente o sconosciuta: storici, alias
  tipo «Reggio Emilia», frazioni irriconoscibili — nessun blocco, il
  filtro non li vede, lo stesso patto di condizione e spedizione),
  scritta accanto a lat/lon in pubblica/modifica/modifica firmata/
  import CSV, ricalcolata per gli importati a ogni giro orario nel
  dopo-import (gemella delle coordinate) e data agli annunci di ieri
  da `deriva_regioni()` all'avvio — DOPO `arricchisci_zone_esistenti`,
  che l'ordine conta (prima la sigla nella zona, poi la regione);
  idempotente, tocca solo le righe ancora vuote. In CAMPI_VETRINA;
  param `regione` su /api/listings (sconosciuta = nessun filtro, mai un
  400) componibile con categoria, prezzo, condizione, spedizione e col
  cursore; `regioni` = {regione: quanti} nella busta di PRIMA pagina,
  conteggi GLOBALI come `conteggi` (non seguono categoria né ricerca) e
  senza le vuote. Frontend: foglio-picker `filtroRegSel` nel pannello
  Filtri, voci dal SERVER («Lombardia · 137», alfabetico, «Tutta
  l'Italia» prima) — la regione scelta resta in elenco anche a 0
  annunci (il campo non deve mentire), nessuna regione (server di ieri,
  vetrina vuota) = la riga sparisce del tutto, in DEMO si conta dai
  dati finti (`renderFiltroRegioni`); stato di sessione `filtroReg`
  come gli altri filtri. NON si mostra da nessuna parte in vetrina
  (deciso: la sigla nella zona la dice già a un lettore italiano, e la
  card resta pulita); se un giorno servisse, il posto è la fila di
  pillole del dettaglio. Due lezioni dal cantiere: `apriPicker` passa
  ora il valore in `data-val` invece che dentro la stringa JS
  dell'onclick — «Valle d'Aosta» spezzava l'apice, e il commento «i
  valori vengono dai cataloghi, l'onclick è sicuro» valeva finché nei
  cataloghi non c'erano apostrofi; e Applica/Azzera del pannello sono
  gemelli per `.filtri-riga .btn.ghost{margin-top:0}` (a pari
  specificità vinceva il `margin-top:10px` della ghost e in flex
  «stretch» stirava Applica di 10px) più la base flex al 50% (col
  basis 0 i 2px di bordo della ghost si sommano FUORI dalla base e la
  facevano larga 4px in più).
  «📍 VICINO A ME» È ESISTITO DUE GIORNI, ED È STATO TOLTO (lug 2026,
  decisione di Andrea) — la voce resta qui perché il motivo vale più
  della funzione, e perché è un'idea che torna in mente da sola.
  Era: comune di chi guarda (colonna `utenti.comune`) più un raggio,
  parametri `vicino`/`raggio_km` su /api/listings con l'haversine
  prestato a SQLite, foglio «Da dove cerchi?», e il comune riusato per
  precompilare la Zona di Vendi e gli avvisi di ricerca. Funzionava.
  È stato tolto perché IL FILTRO PER REGIONE COPRE GIÀ QUEL BISOGNO, e
  due strade per la stessa cosa non sono il doppio delle possibilità:
  sono un bivio davanti a chi cerca, che deve capire in che cosa
  differiscono prima di scegliere — e per un compratore italiano
  «Lombardia» e «entro 50 km da Milano» rispondono alla stessa
  domanda. Non era un problema di codice: era una voce di troppo nel
  pannello. Chi volesse riprovarci si chieda prima cosa TOGLIE, non
  cosa aggiunge.
  Restano in piedi, e sono roba d'altri cantieri: `distanza_km` e
  `RAGGI_AMMESSI` (li usano gli avvisi di ricerca), `comune_da_zona`
  e tutto il motore geografico, `GET /api/comuni` — che era stata
  aperta al pubblico per la vetrina anonima ed è tornata AUTENTICATA
  con la rimozione: non perché aprirla facesse danno (è l'elenco ISTAT
  committato in chiaro) ma perché una superficie pubblica senza più un
  motivo è solo superficie.
  COLONNA `utenti.comune`: INERTE. Nessuno la scrive, nessuno la
  legge; è rimasta per non fare una migrazione distruttiva su chi
  l'aveva valorizzata in quei due giorni, come `avatar_visibile` prima
  di lei. Non è un dato su cui contare: se un domani servisse davvero
  un comune dell'utente, va ripensato da capo.
  E LA ZONA DI VENDI NON SI PRECOMPILA (stessa decisione): il campo
  nasce vuoto e lo scrive l'utente con l'autocomplete. Con l'avviso
  «Ho scritto Milano (MI)…» se n'è andata anche `avvisoComune`, e con
  lei la proposta ricavata dagli ultimi annunci (`comune_suggerito` in
  /api/me). Il posto dove si dice da dove si vende è uno solo, ed è
  quel campo lì. MOTORE: gemello della coda
  promo — `accoda_match` in pubblica() accanto ad accoda_promo, nel
  loop finale dell'import CSV (accodati insieme = UN aggregato) e nel
  dopo-import Nostr (`creato>=t0`: gli importati CONTANO, «un
  annuncio è un annuncio»; importa_nostr.py resta intonso);
  `_drena_match` dorme ATTESA_RAGGRUPPO, rilegge dal DB (spariti nel
  frattempo = muti), prefiltro SQL sugli avvisi attivi (`tg_id !=
  venditore`: mai avvisato del proprio annuncio; categoria e prezzo
  sats in SQL) + verifica fine in Python: parole TUTTE in AND a
  prefisso di parola ('bici' prende 'bicicletta', 'ram' non affoga in
  'ceramica'), prezzo EUR col cambio corrente (cambio mai arrivato =
  l'avviso EUR NON scatta: meglio un match perso che uno sbagliato),
  haversine ≤ raggio. ANTI-MOLESTIA a tre strati: 1) dedup DB sopra;
  2) aggregazione per finestra — match singolo = messaggio ricco
  (titolo, prezzo via `_prezzo_promo`, 📍 zona, link /annuncio/{id}),
  2+ = UN solo «📬 N nuovi annunci corrispondono ai tuoi avvisi»;
  3) `TETTO_AVVISI_GIORNO` (5 in prod, 3 in collaudo) MESSAGGI al
  giorno per utente in `AVVISI_QUOTA` (memoria, pattern IMPORT_QUOTA:
  un riavvio azzera il conteggio, accettato — le raffiche vere le
  ferma l'aggregazione, che è strutturale); l'ultimo messaggio del
  giorno chiude con «per oggi mi fermo qui 🤫», onestà e non silenzio.
  Uscita SEMPRE via `notifica()`: multi-canale e DM NIP-17 gratis,
  nativi Nostr inclusi; 0.2s tra un utente e l'altro, fail-open
  totale (un errore nel matching non tocca mai la pubblicazione).
  `esegui_fusione` migra avvisi e dedup (UPDATE OR IGNORE).
  Endpoint (pattern canale-notifiche): GET/POST /api/me/avvisi-ricerca
  (POST con `id` = modifica del proprietario; ALMENO un criterio, un
  avviso vuoto sarebbe tutta la vetrina in chat; 400 oltre il tetto
  di 5), POST .../{id}/pausa e .../{id}/elimina, GET /api/comuni
  (autenticato, primi 10 per prefisso). Frontend: cassetto «🔎 Avvisi
  di ricerca» nel Profilo (`renderRicerche`, sparisce in
  DEMO/VETRINA; pillole categoria toggle senza re-render — il
  re-render pieno perderebbe i campi digitati —, comune con
  `<datalist>` e debounce 250ms su /api/comuni, select raggio, prezzo
  col toggle sats/€, riepiloghi sotto `esc()`, ✏️ precompila il form,
  conteggio «(N di 5)» nell'header) e CTA «🔔 Avvisami se arriva» in
  #gridEmpty dopo una ricerca a vuoto (mai in DEMO/VETRINA;
  passamano `ricercaPrecompila` con query e categoria attiva,
  consumato da renderRicerche, pattern hintPubblicazione).
  Feedback e stelle (lug 2026): tabella `feedback(ordine_id, da_tg_id,
  per_tg_id, voto 1-5, commento ≤200, creato)` con
  `UNIQUE(ordine_id, da_tg_id)` come giudice dei doppioni.
  `POST /api/orders/{id}/feedback`: solo le due parti, solo su
  `STATI_FEEDBACK = (released, refunded)` — anche gli affari finiti
  male sono affari veri, escluderli gonfierebbe i profili —
  definitivo (niente modifica: chiude il ricatto «cambia il
  feedback o…»; la valvola è `POST /api/admin/feedback/{id}/rimuovi`).
  Commento sotto `controlla_vietato` (niente AI: 200 caratteri legati
  a una transazione pagata). `utenti.rating` e `n_feedback` si
  aggiornano SEMPRE per RICALCOLO (`_ricalcola_rating`: AVG/COUNT
  dalla tabella, `round(…,1)`, dentro `BEGIN IMMEDIATE`): così
  rimozione admin e fusione si sistemano da sole. `esegui_fusione`
  migra i feedback (prima però cancella quelli sugli auto-scambi tra
  le due metà: eviterebbero la UNIQUE e sarebbero auto-voti) e
  ricalcola. `/api/orders` espone `mio_voto/mio_commento` e
  `suo_voto/suo_commento`; `/api/negozio/{chi}` aggiunge
  `n_feedback` al profilo e `feedback` = ultimi 10 ricevuti (voto,
  commento, data, ruolo «acquirente/venditore» — MAI nomi: su una
  pagina pubblica rivelerebbero gli acquisti altrui; `f.id` è opaco
  e serve al bottone rimuovi dell'admin). Invito ⭐ in coda alle
  notifiche di chiusura (sblocco manuale/automatico e rimborso).
  Frontend: `feedbackPanel(o)` nel dettaglio ordine (5 stelle
  cliccabili + textarea, `confirm` prima dell'invio, gira in
  «Feedback lasciato» + eventuale «ricevuto»), lista nel negozio
  (`#negozioFeedback`), conteggio `(N)` accanto alle stelle in
  negozio e profilo, commenti sempre sotto `esc()`.
  Distintivi 🏅 (lug 2026, gamification parte 2): catalogo `DISTINTIVI`
  nel codice (11 badge: id, emoji, nome, descrizione, `fiducia`,
  criterio-lambda) + tabella `badge_utente(tg_id, badge_id,
  ottenuto_il, PK(tg_id,badge_id))`. Append-only: non si revocano mai.
  `controlla_distintivi(con, tg_id)` è il giudice unico: RICALCOLA i
  criteri dai dati veri (stile `_ricalcola_rating`) e assegna con
  INSERT OR IGNORE; `premia_distintivi(tg_id)` (connessione propria,
  fail-open, notifica «🏅» DOPO il commit) è il gancio dal vivo in:
  `_sblocca_sats` (entrambe le parti), `verifica_npub_controlla`,
  `abilita_accesso_nostr`, `login_nostr` (nativo nuovo),
  `login_nostr_collega`, `pubblica`, `lascia_feedback` (entrambe).
  Passata retroattiva SILENZIOSA su tutti gli utenti a ogni avvio in
  `init_db` + catch-all silenzioso in `/api/me` (scrittura su GET ma
  idempotente: è ciò che rende il sistema auto-riparante). I criteri
  pesanti contano solo ordini `released` (sats veri dall'escrow:
  gonfiarli costa la commissione); `ordini.disputata` (nuova colonna,
  settata in `apri_disputa`, backfill sugli stati post-disputa) fa da
  memoria per Specchiato («10 affari senza dispute perse»: venditore
  perde se refunded+disputata, compratore se released+disputata).
  Fulmine usa `spedito_il-creato ≤ 24h+30min` (il reaper dei 30 min è
  il tetto fisico del pagamento: niente colonna `pagato_il`).
  Pioniere = posizione ≤100 per `(registrato ASC, tg_id)`, gli 0
  pre-migrazione contano come i più vecchi. `esegui_fusione` migra i
  badge in unione (UPDATE OR IGNORE + DELETE) e rivaluta. API:
  `/api/me.distintivi` = catalogo COMPLETO con `ottenuto` (ts o null,
  il frontend non hardcoda mai la lista); `/api/negozio` →
  `venditore.distintivi` e `venditore_distintivi` sugli annunci
  (subselect GROUP_CONCAT in `CAMPI_VETRINA` + SELECT di search e
  miei, espanso in {id, emoji, nome, descrizione} da
  `arricchisci_righe_vetrina`) = dal lug 2026 TUTTI i guadagnati
  (bacheca stile Vinted, deciso con Andrea: ⚡ Primo acquisto
  pubblico compreso — aggregati senza segreti); il flag `fiducia`
  non filtra più, decide solo la PRECEDENZA (i fiducia in testa al
  catalogo → in testa alla sfilza: il «+N» taglia i badge di
  percorso, mai quelli di affidabilità). Frontend:
  griglia `renderDistintivi()` nel cassetto «🏅 Distintivi» del
  Profilo (il conteggio «(N di M)» vive nell'header del cassetto,
  `#distintiviConta`; classe `.distintivo` — `.badge` è degli stati
  ordine — mancanti in grigio con la descrizione come molla), e in
  pubblico la SFILZA `sfilzaDistintivi(lista, max, tocca)`: emoji
  nude `.sfilza .medaglia` a 14.5px — la taglia del nome accanto,
  provata anche piu' grossa (19px) e tornata indietro — con un
  piccolo gap (niente
  cerchietti d'oro: nude e sovrapposte si impasterebbero — l'oro
  resta alle tessere del foglietto; `nostrano`
  sempre fuori: il 🟣 accanto al nome c'è già) — nel dettaglio
  annuncio prime 4 + «+N» dentro la card venditore che resta tutta
  cliccabile (nessun tocco sulla sfilza: un bersaglio solo), in
  testata negozio COMPLETA (flex-wrap, mai «+N»: è la bacheca) e
  toccabile → foglietto `#distintiviSheet` (pattern sheet, registrato
  in `closeSheet`, dati da `negozioCorrente`) con le tessere
  `.distintivo` di TUTTI i guadagnati, nome e descrizione — qui
  `nostrano` c'è, ed è il posto che spiega il pallino viola; i
  mancanti mai in pubblico. Cassetto nascosto in DEMO come il wallet.
  Export dati contabili (lug 2026): colonna `ordini.cambio_eur` = EUR
  per BTC al momento della chiusura, scritta da `_sblocca_sats` e
  `_rimborsa_compratore` via `cambio_btc_eur()` (CoinGecko lato server
  — il ≈€ della vetrina resta lato client — cache 15 min, fail-open:
  0 = sconosciuto, e gli ordini storici restano onestamente vuoti nel
  CSV). `POST /api/me/export-biglietto` (autenticato) emette un
  biglietto TTL 5 min (`BIGLIETTI_EXPORT` in memoria, stile
  SFIDE_LOGIN: dentro Telegram il download non può portare l'header
  di auth); `GET /api/export/{biglietto}` (anche HEAD: la sonda di
  Telegram prima del popup) serve il CSV
  degli affari released/refunded dell'utente, da entrambe le parti.
  ATTENZIONE: il biglietto NON è monouso — il downloader di Telegram
  fa più richieste sullo stesso link (HEAD di sonda + GET, a volte a
  range) e bruciarlo alla prima gli farebbe scaricare un 410 (bug
  vero, successo su Android): vale i suoi 5 minuti, poi la purga
  (data, ruolo, annuncio, sats, esito, controvalore_eur) —
  separatore `;`, decimali con virgola e BOM UTF-8 per l'Excel
  italiano, quoting del titolo via csv.writer. Frontend: bottone
  «📄 Esporta i tuoi dati» in fondo a «⚡ Wallet e incassi» nel
  Profilo (`esportaDati()`: `tg.downloadFile` SOLO con initData vero
  e `isVersionAtLeast('8.0')` — nel browser lo stub di Telegram
  esiste comunque e mentirebbe — con ripiego `tg.openLink` se lancia;
  altrimenti `<a download>`; in DEMO sparisce col blocco wallet).
  Import in blocco da CSV (lug 2026): cassetto «📥 Importa in blocco»
  nel Profilo (in DEMO sparisce, il patto del wallet), per i
  commercianti coi cataloghi grandi. Due fasi col pattern biglietto:
  `POST /api/import/zip` (le foto in uno ZIP come CORPO BINARIO puro
  letto a chunk col tetto 50MB applicato DURANTE la lettura; controlli
  sulle sole intestazioni — ≤2000 voci, somma ≤200MB, ≤15MB/voce,
  niente path storti — e MAI extract: si legge per nome con zf.read)
  → `POST /api/import/prepara` (CSV come testo in JSON, ≤2MB, header
  per NOME quindi colonne riordinabili, ≤500 righe; ogni riga:
  `neutralizza_formula` anti CSV-injection su titolo/descrizione/zona
  — strappa =, +, @ iniziali, il `-` resta —, prezzo dal giudice
  unico `prezzo_da_payload` (stessi 400/503 di pubblica, EUR con
  virgola tradotta), `categoria_tollerante` coi `SINONIMI_CATEGORIA`
  e ripiego Altro, foto via URL (`url_foto_ammesso` = anti-SSRF: gli
  URL li scrive l'utente, host risolto e IP privati rifiutati) o nomi
  nello ZIP (match case-insensitive sul basename), filtro parole su
  TUTTE le righe; anteprima {biglietto, valide, scarti, avvisi}
  numerata come nel file — intestazione = riga 1 — TTL 15 min) →
  `POST /api/import/avvia` (quota 1000 righe/giorno per utente e UN
  solo job in corso in TUTTO il server, 409 onesto: mono-processo su
  VPS piccolo) → `GET /api/import/stato/{biglietto}` (polling 2s del
  frontend). Il job `_lavoro_import`, tre fasi: moderazione AI
  COMPLETA ma a LOTTI (`moderazione_ai_lotto`: ~20 annunci per
  chiamata Haiku, semaforo a 3, verdetto per riga `<n>: OK|VIETATO:
  motivo` con parsing robusto — righe storte o numeri allucinati =
  fail-open per voce, errore = fail-open per lotto, ~0,13$ e ~1 min
  per 500 righe); creazione a gruppetti di 4 con COMMIT PER RIGA (un
  crash a metà lascia solo annunci COMPLETI; lo stato è in memoria
  come SFIDE_LOGIN: dopo un riavvio il polling prende 404 e il
  frontend dice la verità); foto nei thread con la filiera buona
  (`normalizza_foto_import`: JPEG già dritto e ≤1600px VERBATIM,
  tutto il resto UNA sola `converti_in_jpeg` — il patto della
  compressione unica vale anche qui; `scarica_foto_import` timeout
  10s tetto 8MB, foto morta = avviso, mai un annuncio perso); Nostr
  in coda a lotti di 5 eventi con pausa 1,5s (checkbox nel form,
  default acceso) quando gli annunci sono GIÀ in vetrina. DEROGA
  dichiarata allo strato 3 della moderazione: UNA notifica admin
  riassuntiva (intervallo id creati + titoli bocciati dall'AI, max
  10) invece di una per annuncio. `GET /api/import/modello` = CSV
  modello scaricabile (pubblico: BOM, `;`, tre righe demo).
  `pulisci_import` nell'orologio: lavori scaduti coi loro ZIP, file
  orfani >1h in `import_tmp/` (in .gitignore), quote dei giorni
  passati. `_salva_una_foto` è il nucleo di scrittura (pieno + `_min`)
  estratto da `salva_foto` e riusato dall'import.
  Spedizione e protezione acquisti (lug 2026, modello Vinted): a
  carico del COMPRATORE, il venditore incassa netto articolo +
  spedizione. Sull'annuncio: colonne `consegna` ('' = non specificata,
  cioè annunci storici e importati col flusso di sempre | spedizione |
  ritiro | entrambe — catalogo `MODALITA_CONSEGNA`),
  `spedizione_sats`/`spedizione_eur` (0 con modalità che spedisce =
  gratis). TRE semantiche del costo, decise dal venditore (lug 2026,
  l'ancora all'euro ha SUPERATO la conversione alla pubblicazione):
  1) listino sats + costo in sats = FISSO, qualunque cosa faccia il
  cambio; 2) listino sats + costo scritto in EURO (toggle `spedValuta`
  sul campo, che decide la SEMANTICA e non la comodità: l'hint lo
  dice) = ANCORATO — si salva spedizione_eur così com'è (sped_sats
  resta 0, niente cambio alla pubblicazione) e diventa sats SOLO in
  compra() col cambio corrente, registrato in `cambio_ordine`: i
  «5 €» del venditore valgono sempre 5 €; senza cambio all'acquisto
  503 onesto SOLO per la scelta spedizione, il ritiro resta sempre
  acquistabile e l'articolo sats non dipende mai dal cambio; i sats
  espliciti battono l'ancora; 3) listino EUR = tutto ancorato per
  natura, articolo e spedizione convertiti INSIEME all'acquisto.
  Nei conti il controvalore sats dell'ancorato è una STIMA
  live («≈», `satsSpedizione` keyed su spedEur>0; prefisso ≈ dei
  bottoni via `stimaCirca`) — dal lug 2026 il costo di spedizione da
  solo non si mostra più da nessuna parte, e con lui se n'è andato
  `spedTesto`: la spedizione entra nei totali e nel conto scomposto,
  sempre in sats; il valore vero si fissa alla creazione
  dell'ordine. Nel NIP-99 spedizione_eur piena parla euro. Gli annunci
  del breve periodo «convertito alla pubblicazione» hanno
  spedizione_eur=0 e restano fissi (caso 1). E `taglia_pacco`
  (`TAGLIE_PACCO` busta/piccolo/medio/grande/ingombrante, con gli
  esempi concreti nel form: servirà alle etichette corriere future; il
  gemello client è il catalogo `TAGLIE` — nome, esempio e `lato` del
  disegno — vedi la scala disegnata qui sotto);
  giudice unico `consegna_da_payload` (sconosciuto → '', mai 400 —
  in pubblica() si chiama PRIMA dello scudo anti-doppione: può
  attendere il cambio, e tra controllo e INSERT niente await).
  Sull'ordine: `ordini.prezzo_sats` RESTA il TOTALE in cassaforte
  (invoice, rimborso integrale e CSV non cambiano semantica); le
  quote `ordini.spedizione_sats`/`protezione_sats` si FISSANO alla
  creazione (il config può cambiare, l'ordine no) e l'articolo si
  deriva per sottrazione; `consegna_scelta` = spedizione|ritiro|''.
  compra(): body `consegna` validato contro la modalità (incompatibile
  = 400; annuncio '' la ignora; 'entrambe' senza scelta = spedizione,
  il client vecchio vede comunque i sats veri della risposta); EUR
  converte articolo+spedizione INSIEME al cambio corrente (un annuncio
  tutto-sats non dipende mai dal cambio); protezione =
  `PROTEZIONE_PERCENTO` (config, 0 = spenta) sul SOLO articolo, per
  difetto (floor), anche sul ritiro; drift/tetto sul solo articolo;
  risposta con `articolo_sats/spedizione_sats/protezione_sats/
  consegna` in più. Chiusure: incasso venditore =
  `netto_venditore(prezzo_sats - protezione_sats)` in _sblocca_sats e
  deposita_invoice (COMMISSIONE_PERCENTO resta leva DISTINTA e
  sottrattiva: compongono senza doppio conteggio); rimborso = totale
  (la protezione torna al compratore). Ritiro in zona SENZA stati
  nuovi: corriere-sentinella 'Ritiro in zona' (gemello di 'Consegna a
  mano', esente tracking, notifica sua) su segna_spedito;
  l'auto-sblocco a 10gg resta ancorato a spedito_il = momento della
  consegna a mano. Vetrina: i 4 campi in CAMPI_VETRINA; param
  `solo_spedizione` su /api/listings (gli storici '' restano fuori:
  il filtro promette un costo dichiarato) — e dal lug 2026 i suoi due
  gemelli `solo_ritiro` (consegna IN ritiro/entrambe) e
  `solo_digitale`, che è l'unico a guardare il SET delle strade
  (`consegna='digitale' OR anche_digitale=1`: la combo va presa, ed è
  la regola di `stradeConsegna()` nel client, dove la DEMO chiede
  proprio a lui invece di ripetere la condizione a mano). Tre spunte
  che si SOMMANO: spedizione+ritiro = solo chi offre tutte e due.
  Le etichette non dicono «Solo con…» (lug 2026): «🚚 Spedizione ·
  🤝 Ritiro in zona · 💾 Codice online · ⚡ In offerta» — sono spunte
  dentro un pannello che si chiama Filtri, il «solo» lo dice il posto;
  `protezione_percento`
  nella busta di prima pagina (la stima del client non hardcoda mai
  la cifra). NIP-99: la spedizione è una riga del CONTENT, nessun tag
  nuovo. Import CSV: colonne facoltative `consegna;spedizione;taglia`
  nel modello e nel parser. La modifica FIRMATA degli importati non
  offre i campi (v1: l'evento non li porta, il form li nasconde).
  Frontend: form Vendi con le TRE CASELLE indipendenti (lug 2026,
  decisione di Andrea, via il select + checkbox: 🚚 Spedizione ·
  🤝 Ritiro in zona · 💾 Invio del codice online, spunta tutte quelle
  che offri, ALMENO una — la validazione vive in publish(), il server
  resta tollerante con '' per i client vecchi; `consegnaForm()` mappa
  le spunte sulle strutture di sempre consegna+anche_digitale, che
  reggono tutte le 7 combinazioni senza colonne nuove, e
  `impostaConsegnaForm()` è il verso opposto per precompilazione e
  reset; costo e taglia compaiono solo con Spedizione spuntata;
  l'hint «una sola strada» con ≥2 spunte è vissuto un giorno e tolto
  come rumore — l'hint del codice online invece è OPERATIVO, dice al
  venditore cosa dovrà fare («lo consegnerai dentro Barattolo dopo il
  pagamento: niente chat private»); allineamento caselle: servono i
  selettori SPECIFICI `.field label.cons-riga`/`.field .cons-riga
  input`, le regole generiche di .field (maiuscoletto, padding da
  campo) vincerebbero sulla classe nuda; LE ICONE sono 20px contro i
  13,5 del testo (`.cons-ico`, `display:inline-block` e
  `line-height:1` o un'emoji da 20 dentro una riga da 13,5 raddoppia
  la casella; la spunta resta 17px, è un controllo e non un disegno):
  lì si sceglie COME arriva la roba, e le tre strade si distinguono
  dal disegno, non dalla riga di testo. La spedizione parla col 🚚 e
  non col 📦 (lug 2026): il camioncino è la spedizione in TUTTA l'app
  — icone della card, badge del dettaglio, spunta dei filtri — mentre
  il 📦 nel progetto è il pacco della TAGLIA, roba del corriere;
  erano due disegni per la stessa strada, e quello sbagliato stava
  proprio dove la strada si sceglie. La firmata
  degli importati salta la validazione, il campo resta nascosto) +
  costo (stessa valuta del listino, `consegnaPayload`) + taglia;
  dettaglio con le PILLOLE DELLE MODALITÀ (lug 2026, dopo il feedback
  di Andrea: il 🚚 muto della card qui diventa parola) —
  `pilloleModalita()` scrive una pillola per le strade DISCRETE
  («🤝 Ritiro in zona», «💾 Codice online»); la SPEDIZIONE dal
  riordino del dettaglio (sotto) non sta più lì: è il badge
  evidenziato `spedBadge()` accanto al prezzo. SENZA il costo
  nella fila delle pillole (lug 2026): una cifra sciolta tra le
  pillole si legge come un prezzo e non dice di che totale fa parte
  — il posto del costo è il momento del pagamento, dove c'era già
  (foglio «Come vuoi riceverlo?» col totale per strada, riga
  «Spedizione» del `contoScomposto`, e il totale dei bottoni compra
  che la spedizione l'ha sempre inclusa).
  [SUPERATA, ago 2026 — SFOLLAMENTO COLORI, decisione di Andrea: la
  gratuità si evidenzia col GRASSETTO, mai col colore. Il chip azzurro
  «Spedizione gratuita» è morto: le pillole di consegna sono TUTTE
  neutre (.pill, un solo cuore) con «gratuita» in grassetto, e il
  «🚚 gratis» in card parla l'inchiostro di casa (var(--ink), token:
  di notte è crema) in grassetto. I token --ship-* restano definiti ma
  senza più chi vestire. La storia sotto resta per i perché.
  ATTENZIONE al € del dettaglio d'asta: `.detail-price .unit.eur` sta
  PIÙ IN BASSO nel foglio a pari specificità — il token dell'asta lo
  vince nominando `.asta` E `.unit.eur` insieme, per specificità e non
  per ordine (bug visto da Andrea nei due temi).]
  UN SOLO CHIP COLORATO, ED È «GRATIS» (lug 2026, decisione di Andrea
  in quattro tempi — vale la pena tenere l'arrivo, non il percorso).
  Il colore veste UNA cosa sola: che la spedizione non si paga.
  «🚚 Spedizione disponibile», «🤝 Ritiro in zona» e «💾 Codice online»
  sono dati di FATTO e stanno tutti e tre in `.pill` normali; solo
  «🚚 Spedizione gratuita» è il chip azzurro `.sped-badge`. Il perché:
  due chip colorati in fila si facevano concorrenza, e quello che
  diceva meno era anche quello che compariva più spesso (quasi ogni
  annuncio spedisce, pochi lo fanno gratis). La gratuità invece è un
  argomento di vendita e non può aspettare il fondo pagina.
  Giudici unici `spedisce` e `spedGratis` — «gratis» si decide in un
  posto solo, e da lì lo legge anche la card.
  IL COLORE È UNO E NON CAMBIA SEGNO COL TEMA. `--ship-soft` (fondo) e
  `--ship-soft-on` (testo) vestono il chip del dettaglio: azzurro
  chiaro con testo blu, 5,62. Un colore che SIGNIFICA qualcosa non può
  cambiare tinta fra il giorno e la sera, o chi l'ha imparato di
  giorno non lo riconosce più; l'inversione al buio ha senso per una
  SUPERFICIE (l'etichetta prezzo, il toast, che di sera diventano di
  carta), mai per un codice colore. L'UNICA cosa che si tara di notte
  è la LUCE: al buio i due scendono a #AEC8E0/#0E4A80 perché sul bruno
  lo stesso chiaro rendeva più che sul crema (contro il fondo 13,59 →
  11,04 → 9,95, in due gradini, il secondo chiesto da Andrea dopo
  averlo visto a schermo; il testo scende con lui e tiene 5,25).
  Attenzione alla distinzione, che è tutta la regola: si abbassa la
  luce, non si cambia il segno.
  IN CARD la stessa idea si SCRIVE: «🚚 gratis» accanto alle altre
  icone, in `--ship-card` — terzo token, e l'unico dei tre che SEGUE
  IL TEMA (#12599E di giorno, #9FC9EA di sera). Non è un'eccezione: lì
  «gratis» è TESTO NUDO sulla carta della card, e un testo deve
  contrastare la superficie su cui sta — il blu scuro sulla card bruna
  farebbe 1,67, cioè sparirebbe (8,68 così). Il segno è il chip,
  questo è inchiostro, e l'inchiostro segue la carta come ovunque
  nell'app; la famiglia (blu) resta la stessa. Si SCRIVE e non si
  colora soltanto perché un cerchietto non insegna niente a chi guarda
  la prima volta, e da quando il chip è l'azzurro chiaro non c'era più
  nemmeno un colore forte da riecheggiare a 15px. Costa ~21px al
  comune, che nel caso a tre strade scende da 69 a 47px e si tronca
  prima («Carma…»): prezzo accettato e misurato — «gratis» fa cambiare
  idea a chi compra, le ultime lettere di un paese no. La regola di
  sempre non si tocca: a cedere è il luogo, mai il gruppo di icone.
  TRE COSE PROVATE E SCARTATE, da non rifare (i motivi, non solo i
  nomi): 1) il badge PIENO blu scuro per «gratuita» contro il tenue
  per «disponibile» — due gradi della stessa famiglia si somigliavano
  troppo, e al buio il tenue spariva nel fondo; 2) SCAMBIARE i due
  colori perché «il chiaro spicca di più» — spicca di più SOLO di
  sera: sul crema il chiaro fa 1,15 contro il fondo, cioè è una
  velatura, quindi scambiandoli nel tema di DEFAULT «gratuita»
  diventerebbe la cosa più muta della fila e «disponibile» la più
  forte, in concorrenza col prezzo; 3) il cerchietto colorato attorno
  alla 🚚 in card, sostituito dalla parola per la ragione qui sopra.
  E una valutata e scartata a tavolino: colorare il RITIRO invece
  della spedizione. Il ritiro vale solo per chi è vicino — colorarlo
  significherebbe gridare a tutti gli altri una cosa che non possono
  usare — mentre «gratis» è un risparmio che vale per chiunque guardi;
  e la località la dice già il comune, lì accanto nella stessa riga.
  Se un giorno si vorrà spingere lo scambio locale, la leva non è il
  colore di un chip ma un filtro «vicino a me».
  IL GEMELLO COL COSTO SOTTO ACQUISTA È VISSUTO UN GIORNO: nato per
  dire il QUANTO nel momento in cui si compra («🚚 Spedizione +
  5,00 €», dentro il recinto), è stato tolto subito dopo averlo visto
  — e la ragione vale anche per chi volesse rimetterlo. Il recinto è
  il posto della FIDUCIA, non del listino: una cifra là dentro fa
  nascere la domanda «di che totale fa parte?» senza rispondere, e
  spezza la riga sola che il recinto deve dire. Il QUANTO vive dove
  c'è un totale VERO accanto: il foglio «Come vuoi riceverlo?» del
  varco (`cifraVia`), la riga «Spedizione» del `contoScomposto` nel
  paySheet, e i bottoni compra, che la spedizione l'hanno sempre
  inclusa. Con lui se ne sono andati `spedBadgeCosto` e
  `spedCostoTesto` (e la classe `.sped-riga`).
  LACUNA TEMPORANEA, DICHIARATA (lug 2026, e questo va letto insieme
  al paragrafo qui sopra, o il paragrafo sembra dire che va tutto
  bene): oggi il costo della spedizione NON si vede da nessuna parte
  nella scheda. Chi ha due strade lo incontra al primo tocco su
  Acquista, nel foglio del varco, che porta il totale per strada; ma
  chi ha la SOLA spedizione il varco non lo apre proprio (serve da due
  strade in su) e scopre il costo nel paySheet, alla riga
  «Spedizione» del conto scomposto — cioè dopo che la invoice è già
  nata. È tardi, ed è riconosciuto come tale. NON si rimedia
  rimettendo una cifra nella scheda (la fila delle pillole e il
  recinto sono stati provati, entrambi per ragioni diverse non
  reggono, vedi sopra): il rimedio è LA PAGINA D'ACQUISTO DEDICATA
  del prossimo cantiere — scelta della strada e conto scomposto in un
  posto solo, prima della invoice — che è la destinazione già
  dichiarata del foglio del varco (vedi IL VARCO). Chi arriva qui
  prima di quel cantiere: la lacuna è nota e ha già la sua casa, non
  aprirne una seconda. Con la vecchia riga del
  costo nella fila delle pillole se n'era andata
  `rigaConsegna` — la riga «🛡️ protezione acquisti inclusa» era
  rumore: la protezione c'è SEMPRE, quindi non è un'informazione, e
  a raccontarla è il recinto escrow. Il dettaglio
  mostra SOLO: data · luogo (se c'è) · consegna · condizione ·
  disponibilità (se >1) · verifica Nostr (nel riquadro venditore).
  NON la categoria (ci si
  arriva dai filtri) e NON la taglia del pacco (è roba del
  venditore e del futuro tariffario per-taglia, al compratore non
  serve lì; via anche `tagliaPill`).
  RIORDINO DEL DETTAGLIO (lug 2026, stile Subito.it): dall'alto —
  foto · riga data `dataRiga()` (piccola e grigia, `.pub-data`): il
  «quando» e basta, «3 giorni fa» — la pubblicazione NON si nomina
  (a quel posto non può voler dire altro), il verbo resta solo
  all'«aggiornato N giorni fa», che è un fatto diverso · titolo con
  la pillola condizione IN CODA, come fosse l'ultima parola («Crema
  spalmabile NUOVO»): `titoloConCondizione()` la mette DENTRO l'h2,
  nel flusso del testo, e la lega all'ULTIMA PAROLA con un nowrap
  (`.fine-titolo`) — così se sull'ultima riga non c'è posto scendono
  INSIEME («Cuffie da studio AKG / K371 Come nuovo») invece di
  lasciare la pillola sola a capo. Ultima parola oltre 14 caratteri
  = non si lega (legate traboccherebbero). Il flex è stato provato
  due volte e non regge: con la base `auto` manda a capo la pillola
  PRIMA di stringere il titolo, con `flex:1 1 0` la incolla a destra
  lontano dalle parole · luogo come TESTO nudo
  `luogoRiga()` (niente pillola) · prezzo — col listino BARRATO
  della lampo SEMPRE sotto di lui, in euro come in sats
  (`.prezzo-col` è una colonna: di lato le due cifre si leggevano
  come una riga di conto; stesso mono, 24px contro 28, e la
  barratura taglia la cifra ma non la parola «sats», che è piccola e
  sembrava sottolineata — la ferma un `display:inline-block`, che
  dal figlio la decorazione ereditata non si toglie altrimenti) — e
  a DESTRA sulla stessa
  riga il toggle valuta €/₿ (`.prezzo-riga`, gemello di quello
  della searchbar: stesso `setValuta`, stessa preferenza; i due si
  accendono insieme perché `aggiornaCurToggle` li pesca per
  `data-cur` e non più per id, e `aggiornaPrezzoDettaglio` riscrive
  il prezzo IN PLACE senza riaprire la scheda — openDetail
  azzererebbe pezzi scelti e strada) · sotto, la riga ≈ dell'altra
  valuta · la fila delle pillole, che si apre col badge EVIDENZIATO
  della spedizione (`spedBadge()`, coppia azzurra
  la coppia azzurra --ship-soft/--ship-soft-on, sua e solo sua: AA nei
  due temi, non fa concorrenza né all'arancio del prezzo né al verde
  escrow;
  forma da pillola come le vicine — stava accanto al prezzo per un
  giorno, ma il suo posto sono le caratteristiche; i due gradi e il
  gemello col costo sotto Acquista sono spiegati sopra) ·
  le altre
  strade come pillole discrete · «DESCRIZIONE» col suo titolino
  `.desc-tit` · riquadro venditore SOLO anagrafica: avatar, nome col
  🟣 in fila coi badge (icona nuda, pattern della testata negozio —
  la scritta «verificato su Nostr» e i ponti di contatto non stanno
  più qui: la verifica è dell'utente e si racconta nel negozio, dove
  i ponti già vivono), sfilza, stelle e freccia. Da lì in giù tutto
  com'era (recinto — che dalle correzioni del lug 2026 ospita il solo
  «Acquista» arancio centrato, con «Fai un'offerta» fuori sotto e
  senza più le pillole di scelta —, altri oggetti, barra col
  richiamo escrow: vedi barra d'acquisto). LA DATA: colonna `annunci.modificato` (0 = mai
  toccato) scritta da modifica() e dalla modifica firmata; per gli
  IMPORTATI l'import ci mette la data dell'EVENTO Nostr
  (`evento_ts` = created_at, che per un replaceable è la
  pubblicazione vera) su INSERT e UPDATE, e il client la mostra
  sempre come «pubblicato» (l'update di là sostituisce l'evento
  intero; `creato` resta l'ora dell'import e ordina la vetrina,
  NON va toccato: il cursore keyset ci vive sopra). Leva
  `GIORNI_DATA_ANNUNCIO` (60, 0 = spenta) nella busta di PRIMA
  pagina come protezione_percento: oltre, la riga sparisce — un
  annuncio stagionato non deve auto-denunciarsi. `a.modificato` in
  CAMPI_VETRINA (search e miei gratis via a.*).
  Il disegno della taglia — che vive ancora nel foglio-picker di
  Vendi e nella stima del set — dal lug 2026 porta la SCALA
  DISEGNATA: `tagliaSVG(id, box)` invece delle emoji, perché 📦 era la
  stessa per piccolo, medio e grande e la gradazione non si vedeva.
  L'ingombro resta fisso (viewBox 22x22 per tutte le voci) e la
  scatola CRESCE DAL BASSO — come una cosa appoggiata sul banco: le
  voci del foglio restano incolonnate e il confronto si legge a colpo
  d'occhio. Lati 8/12/16/20 (il primo tentativo 10/13/16/20 era troppo
  timido) e SOLO quadro + riga del coperchio: il nastro verticale,
  provato, a 8px si riduceva a un puntino di rumore. Tratto a
  `currentColor` come `jarSVG` (chiaro e scuro gratis) con un velo
  dello stesso colore che dà corpo; la busta è un oggetto suo — piatta
  con la piega a V — non una scatola piccola, e nella pillola
  la busta, nei testi, non si fa chiamare «pacco busta» ma «busta
  imbottita». Scartate le emoji scalate via CSS: cambiano forma da un
  sistema all'altro, non seguono i token del tema e crescendo spostano
  le righe. `box` è solo la misura resa (22 nel foglio-picker e nel
  campo: il viewBox non cambia, quindi il rapporto fra le taglie
  resta identico a ogni misura). Per
  'entrambe' due pillole spedizione/ritiro DENTRO l'escrow-zone
  (`consegnaScelta`, si riparte da spedizione a ogni dettaglio; la
  cifra dei bottoni è `totaleStima`); conto scomposto
  (`contoScomposto`) nel paySheet e nella conferma NWC — stima
  subito, valori VERI dalla risposta di /orders; ordine con riga
  consegna+quote, pannello «🤝 Consegna in zona» con
  `markConsegnaMano` al posto di corriere/tracking, `payoutPanel` e
  testa released = totale − protezione; checkbox «🚚 Solo con
  spedizione» nei filtri (in DEMO client-side in renderGrid); icone
  discrete nella meta della card — il prezzo in griglia resta pulito.
  LA RIGA META DELLA CARD (lug 2026): il comune a sinistra, le icone
  in un GRUPPO stretto a destra (`iconeCard` → `<span class="ico">`,
  ordine 🚚 🤝 💾 come nel dettaglio; il 🤝 del ritiro prima in card
  non c'era). SOLO le strade di consegna: il pallino Nostr è USCITO
  dalle card (lug 2026) — in griglia lo spazio è poco, e la verifica
  riguarda il VENDITORE, non l'oggetto: vive nel dettaglio, accanto
  al suo profilo, che è dove uno se la chiede (il gruppo è passato da
  66 a 53px, e il comune ne ha guadagnati altrettanti prima di
  troncare). Prima le icone erano figli diretti di un flex
  `space-between` e si sparpagliavano per tutta la riga; ora a
  spartirsi lo spazio sono in due, e a cedere coi puntini è SEMPRE il
  comune (`.luogo` con `flex:1 1 auto` + `min-width:0`) mentre il
  gruppo non si stringe mai — a 360px con tutte e tre le icone
  insieme deve restare intero. `min-height:17px` sulla riga, che può
  essere vuota del tutto (zona non riconosciuta e nessuna icona) e le
  card resterebbero disallineate.
  La SPEDIZIONE GRATUITA si vede anche in griglia (lug 2026), e si
  SCRIVE: «🚚 gratis» accanto alle altre icone, nel blu `--ship-card`.
  Il perché della parola invece del solo colore, il costo misurato in
  pixel e le rese scartate stanno nella sezione della spedizione, sotto
  «UN SOLO CHIP COLORATO»: qui basti che a cedere resta il comune, mai
  il gruppo di icone.
  Consegna digitale 💾 (lug 2026, quarta voce di MODALITA_CONSEGNA):
  per buoni regalo, codici, licenze — il PRINCIPIO CARDINE è che il
  contenuto passa DENTRO Barattolo, mai fuori. La modalità è LIBERA
  dal tipo di bene (una gift card fisica si spedisce, un codice si
  consegna digitale: le tutele seguono la modalità, mai il tipo);
  niente costo spedizione né taglia (consegna_da_payload azzera anche
  la taglia arrivata per sbaglio). COMBO (lug 2026, la gift card in
  due modi «ti spedisco la tessera, oppure ti mando il codice»):
  colonna `annunci.anche_digitale`, ORTOGONALE di proposito —
  `consegna` tiene la semantica fisica di sempre e ogni check
  esistente resta vero; lecita solo accanto a una modalità fisica
  (con 'digitale' o '' il giudice la forza a 0). Le TUTELE seguono la
  SCELTA del compratore, non l'annuncio (già così per costruzione:
  finestre, blocco di segna_spedito, endpoint contenuto, tetto
  compratori e pannelli leggono `consegna_scelta`): compra() valida
  contro il SET delle strade offerte (spedizione/ritiro dal catalogo
  + digitale se esclusivo o anche_digitale), scelta sconosciuta non
  vuota = 400, scelta assente = default FISICO (spedizione batte
  ritiro, digitale solo se unica: il client vecchio in cache prende
  la strada che conosce); `guardia_venditore_digitale(tg_id,
  consegna, anche_digitale)` copre la combo, anche nell'import CSV
  dove la cella consegna parla col «+» (`spedizione+digitale`,
  riga d'esempio nel modello). `anche_digitale` è in CAMPI_VETRINA;
  NIP-99 aggiunge «o consegna digitale immediata» (e il ritiro combo
  perde il «solo»). Frontend: la combo nasce spuntando la casella
  «💾 Invio del codice online» accanto a una fisica (vedi le tre
  caselle nella sezione spedizione: il vecchio checkbox «Offro
  anche…» e il select non esistono più, «consegna digitale» era
  ambigua e i testi pubblici ora dicono «codice online»);
  la scelta della strada vive nel foglio «Come vuoi riceverlo?» del
  varco (`stradeConsegna` resta il giudice delle strade offerte; le
  vecchie pillole di scelta `pilloleConsegna` dentro l'escrow-zone
  sono morte con le correzioni del lug 2026 — in pagina restano solo
  le pillole INFORMATIVE, che raccontano e non si toccano);
  trust-note asimmetrica `#notaDigitale` visibile SOLO con la scelta
  digitale attiva (su una combo non deve spaventare chi sceglie la
  spedizione, `setConsegnaScelta` la accende/spegne); la pillola
  «💾 Codice online» di `pilloleModalita` (che ha sostituito il vecchio
  «o 💾 codice online» della riga sotto il prezzo, `rigaConsegna`,
  poi sparita del tutto); in card 🚚, 🤝 e 💾 possono convivere.
  NIENTE stati nuovi: locked→shipped
  = `POST /api/orders/{id}/consegna-digitale` (solo venditore,
  contenuto 1-4000 caratteri, corriere-sentinella 'Consegna digitale',
  riga journal con impronta sha256 troncata e MAI il testo);
  shipped→delivered = la RIVELAZIONE, `GET /api/orders/{id}/contenuto`
  — la PRIMA lettura del compratore scrive `consegnato` (= ricevuta di
  lettura) e fa la transizione, le successive sono idempotenti; il
  venditore rilegge ciò che ha consegnato senza effetti, l'admin legge
  solo negli stati di disputa. `ordini.contenuto_digitale` (colonna
  nuova) è cifrata a riposo con Fernet — `CHIAVE_CONTENUTI_DIGITALI`
  in config, prefisso 'f:'; chiave vuota o cryptography assente =
  'plain:' in chiaro, fail-open, i due formati convivono per sempre
  (_cifra_contenuto/_decifra_contenuto) — e NON esce MAI da
  /api/orders (strip con flag `contenuto_presente`): si legge solo
  dall'endpoint-ricevuta. `segna_spedito` su ordine digitale = 400
  (il timer non deve partire senza contenuto consegnato). Finestre
  CORTE in controlla_scadenze: ORE_CONFERMA_DIGITALE (24) dalla
  rivelazione, ORE_SILENZIO_DIGITALE (48) dalla consegna mai rivelata
  — i due rami fisici escludono il digitale. Il caso irriducibile
  (codice riscattato e poi negato) NON si risolve, si rende
  antieconomico: regola di default ASIMMETRICA dichiarata prima
  dell'acquisto («un codice rivelato non torna indietro: 24 ore per
  aprire una disputa, poi l'acquisto è definitivo» — trust-note nel
  dettaglio, confirm della rivelazione, notifica di consegna; dal
  lug 2026 MAI «salvo prove» né promesse di rimborso verso il
  compratore: Barattolo non può verificare i riscatti, deciso con
  Andrea — i consigli-screenshot al VENDITORE restano, sono le prove
  che porta lui), nota al moderatore in apri_disputa (conteggio
  dispute del compratore = le dispute-fotocopia si vedono, + invito
  a chiedere all'emittente quando/dove il codice è stato riscattato,
  e la precisazione che la regola «a zero prove vince chi ha
  consegnato» segue il BENE riscattabile, non il canale: vale anche
  per un buono spedito fisicamente), e leve config SPENTE di
  serie (default 0, pattern TETTO_SATS_ANNUNCIO):
  TETTO_DIGITALE_NUOVI (compratore con acquisti_ok=0 oltre il tetto =
  400, sul solo articolo, in compra()) e DIGITALE_MIN_VENDITE
  (`guardia_venditore_digitale` in pubblica/modifica, riga scartata
  nell'import CSV). SERVIZI ESCLUSI (decisione di prodotto, lug 2026):
  Barattolo vende COSE che esistono, fisiche o digitali — il
  PROMPT_MODERAZIONE vieta prestazioni e servizi («VIETATO: servizio»)
  e whitelista i prodotti digitali leciti (buoni regalo, gift card,
  codici sconto, licenze — nato dal buono Zalando bloccato per
  errore); `messaggio_rifiuto(motivo)` mappa il no dell'AI sui servizi
  al gentile MSG_RIFIUTO_SERVIZI («non ancora supportati»), 'servizi
  sessuali' resta col messaggio severo di sempre. Frontend: casella
  «💾 Invio del codice online» in Vendi con hint screenshot datato
  («in disputa le prove decidono», ripetuto nel pannello di
  consegna); dettaglio con riga «💾 codice inviato online, subito» +
  trust-note asimmetrica; 💾 nella meta della card; ordine con stepper
  «Contenuto consegnato → Rivelato» (finestra 24h nel testo), pannello
  venditore con textarea (`consegnaContenuto`), box «🔓 Rivela» col
  confirm-ricevuta (`rivelaContenuto`), rilettura `mostraContenuto` e
  copia di pagina `contenutoRivelato` (il testo non vive in orders:
  arriva solo da /contenuto); per il compratore niente «è arrivato»
  su shipped digitale (la strada è la rivelazione). NIP-99: riga
  «consegna digitale immediata» nel content, nessun tag nuovo; gli
  importati restano fuori per natura (consegna '': per consegnare il
  codice il venditore deve essere in piattaforma). Modello CSV con la
  riga d'esempio `digitale` (parser già coperto dal giudice unico).
  Offerte / contrattazione sul prezzo (lug 2026, modello Vinted; sara'
  la base del futuro «Lotto», fase 3): NON una chat — macchina a stati
  con al massimo UNA controproposta. Tabella `offerte` (annuncio,
  parti, `valuta` fotografata dal listino, importo_sats/importo_eur
  della proposta e contro_sats/contro_eur della controproposta — uno
  dei due campi sempre 0; UN solo campo `scadenza` riscritto a ogni
  transizione; `ordine_id` = ponte verso l'ordine). Stati: proposta →
  controproposta → accettata → conclusa, più rifiutata / scaduta /
  decaduta. REGOLA CARDINE: l'annuncio non si blocca mai — vince chi
  paga per primo, le offerte rimaste vive decadono con la notifica di
  garbo 🕊 (MAI al compratore vincente). L'accordo riguarda il SOLO
  articolo: spedizione e protezione si sommano sopra come per ogni
  ordine (protezione sull'articolo concordato). Leve config (pattern
  try/except): OFFERTA_MINIMA_PERCENTO (50, minimo per ECCESSO sui
  sats), ORE_RISPOSTA_OFFERTA (48), ORE_PAGAMENTO_OFFERTA (24),
  MAX_OFFERTE_ANNUNCIO (3 tentativi totali per compratore per
  annuncio, UNA attiva alla volta — count-guard senza await, patto
  anti-doppione). Endpoint: `POST /api/listings/{id}/offerta` (importo
  nella valuta del listino, virgola ammessa; ≥ listino = 400 «puoi
  comprare direttamente»; qui il cambio non serve MAI: mai 503),
  `POST /api/offerte/{id}/rispondi` (azione accetta|rifiuta|contro;
  gate di ruolo per stato: proposta = venditore, controproposta =
  compratore e il ping-pong finisce li'; contro > offerta e
  ≤ listino; scadenza controllata anche inline), `GET
  /api/me/offerte` (busta con le leve: il client non hardcoda cifre),
  `offerte_da_agire` in /api/me e `offerta_minima_percento` nella
  busta di prima pagina. L'acquisto: `compra()` con `offerta_id` =
  stessa strada di sempre ma articolo alla cifra pattuita
  (`_importo_accordo`: la contro se c'e', senno' la proposta; EUR
  convertito alla invoice col cambio_ordine, drift/tetto/protezione
  invariati); il legame `offerte.ordine_id` si scrive NELLA stessa
  transazione dell'INSERT; invoice viva gia' in corso = 400 (pagare
  la vecchia lascerebbe l'offerta orfana). `verifica_pagamento`:
  l'offerta dell'ordine pagato → 'conclusa', TUTTE le altre vive
  sull'annuncio → 'decaduta' (notifiche dopo il commit). Reaper e
  annulla_ordine azzerano `ordine_id` (l'offerta resta accettata fino
  alla SUA scadenza: si ripaga con invoice nuova). `scadenze_offerte`
  nell'orologio: scadenza passata → 'scaduta', annuncio non piu'
  attivo → 'decaduta' (copre le rimozioni senza ganci nei delete).
  `modifica()` col prezzo cambiato fa decadere le PENDENTI (erano una
  % di un prezzo che non esiste piu'); le ACCETTATE sopravvivono
  (l'accordo e' stretto). Dal lug 2026 valgono ANCHE per gli importati
  da Nostr (il catalogo e' uno solo, cambia solo chi firma il NIP-99):
  il venditore solo-Nostr riceve l'offerta via DM NIP-17 col link
  /annuncio/{id}, entra col login npub e risponde da qui. ATTENZIONE
  all'imperfezione dichiarata: l'import orario che riscrive il prezzo
  NON fa decadere le offerte pendenti (a differenza di `modifica()`) —
  la cifra e' assoluta, il venditore la giudica contro il nuovo listino
  e comunque scade da sola. `esegui_fusione`
  migra le offerte e cancella le auto-trattative tra le due meta'.
  Piu' offerte accettate possono coesistere: lecito, il confirm del
  venditore lo dichiara («accettare non riserva l'oggetto»). Frontend:
  «Fai un'offerta» subito FUORI dal recinto escrow (e a sinistra di
  Acquista nella barra; nascosto con accordo gia' fatto),
  foglio `#offertaSheet` (registrato in closeSheet) con miniatura+
  titolo+listino, chip −10%/−20% precalcolati, campo nella valuta del
  listino (virgola per EUR) e stima live «≈ N sats totali» (matematica
  di totaleStima con l'articolo offerto, onesta senza cambio); sezione
  «💰 Offerte» sopra gli ordini nella scheda Ordini (`renderOfferte`,
  solo trattative VIVE, azioni inline Accetta/Controproponi/Rifiuta
  con input che non si perde nei re-render, «⚡ Paga ora» per
  l'accettata) + pallino `.off-dot` sul tasto Ordini quando una
  offerta aspetta una MIA mossa; «Paga ora» RIAPRE il dettaglio, che
  con l'accordo mostra il banner 🤝 e i totali pattuiti (`artStima`
  dentro totaleStima) — pillole consegna, NWC, nota EUR ereditati
  gratis; startBuy e compraSubito mandano `offerta_id` (0 = ignorato).
  LESSICO (deciso lug 2026): la scheda per gli utenti si chiama
  «Ordini», non piu' «Affari» — in TUTTI i testi (notifiche, UI,
  confirm); gli id interni (go('affari'), #nav-affari, view-affari)
  restano.
  Offerta lampo ⚡ (lug 2026, modello Vinted «sconto ai follower»):
  sconto PUBBLICO a percentuale, a tempo, sul SOLO articolo —
  spedizione e protezione si sommano sopra, e il listino NON si tocca
  mai (prezzo_sats/prezzo_eur restano pieni, quindi il NIP-99 parla
  il prezzo pieno PER COSTRUZIONE: lo sconto e' un vantaggio di chi
  compra dentro Barattolo; dal lug 2026 vale anche per gli importati —
  lo sconto e' locale, le colonne lampo_* non toccano il listino e
  l'import orario non le riscrive: se il prezzo cambia sui relay la %
  segue il prezzo nuovo, che e' la natura di uno sconto a percentuale).
  Colonne
  `annunci.lampo_percento/lampo_scadenza/lampo_creato` (attiva =
  percento>0 e scadenza futura: OGNI lettura gatea sulla scadenza, la
  scopa `scadenze_lampo` nell'orologio azzera solo i numeri morti,
  senza notifiche) + `lampo_colpo_avvisato` (cooldown dell'avviso) +
  tabella `offerte_lampo` = storico dei lanci per il tetto
  settimanale (le colonne si sovrascrivono, non contano il passato).
  Leve config (try/except): LAMPO_ATTIVE (True), LAMPO_SCONTI
  [10,20,30], LAMPO_MIN/MAX_PERCENTO (5/70), ORE_LAMPO_OPZIONI
  [6,24,48], MAX_LAMPO_SETTIMANA (2), GIORNI_COLPO (7). «Ha fatto
  colpo»: gancio nel ramo INSERT di `toggle_preferito` (DOPO il
  commit, solo annunci attivi, mai i salvataggi propri; l'endpoint e'
  diventato async per il create_task, precedente /api/me) → valvola
  gemella dei promo `accoda_colpo`/`_drena_colpo` (rilettura dal DB:
  spariti/gia' in lampo/in cooldown = muti; cooldown
  timbrato PRIMA delle notifiche; per venditore ≤SOGLIA_AGGREGA
  messaggi singoli con link, oltre UN aggregato) — avviso ANONIMO:
  «qualcuno», mai chi ne' quanti, i preferiti restano privati per
  natura. Lancio: `POST /api/listings/{id}/lampo` (solo il
  proprietario su attivi, percento/ore dalle leve, count-guard senza
  await sul tetto; FRENO: offerta accettata viva = 400, la stretta di
  mano non si cambia in tavola — le pendenti invece NON decadono)
  scrive colonne+storico e avvisa i savers in create_task
  (`_avvisa_savers_lampo`: barrato → scontato, «hai tempo fino
  alle...» di `_quando_scade`, mai i nomi); `/lampo/annulla` = prezzo
  pieno subito ma il lancio resta nello storico (annullare non
  restituisce il gettone: lancia-e-annulla non dev'essere spam
  gratis). `compra()`: lampo viva = articolo al prezzo di
  `_prezzo_lampo` (giudice unico, valuta del listino; EUR converte
  alla invoice come sempre) col MINIMO sull'eventuale accordo
  individuale — chi paga paga sempre il meglio dei due. Superficie:
  lampo_percento/scadenza in CAMPI_VETRINA (search e miei gratis via
  a.*), param `solo_lampo`, ordinamento `lampo` in ORDINAMENTI
  (keyset (lampo_scadenza,id) ASC = chi scade prima in testa, IMPLICA
  il filtro; indice idx_annunci_lampo), leve in /api/me.lampo_leve.
  Frontend: `lampoAttiva`/`conLampo` (vista scontata del listino,
  gemello client di _prezzo_lampo)/`lampoResta`; in CARD il badge
  dice la SOLA percentuale «⚡ −20%», in alto a sinistra sulla foto
  (colori fissi nei due temi, MAI animazioni: patto reduced-motion;
  dal lug 2026 niente countdown lì — allungava il badge e chiedeva
  un aggiornamento al secondo per ogni card disegnata), cartellino
  col listino barrato; il TEMPO che resta vive solo nella scheda,
  sotto il badge e fuori da lui: «rimangono 2h 14m»
  (`.lampo-resta`, colore `--sats-text`, `flex-basis:100%` = SEMPRE
  una riga sua: in euro i tre pezzi ci stavano e in sats no — il
  barrato «180 000 sats» è largo il doppio di «≈ 166 €» — e la riga
  cambiava forma secondo la valuta; meglio una riga in più sempre
  che due rese diverse per la stessa cosa) — la vecchia riga «⚡
  Offerta lampo: ancora…, poi il prezzo torna pieno» è sparita, che
  diceva la stessa cosa due righe sotto. UN solo setInterval per
  tutta l'app aggiorna i `.lampo-count` in-place (ormai uno solo, nel
  dettaglio) e allo zero fa renderGrid + riapertura della scheda in
  sconto — che riconosce dal BARRATO ancora in pagina (`.lampo-was`,
  la sentinella era la riga sparita). La griglia non ha più contatori
  da leggere ma deve comunque tornare a prezzo pieno da sola: ci
  pensa `prossimaLampo`, la prima scadenza fra le card disegnate,
  riscritta in fondo a `renderGrid` — un numero da confrontare invece
  di frugare nel DOM ogni secondo; `artStima` passa da
  conLampo col min sull'accordo (bottoni compra e conto scomposto
  parlano da soli la cifra scontata); foglio `#lampoSheet` del
  proprietario (chip dalle leve, durate a pillole, anteprima
  barrato→scontato con l'ora di fine; nel dettaglio owner «⚡ Lancia
  un'offerta lampo» che con la lampo viva diventa «annullala» con
  confirm); filtro «⚡ Solo in offerta» + voce «⚡ In offerta» in
  Ordina, in DEMO client-side col seme dimostrativo (Cuffie Sony,
  scadenza calcolata al carico).
  L'ASTA 🔨 (ago 2026, «vendita al miglior offerente»): base + durata
  (1/3/7/14/30 giorni, in collaudo anche minuti), chi vuole comprare PUNTA
  versando sats nel deposito di garanzia, per superare chi è in testa
  si versa SOLO LA DIFFERENZA, alla scadenza la puntata più alta
  diventa un ordine normale GIÀ pagato e i perdenti vengono
  rimborsati. Il pregio che ha deciso il cantiere: il vincitore non
  può sparire, ha già pagato. PRINCIPIO ARCHITETTURALE: l'asta
  finisce esattamente dove inizia un ordine — il ciclo di vita degli
  ordini non si tocca; la chiusura invoca `crea_ordine_pagato`, LA
  PRIMITIVA «ordine già pagato» (nasce 'locked', scrive dentro la
  transazione del chiamante) che la futura pagina d'acquisto riuserà.
  SCHEMA: colonne `annunci.asta_base_sats/asta_scadenza/asta_creato/
  asta_avvisata_1h` (patto lampo: gate in LETTURA; `prezzo_sats` È la
  base e non si tocca mai; base>0 e scadenza=0 = DESERTA in mano al
  venditore) + tre tavoli: `puntate` (UNA riga per offerente per
  asta — versato, offerto, `saldo_seq`, etichetta anonima «Offerente
  A,B,C…» per ordine di primo saldo, stati attiva|vincitrice|chiusa,
  UNIQUE(annuncio_id,tg_id)), `rilanci` (una per FATTURA di
  versamento: il client dichiara il TOTALE, il server calcola il
  delta — mai fidarsi di importi dal client; fatture da 10 minuti,
  expiry parametrico su crea_invoice_escrow; stati creato|saldato|
  tardivo), `rimborsi_asta` (il REGISTRO «Da riscuotere» con le
  cinture d'idempotenza a indici parziali; motivi ritiro|perdente|
  tardivo|annullo_admin). INVARIANTI provati in CI: Σ delta saldati =
  versato del vincitore + Σ registro; versato==offerto per ogni
  puntata attiva.
  SALDO_SEQ, la lezione del collaudo: «fa fede l'orario di saldo» a
  risoluzione di secondo NON basta come tie-break (due saldi
  pari-cifra nello stesso secondo sono usciti subito, e vinceva chi
  aveva CREATO la fattura prima). È un progressivo GLOBALE assegnato
  nel blocco senza await della verifica: a parità di cifra comanda
  chi ha saldato prima — per prendere la testa bisogna SUPERARE.
  `_leader_asta` è il giudice UNICO di «chi è in testa» (guardie di
  punta, stato personale, notifiche, pallino, ritiro) e
  `conto_chiusura` è il gemello puro con lo STESSO ordine: sentinelle
  in prove.py, un MAX sulla cifra direbbe il contrario sul pari-cifra
  (successo in /api/me, preso in revisione).
  IL MOTORE: `POST /api/aste/{id}/punta` con la liturgia di compra()
  (guardie → unico await sulla fattura → ricontrollo → zero await al
  commit). Guardie: leva, asta viva (READ GATE: chiusa anche se
  l'orologio non è passato), mai la propria (tg_id E npub condivisa),
  LIGHTNING ADDRESS OBBLIGATORIO alla prima puntata (è il binario del
  rimborso), ritiro definitivo (409), una fattura pendente alla
  volta, minimo = `rilancio_minimo` (+5%, MAI meno di 1 sat: la
  funzione unica di endpoint, foglio e CTA delle notifiche), «sei già
  in testa» (rilanciare su sé stessi costerebbe senza motivo).
  `POST /api/rilanci/{id}/verifica` = poll col CAS: saldo valido =
  versato che si somma + etichetta al primo saldo + PROROGA
  ANTI-CECCHINO nel write path (`nuova_scadenza`: saldo negli ultimi
  ASTA_PROROGA_MINUTI → scadenza = saldo+proroga, NESSUN tetto: l'asta
  finisce con 10 minuti di silenzio) + l'annuncio entra nei preferiti
  da solo; la corsa non si respinge MAI — saldo con testa già più
  alta = puntata valida non in testa, notifica onesta; saldo FUORI
  TEMPO (asta chiusa O puntata ritirata: la fattura pagata nei suoi
  10 minuti ma mai verificata sopravvive alla finestra del ritiro —
  cintura con sentinella in CI) = dritto nel registro, mai versato su
  una puntata fuori gara, mai un ordine.
  IL RITIRO È DEFINITIVO (regola 6 emendata da Andrea): chi non è in
  testa esce quando vuole (CAS + riga registro nella stessa
  transazione, riscossione immediata, FUORI dal gate della leva), ma
  non rientra — mette un tetto per costruzione ai rimborsi (uno a
  offerente) e rende il gesto inequivocabile. Il leader non si ritira
  MAI. Il reaper delle fatture mai saldate (soglia 1200s) libera la
  riga UNIQUE di chi non ha mai pagato: quello non è un ritiro.
  «DA RISCUOTERE» = IL BINARIO DEGLI INCASSI, nessun tubo nuovo:
  `_paga_rimborso` (lock per rimborso, cascata invoice depositata →
  ln_address → fermo, MAI retry), ripiego `POST /api/rimborsi/{id}/
  invoice` a importo esatto, scandaglio di /api/me/ln-address ESTESO
  al registro, `sollecita_rimborsi_puntate` nell'orologio con le
  STESSE leve degli incassi (🧊 admin oltre il tetto, poi silenzio).
  Rimborso INTEGRALE al sat: le fee di routing le paga la
  piattaforma, come ogni uscita.
  LA CHIUSURA: `chiudi_aste` nell'orologio (gira ANCHE a leva spenta:
  i sats non sono ostaggio di ASTA_ABILITATA; il jitter dei 10 min
  ritarda solo l'aggiudicazione, mai un rilancio). Ogni asta è UNA
  transazione col RICONTROLLO DELLA SCADENZA DENTRO (la proroga
  arrivata tra la SELECT e la lavorazione salva l'asta dal giro);
  idempotente: il commit la porta fuori dalla SELECT in un colpo,
  crash dopo il commit = le righe da_riscuotere le recuperano
  solleciti/scandaglio/ripiego. Vincitrice → ordine 'locked'
  (payment_hash dell'ultimo saldo, cambio fotografato, quote 0,
  quantità 1) → annuncio 'venduto'+quantità 0; perdenti → registro +
  riscossione post-commit. IL VINCITORE SCEGLIE LA STRADA DENTRO
  L'ORDINE (`POST /api/orders/{id}/consegna`, dal varco; una strada
  sola = fissata alla nascita): finché `consegna_scelta` è vuota il
  venditore vede «in attesa della scelta» e segna_spedito rifiuta —
  NESSUNA finestra di tutela parte prima della scelta; gli ordini
  STORICI con consegna '' restano il flusso di sempre (la differenza
  la fa l'annuncio all'asta, flag `asta` in /api/orders). Le strade
  dell'asta sono SOLO a costo zero (ritiro, codice online, spedizione
  INCLUSA nel prezzo: il costo è forzato a 0): chi vince non paga mai
  nient'altro. Notifiche: vincitore 🏆, perdenti, venditore, avviso
  «scade tra 1h» ai partecipanti (timbro una tantum; la proroga oltre
  l'ora non lo riarma, dichiarato), polso ordini admin sull'ordine
  nato — nessuna notifica admin nuova oltre al polso.
  DESERTA: scadenza azzerata, base intatta, NON comprabile (compra()
  rifiuta su base>0, anche deserta); il venditore Rilancia
  (`/api/aste/{id}/rilancia`) o Converte a prezzo fisso alla base
  (`/converti` — lecito anche su asta viva SENZA puntate salde: è
  l'annullo del venditore che conserva l'annuncio). CON puntate salde
  l'asta è VINCOLANTE (`_puntate_attive_salde`): niente modifica
  (mai, nemmeno senza puntate: si ritira e si ripubblica), niente
  rimozione, niente riapertura in revisione — solo l'ANNULLO ADMIN
  (`/api/admin/aste/{id}/annulla`: tutte al registro, poi la
  rimozione ordinaria passa). `chiudi-ora` solo in collaudo, dalla
  STESSA chiusura. Un'asta nata in revisione riparte col CRONOMETRO A
  NUOVO alla pubblicazione (decidi_revisione: la coda dei moderatori
  non mangia la durata — regola di prodotto).
  ESCLUSIONI (predicato `_asta`): niente compra diretto, offerte,
  lampo, set (motivoEsclusione), quantità>1 (forzata 1), ricarica;
  solo sats; solo annunci nativi (l'import orario riscrive il
  prezzo); NIENTE NOSTR né promo né match (i loro testi direbbero un
  prezzo a cui non si può comprare — la scoperta è la vetrina col
  filtro «🔨 All'asta», l'ordinamento «chi scade prima» su
  idx_annunci_asta, il badge in card col tempo a grana grossa e il
  countdown vivo solo nel dettaglio, sul battito unico).
  L'ASTA PARLA PETROLIO (ago 2026, ritocchi di Andrea: prima blu, poi
  verde-blu scuro tenuto sul lato BLU della famiglia — tinta ~195°,
  col verde della protezione a ~151°: si toccano nel punto più
  delicato, il bottone dentro il recinto verde, e la prova del nove
  sugli screenshot ingranditi li distingue al primo sguardo): token
  `--asta` #0F6D8C (di sera si SCHIARISCE a #1D7FA0 — si alza la
  luce, non si cambia il segno; misurati: bianco sopra 5,86/4,57, vs
  crema 5,33, vs bruno 3,77), `--asta-text` #0B5570/#7FC4DC (7,51 su
  crema, 8,88 su bruno, distinto dal ghiaccio della spedizione),
  `--asta-tag` #0B5570 FISSO (vive sul cartellino di carta, che non
  cambia di notte: 7,80) — l'arancio è di Acquista, il rosso della
  lampo, il verde della protezione, il viola di Nostr. Anche il NUMERO
  GRANDE del dettaglio di un'asta parla il token (`.detail-price.asta`,
  simbolo di valuta compreso: la regola `.unit` lo lascerebbe arancio,
  mezzo numero per famiglia): l'identità non si spezza sulla soglia
  card→dettaglio, l'arancio resta dei prezzi veri. ATTENZIONE
  alla trappola pagata qui: la riga d'asta del dettaglio NON deve
  prendere in prestito classi della lampo (`.lampo-resta` vinceva a
  pari specificità e la tingeva d'arancio). UN token per tutto: bottoni
  (`.btn.asta`, stessa forma dell'orange), chip del foglio, badge e
  cornice in card, riga/countdown del dettaglio, TARGHETTA prezzo in
  card (quel numero è la puntata in corso, non un prezzo). Il RECINTO
  resta VERDE anche sull'asta (il verde è della protezione, non
  dell'acquisto): dentro, il bottone è blu. I bottoni del foglio
  puntata sono rettangolari COME Acquista per selettore condiviso
  (`#detailContent .btn,#puntaSheet .btn` — un solo cuore, mai una
  copia).
  LA RADICE «🔨 ASTE» ESISTE (ago 2026): il martelletto SVG
  monocromatico (mano di tagliaSVG, inchiostro in [2,22], si accende
  in arancio con currentColor come le sorelle) prende lo SLOT VUOTO
  della nav SOLO a leva accesa — `aggiornaAstaVisibilita` lo scambia
  con lo spaziatore, gli slot restano cinque e il Vendi al centro
  esatto. NON è una seconda vetrina (il patto di Sfoglia): `vaiAste`
  accende ramoVetrina='aste' + filtro + ordinamento «scade prima»
  sulla vetrina UNA; `voceNav` e la entry di navigazione conoscono il
  ramo; `vaiEsplora` uscendo dal ramo spegne ANCHE filtro e
  ordinamento che il tab aveva acceso lui (o Esplora mentirebbe).
  Stato vuoto suo («Nessuna asta in corso», CTA verso Vendi).
  IMPERFEZIONE DICHIARATA: in vetrina anonima /api/me non c'è e il
  tasto resta nascosto — per mostrarlo agli anonimi servirebbe la
  leva nella busta di prima pagina (un tocco a server.py, non fatto
  di proposito: si decide con Andrea).
  FUSIONE con la REGOLA DELLA LAPIDE (Andrea, in revisione — il
  travaso cieco era un doppio conteggio): nelle collisioni
  stessa-asta si sommano SOLO le puntate ATTIVE (i sats di una
  ritirata sono GIÀ al registro) e il superstite gareggia con TUTTO
  il versato (offerto = somma: una persona, una cassaforte,
  versato==offerto sempre vero); l'auto-puntata post-fusione va nel
  registro, mai cancellata (ci sono sats dentro).
  LEVE (config, try/except): ASTA_ABILITATA nasce FALSE come
  IMPORT_NOSTR_APERTO (muove denaro in uscita: si accende dal VPS con
  un gesto, guardando il primo giro; spenta blocca creazione e
  puntate NUOVE, mai chiusure/ritiri/riscossioni),
  ASTA_DURATE_GIORNI [1,3,7,14,30] (nel form pillole compatte
  «24h·3g·7g·14g·30g» con 7 PRESELEZIONATO; tutto passa dall'elenco —
  validazione, avviso 1h, proroghe — mai un 3/7 assunto altrove, e la
  guardia fuori-elenco=400 ha la sua prova pura), ASTA_INCREMENTO_PERCENTO 5,
  ASTA_PROROGA_MINUTI 10, ASTA_MAX_ATTIVE_VENDITORE 3. Superficie:
  asta_base/scadenza in CAMPI_VETRINA + top e conteggio da
  arricchisci_righe_vetrina (offerenti MAI nominati), `asta_leve` e
  `aste_da_agire` in /api/me, `GET /api/aste/{id}` (cronologia
  anonima + mia posizione + strade), `GET /api/me/puntate` (sezione
  «🔨 Le tue puntate» + «Da riscuotere» negli Ordini), foglio
  #puntaSheet col conto «versi adesso: la differenza», barra «🔨
  Punta», toggle «Vendi all'asta» in Vendi (visibile solo a leva
  accesa). Lo SLOT VUOTO della nav resta destinato alla futura radice
  «🔨 Aste» (solo frontend su solo_asta+ordina=asta, pattern Sfoglia).
  STRADE SCARTATE, coi perché (non riproporle senza un motivo nuovo):
  rimborso immediato a ogni sorpasso (ucciderebbe il rilancio a
  differenza e moltiplicherebbe le transazioni); rimborso a tempo
  dopo N ore da superato (timer coi casi limite, rischia di
  rimborsare chi stava per rilanciare: il ritiro volontario ottiene
  lo stesso con la scelta in mano all'utente); tetto di 3 rilanci a
  testa (soffoca il rilancio a un tap e abbassa il prezzo finale — il
  freno naturale è il prezzo; leva aggiungibile a posteriori);
  rientro da zero dopo il ritiro (il definitivo mette un tetto per
  costruzione ai rimborsi e rende il gesto inequivocabile); fee di
  prelievo sull'uscita, es. 1% (la cassaforte restituisce sempre
  intero: far pagare l'uscita scoraggia le puntate, il costo vero è
  solo il routing); aste multi-pezzo e Compralo subito (fuori dalla
  v1).
  Quantità in stock (lug 2026, il mattone del futuro «set»): colonne
  `annunci.quantita` (pezzi disponibili ADESSO, default 1: gli storici
  restano un pezzo solo) e `ordini.quantita`. INVARIANTE: venduto <=>
  quantita=0 — l'esaurito RIUSA lo stato 'venduto', zero stati nuovi
  (filtri vetrina, decadenza offerte, anti-resurrezione dell'import e
  preferiti «non più disponibile» valgono gratis); riallineamento
  idempotente a ogni avvio in init_db. PRENOTAZIONE derivata, niente
  contatore: riservati = SUM(quantita) degli ordini 'creato' freschi
  (<30 min, la soglia del reaper, che copre la vita della invoice: 15)
  via `_riservati` + `idx_ordini_annuncio` (il primo indice su ordini);
  compra() fa il fail-fast di cortesia prima delle await e il
  ricontrollo COMPLETO (stato+quantita+SUM) DOPO crea_invoice_escrow
  senza await fino all'INSERT — chiude il buco storico del doppio
  acquisto (prima N invoice vive sullo stesso annuncio si potevano
  pagare TUTTE); VINCOLO: in compra() niente DML prima del ricontrollo
  (una transazione aperta congelerebbe la lettura). Il conto lavora
  sull'UNITARIO (offerte e lampo parlano il prezzo del singolo pezzo;
  per l'EUR si arrotonda l'unitario PRIMA di moltiplicare, così la
  divisione a ritroso di chi legge l'ordine è esatta) e moltiplica
  alla fine: spedizione UNA volta sola, protezione e
  TETTO_DIGITALE_NUOVI sull'articolo TOTALE, drift TETTO_SATS_ANNUNCIO
  sull'unitario (tre pezzi regolari non devono dare 409).
  `ordini.prezzo_sats` resta il TOTALE in cassaforte; l'unitario si
  deriva: (prezzo_sats − spedizione_sats − protezione_sats)/quantita.
  verifica_pagamento scala con MAX(quantita-?,0) nel ramo vincente del
  CAS; SOLO all'esaurimento partono stato venduto, nostr sold, ✅ sul
  canale e la decadenza delle ALTRE offerte — ATTENZIONE: quel blocco
  vive DENTRO il ramo esaurito, la vendita parziale lascia le
  trattative altrui VIVE e la notifica dice i pezzi rimasti. Il
  rimborso somma i pezzi dell'ordine (incremento RELATIVO) e riattiva
  come sempre. RICARICA: `POST /api/listings/{id}/quantita`
  (scrittura ASSOLUTA: quanti pezzi ho ORA; solo proprietario, stato
  attivo/venduto, mai importati né revisione, mai sotto i riservati) —
  NON aspetta gli affari in corso, a differenza della modifica: tocca
  solo il numero, e il negozio col miele sempre in spedizione deve
  poter ricaricare; l'esaurito riattivato rifà nostr active e toglie
  la spunta dal canale, niente promo/match (ricaricare non è
  pubblicare). `/api/listings/miei` porta anche i venduti: riga spenta
  «Venduto» + «↻ Rimetti in vendita» (`ricaricaAnnuncio`, prompt), il
  relist onesto anche per chi vendeva un pezzo solo. Giudici:
  `quantita_da_payload` (assente = default/conserva lo stock in
  modifica; oltre `MAX_QUANTITA_ANNUNCIO` — leva config, **999999**
  dal lug 2026: quanti pezzi ha in magazzino lo sa il venditore, non
  noi, e cento diceva «non ti credo» a chi ne ha davvero tanti. Quel
  che resta è un guardrail contro il numero incollato per sbaglio,
  non un giudizio sul negozio — e vale anche su ciò che arriva dai
  relay. ATTENZIONE: una riga esplicita nel config del VPS vince sul
  default. Coi numeri grandi non si rompe nulla — colonna INTEGER,
  conti interi Python — ma ogni posto che mostra una quantità passa da
  `fmt()`, o «999999 disponibili» diventa un muro di cifre) = 400
  e `quantita_tollerante` per il CSV (vuota o storta = 1, oltre il
  tetto si lima, mai uno scarto); colonna facoltativa `quantita` nel
  modello CSV con la riga del miele. Superficie: `a.quantita` in
  CAMPI_VETRINA (pubblica per natura), riga «— disponibili: N» nel
  content NIP-99 solo se N>1 (verificato: la spec non ha un tag stock;
  `evento_annuncio_importato` resta pulito e gli importati restano
  quantita=1 per sempre), «ne restano N» nel catalogo della ricerca
  AI. OFFERTE = prezzo UNITARIO (deciso da Andrea): minimo 50% e
  contro invariati sul listino unitario, al pagamento pattuito ×
  quantità scelta, e il confirm di accettazione del venditore lo
  dichiara («la cifra vale AL PEZZO»); con la lampo vince il minimo
  sull'unitario come sempre. Frontend: campo «Quantità disponibile»
  sempre visibile in Vendi (vuoto = 1, `qtaForm`; nascosto nella
  modifica firmata), pillola «N disponibili» + stepper `.qta-riga`
  nell'escrow-zone — la scelta sta PRIMA di startBuy, il patto del
  varco: la invoice nasce lì — con `qtaScelta` azzerata a 1 in
  openDetail; totaleStima/cifraVia × pezzi, cifre riscritte in-place
  da `aggiornaCifreCompra` (estratta da setConsegnaScelta), barra con
  «× N», conto scomposto «Articolo × N» (compare anche senza
  spedizione/protezione quando i pezzi sono >1), ordini con «N pezzi ×
  unitario», demo col Bitcoin Standard in 3 copie. Corner dichiarato:
  un ordine pagato ma verificato oltre i 30 minuti può superare lo
  stock (il MAX para il negativo, il doppio-escrow resta caso da
  moderatore — com'era il doppio acquisto di ieri, ma molto più raro).
  Il SET «Riempi il barattolo» (lug 2026): più annunci DIVERSI dello
  stesso venditore in UN ordine solo — una invoice escrow, UNA
  spedizione, un tracking, una conferma. Modello «testata + righe»,
  MAI padre+figli (gonfierebbe distintivi e rischierebbe doppi
  sblocchi sullo stesso escrow): la testata resta in `ordini`
  (`annuncio_id=0` e `quantita` = somma dei pezzi), la merce vive in
  `ordine_righe(ordine_id, annuncio_id, quantita, unitario_sats,
  titolo)` — unitario GIÀ scontato (lampo/accordo, invariante:
  articolo = Σ unitario×qta, il futuro sconto-set sarà una voce di
  TESTATA sottratta dal totale, deciso e preparato), titolo
  FOTOGRAFATO all'acquisto (i tre JOIN caldi — /api/orders, CSV,
  sollecita_incassi — sono diventati LEFT: con l'INNER un set
  sparirebbe dalla lista, pagato e invisibile). I MONO non hanno
  righe MAI: le sintetizza `_righe_ordine` dalla testata, e ogni
  punto che cicla sugli oggetti dell'ordine passa da lì
  (`_titolo_ordine` = «primo pezzo + N altri»). Guardie:
  `_ordini_vivi_annuncio` è il giudice unico delle 5 guardie «affare
  in corso» (testata O riga), `_riservati` somma due query (la
  seconda sulle righe via idx_righe_annuncio: l'indice caldo non si
  tocca), rimozione/spegni_annuncio annullano anche i set 'creato'
  col pezzo dentro, reaper e annulla_ordine cancellano le righe
  (niente FK cascade: PRAGMA foreign_keys mai acceso).
  compra() col body `{righe:[{annuncio_id, quantita, offerta_id}]}`
  passa da `_compra_set` (2..MAX_RIGHE_SET, leva config, 8): stesso
  venditore E stessa ORIGINE (lug 2026, dopo l'anello: `venditore_id`
  dice a chi vanno i sats ma non da dove arriva la merce, e un account
  che raccogliesse roba di più persone passerebbe con un id solo —
  l'origine è `contatto_nostr`, '' = nato qui, altrimenti la chiave
  che l'ha firmato. ONESTÀ: NON avrebbe fermato il fantasma, che aveva
  una chiave sola per tutte le copie; a quello risponde il tappo, e
  questa è la cintura se un giorno il tappo salta),
  strade = INTERSEZIONE delle FISICHE (spedizione/ritiro;
  il digitale ha la colonna unica del contenuto e le finestre corte,
  gli annunci con consegna '' non dichiarano un costo: entrambi «si
  comprano da soli», 400 col nome del pezzo), lampo e offerte
  accettate PER RIGA sull'unitario, cambio UNO prima della invoice,
  SPEDIZIONE = MAX dei costi dichiarati (il pacco è uno; compromesso
  dichiarato del v1: 3 «medi» possono fare un «grande» e il
  venditore rimette la differenza — mitigato dalla stima mostrata
  prima di spedire; il tariffario per-taglia è la leva futura),
  protezione sull'articolo totale, ricontrollo post-invoice su OGNI
  riga nel blocco senza await e 409 che NOMINA il pezzo soffiato.
  verifica_pagamento scala/esaurisce/decade RIGA per riga (la
  vendita di un pezzo non spegne le trattative sugli altri; nostr
  sold e ✅ canale per annuncio esaurito); il rimborso resta
  INTEGRALE e riattiva TUTTI gli annunci del set. PER TESTATA (tutto
  o niente, dichiarato): disputa/reso, feedback (uno per parte),
  tracking, distintivi e contatori (1 set = 1 vendita/1 acquisto),
  una riga di CSV. STIMA TAGLIA: `PUNTI_TAGLIA` (busta 1, piccolo 3,
  medio 8, grande 18) + `stima_taglia_set` — somma×qta a soglie
  tarate perché un pezzo solo ricada nella SUA taglia, ingombrante =
  sempre ingombrante, taglia mancante = stima '' (mai una bugia);
  SOLO informativa (risposta di compra, /api/orders — letta fresca
  dagli annunci —, messaggio al venditore «verifica tu prima di
  spedire»), non prezza nulla. /api/orders: i set escono con
  `righe`, `taglia_stimata` e titolo sintetizzato; i mono non
  portano la chiave (client vecchio in cache: titolo e totali di
  sempre, il suo «N pezzi × unitario» mostrerebbe una media — per
  questo il client nuovo lo spegne sui set e mostra l'ELENCO).
  Frontend: `sezioneAltriOggetti` in coda a openDetail (striscia
  `.altri-strip` di card dal negozio limit 7, inCatalogo
  obbligatorio, guard anti-race, fail-open) + bottone «📦 Riempi il
  pacco» (lug 2026: la frase lunga «Compra più oggetti in un pacco
  solo» andava a capo a 360px) — MAI il 🫙 nell'etichetta: il
  barattolo è dei preferiti, e il nome del cantiere vive solo nel
  titolo del foglio `#setSheet` (registrato in closeSheet), che dice
  «🫙 Riempi il barattolo — un pacco, una spedizione». Il bottone
  porta l'ACCENTO CARTONE: classe `.btn.carton`, token `--carton`
  (#9A6234 di giorno, #C79A72 di sera — di notte si SCHIARISCE, che
  un marrone scuro affonderebbe nel fondo bruno dell'app; contrasti
  5,04 e 5,99, AA in entrambi) su contorno, testo e ombra, con fondo
  NEUTRO: resta un secondario, l'unico pieno del dettaglio è
  Acquista. La variante a sfondo pieno è stata provata e scartata in
  tutti e due i temi — diventava un blocco che gridava quanto il CTA.
  L'emoji 📦 è già di quel colore per conto suo: nessun glifo si può
  tingere. Composizione:
  `setScelte` Map id→qta (parte dal pezzo aperto), righe con spunta
  e stepper (i SELEZIONABILI prima: il tetto delle 8 righe non
  taglia mai un compatibile per mostrare uno spento), righe spente
  col motivo scritto, pillole consegna su `stradeSet()`
  (intersezione), `totaleSet()` con la matematica di totaleStima
  (artStima per riga × qta + MAX spedizioni + protezione),
  `stimaTagliaSet` gemello client (il giudice resta il server),
  `setCirca()` per il ≈. `startBuySet`/`confermaSetSubito` = gemelli
  di startBuy/NWC: stesso paySheet e stesso pollTimer (chiusure
  MIRATE, mai closeSheet col poll vivo), body a righe con
  offertaAccettataPer per riga; sul 409/404 `rinfrescaSet` rilegge
  il negozio (limit 100), spegne localmente gli spariti, pota
  selezione e quantità e riapre il foglio: l'utente vede il buco,
  non un vicolo cieco (il pezzo solo RISERVATO resta selezionabile:
  il fail-fast lo ridirà, dichiarato). Ordine: elenco «titolo × qta
  — sats» al posto della media, venditore con «📦 Spedisci il set
  (un pacco solo)» + taglia stimata. In DEMO il set non esiste
  (toast), in VETRINA apre l'invito. Gli importati da Nostr restano
  fuori dai set per costruzione (consegna '').
  Doppia valuta (lug 2026): il venditore sceglie la valuta del listino
  in Vendi — colonne `annunci.valuta` ('sats' default: zero impatti
  sugli annunci esistenti) e `annunci.prezzo_eur`. Per i listini EUR
  `prezzo_sats` resta l'EQUIVALENTE al cambio di pubblicazione (serve
  al tetto, alla ricerca AI e come ripiego display). Il pagamento è
  SEMPRE in sats: `compra()` converte al cambio corrente alla
  creazione della invoice (la vita della invoice, 15 min, È il lock
  del prezzo: scaduta, si riconverte; 503 se il cambio non è mai
  arrivato) e salva `ordini.prezzo_sats` = sats effettivi +
  `ordini.cambio_ordine` = cambio usato (colonna nuova: `cambio_eur`
  mantiene la semantica di CHIUSURA e il CSV non cambia). La risposta
  di POST /api/orders ora include `prezzo_sats`. `prezzo_da_payload`
  è il giudice unico di pubblica/modifica: valida, converte e applica
  `TETTO_SATS_ANNUNCIO` — leva SPENTA di serie (default 0 = nessun
  limite; si accende dal config, es. 100_000; NON copre
  importa_nostr.py che scrive dritto nel DB); la modifica
  scrive SEMPRE valuta+prezzo_eur (eur→sats azzera l'euro). Drift del
  cambio tra pubblicazione e acquisto: tolleranza +20% alla creazione
  della invoice, oltre 409 + notifica al venditore (che si ripara
  ri-salvando il prezzo: la modifica riconvalida al cambio di oggi).
  NIP-99: tag `price` nella valuta del listino (es.
  ["price","40.00","EUR"]) e content coerente — importa_nostr sa già
  rileggere quel formato. Ricerca AI: la riga di catalogo porta
  entrambe le valute. Frontend: toggle ₿/€ nella searchbar di
  Esplora e — dal lug 2026 — un gemello nella riga del prezzo del
  DETTAGLIO (`valutaVista` in localStorage['barattolo_valuta'], una
  sola preferenza per tutti e due),
  `prezzoParte(l)` rende la valuta dello spettatore grande e l'altra
  piccola sotto — il «≈» sta SEMPRE e solo sul prezzo convertito, mai
  sul listino. L'unità non porta più uno spazio nel markup: l'aria la
  dà `.unit{margin-left:4px}`, e il SIMBOLO € (`.unit.eur`) sta più
  stretto e nel dettaglio quasi grande quanto la cifra — un simbolo
  di valuta appartiene al numero, la parola «sats» no (feedback di
  Andrea: il € pareva una nota a piè di pagina). Le migliaia si
  separano con lo spazio stretto unificatore U+202F in `fmt`
  (l'escape, mai il carattere: nel sorgente sarebbe invisibile): con
  lo spazio normale il mono di casa spezzava «905 000» in due blocchi
  lontani, e questo per giunta non va mai a capo a metà numero.
  `cambioVivo` + re-render della griglia all'arrivo del
  cambio CoinGecko; form Vendi col suffisso-bottone sats/€
  (`sellValuta`, virgola decimale tradotta); paySheet e conferma NWC
  mostrano la stima «≈» e poi i sats VERI da `prezzo_sats` della
  risposta di POST /orders (MAI da `l.price`, che per i listini EUR
  è solo l'equivalente di pubblicazione).
  IL GESTO INDIETRO (lug 2026): il tasto indietro di Android, lo swipe
  dal bordo e il tasto del browser tornano indietro di un passo invece
  di chiudere l'app — prima chiudono i fogli aperti, poi smontano le
  viste; si esce solo dalla RADICE. La freccia ← e la tab bar restano
  tutte: il gesto si aggiunge. Blocco `nav*` subito dopo `go()`, acceso
  da `navMotore()` una riga prima di `avvia()` (prima non si può: le
  variabili degli strati sono dichiarate più in basso e sarebbero in
  zona morta). Tre scelte da NON rovesciare:
  1) l'URL non si tocca MAI (`pushState` con `location.href`) — il
  server serve solo rotte esplicite (regola 3), un `/profilo` inventato
  darebbe 404 al reload, e le costanti deep-link `NEGOZIO_URL`/
  `ANNUNCIO_URL` si leggono una volta al parse;
  2) l'ascoltatore è DICHIARATIVO: `popstate` non dice «indietro», dice
  «il cursore si è spostato» — si sposta anche in AVANTI e può saltare
  più entry insieme (i browser marcano saltabili quelle spinte fuori da
  un gesto: il deep link dopo l'await, `openOrder` nel setTimeout del
  pagamento, il tour che parte da solo). `navApplica` RI-APPLICA la
  pila scritta nella entry (`history.state.pila`), non «toglie un
  livello»: degrada, non si rompe. Per la stessa ragione niente
  `history.go(-n)` con un contatore di debito — asincrono e coalescente,
  la fabbrica dei bug irriproducibili: le chiusure programmatiche usano
  `replaceState`, che è sincrono;
  3) la pila si DERIVA dal DOM (`navPila`: la vista in fondo, sopra gli
  strati per z-index — fogli, lightbox, tour, cartello; il picker
  forzato ultimo fra i fogli, è l'unico che si apre SOPRA un altro) e a
  rilevarla è un `MutationObserver` sulle classi. È ciò che tiene il
  diff piccolo: i 18 siti che aprono un foglio, `closeSheet()` e le tre
  chiusure mirate anti-`pollTimer` sono rimasti INTONSI. Il callback è
  un microtask (ancora dentro il task del gesto, e coalesce i cambi
  dello stesso giro: per questo foglio→foglio — setSheet→paySheet — è a
  saldo zero da solo).
  Si SPINGE solo entrando in una vista più interna (dettaglio, negozio,
  ordine, sicurezza); i quattro tab sono RADICI sorelle e si
  SOSTITUISCONO (girarli non costa quattro indietro, e dalla radice il
  gesto esce). `navChiudiStrato` chiude sempre con la funzione dedicata,
  MAI `closeSheet()`: il `pollTimer` si ferma solo col `paySheet`, che è
  più preciso di prima. `navRendiVista` ricostruisce col suo opener
  (`openDetail`/`openOrder`/`apriNegozio`) e controlla PRIMA che la
  vista non si sia svuotata — `openOrder` non ha guardie e ci morirebbe
  dentro: è il ripiego che prima era scritto due volte (in
  `tornaDaSicurezza` e nella ri-idratazione di `avvia()`) e ora vive in
  un posto solo. `navRiflette()` è richiamata a mano SOLO in coda a
  `openDetail`: dettaglio→dettaglio (le card della striscia «Altri
  oggetti») non cambia nessuna classe e l'osservatore non la vedrebbe.
  Ogni affordance di ritorno passa da `navIndietro()` = `history.back()`
  (le due «← Torna», il «← I tuoi ordini», la freccia sulla foto, ✕ e
  Annulla dei fogli, tocco sul velo, i tre Escape, «Salta» del tour):
  UNO SOLO smonta i livelli — l'ascoltatore di popstate — così gesto e
  freccia non possono divergere, e non restano gradini morti (un
  indietro che non fa niente). Per questo sono spariti `sicurezzaRitorno`
  e l'euristica di `tornaDalNegozio` su `currentListing`: la cronologia
  sa da dove si veniva meglio di loro. Restano programmatiche le
  chiusure che non sono un gesto (`closeSheet` dopo il pagamento, il
  foglio invito che lascia il posto a quello Nostr, `simulatePaid`).
  DALLA RADICE SI ESCE, E USCIRE VA DETTO (lug 2026, da un bug vero
  visto da Andrea sullo swipe da Sfoglia): `navIndietro` faceva
  `history.back()` alla CIECA, e dentro Telegram — come nella PWA
  installata — la nostra pagina è la PRIMA della sessione, quindi
  «indietro» non ha dove andare e il gesto moriva in silenzio, lo
  schermo fermo dov'era. Vale per OGNI radice; si notava su Sfoglia
  perché è quella da cui uno si aspetta un passo. Ora il gradino su cui
  si sta lo dice la cronologia stessa: `d` nello state (0 = sotto non
  c'è NIENTE di nostro), scritto da `navRiflette` accanto alla pila —
  +1 sul push, invariato sul replace — e seminato a 0 da `navMotore`.
  A `d=0` e a strati chiusi decide il patto della RADICE MADRE (sotto);
  su Esplora nuda, dentro Telegram, si chiama `tg.close()`, e fuori
  resta lo `history.back()` di sempre. NIENTE contatori di debito: `d`
  viaggia nella entry, come la pila — è la stessa ragione per cui
  l'ascoltatore è dichiarativo.
  DUE CONTESTI, E VANNO TENUTI DISTINTI (lug 2026, ed è la lezione che
  costa di più in questo cantiere — il primo giro di correzioni era
  scritto per il contesto sbagliato): dentro la **Mini App** il gesto
  lo intercetta il CLIENT Telegram, che ce lo gira come
  `backButtonClicked` solo se il `BackButton` è visibile, altrimenti
  chiude l'app; nella **PWA installata** (e nel browser, e nell'APK,
  cioè dove Andrea prova) non esiste né `tg.BackButton` né
  `tg.close()` né `disableVerticalSwipes`, e il gesto è quello di
  SISTEMA: non passa MAI da `navIndietro`, parla direttamente con la
  cronologia. Conseguenza da tenere sempre presente: quello che la
  PWA fa non si può INTERCETTARE, si può solo PREPARARE — se un passo
  indietro deve esistere, deve esistere come entry, prima che il gesto
  arrivi. Ogni rimedio scritto come «quando arriva il gesto, deviamo»
  funziona solo dentro Telegram.
  ESPLORA È LA RADICE MADRE (`RADICE_MADRE`, lug 2026, decisione di
  Andrea): da Sfoglia, Vendi, Ordini e Profilo l'indietro porta a
  Esplora, e solo da Esplora si esce. Il MECCANISMO è la cronologia,
  non un intercettatore: il PRIMO passo via da Esplora SPINGE
  (`primoPassoViaDaCasa` in `navRiflette`, e solo il primo — `giu===0`),
  così sotto ogni radice figlia c'è la madre e il gesto di sistema la
  trova da sé, in tutti e due i contesti. Da una figlia all'altra si
  sostituisce come sempre: girare tutti i tab costa UN indietro, mai
  uno a testa — il patto delle sorelle regge dove serviva davvero.
  Tornare alla madre col tab è un INDIETRO vero (`vaiEsplora` chiama
  `navIndietro` quando è l'unico gradino), non una sostituzione: sotto
  resterebbe una entry identica, cioè un indietro che non fa niente, e
  il gesto dopo ne chiederebbe due per uscire.
  LA ENTRY DELLA VETRINA DICE RAMO E CATEGORIA (`chiaveVetrina`): era
  l'imperfezione dichiarata «l'avanti dentro un reparto ricostruisce la
  vista ma non il filtro», e con la radice madre diventava una bugia —
  si tornava a Esplora col mercatino intero e la nav accesa su Sfoglia.
  Per tenerla onesta `setCat` chiama `navRiflette` (cambiare categoria
  non tocca nessuna classe, l'osservatore non se ne accorgerebbe), e
  siccome quella chiamata LEGGE-E-AZZERA `navSpingi`, in
  `apriCategoria` la bandierina si alza subito prima del `go()` che la
  usa e non in cima alla funzione — alzata prima se la mangiava quel
  giro, e la discesa nel reparto tornava a essere un cambio di tab.
  MENTRE SI RI-APPLICA UNA ENTRY NON SI SCRIVE (`navApplicando`): il
  giro di ricostruzione chiama `setCat` e `go`, che riflettono a metà
  strada — con la vista vecchia ancora attiva — e leggevano un cambio
  di radice che nessuno aveva chiesto, spingendo un gradino nuovo
  invece di consumarne uno. Si spegne in un `queueMicrotask`, dopo il
  giro dell'osservatore. La ragione che decide: su Subito
  e Vinted funziona esattamente così — la home è la radice madre, dalle
  sezioni l'indietro ci passa, e di lì si chiude. È la convenzione che
  i nostri utenti hanno GIÀ NELLE DITA, e vale più della simmetria fra
  radici sorelle: quella è una proprietà del nostro modello, questa
  un'abitudine di chi lo usa.
  L'ARGOMENTO PERDENTE sta qui perché fra sei mesi si sappia che è una
  scelta e non una svista — per un giorno la regola è stata l'opposta
  («ogni radice esce per conto suo»), e le ragioni erano: le radici
  sono sorelle e non parenti, la discesa su Esplora è una gerarchia che
  la cronologia non registra, e sarebbe la seconda deroga per Sfoglia,
  che ne ha già una (la piastrella è una discesa). Restano vere: hanno
  solo meno peso della convenzione. CONSEGUENZA ACCETTATA (era il caso
  sollevato contro): chi apre l'app dritto su un'altra radice
  all'indietro finisce in Esplora, dove non è mai passato — lo fanno
  anche loro.
  Il patto delle radici SORELLE resta intatto dove riguarda la
  cronologia: fra tab si SOSTITUISCE sempre, girarli tutti non costa un
  indietro a testa, e il passaggio da Esplora non spinge niente
  (`vaiEsplora` è un ritorno a una radice, quindi replaceState, e `d`
  resta 0). Ed è `vaiEsplora` e NON `go('esplora')` perché la madre è
  il mercatino INTERO: senza il ritorno a «Tutto» si atterrerebbe su
  una vetrina ancora filtrata con la nav accesa su Sfoglia, che è
  esattamente la bugia che `ramoVetrina` esiste per non dire.
  Telegram: `navFreccia` mostra il `BackButton` (Bot API 6.1) solo
  quando c'è dove tornare — ed è la STESSA domanda di `navIndietro`,
  quindi un giudice solo, o la freccia e il gesto divergono. Resta
  nascosto SOLO su Esplora nuda (`d=0`, nessuno strato), e lì il gesto
  chiude la Mini App, che È il patto. Sulle altre radici ora si vede,
  ed è OBBLIGATORIO: con la freccia nascosta il gesto lo intercetta il
  client, che chiuderebbe l'app per conto suo, e il passaggio da
  Esplora non avverrebbe mai. E si vede anche a `d>0` su Esplora — una
  categoria aperta da una piastrella è Esplora ma con Sfoglia sotto, e
  lì l'indietro deve riportare allo scaffale. Lo swipe VERTICALE si
  spegne SEMPRE con `disableVerticalSwipes` (7.7), anche alla radice, e
  dal lug 2026: finché restava acceso lì, tirare giù per aggiornare
  trascinava via la Mini App: un gesto che ovunque significa
  «rinfresca» qui significava «vattene», e chi lo faceva lo leggeva
  come un torna-indietro. Ora quel trascinamento è NOSTRO (vedi il
  gesto di aggiornamento). Non si perde nessuna via d'uscita: la
  chrome di Telegram non si tocca mai, lo dice la sua
  documentazione («the user will still be able to minimize and close
  the Mini App by swiping the Mini App's header»). Il tasto di Telegram
  chiama `history.back()` come tutti, con una serratura di 350ms contro
  il doppio canale (certi client potrebbero emettere sia
  `backButtonClicked` sia `popstate`). Deep link `/annuncio/{id}`:
  l'apertura spinge SOPRA la radice, quindi il primo indietro atterra
  sulla vetrina (deciso: un modello solo, e da un annuncio condiviso
  l'indietro fa scoprire il catalogo invece di buttare fuori). La
  semina della radice in `navMotore` serve perché `history.state`
  SOPRAVVIVE ai `location.reload()` del login e racconterebbe cose
  della vecchia identità. Su `file://` (la DEMO a mano) `STORIA` è
  falsa e il motore resta spento: `navIndietro` smonta lo strato in
  cima e, se non ce n'è, torna al mercatino — che è la stessa regola
  della radice madre, detta a mano perché lì la cronologia non c'è.
  IMPERFEZIONI DICHIARATE:
  dopo un pagamento riuscito resta un gradino morto (`closeSheet`
  programmatico sostituisce, non cancella la entry gemella); l'avanti
  del browser su uno strato non lo riapre (lightbox e tour vogliono
  dati che nella entry non ci sono) e ci pensa il `navRiflette`
  successivo a rimettere la entry in pari — sistema auto-guarente; il
  pannello Filtri è fuori di proposito (è in pagina, usa `style.display`
  che l'osservatore delle classi non vede, e non intrappola nessuno).
  IL GESTO DI AGGIORNAMENTO (lug 2026): tirare giù dalla cima rilegge la
  vista e ci RESTA — pastiglia di carta `#ptr` che scende col dito
  (z-index 25: sopra l'header, o dietro sparirebbe; sotto nav, barra
  d'acquisto e fogli — è un segnale, non uno strato). Nasce perché quel
  trascinamento non era di nessuno: dentro Telegram era la presa che
  porta via la Mini App (vedi `disableVerticalSwipes` qui sopra), nel
  browser il ricarica nativo — che già non parte, `overscroll-behavior:
  none` sul body c'è da sempre, e comunque ripartirebbe da Esplora
  perdendo dov'eri. `aggiornaVista` rilegge la vetrina da sé; Ordini e
  Profilo li ricarica `go()`, che quelle viste le sa già caricare — un
  secondo posto che elenca i loro render divergerebbe al primo cassetto
  nuovo. Mezzo secondo minimo di pastiglia che gira, o su rete veloce
  lampeggerebbe e sembrerebbe non essere successo niente; fail-open.
  UN touchmove SU TUTTA LA PAGINA È UN ASCOLTATORE INVADENTE, quindi è
  timido PER COSTRUZIONE, e sono i tre recinti da non togliere:
  1) solo dalla CIMA (`scrollY<=0`) e a STRATI CHIUSI — lo dice
  `navPila().length===1`, nessuna seconda lista da tenere allineata;
  2) solo sulle viste che hanno davvero qualcosa da rileggere
  (`VISTE_PTR`: esplora, affari, profilo). Così la GALLERIA a
  scroll-snap del dettaglio resta fuori dal gesto senza doverla
  nominare — lì la foto è in cima, quindi `scrollY` è 0 e una diagonale
  avrebbe armato una tirata che poi non ricaricava niente: mezzo
  secondo di pastiglia per nulla. Chi aggiunge una vista ad
  `aggiornaVista` deve aggiungerla anche a `VISTE_PTR`, o il gesto gira
  a vuoto proprio dove lo si chiede;
  3) il gesto dev'essere VERTICALE: appena `dx > dy` la tirata si
  annulla e non torna fino al tocco dopo — è il recinto delle strisce
  che scorrono di fianco dentro le viste ammesse (pillole delle
  categorie, «Altri oggetti»).
  IL touchmove È NON-PASSIVO, MA SOLO MENTRE LA TIRATA È ARMATA (lug
  2026, dalla PWA di Andrea): un ascoltatore passivo non può chiamare
  `preventDefault`, quindi non poteva togliere di mezzo il
  pull-to-refresh NATIVO di Chrome — che ricaricava la pagina, e
  ricaricando si riparte da Esplora: il gesto sembrava un
  torna-indietro proprio mentre si chiedeva un aggiornamento. Si
  appende nel `touchstart` quando `ptrPuo()` dice di sì e si stacca al
  rilascio, così per tutto il resto dello scorrimento la strada veloce
  del compositor resta intatta — è la ragione per cui non ce n'è uno
  permanente. `overscroll-behavior` sull'html lo spegne comunque (vedi
  sotto), ma a decidere dev'essere il nostro gesto, non una proprietà
  che un domani qualcuno rimette ad `auto`.
  `OVERSCROLL-BEHAVIOR VA SULL'HTML`, non solo sul body: alla viewport
  arriva il valore dell'ELEMENTO RADICE, e finché l'html restava `auto`
  quel `none` sul body (che c'era da sempre) non spegneva NIENTE.
  Costava due bug insieme, e vale per i due assi: il pull-to-refresh
  nativo qui sopra, e l'incatenamento ORIZZONTALE della galleria a foto
  singola (vedi il dettaglio annuncio).
  Reduced-motion spegne transizione e giro. Il dettaglio NON si
  aggiorna di proposito: riaprirlo da capo azzererebbe pezzi scelti e
  strada di consegna, e non è quello che chiede un dito che tira giù.
  Cinque modalità, decise in `avvia()`: app vera dentro Telegram (auth
  via initData); WEB dal browser (cookie di sessione, app completa:
  `authHdr()` manda header vuoto e comanda il cookie; il sondaggio
  cookie viene PRIMA di quello collaudo); collaudo locale (identità
  finte + bottone "cookie web" per provare il login web senza widget);
  VETRINA pubblica in sola lettura dal browser (annunci veri, banner
  col widget "Entra con Telegram" — `data-request-access=write` chiede
  il permesso per gli avvisi — e ogni azione apre l'invito verso
  @ilbarattolobot, che dal lug 2026 offre anche la porta «🟣 …o entra
  con Nostr»: chi arriva dal link di un DM entra con la sua chiave e
  il reload riapre /annuncio/{id} autenticato, azione a un tocco);
  demo coi dati finti come riserva se il backend tace.
  Login Nostr nel foglio `#nostrSheet` (bottone 🟣 in vetrina e nella
  barra collaudo — a differenza del widget Telegram funziona anche in
  locale): astrazione `firmatario = {pubkey, firma}` con tre fabbriche
  — estensione NIP-07 (zero librerie), bunker NIP-46 (client fatto in
  casa coi mattoni del bundle: richieste kind-24133 cifrate NIP-44 su
  relay, `auth_url` in popup), nsec incollata che firma SOLO in pagina
  (chiave nella closure, azzerata dopo la firma: mai inviata, mai
  salvata, UI che la sconsiglia). Il bundle si carica pigro da
  `/vendor/nostr.js` solo per bunker/nsec. `barraWeb` con avviso
  onesto per chi entra da Nostr (che indica «Collega Telegram» nel
  Profilo); foglio `#collegaSheet` per la proposta di collegamento.
  Blocco «Le tue identità» nel Profilo (`renderIdentita()`, dati già in
  `/api/me`): riga Telegram (nome+username, o «Collega Telegram» per
  i tg_id negativi → `collegaTelegram()` apre il deep-link col codice,
  mai mostrato in chiaro) e riga Nostr (npub nei 4 stati: assente /
  da verificare / verificata con «Abilita l'accesso» / 🔑 attiva con
  «Disabilita» solo su tg_id positivi).
  Onboarding contestuale (lug 2026): niente wizard iniziale, righe
  `.hintline` che compaiono al momento del bisogno e SOLO se la
  funzione manca davvero; «Non ora» le spegne per sempre in
  `localStorage['barattolo_hint']` = {id: timestamp} (frontend puro,
  zero colonne DB: il dismiss del wallet NWC DEVE essere
  per-dispositivo perché il wallet stesso vive in localStorage), e
  con `hintAttivi()` (=!DEMO && !VETRINA) non esistono in demo e
  vetrina. Tre hint-evento: `nwc` nel paySheet (in fondo, sotto
  Annulla — il percorso di pagamento non si allunga; nel ripiego
  Compra subito la riga resta vuota: lì il wallet c'è), `lnaddr` e
  `npubverifica` sulla scheda dell'annuncio appena pubblicato
  (passamano `hintPubblicazione={id,annuncio}` consumato da
  `openDetail` solo su QUEL annuncio; max UN hint per evento,
  precedenza agli incassi). Il CTA positivo NON dismette (se
  l'azione si completa la condizione cade da sola) e porta al
  Profilo col cassetto giusto aperto (`apriCassettoProfilo`). Più
  la checklist «Completa il profilo (N di M)» sotto la testata del
  Profilo (`renderChecklist`, `#profiloChecklist`): M dinamico
  (ln_address, npub verificata, wallet NWC «su questo dispositivo»,
  + Telegram per i tg_id negativi), niente dismiss, a profilo
  completo sparisce del tutto.
  Tour di benvenuto (lug 2026, ha SOSTITUITO la riga one-shot
  `hintBenvenuto`): quattro tappe col riflettore alla PRIMA visita
  autenticata (mai DEMO/VETRINA), zero librerie. Meccanica: velo
  `#tour` (z-index 80, sopra lightbox 70; cattura ogni tocco e blocca
  wheel/touchmove) + riflettore `#tourLuce` (il buio è la SUA ombra:
  `box-shadow 0 0 0 9999px` — ritaglio con angoli morbidi gratis,
  passaggio di tappa = transition su top/left/width/height, classe
  `.tondo` per barattolino e tappo, anello `outline` arancio) +
  fumetto `#tourFumetto` sui token (dark gratis), sotto il bersaglio
  se c'è posto, sopra altrimenti, clampato ai bordi. Tappe
  (`TAPPE_TOUR`: `trova()` + testo): prima `.card` della griglia →
  primo `.card-jar` (NON per forza sulla prima card) → `.trust-line`
  di Esplora (il deposito di garanzia, con «(escrow)» da prima
  spiegazione) → `.avatar-btn.on` visibile (istanza header su mobile,
  topbar da desktop, filtro `offsetParent`). Le tappe si fotografano
  all'avvio (`tourTappe`): bersaglio assente = la tappa non entra nel
  giro (contatore «N di M» onesto), NESSUNA tappa viva (vista
  sbagliata, vetrina vuota) = non parte e NON consuma. Si consuma in
  `barattolo_hint.tour` APPENA parte (one-shot vero: Salta/Escape
  chiudono e basta); parte in `avvia()` dopo renderGrid, precedenza
  sul banner installa PWA (`tourInCorso` al posto del vecchio
  `benvenutoInVista`; alla chiusura si richiama `bannerInstallaPwa()`
  che riottiene la sua occasione nella stessa visita).
  Reduced-motion: niente transizioni né smooth scroll (`tourRidotto`).
  ATTENZIONE ai rAF: `posizionaTour()` va chiamata anche in SINCRONO
  (pagina in secondo piano = rAF fermi, il tour deve trovarsi
  posizionato comunque); classe `.subito` sul primo posizionamento
  per non far scivolare il riflettore dall'angolo. La checklist si
  apre da sola alla PRIMA visita del Profilo con profilo incompleto
  (`checklistvista` in barattolo_hint + `checklistPrimoSguardo` per
  pagina; a profilo completo la prima visita NON si consuma), dalla
  seconda torna chiusa com'era. Collaudo dal vivo: bottone admin
  «🧽 Trattami da nuovo» in fondo alle statistiche
  (`trattamiDaNuovo()`) — azzera barattolo_hint, va su Esplora (il
  tour vive lì) e riarma tour e checklist SUL DISPOSITIVO: gli hint
  sono localStorage puro, il server non c'entra (per questo non è un
  comando bot) e annunci/ordini/profilo non si toccano (azzera anche
  `barattolo_test`, la memoria del cartello qui sotto).
  Cartello «fase di test» (lug 2026): l'avviso di rodaggio
  all'apertura — modale a tutto schermo col velo SFOCATO
  (`#testModale`, z-index 90: sopra i fogli e sopra il tour), si
  chiude col bottone, con la ✕ o col GESTO INDIETRO — mai col tocco
  fuori né con Escape: deve essere letto, ma non si può fingere che
  l'indietro non esista (lug 2026, deciso con Andrea quando è nato il
  motore di navigazione: su Android un indietro che non fa niente si
  preme tre volte e la terza esce comunque dall'app, e alla prima
  apertura il cartello sta sulla RADICE, dove dentro Telegram il gesto
  chiude la Mini App e non c'è modo di intercettarlo — una regola
  onesta batte una garanzia che non c'è). Interruttore, testo e link vivono nel
  CONFIG (`BANNER_TEST`, `BANNER_TEST_TESTO`, `BANNER_TEST_LINK`) e
  arrivano al client da `GET /api/banner-test`, endpoint PUBBLICO come
  /api/listings (lo legge anche l'anonimo in vetrina; spento o testo
  vuoto = `{attivo:false}` e non si disegna nulla): a rodaggio finito
  basta un False nel config del VPS, senza cantieri. La PRIMA riga del
  testo è il titolo, il resto il messaggio (`white-space:pre-line` e
  `textContent` puro: nessun innerHTML sul testo); il bottone del
  canale compare solo con un link http(s) — la stringa vive in
  `linkCanaleTest`, mai dentro un onclick — e dentro Telegram passa da
  `tg.openTelegramLink`. Frequenza: UNA VOLTA AL GIORNO per
  dispositivo (`localStorage['barattolo_test']` = giorno LOCALE,
  consumato alla comparsa come il tour: i tester aprono l'app di
  continuo), mai in DEMO, sempre in vetrina anonima. PRECEDENZA:
  `modaleTest(dopo)` prende in carico ciò che veniva dopo — alla
  chiusura partono tour e banner installa, e `testModaleInCorso` è
  nelle guardie di `bannerInstallaPwa()`; server muto o interruttore
  spento = il giorno NON si consuma e il seguito parte comunque.
  Il cartello passa una volta al giorno, ma la porta al canale resta:
  fascia `#fasciaTest` sotto la trust-line di Esplora
  (`renderFasciaTest`, chiamata da `modaleTest`) — «🚧 Barattolo è in
  fase di test — 💬 Dicci la tua ›», stesso interruttore e stesso
  link, anche per gli anonimi, mai in DEMO, e senza link nel config
  resta un `<div>` che non finge di essere toccabile. Volutamente NON
  un CTA pieno: fondo `--sats-soft` col bordo ₿ da 1.5px e testo
  `--sats-text` (token, quindi chiaro e scuro gratis), niente ombra
  piena — l'arancione pieno resta del «+ Vendi» e dei bottoni
  d'acquisto, che non devono avere rivali. La risposta del server la
  legge `caricaBannerTest()` UNA volta per apertura e la tengono in
  comune cartello e fascia.
  Contatore dei pionieri (lug 2026): «830 oggetti» e «24 pionieri»
  sono un BLOCCO in colonna (`.conta-blocco`) DENTRO la riga di
  ordina+filtri, accanto ai controlli — il select è alto il triplo di
  una riga di testo, quindi la seconda riga non costa un pixel
  d'altezza alla vetrina (con o senza pionieri la prima card sta allo
  stesso posto: 371 a 360px). Il blocco a due righe SOPRA i controlli
  è stato provato e scartato, e così pure i conteggi appoggiati in
  fondo alla riga (`align-self:flex-end`): lasciavano un vuoto sopra.
  Interlinea 1.15 + gap 3px = blocco alto 31px contro i 33px del
  controllo d'ordinamento, con ~9px di bianco fra le maiuscole delle
  due righe. Resa
  compatta `.section-label.riga-conta` (numero arancione davanti,
  `::after` puntinato spento; la regola sta DOPO `.section-label`, che
  a pari specificità vincerebbe). Perché ci stia tutto a 360px: NIENTE
  emoji sui conteggi (📦 e 👥 provati e tolti, ~22px l'uno) e il
  blocco non si stringe mai (`flex:1 0 auto`) mentre a cedere è
  L'ORDINAMENTO (`min-width:0`; dal lug 2026 è un campo-bottone e non
  una select, quindi l'etichetta si accorcia coi puntini invece di
  troncare la voce del menu) — l'etichetta cresce, «830 RISULTATI» è
  più larga di «14 OGGETTI», e non deve mai finire sotto ai controlli.
  «Pionieri» e non «utenti»: in rodaggio è un club. Il numero è `COUNT(*)` sugli
  utenti con cache di 60s (`conta_pionieri`) e viaggia nella busta
  della PRIMA pagina di `/api/listings` accanto a `totale` e
  `conteggi` (nessun giro di rete in più, lo vede anche l'anonimo);
  è GLOBALE, non segue categoria né ricerca. Interruttore
  `CONTATORE_UTENTI` nel config (acceso di serie): spento, in DEMO o
  con un server vecchio la chiave non arriva e `renderPionieri()` non
  disegna la riga (e il blocco torna a una riga sola, com'era prima
  che i pionieri esistessero).
  Campanello dei nuovi iscritti (lug 2026): `avvisa_nuovi_iscritti()`
  avvisa i MODERATORI di ogni arrivo — mai il canale pubblico (il nome
  di chi si iscrive non si annuncia in piazza; i traguardi li racconta
  Andrea a mano). NIENTE coda in memoria come i post: il filo
  dell'acqua è la colonna `registrato` e a ogni giro d'orologio (10
  min, che è anche la finestra di raggruppamento) si legge chi è
  arrivato da `_ultimo_giro_iscritti` in poi — così copre da sola tutte
  e quattro le porte (Mini App, login web, nativo Nostr, /start del
  bot) e quelle di domani, senza ganci dentro l'autenticazione; il
  primo giro dopo l'avvio ARMA soltanto (un riavvio salta un battito,
  mai raffiche di recupero) e i confronti sono a secondi interi sui due
  estremi, quindi nessuno si perde né si ripete. Regola del drenatore
  promo, stessa `SOGLIA_AGGREGA`: fino a 3 un messaggio ciascuno (nome
  + @username + porta d'ingresso, `html.escape` che le notifiche sono
  HTML), oltre UN aggregato che non nomina nessuno; tetto
  `AVVISI_ISCRITTI_MAX_ORA` (6) sui SINGOLI, l'aggregato passa sempre.
  `TRAGUARDI_PIONIERI` (50/100/250/500/1000) dedotti dai dati senza
  stato: scattano solo nel giro in cui `prima < soglia <= totale`. Il
  conto del messaggio NON usa `conta_pionieri` (la sua cache di 60s
  direbbe «siamo in 24» mentre presenti il 25°). Interruttore
  `AVVISI_ISCRITTI`.
  Sollecito degli incassi fermi (lug 2026): un ordine 'confirmed'
  senza metodo d'incasso riceveva UNA sola notifica — ignorata, i
  sats restavano congelati nel silenzio. Ora l'orologio
  (`sollecita_incassi`) bussa al venditore ogni
  SOLLECITO_INCASSO_GIORNI (7; 0 = spento) con importo e strade
  (address o invoice); l'attesa riparte da MAX(aggiornato,
  sollecito_incasso_il). Dopo SOLLECITO_INCASSO_MAX (4) solleciti
  ignorati, UNA segnalazione 🧊 ai moderatori e poi silenzio: il caso
  e' in mani umane (contatore oltre il tetto = mai piu' riproposto).
  Colonne `ordini.sollecito_incasso_il`/`solleciti_incasso`
  (migrazione idempotente). Qui i sats non si muovono mai, solo
  parole; notifiche DOPO il commit, fail-open nell'orologio.
  Polso degli ordini per i moderatori (lug 2026):
  `polso_ordini_admin(riga)` manda una riga quando un ordine nasce
  (🛒 in verifica_pagamento, sats appena in cassaforte) o si chiude
  (✅ released, ⚖️ disputa vinta dal venditore — `ordini.disputata`
  decide la faccia —, ↩️ rimborso al compratore), sempre col conto
  degli ordini ancora aperti = stati fuori da
  creato/annullato/released/refunded. Il segnaposto {aperti} si
  riempie con replace, MAI format (i titoli possono avere graffe).
  Solo titolo e importi, mai nomi. Interruttore AVVISI_ORDINI_ADMIN,
  fail-open totale; a ~60 utenti il tempo reale basta, col volume si
  aggreghera' (pattern del drenatore promo).
  Redesign «mercatino di paese» (lug 2026, da Claude Design, solo
  CSS/markup): palette in `:root` — crema #FAF4E4, inchiostro #23282C,
  arancio ₿ #F7931A con i toni `--sats-deep/-text`, verde escrow
  #1B8B54, viola Nostr, oro distintivi; font Baloo 2 (titoli e logo) +
  Nunito (testi) + JetBrains Mono (numeri). Linguaggio: bottoni-pillola
  con ombra piena 0 3px 0 che si abbassano su :active (terziari =
  testo sottolineato, `.btn.link`/`.danger-ghost`); card annuncio
  «Etichetta» (cartellino prezzo ruotato −2° a cavallo della foto,
  `.tag-price` dentro `.ph-wrap`); il tratteggio verde è il SIGILLO
  dell'escrow e compare solo lì: `.escrow-zone` nel dettaglio (badge
  flottante «🔒 pagamento protetto»; il vecchio trucco
  `:first-of-type` è morto con la coppia d'acquisto — Acquista è
  arancio per classe), il richiamo `.bc-recinto` sulla barra
  d'acquisto e `.vault` del
  dettaglio ordine (step corrente = cerchio tratteggiato). Il «🔒
  escrow» è USCITO dalle card: la rassicurazione è la riga
  `.trust-line` sotto la searchbar e sopra la griglia del negozio.
  Logo = lockup `.bmark` (B che diventa ₿ con due pseudo-elementi);
  in topbar desktop è markup vero `.nav-logo` (il vecchio
  `nav::before` testuale non esiste più). Badge stati: `refunded` ha
  la SUA classe grigia (non più il verde di released). Distintivi:
  tessere d'oro per i guadagnati, 2 colonne (non le 3 del mockup:
  le descrizioni sono contenuto vero). Stato vuoto con CTA
  «+ Metti in vendita» (riusa `go('vendi')`) e conteggio «N oggetti»
  nel `section-label` (entrambi concordati). Restano fuori (logica
  nuova, respinta): filtri negli Affari e riga «Prossimo:» nei
  distintivi. Dal mockup sono invece ENTRATE (lug 2026, dopo la dark
  mode) le medagliette accanto al nome nella card venditore del
  dettaglio (oggi la sfilza `.sfilza`, dati da `venditore_distintivi`,
  vedi distintivi; la vecchia `.chip-fiducia` non esiste più). La
  pillola-contatore «🏅 N/M» accanto al lockup è vissuta poco: i
  tester l'hanno bocciata e al suo posto (lug 2026) c'è il tasto
  Profilo `.avatar-btn` — il TAPPO del barattolo: `assets/tappo.jpeg`
  (128px, ritagliato con Pillow sul diametro così il cerchio
  inscritto di border-radius coincide col bordo e l'arancione del
  fondo sparisce negli angoli; rotta esplicita, regola 3) reso tondo
  da border-radius+cover, con sotto il tappo disegnato in CSS
  (gradienti radiale+conico mascherato ad anello) come ripiego
  onerror, e sopra l'iniziale dell'utente in Baloo scura con alone
  chiaro (spread sul nome: le emoji iniziali non si spezzano);
  due istanze come la pillola di prima (testata mobile,
  topbar desktop in coda alle voci), accese da `renderAvatar()`
  ovunque tranne che in VETRINA anonima (in demo c'è: il Profilo
  esiste). Micro-anello d'oro `.oro` col primo distintivo guadagnato,
  anello arancione `.attivo` quando la vista è il Profilo (che non ha
  più voce in nav: `go()` accende il tappo). Come l'etichetta prezzo,
  il metallo del tappo resta chiaro anche col tema scuro. Con Profilo
  in testata la nav è scesa a 3 voci (Esplora · Vendi+ · Affari, il +
  al centro geometrico). Sempre dal feedback dei tester (lug 2026):
  la searchbar è un `<form>` senza bottone «Cerca» — si cerca col
  submit, cioè Invio/lente della tastiera (`enterkeyhint=search`),
  placeholder «Cerca su Barattolo…», MAI rimettere un ascoltatore
  keydown sull'Invio (doppia ricerca), e dentro il campo a sinistra
  c'è la lente decorativa `.q-lente` (emoji sbiadita con
  grayscale+opacity, grigia in entrambi i temi); il banner web arancione ha la
  ✕ «ho capito» (`chiudiBarraWeb`, hint `barraweb` nel solito
  `localStorage['barattolo_hint']` — chiuso una volta, mai più su
  quel dispositivo; Esci resta nel banner finché visibile e comunque
  nel Profilo). Festa dei sats: all'apertura di un
  ordine released, monete ₿ con fisica da confetti dal messaggio di
  chiusura (`festaSats`: 20 al venditore, 10 mini al compratore,
  ~1.5s, rAF legato al tempo + rete di sicurezza sull'overlay, spenta
  con prefers-reduced-motion; una volta per ordine e dispositivo in
  localStorage['barattolo_festa'], il patto degli hint). Asset del
  brand (lug 2026): `assets/mascotte.jpeg` (480px) e
  `assets/barattolo.jpeg` (256px), JPEG su fondo arancione ₿ pieno
  resi a tessere arrotondate (niente scontorno), serviti da rotte
  esplicite stile /vendor con cache 1 giorno (regola 3 aggiornata).
  Il barattolo è favicon e iconcina del lockup (header e topbar); la
  mascotte fluttua (floaty, spenta con reduced-motion) negli stati
  vuoti — ripiego sull'emoji 🫙 via onerror+sibling CSS se l'immagine
  non arriva, es. demo da file://. La hero di Esplora (SOLO ≥768px,
  dentro Telegram non c'è) usa invece `assets/barattolo-hero.png`:
  PNG scontornato con alpha, niente tessera, drop-shadow sulla
  sagoma, rotazione −6° e floaty.
  Dark mode «mercatino di sera» (lug 2026, solo miniapp.html): UN solo
  blocco `html[data-tema="scuro"]` in testa al CSS rimappa i token —
  niente doppioni sotto media query, perché è il JS a risolvere SEMPRE
  il tema effettivo (la media query non vede il tema di Telegram).
  Fondo bruno caldo #211A10/card #2C2517 (mai nero piatto), `--ink`
  diventa crema, arancio ₿ e oro invariati (protagonisti), verde/viola
  ricalibrati, contrasti AA verificati. I vecchi colori fissi sono
  token con doppio valore: `--header-bg`, `--nav-bg`, `--ph-a/b`
  (placeholder foto), `--ship/warn/off-bg` (badge stati),
  `--trust-note/sub`, `--step-line`, `--tile-off`, `--toast-bg/text`
  (il toast si INVERTE: crema su fondo scuro), `--ink-soft`, `--desc`,
  `--shadow-card/hover`; `--on-ink`/`--on-trust` sono il testo sopra
  i fondi `--ink`/`--trust` pieni (bianco in chiaro, scuro al buio:
  MAI `#fff` fisso sopra quei fondi). L'etichetta prezzo `.tag-price`
  resta di carta CHIARA anche al buio (valori fissi, il token
  `--paper` non esiste più: un cartellino vero non cambia colore di
  notte, e il prezzo deve staccare). Restano fissi di proposito: il
  finto QR del paySheet (che NON è un QR vero: pattern decorativo CSS
  ink-su-bianco, e chiaro deve restare), i `#fff` sui fondi arancio
  pieni, gli accenti pesca e oro. Scelta utente: cassetto «🌗 Aspetto»
  nel Profilo (pillole Auto/Chiaro/Scuro, `.tema-pill`), preferenza in
  `localStorage['barattolo_tema']` (pattern del toggle valuta, default
  auto); «auto» = `tg.colorScheme` SOLO con initData vero (nel browser
  lo stub di Telegram mentirebbe, il patto di esportaDati), altrimenti
  `prefers-color-scheme`, con ascoltatori `themeChanged` e matchMedia
  (MQL tenuta in costante: certi WebKit la buttavano col GC). Snippet
  anti-flash inline nell'head prima del paint; `applicaTema()` aggiorna
  anche `<meta name="theme-color">` e `tg.setHeaderColor/
  setBackgroundColor`. Levetta in testata (lug 2026): cerchietto
  `.tema-btn` accanto al tappo (testata mobile + topbar desktop, il
  pattern delle due istanze del tappo; nella tab bar mobile è
  nascosto) — 🌙 col tema chiaro, ☀️ con lo scuro, un tocco alterna
  via `alternaTema()` = una riga su `setTema(temaEffettivo()…)`:
  stessa memoria e stesse pillole del Profilo, che passano su
  Chiaro/Scuro (Auto resta selezionabile solo dal Profilo; da Auto
  il primo tocco parte dal tema effettivo del momento). Icona e
  tooltip li aggiorna `applicaTema()` (mai divergenti dalle
  pillole); giratina dell'icona solo con prefers-reduced-motion
  assente. C'è SEMPRE, anche in VETRINA anonima (il tema è di chi
  guarda): il vecchio «in vetrina vale auto e basta» non è più vero.
  Scudo anti-XSS: helper `esc()` (vicino a `fmt`) — OGNI testo scritto
  da un utente che entra in un template `innerHTML` DEVE passarci
  (titoli, descrizioni, zone, nomi, corrieri, tracking…); username e
  npub che finiscono dentro stringhe JS negli onclick passano invece
  dal filtro-alfabeto in `mapListing`/`mapOrder` (l'entity-encoding lì
  non basterebbe). Obbligo nato col cantiere NWC: in localStorage vive
  una credenziale di spesa.
  Compra subito (NWC): la stringa `nostr+walletconnect://` incollata
  nel profilo (scheda Profilo) vive SOLO in `localStorage['barattolo_nwc']`
  del dispositivo, MAI trasmessa al server (stessa filosofia della nsec
  solo-in-pagina: il secret NWC può spendere, fino al budget scelto nel
  wallet — la UI consiglia di impostarlo). Al collegamento `infoNwc()`
  valida la stringa con una STRETTA DI MANO vera: chiamata `get_info`
  via NIP-47 (prova relay, secret e cifratura insieme), tentando
  nip04 (default storico) e poi nip44; una risposta d'errore del
  wallet conta comunque come connessione viva. L'evento info kind
  13194 è solo un suggerimento per la cifratura (tag `encryption`):
  Coinos e altri NON lo pubblicano (verificato lug 2026), mai
  pretenderlo. Log diagnostici `🟪 [nwc]` in console. `clientNwc()` è il
  gemello NIP-47 del bunker NIP-46: richieste kind-23194 cifrate sul
  relay del wallet, risposte 23195 agganciate per tag `e` = id della
  richiesta (il bunker usa msg.id). `compraSubito()`: conferma
  esplicita → ordine+invoice IDENTICI al flusso manuale → poll su
  LNbits subito attivo (è LUI la fonte di verità del successo, mai la
  risposta del wallet) → `pay_invoice`. Wallet muto o in errore =
  ripiego sul paySheet con la STESSA invoice e lo stesso ordine (mai
  doppioni; reaper 30 min per i non pagati). Bottone ⚡ solo con
  wallet collegato e mai in DEMO/VETRINA; senza wallet tutto è come
  prima.
  Vista negozio: il blocco venditore nel dettaglio è cliccabile →
  profilo + griglia dei suoi annunci (card riusate via `cardHTML`);
  all'avvio `avvia()` legge `/negozio/...` da `location.pathname` e
  apre direttamente il negozio; bottone condividi = clipboard + toast.
  Dettaglio annuncio (lug 2026, feedback tester): bottone condividi
  `.share-btn` sulla foto (cerchietto di carta, anche sul segnaposto
  emoji, MAI in DEMO) → `condividiAnnuncio()`, ripieghi a scalare:
  con initData vero prima il canale di Telegram (la WebView NON ha
  navigator.share) — `tg.shareURL` se il client lo offre, poi
  `tg.openTelegramLink` su t.me/share/url (selettore chat) — e fuori
  da Telegram `navigator.share`, clipboard+toast, link nel toast
  (anche senza clipboard: mai il silenzio);
  il link è `GET /annuncio/{id}` (rotta gemella di /negozio,
  serve miniapp.html no-cache; regola 3 aggiornata), il JS legge
  l'URL con `apriAnnuncioDaUrl()` (pattern di apriNegozioDaUrl,
  chiamata in avvia E avviaVetrina: per gli anonimi apre il
  dettaglio in vetrina con l'invito; annuncio sparito = toast e si
  resta in Esplora). Il link t.me/startapp è rimandato: servirebbe
  la Mini App nominata su BotFather e il link web copre già tutti.
  Galleria del dettaglio coi pallini stile Vinted (`.foto-dots`,
  via il vecchio badge 📷 N): uno per foto in basso al centro,
  l'attivo pieno, aggiornati sull'evento scroll della striscia
  scroll-snap già esistente; con una foto sola non esistono.
  E CON UNA FOTO SOLA LA STRISCIA NON È UNA STRISCIA (classe `.una`,
  lug 2026, da un bug vero: gli annunci a foto singola scorrevano di
  lato portandosi dietro tutta la pagina, col testo che slittava come
  in una vista desktop). Restava un contenitore scorrevole
  (`overflow-x:auto`) con lo snap acceso ma senza niente da scorrere —
  misurato, `scrollWidth == clientWidth` — quindi il trascinamento
  orizzontale non lo consumava nessuno e si INCATENAVA all'antenato
  fino alla viewport. NON era un overflow: la pagina non sborda in
  nessuno dei due casi (verificato, 0px). Ora a una foto niente
  overflow e niente snap, più `overscroll-behavior-x:contain` sulla
  striscia — che è la stessa cosa detta dove appartiene, mentre il
  `none` sull'html (vedi il gesto di aggiornamento) è la cintura.
  Pallini e bottone condividi vivono SULLA foto: colori fissi
  (bianco/carta+inchiostro), identici in chiaro e scuro.
  IL TESTO DELL'UTENTE NON PUÒ ALLARGARE LA PAGINA (lug 2026, da due
  annunci veri importati da Nostr che si trascinavano di lato col dito
  sul CORPO dell'annuncio): una parola lunga senza spazi non ha nessun
  punto dove andare a capo, esce dal suo riquadro e allarga il
  DOCUMENTO. Misurato a 375px con un token da 60 caratteri: titolo
  +324px, riquadro venditore +129, descrizione +43. Un URL e una
  chiave prodotto NON sbordano — hanno `/` e `-`, dove il browser sa
  spezzare —, quindi la rete serve solo per il token continuo.
  `overflow-wrap:break-word` sta sul CONTENITORE `.detail-body` e non
  sui tre figli, perché si EREDITA: copre anche il campo che qualcuno
  aggiungerà lì dentro fra sei mesi (stessa rete dei nomi delle
  categorie in Sfoglia). MA NON BASTA DOVE C'È UN FLEX, ed è la parte
  che si dimentica: `.seller .who` è un figlio flex e un figlio flex
  non scende mai sotto il proprio contenuto (`min-width:auto`) — la
  parola si spezzava e la SCATOLA restava larga, +129px col testo già
  sistemato dappertutto. `min-width:0`, lo stesso rimedio del comune
  nella riga meta della card. In griglia la pagina non sbordava già
  (l'`overflow:hidden` del clamp), ma il titolo veniva tagliato a metà
  della prima riga con la seconda vuota e senza puntini.
  Dettaglio immersivo (lug 2026): via il bottone statico sopra la
  foto — il «Torna al mercatino» è il cerchietto di carta
  `.back-float` in alto a sinistra sulla foto (gemello del condividi,
  c'è SEMPRE, anche in DEMO e sul segnaposto emoji) e la foto 1:1
  sale a filo dello schermo. Un tocco sulla foto apre il LIGHTBOX
  `#lightbox`: foto intera mai ritagliata su fondo scuro, pinch e
  trascinamento coi pointer events (le dita in una Map,
  touch-action:none sul palco, capture sotto try/catch), rotella e
  doppio click da desktop, swipe tra le foto coi pallini SOLO a zoom
  1 (ingrandito il dito muove la foto), ✕/tap fuori/Escape per
  chiudere. Vanilla puro, zero librerie; lo zoom (clamp 1–4) tiene
  fermo il punto toccato e la clamp del translate non fa mai perdere
  la foto; body senza scroll a lightbox aperto.
  Barra d'acquisto al posto della tab bar (lug 2026, modello Vinted):
  nel dettaglio di un annuncio COMPRABILE la tab bar sparisce e al suo
  posto compare `#barraCompra` — «Acquista» NUDO (ARANCIO ₿
  `.btn.orange`, il CTA di casa: il verde è del recinto tratteggiato
  che lo avvolge, vedi il richiamo escrow più sotto) + «Fai
  un'offerta» (ghost neutro, senza icona); i bottoni della barra sono
  RETTANGOLARI col
  raggio del riquadro venditore (`border-radius:var(--radius)` in
  `#barraCompra .btn`), non più pillole. Gemella della nav per
  costruzione (position fixed, `--nav-bg`, blur, safe-area, z-index 30
  e altezza allineata: 62px contro 61, nessun salto di layout). La
  regia è `aggiornaBarraCompra(view)`, chiamata da `go()` a ogni cambio
  vista — così copre gratis il ritorno dal negozio e la riapertura del
  dettaglio quando una lampo scade, e uscendo la tab bar torna da sola
  (la classe è `body.con-barra`, tutta la resa vive nel CSS). Nasce
  SOLO su annuncio non proprio e `stato==='attivo'`: altrimenti resta
  la tab bar. I bottoni chiamano `startBuy`/`apriOfferta` TAL QUALI —
  le guardie stanno già lì, quindi in VETRINA la barra c'è e apre il
  foglio-invito; con un accordo accettato il tasto Offerta si spegne
  come in pagina. Dalle correzioni del lug 2026 la barra è NUDA:
  «Acquista» senza prezzo né strada (`cifraBarra` e `NOMI_VIA` non
  esistono più — il conto vivrà nella pagina dedicata del cantiere
  successivo, oggi lo dicono il foglio del varco e il paySheet), e
  attorno al SOLO Acquista c'è il RICHIAMO DELL'ESCROW: contorno
  tratteggiato verde `.bc-recinto` (stesso verde e tratteggio del
  recinto in pagina) col lucchettino `.bc-lucchetto` a cavallo del
  bordo in alto a sinistra — per questo il bottone dice «Acquista»
  senza 🔒: il lucchetto sta sul bordo, come la flag del recinto,
  mai due volte. I due tasti della barra sono GEMELLI (metà e metà,
  stessa forma e misura, offerta a sinistra) e PIATTI: dentro la
  cornice tratteggiata l'ombra piena 0 3px 0 mangiava il respiro in
  basso e la faceva sembrare scentrata — niente ombre nella barra,
  la cornice ha 3px d'aria uguali su ogni lato.
  GEMELLI DAVVERO (lug 2026, feedback di Andrea: l'arancio veniva
  fuori 24px più stretto e 10 più basso, e sembrava un tasto minore).
  Due cause, tutte e due da ricordare: 1) il tratteggio era un
  `border` con `padding`, che si mangiava 5px per lato — ora è un
  `outline` con `outline-offset:3px`, che NON occupa layout, quindi
  il bottone dentro il recinto è grande esattamente quanto il vicino;
  2) le basi flex erano a 0, e con la base a zero il padding (e il
  bordo del ghost) si sommano FUORI dalla base — la stessa lezione
  già pagata sui bottoni Applica/Azzera del pannello Filtri. Ora le
  basi sono al 50% (con `box-sizing:border-box` globale la base È la
  misura finale) e col multi-pezzo diventano 60/40 a favore
  dell'arancio, che lo stepper vuole spazio: si spostano le BASI e
  non il `grow`, perché a spazio già pieno decide lo shrink, che
  segue la base. Il lucchettino sta un filo DENTRO l'angolo
  (`top/left:-12px` contro il tratteggio a -5): centrato sul vertice
  uscirebbe dalla barra. Il padding della barra (12px sopra, 8 sotto)
  è l'aria del lucchettino e del tratteggio, e l'altezza resta quella
  della nav — 61px esatti col pezzo singolo.
  «Acquista» ha il testo un gradino più grande degli altri bottoni
  (17px nel recinto, 16 in barra: è il CTA principale dell'app), e in
  barra lo stepper non porta margine — con la scritta e il chip
  centrati insieme, un margine in più spingeva «Acquista» a 7px dal
  bordo sinistro.
  IL VARCO (lug 2026, da una domanda di Andrea che ha trovato un buco
  vero — la barra l'aveva aperto lei): chi tocca Acquista può non
  sapere nulla della consegna, e l'acquisto partiva con la strada del
  default senza che NULLA la nominasse prima del pagamento (a
  spedizione 0 il conto scomposto esce vuoto, e la protezione oggi è
  spenta). Il rimedio: il primo tocco con scelta ancora IMPLICITA non
  compra — apre il
  foglio «Come vuoi riceverlo?». Stato `consegnaEsplicita` (falso a
  ogni `openDetail`, vero solo alla voce
  del foglio — le pillole di scelta in pagina non esistono più, vedi
  sotto) e OGNI Acquista, barra e recinto, passa da `compraDaBarra()`:
  con una strada sola si va dritti a `startBuy`. Il foglio diventerà
  la pagina dedicata nel prossimo cantiere (transizione dichiarata:
  fino ad allora vale il flusso di oggi) — e quella pagina ha ORA un
  secondo compito, oltre alla scelta della strada: mostrare il CONTO
  SCOMPOSTO prima della invoice, che oggi arriva troppo tardi per chi
  ha la sola spedizione. Vedi «LACUNA TEMPORANEA, DICHIARATA» nella
  sezione della spedizione: le due cose si chiudono insieme, in un
  posto solo.
  `apriFoglioConsegna` RIUSA il markup di `#pickerSheet` (titolo,
  frecce, Esc, tap fuori: gratis) ma NON passa dal catalogo `PICKER` —
  qui il deposito non è una select, è `consegnaScelta`; ogni voce porta
  il suo totale vero (`cifraVia`) e la voce del codice online porta la
  regola asimmetrica GIÀ nel foglio (va detta prima dell'acquisto, e
  chi arriva dalla barra può non aver visto la trust-note in pagina).
  La scelta procede in UN gesto: `setConsegnaScelta` → chiusura MIRATA
  `chiudiPicker()` (mai `closeSheet`: spegnerebbe la pila e azzererebbe
  il `pollTimer` del pagamento che sta per partire) → `startBuy()`. Esc
  e tap fuori chiudono e basta, nessun acquisto a sorpresa; in VETRINA
  il varco non serve (startBuy apre l'invito). Il foglio di PAGAMENTO
  resta fuori da questa storia di proposito: `startBuy` crea ordine E
  invoice prima di aprirlo, con la consegna già cotta dentro
  (`spedizione_sats` e `cambio_ordine` si fissano alla creazione) — una
  scelta lì arriverebbe dopo la invoice.
  ACQUISTA VIVE IN DUE POSTI (correzioni lug 2026, poi rifinite col
  feedback di Andrea): dentro il recinto escrow sta SOLO «Acquista»
  arancio ₿ — centrato, lungo (`min-width:76%`) ma mai a tutta
  fascia (`.escrow-zone .acquista-cta`, specificità doppia perché
  `.btn{width:100%}` sta più in basso nel foglio; raggio 12, più
  squadrato del riquadro: il 16 su un bottone basso leggeva tondo).
  Coi pezzi >1 lo STEPPER sta DENTRO il bottone: `stepperAcquista()`
  = chip traslucido «− N +» accanto alla scritta, span con role
  (mai <button> annidato) e stopPropagation sul gruppetto — il tocco
  sui più/meno non compra mai; due istanze gemelle (pagina e barra)
  aggiornate insieme da `setQta` per classe (`.qm-num/.qm-meno/
  .qm-piu`, il vecchio stepper `.qta-riga` del recinto è morto —
  `.qta-step` vive ancora nel foglio del set). «Fai un'offerta» è
  una trattativa e sta fuori dal tratteggio: su MOBILE vive SOLO
  nella barra (in pagina è nascosto, `#detailContent
  .offerta-pagina{display:none}` sotto i 768 — con l'ID, che
  `.btn{display:flex}` a pari peso lo riaccenderebbe), da desktop
  resta in pagina sotto il recinto perché lì la barra non esiste.
  Nella barra fissa: OFFERTA A SINISTRA, ACQUISTA A DESTRA, metà e
  metà (col multi-pezzo il lato Acquista cresce, `#barraCompra
  .con-qta`). Nel recinto restano anche note e il «⚡ Compra subito»
  NWC (un'ALTRA strada, con la sua cifra); il trucco
  `:first-of-type` che promuoveva il ghost a
  CTA è stato RIMOSSO: Acquista è arancio per classe, sempre. Le PILLOLE DI
  SCELTA consegna (`pilloleConsegna`) non esistono più: in pagina
  restano solo le pillole INFORMATIVE (spedBadge + pilloleModalita),
  la scelta vive nel foglio del varco (e domani nella pagina
  dedicata). COERENZA DI FORME: `#detailContent .btn` e
  `#barraCompra .btn` portano `border-radius:var(--radius)` — nel
  dettaglio ogni bottone-oggetto è rettangolare col raggio del
  riquadro venditore (coppia, NWC, Metti nel barattolo, tasti del
  proprietario, set); i testuali link/danger-ghost non hanno forma.
  Da ≥768px la barra non esiste proprio:
  la nav è una topbar e il dettaglio a due colonne ha già i bottoni
  sotto mano. I fogli (41) e il velo (40) le passano sopra senza che
  rubi tocchi; a lightbox aperto si nasconde con header e nav
  (`body.lb-aperto`); la scivolatina d'ingresso tace con
  prefers-reduced-motion.
  IL RECINTO PARLA POCO (lug 2026): dentro l'escrow-zone resta UNA
  riga — «I tuoi sats restano nel deposito di garanzia finché non
  confermi di aver ricevuto l'oggetto» — e sotto Acquista NIENTE, solo
  il «Scopri di più». Sono uscite: il paragrafo su
  disputa e moderatore, e la riga «Ricevi una invoice Lightning,
  paghi con qualsiasi wallet» (troppo lunga, e chi ha un wallet lo sa
  già). Il «(escrow)» della prima spiegazione lunga se n'è andato con
  loro: la spiegazione lunga adesso vive nella pagina dedicata (regola
  9 rispettata, cambia solo dove sta la prima volta). Il link «Scopri
  di più» (`.scopri-link`) la apre e sta IN LINEA, in coda alla frase
  («…di aver ricevuto l'oggetto. Scopri di più»): non è più il piede
  staccato sotto il bottone (`.escrow-piede`, morto lug 2026). Porta
  lo STESSO verde `--trust-note` del testo di fiducia — è la stessa
  frase che continua, e a dire che è un link bastano la sottolineatura
  e il grassetto in più (800 contro 600); l'inchiostro del piede
  serviva a staccarlo da un blocco che adesso non esiste. È legato
  all'ULTIMA PAROLA con un nowrap (`.fine-frase`, il trucco della
  pillola condizione in coda al titolo): sotto i 390px non ci sta in
  riga e scendono INSIEME — da solo a capo tornerebbe a somigliare al
  piede di prima.
  LA PAGINA «IL PAGAMENTO PROTETTO» (lug 2026, `view-sicurezza`): la
  spiegazione lunga che il recinto non può contenere — hero col
  barattolo, cosa succede quando paghi (4 passi), i tempi, la
  disputa, DOVE IL DEPOSITO NON PUÒ PROTEGGERE (il codice rivelato,
  nei due sensi: quello che non torna indietro e quello che non
  funziona; il ritiro a mano; «l'oggetto promesso, non i gusti»), il
  pagamento Lightning e dove stanno i sats. Markup FISSO e nessun
  dato utente dentro: mai un `esc()` da ricordare. TRE PORTE —
  «Scopri di più» nel recinto, la riga di fiducia di Esplora e del
  negozio (ora un `<button class="trust-line">` col ›: il tour la
  cerca per classe e la classe non è cambiata), un bottone in fondo
  al Profilo — e `apriSicurezza()`/`tornaDaSicurezza()` ricordano da
  dove si veniva (il patto di `tornaDalNegozio`, con la vista di
  partenza che può essersi svuotata). Vale anche per gli anonimi in
  vetrina: la fiducia si spiega prima di chiedere di entrare.
  ATTENZIONE AL TESTO su dove stanno i sats: dice «restano bloccati
  in un conto Lightning della piattaforma», MAI la parola
  «custodia» — che in ambito regolatorio ha un peso specifico
  (decisione di Andrea, da tenere se qualcuno riscrive quel
  paragrafo; il parere legale MiCA è nel backlog).
  I TEMPI DELL'ESCROW STANNO IN UN POSTO SOLO (lug 2026): la costante
  `TEMPI` in cima al JS — `conferma` 72 ore, `autoSblocco` 10 giorni,
  `confermaDig` 24 ore, `silenzioDig` 48 ore, `invoice` 15 minuti —
  con accanto la tabella leva-del-config → chiave (ORE_CONFERMA,
  GIORNI_AUTO_SBLOCCO, ORE_CONFERMA_DIGITALE, ORE_SILENZIO_DIGITALE;
  la vita della invoice non è una leva, è `expiry: 900` in
  `crea_invoice_escrow`). Il client NON riceve quei numeri dal
  server: sono scritti a mano, ed erano sparsi in dodici stringhe
  (notifiche del pannello ordine, i quattro `confirm`, i toast, la
  nota digitale, il foglio del varco, la riga del cambio EUR).
  CHI CAMBIA UNA LEVA NEL CONFIG DEVE CAMBIARE `TEMPI`, e da lì in
  giù nessun numero di tempo si scrive più a mano. Il markup fisso
  della pagina porta segnaposto `<span data-tempo="...">` vuoti che
  riempie `scriviTempi()` all'avvio. (Fuori dal patto, di proposito:
  «l'anteprima vale 15 minuti» dell'import CSV — è il TTL del
  biglietto d'import, un'altra leva, che può cambiare da sola.)
  Preferiti «Nel tuo barattolo» (lug 2026): il simbolo è il
  BARATTOLINO 🫙 — MAI il cuore, MAI il fulmine (su Nostr è lo zap).
  Tabella `preferiti(tg_id, annuncio_id, creato, PK)`; toggle
  `POST /api/listings/{id}/preferito` (prima prova a togliere: il
  barattolo si svuota anche se l'annuncio è sparito del tutto, e
  anche da pieno); `GET /api/me/preferiti` = CAMPI_VETRINA +
  `a.stato` + venditore_id, dal salvato più recente, tetto 100 —
  escono ANCHE venduti/rimossi e il cassetto li mostra onesti «non
  più disponibile» (spenti, dettaglio non apribile, il 🫙 Togli
  resta) finché l'utente non li toglie lui. LIMITE 20
  (`MAX_PREFERITI`, lug 2026): la guardia vive nel SERVER, nel ramo
  INSERT del toggle — `_conta_barattolo` conta solo gli annunci
  ATTIVI (venduti/rimossi non occupano posto: comprare qualcosa che
  c'è dentro libera spazio da solo), oltre = 400 «Il barattolo è
  pieno!...»; niente await tra COUNT e INSERT (il patto
  anti-doppione). La risposta del POST porta anche `conteggio`
  (attivi dopo l'operazione: il frontend aggiorna il livello col
  numero del server). La fusione può superare i 20 in unione,
  accettato: il limite blocca solo le aggiunte nuove. Nessun
  conteggio pubblico: il venditore non vede chi né quanti (v1).
  `esegui_fusione` migra in unione (UPDATE OR IGNORE + DELETE, il
  pattern degli avvisi).
  Frontend: cerchietto `.jar-btn` sulla foto accanto al condividi —
  solo autenticati veri (mai DEMO/VETRINA) e mai sui propri annunci —
  da salvato si accende d'arancio e ondeggia (`jarPop`, spenta con
  reduced-motion), haptic + toast; Set `preferiti` e lista
  `myPreferiti` da `caricaPreferiti()` (in avvia() e a ogni apertura
  del Profilo: un salvato può essere stato venduto nel frattempo, e
  gli attivi entrano in `listings` via inCatalogo per openDetail);
  bottone gemello `#jarCta` «🫙 Metti nel barattolo / Già nel
  barattolo» nel dettaglio, `.btn.ghost` FUORI dal recinto escrow
  (il tratteggio è il sigillo del pagamento: dentro ci sta solo chi
  compra), stesse guardie e stesso `togglePreferito` del
  cerchietto (che aggiorna entrambi); guardia di cortesia client
  (toast senza richiesta a barattolo pieno, la verità resta il 400).
  IL BARATTOLO SI RIEMPIE (lug 2026): le icone (cerchietto del
  dettaglio + header del cassetto `#preferitiJar`) sono l'SVG inline
  di `jarSVG()` — vetro a stroke:currentColor, liquido = un rect
  arancione (`--jar-liquido`, default `--sats`; crema sul cerchietto
  `.salvato` per non sparire nel fondo) dentro la clipPath
  dell'interno (id univoco per istanza) — con 5 livelli a scatti
  `lv0-4` via translateY (0→0, 1-5→1, 6-10→2, 11-19→3, 20→4, da
  `livelloBarattolo` sui soli attivi di `contaBarattolo`);
  transizione morbida spenta con prefers-reduced-motion. Regia unica
  `aggiornaBarattolo(n)`: porta ogni `.jar-ico` in pagina al livello
  giusto e scrive «(N/20)» in `#preferitiConta` (N = attivi; usa il
  `conteggio` del server quando c'è). PRIMO cassetto del Profilo
  «🫙 Nel tuo barattolo» (`renderPreferiti`, stato vuoto che
  invita). Il 🫙 sulle card della vetrina, prima rimandato, dal
  lug 2026 c'è (stile cuoricino Vinted): cerchietto `.card-jar` in
  alto a destra sulla foto in `cardHTML` (quindi vetrina, negozio e
  risultati) — carta semi-trasparente da salvare, arancio pieno da
  salvato, colori fissi come tutto ciò che vive sulla foto; il
  cartellino prezzo sta in basso a sinistra, non si pestano. Il
  livello del barattolino in card è PER-ANNUNCIO (lv0 vuoto / lv4
  pieno: dice «questo l'hai già messo via»), NON quello globale:
  `aggiornaBarattolo` salta i `.jar-ico` dentro `.card-jar`, la
  regia per-card è `aggiornaJarCards()` (chiamata dopo
  caricaPreferiti — le card possono nascere prima del Set — e dopo
  ogni toggle: card, dettaglio e cassetto mai divergenti). Tocco con
  stopPropagation (non apre il dettaglio), scossellina all'aggiunta
  (il loop esistente copre anche le card), stesse guardie del
  cerchietto (mai DEMO/VETRINA/annunci propri; per gli anonimi
  NIENTE icona, coerente col dettaglio dove il cerchietto in VETRINA
  non esiste), tap target ~46px via `::after` sul cerchietto da 34.
  RIFLESSO DEL VETRO (lug 2026): jarSVG ha due pennellate celesti
  `.jar-lux` sul fianco sinistro, colore dal token `--jar-riflesso`
  (#BFE3F0, di sera più tenue #7FA3B5) — ovunque il barattolino
  compare (card, cerchietto del dettaglio, cassetto); dettaglio, non
  protagonista: non copre la lettura del livello.
  Le stelle del rating si mostrano solo se rating > 0 ("0 ★" farebbe
  danno ai venditori appena arrivati); dal lug 2026 le accende il
  sistema di feedback (vedi server.py).
  Scheda Profilo 👤 (lug 2026): nata quarta voce di nav, dal lug 2026
  ci si arriva dal tasto-tappo in testata (vedi redesign: la nav è a
  3 voci; `view-profilo` e il ramo `profilo` in `go()` rilanciano i
  render come sempre, e in VETRINA non c'è proprio il tasto). È a CASSETTI
  richiudibili stile Vinted (CSS `.acc`, header cliccabile con
  emoji+titolo+freccia, `toggleAcc()`; tutti chiusi di default): dopo
  la testata sempre visibile `renderProfilo()` (nome, badge,
  vendite/acquisti conclusi da `/api/me`, stelle solo se rating>0,
  link del negozio con condividi), in ordine: «📋 I tuoi annunci»,
  «🆔 Identità» (righe identità + campo npub + verifica, riuniti
  nello stesso cassetto; si chiamava «Identità e Nostr», accorciato
  col feedback dei tester), «⚡ Incassi e pagamenti» (NWC +
  campo Lightning address `lnAddrProfilo`, che riusa
  `POST /api/me/ln-address`, + export CSV; il payoutPanel dentro
  l'ordine resta dov'è, e in DEMO l'intero cassetto — id
  `walletBlocco` — sparisce), «🔔 Avvisi», «🏅 Distintivi», stats
  admin, bottone Esci solo in modalità WEB. I cassetti senza nulla da
  mostrare spariscono interi; gli id interni dei blocchi sono gli
  stessi di sempre (arrivano da Vendi, traslocati TAL QUALI): Vendi è
  tornato SOLO il form di pubblicazione, e dopo pubblica/modifica si
  apre il dettaglio dell'annuncio appena salvato (l'id arriva da
  `{ok,id}`, ripiego su Esplora se non è in lista).
  PWA installabile (lug 2026, Fase 1 del percorso PWA→APK→Zapstore;
  percorso ormai completo: Fase 2 = icona adattiva, Fase 3 =
  «Distribuzione dell'APK», più sotto): `manifest.json` (id/
  start_url/scope "/", standalone, crema+arancio, 4 icone any+maskable
  generate da `genera_icone.py` — dal lug 2026 ritagliate da
  `assets/barattolo-icona-sorgente.jpeg` (2048px, barattolo già
  composto sul suo arancione: fondo CAMPIONATO dagli angoli, bbox a
  soglia con l'ombra dentro, mai upscale), any al 90% e maskable al
  67% del lato (intero nel cerchio di sicurezza 80%, verificato con
  l'anteprima); si rilancia quando la grafica cambia, e chi la
  rilancia alza VERSIONE in sw.js: le icone sono in dispensa) +
  `sw.js` PRUDENTE servito dalla RADICE, sempre
  no-cache. Il SW: dispensa `statica-{VERSIONE}` con addAll atomico
  (asset di casa + `/vendor/nostr.js` + `offline.html`), cache-first
  runtime SOLO per i Google Fonts (`font-{VERSIONE}`), navigazioni
  network-first con ripiego su `/offline.html` (mascotte dalla
  dispensa) a rete morta — gli header anti-cache di `/` restano
  sovrani. MAI toccate (nemmeno respondWith): `/api/*`, `/foto/*`
  (cache HTTP propria), telegram.org (script che gestiscono l'auth),
  metodi non-GET. Niente skipWaiting: la versione nuova aspetta la
  visita successiva; REGOLA: chi cambia un file in PRECACHE alza
  `VERSIONE`. VINCOLO DI FERRO: dentro la WebView di Telegram tutto
  identico — il SW si registra solo con `!tg?.initData` (e protocollo
  http: la DEMO da file:// non esplode); la WebView ha comunque
  storage separato dal browser, niente unregister (sarebbe esso
  stesso comportamento nuovo). Banner «🫙 Porta Barattolo in tasca»
  (`#installBanner` sotto l'header di Esplora, `bannerInstallaPwa()`):
  solo web MOBILE fuori da Telegram, mai se già standalone, mai in
  DEMO; NESSUNA dismissione persistente (le chiavi storiche
  installa_pwa e pwa_installata in barattolo_hint sono inerti): sia
  il «Non ora» sia appinstalled sono RINVII di pagina (variabile in
  memoria, mai localStorage) — alla visita successiva il banner
  torna, così dopo una disinstallazione ricompare da solo; il caso
  «app installata» lo coprono le guardie standalone, più il fatto
  che Chrome non rilancia beforeinstallprompt ad app installata (su
  iOS e Firefox, senza appinstalled né evento, chi ha installato
  rivedrà il banner nel browser: accettato); Android Chrome/Edge =
  beforeinstallprompt intercettato + prompt vero, iOS e Firefox
  Android (che beforeinstallprompt non ce l'ha) = foglietto
  `#installSheet` coi passi scritti da apriInstallSheet() secondo il
  browser (Safari: Condividi ⬆️; Firefox: menu ⋮ → Installa). Login
  in standalone
  (dichiarato): anonimo = vetrina completa con gli inviti di sempre;
  Nostr bunker/nsec = strada maestra (tutto in pagina, niente popup;
  su iOS lo storage è separato da Safari: login da rifare una volta);
  widget Telegram = da verificare in produzione (Android eredita il
  cookie dal profilo Chrome, il popup callback è fragile; su iOS
  probabilmente resta solo Nostr). Piano di riserva dichiarato e NON
  costruito: widget in modalità redirect (`data-auth-url` + endpoint
  GET che riusa `verifica_login_widget`), solo se il collaudo vero lo
  esige. Lighthouse: dalla v12 la categoria PWA non esiste più — il
  criterio è «installabile senza avvisi» nel pannello Application.
  Icona adattiva dell'APK (lug 2026, TWA): Bubblewrap (1.24.1) NON sa
  fare i due livelli — il suo ic_launcher.xml mette l'INTERA maskable
  nel background su bianco, foreground trasparente: niente parallasse
  e ai bordi il confine tra arancioni; il monochromeIconUrl del
  twa-manifest serve solo a notifiche e shortcut. `genera_icone_apk.py`
  patcha il progetto TWA generato (fuori dal repo, `..\..\barattolo-twa`,
  coi keystore: MAI portarlo dentro): campiona l'arancio con LA STESSA
  ricetta importata da genera_icone.py → `iconBackground` in colors.xml
  (#F78F19: sfondo e barattolo dalla stessa foto, il confine non può
  esistere); scontorna il barattolo (alpha a rampa dalla distanza dal
  fondo, fori interni richiusi col floodfill dall'esterno a 1/4 di
  risoluzione) → ic_launcher_foreground.png nei 5 mipmap (canvas
  108dp, barattolo ~51%: la presenza della maskable riportata al
  cerchio sicuro 66dp); silhouette bianca con la stessa alpha →
  ic_launcher_monochrome.png (temi Android 13+, esige compileSdk ≥33);
  riscrive ic_launcher.xml a tre livelli, allinea il fondo dello SPLASH
  allo stesso arancio campionato (twa-manifest `backgroundColor` + la
  copia in app/build.gradle: lo splash mostra l'immagine dell'icona, e
  sul crema del manifest faceva l'effetto francobollo — il crema resta
  giusto per la PWA, dove background_color è anche il fondo pagina
  pre-paint), ridisegna i drawable-*/splash.png col barattolo
  scontornato su trasparente a 160dp di lato massimo (~40% del lato
  corto; Bubblewrap ci metteva la tessera INTERA a 300dp fissi, un
  macigno, e nel twa-manifest NON esiste una leva di scala:
  splashScreenFadeOutDuration è solo la dissolvenza, l'immagine è
  disegnata centrata a dimensione intrinseca — l'unica leva sono i
  pixel dei PNG) e rimette da solo -Xmx1024m in gradle.properties. LITURGIA di ogni release APK, sempre in
  quest'ordine: `bubblewrap update --appVersionName=X.Y` (alza lui il
  versionCode) → `python genera_icone_apk.py` → `bubblewrap build`
  (le password del keystore le batte Andrea nel SUO terminale) —
  l'update cancella e riscrive proprio i file patchati, lo script va
  SEMPRE rilanciato dopo. ATTENZIONE: anche l'«apply» del web manifest
  (la domanda che `bubblewrap build` fa quando vede il manifest del
  sito cambiato) sovrascrive gli splash — se lo script è già stato
  applicato rispondere `n`; se si risponde `y`, rilanciare lo script
  PRIMA di rifare il build. Verificato sulla 1.2 aprendo l'APK firmato
  con aapt2: tre livelli, alpha vera, adattiva per tutte le densità;
  il medaglione residuo sul telefono è lo stile icone del launcher
  Oppo, non l'APK.
  Distribuzione dell'APK (lug 2026, Fase 3 del percorso PWA→APK→
  Zapstore): due canali, la release GitHub è la FONTE UNICA di verità.
  Repo pubblico `kreamistudio-crypto/barattolo-releases` (satmarket
  resta privato: Obtainium e Zapstore esigono download anonimi) con
  README per gli utenti e `zapstore.yaml` nella root; le release hanno
  tag `vX.Y`, UN solo APK per release (`barattolo-X.Y.apk`, copia
  rinominata di app-release-signed.apk) + `.sha256` + note scritte a
  mano con l'hash. Obtainium segue il repo da solo; Zapstore ci pesca
  l'APK. CLI `zsp` (github.com/zapstore/zsp, SOLO Linux/macOS → vive
  in WSL Ubuntu, `~/bin/zsp`; il progetto corre, ricontrollare il
  README a ogni uso) pubblica gli eventi NIP-82 (32267 app, 30063
  release, 3063 asset) su `relay.zapstore.dev` e carica i file sul suo
  Blossom. CHIAVE NOSTR DEDICATA E FREDDA (scelta deliberata: NON
  quella della piattaforma, per separarne i destini): vive SOLO su
  foglietti + Bitwarden («Barattolo release Nostr»), MAI su
  VPS/disco/repo/chat; si usa in WSL con `read -rs SIGN_WITH &&
  export SIGN_WITH` (prompt nascosto) e `unset SIGN_WITH` a fine rito;
  perderla = gli utenti Zapstore reinstallano (GitHub non è toccato);
  la npub sta in `zapstore.yaml` (campo `pubkey`, whitelisting del
  relay). Il certificato Android è legato alla chiave con la prova
  NIP-C1 (kind 30509, `zsp identity --link-key`): esige la CHIAVE
  PRIVATA del keystore (verificato nel sorgente: firma una prova di
  possesso) e zsp non legge i JKS → rito del p12 TEMPORANEO: `keytool
  -importkeystore` (il keytool è nel JDK di Bubblewrap) →
  `barattolo.p12` accanto al keystore → link-key → `Remove-Item`
  SUBITO. La prova SCADE DOPO UN ANNO: rito da ripetere (ma è
  facoltativo: scaduta, le release escono lo stesso). LITURGIA
  release completa, dopo il `bubblewrap build` di sempre: 1) sha256 e
  `gh release create vX.Y` su barattolo-releases con APK + .sha256;
  2) in WSL `SIGN_WITH` col prompt nascosto → `zsp publish` → unset.
  Prima GitHub, poi Zapstore, sempre. Gli script del rito
  (`genera_chiave_release.py`, `profilo_release.py`) vivono in
  `..\..\barattolo-twa` col keystore, fuori dal repo; nessuno dei due
  scrive segreti su disco.
  LEZIONE publisher nuovo (lug 2026, da un bug vissuto): il popup
  «Trust this app?» di Zapstore resta APPESO per sempre se la npub
  del publisher non ha un profilo kind-0 — il client cerca il profilo
  solo in cache locale, senza timeout né ramo d'errore (verificato
  nel sorgente, relevant_who_follow_container.dart), e la precarica
  dai relay "social" damus/primal/nos.lol. Quindi: per OGNI npub
  nuova che firma release, PRIMA il kind-0 su quei relay, POI lo
  `zsp publish`. Il campo pubkey in zapstore.yaml non c'entra (è il
  whitelisting lato relay, il client non lo guarda). Senza follower
  il secondo stadio (web-of-trust via DVM Vertex) dice solo «No
  reputation information found» ma NON blocca: un follow kind-3 dalla
  piattaforma e la nota di presentazione lo popolano —
  `presenta_release.py` nel repo fa entrambi (una tantum, idempotente,
  legge e ESTENDE la lista follow esistente senza mai sovrascriverla,
  gira sul VPS con la chiave della piattaforma dal config).
- `config.py` — TUTTE le chiavi e impostazioni. NON è nella repo
  (.gitignore) e NON deve MAI entrarci. `config_esempio.py` è il modello.
- `importa_nostr.py` — importa annunci NIP-99/NIP-15 da Nostr.
  Il cuore è `importa_venditore()`, importabile: lo usa anche
  l'orologio del server, che rilancia l'import OGNI ORA in
  `asyncio.to_thread` (fail-open totale: errori = una riga in
  console). Al primo giro scrive il
  badge 🟣 verificato sul profilo del venditore (npub canonica bech32 via
  `hex_to_npub`, gemella di quella di server.py; mai sovrascrivere
  una npub diversa già dichiarata): così il login Nostr lo riconosce
  invece di creargli un account nuovo.
  DUE VITE, e vanno tenute distinte: lanciato A MANO
  (`python importa_nostr.py`, npub e VENDITORE_ID dal config) è com'è
  sempre stato — scrive dritto nel database, bypassa `pubblica()` e
  non verifica le firme: la fiducia sta tutta nella npub scritta nel
  config, il che va bene per un amico e non per uno sconosciuto.
  Chiamato dal SERVER riceve invece il `vaglio` (vedi «Import aperto»
  più sotto), che è il pezzo che chiude quel buco.
  `interroga()` fa DUE REQ separate sullo stesso websocket, annunci e
  cancellazioni kind 5, con `limit` propri (`LIMITE_ANNUNCI` /
  `LIMITE_CANCELLAZIONI`, 500) e aspetta ENTRAMBI gli EOSE — più il
  ramo `CLOSED`, o si resterebbe ad aspettare un EOSE mai dovuto. Con
  una REQ sola il tetto valeva per l'INTERA richiesta e i relay
  servono i più recenti per primi: un venditore con molte
  cancellazioni si spingeva fuori dalla finestra i propri annunci, in
  silenzio (misurato su una chiave con 206 kind 5: dei 200 eventi che
  tornavano, 197 erano cancellazioni e gli annunci letti erano 3 su
  17). `interroga_aperto()` è invece la spazzata SENZA filtro
  d'autore, e serve solo alla scoperta.
  `testo_evento(e)` è il cuore condiviso che dà titolo e descrizione
  GIÀ TRONCATI come finiranno nel database: lo usa `estrai_annuncio`
  per scrivere e il server per capire se un evento è cambiato davvero.
  Se i due divergessero, un annuncio fermo sembrerebbe cambiare a ogni
  giro (o uno cambiato sembrerebbe fermo).
  LEZIONE foto importate (lug 2026): il download è VERBATIM (mai
  ricompresso da noi), ma i relay sono la fonte di verità — quando
  il venditore ripubblica da un client che gli ricomprime le foto
  (successo con Primal: originali nitidi → 1024px qualità ~60 su
  blossom, content-addressed: l'originale non esiste proprio online)
  l'import sovrascrive i pieni locali con quelli, e i vecchi nitidi
  sono persi. Da allora `scarica_foto` ha la SENTINELLA: se il nuovo
  file pesa <60% del locale, riga «📉» nel journal (mai in silenzio),
  e cancella la `_min` gemella ormai stantia (la card ripiega sul
  pieno, il backfill la rifà al riavvio). Riparazione possibile solo
  dal venditore (ri-upload degli originali da un host che non
  ricomprime, o file consegnati a mano: un file rimesso sotto lo
  stesso nome è stabile finché gli URL dell'evento non cambiano —
  ricordarsi di cancellare anche la `_min`).
- IMPORT APERTO da Nostr (lug 2026, cantiere di Alan + le correzioni
  decise da Andrea). Il codice sta in server.py, accanto all'orologio;
  qui perché è la seconda vita di importa_nostr.py.
  Non si importa più UN venditore scelto a mano: si importa chiunque
  pubblichi annunci NIP-99 in italiano, e i filtri sono due — la
  lingua e la legge.
  L'INTERRUTTORE `IMPORT_NOSTR_APERTO` nasce a FALSE nel codice e nel
  config d'esempio, al contrario di POST_AUTOMATICI e degli altri, ed
  è deliberato: il config del VPS non ha la chiave, quindi con un
  default True basterebbe un `git pull` e un riavvio perché la
  scoperta cominci ad aprire account e a mandare DM a estranei. Un
  salto così si fa con un gesto, non per distrazione — e quella riga
  è anche l'interruttore d'emergenza se il primo giro va storto.
  ZERO migrazioni di schema, e non è un risparmio furbo: essere su
  Barattolo È essere su Nostr, il mercatino è una VISTA degli eventi e
  non una copia. Quindi niente registro dei venditori (si deduce),
  niente flag «toglietemi da qui» — l'uscita esiste già ed è nativa
  del protocollo: un kind 5, che le lapidi rispettano per sempre. Un
  flag nostro sarebbe una seconda verità accanto a quella dei relay.
  DUE MESTIERI DISTINTI, e devono restarlo: la SCOPERTA
  (`scopri_venditori_nostr`, ogni 6h) setaccia i relay senza filtro
  d'autore per trovare npub nuove; l'IMPORT chiede chiave per chiave.
  Una spazzata sola non basta: i relay servono i più recenti e 500
  eventi coprono poche settimane di TUTTO Nostr — misurato, la
  spazzata globale non vedeva nessuno dei 17 annunci che la query
  mirata trovava tutti. Tetto `MAX_VENDITORI_NUOVI_GIRO` (10), i più
  prolifici per primi.
  CHI SI IMPORTA: `venditori_nostr_attivi()` = chiunque abbia una
  chiave di cui ha dimostrato il possesso — `npub_accesso` o badge
  `npub` VERIFICATO. È la regola di `notifica()` e dei ponti: mai una
  npub nuda. SCELTA DICHIARATA (decisione di Andrea): ci sono dentro
  anche gli utenti Telegram che avevano verificato la npub solo per il
  badge 🟣, e i loro annunci NIP-99 compaiono qui senza che nessuno
  glielo abbia chiesto. È corretto — se uno pubblica su Nostr è giusto
  che compaia su Barattolo — e i doppioni li prende la deduplica che
  esiste già.
  FILTRO LINGUA `annuncio_italiano`: tre prove dalla più forte alla
  più debole — la zona è un comune vero (passa dal motore geografico
  di casa, che sa che «Como» è un comune ma «como» in una frase
  spagnola no), la zona nomina l'Italia a PAROLA INTERA, oppure il
  testo ha ≥3 PAROLE FUNZIONE italiane (`PAROLE_FUNZIONE_IT`: «di»,
  «che», «per»… un annuncio inglese può dire «vendo» per caso, non
  dice quelle tre insieme). Il confronto è SEMPRE a parole intere: il
  vecchio filtro a sottostringhe prendeva «instal-LAZIO-ne» e
  «a-ROMA-tico», e su 1044 annunci veri ne dichiarava italiani 70 di
  cui 27 stranieri.
  FIRME VERIFICATE DAVVERO (`verifica_firma_nostr`): con un venditore
  fidato ci si poteva fidare del campo `authors` dei relay; da queste
  chiavi ora nascono ACCOUNT, e un relay bugiardo potrebbe attribuire
  annunci a chiunque. Ricetta di `verifica_evento_login` (id
  ricalcolato NIP-01, mai quello ricevuto), senza coincurve = False.
  L'ANELLO CHE SI CHIUDEVA (lug 2026, bug vissuto al primo giro vero:
  40 annunci fantasma — la sezione più importante di questa voce,
  perché è l'errore che la struttura del cantiere invitava a fare).
  La scoperta setaccia i relay SENZA filtro d'autore, e fra gli
  annunci NIP-99 italiani con firma valida ci sono anche i NOSTRI —
  quelli che la piattaforma firma per conto di chi pubblica da qui.
  Nessuno la escludeva: è nato un account intestato alla nostra stessa
  chiave, e l'import ha ricominciato a scaricare in casa ciò che
  avevamo appena pubblicato. Ogni annuncio nativo si è ritrovato una
  copia intestata a un venditore che non esiste, e il negozio di quel
  venditore pieno di roba di persone diverse — che è anche perché
  «Altri oggetti di questo venditore» mostrava oggetti di altri: la
  striscia faceva bene il suo mestiere su un negozio che era una
  discarica. Un solo bug, tre sintomi che sembravano tre bug.
  Il rimedio è `chiave_di_casa(chiave)` (hex o npub, maiuscole
  comprese), usata in DUE punti: `scopri_venditori_nostr`, che non ci
  adotta più, e `venditori_nostr_attivi`, che salta la nostra chiave
  ANCHE se in `utenti` la riga esiste già — ed è quella che ferma il
  danno al primo riavvio, senza aspettare la pulizia. Il confronto è
  sulla CHIAVE e non sul tag `d` ('barattolo-…') o sul tag `r`:
  quelli li può scrivere chiunque, la firma no.
  E IL BUCO VERO, che il fantasma ha solo reso visibile:
  `importa_venditore` credeva sulla parola al filtro `authors` della
  REQ. Ora confronta `e["pubkey"]` con la chiave chiesta e scarta il
  resto. La firma si verificava già, ma risponde a un'ALTRA domanda —
  «l'evento è firmato dalla chiave che DICHIARA?», non «quella chiave
  è il venditore che ho CHIESTO?»: le due insieme chiudono, una sola
  non chiude niente. L'autore di un evento decide A CHI VANNO I SATS
  di chi lo compra. Vale anche per i kind 5: una cancellazione altrui
  col tag `e` giusto avrebbe spento l'annuncio di un altro, perché il
  tag `e` non nomina l'autore. `prove.py` ha una SENTINELLA che
  verifica che quel confronto esista ancora dentro importa_venditore:
  è il tipo di riga che sparisce in un refactor.
  La pulizia delle copie già nate è `ripulisci_anello_nostr.py` (vedi
  sotto).
  MODERAZIONE, e qui i due strati finiscono in modo DIVERSO:
  le PAROLE VIETATE restano uno scarto secco (deterministico: armi e
  droga non vogliono una coda ma una porta chiusa; resta nel registro,
  che i moderatori leggono); l'AI invece NON scarta più niente da sola
  — ogni verdetto diverso da OK, dubbio E bocciatura, fa nascere
  l'annuncio in `stato='revisione'`. È la terza via allargata al
  giudizio più delicato che abbiamo: annunci di gente che non è qui a
  difendersi, in un italiano che non abbiamo scelto noi, dove un'AI
  che sbaglia in silenzio fa perdere un venditore onesto senza saperlo
  mai. Meccanica: il vaglio MARCHIA l'evento (chiave `_revisione`) e
  l'import legge il marchio (stato alla nascita, e un annuncio già in
  vetrina il cui TESTO è cambiato e che non si sa più approvare torna
  in attesa, come una modifica dal form); `_apri_revisioni` gira DOPO
  l'import — quando l'id esiste, l'ordine di `pubblica()` — iscrive il
  motivo nel registro e manda la tastiera ✅/❌, idempotente sul
  registro (un annuncio fermo in coda una settimana non suona ogni
  ora); da lì in poi lo scudo anti-resurrezione lo salta da solo.
  Il ponte `_MOTIVI_REVISIONE` (titolo → motivo) sta in memoria: un
  riavvio lo perde e l'annuncio resta in coda col motivo generico.
  LA MODERAZIONE SI PAGA UNA VOLTA SOLA (`_da_giudicare`): prima si
  vagliava tutto a ogni giro, cioè ogni ora, per farsi ridire la stessa
  cosa sugli stessi testi. Si rigiudica quando cambia il TESTO, non
  l'evento: l'id è l'impronta di tutto (prezzo, foto, data) ma la
  moderazione legge solo titolo e descrizione, e un ritocco al prezzo
  non può cambiare un verdetto. Mai su ciò che non è più attivo (in
  revisione aspetta un umano, rimosso è deciso, e l'import li salta
  comunque). Il fail-CLOSED resta ma preciso: se l'AI tace non entra
  ciò che non è mai stato giudicato, mentre chi era già passato
  continua ad aggiornarsi.
  IL BENVENUTO È L'UNICO MESSAGGIO CHE MANDIAMO SENZA PERMESSO, e
  questa è la regola che governa tutto il resto. Chi viene scoperto
  riceve l'account nativo (la macchina del login Nostr) e UN messaggio
  (`BENVENUTO_NOSTR`, testo definitivo scritto da Andrea — chi lo
  ritocca tenga l'ordine: cos'è Barattolo (sats + deposito di
  garanzia), che facciamo da vetrina a Nostr, cosa si sblocca entrando
  (lampo, spedizione col costo suo, ritiro, buoni e codici online,
  condizioni/quantità/categoria), la reputazione che si costruisce
  vendendo, il progetto in fase di test con la sua npub, e in fondo la
  riga sui suggerimenti — «di serie non ti scriviamo più»).
  I SUGGERIMENTI SUGLI ANNUNCI SONO OPT-IN (lug 2026, decisione di
  Andrea). Un evento NIP-99 non dice consegna, condizione e categoria
  — ed è proprio ciò su cui il compratore filtra — quindi
  `_chiedi_completamento` sa cosa manca e potrebbe dirlo; ma nasceva
  automatico, cioè un consiglio utile mandato a gente che non ci aveva
  chiesto niente: spam, perché a decidere se un messaggio è benvenuto
  non è chi lo scrive. Ora lo governa `utenti.suggerimenti_annunci`,
  SPENTO di serie, acceso dalla voce «💡 Suggerimenti sui miei
  annunci» nel cassetto «🔔 Avvisi» del Profilo
  (`POST /api/me/suggerimenti`, pattern di canale-notifiche;
  `rigaSuggerimenti`/`setSuggerimenti`, il flag esce da /api/me che fa
  SELECT *). Chi non lo accende non riceve MAI nulla, e l'unico posto
  dove lo nominiamo di nostra iniziativa è l'ultima riga del benvenuto.
  ATTENZIONE, il gate sta PRIMA di ogni lettura e non è pignoleria: a
  interruttore spento non si timbra `completamento_avvisato`, o chi lo
  accendesse domani troverebbe i suoi annunci già «avvisati» e non
  riceverebbe mai il consiglio appena chiesto.
  Acceso, resta gentile: una volta sola per annuncio (la colonna, e non
  una coda in memoria, perché «gliel'ho già chiesto» deve sopravvivere
  ai riavvii), mai nel giro in cui l'annuncio è apparso (`creato < t0`:
  chi è appena stato scoperto ha già avuto il benvenuto, e due messaggi
  di fila sono un'altra cosa), un messaggio per VENDITORE e non per
  annuncio, ogni voce dice A COSA SERVE (un motivo, non un rimprovero),
  il paragrafo sul codice online compare solo a chi non ha dichiarato
  nessuna consegna (è il caso di buoni e gift card; a chi vende una
  bici sarebbe rumore), e la chiusa dice dov'è la maniglia per
  spegnerli.
  RISCHIO DICHIARATO E ACCETTATO (decisione di Andrea): si può
  comprare in escrow da un venditore che non sa di essere qui. Prima
  valeva per un venditore consenziente, ora per chiunque venga
  scoperto. È accettato perché è esattamente il problema che il
  deposito di garanzia esiste per risolvere: i sats restano bloccati
  finché il compratore non conferma, e se il venditore non si fa vivo
  il rimborso è la via normale. Il DM di benvenuto arriva PRIMA che se
  ne accorga da solo, ed è il motivo per cui questo non è uno scippo.
  LIMITE NOTO: `venditori_nostr_attivi()` spende una query a vuoto
  ogni ora per ogni utente con badge verificato che non vende su
  Nostr. Irrilevante ai numeri di oggi; con migliaia di utenti servirà
  un tetto per giro.
  RESTANO FUORI dal cantiere, per scelta: il relay Barattolo
  (infrastruttura, cantiere a parte), la PR al repo dei NIP, e il form
  per completare i metadati direttamente sugli importati.
- METADATI DI COMMERCIO NEI TAG NIP-99 (lug 2026): la spec non dice
  nulla di spedizione, condizione e quantità, e finora le scrivevamo
  solo in prosa nel `content` — leggibili da un umano, invisibili a
  ogni macchina, comprese le NOSTRE al giro d'import successivo (è
  letteralmente il motivo per cui un annuncio importato arrivava senza
  consegna né condizione). In scrittura `tag_commercio` (server.py):
  `["delivery","shipping","5.00","EUR"]` ripetibile ·
  `["delivery","pickup"]` · `["delivery","digital"]` ·
  `["condition", new|like-new|good|fair|poor]` · `["stock","3"]`
  (assente = 1). `delivery` è RIPETIBILE apposta invece dell'enum
  chiuso di Shopstr: lì per dire «spedisco o ritiri» serve il valore
  composto "Free/Pickup", e un terzo modo vorrebbe enumerare tutti i
  sottoinsiemi. Il content continua a dire le stesse cose a parole
  (per le persone e per i client che il nostro vocabolario non lo
  conoscono): se un giorno divergessero, quella giusta è il TAG.
  In lettura `estrai_commercio` (importa_nostr.py) parla DUE dialetti,
  il nostro e quello de facto di Shopstr (`shipping` con l'enum,
  `quantity`, `pickup_location`). Due trappole collaudate: costo
  assente ≠ gratis («0» è gratuito, il tag senza importo è «da
  concordare»), e `weight` NON è un peso — per Shopstr è una VARIANTE
  di prodotto col suo prezzo, stessa arità e significato opposto, chi
  lo scambia scrive un dato falso. Restano fuori peso e dimensioni: la
  nostra taglia del pacco è una categoria di corriere italiana, non un
  fatto oggettivo, e ricavarne un peso sarebbe inventare.
  DUE GUARDIE che i relay non scavalcano (decisione di Andrea): lo
  stock si LIMA a `MAX_QUANTITA_ANNUNCIO` (l'import scrive dritto nel
  DB e non passa dai giudici dei payload; si lima e non si scarta,
  come `quantita_tollerante` del CSV — la merce c'è, è il numero a
  essere fuori scala) e la CONSEGNA DIGITALE non arriva mai dai relay
  (il codice passa DENTRO Barattolo, con endpoint, rivelazione-
  ricevuta e finestre di 24/48h: chi sta solo su Nostr non ha quel
  bottone, e promettere una consegna immediata che nessuno può fare
  sarebbe una bugia scoperta a sats già in cassaforte. Chi entra con
  la sua chiave la dichiara dal form, dove anche DIGITALE_MIN_VENDITE
  può dire la sua). CONSEGUENZA da ricordare: un annuncio importato
  che dichiara `delivery` ora ENTRA nei set — «gli importati restano
  fuori per costruzione» non è più vero, ed è giusto così: il catalogo
  è uno solo, cambia solo chi firma l'evento.
  Il disegno è documentato in `proposte/` (la PR al repo dei NIP resta
  in backlog).
- `ricategorizza.py` (lug 2026) — l'AI PROPONE, l'admin decide. Quando
  il catalogo è passato da 9 voci a 25, gli annunci di ieri sono
  rimasti nelle caselle di ieri (un portatile in «Elettronica» invece
  che in «Informatica», una Jade in «Elettronica» invece che in
  «Bitcoin») e quelli che arrivano da Nostr nascono TUTTI in «Altro».
  Lo script legge titolo e descrizione degli attivi, li manda a Haiku a
  lotti da 20 e scrive SOLO nella tabella `categoria_proposta`
  (annuncio_id PK, categoria_ora, categoria_nuova, stato
  proposta|applicata|scartata, deciso_da/deciso_il = anche il registro
  di cos'è successo). `annunci.categoria` non la tocca MAI: a spostare
  è un moderatore, dalla coda. Il catalogo lo legge dal TESTO di
  server.py (fonte unica) e non importando il modulo, che farebbe
  partire init_db e le migrazioni su un database magari diverso da
  quello passato a mano. Di serie non scrive (`--scrivi` riempie la
  coda; `--limite N`, `--rifai`, e un percorso di database come per
  ripulisci_anello). L'AI può rispondere NON SO ed è importante che
  possa: un annuncio lasciato dov'è non fa danno, uno spostato male sì
  — e una categoria inventata o un id fuori lotto si ignorano come nel
  parsing della moderazione a lotti. Idempotente: non richiede gli
  annunci che hanno già una riga fatta sulla categoria che hanno
  ADESSO (se l'ha spostato il venditore, la vecchia proposta non parla
  più di lui e si richiede). Costo misurato: ~0,005 $ a lotto, ~0,20 $
  per 800 annunci, e lo stampa contando i token veri.
  LA CODA (`GET /api/admin/categorie`, `POST
  /api/admin/categorie/decidi`, sezione «🗂 Categorie da sistemare» nel
  Profilo admin): le proposte escono RAGGRUPPATE per spostamento
  («Elettronica → Informatica: 23»), col gruppo più numeroso in testa.
  Il raggruppamento non è una comodità: trecento decisioni una per una
  sono una revisione che nessuno finisce, e il vincolo di Andrea —
  nessuna categoria cambia senza che un umano l'abbia vista — si
  rispetta mostrando i TITOLI dentro il gruppo, con la spunta per
  togliere dal mucchio quello che non convince (`ids` nel body).
  L'UPDATE è condizionato sulla categoria di partenza (il secondo
  moderatore trova il fatto compiuto, come per la revisione) e una
  proposta stantia — categoria cambiata nel frattempo — sparisce da
  sola dalla coda. Dopo lo spostamento gli annunci NATI qui aggiornano
  il loro evento NIP-99 (la categoria è il tag `t`, `solo_aggiornamento`
  sul `d` stabile); niente promo e niente match, che ricategorizzare
  non è pubblicare — la regola della ricarica dello stock. Il
  venditore NON riceve avvisi: la categoria è metadato NOSTRO (dai
  relay non arriva, e l'import non la ricopre mai, che è anche ciò che
  fa sopravvivere la decisione al giro orario). Il complemento è
  l'invito OPT-IN che esisteva già: `_chiedi_completamento` aveva la
  voce «la categoria giusta» ma la sua WHERE guardava solo
  `consegna='' OR condizione=''`, quindi un annuncio completo fermo in
  «Altro» non veniva pescato mai e quella voce non partiva mai —
  aggiunto `OR categoria='Altro'`. La stessa funzione non chiede più
  la condizione dove non vuol dire niente.
  DA SOLA, DOPO OGNI IMPORT (lug 2026, `ricategorizza_automatico` in
  server.py, in coda a `giro_import_nostr`): lo stesso mestiere dello
  script, ma senza che nessuno lo lanci. Il momento è l'import e non un
  orario fisso perché è l'import a creare il problema — gli annunci dai
  relay nascono tutti in «Altro» — e girare a vuoto non costa niente.
  CHI SI GUARDA: gli importati (`contatto_nostr!=''`) e chiunque stia
  in «Altro»; i nativi in una categoria vera hanno avuto un umano che
  l'ha scelta dal form, e la macchina non è lì per correggere le
  persone. I TRE FRENI, che sono la ragione per cui può girare ogni
  ora: 1) DECISO È DECISO — un annuncio su cui un moderatore si è già
  pronunciato, approvando O rifiutando, non si ripropone mai più da
  solo (`p.stato IN ('applicata','scartata')`, qualunque categoria
  abbia adesso); 2) e non si ripaga due volte ciò che è già in coda:
  niente chiamata se esiste già una proposta in attesa sulla categoria
  di ADESSO; 3) `MAX_RICATEGORIZZA_GIRO` (100 = 5 chiamate), che
  un'ondata la digerisce in più ore.
  IL FRENO 1 È NATO DA UN BUG VERO (lug 2026, visto da Andrea, e vale
  la pena tenerlo perché la trappola è sottile). Il freno di partenza
  era il solo 2, cioè «esiste una riga fatta sulla categoria di
  adesso»: copre il RIFIUTO — l'annuncio resta dov'era, la riga
  combacia — ma NON l'APPROVAZIONE, perché appena l'annuncio si sposta
  in «Sport e hobby» la riga vecchia dice «Altro» e non lo protegge
  più. Così l'AI riproponeva altrove un annuncio che una persona aveva
  appena sistemato, a ogni giro; e la nuova proposta SOVRASCRIVEVA la
  riga, cancellando la traccia di chi aveva deciso — quindi il registro
  si consumava da solo e il danno diventava anche invisibile. Il raggio
  era ristretto ai soli IMPORTATI: un nativo approvato esce dal raggio
  d'azione da sé (non è importato e non è più in «Altro»), un importato
  ci resta per sempre. Cintura in più: l'INSERT della macchina ha un
  `WHERE categoria_proposta.stato='proposta'` sul DO UPDATE, così una
  riga decisa non si sovrascrive nemmeno se un domani la query se ne
  dimenticasse. CONSEGUENZA DICHIARATA: un annuncio deciso resta deciso
  anche se il venditore ne riscrive il titolo. Riaprirlo al cambio del
  testo (una colonna con l'impronta, come `_da_giudicare` fa per la
  moderazione) è stato valutato e scartato: per gli importati il testo
  lo riscrivono i relay ogni ora, quindi sarebbe lo stesso giro, solo
  più lento e più difficile da vedere. Per riconsiderare si chiede a
  mano, `ricategorizza.py --rifai` — e la stessa regola vale ora anche
  nel default dello script, dove `--rifai` è il modo di chiederlo
  ESPLICITAMENTE. Più la leva `RICATEGORIZZA_AUTO`
  nel config (default **True**, al contrario di IMPORT_NOSTR_APERTO: qui
  non esce niente verso nessuno — si riempie una coda che un moderatore
  guarderà, e in vetrina non cambia nulla finché non approva). UNA
  notifica aggregata ai moderatori per giro, coi GRUPPI e non i titoli
  (chi modera decide sul gruppo, e venti righe in chat non si leggono),
  e solo se quel giro ha prodotto qualcosa: una coda ferma non suona
  ogni ora. Il prompt e il parsing NON si riscrivono: `_chiedi_categorie`
  importa `PROMPT` e `RIGA` da ricategorizza.py, perché un prompt in due
  copie è un prompt che diverge — si corregge una, si dimentica l'altra,
  e la coda si riempie di proposte diverse secondo chi le ha chieste.
  Fail-open totale come la moderazione: lotto saltato = si riprova al
  giro dopo.
- `sposta_a_mano.py` (lug 2026) — gli spostamenti che decidi tu, quando
  l'AI ha sbagliato o ha detto NON SO. Prende `pezzo di titolo=Categoria`
  (o `id=Categoria`), pesca gli attivi e scrive le proposte in coda come
  se le avesse fatte l'AI. NON tocca `annunci.categoria`, ed è il punto:
  lo spostamento vero resta UNO — il bottone della coda — perché è lì
  che vivono l'UPDATE condizionato, l'aggiornamento dell'evento NIP-99 e
  il registro di chi ha deciso; riscriverlo qui vorrebbe dire tenere
  allineati due posti che fanno la stessa cosa. Di serie non scrive
  (stampa id, titolo, categoria di adesso e venditore, così un frammento
  troppo largo si vede PRIMA); un frammento che pesca cinque poster li
  mette in coda tutti e cinque, ed è voluto.
- `ripulisci_anello_nostr.py` (lug 2026) — la pulizia una-tantum dopo
  l'anello (vedi sopra). Riconosce le copie dal marchio che solo NOI
  scriviamo — il tag `d` di un evento nostro è sempre `barattolo-{id}`,
  e l'id lì dentro è l'annuncio VERO da cui la copia discende, quindi
  ogni copia si lega al suo originale senza indovinare nulla. Di serie
  NON scrive: stampa cosa farebbe; accetta un percorso di database, e
  la prova generale si fa su una copia del file. Spegne le copie
  ('rimosso'), annulla gli ordini mai pagati, e NEUTRALIZZA il
  fantasma togliendogli le chiavi Nostr senza cancellarne la riga (una
  riga di utenti cancellata lascerebbe riferimenti ciechi in annunci,
  ordini e registro). MAI una NIP-09 verso i relay: quegli eventi sono
  i nostri, quelli degli annunci VERI — ritirarli cancellerebbe dalla
  piazza la merce buona. Tre guardie, e si ferma dicendolo: copia con
  affare in corso, account che ha anche annunci suoi (è una persona
  vera che ha raccolto copie per sbaglio), account con copie vive o
  ordini APERTI — quelli chiusi invece non fermano niente, la storia è
  storia e lasciargli la chiave vorrebbe dire tornare a importare per
  sempre. Idempotente.
- `prove.py` + `.github/workflows/prove.yml` (lug 2026) — la rete di
  sicurezza, a ogni push e ogni PR. Solo pezzi PURI: niente config,
  database, relay o Anthropic — una CI che dipende da un server altrui
  diventa rossa quando quello ha il raffreddore, e a furia di rossi
  ingiusti si smette di guardarla. Le funzioni si estraggono da
  server.py per TESTO (`pezzo()`), senza importarlo: chi rifattorizza
  una funzione estratta deve aggiungere anche le sue dipendenze
  all'ambiente (è già successo con `_chiave_comune`, che
  `coordinate_da_zona` ha cominciato a usare). Il workflow fa anche
  `compileall` di tutti gli script (elenco a mano: chi ne aggiunge uno
  lo mette lì, o non lo guarda nessuno — ai tre nati il 3 ago 2026 è
  successo) e cerca segreti nella repo (la regola ferrea 1 in CI:
  `config.py`/`*.db`/`foto/` tracciati, nsec, token del bot Telegram e
  chiavi `sk-ant-`; lunghezze LARGHE apposta — meglio un falso allarme
  da guardare che un token vero che passa perché era un carattere più
  corto — e `grep -I` che salta i binari, o un byte messo per caso in
  una delle 52 illustrazioni fa diventare rossa la CI a caso, e una CI
  rossa a caso non la guarda più nessuno).
  DUE JOB E NON UNO (lug 2026, e il perché vale più della struttura):
  `prove` e `segreti` girano in PARALLELO, senza `needs`. Il controllo
  dei segreti era l'ultimo passo in coda alle prove, e da lì qualunque
  cosa fallisse prima lo nascondeva — non diceva «pulito» a torto: non
  parlava proprio. È successo per davvero: le prove si sono rotte alle
  13:20 del 3 ago 2026 e per 13 push di fila i segreti non li ha
  guardati nessuno, mentre GitHub diceva soltanto «rosso» — un semaforo
  solo per due domande diverse. Provato rompendo `prove.py` di
  proposito su un ramo usa-e-getta: `prove` fallito, `segreti` riuscito
  che dice «pulito». Entrambi `permissions: contents: read`.
  GLI SCRIPT «PURI» NON CHIEDONO IL CONFIG ALL'IMPORT, ed è LA regola
  che impedisce il bis. Chi importa un modulo per una costante non deve
  ritrovarsi il processo chiuso in faccia per una chiave che non gli
  serve: `ricategorizza.py` faceva `from config import DB,
  ANTHROPIC_API_KEY` in cima al file con un `sys.exit(1)` sotto, e
  `prove.py` lo importa per `catalogo()`, `PROMPT` e `RIGA` — roba pura
  che di chiavi non sa niente. In CI `config.py` non c'è PER PROGETTO,
  quindi le prove morivano sempre. Il config si chiede dentro `main()`
  (il modo di `sposta_a_mano.py`, che ha pure il ripiego a
  'satmarket.db'); il ripiego innocuo, tipo `MODELLO_RICERCA`, può
  restare in cima perché non chiude niente ed è un nome globale che
  serve alle funzioni. ATTENZIONE alla trappola che rende questa
  famiglia di bug invisibile: IN LOCALE PASSA SEMPRE, perché il config
  c'è — le 78 prove erano verdi sul portatile mentre la CI era rossa da
  nove ore. Non è una cosa che si becca girando le prove prima del
  push: si becca solo GUARDANDO la CI (`git push && sleep 4 && gh run
  watch --exit-status`), o provando in un clone senza `config.py`, che
  è la condizione vera.
  Su Windows serve `PYTHONIOENCODING=utf-8`,
  o la console cp1252 esplode sulle spunte.

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS).
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
- La coda delle categorie si riempie da sola dopo ogni giro d'import
  (leva `RICATEGORIZZA_AUTO`, accesa di serie): nel journal la riga
  «🗂 Ricategorizzazione: N guardati, M proposte in coda», e ai
  moderatori arriva una notifica sola coi gruppi. Non cambia niente in
  vetrina finché un moderatore non approva. Per spegnerla, `False` nel
  config del VPS e riavvio.
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
- Il Login Widget esige il dominio registrato: BotFather → `/setdomain`
  su @ilbarattolobot → `barattolo.store` (senza, il bottone non compare;
  su localhost non compare mai: si collauda col bottone "cookie web").
- Deploy: commit+push su main → sul server `cd satmarket && git pull &&
  systemctl restart barattolo`. Config e database NON viaggiano mai.
- Webhook del bot: `TELEGRAM_WEBHOOK_SEGRETO` nel config del server
  (stringa casuale) e al riavvio si registra da solo (riga «🔔 Webhook
  Telegram» nel journal). ATTENZIONE: mai avviare MODALITA_COLLAUDO=False
  col BOT_TOKEN vero fuori dal VPS — ruberebbe il webhook (e quindi i
  /start) alla produzione.
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

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente. La scala approvata: badge npub auto-dichiarato →
   verifica con nota pubblica (fatta, lug 2026) → login Nostr con firma
   di sfida (fatto, lug 2026: la nsec incollata nel login web firma
   SOLO nella pagina, mai trasmessa né salvata, e la UI la sconsiglia
   a favore di estensione/bunker — è l'estensione approvata della
   scala, NON un'eccezione) → wallet NWC solo-nel-browser (lug 2026:
   la stringa nostr+walletconnect:// è una credenziale di SPESA e
   vive solo in localStorage del dispositivo, mai sul server — un
   suo salvataggio server-side, anche cifrato, farebbe della
   piattaforma il custode dei wallet di tutti: da respingere) →
   DM di notifica NIP-17 (lug 2026: si CIFRA verso la chiave
   PUBBLICA dell'utente e si firma con la chiave della piattaforma,
   nessun segreto altrui coinvolto) → sessione bunker NIP-46
   conservata (lug 2026: URI + chiave del CLIENT in localStorage del
   dispositivo, pari grado del secret NWC — chiede firme al bunker,
   che può negarle o revocare; NON contiene né può derivare la chiave
   dell'utente, mai sul server) →
   mai custodia di segreti altrui, mai firme che richiedano di
   consegnare chiavi al server.
3. Il server pubblico serve SOLO `/`, `/miniapp.html`, `/negozio/*`,
   `/annuncio/*`, `/foto/*`, `/vendor/nostr.js`, `/vendor/qrcode.js`,
   `/assets/categorie/{slug}.webp` (le 27 illustrazioni di Sfoglia:
   unica rotta con un nome che arriva dal client, e per questo la sola
   con una whitelist — `SLUG_CATEGORIE`, calcolata dal catalogo),
   `/assets/mascotte.jpeg`,
   `/assets/barattolo.jpeg`, `/assets/barattolo-hero.png`,
   `/assets/tappo.jpeg`, le rotte PWA (`/manifest.json`, `/sw.js`,
   `/offline.html`, `/assets/icona-192.png`, `/assets/icona-512.png`,
   `/assets/icona-192-maskable.png`, `/assets/icona-512-maskable.png`,
   `/assets/apple-touch-icon.png`) — tutti file singoli, rotte
   esplicite — e `/api/*`. Non montare mai StaticFiles sull'intera
   directory (config e .git diventerebbero pubblici — falla già
   successa e chiusa).
4. Stati ordine: creato | locked | shipped | delivered | confirmed |
   released | dispute | return_pending | return_shipped | refund |
   refunded | annullato. Non inventarne di nuovi senza aggiornare
   frontend (STATES, stepper cassaforte) e notifiche.
5. Solo l'ACQUIRENTE può segnare "consegnato" (anti-frode venditore).
   Il venditore è protetto dall'auto-sblocco a 10 giorni e dal sollecito
   (max 1 ogni 24h).
6. Testare sempre in locale (MODALITA_COLLAUDO=True, tre identità finte:
   Compratore 111, Venditore 222, Admin 999) prima del deploy.
   In produzione MODALITA_COLLAUDO deve restare False.
7. Stile del codice esistente: commenti e nomi in italiano, tono caldo,
   niente refactoring di massa non richiesti, diff piccoli e verificabili.
8. A fine cantiere, PRIMA del commit finale, valuta se il lavoro ha
   cambiato architettura, API, schema del database o regole del progetto:
   se sì, proponi l'aggiornamento di CLAUDE.md come commit separato,
   senza aspettare che Andrea lo chieda. Ritocchi minori (testi,
   tarature, fix) non lo richiedono.
9. Lessico dell'escrow (lug 2026): nei testi per gli utenti si dice
   sempre «deposito di garanzia» — «(escrow)» solo nella prima
   spiegazione lunga di ogni contesto; azione = «🔒 Compra in
   sicurezza» (era «Compra protetto», cambiata lug 2026);
   MAI «assicurato». «Escrow» resta solo dove il pubblico è bitcoiner:
   memo della invoice LNbits e testi verso Nostr (footer NIP-99,
   presenta_release). Il barattolo 🫙 è dei preferiti, mai metafora
   dell'escrow.

## Stato (lug 2026) e prossimi lavori

Lanciando in rodaggio su community italiana, senza limiti di prezzo
attivi (la leva `TETTO_SATS_ANNUNCIO` esiste ma è spenta, vedi sotto).
Fatti (lug 2026): banner sulla demo browser; vetrina pubblica in sola
lettura (annunci veri dal browser, azioni → invito al bot); moderazione
contenuti a tre strati (parole + AI + admin); badge npub auto-dichiarato
nel profilo e sugli annunci; verifica della npub via nota pubblica
(badge 🟣, dal lug 2026 pubblico SOLO da verificata e senza ✓, vedi
Architettura); pubblicazione degli annunci verso
Nostr con la chiave della piattaforma (NIP-99 + NIP-09, vedi
Architettura); pagina negozio del venditore, interna e pubblica
(`/negozio/{username|codice}`, vedi Architettura); login web col
Telegram Login Widget (sessioni cookie, app completa dal browser,
vedi Architettura — ricordarsi `/setdomain` su BotFather); login web
con Nostr (estensione NIP-07, bunker NIP-46, nsec solo-in-pagina;
tg_id negativi e npub_accesso, vedi Architettura — gli utenti Nostr
per ora restano senza notifiche: le vedono nei loro Affari); scudo
anti-XSS `esc()` su tutti i template; Compra subito col wallet NWC
(NIP-47 lato client, secret solo in localStorage, vedi Architettura
— il percorso felice va collaudato con un wallet vero a budget
minuscolo: in locale è verificato il ripiego, non il pagamento);
doppia cittadinanza completa (righe identità nel cassetto
«🆔 Identità» del Profilo,
badge verificato promuovibile a chiave d'accesso, webhook /start del
bot e fusione atomica Nostr→Telegram, vedi Architettura — in
produzione va provata una fusione vera con un account di test);
notifiche via DM Nostr NIP-17 con scelta del canale (i nativi Nostr
finalmente ricevono gli avvisi, cassetto «🔔 Avvisi» nel Profilo, vedi
Architettura — la cifratura è verificata contro nostr-tools, ma in
produzione va provato un DM vero verso la propria npub su 0xchat o
Amethyst; sul VPS serve `pip install cryptography`); modifica annuncio
del venditore (form di Vendi riusato, moderazione completa,
ripubblicazione Nostr, vedi Architettura); foto HEIC/HEIF e WebP
accettate e convertite in JPEG (client via canvas quando può, server
con Pillow altrimenti — sul VPS serve `pip install pillow
pillow-heif`); scheda Profilo 👤 (tutto ciò che
riguarda l'utente trasloca lì da Vendi, che torna solo form di
pubblicazione; Lightning address impostabile anche da lì; canale
avvisi sempre in chiaro; dal lug 2026 riorganizzata a cassetti
richiudibili stile Vinted, testata sempre visibile e npub+verifica
riuniti nel cassetto identità; vedi Architettura); feedback e stelle
(voto 1-5 + commento a affare concluso, rating per ricalcolo,
ultimi feedback anonimi nel negozio, rimozione admin, vedi
Architettura — parte 1 della gamification); distintivi 🏅 (parte 2:
11 badge auto-assegnati per ricalcolo dai dati veri, cassetto con
griglia e conteggio «N di M» nel Profilo, chip di fiducia nel negozio
pubblico, retroattivi a ogni
avvio, vedi Architettura); badge 🟣 pubblico semplificato (solo da
npub verificata, senza ✓; il non verificato lo vede solo il
proprietario col suo invito a verificare); export CSV contabile
degli affari conclusi (bottone nel Profilo, controvalore EUR
valorizzato alla chiusura da ora in poi, vedi Architettura);
doppia valuta (lug 2026: listino in sats o in EUR a scelta del
venditore, toggle ₿/€ per chi guarda, pagamento sempre in sats col
cambio bloccato dalla vita della invoice, e la leva del tetto per
annuncio con tolleranza +20% sul drift, vedi
Architettura — collaudato in locale da cima a fondo; la riga EUR
nella ricerca AI va provata in produzione, dove la chiave Anthropic
è vera; la leva del tetto `TETTO_SATS_ANNUNCIO` esiste nel codice
ma è SPENTA di default: nessun annuncio viene limitato finché non
la si accende dal config); onboarding contestuale (lug 2026:
suggerimenti discreti al momento del bisogno — wallet NWC nel
paySheet, Lightning address e verifica npub dopo la pubblicazione —
più la checklist «Completa il profilo (N di M)» nel Profilo; «Non
ora» memorizzato in localStorage, mai in demo/vetrina, vedi
Architettura); redesign «mercatino di paese» (lug 2026: palette crema/
arancio/verde sigillo, Baloo 2+Nunito, card «Etichetta», bottoni con
ombra piena, recinto escrow tratteggiato, festa dei sats, mascotte e
barattolo con route /assets, favicon e hero desktop, vedi
Architettura — collaudato in locale su tutte le viste e i tre
viewport; da rivedere dal vivo dentro Telegram dopo il deploy);
dark mode «mercatino di sera» (lug 2026: token scuri su fondo bruno
caldo, toggle Auto/Chiaro/Scuro nel cassetto «🌗 Aspetto» del Profilo,
tg.colorScheme dentro Telegram, vedi Architettura — collaudata in
locale con contrasti AA misurati; da provare dal vivo dentro Telegram
col tema scuro e il cambio tema a app aperta); tre completamenti del
redesign (lug 2026: etichetta prezzo sempre di carta chiara anche in
dark, medagliette di fiducia del venditore nella scheda annuncio via
`venditore_distintivi`, pillola-contatore «🏅 N/M» accanto al lockup
per gli autenticati, vedi Architettura); cinque ritocchi dal feedback
dei tester (lug 2026: via la pillola-contatore, al suo posto il
tasto-tappo del Profilo in testata e nav a 3 voci; searchbar che
cerca con Invio senza bottone; ✕ «ho capito» sul banner web; il
cassetto «🆔 Identità» perde il «e Nostr» — vedi Architettura,
redesign — collaudati in locale su mobile e desktop, chiaro e scuro,
web/vetrina/demo); categorie nuove a 9 voci con pillole ordinate per
contenuto (lug 2026: catalogo `CATEGORIE`, migrazione idempotente,
vuote nascoste, vedi Architettura — collaudate in locale con
migrazione sui dati veri; la ricerca AI col set nuovo va provata in
produzione, dove la chiave Anthropic è vera); tenuta al volume
(lug 2026: paginazione keyset su vetrina/negozio/miei con scroll
infinito, indici su annunci, miniature `_min` per le card con
backfill all'avvio, cache di un giorno su /foto, shortlist a 300
della ricerca AI, ricerca semplice anonima lato server e GET del
singolo annuncio per i link condivisi, vedi Architettura — misurato
in locale con 814 annunci seminati: pagina 25× più leggera di prima
[17KB vs 436KB], query tutte sugli indici, card da ~8-25KB invece
del JPEG pieno; da rivedere dal vivo dentro Telegram dopo il deploy,
e la shortlist AI va provata in produzione con la chiave vera);
modifica firmata degli annunci importati (lug 2026: il doppio
cittadino aggiorna i suoi eventi NIP-99 da Barattolo — due fasi con
moderazione prima della firma, firma nel browser col firmatario del
login, pubblicazione sui relay dal client e copia locale allineata
subito; l'import impara il match per tag `d` e le colonne origine,
vedi Architettura — collaudato in locale da cima a fondo, casi
negativi compresi; in produzione va provata una modifica vera con la
chiave del venditore consenziente, verificando su njump che l'evento
sostituisca il vecchio anche sul suo relay personale); deduplica dei
doppioni su Nostr (lug 2026: era nel backlog, sbloccata dal match a
impronta stretta — cassetto «🔁 Doppioni su Nostr» nel Profilo con le
coppie sospette, ritiro NIP-09 solo della copia della piattaforma con
conferma esplicita, «non è un doppione» persistente in
`doppioni_ignorati`, messaggio mirato del bot dopo la fusione, vedi
Architettura — collaudata in locale da cima a fondo, casi negativi e
soglie comprese; in produzione va provato un ritiro vero verificando
su njump che sparisca SOLO l'evento della piattaforma e che
l'originale del venditore resti); import in blocco da CSV (lug 2026:
cassetto nel Profilo per i commercianti — 70 negozi in arrivo al
lancio — con modello scaricabile, foto da URL o ZIP, moderazione
COMPLETA con AI a lotti, anteprima e conferma esplicita, job
asincrono con avanzamento e report, Nostr a lotti lenti con opt-out,
vedi Architettura — collaudato in locale da cima a fondo, TestClient
e browser; in produzione va provato un import vero con la chiave AI
e un catalogo reale, e il download del modello da dentro Telegram);
post automatici dei fatti (lug 2026: nota Nostr kind-1 + post nel
canale Telegram per ogni nuovo annuncio, anti-spam a drenatore con
aggregato per le raffiche, ciclo di vita ✅ Venduto/cancellazione,
vedi Architettura — collaudato in locale con 13 verifiche simulate;
in produzione serve creare il canale, mettere il bot come admin e
`TELEGRAM_CANALE_ID` nel config del VPS, poi verificare un post vero
su canale e relay); avvisi di ricerca personalizzati (lug 2026:
criteri salvati nel cassetto «🔎» del Profilo — categorie, comune con
raggio km sul dataset comuni committato, prezzo max, parole chiave —
matching alla pubblicazione col gemello della coda promo,
anti-molestia a tre strati (dedup persistente, aggregato per le
raffiche, tetto giornaliero) e CTA «Avvisami se arriva» dopo la
ricerca a vuoto, vedi Architettura — collaudato in locale da cima a
fondo: matching positivo e negativi per ogni criterio, distanze
Milano/Monza/Pavia/Napoli, dedup sulla modifica, aggregato da
raffica, tetto col messaggio onesto, form/pausa/elimina/precompila
nel browser; in produzione va provato un avviso vero con notifica
Telegram reale); gestione completa della npub nel Profilo (lug 2026:
bottone «Rimuovi la npub dal profilo» con conferma, guardia per il
nativo Nostr che ne sarebbe chiuso fuori, canale avvisi riportato
all'automatico quando la destinazione Nostr sparisce, sottotesti che
distinguono le due leve Disabilita/Rimuovi, vedi Architettura, badge
Nostr — collaudato in locale con TestClient [31 verifiche] e nel
browser su tutti gli stati della riga Nostr); dettaglio annuncio
immersivo e preferiti col barattolino (lug 2026: foto a filo con
ritorno flottante, lightbox a tutto schermo con pinch/rotella/swipe
in vanilla JS, cassetto «🫙 Nel tuo barattolo» primo nel Profilo con
gli stati onesti dei non più disponibili, vedi Architettura —
collaudato in locale su mobile e desktop, chiaro e scuro, con
venduto nel mezzo e DEMO/vetrina senza barattolino; il pinch va
riprovato dal vivo su un telefono vero dentro Telegram); PWA
installabile — Fase 1 (lug 2026: manifest con le icone del barattolo
su tessera arancio, service worker prudente con pagina offline e
mascotte, banner «installa» discreto solo su web mobile, dentro
Telegram tutto identico per costruzione, vedi Architettura —
collaudato in locale: dispensa completa senza /api, offline vero a
server spento, guardie del banner esercitate una a una, demo file://
pulita; in produzione vanno provate l'installazione vera su Android
e iPhone e la verifica del widget Telegram in standalone, il cui
esito decide l'eventuale piano di riserva redirect); APK distribuito
sui due canali pubblici (lug 2026, Fase 3: release v1.3 su
github.com/kreamistudio-crypto/barattolo-releases per Obtainium e
download diretto, e su Zapstore con chiave Nostr dedicata fredda e
certificato legato via NIP-C1 — eventi verificati sul relay, hash e
certificato coincidenti; vedi «Distribuzione dell'APK» — restano da
fare: screenshot nella scheda Zapstore, profilo kind-0 dell'identità
release, e la prova d'installazione dallo store sul telefono); avatar
dal social di provenienza (lug 2026, richiesta di Alan: la foto
profilo Telegram o la picture del kind-0 Nostr come francobollo 128px
servito da foto/, catena Telegram→Nostr→iniziale per i doppi
cittadini, selettore «La tua foto» nel cassetto Identità —
Telegram / Nostr / Nessuna, voci solo per le sorgenti vere, default
la catena automatica — vedi Architettura — collaudato in locale: 12
verifiche server comprese la gamba Nostr sui relay veri, rendering e
ripieghi nel browser, selettore avanti e indietro con la validazione
delle sorgenti; in produzione va vista una foto Telegram vera, che
in collaudo il bot simulato non può dare); cartello «fase di test»
all'apertura (lug 2026: modale col velo sfocato, testo e link del
canale scritti nel config, una volta al giorno per dispositivo,
precedenza sul tour di benvenuto, vedi Architettura — collaudato in
locale in tutti gli stati [acceso, spento, link vuoto o storto,
server muto, stesso giorno, giorno nuovo], chiaro e scuro, mobile e
desktop, demo e vetrina; a rodaggio finito si spegne con
`BANNER_TEST = False` nel config del VPS e un riavvio); spedizione e
protezione acquisti modello Vinted (lug 2026: modalità di consegna,
costo spedizione nella valuta del listino e taglia del pacco
sull'annuncio, conto scomposto a carico del compratore col totale in
cassaforte, ritiro in zona senza stati nuovi, filtro «solo con
spedizione», leva `PROTEZIONE_PERCENTO` SPENTA di serie, vedi
Architettura — collaudato in locale: 72 verifiche TestClient sui
quattro strati compreso il giro completo a tre identità con
spedizione EUR, ritiro con auto-sblocco a 72h/10gg e annuncio
storico, più il giro visivo in Chrome headless su chiaro e scuro; in
produzione va rivisto dal vivo dentro Telegram, e quando la
protezione si accenderà dal config vanno decisi i testi con la
cifra); offerte e contrattazione sul prezzo (lug 2026, modello
Vinted: foglio con chip −10%/−20% e stima live, una sola
controproposta, accettazione = 24h per pagare col flusso di sempre
alla cifra pattuita, l'annuncio non si blocca mai e vince chi paga,
sezione «💰 Offerte» in testa alla scheda Ordini col pallino sul nav,
leve config 50%/48h/24h/3, vedi Architettura — collaudato in locale
con 51 verifiche TestClient sui quattro strati: giro pieno sats con
controproposta, giro EUR con virgola e cambio_ordine, anti-abuso
completo, decadenza per vendita, sweep delle scadenze, reaper con
ripagamento, modifica prezzo, regressione dell'acquisto normale; in
produzione va provato un giro vero dentro Telegram con le notifiche
reali); offerta lampo ai barattoli (lug 2026, modello Vinted «sconto
ai follower»: avviso anonimo «ha fatto colpo» al venditore quando
qualcuno salva, sconto pubblico a percentuale e a tempo lanciato dal
foglio del dettaglio, avviso mirato a chi ha l'annuncio nel barattolo,
badge col countdown e prezzo barrato in vetrina e dettaglio, filtro e
ordinamento «⚡ In offerta», minimo con l'accordo individuale in
compra(), scadenza che ripristina tutto da sola anche a pagina
aperta, leve nel config, vedi Architettura — collaudato in locale da
cima a fondo: valvola e cooldown in console, guardie del lancio una a
una, acquisto scontato sats ed EUR, min nei due versi, superficie
pubblica con cursore, e il giro visivo nel browser vero via CDP da
venditore e in demo; in produzione va provato un giro vero dentro
Telegram con le notifiche reali); lampo e offerte anche sugli annunci
importati da Nostr (lug 2026, decisione di prodotto: il catalogo e' uno
solo, la differenza tra nato-qui e nato-su-Nostr e' SOLO chi firma
l'evento NIP-99 — via le guardie contatto_nostr da fai_offerta,
lancia_lampo e _drena_colpo e i due l.nostr dal dettaglio; porta
«🟣 …o entra con Nostr» nel foglio invito della vetrina per il
percorso DM → link → login npub → azione; la guardia di modifica_annuncio
resta: il contenuto degli importati si cambia sui relay, la lampo e'
un'altra strada che non lo tocca; vedi Architettura, offerte e lampo —
collaudato in locale con 16 verifiche TestClient su DB usa-e-getta:
giro offerta completo sull'importato con cifra pattuita nell'ordine,
lampo lanciata/comprata scontata/annullata, «ha fatto colpo» arrivato
al venditore dell'importato, regressioni su nativo e guardie
sopravvissute; in produzione va provato il giro vero: DM NIP-17 con
link a un venditore solo-Nostr, login npub dal foglio invito e
risposta all'offerta); consegna digitale 💾 (lug 2026: quarta modalità
per buoni regalo, codici e licenze — il contenuto passa dentro
Barattolo con consegna tracciata e rivelazione-ricevuta, cifratura a
riposo fail-open, finestre corte 24/48h, regola asimmetrica dichiarata
e leve anti-frode spente di serie, servizi esclusi dalla moderazione
col messaggio gentile e prodotti digitali leciti in whitelist, vedi
Architettura — collaudato in locale con 58 verifiche TestClient su DB
usa-e-getta: giro completo consegna→rivela→sblocco 24h, silenzio 48h,
regressione dei rami fisici, cifratura nei due formati, disputa con
nota admin, leve accese e spente, import CSV e NIP-99; in produzione
va provato un giro vero dentro Telegram, la voce «buono
regalo/servizio» della moderazione AI con la chiave vera, e sul VPS va
scelta CHIAVE_CONTENUTI_DIGITALI nel config — senza, i codici restano
in chiaro nel DB, dichiarato; dal lug 2026 anche in COMBO con una
modalità fisica via `anche_digitale`: il compratore sceglie la strada
con le pillole e le tutele seguono la sua scelta, vedi Architettura —
collaudata con 32 verifiche TestClient: tutele digitali sul ramo
digitale e fisiche sul ramo fisico dello STESSO annuncio, default
fisico per i client vecchi, guardie, NIP-99 e CSV col «+»); regione
derivata e cercabile (lug 2026: nessun campo nuovo nel form — la
regione si ricava dalla sigla della provincia con una mappa fissa,
colonna sua scritta accanto alle coordinate e backfill all'avvio, voce
«Regione» nel pannello Filtri con le sole regioni che hanno annunci e
il loro numero, vedi Architettura — collaudata in locale con 42
verifiche TestClient su DB usa-e-getta [mappa, pubblicazione, modifica,
import CSV, filtro combinato e paginato, risposta legacy, backfill
idempotente] e il giro nel browser vero su chiaro e scuro, coi dati
veri e in demo; in produzione basta il riavvio: la migrazione e il
backfill girano da soli); barra d'acquisto al posto della tab bar nel
dettaglio (lug 2026, modello Vinted: aperto un annuncio comprabile la
tab bar lascia il posto a «Compra in sicurezza» col totale e
«Offerta», stessa altezza e stessa carta — niente salto di layout —
con i gemelli in pagina spenti su mobile e il recinto escrow lasciato
alle spiegazioni; guardie e cifre riusate tal quali, da desktop non
esiste, vedi Architettura — collaudata in locale a 360/375/1280px e nei
due temi: altezza allineata, lampo −20% e cambio consegna sulla cifra,
invito in vetrina, annuncio proprio con la tab bar intatta, fogli e
lightbox che le passano sopra; in produzione va rivista dal vivo dentro
Telegram, dove contano la gesture bar del telefono e il tema del
client); il varco della barra (lug 2026, subito dopo: la barra si
raggiunge senza scorrere e comprava con la consegna decisa in silenzio
— ora la barra dice sempre la strada quando ce n'è più d'una, e il
primo tocco a scelta implicita apre il foglio «Come vuoi riceverlo?»
coi totali per strada, che scegliendo chiude e procede in un gesto
solo, vedi Architettura — collaudato in locale col giro vero a 360px:
foglio, scelta, paySheet coerente, secondo tocco diretto, Escape senza
ordine, combo digitale, vetrina e regressione dei picker); quantità in
stock per annuncio (lug 2026: campo quantità nel form Vendi, stepper e
conto × N all'acquisto con spedizione una volta sola, esaurito = stato
venduto con «Rimetti in vendita» dai tuoi annunci, prenotazione
derivata dagli ordini 'creato' che chiude anche il buco storico del
doppio acquisto — deployata per prima, da sola —, offerte a prezzo
unitario, riga «disponibili» nel NIP-99 e colonna CSV, vedi
Architettura — collaudata in locale con 60 verifiche TestClient su
quattro script [prenotazione con rivale nell'await, parziale/
esaurimento/decadenze, rimborso e ricarica, superficie e import] più
il giro nel browser vero a 375px con invoice LNbits reale; è il
mattone del futuro cantiere «set»); il set «Riempi il barattolo»
(lug 2026: più annunci diversi dello stesso venditore in un ordine
solo — sezione «Altri oggetti di questo venditore» nel dettaglio,
foglio di composizione con spunte e stepper, UNA spedizione al MAX
dei costi dichiarati con la stima della taglia del pacco solo
informativa, un escrow e una conferma con disputa/rimborso
tutto-o-niente dichiarati, modello testata+ordine_righe coi mono
intonsi byte per byte, vedi Architettura — collaudato in locale con
97 verifiche TestClient su quattro script [fondamenta e guardie,
compra a righe con EUR/offerte/lampo e 409 col nome del pezzo,
ciclo di vita completo con rimborso che riattiva tutto, tabella dei
casi della stima taglia] più il giro nel browser vero con invoice
LNbits reale, vista compratore e venditore e il rivale che soffia
il pezzo a metà composizione; in produzione va provato un set vero
dentro Telegram con le notifiche reali; gli SCONTI SET alla Vinted
sono il cantierino successivo, deciso: la preparazione è
l'invariante articolo = Σ unitario×qta, lo sconto sarà una voce di
testata); card più stretta e dettaglio spogliato (lug 2026: in card
le icone si raggruppano a destra e la zona si mostra solo se è un
LUOGO vero; nel dettaglio restano luogo, consegna, condizione,
disponibilità e Nostr, mentre escono categoria, taglia del pacco,
«protezione acquisti inclusa» e il costo dalla pillola della
spedizione, che vive già nel foglio della consegna e nel conto
scomposto; collaudato a 360/375/390 e 1280px, chiaro e scuro);
il luogo si fa pulito, dentro e fuori (lug 2026, subito dopo: il
pallino Nostr esce dalle card — riguarda il venditore, non
l'oggetto, e in griglia lo spazio è poco; si mostra il solo COMUNE
estratto dal dizionario invece del testo intero — in card, e dal
giorno dopo anche nella pillola del dettaglio e nelle righe-elenco
del Profilo: una regola sola ovunque, vedi in Architettura perché
tenere il testo intero nel dettaglio non era tenibile; e in INGRESSO
la zona, pur restando facoltativa senza
ritiro, dev'essere un comune vero — l'avviso morbido del form e
dell'import CSV è diventato bloccante, con un messaggio unico e il
«forse Pavia (PV)?»: chi spedisce e basta lascia il campo vuoto,
niente più «spedisco in tutta Italia» nel campo Zona. Superficie
API: `zona_comune` in CAMPI_VETRINA, che ASSORBE il
`zona_riconosciuta` del giorno prima — il nome è anche il flag —
calcolato nel collo di bottiglia `arricchisci_righe_vetrina`; zero
colonne nuove, in produzione basta il riavvio. Conseguenza
dichiarata: gli annunci storici con la zona storta si mettono in
regola alla prima modifica, come per la condizione. Vedi
Architettura per il vincolo del cuore unico `_chiave_comune`, che
serve al prossimo cantiere. Collaudato con 16 casi mirati più
l'invariante su tutto il dataset [7.904 comuni × 3 forme], 9 casi
TestClient sulla guardia, l'anteprima CSV, i 6 stati della riga di
hint e il gate end-to-end contando le POST); riordino del dettaglio
annuncio stile Subito.it (lug 2026: data relativa sotto la foto con la
colonna `annunci.modificato` e la leva GIORNI_DATA_ANNUNCIO, titolo
con la condizione accanto, luogo come testo nudo, badge azzurro
«Spedizione disponibile» accanto al prezzo con le altre strade
discrete, titolino «Descrizione», e il 🟣 dentro il riquadro
venditore, vedi Architettura — collaudato in locale via CDP a
360/375/390 e 1280px nei due temi e con reduced-motion, sui casi
senza luogo / senza spedizione / solo digitale / lampo attiva /
annuncio storico; in produzione basta il riavvio, la migrazione gira
da sola; più le quattro rifiniture del giorno dopo: badge spedizione
sulla stessa riga del prezzo, 🟣 solo icona in fila coi badge, via i
ponti di contatto dal riquadro venditore; e le correzioni del giorno
dopo ancora: «Acquista» arancio ₿ NUDO senza prezzo — solo lui e
centrato dentro il recinto escrow, «Fai un'offerta» fuori sotto — e
nella barra fissa i due tasti gemelli piatti (offerta a sinistra)
col richiamo tratteggiato verde e il lucchettino, via le
pillole di scelta consegna dal dettaglio (la strada si sceglie nel
foglio del varco, che diventerà la pagina dedicata del prossimo
cantiere), forme rettangolari col raggio del riquadro su TUTTI i
bottoni del dettaglio — riverificate a 360/375/390 nei due temi,
col varco esercitato dal vivo); il recinto parla poco e la spedizione
si vede (lug 2026: «Acquista» un gradino più grande e i due tasti
della barra finalmente gemelli — il tratteggio diventa un outline che
non occupa layout e le basi flex vanno al 50%, la stessa lezione dei
bottoni del pannello Filtri; la spedizione a due gradi dello stesso
azzurro nel solo chip «Spedizione gratuita» sopra il prezzo — le altre
strade restano pillole normali, perché il colore veste solo ciò che è
un vantaggio — con «🚚 gratis» scritto in vetrina; il gemello col costo sotto
Acquista è nato e morto nello stesso cantiere: il recinto è il posto
della fiducia, non del listino; il recinto ridotto a una riga,
via la riga sulla invoice, e tutto il resto nella pagina nuova «Il
pagamento protetto» raggiungibile da tre porte; i tempi dell'escrow
raccolti nella costante `TEMPI` con la tabella delle leve accanto —
erano sparsi in dodici stringhe; più «Riempi il pacco» col nuovo
accento cartone e lo «Scopri di più» in inchiostro. Vedi Architettura
— collaudato in locale via CDP a 360/375/390 e 1280px nei due temi,
sui casi spedizione a pagamento / gratuita / ritiro / digitale /
storico / lampo / multi-pezzo, in vetrina anonima, in DEMO e col
wallet NWC collegato, con le tre porte e i loro ritorni, il tour
ancora intero e zero errori JS; contrasti misurati AA su tutti i
token nuovi. In produzione basta il deploy: nessuna colonna, nessuna
leva nuova. RESTA DA DECIDERE A RODAGGIO: i testi della pagina sono
scritti oggi con la commissione sospesa e la protezione spenta —
quando si accenderanno vanno riletti, in particolare «Se qualcosa va
storto» e «Dove stanno i sats»); il gesto indietro torna indietro
(lug 2026: dentro Telegram, nella PWA e nel browser il tasto/gesto
indietro non chiude più l'app — prima chiude i fogli, poi smonta le
viste, e si esce solo dalla radice; freccia ← e tab bar restano tutte
e ora dicono la stessa cosa del gesto, che è come sono spariti
`sicurezzaRitorno` e l'euristica di `tornaDalNegozio`. Vedi
Architettura per le tre scelte da non rovesciare: URL mai toccato,
ascoltatore dichiarativo, pila derivata dal DOM con un
MutationObserver — che è come i 18 siti dei fogli, `closeSheet` e le
tre chiusure mirate sono rimasti intonsi — collaudato in locale nel
browser vero a 375px: catena viste con salti multipli e AVANTI del
browser, dieci giri di tab senza far crescere la cronologia, deep link
che atterra sulla vetrina, lightbox, tour, cartello e foglio-invito,
nessun gradino morto dopo ✕/velo/Escape, e il caso a cui teneva
Andrea — picker aperto SOPRA il paySheet con invoice LNbits vera: il
primo indietro chiude solo il picker e il pollTimer resta VIVO, il
secondo chiude il foglio e lo ferma. In produzione basta il deploy:
nessuna rotta, nessuna colonna. Da provare dal vivo dentro Telegram,
dove contano la freccia di sistema e il gesto del client); Barattolo
diventa una vetrina di Nostr (lug 2026, cantiere di Alan — PR #5 —
merged con sette correzioni decise da Andrea: si importa chiunque
pubblichi NIP-99 in italiano, con scoperta ogni 6h, firme verificate
davvero, moderazione completa prima che un evento diventi una riga,
metadati di commercio nei tag, catalogo a 25 categorie e la rete di
prove in CI. Le correzioni, che sono la parte da ricordare:
l'interruttore nasce SPENTO perché il salto non sia l'effetto di un
deploy; le categorie SI AGGIUNGONO e non si rinominano, quindi zero
migrazioni e nessun annuncio spostato; la moderazione si paga una
volta sola e si rifà solo quando cambia il TESTO; dubbi E bocciature
dell'AI vanno in una coda visibile agli admin invece di sparire, e la
decisione è REVERSIBILE («↩︎ Ripensaci»); lo stock dai relay si lima
al tetto e la consegna digitale dai relay non passa; i suggerimenti su
cosa manca a un annuncio sono OPT-IN e spenti di serie — il benvenuto
resta l'unico messaggio che mandiamo senza permesso. Più i tre
ritocchi del giorno dopo: quattro icone di categoria che dicevano un
prodotto invece del reparto, il tetto della quantità a 999999 (con
tutte le quantità che passano da `fmt()`), e i due testi definitivi.
Vedi Architettura —
collaudato in locale con 48 prove pure in `prove.py` [che ora coprono
anche il modello CSV, il testo condiviso degli eventi e le due
guardie] più 26 verifiche su DB usa-e-getta [`_da_giudicare` nei sei
casi, il marchio che fa nascere in revisione, il registro legato
all'annuncio e la sua idempotenza, il giro completo
rifiuta→riapri→pubblica→riapri, la guardia degli affari in corso, la
coda «decisi», e i suggerimenti nei loro cinque casi — spenti che non
scrivono e NON timbrano, accesi che scrivono una volta sola e mai nel
giro dell'apparizione], più il foglio delle 25 categorie e
l'interruttore nei due stati guardati nel browser. IN PRODUZIONE: il
deploy da solo non cambia NIENTE — girano le migrazioni delle due
colonne (`completamento_avvisato`, `suggerimenti_annunci`) e basta;
l'import aperto si accende scrivendo la riga nel config del VPS, e
quello è il momento da guardare col journal aperto. Se il config del
VPS ha una riga `MAX_QUANTITA_ANNUNCIO` esplicita, va alzata anche lì.
RESTA DA FARE: decidere se anche lo scarto per PAROLE VIETATE debba
finire in coda come quelli dell'AI — oggi non ci va, resta uno scarto
secco visibile solo nel registro);
il primo giro vero, e l'anello che si chiudeva (lug 2026: acceso
l'import in produzione sono comparsi 40 annunci doppi, articoli
intestati al venditore sbagliato e «Altri oggetti di questo venditore»
pieno di roba d'altri — TRE sintomi di UN bug solo, la scoperta che
adottava la chiave della piattaforma come se fosse un venditore
qualsiasi. Diagnosi fatta sui dati veri con query in sola lettura
PRIMA di toccare qualunque cosa, import spento subito, e zero denaro
coinvolto: nessun ordine aperto su annunci importati. Cura in due
tempi — il TAPPO (`chiave_di_casa` + il confronto dell'autore
nell'import, che è il buco vero: non ci si fida del filtro `authors`
del relay) e la PULIZIA (`ripulisci_anello_nostr.py`), più la cintura
sull'origine nella guardia del set. Vedi Architettura, «L'ANELLO CHE
SI CHIUDEVA» — collaudato con 57 prove pure [9 nuove, compresa la
sentinella sul confronto dell'autore] e 22 verifiche su DB
usa-e-getta che RICOSTRUISCONO il bug daccapo: il negozio del fantasma
con roba di due persone, il relay che risponde con eventi di un terzo,
l'anteprima che non scrive, la copia con l'ordine aperto lasciata
stare, il secondo giro che finisce il lavoro, il rilancio a vuoto.
LEZIONE da non perdere: un cantiere che legge da una fonte pubblica
deve chiedersi per prima cosa se in quella fonte c'è anche la propria
voce).
ritocchi ai filtri e al recinto (lug 2026: le due spunte di consegna
che mancavano — «🤝 Ritiro in zona» e «💾 Codice online», col digitale
che guarda il SET delle strade per prendere anche la combo — e le
etichette senza «Solo con…», che dentro un pannello che si chiama
Filtri il «solo» lo dice il posto; e lo «Scopri di più» che passa in
coda alla frase del recinto, nel verde del testo di fiducia, legato
all'ultima parola perché sotto i 390px scendano insieme. Collaudato
coi dati veri: conteggi dei filtri incrociati con le query sul
database, composizione con condizione e regione, paginazione, risposta
legacy senza `limit` ancora un array, e il ritorno a capo del link
misurato a 360/375/390/1280 nei due temi coi contrasti AA. In
produzione basta il deploy).
E in mezzo, «📍 Vicino a me»: nato, deployato e TOLTO nel giro di due
giorni perché si sovrapponeva al filtro per regione — la storia, il
motivo e cosa è rimasto in piedi stanno in Architettura, alla voce
omonima. Con lui se n'è andata la precompilazione della Zona in Vendi:
il campo nasce vuoto e lo scrive l'utente. Resta INERTE la colonna
`utenti.comune`, che nessuno scrive e nessuno legge.
Due migliorie prima di aprire la pagina «Sfoglia» (lug 2026, decisioni
di Andrea): LA RICATEGORIZZAZIONE — l'AI propone leggendo titolo e
descrizione, i moderatori confermano dalla coda «🗂 Categorie da
sistemare» raggruppata per spostamento, e nessun annuncio cambia
casella senza che un umano l'abbia visto (~0,20 $ per 800 annunci);
più il fix all'invito opt-in, che la voce «la categoria giusta» non la
faceva partire mai. E LA CONDIZIONE CHE NON SI CHIEDE dove non vuol
dire niente: «Alimenti e bevande» e i codici online consegnati dentro
Barattolo — il campo sparisce dal form, la pillola dal dettaglio, la
riga dal pannello Filtri, e gli alimentari di ieri non si migrano ma
smettono di mostrarla. Vedi Architettura per i due giudici unici
(`senza_condizione`, `_sposta_categoria`) — collaudate in locale con
20 prove pure nuove in `prove.py` (parità dei due elenchi
server↔client compresa) e 26 verifiche TestClient su DB usa-e-getta
(guardia nei quattro casi, alimentare storico fuori dal filtro ma in
vetrina, modifica che torna a chiedere la condizione cambiando
categoria, coda con spostamento parziale, proposta stantia, 409 e
scarto), più il giro nel browser vero a 375px: campo che compare e
sparisce sui quattro passaggi, filtro che dorme e si risveglia, coda
admin con «mostra tutti» che non perde le spunte tolte a mano. In
produzione basta il deploy — la tabella `categoria_proposta` la crea
init_db —, e la coda resta vuota finché non si lancia
`python ricategorizza.py --scrivi` sul VPS.
La pagina «Sfoglia» (lug 2026): le 26 categorie diventano una vetrina —
quarta radice della nav, griglia a due colonne di piastrelle
illustrate, dieci in una schermata come nel riferimento. Il tondo del
Vendi resta al centro esatto grazie al quinto posto vuoto, e l'indietro
da una categoria torna a Sfoglia (l'unica eccezione al patto delle
radici, con la sua bandierina). Vedi Architettura — collaudata in
locale a 360/375/390 e 1280px nei due temi: nav misurata (Vendi a
180.0 su 180.0, altezza invariata, nessuna etichetta troncata), catena
del gesto indietro compresi i cinque cambi di tab che non lasciano
gradini, categoria vuota che atterra sul suo «Avvisami se arriva», la
rotta che serve solo le 26 vere (404 su nomi inventati e su
`../../config.py`), il ripiego a emoji, e 77 prove verdi con le tre
nuove sulle illustrazioni. Due problemi veri trovati e chiusi
strada facendo: i nomi di una parola sola che sbordavano dove il
browser non ha il dizionario di sillabazione, e la guardia di
`renderChips` che rimangiava la categoria scelta quando era vuota.
In produzione basta il deploy: nessuna colonna, nessuna leva —
solo i 26 file in `assets/categorie/`, che viaggiano col commit.
L'avvertimento che stava qui — cache di un giorno su nomi NON
versionati, «una rifatta resta vecchia nei browser per 24 ore» — si è
incassato per davvero (ago 2026): la PWA di Andrea mostrava DUE
generazioni vecchie insieme (il biglietto della 27ª con l'alone
«attaccato al titolo», Animali senza il pareggio) mentre la Mini App,
che ha la SUA cache WebView, era giusta — e sembrava in tutto un
render diverso nei due contesti. Ed era STRUTTURALE, non un caso: ogni
illustrazione nuova sposta la mediana dell'inchiostro e il pareggio
riscrive delle sorelle, quindi i file cambiano a ogni categoria
aggiunta. La cura, per tutte e 27: la rotta risponde
`Cache-Control: public, no-cache` — il browser tiene la copia ma la
RICONTROLLA a ogni uso, e l'ETag che FileResponse già manda fa 304
finché il file non cambia — più il timbro una-tantum `?b=2` sugli URL
del client (renderSfoglia e icoCategoria), che ha ripulito le cache
scritte col regime vecchio e NON va più toccato. Il «nome col timbro»
delle foto resta la strada se un giorno servisse rimettere il max-age.
Tre lavori sulla nav, in un cantiere solo (lug 2026): la nav non mente
più entrando da Sfoglia — si accendeva «Esplora» su una vetrina
filtrata, e chi guardava credeva fosse il mercatino intero e lo
trovava vuoto (rimedio: `ramoVetrina`, una variabile e non una vetrina
duplicata, letta dal giudice unico `voceNav()` e spenta da
`setCat('Tutto')`, cioè dal filtro che la giustifica); gli Ordini
passano all'ESTREMA destra col posto vuoto in mezzo, che è solo uno
scambio nel markup perché i cinque slot sono tutti `flex:1`; e le tre
emoji della barra diventano SVG di casa — lente, piastrelle, pacco di
tre quarti — che si ACCENDONO invece di accendere una pillola sotto di
sé. Più le icone della consegna in Vendi, che crescono a 20px e in cui
la spedizione passa dal 📦 al 🚚, cioè al disegno che la spedizione ha
in tutto il resto dell'app. Vedi Architettura, alla voce Sfoglia, per
la taratura delle icone (26px come tetto, viewBox ritagliato a
`2 2 20 20`) e soprattutto per le TRE STRADE SCARTATE col loro perché
— pacco piatto, barattolo del logo, illustrazioni a 24px — che è la
parte che serve fra sei mesi. Collaudato nel browser vero a 360px nei
due temi: nav 61,2px invariata e Vendi a 180,0 su 180,0 dopo ogni
ritocco, giro completo del ramo Sfoglia (piastrella → dettaglio →
negozio → i due indietro → tab Esplora che rimette 837 oggetti con una
richiesta senza `cat`), caselle di consegna che aprono ancora costo e
taglia, e 78 prove verdi. In produzione basta il deploy: nessuna
colonna, nessuna leva, nessun asset nuovo. Resta da vedere dal vivo
dentro Telegram, dove contano la gesture bar del telefono e il tema
del client.
Tre difetti di navigazione nati con quei due cantieri (lug 2026, tutti
e tre visti da Andrea sull'app vera). 1) I DOPPIONI entrando in una
categoria da Sfoglia: non un doppio render ma la pagina-dopo che
arriva in ritardo col cursore della vetrina di prima — rimedio
`vetrinaGiro`, vedi «Tenuta al volume». 2) IL GESTO DI AGGIORNAMENTO,
che non era di nessuno e dentro Telegram portava via la Mini App: ora
`disableVerticalSwipes` vale anche alla radice e la tirata è nostra,
coi tre recinti che tengono fuori la galleria a scroll-snap. 3) LO
SWIPE INDIETRO che da Sfoglia non faceva niente: `history.back()` alla
cieca su una sessione che ha una entry sola — ora il gradino lo dice
`d` nello state e l'ultimo passo è esplicito. E l'ultimo passo è che
ESPLORA È LA RADICE MADRE: dalle altre radici l'indietro ci passa, e
solo da Esplora si esce. Deciso in due tempi, ed è la parte da
ricordare: per un giorno la regola è stata «ogni radice esce per conto
suo» (le radici sono sorelle, non parenti), poi Andrea l'ha rovesciata
perché su Subito e Vinted la home È la radice madre — la convenzione
che gli utenti hanno già nelle dita vale più della simmetria del nostro
modello. Tutte e due le ragioni stanno in Architettura, con la
conseguenza accettata (chi apre l'app dritto su un'altra radice
all'indietro finisce in Esplora senza esserci mai passato).
Vedi Architettura, «il gesto indietro» — riprodotti tutti e tre in
locale prima di toccare niente (i doppioni misurati: 60 card di cui 14
doppie, poi 30 su 30 uniche) e ricollaudati dopo: scroll infinito su
tre pagine, due tocchi svelti su due categorie, le sei guardie del
gesto di aggiornamento, `d` che conta giusto lungo tab → piastrella →
dettaglio → i due indietro, e 78 prove verdi. In produzione basta il
deploy: nessuna colonna, nessuna leva.
E POI IL SECONDO GIRO, dalla PWA installata di Andrea (lug 2026), che
è la lezione grossa del cantiere: i primi rimedi funzionavano dentro
Telegram e NON nella PWA, che è il contesto in cui lui prova davvero.
Tre correzioni. 1) La tirata non aggiornava: ricaricava la pagina, cioè
riportava a Esplora — `overscroll-behavior` stava solo sul body e alla
viewport arriva quello dell'HTML, quindi il pull-to-refresh nativo non
era mai stato spento; e i nostri ascoltatori passivi non potevano
chiamare `preventDefault`, ora il touchmove è non-passivo mentre la
tirata è armata. 2) Da Sfoglia la PWA si chiudeva senza passare da
Esplora: lì il gesto è di SISTEMA e non passa da `navIndietro`, quindi
il passaggio dalla madre non si può intercettare — va PREPARATO, e ora
il primo passo via da Esplora spinge una entry. 3) Gli annunci a foto
SINGOLA scorrevano di lato trascinando la pagina: la striscia restava
scorrevole senza niente da scorrere e l'incatenamento arrivava alla
viewport (stessa causa del punto 1, sull'asse X). Vedi Architettura
per la distinzione fra i due contesti, che è la cosa da non
dimenticare: nella PWA non c'è niente da intercettare.
Verificato in locale nel contesto PWA (senza `initData`, col gesto
simulato come `history.back()` diretto): la catena piastrella →
dettaglio risale a categoria, Sfoglia, Esplora-intera in tre gesti; i
tab costano un indietro solo; la tirata in categoria annulla il gesto
nativo, fa una chiamata e non si muove; la galleria a una foto non
scorre e la pagina non sborda. E POI PROVATO DA ANDREA SUL TELEFONO,
nei DUE contesti: tirata, galleria, radice madre e chiusura funzionano
in entrambi, `tg.close()` compreso.
Restava un terzo caso, che si presentava UGUALE nei due contesti — ed
è il modo in cui si è capito che era contenuto e non contesto: due
annunci importati si trascinavano di lato col dito sul corpo della
scheda, per una parola lunga senza spazi che allargava il documento.
Vedi «il testo dell'utente non può allargare la pagina» nel dettaglio
annuncio, e in particolare il `min-width:0` sul figlio flex, che è la
metà del rimedio che non viene in mente.
La 27ª categoria e l'albero dormiente (ago 2026, due cantierini in un
giorno): «Buoni ed esperienze» accesa subito — la merce vera che
moriva in «Altro» (pacchetto B&B, buoni Zalando) ha una casa, coi
sette posti, i gemelli SENZA_CONDIZIONE e le righe-voucher del
modello CSV traslocate — e l'albero delle SOTTOCATEGORIE definito ma
mostrato mai: 86 sottovoci su 26 categorie (l'86esima, «Mare e
piscina», nata dal Telo d'Amare vero), disegnate sui 46 annunci
veri di produzione, colonna e payload silenzioso già vivi, UI zero
(vedi Architettura per il patto, le regole di confine e la decisione
su Elettronica, che resta col contenuto suo invece di chiudere).
Collaudato: 38 prove pure nuove/aggiornate in prove.py, 16 verifiche
TestClient su DB usa-e-getta (giudici in pubblica/modifica, conserva/
azzera, la 27ª senza condizione, la vetrina che non mostra la
colonna) più il filo del CSV. IN PRODUZIONE basta il deploy (la
migrazione della colonna gira da sola); dopo il deploy gli
spostamenti veri — B&B e Zalando verso la voce nuova (il casco moto
citato nei primi appunti era merce del db di COLLAUDO, non di
produzione) — si mettono in coda con `sposta_a_mano.py` sul VPS e si
approvano dalla coda admin, che aggiorna anche il NIP-99.
Il GIUDICE SILENZIOSO (ago 2026, il giorno dopo): la colonna si
riempie da sola a parole chiave dentro la categoria scelta — misurato
prima di accenderlo (45/46 in produzione, 12/15 fuori campione, zero
sbagliati: si astiene, non sbaglia), agganciato a pubblica/modifica/
CSV/dopo-import Nostr, con `assegna_sottocategorie.py` per la passata
sul pregresso e il termometro `--conta` che dice dove arricchire il
dizionario coi dati veri. Collaudato: 11 prove pure nuove (dizionario
allineato all'albero voce per voce + il giudice nei suoi casi), 6
verifiche TestClient dei ganci su DB usa-e-getta, e lo script nei tre
modi su una copia del db locale (300 assegnate, idempotente al terzo
giro). IN PRODUZIONE: deploy, poi `python assegna_sottocategorie.py`
sul VPS per l'anteprima e `--scrivi` per la passata una tantum.
L'ACCENSIONE dell'albero è un cantiere futuro, solo frontend + param.
L'asta 🔨 (ago 2026, cantiere in sette passi con revisione di Andrea
sui passi dei soldi): vendita al miglior offerente con escrow
incrementale — puntare è pagare, si versa solo la differenza, il
vincitore diventa un ordine già pagato e i perdenti riscuotono dal
binario degli incassi. Vedi Architettura per schema, motore, chiusura,
regola della lapide e strade scartate. Collaudata in locale su DB
usa-e-getta lungo tutti i passi (partita a tre offerenti con la corsa
risolta al saldo, proroga anti-cecchino, tardivi nel registro, ritiro
definitivo con la cintura del saldo postumo, chiusura idempotente con
l'invariante dei totali, fusione con collisione e lapide, giro visivo
della demo) e con 19 prove pure in prove.py (127 totali). IN
PRODUZIONE: il deploy da solo non cambia niente (migrazioni additive);
le aste si accendono SOLO scrivendo `ASTA_ABILITATA = True` nel config
del VPS e riavviando — da fare guardando il primo giro col journal
aperto, e il primo giro vero dentro Telegram (puntata, sorpasso,
chiusura, riscossione con wallet reale a cifre minuscole) è il
collaudo che manca. RESTA DA DECIDERE a rodaggio: se e quando dare
alle aste la radice «🔨 Aste» nello slot vuoto della nav.

Prossimo cantiere deciso: LA PAGINA D'ACQUISTO DEDICATA — scelta della
strada e conto scomposto in un posto solo, prima che nasca la invoice.
Prende il posto del foglio del varco (transizione già dichiarata) e
chiude la lacuna aperta oggi: col solo canale spedizione il costo si
vede per la prima volta nel paySheet, a invoice già creata. È una
lacuna TEMPORANEA con la soluzione già pianificata, non una scelta
definitiva: non rimediarla rimettendo una cifra nella scheda (fila
delle pillole e recinto sono già stati provati e scartati, i motivi
sono in Architettura).
Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri, escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.
