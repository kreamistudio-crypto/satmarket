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
leva: nessuna
pubblico: sì

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
frase: Nel Profilo c'è «🧭 La tua stradina»: un tabellone lunghissimo dalla Terra alla Luna, su una mappa in otto zone, che vedi solo tu, fino all'halving del 2028. Ogni casella è una competenza (l'incasso automatico in Lightning, il wallet on-chain, la doppia configurazione Telegram + Nostr, il primo acquisto…): fatta, diventa una moneta d'oro e Tappo avanza. I tuoi amici sono pedine sul tabellone.
dove: Profilo → «🎖 Livello e titolo» → «🧭 La tua stradina».
leva: nessuna
pubblico: sì

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

## 2026-11-17 · profilo-semplice
frase: Il Profilo è più semplice da leggere: ogni casella dice cosa c'è dentro. Ci sono «Annunci», «Il tuo negozio», «Spedizioni e sconti», «Quando compri», «Wallet e incassi», «Livello e recensioni», «Impostazioni» e «Aiuto».
dove: scheda Profilo, le caselle sotto il riquadro col tuo nome.
leva: nessuna
pubblico: sì

## 2026-11-17 · raccolta
frase: Su Barattolo si può aprire una raccolta fondi in sats: un obiettivo, una scadenza fino a 60 giorni e una barra che si riempie. Chi vuole sostenerla manda uno zap, che va dritto al wallet di chi raccoglie, senza commissioni. Per aprirne una servono tre vendite concluse e un indirizzo Lightning; ogni raccolta la guardano i moderatori prima della vetrina.
dove: Profilo → «Il tuo negozio» → «🎯 Raccolte fondi» (lì il bottone «🎯 Apri una raccolta»); in vetrina la tessera «Raccolte» accanto ad Aste, quando c'è almeno una raccolta; nella scheda di una raccolta il bottone «⚡ Sostieni con uno zap».
leva: RACCOLTE_ATTIVE (accesa di serie; i depositi di garanzia, RACCOLTA_GARANTITA_ATTIVA, spenti di serie)
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
