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
  card 📊 + lista utenti in fondo a Vendi, solo moderatori;
  `utenti.registrato` è la data del primo accesso, "—" per chi
  c'era prima della colonna). I casi ambigui (cannabis
  light, pistola sparachiodi...) NON vanno nella lista parole: li
  valuta l'AI.
  Badge Nostr: colonna `utenti.npub` auto-dichiarata via `/api/me/npub`
  (formato bech32, rifiuta le nsec) + verifica con NOTA PUBBLICA:
  `/api/me/npub/verifica-avvia` genera un codice (vale 1h), l'utente lo
  pubblica in una nota kind-1 dal SUO client, `verifica-controlla`
  interroga 4 relay (websocket-client è sincrono: gira dentro
  `asyncio.to_thread`, relay in parallelo) → `utenti.npub_verificata`,
  badge 🟣✓. Cambiare o rimuovere la npub azzera la verifica.
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
  🟣✓ da subito: la firma Schnorr dimostra il possesso). Un badge
  NON verificato non dà MAI accesso all'account che lo dichiara.
  `hex_to_npub` (bech32 con checksum vero) è il gemello speculare di
  `npub_to_hex`. `vendor/nostr.bundle.js` = nostr-tools 2.23.12
  committato a versione bloccata e servito da `GET /vendor/nostr.js`
  (file singolo, MAI CDN: nessun terzo deve poter cambiare la pagina
  dove si può incollare una nsec).
- `miniapp.html` — frontend intero in un file (HTML+CSS+JS, zero framework).
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
  onesto per chi entra da Nostr (niente avvisi Telegram, per ora);
  foglio `#collegaSheet` per la proposta di collegamento.
  Vista negozio: il blocco venditore nel dettaglio è cliccabile →
  profilo + griglia dei suoi annunci (card riusate via `cardHTML`);
  all'avvio `avvia()` legge `/negozio/...` da `location.pathname` e
  apre direttamente il negozio; bottone condividi = clipboard + toast.
  Le stelle del rating si mostrano solo se rating > 0 (il sistema
  feedback non esiste ancora: "0 ★" farebbe danno ai venditori).
- `config.py` — TUTTE le chiavi e impostazioni. NON è nella repo
  (.gitignore) e NON deve MAI entrarci. `config_esempio.py` è il modello.
- `importa_nostr.py` — importa annunci NIP-99/NIP-15 di un venditore
  consenziente da Nostr (npub e VENDITORE_ID vengono da config.py).
  Il cuore è `importa_venditore()`, importabile: lo usa anche
  l'orologio del server, che rilancia l'import OGNI ORA in
  `asyncio.to_thread` (fail-open totale: segnaposto in config =
  spento, errori = una riga in console). Al primo giro scrive il
  badge 🟣✓ sul profilo del venditore (npub canonica bech32 via
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
- La verifica npub richiede `websocket-client` (pip) nell'ambiente del
  servizio: se manca, il server parte lo stesso e l'endpoint risponde 503.
- La pubblicazione su Nostr richiede anche `coincurve`: installarla con
  `pip install --only-binary :all: coincurve` (le versioni 20/21 senza
  wheel provano a compilare e falliscono; la 19.0.1 ha wheel ovunque).
  Se manca, o se `NOSTR_NSEC_PIATTAFORMA` resta il segnaposto, la
  funzione Nostr si spegne da sola e il resto vive normalmente.
  Anche il LOGIN Nostr dipende da coincurve (verifica Schnorr): senza,
  i suoi endpoint rispondono 503 e tutto il resto vive.

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente. La scala approvata: badge npub auto-dichiarato →
   verifica con nota pubblica (fatta, lug 2026) → login Nostr con firma
   di sfida (fatto, lug 2026: la nsec incollata nel login web firma
   SOLO nella pagina, mai trasmessa né salvata, e la UI la sconsiglia
   a favore di estensione/bunker — è l'estensione approvata della
   scala, NON un'eccezione) → mai custodia di segreti altrui, mai
   firme che richiedano di consegnare chiavi al server.
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

Lanciando in rodaggio su community italiana, limite ~100k sats/annuncio.
Fatti (lug 2026): banner sulla demo browser; vetrina pubblica in sola
lettura (annunci veri dal browser, azioni → invito al bot); moderazione
contenuti a tre strati (parole + AI + admin); badge npub auto-dichiarato
nel profilo e sugli annunci; verifica della npub via nota pubblica
(badge 🟣✓, vedi Architettura); pubblicazione degli annunci verso
Nostr con la chiave della piattaforma (NIP-99 + NIP-09, vedi
Architettura); pagina negozio del venditore, interna e pubblica
(`/negozio/{username|codice}`, vedi Architettura); login web col
Telegram Login Widget (sessioni cookie, app completa dal browser,
vedi Architettura — ricordarsi `/setdomain` su BotFather); login web
con Nostr (estensione NIP-07, bunker NIP-46, nsec solo-in-pagina;
tg_id negativi e npub_accesso, vedi Architettura — gli utenti Nostr
per ora restano senza notifiche: le vedono nei loro Affari).
Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri, feedback/stelle, NWC, escrow on-chain
2-di-3, parere legale MiCA prima di crescere.
