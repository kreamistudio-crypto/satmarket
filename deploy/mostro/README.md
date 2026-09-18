# IL FORK DI MOSTRO — sette patch sopra il tag v0.18.7

Qui dentro non c'è codice in servizio: ci sono le patch che il nodo Mostro di
Dublino applica sopra il sorgente upstream, prodotte con
`git format-patch`. Il codice vero vive sul nodo, nel branch
`barattolo/v0.18.7` di `~/nodo/mostro-src`, e queste sono la sua copia
fuori dalla macchina — perché se quella macchina sparisse, il fork
sparirebbe con lei.

**Non esiste nessun fork su GitHub, ed è una scelta.** Il posto giusto
per questo codice è una pull request a monte: il fork è un tappo che
tiene finché upstream non accoglie (o rifiuta) le tre modifiche. Tenere
un fork pubblico vivo vorrebbe dire mantenerlo per sempre, ed è
esattamente il lavoro che non vogliamo.

Fatto l'8 settembre 2026. Upstream: `v0.18.7`, commit `afc39a2`.

## LE SETTE PATCH, cosa fanno e perché

**0001 — `src/lnurl.rs`, i tre budget da 4s/2s/2s a 30s/15s/10s.**
Un coordinator che esce solo da Tor misura **10,6 secondi** per la
prima richiesta LNURL su circuito freddo (`dns 0.138s`,
`connect 0.138s`, `tls 10.336s`), contro **0,9s** a circuito caldo.
Tutto il tempo se lo mangia il TLS, e il `connect` MENTE sotto il proxy
trasparente: il kernel chiude la stretta di mano locale appena il SYN
tocca il socket in ascolto, prima che Tor guardi il pacchetto — chi
legge il solo `connect` conclude che la rete va benissimo. I nuovi
numeri sono circa 3× il costo misurato. Il prezzo dichiarato: il limite
oltre il quale un host che tace non può più bloccare il ciclo seriale
dei messaggi si allarga da 4 a 30 secondi, e i commenti nel codice ora
lo dicono invece di raccomandare la brevità.

**0002 — `src/config/util.rs`, `dev_fee_percentage = 0` diventa
valido.** `MIN_DEV_FEE_PERCENTAGE` è 0.10 e la guardia usa `<` stretto,
quindi lo zero veniva rifiutato: un coordinator che non riesce a pagare
la dev fee non aveva nessun modo di dirlo, poteva solo pagare almeno il
10% della propria fee o non partire. Lo zero è già uno stato
supportato ovunque nel resto del codice — `find_unpaid_dev_fees` ha
`AND dev_fee > 0` nella query, quindi un ordine a fee nulla non entra
mai nella coda dei pagamenti — tranne in quel controllo.
**Si allenta solo il minimo, mai il massimo**: i negativi restano
invalidi, la fascia fra zero e il minimo resta invalida (chi paga, paga
almeno il 10%: non si apre una scala grigia dove si dichiara di
partecipare pagando lo 0,1%), e il tetto non è toccato. I confronti
sono solo di ordinamento, nessuna uguaglianza fra float.

**0003 — `src/app/dev_fee.rs`, i due cappelli annidati da 15s e 20s a
75s e 90s.** È la patch che conta di più e quella che nel piano non
c'era: sopra la risoluzione LNURL della dev fee ci sono **due** timeout
esterni, uno da 15 secondi attorno a `resolv_ln_address` e uno da 20
attorno a tutto il blocco. La risoluzione sono due richieste HTTPS su
**due domini diversi** (`walletofsatoshi.com` per il `.well-known`,
`livingroomofsatoshi.com` per il callback), ognuna col suo circuito da
scaldare: 10,6 + 10,6 fa 21,2 secondi. Nessuno dei due cappelli era
raggiungibile a freddo, **e non lo era nemmeno prima delle nostre
modifiche**. Senza questa patch le altre due non curano la dev fee: i
30 secondi della 0001 restano invisibili dietro il 15 che taglia per
primo. I 75 devono superare due richieste da 30; i 90 devono restare
sopra i 75 o tornerebbero a decidere loro. Entrambi restano sotto i 5
minuti dopo i quali una prenotazione `PENDING` viene liberata.
I timeout attorno al **pagamento** via LND (50s, 25s, 10s, 5s) NON sono
toccati: il guasto osservato era `NoAPIResponse` in risoluzione, e
allargare cose che non c'entrano è il modo di rendere una patch
irricevibile a monte.

**0004 — `src/app/order.rs`, `take_buy.rs`, `take_sell.rs`: un prezzo
MAI visto risponde `PriceTooStale` invece di tacere.** Dalla 0.18.7 il
prezzo vive in una cache solo in RAM riempita dallo scheduler; finché
nessun prezzo è mai entrato (riavvio + provider giù, il 15 set 2026 per
tre ore) `get_bitcoin_price` torna `NoAPIResponse`, che ai tre confini
dell'ordine è un errore INTERNO: un WARN e nessuna risposta all'utente.
Un prezzo VECCHIO invece rispondeva già `PriceTooStale` come cant-do.
Per chi scambia i due casi sono uguali, quindi la risposta è la stessa;
il PriceManager e i suoi log non si toccano. Un test di `order.rs` che
fissava il vecchio comportamento è rinominato e ribaltato. Nasce da
`patch-0004-prezzo-mai-visto.py` (sostituzioni mirate, ancore uniche,
provate a secco sul sorgente del tag) e vive qui come `.patch` esportato
dal nodo; il client Barattolo dalla stessa sera legge `price_too_stale`
e dice «riprova fra poco, o pubblica a prezzo fisso».

**0005 — le commissioni PER PARTE: `src/barattolo_fee.rs` (nuovo) e sette
agganci in `main.rs`, `take_buy.rs`, `take_sell.rs`, `util.rs`,
`flow.rs`, `add_invoice.rs`.** IN SERVIZIO dal 18 set 2026 (immagine
`-bar3`, commit `3a7a121` sul nodo): compilata al primo colpo, e provata
con uno scambio vero — vedi PROVATO, qui sotto, con quel che ancora
manca. Con la 0007 è una delle due che NON vanno proposte a monte: è la
politica di prezzo di Barattolo, non un difetto di Mostro.
Chi è pioniere OPPURE ha il livello 5 su Barattolo paga mezzo punto in
meno sulla SUA metà della commissione, e lo sconto lo applica mostrod
alla fonte — hold invoice e payout nascono giusti, nessun rimborso dopo.
Upstream ha UNA colonna `order.fee` per tutt'e due le parti, e `Order`
sta in mostro-core, che non si forka. Quindi:
- `order.fee` diventa **la fee del COMPRATORE**: i suoi usi
  (`set_waiting_invoice_status`, `validate_invoice`, `do_payment`,
  `check_failure_retries`, i messaggi al compratore) restano intatti
  byte per byte;
- la fee del **VENDITORE** va in una tabella a lato, `barattolo_fees`,
  creata con `CREATE TABLE IF NOT EXISTS` e tenuta FUORI dalle
  migrazioni sqlx apposta (una migrazione upstream nuova non ci litiga
  mai), e si legge nei **TRE** posti dove upstream usa `order.fee` dal
  lato di chi vende. Il disegno ne aveva visto uno solo
  (`show_hold_invoice`); gli altri due — i messaggi `BuyerTookOrder` di
  `flow.rs` e `add_invoice.rs` — li ha trovati il censimento, e senza di
  loro il venditore si sarebbe sentito dire una cifra diversa da quella
  della sua hold. Il patcher quel censimento lo RIFÀ a ogni giro: se
  upstream aggiunge un quarto uso, si ferma.
- `order.rs` NON si tocca: alla pubblicazione chi prende non esiste, e
  la fee si riscrive alla presa, quando le due trade key sono note.

**CHI ha lo sconto non lo sa mostrod**: alla presa chiede a Barattolo
(`POST /api/p2p/sconto`, le due trade key in una richiesta sola, dietro
un segreto) e riceve un sì o un no per chiave. **QUANTO vale lo sa solo
mostrod** (`BARATTOLO_SCONTO_FEE`, col tetto cablato `MAX_DISCOUNT` =
1%): chi bucasse il VPS può al massimo regalare mezzo punto a qualcuno,
mai riscrivere una commissione.
**SE IL SERVER NON RISPONDE: FEE PIENA per tutt'e due** — timeout (12 s,
che è anche il massimo che un VPS morto può fermare il ciclo seriale
dei messaggi), non-200, JSON storto, chiave assente dalla risposta,
riga a lato che non si scrive. Ogni caso lascia UNA riga di log col
motivo. Un **battito ogni 60 s** verso `/api/salute` tiene calda la
connessione (la lezione della 0001: 10,6 s a circuito freddo), e parla
nel log solo quando lo stato CAMBIA.
**SENZA LE TRE VARIABILI D'AMBIENTE LA PATCH È INERTE**: nessuna
richiesta, nessuna riga scritta, `order.fee` com'era — upstream byte
per byte, ed è anche il rollback senza ricompilare. Le tre variabili
stanno nel compose del nodo, servizio `mostro`:
`BARATTOLO_SCONTO_FEE=0.005`, `BARATTOLO_SCONTO_URL=https://barattolo.store/api/p2p/sconto`,
`BARATTOLO_SCONTO_SEGRETO=<lo stesso di P2P_SCONTO_SEGRETO sul VPS>`.
⚠️ Il segreto è un segreto: mai nel canale Telegram del nodo, entra nel
backup age col resto del compose.
NON COPERTO, e dichiarato: la strada dei BOND (`[anti_abuse_bond]`, da
noi spenta) mette `order.fee` nel contesto di chi prende e può far
correre più prese sullo stesso ordine. Prima di accendere i bond questa
patch si rilegge.
Nasce da `patch-0005-fee-per-parte.py` (con `barattolo_fee.rs` accanto;
`--secco` prova le ancore senza scrivere) e vive qui come `.patch`
esportato dal nodo.

**0006 — `src/app/release.rs`: «has failed!» dice PERCHÉ.** In servizio
dal 18 set 2026 nella stessa `-bar3` (commit `4f20e04` sul nodo). Solo
log, nessun comportamento cambia. Quando il payout a chi compra
fallisce, upstream scrive «Invoice with hash: … has failed!» e basta —
ma quella riga nasce quando lo stream di `SendPaymentV2` consegna
`status = FAILED`, e nello STESSO messaggio LND dice il motivo
(`payment.failure_reason`: NO_ROUTE, INSUFFICIENT_BALANCE, TIMEOUT…),
che mostrod non leggeva in nessun punto. Il 17 set 2026 (scambio
`3fcdb207`, 14.837 sats fermi) ci ha fatto tirare a indovinare: era
NO_ROUTE per il tetto delle fee di rotta, trovato da `lncli` e non dal
log. Ora la riga porta il motivo (nome e codice grezzo) e quanti
tentativi HTLC sono partiti — zero vuol dire che LND non ha nemmeno
provato una strada. Nasce da `patch-0006-perche-e-fallito.py`. Questa
SÌ è da proporre a monte: è un difetto di diagnosi di chiunque.
⚠️ MAI VISTA PARLARE: compila e i test sono verdi, ma la riga esce solo
quando un payout fallisce, e dal 18 set non ne è fallito nessuno.

**0007 — gli EVENTI al server di Barattolo: `src/barattolo_eventi.rs`
(nuovo) e ventiquattro agganci in tredici file.** ⚠️ SCRITTA il 18 set
2026 e **MAI COMPILATA**: sul PC non c'è `cargo`, e il primo
`cargo build` è quello sul nodo. NON è in servizio, e in questa cartella
non c'è ancora il suo `.patch`: nasce dal nodo, a test verdi, come le
sorelle. Come la 0005 NON va proposta a monte: è l'integrazione di
Barattolo, non un difetto di Mostro.
IL PERCHÉ: il server di Barattolo deduceva cosa succede in uno scambio
dalle buste cifrate che non può leggere — da lì gli avvisi generici
«Novità in un tuo scambio» e, dal vivo il 18 set, avvisi a caso. mostrod
i fatti li SA. A ogni transizione di stato di un ordine fa un POST a
`BARATTOLO_EVENTI_URL`, sulla strada dello sconto: **lo stesso client
HTTP della 0005** (`barattolo_fee::http()`, che la patch rende
`pub(crate)`), quindi lo stesso pool di connessioni e lo stesso circuito
Tor che il battito da 60 s tiene caldo; segreto in header (bearer). Se
lo sconto non è configurato e il suo battito non gira, il modulo ne
avvia uno suo.
COSA ESCE, e nient'altro: l'id dell'ordine, l'azione, l'ora, le due
TRADE pubkey, chi ha fatto il gesto (`buyer` / `seller` / `mostro`), un
dettaglio-macchina breve e — SOLO su `released` e `success` — tre
importi in sats (l'ordine, il netto a chi compra, il totale bloccato da
chi vende: dopo la 0005 le due fee possono differire, e il server da
solo non li saprebbe al satoshi). **Mai fatture, preimage, hash, testi,
coordinate**: `event_of` è l'UNICO lettore di `Order` del modulo, un
dettaglio è ripulito a 40 caratteri di `[A-Za-z0-9_-]`, una chiave che
non sia 64 esadecimali esce `null` — e un test guarda che quei campi non
escano, azione per azione.
LE TREDICI AZIONI: `taken`, `hold-invoice-requested`,
`hold-invoice-paid`, `buyer-invoice-requested`, `buyer-invoice-added`,
`fiat-sent`, `released`, `success`, `cancel-requested`, `canceled`,
`expired`, `dispute-opened`, `payout-failed` (col motivo di LND, lo
stesso numero che la 0006 scrive nel log). Dodici erano nella richiesta;
`cancel-requested` — il primo passo dell'annullo d'accordo — l'ha
aggiunta il censimento: senza, all'altra parte non arriverebbe che le
si chiede di annullare.
I DETTAGLI sono un vocabolario CHIUSO (il blocco «THE DETAILS» nel
modulo), e non sono decorazione: mostrod fa certi passi A COPPIE nello
stesso istante — la presa E la richiesta di garanzia; la garanzia pagata
E la richiesta della fattura — con due POST indipendenti che arrivano
nell'ordine che capita. Il dettaglio dice quale ramo è passato, così il
server manda UN avviso per coppia invece di tirare a indovinare.
**FIRE-AND-FORGET, l'opposto del fail-closed della 0005**: `emit*` sono
funzioni SINCRONE che ritornano subito; il POST vive in un task suo, 8 s
di budget, poi UN solo retry dopo 5 s con 12 s (un circuito freddo ne
misura 10,6) — 25 s in tutto, sotto i 60 dopo i quali il server ripiega
sul libro pubblico. Un 4xx non si riprova (è un errore nostro). Nessun
gesto dello scambio aspetta mai: se il server è giù mostrod va avanti
come upstream. UNA riga di log per POST, con l'esito.
**SENZA `BARATTOLO_EVENTI_URL` LA PATCH È INERTE**: nessun task, nessuna
richiesta. Il segreto è `BARATTOLO_EVENTI_SEGRETO`; se manca vale
`BARATTOLO_SCONTO_SEGRETO`. Consigliato uno SUO — lo stesso di
`P2P_EVENTI_SEGRETO` sul VPS: quello dello sconto fa una domanda, questo
fa partire avvisi, e due porte si ruotano una alla volta.
DOVE SI AGGANCIA, in breve: `show_hold_invoice` e `update_order_status`
(la presa e quel che apre), `hold_invoice_paid`, `add_invoice_action` e
`pay_new_invoice`, `fiat_sent_action`, `release_action`,
`payment_success`, il ramo `Failed` del watcher di `do_payment`, i
quattro annulli di `cancel.rs` (d'accordo in due passi, di chi ha preso,
di chi ha pubblicato a presa in corso e in vetrina), i tre job dello
scheduler (presa non completata, garanzia a fine CLTV, ordine scaduto
nel libro), `dispute_action`, e le due chiusure del moderatore.
⚠️ DOVE UPSTREAM **MUOVE** `order` dentro un'altra funzione
(`add_invoice_action` → `show_hold_invoice`) l'aggancio tiene una COPIA
e avvisa solo a gesto riuscito; e l'annullo di chi aveva preso avvisa
PRIMA che `edit_pubkeys_order` gli cancelli le chiavi dall'ordine.
NON COPERTO, e dichiarato: la strada dei BOND (le prese in gara sullo
stesso ordine) e il ramo Cashu non hanno agganci; su questo nodo sono
spenti tutti e due.
Nasce da `patch-0007-eventi-al-server.py` (con `barattolo_eventi.rs`
accanto; `--secco` prova le ancore senza scrivere). Il patcher, oltre
alle ancore uniche, controlla tre cose che Rust non controlla perché
sono stringhe: che ogni azione mandata stia nell'elenco del modulo, che
ogni azione dell'elenco abbia un aggancio, che ogni dettaglio sia
dichiarato — e che nessun aggancio sia finito sotto `#[cfg(test)]`. I
fine-riga sono quelli del file che trova (un `barattolo_fee.rs` arrivato
in CRLF da un checkout Windows non fa cadere l'ancora).

## COSA CURA, E COSA NO

Il difetto ha due facce, e le patch le trattano in modo diverso.

- **Il trader col Lightning address** è curato dalla sola 0001.
  `is_valid_invoice` prova PRIMA l'indirizzo Lightning e l'LNURL, e
  solo dopo ripiega sulla bolt11: chi consegna un indirizzo finiva
  sullo stesso `lnurl_get` e si prendeva un `InvoiceInvalidError` in
  fase di VALIDAZIONE, senza che niente gli dicesse perché. Quella
  strada passa da `validate_lightning_address` e **non ha nessun
  cronometro esterno** (verificato).
- **La dev fee** ha bisogno anche della 0003, per i due cappelli
  annidati di cui sopra.

## IN SERVIZIO

Immagine `mostro:v0.18.7-bar3` dal 18 set 2026 (la `-bar2` con le prime
quattro patch e la `-bar1` con le prime tre sono restate sulla macchina,
come tag di rollback), costruita
sul nodo con `docker build -f docker/Dockerfile -t mostro:v0.18.7-bar3 .` dentro
`~/nodo/mostro-src`. Il `Dockerfile` fa `COPY . .`, cioè copia il
sorgente LOCALE e non lo riscarica: è la ragione per cui le patch
finiscono davvero nel binario, ed è la cosa da riverificare se un
domani quel file cambia.

**Un tag non si sovrascrive mai.** `mostro:v0.18.5` e `mostro:v0.18.6`
sono ancora sulla macchina, e il giorno che servisse una build nuova
prende un nome nuovo (`-bar4`). Un tag riusato è un rollback che non si
può fare.

Il compose passa alla versione nuova in **una riga** (la 64 di
`~/nodo/docker-compose.yml`), e quella riga è anche tutto il rollback:
rimessa a `v0.18.6` e rifatto l'`up -d`, si torna indietro. Copie di
sicurezza sul nodo: `docker-compose.yml.prima-bar1`.
La 0005 ha un gradino di rollback PRIMA di quello: tolte dal compose le
tre variabili `BARATTOLO_SCONTO_*` e rifatto l'`up -d`, la patch è
inerte senza cambiare immagine. La `fee` in `settings.toml` (0.03 dal
18 set 2026) si rimette a mano: è config, non patch.

⚠️ **`up -d`, non `restart`.** `docker compose restart mostro` riavvia
il container ESISTENTE, che resta quello costruito sull'immagine
vecchia: vedresti un riavvio pulito e crederesti di aver messo in
servizio il fork restando sulla 0.18.6. Cambiando immagine ci vuole
`docker compose up -d mostro`, che ricrea il container. Il `restart`
resta giusto quando cambia solo la configurazione.
Il servizio si chiama `mostro`, il container `nodo-mostro-1`: la prova
che gira il fork è
`docker inspect --format '{{.Config.Image}}' nodo-mostro-1`.

## LA MODIFICA AL CONFIG, che è un'ALTRA cosa

`dev_fee_percentage` in `[mostro]` di `~/nodo/mostro/settings.toml` è
stato messo a **`0.0`** (era `0.30`, riga 114; copia in
`settings.toml.prima-bar1`). Non sta nelle patch e non deve starci: le
patch rendono lo zero *dicibile*, il config decide di dirlo.

⚠️ **`0.0` e non `0`**: il campo è un `f64` e il TOML distingue interi
da decimali. Con `0` la deserializzazione fallisce («invalid type:
integer») e mostrod non parte affatto.

Vale per gli scambi **futuri**: la percentuale si consulta quando la
fee si CALCOLA, quindi non ripulisce una riga che ce l'ha già scritta.
E il giorno che si rimettesse il 30% senza le patch, il difetto
tornerebbe identico.

## PROVATO

- I tre commit sopra il tag, uno per file, nessun altro tocco:
  `git log --oneline v0.18.7..HEAD`.
- `cargo test` nello stadio `builder` dell'immagine, sui tre moduli
  toccati: **27 test in `lnurl`, 24 in `config::util`, 58 in
  `dev_fee`**, zero falliti. Compreso il test nuovo
  `dev_fee_zero_is_accepted_as_opt_out` e i due vecchi
  `dev_fee_below_minimum_is_rejected` e
  `dev_fee_above_maximum_is_rejected`, che sono la prova che allentando
  il minimo non si è aperto né il fondo né il tetto.
  ⚠️ Il `cargo build --release` del Dockerfile **non compila i test**:
  una build verde non dice niente su di loro, vanno lanciati a parte.
- La 0004: `market_priced_order_without_price_data_is_a_cant_do` verde
  nei test di `app::order`, `app::take_buy`, `app::take_sell` sul nodo.
- La 0005 e la 0006 (18 set 2026): build verde AL PRIMO COLPO — il Rust
  non era mai stato compilato, sul PC non c'è `cargo` — e **144 test
  verdi, zero falliti** nello stadio `builder`, coi cinque filtri
  `barattolo_fee app::take_buy app::take_sell flow app::add_invoice`.
  I test upstream dei due take non si sono accorti di niente, che è la
  prova di «a sconto spento, upstream byte per byte».
- LO SCAMBIO DI PROVA della 0005 (18 set 2026, ordine `4ed69365`, 7388
  sats, due pionieri): `discount true` per tutt'e due, fee **74 + 74**
  (1% a testa: `round(0.02 × 7388 / 2)`), hold **7462**, payout **7314**,
  37 sats di rotta. Al satoshi.
- In servizio: `inspect` dice `mostro:v0.18.7-bar3` (era `-bar2` fino al
  18 set 2026), log con
  «Settings correctly loaded!», prezzi pubblicati su Nostr.

**Quello che NON è provato**, ed è la parte onesta: che la dev fee ora
passi davvero a circuito freddo. Si prova solo al prossimo scambio
vero, senza scaldare il circuito prima — che è esattamente l'accidente
che il 7 settembre 2026 aveva fatto sembrare risolto un problema che
non lo era.
DELLA 0007 NON È PROVATO NIENTE SUL CAMPO, e sul PC nemmeno compilata:
verificate sul clone del tag (con le sei patch applicate) le ANCORE —
ventiquattro, tutte uniche, e il patcher rilanciato si ferma — e LETTE
le firme che ogni aggancio usa (il tipo di `order` in quel punto, se è
ancora vivo o già mosso, i campi di `Order` in mostro-core 0.14.6,
`failure_reason` come `i32`, `HoldInvoiceOrigin: PartialEq`). I test
Rust sono scritti — la forma del corpo, cosa non esce MAI, un server
HTTP di cartone per il retry (uno solo), il rifiuto non riprovato, il
server morto che è un `false` e non un blocco — e il loro primo giro è
`cargo test` sul nodo.
E DELLA 0005, tre cose: 1) **il caso fail-closed** — server muto o
segreto sbagliato, fee piena per tutt'e due e la riga `discount NOT
verified` nel log; 2) **il caso senza sconto** con la patch accesa;
3) e quella che conta di più: **lo scambio con UNO SOLO scontato**. Fra
due pionieri la fee di chi compra e quella di chi vende sono UGUALI,
quindi quello scambio non distingue `order.fee` dalla riga di
`barattolo_fees`: se i tre posti del venditore leggessero la colonna
sbagliata, il conto sarebbe tornato identico. La tabella a lato esiste
per il caso asimmetrico, e il caso asimmetrico dal vivo non c'è ancora.

## AGGIORNARE A UNA VERSIONE UPSTREAM NUOVA

```
cd ~/nodo/mostro-src
git fetch --tags
git switch -c barattolo/vX.Y.Z vX.Y.Z
git cherry-pick a9d387b 1d6652c 1d5f634 2b71308 3a7a121 4f20e04   # + il commit della 0007, quando c'è
docker build -f docker/Dockerfile -t mostro:vX.Y.Z-bar1 .
docker build -f docker/Dockerfile --target builder -t mostro-test:bar1 .
docker run --rm mostro-test:bar1 cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice
```

poi la riga dell'immagine nel compose e `docker compose up -d mostro`.
I filtri vanno TUTTI dopo `--`, in un colpo solo: la forma vecchia
(`sh -c "… && …"`) ha le virgolette annidate, e lanciata dal PC dentro
`ssh "…"` PowerShell non le fa passare.

**Un conflitto su `lnurl.rs` o su `dev_fee.rs` è la NOTIZIA BUONA**:
vuol dire che upstream ci ha messo mano, e la domanda diventa se la
nostra patch serve ancora invece di come riapplicarla.

## A MONTE

Le tre modifiche vanno proposte a `MostroP2P/mostro`. I messaggi di
commit sono scritti in inglese e contengono le misure apposta: sono
già la spiegazione della PR.

Da dire nell'issue, perché è la parte che upstream non sa: i due
cappelli da 15s e 20s rendono la risoluzione della dev fee
**impossibile** su circuito Tor freddo a prescindere dai budget LNURL —
e `docs/DEV_FEE.md` di upstream dice «LNURL: 15s» mentre il codice ha
tre budget da 4/2/2. Vale il codice; la discrepanza è parte della
segnalazione.
