# Studio: «Paga con Bolt Card» (24 settembre 2026)

Sola lettura, nessuna modifica al codice, nessun cantiere aperto. Base:
`main` a `a20fc2d` (i nomi di funzione qui sotto sono di quel commit). Il
VPS, il nodo e il relay non sono stati toccati. Fatti di rete verificati
sulle fonti in fondo; quel che NON ho potuto verificare da qui è scritto
come tale, con la prova da fare accanto.

**La domanda:** si può mettere sul foglio di pagamento di un ordine un
bottone «Paga con Bolt Card», che legge la carta col telefono e fa pagare
la fattura dell'ordine alla carta? E il caso di persona, dove chi vende
incassa avvicinando la carta di chi compra?

**La risposta corta.** Il pezzo di server è piccolo e sta tutto in una
rotta: la Bolt Card è LNURL-withdraw, cioè lo stesso mestiere che
`invoice_da_ln_address` fa già al contrario. Il pezzo che decide è il
**telefono**: la lettura NFC dalla pagina funziona SOLO in Chrome per
Android (e quindi, per costruzione, nell'APK, che è Chrome), NON dentro
Telegram — né su Android, dove la Mini App vive nel WebView, né su iPhone,
dove nessun browser ha l'NFC. Quindi «Paga con Bolt Card» dentro Telegram
non esiste come bottone che legge: esiste come bottone che APRE Chrome su
una pagina nostra. E il caso di persona non è un secondo cantiere ma la
stessa rotta con un altro dito: il venditore col telefono Android legge la
carta del compratore, ed è l'unica strada per chi compra con un iPhone.
**Raccomandazione: farlo, piccolo, in quest'ordine — prima la prova di
cinque minuti sul telefono di Andrea (l'APK legge una carta?), poi la rotta
del server con la guardia SSRF, poi il bottone nell'APK, e Telegram che
apre Chrome. Il caso di persona subito dopo, perché è a costo zero sul
server.** Peso stimato: un cantiere di una-due giornate, con la prova sul
telefono come tappa critica.

## Come leggere questo file

- I quattro pezzi (la carta, la lettura, il server, il caso di persona)
  hanno ognuno: se funziona, cosa serve, i rischi, quanto lavoro.
- «VERIFICATO» = letto su una fonte primaria (spec, documentazione
  Chrome). «PER COSTRUZIONE» = segue da come è fatta la cosa, ma non l'ho
  visto girare. «DA PROVARE» = la prova che chiude la domanda, e dove.

## 0. Cos'è una Bolt Card, in cinque righe

Una carta NFC (chip NXP NTAG424 DNA) che a ogni tocco emette un URL
diverso. Il chip ha la funzione SUN (Secure Unique NFC message): l'URL
scritto sulla carta porta due parametri, `p` (UID e contatore, cifrati AES)
e `c` (un CMAC che li autentica), e il contatore sale a ogni lettura. Il
formato — VERIFICATO sulla spec boltcard — è

    lnurlw://card.dominio.tld?p=<32 hex>&c=<16 hex>

con lo schema `lnurlw://` di LUD-17 (si legge: «questo è un LNURL-withdraw
in chiaro, sostituisci lo schema con https»). Il servizio della carta
(«bolt card service») decifra, verifica il CMAC e **accetta solo un
contatore più alto dell'ultimo visto**: quindi ogni URL letto vale UNA
volta. Sopra ci mette le sue regole: carta abilitata, limite per pagamento,
limite giornaliero, eventuale lista di esercenti.

La **Swiss Bitcoin Pay Card** è una carta di questo standard (loro la
chiamano «Lightning-NFC standard», LNURLw), custodial presso di loro, senza
registrazione, con un pannello su `card.swiss-bitcoin-pay.ch` dove si
ricarica on-chain o Lightning. Idem la Bolt Card di CoinCorner, le carte
emesse dall'estensione `boltcards` di LNbits, LaWallet. Per un esercente
sono tutte uguali: un URL da leggere e un LNURL-withdraw da servire.

**Il flusso di un punto cassa, che è quello che Barattolo farebbe:**

1. Legge l'NDEF della carta → l'URL `lnurlw://…?p=…&c=…`.
2. `GET https://card.dominio.tld/…?p=…&c=…` → JSON LUD-03:
   `{"tag":"withdrawRequest","callback":…,"k1":…,"minWithdrawable":…,
   "maxWithdrawable":…,"defaultDescription":…}` (i due limiti in msat),
   più campi opzionali: `payLink` (LUD-19, un LNURL-pay per RICARICARE la
   carta), `balanceCheck` (LUD-14), e la proposta `pinLimit` della spec
   boltcard (sopra quella cifra il callback vuole un `pin`).
3. `GET <callback>?k1=<k1>&pr=<bolt11 della fattura>` →
   `{"status":"OK"}` oppure `{"status":"ERROR","reason":"…"}`.
4. Il servizio della carta paga la fattura **per conto suo e in
   asincrono** (LUD-03 lo dice esplicitamente): «OK» vuol dire «ci
   provo», non «pagato». Chi ha emesso la fattura lo scopre come sempre —
   da noi, col poll di `invoice_pagata`.

Il punto 4 è la chiave di tutto lo studio: **il nostro server non paga
niente e non tocca chiavi**. Presenta una fattura che esiste già e aspetta
il pagamento come oggi. Cambia solo CHI paga: non un wallet inquadrando il
QR, ma un servizio a cui abbiamo passato la fattura.

## 1. La lettura NFC dalla pagina (Web NFC): dove funziona davvero

L'API è `NDEFReader` (Web NFC). Regole, VERIFICATE sulla documentazione
Chrome: solo HTTPS, solo frame di primo livello, solo dopo un gesto
dell'utente, con un permesso «nfc» che Chrome chiede al primo uso, e **la
pagina deve essere visibile** — schermo acceso, scheda in primo piano —
altrimenti la lettura è sospesa. Il record URL arriva con
`recordType: "url"` e il testo si decodifica con `TextDecoder`. Si ferma
con un `AbortController` (che chiuderemmo con il foglio). La presenza di
`NDEFReader` dice che il browser SA leggere, non che il telefono ha
l'antenna: la prova dell'hardware è il tocco.

| Dove | Legge la carta? | Perché |
|---|---|---|
| Chrome per Android (≥ 89, Android 6+, telefono con NFC) | **SÌ** — VERIFICATO | è l'unico motore che ha spedito Web NFC |
| L'APK di Barattolo (TWA da Zapstore, oggi Chrome 153) | **SÌ, PER COSTRUZIONE** — DA PROVARE | una TWA è una scheda di Chrome: la pagina gira nel processo di Chrome, con il suo motore e il suo permesso NFC di manifest. Non un WebView. È la prova da fare per prima |
| Altri browser Chromium su Android (Samsung Internet, Brave…) | probabile, NON verificato | stesso motore, ma ognuno decide cosa espone |
| Telegram su Android (la Mini App) | **NO** — VERIFICATO | la Mini App vive nel WebView di sistema, e il WebView non ha Web NFC: `NDEFReader` è `undefined`. Nessuna leva nostra lo cambia |
| Telegram su iPhone, Safari, Chrome su iOS | **NO** — VERIFICATO | tutti i browser iOS sono WebKit, e Apple dà l'NFC solo alle app native (Core NFC). Nessun ripiego web |
| Telegram Desktop, Telegram Web | NO | un PC senza antenna |
| Firefox Android | NO | non ha spedito Web NFC |

Due conseguenze pratiche, che valgono più della tabella.

**Dentro Telegram il bottone non legge: apre.** La Mini App ha `openLink`,
che apre un URL nel browser esterno senza chiudere la Mini App. Quindi
«Paga con Bolt Card» dentro Telegram diventa: apri
`https://barattolo.store/…` in Chrome, su una pagina nostra che sa di
quale ordine si tratta ed è autenticata. L'autenticazione fuori da
Telegram **esiste già**: il cookie `barattolo_sessione` (Login Widget o
firma Nostr, `apri_sessione`). Ma chi apre da Telegram in Chrome
probabilmente NON ha quella sessione, quindi la via più liscia è un
**token usa-e-getta dell'ordine** nell'URL — esadecimale, legato
all'ordine, buono per pochi minuti (quanto la fattura), che autorizza SOLO
questo gesto: leggere una carta e presentare QUELLA fattura. Non apre
niente altro, non vale come sessione. Su iPhone `openLink` apre Safari e
lì la pagina dirà, onestamente, «su iPhone la carta non si legge dal
browser: chiedi a chi vende di leggerla col suo telefono» — che è il
pezzo 3.

**Il telefono, non la pagina, decide chi prende il tocco.** Quando una
pagina Chrome in primo piano ha una `scan()` attiva, è Chrome a ricevere il
tag. Senza pagina in ascolto, Android smista l'URL `lnurlw://` all'app che
lo ha registrato (un wallet, se c'è) o non fa niente. Quindi il foglio deve
mettersi in ascolto PRIMA di dire «avvicina la carta», e smettere quando si
chiude.

**Cosa serve nel client** (~80 righe in `miniapp.html`, più il banco):
il bottone sul `paySheet` — accanto a «✓ Ho pagato», nascosto se
`'NDEFReader' in window` è falso e in VETRINA/DEMO — che al tocco chiama
`scan()`, mostra «📶 Avvicina la carta al telefono», legge il primo record
`url`, lo manda al server con una POST, mostra lo stato che torna
(«letta, sto chiedendo il pagamento» / il motivo di un rifiuto), e lascia
al poll di `verificaOrdine` (già ogni 4 secondi) il passaggio a `locked`:
**non si aggiunge un secondo modo di dichiarare il pagamento**, è la
stessa lezione del «Compra subito» NWC — decreta il successo il poll su
LNbits, mai chi ha pagato. L'`AbortController` si chiude in
`annullaPagamento` e a `locked`. Il testo del motivo si scrive col
`textContent`, mai innerHTML (viene da un server altrui, passato dal
nostro). Nel banco node, `NDEFReader` è finto: si prova il bottone che
compare, la scan che parte al tocco, l'URL che arriva alla POST, l'abort.

## 2. Il server presenta la fattura al link

**Funziona: sì, e somiglia a codice che c'è già.** `invoice_da_ln_address`
fa due GET su un dominio altrui e rilegge la risposta; qui sono le stesse
due GET nel verso opposto, senza nemmeno il controllo sull'importo della
fattura, perché la fattura è la nostra.

**La rotta.** `POST /api/orders/{id}/bolt-card` con body `{"link": …}`.
Nell'ordine:

1. **L'ordine è mio e sta in `creato`**, con lo stesso 400 uniforme di
   `verifica_pagamento` (l'anti-enumerazione dell'audit di agosto: chi
   chiama 1, 2, 3… non impara niente). Nel pezzo 3 il «mio» si allarga al
   venditore, con la condizione scritta lì.
2. **La fattura ha ancora vita**: `vita_fattura(o["invoice"])` sopra un
   margine (60 secondi). Sotto: 409 «la fattura sta per scadere, riapri
   l'ordine». Il servizio della carta paga subito, ma paga una bolt11 con
   una scadenza sua, e presentargli una fattura che muore fra tre secondi
   è chiedergli di fallire.
3. **Il link si normalizza e si GIUDICA**: `lnurlw://` → `https://`
   (LUD-17); accettare anche il bech32 `LNURL1…` (LUD-01) costa poco e
   copre le carte scritte così. Poi la guardia, che è la parte nuova
   davvero (vedi i rischi): solo `https`, host risolto e rifiutato se
   privato, loopback, link-local, il nostro stesso dominio, l'onion o la
   rete del ponte WireGuard; nessun redirect seguito; risposta a tetto di
   pochi KB e solo JSON.
4. **Prima GET** con `httpx` e un timeout scritto (15 s, come i quattro
   tubi verso LNbits): `tag == "withdrawRequest"`, e
   `minWithdrawable ≤ sats×1000 ≤ maxWithdrawable`. Fuori: 400 con un
   motivo gentile e senza numeri altrui («questa carta non consente un
   pagamento di questo importo»).
5. **Seconda GET** al `callback` con `k1` e `pr`. `OK` → si timbra
   sull'ordine `bolt_card_presentata = adesso` (una colonna, o una voce
   nel diario che `_timbra_pagamento` già tiene) e si risponde
   `{"stato": "presentata"}`. `ERROR` → si risponde il `reason` tagliato a
   una lunghezza fissa e ripulito, mai loggato per intero.
6. **Poi niente.** Il poll del client chiama `verifica_pagamento` →
   `invoice_pagata` → `_incassa_ordine`, byte per byte come oggi: il CAS
   `creato → locked` resta l'unico giudice, e le notifiche, lo stock, le
   offerte, la ricevuta partono da lì.

Non passa da LNbits: l'endpoint `lnurlscan` di LNbits saprebbe decodificare
il link, ma la fattura da presentare è QUELLA dell'ordine, e le due GET le
sappiamo già fare. Meno tubi, meno cose che tacciono.

**I rischi, uno per uno.**

- **Pagamento doppio: no, per costruzione — ma si dichiara.** La fattura
  è una bolt11 con un `payment_hash`: Lightning non salda due volte lo
  stesso hash, e il nostro LND rifiuta un secondo HTLC su una fattura già
  saldata. Lo stesso link non si può presentare due volte (contatore e
  `k1` usa-e-getta). Due tocchi di fila sullo stesso ordine sono due link
  diversi verso la STESSA fattura: il secondo fallisce presso il servizio
  della carta («già pagata») o, se il primo è ancora in volo, ne salda
  uno solo e l'altro torna al mittente — nessun sat perso, ma un errore
  brutto da leggere. Cura gentile: il server rifiuta una seconda
  presentazione entro 30 secondi da un «OK» senza pagamento arrivato
  (il timbro del punto 5), e il client dopo «letta» smette di ascoltare.
  Dal nostro lato il CAS di `_incassa_ordine` è già a prova di chiamate
  accavallate (è nato per il poll e il bottone insieme).
- **Fattura scaduta.** `INVOICE_EXPIRY` è 900 secondi e l'ordine si
  autodistrugge poco dopo: se scade fra il nostro controllo e il loro
  pagamento, il pagamento fallisce presso di loro, nessun sat si muove,
  l'ordine muore da solo e chi compra riparte — ed è già il caso in cui
  paga col wallet all'ultimo secondo. La «ripresa» (stessa fattura viva
  riaperta) vale identica. **Un pagamento che arriva dopo la
  distruzione dell'ordine** è il caso di `controlla_annullati`, che
  riacciuffa e incassa: c'è già.
- **La sicurezza del link usa-e-getta, letta dal verso giusto.** Il
  `p`/`c` letto dalla carta è un **titolo al portatore**: chiunque lo
  tenga può farsi pagare UNA fattura a sua scelta fino al limite per
  pagamento della carta, finché la carta non viene toccata di nuovo (il
  contatore sale e il vecchio link muore). Non scade a tempo. Quindi: il
  link viaggia in HTTPS nel BODY di una POST (mai in querystring: mai in
  un log di Caddy né in una history), il server lo usa entro pochi
  secondi e **non lo scrive da nessuna parte** — non in `print`, non nel
  database, non nel diario — e il `reason` di un errore non lo ricopia.
  E va detto per intero: **la fiducia del compratore va nel nostro server
  esattamente come in qualunque cassa** — un Barattolo malevolo potrebbe
  presentare una fattura più grossa, fino al limite della carta. La
  difesa del compratore sono i limiti che ha messo sulla SUA carta, non
  noi; noi possiamo solo garantire di presentare la fattura dell'ordine
  che ha aperto lui, con la cifra che ha visto. Il servizio della carta,
  per parte sua, non ci fida di niente: se l'importo supera i suoi
  limiti risponde ERROR e basta.
- **SSRF, ed è il rischio NUOVO.** Il server fa due GET su un URL che
  arriva dal client. `invoice_da_ln_address` ha la stessa forma, ma il
  dominio lì è quello del Lightning address che il venditore ha salvato
  nel profilo; qui è quello che il client manda ADESSO. Dal VPS sono
  raggiungibili cose che da fuori non lo sono: `127.0.0.1:8080`
  (uvicorn stesso), l'LNbits self-hosted, e **dal 21 settembre il ponte
  WireGuard verso il nodo**, cioè la REST di LND. Un link
  `https://10.x.x.x/…` costruito a mano farebbe fare al server una GET
  lì dentro, con la risposta che finisce nel `reason` mostrato al
  client. La guardia del punto 3 non è un rifinimento: senza, la rotta
  non si scrive. E si prova in `prove.py` con gli indirizzi cattivi
  elencati per nome (loopback, 10/8, 172.16/12, 192.168/16, 169.254/16,
  il nostro dominio, l'onion), con il DNS finto che risolve un nome
  pubblico su un IP privato, e con un redirect verso l'interno.
- **Il PIN.** La spec boltcard elenca come opzionale un `pinLimit`
  (msat): sopra quella cifra il callback vuole `&pin=`. Prima versione:
  non gestito e dichiarato — se il servizio risponde ERROR per il PIN,
  chi compra legge il motivo e paga col wallet. Il PIN chiesto nel foglio
  è un cantiere dopo, e non si salverebbe mai.
- **Liquidità in entrata.** Paga il nodo del servizio della carta verso
  la nostra fattura: serve capacità IN ENTRATA sul nostro LND, come per
  ogni pagamento di oggi (LNbits sul VPS, LND sul nodo via ponte). Niente
  di nuovo, ma chi paga è un custode grosso (Swiss Bitcoin Pay,
  CoinCorner) con rotte buone: se fallisce, è più facile che sia il
  nostro lato.
- **Anti-abuso.** Ogni chiamata costa due GET fuori: una presentazione
  per ordine ogni 30 secondi (il timbro) e poche per utente al minuto,
  con lo stesso 429 dei rate limit di casa.
- **Il nostro server non diventa un oracolo sulla carta.** Non si chiama
  `balanceCheck`, non si ricopiano `maxWithdrawable` e i limiti nei
  messaggi, non si dice al venditore (pezzo 3) niente più di
  «letta / pagata / rifiutata».

**Quanto lavoro.** Rotta + normalizzazione + guardia SSRF: ~150 righe in
`server.py`. Prove: ~80 righe in `prove.py` con `httpx` finto (le due GET
per ordine, il tag sbagliato, l'importo fuori limite, ERROR, il timeout,
la fattura corta, l'ordine altrui) più la guardia; un collaudo in gabbia
col server vero e un servizio-carta di cartone che risponde alle due GET
e poi «paga» la fattura sul LNbits finto — è la forma che
`collaudo_lnbits_muto` e i collaudi in CI hanno già. Verbale in CANTIERI e
la rotta nell'elenco delle rotte pubbliche di ARCHITETTURA (la
sentinella conta). Una giornata, il client compreso.

## 3. Di persona: chi vende incassa avvicinando la carta di chi compra

**Funziona, ed è la STESSA rotta.** Cambia chi la chiama e chi tiene il
telefono. Ed è la strada che vale di più: è l'unica per chi compra con un
iPhone, e la più naturale per il ritiro a mano — dove oggi il compratore
paga col wallet davanti al venditore, poi conferma («Ho ricevuto»: il
bottone c'è già in `locked` con `consegnaScelta === 'ritiro'`) e i sats
partono. Con la carta: tocco, `locked`, conferma, `released`. Il deposito
di garanzia resta in mezzo per costruzione, anche se dura un minuto.

**Il disegno.** L'ordine lo apre SEMPRE il compratore, sul suo telefono
(Telegram va benissimo: qui non deve leggere niente): «🔒 Compra in
sicurezza» → ordine in `creato`, fattura da 15 minuti. È lui che poi
conferma, apre dispute, prende XP — un ordine «per conto di» non esiste
in Barattolo e non deve nascere per questo. Il venditore vede l'ordine:
`/api/orders` non filtra per stato, quindi un `creato` gli compare già
(da verificare che la card lo mostri e cosa dice). Sulla sua card, in
`creato`: «📶 Incassa con Bolt Card». Tocca, il suo telefono (APK o
Chrome) legge la carta del compratore, la POST parte col SUO
`init_data`, e la rotta accetta perché `venditore_id == user` E lo stato
è `creato`. Da lì identico al pezzo 2; il poll del compratore vede
`locked` e la ricevuta parte a tutti e due.

**Il consenso, che è il punto del pezzo.** Il tocco della carta È il
consenso fisico del compratore, e la cifra è quella dell'ordine che ha
aperto lui. Ma un compratore può avere DUE ordini in `creato` con lo
stesso venditore (o uno grosso per sbaglio), e il venditore sceglierebbe
quale fattura presentare al link: un link vale una fattura, e il
venditore la sceglie lui. Cura: **il compratore designa l'ordine**, non
il venditore. Il modo più povero e più giusto è un codice a 4 cifre
sulla card del compratore in `creato` («fai leggere la carta a chi vende:
codice 7315») che il venditore scrive prima di toccare; oppure un QR
sulla card del compratore che il venditore inquadra (Telegram ha
`showScanQrPopup`, l'APK no: il codice a mano copre tutti e due). Il
server accetta la chiamata del venditore SOLO con il codice giusto, e il
codice vale per quell'ordine e per la vita della fattura. Costa venti
righe e chiude la domanda «e se il venditore presenta l'altro ordine?»
prima che qualcuno la faccia.

**Cosa NON cambia.** Chi può scrivere `delivered` (nessuno a mano, regola
5), chi conferma (il compratore), il tetto e la commissione, la ricevuta.
E la spedizione: questo pezzo ha senso per `ritiro` e per il digitale
consegnato lì; per la spedizione il compratore paga da casa col pezzo 1
o col wallet.

**I rischi in più, rispetto al pezzo 2.**

- **Il venditore tiene in mano il link del compratore** per un istante,
  dentro Chrome, e il link vale UNA fattura fino al limite della carta.
  Il nostro server presenta solo la fattura dell'ordine designato, quindi
  con la nostra app il venditore non può farci altro. Con un'ALTRA app
  di cassa sul suo telefono sì — ma quello è il rischio di ogni carta di
  ogni esercente, e la difesa è il limite per pagamento sulla carta. Va
  scritto nella spiegazione lunga, una volta: «la carta paga fino al
  limite che hai scelto tu, a chiunque la avvicini».
- **Il telefono del venditore deve avere l'NFC e Chrome/APK**: la
  tabella del pezzo 1 vale per lui. Un venditore con iPhone non incassa
  così, e il bottone non gli compare.
- **La scadenza in strada.** I 15 minuti della fattura partono quando il
  compratore apre l'ordine, non quando si incontrano: se apre l'ordine
  a casa e arriva dopo mezz'ora, la fattura è morta e il venditore legge
  «scaduta». La cura non è allungare `INVOICE_EXPIRY` (ha i suoi
  perché: lo stock riservato, l'ordine che si autodistrugge) ma un testo
  sulla card del compratore: «apri l'ordine quando sei davanti a chi
  vende», e la «ripresa» che gli ridà una fattura nuova se la vecchia è
  scaduta — è già il comportamento di `compra` con un ordine morto.

**Quanto lavoro.** Sul server: il ramo `venditore_id` nella rotta, il
codice a 4 cifre (una colonna o il diario, generato in `compra`,
mostrato al solo compratore) e le sue prove — mezza giornata. Nel client:
il bottone sulla card del venditore in `creato` e il codice sulla card
del compratore. Il giro dal vivo si fa a due telefoni e una carta vera:
è lo stesso banco della tappa 8 del P2P, cioè lo si sa già montare.

## 4. Cosa serve per decidere, in ordine

1. **La prova di cinque minuti (DA PROVARE, sul telefono di Andrea).**
   Aprire nell'APK una pagina che chiama `NDEFReader.scan()` — basta un
   lettore Web NFC pubblico, o venti righe nostre dietro una rotta di
   collaudo — e avvicinare una Bolt Card o la Swiss Bitcoin Pay Card.
   Se il permesso compare e il record `url` si legge, il pezzo 1 nell'APK
   è chiuso PER FATTO e non per costruzione. Se non compare, l'intero
   cantiere si riduce a «Telegram apre Chrome», che resta fattibile.
   Nello stesso giro: la stessa pagina dentro Telegram su Android deve
   dire `NDEFReader` assente — è la controprova che il ripiego serve.
2. **Una carta vera per il giro dal vivo.** Il servizio-carta di cartone
   basta per le prove in gabbia; il giro dal vivo vuole una carta con
   qualche migliaio di sats, e i suoi limiti letti dal pannello di chi la
   emette, per vedere il rifiuto vero sull'importo.
3. **Il tetto della carta contro i prezzi di Barattolo.** Le carte
   nascono con limiti per pagamento modesti (LaWallet ha avuto un tetto a
   10.000 sats; le altre lo lasciano scegliere): un ordine da 200.000
   sats verrà rifiutato dalla carta, e il messaggio deve dirlo senza
   numeri altrui. Non è un difetto nostro, ma va nel testo.
4. **Le firme del deploy e la rotta nuova** valgono come sempre: la rotta
   entra nell'elenco di ARCHITETTURA e nelle prove delle anteprime, o la
   sentinella la ferma.

**Strade scartate, con il perché, così non si ripropongono.**

- *Leggere la carta con l'NFC del sistema e un'app nostra nativa.* Non
  esiste un'app nativa: l'APK è una TWA, cioè Chrome. Scriverla per l'NFC
  di iPhone (Core NFC) è un altro progetto, e il pezzo 3 copre il
  compratore con l'iPhone senza scriverla.
- *Far pagare la carta al QR di sempre.* Una Bolt Card non inquadra
  niente: il verso è «io ti do un link, tu mi presenti una fattura». Il
  QR resta per i wallet.
- *Passare da LNbits (`lnurlscan`) per parlare con la carta.* Un tubo in
  più che può tacere, per due GET che il server sa già fare; e la
  fattura è la nostra, non una che LNbits deve coniare.
- *Salvare il link della carta «per ritentare».* Vale UNA fattura fino al
  limite della carta e non scade a tempo: tenerlo è tenere un titolo al
  portatore altrui. Si usa in pochi secondi e si butta.
- *Un ordine aperto dal venditore per il compratore.* Rompe la regola 5 e
  tutto ciò che poggia sull'identità del compratore (conferma, disputa,
  XP, recensione). L'ordine lo apre chi compra, anche se non legge niente.

## 5. Raccomandazione

Sì, e piccolo: **una rotta, una guardia, un bottone** — e la prova sul
telefono PRIMA di scrivere la rotta. Il valore vero non è «paga con la
carta da casa» (chi ha una Bolt Card ha anche un wallet, e da casa
inquadra il QR) ma **il ritiro a mano**: il compratore con un iPhone o
con Telegram che paga il deposito di garanzia con un tocco sul telefono
di chi vende, senza aprire niente. È il caso più vicino a un mercatino
vero, ed è quello in cui Barattolo si distingue da un punto cassa
qualsiasi: il tocco non paga il venditore, riempie la cassaforte. Se
Andrea lo apre, l'ordine è: prova sul telefono → rotta + SSRF + prove →
bottone nell'APK e «apri in Chrome» da Telegram → il codice a 4 cifre e
il bottone del venditore → giro a due telefoni con una carta vera.

## Fonti

- Spec Bolt Card: https://github.com/boltcard/boltcard/blob/main/docs/SPEC.md
  (formato URL, `p`/`c`, contatore crescente, limiti, `pinLimit` opzionale)
- LUD-03 withdrawRequest: https://github.com/lnurl/luds/blob/luds/03.md
  (campi, callback `k1`+`pr`, risposta `OK`/`ERROR`, pagamento asincrono)
- LUD-17 (schema `lnurlw://`), LUD-14 (`balanceCheck`), LUD-19
  (`payLink`): https://github.com/lnurl/luds
- Web NFC su Chrome per Android: https://developer.chrome.com/docs/capabilities/nfc
  (Chrome 89+, HTTPS, primo livello, gesto, pagina visibile, permesso)
- Web NFC, supporto per browser: https://caniuse.com/webnfc e
  https://developer.mozilla.org/en-US/docs/Web/API/Web_NFC_API
  (solo Chromium su Android; niente WebView legacy; niente iOS)
- Telegram Mini Apps, `openLink` e piattaforme: https://core.telegram.org/bots/webapps
- Swiss Bitcoin Pay Card: https://swiss-bitcoin-pay.ch/cards
  (LNURLw, senza registrazione, pannello `card.swiss-bitcoin-pay.ch`)
- Bolt Card, il sito: https://www.boltcard.org/ ; CoinCorner:
  https://support.coincorner.com/hc/en-us/articles/5600580995346-The-Bolt-Card ;
  estensione LNbits: https://github.com/lnbits/boltcards
- Il tetto a 10.000 sats di LaWallet, come esempio di limite per carta:
  https://github.com/lawalletio/lawallet-nwc/issues/304
