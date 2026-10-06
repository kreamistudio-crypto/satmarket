# Le statistiche di instradamento del nodo (5 ott 2026)

Studio, nessuna modifica: né al codice né al nodo. Domanda di Andrea:
verso chi e da quali canali paghiamo, da dove entrano i compratori, dove
falliscono i payout, come bilanciare ACINQ e LNBiG, e se conviene un
canale con un altro nodo. I dati li ha letti Andrea sul nodo (LND,
`listchannels`, `listpayments`, `listinvoices`, `fwdinghistory`,
`describegraph`, `querymc`) e sul VPS (`payout_passi`, `payout_tentati`,
gli indirizzi Lightning per dominio), con comandi di sola lettura dati
uno alla volta. Le chiavi pubbliche qui stanno per le prime otto cifre
(un esadecimale da 64 fa rossa la CI). Prosegue lo studio della
liquidità (`STUDIO-LIQUIDITA-NODO-2026-10-01.md`, §9).

## In breve

- I payout veri sono pochi e vanno bene: 38 pagamenti per 965.795 sats
  in cinque settimane, tutti usciti dai canali ACINQ, 1.703 sats di
  commissioni. Il 91 % di quelle commissioni va verso UNA destinazione:
  il punto di ricezione dei wallet su Spark, cioè (per esclusione)
  Wallet of Satoshi, il wallet dei venditori.
- I sette decimi di quel che è uscito dal nodo (6,37M su 7,34M) sono
  manovre nostre: swap, la spinta verso Blixt, il #152.
- I compratori sono entrati 62 volte su 63 da ACINQ — ma fino al 5 ott
  c'era solo ACINQ: la misura vera comincia adesso.
- Il 5 ott qualcuno ha usato il nodo come ponte ACINQ → LNBiG per
  630.529 sats (21 inoltri, 94,8 sats guadagnati), anche dopo il rialzo
  a 500 ppm. Ha consumato l'entrata ACINQ, quella di Phoenix.
- Consigli: tariffa alta sul SOLO canale LNBiG; un giro su noi stessi
  da ~350.000 fuori dal canale ACINQ da 400k; nessun canale con Spark
  adesso; i 12 falliti si lasciano dove sono.

## 1. I canali la sera del 5 ott (misurati)

| Canale | Capacità | Noi | Loro | Uscita utile | Entrata utile |
|---|---|---|---|---|---|
| LNBiG [Hub-2] | 5.000.000 | 53.119 | 4.945.904 | ~3.100 | ~4.895.900 |
| ACINQ 400k | 400.000 | 395.024 | 4.000 | ~391.000 | 0 |
| ACINQ 1M | 1.000.000 | 583.209 | 415.794 | ~573.200 | ~405.800 |
| **Totale** | | **1.031.352** | | **~967.300** | **~5.301.700** |

«Utile» = tolta la riserva del canale (50.000, 4.000 e 10.000 per lato).
L'entrata da ACINQ è **~405.800**, tutta sul canale da 1M: il 400k è
tutto dalla nostra parte e non riceve niente.

## 2. Verso chi paghiamo

70 pagamenti riusciti dal 1 set al 5 ott, 7.337.879 sats, 5.185 di
commissioni, tre salti in media.

| Destinazione | Cos'è | n | sats | Comm. media | ppm |
|---|---|---|---|---|---|
| `02b06bf3` SatsRouting2 | gli swap (manovra nostra) | 10 | 5.234.696 | 200,3 | 383 |
| `03072348`, privato dietro Blixt | la spinta di set (manovra nostra) | 20 | 889.659 | 67,7 | 1.522 |
| `030936e7`, privato dietro Spark | **payout: WoS e i wallet su Spark** | 23 | 447.956 | 67,1 | 3.443 |
| `027cf03b` GREENARTIST | il pagamento del #152 | 1 | 247.707 | 124,6 | 503 |
| `03c181e1` Swiss Bitcoin Pay | payout (`sbpc.ch`, torna al sats col VPS) | 3 | 155.920 | 37,3 | 718 |
| cinque privati dietro ACINQ | payout verso Phoenix | 12 | 361.919 | 4,0 | 133 |
| `0324ba23` kappa | una prova | 1 | 22 | 1,0 | — |

**I payout veri**: 38 pagamenti, 965.795 sats, 1.703 di commissioni
(1.764 ppm in media). Phoenix costa quasi niente (è un cliente dello
stesso nodo a cui siamo attaccati); Spark costa 1.543 sats su 447.956.

**Chi è `030936e7`.** In fattura indica come porte `039174f8` e
`02a98e8c`: sono i due nodi di instradamento di Spark, pubblicati con
le stesse chiavi e gli stessi indirizzi nella documentazione di Spark
(«connect to our routing nodes»). Che dietro ci sia Wallet of Satoshi è
una DEDUZIONE per esclusione, non una lettura: la cassaforte «nodo» ha
pagato 8 volte indirizzi `walletofsatoshi.com` di 5 venditori diversi, e
fra le destinazioni viste da LND non c'è un'altra casella dove possano
stare. Quindi `030936e7` non è un venditore: è il punto di ricezione
comune di chi sta su Spark. I 23 pagamenti non tornano al sats con gli 8
del mercatino perché dallo stesso LND paga anche mostrod (il P2P).

**Il primo salto** (per pezzo): ACINQ 400k 34 pezzi, 746.247 sats,
1.851 ppm; ACINQ 1M 30 pezzi, 2.146.632, 1.127 ppm; LNBiG 6 pezzi,
4.445.000, 312 ppm — solo gli swap. Nessun payout è mai uscito da
LNBiG: il canale è nato il 5 ott e la sua uscita è andata tutta negli
swap. Quanto costerebbe Spark passando da LNBiG NON è misurato (§8).

## 3. Da dove entrano i compratori

105 fatture, 61 incassate (07/09–05/10) per 1.977.270 sats, 44 annullate
(depositi mai pagati e garanzie P2P scadute: è il loro corso). Tre
pagate in più pezzi.

| Canale d'arrivo | Fatture | sats | <10k | 10-50k | 50-200k | Pezzo massimo |
|---|---|---|---|---|---|---|
| ACINQ 400k | 40 | 743.628 | 22 | 14 | 4 | 130.000 |
| ACINQ 1M | 22 | 1.102.622 | 3 | 10 | 10 | 130.000 |
| LNBiG | 1 | 131.017 | 0 | 0 | 1 | 131.017 |

Ultimi sette giorni: 850.145 sats (ACINQ 719.128, LNBiG 131.017); dentro
ci sono i 265.000 dello sweep del 1 ott, che è nostro.

**Cosa NON dice questa tabella.** Chi riceve su Lightning non vede chi
paga, solo il canale d'arrivo. E fino al 5 ott i canali erano solo
ACINQ: «62 su 63 da ACINQ» non dice quanti compratori usano Phoenix.
Di certo c'è un fatto (l'acquisto da Phoenix da 56.459 fallito con
~29.000 di entrata ACINQ: Phoenix entra SOLO da lì) e un indizio dal
VPS, gli indirizzi Lightning salvati nei profili (63):
`walletofsatoshi.com` 28, `sats.mobi` 7, `primal.net` 6,
`blitzwalletapp.com` 4, `getalby.com`, `coinos.io` e `bitbox.cash` 3,
`sbpc.ch` 2, altri sette domini 1. Chi usa Phoenix di solito non ha un
indirizzo e incolla la fattura: sul nodo sono 5 destinazioni e 12
payout. La quota vera per canale si legge rifacendo questa tabella fra
due settimane (appendice).

**I payout per wallet** (ordini `released`, dal VPS; saas + nodo):
`walletofsatoshi.com` 29 ordini di 11 + 5 venditori, 863.746 sats;
senza indirizzo 12; `sbpc.ch` 8; `bitbox.cash` 6; `blitzwalletapp.com`
e `primal.net` 5; `blink.sv` 4; `getalby.com` 3; `sats.mobi` 2.

## 4. Gli inoltri: il ponte ACINQ → LNBiG

21 inoltri, tutti il 5 ott, tutti ACINQ 1M → LNBiG: 630.529 sats, 94,8
di guadagno, pezzo massimo 92.653. Quindici alle 17:11 UTC a ~1 sat
(483.853, quelli dello studio della liquidità); sei alle 19:29, DOPO il
rialzo a 1 sat + 500 ppm (146.676 sats, ~80 di guadagno).

I conti tornano da tre lati: LNBiG ha «inviati» 5.076.921 = 4.445.000
di swap + ~1.400 di commissioni + ~630.500; ACINQ 1M ha «ricevuti»
1.733.256 = 1.102.622 di fatture + 630.634.

Cosa ha fatto il ponte: ha tolto 630.529 all'entrata ACINQ (quella di
Phoenix) e alla nostra uscita su LNBiG, e li ha messi dalla nostra
parte su ACINQ. Adesso è fermo da solo: su LNBiG restano ~3.100 di
uscita utile. Riparte il giorno che lì torna dell'uscita.

Chi sia non si sa (`fwdinghistory` dice i canali, non mittente e
destinatario). Che continui a 500 ppm dice che quella strada a qualcuno
serve.

## 5. Dove falliscono i pagamenti

82 pagamenti in tutto: 70 riusciti, 12 falliti, nessuno in volo. Sul
VPS nessun payout aperto.

| Quando | Verso | Importo | Motivo | Cos'era |
|---|---|---|---|---|
| 01/09 | SatsRouting2 | 50.000 | NO_ROUTE | prova, nostra |
| 15/09, sei in 40 minuti | privato dietro Blixt (porta `0230a5bc`) | 100-300.000 | 2 TIMEOUT, 4 NO_ROUTE | la spinta verso Blixt, nostra |
| 17/09, tre | `030936e7` (Spark) | 14.837 | NO_ROUTE | **payout** |
| 23/09 | privato dietro ACINQ (Phoenix) | 6.617 | NO_ROUTE | **payout**, poi riuscito |
| 05/10 | SatsRouting2 | 588.920 | TIMEOUT | il sesto swap in un pezzo, nostro |

Otto su dodici sono manovre nostre di liquidità, e confermano una
lezione già scritta: verso un wallet mobile o un nodo piccolo i pezzi
grossi non passano. I payout veri falliti sono quattro tentativi, tutti
piccoli e tutti NO_ROUTE, cioè LND non ha trovato una strada SULLA CARTA
e non è partito niente. Il 17 set veniva due giorni dopo la raffica
verso Blixt: è plausibile (non provato) che fosse la memoria delle
strade avvelenata da quei fallimenti, la stessa che ha chiesto il
`resetmc`. Il 1 ott un 14.837 è uscito verso un Phoenix: se è lo stesso
payout lo dice solo il VPS.

**Il punto esatto della rottura non si legge più.** Nei 12 falliti LND
non conserva nessun tentativo (nemmeno i due HTLC in MPP_TIMEOUT del
sesto swap, visti in diretta): a pagamento chiuso li cancella. L'opzione
che li tiene si chiama `keep-failed-payment-attempts` ed è spenta per
default; va verificata su `lnd.conf` prima di parlarne (§7).

**La memoria delle strade** (`querymc`, 61 coppie) non mostra nessun
«no» sull'ultimo tratto Spark → destinazione: i «no» stanno sul tratto
PRIMA di Spark (tre nodi intermedi dopo ACINQ il 30/09, due il 05/10),
poi una strada si trova. Verso Spark, da ACINQ, si arriva a tentativi.

## 6. Quanta entrata e quanta uscita, e dove

Il mercatino su ACINQ si bilancia da solo: un deposito entra (entrata
ACINQ giù), il suo payout esce da ACINQ (entrata ACINQ su). Quel che
sbilancia è il resto: i sats NOSTRI fermi dalla nostra parte su ACINQ,
che occupano posto all'entrata di Phoenix, e il ponte.

Dalla nostra parte ci sono 1.031.352 sats. La Cassaforte ne deve ai
venditori 609.880 (dato del 5 ott, dallo studio della liquidità, non
riletto qui); il resto, ~421.000, è nostro (riserve 64.000 e i 40.452
di Alan compresi). Oggi stanno quasi tutti su ACINQ.

**Dove dovrebbero stare:**

| | Entrata utile | Uscita utile | Perché |
|---|---|---|---|
| ACINQ (due canali, 1,4M) | **mai sotto 630.000**; a riposo ~750.000 | quanto la Cassaforte deve (~610.000) | 630.000 = l'ordine P2P più grosso (`max_order_amount` 500.000) più il pezzo più grosso visto al mercatino (130.000) |
| LNBiG (5M) | il serbatoio: ~4,5M | **~350.000**: i sats nostri | l'entrata lì abbonda; l'uscita serve a provare i payout verso Spark da quel lato |

Oggi: entrata ACINQ ~405.800 (sotto il pavimento), uscita LNBiG ~3.100.

**Il ribilanciamento.** Un giro su noi stessi da **350.000**: fuori dal
canale ACINQ da 400k, dentro da LNBiG. È la ricetta che la ronda della
liquidità già scrive nell'allarme (Cantieri, «Avvisi sui pagamenti che
non arrivano»): `addinvoice`, poi `payinvoice --allow_self_payment
--outgoing_chan_id <ACINQ 400k> --last_hop <LNBiG>` con
`--macaroontimeout 300`. Due differenze dalla ricetta:
- dal canale da **400k** e non da quello con più uscita: è tutto dalla
  nostra parte e non riceve; dopo, ricevono tutti e due;
- in **due pezzi da 175.000**, sotto il tetto dei 300.000.

Dopo (calcolato): ACINQ entrata ~755.800 e uscita ~614.200; LNBiG
uscita ~353.100 ed entrata ~4.545.900.

Il costo: non misurato. Da ACINQ abbiamo pagato fra 133 ppm (Phoenix) e
~700 ppm (SatsRouting2 il 5 ott): stima **100-350 sats**, tetto della
ronda al 3 per mille = **1.050 sats** (`--fee_limit 525` a pezzo). È
una scrittura, e non è mai stata provata sul nostro LND: si fa con
Andrea al comando, un pezzo, si guarda, poi l'altro.

Non è urgente come sembra: i payout in attesa, uscendo da ACINQ,
rialzano l'entrata da soli. Ma dipendono dai tempi degli ordini, e il
lancio del P2P è il 10 ott.

**La soglia della ronda.** `SOGLIA_ACINQ` è 150.000: suona tardi per un
ordine P2P da 500.000 pagato da Phoenix. Da valutare se portarla a
300.000 (decisione di Andrea; è una leva da fuori).

## 7. Le tariffe, il canale con Spark, i falliti

**La tariffa contro il ponte.** Su un inoltro si paga la tariffa del
canale da cui ESCE: alzarla sul solo canale LNBiG colpisce esattamente
ACINQ → LNBiG e niente altro (i nostri pagamenti non pagano la nostra
tariffa). Proposta: **LNBiG a 1 sat + 2.500 ppm**, `time_lock_delta` 80
com'è. Perché 2.500: deve stare ben sopra il costo di rifare il giro
all'indietro (≤ 1.000 ppm). Se il ponte smette, l'entrata ACINQ resta
dov'è; se continua, ogni 100.000 che sposta ne rende 250 e ne costa al
più 100 a rimetterli a posto.
`lncli updatechanpolicy --base_fee_msat 1000 --fee_rate_ppm 2500
--time_lock_delta 80 --chan_point <quello di LNBiG, da listchannels>`:
una scrittura, la decide Andrea.

Secondo passo, SOLO dopo una settimana di misura e non insieme: i due
canali ACINQ a 500 ppm frenano anche il verso buono, LNBiG → ACINQ, che
è il nostro ribilanciamento fatto da altri e pagato a noi. Riportarli
bassi (1 sat + 100 ppm) rovescerebbe in parte la decisione del 5 ott:
quella nasceva dal ponte, che la tariffa ACINQ non tocca. Rischio: un
flusso forte svuoterebbe la nostra uscita su ACINQ, quella dei payout
a Phoenix. Per questo è un secondo passo.

**Un canale con Spark: non adesso.**
- Il risparmio: verso Spark abbiamo speso 1.543 sats in cinque
  settimane. Un canale costa apertura e chiusura on-chain e capitale
  fermo; LND 0.19 non ha lo splicing.
- Sarebbe a senso unico (solo payout): si svuota. A 448.000 al mese un
  canale da 500.000 dura un mese, e riempirlo vuol dire un giro che
  paga le stesse commissioni che si volevano evitare, o un canale
  nuovo.
- Non è detto che i 3.443 ppm siano il costo di ARRIVARE a Spark: una
  parte può essere dell'ultimo tratto, che il canale non toglie.
- Spark annuncia solo indirizzi in chiaro; noi usciamo da Tor. WoS
  rifiuta i peer dagli exit, ACINQ li accetta: Spark non è provato.
- Prima c'è una prova gratuita: `039174f8` ha il suo canale più largo
  (4,05 BTC, da 1ml) con LNBiG [Hub-3], noi siamo su Hub-2. Dopo il
  ribilanciamento LND avrà dell'uscita su LNBiG e sceglierà da solo.

Si riapre se i payout verso Spark passano i ~3M al mese o le
commissioni verso Spark i ~10.000 sats al mese, e se da LNBiG non
costano meno.

**I 12 falliti: si lasciano.** Un pagamento FAILED non ha mosso un
sats e non ne muoverà: non c'è niente da recuperare né da ripagare.
Non si cancellano (`deletepayments`): sono l'unica traccia rimasta, e
la ronda dei pagamenti li conosce. I quattro payout veri sono chiusi
(sul VPS nessun payout aperto). L'unica cosa da valutare è accendere
`keep-failed-payment-attempts` al prossimo riavvio GIÀ previsto di LND
(mai un riavvio apposta), per sapere la prossima volta DOVE si rompe
una strada.

## 8. Cosa resta da guardare

- Quanto costa Spark da LNBiG: dopo il ribilanciamento, rifare il
  comando 2 e leggere il primo salto dei pagamenti verso `030936e7`.
- La quota vera dei compratori per canale: rifare il comando 4 fra due
  settimane, ora che LNBiG c'è.
- Se il ponte riparte quando LNBiG ha di nuovo uscita, e a che prezzo:
  il comando 5.
- Che `030936e7` sia WoS: deduzione. La prova è leggere la destinazione
  di una fattura chiesta a un indirizzo `walletofsatoshi.com`.
- La Cassaforte a 609.880 è il dato del 5 ott: va riletta prima del
  ribilanciamento. (Riletta il 6 ott: 1.066.724, §9.)
- NON provati: il giro su noi stessi sul nostro LND, un `connect`
  verso Spark da un exit Tor. (La tariffa a 2.500 ppm è stata messa il
  6 ott, §9: resta da misurare se il ponte si ferma.)

## 9. Cosa è stato fatto il 6 ott

I comandi li ho scritti io, uno alla volta; li ha eseguiti Andrea.

**La tariffa: fatta.** `updatechanpolicy` sul solo `chan_point` di
LNBiG, `failed_updates []`. Riletta: LNBiG 1 sat + **2.500 ppm**, i due
ACINQ 1 sat + 500 ppm, `cltv` 80 su tutti e tre (la politica NOSTRA,
da `getchaninfo`). Il residuo del vecchio Magma compare ancora nel
`feereport` a 1 ppm: è chiuso (`closedchannels`, letto il 5 ott).

**Il giro: NON fatto, per decisione di Andrea.** I numeri del 6 ott:

| Canale | Uscita utile | Entrata utile |
|---|---|---|
| LNBiG | 71.703 | 4.827.352 |
| ACINQ 400k | 391.056 | 0 |
| ACINQ 1M | 774.179 | 204.876 |

La Cassaforte nodo era a **1.066.724**, non più a 609.880. Il debito
verso i venditori è il saldo meno il margine nostro misurato il 1 ott
(12.475), cioè ~1.054.249; più i 40.452 di Alan fa 1.094.701 da coprire
con l'uscita ACINQ (1.165.235). Margine 70.534: al più un giro da
65.000, non da 350.000. Il capitale di `capitale_cassa.py` (277.200)
non allarga il conto: 265.000 sono lo sweep del #152, già uscito col
suo payout. L'entrata ACINQ torna coi payout degli ordini aperti; per
allargarla davvero serve un canale ACINQ nuovo con sats freschi (da
studiare quando servirà). Lezione per il §6: la ricetta dei 350.000
valeva per la Cassaforte di quel giorno; un giro si calcola sempre sulla
Cassaforte riletta.

**La ronda: soglia ACINQ a 300.000, copertura, guardia oraria.** Il
codice e il perché stanno in CANTIERI («La guardia oraria dell'entrata
ACINQ e la copertura della Cassaforte»), la procedura in PRODUZIONE.
Installazione e prova a vuoto sul nodo: verbale qui sotto quando fatte.

**Il backup del 6 ott: provato in parte.** Lo SCB vivo
(`/home/debian/nodo/lnd/data/chain/bitcoin/mainnet/channel.backup`,
2.027 byte) ha i tre canali, LNBiG compreso, ed è stato scritto il 5 ott
alle 16:50 UTC, prima del backup delle 03:30. Il journal dice «backup
ok» alle 03:30:15. `nodo-20261006-0330.tgz.age` (31.003.274 byte) è
arrivato sul PC alle 05:30 ora italiana; `storico.log` dice ok. NON
confrontata l'impronta dello SCB dentro l'archivio: Andrea non mette la
chiave age del nodo in un file sul PC, e si fa alla prossima prova di
ripristino completa.

## Appendice: i comandi per rimisurare

Tutti di sola lettura, da `~/nodo` sul nodo. `N` è la mappa dei canali:
`{"1066579055655714817":"LNBiG","1063354188044304385":"ACINQ 1M","1061107885743538177":"ACINQ 400k"}`.

**1, i canali:**
```bash
cd ~/nodo && docker compose exec -T lnd lncli listchannels | python3 -c 'import json,sys; [print(c["chan_id"], c["remote_pubkey"][:8], "cap", c["capacity"], "noi", c["local_balance"], "loro", c["remote_balance"], "inviati", c["total_satoshis_sent"], "ricevuti", c["total_satoshis_received"]) for c in json.load(sys.stdin)["channels"]]'
```

**2, destinazioni e primo salto dei riusciti:**
```bash
cd ~/nodo && docker compose exec -T lnd lncli listpayments | python3 -c '
import json,sys,collections
D=collections.defaultdict(lambda:[0,0,0]); H=collections.defaultdict(lambda:[0,0,0])
for p in json.load(sys.stdin)["payments"]:
    ok=[h for h in p["htlcs"] if h["status"]=="SUCCEEDED"]
    if p["status"]!="SUCCEEDED" or not ok: continue
    d=D[ok[0]["route"]["hops"][-1]["pub_key"][:8]]; d[0]+=1; d[1]+=int(p["value_sat"]); d[2]+=int(p["fee_msat"])
    for h in ok:
        r=h["route"]; f=int(r["total_fees_msat"]); a=H[r["hops"][-1]["pub_key"][:8]+" da "+r["hops"][0]["chan_id"]]; a[0]+=1; a[1]+=(int(r["total_amt_msat"])-f)//1000; a[2]+=f
for T in (D,H):
    print("---")
    for k,(n,s,f) in sorted(T.items(), key=lambda x:-x[1][1]): print(k, "| n", n, "| sats", s, "| ppm", round(f*1000/s) if s else 0)
'
```

**4, le fatture incassate per canale d'arrivo:**
```bash
cd ~/nodo && docker compose exec -T lnd lncli listinvoices --max_invoices 100000 | python3 -c '
import json,sys,collections
T=collections.defaultdict(lambda:[0,0,0])
for i in json.load(sys.stdin)["invoices"]:
    for h in i["htlcs"]:
        if i["state"]=="SETTLED" and h["state"]=="SETTLED": a=T[h["chan_id"]]; s=int(h["amt_msat"])//1000; a[0]+=1; a[1]+=s; a[2]=max(a[2],s)
for k,a in T.items(): print(k, "| pezzi", a[0], "| sats", a[1], "| massimo", a[2])
'
```
Senza `--max_invoices` ne escono cento.

**5, gli inoltri** (senza `--start_time` si vedono solo le ultime 24 ore):
```bash
cd ~/nodo && docker compose exec -T lnd lncli fwdinghistory --start_time $(date -d 2026-09-01 +%s) --max_events 50000 | python3 -c '
import json,sys,collections
C=collections.defaultdict(lambda:[0,0,0])
for e in json.load(sys.stdin)["forwarding_events"]: a=C[e["chan_id_in"]+" -> "+e["chan_id_out"]]; a[0]+=1; a[1]+=int(e["amt_out"]); a[2]+=int(e["fee_msat"])
for k,a in C.items(): print(k, "| n", a[0], "| sats", a[1], "| guadagno sats", round(a[2]/1000,1))
'
```

Gli altri letti il 5 ott: i falliti con `listpayments
--include_incomplete` e `decodepayreq` della loro fattura (la «porta»
in fattura dice il wallet: `03864ef0` è ACINQ, cioè Phoenix); i nomi
con `getnodeinfo` e `describegraph`; `querymc`. Sul VPS, in
`-readonly`: `payout_passi` e `payout_tentati` raggruppati, e gli
indirizzi Lightning per SOLO dominio.

Fonti: [Spark, Lightning Interoperability](https://docs.spark.money/learn/lightning);
1ml, le pagine dei nodi `039174f8…` e `02a98e8c…` (capacità, canali, il
canale con LNBiG [Hub-3]), lette il 5 ott 2026.
