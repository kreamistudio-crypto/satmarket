# Novità di Barattolo per gli utenti

Questo file è la fonte dei post automatici sul canale (cantiere «novita», 10 nov 2026).
A ogni PROMOZIONE su main con la CI verde, n8n (sul RELAY, bot «Barattolo News») legge
le voci NUOVE di questo file rispetto al main di prima, e per ognuna con
`pubblico: sì` fa scrivere a Claude una BOZZA di post, che arriva in privato ad
Andrea coi tasti Pubblica / Modifica / Scarta. Nel canale non esce niente senza il suo
tocco. Il disegno intero: docs/ARCHITETTURA.md, «LE NOVITÀ PER GLI UTENTI».

CHI LA SCRIVE: il thread del cantiere, a fine lavoro, nello stesso commit della voce
in docs/CANTIERI.md. Solo per quello che un utente può VEDERE o USARE: un ritocco
interno, una prova, un documento non portano voce.

COME SI SCRIVE: una voce per novità, in fondo al file, così (le righe vanno tutte,
in quest'ordine; niente altro fra una voce e l'altra):

    ## 2026-11-10 · nome-del-cantiere
    frase: Cosa cambia per chi usa Barattolo, in una o due frasi semplici.
    dove: La pagina e i bottoni dove si vede (per la registrazione dello schermo).
    leva: NOME_DELLA_LEVA spenta di serie   oppure   leva: nessuna
    pubblico: no

- `frase`: per gli utenti, non per noi. Fatti soli: è la base del post, Claude non
  aggiunge niente che qui non c'è. Lessico di Barattolo («deposito di garanzia»,
  «Ordini»). Al massimo 400 caratteri.
- `dove`: scheda, pagina, bottone, coi nomi che l'utente legge sullo schermo.
- `leva`: il nome della leva che la accende (deve esistere in config_esempio.py) e
  com'è DI SERIE, oppure `nessuna` se la novità c'è per tutti appena arriva su main.
- `pubblico`: `sì` solo se, arrivata su main, la vede CHIUNQUE. Leva spenta, o accesa
  solo per gli admin: `no` (un post la annuncerebbe a tutti). Il config del VPS
  vince sul codice: se non sai com'è là, scrivi `no`.
- Il giorno che Andrea accende una leva per tutti, la novità si annuncia con una
  voce NUOVA (`leva: NOME accesa per tutti dal <data>`, `pubblico: sì`). Le voci
  vecchie non si cambiano: n8n guarda solo le intestazioni nuove.
- L'intestazione (`## data · nome`) non si ripete mai: è la chiave con cui n8n
  riconosce una voce già vista.

La forma la controlla `prove_novita_md` in prove.py.

<!-- LE VOCI COMINCIANO QUI SOTTO -->

## 2026-11-10 · come-ricevi
frase: Nel Profilo c'è una voce nuova, «📥 Come ricevi»: lì scegli in che forma ti arrivano i sats quando ti pagano in Lightning e quando ti pagano on-chain, senza cercarlo dentro la voce «₿ On-chain».
dove: Profilo → «📥 Come ricevi», con le due righe «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in».
leva: SWAP_AUTO_ATTIVO spenta di serie
pubblico: no

## 2026-11-10 · onion-location
frase: Se apri barattolo.store con Tor Browser, nella barra degli indirizzi compare «.onion disponibile»: un tocco e sei sul sito .onion di Barattolo, dove il server non vede il tuo indirizzo IP.
dove: Tor Browser, barra degli indirizzi su barattolo.store: la pillola viola «.onion disponibile».
leva: nessuna
pubblico: sì

## 2026-11-11 · cifra-btc
frase: Quando paghi on-chain, accanto ai sats da mandare ora vedi anche la cifra in BTC (per esempio 0,00008128 BTC): la tocchi e la copi, pronta da incollare nel wallet. Nel pagamento di un ordine on-chain c'è anche «₿ Apri nel wallet», che apre il wallet con indirizzo e cifra già scritti.
dove: il foglio «Blocca … sats» del pagamento on-chain, «🔒 Blocca i sats» degli scambi P2P on-chain, la scheda «Cambio» e il riquadro «Caricali in Lightning» del P2P: la riga «In BTC» col bottoncino 📋.
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

## 2026-11-11 · foglio-oc-visto
frase: Quando paghi un ordine on-chain, appena la rete vede i tuoi sats la pagina del pagamento si chiude da sola: in «Ordini» l'ordine dice «Visto in rete, aspetto la conferma» invece di «Da pagare», e dopo una conferma, circa dieci minuti, diventa pagato.
dove: il foglio «Blocca … sats» del pagamento on-chain e la riga dell'ordine in «Ordini» (etichetta «In arrivo»).
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

## 2026-11-11 · seconda-firma-parla
frase: Nell'ordine on-chain il tasto «✍️ Metti la seconda firma» ora mostra l'anello mentre firma e alla fine dice com'è andata, o perché non ha firmato. Quando i sats sono partiti, l'ordine scrive «Il rimborso è partito» o «I sats sono partiti» col link alla transazione, e il tasto sparisce.
dove: la pagina di un ordine on-chain, nel riquadro ₿ «Pagato on-chain, in un 2-di-3».
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

## 2026-11-11 · cambio-per-tutti
frase: La pagina «Cambio» è aperta a tutti: sposti i tuoi sats da Lightning a un tuo indirizzo bitcoin, o da bitcoin a Lightning, senza commissioni di Barattolo. Da 25.000 sats (50.000 da bitcoin verso Lightning) fino a 0,01 BTC a cambio, al massimo 5 cambi al giorno. E chi vende in Lightning sul mercatino può scegliere di ricevere on-chain.
dove: la scheda «Cambio» in basso, col tasto «🔁 Cambia»; per chi vende, il riquadro dell'incasso nella pagina dell'ordine.
leva: SWAP_ATTIVO e CAMBIO_LIBERO_ATTIVO accese per tutti dal 2026-11-11
pubblico: sì

## 2026-11-11 · cambio-address-e-cifra
frase: Nel Cambio da bitcoin a Lightning non serve più creare a mano la richiesta nel wallet: incolli il tuo Lightning address (nome@wallet) e la richiesta della cifra giusta la chiede Barattolo al tuo wallet. E se preferisci crearla tu, la cifra esatta si tocca e si copia, pronta da incollare.
dove: la scheda «Cambio», direzione da bitcoin a Lightning, il campo «La tua richiesta Lightning».
leva: CAMBIO_BTC_LN_ATTIVO (nessuna leva nuova)
pubblico: sì

## 2026-11-12 · card-p2p-coppia
frase: Le card del P2P si leggono al volo: in alto a destra due quadratini con la freccia dicono cosa invii e cosa ricevi (euro o USDT verso i sats, o il contrario), la faccia di chi ha pubblicato sta in fondo accanto alle sue stelline e ai suoi scambi, e il tempo che resta è la riga colorata sul bordo di sotto, che si accorcia e diventa arancio e poi rossa quando l'ordine sta per scadere.
dove: la scheda «P2P», le card del libro (Compra BTC e Vendi BTC, anche quelle on-chain).
leva: nessuna
pubblico: sì

## 2026-11-12 · nome-swap
frase: La scheda «Cambio» ora si chiama «Swap»: è la stessa pagina, sposta i tuoi sats fra Lightning e il tuo indirizzo bitcoin. E da bitcoin a Lightning, se scrivi una cifra troppo piccola, l'app ti dice il minimo dal lato dove l'hai scritta: il minimo di 50.000 sats vale per quello che ricevi, quindi in «Mandi» serve un po' di più.
dove: la scheda «Swap» in basso, i riquadri «Mandi» e «Ricevi».
leva: CAMBIO_LIBERO_ATTIVO (nessuna leva nuova)
pubblico: sì

## 2026-11-12 · p2p-onchain-500
frase: Negli scambi P2P on-chain ora si arriva fino a 500 € per ordine (prima 250 €), lo stesso tetto degli acquisti on-chain del mercatino. Gli scambi P2P in Lightning restano fino a 250 € durante la beta. E nelle card del libro, anche in quelle on-chain, toccando la faccia di chi ha pubblicato si apre il suo negozio, mai l'ordine.
dove: la scheda «P2P», il foglio «Pubblica» a rete on-chain e le card del libro.
leva: ONCHAIN_MAX_EURO (nessuna leva nuova; il P2P on-chain resta dietro ONCHAIN_SOLO_ADMIN)
pubblico: no

## 2026-11-12 · usdt-novita-tutorial
frase: In cima al libro del P2P c'è un rettangolo verde «USDT · Novità»: toccalo e un breve tutorial ti mostra come riconoscere un ordine in USDT dalla T verde di Tether, come pubblicarne uno scegliendo USDT e la rete (Tron o Ethereum), e come si paga senza sbagliare rete. Si rivede quando vuoi, con lo stesso tocco.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: no

## 2026-11-13 · usdt-foglio-presa
frase: Negli ordini P2P in USDT con un intervallo, quando scegli quanto scambiare il foglio ora parla USDT come la card: «Quanti USDT», la fascia in USDT, e i sats che ricevi contati al cambio del dollaro, gli stessi del conto che vedi subito dopo. Anche «come invii gli USDT», «Come funziona» e il cambio «1 BTC ≈ … USDT» nella pagina dell'ordine.
dove: la scheda «P2P», toccando un ordine in USDT con «scegli tu» nel libro.
leva: P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: no

## 2026-11-13 · rete-scelta
frase: Negli scambi P2P, quando prendi un ordine con più metodi o più reti, la tua scelta arriva davvero all'altra persona: nella pagina dello scambio e in cima alla chat legge «ha scelto USDT su Tron» (o «SEPA Instant»), e le arriva un avviso su Telegram. Il recapito si può dare solo sulla rete scelta, e se ne arriva uno di un'altra rete la pagina lo dice in rosso prima che paghi.
dove: la scheda «P2P», la pagina dello scambio in «I miei scambi» (sotto il conto) e la chat dello scambio.
leva: nessuna
pubblico: sì

## 2026-11-13 · fee-una-volta
frase: Il riquadro colorato delle commissioni in cima al libro P2P ora compare solo la prima volta, alla fine del tutorial, e poi non occupa più spazio sopra gli ordini. Si rivede rifacendo «Come funziona» fino in fondo, e la commissione resta sempre scritta nel conto di ogni ordine prima di prenderlo.
dove: la scheda «P2P», in cima al libro degli ordini; il bottone «Come funziona».
leva: nessuna
pubblico: no

## 2026-11-13 · prezzo-btc-libro
frase: In cima al libro del P2P, sotto i rettangoli «Novità», c'è il prezzo di bitcoin aggiornato ogni minuto: quanto vale 1 BTC in euro, quanto è salito o sceso e una piccola linea, verde se sale e rossa se scende. Toccandolo passi dalle ultime 24 ore agli ultimi 7 giorni e agli ultimi 30 giorni, e toccando il simbolo € lo vedi in dollari.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: nessuna
pubblico: sì

## 2026-11-13 · card-p2p-monete
frase: Nella home, nella fila «Scambi P2P», ogni ordine ora ha la sua moneta: un ordine in USDT si presenta con la sua card verde, il ₿ accanto alla T di Tether, e la cifra scritta in USDT, non più in euro. E in testa a «I miei scambi» c'è un disegno nuovo con tutte le monete insieme, il ₿ al centro.
dove: la home del mercatino (fila «Scambi P2P») e la pagina «I miei scambi».
leva: P2P_IN_VETRINA e P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: sì

## 2026-11-14 · p2p-chf
frase: Nel P2P arriva il franco svizzero: si possono pubblicare e prendere ordini in CHF, pagati con TWINT, bonifico svizzero, Revolut, Wise o contanti di persona. La card dice CHF con la croce svizzera, il tetto della beta è quello degli euro convertito in franchi, e l'app controlla il numero TWINT e l'IBAN svizzero prima che partano.
dove: la scheda «P2P», il foglio «Pubblica» (valuta CHF), le card del libro e della home.
leva: P2P_CHF_ATTIVO (nuova, spenta) e P2P_CHF_SOLO_ADMIN
pubblico: no

## 2026-11-14 · usdt-cifra-copia
frase: Negli scambi P2P in USDT, chi deve mandare gli USDT ora trova sotto l'indirizzo anche la cifra esatta da inviare, con il suo tasto «📋 Copia» accanto, come per l'indirizzo. Copia solo il numero, pronto da incollare nel wallet: niente più cifre riscritte a mano.
dove: la pagina dello scambio in «I miei scambi», nel riquadro «💵 Dove mandare gli USDT».
leva: nessuna
pubblico: sì

## 2026-11-14 · banner-mappa-contanti
frase: La mappa dei contanti di persona ora è un tondo accanto alla campanella, in alto nel libro P2P: resta lì anche mentre scorri, e toccandolo si apre l'Italia coi pallini. In fondo alla mappa c'è «Numerino», spento di serie: acceso, il tondo mostra quante offerte in contanti nuove sono arrivate dall'ultima volta, e aprendo la mappa il numero sparisce.
dove: la scheda «P2P», la riga in alto con «Filtro», la campanella e il tema.
leva: nessuna
pubblico: sì

## 2026-11-14 · mappa-mercatino
frase: Nel mercatino arriva la mappa del ritiro a mano: il tondo della mappa, accanto alla barra di ricerca, apre l'Italia coi pallini degli annunci da ritirare di persona. Ogni pallino sta al centro della città dell'annuncio, mai sull'indirizzo; tocchi una città e vedi solo i suoi annunci. Come nel P2P, il «Numerino» in fondo alla mappa conta i nuovi annunci.
dove: la home del mercatino (Esplora), il tondo della mappa accanto alla barra di ricerca.
leva: MERCATINO_MAPPA_RITIRO (nuova, accesa di serie)
pubblico: sì

## 2026-11-14 · notifiche-telefono
frase: Nell'app di Barattolo (quella di Zapstore), nel sito aggiunto alla schermata Home e nel browser del PC ora puoi ricevere le notifiche come quelle di WhatsApp, anche ad app chiusa: ordini pagati o spediti, scambi P2P presi, messaggi. Si accendono da Profilo → Avvisi → «📲 Notifiche sul telefono», e con «Mandami una notifica di prova» vedi subito se arrivano.
dove: il Profilo, cassetto «🔔 Avvisi», la prima riga.
leva: WEB_PUSH_ATTIVO (nuova, accesa)
pubblico: sì

## 2026-11-14 · avvisi-sconvenienti
frase: Gli avvisi dei nuovi ordini P2P ora si possono allargare anche agli ordini un po' meno convenienti del mercato: nella campanella, sotto «Convenienza», tocchi «Con un limite» e scegli fin dove ti va bene, da «Fino a 10% peggio» ad «Almeno 5% meglio». Così ti arrivano anche gli ordini quasi a mercato, ma non quelli troppo cari.
dove: la scheda «P2P», la campanella 🔔 in alto (e il cassetto «🔔 Avvisi» del Profilo).
leva: P2P_AVVISI_NUOVI_ORDINI (nessuna leva nuova)
pubblico: sì

## 2026-11-14 · ordine-libro-ricordato
frase: Nel libro P2P l'ordine che scegli ora resta: se metti «Convenienza» o «Importo: dal più grande», alla prossima visita il libro si apre già ordinato così, in «Compra» e in «Vendi». La scelta resta salvata sul telefono; per tornare come prima basta rimettere «Più recenti».
dove: la scheda «P2P», la pillola con le tre righe in cima al libro («Ordina il libro»).
leva: nessuna
pubblico: sì

## 2026-11-14 · feedback-modificabile
frase: Un feedback scritto di getto si può correggere: chi l'ha lasciato può modificarlo una volta (stelle e commento) o cancellarlo, entro 7 giorni da quando l'ha scritto; dopo resta definitivo. Vale nel mercatino e per le recensioni degli scambi P2P. Chi lo ha ricevuto viene avvisato, e sul profilo la riga dice «modificato». Cancellato è per sempre: su quell'affare non se ne lascia un altro.
dove: la pagina dell'ordine (scheda «Ordini») o dello scambio P2P, sotto il voto che hai lasciato: «✏️ Modifica» e «🗑 Cancella».
leva: FEEDBACK_MODIFICABILE (nuova, accesa di serie) e FEEDBACK_MODIFICA_GIORNI (7)
pubblico: sì

## 2026-11-14 · recensioni-ricevute
frase: Le recensioni che hai ricevuto adesso hanno un posto tutto loro: nel Profilo c'è «⭐ Recensioni ricevute», con il numero accanto, e ci arrivi anche toccando le tue stelle in cima alla pagina. Dentro trovi le ultime recensioni del mercatino e degli scambi P2P, con chi le ha scritte e quando, proprio come le vede chi apre il tuo negozio.
dove: il Profilo, sezione «Livello e inviti», la prima riga (o un tocco sulle stelle sotto il tuo nome).
leva: nessuna
pubblico: sì

## 2026-11-14 · invito-codice-sconto
frase: Chi vende può mandare il suo codice sconto a chi ha già comprato da lui: tocca «📣» sul codice, sceglie i clienti (già tutti spuntati) e preme «Invia invito sconto». Lo recapita Barattolo, sul bot, in DM Nostr o nell'app, e i contatti restano privati. Lo stesso codice arriva una volta sola, al massimo un invito a settimana per negozio; chi non vuole offerte le spegne negli Avvisi.
dove: Profilo → «🎟 Codici sconto» (il tasto «📣» sulla riga del codice) e Profilo → «🔔 Avvisi» (la riga «🎟️ Offerte dei negozi»).
leva: CODICI_SCONTO_INVITI (nuova, accesa di serie), CODICI_SCONTO_INVITI_GIORNI, CODICI_SCONTO_INVITI_MAX
pubblico: sì

## 2026-11-14 · paycode-dopo-garanzia
frase: Con Barattozon il PayCode arriva a chi compra solo quando i sats di chi vende sono in garanzia. Prima, nella pagina dello scambio c'è solo il tempo che resta, con la frase «Il PayCode compare qui quando i sats sono in garanzia»: così nessuno va al tabacchino a pagare prima che i sats siano al sicuro.
dove: la pagina dello scambio in «I miei scambi», nel riquadro «🧾 Il PayCode».
leva: nessuna
pubblico: sì

## 2026-11-14 · mancia-venditore
frase: Ti è piaciuto un affare e vuoi dare qualcosa in più al venditore? Ora puoi lasciargli una mancia: nell'ordine pagato c'è «🎁 Lascia una mancia», scegli quanti sats e li mandi dritti al suo wallet, senza commissioni. Nello stesso foglio puoi aggiungere, se vuoi, anche uno zap a Barattolo.
dove: la scheda «Ordini», dentro un ordine già pagato, accanto al voto.
leva: MANCIA_ATTIVA (nuova, accesa)
pubblico: sì

## 2026-11-14 · prezzo-btc-scura
frase: La card del prezzo di bitcoin in cima al libro P2P ha una veste nuova, scura, che si stacca dagli ordini sotto. E in dollari ora è uguale a quella in euro: linea, percentuale e periodo restano, e il tocco cambia sempre fra 24 ore, 7 giorni e 30 giorni.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: nessuna
pubblico: sì

## 2026-11-14 · mappa-ritocchi
frase: Il tondo delle mappe, nel P2P e nel mercatino, ora ha l'icona colorata 🗺️. E quando tocchi una città sulla mappa, la pagina scende da sola alle sue offerte o ai suoi annunci, senza doverli cercare sotto la mappa.
dove: la scheda «P2P» (il tondo 🗺️ accanto alla campanella) e l'Esplora del mercatino (il tondo 🗺️ in fondo alla barra di ricerca); un tocco su un pallino della mappa.
leva: nessuna
pubblico: sì

## 2026-11-14 · mancia-senza-indirizzo
frase: Se il venditore non ha ancora un indirizzo Lightning, il riquadro della mancia ora c'è lo stesso e te lo dice, invece di sparire: «non ha ancora un indirizzo Lightning nel profilo: per ora la mancia non si può mandare». E chi vende, nello stesso ordine, vede l'invito ad aggiungerlo dal Profilo: così può ricevere le mance e incassare da solo.
dove: la scheda «Ordini», dentro un ordine già pagato, accanto al voto.
leva: MANCIA_ATTIVA (la stessa della mancia)
pubblico: sì

## 2026-11-15 · cassa-negozio
frase: Hai un negozio, un banco al mercato o un bar? Nel Profilo c'è la «🏪 Cassa in negozio»: scrivi l'importo (in euro o in sats) o tocca i tuoi articoli, e Barattolo mostra un QR Lightning o on-chain. Il cliente lo inquadra con qualsiasi wallet, senza account. I sats vanno dritti al tuo wallet, senza commissioni, e i pezzi venduti escono da soli dalla vetrina.
dove: il Profilo, nel gruppo «Negozio e spedizioni», la voce «🏪 Cassa in negozio».
leva: CASSA_ATTIVA (nuova, accesa)
pubblico: sì

## 2026-11-15 · cassa-negli-ordini
frase: Le vendite della «🏪 Cassa in negozio» ora stanno in «Ordini», insieme a tutto il resto, con il loro segno. Il filtro «🏪 Cassa» in cima mostra solo quelle, e un tocco riapre la ricevuta.
dove: la scheda «Ordini», il filtro «🏪 Cassa» accanto a «Vendite».
leva: CASSA_ATTIVA (la stessa della cassa)
pubblico: sì

## 2026-11-16 · p2p-monete
frase: Nel P2P arrivano tre valute nuove: ETH, Monero e USDe. Funzionano come l'euro e l'USDT: scegli la valuta in cima a «Pubblica», sotto trovi solo le sue reti, l'importo lo scrivi nella moneta e i sats restano nel deposito di garanzia come sempre. Chi paga vede indirizzo controllato, QR, cifra esatta e il link all'explorer. USDe su Ethereum, Arbitrum, Base, BNB Chain e Solana.
dove: la scheda «P2P»: la valuta in cima al foglio «Pubblica», il filtro di ogni moneta nel libro e la card col suo logo.
leva: P2P_COIN_ATTIVO (nuova, accesa)
pubblico: sì

## 2026-11-16 · bottone-tappo
frase: Nel bot di Barattolo c'è il bottone «💬 Chiedi a Tappo»: un tocco e sei nella chat di Tappo, che risponde alle domande su come funziona Barattolo. Il bot di Barattolo resta quello degli avvisi su ordini e pagamenti.
dove: il bot @ilbarattolobot, nel messaggio di benvenuto (/start) e nella risposta a chi gli scrive una frase.
leva: TAPPO_LINK (accesa di serie)
pubblico: sì

## 2026-11-16 · nav-nostr
frase: La scheda «Swap» in basso adesso la vede anche chi apre Barattolo dal sito e non è ancora entrato: al suo posto prima c'era «Aste», che sono spente. Toccandola si entra con Telegram o con Nostr, e subito dopo si arriva alla pagina «Swap». E le aste hanno una casa nuova: la tessera «Aste» fra le categorie e una card quadrata in «Da scoprire», che portano alla pagina dove chiedere «🔔 Avvisami».
dove: la barra in basso del sito, prima del login; il foglio «Ti aspettiamo su Telegram» (su Tor «Entra nel Barattolo»); la home del mercatino, «Esplora per categorie» e «Da scoprire».
leva: SWAP_ATTIVO (nessuna leva nuova)
pubblico: sì

## 2026-11-16 · supporto-profilo
frase: Nel Profilo c'è la sezione «Supporto», con le due strade per chi ha una domanda: «🤖 Chiedi a Tappo», che ti risponde subito su come funziona Barattolo, e «💬 Assistenza», la chat con lo staff, che prima stava in «Privacy».
dove: scheda Profilo, sezione «Supporto», voci «🤖 Chiedi a Tappo» e «💬 Assistenza».
leva: TAPPO_LINK accesa di serie
pubblico: sì

## 2026-11-16 · p2p-onchain-commissione
frase: Negli scambi P2P on-chain la commissione ora è la stessa degli scambi Lightning, metà a testa e con gli stessi sconti per pionieri e livello 5: chi vende la deposita insieme ai sats, chi compra la trova tolta dai sats che riceve. La vedi nella riga «Fee P2P» del conto, già prima di prendere. Gli acquisti del mercatino restano senza commissioni.
dove: la scheda «P2P», un ordine on-chain del libro: il foglio «Stai comprando sats» / «Stai vendendo sats» col conto, e la pagina dello scambio.
leva: P2P_ONCHAIN_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

## 2026-11-16 · p2p-tasti-rete
frase: Quando tocchi un ordine P2P, sotto «Stai comprando sats» o «Stai vendendo sats» ci sono già i due tasti «⚡ Lightning» e «₿ On-chain», accesi sulla rete dell'ordine. Se scegli l'altra rete vedi subito quanto costa lo swap e quanto ti arriva, prima ancora di prendere l'ordine, e il costo dello swap è una riga del dettaglio.
dove: la scheda «P2P», il foglio che si apre toccando un ordine del libro, Lightning o on-chain.
leva: P2P_ALTRA_RETE_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

## 2026-11-16 · p2p-tasti-lato
frase: In cima al libro P2P «Compra BTC» e «Vendi BTC» sono due pillole grandi: quella accesa, verde o corallo, dice da che parte del libro sei. Anche nel tema scuro.
dove: la scheda «P2P», in cima al libro.
leva: nessuna
pubblico: sì

## 2026-11-16 · ripubblica
frase: Quando pubblichi un ordine P2P c'è la sezione nuova «🔁 Ripubblica»: scrivi due prezzi di bitcoin, da X a Y. Se l'ordine scade senza che nessuno l'abbia preso e BTC è fra quei due prezzi, lo ripubblichiamo uguale, da solo, a ogni scadenza. Il bot ti dice ogni volta com'è andata. Lightning riparte appena apri Barattolo, on-chain subito. Vuoto = non succede niente.
dove: la scheda «P2P», il «+» per pubblicare: la sezione «🔁 Ripubblica» sotto il paracadute; la card del tuo ordine («🔁 Ripubblica da… a…») e la sua pagina, col tasto «Non ripubblicarlo più».
leva: P2P_RIPUBBLICA (nuova, accesa di serie)
pubblico: sì

## 2026-11-16 · app-negozio
frase: La cassa in negozio diventa «Barattolo Negozio»: una pagina tutta per chi sta al banco, con lo stesso account di Barattolo e senza la barra del mercatino. Dentro trovi la Cassa e le Vendite della cassa. Dal browser, per esempio sul tablet del negozio, ci entri dritto con barattolo.store/?app=negozio.
dove: Profilo → «Negozio e spedizioni» → «🏪 Cassa in negozio»; si torna a Barattolo con «↩ Barattolo» in alto a destra.
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

## 2026-11-16 · cassa-carrello
frase: La cassa di Barattolo Negozio adesso è fatta come il carrello: le card dei tuoi annunci con le foto, «Aggiungi» e poi − e +, e in fondo la barra col totale. Cambia solo il bottone: «Incassa», e i sats vanno dritti al tuo wallet, senza deposito di garanzia.
dove: Profilo → «Negozio e spedizioni» → «🏪 Cassa in negozio», scheda «🧾 Cassa».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

## 2026-11-16 · p2p-onchain-valute
frase: Negli scambi P2P on-chain ora puoi farti pagare anche in franchi svizzeri, ETH, Monero o USDe: i bitcoin restano nel deposito a tre chiavi, e chi compra paga nella sua moneta. E gli ordini on-chain restano nel libro 7 giorni, come quelli Lightning.
dove: la scheda «P2P», il «+» con «On-chain»: la valuta in cima al foglio «Pubblica»; nel libro, il filtro della valuta vale anche per le card on-chain.
leva: P2P_ONCHAIN_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

## 2026-11-16 · p2p-monete-mercato
frase: Gli ordini P2P in ETH, Monero e USDe ora funzionano come quelli in euro: a prezzo di mercato i sats si fanno quando qualcuno prende l'ordine, al cambio di quel momento, e anche questi ordini si possono ripubblicare da soli con «🔁 Ripubblica».
dove: la scheda «P2P», il «+» con valuta ETH, XMR o USDe, a prezzo di mercato; la sezione «🔁 Ripubblica» del foglio.
leva: P2P_COIN_ATTIVO accesa di serie
pubblico: sì

## 2026-11-16 · p2p-banner-tempo
frase: In cima al libro P2P ora ci sono tre rettangoli «Novità», ognuno col suo tutorial: On-Chain arancio, le stablecoin USDT e USDe in verde, ETH e Monero in blu. La card del prezzo di bitcoin è blu notte, e il tempo rimasto di un ordine è una riga con la barra, anche quando prendi un ordine on-chain.
dove: la scheda «P2P», in cima al libro; il foglio che si apre toccando un ordine, alla riga «Tempo rimasto».
leva: nessuna
pubblico: sì

## 2026-11-16 · payjoin
frase: Negli acquisti on-chain del mercatino arriva il PayJoin: se il tuo wallet lo sa fare (Sparrow, BlueWallet, Wasabi, Bull Bitcoin, Cake Wallet), mentre paghi Barattolo aggiunge una sua moneta alla transazione. Più privacy per te, stessa cifra, e il deposito di garanzia riceve gli stessi sats. Se il wallet non lo sa fare, si paga come sempre.
dove: Il pagamento on-chain di un ordine: il QR e «₿ Apri nel wallet»; la riga «🔀 PayJoin» nel foglio dice quando c'è.
leva: PAYJOIN_ATTIVO (accesa di serie)
pubblico: sì

## 2026-11-16 · notifica-apre-annuncio
frase: Toccando l'avviso di un annuncio, che arrivi dal bot, dal canale o come notifica sul telefono, adesso si apre la pagina di quell'annuncio, non più la home.
dove: gli avvisi «🔎 Un annuncio fa per te!», i post del canale, gli avvisi delle offerte e dei nuovi annunci, nel bot e nelle notifiche del telefono.
leva: nessuna
pubblico: sì

## 2026-11-16 · p2p-mappa-recenti
frase: Nella home gli scambi P2P mostrano anche gli ordini on-chain (USDe, ETH, Monero compresi), col fulmine ⚡ o la ₿ in fondo alla card per dire subito la rete. Nel libro la mappa 🗺️ c'è sempre, «Più recenti» mescola on-chain e Lightning, scorrendo i rettangoli «Novità» diventano uno solo, e «🔁 Ripubblica» c'è anche in «Compra BTC» con Barattozon.
dove: la home, fila «Scambi P2P»; la scheda «P2P», in alto accanto alla campanella; la pillola «Ordina» con «Più recenti».
leva: nessuna
pubblico: sì

## 2026-11-16 · esauriti-elimina-zona
frase: Un annuncio esaurito che non tornerà, come un oggetto usato venduto una volta, adesso si può eliminare: sparisce dal tuo negozio, mentre ordini e recensioni restano. E quando pubblichi un annuncio nuovo la «Zona» è già scritta con quella dell'ultimo, e la cambi quando vuoi.
dove: «I tuoi annunci» nel Profilo, il tasto «🗑 Elimina» accanto a «🔄 Rifornisci»; la pagina dell'annuncio esaurito, «🗑 Elimina l'annuncio»; il form «Vendi», campo «Zona».
leva: nessuna
pubblico: sì

## 2026-11-16 · codice-ritiro
frase: Spedizioni a un locker o a un punto di ritiro: quando il codice per ritirare il pacco è pronto, chi ha comprato lo trova in cima all'ordine, subito sotto il prezzo. E chi vende sa fin dalla spedizione se il codice arriverà a lui, da incollare nell'ordine, o direttamente a chi compra.
dove: l'ordine, riquadro «📦 Istruzioni per il ritiro»; per chi vende il riquadro «📦 Spedisci» e il messaggio del bot alla spedizione.
leva: nessuna
pubblico: sì

## 2026-11-16 · categoria-connettori
frase: Se colleghi un negozio Shopify o WooCommerce adesso puoi scegliere la categoria dei suoi prodotti: se vendi tutto dello stesso tipo la dichiari una volta e vale per tutti, anche per quelli già entrati. Se non la scegli, Barattolo usa la categoria del tuo negozio quando è una delle sue, invece di mettere tutto in «Altro».
dove: Profilo → «Il tuo catalogo» → «📥 Importa in blocco / catalogo esterno», ✏️ sul negozio collegato, casella «Categoria dei prodotti».
leva: nessuna
pubblico: sì

## 2026-11-16 · posta-senza-tracciamento
frase: Chi vende può spedire con la posta senza tracciamento senza fingere una consegna a mano: la sceglie fra i corrieri quando segna la spedizione, e chi compra legge che il pacco non si può seguire. Se hai segnato «Consegna a mano» su un ordine che invece hai spedito, o hai scritto un codice sbagliato, nell'ordine c'è il bottone per correggerlo, e chi compra viene avvisato.
dove: l'ordine del venditore: «📦 Segna come spedito», la voce «✉️ Posta senza tracciamento»; sotto, il bottone «✏️ Correggi il tracciamento» (o «🚚 Era una spedizione?»).
leva: nessuna
pubblico: sì

## 2026-11-16 · codici-uno-alla-volta
frase: Se compri più codici digitali nello stesso ordine (per esempio 10 buoni), adesso si aprono uno alla volta: provi il primo, tocchi «✅ Funziona» e vedi il successivo. Se un codice non funziona la disputa riguarda solo quello, e i codici mai aperti ti tornano: chi prova a imbrogliare rischia un codice, non tutto l'ordine. Chi vende scrive ogni codice nel suo riquadro.
dove: l'ordine di un codice online da 2 pezzi in su: per chi vende il form «Consegna i codici», per chi compra il pannello «🔓 Apri il codice 1».
leva: CODICI_UNO_ALLA_VOLTA (accesa di serie)
pubblico: sì

## 2026-11-16 · backup-obbligato
frase: Prima del tuo primo scambio P2P on-chain, se le tue 12 parole non hanno ancora una copia (nel cloud di Telegram o sui relay Nostr), Barattolo te le mostra e te ne fa riscrivere tre: così i sats nel deposito di garanzia non restano mai chiusi da una chiave persa. Chi entra da Telegram o con Nostr di solito non vede niente di nuovo.
dove: Il P2P, quando pubblichi o prendi un ordine on-chain; Profilo → «₿ On-chain» → «Le ho scritte su carta».
leva: nessuna
pubblico: sì

## 2026-11-17 · onchain-come-lightning
frase: Negli scambi P2P on-chain, quando i bitcoin sono nel deposito di garanzia, chi compra ha 24 ore per pagare in USDT, ETH, Monero o USDe e 72 ore in euro o franchi, col conto alla rovescia su card e pagina. A scambio concluso si lascia la recensione come negli scambi Lightning, il bot dice i sats netti, e lo scambio conta nei «✅ scambi P2P».
dove: «I miei scambi», la card on-chain e la pagina dello scambio (riga «Tempo per pagare», riquadro «⭐ Lascia una recensione»); il messaggio del bot «Scambio on-chain concluso!».
leva: nessuna
pubblico: sì

## 2026-11-17 · primo-wallet
frase: Chi non ha ancora un wallet trova una guida in tre passi: scarica Wallet of Satoshi, salva le parole di recupero, poi il passo che ti serve: come mettere i primi sats e inquadrare il QR se stai pagando, dove trovare il tuo indirizzo Lightning se stai incassando. I sats restano nel tuo wallet, non su Barattolo. Al primo indirizzo salvato arriva il distintivo «📥 Pronto a incassare».
dove: Profilo, la casella verde «👛 Il tuo primo wallet» sotto i giorni di fila (finché non hai un Lightning address); e il bottone «👛 Non hai un wallet? Ti spieghiamo come fare» sotto la fattura da pagare, nel riquadro «💰 Come ricevi i tuoi sats» di un ordine e nel Profilo accanto al Lightning address.
leva: nessuna
pubblico: sì

## 2026-11-17 · totali-acquisti
frase: Nel Profilo ora vedi anche quanto hai comprato: negli ultimi 30 giorni e da sempre, quanti acquisti e quanti sats hai pagato in tutto, spedizione compresa. Se non hai annunci il cassetto si chiama «I tuoi acquisti».
dove: Profilo → «Negozio e spedizioni» → «📊 Il tuo negozio» (o «📊 I tuoi acquisti»), sezione «🛍️ Acquisti conclusi».
leva: ACQUISTI_NEL_PROFILO spenta di serie (17 nov sera, privacy: Andrea «gli acquisti non li aggiungere»)
pubblico: no

## 2026-11-17 · etichetta-alimenti
frase: Chi vende alimenti e bevande può aggiungere all'annuncio l'etichetta: peso netto, ingredienti, allergeni e tabella dei valori nutrizionali, come sulla confezione. Chi compra la legge nella pagina dell'annuncio prima di comprare, uguale per tutti, con gli allergeni in grassetto. È facoltativa, ma la legge europea la chiede per gli alimenti venduti online.
dove: Vendi → categoria «Alimenti e bevande» → riquadro «🏷️ Etichetta dell'alimento» sotto la descrizione; nella pagina dell'annuncio, la sezione «Etichetta» sotto la descrizione.
leva: ETICHETTA_ALIMENTI (accesa di serie)
pubblico: sì

## 2026-11-17 · avvisi-barattolo
frase: Quando metti un articolo nel tuo barattolo 🫙 puoi scegliere cosa farti dire dal bot su quell'articolo: se il prezzo scende, se arriva uno sconto lampo, se ne resta solo uno, se torna disponibile. Al massimo un avviso al giorno per articolo, con il tasto che apre l'annuncio.
dove: il barattolino 🫙 sulla foto di un annuncio, poi il foglietto «🔔 Avvisami se…»; per cambiare idea, Profilo → «Nel tuo barattolo» → la 🔔 accanto all'articolo.
leva: AVVISI_BARATTOLO_ATTIVI (accesa di serie)
pubblico: sì

## 2026-11-17 · spedisci-entro
frase: Quando vendi un oggetto da spedire, il messaggio del bot ti dice entro che giorno spedirlo, col tasto per aprire l'ordine. Nell'ordine trovi la stessa data e «📖 Come si spedisce?», una guida in quattro passi dall'imballo al tracciamento. Chi compra vede entro quando parte il pacco, e nei passi dell'ordine compaiono l'ora del pagamento e quella della spedizione.
dove: il messaggio «Hai venduto!» del bot; l'ordine del venditore, riquadro «📦 Spedisci» (riga «⏳ Spedisci entro…» e link «📖 Come si spedisce?»); i passi dell'ordine, per chi vende e per chi compra.
leva: nessuna
pubblico: sì

## 2026-11-17 · link-packlink
frase: Quando devi spedire un ordine e non hai ancora l'etichetta, nel riquadro della spedizione trovi il link «Spedisci con Packlink»: compri l'etichetta là (Poste, BRT, InPost e altri, da 5,48 €, in euro) e incolli nell'ordine il codice del corriere.
dove: l'ordine venduto, riquadro «Spedisci e inserisci il tracciamento», sotto il campo del codice.
leva: nessuna
pubblico: sì

## 2026-11-17 · chiedi-locker
frase: Se un venditore non spedisce ai locker o ai punti di ritiro, alla cassa la riga del locker adesso resta visibile, spenta, con il tasto «Chiedi al venditore se spedisce con InPost o Poste»: lui riceve un avviso dal bot (senza sapere chi ha chiesto) che lo porta a spuntare i suoi corrieri, e quando lo fa chi aveva chiesto riceve l'avviso. Una richiesta per venditore ogni 7 giorni.
dove: la cassa di un annuncio a spedizione di un venditore senza InPost, Poste o SDA, sotto «Spedizione a un indirizzo»; il messaggio del bot «Qualcuno vorrebbe ricevere … in un locker» col bottone «📦 Come spedisci».
leva: RICHIESTA_PUNTI (accesa di serie)
pubblico: sì

## 2026-11-17 · onchain-controparte
frase: Negli scambi P2P on-chain ora vedi chi c'è dall'altra parte: appena l'ordine è preso, nella pagina dello scambio compare la sua scheda con faccia, nome e stelline, come negli scambi Lightning. Toccando la faccia si apre il suo negozio.
dove: P2P → «I miei scambi» → uno scambio on-chain preso, sotto la nota dello stato.
leva: nessuna
pubblico: sì

## 2026-11-17 · onchain-annulla
frase: Negli scambi P2P on-chain chi compra può annullare con «✕ Annulla» finché chi vende non ha ancora depositato i sats, come negli scambi Lightning: prima bisognava aspettare la fine del tempo del deposito.
dove: P2P → «I miei scambi» → uno scambio on-chain preso, in attesa del deposito.
leva: nessuna
pubblico: sì

## 2026-11-17 · barattozon-onchain
frase: Barattozon adesso c'è anche on-chain: in «Vendi BTC» col tabacchino puoi toccare «On-chain» in cima al foglio e pubblicare il tuo PayCode nel libro on-chain. Serve un PayCode che scade fra almeno 12 ore; chi prende l'ordine vede il codice solo quando i tuoi sats sono confermati nel deposito di garanzia, poi lo paga al tabacchino e tocca «Ho pagato al tabacchino».
dove: Il P2P, «Vendi BTC» → la capsula Barattozon (o il + col metodo «Contanti al tabacchino»), il tasto «On-chain» in cima al foglio; nello scambio il riquadro «🧾 Il PayCode da pagare al tabacchino».
leva: P2P_ONCHAIN_BARATTOZON (accesa di serie)
pubblico: sì

## 2026-11-17 · livelli-carosello
frase: I tuoi livelli adesso si sfogliano: nel Profilo, sotto «Livello e titolo», ogni livello è una tessera da scorrere col dito. Sulla tua c'è l'anello con i tuoi XP sulla soglia del prossimo, i livelli già passati hanno la spunta, quelli davanti il lucchetto, e sotto vedi i vantaggi del livello che stai guardando: ✅ quelli già tuoi, 🔒 quelli da sbloccare.
dove: Profilo → «🎖 Livello e titolo» → «I vantaggi di ogni livello».
leva: nessuna
pubblico: sì

## 2026-11-17 · stradina-obiettivi
frase: Nel Profilo c'è «🚀 Rotta per la Luna»: un tabellone lunghissimo dalla Terra alla Luna, su una mappa in otto zone raccontate da Tappo, fino all'halving del 2028. Ogni casella è una competenza (l'incasso automatico in Lightning, il wallet on-chain, la doppia configurazione Telegram + Nostr, il primo acquisto…): fatta, diventa una moneta d'oro e Tappo avanza. I tuoi amici sono pedine sul tabellone.
dove: Profilo → «Livello e recensioni» → «🚀 Rotta per la Luna».
leva: STRADINA_ATTIVA spenta di serie
pubblico: no

## 2026-11-17 · contante-per-posta
frase: Nel P2P c'è un metodo in più, «Contante per posta»: chi compra sats spedisce le banconote a chi le vende, in una busta sigillata nascosta in un pacco, con un servizio tracciato. Le regole sono scritte nello scambio: chi spedisce filma l'imballo col numero di tracciamento in vista, chi riceve filma l'apertura prima di liberare i sats, e chi prende l'ordine blocca una piccola cauzione.
dove: P2P → «Pubblica» → «Altri metodi ▾» → «Contante per posta»; la pagina dello scambio con le regole; «Info P2P», voce «Contante per posta».
leva: P2P_POSTA_ATTIVO (nuova, spenta di serie: in produzione resta spenta per scelta di Andrea, accesa solo sul collaudo)
pubblico: no

## 2026-11-17 · chat-onchain
frase: Anche negli scambi P2P on-chain adesso c'è la chat fra chi compra e chi vende, come nel Lightning: cifrata, con foto e PDF, da quando l'ordine è preso a quando i sats vengono liberati. Quando l'altra persona ti scrive, il bot te lo dice col tasto che apre dritto la chat; in una disputa il moderatore la può leggere, e a scambio finito si cancella.
dove: la pagina di uno scambio on-chain preso, riquadro «💬 Chat con …» in fondo (il richiamo «💬 Chat» in cima porta giù); il messaggio del bot «Hai un nuovo messaggio nello scambio on-chain» col bottone «🟠 Apri lo scambio».
leva: P2P_CHAT_SCAMBIO (la stessa della chat del Lightning, accesa di serie)
pubblico: sì

## 2026-11-17 · serie-giorni
frase: Nel tuo Profilo c'è una fiamma che conta quanti giorni di fila hai aperto Barattolo, col tuo record e gli ultimi sette giorni. Basta entrare una volta al giorno. Se salti un giorno riparte da 1 e il record resta. Non dà punti né premi e la vedi solo tu: è solo la soddisfazione di non fermarla.
dove: Profilo, nel riquadro col tuo nome (riga «5 giorni di fila · record 12») e la fila dei sette giorni subito sotto; al primo accesso del giorno il saluto che compare in basso per un paio di secondi.
leva: SERIE_GIORNI_ATTIVA (accesa di serie)
pubblico: sì

## 2026-11-17 · premi-fedelta
frase: I negozi possono premiare chi torna a comprare: nel Profilo, «🎀 Premi fedeltà», chi vende scrive fino a quattro soglie in euro col suo regalo («da 100 € la borsa, da 200 € la tazza»). Barattolo conta quanto ogni cliente ha speso lì e, passata la soglia, il premio compare sul suo ordine successivo: il venditore lo mette nel pacco. Sulla pagina del negozio vedi i premi e quanto hai già speso.
dove: Profilo → «🎀 Premi fedeltà»; la pagina di un negozio, riga «🎀 Premi fedeltà» sotto le promesse; il dettaglio dell'ordine, riga «🎀 Premio fedeltà»; il messaggio del bot «Premio fedeltà!».
leva: PREMI_FEDELTA_ATTIVI (accesa di serie)
pubblico: sì

## 2026-11-17 · nip05-utenti
frase: Dal livello «Bottega avviata» puoi avere gratis il tuo nome verificato su Nostr, tipo mario@barattolo.store. Lo scegli nel Profilo, lo incolli nel campo NIP-05 del tuo profilo Nostr e le app Nostr mostrano la spunta accanto al tuo nome. Serve una chiave Nostr collegata con una firma.
dove: Profilo → «Impostazioni» → «🆔 Nostr e identità» → riga «✔️ Nome verificato su Nostr» → «Prendi questo nome» e poi «📋 Copia»; nella scala dei livelli, tra i vantaggi di «Bottega avviata».
leva: NIP05_UTENTI_ATTIVO (accesa di serie)
pubblico: sì

## 2026-11-17 · caccia-a-tappo
frase: È arrivata la Caccia a Tappo, il gioco di Barattolo. Ogni giorno Tappo si nasconde in un annuncio vero, diverso per ognuno: leggi gli indizi, apri gli annunci e tocca «Tappo è qui?». Chi lo trova vince i bulloni 🔩, accende i barattoli della dispensa, sale di grado e completa le sfide. Coi bulloni prendi cappellini, attrezzi e 5 posti in più nei preferiti. Si gioca gratis: i bulloni non sono sats.
dove: Profilo → «Livello e recensioni» → «🔩 Caccia a Tappo», nella Mini App, nell'app e sul sito; il tasto «Tappo è qui?» nella scheda di ogni annuncio, quando la caccia del giorno è aperta.
leva: GIOCO_TAPPO_ATTIVO spenta di serie
pubblico: no

## 2026-11-17 · mondo-di-tappo
frase: Sul tabellone dei livelli arrivano le missioni di Tappo: otto scene brevi a carte sulla storia del denaro, il deposito di garanzia, le tue chiavi, Lightning, la privacy e Nostr, ognuna col bottone per farlo davvero. Danno bulloni 🔩 e montano il razzo con cui Tappo vuole arrivare sulla Luna. E nella Caccia a Tappo c'è il Mondo: la dispensa da girare, coi barattoli da aprire.
dove: Profilo → «Livello e recensioni» → «🚀 Rotta per la Luna»: la missione sta subito prima della casella che insegna; tutte anche nella «🔩 Caccia a Tappo», lì accanto, schede «Sfide» e «Mondo».
leva: GIOCO_TAPPO_ATTIVO spenta di serie
pubblico: no

## 2026-11-17 · profilo-semplice
frase: Il Profilo è più semplice da leggere: ogni casella dice cosa c'è dentro. Ci sono «Annunci», «Il tuo negozio», «Spedizioni e sconti», «Quando compri», «Wallet e incassi», «Livello e recensioni», «Impostazioni» e «Aiuto».
dove: scheda Profilo, le caselle sotto il riquadro col tuo nome.
leva: nessuna
pubblico: sì

## 2026-11-17 · raccolta
frase: Su Barattolo si può aprire una raccolta fondi in sats: un obiettivo, una scadenza fino a 60 giorni e una barra che si riempie. Chi vuole sostenerla manda uno zap, che va dritto al wallet di chi raccoglie, senza commissioni. Per aprirne una servono tre vendite concluse e un indirizzo Lightning; ogni raccolta la guardano i moderatori prima della vetrina.
dove: Profilo → «Il tuo negozio» → «🎯 Raccolte fondi» (lì il bottone «🎯 Apri una raccolta»); in vetrina la tessera «Raccolte» accanto ad Aste, quando c'è almeno una raccolta; nella scheda di una raccolta il bottone «⚡ Sostieni con uno zap».
leva: RACCOLTE_ATTIVE spenta di serie (e i depositi di garanzia, RACCOLTA_GARANTITA_ATTIVA, spenti di serie)
pubblico: no

## 2026-11-17 · inglese-tappa-1
frase: Barattolo si legge anche in inglese: se il tuo Telegram o il tuo browser non sono in italiano, la vetrina, gli annunci e l'acquisto compaiono in inglese da soli, coi prezzi all'inglese (1,234.50 €). Ordini, P2P, Profilo e bot arrivano nelle prossime tappe. Per provarlo da un telefono italiano apri barattolo.store/?lingua=en (?lingua=it per tornare).
dove: tutta la Mini App e il sito per chi ha Telegram o il browser in una lingua diversa dall'italiano; la pagina «Il pagamento protetto» (barattolo.store/sicurezza) anche lei.
leva: LINGUA_INGLESE (spenta di serie dal 17 nov sera, scelta di Andrea: in produzione arriva spenta e si accende dal config; accesa sul collaudo)
pubblico: sì

## 2026-11-17 · assistenza-screenshot
frase: Nella chat con l'assistenza di Barattolo ora puoi allegare anche degli screenshot, fino a tre per messaggio: lo staff vede subito cosa vedi tu, e può risponderti anche lui con uno screenshot. Li vedete solo tu e lo staff.
dove: Profilo → «Aiuto» → «💬 Assistenza», il bottone «📎 Allega screenshot» sotto la casella.
leva: ASSISTENZA_ATTIVA (quella dell'assistenza, già accesa)
pubblico: sì

## 2026-11-17 · chiavi-dalle-parole
frase: Le chiavi degli scambi P2P adesso nascono dalle 12 parole del tuo wallet on-chain, le stesse che hanno già la loro copia nel cloud di Telegram o sui relay Nostr. Così, ovunque apri Barattolo con quelle parole, i tuoi scambi nuovi li governi da lì: telefono, Telegram Desktop o browser. Gli scambi già aperti continuano come prima, dal dispositivo dove li hai presi.
dove: lo scambio P2P (pubblicare o prendere un ordine); il foglio «Il tuo profilo di scambio» lo dice; se su un dispositivo le parole non ci sono, il primo gesto chiede di incollarle da Profilo → «Wallet e incassi».
leva: nessuna
pubblico: sì

## 2026-11-17 · onchain-rimborso-liscio
frase: Rinunciare a uno scambio P2P on-chain è più semplice. Chi vende bitcoin scrive dove riavere i sats nel foglio stesso, prima di bloccarli. Se quell'indirizzo manca, il «Rinuncio» di chi compra non dà più errore: viene registrato e il bot avvisa chi vende col tasto che apre lo scambio. E se firmi da un dispositivo senza la chiave del wallet, Barattolo la cerca da solo o ti chiede lì le 12 parole.
dove: P2P on-chain: il foglio «🔒 Blocca i sats» col riquadro «Dove tornano i sats?»; la pagina dello scambio, tasto «↩️ Rinuncio: rimborsa chi vende»; il foglio «🔑 Serve la chiave del tuo wallet»; i messaggi del bot «Chi compra vuole rinunciare» e «Ora puoi rinunciare».
leva: nessuna
pubblico: no

## 2026-11-17 · onchain-tempo-bonifico
frase: Negli scambi P2P on-chain in euro e franchi il tempo per pagare scende da 72 a 24 ore, come per USDT e monete. In cambio, da «Ho inviato» chi vende ha 48 ore per veder arrivare il bonifico e liberare i sats: se passano senza rilascio, il bot avvisa tutti e due e indica la disputa. Niente si annulla da solo: i bitcoin restano nel deposito di garanzia.
dove: P2P on-chain: la card in «I miei scambi» e la riga «Tempo per pagare» nella pagina dello scambio; nello stato «Euro inviati» la frase con le 48 ore; i messaggi del bot «Il tempo per pagare è finito» e «Sono passate 48 ore da «Ho inviato gli euro»».
leva: nessuna
pubblico: sì

## 2026-11-17 · annullo-registrato
frase: Se prendi un ordine P2P, tocchi «Annulla» e l'annullo non arriva al coordinatore, alla scadenza del tempo non ti viene più contato uno scambio non completato: il bot te lo scrive nel messaggio.
dove: P2P Lightning: la pagina dello scambio appena preso, «✕ Annulla» e «Sì, annulla»; il messaggio del bot «Non hai proseguito in tempo» con la riga «Avevi chiesto di annullare».
leva: nessuna
pubblico: no

## 2026-11-17 · onchain-ritiro
frase: Negli scambi P2P on-chain, chi si ritira dopo che l'altro ha già bloccato i sats si vede contare uno «scambio non completato», come negli scambi Lightning, e chi aveva bloccato i sats può lasciargli una recensione. Nessuna cauzione e nessuna penale in denaro. Il foglio di «Rinuncio» lo dice prima della firma. Non conta se chi vende non aveva ancora scritto dove pagare.
dove: P2P on-chain: il foglio «↩️ Rinunci allo scambio?»; la pagina dello scambio rimborsato, con la frase «scambio non completato» e il riquadro «⭐ Lascia una recensione» per chi aveva depositato; il messaggio del bot «Scambio on-chain annullato».
leva: nessuna
pubblico: sì

## 2026-11-17 · quanto-vuoto
frase: Quando prendi un ordine P2P con un intervallo (per esempio da 50 a 276 €), il campo dell'importo ora è vuoto: scrivi subito la cifra che vuoi, senza cancellare il minimo che prima c'era già scritto. Sotto ci sono i tasti «Minimo» e «Massimo» per metterla con un tocco.
dove: P2P: tocca un ordine con un intervallo, poi «Scegli»; foglio «Quanto vuoi scambiare?».
leva: nessuna
pubblico: no

## 2026-11-17 · onchain-contanti-luogo
frase: Gli ordini P2P on-chain in contanti ora hanno il luogo dello scambio, come quelli Lightning: chi pubblica scrive la zona, e la card la mostra con «📍». Vale anche lo stesso tetto in euro del contanti.
dove: P2P: «+», rete on-chain, metodo «Contanti», campo «Zona di scambio»; la card on-chain nel libro; il foglio che si apre toccandola.
leva: nessuna
pubblico: no

## 2026-11-17 · onchain-contanti-scambio
frase: Lo scambio P2P on-chain in contanti ora va come quello Lightning: chi vende scrive dove e quando vedervi, chi compra apre il navigatore, ognuno può segnare «📍 Sono qui» quando arriva, e il bottone è «Ho consegnato i contanti».
dove: P2P on-chain con metodo «Contanti»: la pagina dello scambio, riquadro «📍 Dove vedervi» e, a sats bloccati, il riquadro con «📍 Sono qui»; il bottone «💵 Ho consegnato i contanti».
leva: nessuna
pubblico: no

## 2026-11-17 · onchain-contanti-metodo
frase: Negli ordini P2P on-chain con «Contanti» insieme ad altri metodi ora scegli come pagare prima di prendere: con «Contanti» lo scambio va di persona, con appuntamento e «📍 Sono qui».
dove: P2P on-chain, tocca un ordine con più metodi fra cui «Contanti»: sotto il riassunto ci sono le pillole dei metodi.
leva: nessuna
pubblico: no

## 2026-11-17 · paracadute-su-giu
frase: Il paracadute degli ordini P2P adesso ha due scelte: una se BTC sale e una se BTC scende, ognuna 5%, 10%, 20% o nessuna. Così puoi tenere l'ordine se BTC sale e toglierlo se scende, o il contrario. Gli ordini già pubblicati restano come sono.
dove: P2P, foglio «Pubblica» → «🪂 Paracadute», le righe «📈 Se BTC sale» e «📉 Se BTC scende»; sulla card del tuo ordine «🪂 Paracadute ↑10% ↓5%».
leva: P2P_PARACADUTE (quella del paracadute, già accesa)
pubblico: sì

## 2026-11-17 · onchain-importi-grossi
frase: Per gli acquisti sopra 500 € la cassa ti propone da sola l'on-chain: nel «Come vuoi pagare?» On-chain porta «✅ Consigliato per questa cifra», perché con cifre così il Lightning spesso non passa. Il Lightning resta, con un avviso.
dove: Mercatino: un oggetto sopra 500 €, «Acquista», foglio «Come vuoi pagare?»; nel foglio della fattura Lightning la riga «⚠️ Sopra 500 € il Lightning spesso non passa».
leva: ONCHAIN_CONSIGLIATO_SOPRA_EURO accesa di serie (500)
pubblico: sì

## 2026-11-17 · inglese-tappa-2
frase: Barattolo è tutto in inglese: ordini, scambio P2P, Vendi, Profilo, aste, raccolte, avvisi e assistenza compaiono in inglese da soli se il tuo Telegram o il tuo browser non sono in italiano, coi prezzi all'inglese (1,234.50 €). Mancano solo i messaggi del bot e l'interruttore della lingua nel Profilo, in arrivo. Da un telefono italiano apri barattolo.store/?lingua=en (?lingua=it per tornare).
dove: tutta la Mini App e il sito, per chi ha Telegram o il browser in una lingua diversa dall'italiano: Ordini, P2P, Vendi, Profilo, aste, raccolte, cassa in negozio, swap, on-chain, avvisi, assistenza, privacy.
leva: LINGUA_INGLESE (spenta di serie dal 17 nov sera, scelta di Andrea: in produzione arriva spenta e si accende dal config; accesa sul collaudo)
pubblico: no

## 2026-11-17 · serie-classifica
frase: I giorni di fila adesso hanno una classifica: chi apre Barattolo da più giorni senza saltarne uno. Ci entri dal secondo giorno di fila, e a pari giorni si è a pari merito. La vede solo chi è entrato in Barattolo; se non vuoi comparire accendi «Non mostrarmi in classifica». Non dà punti né premi.
dove: Profilo, sotto la fila dei sette giorni, il bottone «Classifica Streak», con la fiamma. Per non comparire: Profilo, cassetto «Livello e recensioni», «🏆 Non mostrarmi in classifica».
leva: SERIE_GIORNI_ATTIVA (quella della serie, già accesa)
pubblico: sì

## 2026-11-17 · onchain-grossi-uscita
frase: Negli acquisti on-chain sopra 500 € chi vende riceve on-chain anche se aveva scelto Lightning, perché con cifre così il Lightning spesso non passa. L'ordine glielo dice con «Cifra grossa: ricevi on-chain».
dove: Ordini → una vendita pagata on-chain sopra 500 €, riquadro «Pagato on-chain»; il messaggio del bot quando chi compra conferma.
leva: ONCHAIN_CONSIGLIATO_SOPRA_EURO accesa di serie (500)
pubblico: sì

## 2026-11-17 · avviso-indirizzo
frase: Negli scambi on-chain chi vende sa quando chi compra ha scelto dove ricevere i sats: arriva un messaggio dal bot. E se tocca «Ricevuti» prima, Barattolo glielo dice e c'è «🔔 Ricordaglielo», che manda un promemoria a chi compra.
dove: P2P → «I miei scambi» → uno scambio on-chain con i sats nel deposito: la riga «⏳ Chi compra non ha ancora scelto il wallet» col bottone «🔔 Ricordaglielo», e il foglio di «Ricevuti: libera i sats»; il messaggio del bot «📍 Chi compra ha scelto dove ricevere».
leva: P2P_ONCHAIN_AVVISO_INCASSO accesa di serie
pubblico: sì

## 2026-11-17 · barattozon-oc-compra
frase: Barattozon on-chain adesso c'è anche in «Compra BTC»: scegli il tabacchino, tocca «On-chain» e scrivi da quanto a quanto. Chi prende l'ordine scrive il suo PayCode; tu lo vedi quando i suoi sats sono nel deposito di garanzia e lo paghi al tabacchino.
dove: Il P2P, «Compra BTC» → metodo «Contanti al tabacchino», il tasto «On-chain» in cima al foglio; chi prende tocca «🧾 Il tuo PayCode» e scrive importo, PayCode e scadenza.
leva: P2P_ONCHAIN_BARATTOZON (accesa di serie)
pubblico: sì

## 2026-11-18 · fiamma-giorno
frase: La prima volta al giorno che apri il Profilo, la tua serie te lo dice: il cerchio di oggi si accende piano come una brace e il numero dei giorni di fila sale da ieri a oggi. Una volta al giorno, e basta.
dove: Profilo, la riga «🔥 N giorni di fila» sotto il nome e la fila dei sette giorni, il cerchio «oggi».
leva: SERIE_GIORNI_ATTIVA (quella della serie, già accesa)
pubblico: sì

## 2026-11-18 · reso-spese-venditore
frase: Se in disputa l'oggetto va restituito perché era rotto, bloccato o diverso dall'annuncio, il moderatore può decidere che la spedizione di ritorno la paghi il venditore: ti manda l'etichetta prepagata nella chat dell'ordine entro 3 giorni e tu non paghi niente. Se non arriva, con un tocco avvisi i moderatori, che possono rimborsarti subito.
dove: Ordini → un ordine in reso deciso così: il riquadro «↩️ Rispedisci l'oggetto per il rimborso» con «🏷️ Il reso lo paga il venditore», e dopo 3 giorni il bottone «⏰ Il venditore non ha mandato l'etichetta». Chi vende vede «🏷️ Il reso è a tue spese» con «💬 Manda l'etichetta in chat». Il moderatore ha il bottone «📦 Reso a spese del venditore» fra le decisioni della disputa.
leva: nessuna
pubblico: sì

## 2026-11-18 · etichetta-obbligatoria
frase: Chi vende alimenti o bevande ora compila la tabella nutrizionale, come chiede la legge europea per la vendita online. Se per il suo prodotto non serve (frutta fresca, spezie, alcolici, artigianale in piccole quantità…) tocca «Non dovuta per legge» e sceglie il motivo, che chi compra legge nell'annuncio. Si possono aggiungere anche origine, conservazione, lotto e scadenza.
dove: Vendi → categoria «Alimenti e bevande» → riquadro «🏷️ Etichetta dell'alimento» (tabella, «Non dovuta per legge», Origine, Conservazione, Lotto, Scadenza); nella pagina dell'annuncio, la sezione «Etichetta» sotto la descrizione.
leva: ETICHETTA_OBBLIGATORIA (accesa di serie)
pubblico: sì

## 2026-11-18 · bitcoin-only
frase: Nel filtro del P2P ci sono due pillole nuove: «No altcoin» toglie ETH e XMR, «No stablecoin» toglie USDT e USDe; accese tutte e due restano solo euro e franchi. Il telefono si ricorda la scelta. E ricorda: quelle monete servono solo a pagare, da noi si compra e si vende sempre bitcoin.
dove: P2P → «Filtro» → «Valute», le ultime due pillole «No altcoin» e «No stablecoin», poi «Applica». Spente di serie.
leva: P2P_BITCOIN_ONLY_ATTIVO (accesa di serie)
pubblico: sì

## 2026-11-18 · ammanco-p2p-onchain
frase: Negli scambi on-chain un deposito con pochi sats in meno (succede con gli swap) non blocca più lo scambio: li copre il margine per la rete e si va avanti. Se ne mancano di più, chi ha depositato può toccare «↩️ Annulla e riprendi i sats» e riaverli sul suo wallet.
dove: P2P → «I miei scambi» → uno scambio on-chain preso: la riga «👀 Visti in rete … ne mancano N» e il bottone «↩️ Annulla e riprendi i sats» di chi ha depositato; il messaggio del bot «Sono arrivati N sats in meno».
leva: nessuna
pubblico: sì

## 2026-11-18 · sottocategorie
frase: In Esplora le categorie hanno le sottocategorie: tocchi una categoria e si apre una tendina, con il numero di annunci accanto a ogni voce. Per esempio Informatica → Computer e portatili, oppure Tablet ed e-reader. E quando pubblichi Barattolo propone la sottocategoria leggendo il titolo; puoi cambiarla tu.
dove: Esplora → «Esplora per categorie», tocca una categoria: la tendina sotto la card («Tutta la categoria» e le sottocategorie con annunci); la card accesa scrive la scelta sotto il nome. Vendi → il campo «Sottocategoria (facoltativa)» sotto la categoria.
leva: SOTTOCATEGORIE_VETRINA (accesa di serie)
pubblico: sì

## 2026-11-18 · premi-fedelta-2
frase: Premi fedeltà dei negozi: le soglie ora si scrivono in euro o in sats, e il regalo si sceglie fra gli articoli del proprio negozio. Chi ha un premio da riscuotere lo sa subito: glielo dicono il bot, la pagina del negozio e la scheda degli articoli. E ogni negozio vede la classifica dei suoi clienti per totale speso, in sats o in euro.
dove: Profilo → «🎀 Premi fedeltà»: l'interruttore «€ euro / ₿ sats», la tendina del regalo («✏️ Lo scrivo io» o un articolo 🎁), e sotto «🏆 I tuoi clienti» → «Guarda chi ha speso di più da te»; la pagina di un negozio, riga «🎁 Hai un premio da riscuotere»; la scheda di un articolo di quel negozio; i messaggi del bot «Premio fedeltà!», «Ordine pagato» e «Hai venduto».
leva: PREMI_FEDELTA_ATTIVI e CLASSIFICA_CLIENTI_ATTIVA (accese di serie)
pubblico: sì

## 2026-11-18 · apri-esplora-annuncio
frase: Negli avvisi dei nuovi annunci ogni titolo adesso è un link: toccandolo si apre la pagina di quel prodotto. Se l'annuncio nuovo è uno solo, il bottone in fondo diventa «🫙 Apri l'annuncio»; «🫙 Apri Esplora» resta per sfogliare tutti i nuovi coi tuoi filtri.
dove: il bot, l'avviso «🆕 N nuovi annunci nel mercatino» e quello «🔔 … ha pubblicato» di un venditore che segui.
leva: nessuna
pubblico: sì

## 2026-11-18 · vetrina-pulita
frase: I canali di Barattolo si puliscono da soli: quando un ordine P2P viene preso, annullato o scade, il suo post sparisce, così lì trovi solo ordini che puoi ancora prendere (l'annuncio venduto del mercatino resta, con «✅ Venduto»). E gli avvisi dei nuovi ordini P2P adesso dicono ordine per ordine se per te è un «🟢 Compra BTC» o un «🔴 Vendi BTC», e puoi sceglierli anche per metodo di pagamento.
dove: i canali Telegram di Barattolo; nel P2P la campanella 🔔 in alto (o Profilo → «🔔 Avvisi») → «Avvisami dei nuovi ordini P2P»: le chip «Compra BTC» e «Vendi BTC» e la sezione nuova «Metodo di pagamento»; il messaggio del bot «🔔 N nuovi ordini nel libro P2P».
leva: VETRINA_SI_PULISCE (accesa di serie)
pubblico: sì

## 2026-11-18 · chiedi-annullo
frase: Negli scambi on-chain chi ha messo i sats nel deposito può chiedere a chi compra di annullare: il bot glielo scrive, e se è d'accordo tocca «Rinuncio» e i sats tornano indietro. Si chiede prima che chi compra dica di aver pagato.
dove: P2P → «I miei scambi» → uno scambio on-chain col deposito fatto: il bottone «🙏 Chiedi a chi compra di annullare».
leva: nessuna
pubblico: sì

## 2026-11-19 · negozi-firma-ripiego
frase: Chi ha un negozio collegato e una chiave Nostr sua ha 3 giorni per firmare i suoi prodotti e pubblicarli a nome suo; se non lo fa, li pubblica Barattolo, così compaiono comunque su Nostr. Se firma dopo, tornano a nome suo da soli.
dove: nessun bottone nuovo: il titolare firma come sempre con «✍️ Firma i tuoi N annunci per Nostr» nel Profilo; passati 3 giorni succede da solo al giro del negozio.
leva: NEGOZI_FIRMA_RIPIEGO_GIORNI (3 di serie)
pubblico: sì

## 2026-11-18 · negozi-su-nostr
frase: I prodotti dei negozi collegati (Shopify e WooCommerce) adesso escono anche su Nostr, come tutti gli altri annunci di Barattolo: un annuncio per prodotto, con le varianti (taglie, colori) raccolte in uno solo col prezzo «da». Si aggiornano da soli quando cambiano prezzo o disponibilità, e un prodotto tolto dal negozio sparisce anche da lì.
dove: nessun bottone: succede da solo a ogni giro del negozio (una volta all'ora); i prodotti si vedono in qualunque app Nostr che mostra gli annunci (NIP-99).
leva: NEGOZI_SU_NOSTR (accesa di serie)
pubblico: sì

## 2026-11-18 · amber-da-solo
frase: Dal telefono entrare con Nostr è più comodo: tocchi «Entra con nostrconnect» e il tuo firmatario si apre da solo per chiederti l'ok, Amber su Android e Clave su iPhone. Approvi, torni su Barattolo e sei dentro, senza copiare e incollare nessuna stringa.
dove: dal sito nel browser, «…o entra con Nostr» → «📱 Entra con nostrconnect»; se l'app non si apre da sola, il bottone «📲 Apri Amber e approva» (su iPhone «Apri Clave e approva»). Dal computer resta il codice QR da inquadrare.
leva: NOSTRCONNECT_APRI_APP (accesa di serie)
pubblico: sì

## 2026-11-18 · tempo-pagamento
frase: Nel P2P chi vende sceglie con un orologio quanto tempo ha chi compra per pagare, da 15 minuti a 24 ore (sotto le 24 solo coi metodi veloci, come SEPA Instant, Revolut o USDT). Chi prende lo vede già nel libro («⏱ 30 min»), e allo scadere senza «Ho inviato» lo scambio Lightning si annulla da solo e i sats tornano a chi vende; sull'on-chain si apre la disputa.
dove: P2P → «Pubblica» → «Vendi BTC», la sezione «Tempo per pagare» (il cursore con l'anello) sotto «Chi può prendere l'ordine»; sulla card del libro il bollino «⏱ …» per i tempi sotto le 24 ore; nel dettaglio dell'ordine la riga «Se lo prendi hai…»; nella pagina dello scambio il riquadro con l'anello.
leva: P2P_TEMPO_PER_PAGARE (accesa di serie); sull'on-chain compare con la promozione, sul Lightning solo dopo la -bar10 sul nodo (patch 0013): «pubblico» diventa sì quel giorno
pubblico: no

## 2026-11-18 · cauzione-a-scelta
frase: Negli scambi P2P on-chain chi vende può chiedere una cauzione a chi prende il suo ordine, con qualunque metodo: una piccola cauzione in Lightning col QR (il 3%, almeno 1000 sats) che torna a fine scambio. Chi prende la perde se rinuncia dopo il deposito o se lascia scadere il tempo per pagare senza «Ho inviato», e metà va a chi vende.
dove: P2P → «Pubblica» → «Vendi BTC» a rete on-chain, la sezione «Cauzione di chi prende» («No» / «🔐 Chiedila») dopo «Tempo per pagare»; sulla card del libro il bollino «🔐 Cauzione»; nel foglio di chi prende la riga «Chi vende chiede una cauzione» e il foglio «🔐 Blocca la cauzione»; il foglio di «↩️ Rinuncio» lo ricorda.
leva: P2P_ONCHAIN_CAUZIONE_A_SCELTA (accesa di serie), ma vive sopra P2P_ONCHAIN_CAUZIONE e il suo macaroon (DA-FARE-ANDREA voce 20) e, a porticina chiusa, solo per i moderatori: «pubblico» diventa sì quando la cauzione on-chain si apre a tutti
pubblico: no

## 2026-11-18 · annullo-chiesto
frase: Negli scambi on-chain, se chi vende chiede di annullare e chi compra accetta toccando «Rinuncio», a chi compra non si conta più nessuno «scambio non completato»: sta facendo un favore.
dove: P2P → uno scambio on-chain dopo «🙏 Chiedi a chi compra di annullare»: il foglio di «↩️ Rinuncio» non avvisa più del «non completato».
leva: nessuna
pubblico: sì

## 2026-11-18 · connettori-ripartono
frase: Chi ha collegato un negozio Shopify o WooCommerce non deve più riaccenderlo a mano se il sito è rimasto giù per qualche ora: Barattolo riprova da solo una volta al giorno e, appena il negozio risponde, il collegamento riparte e il bot te lo dice.
dove: Profilo → «📥 Carica tanti annunci insieme» → «Catalogo esterno»: la riga del negozio fermo dice «⚠️ non risponde · riprovo da solo ogni giorno»; i messaggi del bot «Il collegamento col tuo negozio non risponde» e «Il tuo negozio risponde di nuovo».
leva: nessuna
pubblico: no

## 2026-11-18 · apri-ordine-notifica
frase: Negli avvisi dei nuovi ordini P2P ogni riga adesso apre il suo ordine: tocca «🟢 Compra BTC» o «🔴 Vendi BTC» e si apre proprio quella card, anche se è on-chain. Se l'ordine nuovo è uno solo, il tasto in fondo diventa «🫙 Apri l'ordine»; con più ordini resta «🫙 Apri il libro ordini».
dove: il bot, l'avviso «🔔 N nuovi ordini nel libro P2P»; lo stesso tocco sulla notifica del telefono apre il primo ordine.
leva: nessuna
pubblico: sì

## 2026-11-18 · sottocategorie-riga
frase: Le sottocategorie ora sono card disegnate come le categorie: tocchi Bitcoin e vedi subito tutti i suoi annunci, e sotto spunta una seconda riga con Hardware wallet, Cappellini, Spille e adesivi, Cover per telefono… ognuna col numero di annunci. Un tocco e filtri.
dove: Esplora → «Esplora per categorie», tocca una categoria: la seconda riga di card sotto la fila (solo le sottocategorie con annunci, che salgono a molla, ognuna con la sua icona disegnata), le altre categorie in grigio e la ✕ sulla categoria accesa. Ritoccando una sottocategoria torni a tutta la categoria; ritoccando la categoria, a Tutto.
leva: SOTTOCATEGORIE_VETRINA (accesa di serie)
pubblico: sì

## 2026-11-18 · chiavi-ovunque
frase: Uno scambio P2P preso dalla web app ora si porta avanti anche dalla Mini App in Telegram o dal browser del computer, e viceversa: appena apri il P2P, ogni dispositivo usa le chiavi delle tue 12 parole. E il tasto «Apri lo scambio» del bot, su un ordine ripreso, apre lo scambio di adesso e non quello annullato prima.
dove: P2P → «I miei scambi» e il tasto «⚡ Apri lo scambio» degli avvisi del bot.
leva: nessuna
pubblico: sì

## 2026-11-19 · scelte-negozio
frase: I prodotti dei negozi WooCommerce con una scelta che non cambia il prezzo (il gusto, il colore del nastro…) ora entrano come un annuncio solo, col titolo giusto e le sue tendine: chi compra sceglie prima di pagare, e la scelta arriva al venditore con l'ordine.
dove: la scheda di un prodotto importato da WooCommerce con tendine «Qualsiasi» (per esempio la Box Natale di Uhmami): le tendine sotto il prezzo, e di nuovo alla cassa in «🎁 Le tue scelte» (anche nel carrello). Il venditore la legge nella nota dell'ordine.
leva: nessuna
pubblico: sì

## 2026-11-19 · filtri-p2p-ricordati
frase: Il Filtro del P2P ora si ricorda: valute, metodi, premio, reputazione e Lightning/on-chain restano come li hai lasciati anche quando esci e rientri.
dove: P2P → la pillola «Filtro» sopra il libro: scegli, tocca «Applica», esci e rientra. «Azzera» lo toglie. Vale su quel telefono o browser.
leva: nessuna
pubblico: sì

## 2026-11-19 · fattura-rifatta-conto
frase: Se la fattura Lightning ti scade e la rigeneri dall'ordine, ora il foglio del pagamento ti rimostra il conto intero (articolo, spedizione, protezione e totale in sats) e, se il negozio regala la spedizione sopra una soglia, quanto ti manca per arrivarci.
dove: Ordini → un ordine «Da pagare» con la fattura scaduta → «⚡ Genera una nuova fattura»: le righe sotto il titolo del foglio, e la riga «🚚 Ti mancano … per la spedizione gratis».
leva: nessuna
pubblico: sì

## 2026-11-19 · ritorno-nel-libro
frase: Nel P2P, se chi prende il tuo ordine non paga in tempo, l'ordine non sparisce più: torna nel libro uguale, e la garanzia torna a te. E il tempo per pagare parte solo quando dici dove vuoi gli euro, non prima. Sull'on-chain l'ordine rinasce nel libro anche quando chi l'ha preso annulla, non deposita o si ritira.
dove: P2P, uno scambio col tempo per pagare: alla presa il riquadro «⏱ Hai … per pagare» coi tre passi; nella pagina dello scambio l'anello che parte da «Indica dove ricevere gli euro» e la riga rossa negli ultimi dieci minuti; il bot avvisa dieci minuti prima della fine. Sull'on-chain l'avviso «🔁 Il tuo ordine è tornato nel libro» con «🚫 Non ripubblicarlo». Sul Lightning il ritorno nel libro arriva con l'aggiornamento del nodo.
leva: nessuna
pubblico: sì

## 2026-11-19 · chiavi-dal-conto
frase: Uno scambio P2P preso dal sito si porta avanti anche dalla Mini App, e viceversa, senza fare niente: le chiavi degli scambi tornano dal tuo account, come prima del 17 novembre.
dove: P2P → «I miei scambi»: prendi un ordine dal sito, poi tocca «⚡ Apri lo scambio» nel bot. Nella Mini App i bottoni del passo ci sono, senza «Le chiavi di questo scambio non sono in questo browser».
leva: nessuna
pubblico: sì

## 2026-11-19 · chiave-moderatore-dal-conto
frase: Per i moderatori: la chiave di moderatore ora segue l'account. Il dispositivo che ce l'ha ne lascia una copia chiusa col conto, e sul PC, sul sito o su un altro telefono arriva da sola alla prima apertura delle dispute.
dove: Pannello 👑 → «⚖️ Moderazione P2P»: aprila una volta dal dispositivo che ha la chiave, poi dall'altro; compare «🔑 La tua chiave di moderatore è arrivata anche qui» e i bottoni per prendere e decidere ci sono.
leva: nessuna
pubblico: no

## 2026-11-19 · parole-casa
frase: Quando Barattolo ti chiede le 12 parole del wallet on-chain, ti dice da dove riprenderle: cloud di Telegram, browser del sito o relay Nostr.
dove: Profilo → «₿ On-chain»; nel foglio «🔑 Serve la chiave del tuo wallet» e nel riquadro «Il tuo wallet è su un altro dispositivo» la frase dice dove stanno le parole (cloud di Telegram, browser del sito, relay Nostr).
leva: nessuna
pubblico: sì

## 2026-11-19 · cassetta-telegram
frase: Il wallet on-chain nasce sia dal sito sia dalla Mini App, ed è sempre uno solo. Le 12 parole raggiungono da sole il cloud di Telegram e, se hai Nostr collegato, i relay: Barattolo le porta chiuse e non le può leggere.
dove: Nato sul sito: apri Barattolo dentro Telegram una volta, poi riapri il sito, poi di nuovo la Mini App: le parole ci sono, senza incollarle. Con Nostr collegato: entra nel sito con la tua chiave Nostr e le parole arrivano anche lì.
leva: nessuna
pubblico: sì

## 2026-11-19 · regole-sulla-card
frase: Nel P2P, quando apri un ordine col tempo per pagare, la prima cosa che leggi è quanto tempo avrai e di toccare subito «Ho inviato gli euro» dopo aver pagato, anche sugli ordini on-chain. E se prendi un ordine, il bot ti manda un messaggio col tempo che resta che si aggiorna da solo ogni minuto, senza suonare ogni volta.
dove: P2P → tocca una card col tempo per pagare: la riga «⏱ Se lo prendi hai …» in cima al foglio (on-chain: in cima a «Compra»). Dopo la presa, nel bot, il messaggio «⏳ Tempo per pagare: mancano …» con «Apri lo scambio».
leva: P2P_CONTO_ALLA_ROVESCIA (accesa di serie) per il messaggio del bot; la riga nel foglio nessuna
pubblico: sì

## 2026-11-19 · riprendi-scaduto
frase: Negli scambi P2P on-chain, se chi ha preso il tuo ordine non tocca «Ho inviato gli euro» entro il tempo per pagare, puoi riprenderti i sats con un tocco su «↩️ Riprendi i sats»: Barattolo firma il rimborso senza aspettare un moderatore, tu metti la seconda firma, e l'ordine torna nel libro.
dove: P2P → «I miei scambi» → uno scambio on-chain col deposito fatto e il tempo per pagare finito: il bottone «↩️ Riprendi i sats», poi «✍️ Metti la seconda firma».
leva: P2P_ONCHAIN_RIPRENDI_SCADUTO (accesa di serie) con P2P_ONCHAIN_RIPRENDI_SCADUTO_SOLO_ADMIN chiusa di serie, cioè solo per i moderatori: «pubblico» diventa sì quando si apre a tutti
pubblico: no

## 2026-11-19 · cauzione-tornata
frase: Negli scambi P2P on-chain con la cauzione, quando la cauzione ti torna il bot te lo dice: «La cauzione è tornata nel tuo wallet», con i sats.
dove: Il bot di Barattolo, dopo uno scambio on-chain chiuso in cui avevi bloccato la cauzione: il messaggio «🔐 La cauzione è tornata nel tuo wallet» con «Apri lo scambio».
leva: P2P_ONCHAIN_CAUZIONE spenta di serie (in produzione accesa solo per i moderatori)
pubblico: no

## 2026-11-19 · onchain-passi
frase: Negli scambi P2P on-chain i passi sono quelli di uno scambio Lightning: chi vende scrive prima dove vuole gli euro, chi compra paga e tocca «Ho inviato gli euro», e solo allora chi vende vede «Ricevuti: libera i sats». E il bot avvisa appena la rete vede il deposito, prima ancora della conferma.
dove: P2P → «I miei scambi» → uno scambio on-chain: col deposito visto «Deposito inviato» senza più «Blocca i sats»; coi sats nel deposito, a chi vende «💶 Indica dove ricevere gli euro».
leva: nessuna
pubblico: sì

## 2026-11-19 · meta-cauzione-auto
frase: Negli scambi P2P on-chain con la cauzione, se chi ha preso la perde, la metà che spetta a chi vende parte da sola verso il suo indirizzo Lightning del Profilo, senza aspettare un moderatore.
dove: Il bot di Barattolo: «🔐 Metà della cauzione di chi ha preso è tua: … in arrivo sul tuo wallet». Senza indirizzo Lightning nel Profilo il bot chiede di scriverlo, e la metà parte appena c'è.
leva: P2P_ONCHAIN_CAUZIONE_META_AUTO (accesa di serie, senza tetto: P2P_ONCHAIN_CAUZIONE_META_TETTO = 0); la cauzione stessa P2P_ONCHAIN_CAUZIONE, in produzione solo per i moderatori
pubblico: no

## 2026-11-19 · contanti-oc-cinque-minuti
frase: Negli scambi P2P on-chain in contanti di persona i passi sono quelli del Lightning: chi compra consegna i contanti e tocca «Ho consegnato i contanti», poi chi vende li conta e libera i sats. E chi deve pagare riceve dal bot un promemoria anche a cinque minuti dalla fine del tempo.
dove: P2P → «I miei scambi» → uno scambio on-chain in contanti; il bot di Barattolo, promemoria «⏰ Mancano 5 minuti: hai già mandato gli euro?».
leva: nessuna
pubblico: sì

## 2026-11-19 · bollini-home
frase: Le card «Scambi P2P» della home mostrano gli stessi bollini del libro: «⏱ 30 min» quando chi vende ha scelto un tempo per pagare sotto le 24 ore, e «🔐 Cauzione» quando chi pubblica un ordine on-chain la chiede a chi lo prende.
dove: Home (Esplora) → la fila «Scambi P2P»: i bollini sotto i metodi di pagamento.
leva: P2P_ONCHAIN_CAUZIONE per il solo «🔐 Cauzione» (in produzione solo per i moderatori); il «⏱» non ha leva
pubblico: sì

## 2026-11-19 · notifica-account
frase: Se tieni aperti più account sullo stesso telefono, toccando una notifica Barattolo apre da solo l'account a cui è arrivata, e le tendine dei prodotti importati mostrano l'apostrofo giusto.
dove: Una notifica sul telefono per un account diverso da quello aperto: il tocco passa a lui («🔁 Apro …: l'avviso è suo») e apre la pagina dell'avviso. Le tendine «Scegli…» delle box importate da WooCommerce.
leva: nessuna
pubblico: sì

## 2026-11-19 · avvisi-bz-lato
frase: Negli avvisi dei nuovi ordini P2P Barattozon è diventato un metodo di pagamento: così puoi farti avvisare solo degli ordini Barattozon in «Compra BTC», o solo di quelli in «Vendi BTC». Le scelte che avevi già fatto restano uguali.
dove: P2P → la campanella 🔔 (o Profilo → «🔔 Avvisi») → «Avvisami dei nuovi ordini P2P»: «Tipo di ordini» ha «Compra BTC» e «Vendi BTC», e «Barattozon» è la prima pillola di «Metodo di pagamento».
leva: nessuna
pubblico: sì

## 2026-11-19 · push-attive
frase: Con più account sullo stesso telefono, la voce «📲 Notifiche sul telefono» ti dice per quale account arrivano: sugli altri trovi «Attiva qui», che le sposta su quello.
dove: Profilo → «🔔 Avvisi» → «📲 Notifiche sul telefono», su un account diverso da quello che riceve le notifiche: la nota «Su questo telefono ora arrivano le notifiche di un altro tuo account…» e il tasto «Attiva qui».
leva: WEB_PUSH_ATTIVO (accesa di serie)
pubblico: sì

## 2026-11-19 · pubblica-col-tempo
frase: Negli scambi P2P Lightning, se chi vende ha scelto un tempo per pagare corto, quando qualcuno prende l'ordine ha lo stesso tempo anche lui per bloccare i sats, invece di tre ore: chi compra non resta ad aspettare.
dove: P2P → «I miei scambi» → lo scambio appena preso: «Chi ha pubblicato ha fino a 30 minuti per rispondere»; nel foglio «Pubblica», sotto «Tempo per pagare».
leva: nessuna
pubblico: no

## 2026-11-19 · onchain-tempo-deposito
frase: Negli scambi P2P on-chain chi vende con un tempo per pagare corto ha lo stesso tempo per inviare il deposito quando qualcuno prende l'ordine (basta che parta, la conferma arriva dopo), e il tempo più corto da scegliere è 30 minuti.
dove: P2P → «Pubblica» → «Vendi BTC» on-chain → «Tempo per pagare» (il cursore parte da 30 minuti, e la nota sotto lo dice); nello scambio, il foglio «🔒 Blocca i sats»: «⏱ Basta che il deposito parta entro le …».
leva: P2P_ONCHAIN_DEPOSITO_COL_TEMPO (accesa di serie)
pubblico: sì

## 2026-11-19 · recapito-nel-tempo
frase: Negli scambi P2P col tempo per pagare, anche chi vende ha quel tempo per dire dove vuole gli euro (o gli USDT): riceve i promemoria e vede quanto resta. Se non lo dice in tempo, su Lightning l'ordine torna nel libro, on-chain lo scambio si annulla e i sats tornano a lui; chi compra non deve mandare niente e non gli si conta niente.
dove: P2P → «I miei scambi» → lo scambio preso, sotto lo stato: «Hai ancora … per toccare «Indica dove ricevere gli euro»» (a chi compra: «Chi vende ha ancora …»); nel riquadro della presa, il primo passo dice anche il tempo di chi vende.
leva: P2P_RECAPITO_NEL_TEMPO (accesa di serie)
pubblico: sì

## 2026-11-20 · conto-chi-aspetta
frase: Negli scambi P2P col tempo per pagare, anche chi vende riceve su Telegram un messaggio che si aggiorna da solo ogni minuto, «⏳ Chi compra ha ancora … per pagare»: sai quanto manca senza aprire l'app.
dove: Telegram, chat del bot: quando parte il tempo per pagare di chi compra (Lightning e on-chain), il messaggio «⏳ Chi compra ha ancora … per pagare» col bottone dello scambio.
leva: P2P_CONTO_ALLA_ROVESCIA (accesa di serie)
pubblico: sì

## 2026-11-20 · sessioni-attive
frase: Nel Profilo c'è «💻 Sessioni attive»: vedi dove è aperto il tuo account (la Mini App e ogni browser in cui sei entrato) e chiudi quelle che non riconosci. Come su Telegram, da una sessione chiudi solo quelle aperte dopo; dalla Mini App le chiudi tutte.
dove: Profilo → gruppo «Impostazioni» → «💻 Sessioni attive».
leva: nessuna
pubblico: sì

## 2026-11-20 · ritorno-da-solo-oc
frase: Negli scambi P2P on-chain è come sul Lightning: se il tempo per pagare finisce e chi compra non ha toccato «Ho inviato gli euro», Barattolo firma da solo il ritorno dei sats a chi vende, che mette la seconda firma, e l'ordine torna nel libro. Non vale col tabacchino e col contanti di persona.
dove: P2P → «I miei scambi» → lo scambio on-chain a tempo finito: «⏰ Il tempo per pagare è finito…» e il tasto «✍️ Metti la seconda firma»; prima di prendere, il riquadro «⏱ Hai … per pagare» dice «lo scambio scade e i sats tornano a chi vende, anche se hai pagato».
leva: P2P_ONCHAIN_RITORNO_DA_SOLO (accesa di serie)
pubblico: sì

## 2026-11-20 · cassa-presenza
frase: In Barattolo Negozio la cassa al banco ha due cose nuove. Sul QR c'è «🔁 Gira verso il cliente»: il telefono mostra a chi paga solo la cifra, i pezzi e un QR grande, e quando paga compare «✅ Pagato, grazie!». E nella scheda «Vendite» c'è la chiusura di cassa di oggi o di ieri: vendite, sats, Lightning e on-chain, i pezzi usciti, e il riepilogo da copiare.
dove: Profilo → «🏪 Cassa in negozio» → «Incassa» → «🔁 Gira verso il cliente»; e la scheda «📒 Vendite» → «📒 Chiusura di cassa».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

## 2026-11-20 · dettaglio-schede
frase: La pagina di uno scambio P2P è più ordinata: in alto tre schede, «📋 Passi», «💰 Importi» e «💬 Chat». Entrando vedi subito i passi, lo stato e il bottone da toccare; il conto e la chat sono a un tocco, con un pallino rosso quando ti hanno scritto.
dove: P2P → «I miei scambi» → uno scambio (Lightning o on-chain): le schede sotto il titolo «Nel dettaglio», ferme in alto anche scorrendo.
leva: nessuna
pubblico: sì

## 2026-11-20 · pubblica-passi
frase: Pubblicare un ordine P2P adesso va a passi, una pagina alla volta: «1. Cosa», «2. Quanto», «3. Regole» e «4. Rileggi», col riepilogo prima di pubblicare. Si va con «Avanti →» e si torna con «← Indietro» o toccando un passo già fatto. La scelta fra ⚡ Lightning e ₿ On-chain resta in cima a ogni passo, e le scelte sono le stesse di prima.
dove: P2P → il + → «Pubblica» (Vendi BTC o Compra BTC). Con Barattozon il foglio resta quello di sempre, coi suoi passi.
leva: nessuna
pubblico: sì

## 2026-11-20 · cassa-vetrina
frase: Barattolo Negozio adesso si apre sulla pagina del tuo negozio, uguale a quella che vede chi compra. Tocchi le card per mettere i pezzi nel conto, in fondo c'è la barra del carrello, e «Controlla e incassa» porta al conto e al QR: i sats vanno dritti al tuo wallet, senza deposito di garanzia.
dove: Profilo → «🏪 Cassa in negozio»: la vetrina del tuo negozio, la barra in fondo «Controlla e incassa», e in alto «📒 Vendite».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

## 2026-11-20 · abbonamento-canale
frase: Su Barattolo si può comprare un mese di accesso al canale Telegram privato di un negozio. Paghi in sats, apri l'ordine e con «🔓 Rivela» trovi il tuo link d'invito personale: lo tocchi e il bot ti fa entrare. Per restare rinnovi ricomprando lo stesso annuncio, e Barattolo ti avvisa prima della scadenza.
dove: nella scheda dell'annuncio, la nota «🔑 Abbonamento di 30 giorni a…»; dopo il pagamento, l'ordine → «🔓 Rivela».
leva: ABBONAMENTI_CANALE (accesa di serie; attiva solo coi canali collegati in CANALI_ABBONAMENTO)
pubblico: sì

## 2026-11-20 · app-negozio-sola
frase: Barattolo Negozio diventa un'app Android tutta sua, con la sua icona (due barattoli sul bancone di un mercato) e il suo nome. Si apre sulla cassa del tuo negozio, l'indietro la chiude invece di portarti al mercatino, e se non sei ancora entrato ti fa entrare col tuo account di Barattolo, con Telegram o con Nostr.
dove: Zapstore → «Barattolo Negozio» (accanto a Barattolo, stesso firmatario).
leva: CASSA_ATTIVA (accesa di serie)
pubblico: no

## 2026-11-20 · ripubblica-semplice
frase: La ripubblica degli ordini P2P è più semplice: pubblicando ti chiediamo solo «Vuoi ripubblicarlo?». Con Sì, se nessuno prende l'ordine nei suoi 7 giorni, alla scadenza torna nel libro uguale, da solo, ogni volta. Se hai messo il paracadute, si ripubblica solo finché BTC resta dentro le soglie del giorno in cui l'hai pubblicato.
dove: P2P → il + → «Pubblica» → «3. Regole» → «🔁 Ripubblica».
leva: P2P_RIPUBBLICA (accesa di serie)
pubblico: sì


## 2026-11-21 · filtri-negozio
frase: Se hai collegato il tuo negozio WooCommerce o Shopify, adesso scegli tu cosa entra su Barattolo: tutto tranne alcune categorie o tag, solo quelli che vuoi, o prodotto per prodotto. Il negozio resta sincronizzato ogni ora, e quello che togli non si cancella: va in panchina e lo riaccogli quando vuoi, con lo stesso annuncio.
dove: Profilo → «📥 Carica tanti annunci insieme / catalogo esterno» → il tuo negozio → «🧺 Cosa entra».
leva: CONNETTORI_NEGOZIO_APERTI (il cassetto dei negozi collegati)
pubblico: sì

## 2026-11-22 · carica-prodotti-menu
frase: «Carica prodotti» è più semplice: scegli prima da dove arrivano i tuoi prodotti, da un file CSV, da Shopify o da WooCommerce, e si apre solo quello che ti serve, con «‹ Indietro» per cambiare. E sugli annunci che arrivano dal tuo negozio collegato il bottone dice «Rimuovi da qui»: spariscono da Barattolo, non dal tuo e-commerce.
dove: Profilo → «📥 Carica prodotti».
leva: CONNETTORI_NEGOZIO_APERTI (il cassetto dei negozi collegati)
pubblico: sì


## 2026-11-22 · onchain-prodotti-costosi
frase: Sopra 500 € gli acquisti del mercatino si pagano solo on-chain, e chi vende riceve on-chain: con cifre così il Lightning non passa. Chi pubblica un oggetto sopra 500 € lo vede già in «Come vuoi ricevere», e l'annuncio dice «Preferisce ricevere on-chain». E il mercatino on-chain non ha più un tetto: anche un oggetto da 2 BTC si compra col deposito di garanzia 2-di-3.
dove: Mercatino: un oggetto sopra 500 €, «Acquista», foglio «Come vuoi pagare?» (Lightning spento con «Sopra 500 € si paga solo on-chain.»); Vendi, «Come vuoi ricevere per questo oggetto?» con «Sopra 500 € si riceve solo on-chain.».
leva: ONCHAIN_SOLO_SOPRA_SOGLIA accesa di serie (soglia ONCHAIN_CONSIGLIATO_SOPRA_EURO, 500)
pubblico: sì
