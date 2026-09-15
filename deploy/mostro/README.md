# IL FORK DI MOSTRO — tre patch sopra il tag v0.18.7

Qui dentro non c'è codice: ci sono le tre patch che il nodo Mostro di
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

## LE TRE PATCH, cosa fanno e perché

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

Immagine `mostro:v0.18.7-bar1`, costruita sul nodo con
`docker build -f docker/Dockerfile -t mostro:v0.18.7-bar1 .` dentro
`~/nodo/mostro-src`. Il `Dockerfile` fa `COPY . .`, cioè copia il
sorgente LOCALE e non lo riscarica: è la ragione per cui le patch
finiscono davvero nel binario, ed è la cosa da riverificare se un
domani quel file cambia.

**Un tag non si sovrascrive mai.** `mostro:v0.18.5` e `mostro:v0.18.6`
sono ancora sulla macchina, e il giorno che servisse una `-bar2` prende
un nome nuovo. Un tag riusato è un rollback che non si può fare.

Il compose passa alla versione nuova in **una riga** (la 64 di
`~/nodo/docker-compose.yml`), e quella riga è anche tutto il rollback:
rimessa a `v0.18.6` e rifatto l'`up -d`, si torna indietro. Copie di
sicurezza sul nodo: `docker-compose.yml.prima-bar1`.

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
- In servizio: `inspect` dice `mostro:v0.18.7-bar1`, log con
  «Settings correctly loaded!», prezzi pubblicati su Nostr.

**Quello che NON è provato**, ed è la parte onesta: che la dev fee ora
passi davvero a circuito freddo. Si prova solo al prossimo scambio
vero, senza scaldare il circuito prima — che è esattamente l'accidente
che il 7 settembre 2026 aveva fatto sembrare risolto un problema che
non lo era.

## AGGIORNARE A UNA VERSIONE UPSTREAM NUOVA

```
cd ~/nodo/mostro-src
git fetch --tags
git switch -c barattolo/vX.Y.Z vX.Y.Z
git cherry-pick a9d387b 1d6652c 1d5f634
docker build -f docker/Dockerfile -t mostro:vX.Y.Z-bar1 .
docker build -f docker/Dockerfile --target builder -t mostro-test:bar1 .
docker run --rm mostro-test:bar1 sh -c "cargo test --release lnurl && cargo test --release config::util && cargo test --release dev_fee"
```

poi la riga dell'immagine nel compose e `docker compose up -d mostro`.

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
