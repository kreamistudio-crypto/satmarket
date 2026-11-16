# La base di conoscenza di Tappo

<!-- FILE GENERATO da assistente/conoscenza.py: non si tocca a mano.
Si rifà con `python assistente/conoscenza.py` dopo ogni ritocco al
libro (assistente/sapere.md), alla Mini App (miniapp.html) o a
NOVITA.md; prove_conoscenza_tappo è rossa finché non è aggiornato. -->

<!-- pezzo libro-001 | libro | sempre -->
## Libro · Cos'è Barattolo

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

<!-- pezzo libro-002 | libro -->
## Libro · Entrare e il profilo (1/2)

Non servono email, password o numero di telefono. Si entra in due modi:
- con Telegram: dentro la Mini App sei già riconosciuto; sul sito c'è «Entra con Telegram»;
- con una chiave Nostr: «Entra con Nostr», con un'estensione del browser, un bunker (nostrconnect) o un'app che firma. La chiave privata (nsec) non arriva mai ai server di Barattolo: quando serve una firma la fa il tuo browser o il tuo bunker.

Entrare sul sito passando dal bot (se nelle REGOLAZIONI del pannello «Entra dal bot» è accesa): sul sito «Entra con Telegram» apre il bot @ilbarattolobot con un link fatto apposta (sul sito .onion il link arriva come QR, da inquadrare col telefono). Tocchi «Avvia» e il bot chiede «🔑 Entri su Barattolo come …?», mostrando tre figure del mercatino (per esempio 🍯 Miele, 🚲 Bici, 📚 Libri). Tocchi quella che la pagina ti mostra e sei dentro, con l'account che hai aperto in quel momento nell'app di Telegram: chi ha due account sceglie così quale usare. Il link vale due minuti e una volta sola. Se non sei stato tu a chiederlo, tocca «❌ Non sono stato io»: anche una figura sbagliata chiude il tentativo. ATTENZIONE ALLA TRUFFA: la figura giusta la vede solo chi ha chiesto di entrare, sulla sua pagina. Se qualcuno ti manda un link del bot e ti dice o ti scrive quale figura toccare, vuole entrare nel tuo account: non toccare la figura, tocca «❌ Non sono stato io». Barattolo e lo staff non ti chiedono mai di toccare una figura.

Un account nato con Telegram può collegare anche una chiave Nostr dal Profilo, e viceversa.

Nel Profilo si impostano le cose che servono a vendere e a scambiare: soprattutto l'indirizzo Lightning per incassare (voce «Lightning address»), il wallet collegato con NWC (facoltativo) e gli avvisi. Chi usa anche i bitcoin on-chain trova altre due voci: «📥 Come ricevi» e «₿ On-chain» (vedi «Bitcoin on-chain»).

<!-- pezzo libro-003 | libro -->
## Libro · Entrare e il profilo (2/2)

Le notifiche sul telefono (se nelle REGOLAZIONI del pannello «Notifiche sul telefono» è accesa): nell'app di Barattolo per Android (quella di Zapstore), nel sito aggiunto alla schermata Home e nel browser del computer, gli avvisi degli ordini, degli scambi P2P e dei messaggi possono arrivare come notifica normale, tipo WhatsApp, anche con l'app chiusa. Si accendono dal Profilo → «🔔 Avvisi» → «📲 Notifiche sul telefono» → «Attiva», e il telefono chiede il permesso: va detto sì. Poi «🔔 Mandami una notifica di prova» fa vedere subito se arrivano. Vale per quel telefono (su un altro si accende di nuovo), e arrivano in più rispetto a Telegram o ai messaggi Nostr, che restano come sono. Si spengono dallo stesso tasto; uscendo dall'account smettono di arrivare su quel telefono. Dentro Telegram il tasto non c'è, perché gli avvisi arrivano già dal bot. NON arrivano: sui telefoni senza i servizi Google (per esempio GrapheneOS), con Tor Browser o sul sito .onion; sull'iPhone solo se Barattolo è aggiunto alla schermata Home (Condividi → «Aggiungi alla schermata Home», da iOS 16.4) e aperto da lì. Se le hai bloccate per sbaglio, si riaprono dalle impostazioni del telefono, alla voce Notifiche. Toccando una notifica si apre la pagina di cui parla: l'ordine, lo scambio o l'annuncio (dal 16 nov 2026 anche gli avvisi degli annunci aprono l'annuncio e non la home); lo stesso vale per i link degli avvisi del bot.

<!-- pezzo libro-004 | libro -->
## Libro · Il wallet Lightning

Per pagare e per incassare serve un wallet Lightning tuo. Ne esistono tanti, gratuiti, e ne basta uno. Barattolo non ha un wallet suo e non tiene i tuoi sats, tranne il tempo di un affare (vedi il deposito di garanzia).

- Per pagare: Barattolo ti mostra una fattura Lightning (invoice). La apri nel wallet, la copi e incolli, o ne inquadri il QR.
- NWC (Nostr Wallet Connect): se colleghi il wallet dal Profilo, «⚡ Compra subito» paga in un tocco, e nel P2P la fattura per ricevere la fa il wallet da solo. La connessione resta solo sul tuo dispositivo, non arriva ai nostri server, e nel wallet le puoi dare un tetto di spesa.
- Per incassare: l'indirizzo Lightning (quello con la @, tipo nome@dominio) si imposta una volta nel Profilo e non scade. Se non ce l'hai, quando l'affare si chiude ti avvisiamo e incolli una fattura nell'ordine in quel momento (prima no: una fattura scade).
- Nel P2P l'indirizzo di Wallet of Satoshi non passa la verifica: lì si incolla una fattura del wallet, che invece funziona. Lo stesso vale per qualunque indirizzo che il servizio di scambio non riesce a verificare.

<!-- pezzo libro-005 | libro -->
## Libro · Comprare nel mercatino (1/2)

1. Trovi l'annuncio: dalla vetrina (Esplora), dalla ricerca, dalle categorie. Puoi salvare i preferiti e farti avvisare quando arriva quello che cerchi.
2. Scegli come riceverlo, fra quelli che il venditore offre: spedizione a un indirizzo, spedizione a un punto di ritiro o a un locker, ritiro a mano in zona, oppure consegna dentro Barattolo se è un codice o un buono digitale.
3. Paghi con «🔒 Compra in sicurezza»: arriva una fattura Lightning da pagare col wallet. La fattura dura pochi minuti (vedi i NUMERI DI OGGI): se scade non è successo niente, se ne fa un'altra al cambio del momento.
4. I sats entrano nel deposito di garanzia. Il venditore viene avvisato, sa di essere pagato, ma i sats non sono ancora suoi.
5. Il venditore spedisce e segna il corriere col tracciamento, oppure vi accordate per il ritiro, oppure ti consegna il codice dentro l'ordine.
6. Quando l'oggetto è arrivato ed è come promesso, lo confermi dall'ordine, nella scheda «Ordini». Solo in quel momento i sats passano al venditore.

Si può anche fare un'offerta più bassa con «Fai un'offerta»: il venditore la accetta o la rifiuta, e se la accetta hai un tempo per pagare, scritto nell'ordine. Un'offerta senza risposta scade da sola.

La mancia al venditore (se nelle REGOLAZIONI del pannello «Mancia al venditore» è accesa): un'offerta può essere solo più bassa del prezzo, ma chi vuole dare di più al venditore può lasciargli una mancia. Nell'ordine già pagato, nella scheda «Ordini», c'è «🎁 Lascia una mancia»: si sceglie la cifra (500, 1.000, 2.100 sats o un'altra) e si paga col proprio wallet. Nello stesso foglio, se vuoi, puoi aggiungere anche uno zap a Barattolo (di serie è «Niente»): sono due fatture, una dopo l'altra. La mancia va DRITTA al Lightning address del venditore: Barattolo non la tocca e non prende commissioni. Per questo è un regalo fuori dal deposito di garanzia e NON si rimborsa, anche se poi l'ordine va male: chi ha dubbi la lascia dopo aver ricevuto l'oggetto. Il bottone c'è solo su un ordine pagato (non su uno annullato, in disputa o rimborsato) e solo se il venditore ha impostato il suo Lightning address nel Profilo. Se non l'ha impostato, il riquadro c'è lo stesso ma senza bottone, con la frase «non ha ancora un indirizzo Lightning nel profilo: per ora la mancia non si può mandare»: è normale, la mancia non avrebbe dove andare (anche se il venditore ha incassato l'ordine, per esempio con una fattura incollata a mano). Al venditore senza indirizzo, nello stesso ordine, compare l'invito «Aggiungilo dal Profilo»: appena lo salva, il bottone compare anche a chi ha comprato. Il venditore riceve un avviso e vede la mancia nell'ordine: «arrivata» se Barattolo ha potuto verificarla, altrimenti «controlla il wallet».

<!-- pezzo libro-006 | libro -->
## Libro · Comprare nel mercatino (2/2)

Tutti i tuoi acquisti e le tue vendite stanno nella scheda «Ordini», con lo stato di ogni ordine e i bottoni per il passo successivo. In fondo all'elenco c'è «📄 Esporta tutti gli ordini in CSV», che scarica un file con tutti i dettagli dei tuoi ordini (utile a chi vende per tenere i conti).

Il feedback: ad affare concluso, dalla pagina dell'ordine, compratore e venditore si lasciano a vicenda un voto da 1 a 5 stelle con un commento breve (chi compra può aggiungere fino a 3 foto). Lo stesso vale per la recensione a fine scambio P2P, che va nella stessa media del profilo. Chi l'ha lasciato può modificarlo una volta sola (stelle e commento; le foto restano) oppure cancellarlo, entro 7 giorni da quando l'ha scritto: sotto il voto ci sono «✏️ Modifica» e «🗑 Cancella», con la data fino a cui valgono. Dopo diventa definitivo. Chi ha ricevuto il feedback viene avvisato del cambio, e sul profilo la riga porta la scritta «modificato». Cancellato è per sempre: su quell'affare non se ne può lasciare un altro. Il feedback lasciato da un altro non si può cambiare: se è offensivo o falso, lo può togliere solo un moderatore (scrivi allo staff). Nessuno può chiederti di cambiare un voto in cambio di qualcosa: se succede, segnalalo allo staff. Le recensioni che hai ricevuto le trovi tutte in un posto: Profilo → «Livello e inviti» → «⭐ Recensioni ricevute» (oppure tocca le stelle sotto il tuo nome in cima al Profilo). Ci sono le ultime 50, del mercatino e degli scambi P2P insieme, come le vedono gli altri nel tuo negozio.

Per un contenuto digitale il venditore può chiederti qualche informazione prima di pagare (per esempio nome, cognome o email, una scelta da un elenco, un sì o un no): rispondi alla cassa. Le risposte viaggiano cifrate dentro l'ordine, le leggete solo tu e il venditore, e si cancellano come l'indirizzo. Il numero di telefono non si può chiedere.

<!-- pezzo libro-007 | libro -->
## Libro · Il deposito di garanzia

Quando compri, i sats non vanno subito al venditore: si fermano in un deposito di garanzia (in gergo escrow) che custodisce Barattolo, su un nodo Lightning suo. Il venditore spedisce tranquillo perché sa che i soldi ci sono; tu sai che non si muovono finché l'oggetto non è arrivato davvero.

I tempi (le cifre esatte sono nei NUMERI DI OGGI):
- dopo la consegna hai un certo numero di ore per controllare l'oggetto e confermare. Oggi i sats non partono da soli: allo scadere arriva un promemoria, e se il silenzio continua interviene un moderatore. Nessuno incassa mentre tu non hai confermato;
- per un codice o un buono digitale le finestre sono più corte, e lì allo scadere i sats vanno al venditore: provalo subito.
- se compri più codici nello stesso ordine (per esempio 10 buoni), si aprono uno alla volta: apri il primo, lo provi e tocchi «✅ Funziona» per vedere il successivo. Ogni codice ha le sue ore per dire «⚠️ Non funziona»: la disputa riguarda solo quel codice, i codici che hai confermato restano pagati al venditore e quelli che non hai mai aperto ti tornano. I sats partono tutti insieme alla fine, quando confermi l'ultimo (se ti fermi e non apri il successivo, dopo un po' vanno al venditore). Chi vende scrive ogni codice nel suo riquadro, e può correggerne uno finché non l'hai aperto.

I sats restano in un conto Lightning della piattaforma solo per il tempo dell'affare: non sono un investimento e non vengono messi a rendere. Quando l'affare si chiude escono, al venditore o a te.

<!-- pezzo libro-008 | libro -->
## Libro · Se qualcosa va storto: la disputa

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
- un pacco perso o rovinato dal corriere è una cosa fra chi spedisce e il corriere: Barattolo garantisce la transazione, non il viaggio. Spedite sempre col tracciamento, e le cose di valore con la copertura del corriere. Chi vende può anche spedire con la posta senza tracciamento (la sceglie fra i corrieri quando segna la spedizione): costa meno, ma il pacco non si può seguire, e se si perde il rischio resta di chi l'ha spedito;
- il deposito garantisce l'oggetto promesso, non i gusti: «non mi piace più» non è un difetto, un oggetto diverso dalla descrizione sì;
- un indirizzo sbagliato lo paga chi l'ha scritto: se il pacco torna indietro, le spese di spedizione restano a te. Per questo prima di pagare ti chiediamo di ricontrollarlo.

Pagare fuori da Barattolo (un bonifico, un pagamento diretto al venditore) vuol dire rinunciare al deposito di garanzia: nessuno può più aiutarti a recuperare i soldi.

<!-- pezzo libro-009 | libro -->
## Libro · Vendere nel mercatino (1/4)

1. Tocca «Vendi» (il tasto ＋ in basso).
2. Aggiungi almeno una foto (senza foto non si pubblica), il titolo, la descrizione, la categoria e il prezzo.
3. Scegli come consegni: spedizione (con i corrieri che usi), punto di ritiro o locker, ritiro a mano in zona, o consegna digitale per codici e buoni.
4. Pubblica. Ogni annuncio passa dalla moderazione, anche quando lo modifichi: se qualcosa non convince resta in attesa di un moderatore, e se viene fermato il messaggio spiega perché e come rimediare.

La «Zona» di un annuncio nuovo parte già scritta con quella del tuo ultimo annuncio (per esempio «Dro (TN)»): se vendi da un altro posto la cambi come ogni altro campo (dal 16 novembre 2026).

Gli annunci esauriti: quando vendi l'ultimo pezzo l'annuncio diventa «Esaurito», resta in fondo al tuo negozio e con «🔄 Rifornisci» torna in vendita appena hai altri pezzi. Se era un pezzo unico che non tornerà (un oggetto usato, per esempio), in «I tuoi annunci» o nella sua pagina tocca «🗑 Elimina»: sparisce dal negozio, da Nostr e dal canale, ma gli ordini e le recensioni restano (dal 16 novembre 2026). Si può fare quando l'ordine di quel pezzo è concluso: con una spedizione, un reso o un rimborso ancora aperti l'app dice di aspettare.

Hai un catalogo grande? Nel Profilo c'è «📥 Importa in blocco»: scarichi il modello CSV, una riga per annuncio, fino a 500 annunci per volta. Ogni riga vuole almeno una foto, con un link nella colonna «foto» (più d'uno separati da |) oppure coi nomi dei file dentro uno ZIP che carichi insieme; una riga senza foto viene scartata. Prima di pubblicare tocchi «🔎 Controlla il file» e vedi cosa va e cosa no. Se hai un negozio Shopify o WooCommerce, nella stessa sezione lo puoi collegare: i prodotti entrano da soli e restano in pari (se la sezione non la vedi, guarda i NUMERI DI OGGI o chiedi allo staff). Nel collegamento (✏️ sul negozio) c'è anche «Categoria dei prodotti»: se vende tutto dello stesso tipo la sceglie lì e vale per tutti, anche per quelli già entrati; con «Decide il negozio» Barattolo usa la categoria del suo e-commerce quando corrisponde a una delle nostre, e il resto va in «Altro». Gli annunci importati passano dalla moderazione come gli altri.

Per incassare da solo imposta il tuo indirizzo Lightning nel Profilo: quando chi compra conferma, i sats ti arrivano lì.

Se spedisci a un locker o a un punto di ritiro, il codice per ritirare il pacco lo manda il corriere a chi hai scritto come destinatario. Se chi compra ha lasciato un'email per il corriere, puoi metterla sull'etichetta e il codice arriva direttamente a lui. Se non l'ha lasciata, il codice arriva a te: appena ce l'hai, apri l'ordine e incollalo in «📦 Istruzioni di ritiro per l'acquirente». È l'unico modo in cui lui lo riceve, e la giacenza dura pochi giorni.

<!-- pezzo libro-010 | libro -->
## Libro · Vendere nel mercatino (2/4)

Le commissioni del mercatino: Barattolo non prende commissioni, né a chi vende né a chi compra. Si pagano solo le commissioni della rete, che non vanno a Barattolo: su Lightning sono pochi sats o niente, on-chain sono quelle dei miner. Se un giorno cambiasse, la cifra sarebbe nei NUMERI DI OGGI. Negli acquisti on-chain può esserci solo una quota fissa a Barattolo per le spese di rete, scritta nel conto prima di pagare: quanto vale oggi lo dicono i NUMERI DI OGGI.

Quando qualcuno chiede delle commissioni, tieni sempre separati il mercatino (zero commissioni di Barattolo, solo quelle della rete) e lo scambio P2P (la commissione del coordinatore, spiegata più sotto). Mescolarli confonde.

Le donazioni: chi vuole sostenere Barattolo con qualche sats può mandarli all'indirizzo Lightning zap@barattolo.store (si incolla nel wallet come destinatario, si sceglie l'importo e si invia), oppure con uno zap al profilo Nostr «Barattolo», che accetta anche bitcoin on-chain. Sono un regalo libero: non danno vantaggi nell'app e non sono mai obbligatorie. Se qualcuno chiede come donare, dai questo indirizzo e ringrazia di cuore.

Quando arriva un ordine il bot ti avvisa. Spedisci, segna il corriere e il codice di tracciamento nell'ordine, e aspetta la conferma di chi compra. Se spedisci una busta senza codice scegli «✉️ Posta senza tracciamento» fra i corrieri: non serve fingere una consegna a mano. Hai scritto un codice sbagliato, o hai segnato «Consegna a mano» su un ordine che invece hai spedito? Nell'ordine c'è il bottone per correggerlo, e chi compra viene avvisato. L'indirizzo di chi compra lo vedi solo tu, per stampare l'etichetta: non usarlo per altro.

Le prestazioni si possono vendere, ma devono essere definite: quanto durano, che cosa comprendono, a che prezzo. «Un'ora di lezione di inglese» sì; «ti faccio quello che ti serve» no.

Su Barattolo non si vendono: armi, droghe, servizi sessuali, refurtiva, contraffazioni, documenti, dati personali, farmaci, animali protetti.

Un venditore può mettere il negozio in ferie (gli annunci restano ma non si comprano) e ha una pagina del negozio col suo link da condividere.

<!-- pezzo libro-011 | libro -->
## Libro · Vendere nel mercatino (3/4)

I codici sconto: nel Profilo, alla voce «🎟 Codici sconto», chi vende crea i suoi codici (in percentuale o a cifra fissa, con una durata e un tetto di usi) e li dà a chi vuole; chi compra lo scrive alla cassa. Col tasto «📣» sulla riga di un codice ancora valido può anche mandarlo ai clienti che hanno già comprato da lui: sceglie chi (sono già tutti spuntati) e preme «Invia invito sconto». Il messaggio lo manda Barattolo, sul bot, come DM Nostr o dentro l'app, e chi vende non vede mai i contatti dei clienti. Ogni cliente riceve lo stesso codice una volta sola, e al massimo un invito a settimana dallo stesso negozio. Un codice scaduto, finito o in pausa non si può mandare: si riattiva con ✏️ (scegliendo di nuovo i giorni, che ripartono da oggi). La data «scade il» è scritta all'italiana, giorno/mese/anno. Chi riceve le offerte e non le vuole più le spegne in Profilo → «🔔 Avvisi» → «🎟️ Offerte dei negozi», per tutti i negozi o per uno solo.

Chi vende contenuti digitali può aggiungere all'annuncio le domande da fare a chi compra (testo breve, elenco a tendina, email, sì/no), obbligatorie o facoltative; nome, cognome ed email si aggiungono con un tocco. Il numero di telefono non si può chiedere.

<!-- pezzo libro-012 | libro -->
## Libro · Vendere nel mercatino (4/4)

La cassa in negozio (se nelle REGOLAZIONI del pannello «Cassa in negozio» è accesa): chi vende di persona, in un negozio, a un banco del mercato o a un evento, può usare Barattolo come cassa. Nel Profilo, nel gruppo «Negozio e spedizioni», c'è «🏪 Cassa in negozio»: apre «Barattolo Negozio», la faccia di Barattolo per chi sta al banco, con lo stesso account e senza la barra di Barattolo (si torna con «↩ Barattolo» in alto a destra; dal browser, per esempio sul tablet del banco, ci si arriva anche dall'indirizzo barattolo.store/?app=negozio). Ha due schede: «🧾 Cassa» e «📒 Vendite», cioè le vendite della cassa; a chi tiene un punto di ritiro di Barattolo compare anche «📦 Banco» coi pacchi in arrivo. La Cassa è fatta come il carrello: le card dei propri annunci attivi con almeno un pezzo, ognuna con «Aggiungi» (o un tocco sulla card) e poi i tasti «−» e «+»; in fondo la stessa barra del carrello col totale e i pezzi, e al posto di «Controlla e paga» il bottone «Incassa». Sopra le card si può anche scrivere un importo libero (in euro o in sats, il tasto accanto cambia valuta), e una nota per sé (es. «tavolo 4»). Se non ci sono annunci attivi la Cassa lo dice, e si incassa scrivendo l'importo. Compare un QR grande con due porte, «⚡ Lightning» e «On-chain»: il cliente lo inquadra con qualsiasi wallet, e non gli serve un account su Barattolo né Telegram. I sats vanno DRITTI al wallet di chi vende: in Lightning al suo Lightning address del Profilo, on-chain a un indirizzo nuovo del suo wallet (quello scelto in Profilo → «Incassi on-chain»), mai al deposito di garanzia. Per questo non c'è deposito, né spedizione, né conferma, né disputa, e Barattolo non prende commissioni: è un pagamento di persona, come al banco. Ogni vendita della cassa finisce comunque in «Ordini», insieme agli altri ordini, con il segno «🏪 Cassa in negozio»: il filtro «🏪 Cassa» in cima a «Ordini» mostra solo quelle (stanno anche in «Vendite»), e toccandone una si riapre la sua ricevuta. Il totale di oggi si legge in cima alla cassa. Quando il pagamento arriva la cassa dice «✅ Pagato!». Se il wallet di chi vende non comunica i pagamenti, la cassa dice di guardare il proprio wallet e di toccare «✓ Ricevuto». On-chain, appena il pagamento si vede in rete la cassa dice «in arrivo»: per una cifra piccola si può consegnare subito («✓ Consegna adesso»), per una grande è meglio aspettare la conferma (di solito fra 10 e 60 minuti). On-chain si incassa da 546 sats in su. I pezzi venduti alla cassa escono da soli dalla vetrina, e l'annuncio finito diventa venduto. Per usare la cassa serve almeno uno fra il Lightning address e il wallet on-chain nel Profilo: se mancano, la cassa lo dice e porta al campo giusto.

<!-- pezzo libro-013 | libro -->
## Libro · Spedizione, indirizzo e ritiro

- Spedizione a un indirizzo: lo scrivi al momento dell'acquisto e resta dentro l'ordine. Lo vede solo il venditore, è cifrato nel database e viene cancellato appena confermi di aver ricevuto. I moderatori non lo leggono, nemmeno in disputa.
- Punto di ritiro o locker: un tuo indirizzo non serve proprio; al banco basta il nome del destinatario. Puoi lasciare un'email se vuoi che il codice di ritiro te lo mandi il corriere: è facoltativa.
- Ritiro a mano: vi accordate per vedervi in zona. Controlla l'oggetto prima di confermare.

<!-- pezzo libro-014 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (1/11)

Nel P2P non compri da Barattolo: compri da un'altra persona. Vi accordate su un prezzo, gli euro viaggiano fra voi due col metodo scelto, e i sats restano bloccati in garanzia finché gli euro non sono arrivati. Barattolo non tocca i tuoi euro. Si entra dal tasto «P2P» in basso; lì ci sono il «Libro ordini», «I miei scambi», «Pubblica» e «Info P2P», che spiega tutto con calma.

Come funziona, in cinque passi:
1. Qualcuno pubblica un ordine: dice se compra o vende sats, per quanti euro e con quali metodi di pagamento. L'ordine va nel libro, che vedono tutti.
2. Tu lo prendi: scegli il metodo e l'ordine si riserva a te. La tua scelta arriva all'altra persona: nella pagina dello scambio legge «ha scelto…» (per esempio «USDT su Tron» o «SEPA Instant»), la stessa riga in cima alla chat dello scambio, e un avviso su Telegram. Se un recapito arrivato è per un metodo o una rete diversi da quelli scelti, la pagina lo dice in rosso: prima di pagare, chiarite in chat.
3. Chi vende blocca i sats: paga una richiesta speciale (una hold invoice) che trattiene i sats senza consegnarli. Da lì sono in garanzia.
4. Chi compra manda gli euro col metodo scelto, al recapito che l'altra persona lascia dentro lo scambio, e poi lo dice nell'app.
5. Chi vende controlla di aver ricevuto gli euro e libera i sats: arrivano all'indirizzo Lightning o alla fattura di chi compra.

La garanzia: i sats in garanzia possono prendere due strade sole, andare a chi compra o tornare a chi vende. Nessuno può dirottarli altrove. A tenerli è il coordinatore, un programma che si chiama Mostro: lo fa girare Barattolo, sul suo nodo.

Come si legge una card del libro: in alto a destra due quadratini con una freccia dicono cosa invii e cosa ricevi (le stelle blu dell'Europa per gli euro, la T verde di Tether per gli USDT, il fulmine nero per i sats su Lightning, la ₿ arancio per bitcoin on-chain). Sotto ci sono la cifra da inviare e quella da ricevere, i metodi di pagamento e, nel riquadro in fondo, la faccia di chi ha pubblicato con le sue stelline e quanti scambi P2P ha già fatto («✅ 22 scambi P2P»); toccando la faccia si apre il suo negozio (anche sulle card on-chain; se non ha ancora un negozio, l'app te lo dice e non apre l'ordine). La riga colorata sul bordo di sotto è il tempo che resta all'ordine: si accorcia, diventa arancio negli ultimi tre giorni e rossa, lampeggiante, nell'ultimo.

<!-- pezzo libro-015 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (2/11)

Il prezzo di bitcoin nel libro: in cima al libro P2P, sotto i rettangoli «Novità», c'è la card «1 BTC adesso» col prezzo in euro (lo stesso che l'app usa per i conti, aggiornato ogni minuto), quanto è salito o sceso e una piccola linea, verde se sale e rossa se scende. Toccandola si passa dalle ultime 24 ore ai 7 giorni e ai 30 giorni; toccando il simbolo € si passa ai dollari (prezzo, linea e percentuale in dollari) e un altro tocco torna agli euro. La card è grafite lucida, un grigio scuro con un riflesso in alto a sinistra (dal 16 novembre 2026), sia di giorno sia di sera, per staccarsi dagli ordini; in dollari è identica a quella in euro (linea, percentuale e periodo, e il tocco cambia periodo anche lì). Subito dopo un aggiornamento può mostrare solo il prezzo, finché non ha la storia del periodo.

Quanto si può per ordine nel P2P, per ora (fase beta): fino a 250 € negli scambi in Lightning e fino a 999 € in quelli on-chain (dal 16 novembre 2026; prima 500 €, e fino al 12 novembre 250 €). Lo stesso tetto di 999 € vale per gli acquisti on-chain del mercatino e per chi prende un ordine ricevendo sull'altra rete. Il foglio «Pubblica» lo scrive sotto la cifra e non lascia andare oltre.

Il prezzo: gli ordini si scrivono in euro e i sats si contano al cambio del momento, per questo finché l'ordine è nel libro la cifra in sats ha il segno ≈. La cifra esatta si fissa quando l'ordine viene preso. Alcuni ordini hanno un intervallo («da 20 a 100 €»): lì scegli tu quanto.

I tasti «Compra BTC» e «Vendi BTC» in cima al libro P2P sono due pillole (dal 16 novembre 2026, di giorno e di sera): quella accesa, verde per «Compra BTC» e corallo per «Vendi BTC», dice quale lato del libro stai guardando.

L'ordine del libro: in cima al libro P2P la pillola con le tre righe (di serie dice «Recenti») apre «Ordina il libro», con quattro scelte: Più recenti, Convenienza, Importo dal più grande, Importo dal più piccolo. La pillola diventa arancio quando l'ordine non è quello di serie. Dal 14 novembre 2026 la scelta resta salvata su quel telefono o computer: alla visita dopo il libro si apre già ordinato così, sia in «Compra» sia in «Vendi». Su un altro dispositivo si sceglie di nuovo. Le card on-chain e quelle Lightning stanno nello stesso ordine, qualunque sia la scelta: con «Più recenti» la più nuova sta in cima, on-chain o Lightning che sia (dal 16 novembre 2026).

Premio e sconto: chi pubblica può chiedere fino al 20% sopra o sotto il prezzo di mercato. Sopra si chiama premio e conviene a chi vende, sotto si chiama sconto e conviene a chi compra. La riga c'è sempre nel conto.

<!-- pezzo libro-016 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (3/11)

La commissione del P2P la decide il coordinatore ed è già dentro i sats che passano di mano: chi vende ne blocca un po' di più, chi compra ne riceve un po' di meno. Nell'ottobre 2026, durante la beta, è il 3% in tutto, cioè 1,5% per chi compra e 1,5% per chi vende; finita la beta sarà del 4% (2% per parte). Pionieri e chi è al livello 5 hanno uno sconto dello 0,5% sulla propria parte. La cifra esatta la vedi sempre nel conto, prima di prendere un ordine. Dal 16 novembre 2026 la stessa commissione, con gli stessi sconti, vale anche negli scambi P2P on-chain (a tre chiavi); gli acquisti del mercatino, anche on-chain, restano senza commissioni di Barattolo (on-chain al più la quota fissa per le spese di rete, vedi «Bitcoin on-chain»). Pubblicare o prendere un ordine non costa niente. Il riquadro colorato delle commissioni in cima al libro P2P compare solo la prima volta, alla fine del tutorial: poi non c'è più, e si rivede rifacendo «Come funziona» fino a «Fine 🎉» (toccandolo si apre il dettaglio con lo sconto).

I metodi di pagamento degli euro sono un elenco chiuso: SEPA (il bonifico), SEPA Instant, Revolut, Satispay, PayPal, Wise, Contanti (di persona) e Contanti al tabacchino (Barattozon). Quando pubblichi un ordine vedi subito SEPA, Revolut, Satispay e Contanti; SEPA Instant, PayPal, Wise e il tabacchino si aprono toccando «Altri metodi ▾». Chi prende un ordine sceglie fra i metodi messi da chi l'ha pubblicato, e il filtro del libro li ha tutti. Wise c'è dal 2 novembre 2026: chi riceve gli euro su Wise dà il suo Wisetag, l'email del conto Wise o l'IBAN che Wise gli ha dato (con l'IBAN può pagare anche chi Wise non ce l'ha, con un bonifico). Gli euro non passano da Barattolo: il recapito (IBAN, numero, tag) ve lo scambiate dentro lo scambio, cifrato. La garanzia protegge i sats, non gli euro: se chi compra dice di aver mandato gli euro e non è vero, chi vende semplicemente non libera; se li ha mandati e chi vende non libera, c'è la disputa.

I tempi: se il tempo scade prima che i sats siano bloccati non perde niente nessuno, e l'ordine torna nel libro o si chiude. Coi sats in garanzia avete circa quattro giorni: se chi compra non ha detto di aver pagato, allo scadere i sats tornano da soli a chi vende; se l'ha detto, si apre una disputa.

<!-- pezzo libro-017 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (4/11)

La ripubblica (dal 16 novembre 2026): gli ordini nel libro durano un tempo fissato, una settimana, sia quelli Lightning sia quelli on-chain (dal 16 novembre 2026; prima gli on-chain 24 ore), e poi scadono se nessuno li ha presi. Nel foglio «Pubblica», sotto il paracadute, c'è la sezione «🔁 Ripubblica»: scrivi due prezzi di un bitcoin, da X a Y, nella valuta dell'ordine (euro, franchi, o dollari per gli USDT; per gli ordini in ETH, Monero o USDe il prezzo di BTC è in euro). Quando l'ordine scade, se in quel momento BTC è fra quei due prezzi (anche esattamente su uno dei due), l'ordine viene ripubblicato uguale: stessa cifra, a prezzo fisso gli stessi sats, a mercato lo stesso premio o sconto, stessi metodi, zona e paracadute. Succede a ogni scadenza, finché BTC resta dentro. Se lasci i campi vuoti non si ripubblica niente, e il foglio riparte sempre vuoto. Il bot ti avvisa ogni volta, nel messaggio della scadenza: «Lo ripubblico uguale» oppure «Non l'ho ripubblicato», col prezzo di BTC di quel momento. Gli ordini Lightning li ripubblica il tuo telefono appena apri Barattolo (su qualunque pagina, senza fare niente): finché non lo apri l'ordine resta fuori dal libro, e se nel frattempo BTC è uscito dall'intervallo non si ripubblica. Gli ordini on-chain li ripubblica Barattolo subito, anche a telefono spento, per un'altra settimana. Per smettere: nella pagina del tuo ordine tocca «Non ripubblicarlo più». Sulla card del tuo ordine c'è la riga «🔁 Ripubblica da… a…». Non vale per Barattozon in «Vendi BTC» (il PayCode scade da solo); vale invece per Barattozon in «Compra BTC», dove il PayCode lo scrive chi prende l'ordine (dal 16 novembre 2026), e per gli ordini in ETH, Monero o USDe. Barattolo decide solo con un prezzo di BTC aggiornato, mai con uno vecchio.

La disputa nel P2P: si apre solo coi sats già in garanzia, col bottone «⚠️ Apri una disputa» in fondo alla pagina dello scambio. Ferma lo scambio e chiama un moderatore, che potrà leggere la chat di quello scambio. Se è solo una domanda o un ritardo, prima scrivi all'altra persona nella chat. Chi vende può sempre liberare i sats anche a disputa aperta, e la disputa si chiude.

La chat dello scambio: da quando l'ordine è preso a quando lo scambio finisce c'è una chat fra voi due, cifrata, con foto e PDF. A fine scambio si cancella. Barattolo non ti scrive mai nella chat dello scambio: chi lì si presenta come «assistenza» è l'altra persona.

Contanti di persona (metodo «Contanti»): ci si incontra, chi compra sats porta le banconote, chi vende le conta e libera i sats lì, davanti all'altro. Le regole:
- i contanti si consegnano solo quando chi vende preme «Libera i sats» davanti a te, e si va via solo con lo scambio concluso;
- vedetevi in un posto pubblico e di giorno, contate insieme, mai grosse cifre da soli;
- chi vende fissa l'appuntamento (giorno, ora, luogo) dentro lo scambio;

<!-- pezzo libro-018 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (5/11)

- all'arrivo ognuno può toccare «📍 Sono qui»: registra ora e, se il telefono la dà, la posizione. È facoltativo ma aiuta nelle dispute;
- c'è un tetto in euro per scambio (vedi i NUMERI DI OGGI); sopra si divide in più ordini. Chi prende un ordine in contanti può dover bloccare una piccola cauzione.

Gli avvisi dei nuovi ordini P2P: nel libro P2P, la campanella 🔔 in alto apre «Avvisami dei nuovi ordini P2P». Acceso, il bot ti scrive quando nel libro arrivano ordini nuovi del tipo che scegli (vendita BTC, acquisto BTC, Barattozon). Sotto «Convenienza» puoi lasciare «Tutti» oppure toccare «Con un limite» e scegliere fin dove ti va bene: «Fino a 10% peggio», «Fino a 5% peggio», «Fino a 2% peggio», «A prezzo di mercato o meglio», «Almeno 2% meglio», «Almeno 5% meglio». «Peggio» e «meglio» sono sempre dal tuo punto di vista, rispetto al prezzo di mercato: con «Fino a 5% peggio» ti avvisa di tutto tranne gli ordini che ti costerebbero più del 5% sopra il mercato (o che, se vendi, pagano più del 5% sotto). Lo stesso blocco sta nel Profilo, nel cassetto «🔔 Avvisi». Non ti avvisa mai dei tuoi ordini.

La mappa del contanti: nel libro P2P, in alto accanto alla campanella, il tondo con la mappa colorata 🗺️ apre l'Italia coi pallini delle offerte in contanti di persona. Dal 16 novembre 2026 c'è sempre, sia in «Compra BTC» sia in «Vendi BTC»: se nel tab non ci sono offerte in contanti la mappa si apre vuota e lo dice. In fondo alla mappa c'è l'interruttore «Notifiche nuove offerte in contanti», spento di serie: acceso, sul tondo compare quante offerte in contanti nuove sono arrivate dall'ultima volta che hai aperto la mappa, e aprendola il numero sparisce. La scelta resta su quel telefono; si vede anche mentre scorri le card. Ogni pallino sta sul centro del comune dove la persona propone di vedersi, mai su un indirizzo. Si avvicina con due dita, con la rotellina o con un doppio tocco; toccando un comune l'elenco mostra solo le sue offerte e la pagina scende da sola fino a loro.

La mappa del ritiro a mano: nel mercatino, in fondo alla barra di ricerca, il tondo 🗺️ apre l'Italia coi pallini degli annunci che si possono ritirare di persona («🤝 Ritiro in zona», anche insieme alla spedizione). Ogni pallino sta sul centro del comune scritto nella «Zona» dell'annuncio, mai sull'indirizzo: il posto esatto si decide in chat. Con la mappa aperta sotto restano solo gli annunci col ritiro a mano; toccando un comune restano solo i suoi (la pagina scende da sola fino a loro), e la pillola «📍 Comune ✕» riporta a tutti. Si muove come quella del P2P: due dita, rotellina, doppio tocco, ＋ − ⟲. In fondo alla mappa l'interruttore «Notifiche nuovi annunci col ritiro a mano», spento di serie: acceso, sul tondo compare quanti annunci col ritiro sono arrivati dall'ultima volta che hai aperto la mappa. Per comparire sulla mappa basta scrivere il nome del comune nella «Zona» quando si vende.

<!-- pezzo libro-019 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (6/11)

Revolut: chi riceve gli euro su Revolut sceglie come, con tre bottoni nel modulo del recapito: RevTag (di serie), numero di telefono, oppure IBAN con l'intestatario.

Se chi vende chiede di annullare uno scambio coi sats già in garanzia, chi compra non è obbligato ad accettare: se ha già mandato gli euro o li vuole mandare, ha ancora «Ho inviato gli euro», e può aprire una disputa.

Barattozon (nel libro «Contanti al tabacchino»): chi vende sats fa un ordine Amazon da pagare in contanti nel punto vendita, e chi compra lo paga alla cassa di un tabacchino abilitato col PayCode. Il PayCode vale almeno 25 € e Amazon lo accetta fino a 999 €. Il PayCode arriva a chi compra solo quando i sats sono in garanzia (prima nella pagina non si vede), quindi si paga solo quando la pagina dice «Sats in garanzia»; si tiene lo scontrino come prova, e poi si tocca «Ho pagato al tabacchino». Chi vende controlla su Amazon che l'ordine risulti pagato e libera i sats. Alla cassa bisogna dire «devo pagare un ordine Amazon in contanti con un PayCode»: non una ricarica e non un buono regalo. Barattozon c'è da tutti e due i lati del libro: anche chi COMPRA sats può pubblicare un ordine «al tabacchino», con una fascia di euro (per esempio da 30 a 80 €, il massimo è obbligatorio); chi vende lo prende scrivendo il PayCode (importo esatto, le nove cifre, la scadenza) e chi compra lo paga al tabacchino.

Altre valute e reti (solo se nei NUMERI DI OGGI risultano disponibili): ordini P2P pagati in USDT al posto degli euro (qui sotto), ordini P2P in franchi svizzeri (CHF), ordini P2P in ETH, Monero o USDe, e scambi P2P coi bitcoin on-chain, con la garanzia a firme multiple (due chiavi su tre).

Ordini P2P in USDT (se nei NUMERI DI OGGI «Ordini P2P in USDT» è acceso): al posto degli euro si paga in USDT, il dollaro digitale di Tether (1 USDT vale 1 dollaro). I sats restano su Lightning con la garanzia di sempre (per gli USDT negli scambi on-chain vedi più sotto); gli USDT passano direttamente da una persona all'altra, e Barattolo non li tocca mai. Le reti sono solo due, Tron (TRC-20) ed Ethereum (ERC-20), mai altre: in un ordine in USDT le reti prendono il posto dei metodi di pagamento.
- Nel libro un ordine in USDT si riconosce dalla T verde di Tether nei quadratini in alto a destra della card.
- Nella home, nella fila «Scambi P2P», la card di un ordine in USDT è verde, con la moneta ₿ accanto alla T di Tether, e la cifra è scritta in USDT. Gli ordini in euro hanno la card di sempre, col ₿ e l'euro.
- Dal 16 novembre 2026 nella fila della home ci sono anche gli ordini on-chain (anche in USDe, ETH, Monero e franchi), mescolati con quelli Lightning, il più nuovo per primo. In fondo a ogni card, a destra, un piccolo simbolo dice la rete: il fulmine per Lightning, la ₿ arancio per on-chain. Toccando una card on-chain si apre il suo foglio. I propri ordini non compaiono nella propria home (si vedono nel libro e in «I miei scambi»), ma gli altri li vedono.

<!-- pezzo libro-020 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (7/11)

- In cima al libro c'è il rettangolo verde delle stablecoin, «USDT · USDe · Novità» (dal 16 novembre 2026 USDT e USDe stanno insieme; ETH e Monero hanno il loro rettangolo blu): toccandolo parte un breve tutorial che mostra come riconoscere un ordine in USDT, come pubblicarne uno e come si paga senza sbagliare rete. Si può rivedere toccandolo di nuovo.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta, euro o USDT. Con USDT si scelgono le reti (Tron, Ethereum o tutte e due) e l'importo si scrive in USDT. Il tetto della fase beta è lo stesso degli euro, convertito in USDT.
- Un ordine in USDT con un intervallo («da 50 a 276 USDT, scegli tu»): toccandolo, nel foglio «Quanto vuoi scambiare?» la cifra si scrive in USDT, e i sats si contano al cambio del dollaro (1 USDT = 1 $), non dell'euro. Per questo 276 USDT valgono meno sats di 276 €.
- Chi riceve gli USDT (cioè chi vende i sats) scrive nello scambio il suo indirizzo USDT, copiato dal suo wallet. L'app controlla che sia della rete giusta e ferma un indirizzo bitcoin, Lightning, Liquid o dell'altra rete, perché con la rete sbagliata gli USDT si perdono. Un limite da sapere: un indirizzo Ethereum (0x…) vale anche su reti che non offriamo (Polygon, BNB, Arbitrum…), quindi chi paga deve mandare proprio sulla rete scritta nello scambio.
- Chi paga vede la rete in grande, l'indirizzo col QR e il contratto del vero USDT, per non farsi ingannare da token falsi che si chiamano «USDT» anche loro. Sotto l'indirizzo c'è la riga «Da mandare» con la cifra esatta in USDT e il suo tasto «📋 Copia», come per l'indirizzo: copia solo il numero, col punto (per esempio 25.00), pronto da incollare nel wallet. Manda gli USDT, incolla l'id della transazione (lo trova nei dettagli dell'invio, nel wallet) e tocca «💵 Ho inviato gli USDT».
- Chi vende controlla che siano arrivati sulla rete giusta, anche col tasto «🔎 Controlla su Tronscan» (o Etherscan) sotto l'id, e libera i sats solo quando ci sono davvero. Se qualcosa non torna si apre una disputa: il moderatore legge l'id della transazione sulla rete giusta.

Ordini P2P in franchi svizzeri (se nei NUMERI DI OGGI «Scambi P2P pagati in franchi svizzeri (CHF)» è disponibile): al posto degli euro l'ordine è in franchi svizzeri, CHF. I sats restano su Lightning con la garanzia di sempre; i franchi passano direttamente da una persona all'altra, e Barattolo non li tocca mai.
- Nel libro un ordine in franchi si riconosce dalla croce bianca su fondo rosso nei quadratini in alto a destra della card; nella home la sua card è rossa, col ₿ accanto al franco, e la cifra è scritta in CHF.

<!-- pezzo libro-021 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (8/11)

- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta CHF. I metodi sono TWINT, bonifico svizzero («Bonifico CH»), Revolut, Wise e contanti di persona; TWINT e il bonifico svizzero esistono solo negli ordini in franchi. Il tetto della fase beta è lo stesso degli euro, convertito in franchi al cambio del momento, e vale anche per i contanti di persona. Barattozon non è in franchi; gli scambi on-chain sì (dal 16 novembre 2026): i bitcoin restano nel deposito a tre chiavi, chi compra paga in franchi.
- Chi riceve i franchi scrive nello scambio dove riceverli: per TWINT il numero di cellulare svizzero (+41 7…), per il bonifico svizzero intestatario e IBAN svizzero (comincia con CH o LI, 21 caratteri). L'app controlla il numero e l'IBAN prima che partano, e ferma un numero non svizzero o un IBAN con una cifra sbagliata.
- Chi paga manda i franchi e tocca «Ho inviato i franchi»; chi vende controlla di averli ricevuti e libera i sats.

Ordini P2P in ETH, Monero o USDe (se nei NUMERI DI OGGI «Scambi P2P pagati in ETH, Monero (XMR) o USDe» è disponibile): sono tre valute a sé, come l'euro, l'USDT e i franchi. Con ognuna si comprano o si vendono sats, che restano su Lightning con la garanzia di sempre; la moneta passa direttamente da una persona all'altra, e Barattolo non la tocca mai. ETH è Ethereum, XMR è Monero, USDe è il dollaro digitale di Ethena.
- Per pubblicarne uno: scheda «P2P», nuovo ordine, e in cima al foglio si sceglie la valuta: EUR, USDT, ETH, XMR o USDe. Sotto compare solo la sua lista: con ETH «ETH (Ethereum)», con XMR «XMR (Monero)», con USDe le sue cinque reti, «USDe (Ethereum)», «USDe (Arbitrum)», «USDe (Base)», «USDe (BNB Chain)» e «USDe (Solana)», una o più. Con l'euro restano solo i metodi classici (bonifico, Revolut, contanti…).
- L'importo si scrive nella moneta (per esempio 0,02 ETH o 50 USDe), ed è uno solo, senza una fascia «da… a…». Dal 16 novembre 2026 funziona come in euro: a prezzo di mercato la cifra in moneta resta quella, e i sats si fanno quando qualcuno prende l'ordine, al cambio di quel momento e col premio o lo sconto scelto. Il cambio della moneta conta al mezzo euro. Se il cambio si sposta di oltre il 5% da quando l'ordine è stato pubblicato, chi l'ha pubblicato lo vede scritto nella pagina dell'ordine; se si sposta troppo (circa il 30%) l'ordine non si può più prendere e conviene rifarlo. Si può anche scrivere un prezzo fisso in sats: allora i sats non cambiano più. Per ordini molto piccoli o vicini al tetto può succedere che il mercato non ci stia: allora i sats si fissano quando si pubblica, come prima.
- Nel libro ogni valuta ha il suo filtro in cima (EUR, USDT, ETH, XMR, USDe), e la card mostra il logo della moneta nei quadratini in alto a destra e la cifra nella moneta, per esempio «Invia 0,0153 ETH».

<!-- pezzo libro-022 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (9/11)

- Chi riceve scrive nello scambio il suo indirizzo, copiato dal wallet. L'app controlla che sia della moneta e della rete giusta e ferma un indirizzo sbagliato o con un refuso. Un limite da sapere: Ethereum, Arbitrum, Base e BNB Chain hanno indirizzi uguali (0x…), quindi chi paga deve mandare proprio sulla rete scritta nello scambio. Per USDe lo scambio mostra anche il contratto del vero USDe, contro i token falsi con lo stesso nome.
- Chi paga vede l'indirizzo col QR e la cifra esatta da mandare, che è quella dell'ordine. Manda, incolla l'id della transazione e tocca «Ho inviato». Con Monero serve anche la chiave della transazione (tx key), che il wallet di chi manda conserva: Monero è privato, e solo con id, chiave e indirizzo si vede quanto è arrivato.
- Chi vende controlla l'arrivo col tasto «🔎 Controlla su …» (Etherscan, xmrchain, Arbiscan, Basescan, BscScan o Solscan) e libera i sats solo quando ci sono davvero. Se qualcosa non torna si apre una disputa.
- Dal 16 novembre 2026 ETH, Monero e USDe ci sono anche negli scambi on-chain (a tre chiavi): i bitcoin restano nel deposito, chi compra paga nella moneta. Lì si sceglie una rete sola, e chi paga vede rete, cifra da copiare e QR; non incolla l'id della transazione, ma lo conserva perché in una disputa lo chiede il moderatore.
- In cima al libro (dal 16 novembre 2026) ci sono tre rettangoli «Novità»: quello arancio «On-Chain», quello verde delle stablecoin «USDT · USDe» (dice solo quel che c'è) e quello blu «ETH · XMR». Ognuno apre il suo breve tutorial: il verde mostra un ordine in USDe col bollino della rete, il foglio e le reti; il blu mostra le due monete, il foglio in ETH e il prezzo di mercato. Si possono rivedere toccandoli di nuovo. Scorrendo il libro verso il basso i tre diventano un rettangolo solo, con le icone di tutte le monete e la scritta «Novità», che resta in alto; scorrendo verso l'alto (o toccandolo) tornano subito i tre.
- Nel foglio «Pubblica», scelta una rete sola di USDT o USDe, l'icona della valuta porta in alto a destra il bollino della rete, come nella card del libro.

Scambi P2P on-chain (se nei NUMERI DI OGGI «Scambi P2P in bitcoin on-chain» è disponibile): si scambiano bitcoin sulla rete principale, non su Lightning. La garanzia non è quella di Lightning: chi vende blocca i bitcoin in un deposito a tre chiavi, una sua, una di chi compra e una di Barattolo, e per spostarli ne servono due. Barattolo da solo non li può muovere.
- Nel libro uno scambio on-chain si riconosce dalla moneta arancio ₿ (quelli di Lightning hanno il fulmine). Sopra le card c'è il rettangolo arancio «On-Chain» con la scritta «Novità», che apre la pagina «Scambi on-chain»: lì si pubblica («Pubblica uno scambio on-chain») e si seguono i propri.

<!-- pezzo libro-023 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (10/11)

- Per pubblicare si può anche toccare il + di «Compra BTC» o «Vendi BTC» e scegliere «On-chain» invece di «Lightning». Serve aver preparato Profilo → «₿ On-chain» (le 12 parole e la loro copia: vedi «Bitcoin on-chain»). Un ordine resta nel libro 7 giorni (dal 16 novembre 2026; prima 24 ore); il tetto per ordine è quello on-chain dei NUMERI DI OGGI e del paragrafo sui limiti.
- Il giro, passo per passo: chi prende fa nascere l'indirizzo a tre chiavi. Chi vende ha 6 ore per depositare con «🔒 Blocca i sats»: i sats dello scambio più un piccolo margine per la commissione della rete, più la sua metà della commissione del P2P. Con una conferma della rete (circa dieci minuti) lo scambio va avanti, e tutti e due ricevono l'avviso. Allora chi compra manda gli euro col metodo scritto e tocca «💶 Ho inviato gli euro». Chi vende li controlla sul suo conto e SOLO quando li vede tocca «🔓 Ricevuti: libera i sats»; la seconda firma la mette da solo il telefono di chi compra, e i bitcoin partono.
- Chi compra deve dire dove ricevere: nello scambio c'è «Dove ricevi i bitcoin?», si incolla un proprio indirizzo e si tocca «✍️ Firma e usa questo indirizzo». Chi ha messo nel Profilo la chiave del conto del suo wallet non deve scriverlo ogni volta: ogni scambio arriva a un indirizzo nuovo.
- Se il deposito non arriva in tempo, chi compra può rinunciare («Rinuncia: il deposito non è arrivato»); chi deve depositare e non ha ancora mandato niente può annullare («Annulla (non deposito)»). Con i sats già nel deposito non si annulla da soli: si esce col rimborso d'accordo o con «⚖️ Apri una disputa». Decide un moderatore di Barattolo, Barattolo mette la sua firma e la seconda la mette il telefono di chi ha ragione.
- La commissione (dal 16 novembre 2026) è quella degli scambi Lightning, metà a testa e con gli stessi sconti: chi vende deposita la sua metà insieme ai sats, chi compra riceve i sats meno la sua metà. Nel conto dello scambio, e già nel foglio prima di prendere, c'è la riga «Fee P2P» con la percentuale, come negli scambi Lightning. Se lo scambio finisce col rimborso a chi vende, torna tutto, commissione compresa. Sotto i 546 sats di commissione in tutto non si paga niente.
- A fine scambio la pagina dice «Concluso: i sats sono andati al wallet di chi ha comprato» oppure «Rimborsato: i sats sono tornati a chi li aveva depositati».
- La barra del tempo sotto un ordine on-chain del libro conta i suoi 7 giorni come quella degli ordini Lightning: arancio negli ultimi tre giorni, rossa l'ultimo. Nel foglio di chi prende un ordine on-chain c'è la riga «Tempo rimasto» col conto e la barra, come nella pagina di un ordine Lightning: dal 16 novembre 2026 è una riga sola, non più l'anello rotondo.

<!-- pezzo libro-024 | libro -->
## Libro · Lo scambio P2P: comprare e vendere bitcoin per euro (11/11)

- USDT negli scambi on-chain (se nei NUMERI DI OGGI «Scambi P2P on-chain pagati in USDT» è disponibile): la garanzia resta il deposito bitcoin a tre chiavi, e al posto degli euro chi compra paga in USDT su Tron o Ethereum, da persona a persona, con le stesse regole degli ordini in USDT qui sopra: chi vende scrive il suo indirizzo USDT, chi paga incolla l'id della transazione e tocca «Ho inviato gli USDT». Un ordine è in una valuta sola: o euro o USDT.

Ricevere o pagare su un'altra rete (se nei NUMERI DI OGGI «P2P su un'altra rete» è disponibile): la rete di un ordine dice come paga chi l'ha pubblicato, ma chi lo prende può usare l'altra, con uno swap di SATS Routing fatto dal suo telefono (come la pagina «Swap»). Il costo dello swap si vede prima di confermare, e Barattolo non aggiunge commissioni.
- La scelta si fa già nel foglio che si apre toccando l'ordine (dal 16 novembre 2026): sotto «Stai comprando sats» / «Stai vendendo sats» ci sono i due tasti «⚡ Lightning» e «₿ On-chain», già accesi sulla rete dell'ordine. Toccando l'altra rete compare subito quanto costa lo swap di SATS Routing e quanto arriva (o quanto si paga), e nel dettaglio sotto ci sono due righe che il totale conta: «Swap SATS Routing 0,6%» (la commissione del servizio) e «Rete dello swap» (le transazioni sulla rete bitcoin), così si vede che lo swap non è la commissione del P2P anche quando le due cifre si somigliano; la scelta resta, e dopo aver preso il foglio giusto si apre già su quella rete. I tasti ci sono solo dove l'altra rete si può davvero usare.
- Ordine Lightning, ma vuoi ricevere bitcoin on-chain: nel foglio «Dove ricevere i sats» scegli «₿ On-chain», incolli un tuo indirizzo bitcoin e l'app ti dice quanti sats ti arrivano circa e quanto costa lo swap. Alla liberazione i sats diventano bitcoin al tuo indirizzo. Se il moderatore dà ragione a chi vende, lo swap scade senza costare niente.
- Scambio on-chain, ma vuoi ricevere in Lightning: nello scambio tocchi «⚡ Ricevi in Lightning» e, quando chi vende ha confermato gli euro, incolli una tua richiesta Lightning (o «⚡ Prendila dal mio Lightning address») e tocchi «✅ Conferma lo swap». Ti arriva il prezzo meno il costo dello swap; se la richiesta non si riesce a pagare, i bitcoin tornano da soli al tuo wallet on-chain di Barattolo. Si torna indietro con «₿ Ricevi on-chain invece».
- Scambio on-chain che hai preso tu per vendere, ma hai solo sats Lightning: nel foglio «🔒 Blocca i sats» scegli «⚡ Lightning» e tocchi «⚡ Crea la richiesta Lightning»; la paghi col tuo wallet e lo swap mette i bitcoin nel deposito a tre chiavi. Un annullo o un rimborso tornano però on-chain, al tuo wallet di Barattolo.
- Lo swap ha i suoi limiti di cifra (quelli di SATS Routing): fuori dai limiti l'app lo dice e lo scambio si fa sulla rete dell'ordine.

<!-- pezzo libro-025 | libro -->
## Libro · Bitcoin on-chain (1/2)

Oltre a Lightning, alcune funzioni usano i bitcoin «on-chain», cioè sulla rete principale di Bitcoin: la moneta arancione ₿ le indica in tutta l'app. Quali sono accese, e per chi, lo dicono i NUMERI DI OGGI: una funzione spenta lì non c'è.

- Pagare un ordine on-chain: chi compra manda i bitcoin a un indirizzo e l'ordine nasce alla prima conferma della rete. Appena la rete vede i sats la pagina del pagamento si chiude da sola, e in «Ordini» l'ordine dice «⏳ Visto in rete, aspetto la conferma» (etichetta «In arrivo»): non c'è altro da fare, si aspetta la conferma, circa dieci minuti. Se è arrivata solo una parte, la pagina resta aperta e dice quanti sats mancano. Appena il pagamento si vede in rete, chi vende riceve «Pagamento in arrivo»: l'oggetto è prenotato, ma non si spedisce finché non arriva l'avviso vero, alla conferma.
- La quota fissa a Barattolo: negli acquisti on-chain del mercatino il conto può avere la riga «Quota fissa a Barattolo (spese di rete)». La paga chi compra, si vede prima di pagare, va a Barattolo quando i sats vengono liberati e col rimborso torna indietro. Quanto vale oggi (o se non c'è) lo dicono i NUMERI DI OGGI.
- PayJoin negli acquisti on-chain del mercatino (dal 16 novembre 2026, se nei NUMERI DI OGGI è disponibile): il QR e «₿ Apri nel wallet» portano anche un link PayJoin («pj=»), e nel foglio di pagamento compare la riga «🔀 PayJoin». Se il tuo wallet lo sa fare (per esempio Sparrow, BlueWallet, Wasabi, Bull Bitcoin, Cake Wallet), mentre paghi Barattolo aggiunge alla transazione una sua piccola moneta: così chi guarda la blockchain non può più dire che tutti gli ingressi sono tuoi, né leggere a colpo d'occhio quale uscita è il tuo resto. Paghi la stessa cifra, e il deposito a tre chiavi riceve esattamente gli stessi sats. Il tuo wallet può mettere qualche sats in più di commissione di rete per l'ingresso aggiunto (lo decide lui, entro il limite che si dà). Se il wallet non lo sa fare, o se in quel momento Barattolo non ha una moneta pronta, si paga come sempre, senza differenze. La riga non c'è sempre: compare solo quando il PayJoin si può fare. Negli scambi P2P e nello Swap il PayJoin non c'è.
- Quando paghi on-chain (un ordine, il deposito di uno scambio P2P, lo Swap) l'app scrive i sats da mandare e, sotto, la riga «In BTC» con la stessa cifra in bitcoin (per esempio 0,00008128 BTC): molti wallet on-chain la chiedono così. Un tocco la copia, col punto (0.00008128), pronta da incollare nel wallet. Se invece inquadri il QR, la cifra il wallet la compila da solo; anche «₿ Apri nel wallet» apre il wallet con indirizzo e cifra già scritti.
- Profilo → «📥 Come ricevi»: due righe, «Quando ti pagano in Lightning, ricevi in» e «Quando ti pagano on-chain, ricevi in». Lì scegli se i sats ti arrivano in Lightning, on-chain, oppure «Ogni volta» (decidi tu ordine per ordine).

<!-- pezzo libro-026 | libro -->
## Libro · Bitcoin on-chain (2/2)

- Chi ha queste scelte trova anche, nel modulo dell'annuncio sotto il prezzo, «Come vuoi ricevere per questo oggetto?»: la scelta dell'annuncio vale più di quella del Profilo.
- Nel mercatino, quando chi vende riceve su una rete diversa da quella con cui paga chi compra, lo swap di SATS Routing lo paga chi vende: esce dai suoi sats quando li riceve, e chi lo fa vede il costo prima di confermare. Chi compra paga solo il prezzo del conto, senza righe in più.
- Profilo → «₿ On-chain»: «Dove ricevi i bitcoin» (l'unica cosa da compilare: il tuo indirizzo o il tuo wallet), poi la chiave e le 12 parole. Le 12 parole servono solo a FIRMARE i tuoi scambi on-chain: i sats non arrivano lì. Non darle mai a nessuno.
- Le 12 parole hanno bisogno di una copia fuori dal telefono: Barattolo la salva cifrata nel cloud di Telegram e/o sui relay Nostr, e senza una copia non si apre un ordine on-chain nuovo. Se manca la copia sui relay, nel Profilo c'è «Salva sui relay Nostr».
- Il wallet è uno solo, fra la Mini App in Telegram e il sito: se apri Barattolo da un altro posto, ti chiede di incollare le stesse 12 parole invece di crearne di nuove.
- Se non hai ancora scelto dove ricevere, la consegna dei bitcoin a te aspetta: l'app ti manda a Profilo → «₿ On-chain» per sceglierlo.
- La seconda firma: i sats on-chain escono con due firme su tre. Di solito il tuo telefono mette la sua da solo quando apri Barattolo; nell'ordine c'è anche il tasto «✍️ Metti la seconda firma», che mostra l'anello mentre firma e poi dice com'è andata, o perché non ha firmato (per esempio: la tua chiave sta solo sul telefono con cui hai pagato o venduto). Quando i sats sono partiti l'ordine lo dice, con il link «Vedi la transazione», e il tasto sparisce.

<!-- pezzo libro-027 | libro -->
## Libro · Lo Swap: spostare i tuoi sats fra Lightning e bitcoin on-chain (1/2)

La pagina «Swap» (la scheda in basso; fino al 12 novembre 2026 si chiamava «Cambio») sposta i TUOI sats fra Lightning e un tuo indirizzo bitcoin on-chain, nelle due direzioni, senza un ordine di mezzo. Se è accesa lo dicono i NUMERI DI OGGI.
- Lightning → bitcoin: scrivi la cifra (quella che mandi o quella che ricevi), incolli il tuo indirizzo bitcoin e paghi la fattura Lightning col tuo wallet; i bitcoin arrivano al tuo indirizzo. Il telefono li ritira quando il blocco del servizio ha la sua prima conferma sulla rete (di solito una decina di minuti): fino ad allora lo swap dice «aspetto la prima conferma», ed è normale.
- Bitcoin → Lightning: scrivi quanto vuoi ricevere (o quanto mandi), incolli una tua fattura Lightning di quella cifra esatta e mandi i bitcoin all'indirizzo che l'app ti mostra; quando arrivano, la tua fattura viene pagata. La cifra esatta nella frase «crea una richiesta di … sats esatti» si tocca e si copia, pronta da incollare nel wallet. Al posto della fattura puoi incollare il tuo Lightning address (nome@wallet): la fattura della cifra giusta la chiede Barattolo al tuo wallet quando premi «Conferma».
- Lo swap lo fa un servizio esterno (SATS Routing). Barattolo non prende commissioni: prima di confermare vedi quanto ricevi, con dentro la commissione del servizio e quella della rete.
- I sats non passano mai da Barattolo: partono dal tuo wallet e arrivano al tuo wallet.
- Lo swap si fa col proprio account: la scheda «Swap» in basso la vede anche chi non è ancora entrato (dal 16 novembre 2026, prima al suo posto c'era «Aste»), e toccandola si apre il foglio per entrare con Telegram o con Nostr; appena entrato, l'app porta alla pagina «Swap». Chi vede ancora «Aste» nella barra ha l'app aperta da prima dell'aggiornamento: basta chiuderla e riaprirla.
- Le aste non sono ancora partite. Dal 16 novembre 2026 ci si arriva dalla tessera «Aste» in «Esplora per categorie» (subito dopo «Scambio P2P») e dalla card quadrata «Aste» in «Da scoprire», nella home del mercatino: tutte e due portano alla pagina «Le aste stanno arrivando», dove col bottone «🔔 Avvisami» chiedi di essere avvisato quando partono. Il vecchio tasto «🔨 Aste ›» in cima alla home non c'è più.
- Limiti: da 25.000 sats a 0,01 BTC (1.000.000 sats) a swap, al massimo 5 swap al giorno. Da bitcoin verso Lightning il minimo è 50.000 sats RICEVUTI in Lightning (è il minimo del servizio): chi scrive la cifra in «Mandi» deve mandarne un po' di più, perché dai bitcoin mandati si tolgono la commissione del servizio e la rete. Se la cifra è sotto, l'app dice il minimo dal lato dove l'hai scritta (per esempio «Lo swap parte da 50.568 sats da mandare»). Se il servizio cambia i suoi limiti, vale il più stretto.

La privacy dello Swap, cioè chi vede cosa:

<!-- pezzo libro-028 | libro -->
## Libro · Lo Swap: spostare i tuoi sats fra Lightning e bitcoin on-chain (2/2)

- Barattolo si segna, legati al tuo account, la direzione, la cifra, il numero dello swap e l'indirizzo del servizio dove passano i bitcoin. Non si segna il tuo indirizzo bitcoin né la tua fattura Lightning. Però dal numero dello swap, sulla blockchain pubblica, si può seguire dove sono andati i bitcoin.
- SATS Routing vede quel che serve a fare lo swap: la fattura Lightning e il tuo indirizzo bitcoin. Non sa chi sei su Barattolo.
- La pagina parla con SATS Routing e con mempool.space (da lì legge la rete e trasmette la transazione) direttamente dal tuo telefono o computer, quindi loro vedono il tuo IP. Se entri dal sito .onion con Tor Browser, non lo vede nessuno dei tre.
- Sulla blockchain, da Lightning a bitcoin: al tuo indirizzo arriva una transazione con un solo ingresso, l'indirizzo del servizio, e una sola uscita, il tuo indirizzo; di solito ha l'aspetto di un pagamento qualunque. Da bitcoin a Lightning: si vede la transazione che parte dal tuo wallet verso l'indirizzo del servizio, come ogni pagamento on-chain.
- Payjoin: nello Swap non si usa. Da Lightning a bitcoin la transazione verso il tuo indirizzo la prepara il tuo telefono per lo swap, e non sa fare Payjoin: se incolli un link Payjoin («bitcoin:…?pj=…») l'app tiene solo l'indirizzo e i bitcoin arrivano lì con una transazione normale. Da bitcoin a Lightning l'indirizzo del servizio non accetta Payjoin, quindi anche il tuo wallet manda una transazione normale.
- Il consiglio di sempre: un indirizzo nuovo per ogni swap, in un wallet di cui solo tu hai le chiavi.

<!-- pezzo libro-029 | libro -->
## Libro · Nostr

Gli annunci di Barattolo vengono pubblicati anche su Nostr, una rete aperta: esistono sui relay anche indipendentemente da Barattolo. Se colleghi una tua chiave Nostr dal Profilo, i tuoi annunci escono firmati da te (la firma la fa il tuo browser) e restano tuoi. Gli avvisi possono arrivarti anche su Nostr, oltre che su Telegram. La chiave privata (nsec) non va mai data a nessuno, nemmeno a Barattolo.

Su Nostr risponde anche Tappo: si può scrivere un DM al profilo «Barattolo» (npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy) oppure rispondere sotto le sue note, e Tappo risponde come su Telegram. Ai bot e allo spam non risponde, e se qualcuno dello staff sta già seguendo quella conversazione lascia parlare lui. Per un problema con un ordine, in pubblico Tappo invita a scrivergli in privato.

<!-- pezzo libro-030 | libro -->
## Libro · I tuoi dati, in breve

Barattolo sa di te pochissimo: niente email, password o telefono. Da Telegram riceve il numero identificativo, il nome e lo username; da Nostr solo la chiave pubblica. L'indirizzo di spedizione è cifrato e si cancella quando confermi di aver ricevuto. Niente tracciamento, niente pubblicità, niente cookie di terzi. Tutto è spiegato nella pagina «I tuoi dati» (barattolo.store/privacy).

L'indirizzo IP: come ogni server, quello di Barattolo vede l'IP di chi si collega mentre gli risponde. Finisce solo nel registro tecnico della macchina: non nel database, non in un profilo, e non lo incrociamo con niente. Da Telegram l'IP non arriva.

Tor: Barattolo ha anche un sito .onion, lo stesso Barattolo dentro la rete Tor. Da lì il server non vede il tuo IP e non lo scrive da nessuna parte. L'indirizzo esatto è nella pagina «I tuoi dati», e quando apri barattolo.store con Tor Browser la barra degli indirizzi ti propone da sola la versione .onion («.onion disponibile»). Con un .onion conta ogni carattere: usa solo quello ufficiale.

Cancellare l'account: nel Profilo, nella parte della privacy accanto a «🔐 I tuoi dati», c'è «🗑 Cancella il mio account» (se la voce non c'è, oggi non è disponibile). Si può fare solo quando non hai niente in corso: se c'è un ordine non concluso, un pagamento in arrivo, sats ancora da ricevere, un'asta con puntate o uno scambio P2P aperto, il foglio te lo elenca e il bottone non compare finché non è tutto chiuso. Poi il foglio dice cosa sparisce e cosa resta; per confermare scrivi CANCELLA e tocchi «🗑 Cancella per sempre». Non si può annullare.
- Spariscono il profilo (nome, foto, Lightning address, chiave Nostr collegata), i preferiti, gli avvisi, gli indirizzi salvati e le chat; gli annunci in vetrina vengono ritirati, anche da Nostr e dai canali; le recensioni ricevute, i punti e l'eventuale posto da pioniere si perdono.
- Restano, senza il tuo nome, gli ordini conclusi e i pagamenti (per la contabilità e le contestazioni: chi ha fatto affari con te vede «Utente cancellato») e le recensioni che hai scritto, senza firma.
- Di te Barattolo tiene solo un'impronta del numero dell'account (non il numero, e mai il telefono) con la data, e le eventuali penalità degli scambi P2P: se rientri con lo stesso account parti da zero, e tornano solo quelle. La chat col bot la togli tu da Telegram, e i messaggi Nostr firmati da te restano tuoi.

Questo assistente: la tua domanda e le ultime battute arrivano ad Anthropic, l'azienda dell'intelligenza artificiale che risponde, ma mai il tuo nome, il tuo account o i tuoi ordini. Le conversazioni non vengono conservate: in chat privata l'assistente ricorda le domande e le risposte della giornata, per seguire il filo del discorso, e a mezzanotte spariscono.

<!-- pezzo libro-031 | libro -->
## Libro · Se Barattolo sparisse

Il mercatino gira su un server solo: se si fermasse, Barattolo si fermerebbe. Ma i sats del deposito stanno su un nodo Lightning separato, con la seed custodita offline; gli annunci restano su Nostr; lo storico è salvato ogni giorno con copie cifrate anche fuori dal server.

<!-- pezzo libro-032 | libro | sempre -->
## Libro · Sicurezza e truffe

- Nessuno di Barattolo ti chiederà mai la seed, le parole di recupero, la nsec, una chiave privata o una password. Chi le chiede è un truffatore. Se le hai date a qualcuno, considerale esposte e sposta subito i fondi su un wallet nuovo.
- Barattolo non ti scrive per primo chiedendo soldi.
- Gli account ufficiali di Barattolo su Telegram sono SOLO questi: il bot https://t.me/ilbarattolobot, il canale https://t.me/barattolostore (con la sua chat privata e il gruppo dei commenti), Tappo https://t.me/TappoBarattoloBot (dal 16 novembre 2026 ci si arriva anche col bottone «💬 Chiedi a Tappo» nel bot di Barattolo, nel benvenuto e quando gli si scrive una frase, e dalla voce «🤖 Chiedi a Tappo» nel Profilo della Mini App, sezione Supporto), e le due persone dello staff, Andrea https://t.me/aandreaiita e Alan https://t.me/AlanBimbati. Quando qualcuno chiede se un account è vero o come trovare lo staff, metti SEMPRE questi link, nascosti dietro il nome (per esempio «Andrea» che porta a https://t.me/aandreaiita), così chi li tocca arriva all'account giusto senza poter sbagliare. Chiunque altro dica di essere dello staff, dell'assistenza o di Barattolo NON lo è, anche se il nome sembra uguale: i truffatori copiano nome e foto e cambiano una lettera (per esempio una «I» maiuscola al posto della «l», come @aIanbarattoIo, che NON è Alan). Prima di fidarti, guarda il NOME UTENTE, quello con la @ (lo trovi aprendo il profilo, alla voce «Nome utente»), e controllalo lettera per lettera: il nome visualizzato e la bio li può scrivere chiunque, quindi «Alan» o «Barattolo» scritto lì non prova niente.
- Lo staff non ti chiede mai soldi in privato, né per «scambi di buoni», «sblocchi», «verifiche» o rimborsi. Se qualcuno lo fa, non mandare niente, bloccalo e segnalalo da Telegram, e avvisa lo staff.
- Paga sempre dentro Barattolo: un pagamento fuori dal deposito di garanzia non è protetto.
- Nel P2P, libera i sats solo quando gli euro sono arrivati davvero sul tuo conto, non prima e non sulla fiducia di una ricevuta.

<!-- pezzo libro-033 | libro | sempre -->
## Libro · Parlare con una persona

Se nei NUMERI DI OGGI l'assistenza in app risulta disponibile, c'è anche una chat con lo staff dentro Barattolo: Profilo → Supporto → «💬 Assistenza» (fino al 16 novembre 2026 stava in Profilo → Privacy). Ognuno ha la sua conversazione; lo staff risponde col bollino 🛡️ e ti arriva un avviso quando c'è una risposta.

Se l'assistente non basta, sotto ogni sua risposta c'è il bottone «🙋 Parla con una persona»: ti dà la chat privata di Barattolo (t.me/barattolostore?direct), dove risponde una persona dello staff. Se quel link ti apre il canale invece della chat: le chat private dei canali ci sono solo nelle versioni recenti di Telegram, quindi aggiorna l'app e riprova dal telefono; oppure apri il canale @barattolostore e cerca in fondo alla pagina il tasto per mandare un messaggio. Se ancora non va, scrivilo a Tappo (@TappoBarattoloBot): passa lui il messaggio allo staff. Per un problema con un ordine o uno scambio preciso, scrivi lì il numero dell'ordine e cosa è successo. Per una lite su un ordine coi sats in garanzia, la strada giusta resta la disputa, dalla pagina dell'ordine o dello scambio.

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
## Schermata «Lo scambio P2P (info)» · Lo scambio P2P (1/8)

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
## Schermata «Lo scambio P2P (info)» · Il premio e lo sconto (2/8)

## Il premio e lo sconto
Chi pubblica può chiedere un po' più o un po' meno del mercato, fino a ±%. Sopra il mercato si chiama premio e conviene a chi vende; sotto si chiama sconto e conviene a chi compra. Nel conto dello scambio quella riga c'è sempre, col suo nome e la sua percentuale.
Il premio si applica prima della commissione: prima si calcola il controvalore col premio, poi la commissione morde su quello. È l'ordine in cui il conto mostra le righe, e non è impaginazione.
## La commissione
## Come si pagano gli euro
I metodi sono un elenco chiuso: . Chi pubblica sceglie quali accetta, chi prende ne sceglie uno.
Gli euro non passano da Barattolo. Viaggiano fra te e l'altra persona sul circuito che avete scelto, come se vi foste messi d'accordo per strada. Il recapito che serve — l'IBAN, il RevTag, il numero — ve lo scambiate qui dentro e cifrato: lo legge solo chi deve pagare.
Per questo la garanzia protegge i sats e non gli euro: se dici di aver inviato gli euro e non l'hai fatto, chi vende semplicemente non libera. E se li hai inviati e non liberano, c'è la disputa.

<!-- pezzo schermata-006 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (3/8)

## Barattozon: il PayCode al tabacchino, passo per passo
È il metodo per chi non vuole passare da una banca o da un'app: chi vende sats fa un ordine Amazon da pagare in contanti nel punto vendita e chi compra lo paga alla cassa del tabacchino col PayCode. Il tabacchino incassa i contanti, l'ordine Amazon risulta pagato, e i sats si liberano. Nel libro il metodo si chiama ancora «Contanti al tabacchino»: è la parola che leggono anche le altre app.
Paghi in contanti alla cassa del tabacchino un ordine Amazon di chi vende: ricevi cifrati codice, importo e scadenza appena l'ordine è tuo, e paghi solo quando la pagina dice «Sats in garanzia». Non vedi nome, indirizzo né cosa ha comprato. Per pagare non serve alcun documento. Tieni lo scontrino in caso di disputa.
Chi vende fa l'ordine su Amazon scegliendo «paga in contanti nel punto vendita». Amazon gli manda una mail con tre cose: il PayCode (nove cifre, come 479-868-518), l'importo esatto coi centesimi e una scadenza, settantadue ore dal checkout. Vale fino a novecentonovantanove euro per ordine, senza commissione; per Barattozon un PayCode vale almeno venticinque euro. Non vale per Amazon Warehouse, contenuti digitali, oro, abbonamenti a Prime, buoni regalo e acquisti 1-Click: se la mail di Amazon non offre il pagamento in contanti, l'ordine non è pagabile con Barattozon.
Chi vende pubblica qui, con Barattozon come unico metodo, e il foglio lo porta per mano in quattro passi: il PayCode, l'importo, la scadenza (con un selettore di data e ora, fra un'ora e settantadue ore) e il premio, con lo stesso cursore degli altri ordini, da meno venti a più venti per cento, a numeri interi. Un PayCode vale almeno 25 €. Prima dei quattro passi si sceglie il tipo di prezzo, come per ogni ordine: a prezzo di mercato i sats si calcolano quando qualcuno prende l'ordine, col premio, sull'importo arrotondato per eccesso all'euro intero (25,47 € diventano 26: chi paga riceve sempre almeno il valore di quel che paga, e la differenza la mette chi pubblica); a prezzo fisso i sats nascono adesso, sui centesimi esatti e al cambio di oggi, e la convenienza per chi prende si muove col bitcoin. Il segno decide il verso: col premio positivo chi paga al tabacchino riceve meno sats del cambio pieno e la differenza resta a chi vende; col premio negativo ne riceve di più, e quella differenza la paga chi vende per la comodità. A zero passa il cambio pieno. Premio più basso = più conveniente per chi paga = più probabile che qualcuno lo prenda in tempo. Prima di pubblicare c'è il riepilogo, che a prezzo di mercato dice anche l'arrotondamento. Il cambio si fissa lì a prezzo fisso, alla presa a mercato; l'ordine resta nel libro fino a due ore prima della scadenza del PayCode (mai oltre settantadue ore): poi esce da solo.

<!-- pezzo schermata-007 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (4/8)

Nel libro la card dice quanto conviene adesso, come negli altri ordini: «più conveniente» o «meno conveniente» per chi guarda, e dal dieci per cento il cartellino dell'affare. I sats sono fissi dalla pubblicazione e il bitcoin no, quindi la convenienza vera si muove col prezzo, e il numero la segue, senza limiti. Nel dettaglio trovi i due numeri uno accanto all'altro: il premio scelto da chi vende e quello al prezzo di adesso. Dopo la presa il conto si ferma al prezzo di quel momento: i sats che ricevi sono quelli scritti, al satoshi.
Chi compra prende l'ordine, indica dove ricevere i sats, e chi vende li blocca in garanzia. Il PayCode, l'importo e la scadenza gli arrivano qui dentro e cifrati solo quando la pagina dice «Sats in garanzia», in un riquadro col tempo che resta: prima il codice non c'è, e al tabacchino non si va. Nel libro pubblico c'è solo l'importo: il PayCode non lo vede nessun altro, nemmeno Barattolo.
Chi compra va a pagare in un punto abilitato al PayCode: non tutte le tabaccherie lo sono. Si cercano sulla 
mappa di Amazon, che chiede un account Amazon (uno qualsiasi); chi non ce l'ha cerca per CAP su 
PuntoLis spuntando «Amazon Paga in Contanti», o scrive il suo CAP a chi vende, che lo cerca per lui. Alla cassa mostra il codice e dice «devo pagare un ordine Amazon in contanti con un PayCode»: non una ricarica, non un buono regalo, che non pagano l'ordine. Paga l'importo esatto, senza commissione, e controlla lo scontrino: pagamento dell'ordine, non «codice acquisto» o buono. Poi tiene lo scontrino, la sua prova, e torna qui a toccare «Ho pagato al tabacchino».
Chi vende controlla su Amazon che l'ordine risulti saldato, e sceglie fra due bottoni: «Risulta pagato: libera i sats» oppure «Non risulta pagato: apri una disputa». Ha ventiquattro ore a vista, e Barattolo glielo ricorda su Telegram dopo un'ora, sei ore e venti ore. Non esiste una conferma automatica: Amazon non parla con Barattolo, e i sats non si liberano da soli. Se chi vende non fa nulla, i sats restano in garanzia e chi ha pagato può aprire lui la disputa: decide un moderatore, e lo scontrino è quel che guarda.
Se scade. Ci sono due scadenze, e vanno tenute distinte. Quella del libro cade almeno due ore prima di quella del PayCode: se nessuno ha preso l'ordine, esce dalla vetrina e a chi vende arriva un avviso — il PayCode vale ancora per poche ore, ma nessuno può più prenderlo; quando scade anche lui, l'ordine Amazon va rifatto e ripubblicato con un PayCode nuovo. Quella del PayCode conta quando i sats sono già in garanzia: la pagina dello scambio lo dice, ti avvisa sei ore prima e un'ora prima (anche su Telegram o Nostr, secondo le tue impostazioni) e mette in evidenza l'annullo d'accordo, con cui i sats tornano a chi li ha bloccati. Nessuno annulla da solo: se hai pagato in tempo, lo scontrino lo dimostra e chi vende libera.

<!-- pezzo schermata-008 | schermata -->
## Schermata «Lo scambio P2P (info)» · Barattozon: il PayCode al tabacchino, passo per passo (5/8)

Se ti danno un buono regalo. Alla cassa possono emettere per errore un buono regalo Amazon o una ricarica: l'ordine di chi vende non risulta pagato. Non toccare «Ho pagato al tabacchino»: scrivi a chi vende e decidete insieme.
Prendi un ordine Barattozon solo se fai in tempo ad andare al tabacchino: quando mancano meno di sei ore, il dettaglio te lo ricorda prima di prenderlo.
## Contanti di persona
Il metodo «Contanti» è l'incontro a mano: chi compra sats porta le banconote, chi vende le conta e libera i sats lì, davanti a lui. Una banconota non lascia ricevuta, quindi le regole sono tre e valgono dall'inizio.
Il rilascio sul posto. A chi compra: Consegna i contanti solo quando chi vende preme «Libera i sats» davanti a te, e controlla che lo scambio risulti concluso prima di andare via. A chi vende: Conta i contanti davanti a chi ti paga, poi premi «Libera i sats» lì, davanti a lui: chi compra deve vedere lo scambio concluso prima di andare via. Mai prima di vedersi, mai dopo essersi salutati.
L'incontro. Vedetevi in un posto pubblico e di giorno — un bar, un incontro bitcoin —, contate le banconote insieme, e mai grosse cifre da soli.
🕒 L'appuntamento. Chi vende indica dove e quando vedervi: il giorno e l'ora con pochi tocchi, e il luogo come indirizzo vero — mentre lo scrive gli proponiamo indirizzi esistenti, o usa la sua posizione. Chi compra lo trova in cima alla pagina dello scambio, con «🧭 Apri nel navigatore». Se l'appuntamento cambia, l'altra persona riceve l'avviso.
📍 «Sono qui», la prova d'incontro. Quando arrivate, ognuno tocca «Sono qui» dal suo telefono, senza aspettare l'altro: si registrano l'ora esatta e, se il telefono la dà, la posizione, firmate con la chiave usa-e-getta dello scambio. È facoltativo, per la privacy, ma aiuta a risolvere le dispute. L'altra persona vede l'ora in cui l'hai segnato, mai la tua posizione; un moderatore, solo in caso di disputa, vede se eravate lì insieme, all'ora e vicino al luogo dell'appuntamento. Il GPS si può falsificare: la posizione è una conferma, non una prova assoluta.
In disputa, sul contanti. Se chi vende dice di non aver ricevuto i contanti e non c'è la prova d'incontro, in disputa si dà ragione a chi vende. Ma se chi compra ha segnato la presenza all'ora e vicino al luogo dell'appuntamento e chi vende no, la disputa non va in automatico a chi vende: decide il moderatore. Lo scriviamo adesso, prima dello scambio, e non il giorno della disputa.
## I tempi
Se il tempo scade prima che i sats siano bloccati, la richiesta di pagamento si annulla e nessuno perde niente. Se a mancare è stato chi ha preso l'ordine, l'ordine torna nel libro per qualcun altro; se è stato chi l'ha pubblicato, si chiude.
Coi sats in garanzia avete circa quattro giorni. Se chi compra non ha ancora detto di aver pagato, allo scadere i sats tornano da soli a chi vende; se l'ha detto, si apre una disputa.

<!-- pezzo schermata-009 | schermata -->
## Schermata «Lo scambio P2P (info)» · La chat dello scambio (6/8)

## La chat dello scambio
Da quando l'ordine è preso a quando lo scambio finisce, nella sua pagina c'è una chat fra voi due: serve a mettervi d'accordo, a dirvi «fatto», a chiedere «ti è arrivato?». Oltre al testo puoi mandare foto (jpg, png, webp) e PDF fino a 20 MB, col 📎: partono cifrati dal tuo telefono, le foto senza la posizione e i PDF senza i dati nascosti (autore, programma, date), e se ne vanno con la chat. Il recapito per gli euro resta nel suo riquadro, così non si perde fra i messaggi.
È cifrata fra voi due. Ogni telefono fa nascere a caso una chiave apposta per quello scambio; Barattolo trasporta i messaggi già chiusi. A fine scambio la cancella: i telefoni buttano chiave e messaggi, il nostro server cancella le buste, e nei backup non ci sono mai entrate.
Barattolo non ti scrive mai qui. Chi nella chat si presenta come «assistenza» è l'altra persona.
Non uscire dallo scambio per pagare. I link nella chat non si aprono, e sotto un messaggio che ne porta uno, o che ti chiede di spostarti altrove, compare una riga rossa.
Non mandare codici o chiavi. Per completare uno scambio non servono a nessuno.
Se cambi telefono o browser a metà scambio la chat ti segue, con tutti i messaggi: appena nasce, il telefono lascia sul nostro server una copia sigillata della chiave, chiusa con la chiave di quello scambio. La apre solo chi ha il tuo profilo di scambio, il server la riconsegna solo a te, e a fine scambio sparisce con il resto.
Chi la può aprire. La chat è cifrata fra voi due e Barattolo la trasporta. Se il tuo account è nato su Nostr, Barattolo non la può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo ritrovi scambio e chat su ogni dispositivo, e per questo Barattolo durante lo scambio potrebbe tecnicamente aprirla. Non lo fa. A fine scambio la chat si cancella, per tutti. Il moderatore la legge solo se una di voi due apre una disputa.
In una disputa il moderatore legge la chat solo se una di voi due la apre: è il telefono di chi apre la disputa a dargli la chiave, e glielo diciamo prima del tocco. Legge e non scrive al posto vostro; a disputa chiusa si cancella tutto, come a fine scambio.

<!-- pezzo schermata-010 | schermata -->
## Schermata «Lo scambio P2P (info)» · Gli avvisi: cosa ti diciamo, e quando (7/8)

## Gli avvisi: cosa ti diciamo, e quando
Ad app aperta la pagina dello scambio si muove da sola: la richiesta da pagare, il foglio dove indicare i sats e il passo dopo compaiono appena arrivano — via Tor ci vogliono di solito dieci-venti secondi. Ad app chiusa ti avvisiamo su Telegram o su Nostr, secondo le tue impostazioni.
Un avviso per ogni passo che ti riguarda, e dice quale: il tuo ordine è stato preso, c'è la garanzia da pagare, i sats sono in garanzia e tocca a te indicare dove riceverli, l'altra persona ha indicato dove ricevere i sats, dice di aver inviato gli euro, chiede di annullare, ha aperto una disputa, il pagamento dei sats non è passato. E alla fine: concluso (con quanto hai ricevuto o pagato, commissione compresa), annullato, tornato nel libro o scaduto.
«Ti ha indicato dove inviare gli euro: tocca a te», quando chi vende ti lascia il recapito. Il recapito non è nell'avviso: lo leggi qui dentro, cifrato — e prima di inviare gli euro guarda che la pagina dica «Sats in garanzia». Col contanti di persona è «dove e quando vedervi», e se l'appuntamento cambia te lo diciamo.
«Hai un nuovo messaggio nello scambio», quando l'altra persona ti scrive nella chat e non la stai guardando. Il testo non è nell'avviso: lo leggi qui dentro. Uno per ogni volta che c'è da leggere, non uno per messaggio.
Niente, per un gesto che hai fatto tu: l'hai già davanti. L'avviso va a chi deve fare il passo dopo, o deve saperlo.
Da dove vengono. A raccontarci i passi è il coordinatore — che facciamo girare noi — nel momento in cui succedono. Ci dice quale ordine, quale passo, e fra quali due chiavi usa-e-getta; degli importi ci dice solo quelli della chiusura. Non ci manda fatture, recapiti né messaggi: quelli restano cifrati fra voi due, e non li vediamo. Se un suo avviso si perde per strada, i passi pubblici — preso, concluso, annullato, scaduto — li leggiamo dal libro, e te li diciamo un minuto dopo.
Gli avvisi si spengono tutti dal cassetto «🔔 Avvisi» del profilo. A scambio aperto conviene tenerli accesi: alcuni passi hanno i minuti contati, e l'avviso dice quanti.

<!-- pezzo schermata-011 | schermata -->
## Schermata «Lo scambio P2P (info)» · Se qualcosa va storto (8/8)

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

<!-- pezzo schermata-012 | schermata -->
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

<!-- pezzo schermata-013 | schermata -->
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

<!-- pezzo schermata-014 | schermata -->
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

<!-- pezzo schermata-015 | schermata -->
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

<!-- pezzo schermata-016 | schermata -->
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

<!-- pezzo schermata-017 | schermata -->
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

<!-- pezzo schermata-018 | schermata -->
## Schermata «I tuoi dati» · Cosa nasce mentre usi il mercatino (2/17)

## Cosa nasce mentre usi il mercatino
I tuoi annunci: sono pubblici per definizione — è il loro mestiere.
I tuoi ordini: cosa hai comprato o venduto, quanto, quando, e come è andata.
Il tuo Lightning address, se lo imposti per incassare da solo: è un nome@dominio, come una mail, e ce l'abbiamo in chiaro — è lì che ti mandiamo i sats quando un affare si chiude, quindi dobbiamo poterlo leggere. Non esce da nessuna parte: non lo vede chi compra, non lo vedono i moderatori.
La fattura che incolli per incassare, se l'address non lo usi: si incolla solo al momento dell'incasso — nel Profilo non se ne salva nessuna, perché una fattura scade e vale per un pagamento solo — e resta scritta in quell'ordine, come ricevuta di dove sono andati i sats.
La tua reputazione: voti ricevuti, distintivi, il livello, e gli XP, che contano il commercio — quanto hai comprato e venduto, più una piccola parte di quello delle persone che hai invitato, da quando quelle che commerciano sono almeno tre.
Gli inviti: il tuo codice e, se sei arrivato con un invito, chi ti ha invitato. A chi ti ha invitato non diciamo mai chi sei: vede quante persone ha portato, e i punti che gli hanno fruttato tutte insieme gli arrivano — nel cassetto, nel suo totale, nel livello e in classifica — solo quando quelle che commerciano sono almeno tre: prima restano da parte, e lui vede soltanto che ci sono, senza la cifra. Un limite onesto: se ha invitato soltanto te, la riga «punti in attesa» gli dice che hai cominciato a commerciare — non quanto.
La tua posizione in classifica, se ci entri: lì di te si vedono nome, foto, titolo, media dei voti, da quante persone, quanti affari e il punteggio. Il punteggio mette insieme la media e il commercio, quindi da lì si può ricavare quanto hai commerciato — è una scelta presa sapendolo, perché senza quel numero l'ordine della lista non si legge. Gli XP in chiaro invece non escono mai, e nemmeno il tuo identificativo. Se non vuoi comparire, nel Profilo («Livello e titolo») c'è Non mostrarmi in classifica: il tuo livello resta sul profilo, perché a chi scambia con te serve per fidarsi. E se la tua reputazione la pubblichiamo su Nostr (vedi sotto), smettiamo e chiediamo ai relay di ritirarla.
Il tuo barattolo, cioè gli annunci che hai messo da parte. Di questi si vede quanti l'hanno salvato, mai chi: nemmeno chi vende sa che sei stato tu — a meno che tu non condivida il barattolo col suo link, che è un gesto tuo: la voce qui sotto dice cosa comporta.
I tuoi avvisi di ricerca, se ne crei: cosa cerchi, dove, entro che prezzo.
Gli avvisi del mercatino, se li accendi (sono spenti di serie): le categorie e il prezzo massimo che hai scelto per «🛒 Avvisami dei nuovi annunci», e i venditori che segui — che non lo sanno: nessuno vede chi lo segue, né quanti. E per ogni annuncio di cui ti abbiamo avvisato, il suo numero accanto al tuo, per non avvisarti due volte: se ne va da solo dopo un mese.

<!-- pezzo schermata-019 | schermata -->
## Schermata «I tuoi dati» · Cosa nasce mentre usi il mercatino (3/17)

Il tuo carrello, se ne componi uno: quali oggetti e quanti, di un venditore solo, così lo ritrovi quando rientri. Dentro non c'è l'indirizzo né la consegna — quelli nascono nella cassa — e chi vende non lo vede.
## Il barattolo condiviso
Il barattolo resta privato finché non decidi tu: dal Profilo puoi creare un link che mostra la lista delle cose che hai messo da parte. È come pubblicare una lista di desideri — chi apre il link vede cosa ti interessa comprare, anche un venditore con cui stai trattando se il link gli arriva. Va fatto sapendolo, e te lo diciamo lì, prima del tocco che crea il link.
La pagina del link non fa il tuo nome: niente nome, niente foto, niente negozio. Chi lo riceve da te sa di chi è, ma un link girato a terzi non lega la lista a una persona. E mostra una fotografia, non il barattolo vivo: quello che salvi dopo non si vede finché non la aggiorni tu, con un gesto.
La revoca è un tocco e il link muore subito: la pagina si rilegge dai nostri dati a ogni apertura, non c'è una copia che sopravviva. Tre limiti onesti, però: chi aveva la pagina già aperta la vede finché non ricarica; l'anteprima del link che Telegram o WhatsApp tengono in cache può durare qualche giorno, ma mostra solo il titolo generico — la lista, in quell'anteprima, non c'è mai entrata; e uno screenshot resta, come per ogni cosa pubblicata. Se un domani ricondividi, il link sarà nuovo: quello vecchio resta morto.

<!-- pezzo schermata-020 | schermata -->
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

<!-- pezzo schermata-021 | schermata -->
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
I punti di ritiro che salvi: finché non li togli. Li trovi nel Profilo, in «📍 Punti di ritiro», con una ✕ accanto a ognuno.
Il tuo Lightning address, se l'hai impostato: finché non lo togli. Sta nel Profilo, in «Incassi e pagamenti», col suo bottone.
La nota che scrivi a chi vende: resta nell'ordine, come il resto di quello che vi siete detti. Finché il pacco non parte puoi cambiarla o toglierla dall'ordine stesso.
Il codice sconto che usi: il suo nome resta scritto nell'ordine — è la ricevuta dello sconto che hai avuto, per te e per chi vende.
Tutto il resto non ha una scadenza, e non è una dimenticanza: annunci, ordini, voti e reputazione sono la memoria degli affari fatti, e servono a te quanto a chi commercia con te — una recensione che sparisce dopo un anno non è una recensione. Un ordine concluso puoi nasconderlo dalla tua lista quando non vuoi più vederlo: sparisce dalla vista, la riga resta.

<!-- pezzo schermata-022 | schermata -->
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

<!-- pezzo schermata-023 | schermata -->
## Schermata «I tuoi dati» · Cosa esce da qui (7/17)

## Cosa esce da qui
✈️Telegram. Gli avvisi te li mandiamo col bot, quindi Telegram vede che ti abbiamo scritto e cosa c'è nel messaggio. Per questo gli avvisi su indirizzo, busta e codici sono scritti vuoti apposta: dicono «apri l'ordine», mai il contenuto. E i bottoni per scrivere alla controparte ti portano fuori, in una chat di Telegram: quella conversazione è vostra e di Telegram, non nostra — non la leggiamo, non ce l'abbiamo, e in una disputa non possiamo usarla.
🟣Nostr. Gli annunci vanno sui relay, che in gran parte sono di altri — e uno è nostro, relay.barattolo.store: lì la copia degli annunci ce l'abbiamo anche noi, ma non è un privilegio, perché quella copia ce l'ha chiunque apra uno qualsiasi degli altri relay. Da noi leggere è aperto a tutti; scrivere no, e possono farlo solo Barattolo e chi ci ha dimostrato la propria chiave Nostr. Ritirare un annuncio manda anche la richiesta di cancellarlo, e i relay che la rispettano lo tolgono — ma nessuno può garantire che l'abbiano fatto tutti, il nostro compreso: nemmeno sul relay di casa possiamo promettere quello che sugli altri non possiamo. Se hai verificato la tua chiave, sui relay va anche la tua reputazione — livello, XP e affari conclusi — firmata da noi (è il kind 30382): con «Non mostrarmi in classifica» smettiamo di pubblicarla e chiediamo di ritirarla, con lo stesso limite degli annunci. Quello che finisce su Nostr non torna indietro. È il prezzo della piazza aperta, ed è la stessa proprietà che rende il tuo annuncio tuo anche il giorno che Barattolo non ci fosse più.
⚡Il nodo dei pagamenti. Quando paghi, la fattura porta il numero dell'annuncio e il suo titolo — mai chi sei.
🤖L'intelligenza artificiale che controlla gli annunci: le arriva il testo dell'annuncio — titolo e descrizione — e mai chi l'ha scritto. Quello che scrivi nella barra di ricerca non le arriva mai: la ricerca è un indice di casa, e la tua domanda non esce da qui.
💬L'assistente del bot, quando è acceso: se scrivi una domanda al bot, la domanda e le ultime battute della conversazione arrivano ad Anthropic, l'azienda dell'intelligenza artificiale che ti risponde, insieme alle nostre guide — mai il tuo nome, il tuo account né i tuoi ordini. Anthropic non usa questi testi per addestrare i suoi modelli. Noi le conversazioni non le salviamo: il server ricorda le ultime battute per mezz'ora, solo in memoria, poi spariscono. Se tocchi «🙋 Parla con una persona», la tua ultima domanda arriva ai moderatori insieme al tuo nome Telegram.
💱Il cambio euro/bitcoin, che chiediamo noi una volta al minuto e non il tuo browser: così nessun terzo sa che stai guardando un prezzo.

<!-- pezzo schermata-024 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (8/17)

## Il profilo di scambio P2P
Per scambiare sats in euro con altre persone lo scambio passa da un coordinatore (il programma si chiama Mostro, e a farlo girare è Barattolo, sul nostro nodo), e per riconoscerti lì serve un profilo di scambio. Nasce e funziona da solo: dentro l'app non c'è niente da creare né da gestire. Qui sotto diciamo per intero da dove viene e chi lo può ricavare, perché dipende da dove è nato il tuo account, non da come entri.
Se il tuo account è nato con Telegram (anche se poi entri con Nostr), il profilo lo ricaviamo noi dal tuo account: così è lo stesso dal bot, dal sito e dall'app, e torna da solo su un telefono nuovo senza che tu debba salvare niente. Il prezzo lo diciamo per intero: quel profilo il server di Barattolo lo sa ricavare, quindi in linea di principio potrebbe firmare uno scambio al posto tuo. Non lo facciamo, e non c'è niente nel programma che lo faccia — ma potremmo, e questo è l'unico posto di Barattolo in cui possiamo dirlo di un tuo segreto. Per ricavarlo servono due cose insieme, una nella configurazione del server e una nel database: chi si portasse via una sola delle due non ricaverebbe nulla.
Se il tuo account è nato su Nostr, il profilo non lo può ricavare nessuno tranne te, noi compresi, ed è lo stesso ovunque perché ce l'hai tu. Vale anche se in passato hai reso il tuo profilo di scambio una chiave Nostr che è tua, dovunque sia nato l'account: resta così, e questa strada resta nel patto anche se oggi non ha più un gesto dentro l'app.
Per fartelo ritrovare su ogni dispositivo, il tuo browser ne mette una copia cifrata sui relay Nostr — i tuoi, quelli pubblici che usa Barattolo e il nostro: la apre solo la tua chiave, noi no, e sul nostro server non ce n'è nessuna. Il prezzo lo diciamo per intero: chi legge quei relay vede che la copia esiste ed è tua, non cosa contiene. «Dimentica il profilo» la toglie anche da lì: la sostituisce con una vuota e chiede ai relay di cancellarla. Non possiamo garantire che tutti obbediscano: su un relay che non lo fa può restare la copia vecchia, sempre cifrata, e resta visibile che una copia c'è stata.
Negli altri casi — un profilo nato nel browser prima che arrivasse quello del conto — il profilo vive sul dispositivo e non lo può ricavare nessuno. Dentro Telegram ne salviamo una copia nel cloud del tuo account Telegram, così sopravvive alla cache svuotata e ti segue fra telefono e computer: chi ha il tuo account Telegram ce l'ha anche lui — è già così per tutto Barattolo — e Telegram potrebbe leggerlo, che è il prezzo. Il codice segreto serve a portare il profilo fuori da Barattolo, in un altro programma che parla con lo stesso coordinatore.

<!-- pezzo schermata-025 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (9/17)

In tutti e tre i casi il server conosce la parte pubblica del profilo e le chiavi usa-e-getta di ogni scambio, per poterti avvisare quando c'è una novità, e da settembre 2026 anche a che numero di scambio sei arrivato: serve a non riusare due volte la stessa chiave usa-e-getta quando apri Barattolo da un dispositivo nuovo, ed è un dato che dai conti che teneva già si sarebbe comunque ricavato. Dal foglio qui sotto il codice segreto lo vedi e lo copi, e il profilo lo dimentichi; dimenticandolo si cancella anche la parte pubblica che il server teneva.
Dal 16 settembre 2026 il server annota anche quali ordini pubblichi e quali prendi, per avvisarti con i numeri quando lo scambio si muove (preso, concluso, annullato, tornato in vetrina): sono i passaggi pubblici del libro, e la cifratura dei messaggi non si tocca. Dal 12 ottobre 2026 chi scambia da Barattolo è riconosciuto dall'altra persona con qualunque modo di entrare — Telegram, nsec, bunker o estensione: la presa si annota, chi ha pubblicato vede il suo profilo e le due parti possono recensirsi. Il collegamento fra la chiave dello scambio e l'account lo sa solo il server, e lo mostra solo all'altra parte di quello scambio: mai in pubblico, mai sui relay. Non c'è un interruttore: chi vuole restare anonimo entra con una chiave Nostr nuova, che per l'altra persona è un'altra persona. Gli scambi di prima del 12 ottobre 2026 restano come erano (dal 17 settembre al 12 ottobre chi entrava da Nostr era anonimo di serie, e quella promessa resta valida sul passato). Riconosciuto dall'altra persona, e dal server: come per tutti, il coordinatore ci dice fra quali due account è lo scambio (è la cronaca dei quaranta giorni, più sotto), e dal 10 ottobre 2026 l'esito dello scambio si scrive sul suo account — completato, o non completato se ha preso e non ha fatto il primo passo — col numero dell'ordine, per circa quattrocento giorni. Gli avvisi si spengono tutti dal cassetto «🔔 Avvisi» del profilo.
Dal 9 ottobre 2026, se accendi «🔔 Avvisami dei nuovi ordini P2P» (spento di serie), il server conserva le tue preferenze — quali tipi di ordine e da quale convenienza in su — e, per ogni ordine di cui ti ha avvisato, il suo numero accanto al tuo: serve a non avvisarti due volte dello stesso, e se ne va da solo dopo la finestra del libro. Chi ha pubblicato quegli ordini non lo sa. «Dimentica il profilo» porta via anche quelle righe.

<!-- pezzo schermata-026 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (10/17)

Dal 18 settembre 2026 gli avvisi sugli scambi nascono dal coordinatore, che facciamo girare noi: a ogni passo di uno scambio dice al server di Barattolo quale ordine, quale passo, fra quali due chiavi usa-e-getta, e chi dei due ha fatto il gesto — e da lì il server avvisa l'altra persona, con una frase che dice cosa è successo. Il prezzo lo diciamo per intero: il server ora sa a che punto è ogni scambio, e per chi usa Barattolo sa fra quali due account (le chiavi usa-e-getta le conosceva già). Non riceve gli importi, tranne i tre della chiusura — quanto valeva lo scambio, quanto è andato a chi compra e quanto ha bloccato chi vende, che servono alla frase «scambio concluso» — e non riceve mai fatture, recapiti né messaggi: quelli restano cifrati fra voi due. Questa cronaca si cancella da sola dopo quaranta giorni, e subito se dimentichi il profilo. Con questo è sparito l'avviso generico «Novità in un tuo scambio», e con lui due cose che esistevano solo per farlo funzionare: il server non guarda più sui relay le buste cifrate che il coordinatore ti manda, e il tuo telefono non gli dice più «sto facendo un gesto». Una cosa il telefono continua a dirla, solo se vendi: «ho indicato all'altra persona dove ricevere gli euro», col numero dell'ordine — serve ad avvisarla che tocca a lei, perché quel passo il coordinatore non lo vede. E se l'ordine ha più metodi, il telefono di chi lo prende ci dice quale ha scelto (il nome, per esempio «SEPA» o «ETH (Ethereum)»): serve ad avvisare chi l'ha pubblicato e a scrivere gli avvisi con la moneta giusta, e se ne va con la cronaca. Il recapito non passa da noi: l'IBAN, il RevTag o il numero viaggiano cifrati fra i vostri due telefoni, e nell'avviso non ci sono. I recapiti sono cifrati fra voi due. Se il tuo account è nato su Nostr, Barattolo non li può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo Barattolo potrebbe tecnicamente aprirli. Non lo fa. E dallo stesso giorno il recapito che hai ricordato non parte più da solo: lo trovi già scritto, e parte quando lo invii tu.
Dal 10 ottobre 2026, di ogni scambio chiuso — concluso o annullato — e di ogni ordine scaduto o ritirato senza essere preso, teniamo anche oltre i quaranta giorni i conti: il numero dell'ordine (che è pubblico), le date, come è finito, gli importi della chiusura, il metodo di pagamento e la cifra in euro del libro. Senza le persone: in quel registro non c'è il tuo account né una tua chiave, e chi ha scambiato con chi continua a cancellarsi come detto qui sopra. Il legame fra un ordine e te resta quello che il server annota già — quali ordini pubblichi e quali prendi — e «dimentica il profilo» lo cancella come sempre. Serve a sapere quanto lavora il servizio e quanto incassa di commissioni, e lo leggono solo gli amministratori di Barattolo.

<!-- pezzo schermata-027 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (11/17)

Dal 10 ottobre 2026 teniamo, legato al tuo account, come sono finiti i tuoi scambi: una riga per ogni scambio completato — a tutte e due le parti — e una per ogni scambio non completato, che si conta a chi ha preso un ordine e non ha fatto in tempo il suo primo passo (bloccare la garanzia se vende, dire dove ricevere i sats se compra), tanto che l'ordine è tornato in vetrina. Mai a chi ha aspettato, mai a chi si ritira prima che lo scambio parta. Dal 12 ottobre 2026, dove il servizio di scambio dà a chi pubblica più tempo di chi prende, si conta anche a chi ha pubblicato un ordine e, quando glielo prendono, non risponde in tempo o annulla dopo la presa: una sola volta per ordine, e mai se la presa è arrivata mentre i suoi ordini erano in pausa o nella mezz'ora prima. Di ogni presa rimasta senza risposta teniamo comunque una riga, che serve al segno «⚡ Risponde in fretta»: compare accanto al nome di chi, negli ultimi 30 giorni, ha concluso almeno tre scambi pubblicati da lui con tre persone diverse rispondendo di solito entro dieci minuti, e sparisce alla prima presa lasciata senza risposta. Si conta come non completato anche lo scambio in cui la garanzia arriva a scadenza (circa quattro giorni) perché chi compra non ha mai segnato gli euro come inviati, pur avendo ricevuto il recapito a cui mandarli. Se un tuo tentativo ti ha scusato teniamo una riga anche per quello, perché la scusa vale una volta ogni 30 giorni. E se un moderatore, chiudendo una disputa, segna la colpa a chi l'ha persa, teniamo una riga «disputa persa»: compare come «⚖️ N dispute perse» negli stessi posti del contatore, per 90 giorni e già dalla prima; in quei 90 giorni chi pubblica con un filtro non ti accetta, e quello scambio non vale come completato a chi l'ha persa. Chi la perde lo viene a sapere subito, nel messaggio che chiude la disputa. Ogni riga dice il numero dell'ordine, quando, se compravi o vendevi e com'è finita: niente importi. A cosa serve: al contatore «⚠️ N non completati», che conta solo gli ultimi 90 giorni e compare dal secondo (il primo si tollera), e al filtro di chi pubblica — «solo chi ha almeno 1, 3 o 5 scambi P2P completati» —, che guarda quanti ne hai completati e se ne hai di non completati negli ultimi 30 giorni. Chi lo vede: il contatore, quando c'è, lo vede chi vede te — accanto al tuo nome sugli ordini che pubblichi, nella pagina dello scambio o dell'ordine per l'altra persona, e nella pagina del tuo negozio; quanti scambi hai completato, dal 10 ottobre 2026, lo vede anche chi vede te, negli stessi posti («✅ 12 scambi P2P completati», accanto alle stelline): è il numero che aiuta chi sta per scambiare a decidere di chi fidarsi. Quanti ne hai di non completati sotto la soglia della scritta resta tuo, e chi pubblica col filtro non riceve altri numeri: se puoi prendere quell'ordine lo decide il server, e lo dice a te. Un giorno dopo la chiusura di uno scambio, se non hai lasciato la recensione, ti arriva un solo promemoria. Per quanto: circa quattrocento giorni, poi ogni riga si cancella da sola. Vale anche se entri con una chiave Nostr e prendi senza farti riconoscere: all'altra persona continuiamo a non dire chi sei, ma l'esito si scrive sul tuo account come per tutti. Perché uno scambio in cui ci hai provato non ti venga contato, il telefono ci dice anche i tentativi — hai aperto o copiato la richiesta della garanzia, toccato «Apri nel wallet», mandato una fattura che il coordinatore ha accettato o rifiutato, o incollato una che il telefono ha scartato: il gesto, mai la fattura né il pagamento —, e quelli se ne vanno con la cronaca, dopo quaranta giorni. «Dimentica il profilo» cancella subito i tentativi ma non gli esiti: sono del tuo account, come le recensioni, e non è da lì che ci si toglie un contatore.

<!-- pezzo schermata-028 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (12/17)

La pausa degli ordini, se la imposti, sta legata al tuo account: i giorni, le ore e il nome del tuo fuso orario (per esempio «Europe/Rome»), e niente altro. Serve a non far prendere i tuoi ordini dal libro di Barattolo nelle ore che hai scelto (restano visibili, in grigio), e a non contarti una presa arrivata mentre eri in pausa. Non esce da Barattolo, resta finché non la togli, e se ne va subito se dimentichi il profilo.
Il paracadute, se lo apri pubblicando un ordine, sta su quell'ordine: la soglia che hai scelto, il prezzo di BTC che avevamo in quel momento e, se si apre, quando e a che prezzo. Serve a togliere l'ordine dal libro di Barattolo se il prezzo si muove oltre la soglia; l'annullamento vero lo firma il tuo telefono, noi quella firma non la facciamo. Se dimentichi il profilo di scambio lo cancelliamo.
Se togli uno scambio chiuso con la ✕, il server ricorda il numero dell'ordine e quando l'hai tolto, così sparisce anche dagli altri tuoi dispositivi. Si cancella da solo dopo quaranta giorni, e subito se dimentichi il profilo.
Dal 17 settembre 2026, quando un ordine viene preso, le due parti si vedono: chi ha pubblicato e chi ha preso vedono il profilo l'uno dell'altra — lo stesso che sta già sotto ogni annuncio del mercatino: nome, foto, stelline, livello e titolo — e i bottoni per scriversi su Telegram o su Nostr, ma solo dove quei canali esistono davvero (la npub soltanto se ne hai dimostrato il possesso). Prima della presa non si vede niente, e non c'è nessun altro modo di chiederlo: a questa domanda il server risponde solo a una delle due parti di quello scambio. Il perché è che dall'altra parte c'è una persona a cui stai per mandare dei soldi veri, e un volto con una reputazione è quello che rende pesabile la fiducia — la stessa ragione per cui nel mercatino chi vende ha un nome. Te lo diciamo prima: nel foglio dove pubblichi e in quello dove prendi. Al posto dei campi dove prima ci si scriveva il proprio contatto a mano, che non erano verificati da nessuno.

<!-- pezzo schermata-029 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (13/17)

Negli scambi l'altra persona vede il tuo profilo Barattolo: il nome e la foto che hai scelto, le recensioni, il livello, da quanto sei iscritto, gli scambi completati e non completati e, se li hai, il tuo @username Telegram e la tua chiave Nostr (npub), così potete scrivervi. Non vede mai il tuo numero di telefono, da dove ti colleghi, i tuoi recapiti né cosa hai comprato. Se vuoi scambiare senza profilo, entra con una chiave Nostr nuova. Vale con qualunque modo di entrare: anche chi entra con una chiave Nostr è riconosciuto dall'altra persona come tutti (dal 12 ottobre 2026) — chi ha pubblicato vede il suo profilo, e le due parti possono recensirsi. Una chiave Nostr nuova, per l'altra persona, è un'altra persona: non c'è un interruttore, e non c'è un modo di scambiare da Barattolo senza farsi vedere dall'altra parte. L'esito dello scambio si scrive sul suo account come per tutti — è il paragrafo qui sopra sugli esiti degli scambi —, e se arriva al contatore «⚠️ N non completati» quello compare dove compare lui: nella pagina del suo negozio e sugli ordini che pubblica. Gli scambi già presi prima del 12 ottobre restano come erano, e a cancellare il pregresso c'è «dimentica il profilo» — che toglie le prese annotate, non gli esiti. Chi entra con una chiave e pubblica, invece, si mostra — col profilo che ha qui, cioè il nome e la foto della sua chiave: è così da quando le card del libro hanno un volto, e il foglio dove si pubblica lo dice prima.

<!-- pezzo schermata-030 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (14/17)

Dal 12 ottobre 2026, dentro ogni scambio preso c'è una chat. La chat è cifrata fra voi due e Barattolo la trasporta. Se il tuo account è nato su Nostr, Barattolo non la può aprire. Se è nato con Telegram (anche se poi entri con Nostr), il tuo profilo di scambio lo ricava il server: per questo ritrovi scambio e chat su ogni dispositivo, e per questo Barattolo durante lo scambio potrebbe tecnicamente aprirla. Non lo fa. A fine scambio la chat si cancella, per tutti. Il moderatore la legge solo se una di voi due apre una disputa. Per intero. Ogni telefono fa nascere a caso una chiave usa-e-getta per quello scambio: non si ricalcola da niente. Perché tu ritrovi la chat se cambi telefono o browser, o se la memoria del browser si svuota, il telefono ne lascia sul nostro server una copia sigillata, chiusa con la chiave di quello scambio: la apre solo chi ha il tuo profilo di scambio, e il server la riconsegna solo a te — mai all'altra persona, mai a un moderatore. È qui la differenza, e conta dove è nato l'account, non come entri: il profilo di scambio di un account nato su Nostr lo ha solo lui; quello di un account nato con Telegram lo ricava il nostro server dall'account — anche quando poi entri con una chiave Nostr collegata —, ed è per questo che torna da solo su ogni dispositivo. I messaggi arrivano al nostro server già chiusi. Di ognuno il server vede su quale scambio, chi dei due l'ha spedito, a che ora, quanto pesa e fin dove l'altra persona ha ritirato: gli serve per consegnarlo e per avvisare. Il testo no. Lo stesso per le foto e i PDF che vi mandate (dal 16 ottobre 2026): partono cifrati dal telefono, con una chiave a caso che viaggia dentro il messaggio; del file il server vede solo quanto pesa, e lo cancella con la chat. Le foto partono ridisegnate, senza la posizione né gli altri dati della fotocamera; i PDF riscritti senza autore, programma, date e identificativo. L'avviso «hai un nuovo messaggio» non porta il testo. A scambio finito — concluso, annullato, o quando chi vende ha liberato i sats — i due telefoni buttano chiave e messaggi e il server cancella le buste, le copie sigillate e quegli orari: stanno in un archivio a parte che non entra nei backup, e nel registro del server non resta una riga per messaggio, solo quella di un avviso partito. Se una di voi due apre una disputa, il suo telefono chiude la chiave di lettura in una busta per i moderatori — lo legge scritto prima di confermare —; la apre solo il moderatore che prende la disputa, che legge e non può scrivere al posto vostro, e a disputa chiusa si cancella tutto allo stesso modo. Quello che non possiamo cancellare: quel che l'altra persona ha copiato o fotografato dal suo schermo.

<!-- pezzo schermata-031 | schermata -->
## Schermata «I tuoi dati» · Il profilo di scambio P2P (15/17)

Le conversazioni fuori da Barattolo non sono nostre: se vi scrivete su Telegram o su Nostr quella chat è vostra e di chi la trasporta — non la leggiamo, non ce l'abbiamo, e in una disputa non possiamo usarla. A decidere sono i fatti dello scambio: chi ha bloccato i sats, chi ha detto di aver mandato gli euro, chi li ha liberati.
Dal 10 ottobre 2026, negli scambi in contanti di persona, ci sono «📍 Sono qui» e l'appuntamento. «Sono qui» lo tocchi tu, se e quando vuoi: il server riceve una nota firmata con la tua chiave usa-e-getta, con l'ora e — solo se il telefono la dà — la posizione (il telefono te la chiede, e si può dire di no); se la dai, ne ricaviamo subito la distanza dall'altra persona e dal luogo dell'appuntamento. L'appuntamento lo scrive chi vende nel recapito, che viaggia cifrato fra voi due: al server arrivano solo l'ora e le coordinate del punto, se l'indirizzo è stato riconosciuto — mai il testo. Mentre chi vende scrive l'indirizzo, i suggerimenti li chiediamo noi a Photon, che usa i dati di OpenStreetMap, mandando solo il testo cercato: né chi sei né dove sei; «Usa la mia posizione» non esce dal nostro server. Chi legge: l'altra persona vede l'ora delle tue presenze, mai la tua posizione; un moderatore vede il confronto se si apre una disputa. Posizioni e testi cercati non li scriviamo nei registri del server. Per quanto: le posizioni e il punto restano solo finché una disputa sui contanti è possibile — si cancellano quando i sats vengono liberati o lo scambio si chiude (annullato, scaduto, tornato nel libro), e in ogni caso entro quindici giorni; restano le ore e le distanze, che se ne vanno con la cronaca dopo quaranta giorni. Con «dimentica il profilo» se ne vanno anche le tue presenze e i tuoi appuntamenti; su uno scambio ancora aperto resta solo l'ora, perché l'altra persona l'ha già vista. Il GPS si può falsificare: per noi è una conferma, non una prova assoluta.
👤 Il tuo profilo di scambio
Gli ordini di scambio sono pubblici per come è fatto il coordinatore: vivono sui relay e li legge chiunque, e da settembre 2026 una copia sta anche sul nostro relay — serve a far vedere il libro degli scambi anche quando i relay del coordinatore non rispondono. Non c'è scritto chi sei: un ordine porta l'importo, il metodo di pagamento e una chiave usa-e-getta, diversa a ogni scambio. Dei messaggi che il coordinatore ti manda durante lo scambio — buste cifrate, che si aprono solo dal tuo telefono — sul nostro relay non teniamo copia: per un giorno, fra il 17 e il 18 settembre 2026, l'abbiamo tenuta per avvisarti più in fretta, e da quando gli avvisi li racconta il coordinatore non serve più. Le conversazioni fra te e l'altra persona invece non passano di lì: sono cifrate e viaggiano sui relay del coordinatore, e sul nostro non ne teniamo copia.

<!-- pezzo schermata-032 | schermata -->
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

<!-- pezzo schermata-033 | schermata -->
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

<!-- pezzo schermata-034 | schermata -->
## Schermata «Vendi (pubblicare un annuncio)» (1/2)

&#8592;
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
Consegna — spunta le opzioni che offri
 🚚Spedizione
 🤝Ritiro in zona
 💾Invio del codice onlinebuono regalo, codice sconto, licenza
Se l'acquirente sceglie il codice, lo consegnerai dentro Barattolo dopo il pagamento: niente chat private, tutto tracciato. 💡 Fai uno screenshot datato del saldo o della validità prima di vendere: in caso di disputa, le prove decidono.
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
 🌍 Spedizione internazionale 
Dogana ed eventuale IVA sono a carico di chi riceve: non le incassi tu e non le anticipa Barattolo.
 Non spedisco in Italia
Lo paga chi compra, tu lo incassi per intero. Nel tuo paese vuoto o 0 = gratis. Nelle zone estere 0 = gratis e casella vuota = lì non spedisci. San Marino e Città del Vaticano contano come Italia.
Costo verso un punto di ritiro (facoltativo)
sats
Spesso costa meno che a un indirizzo. Vuoto = vale il costo qui sopra; 0 = gratis al punto.

<!-- pezzo schermata-035 | schermata -->
## Schermata «Vendi (pubblicare un annuncio)» (2/2)

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

<!-- pezzo schermata-036 | schermata -->
## Schermata «Profilo» · Il tuo profilo

## Il tuo profilo
Completa il profilo ▾
Il tuo catalogo▾
📋I tuoi annunci▾
✏️ Modifica più annunci
📥Importa in blocco▾
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
🏪 Catalogo esterno 
🏪Pacchi al tuo punto ▾
🔁Doppioni su Nostr ▾
Negozio e spedizioni▾
📊Il tuo negozio ▾
🏪Cassa in negozio›
👁Guarda il tuo negozio come lo vedono tutti›
</>Widget per il web›
📦Come spedisci ▾
🚚Spedizione gratis ▾
🎁Sconto sugli articoli ▾
🎟Codici sconto ▾
🖼Banner del negozio ▾
🔗Link del negozio ▾
🌴Negozio in ferie ▾
Quando compri▾
🫙Nel tuo barattolo ▾
🔎Avvisi di ricerca ▾
📍Punti di ritiro ▾
🔒Come funziona il pagamento protetto›
Incassi e pagamenti▾
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
📄Esporta i tuoi datiIl CSV dei tuoi affari conclusi, comodo per la contabilità.›
Livello e inviti▾
⭐Recensioni ricevute ▾
🎖Livello e titolo ▾
💌I tuoi inviti ▾
🏅Distintivi ▾
Avvisi e aspetto▾
🔔Avvisi▾
🌗Aspetto▾
 Chiaro o scuro? Con Auto segue il sistema.
Auto
☀️ Chiaro
🌙 Scuro
 Quanto grande si legge Barattolo. La scelta ti segue su
 ogni dispositivo.
Privacy▾
🆔Identità▾
🔐I tuoi dati›
🗑Cancella il mio account›
🧅Sito Tor▾
Supporto▾
🤖Chiedi a Tappo›
💬Assistenza›
Amministrazione▾
⚖️ Moderazione P2P
💬 Assistenza clienti
On-chain
Tutorial
Esci

<!-- pezzo schermata-037 | schermata -->
## Schermata «On-chain e finestre della Mini App» · On-chain (1/3)

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
lnbc…
inquadra il QR col wallet, o tocca la invoice per copiarla
 ⚡ Apri nel wallet
⚡ Generane una nuova
✓ Ho pagato
Annulla
## Come vuoi pagare?
## ⚡ Compra subito
 Stai per pagare sats
 dal tuo wallet collegato. I sats finiscono bloccati
 nel deposito di garanzia, come sempre: al venditore arrivano solo quando
 confermi di aver ricevuto l'oggetto.
⚡ Conferma e paga
Annulla
## 🔗 Condividi il barattolo
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

<!-- pezzo schermata-038 | schermata -->
## Schermata «On-chain e finestre della Mini App» · 🎁 Lascia una mancia (2/3)

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
## 🏪 Cassa in negozio
✕
€
I tuoi articoli
Incassa
🧾 Le vendite della cassa, in «Ordini»
💡 Chi compra inquadra il QR con qualsiasi wallet: non serve un account. I sats vanno dritti al tuo wallet, senza deposito di garanzia e senza commissioni: è un pagamento di persona, come al banco.
 sats
✓ Ricevuto
Nuovo conto
Annulla il conto
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

<!-- pezzo schermata-039 | schermata -->
## Schermata «On-chain e finestre della Mini App» · Entra con Nostr (3/3)

## Entra con Nostr
 Dimostri di possedere la tua chiave firmando una sfida.
 La chiave privata non viene mai inviata a nessuno.
🔄 Riprova
📱 Entra con nostrconnect
📋 Copia il link
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
## Ti conosciamo già!
Usa l'account esistente
Annulla
## 🏅 Distintivi guadagnati
 Si guadagnano usando Barattolo: affari conclusi, feedback, identità verificate.
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
