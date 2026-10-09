# Guida P2P passo per passo — i testi esatti, per i tutorial video

Studio in sola lettura del 7 ottobre 2026, chiesto da Andrea per scrivere
i testi dei tutorial video del P2P. **Aggiornata lo stesso giorno** coi
testi del cantiere «I testi del P2P che confondevano» (i tredici punti di
«Notato strada facendo», in fondo, sono chiusi) e con gli avvisi
annullo/recapito dell'altra sessione. Letto sul codice di `origin/main` a
`566730c` (`miniapp.html`, `server.py`, `config_esempio.py`), non a
memoria; i valori che vivono FUORI dal codice (config del VPS, settings
del nodo) sono detti come tali, con la fonte.

Come si legge:

- **🧑 Chi** fa il gesto, **📱 Schermo** cosa vede, **⚠️ Storto** cosa può
  andare storto, col messaggio che compare.
- Fra «caporali» c'è il testo ESATTO, come lo scrive il codice. Dove il
  testo ha un pezzo variabile lo scrivo fra parentesi angolari:
  `«<nome>»`, `<cifra>`. Il nome dell'altra persona compare solo dove la
  pagina dello scambio lo mostra; altrimenti il testo dice «Chi vende» /
  «Chi compra».
- **✈️ Telegram** è l'avviso del bot (lo stesso testo va su Nostr a chi
  entra da lì). Arriva solo a chi ha gli avvisi P2P accesi, e MAI a chi
  ha fatto il gesto (tranne la garanzia pagata, che arriva a tutti e
  due: la si paga da un wallet esterno).
- Le parole in grassetto dei messaggi Telegram sono il `<b>` del bot.
- Le cifre in sats l'app le scrive col mezzo spazio fra le migliaia
  («500 000 sats»); gli euro con la virgola («50,00 €»).

Le leve che cambiano quel che si vede (valori al 7 ott 2026):

| Leva | Nel codice | In produzione |
|---|---|---|
| `P2P_ATTIVO` + `P2P_PROVA_IDS` | spento / vuota | acceso per i soli tester fino al lancio del 10 ott |
| `P2P_IN_VETRINA` (card P2P in home) | False | si accende il 10 ott 2026 |
| `fee` del coordinatore (letta viva) | — | 0,03 = 3% in tutto, 1,5% per parte (NODO-MOSTRO) |
| `P2P_COMMISSIONE_PERCENTO` (listino) | 2 | 4 = 2% per parte (PRODUZIONE) |
| `P2P_SCONTO_FEDELTA_PERCENTO` | 0 | 0,5 → 1% per parte a Pionieri e livello 5 (PRODUZIONE) |
| `max_order_amount` del coordinatore | — | 500 000 sats (NODO-MOSTRO) |
| `P2P_MAX_EURO` | 0 (spento) | da guardare nel pannello «⚙️ Stato delle leve» |
| `P2P_CONTANTI_MAX_EURO` | 250 € | 250 € se il config non dice altro |
| `BARATTOZON_MIN_EURO` | 25 € | 25 € se il config non dice altro |
| `P2P_CAUZIONE` | False | da guardare nel pannello (il nodo -bar6 la chiede) |
| `expiration_hours` (vita nel libro) | default client 168 h | 168 h = 7 giorni (NODO-MOSTRO) |
| `expiration_seconds` (tempo per passo) | default client 900 s | 900 s = 15 minuti |

Il glossario che i video devono usare, perché è quello dell'app:
**garanzia** (i sats bloccati), **recapito** (dove mandare gli euro),
**coordinatore** (Mostro, che fa girare Barattolo), **libro degli
ordini**, **premio/sconto** (lo scostamento dal prezzo di mercato).

---

## 1. Primo accesso al P2P

### Da dove si entra

1. **La barra in basso, voce «P2P»** (icona ₿).
   - 📱 Prima del lancio (leva spenta, o non sei fra i tester) si apre la
     pagina «Qualcosa di nuovo è in arrivo» / «Stiamo preparando
     qualcosa per i tuoi sats.» col bottone «🔔 Avvisami» (diventa
     «✓ Ti avviseremo»), il conto «Sii il primo» / «1 lo aspetta» /
     «<N> lo aspettano» e la promessa «Un solo messaggio, il giorno
     che arriva.»
   - 📱 Dopo il lancio si apre il **Libro ordini**, già sul lato
     «Compra BTC».
2. **La card in «Da scoprire»** della home: «Scambio P2P: in arrivo il
   10/10/26» fino al 10 ottobre; passata la data col P2P chiuso «in
   arrivo a breve»; col P2P aperto a tutti «Ora disponibile», e porta
   dritta al libro. Prima di «Ora disponibile» porta sempre alla
   pagina «Qualcosa di nuovo è in arrivo», anche ai tester.
3. **La fila «Scambi P2P» nella home** (con `P2P_IN_VETRINA` accesa):
   card con il volto di chi ha pubblicato e all'angolo lo **scudo
   Staff** o la **stellina** (vedi §11). Toccandola:
   - se sei entrato e il P2P vale per te, si apre il dettaglio
     dell'ordine (come dal libro);
   - altrimenti il foglio «Lo scambio P2P»: «Qui compri e vendi sats in
     euro direttamente con un'altra persona: chi compra manda gli euro
     (bonifico, Revolut, contanti…), chi vende manda i sats.» / «Finché
     gli euro non sono arrivati, i sats restano bloccati in un deposito
     di garanzia: chi vende non può riprenderseli a metà strada.» e poi
     «Gli scambi si fanno dall'app di Barattolo su Telegram.» col bottone
     «Apri Barattolo su Telegram», oppure «Per te non è ancora aperto:
     arriva a breve.» con «Ho capito».
   - La fila si spegne dal Profilo: «🔁 Scambi P2P nella home» —
     «Attivo» / «Spento».
4. **Il canale Telegram «Barattolo Vetrina»**: ogni ordine pubblicato
   esce come post «🔁 **Compra BTC su Barattolo**» (o «Vende BTC»), «💶
   <cifra> €», «🏷️ <premio>» (solo Barattozon), «💳 <metodo>», «🔒 Sats
   bloccati in un deposito di garanzia fino allo scambio», il link «🫙
   Apri lo Scambio P2P su Barattolo», la firma di chi l'ha pubblicato e
   «#p2p #barattolo».
5. L'indirizzo diretto `barattolo.store/p2p`.

### Dentro il P2P: la barra cambia

📱 Nel P2P la barra in basso diventa: **«Libro ordini»**, il **+**
tondo al centro, **«I miei scambi»** (col pallino quando qualcosa tocca
a te), **«Info P2P»**. In cima al libro i due lati **«Compra BTC»**
(verde) e **«Vendi BTC»** (rosso), con il logo che scuote, e il
banner della fee (vedi §12). Fuori dal libro il + diventa grigio e
riporta al libro su «Compra BTC».

### Il tour della prima volta

🧑 Parte da solo la prima volta che si apre il libro.
📱 Sei cartoline, coi bottoni «Salta» e «Avanti»:

1. «Qui scambi bitcoin ed euro direttamente con altre persone. Tu
   scegli quanto, come e a che prezzo.»
2. «Chi vende blocca i sats prima che tu paghi. Nessuno può scappare con
   i soldi: si sbloccano solo a scambio concluso.»
3. «SEPA, Revolut, Satispay, contanti — e con Barattozon i tuoi contanti
   dal tabaccaio diventano sats.»
4. «I recapiti ve li scambiate voi due, cifrati. Barattolo non li legge:
   lo dice la matematica, non una promessa.»
5. «Chi è onesto nel mercatino è onesto anche qui: la reputazione è una
   sola. Guarda le stelle prima di scambiare.»
6. (col marchio Barattozon) «Con Barattozon chi vende sats prepara il
   suo ordine Amazon da pagare in contanti alla cassa e ti passa il
   PayCode. Tu paghi quel PayCode dal tabaccaio, e i sats in garanzia
   si sbloccano verso di te.»

Il finale: per un attimo «Controllo il tuo account…», poi una di queste:

- Pioniere: «Sei un Pioniere!», la cifra grande «1%», «In beta la tua
  fee P2P è dell'1% invece dell'1,5%».
- Livello 5: «Sei al livello 5!» con la stessa cifra e la stessa nota.
- Tutti gli altri: «In beta la fee P2P è dell'1,5% per parte» e sotto
  «Dal livello 5 avrai uno sconto dello 0,5%».
- Senza fee letta: «La fee P2P la trovi nel conto dello scambio»; a fee
  zero: «In questo momento lo scambio non ha commissione».

Subito dopo, il **giro guidato** (sette fumetti che indicano le cose
vere sullo schermo, si salta come il tour):

1. su «Compra BTC»: «Vuoi **comprare** bitcoin? Parti da qui.»
2. su una card (se il libro è vuoto, una card finta con l'etichetta
   «Esempio»): «Qui trovi chi è disposto a venderti bitcoin. Tocca una
   card per vederla e prenderla.»
3. sul +: «Non trovi l'affare giusto? Pubblica qui il tuo annuncio e
   aspetta chi lo prende.»
4. su «Vendi BTC»: «Vuoi **vendere** bitcoin? Da qui.»
5. su una card: «Qui ci sono gli annunci di chi vuole comprare i tuoi
   bitcoin.»
6. sul +: «Pubblica il tuo annuncio di vendita e aspetta che qualcuno lo
   prenda.»
7. sul logo Barattozon sotto il +: «**Barattozon**: ti pagano in
   contanti l'ordine Amazon, tu dai i sats. Trascina il + giù.» (qui il
   + si può trascinare davvero).

### Telegram o Nostr: chi sei, qui dentro

- **Da Telegram** 🧑 non c'è niente da creare: il **profilo di
  scambio** lo ricava il server dal tuo account, ed è lo stesso dal bot,
  dal sito e dall'app. 📱 Lo si guarda da «🔐 Il patto sui tuoi dati, per
  intero» (fondo di «Info P2P») → «👤 Il tuo profilo di scambio»: foglio
  «👤 Il tuo profilo di scambio» con «Profilo attivo dal <data>.»,
  «Questo profilo **torna da solo** ogni volta che entri, su qualunque
  dispositivo: non c'è niente da salvare. Il codice segreto serve solo
  se vuoi portarlo fuori da Barattolo.», i bottoni «🔑 Mostra il codice
  segreto» (poi «📋 Copia il codice segreto», «✓ L'ho salvato») e «🗑
  Dimentica il profilo su questo dispositivo». Prima del primo scambio:
  «Non hai ancora un profilo di scambio: nasce da solo al primo scambio,
  legato al tuo account, e le recensioni che guadagni restano attaccate
  a lui.»
- **Dal sito senza essere entrato** 🧑 tocca una card o il +.
  📱 Foglio «🫙 Ti aspettiamo su Telegram» con «Per scambiare sats in
  euro con altre persone serve un account: il tuo profilo di scambio
  nasce qui dentro, e i sats restano custoditi in garanzia fino alla
  fine dello scambio.», il bottone per il bot e «…o entra con Nostr».
  Dall'indirizzo .onion: «🧅 Entra con la tua chiave» e «Entra con
  Nostr».
- **Con una chiave Nostr** 🧑 quando PRENDI un ordine resti anonimo.
  📱 Nel dettaglio: «🕶️ Tu resti anonimo: sei entrato con un profilo
  senza nome, e chi ha pubblicato non saprà chi sei. Il suo profilo
  invece lo vedi qui sopra. Se vuoi farti riconoscere — e potervi
  recensire — c'è l'interruttore nel cassetto «🔔 Avvisi».» Nel
  cassetto «🔔 Avvisi» del Profilo: «👤 Fatti riconoscere negli scambi»
  — «Se lo accendi, quando prendi un ordine l'altra parte vede il tuo
  profilo e potete recensirvi; se resta spento, resti invisibile e su
  quegli scambi non ci sono recensioni.» — «Spento» / «Attivo».
  Toast: «👤 Da ora chi scambia con te ti vede, e potete recensirvi» /
  «Da ora le tue prese non vengono annotate (gli scambi già presi
  restano)». Chi entra con Nostr e PUBBLICA si mostra comunque col nome
  e la foto della sua chiave. L'interruttore chi entra da Telegram non
  lo vede.
- **Gli avvisi**, per tutti, nel cassetto «🔔 Avvisi»: «⚡ Avvisi sugli
  scambi P2P» — «Quando il tuo ordine viene preso, quando lo scambio si
  chiude e quando tocca a te. Spenti, non ti scriviamo nulla dello
  scambio.» — «Attivi» / «Spenti». Toast: «⚡ Avvisi sugli scambi
  attivi» / «Avvisi sugli scambi spenti: non ti scriviamo più».

### Il wallet Lightning

Il P2P non ha un wallet suo: serve un **wallet Lightning esterno**.

- **Per bloccare i sats (chi vende) o la cauzione (chi prende in
  contanti)**: si paga una «richiesta» dal proprio wallet. 📱 Il foglio
  ha il QR, la richiesta scritta, la scadenza col bottone «⚡ Apri nel
  wallet» e «📋 Copia la richiesta» (toast «Richiesta di pagamento
  copiata 📋»). Si chiude da solo quando il pagamento arriva: «non c'è
  niente da confermare».
- **Per ricevere i sats (chi compra)**: l'app consiglia l'**indirizzo
  Lightning** (quello con la @), oppure una fattura. Se nel Profilo hai
  salvato l'indirizzo degli incassi compare «⚡ Usa l'indirizzo dei
  tuoi incassi: <indirizzo>». Se hai collegato un wallet (NWC) che sa
  fare fatture, la fattura la chiede l'app da sola: «⚡ Chiedo la
  fattura al wallet…» → «⚡ Fattura fatta dal wallet e inviata ✅».
- ⚠️ **Wallet of Satoshi**: il suo indirizzo non passa la verifica.
  📱 «⚠️ Il tuo indirizzo Wallet of Satoshi qui non funziona: incolla una
  fattura dal tuo wallet.» (La fattura di Wallet of Satoshi passa: non
  passa solo il suo indirizzo.) È l'unico avviso su Wallet of Satoshi
  che vede: la riga generica dei due fogli, in quel caso, non compare.

⚠️ Storto all'ingresso: «Nel demo si guarda soltanto: gli scambi veri
vivono nell'app 🔁»; «Rete assente: riprova»; «Non ci sono riuscito,
riprova».

---

## 2. Comprare BTC

### 2a. Il libro, lato «Compra BTC»

🧑 Chi compra tocca «Compra BTC» (è già lì all'ingresso).
📱 Ogni card dice, dall'alto:

- «Invia 50 €» (la cifra grande) e «Ricevi ≈ 72 000 sats» (la ≈ dice
  che è una stima al cambio di adesso; senza ≈ se i sats sono fissati);
- l'anello della scadenza (se ci passi sopra: «scade fra 3 g», «scade
  fra 5 h», «scade fra 12 min»);
- il cartellino del prezzo: «al prezzo di mercato», oppure «<N>% più
  conveniente» (verde) / «<N>% meno conveniente», e dal 10% «⚡ Ottimo
  affare», oltre il 15% «⚡⚡ Super affare»;
- i metodi: «💳 Revolut, SEPA» (Barattozon col suo logo);
- la reputazione di chi ha pubblicato: stella, media e numero di
  recensioni, «★ 4,9 · 👤 24»;
- sul proprio ordine: «È il tuo ordine — tocca per aprirlo».

Ordinamento (in cima): «Recenti» / «Convenienza» / «Più grandi» / «Più
piccoli». C'è anche un «Filtro». Accanto alla levetta del tema, sulla
stessa riga, la campanella 🔔 (dal 9 ott 2026; piena e arancio se gli
avvisi sono accesi, vuota se spenti): apre un foglio dal basso con, in
cima, il solo interruttore «Avvisami dei nuovi ordini P2P»
(Spenti/Attivi, spento di serie); sotto «Tipo di ordini» («Vendita BTC»
/ «Acquisto BTC» / «Barattozon», a scelta multipla) e «Convenienza»
(«Tutti» / «Solo se conveniente», e con la seconda le chip «A prezzo di
mercato o meglio» / «Almeno 2% meglio» / «Almeno 5% meglio») — grigie e
non toccabili finché l'interruttore è spento —; in fondo una riga sola,
«Arriva nella chat del bot Telegram» (chi entra da Telegram) o «Arriva
come messaggio Nostr» (chi entra con Nostr). Lo stesso blocco sta nel
cassetto «🔔 Avvisi» del Profilo. L'avviso che arriva: «🔔 2 nuovi ordini nel libro P2P /
vendita BTC: 2 / Il più conveniente per te: vendita BTC da 50,00 € via
SEPA, 3% più conveniente / 🫙 Apri il libro ordini».

### 2b. Ordine a importo fisso

1. 🧑 Chi compra tocca la card.
   📱 Foglio «**Stai comprando sats**» con, in ordine:
   - «Metodo di pagamento — come invii gli euro»: le pillole dei metodi.
     Con più metodi, finché non ne scegli uno, in rosso «Scegli con
     quale metodo vuoi inviare gli euro.» e il bottone spento;
   - (solo contanti) la regola e il tetto, vedi §6;
   - «Chi ha pubblicato quest'ordine»: media, recensioni, volto (il
     tocco porta al suo negozio);
   - «Tempo rimasto: <6g 23:47:17>»;
   - il **conto**: «Controvalore di **50 €**», poi (se c'è) «Premio
     richiesto dall'utente» o «Sconto offerto dall'utente» e
     «Subtotale», poi «Fee P2P **1,5%**» col cartellino («beta», «🌱
     Pioniere», «Lv. 5»), e in fondo «Ricevi <sats>» e «Totale da
     inviare 50 €»;
   - «Come funziona»: «Indichi dove ricevere i sats» → «Chi vende li
     mette in garanzia» → «Invii gli euro col metodo scelto» → «I sats
     arrivano a te»;
   - in fondo «Annulla» e «**Compra**».
2. 🧑 Tocca «Compra».
   📱 «Sto prendendo l'ordine…», poi si apre la **pagina dello scambio**
   («Nel dettaglio»): in alto il conto, sotto i quattro passi «Ordine
   preso / Di' dove ricevere i sats», «Sats bloccati / Chi vende li ha
   messi in garanzia», «Euro inviati / Al recapito che ti dà chi vende»,
   «Scambio concluso / I sats sono arrivati a te», e il riquadro dello
   stato: «**Dove vuoi i sats?**» «👉 tocca a te» «Indica il tuo
   indirizzo Lightning, o incolla una fattura: è lì che arriveranno alla
   fine dello scambio.»
   Toast: «⚡ Tocca a te: indica dove ricevere i sats». Bottone «💸
   Dove ricevere i sats».
   ✈️ A chi aveva pubblicato: «⚡ **Il tuo ordine è stato preso da
   <nome>!** Vendi <N> sats per 50,00 € via Revolut.» + «Appena chi
   compra indica dove ricevere i sats, tocca a te bloccare la
   garanzia.»
3. 🧑 Tocca «💸 Dove ricevere i sats».
   📱 Foglio «💸 Dove ricevere i sats»: «Riceverai **<N> sats**.» —
   «**⚡ Indirizzo Lightning (consigliato)** / Quello che finisce per
   @qualcosa. Non scade mai. / ⚠️ Wallet of Satoshi non funziona qui:
   con quello incolla una fattura.» — «**🧾 Oppure una fattura dal tuo
   wallet** / Senza importo, o di <N> sats esatti. Meglio se dura almeno
   un giorno: se scade prima te ne chiediamo un'altra.» — «📋 Copia la
   cifra: <N>» — campo
   «Dove vuoi ricevere i sats» (segnaposto «tuonome@wallet.com oppure
   lnbc…») — bottone «Invia». Hai 15 minuti.
   📱 Dopo: toast «Inviato ✅», stato «**Chi vende sta bloccando i
   sats**» «Appena sono al sicuro in garanzia te lo diciamo: da lì potrai
   inviare gli euro.»
   ✈️ A chi vende: «🔒 **Paga la garanzia: la richiesta è nell'app.**
   <nome> ha indicato dove ricevere i sats, ora tocca a te.»
4. Chi vende blocca i sats (§3, passo 2).
   ✈️ A chi compra: «🔒 **<nome> ha bloccato i sats in garanzia.** Appena
   ti indica dove inviare 50,00 €, tocca a te.»
   📱 Stato «**Sats in garanzia**». Il bottone «✅ Ho inviato gli euro» c'è
   ma è spento: «Si accende quando arriva il recapito. Te l'ha già dato
   per un'altra strada?» (il link apre «Hai già il recapito?» — «Qui
   dentro non è arrivato. Se chi vende ti ha detto dove mandare gli euro
   per un'altra strada, accendi il bottone — ma invia gli euro solo a un
   recapito che ti ha dato LUI, e solo perché questa pagina dice «Sats
   in garanzia».» — «Sì, ce l'ho»).
5. Chi vende manda il recapito (§3, passo 3).
   ✈️ «💶 **<nome> ti ha indicato dove inviare 50,00 €: tocca a te.**
   Apri Barattolo → P2P → I miei scambi: il recapito è lì, cifrato fra
   voi due. *Invia solo se la pagina dello scambio dice «Sats in
   garanzia»: lo dice il coordinatore, non chi vende.*»
   📱 Toast «💶 <nome> ti ha indicato dove inviare gli euro: tocca a te».
   Riquadro «💶 Dove mandare gli euro» col recapito (per esempio
   «Revolut: @mariorossi»), e lo stato «Sats in garanzia» «I sats sono al
   sicuro in garanzia. Ora manda gli euro al recapito indicato da chi
   vende, poi dillo qui.» Il bottone si accende.
6. 🧑 Manda gli euro FUORI dall'app (banca, Revolut…), poi tocca «✅ Ho
   inviato gli euro».
   📱 «Hai inviato gli euro?» — «Dillo solo dopo aver davvero mandato
   50,00 € con il metodo concordato. Chi vende lo vedrà e libererà i
   sats. Da qui non potrai più annullare: se qualcosa va storto, resta la
   disputa.» — «Sì, li ho inviati» → «Sto avvisando che hai pagato…» →
   «Fatto ✅». Stato «**Euro inviati**» «Hai detto di aver mandato gli
   euro: appena chi vende li vede, libera i sats.»
7. Chi vende libera (§3, passo 5).
   📱 Stato «**Sats liberati: in pagamento**» «Chi vende ha liberato i
   sats e il pagamento verso il tuo wallet è in corso. Se non riesce te lo
   diciamo qui, e potrai dare una fattura nuova.» Poi «**Scambio
   concluso**» «È andato tutto a buon fine.» e il riquadro «⭐ Lascia una
   recensione» (§11).
   ✈️ «✅ **Scambio concluso!** <N> sats in arrivo al tuo recapito.» +
   «Lascia una recensione: la trovi nella pagina dello scambio.»

### 2c. Ordine a intervallo («Scegli»)

1. 📱 La card dice «Invia da 20 a 100 €, scegli tu» e «Ricevi ≈ da <x> a
   <y> sats».
2. 🧑 Tocca la card. 📱 Al posto del conto «Scegli quanto vuoi inviare
   per vedere il dettaglio», e il bottone in fondo è arancione e dice
   **«Scegli»**.
3. 🧑 Tocca «Scegli». 📱 Foglio «**Quanto vuoi scambiare?**»: «Quest'offerta
   va da **20 €** a **100 €**: scegli tu quanto vuoi inviare.», campo
   «Quanti euro» (solo cifre intere), sotto la stima «Riceverai circa
   <N> sats.», bottone «Continua».
4. 📱 Di ritorno nel dettaglio: «Importo scelto: **50 €** (da 20 a 100)»
   col bottoncino «Cambia», il conto vero sulla cifra scelta, e il
   bottone torna «**Compra**». Da qui è uguale al fisso (2b dal passo 2).
5. Nella pagina dello scambio, finché la cifra non è fissata, il conto
   dice «L'importo lo sceglie chi prende: il dettaglio compare dopo la
   presa».

### ⚠️ Cosa può andare storto (comprando)

- Fuori dalla fascia: toast «Scegli una cifra fra 20 e 100 €.»
- Contanti sopra il tetto: «In contanti di persona il massimo è 250 €
  per scambio: sopra, si divide in più ordini»
- Ordine sparito: «Quest'ordine non c'è più: aggiorna il libro»
- Il tuo ordine: «È il tuo ordine: non puoi prenderlo» (e nel dettaglio
  «È il tuo ordine: l'hai pubblicato tu, e non si può prendere.» con
  solo «Indietro»).
- La presa non risponde: stato «**Nessuna risposta**» «La risposta non è
  arrivata. Puoi riprovare: se l'ordine è ancora libero, viene riservato
  a te.» col bottone «↻ Riprova»; varianti «La risposta sta tardando»
  («…Resta su questa pagina: se arriva si aggiorna da sola…») e «Il
  messaggio non è partito» («Nessuno ha preso in consegna la
  richiesta…»). Rifiutata: «**Ordine non preso**» «La richiesta non è
  stata accettata.»
- Errori nel foglio dei sats: «Serve un indirizzo o una richiesta di
  pagamento.»; «Questa richiesta di pagamento non si legge: controlla di
  averla copiata tutta.»; «La richiesta è di <x> sats, ma ne devi
  ricevere <y>. Rifalla dell'importo esatto, oppure lascia l'importo
  libero.»; «Questa richiesta scade fra <n> minuti, e viene accettata
  solo se vale ancora più di <m> minuti quando arriva…»; «Non sembra un
  indirizzo Lightning né una richiesta di pagamento.»; «Non sono
  riuscito a verificare questo indirizzo: usa una fattura del tuo
  wallet.»
- Non dai il recapito sats in 15 minuti: ✈️ «🔄 **Non hai proseguito in
  tempo:** l'ordine è tornato in vetrina. Se ti interessa ancora, puoi
  riprenderlo.» Nell'app: «Il giro si è chiuso senza garanzia: l'ordine
  è tornato nel libro».
- Il pagamento dei sats non passa: ✈️ «⚠️ **Il pagamento dei sats non è
  passato** (<motivo>): apri «Dove ricevere i sats» e dai una fattura
  nuova. *I sats restano fermi per te finché il pagamento non passa.*»
  (motivi: «non si è trovata una strada fino al tuo wallet», «il tempo è
  scaduto», «sul nodo mancava liquidità in quel momento», «la fattura non
  è più valida»). 📱 Toast «⚠️ Il pagamento dei tuoi sats non è riuscito:
  serve una fattura nuova», stato «**Serve una fattura nuova**», bottone
  «⚡ Dai una fattura nuova», foglio «⚡ Una fattura nuova» con «⚠️ Il
  pagamento dei tuoi sats non è riuscito.» e la causa («**la fattura che
  avevi dato è scaduta**…» oppure «…di solito vuol dire che il pagamento
  non ha trovato una strada fino al tuo wallet.»), poi «Incolla una
  fattura dal tuo wallet, senza importo o di <N> sats esatti. La paghiamo
  subito.» / «⚠️ Wallet of Satoshi: va bene la fattura, non
  l'indirizzo.» — «📋 Copia la cifra: <N>» — campo — «Invia». In «Sats
  liberati» c'è anche «⚡ I sats non arrivano? Dai una fattura nuova»:
  stesso foglio, con in cima «Se i sats non ti sono arrivati, qui puoi
  dare una richiesta di pagamento nuova.»
- Pagamento che si ritenta: «**Pagamento non riuscito**» «L'invio dei
  sats si riprova da solo. Se non riesce potrai indicare un altro
  indirizzo.»

---

## 3. Vendere BTC

1. 🧑 Chi vende tocca «**Vendi BTC**». 📱 Card rosse di chi vuole comprare:
   «Ricevi 50 €» e «Invia ≈ <N> sats». Tocca una card: foglio «**Stai
   vendendo sats**», «Metodo di pagamento — come ricevi gli euro», il
   conto (in fondo «Invia <sats>» e «Ricevi 50 €»), «Come funziona»:
   «Metti i sats in garanzia» → «Ricevi gli euro col metodo scelto» →
   «Controlli che siano arrivati» → «Liberi i sats a chi compra»
   (contanti: «Ricevi i contanti di persona» → «Li conti» → «Liberi i
   sats sul posto»), bottone «**Vendi**».
2. 🧑 Tocca «Vendi». 📱 «Sto preparando la garanzia…», poi toast «⚡ Tocca a
   te: blocca i sats in garanzia», passi «Ordine preso / Invia i sats»,
   «Sats bloccati / Restano in garanzia fino alla fine», «Euro inviati /
   Al recapito che hai indicato», «Scambio concluso / I sats sono arrivati
   al compratore», stato «**Blocca i sats**» «Paga la richiesta: i sats
   restano bloccati in garanzia e non escono finché non li liberi tu.»,
   bottone «🔒 Blocca i sats».
   🧑 Lo tocca. 📱 Foglio «🔒 Blocca i sats»: «Paga **<N> sats** dal tuo
   wallet: i sats restano **bloccati in garanzia** e non escono finché non
   li liberi tu. Hai circa 15 minuti.», QR, «⚡ Apri nel wallet», «📋
   Copia la richiesta», «Quando i sats sono in garanzia questo foglio si
   chiude da solo: non c'è niente da confermare.» Il numero da pagare è
   i sats PIÙ la tua metà di commissione.
   ✈️ A te, che hai pagato da fuori: «🔒 **Garanzia bloccata ✓:** appena
   chi compra indica dove ricevere i sats, tocca a te indicare dove
   ricevere gli euro.» (se l'ordine era tuo e chi compra ha già dato
   l'indirizzo: «🔒 **Garanzia bloccata ✓:** ora indica dove ricevere gli
   euro.»).
   ✈️ A chi aveva pubblicato (compra): «⚡ **Il tuo ordine è stato preso
   da <nome>!** Compri <N> sats per 50,00 € via SEPA.» + «Appena chi vende
   blocca la garanzia, tocca a te indicare dove ricevere i sats.»
3. **Il recapito.** 📱 A garanzia bloccata (e solo allora) compare «👉
   tocca a te» e il bottone «**💶 Indica dove ricevere gli euro**».
   🧑 Lo tocca. 📱 Foglio «**🤝 I vostri recapiti**»:
   - se l'ordine ha più metodi e la scelta non è ancora arrivata: «Con
     quale metodo ricevi gli euro» con le pillole; altrimenti «💶 Il
     metodo dello scambio è **<metodo>**»;
   - i campi del metodo (tabella in §5), già scritti se li avevi salvati
     in uno scambio prima: **non partono da soli**, li invii tu;
   - il bottone «💶 Invia a chi compra»;
   - sempre: «🔒 Lo vedete solo tu e l'altra persona, nemmeno Barattolo.
     Resta salvato su questo dispositivo per i prossimi scambi.» e «⚠️ Non
     scrivere password o codici. Quello che vi dite fuori da Barattolo non
     conta in caso di disputa.»
   🧑 Tocca «💶 Invia a chi compra». 📱 «Invio…» → toast «Recapito inviato
   a chi compra ✓». Il foglio ora dice «💶 Aggiorna il recapito» e sotto
   «✓ Recapito inviato. Se lo cambi, vale l'ultimo: cambialo solo se chi
   compra non ha ancora pagato.»
   **Cosa scrivere:** solo dove ricevere gli euro (IBAN e intestatario,
   RevTag, numero Satispay, email PayPal). Niente password, codici,
   messaggi.
   **Se lo cambio:** riapri il foglio col bottone «🤝 I vostri recapiti» della pagina dello
   scambio (compare a chi vende dopo il primo invio),
   correggi e tocca «💶 Aggiorna il recapito». Vale l'ultimo: nella pagina
   di chi compra il riquadro cambia, e gli arriva ✈️ «📮 **<nome> ha
   aggiornato il recapito.** Controlla il nuovo prima di inviare gli
   euro.» — e se chi compra ha già segnato gli euro come inviati: «📮
   **<nome> ha aggiornato il recapito dopo che hai segnato gli euro come
   inviati.** Se li hai già inviati al recapito precedente, scrivilo
   nella chat dello scambio: non inviarli una seconda volta.» Ogni cambio
   avvisa, fino a **dieci** avvisi per scambio; lo stesso recapito
   rimandato uguale non riavvisa.
4. 📱 Stato «**Sats in garanzia**» «I tuoi sats sono bloccati. Aspetta che
   chi compra mandi gli euro.»
   ✈️ Quando chi compra dice di aver pagato: «💶 **<nome> dice di aver
   inviato 50,00 €:** controlla il conto e rilascia i sats. *Rilascia solo
   quando gli euro sono arrivati davvero.*»
   📱 Stato «**Euro inviati**» «Chi compra dice di aver mandato gli euro.
   Controlla di averli ricevuti: poi libera i sats.» e bottone «🔓 Libera
   i sats».
5. 🧑 Controlla la banca, poi tocca «🔓 Libera i sats».
   📱 «Liberi i sats?» — «Fallo solo se hai ricevuto 50,00 € davvero. I
   sats partono verso chi compra e non tornano indietro.» — «Sì, libero
   i sats» → «Sto liberando i sats…» → «Sats liberati ✅». Stato «**Sats in
   pagamento**» «Hai liberato i sats: sono in pagamento verso chi compra.»
   ✈️ Se dopo un minuto il pagamento non è ancora passato: «⏳ **Sats in
   pagamento.** Hai liberato i sats: sono in pagamento verso chi compra.
   *Quando il pagamento passa, te lo diciamo qui.*» (o la variante «Il
   pagamento verso chi compra non è passato. Chi compra deve dare una
   fattura nuova: non devi fare niente.»).
   ✈️ A pagamento passato: «✅ **Scambio concluso!** Hai venduto <N> sats
   per 50,00 €, in tutto <M> sats commissione compresa.» (+ l'invito
   alla recensione).

### ⚠️ Cosa può andare storto (vendendo)

- «La richiesta di pagamento non è ancora arrivata» (toast, se tocchi
  «🔒 Blocca i sats» troppo presto).
- Non blocchi in 15 minuti: se l'ordine era di un altro ✈️ «🔄 **Non hai
  proseguito in tempo:** l'ordine è tornato in vetrina…»; se era tuo ✈️
  «⏰ **Non hai proseguito in tempo:** il tuo ordine è stato annullato.
  Puoi ripubblicarlo quando vuoi.» All'altra persona: «🔄 **Chi aveva
  preso il tuo ordine non ha proseguito.** È tornato in vetrina: non devi
  fare niente.» oppure «⏰ **Chi aveva pubblicato l'ordine non ha
  proseguito in tempo:** lo scambio è annullato, non devi fare niente.»
  Nell'app: «Scambio annullato prima della garanzia: nessun sat si è
  mosso».
- Recapito: «Non si sa ancora con chi stai scambiando»; «Compila:
  <campo>»; «Questo IBAN non sembra completo: controllalo»; «Non è
  partito: <motivo>».
- Chi compra non dice niente per ore: per circa quattro giorni non
  succede niente da solo (vedi §9); si scrive o si apre una disputa.

---

## 4. Pubblicare un ordine

🧑 Dal libro, sul lato giusto («Compra BTC» = pubblico un ordine di
acquisto, «Vendi BTC» = di vendita), tocca il **+** verde o rosso (da
computer: la pillola «Pubblica» in alto).
📱 Foglio «**Vuoi comprare Bitcoin**» / «**Vuoi vendere Bitcoin**», con
le sezioni in quest'ordine:

1. «Seleziona la valuta con cui invierai» / «…riceverai»: «🇪🇺 EUR»
   (l'unica).
2. «Come vuoi inviare — puoi sceglierne più di uno» / «Come vuoi
   ricevere — puoi sceglierne più di uno»: la tendina «Seleziona metodi
   di pagamento», con le voci da spuntare (✓). Barattozon c'è solo
   vendendo, e da solo (§7). Coi contanti compare la regola: «💶
   **Contanti di persona** — al massimo **250 €** per scambio: sopra, si
   divide in più ordini. <regola> Vedetevi in un posto pubblico e di
   giorno — un bar, un incontro bitcoin —, contate le banconote insieme, e
   mai grosse cifre da soli.»
3. «Inserisci l'importo in EUR che vuoi inviare» / «…ricevere»: il campo
   «Importo». **Fisso o intervallo:** toccando il primo campo compare il
   secondo, «Importo massimo», preceduto da «a», con il suggerimento «💡
   Tocca il secondo campo solo se vuoi creare un ordine a intervallo».
   Lasciato vuoto = ordine a importo fisso; scritto = intervallo «da… a…».
   Solo euro interi (la virgola non si scrive). Se c'è un tetto: «Fase
   beta: max <cifra>».
4. «Tipo di prezzo» (con la ⓘ): «**Prezzo di mercato**» o «**Prezzo
   fisso**», con l'interruttore «Mercato». La ⓘ spiega: «• Scegli Prezzo di
   mercato se vuoi usare il prezzo che ha Bitcoin quando qualcuno prende
   la tua offerta.» / «• Scegli Prezzo fisso se vuoi definire tu
   l'importo esatto di sats che scambierai.» — «Ho capito».
5. Solo a prezzo fisso: «Inserisci la quantità di sats che vuoi comprare»
   / «…vendere», campo «Quantità di sats», e «A prezzo fisso il cambio lo
   decidi tu: chi prende paga gli euro che hai scritto per questi sats.»
   A prezzo fisso **niente intervallo**: «A prezzo fisso l'importo è uno
   solo: un ordine a intervallo non può fissare la quantità di sats.»
6. Solo a prezzo di mercato: «Premio (%)» (con la ⓘ) e il cursore da
   **−20%** a **+20%**, e sotto la nota che cambia col cursore: a zero
   «Vuoi comprare Bitcoin al prezzo di mercato: quello del momento in cui
   qualcuno prende l'offerta.»; comprando sopra zero «…chi vende riceve i
   tuoi euro e consegna **meno** sats. Un ordine più appetibile per chi
   vende.», sotto zero «…chi vende consegna **più** sats per i tuoi euro.
   Conviene a te, meno a chi vende.»; vendendo sopra zero «…consegni
   **meno** sats per gli stessi euro. Conviene a te, meno a chi compra.»,
   sotto zero «…consegni **più** sats per gli stessi euro. Un ordine più
   appetibile per chi compra.» La ⓘ: «Il premio è quanto ti scosti dal
   prezzo di mercato. Sopra lo zero passano meno sats a parità di euro;
   sotto lo zero ne passano di più. Più il tuo premio è generoso per chi
   legge, prima qualcuno prende l'offerta. A zero vale il prezzo di
   mercato del momento in cui l'offerta viene presa.»
7. «Quanto si può, e quanto costa»: per esempio «Al momento si accettano
   ordini fino a 500 000 sats — la fee P2P è dell'1,5% per parte» (a un
   Pioniere: «…la fee P2P è dell'1,5% per parte, e tu hai uno sconto
   dello 0,5%, quindi paghi l'1% di fee»).
8. Il bottone «**⚡ Pubblica ordine**».

🧑 Tocca «⚡ Pubblica ordine». 📱 «Sto pubblicando…» → «Ordine
pubblicato». Si apre la pagina del tuo ordine: «**Ordine pubblicato**»
«È nel libro: aspetta che qualcuno ti venda i sats. Puoi ritirarlo quando
vuoi, finché nessuno lo prende.» (vendendo: «…che qualcuno ti compri i
sats…»), passo 1 «Ordine pubblicato / Aspetta chi ti vende i sats», e il
bottone «✕ Annulla l'ordine». Nel libro la card ha «È il tuo ordine —
tocca per aprirlo», e l'ordine esce anche nel canale «Barattolo Vetrina»
col tuo nome.

Quando qualcuno lo prende: ✈️ «⚡ **Il tuo ordine è stato preso da
<nome>!** Compri/Vendi <N> sats per <cifra> via <metodo>.» con la frase
del passo dopo (vedi §2 e §3). Da qui lo scambio va come in §2 (se
compri) o §3 (se vendi), con una differenza: **chi ha preso fa sempre il
primo gesto**. Su un tuo ordine di vendita preso da chi compra, lui dà
l'indirizzo e poi tu blocchi la garanzia; su un tuo ordine di acquisto
preso da chi vende, lui blocca la garanzia e poi tu dai l'indirizzo.

### ⚠️ Cosa può andare storto (pubblicando)

La sezione col problema lampeggia e un toast dice cosa manca:

- «Scrivi l'importo in euro»; «L'importo massimo deve superare il primo»
- «Troppi: il massimo è <x> €»; «Troppi: il massimo è <x> sats»;
  «Troppo pochi: il minimo è <x> sats»; «Scrivi quanti sats»
- «Scegli almeno un metodo di pagamento»
- «In contanti di persona il massimo è 250 € per scambio: sopra, si
  divide in più ordini»
- «Il premio va da −20 a +20%, a numeri interi»
- «Aspetta un attimo: sto leggendo il cambio»
- Cambiando metodo con un importo già scritto: «<cifra> → senza
  Barattozon gli ordini sono in euro interi» (e il campo si svuota).
- La pubblicazione non risponde: «**Nessuna risposta**» «La risposta non è
  arrivata: l'ordine potrebbe non essere nel libro. Puoi riprovare a
  pubblicarlo con la stessa chiave: se era già stato registrato, te lo
  dice.» col bottone «↻ Riprova a pubblicare»; rifiutata: «**Ordine non
  pubblicato**» «La pubblicazione non è stata accettata.»; e il toast
  «Non si e' potuto pubblicare: <motivo>».

---

## 5. Metodi di pagamento

L'elenco è chiuso, nell'ordine dell'app: **SEPA**, **SEPA Instant**,
**Revolut**, **Satispay**, **PayPal**, **Contanti**, **Contanti al
tabacchino** (che nell'app si vede col logo **Barattozon**). Chi pubblica
ne sceglie uno o più; chi prende ne sceglie uno nel dettaglio. Gli euro
non passano da Barattolo: viaggiano fra le due persone.

Cosa chiede il foglio «🤝 I vostri recapiti» a chi vende, per metodo:

| Metodo | Campi (etichetta → esempio nel campo) | Cosa riceve chi compra |
|---|---|---|
| SEPA, SEPA Instant | «Intestatario (nome e cognome)» → «Mario Rossi»; «IBAN» → un IBAN italiano d'esempio; «Causale (facoltativa)» → «es. regalo Mario» (dal 9 ott 2026: al più 140 caratteri; le lettere accentate diventano da sole la lettera semplice, «caffè» → «caffe», e il campo mostra il testo convertito; restano solo lettere, numeri, spazi e . , - / ( ) ' + ? : — il resto, es. € ! «, si rifiuta dicendo quali togliere; non si ricorda: a ogni nuovo scambio nasce vuota, nome e IBAN restano ricordati) | «Bonifico SEPA / Intestatario: … / IBAN: …» e, solo se scritta, «/ Causale: …» (con SEPA Instant: «Bonifico SEPA Instant / …»); chi compra ha il «📋 Copia» su intestatario, IBAN e causale |
| Revolut | «Il tuo RevTag» → «@mariorossi» | «Revolut: @…» |
| Satispay | «Numero di telefono Satispay» → «333 1234567» | «Satispay: …» |
| PayPal | «Email o link paypal.me» → «mario@esempio.it» | «PayPal: …» |
| Contanti | «📍 Dove proponi di vedervi», «🕒 Quando» (§6) | l'appuntamento |
| Contanti al tabacchino | parte da solo, vedi §7 | il PayCode |
| un metodo che arriva da un'altra app | «Dove vuoi ricevere gli euro (<metodo>)» → «IBAN, @tag, numero…» | «<metodo>: …» |

Il bottone di chi compra cambia nome col metodo: «✅ Ho inviato gli
euro» (bonifico, Revolut, Satispay, PayPal), «✅ Ho consegnato i
contanti» (contanti di persona), «✅ Ho pagato al tabacchino»
(Barattozon).

---

## 6. Contanti di persona

### Prima: il tetto e la cauzione

- **Tetto**: al massimo **250 €** per scambio in contanti, per chi
  pubblica e per chi prende. In «Info P2P»: «**Il tetto:** al massimo
  **250 €** per scambio in contanti, sia per chi pubblica sia per chi
  prende. Sopra, si divide in più scambi: il rischio di ogni incontro si
  ferma lì.»
- **La regola**, ripetuta nel foglio Pubblica e nel dettaglio: a chi
  compra «Consegna i contanti solo quando chi vende preme «Libera i sats»
  davanti a te, e controlla che lo scambio risulti concluso prima di
  andare via.»; a chi vende «Conta i contanti davanti a chi ti paga, poi
  premi «Libera i sats» lì, davanti a lui: chi compra deve vedere lo
  scambio concluso prima di andare via.»
- **La cauzione** (solo se accesa: leva `P2P_CAUZIONE` E coordinatore
  che la chiede; sul nodo: 3% dei sats, almeno 1.000 sats, solo a chi
  PRENDE, solo col metodo «Contanti»):
  1. 📱 Nel dettaglio: «🔐 **La cauzione di chi prende.** Per prendere
     quest'ordine in contanti blocchi una piccola cauzione di circa
     **<N> sats** (il 3%, almeno 1 000 sats): resta nel tuo wallet e
     **torna a fine scambio**. La perdi solo se un moderatore decide che
     non ti sei presentato all'incontro. Finché non è bloccata, l'ordine
     resta nel libro e qualcun altro può prenderlo.» Il primo passo
     diventa «Blocchi la cauzione e indichi dove ricevere i sats» (o «…e
     metti i sats in garanzia»).
  2. 🧑 Prende l'ordine. 📱 Toast «🔐 Tocca a te: blocca la cauzione»,
     stato «**Blocca la cauzione**» «Paga la richiesta: è una piccola
     cauzione che resta in sospeso nel tuo wallet e torna a fine scambio.
     Finché non è bloccata l'ordine resta nel libro, e qualcun altro può
     prenderlo prima di te.», riquadro «🔐 Cauzione da bloccare: <N>
     sats…», bottone «🔐 Blocca la cauzione» → foglio «🔐 Blocca la
     cauzione» («…Resta in sospeso nel tuo wallet e **torna a fine
     scambio**; la perdi solo se un moderatore decide che non ti sei
     presentato. Hai circa <n> minuti: scaduta, l'ordine resta nel libro
     e va ripreso.»).
  3. ✈️ Pagata da fuori: «🔐 **Cauzione bloccata ✓:** ora indica dove
     ricevere i sats.» (o «…ora paga la garanzia, la richiesta è
     nell'app.»). 📱 «🔐 Cauzione bloccata: <N> sats, in sospeso nel tuo
     wallet. Torna a fine scambio.»
  4. ⚠️ Non pagata in tempo: «**La cauzione non è stata bloccata in
     tempo**» «La richiesta è scaduta e l'ordine è tornato nel libro:
     nessun sat si è mosso. Se ti interessa ancora, riprendilo.» col
     bottone «↻ Riprendi l'ordine»; toast «Chiuso prima che la cauzione
     fosse bloccata: nessun sat si è mosso»; «La richiesta è scaduta:
     riprendi l'ordine, ne arriva una nuova».
  5. A fine scambio: ✈️ «🔐 La cauzione che avevi bloccato torna nel tuo
     wallet.» 📱 «🔐 Cauzione restituita: <N> sats sono tornati nel tuo
     wallet.»
  Spenta, «Info P2P» dice: «**La cauzione di chi prende:** in questo
  momento non c'è: chi prende un ordine in contanti non blocca niente
  prima dell'incontro.»

### L'appuntamento

1. 🧑 Chi vende, a garanzia bloccata, vede «📍 **Indica dove e quando
   vedervi**» (al posto di «Indica dove ricevere gli euro»).
2. 📱 Foglio «🤝 I vostri recapiti» coi campi «📍 Dove proponi di vedervi»
   (esempio «Bar Sport, piazza Garibaldi…») e «🕒 Quando» (giorno e ora
   col selettore del telefono, entro una settimana). Mentre scrive
   arrivano indirizzi veri («Indirizzi da © OpenStreetMap»), e c'è «📍 Usa
   la mia posizione». Sotto il luogo, una di queste:
   - «🧭 Indirizzo riconosciuto: chi compra avrà «Apri nel navigatore».»
     (o «🧭 Il punto è la tua posizione di adesso…») con «Togli»;
   - «👆 Scegline uno e chi compra avrà «Apri nel navigatore». A mano va
     bene, ma senza link.»;
   - «✋ Indirizzo non riconosciuto: chi compra non avrà il link al
     navigatore. Scegline uno dai suggerimenti o usa la tua posizione.»
3. 🧑 Tocca «📍 Invia a chi compra». 📱 Toast «Appuntamento inviato a chi
   compra ✓»; poi il bottone diventa «📍 Aggiorna l'appuntamento» con
   «✓ Appuntamento inviato. Se lo cambi, vale l'ultimo e chi compra viene
   avvisato.» e «🔒 Lo vedete solo tu e l'altra persona, nemmeno
   Barattolo. Il luogo resta salvato su questo dispositivo, l'ora no.»
4. Chi compra: ✈️ «📍 **<nome> ti ha indicato dove e quando vedervi.**
   Apri Barattolo → P2P → I miei scambi: giorno, ora e luogo sono lì,
   cifrati fra voi due. *Vai all'incontro solo se la pagina dello scambio
   dice «Sats in garanzia»: lo dice il coordinatore, non chi vende.*» Se
   cambia: «🕒 **<nome> ha cambiato l'appuntamento.**» (stessa coda).
   📱 In cima alla pagina: «🕒 Appuntamento: **<giorno, ora>**», «📍
   <luogo>», «🧭 Apri nel navigatore» (o «Indirizzo scritto a mano: niente
   link al navigatore. Se non lo trovi, chiedi a chi vende.»). Chi vende
   lì ha «✏️ Cambia l'appuntamento».
5. ⚠️ Errori: «Scegli giorno e ora dell'incontro»; «L'ora dell'incontro è
   già passata: scegline una nuova»; «Fissa l'incontro entro una
   settimana»; «I suggerimenti non rispondono: puoi scrivere l'indirizzo a
   mano.»

### All'incontro: «📍 Sono qui»

📱 Il riquadro dei contanti: in alto la regola breve («💶 Consegna i
contanti solo quando chi vende preme «Libera i sats» davanti a te.» / «💶
Conta i contanti davanti a chi ti paga, poi premi «Libera i sats» lì,
davanti a lui.»), poi «**1 📍 Sono qui** quando arrivi · facoltativo» con
«Registra ora e posizione: facoltativo, ma aiuta a risolvere le
dispute.» e il bottone «📍 Sono qui», le due righe delle presenze, la
regola della disputa e «Consigli per l'incontro», poi «2 Poi, al momento
di pagare» (chi compra) / «2 Poi, contati i contanti» (chi vende).

1. 🧑 Ognuno, arrivato, tocca «📍 Sono qui» dal suo telefono (il telefono
   chiede la posizione: si può dire di no). 📱 «Registro ora e posizione…»
   → toast «📍 Presenza registrata alle <ora>» oppure «…, SENZA posizione:
   il telefono non l'ha data». Righe: «✓ Hai segnato la presenza alle
   <ora> · con la posizione» / «Chi vende non ha ancora segnato la
   presenza» → «✓ Chi vende ha segnato la presenza alle <ora>». Poi c'è
   «📍 Segna di nuovo». L'altro vede l'ora, mai la posizione.
2. 🧑 Chi compra consegna e tocca «✅ Ho consegnato i contanti». 📱 «Hai
   consegnato i contanti?» — «Dillo quando consegni 50,00 € a chi vende,
   lì di persona. <regola> Da qui non potrai più annullare: se qualcosa va
   storto, resta la disputa.» — «Sì, li ho consegnati». Se non aveva
   segnato la presenza, prima: «📍 Non hai segnato «Sono qui». Se chi vende
   dice di non aver ricevuto i contanti e non c'è la prova d'incontro, in
   disputa si dà ragione a chi vende. Puoi tornare indietro e segnarlo
   adesso, o proseguire.» con «Indietro». Stato «**Contanti consegnati**»
   «Hai detto di aver consegnato i contanti: chi vende li conta e libera i
   sats davanti a te.»
3. Chi vende: ✈️ «💶 **<nome> dice di averti consegnato 50,00 € in
   contanti:** contali e libera i sats, lì di persona. *Libera solo dopo
   averli contati, davanti a chi ti paga.*» 🧑 Conta, tocca «🔓 Libera i
   sats». 📱 «Hai contato i contanti davanti a chi ti ha pagato?» — «Libera
   i sats solo lì, davanti a chi ti ha dato 50,00 € in contanti, dopo
   averli contati insieme. I sats partono verso chi compra e non tornano
   indietro.» — «Sì, li ho contati: libero i sats».

### Se uno non si presenta

- Non c'è nessun gesto automatico: i sats restano in garanzia (§9).
  Le strade sono l'**annullo d'accordo** (§8) o la **disputa** (§10).
- In disputa vale la regola scritta prima: «Se chi vende dice di non aver
  ricevuto i contanti e non c'è la prova d'incontro, in disputa si dà
  ragione a chi vende. Ma se chi compra ha segnato la presenza all'ora e
  vicino al luogo dell'appuntamento e chi vende no, la disputa non va in
  automatico a chi vende: decide il moderatore.»
- Con la cauzione accesa il moderatore può **bruciarla** a chi non si è
  presentato. ✈️ A lui: «🔐 **La tua cauzione è stata bruciata: <N>
  sats.** Un moderatore ha deciso che non ti sei presentato all'incontro:
  metà va a <l'altro>, metà al servizio.» All'altro: «⚖️ **Metà della
  cauzione di <l'altro> è tua: <N> sats.** Apri la pagina dello scambio
  nell'app e dai una fattura di quell'importo entro quindici giorni: dopo,
  il servizio se la tiene.» 📱 Riquadro «⚖️ Metà della cauzione
  dell'altra persona è tua: <N> sats. Dai una fattura entro il <data>:
  dopo, il servizio se la tiene.» con «⚡ Incassa <N> sats» → foglio «⚖️
  Incassa la cauzione» (fattura di quell'importo esatto; errori «Questa
  non sembra una fattura Lightning», «La fattura deve essere di <N> sats
  esatti: questa è di <M>») → «⚡ Fattura inviata ✅», poi «⚖️ Cauzione
  incassata: <N> sats sono arrivati nel tuo wallet.»

---

## 7. Barattozon (Contanti al tabacchino)

Il metodo in una riga, come lo dice l'app a chi vende: «Con Barattozon
fai pagare in contanti alla cassa del tabacchino un tuo ordine Amazon:
chi lo paga riceve cifrati codice, importo e scadenza appena prende
l'ordine, e paga solo quando la pagina dice «Sats in garanzia». Non vede
nome, indirizzo né cosa hai comprato. Per pagare non serve alcun
documento. Chi paga tiene lo scontrino in caso di
disputa.»

### 7a. Chi pubblica (vende sats)

1. 🧑 Fa un ordine su Amazon con «paga in contanti nel punto vendita».
   Amazon manda una mail con PayCode (nove cifre), importo coi centesimi
   e scadenza (72 ore). Non vale per Amazon Warehouse, contenuti
   digitali, oro, abbonamenti a Prime, buoni regalo e acquisti 1-Click.
2. 🧑 Nel libro, **solo su «Vendi BTC»**, entra in Barattozon in uno di
   tre modi: tocca la linguetta col logo Barattozon sotto il +; tiene
   premuto il + e lo **trascina giù** sul logo (la linguetta si illumina,
   si lascia lì sopra); oppure apre il + e sceglie «Contanti al
   tabacchino» fra i metodi (gli altri metodi si spengono: «— col
   tabacchino, uno solo»).
   📱 Il titolo del foglio diventa il logo Barattozon. Prima il «Tipo di
   prezzo», con la nota: a mercato «A prezzo di mercato i sats si
   calcolano quando qualcuno prende l'ordine, col premio del passo 4. Per
   quel calcolo l'importo è arrotondato per eccesso all'euro intero: la
   differenza la metti tu.»; a fisso «A prezzo fisso i sats li calcoli
   adesso, sui centesimi esatti e al cambio di oggi: chi prende li vede
   fermi, e la convenienza si muove col bitcoin.»
   Poi il percorso, con la testata «Passo 1 di 4 · Il PayCode» (e via
   così) e il riquadro «🧾 …» qui sopra:
   - **1 Il PayCode** — campo per le nove cifre; «Nove cifre, coi
     trattini o senza. È il codice che chi compra dà alla cassa del
     tabacchino: viaggia cifrato, e lo legge solo chi prende l'ordine.» e
     la riga delle esclusioni Amazon.
   - **2 L'importo esatto** — coi centesimi; «Quello scritto sulla mail
     di Amazon, coi centesimi: al tabacchino si paga esattamente quella
     cifra. Amazon accetta i contanti fino a **999 €** per ordine, senza
     commissione; un PayCode Barattozon vale almeno **25 €**.»
   - **3 Quando scade il PayCode** — una riga, «Scegli quando scade»
     (poi «Scade lunedì 12 ottobre alle 14:30»), che al tocco apre dal
     basso il foglio «⏳ Quando scade il PayCode» (dal 9 ott 2026, al
     posto del selettore di sistema): «Copiala dalla mail di Amazon:
     deve stare fra un'ora e 72 ore da adesso. Prima il giorno, poi
     l'ora e i minuti.», le chip del **Giorno** («Oggi», «Domani», poi
     «dom 11 ott», «lun 12 ott»), la griglia delle **Ore** (00-23) e
     quella dei **Minuti** (di cinque in cinque; le celle fuori dalla
     finestra sono spente), la riga «Scade lunedì 12 ottobre alle 14:30
     · fra 2 giorni e 23 ore», i bottoni «Conferma» e «Annulla». Sotto
     la riga resta l'aiuto: «⏳ Amazon dà 72 ore dal checkout: copia la
     scadenza dalla mail. Deve stare fra un'ora e 72 ore da adesso. Nel
     libro l'ordine resta fino a **due ore prima** di quella scadenza,
     per lasciare a chi paga il tempo di andare al tabacchino; poi esce
     da solo.»
   - **4 Il premio** — cursore da −20 a +20 (si può anche scrivere a
     mano, toccando la cifra con la matita), e la riga che fa il conto:
     «Chi paga al tabacchino riceve circa <N> sats al cambio di adesso,
     cioè il 5% in meno del cambio: risparmi tu. La cifra esatta si fissa
     alla presa, su 26 €.» (a premio negativo «…in più del cambio: lo
     paghi tu per la comodità.»; a zero «…, il cambio pieno.»). Sotto: «Da
     −20 a +20%, a numeri interi: il segno decide il verso. **Premio più
     basso = più conveniente per chi paga = più probabile che qualcuno lo
     prenda in tempo.**»
   - Fatti i quattro: «Tutti e quattro i passi sono fatti: rileggi e
     pubblica.» Ogni passo fatto ha il tondo col ✓.
3. **La ✕ rossa**: se il valore del passo 2 o del passo 3 è sbagliato, il
   tondo col numero diventa **rosso con la ✕** e sotto il campo compare
   la frase in rosso. Per l'importo sotto i 25 €: «Un PayCode Barattozon
   vale almeno 25 €: sotto non si pubblica». Altre: «Amazon accetta il
   pagamento in contanti fino a 999 € per ordine»; «Scrivi l'importo
   dell'ordine Amazon, coi centesimi se servono»; «La scadenza è già
   passata: serve un PayCode nuovo»; «Scade troppo presto: serve almeno
   un'ora perché qualcuno vada al tabacchino»; «Troppo lontana: un PayCode
   vale al massimo 72 ore»; «Troppo lontana: la garanzia copre al massimo
   <n> ore da adesso». Mentre si scrive la ✕ aspetta: compare dopo circa
   0,7 secondi di pausa, o uscendo dal campo; corretto il valore, sparisce.
4. 🧑 Tocca «[logo] **Rileggi e pubblica**». 📱 Riepilogo «**Il tuo PayCode,
   in breve**»: «PayCode: …», «Importo: 25,47 €», «Scade il: …», «Prezzo:
   di mercato, sats calcolati alla presa» (o «fisso, sats calcolati
   adesso»), «Premio: …», la riga del conto, «Per il calcolo dei sats
   l'importo è arrotondato a 26 €: la differenza di 0,53 € la metti tu.»
   (a fisso: «Tu blocchi <N> sats in garanzia, e l'ordine Amazon lo paga
   chi li riceve.»), «Nel libro fino alle <ora> del <giorno>, poi esce da
   solo.» Bottone «Pubblica». Poi come §4.
5. Quando qualcuno prende: ✈️ «🧾 **Il tuo PayCode è stato preso da
   <nome>!** Vendi <N> sats per 25,47 €.» + il passo dopo. Il PayCode
   **parte da solo** verso chi ha preso, appena il server riconosce chi è:
   toast «🧾 PayCode, importo e scadenza sono partiti verso chi compra ✓».
   ⚠️ Se non lo riconosce: «🧾 Il PayCode non è partito da solo: non
   sappiamo ancora chi ha preso» (o «…chi ha preso usa un'app esterna a
   Barattolo») e il bottone «🧾 Mandalo da qui lo stesso» → «Mandare il
   PayCode a mano?».
6. Si blocca la garanzia come in §3. Stato «**Sats in garanzia**» «I tuoi
   sats sono bloccati. Chi compra ha il PayCode: aspetta che vada al
   tabacchino e segni «pagato».»
7. Quando chi compra segna «pagato»: ✈️ «🧾 **PayCode pagato: controlla su
   Amazon.** <nome> dice di aver pagato 25,47 € in contanti al
   tabacchino. Apri il tuo ordine su Amazon: se risulta saldato libera i
   sats, se no apri una disputa — dalla pagina dello scambio. *Non esiste
   una conferma automatica e i sats non si liberano da soli. Hai 24 ore a
   vista: te lo ricordiamo qui.*» 📱 Stato «**PayCode pagato: controlla su
   Amazon**» e il riquadro «🔎 Controlla su Amazon che l'ordine risulti
   pagato» con «Decidi entro le <ora> del <giorno>: <conto alla
   rovescia>» e i due bottoni «✅ **Risulta pagato: libera i sats**» e
   «🚨 **Non risulta pagato: apri una disputa**», più «Se non fai niente,
   i sats restano in garanzia e chi ha pagato può aprire lui la disputa: a
   decidere sarà un moderatore, e lo scontrino conta. Ti ricordiamo su
   Telegram dopo un'ora, sei ore e venti ore.»
   ✈️ I tre promemoria (dopo 1 h, 6 h, 20 h, solo se lo scambio è fermo):
   «🧾 Promemoria: un'ora fa chi compra ha detto di aver pagato il tuo
   PayCode al tabacchino…», «🧾 Sono passate sei ore…», «⏰ Venti ore da
   quando chi compra ha detto di aver pagato il tuo PayCode: le 24 ore
   stanno finendo…».
   🧑 Libera: «Liberi i sats?» — «Fallo solo se su Amazon il tuo ordine da
   25,47 € risulta pagato davvero. I sats partono verso chi compra e non
   tornano indietro.» In «I miei scambi» resta «Amazon pagato: 25,47 € per
   <N> sats».

### 7b. Chi prende (compra sats pagando il PayCode)

1. 📱 Su «Compra BTC» la card ha il logo Barattozon. Nel dettaglio
   («Stai comprando sats») c'è «📖 Come funziona, passo per passo» (porta
   a «Info P2P») e, se mancano meno di sei ore: «⏳ Occhio al tempo:
   questo ordine esce dal libro fra meno di sei ore (o «…di un'ora»), e il
   PayCode scade circa due ore dopo. Devi fare in tempo ad andare al
   tabacchino e pagare: se il PayCode scade prima, lo scambio va annullato
   e non ricevi i sats.» Passi: «Indichi dove
   ricevere i sats» → «Chi vende li mette in garanzia» → «Paghi il PayCode
   al tabacchino» → «I sats arrivano a te».
2. 🧑 Compra, dà l'indirizzo sats (come §2b). 📱 Il riquadro «🧾 Il PayCode
   da pagare al tabacchino» compare con codice (e «📋»: «PayCode copiato
   📋»), «Importo 25,47 € in contanti», «Scade il …», «Tempo che resta:
   <conto>», e i quattro passi: «Vai in tabaccheria, al bar, in edicola o
   alla posta: dove si accettano i pagamenti Amazon in contanti, senza
   commissione.» / «Dai il PayCode alla cassa e paga **25,47 €** in
   contanti.» / «Tieni lo scontrino: è la tua prova.» / «Torna qui e tocca
   **«Ho pagato al tabacchino»**». Finché la garanzia non c'è: «⚠️ **Non
   inviare ancora niente:** aspetta che questa pagina dica «Sats in
   garanzia».»
3. 📱 A garanzia bloccata: «**Sats in garanzia**» «I sats sono al sicuro in
   garanzia. Vai al tabacchino col PayCode qui sotto, paga in contanti alla
   cassa, tieni lo scontrino e poi torna qui a segnare «pagato».»
4. 🧑 Paga in contanti alla cassa, **tiene lo scontrino**, torna e tocca «✅
   Ho pagato al tabacchino». 📱 «Hai pagato il PayCode al tabacchino?» —
   «Dillo solo dopo aver pagato davvero 25,47 € in contanti alla cassa.
   Tieni lo scontrino: chi vende controlla su Amazon che l'ordine risulti
   saldato e libera i sats. Da qui non potrai più annullare: se qualcosa va
   storto, resta la disputa.» — «Sì, ho pagato». Stato «**PayCode pagato**»
   «Hai detto di aver pagato al tabacchino. Chi vende controlla su Amazon
   che l'ordine risulti saldato e libera i sats: tieni lo scontrino, è la
   tua prova.»
5. ✈️ Alla fine: «✅ **Sats rilasciati!** <N> sats in arrivo al tuo
   recapito.» In «I miei scambi»: «Hai ricevuto <N> sats pagando 25,47 € al
   tabacchino».

### ⚠️ Barattozon: le scadenze e cosa va storto

- Il PayCode si avvicina alla scadenza (a sats in garanzia): 📱 «Il PayCode
  scade fra meno di sei ore» / «Il PayCode scade fra meno di un'ora» /
  «Il PayCode è scaduto», con la frase per lato (a chi compra, scaduto:
  «Non si può più pagare al tabacchino. Se non l'hai pagato in tempo,
  tocca «✕ Annulla»: i sats tornano a chi li ha bloccati. Se l'hai pagato
  prima della scadenza, tieni lo scontrino: chi vende lo vede pagato su
  Amazon e libera.»). Il bottone «✕ Annulla» diventa arancione.
  ✈️ «⏳ Un tuo scambio in contanti al tabacchino scade fra circa sei
  ore…» e «⏰ Un tuo scambio in contanti al tabacchino scade fra meno di
  un'ora…».
- Nessuno prende entro la scadenza del libro: ✈️ «⏰ **Nessuno ha pagato
  il tuo PayCode entro la scadenza del libro:** l'ordine è uscito dalla
  vetrina (…). La scadenza del libro cade due ore prima di quella Amazon…
  Quando scade anche lui, l'ordine Amazon va rifatto e ripubblicato con un
  PayCode nuovo.»
- Errori nel foglio del recapito (se il PayCode si manda a mano): «Il
  PayCode ha 9 cifre, come 479-868-518»; «Scrivi la scadenza come
  17/09/2026 alle 14:30»; «L'importo dell'ordine e' una cifra in euro,
  coi centesimi se servono (23,47)».

---

## 8. Annullare

### Da solo, prima che qualcuno prenda il mio ordine

1. 🧑 Chi ha pubblicato apre il suo ordine (dal libro «È il tuo ordine —
   tocca per aprirlo», o da «I miei scambi» → gruppo «Nel libro») e tocca
   «**✕ Annulla l'ordine**».
2. 📱 «**Annulli l'ordine?**» — «L'ordine esce dal libro. Nessuno ha ancora
   scambiato niente con te.» — «Sì, annulla» / «Indietro».
3. 📱 «Sto annullando l'ordine…» → «Ordine annullato ✓». La pagina resta
   aperta e dice «**Ordine annullato**» «È uscito dal libro prima che
   qualcuno lo prendesse: nessun sat si è mosso.» Nessun avviso a nessuno.

### Dopo la presa, prima della garanzia

🧑 Una delle due parti tocca «**✕ Annulla**». 📱 Il foglio dice «**Annulli
lo scambio?**» — «Lo scambio si annulla subito, senza bisogno del sì
dell'altra persona, e nessuno perde niente: se i sats erano già bloccati,
tornano a chi li ha bloccati.» — «Sì, annulla». Il coordinatore annulla
davvero subito: toast «Scambio annullato ✓», e si torna a «I miei
scambi». (I sats possono essere già bloccati quando chi vende ha preso un
ordine di acquisto: paga la garanzia prima che chi compra dia la fattura.)
✈️ All'altra persona: se ha annullato chi aveva preso, a chi aveva
pubblicato «🔄 **<nome> ha annullato lo scambio.** Il tuo ordine è tornato
in vetrina: non devi fare niente.»; se ha annullato chi aveva pubblicato,
a chi aveva preso «❌ **<nome> ha annullato lo scambio.** I sats
eventualmente in garanzia tornano a chi vende.» A chi vende e aveva già
bloccato i sats, al posto di quella frase (o in coda al ritorno in
vetrina): «I sats che avevi bloccato in garanzia sono tornati a te.»
✈️ E a chi ha annullato: «❌ **Hai annullato lo scambio con <nome>.**»
— più «I sats che avevi bloccato in garanzia sono tornati a te.» se li
aveva bloccati, e la riga della cauzione se l'aveva messa.

### D'accordo con l'altro, a sats in garanzia

1. 🧑 A propone: «✕ Annulla» → «Annulli lo scambio?» (come sopra) →
   «Chiedo di annullare…» → «Richiesta di annullo inviata».
   📱 A vede «**Hai chiesto di annullare**» «Serve anche il sì dell'altra
   persona.»
2. ✈️ B riceve: «↩️ **<nome> chiede di annullare lo scambio.** Se sei
   d'accordo, annulla anche tu dalla pagina dello scambio; se no non fare
   niente, e lo scambio continua.»
   📱 B vede «**L'altra persona vuole annullare**» «Se sei d'accordo, i sats
   tornano a chi li ha bloccati.» col bottone «🤝 Accetta di annullare».
3. 🧑 B accetta: «**Accetti di annullare?**» — «Lo scambio si chiude e i
   sats tornano a chi li aveva bloccati. Nessuno perde niente.» — «Sì,
   annulliamo» → «Accetto di annullare…» → «Scambio annullato ✓».
4. ✈️ A riceve: «❌ **<nome> ha accettato di annullare: lo scambio è
   annullato.** I sats eventualmente in garanzia tornano a chi vende.»
   (se A vende: «…I sats che avevi bloccato in garanzia sono tornati a
   te.»). ✈️ B riceve: «❌ **Hai accettato di annullare: lo scambio con
   <nome> è annullato.**» — più la stessa frase dei sats, se a vendere è
   B.
   📱 Tutti e due: «**Scambio annullato**» «Nessuno ha perso niente: i sats
   sono tornati a chi li aveva bloccati.» (e la riga della cauzione, se
   c'era).

Se B non fa niente, lo scambio continua. **Dopo «Ho inviato gli euro» il
bottone «✕ Annulla» non c'è più**: resta solo «⚠️ C'è un problema» (la
disputa). In disputa si può ancora annullare d'accordo: «La disputa è
aperta, ma potete ancora chiuderla fra voi: se anche l'altra persona è
d'accordo lo scambio si annulla, la disputa si chiude e i sats tornano a
chi li ha bloccati.» (a chi compra in più: «Se hai già inviato gli euro
non annullare: aspetta il moderatore.»).

⚠️ Storto: «Aspetta: la risposta non è ancora arrivata»; «Risulta già una
tua richiesta di annullare: ora serve il sì dell'altra persona. Se non
l'avevi chiesto tu, scrivici»; «Non è riuscito: <motivo>»; «La risposta
tarda: controllo com'è andata…».

---

## 9. Scadenze

| Cosa | Quanto | Cosa succede |
|---|---|---|
| Un ordine nel libro | 7 giorni (168 h, dal nodo) | «Info P2P»: «Un ordine vive nel libro **7 giorni**. Scaduto quello sparisce da solo, e non è successo niente.» ✈️ a chi l'ha pubblicato: «⏰ **Il tuo ordine è scaduto** senza che la presa fosse completata: vendevi/compravi <N> sats per <cifra> via <metodo>. Puoi ripubblicarlo quando vuoi.» |
| Un ordine Barattozon | fino a 2 h prima della scadenza del PayCode (mai oltre 72 h) | esce da solo, avviso dedicato (§7) |
| Ogni passo dopo la presa | 15 minuti | «Preso l'ordine, **ogni passo ha 15 minuti**, e il primo tocca sempre a chi l'ha preso: se compri, dici dove vuoi i sats e poi chi vende li blocca; se vendi, blocchi i sats e poi chi compra dice dove li vuole. Il cronometro **riparte a ogni mossa**.» Se manca chi ha **preso**, l'ordine torna nel libro; se manca chi ha **pubblicato**, si chiude. Nessuno perde niente. |
| La richiesta della cauzione | qualche minuto (lo dice il foglio) | l'ordine torna nel libro, va ripreso |
| Sats già in garanzia | circa quattro giorni | «Coi sats in garanzia avete **circa quattro giorni**. Se chi compra non ha ancora detto di aver pagato, allo scadere i sats **tornano da soli a chi vende**; se l'ha detto, si apre una disputa.» Dal sorgente della 0.19.0: il coordinatore si muove a ~92 ore; una disputa già aperta e non decisa la chiude LND a ~94 ore, coi sats a chi vende. ✈️ «⏰ **La garanzia è arrivata a scadenza: lo scambio è annullato.** I sats tornano a chi vende.» |
| Barattozon, dopo «pagato» | 24 ore «a vista» per chi vende | promemoria a 1, 6, 20 ore; poi nulla di automatico |
| La fattura di chi compra | meglio almeno un giorno | se scade prima del rilascio: «Serve una fattura nuova» |
| Appuntamento in contanti | entro una settimana | «Fissa l'incontro entro una settimana» |
| Metà della cauzione vinta | 15 giorni per incassarla | dopo «il servizio se la tiene» |
| Righe chiuse in «I miei scambi» | 30 giorni (24 h le prese rifiutate) | spariscono da sole; restano i conclusi senza recensione |

📱 Il tempo si vede: l'anello sulla card del libro, «Tempo rimasto: …» nel
dettaglio, l'orologio dentro il foglio da pagare.

---

## 10. Disputa

- **Quando**: solo a sats **già in garanzia** — negli stati «Sats in
  garanzia», «Pagamento non riuscito», «Euro inviati» / «Contanti
  consegnati» / «PayCode pagato». Prima non c'è niente da contendere.
- **Il bottone**: «⚠️ **C'è un problema**» (rosso, in fondo alla pagina
  dello scambio); per chi vende in Barattozon è «🚨 Non risulta pagato:
  apri una disputa».
- 🧑 Lo tocca. 📱 «**Aprire una disputa?**» — «Un moderatore guarderà il
  caso e deciderà chi riceve i sats. Da quel momento lo scambio si ferma:
  né tu né l'altra persona potete più muovere i sats. A decidere è
  Barattolo, e le strade restano due: i sats vanno a chi compra o tornano
  a chi vende. Prima di aprirla, dai tempo all'altra persona: quasi sempre
  è un ritardo. Se qui sopra c'è il suo profilo coi bottoni per
  scrivergli, provate prima a sentirvi.» —
  «Sì, apri la disputa» → «Apro la disputa…» → «Disputa aperta».
- 📱 Stato per tutti e due: «**Disputa aperta**» «Un moderatore esaminerà
  lo scambio. I sats restano bloccati fino alla decisione.»
- ✈️ All'altra persona: «⚖️ **<nome> ha aperto una disputa sullo scambio
  da 50,00 €:** i moderatori vi contatteranno.»
- **Chi la gestisce**: i moderatori del coordinatore, cioè lo **staff di
  Barattolo** (quelli col bollino «Staff»). ✈️ Ai moderatori: «⚖️
  **Disputa P2P aperta** sull'ordine <codice>, da **chi compra**.» con
  compra, vende, importo, metodo, «Garanzia bloccata dal …» e «I sats
  restano in garanzia finché un moderatore non decide o le due parti non si
  accordano.» Se il moderatore è una delle parti: «⚠️ **Sei una delle due
  parti:** questa disputa la decide un altro moderatore.» Il moderatore
  decide dalla pagina «⚖️ Moderazione P2P», scrive un motivo (almeno 20
  caratteri), conferma due volte («Conferma definitiva» — «…La decisione
  resta nel registro, col tuo nome.») e sceglie una delle due: «I sats
  vanno a chi compra» o «I sats tornano a chi vende» (nei contanti può
  anche spuntare «🔐 **Brucia la cauzione di …**»).
- **Cosa succede ai sats**: restano fermi in garanzia finché il
  moderatore non decide (o le parti non annullano d'accordo). Due strade
  sole. ✈️ Esiti: «⚖️ **Un moderatore ha chiuso la disputa: i sats vanno a
  chi compra.**» (poi «✅ Scambio concluso!») oppure «⚖️ **Un moderatore ha
  annullato lo scambio.** I sats eventualmente in garanzia tornano a chi
  vende.» (a chi vende: «…I sats che avevi bloccato in garanzia sono
  tornati a te.»). Se l'avviso del coordinatore si perde, quello dal libro: «⚖️ **La
  disputa è stata chiusa: lo scambio è andato in porto.**» / «⚖️ **La
  disputa è stata chiusa: lo scambio è stato annullato.** I sats in
  garanzia tornano a chi vende.»
- «Tieni le prove di quello che hai fatto: la ricevuta del bonifico, la
  schermata del pagamento. Sono quelle che guarda chi decide.» Le chat
  fuori da Barattolo non contano.
- Dopo una disputa chiusa in porto la recensione si può lasciare.
- ⚠️ Storto: «Non è riuscita: <motivo>».

---

## 11. Dopo lo scambio

### La recensione

- 📱 A scambio concluso, se l'altra persona ha un profilo su Barattolo,
  nella pagina dello scambio: «**⭐ Lascia una recensione**» «Com'è andata
  con <nome>? Le stelle e il commento vanno sul suo profilo di Barattolo,
  nella stessa media del mercatino. È definitiva: non potrà essere
  modificata.», le cinque stelle, il campo «Commento (facoltativo, max 200
  caratteri)», il bottone «⭐ Invia la recensione» (se c'è anche il voto
  del circuito: «Le stelle viaggiano anche sul circuito degli scambi, che è
  la reputazione di chi scambia fuori da Barattolo; il commento resta
  qui.»).
- 🧑 Sceglie le stelle, tocca invia. 📱 «**Invii questa recensione?**» «È
  definitiva: non potrà essere modificata.» → «⭐ Invio la recensione…» →
  «⭐ Grazie per la recensione!». Poi il riquadro diventa «⭐ Recensione
  lasciata» con le stelle e il commento.
- ⚠️ «Scegli da 1 a 5 stelle»; «Commento troppo lungo (max 200
  caratteri)»; il commento con parole vietate viene rifiutato; «Hai già
  lasciato la recensione…»; se l'altro non ha un profilo: «Questa persona
  non ha un profilo su Barattolo: non c'è un posto dove lasciarle una
  recensione.» e resta solo «⭐ Vota chi ha scambiato con te» → foglio «⭐
  Com'è andata?» («È il voto degli scambi P2P, e non ha niente a che
  vedere con le stelle del tuo negozio su Barattolo.») → «Mando il voto…»
  → «Grazie ⭐».

### La stellina e lo scudo Staff

- **La stellina** è la media delle recensioni di chi ha pubblicato, la
  stessa del mercatino: sulla card del libro «★ 4,9 · 👤 24», nel dettaglio
  «Chi ha pubblicato quest'ordine» con «media» e «recensioni». La stella
  si riempie per quanto vale la media. Nella card P2P della home sta
  all'angolo del volto (per il lettore di schermo: «Valutazione 4,9 su
  5»). Senza recensioni, niente stella.
- **Lo scudo Staff**: il bollino «Staff» (sui volti nelle card, nella card
  dell'altra persona nella pagina dello scambio). **Ha la precedenza**: chi
  è staff porta lo scudo e non la stellina. Toccandolo: «**Staff di
  Barattolo**» «Fa parte dello staff di Barattolo: solo chi ha questo
  bollino è un moderatore.» — «Ho capito».
- Dalla presa in poi le due parti si vedono: nome, foto, stelline,
  livello, «<N> giorni qui», e i tondi per scriversi su Telegram o Nostr
  (solo dove esistono).

### La ✕ in «I miei scambi»

- 📱 «I miei scambi» raggruppa: «Tocca a te», «In corso», «Nel libro»,
  «Conclusi», «Annullati» (con «👉 tocca a te» sulle righe che aspettano
  te). Le righe chiuse si raccontano al passato: «Hai ricevuto … inviando
  …», «Annullato».
- La **✕** compare solo sulle righe **chiuse** (concluse, annullate,
  prese rifiutate) e su quelle «Nessuna risposta» passati 7 giorni (prima:
  «Resta qui ancora <n> giorni: fino ad allora l'ordine può essere ancora
  vivo nel libro, e la sua chiave serve a riprenderlo. Poi lo potrai
  togliere.»).
- 🧑 Tocca la ✕. 📱 «**Togliere questo scambio?**» — «La riga e la sua
  chiave se ne vanno da tutti i tuoi dispositivi, e non tornano. Lo scambio
  è chiuso, quindi non c'è più niente da fare.» (se manca la recensione:
  «Su questo scambio puoi ancora dare il voto: togliendolo lo perdi.») —
  «Togli» → «Scambio tolto». Dal 7 ott 2026 sparisce anche dagli altri
  dispositivi.
- ⚠️ «Non riesco a toglierlo adesso: controlla la connessione e riprova»;
  «Lo scambio risulta ancora in corso: lo potrai togliere quando sarà
  chiuso»; «Questo scambio è ancora aperto»; «Ancora <n> giorni: l'ordine
  può essere ancora vivo».

---

## 12. I soldi: commissione, sconto Pionieri, premio, limiti

### La commissione

- La decide il **coordinatore** e l'app la legge viva. Oggi **3% in
  tutto, 1,5% per parte**: metà la paga chi compra (riceve un po' meno
  sats), metà chi vende (blocca un po' più sats). «Non si paga a parte: è
  già dentro i sats che passano di mano — chi vende ne blocca un po' di
  più, chi compra ne riceve un po' di meno.» Pubblicare o prendere non
  costa niente: «Oltre a questa, Barattolo non ti chiede **nient'altro**:
  pubblicare un ordine o prenderlo non costa niente.»
- Si calcola **dopo** il premio: «Il premio si applica **prima** della
  commissione: prima si calcola il controvalore col premio, poi la
  commissione morde su quello.»
- 📱 Il banner in cima al libro (un'immagine: «Fee P2P: 2% barrato, in
  beta 1,5% per parte, in beta 1% per pionieri o livello 5»). Toccato,
  foglio «**Le commissioni del P2P**»: «Durante la beta la fee P2P è del
  **3%** in tutto, cioè **1,5%** per chi compra e **1,5%** per chi vende.
  Finita la beta sarà del **4%** in tutto (2% per parte). Pionieri e
  livello 5 hanno sempre uno **sconto dello 0,5%** sulla propria parte.»
  (+ «**Tu sei fra questi.**» a chi ce l'ha) e «Ho capito».
- Il banner è disegnato con quelle tre cifre (listino 4%, beta 3%,
  sconto 0,5): se una delle tre cifre vive è diversa, **il banner non si
  vede**, finché non si ridisegna. Il foglio, che le legge vive, resta.
- Nel conto: «Fee P2P **1,5%**» col cartellino «beta», oppure «🌱
  Pioniere» / «Lv. 5» a chi ha lo sconto, o «sconto non verificato» se il
  coordinatore non l'ha applicato.

### Lo sconto Pionieri

- **Uno sconto solo**: Pionieri (la coorte è congelata a 101) **oppure**
  livello 5 («Maestro del banco»): 0,5 punti in meno sulla propria metà →
  **1% per parte**. Pioniere e livello 5 insieme non si sommano.
- Lo applica il coordinatore (chiede al server se quella chiave ha lo
  sconto); l'app lo mostra nel conto, nel finale del tour («Sei un
  Pioniere!» / «Sei al livello 5!»), nel foglio Pubblica («…e tu hai uno
  sconto dello 0,5%, quindi paghi l'1% di fee») e nel foglio delle
  commissioni.

### Il premio

- Chi pubblica a prezzo di mercato sceglie un premio da **−20% a +20%**, a
  numeri interi (Barattozon pure, anche a prezzo fisso).
- Sulla card: «<N>% più conveniente» / «<N>% meno conveniente» per chi
  guarda, «al prezzo di mercato» a zero; dal 10% «⚡ Ottimo affare», oltre
  il 15% «⚡⚡ Super affare».
- Nel conto di chi prende: «Premio richiesto dall'utente» o «Sconto
  offerto dall'utente», poi «Subtotale». Nel conto di chi ha pubblicato:
  «Premio che hai richiesto» / «Sconto che hai offerto». Sugli ordini a
  sats fissi: «Premio scelto: …» · «Al prezzo di adesso: …» (dopo la
  presa: «della presa»).
- In «Info P2P»: «Sopra il mercato si chiama **premio** e conviene a chi
  vende; sotto si chiama **sconto** e conviene a chi compra.»

### I limiti d'importo

| Limite | Valore | Messaggio |
|---|---|---|
| Massimo del coordinatore | 500 000 sats per ordine | «Troppi: il massimo è 500 000 sats»; nel foglio «Al momento si accettano ordini fino a 500 000 sats» |
| Minimo del coordinatore | quello che dichiara | «Troppo pochi: il minimo è <x> sats» |
| Tetto in euro di Barattolo (`P2P_MAX_EURO`) | spento nel codice | se acceso: «Troppi: il massimo è <x> €» e «Fase beta: max <x> €» |
| Contanti di persona | 250 € per scambio | «In contanti di persona il massimo è 250 € per scambio: sopra, si divide in più ordini» |
| Barattozon, minimo | 25 € | «Un PayCode Barattozon vale almeno 25 €: sotto non si pubblica» |
| Barattozon, massimo | 999 € (Amazon) | «Amazon accetta il pagamento in contanti fino a 999 € per ordine» |
| Cifre | euro interi; solo Barattozon coi centesimi | il campo non accetta la virgola |

---

## Notato strada facendo — chiuso il 7 ott 2026

I tredici punti trovati scrivendo questa guida. Undici sono stati
corretti nel cantiere «I testi del P2P che confondevano» (testi approvati
da Andrea), due restano come sono per sua decisione. I testi nuovi sono
già nelle sezioni qui sopra.

1. ✅ **«Annulli lo scambio?» prima della garanzia.** Ora: «Lo scambio si
   annulla subito, senza bisogno del sì dell'altra persona, e nessuno
   perde niente: se i sats erano già bloccati, tornano a chi li ha
   bloccati.» (§8). Coi sats in garanzia resta la frase dell'accordo.
2. ✅ **«Nessun timer» contro la garanzia che scade.** Verificato sul
   sorgente della 0.19.0 che gira; «Info P2P» ora dice «Coi sats in
   garanzia avete circa quattro giorni…» (§9). Resta aperto un altro
   pezzo: la disputa che il coordinatore apre da solo a ~92 ore non
   avvisa nessuno (cantiere «avviso garanzia lunga»).
3. ✅ **L'ordine dei primi due passi.** «Info P2P» ora dice che il primo
   passo tocca a chi ha preso, nei due versi (§9), e il passo 5 non dice
   più «all'inizio».
4. ✅ **Il «contatto» della disputa.** Ora: «Se qui sopra c'è il suo
   profilo coi bottoni per scrivergli, provate prima a sentirvi.» (§10).
5. ✅ **Il PayCode alla presa.** Ora: «…appena l'ordine è tuo, e paghi
   solo quando la pagina dice «Sats in garanzia».» (§7), anche nel passo
   4 della lista di Barattozon in «Info P2P».
6. ✅ **«…o i sats tornano indietro».** Ora: «…se il PayCode scade prima,
   lo scambio va annullato e non ricevi i sats.» (§7b).
7. ✅ **Il banner della fee fisso.** Si nasconde se una qualsiasi delle tre
   cifre vive (fee, listino, sconto) non è quella disegnata (§12).
8. ✅ **Cambiare il recapito dopo il pagato.** La riga del foglio ora dice
   «…cambialo solo se chi compra non ha ancora pagato.» (§3). L'avviso a
   chi compra l'ha rifatto l'altra sessione; nessun blocco del cambio.
9. ✅ **SEPA Instant.** Il recapito si compone «Bonifico SEPA Instant /
   …» quando il metodo è Instant (§5).
10. ✅ **Dopo «Ho inviato gli euro» non si annulla più.** I tre «pagato»
    ora finiscono con «Da qui non potrai più annullare: se qualcosa va
    storto, resta la disputa.» (§2b, §6, §7b).
11. ➖ **La ✕ rossa di Barattozon aspetta 0,7 secondi.** Nessuna modifica
    (decisione di Andrea): nel video si scrive la cifra tutta di fila.
12. ✅ **«Dove vuoi i sats?».** Ora: «Indica il tuo indirizzo Lightning, o
    incolla una fattura: …» (§2b).
13. ➖ **Le leve del 10 ottobre.** Nessuna modifica (decisione di Andrea):
    prima di girare si guarda il pannello «⚙️ Stato delle leve».
