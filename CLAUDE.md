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
  'rimosso' + messaggio gentile al venditore. La modifica firmata
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
  libero resta solo dal lato annunci).
  Città vere in Vendi (lug 2026): il campo Zona resta testo LIBERO ma
  suggerisce i comuni mentre si digita — datalist `zonaList` su
  /api/comuni (debounce 250ms, pattern avvisi) col valore nel formato
  «Comune (SIGLA)» («Carmagnola (TO)»: distingue gli omonimi, e
  normalizza('Pavia (PV)') = 'pavia pv' è una chiave GIÀ registrata
  da carica_comuni, riconosciuta senza codice nuovo; il valore si
  salva e si mostra così com'è). Al blur passa da
  `GET /api/zona-controlla` (autenticato): comune riconoscibile nel
  testo = silenzio; nulla di riconoscibile ma un QUASI-comune sì =
  riga `#zonaHint` «intendevi Pavia (PV)?» con [Usa] / [Lascia così],
  il nome suggerito vive nella variabile `zonaSuggerita` e mai dentro
  l'onclick (gli apostrofi di Sant'Angelo). LA ZONA SEGUE LA CONSEGNA
  (lug 2026): col RITIRO ('ritiro'/'entrambe') è OBBLIGATORIA e deve
  CONTENERE un comune riconosciuto — frazioni ok per costruzione
  («Frazione Salsasio, Carmagnola (TO)» passa: gli n-grammi trovano
  il comune), «Pvia» no; la regola vive in `guardia_zona_condizione`
  (400 col messaggio dei suggerimenti; senza dataset si spegne,
  fail-open) e nel client (campo vuoto fermato in publish(), label
  dinamica «obbligatorio per il ritiro» da aggiornaConsegnaForm, hint
  fermo al blur). SENZA ritiro resta facoltativa e la validazione è
  morbida (mai bloccante; niente candidato = niente riga). «Spedisco
  in tutta Italia» non vive più nel campo Zona (è roba della
  consegna): l'annuncio senza luogo mostra in card/dettaglio
  «📦 Spedizione» o «💾 Online» via `luogoMeta` (storici = «📍 —»).
  `suggerisci_comune` = difflib a
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
  facevano larga 4px in più). MOTORE: gemello della coda
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
  `espandi_distintivi_vetrina`) = dal lug 2026 TUTTI i guadagnati
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
  In vetrina/dettaglio il controvalore sats dell'ancorato è una STIMA
  live («≈», `satsSpedizione`/`spedTesto` keyed su spedEur>0, ripiego
  onesto in € se il cambio del client manca; prefisso ≈ dei bottoni
  via `stimaCirca`); il valore vero si fissa alla creazione
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
  il filtro promette un costo dichiarato); `protezione_percento`
  nella busta di prima pagina (la stima del client non hardcoda mai
  la cifra). NIP-99: la spedizione è una riga del CONTENT, nessun tag
  nuovo. Import CSV: colonne facoltative `consegna;spedizione;taglia`
  nel modello e nel parser. La modifica FIRMATA degli importati non
  offre i campi (v1: l'evento non li porta, il form li nasconde).
  Frontend: form Vendi con le TRE CASELLE indipendenti (lug 2026,
  decisione di Andrea, via il select + checkbox: 📦 Spedizione ·
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
  campo) vincerebbero sulla classe nuda; la firmata
  degli importati salta la validazione, il campo resta nascosto) +
  costo (stessa valuta del listino, `consegnaPayload`) + taglia;
  dettaglio con le PILLOLE DELLE MODALITÀ (lug 2026, dopo il feedback
  di Andrea: il 🚚 muto della card qui diventa parola) —
  `pilloleModalita()` scrive una pillola per ogni strada offerta
  («🚚 Spedizione + X» col costo DENTRO la pillola nella valuta della
  vista via `spedTesto`, o «🚚 Spedizione gratuita»; «🤝 Ritiro in
  zona»; «💾 Codice online») e per questo `rigaConsegna` è rimasta la
  sola «🛡️ protezione acquisti inclusa»: la stessa cosa non si dice
  due volte (resta gatata su `l.consegna`, gli storici non promettono
  nulla). Più la pillola della taglia, che dal lug 2026 porta la SCALA
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
  `tagliaPill()` non si fa più chiamare «pacco busta» ma «busta
  imbottita». Scartate le emoji scalate via CSS: cambiano forma da un
  sistema all'altro, non seguono i token del tema e crescendo spostano
  le righe. `box` è solo la misura resa (22 nel foglio-picker e nel
  campo, 16 nella pillola: il viewBox non cambia, quindi il rapporto
  fra le taglie resta identico). Per
  'entrambe' due pillole spedizione/ritiro DENTRO l'escrow-zone
  (`consegnaScelta`, si riparte da spedizione a ogni dettaglio; la
  cifra dei bottoni è `totaleStima`); conto scomposto
  (`contoScomposto`) nel paySheet e nella conferma NWC — stima
  subito, valori VERI dalla risposta di /orders; ordine con riga
  consegna+quote, pannello «🤝 Consegna in zona» con
  `markConsegnaMano` al posto di corriere/tracking, `payoutPanel` e
  testa released = totale − protezione; checkbox «🚚 Solo con
  spedizione» nei filtri (in DEMO client-side in renderGrid); 🚚
  discreto nella meta della card — il prezzo in griglia resta pulito.
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
  pillole di scelta GENERALIZZATE (`stradeConsegna`/`pilloleConsegna`:
  compaiono con ≥2 strade, l'erede del vecchio ramo 'entrambe';
  la pillola dice «💾 Codice online»);
  trust-note asimmetrica `#notaDigitale` visibile SOLO con la scelta
  digitale attiva (su una combo non deve spaventare chi sceglie la
  spedizione, `setConsegnaScelta` la accende/spegne); la pillola
  «💾 Codice online» di `pilloleModalita` (che ha sostituito il vecchio
  «o 💾 codice online» dentro `rigaConsegna`); in card 🚚 e 💾 possono
  convivere. ATTENZIONE a non confonderle: le pillole di
  `pilloleConsegna` stanno DENTRO l'escrow-zone e SI TOCCANO (il
  compratore sceglie la strada), quelle di `pilloleModalita` stanno
  nella fila informativa del dettaglio e raccontano soltanto.
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
  «💰 Fai un'offerta» ULTIMO nella escrow-zone (non disturba il trucco
  :first-of-type; nascosto su importati e con accordo gia' fatto),
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
  gemello client di _prezzo_lampo)/`lampoResta`; badge «⚡ −20%
  2h 14m» in alto a sinistra sulla foto (colori fissi nei due temi,
  MAI animazioni: patto reduced-motion), cartellino e dettaglio col
  listino barrato + riga countdown; UN solo setInterval per tutta
  l'app aggiorna i `.lampo-count` in-place e allo zero fa
  renderGrid + riapertura del dettaglio in sconto (tutto torna
  normale da solo anche a pagina aperta); `artStima` passa da
  conLampo col min sull'accordo (bottoni compra e conto scomposto
  parlano da soli la cifra scontata); foglio `#lampoSheet` del
  proprietario (chip dalle leve, durate a pillole, anteprima
  barrato→scontato con l'ora di fine; nel dettaglio owner «⚡ Lancia
  un'offerta lampo» che con la lampo viva diventa «annullala» con
  confirm); filtro «⚡ Solo in offerta» + voce «⚡ In offerta» in
  Ordina, in DEMO client-side col seme dimostrativo (Cuffie Sony,
  scadenza calcolata al carico).
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
  modifica; oltre `MAX_QUANTITA_ANNUNCIO` — leva config, 100 — = 400)
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
  chiude SOLO col bottone o con la ✕ (niente tocco fuori, niente
  Escape: deve essere letto). Interruttore, testo e link vivono nel
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
  Barra d'acquisto al posto della tab bar (lug 2026, modello Vinted):
  nel dettaglio di un annuncio COMPRABILE la tab bar sparisce e al suo
  posto compare `#barraCompra` — «🔒 Compra in sicurezza · ≈ N sats»
  (primario largo) + «💰 Offerta» (compatto). Gemella della nav per
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
  come in pagina. La cifra è `cifraBarra()` (la matematica di
  `totaleStima`, che già conosce lampo e accordo, con la ⚡ davanti
  quando lo sconto è vivo) e `setConsegnaScelta` la riscrive col tocco
  sulle pillole spedizione/ritiro.
  IL VARCO (lug 2026, da una domanda di Andrea che ha trovato un buco
  vero — la barra l'aveva aperto lei): la barra si raggiunge SENZA
  scorrere, quindi chi la tocca può non aver mai incontrato le pillole
  spedizione/ritiro, e l'acquisto partiva con la strada del default
  senza che NULLA la nominasse prima del pagamento (a spedizione 0 il
  conto scomposto esce vuoto, e la protezione oggi è spenta). Prima
  della barra non poteva succedere: i bottoni stavano SOTTO le pillole.
  Due pezzi. 1) La barra DICE la strada quando ce n'è più d'una — «🚚
  Spedizione · 905 000 sats», catalogo `NOMI_VIA` — e la dice anche col
  SOLO digitale (è la strada con la regola asimmetrica delle 24 ore:
  mai sottintesa). La riga della cifra è un flex dove il NUMERO non si
  stringe mai (`.bc-num`) e a cedere coi puntini è il nome della strada
  (`.bc-via`): serve solo nell'estremo strada+lampo+EUR a 360px.
  2) Il primo tocco con scelta ancora IMPLICITA non compra: apre il
  foglio «Come vuoi riceverlo?». Stato `consegnaEsplicita` (falso a
  ogni `openDetail`, vero solo al tocco dell'utente — pillola o voce
  del foglio) e il bottone passa da `compraDaBarra()`.
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
  Su MOBILE i due gemelli in pagina si
  spengono (`.escrow-zone .btn.ghost.compra` con la sua `.escrow-note`
  e `.off-cta`, classe nata per questo): il recinto resta il posto
  delle spiegazioni, della scelta di consegna e del «⚡ Compra subito»
  NWC, che è un'ALTRA strada e non un doppione — e il trucco
  `:first-of-type` non si tocca. Da ≥768px la barra non esiste proprio:
  la nav è una topbar e il dettaglio a due colonne ha già i bottoni
  sotto mano. I fogli (41) e il velo (40) le passano sopra senza che
  rubi tocchi; a lightbox aperto si nasconde con header e nav
  (`body.lb-aperto`); la scivolatina d'ingresso tace con
  prefers-reduced-motion.
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
mattone del futuro cantiere «set»).
Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri, escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.
