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
