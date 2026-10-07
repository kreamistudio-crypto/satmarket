# Studio: «Agentic Dollars on Bitcoin», l'hackathon RGB di Torino (1 ottobre 2026)

Sola lettura, nessuna modifica al codice, nessun cantiere aperto. Base:
`origin/main` a `2a504a8` (i numeri di riga qui sotto sono di quel
commit; i NOMI di funzioni, tabelle e leve sono la cosa da cercare, le
righe si spostano). Il VPS, il nodo Mostro e il relay non sono stati
toccati e questo studio non chiede di toccarli prima del 10 ottobre.
Fatti esterni verificati sulle fonti in fondo, lette il 1 ott 2026;
quel che NON ho potuto verificare da qui è scritto come tale.

> **Aggiornato il 7 ottobre 2026**: in fondo c'è la **parte seconda**,
> «le idee di Alan, e cosa reggono» — il Cassiere, l'estensione NIP-47
> per gli asset RGB, l'emittente legato a un'identità Nostr, il piano
> rifatto e le domande per il Q&A. La prima parte resta com'era il 1 ott;
> tre fatti sono cambiati nel frattempo e la parte seconda li corregge:
> la scadenza della candidatura era il 5 ott alle 12:00 (passata), QVAC è
> alla 0.21 (CLI 0.15), e il NIP-47 è stato ridotto a un nucleo di cinque
> metodi con le estensioni in un repo apposta.

**La domanda di Andrea.** Arrivare all'hackathon «Agentic Dollars on
Bitcoin» (Torino, BLOX, 17-18 ottobre 2026; organizza la RGB Protocol
Association, sponsor Tether; RGB e QVAC obbligatori, WDK bonus; si
giudicano transazioni RGB vere, non simulate; giudici di Tether,
KaleidoSwap e Utexo) con l'infrastruttura pronta, e integrare in
Barattolo in due giorni l'idea di Alan: 1) la fidelity card come asset
RGB — Barattolo emette un token «BRT» e un asset per ogni negozio
consigliato, un punto per euro speso, lo sconto lo decide il negozio,
l'utente tiene i punti in un wallet NON custodial dentro la webapp;
2) QVAC come assistente locale che legge il wallet e suggerisce quando
usare i punti, l'utente approva e il wallet firma; 3) nel P2P, swap di
asset RGB (USDT su RGB, se Tether li emette) accanto a BTC/euro.

**La risposta corta.** L'idea regge, ma TRE delle sue premesse non
stanno in piedi al 1 ottobre 2026 e vanno sostituite PRIMA di
candidarsi, non all'evento. (a) **USDT su RGB non è ancora disponibile
al pubblico**: annunciato ad agosto 2025, «atteso entro settimane» a
luglio 2026, «it's coming home» senza data il 24 settembre; nessun
contract id pubblico, nessun USDT ufficiale in rete di prova. I
«dollari» della demo saranno un asset NIA emesso da noi, come fece
KaleidoSwap nel 2024. (b) **Il wallet RGB non custodial «dentro la
webapp» non esiste in forma difendibile**: il modulo RGB del WDK
(`@utexo/wdk-wallet-rgb`) è un addon nativo per Linux/macOS in Node,
niente browser e niente Windows; nel browser ci sono solo
`@utexo/rgb-sdk-web` (beta, signet, non è WDK) e un modulo WDK nato il
26 settembre con zero stelle, e tutt'e due tengono lo stato RGB in
IndexedDB, che Safari cancella dopo 7 giorni senza interazione — e
senza quello stato la sola seed NON recupera gli asset. Nella Mini App
su iOS sarebbe un wallet che perde i punti da solo. (c) **QVAC non gira
nel browser**, lo dice Tether in una pagina apposta: gira in Node, Bare
ed Expo. Quindi l'«assistente locale nella webapp» è un processo locale
accanto al browser (un `qvac serve` su 127.0.0.1 o un'app Electron), o
un'app Expo su Android — non JavaScript nella pagina. **E il
regolamento decide la forma del lavoro**: «we only judge what you build
during the hackathon. Declare what already exists when you arrive, keep
the weekend's work in dated commits, and do the RGB and QVAC integration
on site». Prima dell'evento si prepara l'INFRASTRUTTURA (una macchina
nuova con il nodo RGB su signet, gli asset emessi, i pacchetti provati,
il modello scaricato), e il CODICE che lega RGB e QVAC a Barattolo si
scrive a Torino, in commit datati. **Raccomandazione: candidarsi entro
il 3 ottobre (la pagina dice 7, il nastro dice ancora 3), un modulo a
testa, squadra da due; prima del 10 ottobre NIENTE al VPS e NIENTE al
nodo Mostro — una VM nuova su signet con rgb-lib-python o RLN, gli asset
BRT e CAFFE-LUCA emessi lì, il backup cifrato come quello del nodo; dal
10 al 16 i tutorial dei mentor, il Q&A del 13, le prove dei pacchetti sul
portatile; all'evento il flusso minimo — emissione già fatta, punti
assegnati dopo un ordine di collaudo, riscatto con sconto in sats,
l'assistente QVAC locale che propone e l'utente che approva — con il
wallet dell'utente lato server dichiarato «custodial per la demo» come
rete, e quello nel browser su signet come tentativo da fare il primo
giorno. Lo swap nel P2P si lascia fuori: Mostro non ha nessuna nozione
di asset, e lo swap RGB su Lightning è il prodotto di uno dei giudici.**

## Come leggere questo file

- Le sei domande di Andrea (A-F) hanno una sezione ciascuna, più la
  sezione 0 su cosa c'è già in casa e le fonti.
- «VERIFICATO» = letto sulla documentazione ufficiale, sul README, sul
  registry npm o su una pagina datata. «NEL CODICE» = con nome e riga
  in `server.py` o `miniapp.html`. «A VERBALE» = decisione già scritta
  in `CLAUDE.md`, `docs/CANTIERI.md` o `docs/ARCHITETTURA.md`, col
  NOME della voce, da non contraddire. «DA DECIDERE» = una scelta di
  Andrea, con le strade accanto. «NON TROVATO» = cercato e non
  verificato: vale come dubbio, non come fatto. «STIMA» = ore a
  orecchio per uno sviluppatore solo, da prendere come ordine di
  grandezza.
- Quando qui si scrive «RGB» si intende **RGB Protocol on Bitcoin
  v0.11.1** di `github.com/rgb-protocol` (la linea dell'Associazione,
  di Bitfinex, Tether e Utexo), non la «v0.12» di RGB-WG: sono due
  consensi incompatibili, e solo il primo ha wallet, nodi e l'USDT
  annunciato (vedi A.1).

## 0. Da dove partiamo (NEL CODICE e A VERBALE)

L'idea di Alan ha in casa più di quanto sembri, e due regole che la
indirizzano.

- **«Un punto per euro» esiste già, ed è una decisione scritta.**
  `XP_PER_EURO = 1` (`server.py:2798`, «un euro, un punto»), col fisso
  `FISSO_XP_ORDINE = 10` per ogni affare concluso, i pesi per ruolo
  (`XP_RUOLO`: venditore 1.0, compratore 0.6) e il perimetro di agosto
  2026: **gli XP sono il COMMERCIO e nient'altro** (comprare e vendere
  danno punti; visitare, pubblicare, feedback no). Gli XP vivono in
  `xp_eventi` (`server.py:4773`) e fanno i `LIVELLI` (`server.py:3506`:
  nuovo → avviato 50 → pratico 200 → esperto 800 → maestro 3000, con
  entrambe le soglie di XP e affari). Un asset «BRT» non è una regola
  nuova: è la **stessa moneta dell'impegno, portata fuori dal
  database** — e questa è la frase da dire ai giudici, perché risponde
  al criterio «Marketability: a reason to exist after Sunday».
- **Lo sconto fedeltà esiste già, in due forme.** Nel P2P, per parte,
  letto vivo dal 38385 (`_fedelta_sconto`, `server.py:11854`:
  `FEE_DINAMICA_SCONTO_PIONIERE` per i pionieri, lo sconto del livello
  massimo; CANTIERI «Le commissioni per persona: lo sconto fedeltà del
  P2P, applicato alla fonte»); e sul banner, 0-99 per livello
  (`server.py:3884`). Un «riscatto punti» è un terzo sconto: va messo
  accanto a questi, non sopra.
- **I negozi consigliati hanno un'identità pubblica.** Le pagine dei
  Consigliati (`server.py:2109` in poi, testo in `racconti.py`, stato
  in `impostazioni` come `racconto_pubblicato:<slug>`), il legame
  pagina → negozio per **codice negozio** (pubblico, mai il tg_id), la
  card «Consigliati» della home (`consigliati_pubblici`,
  `server.py:2252`) e «📊 Il tuo negozio» per il venditore. Un asset
  per negozio («CAFFE-LUCA») si aggancia al codice negozio, che è già
  la forma di casa, e la pagina del Consigliato è il posto naturale per
  «quanti punti hai qui e cosa ti danno».
- **La coorte dei pionieri esiste e non dà ancora niente** (`COORTI`,
  `server.py:2690`; in CLAUDE.md «i PRIVILEGI DEI PIONIERI» sono nel
  «da riprendere»). Un primo privilegio potrebbe essere proprio il
  moltiplicatore sui punti: non si decide qui, ma è un argomento per il
  pitch.
- **Il precedente del wallet nel browser è A VERBALE, e dice da che
  parte stare.** ARCHITETTURA, «LA SCALA NOSTR APPROVATA»
  (`docs/ARCHITETTURA.md:28298`): il wallet NWC solo-nel-browser è
  approvato perché la stringa di spesa «vive solo in localStorage del
  dispositivo, mai sul server», e «un suo salvataggio server-side, anche
  cifrato, farebbe della piattaforma il custode dei wallet di tutti: da
  respingere». Una seed RGB nel dispositivo è **pari grado del secret
  NWC**: sta nella scala. Una seed RGB sul server per conto dell'utente
  è il gradino RESPINTO — e la regola ferrea 2 («mai custodia di
  segreti altrui») lo ribadisce. Quindi il «wallet lato server per la
  demo» di questo studio è ammissibile SOLO come rete dichiarata, con
  asset di prova su signet e nessun utente vero, e non è una strada di
  produzione: va detto così ai giudici e scritto così nel codice.
- **Il P2P non sa cos'è un asset.** `P2P_VALUTE` ha una voce sola
  (`miniapp.html:55130`, EUR) e `ordineDaCampiP2P` scrive `fiat_code:
  'EUR'` a mano, con una prova che «guarda avanti» pronta a diventare
  rossa il giorno che il catalogo cresce (CANTIERI, «LA VALUTA È UNA
  TENDINA CON UNA VOCE SOLA»). Mostro upstream: nessuna issue o PR su
  RGB, stablecoin o asset diversi da BTC (VERIFICATO sulla ricerca
  issue del repo, 1 ott 2026); `fiat_code` e `payment_method` sono
  stringhe libere, la hold invoice è BTC. Un «ordine in USDT-RGB» su
  Mostro sarebbe un ordine con fiat «USDT» e metodo «RGB»: il
  coordinatore non vedrebbe né l'asset né il suo trasferimento.
- **Il recinto delle leve c'è già.** `P2P_ATTIVO` + `P2P_PROVA_IDS`
  (`server.py:41088`: lista di tg_id, vuota = aperto a tutti, storta =
  chiusa a tutti e lo dice) e il pannello «⚙️ Stato delle leve» che
  chiede al valore VIVO (`server.py:25696`). Una coppia `RGB_ATTIVO` /
  `RGB_PROVA_IDS` è il calco, e col default `False` e nessuna riga nel
  config del VPS **non si accende da sola** nel deploy automatico.
- **Le tre regole che un pezzo nuovo deve rispettare**: regola ferrea 3
  (nessun `app.mount`, ogni file servito ha la sua rotta e il suo nome
  in whitelist; la sentinella di `prove.py` conta le rotte-pagina
  contro `prove_anteprime`) — 14 MB di WASM nella pagina sarebbero una
  rotta esplicita con la sua forma, e `/miniapp.html` ha gli header
  anti-cache che non si toccano; regola 6 (collaudo con 111/222/999,
  LNbits finto di default, mai relay veri); e il deploy che tira da main
  entro un minuto — ogni commit pushato a main va online, quindi i
  commit dell'hackathon o stanno dietro la leva spenta o stanno su un
  ramo.
- **L'app Android è una TWA** (Bubblewrap, Chrome vero; ARCHITETTURA
  «Distribuzione dell'APK»), la Mini App gira nella WebView di Telegram
  (Chromium su Android, WKWebView su iOS), la PWA ha il service worker
  solo fuori da Telegram (`miniapp.html:65438`). Nessuna delle tre è
  un'app React Native con worklet Bare: la strada «Expo» di QVAC e di
  `wdk-rgb-lightning` sarebbe un'app NUOVA, non Barattolo.

## A. RGB: cosa serve davvero

### A.1 Quale RGB, e in che stato (VERIFICATO)

- **Due linee, un nome.** `github.com/rgb-protocol` (rgb-consensus,
  rgb-ops, rgb-api, rgb-schemas, rgb-aluvm; crate `0.11.1` taggate il
  16 set 2026) è «RGB Protocol on Bitcoin v0.11.1», su mainnet dal 16
  lug 2025, documentata su docs.rgb.info, sostenuta dall'Associazione
  (fondata lug 2025 in Svizzera; membri Bitfinex, Tether, Fulgur,
  DIBA, KaleidoSwap, Utexo…). `RGB-WG/rgb` (LNP/BP, Orlovsky) è «v0.12»:
  ultima release rc.2 del 3 giu 2025, ultimo commit 20 lug 2025,
  nessuna v0.12.0 finale, nessun wallet o nodo Lightning che la
  integri; docs.rgb.info la chiama «unfinished proposal», rgb.tech
  chiama la 0.11.1 «fork» e ne sconsiglia la produzione. **Per
  l'hackathon conta solo la 0.11.1**: è quella dei giudici, dei tool
  linkati dalla pagina e dell'USDT annunciato.
- **Stabile il consenso, beta tutto il resto.** `rgb-lib` (RGB-Tools,
  Bitfinex) è `0.3.0-beta.7`, ogni release dice «meant for testing
  purposes, possibly on mainnet for reckless users and small amounts»;
  RGB Lightning Node (RLN) è «early alpha», **non ha nessuna release
  taggata**, e il README dice «The RGB functionality for now can be
  tested only in regtest or testnet environments». Il fork di Utexo di
  RLN ha **spento le API Lightning su mainnet** il 29 set 2026 (PR
  #177: `LightningUnsupportedOnMainnet`, solo metodi on-chain). Audit
  terzo del consenso: NON TROVATO come documento (rgb.info parla di
  «anni di audit interno fino a v0.11.0-beta.9»).
- **Schemi**: NIA (fungibile non inflazionabile — il nostro caso), CFA,
  UDA (non fungibile), IFA (inflazionabile), PFA.

### A.2 Il nodo: cosa serve e dove metterlo

**Cosa serve, in tre pezzi (VERIFICATO sui README):**
1. **Un wallet RGB con stato client-side** — o `rgb-lib` (Rust; binding
   ufficiali Python/Kotlin/Swift via uniffi, Node e C via c-ffi; `pip
   install rgb-lib`, su PyPI `0.3.0b7` del 18 lug 2026, Python ≥ 3.9),
   oppure RLN, che è «un nodo = un wallet» con REST sulla 3001
   (`/init`, `/unlock`, `/createutxos`, `/issueassetnia`, `/rgbinvoice`,
   `/sendrgb`, `/listtransfers`, `/refreshtransfers`, `/backup`,
   `/restore`, più canali e fatture LN con `asset_id`). RLN è un fork
   di LDK con un output in più nella commitment per l'ancora RGB: un
   LND non può aprire canali RGB.
2. **Un indexer** Electrum o Esplora raggiungibile (rgb-lib fa
   TransactionSync senza bitcoind; RLN vuole bitcoind SOLO in modalità
   BlockSync). Su signet esistono endpoint pubblici: quelli di Utexo nel
   pacchetto `rgb-sdk-web` (`https://esplora-api.utexo.com`,
   `https://rgb-proxy.utexo.com/json-rpc`) e quelli di Iris su
   testnet3/testnet4 (`ssl://electrum.iriswallet.com:50013` e
   `:50053`, proxy `rpcs://proxy.iriswallet.com/0.2/json-rpc`). Che
   quelli Utexo accettino chiunque e reggano il 17-18 ottobre: NON
   VERIFICATO — domanda per il Q&A del 13.
3. **Un proxy RGB** per lo scambio dei consignment (`rgb-proxy-server`,
   `docker run -d ghcr.io/rgb-tools/rgb-proxy-server`): non valida,
   inoltra; «vede gli identificatori del ricevente». In alternativa lo
   scambio out-of-band (`provide_out_of_band_consignment`).

**Dove metterlo — DA DECIDERE, con la mia raccomandazione:**
- **NON sul nodo Mostro.** È fuori dal perimetro di questa sessione per
  ordine di Andrea, e anche senza l'ordine: esce solo da Tor, e un
  indexer Esplora più un proxy HTTPS su circuiti freddi sono la stessa
  trappola della dev fee (NODO-MOSTRO, «LA DEV FEE SI IMPIANTA SUL
  CIRCUITO FREDDO»); e l'audit del 2 set ha una superficie di 23 righe
  che la ronda confronta — un servizio nuovo la cambia.
- **NON sul VPS di Barattolo.** È la produzione del 10 ottobre: il
  deploy tira ogni minuto, `/api/salute` tocca il db, Caddy serve una
  cosa sola; un RLN alpha senza release accanto al mercatino è un
  rischio che non paga niente. Il VPS entrerà in gioco solo per la
  rotta della demo, dietro la leva, e solo se la demo si fa sul VPS e
  non sul portatile (vedi E).
- **SÌ: una macchina NUOVA, piccola, su signet** («rgb-prova»): Debian
  o Ubuntu, 2 vCPU / 4 GB, docker; LNVPS come il nodo, o Hetzner — la
  regola «nodo su Hetzner VIETATO» (memoria «Uscita di sicurezza»)
  riguarda un nodo Lightning con fondi veri, e qui non ci sono fondi:
  signet vale zero. Su quella macchina: `rgb-lib-python` in un venv
  (la nostra lingua, zero toolchain Rust) oppure RLN in docker; il
  proxy nostro in docker; nessun bitcoind (TransactionSync su
  Esplora). **Regtest sul portatile** (WSL2, `rgb-sandbox` o
  `./regtest.sh start` di RLN) per imparare e per la prova in sede
  senza rete; **signet** per la demo, perché ha un explorer pubblico
  (`mempool.space/signet`) che un giudice può aprire e vedere la
  transazione — «working transactions, not simulated» si dimostra con
  un link. Blocchi signet ogni ~10 minuti: le assegnazioni per il pitch
  si fanno PRIMA, in sede, e si mostrano confermate (vedi D).
- **Un'alternativa più leggera, da tenere**: tutto sul portatile della
  demo (WSL2 per rgb-lib-python; QVAC gira in Windows nativo), con
  signet e gli endpoint pubblici. Nessuna VM, nessun costo, ma un solo
  punto di guasto il giorno del pitch. La VM è la versione che
  sopravvive al portatile.

### A.3 Emettere un asset (VERIFICATO)

- Serve **un UTXO «colorabile»**: `create_utxos(up_to, num=5,
  size=1000 sats, fee_rate)` manda una transazione Bitcoin che crea
  fino a cinque uscite da 1000 sats; l'emissione (`issue_asset_nia(
  amounts, ticker, name, precision)` o `/issueassetnia`) assegna il
  genesis a una di quelle. L'esempio dell'openapi di RLN usa proprio
  ticker «USDT», name «Tether». Costo on-chain: la fee della tx di
  `create_utxos` più i sats bloccati negli UTXO; nessuna fee di
  protocollo. Su signet: i sats arrivano da un faucet (quale sia vivo
  oggi: NON VERIFICATO, da chiedere ai mentor).
- Per noi: **BRT** (precision 0, importo grande — es. 21.000.000 — in
  un'emissione sola, perché NIA non si rigonfia), e un asset per
  negozio di prova (**CAFFE-LUCA**, per il pitch; un secondo per far
  vedere che la forma scala). L'emittente di BRT è Barattolo; quello
  dell'asset del negozio è Barattolo PER CONTO del negozio nella demo —
  in produzione sarebbe il negozio col suo wallet, e va detto.
- Un `contract_id` per asset, da scrivere in `impostazioni` sul lato
  server (non muove denaro, non è un segreto: lo stesso recinto di
  `sponsor_slug` e `racconto_pubblicato`).

### A.4 Trasferire a un utente (VERIFICATO, e qui sta il nodo)

1. **Chi riceve genera una invoice RGB**: `rgb:<ContractId>/<Schema>/
   <Amount>/<BlindedUTXO>`; in modalità **blind** il ricevente DEVE
   possedere già un UTXO (i 1000 sats di `create_utxos`); in modalità
   **witness** (`witness_receive`, `/rgbinvoice` con `witness: true`)
   dà un indirizzo e l'uscita la paga chi manda — **così un utente
   «vuoto» può ricevere** i suoi primi punti senza avere sats on-chain.
   Per la demo: witness per la prima assegnazione, blind dopo.
2. **Chi manda** costruisce PSBT + consignment (storia dal genesis) e
   lo deposita sul proxy; **chi riceve valida** e manda ACK; chi manda
   trasmette la witness tx. Il commitment è un OP_RETURN da 34 byte.
3. **Conferme**: `min_confirmations` decide quando il trasferimento
   diventa `Settled`; `refresh()` aggiorna; di norma ≥ 1 blocco. Se 0
   sia ammesso: NON TROVATO. Su signet, dieci minuti; su regtest, un
   `mine` nostro.
4. **In un canale Lightning RGB** niente conferme, ma vuole RLN ai due
   capi e canali con liquidità in asset: fuori portata in due giorni e
   spento su mainnet dal fork di Utexo. **La demo è on-chain in rete di
   prova**, e questo va detto nel pitch come scelta.

### A.5 Backup e recovery dello stato client-side (VERIFICATO)

- **La seed non basta**: «a mnemonic phrase alone isn't enough to
  restore a wallet, since the wallet has to back up the extra
  validation data too» (rgb.info). Lo stash (stato + consignment)
  vive nel `data_dir` del wallet; senza, non si prova la validità dei
  propri asset né si costruisce il consignment per spenderli.
- **La regola d'oro di rgb-lib**: «never instantiate a wallet in
  multiple places!» — la stessa seed su due directory o due dispositivi
  «can lead to RGB asset loss due to improper UTXO management».
  Conseguenza per noi: un wallet per utente lato server è UNA directory
  per utente, e nessun secondo processo che la apra (il «vecchio
  processo che consuma la transizione» della memoria vale anche qui).
- **Lo strumento**: `Wallet.backup(path, password)` e `restore_backup(
  path, password, target_dir)`; RLN `/backup` e `/restore`. Il calco
  è `backup-nodo.sh`: archivio cifrato con la sola chiave pubblica age,
  tirato in pull dal PC, timer notturno. Per la demo basta un backup a
  mano dopo l'emissione e uno dopo ogni giro di prova.
- Il wallet browser (`rgb-lib-wasm`) ha il suo backup cifrato (Scrypt +
  XChaCha20Poly1305) su file o su VSS: è l'unica difesa dallo
  svuotamento dell'IndexedDB (vedi B).

### A.6 USDT su RGB, oggi (VERIFICATO)

- 28 ago 2025, Tether: «plans to launch USD₮ on RGB». 6 lug 2026,
  Bitcoin Magazine: «expected to be launched within weeks, possibly this
  July», deployment di Utexo. 17 lug, Bitfinex: «Tether itself has yet
  to confirm an official launch date». 4 set, rgb.info: UniSat «next
  launch partner», «no release date». 24 set, Ardoino su X: «USDT on
  Bitcoin. It's coming home», nessuna data.
- **Contract id pubblico: NON TROVATO. Un USDT ufficiale su
  testnet/signet/regtest: NON TROVATO.** Il «tUSDT» scambiato da
  KaleidoSwap su mainnet il 30 set 2025 è descritto solo in snippet
  come asset bridgiato via Utexo.
- **Per la demo**: un NIA emesso da noi («BUSD», o lasciare che i
  dollari li porti chi li ha). Se Tether lanciasse fra il 1 e il 17
  ottobre, cambierebbe la sezione sullo swap, non quella sui punti —
  e la pagina del regolamento non promette asset di prova (vedi F).

## B. WDK + RGB nel browser: cosa funziona davvero

### B.1 Il WDK (VERIFICATO)

`@tetherto/wdk` `1.0.0-beta.18` (14 set 2026), Apache-2.0, JavaScript
ESM; «self-custodial and stateless — private keys never leave your app
and no data is stored by WDK»; piattaforme dichiarate **Node.js, Bare,
React Native** («future embedded environments») — **il browser non è
nominato** nella pagina «About», ma esiste di fatto: il Playground
ufficiale firma e invia su Sepolia client-side, lo showcase elenca un
wallet «Web», e la configurazione di `wallet-btc` prevede Electrum su
WebSocket «required for browser and React Native environments». Moduli
ufficiali: EVM (più varianti gasless/4337), BTC (BIP-84), Spark
(Lightning), TON, TRON, Solana, Aptos. **RGB e Cosmos sono «community
modules»**, con la riga «Tether and the WDK Team do not endorse or
assume responsibility for their code, security, or maintenance».

### B.2 I tre modi di avere RGB nel WDK — e dove girano (VERIFICATO)

| Pacchetto | Versione | Gira in | Cosa è |
|---|---|---|---|
| `@utexo/wdk-wallet-rgb` (quello linkato dalla docs WDK) | 2.0.3, 28 gen 2026, «beta» | Node 22 su Linux x64/arm64 e macOS arm64; entry Bare; **niente browser, niente Windows, niente macOS Intel** | wrapper di `@utexo/rgb-sdk` (addon nativo di rgb-lib); vuole mnemonic, `dataDir` persistente, indexer Electrs, transport endpoint; un account BIP-86; NIA; invoice blind/witness; backup cifrato |
| `@utexo/wdk-rgb-lightning` | 0.1.0-beta.15, 29 lug 2026 | Node/Bare (React Native sì), **niente browser, niente Windows** | «runs a full LDK + rgb-lib Lightning node» IN-PROCESS, firma via VLS; i servizi remoti sono solo bitcoind RPC, indexer, proxy, LSP/VSS opzionali |
| `@darkhorse-wallet/wdk-wallet-rgb` (RGB-Launchpad) | 0.1.1, **26 set 2026**, 0 stelle, maintainer anonimo | **Browser** (Chromium testato con Playwright), su `@utexo/rgb-lib-wasm` | `registerWallet('rgb', WalletManagerRgb, {network:'Signet', proxyUrl})`, `issueAsset`, `receiveAsset`, `transfer`; bundler obbligatorio, Buffer shim, IndexedDB «one snapshot per network», un solo account; **«la sola seed non basta a recuperare»** |

E fuori dal WDK: **`@utexo/rgb-sdk-web`** `1.0.0-beta.12` (27 lug
2026, MIT): «runs entirely in the browser, no RGB server, no Node.js,
no native binaries», porta `rgb-lib-wasm` più **l'RLN compilato in
WASM** (`@utexo/rln-wasm`), default **signet** con gli endpoint
pubblici Utexo, classe `UTEXOWallet` (`init()` → `unlock()`), sandbox
React+Vite da clonare. Il binding `@utexo/rgb-lib-wasm` è `1.0.0-beta.3`
(1 lug 2026), **13,8 MB**, «Beta Software — has not been audited»,
solo NIA e IFA, DB in memoria + IndexedDB, Esplora via HTTP, backup
cifrato su file o VSS. BitMask (l'estensione storica in WASM) è in
ricostruzione per la 0.12 (issue #457 del 19 set 2026: export
TypeScript senza implementazione Rust) — non è una base.

### B.3 Nella Mini App e nella TWA (VERIFICATO, poi dedotto)

- **WASM gira** in WKWebView (Safari iOS da 11) e in Chromium: il
  problema non è il supporto, è la memoria e lo storage. Apple non
  pubblica un tetto per WKWebView («reloaded because it was using
  significant memory», nessun numero). Misure di `rgb-lib-wasm` su
  iOS: NON TROVATE.
- **Lo storage è il difetto vero.** MDN (5 gen 2026): **Safari cancella
  lo storage script-writable degli origin senza interazione negli
  ultimi 7 giorni, «applies to both best-effort and persistent
  storage»**; Chrome non cancella da sé ma fa LRU sotto pressione, e
  `navigator.storage.persist()` esenta; «an origin loses ALL stored
  data at once». Con RGB «seed alone insufficient», un utente iOS che
  non apre Barattolo per una settimana **perde i punti**, non la
  sessione. La TWA è Chrome: regge meglio, ma non è «mai».
- **Telegram offre tre cassetti** (Bot API 9.6): `CloudStorage` (4 KB
  per chiave, 1024 chiavi), `SecureStorage` (Keychain/Keystore, 10
  voci: giusto per una seed cifrata), `DeviceStorage` (5 MB). Nessuno è
  IndexedDB, e 5 MB non bastano a uno snapshot rgb-lib arbitrario: la
  seed si salva bene, lo stash no. Il backup cifrato su VSS di
  `rgb-lib-wasm` sarebbe la cura, e vuole un VSS nostro: un cantiere,
  non un weekend.
- **Il seed nel browser**, la ricetta degli starter WDK: mnemonic
  cifrata AES-256-GCM con chiave da PBKDF2 (600k) via WebCrypto,
  ciphertext in storage, chiave in memoria. È lo stesso gradino del
  secret NWC (A VERBALE): approvato.

### B.4 Verdetto e ripiego (DA DECIDERE)

**«WDK + RGB nel browser» esiste in una forma sola** — il modulo
Darkhorse, cinque giorni di vita, beta su beta (WDK beta, rgb-lib-wasm
beta non auditata, rgb-lib «testing phase») — e **non è dichiarabile
come «supportato da WDK»**: Tether lo scrive. È dimostrabile su signet
in Chrome su un portatile; **non è difendibile come wallet non
custodial di produzione in una WebView**. Quattro ripieghi, dal più
onesto al più comodo:

1. **Wallet dell'utente nel browser con `@utexo/rgb-sdk-web` su
   signet, in Chrome desktop** — la demo «non custodial» più corta che
   esista, endpoint pubblici già nel pacchetto, sandbox da clonare.
   Onestà richiesta: beta, signet, **non è WDK** (niente bonus), e la
   fragilità dello storage va dichiarata. STIMA 6-10 h solo per farlo
   girare in una pagina nostra con bundler; il rischio è tutto nel
   bundling e nei polyfill.
2. **Modulo WDK Darkhorse su signet** — l'unica via che vale il bonus
   WDK «centrale». Da provare la settimana del 10 (un pomeriggio: se la
   sandbox del README gira in Chrome con `proxyUrl`
   `rgb-proxy.utexo.com` o col proxy nostro, è viva); se non gira in
   due ore, si lascia. Un maintainer anonimo e zero stelle: lo si usa
   per la demo, non lo si scrive nel backlog.
3. **Wallet lato server, uno per utente, «custodial per la demo»,
   dichiarato** — `rgb-lib-python` sulla VM: una `Wallet` per tg_id
   con la sua directory e la sua mnemonic nel config della VM (mai nel
   repo, mai in `impostazioni`), Barattolo che chiede la invoice per
   conto dell'utente e manda i punti dall'emittente. È la rete: non
   dipende dal browser, usa la nostra lingua, e il trasferimento RGB è
   vero esattamente come negli altri casi (due wallet, un consignment,
   una tx su signet). Va detto ai giudici in una riga: «in produzione
   la chiave sta nel dispositivo; qui la tiene il server per la demo».
   STIMA 4-6 h, già pagate in gran parte dalla preparazione (A).
4. **Il wallet sul telefono dell'utente**: Iris Wallet (Android,
   v0.3.1-73, varianti Signet/Testnet/Mainnet) o Tribe RGB (iOS e
   Android, v0.6.3) — la Mini App mostra la invoice RGB come QR e il
   wallet esterno riceve e manda. Zero custodia, zero WASM, e un
   trasferimento «fra due app diverse» impressiona; ma dipende da un
   wallet altrui su signet, con un telefono in più sul tavolo. Da
   tenere per il pitch se il giorno prima gira: non come piano.

**Raccomandazione:** la (3) si prepara comunque e si tiene accesa come
rete; la (2) si prova prima del Q&A del 13 e, se vive, diventa la demo
e vale il bonus; la (1) è il ripiego della (2); la (4) è un fiore
all'occhiello se avanza tempo. Mostrare DUE wallet dell'utente
(browser e server) non serve: uno solo, quello che gira.

## C. QVAC: dove gira e con quale modello

### C.1 Dove gira (VERIFICATO)

- `@qvac/sdk` `0.20.1` (28 set 2026), Apache-2.0, nessuna etichetta
  beta ma **breaking change ogni poche settimane** (0.19.0 il 7 set,
  0.20.0 il 22 set); anche Python `tetherto-qvac-sdk` 0.20.1. Runtime:
  **Node.js ≥ 22.17, Bare ≥ 1.24, Expo/React Native ≥ 54** su macOS 14+,
  iOS 17+, Linux (Vulkan ≥ 1.4), **Android 12+ arm64**, **Windows 10+
  x64**; RAM «≥ 4 GB o most LLMs will fail to load», ≥ 5 GB di disco.
- **Nel browser NO**, e lo dice Tether in una pagina di confronto:
  «WebLLM runs language models inside a browser tab on WebGPU… QVAC
  runs outside the browser, in Node.js, Bare or Expo, as a library
  linked into an application». Nessuna pagina della docs nomina
  browser, WASM o WebGPU come target. La via «browser» ufficiale è
  indiretta: l'interfaccia in una pagina, l'inferenza in un processo
  locale — il pattern di quasi tutti i quindici esempi di
  `qvac-examples` (server Node su 127.0.0.1 + UI HTML) e della CLI:
  `npm i -g @qvac/cli`, **`qvac serve --openai`** espone
  `/v1/chat/completions` compatibile OpenAI su `127.0.0.1:11434`, CORS
  spento salvo `--cors-origin`.
- Il modello sul telefono con QVAC vuol dire **un'app Expo** (dispositivo
  fisico, «QVAC currently does not run on emulators», Android 12+,
  `expo prebuild`, Android Studio + JDK; il tutorial è fermo alla
  0.7.0). Non è la Mini App, non è la TWA.

### C.2 Quale modello (VERIFICATO sui byte del registry)

| Costante | Peso | Nota |
|---|---|---|
| `LLAMA_3_2_1B_INST_Q4_0` | ~773 MB | il modello del quickstart e del tutorial Expo |
| `QWEN3_1_7B_INST_Q4` | ~1,0 GB | usato dai progetti da hackathon con tool calling (Treble) |
| `SMOLLM2_360M_INST_Q8` | ~368 MB | il ripiego per una macchina stretta |
| `QWEN3_4B_INST_Q4_K_M` | ~2,4 GB | lo starter della Developers Cup; da 16 GB |

Velocità su Android con QVAC: NON PUBBLICATA. La FAQ dell'hackathon:
«The models we recommend for this hackathon are small and quantized,
and run on an ordinary laptop. You only need one capable machine per
team», con «recommended models and minimum specs» nei tutorial. Il
criterio 2 dice «We look at how you use it, not at model size»: il 1B
basta.

### C.3 Come si usa per «hai 850 punti, puoi avere 5.000 sats di sconto» (VERIFICATO)

`completion({ modelId, history, stream, tools, responseFormat,
generationParams })`: `responseFormat` con JSON Schema «guaranteed to
parse» (changelog 0.10.0), tool calling con Zod e eventi `toolCall`
(`loadModel` con `modelConfig.tools: true`; «tool grammar» nella
0.20.0). Il nostro caso è un prompt strutturato — saldo in punti, regola
del negozio («100 punti = 500 sats, max 30% del prezzo»), prezzo
dell'ordine, sats disponibili — e uno schema `{usa_punti, quanti,
sats_sconto, motivo}`: il modello PROPONE, la pagina mostra, l'utente
APPROVA, il wallet manda i punti. È letteralmente la traccia 04 del
regolamento («Local AI that proposes, you approve») e la privacy è
reale: il saldo non esce dal portatile. Attenzione al breaking della
0.20.0 sul messaggio `system` con `kvCache`.

### C.4 Le tre strade, con stime (DA DECIDERE)

| Strada | Cos'è | STIMA | Rischi |
|---|---|---|---|
| **Processo locale + pagina** (raccomandata) | `qvac serve --openai` (o 60 righe di Node con `@qvac/sdk`) sul portatile della demo; la pagina di Barattolo chiama `127.0.0.1:11434` con `--cors-origin` sull'origin della pagina | 3-6 h | CORS e origin (la pagina su `https://barattolo.store` che parla a `http://127.0.0.1` è mixed content: la pagina va servita in locale, o si usa Electron); il modello va scaricato PRIMA (773 MB) |
| **App Electron «Barattolo Assistente»** | tutorial ufficiale electron-vite + React, SDK nel main, IPC al renderer; la stessa finestra può ospitare la pagina di Barattolo e il wallet browser (B.4-1/2) | 4-8 h + 2-4 di packaging | bundle grosso, `asar:false`, driver Vulkan su Windows; più «prodotto» da mostrare, meno Mini App |
| **App Expo Android** | QVAC sul telefono, dispositivo fisico, Android 12+, ≥ 4 GB RAM | 12-20 h | toolchain nativo (Gradle, NDK), tutorial indietro, nessun esempio mobile ufficiale, primo avvio lento |

Raccomandazione: la prima, perché «on device» nel nostro caso È il
portatile dei giudici (il criterio misura dove gira il modello, non il
form factor), e perché è l'unica che Andrea può far girare da solo in
una mattina. La seconda se Alan vuole il «prodotto» e c'è una persona
in più. La terza no: è un'app nuova, non Barattolo, e si mangia il
weekend. La domanda per i mentor è una sola: «la UI nella Mini App e
l'inferenza in un processo locale sul portatile contano come on-device
per il criterio 2?» — la pagina di confronto con WebLLM fa pensare di
sì, ma lo si chiede il 13.

## D. Il flusso minimo che vince

Il giudizio è 1-5 su cinque voci a pari peso (RGB, QVAC, esecuzione,
mercato, UX) più il bonus WDK; «Execution» pesa quanto si è costruito
NEL weekend, «UX» giudica «clarity of steps, error handling», non
l'estetica. Il flusso va scelto perché finisca, non perché stupisca.

**Le transazioni RGB da mostrare, nell'ordine in cui si fanno (quattro
vere, una dichiarata):**

1. **Emissione** (fatta PRIMA, dichiarata come pre-esistente): BRT e
   CAFFE-LUCA emessi su signet dal wallet emittente; si mostra il
   `contract_id`, il genesis e la tx di `create_utxos` sull'explorer.
   È infrastruttura, non integrazione: lecita prima, da elencare
   all'arrivo.
2. **Assegnazione** (in sede): un ordine di collaudo in Barattolo
   (111 compra da 222, LNbits finto, stato `confirmed`) → il server
   calcola i punti con la regola di casa (`XP_PER_EURO`, cioè la stessa
   cifra degli XP) → chiede al wallet dell'utente una invoice RGB
   (witness la prima volta) → l'emittente manda i BRT → tx su signet,
   consignment via proxy, ACK, broadcast. Il «Settled» arriva al blocco
   dopo: **si fa un'ora prima del pitch**, e in pitch si mostra lo
   stato e il link. In regtest sul portatile si può fare dal vivo con
   un `mine`, se il mentor dice che regtest vale.
3. **Riscatto** (in sede): nella pagina dell'ordine successivo,
   l'assistente QVAC locale propone («hai 850 BRT: 500 valgono 2.500
   sats su questo ordine»); l'utente approva; il wallet manda i BRT
   alla invoice dell'emittente; il server, vista la transazione (o
   l'ACK del consignment, con `min_confirmations` basso dichiarato),
   applica lo sconto in sats sull'importo dell'ordine. Lo sconto è un
   TERZO sconto accanto a fedeltà e banner (sezione 0): nel conto si
   mostra con la sua riga.
4. **Il punto del negozio** (in sede, se avanza): la stessa
   assegnazione con CAFFE-LUCA a un ordine del negozio consigliato, e
   la pagina del Consigliato che mostra il saldo e la regola dello
   sconto del negozio. Mostra che la forma scala; costa poco perché è
   la 2 con un altro `contract_id`.
5. **Lo swap nel P2P — «mostrato ma non in produzione», o fuori.**
   Mostro non conosce gli asset; uno swap RGB atomico su Lightning è
   RLN ai due capi più canali con liquidità, cioè il prodotto di
   KaleidoSwap, che siede in giuria. Due forme oneste: (a) un ordine
   Mostro con `fiat_code` «USDT» e metodo «RGB», dove chi compra sats
   paga l'asset alla invoice RGB di chi vende e la prova in disputa è
   il consignment — un flusso vero ma «in fiducia» come un bonifico,
   da etichettare «sperimentale»; (b) una slide. Raccomando (b), o
   niente: una quinta transazione fatta male toglie punti a «Execution»
   e a «UX» più di quanti ne dia a «RGB usage».

**Cosa dichiarare «mostrato ma non in produzione»:** la rete (signet),
il wallet lato server se è quello che gira, l'emissione dell'asset del
negozio fatta da Barattolo per conto suo, la regola dello sconto scritta
in config invece che scelta dal negozio nel suo pannello, lo sconto in
sats applicato a un ordine con LNbits finto (il modo in cui Barattolo
collauda sempre), e il fatto che la Mini App vera su iOS non avrebbe un
wallet nella pagina (B.3).

**Cosa invece deve essere vero senza asterischi:** le transazioni RGB
2 e 3 (due wallet, consignment, tx in un blocco), il modello che gira
sul portatile senza rete, l'utente che approva con un tocco.

## E. Il piano in due parti

### E.1 Prima dell'evento (dal 2 al 16 ottobre), senza toccare il lancio

Tutto quel che segue è infrastruttura e apprendimento, lecito dal
regolamento, e **non tocca `main`** tranne un commit: la leva spenta.

| Quando | Cosa | STIMA | Chi |
|---|---|---|---|
| **entro il 3 ott** | Candidarsi: un modulo a testa (`forms.gle/AdoCUYeL4z5hpA3a6`), «team di 2», presenza due giorni, due righe su cosa si vuole costruire (la fidelity card RGB sopra un mercatino Lightning che esiste e lancia il 10) | 1 h | Andrea e Alan |
| 2-5 ott | La VM «rgb-prova»: Linux, docker, `rgb-lib-python` in venv, proxy nostro; chiavi e password in un config fuori dal repo; backup cifrato age sul calco di `backup-nodo.sh` | 4-6 h | Andrea con i comandi scritti uno alla volta |
| 2-5 ott | Signet: un faucet (da trovare), `create_utxos`, emissione di BRT e CAFFE-LUCA, due wallet di prova (A e B) che si scambiano asset blind e witness, `refresh`, backup e restore provati davvero (drill, come per il nodo) | 4-8 h | Andrea |
| 6-9 ott | Regtest sul portatile (WSL2, `rgb-sandbox`) per avere una rete che non aspetta dieci minuti, e per lavorare in treno | 2-3 h | chi vuole |
| 6-9 ott | QVAC sul portatile della demo (Windows nativo): `npm i -g @qvac/cli`, `qvac serve --openai`, Llama 3.2 1B e Qwen3 1.7B SCARICATI, una chiamata con `responseFormat` provata da una pagina locale | 2-4 h | Andrea |
| **10 ott** | **Il lancio.** Niente dell'hackathon tocca il VPS quel giorno. | — | — |
| 11-12 ott | Un commit solo su main: `RGB_ATTIVO = False` e `RGB_PROVA_IDS` in `config_esempio.py`, la riga nel pannello «Stato delle leve», la prova che a leva spenta nessuna rotta nuova risponde. Nessuna rotta, nessun modulo: solo il cancello | 2 h + prove | Claude con Andrea |
| 11-12 ott | I pacchetti del browser (B.4-2 e B.4-1) provati in una cartella FUORI dal repo, in Chrome, su signet: due ore ciascuno, poi si decide quale vive | 4 h | Alan, se è il suo pezzo |
| **13 ott** | Q&A tecnico con i mentor (solo confermati): le domande in E.3 | 1-2 h | tutti e due |
| 14-16 ott | Si legge il run-of-show; si decide la rete (regtest o signet) e il wallet (browser o server); si scrive su carta il flusso D con gli schermi; backup della VM; portatile con tutto scaricato; un secondo portatile o la VM come riserva | 3-4 h | tutti e due |

Costo vivo: la VM (pochi euro al mese) e il viaggio. Niente spese di
protocollo: signet vale zero.

**Cosa NON si fa prima**, perché il regolamento lo vieta e perché
toglierebbe punti a «Execution»: le rotte `/api/rgb/*`, la UI del
saldo, il foglio del riscatto, la chiamata a QVAC dalla pagina, la riga
dello sconto nel conto. Si possono DISEGNARE (uno schizzo per schermo,
i nomi delle funzioni, dove si aggancia in `server.py`: accanto a
`_fedelta_sconto` per lo sconto, accanto a `xp_eventi` per i punti,
accanto a `consigliati_pubblici` per il negozio) — e il disegno si
porta a Torino.

### E.2 All'evento (17-18 ottobre)

| Ora | Cosa | Note |
|---|---|---|
| sab 09:00-10:00 | Kickoff; **dichiarazione del pre-esistente** ai mentor (Barattolo com'è, la VM, gli asset, la leva); una copia del db di collaudo con 111/222/999 | il verbale del pre-esistente lo scriviamo noi, in una pagina, e lo consegniamo |
| sab 10:00-13:00 | Server: `rgb.py` (o la sezione in `server.py`) che apre il wallet emittente e, dietro la leva, i wallet utente; `POST /api/rgb/invoice`, `/api/rgb/assegna` (chiamata da `confirmed`), `/api/rgb/saldo`. Prove minime con `prova()` | commit datati, uno per funzione |
| sab 13:00-16:00 | Client: la voce «🪙 I miei punti» nel Profilo (dentro il cassetto giusto, sulla forma del 25 set), il saldo per asset, la invoice come QR/testo; il pannello admin con «assegna punti a questo ordine» per la demo | prima assegnazione VERA su signet entro le 16 |
| sab 16:00-19:00 | QVAC: la chiamata dalla pagina dell'ordine al processo locale, lo schema JSON, il foglio «L'assistente propone» con «Approva» / «No, grazie» | il modello è già sul disco |
| sab sera | Riscatto: `POST /api/rgb/riscatta`, la riga di sconto nel conto, lo stato dell'ordine che lo mostra; secondo trasferimento vero | qui si decide se il browser-wallet vive o si resta sul server |
| dom 09:00-12:00 | Il giro intero tre volte di fila senza toccare il codice; gestione degli errori visibile («proxy irraggiungibile», «conferma in arrivo»); l'asset del negozio se avanza | «UX: error handling» è un criterio |
| dom 12:00-14:30 | Le assegnazioni per il pitch fatte e confermate; slide: 6 (problema, cosa c'era venerdì, cosa c'è domenica, le tx sull'explorer, QVAC, cosa resta); prova del pitch a tempo | niente codice dopo le 14 |
| dom 15:00 | Consegna | repo con i commit del weekend su un ramo o dietro la leva |
| dom 16:00 | Pitch | il portatile con modello e wallet, la VM in riserva, un hotspot |

**Rischi, in ordine di probabilità:**
1. **Il proxy o l'indexer pubblico non risponde** il sabato → proxy
   nostro sulla VM e indexer di riserva (Iris testnet4, o mempool
   signet); su regtest in locale non ci sono terzi.
2. **Il wallet browser non si bundla** → si resta sul server (B.4-3),
   deciso entro sabato sera, senza discussione.
3. **Mixed content** fra pagina HTTPS e `127.0.0.1` → la pagina della
   demo si serve in locale (`http://127.0.0.1:8080`, come in collaudo),
   o il processo QVAC gira dietro Caddy locale con TLS; da provare il 9.
4. **Blocchi signet lenti** nel momento sbagliato → tutte le tx del
   pitch fatte un'ora prima; nel pitch si rifà solo il «proposta →
   approva → invio», e si mostra lo stato `WaitingConfirmations`,
   che è anch'esso vero.
5. **La seed su due processi** (il server che riavvia con un wallet
   ancora aperto) → un solo processo per wallet, lock, e il riavvio
   fatto a mano.
6. **Il portatile** → la VM e un secondo portatile con il modello già
   scaricato.
7. **Le regole dette a voce diverse dalla pagina** (rete, cosa conta
   come «on device», consegna) → chiederlo il 13 e scriverlo.

### E.3 Cosa chiedere ai mentor il primo giorno (e al Q&A del 13)

1. **La rete**: regtest in sede vale come «working transactions, not
   simulated»? O vogliono signet/testnet4 con un explorer pubblico?
   Forniscono asset di prova, un faucet o un proxy per l'evento?
2. **«On device» per il criterio 2**: l'inferenza in un processo locale
   sul portatile (`qvac serve`) con la UI in una pagina web conta
   pieno? E l'app Electron?
3. **Il bonus WDK**: il modulo RGB per browser di Darkhorse è «WDK»
   agli occhi del team WDK, o il bonus vuole un modulo ufficiale
   (`wallet-btc` per i sats, per esempio)? Un `wallet-btc` su signet
   che finanzia gli UTXO colorati dell'utente varrebbe «centrale»?
4. **Utexo**: gli endpoint signet pubblici (`esplora-api`, `rgb-proxy`)
   reggono il weekend e si possono usare? C'è un faucet signet loro?
   Il `witness_receive` è la via giusta per il primo invio a un utente
   senza sats?
5. **KaleidoSwap**: come vedono un marketplace che fa punti-asset senza
   canali, e se lo swap on-chain «in fiducia» su Mostro è una cosa che
   vorrebbero vedere o no.
6. **Consegna**: repo pubblico sì/no, licenza, durata del pitch, se
   guardano i commit.
7. **CypherTank**: il posto garantito vale per le finali del 25-27
   ottobre o per la stagione dopo (la pagina dice «finals», rgb.info
   «semifinals»).

## F. Il regolamento, letto sulla pagina

Tutto VERIFICATO su `rgbprotocol.org/agentic-dollars-hackathon/` (letta
per intero il 1 ott 2026) salvo dove detto.

- **Lavoro fatto prima**, testuale: «Yes, but we only judge what you
  build during the hackathon. Declare what already exists when you
  arrive, keep the weekend's work in dated commits, and do the RGB and
  QVAC integration on site.» E nel criterio 3: «how much substantial
  work was done during the hackathon hours». Quindi: Barattolo intero,
  la VM, gli asset emessi, i pacchetti provati e il modello scaricato
  sono **pre-esistente da dichiarare**; le rotte, la UI, la chiamata a
  QVAC e il riscatto sono **lavoro del weekend**, in commit datati.
- **Cosa va dichiarato**: «what already exists when you arrive» — la
  pagina non dà un modulo; lo scriviamo noi (una pagina: cos'è
  Barattolo, cosa c'era venerdì sera con gli hash dei commit, cosa
  faremo). È anche la prima slide.
- **Tecnologie**: RGB obbligatorio («Issue, transfer and verify assets
  on Bitcoin, with client-side validation»), QVAC obbligatorio («Run AI
  models directly on device… with no cloud»), WDK bonus («a working
  integration earns extra points on top of your total, and a well-built,
  central integration earns the full bonus»). «Working transactions,
  not simulated» è il criterio RGB; **la rete NON è specificata**.
- **Giudizio**: cinque criteri da 1 a 5 a pari peso (RGB usage, QVAC
  and local AI, Execution, Marketability, UX and UI), ogni giudice
  vota ciascuno. Giudici «team members from Tether, KaleidoSwap and
  Utexo»; i nomi «closer to the event». Mentor WDK e QVAC in sede
  «across both days».
- **Premi**: 4.000 € + posto garantito «in the CypherTank finals»
  (Lugano), 1.500 €, 500 €.
- **Squadre e iscrizione**: 2-4 persone, solisti abbinati; ~70 posti;
  gratis, pasti coperti, viaggio e alloggio no; selezione «for
  motivation and for a clear vision… not for a long CV»; **ogni
  membro compila il suo modulo**; conferme 4-12 ottobre; **tutorial
  registrati per RGB, QVAC e WDK a tutti i candidati** (dal 24 set);
  Q&A tecnico live il 13 ottobre ai confermati; run-of-show ai
  confermati prima del weekend.
- **⚠️ La scadenza**: la pagina dice «October 7» in due punti e nella
  timeline, ma il nastro scorrevole della stessa pagina dice «APPLY BY
  03.10», come rgb.info e Atlas21 del 17-18 settembre. Lettura:
  spostata al 7, il nastro è un residuo. **Si manda entro il 3.**
- **Programma**: sabato 09:00 porte e kickoff; domenica 15:00 fine
  lavori e consegna, dalle 16:00 pitch e premi «with train travelers in
  mind». Orari notturni: non scritti. Sede BLOX, Via Pietro Micca 21
  (indirizzo da blox.space; la pagina dice solo «central Turin»).
- **NON TROVATO sulla pagina**: licenza/IP dei progetti, obbligo di
  repo pubblico, formato della consegna (video, slide, durata), nomi
  dei giudici, infrastruttura fornita (nodo, faucet, asset), hardware
  richiesto («Nothing exotic… one capable machine per team»). Nessuna
  edizione precedente di questo hackathon; i precedenti di Tether
  (Galactica WDK, Developers Cup, QVAC Hackathon I) sono online e
  chiedevano «All inference must use the QVAC SDK» e progetti open
  source — indizio, non regola, per Torino.

## Raccomandazione, in dieci righe

1. **Candidarsi entro il 3 ottobre**, un modulo a testa, squadra da due.
2. **Niente al VPS e niente al nodo** prima del 10; l'hackathon vive su
   una VM nuova su signet e sul portatile.
3. **I «dollari» li emettiamo noi** (NIA su signet): USDT su RGB non
   c'è al pubblico, e non si aspetta.
4. **Il wallet dell'utente lato server, dichiarato, come rete**; quello
   nel browser (modulo WDK Darkhorse, poi `rgb-sdk-web`) come tentativo
   deciso entro sabato sera. Mai una seed di utenti veri sul server.
5. **QVAC in un processo locale sul portatile** con `responseFormat`
   JSON: propone, l'utente approva. Modello Llama 3.2 1B o Qwen3 1.7B,
   scaricato prima.
6. **Il flusso minimo**: emissione (prima), assegnazione dopo un ordine,
   riscatto con sconto in sats, l'asset del negozio se avanza.
7. **Lo swap nel P2P fuori dalla demo**: una slide, o niente.
8. **Prima del 17 solo infrastruttura e una leva spenta su main**; il
   codice che integra si scrive a Torino in commit datati, e il
   pre-esistente si consegna scritto.
9. **Le sette domande di E.3 il 13 ottobre**, scritte e con le
   risposte scritte accanto.
10. **Dopo l'evento**, se la cosa è piaciuta: il cantiere vero sarebbe
    «i punti come asset RGB» con la seed nel dispositivo e un VSS
    nostro per lo stash — un cantiere da settimane, dietro la leva, che
    non si confonde con la demo.

## Fonti

Lette il 1 ott 2026; «API» = letto sull'API GitHub o sul registry npm,
che danno le date più affidabili.

- **Hackathon**: https://rgbprotocol.org/agentic-dollars-hackathon/
  (pagina ufficiale, letta per intero: regole, criteri, premi, FAQ,
  programma, strumenti, giudici); https://forms.gle/AdoCUYeL4z5hpA3a6
  (modulo, domande lette una per una);
  https://rgb.info/rgb-tether-hackathon-agentic-dollars/ (17 set 2026,
  dice 3 ottobre e «semifinals»);
  https://atlas21.com/turin-rgb-hackathon-ai-digital-dollars-bitcoin/ ;
  https://rgbprotocol.org/about/ , https://rgbprotocol.org/members/ ,
  https://rgbprotocol.org/terms-of-use/ ; https://blox.space/ (sede);
  https://bitcoinmagazine.com/news/cypher-tank-bitcoin-event-returns
  (CypherTank 2026); i precedenti
  https://www.hackathons.space/hackathons/tether-hackathon-galactica-wdk-edition-1 ,
  https://dorahacks.io/hackathon/tether-developers-cup/detail e
  https://dorahacks.io/hackathon/qvac-unleach-edge-ai-i/detail (letti
  tramite un lettore testuale: il sito risponde 405),
  https://github.com/edycutjong/punditpay ,
  https://github.com/edycutjong/treble ,
  https://qvac.tether.io/blog/the-future-of-ai-is-local/ . Non
  leggibili: https://x.com/RGBAssociation (402).
- **RGB, le due linee**: https://docs.rgb.info/ e
  https://github.com/rgb-protocol/RGB-Documentation (la nota su
  «v0.12 unfinished proposal»); https://github.com/rgb-protocol e
  https://api.github.com/repos/rgb-protocol/rgb-consensus/releases
  (0.11.1 del 16 set 2026);
  https://rgb.info/rgb-protocol-v0-11-1-core-libraries-update/ ,
  https://rgb.info/rgb-protocol-myths-debunked/ ,
  https://rgb.info/rgb-v0-11-1-vs-v0-12/ ,
  https://rgb.info/rgb-v0-11-1-bitcoin-mainnet-launch/ ,
  https://rgb.info/rgb-faq/ , https://rgb.info/build/developer-tools/ ;
  https://rgb.tech/blog/release-v0-12-consensus/ e
  https://rgb.tech/blog/on-rgb-fork-by-bitfinex/ (lug 2025);
  https://api.github.com/repos/RGB-WG/rgb/releases e …/commits
  (ultimo commit 20 lug 2025).
- **rgb-lib e RLN**: https://github.com/RGB-Tools/rgb-lib (README:
  «never instantiate a wallet in multiple places»), …/releases (API,
  0.3.0-beta.7), …/tree/master/bindings ;
  https://docs.rs/rgb-lib/0.3.0-beta.7/rgb_lib/ (Wallet, `blind_receive`,
  `witness_receive`, `create_utxos`, `restore_backup`);
  https://pypi.org/project/rgb-lib/ (0.3.0b7, 18 lug 2026);
  https://github.com/RGB-Tools/rgb-lightning-node (README, `openapi.yaml`,
  `Cargo.toml`, `regtest.sh`; nessuna release);
  https://github.com/UTEXO-Protocol/rgb-lightning-node e
  https://github.com/UTEXO-Protocol/rgb-lightning-node/pull/177
  (Lightning spento su mainnet, 29 set 2026);
  https://github.com/RGB-Tools/rgb-proxy-server ,
  https://github.com/RGB-Tools/faucet-rgb ,
  https://github.com/rgb-protocol/rgb-sandbox ;
  https://docs.rgb.info/annexes/contract-transfers.md ,
  https://docs.rgb.info/annexes/invoices.md ,
  https://docs.rgb.info/commitment-layer/deterministic-bitcoin-commitments-dbc/opret.md ,
  https://docs.rgb.info/rgb-over-lightning-network/lightning-network-compatibility.md ;
  https://rgb.info/rgb-ownership/ (la seed non basta).
- **USDT su RGB**:
  https://tether.io/news/tether-to-launch-usdt-on-rgb-expanding-native-bitcoin-stablecoin-support/
  (28 ago 2025);
  https://bitcoinmagazine.com/business/usdt-returns-to-bitcoin-rgb-and-utexo-enable-private-lightning-settlements
  (6 lug 2026, «within weeks»);
  https://rgb.info/bitcoin-magazine-rgb-protocol-usdt-utexo/ ;
  https://blog.bitfinex.com/industry-news/will-usdt-on-rgb-accelerate-rgb-adoption/
  (17 lug 2026); https://rgb.info/unisat-usdt-bitcoin-launch-partner/
  (4 set 2026);
  https://www.thecoinrepublic.com/2026/09/25/stablecoin-news-tether-ceo-confirms-usdt-is-coming-to-bitcoin/ .
- **Wallet utente**: https://rgb.info/ecosystem/rgb-wallets/ ;
  https://github.com/RGB-Tools/iris-wallet-android (v0.3.1-73);
  https://github.com/RGB-Tools/iris-wallet-desktop ;
  https://github.com/bithyve/bitcoin-tribe (v0.6.3);
  https://github.com/bitmask-stack/bitmask-core e …/issues/457 .
- **WDK**: https://docs.wdk.tether.io/ , …/overview/about/ ,
  …/sdk/get-started/ , …/start-building/nodejs-bare-quickstart/ ,
  …/overview/changelog/ , …/sdk/wallet-modules/which-wallet-module/ ,
  …/sdk/wallet-modules/wallet-btc/configuration (WebSocket «required
  for browser»), …/sdk/community-modules/wdk-wallet-rgb/ ,
  …/sdk/community-modules/wdk-rgb-lightning/ , …/tools/secret-manager ,
  …/overview/showcase ; https://wdk.tether.io/developers/playground ;
  https://github.com/tetherto/wdk ;
  https://registry.npmjs.org/@tetherto/wdk (1.0.0-beta.18) e
  …/@tetherto/wdk-wallet-btc ;
  https://registry.npmjs.org/@utexo/wdk-wallet-rgb (2.0.3) e
  https://github.com/UTEXO-Protocol/wdk-wallet-rgb ;
  https://registry.npmjs.org/@utexo/rgb-sdk ,
  …/@utexo/rgb-lib-bare («not Node.js or browsers»),
  …/@utexo/wdk-rgb-lightning e
  https://github.com/UTEXO-Protocol/wdk-rgb-lightning ,
  https://rgb.info/wdk-rgb-lightning-architecture/ (1 set 2026);
  https://registry.npmjs.org/@utexo/rgb-lib-wasm (1.0.0-beta.3, 13,8
  MB) e https://github.com/UTEXO-Protocol/rgb-lib-wasm ;
  https://registry.npmjs.org/@utexo/rgb-sdk-web (1.0.0-beta.12) e
  https://github.com/UTEXO-Protocol/rgb-sdk-web ,
  https://github.com/UTEXO-Protocol/rgb-sdk-web-sandbox ,
  https://rgb.info/utexo-rgb-sdk-bridge-community-call-demo/ ;
  https://registry.npmjs.org/@darkhorse-wallet/wdk-wallet-rgb (0.1.1,
  26 set 2026), https://github.com/RGB-Launchpad/wdk-wallet-rgb-browser
  (README) e https://github.com/RGB-Launchpad/wallet-ext ;
  https://github.com/base58-io/wdk-starter-browser-extension e
  https://github.com/Khristo19/dtms-wallet (la ricetta del seed cifrato
  nel browser); https://github.com/UTEXO-Protocol/webrgb .
- **Mini App e storage**: https://core.telegram.org/bots/webapps (Bot
  API 9.6: CloudStorage, SecureStorage, DeviceStorage);
  https://docs.telegram-mini-apps.com/platform/about ;
  https://caniuse.com/wasm ;
  https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria
  (Safari 7 giorni, Chrome LRU); https://developer.apple.com/forums/thread/766309 .
- **QVAC**: https://qvac.tether.io/ , https://qvac.tether.io/compare/web-llm
  («QVAC runs outside the browser»), https://qvac.tether.io/blog/one-sdk-for-all-of-your-ai ,
  https://qvac.tether.io/blog/what-your-own-machine-can-run (1 ott 2026),
  https://qvac.tether.io/changelog (0.10.0 `responseFormat`, 0.20.0 tool
  grammar); https://docs.qvac.tether.io/ , …/js-ts-sdk/ (Node, Bare,
  Expo), …/system-requirements/ , …/reference/api/ ,
  …/ai-capabilities/text-generation/ , …/tutorials/expo/ ,
  …/tutorials/electron/ , …/cli/http-server/ (`qvac serve --openai`,
  11434), …/models/assess-model-fit ; https://github.com/tetherto/qvac
  (README, releases: sdk-v0.20.1 del 28 set 2026),
  https://raw.githubusercontent.com/tetherto/qvac/main/packages/inference/src/models/registry/models.ts
  (i pesi); https://registry.npmjs.org/@qvac/sdk/latest ;
  https://pypi.org/pypi/tetherto-qvac-sdk/json ;
  https://github.com/tetherto/qvac-examples ,
  https://github.com/tetherto/qvac-football-predictor ,
  https://github.com/holepunchto/hello-pear-qvac-tui ;
  https://news.ycombinator.com/item?id=47708697 .
- **KaleidoSwap e Utexo**: https://github.com/kaleidoswap/desktop-app ,
  https://github.com/kaleidoswap/kaleido-sdk («testnet/signet use
  only»), https://docs.kaleidoswap.com/ ,
  https://rgb.info/rgb-lightning-sovereign-trading-kaleidoswap-mvp/ ,
  https://rgb.info/kaleidoswap-pre-seed-rgb-dex-bitcoin-lightning/ ;
  https://github.com/UTEXO-Protocol , https://utexo.com/ ,
  https://rgb.info/usdt-on-bitcoin-utexo-rgb-lightning/ ,
  https://rgb.info/matteo-branchetti-utexo-stablecoins-on-bitcoin/ .
  Non leggibili: https://kaleidoswap.com/ (403), https://utexo.io/
  (vuota), npmjs.com (403: letto il registry).
- **Mostro**: https://github.com/MostroP2P/mostro/issues?q=rgb+OR+stablecoin+OR+usdt
  (nessuna issue sul tema).
- **In casa**: `CLAUDE.md` (regole ferree 2, 3, 6; «Adesso»),
  `docs/ARCHITETTURA.md` («LA SCALA NOSTR APPROVATA», «LE ROTTE
  PUBBLICHE», «Distribuzione dell'APK»), `docs/CANTIERI.md` («Le
  commissioni per persona: lo sconto fedeltà del P2P», «LA VALUTA È
  UNA TENDINA CON UNA VOCE SOLA», «Il profilo più elegante»),
  `docs/NODO-MOSTRO.md` («LA DEV FEE SI IMPIANTA SUL CIRCUITO
  FREDDO»), `docs/PRODUZIONE.md` (il backup del nodo),
  `config_esempio.py` (le leve P2P), `server.py` e `miniapp.html` alle
  righe citate.

---

# Parte seconda (7 ottobre 2026): le idee di Alan, e cosa reggono

Sola lettura, nessun codice. Base `origin/main` a `5785342`; il VPS, il
nodo Mostro, il relay e la VM rgb-prova non sono stati toccati. Le fonti
nuove sono in fondo a questa parte, lette il 7 ott 2026; i tutorial su
Drive sono video e non li ho visti. La prima parte (1 ott) resta com'è:
dove questa la corregge, lo dice.

**Le novità, in una riga ciascuna.** 1) La demo diventa «**Il
Cassiere**»: si paga un ordine in dollari di prova **USDB** su RGB, l'AI
locale (QVAC) propone e l'utente approva, il wallet WDK è al centro, i
punti MOON sono il bonus, poi salvadanaio e budget privato se avanza.
2) Barattolo parla col wallet attraverso un'**estensione di NIP-47** per
gli asset RGB (`rgb_list_assets`, `rgb_make_invoice`, `rgb_pay_invoice`,
notifiche), pubblicata come bozza durante l'hackathon. 3) **L'emittente
legato a un'identità Nostr**: un evento firmato dalla chiave
dell'emittente dichiara l'asset_id e i metadati, verificabile via
NIP-05 — un web of trust (MOON da To The Mooon ha senso, «USDT» da uno
sconosciuto no). 4) Roadmap: Mostro con asset RGB, consegne via relay
Nostr al posto del proxy, certificati di autenticità per le edizioni
limitate (le magliette numerate di AGORA), per un grant. 5) Nel pitch,
nei primi 30 secondi, chi siamo. Priorità: core (checkout in USDB +
Cassiere + WDK che paga), poi il NIP minimo con l'emittente verificato
nella schermata, poi budget e salvadanaio, roadmap solo slide. JAR fuori.

**La risposta corta.** Regge, e meglio di quanto Alan sapesse:
**il protocollo RGB 0.11 ha GIÀ il posto per l'identità dell'emittente**
— ogni genesis porta un campo `issuer` (una stringa ASCII fino a 4096
caratteri, impegnata nel ContractId, con la nota «i controlli si fanno a
livello applicativo»), che rgb-lib oggi riempie sempre con
`ssi:anonymous`. L'idea di Alan è quindi il livello applicativo che il
consenso aspetta: **l'evento Nostr firmato dice «questo contratto è
mio», e il genesis può dire «il mio emittente è questa chiave Nostr»** —
le due metà si chiudono a vicenda e nessuno può attaccare l'identità di
Tether a un contratto che Tether non ha firmato. Non esiste nessun NIP
né bozza che lo faccia (cercato nel repo dei NIP: zero issue o PR con
«RGB»); gli analoghi da cui copiare la forma sono NIP-87 (gli annunci
delle zecche Cashu, con le raccomandazioni degli utenti: il web of
trust già scritto) e NIP-73 (gli identificatori esterni: `bitcoin:tx:…`
è la riga da cui nasce `rgb:contract:…`). **Sul lato wallet il NIP-47
ha cambiato forma dal 1 ott**: il nucleo è stato ridotto a cinque
metodi e tutto il resto — notifiche, hold invoice, BOLT12, BIP-321 —
vive come **estensioni numerate in un repo apposta**
(`nostr-wallet-connect/nwc`), con un processo in tre righe («apri
prima una issue, non assegnarti il numero»). La nostra estensione RGB è
esattamente un file di quel repo, e il client NWC di Barattolo
(`metodiNwc`, che legge `get_info.methods`) la scopre senza cambiare
niente. **Attenzione a due cose che NON reggono come sono scritte.**
(a) «Non custodial» nel pitch va detto con precisione: il P2P (Mostro)
e il wallet dell'utente lo sono, il deposito di garanzia del mercatino
lo tiene Barattolo per la durata dell'ordine (LNbits custodial, è
scritto in CLAUDE.md): «su protocolli aperti, con l'utente padrone dei
suoi sats nel P2P e nel suo wallet» è vero, «tutto non custodial» no, e
in una giuria con Utexo e KaleidoSwap la precisione paga. (b) KaleidoSwap
— che siede in giuria — ha pubblicato il 26 set **WebRGB**, un provider
`window.rgb` sul calco di WebLN con gli stessi metodi che vogliamo noi
(`listAssets`, `blindReceive`, `witnessReceive`, `sendAsset`,
`getTransferStatus`, eventi `transferReceived`/`transferSettled`),
e ha un wallet mobile **Rate** «non custodial, multi-protocollo, con
un assistente AI on-device» su QVAC, Nostr-native e con NWC. Non è un
problema: è il modo di presentare la nostra estensione — **«WebRGB
sopra NWC»**, gli stessi nomi e le stesse forme, per il wallet che non
sta nella stessa pagina (il telefono, il portatile, Rate) — e la
domanda giusta per il Q&A. Il Cassiere non compete con Rate: Rate è il
wallet, Barattolo è la cassa.

## A. Il NIP «asset RGB su Nostr»: regge? E cosa c'è già

### A.1 L'identità dell'emittente nel protocollo RGB (VERIFICATO sul sorgente)

- In `rgb-consensus` (la linea 0.11.1 di rgb-protocol), il `Genesis` ha
  il campo **`issuer: Identity`**: «An ASCII printable string up to
  4096 chars representing identity of the developer. We deliberately do
  not define the internal structure of the identity such that it can be
  updated without changes to the consensus level. Contract or schema
  validity doesn't assume any checks on the identity; **these checks
  must be performed at the application level**». Il default è
  `ssi:anonymous`. `Identity` implementa `CommitEncode`: **entra
  nell'impegno del genesis, cioè nel ContractId** — cambiarlo cambia
  l'asset. `rgb-ops` lo legge in `ContractInfo.issuer` e lo stampa come
  «Developer: …».
- **rgb-lib lo lascia anonimo**: in `src/wallet/offline.rs` tutte e
  quattro le emissioni (NIA, UDA, CFA, IFA) chiamano
  `ContractBuilder::with(Identity::default(), …)`; nessun parametro lo
  espone, né `issue_asset_nia` né `list_assets` lo restituiscono.
  Quindi **JAR e MOON hanno `issuer = ssi:anonymous`** e non si
  cambia: un NIA non si riemette con lo stesso id.
- **La CLI `rgb` di rgb-protocol lo espone**: `rgb issue <issuer>
  <contract.yaml>` prende l'identità come primo argomento. Si potrebbe
  emettere USDB con `issuer = nostr:<pubkey hex>` da lì, ma è un
  attrezzo diverso da rgb-lib con un suo stash: imparare e provare
  l'interoperabilità costa 4-8 ore e un rischio nuovo a dieci giorni
  dall'evento. L'alternativa è una patch di quattro righe a rgb-lib
  (un argomento `issuer` opzionale) e la ricompilazione della ruota
  Python: toolchain Rust, 3-5 ore, da fare sul PC e non sulla VM da 4
  GB. **Nessuna delle due prima del 17 se non avanza tempo**: la demo
  regge al livello 1 (sotto), e il livello 2 si DICE — «il campo c'è,
  rgb-lib non lo espone ancora: ecco la issue aperta a RGB-Tools».
- Lo schema NIA, invece, non ha nessun campo per l'emittente
  (VERIFICATO su docs.rgb.info: `spec` con ticker, name, details,
  precision; `terms` con testo e allegato; `issuedSupply`): l'unico
  posto libero sarebbe la stringa `details`/`terms`, e quello sì che
  rgb-lib lo scrive. Metterci `nostr:<npub>` è un ripiego leggibile
  dai wallet di oggi (Iris mostra i terms), non un impegno: il campo
  giusto è `issuer`.

### A.2 Due livelli di verifica, e cosa impedisce ciascuno

| Livello | Chi afferma cosa | Cosa impedisce | Cosa non impedisce |
|---|---|---|---|
| **1 — dichiarato** | la chiave Nostr dell'emittente firma un evento: «il contratto `rgb:…` è mio», con i metadati | che qualcuno attacchi l'identità di Tether a un contratto suo: Tether non lo firma; che un wallet mostri «Tether» su un asset che Tether non ha mai nominato | che un impostore firmi un SUO contratto con un SUO NIP-05 su `tether-usd.xyz`: lì decide la fiducia nel dominio, come per ogni NIP-05; e che due chiavi dichiarino lo stesso contratto (il wallet le mostra entrambe, e le raccomandazioni di chi segui — il web of trust — scelgono) |
| **2 — impegnato** | il genesis porta `issuer = nostr:<pubkey>` e l'evento del livello 1 è firmato da quella chiave | che due chiavi reclamino lo stesso contratto: il ContractId stesso dice di chi è | niente di nuovo sul dominio: la fiducia resta nel NIP-05 |

Per la demo: MOON al livello 1 (è già emesso anonimo), USDB al livello
1 e, se la patch si fa, al livello 2 — il contrasto fra i due è una
slide che spiega il NIP meglio di qualunque frase.

### A.3 Cosa esiste già di simile (VERIFICATO)

- **Nel repo dei NIP: niente.** Zero issue e zero PR con «RGB»; nessuna
  PR su «asset/token/stablecoin» che leghi un contratto a una chiave.
  La PR #1658 «Asset prices» è un feed di prezzi, non un'identità.
- **NIP-87** (Cashu/Fedimint discoverability) è il calco più vicino:
  l'operatore della zecca pubblica un evento addressable (`kind:38172`)
  con `d` = la chiave della zecca, `u` = l'URL, `n` = la rete
  (`mainnet|testnet|signet|regtest`), i `nuts` supportati; gli UTENTI
  pubblicano raccomandazioni (`kind:38000`) con `k` = il kind
  raccomandato, `d`, e un tag `a` che punta all'annuncio «per
  disambiguare duplicati che reclamano la stessa zecca». È il web of
  trust di Alan già scritto: si cambia «zecca» con «contratto».
- **NIP-73** (external content ids): `["i", "bitcoin:tx:<txid>"]` con
  `["k", "bitcoin:tx"]`, `bitcoin:address:…`, `isbn:…`, `doi:…`. Non ha
  una procedura per i tipi nuovi (si aggiunge una riga alla tabella con
  una PR): la nostra riga è `rgb:contract:<ContractId>` con `k` =
  `rgb:contract`, e da quel momento qualunque nota su Nostr può parlare
  di un asset.
- **NIP-05** è `final`: `GET https://<dominio>/.well-known/nostr.json?
  name=<nome>`, `names` con la chiave in hex minuscolo, la verifica in
  **due versi** (il kind 0 dichiara il nip05 E il JSON nomina quella
  chiave), «**MUST NOT return any HTTP redirects**» e chi legge «MUST
  ignore any HTTP redirects», `Access-Control-Allow-Origin: *` per il
  browser. In casa c'è già il giudice giusto per quella GET:
  `url_api_ammesso` (solo https sulla 443, host pubblico, mai loopback)
  con `follow_redirects=False`, nato il 1 ott per la SSRF del Lightning
  address — la verifica NIP-05 lato server è lo stesso gesto.
- **NIP-39** (identità esterne) e **NIP-89** (handler) dicono la forma
  dei tag `i` con prova e degli eventi addressable con `d` casuale:
  utili come stile, non come base.
- **NIP-47 oggi** (VERIFICATO sul master del 7 ott): `draft optional`,
  tre kind (13194 info, 23194 richiesta, 23195 risposta), **cinque
  metodi nel nucleo** (`pay_invoice`, `make_invoice`, `lookup_invoice`,
  `get_balance`, `get_info`), tag `encryption` e **tag `extensions`**
  («02 03 04»), `get_info.extensions`; i metodi aggiunti dalle
  estensioni «SHOULD also appear in content». Le estensioni stanno in
  `github.com/nostr-wallet-connect/nwc` (★4, ultimo push 11 set 2026):
  02 notifiche (kind 23197, payload generico `{notification_type,
  notification}`), 03 hold invoice, 04 keysend, 05 storico, 06
  metadati, 07 deep link, 08 connessione creata dal client, 09
  `lookup_payment`, 12 BOLT12, **321 BIP-321 (`pay`/`receive`)** — il
  modello di forma per la nostra. CONTRIBUTING: «Open an issue first»,
  «Use `XX.md` as a placeholder», «Do not self-assign the final
  number», MUST/SHOULD/MAY, esempi di richiesta e risposta. Un
  comando sconosciuto riceve `NOT_IMPLEMENTED`: un wallet vecchio non
  si rompe.
- **KaleidoSwap su Nostr** (VERIFICATO sui 42 repo dell'org, 7 ott):
  **nessun lavoro sull'identità degli emittenti**. Il loro `registry` è
  una pagina web su `api.signet.kaleidoswap.com` (lista centrale, MIT).
  Nostr lo usano in **`pivss`** (backup incentivati dello stato
  Lightning/RGB: i server si annunciano con un evento addressable
  `kind:38831`, prezzo in sats e offerta BOLT12 — stessa grammatica di
  NIP-87), nel wallet **Rate** (contatti, zap, Lightning Address, NWC
  «to pair external apps») e nella roadmap («P2P trading via Nostr»,
  non ancora vivo). **WebRGB** (`@kaleidorg/webrgb` 0.3.0 del 26 set,
  7 commit, fork `@utexo/webrgb` in `dev`): `enable()`, `getInfo()` →
  `{ready, network, protocol: "RGB_L1"|"RGB_LN", methods}`,
  `blindReceive({assetId?, amount?, minConfirmations?})` (→ `invoice`,
  minimo consigliato 3 conferme), `witnessReceive` (Utexo),
  `issueAsset`, `listAssets`, `getAssetBalance`, `sendAsset({invoice})`
  → `{txid, transferId}`, `listTransfers`, `getTransferStatus`,
  `decodeRgbInvoice`, `makeLnInvoice`/`payLnInvoice` solo se `RGB_LN`;
  errori `USER_REJECTED`, `NOT_ENABLED`, `METHOD_NOT_SUPPORTED`,
  `INVALID_PARAMS`, `ASSET_NOT_FOUND`, `INTERNAL_ERROR`; scoperta alla
  EIP-6963 (`rgb:requestProvider`/`rgb:announceProvider`). Lo
  implementa solo l'estensione browser di KaleidoSwap; **niente
  registro, niente emittente, niente NWC**; Utexo nomina un
  `@utexo/webrgb-walletconnect` per i wallet mobili (NON letto: da
  chiedere). **Conclusione**: la nostra estensione NWC ricalca WebRGB
  nei nomi e nelle forme (`assetId`, `invoice`, `txid`, `transferId`,
  gli stati), così un wallet che fa l'uno fa l'altro in un pomeriggio.
- **Il `kaleido-mind`** di KaleidoSwap («local-first reasoning and
  tool-calling engine for Bitcoin wallets», su QVAC, Qwen3 0.6B nel
  wallet Rate) parte dalla nostra stessa lezione: «small on-device
  models are slow and weak at arguments, so they are never asked to do
  the slow or weak parts» — il conto lo fa il programma. Citarlo nel
  pitch è un omaggio che costa zero.

### A.4 Il verdetto

Regge. Le tre cose che lo rendono difendibile davanti a quella giuria:
(1) il campo `issuer` del consenso, che dice che il protocollo ha
previsto il livello applicativo; (2) la forma presa da NIP-87 e NIP-73,
non inventata; (3) l'estensione NWC come «WebRGB sopra Nostr», nel repo
e col processo che esistono dal settembre 2026. Il rischio è solo di
scala: in due giorni si pubblica una **bozza**, e si dice bozza.

## B. La forma minima della bozza, da scrivere a Torino

Due testi, due repo, un'ora e mezza di scrittura la domenica mattina
con i nomi già decisi qui. I numeri dei kind e del file sono
SEGNAPOSTI: li assegnano i maintainer.

### B.1 «NIP-XX: RGB asset announcements» (repo `nostr-protocol/nips`, PR in bozza)

**L'annuncio** — evento addressable **`kind:3xxxx`** (segnaposto; NIP-87
usa 38172/38173, pivss 38831: si sceglie un numero libero in PR),
pubblicato dalla chiave dell'EMITTENTE:

```yaml
{
  "kind": 3xxxx,
  "pubkey": "<hex della chiave dell'emittente>",
  "tags": [
    ["d", "<ContractId senza prefisso, es. 9N5NpOdN-Qdy418I-xs_gEFy-Wzk1p6X-S33L673-X~lm9iM>"],
    ["i", "rgb:contract:<ContractId>"], ["k", "rgb:contract"],   // NIP-73, la riga nuova
    ["n", "signet"],                      // rete, come NIP-87: mainnet|testnet|signet|regtest
    ["schema", "nia"],                    // nia|uda|cfa|ifa|pfa
    ["ticker", "MOON"], ["name", "Punti To The Mooon"], ["precision", "0"],
    ["supply", "1000000"],                // issuedSupply, in unità minime
    ["issuer", "nostr:<hex>"],            // SOLO al livello 2: il valore del campo issuer del genesis
    ["u", "https://…/moon.rgb"],          // opzionale: dove scaricare il contract consignment
    ["alt", "Annuncio dell'asset RGB MOON"]
  ],
  "content": "<testo libero: cos'è, cosa vale, dove si spende; oppure il contract consignment in base64>"
}
```

Perché queste scelte: `d` = ContractId rende l'annuncio **uno per
contratto per chiave** (replaceable: l'emittente corregge i metadati
senza duplicati) e interrogabile con `#d`; il tag `i`/`k` di NIP-73 fa
sì che una recensione, un annuncio di Barattolo o un ordine Mostro
possano puntare all'asset con un tag standard; `n` è il nome del campo
di NIP-87; i metadati sono COPIE di quel che il wallet legge dal
genesis, e **il wallet li confronta** (ticker, name, precision, supply:
se divergono, l'annuncio è storto e non si mostra); il **contract
consignment** nel `content` o dietro `u` risolve la lezione del 1 ott
(«la prima fattura è "qualunque asset"»: il wallet che importa il
consignment dall'annuncio conosce l'asset PRIMA di riceverlo — e
docs.rgb.info stesso dice che un contract consignment «è dell'ordine di
pochi KiB» e si può codificare «come una chiave PGP o un QR»).

**La raccomandazione** — **`kind:3xxxx+1`** (il calco di NIP-87
`kind:38000`), pubblicata da chiunque:

```yaml
{
  "kind": 3xxxx+1,
  "tags": [
    ["k", "3xxxx"],
    ["d", "<ContractId>"],
    ["a", "3xxxx:<hex emittente>:<ContractId>", "wss://relay…"],   // QUALE annuncio si raccomanda
    ["i", "rgb:contract:<ContractId>"], ["k", "rgb:contract"]
  ],
  "content": "Li accetto nel mio negozio: 1 MOON = 1 sat di sconto."
}
```

È qui che nasce il web of trust: un wallet che vede due annunci per lo
stesso contratto mostra quello raccomandato da chi l'utente segue
(`{"kinds":[3xxxx+1], "authors":[<io e i miei contatti>], "#d":[<id>]}`),
e un negozio che «raccomanda» MOON dice ai suoi clienti che lo accetta.

**La verifica**, in cinque passi che il wallet (o Barattolo) fa in
quest'ordine, e si ferma al primo che fallisce:
1. La firma dell'evento è valida (NIP-01) e `d` è esattamente il
   ContractId che il wallet ha in mano (confronto sulla stringa
   normalizzata, mai sul ticker: «using tickers instead of ids was
   rejected due to security concerns», docs.rgb.info).
2. I metadati del tag combaciano col genesis (ticker, name, precision,
   supply).
3. Il kind 0 dell'autore dichiara un `nip05`.
4. Il NIP-05 risolve alla STESSA chiave: GET `https://<dominio>/.
   well-known/nostr.json?name=<nome>`, senza seguire redirect, host
   pubblico (in casa: `url_api_ammesso`), e `names[<nome>]` ==
   `pubkey` dell'evento. Senza questo passo l'annuncio è «dichiarato»,
   non «verificato».
5. (Livello 2) Il campo `issuer` del genesis è `nostr:<hex>` e `hex` ==
   `pubkey` dell'evento: allora l'identità è **impegnata**.

**Sicurezza, da scrivere nella bozza**: il NIP-05 è «identification,
not verification» (parole del NIP): il wallet mostra il DOMINIO per
intero e non lo abbrevia; segue la chiave, non l'indirizzo (se il JSON
un domani risponde un'altra chiave, l'annuncio smette di essere
verificato, non cambia emittente); i metadati dell'evento non
sostituiscono MAI quelli del genesis; l'annuncio NON autorizza
niente — non muove asset, non apre canali: è un'etichetta firmata.

### B.2 «NWC-XX: RGB Assets» (repo `nostr-wallet-connect/nwc`, issue prima, poi PR)

Sul calco di `321.md`: Summary, Motivation («WebRGB è il provider nella
stessa pagina; questa estensione porta gli stessi metodi al wallet che
sta altrove»), Dependencies (NIP-47, 02 per le notifiche, 06 per i
metadati, WebRGB SPEC v1, rgb-lib per gli stati), Discovery, Methods,
Errors.

**Discovery**: i metodi nel `content` dell'evento info e in
`get_info.methods`; `["extensions", "XX"]`; in `get_info.result` un
campo in più, `rgb: {network, protocol: "RGB_L1"|"RGB_LN"}`.

**I quattro metodi** (i nomi con prefisso `rgb_` perché il nucleo non
ha namespace e `pay`/`receive` sono già presi dalla 321; i campi coi
nomi di WebRGB):

```yaml
# rgb_list_assets — il libro degli asset del wallet
{"method":"rgb_list_assets","params":{"schema":"nia"}}            # schema opzionale
→ {"result_type":"rgb_list_assets","result":{"assets":[
     {"asset_id":"rgb:…","schema":"nia","ticker":"MOON","name":"Punti To The Mooon",
      "precision":0,"balance":{"settled":60,"future":60,"spendable":60},
      "issuer":"ssi:anonymous"}]}}                                 # issuer: il campo del genesis, se il wallet lo sa

# rgb_make_invoice — una fattura RGB per RICEVERE (blind o witness)
{"method":"rgb_make_invoice","params":{"asset_id":"rgb:…",        # opzionale: assente = «qualunque asset» (primo contatto)
   "amount":100,"witness":false,"min_confirmations":1,"expiry":3600,"metadata":{}}}
→ {"result":{"invoice":"rgb:…/…/…","recipient_id":"<utxob o indirizzo>","expires_at":1760000000,
   "witness":false,"min_confirmations":1}}

# rgb_pay_invoice — PAGARE una fattura RGB (il wallet chiede conferma all'utente)
{"method":"rgb_pay_invoice","params":{"invoice":"rgb:…","amount":5,  # amount solo se la fattura non lo porta
   "fee_rate":2,"metadata":{"ordine":"203"}}}
→ {"result":{"transfer_id":"<id del trasferimento nel wallet>","txid":"<hex>|null",
   "state":"waiting_counterparty",        # waiting_counterparty|waiting_confirmations|settled|failed (gli stati di rgb-lib)
   "asset_id":"rgb:…","amount":5,"created_at":1760000000}}

# rgb_lookup_transfer — lo stato dopo
{"method":"rgb_lookup_transfer","params":{"transfer_id":"…"}}      # oppure {"txid":"…"}
→ {"result":{"transfer_id":"…","txid":"…","state":"settled","asset_id":"rgb:…","amount":5,
   "confirmations":1,"created_at":…,"settled_at":…}}
```

**Le notifiche** (via 02, stesso payload generico):
`rgb_transfer_received` quando il consignment è validato e accettato
(lo stato è `waiting_confirmations`), `rgb_transfer_settled` al
blocco; nel tag `notifications` dell'info event. Sono gli eventi
`transferReceived`/`transferSettled` di WebRGB.

**Gli errori**: quelli del nucleo (`NOT_IMPLEMENTED`, `RESTRICTED`,
`INSUFFICIENT_BALANCE`, `INTERNAL`) più `ASSET_NOT_FOUND`,
`INVALID_INVOICE`, `UNSUPPORTED_NETWORK` (la fattura è di un'altra
rete: la 321 ha lo stesso errore), `TRANSFER_FAILED`. Da scrivere con
un MUST: **il wallet MUST chiedere conferma all'utente per
`rgb_pay_invoice`** — il «propone, tu approvi» del criterio 4 vive nel
wallet, non nell'app che chiede.

**Perché regge sul lato tecnico.** Un trasferimento RGB non è una
chiamata sincrona come `pay_invoice`: chi paga costruisce PSBT e
consignment, lo deposita sul proxy, aspetta l'ACK di chi riceve, poi
trasmette; il «pagato» arriva in tre tempi. La risposta di
`rgb_pay_invoice` quindi torna SUBITO con `transfer_id` e
`waiting_counterparty`, e Barattolo — che è chi riceve — vede il
consignment arrivare dal SUO lato (`rgb.py aggiorna barattolo`) e lo
accetta: non ha bisogno di fidarsi della risposta del wallet. La
notifica `rgb_transfer_received` è una comodità, non la prova.

### B.3 Dove si pubblica, e con quale chiave

- I due testi nel repo di Barattolo (`docs/NIP-XX-RGB-ASSETS.md`,
  `docs/NWC-XX-RGB-ASSETS.md`) nel commit datato della domenica; la
  issue nel repo `nwc` («Open an issue first») la domenica stessa; la
  PR ai NIP può aspettare la settimana dopo con l'implementazione
  pulita — la bozza pubblicata è quel che vale per il pitch.
- Gli annunci di MOON e USDB firmati dalle **due identità di prova**
  (sezione D), MAI dalla chiave della piattaforma (regola ferrea 1 e
  memoria «Nsec di prova nel config locale»). Dove: sul **relay locale
  del portatile** per tutto il weekend (la regola di casa: niente relay
  veri in collaudo); se Alan vuole che la domenica la bozza sia
  «pubblicata» anche su un relay pubblico, si pubblicano SOLO i due
  annunci dalle chiavi di prova, e lo si decide prima, non sul palco.

## C. Come si vede nella schermata del Cassiere

La schermata è il foglio del pagamento di un ordine, dentro il cassetto
giusto del conto (la forma del 25 set, «Il profilo più elegante»), con
la leva `RGB_ATTIVO` accesa e un wallet NWC che dichiara
`rgb_list_assets`. Dall'alto:

1. **Il conto** come oggi (prezzo in sats, eventuale sconto fedeltà) e
   una riga nuova: «**oppure 4,80 USDB**» col cambio dichiarato
   («1 USDB = 1 $, al cambio di oggi» dalla fonte già in casa del P2P).
2. **La card dell'asset**, la novità di Alan: icona, «**USDB · Dollari
   di prova**», il saldo del wallet («hai 500,00 USDB»), e la riga
   dell'emittente in una delle quattro forme — e si scrive sempre il
   dominio intero:
   - `✓✓ Emesso da Dollari di prova (usdb@<dominio>) · identità impegnata nel contratto` (livello 2)
   - `✓ Emesso da To The Mooon (tothemooon@<dominio>)` (livello 1 con NIP-05 verificato)
   - `Dichiarato da <npub abbreviato> · identità non verificata` (firma valida, niente NIP-05 o NIP-05 che non torna)
   - `⚠️ Emittente sconosciuto` (nessun annuncio): l'asset si può
     spendere lo stesso — non è Barattolo a decidere cosa vale — ma la
     riga resta grigia e il Cassiere non lo propone da solo.
   Un tocco sulla riga apre il dettaglio: il ContractId intero
   copiabile, la rete, ticker/name/precision/supply letti dal genesis,
   «confronto con l'annuncio: combacia», il link all'evento (`nevent`),
   la data dell'annuncio, e per il livello 2 la frase «il genesis di
   questo contratto porta `issuer = nostr:…`, la stessa chiave che ha
   firmato l'annuncio».
3. **La proposta del Cassiere**, in un fumetto: «Paga 4,80 USDB e usa
   40 MOON (40 sats di sconto): ti restano 495,20 USDB e 20 MOON.
   Motivo: …» — il JSON di QVAC reso in una frase, con «**Approva**» e
   «No, pago in sats». La regola («max 20% del prezzo in punti», il
   tetto del budget) la mostra sotto in piccolo: il modello ha scelto
   dentro quella, non l'ha inventata.
4. **Approva** → `rgb_pay_invoice` al wallet; il wallet WDK chiede la
   sua conferma (sul portatile, nella finestra del servizio NWC: è lì
   che «l'utente firma»); torna `waiting_counterparty`; Barattolo
   accetta il consignment e il foglio passa a «**Pagamento in arrivo ·
   in attesa del blocco**» con il link a mempool.space/signet; al
   blocco, «Pagato in USDB ✓». Il lessico: nessun «deposito di
   garanzia» su questo pagamento — è diretto — e il foglio lo dice in
   una riga («pagamento diretto, senza deposito di garanzia: l'ordine
   si chiude subito»), perché la regola 9 vieta di far credere il
   contrario.
5. **Il bonus MOON** sotto, dopo il pagamento: «+5 MOON da To The
   Mooon in arrivo» (l'assegnazione del 1 ott, un punto per euro).
6. **Il salvadanaio e il budget**, se si fanno: «Arrotonda a 5 USDB e
   metti 0,20 nel salvadanaio» come seconda proposta del Cassiere, e
   «Budget del mese: 42,30 di 60 USDB» come riga grigia — il budget
   vive SOLO nel browser (localStorage, o `DeviceStorage` di Telegram)
   e viaggia verso QVAC, mai verso il server: è il «privato» del filone
   03.

Gli stati dell'ordine (regola ferrea 4) non cambiano: il pagamento in
USDB segna il metodo e porta l'ordine allo stato che oggi significa
«chiuso, sats consegnati» — quale sia esattamente (dopo l'ACK o dopo il
blocco) è una **DECISIONE da prendere il sabato**, scritta nel commit,
e si dichiara.

## D. Il piano aggiornato, e cosa si prepara prima (dichiarato)

Il regolamento non è cambiato: «we only judge what you build during the
hackathon. Declare what already exists when you arrive, keep the
weekend's work in dated commits, and do the RGB and QVAC integration on
site». Tre cose dalla pagina, rilette il 7 ott: la **scadenza era il 5
ottobre alle 12:00** (chi si è iscritto è iscritto; conferme «by
Thursday, October 8»); i **quattro filoni** sono «01 Payments and
checkout», «02 Self-custodial digital dollar apps», «03 Private
financial intelligence — On-device budgeting and fraud alerts», «04
Autonomous economic agents — Local AI that proposes, you approve» (il
Cassiere li tocca tutti e quattro, e lo si dice); **la pagina non nomina
nessun Q&A né il 13 ottobre** — la data viene da Andrea (la mail di
conferma): si verifica su quella.

### D.1 Prima del 17: infrastruttura, dichiarata

| Quando | Cosa | STIMA | Note |
|---|---|---|---|
| 8-9 ott | **Emettere USDB** sulla VM: wallet nuovo `usdb` (l'emittente dei dollari è un soggetto diverso dal mercante Barattolo e dal negozio), faucet, 5 UTXO, `emetti usdb USDB "Dollari di prova Barattolo" 100000000` con **precision 2** (docs.rgb.info: «2 for USD»; `rgb.py` oggi emette a precisione 0: un argomento in più), backup | 1-2 h | la ricetta è in HACKATHON-SETUP §2; «USDB» passa il ticker ([A-Z0-9]{1,8}) |
| 8-9 ott | **500 USDB al wallet utente** (fattura «qualunque asset» per il primo contatto, come per MOON) e **UTXO colorabili al wallet `barattolo`**, che a Torino sarà chi RICEVE i pagamenti | 1 h, due blocchi | tx fatte e confermate prima: non sono la demo |
| 9-10 ott | **Due identità Nostr di prova**: due coppie di chiavi nuove (nostr-tools o `nak key generate`), kind 0 con `name`, `about` e `nip05` (`usdb@…` e `tothemooon@…`), le private in `~/wdk-prova/identita/` a 600 e nell'archivio age — MAI nel repo, MAI la chiave della piattaforma | 1 h | **DA DECIDERE il dominio del NIP-05**: (a) `barattolo.store/.well-known/nostr.json` come rotta ESPLICITA (regola 3, sul calco di `assetlinks.json`) nel commit dell'11-12 ott: due nomi, un file statico, zero rischio, e la riga «Emesso da To The Mooon (tothemooon@barattolo.store)» legge benissimo; (b) GitHub Pages con `.nojekyll` (serve `.well-known` e manda `Access-Control-Allow-Origin: *`): zero produzione, ma «github.io» nella schermata. Raccomando (a), con la nota che il VERO To The Mooon avrebbe il suo dominio |
| 9-10 ott | **Relay locale** strfry in docker sul portatile (`ws://127.0.0.1:7777`): per NWC e per gli annunci | 1 h | in collaudo la CSP ammette `ws:` |
| 11-12 ott | **`nwc-wdk.mjs`, la BASE**: apre il wallet WDK (`punti.mjs`), pubblica l'evento info (13194) con `encryption` nip44, risponde a `get_info` e `get_balance`; stampa la connection string da incollare nel Profilo. **I metodi `rgb_*` NO**: si scrivono a Torino (sono l'integrazione, e sono «Execution») | 4-6 h | `@getalby/sdk` `NWCWalletService` fa il grosso; se il tipo non accetta nomi fuori lista, l'evento 23194 si gestisce a mano con nostr-tools (30 righe) |
| 11-12 ott | **`rgb_http.py` sulla VM**, loopback, dal tunnel (`-L 8787`): `fattura`, `aggiorna`, `saldo`, `lista` del wallet `barattolo` dietro HTTP, così il server di Barattolo sul portatile non fa `ssh` da dentro una rotta | 2 h | è `rgb.py` con una faccia HTTP; il tunnel resta l'unica porta |
| 11-12 ott | **Il commit su main** (uno): `RGB_ATTIVO = False` e `RGB_PROVA_IDS` in `config_esempio.py`, la riga nel pannello «Stato delle leve», la prova che a leva spenta non risponde nulla; e, se (a), la rotta `/.well-known/nostr.json` | 2 h + prove | niente rotte RGB, niente UI |
| 11-12 ott | **QVAC**: `npm i -g @qvac/cli@latest` (la CLI è alla 0.15, l'SDK alla 0.21: installata la 0.14), `qvac.config.json` con l'alias `cassiere` → `QWEN3_1_7B_INST_Q4`, `ctx_size 8192`; scaricare (~1 GB); una **pagina locale di prova** FUORI dal repo che chiama `http://127.0.0.1:11434/v1/chat/completions` con `response_format: json_schema` e `reasoning_budget: false` (Qwen3 pensa, e con `max_tokens` stretto lascia `content` vuoto: documentato); il server lanciato con `--cors-origin http://127.0.0.1:8080` ESATTO (niente `*`, e `--cors` da solo non accende niente: documentato) | 2-3 h | structured output e `tools` NON si combinano (400): il Cassiere usa lo schema e il conto già fatto, senza tool |
| 13 ott | **Q&A** (sezione E) | 1-2 h | con le risposte scritte accanto |
| 14-16 ott | La **dichiarazione** scritta (HACKATHON-SETUP §5 aggiornata), gli schermi del Cassiere su carta, il flusso provato tre volte con la pagina di prova e il wallet; backup della VM; portatile con tutto scaricato | 3-4 h | |

Cosa NON si fa prima: le rotte `/api/rgb/*` e `/api/cassiere/*`, il
bottone «Paga in USDB», la card dell'asset, la chiamata a QVAC dalla
pagina di Barattolo, i metodi `rgb_*` nel servizio NWC, la verifica
NIP-05 in Barattolo, i due testi del NIP. Si DISEGNANO (questo file è
il disegno).

### D.2 I due giorni

| Ora | Cosa | Chi | Note |
|---|---|---|---|
| sab 09:00-09:45 | Kickoff; la dichiarazione consegnata; il tavolo: VM su, tunnel su, relay locale su, QVAC su, server in collaudo su `127.0.0.1:8080` col db 111/222/999 | tutti e due | niente codice prima della dichiarazione |
| sab 09:45-13:00 | **Wallet**: i quattro metodi `rgb_*` in `nwc-wdk.mjs` sopra `punti.mjs` (lista, fattura, paga con conferma a terminale, lookup), provati con un client NWC a riga di comando. **Server** in parallelo: `/api/rgb/fattura` (chiede a `rgb_http.py` la fattura blind di `barattolo` in USDB per l'ordine, importo al cambio), `/api/rgb/stato`, tutto dietro `RGB_ATTIVO` | Alan il wallet, Claude+Andrea il server | commit datati, uno per funzione |
| sab 13:45-16:30 | **Client**: nel foglio del pagamento la riga «oppure N USDB» e il bottone «Paga in USDB» → fattura → `rgb_pay_invoice` via `clientNwc` → stato «in arrivo» → `rgb.py aggiorna` lato server → «Pagato» | | **primo pagamento VERO in USDB su signet entro le 16:30**: è il core, da qui in poi tutto è aggiunta |
| sab 16:30-19:30 | **Il Cassiere**: la pagina chiama QVAC (schema `{paga_in_usdb, usdb, usa_punti, punti, sconto_sats, motivo}` col conto già fatto), il fumetto, «Approva» che fa il passo di prima da solo | | se CORS o mixed content mordono: la chiamata la fa il server (`/api/cassiere/proposta` → 127.0.0.1:11434) e si dichiara |
| sab sera | **MOON come bonus** dopo il pagamento (l'assegnazione del 1 ott agganciata al «Pagato»); la card dell'asset con ticker/saldo (senza emittente); il giro intero due volte | | |
| dom 09:00-11:00 | **Il NIP**: i due annunci (MOON e USDB) firmati dalle identità di prova e pubblicati sul relay locale; in Barattolo la lettura dell'annuncio per `#d`, la verifica NIP-05 (lato server con `url_api_ammesso`, senza redirect) e la riga «Emesso da … ✓» nella card; i due testi `docs/NIP-XX…` e `docs/NWC-XX…` dal disegno di B | Alan la pubblicazione e i testi, Claude+Andrea la verifica | la issue nel repo `nwc` aperta a mezzogiorno |
| dom 11:00-13:00 | **Se avanza**: il salvadanaio (seconda proposta del Cassiere, arrotondamento) e il budget nel browser; sennò: gestione degli errori visibile («wallet non collegato», «proxy irraggiungibile», «conferma in arrivo») — «UX: error handling» è un criterio | | |
| dom 13:00-14:30 | Le tx del pitch fatte e confermate; le slide (sotto); prova a tempo | | niente codice dopo le 14:00 |
| dom 15:00 / 16:00 | Consegna / pitch | | portatile, VM in riserva, hotspot |

**Le slide (7)**: 1) chi siamo, 30 secondi (sotto); 2) venerdì sera —
la dichiarazione; 3) il Cassiere dal vivo (il video di riserva già
registrato); 4) le tx su mempool.space/signet; 5) il NIP: i due
livelli, il campo `issuer`, «WebRGB sopra NWC»; 6) la roadmap: Mostro
con asset RGB, consegne via relay Nostr al posto del proxy, i
certificati UDA per le magliette numerate di AGORA — per un grant
dell'RGB Protocol Association (**l'esistenza di un programma di grant
NON l'ho verificata**: da chiedere il 13); 7) cosa resta.

**I 30 secondi**, con la precisione di cui sopra: «Barattolo è un
mercatino italiano in satoshi, in produzione dal 10 ottobre: si entra
col P2P comprando sats con euro su Mostro, si compra e si vende con un
deposito di garanzia Lightning, si esce col P2P. Un'economia circolare
fra persone, su protocolli aperti — Nostr, Lightning, Mostro, e da
questo weekend RGB — dove nel P2P e nel suo wallet l'utente è padrone
dei suoi sats. Oggi vi mostriamo il Cassiere: si paga in dollari su
Bitcoin, un'AI che gira su questo portatile propone, l'utente approva,
e il wallet sa chi ha emesso quei dollari.»

**La roadmap, con una riga di realtà ciascuna** (per non promettere
cose che il protocollo non fa): Mostro non ha nozione di asset
(VERIFICATO il 1 ott), e un ordine «vendo USDB per euro» vorrebbe un
campo in più nel NIP-69 — una proposta, non un cantiere; le consegne
via relay Nostr sono nel futuro scritto da docs.rgb.info stesso
(«easily adaptable to censorship-resistant transmission media such as
Nostr, through the use of relay servers»), ma un transfer consignment
cresce con la storia e i relay tagliano gli eventi grossi: la forma
realistica è **il consignment su Blossom (che Barattolo usa già per le
foto delle recensioni) e un puntatore firmato sul relay**; i certificati
sono lo schema UDA (esiste: `EmbeddedMedia`, `Attachments`,
`ProofOfReserves`) — uno per maglietta, con la foto e il numero.

### D.3 Rischi nuovi, in ordine

1. **Il wallet chiede conferma a terminale** e il pubblico non la vede
   → la finestra del servizio NWC proiettata accanto alla pagina, o un
   `--approva-tutto` SOLO per il pitch e dichiarato.
2. **`@getalby/sdk` non accetta metodi fuori lista** → 23194 a mano
   (30 righe), deciso al mattino del sabato entro un'ora.
3. **Il NIP-05 non risolve dal portatile** (DNS, hotspot) → la verifica
   ha una cache di 24 h fatta il venerdì, e la riga dice «verificato il
   16 ott».
4. **Due annunci per lo stesso contratto** nella demo (un errore nostro)
   → il wallet mostra entrambi: è la feature, non il bug — ma si evita.
5. **La precisione 2 di USDB** nei conti (4,80 = 480 unità): un `//
   100` sbagliato è il bug più probabile del sabato → una prova sola,
   scritta prima della rotta.
6. I sei rischi della prima parte restano (proxy, bundling, mixed
   content, blocchi lenti, seed su due processi, portatile).

## E. Le domande per il Q&A del 13

Scritte, con lo spazio per la risposta accanto. Le prime cinque sono
nuove, le altre restano dalla prima parte (E.3) e da HACKATHON-SETUP §8.

1. **Il campo `issuer` del genesis**: è nei vostri piani esporlo in
   rgb-lib (`issue_asset_*` e `list_assets`)? Un wallet come Iris lo
   mostra? Se noi emettiamo con `issuer = nostr:<pubkey>` dalla CLI
   `rgb`, i wallet rgb-lib accettano il consignment senza problemi?
2. **WebRGB sopra NWC**: la nostra estensione NIP-47 ricalca i nomi e
   le forme di WebRGB (`blindReceive`, `sendAsset`,
   `getTransferStatus`, `transferReceived`): vi va bene, e cos'è
   `@utexo/webrgb-walletconnect`? Rate potrebbe essere il wallet
   dell'utente in una demo così (RLN, signet, NWC)?
3. **Il checkout in un asset RGB on-chain** (pagamento diretto, tre
   tempi, 1 conferma) conta per il filone «Payments and checkout», o
   per voi «checkout» vuol dire Lightning RGB?
4. **USDB**: un dollaro di prova emesso da noi va bene, o Tether/Utexo
   porteranno un USDT di prova su signet per l'evento (contract id,
   faucet)?
5. **La bozza di NIP**: la giudicate come lavoro del weekend se il
   disegno (campi e nomi) esiste già nel nostro repo dal 7 ottobre e il
   testo e l'implementazione si fanno in sede? E il servizio NWC «base»
   fatto prima (senza i metodi `rgb_*`): infrastruttura dichiarabile o
   integrazione?
6. La rete: signet con explorer pubblico vale «working transactions»?
   `min_confirmations = 0` per il palco?
7. «On device» per il criterio 2 con l'inferenza in `qvac serve` sul
   portatile e la UI nella pagina; e il consiglio fra Qwen3 1.7B e
   Llama 3.2 1B per JSON a schema.
8. Il bonus WDK: il wallet WDK (`@utexo/wdk-wallet-rgb`) che gira in
   Node sul portatile e parla NWC è «centrale»? La pagina della docs
   elenca `mainnet|testnet|regtest` per quel modulo e noi lo usiamo su
   signet senza errori: è supportato?
9. Gli endpoint pubblici Utexo il 17-18; la fattura «qualunque asset»
   per il primo contatto (o un contract consignment nell'annuncio
   Nostr, come proponiamo); beta.7/beta.8 insieme.
10. Consegna: repo pubblico, licenza, durata del pitch, se guardano i
    commit. CypherTank: finali o semifinali.
11. **Il grant dell'RGB Protocol Association**: esiste un programma?
    Per cosa, con che tempi? (NON VERIFICATO da qui.)

## Fonti della parte seconda

Lette il 7 ott 2026.

- **La gara**: https://rgbprotocol.org/agentic-dollars-hackathon/
  (riletta per intero: scadenza 5 ott 12:00, conferme entro l'8, i
  quattro filoni e i cinque criteri testuali, nessun Q&A nominato).
- **NIP**: https://github.com/nostr-protocol/nips/blob/master/47.md
  (il nucleo ridotto, tag `extensions`), …/05.md (`final`, i due versi,
  niente redirect), …/87.md (38172/38173/38000), …/73.md (`i`/`k`,
  `bitcoin:tx:`), …/89.md, …/39.md; la ricerca issue/PR del repo con
  «RGB», «asset», «token», «stablecoin» (zero risultati sul tema; PR
  #1658 è un feed di prezzi).
- **Estensioni NWC**: https://github.com/nostr-wallet-connect/nwc
  (README con la tabella 02-321, CONTRIBUTING, `02.md`, `321.md`).
- **RGB**: https://github.com/rgb-protocol/rgb-consensus
  (`src/operation/operations.rs`: `Identity`, `Genesis.issuer`),
  https://github.com/rgb-protocol/rgb-ops (`src/info.rs`),
  https://github.com/rgb-protocol/rgb-api (`cli/src/command.rs`: `rgb
  issue <issuer>`), https://github.com/rgb-protocol/rgb-schemas
  (`src/nia.rs`), https://github.com/RGB-Tools/rgb-lib
  (`src/wallet/offline.rs`: `Identity::default()` quattro volte);
  https://docs.rgb.info/ (indice, schema NIA, invoices, contract
  transfers, glossario: «Contract issuer: an actor creating contract
  Genesis», il consignment «di pochi KiB», Nostr «in the future»).
- **KaleidoSwap**: l'elenco dei repo dell'org (42, via API GitHub);
  https://github.com/kaleidoswap/webrgb (README, SPEC.md, CHANGELOG) e
  https://github.com/UTEXO-Protocol/webrgb (fork, INTEGRATION.md);
  https://github.com/kaleidoswap/registry ; https://github.com/kaleidoswap/Rate ;
  https://github.com/kaleidoswap/kaleido-mind ;
  https://github.com/kaleidoswap/pivss (kind 38831).
- **QVAC**: https://docs.qvac.tether.io/quickstart/ , …/cli/ ,
  …/cli/http-server/ (`--cors-origin` esatto, `--cors` da solo non
  basta, `response_format` json_schema, «cannot be combined with
  tools», `reasoning_budget: false`, `QWEN3_1_7B_INST_Q4`), …/sdk/ ,
  …/sdk/reference/release-notes/ (0.21.0).
- **WDK**: https://docs.wdk.tether.io/ , …/sdk/wallet-modules/ ,
  …/sdk/community-modules/wdk-wallet-rgb/ (`mainnet|testnet|regtest`),
  …/overview/changelog/ ; nessuna parola su Nostr o NWC.
- **In casa**: `miniapp.html` (`clientNwc`, `metodiNwc`, `infoNwc`,
  `leggiEventoInfo`), `server.py` (`url_api_ammesso`,
  `_url_lnurl_ammesso`, `CSP_PROVA` con `connect-src 'self' wss:` più
  `ws:` in collaudo, `XP_PER_EURO`, `_fedelta_sconto`,
  `consigliati_pubblici`, la rotta `/.well-known/assetlinks.json`),
  `config_esempio.py` (`P2P_ATTIVO`, `P2P_PROVA_IDS`),
  `docs/HACKATHON-SETUP.md` (lo stato del 1 ott), `CLAUDE.md` (regole
  ferree 1, 2, 3, 4, 9; «escrow Lightning custodial (LNbits)»).
