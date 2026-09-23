# Audit di sicurezza n. 2 — client, Mostro e infrastruttura nuova (23 settembre 2026)

Sola lettura, nessuna modifica al codice. Base: `origin/main` a `eb26d02`
(i numeri di riga qui sotto sono di quel commit). Lavorato in un worktree
isolato; il VPS, il nodo e il relay non sono stati toccati, nemmeno in
lettura. Copre quel che il primo audit (`docs/AUDIT-PAGAMENTI-2026-09-19.md`)
aveva dichiarato di non aver guardato — il client per intero, le patch Rust
sull'albero upstream, l'app Android — più tutto quel che è cambiato dopo il
19 settembre: il ponte WireGuard, il servizio da utente `barattolo`, il
giudice del deploy, le rotte P2P nuove, «paga da un'altra cassaforte».

**La domanda:** esiste un modo per rubare o bloccare sats, prendere il
controllo di un account o del server, deanonimizzare un utente, o far fare
all'app di qualcuno un gesto che non ha voluto?

**La risposta corta.** Nessuna falla che muova sats da sola. Una falla ALTA,
riprodotta in locale sul server di collaudo: **chiunque abbia una sessione
può dichiararsi «taker» (o «maker») di qualunque ordine del libro P2P con una
sola POST** — e da lì riceve i contatti Telegram/Nostr dell'altra parte,
compare nell'app dell'altra parte come la persona con cui sta scambiando, e si
prende la recensione dello scambio al posto di chi l'ha fatto davvero. Il
resto sono cose medie e basse, e sette voci del primo audit che restano
aperte. Il client è stato letto per intero e sondato dal vivo con payload
costruiti apposta: **nessuna XSS trovata** — ma il premio di una XSS è
cresciuto (nel `localStorage` vivono il segreto NWC, la sessione bunker e le
chiavi private del profilo di scambio), e una CSP sugli script non c'è ancora.

## Come leggere questo file

- **GRAVE** = sats persi o doppi, possibile oggi (nessuna, questo giro).
  **ALTA / MEDIA / BASSA** = il resto, in ordine.
- Ogni voce ha lo scenario passo per passo, la prova (riga di codice o
  riproduzione locale), e la cura proposta **come cantiere separato**: qui
  non si è curato niente.
- In fondo: cosa è stato trovato SANO, cosa NON si è potuto verificare (col
  comando di sola lettura), le prove che mancano.

## Cosa ho letto, e quanto a fondo

**A — IL CLIENT, `miniapp.html` per intero (52.070 righe), non a campione.**
Inventario meccanico di TUTTI i punti di iniezione nel DOM: 278 sink
(`innerHTML =`/`+=`, `insertAdjacentHTML`, `outerHTML`; zero `document.write`,
`eval`, `new Function`, `srcdoc`, `postMessage`), ognuno con le sue `${…}`
estratte e giudicate; poi una seconda passata su OGNI `${…}` del file che
nomina un campo scritto da utenti, relay, mostro o server (85 espressioni
fuori da `esc()`, guardate una per una); poi i contesti d'attributo
(`on*=`, `href`, `src`, `style`), i `.href =`/`.src =`, i deep link
(`location.search`, `location.hash`, `?barre`, `?diagnosi`), il
`CloseWatcher`, il bunker NIP-46, la nsec incollata, l'estensione, il wallet
NWC, i messaggi in arrivo dai relay (libro 38383/38385, buste kind 14 del
coordinatore, la chat cifrata fra le parti col recapito e il PayCode), il
`localStorage`/CloudStorage. E una SONDA DAL VIVO sul server di collaudo con
database usa-e-getta: annuncio e nome utente col payload
`<img src=x onerror=alert(1)>"'><svg/onload=alert(2)>`, guardati nella
vetrina, nel dettaglio e nella pagina negozio.

**B — MOSTRO.** Clonato `MostroP2P/mostro` al tag `v0.18.8` nello scratchpad,
applicate le sette patch con `git am` (entrano pulite: 19 file, +1581/−25),
letto per intero il diff sui file upstream e i due moduli
`barattolo_fee.rs` (508 righe) e `barattolo_eventi.rs` (830). Letti, sul
sorgente upstream, i controlli di autorizzazione di `add_invoice`, `release`,
`cancel`, `fiat_sent`, `dispute`, `admin_*`, e la validazione dell'ordine a
prezzo fisso in `order.rs`. Niente compilato (niente `cargo` qui).

**C — INFRASTRUTTURA E SERVER.** `deploy.sh` e `giudice_deploy.py` per intero;
le due unit di deploy e backup; `deploy/utente/` (drop-in, sudoers,
`cambio-utente.sh` per intero); `deploy/ponte/` (i quattro file); le ronde
del nodo (`ronda-tor.sh`, `ronda-liquidita.sh`, `ronda-superficie.sh`,
`tor-entrypoint.sh`, `Dockerfile.tor`); il workflow CI; `backup-fuori.sh` a
maglie larghe; la policy del relay. Del server: tutte le rotte `/api/p2p/*`
coi loro giudici (`_registra_ordini_p2p`, `_registra_chiavi_p2p`,
`_facce_ordini_p2p`, `_controparti_p2p`, `_parti_recensione_p2p`,
`_scambio_concluso_p2p`, `_parti_scambio_p2p`, `_avviso_recapito_p2p`,
`_evento_p2p_pulito`, `_registra_evento_p2p`, `_avvisi_libro_p2p`,
`_pagamenti_p2p`, `_sconti_per_chiavi_p2p`, `_seme_profilo_p2p`, le sveglie,
il canale), «paga da un'altra cassaforte» (`_esamina_altra_cassaforte`,
`_giudica_origine`, `sorveglia_crediti`), initData e sessioni, la guardia
CSRF, i cookie, il login Nostr e il collegamento firmato, `salva_npub`,
l'upload delle foto, i widget e le pagine pubbliche, `assetlinks.json`,
`genera_icone_apk.py`.

**D — ISTRUZIONI ESTRANEE.** Grep su tutti i file tracciati (e sui `docs/`)
per tag `system-reminder`/`<system`, «ignora le istruzioni», testo rivolto a
un'AI, caratteri invisibili (zero-width, RTL override, tag Unicode), `base64
-d`, `curl | sh`, `authorized_keys`; più `.claude/` della working copy e le
impostazioni globali di Claude Code.

**NON LETTO:** il progetto TWA (sta fuori dal repo: `AndroidManifest.xml` e
`LauncherActivity.java` non si sono potuti guardare — ne parla la sezione
«non verificato»); `prove.py` per intero (letto per grep, per dire dove una
difesa è tenuta da una sola sentinella di testo); i sorgenti di LNbits e
strfry; i file di deploy del relay oltre alla policy.

**STRUMENTI STATICI:** `bandit`, `semgrep` e `pip-audit` non sono installati
qui e non li ho scaricati. Al loro posto due script usa-e-getta nello
scratchpad (l'inventario dei sink e lo scanner dei campi utente) e le passate
a mano descritte sopra.

---

# ALTA

## A1 — Il posto del taker (e del maker) in `p2p_ordini` si prende con una POST

**Chi ci rimette:** chi scambia — la sua controparte vera, e la sua
reputazione. **Serve:** una sessione qualunque (anche un account nato un
minuto prima) e l'id di un ordine, che sta nel libro pubblico. **Riprodotto
dal vivo** sul server di collaudo (sotto).

### Il meccanismo

`_registra_ordini_p2p` (`server.py:37436`) è la rotta con cui il client dice
«questi ordini sono miei» (`pubblicati`) e «questo l'ho preso io» (`presi`).
Il ramo `presi` scrive `preso_da` su QUALUNQUE riga il cui `preso_da` sia 0 e
lo stato non sia finale — quindi anche su un ordine ancora `pending`, prima
che chiunque lo prenda:

```
UPDATE p2p_ordini SET preso_da=? WHERE ordine=? AND tg_id<>?
  AND (preso_da=0 OR preso_da=?) AND stato NOT IN ('success','canceled','expired')
```

Il commento sopra dice «a cose fatte quel posto non si prende più», ed è vero:
la difesa guarda il DOPO (una presa già dichiarata non si sovrascrive) e non
il PRIMA. Chi arriva primo vince, e il primo può essere chiunque. Il ramo
`pubblicati` ha lo stesso difetto per il maker: l'`INSERT OR IGNORE` intesta
l'ordine al primo che lo nomina, e per un ordine pubblicato da un ALTRO client
Mostro (che a Barattolo non dice mai niente) il primo è l'attaccante.

Da quella riga dipendono tre cose, e nessuna delle tre passa dal coordinatore:

1. **`_controparti_p2p`** (`server.py:37565`) serve il volto e i canali —
   `telegram` (lo @username) e `npub` — «dell'altra parte» leggendo `tg_id` e
   `preso_da` di `p2p_ordini`. All'attaccante arrivano i contatti del maker;
   al maker arriva la faccia dell'attaccante, col bottone «Scrivi su
   Telegram» che porta a LUI.
2. **`_parti_recensione_p2p`** (`server.py:37820`): a scambio concluso la
   recensione del maker va a `preso_da`, cioè all'attaccante; il taker vero è
   `estraneo` e non può né ricevere né lasciare niente.
3. **`_avviso_recapito_p2p`** (`server.py:38280`) ripiega su `p2p_ordini`
   finché il coordinatore non ha parlato: nella finestra fra la presa e il
   primo evento di mostrod, l'avviso «ti ha indicato dove inviare gli euro»
   parte verso l'attaccante (senza il recapito, che viaggia cifrato fra le due
   chiavi vere).

Gli eventi di mostrod (patch 0007) scrivono `p2p_scambi` con le trade key
VERE (`_registra_evento_p2p`, `server.py:40533`), ma **non correggono mai
`preso_da`**: le tre funzioni qui sopra continuano a leggere la dichiarazione.
Il giro del libro azzera `preso_da` a ogni `pending` visto
(`server.py:40248`), quindi su un ordine ancora in vetrina la dichiarazione
dura al più un minuto — ma una POST al secondo la tiene viva, e sull'ordine
GIÀ preso (da un altro client, o da un nativo Nostr che per scelta non
dichiara) una POST sola basta e resta per sempre.

### Lo scenario, passo per passo

1. L'attaccante (333) apre il libro e copia l'id di un ordine `pending` di 111.
2. Manda `POST /api/p2p/ordini {"ordini":[id],"presi":true}` — in un ciclo,
   una al secondo, finché il libro dice `in-progress`.
3. Il taker vero (444) prende l'ordine su mostrod; il suo client dichiara la
   presa: la riga porta già 333, la dichiarazione cade.
4. 111 apre lo scambio: vede «Attaccante», stelline di 333, «✈️ Scrivi ad
   Attaccante su Telegram». 333 apre `/api/p2p/controparte`: ha nome, negozio,
   @username e npub di 111.
5. Lo scambio va avanti fra le chiavi vere (i sats, gli euro e il recapito
   cifrato non passano di qui). A fine scambio 111 lascia cinque stelle «al
   taker»: finiscono sul profilo di 333. 444 resta senza.

Variante di ingegneria sociale: 333, con in mano il contatto Telegram di 111,
gli scrive «sono io il compratore, ho fatto il bonifico, libera i sats». La
pagina dello scambio dice il vero («euro inviati» lo dichiara solo il
compratore vero, via mostrod), ma il bottone Telegram che l'app stessa ha
messo davanti a 111 porta all'impostore.

### La prova

Server di collaudo dal worktree, database usa-e-getta, `P2P_ATTIVO=True`,
tre identità finte oltre alle solite:

```
maker 111 registra:                  200 {"ok":true,"registrati":1}
attaccante 333 si dichiara taker:    200 {"ok":true,"registrati":0}
taker vero 444 si dichiara dopo:     200 {"ok":true,"registrati":0}
controparte vista dal maker 111:     {"nome":"Attaccante", … "telegram":"attaccante"}
controparte vista dall'attaccante:   {"nome":"Compratore", … "telegram":"compratore"}
controparte vista dal taker vero:    {"controparti":{}}
```

Poi, con la riga portata a `success` (com'è a scambio finito):

```
recensibile per l'attaccante 333:    {"si":true,"motivo":""}
recensibile per il taker vero 444:   {"si":false,"motivo":"ignota"}
il maker 111 recensisce «il taker»:  200 {"ok":true,"voto":5}
feedback: [(da 111, per 333, 5 stelle)]   rating di 333: 5.0 (1 voto), di 444: 0.0
```

Copertura di oggi: `prove.py` fa girare `_registra_ordini_p2p` (18
menzioni) e prova che una presa già dichiarata non si sovrascrive; nessuna
prova dichiara la presa PRIMA della presa vera, e nessuna incrocia
`preso_da` con `p2p_scambi`.

### La cura proposta (cantiere suo)

1. **La parte la dice il coordinatore, non il telefono.** Dove esiste una riga
   in `p2p_scambi` (mostrod ha parlato), `_controparti_p2p`,
   `_parti_recensione_p2p` e `_facce_ordini_p2p` leggono compratore/venditore
   DA LÌ — è già quel che fa `_parti_scambio_p2p`, ed è la ragione per cui il
   recapito è al riparo dopo il primo evento. `p2p_ordini.tg_id`/`preso_da`
   restano la riserva per quando mostrod tace.
2. **`presi` si accetta solo se combacia.** La dichiarazione scrive
   `preso_da` solo se `p2p_scambi` per quell'ordine nomina come compratore o
   venditore proprio quel `tg_id`; altrimenti si tiene in una colonna
   `preso_dichiarato` che NESSUNA delle tre funzioni legge. Stessa regola per
   `pubblicati` sul maker.
3. **La recensione va a chi mostrod ha nominato**, mai a una dichiarazione.
4. **Il libro azzera `preso_da` anche fuori dal `pending`** quando
   `p2p_scambi` esiste e lo contraddice (una riga di riconciliazione nel giro
   del libro).
5. Una prova che fa esattamente i passi 1-5 dello scenario e pretende che 444
   riceva la recensione e 333 nulla.

**Da fare SUBITO, senza codice:** la query in fondo («non verificato») dice
se è già successo in produzione.

---

# MEDIA

## M1 — «Paga da un'altra cassaforte» sulla cassaforte SaaS: il calendario come giudice contro una hold invoice

`_giudica_origine` (`server.py:20662`) apre la porta con `ORIGINE_MORTA` in
due modi: LNbits/LND dicono `failed`/mai partito (buono), oppure — SOLO dove
LND non c'è, cioè sulla cassaforte SaaS — LNbits dice ancora `pending` ma la
fattura di quel tentativo è scaduta da più di 60 minuti
(`ALTRA_CASSAFORTE_DOPO_SCADENZA_S`, `server.py:20642`). Il commento sopra
la costante lo dice da solo: «NON È UNA PROVA CONTRO UNA HOLD INVOICE: un
HTLC già accettato si può saldare fino al suo CLTV — giorni». È il residuo
di G1 del primo audit, spostato in un gesto che fa UNA PERSONA con le voci
davanti, e sorvegliato da `sorveglia_crediti` (`server.py:21177`), che
AVVISA a doppio pagamento avvenuto: non lo impedisce.

**Scenario:** venditore con Lightning address su un server suo che conia hold
invoice; ordine su cassaforte SaaS; il payout resta `pending`, la fattura
scade; dopo un'ora un moderatore vede «origine morta», paga dal nodo; il
venditore salda l'HTLC: pagato due volte, e la ronda lo dice dopo.

**Quanto vale oggi:** poco — la SaaS ha una manciata di ordini vecchi, e serve
il tocco di un moderatore. Ma è l'unica porta rimasta a un doppio pagamento
e sta scritta nel codice come accettata. **Cura:** sulla cassaforte senza
LND, `pending` = `ORIGINE_VIVA` sempre; chi vuole pagare lo stesso passa da
un `--forza` esplicito con la frase «se si salda anche l'origine, avete pagato
due volte» e un tetto in sats; oppure si chiudono a mano i payout SaaS
residui e la strada si spegne.

## M2 — L'ordine-trappola a prezzo fisso: nessun avviso sul distacco dal mercato

Upstream non confronta `amount` con `fiat_amount` su un ordine a prezzo
fisso (`calculate_and_check_quote`, `src/app/order.rs:15-34`: con `amount >
0` la quote È l'amount; si controllano solo i tetti). Il client mostra
tutt'e due i numeri — «Paghi 100,00 €» grande e «ricevi ≈ 985 sats» piccolo
(`rigaOrdineP2P`, `miniapp.html:40064`) — ma `badgePremioP2P`
(`miniapp.html:40038`) tace apposta sugli ordini a prezzo fisso che non
sono Barattozon («quel prezzo il mercato non lo guarda»), e il conto del
dettaglio (`contoDettP2P`, `miniapp.html:44857`) scrive premio zero. Un
venditore pubblica «100 € per 1.000 sats» e chi legge in fretta la riga
grande paga cento euro per un euro di sats; lo stesso, rovesciato, su un
ordine di acquisto. Non è un furto nel senso del protocollo (i due numeri ci
sono), è un'app che non avverte dove Barattozon invece lo fa. **Cura:** il
premio implicito — che il codice sa già calcolare
(`premioImplicitoTabacchinoP2P`) — si calcola per OGNI ordine a prezzo fisso
a cambio vivo; oltre ±20% la card porta un badge rosso e il foglio della
presa chiede una conferma esplicita con la cifra del mercato accanto.

## M3 — `/api/p2p/canale`: chiunque scrive nel canale pubblico, senza limite e senza un ordine

`annuncia_ordine_p2p_canale` (`server.py:38700`) posta nel canale «Barattolo
Vetrina» lato, euro e metodo che arrivano dal corpo, con la firma del
mittente. Nessuna prova che l'ordine esista (dichiarato nel docstring),
nessun limite di frequenza, nessun anti-doppione. Un account P2P manda mille
post in un minuto — «Vende BTC 99.999 € Contanti» — e il canale è da
ripulire a mano, col nome di Barattolo sopra. Il metodo passa da
`html.escape`, quindi niente HTML: è spam, non iniezione. **Cura:** un post
ogni 10 minuti per persona e uno per ordine (chiave `ordine` nel corpo,
UNIQUE su una tabella `p2p_canale_post`), e prima di postare il server
controlla sullo specchio del libro (`p2p_ordini`, che il giro riempie) che
quell'id esista ed appartenga a chi chiede.

## M4 — Un XSS ruberebbe il wallet: la CSP sugli script non c'è ancora

Non è una falla nuova (M8 del primo audit, ancora aperta) ma il premio è
cambiato. Nel `localStorage` vivono: il segreto NWC (`barattolo_nwc@<tg_id>`,
`miniapp.html:38702`, con `pay_invoice` per il mercatino), la chiave client
del bunker (`barattolo_bunker`, `miniapp.html:38407`), e il MAZZO del
profilo di scambio — le chiavi private con cui si parla a mostrod
(`barattolo_mostro`, `miniapp.html:40933`). Con il mazzo si fa `release` al
posto del venditore. Il client non ha una XSS (vedi «sano»: 278 sink, 85
espressioni sui campi utente, sonda dal vivo), ma la sola CSP è
`frame-ancestors` (`server.py:1605`) e una riga sbagliata domani non trova
nessuna seconda difesa. **Cura:** `script-src 'nonce-…'` generato per
risposta su `/` e `/miniapp.html` (gli script sono inline: serve il nonce sui
`<script>` di pagina, e `'self'` per `vendor/`), `object-src 'none'`,
`base-uri 'self'`. Costa un giro sul markup; è la sola cosa che regge a un
`esc()` dimenticato.

## M5 — Dal primo audit, ancora aperte e riverificate su `eb26d02`

- **M2 (SSRF cieca dal Lightning address):** `invoice_da_ln_address` fa
  ancora `follow_redirects=True` e nessun controllo sull'IP del `callback`
  (`server.py:9748`); la guardia anti-SSRF che esiste (`url_foto_ammesso`,
  `server.py:14017`) è solo per le foto del CSV. Ora che il servizio gira da
  `barattolo`, dalla porta 18080 si arriva alla REST di LND via WireGuard (con
  un macaroon: la GET cieca non lo porta) e a LNbits su `127.0.0.1:5001`.
- **M5 (chiavi P2P senza firma):** `_registra_chiavi_p2p` (`server.py:37385`)
  accetta ancora qualunque 64-hex; lo sconto si presta.
- **M7 (comandi del bot per username):** `ADMIN_BOT_USERNAME`
  (`server.py:12401`) è ancora lì.
- **B1:** la firma dell'initData si confronta ancora con `!=`
  (`server.py:6938`).
- **M4 (12 s nel ciclo seriale):** `LOOKUP_BUDGET` è ancora 12 s e la
  domanda dello sconto gira ancora dentro la presa (`barattolo_fee.rs:55`);
  nessun interruttore dopo N fallimenti.
- **M6 (i due segreti):** `ENV_SECRET_FALLBACK` c'è ancora
  (`barattolo_eventi.rs:34`): se sul nodo manca `BARATTOLO_EVENTI_SEGRETO`, chi
  legge il segreto dello sconto fabbrica eventi. Da verificare col comando in
  fondo.
- **A2 (il seme del profilo lo ricava il server):** invariato
  (`_seme_profilo_p2p`, `server.py:37262`); e ora A1 mostra un secondo modo,
  senza segreti, di mettersi in mezzo a uno scambio.

---

# BASSA

- **B1 — `esc()` dentro `onclick`** (`miniapp.html:34804-34805`,
  `decidiPagamento('${esc(p.tipo)}', …)`): l'HTML decodifica le entità PRIMA
  che il JS legga l'attributo, quindi `esc()` lì non protegge da niente. Oggi
  `p.tipo` è una costante del server (`ordine`/`rimborso`/`sblocco`) e non c'è
  danno; il pattern è sbagliato e va sostituito con `data-tipo` +
  `this.dataset.tipo`, come già fa il resto del file (`miniapp.html:40766`).
- **B2 — `pontiContatto` si fida di chi la chiama** (`miniapp.html:16188`):
  `username` e `npub` entrano nudi in `onclick="apriChat('${username}')"`. I
  tre chiamanti puliscono con una regex (`16053`, `11805`, `51136`), e in
  produzione lo username lo scrive Telegram e la npub passa da `RE_NPUB` o
  `hex_to_npub`; ma la difesa vive nei chiamanti e non nella funzione. Cura:
  la regex dentro `pontiContatto`.
- **B3 — Le sfide del login Nostr si sfrattano a vicenda:** `SFIDE_LOGIN` ha
  un tetto di 1000 con sfratto FIFO (`server.py:7124`); mille GET anonime a
  `/api/login/nostr/sfida` in cinque minuti fanno fallire il login Nostr a chi
  aveva la sfida in mano. Cura: sfide legate all'IP con un tetto per IP, o un
  HMAC senza stato al posto del dizionario.
- **B4 — Chi buca il servizio riavvia il ponte a piacere:** le quattro righe
  di sudoers permettono a `barattolo` `systemctl restart tor` e
  `wg-quick@wg0` senza limiti (`deploy/utente/sudoers-barattolo-ponte`). Il
  guardiano ha il suo freno a 15 minuti, ma un processo compromesso lo
  scavalca chiamando `sudo` da sé: una tempesta di restart spegne l'onion e
  il ponte. Accettato dal cantiere; una regola polkit con un rate limit, o un
  wrapper sudoers che rifiuta più di un restart al minuto, lo chiude.
- **B5 — Nomi fissi in `/tmp` da root sul nodo:** `ronda-liquidita.sh` scrive
  `/tmp/liq-ch.json` e `/tmp/liq-info.json`, `ronda-tor.sh` `/tmp/ronda-tor-fwd`.
  Se sull'host esiste un utente non root (su LNVPS Debian di solito c'è
  `debian`), un symlink piazzato prima farebbe scrivere root altrove — a meno
  che `fs.protected_symlinks=1`, che è il default di Debian e lo blocca. Da
  confermare col comando in fondo; cura `mktemp`.
- **B6 — La risposta dello sconto si legge tutta in memoria:** `ask_server`
  (`barattolo_fee.rs:136`) fa `response.text()` senza tetto. Un server
  compromesso che risponde con un corpo da gigabyte lo fa scaricare a mostrod
  dentro il ciclo seriale. Cura: `Content-Length` sopra 64 KB = no.
- **B7 — La cintura di cartone del deploy resta scritta:** a file dei
  firmatari assente `deploy.sh` accetta l'autore fra `NOSTRI`
  (`deploy.sh:87`), che è testo libero. Le firme sono ACCESE (23 set: una
  punta nuda rifiutata), quindi oggi non morde; ma se il file sparisse per
  un errore di ripristino, il deploy tornerebbe a fidarsi di una riga che
  chiunque scrive, e lo direbbe solo nel journal. Cura: a file assente
  «rifiutato», non «cintura».
- **B8 — Le action della CI non sono inchiodate allo sha** (`actions/checkout@v5`,
  `actions/setup-python@v6`). Sono di GitHub, il token è `contents: read`, e
  il VPS non si fida della CI ma della firma: il danno possibile è un rosso
  finto. Basso, e si dichiara.
- **B9 — I tg_id nel journal:** le rotte P2P stampano a chi è partito ogni
  avviso (`server.py:38418`, `_esiti_p2p_dice`), e il journal è anche la
  prima cosa che si incolla in chat quando qualcosa non va. Non è un segreto,
  è una traccia: da tenere a mente quando si incolla.
- **B10 — La nsec incollata resta in memoria come stringa:** `firmatarioNsec`
  (`miniapp.html:38473`) azzera i byte della chiave dopo la prima firma, ma la
  stringa `nsec1…` letta dal campo non si può azzerare in JavaScript e vive
  fino al garbage collector. Inevitabile nel browser; si dichiara.
- **B11 — Il diario di diagnosi porta nomi e stati:** `testoDiagnosiP2P`
  (`miniapp.html:44144`) mette in clipboard id degli ordini, chiavi troncate,
  errori grezzi. Va in clipboard e non nel DOM (verificato), ed è un gesto
  dell'utente: va bene, ma «incollala a chi ti sta aiutando» vuol dire anche
  «a un estraneo in un gruppo Telegram».

---

# Verificato e trovato SANO

**Il client — XSS.** Ogni titolo, descrizione, nome, username, negozio,
racconto, commento, recensione di mercatino e P2P, recapito, PayCode,
metodo di pagamento dal 38383, motivo di moderazione, nota delle leve, nome
file, npub, contenuto digitale passa da `esc()` prima del DOM (inventario dei
278 sink e scanner delle 85 espressioni: le sole fuori da `esc()` sono
costanti del client — cataloghi di categorie, condizioni, taglie, tappe del
tour, emoji da `EMOJI_CAT` — o vanno in `textContent`: `toast`,
`chiediConferma`, `bunkerDice`, `apriCollega`). `condPill`, `nomeVia`,
`avatarImg` (filtro alfabeto sul nome file), `titoloRiga` sono su cataloghi
interni. Nessun `href="${…}"` con dati altrui: l'unico è l'`auth_url` del
bunker, ammesso solo se `^https?://` (`miniapp.html:38442`); `intent://` e
`nostrsigner:` restano non toccabili. Gli `<img src>` passano da `esc()` o
da un filtro sul nome. Nessun `javascript:`, nessun `postMessage` in ascolto,
nessun `eval`/`Function`, nessun `srcdoc`. Le pagine pubbliche e i widget
del server usano `_testo`/`_attr` (`html.escape`, `server.py:54180`). La
sonda dal vivo (annuncio + nome venditore col payload) non ha prodotto
nessun elemento iniettato, nessun alert, e il bottone di contatto è uscito
come `apriChat('imgsrcxonerroralert1svgonloadalert2')`.

**Il client — identità e chiavi.** L'initData va SOLO al nostro `API_BASE`
(tutte le `fetch(` censite). La nsec firma in pagina e non parte mai
(`entraConNostr` manda il solo evento 22242). Il bunker conserva la chiave
del CLIENT NIP-46, non quella dell'utente. Le sfide di login sono monouso,
scadono in 5 minuti, legate all'host (`verifica_evento_login`). La npub
entra solo nella forma `RE_NPUB` o da `hex_to_npub` dopo una firma
verificata; il collegamento firmato ripete la condizione nella WHERE.

**Il client — P2P.** I relay si costruiscono con `new NT.Relay(url)`, che in
nostr-tools 2.23.12 porta `verifyEvent`: ogni evento è firmato o cade. Il
libro si legge solo da `authors: [mostro]`; i `${…}` dei suoi tag passano da
`esc()`; il `rating` è in un `try` e la media è clampata a 5; `fa`/`amt`
passano da `Number` e da un floor. Le buste del coordinatore (kind 14) si
accettano solo se `ev.pubkey === mostroHexP2P()` e si decifrano NIP-44 con la
trade key dell'ordine (`mostroArriva`, `miniapp.html:43315`); i messaggi
dell'altra parte solo se firmati dal `peer` che mostrod ha nominato, con
tetto di byte, tolleranza d'orologio e secchio anti-raffica
(`campoArriva`, `miniapp.html:49367`). Il recapito degli euro e il PayCode
sono testo cifrato fra i due telefoni: il server non li vede e il DOM li
riceve escapati. Il segnale «sto facendo un gesto» non esiste più (tolto con
la 0007). Il wallet NWC nel P2P fa solo `make_invoice`; nel mercatino paga
la fattura del NOSTRO server. Il `?barre` passa da una regex stretta
(`^\d{1,4},\d{1,4}(,\d{2,4})?$`); `?diagnosi=1` e il `CloseWatcher` toccano
solo la pagina.

**Mostro — le sette patch su v0.18.8.** Entrano pulite con `git am`. Gli
agganci della 0005 stanno dove devono: `apply_party_fees` gira dopo il
calcolo dell'importo e PRIMA della validazione della fattura del compratore
(`take_sell.rs:205`) e prima della hold invoice (`take_buy.rs:159`); i tre
usi lato venditore di `order.fee` passano da `seller_fee` (`util.rs:1584`,
`flow.rs:109`, `add_invoice.rs:127`); la riga a lato si fida solo se
`amount` e `fee_buyer` combaciano; sconto clampato a `MAX_DISCOUNT=0.01`,
`parse_discount` spegne su qualunque errore, solo un `true` letterale sotto
`sconti[<chiave>]` concede; ogni fallimento è fee piena; `party_fee` non
va mai sotto zero. La 0007 non blocca mai il ciclo (task a parte, 8 s + 5 s
+ 12 s, un retry, mai su 4xx), manda solo id, azione, ora, due pubkey, attore,
un dettaglio filtrato a `[A-Za-z0-9_-]{0,40}` e tre importi SOLO su
`released`/`success` (`payload`, `event_of`); i log stampano l'URL, mai il
Bearer. L'aggancio pre-claim in `do_payment` classifica l'errore per classe
e non ne copia il testo. La 0004 e la 0002 sono quel che dicono. Upstream:
`add_invoice` e `fiat_sent` pretendono la chiave del compratore, `release`
quella del venditore, `dispute` una delle due, `admin_*` il solver assegnato.
Il server di Barattolo non può, tramite la risposta dello sconto o gli
eventi, cambiare importi, stati o destinatari di un ordine: dice sì/no per
chiave e riceve una cronaca.

**Il server — le rotte P2P nuove.** `/api/p2p/sconto` e `/api/p2p/evento`:
404 a leva spenta, Bearer a tempo costante e a byte, corpo ripulito campo per
campo (`_evento_p2p_pulito`: azione e attore da lista chiusa, chiavi 64-hex,
`ts` entro ±900 s e non `bool`, importi interi 0…10⁹ solo su due azioni),
idempotenza su `(ordine, momento, quando)`. `/api/p2p/seme`: nessun
parametro, `tg_id > 0`, `no-store`, il sale nasce con `INSERT OR IGNORE` e si
rilegge. `/api/p2p/chiavi` GET: un conto, mai una pubkey; DELETE: via tutto,
volti e parti compresi. `/api/p2p/recapito`: risponde sempre `{"ok": true}`,
avvisa solo chi VENDE secondo mostrod (o i telefoni), a scambio vivo, massimo
3 per giro e uno al minuto, e il recapito non ha un campo dove passare.
`/api/p2p/pagamenti`: parti da `p2p_scambi`, chi non è della partita riceve
niente. `/api/p2p/facce` e `/controparte`: POST senza id nell'URL. Le
sveglie: una chiave sola letta dal corpo, tetto 20, orizzonte 72 h.
`_registra_evento_p2p` riscrive le parti a ogni evento e una chiave ignota
vale 0.

**Il server — «paga da un'altra cassaforte».** Solo admin; le guardie si
rifanno alla conferma; UPDATE condizionato a `payout_stato='incerto'` E alla
cassaforte d'origine letta (due mani = un 409); `conferma: true` obbligatoria;
gli hash tentati si timbrano `DEVIATO`, i crediti si scrivono prima di
pagare, `_riprendi_uscita` tiene il lucchetto per ordine. Sulla cassaforte
NODO, LND `IN_FLIGHT` = viva, e il calendario non si guarda mai. (M1 è il
solo ramo SaaS.)

**Il server — il resto.** Login: cookie `HttpOnly`, `Secure` fuori dal
collaudo, `SameSite=Lax`; la guardia CSRF confronta `Origin` con `Host` su
ogni POST/PUT/PATCH/DELETE con cookie; CORS `*` senza credenziali; l'initData
scade a 24 h e la data sta dentro la stringa firmata. Le rotte dei
moderatori usano `e_admin` (id). Upload foto: tetto 15 MB, Pillow decide il
formato, niente nome dal client. `/.well-known/assetlinks.json` è una rotta
esplicita a file singolo (regola 3) con la sola impronta pubblica.
`/api/salute` dice ok/giu e mai da dove. Le rotte per file dei contenuti e
delle buste portano `sandbox; default-src 'none'`.

**L'infrastruttura.** `deploy.sh`: fetch esplicito dei due ref, giudice in
ordine di costo (antenato di `origin/main` → solo in avanti → firma della
punta con `allowedSignersFile` fuori dal repo → CI chiesta a GitHub col
token di sola lettura), tre verdetti, timbri `.deploy-rifiutato` e
`.deploy-bocciato`, `--forza` non salta il giudice, il giudice è sempre lo
script GIÀ in produzione (copia sotto `/run`, `RuntimeDirectory` 0700), il
motivo passa da `scappa` prima di Telegram. `giudice_deploy.py`: token da
`git credential fill` (mai da argomento né ambiente), `_senza_token` su ogni
riga stampata, giro valido solo se `event == push` e `head_branch == main`,
`skipped`/`cancelled` non sono verdi, un lavoro che manca a giro finito è
un no, nel dubbio «aspetta». La CI: `contents: read` sui due job, `pronto`
solo su push a main, push senza `--force`, scanner dei segreti su file E
cronologia. L'utente `barattolo`: non scrive in nessun posto da cui root
esegue (codice e config di root, `dati/`, `foto/`, `buste/`, `contenuti/`,
`import_tmp/` suoi), `UMask=0027`, drop-in reversibile in due comandi, sudoers
di quattro righe complete di argomenti provate con `visudo -cf` prima di
posarle, il cambio si annulla da solo al primo guasto, la scrittura di prova
sul database si fa come `barattolo` e si annulla. Il ponte WireGuard: chiavi
private fuori dai file, sul nodo la catena `WG-PONTE` in cima a INPUT (ACCEPT
solo `10.77.0.2 → 10.77.0.1:18080/tcp`, DROP del resto dal tunnel, DROP verso
`10.77.0.1` dalle altre interfacce, 51820/udp solo dall'IP del VPS), FORWARD
chiuso nei due versi e in `DOCKER-USER`, v6 chiuso, la chiave caricata per
ultima così il tunnel non esiste senza firewall; sul VPS nessuna porta in
ascolto, `AllowedIPs` di un solo indirizzo; i due socat con `DynamicUser`,
`NoNewPrivileges`, `ProtectSystem=strict`, TLS end-to-end col cert di LND;
la superficie della ronda confronta la catena regola per regola invece di
impararla. Il proxy trasparente di tor riapplica le tre REDIRECT e il DROP
del FORWARD (v4 e v6) a ogni avvio, fail-closed se manca iptables. La policy
del relay accetta scritture solo dalle chiavi in lista più quella della
piattaforma. Il backup cifra con la sola chiave pubblica age.

**L'app Android (dal repo).** `genera_icone_apk.py` concede il permesso
sull'URI dello splash al SOLO proprio pacchetto (`grantUriPermission(getPackageName(), …)`);
il parametro `barre` viene aggiunto alla URL di avvio della libreria e la
pagina lo legge con una regex stretta; il tema opaco è sulla sola
`LauncherActivity`. Quel che non sta nel repo è in «non verificato».

**Punto D — istruzioni estranee.** Nei file tracciati (workflow, script,
docstring, commenti, `docs/`, CLAUDE.md): nessun tag `system-reminder` o
`<system`, nessun «ignora le istruzioni», nessun testo rivolto a un'AI,
nessun carattere invisibile, nessun `base64 -d`/`curl | sh`/`authorized_keys`.
`.claude/` della working copy (non tracciato): solo `permissions` (401
allow, nessun `deny`, nessun `hooks`), `launch.json` con quattro server
locali; le impostazioni globali hanno il solo `theme`, nessun hook. **Il
blocco `<system-reminder>` visto nell'output di `git` il 18-21 set è dello
STRUMENTO, non del repo:** in questa sessione lo stesso blocco («Attribution
for git commits…», «send it with SendUserFile») è comparso in coda al
risultato del PRIMO comando Bash, che leggeva file di memoria e non toccava
git. È il promemoria interno di Claude Code appeso ai risultati dei tool: un
file del repo non può produrlo, e infatti non c'è.

---

# Cosa NON ho potuto verificare, e il comando di sola lettura

Sul **VPS** (li lancia Andrea):

```bash
sqlite3 -readonly /srv/barattolo/dati/satmarket.db "SELECT o.ordine, o.tg_id, o.preso_da, s.compratore, s.venditore FROM p2p_ordini o JOIN p2p_scambi s USING(ordine) WHERE o.preso_da NOT IN (0, s.compratore, s.venditore) OR (o.tg_id NOT IN (0, s.compratore, s.venditore) AND s.compratore>0 AND s.venditore>0);"
```
Vuoto = A1 non è (ancora) successo in produzione. Ogni riga è un posto preso
da chi mostrod non ha nominato: da guardare a mano, recensioni comprese
(`SELECT * FROM feedback WHERE scambio=<ordine>`).

```bash
sqlite3 -readonly /srv/barattolo/dati/satmarket.db "SELECT COUNT(*), COALESCE(SUM(prezzo_sats),0) FROM ordini WHERE COALESCE(NULLIF(cassaforte_payout,''), cassaforte)='saas' AND stato NOT IN ('released','refunded','annullato');"
```
Quanto è ancora esposto a M1.

```bash
systemctl show barattolo -p User -p ExecStart -p WorkingDirectory; sudo -l -U barattolo; ls -ld /srv/barattolo /srv/barattolo/.git /srv/barattolo/config.py /srv/barattolo/dati /srv/barattolo/foto
```
Utente, i quattro riavvii e nient'altro, permessi (750 root:barattolo,
`.git` 700, config 640, `dati` 700 barattolo).

```bash
ls -l /etc/barattolo-deploy/firmatari && cut -d' ' -f1,2 /etc/barattolo-deploy/firmatari && git -C /srv/barattolo -c gpg.ssh.allowedSignersFile=/etc/barattolo-deploy/firmatari verify-commit HEAD; echo "esito $?"
```
Il file c'è, i principal (senza le chiavi), e la punta in produzione è
firmata da una di quelle chiavi.

```bash
ss -ltnup | grep -E ':(18080|5001|8080|51820) '; wg show wg0 | grep -vE 'private|preshared'
```
18080/5001/8080 solo su `127.0.0.1`, nessuna 51820 in ascolto sul VPS, un
solo peer, handshake recente.

```bash
sysctl fs.protected_symlinks
```
(Anche sul nodo.) Deve dire 1 (B5).

Da **fuori** (dal PC):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"ordini":["x"],"presi":true}' https://barattolo.store/api/p2p/ordini
```
Deve dire 401 (senza sessione la rotta non si tocca: A1 vuole una sessione,
che chiunque può aprire con un account Telegram).

```bash
curl -sI https://barattolo.store/ | grep -i content-security-policy
```
Oggi solo `frame-ancestors` (M4).

Sul **nodo** (li lancia Andrea):

```bash
docker compose exec mostro sh -c 'env | grep -o "^BARATTOLO_[A-Z_]*"'
```
Solo i NOMI: `BARATTOLO_EVENTI_SEGRETO` deve esserci, o i due segreti sono
uno (M5/M6).

```bash
docker compose exec lnd lncli listmacaroonids; docker compose exec mostro sh -c 'ls -l /config/*.macaroon 2>/dev/null'
```
E `lncli printmacaroon --macaroon_file <quello di mostrod>`: deve avere
`info`, `invoices`, `offchain` e NIENTE `onchain`, `peers`, `macaroon`,
`signer`, `message`. (CLAUDE.md lo dice; questo lo prova.)

```bash
iptables -S WG-PONTE; iptables -S INPUT | head -3; iptables -S FORWARD | grep wg0; iptables -S DOCKER-USER | grep wg0
```
La forma di `wg0-nodo.conf`, che la ronda già confronta.

```bash
id debian 2>/dev/null; ls -l /tmp/liq-*.json /tmp/ronda-tor-fwd 2>/dev/null
```
Se c'è un utente non root, B5 conta.

Nel **progetto TWA** (fuori dal repo, sul PC):

```bash
grep -nE 'exported|<provider|<activity|intent-filter|android:host|grantUriPermissions' app/src/main/AndroidManifest.xml
```
`FileProvider` con `android:exported="false"` e `grantUriPermissions="true"`;
`LauncherActivity` esportata SOLO con i filtri VIEW sul nostro host; nessun
altro componente esportato. E `grep -n "Barattolo:" app/src/main/java/*/LauncherActivity.java`
deve trovare i tre marcatori del generatore.

**Rust mai compilato qui:** la logica delle patch l'ho letta sull'albero
patchato, non vista girare. In particolare non ho verificato che
`reqwest` nel container esca dal proxy trasparente come il resto (lo dice la
rete, non il codice) né che `BARATTOLO_SCONTO_URL` punti a `https://` (un
`http://` manderebbe il Bearer in chiaro attraverso Tor fino all'exit).

---

# Le prove che mancano

Dove oggi c'è solo una sentinella di TESTO (cerca una stringa nel sorgente e
non fa girare niente): il giudice di `deploy.sh` (antenato, solo in avanti,
`verify-commit` — «un `pronto` che non discende da main non si mette» non è
mai stato ESEGUITO: `prove.py` legge `deploy.sh` per grep, righe 40449 e
40850), `compare_digest` delle porte P2P, `pontiContatto`. `giudice_deploy.py`
invece gira davvero con un GitHub di cartone, come `_registra_ordini_p2p`,
`_controparti_p2p`, `_avviso_recapito_p2p`, `_giudica_origine`.

Da scrivere, in ordine:

1. **A1 che gira:** i cinque passi dello scenario contro le funzioni vere;
   rossa oggi, verde con la cura; più la riconciliazione `p2p_ordini` ↔
   `p2p_scambi`.
2. **`deploy.sh` a due repo di cartone:** un `pronto` fuori da main, uno
   indietro, uno con la punta non firmata a file dei firmatari presente, uno
   a file assente (che con la cura di B7 deve essere rifiutato, non «cintura»).
3. **M1:** cassaforte SaaS, LNbits `pending`, fattura scaduta da due ore →
   «altra cassaforte» deve dire `viva`.
4. **M2:** un 38383 a prezzo fisso con `amt` al 5% del mercato → la card
   porta l'avviso e la presa chiede conferma.
5. **M3:** due `/api/p2p/canale` in un minuto dallo stesso account → la
   seconda non posta.
6. **B1/B2 come prove del client:** il banco che carica `miniapp.html` in un
   DOM finto (c'è già per altre cose) e prova `pontiContatto('a\')…')` e la
   coda pagamenti con un `tipo` storto: nessun `onclick` rotto.
7. **CSP:** una sentinella che fallisce se `/` risponde senza `script-src`,
   il giorno che M4 si chiude.
8. **Il fixed `/tmp` delle ronde:** una prova sul nodo (dove le ronde
   vivono) è fuori portata; nel repo basta la sentinella «nessun
   `/tmp/<nome fisso>` negli script di `deploy/nodo/`».
