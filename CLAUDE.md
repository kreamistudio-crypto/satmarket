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
  Categorie (lug 2026): catalogo unico `CATEGORIE` in server.py —
  Elettronica · Casa e giardino · Abbigliamento · Sport e hobby ·
  Motori · Bambini · Animali · Libri e media · Altro ("Tutto" è solo
  la vista del frontend, non una categoria). `categoria_valida`
  normalizza i payload (sconosciuta → Altro: il client non decide il
  catalogo); migrazione idempotente in `init_db` rinomina le tre voci
  vecchie (Sport/Casa/Libri) con COLLATE NOCASE, che raddrizza anche
  le maiuscole storte dei vecchi import ('casa'). La lista entra nel
  prompt della ricerca AI; nel NIP-99 il tag `t` è la prima parola
  minuscola ("Casa e giardino" → "casa": un hashtag non ha spazi).
  `categoria_automatica` di importa_nostr.py parla il set nuovo
  (Bambini prima di Motori: "seggiolino auto" è roba da bimbi).
  Frontend: pillole ordinate per numero di annunci ATTIVI
  (decrescente), "Tutto" sempre prima, le vuote non compaiono proprio
  (Tutto e la ricerca coprono la scoperta); conteggi dai listings
  caricati, rifatti a ogni giro in `renderChips()` (chiamata da
  `loadListings` e `avviaVetrina`); se la categoria attiva resta
  senza annunci si torna su Tutto. Vale per vetrina autenticata,
  anonima e DEMO (dati finti già rimappati). Dal cantiere «tenuta al
  volume» (sotto) i conteggi delle pillole coi dati vivi vengono dal
  server (`conteggi` in prima pagina), il locale resta per la demo.
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
  (`nostr_origine_d=''`); sul match aggiorna anche
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
  verso i canali che esistono. Dettaglio annuncio e dettaglio ordine
  mostrano «✈️ Scrivi su Telegram» (t.me/username) e/o «🟣 Scrivi su
  Nostr» (profilo su njump.me: il DM parte dal client dell'utente)
  secondo l'identità della controparte; il doppio cittadino li ha
  entrambi, senza canali resta la riga onesta «le trattative non sono
  necessarie: l'escrow protegge». La npub del ponte è SOLO dal
  possesso dimostrato — npub_accesso o badge verificato, la regola di
  `notifica()`: per l'annuncio il client usa `contatto_nostr`
  (importati) con ripiego su `venditore_npub` verificata (già in
  CAMPI_VETRINA); per l'ordine `/api/orders` aggiunge
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
  libero resta solo dal lato annunci). MOTORE: gemello della coda
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
  `venditore.distintivi` = solo i `fiducia` guadagnati; dal lug 2026
  anche gli annunci portano `venditore_distintivi` (subselect
  GROUP_CONCAT in `CAMPI_VETRINA` + SELECT di search e miei, espanso
  in chip fiducia {id, emoji, nome, descrizione} da
  `espandi_distintivi_vetrina`: i non-fiducia verso la vetrina non
  escono proprio). Frontend:
  griglia `renderDistintivi()` nel cassetto «🏅 Distintivi» del
  Profilo (il conteggio «(N di M)» vive nell'header del cassetto,
  `#distintiviConta`; classe `.distintivo` — `.badge` è degli stati
  ordine — mancanti in grigio con la descrizione come molla), chip
  fiducia accanto al nome in `renderNegozio` (filtrando `nostrano`:
  il 🟣 c'è già), cassetto nascosto in DEMO come il wallet.
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
  Esplora (`valutaVista` in localStorage['barattolo_valuta']),
  `prezzoParte(l)` rende la valuta dello spettatore grande e l'altra
  piccola sotto — il «≈» sta SEMPRE e solo sul prezzo convertito, mai
  sul listino; `cambioVivo` + re-render della griglia all'arrivo del
  cambio CoinGecko; form Vendi col suffisso-bottone sats/€
  (`sellValuta`, virgola decimale tradotta); paySheet e conferma NWC
  mostrano la stima «≈» e poi i sats VERI da `prezzo_sats` della
  risposta di POST /orders (MAI da `l.price`, che per i listini EUR
  è solo l'equivalente di pubblicazione).
  Cinque modalità, decise in `avvia()`: app vera dentro Telegram (auth
  via initData); WEB dal browser (cookie di sessione, app completa:
  `authHdr()` manda header vuoto e comanda il cookie; il sondaggio
  cookie viene PRIMA di quello collaudo); collaudo locale (identità
  finte + bottone "cookie web" per provare il login web senza widget);
  VETRINA pubblica in sola lettura dal browser (annunci veri, banner
  col widget "Entra con Telegram" — `data-request-access=write` chiede
  il permesso per gli avvisi — e ogni azione apre l'invito verso
  @ilbarattolobot); demo coi dati finti come riserva se il backend tace.
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
  comando bot) e annunci/ordini/profilo non si toccano.
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
  flottante «🔒 pagamento protetto»; trucco `:first-of-type` che
  promuove il bottone escrow a CTA arancione quando «Compra subito»
  manca — la condizione walletNwc() non si tocca) e `.vault` del
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
  mode) le medagliette di fiducia `.chip-fiducia` accanto al nome
  nella card venditore del dettaglio (max 3, `nostrano` filtrato,
  dati da `venditore_distintivi`, vedi distintivi). La
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
  Pallini e bottone condividi vivono SULLA foto: colori fissi
  (bianco/carta+inchiostro), identici in chiaro e scuro.
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
  (il tratteggio è il sigillo del pagamento, e dentro c'è il trucco
  `:first-of-type`), stesse guardie e stesso `togglePreferito` del
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
- `importa_nostr.py` — importa annunci NIP-99/NIP-15 di un venditore
  consenziente da Nostr (npub e VENDITORE_ID vengono da config.py).
  Il cuore è `importa_venditore()`, importabile: lo usa anche
  l'orologio del server, che rilancia l'import OGNI ORA in
  `asyncio.to_thread` (fail-open totale: segnaposto in config =
  spento, errori = una riga in console). Al primo giro scrive il
  badge 🟣 verificato sul profilo del venditore (npub canonica bech32 via
  `hex_to_npub`, gemella di quella di server.py; mai sovrascrivere
  una npub diversa già dichiarata): così il login Nostr lo riconosce
  invece di creargli un account nuovo. ATTENZIONE: scrive
  direttamente nel database, quindi BYPASSA la moderazione di
  `pubblica()`, e le firme degli eventi non vengono verificate
  (fiducia nei 4 relay). Limite accettato per venditori fidati
  scelti in config; da chiudere se mai si aprirà ad altri.
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

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS).
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
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
   `/annuncio/*`, `/foto/*`, `/vendor/nostr.js`, `/assets/mascotte.jpeg`,
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
   spiegazione lunga di ogni contesto; azione = «🔒 Compra protetto»;
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
release, e la prova d'installazione dallo store sul telefono).
Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri, escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.
