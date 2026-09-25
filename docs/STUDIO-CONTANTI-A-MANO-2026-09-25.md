# Studio: «Contanti a mano nel P2P» (25 settembre 2026)

Sola lettura, nessuna modifica al codice, nessun cantiere aperto. Base:
`origin/main` a `b916518` (i numeri di riga qui sotto sono di quel
commit; i NOMI di funzioni, tabelle e leve sono la cosa da cercare, le
righe si spostano). Il VPS, il nodo e il relay non sono stati toccati.
Fatti esterni verificati sulle fonti in fondo, lette il 25 set 2026;
quel che NON ho potuto verificare da qui è scritto come tale.

**La domanda di Andrea.** Come garantire meglio gli scambi in contanti
di persona nel P2P di Barattolo su Mostro: cosa fanno gli altri, cosa
si può fare senza toccare mostrod, se e come mettere una cauzione anche
a chi compra, e cosa fare prima del 10 ottobre.

**La risposta corta.** Oggi il contanti di persona è, nel nostro P2P,
**un metodo come SEPA**: la voce `Contanti` sta in `P2P_METODI` accanto
agli altri, senza una riga di regola, di testo o di tetto sua. Il
rischio che porta è però di un'altra specie: un bonifico lascia una
ricevuta, una banconota no — quindi **in disputa non c'è niente da
guardare**, e il moderatore di Barattolo (che ha promesso in «Info P2P»
di «guardare le prove di tutti e due») si troverebbe una parola contro
l'altra. Gli altri exchange lo sanno da anni e rispondono in due modi:
**far pagare l'assenza** (RoboSats e Bisq mettono una cauzione anche a
chi compra) o **restringere il perimetro** (Bisq limita il F2F, Peach lo
fa solo ai meetup con la sua gente, Hodl Hodl scrive nei Terms che
sul contanti di persona non giudica e rimborsa chi vende). Mostro upstream ha GIÀ una cauzione
per tutt'e due le parti, `[anti_abuse_bond]`, che sul nostro nodo è
spenta per scelta: è la strada meno invasiva per la cauzione del
compratore, molto più di una hold invoice gestita da Barattolo fuori da
Mostro, che porterebbe custodia, un segreto in più sul VPS e un pezzo di
escrow che sparisce se sparisce Barattolo. **Raccomandazione: prima del
10 ottobre nessuna patch e nessuna cauzione, ma il perimetro — un tetto
in euro per il contanti, una regola scritta nel foglio e nella pagina
(«si libera sul posto, mai prima; senza la prova di presenza la disputa
si decide contro chi compra i sats»), e la prova di presenza a QR fra i
due telefoni, che è un cantiere solo di client; dopo, i bond di Mostro
accesi in una finestra corta e a importo basso, prima di qualunque
cauzione fatta in casa.**

## Come leggere questo file

- Le quattro domande di Andrea hanno una sezione ciascuna (1-4), più le
  fonti.
- «VERIFICATO» = letto sulla documentazione ufficiale, sul wiki o sul
  sorgente. «NEL CODICE» = con nome e riga in `server.py` o
  `miniapp.html`. «A VERBALE» = decisione già scritta in `CLAUDE.md`,
  `docs/CANTIERI.md` o `docs/ARCHITETTURA.md`, col NOME della voce, da
  non contraddire. «DA DECIDERE» = una scelta di Andrea, con le due
  strade accanto. «NON TROVATO» = cercato e non verificato: vale come
  dubbio, non come fatto.

## 0. Da dove partiamo (NEL CODICE)

Il contanti oggi, in cinque righe:

- **È un metodo fra sette.** `P2P_METODI` (`miniapp.html:50491`) elenca
  `SEPA, SEPA Instant, Revolut, Satispay, PayPal, Contanti, Contanti al
  tabacchino`. Il tabacchino ha un cantiere intero (Barattozon: PayCode,
  scadenze, tetto dei 999 € di Amazon, `_euro_tabacchino`,
  `server.py:43216`). `Contanti` no: compare in un filtro del libro
  («gli ordini in contanti», `miniapp.html:52671`) e basta. Nessun
  testo, nessun tetto, nessuna guida, nessuna riga in «Info P2P».
- **Il flusso è quello di ogni metodo.** Chi vende sats blocca i sats
  nella hold invoice del coordinatore; chi compra dice «Fatto ✅» con
  `fiat-sent` (`miniapp.html:50392`); chi vende **rilascia**
  (`euro_inviati` → `rilascia`, `miniapp.html:47388`). La disputa si apre
  da `attivo`, `pagamento_ritentato` o `euro_inviati`
  (`P2P_DISPUTABILI`, `miniapp.html:47452`) e la decide un moderatore di
  Barattolo, con due esiti soli (Info P2P, `miniapp.html:9539`).
- **Chi compra non mette niente.** Il bond anti-abuso di mostrod è
  spento (`[anti_abuse_bond]` commentata; A VERBALE in `CLAUDE.md`, «I
  TRE TIMER», e in CANTIERI alla riga «il bond anti-abuso sul nostro
  coordinatore è spento»). Abbandonare uno
  scambio dopo la presa non costa nulla a nessuno dei due, salvo la
  reputazione.
- **I tetti che ci sono.** `max_order_amount` 500.000 sats sul nodo (dal
  17 set, letto dal 38385) e la leva NOSTRA in euro `P2P_MAX_EURO`
  (`server.py:39701`, giudicata dal client, oggi a 0 = spenta). Sono
  tetti per ordine e uguali per ogni metodo.
- **Quel che le parti sanno l'una dell'altra.** Dalla presa in poi si
  vedono profilo, stelline, livello e titolo, e i bottoni per scriversi
  (Info P2P, «I tuoi dati», `miniapp.html:10036`); la chat fuori da
  Barattolo «in una disputa non possiamo usarla» (`miniapp.html:10038`).
  Le recensioni P2P ai due lati esistono dal 17 set e dal 24 set contano
  in classifica (CANTIERI, «Le recensioni che contano in classifica»).
  La reputazione esce anche su Nostr come kind 30382 (CANTIERI, «La
  reputazione come evento NIP-85»). Il livello (`LIVELLI`,
  `server.py:3340`: Nuovo arrivato, Bottega avviata a 50 XP e 1 affare,
  Mercante pratico a 200 e 5, Mercante esperto a 800 e 15, Maestro del
  banco a 3000 e 40) oggi nel P2P conta solo per lo sconto fedeltà del
  livello 5.

**La finestra di tempo che il contanti ha davvero**, letta sui timer di
Mostro (A VERBALE, «I TRE TIMER»): dopo la presa i 900 secondi valgono
per la fattura di chi compra e per il pagamento della hold di chi
vende, poi lo scambio sta in `active` senza nessun cronometro di
mostrod, e l'unica scadenza è l'HTLC della hold invoice —
`hold_invoice_cltv_delta` 576 blocchi meno il margine di 24, circa **92
ore**. Quindi due persone che si danno appuntamento hanno fino a quasi
quattro giorni fra il blocco dei sats e l'incontro, e dopo mostrod
molla la presa da sola. È una finestra generosa per un incontro, e per
questo anche per chi vuole tenere bloccati i sats di qualcuno per
niente.

## 1. Come lo trattano gli altri (VERIFICATO sulle fonti in fondo)

Cinque piattaforme, due famiglie. **RoboSats e Bisq 1 fanno pagare
tutt'e due le parti** prima ancora di sapere come andrà: una cauzione
che si perde se non si fa la propria parte. **Hodl Hodl, Peach e Mostro
fanno depositare solo chi vende bitcoin** e affidano il resto alla
reputazione e a un arbitro. Il contanti di persona lo hanno tutti come
metodo; la regola scritta sul contanti ce l'ha quasi solo Bisq, e tutti
ammettono che la disputa sul contanti «non si decide».

### 1a. RoboSats: la cauzione di fedeltà di tutt'e due

- **Il bond.** Maker E taker bloccano una hold invoice Lightning sul
  nodo del coordinatore, del **3%** dell'importo per default, che il
  maker può fissare **fra il 2% e il 15%** (`DEFAULT_BOND_SIZE = 3`,
  `MIN_BOND_SIZE = 2`, `MAX_BOND_SIZE = 15` in `settings.py`); «bondless
  takers are not available». I sats non escono dal wallet: è una hold,
  come quella di Mostro.
- **Quando si brucia.** In quattro casi: si perde una disputa; si
  annulla da soli dopo che il contratto è finale; non si consegna in
  tempo la escrow invoice (chi vende) o la payout invoice (chi compra);
  chi vende non conferma il fiat ricevuto. A scambio concluso torna da
  solo. **Metà del bond bruciato va alla parte onesta** «as
  compensation for wasted time» (`SLASHED_BOND_REWARD_SPLIT = 0.5`),
  l'altra metà al coordinatore; ma la regola scritta è che «you will
  not be able to win your counterparty's bond», salvo discrezione del
  coordinatore.
- **L'escrow di chi vende** è una seconda hold invoice, separata dal
  bond; tempo per depositarla **3 ore** per default (da 1 a 10, scelto
  dal maker), stessa finestra per la payout invoice di chi compra. Chi
  vende e non deposita perde il bond.
- **Timer.** Bond del maker entro 300 s, del taker entro 150-200 s
  (varia per config); pagamento fiat entro **24 ore**, allo scadere si
  apre una disputa da sola; ordine pubblico al massimo 24 ore.
- **In disputa** decide lo staff del coordinatore con estratti e log
  della chat; l'escrow va a chi vince, chi perde perde il bond; la fase
  di disputa dura 1 giorno di timer.
- **Cash F2F esiste** dalla v0.5.3 (ott 2023): una mappa nel libro con
  la posizione **randomizzata in 15×15 km**, e il punto esatto si dice
  solo in chat cifrata. **Nessuna regola sul contanti nei docs**
  (nessun «incontratevi in un posto pubblico»): l'unica è di un
  coordinatore, Temple of Sats, che vieta il F2F negli Stati Uniti.
- **Tetti.** Per ordine da 20.000 a 4.000.000 sats nei docs (per il
  routing Lightning), e ogni coordinatore mette il suo `MAX_ORDER_SIZE`
  (500.000 nel sample, FreePort 500.000). Fee 0,2% totale.
- **Cosa vale per noi.** È il modello più vicino a Mostro (hold invoice,
  coordinatore, Lightning), e la cosa che fa in più è esattamente la
  cauzione del compratore, senza nessuna regola in più per il contanti:
  il bond paga il tempo perso, non la banconota.

### 1b. Bisq 1 e Bisq Easy: il deposito cauzionale e il perimetro del F2F

- **Bisq 1, il deposito.** Tutt'e due le parti bloccano un deposito in
  un multisig 2-di-2 on-chain: **dal 15% al 50%** dell'importo, minimo
  0,001 BTC, scelto dal maker e uguale per il taker; chi vende mette
  anche i bitcoin dello scambio (1 BTC venduto col 25%: 1,25 di qua,
  0,25 di là, 1,5 nel multisig). Esito normale: tornano tutt'e due.
- **Tre gradini di disputa**: chat, mediazione (il mediatore ha un bond
  di 10.000 BSQ, risponde entro 48 ore e propone soltanto: non ha
  chiavi), arbitrato (solo se uno rifiuta la proposta; la «delayed
  payout tx» manda TUTTO ai Burning Men della DAO dopo 20 giorni sul
  fiat, e dal 2023 l'arbitro paga di tasca sua e si fa rimborsare dalla
  DAO). Chi vince riprende importo e deposito suo e «una porzione
  limitata» di quello dell'altro.
- **La tabella delle penali** (percentuali del deposito): 100% frode o
  chargeback; **50% per chi mette contatti fuori piattaforma
  nell'offerta di un F2F o cash by mail**; 25% chi non risponde al
  mediatore in 48 ore; 20% chi annulla senza motivo; ritardi nel
  pagamento dal 5% (sotto 24 ore) al 20% (oltre 72).
- **Il F2F di Bisq 1** è un metodo con la sua pagina di regole: campi
  Paese, valuta, **città** (visibile nell'offerta) e «informazioni
  aggiuntive», **vietato mettere un contatto diretto** (regola del 9
  apr 2022, penale suggerita del 50%). Consigli: posto pubblico neutro
  con testimoni o telecamere, non portare più del necessario,
  controllare le banconote, **portare il computer perché chi compra
  segna «pagato» e chi vende rilascia sul posto**. Il wiki dice chiaro
  che mediatori e arbitri «often won't have a way to settle disputes»
  per «lack of verifiable actions». **Tetto per scambio: 0,25 BTC**
  (era 1 BTC nel 2021), periodo di scambio 4 giorni, senza firma
  dell'account. Cash by mail 0,0624 BTC e 8 giorni; cash deposit 0,0624
  e 4 giorni. «Cash at ATM» non esiste, né in Bisq 1 né in Bisq 2.
- **Bisq Easy (Bisq 2)** è l'altro estremo: **nessun deposito da
  nessuna parte**, nessuna fee, chi compra paga per primo, quindi la
  reputazione serve solo a chi vende, fatta di BSQ bruciati o bonded e
  di età dell'account; **tetto 600 USD** per scambio e formula «massimo
  in USD = punteggio / 200», con almeno 30.000 punti per essere presi
  (alzati da 10.000 dopo una truffa). La disputa la fa un mediatore
  volontario senza escrow; la sanzione è il ban.
- **Cosa vale per noi.** Bisq è chi ha scritto di più sul contanti, e
  la sua risposta è il PERIMETRO: tetto più basso del resto, città
  nell'offerta e mai un contatto, incontro con l'app in mano, e la
  frase onesta che la disputa sul contanti non si decide. Bisq Easy
  mostra che senza deposito il tetto scende a 600 USD e sale solo con
  la reputazione: è la nostra scala dei livelli, applicata a un
  metodo.

### 1c. Hodl Hodl: deposita solo chi vende, e sul contanti non giudica

- **Escrow multisig 2-di-3** on-chain (chi vende, chi compra, Hodl
  Hodl): Hodl Hodl da sola non muove niente; in disputa usa la sua
  chiave con una delle due parti. La chiave di chi compra serve SOLO se
  la disputa è vinta da lui. **Deposita solo chi vende; nessuna
  cauzione del compratore** (FAQ, blog e Terms non ne parlano). Fee
  0,75% per parte (0,5% con referral).
- **Se chi compra sparisce**: alla scadenza della finestra di pagamento
  (la fissa chi pubblica, `payment_window_minutes`, 60 negli esempi)
  una delle parti annulla o apre disputa; chi vende paga la fee di rete
  del rimborso. Chi compra non rischia sats.
- **«In person» esiste** come metodo, e **LA RIGA CHE CONTA STA NEI
  TERMS OF SERVICE**: «Hodl Hodl does not resolve disputes for 'in
  person' payment method trades. Bitcoin is returned to the Seller
  unless both parties explicitly agree otherwise.» Cioè sul contanti
  di persona **l'admin non giudica: rimborsa chi vende**, per regola
  scritta prima. Nelle altre dispute risponde entro 12 ore, guarda
  prove di pagamento, chat e reputazione, e «where both parties provide
  equally convincing evidence» sceglie il caso più forte.
- **Reputazione**: media aritmetica dei voti, dati a scambio concluso o
  a disputa risolta; nell'API anche il tempo medio di pagamento e di
  rilascio. La verifica volontaria è stata tolta.
- **Cosa vale per noi.** È la regola più netta che esista sul contanti:
  senza prove i sats tornano a chi li ha bloccati, e sta scritta nei
  Terms, non decisa il giorno della disputa. È la regola 2e di questo
  studio, con l'aggiunta della prova di presenza che Hodl Hodl non ha.

### 1d. Peach: il contanti solo ai meetup, e la chiave che non c'è più

- ⚠️ **Contesto che cambia tutto (31 ago 2026, «Peach at a
  Crossroads»)**: Peach **non firma più l'escrow** («the seller fully
  controls the escrowed BTC»); possono vendere solo utenti KYC, in
  whitelist, o con zero dispute perse e 60+ vendite (o 30+ vendite e
  80+ scambi); i non-KYC un solo scambio alla volta; la fee del 2%
  resta; il sistema di dispute in-app resta, ma senza chiave. Quel che
  segue è il disegno storico, che i loro docs ancora raccontano.
- **Escrow 2-di-2** chi vende + Peach (chi compra NON ha una chiave),
  che dopo ~30 giorni passa sotto il pieno controllo di Peach; **chi
  compra non deposita niente** (nell'API `sellerFee: 0`, fee 2% a chi
  compra). Finestre: 12 ore a chi compra per pagare, 12 a chi vende per
  finanziare l'escrow, 1 ora nello «instant trade».
- **Cash trade e meetup**: i «meetup» sono ritrovi bitcoin già
  esistenti nelle città, almeno mensili; nell'app si sceglie «remote /
  meetups», si aggiunge il meetup come metodo di pagamento, si accetta
  un **disclaimer del contanti** («trade responsibly with cash, as
  Peach cannot be the responsible in case something goes wrong»; «we
  only recommend using the cash feature on the meetup itself»), e il
  matching è «alla Tinder» fra chi va allo stesso meetup. Il rilascio è
  la stessa slitta «I received the payment» di chi vende. Nell'API il
  cancel vale «at any time during cash trades»: chi vende può annullare
  un cash trade quando vuole e riprendersi i sats. Tetti: 1.000 CHF al
  giorno senza registrazione, **1.000 CHF al mese per cash trade e gift
  card**, 100.000 CHF l'anno. Agli organizzatori dei meetup una parte
  della fee (1% del volume cash, fonte terza).
- **Disputa**: motivi a catalogo (`noPayment`, `unresponsive`,
  `abusive`, `other`), mediatori di Peach su prove, risposta entro 24
  ore, decisione «conclusive, final and binding». Nessuna clausola sul
  contanti (NON TROVATA); dal 1 set 2026 senza chiave la mediazione è
  persuasione.
- **QR al meetup: NON TROVATO.** Nessuna pagina descrive un QR fra i
  due telefoni per confermare i contanti; l'unico QR è l'abbinamento
  della web app. La prova di presenza (2b) non la fa nessuno di questi
  cinque.
- **Cosa vale per noi.** Peach ha messo il contanti dentro un PERIMETRO
  SOCIALE (un meetup con gente che si conosce) e un tetto basso, invece
  che dentro una regola di disputa: è la strada che ha senso per una
  community italiana che si vede ai meetup, e non costa codice. E la
  sua svolta di agosto dice cosa succede a un escrow senza cauzione di
  chi compra: alla fine la garanzia torna tutta sulla reputazione di
  chi vende.

### 1e. Mostro: nessuna regola sul contanti, ma un bond già scritto

- **Il contanti è una stringa.** `payment_method` è testo libero
  separato da virgole, e l'esempio del protocollo è proprio «face to
  face,bank transfer,mobile»; nel 38383 il tag `pm` ha «face to face»
  fra gli esempi e c'è un tag facoltativo `g` (geohash) «for
  location-based trades». **Nessun ramo cash o F2F in `src/app/`**:
  «Mostro does not intervene in the fiat exchange, it only coordinates
  the exchange of sats».
- **Chi compra non rischia niente, nemmeno in reputazione.** Il voto
  si dà solo con l'ordine in `success` (o `settled-hold-invoice`, e lì
  vota solo chi vende: `rate_user.rs`); dopo un `admin-cancel` — la
  disputa persa da chi compra — **nessuno vota nessuno**. L'unica leva
  è il bond.
- **La disputa** si apre da `active` o `fiat-sent`, non tocca la hold
  invoice all'apertura; `admin-settle` salda la hold e paga chi
  compra, `admin-cancel` cancella la hold e restituisce a chi vende,
  tutt'e due con un `bond_resolution` facoltativo.
- **La reputazione va sulla chiave identità** (`m/44'/1237'/38383'/0/0`,
  `master_*_pubkey` in `rate_user.rs`), pubblicata come kind 38384; la
  pagina `user_rating` dice «trade pubkey» ma vale il codice. Chi
  scambia in piena privacy (trade key sola) non accumula nulla e non
  viene votato. Il nostro client manda l'identità (il profilo di
  scambio, `SEGRETI_PROFILO_P2P`), quindi i nostri utenti la reputazione
  di Mostro la costruiscono.
- **`[anti_abuse_bond]`**, arrivato con la **v0.17.5** e rifinito fino
  alla 0.18.8 (PR #964: «pay the maker after a timeout slash»; sono le
  due migrazioni `bond_payout_recipient` che la nostra `-bar5` ha già
  applicato al database, PRODUZIONE «Mostro 0.18.8»). Dal template, tutto
  commentato: `enabled = false`, `amount_pct = 0.01`,
  `base_amount_sats = 1000` (bond = max dei due), `apply_to = "take"`
  (o `make`, o `both`), `slash_on_waiting_timeout = false`,
  `slash_node_share_pct = 0.5`, `payout_invoice_window_seconds = 300`,
  `payout_claim_window_days = 15`. È **una seconda hold invoice** con
  la sua riga e il suo ciclo; si brucia in DUE soli casi — la
  direttiva del solver in disputa (`BondResolution`: `slash_seller` o
  `slash_buyer` su `admin-settle`/`admin-cancel`) o il timeout dello
  stato di attesa se la leva lo permette — e in tutti gli altri torna.
  Allo slash metà resta al nodo e metà va alla controparte, che la
  reclama con una fattura (`add-bond-invoice`) entro 15 giorni. La
  sezione 3a dice cosa costa accenderlo.
- **Cosa vale per noi.** La cauzione del compratore che RoboSats fa da
  anni **Mostro ce l'ha già, spenta**. Non è una patch: è tre righe di
  `settings.toml` più il lavoro del client. E il 38385 la annuncia
  (`bond_enabled`, `bond_apply_to`, `bond_amount_pct`), quindi il client
  la legge viva come legge la fee.

## 2. Cosa possiamo fare senza toccare mostrod

Tutto quel che segue vive nel client, nel server di Barattolo e nei
testi: il coordinatore non lo vede e non deve saperlo. È lo stesso
gradino del tetto in euro (`P2P_MAX_EURO` «il coordinatore non la
conosce e non la applica»): la regola la giudica il client, il
protocollo resta upstream.

### 2a. La regola del rilascio sul posto (testo e foglio, peso piccolo)

Il rischio del contanti sta tutto nell'ORDINE dei gesti. Con un
bonifico chi vende sats rilascia quando vede i soldi sul conto, e la
banca è il testimone. Col contanti il testimone non c'è, quindi la
regola deve dire cosa fa da testimone: **i sats si liberano davanti
all'altra persona, dopo aver contato le banconote, e mai prima di
vedersi**. Tre righe da scrivere, in tre posti:

1. **Nel foglio dove si pubblica o si prende** con `Contanti` scelto,
   una riga sotto il metodo (non un avviso a ogni gesto: la decisione
   «vi vedete» del 17 set dice che i fogli non si riempiono di avvisi
   che non cambiano la cifra; qui invece la riga cambia il gesto, e sta
   sul metodo, non sul foglio).
2. **Nella pagina dello scambio**, sul gradino di chi vende: il bottone
   che oggi dice di liberare i sats, col contanti, chiede conferma
   dicendo «Hai contato i contanti davanti a chi ti ha pagato?»
   (`chiediConferma`, la settantesima è del PayCode: la settantunesima
   sarebbe questa).
3. **In «Info P2P»**, un paragrafo «Contanti di persona» accanto a
   quello del tabacchino, che dice la regola e quel che succede in
   disputa (vedi 2e).

Cosa NON risolve: chi vende sats può comunque prendere i contanti e non
liberare. Lì la regola non serve; serve la prova di presenza (2b) e la
cauzione (3).

### 2b. La prova di presenza: QR firmati fra i due telefoni

L'idea è dare alla disputa un fatto che oggi non ha: **i due telefoni
erano nello stesso posto alla stessa ora, e tutt'e due lo hanno
firmato**. Non prova che le banconote siano passate di mano; prova che
l'incontro c'è stato, che è la cosa che una delle due parti potrebbe
negare.

**Come funziona, col materiale che c'è già.** Ogni parte ha nel browser
la sua trade key Nostr dello scambio (nasce lì, mai sul server: regola
ferrea 2). Il client sa già firmare eventi con quella chiave
(`messaggioMostro`, `bustaMostro`) e sa già mostrare e leggere un QR
(le fatture). Quindi:

1. Sul gradino «vi vedete» chi compra sats tocca «📍 Siamo qui»: il
   telefono compone una nota `{ordine, ruolo, ora, geohash (facoltativo,
   precisione a ~150 m), nonce}` firmata con la sua trade key, e la
   mostra come QR.
2. Chi vende la inquadra; il suo telefono verifica la firma contro la
   chiave dell'altra parte (che conosce: è la controparte dell'ordine),
   controlla che l'ora sia entro pochi minuti e che l'ordine sia quello,
   e **contro-firma** la stessa nota con la propria chiave. Ora esiste
   una ricevuta con DUE firme.
3. La ricevuta a due firme si manda **al server di Barattolo** (una
   rotta nuova, tipo `POST /api/p2p/presenza`, che salva l'ordine, le
   due chiavi, l'ora e le firme, e le verifica) e, opzionale, cifrata
   all'altra parte come kind 14, così ce l'hanno tutt'e due.
4. Se lo scambio finisce in disputa, il moderatore vede «presenza
   firmata da tutt'e due alle 17:42» oppure «nessuna presenza». La
   regola scritta in «Info P2P» dice cosa ne fa (2e).

**Perché il server e non solo i telefoni.** In disputa la prova la deve
vedere il moderatore, e la deve vedere anche se una delle due parti ha
cancellato l'app: una ricevuta che vive solo sui due telefoni è nelle
mani di chi ha interesse a perderla.

**Perché due firme e non una.** Un QR firmato da uno solo prova che UNO
c'era. Il contro-firma è quel che rende la ricevuta un fatto su
entrambi: nessuno dei due può poi dire «non l'ho mai incontrato».

**Il luogo, con misura.** La posizione GPS è un dato pesante (privacy,
e il browser la chiede con un permesso a sé): la nota funziona anche
senza, con la sola ora e il nonce. Il geohash a ~150 m si offre come
facoltativo, e non si salva mai la posizione esatta. Il dato che pesa
davvero non è il luogo: è il **tempo**, perché una ricevuta firmata
alle 17:42 da tutt'e due nello stesso minuto non si fabbrica dopo.

**Cosa NON prova.** Che i contanti siano stati contati, né quanti. Chi
vende sats può firmare la presenza e poi dire «erano meno». Per quello
c'è solo la regola: **la presenza firmata dopo il conteggio, non
prima**, e il testo che lo dice.

**Peso**: due gesti nel client (mostra QR / inquadra QR), una rotta e
una tabella sul server, un pezzo di pagina per il moderatore, prove.
Un cantiere di un paio di giorni, senza toccare mostrod e senza
custodia.

### 2c. Limiti per livello e tetti per scambio

Oggi i tetti sono uguali per ogni metodo. Il contanti merita **un tetto
suo, più basso**, per la stessa ragione per cui Amazon ferma il
tabacchino a 999 €: sopra una cifra il rischio di un incontro a vuoto,
o di una rapina, non lo paga il protocollo. La leva è la gemella di
`P2P_MAX_EURO`: **`P2P_MAX_EURO_CONTANTI`**, giudicata dal client nel
foglio (stesso posto, `miniapp.html:51567`), che vale SOLO quando il
metodo scelto è `Contanti`, e sotto resta il tetto generale e quello in
sats del nodo. Andrea sceglie il numero; il confronto con gli altri è in
1: Bisq ferma il F2F sotto i limiti degli altri metodi e Peach tiene i
suoi incontri su cifre da evento.

**Per livello.** `livello_utente` (`server.py:3347`) dà già cinque
gradini con XP E affari. Il tetto del contanti può salire col livello,
in una tabella nel config (es. Nuovo arrivato = 100 €, Bottega avviata
= 250, dal Mercante pratico in su il tetto generale). Il livello il
client lo conosce (`/api/me`, la pastiglia «Lv. N»), quindi il giudizio
resta nel foglio senza una domanda in più. Due cautele A VERBALE: 1) il
livello lo dà il mercatino, non il P2P — un Maestro del banco che non
ha mai scambiato sats è un Maestro del banco; 2) il tetto vale per chi
PUBBLICA l'ordine; chi lo PRENDE lo vede già scritto, e il client di chi
prende può rifiutare di prendere un contanti sopra il proprio tetto (è
lo stesso gesto: un giudizio nel foglio prima della busta).

### 2d. Divisione in più ordini

«Vuoi vendere 800 € in contanti? Fanne quattro da 200» è la cosa più
economica che esista: il rischio di ogni incontro si ferma al tetto, e
la fiducia si costruisce a gradini. Costa zero al protocollo (sono
quattro ordini normali), ma ha due controindicazioni da scrivere:
ogni ordine paga la sua fee (oggi 3% metà a testa, quindi non cambia in
proporzione) e ogni presa riparte con i suoi 900 secondi per gesto; e
il libro pubblico mostra quattro ordini uguali, che a un occhio esterno
dicono «stessa persona». Il modo giusto è **suggerirlo nel foglio**
quando la cifra supera il tetto del contanti («sopra X € il contanti
si divide: pubblica più ordini») invece di automatizzarlo, che sarebbe
un ordine per conto di qualcuno.

### 2e. La regola della disputa, scritta prima

La più importante e la meno tecnica. Oggi «Info P2P» promette di
guardare le prove: col contanti va detto QUALI prove esistono e cosa
vale la loro assenza, altrimenti il moderatore decide a occhio e
chiunque perda dirà che era di parte. Proposta, da scrivere in «Info
P2P» sotto «Contanti di persona»:

- I sats si liberano sul posto, dopo aver contato. Chi li libera prima
  di vedersi, li ha regalati.
- La prova dello scambio è la **presenza firmata** dai due telefoni
  (2b). Senza presenza firmata, in disputa **i sats tornano a chi li ha
  bloccati**: chi compra sats accetta di incontrarsi con l'app in mano,
  o non compra in contanti.
- Con la presenza firmata e chi vende che non libera, i sats vanno a
  chi compra: la firma del venditore dice che l'incontro c'è stato, e
  la regola dice che si firma DOPO il conteggio.

È dura verso chi compra sats, ed è la scelta che fanno anche gli altri
(vedi 1): chi porta i contanti è la parte che può sempre non
presentarsi, quindi è la parte a cui si chiede il gesto in più. La
regola vale solo se sta scritta PRIMA dello scambio, nel foglio e nella
pagina, e non il giorno della disputa.

## 3. Una cauzione anche per chi compra

### 3a. Come bond di Mostro: non una patch, una leva già scritta

**Dove sta nel protocollo.** Il bond è una seconda hold invoice, con il
suo hash e la sua riga nella tabella `bonds`, che mostrod chiede a chi
PRENDE subito dopo `take-buy`/`take-sell` (`apply_to = "take"`), a chi
PUBBLICA in risposta a `new-order` prima che l'ordine esca nel libro
(`make`), o a tutt'e due (`both`). Chi compra sats è a volte maker (un
ordine `buy`) e a volte taker (prende un `sell`): **per coprire chi
compra in ogni verso serve `both`**, e allora la cauzione la mette anche
chi vende, che oltre alla hold dell'importo blocca l'1%. Importo:
`max(amount_pct × importo, base_amount_sats)`, cioè con i default l'1%
con un pavimento di 1.000 sats — su un ordine da 50.000 sats il
pavimento vince e la cauzione è il 2%.

**Quanto è invasivo, in ordine.**

1. **Sul nodo: tre righe di `settings.toml`** (`enabled`, `apply_to`,
   `amount_pct`/`base_amount_sats`) e un `docker compose restart
   mostro`. Le migrazioni ci sono già (0.18.8). Rollback: `enabled =
   false`, con i bond aperti che si chiudono da soli al loro ciclo.
2. **Sul client: un messaggio nuovo in ingresso e uno in uscita.** Dopo
   la presa (o la pubblicazione) mostrod manda `pay-bond-invoice` con
   la bolt11 della cauzione, e finché non è pagata l'ordine per il
   taker resta `pending` e prendibile da altri (per il maker non viene
   pubblicato). Il nostro client oggi non conosce quel messaggio: va
   aggiunto un gradino «Blocca la cauzione» prima dei gradini di
   adesso, con lo stesso stampo della hold di chi vende (`garanzia_chiesta`
   → `garanzia_pagata`, `server.py:43759`), l'avviso relativo (patch
   0007: gli eventi del bond vanno censiti in `barattolo_eventi.rs`), e
   il conto che mostra la cauzione come riga a sé, che TORNA. In
   uscita, chi vince uno slash riceve `bond_slashed` e deve rispondere
   con `add-bond-invoice` entro 300 secondi (5 tentativi, 15 giorni per
   reclamare): il client deve saperlo fare, altrimenti la metà del
   vincitore va al nodo come `forfeited`, che è il difetto MOSTRO-006
   già visto upstream. Il wallet NWC del P2P (CANTIERI «Il wallet fa la
   fattura») rende il gesto automatico per chi ce l'ha.
3. **Sul moderatore: la direttiva.** Lo slash in disputa non è
   automatico — «there is no `slash_on_lost_dispute` flag» — ma va
   detto dal solver nel payload `BondResolution` di `admin-settle` o
   `admin-cancel`. Oggi la disputa la chiudiamo dal nodo a mano (la
   liturgia di `admin_cancel.rs` è a verbale): va aggiunto il campo, e
   va scritta PRIMA la regola di quando si brucia (2e: senza presenza
   firmata si brucia a chi compra; con presenza firmata e nessun
   rilascio si brucia a chi vende).
4. **Le due patch del fork si rileggono** (A VERBALE in
   `deploy/mostro/README.md`, 0005: «la strada dei BOND mette
   `order.fee` nel contesto di chi prende e può far correre più prese
   sullo stesso ordine. Prima di accendere i bond questa patch si
   rilegge»), e la 0007 va estesa agli eventi del bond.
5. **I timer.** `slash_on_waiting_timeout` resta `false` all'inizio:
   accenderlo vuol dire che chi tarda i 900 secondi PERDE la cauzione
   invece di veder tornare l'ordine nel libro, ed è la leva che
   CLAUDE.md già nomina come cura vera per «15 minuti sono pochi» — ma
   va accesa dopo, quando i bond sono provati, non insieme.

**Quel che il bond NON fa.** Non sa che lo scambio è in contanti: brucia
per un timeout o per una direttiva, e la direttiva la scriviamo noi.
Quindi la cauzione di Mostro **è il braccio, e la regola 2e è la
testa**: senza la regola scritta e la prova di presenza il moderatore
non ha su cosa fondare lo slash, e un bond che non si brucia mai è una
tassa sul tempo e basta. Ed è un bond PICCOLO: l'1% non ferma chi vuole
tenere bloccati i sats altrui per un giorno — RoboSats parte dal 3% e
lascia salire al 15%. `amount_pct` è nostro, e la scelta del numero è
di Andrea; su un ordine in contanti da 200 € l'1% è un caffè.

**Il costo per chi scambia.** Una hold invoice in più da pagare col
wallet, che resta «in sospeso» finché torna: è lo stesso che chi vende
vive già con la hold dell'importo, quindi i wallet che funzionano oggi
funzionano anche qui (e la finestra è la stessa, ~92 ore). Per chi
compra sats è il primo sat che gli si chiede di muovere PRIMA di
ricevere: va detto nel foglio, con la parola «cauzione, che torna».

### 3b. Gestita da Barattolo: una hold invoice sul nostro nodo fuori da Mostro

L'alternativa è che **Barattolo** chieda a chi compra sats una hold
invoice sua — una cauzione tenuta sul nodo, fuori dal coordinatore — e
la saldi (bruci) o la cancelli (restituisca) secondo l'esito dello
scambio.

**Si può fare tecnicamente.** Il ponte LNbits→LND del cantiere «Il
doppio wallet» (CANTIERI, fase 0) usa un macaroon dedicato con
`invoices` in lettura E scrittura (`root_key_id 1`): è esattamente il
permesso di `invoicesrpc` (`AddHoldInvoice`, `SettleInvoice`,
`CancelInvoice`). LNbits però NON espone hold invoice nella sua API,
quindi la strada non passa da LNbits ma da una chiamata diretta a LND
attraverso lo stesso ponte — e il server di Barattolo oggi verso LND ha
SOLO un macaroon di lettura (`LND_PONTE_MACAROON_LETTURA`,
`offchain:read`, `root_key_id 2`, CANTIERI «Guardiano del ponte LND»).
Quindi servirebbe **un terzo macaroon, di scrittura, sul VPS**, cioè un
segreto in più che chi buca il VPS usa per creare e SALDARE hold
invoice: è la stessa categoria della `LNBITS_ADMIN_KEY`, non peggio,
ma non è gratis.

**I rischi, in ordine di peso.**

1. **Custodia.** Oggi Barattolo nel P2P «non tocca un sat»
   (`config_esempio.py:620`): la hold di Mostro la tiene mostrod, e la
   disputa la decide un moderatore ma i sats li muove il coordinatore.
   Con una cauzione nostra, Barattolo tiene sats di chi compra sul
   proprio nodo e decide da solo quando bruciarli: è custodia, con le
   domande legali che l'escrow del mercatino ha già (MiCA a verbale nel
   backlog) e in più un potere di confisca. Il moderatore che oggi
   sceglie fra due esiti diventa uno che può anche incassare.
2. **Due stati da tenere allineati.** Lo scambio vive in mostrod; la
   cauzione vivrebbe nel nostro database (`p2p_scambi`) con la sua
   macchina a stati: quando si cancella (scambio concluso, annullato
   d'accordo, tornato nel libro), quando si salda (disputa persa da chi
   compra, abbandono dopo la presa), cosa succede se mostrod dice
   `canceled` mentre la nostra riga dice «in disputa». La patch 0007 ci
   racconta ogni passo, ma un avviso perso (Tor, il VPS giù) lascia una
   cauzione appesa: e una hold invoice appesa scade con l'HTLC, cioè
   torna da sola a chi compra dopo il suo cltv, che è il verso
   giusto in cui fallire ma è anche una cauzione che si può far scadere
   aspettando.
3. **Se Barattolo sparisce.** La hold di Mostro tiene i sats di chi
   vende sul nodo di Andrea; la cauzione starebbe sullo stesso nodo. Se
   Barattolo (il VPS) sparisce e il nodo no, le hold invoice restano
   appese fino al cltv e tornano a chi compra: **nessuno perde, nessuno
   può più far valere una disputa**. Se sparisce il nodo, spariscono
   insieme la cauzione e la hold del venditore, che è già il rischio di
   oggi (A VERBALE: «la garanzia siamo noi»). Quindi la cauzione fatta
   in casa non aggiunge un rischio di perdita, aggiunge **un pezzo di
   escrow che nessun client Mostro esterno conosce**: chi prende un
   nostro ordine da un'altra app non la paga, e il nostro client deve
   rifiutare il contanti verso un esterno (il giudice
   `_giudice_parte_p2p` del PayCode sa già dire «esterno»).
4. **Il valore del bond.** Se la cauzione si brucia a favore di
   Barattolo, Barattolo guadagna dalle dispute, che è un incentivo
   sbagliato. Se va alla controparte, è un incentivo a inventare
   dispute per incassarla. RoboSats risolve col «va al coordinatore ma
   il coordinatore ci mette la faccia» e Bisq con la DAO: da soli, la
   sola risposta pulita è **bruciarla davvero** (pagata a un indirizzo
   che nessuno controlla) o darla a chi ha vinto solo se ha la
   presenza firmata. È una decisione di Andrea, e va scritta prima.

**Il confronto secco.** Il bond di Mostro (3a) fa la stessa cosa dentro
il protocollo, con la stessa custodia che abbiamo già (mostrod sul
nodo), visibile a ogni client, e senza un segreto in più sul VPS. La
cauzione fatta in casa vale solo se il bond di Mostro non copre il caso
che ci serve, e la sezione 3a dice quanto lo copre.

## 4. Raccomandazione in dieci righe

**Prima del 10 ottobre — niente al nodo, niente patch, perimetro e
parole (un cantiere piccolo, solo client, server e testi):**
1. La leva **`P2P_MAX_EURO_CONTANTI`**, gemella di `P2P_MAX_EURO`,
   giudicata nel foglio quando il metodo è `Contanti`; il numero lo
   sceglie Andrea (fra i 150 e i 300 € sta nel solco di Bisq Easy e dei
   meetup di Peach), e sopra il foglio suggerisce di dividere (2d).
2. **La regola scritta** in tre posti (2a): la riga sotto il metodo nel
   foglio, la conferma «Hai contato i contanti davanti a chi ti ha
   pagato?» sul bottone di chi vende, e il paragrafo «Contanti di
   persona» in «Info P2P» con la regola di disputa di Hodl Hodl (2e:
   senza prova, i sats tornano a chi li ha bloccati).
3. **Il consiglio del meetup**: nel paragrafo, «vedetevi a un incontro
   bitcoin, o in un posto pubblico»; è la strada di Peach e costa una
   frase.

**Dopo il 10 ottobre, in quest'ordine:**
4. **La prova di presenza a QR** (2b): due gesti nel client, una rotta e
   una tabella, la riga per il moderatore. Da sola dà alla disputa il
   fatto che oggi non ha, senza custodia e senza il nodo.
5. **Il bond di Mostro acceso** (3a), `apply_to = "both"`,
   `slash_on_waiting_timeout = false`, in una finestra chiusa con
   `P2P_PROVA_IDS` e a importo basso, DOPO che il client sa ricevere
   `pay-bond-invoice` e rispondere a `bond_slashed`, dopo la rilettura
   della 0005 e con la direttiva `BondResolution` nel gesto del
   moderatore. La percentuale è di Andrea: l'1% è un caffè, RoboSats
   parte dal 3%.
6. **Il timeout che brucia** (`slash_on_waiting_timeout = true`) solo
   quando i bond sono provati: è la cura per «15 minuti sono pochi» già
   a verbale, e va da sola.
7. **La cauzione fatta in casa** (3b) NON si fa: stessa custodia con
   un segreto in più sul VPS, un pezzo di escrow che i client esterni
   non vedono, e un incentivo storto su chi incassa. Si riapre solo se
   il bond di Mostro si rivela inaccendibile per un motivo nuovo.
8. **I tetti per livello** (2c) quando i livelli contano anche gli
   scambi P2P: oggi misurano il mercatino, e un Maestro del banco che
   non ha mai scambiato sats non è un mercante di contanti.

## Fonti lette il 25 set 2026

- RoboSats: https://learn.robosats.org/docs/bonds/ ,
  https://learn.robosats.org/docs/escrow/ ,
  https://learn.robosats.org/docs/trade-pipeline/ ,
  https://learn.robosats.org/docs/limits/ ,
  https://learn.robosats.org/docs/disputes/ ,
  https://github.com/RoboSats/robosats/blob/main/docs/_pages/docs/03-understand/04-bonds.md ,
  `robosats/settings.py`, `api/models/order.py`, `.env-sample` e
  `frontend/static/federation.json` sul ramo main di
  https://github.com/RoboSats/robosats ; il F2F con la mappa in
  https://www.nobsbitcoin.com/robosats-v0-5-3/ .
- Bisq 1: https://bisq.wiki/Security_deposit ,
  https://bisq.wiki/Dispute_resolution , https://bisq.wiki/Arbitrator ,
  https://bisq.wiki/Table_of_penalties ,
  https://bisq.wiki/Face-to-face_(payment_method) ,
  https://bisq.wiki/Payment_methods (29 mag 2026),
  https://bisq.wiki/Cash_by_Mail , https://bisq.wiki/Account_limits ,
  https://bisq.community/t/new-rules-for-cash-by-mail-cbm-and-face-to-face-f2f-trades/11500 ,
  https://docs.bisq.network/trading-rules.html . Bisq Easy:
  https://bisq.wiki/Bisq_Easy , https://bisq.wiki/Reputation ,
  https://github.com/bisq-network/bisq2/discussions/2726 ,
  https://github.com/bisq-network/bisq2/releases .
- Hodl Hodl: https://hodlhodl.com/pages/faq , https://hodlhodl.com/faq ,
  https://accounts.hodlhodl.com/terms-of-service (la clausola «In
  person»), https://hodlhodl.com/blog/en/escrow-explained ,
  https://hodlhodl.com/api/docs ; i due post Medium sul metodo «In
  person» letti solo dagli estratti di ricerca (Medium risponde 403).
- Peach: https://peachbitcoin.com/blog/peach-at-a-crossroads/ (31 ago
  2026), https://peachbitcoin.com/faq/trading/ ,
  https://peachbitcoin.com/quick-start/ ,
  https://peachbitcoin.com/terms-and-conditions/ ,
  https://peachbitcoin.com/blog/how-to-buy-and-sell-bitcoin-with-cash-using-peach/ ,
  https://peachbitcoin.com/blog/peach-for-meetups/ ,
  https://docs.peachbitcoin.com/ (API: il cancel nei cash trade);
  fonte terza per l'1% agli organizzatori:
  https://typefully.com/teemupleb/peach-a-non-kyc-bitcoin-trading-app-explained-PfKSM7a .
- Mostro: https://mostro.network/protocol/new_sell_order.html ,
  https://mostro.network/protocol/order_event.html ,
  https://mostro.network/protocol/pay_bond_invoice.html ,
  https://mostro.network/protocol/bond_slashed.html ,
  https://mostro.network/protocol/dispute.html ,
  https://mostro.network/protocol/admin_settle_order.html ,
  https://mostro.network/protocol/admin_cancel_order.html ,
  https://mostro.network/protocol/user_rating.html ,
  https://mostro.network/protocol/key_management.html ; sul ramo main di
  https://github.com/MostroP2P/mostro : `settings.tpl.toml`,
  `docs/ANTI_ABUSE_BOND.md`, `src/scheduler.rs`, `src/app/dispute.rs`,
  `src/app/admin_settle.rs`, `src/app/admin_cancel.rs`,
  `src/app/rate_user.rs`, `src/nip33.rs`; le release v0.17.5 e
  v0.18.0-0.18.8 e la PR #964.
- In casa: `CLAUDE.md` («I TRE TIMER», «LE RISPOSTE DEL TEAM MOSTRO»),
  `docs/CANTIERI.md` («Il doppio wallet», «Guardiano del ponte LND»,
  «Le recensioni che contano in classifica», «La reputazione come
  evento NIP-85», «L'avviso "vi vedete" esce da tutti i fogli»),
  `deploy/mostro/README.md` (0005, 0007, il rollback dalla 0.18.8),
  `config_esempio.py` (le leve P2P), `server.py` e `miniapp.html` alle
  righe citate.
