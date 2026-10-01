# I due LNbits, lo sweep del #152 e il canale da 5M (1 ott 2026)

Studio in sola lettura chiesto da Andrea, nato da un'idea di Alan: un
wallet «Alan» su LNbits, da usare con Zeus (LndHub) per spendere e così
svuotare il lato nostro dei canali. Nessun codice toccato: i comandi li
ha eseguiti Andrea sul VPS e sul nodo, uno alla volta, e i numeri qui
sotto sono i suoi. Scritto da Claude per Andrea e Alan.

## 1. Il wallet «Alan» su LNbits: NO, e perché

Deciso da Andrea il 1 ott, per quattro motivi:
- il saldo di un wallet LNbits è una riga di contabilità sopra la cassa
  COMUNE del nodo: LNbits non controlla che la somma dei wallet stia nel
  nodo. Un wallet caricato con sats non liberi spende i depositi;
- fa entrata solo se riceve sats GIÀ nel nodo e non dovuti a nessuno: se
  si ricarica da fuori consuma entrata, quando spende la restituisce
  (saldo netto zero). Cioè è un prelievo di capitale, non una leva;
- LNbits ascolta solo su `127.0.0.1:5001`: per Zeus andrebbe esposto a
  internet l'LNbits che custodisce la chiave che paga della cassaforte;
- `ronda-pagamenti.py` griderebbe «🚨 PAGAMENTO SCONOSCIUTO» a ogni
  spesa: il rumore che quella ronda è nata per togliere.
Il tetto di saldo di LNbits vale per TUTTI i wallet dell'istanza, quindi
non è una cura. Lo stesso effetto, se servisse, è la «spinta» di set
2026: un pagamento solo verso un wallet di Alan, un solo `--impara`.

## 2. I due LNbits

| | SaaS («saas») | Nodo («nodo») |
|---|---|---|
| Dove | ospitato, fondi su Spark | VPS, Docker `/opt/lnbits`, v1.6.1, solo `127.0.0.1:5001` |
| Fonte | Spark | LND del nodo via ponte WireGuard |
| Chiavi nel config | `LNBITS_URL`, `LNBITS_INVOICE_KEY`, `LNBITS_ADMIN_KEY` | `LNBITS_NODO_URL`, `LNBITS_NODO_INVOICE_KEY`, `LNBITS_NODO_ADMIN_KEY` |
| Wallet | «LNbits wallet» | «Cassaforte Barattolo», l'UNICO dell'istanza (visto nel pannello) |
| Depositi aperti | #129, #131, #134, #138 (To The Mooon), #153 (Steu): 403.105 | #159, #161, #183, #194, #195, #198, #201: 337.063 |

I cinque del SaaS hanno `cassaforte_payout` vuota: PAGANO ANCORA DAL SAAS
(letto il 1 ott), e Andrea vuole che restino così.

## 3. Lo sweep del 1 ott 2026

**Il buco.** Prima: SaaS 753.422 (depositi 403.105, +350.317), Cassaforte
nodo 84.538 (depositi 337.063, −252.525). Il #152 (P3dr0, 247.707) era
stato dichiarato morto il 24 set alle 12:24 e ripagato DAL NODO
(`gesti_cassaforte`: dichiara_morto saas→nodo 247.707), ma lo spostamento
a mano dei suoi sats dal SaaS al nodo, che la procedura chiedeva PRIMA,
non era stato fatto. Tolti i 247.707 restano −4.818 sul nodo (commissioni
e riserve dei payout già fatti) e +102.610 sul SaaS (la parte di
Barattolo). Il totale era positivo (+97.792): nessun sats sparito, sats
nel barattolo sbagliato. Effetto concreto: il #159 (105.268) non sarebbe
partito, e dopo un paio di payout nessun altro — `MOTIVO_SALDO`, «non
per colpa tua… ci riproviamo noi», nessun sats perso.

**Il gesto.** 265.000 = 247.707 + 17.293 di margine (la riserva di
LNbits è `max(1%, 2000)` a payout, più le commissioni dei sette payout).
Fattura dalla Cassaforte nodo (pannello col tunnel ssh), memo
`Sweep SaaS verso nodo (#152) N/3` — mai «Barattolo escrow…», o
`orfani.py` la leggerebbe come l'incasso di un ordine — pagata dal
pannello del SaaS controllando importo e memo prima di «Pay». Prima di
ogni pezzo: nessuna riga `in_volo`, `incerto` o `da_riprovare` nelle tre
tabelle che pagano.

| Pezzo | Nodo | SaaS | Commissione |
|---|---|---|---|
| 1/3 5.000 | 89.538 (+5.000) | 748.401 | 21 |
| 2/3 130.000 | 219.538 (+130.000) | 617.878 | 523 |
| 3/3 130.000 | 349.538 (+130.000) | 487.355 | 523 |

Totale 265.000 spostati, 1.067 di commissioni (0,4 %). Dopo: nodo
349.538 contro 337.063 (margine 12.475), SaaS 487.355 contro 403.105
(+84.250 di Barattolo, per la fase 5).

**I controlli dopo, tutti verdi:** `orfani.py` con ORFANI 0 e FUORI POSTO
0 sulle due casseforti (fra i NON NOSTRI del nodo le tre fatture dello
sweep, le due sonde del 15 set e due da 100; sul SaaS 91 vecchi più
l'«Admin credit» da 247.231 del 24 set); il riquadro «🏦 Cassaforte
SaaS» con 5 ordini che escono ancora dal SaaS; il credito del #152 in
«🔀 Crediti da recuperare» resta aperto, come deve.

## 4. Il nodo dopo lo sweep

Misurati prima dello sweep: due canali ACINQ, 400k (noi 240.873, loro
157.833) e 1M (noi 114.425, loro 884.281), riserve 4.000 e 10.000 per
lato, zero HTLC; on-chain 149.848 confermati, di cui 20.000 di riserva
per i canali anchor. Lo sweep è entrato tutto dai canali, quindi
CALCOLATI dopo: **noi 620.298, loro 777.114** — utili, tolte le riserve,
**606.298 in uscita e 763.114 in entrata**.

**I sats che non sono della Cassaforte:** nei canali 620.298 − 349.538
= 270.760 (256.760 spendibili, 14.000 sono riserve); on-chain 149.848
(129.848 spendibili). In tutto **420.608, di cui 386.608 spendibili**.
Di chi sono lo dice un documento solo per una parte: ~50.000 sono il
cuscinetto prestato da Alan (set 2026). Il resto (~370.000, fra
commissioni del P2P, resto dell'apertura dei canali e capitale versato)
NON È ATTRIBUITO: lo dicono Andrea e Alan, non un comando.

## 5. Quanta entrata per il lancio del 10 ottobre

L'entrata la consumano i depositi: il mercatino (picco visto 1,14M, oggi
337k sul nodo) e il P2P (ogni scambio tiene la hold invoice di chi vende
fino al rilascio, `max_order_amount` 500.000). Il conto:
1M per il mercatino + 1M per il P2P (due scambi grossi insieme) + 500k
perché la ronda della liquidità (soglia 500.000) non suoni nei giorni
normali = **~2,5M utili**. Oggi 763.114: **mancano ~1,75M**. L'uscita
non è il problema: un deposito che entra diventa uscita per il suo
payout.

## 6. I servizi di swap (verificati il 1 ott sulle fonti)

- **Boltz è spento dal 3 ago 2026** (sospensione a tempo indeterminato
  dopo un attacco al codice); Zeus è passato il 17 set a SATS Routing.
- **SATS Routing** (satsrouting.exchange): copia di Boltz v2 gestita da
  volontari, online da ago 2026, audit di terzi chiuso il 1 set. Swap
  atomico (HTLC): o va tutto o i sats tornano da soli. API letta dal
  vivo, Lightning → on-chain: **0,6 % + 1.114 sats** di commissioni
  on-chain (claim 467, lockup 647), **minimo 4.284, massimo 5.000.000**
  a swap. Giovane: ci si va a pezzi. Il nodo non deve collegarsi a
  loro: paga una fattura che viaggia sulla rete; il segreto e il claim
  li tiene il sito nel browser del PC, con la chiave di salvataggio.
- **FixedFloat** (ff.io): NO. Custodial di fatto (si mandano i sats e si
  aspetta), 0,5 % variabile o 1 % fisso, controlli AML che sospendono
  l'ordine e chiedono documenti e provenienza dei fondi, blocchi
  segnalati lunghi mesi; due attacchi nel 2024 (26,1 M$ e 2,8 M$).
- **Loop Out** (Lightning Labs, v0.35.0-beta del 25 ago 2026): 0,05-0,5 %,
  minimo ~250k e 30k di anticipo, ma vuole loopd sul nodo e un macaroon
  largo: superficie nuova su una macchina con l'audit chiuso. Riserva.
- **Il lease comprato** resta scartato con prova (Magma, set 2026).

## 7. Il piano del canale da 5M

**Verso chi: LNBiG [Hub-2]**, `033e9ce4e8f0e68f7db49ffb6b9eecc10605f3f3fcb3c630545887749ab515b9c7`,
onion `xbi6bipfby6prt6wddufgv5mq4mx2ihxsy4u4hycd73qfgc3oslonuid.onion:9735`
(letti su 1ml il 1 ott: 421 canali, ~231 BTC; da ricontrollare su Amboss
via Tor prima del gesto). È il «secondo peer con onion» già segnato nel
doppio wallet: onion verso onion, niente exit Tor, e si toglie il peer
unico. Ripiego: un terzo canale ACINQ (provato, ma tutto su un peer). Il
nodo di SATS Routing come peer no: troppo giovane per 5M, e il giorno che
si spegne il canale è da chiudere a forza.

**I passi** (ogni gesto che sposta soldi ha il suo avviso in chat):
1. `lncli connect` verso LNBiG, prima che Alan mandi i 5M: dice se ci
   accetta. Non sposta soldi.
2. `lncli newaddress p2tr`; Alan manda 5.000.000 on-chain, con
   l'indirizzo letto per un'altra strada (prime e ultime otto lettere).
3. `walletbalance` fino a 5.149.848 confermati.
4. `lncli wallet estimatefeerate`, poi `openchannel --local_amt 5000000`
   (la commissione dai 129.848 già nel nodo). Un rifiuto non trasmette
   niente.
5. `pendingchannels` fino al canale attivo; `ronda-liquidita.sh --impara`.
6. Gli swap con SATS Routing, ogni volta con un indirizzo nuovo,
   `decodepayreq`, poi `payinvoice --outgoing_chan_id <LNBiG>` con un tetto
   alle commissioni, e `ronda-nodo.sh --impara <hash>`: **prova 50.000**
   (costo ~1.414), poi **800.000, 800.000, 850.000** = 2,5M.

**I conti (commissioni del 1 ott, cambiano):** swap ~19.500 sats più
l'instradamento e la transazione di apertura; tornano on-chain ~2,48M,
capitale di Alan. Alla fine, sui canali (6,4M di capacità): ~3,1M in
uscita, ~3,28M in entrata, ~3,21M utili tolte le riserve (50.000 sono la
riserva del canale nuovo). Sopra i 2,5M del lancio, con aria.

## 8. Cosa resta aperto

- Di chi sono i ~370.000 non attribuiti (§4): lo scrivono Andrea e Alan.
- L'«Admin credit» del #152 sul SaaS è di 247.231, non 247.707: 476 sats
  di differenza da capire alla disdetta.
- Il credito del #152 resta aperto finché il SaaS non marca fallito il
  pagamento appeso (procedura in PRODUZIONE, «CHIUDERE LA CASSAFORTE
  SAAS»).
- Il SaaS chiude (fase 5) quando i cinque ordini si chiudono: allora lo
  sweep dei ~84.000 di Barattolo.
- Dopo l'apertura, l'SCB nuovo entra nel backup delle 03:30 del nodo.

Fonti: [Zeus PR #4620](https://github.com/ZeusLN/zeus/pull/4620),
[massmux su SATS Routing](https://massmux.org/p/a-new-boltzs-fork-is-running-sats),
[SatsRouting/boltz-backend](https://github.com/SatsRouting/boltz-backend),
`https://api.satsrouting.exchange/v2/swap/reverse` (1 ott),
[ff.io FAQ](https://ff.io/faq), [ff.io termini](https://ff.io/terms-of-service),
[kycnot.me](https://kycnot.me/service/fixedfloat),
[Halborn sul 2024](https://www.halborn.com/blog/post/explained-the-fixedfloat-hack-february-2024),
[Loop CLI](https://docs.lightning.engineering/lightning-network-tools/loop/the-loop-cli),
[LNBiG Hub-2 su 1ml](https://1ml.com/node/033e9ce4e8f0e68f7db49ffb6b9eecc10605f3f3fcb3c630545887749ab515b9c7).
