# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Architettura

- `server.py` — backend FastAPI + SQLite (`satmarket.db`), un solo file.
  Escrow LNbits (invoice key incassa, admin key paga), commissione 1%,
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
  Formati foto: la miniapp converte in JPEG 1200px via canvas tutto
  ciò che il browser decodifica (WebP ovunque, HEIC su iPhone); ciò
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
  `venditore.distintivi` = solo i `fiducia` guadagnati. Frontend:
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
  nuova, respinta): filtri negli Affari, contatore 🏅 in testata,
  riga «Prossimo:» nei distintivi. Festa dei sats: all'apertura di un
  ordine released, monete ₿ con fisica da confetti dal messaggio di
  chiusura (`festaSats`: 20 al venditore, 10 mini al compratore,
  ~1.5s, rAF legato al tempo + rete di sicurezza sull'overlay, spenta
  con prefers-reduced-motion; una volta per ordine e dispositivo in
  localStorage['barattolo_festa'], il patto degli hint). IN SOSPESO: immagini mascotte/
  barattolo da Claude Design (superano il tetto 256KiB di DesignSync:
  vanno salvate a mano in `assets/`) + route esplicite stile /vendor
  in server.py + favicon + hero desktop — solo dopo, aggiornare la
  regola 3.
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
  Le stelle del rating si mostrano solo se rating > 0 ("0 ★" farebbe
  danno ai venditori appena arrivati); dal lug 2026 le accende il
  sistema di feedback (vedi server.py).
  Scheda Profilo 👤 (lug 2026): quarta voce di nav (`view-profilo`;
  il ramo `profilo` in `go()` rilancia i render, e in VETRINA la tab
  apre l'invito al bot come Vendi/Affari). Dal lug 2026 è a CASSETTI
  richiudibili stile Vinted (CSS `.acc`, header cliccabile con
  emoji+titolo+freccia, `toggleAcc()`; tutti chiusi di default): dopo
  la testata sempre visibile `renderProfilo()` (nome, badge,
  vendite/acquisti conclusi da `/api/me`, stelle solo se rating>0,
  link del negozio con condividi), in ordine: «📋 I tuoi annunci»,
  «🆔 Identità e Nostr» (righe identità + campo npub + verifica,
  riuniti nello stesso cassetto), «⚡ Incassi e pagamenti» (NWC +
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
   nessun segreto altrui coinvolto) →
   mai custodia di segreti altrui, mai firme che richiedano di
   consegnare chiavi al server.
3. Il server pubblico serve SOLO `/`, `/miniapp.html`, `/negozio/*`,
   `/foto/*`, `/vendor/nostr.js` (file singolo) e `/api/*`.
   Non montare mai StaticFiles sull'intera directory (config e .git
   diventerebbero pubblici — falla già successa e chiusa).
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
«🆔 Identità e Nostr» del Profilo,
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
pillow-heif`); scheda Profilo 👤 quarta voce di nav (tutto ciò che
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
ombra piena, recinto escrow tratteggiato, vedi Architettura — solo
CSS/markup, collaudato in locale su tutte le viste e i tre viewport;
IN SOSPESO le immagini mascotte/barattolo con la loro route /assets,
il favicon e la hero desktop: servono i file salvati a mano da
Claude Design in `assets/`).
Backlog concordato: commissione minima fissa; deduplica annunci Nostr
al collegamento (proporre il ritiro del doppione pubblicato dalla
piattaforma quando l'utente fuso ha gli stessi oggetti sui relay con
la sua chiave — rimandata: il match sui titoli fa falsi positivi e un
NIP-09 sbagliato cancella presenza legittima); poi post-lancio: tracking
verificato via API corrieri, escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.
