# La base di conoscenza di Tappo

<!-- FILE GENERATO da assistente/conoscenza.py: non si tocca a mano.
Si rifà con `python assistente/conoscenza.py` dopo ogni ritocco al
libro (assistente/sapere.md), alla Mini App (miniapp.html) o a
NOVITA.md; prove_conoscenza_tappo è rossa finché non è aggiornato. -->

<!-- pezzo libro-001 | libro | sempre -->
## Libro · Cos'è Barattolo (1/2)

Barattolo è un mercatino fra persone, come un Subito.it, dove si paga solo in bitcoin: in satoshi («sats», la centesima milionesima parte di un bitcoin) sulla rete Lightning, che è veloce e costa quasi niente anche per pochi euro. Il prezzo si può leggere anche in euro con l'interruttore € / ₿, ma quello che viaggia sono sempre sats.

Barattolo ha due anime:
- il mercatino: si comprano e si vendono oggetti, servizi definiti e codici digitali, coi sats fermi in un deposito di garanzia finché chi compra non conferma di aver ricevuto;
- lo scambio P2P: si comprano e si vendono bitcoin con altre persone, per euro, coi sats bloccati in garanzia finché gli euro non sono arrivati.

Dove si trova:
- dentro Telegram, come Mini App: si apre dal bot @ilbarattolobot col bottone «🫙 Apri Barattolo»;
- sul sito barattolo.store, da qualunque browser;
- come app per Android, da Zapstore o dalle release su GitHub (con Obtainium si aggiorna da sola). L'app è una finestra su barattolo.store: dentro non c'è niente di diverso. Per controllare che sia proprio quella ufficiale c'è AppVerifier: le due righe da incollare sono nella pagina «Il pagamento protetto» (barattolo.store/sicurezza);
- su Nostr: gli annunci vengono pubblicati anche lì, e si leggono con qualunque app Nostr che mostra gli annunci (NIP-99).

Barattolo in inglese (dal 17 novembre 2026): se il Telegram o il browser di chi apre Barattolo non è in italiano, tutta l'app compare in inglese da sola — vetrina, schede, acquisto, Ordini, scambio P2P, Vendi, Profilo, aste, raccolte, avvisi e assistenza — coi prezzi scritti all'inglese («1,234.50 €»). Restano in italiano, per ora, i messaggi del bot di Telegram e gli avvisi di errore del server; l'interruttore della lingua nel Profilo arriva in una tappa successiva. Per vedere l'inglese da un telefono italiano si apre barattolo.store/?lingua=en, e ?lingua=it riporta all'italiano; la scelta resta su quel dispositivo. Se qualcuno scrive a Tappo in inglese, Tappo risponde in inglese.

Le chiavi degli scambi P2P (dal 19 novembre 2026, di nuovo come prima del 17): le ricava il tuo account, uguali ovunque entri con lui — Mini App, sito, app, Telegram Desktop. Uno scambio preso dal sito si porta avanti dalla Mini App e viceversa, senza incollare niente. Le 12 parole del wallet on-chain servono SOLO all'on-chain. Dal 17 al 19 novembre le chiavi nascevano dalle 12 parole: chi ha preso uno scambio in quei giorni lo finisce dal dispositivo dove l'ha preso (resta lì «in pensione» solo per finirlo). Chi entra con Nostr ritrova il profilo entrando con la stessa chiave Nostr. Se lo scambio dice «Le chiavi di questo scambio non sono in questo browser», è di un altro profilo: si finisce da dove è stato preso, o si scrive a @ilbarattolobot se quella memoria è persa.

<!-- pezzo libro-002 | libro | sempre -->
## Libro · Cos'è Barattolo (2/2)

Il bot di Telegram serve a tre cose: aprire Barattolo, mandarti gli avvisi sui tuoi ordini e scambi, e sfogliare le categorie anche senza aprire la Mini App (scrivi /sfoglia). Gli acquisti, le vendite e le trattative si fanno nella Mini App o sul sito.

<!-- pezzo libro-003 | libro -->
## Libro · Entrare e il profilo (1/4)

Non servono email, password o numero di telefono. Si entra in due modi:
- con Telegram: dentro la Mini App sei già riconosciuto; sul sito c'è «Entra con Telegram»;
- con una chiave Nostr: «Entra con Nostr», con un'estensione del browser, un bunker (nostrconnect) o un'app che firma. La chiave privata (nsec) non arriva mai ai server di Barattolo: quando serve una firma la fa il tuo browser o il tuo bunker.
- dal sito sul telefono non serve più copiare e incollare la stringa: tocchi «📱 Entra con nostrconnect» e il firmatario si apre da solo, Amber su Android e Clave su iPhone; approvi e torni su Barattolo. Se non si apre, c'è il bottone «📲 Apri Amber e approva» (o «Apri Clave e approva»); il codice QR e «Copia il link» restano per chi firma da un altro telefono. Su iPhone il bunker:// di Clave resta la strada più solida.

Entrare sul sito passando dal bot (se nelle REGOLAZIONI del pannello «Entra dal bot» è accesa): sul sito «Entra con Telegram» apre il bot @ilbarattolobot con un link fatto apposta (sul sito .onion il link arriva come QR, da inquadrare col telefono). Tocchi «Avvia» e il bot chiede «🔑 Entri su Barattolo come …?», mostrando tre figure del mercatino (per esempio 🍯 Miele, 🚲 Bici, 📚 Libri). Tocchi quella che la pagina ti mostra e sei dentro, con l'account che hai aperto in quel momento nell'app di Telegram: chi ha due account sceglie così quale usare. Il link vale due minuti e una volta sola. Se non sei stato tu a chiederlo, tocca «❌ Non sono stato io»: anche una figura sbagliata chiude il tentativo. ATTENZIONE ALLA TRUFFA: la figura giusta la vede solo chi ha chiesto di entrare, sulla sua pagina. Se qualcuno ti manda un link del bot e ti dice o ti scrive quale figura toccare, vuole entrare nel tuo account: non toccare la figura, tocca «❌ Non sono stato io». Barattolo e lo staff non ti chiedono mai di toccare una figura.

Un account nato con Telegram può collegare anche una chiave Nostr dal Profilo, e viceversa.

<!-- pezzo libro-004 | libro -->
## Libro · Entrare e il profilo (2/4)

Nome e foto: di serie vengono dal tuo profilo Telegram o Nostr. La foto la scegli tu: Profilo → «🆔 Nostr e identità» → «📷 La tua foto», con «✈️ Telegram», «Nostr» (ognuna compare solo se hai quel profilo) o «Nessuna», che al posto della foto mostra la tua iniziale; si torna indietro quando vuoi. Chi ha sia Telegram sia Nostr e sceglie Nostr prende da lì anche il nome. Puoi anche mettere un nome e una foto tuoi, solo per Barattolo, gratis (se nelle REGOLAZIONI del pannello «Nome e foto scelti su Barattolo» è accesa): nello stesso cassetto, alla riga «✏️ Nome e foto su Barattolo», tocca «✏️ Scegli nome e foto», scrivi il nome e/o carica la foto e tocca «✏️ Manda al moderatore». Puoi cambiare anche solo uno dei due: l'altro resta com'è. Un moderatore li guarda prima che si vedano; intanto resta il nome di prima. Approvati, valgono su tutto Barattolo (annunci, negozio, Ordini, P2P, recensioni) e compare la scelta «✏️ Mia»; il tuo profilo Telegram o Nostr, la npub e l'accesso con Nostr non cambiano. Se non li approva, ti arriva il motivo e puoi riprovare subito. Dopo un'approvazione il cambio successivo si può fare dopo 30 giorni. Il nome: da 3 a 30 caratteri, lettere, numeri, spazi e . - ' _ , niente emoji, niente parole come «barattolo», «admin», «staff», «supporto», e non uguale a quello dello staff, dei negozi Consigliati o di chi ha già venduto almeno 10 volte. Puoi tornare a «✈️ Telegram» o «Nostr» quando vuoi, e rientrare su «✏️ Mia» senza un nuovo controllo. Chi ha un ordine in corso con te riceve un avviso col tuo nome nuovo.

Nel Profilo si impostano le cose che servono a vendere e a scambiare: soprattutto l'indirizzo Lightning per incassare (voce «Lightning address»), il wallet collegato con NWC (facoltativo) e gli avvisi. Chi usa anche i bitcoin on-chain trova altre due voci: «📥 Come ricevi» e «₿ On-chain» (vedi «Bitcoin on-chain»).

<!-- pezzo libro-005 | libro -->
## Libro · Entrare e il profilo (3/4)

La serie dei giorni (se nelle REGOLAZIONI del pannello «Serie dei giorni» è accesa): nel Profilo, sotto le stelle, c'è una fiamma con scritto quanti giorni di fila hai aperto Barattolo e il tuo record, per esempio «5 giorni di fila · record 12»; subito sotto ci sono gli ultimi sette giorni, accesi quelli della serie. Conta aprire Barattolo da dentro il tuo account, almeno una volta al giorno, da Telegram, dal sito o dall'app: contano i giorni, non quante volte. Il giorno è quello italiano, da mezzanotte a mezzanotte. Se salti un giorno la serie riparte da 1 e il record resta. È solo un contatore: non dà XP, livelli, sconti né premi, e sul tuo negozio e sul profilo che vedono gli altri non compare. Sotto i sette giorni c'è il bottone «Classifica Streak» con la fiamma (fino al 17 nov sera si chiamava «Classifica dei giorni di fila»): mostra chi ha la fila più lunga ancora accesa (nome, foto e giorni), la vede solo chi è entrato in Barattolo, ci si entra dal secondo giorno di fila e a pari giorni la posizione è la stessa (per questo all'inizio, quando tutti hanno gli stessi giorni, sono tutti 1°; le posizioni si separano quando le serie diventano diverse); accanto a ognuno c'è sempre il numero della posizione, e la medaglia 🥇🥈🥉 solo ai primi tre posti se quel posto è diviso al più da tre persone; escono le prime 50 righe, e chi sta più giù vede la sua posizione a parte. Chi non vuole comparire accende «🏆 Non mostrarmi in classifica» nel Profilo (dove c'è il livello): esce da questa classifica e da quella del mercatino, e la sua serie continua a vederla lui. Al primo accesso del giorno, dal secondo giorno di fila, compare per un attimo un saluto con il numero. La prima volta del giorno che apri il Profilo, il cerchio di oggi si accende piano come una brace e il numero dei giorni sale da ieri a oggi (per esempio da 4 a 5): succede una volta al giorno, ed è solo un'animazione. Il bot non manda promemoria per non farla scadere.

<!-- pezzo libro-006 | libro -->
## Libro · Entrare e il profilo (4/4)

Le notifiche sul telefono (se nelle REGOLAZIONI del pannello «Notifiche sul telefono» è accesa): nell'app di Barattolo per Android (quella di Zapstore), nel sito aggiunto alla schermata Home e nel browser del computer, gli avvisi degli ordini, degli scambi P2P e dei messaggi possono arrivare come notifica normale, tipo WhatsApp, anche con l'app chiusa. Si accendono dal Profilo → «🔔 Avvisi» → «📲 Notifiche sul telefono» → «Attiva», e il telefono chiede il permesso: va detto sì. Poi «🔔 Mandami una notifica di prova» fa vedere subito se arrivano. Vale per quel telefono (su un altro si accende di nuovo), e arrivano in più rispetto a Telegram o ai messaggi Nostr, che restano come sono. Si spengono dallo stesso tasto; uscendo dall'account smettono di arrivare su quel telefono. Dentro Telegram il tasto non c'è, perché gli avvisi arrivano già dal bot. NON arrivano: sui telefoni senza i servizi Google (per esempio GrapheneOS), con Tor Browser o sul sito .onion; sull'iPhone solo se Barattolo è aggiunto alla schermata Home (Condividi → «Aggiungi alla schermata Home», da iOS 16.4) e aperto da lì. Se le hai bloccate per sbaglio, si riaprono dalle impostazioni del telefono, alla voce Notifiche. Toccando una notifica si apre la pagina di cui parla: l'ordine, lo scambio o l'annuncio (dal 16 nov 2026 anche gli avvisi degli annunci aprono l'annuncio e non la home); lo stesso vale per i link degli avvisi del bot. Chi ha più account aperti sullo stesso telefono (per esempio due negozi): il tocco sulla notifica apre da solo l'account a cui l'avviso è arrivato. Attenzione: su un telefono le notifiche arrivano a un account alla volta, l'ultimo su cui le hai attivate; sugli altri account aperti lì la voce «📲 Notifiche sul telefono» lo dice («arrivano le notifiche di un altro tuo account») e il tasto «Attiva qui» le sposta su quello. Un avviso già visto si rilegge nella chat del bot di Barattolo (per gli account Telegram) o nel Profilo → «🔔 Avvisi» → «📬 I tuoi avvisi» (per gli account entrati con Nostr).

<!-- pezzo libro-007 | libro -->
## Libro · Il wallet Lightning (1/2)

Per pagare e per incassare serve un wallet Lightning tuo. Ne esistono tanti, gratuiti, e ne basta uno. Barattolo non ha un wallet suo e non tiene i tuoi sats, tranne il tempo di un affare (vedi il deposito di garanzia).

- Per pagare: Barattolo ti mostra una fattura Lightning (invoice). La apri nel wallet, la copi e incolli, o ne inquadri il QR.
- NWC (Nostr Wallet Connect): se colleghi il wallet dal Profilo, «⚡ Compra subito» paga in un tocco, e nel P2P la fattura per ricevere la fa il wallet da solo. La connessione resta solo sul tuo dispositivo, non arriva ai nostri server, e nel wallet le puoi dare un tetto di spesa.
- Per incassare: l'indirizzo Lightning (quello con la @, tipo nome@dominio) si imposta una volta nel Profilo e non scade. Se non ce l'hai, quando l'affare si chiude ti avvisiamo e incolli una fattura nell'ordine in quel momento (prima no: una fattura scade).
- Nel P2P l'indirizzo di Wallet of Satoshi non passa la verifica: lì si incolla una fattura del wallet, che invece funziona. Lo stesso vale per qualunque indirizzo che il servizio di scambio non riesce a verificare.
- Nel P2P, chi compra sats deve dire a ogni scambio dove riceverli: lo chiede il servizio di scambio (Mostro) appena l'ordine è preso, prima che chi vende blocchi i sats in garanzia, e non ricorda niente fra uno scambio e l'altro. Dal 24 novembre 2026 chi ha salvato un indirizzo Lightning negli incassi del Profilo non deve più farlo a mano: l'app lo controlla e lo manda da sola appena l'ordine è preso, e dice «⚡ Ricevi su …»; lo scambio parte subito. Il foglio «Dove ricevere i sats» si apre solo se l'indirizzo non passa (per esempio Wallet of Satoshi, dove si incolla una fattura), se il servizio di scambio lo rifiuta, o se è collegato un wallet NWC (che la fattura la fa da solo). Chi vuole ricevere quei sats on-chain con lo swap tocca «₿ Ricevi on-chain» nel foglio dell'ordine, prima di «Compra» (diventa «✓ Ricevi on-chain»): alla presa il foglio si apre già su «₿ On-chain». Non è una sicurezza per tirarsi indietro: se il foglio resta lì e scade (30 minuti) conta come scambio non completato; per ritirarsi prima che i sats siano in garanzia c'è «✕ Annulla» nella pagina dello scambio, che non conta.

<!-- pezzo libro-008 | libro -->
## Libro · Il wallet Lightning (2/2)

- Chi non ha ancora un wallet trova la guida «👛 Il tuo primo wallet»: si apre dalla casella verde «👛 Il tuo primo wallet» nel Profilo, subito sotto la fila dei giorni di fila (c'è solo finché non hai un Lightning address), e dal bottone «👛 Non hai un wallet? Ti spieghiamo come fare» che sta sotto la fattura da pagare, nel riquadro dell'incasso o del rimborso di un ordine e nel Profilo accanto al Lightning address. Sono tre passi: 1) scarica Wallet of Satoshi (gratis, in Europa i sats restano sul telefono di chi lo usa); 2) salva le parole di recupero su carta; 3) dipende da cosa stavi facendo: se devi pagare, metti qualche sats (te li manda un amico o li compri in euro nel P2P) e inquadri il QR dal wallet; se devi incassare, tocchi «Ricevi» nel wallet, copi il tuo indirizzo nome@walletofsatoshi.com e lo incolli nel campo della guida. La prima volta che salvi il tuo Lightning address (dalla guida o dal Profilo) ricevi il distintivo «📥 Pronto a incassare»: non dà punti (i punti si fanno solo con gli affari), è un distintivo. Nella tendina «Hai già un altro wallet?»: va bene qualsiasi wallet che dia un indirizzo con la @ (per esempio Blink, nome@blink.sv, o Coinos, nome@coinos.io), non per forza Wallet of Satoshi; Muun invece non ha un indirizzo con la @, quindi con Muun a ogni vendita si incolla una fattura e la mancia non si può ricevere finché non si aggiunge un indirizzo di un altro wallet; quello di Phoenix Barattolo non lo sa ancora pagare, quindi con Phoenix a ogni vendita si incolla una fattura. Barattolo non ha un wallet suo e non tiene i sats di nessuno: se qualcuno chiede un «conto su Barattolo», la risposta è questa guida.

<!-- pezzo libro-009 | libro -->
## Libro · Comprare nel mercatino (1/4)

1. Trovi l'annuncio: dalla vetrina (Esplora), dalla ricerca, dalle categorie. Toccando una categoria in «Esplora per categorie» vedi subito tutti i suoi annunci, e sotto la fila compare una seconda riga di card con le sue sottocategorie (per esempio Bitcoin → Hardware wallet e firma, Cappellini, Spille e adesivi…), ognuna col numero di annunci; le altre categorie in alto diventano grigie. Tocchi la sottocategoria che ti interessa; ritoccandola torni a tutta la categoria. Compaiono solo le sottocategorie che hanno annunci. Per uscire: ritocca la categoria accesa (ha una piccola ✕), o la card «Tutto». Puoi salvare i preferiti e farti avvisare quando arriva quello che cerchi.
2. Scegli come riceverlo, fra quelli che il venditore offre: spedizione a un indirizzo, spedizione a un punto di ritiro o a un locker, ritiro a mano in zona, oppure consegna dentro Barattolo se è un codice o un buono digitale. Se il venditore non spedisce ai locker, la riga del locker è spenta e c'è il tasto «Chiedi al venditore se spedisce con InPost o Poste»: lui riceve un avviso (senza sapere chi ha chiesto) e, se aggiunge InPost, Poste Italiane o SDA nel Profilo, Barattolo ti avvisa. Una richiesta per venditore ogni 7 giorni.
3. Paghi con «🔒 Compra in sicurezza»: arriva una fattura Lightning da pagare col wallet. La fattura dura pochi minuti (vedi i NUMERI DI OGGI): se scade non è successo niente, se ne fa un'altra al cambio del momento. Se la rigeneri dall'ordine («⚡ Genera una nuova fattura», stesso importo), il foglio ti rimostra il conto: articolo, spedizione, protezione e totale in sats, e quanto ti manca per la spedizione gratis del negozio.
4. I sats entrano nel deposito di garanzia. Il venditore viene avvisato, sa di essere pagato, ma i sats non sono ancora suoi.
5. Il venditore spedisce e segna il corriere col tracciamento, oppure vi accordate per il ritiro, oppure ti consegna il codice dentro l'ordine.
6. Quando l'oggetto è arrivato ed è come promesso, lo confermi dall'ordine, nella scheda «Ordini». Solo in quel momento i sats passano al venditore.

<!-- pezzo libro-010 | libro -->
## Libro · Comprare nel mercatino (2/4)

Gli avvisi del barattolo (se nelle REGOLAZIONI del pannello «Avvisi del barattolo» è accesa): quando metti un articolo nel barattolo 🫙 si apre il foglietto «🔔 Avvisami se…» con quattro spunte, tutte accese di serie: «📉 Il prezzo scende», «⚡ Arriva uno sconto lampo», «☝️ Ne resta solo uno» (l'articolo aveva più pezzi e ne è rimasto uno), «🔁 È di nuovo disponibile» (era esaurito e torna, o il negozio rientra dalle ferie). Togli quelle che non vuoi e tocca «Va bene», oppure chiudi il foglietto e restano tutte. Gli avvisi arrivano dal bot, con il tasto «🫙 Apri l'annuncio», al massimo uno al giorno per articolo: se nello stesso giorno succedono più cose arrivano in un messaggio solo, e quello che cade dentro il giorno arriva il giorno dopo se è ancora vero. Se il prezzo sale non arriva niente. Il prezzo si guarda nella valuta dell'annuncio: un annuncio in euro non «scende» perché cambia il valore del bitcoin, e un ritocco sotto l'1% non conta. Le spunte si cambiano quando vuoi dalla 🔔 accanto a ogni articolo, nel Profilo, sezione «Nel tuo barattolo» (🔕 vuol dire nessun avviso). Gli articoli messi nel barattolo prima del 17 novembre 2026 ricevono solo lo sconto lampo, come prima, finché non tocchi la loro 🔔.

Si può anche fare un'offerta più bassa con «Fai un'offerta»: il venditore la accetta o la rifiuta, e se la accetta hai un tempo per pagare, scritto nell'ordine. Un'offerta senza risposta scade da sola.

La mancia al venditore (se nelle REGOLAZIONI del pannello «Mancia al venditore» è accesa): un'offerta può essere solo più bassa del prezzo, ma chi vuole dare di più al venditore può lasciargli una mancia. Nell'ordine già pagato, nella scheda «Ordini», c'è «🎁 Lascia una mancia»: si sceglie la cifra (500, 1.000, 2.100 sats o un'altra) e si paga col proprio wallet. Nello stesso foglio, se vuoi, puoi aggiungere anche uno zap a Barattolo (di serie è «Niente»): sono due fatture, una dopo l'altra. La mancia va DRITTA al Lightning address del venditore: Barattolo non la tocca e non prende commissioni. Per questo è un regalo fuori dal deposito di garanzia e NON si rimborsa, anche se poi l'ordine va male: chi ha dubbi la lascia dopo aver ricevuto l'oggetto. Il bottone c'è solo su un ordine pagato (non su uno annullato, in disputa o rimborsato) e solo se il venditore ha impostato il suo Lightning address nel Profilo. Se non l'ha impostato, il riquadro c'è lo stesso ma senza bottone, con la frase «non ha ancora un indirizzo Lightning nel profilo: per ora la mancia non si può mandare»: è normale, la mancia non avrebbe dove andare (anche se il venditore ha incassato l'ordine, per esempio con una fattura incollata a mano). Al venditore senza indirizzo, nello stesso ordine, compare l'invito «Aggiungilo dal Profilo»: appena lo salva, il bottone compare anche a chi ha comprato. Il venditore riceve un avviso e vede la mancia nell'ordine: «arrivata» se Barattolo ha potuto verificarla, altrimenti «controlla il wallet».

<!-- pezzo libro-011 | libro -->
## Libro · Comprare nel mercatino (3/4)

Le raccolte fondi in sats (se nelle REGOLAZIONI del pannello «Raccolte in sats» sono accese): chi ha almeno 3 vendite concluse su Barattolo e un indirizzo Lightning nel Profilo può aprire una raccolta da Profilo → «Il tuo negozio» → «🎯 Raccolte fondi» → «🎯 Apri una raccolta»: titolo, racconto, obiettivo in euro (da 10 a 1.000 € in questa prima fase, fissato in sats al cambio del giorno) e durata (da 7 a 60 giorni). Una alla volta. Prima di andare in vetrina la guardano i moderatori: una raccolta è un sostegno, quindi NON può promettere quote, interessi, rendimenti, guadagni o token; l'eventuale ricompensa è un grazie, non un acquisto. Chi la sostiene ha due strade. «⚡ Sostieni con uno zap»: lo zap va DRITTO al wallet di chi raccoglie, Barattolo non lo tocca e non prende commissioni, e per questo NON si rimborsa, nemmeno se l'obiettivo non arriva. «🛡️ Sostieni con garanzia» (c'è solo se chi raccoglie l'ha scelta e se la funzione è accesa): da 50 € in su, si paga on-chain in un deposito di garanzia 2-di-3 (chi sostiene, chi raccoglie, Barattolo) e il deposito va pagato entro 24 ore; a scadenza, se i DEPOSITI hanno raggiunto l'obiettivo (gli zap non contano per questo), i sats vanno a chi raccoglie, altrimenti tornano al wallet di chi li ha messi. In tutti e due i casi Barattolo mette la sua firma e la seconda la mette il telefono di chi riceve, da solo all'apertura dell'app o col bottone «✍️ Firma» nella scheda della raccolta. Un deposito arrivato tardi o incompleto torna indietro. La rete on-chain la paga chi deposita, pochi sats. Se i moderatori fermano una raccolta, i depositi tornano a chi li aveva messi (gli zap no). Chi vede una raccolta sospetta la può segnalare dal fondo della sua scheda («🚩 Segnala questa raccolta»). Le raccolte non danno XP.

Tutti i tuoi acquisti e le tue vendite stanno nella scheda «Ordini», con lo stato di ogni ordine e i bottoni per il passo successivo. In fondo all'elenco c'è «📄 Esporta tutti gli ordini in CSV», che scarica un file con tutti i dettagli dei tuoi ordini (utile a chi vende per tenere i conti).

<!-- pezzo libro-012 | libro -->
## Libro · Comprare nel mercatino (4/4)

Il feedback: ad affare concluso, dalla pagina dell'ordine, compratore e venditore si lasciano a vicenda un voto da 1 a 5 stelle con un commento breve (chi compra può aggiungere fino a 3 foto). Lo stesso vale per la recensione a fine scambio P2P, che va nella stessa media del profilo. Chi l'ha lasciato può modificarlo una volta sola (stelle e commento; le foto restano) oppure cancellarlo, entro 7 giorni da quando l'ha scritto: sotto il voto ci sono «✏️ Modifica» e «🗑 Cancella», con la data fino a cui valgono. Dopo diventa definitivo. Chi ha ricevuto il feedback viene avvisato del cambio, e sul profilo la riga porta la scritta «modificato». Cancellato è per sempre: su quell'affare non se ne può lasciare un altro. Il feedback lasciato da un altro non si può cambiare: se è offensivo o falso, lo può togliere solo un moderatore (scrivi allo staff). Nessuno può chiederti di cambiare un voto in cambio di qualcosa: se succede, segnalalo allo staff. Le recensioni che hai ricevuto le trovi tutte in un posto: Profilo → «Livello e recensioni» → «⭐ Recensioni ricevute» (oppure tocca le stelle sotto il tuo nome in cima al Profilo). Ci sono le ultime 50, del mercatino e degli scambi P2P insieme, come le vedono gli altri nel tuo negozio.
Nascondere le recensioni dal profilo pubblico (dal 22 novembre 2026, se nelle REGOLAZIONI del pannello «Recensioni nascondibili dal profilo pubblico» è accesa): in fondo al cassetto «⭐ Recensioni ricevute» (Profilo → «Livello e recensioni») ci sono due interruttori, «Mostra sul profilo pubblico le recensioni del mercatino» e «Mostra sul profilo pubblico le recensioni degli scambi P2P». Di serie sono tutti e due su «Attivo», cioè si vede tutto come prima; toccandolo diventa «Spento». Spento, quelle recensioni non si vedono più nel tuo profilo pubblico e nel tuo negozio, né nel riquadro «Chi ha pubblicato» del P2P. Con le recensioni P2P spente spariscono anche «✅ N scambi P2P» e «⚡ Risponde in fretta», sia dal profilo sia dalle card del P2P: serve a chi non vuole far sapere che usa il P2P, cioè che ha bitcoin. Restano SEMPRE: le stelle e il numero di recensioni (contano anche quelle nascoste, così nessuno alza la media nascondendo i voti brutti); le recensioni negative, da 1 e 2 stelle, che non si possono nascondere mai, nemmeno con l'interruttore spento; gli avvisi di scambi non completati e di dispute perse. Quelle nascoste le vedi sempre solo tu, nel tuo cassetto: nemmeno i moderatori le vedono sul profilo. Si può nascondere tutto il mercatino, tutto il P2P o tutte e due, e riaccendere quando vuoi; non si sceglie una recensione per volta.

Per un contenuto digitale il venditore può chiederti qualche informazione prima di pagare (per esempio nome, cognome o email, una scelta da un elenco, un sì o un no): rispondi alla cassa. Le risposte viaggiano cifrate dentro l'ordine, le leggete solo tu e il venditore, e si cancellano come l'indirizzo. Il numero di telefono non si può chiedere.

<!-- pezzo libro-013 | libro -->
## Libro · Il deposito di garanzia

Quando compri, i sats non vanno subito al venditore: si fermano in un deposito di garanzia (in gergo escrow) che custodisce Barattolo, su un nodo Lightning suo. Il venditore spedisce tranquillo perché sa che i soldi ci sono; tu sai che non si muovono finché l'oggetto non è arrivato davvero.

I tempi (le cifre esatte sono nei NUMERI DI OGGI):
- dopo la consegna hai un certo numero di ore per controllare l'oggetto e confermare. Oggi i sats non partono da soli: allo scadere arriva un promemoria, e se il silenzio continua interviene un moderatore. Nessuno incassa mentre tu non hai confermato;
- per un codice o un buono digitale le finestre sono più corte, e lì allo scadere i sats vanno al venditore: provalo subito.
- se compri più codici nello stesso ordine (per esempio 10 buoni), si aprono uno alla volta: apri il primo, lo provi e tocchi «✅ Funziona» per vedere il successivo. Ogni codice ha le sue ore per dire «⚠️ Non funziona»: la disputa riguarda solo quel codice, i codici che hai confermato restano pagati al venditore e quelli che non hai mai aperto ti tornano. I sats partono tutti insieme alla fine, quando confermi l'ultimo (se ti fermi e non apri il successivo, dopo un po' vanno al venditore). Chi vende scrive ogni codice nel suo riquadro, e può correggerne uno finché non l'hai aperto.

I sats restano in un conto Lightning della piattaforma solo per il tempo dell'affare: non sono un investimento e non vengono messi a rendere. Quando l'affare si chiude escono, al venditore o a te.

<!-- pezzo libro-014 | libro -->
## Libro · Se qualcosa va storto: la disputa (1/2)

Finché i sats sono nel deposito puoi aprire una disputa dalla pagina del tuo ordine. Il deposito si congela e interviene un moderatore: legge le due versioni, guarda quello che c'è (foto, tracciamento, messaggi nell'ordine) e decide. Le strade sono tre:
- i sats tornano a te, spedizione compresa;
- i sats vanno al venditore;
- i sats tornano a te meno le spese di spedizione, che restano al venditore (per esempio un pacco tornato indietro per un indirizzo sbagliato).
Se l'oggetto va restituito, il rimborso parte dopo che è tornato indietro.
Il reso a spese del venditore (dal 18 novembre 2026): se l'oggetto è arrivato rotto, bloccato o diverso dall'annuncio, il moderatore può decidere che a pagare la spedizione di ritorno sia il venditore. Il venditore crea un'etichetta di reso prepagata e la manda nella chat dell'ordine entro 3 giorni; chi ha comprato non paga niente, usa quell'etichetta, rispedisce e scrive il tracciamento nell'ordine. Il rimborso parte quando il venditore riceve l'oggetto. Se in 3 giorni l'etichetta non arriva, chi ha comprato tocca «⏰ Il venditore non ha mandato l'etichetta» nella pagina dell'ordine: avvisa i moderatori, che guardano la chat e possono rimborsarlo subito. Barattolo non paga e non vende etichette.

Aprire una disputa non è un'accusa: spesso è un malinteso che si chiarisce in mezza giornata. Prima di aprirla conviene scrivere all'altra persona.

Dove il deposito non può proteggerti, ed è meglio saperlo prima:
- una prestazione (una lezione, una consulenza) avviene fuori da Barattolo: in disputa si guardano le condizioni scritte nell'ordine, come l'appuntamento concordato e il collegamento lasciato;
- un codice rivelato non torna indietro: nessuno può sapere se l'hai già usato. Provalo subito;
- un posto in un abbonamento condiviso può sparire dopo: il piano resta di chi te l'ha venduto;
- nel ritiro a mano il controllo è tuo: guarda e prova l'oggetto prima di confermare, perché con la conferma i sats partono e non tornano indietro;
- un punto di ritiro di Barattolo è una persona che si è offerta, non un'azienda: se segna di aver ricevuto il pacco, per noi chi ha spedito ha consegnato. Vai a ritirare presto;
- un pacco perso o rovinato dal corriere è una cosa fra chi spedisce e il corriere: Barattolo garantisce la transazione, non il viaggio. Spedite sempre col tracciamento, e le cose di valore con la copertura del corriere. Chi vende può anche spedire con la posta senza tracciamento (la sceglie fra i corrieri quando segna la spedizione): costa meno, ma il pacco non si può seguire, e se si perde il rischio resta di chi l'ha spedito;
- il deposito garantisce l'oggetto promesso, non i gusti: «non mi piace più» non è un difetto, un oggetto diverso dalla descrizione sì;
- un indirizzo sbagliato lo paga chi l'ha scritto: se il pacco torna indietro, le spese di spedizione restano a te. Per questo prima di pagare ti chiediamo di ricontrollarlo.

<!-- pezzo libro-015 | libro -->
## Libro · Se qualcosa va storto: la disputa (2/2)

Pagare fuori da Barattolo (un bonifico, un pagamento diretto al venditore) vuol dire rinunciare al deposito di garanzia: nessuno può più aiutarti a recuperare i soldi.

<!-- pezzo libro-016 | libro -->
## Libro · Vendere nel mercatino (1/10)

1. Tocca «Vendi» (il tasto ＋ in basso).
2. Aggiungi almeno una foto (senza foto non si pubblica), il titolo, la descrizione, la categoria e il prezzo. Sotto la categoria c'è «Sottocategoria (facoltativa)»: Barattolo la propone da solo leggendo il titolo, tu puoi cambiarla o lasciare «La sceglie Barattolo» (se dal titolo non è sicuro, l'annuncio sta solo nella categoria e si trova in «Tutta la categoria»).
3. Scegli come consegni: spedizione (con i corrieri che usi), punto di ritiro o locker, ritiro a mano in zona, o consegna digitale per codici e buoni.
4. Pubblica. Ogni annuncio passa dalla moderazione, anche quando lo modifichi: se qualcosa non convince resta in attesa di un moderatore, e se viene fermato il messaggio spiega perché e come rimediare.

Chi vende alimenti o bevande (categoria «Alimenti e bevande») trova sotto la descrizione il riquadro «🏷️ Etichetta dell'alimento»: peso netto, ingredienti, gli allergeni da toccare fra i 14 della legge europea e la tabella dei valori nutrizionali per 100 g o per 100 ml, da copiare dalla confezione. Dal 18 novembre 2026 la tabella nutrizionale è obbligatoria, perché la legge europea (Reg. UE 1169/2011) chiede che chi compra online legga queste informazioni prima di pagare: senza tabella l'annuncio non si pubblica. Va compilata tutta; l'energia basta scriverla in kJ o in kcal. Se per quel prodotto la legge non la chiede, si tocca «Non dovuta per legge» e si sceglie il motivo: frutta, verdura o prodotto non lavorato di un solo ingrediente; spezie, erbe, sale, caffè o tè; acqua o aceto; alcolico oltre l'1,2%; confezione sotto i 25 cm²; prodotto artigianale venduto da chi lo fa, in piccole quantità. Chi compra legge il motivo nell'annuncio. Peso, ingredienti e allergeni restano facoltativi, e si possono aggiungere anche origine, conservazione, lotto e scadenza. Gli annunci di alimenti pubblicati prima restano online: la tabella viene chiesta alla prima modifica. Chi compra trova tutto nella pagina dell'annuncio, nella sezione «Etichetta» sotto la descrizione.

La «Zona» di un annuncio nuovo parte già scritta con quella del tuo ultimo annuncio (per esempio «Dro (TN)»): se vendi da un altro posto la cambi come ogni altro campo (dal 16 novembre 2026).

Gli annunci esauriti: quando vendi l'ultimo pezzo l'annuncio diventa «Esaurito», resta in fondo al tuo negozio e con «🔄 Rifornisci» torna in vendita appena hai altri pezzi. Se era un pezzo unico che non tornerà (un oggetto usato, per esempio), in «I tuoi annunci» o nella sua pagina tocca «🗑 Elimina»: sparisce dal negozio, da Nostr e dal canale, ma gli ordini e le recensioni restano (dal 16 novembre 2026). Si può fare quando l'ordine di quel pezzo è concluso: con una spedizione, un reso o un rimborso ancora aperti l'app dice di aspettare.

<!-- pezzo libro-017 | libro -->
## Libro · Vendere nel mercatino (2/10)

Hai un catalogo grande? Nel Profilo, nel gruppo «Annunci», c'è «📥 Carica tanti annunci insieme»: scarichi il modello CSV, una riga per annuncio, fino a 500 annunci per volta. Ogni riga vuole almeno una foto, con un link nella colonna «foto» (più d'uno separati da |) oppure coi nomi dei file dentro uno ZIP che carichi insieme; una riga senza foto viene scartata. Prima di pubblicare tocchi «🔎 Controlla il file» e vedi cosa va e cosa no. Se hai un negozio Shopify o WooCommerce, nella stessa sezione lo puoi collegare (dal 22 novembre 2026, a chi vede i negozi collegati la sezione si chiama «📥 Carica prodotti» e apre su tre scelte: «Da un file CSV», «Shopify», «WooCommerce»; ognuna apre la sua pagina con «‹ Indietro»): i prodotti entrano da soli e restano in pari (se la sezione non la vedi, guarda i NUMERI DI OGGI o chiedi allo staff). Nel collegamento (✏️ sul negozio) c'è anche «Categoria dei prodotti»: se vende tutto dello stesso tipo la sceglie lì e vale per tutti, anche per quelli già entrati; con «Decide il negozio» Barattolo usa la categoria del suo e-commerce quando corrisponde a una delle nostre; se nemmeno il negozio la indica, Barattolo prova a capirla dal nome del prodotto, e il resto va in «Altro». Gli annunci importati passano dalla moderazione come gli altri. Dal 18 novembre 2026 i prodotti di un negozio collegato escono anche su Nostr, come gli altri annunci: un annuncio per prodotto (le varianti, per esempio le taglie, sono un annuncio solo col prezzo «da»), entro qualche ora dall'entrata, e si aggiornano da soli; un prodotto tolto dal negozio sparisce anche da lì. Chi ha anche una chiave Nostr sua li firma lui, a nome suo, con «✍️ Firma i tuoi N annunci per Nostr» nel Profilo; dal 19 novembre 2026, se non firma entro 3 giorni, li pubblica Barattolo col suo nome, e se firma dopo tornano a nome suo. Se il negozio collegato non risponde per cinque ore di fila il collegamento si ferma («⚠️ non risponde») e il bot lo dice al venditore; da lì Barattolo riprova da solo una volta al giorno e, appena il sito risponde, il collegamento riparte e il bot lo avvisa. Se ha cambiato le chiavi del negozio, le riscrive con ✏️; ▶️ lo riaccende subito. Lo stesso negozio non si collega due volte, nemmeno scrivendo l'indirizzo con maiuscole diverse. Dal 19 novembre 2026, se un prodotto WooCommerce ha delle tendine che non cambiano il prezzo (lasciate su «Qualsiasi» nel negozio, per esempio il gusto), entra come un annuncio solo con le sue tendine: chi compra sceglie nella scheda o alla cassa («🎁 Le tue scelte»), senza scelta non si paga, e il venditore trova la scelta nella nota dell'ordine. Dal 21 novembre 2026 il venditore sceglie COSA entra dal suo negozio: «🧺 Cosa entra» sul negozio collegato, con «Tutto, tranne…» o «Solo questi…» per categorie e tag del suo negozio, e prodotto per prodotto (la scelta sul singolo prodotto vince sulle categorie). Un negozio appena collegato aspetta questa scelta prima di far entrare qualcosa. Quello che esce non si cancella: va «in panchina» e con «↩️ Riaccogli» torna lo stesso annuncio; le scelte valgono dal giro che parte appena salva. Sugli annunci che arrivano dal negozio il bottone si chiama «🪑 Rimuovi da qui» (dal 22 novembre 2026): toglie l'annuncio da Barattolo e non dal suo e-commerce, e lo mette in panchina, e un prodotto messo in bozza sul negozio esce e torna da solo quando lo ripubblica. Un prodotto cancellato dal negozio invece sparisce davvero.

<!-- pezzo libro-018 | libro -->
## Libro · Vendere nel mercatino (3/10)

Per incassare da solo imposta il tuo indirizzo Lightning nel Profilo: quando chi compra conferma, i sats ti arrivano lì.

Se spedisci a un locker o a un punto di ritiro, il codice per ritirare il pacco lo manda il corriere a chi hai scritto come destinatario. Se chi compra ha lasciato un'email per il corriere, puoi metterla sull'etichetta e il codice arriva direttamente a lui. Se non l'ha lasciata, il codice arriva a te: appena ce l'hai, apri l'ordine e incollalo in «📦 Istruzioni di ritiro per l'acquirente». È l'unico modo in cui lui lo riceve, e la giacenza dura pochi giorni.

Le commissioni del mercatino: Barattolo non prende commissioni, né a chi vende né a chi compra. Si pagano solo le commissioni della rete, che non vanno a Barattolo: su Lightning sono pochi sats o niente, on-chain sono quelle dei miner. Se un giorno cambiasse, la cifra sarebbe nei NUMERI DI OGGI. Negli acquisti on-chain può esserci solo una quota fissa a Barattolo per le spese di rete, scritta nel conto prima di pagare: quanto vale oggi lo dicono i NUMERI DI OGGI.

Quando qualcuno chiede delle commissioni, tieni sempre separati il mercatino (zero commissioni di Barattolo, solo quelle della rete) e lo scambio P2P (la commissione del coordinatore, spiegata più sotto). Mescolarli confonde.

Le donazioni: chi vuole sostenere Barattolo con qualche sats può mandarli all'indirizzo Lightning zap@barattolo.store (si incolla nel wallet come destinatario, si sceglie l'importo e si invia), oppure con uno zap al profilo Nostr «Barattolo», che accetta anche bitcoin on-chain. Sono un regalo libero: non danno vantaggi nell'app e non sono mai obbligatorie. Se qualcuno chiede come donare, dai questo indirizzo e ringrazia di cuore.

<!-- pezzo libro-019 | libro -->
## Libro · Vendere nel mercatino (4/10)

Quando arriva un ordine il bot ti avvisa. Spedisci, segna il corriere e il codice di tracciamento nell'ordine, e aspetta la conferma di chi compra. Se spedisci una busta senza codice scegli «✉️ Posta senza tracciamento» fra i corrieri: non serve fingere una consegna a mano. Hai scritto un codice sbagliato, o hai segnato «Consegna a mano» su un ordine che invece hai spedito? Nell'ordine c'è il bottone per correggerlo, e chi compra viene avvisato. L'indirizzo di chi compra lo vedi solo tu, per stampare l'etichetta: non usarlo per altro. Nel messaggio «Hai venduto» e in cima al riquadro «📦 Spedisci» dell'ordine c'è il giorno entro cui spedire: cinque giorni dal pagamento, il giorno in cui parte il promemoria (non si annulla niente da solo: è un impegno con chi ha comprato). Accanto c'è «📖 Come si spedisce?», la guida in quattro passi: imballa, compra l'etichetta, consegna il pacco, segna come spedito. Nei passi dell'ordine compaiono anche l'ora del pagamento e quella della spedizione, e chi compra legge entro quando il venditore spedisce. Non hai ancora l'etichetta? Nel riquadro della spedizione c'è il link «Spedisci con Packlink» (Poste, BRT, InPost e altri, da 5,48 €): si paga là, in euro, non in sats; nell'ordine incolla il codice del corriere, non quello dell'ordine Packlink.

Le prestazioni si possono vendere, ma devono essere definite: quanto durano, che cosa comprendono, a che prezzo. «Un'ora di lezione di inglese» sì; «ti faccio quello che ti serve» no.

Su Barattolo non si vendono: armi, droghe, servizi sessuali, refurtiva, contraffazioni, documenti, dati personali, farmaci, animali protetti.

Un venditore può mettere il negozio in ferie (gli annunci restano ma non si comprano) e ha una pagina del negozio col suo link da condividere. Le ferie si mettono da Profilo → «🌴 Negozio in ferie», scegliendo il giorno del rientro: gli annunci restano in vetrina col prezzo in grigio, nessuno li può comprare, e al rientro tornano comprabili da soli. Non si chiude con affari da spedire o aste in corso.

Le foto dell'annuncio (dal 24 novembre 2026): sotto ogni foto ci sono le frecce ◀ ▶ per spostarla, e la prima foto è la copertina. Sotto ogni foto c'è anche «Descrizione della foto (facoltativa)», fino a 80 caratteri: chi compra la legge sulla foto nella scheda dell'annuncio e aprendola a schermo intero. Sul computer le foto stanno in fila accanto al riquadro «Aggiungi foto». In «Modifica» le foto attuali restano: se ne aggiungono altre fino a 5, si spostano con le frecce e si toglie quella che non si vuole con la ✕. Le descrizioni passano dalla moderazione come il resto.

<!-- pezzo libro-020 | libro -->
## Libro · Vendere nel mercatino (5/10)

Le varianti (dal 24 novembre 2026): nel modulo «Vendi», sotto la quantità, c'è «🎨 Varianti (facoltative)». Si scrive il nome (per esempio «Colore») e le voci separate da virgole («rosso, blu, verde»). Così chi compra sceglie la voce prima di pagare, e chi vende la trova nella nota dell'ordine; prezzo e pezzi sono quelli dell'annuncio. Se ogni voce ha un prezzo o dei pezzi diversi, si spunta «Prezzo o pezzi diversi per ogni variante» e si scrivono accanto a ogni voce (vuoto = quelli dell'annuncio): nascono tanti annunci quante le voci, che in vetrina sono una card sola, e nella scheda chi compra sceglie la variante coi bottoncini. Ogni variante poi si modifica dalla sua «Modifica», come un annuncio qualunque, e si esaurisce da sola. Le varianti non valgono per le aste e gli abbonamenti.

Fermare per un po' un annuncio solo: nella sua scheda «🔄 Aggiorna i pezzi» e 0. Diventa «Esaurito»: resta visibile, in grigio, ma nessuno lo compra; con «🔄 Rifornisci» si rimettono i pezzi e torna in vendita. Non vale per i servizi e per gli annunci importati da Nostr. Per toglierlo proprio dalla vetrina, senza scadenza: nella sua scheda «🙈 Nascondi dalla vetrina». Nessuno lo vede più (nemmeno col link), e lo ritrovi in Profilo → «I tuoi annunci», in grigio, con «👁 Rimetti in vetrina» per farlo tornare quando vuoi (dal 24 novembre 2026). Non si nasconde con un ordine ancora aperto su quell'annuncio, né un'asta o un annuncio importato da Nostr o da un negozio collegato. Bozze degli annunci non ce ne sono: appena pubblicato, l'annuncio passa dalla moderazione e poi va in vetrina.

I numeri del negozio: nel Profilo, gruppo «Il tuo negozio», il cassetto «📊 I numeri del negozio» mostra le visite alla pagina del negozio, le vendite concluse (ultimi 30 giorni e da sempre, coi sats che ha incassato: spedizione compresa, commissione tolta) e le recensioni. Contano gli ordini del mercatino conclusi, non gli scambi P2P. Quanto hai comprato NON si vede nel Profilo, per la privacy (scelta del 17 novembre 2026): né in questo cassetto né nella riga sotto il nome, che dice solo «N vendite concluse». I tuoi acquisti li trovi uno per uno in «Ordini». Chi ha solo comprato e non ha annunci non ha questo cassetto.

<!-- pezzo libro-021 | libro -->
## Libro · Vendere nel mercatino (6/10)

I codici sconto: nel Profilo, gruppo «Spedizioni e sconti», alla voce «🎟 Codici sconto», chi vende crea i suoi codici (in percentuale o a cifra fissa, con una durata e un tetto di usi) e li dà a chi vuole; chi compra lo scrive alla cassa. Col tasto «📣» sulla riga di un codice ancora valido può anche mandarlo ai clienti che hanno già comprato da lui: sceglie chi (sono già tutti spuntati) e preme «Invia invito sconto». Il messaggio lo manda Barattolo, sul bot, come DM Nostr o dentro l'app, e chi vende non vede mai i contatti dei clienti. Ogni cliente riceve lo stesso codice una volta sola, e al massimo un invito a settimana dallo stesso negozio. Un codice scaduto, finito o in pausa non si può mandare: si riattiva con ✏️ (scegliendo di nuovo i giorni, che ripartono da oggi). La data «scade il» è scritta all'italiana, giorno/mese/anno. Chi riceve le offerte e non le vuole più le spegne in Profilo → «🔔 Avvisi» → «🎟️ Offerte dei negozi», per tutti i negozi o per uno solo.

I premi fedeltà del negozio: nel Profilo, gruppo «Spedizioni e sconti», alla voce «🎀 Premi fedeltà», chi vende scrive fino a quattro gradini in euro, ognuno col suo regalo («da 100 € la borsa, da 200 € la tazza»). Barattolo conta quanto ogni cliente ha speso in quel negozio (solo gli ordini conclusi, in euro al cambio di quel giorno, mai gli altri negozi) e, quando passa una soglia, avvisa tutti e due e mostra il premio sul suo ordine successivo pagato e non ancora spedito: «Nel pacco trovi…» a chi compra, «Nel pacco metti…» a chi vende. Il regalo lo mette nel pacco il venditore: Barattolo non lo compra e non lo spedisce, e non è uno sconto (il prezzo non cambia). Ogni soglia vale una volta per cliente; se l'ordine col premio viene annullato, il premio passa al prossimo. Sulla pagina del negozio chi compra vede i gradini e quanto ha già speso lì. Non sono punti XP né livelli: quelli si fanno con tutti gli affari su Barattolo. Dal 18 novembre: il negozio sceglie se scrivere le soglie in euro o in sats (interruttore «€ euro / ₿ sats» nel cassetto; in sats conta i sats pagati, in euro ogni ordine al cambio del suo giorno); il regalo si può scegliere dalla tendina fra gli articoli in vetrina del proprio negozio, oppure «✏️ Lo scrivo io». Lo sceglie sempre chi vende, mai chi compra. Chi ha un premio da riscuotere lo sa: gli arriva il messaggio del bot «hai un premio da riscuotere» (anche quando il negozio scrive una soglia che aveva già passato), lo legge sulla pagina del negozio («🎁 Hai un premio da riscuotere») e sulla scheda di ogni articolo di quel negozio; quando paga l'ordine, il messaggio «Ordine pagato» gli dice cosa troverà nel pacco e «Hai venduto» dice al negozio cosa metterci. Nello stesso cassetto, «🏆 I tuoi clienti» mostra al negozio la classifica di chi ha comprato da lui, dal più alto per totale speso (solo ordini conclusi), in sats o in euro con un tocco: ognuno vede solo i suoi clienti.

<!-- pezzo libro-022 | libro -->
## Libro · Vendere nel mercatino (7/10)

Gli abbonamenti ai canali Telegram (dal 20 novembre 2026): alcuni negozi vendono un mese di accesso al loro canale Telegram privato. Nell'annuncio c'è la nota «🔑 Abbonamento di 30 giorni a…» col nome del canale. Si paga in Lightning, un mese per volta. Dopo il pagamento chi compra apre l'ordine e tocca «🔓 Rivela»: trova il suo link d'invito, che vale una volta sola e solo per lui (se è su Barattolo con Telegram, entra solo il suo account). Toccato il link chiede di entrare e il bot di Barattolo lo accetta da solo. Quando entra nel canale l'acquisto è definitivo e non si rimborsa, perché i contenuti li ha già visti: una disputa si apre solo prima di entrare, per esempio se il link non funziona. Per restare si rinnova ricomprando lo stesso annuncio: chi è già dentro ha un mese in più, senza link nuovo. Barattolo avvisa 3 giorni prima della scadenza e il giorno stesso; dopo altri 3 giorni senza rinnovo il bot toglie l'abbonato dal canale, e chi ripaga riceve un link nuovo e rientra. Lightning non può prelevare da solo ogni mese, quindi il rinnovo è sempre un gesto di chi compra. La casella per vendere abbonamenti la vede solo chi ha un canale collegato da Barattolo.

Chi vende contenuti digitali può aggiungere all'annuncio le domande da fare a chi compra (testo breve, elenco a tendina, email, sì/no), obbligatorie o facoltative; nome, cognome ed email si aggiungono con un tocco. Il numero di telefono non si può chiedere.

<!-- pezzo libro-023 | libro -->
## Libro · Vendere nel mercatino (8/10)

La cassa in negozio (se nelle REGOLAZIONI del pannello «Cassa in negozio» è accesa): chi vende di persona, in un negozio, a un banco del mercato o a un evento, può usare Barattolo come cassa. Dal 20 novembre 2026 la cassa sta SOLO nell'app Android «Barattolo Negozio» (l'icona: due barattoli sul bancone di un mercato, sotto una tenda a strisce, su Zapstore accanto a Barattolo), la faccia di Barattolo per chi sta al banco, con lo stesso account: nell'app e nel sito di Barattolo non c'è più (né nel Profilo né in «Ordini»). Dal browser, per esempio sul tablet del banco, ci si arriva dall'indirizzo barattolo.store/?app=negozio. L'app si apre direttamente sulla cassa, l'indietro chiude l'app invece di portare al mercatino, e chi non è ancora entrato vede la schermata d'accesso con Telegram o Nostr, lo stesso account di Barattolo. Ha due schede: «🧾 Cassa» e «📒 Vendite», cioè le vendite della cassa; a chi tiene un punto di ritiro di Barattolo compare anche «📦 Banco» coi pacchi in arrivo. Chi ha un negozio su Barattolo entra direttamente nella pagina del proprio negozio, uguale a quella che vede chi compra (in alto a sinistra «← Barattolo» per uscire, a destra «📒 Vendite»): un tocco su una card mette un pezzo nel conto (sulla foto compare ✓ o il numero dei pezzi), in fondo c'è la barra del carrello col totale e «Controlla e incassa», che apre il conto con le righe degli articoli (− e + per cambiare i pezzi), l'importo libero facoltativo, la nota e «Incassa»; «Nuovo conto» riporta alla vetrina. Altrimenti la Cassa è fatta come il carrello: le card dei propri annunci attivi con almeno un pezzo, ognuna con «Aggiungi» (o un tocco sulla card) e poi i tasti «−» e «+»; in fondo la stessa barra del carrello col totale e i pezzi, e al posto di «Controlla e paga» il bottone «Incassa». Sopra le card si può anche scrivere un importo libero (in euro o in sats, il tasto accanto cambia valuta), e una nota per sé (es. «tavolo 4»). Se non ci sono annunci attivi la Cassa lo dice, e si incassa scrivendo l'importo. Compare un QR grande con due porte, «⚡ Lightning» e «On-chain»: il cliente lo inquadra con qualsiasi wallet, e non gli serve un account su Barattolo né Telegram. I sats vanno DRITTI al wallet di chi vende: in Lightning al suo Lightning address del Profilo, on-chain a un indirizzo nuovo del suo wallet (quello scelto in Profilo → «Incassi on-chain»), mai al deposito di garanzia. Per questo non c'è deposito, né spedizione, né conferma, né disputa, e Barattolo non prende commissioni: è un pagamento di persona, come al banco. Le vendite della cassa stanno nella scheda «📒 Vendite» dell'app, e toccandone una si riapre la sua ricevuta. Il totale di oggi si legge in cima alla cassa. Sul QR c'è il bottone «🔁 Gira verso il cliente»: il telefono mostra a tutto schermo, su bianco, solo la cifra, i pezzi e un QR più grande, da girare verso chi paga; quando paga compare «✅ Pagato, grazie!», e si torna alla cassa con la ✕ in alto (lo schermo resta acceso finché è aperto, se il telefono lo permette). Nella scheda «📒 Vendite», in cima, c'è la «📒 Chiusura di cassa» di oggi o di ieri: quante vendite pagate, i sats (e gli euro al cambio di adesso), quanti in Lightning e quanti on-chain, i pezzi usciti, gli importi liberi, e «📋 Copia il riepilogo» per incollarlo dove si tiene la contabilità; gli on-chain ancora in arrivo non sono contati. Quando il pagamento arriva la cassa dice «✅ Pagato!». Se il wallet di chi vende non comunica i pagamenti, la cassa dice di guardare il proprio wallet e di toccare «✓ Ricevuto». On-chain, appena il pagamento si vede in rete la cassa dice «in arrivo»: per una cifra piccola si può consegnare subito («✓ Consegna adesso»), per una grande è meglio aspettare la conferma (di solito fra 10 e 60 minuti). On-chain si incassa da 546 sats in su. I pezzi venduti alla cassa escono da soli dalla vetrina, e l'annuncio finito diventa venduto. Per usare la cassa serve almeno uno fra il Lightning address e il wallet on-chain nel Profilo: se mancano, la cassa lo dice e porta al campo giusto.

<!-- pezzo libro-024 | libro -->
## Libro · Vendere nel mercatino (9/10)

Le promozioni a pagamento (se nelle REGOLAZIONI del pannello «Promozioni a pagamento» sono accese): chi vende può far vedere di più un suo annuncio dal tasto «Promuovi» (giallo e rosso come un razzo, col razzo disegnato), in cima alla scheda dell'annuncio, subito sotto la foto. Il foglio ha tre voci: la voce scelta apre sotto un disegnino animato di cosa succede, e la prima è già scelta e aperta quando il foglio si apre. «In cima», 5.000 sats: l'annuncio torna primo tra i più recenti ed esce di nuovo nel canale Barattolo Vetrina; si può rifare dopo 24 ore. «In evidenza»: dentro la voce si sceglie 7 giorni (15.000 sats) o 15 giorni (25.000 sats); l'annuncio entra nella fila «In evidenza» della home, sotto «Da scoprire», con l'etichetta arancione «In evidenza», e il primo giorno è anche in cima; i posti sono 8, e se sono tutti presi il foglio dice quando si libera il prossimo; se è già in evidenza i giorni si aggiungono. «Il negozio in Da scoprire», 30 giorni, 50.000 sats: la card del negozio va in «Da scoprire» in home, fatta col banner del negozio e il logo; serve prima il banner approvato dal moderatore: senza, la voce si può scegliere lo stesso, lo dice, e il tasto in fondo diventa «Prima fai il banner» e porta al cassetto del banner nel Profilo (il banner si paga a parte, una volta sola; dopo l'ok del moderatore si torna a Promuovi per la card); finiti i 30 giorni il negozio resta per sempre fra i Consigliati. Nel prezzo c'è anche una pagina dedicata del negozio, come quelle dei Consigliati, che prepara lo staff: dopo il pagamento il negozio trova nella sua chat di Assistenza (Profilo → «Aiuto» → «💬 Assistenza») la richiesta di mandare da 3 a 6 foto, il logo e un testo su chi sono e cosa fanno, e la pagina gliela fanno vedere prima di pubblicarla. Questa terza voce c'è anche nel cassetto del banner del negozio nel Profilo. Si paga una volta con una fattura Lightning, non è un abbonamento, non ci sono sconti. Le card in «Da scoprire» e nella fila «In evidenza» si danno il turno: a ogni apertura dell'app parte per prima quella dopo. Se una promozione pagata non si applica, o un moderatore la toglie, il rimborso lo fa lo staff a mano: scrivi allo staff. I prezzi esatti sono quelli che mostra il foglio.

<!-- pezzo libro-025 | libro -->
## Libro · Vendere nel mercatino (10/10)

Sul telefono «Da scoprire» scorre da sola ogni 5 secondi: la card al centro è grande, quelle ai lati più piccole. Si ferma quando la tocchi, e non si muove se nel telefono hai chiesto meno animazioni. Sotto la card grande c'è una fila di quadrati fermi, uno per ogni negozio della fila: la foto di un suo prodotto e sotto cosa vende (per esempio «Si gioca in sats»); toccando un quadrato si apre il negozio. Finché i negozi in «Da scoprire» sono meno di otto, ognuno sta sia nella card grande sia in un quadrato (con un negozio solo i quadrati non ci sono); da otto in su un negozio sta o nella card grande o nei quadrati. La foto del quadrato la sceglie lo staff per i negozi con la pagina dedicata (per esempio il ritratto di AndreAI), per gli altri è la foto del loro annuncio più recente. Dietro la card grande e i quadrati c'è uno sfondo sfumato coi colori della foto della card al centro, che cambia piano quando la card scorre. I quadrati restano fermi anche mentre la card grande scorre, e a ogni apertura dell'app i negozi si danno il turno. L'ordine della home è: «Da scoprire» in cima, poi la fila degli annunci in evidenza (tutte e due senza titolo: le card dicono già cosa sono), poi «Esplora per categorie», poi gli scambi P2P e gli annunci. Dopo i primi sei annunci ci sono due banner, uno sopra l'altro: «Offerte a tempo» e «Sconti dei negozi» (ci sono solo quando ci sono offerte o sconti; con meno annunci stanno in fondo). Toccandone uno vedi solo quegli annunci, e il banner prende il bordo arancione; ritoccandolo torni a vederli tutti. Fino al 24 novembre 2026 queste due card stavano in «Da scoprire». Toccando un negozio in «Da scoprire» la sua pagina si apre subito: dalla card grande, sul telefono, la card si allarga e sale in cima e diventa l'immagine in testa al negozio, e sotto si apre il resto della pagina; da un quadrato la pagina sale dal basso. Se nel telefono hai chiesto meno animazioni, il negozio si apre e basta.

In alto nella home, accanto al nome Barattolo, c'è un megafono: apre il canale Telegram delle notizie di Barattolo, https://t.me/barattolostore. Dal 23 novembre 2026 la fascia «Barattolo è in fase di test» in cima alla home non c'è più. All'apertura compare un riquadro che invita a entrare nel canale delle notizie (la prima volta prima del tour di benvenuto, che parte quando lo chiudi): torna al massimo ogni 3 giorni e, quando sei entrato nel canale, non compare più. Il bottone del podio che stava in alto si è spostato nel Profilo: è «Il Podio di Barattolo», subito sotto «Classifica Streak», e apre la classifica del mercatino (si vede solo quando la classifica è accesa).

<!-- pezzo libro-026 | libro -->
## Libro · Spedizione, indirizzo e ritiro

- Spedizione a un indirizzo: lo scrivi al momento dell'acquisto e resta dentro l'ordine. Lo vede solo il venditore, è cifrato nel database e viene cancellato appena confermi di aver ricevuto. I moderatori non lo leggono, nemmeno in disputa.
- Punto di ritiro o locker: un tuo indirizzo non serve proprio; al banco basta il nome del destinatario. Puoi lasciare un'email se vuoi che il codice di ritiro te lo mandi il corriere: è facoltativa.
- Ritiro a mano: vi accordate per vedervi in zona. Controlla l'oggetto prima di confermare.

<!-- pezzo libro-027 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (1/24)

Nel P2P non compri da Barattolo: compri da un'altra persona. Vi accordate su un prezzo, gli euro viaggiano fra voi due col metodo scelto, e i sats restano bloccati finché gli euro non sono arrivati (sul Lightning con una fattura «trattenuta», non in un deposito di Barattolo). Barattolo non tocca i tuoi euro. Si entra dal tasto «P2P» in basso; lì ci sono il «Libro ordini», «I miei scambi», «Pubblica» e «Info P2P», che spiega tutto con calma. Dal 20 novembre 2026 la pagina di uno scambio («Nel dettaglio», Lightning e on-chain) ha in alto tre schede, sempre in vista anche scorrendo: «📋 Passi» (si apre lì: i passi, lo stato, il bottone da toccare, e in fondo «✕ Annulla» e la disputa), «💰 Importi» (il conto: quanto ricevi e quanto mandi) e «💬 Chat» (la chat e chi è l'altra persona; un pallino rosso conta i messaggi nuovi). Se la chat non c'è ancora, le schede sono due. Sul computer a schermo largo, fuori da Telegram, la pagina resta su colonne, senza schede. Dal 20 novembre 2026 anche il foglio «Pubblica» del P2P va a passi, una pagina alla volta: «1. Cosa» (valuta, metodi di pagamento, zona di scambio), «2. Quanto» (importo, tipo di prezzo, premio), «3. Regole» (chi può prendere l'ordine, tempo per pagare, cauzione, pausa, paracadute, ripubblica) e «4. Rileggi» (un riepilogo «Rileggi prima di pubblicare», poi il bottone che pubblica). Si va avanti con «Avanti →» (se manca qualcosa del passo lo dice e non va avanti), si torna con «← Indietro» o toccando un passo già fatto nella riga in alto. L'interruttore «On-chain / Lightning» resta in cima a ogni passo, e le scelte sono le stesse di prima. Con Barattozon il foglio resta quello di sempre, coi suoi quattro passi del PayCode.

Come funziona, in cinque passi:
1. Qualcuno pubblica un ordine: dice se compra o vende sats, per quanti euro e con quali metodi di pagamento. L'ordine va nel libro, che vedono tutti.
2. Tu lo prendi: scegli il metodo e l'ordine si riserva a te. La tua scelta arriva all'altra persona: nella pagina dello scambio legge «ha scelto…» (per esempio «USDT su Tron» o «SEPA Instant»), la stessa riga in cima alla chat dello scambio, e un avviso su Telegram. Se un recapito arrivato è per un metodo o una rete diversi da quelli scelti, la pagina lo dice in rosso: prima di pagare, chiarite in chat.
3. Chi vende blocca i sats: paga una richiesta speciale (una hold invoice) che trattiene i sats senza consegnarli. Da lì sono in garanzia.
4. Chi compra manda gli euro col metodo scelto, al recapito che l'altra persona lascia dentro lo scambio, e poi lo dice nell'app.
5. Chi vende controlla di aver ricevuto gli euro e libera i sats: arrivano all'indirizzo Lightning o alla fattura di chi compra.

<!-- pezzo libro-028 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (2/24)

La garanzia: nello scambio Lightning chi vende paga una fattura «trattenuta» (hold invoice), e i sats restano bloccati nella rete Lightning, non in un deposito di Barattolo. Possono prendere due strade sole: andare a chi compra quando chi vende conferma di aver ricevuto gli euro, o tornare a chi vende. Nessuno, nemmeno Barattolo, può prenderli o dirottarli altrove. A farli andare da una parte o dall'altra è il coordinatore, un programma che si chiama Mostro, che Barattolo fa girare sul suo nodo. Per il P2P Lightning non dire mai che Barattolo «fa da garante», «tiene i sats» o ha un «deposito di garanzia»: il deposito di garanzia di Barattolo c'è solo nel mercatino (sugli scambi on-chain c'è il deposito a due firme su tre, spiegato più sotto).

Come si legge una card del libro: in alto a destra due quadratini con una freccia dicono cosa invii e cosa ricevi (le stelle blu dell'Europa per gli euro, la T verde di Tether per gli USDT, il fulmine nero per i sats su Lightning, la ₿ arancio per bitcoin on-chain). Sotto ci sono la cifra da inviare e quella da ricevere, i metodi di pagamento e, nel riquadro in fondo, la faccia di chi ha pubblicato con le sue stelline e quanti scambi P2P ha già fatto («✅ 22 scambi P2P»); toccando la faccia si apre il suo negozio (anche sulle card on-chain; se non ha ancora un negozio, l'app te lo dice e non apre l'ordine). La riga colorata sul bordo di sotto è il tempo che resta all'ordine: si accorcia, diventa arancio negli ultimi tre giorni e rossa, lampeggiante, nell'ultimo.

Il prezzo di bitcoin nel libro: in cima al libro P2P, sotto i rettangoli «Novità», c'è la card «1 BTC adesso» col prezzo in euro (lo stesso che l'app usa per i conti, aggiornato ogni minuto), quanto è salito o sceso e una piccola linea, verde se sale e rossa se scende. Toccandola si passa dalle ultime 24 ore ai 7 giorni e ai 30 giorni; toccando il simbolo € si passa ai dollari (prezzo, linea e percentuale in dollari) e un altro tocco torna agli euro. La card è grafite lucida, un grigio scuro con un riflesso in alto a sinistra (dal 16 novembre 2026), sia di giorno sia di sera, per staccarsi dagli ordini; in dollari è identica a quella in euro (linea, percentuale e periodo, e il tocco cambia periodo anche lì). Subito dopo un aggiornamento può mostrare solo il prezzo, finché non ha la storia del periodo.

Quanto si può per ordine nel P2P, per ora (fase beta): fino a 250 € negli scambi in Lightning e fino a 999 € in quelli on-chain (dal 16 novembre 2026; prima 500 €, e fino al 12 novembre 250 €). Gli acquisti on-chain del mercatino non hanno un tetto (dal 22 novembre 2026; prima un tetto loro, separato da quello del P2P); chi prende un ordine ricevendo sull'altra rete ha il suo, 999 €. Il foglio «Pubblica» lo scrive sotto la cifra e non lascia andare oltre.

<!-- pezzo libro-029 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (3/24)

Il prezzo: gli ordini si scrivono in euro e i sats si contano al cambio del momento, per questo finché l'ordine è nel libro la cifra in sats ha il segno ≈. La cifra esatta si fissa quando l'ordine viene preso. Alcuni ordini hanno un intervallo («da 20 a 100 €»): lì scegli tu quanto. Nel foglio «Quanto vuoi scambiare?» il campo è vuoto (dal 17 novembre 2026; prima c'era già scritto il minimo e andava cancellato): si scrive la cifra, oppure si tocca «Minimo» o «Massimo» per metterla con un tocco, e poi «Continua».

I tasti «Compra BTC» e «Vendi BTC» in cima al libro P2P sono due pillole (dal 16 novembre 2026, di giorno e di sera): quella accesa, verde per «Compra BTC» e corallo per «Vendi BTC», dice quale lato del libro stai guardando.

L'ordine del libro: in cima al libro P2P la pillola con le tre righe (di serie dice «Recenti») apre «Ordina il libro», con quattro scelte: Più recenti, Convenienza, Importo dal più grande, Importo dal più piccolo. La pillola diventa arancio quando l'ordine non è quello di serie. Dal 14 novembre 2026 la scelta resta salvata su quel telefono o computer: alla visita dopo il libro si apre già ordinato così, sia in «Compra» sia in «Vendi». Su un altro dispositivo si sceglie di nuovo. Le card on-chain e quelle Lightning stanno nello stesso ordine, qualunque sia la scelta: con «Più recenti» la più nuova sta in cima, on-chain o Lightning che sia (dal 16 novembre 2026).

Premio e sconto: chi pubblica può chiedere fino al 20% sopra o sotto il prezzo di mercato. Sopra si chiama premio e conviene a chi vende, sotto si chiama sconto e conviene a chi compra. La riga c'è sempre nel conto.

La commissione del P2P la decide il coordinatore ed è già dentro i sats che passano di mano: chi vende ne blocca un po' di più, chi compra ne riceve un po' di meno. Nell'ottobre 2026, durante la beta, è il 3% in tutto, cioè 1,5% per chi compra e 1,5% per chi vende; finita la beta sarà del 4% (2% per parte). Pionieri e chi è al livello 5 hanno uno sconto dello 0,5% sulla propria parte. La cifra esatta la vedi sempre nel conto, prima di prendere un ordine. Dal 16 novembre 2026 la stessa commissione, con gli stessi sconti, vale anche negli scambi P2P on-chain (a tre chiavi); gli acquisti del mercatino, anche on-chain, restano senza commissioni di Barattolo (on-chain al più la quota fissa per le spese di rete, vedi «Bitcoin on-chain»). Negli scambi P2P on-chain la commissione è almeno di 546 sats in tutto, divisi tra i due in proporzione, perché la rete non trasmette cifre più piccole. Pubblicare o prendere un ordine non costa niente. Il riquadro colorato delle commissioni in cima al libro P2P compare solo la prima volta, alla fine del tutorial: poi non c'è più, e si rivede rifacendo «Come funziona» fino a «Fine 🎉» (toccandolo si apre il dettaglio con lo sconto).

<!-- pezzo libro-030 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (4/24)

I metodi di pagamento degli euro sono un elenco chiuso: SEPA (il bonifico), SEPA Instant, Revolut, Satispay, PayPal, Wise, Contanti (di persona), Contanti al tabacchino (Barattozon) e Contante per posta. Quando pubblichi un ordine vedi subito SEPA, SEPA Instant, Revolut, Satispay e Contanti; PayPal, Wise, il tabacchino e Contante per posta si aprono toccando «Altri metodi ▾». Chi prende un ordine sceglie fra i metodi messi da chi l'ha pubblicato, e il filtro del libro li ha tutti. Wise c'è dal 2 novembre 2026: chi riceve gli euro su Wise dà il suo Wisetag, l'email del conto Wise o l'IBAN che Wise gli ha dato (con l'IBAN può pagare anche chi Wise non ce l'ha, con un bonifico). Gli euro non passano da Barattolo: il recapito (IBAN, numero, tag) ve lo scambiate dentro lo scambio, cifrato. La garanzia protegge i sats, non gli euro: se chi compra dice di aver mandato gli euro e non è vero, chi vende semplicemente non libera; se li ha mandati e chi vende non libera, c'è la disputa.

I tempi: se il tempo scade prima che i sats siano bloccati non perde niente nessuno, e l'ordine torna nel libro o si chiude. Coi sats in garanzia avete circa quattro giorni: se chi compra non ha detto di aver pagato, allo scadere i sats tornano da soli a chi vende; se l'ha detto, si apre una disputa.

<!-- pezzo libro-031 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (5/24)

Il tempo per pagare (dal 18 novembre 2026): chi pubblica un ordine «Vendi BTC» sceglie nel foglio, alla voce «Tempo per pagare», con un cursore e un anello, entro quanto chi lo prende deve mandare i soldi: da 15 minuti a 24 ore (24 di serie); sugli ordini on-chain dal 19 novembre 2026 si parte da 30 minuti. Sotto le 24 ore si scende solo se tutti i metodi dell'ordine sono veloci (SEPA Instant, Revolut, Satispay, PayPal, USDT o cripto): con un bonifico ordinario, Wise o i contanti fra i metodi il cursore resta fermo a 24 ore e l'app dice quale metodo lo blocca. Non c'è col tabacchino, col contanti di persona, col contante per posta e sugli ordini «Compra BTC». Nel libro gli ordini con meno di 24 ore hanno il bollino «⏱ 30 min» (o il tempo scelto): chi vende ha fretta. Dal 19 novembre 2026 lo stesso bollino c'è anche sulle card «Scambi P2P» della home. Chi guarda l'ordine prima di prenderlo legge per prima cosa, in cima al foglio dell'ordine, «Hai 30 minuti per inviare gli euro e toccare "Ho inviato gli euro".» con l'icona ⏱ ferma, e sotto «⚠️ Altrimenti lo scambio scade e i sats tornano a chi vende.» (sull'on-chain: «⚠️ Altrimenti chi vende può aprire una disputa.») (dal 19 novembre 2026 anche sugli ordini on-chain, in cima a «Compra»; in USDT o franchi dice «gli USDT», «i franchi»). Dal 20 novembre 2026 la riga e i tasti «⚡ Lightning» e «₿ On-chain» restano fissi in alto anche scorrendo il foglio. Dal 19 novembre 2026 il tempo parte quando chi vende tocca «Indica dove ricevere gli euro» (sull'on-chain quando ha scritto dove vuole gli euro e il deposito è confermato), mai prima: finché chi vende non lo scrive, il tempo di chi compra non corre e l'app lo dice a tutti e due. Dalla sera del 19 novembre 2026 anche chi vende ha lo stesso tempo per dire dove vuole gli euro (o gli USDT, o l'altra valuta), da quando lo scambio è attivo (sull'on-chain dal deposito confermato): l'app gli mostra quanto resta, e il bot gli manda promemoria nella valuta dell'ordine (con tempi fino a 4 ore a metà tempo e 5 minuti prima della fine; con tempi più lunghi, compreso l'ordine normale da 24 ore, dopo 1 ora, dopo 6 ore e un'ora prima della fine). Se non lo dice in tempo, sul Lightning l'ordine torna nel libro e la garanzia torna a chi vende; sull'on-chain lo scambio si annulla e Barattolo firma il rimborso dei sats a chi li aveva depositati (lui mette la seconda firma). A chi compra non si conta niente e non deve mandare niente. Quando chi prende un ordine col tempo, un riquadro «⏱ Hai … per pagare» spiega i tre passi e va confermato con «Ho capito, prendo». Da lì, nella pagina dello scambio, tutti e due vedono un anello che si svuota e quanto resta, sotto c'è la riga «Se hai pagato, tocca "Ho inviato gli euro" prima che il tempo finisca» (rossa negli ultimi dieci minuti), e il bot manda promemoria col tempo che resta, gli ultimi a dieci e a cinque minuti dalla fine (sotto l'ora solo quello a cinque). Dal 19 novembre 2026 a chi deve pagare il bot manda anche UN messaggio «⏳ Tempo per pagare: mancano …» che si riscrive da solo ogni minuto (senza suonare ogni volta) finché tocca «Ho inviato gli euro» o il tempo finisce; alla fine dice com'è andata. Dal 20 novembre 2026 un messaggio così arriva anche a chi vende, che aspetta gli euro: «⏳ Chi compra ha ancora … per pagare», riscritto ogni minuto, e a «Ho inviato gli euro» dice di controllare il conto. Arriva solo su Telegram: chi riceve gli avvisi solo come DM Nostr non lo riceve. Sugli scambi Lightning, se allo scadere chi compra non ha toccato «Ho inviato gli euro», lo scambio scade da solo, i sats tornano a chi vende e l'ordine torna nel libro uguale (alla presa dopo la garanzia si blocca di nuovo), anche se gli euro erano partiti: chi li aveva mandati senza toccare il bottone scrive subito all'assistenza, e chi vende, se gli euro arrivano lo stesso, li rimanda; se non vuole più l'ordine nel libro, lo apre e lo ritira. Conta come scambio non completato per chi compra, ma solo se chi vende aveva detto dove ricevere gli euro nella prima metà del tempo. Sugli scambi on-chain, dal 20 novembre 2026, è come sul Lightning: se allo scadere chi compra non ha toccato «Ho inviato gli euro», Barattolo firma da solo il ritorno dei sats a chi vende, chi vende mette la seconda firma con «✍️ Metti la seconda firma» (i sats sono nel deposito 2-di-3 e servono due firme), i sats tornano al suo indirizzo di ritorno e l'ordine torna nel libro, anche se gli euro erano partiti: chi li aveva mandati senza toccare il bottone scrive subito ai moderatori dalla pagina dello scambio. Non vale col tabacchino (Barattozon) e col contanti di persona: lì allo scadere arriva un avviso a tutti e due e chi vende può aprire una disputa. Se chi vende non ha scritto l'indirizzo di ritorno, resta la disputa finché non lo scrive. Chi pubblica una vendita Lightning col tempo per pagare corto, quando qualcuno la prende ha lo stesso tempo (al massimo) per bloccare i sats, al posto delle solite tre ore: se non li blocca in tempo l'ordine torna nel libro, e conta come scambio non completato (in arrivo: vale dal giorno in cui il servizio di scambio lo fa rispettare, e allora la pagina dello scambio dice «Chi ha pubblicato ha fino a 30 minuti per rispondere»). Sulle vendite on-chain (dal 19 novembre 2026) è uguale: chi pubblica col tempo per pagare corto, quando qualcuno prende l'ordine, ha lo stesso tempo (al massimo 6 ore) per INVIARE il deposito; basta che la transazione parta, la conferma della rete può arrivare dopo. Se in quel tempo non parte niente, lo scambio si annulla da solo, chi aveva preso riceve un avviso (e la cauzione, se c'era, gli torna) e l'ordine non torna nel libro. Il foglio del deposito lo dice: «⏱ Basta che il deposito parta entro le …».

<!-- pezzo libro-032 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (6/24)

Annullare uno scambio Lightning appena preso (quelli on-chain, con la ₿ arancio, hanno regole diverse: vedi più sotto): prima che i sats siano in garanzia NON serve aspettare. Chi ha preso l'ordine o chi l'ha pubblicato tocca «✕ Annulla» nella pagina dello scambio e poi «Sì, annulla»: lo scambio si annulla subito, senza il sì dell'altra persona, e nessuno perde niente. Se chi vende aveva già bloccato i sats (succede quando chi vende prende un ordine di acquisto), tornano subito a lui. Se annulla chi aveva preso, l'ordine torna subito nel libro, e chi l'aveva pubblicato riceve «Il tuo ordine è tornato in vetrina: non devi fare niente.». Se annulla chi l'aveva pubblicato, l'ordine si chiude: per rimetterlo nel libro va pubblicato di nuovo. Solo dopo, coi sats in garanzia, annullare da soli non si può più: serve l'annullo d'accordo, uno lo propone con «✕ Annulla» e l'altro accetta con «🤝 Accetta di annullare». Dopo «Ho inviato gli euro» il bottone «✕ Annulla» non c'è più: resta «⚠️ Apri una disputa». Se chi ha preso l'ordine ha toccato «✕ Annulla» ma l'annullo non è arrivato (la rete, la pagina chiusa a metà) e poi il tempo scade, il bot scrive «Non hai proseguito in tempo» con sotto «Avevi chiesto di annullare: questo non conta come scambio non completato.» (dal 17 novembre 2026): nessuna penalità.

Il paracadute degli ordini P2P: nel foglio «Pubblica», dopo la pausa, la sezione «🪂 Paracadute» ha due righe (dal 17 novembre 2026), «🟢 Se BTC sale» e «🔴 Se BTC scende», ognuna Nessuna, 5%, 10% o 20%. Se prima che qualcuno prenda l'ordine il prezzo di BTC si muove più di così in quel verso rispetto al momento della pubblicazione, l'ordine esce dal libro da solo, senza penalità, e il bot avvisa col tasto «🔁 Ripubblica al prezzo nuovo». Esempio: «sale: Nessuna» e «scende: 5%» tengono l'ordine se BTC sale e lo tolgono se scende più del 5%. Servono due letture di fila oltre la soglia, a un minuto l'una dall'altra. Di serie le due righe sono su «Nessuna», e il foglio non ricorda la scelta di prima. Sulla card del proprio ordine si legge «🪂 Paracadute ↑10% ↓5%» (freccia in su = salita, in giù = discesa). Gli ordini pubblicati prima del 17 novembre avevano una soglia sola, e vale nei due versi. Uno scambio già preso va avanti come sempre. Non c'è sugli ordini Barattozon in «Vendi BTC». Vale anche per gli ordini on-chain.

<!-- pezzo libro-033 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (7/24)

La pausa degli ordini P2P: chi pubblica può mettere in pausa i suoi ordini quando non c'è. Si imposta da «I miei scambi» col tasto «⏸ Pausa degli ordini», oppure nel foglio «Pubblica» al passo «3. Regole» con «⏸ Imposta la pausa». Due modi: una volta sola, fino a 7 giorni, o ricorrente, a giorni e orari fissi (per esempio tutte le notti dalle 22 alle 6). In pausa gli ordini restano nel libro, in grigio con «⏸ Puoi prenderlo tra…», e dentro Barattolo nessuno li può prendere; chi li ha pubblicati vede «⏸ In pausa fino alle …». Vale solo dentro Barattolo: le altre app che usano lo stesso coordinatore Mostro li vedono e li possono prendere lo stesso. Bozze degli ordini non ce ne sono: il foglio fa rileggere tutto al passo «4. Rileggi» prima di pubblicare, e chi vuole un ordine nel libro che ancora non si possa prendere imposta la pausa prima di pubblicarlo. Per togliere un ordine del tutto lo si annulla, e poi lo si ripubblica.

<!-- pezzo libro-034 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (8/24)

La ripubblica (dal 16 novembre 2026; semplificata il 20 novembre 2026): gli ordini nel libro durano una settimana, sia quelli Lightning sia quelli on-chain, e poi scadono se nessuno li ha presi. Nel foglio «Pubblica», al passo «3. Regole», sotto il paracadute, c'è la sezione «🔁 Ripubblica» con la domanda «Vuoi ripubblicarlo?» e due scelte, «No» (di serie, e il foglio riparte sempre da «No») e «Sì». Con «Sì», quando l'ordine scade senza che nessuno l'abbia preso, torna nel libro uguale: stessa cifra, a prezzo fisso gli stessi sats, a mercato lo stesso premio o sconto, stessi metodi, zona e paracadute. Succede a ogni scadenza. Il limite di prezzo lo fa il paracadute: se l'hai messo, l'ordine si ripubblica solo se BTC è ancora dentro le soglie misurate dal prezzo del giorno in cui l'hai pubblicato la prima volta, e quelle soglie non si spostano con le ripubblicazioni. Esempio: BTC a 100.000 € con paracadute 5% se sale e 5% se scende = fra 95.000 e 105.000 €, per sempre; se alla scadenza BTC è a 106.000 €, non si ripubblica. Con «se scende: Nessuna» in discesa non c'è limite. Senza paracadute, con «Sì» si ripubblica sempre, a qualunque prezzo. Il bot ti avvisa ogni volta, nel messaggio della scadenza: «Lo ripubblico uguale» oppure «Non l'ho ripubblicato: BTC è a…, oltre il tuo paracadute». Gli ordini Lightning li ripubblica il tuo telefono appena apri Barattolo (su qualunque pagina, senza fare niente): finché non lo apri l'ordine resta fuori dal libro. Gli ordini on-chain li ripubblica Barattolo subito, anche a telefono spento, per un'altra settimana. Per smettere: nella pagina del tuo ordine tocca «Non ripubblicarlo più». Sulla card del tuo ordine, che vedi solo tu, c'è la riga «🔁 Si ripubblica alla scadenza». Gli ordini pubblicati prima del 20 novembre con due prezzi «da… a…» vanno avanti come prima (card «🔁 Ripubblica fra… e…»). Non vale per Barattozon in «Vendi BTC» (il PayCode scade da solo); vale invece per Barattozon in «Compra BTC» e per gli ordini in ETH, Monero o USDe. Paracadute e ripubblica sono due cose diverse: il paracadute toglie l'ordine PRIMA, se BTC si muove troppo mentre aspetta nel libro; la ripubblica lo rimette DOPO, quando scade. Un ordine tolto dal paracadute non si ripubblica da solo: si rifà col tasto «🔁 Ripubblica al prezzo nuovo».

La disputa nel P2P: si apre solo coi sats già in garanzia, col bottone «⚠️ Apri una disputa» in fondo alla pagina dello scambio (nella scheda «📋 Passi»). Ferma lo scambio e chiama un moderatore, che potrà leggere la chat di quello scambio. Se è solo una domanda o un ritardo, prima scrivi all'altra persona nella chat. Chi vende può sempre liberare i sats anche a disputa aperta, e la disputa si chiude.

<!-- pezzo libro-035 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (9/24)

La chat dello scambio: da quando l'ordine è preso a quando lo scambio finisce c'è una chat fra voi due, cifrata, con foto e PDF (sul computer anche uno screenshot incollato con Ctrl+V: prima di mandarlo l'app chiede «Mandi l'immagine incollata?»). A fine scambio si cancella. Barattolo non ti scrive mai nella chat dello scambio: chi lì si presenta come «assistenza» è l'altra persona.

Contanti di persona (metodo «Contanti»): ci si incontra, chi compra sats porta le banconote, chi vende le conta e libera i sats lì, davanti all'altro. Le regole:
- i contanti si consegnano solo quando chi vende preme «Libera i sats» davanti a te, e si va via solo con lo scambio concluso;
- vedetevi in un posto pubblico e di giorno, contate insieme, mai grosse cifre da soli;
- chi vende fissa l'appuntamento (giorno, ora, luogo) dentro lo scambio;
- all'arrivo ognuno può toccare «📍 Sono qui»: registra ora e, se il telefono la dà, la posizione. È facoltativo ma aiuta nelle dispute;
- c'è un tetto in euro per scambio (vedi i NUMERI DI OGGI); sopra si divide in più ordini. Chi prende un ordine in contanti può dover bloccare una piccola cauzione.

Contante per posta (metodo «Contante per posta», dal 17 novembre 2026, sotto «Altri metodi ▾»): chi compra sats spedisce le banconote a chi li vende, in una busta di carta sigillata dentro una busta di plastica sigillata, nascoste in un pacco con altro dentro; chi vende dà nome e indirizzo dentro lo scambio, cifrati come un IBAN. Le regole, le stesse di Bisq: si spedisce solo a «Sats in garanzia», con un servizio tracciato (meglio quello di Poste Italiane per denaro e valori, da sportello: è l'unico che ammette il denaro e lo rimborsa, fino a 3.000 €; posta ordinaria e corrieri il denaro lo escludono dal rimborso); chi spedisce filma mentre chiude busta e pacco col numero di tracciamento in vista e scrive il numero nella chat dello scambio; chi riceve apre il pacco filmando, col tracciamento in vista, fino alle banconote contate, e poi libera. Chi prende un ordine scegliendo «Contante per posta» blocca la stessa piccola cauzione del contanti di persona. In disputa contano solo le prove: tracciamento consegnato e i due video. Mai scrivere «contanti» sulla busta. Vale anche in franchi svizzeri. Il metodo si accende con una leva: se sotto «Altri metodi ▾» non lo vedi, da voi non è ancora attivo, e non c'è niente da sbloccare.

<!-- pezzo libro-036 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (10/24)

Gli avvisi dei nuovi ordini P2P: nel libro P2P, la campanella 🔔 in alto apre «Avvisami dei nuovi ordini P2P». Acceso, il bot ti scrive quando nel libro arrivano ordini nuovi del tipo che scegli: «Compra BTC» (ordini di chi vende, dove compri tu), «Vendi BTC» (ordini di chi compra, dove vendi tu). Nel messaggio ogni ordine ha la sua riga, che comincia con «🟢 Compra BTC» o «🔴 Vendi BTC» dal tuo punto di vista, poi la cifra, i metodi e la convenienza; toccando «🟢 Compra BTC» o «🔴 Vendi BTC» di una riga si apre quell'ordine nel libro, come toccando la sua card, e se l'ordine nuovo è uno solo il tasto in fondo è «🫙 Apri l'ordine» (con più ordini resta «🫙 Apri il libro ordini»; dal 18 novembre 2026, anche per gli ordini on-chain). Sotto «Valuta» (la vede chi nel P2P ha anche altre valute oltre all'euro) puoi lasciare «Tutte» o accendere una o più valute insieme: «Euro», «Franchi», «USDT» e, dove ci sono, «Ethereum», «Monero» e «USDe»; ti arrivano solo gli ordini in quelle valute (dal 24 novembre 2026; prima se ne sceglieva una sola). Sotto «Metodo di pagamento» puoi lasciare «Tutti» o scegliere uno o più metodi (Barattozon, SEPA, Revolut, Satispay, Contanti...): ti arrivano solo gli ordini che ne accettano almeno uno (dal 18 novembre 2026). Barattozon sta fra i metodi dal 19 novembre 2026 (prima era un tipo a parte): per avere solo gli ordini Barattozon in cui compri tu bitcoin, scegli «Compra BTC» e il metodo «Barattozon»; per quelli in cui vendi, «Vendi BTC» e «Barattozon». Sotto «Convenienza» puoi lasciare «Tutti» oppure toccare «Con un limite» e scegliere fin dove ti va bene: «Fino a 10% peggio», «Fino a 5% peggio», «Fino a 2% peggio», «A prezzo di mercato o meglio», «Almeno 2% meglio», «Almeno 5% meglio». «Peggio» e «meglio» sono sempre dal tuo punto di vista, rispetto al prezzo di mercato: con «Fino a 5% peggio» ti avvisa di tutto tranne gli ordini che ti costerebbero più del 5% sopra il mercato (o che, se vendi, pagano più del 5% sotto). Lo stesso blocco sta nel Profilo, nel cassetto «🔔 Avvisi». Non ti avvisa mai dei tuoi ordini.

I post nei canali Telegram di Barattolo: quando un ordine P2P viene preso, annullato o scade, il suo post sparisce dal canale da solo (dal 18 novembre 2026). Se il post ha più di due giorni Telegram non lo lascia cancellare: allora resta, ma con scritto «Ordine P2P non più disponibile». Il post di un annuncio venduto del mercatino invece resta, con «✅ Venduto». I post di prima del 18 novembre restano com'erano.

<!-- pezzo libro-037 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (11/24)

La mappa del contanti: nel libro P2P, in alto accanto alla campanella, il tondo con la mappa colorata 🗺️ apre l'Italia coi pallini delle offerte in contanti di persona. Dal 16 novembre 2026 c'è sempre, sia in «Compra BTC» sia in «Vendi BTC»: se nel tab non ci sono offerte in contanti la mappa si apre vuota e lo dice. In fondo alla mappa c'è l'interruttore «Notifiche nuove offerte in contanti», spento di serie: acceso, sul tondo compare quante offerte in contanti nuove sono arrivate dall'ultima volta che hai aperto la mappa, e aprendola il numero sparisce. La scelta resta su quel telefono; si vede anche mentre scorri le card. Ogni pallino sta sul centro del comune dove la persona propone di vedersi, mai su un indirizzo. Si avvicina con due dita, con la rotellina o con un doppio tocco; toccando un comune l'elenco mostra solo le sue offerte e la pagina scende da sola fino a loro.

La mappa del ritiro a mano: nel mercatino, in fondo alla barra di ricerca, il tondo 🗺️ apre l'Italia coi pallini degli annunci che si possono ritirare di persona («🤝 Ritiro in zona», anche insieme alla spedizione). Ogni pallino sta sul centro del comune scritto nella «Zona» dell'annuncio, mai sull'indirizzo: il posto esatto si decide in chat. Con la mappa aperta sotto restano solo gli annunci col ritiro a mano; toccando un comune restano solo i suoi (la pagina scende da sola fino a loro), e la pillola «📍 Comune ✕» riporta a tutti. Si muove come quella del P2P: due dita, rotellina, doppio tocco, ＋ − ⟲. In fondo alla mappa l'interruttore «Notifiche nuovi annunci col ritiro a mano», spento di serie: acceso, sul tondo compare quanti annunci col ritiro sono arrivati dall'ultima volta che hai aperto la mappa. Per comparire sulla mappa basta scrivere il nome del comune nella «Zona» quando si vende.

Revolut: chi riceve gli euro su Revolut sceglie come, con tre bottoni nel modulo del recapito: RevTag (di serie), numero di telefono, oppure IBAN con l'intestatario.

Se chi vende chiede di annullare uno scambio coi sats già in garanzia, chi compra non è obbligato ad accettare: se ha già mandato gli euro o li vuole mandare, ha ancora «Ho inviato gli euro», e può aprire una disputa.

<!-- pezzo libro-038 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (12/24)

Barattozon (nel libro «Contanti al tabacchino»): chi vende sats fa un ordine Amazon da pagare in contanti nel punto vendita, e chi compra lo paga alla cassa di un tabacchino abilitato col PayCode. Il PayCode vale almeno 25 € e Amazon lo accetta fino a 999 €. Il PayCode arriva a chi compra solo quando i sats sono in garanzia (prima nella pagina non si vede), quindi si paga solo quando la pagina dice «Sats in garanzia»; si tiene lo scontrino come prova, e poi si tocca «Ho pagato al tabacchino». Chi vende controlla su Amazon che l'ordine risulti pagato e libera i sats. Alla cassa bisogna dire «devo pagare un ordine Amazon in contanti con un PayCode»: non una ricarica e non un buono regalo. L'arrotondamento: al tabacchino si paga sempre l'importo esatto del PayCode, coi centesimi. Negli scambi Lightning a prezzo di mercato, solo per calcolare i sats, l'importo si arrotonda per eccesso all'euro intero: con un PayCode da 47,30 € i sats si calcolano su 48 €. È a favore di chi paga al tabacchino, che riceve sempre almeno il valore di quel che paga; la differenza, meno di un euro, la mette sempre chi vende i sats, cioè chi ha il PayCode: in «Vendi BTC» chi ha pubblicato l'ordine, in «Compra BTC» chi l'ha preso. A prezzo fisso e negli scambi on-chain i sats si calcolano sui centesimi esatti. Barattozon c'è da tutti e due i lati del libro: anche chi COMPRA sats può pubblicare un ordine «al tabacchino», con una fascia di euro (per esempio da 30 a 80 €, il massimo è obbligatorio); chi vende lo prende scrivendo il PayCode (importo esatto, le nove cifre, la scadenza) e chi compra lo paga al tabacchino. Barattozon in «Vendi BTC» c'è anche on-chain (dal 17 novembre 2026): toccando Barattozon sotto il + esce prima la scelta «On-chain» o «Lightning», come per gli altri ordini (dal 20 novembre 2026), e nel foglio «Pubblica» si può ancora cambiare dall'interruttore in cima. Lì il PayCode deve scadere fra almeno 12 ore (il deposito si conferma in rete e poi bisogna andare al tabacchino), l'ordine esce dal libro da solo 8 ore prima della scadenza, e il PayCode lo custodisce Barattolo: chi prende lo vede solo quando i sats di chi vende sono confermati nel deposito a tre chiavi. La commissione di rete del deposito la paga chi vende. Con meno di 12 ore, meglio Lightning. Anche Barattozon in «Compra BTC» c'è on-chain (dal 17 novembre 2026, sera): chi compra pubblica la fascia a prezzo di mercato; chi prende scrive importo, PayCode e una scadenza fra almeno 8 ore, poi deposita i sats, e chi compra vede il PayCode solo a deposito confermato e lo paga al tabacchino.

Altre valute e reti (solo se nei NUMERI DI OGGI risultano disponibili): ordini P2P pagati in USDT al posto degli euro (qui sotto), ordini P2P in franchi svizzeri (CHF), ordini P2P in ETH, Monero o USDe, e scambi P2P coi bitcoin on-chain, con la garanzia a firme multiple (due chiavi su tre).

<!-- pezzo libro-039 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (13/24)

Ordini P2P in USDT (se nei NUMERI DI OGGI «Ordini P2P in USDT» è acceso): al posto degli euro si paga in USDT, il dollaro digitale di Tether (1 USDT vale 1 dollaro). I sats restano su Lightning con la garanzia di sempre (per gli USDT negli scambi on-chain vedi più sotto); gli USDT passano direttamente da una persona all'altra, e Barattolo non li tocca mai. Le reti sono solo due, Tron (TRC-20) ed Ethereum (ERC-20), mai altre: in un ordine in USDT le reti prendono il posto dei metodi di pagamento.
- Nel libro un ordine in USDT si riconosce dalla T verde di Tether nei quadratini in alto a destra della card.
- Nella home, accanto al titolo «Scambi P2P», c'è un interruttore (dal 24 novembre 2026): spento, le card degli scambi spariscono e restano solo il titolo e l'interruttore, che le riaccende con un tocco. È la stessa scelta di «🔁 Scambi P2P nella home» nel Profilo, e vale su ogni dispositivo. Sulle card della home il tempo per pagare e la cauzione sono solo due icone, ⏱ e 🔐, accanto alla moneta della rete; le parole («30 min», «Cauzione») si leggono sulle card del libro P2P.
- Nella home, nella fila «Scambi P2P», la card di un ordine in USDT è verde, con la moneta ₿ accanto alla T di Tether, e la cifra è scritta in USDT. Gli ordini in euro hanno la card di sempre, col ₿ e l'euro.
- Dal 16 novembre 2026 nella fila della home ci sono anche gli ordini on-chain (anche in USDe, ETH, Monero e franchi), mescolati con quelli Lightning, il più nuovo per primo. In fondo a ogni card, a destra, un piccolo simbolo dice la rete: il fulmine per Lightning, la ₿ arancio per on-chain. Toccando una card on-chain si apre il suo foglio. I propri ordini non compaiono nella propria home (si vedono nel libro e in «I miei scambi»), ma gli altri li vedono.
- In cima al libro c'è il rettangolo verde delle stablecoin, «USDT · USDe · Novità» (dal 16 novembre 2026 USDT e USDe stanno insieme; ETH e Monero hanno il loro rettangolo blu): toccandolo parte un breve tutorial che mostra come riconoscere un ordine in USDT, come pubblicarne uno e come si paga senza sbagliare rete. Si può rivedere toccandolo di nuovo.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta, euro o USDT. Con USDT si scelgono le reti (Tron, Ethereum o tutte e due) e l'importo si scrive in USDT. Il tetto della fase beta è lo stesso degli euro, convertito in USDT.
- Un ordine in USDT con un intervallo («da 50 a 276 USDT, scegli tu»): toccandolo, nel foglio «Quanto vuoi scambiare?» la cifra si scrive in USDT, e i sats si contano al cambio del dollaro (1 USDT = 1 $), non dell'euro. Per questo 276 USDT valgono meno sats di 276 €.

<!-- pezzo libro-040 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (14/24)

- Chi riceve gli USDT (cioè chi vende i sats) scrive nello scambio il suo indirizzo USDT, copiato dal suo wallet. L'app controlla che sia della rete giusta e ferma un indirizzo bitcoin, Lightning, Liquid o dell'altra rete, perché con la rete sbagliata gli USDT si perdono. Un limite da sapere: un indirizzo Ethereum (0x…) vale anche su reti che non offriamo (Polygon, BNB, Arbitrum…), quindi chi paga deve mandare proprio sulla rete scritta nello scambio.
- Chi paga vede la rete in grande, l'indirizzo col QR e il contratto del vero USDT, per non farsi ingannare da token falsi che si chiamano «USDT» anche loro. Sotto l'indirizzo c'è la riga «Da mandare» con la cifra esatta in USDT e il suo tasto «📋 Copia», come per l'indirizzo: copia solo il numero, col punto (per esempio 25.00), pronto da incollare nel wallet. Manda gli USDT, incolla l'id della transazione (lo trova nei dettagli dell'invio, nel wallet) e tocca «💵 Ho inviato gli USDT».
- Chi vende controlla che siano arrivati sulla rete giusta, anche col tasto «🔎 Controlla su Tronscan» (o Etherscan) sotto l'id, e libera i sats solo quando ci sono davvero. Se qualcosa non torna si apre una disputa: il moderatore legge l'id della transazione sulla rete giusta.

Ordini P2P in franchi svizzeri (se nei NUMERI DI OGGI «Scambi P2P pagati in franchi svizzeri (CHF)» è disponibile): al posto degli euro l'ordine è in franchi svizzeri, CHF. I sats restano su Lightning con la garanzia di sempre; i franchi passano direttamente da una persona all'altra, e Barattolo non li tocca mai.
- Nel libro un ordine in franchi si riconosce dalla croce bianca su fondo rosso nei quadratini in alto a destra della card; nella home la sua card è rossa, col ₿ accanto al franco, e la cifra è scritta in CHF.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta CHF. I metodi sono TWINT, bonifico svizzero («Bonifico CH»), Revolut, Wise e contanti di persona; TWINT e il bonifico svizzero esistono solo negli ordini in franchi. Il tetto della fase beta è lo stesso degli euro, convertito in franchi al cambio del momento, e vale anche per i contanti di persona. Barattozon non è in franchi; gli scambi on-chain sì (dal 16 novembre 2026): i bitcoin restano nel deposito a tre chiavi, chi compra paga in franchi.
- Chi riceve i franchi scrive nello scambio dove riceverli: per TWINT il numero di cellulare svizzero (+41 7…), per il bonifico svizzero intestatario e IBAN svizzero (comincia con CH o LI, 21 caratteri). L'app controlla il numero e l'IBAN prima che partano, e ferma un numero non svizzero o un IBAN con una cifra sbagliata.
- Chi paga manda i franchi e tocca «Ho inviato i franchi»; chi vende controlla di averli ricevuti e libera i sats.

<!-- pezzo libro-041 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (15/24)

Ordini P2P in ETH, Monero o USDe (se nei NUMERI DI OGGI «Scambi P2P pagati in ETH, Monero (XMR) o USDe» è disponibile): sono tre valute a sé, come l'euro, l'USDT e i franchi. Con ognuna si comprano o si vendono sats, che restano su Lightning con la garanzia di sempre; la moneta passa direttamente da una persona all'altra, e Barattolo non la tocca mai. ETH è Ethereum, XMR è Monero, USDe è il dollaro digitale di Ethena.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta: EUR, USDT, ETH, XMR o USDe. Sotto compare solo la sua lista: con ETH «ETH (Ethereum)», con XMR «XMR (Monero)», con USDe le sue cinque reti, «USDe (Ethereum)», «USDe (Arbitrum)», «USDe (Base)», «USDe (BNB Chain)» e «USDe (Solana)», una o più. Con l'euro restano solo i metodi classici (bonifico, Revolut, contanti…).
- L'importo si scrive nella moneta (per esempio 0,02 ETH o 50 USDe), ed è uno solo, senza una fascia «da… a…». Dal 16 novembre 2026 funziona come in euro: a prezzo di mercato la cifra in moneta resta quella, e i sats si fanno quando qualcuno prende l'ordine, al cambio di quel momento e col premio o lo sconto scelto. Il cambio della moneta conta al mezzo euro. Se il cambio si sposta di oltre il 5% da quando l'ordine è stato pubblicato, chi l'ha pubblicato lo vede scritto nella pagina dell'ordine; se si sposta troppo (circa il 30%) l'ordine non si può più prendere e conviene rifarlo. Si può anche scrivere un prezzo fisso in sats: allora i sats non cambiano più. Per ordini molto piccoli o vicini al tetto può succedere che il mercato non ci stia: allora i sats si fissano quando si pubblica, come prima.
- Nel libro ogni valuta ha il suo filtro in cima (EUR, USDT, ETH, XMR, USDe), e la card mostra il logo della moneta nei quadratini in alto a destra e la cifra nella moneta, per esempio «Invia 0,0153 ETH».
- Le monete del P2P servono solo a PAGARE: ogni scambio ha sempre bitcoin da una parte, e da Barattolo non si comprano USDT, ETH, XMR o USDe con gli euro. Chi ha ETH e vuole bitcoin prende un ordine di chi vende sats e paga in ETH, come pagherebbe con un bonifico; chi riceve USDT li riceve in cambio dei suoi bitcoin.
- «No altcoin» e «No stablecoin» (se nei NUMERI DI OGGI «Pillole «No altcoin» e «No stablecoin» nel Filtro del P2P» è acceso, dal 18 novembre 2026): nel Filtro del libro P2P, in fondo alle «Valute», ci sono due pillole. «No altcoin» toglie gli scambi pagati in ETH e XMR (il loro rettangolo «Novità» e le loro card nella fila della home), e il banner di «I miei scambi» torna quello con le sole monete bitcoin ed euro; USDT e USDe restano. «No stablecoin» toglie gli scambi in USDT e USDe (e il loro «Novità»). Accese tutte e due, restano solo euro e franchi. Si applicano con «Applica»; di serie sono spente, il telefono si ricorda la scelta (vale su quel dispositivo) e «Azzera» le spegne come le altre.

<!-- pezzo libro-042 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (16/24)

- Il Filtro del libro P2P si ricorda (dal 19 novembre 2026): valute, metodi, premio, reputazione e Lightning/on-chain scelti con «Applica» restano anche uscendo e rientrando, sia nella Mini App sia sul sito. Vale su quel telefono o browser (un altro dispositivo non lo sa); «Azzera» li toglie anche dalla memoria. Se il libro sembra vuoto, spesso è un filtro rimasto acceso: la pillola «Filtro» colorata lo dice.
- Chi riceve scrive nello scambio il suo indirizzo, copiato dal wallet. L'app controlla che sia della moneta e della rete giusta e ferma un indirizzo sbagliato o con un refuso. Un limite da sapere: Ethereum, Arbitrum, Base e BNB Chain hanno indirizzi uguali (0x…), quindi chi paga deve mandare proprio sulla rete scritta nello scambio. Per USDe lo scambio mostra anche il contratto del vero USDe, contro i token falsi con lo stesso nome.
- Chi paga vede l'indirizzo col QR e la cifra esatta da mandare, che è quella dell'ordine. Manda, incolla l'id della transazione e tocca «Ho inviato». Con Monero serve anche la chiave della transazione (tx key), che il wallet di chi manda conserva: Monero è privato, e solo con id, chiave e indirizzo si vede quanto è arrivato.
- Chi vende controlla l'arrivo col tasto «🔎 Controlla su …» (Etherscan, xmrchain, Arbiscan, Basescan, BscScan o Solscan) e libera i sats solo quando ci sono davvero. Se qualcosa non torna si apre una disputa.
- Dal 16 novembre 2026 ETH, Monero e USDe ci sono anche negli scambi on-chain (a tre chiavi): i bitcoin restano nel deposito, chi compra paga nella moneta. Lì si sceglie una rete sola, e chi paga vede rete, cifra da copiare e QR (l'id della transazione: vedi più sotto).
- In cima al libro (dal 16 novembre 2026) ci sono tre rettangoli «Novità»: quello arancio «On-Chain», quello verde delle stablecoin «USDT · USDe» (dice solo quel che c'è) e quello blu «ETH · XMR». Ognuno apre il suo breve tutorial: il verde mostra un ordine in USDe col bollino della rete, il foglio e le reti; il blu mostra le due monete, il foglio in ETH e il prezzo di mercato. Si possono rivedere toccandoli di nuovo. Scorrendo il libro verso il basso i tre diventano un rettangolo solo, con le icone di tutte le monete e la scritta «Novità», che resta in alto; scorrendo verso l'alto (o toccandolo) tornano subito i tre.
- I rettangoli «Novità» durano 45 giorni dal giorno in cui la cosa è arrivata a tutti, poi spariscono da soli (regola del 19 novembre 2026, vale anche per quelli futuri): quello degli USDT fino al 26 dicembre 2026, quelli on-chain, ETH, Monero e USDe fino al 30 dicembre 2026. Dal 27 dicembre il verde dice solo «USDe». Le funzioni restano tutte: sparisce solo il rettangolo col suo tutorial.
- Nel foglio «Pubblica», scelta una rete sola di USDT o USDe, l'icona della valuta porta in alto a destra il bollino della rete, come nella card del libro.

<!-- pezzo libro-043 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (17/24)

Scambi P2P on-chain (se nei NUMERI DI OGGI «Scambi P2P in bitcoin on-chain» è disponibile): si scambiano bitcoin sulla rete principale, non su Lightning. La garanzia non è quella di Lightning: chi vende blocca i bitcoin in un deposito a tre chiavi, una sua, una di chi compra e una di Barattolo, e per spostarli ne servono due. Barattolo da solo non li può muovere: la sua chiave firma sempre insieme a una delle due parti, e solo in due casi: una disputa decisa da un moderatore, o il tempo per pagare finito senza «Ho inviato» (allora firma da sola il ritorno a chi vende). Anche per il P2P on-chain non dire mai che Barattolo «fa da garante» o «tiene i sats»: i bitcoin stanno nell'indirizzo a tre chiavi, non da Barattolo.
- Nel libro uno scambio on-chain si riconosce dalla moneta arancio ₿ (quelli di Lightning hanno il fulmine). Sopra le card c'è il rettangolo arancio «On-Chain» con la scritta «Novità», che apre la pagina «Scambi on-chain»: lì si pubblica («Pubblica uno scambio on-chain») e si seguono i propri.
- Per pubblicare si può anche toccare il + di «Compra BTC» o «Vendi BTC» e scegliere «On-chain» invece di «Lightning». Serve aver preparato Profilo → «₿ On-chain» (le 12 parole e la loro copia: vedi «Bitcoin on-chain»). Un ordine resta nel libro 7 giorni (dal 16 novembre 2026; prima 24 ore); il tetto per ordine è quello on-chain dei NUMERI DI OGGI e del paragrafo sui limiti.
- Il giro, passo per passo: chi prende fa nascere l'indirizzo a tre chiavi. Chi vende ha 6 ore per depositare con «🔒 Blocca i sats»: i sats dello scambio più un piccolo margine per la commissione della rete, più la sua metà della commissione del P2P. Appena la rete vede il deposito, prima ancora della conferma, il bot lo dice a tutti e due: chi ha depositato non deve depositare di nuovo, chi compra non deve ancora mandare niente. Con una conferma della rete (circa dieci minuti) lo scambio va avanti, e tutti e due ricevono l'avviso. Chi vende scrive nello scambio dove vuole gli euro (il tasto «💶 Indica dove ricevere gli euro» porta al campo, poi «Salva»): solo allora chi compra manda gli euro col metodo scritto e tocca «💶 Ho inviato gli euro», come nel Lightning. Chi vende li controlla sul suo conto e SOLO quando li vede tocca «🔓 Ricevuti: libera i sats», che compare dopo «Ho inviato» (dal 19 novembre 2026; prima c'era già a deposito confermato); la seconda firma la mette da solo il telefono di chi compra, e i bitcoin partono.
- Chi compra deve dire dove ricevere: nello scambio c'è «Dove ricevi i bitcoin?», si incolla un proprio indirizzo e si tocca «✍️ Firma e usa questo indirizzo». Chi ha messo nel Profilo la chiave del conto del suo wallet non deve scriverlo ogni volta: ogni scambio arriva a un indirizzo nuovo.

<!-- pezzo libro-044 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (18/24)

- Finché nessun sats è arrivato nel deposito, chi compra può annullare quando vuole con «✕ Annulla» (dal 17 novembre 2026; prima solo a tempo del deposito finito, e allora il tasto si chiama «Rinuncia: il deposito non è arrivato»); chi deve depositare e non ha ancora mandato niente può annullare («Annulla (non deposito)»). Con i sats già nel deposito non si annulla da soli: si esce col rimborso d'accordo o con «⚖️ Apri una disputa». Due eccezioni per un deposito incompleto (dal 18 novembre 2026). Se mancano pochi sats, tipicamente le commissioni di uno swap, lo scambio va avanti lo stesso: li copre il margine per la rete che chi vende ha già messo, fino a metà del margine, e il bot glielo dice («Sono arrivati N sats in meno»). Se ne mancano di più, la pagina dice «ne mancano N perché il deposito valga» e chi ha depositato, dopo la prima conferma, può toccare «↩️ Annulla e riprendi i sats»: lo scambio si chiude, Barattolo firma il rimborso verso il suo wallet e il suo telefono mette la seconda firma. Chi ha depositato può anche chiedere a chi compra di annullare con «🙏 Chiedi a chi compra di annullare» (dal 18 novembre 2026, solo prima che chi compra dica di aver pagato): il bot gli scrive, e se è d'accordo tocca «Rinuncio»: in quel caso a chi rinuncia non si conta nessuno «scambio non completato» e nessuna cauzione si perde, perché fa un favore. Se hai già mandato i soldi non rinunciare: tocca «Ho inviato» o scrivi nella chat. I sats non tornano mai all'indirizzo da cui sono partiti (per esempio la piattaforma di swap): vanno al wallet del Profilo o all'indirizzo scritto nel riquadro «Dove tornano i sats?». Decide un moderatore di Barattolo, Barattolo mette la sua firma e la seconda la mette il telefono di chi ha ragione. Uno scambio on-chain annullato si chiude: a differenza di Lightning non torna nel libro, chi l'aveva pubblicato lo ripubblica.
- Dove tornano i sats (dal 17 novembre 2026): chi vende bitcoin on-chain e non ha scelto un wallet nel Profilo trova, nel foglio «🔒 Blocca i sats» prima del codice QR, il riquadro «Dove tornano i sats?»: incolla un indirizzo del suo wallet Bitcoin e tocca «✍️ Firma e usa questo indirizzo». Vale per quello scambio: lì tornano i sats se lo scambio si annulla, e il resto quando li libera. Se ha già depositato, lo stesso riquadro è nella pagina dello scambio. Non è il riquadro «Dove vuoi gli euro», che è il recapito per farsi pagare: lì un indirizzo bitcoin non serve. Chi ha scelto il wallet nel Profilo (Profilo, «₿ On-chain», «Dove ricevi i bitcoin») non deve scrivere niente.

<!-- pezzo libro-045 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (19/24)

- Quando chi compra non ha ancora scelto dove ricevere (scambi on-chain, dal 17 novembre 2026): chi vende che tocca «Ricevuti: libera i sats» prima che chi compra abbia indicato il suo wallet legge «⏳ Chi compra non ha scelto dove ricevere» e può toccare «🔔 Ricordaglielo» (c'è anche nella pagina dello scambio): il bot scrive a chi compra di incollare un indirizzo nel riquadro «Dove ricevi i bitcoin?». Si può ricordare una volta all'ora. Quando chi compra sceglie dove ricevere, nello scambio o nel Profilo, il bot lo dice a chi vende con «📍 Chi compra ha scelto dove ricevere», e da lì «Ricevuti» manda i sats a quell'indirizzo. Fino ad allora i sats restano al sicuro nel deposito a tre chiavi.
- Rinunciare coi sats già nel deposito (dal 17 novembre 2026): chi compra tocca «↩️ Rinuncio: rimborsa chi vende». Se chi vende non ha ancora scritto dove riavere i sats, non è un errore: la rinuncia viene registrata, la pagina dice «Hai chiesto di rinunciare» e il bot avvisa chi vende («Chi compra vuole rinunciare») col tasto che apre lo scambio. Appena chi vende scrive l'indirizzo, a chi compra arriva «Ora puoi rinunciare» e tocca di nuovo «Rinuncio». Poi il telefono di chi vende mette la seconda firma quando apre l'app, e i sats tornano a lui meno la commissione di rete. Un moderatore non può saltare questo passaggio: senza l'indirizzo di chi vende il rimborso non ha dove andare, e i sats restano al sicuro nel deposito.

<!-- pezzo libro-046 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (20/24)

- Il contanti di persona negli scambi on-chain (dal 17 novembre 2026): come nel Lightning, chi pubblica un ordine on-chain con «Contanti» scrive la zona di scambio (una città o una zona, mai un indirizzo), la card la mostra con «📍», e vale lo stesso tetto in euro per scambio (vedi i NUMERI DI OGGI). Gli ordini on-chain in contanti pubblicati prima non hanno la zona. Lo scambio on-chain in contanti (quando «Contanti» è l'unico metodo dell'ordine) va come quello Lightning: chi vende scrive nello scambio «📍 Dove vedervi» (luogo, giorno e ora; chi compra ha «🧭 Apri nel navigatore» se l'indirizzo è stato riconosciuto), quando i sats sono nel deposito di garanzia ognuno può segnare «📍 Sono qui» dal suo telefono (facoltativo: registra l'ora e, se il telefono la dà, la posizione; l'altra persona vede solo l'ora, mai la posizione), chi compra consegna i contanti e tocca «💵 Ho consegnato i contanti», chi vende li conta e tocca «Ricevuti: libera i sats» lì davanti. In disputa un moderatore guarda le presenze, con la stessa regola del Lightning. Su un ordine on-chain con «Contanti» insieme ad altri metodi, chi prende sceglie il metodo nel foglio dell'ordine prima di toccare «Compra» o «Vendi»: scegliendo «Contanti» lo scambio va in contanti di persona, scegliendo un metodo online va come un bonifico; il metodo scelto resta fissato. La cauzione negli scambi on-chain in contanti non è ancora attiva: è in prova, e quando arriverà si bloccherà in Lightning con un QR e tornerà a fine scambio. Quando sarà attiva, chi vende in un ordine on-chain («Vendi BTC») potrà anche chiederla a chiunque lo prenda, con qualunque metodo (nel foglio «Pubblica», voce «Cauzione di chi prende»; sulla card del libro e su quella «Scambi P2P» della home il bollino «🔐 Cauzione»): serve a chi deposita i bitcoin, che se lo scambio salta paga due volte la commissione di rete, per il deposito e per il ritorno. Quando la cauzione torna, il bot lo dice a chi l'aveva bloccata («🔐 La cauzione è tornata nel tuo wallet», coi sats; dal 19 novembre 2026). Il foglio di «↩️ Rinuncio» dice prima se e quanta cauzione si perde (dal 19 novembre 2026). Dopo «Rinuncio» chi vende vede solo «✍️ Metti la seconda firma»: la tocca e i sats tornano a lui. Questa cauzione chi prende la perde da sola, senza moderatore, se rinuncia dopo che i bitcoin sono nel deposito o se lascia scadere il tempo per pagare senza toccare «Ho inviato» (non se chi vende non aveva scritto dove pagare, e non se l'annullo l'aveva chiesto chi vende); metà va a chi vende e parte da sola verso il suo indirizzo Lightning del Profilo (dal 19 novembre 2026; se non ce l'ha, il bot gli chiede di scriverlo e la metà arriva appena lo salva). Quanto vale: il 3% dei sats dello scambio, almeno 1.000 sats e, dal 22 novembre 2026, al massimo 50.000 sats; la cifra esatta la vedi nel foglio prima di prendere.

<!-- pezzo libro-047 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (21/24)

- L'ordine on-chain che torna nel libro (dal 19 novembre 2026): quando uno scambio on-chain salta per colpa di chi l'ha preso (annulla prima del deposito, non deposita nel suo tempo di 6 ore, rinuncia dopo il deposito, o non paga e un moderatore rimanda i sats a chi vende), l'ordine di chi l'aveva pubblicato rinasce nel libro uguale: stesso prezzo, stessi metodi, stesso tempo per pagare, con un nome nuovo. Lo scambio vecchio resta chiuso com'era, con la sua chat. Il bot avvisa chi aveva pubblicato con «🔁 Il tuo ordine è tornato nel libro» e il tasto «🚫 Non ripubblicarlo», che apre l'ordine nuovo: lì lo si ritira con un tocco. Alla presa dopo chi mette i bitcoin deposita di nuovo e paga di nuovo la commissione di rete (il deposito 2-di-3 vecchio conteneva la chiave dell'altra persona). Per Barattozon in «Vendi BTC» torna solo se chi l'ha preso annulla prima del deposito e al PayCode mancano più di 8 ore; per Barattozon in «Compra BTC» non vale.
- Ritirarsi dopo che l'altro ha bloccato i sats (scambi on-chain, dal 17 novembre 2026): non c'è nessuna cauzione e nessuna penale in denaro. Però a chi compra bitcoin e rinuncia a deposito già confermato, quando chi vende aveva già scritto dove pagare, viene contato uno «scambio non completato», come nel Lightning: il primo è tollerato, con un secondo nello stesso mese non si prendono gli ordini con filtro (1+, 3+, 5+) per 30 giorni, e da due in 90 giorni compare sul profilo. Il foglio di «↩️ Rinuncio» lo dice prima della firma. In più chi aveva bloccato i sats può lasciargli una recensione dalla pagina dello scambio (solo lui: chi si è ritirato no). Lo stesso «non completato» vale per chi lascia finire il tempo per pagare senza toccare «Ho inviato» e poi un moderatore, in disputa, rimanda i sats a chi vende. Non conta mai se chi vende non aveva scritto dove pagare, né prima del deposito confermato (lì c'è «✕ Annulla»).
- Se serve la chiave del wallet (dal 17 novembre 2026): succede a chi firma uno scambio on-chain da un dispositivo diverso da quello su cui è nato il suo wallet. Barattolo prima la cerca da solo (nel cloud di Telegram o sui relay Nostr); se non la trova apre il foglio «🔑 Serve la chiave del tuo wallet», dove si incollano le 12 parole: il foglio dice dove riprenderle (dal 19 novembre 2026: nel cloud di Telegram, nel browser del sito dove il wallet è nato, o sui relay Nostr); si leggono là in Profilo, «₿ On-chain», «Mostra le 12 parole». A Barattolo non arrivano, e il gesto riparte da solo.
- La commissione (dal 16 novembre 2026) è quella degli scambi Lightning, metà a testa e con gli stessi sconti: chi vende deposita la sua metà insieme ai sats, chi compra riceve i sats meno la sua metà. Nel conto dello scambio, e già nel foglio prima di prendere, c'è la riga «Fee P2P» con la percentuale, come negli scambi Lightning. Se lo scambio finisce col rimborso a chi vende, torna tutto, commissione compresa. Sotto i 546 sats di commissione in tutto non si paga niente.

<!-- pezzo libro-048 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (22/24)

- Il tempo per pagare (dal 17 novembre 2026): dal deposito confermato chi compra ha 24 ore per pagare, in USDT, ETH, Monero o USDe come in euro e franchi (per euro e franchi all'inizio erano 72 ore: non più). Col PayCode di Barattozon il tempo è la scadenza del PayCode. La card in «I miei scambi» dice quanto resta («Hai ancora 23 h 10 min») e ha la barra del tempo sul bordo di sotto; la pagina dello scambio ha la riga «Tempo per pagare» col conto che scorre. Alla scadenza senza «Ho inviato» (dal 20 novembre 2026) Barattolo firma da solo il rimborso verso l'indirizzo di ritorno di chi ha messo i bitcoin nel deposito, senza moderatore; lui mette la seconda firma con «✍️ Metti la seconda firma», i bitcoin tornano al suo indirizzo e l'ordine torna nel libro; a chi non ha pagato conta uno «scambio non completato», e la cauzione, se chi vende l'aveva chiesta, si perde come sul Lightning. Col PayCode di Barattozon e col contanti di persona non succede da solo: il bot avvisa tutti e due, e chi vende, se i soldi non sono arrivati, può aprire una disputa. Dopo «Ho inviato» non torna niente da solo: resta la disputa. Per questo chi compra deve toccare «Ho inviato gli euro» appena ha pagato. La disputa si può aprire anche prima. Dal 19 novembre 2026 il tempo parte quando c'è anche il recapito (dove vuole gli euro chi vende), non prima.
- Il tempo del bonifico (scambi on-chain in euro o franchi): da quando chi compra tocca «Ho inviato», chi vende ha 48 ore per veder arrivare il bonifico e liberare i sats. La pagina dello scambio dice fino a quando. Passate le 48 ore senza che abbia liberato, il bot avvisa tutti e due: chi vende libera se gli euro ci sono, altrimenti apre una disputa; chi compra apre una disputa con «⚖️ Apri una disputa» e tiene pronta la ricevuta. Niente si annulla e niente si libera da solo: i bitcoin restano nel deposito finché una delle due parti non fa il suo gesto o decide un moderatore. Non vale per USDT e monete (arrivano in minuti), per il PayCode e per i contanti di persona.
- Chi è l'altra persona (dal 17 novembre 2026): nella pagina dello scambio on-chain, appena l'ordine è preso, c'è il riquadro con la faccia, il nome e le stelline dell'altra persona, come negli scambi Lightning; toccando la faccia si apre il suo negozio, e i tondi accanto (Telegram, Nostr) servono a scriverle, se li ha. Per scriversi c'è anche la chat dello scambio. Il riquadro e la chat stanno nella scheda «💬 Chat».
- I promemoria dello scambio on-chain (dal 17 novembre 2026), come nel Lightning: il bot ricorda a chi compra di pagare dopo un'ora, dopo sei ore, quattro ore prima della fine del suo tempo e poi a dieci e a cinque minuti dalla fine (solo se chi vende ha già scritto dove ricevere i soldi, e mai con i contanti di persona); e ricorda a chi vende di controllare e liberare i sats un'ora, sei ore e venti ore dopo «Ho inviato». Con una disputa aperta i promemoria si fermano.

<!-- pezzo libro-049 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (23/24)

- Negli scambi on-chain pagati in ETH, Monero o USDe (dal 17 novembre 2026), come per gli USDT: prima di «Ho inviato» si incolla l'id della transazione (con Monero anche la chiave della transazione, la «tx key»). Lo vedono chi vende e, in una disputa, il moderatore, col tasto per controllarlo sull'explorer.
- La chat negli scambi on-chain (dal 17 novembre 2026), come nel Lightning: da quando l'ordine è preso a quando i sats vengono liberati o rimborsati c'è una chat fra voi due, cifrata, con foto e PDF, nella scheda «💬 Chat» della pagina dello scambio (prima del 20 novembre 2026 stava in fondo alla pagina). Quando l'altra persona ti scrive, il bot dice «Hai un nuovo messaggio nello scambio on-chain» (mai il testo) e il bottone «🟠 Apri lo scambio» porta dritto alla chat. Se l'altra persona non ha ancora aperto Barattolo, al posto del campo c'è «🔔 Avvisa». In una disputa il moderatore la legge; a scambio finito si cancella.
- A fine scambio la pagina dice «Concluso: i sats sono andati al wallet di chi ha comprato» oppure «Rimborsato: i sats sono tornati a chi li aveva depositati». Il messaggio del bot a chi compra dice i sats netti, cioè già tolta la sua metà della commissione, come la card.
- La recensione (dal 17 novembre 2026): a scambio on-chain concluso, nella pagina dello scambio c'è «⭐ Lascia una recensione», come negli scambi Lightning: stelle e commento vanno sul profilo dell'altra persona, nella stessa media del mercatino, e si possono modificare una volta o cancellare per qualche giorno. C'è anche quando una disputa l'ha decisa un moderatore; non c'è dopo un rimborso d'accordo. Il messaggio del bot «Scambio on-chain concluso!» lo ricorda. Gli scambi on-chain conclusi contano anche nel numero «✅ N scambi P2P» accanto alle stelline (dopo una disputa conta solo per chi ha ricevuto i bitcoin).
- La barra del tempo sotto un ordine on-chain del libro conta i suoi 7 giorni come quella degli ordini Lightning: arancio negli ultimi tre giorni, rossa l'ultimo. Nel foglio di chi prende un ordine on-chain c'è la riga «Tempo rimasto» col conto e la barra, come nella pagina di un ordine Lightning: dal 16 novembre 2026 è una riga sola, non più l'anello rotondo.
- USDT negli scambi on-chain (se nei NUMERI DI OGGI «Scambi P2P on-chain pagati in USDT» è disponibile): la garanzia resta il deposito bitcoin a tre chiavi, e al posto degli euro chi compra paga in USDT su Tron o Ethereum, da persona a persona, con le stesse regole degli ordini in USDT qui sopra: chi vende scrive il suo indirizzo USDT, chi paga incolla l'id della transazione e tocca «Ho inviato gli USDT». Un ordine è in una valuta sola: o euro o USDT.

<!-- pezzo libro-050 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (24/24)

Ricevere o pagare su un'altra rete (se nei NUMERI DI OGGI «P2P su un'altra rete» è disponibile): la rete di un ordine dice come paga chi l'ha pubblicato, ma chi lo prende può usare l'altra, con uno swap di SATS Routing fatto dal suo telefono (come la pagina «Swap»). Il costo dello swap si vede prima di confermare, e Barattolo non aggiunge commissioni.
- La scelta si fa già nel foglio che si apre toccando l'ordine (dal 16 novembre 2026): sotto «Stai comprando sats» / «Stai vendendo sats» ci sono i due tasti «⚡ Lightning» e «₿ On-chain», già accesi sulla rete dell'ordine. Toccando l'altra rete compare subito quanto costa lo swap di SATS Routing e quanto arriva (o quanto si paga), e nel dettaglio sotto ci sono due righe che il totale conta: «Swap SATS Routing 0,6%» (la commissione del servizio) e «Rete dello swap» (le transazioni sulla rete bitcoin), così si vede che lo swap non è la commissione del P2P anche quando le due cifre si somigliano; la scelta resta, e dopo aver preso il foglio giusto si apre già su quella rete. I tasti ci sono solo dove l'altra rete si può davvero usare.
- Ordine Lightning, ma vuoi ricevere bitcoin on-chain: nel foglio «Dove ricevere i sats» scegli «₿ On-chain», incolli un tuo indirizzo bitcoin e l'app ti dice quanti sats ti arrivano circa e quanto costa lo swap. Alla liberazione i sats diventano bitcoin al tuo indirizzo. Se il moderatore dà ragione a chi vende, lo swap scade senza costare niente.
- Scambio on-chain, ma vuoi ricevere in Lightning: nello scambio tocchi «⚡ Ricevi in Lightning» e, quando chi vende ha confermato gli euro, incolli una tua richiesta Lightning (o «⚡ Prendila dal mio Lightning address») e tocchi «✅ Conferma lo swap». Ti arriva il prezzo meno il costo dello swap; se la richiesta non si riesce a pagare, i bitcoin tornano da soli al tuo wallet on-chain di Barattolo. Si torna indietro con «₿ Ricevi on-chain invece».
- Scambio on-chain che hai preso tu per vendere, ma hai solo sats Lightning: nel foglio «🔒 Blocca i sats» scegli «⚡ Lightning» e tocchi «⚡ Crea la richiesta Lightning»; la paghi col tuo wallet e lo swap mette i bitcoin nel deposito a tre chiavi. Un annullo o un rimborso tornano però on-chain, al tuo wallet di Barattolo.
- Lo swap ha i suoi limiti di cifra (quelli di SATS Routing): fuori dai limiti l'app lo dice e lo scambio si fa sulla rete dell'ordine.

<!-- pezzo libro-051 | libro -->
## Libro · Bitcoin on-chain (1/3)

Oltre a Lightning, alcune funzioni usano i bitcoin «on-chain», cioè sulla rete principale di Bitcoin: la moneta arancione ₿ le indica in tutta l'app. Quali sono accese, e per chi, lo dicono i NUMERI DI OGGI: una funzione spenta lì non c'è.

- Pagare un ordine on-chain: chi compra manda i bitcoin a un indirizzo e l'ordine nasce alla prima conferma della rete. Appena la rete vede i sats la pagina del pagamento si chiude da sola, e in «Ordini» l'ordine dice «⏳ Visto in rete, aspetto la conferma» (etichetta «In arrivo»): non c'è altro da fare, si aspetta la conferma, circa dieci minuti. Se è arrivata solo una parte, la pagina resta aperta e dice quanti sats mancano. Appena il pagamento si vede in rete, chi vende riceve «Pagamento in arrivo»: l'oggetto è prenotato, ma non si spedisce finché non arriva l'avviso vero, alla conferma.
- Gli acquisti grossi (dal 17 novembre 2026): sopra 500 € la cassa del mercatino propone da sola l'on-chain. E chi vende riceve on-chain anche se per quell'oggetto aveva scelto Lightning: l'ordine glielo scrive («Cifra grossa: ricevi on-chain»), e i sats partono quando ha scelto dove riceverli in Profilo → «₿ On-chain». Nel foglio «Come vuoi pagare?» On-chain porta «✅ Consigliato per questa cifra», e se si sceglie Lightning la fattura avvisa «Sopra 500 € il Lightning spesso non passa». Il motivo: con cifre così i wallet Lightning e i canali spesso non reggono, e il pagamento fallisce. Dal 22 novembre 2026, sopra 500 € un oggetto si paga SOLO on-chain: il Lightning nel foglio è spento e dice «Sopra 500 € si paga solo on-chain.»; chi pubblica sopra 500 € trova in «Come vuoi ricevere per questo oggetto?» solo On-chain, con «Sopra 500 € si riceve solo on-chain.», e sull'annuncio la scritta «Preferisce ricevere on-chain». Non serve mettere un indirizzo prima: i sats restano nel deposito di garanzia finché chi vende non sceglie dove riceverli. L'on-chain vale per un oggetto solo, senza offerta accettata né codice sconto: nel carrello, con un'offerta o un codice sconto (o se chi vende l'on-chain non ce l'ha ancora) resta il Lightning, con l'avviso.
- La quota fissa a Barattolo: negli acquisti on-chain del mercatino il conto può avere la riga «Quota fissa a Barattolo (spese di rete)». La paga chi compra, si vede prima di pagare, va a Barattolo quando i sats vengono liberati e col rimborso torna indietro. Quanto vale oggi (o se non c'è) lo dicono i NUMERI DI OGGI.

<!-- pezzo libro-052 | libro -->
## Libro · Bitcoin on-chain (2/3)

- PayJoin negli acquisti on-chain del mercatino (dal 16 novembre 2026, se nei NUMERI DI OGGI è disponibile): il QR e «₿ Apri nel wallet» portano anche un link PayJoin («pj=»), e nel foglio di pagamento compare la riga «🔀 PayJoin». Se il tuo wallet lo sa fare (per esempio Sparrow, BlueWallet, Wasabi, Bull Bitcoin, Cake Wallet), mentre paghi Barattolo aggiunge alla transazione una sua piccola moneta: così chi guarda la blockchain non può più dire che tutti gli ingressi sono tuoi, né leggere a colpo d'occhio quale uscita è il tuo resto. Paghi la stessa cifra, e il deposito a tre chiavi riceve esattamente gli stessi sats. Il tuo wallet può mettere qualche sats in più di commissione di rete per l'ingresso aggiunto (lo decide lui, entro il limite che si dà). Se il wallet non lo sa fare, o se in quel momento Barattolo non ha una moneta pronta, si paga come sempre, senza differenze. La riga non c'è sempre: compare solo quando il PayJoin si può fare. Negli scambi P2P e nello Swap il PayJoin non c'è.
- Quando paghi on-chain (un ordine, il deposito di uno scambio P2P, lo Swap) l'app scrive i sats da mandare e, sotto, la riga «In BTC» con la stessa cifra in bitcoin (per esempio 0,00008128 BTC): molti wallet on-chain la chiedono così. Un tocco la copia, col punto (0.00008128), pronta da incollare nel wallet. Se invece inquadri il QR, la cifra il wallet la compila da solo; anche «₿ Apri nel wallet» apre il wallet con indirizzo e cifra già scritti.
- Profilo → «📥 Come ricevi»: due righe, «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in». Lì scegli se i sats ti arrivano in Lightning, on-chain, oppure «Ogni volta» (decidi tu ordine per ordine).
- Chi ha queste scelte trova anche, nel modulo dell'annuncio sotto il prezzo, «Come vuoi ricevere per questo oggetto?»: la scelta dell'annuncio vale più di quella del Profilo.
- Nel mercatino, quando chi vende riceve su una rete diversa da quella con cui paga chi compra, lo swap di SATS Routing lo paga chi vende: esce dai suoi sats quando li riceve, e chi lo fa vede il costo prima di confermare. Chi compra paga solo il prezzo del conto, senza righe in più.
- Profilo → «₿ On-chain»: «Dove ricevi i bitcoin» (l'unica cosa da compilare: il tuo indirizzo o il tuo wallet), poi la chiave e le 12 parole. Salvato l'indirizzo, la voce dice «✅ Ricevi nel tuo wallet» con l'inizio e la fine dell'indirizzo (per esempio bc1qw508…v8f3t4): intero non si mostra, ma è salvato. Per cambiarlo si incolla lì quello nuovo; «Togli» lo toglie. Le 12 parole servono solo a FIRMARE i tuoi scambi on-chain: i sats non arrivano lì. Non darle mai a nessuno.

<!-- pezzo libro-053 | libro -->
## Libro · Bitcoin on-chain (3/3)

- Le 12 parole hanno bisogno di una copia fuori dal telefono: Barattolo la salva cifrata nel cloud di Telegram e/o sui relay Nostr. Se manca la copia sui relay, nel Profilo c'è «Salva sui relay Nostr». Dal 16 novembre 2026, chi non ha nessuna copia (succede a chi entra dal sito o da Tor senza Nostr: lì il cloud di Telegram non c'è, e Tor Browser cancella tutto quando lo chiudi) prima di pubblicare o prendere un ordine on-chain vede le 12 parole, le scrive su carta e ne riscrive tre a caso per controllo; lo stesso controllo c'è dietro «Le ho scritte su carta» nel Profilo. Le parole restano sul telefono: Barattolo non le chiede mai. Se qualcuno su Tor rivede il foglio a ogni apertura, è normale: Tor cancella anche il segno che il controllo è fatto (e le parole stesse: le ritrova incollandole dal Profilo).
- Il wallet è uno solo, fra la Mini App in Telegram e il sito: se apri Barattolo da un altro posto, ti chiede di incollare le stesse 12 parole invece di crearne di nuove.
- Dove nasce il wallet on-chain (dal 19 novembre 2026): ovunque, dal sito come dalla Mini App; il wallet resta UNO solo per account (se c'è già, Barattolo non ne fa nascere un secondo). Le 12 parole raggiungono da sole la loro copia: se il wallet nasce sul sito col login Telegram, basta aprire una volta Barattolo dentro Telegram (@ilbarattolobot) e poi di nuovo il sito: le parole arrivano chiuse nella Mini App (Barattolo non le può leggere) e finiscono nel cloud di Telegram. Se l'account ha anche la chiave Nostr collegata, le parole arrivano allo stesso modo al sito quando si entra con quella chiave, e da lì vanno sui relay Nostr: poi ogni login Nostr le ritrova. Barattolo sa solo DOVE sta la copia, mai le parole, e quando le chiede dice da dove riprenderle. Se arrivano parole diverse da quelle già sul dispositivo, non si sovrascrive niente: decide l'utente dal Profilo («₿ On-chain»).
- Se non hai ancora scelto dove ricevere, la consegna dei bitcoin a te aspetta: l'app ti manda a Profilo → «₿ On-chain» per sceglierlo.
- La seconda firma: i sats on-chain escono con due firme su tre. Di solito il tuo telefono mette la sua da solo quando apri Barattolo; nell'ordine c'è anche il tasto «✍️ Metti la seconda firma», che mostra l'anello mentre firma e poi dice com'è andata, o perché non ha firmato (per esempio: la tua chiave sta solo sul telefono con cui hai pagato o venduto). Quando i sats sono partiti l'ordine lo dice, con il link «Vedi la transazione», e il tasto sparisce.

<!-- pezzo libro-054 | libro -->
## Libro · Lo Swap: spostare i tuoi sats fra Lightning e bitcoin on-chain (1/2)

La pagina «Swap» (la scheda in basso; fino al 12 novembre 2026 si chiamava «Cambio») sposta i TUOI sats fra Lightning e un tuo indirizzo bitcoin on-chain, nelle due direzioni, senza un ordine di mezzo. Se è accesa lo dicono i NUMERI DI OGGI.
- Lightning → bitcoin: scrivi la cifra (quella che mandi o quella che ricevi), incolli il tuo indirizzo bitcoin e paghi la fattura Lightning col tuo wallet; i bitcoin arrivano al tuo indirizzo. Il telefono li ritira quando il blocco del servizio ha la sua prima conferma sulla rete (di solito una decina di minuti): fino ad allora lo swap dice «aspetto la prima conferma», ed è normale.
- Bitcoin → Lightning: scrivi quanto vuoi ricevere (o quanto mandi), incolli una tua fattura Lightning di quella cifra esatta e mandi i bitcoin all'indirizzo che l'app ti mostra; quando arrivano, la tua fattura viene pagata. La cifra esatta nella frase «crea una richiesta di … sats esatti» si tocca e si copia, pronta da incollare nel wallet. Al posto della fattura puoi incollare il tuo Lightning address (nome@wallet): la fattura della cifra giusta la chiede Barattolo al tuo wallet quando premi «Conferma».
- Lo swap lo fa un servizio esterno (SATS Routing). Barattolo non prende commissioni: prima di confermare vedi quanto ricevi, con dentro la commissione del servizio e quella della rete.
- I sats non passano mai da Barattolo: partono dal tuo wallet e arrivano al tuo wallet.
- Lo swap si fa col proprio account: la scheda «Swap» in basso la vede anche chi non è ancora entrato (dal 16 novembre 2026, prima al suo posto c'era «Aste»), e toccandola si apre il foglio per entrare con Telegram o con Nostr; appena entrato, l'app porta alla pagina «Swap». Chi vede ancora «Aste» nella barra ha l'app aperta da prima dell'aggiornamento: basta chiuderla e riaprirla.
- Le aste non sono ancora partite. Ci si arriva dalla tessera «Aste» in «Esplora per categorie» (subito dopo «Scambio P2P»), nella home del mercatino: porta alla pagina «Le aste stanno arrivando», dove col bottone «🔔 Avvisami» chiedi di essere avvisato quando partono. Il vecchio tasto «🔨 Aste ›» in cima alla home non c'è più, e dal 24 novembre 2026 nemmeno la card quadrata «Aste» in «Da scoprire».
- Limiti: da 25.000 sats a 0,01 BTC (1.000.000 sats) a swap, al massimo 5 swap al giorno. Da bitcoin verso Lightning il minimo è 50.000 sats RICEVUTI in Lightning (è il minimo del servizio): chi scrive la cifra in «Mandi» deve mandarne un po' di più, perché dai bitcoin mandati si tolgono la commissione del servizio e la rete. Se la cifra è sotto, l'app dice il minimo dal lato dove l'hai scritta (per esempio «Lo swap parte da 50.568 sats da mandare»). Se il servizio cambia i suoi limiti, vale il più stretto.

La privacy dello Swap, cioè chi vede cosa:

<!-- pezzo libro-055 | libro -->
## Libro · Lo Swap: spostare i tuoi sats fra Lightning e bitcoin on-chain (2/2)

- Barattolo si segna, legati al tuo account, la direzione, la cifra, il numero dello swap e l'indirizzo del servizio dove passano i bitcoin. Non si segna il tuo indirizzo bitcoin né la tua fattura Lightning. Però dal numero dello swap, sulla blockchain pubblica, si può seguire dove sono andati i bitcoin.
- SATS Routing vede quel che serve a fare lo swap: la fattura Lightning e il tuo indirizzo bitcoin. Non sa chi sei su Barattolo.
- La pagina parla con SATS Routing e con mempool.space (da lì legge la rete e trasmette la transazione) direttamente dal tuo telefono o computer, quindi loro vedono il tuo IP. Se entri dal sito .onion con Tor Browser, non lo vede nessuno dei tre.
- Sulla blockchain, da Lightning a bitcoin: al tuo indirizzo arriva una transazione con un solo ingresso, l'indirizzo del servizio, e una sola uscita, il tuo indirizzo; di solito ha l'aspetto di un pagamento qualunque. Da bitcoin a Lightning: si vede la transazione che parte dal tuo wallet verso l'indirizzo del servizio, come ogni pagamento on-chain.
- Payjoin: nello Swap non si usa. Da Lightning a bitcoin la transazione verso il tuo indirizzo la prepara il tuo telefono per lo swap, e non sa fare Payjoin: se incolli un link Payjoin («bitcoin:…?pj=…») l'app tiene solo l'indirizzo e i bitcoin arrivano lì con una transazione normale. Da bitcoin a Lightning l'indirizzo del servizio non accetta Payjoin, quindi anche il tuo wallet manda una transazione normale.
- Il consiglio di sempre: un indirizzo nuovo per ogni swap, in un wallet di cui solo tu hai le chiavi.

<!-- pezzo libro-056 | libro -->
## Libro · La Caccia a Tappo (il gioco) (1/2)

La Caccia a Tappo è il gioco di Barattolo (se nelle REGOLAZIONI del pannello «Caccia a Tappo (il gioco)» è accesa). Si apre dal Profilo → «Livello e recensioni» → «🔩 Caccia a Tappo», e funziona uguale nella Mini App di Telegram, nell'app e sul sito.

Come si gioca: ogni giorno Tappo scappa dal barattolo e si nasconde in un annuncio vero della vetrina, diverso per ogni persona (quindi chiedere a un amico dov'è non serve). Nella pagina del gioco c'è la dispensa di Tappo: sei scaffali, con un barattolo per ogni categoria. Scegli lo scaffale dove cercare e il grado della caccia, leggi il primo indizio (per esempio il barattolo, cioè la categoria, la fascia di prezzo o una parola del titolo) e vai fra gli annunci: in ogni scheda c'è il tasto «🔩 Tappo è qui?», che risponde sì o no. Ogni tocco è un'occhiata, e le occhiate del giorno sono contate. A mezzanotte (ora italiana) la caccia ricomincia con un nascondiglio nuovo. Dov'è nascosto Tappo oggi non lo sa nessuno, nemmeno l'assistente: non si può dire.

Cosa si vince: i bulloni 🔩, la moneta del gioco. Chi trova Tappo ne prende di più se ha usato meno indizi. I bulloni NON sono sats e NON sono XP: non si comprano, non si regalano, non si scambiano, non si incassano e non fanno salire di livello. Giocare è gratis e non si vince denaro.

Cosa lo rende lungo: i sei gradi (Curioso, Segugio, Esploratore, Detective, Volpe, Leggenda), che si aprono trovando Tappo più volte al grado prima; salendo gli indizi sono più vaghi, le occhiate meno, e dal Detective Tappo scappa lasciando un biglietto e va ritrovato in due o tre tappe. Ogni ritrovamento accende il barattolo di quella categoria: bronzo, argento dopo 5 volte, oro dopo 20. Poi ci sono le sfide (scheda «Sfide»), che pagano bulloni da sole quando arrivi alla soglia.

Coi bulloni, nella scheda «Bottega», si prendono: attrezzi che si consumano (🔦 torcia: 3 occhiate in più per oggi; 💡 lampadina: apre il prossimo indizio senza abbassare il premio; 🧲 calamita: per oggi dice se sei vicino a ogni occhiata sbagliata), cappellini e sfondi per Tappo, il titolo «🔩 Amico di Tappo», 5 posti in più nel barattolo dei preferiti e una coppa. Quel che hai sta nella scheda «Zaino». Un oggetto preso non si rende.

Per chi vende: se Tappo si nasconde in un tuo annuncio e qualcuno lo trova, il bot te lo dice (senza dire chi è stato). Non devi fare niente: sono visite in più. Nei tuoi annunci, per te, Tappo non si nasconde mai.

<!-- pezzo libro-057 | libro -->
## Libro · La Caccia a Tappo (il gioco) (2/2)

Il Mondo di Tappo (scheda «Mondo», la prima): Tappo cammina dentro la dispensa, sei zone una sopra l'altra, una per scaffale. Si guida toccando dove andare o trascinando il dito (dal computer anche frecce o WASD). Nel mondo si raccolgono i bulloni sparsi (ognuno si prende una volta), si aprono i barattoli (portano agli annunci di quella categoria), si legge il cartello con la caccia del giorno, si entra in bottega e, nella prima zona, il Banco del cambio porta agli scambi P2P. Le zone più in alto si aprono trovando Tappo più volte. Sul palco di ogni zona ci sono gli annunci in evidenza: chi vende può metterci un suo annuncio in vetrina per un giorno spendendo 40 bulloni (uno al giorno a testa, al massimo 3 annunci per zona). L'evidenza vale solo dentro il gioco, non in Esplora.

Le missioni di Tappo: otto scene brevi a carte, una per zona della «🚀 Rotta per la Luna», il tabellone dei livelli (e tutte in cima alla scheda «Sfide» della Caccia a Tappo), ognuna subito prima della casella che insegna: Tappo ha un problema, Barattolo lo risolve, e alla fine un bottone porta a fare la cosa vera nell'app. Sono «Dal baratto ai sats» (la storia del denaro, prima di «Attiva l'incasso automatico in Lightning»), «Il barattolo col lucchetto» (il deposito di garanzia), «Le dodici parole» (le chiavi sono tue: dove tenere la frase di recupero, e nessuno, nemmeno Barattolo, la chiede mai), «La staffetta del fulmine» (Lightning), «L'oblò scuro» (la privacy: cosa sa Barattolo di te), «Il quaderno di tutti» (Bitcoin è un registro che tengono in tanti, e nessuno lo trucca), «L'antenna di Tappo» (Nostr: gli annunci su tanti relay e un nome che è una chiave tua) e «L'ultimo bullone» (il dimezzamento e i 21 milioni). Ogni missione monta un pezzo del razzo con cui Tappo vuole arrivare sulla Luna, all'halving del 2028. Danno da una a tre stelle: la prima volta pagano bulloni, rigiocarle per le tre stelle si può ma non paga di nuovo. Non danno XP. Le parole e i conti dentro le missioni sono finti.

<!-- pezzo libro-058 | libro -->
## Libro · Nostr

Gli annunci di Barattolo vengono pubblicati anche su Nostr, una rete aperta: esistono sui relay anche indipendentemente da Barattolo. Se colleghi una tua chiave Nostr dal Profilo, i tuoi annunci escono firmati da te (la firma la fa il tuo browser) e restano tuoi. Gli avvisi possono arrivarti anche su Nostr, oltre che su Telegram. La chiave privata (nsec) non va mai data a nessuno, nemmeno a Barattolo.

Il nome verificato su Nostr (se nelle REGOLAZIONI del pannello «Nome verificato su Nostr» è accesa): dal livello «Bottega avviata» chi ha una chiave Nostr collegata CON UNA FIRMA (non basta averla solo scritta nel profilo) può scegliere gratis un nome come mario@barattolo.store. Si fa nel Profilo, gruppo «Impostazioni», cassetto «🆔 Nostr e identità», alla riga «✔️ Nome verificato su Nostr»: si scrive il nome (lettere minuscole, cifre, punto, trattino o _, da 3 a 30 caratteri) e si tocca «Prendi questo nome». Poi bisogna copiarlo («📋 Copia») e incollarlo nella propria app Nostr (Damus, Primal, Amethyst...), nel campo «NIP-05» o «Indirizzo Nostr» del profilo: Barattolo non lo può scrivere al posto tuo. Le app mostrano allora la spunta accanto al nome. Non si possono prendere un nome già preso, lo username Telegram di un altro, né nomi come «admin», «staff» o «barattolo». Si può cambiare o lasciare quando si vuole. Se scendi sotto il livello o togli la chiave, il nome resta salvato ma va in pausa finché non torna tutto a posto.

Su Nostr risponde anche Tappo: si può scrivere un DM al profilo «Barattolo» (npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy) oppure rispondere sotto le sue note, e Tappo risponde come su Telegram. Ai bot e allo spam non risponde, e se qualcuno dello staff sta già seguendo quella conversazione lascia parlare lui. Per un problema con un ordine, in pubblico Tappo invita a scrivergli in privato.

<!-- pezzo libro-059 | libro -->
## Libro · I tuoi dati, in breve (1/2)

Barattolo sa di te pochissimo: niente email, password o telefono. Da Telegram riceve il numero identificativo, il nome e lo username; da Nostr solo la chiave pubblica. L'indirizzo di spedizione è cifrato e si cancella quando confermi di aver ricevuto. Niente tracciamento, niente pubblicità, niente cookie di terzi. Tutto è spiegato nella pagina «I tuoi dati» (barattolo.store/privacy).

L'indirizzo IP: come ogni server, quello di Barattolo vede l'IP di chi si collega mentre gli risponde. Finisce solo nel registro tecnico della macchina: non nel database, non in un profilo, e non lo incrociamo con niente. Da Telegram l'IP non arriva.

Tor: Barattolo ha anche un sito .onion, lo stesso Barattolo dentro la rete Tor. Da lì il server non vede il tuo IP e non lo scrive da nessuna parte. L'indirizzo esatto è nella pagina «I tuoi dati», e quando apri barattolo.store con Tor Browser la barra degli indirizzi ti propone da sola la versione .onion («.onion disponibile»). Con un .onion conta ogni carattere: usa solo quello ufficiale.

Sessioni attive: nel Profilo, nel gruppo «Impostazioni» accanto a «🔐 I tuoi dati», c'è «💻 Sessioni attive». Mostra dove è aperto il tuo account: la Mini App di Telegram e ogni browser in cui sei entrato dal sito (per esempio «Chrome su Windows»), con la data. Come su Telegram, da una sessione chiudi solo quelle aperte DOPO di lei, mai una più vecchia; dalla Mini App di Telegram le chiudi tutte. La sessione da cui stai guardando non si chiude da lì: per quella c'è «Esci». Se vedi un browser che non riconosci, chiudilo dalla Mini App.

Cancellare l'account: nel Profilo, nel gruppo «Impostazioni» accanto a «🔐 I tuoi dati», c'è «🗑 Cancella il mio account» (se la voce non c'è, oggi non è disponibile). Si può fare solo quando non hai niente in corso: se c'è un ordine non concluso, un pagamento in arrivo, sats ancora da ricevere, un'asta con puntate o uno scambio P2P aperto, il foglio te lo elenca e il bottone non compare finché non è tutto chiuso. Poi il foglio dice cosa sparisce e cosa resta; per confermare scrivi CANCELLA e tocchi «🗑 Cancella per sempre». Non si può annullare.
- Spariscono il profilo (nome, foto, Lightning address, chiave Nostr collegata), i preferiti, gli avvisi, gli indirizzi salvati e le chat; gli annunci in vetrina vengono ritirati, anche da Nostr e dai canali; le recensioni ricevute, i punti e l'eventuale posto da pioniere si perdono.
- Restano, senza il tuo nome, gli ordini conclusi e i pagamenti (per la contabilità e le contestazioni: chi ha fatto affari con te vede «Utente cancellato») e le recensioni che hai scritto, senza firma.
- Di te Barattolo tiene solo un'impronta del numero dell'account (non il numero, e mai il telefono) con la data, e le eventuali penalità degli scambi P2P: se rientri con lo stesso account parti da zero, e tornano solo quelle. La chat col bot la togli tu da Telegram, e i messaggi Nostr firmati da te restano tuoi.

<!-- pezzo libro-060 | libro -->
## Libro · I tuoi dati, in breve (2/2)

Questo assistente: la tua domanda e le ultime battute arrivano ad Anthropic, l'azienda dell'intelligenza artificiale che risponde, ma mai il tuo nome, il tuo account o i tuoi ordini. Le conversazioni non vengono conservate: in chat privata l'assistente ricorda le domande e le risposte della giornata, per seguire il filo del discorso, e a mezzanotte spariscono.

<!-- pezzo libro-061 | libro -->
## Libro · Se Barattolo sparisse

Il mercatino gira su un server solo: se si fermasse, Barattolo si fermerebbe. Ma i sats del deposito stanno su un nodo Lightning separato, con la seed custodita offline; gli annunci restano su Nostr; lo storico è salvato ogni giorno con copie cifrate anche fuori dal server.

<!-- pezzo libro-062 | libro | sempre -->
## Libro · Sicurezza e truffe

- Nessuno di Barattolo ti chiederà mai la seed, le parole di recupero, la nsec, una chiave privata o una password. Chi le chiede è un truffatore. Se le hai date a qualcuno, considerale esposte e sposta subito i fondi su un wallet nuovo.
- Barattolo non ti scrive per primo chiedendo soldi.
- Gli account ufficiali di Barattolo su Telegram sono SOLO questi: il bot https://t.me/ilbarattolobot, il canale https://t.me/barattolostore (con la sua chat privata e il gruppo dei commenti), Tappo https://t.me/TappoBarattoloBot (dal 16 novembre 2026 ci si arriva anche col bottone «💬 Chiedi a Tappo» nel bot di Barattolo, nel benvenuto e quando gli si scrive una frase, e dalla voce «🤖 Chiedi a Tappo» nel Profilo della Mini App, sezione Supporto), e le due persone dello staff, Andrea https://t.me/aandreaiita e Alan https://t.me/AlanBimbati. Quando qualcuno chiede se un account è vero o come trovare lo staff, metti SEMPRE questi link, nascosti dietro il nome (per esempio «Andrea» che porta a https://t.me/aandreaiita), così chi li tocca arriva all'account giusto senza poter sbagliare. Chiunque altro dica di essere dello staff, dell'assistenza o di Barattolo NON lo è, anche se il nome sembra uguale: i truffatori copiano nome e foto e cambiano una lettera (per esempio una «I» maiuscola al posto della «l», come @aIanbarattoIo, che NON è Alan). Prima di fidarti, guarda il NOME UTENTE, quello con la @ (lo trovi aprendo il profilo, alla voce «Nome utente»), e controllalo lettera per lettera: il nome visualizzato e la bio li può scrivere chiunque, quindi «Alan» o «Barattolo» scritto lì non prova niente.
- Lo staff non ti chiede mai soldi in privato, né per «scambi di buoni», «sblocchi», «verifiche» o rimborsi. Se qualcuno lo fa, non mandare niente, bloccalo e segnalalo da Telegram, e avvisa lo staff.
- Paga sempre dentro Barattolo: un pagamento fuori dal deposito di garanzia non è protetto.
- Nel P2P, libera i sats solo quando gli euro sono arrivati davvero sul tuo conto, non prima e non sulla fiducia di una ricevuta.

<!-- pezzo libro-063 | libro | sempre -->
## Libro · Parlare con una persona (1/2)

Se nei NUMERI DI OGGI l'assistenza in app risulta disponibile, c'è anche una chat con lo staff dentro Barattolo: Profilo → Aiuto → «💬 Assistenza». Ognuno ha la sua conversazione; lo staff risponde col bollino 🛡️ e ti arriva un avviso quando c'è una risposta. Al messaggio si possono allegare fino a tre screenshot (il bottone «📎 Allega screenshot» sotto la casella, oppure sul computer Ctrl+V di uno screenshot copiato, senza salvarlo prima): li vedono solo lo staff e chi li ha mandati. Anche lo staff può rispondere con uno screenshot, che trovi nella stessa conversazione.

Se l'assistente non basta, sotto ogni sua risposta c'è il bottone «🙋 Parla con una persona»: ti dà la chat privata di Barattolo (t.me/barattolostore?direct), dove risponde una persona dello staff. Se quel link ti apre il canale invece della chat: le chat private dei canali ci sono solo nelle versioni recenti di Telegram, quindi aggiorna l'app e riprova dal telefono; oppure apri il canale @barattolostore e cerca in fondo alla pagina il tasto per mandare un messaggio. Se ancora non va, scrivilo a Tappo (@TappoBarattoloBot): passa lui il messaggio allo staff. Per un problema con un ordine o uno scambio preciso, scrivi lì il numero dell'ordine e cosa è successo. Per una lite su un ordine coi sats in garanzia, la strada giusta resta la disputa, dalla pagina dell'ordine o dello scambio.

I livelli: ogni persona ha un livello che sale con gli XP (li danno solo gli acquisti e le vendite concluse, più una quota per chi inviti) e con il numero di affari conclusi: Nuovo arrivato, Bottega avviata, Mercante pratico, Mercante esperto, Maestro del banco. Lo trovi nel Profilo, nel cassetto «🎖 Livello e titolo». Dal 17 novembre 2026 i livelli si sfogliano come tessere, scorrendo col dito: sulla tua c'è l'anello con i tuoi XP sulla soglia del prossimo e quanto manca, i livelli già passati hanno la spunta, quelli davanti il lucchetto; sotto ci sono i vantaggi del livello che stai guardando, ✅ se già tuoi, 🔒 se ancora da sbloccare (sconto sul banner del negozio, link del negozio a scelta, il titolo da mettere sotto il nome, lo sconto sulle commissioni P2P dal livello 5). Il livello si vede anche sul tuo negozio e in classifica, accanto al titolo.

<!-- pezzo libro-064 | libro | sempre -->
## Libro · Parlare con una persona (2/2)

Rotta per la Luna (pronta dal 17 novembre 2026, ma PER ORA SPENTA: nel Profilo non c'è ancora, e se qualcuno la chiede si risponde che arriverà presto; nei primi giorni si chiamava «la stradina»). Quando sarà accesa: nel Profilo, nel cassetto «Livello e recensioni», c'è «🚀 Rotta per la Luna», un tabellone lunghissimo che vede solo chi lo apre, dalla Terra (in basso) alla Luna (in cima), su una mappa disegnata in otto zone: «Primi passi», «Il mercatino», «Il porto», «Il bosco dei sats», «La scala d'oro», «La vetta», «In orbita», «Verso la Luna». All'ingresso di ogni zona Tappo racconta in una frase cosa si impara lì (per esempio al porto: mettere al sicuro i sats con un wallet on-chain e la firma Nostr). La storia è quella del razzo di bulloni, la stessa del gioco di Tappo: Tappo costruisce un razzo per la Luna, un pezzo per zona (piedini, serbatoio, motore, ali, oblò, punta, antenna), il Tarlo e la Gazza dispettosi provano a rubargli i bulloni, e all'halving del 2028 il razzo parte. Ogni casella è una competenza di Barattolo e di bitcoin, dalla più facile alla più difficile: mettere un articolo nel barattolo, la foto, seguire un venditore, attivare l'incasso automatico in Lightning (l'indirizzo Lightning nel Profilo); poi il primo annuncio, il primo acquisto, la prima recensione, collegare la chiave Nostr, invitare una persona col proprio link; poi la prima vendita, creare il wallet on-chain, verificare la chiave Nostr con una nota pubblica, la doppia configurazione Telegram + Nostr, il primo scambio P2P; poi le soglie che crescono (fino a 100 vendite e 10 milioni di sats incassati) e le caselle a tempo («Un mese con Barattolo», sei mesi, un anno, un anno e mezzo, due anni). L'ultima casella prima della Luna è «Arriva all'halving del 2028» (circa aprile 2028): nessuno arriva in cima prima di allora. Le caselle si spuntano da sole quando la cosa è fatta e diventano monete d'oro; Tappo è la tua pedina e cammina in fila: sta sulla prima casella che manca, quella da fare adesso (quelle fatte più su restano accese), e quando la fai cammina fino alla successiva. La prima volta Tappo si presenta e racconta il razzo (si rivede col tasto «❓ Come funziona» in cima). Toccando la casella da fare, la scheda in basso dice a cosa serve, con «Come funziona?» e i passi (per esempio il primo acquisto spiega il deposito di garanzia); sulle caselle già fatte la scheda non esce. Il bottone «Vai» porta dritto al posto giusto (il cassetto del Profilo, la vetrina, un negozio da seguire, «Vendi») e un riflettore, come nei tutorial dell'app, indica cosa toccare; appena la cosa è fatta l'app torna da sola alla Rotta per la Luna. Quando finisci una zona compare il razzo che prende il pezzo nuovo; toccando il razzo in cima lo si rivede. I gradini della scala dei livelli sono barattoli che si accendono quando si sale di livello. Gli amici (i venditori che segui e chi ha concluso uno scambio con te) stanno come pedine sul loro livello, e in fondo c'è «La gara fra amici». La strada si scopre camminando: si vede la zona dove sei e quella dopo, grigia e spenta, con le caselle ancora misteriose (un cerchio col punto di domanda); quando fai una casella, la prossima si accende e il suo nome compare, con un suono; più su c'è un lucchetto, e il pezzo successivo si apre finendo la zona dove sei. In cima, in fondo alla barra, c'è il razzo di Tappo, che cresce di un pezzo a ogni zona (otto pezzi, dalla pedana ai motori accesi). Il tasto «🗺 Vedi tutta», in alto a destra, mostra il viaggio intero in una schermata (le zone ancora chiuse hanno il lucchetto); toccando una zona si torna lì. Ci sono anche dei suoni, che si spengono col tasto 🔊 in cima. Le caselle NON danno XP e non danno sats: sono la mappa, non un premio. Chi ha scelto «Non mostrarmi in classifica» non compare fra gli amici di nessuno.

<!-- pezzo schermata-001 | schermata -->
## Schermata «astepresto»

🔨
 Le aste stanno arrivando
 Presto potrai vendere al miglior offerente.
 Chi punta versa subito i sats: chi vince non sparisce.
Un solo messaggio, il giorno che arriva.

<!-- pezzo schermata-002 | schermata -->
## Schermata «P2P, libro ordini»

Compra BTC
 Sei su Compra BTC. Tocca per passare a Vendi BTC
 Sei su Vendi BTC. Tocca per passare a Compra BTC
Vendi BTC
 Più recenti
 Convenienza
 Importo: dal più grande
 Importo: dal più piccolo
Questo ordine non è più disponibile
 È stato preso, è scaduto oppure chi l'aveva pubblicato l'ha ritirato. Qui sotto trovi gli altri ordini aperti.
✕
aggiorno…

<!-- pezzo schermata-003 | schermata -->
## Schermata «I miei scambi P2P»

## 
 Più recenti
 Prima quelli da fare
 Importo: dal più grande
 Importo: dal più piccolo
Questo scambio non è fra i tuoi
 È stato tolto o chiuso da tempo, oppure è di un altro account. Qui sotto trovi i tuoi scambi.
✕

<!-- pezzo schermata-004 | schermata -->
## Schermata «Lo scambio P2P (info)» · Lo scambio P2P (1/9)

## Lo scambio P2P
Comprare e vendere bitcoin fra persone, coi sats fermi in garanzia finché non è tutto a posto.
Qui non compri da Barattolo: compri da un'altra persona. Vi mettete d'accordo su un prezzo, gli euro viaggiano fra voi due col metodo che scegliete, e i sats restano bloccati in garanzia finché gli euro non sono arrivati davvero. Barattolo non tocca i tuoi euro, e i sats li tiene in garanzia: solo per farli arrivare a chi compra, o tornare a chi vende.
## Come funziona, in cinque passi
Qualcuno pubblica un ordine. Dice se compra o vende sats, per quanti euro e con quali metodi di pagamento. L'ordine finisce nel libro degli ordini, che vedono tutti.
Tu lo prendi. Scegli con quale metodo vuoi inviare gli euro (o riceverli) e l'ordine si riserva a te: da quel momento non lo può più prendere nessun altro.
Chi vende blocca i sats. Paga una richiesta particolare, che trattiene i sats invece di consegnarli: escono dal suo wallet ma non arrivano a nessuno. Da qui in poi sono in garanzia.
Chi compra manda gli euro. Col metodo scelto, al recapito che l'altra persona gli lascia qui dentro: finché non arriva il bottone resta spento, e appena arriva ti avvisiamo. Poi lo dice qui.
Chi vende libera i sats. Controlla di aver ricevuto gli euro e li libera: arrivano all'indirizzo Lightning indicato da chi compra.
## La garanzia: chi può muovere i sats
«In garanzia» non è un modo di dire. La richiesta di pagamento del terzo passo è speciale: si paga, ma non si incassa. I sats restano appesi a mezz'aria, e da lì possono prendere due strade sole — andare a chi compra, oppure tornare a chi vende. Una terza strada non esiste: nessuno può dirottarli altrove, nemmeno chi li sta tenendo.
E a tenerli è il coordinatore, che siamo noi: il programma si chiama Mostro, a farlo girare è Barattolo e il nodo è nostro — è lo stesso che tiene il libro degli ordini. Lo scriviamo invece di lasciartelo scoprire, perché non toglie niente a quello che c'è scritto qui sopra: le uniche due cose che il coordinatore fa coi sats sono consegnarli a chi compra o restituirli a chi vende. Non li tiene per sé e non li porta altrove.
## Il prezzo, e perché le cifre ballano
Gli ordini si scrivono in euro — «vendo 50 € di sats» — e i sats si contano al cambio del momento. Il cambio si muove in continuazione, quindi finché l'ordine è nel libro la cifra in sats è una stima: la vedi col segno ≈ davanti, che è il modo onesto di dire «più o meno tanti».
La cifra esatta si fissa quando l'ordine viene preso, non un attimo prima. Da lì in poi non cambia più: quello che leggi nello scambio è quello che passa di mano.
Alcuni ordini portano un intervallo («da 20 a 100 €»): quelli li prendi scegliendo tu quanto, dentro la fascia.

<!-- pezzo schermata-005 | schermata -->
## Schermata «Lo scambio P2P (info)» · Il premio e lo sconto (2/9)

## Il premio e lo sconto
Chi pubblica può chiedere un po' più o un po' meno del mercato, fino a ±%. Sopra il mercato si chiama premio e conviene a chi vende; sotto si chiama sconto e conviene a chi compra. Nel conto dello scambio quella riga c'è sempre, col suo nome e la sua percentuale.
Il premio si applica prima della commissione: prima si calcola il controvalore col premio, poi la commissione morde su quello. È l'ordine in cui il conto mostra le righe, e non è impaginazione.
## La commissione
## Come si pagano gli euro
I metodi sono un elenco chiuso: . Chi pubblica sceglie quali accetta, chi prende ne sceglie uno.
Gli euro non passano da Barattolo. Viaggiano fra te e l'altra persona sul circuito che avete scelto, come se vi foste messi d'accordo per strada. Il recapito che serve — l'IBAN, il RevTag, il numero — ve lo scambiate qui dentro e cifrato: lo legge solo chi deve pagare.
Per questo la garanzia protegge i sats e non gli euro: se dici di aver inviato gli euro e non l'hai fatto, chi vende semplicemente non libera. E se li hai inviati e non liberano, c'è la disputa.

<!-- pezzo schermata-006 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (3/9)

## Barattozon: il PayCode al tabacchino, passo per passo
È il metodo per chi non vuole passare da una banca o da un'app: chi vende sats fa un ordine Amazon da pagare in contanti nel punto vendita e chi compra lo paga alla cassa del tabacchino col PayCode. Il tabacchino incassa i contanti, l'ordine Amazon risulta pagato, e i sats si liberano. Nel libro il metodo si chiama ancora «Contanti al tabacchino»: è la parola che leggono anche le altre app.
Paghi in contanti alla cassa del tabacchino un ordine Amazon di chi vende: ricevi cifrati codice, importo e scadenza appena l'ordine è tuo, e paghi solo quando la pagina dice «Sats in garanzia». Non vedi nome, indirizzo né cosa ha comprato. Per pagare non serve alcun documento. Tieni lo scontrino in caso di disputa.
Chi vende fa l'ordine su Amazon scegliendo «paga in contanti nel punto vendita». Amazon gli manda una mail con tre cose: il PayCode (nove cifre, come 479-868-518), l'importo esatto coi centesimi e una scadenza, settantadue ore dal checkout. Vale fino a novecentonovantanove euro per ordine, senza commissione; per Barattozon un PayCode vale almeno venticinque euro. Non vale per Amazon Warehouse, contenuti digitali, oro, abbonamenti a Prime, buoni regalo e acquisti 1-Click: se la mail di Amazon non offre il pagamento in contanti, l'ordine non è pagabile con Barattozon.
Chi vende pubblica qui, con Barattozon come unico metodo, e il foglio lo porta per mano in quattro passi: il PayCode, l'importo, la scadenza (con un selettore di data e ora, fra un'ora e settantadue ore) e il premio, con lo stesso cursore degli altri ordini, da meno venti a più venti per cento, a numeri interi. Un PayCode vale almeno 25 €. Prima dei quattro passi si sceglie il tipo di prezzo, come per ogni ordine: a prezzo di mercato i sats si calcolano quando qualcuno prende l'ordine, col premio, sull'importo arrotondato per eccesso all'euro intero (25,47 € diventano 26: chi paga riceve sempre almeno il valore di quel che paga, e la differenza la mette chi pubblica); a prezzo fisso i sats nascono adesso, sui centesimi esatti e al cambio di oggi, e la convenienza per chi prende si muove col bitcoin. Il segno decide il verso: col premio positivo chi paga al tabacchino riceve meno sats del cambio pieno e la differenza resta a chi vende; col premio negativo ne riceve di più, e quella differenza la paga chi vende per la comodità. A zero passa il cambio pieno. Premio più basso = più conveniente per chi paga = più probabile che qualcuno lo prenda in tempo. Prima di pubblicare c'è il riepilogo, che a prezzo di mercato dice anche l'arrotondamento. Il cambio si fissa lì a prezzo fisso, alla presa a mercato; l'ordine resta nel libro fino a due ore prima della scadenza del PayCode (mai oltre settantadue ore): poi esce da solo.

<!-- pezzo schermata-007 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (4/9)

Nel libro la card dice quanto conviene adesso, come negli altri ordini: «più conveniente» o «meno conveniente» per chi guarda, e dal dieci per cento il cartellino dell'affare. I sats sono fissi dalla pubblicazione e il bitcoin no, quindi la convenienza vera si muove col prezzo, e il numero la segue, senza limiti. Nel dettaglio trovi i due numeri uno accanto all'altro: il premio scelto da chi vende e quello al prezzo di adesso. Dopo la presa il conto si ferma al prezzo di quel momento: i sats che ricevi sono quelli scritti, al satoshi.
Chi compra prende l'ordine, indica dove ricevere i sats, e chi vende li blocca in garanzia. Il PayCode, l'importo e la scadenza gli arrivano qui dentro e cifrati solo quando la pagina dice «Sats in garanzia», in un riquadro col tempo che resta: prima il codice non c'è, e al tabacchino non si va. Nel libro pubblico c'è solo l'importo: il PayCode non lo vede nessun altro, nemmeno Barattolo.
Chi compra va a pagare in un punto abilitato al PayCode: non tutte le tabaccherie lo sono. Si cercano sulla 
mappa di Amazon, che chiede un account Amazon (uno qualsiasi); chi non ce l'ha cerca per CAP su 
PuntoLis spuntando «Amazon Paga in Contanti», o scrive il suo CAP a chi vende, che lo cerca per lui. Alla cassa mostra il codice e dice «devo pagare un ordine Amazon in contanti con un PayCode»: non una ricarica, non un buono regalo, che non pagano l'ordine. Paga l'importo esatto, senza commissione, e controlla lo scontrino: pagamento dell'ordine, non «codice acquisto» o buono. Poi tiene lo scontrino, la sua prova, e torna qui a toccare «Ho pagato al tabacchino».
Chi vende controlla su Amazon che l'ordine risulti saldato, e sceglie fra due bottoni: «Risulta pagato: libera i sats» oppure «Non risulta pagato: apri una disputa». Ha ventiquattro ore a vista, e Barattolo glielo ricorda su Telegram dopo un'ora, sei ore e venti ore. Non esiste una conferma automatica: Amazon non parla con Barattolo, e i sats non si liberano da soli. Se chi vende non fa nulla, i sats restano in garanzia e chi ha pagato può aprire lui la disputa: decide un moderatore, e lo scontrino è quel che guarda.
Se scade. Ci sono due scadenze, e vanno tenute distinte. Quella del libro cade almeno due ore prima di quella del PayCode: se nessuno ha preso l'ordine, esce dalla vetrina e a chi vende arriva un avviso — il PayCode vale ancora per poche ore, ma nessuno può più prenderlo; quando scade anche lui, l'ordine Amazon va rifatto e ripubblicato con un PayCode nuovo. Quella del PayCode conta quando i sats sono già in garanzia: la pagina dello scambio lo dice, ti avvisa sei ore prima e un'ora prima (anche su Telegram o Nostr, secondo le tue impostazioni) e mette in evidenza l'annullo d'accordo, con cui i sats tornano a chi li ha bloccati. Nessuno annulla da solo: se hai pagato in tempo, lo scontrino lo dimostra e chi vende libera.

<!-- pezzo schermata-008 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (5/9)

Se ti danno un buono regalo. Alla cassa possono emettere per errore un buono regalo Amazon o una ricarica: l'ordine di chi vende non risulta pagato. Non toccare «Ho pagato al tabacchino»: scrivi a chi vende e decidete insieme.
Prendi un ordine Barattozon solo se fai in tempo ad andare al tabacchino: quando mancano meno di sei ore, il dettaglio te lo ricorda prima di prenderlo.
## Contanti di persona
Il metodo «Contanti» è l'incontro a mano: chi compra sats porta le banconote, chi vende le conta e libera i sats lì, davanti a lui. Una banconota non lascia ricevuta, quindi le regole sono tre e valgono dall'inizio.
Il rilascio sul posto. A chi compra: Consegna i contanti solo quando chi vende preme «Libera i sats» davanti a te, e controlla che lo scambio risulti concluso prima di andare via. A chi vende: Conta i contanti davanti a chi ti paga, poi premi «Libera i sats» lì, davanti a lui: chi compra deve vedere lo scambio concluso prima di andare via. Mai prima di vedersi, mai dopo essersi salutati.
L'incontro. Vedetevi in un posto pubblico e di giorno — un bar, un incontro bitcoin —, contate le banconote insieme, e mai grosse cifre da soli.
🕒 L'appuntamento. Chi vende indica dove e quando vedervi: il giorno e l'ora con pochi tocchi, e il luogo come indirizzo vero — mentre lo scrive gli proponiamo indirizzi esistenti, o usa la sua posizione. Chi compra lo trova in cima alla pagina dello scambio, con «🧭 Apri nel navigatore». Se l'appuntamento cambia, l'altra persona riceve l'avviso.
📍 «Sono qui», la prova d'incontro. Quando arrivate, ognuno tocca «Sono qui» dal suo telefono, senza aspettare l'altro: si registrano l'ora esatta e, se il telefono la dà, la posizione, firmate con la chiave usa-e-getta dello scambio. È facoltativo, per la privacy, ma aiuta a risolvere le dispute. L'altra persona vede l'ora in cui l'hai segnato, mai la tua posizione; un moderatore, solo in caso di disputa, vede se eravate lì insieme, all'ora e vicino al luogo dell'appuntamento. Il GPS si può falsificare: la posizione è una conferma, non una prova assoluta.
In disputa, sul contanti. Se chi vende dice di non aver ricevuto i contanti e non c'è la prova d'incontro, in disputa si dà ragione a chi vende. Ma se chi compra ha segnato la presenza all'ora e vicino al luogo dell'appuntamento e chi vende no, la disputa non va in automatico a chi vende: decide il moderatore. Lo scriviamo adesso, prima dello scambio, e non il giorno della disputa.

<!-- pezzo schermata-009 | schermata -->
## Schermata «Lo scambio P2P (info)» · Contante per posta (6/9)

## Contante per posta
Il metodo «Contante per posta» è la busta di banconote spedita: chi compra sats la manda a chi li vende, chi vende la apre e libera i sats. È il metodo più facile da contestare, quindi le regole sono scritte prima, e in disputa valgono solo le prove.
Chi spedisce. Spedisci solo quando questa pagina dice «Sats in garanzia», con un servizio tracciato (meglio col servizio di Poste Italiane per denaro e valori, da sportello, che il contante lo ammette e lo rimborsa fino a 3.000 €): filma mentre chiudi busta e pacco col numero di tracciamento in vista, e scrivi il numero nella chat dello scambio.
Chi riceve. Apri il pacco filmando, col numero di tracciamento in vista, dall'esterno sigillato fino alle banconote contate; poi libera i sats. Senza quel video, in disputa la tua parola non basta.
Il pacco. Busta di carta sigillata dentro una busta di plastica sigillata, in un pacco con altro dentro che non suoni vuoto; mai la parola «contanti» sulla busta; mittente vero, che un pacco non consegnato torna indietro.
La cauzione. Chi prende un ordine scegliendo «Contante per posta» blocca la stessa piccola cauzione del contanti di persona: torna a fine scambio, e si perde solo se un moderatore decide che non ha spedito.
In disputa, sulla posta. In disputa contano le prove: il tracciamento consegnato e i due video. Chi spedisce senza tracciamento non può provare di aver spedito; chi apre senza filmare non può provare che la busta era vuota. La posta ordinaria e i corrieri il denaro lo escludono dal rimborso: un pacco perso è perso; solo il servizio di Poste per denaro e valori lo rimborsa, fino a 3.000 €.
## I tempi
Se il tempo scade prima che i sats siano bloccati, la richiesta di pagamento si annulla e nessuno perde niente. Se a mancare è stato chi ha preso l'ordine, l'ordine torna nel libro per qualcun altro; se è stato chi l'ha pubblicato, si chiude.
Coi sats in garanzia avete circa quattro giorni. Se chi compra non ha ancora detto di aver pagato, allo scadere i sats tornano da soli a chi vende; se l'ha detto, si apre una disputa.

<!-- pezzo schermata-010 | schermata -->
## Schermata «Lo scambio P2P (info)» · La chat dello scambio (7/9)

## La chat dello scambio
Da quando l'ordine è preso a quando lo scambio finisce, nella sua pagina c'è una chat fra voi due: serve a mettervi d'accordo, a dirvi «fatto», a chiedere «ti è arrivato?». Oltre al testo puoi mandare foto (jpg, png, webp) e PDF fino a 20 MB, col 📎: partono cifrati dal tuo telefono, le foto senza la posizione e i PDF senza i dati nascosti (autore, programma, date), e se ne vanno con la chat. Il recapito per gli euro resta nel suo riquadro, così non si perde fra i messaggi.
È cifrata fra voi due. Ogni telefono fa nascere a caso una chiave apposta per quello scambio; Barattolo trasporta i messaggi già chiusi. A fine scambio la cancella: i telefoni buttano chiave e messaggi, il nostro server cancella le buste, e nei backup non ci sono mai entrate.
Barattolo non ti scrive mai qui. Chi nella chat si presenta come «assistenza» è l'altra persona.
Non uscire dallo scambio per pagare. I link nella chat non si aprono, e sotto un messaggio che ne porta uno, o che ti chiede di spostarti altrove, compare una riga rossa.
Non mandare codici o chiavi. Per completare uno scambio non servono a nessuno.
Se cambi telefono o browser a metà scambio la chat ti segue, con tutti i messaggi: appena nasce, il telefono lascia sul nostro server una copia sigillata della chiave, chiusa con la chiave di quello scambio. La apre solo chi ha il tuo profilo di scambio, il server la riconsegna solo a te, e a fine scambio sparisce con il resto.
Chi la può aprire. La chat è cifrata fra voi due e Barattolo la trasporta. Se il tuo account è nato su Nostr, Barattolo non la può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo ritrovi scambio e chat su ogni dispositivo, e per questo Barattolo durante lo scambio potrebbe tecnicamente aprirla. Non lo fa. A fine scambio la chat si cancella, per tutti. Il moderatore la legge solo se una di voi due apre una disputa.
In una disputa il moderatore legge la chat solo se una di voi due la apre: è il telefono di chi apre la disputa a dargli la chiave, e glielo diciamo prima del tocco. Legge e non scrive al posto vostro; a disputa chiusa si cancella tutto, come a fine scambio.

<!-- pezzo schermata-011 | schermata -->
## Schermata «Lo scambio P2P (info)» · Gli avvisi: cosa ti diciamo, e quando (8/9)

## Gli avvisi: cosa ti diciamo, e quando
Ad app aperta la pagina dello scambio si muove da sola: la richiesta da pagare, il foglio dove indicare i sats e il passo dopo compaiono appena arrivano — via Tor ci vogliono di solito dieci-venti secondi. Ad app chiusa ti avvisiamo su Telegram o su Nostr, secondo le tue impostazioni.
Un avviso per ogni passo che ti riguarda, e dice quale: il tuo ordine è stato preso, c'è la garanzia da pagare, i sats sono in garanzia e tocca a te indicare dove riceverli, l'altra persona ha indicato dove ricevere i sats, dice di aver inviato gli euro, chiede di annullare, ha aperto una disputa, il pagamento dei sats non è passato. E alla fine: concluso (con quanto hai ricevuto o pagato, commissione compresa), annullato, tornato nel libro o scaduto.
«Ti ha indicato dove inviare gli euro: tocca a te», quando chi vende ti lascia il recapito. Il recapito non è nell'avviso: lo leggi qui dentro, cifrato — e prima di inviare gli euro guarda che la pagina dica «Sats in garanzia». Col contanti di persona è «dove e quando vedervi», e se l'appuntamento cambia te lo diciamo.
«Hai un nuovo messaggio nello scambio», quando l'altra persona ti scrive nella chat e non la stai guardando. Il testo non è nell'avviso: lo leggi qui dentro. Uno per ogni volta che c'è da leggere, non uno per messaggio.
Niente, per un gesto che hai fatto tu: l'hai già davanti. L'avviso va a chi deve fare il passo dopo, o deve saperlo.
Da dove vengono. A raccontarci i passi è il coordinatore — che facciamo girare noi — nel momento in cui succedono. Ci dice quale ordine, quale passo, e fra quali due chiavi usa-e-getta; degli importi ci dice solo quelli della chiusura. Non ci manda fatture, recapiti né messaggi: quelli restano cifrati fra voi due, e non li vediamo. Se un suo avviso si perde per strada, i passi pubblici — preso, concluso, annullato, scaduto — li leggiamo dal libro, e te li diciamo un minuto dopo.
Gli avvisi si spengono tutti dal cassetto «🔔 Avvisi» del profilo. A scambio aperto conviene tenerli accesi: alcuni passi hanno i minuti contati, e l'avviso dice quanti.

<!-- pezzo schermata-012 | schermata -->
## Schermata «Lo scambio P2P (info)» · Se qualcosa va storto (9/9)

## Se qualcosa va storto
Prima di tutto: dai tempo all'altra persona, e scrivile nella chat dello scambio. Quasi sempre è un bonifico che deve arrivare, o qualcuno che dorme.
Annullare d'accordo. Uno dei due propone di annullare, l'altro accetta, e i sats tornano a chi li aveva bloccati. Serve il sì di tutti e due: nessuno si tira indietro da solo dopo che l'altro si è mosso.
La disputa. Si apre quando i sats sono già in garanzia — prima non c'è niente da contendere. Da quel momento lo scambio si ferma: né tu né l'altra persona potete più muovere i sats, e a decidere chi li riceve è un moderatore del coordinatore, cioè di Barattolo: guardiamo le prove di tutti e due e scegliamo. Anche lì le strade restano due — i sats vanno a chi compra o tornano a chi vende — e lo diciamo adesso, invece di lasciartelo scoprire quel giorno.
Tieni le prove di quello che hai fatto: la ricevuta del bonifico, la schermata del pagamento. Sono quelle che guarda chi decide.
Uno scambio fermo sul passo sbagliato. Se la pagina non dice quello che è successo davvero, copia la diagnosi e mandacela: racconta cosa ha visto l'app in questa sessione. Non contiene chiavi, fatture né recapiti.
🩺 Copia la diagnosi dei tuoi scambi
## Chi sei, qui dentro
✈️Se il tuo account è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricaviamo dal tuo account: ti segue da solo fra telefono e computer, e non c'è niente da creare. Il prezzo lo diciamo per intero — il server di Barattolo lo sa ricavare: non lo facciamo e niente nel programma lo fa, ma potremmo.
🟣Se il tuo account è nato su Nostr, o se in passato hai reso il tuo profilo di scambio una chiave Nostr tua, quel profilo non lo può ricavare nessuno, noi compresi.
🎭Il tuo nome non c'è. Ogni scambio usa una chiave usa-e-getta, diversa ogni volta: nell'ordine pubblico si leggono l'importo e il metodo di pagamento, mai chi sei. Anche dentro l'app, di nomi non ne compaiono.
📖Gli ordini sono pubblici. Il libro vive fuori da qui e lo legge chiunque: è così che funziona uno scambio senza padrone. I recapiti e la chat no: sono cifrati fra voi due, e Barattolo non li legge.
🔐 Il patto sui tuoi dati, per intero
🫙 Qualcosa non torna, o non è chiaro? Scrivici: durante il rodaggio leggiamo tutto.

<!-- pezzo schermata-013 | schermata -->
## Schermata «Il pagamento protetto» (1/5)

← Torna
Barattolo⚡
## Il pagamento protetto
Come fa un mercatino fra sconosciuti a essere sicuro per tutti e due.
Quando compri su Barattolo i tuoi sats non vanno subito al venditore: si fermano in un deposito di garanzia (in gergo escrow) che custodisce Barattolo. Il venditore sa che i soldi ci sono e spedisce tranquillo; tu sai che non si muovono finché l'oggetto non è arrivato davvero.
## Cosa succede quando paghi
Paghi. Ricevi una invoice Lightning e la paghi col wallet che preferisci — si apre, si incolla o si inquadra il codice. Se hai collegato un wallet con NWC, «⚡ Compra subito» fa tutto in un tocco.
I sats si fermano. Appena il pagamento arriva, entrano nel deposito di garanzia. Il venditore riceve l'avviso e prepara l'oggetto: da quel momento sa di essere pagato, ma i sats non sono ancora suoi.
Il venditore consegna. Spedisce e segna il corriere, oppure vi mettete d'accordo per il ritiro in zona, oppure — se è un codice o un buono — te lo consegna qui dentro, mai in chat private.
Ricevi e confermi. Quando l'oggetto è arrivato ed è come promesso, lo confermi. Solo in quel momento i sats passano al venditore.
Se sei tu a vendere: i sats ti arrivano da soli sul tuo Lightning address — lo imposti una volta nel Profilo, non scade mai, e lo usiamo al momento del pagamento. Se non ne hai uno, quando chi compra conferma ti avvisiamo e in quel momento incolli una fattura nell'ordine. Prima no: una fattura Lightning scade, da un'ora a pochi giorni, e arriverebbe scaduta.
## I tempi
Dopo la consegna hai ore per controllare l'oggetto e confermare. I sats non partono da soli: se allo scadere non hai detto nulla ti mandiamo un promemoria, e se il silenzio continua interviene un moderatore.
Lo stesso vale se non segni mai la ricezione: dopo giorni dalla spedizione ti scriviamo, ma il deposito resta fermo. Nessuno incassa mentre tu non hai confermato.
Il codice online ha finestre più corte: ore da quando lo riveli, e ore se il venditore l'ha consegnato e tu non l'hai ancora aperto.
La invoice del pagamento vive minuti. Se scade non è successo niente: si rifà, e il prezzo si riconverte al cambio del momento.
## Se qualcosa va storto
Finché i sats sono nel deposito puoi aprire una disputa dalla pagina del tuo ordine. Il deposito si congela e interviene un moderatore: legge le due versioni, guarda quello che avete (foto, tracking, messaggi) e decide. Le strade sono tre — i sats tornano a te, spedizione compresa; vanno al venditore; oppure tornano a te meno le spese di spedizione, che restano al venditore: è il caso del pacco tornato indietro per un indirizzo sbagliato. Quando l'oggetto va restituito, il rimborso parte dopo che è tornato indietro.
Aprire una disputa non è un'accusa: nella gran parte dei casi è un malinteso che si chiarisce in mezza giornata.

<!-- pezzo schermata-014 | schermata -->
## Schermata «Il pagamento protetto» · Dove il deposito non può proteggerti (2/5)

## Dove il deposito non può proteggerti
Meglio dirlo prima che scoprirlo dopo.
Di una prestazione non vediamo niente. Una lezione o una consulenza avvengono fuori di qui — in videochiamata, o di persona — e Barattolo non può sapere se ci sono state. Quello che possiamo guardare, se finite in disputa, sono le condizioni: l'appuntamento era stato concordato da tutti e due? Il collegamento era stato lasciato nell'ordine, e quando? Sono fatti che restano scritti qui dentro, ed è su quelli che un moderatore decide.
Per questo i sats non si muovono da soli: nessun timer li sblocca, si sbloccano quando chi ha comprato conferma. Se non conferma, decide un moderatore.
Un codice rivelato non torna indietro. Nessuno — nemmeno noi — può sapere se l'hai già riscattato. Per questo la finestra è di ore: provalo subito. Se non ci sono prove da nessuna delle due parti, la regola di default dà ragione a chi ha consegnato.
Vale anche al contrario: se il codice non funziona, hai ore per aprire una disputa — e in quel momento i sats sono ancora fermi.
Un posto su un abbonamento condiviso può sparire dopo. Il piano resta di chi te l'ha venduto: può toglierti il posto, e il fornitore può chiuderlo — quasi tutti chiedono che chi condivide viva sotto lo stesso tetto. È più scomodo di un codice: lì la domanda è «l'ho riscattato o no», qui l'accesso funzionava e poi ha smesso, e Barattolo non può verificare né l'una né l'altra cosa. Provalo subito: la finestra è quella del codice, ore. Dopo, i sats sono usciti.
Nel ritiro a mano, il controllo è il tuo. Guarda e prova l'oggetto prima di confermare che l'hai ritirato: con la conferma i sats partono al venditore, e non tornano indietro.
Un punto di ritiro di Barattolo è una persona, non un'azienda. Dietro un locker o una tabaccheria c'è un contratto con un corriere; dietro un punto nostro c'è qualcuno che si è offerto, e con noi non ha firmato niente. Quello che ti diamo è un fatto con una data: quando il punto riceve il pacco lo segna qui dentro, e quel momento resta scritto. Dal banco alla tua mano, invece, non c'è più niente che possiamo verificare — è lo stesso buco del ritiro a mano.
Se il pacco non arriva, apri la disputa: i sats sono ancora fermi e decide un moderatore. Ma sappi cosa gli risulta: se il punto ha segnato di aver ricevuto il pacco, per noi chi ha spedito ha consegnato. E se un punto sbaglia, l'unica cosa che possiamo fare è toglierlo dalla mappa: non abbiamo un contratto da fargli valere. Vai a ritirare presto, e scegli un punto di cui ti fidi.
Il pacco perso o rovinato è una cosa fra chi spedisce e il corriere. Barattolo garantisce la transazione: che il venditore non incassi senza aver consegnato e che tu non paghi senza ricevere. L'oggetto in viaggio no — se il corriere lo perde o lo rompe, il reclamo si apre con lui.

<!-- pezzo schermata-015 | schermata -->
## Schermata «Il pagamento protetto» · Dove il deposito non può proteggerti (3/5)

Spedite sempre col tracciamento, e per le cose di valore con la copertura del corriere. Il tracciamento è la prova che l'oggetto è partito ed è arrivato, ed è la prima cosa che guarda un moderatore; la copertura di base, verso i punti di ritiro, è quasi sempre molto bassa.
Chi vende può anche scegliere la posta senza tracciamento: costa meno, ma il pacco non si può seguire, chi compra lo vede scritto nell'ordine, e se si perde il rischio resta di chi l'ha spedito.
Il deposito garantisce l'oggetto promesso, non i gusti. «Non mi piace più» non è un difetto; un oggetto diverso da com'era descritto sì.
Un indirizzo sbagliato lo paga chi l'ha scritto. Se l'indirizzo che hai indicato è sbagliato e il pacco torna indietro, le spese di spedizione restano a tuo carico. Per questo prima di pagare ti chiediamo di ricontrollarlo, e di confermarlo con una spunta.
## Cosa non si può vendere
Su Barattolo non si vendono:
armi
droghe
servizi sessuali
refurtiva
contraffazioni
documenti
dati personali
farmaci
animali protetti
Ogni annuncio passa dalla moderazione, anche quando lo modifichi: se qualcosa non convince, resta in attesa di un moderatore.
## Il pagamento, in pratica
Su Barattolo si paga solo in bitcoin, sulla rete Lightning: trasferimenti immediati e con commissioni di rete quasi nulle, anche per pochi euro di valore. Il prezzo lo puoi leggere in sats o in euro con l'interruttore € / ₿ — quello che viaggia sono sempre sats.
Ti serve un wallet Lightning: ne esistono tanti, gratuiti, e ne basta uno. Al pagamento Barattolo ti mostra una invoice: la copi, o inquadri il codice, e il wallet fa il resto. Se colleghi il wallet con NWC (Nostr Wallet Connect) dal tuo Profilo, il bottone «⚡ Compra subito» paga senza passaggi, e nel P2P la fattura per ricevere i sats la fa il wallet da solo — la connessione resta solo sul tuo dispositivo, non arriva mai ai nostri server, e nel wallet puoi darle un tetto di spesa (o, per il solo P2P, il solo permesso di ricevere).

<!-- pezzo schermata-016 | schermata -->
## Schermata «Il pagamento protetto» · L'indirizzo per la spedizione (4/5)

## L'indirizzo per la spedizione
Se scegli la spedizione a un indirizzo — casa, ufficio, un amico o un negozio che accetta il pacco per te — lo scrivi al momento dell'acquisto e resta dentro l'ordine: lo vede solo il venditore, per stampare l'etichetta. Non lo pubblichiamo da nessuna parte, non lo usiamo per altro, e i moderatori non lo leggono — nemmeno per decidere una disputa: a loro risulta soltanto se l'hai indicato, quando, e che l'hai confermato.
E non lo conserviamo: lo trasportiamo. Nel database è cifrato, e appena confermi di aver ricevuto l'oggetto viene cancellato — da quel momento l'affare è chiuso e quello che succede fra te e il venditore non ci riguarda più. Se invece l'ordine si chiude senza la tua conferma — un rimborso, una disputa decisa da un moderatore — sparisce entro giorni. Finché l'ordine è aperto resta, perché è lì che serve: se un affare non si chiude mai, l'indirizzo lo aspetta.
La strada che ne chiede di meno è il punto di ritiro: lì un indirizzo tuo non c'è proprio — al banco basta il nome del destinatario, che sceglie il venditore. Puoi lasciare la tua email, se vuoi che il codice di ritiro te lo mandi il corriere invece del venditore: è facoltativa, non è mai una condizione per comprare, e sparisce con l'ordine.
## Dove stanno i sats, e per quanto
I sats restano bloccati in un conto Lightning della piattaforma per il tempo dell'affare, e non un minuto di più: dal pagamento alla conferma. Non è un conto tuo, non è un investimento, non li mettiamo a rendere da nessuna parte. Quando l'affare si chiude, escono — al venditore o a te.
## Se Barattolo sparisse
Oggi il mercatino gira su un server solo, con un database solo. Non è ridondato in altre nazioni: se lo spegnessero, Barattolo si fermerebbe. Meglio dirlo prima che chiederlo.
Quello che non si ferma con lui:
⚡I sats. Il deposito non vive qui dentro: sta su un nodo Lightning nostro, separato dal server, e la sua seed è custodita offline. Il gestionale che lo comanda è ospitato da terzi; il nodo e la seed no.
🟣Gli annunci. Vanno su Nostr (NIP-99) ed esistono sui relay indipendentemente da noi. Se hai una chiave Nostr tua, provata, l'annuncio esce sul tuo account — a firmarlo è il tuo browser, la chiave non passa mai di qui — e resta tuo anche se Barattolo non c'è più. Se non ce l'hai lo firma la nostra: resta leggibile in piazza, ma a governarlo siamo noi. La chiave si collega dal Profilo, ed è il motivo per cui abbiamo scelto Nostr dal primo giorno.
📖Il codice. È la cosa più facile da rimettere in piedi altrove.
💾Lo storico degli ordini e la reputazione che ci avete costruito. Vivono in un posto solo, ma sono salvati ogni giorno, con copie cifrate anche fuori dal server.

<!-- pezzo schermata-017 | schermata -->
## Schermata «Il pagamento protetto» · L'app Android: controlla che sia nostra (5/5)

## L'app Android: controlla che sia nostra
Barattolo si installa anche come app per Android, da 
Zapstore o dalle 
release su GitHub (con Obtainium si aggiorna da sola). Dentro non c'è niente di diverso dal sito: è una finestra su barattolo.store.
Per essere sicuro che quella che hai sia proprio la nostra, e non una copia che le somiglia, controllala con 
AppVerifier: incolla queste due righe, il nome tecnico dell'app e l'impronta del certificato con cui la firmiamo. Se non combaciano, non aprirla e scrivici.
store.barattolo.app
2F:3F:5E:68:94:AB:A0:B8:E4:39:B7:28:9D:55:50:D5:0E:22:37:15:F3:A8:E6:4F:2C:49:38:BC:D5:A2:C2:3C
📋 Copia le due righe
🔗 Condividi questa pagina
🔐 E i tuoi dati?
🫙 Domande, dubbi, o qualcosa che non torna? Scrivici: durante il rodaggio leggiamo tutto.

<!-- pezzo schermata-018 | schermata -->
## Schermata «I tuoi dati» (1/17)

← Torna
Barattolo⚡
## I tuoi dati
Cosa sappiamo di te, per quanto tempo, e chi lo legge.
La risposta corta è: pochissimo. Per stare su Barattolo non ci lasci un'email, non scegli una password, non ci dai un numero di telefono. Entri con Telegram o con una chiave Nostr, e tutto il resto sono le cose che servono a fare un affare — quasi tutte le scrivi tu, quando servono, e alcune le cancelliamo da soli appena l'affare è finito.
## Chi sei, per noi
Se entri da Telegram riceviamo quello che Telegram dà a tutte le sue Mini App: un numero identificativo, il tuo nome e lo username se ce l'hai. Se hai una foto profilo ne teniamo una copia nostra, piccola — mai un link ai file di Telegram, che portano dentro il token del bot e scadono. Se la tua foto è nascosta ai non-contatti, resta l'iniziale: quello è il tuo modo di dire no, e vale.
Se entri da Nostr riceviamo la tua chiave pubblica, e basta. La chiave privata non ce l'abbiamo mai: quando serve una firma la fa il tuo browser, o il tuo bunker, e quello che arriva qui è già firmato.
Password non ne abbiamo perché non esistono: la porta la apre Telegram, oppure una firma tua. Non c'è niente da rubarci che ti apra l'account.

<!-- pezzo schermata-019 | schermata -->
## Schermata «I tuoi dati» · Cosa nasce mentre usi il mercatino (2/17)

## Cosa nasce mentre usi il mercatino
I tuoi annunci: sono pubblici per definizione — è il loro mestiere.
I tuoi ordini: cosa hai comprato o venduto, quanto, quando, e come è andata.
Il tuo Lightning address, se lo imposti per incassare da solo: è un nome@dominio, come una mail, e ce l'abbiamo in chiaro — è lì che ti mandiamo i sats quando un affare si chiude, quindi dobbiamo poterlo leggere. Non esce da nessuna parte: non lo vede chi compra, non lo vedono i moderatori.
La fattura che incolli per incassare, se l'address non lo usi: si incolla solo al momento dell'incasso — nel Profilo non se ne salva nessuna, perché una fattura scade e vale per un pagamento solo — e resta scritta in quell'ordine, come ricevuta di dove sono andati i sats.
La tua reputazione: voti ricevuti, distintivi, il livello, e gli XP, che contano il commercio — quanto hai comprato e venduto, più una piccola parte di quello delle persone che hai invitato, da quando quelle che commerciano sono almeno tre.
Gli inviti: il tuo codice e, se sei arrivato con un invito, chi ti ha invitato. A chi ti ha invitato non diciamo mai chi sei: vede quante persone ha portato, e i punti che gli hanno fruttato tutte insieme gli arrivano — nel cassetto, nel suo totale, nel livello e in classifica — solo quando quelle che commerciano sono almeno tre: prima restano da parte, e lui vede soltanto che ci sono, senza la cifra. Un limite onesto: se ha invitato soltanto te, la riga «punti in attesa» gli dice che hai cominciato a commerciare — non quanto.
La tua posizione in classifica, se ci entri: lì di te si vedono nome, foto, titolo, media dei voti, da quante persone, quanti affari e il punteggio. Il punteggio mette insieme la media e il commercio, quindi da lì si può ricavare quanto hai commerciato — è una scelta presa sapendolo, perché senza quel numero l'ordine della lista non si legge. Gli XP in chiaro invece non escono mai, e nemmeno il tuo identificativo. Se non vuoi comparire, nel Profilo («Livello e titolo») c'è Non mostrarmi in classifica: il tuo livello resta sul profilo, perché a chi scambia con te serve per fidarsi. E se la tua reputazione la pubblichiamo su Nostr (vedi sotto), smettiamo e chiediamo ai relay di ritirarla.
I tuoi giorni di fila: contiamo i giorni consecutivi in cui apri Barattolo — il numero di adesso, il tuo record e la data dell'ultimo giorno, non le ore né le volte. Dal secondo giorno di fila entri nella Classifica Streak (la classifica dei giorni di fila), che vede solo chi è entrato in Barattolo: lì di te si leggono nome, foto e giorni. Non mostrarmi in classifica ti toglie anche da lì.
Il tuo barattolo, cioè gli annunci che hai messo da parte. Di questi si vede quanti l'hanno salvato, mai chi: nemmeno chi vende sa che sei stato tu — a meno che tu non condivida il barattolo col suo link, che è un gesto tuo: la voce qui sotto dice cosa comporta.
I tuoi avvisi di ricerca, se ne crei: cosa cerchi, dove, entro che prezzo.

<!-- pezzo schermata-020 | schermata -->
## Schermata «I tuoi dati» · Cosa nasce mentre usi il mercatino (3/17)

Gli avvisi del mercatino, se li accendi (sono spenti di serie): le categorie e il prezzo massimo che hai scelto per «🛒 Avvisami dei nuovi annunci», e i venditori che segui — che non lo sanno: nessuno vede chi lo segue, né quanti. E per ogni annuncio di cui ti abbiamo avvisato, il suo numero accanto al tuo, per non avvisarti due volte: se ne va da solo dopo un mese.
Il tuo carrello, se ne componi uno: quali oggetti e quanti, di un venditore solo, così lo ritrovi quando rientri. Dentro non c'è l'indirizzo né la consegna — quelli nascono nella cassa — e chi vende non lo vede.
## Il barattolo condiviso
Il barattolo resta privato finché non decidi tu: dal Profilo puoi creare un link che mostra la lista delle cose che hai messo da parte. È come pubblicare una lista di desideri — chi apre il link vede cosa ti interessa comprare, anche un venditore con cui stai trattando se il link gli arriva. Va fatto sapendolo, e te lo diciamo lì, prima del tocco che crea il link.
La pagina del link non fa il tuo nome: niente nome, niente foto, niente negozio. Chi lo riceve da te sa di chi è, ma un link girato a terzi non lega la lista a una persona. E mostra una fotografia, non il barattolo vivo: quello che salvi dopo non si vede finché non la aggiorni tu, con un gesto.
La revoca è un tocco e il link muore subito: la pagina si rilegge dai nostri dati a ogni apertura, non c'è una copia che sopravviva. Tre limiti onesti, però: chi aveva la pagina già aperta la vede finché non ricarica; l'anteprima del link che Telegram o WhatsApp tengono in cache può durare qualche giorno, ma mostra solo il titolo generico — la lista, in quell'anteprima, non c'è mai entrata; e uno screenshot resta, come per ogni cosa pubblicata. Se un domani ricondividi, il link sarà nuovo: quello vecchio resta morto.

<!-- pezzo schermata-021 | schermata -->
## Schermata «I tuoi dati» · Quello che chiediamo solo quando serve (4/17)

## Quello che chiediamo solo quando serve
Cinque cose non ce le dai per stare qui: te le chiediamo nel momento esatto in cui servono a un affare, e vivono dentro quell'ordine — tranne una, che puoi scegliere di tenerti.
L'indirizzo di spedizione, se scegli la spedizione a un indirizzo. Lo vede solo chi ti vende, per stampare l'etichetta. Ricontrollalo prima di pagare: se è sbagliato e il pacco torna indietro, le spese di spedizione restano a tuo carico.
Il punto di ritiro che scegli, se preferisci quella strada — lì un indirizzo tuo non c'è proprio. Questo, se vuoi, puoi anche tenertelo nel profilo per non riscriverlo ogni volta: è l'unica delle cinque che si può salvare, e la ragione è che un punto di ritiro è un luogo pubblico — un locker, una tabaccheria — mentre casa tua no. Lo salvi con un tocco quando compri, mai da solo, e lo togli quando vuoi.
Un punto di Barattolo è un luogo pubblico anche lui, ma con una differenza che vale la pena sapere: dietro il banco c'è una persona, che vede il pacco, legge il nome sull'etichetta e ti vede in faccia quando passi. Un locker non fa niente di tutto questo. Quello che il punto non sa è cosa c'è nel pacco e chi te l'ha venduto: da noi riceve un codice e basta.
Il codice di un buono o di un prodotto digitale, che chi vende consegna qui dentro invece che in chat.
La tua email, se scegli il punto di ritiro e vuoi che il codice del locker te lo mandi direttamente il corriere. È facoltativa: senza, il codice arriva a chi vende, che te lo passa qui dentro. La legge solo chi ti vende, per stampare l'etichetta, e sparisce con l'ordine come l'indirizzo. Il numero di telefono non te lo chiediamo mai, nemmeno qui.
La nota che scrivi a chi vende, se la scrivi: la taglia, il numero, la variante. È facoltativa, e a differenza dell'indirizzo e dell'email resta nell'ordine — non la cancelliamo, perché è parte di quello che vi siete detti. Scrivici quello che serve per prepararti l'oggetto, non il tuo recapito: per quello ci sono i campi qui sopra.
L'indirizzo lo trasportiamo, non lo conserviamo. Appena confermi di aver ricevuto l'oggetto viene cancellato, senza aspettare nessuna scadenza: da quel momento l'affare è chiuso e quello che succede fra te e chi vende non ci riguarda più. Se l'ordine si chiude senza quella conferma — un rimborso, una disputa decisa da un moderatore — sparisce entro giorni.
Ma se l'ordine non si chiude mai, il tuo indirizzo resta lì. Non c'è nessun timer che lo cancelli comunque, ed è una scelta: finché un affare è aperto quell'indirizzo è l'unica cosa che permette a chi vende di spedirti il pacco, e cancellarlo vorrebbe dire chiudere l'affare al posto tuo. Non è un caso raro — un venditore che sparisce, un pacco che non parte — ed è la coda che finisce sotto gli occhi di un moderatore. Fino ad allora l'indirizzo aspetta insieme all'ordine.
Se vuoi che sparisca, la strada è chiudere l'affare: confermare la ricezione, o aprire una disputa.

<!-- pezzo schermata-022 | schermata -->
## Schermata «I tuoi dati» · Cosa vuol dire «cifrato» (5/17)

## Cosa vuol dire «cifrato»
Vuol dire al riparo da un database rubato, non da noi. L'indirizzo di spedizione, il codice di ritiro della busta e il contenuto di un buono digitale non stanno in chiaro: sono cifrati, e la chiave non è dentro il database. Se qualcuno ne rubasse una copia — un backup, il file del database — quelle tre cose resterebbero illeggibili.
La chiave però sta sullo stesso server che ti risponde, perché è lì che serve per mostrare l'indirizzo a chi vende quando apre l'ordine. Quindi finché quel dato è lì, il server lo può leggere — e chi amministra il server anche. Non lo facciamo e non abbiamo nessuno strumento che lo faccia; nei log restano le impronte e mai i contenuti, e i messaggi d'errore sono scritti apposta per non contenere un CAP. Ma è una promessa nostra, non una garanzia della matematica.
L'unica garanzia vera è che il dato duri poco. È per questo che l'indirizzo si cancella da solo, invece di restare lì «tanto è cifrato».
## Per quanto teniamo le cose
L'indirizzo di spedizione: fino alla tua conferma, o giorni dalla chiusura senza conferma. Qui sopra c'è la storia per intero.
L'email per il corriere: la stessa cosa, e con la stessa scopa — sparisce insieme all'indirizzo, alle stesse condizioni.
La sessione del browser, se entri dal web: giorni, poi si rientra. Nel database non c'è il tuo accesso ma solo la sua impronta.
L'accesso da dentro Telegram vale ore: dopo, riaprendo l'app, se ne fa uno nuovo.
La memoria di quali avvisi ti abbiamo già mandato: giorni, così lo stesso annuncio non ti risuona addosso.
Il carrello: giorni dall'ultima volta che lo tocchi, poi se ne va da solo. Prima, se lo svuoti tu o se paghi un ordine dello stesso venditore.
La fattura di un pagamento vive minuti. Se non la paghi, l'ordine non è mai esistito.
I punti di ritiro che salvi: finché non li togli. Li trovi nel Profilo, in «Quando compri» → «📍 I tuoi punti di ritiro», con una ✕ accanto a ognuno.
Il tuo Lightning address, se l'hai impostato: finché non lo togli. Sta nel Profilo, in «Wallet e incassi», col suo bottone.
La nota che scrivi a chi vende: resta nell'ordine, come il resto di quello che vi siete detti. Finché il pacco non parte puoi cambiarla o toglierla dall'ordine stesso.
Il codice sconto che usi: il suo nome resta scritto nell'ordine — è la ricevuta dello sconto che hai avuto, per te e per chi vende.
Tutto il resto non ha una scadenza, e non è una dimenticanza: annunci, ordini, voti e reputazione sono la memoria degli affari fatti, e servono a te quanto a chi commercia con te — una recensione che sparisce dopo un anno non è una recensione. Un ordine concluso puoi nasconderlo dalla tua lista quando non vuoi più vederlo: sparisce dalla vista, la riga resta.

<!-- pezzo schermata-023 | schermata -->
## Schermata «I tuoi dati» · Chi legge cosa (6/17)

## Chi legge cosa
Chiunque, anche senza entrare: i tuoi annunci, il tuo nome e username, la tua chiave Nostr se l'hai dichiarata, il tuo negozio, i voti e i distintivi. Il numero identificativo di Telegram non esce mai.
Chi compra e chi vende, dentro il loro ordine: quello che serve a portarlo a termine, l'indirizzo e il codice compresi.
I moderatori, quando si apre una disputa: vedi qui sotto.
Noi, nei limiti scritti qui sopra: il server può leggere quello che ha, finché ce l'ha.
## Cosa vede un moderatore
Il tuo indirizzo non lo legge. Quando si apre una disputa un moderatore guarda l'ordine per decidere, e del tuo indirizzo non vede niente nemmeno lì: gli risulta soltanto se l'hai indicato e quando, mai una riga di quello che hai scritto. Lo stesso vale per il nome e il codice di ritiro della busta e per il documento del corriere: quelli li leggono solo chi compra e chi vende.
La tua email per il corriere non la legge. Vale la stessa regola dell'indirizzo, per la stessa ragione: gli risulta soltanto se l'avevi lasciata e quando, che è quello che gli serve per capire da dove doveva arrivare il codice. Il valore no.
Il contenuto di un buono o di un codice digitale invece sì. Se apri una disputa su un acquisto digitale, il moderatore lo legge. Non c'è modo di decidere quella lite senza guardarlo — è l'oggetto stesso del contendere, e chi la apre di solito dice proprio che quel codice non funziona.
E la nota che hai scritto a chi vende, sì. Se una disputa dice «avevo chiesto la taglia L», quella nota è la lite: senza leggerla non c'è modo di decidere. Vale la regola di sopra al contrario — un moderatore che apre un ordine la legge, in disputa o quando lo cerca per numero. È anche il motivo per cui il campo dice, mentre lo scrivi, di non usarlo per il tuo recapito.
Fuori dalle dispute quel contenuto non lo legge nessuno tranne te e chi te l'ha venduto. Se non vuoi che lo veda nessun altro, la strada è non aprire la disputa.

<!-- pezzo schermata-024 | schermata -->
## Schermata «I tuoi dati» · Cosa esce da qui (7/17)

## Cosa esce da qui
✈️Telegram. Gli avvisi te li mandiamo col bot, quindi Telegram vede che ti abbiamo scritto e cosa c'è nel messaggio. Per questo gli avvisi su indirizzo, busta e codici sono scritti vuoti apposta: dicono «apri l'ordine», mai il contenuto. E i bottoni per scrivere alla controparte ti portano fuori, in una chat di Telegram: quella conversazione è vostra e di Telegram, non nostra — non la leggiamo, non ce l'abbiamo, e in una disputa non possiamo usarla.
🟣Nostr. Gli annunci vanno sui relay, che in gran parte sono di altri — e uno è nostro, relay.barattolo.store: lì la copia degli annunci ce l'abbiamo anche noi, ma non è un privilegio, perché quella copia ce l'ha chiunque apra uno qualsiasi degli altri relay. Da noi leggere è aperto a tutti; scrivere no, e possono farlo solo Barattolo e chi ci ha dimostrato la propria chiave Nostr. Ritirare un annuncio manda anche la richiesta di cancellarlo, e i relay che la rispettano lo tolgono — ma nessuno può garantire che l'abbiano fatto tutti, il nostro compreso: nemmeno sul relay di casa possiamo promettere quello che sugli altri non possiamo. Se hai verificato la tua chiave, sui relay va anche la tua reputazione — livello, XP e affari conclusi — firmata da noi (è il kind 30382): con «Non mostrarmi in classifica» smettiamo di pubblicarla e chiediamo di ritirarla, con lo stesso limite degli annunci. Quello che finisce su Nostr non torna indietro. È il prezzo della piazza aperta, ed è la stessa proprietà che rende il tuo annuncio tuo anche il giorno che Barattolo non ci fosse più.
⚡Il nodo dei pagamenti. Quando paghi, la fattura porta il numero dell'annuncio e il suo titolo — mai chi sei.
🤖L'intelligenza artificiale che controlla gli annunci: le arriva il testo dell'annuncio — titolo e descrizione — e mai chi l'ha scritto. Quello che scrivi nella barra di ricerca non le arriva mai: la ricerca è un indice di casa, e la tua domanda non esce da qui.
💬L'assistente del bot, quando è acceso: se scrivi una domanda al bot, la domanda e le ultime battute della conversazione arrivano ad Anthropic, l'azienda dell'intelligenza artificiale che ti risponde, insieme alle nostre guide — mai il tuo nome, il tuo account né i tuoi ordini. Anthropic non usa questi testi per addestrare i suoi modelli. Noi le conversazioni non le salviamo: il server ricorda le ultime battute per mezz'ora, solo in memoria, poi spariscono. Se tocchi «🙋 Parla con una persona», la tua ultima domanda arriva ai moderatori insieme al tuo nome Telegram.
💱Il cambio euro/bitcoin, che chiediamo noi una volta al minuto e non il tuo browser: così nessun terzo sa che stai guardando un prezzo.

<!-- pezzo schermata-025 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (8/17)

## Il profilo di scambio P2P
Per scambiare sats in euro con altre persone lo scambio passa da un coordinatore (il programma si chiama Mostro, e a farlo girare è Barattolo, sul nostro nodo), e per riconoscerti lì serve un profilo di scambio. Nasce e funziona da solo: dentro l'app non c'è niente da creare né da gestire. Qui sotto diciamo per intero da dove viene e chi lo può ricavare, perché dipende da dove è nato il tuo account, non da come entri.
Se il tuo account è nato con Telegram (anche se poi entri con Nostr), il profilo lo ricaviamo noi dal tuo account: così è lo stesso dal bot, dal sito e dall'app, e torna da solo su un telefono nuovo senza che tu debba salvare niente. Il prezzo lo diciamo per intero: quel profilo il server di Barattolo lo sa ricavare, quindi in linea di principio potrebbe firmare uno scambio al posto tuo. Non lo facciamo, e non c'è niente nel programma che lo faccia — ma potremmo, e questo è l'unico posto di Barattolo in cui possiamo dirlo di un tuo segreto. Per ricavarlo servono due cose insieme, una nella configurazione del server e una nel database: chi si portasse via una sola delle due non ricaverebbe nulla.
Se il tuo account è nato su Nostr, il profilo non lo può ricavare nessuno tranne te, noi compresi, ed è lo stesso ovunque perché ce l'hai tu. Vale anche se in passato hai reso il tuo profilo di scambio una chiave Nostr che è tua, dovunque sia nato l'account: resta così, e questa strada resta nel patto anche se oggi non ha più un gesto dentro l'app.
Per fartelo ritrovare su ogni dispositivo, il tuo browser ne mette una copia cifrata sui relay Nostr — i tuoi, quelli pubblici che usa Barattolo e il nostro: la apre solo la tua chiave, noi no, e sul nostro server non ce n'è nessuna. Il prezzo lo diciamo per intero: chi legge quei relay vede che la copia esiste ed è tua, non cosa contiene. «Dimentica il profilo» la toglie anche da lì: la sostituisce con una vuota e chiede ai relay di cancellarla. Non possiamo garantire che tutti obbediscano: su un relay che non lo fa può restare la copia vecchia, sempre cifrata, e resta visibile che una copia c'è stata.
Negli altri casi — un profilo nato nel browser prima che arrivasse quello del conto — il profilo vive sul dispositivo e non lo può ricavare nessuno. Dentro Telegram ne salviamo una copia nel cloud del tuo account Telegram, così sopravvive alla cache svuotata e ti segue fra telefono e computer: chi ha il tuo account Telegram ce l'ha anche lui — è già così per tutto Barattolo — e Telegram potrebbe leggerlo, che è il prezzo. Il codice segreto serve a portare il profilo fuori da Barattolo, in un altro programma che parla con lo stesso coordinatore.

<!-- pezzo schermata-026 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (9/17)

In tutti e tre i casi il server conosce la parte pubblica del profilo e le chiavi usa-e-getta di ogni scambio, per poterti avvisare quando c'è una novità, e da settembre 2026 anche a che numero di scambio sei arrivato: serve a non riusare due volte la stessa chiave usa-e-getta quando apri Barattolo da un dispositivo nuovo, ed è un dato che dai conti che teneva già si sarebbe comunque ricavato. Dal foglio qui sotto il codice segreto lo vedi e lo copi, e il profilo lo dimentichi; dimenticandolo si cancella anche la parte pubblica che il server teneva.
Dal 16 settembre 2026 il server annota anche quali ordini pubblichi e quali prendi, per avvisarti con i numeri quando lo scambio si muove (preso, concluso, annullato, tornato in vetrina): sono i passaggi pubblici del libro, e la cifratura dei messaggi non si tocca. Dal 12 ottobre 2026 chi scambia da Barattolo è riconosciuto dall'altra persona con qualunque modo di entrare — Telegram, nsec, bunker o estensione: la presa si annota, chi ha pubblicato vede il suo profilo e le due parti possono recensirsi. Il collegamento fra la chiave dello scambio e l'account lo sa solo il server, e lo mostra solo all'altra parte di quello scambio: mai in pubblico, mai sui relay. Non c'è un interruttore: chi vuole restare anonimo entra con una chiave Nostr nuova, che per l'altra persona è un'altra persona. Gli scambi di prima del 12 ottobre 2026 restano come erano (dal 17 settembre al 12 ottobre chi entrava da Nostr era anonimo di serie, e quella promessa resta valida sul passato). Riconosciuto dall'altra persona, e dal server: come per tutti, il coordinatore ci dice fra quali due account è lo scambio (è la cronaca dei quaranta giorni, più sotto), e dal 10 ottobre 2026 l'esito dello scambio si scrive sul suo account — completato, o non completato se ha preso e non ha fatto il primo passo — col numero dell'ordine, per circa quattrocento giorni. Gli avvisi si spengono tutti dal cassetto «🔔 Avvisi» del profilo.
Dal 9 ottobre 2026, se accendi «🔔 Avvisami dei nuovi ordini P2P» (spento di serie), il server conserva le tue preferenze — quali tipi di ordine e da quale convenienza in su — e, per ogni ordine di cui ti ha avvisato, il suo numero accanto al tuo: serve a non avvisarti due volte dello stesso, e se ne va da solo dopo la finestra del libro. Chi ha pubblicato quegli ordini non lo sa. «Dimentica il profilo» porta via anche quelle righe.

<!-- pezzo schermata-027 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (10/17)

Dal 18 settembre 2026 gli avvisi sugli scambi nascono dal coordinatore, che facciamo girare noi: a ogni passo di uno scambio dice al server di Barattolo quale ordine, quale passo, fra quali due chiavi usa-e-getta, e chi dei due ha fatto il gesto — e da lì il server avvisa l'altra persona, con una frase che dice cosa è successo. Il prezzo lo diciamo per intero: il server ora sa a che punto è ogni scambio, e per chi usa Barattolo sa fra quali due account (le chiavi usa-e-getta le conosceva già). Non riceve gli importi, tranne i tre della chiusura — quanto valeva lo scambio, quanto è andato a chi compra e quanto ha bloccato chi vende, che servono alla frase «scambio concluso» — e non riceve mai fatture, recapiti né messaggi: quelli restano cifrati fra voi due. Questa cronaca si cancella da sola dopo quaranta giorni, e subito se dimentichi il profilo. Con questo è sparito l'avviso generico «Novità in un tuo scambio», e con lui due cose che esistevano solo per farlo funzionare: il server non guarda più sui relay le buste cifrate che il coordinatore ti manda, e il tuo telefono non gli dice più «sto facendo un gesto». Una cosa il telefono continua a dirla, solo se vendi: «ho indicato all'altra persona dove ricevere gli euro», col numero dell'ordine — serve ad avvisarla che tocca a lei, perché quel passo il coordinatore non lo vede. E se l'ordine ha più metodi, il telefono di chi lo prende ci dice quale ha scelto (il nome, per esempio «SEPA» o «ETH (Ethereum)»): serve ad avvisare chi l'ha pubblicato e a scrivere gli avvisi con la moneta giusta, e se ne va con la cronaca. Il recapito non passa da noi: l'IBAN, il RevTag o il numero viaggiano cifrati fra i vostri due telefoni, e nell'avviso non ci sono. I recapiti sono cifrati fra voi due. Se il tuo account è nato su Nostr, Barattolo non li può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo Barattolo potrebbe tecnicamente aprirli. Non lo fa. E dallo stesso giorno il recapito che hai ricordato non parte più da solo: lo trovi già scritto, e parte quando lo invii tu.
Dal 10 ottobre 2026, di ogni scambio chiuso — concluso o annullato — e di ogni ordine scaduto o ritirato senza essere preso, teniamo anche oltre i quaranta giorni i conti: il numero dell'ordine (che è pubblico), le date, come è finito, gli importi della chiusura, il metodo di pagamento e la cifra in euro del libro. Senza le persone: in quel registro non c'è il tuo account né una tua chiave, e chi ha scambiato con chi continua a cancellarsi come detto qui sopra. Il legame fra un ordine e te resta quello che il server annota già — quali ordini pubblichi e quali prendi — e «dimentica il profilo» lo cancella come sempre. Serve a sapere quanto lavora il servizio e quanto incassa di commissioni, e lo leggono solo gli amministratori di Barattolo.

<!-- pezzo schermata-028 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (11/17)

Dal 10 ottobre 2026 teniamo, legato al tuo account, come sono finiti i tuoi scambi: una riga per ogni scambio completato — a tutte e due le parti — e una per ogni scambio non completato, che si conta a chi ha preso un ordine e non ha fatto in tempo il suo primo passo (bloccare la garanzia se vende, dire dove ricevere i sats se compra), tanto che l'ordine è tornato in vetrina. Mai a chi ha aspettato, mai a chi si ritira prima che lo scambio parta. Dal 12 ottobre 2026, dove il servizio di scambio dà a chi pubblica più tempo di chi prende, si conta anche a chi ha pubblicato un ordine e, quando glielo prendono, non risponde in tempo o annulla dopo la presa: una sola volta per ordine, e mai se la presa è arrivata mentre i suoi ordini erano in pausa o nella mezz'ora prima. Di ogni presa rimasta senza risposta teniamo comunque una riga, che serve al segno «⚡ Risponde in fretta»: compare accanto al nome di chi, negli ultimi 30 giorni, ha concluso almeno tre scambi pubblicati da lui con tre persone diverse rispondendo di solito entro dieci minuti, e sparisce alla prima presa lasciata senza risposta. Si conta come non completato anche lo scambio in cui la garanzia arriva a scadenza (circa quattro giorni) perché chi compra non ha mai segnato gli euro come inviati, pur avendo ricevuto il recapito a cui mandarli. Se un tuo tentativo ti ha scusato teniamo una riga anche per quello, perché la scusa vale una volta ogni 30 giorni. E se un moderatore, chiudendo una disputa, segna la colpa a chi l'ha persa, teniamo una riga «disputa persa»: compare come «⚖️ N dispute perse» negli stessi posti del contatore, per 90 giorni e già dalla prima; in quei 90 giorni chi pubblica con un filtro non ti accetta, e quello scambio non vale come completato a chi l'ha persa. Chi la perde lo viene a sapere subito, nel messaggio che chiude la disputa. Ogni riga dice il numero dell'ordine, quando, se compravi o vendevi e com'è finita: niente importi. A cosa serve: al contatore «⚠️ N non completati», che conta solo gli ultimi 90 giorni e compare dal secondo (il primo si tollera), e al filtro di chi pubblica — «solo chi ha almeno 1, 3 o 5 scambi P2P completati» —, che guarda quanti ne hai completati e se ne hai di non completati negli ultimi 30 giorni. Chi lo vede: il contatore, quando c'è, lo vede chi vede te — accanto al tuo nome sugli ordini che pubblichi, nella pagina dello scambio o dell'ordine per l'altra persona, e nella pagina del tuo negozio; quanti scambi hai completato, dal 10 ottobre 2026, lo vede anche chi vede te, negli stessi posti («✅ 12 scambi P2P completati», accanto alle stelline): è il numero che aiuta chi sta per scambiare a decidere di chi fidarsi. Quanti ne hai di non completati sotto la soglia della scritta resta tuo, e chi pubblica col filtro non riceve altri numeri: se puoi prendere quell'ordine lo decide il server, e lo dice a te. Un giorno dopo la chiusura di uno scambio, se non hai lasciato la recensione, ti arriva un solo promemoria. Per quanto: circa quattrocento giorni, poi ogni riga si cancella da sola. Vale anche se entri con una chiave Nostr e prendi senza farti riconoscere: all'altra persona continuiamo a non dire chi sei, ma l'esito si scrive sul tuo account come per tutti. Perché uno scambio in cui ci hai provato non ti venga contato, il telefono ci dice anche i tentativi — hai aperto o copiato la richiesta della garanzia, toccato «Apri nel wallet», mandato una fattura che il coordinatore ha accettato o rifiutato, o incollato una che il telefono ha scartato: il gesto, mai la fattura né il pagamento —, e quelli se ne vanno con la cronaca, dopo quaranta giorni. «Dimentica il profilo» cancella subito i tentativi ma non gli esiti: sono del tuo account, come le recensioni, e non è da lì che ci si toglie un contatore.

<!-- pezzo schermata-029 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (12/17)

La pausa degli ordini, se la imposti, sta legata al tuo account: i giorni, le ore e il nome del tuo fuso orario (per esempio «Europe/Rome»), e niente altro. Serve a non far prendere i tuoi ordini dal libro di Barattolo nelle ore che hai scelto (restano visibili, in grigio), e a non contarti una presa arrivata mentre eri in pausa. Non esce da Barattolo, resta finché non la togli, e se ne va subito se dimentichi il profilo.
Il paracadute, se lo apri pubblicando un ordine, sta su quell'ordine: le soglie che hai scelto (se BTC sale, se scende), il prezzo di BTC che avevamo in quel momento e, se si apre, quando e a che prezzo. Serve a togliere l'ordine dal libro di Barattolo se il prezzo si muove oltre la soglia; l'annullamento vero lo firma il tuo telefono, noi quella firma non la facciamo. Se dimentichi il profilo di scambio lo cancelliamo.
Se togli uno scambio chiuso con la ✕, il server ricorda il numero dell'ordine e quando l'hai tolto, così sparisce anche dagli altri tuoi dispositivi. Si cancella da solo dopo quaranta giorni, e subito se dimentichi il profilo.
Dal 17 settembre 2026, quando un ordine viene preso, le due parti si vedono: chi ha pubblicato e chi ha preso vedono il profilo l'uno dell'altra — lo stesso che sta già sotto ogni annuncio del mercatino: nome, foto, stelline, livello e titolo — e i bottoni per scriversi su Telegram o su Nostr, ma solo dove quei canali esistono davvero (la npub soltanto se ne hai dimostrato il possesso). Prima della presa non si vede niente, e non c'è nessun altro modo di chiederlo: a questa domanda il server risponde solo a una delle due parti di quello scambio. Il perché è che dall'altra parte c'è una persona a cui stai per mandare dei soldi veri, e un volto con una reputazione è quello che rende pesabile la fiducia — la stessa ragione per cui nel mercatino chi vende ha un nome. Te lo diciamo prima: nel foglio dove pubblichi e in quello dove prendi. Al posto dei campi dove prima ci si scriveva il proprio contatto a mano, che non erano verificati da nessuno.

<!-- pezzo schermata-030 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (13/17)

Negli scambi l'altra persona vede il tuo profilo Barattolo: il nome e la foto che hai scelto, le recensioni, il livello, da quanto sei iscritto, gli scambi completati e non completati e, se li hai, il tuo @username Telegram e la tua chiave Nostr (npub), così potete scrivervi. Non vede mai il tuo numero di telefono, da dove ti colleghi, i tuoi recapiti né cosa hai comprato. Se vuoi scambiare senza profilo, entra con una chiave Nostr nuova. Vale con qualunque modo di entrare: anche chi entra con una chiave Nostr è riconosciuto dall'altra persona come tutti (dal 12 ottobre 2026) — chi ha pubblicato vede il suo profilo, e le due parti possono recensirsi. Una chiave Nostr nuova, per l'altra persona, è un'altra persona: non c'è un interruttore, e non c'è un modo di scambiare da Barattolo senza farsi vedere dall'altra parte. L'esito dello scambio si scrive sul suo account come per tutti — è il paragrafo qui sopra sugli esiti degli scambi —, e se arriva al contatore «⚠️ N non completati» quello compare dove compare lui: nella pagina del suo negozio e sugli ordini che pubblica. Gli scambi già presi prima del 12 ottobre restano come erano, e a cancellare il pregresso c'è «dimentica il profilo» — che toglie le prese annotate, non gli esiti. Chi entra con una chiave e pubblica, invece, si mostra — col profilo che ha qui, cioè il nome e la foto della sua chiave: è così da quando le card del libro hanno un volto, e il foglio dove si pubblica lo dice prima.

<!-- pezzo schermata-031 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (14/17)

Dal 12 ottobre 2026, dentro ogni scambio preso c'è una chat. La chat è cifrata fra voi due e Barattolo la trasporta. Se il tuo account è nato su Nostr, Barattolo non la può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo ritrovi scambio e chat su ogni dispositivo, e per questo Barattolo durante lo scambio potrebbe tecnicamente aprirla. Non lo fa. A fine scambio la chat si cancella, per tutti. Il moderatore la legge solo se una di voi due apre una disputa. Per intero. Ogni telefono fa nascere a caso una chiave usa-e-getta per quello scambio: non si ricalcola da niente. Perché tu ritrovi la chat se cambi telefono o browser, o se la memoria del browser si svuota, il telefono ne lascia sul nostro server una copia sigillata, chiusa con la chiave di quello scambio: la apre solo chi ha il tuo profilo di scambio, e il server la riconsegna solo a te — mai all'altra persona, mai a un moderatore. È qui la differenza, e conta dove è nato l'account, non come entri: il profilo di scambio di un account nato su Nostr lo ha solo lui; quello di un account nato con Telegram lo ricava il nostro server dall'account — anche quando poi entri con una chiave Nostr collegata —, ed è per questo che torna da solo su ogni dispositivo. I messaggi arrivano al nostro server già chiusi. Di ognuno il server vede su quale scambio, chi dei due l'ha spedito, a che ora, quanto pesa e fin dove l'altra persona ha ritirato: gli serve per consegnarlo e per avvisare. Il testo no. Lo stesso per le foto e i PDF che vi mandate (dal 16 ottobre 2026): partono cifrati dal telefono, con una chiave a caso che viaggia dentro il messaggio; del file il server vede solo quanto pesa, e lo cancella con la chat. Le foto partono ridisegnate, senza la posizione né gli altri dati della fotocamera; i PDF riscritti senza autore, programma, date e identificativo. L'avviso «hai un nuovo messaggio» non porta il testo. A scambio finito — concluso, annullato, o quando chi vende ha liberato i sats — i due telefoni buttano chiave e messaggi e il server cancella le buste, le copie sigillate e quegli orari: stanno in un archivio a parte che non entra nei backup, e nel registro del server non resta una riga per messaggio, solo quella di un avviso partito. Se una di voi due apre una disputa, il suo telefono chiude la chiave di lettura in una busta per i moderatori — lo legge scritto prima di confermare —; la apre solo il moderatore che prende la disputa, che legge e non può scrivere al posto vostro, e a disputa chiusa si cancella tutto allo stesso modo. Quello che non possiamo cancellare: quel che l'altra persona ha copiato o fotografato dal suo schermo.

<!-- pezzo schermata-032 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (15/17)

Le conversazioni fuori da Barattolo non sono nostre: se vi scrivete su Telegram o su Nostr quella chat è vostra e di chi la trasporta — non la leggiamo, non ce l'abbiamo, e in una disputa non possiamo usarla. A decidere sono i fatti dello scambio: chi ha bloccato i sats, chi ha detto di aver mandato gli euro, chi li ha liberati.
Dal 10 ottobre 2026, negli scambi in contanti di persona, ci sono «📍 Sono qui» e l'appuntamento. «Sono qui» lo tocchi tu, se e quando vuoi: il server riceve una nota firmata con la tua chiave usa-e-getta, con l'ora e — solo se il telefono la dà — la posizione (il telefono te la chiede, e si può dire di no); se la dai, ne ricaviamo subito la distanza dall'altra persona e dal luogo dell'appuntamento. L'appuntamento lo scrive chi vende nel recapito, che viaggia cifrato fra voi due: al server arrivano solo l'ora e le coordinate del punto, se l'indirizzo è stato riconosciuto — mai il testo. Mentre chi vende scrive l'indirizzo, i suggerimenti li chiediamo noi a Photon, che usa i dati di OpenStreetMap, mandando solo il testo cercato: né chi sei né dove sei; «Usa la mia posizione» non esce dal nostro server. Chi legge: l'altra persona vede l'ora delle tue presenze, mai la tua posizione; un moderatore vede il confronto se si apre una disputa. Posizioni e testi cercati non li scriviamo nei registri del server. Per quanto: le posizioni e il punto restano solo finché una disputa sui contanti è possibile — si cancellano quando i sats vengono liberati o lo scambio si chiude (annullato, scaduto, tornato nel libro), e in ogni caso entro quindici giorni; restano le ore e le distanze, che se ne vanno con la cronaca dopo quaranta giorni. Con «dimentica il profilo» se ne vanno anche le tue presenze e i tuoi appuntamenti; su uno scambio ancora aperto resta solo l'ora, perché l'altra persona l'ha già vista. Il GPS si può falsificare: per noi è una conferma, non una prova assoluta.
👤 Il tuo profilo di scambio
Gli ordini di scambio sono pubblici per come è fatto il coordinatore: vivono sui relay e li legge chiunque, e da settembre 2026 una copia sta anche sul nostro relay — serve a far vedere il libro degli scambi anche quando i relay del coordinatore non rispondono. Non c'è scritto chi sei: un ordine porta l'importo, il metodo di pagamento e una chiave usa-e-getta, diversa a ogni scambio. Dei messaggi che il coordinatore ti manda durante lo scambio — buste cifrate, che si aprono solo dal tuo telefono — sul nostro relay non teniamo copia: per un giorno, fra il 17 e il 18 settembre 2026, l'abbiamo tenuta per avvisarti più in fretta, e da quando gli avvisi li racconta il coordinatore non serve più. Le conversazioni fra te e l'altra persona invece non passano di lì: sono cifrate e viaggiano sui relay del coordinatore, e sul nostro non ne teniamo copia.

<!-- pezzo schermata-033 | schermata -->
## Schermata «I tuoi dati» · Se ti colleghi da Tor (16/17)

## Se ti colleghi da Tor
Barattolo si raggiunge anche da un indirizzo .onion, cioè da dentro la rete Tor. Quello che cambia è da dove risulta che ti colleghi: il nostro server non vede il tuo indirizzo IP e non lo scrive da nessuna parte, chi ti fornisce la connessione non sa che stai su Barattolo, e fra il tuo browser e noi non c'è nessun altro. Le foto, le pagine e tutto il resto restano dentro il tunnel.
Di là la pagina non porta lo script di Telegram: fuori non protegge nessuno — sei già su barattolo.store — ma da Tor sarebbe la contraddizione più grossa, perché sarebbe la prima richiesta a uscire col tuo indirizzo vero. Per la stessa ragione lì non c'è il bottone «Entra con Telegram» (funziona solo sul dominio normale) e si entra con una chiave Nostr.
Fin dove arriva, detto per intero: Tor nasconde da dove ti colleghi, non quello che scrivi. L'indirizzo di consegna, il punto di ritiro e l'email per il corriere li legge chi ti spedisce — è così su Tor e fuori, e non è una cosa che si perde scegliendo Tor: quella parte non è mai stata una questione di rete. Restano fuori dal tunnel anche i relay Nostr quando entri, il tuo wallet Lightning quando paga (parla per conto suo con la rete), e i collegamenti che portano altrove — la chat di Telegram, il profilo Nostr, il sito del corriere: sono link a case d'altri, e li apri tu quando li tocchi.
L'indirizzo è — per aprirlo serve il Tor Browser, o uno dei modi qui sotto.
## Cosa non facciamo
Nessun tracciamento. Niente analytics, niente pixel, niente cookie di terzi: nella pagina non c'è nessuno oltre a noi. Da agosto 2026 nemmeno i caratteri — prima li chiedevamo a Google, e a ogni apertura il tuo indirizzo IP arrivava a Google. Adesso stanno qui.
Un cookie solo, e serve a tenerti dentro se entri dal browser: contiene un numero casuale, e nel database c'è soltanto la sua impronta.
Non vendiamo niente a nessuno e non ti profiliamo. Non c'è pubblicità, quindi non c'è nessuno a cui rivenderti.
Non chiediamo email, password o numero di telefono per iscriverti. Un'email puoi lasciarla quando compri, o dopo dall'ordine, se vuoi il codice del locker dal corriere; un numero puoi scriverlo nell'indirizzo di spedizione, se vuoi che il corriere ti chiami: sono facoltativi tutti e due e spariscono con l'ordine. Un campo per il telefono, da solo, in Barattolo non esiste.
La connessione al tuo wallet non passa da qui. Se lo colleghi, resta sul tuo dispositivo e non arriva mai ai nostri server. Il Lightning address è un'altra cosa e ce l'abbiamo, se lo imposti: qui sopra c'è cos'è e per quanto.
Una cosa che facciamo e va detta: il server, come ogni server del mondo, vede l'indirizzo IP di chi si collega mentre gli risponde. Finisce nel registro tecnico della macchina — non nel database, non in un profilo, e non lo incrociamo con niente.

<!-- pezzo schermata-034 | schermata -->
## Schermata «I tuoi dati» · Quello che resta sul tuo telefono (17/17)

## Quello che resta sul tuo telefono
Alcune cose non arrivano mai qui: vivono nel tuo browser e se ne vanno se lo ripulisci. Sono il tema chiaro o scuro, la valuta con cui leggi i prezzi, e — le due che contano — la connessione al tuo wallet e la sessione con il tuo firmatario Nostr.
Due piccole cose invece le teniamo nel tuo profilo, perché ti seguano su ogni dispositivo: la dimensione del testo che hai scelto e quali avvisi hai già visto o chiuso — il giro di benvenuto, i «Non ora» dei suggerimenti, il cartello del giorno, e se hai acceso o spento gli effetti ridotti. Sono solo il nome dell'avviso e il momento in cui l'hai visto: servono a non mostrartelo di nuovo, anche dove il browser non ricorda niente fra un'apertura e l'altra. Dentro Telegram una copia sta anche nello spazio che Telegram riserva all'app per il tuo account.
## Cosa puoi fare adesso
Togliere la chiave Nostr dal profilo, o cambiarla.
Scegliere quale foto mostrare, o non mostrarne nessuna.
Scegliere dove ricevere gli avvisi, o spegnerli.
Mettere in pausa o cancellare i tuoi avvisi di ricerca.
Spegnere gli avvisi dei nuovi annunci, e smettere di seguire un venditore.
Togliere un punto di ritiro che avevi salvato.
Chiudere il negozio per ferie, e nascondere gli ordini conclusi.
Scaricare i tuoi affari in un file, dal Profilo.
## Chi contattare
Per qualsiasi cosa riguardi i tuoi dati — sapere cosa abbiamo, farlo correggere, farlo cancellare — scrivici in privato su Telegram. Risponde una persona, e le leggiamo tutte.
💬 Scrivici per i tuoi dati
🔗 Condividi questa pagina
 Questo documento è in costruzione.
 Barattolo è in rodaggio, e una cosa ancora non c'è: il
 titolare del trattamento. Finché non c'è, il contatto
 qui sopra non è un recapito formale — ma è vero, lo
 leggiamo e rispondiamo.
 E una cosa manca come strumento: cancellare l'account non si
 può ancora fare con un bottone. Quasi tutto lo puoi già
 togliere da solo dal Profilo, ma un gesto che cancella tutto in
 una volta non esiste — meglio dirlo che lasciarlo scoprire.
 E da novembre
 2026 c'è anche il gesto che toglie tutto in una volta:
 «🗑 Cancella il mio account», nel Profilo sotto la
 privacy, quando non hai niente in corso. Spariscono profilo,
 annunci, preferiti, chat e collegamenti; gli ordini e le
 recensioni già chiusi restano senza nome, come
 «Utente cancellato». Di te teniamo solo un'impronta del
 numero del tuo account — non il numero, e mai il telefono: un
 calcolo che non si rovescia — con la data, e le eventuali penalità degli
 scambi P2P: se torni, ritrovi quelle e nient'altro.

<!-- pezzo schermata-035 | schermata -->
## Schermata «Vendi (pubblicare un annuncio)» (1/3)

&#8592;

<!-- pezzo schermata-036 | schermata -->
## Schermata «Vendi (pubblicare un annuncio)» · Metti in vendita (2/3)

## Metti in vendita
✕
3 minuti e il tuo oggetto è nel mercatino. Pubblicare non costa nulla: il deposito di garanzia protegge ogni vendita.
 +Aggiungi foto (fino a 5)
 o trascinale qui
📷 Scatta foto
🖼️ Dalla galleria
Aggiungi almeno una foto per pubblicare
Le foto che carichi sostituiscono tutte quelle attuali. Non toccarle e restano com'erano.
Titolo
Categoria
 ElettronicaInformaticaTelefoniaAudio e videoConsole e videogiochiFoto e otticaBitcoinCasa e giardinoElettrodomesticiFai da te e utensiliAlimenti e bevandeBellezza e benessereAbbigliamentoScarpe e accessoriOrologi e gioielliBambiniSport e hobbyBicicletteMotoriAnimaliLibri e mediaMusica e filmStrumenti musicaliCollezionismoArte e artigianatoBuoni ed esperienzeLezioni e corsiLavoro e serviziAltro
▾
Sottocategoria (facoltativa)
▾
Condizioni dell'oggetto
 Scegli le condizioni…
 Nuovo — mai usato
 Come nuovo — in perfette condizioni
 In buono stato — usato ma ben conservato
 Accettabile — vissuto, segni d'uso evidenti
 Da sistemare — non funzionante o da riparare
▾
Prezzo
sats ⇄
Come vuoi ricevere per questo oggetto?
Vendita
 🔨Vendi all'astabase + durata: vince la puntata più alta
Il prezzo qui sopra diventa la base d'asta (solo sats). Un pezzo solo; la consegna è senza costi extra — la spedizione, se la offri, è inclusa nel prezzo. Chi punta versa subito nel deposito di garanzia; chi non vince viene rimborsato.
Quantità disponibile
Quanti pezzi uguali hai? Vuoto o 1 = un pezzo solo. All'esaurimento l'annuncio si mette in pausa: lo ricarichi dai tuoi annunci.
🎨 Varianti (facoltative)
 Prezzo o pezzi diversi per ogni variante
Chi compra sceglie prima di pagare e tu trovi la scelta nell'ordine.
Consegna — spunta le opzioni che offri
 🚚Spedizione
 🤝Ritiro in zona
 💾Invio del codice onlinebuono regalo, codice sconto, licenza
Se l'acquirente sceglie il codice, lo consegnerai dentro Barattolo dopo il pagamento: niente chat private, tutto tracciato. 💡 Fai uno screenshot datato del saldo o della validità prima di vendere: in caso di disputa, le prove decidono.
 🔑Abbonamento al mio canale Telegramogni mese: chi paga entra, chi non rinnova esce
Dopo il pagamento il link d'invito parte da solo. Quando chi compra entra nel canale l'acquisto è chiuso e i sats ti arrivano.
 📅È un serviziolezione, consulenza: una prestazione con una durata
💻 Online
📍 Di persona
minuti
Quanto dura, e che cosa comprende: scrivilo nella descrizione. Una prestazione si vende qui se è stabilita PRIMA — «un'ora di conversazione in inglese» sì, «ti sviluppo quello che ti serve» no: senza un perimetro, in disputa non si può decidere niente. Dopo il pagamento proponi tu giorno e ora, e chi ha comprato conferma.
unità/ordine
Quante unità accetti in UN ordine solo (es. 2 = un'ora, se l'unità è mezz'ora). Vuoto = nessun limite: chi compra sceglie quante ne vuole.
Costo di spedizione
Paese di casa
Italia
sats ⇄
Locker / punto
sats
Facoltativo, spesso costa meno. Vuoto = come a casa; 0 = gratis al punto.
 🌍 Spedizione internazionale

<!-- pezzo schermata-037 | schermata -->
## Schermata «Vendi (pubblicare un annuncio)» · Metti in vendita (3/3)

Dogana ed eventuale IVA sono a carico di chi riceve: non le incassi tu e non le anticipa Barattolo.
 Non spedisco in Italia
Lo paga chi compra, tu lo incassi per intero. Nel tuo paese vuoto o 0 = gratis. Nelle zone estere 0 = gratis e casella vuota = lì non spedisci. San Marino e Città del Vaticano contano come Italia.
💡 Indica nel Profilo (📦 Come spedisci) con quali corrieri spedisci: con Poste Italiane, SDA o InPost chi compra potrà scegliere anche un punto di ritiro.
Ogni pezzo in più: +
sats
Il primo pezzo costa il prezzo qui sopra; ogni pezzo in più aggiunge questa cifra. Lascia vuoto se spedisci tutto in un pacco solo.
Taglia del pacco
 Scegli la taglia…
 Busta — sta in una busta imbottita
 Piccolo — come una scatola di scarpe
 Medio — come una cassetta d'acqua
 Grande — come un forno a microonde
 Ingombrante — serve un furgone
▾
Zona (facoltativa)
Descrizione
🔕 Nessuno può scriverti: aggiungi uno username su Telegram (Impostazioni → Nome utente) per farti contattare da chi compra — o collega una npub nel Profilo.
Annulla la modifica
Cosa non si può vendere
⚡ Pubblica annuncio

<!-- pezzo schermata-038 | schermata -->
## Schermata «Profilo» · Il tuo profilo

## Il tuo profilo
Completa il profilo ▾
Annunci▾
📋I tuoi annunci▾
✏️ Modifica più annunci
📥Carica tanti annunci insieme▾
‹ Indietro
 Hai un catalogo grande? Compila il modello CSV (una riga = un
 annuncio, massimo 500 per volta) e caricalo qui. Ogni riga
 vuole almeno una foto, in due modi: URL nella colonna
 foto (più d'uno separati da |) oppure nomi di
 file dentro uno ZIP. Una riga senza foto viene scartata.
📄 Scarica il modello CSV
Il tuo file CSV
ZIP delle foto (se nel file hai scritto i nomi)
 Pubblica gli annunci anche su Nostr
🔎 Controlla il file
‹ Indietro
🏪 Catalogo esterno 
🔁Doppioni su Nostr ▾
Il tuo negozio▾
📊I numeri del negozio ▾
👁Guarda il tuo negozio›
🖼Banner del negozio ▾
🔗Link del negozio ▾
🌴Negozio in ferie ▾
🏪Cassa in negozio›
🎯Raccolte fondi›
</>Mettilo sul tuo sito›
🏪Pacchi al tuo punto ▾
Spedizioni e sconti▾
📦Come spedisci ▾
🚚Spedizione gratis ▾
🎁Sconto sugli articoli ▾
🎟Codici sconto ▾
🎀Premi fedeltà ▾
Quando compri▾
🫙Nel tuo barattolo ▾
🔎Avvisi di ricerca ▾
📍I tuoi punti di ritiro ▾
Wallet e incassi▾
⚡Lightning address▾
📥Come ricevi▾
On-chain▾
👛Wallet NWC (facoltativo)▾
La stringa di connessione (NWC)
⚡ Collega il wallet (NWC)
 Col wallet collegato paghi in un tocco («⚡ Compra
 subito»), e nel P2P la fattura per ricevere i sats la fa
 il wallet da solo. La stringa resta solo nel tuo
 browser: Barattolo non la vede mai. Nella app del
 wallet imposta un limite di spesa per questa
 connessione — e se ti serve solo per il P2P, creala col
 solo permesso di ricevere (make_invoice): così chi
 la rubasse non potrebbe spendere niente.
Livello e recensioni▾
⭐Recensioni ricevute ▾
🎖Livello e titolo ▾
💌I tuoi inviti ▾
🏅Distintivi ▾
🚀Rotta per la LunaIl tuo viaggio con Tappo: le tappe fatte e quelle davanti.›
🔩Caccia a Tappo›
Impostazioni▾
🔔Avvisi▾
🌗Aspetto▾
 Chiaro o scuro? Con Auto segue il sistema.
Auto
☀️ Chiaro
🌙 Scuro
 Quanto grande si legge Barattolo. La scelta ti segue su
 ogni dispositivo.
🆔Nostr e identità▾
🔐I tuoi dati›
💻Sessioni attiveDove è aperto il tuo account.›
📄Esporta i tuoi datiIl CSV dei tuoi affari conclusi, comodo per la contabilità.›
🧅Sito Tor▾
🗑Cancella il mio account›
Aiuto▾
🤖Chiedi a Tappo›
💬Assistenza›
🔒Come funziona il pagamento protetto›
Amministrazione▾
⚖️ Moderazione P2P
💬 Assistenza clienti
On-chain
Tutorial
Esci

<!-- pezzo schermata-039 | schermata -->
## Schermata «On-chain e finestre della Mini App» · On-chain (1/5)

## On-chain
✕
✕
↺ Rifai
✓ Usa questa foto
↻ Riprova
Scegli una foto dal telefono
Salta
Avanti
✕
## 
Fai un'offerta
 🔒
Acquista
Controlla e paga
Barattolo⚡
Esplora
P2P
Libro ordini
＋VendiPubblica
Aste
I miei scambi
Ordini
Info P2P
🌙
## Blocca sats a garanzia
 Paga con qualsiasi wallet Lightning. I sats restano bloccati e al sicuro finché non confermi di aver ricevuto l'oggetto.
Non hai sats? Compra da qui
lnbc…
inquadra il QR col wallet, o tocca la invoice per copiarla
👛 Non hai un wallet? Ti spieghiamo come fare
 ⚡ Apri nel wallet
⚡ Generane una nuova
✓ Ho pagato
Annulla
## Non hai sats?
## Come vuoi pagare?
## ⚡ Compra subito
 Stai per pagare sats
 dal tuo wallet collegato. I sats finiscono bloccati
 nel deposito di garanzia, come sempre: al venditore arrivano solo quando
 confermi di aver ricevuto l'oggetto.
⚡ Conferma e paga
Annulla
## 🔗 Condividi il barattolo
## 🔔 Avvisami se…
## 👤 Il tuo profilo di scambio
## 🔑 Metti al sicuro il profilo di scambio
## 🔑 La chiave di moderatore
&#8592;
## Vuoi comprare Bitcoin
 &#8592;
Per entrare oggi pubblica il tuo primo ordine. Dalle 10:00 di domani si prende.
## Vuoi comprare Bitcoin
## 🧾 Il PayCode
## 💶 L'importo esatto
## 📎 Il file della chat
Chiudi
## ⏳ Quando scade il PayCode
## ⏸ Pausa degli ordini
 ＋
&#10005;
## Stai comprando sats
 &#10005;
&#10005;
## ⚙️ Le leve
 &#10005;
## Filtro
## 📬 I tuoi avvisi
## Filtro
## Quanto vuoi scambiare?
## Le commissioni del P2P
Ho capito
## Lo scambio P2P
Qui compri e vendi sats in euro direttamente con un'altra persona: chi compra manda gli euro (bonifico, Revolut, contanti…), chi vende manda i sats.
Finché gli euro non sono arrivati, i sats restano bloccati in un deposito di garanzia: chi vende non può riprenderseli a metà strada.
Apri Barattolo su Telegram
Ho capito
## Cosa non si può vendere
Ho capito
## ⭐ Com'è andata?
## 🔒 Blocca i sats
## 🔒 Blocca i sats
## 🔑 Serve la chiave del tuo wallet
## 📍 Dove vedervi
## 🔐 Blocca la cauzione
## ⚖️ Incassa la cauzione
## 💸 Dove ricevere i sats
## 🤝 I vostri recapiti
## Vuoi uscire dal carrello?
Se lo salvi per dopo, lo ritrovi
 in Esplora, alla voce «Carrello». Se lo svuoti, si ricomincia da
 capo e non si torna indietro.
Salva per dopo
Svuota il carrello
Annulla
## ✖️ Annulli l'ordine?
✖️ Annulla l'ordine
Indietro
## 
Conferma
Annulla
## 📦 La tua prima spedizione
 Il deposito protegge i sats, non il pacco: se il corriere lo
 perde o lo rovina, il reclamo lo apri tu con lui.
 • Spedisci col tracciamento — è la prova che l'oggetto è
 partito ed è arrivato.
 • Per le cose di valore, compra la copertura del corriere:
 quella di base, verso i punti di ritiro, è molto bassa.
Ho capito
Come funziona il deposito

<!-- pezzo schermata-040 | schermata -->
## Schermata «On-chain e finestre della Mini App» · 📖 Come si spedisce? (2/5)

## 📖 Come si spedisce?
Imballa bene. Una scatola robusta, i vuoti riempiti
 (carta, pluriball) e il nastro sulle chiusure. Fai una foto
 all'oggetto e al pacco chiuso: in caso di disputa è una prova.
Compra l'etichetta. Dal sito o dall'app del corriere, o
 allo sportello. L'indirizzo o il locker di chi compra sono in
 cima all'ordine, in «📦 Spedisci a». Per le cose di valore
 aggiungi la copertura del corriere.
Consegna il pacco al corriere, al locker o all'ufficio
 postale, e conserva la ricevuta.
Segna come spedito qui nell'ordine, col numero di
 tracciamento: chi compra lo vede e segue il pacco. Puoi anche
 scegliere «Posta senza tracciamento», ma se il pacco si perde il
 rischio è tuo.
Quando il pacco arriva, chi compra
 conferma e i sats passano a te.
Ho capito
## 📦 Come spedirai?
 Seleziona con quali corrieri spedirai. Non è
 obbligatorio, ma con Poste Italiane, SDA o InPost chi
 compra potrà scegliere anche un locker o un punto di
 ritiro; con gli altri, o senza dichiararli, riceverà il
 pacco all'indirizzo che indica.
Salva e pubblica
Pubblica lo stesso
## 💰 Fai un'offerta
€
₿
✕
 sats
💰 Offri
## 🎁 Lascia una mancia
✕
 sats
⚡ Vuoi mandare anche uno zap a Barattolo?
Facoltativo: ci aiuta a tenere acceso il mercatino.
💡 La mancia va dritta al wallet del venditore: Barattolo non la tocca e non prende commissioni. È un regalo fuori dal deposito di garanzia, quindi non si rimborsa.
🎁 Manda la mancia
## sats 
inquadra il QR col wallet, o tocca la fattura per copiarla
 ⚡ Apri nel wallet
✓ L'ho pagata
Salta lo zap a Barattolo
## 🎯 Apri una raccolta
✕
 €
Quanto dura
 🛡️ Accetta anche depositi di garanzia
💡 L'obiettivo si fissa in sats al cambio di oggi. La guardano i moderatori prima della vetrina: niente quote, interessi, rendimenti o token, una raccolta è un sostegno. Gli zap arrivano dritti al tuo Lightning address.
🎯 Manda ai moderatori
## ⚡ Sostieni con uno zap
✕
 sats
 Non mostrare il mio nome
💡 Lo zap va dritto al wallet di chi raccoglie: Barattolo non lo tocca e non prende commissioni, quindi non si rimborsa.
⚡ Manda lo zap
## sats
inquadra il QR col wallet, o tocca la fattura per copiarla
 ⚡ Apri nel wallet
✓ L'ho pagata
## 🛡️ Sostieni con garanzia
✕
 €
💡 I sats restano in un deposito di garanzia 2-di-3 (tu, chi raccoglie, Barattolo) fino alla scadenza: vanno a chi raccoglie solo se i depositi arrivano all'obiettivo, sennò tornano al tuo wallet. Si paga on-chain, e la rete la paghi tu.
🛡️ Prepara il deposito
## sats
🔎 Ho pagato, controlla
Annulla il deposito
## 🏪 Cassa in negozio
✕
Importo libero (facoltativo)
€
I tuoi articoli
Incassa
🧾 Le vendite della cassa, in «Ordini»
💡 Chi compra inquadra il QR con qualsiasi wallet: non serve un account. I sats vanno dritti al tuo wallet, senza deposito di garanzia e senza commissioni: è un pagamento di persona, come al banco.
## Incassa sats
chi paga inquadra il QR col suo wallet, o tocca il testo per copiarlo
🔁 Gira verso il cliente
✓ Ricevuto
Nuovo conto
Annulla il conto
🏪 Torna alla cassa
✕
 sats

<!-- pezzo schermata-041 | schermata -->
## Schermata «On-chain e finestre della Mini App» · 💰 Offri per tutto il carrello (3/5)

## 💰 Offri per tutto il carrello
€
₿
✕
 sats
💰 Offri
## 🔨 Fai la tua puntata
 sats
Puntare = pagare: i sats vanno subito nel deposito di garanzia. Se vinci sono già il pagamento; se non vinci tornano indietro alla chiusura (o quando ti ritiri).
🔨 Punta
Annulla
## ⚡ Lancia un'offerta lampo
 %
Chi ha l'annuncio nel barattolo riceve l'avviso. Lo sconto vale per tutti finché dura; alla scadenza il prezzo torna pieno da solo.
⚡ Lancia
Annulla
## 🔑 Codici pronti
Incolla qui i codici o i link, uno per riga. Quando qualcuno paga, Barattolo gliene consegna uno da solo. I pezzi dell'annuncio diventano i codici pronti.
🔑 Aggiungi i codici
Togli i codici non consegnati
## 🔄 Rifornisci l'annuncio
 Quanti pezzi hai ora
 pezzi
È il numero che hai adesso, non quanti ne aggiungi. Non tocca nient'altro: gli affari in corso restano dove sono.
🔄 Rifornisci
Annulla
## 🚚 Aggiorna la spedizione
🚚 Aggiorna
Annulla
## ✏️ Modifica più annunci
## </> Widget per il web
Incolla questo codice nel tuo sito: mostra il tuo negozio e porta chi tocca qui su Barattolo.
L'altezza è quella che vedi nel codice: cambiala se ti serve. Il widget si adatta da solo alla larghezza che gli dai.
📋 Copia il codice del widget
👁 Guarda come viene
Chiudi
## 🔨 Rilancia l'asta
Per quanto tempo
L'asta riparte dalla stessa base, col cronometro a nuovo. Chi guardava riceve l'avviso quando manca un'ora.
🔨 Rilancia
Annulla
## ↩️ Riscuoti i tuoi sats
Incolla una invoice Lightning dell'importo esatto. Se hai un Lightning address nel Profilo, i rimborsi arrivano da soli e questo foglio non serve.
↩️ Riscuoti
Annulla
## 
Annulla
## 👥 I tuoi account
🚪 Esci da tutti
Chiudi
## 💻 Sessioni attive
Chiudi
## 🗑 Cancella il mio account
Per confermare scrivi CANCELLA
🗑 Cancella per sempre
Annulla
## 🫙 Ti aspettiamo su Telegram
 Apri il bot
…o entra con Nostr
Continua a guardare
## 🫙 Porta Barattolo in tasca
Chiudi
## Entra con Telegram
Nel bot tocca questa figura
Inquadralo col telefono: entra l'account aperto nel Telegram del telefono.
 Apri Telegram
🔄 Riprova
Chiudi
## 🧪 Collaudo privato
Un attimo…

<!-- pezzo schermata-042 | schermata -->
## Schermata «On-chain e finestre della Mini App» · Entra con Nostr (4/5)

## Entra con Nostr
 Dimostri di possedere la tua chiave firmando una sfida.
 La chiave privata non viene mai inviata a nessuno.
🔄 Riprova
📱 Entra con nostrconnect
 📲 Apri Amber e approva
 ⚠️ Non si è aperto nessun firmatario. Se hai Amber su questo telefono tocca di nuovo «Apri Amber e approva»; se no copia il link qui sotto, o inquadra il codice dal telefono dove firmi.
 📲 Riprova in un altro modo
📋 Copia il link
Con Amber su questo telefono basta il bottone verde: approva e torna qui, la risposta ti aspetta. Il codice serve solo se firmi da un altro telefono.
Se il firmatario ce l'hai su questo telefono il codice non lo puoi inquadrare da solo: copia il link, incollalo nell'app, approva e torna qui: la risposta ti aspetta. Su iPhone con Clave è più sicura la strada del bunker:// qui sotto (Clave firma senza che tu cambi app).
 Sto entrando…
🧩 Con l'estensione del browser
 🔗 Con un bunker remoto (NIP-46)
📱 Su iPhone con Clave è la strada che funziona meglio: in Clave apri Connect → Bunker, tocca Copy URI e incolla qui sotto. Clave firma da sola, senza che tu cambi app.
Collega il bunker
 🔑 Con la chiave privata (sconsigliato)
 La chiave resta SOLO su questo dispositivo, non viene mai inviata
 a nessuno, e da qui firma da sola i tuoi annunci su Nostr. «Esci»
 la cancella. Incollare una nsec resta la strada meno sicura: se
 puoi, usa l'estensione o il bunker.
Entra
 🎟 Hai un codice invito?
Scrivilo prima di entrare, in qualunque modo entri: si collega da solo.
 Non hai ancora un profilo Nostr?
Creane uno
Annulla
## 🌱 Crea il tuo profilo Nostr
 Su Nostr non c'è un account con email e password: c'è una
 chiave. La parte pubblica è il tuo nome (la npub), quella
 privata è la firma — e resta tua, non la vede mai nessuno.
 Barattolo non la vede mai: quando serve una firma la fa il
 tuo telefono o il tuo browser, e qui arriva già firmata.
📱 Dal telefono
 Un firmatario custodisce la chiave sul telefono e firma per
 te: è la strada più comoda se entri da qui, perché poi ti basta
 inquadrare il codice. Su Android c'è Amber, su
 iPhone c'è Clave.
1. Installa Amber (Android) o Clave (iPhone).
2. Aprilo e scegli di creare una chiave nuova.
3. Torna qui, tocca «Entra con nostrconnect» e inquadra il codice.
🤖 Scarica Amber (Android)
🍎 Scarica Clave (iPhone)
💻 Dal browser
 nstart.me ti prende per mano e crea la chiave passo passo,
 mettendola al sicuro.
1. Apri nstart.me e segui i passi.
2. Conserva la chiave privata dove la ritrovi: se la
 perdi non la rifà nessuno, nemmeno noi.
3. Torna qui: se hai installato un'estensione (Alby, nos2x)
 entri con «Con l'estensione», altrimenti col bunker
 che nstart ti propone.
🌐 Apri nstart.me
 Amber, Clave e nstart.me non sono di Barattolo: sono strumenti liberi
 del mondo Nostr, e la chiave che creano è tua e funziona con
 qualsiasi app, non solo qui.
Ho capito, torno all'accesso

<!-- pezzo schermata-043 | schermata -->
## Schermata «On-chain e finestre della Mini App» · 👛 Il tuo primo wallet (5/5)

## 👛 Il tuo primo wallet
I sats restano nel tuo wallet, non su Barattolo: li teniamo solo il tempo di un affare.
 Scarica Wallet of Satoshi
Gratis. I sats restano sul tuo telefono.
⚡ Scarica l'app
 Salva le parole di recupero
Scrivile su carta: servono se perdi il telefono.
 Hai già un altro wallet?
Va bene qualsiasi wallet con un indirizzo Lightning (nome@dominio), per esempio Blink o Coinos. Muun non ne ha uno. Quello di Phoenix Barattolo non lo sa ancora pagare: con Phoenix, a ogni vendita incolli una fattura.
Wallet of Satoshi è un'app di altri, non di Barattolo: non ci dà niente per consigliarla.
Ho capito
## Ti conosciamo già!
Usa l'account esistente
Annulla
## ✍️ Prima scrivi le 12 parole
## 🏅 Distintivi guadagnati
 Si guadagnano usando Barattolo: affari conclusi, feedback, identità verificate.
Chiudi
## Classifica Streak
 Chi apre Barattolo ogni giorno, senza saltarne uno. Non dà punti né premi.
Chiudi
↻
Un attimo, riprovo…
📡
Manca la rete, riprova
Riprova
Chiudi
✓ Invio sats in corso…

<!-- pezzo novita-001 | novita -->
## Novità · 2026-11-10 · come-ricevi

frase: Nel Profilo c'è una voce nuova, «📥 Come ricevi»: lì scegli in che forma ti arrivano i sats quando ti pagano in Lightning e quando ti pagano on-chain, senza cercarlo dentro la voce «₿ On-chain».
dove: Profilo → «📥 Come ricevi», con le due righe «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in».
leva: SWAP_AUTO_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-002 | novita -->
## Novità · 2026-11-10 · onion-location

frase: Se apri barattolo.store con Tor Browser, nella barra degli indirizzi compare «.onion disponibile»: un tocco e sei sul sito .onion di Barattolo, dove il server non vede il tuo indirizzo IP.
dove: Tor Browser, barra degli indirizzi su barattolo.store: la pillola viola «.onion disponibile».
leva: nessuna
pubblico: sì

<!-- pezzo novita-003 | novita -->
## Novità · 2026-11-11 · cifra-btc

frase: Quando paghi on-chain, accanto ai sats da mandare ora vedi anche la cifra in BTC (per esempio 0,00008128 BTC): la tocchi e la copi, pronta da incollare nel wallet. Nel pagamento di un ordine on-chain c'è anche «₿ Apri nel wallet», che apre il wallet con indirizzo e cifra già scritti.
dove: il foglio «Blocca … sats» del pagamento on-chain, «🔒 Blocca i sats» degli scambi P2P on-chain, la scheda «Cambio» e il riquadro «Caricali in Lightning» del P2P: la riga «In BTC» col bottoncino 📋.
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-004 | novita -->
## Novità · 2026-11-11 · foglio-oc-visto

frase: Quando paghi un ordine on-chain, appena la rete vede i tuoi sats la pagina del pagamento si chiude da sola: in «Ordini» l'ordine dice «Visto in rete, aspetto la conferma» invece di «Da pagare», e dopo una conferma, circa dieci minuti, diventa pagato.
dove: il foglio «Blocca … sats» del pagamento on-chain e la riga dell'ordine in «Ordini» (etichetta «In arrivo»).
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-005 | novita -->
## Novità · 2026-11-11 · seconda-firma-parla

frase: Nell'ordine on-chain il tasto «✍️ Metti la seconda firma» ora mostra l'anello mentre firma e alla fine dice com'è andata, o perché non ha firmato. Quando i sats sono partiti, l'ordine scrive «Il rimborso è partito» o «I sats sono partiti» col link alla transazione, e il tasto sparisce.
dove: la pagina di un ordine on-chain, nel riquadro ₿ «Pagato on-chain, in un 2-di-3».
leva: ONCHAIN_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-006 | novita -->
## Novità · 2026-11-11 · cambio-per-tutti

frase: La pagina «Cambio» è aperta a tutti: sposti i tuoi sats da Lightning a un tuo indirizzo bitcoin, o da bitcoin a Lightning, senza commissioni di Barattolo. Da 25.000 sats (50.000 da bitcoin verso Lightning) fino a 0,01 BTC a cambio, al massimo 5 cambi al giorno. E chi vende in Lightning sul mercatino può scegliere di ricevere on-chain.
dove: la scheda «Cambio» in basso, col tasto «🔁 Cambia»; per chi vende, il riquadro dell'incasso nella pagina dell'ordine.
leva: SWAP_ATTIVO e CAMBIO_LIBERO_ATTIVO accese per tutti dal 2026-11-11
pubblico: sì

<!-- pezzo novita-007 | novita -->
## Novità · 2026-11-11 · cambio-address-e-cifra

frase: Nel Cambio da bitcoin a Lightning non serve più creare a mano la richiesta nel wallet: incolli il tuo Lightning address (nome@wallet) e la richiesta della cifra giusta la chiede Barattolo al tuo wallet. E se preferisci crearla tu, la cifra esatta si tocca e si copia, pronta da incollare.
dove: la scheda «Cambio», direzione da bitcoin a Lightning, il campo «La tua richiesta Lightning».
leva: CAMBIO_BTC_LN_ATTIVO (nessuna leva nuova)
pubblico: sì

<!-- pezzo novita-008 | novita -->
## Novità · 2026-11-12 · card-p2p-coppia

frase: Le card del P2P si leggono al volo: in alto a destra due quadratini con la freccia dicono cosa invii e cosa ricevi (euro o USDT verso i sats, o il contrario), la faccia di chi ha pubblicato sta in fondo accanto alle sue stelline e ai suoi scambi, e il tempo che resta è la riga colorata sul bordo di sotto, che si accorcia e diventa arancio e poi rossa quando l'ordine sta per scadere.
dove: la scheda «P2P», le card del libro (Compra BTC e Vendi BTC, anche quelle on-chain).
leva: nessuna
pubblico: sì

<!-- pezzo novita-009 | novita -->
## Novità · 2026-11-12 · nome-swap

frase: La scheda «Cambio» ora si chiama «Swap»: è la stessa pagina, sposta i tuoi sats fra Lightning e il tuo indirizzo bitcoin. E da bitcoin a Lightning, se scrivi una cifra troppo piccola, l'app ti dice il minimo dal lato dove l'hai scritta: il minimo di 50.000 sats vale per quello che ricevi, quindi in «Mandi» serve un po' di più.
dove: la scheda «Swap» in basso, i riquadri «Mandi» e «Ricevi».
leva: CAMBIO_LIBERO_ATTIVO (nessuna leva nuova)
pubblico: sì

<!-- pezzo novita-010 | novita -->
## Novità · 2026-11-12 · p2p-onchain-500

frase: Negli scambi P2P on-chain ora si arriva fino a 500 € per ordine (prima 250 €), lo stesso tetto degli acquisti on-chain del mercatino. Gli scambi P2P in Lightning restano fino a 250 € durante la beta. E nelle card del libro, anche in quelle on-chain, toccando la faccia di chi ha pubblicato si apre il suo negozio, mai l'ordine.
dove: la scheda «P2P», il foglio «Pubblica» a rete on-chain e le card del libro.
leva: ONCHAIN_MAX_EURO (nessuna leva nuova; il P2P on-chain resta dietro ONCHAIN_SOLO_ADMIN)
pubblico: no

<!-- pezzo novita-011 | novita -->
## Novità · 2026-11-12 · usdt-novita-tutorial

frase: In cima al libro del P2P c'è un rettangolo verde «USDT · Novità»: toccalo e un breve tutorial ti mostra come riconoscere un ordine in USDT dalla T verde di Tether, come pubblicarne uno scegliendo USDT e la rete (Tron o Ethereum), e come si paga senza sbagliare rete. Si rivede quando vuoi, con lo stesso tocco.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: no

<!-- pezzo novita-012 | novita -->
## Novità · 2026-11-13 · usdt-foglio-presa

frase: Negli ordini P2P in USDT con un intervallo, quando scegli quanto scambiare il foglio ora parla USDT come la card: «Quanti USDT», la fascia in USDT, e i sats che ricevi contati al cambio del dollaro, gli stessi del conto che vedi subito dopo. Anche «come invii gli USDT», «Come funziona» e il cambio «1 BTC ≈ … USDT» nella pagina dell'ordine.
dove: la scheda «P2P», toccando un ordine in USDT con «scegli tu» nel libro.
leva: P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: no

<!-- pezzo novita-013 | novita -->
## Novità · 2026-11-13 · rete-scelta

frase: Negli scambi P2P, quando prendi un ordine con più metodi o più reti, la tua scelta arriva davvero all'altra persona: nella pagina dello scambio e in cima alla chat legge «ha scelto USDT su Tron» (o «SEPA Instant»), e le arriva un avviso su Telegram. Il recapito si può dare solo sulla rete scelta, e se ne arriva uno di un'altra rete la pagina lo dice in rosso prima che paghi.
dove: la scheda «P2P», la pagina dello scambio in «I miei scambi» (sotto il conto) e la chat dello scambio.
leva: nessuna
pubblico: sì

<!-- pezzo novita-014 | novita -->
## Novità · 2026-11-13 · fee-una-volta

frase: Il riquadro colorato delle commissioni in cima al libro P2P ora compare solo la prima volta, alla fine del tutorial, e poi non occupa più spazio sopra gli ordini. Si rivede rifacendo «Come funziona» fino in fondo, e la commissione resta sempre scritta nel conto di ogni ordine prima di prenderlo.
dove: la scheda «P2P», in cima al libro degli ordini; il bottone «Come funziona».
leva: nessuna
pubblico: no

<!-- pezzo novita-015 | novita -->
## Novità · 2026-11-13 · prezzo-btc-libro

frase: In cima al libro del P2P, sotto i rettangoli «Novità», c'è il prezzo di bitcoin aggiornato ogni minuto: quanto vale 1 BTC in euro, quanto è salito o sceso e una piccola linea, verde se sale e rossa se scende. Toccandolo passi dalle ultime 24 ore agli ultimi 7 giorni e agli ultimi 30 giorni, e toccando il simbolo € lo vedi in dollari.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: nessuna
pubblico: sì

<!-- pezzo novita-016 | novita -->
## Novità · 2026-11-13 · card-p2p-monete

frase: Nella home, nella fila «Scambi P2P», ogni ordine ora ha la sua moneta: un ordine in USDT si presenta con la sua card verde, il ₿ accanto alla T di Tether, e la cifra scritta in USDT, non più in euro. E in testa a «I miei scambi» c'è un disegno nuovo con tutte le monete insieme, il ₿ al centro.
dove: la home del mercatino (fila «Scambi P2P») e la pagina «I miei scambi».
leva: P2P_IN_VETRINA e P2P_USDT_ATTIVO (nessuna leva nuova)
pubblico: sì

<!-- pezzo novita-017 | novita -->
## Novità · 2026-11-14 · p2p-chf

frase: Nel P2P arriva il franco svizzero: si possono pubblicare e prendere ordini in CHF, pagati con TWINT, bonifico svizzero, Revolut, Wise o contanti di persona. La card dice CHF con la croce svizzera, il tetto della beta è quello degli euro convertito in franchi, e l'app controlla il numero TWINT e l'IBAN svizzero prima che partano.
dove: la scheda «P2P», il foglio «Pubblica» (valuta CHF), le card del libro e della home.
leva: P2P_CHF_ATTIVO (nuova, spenta) e P2P_CHF_SOLO_ADMIN
pubblico: no

<!-- pezzo novita-018 | novita -->
## Novità · 2026-11-14 · usdt-cifra-copia

frase: Negli scambi P2P in USDT, chi deve mandare gli USDT ora trova sotto l'indirizzo anche la cifra esatta da inviare, con il suo tasto «📋 Copia» accanto, come per l'indirizzo. Copia solo il numero, pronto da incollare nel wallet: niente più cifre riscritte a mano.
dove: la pagina dello scambio in «I miei scambi», nel riquadro «💵 Dove mandare gli USDT».
leva: nessuna
pubblico: sì

<!-- pezzo novita-019 | novita -->
## Novità · 2026-11-14 · banner-mappa-contanti

frase: La mappa dei contanti di persona ora è un tondo accanto alla campanella, in alto nel libro P2P: resta lì anche mentre scorri, e toccandolo si apre l'Italia coi pallini. In fondo alla mappa c'è «Numerino», spento di serie: acceso, il tondo mostra quante offerte in contanti nuove sono arrivate dall'ultima volta, e aprendo la mappa il numero sparisce.
dove: la scheda «P2P», la riga in alto con «Filtro», la campanella e il tema.
leva: nessuna
pubblico: sì

<!-- pezzo novita-020 | novita -->
## Novità · 2026-11-14 · mappa-mercatino

frase: Nel mercatino arriva la mappa del ritiro a mano: il tondo della mappa, accanto alla barra di ricerca, apre l'Italia coi pallini degli annunci da ritirare di persona. Ogni pallino sta al centro della città dell'annuncio, mai sull'indirizzo; tocchi una città e vedi solo i suoi annunci. Come nel P2P, il «Numerino» in fondo alla mappa conta i nuovi annunci.
dove: la home del mercatino (Esplora), il tondo della mappa accanto alla barra di ricerca.
leva: MERCATINO_MAPPA_RITIRO (nuova, accesa di serie)
pubblico: sì

<!-- pezzo novita-021 | novita -->
## Novità · 2026-11-14 · notifiche-telefono

frase: Nell'app di Barattolo (quella di Zapstore), nel sito aggiunto alla schermata Home e nel browser del PC ora puoi ricevere le notifiche come quelle di WhatsApp, anche ad app chiusa: ordini pagati o spediti, scambi P2P presi, messaggi. Si accendono da Profilo → Avvisi → «📲 Notifiche sul telefono», e con «Mandami una notifica di prova» vedi subito se arrivano.
dove: il Profilo, cassetto «🔔 Avvisi», la prima riga.
leva: WEB_PUSH_ATTIVO (nuova, accesa)
pubblico: sì

<!-- pezzo novita-022 | novita -->
## Novità · 2026-11-14 · avvisi-sconvenienti

frase: Gli avvisi dei nuovi ordini P2P ora si possono allargare anche agli ordini un po' meno convenienti del mercato: nella campanella, sotto «Convenienza», tocchi «Con un limite» e scegli fin dove ti va bene, da «Fino a 10% peggio» ad «Almeno 5% meglio». Così ti arrivano anche gli ordini quasi a mercato, ma non quelli troppo cari.
dove: la scheda «P2P», la campanella 🔔 in alto (e il cassetto «🔔 Avvisi» del Profilo).
leva: P2P_AVVISI_NUOVI_ORDINI (nessuna leva nuova)
pubblico: sì

<!-- pezzo novita-023 | novita -->
## Novità · 2026-11-14 · ordine-libro-ricordato

frase: Nel libro P2P l'ordine che scegli ora resta: se metti «Convenienza» o «Importo: dal più grande», alla prossima visita il libro si apre già ordinato così, in «Compra» e in «Vendi». La scelta resta salvata sul telefono; per tornare come prima basta rimettere «Più recenti».
dove: la scheda «P2P», la pillola con le tre righe in cima al libro («Ordina il libro»).
leva: nessuna
pubblico: sì

<!-- pezzo novita-024 | novita -->
## Novità · 2026-11-14 · feedback-modificabile

frase: Un feedback scritto di getto si può correggere: chi l'ha lasciato può modificarlo una volta (stelle e commento) o cancellarlo, entro 7 giorni da quando l'ha scritto; dopo resta definitivo. Vale nel mercatino e per le recensioni degli scambi P2P. Chi lo ha ricevuto viene avvisato, e sul profilo la riga dice «modificato». Cancellato è per sempre: su quell'affare non se ne lascia un altro.
dove: la pagina dell'ordine (scheda «Ordini») o dello scambio P2P, sotto il voto che hai lasciato: «✏️ Modifica» e «🗑 Cancella».
leva: FEEDBACK_MODIFICABILE (nuova, accesa di serie) e FEEDBACK_MODIFICA_GIORNI (7)
pubblico: sì

<!-- pezzo novita-025 | novita -->
## Novità · 2026-11-14 · recensioni-ricevute

frase: Le recensioni che hai ricevuto adesso hanno un posto tutto loro: nel Profilo c'è «⭐ Recensioni ricevute», con il numero accanto, e ci arrivi anche toccando le tue stelle in cima alla pagina. Dentro trovi le ultime recensioni del mercatino e degli scambi P2P, con chi le ha scritte e quando, proprio come le vede chi apre il tuo negozio.
dove: il Profilo, sezione «Livello e inviti», la prima riga (o un tocco sulle stelle sotto il tuo nome).
leva: nessuna
pubblico: sì

<!-- pezzo novita-026 | novita -->
## Novità · 2026-11-14 · invito-codice-sconto

frase: Chi vende può mandare il suo codice sconto a chi ha già comprato da lui: tocca «📣» sul codice, sceglie i clienti (già tutti spuntati) e preme «Invia invito sconto». Lo recapita Barattolo, sul bot, in DM Nostr o nell'app, e i contatti restano privati. Lo stesso codice arriva una volta sola, al massimo un invito a settimana per negozio; chi non vuole offerte le spegne negli Avvisi.
dove: Profilo → «🎟 Codici sconto» (il tasto «📣» sulla riga del codice) e Profilo → «🔔 Avvisi» (la riga «🎟️ Offerte dei negozi»).
leva: CODICI_SCONTO_INVITI (nuova, accesa di serie), CODICI_SCONTO_INVITI_GIORNI, CODICI_SCONTO_INVITI_MAX
pubblico: sì

<!-- pezzo novita-027 | novita -->
## Novità · 2026-11-14 · paycode-dopo-garanzia

frase: Con Barattozon il PayCode arriva a chi compra solo quando i sats di chi vende sono in garanzia. Prima, nella pagina dello scambio c'è solo il tempo che resta, con la frase «Il PayCode compare qui quando i sats sono in garanzia»: così nessuno va al tabacchino a pagare prima che i sats siano al sicuro.
dove: la pagina dello scambio in «I miei scambi», nel riquadro «🧾 Il PayCode».
leva: nessuna
pubblico: sì

<!-- pezzo novita-028 | novita -->
## Novità · 2026-11-14 · mancia-venditore

frase: Ti è piaciuto un affare e vuoi dare qualcosa in più al venditore? Ora puoi lasciargli una mancia: nell'ordine pagato c'è «🎁 Lascia una mancia», scegli quanti sats e li mandi dritti al suo wallet, senza commissioni. Nello stesso foglio puoi aggiungere, se vuoi, anche uno zap a Barattolo.
dove: la scheda «Ordini», dentro un ordine già pagato, accanto al voto.
leva: MANCIA_ATTIVA (nuova, accesa)
pubblico: sì

<!-- pezzo novita-029 | novita -->
## Novità · 2026-11-14 · prezzo-btc-scura

frase: La card del prezzo di bitcoin in cima al libro P2P ha una veste nuova, scura, che si stacca dagli ordini sotto. E in dollari ora è uguale a quella in euro: linea, percentuale e periodo restano, e il tocco cambia sempre fra 24 ore, 7 giorni e 30 giorni.
dove: la scheda «P2P», in cima al libro degli ordini (Compra BTC e Vendi BTC).
leva: nessuna
pubblico: sì

<!-- pezzo novita-030 | novita -->
## Novità · 2026-11-14 · mappa-ritocchi

frase: Il tondo delle mappe, nel P2P e nel mercatino, ora ha l'icona colorata 🗺️. E quando tocchi una città sulla mappa, la pagina scende da sola alle sue offerte o ai suoi annunci, senza doverli cercare sotto la mappa.
dove: la scheda «P2P» (il tondo 🗺️ accanto alla campanella) e l'Esplora del mercatino (il tondo 🗺️ in fondo alla barra di ricerca); un tocco su un pallino della mappa.
leva: nessuna
pubblico: sì

<!-- pezzo novita-031 | novita -->
## Novità · 2026-11-14 · mancia-senza-indirizzo

frase: Se il venditore non ha ancora un indirizzo Lightning, il riquadro della mancia ora c'è lo stesso e te lo dice, invece di sparire: «non ha ancora un indirizzo Lightning nel profilo: per ora la mancia non si può mandare». E chi vende, nello stesso ordine, vede l'invito ad aggiungerlo dal Profilo: così può ricevere le mance e incassare da solo.
dove: la scheda «Ordini», dentro un ordine già pagato, accanto al voto.
leva: MANCIA_ATTIVA (la stessa della mancia)
pubblico: sì

<!-- pezzo novita-032 | novita -->
## Novità · 2026-11-15 · cassa-negozio

frase: Hai un negozio, un banco al mercato o un bar? Nel Profilo c'è la «🏪 Cassa in negozio»: scrivi l'importo (in euro o in sats) o tocca i tuoi articoli, e Barattolo mostra un QR Lightning o on-chain. Il cliente lo inquadra con qualsiasi wallet, senza account. I sats vanno dritti al tuo wallet, senza commissioni, e i pezzi venduti escono da soli dalla vetrina.
dove: il Profilo, nel gruppo «Negozio e spedizioni», la voce «🏪 Cassa in negozio».
leva: CASSA_ATTIVA (nuova, accesa)
pubblico: sì

<!-- pezzo novita-033 | novita -->
## Novità · 2026-11-15 · cassa-negli-ordini

frase: Le vendite della «🏪 Cassa in negozio» ora stanno in «Ordini», insieme a tutto il resto, con il loro segno. Il filtro «🏪 Cassa» in cima mostra solo quelle, e un tocco riapre la ricevuta.
dove: la scheda «Ordini», il filtro «🏪 Cassa» accanto a «Vendite».
leva: CASSA_ATTIVA (la stessa della cassa)
pubblico: sì

<!-- pezzo novita-034 | novita -->
## Novità · 2026-11-16 · p2p-monete

frase: Nel P2P arrivano tre valute nuove: ETH, Monero e USDe. Funzionano come l'euro e l'USDT: scegli la valuta in cima a «Pubblica», sotto trovi solo le sue reti, l'importo lo scrivi nella moneta e i sats restano nel deposito di garanzia come sempre. Chi paga vede indirizzo controllato, QR, cifra esatta e il link all'explorer. USDe su Ethereum, Arbitrum, Base, BNB Chain e Solana.
dove: la scheda «P2P»: la valuta in cima al foglio «Pubblica», il filtro di ogni moneta nel libro e la card col suo logo.
leva: P2P_COIN_ATTIVO (nuova, accesa)
pubblico: sì

<!-- pezzo novita-035 | novita -->
## Novità · 2026-11-16 · bottone-tappo

frase: Nel bot di Barattolo c'è il bottone «💬 Chiedi a Tappo»: un tocco e sei nella chat di Tappo, che risponde alle domande su come funziona Barattolo. Il bot di Barattolo resta quello degli avvisi su ordini e pagamenti.
dove: il bot @ilbarattolobot, nel messaggio di benvenuto (/start) e nella risposta a chi gli scrive una frase.
leva: TAPPO_LINK (accesa di serie)
pubblico: sì

<!-- pezzo novita-036 | novita -->
## Novità · 2026-11-16 · nav-nostr

frase: La scheda «Swap» in basso adesso la vede anche chi apre Barattolo dal sito e non è ancora entrato: al suo posto prima c'era «Aste», che sono spente. Toccandola si entra con Telegram o con Nostr, e subito dopo si arriva alla pagina «Swap». E le aste hanno una casa nuova: la tessera «Aste» fra le categorie e una card quadrata in «Da scoprire», che portano alla pagina dove chiedere «🔔 Avvisami».
dove: la barra in basso del sito, prima del login; il foglio «Ti aspettiamo su Telegram» (su Tor «Entra nel Barattolo»); la home del mercatino, «Esplora per categorie» e «Da scoprire».
leva: SWAP_ATTIVO (nessuna leva nuova)
pubblico: sì

<!-- pezzo novita-037 | novita -->
## Novità · 2026-11-16 · supporto-profilo

frase: Nel Profilo c'è la sezione «Supporto», con le due strade per chi ha una domanda: «🤖 Chiedi a Tappo», che ti risponde subito su come funziona Barattolo, e «💬 Assistenza», la chat con lo staff, che prima stava in «Privacy».
dove: scheda Profilo, sezione «Supporto», voci «🤖 Chiedi a Tappo» e «💬 Assistenza».
leva: TAPPO_LINK accesa di serie
pubblico: sì

<!-- pezzo novita-038 | novita -->
## Novità · 2026-11-16 · p2p-onchain-commissione

frase: Negli scambi P2P on-chain la commissione ora è la stessa degli scambi Lightning, metà a testa e con gli stessi sconti per pionieri e livello 5: chi vende la deposita insieme ai sats, chi compra la trova tolta dai sats che riceve. La vedi nella riga «Fee P2P» del conto, già prima di prendere. Gli acquisti del mercatino restano senza commissioni.
dove: la scheda «P2P», un ordine on-chain del libro: il foglio «Stai comprando sats» / «Stai vendendo sats» col conto, e la pagina dello scambio.
leva: P2P_ONCHAIN_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

<!-- pezzo novita-039 | novita -->
## Novità · 2026-11-16 · p2p-tasti-rete

frase: Quando tocchi un ordine P2P, sotto «Stai comprando sats» o «Stai vendendo sats» ci sono già i due tasti «⚡ Lightning» e «₿ On-chain», accesi sulla rete dell'ordine. Se scegli l'altra rete vedi subito quanto costa lo swap e quanto ti arriva, prima ancora di prendere l'ordine, e il costo dello swap è una riga del dettaglio.
dove: la scheda «P2P», il foglio che si apre toccando un ordine del libro, Lightning o on-chain.
leva: P2P_ALTRA_RETE_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

<!-- pezzo novita-040 | novita -->
## Novità · 2026-11-16 · p2p-tasti-lato

frase: In cima al libro P2P «Compra BTC» e «Vendi BTC» sono due pillole grandi: quella accesa, verde o corallo, dice da che parte del libro sei. Anche nel tema scuro.
dove: la scheda «P2P», in cima al libro.
leva: nessuna
pubblico: sì

<!-- pezzo novita-041 | novita -->
## Novità · 2026-11-16 · ripubblica

frase: Quando pubblichi un ordine P2P c'è la sezione nuova «🔁 Ripubblica»: scrivi due prezzi di bitcoin, da X a Y. Se l'ordine scade senza che nessuno l'abbia preso e BTC è fra quei due prezzi, lo ripubblichiamo uguale, da solo, a ogni scadenza. Il bot ti dice ogni volta com'è andata. Lightning riparte appena apri Barattolo, on-chain subito. Vuoto = non succede niente.
dove: la scheda «P2P», il «+» per pubblicare: la sezione «🔁 Ripubblica» sotto il paracadute; la card del tuo ordine («🔁 Ripubblica da… a…») e la sua pagina, col tasto «Non ripubblicarlo più».
leva: P2P_RIPUBBLICA (nuova, accesa di serie)
pubblico: sì

<!-- pezzo novita-042 | novita -->
## Novità · 2026-11-16 · app-negozio

frase: La cassa in negozio diventa «Barattolo Negozio»: una pagina tutta per chi sta al banco, con lo stesso account di Barattolo e senza la barra del mercatino. Dentro trovi la Cassa e le Vendite della cassa. Dal browser, per esempio sul tablet del negozio, ci entri dritto con barattolo.store/?app=negozio.
dove: Profilo → «Negozio e spedizioni» → «🏪 Cassa in negozio»; si torna a Barattolo con «↩ Barattolo» in alto a destra.
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

<!-- pezzo novita-043 | novita -->
## Novità · 2026-11-16 · cassa-carrello

frase: La cassa di Barattolo Negozio adesso è fatta come il carrello: le card dei tuoi annunci con le foto, «Aggiungi» e poi − e +, e in fondo la barra col totale. Cambia solo il bottone: «Incassa», e i sats vanno dritti al tuo wallet, senza deposito di garanzia.
dove: Profilo → «Negozio e spedizioni» → «🏪 Cassa in negozio», scheda «🧾 Cassa».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

<!-- pezzo novita-044 | novita -->
## Novità · 2026-11-16 · p2p-onchain-valute

frase: Negli scambi P2P on-chain ora puoi farti pagare anche in franchi svizzeri, ETH, Monero o USDe: i bitcoin restano nel deposito a tre chiavi, e chi compra paga nella sua moneta. E gli ordini on-chain restano nel libro 7 giorni, come quelli Lightning.
dove: la scheda «P2P», il «+» con «On-chain»: la valuta in cima al foglio «Pubblica»; nel libro, il filtro della valuta vale anche per le card on-chain.
leva: P2P_ONCHAIN_ATTIVO spenta di serie (accesa per tutti in produzione dal 16 nov)
pubblico: sì

<!-- pezzo novita-045 | novita -->
## Novità · 2026-11-16 · p2p-monete-mercato

frase: Gli ordini P2P in ETH, Monero e USDe ora funzionano come quelli in euro: a prezzo di mercato i sats si fanno quando qualcuno prende l'ordine, al cambio di quel momento, e anche questi ordini si possono ripubblicare da soli con «🔁 Ripubblica».
dove: la scheda «P2P», il «+» con valuta ETH, XMR o USDe, a prezzo di mercato; la sezione «🔁 Ripubblica» del foglio.
leva: P2P_COIN_ATTIVO accesa di serie
pubblico: sì

<!-- pezzo novita-046 | novita -->
## Novità · 2026-11-16 · p2p-banner-tempo

frase: In cima al libro P2P ora ci sono tre rettangoli «Novità», ognuno col suo tutorial: On-Chain arancio, le stablecoin USDT e USDe in verde, ETH e Monero in blu. La card del prezzo di bitcoin è blu notte, e il tempo rimasto di un ordine è una riga con la barra, anche quando prendi un ordine on-chain.
dove: la scheda «P2P», in cima al libro; il foglio che si apre toccando un ordine, alla riga «Tempo rimasto».
leva: nessuna
pubblico: sì

<!-- pezzo novita-047 | novita -->
## Novità · 2026-11-16 · payjoin

frase: Negli acquisti on-chain del mercatino arriva il PayJoin: se il tuo wallet lo sa fare (Sparrow, BlueWallet, Wasabi, Bull Bitcoin, Cake Wallet), mentre paghi Barattolo aggiunge una sua moneta alla transazione. Più privacy per te, stessa cifra, e il deposito di garanzia riceve gli stessi sats. Se il wallet non lo sa fare, si paga come sempre.
dove: Il pagamento on-chain di un ordine: il QR e «₿ Apri nel wallet»; la riga «🔀 PayJoin» nel foglio dice quando c'è.
leva: PAYJOIN_ATTIVO (accesa di serie)
pubblico: sì

<!-- pezzo novita-048 | novita -->
## Novità · 2026-11-16 · notifica-apre-annuncio

frase: Toccando l'avviso di un annuncio, che arrivi dal bot, dal canale o come notifica sul telefono, adesso si apre la pagina di quell'annuncio, non più la home.
dove: gli avvisi «🔎 Un annuncio fa per te!», i post del canale, gli avvisi delle offerte e dei nuovi annunci, nel bot e nelle notifiche del telefono.
leva: nessuna
pubblico: sì

<!-- pezzo novita-049 | novita -->
## Novità · 2026-11-16 · p2p-mappa-recenti

frase: Nella home gli scambi P2P mostrano anche gli ordini on-chain (USDe, ETH, Monero compresi), col fulmine ⚡ o la ₿ in fondo alla card per dire subito la rete. Nel libro la mappa 🗺️ c'è sempre, «Più recenti» mescola on-chain e Lightning, scorrendo i rettangoli «Novità» diventano uno solo, e «🔁 Ripubblica» c'è anche in «Compra BTC» con Barattozon.
dove: la home, fila «Scambi P2P»; la scheda «P2P», in alto accanto alla campanella; la pillola «Ordina» con «Più recenti».
leva: nessuna
pubblico: sì

<!-- pezzo novita-050 | novita -->
## Novità · 2026-11-16 · esauriti-elimina-zona

frase: Un annuncio esaurito che non tornerà, come un oggetto usato venduto una volta, adesso si può eliminare: sparisce dal tuo negozio, mentre ordini e recensioni restano. E quando pubblichi un annuncio nuovo la «Zona» è già scritta con quella dell'ultimo, e la cambi quando vuoi.
dove: «I tuoi annunci» nel Profilo, il tasto «🗑 Elimina» accanto a «🔄 Rifornisci»; la pagina dell'annuncio esaurito, «🗑 Elimina l'annuncio»; il form «Vendi», campo «Zona».
leva: nessuna
pubblico: sì

<!-- pezzo novita-051 | novita -->
## Novità · 2026-11-16 · codice-ritiro

frase: Spedizioni a un locker o a un punto di ritiro: quando il codice per ritirare il pacco è pronto, chi ha comprato lo trova in cima all'ordine, subito sotto il prezzo. E chi vende sa fin dalla spedizione se il codice arriverà a lui, da incollare nell'ordine, o direttamente a chi compra.
dove: l'ordine, riquadro «📦 Istruzioni per il ritiro»; per chi vende il riquadro «📦 Spedisci» e il messaggio del bot alla spedizione.
leva: nessuna
pubblico: sì

<!-- pezzo novita-052 | novita -->
## Novità · 2026-11-16 · categoria-connettori

frase: Se colleghi un negozio Shopify o WooCommerce adesso puoi scegliere la categoria dei suoi prodotti: se vendi tutto dello stesso tipo la dichiari una volta e vale per tutti, anche per quelli già entrati. Se non la scegli, Barattolo usa la categoria del tuo negozio quando è una delle sue, invece di mettere tutto in «Altro».
dove: Profilo → «Il tuo catalogo» → «📥 Importa in blocco / catalogo esterno», ✏️ sul negozio collegato, casella «Categoria dei prodotti».
leva: nessuna
pubblico: sì

<!-- pezzo novita-053 | novita -->
## Novità · 2026-11-16 · posta-senza-tracciamento

frase: Chi vende può spedire con la posta senza tracciamento senza fingere una consegna a mano: la sceglie fra i corrieri quando segna la spedizione, e chi compra legge che il pacco non si può seguire. Se hai segnato «Consegna a mano» su un ordine che invece hai spedito, o hai scritto un codice sbagliato, nell'ordine c'è il bottone per correggerlo, e chi compra viene avvisato.
dove: l'ordine del venditore: «📦 Segna come spedito», la voce «✉️ Posta senza tracciamento»; sotto, il bottone «✏️ Correggi il tracciamento» (o «🚚 Era una spedizione?»).
leva: nessuna
pubblico: sì

<!-- pezzo novita-054 | novita -->
## Novità · 2026-11-16 · codici-uno-alla-volta

frase: Se compri più codici digitali nello stesso ordine (per esempio 10 buoni), adesso si aprono uno alla volta: provi il primo, tocchi «✅ Funziona» e vedi il successivo. Se un codice non funziona la disputa riguarda solo quello, e i codici mai aperti ti tornano: chi prova a imbrogliare rischia un codice, non tutto l'ordine. Chi vende scrive ogni codice nel suo riquadro.
dove: l'ordine di un codice online da 2 pezzi in su: per chi vende il form «Consegna i codici», per chi compra il pannello «🔓 Apri il codice 1».
leva: CODICI_UNO_ALLA_VOLTA (accesa di serie)
pubblico: sì

<!-- pezzo novita-055 | novita -->
## Novità · 2026-11-16 · backup-obbligato

frase: Prima del tuo primo scambio P2P on-chain, se le tue 12 parole non hanno ancora una copia (nel cloud di Telegram o sui relay Nostr), Barattolo te le mostra e te ne fa riscrivere tre: così i sats nel deposito di garanzia non restano mai chiusi da una chiave persa. Chi entra da Telegram o con Nostr di solito non vede niente di nuovo.
dove: Il P2P, quando pubblichi o prendi un ordine on-chain; Profilo → «₿ On-chain» → «Le ho scritte su carta».
leva: nessuna
pubblico: sì

<!-- pezzo novita-056 | novita -->
## Novità · 2026-11-17 · onchain-come-lightning

frase: Negli scambi P2P on-chain, quando i bitcoin sono nel deposito di garanzia, chi compra ha 24 ore per pagare in USDT, ETH, Monero o USDe e 72 ore in euro o franchi, col conto alla rovescia su card e pagina. A scambio concluso si lascia la recensione come negli scambi Lightning, il bot dice i sats netti, e lo scambio conta nei «✅ scambi P2P».
dove: «I miei scambi», la card on-chain e la pagina dello scambio (riga «Tempo per pagare», riquadro «⭐ Lascia una recensione»); il messaggio del bot «Scambio on-chain concluso!».
leva: nessuna
pubblico: sì

<!-- pezzo novita-057 | novita -->
## Novità · 2026-11-17 · primo-wallet

frase: Chi non ha ancora un wallet trova una guida in tre passi: scarica Wallet of Satoshi, salva le parole di recupero, poi il passo che ti serve: come mettere i primi sats e inquadrare il QR se stai pagando, dove trovare il tuo indirizzo Lightning se stai incassando. I sats restano nel tuo wallet, non su Barattolo. Al primo indirizzo salvato arriva il distintivo «📥 Pronto a incassare».
dove: Profilo, la casella verde «👛 Il tuo primo wallet» sotto i giorni di fila (finché non hai un Lightning address); e il bottone «👛 Non hai un wallet? Ti spieghiamo come fare» sotto la fattura da pagare, nel riquadro «💰 Come ricevi i tuoi sats» di un ordine e nel Profilo accanto al Lightning address.
leva: nessuna
pubblico: sì

<!-- pezzo novita-058 | novita -->
## Novità · 2026-11-17 · totali-acquisti

frase: Nel Profilo ora vedi anche quanto hai comprato: negli ultimi 30 giorni e da sempre, quanti acquisti e quanti sats hai pagato in tutto, spedizione compresa. Se non hai annunci il cassetto si chiama «I tuoi acquisti».
dove: Profilo → «Negozio e spedizioni» → «📊 Il tuo negozio» (o «📊 I tuoi acquisti»), sezione «🛍️ Acquisti conclusi».
leva: ACQUISTI_NEL_PROFILO spenta di serie (17 nov sera, privacy: Andrea «gli acquisti non li aggiungere»)
pubblico: no

<!-- pezzo novita-059 | novita -->
## Novità · 2026-11-17 · etichetta-alimenti

frase: Chi vende alimenti e bevande può aggiungere all'annuncio l'etichetta: peso netto, ingredienti, allergeni e tabella dei valori nutrizionali, come sulla confezione. Chi compra la legge nella pagina dell'annuncio prima di comprare, uguale per tutti, con gli allergeni in grassetto. È facoltativa, ma la legge europea la chiede per gli alimenti venduti online.
dove: Vendi → categoria «Alimenti e bevande» → riquadro «🏷️ Etichetta dell'alimento» sotto la descrizione; nella pagina dell'annuncio, la sezione «Etichetta» sotto la descrizione.
leva: ETICHETTA_ALIMENTI (accesa di serie)
pubblico: sì

<!-- pezzo novita-060 | novita -->
## Novità · 2026-11-17 · avvisi-barattolo

frase: Quando metti un articolo nel tuo barattolo 🫙 puoi scegliere cosa farti dire dal bot su quell'articolo: se il prezzo scende, se arriva uno sconto lampo, se ne resta solo uno, se torna disponibile. Al massimo un avviso al giorno per articolo, con il tasto che apre l'annuncio.
dove: il barattolino 🫙 sulla foto di un annuncio, poi il foglietto «🔔 Avvisami se…»; per cambiare idea, Profilo → «Nel tuo barattolo» → la 🔔 accanto all'articolo.
leva: AVVISI_BARATTOLO_ATTIVI (accesa di serie)
pubblico: sì

<!-- pezzo novita-061 | novita -->
## Novità · 2026-11-17 · spedisci-entro

frase: Quando vendi un oggetto da spedire, il messaggio del bot ti dice entro che giorno spedirlo, col tasto per aprire l'ordine. Nell'ordine trovi la stessa data e «📖 Come si spedisce?», una guida in quattro passi dall'imballo al tracciamento. Chi compra vede entro quando parte il pacco, e nei passi dell'ordine compaiono l'ora del pagamento e quella della spedizione.
dove: il messaggio «Hai venduto!» del bot; l'ordine del venditore, riquadro «📦 Spedisci» (riga «⏳ Spedisci entro…» e link «📖 Come si spedisce?»); i passi dell'ordine, per chi vende e per chi compra.
leva: nessuna
pubblico: sì

<!-- pezzo novita-062 | novita -->
## Novità · 2026-11-17 · link-packlink

frase: Quando devi spedire un ordine e non hai ancora l'etichetta, nel riquadro della spedizione trovi il link «Spedisci con Packlink»: compri l'etichetta là (Poste, BRT, InPost e altri, da 5,48 €, in euro) e incolli nell'ordine il codice del corriere.
dove: l'ordine venduto, riquadro «Spedisci e inserisci il tracciamento», sotto il campo del codice.
leva: nessuna
pubblico: sì

<!-- pezzo novita-063 | novita -->
## Novità · 2026-11-17 · chiedi-locker

frase: Se un venditore non spedisce ai locker o ai punti di ritiro, alla cassa la riga del locker adesso resta visibile, spenta, con il tasto «Chiedi al venditore se spedisce con InPost o Poste»: lui riceve un avviso dal bot (senza sapere chi ha chiesto) che lo porta a spuntare i suoi corrieri, e quando lo fa chi aveva chiesto riceve l'avviso. Una richiesta per venditore ogni 7 giorni.
dove: la cassa di un annuncio a spedizione di un venditore senza InPost, Poste o SDA, sotto «Spedizione a un indirizzo»; il messaggio del bot «Qualcuno vorrebbe ricevere … in un locker» col bottone «📦 Come spedisci».
leva: RICHIESTA_PUNTI (accesa di serie)
pubblico: sì

<!-- pezzo novita-064 | novita -->
## Novità · 2026-11-17 · onchain-controparte

frase: Negli scambi P2P on-chain ora vedi chi c'è dall'altra parte: appena l'ordine è preso, nella pagina dello scambio compare la sua scheda con faccia, nome e stelline, come negli scambi Lightning. Toccando la faccia si apre il suo negozio.
dove: P2P → «I miei scambi» → uno scambio on-chain preso, sotto la nota dello stato.
leva: nessuna
pubblico: sì

<!-- pezzo novita-065 | novita -->
## Novità · 2026-11-17 · onchain-annulla

frase: Negli scambi P2P on-chain chi compra può annullare con «✕ Annulla» finché chi vende non ha ancora depositato i sats, come negli scambi Lightning: prima bisognava aspettare la fine del tempo del deposito.
dove: P2P → «I miei scambi» → uno scambio on-chain preso, in attesa del deposito.
leva: nessuna
pubblico: sì

<!-- pezzo novita-066 | novita -->
## Novità · 2026-11-17 · barattozon-onchain

frase: Barattozon adesso c'è anche on-chain: in «Vendi BTC» col tabacchino puoi toccare «On-chain» in cima al foglio e pubblicare il tuo PayCode nel libro on-chain. Serve un PayCode che scade fra almeno 12 ore; chi prende l'ordine vede il codice solo quando i tuoi sats sono confermati nel deposito di garanzia, poi lo paga al tabacchino e tocca «Ho pagato al tabacchino».
dove: Il P2P, «Vendi BTC» → la capsula Barattozon (o il + col metodo «Contanti al tabacchino»), il tasto «On-chain» in cima al foglio; nello scambio il riquadro «🧾 Il PayCode da pagare al tabacchino».
leva: P2P_ONCHAIN_BARATTOZON (accesa di serie)
pubblico: sì

<!-- pezzo novita-067 | novita -->
## Novità · 2026-11-17 · livelli-carosello

frase: I tuoi livelli adesso si sfogliano: nel Profilo, sotto «Livello e titolo», ogni livello è una tessera da scorrere col dito. Sulla tua c'è l'anello con i tuoi XP sulla soglia del prossimo, i livelli già passati hanno la spunta, quelli davanti il lucchetto, e sotto vedi i vantaggi del livello che stai guardando: ✅ quelli già tuoi, 🔒 quelli da sbloccare.
dove: Profilo → «🎖 Livello e titolo» → «I vantaggi di ogni livello».
leva: nessuna
pubblico: sì

<!-- pezzo novita-068 | novita -->
## Novità · 2026-11-17 · stradina-obiettivi

frase: Nel Profilo c'è «🚀 Rotta per la Luna»: un tabellone lunghissimo dalla Terra alla Luna, su una mappa in otto zone raccontate da Tappo, fino all'halving del 2028. Ogni casella è una competenza (l'incasso automatico in Lightning, il wallet on-chain, la doppia configurazione Telegram + Nostr, il primo acquisto…): fatta, diventa una moneta d'oro e Tappo avanza. I tuoi amici sono pedine sul tabellone.
dove: Profilo → «Livello e recensioni» → «🚀 Rotta per la Luna».
leva: STRADINA_ATTIVA spenta di serie
pubblico: no

<!-- pezzo novita-069 | novita -->
## Novità · 2026-11-17 · contante-per-posta

frase: Nel P2P c'è un metodo in più, «Contante per posta»: chi compra sats spedisce le banconote a chi le vende, in una busta sigillata nascosta in un pacco, con un servizio tracciato. Le regole sono scritte nello scambio: chi spedisce filma l'imballo col numero di tracciamento in vista, chi riceve filma l'apertura prima di liberare i sats, e chi prende l'ordine blocca una piccola cauzione.
dove: P2P → «Pubblica» → «Altri metodi ▾» → «Contante per posta»; la pagina dello scambio con le regole; «Info P2P», voce «Contante per posta».
leva: P2P_POSTA_ATTIVO (nuova, spenta di serie: in produzione resta spenta per scelta di Andrea, accesa solo sul collaudo)
pubblico: no

<!-- pezzo novita-070 | novita -->
## Novità · 2026-11-17 · chat-onchain

frase: Anche negli scambi P2P on-chain adesso c'è la chat fra chi compra e chi vende, come nel Lightning: cifrata, con foto e PDF, da quando l'ordine è preso a quando i sats vengono liberati. Quando l'altra persona ti scrive, il bot te lo dice col tasto che apre dritto la chat; in una disputa il moderatore la può leggere, e a scambio finito si cancella.
dove: la pagina di uno scambio on-chain preso, riquadro «💬 Chat con …» in fondo (il richiamo «💬 Chat» in cima porta giù); il messaggio del bot «Hai un nuovo messaggio nello scambio on-chain» col bottone «🟠 Apri lo scambio».
leva: P2P_CHAT_SCAMBIO (la stessa della chat del Lightning, accesa di serie)
pubblico: sì

<!-- pezzo novita-071 | novita -->
## Novità · 2026-11-17 · serie-giorni

frase: Nel tuo Profilo c'è una fiamma che conta quanti giorni di fila hai aperto Barattolo, col tuo record e gli ultimi sette giorni. Basta entrare una volta al giorno. Se salti un giorno riparte da 1 e il record resta. Non dà punti né premi e la vedi solo tu: è solo la soddisfazione di non fermarla.
dove: Profilo, nel riquadro col tuo nome (riga «5 giorni di fila · record 12») e la fila dei sette giorni subito sotto; al primo accesso del giorno il saluto che compare in basso per un paio di secondi.
leva: SERIE_GIORNI_ATTIVA (accesa di serie)
pubblico: sì

<!-- pezzo novita-072 | novita -->
## Novità · 2026-11-17 · premi-fedelta

frase: I negozi possono premiare chi torna a comprare: nel Profilo, «🎀 Premi fedeltà», chi vende scrive fino a quattro soglie in euro col suo regalo («da 100 € la borsa, da 200 € la tazza»). Barattolo conta quanto ogni cliente ha speso lì e, passata la soglia, il premio compare sul suo ordine successivo: il venditore lo mette nel pacco. Sulla pagina del negozio vedi i premi e quanto hai già speso.
dove: Profilo → «🎀 Premi fedeltà»; la pagina di un negozio, riga «🎀 Premi fedeltà» sotto le promesse; il dettaglio dell'ordine, riga «🎀 Premio fedeltà»; il messaggio del bot «Premio fedeltà!».
leva: PREMI_FEDELTA_ATTIVI (accesa di serie)
pubblico: sì

<!-- pezzo novita-073 | novita -->
## Novità · 2026-11-17 · nip05-utenti

frase: Dal livello «Bottega avviata» puoi avere gratis il tuo nome verificato su Nostr, tipo mario@barattolo.store. Lo scegli nel Profilo, lo incolli nel campo NIP-05 del tuo profilo Nostr e le app Nostr mostrano la spunta accanto al tuo nome. Serve una chiave Nostr collegata con una firma.
dove: Profilo → «Impostazioni» → «🆔 Nostr e identità» → riga «✔️ Nome verificato su Nostr» → «Prendi questo nome» e poi «📋 Copia»; nella scala dei livelli, tra i vantaggi di «Bottega avviata».
leva: NIP05_UTENTI_ATTIVO (accesa di serie)
pubblico: sì

<!-- pezzo novita-074 | novita -->
## Novità · 2026-11-17 · caccia-a-tappo

frase: È arrivata la Caccia a Tappo, il gioco di Barattolo. Ogni giorno Tappo si nasconde in un annuncio vero, diverso per ognuno: leggi gli indizi, apri gli annunci e tocca «Tappo è qui?». Chi lo trova vince i bulloni 🔩, accende i barattoli della dispensa, sale di grado e completa le sfide. Coi bulloni prendi cappellini, attrezzi e 5 posti in più nei preferiti. Si gioca gratis: i bulloni non sono sats.
dove: Profilo → «Livello e recensioni» → «🔩 Caccia a Tappo», nella Mini App, nell'app e sul sito; il tasto «Tappo è qui?» nella scheda di ogni annuncio, quando la caccia del giorno è aperta.
leva: GIOCO_TAPPO_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-075 | novita -->
## Novità · 2026-11-17 · mondo-di-tappo

frase: Sul tabellone dei livelli arrivano le missioni di Tappo: otto scene brevi a carte sulla storia del denaro, il deposito di garanzia, le tue chiavi, Lightning, la privacy e Nostr, ognuna col bottone per farlo davvero. Danno bulloni 🔩 e montano il razzo con cui Tappo vuole arrivare sulla Luna. E nella Caccia a Tappo c'è il Mondo: la dispensa da girare, coi barattoli da aprire.
dove: Profilo → «Livello e recensioni» → «🚀 Rotta per la Luna»: la missione sta subito prima della casella che insegna; tutte anche nella «🔩 Caccia a Tappo», lì accanto, schede «Sfide» e «Mondo».
leva: GIOCO_TAPPO_ATTIVO spenta di serie
pubblico: no

<!-- pezzo novita-076 | novita -->
## Novità · 2026-11-17 · profilo-semplice

frase: Il Profilo è più semplice da leggere: ogni casella dice cosa c'è dentro. Ci sono «Annunci», «Il tuo negozio», «Spedizioni e sconti», «Quando compri», «Wallet e incassi», «Livello e recensioni», «Impostazioni» e «Aiuto».
dove: scheda Profilo, le caselle sotto il riquadro col tuo nome.
leva: nessuna
pubblico: sì

<!-- pezzo novita-077 | novita -->
## Novità · 2026-11-17 · raccolta

frase: Su Barattolo si può aprire una raccolta fondi in sats: un obiettivo, una scadenza fino a 60 giorni e una barra che si riempie. Chi vuole sostenerla manda uno zap, che va dritto al wallet di chi raccoglie, senza commissioni. Per aprirne una servono tre vendite concluse e un indirizzo Lightning; ogni raccolta la guardano i moderatori prima della vetrina.
dove: Profilo → «Il tuo negozio» → «🎯 Raccolte fondi» (lì il bottone «🎯 Apri una raccolta»); in vetrina la tessera «Raccolte» accanto ad Aste, quando c'è almeno una raccolta; nella scheda di una raccolta il bottone «⚡ Sostieni con uno zap».
leva: RACCOLTE_ATTIVE spenta di serie (e i depositi di garanzia, RACCOLTA_GARANTITA_ATTIVA, spenti di serie)
pubblico: no

<!-- pezzo novita-078 | novita -->
## Novità · 2026-11-17 · inglese-tappa-1

frase: Barattolo si legge anche in inglese: se il tuo Telegram o il tuo browser non sono in italiano, la vetrina, gli annunci e l'acquisto compaiono in inglese da soli, coi prezzi all'inglese (1,234.50 €). Ordini, P2P, Profilo e bot arrivano nelle prossime tappe. Per provarlo da un telefono italiano apri barattolo.store/?lingua=en (?lingua=it per tornare).
dove: tutta la Mini App e il sito per chi ha Telegram o il browser in una lingua diversa dall'italiano; la pagina «Il pagamento protetto» (barattolo.store/sicurezza) anche lei.
leva: LINGUA_INGLESE (spenta di serie dal 17 nov sera, scelta di Andrea: in produzione arriva spenta e si accende dal config; accesa sul collaudo)
pubblico: sì

<!-- pezzo novita-079 | novita -->
## Novità · 2026-11-17 · assistenza-screenshot

frase: Nella chat con l'assistenza di Barattolo ora puoi allegare anche degli screenshot, fino a tre per messaggio: lo staff vede subito cosa vedi tu, e può risponderti anche lui con uno screenshot. Li vedete solo tu e lo staff.
dove: Profilo → «Aiuto» → «💬 Assistenza», il bottone «📎 Allega screenshot» sotto la casella.
leva: ASSISTENZA_ATTIVA (quella dell'assistenza, già accesa)
pubblico: sì

<!-- pezzo novita-080 | novita -->
## Novità · 2026-11-17 · chiavi-dalle-parole

frase: Le chiavi degli scambi P2P adesso nascono dalle 12 parole del tuo wallet on-chain, le stesse che hanno già la loro copia nel cloud di Telegram o sui relay Nostr. Così, ovunque apri Barattolo con quelle parole, i tuoi scambi nuovi li governi da lì: telefono, Telegram Desktop o browser. Gli scambi già aperti continuano come prima, dal dispositivo dove li hai presi.
dove: lo scambio P2P (pubblicare o prendere un ordine); il foglio «Il tuo profilo di scambio» lo dice; se su un dispositivo le parole non ci sono, il primo gesto chiede di incollarle da Profilo → «Wallet e incassi».
leva: nessuna
pubblico: sì

<!-- pezzo novita-081 | novita -->
## Novità · 2026-11-17 · onchain-rimborso-liscio

frase: Rinunciare a uno scambio P2P on-chain è più semplice. Chi vende bitcoin scrive dove riavere i sats nel foglio stesso, prima di bloccarli. Se quell'indirizzo manca, il «Rinuncio» di chi compra non dà più errore: viene registrato e il bot avvisa chi vende col tasto che apre lo scambio. E se firmi da un dispositivo senza la chiave del wallet, Barattolo la cerca da solo o ti chiede lì le 12 parole.
dove: P2P on-chain: il foglio «🔒 Blocca i sats» col riquadro «Dove tornano i sats?»; la pagina dello scambio, tasto «↩️ Rinuncio: rimborsa chi vende»; il foglio «🔑 Serve la chiave del tuo wallet»; i messaggi del bot «Chi compra vuole rinunciare» e «Ora puoi rinunciare».
leva: nessuna
pubblico: no

<!-- pezzo novita-082 | novita -->
## Novità · 2026-11-17 · onchain-tempo-bonifico

frase: Negli scambi P2P on-chain in euro e franchi il tempo per pagare scende da 72 a 24 ore, come per USDT e monete. In cambio, da «Ho inviato» chi vende ha 48 ore per veder arrivare il bonifico e liberare i sats: se passano senza rilascio, il bot avvisa tutti e due e indica la disputa. Niente si annulla da solo: i bitcoin restano nel deposito di garanzia.
dove: P2P on-chain: la card in «I miei scambi» e la riga «Tempo per pagare» nella pagina dello scambio; nello stato «Euro inviati» la frase con le 48 ore; i messaggi del bot «Il tempo per pagare è finito» e «Sono passate 48 ore da «Ho inviato gli euro»».
leva: nessuna
pubblico: sì

<!-- pezzo novita-083 | novita -->
## Novità · 2026-11-17 · annullo-registrato

frase: Se prendi un ordine P2P, tocchi «Annulla» e l'annullo non arriva al coordinatore, alla scadenza del tempo non ti viene più contato uno scambio non completato: il bot te lo scrive nel messaggio.
dove: P2P Lightning: la pagina dello scambio appena preso, «✕ Annulla» e «Sì, annulla»; il messaggio del bot «Non hai proseguito in tempo» con la riga «Avevi chiesto di annullare».
leva: nessuna
pubblico: no

<!-- pezzo novita-084 | novita -->
## Novità · 2026-11-17 · onchain-ritiro

frase: Negli scambi P2P on-chain, chi si ritira dopo che l'altro ha già bloccato i sats si vede contare uno «scambio non completato», come negli scambi Lightning, e chi aveva bloccato i sats può lasciargli una recensione. Nessuna cauzione e nessuna penale in denaro. Il foglio di «Rinuncio» lo dice prima della firma. Non conta se chi vende non aveva ancora scritto dove pagare.
dove: P2P on-chain: il foglio «↩️ Rinunci allo scambio?»; la pagina dello scambio rimborsato, con la frase «scambio non completato» e il riquadro «⭐ Lascia una recensione» per chi aveva depositato; il messaggio del bot «Scambio on-chain annullato».
leva: nessuna
pubblico: sì

<!-- pezzo novita-085 | novita -->
## Novità · 2026-11-17 · quanto-vuoto

frase: Quando prendi un ordine P2P con un intervallo (per esempio da 50 a 276 €), il campo dell'importo ora è vuoto: scrivi subito la cifra che vuoi, senza cancellare il minimo che prima c'era già scritto. Sotto ci sono i tasti «Minimo» e «Massimo» per metterla con un tocco.
dove: P2P: tocca un ordine con un intervallo, poi «Scegli»; foglio «Quanto vuoi scambiare?».
leva: nessuna
pubblico: no

<!-- pezzo novita-086 | novita -->
## Novità · 2026-11-17 · onchain-contanti-luogo

frase: Gli ordini P2P on-chain in contanti ora hanno il luogo dello scambio, come quelli Lightning: chi pubblica scrive la zona, e la card la mostra con «📍». Vale anche lo stesso tetto in euro del contanti.
dove: P2P: «+», rete on-chain, metodo «Contanti», campo «Zona di scambio»; la card on-chain nel libro; il foglio che si apre toccandola.
leva: nessuna
pubblico: no

<!-- pezzo novita-087 | novita -->
## Novità · 2026-11-17 · onchain-contanti-scambio

frase: Lo scambio P2P on-chain in contanti ora va come quello Lightning: chi vende scrive dove e quando vedervi, chi compra apre il navigatore, ognuno può segnare «📍 Sono qui» quando arriva, e il bottone è «Ho consegnato i contanti».
dove: P2P on-chain con metodo «Contanti»: la pagina dello scambio, riquadro «📍 Dove vedervi» e, a sats bloccati, il riquadro con «📍 Sono qui»; il bottone «💵 Ho consegnato i contanti».
leva: nessuna
pubblico: no

<!-- pezzo novita-088 | novita -->
## Novità · 2026-11-17 · onchain-contanti-metodo

frase: Negli ordini P2P on-chain con «Contanti» insieme ad altri metodi ora scegli come pagare prima di prendere: con «Contanti» lo scambio va di persona, con appuntamento e «📍 Sono qui».
dove: P2P on-chain, tocca un ordine con più metodi fra cui «Contanti»: sotto il riassunto ci sono le pillole dei metodi.
leva: nessuna
pubblico: no

<!-- pezzo novita-089 | novita -->
## Novità · 2026-11-17 · paracadute-su-giu

frase: Il paracadute degli ordini P2P adesso ha due scelte: una se BTC sale e una se BTC scende, ognuna 5%, 10%, 20% o nessuna. Così puoi tenere l'ordine se BTC sale e toglierlo se scende, o il contrario. Gli ordini già pubblicati restano come sono.
dove: P2P, foglio «Pubblica» → «🪂 Paracadute», le righe «📈 Se BTC sale» e «📉 Se BTC scende»; sulla card del tuo ordine «🪂 Paracadute ↑10% ↓5%».
leva: P2P_PARACADUTE (quella del paracadute, già accesa)
pubblico: sì

<!-- pezzo novita-090 | novita -->
## Novità · 2026-11-17 · onchain-importi-grossi

frase: Per gli acquisti sopra 500 € la cassa ti propone da sola l'on-chain: nel «Come vuoi pagare?» On-chain porta «✅ Consigliato per questa cifra», perché con cifre così il Lightning spesso non passa. Il Lightning resta, con un avviso.
dove: Mercatino: un oggetto sopra 500 €, «Acquista», foglio «Come vuoi pagare?»; nel foglio della fattura Lightning la riga «⚠️ Sopra 500 € il Lightning spesso non passa».
leva: ONCHAIN_CONSIGLIATO_SOPRA_EURO accesa di serie (500)
pubblico: sì

<!-- pezzo novita-091 | novita -->
## Novità · 2026-11-17 · inglese-tappa-2

frase: Barattolo è tutto in inglese: ordini, scambio P2P, Vendi, Profilo, aste, raccolte, avvisi e assistenza compaiono in inglese da soli se il tuo Telegram o il tuo browser non sono in italiano, coi prezzi all'inglese (1,234.50 €). Mancano solo i messaggi del bot e l'interruttore della lingua nel Profilo, in arrivo. Da un telefono italiano apri barattolo.store/?lingua=en (?lingua=it per tornare).
dove: tutta la Mini App e il sito, per chi ha Telegram o il browser in una lingua diversa dall'italiano: Ordini, P2P, Vendi, Profilo, aste, raccolte, cassa in negozio, swap, on-chain, avvisi, assistenza, privacy.
leva: LINGUA_INGLESE (spenta di serie dal 17 nov sera, scelta di Andrea: in produzione arriva spenta e si accende dal config; accesa sul collaudo)
pubblico: no

<!-- pezzo novita-092 | novita -->
## Novità · 2026-11-17 · serie-classifica

frase: I giorni di fila adesso hanno una classifica: chi apre Barattolo da più giorni senza saltarne uno. Ci entri dal secondo giorno di fila, e a pari giorni si è a pari merito. La vede solo chi è entrato in Barattolo; se non vuoi comparire accendi «Non mostrarmi in classifica». Non dà punti né premi.
dove: Profilo, sotto la fila dei sette giorni, il bottone «Classifica Streak», con la fiamma. Per non comparire: Profilo, cassetto «Livello e recensioni», «🏆 Non mostrarmi in classifica».
leva: SERIE_GIORNI_ATTIVA (quella della serie, già accesa)
pubblico: sì

<!-- pezzo novita-093 | novita -->
## Novità · 2026-11-17 · onchain-grossi-uscita

frase: Negli acquisti on-chain sopra 500 € chi vende riceve on-chain anche se aveva scelto Lightning, perché con cifre così il Lightning spesso non passa. L'ordine glielo dice con «Cifra grossa: ricevi on-chain».
dove: Ordini → una vendita pagata on-chain sopra 500 €, riquadro «Pagato on-chain»; il messaggio del bot quando chi compra conferma.
leva: ONCHAIN_CONSIGLIATO_SOPRA_EURO accesa di serie (500)
pubblico: sì

<!-- pezzo novita-094 | novita -->
## Novità · 2026-11-17 · avviso-indirizzo

frase: Negli scambi on-chain chi vende sa quando chi compra ha scelto dove ricevere i sats: arriva un messaggio dal bot. E se tocca «Ricevuti» prima, Barattolo glielo dice e c'è «🔔 Ricordaglielo», che manda un promemoria a chi compra.
dove: P2P → «I miei scambi» → uno scambio on-chain con i sats nel deposito: la riga «⏳ Chi compra non ha ancora scelto il wallet» col bottone «🔔 Ricordaglielo», e il foglio di «Ricevuti: libera i sats»; il messaggio del bot «📍 Chi compra ha scelto dove ricevere».
leva: P2P_ONCHAIN_AVVISO_INCASSO accesa di serie
pubblico: sì

<!-- pezzo novita-095 | novita -->
## Novità · 2026-11-17 · barattozon-oc-compra

frase: Barattozon on-chain adesso c'è anche in «Compra BTC»: scegli il tabacchino, tocca «On-chain» e scrivi da quanto a quanto. Chi prende l'ordine scrive il suo PayCode; tu lo vedi quando i suoi sats sono nel deposito di garanzia e lo paghi al tabacchino.
dove: Il P2P, «Compra BTC» → metodo «Contanti al tabacchino», il tasto «On-chain» in cima al foglio; chi prende tocca «🧾 Il tuo PayCode» e scrive importo, PayCode e scadenza.
leva: P2P_ONCHAIN_BARATTOZON (accesa di serie)
pubblico: sì

<!-- pezzo novita-096 | novita -->
## Novità · 2026-11-18 · fiamma-giorno

frase: La prima volta al giorno che apri il Profilo, la tua serie te lo dice: il cerchio di oggi si accende piano come una brace e il numero dei giorni di fila sale da ieri a oggi. Una volta al giorno, e basta.
dove: Profilo, la riga «🔥 N giorni di fila» sotto il nome e la fila dei sette giorni, il cerchio «oggi».
leva: SERIE_GIORNI_ATTIVA (quella della serie, già accesa)
pubblico: sì

<!-- pezzo novita-097 | novita -->
## Novità · 2026-11-18 · reso-spese-venditore

frase: Se in disputa l'oggetto va restituito perché era rotto, bloccato o diverso dall'annuncio, il moderatore può decidere che la spedizione di ritorno la paghi il venditore: ti manda l'etichetta prepagata nella chat dell'ordine entro 3 giorni e tu non paghi niente. Se non arriva, con un tocco avvisi i moderatori, che possono rimborsarti subito.
dove: Ordini → un ordine in reso deciso così: il riquadro «↩️ Rispedisci l'oggetto per il rimborso» con «🏷️ Il reso lo paga il venditore», e dopo 3 giorni il bottone «⏰ Il venditore non ha mandato l'etichetta». Chi vende vede «🏷️ Il reso è a tue spese» con «💬 Manda l'etichetta in chat». Il moderatore ha il bottone «📦 Reso a spese del venditore» fra le decisioni della disputa.
leva: nessuna
pubblico: sì

<!-- pezzo novita-098 | novita -->
## Novità · 2026-11-18 · etichetta-obbligatoria

frase: Chi vende alimenti o bevande ora compila la tabella nutrizionale, come chiede la legge europea per la vendita online. Se per il suo prodotto non serve (frutta fresca, spezie, alcolici, artigianale in piccole quantità…) tocca «Non dovuta per legge» e sceglie il motivo, che chi compra legge nell'annuncio. Si possono aggiungere anche origine, conservazione, lotto e scadenza.
dove: Vendi → categoria «Alimenti e bevande» → riquadro «🏷️ Etichetta dell'alimento» (tabella, «Non dovuta per legge», Origine, Conservazione, Lotto, Scadenza); nella pagina dell'annuncio, la sezione «Etichetta» sotto la descrizione.
leva: ETICHETTA_OBBLIGATORIA (accesa di serie)
pubblico: sì

<!-- pezzo novita-099 | novita -->
## Novità · 2026-11-18 · bitcoin-only

frase: Nel filtro del P2P ci sono due pillole nuove: «No altcoin» toglie ETH e XMR, «No stablecoin» toglie USDT e USDe; accese tutte e due restano solo euro e franchi. Il telefono si ricorda la scelta. E ricorda: quelle monete servono solo a pagare, da noi si compra e si vende sempre bitcoin.
dove: P2P → «Filtro» → «Valute», le ultime due pillole «No altcoin» e «No stablecoin», poi «Applica». Spente di serie.
leva: P2P_BITCOIN_ONLY_ATTIVO (accesa di serie)
pubblico: sì

<!-- pezzo novita-100 | novita -->
## Novità · 2026-11-18 · ammanco-p2p-onchain

frase: Negli scambi on-chain un deposito con pochi sats in meno (succede con gli swap) non blocca più lo scambio: li copre il margine per la rete e si va avanti. Se ne mancano di più, chi ha depositato può toccare «↩️ Annulla e riprendi i sats» e riaverli sul suo wallet.
dove: P2P → «I miei scambi» → uno scambio on-chain preso: la riga «👀 Visti in rete … ne mancano N» e il bottone «↩️ Annulla e riprendi i sats» di chi ha depositato; il messaggio del bot «Sono arrivati N sats in meno».
leva: nessuna
pubblico: sì

<!-- pezzo novita-101 | novita -->
## Novità · 2026-11-18 · sottocategorie

frase: In Esplora le categorie hanno le sottocategorie: tocchi una categoria e si apre una tendina, con il numero di annunci accanto a ogni voce. Per esempio Informatica → Computer e portatili, oppure Tablet ed e-reader. E quando pubblichi Barattolo propone la sottocategoria leggendo il titolo; puoi cambiarla tu.
dove: Esplora → «Esplora per categorie», tocca una categoria: la tendina sotto la card («Tutta la categoria» e le sottocategorie con annunci); la card accesa scrive la scelta sotto il nome. Vendi → il campo «Sottocategoria (facoltativa)» sotto la categoria.
leva: SOTTOCATEGORIE_VETRINA (accesa di serie)
pubblico: sì

<!-- pezzo novita-102 | novita -->
## Novità · 2026-11-18 · premi-fedelta-2

frase: Premi fedeltà dei negozi: le soglie ora si scrivono in euro o in sats, e il regalo si sceglie fra gli articoli del proprio negozio. Chi ha un premio da riscuotere lo sa subito: glielo dicono il bot, la pagina del negozio e la scheda degli articoli. E ogni negozio vede la classifica dei suoi clienti per totale speso, in sats o in euro.
dove: Profilo → «🎀 Premi fedeltà»: l'interruttore «€ euro / ₿ sats», la tendina del regalo («✏️ Lo scrivo io» o un articolo 🎁), e sotto «🏆 I tuoi clienti» → «Guarda chi ha speso di più da te»; la pagina di un negozio, riga «🎁 Hai un premio da riscuotere»; la scheda di un articolo di quel negozio; i messaggi del bot «Premio fedeltà!», «Ordine pagato» e «Hai venduto».
leva: PREMI_FEDELTA_ATTIVI e CLASSIFICA_CLIENTI_ATTIVA (accese di serie)
pubblico: sì

<!-- pezzo novita-103 | novita -->
## Novità · 2026-11-18 · apri-esplora-annuncio

frase: Negli avvisi dei nuovi annunci ogni titolo adesso è un link: toccandolo si apre la pagina di quel prodotto. Se l'annuncio nuovo è uno solo, il bottone in fondo diventa «🫙 Apri l'annuncio»; «🫙 Apri Esplora» resta per sfogliare tutti i nuovi coi tuoi filtri.
dove: il bot, l'avviso «🆕 N nuovi annunci nel mercatino» e quello «🔔 … ha pubblicato» di un venditore che segui.
leva: nessuna
pubblico: sì

<!-- pezzo novita-104 | novita -->
## Novità · 2026-11-18 · vetrina-pulita

frase: I canali di Barattolo si puliscono da soli: quando un ordine P2P viene preso, annullato o scade, il suo post sparisce, così lì trovi solo ordini che puoi ancora prendere (l'annuncio venduto del mercatino resta, con «✅ Venduto»). E gli avvisi dei nuovi ordini P2P adesso dicono ordine per ordine se per te è un «🟢 Compra BTC» o un «🔴 Vendi BTC», e puoi sceglierli anche per metodo di pagamento.
dove: i canali Telegram di Barattolo; nel P2P la campanella 🔔 in alto (o Profilo → «🔔 Avvisi») → «Avvisami dei nuovi ordini P2P»: le chip «Compra BTC» e «Vendi BTC» e la sezione nuova «Metodo di pagamento»; il messaggio del bot «🔔 N nuovi ordini nel libro P2P».
leva: VETRINA_SI_PULISCE (accesa di serie)
pubblico: sì

<!-- pezzo novita-105 | novita -->
## Novità · 2026-11-18 · chiedi-annullo

frase: Negli scambi on-chain chi ha messo i sats nel deposito può chiedere a chi compra di annullare: il bot glielo scrive, e se è d'accordo tocca «Rinuncio» e i sats tornano indietro. Si chiede prima che chi compra dica di aver pagato.
dove: P2P → «I miei scambi» → uno scambio on-chain col deposito fatto: il bottone «🙏 Chiedi a chi compra di annullare».
leva: nessuna
pubblico: sì

<!-- pezzo novita-106 | novita -->
## Novità · 2026-11-19 · negozi-firma-ripiego

frase: Chi ha un negozio collegato e una chiave Nostr sua ha 3 giorni per firmare i suoi prodotti e pubblicarli a nome suo; se non lo fa, li pubblica Barattolo, così compaiono comunque su Nostr. Se firma dopo, tornano a nome suo da soli.
dove: nessun bottone nuovo: il titolare firma come sempre con «✍️ Firma i tuoi N annunci per Nostr» nel Profilo; passati 3 giorni succede da solo al giro del negozio.
leva: NEGOZI_FIRMA_RIPIEGO_GIORNI (3 di serie)
pubblico: sì

<!-- pezzo novita-107 | novita -->
## Novità · 2026-11-18 · negozi-su-nostr

frase: I prodotti dei negozi collegati (Shopify e WooCommerce) adesso escono anche su Nostr, come tutti gli altri annunci di Barattolo: un annuncio per prodotto, con le varianti (taglie, colori) raccolte in uno solo col prezzo «da». Si aggiornano da soli quando cambiano prezzo o disponibilità, e un prodotto tolto dal negozio sparisce anche da lì.
dove: nessun bottone: succede da solo a ogni giro del negozio (una volta all'ora); i prodotti si vedono in qualunque app Nostr che mostra gli annunci (NIP-99).
leva: NEGOZI_SU_NOSTR (accesa di serie)
pubblico: sì

<!-- pezzo novita-108 | novita -->
## Novità · 2026-11-18 · amber-da-solo

frase: Dal telefono entrare con Nostr è più comodo: tocchi «Entra con nostrconnect» e il tuo firmatario si apre da solo per chiederti l'ok, Amber su Android e Clave su iPhone. Approvi, torni su Barattolo e sei dentro, senza copiare e incollare nessuna stringa.
dove: dal sito nel browser, «…o entra con Nostr» → «📱 Entra con nostrconnect»; se l'app non si apre da sola, il bottone «📲 Apri Amber e approva» (su iPhone «Apri Clave e approva»). Dal computer resta il codice QR da inquadrare.
leva: NOSTRCONNECT_APRI_APP (accesa di serie)
pubblico: sì

<!-- pezzo novita-109 | novita -->
## Novità · 2026-11-18 · tempo-pagamento

frase: Nel P2P chi vende sceglie con un orologio quanto tempo ha chi compra per pagare, da 15 minuti a 24 ore (sotto le 24 solo coi metodi veloci, come SEPA Instant, Revolut o USDT). Chi prende lo vede già nel libro («⏱ 30 min»), e allo scadere senza «Ho inviato» lo scambio Lightning si annulla da solo e i sats tornano a chi vende; sull'on-chain si apre la disputa.
dove: P2P → «Pubblica» → «Vendi BTC», la sezione «Tempo per pagare» (il cursore con l'anello) sotto «Chi può prendere l'ordine»; sulla card del libro il bollino «⏱ …» per i tempi sotto le 24 ore; nel dettaglio dell'ordine la riga «Se lo prendi hai…»; nella pagina dello scambio il riquadro con l'anello.
leva: P2P_TEMPO_PER_PAGARE (accesa di serie); sull'on-chain compare con la promozione, sul Lightning solo dopo la -bar10 sul nodo (patch 0013): «pubblico» diventa sì quel giorno
pubblico: no

<!-- pezzo novita-110 | novita -->
## Novità · 2026-11-18 · cauzione-a-scelta

frase: Negli scambi P2P on-chain chi vende può chiedere una cauzione a chi prende il suo ordine, con qualunque metodo: una piccola cauzione in Lightning col QR (il 3%, almeno 1000 sats) che torna a fine scambio. Chi prende la perde se rinuncia dopo il deposito o se lascia scadere il tempo per pagare senza «Ho inviato», e metà va a chi vende.
dove: P2P → «Pubblica» → «Vendi BTC» a rete on-chain, la sezione «Cauzione di chi prende» («No» / «🔐 Chiedila») dopo «Tempo per pagare»; sulla card del libro il bollino «🔐 Cauzione»; nel foglio di chi prende la riga «Chi vende chiede una cauzione» e il foglio «🔐 Blocca la cauzione»; il foglio di «↩️ Rinuncio» lo ricorda.
leva: P2P_ONCHAIN_CAUZIONE_A_SCELTA (accesa di serie), ma vive sopra P2P_ONCHAIN_CAUZIONE e il suo macaroon (DA-FARE-ANDREA voce 20) e, a porticina chiusa, solo per i moderatori: «pubblico» diventa sì quando la cauzione on-chain si apre a tutti
pubblico: no

<!-- pezzo novita-111 | novita -->
## Novità · 2026-11-18 · annullo-chiesto

frase: Negli scambi on-chain, se chi vende chiede di annullare e chi compra accetta toccando «Rinuncio», a chi compra non si conta più nessuno «scambio non completato»: sta facendo un favore.
dove: P2P → uno scambio on-chain dopo «🙏 Chiedi a chi compra di annullare»: il foglio di «↩️ Rinuncio» non avvisa più del «non completato».
leva: nessuna
pubblico: sì

<!-- pezzo novita-112 | novita -->
## Novità · 2026-11-18 · connettori-ripartono

frase: Chi ha collegato un negozio Shopify o WooCommerce non deve più riaccenderlo a mano se il sito è rimasto giù per qualche ora: Barattolo riprova da solo una volta al giorno e, appena il negozio risponde, il collegamento riparte e il bot te lo dice.
dove: Profilo → «📥 Carica tanti annunci insieme» → «Catalogo esterno»: la riga del negozio fermo dice «⚠️ non risponde · riprovo da solo ogni giorno»; i messaggi del bot «Il collegamento col tuo negozio non risponde» e «Il tuo negozio risponde di nuovo».
leva: nessuna
pubblico: no

<!-- pezzo novita-113 | novita -->
## Novità · 2026-11-18 · apri-ordine-notifica

frase: Negli avvisi dei nuovi ordini P2P ogni riga adesso apre il suo ordine: tocca «🟢 Compra BTC» o «🔴 Vendi BTC» e si apre proprio quella card, anche se è on-chain. Se l'ordine nuovo è uno solo, il tasto in fondo diventa «🫙 Apri l'ordine»; con più ordini resta «🫙 Apri il libro ordini».
dove: il bot, l'avviso «🔔 N nuovi ordini nel libro P2P»; lo stesso tocco sulla notifica del telefono apre il primo ordine.
leva: nessuna
pubblico: sì

<!-- pezzo novita-114 | novita -->
## Novità · 2026-11-18 · sottocategorie-riga

frase: Le sottocategorie ora sono card disegnate come le categorie: tocchi Bitcoin e vedi subito tutti i suoi annunci, e sotto spunta una seconda riga con Hardware wallet, Cappellini, Spille e adesivi, Cover per telefono… ognuna col numero di annunci. Un tocco e filtri.
dove: Esplora → «Esplora per categorie», tocca una categoria: la seconda riga di card sotto la fila (solo le sottocategorie con annunci, che salgono a molla, ognuna con la sua icona disegnata), le altre categorie in grigio e la ✕ sulla categoria accesa. Ritoccando una sottocategoria torni a tutta la categoria; ritoccando la categoria, a Tutto.
leva: SOTTOCATEGORIE_VETRINA (accesa di serie)
pubblico: sì

<!-- pezzo novita-115 | novita -->
## Novità · 2026-11-18 · chiavi-ovunque

frase: Uno scambio P2P preso dalla web app ora si porta avanti anche dalla Mini App in Telegram o dal browser del computer, e viceversa: appena apri il P2P, ogni dispositivo usa le chiavi delle tue 12 parole. E il tasto «Apri lo scambio» del bot, su un ordine ripreso, apre lo scambio di adesso e non quello annullato prima.
dove: P2P → «I miei scambi» e il tasto «⚡ Apri lo scambio» degli avvisi del bot.
leva: nessuna
pubblico: sì

<!-- pezzo novita-116 | novita -->
## Novità · 2026-11-19 · scelte-negozio

frase: I prodotti dei negozi WooCommerce con una scelta che non cambia il prezzo (il gusto, il colore del nastro…) ora entrano come un annuncio solo, col titolo giusto e le sue tendine: chi compra sceglie prima di pagare, e la scelta arriva al venditore con l'ordine.
dove: la scheda di un prodotto importato da WooCommerce con tendine «Qualsiasi» (per esempio la Box Natale di Uhmami): le tendine sotto il prezzo, e di nuovo alla cassa in «🎁 Le tue scelte» (anche nel carrello). Il venditore la legge nella nota dell'ordine.
leva: nessuna
pubblico: sì

<!-- pezzo novita-117 | novita -->
## Novità · 2026-11-19 · filtri-p2p-ricordati

frase: Il Filtro del P2P ora si ricorda: valute, metodi, premio, reputazione e Lightning/on-chain restano come li hai lasciati anche quando esci e rientri.
dove: P2P → la pillola «Filtro» sopra il libro: scegli, tocca «Applica», esci e rientra. «Azzera» lo toglie. Vale su quel telefono o browser.
leva: nessuna
pubblico: sì

<!-- pezzo novita-118 | novita -->
## Novità · 2026-11-19 · fattura-rifatta-conto

frase: Se la fattura Lightning ti scade e la rigeneri dall'ordine, ora il foglio del pagamento ti rimostra il conto intero (articolo, spedizione, protezione e totale in sats) e, se il negozio regala la spedizione sopra una soglia, quanto ti manca per arrivarci.
dove: Ordini → un ordine «Da pagare» con la fattura scaduta → «⚡ Genera una nuova fattura»: le righe sotto il titolo del foglio, e la riga «🚚 Ti mancano … per la spedizione gratis».
leva: nessuna
pubblico: sì

<!-- pezzo novita-119 | novita -->
## Novità · 2026-11-19 · ritorno-nel-libro

frase: Nel P2P, se chi prende il tuo ordine non paga in tempo, l'ordine non sparisce più: torna nel libro uguale, e la garanzia torna a te. E il tempo per pagare parte solo quando dici dove vuoi gli euro, non prima. Sull'on-chain l'ordine rinasce nel libro anche quando chi l'ha preso annulla, non deposita o si ritira.
dove: P2P, uno scambio col tempo per pagare: alla presa il riquadro «⏱ Hai … per pagare» coi tre passi; nella pagina dello scambio l'anello che parte da «Indica dove ricevere gli euro» e la riga rossa negli ultimi dieci minuti; il bot avvisa dieci minuti prima della fine. Sull'on-chain l'avviso «🔁 Il tuo ordine è tornato nel libro» con «🚫 Non ripubblicarlo». Sul Lightning il ritorno nel libro arriva con l'aggiornamento del nodo.
leva: nessuna
pubblico: sì

<!-- pezzo novita-120 | novita -->
## Novità · 2026-11-19 · chiavi-dal-conto

frase: Uno scambio P2P preso dal sito si porta avanti anche dalla Mini App, e viceversa, senza fare niente: le chiavi degli scambi tornano dal tuo account, come prima del 17 novembre.
dove: P2P → «I miei scambi»: prendi un ordine dal sito, poi tocca «⚡ Apri lo scambio» nel bot. Nella Mini App i bottoni del passo ci sono, senza «Le chiavi di questo scambio non sono in questo browser».
leva: nessuna
pubblico: sì

<!-- pezzo novita-121 | novita -->
## Novità · 2026-11-19 · chiave-moderatore-dal-conto

frase: Per i moderatori: la chiave di moderatore ora segue l'account. Il dispositivo che ce l'ha ne lascia una copia chiusa col conto, e sul PC, sul sito o su un altro telefono arriva da sola alla prima apertura delle dispute.
dove: Pannello 👑 → «⚖️ Moderazione P2P»: aprila una volta dal dispositivo che ha la chiave, poi dall'altro; compare «🔑 La tua chiave di moderatore è arrivata anche qui» e i bottoni per prendere e decidere ci sono.
leva: nessuna
pubblico: no

<!-- pezzo novita-122 | novita -->
## Novità · 2026-11-19 · parole-casa

frase: Quando Barattolo ti chiede le 12 parole del wallet on-chain, ti dice da dove riprenderle: cloud di Telegram, browser del sito o relay Nostr.
dove: Profilo → «₿ On-chain»; nel foglio «🔑 Serve la chiave del tuo wallet» e nel riquadro «Il tuo wallet è su un altro dispositivo» la frase dice dove stanno le parole (cloud di Telegram, browser del sito, relay Nostr).
leva: nessuna
pubblico: sì

<!-- pezzo novita-123 | novita -->
## Novità · 2026-11-19 · cassetta-telegram

frase: Il wallet on-chain nasce sia dal sito sia dalla Mini App, ed è sempre uno solo. Le 12 parole raggiungono da sole il cloud di Telegram e, se hai Nostr collegato, i relay: Barattolo le porta chiuse e non le può leggere.
dove: Nato sul sito: apri Barattolo dentro Telegram una volta, poi riapri il sito, poi di nuovo la Mini App: le parole ci sono, senza incollarle. Con Nostr collegato: entra nel sito con la tua chiave Nostr e le parole arrivano anche lì.
leva: nessuna
pubblico: sì

<!-- pezzo novita-124 | novita -->
## Novità · 2026-11-19 · regole-sulla-card

frase: Nel P2P, quando apri un ordine col tempo per pagare, la prima cosa che leggi è quanto tempo avrai e di toccare subito «Ho inviato gli euro» dopo aver pagato, anche sugli ordini on-chain. E se prendi un ordine, il bot ti manda un messaggio col tempo che resta che si aggiorna da solo ogni minuto, senza suonare ogni volta.
dove: P2P → tocca una card col tempo per pagare: la riga «⏱ Se lo prendi hai …» in cima al foglio (on-chain: in cima a «Compra»). Dopo la presa, nel bot, il messaggio «⏳ Tempo per pagare: mancano …» con «Apri lo scambio».
leva: P2P_CONTO_ALLA_ROVESCIA (accesa di serie) per il messaggio del bot; la riga nel foglio nessuna
pubblico: sì

<!-- pezzo novita-125 | novita -->
## Novità · 2026-11-19 · riprendi-scaduto

frase: Negli scambi P2P on-chain, se chi ha preso il tuo ordine non tocca «Ho inviato gli euro» entro il tempo per pagare, puoi riprenderti i sats con un tocco su «↩️ Riprendi i sats»: Barattolo firma il rimborso senza aspettare un moderatore, tu metti la seconda firma, e l'ordine torna nel libro.
dove: P2P → «I miei scambi» → uno scambio on-chain col deposito fatto e il tempo per pagare finito: il bottone «↩️ Riprendi i sats», poi «✍️ Metti la seconda firma».
leva: P2P_ONCHAIN_RIPRENDI_SCADUTO (accesa di serie) con P2P_ONCHAIN_RIPRENDI_SCADUTO_SOLO_ADMIN chiusa di serie, cioè solo per i moderatori: «pubblico» diventa sì quando si apre a tutti
pubblico: no

<!-- pezzo novita-126 | novita -->
## Novità · 2026-11-19 · cauzione-tornata

frase: Negli scambi P2P on-chain con la cauzione, quando la cauzione ti torna il bot te lo dice: «La cauzione è tornata nel tuo wallet», con i sats.
dove: Il bot di Barattolo, dopo uno scambio on-chain chiuso in cui avevi bloccato la cauzione: il messaggio «🔐 La cauzione è tornata nel tuo wallet» con «Apri lo scambio».
leva: P2P_ONCHAIN_CAUZIONE spenta di serie (in produzione accesa solo per i moderatori)
pubblico: no

<!-- pezzo novita-127 | novita -->
## Novità · 2026-11-19 · onchain-passi

frase: Negli scambi P2P on-chain i passi sono quelli di uno scambio Lightning: chi vende scrive prima dove vuole gli euro, chi compra paga e tocca «Ho inviato gli euro», e solo allora chi vende vede «Ricevuti: libera i sats». E il bot avvisa appena la rete vede il deposito, prima ancora della conferma.
dove: P2P → «I miei scambi» → uno scambio on-chain: col deposito visto «Deposito inviato» senza più «Blocca i sats»; coi sats nel deposito, a chi vende «💶 Indica dove ricevere gli euro».
leva: nessuna
pubblico: sì

<!-- pezzo novita-128 | novita -->
## Novità · 2026-11-19 · meta-cauzione-auto

frase: Negli scambi P2P on-chain con la cauzione, se chi ha preso la perde, la metà che spetta a chi vende parte da sola verso il suo indirizzo Lightning del Profilo, senza aspettare un moderatore.
dove: Il bot di Barattolo: «🔐 Metà della cauzione di chi ha preso è tua: … in arrivo sul tuo wallet». Senza indirizzo Lightning nel Profilo il bot chiede di scriverlo, e la metà parte appena c'è.
leva: P2P_ONCHAIN_CAUZIONE_META_AUTO (accesa di serie, senza tetto: P2P_ONCHAIN_CAUZIONE_META_TETTO = 0); la cauzione stessa P2P_ONCHAIN_CAUZIONE, in produzione solo per i moderatori
pubblico: no

<!-- pezzo novita-129 | novita -->
## Novità · 2026-11-19 · contanti-oc-cinque-minuti

frase: Negli scambi P2P on-chain in contanti di persona i passi sono quelli del Lightning: chi compra consegna i contanti e tocca «Ho consegnato i contanti», poi chi vende li conta e libera i sats. E chi deve pagare riceve dal bot un promemoria anche a cinque minuti dalla fine del tempo.
dove: P2P → «I miei scambi» → uno scambio on-chain in contanti; il bot di Barattolo, promemoria «⏰ Mancano 5 minuti: hai già mandato gli euro?».
leva: nessuna
pubblico: sì

<!-- pezzo novita-130 | novita -->
## Novità · 2026-11-19 · bollini-home

frase: Le card «Scambi P2P» della home mostrano gli stessi bollini del libro: «⏱ 30 min» quando chi vende ha scelto un tempo per pagare sotto le 24 ore, e «🔐 Cauzione» quando chi pubblica un ordine on-chain la chiede a chi lo prende.
dove: Home (Esplora) → la fila «Scambi P2P»: i bollini sotto i metodi di pagamento.
leva: P2P_ONCHAIN_CAUZIONE per il solo «🔐 Cauzione» (in produzione solo per i moderatori); il «⏱» non ha leva
pubblico: sì

<!-- pezzo novita-131 | novita -->
## Novità · 2026-11-19 · notifica-account

frase: Se tieni aperti più account sullo stesso telefono, toccando una notifica Barattolo apre da solo l'account a cui è arrivata, e le tendine dei prodotti importati mostrano l'apostrofo giusto.
dove: Una notifica sul telefono per un account diverso da quello aperto: il tocco passa a lui («🔁 Apro …: l'avviso è suo») e apre la pagina dell'avviso. Le tendine «Scegli…» delle box importate da WooCommerce.
leva: nessuna
pubblico: sì

<!-- pezzo novita-132 | novita -->
## Novità · 2026-11-19 · avvisi-bz-lato

frase: Negli avvisi dei nuovi ordini P2P Barattozon è diventato un metodo di pagamento: così puoi farti avvisare solo degli ordini Barattozon in «Compra BTC», o solo di quelli in «Vendi BTC». Le scelte che avevi già fatto restano uguali.
dove: P2P → la campanella 🔔 (o Profilo → «🔔 Avvisi») → «Avvisami dei nuovi ordini P2P»: «Tipo di ordini» ha «Compra BTC» e «Vendi BTC», e «Barattozon» è la prima pillola di «Metodo di pagamento».
leva: nessuna
pubblico: sì

<!-- pezzo novita-133 | novita -->
## Novità · 2026-11-19 · push-attive

frase: Con più account sullo stesso telefono, la voce «📲 Notifiche sul telefono» ti dice per quale account arrivano: sugli altri trovi «Attiva qui», che le sposta su quello.
dove: Profilo → «🔔 Avvisi» → «📲 Notifiche sul telefono», su un account diverso da quello che riceve le notifiche: la nota «Su questo telefono ora arrivano le notifiche di un altro tuo account…» e il tasto «Attiva qui».
leva: WEB_PUSH_ATTIVO (accesa di serie)
pubblico: sì

<!-- pezzo novita-134 | novita -->
## Novità · 2026-11-19 · pubblica-col-tempo

frase: Negli scambi P2P Lightning, se chi vende ha scelto un tempo per pagare corto, quando qualcuno prende l'ordine ha lo stesso tempo anche lui per bloccare i sats, invece di tre ore: chi compra non resta ad aspettare.
dove: P2P → «I miei scambi» → lo scambio appena preso: «Chi ha pubblicato ha fino a 30 minuti per rispondere»; nel foglio «Pubblica», sotto «Tempo per pagare».
leva: nessuna
pubblico: no

<!-- pezzo novita-135 | novita -->
## Novità · 2026-11-19 · onchain-tempo-deposito

frase: Negli scambi P2P on-chain chi vende con un tempo per pagare corto ha lo stesso tempo per inviare il deposito quando qualcuno prende l'ordine (basta che parta, la conferma arriva dopo), e il tempo più corto da scegliere è 30 minuti.
dove: P2P → «Pubblica» → «Vendi BTC» on-chain → «Tempo per pagare» (il cursore parte da 30 minuti, e la nota sotto lo dice); nello scambio, il foglio «🔒 Blocca i sats»: «⏱ Basta che il deposito parta entro le …».
leva: P2P_ONCHAIN_DEPOSITO_COL_TEMPO (accesa di serie)
pubblico: sì

<!-- pezzo novita-136 | novita -->
## Novità · 2026-11-19 · recapito-nel-tempo

frase: Negli scambi P2P col tempo per pagare, anche chi vende ha quel tempo per dire dove vuole gli euro (o gli USDT): riceve i promemoria e vede quanto resta. Se non lo dice in tempo, su Lightning l'ordine torna nel libro, on-chain lo scambio si annulla e i sats tornano a lui; chi compra non deve mandare niente e non gli si conta niente.
dove: P2P → «I miei scambi» → lo scambio preso, sotto lo stato: «Hai ancora … per toccare «Indica dove ricevere gli euro»» (a chi compra: «Chi vende ha ancora …»); nel riquadro della presa, il primo passo dice anche il tempo di chi vende.
leva: P2P_RECAPITO_NEL_TEMPO (accesa di serie)
pubblico: sì

<!-- pezzo novita-137 | novita -->
## Novità · 2026-11-20 · conto-chi-aspetta

frase: Negli scambi P2P col tempo per pagare, anche chi vende riceve su Telegram un messaggio che si aggiorna da solo ogni minuto, «⏳ Chi compra ha ancora … per pagare»: sai quanto manca senza aprire l'app.
dove: Telegram, chat del bot: quando parte il tempo per pagare di chi compra (Lightning e on-chain), il messaggio «⏳ Chi compra ha ancora … per pagare» col bottone dello scambio.
leva: P2P_CONTO_ALLA_ROVESCIA (accesa di serie)
pubblico: sì

<!-- pezzo novita-138 | novita -->
## Novità · 2026-11-20 · sessioni-attive

frase: Nel Profilo c'è «💻 Sessioni attive»: vedi dove è aperto il tuo account (la Mini App e ogni browser in cui sei entrato) e chiudi quelle che non riconosci. Come su Telegram, da una sessione chiudi solo quelle aperte dopo; dalla Mini App le chiudi tutte.
dove: Profilo → gruppo «Impostazioni» → «💻 Sessioni attive».
leva: nessuna
pubblico: sì

<!-- pezzo novita-139 | novita -->
## Novità · 2026-11-20 · ritorno-da-solo-oc

frase: Negli scambi P2P on-chain è come sul Lightning: se il tempo per pagare finisce e chi compra non ha toccato «Ho inviato gli euro», Barattolo firma da solo il ritorno dei sats a chi vende, che mette la seconda firma, e l'ordine torna nel libro. Non vale col tabacchino e col contanti di persona.
dove: P2P → «I miei scambi» → lo scambio on-chain a tempo finito: «⏰ Il tempo per pagare è finito…» e il tasto «✍️ Metti la seconda firma»; prima di prendere, il riquadro «⏱ Hai … per pagare» dice «lo scambio scade e i sats tornano a chi vende, anche se hai pagato».
leva: P2P_ONCHAIN_RITORNO_DA_SOLO (accesa di serie)
pubblico: sì

<!-- pezzo novita-140 | novita -->
## Novità · 2026-11-20 · cassa-presenza

frase: In Barattolo Negozio la cassa al banco ha due cose nuove. Sul QR c'è «🔁 Gira verso il cliente»: il telefono mostra a chi paga solo la cifra, i pezzi e un QR grande, e quando paga compare «✅ Pagato, grazie!». E nella scheda «Vendite» c'è la chiusura di cassa di oggi o di ieri: vendite, sats, Lightning e on-chain, i pezzi usciti, e il riepilogo da copiare.
dove: Profilo → «🏪 Cassa in negozio» → «Incassa» → «🔁 Gira verso il cliente»; e la scheda «📒 Vendite» → «📒 Chiusura di cassa».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

<!-- pezzo novita-141 | novita -->
## Novità · 2026-11-20 · dettaglio-schede

frase: La pagina di uno scambio P2P è più ordinata: in alto tre schede, «📋 Passi», «💰 Importi» e «💬 Chat». Entrando vedi subito i passi, lo stato e il bottone da toccare; il conto e la chat sono a un tocco, con un pallino rosso quando ti hanno scritto.
dove: P2P → «I miei scambi» → uno scambio (Lightning o on-chain): le schede sotto il titolo «Nel dettaglio», ferme in alto anche scorrendo.
leva: nessuna
pubblico: sì

<!-- pezzo novita-142 | novita -->
## Novità · 2026-11-20 · pubblica-passi

frase: Pubblicare un ordine P2P adesso va a passi, una pagina alla volta: «1. Cosa», «2. Quanto», «3. Regole» e «4. Rileggi», col riepilogo prima di pubblicare. Si va con «Avanti →» e si torna con «← Indietro» o toccando un passo già fatto. La scelta fra ⚡ Lightning e ₿ On-chain resta in cima a ogni passo, e le scelte sono le stesse di prima.
dove: P2P → il + → «Pubblica» (Vendi BTC o Compra BTC). Con Barattozon il foglio resta quello di sempre, coi suoi passi.
leva: nessuna
pubblico: sì

<!-- pezzo novita-143 | novita -->
## Novità · 2026-11-20 · cassa-vetrina

frase: Barattolo Negozio adesso si apre sulla pagina del tuo negozio, uguale a quella che vede chi compra. Tocchi le card per mettere i pezzi nel conto, in fondo c'è la barra del carrello, e «Controlla e incassa» porta al conto e al QR: i sats vanno dritti al tuo wallet, senza deposito di garanzia.
dove: Profilo → «🏪 Cassa in negozio»: la vetrina del tuo negozio, la barra in fondo «Controlla e incassa», e in alto «📒 Vendite».
leva: CASSA_ATTIVA (accesa di serie)
pubblico: sì

<!-- pezzo novita-144 | novita -->
## Novità · 2026-11-20 · abbonamento-canale

frase: Su Barattolo si può comprare un mese di accesso al canale Telegram privato di un negozio. Paghi in sats, apri l'ordine e con «🔓 Rivela» trovi il tuo link d'invito personale: lo tocchi e il bot ti fa entrare. Per restare rinnovi ricomprando lo stesso annuncio, e Barattolo ti avvisa prima della scadenza.
dove: nella scheda dell'annuncio, la nota «🔑 Abbonamento di 30 giorni a…»; dopo il pagamento, l'ordine → «🔓 Rivela».
leva: ABBONAMENTI_CANALE (accesa di serie; attiva solo coi canali collegati in CANALI_ABBONAMENTO)
pubblico: sì

<!-- pezzo novita-145 | novita -->
## Novità · 2026-11-20 · app-negozio-sola

frase: Barattolo Negozio diventa un'app Android tutta sua, con la sua icona (due barattoli sul bancone di un mercato) e il suo nome. Si apre sulla cassa del tuo negozio, l'indietro la chiude invece di portarti al mercatino, e se non sei ancora entrato ti fa entrare col tuo account di Barattolo, con Telegram o con Nostr.
dove: Zapstore → «Barattolo Negozio» (accanto a Barattolo, stesso firmatario).
leva: CASSA_ATTIVA (accesa di serie)
pubblico: no

<!-- pezzo novita-146 | novita -->
## Novità · 2026-11-20 · ripubblica-semplice

frase: La ripubblica degli ordini P2P è più semplice: pubblicando ti chiediamo solo «Vuoi ripubblicarlo?». Con Sì, se nessuno prende l'ordine nei suoi 7 giorni, alla scadenza torna nel libro uguale, da solo, ogni volta. Se hai messo il paracadute, si ripubblica solo finché BTC resta dentro le soglie del giorno in cui l'hai pubblicato.
dove: P2P → il + → «Pubblica» → «3. Regole» → «🔁 Ripubblica».
leva: P2P_RIPUBBLICA (accesa di serie)
pubblico: sì

<!-- pezzo novita-147 | novita -->
## Novità · 2026-11-21 · filtri-negozio

frase: Se hai collegato il tuo negozio WooCommerce o Shopify, adesso scegli tu cosa entra su Barattolo: tutto tranne alcune categorie o tag, solo quelli che vuoi, o prodotto per prodotto. Il negozio resta sincronizzato ogni ora, e quello che togli non si cancella: va in panchina e lo riaccogli quando vuoi, con lo stesso annuncio.
dove: Profilo → «📥 Carica tanti annunci insieme / catalogo esterno» → il tuo negozio → «🧺 Cosa entra».
leva: CONNETTORI_NEGOZIO_APERTI (il cassetto dei negozi collegati)
pubblico: sì

<!-- pezzo novita-148 | novita -->
## Novità · 2026-11-22 · carica-prodotti-menu

frase: «Carica prodotti» è più semplice: scegli prima da dove arrivano i tuoi prodotti, da un file CSV, da Shopify o da WooCommerce, e si apre solo quello che ti serve, con «‹ Indietro» per cambiare. E sugli annunci che arrivano dal tuo negozio collegato il bottone dice «Rimuovi da qui»: spariscono da Barattolo, non dal tuo e-commerce.
dove: Profilo → «📥 Carica prodotti».
leva: CONNETTORI_NEGOZIO_APERTI (il cassetto dei negozi collegati)
pubblico: sì

<!-- pezzo novita-149 | novita -->
## Novità · 2026-11-22 · onchain-prodotti-costosi

frase: Sopra 500 € gli acquisti del mercatino si pagano solo on-chain, e chi vende riceve on-chain: con cifre così il Lightning non passa. Chi pubblica un oggetto sopra 500 € lo vede già in «Come vuoi ricevere», e l'annuncio dice «Preferisce ricevere on-chain». E il mercatino on-chain non ha più un tetto: anche un oggetto da 2 BTC si compra col deposito di garanzia 2-di-3.
dove: Mercatino: un oggetto sopra 500 €, «Acquista», foglio «Come vuoi pagare?» (Lightning spento con «Sopra 500 € si paga solo on-chain.»); Vendi, «Come vuoi ricevere per questo oggetto?» con «Sopra 500 € si riceve solo on-chain.».
leva: ONCHAIN_SOLO_SOPRA_SOGLIA accesa di serie (soglia ONCHAIN_CONSIGLIATO_SOPRA_EURO, 500)
pubblico: sì

<!-- pezzo novita-150 | novita -->
## Novità · 2026-11-23 · promozioni

frase: Adesso puoi far vedere di più quello che vendi, pagando in sats. Dalla scheda dell'annuncio, «Promuovi»: «In cima» lo riporta primo e lo fa riuscire nel canale Barattolo Vetrina, «In evidenza» lo mette nella nuova fila in home. Il tuo negozio può avere la sua card in «Da scoprire» per 30 giorni. E sul telefono «Da scoprire» scorre da sola.
dove: Scheda dell'annuncio → «Promuovi»; Profilo → cassetto del banner del negozio → «Promuovi»; home: la fila «In evidenza» sotto «Da scoprire».
leva: PROMOZIONI_ATTIVE (accesa di serie)
pubblico: sì

<!-- pezzo novita-151 | novita -->
## Novità · 2026-11-23 · barattozon-rinasce

frase: Anche gli ordini Barattozon on-chain in «Vendi BTC» tornano nel libro da soli se chi li prende annulla prima del deposito, con lo stesso PayCode, finché al PayCode mancano più di 8 ore.
dove: P2P → un tuo ordine Barattozon on-chain preso e annullato da chi l'ha preso → avviso «🔁 Il tuo ordine è tornato nel libro».
leva: P2P_ONCHAIN_BARATTOZON (accesa di serie)
pubblico: no

<!-- pezzo novita-152 | novita -->
## Novità · 2026-11-23 · profilo-mio

frase: Adesso puoi mettere su Barattolo un nome e una foto tuoi, gratis. Li guarda un moderatore, poi si vedono ovunque nel mercatino e nel P2P. Il tuo profilo Telegram o Nostr non cambia.
dove: Profilo → «🆔 Nostr e identità» → «✏️ Nome e foto su Barattolo» → «✏️ Scegli nome e foto»; approvati, la scelta «✏️ Mia» in «📷 La tua foto».
leva: PROFILO_MIO_ATTIVO (accesa di serie)
pubblico: sì

<!-- pezzo novita-153 | novita -->
## Novità · 2026-11-23 · nascondi-annuncio

frase: Adesso puoi nascondere un annuncio solo, senza mettere in ferie tutto il negozio e senza una data di rientro. Nella sua scheda tocca «🙈 Nascondi dalla vetrina»: nessuno lo vede più. Lo ritrovi in «I tuoi annunci», da dove con «👁 Rimetti in vetrina» torna quando vuoi.
dove: Scheda del tuo annuncio → «🙈 Nascondi dalla vetrina»; Profilo → «I tuoi annunci» → «👁 Rimetti in vetrina».
leva: NASCONDI_ANNUNCIO (accesa di serie)
pubblico: sì

<!-- pezzo novita-154 | novita -->
## Novità · 2026-11-24 · foto-varianti

frase: Le foto del tuo annuncio adesso si mettono in ordine con le frecce ◀ ▶ (la prima è la copertina), e ognuna può avere una breve descrizione che si legge a schermo intero. In «Modifica» le foto restano: ne aggiungi altre e togli quella che non vuoi. E ci sono le varianti: «Colore: rosso, blu, verde», anche con un prezzo e dei pezzi diversi per ognuna.
dove: Vendi → le foto (frecce ◀ ▶ e «Descrizione della foto (facoltativa)»), «🎨 Varianti (facoltative)» sotto la quantità, «Prezzo o pezzi diversi per ogni variante»; I tuoi annunci → Modifica → «Le tue foto (fino a 5)».
leva: nessuna
pubblico: sì

<!-- pezzo novita-155 | novita -->
## Novità · 2026-11-24 · avvisi-p2p-valute

frase: Negli avvisi dei nuovi ordini P2P adesso le valute si scelgono una per una, e puoi accenderne più di una insieme: per esempio «Euro» e «USDT». Ci sono anche Ethereum, Monero e USDe: un ordine in Monero ti arriva solo se hai acceso «Monero» (o lasciato «Tutte»).
dove: Libro P2P → la campanella 🔔 → «Valuta»; Profilo → «🔔 Avvisi» → «Valuta».
leva: P2P_COIN_ATTIVO (le monete; accesa di serie)
pubblico: sì

<!-- pezzo novita-156 | novita -->
## Novità · 2026-11-24 · home-card-pulite

frase: La home è più pulita. Le card degli scambi P2P sono più corte, col tempo per pagare e la cauzione come due icone, e accanto a «Scambi P2P» c'è un interruttore per nasconderle. Gli annunci in evidenza stanno sopra due onde arancio che scorrono mentre sfogli le card. Le offerte a tempo e gli sconti sono due banner dopo i primi sei annunci, e i negozi di «Da scoprire» si aprono subito.
dove: Esplora → «Scambi P2P» (l'interruttore accanto al titolo); la fila «In evidenza» sotto «Da scoprire»; i due banner fra gli annunci.
leva: nessuna
pubblico: no

<!-- pezzo novita-157 | novita -->
## Novità · 2026-11-24 · p2p-incasso-da-solo

frase: Nel P2P, quando compri sats e hai salvato un indirizzo Lightning negli incassi, non devi più dire ogni volta dove riceverli: l'app lo manda da sola appena prendi l'ordine, e lo scambio parte subito. Se l'indirizzo non passa, si apre il foglio di sempre.
dove: P2P → prendi un ordine di chi vende sats → «⚡ Ricevi su …»; per riceverli on-chain, «₿ Ricevi on-chain» nel foglio dell'ordine prima di «Compra»; Profilo → «⚡ Attiva incassi automatici» per salvare l'indirizzo.
leva: P2P_INCASSO_DA_SOLO (accesa di serie)
pubblico: no

<!-- pezzo novita-158 | novita -->
## Novità · 2026-11-24 · foto-in-fila-incolla

frase: Sul computer le foto del tuo annuncio stanno in fila, una accanto all'altra, e non scendono più per mezzo schermo. La descrizione di una foto adesso si legge anche sulla foto nella scheda dell'annuncio, non solo a schermo intero. E puoi incollare uno screenshot con Ctrl+V nell'assistenza e nella chat di un ordine, senza salvarlo prima.
dove: Vendi → le foto (sul computer); la scheda di un annuncio → la foto; Assistenza e chat dell'ordine → Ctrl+V nella casella.
leva: nessuna
pubblico: sì
