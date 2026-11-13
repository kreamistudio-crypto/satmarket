Libro del sapere di Barattolo, per l'assistente automatico del bot. Contiene solo cose pubbliche, le stesse che la Mini App e il sito dicono a chiunque. Le cifre che cambiano (commissioni, tempi, funzioni accese o spente) stanno nei NUMERI DI OGGI: se qui e lì non coincidono, valgono i NUMERI DI OGGI.

# Cos'è Barattolo

Barattolo è un mercatino fra persone, come un Subito.it, dove si paga solo in bitcoin: in satoshi («sats», la centesima milionesima parte di un bitcoin) sulla rete Lightning, che è veloce e costa quasi niente anche per pochi euro. Il prezzo si può leggere anche in euro con l'interruttore € / ₿, ma quello che viaggia sono sempre sats.

Barattolo ha due anime:
- il mercatino: si comprano e si vendono oggetti, servizi definiti e codici digitali, coi sats fermi in un deposito di garanzia finché chi compra non conferma di aver ricevuto;
- lo scambio P2P: si comprano e si vendono bitcoin con altre persone, per euro, coi sats bloccati in garanzia finché gli euro non sono arrivati.

Dove si trova:
- dentro Telegram, come Mini App: si apre dal bot @ilbarattolobot col bottone «🫙 Apri Barattolo»;
- sul sito barattolo.store, da qualunque browser;
- come app per Android, da Zapstore o dalle release su GitHub (con Obtainium si aggiorna da sola). L'app è una finestra su barattolo.store: dentro non c'è niente di diverso. Per controllare che sia proprio quella ufficiale c'è AppVerifier: le due righe da incollare sono nella pagina «Il pagamento protetto» (barattolo.store/sicurezza);
- su Nostr: gli annunci vengono pubblicati anche lì, e si leggono con qualunque app Nostr che mostra gli annunci (NIP-99).

Il bot di Telegram serve a tre cose: aprire Barattolo, mandarti gli avvisi sui tuoi ordini e scambi, e sfogliare le categorie anche senza aprire la Mini App (scrivi /sfoglia). Gli acquisti, le vendite e le trattative si fanno nella Mini App o sul sito.

# Entrare e il profilo

Non servono email, password o numero di telefono. Si entra in due modi:
- con Telegram: dentro la Mini App sei già riconosciuto; sul sito c'è «Entra con Telegram»;
- con una chiave Nostr: «Entra con Nostr», con un'estensione del browser, un bunker (nostrconnect) o un'app che firma. La chiave privata (nsec) non arriva mai ai server di Barattolo: quando serve una firma la fa il tuo browser o il tuo bunker.

Entrare sul sito passando dal bot (se nelle REGOLAZIONI del pannello «Entra dal bot» è accesa): sul sito «Entra con Telegram» apre il bot @ilbarattolobot con un link fatto apposta (sul sito .onion il link arriva come QR, da inquadrare col telefono). Tocchi «Avvia» e il bot chiede «🔑 Entri su Barattolo come …?», mostrando tre figure del mercatino (per esempio 🍯 Miele, 🚲 Bici, 📚 Libri). Tocchi quella che la pagina ti mostra e sei dentro, con l'account che hai aperto in quel momento nell'app di Telegram: chi ha due account sceglie così quale usare. Il link vale due minuti e una volta sola. Se non sei stato tu a chiederlo, tocca «❌ Non sono stato io»: anche una figura sbagliata chiude il tentativo.

Un account nato con Telegram può collegare anche una chiave Nostr dal Profilo, e viceversa.

Nel Profilo si impostano le cose che servono a vendere e a scambiare: soprattutto l'indirizzo Lightning per incassare (voce «Lightning address»), il wallet collegato con NWC (facoltativo) e gli avvisi. Chi usa anche i bitcoin on-chain trova altre due voci: «📥 Come ricevi» e «₿ On-chain» (vedi «Bitcoin on-chain»).

# Il wallet Lightning

Per pagare e per incassare serve un wallet Lightning tuo. Ne esistono tanti, gratuiti, e ne basta uno. Barattolo non ha un wallet suo e non tiene i tuoi sats, tranne il tempo di un affare (vedi il deposito di garanzia).

- Per pagare: Barattolo ti mostra una fattura Lightning (invoice). La apri nel wallet, la copi e incolli, o ne inquadri il QR.
- NWC (Nostr Wallet Connect): se colleghi il wallet dal Profilo, «⚡ Compra subito» paga in un tocco, e nel P2P la fattura per ricevere la fa il wallet da solo. La connessione resta solo sul tuo dispositivo, non arriva ai nostri server, e nel wallet le puoi dare un tetto di spesa.
- Per incassare: l'indirizzo Lightning (quello con la @, tipo nome@dominio) si imposta una volta nel Profilo e non scade. Se non ce l'hai, quando l'affare si chiude ti avvisiamo e incolli una fattura nell'ordine in quel momento (prima no: una fattura scade).
- Nel P2P l'indirizzo di Wallet of Satoshi non passa la verifica: lì si incolla una fattura del wallet, che invece funziona. Lo stesso vale per qualunque indirizzo che il servizio di scambio non riesce a verificare.

# Comprare nel mercatino

1. Trovi l'annuncio: dalla vetrina (Esplora), dalla ricerca, dalle categorie. Puoi salvare i preferiti e farti avvisare quando arriva quello che cerchi.
2. Scegli come riceverlo, fra quelli che il venditore offre: spedizione a un indirizzo, spedizione a un punto di ritiro o a un locker, ritiro a mano in zona, oppure consegna dentro Barattolo se è un codice o un buono digitale.
3. Paghi con «🔒 Compra in sicurezza»: arriva una fattura Lightning da pagare col wallet. La fattura dura pochi minuti (vedi i NUMERI DI OGGI): se scade non è successo niente, se ne fa un'altra al cambio del momento.
4. I sats entrano nel deposito di garanzia. Il venditore viene avvisato, sa di essere pagato, ma i sats non sono ancora suoi.
5. Il venditore spedisce e segna il corriere col tracciamento, oppure vi accordate per il ritiro, oppure ti consegna il codice dentro l'ordine.
6. Quando l'oggetto è arrivato ed è come promesso, lo confermi dall'ordine, nella scheda «Ordini». Solo in quel momento i sats passano al venditore.

Si può anche fare un'offerta più bassa con «Fai un'offerta»: il venditore la accetta o la rifiuta, e se la accetta hai un tempo per pagare, scritto nell'ordine. Un'offerta senza risposta scade da sola.

Tutti i tuoi acquisti e le tue vendite stanno nella scheda «Ordini», con lo stato di ogni ordine e i bottoni per il passo successivo. In fondo all'elenco c'è «📄 Esporta tutti gli ordini in CSV», che scarica un file con tutti i dettagli dei tuoi ordini (utile a chi vende per tenere i conti).

Per un contenuto digitale il venditore può chiederti qualche informazione prima di pagare (per esempio nome, cognome o email, una scelta da un elenco, un sì o un no): rispondi alla cassa. Le risposte viaggiano cifrate dentro l'ordine, le leggete solo tu e il venditore, e si cancellano come l'indirizzo. Il numero di telefono non si può chiedere.

# Il deposito di garanzia

Quando compri, i sats non vanno subito al venditore: si fermano in un deposito di garanzia (in gergo escrow) che custodisce Barattolo, su un nodo Lightning suo. Il venditore spedisce tranquillo perché sa che i soldi ci sono; tu sai che non si muovono finché l'oggetto non è arrivato davvero.

I tempi (le cifre esatte sono nei NUMERI DI OGGI):
- dopo la consegna hai un certo numero di ore per controllare l'oggetto e confermare. Oggi i sats non partono da soli: allo scadere arriva un promemoria, e se il silenzio continua interviene un moderatore. Nessuno incassa mentre tu non hai confermato;
- per un codice o un buono digitale le finestre sono più corte, e lì allo scadere i sats vanno al venditore: provalo subito.

I sats restano in un conto Lightning della piattaforma solo per il tempo dell'affare: non sono un investimento e non vengono messi a rendere. Quando l'affare si chiude escono, al venditore o a te.

# Se qualcosa va storto: la disputa

Finché i sats sono nel deposito puoi aprire una disputa dalla pagina del tuo ordine. Il deposito si congela e interviene un moderatore: legge le due versioni, guarda quello che c'è (foto, tracciamento, messaggi nell'ordine) e decide. Le strade sono tre:
- i sats tornano a te, spedizione compresa;
- i sats vanno al venditore;
- i sats tornano a te meno le spese di spedizione, che restano al venditore (per esempio un pacco tornato indietro per un indirizzo sbagliato).
Se l'oggetto va restituito, il rimborso parte dopo che è tornato indietro.

Aprire una disputa non è un'accusa: spesso è un malinteso che si chiarisce in mezza giornata. Prima di aprirla conviene scrivere all'altra persona.

Dove il deposito non può proteggerti, ed è meglio saperlo prima:
- una prestazione (una lezione, una consulenza) avviene fuori da Barattolo: in disputa si guardano le condizioni scritte nell'ordine, come l'appuntamento concordato e il collegamento lasciato;
- un codice rivelato non torna indietro: nessuno può sapere se l'hai già usato. Provalo subito;
- un posto in un abbonamento condiviso può sparire dopo: il piano resta di chi te l'ha venduto;
- nel ritiro a mano il controllo è tuo: guarda e prova l'oggetto prima di confermare, perché con la conferma i sats partono e non tornano indietro;
- un punto di ritiro di Barattolo è una persona che si è offerta, non un'azienda: se segna di aver ricevuto il pacco, per noi chi ha spedito ha consegnato. Vai a ritirare presto;
- un pacco perso o rovinato dal corriere è una cosa fra chi spedisce e il corriere: Barattolo garantisce la transazione, non il viaggio. Spedite sempre col tracciamento, e le cose di valore con la copertura del corriere;
- il deposito garantisce l'oggetto promesso, non i gusti: «non mi piace più» non è un difetto, un oggetto diverso dalla descrizione sì;
- un indirizzo sbagliato lo paga chi l'ha scritto: se il pacco torna indietro, le spese di spedizione restano a te. Per questo prima di pagare ti chiediamo di ricontrollarlo.

Pagare fuori da Barattolo (un bonifico, un pagamento diretto al venditore) vuol dire rinunciare al deposito di garanzia: nessuno può più aiutarti a recuperare i soldi.

# Vendere nel mercatino

1. Tocca «Vendi» (il tasto ＋ in basso).
2. Aggiungi almeno una foto (senza foto non si pubblica), il titolo, la descrizione, la categoria e il prezzo.
3. Scegli come consegni: spedizione (con i corrieri che usi), punto di ritiro o locker, ritiro a mano in zona, o consegna digitale per codici e buoni.
4. Pubblica. Ogni annuncio passa dalla moderazione, anche quando lo modifichi: se qualcosa non convince resta in attesa di un moderatore, e se viene fermato il messaggio spiega perché e come rimediare.

Hai un catalogo grande? Nel Profilo c'è «📥 Importa in blocco»: scarichi il modello CSV, una riga per annuncio, fino a 500 annunci per volta. Ogni riga vuole almeno una foto, con un link nella colonna «foto» (più d'uno separati da |) oppure coi nomi dei file dentro uno ZIP che carichi insieme; una riga senza foto viene scartata. Prima di pubblicare tocchi «🔎 Controlla il file» e vedi cosa va e cosa no. Se hai un negozio Shopify o WooCommerce, nella stessa sezione lo puoi collegare: i prodotti entrano da soli e restano in pari (se la sezione non la vedi, guarda i NUMERI DI OGGI o chiedi allo staff). Gli annunci importati passano dalla moderazione come gli altri.

Per incassare da solo imposta il tuo indirizzo Lightning nel Profilo: quando chi compra conferma, i sats ti arrivano lì.

Le commissioni del mercatino: Barattolo non prende commissioni, né a chi vende né a chi compra. Si pagano solo le commissioni della rete, che non vanno a Barattolo: su Lightning sono pochi sats o niente, on-chain sono quelle dei miner. Se un giorno cambiasse, la cifra sarebbe nei NUMERI DI OGGI.

Quando qualcuno chiede delle commissioni, tieni sempre separati il mercatino (zero commissioni di Barattolo, solo quelle della rete) e lo scambio P2P (la commissione del coordinatore, spiegata più sotto). Mescolarli confonde.

Le donazioni: chi vuole sostenere Barattolo con qualche sats può mandarli all'indirizzo Lightning zap@barattolo.store (si incolla nel wallet come destinatario, si sceglie l'importo e si invia), oppure con uno zap al profilo Nostr «Barattolo», che accetta anche bitcoin on-chain. Sono un regalo libero: non danno vantaggi nell'app e non sono mai obbligatorie. Se qualcuno chiede come donare, dai questo indirizzo e ringrazia di cuore.

Quando arriva un ordine il bot ti avvisa. Spedisci, segna il corriere e il codice di tracciamento nell'ordine, e aspetta la conferma di chi compra. L'indirizzo di chi compra lo vedi solo tu, per stampare l'etichetta: non usarlo per altro.

Le prestazioni si possono vendere, ma devono essere definite: quanto durano, che cosa comprendono, a che prezzo. «Un'ora di lezione di inglese» sì; «ti faccio quello che ti serve» no.

Su Barattolo non si vendono: armi, droghe, servizi sessuali, refurtiva, contraffazioni, documenti, dati personali, farmaci, animali protetti.

Un venditore può mettere il negozio in ferie (gli annunci restano ma non si comprano) e ha una pagina del negozio col suo link da condividere.

Chi vende contenuti digitali può aggiungere all'annuncio le domande da fare a chi compra (testo breve, elenco a tendina, email, sì/no), obbligatorie o facoltative; nome, cognome ed email si aggiungono con un tocco. Il numero di telefono non si può chiedere.

# Spedizione, indirizzo e ritiro

- Spedizione a un indirizzo: lo scrivi al momento dell'acquisto e resta dentro l'ordine. Lo vede solo il venditore, è cifrato nel database e viene cancellato appena confermi di aver ricevuto. I moderatori non lo leggono, nemmeno in disputa.
- Punto di ritiro o locker: un tuo indirizzo non serve proprio; al banco basta il nome del destinatario. Puoi lasciare un'email se vuoi che il codice di ritiro te lo mandi il corriere: è facoltativa.
- Ritiro a mano: vi accordate per vedervi in zona. Controlla l'oggetto prima di confermare.

# Lo scambio P2P: comprare e vendere bitcoin per euro

Nel P2P non compri da Barattolo: compri da un'altra persona. Vi accordate su un prezzo, gli euro viaggiano fra voi due col metodo scelto, e i sats restano bloccati in garanzia finché gli euro non sono arrivati. Barattolo non tocca i tuoi euro. Si entra dal tasto «P2P» in basso; lì ci sono il «Libro ordini», «I miei scambi», «Pubblica» e «Info P2P», che spiega tutto con calma.

Come funziona, in cinque passi:
1. Qualcuno pubblica un ordine: dice se compra o vende sats, per quanti euro e con quali metodi di pagamento. L'ordine va nel libro, che vedono tutti.
2. Tu lo prendi: scegli il metodo e l'ordine si riserva a te. La tua scelta arriva all'altra persona: nella pagina dello scambio legge «ha scelto…» (per esempio «USDT su Tron» o «SEPA Instant»), la stessa riga in cima alla chat dello scambio, e un avviso su Telegram. Se un recapito arrivato è per un metodo o una rete diversi da quelli scelti, la pagina lo dice in rosso: prima di pagare, chiarite in chat.
3. Chi vende blocca i sats: paga una richiesta speciale (una hold invoice) che trattiene i sats senza consegnarli. Da lì sono in garanzia.
4. Chi compra manda gli euro col metodo scelto, al recapito che l'altra persona lascia dentro lo scambio, e poi lo dice nell'app.
5. Chi vende controlla di aver ricevuto gli euro e libera i sats: arrivano all'indirizzo Lightning o alla fattura di chi compra.

La garanzia: i sats in garanzia possono prendere due strade sole, andare a chi compra o tornare a chi vende. Nessuno può dirottarli altrove. A tenerli è il coordinatore, un programma che si chiama Mostro: lo fa girare Barattolo, sul suo nodo.

Come si legge una card del libro: in alto a destra due quadratini con una freccia dicono cosa invii e cosa ricevi (le stelle blu dell'Europa per gli euro, la T verde di Tether per gli USDT, il fulmine nero per i sats su Lightning, la ₿ arancio per bitcoin on-chain). Sotto ci sono la cifra da inviare e quella da ricevere, i metodi di pagamento e, nel riquadro in fondo, la faccia di chi ha pubblicato con le sue stelline e quanti scambi P2P ha già fatto («✅ 22 scambi P2P»); toccando la faccia si apre il suo negozio (anche sulle card on-chain; se non ha ancora un negozio, l'app te lo dice e non apre l'ordine). La riga colorata sul bordo di sotto è il tempo che resta all'ordine: si accorcia, diventa arancio negli ultimi tre giorni e rossa, lampeggiante, nell'ultimo.

Il prezzo di bitcoin nel libro: in cima al libro P2P, sotto i rettangoli «Novità», c'è la card «1 BTC adesso» col prezzo in euro (lo stesso che l'app usa per i conti, aggiornato ogni minuto), quanto è salito o sceso e una piccola linea, verde se sale e rossa se scende. Toccandola si passa dalle ultime 24 ore ai 7 giorni e ai 30 giorni. Subito dopo un aggiornamento può mostrare solo il prezzo, finché non ha la storia del periodo.

Quanto si può per ordine nel P2P, per ora (fase beta): fino a 250 € negli scambi in Lightning e fino a 500 € in quelli on-chain (dal 12 novembre 2026; prima anche l'on-chain si fermava a 250 €). Il foglio «Pubblica» lo scrive sotto la cifra e non lascia andare oltre.

Il prezzo: gli ordini si scrivono in euro e i sats si contano al cambio del momento, per questo finché l'ordine è nel libro la cifra in sats ha il segno ≈. La cifra esatta si fissa quando l'ordine viene preso. Alcuni ordini hanno un intervallo («da 20 a 100 €»): lì scegli tu quanto.

Premio e sconto: chi pubblica può chiedere fino al 20% sopra o sotto il prezzo di mercato. Sopra si chiama premio e conviene a chi vende, sotto si chiama sconto e conviene a chi compra. La riga c'è sempre nel conto.

La commissione del P2P la decide il coordinatore ed è già dentro i sats che passano di mano: chi vende ne blocca un po' di più, chi compra ne riceve un po' di meno. Nell'ottobre 2026, durante la beta, è il 3% in tutto, cioè 1,5% per chi compra e 1,5% per chi vende; finita la beta sarà del 4% (2% per parte). Pionieri e chi è al livello 5 hanno uno sconto dello 0,5% sulla propria parte. La cifra esatta la vedi sempre nel conto, prima di prendere un ordine. Pubblicare o prendere un ordine non costa niente. Il riquadro colorato delle commissioni in cima al libro P2P compare solo la prima volta, alla fine del tutorial: poi non c'è più, e si rivede rifacendo «Come funziona» fino a «Fine 🎉» (toccandolo si apre il dettaglio con lo sconto).

I metodi di pagamento degli euro sono un elenco chiuso, che vedi quando pubblichi o prendi un ordine. Gli euro non passano da Barattolo: il recapito (IBAN, numero, tag) ve lo scambiate dentro lo scambio, cifrato. La garanzia protegge i sats, non gli euro: se chi compra dice di aver mandato gli euro e non è vero, chi vende semplicemente non libera; se li ha mandati e chi vende non libera, c'è la disputa.

I tempi: se il tempo scade prima che i sats siano bloccati non perde niente nessuno, e l'ordine torna nel libro o si chiude. Coi sats in garanzia avete circa quattro giorni: se chi compra non ha detto di aver pagato, allo scadere i sats tornano da soli a chi vende; se l'ha detto, si apre una disputa.

La disputa nel P2P: si apre solo coi sats già in garanzia, col bottone «⚠️ Apri una disputa» in fondo alla pagina dello scambio. Ferma lo scambio e chiama un moderatore, che potrà leggere la chat di quello scambio. Se è solo una domanda o un ritardo, prima scrivi all'altra persona nella chat. Chi vende può sempre liberare i sats anche a disputa aperta, e la disputa si chiude.

La chat dello scambio: da quando l'ordine è preso a quando lo scambio finisce c'è una chat fra voi due, cifrata, con foto e PDF. A fine scambio si cancella. Barattolo non ti scrive mai nella chat dello scambio: chi lì si presenta come «assistenza» è l'altra persona.

Contanti di persona (metodo «Contanti»): ci si incontra, chi compra sats porta le banconote, chi vende le conta e libera i sats lì, davanti all'altro. Le regole:
- i contanti si consegnano solo quando chi vende preme «Libera i sats» davanti a te, e si va via solo con lo scambio concluso;
- vedetevi in un posto pubblico e di giorno, contate insieme, mai grosse cifre da soli;
- chi vende fissa l'appuntamento (giorno, ora, luogo) dentro lo scambio;
- all'arrivo ognuno può toccare «📍 Sono qui»: registra ora e, se il telefono la dà, la posizione. È facoltativo ma aiuta nelle dispute;
- c'è un tetto in euro per scambio (vedi i NUMERI DI OGGI); sopra si divide in più ordini. Chi prende un ordine in contanti può dover bloccare una piccola cauzione.

La mappa del contanti: nel libro P2P, sopra le card, la pillola «🗺️ Mappa» apre l'Italia coi pallini delle offerte in contanti di persona. Ogni pallino sta sul centro del comune dove la persona propone di vedersi, mai su un indirizzo. Si avvicina con due dita, con la rotellina o con un doppio tocco; toccando un comune l'elenco mostra solo le sue offerte.

Revolut: chi riceve gli euro su Revolut sceglie come, con tre bottoni nel modulo del recapito: RevTag (di serie), numero di telefono, oppure IBAN con l'intestatario.

Se chi vende chiede di annullare uno scambio coi sats già in garanzia, chi compra non è obbligato ad accettare: se ha già mandato gli euro o li vuole mandare, ha ancora «Ho inviato gli euro», e può aprire una disputa.

Barattozon (nel libro «Contanti al tabacchino»): chi vende sats fa un ordine Amazon da pagare in contanti nel punto vendita, e chi compra lo paga alla cassa di un tabacchino abilitato col PayCode. Il PayCode vale almeno 25 € e Amazon lo accetta fino a 999 €. Si paga solo quando la pagina dice «Sats in garanzia», si tiene lo scontrino come prova, e poi si tocca «Ho pagato al tabacchino». Chi vende controlla su Amazon che l'ordine risulti pagato e libera i sats. Alla cassa bisogna dire «devo pagare un ordine Amazon in contanti con un PayCode»: non una ricarica e non un buono regalo. Barattozon c'è da tutti e due i lati del libro: anche chi COMPRA sats può pubblicare un ordine «al tabacchino», con una fascia di euro (per esempio da 30 a 80 €, il massimo è obbligatorio); chi vende lo prende scrivendo il PayCode (importo esatto, le nove cifre, la scadenza) e chi compra lo paga al tabacchino.

Altre valute e reti (solo se nei NUMERI DI OGGI risultano disponibili): ordini P2P pagati in USDT al posto degli euro (qui sotto), e scambi P2P coi bitcoin on-chain, con la garanzia a firme multiple (due chiavi su tre).

Ordini P2P in USDT (se nei NUMERI DI OGGI «Ordini P2P in USDT» è acceso): al posto degli euro si paga in USDT, il dollaro digitale di Tether (1 USDT vale 1 dollaro). I sats restano su Lightning con la garanzia di sempre (per gli USDT negli scambi on-chain vedi più sotto); gli USDT passano direttamente da una persona all'altra, e Barattolo non li tocca mai. Le reti sono solo due, Tron (TRC-20) ed Ethereum (ERC-20), mai altre: in un ordine in USDT le reti prendono il posto dei metodi di pagamento.
- Nel libro un ordine in USDT si riconosce dalla T verde di Tether nei quadratini in alto a destra della card.
- In cima al libro c'è il rettangolo verde «USDT · Novità»: toccandolo parte un breve tutorial che mostra come riconoscere un ordine in USDT, come pubblicarne uno e come si paga senza sbagliare rete. Si può rivedere toccandolo di nuovo.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta, euro o USDT. Con USDT si scelgono le reti (Tron, Ethereum o tutte e due) e l'importo si scrive in USDT. Il tetto della fase beta è lo stesso degli euro, convertito in USDT.
- Un ordine in USDT con un intervallo («da 50 a 276 USDT, scegli tu»): toccandolo, nel foglio «Quanto vuoi scambiare?» la cifra si scrive in USDT, e i sats si contano al cambio del dollaro (1 USDT = 1 $), non dell'euro. Per questo 276 USDT valgono meno sats di 276 €.
- Chi riceve gli USDT (cioè chi vende i sats) scrive nello scambio il suo indirizzo USDT, copiato dal suo wallet. L'app controlla che sia della rete giusta e ferma un indirizzo bitcoin, Lightning, Liquid o dell'altra rete, perché con la rete sbagliata gli USDT si perdono. Un limite da sapere: un indirizzo Ethereum (0x…) vale anche su reti che non offriamo (Polygon, BNB, Arbitrum…), quindi chi paga deve mandare proprio sulla rete scritta nello scambio.
- Chi paga vede la rete in grande, l'indirizzo col QR e il contratto del vero USDT, per non farsi ingannare da token falsi che si chiamano «USDT» anche loro. Manda gli USDT, incolla l'id della transazione (lo trova nei dettagli dell'invio, nel wallet) e tocca «💵 Ho inviato gli USDT».
- Chi vende controlla che siano arrivati sulla rete giusta, anche col tasto «🔎 Controlla su Tronscan» (o Etherscan) sotto l'id, e libera i sats solo quando ci sono davvero. Se qualcosa non torna si apre una disputa: il moderatore legge l'id della transazione sulla rete giusta.

Scambi P2P on-chain (se nei NUMERI DI OGGI «Scambi P2P in bitcoin on-chain» è disponibile): si scambiano bitcoin sulla rete principale, non su Lightning. La garanzia non è quella di Lightning: chi vende blocca i bitcoin in un deposito a tre chiavi, una sua, una di chi compra e una di Barattolo, e per spostarli ne servono due. Barattolo da solo non li può muovere.
- Nel libro uno scambio on-chain si riconosce dalla moneta arancio ₿ (quelli di Lightning hanno il fulmine). Sopra le card c'è il rettangolo arancio «On-Chain» con la scritta «Novità», che apre la pagina «Scambi on-chain»: lì si pubblica («Pubblica uno scambio on-chain») e si seguono i propri.
- Per pubblicare si può anche toccare il + di «Compra BTC» o «Vendi BTC» e scegliere «On-chain» invece di «Lightning». Serve aver preparato Profilo → «₿ On-chain» (le 12 parole e la loro copia: vedi «Bitcoin on-chain»). Un ordine resta nel libro 24 ore; il tetto per ordine è quello on-chain dei NUMERI DI OGGI e del paragrafo sui limiti.
- Il giro, passo per passo: chi prende fa nascere l'indirizzo a tre chiavi. Chi vende ha 6 ore per depositare con «🔒 Blocca i sats»: i sats dello scambio più un piccolo margine per la commissione della rete. Con una conferma della rete (circa dieci minuti) lo scambio va avanti, e tutti e due ricevono l'avviso. Allora chi compra manda gli euro col metodo scritto e tocca «💶 Ho inviato gli euro». Chi vende li controlla sul suo conto e SOLO quando li vede tocca «🔓 Ricevuti: libera i sats»; la seconda firma la mette da solo il telefono di chi compra, e i bitcoin partono.
- Chi compra deve dire dove ricevere: nello scambio c'è «Dove ricevi i bitcoin?», si incolla un proprio indirizzo e si tocca «✍️ Firma e usa questo indirizzo». Chi ha messo nel Profilo la chiave del conto del suo wallet non deve scriverlo ogni volta: ogni scambio arriva a un indirizzo nuovo.
- Se il deposito non arriva in tempo, chi compra può rinunciare («Rinuncia: il deposito non è arrivato»); chi deve depositare e non ha ancora mandato niente può annullare («Annulla (non deposito)»). Con i sats già nel deposito non si annulla da soli: si esce col rimborso d'accordo o con «⚖️ Apri una disputa». Decide un moderatore di Barattolo, Barattolo mette la sua firma e la seconda la mette il telefono di chi ha ragione.
- A fine scambio la pagina dice «Concluso: i sats sono andati al wallet di chi ha comprato» oppure «Rimborsato: i sats sono tornati a chi li aveva depositati».
- USDT negli scambi on-chain (se nei NUMERI DI OGGI «Scambi P2P on-chain pagati in USDT» è disponibile): la garanzia resta il deposito bitcoin a tre chiavi, e al posto degli euro chi compra paga in USDT su Tron o Ethereum, da persona a persona, con le stesse regole degli ordini in USDT qui sopra: chi vende scrive il suo indirizzo USDT, chi paga incolla l'id della transazione e tocca «Ho inviato gli USDT». Un ordine è in una valuta sola: o euro o USDT.

Ricevere o pagare su un'altra rete (se nei NUMERI DI OGGI «P2P su un'altra rete» è disponibile): la rete di un ordine dice come paga chi l'ha pubblicato, ma chi lo prende può usare l'altra, con uno swap di SATS Routing fatto dal suo telefono (come la pagina «Swap»). Il costo dello swap si vede prima di confermare, e Barattolo non aggiunge commissioni.
- Ordine Lightning, ma vuoi ricevere bitcoin on-chain: nel foglio «Dove ricevere i sats» scegli «₿ On-chain», incolli un tuo indirizzo bitcoin e l'app ti dice quanti sats ti arrivano circa e quanto costa lo swap. Alla liberazione i sats diventano bitcoin al tuo indirizzo. Se il moderatore dà ragione a chi vende, lo swap scade senza costare niente.
- Scambio on-chain, ma vuoi ricevere in Lightning: nello scambio tocchi «⚡ Ricevi in Lightning» e, quando chi vende ha confermato gli euro, incolli una tua richiesta Lightning (o «⚡ Prendila dal mio Lightning address») e tocchi «✅ Conferma lo swap». Ti arriva il prezzo meno il costo dello swap; se la richiesta non si riesce a pagare, i bitcoin tornano da soli al tuo wallet on-chain di Barattolo. Si torna indietro con «₿ Ricevi on-chain invece».
- Scambio on-chain che hai preso tu per vendere, ma hai solo sats Lightning: nel foglio «🔒 Blocca i sats» scegli «⚡ Lightning» e tocchi «⚡ Crea la richiesta Lightning»; la paghi col tuo wallet e lo swap mette i bitcoin nel deposito a tre chiavi. Un annullo o un rimborso tornano però on-chain, al tuo wallet di Barattolo.
- Lo swap ha i suoi limiti di cifra (quelli di SATS Routing): fuori dai limiti l'app lo dice e lo scambio si fa sulla rete dell'ordine.

# Bitcoin on-chain

Oltre a Lightning, alcune funzioni usano i bitcoin «on-chain», cioè sulla rete principale di Bitcoin: la moneta arancione ₿ le indica in tutta l'app. Quali sono accese, e per chi, lo dicono i NUMERI DI OGGI: una funzione spenta lì non c'è.

- Pagare un ordine on-chain: chi compra manda i bitcoin a un indirizzo e l'ordine nasce alla prima conferma della rete. Appena la rete vede i sats la pagina del pagamento si chiude da sola, e in «Ordini» l'ordine dice «⏳ Visto in rete, aspetto la conferma» (etichetta «In arrivo»): non c'è altro da fare, si aspetta la conferma, circa dieci minuti. Se è arrivata solo una parte, la pagina resta aperta e dice quanti sats mancano. Appena il pagamento si vede in rete, chi vende riceve «Pagamento in arrivo»: l'oggetto è prenotato, ma non si spedisce finché non arriva l'avviso vero, alla conferma.
- Quando paghi on-chain (un ordine, il deposito di uno scambio P2P, lo Swap) l'app scrive i sats da mandare e, sotto, la riga «In BTC» con la stessa cifra in bitcoin (per esempio 0,00008128 BTC): molti wallet on-chain la chiedono così. Un tocco la copia, col punto (0.00008128), pronta da incollare nel wallet. Se invece inquadri il QR, la cifra il wallet la compila da solo; anche «₿ Apri nel wallet» apre il wallet con indirizzo e cifra già scritti.
- Profilo → «📥 Come ricevi»: due righe, «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in». Lì scegli se i sats ti arrivano in Lightning, on-chain, oppure «Ogni volta» (decidi tu ordine per ordine).
- Chi ha queste scelte trova anche, nel modulo dell'annuncio sotto il prezzo, «Come vuoi ricevere per questo oggetto?»: la scelta dell'annuncio vale più di quella del Profilo.
- Profilo → «₿ On-chain»: «Dove ricevi i bitcoin» (l'unica cosa da compilare: il tuo indirizzo o il tuo wallet), poi la chiave e le 12 parole. Le 12 parole servono solo a FIRMARE i tuoi scambi on-chain: i sats non arrivano lì. Non darle mai a nessuno.
- Le 12 parole hanno bisogno di una copia fuori dal telefono: Barattolo la salva cifrata nel cloud di Telegram e/o sui relay Nostr, e senza una copia non si apre un ordine on-chain nuovo. Se manca la copia sui relay, nel Profilo c'è «Salva sui relay Nostr».
- Il wallet è uno solo, fra la Mini App in Telegram e il sito: se apri Barattolo da un altro posto, ti chiede di incollare le stesse 12 parole invece di crearne di nuove.
- Se non hai ancora scelto dove ricevere, la consegna dei bitcoin a te aspetta: l'app ti manda a Profilo → «₿ On-chain» per sceglierlo.
- La seconda firma: i sats on-chain escono con due firme su tre. Di solito il tuo telefono mette la sua da solo quando apri Barattolo; nell'ordine c'è anche il tasto «✍️ Metti la seconda firma», che mostra l'anello mentre firma e poi dice com'è andata, o perché non ha firmato (per esempio: la tua chiave sta solo sul telefono con cui hai pagato o venduto). Quando i sats sono partiti l'ordine lo dice, con il link «Vedi la transazione», e il tasto sparisce.

# Lo Swap: spostare i tuoi sats fra Lightning e bitcoin on-chain

La pagina «Swap» (la scheda in basso; fino al 12 novembre 2026 si chiamava «Cambio») sposta i TUOI sats fra Lightning e un tuo indirizzo bitcoin on-chain, nelle due direzioni, senza un ordine di mezzo. Se è accesa lo dicono i NUMERI DI OGGI.
- Lightning → bitcoin: scrivi la cifra (quella che mandi o quella che ricevi), incolli il tuo indirizzo bitcoin e paghi la fattura Lightning col tuo wallet; i bitcoin arrivano al tuo indirizzo.
- Bitcoin → Lightning: scrivi quanto vuoi ricevere (o quanto mandi), incolli una tua fattura Lightning di quella cifra esatta e mandi i bitcoin all'indirizzo che l'app ti mostra; quando arrivano, la tua fattura viene pagata. La cifra esatta nella frase «crea una richiesta di … sats esatti» si tocca e si copia, pronta da incollare nel wallet. Al posto della fattura puoi incollare il tuo Lightning address (nome@wallet): la fattura della cifra giusta la chiede Barattolo al tuo wallet quando premi «Conferma».
- Lo swap lo fa un servizio esterno (SATS Routing). Barattolo non prende commissioni: prima di confermare vedi quanto ricevi, con dentro la commissione del servizio e quella della rete.
- I sats non passano mai da Barattolo: partono dal tuo wallet e arrivano al tuo wallet.
- Limiti: da 25.000 sats a 0,01 BTC (1.000.000 sats) a swap, al massimo 5 swap al giorno. Da bitcoin verso Lightning il minimo è 50.000 sats RICEVUTI in Lightning (è il minimo del servizio): chi scrive la cifra in «Mandi» deve mandarne un po' di più, perché dai bitcoin mandati si tolgono la commissione del servizio e la rete. Se la cifra è sotto, l'app dice il minimo dal lato dove l'hai scritta (per esempio «Lo swap parte da 50.568 sats da mandare»). Se il servizio cambia i suoi limiti, vale il più stretto.

La privacy dello Swap, cioè chi vede cosa:
- Barattolo si segna, legati al tuo account, la direzione, la cifra, il numero dello swap e l'indirizzo del servizio dove passano i bitcoin. Non si segna il tuo indirizzo bitcoin né la tua fattura Lightning. Però dal numero dello swap, sulla blockchain pubblica, si può seguire dove sono andati i bitcoin.
- SATS Routing vede quel che serve a fare lo swap: la fattura Lightning e il tuo indirizzo bitcoin. Non sa chi sei su Barattolo.
- La pagina parla con SATS Routing e con mempool.space (da lì legge la rete e trasmette la transazione) direttamente dal tuo telefono o computer, quindi loro vedono il tuo IP. Se entri dal sito .onion con Tor Browser, non lo vede nessuno dei tre.
- Sulla blockchain, da Lightning a bitcoin: al tuo indirizzo arriva una transazione con un solo ingresso, l'indirizzo del servizio, e una sola uscita, il tuo indirizzo; di solito ha l'aspetto di un pagamento qualunque. Da bitcoin a Lightning: si vede la transazione che parte dal tuo wallet verso l'indirizzo del servizio, come ogni pagamento on-chain.
- Payjoin: nello Swap non si usa. Da Lightning a bitcoin la transazione verso il tuo indirizzo la prepara il tuo telefono per lo swap, e non sa fare Payjoin: se incolli un link Payjoin («bitcoin:…?pj=…») l'app tiene solo l'indirizzo e i bitcoin arrivano lì con una transazione normale. Da bitcoin a Lightning l'indirizzo del servizio non accetta Payjoin, quindi anche il tuo wallet manda una transazione normale.
- Il consiglio di sempre: un indirizzo nuovo per ogni swap, in un wallet di cui solo tu hai le chiavi.

# Nostr

Gli annunci di Barattolo vengono pubblicati anche su Nostr, una rete aperta: esistono sui relay anche indipendentemente da Barattolo. Se colleghi una tua chiave Nostr dal Profilo, i tuoi annunci escono firmati da te (la firma la fa il tuo browser) e restano tuoi. Gli avvisi possono arrivarti anche su Nostr, oltre che su Telegram. La chiave privata (nsec) non va mai data a nessuno, nemmeno a Barattolo.

# I tuoi dati, in breve

Barattolo sa di te pochissimo: niente email, password o telefono. Da Telegram riceve il numero identificativo, il nome e lo username; da Nostr solo la chiave pubblica. L'indirizzo di spedizione è cifrato e si cancella quando confermi di aver ricevuto. Niente tracciamento, niente pubblicità, niente cookie di terzi. Tutto è spiegato nella pagina «I tuoi dati» (barattolo.store/privacy).

L'indirizzo IP: come ogni server, quello di Barattolo vede l'IP di chi si collega mentre gli risponde. Finisce solo nel registro tecnico della macchina: non nel database, non in un profilo, e non lo incrociamo con niente. Da Telegram l'IP non arriva.

Tor: Barattolo ha anche un sito .onion, lo stesso Barattolo dentro la rete Tor. Da lì il server non vede il tuo IP e non lo scrive da nessuna parte. L'indirizzo esatto è nella pagina «I tuoi dati», e quando apri barattolo.store con Tor Browser la barra degli indirizzi ti propone da sola la versione .onion («.onion disponibile»). Con un .onion conta ogni carattere: usa solo quello ufficiale.

Questo assistente: la tua domanda e le ultime battute arrivano ad Anthropic, l'azienda dell'intelligenza artificiale che risponde, ma mai il tuo nome, il tuo account o i tuoi ordini. Le conversazioni non vengono conservate: in chat privata l'assistente ricorda le domande e le risposte della giornata, per seguire il filo del discorso, e a mezzanotte spariscono.

# Se Barattolo sparisse

Il mercatino gira su un server solo: se si fermasse, Barattolo si fermerebbe. Ma i sats del deposito stanno su un nodo Lightning separato, con la seed custodita offline; gli annunci restano su Nostr; lo storico è salvato ogni giorno con copie cifrate anche fuori dal server.

# Sicurezza e truffe

- Nessuno di Barattolo ti chiederà mai la seed, le parole di recupero, la nsec, una chiave privata o una password. Chi le chiede è un truffatore. Se le hai date a qualcuno, considerale esposte e sposta subito i fondi su un wallet nuovo.
- Barattolo non ti scrive per primo chiedendo soldi.
- Paga sempre dentro Barattolo: un pagamento fuori dal deposito di garanzia non è protetto.
- Nel P2P, libera i sats solo quando gli euro sono arrivati davvero sul tuo conto, non prima e non sulla fiducia di una ricevuta.

# Parlare con una persona

Se nei NUMERI DI OGGI l'assistenza in app risulta disponibile, c'è anche una chat con lo staff dentro Barattolo: Profilo → Privacy → «💬 Assistenza». Ognuno ha la sua conversazione; lo staff risponde col bollino 🛡️ e ti arriva un avviso quando c'è una risposta.

Se l'assistente non basta, sotto ogni sua risposta c'è il bottone «🙋 Parla con una persona»: ti dà la chat privata di Barattolo (t.me/barattolostore?direct), dove risponde una persona dello staff. Per un problema con un ordine o uno scambio preciso, scrivi lì il numero dell'ordine e cosa è successo. Per una lite su un ordine coi sats in garanzia, la strada giusta resta la disputa, dalla pagina dell'ordine o dello scambio.
