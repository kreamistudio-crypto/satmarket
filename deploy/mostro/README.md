# IL FORK DI MOSTRO — otto patch sopra il tag v0.19.0

**Dal 1 ottobre 2026 (sera) i due moduli `.rs` sono cambiati** — cantiere
«CSP e le voci aperte degli audit», cura 9: in `barattolo_fee.rs`
l'interruttore della domanda dello sconto (3 fallimenti di fila → 60 s
di pausa) e il tetto di 64 KB alla risposta letta a pezzi; in
`barattolo_eventi.rs` via il ripiego sul segreto della 0005 (senza
`BARATTOLO_EVENTI_SEGRETO` gli eventi sono spenti). Le `.patch` 0005 e
0007 portano i moduli nuovi, e la 0008 il contesto spostato di
`barattolo_eventi.rs` (diff innestati nelle `.patch` di prima, stessi
header); le altre cinque sono byte per byte quelle del 30 set.
Verificato con `git am` su due cloni puliti: l'albero è quello degli
otto patcher. ⚠️ NON compilato sul PC: è il lavoro del prossimo giro
del nodo (`-bar7`). Il verbale sta in CANTIERI, «CSP e le voci aperte
degli audit — 9)».

**Dal 1 ottobre 2026 le patch sono OTTO**: la 0008 (la cauzione di chi
prende, solo per il metodo «Contanti») sta sopra la 0007 ed è stata
fatta sul PC come le sette del 30 set — patcher a `--secco` su un clone
pulito della `v0.19.0` con le sette applicate via `git am`, un commit,
`git format-patch`; e `git am` delle otto su un secondo clone dà l'albero
byte per byte uguale. Dove sotto si legge «sette» vale per le sette di
prima; la 0008 ha la sua voce in fondo a «LE SETTE PATCH» e la sua riga
nella tabella dei patcher. ⚠️ Nemmeno lei è stata compilata sul PC.

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

Fatto l'8 settembre 2026 sulla `v0.18.7` (commit `afc39a2`; sul nodo il
branch `barattolo/v0.18.7` porta i sette commit `a9d387b`, `1d6652c`,
`1d5f634`, `2b71308`, `3a7a121`, `4f20e04` e `9387493`, ed e' quel che
gira nella `-bar4`). **Dal 22 settembre 2026 le sette `.patch` qui accanto
stanno sopra la `v0.18.8`** (commit `e67676d`, uscita il 18 set): sono
state RIFATTE sul PC — ogni patch ha il suo patcher ad ancore uniche con
`--secco` (vedi «I SETTE PATCHER»), i sette patcher sono stati fatti
girare in fila su un clone pulito del tag, un commit per patch col
messaggio di prima, e `git format-patch` le ha esportate. Verificato in
due strade: le vecchie sette `.patch` entrano pulite sulla 0.18.8 con
`git am`, e l'albero che ne esce e' **byte per byte** quello dei
patcher — la sola differenza e' il ritocco alla 0007 (l'aggancio
pre-claim, sotto). Da sole ricostruiscono il fork: vedi «RICOSTRUIRE IL
FORK DA ZERO», in fondo. ⚠️ NIENTE E' STATO COMPILATO SUL PC (non c'e'
`cargo`): il primo `cargo build` della 0.18.8 col fork e' quello del
nodo, punto 4 della liturgia `-bar5` in PRODUZIONE.

**Dal 30 settembre 2026 le sette `.patch` stanno sopra la `v0.19.0`**
(commit `d53e41d`, uscita il 29 set), con la stessa ricetta del 22 set:
i sette patcher fatti girare in fila sul PC su un checkout PULITO del
tag (⚠️ con `-c core.autocrlf=false`: un checkout Windows esce in CRLF
e le ancore con `\n` non trovano niente — e' la trappola in cui e'
caduto il primo giro dello studio), un commit per patch col messaggio
di sempre, `git format-patch` a esportarle qui. La SOLA differenza dal
fork della 0.18.8 e' UNA PAROLA nell'ancora 11 della 0007: dalla
0.19.0 `release_action` chiude la disputa aperta come
`DisputeStatus::Released` e non piu' `Settled` (upstream `#967`, «chi
legge la disputa deve distinguere chi l'ha risolta»), e il patcher lo
dice. Le altre sei entrano con le ancore di prima, perche' i file che
toccano o non sono nel diff o cambiano altrove (`main.rs` aggiunge
solo `pub mod publish;`, `order.rs` il rifiuto del range a meta').
VERIFICATO IN DUE STRADE, come il 22 set: un secondo checkout del tag
con `git am` delle sette nuove da' l'albero **byte per byte** uguale a
quello dei patcher (diff vuoto). ⚠️ NIENTE E' STATO COMPILATO: il primo
`cargo` della 0.19.0 col fork e' quello del nodo, punto 4 della liturgia
`-bar6` in PRODUZIONE («LA SALITA A MOSTRO 0.19.0»). Finche' quella
liturgia non e' fatta IN SERVIZIO resta la `-bar5` sulla 0.18.8, e i
`.patch` di quella stanno nella storia di git (commit `d9f5ea1` e prima).

COSA CAMBIA DALLA 0.18.8 ALLA 0.19.0, letto sul diff (lo studio intero
sta in `docs/STUDIO-MOSTRO-0190-2026-09-30.md`): il gift wrap (protocollo
v1) non c'e' piu' e `transport = "gift-wrap"` rifiuta l'avvio
(`"nip44"` e' accettato, la riga assente vale nip44 — il nostro nodo
parla nip44 dal 6 set); NESSUNA migrazione nuova (15 file, gli stessi
della `-bar5`), quindi il rollback torna a essere la riga del compose;
mostro-core 0.14.6 → 0.16.0 (la restore torna la trade key della
controparte, la reputazione porta `since`, lo stato di disputa
`cooperatively-canceled`); `#992` il publish si risolve al PRIMO relay
che conferma (era ~10 s persi a evento con un relay muto); `published_at`
sul 38383 e sul 38386; `hold_invoice_expiration_window` deve essere > 0
(il nostro e' 300). Il resto sono bond, da noi spenti. Il client
Barattolo parla il v2 da sempre e non cambia lingua.

COSA CAMBIA DALLA 0.18.7 ALLA 0.18.8, letto sul diff: `#908` sposta la
contabilita' dei payout falliti in un punto solo (`do_payment` si spacca
in `do_payment` + `dispatch_payout`, e il nostro ramo `Failed` della 0006
e 0007 vive ora dentro `dispatch_payout`, con `order` clonato per il task);
`#825` valida l'iniziatore della disputa PRIMA del rimborso in
`admin_cancel` e `admin_settle` (i nostri due agganci stanno dopo, e non
si toccano); `#882` corregge gli stati terminali con il trattino in
`db.rs`, quindi la restore-session non riporta piu' gli ordini
`cooperatively-canceled` e `canceled-by-admin` (prima passavano per il
refuso); `#964` e due migrazioni nuove sono dei bond, da noi spenti;
`fedimint-tonic-lnd` sale alla 0.4.0 (lo stato `Initiated` di LND).
mostro-core resta **0.14.6**: la ricetta che il client ricalca non si e'
mossa.

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
NON COPERTO fino al 1 ott 2026, e dichiarato: la strada dei BOND
(`[anti_abuse_bond]`) mette `order.fee` nel contesto di chi prende e può
far correre più prese sullo stesso ordine. RILETTA per il cantiere della
cauzione: `apply_party_fees` gira a OGNI tentativo di presa e scrive UNA
riga per ordine (`INSERT OR REPLACE`), quindi con due prese in gara
l'ultima sovrascrive la riga del vincitore e al blocco `seller_fee` non
trova i suoi numeri e ripiega su `order.fee` — lo sconto dello 0,5%
perso o regalato, mai un flusso rotto. La cura sta nella 0008 (pezzo B):
al blocco della cauzione la riga si riscrive per il VINCITORE.
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
(nuovo) e venticinque agganci in tredici file.** IN SERVIZIO dal 19 set
2026 (immagine `-bar4`, commit `9387493` sul nodo): scritta il 18 sul
PC senza `cargo`, il suo primo `cargo build` è stato quello sul nodo, e
lo stesso giorno è stata collaudata a due telefoni. Il `.patch` è
arrivato in questa cartella il 22 set, esportato dal nodo il 19 con
`git format-patch`. Come la 0005 NON va proposta a monte: è
l'integrazione di Barattolo, non un difetto di Mostro.
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
IL VENTICINQUESIMO AGGANCIO E' DEL 22 SET 2026, con la 0.18.8: il
`payout-failed` PRIMA di arrivare a LND. Fino alla `-bar4` l'evento
partiva solo dal ramo `Failed` dello stream di `SendPaymentV2` — cioe'
quando LND aveva preso in carico il pagamento e l'aveva fallito lui;
un indirizzo Lightning che non si risolve, una fattura storta o
scaduta, LND irraggiungibile, restavano MUTI verso il server (era cosi'
anche sulla 0.18.7). Upstream `#908` li fa passare tutti dal ramo `Err`
di `do_payment`, quindi un aggancio solo li copre:
`emit_payout_failed_pre_claim(&order, &e)`, col dettaglio che nomina la
CLASSE del guasto (`INVOICE_INVALID`, `INVOICE_EXPIRED`,
`ADDRESS_UNRESOLVED`, `LND_UNREACHABLE`, `INVALID_PUBKEY`, `DB_ERROR`,
o `PRE_CLAIM` per il resto) e mai il testo dell'errore. Lo stream di LND
continua a mandare il SUO motivo (`NO_ROUTE`…). Il server riceve la
stessa azione con una parola in piu' nel vocabolario dei dettagli.
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
fa partire avvisi, e due porte si ruotano una alla volta. Le due
variabili stanno nel compose del nodo, sotto `environment:` del servizio
`mostro`, accanto alle tre della 0005:
`BARATTOLO_EVENTI_URL=https://barattolo.store/api/p2p/evento` e
`BARATTOLO_EVENTI_SEGRETO=<lo stesso di P2P_EVENTI_SEGRETO sul VPS>`.
⚠️ Anche questo segreto entra nel backup age col compose, e mai nel
canale Telegram del nodo.
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
NON COPERTO, e dichiarato: il ramo Cashu non ha agganci (spento). La
strada dei BOND dal 1 ott 2026 ce li ha, nella 0008: il ramo
`resume_take_after_bond` senza fattura (che scavalcava l'aggancio 5) e
l'evento `bond-slashed`; le prese in gara sullo stesso ordine restano
senza aggancio finché nessuna cauzione si blocca (l'ordine è ancora
`pending` per tutti), e la presa vera parte al blocco.
Nasce da `patch-0007-eventi-al-server.py` (con `barattolo_eventi.rs`
accanto; `--secco` prova le ancore senza scrivere). Il patcher, oltre
alle ancore uniche, controlla tre cose che Rust non controlla perché
sono stringhe: che ogni azione mandata stia nell'elenco del modulo, che
ogni azione dell'elenco abbia un aggancio, che ogni dettaglio sia
dichiarato — e che nessun aggancio sia finito sotto `#[cfg(test)]`. I
fine-riga sono quelli del file che trova (un `barattolo_fee.rs` arrivato
in CRLF da un checkout Windows non fa cadere l'ancora).

**0008 — LA CAUZIONE SOLO PER CERTI METODI DI PAGAMENTO** (1 ott 2026,
cantiere B, decisione di Andrea; `src/config/types.rs`, `src/app/bond/`
`flow.rs`, `mod.rs`, `slash.rs`, `take_buy.rs`, `take_sell.rs`,
`util.rs`, `nip33.rs`, `barattolo_eventi.rs`, `settings.tpl.toml`: 19
agganci in 10 file più due moduli di test in coda). Negli scambi in
CONTANTI di persona chi prende blocca una piccola cauzione
(l'`anti_abuse_bond` di mostrod: una seconda hold invoice) così chi non
si presenta la perde. Ma upstream la cauzione è TUTTO o NIENTE:
`taker_bond_required()` e `maker_bond_required()` non ricevono l'ordine,
e `payment_method` è una stringa che nessuno guarda. Quattro pezzi:
**A)** un campo `only_payment_methods = ["Contanti"]` in
`[anti_abuse_bond]` (serde default: assente o vuoto = ogni metodo, cioè
upstream), `bond_applies_to_order(&order)` che spezza
`order.payment_method` sulle virgole e confronta la PAROLA INTERA senza
maiuscole («Contanti al tabacchino 23.47» resta fuori, «Contanti,Revolut»
entra: chi prende può scegliere il contante, la stessa regola del tetto
nel client), i tre punti di chiamata (`take_buy`, `take_sell`,
`publish_order`) che passano da `*_required_for(&order)` — tutti già
dentro un `if bond_required` — e il tag `bond_only_payment_methods` nel
38385, che il client legge vivo come la fee. Se sbaglia, sbaglia in
CHIUSURA: nessuna cauzione, cioè il comportamento di ieri.
**B)** la rilettura della 0005 (sopra): al blocco `apply_party_fees` si
riesegue per il vincitore su una COPIA dell'ordine — l'ordine tiene i
numeri della sua riga della cauzione, contro cui la fattura di chi
compra è già stata validata.
**C)** il buco della 0007: un ordine sell preso senza fattura riparte da
`resume_take_after_bond` e non passa dal ramo di `take_sell` agganciato;
copiati lì `taken`/`invoice-next` e `buyer-invoice-requested`.
**D)** l'evento `bond-slashed` (la quattordicesima azione di
`barattolo_eventi.rs`, `ACTIONS` da 12 a 13 voci): da
`notify_bond_slashed`, che i tre posti dove la bruciatura è CONFERMATA
(timeout, admin-settle, admin-cancel) chiamano — col lato che l'ha persa
nel dettaglio (`buyer` | `seller`), `sats` = la cauzione, `sats_buyer` e
`sats_seller` = quanto riceve ognuno; senza, chi vince metà cauzione lo
saprebbe solo aprendo l'app entro quindici giorni. Le due literal
complete di `AntiAbuseBondSettings` nei test di `nip33.rs` ricevono il
campo nuovo (senza, i TEST non compilerebbero). I test: `payment_method_in`
su otto forme, i tre cancelli spenti senza config, il tag emesso solo
con una lista e la cauzione accesa, il toml con e senza chiave — nel
filtro del `cargo test` entrano `barattolo_bond` e
`toml_only_payment_methods`. Niente migrazioni: il rollback resta la
riga dell'immagine nel compose, più `enabled = false` (o il blocco
commentato) in `settings.toml`. ⚠️ Non compilata sul PC: le firme sono
state lette sul clone della v0.19.0 con le sette applicate, e il primo
`cargo` è quello del nodo, punto 4 della liturgia. Nasce da
`patch-0008-cauzione-solo-contanti.py` (`--secco` prova le ancore senza
scrivere; pretende la 0005 e la 0007 sotto; controlla che
`bond-slashed` sia entrata in `ACTIONS` e nel vocabolario dei dettagli,
e che nessun aggancio sia finito sotto `#[cfg(test)]`).

## GLI OTTO PATCHER

Dal 22 set 2026 OGNI patch ha il suo script accanto, tutti con la stessa
forma: si lanciano dalla radice di `mostro-src`, provano TUTTE le ancore
su copie in memoria (ognuna deve comparire UNA volta, o si fermano senza
scrivere niente), con `--secco` dicono quante ne hanno trovate e non
scrivono, senza `--secco` scrivono e dicono cosa fare dopo. I fine-riga
sono quelli del file che trovano. Se una patch e' gia' applicata si
fermano («porta gia' questa modifica»).

| patch | patcher | tocca |
|---|---|---|
| 0001 | `patch-0001-lnurl-tor-freddo.py` | `src/lnurl.rs`, 3 sostituzioni |
| 0002 | `patch-0002-dev-fee-zero.py` | `src/config/util.rs`, 2 (guardia + test) |
| 0003 | `patch-0003-dev-fee-cappelli.py` | `src/app/dev_fee.rs`, 3 |
| 0004 | `patch-0004-prezzo-mai-visto.py` | `order.rs`, `take_buy.rs`, `take_sell.rs`, 4 |
| 0005 | `patch-0005-fee-per-parte.py` + `barattolo_fee.rs` | 7 agganci in 6 file |
| 0006 | `patch-0006-perche-e-fallito.py` | `src/app/release.rs`, 1 |
| 0007 | `patch-0007-eventi-al-server.py` + `barattolo_eventi.rs` | 25 agganci in 13 file |
| 0008 | `patch-0008-cauzione-solo-contanti.py` | 20 agganci in 10 file (il ventesimo, 1 ott 2026, emenda il test della 0007 sugli importi), più i test in coda a `flow.rs` e `nip33.rs` (1 ott 2026) |

I primi tre sono nati il 22 set 2026 (fino ad allora quelle patch
esistevano solo come `.patch`, da ritocchi a mano sul nodo); la 0004 ha
avuto `--secco` lo stesso giorno (prima scriveva e basta, un file alla
volta). L'ordine e' quello: la 0007 pretende `src/barattolo_fee.rs`
della 0005, e si ferma se non c'e'; la 0008 pretende tutt'e due i
moduli, cioe' la 0005 E la 0007.

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

Immagine `mostro:v0.19.0-bar6` dal 1 ott 2026: le OTTO patch di questa
cartella sopra la `v0.19.0` (`d53e41d`), otto commit sul nodo sul branch
`barattolo/v0.19.0` (la 0001 è `e8b6b14`), 520 test `cargo` verdi nello
stadio `builder`, e la cauzione di chi prende accesa nel `settings.toml`
solo per «Contanti» (PRODUZIONE, «LA SALITA A MOSTRO 0.19.0, COM'È
ANDATA»). La `-bar5` resta sulla macchina come tag di rollback: con lei
va rimesso anche il `settings.toml` dalla copia `prima-bar6`, perché la
0.18.8 non conosce `only_payment_methods` e chiederebbe la cauzione su
ogni metodo. Sul nodo i patcher hanno morso due volte al primo `cargo`
(il tipo `Tag` e il test della 0007 sugli importi, tutt'e due nella
0008): le due correzioni stanno nei commit `482bbfc` e `beb01bd`, e la
lezione resta quella del 22 set — sul PC non c'è `cargo`, il primo build
è quello del nodo, e la liturgia prevede di tornare al commit della
patch prima, rimettere il solo patcher nuovo e rifare i test.

Fino al 1 ott 2026, immagine `mostro:v0.18.8-bar5` dal 22 set 2026: le sette patch di questa
cartella sopra la `v0.18.8`, commit sul nodo `8a5eef9..1489f38` (la
liturgia sta in PRODUZIONE, «LA SALITA A MOSTRO 0.18.8»); sul nodo 440
test `cargo` passati, 15 migrazioni nel database, e il primo scambio
Barattozon da 23,47 € (31.209 sats) riuscito lo stesso giorno. La
`-bar4` (0.18.7, con tutte e sette le patch di allora) resta sulla
macchina come tag di rollback, coi vincoli delle migrazioni detti sotto;
la `-bar3` con le prime sei, la `-bar2` con le prime quattro e la
`-bar1` con le prime tre sono restate anche loro. Costruita sul nodo con
`docker build -f docker/Dockerfile -t mostro:v0.18.8-bar5 .` dentro
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
inerte senza cambiare immagine. La 0007 ha lo stesso gradino: tolta
`BARATTOLO_EVENTI_URL` e rifatto l'`up -d`, nessun POST parte più (e
sul VPS, svuotato `P2P_EVENTI_SEGRETO`, il libro torna a parlare subito). La `fee` in `settings.toml` (0.03 dal
18 set 2026) si rimette a mano: è config, non patch.

⚠️ **IL ROLLBACK DALLA 0.18.8 ALLA 0.18.7 NON E' UNA RIGA SOLA.** La
0.18.8 porta due migrazioni nuove (`20260913120000_bond_payout_recipient`
e `20260914120000_bond_payout_recipient_repair`: una colonna in piu'
nella tabella `bonds`, e una riparazione che da noi non tocca niente) e
mostrod le applica al primo avvio, scrivendole in `_sqlx_migrations`.
Un binario 0.18.7 che riparte su quel database si FERMA:
`sqlx` rifiuta un database con una migrazione che il binario non
conosce (`VersionMissing`; `ignore_missing` non e' acceso). Quindi
tornare a `-bar4` vuol dire O ripristinare il database dal backup fatto
prima del deploy, O togliere a mano le due righe da `_sqlx_migrations`
(la colonna in piu' resta, ed e' innocua per il vecchio binario). La
sequenza sta in PRODUZIONE. Da `-bar6` (0.19.0) a `-bar5` (0.18.8)
invece resta la riga del compose: la 0.19.0 NON porta migrazioni, e
l'unico residuo e' una disputa chiusa dalle parti come
`cooperatively-canceled` (stato che mostro-core 0.14.6 non sa leggere):
si guarda PRIMA con la query in PRODUZIONE, «LA SALITA A MOSTRO 0.19.0».

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

- I sette commit sopra il tag, uno per patch, nessun altro tocco:
  `git log --oneline v0.18.7..HEAD` (i primi tre erano uno per file).
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

- LA 0.18.8 (22 set 2026, sul PC): le sette entrano pulite con `git am`
  sul tag; i sette patcher girano a secco e a scrittura su un clone
  pulito con TUTTE le ancore uniche; le due strade danno lo stesso
  albero byte per byte (prima del ritocco alla 0007); `git am` delle
  sette `.patch` nuove riproduce l'albero dei patcher. **NON compilato,
  NON testato in Rust**: il primo `cargo` e' quello del nodo — e sono
  quattro i punti da guardare per primi se si ferma: `&order` nel ramo
  `Failed` ora dentro `dispatch_payout` (upstream clona `order` per il
  task), `PaymentFailureReason` di `lnrpc` con `fedimint-tonic-lnd`
  0.4.0, i nomi delle varianti di `ServiceError` nel classificatore
  pre-claim, e `MostroError` nel `match` (via `mostro_core::prelude`).
- IN SERVIZIO DAL 22 SET 2026, lo stesso giorno: sul nodo i sette
  patcher hanno detto le uscite attese, `cargo test` nello stadio
  `builder` ha dato **440 passati, 0 falliti**, il database ha 15
  migrazioni (le due della 0.18.8 comprese), e il primo scambio
  Barattozon da **23,47 €** (31.209 sats) e' riuscito. I quattro punti
  «da guardare per primi» qui sopra hanno compilato: restano scritti
  per la prossima salita.

**Quello che NON è provato**, ed è la parte onesta: che la dev fee ora
passi davvero a circuito freddo. Si prova solo al prossimo scambio
vero, senza scaldare il circuito prima — che è esattamente l'accidente
che il 7 settembre 2026 aveva fatto sembrare risolto un problema che
non lo era.
LA 0007 È IN SERVIZIO DAL 19 SET 2026 (`-bar4`, commit `9387493` sul
nodo) E COLLAUDATA A DUE TELEFONI lo stesso giorno — vedi CANTIERI,
«Mostro è l'unica fonte degli avvisi P2P» e «La garanzia pagata la
sente anche chi vende», che è il ritocco nato da quel collaudo. Prima
del nodo, sul PC senza `cargo`, erano state verificate sul clone del
tag (con le sei patch applicate) le ANCORE — ventiquattro, tutte
uniche, e il patcher rilanciato si ferma — e LETTE le firme che ogni
aggancio usa (il tipo di `order` in quel punto, se è ancora vivo o già
mosso, i campi di `Order` in mostro-core 0.14.6, `failure_reason` come
`i32`, `HoldInvoiceOrigin: PartialEq`). I test Rust — la forma del
corpo, cosa non esce MAI, un server HTTP di cartone per il retry (uno
solo), il rifiuto non riprovato, il server morto che è un `false` e
non un blocco — avevano come primo giro lo stadio `builder` sul nodo,
punto 4 della liturgia in PRODUZIONE, e lì il 19 set 2026 hanno dato
**310 passati, 0 falliti** (il conto lo ha riferito Andrea il 22 set,
dal nodo). Con la build verde e il collaudo a due telefoni, è quel che
è a verbale.
IL `.PATCH` DELLA 0007 È ARRIVATO CON 760 CR DENTRO (22 set 2026), ed
è la stessa lezione del `.gitattributes`: `barattolo_eventi.rs` era
stato copiato sul nodo dal checkout Windows, in CRLF, e il commit
`9387493` l'ha preso così — quindi `git format-patch` l'ha esportato
con un CR in fondo a ognuna delle 760 righe del modulo (e solo a
quelle). Nel repo il file è LF: la patch è stata normalizzata a LF e
l'`index` del file nuovo riscritto sul blob LF (`e0b7e30`, quello di
questa cartella), e da lei il modulo esce **byte per byte identico** a
`barattolo_eventi.rs` qui accanto. Sul nodo il file resta CRLF: stesso
codice, blob diverso (`2e14403`). Da oggi `barattolo_eventi.rs` ha la
sua riga nel `.gitattributes`, come la sorella.
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

PRIMA sul PC, a secco, su un clone del tag nuovo: si fanno girare i
sette patcher in fila (`--secco`, poi senza, un commit per patch) —
un'ancora che compare zero o due volte e' la NOTIZIA BUONA: vuol dire
che upstream ci ha messo mano, e la domanda diventa se la nostra patch
serve ancora invece di come riapplicarla. Si guarda anche il diff
upstream sui file che le patch toccano (`git diff --stat vVECCHIA vNUOVA`
contro `git diff --stat vNUOVA HEAD`), che e' come il 22 set 2026 si e'
visto `#908` sotto la 0006 e 0007. Poi si esportano le `.patch` nuove
(`git format-patch vX.Y.Z..HEAD`) e si mettono qui, coi nomi di sempre.

POI sul nodo, la liturgia della `-bar5` in PRODUZIONE:

```
cd ~/nodo/mostro-src
git fetch --tags
git switch -c barattolo/vX.Y.Z vX.Y.Z
python3 ~/nodo/patch-barN/patch-0001-lnurl-tor-freddo.py --secco     # e cosi' per le sette, poi senza --secco, un commit ciascuna
docker build -f docker/Dockerfile --target builder -t mostro-test:barN .
docker run --rm mostro-test:barN cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice barattolo_eventi app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle publish spam_gate   # gli ultimi due dalla 0.19.0
docker build -f docker/Dockerfile -t mostro:vX.Y.Z-barN .
```

poi la riga dell'immagine nel compose e `docker compose up -d mostro`.
I filtri vanno TUTTI dopo `--`, in un colpo solo: la forma vecchia
(`sh -c "… && …"`) ha le virgolette annidate, e lanciata dal PC dentro
`ssh "…"` PowerShell non le fa passare. Anche `git am` delle sette
`.patch` funziona, ed e' la strada di «RICOSTRUIRE DA ZERO»: i patcher
sono quella che DICE dove un'ancora non regge piu'.

## RICOSTRUIRE IL FORK DA ZERO

È il caso per cui questa cartella esiste: il nodo sparito, o un nodo
nuovo. Non serve il branch del vecchio nodo: bastano il sorgente upstream e le
sette `.patch`, applicate in fila con `git am`. La sequenza e' stata
provata il 22 set 2026 su un clone pulito di `MostroP2P/mostro` a
`e67676d` (v0.18.8) e il 30 set 2026 a `d53e41d` (v0.19.0): le sette entrano una dopo l'altra senza un
conflitto, l'albero e' byte per byte quello dei sette patcher, e il
`barattolo_eventi.rs` che ne esce e' quello di questa cartella.

```
git clone https://github.com/MostroP2P/mostro.git ~/nodo/mostro-src
cd ~/nodo/mostro-src
git switch -c barattolo/v0.19.0 v0.19.0        # d53e41d
git am ~/nodo/patch-bar6/000[1-8]-*.patch      # le otto, copiate dal PC con scp
git log --oneline v0.19.0..HEAD                 # otto righe, la 0001 in fondo
docker build -f docker/Dockerfile --target builder -t mostro-test:bar6 .
docker run --rm mostro-test:bar6 cargo test --release -- lnurl config::util dev_fee app::order app::take_buy app::take_sell barattolo_fee flow app::add_invoice barattolo_eventi app::fiat_sent app::release app::cancel app::dispute scheduler app::admin_cancel app::admin_settle publish spam_gate barattolo_bond toml_only_payment_methods
docker build -f docker/Dockerfile -t mostro:v0.19.0-bar6 .
```

Poi la riga dell'immagine nel compose, le cinque variabili d'ambiente
(tre della 0005, due della 0007: i valori stanno nel backup age, non
qui) e `docker compose up -d mostro`.

Tre cose da sapere prima di fidarsi del risultato:
- **gli hash cambiano**: `git am` ricommitta, quindi i sette commit
  nuovi NON si chiameranno come quelli del nodo. Il contenuto si': e'
  quello dei `.patch`, che dal 22 set 2026 sono l'esportazione dei
  sette patcher sulla 0.19.0 fatta sul PC il 30 set 2026 (dal 22 set
  lo erano sulla 0.18.8; fino ad allora erano l'esportazione dal nodo:
  sulla 0.18.7 le due cose coincidevano).
- **le `.patch` vanno sul nodo in LF**, com'è nel repo: il
  `.gitattributes` di questa cartella (`*.patch -text`) le tiene così
  anche su un checkout Windows, ma se passano da un editor o da uno
  strumento che «aggiusta» i fine-riga, `git am` fallisce sui contesti.
  Lo stesso vale per i due `.rs` accanto, che hanno `eol=lf` per la
  stessa ragione.
- **`git am` vuole un nome**: su una macchina nuova
  `git config user.name` e `user.email` prima, o si ferma.

Le tre modifiche vanno proposte a `MostroP2P/mostro`. I messaggi di
commit sono scritti in inglese e contengono le misure apposta: sono
già la spiegazione della PR.

Da dire nell'issue, perché è la parte che upstream non sa: i due
cappelli da 15s e 20s rendono la risoluzione della dev fee
**impossibile** su circuito Tor freddo a prescindere dai budget LNURL —
e `docs/DEV_FEE.md` di upstream dice «LNURL: 15s» mentre il codice ha
tre budget da 4/2/2. Vale il codice; la discrepanza è parte della
segnalazione.
