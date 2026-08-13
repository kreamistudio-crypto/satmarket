# Barattolo 🫙⚡ — istruzioni per Claude

Mini App Telegram: mercatino tipo Subito.it con pagamenti SOLO in satoshi
ed escrow Lightning custodial (LNbits). Proprietario: Andrea (principiante,
guidalo passo passo, un comando alla volta, spiega con metafore semplici).
Collaboratore: Alan (25% ricavi netti, accordo scritto). Lingua: italiano.

## Architettura

- `server.py` — backend FastAPI + SQLite (`satmarket.db`), un solo file.
  Escrow LNbits (invoice key incassa, admin key paga), commissione
  SOSPESA (COMMISSIONE_PERCENTO=0 nel config, cifra da decidere:
  quando si accenderà vanno rimessi i testi con la cifra — l'elenco
  dei punti è nel commit del lug 2026 che l'ha azzerata — E va
  ricordato che dal cantiere C-1 la cintura di `paga_venditore` è
  RETROATTIVA: una invoice depositata col vecchio netto e pagata col
  nuovo non combacia più e viene rifiutata, quindi il venditore dovrà
  incollarne una nuova. È il comportamento corretto — non si paga la
  cifra sbagliata — ma il giorno dell'accensione va guardata la coda
  degli ordini `confirmed` con una invoice già depositata),
  notifiche via bot Telegram, ricerca AI (Haiku), orologio asyncio per gli
  sblocchi automatici (72h dalla consegna, 10gg dalla spedizione).
  L'IMPORTO DI OGNI BOLT11 IN USCITA SI CONTROLLA CONTRO IL DOVUTO
  (ago 2026, C-1 dell'audit, ed è la regola da non ammorbidire).
  Giudice unico `importo_invoice`: l'aritmetica dei millisat vive lì e
  in nessun altro posto — era in tre copie a mano — e ci passano il
  deposito dell'invoice a mano (ordini e rimborsi d'asta), il
  Lightning address e la cintura. Fail-closed: campo mancante → 0, che
  non combacia mai col dovuto, quindi anche le invoice a importo
  libero si rifiutano da sole. IL PERCHÉ, che è la parte da tenere:
  nel LNURL-pay la fattura la fabbrica il wallet del BENEFICIARIO, e
  il `ln_address` è auto-dichiarato — quindi può puntare a un dominio
  dell'utente. Finché `invoice_da_ln_address` restituiva la `pr` senza
  rileggerla e `paga_venditore` non passava `amount` a LNbits, usciva
  la cifra scritta DENTRO la bolt11: bastava un diritto qualunque,
  anche da 1 sat, e il tetto della perdita era il saldo della
  cassaforte, cioè l'escrow di tutti (riprodotto sul codice di prima:
  1 sat dovuto, 100 milioni usciti). Il controllo esisteva già sul
  ramo dell'invoice incollata a mano e mancava solo su quello
  AUTOMATICO — cioè quello che gira da solo senza che nessuno guardi,
  ed è la lezione più larga di questo cantiere. L'uguaglianza ESATTA è
  la specifica LUD-06, non una nostra severità. `paga_venditore` porta
  `atteso_sats` OBBLIGATORIO E SENZA DEFAULT apposta: è ciò che fa
  ereditare il controllo a ogni futura strada d'uscita, e chi lo
  dimentica lo sente da Python. Il rifiuto non chiama LNbits nemmeno
  una volta, e NON inventa un ramo nuovo — vale quello di sempre: il
  diritto resta aperto (`confirmed`/`refund`/`da_riscuotere`), i sats
  in cassaforte, l'utente invitato a incollare una invoice a mano — in
  più i moderatori ricevono l'avviso (un importo storto è o un wallet
  rotto o un tentativo di prelievo: mai dentro un `return False`;
  l'avviso è sotto try/except, una notifica non deve mai rompere un
  rifiuto). Gratis: `salva_ln_address` prova l'address alla
  registrazione, quindi un endpoint bugiardo si ferma già alla porta.
  IMPERFEZIONE DICHIARATA: un ln_address bugiardo ritenta a ogni giro
  — non lo disattiviamo da soli, perché un wallet legittimo può avere
  un singhiozzo e togliere l'address a un venditore onesto sarebbe una
  cura peggiore del male; se in rodaggio si vedrà un caso vero la leva
  è un contatore di rifiuti sull'utente. `prove.py` difende la FORMA
  con cinque sentinelle (firma senza default, rifiuto prima
  dell'admin key, nessuna chiamata a un argomento in tutto il file,
  `amount_msat` una volta sola, la `pr` mai restituita nuda): questo
  controllo sparisce in un riordino senza rompere nessuna prova
  funzionale, ed è esattamente il tipo di riga che va sorvegliata.
  E `paga_venditore` HA TRE ESITI, non due (ago 2026, la voce media
  più grave dell'audit): PAGATO, NON_PAGATO e **INCERTO**. La POST
  verso LNbits stava senza `try`: se il nodo pagava ma non riusciva a
  rispondere entro i 60 secondi, l'eccezione risaliva, il database non
  registrava NIENTE e l'ordine restava ritentabile — e i ritentativi
  non sono ipotetici (lo scandaglio di `salva_ln_address`, la invoice
  appena depositata, il compratore che riconferma). IL DOPPIO
  PAGAMENTO È VERO SU UNA STRADA SOLA, ed è quella che si usa proprio
  quando le cose vanno male: sul ramo dell'invoice incollata a mano ci
  salverebbe Lightning (una fattura saldata non si paga due volte), ma
  sul ramo del **Lightning address** ogni tentativo conia una fattura
  NUOVA. Riprodotto sul codice di prima: due giri, due fatture
  diverse, due richieste di pagamento per lo stesso ordine. Non è un
  booleano APPOSTA — dentro un «if» l'incerto sembrerebbe un successo,
  sotto un «not» un fallimento — e una sentinella verifica che nessuno
  lo rimetta lì. Su INCERTO la riga si CONGELA (`payout_stato`:
  '' | 'incerto' | 'uscito', più `payout_hash` e `payout_verso`, su
  `ordini` e su `rimborsi_asta`): stato e invoice restano dov'erano e
  le TRE funzioni d'uscita (`_sblocca_sats`, `_rimborsa_compratore`,
  `_paga_rimborso`) escono a mani vuote. Ai moderatori arriva il
  `payment_hash`, che è quello che si cerca su LNbits. Si scongela
  dalla sezione «🧊 Pagamenti da verificare» del Profilo admin
  (`/api/admin/pagamenti` + `/decidi`): «è uscito» NON riscrive il ramo
  riuscito in copia — timbra 'uscito' e richiama la funzione di
  sempre, che vede il timbro, non paga e va dritta alla chiusura, così
  contatori, notifiche e stato finale restano in un posto solo; «non è
  uscito» toglie il congelamento. UPDATE condizionato: il secondo
  moderatore trova il 409. `payout_verso` dice CHI aspettava i sats e
  NON si deduce dallo stato: un ordine in 'dispute' può essere sulla
  strada del venditore o su quella del compratore, e indovinare
  vorrebbe dire chiudere l'affare a favore della persona sbagliata.
  UNA DISPUTA DECISA RESTA IN MANO AL MODERATORE (ago 2026): quando
  lo sblocco non riesce a pagare, l'ordine passa a 'confirmed' — e
  spariva dalla query di `risolvi_disputa`, che guardava i soli stati
  di disputa. Da lì il moderatore non poteva più decidere niente, in
  particolare non poteva più rimborsare, e i sats restavano fermi
  senza rimedio (il gemello col rimborso finiva in 'refund', stessa
  trappola). LA STRADA SCARTATA, e va tenuta perché è quella che torna
  in mente: NON riscrivere lo stato quando l'ordine viene da una
  disputa. 'confirmed' vuol dire «i sats spettano al venditore, manca
  il modo di darglieli», che dopo una disputa decisa a suo favore è
  la verità — e da lì `deposita_invoice` funziona e il sollecito degli
  incassi lo insegue; tenere 'dispute' lo renderebbe AMBIGUO (la
  stessa parola per «un moderatore deve guardarlo» e «è stato deciso,
  aspetta un wallet»). La transizione era giusta: mancava solo il
  ritorno in coda. Quindi `risolvi_disputa` accetta anche
  'confirmed'/'refund' quando `disputata=1` — che è anche la
  migrazione del pregresso, gli ordini già in trappola tornano
  decidibili senza toccare il database — e per cambiare strada il caso
  si RIAPRE ('dispute') prima di ridecidere, invece di allentare le
  guardie delle funzioni d'uscita (`_sblocca_sats` non parte da
  'refund' e deve restare così, o il ripensamento sarebbe un no-op
  silenzioso). L'esito si valida PRIMA, o un refuso lascerebbe il caso
  riaperto per niente. E chi PERDE una disputa ora lo viene a sapere:
  nel ramo fallito veniva avvisata solo la parte che aspettava i sats.
  Una volta sola, nel giro in cui l'ordine cambia stato davvero.
  `verifica-pagamento` È DI CHI HA COMPRATO (ago 2026): chiamava
  `verifica_utente` e ne buttava via il risultato, poi leggeva
  l'ordine per solo id — l'unica rotta `/api/orders/{id}/…` senza
  guardia di proprietà, mentre il gemello dei rilanci ce l'ha e il suo
  commento la nomina pure. Non si rubavano sats (senza la invoice
  pagata non parte niente) ma si otteneva un ORACOLO: gli id sono
  progressivi, e le risposte distinguevano «non esiste» (404) da
  «esiste, non pagato» da lo STATO REALE di un ordine altrui — cioè in
  fila si leggeva il registro ordini dell'intero mercatino, più una
  domanda a LNbits sul payment_hash di un altro e la possibilità di
  innescare in anticipo il flusso altrui (notifiche, decadenza delle
  offerte, «venduto» su Nostr e sul canale). Ora la guardia è dentro
  la WHERE col 400 dei fratelli, che è anche la risposta che NON
  distingue «non è tuo» da «non esiste»: chi enumera non impara nulla.
  `/api/listings` è PUBBLICA (vetrina anche senza Telegram) ma serve solo
  la whitelist esplicita `CAMPI_VETRINA`: `venditore_id` esce solo alle
  richieste autenticate. La ricerca AI resta riservata agli autenticati
  (pubblica sarebbe credito API regalato ai bot). Tutto il resto è
  autenticato via `verifica_utente`. Moderazione a tre strati su
  `pubblica()`: filtro `PAROLE_VIETATE` (parole intere su testo
  normalizzato), parere AI opzionale (fail-open se la chiave manca o
  la chiamata fallisce), notifica agli admin di ogni annuncio +
  endpoint admin di rimozione e di statistiche (`/api/admin/stats`:
  card 📊 + lista utenti in fondo al Profilo, solo moderatori;
  `utenti.registrato` è la data del primo accesso, "—" per chi
  c'era prima della colonna). I casi ambigui (cannabis
  light, pistola sparachiodi...) NON vanno nella lista parole: li
  valuta l'AI.
  CHI SI FINGE BARATTOLO (ago 2026, M1 dell'audit): dalle anteprime
  dei link `/annuncio/{id}` è una scheda COL NOSTRO NOME su un NOSTRO
  indirizzo dove titolo, descrizione e immagine li sceglie chi
  pubblica — «Barattolo — verifica il tuo pagamento in sospeso»
  condiviso da lì è un link autentico che sembra un messaggio
  ufficiale, e chi lo riceve non ha NESSUN segnale per distinguerlo.
  Voce nel `PROMPT_MODERAZIONE` con DUE esiti, e la gradazione è il
  punto: VIETATO quando il testo **SI RIVOLGE A CHI LEGGE** come
  farebbe la piattaforma (avviso di sicurezza, account da sbloccare,
  pagamento in sospeso, dati da confermare, link da aprire,
  un'AZIONE da compiere) — vale anche per un ALTRO servizio, una
  banca o un corriere; DUBBIO per chi si intesta soltanto un ruolo
  che non ha («Assistenza Barattolo», «Barattolo Ufficiale»), che in
  revisione è già fuori dalla vetrina E dall'anteprima, quindi il
  caso incerto costa una riga di coda e non un rifiuto. Il segno più
  netto del VIETATO è che nomina un ordine, un account o un pagamento
  CHE ESISTEREBBERO GIÀ — cosa impossibile in un annuncio che chi
  legge sta guardando per la prima volta.
  «ASSISTENZA BARATTOLO — SUPPORTO AGLI UTENTI», e la storia vale più
  del caso: è l'esempio di come NON si tiene un collaudo.
  Per tre giorni il modello ha risposto VIETATO dove il prompt gli
  insegna DUBBIO su quella riga esatta, e l'atteso del collaudo fu
  ALZATO a VIETATO per inseguirlo — con la motivazione, allora
  ragionevole, che sbagliava dalla parte severa su un caso che la
  severità la merita. Ad ago 2026 il modello si è ri-allineato al
  prompt e risponde DUBBIO, e l'atteso è tornato DUBBIO: quello che
  il prompt insegna, e che non era mai cambiato.
  LA REGOLA CHE NE ESCE (decisione di Andrea): **un atteso che cambia
  due volte non è più un atteso**. L'atteso segue il PROMPT, non il
  modello — se un domani quel caso oscillasse ancora si dichiara come
  CASO INSTABILE nel collaudo, e non lo si rincorre una terza volta:
  un valore che si riscrive a ogni giro non prova più niente, e
  intanto il conto smette di essere leggibile. La stessa ragione per
  cui l'atteso resta STRETTO (mai «VIETATO o DUBBIO»): i giri devono
  poter tornare pieni, o una regressione vera si perde nel rumore.
  Il prompt NON si è mai toccato in tutta questa storia, ed è ciò che
  ha reso possibile il ritorno: la sua riga DUBBIO è sempre stata
  viva, tenuta in piedi anche da «Barattolo Ufficiale — store».
  Se un domani cadessero tutt'e due, la voce è scivolata verso il
  rifiuto e va guardata.
  DUE CONTRO-REGOLE, e sono la metà che conta: quelle che un riordino
  toglie per prime perché sembrano un ripensamento. 1) **Nominare
  Barattolo è lecito e non è MAI di per sé un motivo** («gadget di
  Barattolo», «venduto tramite Barattolo»): senza, il divieto diventa
  un filtro sulla PAROLA, cioè un blocco su merce legittima.
  2) **RACCONTARE come funziona Barattolo è lecito e comune** — chi
  spiega il deposito di garanzia sta RASSICURANDO chi compra, parla
  in prima persona di sé e della sua roba, non a nome nostro.
  LA SECONDA È COSTATA UN FALSO POSITIVO VERO, ed è la storia da
  tenere. Prima stesura, primo giro del collaudo sul VPS: 14/15, e a
  cadere era «Bicicletta da corsa Bianchi» la cui DESCRIZIONE spiega
  l'escrow — bocciata col motivo «non descrive l'oggetto in vendita».
  L'oggetto c'era, era una bici, stava nel TITOLO. La causa era la
  formulazione: dentro la definizione del VIETATO c'era scritto «e
  non descrive nessun oggetto in vendita», e il modello l'ha presa
  per un test SUFFICIENTE da applicare alla sola descrizione. La cura
  ha tre gambe — la distinzione rivolgersi/raccontare, la REGOLA CHE
  VINCE SULLE ALTRE («se c'è davvero una COSA in vendita e a chi
  legge non si chiede di verificare, sbloccare o confermare NIENTE
  allora non è impersonazione: al massimo è un annuncio prolisso, e
  un annuncio prolisso è OK»), e la COPPIA DI ESEMPI che insegna il
  confine meglio della regola astratta: la bici → OK e le cuffie con
  la descrizione avvelenata → VIETATO, due descrizioni che nominano
  tutt'e due Barattolo e finiscono in due esiti opposti.
  ATTENZIONE alla seconda metà della regola sovrana («…e non si
  chiede NIENTE»): senza, diventerebbe una scappatoia — anche
  l'annuncio avvelenato una cosa in vendita ce l'ha.
  E L'ANNUNCIO SI GIUDICA INTERO, titolo e descrizione INSIEME:
  l'oggetto può stare nel solo titolo e la descrizione parlare
  d'altro, e va benissimo; ma un messaggio rivolto al lettore
  avvelena l'annuncio anche col titolo pulito — `og:title` viene
  dall'uno e `og:description` dall'altra, e la card li mostra
  entrambi. Il «vale sul TITOLO come sulla DESCRIZIONE» della prima
  stesura diceva la cosa giusta e induceva quella sbagliata: il
  modello ha giudicato i due campi SEPARATAMENTE.
  IL RIFIUTO DICE COSA HA SBAGLIATO: `MSG_RIFIUTO_IMPERSONAZIONE` al
  posto della lista di armi e droghe, che non c'entrava niente — e
  dice anche DOV'È IL CONFINE, che qui è sottile. In
  `messaggio_rifiuto` l'impersonazione si guarda PRIMA dei servizi, e
  non è l'ordine che capita: il motivo lo scrive l'AI con parole sue
  e può dire «finto servizio clienti», che col ramo dei servizi
  davanti risponderebbe «i servizi non sono ancora supportati» a chi
  ha appena provato a spacciarsi per noi (una prova nomina quel caso,
  ed è l'unica che diventa rossa scambiando i rami).
  `PAROLE_IMPERSONAZIONE` sono prefissi, e «fint» c'è perché «finto»
  NON è una declinazione di «finge» — l'ha detto una prova, non la
  lettura del codice. E «confond» è entrata ad ago 2026 da un caso
  VERO (sotto): il motivo diceva «progettato per confondere con
  Barattolo», nessuna delle altre parole matchava, e a un venditore
  onesto è arrivata la lista delle armi e delle droghe.
  «SAT» È LA MONETA, NON UN NOSTRO MARCHIO (ago 2026, falso positivo
  vero dal campo, e la TERZA contro-regola): «Sat's Oil 🫒 GENESIS
  EDITION» bloccato per impersonazione col motivo «il nome appare
  progettato per confondere con Barattolo (associando "sat")». Su un
  mercatino che incassa in satoshi chiamarsi coi sats è la cosa più
  normale del mondo: il prompt ora dice che 'sat', 'sats', 'satoshi',
  'bitcoin' sono la MONETA e non un marchio, e soprattutto che UNA
  SOMIGLIANZA DI NOME NON È MAI UN MOTIVO — a decidere resta sempre e
  solo il gesto di RIVOLGERSI a chi legge. Senza quella riga il
  divieto torna a essere un filtro sulla PAROLA, che è l'errore già
  pagato col «barattolo» vaso di vetro.
  E SE IL TESTO NON C'È NON SI CONCLUDE NIENTE: lo stesso motivo
  diceva «il titolo e la descrizione mancano» mentre il titolo c'era
  — il modello aveva DEDOTTO l'impersonazione da ciò che il testo non
  diceva. La regola nuova («un'assenza non è un tentativo di
  ingannare nessuno; non dedurre MAI l'impersonazione dal non detto»)
  vale in sé, e in più DISINNESCA quella confabulazione: se il
  modello crede che il testo manchi, adesso quella premessa porta a
  OK invece che a VIETATO. Nel collaudo il caso è una REGRESSIONE
  PERMANENTE con due gemelle — «SatShop», che dice se la cura ha
  imparato la regola o solo il nome, e «Satoshi Coffee» a descrizione
  VUOTA, che mette insieme i due difetti.
  Il collaudo col MODELLO vero è `collaudo_impersonazione.py` (19
  casi, ago 2026: **18/19 e ZERO falsi positivi**, i tre nuovi sui
  sats passano tutti). L'unico fuori posto era **«Assistenza
  Barattolo — supporto agli utenti»**, atteso VIETATO e risposta
  DUBBIO: non un falso positivo ma un «caso cattivo passato», il tipo
  meno grave — e da quando l'AI segnala e non decide quel caso finisce
  comunque in coda, sotto gli occhi di un moderatore. L'atteso è stato
  RIMESSO a DUBBIO (vedi la voce sua, sopra): col prossimo giro il
  conto deve tornare **19/19**. CHI LO RILANCIA SCRIVA QUI IL NOME di
  quel che cade: un «18/19» senza nome è un numero su cui fra sei mesi
  nessuno può agire, ed è esattamente il rumore in cui una regressione
  vera si perde. Vuole la chiave e VA RILANCIATO A OGNI RITOCCO DEL
  PROMPT — è
  l'unica cosa che dice se il modello ha capito, e il falso positivo
  della bici è saltato fuori da lì e non dalla lettura. `prove.py`
  difende la FORMA (la voce, le due contro-regole, la regola sovrana
  con la sua seconda condizione, la coppia di esempi) e che
  `moderazione_ai_lotto` non abbia un prompt SUO — 500 righe di CSV
  passano di lì, e due prompt che si sdoppiano lascerebbero scoperta
  in silenzio la strada da cui gli annunci entrano a centinaia.
  Nel collaudo la bici è una REGRESSIONE PERMANENTE e ha accanto una
  GEMELLA scritta con altre parole: se cadesse solo la gemella
  vorrebbe dire che la cura ha insegnato al modello l'esempio invece
  della regola. Il conto separa i falsi positivi dagli altri sbagli,
  perché non pesano uguale — un OK finito altrove è un annuncio
  legittimo bloccato, e se ne accorge solo chi l'ha scritto.
  L'AI SEGNALA, NON DECIDE (ago 2026, decisione di Andrea dopo il
  falso positivo qui sopra, che ha tenuto fermo un venditore vero).
  Fino a ieri un VIETATO dell'AI bloccava secco e l'annuncio non
  nasceva nemmeno: chi sbagliava non lo sapeva nessuno, tranne chi
  protestava. Ora il rifiuto resta SOLO dove il no è la risposta
  giusta anche quando il modello ha sbagliato — cioè dove non esiste
  una lettura innocente — e tutto il resto va in REVISIONE.
  LA RAGIONE PER CUI SI PUÒ FARE, ed è quella che rende la scelta poco
  rischiosa: in revisione l'annuncio NON È PUBBLICO. Non è che la
  merce illegale va online aspettando un umano — resta invisibile
  esattamente come se fosse stata rifiutata. Cambia solo che esiste
  una riga, che il venditore legge «in attesa» invece di «no», e che
  qualcuno deve guardarla: IL COSTO È LA CODA, NON IL RISCHIO.
  L'ELENCO, dichiarato e non dedotto — QUATTRO famiglie: 1) armi,
  munizioni ed esplosivi; 2) droghe e stupefacenti; 3) sesso a
  pagamento e sfruttamento, minori compresi; 4) documenti falsi,
  credenziali, carte clonate, account rubati.
  COSA NON C'È E PERCHÉ, che è la metà da leggere: refurtiva,
  contraffazione, farmaci con obbligo di ricetta e animali protetti
  sono illegali quanto gli altri, ma hanno tutti una LETTURA INNOCENTE
  che il modello può aver frainteso — un iPhone senza scatola non è
  rubato, una borsa di marca non è falsa, un integratore non è un
  farmaco, un pappagallo non è una specie protetta. Su quelli un no
  secco ferma gente onesta in silenzio, e una riga in coda costa un
  tocco. Fuori anche l'impersonazione (il caso che ha aperto tutto) e
  i servizi, che erano già DUBBIO.
  IL GIUDICE È `_vietato_bloccante(motivo)`, che guarda il motivo
  scritto dal modello con parole sue, A PAROLE INTERE come il filtro
  di casa — `PAROLE_BLOCCANTI` per le corte (esatte: «arma» sta dentro
  «armadio») e `PREFISSI_BLOCCANTI` per le lunghe senza omonimi, che
  così prendono le declinazioni. FAIL-SAFE VERSO LA CODA: un motivo
  che non si riconosce non blocca — sbagliare qui fa guardare una riga
  a un umano, sbagliare nell'altro verso ferma un venditore onesto
  senza che nessuno lo sappia.
  E IL DECLASSAMENTO STA NEL GIUDICE UNICO `_leggi_verdetto`, NON NEL
  PROMPT, deliberatamente: il modello è già stato visto disobbedire
  alla lettera del prompt (dice VIETATO dove gli si insegna DUBBIO,
  vedi «Assistenza Barattolo»), quindi la garanzia deve stare dove il
  modello non arriva; e i verdetti del prompt li collauda uno script
  che vuole la chiave, cambiarlo alla cieca sarebbe un ritocco non
  verificato. La leva `MODERAZIONE_REVISIONE` resta sovrana: spenta,
  è ancora il binario di ieri (rifiuto secco), quindi il freno
  d'emergenza continua a fare quello che promette — ed è anche
  l'unica strada da cui `MSG_RIFIUTO_IMPERSONAZIONE` è ancora
  raggiungibile.
  IMPERFEZIONE DICHIARATA: se l'AI scrive «droga» sulla cannabis
  light — un caso che questo progetto considera grigio apposta — il
  blocco scatta. Si accetta: quando il modello è abbastanza sicuro da
  dire quella parola secca il no è la risposta giusta, e chi non è
  d'accordo protesta. La lista si accorcia, non si allunga.
  IL COSTO, MISURATO e non stimato (`stima_coda_moderazione.py` sui
  rifiuti VERI del registro, 30 giorni di produzione): la coda passa
  da 7 a 14, cioè **0,2 annunci in più al giorno**. È il numero che
  rende la decisione facile — e va rimisurato se il volume cresce.
  UNA PROVA HA CAMBIATO LATO: chiedeva che «VIETATO: impersonazione»
  fosse un rifiuto secco, cioè certificava il comportamento che ha
  fermato il venditore (il precedente è la sentinella del reaper sui
  'creato', e quella degli avatar).
  Terza via della moderazione (lug 2026, decisione di Andrea: basta
  blocchi a priori — l'AI segnala, l'ADMIN decide): il prompt ha TRE
  verdetti — VIETATO solo per i casi netti (armi, droghe, sesso...),
  DUBBIO per i grigi (servizi non palesemente vietati, buoni
  riscattabili presso il venditore stesso; l'«ambiguo ma
  plausibilmente lecito» resta OK). `_leggi_verdetto` è il giudice
  unico (singolo e lotto): a leva `MODERAZIONE_REVISIONE` spenta il
  dubbio torna vietato (binario di ieri). Col dubbio l'annuncio nasce
  (o la modifica lo manda) in `stato='revisione'`: invisibile al
  pubblico per costruzione (i filtri stato='attivo' non si toccano),
  visibile al proprietario in /miei col badge ⏳ (riga spenta, niente
  Modifica, resta il ritiro), scudo anti-doppione allargato
  ('attivo','revisione'), ganci TRATTENUTI (niente Nostr/promo/match/
  distintivi — `_dati_distintivi` esclude la revisione). Risposta col
  flag `{revisione:true, attesa_ore}` (leva REVISIONE_ATTESA_ORE, solo
  testi onesti: «di solito entro N ore», mai un silenzio). Circuito:
  `avvisa_revisione` manda ai moderatori la notifica con tastiera
  inline ✅/❌ via bot_api (notifica() non porta reply_markup;
  callback_data `rev:ok|no:{id}`, NIENTE token in memoria: deve
  sopravvivere ai riavvii, autorizza `e_admin` sul mittente) +
  sezione «⏳ In revisione» sopra le stats admin del Profilo
  (`rigaRevisione`/`decidiRevisione`) + pallino `.off-dot` sul tappo
  (conteggio `in_revisione` in /api/me solo admin). Il cuore unico è
  `decidi_revisione` (UPDATE condizionato sullo stato: il secondo
  moderatore trova il 409, mai doppi ganci): ✅ = attivo + partono i
  ganci trattenuti (Nostr con `solo_aggiornamento` se l'evento
  esisteva già — il caso modifica — e promo solo senza post_canale_id;
  accoda_match è sempre innocuo per il dedup persistente); ❌ =
  'rimosso' + messaggio gentile al venditore + ritiro da Nostr e dal
  canale (serve da quando esiste il ripensamento: prima si poteva dare
  per scontato che un annuncio in revisione non fosse MAI stato
  online, e per un riaperto non è vero).
  LA DECISIONE È REVERSIBILE (lug 2026, decisione di Andrea): terzo
  esito `riapri` di `decidi_revisione` — da 'attivo' o 'rimosso' si
  torna in 'revisione'. Senza, l'unico rimedio a un rifiuto sbagliato
  sarebbe chiedere al venditore di ripubblicare. Riaprire vuol dire
  fuori da OGNI vetrina, non solo dalla nostra: ritiro NIP-09 + post
  di canale cancellato + ordini 'creato' annullati, e la guardia degli
  affari in corso della rimozione admin (con sats in cassaforte prima
  si chiude l'ordine). E perché il ripensamento esista davvero dev'essere
  RITROVABILE: `GET /api/admin/revisione?decisi=1` dà le ultime 20
  decisioni degli ultimi `GIORNI_RIPENSAMENTO` (7) — l'ULTIMA per
  annuncio, via MAX(id) sul registro — e nel Profilo admin c'è la
  sezione «↩︎ Decisi di recente» (`rigaDecisa`) col bottone. Si chiede
  SEMPRE, anche a coda vuota: è quando la coda è vuota che uno si
  accorge di aver sbagliato a svuotarla. La risposta resta un array in
  entrambi i casi, così un client vecchio in cache vede la coda di
  sempre. Il motivo mostrato pesca `esito IN ('dubbio','vietato')`:
  dall'import aperto anche il «vietato» dell'AI mette in coda, e
  guardare il solo dubbio lascerebbe metà coda senza spiegazione.
  La modifica firmata
  degli importati resta bloccante anche sul dubbio (dichiarato:
  l'import orario riporterebbe dentro). Import CSV: righe dubbie
  CREATE in revisione (contatore `in_revisione_n` nel report, fuori
  da Nostr/promo, niente tastiera per riga). Orologio
  `sollecita_revisioni` (leva REVISIONE_SOLLECITO_GIORNI, 2): UNA
  notifica aggregata al giorno, ma l'annuncio RESTA in attesa — mai
  online da solo, gemello del «prompt mai auto-modificato». REGISTRO
  `moderazione_log` (append-only, `registra_moderazione` fail-open):
  ogni esito di parole/AI/lotto/admin con motivo e deciso_da;
  `/api/admin/stats.moderazione` = in_revisione + riepilogo 30gg +
  motivi frequenti + ultime 20 righe, sezione «🛡 Registro
  moderazione» nel Profilo admin — è con QUESTI dati che il prompt si
  corregge A MANO: la macchina raccoglie, l'umano decide.
  Scudo anti-doppione (lug 2026, nato da un bug vero: 5 annunci
  identici da un solo utente): `pubblica()` risponde in modo
  IDEMPOTENTE — stesso venditore + stesso titolo + stesso
  prezzo_sats su un annuncio ATTIVO nato entro
  `FINESTRA_ANTIDOPPIONE` (30s) = retry, si ritorna l'id già
  esistente senza creare nulla (niente await tra controllo e INSERT:
  nel server mono-processo il blocco è atomico, para anche i submit
  concorrenti). Nel client `publish()` passa da `bottoneInAttesa`
  (bottone spento + overlay fino alla risposta): la causa prima era
  il fetch lento (foto base64 + moderazione AI) col dito che ritocca.
  L'ANNULLO VERO E LE LAPIDI (ago 2026, giro urgente dal campo — tre
  problemi riprodotti prima di toccare). 1) IL QR DEL PAYSHEET ERA
  FINTO: un pattern CSS decorativo che non codificava niente
  (verificato con uno scanner). Ora `mostraQr()` disegna un QR VERO —
  `lightning:<bolt11>` TUTTO MAIUSCOLO, che entra nella modalità
  alfanumerica (codice più rado, più facile da inquadrare: il formato
  dei wallet) — su canvas scuro-su-bianco FISSO nei due temi (il patto
  dell'etichetta prezzo: un codice si legge col contrasto, non col
  tema), zona quieta doppia (padding + 4 moduli nel canvas). Libreria
  `vendor/qrcode.js` (qrcode-generator 1.5.2, MIT) committata a
  versione bloccata e servita da rotta esplicita, MAI CDN — il patto
  di nostr.bundle.js: il QR dice al wallet dove mandare i sats.
  Caricamento pigro alla prima invoice; in DEMO niente QR (la stringa
  è finta, mai un QR bugiardo); in dispensa PWA (sw.js VERSIONE v3).
  Vale per ordini, set e puntate: il paySheet è uno.
  2) L'ANNULLA DEL FOGLIO ANNULLA DAVVERO (`annullaPagamento()`, con
  la conferma «se hai già pagato, NON annullare»); chiusura, velo,
  Esc e gesto indietro NON annullano mai — chi inquadra il QR esce
  verso il wallet e torna. La liturgia server (`annulla_ordine`,
  gemello `annulla_rilancio`): pagamento controllato PRIMA (la
  invoice può essere viva nel wallet, a differenza del reaper che
  agisce a fattura morta), CAS sullo stato, e la riga diventa LAPIDE
  'annullato' — MAI DELETE: un saldo atterrato nella corsa
  annulla-vs-saldo deve avere una riga su cui posarsi. Il RIACCIUFFO
  è `controlla_annullati` nell'orologio: lapide-ordine pagata →
  torna 'creato' (timbro fresco, il reaper non se la mangia) e passa
  da `_incassa_ordine` — chi paga ha comprato, la regola di
  verifica_pagamento (e un avviso ai moderatori); lapide-rilancio
  pagata → binario del fuori-tempo («Da riscuotere»). CONFLITTO
  DICHIARATO (provato in CI e su DB usa-e-getta): se nel frattempo
  l'oggetto e' andato a un altro, il riacciuffo porta COMUNQUE
  l'ordine a locked — lo stock non va mai negativo (il MAX del corner
  del reaper, da cui passa per costruzione), l'annuncio resta
  'venduto', e il doppio escrow e' il caso da moderatore di sempre:
  l'avviso ⚠️ ai moderatori parte proprio per questo. La purga vive
  nel reaper: lapidi-ordine a 1h dall'annullo, lapidi-rilancio con la
  soglia dei rilanci — sempre DOPO che la fattura non può più essere
  pagata. `_incassa_ordine` è il ramo pagato di verifica_pagamento
  ESTRATTO (serve al riacciuffo): CAS 'creato'→'locked', stock,
  offerte, notifiche — non ricontrolla la invoice, il chiamante l'ha
  appena fatto. 3) LA RIPRESA DEL PENTITO in compra(): lo stesso
  compratore che ritenta sullo stesso annuncio NON è un rivale — se
  ha un ordine 'creato' suo con fattura viva (colonna
  `ordini.invoice`, nuova; soglia `RIPRESA_INVOICE_S` 720s) e
  richiesta identica gli si RIPRESENTA la sua (flag `ripresa`, mai
  ordini gemelli); vecchia o richiesta diversa = lapide e rinnovo;
  già pagata = si incassa e 409 «l'oggetto è già tuo». Il messaggio
  d'attesa «qualcun altro sta pagando» resta SOLO per gli altri: è
  l'anti-doppio-acquisto, giusto così. (Il blocco della scelta
  consegna in compra() sta ora PRIMA del fail-fast dello stock: la
  ripresa confronta la scelta.) I set restano fuori dalla ripresa,
  dichiarato.
  E NESSUNA RIGA SI CANCELLA SENZA AVER CHIESTO A LNBITS (ago 2026):
  è l'invariante, ed è la stessa regola delle lapidi arrivata fino in
  fondo. Il reaper buttava via gli ordini 'creato' scaduti con un
  DELETE secco — «nessun sat è coinvolto, è solo pulizia», vero SOLO
  se qualcuno ha guardato, e a guardare c'è un poll che vive nel
  TELEFONO DEL COMPRATORE (`pollTimer`, più il bottone «ho pagato»
  nella lista). Chi paga da un wallet esterno e chiude l'app — o
  Telegram gli uccide la WebView, o cade la rete — lascia una riga mai
  verificata, e il DELETE si portava via il `payment_hash`, cioè
  l'UNICO filo verso quel pagamento: i sats restavano in cassaforte
  senza un ordine, e nemmeno LNbits sa a chi renderli (registra che
  qualcuno ha pagato, non CHI). La finestra è vera e vale fra i 15 e i
  30 minuti: la fattura muore a `INVOICE_EXPIRY` (900s), la riga a
  1800s. `annulla_ordine` la regola la rispettava già; il reaper la
  scavalcava dalla porta di servizio — ed è il modo in cui muoiono le
  regole, non abrogate ma aggirate da un'altra strada.
  MAI SUCCESSO IN PRODUZIONE, e il METODO per dirlo va tenuto perché
  da SQL non si può: le righe cancellate non esistono più, e l'unico
  posto dove il fatto resta scritto è LNbits. Si incrociano i suoi
  incassi (`GET /api/v1/payments`, entrate riuscite) coi
  `payment_hash` noti a `ordini` + `rilanci` — devono combaciare per
  costruzione, `crea_invoice_escrow` è l'unica cosa che emette fatture
  in entrata — e ogni incasso senza riga è un orfano. Il `memo` dice
  quale annuncio (`Barattolo escrow #{id}`), mai chi ha pagato. Fatto
  ad ago 2026: zero orfani, i soli col nostro memo erano sei collaudi
  di luglio.
  IL REAPER NON POTEVA GUARDARE DA SÉ, ed è ciò che ha deciso la
  forma: è SINCRONO e vive dentro `GET /api/orders` (unico chiamante,
  il «reaper pigro»), quindi a LNbits non ci può parlare. Ora lui i
  'creato' non li tocca più — né ordini né rilanci — e a guardarli c'è
  `controlla_abbandonati` nell'orologio, gemella di
  `controlla_annullati` per chi non ha annullato niente: ha pagato ed
  è sparito. Pagata → il flusso di sempre da `_incassa_ordine` col suo
  CAS (se il poll ha vinto un istante prima, rowcount 0 e nessuno
  rinotifica); non pagata → la LAPIDE 'annullato', da cui la purga
  passa un'ora dopo. SOLO A FATTURA MORTA
  (`INVOICE_EXPIRY`/`RILANCIO_EXPIRY`): prima il compratore può ancora
  pagare, e dichiarargli l'ordine annullato sarebbe una bugia oltre
  che una corsa col suo poll — per questo il 900 è diventato un NOME e
  non è più un numero nella firma di `crea_invoice_escrow`, che due
  copie a mano sono due copie da tenere in pari e quella sbagliata
  dichiara annullato un ordine ancora pagabile.
  FAIL-OPEN NEL VERSO GIUSTO: LNbits muto = la riga RESTA 'creato' e
  si riprova al giro dopo, e nessuno la cancella più alle sue spalle.
  Il prezzo dichiarato è che a LNbits giù quelle righe si accumulano
  invece di autopulirsi — meglio una riga che si attarda che un
  pagamento buttato via.
  IL RILANCIO PAGATO NON ENTRA IN GARA, dichiarato: la fattura è
  scaduta da un pezzo e applicare adesso un rilancio vecchio di dieci
  minuti falserebbe una gara che è andata avanti. Prende il binario
  del fuori-tempo di `verifica_rilancio` — i sats nel registro «Da
  riscuotere», la risposta che il progetto dà già a ogni saldo su una
  puntata fuori gara — e chi ha pagato lo viene a sapere.
  DUE CONSEGUENZE: un checkout abbandonato compare come «Annullato»
  negli Ordini per un'ora invece di sparire a 30 minuti (è la riga che
  l'annullo esplicito produce già, col suo «nessun pagamento è stato
  trattenuto»: più onesta di una riga che svanisce); e stock e guardia
  «affare in corso» si liberano PRIMA — verificato che tutti e sei i
  chiamanti di `_ordini_vivi_annuncio` trattano 'annullato' come
  terminale.
  L'IMPERFEZIONE DICHIARATA QUI È STATA CHIUSA (ago 2026): era
  «`_incassa_ordine` non avvisa MAI il compratore», e la cura ipotizzata
  allora — una notifica sul solo ramo dell'orologio — è stata SCARTATA
  in favore della notifica SEMPRE. Vedi «LA RICEVUTA DEL COMPRATORE».
  Nelle prove UNA SENTINELLA HA CAMBIATO LATO — chiedeva che il reaper
  spazzasse anche i 'creato', cioè certificava il buco (il precedente
  è la gemella degli avatar) — e la tortura a nove mutazioni ne ha
  trovata una CHE NON POTEVA FALLIRE: cercava il nome della funzione
  nell'orologio, e un «pass  # await controlla_abbandonati()» la
  lasciava verde con la funzione mai chiamata. Ora chiede la RIGA
  intera. È la lezione da portarsi dietro: una sentinella si scrive
  rompendo il codice, non rileggendola.
  LA RICEVUTA DEL COMPRATORE (ago 2026): chi paga riceve una notifica
  SEMPRE, appena i sats sono in cassaforte. Prima non gli arrivava
  niente dal server — al venditore «Hai venduto», ai moderatori il
  polso 🛒, a chi restava in trattativa il 🕊, e a lui il solo toast
  in-app, che dura tre secondi e non lascia niente da ritrovare. Il
  toast è morto; la notifica resta ed è la ricevuta che ritrova domani
  cercando cosa ha comprato (in DEMO il toast RESTA: lì non c'è nessun
  server che notifichi, ed è l'unico riscontro).
  LA CURA È «SEMPRE» E NON «SOLO DALL'OROLOGIO», ed è la strada
  scartata da tenere: l'imperfezione era dichiarata sul ramo che parte
  dall'orologio (`controlla_abbandonati`, il riacciuffo di
  `controlla_annullati`) perché lì il compratore non è davanti allo
  schermo, e la cura ovvia era un ramo apposta. Notificare SEMPRE
  costa un messaggio in più nel caso normale e in cambio toglie il
  ramo: la ricevuta vive in `_incassa_ordine`, cioè nel FUNNEL da cui
  passano tutte e tre le strade dell'accredito, e ogni strada futura
  la eredita senza che nessuno se ne debba ricordare. Chi la spostasse
  su `verifica_pagamento` rimetterebbe il silenzio esattamente dove
  faceva più male: c'è la sentinella.
  LA CODA DEV'ESSERE QUELLA DELLA STRADA SCELTA, o si dice il falso a
  metà degli ordini — giudice PURO `_coda_ricevuta(consegna, via_punto,
  punto_scritto)`, che prende i campi e non la riga (il patto di
  `in_ferie`) e si tortura in CI. Cinque code: spedizione a casa (il
  tracciamento in arrivo), punto di ritiro (nessun tracciamento da
  aspettare, si aspetta l'avviso che il pacco è arrivato — il gemello
  di `MSG_BUSTA_PRONTA`), ritiro a mano (ci si accorda col venditore),
  codice online, e il ripiego della consegna non dichiarata (gli
  storici e gli importati da Nostr: nessuna promessa su una strada che
  nessuno ha scelto). Più il caso del residuo del quarto giro — via
  punto scelta e punto MAI scritto, cioè gli ordini nati da un client
  di ieri: lì la palla è SUA e la coda glielo chiede, perché senza
  quel testo il venditore non può nemmeno spedire.
  SUL DIGITALE NON SI PROMETTE LA CONFERMA, ed è la riga da non
  ammorbidire: lì le finestre corte scattano DA SOLE
  (`ORE_CONFERMA_DIGITALE` dalla rivelazione, `ORE_SILENZIO_DIGITALE`
  dalla consegna mai letta), quindi «i sats partono quando confermi»
  sarebbe falso — e falso verso chi ha comprato proprio la cosa che
  non torna indietro. La ricevuta dice solo che il contenuto arriva
  dentro Barattolo; il come e il quando li dice la notifica della
  consegna, che arriva col contenuto. C'è la prova che quella coda non
  contiene «conferm».
  Le altre code invece la nominano, e restano vere anche a
  `AUTO_SBLOCCO_ATTIVO` riacceso: dicono «confermalo e i sats vanno a
  lui», mai «SOLO se confermi» — quindi questa notifica NON entra
  nell'elenco dei testi da rimettere il giorno del rientro.
  Il PUNTO DI RITIRO è testo del compratore e al giudice arriva come
  BOOL, mai la stringa: nel messaggio non ci entra per costruzione. Il
  TITOLO invece ci entra, ed è testo del VENDITORE su un tubo HTML: si
  tronca PRIMA e si escapa DOPO, o un «<» spegne la ricevuta in
  silenzio — la lezione dell'avviso di spedizione, sullo stesso tubo.
  Le ASTE restano fuori per costruzione: il vincitore ha già pagato e
  il suo ordine nasce da `crea_ordine_pagato`, che non passa di qui (e
  il 🏆 ce l'ha già).
  IL RITIRO SI CONFERMA DA 'LOCKED' (ago 2026, dal campo: il
  compratore non trovava il bottone). Il server accettava già la
  conferma da locked — mancava nel CLIENT: ora a locked-ritiro il
  compratore ha nota 🤝 e «✅ L'ho ritirato — libera i sats», senza
  aspettare che il venditore segni nulla (rischia solo lui: la
  semantica del deposito; per la spedizione il bottone resta da
  shipped, dichiarato). E il ritiro mai concluso non ha NESSUN timer
  che corre (riprodotto: l'auto-sblocco parte dalle DICHIARAZIONI,
  e lì nessuno ha dichiarato niente — senza dichiarazioni i sats non
  si muovono MAI da soli): la cura è `sollecita_ritiri_fermi`
  nell'orologio — promemoria alle DUE parti (il compratore può
  confermare, il venditore può segnare la consegna e da lì parte la
  finestra di conferma), colonne sue `sollecito_ritiro_il`/
  `solleciti_ritiro` (NON quelle del sollecito incassi: vivono su
  'confirmed' e un contatore ereditato salterebbe al tetto), stesse
  leve SOLLECITO_INCASSO_*, al tetto 🧊 ai moderatori e poi silenzio.
  IL DISARMO DELL'AUTO-SBLOCCO (ago 2026, decisione di Andrea): in
  questa fase **i sats non si muovono MAI senza un gesto umano**. La
  regola precisa — quella da non ammorbidire — è che NESSUN TIMER
  SPOSTA SATS DA UNA PARTE A UN'ALTRA. Leva `AUTO_SBLOCCO_ATTIVO`,
  che nasce FALSE nel CODICE come IMPORT_NOSTR_APERTO e per la stessa
  ragione (muove denaro: si riaccende dal VPS con un gesto, mai per
  effetto di un deploy).
  COSA SI DISARMA: i due rami fisici di `controlla_scadenze` — 72h da
  `consegnato` (delivered) e GIORNI_AUTO_SBLOCCO giorni da
  `spedito_il` (shipped), ritiro in zona compreso, che passa dallo
  stesso ramo. Il caso che ha aperto il cantiere è il secondo:
  l'ancora è la parola del venditore, che la piattaforma NON verifica
  (niente tracking API) — un pacco mai partito e dieci giorni di
  silenzio incassavano. Il primo si disarma per la regola cardinale e
  non per l'asimmetria: `consegnato` lo scrive SOLO il compratore
  (regola ferrea 5), quindi lì l'ancora è sua — ma UN SILENZIO NON È
  UN CONSENSO, e chi tace può aver trovato il problema proprio
  aprendo il pacco.
  COSA RESTA ARMATO, e perché la regola tiene lo stesso: 1) LE
  FINESTRE DEL DIGITALE (ORE_CONFERMA_DIGITALE 24h dalla rivelazione,
  ORE_SILENZIO_DIGITALE 48h dalla consegna mai rivelata) — la prima è
  ancorata a un'AZIONE DEL COMPRATORE registrata da noi, la seconda a
  un FATTO CHE VERIFICHIAMO: il contenuto è nel nostro database,
  consegnato e mai letto. Non è la parola di nessuno. Restano armate
  ANCHE a leva spenta: la leva gatea i soli rami fisici, ed è la cosa
  da ricordare quando si legge il suo nome. 2) I TIMER CHE
  RESTITUISCONO: `chiudi_aste` (i sats erano già in cassaforte dalla
  puntata — la chiusura non li muove, li ASSEGNA), `_paga_rimborso`
  ai perdenti, e il riacciuffo `controlla_annullati` (che raccoglie
  un pagamento già uscito dal wallet del compratore). Disarmarli
  congelerebbe i sats di chi li ha versati e lascerebbe pagamenti
  orfani: si curerebbe un male causandone uno peggiore.
  AL POSTO DELLO SBLOCCO, `sollecita_conferme_ferme` nell'orologio —
  gemella di `sollecita_incassi`, colonne SUE
  (`sollecito_conferma_il`, `solleciti_conferma`: un contatore
  ereditato salterebbe al tetto), gira SOLO a leva spenta perché è il
  SOSTITUTO e non un'aggiunta (a leva accesa il primo squillo
  cadrebbe nello stesso istante dello sblocco). `ORE_CONFERMA` e
  `GIORNI_AUTO_SBLOCCO` non cambiano valore: da «quando partono i
  sats» diventano «quando parte il primo squillo». Poi
  PROMEMORIA_CONFERMA_GIORNI (3) di attesa fra uno e l'altro, e dopo
  PROMEMORIA_CONFERMA_MAX (3) ignorati UNA segnalazione 🧊 ai
  moderatori e poi silenzio — il patto dei solleciti. Leve proprie e
  non SOLLECITO_INCASSO_* (7×4): lì aspetta una persona sola su sats
  già suoi, qui due persone si aspettano a vicenda, e ~35 giorni
  prima che un umano guardi sono troppi. Le ancore sono
  `consegnato`/`spedito_il` e NON `aggiornato` come nei gemelli
  (cambia a ogni transizione e sposterebbe il primo squillo). Il
  promemoria è una NOTIFICA NORMALE che rimanda all'ordine, dove i
  due bottoni (conferma / disputa) ci sono già col loro confirm:
  niente tastiera inline — `notifica()` è multi-canale e non porta
  reply_markup, e il gesto più consequenziale dell'app non deve poter
  partire da un tocco in chat. Il compratore riceve ogni squillo, il
  venditore SOLO IL PRIMO (non ha niente da fare, e ha già il suo
  `sollecita_acquirente` col cap a 24h).
  IL SET E L'ASTA non hanno un solo timer proprio, ed è la parte che
  serve saperlo: le colonne dei tempi vivono SOLO in testata
  (`ordini`), le SELECT di `controlla_scadenze` non toccano mai
  `ordine_righe`, e l'ordine nato dall'asta (`crea_ordine_pagato`)
  ricade nei rami fisici come tutti gli altri. Il disarmo li copre
  per costruzione, senza una riga dedicata. L'unica accortezza è il
  LEFT JOIN su `annunci` nel promemoria (con l'INNER i set,
  annuncio_id=0, sparirebbero), già imparata in `sollecita_incassi`.
  LA STRADA SCARTATA, e va tenuta perché è quella che torna in mente:
  L'AUTO-SBLOCCO CIECO. Ha quasi sbloccato un ordine vero con un
  pacco mai arrivato — l'ordine #28, a 6,4 giorni su 10 il giorno del
  cantiere: mancavano tre giorni e mezzo. L'argomento a favore era
  reale (protegge il venditore da chi sparisce dopo aver ricevuto),
  ma protegge dalla parte sbagliata: senza tracking verificato, chi
  «dichiara» ha sempre ragione. Non riproporlo senza il pezzo che
  manca.
  LA CONSEGUENZA ACCETTATA: un ordine il cui compratore sparisce non
  si chiude più da solo — i sats restano in cassaforte finché un
  moderatore non decide. È il caso che il 🧊 esiste per intercettare,
  ed è il prezzo della regola.
  IL PIANO DI RIENTRO: si rivaluta a volumi più alti, quando il
  numero di casi fermi renderà insostenibile il lavoro dei
  moderatori, e SOLO col tracking verificato via API corrieri (è già
  in backlog) — cioè quando «ho spedito» smetterà di essere una
  dichiarazione di parte e diventerà un fatto. Riaccendere è una riga
  nel config del VPS, ma i TESTI sono scritti sul mondo disarmato e
  vanno rimessi: i posti sono `TEMPI` e la sua tabella in
  miniapp.html, le righe di `view-sicurezza` sui tempi, i pannelli e
  i due confirm dell'ordine, e le due notifiche del server
  (`segna_consegnato` e il testo al venditore di
  `sollecita_ritiri_fermi`). È lo stesso patto della commissione
  sospesa.
  IL TRACCIAMENTO SI CORREGGE, MA NON DAL VENDITORE (ago 2026, caso
  vero dal campo): un venditore compra la spedizione da un
  intermediario (Packlink, Sendcloud) e inserisce il codice
  dell'ORDINE dell'intermediario invece di quello del corriere — che
  spesso gli arriva per email solo DOPO aver consegnato il pacco al
  punto di ritiro. `segna_spedito` filtra su stato='locked', quindi il
  tracciamento si scrive una volta sola e nessuno poteva più
  correggerlo: il compratore restava con un codice che nessun corriere
  conosce. La cura ha TRE gambe, e la terza è quella che decide.
  1) PREVENZIONE: una riga nel form della spedizione E in quello del
  reso (`AVVISO_INTERMEDIARIO`, un posto solo) che lo dice PRIMA.
  2) CONTROLLO DI FORMA, mai bloccante: `FORME_TRACKING` riconosce i
  formati tipici dei corrieri in elenco (Poste S10 o 12-13 cifre, BRT
  10-14, GLS/SDA 9-14, DHL 10-11 o JJD/JVGL, UPS 1Z+16 o 9-18, InPost
  24 cifre; «Altro corriere» e le sentinelle non si controllano mai) e
  a forma storta CHIEDE, non impedisce — primo tocco = avviso, secondo
  tocco sullo STESSO codice = si passa (`trackingDaControllare`,
  `trackingForzato` legato al valore, così correggendolo si
  ricontrolla). È EURISTICA E NON VERIFICA, ed è scritto: nessuno di
  questi codici lo possiamo interrogare, la verifica vera arriverà col
  tracking via API dei corrieri (già in backlog). Meglio una domanda
  in più che una spedizione vera fermata da una regola NOSTRA
  sbagliata: i corrieri cambiano i formati senza avvisarci.
  3) CORREZIONE, `POST /api/admin/orders/{id}/tracking` (`reso=1` per
  quello del reso): SOLO moderatore — decisione di Andrea, un
  tracciamento riscrivibile a piacere non è più una prova in disputa,
  quindi il venditore NON ha nessun bottone. Stati shipped/delivered
  (return_shipped per il reso). NON SI TOCCA `spedito_il`, che è
  l'ANCORA del promemoria di `sollecita_conferme_ferme`: riscriverla
  farebbe ripartire da capo l'attesa del compratore a ogni correzione,
  la stessa trappola già pagata con `aggiornato` in
  `sollecita_venditori_fermi` — e per la stessa ragione non si tocca
  nemmeno lo stato né `aggiornato`, che qui non servono (il quando lo
  dice `tracking_corretto_il`). I CORRIERI-SENTINELLA si rifiutano nei
  DUE VERSI (`CORRIERI_SENTINELLA`: 'Consegna a mano', 'Ritiro in
  zona', 'Consegna digitale', più consegna_scelta ritiro/digitale):
  trasformare un ritiro in una spedizione — o viceversa — a sats già
  in cassaforte cambia la STORIA dell'ordine, non un dato di servizio.
  Colonne `tracking_corretto_il` / `tracking_reso_corretto_il`
  (0 = mai), che escono gratis da `/api/orders` col `o.*` e diventano
  la riga «(tracciamento corretto da un moderatore il …)» visibile a
  ENTRAMBE le parti — in silenzio varrebbe meno, non di più — più
  `registra_moderazione` e la notifica a CHI ASPETTA IL PACCO (il
  compratore sulla spedizione, il VENDITORE sul reso: è lui che
  aspetta indietro l'oggetto).
  E IL MODERATORE DEVE POTERCI ARRIVARE (buco trovato provandolo dal
  vivo, non leggendo il codice): un ordine 'shipped' fra estranei non
  compare in NESSUNA coda — e giustamente, non è un caso da moderare —
  quindi il pannello sarebbe stato irraggiungibile. `/api/orders`
  accetta ora `ordine=N`, solo ai moderatori, che AGGIUNGE quel
  singolo ordine alla lista di sempre senza allargarla (dispute e resi
  restano quelli): si vede l'ordine di cui il venditore ha dato il
  NUMERO, uno alla volta. Il numero glielo dà la riga
  `notaTrackingSbagliato` nel suo ordine — non un bottone, ed è il
  punto — che porta il numero già scritto e il canale del rodaggio
  (`BANNER_TEST_LINK`, quello che c'è già: nessun secondo contatto da
  tenere aggiornato). Ingresso nel Profilo admin, «🛠 Apri un ordine
  per numero»: da lì si apre l'ordine come sempre e la correzione vive
  DENTRO, dove sta il contesto — un posto solo.
  IL MESSAGGIO AI SINGOLI UTENTI (ago 2026, caso vero dal campo: una
  venditrice senza username Telegram né npub scrive «contattami per i
  colori» — e nessuno può scriverle, moderatori compresi):
  `POST /api/admin/utenti/{tg_id}/messaggio` (solo moderatori, 403
  PRIMA di leggere il body) manda UN messaggio via `notifica()` — mai
  il bot diretto: canale preferito e nativi Nostr col DM coperti
  gratis — con l'HTML del testo scappato (la lezione dei promemoria)
  e la riga nel registro moderazione (esito 'messaggio', deciso_da).
  È A SENSO UNICO per costruzione, e va detto DUE volte: il confirm
  del moderatore prima dell'invio e la coda del messaggio al
  destinatario, che indica il canale del rodaggio (`BANNER_TEST_LINK`,
  il contatto che c'è già) come strada per risponderci. UI: «💬 Scrivi
  a un utente» nelle stats admin, sotto «Apri un ordine per numero» —
  la ricerca filtra la lista utenti GIÀ caricata dalle statistiche
  (id esatto, pezzo di nome o @username, codice negozio esatto:
  `u.negozio` è entrato nella SELECT apposta), nessun endpoint di
  ricerca nuovo; negli onclick viaggia SOLO il tg_id numerico, il
  patto del filtro-alfabeto. E LA PREVENZIONE, che vale più dello
  strumento: il giudice client `nonContattabile()` — niente username
  E niente npub dal possesso dimostrato, la STESSA regola dei ponti
  di contatto, quindi i nativi Nostr non lo sono mai — accende la
  riga «🔕 nessuno può scriverti» in DUE posti: sopra Pubblica nel
  form Vendi (il momento in cui ci si mette in vetrina, il pattern
  degli hint contestuali; si rivaluta a ogni ingresso nella vista) e
  nel cassetto Identità del Profilo, dove vivono le due maniglie per
  rimediare (lo username si aggiunge da Telegram, la npub si verifica
  lì sotto). NIENTE dismiss, ed è deliberato: non è un consiglio ma
  uno stato del profilo, e sparisce da solo quando smette di essere
  vero. E CHI PUBBLICA LO STESSO LO SENTE DAL BOT (ago 2026, il passo
  dopo): `avvisa_contatto_mancante` in coda al ramo ATTIVO di
  pubblica() — SUBITO, perché è il momento in cui il problema nasce;
  sul nato in revisione tace, il testo dice «in vetrina» e mentirebbe
  (imperfezione dichiarata: chi debutta in revisione lo riceve alla
  prima pubblicazione diretta). Gemella della campagna spedizioniere:
  timbro `utenti.avvisato_contatto` scritto PRIMA dell'invio (un
  errore di rete può perdere un avviso di cortesia, mai raddoppiarlo),
  UNA volta per utente per sempre — due pubblicazioni = un messaggio
  solo, ed è la prova regina, ESEGUIBILE in prove.py sul pezzo vero
  con sqlite in memoria. Chi poi aggiunge lo username o verifica la
  npub non entra proprio nel ramo; la npub NUDA non basta (è una
  dichiarazione, non una porta). ATTENZIONE al collaudo: le identità
  finte hanno sempre uno username (l'upsert scrive nome.lower()),
  quindi il ramo dal vivo non si innesca da lì — si prova con le
  prove eseguibili, non truccando il database.
  IL VENDITORE CHE NON FA PARTIRE LA MERCE (ago 2026, il buco 1 di
  ieri, chiuso — col suo gemello digitale che non era nemmeno
  dichiarato): un ordine `locked` non ha MAI avuto un timer, quindi il
  venditore che non spedisce (o non consegna il codice) non sentiva
  niente e il compratore non sapeva che `apri_disputa` accetta
  `locked` e che il bottone «⚠️ C'è un problema» è lì. La cura è
  `sollecita_venditori_fermi` nell'orologio, e le tre cose da sapere
  sono queste.
  1) È UNA SORELLA E NON UNA TERZA POPOLAZIONE di
  `sollecita_conferme_ferme`, e la ragione è la guardia: quel buco è
  PREESISTENTE al disarmo, non figlio suo, quindi qui NON si guarda
  `AUTO_SBLOCCO_ATTIVO` — è un'AGGIUNTA, non il sostituto di uno
  sblocco, e riaccendendo la leva col tracking verificato non deve
  riaprirsi in silenzio. Con la sorella lo si ottiene senza toccare
  una riga del codice dei soldi (e senza far ingiallire nessuna delle
  22 sentinelle del disarmo). Poi ogni asse è diverso — stato, ancora,
  colonne — e i destinatari sono INVERTITI: il VENDITORE a ogni
  squillo (è lui che deve agire), il COMPRATORE solo al primo, per
  dirgli che i sats sono fermi e che può aprire una disputa. Al tetto
  il 🧊 ai moderatori col TOTALE e non col netto (qui non si sa ancora
  chi lo prende, e l'esito probabile è il rimborso), poi silenzio.
  2) DUE FINESTRE, UNA PER STRADA, leve proprie:
  `PROMEMORIA_SPEDIZIONE_GIORNI` (5) e `PROMEMORIA_DIGITALE_ORE` (48),
  ognuna a 0 spegne la SUA popolazione. I 5 giorni sono più lunghi di
  qualunque ciclo spedisci-e-segna col weekend in mezzo (pagamento
  venerdì → primo squillo mercoledì: un venditore onesto non lo sente
  quasi mai, e serve anche a chi ha spedito e si è scordato di
  segnarlo) e più corti dei 10 giorni che erano l'orizzonte della
  protezione di ieri. Le 48 ore sono `ORE_SILENZIO_DIGITALE`, l'altra
  finestra di silenzio di quella strada: un codice si manda in minuti.
  Cadenza e tetto sono RIUSATI dalla gemella (`PROMEMORIA_CONFERMA_*`,
  3×3 — è la stessa cadenza per decisione, e un posto solo da cambiare
  batte due da tenere uguali): il 🧊 cade al giorno 14 e all'11.
  Coupling dichiarato e coerente: `PROMEMORIA_CONFERMA_GIORNI = 0`
  spegne TUTTI i promemoria — è la leva del passo, e senza passo non
  si ribussa a nessuno.
  3) L'ANCORA È `creato` E NON `aggiornato`, ed è la trappola da non
  ricalcare: `deposita_invoice` accetta il venditore proprio su
  `locked` e scrive `aggiornato`, quindi copiando il gemello dei
  ritiri il venditore avrebbe potuto rimandare all'infinito il proprio
  promemoria ri-salvando la sua invoice d'incasso — il gesto più a
  portata di mano proprio a chi il promemoria vuole evitare. `creato`
  invece è IMMUTABILE una volta che l'ordine è locked (gli unici
  scrittori sono l'INSERT e la resurrezione di `controlla_annullati`,
  che avviene prima) ed è il pagamento a meno di mezz'ora (vita della
  invoice più la finestra del reaper). Niente colonna nuova per
  questo, niente backfill. Colonne NUOVE invece per il contatore —
  `sollecito_venditore_il`/`solleciti_venditore` —: dicono CHI
  aspettiamo (`_conferma` il compratore, `_venditore` il venditore), e
  un contatore ereditato manderebbe al tetto la popolazione 'shipped'
  del compratore appena l'ordine viene spedito. Da non confondere con
  `ordini.sollecito_il`, che è il contrario: quando il venditore ha
  sollecitato il compratore col suo bottone.
  Il ritiro non ci entra (ha già `sollecita_ritiri_fermi`) e la strada
  non dichiarata nemmeno. LEFT JOIN su `annunci` per i set, la solita
  lezione. IMPERFEZIONE DICHIARATA: il vincitore d'asta che sceglie la
  strada tardi si mangia parte della finestra del suo venditore
  (`scegli_consegna_ordine` muove `aggiornato`, che qui non si
  guarda) — innocuo, è un promemoria e non una penale. Il titolo qui
  passa da `html.escape`: le notifiche sono HTML e un «<» spegnerebbe
  il promemoria in silenzio. (I quattro solleciti fratelli non lo
  facevano ancora — chiuso ad ago 2026, ed erano quindici siti e non
  quattro: vedi «IL TITOLO NUDO NELLE NOTIFICHE».)
  E CHI HA PAGATO PUÒ BUSSARE PRIMA (ago 2026, `sollecita_venditore`,
  `POST /api/orders/{id}/sollecita-venditore`): il promemoria qui
  sopra parte a giorni, e fino ad allora chi aveva pagato guardava un
  ordine fermo senza NESSUNA maniglia in mano. Il bottone non aggiunge
  la funzione — quella c'era già —, aggiunge il PRIMA e l'A COMANDO,
  ed è il gemello speculare di `sollecita_acquirente`: là bussa chi
  vende, qui chi compra.
  I DUE CONTATORI CONVIVONO E NON SI TOCCANO, ed è la decisione da non
  rovesciare: colonne SUE (`sollecito_manuale_il`,
  `solleciti_manuali`, «manuale» come le leve) e l'ancora è `creato`,
  che il bottone non scrive — quindi bussare a mano non sposta di un
  minuto il 🧊 ai moderatori. Il contrario sarebbe il rovescio esatto
  di quel che serve: chi bussa spesso allontanerebbe il momento in cui
  un umano guarda il caso. Il prezzo è che nella stessa giornata
  possono partire un manuale e un automatico — accettato: sono lo
  stesso messaggio nello stesso registro.
  L'ANCORA È `creato` anche qui, per la trappola della gemella:
  `deposita_invoice` accetta il venditore proprio su 'locked' e scrive
  `aggiornato`, quindi con `aggiornato` sarebbe il VENDITORE a
  rimandare all'infinito il promemoria di chi lo aspetta, ri-salvando
  la propria invoice d'incasso.
  IL TETTO È LA METÀ CHE CONTA, o il bottone diventa un modo per
  tempestare qualcuno: `SOLLECITO_MANUALE_ORE` (48) e
  `SOLLECITO_MANUALE_DIGITALE_ORE` (24) dicono da quando si può — mai
  subito —, `SOLLECITO_MANUALE_PAUSA_ORE` (24) ogni quanto si ripete,
  `SOLLECITO_MANUALE_MAX` (3) quante volte in tutto: oltre non c'è più
  niente da dire e la maniglia diventa la disputa, e il 400 lo dice
  con quelle parole. Le due finestre stanno COMODAMENTE prima
  dell'automatico (5 giorni e 48 ore): un venditore che spedisce nel
  fine settimana non sente mai niente, e un codice si manda in minuti
  ma una giornata intera la merita chiunque. A 0 la finestra spegne la
  sua popolazione, MAX a 0 spegne il gesto.
  IL TESTO È UN PROMEMORIA, NON UN RIMPROVERO, e non è cortesia ma la
  verità statistica: chi non ha spedito ha quasi sempre solo avuto una
  giornata storta, e il messaggio lo dice prima di chiedere qualcosa.
  IL RITIRO IN ZONA RESTA FUORI (ha `sollecita_ritiri_fermi`, e lì chi
  ha comprato può già confermare da solo). LA VIA NON DICHIARATA NO,
  ed è una correzione dal campo (ago 2026): il bottone non compariva
  su ordini pagati da settimane, e il discriminante era `consegna_
  scelta=''` — gli STORICI e quelli nati da un annuncio importato da
  Nostr. La regola l'aveva ereditata dal promemoria automatico col
  motivo «lì il venditore non può agire», che però vale per UNA sola
  delle tre cose che quel vuoto raccoglie: `segna_spedito` rifiuta la
  via vuota SOLO se l'annuncio è all'ASTA e il vincitore non ha ancora
  scelto — sugli altri il venditore spedisce eccome, e il suo pannello
  «Spedisci» è lì.
  QUINDI SI FA LA STESSA IDENTICA DOMANDA di `segna_spedito` (la
  lettura di `asta_base_sats`), e c'è la prova che la facciano
  entrambe: due strade che rispondono diverso sulla stessa condizione
  sono una che promette quel che l'altra nega. Sull'asta in attesa il
  400 NON è quello anti-oracolo — l'ordine è suo, e la cosa utile da
  dirgli è che la palla è sua: «prima scegli come vuoi riceverlo».
  ASIMMETRIA DICHIARATA con l'automatico, che la via vuota continua a
  NON guardarla: estenderlo è un'altra decisione, e ha un costo che si
  vede solo al primo giro — squillerebbe in un colpo su ogni ordine
  storico fermo in 'locked' da mesi, compresi quelli di cui nessuno si
  ricorda più. Il bottone no: parte solo se qualcuno lo tocca.
  La guardia di proprietà sta DENTRO la WHERE col 400 dei
  fratelli, e c'è la prova che venditore, estraneo e ordine
  inesistente ricevano la STESSA risposta: chi enumera non impara
  niente. Lato client il giudice è `puoiSollecitareVenditore` e le
  quattro leve si ripetono a mano in `SOLLECITO`, col patto di `TEMPI`
  — chi le cambia nel config le cambia anche lì; il server resta
  comunque il giudice. Col sedicesimo sito il censimento dei titoli
  scappati sale a sedici funzioni.
  LA PAUSA E IL TETTO SONO DELL'ORDINE, MAI DELLA PERSONA (ago 2026,
  segnalato dal campo): sollecitare un venditore non deve zittire il
  bottone su un ordine diverso. Vale per costruzione — i due timbri
  sono COLONNE della riga e l'UPDATE è `WHERE id=?` — ma «per
  costruzione» non è una garanzia finché non c'è una prova che lo
  dica: adesso ce n'è una ESEGUIBILE, due ordini di fila sul pezzo
  vero, e la stessa per il bottone GEMELLO del venditore (due
  compratori diversi). La mutazione che sposta il timbro sulla persona
  fa rosse quattro righe.
  IL BOTTONE SPENTO RESTA IN PAGINA E DICE PERCHÉ (ago 2026, dal
  campo — è sembrato un guasto proprio a chi l'aveva appena usato):
  il giudice `statoSollecito` ha TRE esiti e non due — '' non c'è,
  'ok' si può bussare, e in mezzo 'pausa' e 'tetto', che sono il
  bottone spento con «Già ricordato oggi — potrai rifarlo domani» e
  «Hai già ricordato N volte» al posto dell'etichetta.
  MA «È ANCORA PRESTO» RESTA IL NIENTE, ed è la riga da non
  uniformare: prima delle 48 ore non è ancora il momento di bussare, e
  un bottone spento lì sarebbe un invito a farlo appena si accende —
  trasformerebbe un'attesa normale in un conto alla rovescia. Sparire
  è sbagliato solo DOPO che il bottone c'è stato.
  Da spento NON ha un onclick (non basta `disabled` per dormire
  tranquilli) e il numero del tetto viene dalla leva.
  E LA FINESTRA SI SCRIVE COL NOT DELLA FORMA POSITIVA
  (`if (!(o.creato + ore*3600 <= adesso))`), che non è un vezzo: in
  DEMO gli ordini finti non hanno `creato`, la somma fa NaN e ogni
  confronto è falso — così NaN cade sul ramo «non c'è» invece che su
  'ok'. C'è la prova, e la mutazione che rimette la forma diretta la
  fa rossa.
  E IL DOPPIO TOCCO NON MANDA DUE PROMEMORIA: finché la risposta è per
  strada il bottone è spento. Senza, su rete lenta il secondo tocco
  prende il 400 della pausa — «hai già mandato un promemoria nelle
  ultime 24 ore» — che è la stessa frase che si leggerebbe se il tetto
  fosse davvero per persona: il difetto vero e quello immaginato si
  raccontano identici, ed è la ragione per cui questa riga vale più
  della comodità che sembra. Il gemello del venditore aveva la stessa
  finestra aperta e si è chiusa insieme.
  Il client scrive il conto sulla riga di `orders` e non su
  `currentOrder`, che può essere un oggetto DETACHED se nel frattempo
  la lista si è ricaricata.
  E DOPO IL 🧊 C'È UNA CODA (ago 2026): ogni sollecito bussa N volte,
  manda UNA segnalazione ai moderatori e poi tace per sempre — e quel
  🧊 era un messaggio Telegram e basta. Da lì in poi un ordine coi sats
  in cassaforte non compariva in NESSUNA lista del pannello e si
  raggiungeva solo sapendone il numero (`/api/orders?ordine=N` mostra
  ai moderatori i soli `dispute`/`return_*`/`refund`). `GET
  /api/admin/fermi` + sezione «⏸ Ordini fermi» nel Profilo admin, fra
  i pagamenti incerti e la revisione: aperta, perché aspetta una
  decisione.
  LA REGOLA È UNA FRASE — «i sats sono in cassaforte e nessuno si
  muove da CODA_FERMI_GIORNI giorni» — cioè il COMPLEMENTO dei
  terminali (`stato NOT IN ('creato','released','refunded',
  'annullato')`) e NON l'elenco degli invisibili. Si dice ad alta voce
  senza andare a leggere la WHERE di `miei_ordini`, e se un domani
  qualcuno restringe la lista dei moderatori la coda non sviluppa un
  buco in silenzio. Ci entrano anche `refund` — sats dovuti al
  COMPRATORE e ZERO solleciti, buco già dichiarato in
  `sollecita_rimborsi_puntate` — e le dispute, che i moderatori vedono
  già ma in una lista NON ordinata per attesa: una disputa aperta da
  quaranta giorni si confonde con una di ieri. `creato` resta fuori: lì
  i sats non sono ancora in cassaforte, e se ne occupa
  `controlla_abbandonati`.
  DIECI GIORNI, ed è l'invariante che si compra: precedono TUTTI e sei
  i 🧊 con le leve di serie (spedizione g.14, digitale g.11, ritiro
  g.35, conferme g.12 da 'delivered' e g.19 da 'shipped', busta g.12,
  incassi g.35), quindi **se il 🧊 è partito, la riga c'è** — la coda
  non può mai essere più povera delle notifiche già mandate. Dipende
  dalle leve, quindi NON ce lo si ricorda: una prova in CI rifà il
  conto dai default del codice e diventa rossa se qualcuno stringe un
  passo (`PROMEMORIA_DIGITALE_ORE` a 24 la fa rossa). `ORE_CONFERMA` e
  `GIORNI_AUTO_SBLOCCO` vivono solo nel config e restano fuori dal
  conto: dichiarato, non dimenticato. Il contatore esaurito
  (`solleciti_* > MAX`) è stato valutato e SCARTATO — sembra gratis
  perché non ha numeri da tarare, ma è cieco proprio sulla popolazione
  che ha motivato il cantiere (chi non ha un sollecito non ha un
  contatore), si spegne insieme alle leve, e sono cinque rami invece
  di una frase.
  LE ANCORE sono una per stato e la regola che le governa è che
  ognuna finisce in `COALESCE(..., 0)` e NESSUNA guardia «> 0» entra
  nella WHERE: in SQLite «NULL < x» vale NULL, quindi un'ancora vuota
  non darebbe un falso allarme — **farebbe sparire l'ordine dalla coda
  degli ordini spariti**, che è il solo modo in cui questa funzione può
  fallire davvero. Uno zero fa comparire la riga in CIMA, e le catene
  di ripiego vanno all'indietro nel tempo per la stessa ragione. NON È
  TEORICO, ed è la scoperta del cantiere: `ordini.creato` è dichiarato
  senza NOT NULL e senza DEFAULT, e uno `shipped` con `spedito_il=0`
  oggi non riceve nessun promemoria e nessun 🧊 — le due funzioni che
  lo guardano hanno proprio quel «> 0», ed è la sorella mai nominata
  del `locked` con `consegna_scelta=''`. `locked` si ancora a `creato`
  e MAI ad `aggiornato`: lì scrivono `aggiornato` sia
  `deposita_invoice` sia `scegli_consegna_ordine`, quindi il venditore
  potrebbe tenersi fuori dalla coda da solo ri-salvando la propria
  invoice d'incasso (la trappola già pagata in
  `sollecita_venditori_fermi`). IMPERFEZIONE DICHIARATA su
  `confirmed`, ereditata da `sollecita_incassi`: lì `aggiornato` è
  l'ultimo tentativo di pagamento fallito, quindi chi ri-deposita ogni
  settimana una invoice che non paga rimanda il proprio ingresso — si
  tiene lo stesso, così coda e sollecito restano d'accordo su «da
  quando aspetta» invece di litigare, e il contatore nella riga lo
  tradisce comunque.
  LA RIGA dice il totale in cassaforte (su un ordine fermo non si sa
  chi lo prende: la scelta già motivata nel 🧊), lo stato e la strada
  (`''` non è un vuoto ma LA DIAGNOSI: asta senza scelta, o ordine
  storico), da quanti giorni, e due cose che cambiano la decisione di
  chi guarda: **quante volte la macchina ha bussato** — a zero, «🔕 mai
  sollecitato», che è il caso scoperto e dev'essere il più rumoroso —
  e **se le due parti sono raggiungibili** (la regola di `notifica()`:
  Telegram col tg_id positivo, Nostr solo da chiave del possesso
  dimostrato; un nativo che ha perso la chiave non lo sente nessuno, e
  `notifica()` è fail-open, quindi senza quel campo il moderatore lo
  scopre scrivendo nel vuoto). I badge sono SOLO navigazione —
  «Apri l'ordine» riusa `apriOrdinePerId`, che guadagna un argomento
  facoltativo così il gesto per aprire un ordine resta UNO, e «✉️»
  riusa `scegliUtenteAdmin` — perché ciò che AGISCE vive dentro
  l'ordine, dove c'è il contesto.
  NIENTE PALLINO (`aggiornaAdmDot` riceve ancora solo `in_revisione`,
  e nemmeno i pagamenti incerti lo accendono): una coda che può restare
  piena per settimane accenderebbe un cartello sempre acceso, e un
  cartello sempre acceso non lo guarda nessuno. NIENTE LIMIT sul
  server: una coda che tronca nasconde le righe più VECCHIE, cioè
  proprio quelle per cui esiste, e il numero totale è esso stesso
  l'informazione — a tenere corta la pagina c'è il tetto di 8 col
  «mostra i più vecchi», che ridisegna la SOLA sezione (il pattern di
  `apriTuttiCat`: rifare le cinque fetch per allungare una lista già in
  memoria chiuderebbe pure i cassetti aperti). NIENTE archiviazione:
  quelli sono sats di qualcuno, ogni stato non terminale ha una strada
  d'uscita in mano a una persona, e un «archivia» sarebbe l'unico modo
  di rendere un ordine invisibile DUE volte. LEGGE E BASTA, come
  `controlla_libro_mastro`, e la prova non è una sentinella sulla
  forma: il dump di `ordini` prima e dopo dev'essere identico.
  E CHI HA PAGATO SE LO SENTE DIRE SEMPRE, non una volta sola: il
  compratore riceveva UNA notifica al primo squillo automatico e, se
  non la leggeva, nessuno gli ripeteva che i suoi sats erano fermi e
  che la disputa è aperta dal primo minuto. La cura è una RIGA
  nell'ordine (`notaFermo`) e non una ripetizione, ed è una decisione:
  una notifica in più chiude solo la metà di chi legge Telegram in quel
  momento, mentre la riga c'è per chi apre al giorno 2, al giorno 40 —
  quando i promemoria hanno smesso — e per chi la notifica non l'ha
  mai vista; e messaggi identici che non chiedono NESSUN gesto sono la
  famiglia che fa bloccare il bot, col quale si perdono le notifiche
  degli ordini, che sono portanti. Sta sopra i due bottoni che c'erano
  già, così si legge come una storia sola: il fatto → la maniglia
  gentile (🔔) → l'uscita (⚠️).
  È SCRITTA PER RESTARE VERA PER SEMPRE: niente «glielo stiamo
  ricordando», che al tetto dei promemoria diventerebbe una bugia, e
  «nessun timer li muove» regge anche a `AUTO_SBLOCCO_ATTIVO`
  riacceso, perché su `locked` non è mai esistito nessun timer. NON è
  un riuso di `statoSollecito`, che ha due esclusioni sbagliate qui —
  il tetto raggiunto (la riga non è il bottone) e la leva a zero (una
  leva che spegne il promemoria non deve spegnere le PAROLE) — ma ne
  condivide la FINESTRA (48h, 24h sul digitale), così la riga e la
  maniglia gentile arrivano insieme: prima di allora un ordine che
  aspetta è normale e non va fatto sembrare un problema. Fuori il
  ritiro (ha già la sua nota verde e lì si conferma da soli) e l'asta
  senza strada scelta (lì la palla è del compratore). La finestra col
  NOT della forma positiva, per il NaN della DEMO.
  AMBRA E NON ROSSO (guardata a schermo): `--warn-bg` nell'ordine è il
  registro di «disputa aperta», e qui non c'è ancora nessun problema
  conclamato — c'è un venditore in ritardo. Si usa la coppia
  `--sats-soft`/`--sats-text` già in uso due righe più giù, e il rosso
  resta al bottone sotto, che è l'uscita: verde (al sicuro) → ambra (in
  ritardo) → rosso (via d'uscita).
  IL CASO INCAGLIATO ERA UN VICOLO CIECO (ago 2026, chiuso qui perché
  la coda ce lo porta davanti): `risolvi_disputa` accetta
  `confirmed`/`refund` con `disputata=1` — è la cura della «disputa
  decisa che resta in mano al moderatore» — ma nel client il pannello
  «⚖️ Decisione del moderatore» compariva SOLO su `s==='dispute'`.
  Quindi il caso era decidibile dal server e non offerto dal client:
  un buco latente che la coda avrebbe trasformato in una riga su cui
  non si può fare niente. Ora la condizione guarda anche `disputata`
  (che entra in `mapOrder`) e il testo dice cos'è successo — «era stata
  decisa, ma il pagamento non è riuscito» — invece di ripetere quello
  della disputa fresca.
  DUE LEZIONI DEL CANTIERE, e sono di metodo. 1) Il testo della riga
  diceva «non si sbloccano da soli» e ha fatto scattare una sentinella
  del DISARMO, che vieta la stringa «si sbloccano da soli» in tutto il
  client: la conteneva NELLA NEGAZIONE. La sentinella non si è
  allentata per far passare della prosa nuova — è così che muoiono le
  regole, aggirate da un'altra strada — e la frase è diventata quella
  della regola cardinale, «nessun timer li muove». 2) La tortura a 21
  mutazioni (una per riga sorvegliata: terminali rimessi dentro, ancora
  spostata su `aggiornato`, COALESCE tolto, guardia «> 0» rimessa,
  ORDER BY rovesciato, LEFT JOIN secco, leva che non spegne, guardia
  admin caduta, UPDATE infilato nella coda, soglia alzata a 12, riga
  del compratore tolta, forma diretta rimessa, pallino che impara la
  coda, pannello del moderatore tornato indietro…) ha trovato DUE
  SENTINELLE CHE NON POTEVANO FALLIRE, tutte e due mie: una regex che
  si fermava alla prima parentesi e quindi non vedeva
  `aggiornaAdmDot((s.in_revisione||0)+fermi.length)`, e un confronto
  fra due giri della STESSA query, cioè una tautologia. Zero
  sopravvissute solo dopo averle riscritte.
  LO STESSO «<» SPEGNEVA L'AVVISO DELLA SPEDIZIONE (ago 2026, B6
  dell'audit, chiuso): corriere e tracciamento sono testo di CHI
  SPEDISCE e finivano nudi nell'HTML — un «Bartolini <BRT>», che uno
  scrive senza pensarci, faceva fallire il parse di Telegram e il
  compratore non riceveva l'avviso, senza errore e senza traccia. Ora
  passano da `html.escape` in tutti e tre i rami di `segna_spedito` e
  nel gemello `reso_spedito`, dove ad aspettare è il venditore e c'è
  un rimborso di mezzo. SI SCAPPA AL MOMENTO DELL'AVVISO E MAI A
  MONTE, ed è la riga da non ammorbidire: nel database, e nel
  confronto coi CORRIERI-SENTINELLA ('Ritiro in zona', 'Consegna a
  mano'), il testo deve restare quello che è stato scritto — è anche
  una prova in disputa, e il client ha già il suo `esc()`. Le prove
  sono ESEGUIBILI e guardano che i `<b>` restino PARI, che è quel che
  Telegram controlla prima di rifiutare l'invio, più il rovescio (nel
  database il testo arriva intero e le sentinelle matchano ancora).
  BUCHI PREESISTENTI, dichiarati e NON chiusi: 1) ordine d'asta con
  `consegna_scelta=''` mai scelta — non squilla da nessuna parte
  (`sollecita_ritiri_fermi` filtra 'ritiro',
  `sollecita_venditori_fermi` filtra le due strade esplicite: lì il
  venditore non può agire, e sarebbe un rimprovero a vuoto); 2) ordini
  fermi in 'refund', già noto nella docstring di
  `sollecita_rimborsi_puntate`.
  IL TITOLO NUDO NELLE NOTIFICHE (ago 2026, il resto della famiglia di
  B6): B6 aveva chiuso i due rami della spedizione, ma il TITOLO — che
  è testo del venditore e passa dallo stesso tubo HTML — restava nudo
  quasi ovunque. Il conto vero è **quindici siti**, non i «quattro
  solleciti fratelli» che questo file dichiarava: il polso 🛒 ai
  moderatori, quattro solleciti su sei, e altri otto che solo un
  censimento ha tirato fuori (`_sblocca_sats`, `_rimborsa_compratore`,
  `_racconta_chiusura`, `verifica_rilancio`, `rispondi_offerta`,
  `scadenze_offerte`, `annulla_asta_admin`, `_paga_rimborso`). LA
  LEZIONE DEL GIRO è quella: l'elenco a memoria di un buco dichiarato
  invecchia e RIMPICCIOLISCE — a contare dev'essere una prova che
  guarda il file, non una riga di CLAUDE.md.
  IL PIÙ GRAVE ERA `_paga_rimborso`, e vale la pena saperlo: quel
  titolo finisce nel 🧊 di `_congela_pagamento`, cioè l'avviso di un
  pagamento INCERTO — quello che questo file dichiara non debba MAI
  sparire, perché dice che dei sats possono essere usciti davvero.
  LA REGOLA È UNA SOLA: si scappa ALL'ASSEGNAZIONE, una volta, e da lì
  lo stesso valore serve le notifiche e il polso. LA STRADA SCARTATA,
  scritta e poi tolta, va tenuta perché è quella che torna in mente:
  l'escape DENTRO `polso_ordini_admin`, col segnaposto `{titolo}`
  accanto a `{aperti}` — «un posto solo, e il sesto chiamante non può
  dimenticarlo». Non regge: `_sblocca_sats` e `_rimborsa_compratore`
  usano la STESSA variabile per le loro notifiche E per il polso,
  quindi quella variabile vivrebbe in due regimi (grezza per uno,
  scappata per gli altri) e il primo che li confonde scrive «&amp;lt;»
  dentro un avviso. Il polso quindi NON scappa, e c'è la prova che non
  lo faccia: un doppio escape non si vede finché qualcuno non legge un
  titolo storto.
  IL ROVESCIO — dove NON si scappa — è la metà che si dimentica, e qui
  ha un caso vero: in `_compra_set` il nome del pezzo esaurito va nel
  `detail` di un 404, cioè JSON che il client rende col SUO `esc()`;
  un `html.escape` lì farebbe leggere «Cuffie &lt;b&gt;AKG&lt;/b&gt;»
  a chi compra. La variabile si chiama `nome_pezzo` APPOSTA: così il
  censimento non la pesca e chi legge vede subito che è un'altra cosa.
  Stessa ragione per cui i tag NIP-99 continuano a portare il titolo
  grezzo (lì è protocollo, non prosa).
  E IL RIPIEGO «or …» NON È COSMESI: in `sollecita_incassi` il titolo
  si assegnava senza, e quella riga sta FUORI dal `try` — un titolo
  NULL non avrebbe saltato un promemoria, avrebbe ammazzato il giro per
  tutti quelli dopo. Oggi è irraggiungibile (nessun `DELETE FROM
  annunci` esiste), ma i quattro fratelli ora hanno la stessa forma.
  L'ULTIMA RETE È IN FONDO AL TUBO (`_manda_telegram`), e non
  sostituisce l'escape alla fonte: è quel che salva il sito che
  qualcuno scriverà l'anno prossimo. LA RISPOSTA DI TELEGRAM NON LA
  GUARDAVA NESSUNO — un `await c.post(...)` e via — ed è la parte
  LETTERALE di «senza errore e senza traccia»: il 400 «can't parse
  entities» finiva nel nulla. Ora su un rifiuto del PARSE (e solo su
  quello: bot bloccato, chat inesistente e 429 non li ripara un
  secondo invio) il messaggio si rimanda SPOGLIO — `spoglia_html`, lo
  stesso ripiego dei DM Nostr — così arriva senza grassetti invece di
  non arrivare. E si STAMPA, o sarebbe un guasto che si autoripara in
  silenzio e nessuno andrebbe mai a scappare il sito che l'ha causato.
  LA PROVA CHE CONTA È IL CENSIMENTO, non un elenco: guarda tutte le
  funzioni del file, tiene quelle che notificano e chiede che ogni
  `titolo = …` nasca scappato — così il sollecito nuovo di domani entra
  nel conto da solo. Accanto, la prova che il censimento VEDE davvero
  le quindici funzioni: a predicato rotto, uno «zero scoperti»
  sembrerebbe una promozione invece che una cecità.
  E UNA SENTINELLA NON POTEVA FALLIRE, per la seconda volta in due
  giorni: «il ripiego stampa» cercava `print(` in tutta la funzione, e
  il `print` del collaudo dieci righe più su la teneva verde anche
  togliendo quello del ripiego. L'ha smascherata la tortura (0 rosse
  su una mutazione che doveva farne una); ora guarda DENTRO il ramo.
  I TIMBRI DEGLI AVVISI PERIODICI (ago 2026, caso dal campo: il
  termometro arrivato TRE volte in cinquanta minuti — 12:35, 13:04,
  13:25 — agli orari dei tre deploy di quel lunedì). «Ogni lunedì»,
  «una al giorno»: promesse che valgono solo se il timbro sopravvive a
  un riavvio, e i tre timbri vivevano in GLOBALI. Un globale muore col
  processo, quindi non erano gate: erano dedupliche valide quanto il
  processo, e su una macchina dove si deploya tre volte in un'ora
  quella garanzia vale zero. Tabella `timbri` (nome, valore, quando) +
  `timbro_letto`/`timbro_scrivi`, e i tre chiamanti sono
  `termometro_sottocategorie`, `sollecita_revisioni` e
  `controlla_libro_mastro`.
  IL PEGGIORE ERA `sollecita_revisioni`, non quello che si è visto: il
  suo gate era `adesso - _ultimo < 86400` contato da un globale — cioè
  ESATTAMENTE l'antipattern che la docstring del termometro additava,
  tre funzioni più giù — e lì manca perfino il gate del calendario,
  quindi bastavano due deploy a un minuto di distanza. Si è visto
  quello del termometro solo perché il lunedì li concentra.
  FAIL-OPEN NEL VERSO DEL PARLARE: se la lettura non riesce si
  risponde «mai timbrato», cioè l'avviso PARTE. Fra un doppione e un
  allarme che non arriva si sceglie il doppione — un timbro
  illeggibile non deve poter zittire per sempre una segnalazione — e
  la scrittura che fallisce non alza: il giro dell'orologio non si
  ferma per un timbro (il prezzo è che quell'avviso può ripetersi).
  IL TIMBRO NON SI SCRIVE SE NON SI PARLA, ed è la riga che si sbaglia
  per prima: nel termometro si esce PRIMA di timbrare quando la coda è
  sotto il minimo, o una settimana silenziosa brucerebbe il turno e il
  lunedì dopo non ricontrollerebbe. Quando invece si parla, il timbro
  va PRIMA dell'invio: il patto delle campagne — un errore di rete può
  perdere un avviso di cortesia, mai raddoppiarlo.
  E OGNUNO LASCIA UNA RIGA NEL JOURNAL quando manda (il secondo
  difetto del caso dal campo: l'invio non si trovava né su 24 ore né
  su tre giorni, quindi un avviso che parte troppo non si poteva
  nemmeno diagnosticare). La riga sta PRIMA della notifica e c'è la
  prova che ci resti.
  GLI ALTRI QUATTRO GATE IN RAM RESTANO, e il perché è la parte da non
  rovesciare: `_ultimo_giro_iscritti` non è un gate ma un FILO
  DELL'ACQUA — al riavvio ARMA e basta, cioè salta un battito invece
  di rifare una raffica: sbaglia già nel verso giusto. Gli altri tre
  (`_prossimo_import_nostr`, `_prossima_scoperta_nostr`,
  `_prossimo_rinfresco_nostr`) programmano LAVORO e non avvisi: un
  riavvio li fa partire prima, e il lavoro è idempotente — il
  benvenuto della scoperta è gated da un fatto del database
  (`crea_utente_nostr` gira solo se la riga non c'è), i suggerimenti
  dal timbro `suggerito_il`. Chi aggiunge un avviso PERIODICO invece
  usi `timbri`: c'è la prova che i tre non tornino a un globale.
  LA PROVA È ESEGUIBILE e non una sentinella: fa girare la funzione
  vera tre volte su tre AMBIENTI diversi con lo stesso database sotto
  — che è cosa succede a tre deploy — e chiede UNA notifica sola. Una
  sentinella sulla forma non basterebbe: qui il difetto non era una
  riga mancante, era uno stato che non sopravviveva.
  Categorie (lug 2026): catalogo unico `CATEGORIE` in server.py, 27
  voci — le 9 di sempre (Elettronica · Casa e giardino ·
  Abbigliamento · Sport e hobby · Motori · Bambini · Animali · Libri e
  media · Altro) più le 16 del catalogo largo (Informatica ·
  Telefonia · Audio e video · Console e videogiochi · Foto e ottica ·
  Bitcoin · Elettrodomestici · Fai da te e utensili · Alimenti e
  bevande · Scarpe e accessori · Orologi e gioielli · Biciclette ·
  Musica e film · Strumenti musicali · Collezionismo · Arte e
  artigianato), più «Bellezza e benessere» (lug 2026, 🧴): cosmetici,
  creme, profumi, saponi, oli essenziali, integratori e cura della
  persona, che prima si spartivano fra «Alimenti e bevande» (le
  tisane, gli integratori) e «Altro», e nessuna delle due era giusta.
  È la seconda voce delle CATEGORIE_SENZA_CONDIZIONE, per la stessa
  ragione degli alimenti (vedi sotto).
  Più «Buoni ed esperienze» (ago 2026, 🎟️ — il biglietto dice il
  reparto, il 🎁 direbbe un'occasione): gift card, buoni acquisto,
  voucher per soggiorni e cene — i due annunci veri che morivano in
  «Altro» (il pacchetto B&B, i buoni Zalando). È una famiglia di
  MERCE, non un modo di consegnare: la strada «Prodotti digitali» è
  stata valutata e scartata perché avrebbe detto il COME invece del
  COSA — i buoni Zalando veri hanno consegna=entrambe, la tessera si
  SPEDISCE, e una categoria «Digitale» con spedizione fisica è una
  contraddizione in vetrina. Ortogonale per costruzione al filtro
  «💾 Codice online»: la categoria dice cosa compri, il filtro come
  arriva. I SERVIZI restano fuori (decisione presa: un buono per una
  notte è una cosa che esiste, «ti sviluppo un bot» no) e la
  moderazione non cambia — i buoni riscattabili presso il venditore
  stesso restano DUBBIO. Terza voce delle CATEGORIE_SENZA_CONDIZIONE:
  un buono è nuovo per definizione, anche la tessera fisica. Le due
  righe-voucher del MODELLO_IMPORT traslocano lì e perdono la cella
  condizione (insegnerebbe una cosa falsa, la regola del miele).
  "Tutto" è solo la vista del
  frontend, non una categoria. «Bitcoin» è l'unica di casa nostra e non dei mercatini
  generalisti: su un mercatino che incassa in sats, Jade e BitBox02
  sono merce di casa. In vetrina il catalogo resta PIATTO, ma dal
  (ago 2026) l'albero delle SOTTOCATEGORIE esiste DORMIENTE nel
  codice — vedi la voce sua, più sotto.
  SI AGGIUNGE, NON SI RINOMINA (lug 2026, decisione di Andrea, ed è la
  regola da non rovesciare): le voci esistenti restano tutte con lo
  stesso nome. Il cantiere del catalogo largo proponeva di rinominarne
  tre (Casa e arredamento, Sport, Libri e riviste) con la sua
  migrazione; è stato scartato perché quei tre non erano voci nuove ma
  nomi nuovi per voci esistenti, e due nomi per la stessa cosa non
  sono più scelta ma un bivio senza risposta giusta davanti a chi
  pubblica. Conseguenza: NESSUNA migrazione di categoria da scrivere —
  nessun annuncio cambia casella, nessun venditore ritrova il suo
  oggetto dove non l'ha messo. Per la stessa ragione il fai-da-te è
  entrato come «Fai da te e utensili» e non «Giardino e fai da te»: il
  giardino ce l'ha già Casa e giardino.
  `categoria_valida`
  normalizza i payload (sconosciuta → Altro: il client non decide il
  catalogo); resta solo la migrazione VECCHIA in `init_db` (Sport →
  Sport e hobby ecc. con COLLATE NOCASE, che raddrizza le maiuscole
  storte dei vecchi import, 'casa'). La lista entra nel
  prompt della ricerca AI; nel NIP-99 il tag `t` è la prima parola
  minuscola ("Casa e giardino" → "casa": un hashtag non ha spazi).
  LE ICONE (`EMOJI_CAT` nel client) dicono il REPARTO, non un
  prodotto: 🍳 Elettrodomestici (il cesto 🧺 e' dove finisce il bucato,
  non un elettrodomestico), 🍎 Alimenti e bevande (il vasetto 🍯 diceva
  un prodotto solo, e per giunta somiglia al 🫙 dei preferiti, che non
  deve avere sosia), 🚗 Motori (lo scooter e' un pezzo del reparto),
  🏡 Casa e giardino (la sedia ne diceva meta'), 🧴 Bellezza e
  benessere (il flacone e' il ripiano intero — creme, oli, saponi,
  shampoo —, mentre il rossetto 💄 direbbe il solo trucco e lascerebbe
  fuori integratori e saponi, e il sapone 🧼 e' un prodotto solo).
  ₿ Bitcoin resta un
  glifo di TESTO e non un'emoji a colori — nel foglio stona un po'
  con le vicine, ed e' voluto: il simbolo vince sull'uniformita'.
  Guardate e tenute come sono: 🏺 Collezionismo (tira
  sull'antiquariato, ma non c'e' di meglio) e 📦 Altro (e' anche il
  pacco della spedizione: convivono senza confondersi).
  AGGIUNGERE UNA CATEGORIA TOCCA SETTE POSTI: `CATEGORIE` e
  `SINONIMI_CATEGORIA` e `MODELLO_IMPORT` in server.py, `<select
  id="sellCat">` e `EMOJI_CAT` e `CATS` in miniapp.html, più
  l'ILLUSTRAZIONE in `assets/categorie/{slug}.webp` (il settimo, lug
  2026, nato con la pagina Sfoglia) — e `CATEGORIE_SENZA_CONDIZIONE`
  col suo gemello `CAT_SENZA_COND`, se la voce nuova è di quelle dove
  la condizione non vuol dire niente.
  Non serve
  ricordarseli: `prove.py` li incrocia tutti e sette e fallisce se
  divergono (il sesto, il modello CSV, è entrato dopo essersi fatto
  dimenticare per davvero).
  L'ALBERO DELLE SOTTOCATEGORIE (ago 2026): definito ora, mostrato
  MAI — catalogo `SOTTOCATEGORIE` in server.py (86 sottovoci su 26
  categorie, disegnato sui 46 annunci veri di produzione), DORMIENTE:
  niente form, niente filtri, niente Sfoglia finché non si deciderà
  di accenderlo. Il patto, scritto anche nel commento del catalogo:
  id kebab-case PER SEMPRE e unici in TUTTO l'albero (un filtro senza
  categoria non dev'essere ambiguo), etichette ritoccabili senza
  migrazioni (pattern CONDIZIONI), ordine delle tuple = ordine di
  presentazione, SI AGGIUNGE NON SI RINOMINA anche qui, NIENTE voci
  «Altro X» (il fallback è '', un secondo cimitero per categoria
  sarebbe il vizio di «Altro» moltiplicato per ventisei), chiave
  assente = categoria piatta (oggi solo «Altro», per forza: «Altro»
  con sottovoci non è più «Altro»), e le regole — senza_condizione e
  simili — si EREDITANO dalla categoria: la sottovoce è un'etichetta
  di scaffale, non un secondo asse di regole. Giudici:
  `sottocategoria_valida(categoria, s)` ('' su sconosciuta o fuori
  categoria — il client non decide il catalogo) e
  `sottocategoria_tollerante` per il CSV (accetta id O etichetta,
  storta = '' mai uno scarto). La colonna `annunci.sottocategoria`
  nasce già ('' = non dichiarata, lecito per sempre) e i payload che
  la portano la scrivono: pubblica(), modifica() (assenza = CONSERVA,
  il pattern dello stock; cambio categoria = il giudice azzera da
  solo) e la cella facoltativa `sottocategoria` del CSV d'import. MAI
  nella modifica firmata degli importati né dall'import Nostr
  (l'evento non la porta), FUORI da CAMPI_VETRINA e dal modello CSV
  scaricabile (pubblicizzarla sarebbe mostrarla — nelle rotte
  autenticate con `a.*` esce gratis, innocuo e dichiarato).
  LE REGOLE DI CONFINE, decise sui casi veri e scritte nel commento
  del catalogo (entreranno nel prompt della ricategorizzazione AI
  all'accensione): smartwatch → Orologi e gioielli (il nome della
  sottovoce «Orologi e smartwatch» È la regola); cuffie e auricolari
  → Audio e video, Telefonia tiene «Cover e accessori»; stampanti da
  ufficio → Informatica, stampa 3D → Elettronica; droni e modellismo
  RC → Elettronica (non Foto e ottica); caschi moto → Motori; la roba
  da bimbi — vestiti, giocattoli, attrezzatura — sta in Bambini
  (regola d'oro, decisione di Andrea: Abbigliamento è adulti,
  Donna/Uomo), ma le bici VERE da bimbo in Biciclette e i giochi da
  tavolo per famiglie in Sport e hobby; l'artigianale si classifica
  per FUNZIONE (le tazze al tornio in Cucina e tavola, i saponi in
  Bellezza), Arte e artigianato è l'oggetto d'arte; Collezionismo =
  valore da collezione (numerato, raro, sealed), non il semplicemente
  vecchio; per ASCOLTARE → Audio e video, per SUONARE → Strumenti.
  ELETTRONICA È RESTATA con un contenuto SUO (decisione di Andrea: in
  produzione aveva ZERO annunci dopo gli scorpori, ma chiuderla
  avrebbe spostato il residuo in «Altro» e tolto LA parola che un
  venditore normale cerca): droni/modellismo, stampa 3D, smart home,
  componenti maker, strumenti di misura — con le sottovoci nitide
  sparisce anche l'esitazione col laptop. NON rinominata: la regola
  «si aggiunge, non si rinomina» tiene, e lo scaffale dice il
  contenuto meglio di un nome nuovo.
  IL GIUDICE SILENZIOSO (ago 2026, idea di Andrea): la colonna si
  riempie DA SOLA, senza AI e senza che nessuno veda nulla — parole
  chiave dentro la categoria GIÀ scelta, il pattern SINONIMI_CATEGORIA
  un piano più in basso. Catalogo `SINONIMI_SOTTOCATEGORIA` +
  `sottocategoria_indovina(categoria, titolo, descrizione)` in
  server.py accanto all'albero: parole intere normalizzate, prefisso
  solo da 5 lettere in su («auto» non prende «autoradio»), titolo pesa
  2 e descrizione 1, assegna solo il vincitore UNICO — il pareggio è
  un dubbio e il dubbio resta ''. MISURATO sui dati veri prima di
  accenderlo: 45/46 giusti in produzione più il NON SO voluto del Telo
  d'Amare, 12/15 fuori campione, ZERO sbagliati nei due giri — quando
  non ce la fa SI ASTIENE, mai un'assegnazione tirata a indovinare, ed
  è strutturale: dentro una categoria i vocabolari delle voci quasi
  non si sovrappongono. Zero rete e zero await (il patto anti-doppione
  di pubblica non si tocca). Si aggancia dove il payload non porta una
  sottovoce valida: pubblica(), modifica() (che ci RIPROVA sui testi
  nuovi quando la colonna è vuota — il ritocco può aver aggiunto la
  parola che mancava — ma non rigiudica MAI un valore scritto),
  l'import CSV, e il dopo-import Nostr (ogni giro, solo righe vuote:
  così quando la coda delle categorie sposta un annuncio fuori da
  «Altro», la sottovoce arriva da sola al giro dopo). Il dizionario è
  UNO e vive in server.py — la proposta in proposte/ è morta lì
  dentro, la lezione del prompt in due copie — e si arricchisce coi
  dati veri: `python assegna_sottocategorie.py --conta` sul VPS dice
  quante righe sono assegnate e DOVE il giudice si astiene di più, coi
  titoli d'esempio (SOLO gli attivi: il conto a tre stati pescava i
  venduti delle prove di rodaggio e misurava fantasmi — la passata
  --scrivi invece tiene anche revisione e venduto, che possono tornare
  in vetrina); si impara dai NON SO, mai dagli sbagli.
  IL TERMOMETRO SUONA DA SOLO (ago 2026, «il --conta lo dimenticherò
  di sicuro»): `termometro_sottocategorie` nell'orologio — il LUNEDÌ,
  UNA notifica aggregata agli admin con totale e le 3 categorie più
  scoperte, più il conto dei vuoti che il dizionario di OGGI
  coprirebbe già (= serve solo un rilancio dello script: chiude anche
  il secondo modo di dimenticarsene). L'ancora è il CALENDARIO e non
  un conteggio in memoria, ed è deliberato: il gate in RAM muore a
  ogni deploy e un «ogni 7 giorni» contato da lì suonerebbe a ogni
  riavvio. MA IL SOLO CALENDARIO NON BASTAVA, e qui c'era scritto il
  contrario — «un riavvio può al più far suonare due volte quel
  lunedì»: non era garantito da niente, ed è arrivato il caso dal
  campo a smentirlo (TRE notifiche in cinquanta minuti, agli orari di
  tre deploy). Dentro il lunedì a distinguere il primo battito dal
  centoquarantesimo c'era un globale, cioè una deduplica valida
  quanto il processo. Dall'ago 2026 il timbro sta nella tabella
  `timbri` — vedi «I TIMBRI DEGLI AVVISI PERIODICI».
  Conta come il --conta (soli attivi, «Altro» escluso:
  è piatta per forza, non è «scoperta»); tace sotto
  TERMOMETRO_SOTTOCATEGORIE_MINIMO (5), tace a vetrina piena, e la
  leva TERMOMETRO_SOTTOCATEGORIE (True di serie) la spegne — una coda
  ferma non suona, il patto dei solleciti. Lo stesso
  script fa la passata sul pregresso (anteprima di serie, `--scrivi`
  per farla, un percorso di database per la prova generale su una
  copia — pattern ripulisci_anello): tocca solo righe VUOTE in stati
  attivo/revisione/venduto, idempotente, e legge il giudice dal TESTO
  di server.py senza importarlo (la lezione di ricategorizza: l'import
  farebbe partire init_db, e in CI il config non esiste). NIENTE coda
  admin per queste assegnazioni, ed è deciso: il dato non esce da
  nessuna parte finché l'albero dorme, e correggere un'assegnazione il
  giorno dell'accensione costerà un rilancio dello script.
  ALL'ACCENSIONE (documentato, non costruito): foglio-picker in Vendi
  dipendente dalla categoria (pattern PICKER) — che il giudice potrà
  PRESELEZIONARE, con l'utente ultimo giudice —, param `sotto` su
  /api/listings ('' storici fuori dal filtro, il patto del dato
  dichiarato), chips dentro la vetrina di categoria in Sfoglia
  (nessuna piastrella nuova), prompt AI con albero e confini per il
  residuo delle astensioni, eventuale secondo tag `t` NIP-99 — sarà
  solo frontend + un parametro, e il catalogo sarà già catalogato
  invece che vuoto. `prove.py` difende il patto: chiavi ∈ CATEGORIE,
  id unici e kebab, niente «altro», i giudici nei loro casi, il
  dizionario allineato all'albero voce per voce.
  LA PAGINA «SFOGLIA» (lug 2026): le categorie come vetrina, quarta
  radice della nav — griglia a due colonne di piastrelle illustrate,
  modello Vinted. Vista `view-sfoglia` (niente header, come Ordini e
  Profilo; niente barra di ricerca, che vive in Esplora e duplicarla
  sarebbe un secondo posto da tenere allineato per sempre).
  `renderSfoglia` disegna le voci del catalogo (27 dall'ago 2026)
  ORDINATE PER NUMERO DI ANNUNCI (ago 2026, decisione di Andrea che
  ROVESCIA la regola della nascita — «in ordine FISSO, mai per
  numero»): la più piena in cima, poi a scendere, le vuote in fondo.
  IL PERCHÉ DI ALLORA VA TENUTO perché resta vero: una mappa che si
  riordina non si impara, e ai nostri numeri si riordina SPESSO — le
  categorie piene hanno pochi annunci ciascuna, e un annuncio in più
  basta a far saltare una piastrella di posto. Andrea l'ha scelto
  sapendolo: la parte viva della griglia in cima vale più della mappa.
  (In mezzo c'è stata, per qualche ora, la via delle DUE FASCE — piene
  sopra e vuote sotto, catalogo dentro ogni fascia — superata nello
  stesso giorno.) IL PAREGGIO È L'ORDINE DI CATALOGO, garantito dalla
  stabilità del sort: due categorie con lo stesso conteggio non
  ballano a ogni apertura. I conteggi sono quelli che viaggiano GIÀ
  nella busta di prima pagina (la fonte di `renderChips`: zero query
  nuove, zero endpoint) e NON si mostrano sulle piastrelle; senza
  conteggi (apertura precoce, server muto) sono tutti a zero e il
  sort stabile restituisce da solo l'ordine di catalogo — il ripiego
  è il comportamento della nascita, senza un ramo apposta. La griglia
  non è più «statica una volta per sempre»: si ridisegna SOLO quando
  la firma dell'ordine cambia (`sfogliaDaRifare`), sull'ENTRATA nella
  vista — mai mentre la si guarda. E LO SFARFALLIO DELLE ICONE è
  chiuso (ago 2026, visto da Andrea): all'apertura si vedevano per un
  attimo le EMOJI di ripiego, poi le illustrazioni — non un ritardo
  del render ma la rotta no-cache, che obbliga ogni `<img>` a
  rivalidare (un giro di rete per il 304) prima che l'onload spenga
  l'emoji. La cura è `scaldaSfoglia` (le 27 illustrazioni scaldate a
  riposo 2,5s dopo l'avvio: dentro la sessione il browser riusa la
  risorsa senza rivalidare, con l'URL IDENTICO byte per byte —
  helper unico `urlIllustrazione`) più il `data-ok` COTTO nell'HTML
  quando la figura scaldata è già arrivata: le ufficiali dal primo
  fotogramma, zero richieste al render, e chi apre prima del calore
  ha il giro di prima — degradazione, non regressione. ~805 KB una
  volta per sessione, l'ordine di grandezza della prima pagina di
  vetrina. Il nome va in `data-cat` e mai dentro la
  stringa JS dell'onclick — la lezione di «Valle d'Aosta» sul picker.
  LE CATEGORIE VUOTE SONO PIASTRELLE NORMALI (lug 2026, deciso da
  Andrea guardando la pagina vera). Erano nate spente a metà opacità,
  con i conteggi di `conteggiServer` a decidere chi lo fosse; ma in
  rodaggio le vuote sono la maggioranza — 17 su 26 — e la griglia
  sembrava mezza rotta. Chi ne apre una vuota trova la vetrina col suo
  «🔔 Avvisami se arriva», che è il posto giusto per dirlo: meglio
  dopo, con una via d'uscita in mano, che prima con un colore.
  DUE DETTAGLI DEL PASSAGGIO A ESPLORA, tutti e due nati da un tester
  che li ha visti: `apriCategoria` SVUOTA la griglia prima di partire
  (setCat ricarica dal server e la risposta arriva mezzo secondo dopo:
  senza, si atterra vedendo per un attimo gli annunci della categoria
  di prima, che è la cosa più sbagliata da mostrare a chi ne ha appena
  scelta un'altra); e il tasto Esplora della barra passa da
  `vaiEsplora()`, che riporta ad activeCat='Tutto' — NON è go('esplora'),
  che serve anche a tornare da una scheda e lì il filtro deve restare.
  Chi tocca il nome del tab si aspetta tutto il mercatino, non la
  categoria in cui era entrato da Sfoglia mezz'ora prima.
  MA LA NAV MENTIVA (lug 2026, bug vero visto da Andrea): entrando da
  una piastrella si accendeva «Esplora», e quel che si vedeva era una
  vetrina FILTRATA con pochi oggetti — chi guardava credeva fosse tutto
  il mercatino, e lo trovava vuoto. La vetrina resta UNA (duplicarla
  per Sfoglia sarebbe stato due posti da tenere allineati per sempre):
  a cambiare è solo la RADICE da cui la si guarda, che ora ha un nome —
  `ramoVetrina` ('esplora' | 'sfoglia'). Il giudice unico è `voceNav()`,
  dove viveva già la mappa delle viste interne (dettaglio, negozio e
  sicurezza rispondono alla vetrina; l'ordine agli Ordini) — e per la
  stessa ragione una scheda aperta DENTRO un reparto resta nel ramo: la
  nav dice dove sei, e «dove sei» è la strada che hai fatto, che è
  anche quella che l'indietro ripercorre.
  Il ramo si accende in `apriCategoria` e si spegne in `setCat('Tutto')`
  — cioè quando si torna al catalogo intero da QUALUNQUE strada (il tab
  Esplora, la pillola «Tutto», il ritorno dopo una pubblicazione): un
  posto solo, e il ramo non può sopravvivere al filtro che lo
  giustifica, o resterebbe acceso «Sfoglia» davanti a tutto il
  mercatino — la stessa bugia al contrario. `vaiEsplora` lo chiude
  comunque, anche a categoria già Tutto: il tocco sul nome del tab è
  sempre un ritorno alla radice e non deve dipendere dallo stato di
  un'altra variabile per esserlo. Il ramo NON vive nella cronologia (è
  una variabile, non una entry): un «avanti» del browser dentro un
  reparto ricostruisce la vista ma non il filtro — è la stessa
  imperfezione dichiarata del motore di navigazione, non una nuova.
  CONSEGUENZA sul resto: `renderChips` non riporta più a «Tutto» la
  categoria attiva rimasta senza annunci. Quella scorciatoia era nata
  contro i filtri fantasma, ma con Sfoglia diventava una bugia — si
  tocca «Informatica», che è vuota, e si finisce davanti alla vetrina
  intera senza che nulla lo dica. Ora la categoria scelta resta in
  elenco anche a zero annunci, in TESTA (la fila scorre di lato, e una
  pillola accesa in fondo non la vedrebbe nessuno): è la regola della
  regione nel pannello Filtri, «il campo non deve mentire».
  NAV A CINQUE POSTI: il tondo del Vendi resta al centro ESATTO
  (verificato: 180.0 su 180.0 a 360px) perché le voci sono quattro ma
  gli slot cinque — `.nav-vuoto`, uno spaziatore elastico che tiene il
  quinto posto, vuoto di proposito e già destinato a qualcos'altro. In
  topbar desktop sparisce (lì i bottoni sono `flex:0 0 auto`).
  L'ORDINE è [Esplora][Sfoglia](+)[vuoto][Ordini] (lug 2026): il posto
  vuoto sta IN MEZZO, fra Vendi e Ordini, non in coda — così gli Ordini
  restano all'estrema destra, dove il pollice li trova senza guardare.
  Spostarlo è solo uno scambio di posto nel markup: voci e spaziatore
  sono tutti `flex:1`, quindi il Vendi resta il terzo di cinque slot
  uguali e nessuna regola CSS si tocca (misurato: centro invariato,
  nav 61,2px, e da desktop lo spaziatore è già `display:none`).
  LE ICONE SONO NOSTRE (lug 2026): tre SVG al posto delle emoji
  🛍️🗂️🤝, che cambiavano forma da un telefono all'altro e non
  seguivano i token del tema — LENTE per Esplora, PIASTRELLE per
  Sfoglia (la sua pagina in miniatura), PACCO di tre quarti per gli
  Ordini. Inline nel markup, non da JS: nessun lampo all'avvio e la
  barra esiste prima che il primo script giri. Disegnate sulla griglia
  da 24 con la mano di `tagliaSVG` e `jarSVG` — tratto a currentColor,
  capi tondi, velo al 12% (classe `.velo`) che dà corpo — e fuori
  squadra di un pelo, che è la personalità delle illustrazioni delle
  categorie portata dove un'immagine non può arrivare.
  LA VOCE ATTIVA SI ILLUMINA E BASTA (modello Vinted e Subito): via la
  pillola pesca sotto l'icona e il suo anello, resta il colore —
  `--sats-deep` di giorno, `--sats-text` di sera (sul bruno l'arancio
  del giorno rende 4,8, quello della sera 8,5: si abbassa la LUCE, non
  si cambia il segno — la regola della spedizione gratuita). Icona ed
  etichetta si accendono INSIEME senza una riga di codice: il colore lo
  dà il bottone, l'icona lo eredita con currentColor. È tutto ciò che
  rende possibile l'accensione, ed è il motivo per cui qui non possono
  esserci immagini. Niente transizioni, quindi
  `prefers-reduced-motion` non ha nulla da spegnere.
  MISURA 26px, ed è un TETTO: è quanto occupavano le emoji col loro
  respiro (20 di glifo + 3+3 di padding), quindi la nav resta 61px e
  l'invariante con `#barraCompra` è salva. Per crescere ancora
  servirebbe una barra più alta, e quella non si tocca. Il resto della
  presenza si prende dove non costa nulla: il viewBox è `2 2 20 20` e
  non `0 0 24 24` — la stessa griglia RITAGLIATA sul margine che
  avanzava attorno all'inchiostro (le tre stanno fra 2,65 e 21,35 col
  tratto compreso: verificato, il ritaglio non taglia). Il disegno
  cresce del 30% dentro la stessa scatola e il tratto scende a 1.5
  perché ingrandito con lui torna a rendere 1,95px: stesso peso, figura
  più grande. È il gemello del ritaglio che `ritaglia_categorie.py` fa
  alle illustrazioni — il margine trasparente è spazio buttato. Chi
  ridisegna un'icona tenga l'inchiostro dentro [2,22], o il ritaglio
  gliela taglia. In topbar desktop stanno a 22px e la voce attiva torna
  una pillola: lì non è una tab bar da pollice ma una fila di
  linguette, e la pillola è il suo idioma.
  TRE STRADE PROVATE E SCARTATE, coi motivi, che è la parte che serve
  fra sei mesi: 1) il PACCO PIATTO — quadro più riga del coperchio, cioè
  la famiglia di `tagliaSVG` — a 24px si legge come un portafoglio, e
  col nastro verticale intero come una finestra a quattro riquadri; di
  tre quarti è un pacco e basta, e la parentela con le taglie si perde
  ma si guadagna un'icona che si riconosce. 2) IL BARATTOLO del logo,
  chiesto da Andrea, disegnato e guardato acceso: funziona, ma nella
  STESSA schermata quella forma farebbe tre mestieri — marchio in
  testata, «l'ho messo via» sulle card (dove per giunta è pieno o vuoto
  e racconta un livello), «dove sono» in barra — e i primi due si
  vedono insieme, uno sopra l'altro, in ogni vetrina. La lente invece
  non dice niente altrove: è libera. 3) LE ILLUSTRAZIONI delle
  categorie rimpicciolite a 24px: a quella misura il disegno diventa
  una macchia calda, e soprattutto un'immagine NON PUÒ ACCENDERSI — il
  meglio che si può fare per spegnerla è sbiadirla (grigio più
  opacità), che la fa sembrare rotta, non spenta. Guardate a schermo
  tutte e tre prima di decidere; non riproporle senza un motivo nuovo.
  IL GESTO INDIETRO ha qui la sua UNICA eccezione, ed è dichiarata: il
  tocco su una piastrella porta a Esplora, che è una radice — ma non è
  un cambio di tab, è una DISCESA, e l'indietro deve riportare allo
  scaffale. `navSpingi` è una bandierina alzata da `apriCategoria` e
  letta-e-azzerata in cima a `navRiflette` (prima di ogni via d'uscita,
  o si scaricherebbe su una navigazione che non l'ha chiesta).
  LE ILLUSTRAZIONI: 27 WebP in `assets/categorie/{slug}.webp`, nome
  calcolato da `slug_categoria` (server) e `slugCat` (client) — nessun
  elenco doppio. Sono SCONTORNATE su trasparenza, non su un fondo:
  quindi il colore della piastrella è una scelta nostra, ed è un BRUNO
  di casa (`--cat-fondo`), scuro perché i disegni sono in tinte calde e
  sabbiose — misurato sui file veri: su un `--carton` chiaro
  venticinque su ventisei scenderebbero sotto 3:1 (media 1,85), cioè
  sparirebbero. Di sera sale di un gradino, che la pagina è già bruna e
  la piastrella deve staccarsene; un gradino più chiaro di giorno è
  stato provato a schermo e rimesso indietro (decisione di Andrea).
  LA PIASTRELLA È UNA COLONNA FLEX, e questa è la parte che vale: nome
  sopra a quota propria, illustrazione sotto che si prende TUTTO il
  resto. Finché erano due strati sovrapposti, ogni pixel dato al
  disegno andava misurato contro la riga di testo — e il tetto restava
  56px, perché le illustrazioni hanno zone quasi bianche e il nome in
  crema ci faceva 1,00:1, cioè spariva. Un velo scuro sfumato sotto il
  nome, provato, salvava il testo ma spegneva il 55% dei disegni: cura
  un male causandone un altro. Col flex non possono pestarsi PER
  COSTRUZIONE e il disegno arriva a 73px. Perché siano TUTTI della
  stessa altezza serve che nessun nome vada a capo: 14px col margine a
  9 è la taratura che fa stare in una riga anche il più lungo
  («Console e videogiochi»: ne chiede 140 e ne ha 141, a 360px). Chi
  alza il corpo del testo rimette quelle voci su due righe, e quelle
  piastrelle avranno il disegno più piccolo delle altre.
  MA L'ALTEZZA UGUALE NON BASTA, e questa è la lezione che si paga
  guardando tutte e 26 insieme invece che una alla volta. Prima
  scappano le LARGHEZZE (la scarpa faceva 122×72 contro l'orologio
  47×72), e a quello risponde il TETTO alla larghezza del riquadro,
  54% della piastrella. Ma anche a rettangoli pari le icone non
  sembrano uguali: un pallone e una chitarra possono occupare lo
  stesso rettangolo, ma il pallone è pieno e la chitarra è un filo —
  a pesare è l'INCHIOSTRO, cioè quanti pixel pieni il disegno copre.
  Misurato: le sei che Andrea ha indicato «troppo grosse» erano le
  sei più cariche d'inchiostro, e la chitarra «troppo piccola» era la
  più leggera. Il rettangolo non lo diceva; l'inchiostro sì.
  Il pareggio lo fa `ritaglia_categorie.py`, che mette un TETTO
  sull'inchiostro reso (1,05× la mediana) e dà un bordo trasparente a
  chi lo supera — il disegno non si tocca, si rende più piccolo in
  pagina. Il contrario non si può: i più leggeri sono già al massimo
  che la piastrella concede, quindi la chitarra resta la più leggera,
  ed è un limite dichiarato. Per questo l'immagine è CENTRATA nel suo
  riquadro (`object-position:50% 50%`): coi bordi del pareggio,
  ancorarla a un angolo l'avrebbe allontanata chi più chi meno.
  Normalizzare l'AREA del rettangolo è stato provato e scartato: per
  far stare gli estremi ogni disegno scende sui 57px e le piastrelle
  si svuotano — si perde su tutte per pareggiare due casi.
  `ritaglia_categorie.py` toglie il margine trasparente che le
  illustrazioni hanno di fabbrica (~30%): senza, un terzo dello spazio
  della piastrella sarebbe vuoto e il disegno si vedrebbe piccolo. È
  idempotente e va rilanciato quando si aggiunge o si rifà
  un'illustrazione; `prove.py` verifica che i file siano tirati, che è
  l'invariante su cui il CSS poggia.
  L'ALPHA SI GUARDA SOPRA UNA SOGLIA (8 su 255), non sopra lo zero, e
  la ragione è un caso vero: «Bellezza e benessere» arrivava con una
  velatura quasi invisibile stesa su TUTTA la tela, quindi col
  confronto a zero risultava già tirata — il ritaglio non la toccava e
  il disegno vero, 329×236 dentro un quadrato da 512, si vedeva molto
  più piccolo degli altri. Sugli altri 25 file la soglia sposta il
  riquadro di 4px in tutto. La stessa soglia sta nella prova, o
  lascerebbe passare proprio il caso che deve prendere. Lo script non
  riscrive per scarti sotto il 2%: così rilanciarlo non ricomprime
  ogni volta tutto (i file sono lossy, e la regola della compressione
  unica vale anche qui).
  MISURE tarate su QUANTE piastrelle stanno in una schermata: dieci,
  come nel riferimento (decisione di Andrea). A 360×760 restano 630px
  fra l'etichetta e la nav, cioè cinque righe da 120 — piastrella 110 e
  gap 10, che con la larghezza 159 fa `aspect-ratio:1.445`. Per questo
  l'etichetta non porta il `padding-top` maggiorato delle altre viste e
  la griglia ha 8px di respiro invece di 12: sono i pixel della quinta
  riga. 3 colonne da 768px, 4 da 1024.
  NEL PICKER DI VENDI ci sono le ILLUSTRAZIONI (lug 2026: prima le
  emoji, poi la prova a schermo ha convinto Andrea del contrario).
  `icoCategoria()` le rende nude a 30px, nelle voci del foglio e nel
  campo chiuso, e il file è il FRANCOBOLLO `{slug}-mini.webp` da 128px
  — non quello pieno: 181 KB in tutto invece di 787, e 1,4 MB di
  bitmap invece di 13, per un menu che si apre in due secondi. Li fa
  `ritaglia_categorie.py` dai file già pareggiati, così le proporzioni
  del menu sono quelle della griglia senza un secondo posto da tarare;
  la rotta `/assets/categorie/{nome}` accetta il suffisso passando
  dalla stessa whitelist, e `prove.py` controlla che ci siano tutti e
  26 (manca solo lì dentro, e il ripiego a emoji fa sembrare che vada
  tutto bene). Classe `.cat-ico` e non `.p-ico`, che è condivisa con
  le taglie del pacco.
  IMPERFEZIONE DICHIARATA, ed è il prezzo della resa nuda: il foglio
  in tema chiaro è BIANCO, e questi disegni usano il crema come colore
  del CORPO — così il barattolo di crema ci perde il corpo (restano
  coperchio e contagocce a mezz'aria) e il telefono e il ciak si
  assottigliano. Gli altri 23 reggono, e in tema scuro reggono tutti.
  La pastiglia scura sotto l'icona è stata provata e SCARTA­TA: dava
  contrasto a tutti e rendeva identici i due temi, ma trasformava una
  lista da scorrere in un cassetto di app. Se un giorno si vorrà
  chiudere quel buco, la strada non è il CSS: è rifare quei tre
  disegni con un corpo che non sia quasi-bianco.
  `categoria_automatica` di importa_nostr.py NON ESISTE PIÙ (lug
  2026): indovinare la categoria dal titolo sbagliava in silenzio — lo
  «Sparkling Sake» finiva fra gli arredi perché quella categoria
  pescava «cucina» — e sugli importati nessuno se ne accorgeva. Gli
  annunci da Nostr nascono in «Altro» e a collocarli è il VENDITORE,
  che è l'unico a saperlo; l'import non ricopre mai una categoria già
  scelta, quindi la sua resta per sempre, e a chiederglielo c'è il DM
  di completamento (vedi import aperto).
  Frontend: pillole ordinate per numero di annunci ATTIVI
  (decrescente), "Tutto" sempre prima, le vuote non compaiono proprio
  (Tutto e la ricerca coprono la scoperta); conteggi dai listings
  caricati, rifatti a ogni giro in `renderChips()` (chiamata da
  `loadListings` e `avviaVetrina`); se la categoria attiva resta
  senza annunci si torna su Tutto. Vale per vetrina autenticata,
  anonima e DEMO (dati finti già rimappati). Dal cantiere «tenuta al
  volume» (sotto) i conteggi delle pillole coi dati vivi vengono dal
  server (`conteggi` in prima pagina), il locale resta per la demo.
  Condizioni dell'oggetto (lug 2026): scala a 5 livelli — catalogo
  `CONDIZIONI` in server.py (nuovo | come_nuovo | buono | accettabile |
  da_sistemare, id → etichetta breve; il catalogo JS `CONDIZIONI` del
  client porta anche la `desc` breve del foglio di scelta, e le
  <option> del form — ormai un deposito nascosto, vedi il
  foglio-picker — le etichette lunghe). Colonna `annunci.condizione`
  ('' = storici e importati, nessun obbligo retroattivo), OBBLIGATORIA
  client E SERVER (dal lug 2026, deciso: `guardia_zona_condizione` — giudice
  unico di pubblica e modifica — risponde 400 su assente o
  sconosciuta; gli storici si mettono in regola al primo ritocco; MAI
  nella modifica firmata degli importati, l'evento NIP-99 non la porta
  e il campo si nasconde, e la guardia in modifica scatta DOPO i
  controlli di proprietà/stato: chi tocca un annuncio in revisione
  deve sentirsi dire quello. L'import CSV resta tollerante:
  `condizione_tollerante`, colonna facoltativa). In
  CAMPI_VETRINA (search e miei gratis via a.*); param `condizione` su
  /api/listings (dichiarata soltanto: gli storici '' restano fuori,
  valore storto = nessun filtro) + scelta nel pannello Filtri (in DEMO
  client-side; dal lug 2026 anche lei un foglio-picker, con le pillole
  NUDE senza le descrizioni e la voce «Qualsiasi condizione»).
  IL SEGNO (lug 2026, dopo il feedback di Andrea): PILLOLA TESTUALE
  COLORATA `condPill()` — forma delle pillole di zona e categoria, la
  scala parla col COLORE (classi `.pill.cond-*`: verde pieno
  `--trust-deep` → verde tenue `--trust-soft` → ambra oro → arancio
  `--sats-soft` → grigio `--off-bg`, coppie della palette con
  contrasto AA misurato nei due temi; l'oro resta chiaro di sera come
  l'etichetta prezzo, e due override `html[data-tema="scuro"]` dove la
  coppia chiara non regge al buio). Vive nel dettaglio e nel
  foglio-picker del form, MAI in card: la vetrina resta pulita (le
  emoji ✨🌟👍🆗🔧 non comunicavano una gradazione; i pallini graduati
  ●●●○○ provati al loro posto si confondevano con le stelle delle
  recensioni — bocciati, non riproporli). Riga «— condizione:
  …» nel content NIP-99 (nessun tag: la spec non ne ha uno, pattern
  della spedizione) e nel catalogo della ricerca AI; colonna
  facoltativa `condizione` nel CSV d'import con `condizione_tollerante`
  (SINONIMI_CONDIZIONE: «ottimo» → come_nuovo, «da riparare» →
  da_sistemare…, sconosciuta = non dichiarata, mai uno scarto).
  DOVE LA CONDIZIONE NON VUOL DIRE NIENTE (lug 2026, decisione di
  Andrea): una marmellata è nuova per definizione, e chiederlo è una
  domanda senza risposte sbagliate — cioè una domanda inutile. La leva
  è `CATEGORIE_SENZA_CONDIZIONE` (frozenset accanto a CATEGORIE:
  «Alimenti e bevande» e «Bellezza e benessere» — creme, profumi e
  integratori si vendono nuovi, e un cosmetico già usato non è merce
  di seconda mano, è una cosa che non si vende — e dall'ago 2026
  «Buoni ed esperienze»: un buono è nuovo per definizione, anche la
  tessera fisica) e il giudice unico è
  `senza_condizione(categoria, consegna)`, da cui passano form,
  dettaglio, vetrina, NIP-99, ricerca AI e import — o divergono. Il
  secondo asse è la CONSEGNA: un codice Zalando è nuovo per
  definizione come la marmellata, ma vale solo per il digitale
  ESCLUSIVO (`consegna=='digitale'`) — sulla combo la merce fisica c'è
  e una condizione ce l'ha, quindi si guarda quella colonna e MAI
  `anche_digitale`. NON ci entrano «Arte e artigianato» (ci finisce
  anche l'arte usata, e un quadro di seconda mano può essere rovinato)
  né «Bitcoin» (le Jade di seconda mano sono merce vera).
  Tre conseguenze, e sono la parte da ricordare: 1) in SCRITTURA si
  azzera — `guardia_zona_condizione` non la chiede più e butta quella
  che arriva, così il database si pulisce da solo un annuncio alla
  volta invece che con una migrazione (e se domani quell'annuncio
  cambia categoria, la condizione gliela si chiede lì, che è quando
  serve: lo stesso patto della zona storta); 2) gli alimentari di
  IERI, che in colonna una condizione ce l'hanno, NON si migrano — il
  dato non si perde mai, come la zona resta intera nel database mentre
  in vetrina si mostra il solo comune — e a nasconderla è
  `condizione_da_mostrare` in uscita (lato client il gate è
  `titoloConCondizione`, l'unico posto dove la pillola si disegna:
  così vale anche per la DEMO, che non passa da mapListing); 3) il
  FILTRO condizione li lascia fuori (patto degli storici: il filtro
  promette una condizione dichiarata), e il vecchio con la colonna
  piena lo escludono le due clausole aggiunte alla query — o
  pescherebbe una condizione che la scheda non mostra più. In vetrina
  la riga «Condizione» del pannello Filtri sparisce sulle categorie
  esenti e il filtro DORME (`condFiltrabile()` toglie il parametro):
  non si azzera, o si romperebbe il patto dei filtri di sessione che
  sopravvivono al cambio categoria. Gemello client `CAT_SENZA_COND` +
  `senzaCondizione()`, e `prove.py` fallisce se i due elenchi
  divergono. Nel form il campo compare e sparisce da
  `aggiornaCondizioneForm()`, chiamata dal `poi` del picker categoria
  e da `aggiornaConsegnaForm()` (i due soli ingressi che la cambiano).
  Foglio-picker al posto delle tendine native (lug 2026): la
  `<select>` del sistema operativo non si può vestire da Barattolo, e
  TUTTE le tendine dell'app sono passate al nostro foglio — categoria,
  condizioni e taglia del pacco nel form Vendi, condizioni nel
  pannello Filtri, ordinamento della vetrina. Il MOTIVO per cui non è
  una riscrittura: la select resta in pagina come DEPOSITO del valore
  (attributo `hidden`), e tutto il JS di prima continua a leggerla e
  scriverla (`el('sellCond').value`) — publish, modifica, reset,
  filtri e validazioni intonsi. A parlare col dito è il campo-bottone
  `.campo-scelta` (`#{id}Btn`, veste da select con la freccia ▾) che
  apre `#pickerSheet` col pattern dei fogli di sempre: `PICKER` è il
  catalogo, e ogni voce dichiara `titolo`, `voci()` (val + resa nel
  foglio), `campo(v)` (resa nel campo-bottone) e un `poi` facoltativo
  — l'azione che prima stava sull'`onchange`, indispensabile
  all'ordinamento (`setOrdina`), che con la select nascosta non riceve
  più l'evento. `apriPicker` disegna e mette a fuoco la voce scelta,
  `scegliPicker` scrive nel select, chiude ed esegue `poi`;
  `aggiornaPicker(id)` riallinea il campo al valore e VA RICHIAMATA da
  chiunque tocchi il select via JS (`aggiornaPickerVendi()` fa i tre
  del form in blocco, così non se ne dimentica uno: è in editListing,
  annullaModifica e publish; più setOrdina, toggleFiltri e
  azzeraFiltri per gli altri due). Le stesse condizioni si rendono in
  DUE modi secondo il posto: col form la pillola + la descrizione (che
  aiuta a scegliere), nel filtro le pillole NUDE (lì non si impara la
  scala, si sceglie). Accessibilità: `role="dialog"`/`radiogroup`, Esc
  chiude, frecce ↑↓ scorrono, e `pickerTrigger` riporta il focus al
  campo per OGNI strada di chiusura — un campo-bottone `display:none`
  però non può prenderlo (succede solo forzando il picker da codice su
  un campo nascosto, come la taglia senza Spedizione spuntata).
  CHIUSURA CHE NON FA CATENA (lezione del secondo giro): `scegliPicker`
  chiamava `closeSheet()`, che spegne TUTTA la pila di fogli e azzera
  il `pollTimer`. Invisibile finché il picker si apre da una vista o
  dal pannello Filtri (che è markup in pagina, non un foglio: finisce
  sotto il velo e resta aperto dopo la scelta), ma aperto da DENTRO un
  foglio avrebbe chiuso anche quello sotto — e sopra il paySheet
  avrebbe ucciso il polling del pagamento. Quindi `chiudiPicker()`
  spegne solo il picker e tiene il velo se `altroFoglioAperto()`, e
  `tapFuoriSheet()` sul velo chiude il foglio più in ALTO invece della
  pila (`closeSheet` resta il catch-all). Il picker si può quindi
  aprire dentro un foglio senza pensarci. Cintura in CSS:
  `select[hidden]{display:none !important}`, perché le nostre select
  si pescano per tag (`.field select`, `.strumenti select`) e una
  futura regola col `display` farebbe ricomparire la tendina di
  sistema. Tre vestiti per tre contesti, stesso markup:
  `.campo-scelta` è la misura da campo di form, `.strumenti
  .campo-scelta` la ritara a pillola come il bottone Filtri (con
  l'etichetta che si accorcia coi puntini, vedi il contatore dei
  pionieri più sotto), `.filtri-riga .campo-scelta` la veste come gli
  input di accanto. Dal primo giro: `prefers-reduced-motion` ora
  ferma la scivolata di TUTTI i fogli (`.sheet{transition:none}`),
  che mancava da sempre.
  Tenuta al volume (lug 2026): la vetrina va a PAGINE col cursore
  keyset. `/api/listings`, `/api/negozio/{chi}` e `/api/listings/miei`
  accettano `limit` (clampato a 100) e `cursore` = '{creato}_{id}'
  dell'ultima riga (ordine `creato DESC, id DESC`; cursore storto =
  prima pagina, mai 400; helper unico `pagina_annunci`). Il
  discriminatore è retro-compatibile nei DUE sensi: SENZA `limit` la
  risposta è l'array di sempre col tetto di sicurezza 500 (un JS
  vecchio in cache vive felice), CON `limit` è la busta
  `{annunci, cursore}` + SOLO in prima pagina `totale` (della vista:
  rispetta cat/q) e `conteggi` (globali per categoria); il negozio
  AGGIUNGE le chiavi al dict di sempre; un server vecchio col JS
  nuovo = array letto come pagina unica (`leggiPagina`). Indici
  `idx_annunci_vetrina/categoria/venditore` in `init_db`. Param `q`
  su /api/listings = ricerca semplice LIKE (titolo/descrizione/zona)
  per la vetrina ANONIMA, componibile con cat+cursore. Ordinamento e
  filtro prezzo (lug 2026): param `ordina` (vuoto = più recenti |
  prezzo_su | prezzo_giu; catalogo `ORDINAMENTI`, keyset su
  (prezzo_sats, id) con `idx_annunci_prezzo`; sconosciuto = default,
  mai errore) e `prezzo_min`/`prezzo_max` + `valuta_filtro` (eur =
  conversione LATO SERVER con `cambio_btc_eur`, 503 se il cambio
  manca; il confronto è sempre su prezzo_sats, che per i listini EUR
  è l'equivalente al cambio di pubblicazione — dichiarato). Frontend:
  select discreto + pannello «Filtri» sotto l'etichetta della griglia
  (`.strumenti`, `setOrdina`/`applicaFiltri`/`azzeraFiltri`), filtro
  nella valuta del toggle attivo al momento di Applica, stato per
  SESSIONE (mai localStorage) che sopravvive al cambio categoria
  (patto delle app di mercatino), in DEMO client-side sui dati finti.
  La ricerca AI coi vincoli scritti resta separata da questi filtri
  di navigazione. Le MINIATURE dal lug 2026 sono QUADRATE
  (ImageOps.fit al centro, 640 q87 LANCZOS, `MINIATURA_LATO/QUALITA`):
  la card 1:1 col cover ingrandiva il lato corto delle vecchie
  rettangolari (la sgranatura); il backfill rifà da solo quelle di
  ricette vecchie confrontando le intestazioni col lato CORTO della
  foto piena. Nasce
  `GET /api/listings/{id}` (registrato DOPO /miei: l'ordine delle
  rotte conta) per il deep-link /annuncio/{id} oltre le pagine
  caricate.
  LA RICERCA AI HA UN FRENO (ago 2026, audit): era l'unica rotta dove
  UNA richiesta di un utente qualunque = UNA chiamata ad Anthropic, e
  con un prompt di dimensione massima FISSA — la shortlist si riempie
  fino a 300 annunci anche quando la domanda non trova niente, quindi
  ogni ricerca costa uguale, tanto. L'unico recinto era
  l'autenticazione, che la passa chiunque abbia un account.
  `TETTO_RICERCHE_AI_ORA` (30, leva; 0 = nessun freno) col pattern di
  `IMPORT_QUOTA` e l'ora al posto del giorno; purga in `pulisci_avvisi`.
  A quota finita NON si sbatte la porta: si risponde col filtro per
  parole — che esisteva già come ripiego dell'eccezione e non costa
  niente — E LO SI DICE, invece di far sembrare che l'AI abbia capito
  poco. Il discriminatore è `busta=1` → `{annunci, ai}`; senza il
  parametro resta l'array di sempre, che è il patto della paginazione,
  e il client regge tutt'e due le forme. Più il `timeout` sulla
  chiamata, che era l'unica delle quattro del file a non averlo.
  ANCHE LO SCARICATORE DI FOTO È UNO SOLO (ago 2026, audit):
  `scarica_foto_url` in server.py, con `url_foto_ammesso` sulla
  partenza E su ogni salto (`_RedirectControllato`), timeout e tetto
  di byte. Prima urllib seguiva i redirect DA SOLO e in silenzio,
  quindi il guardiano giudicava solo il PRIMO indirizzo: bastava un
  «302 Location: http://127.0.0.1/…» per portare il server dentro la
  sua stessa rete. E `importa_nostr.scarica_foto` non aveva guardie
  AFFATTO — e non è solo lo script a mano, il server lo esegue ogni
  ora: con IMPORT_NOSTR_APERTO acceso quegli URL li scrive chiunque su
  Nostr. Ora l'import RICEVE lo scaricatore del server, ed è il patto
  del `vaglio`: quel che ha bisogno delle guardie del server vive nel
  server, e lo script lanciato a mano resta identico.
  La ricerca AI legge una SHORTLIST (`TETTO_CATALOGO_AI`
  300): match LIKE sulle parole della query + i più recenti a
  riempire — compromesso dichiarato: il sinonimo puro fuori dai 300
  più freschi può sfuggire. FOTO: accanto a ogni JPEG pieno nasce
  `a{id}_{i}{ver}_min.jpg` (vedi ricetta miniature più sotto) — nel DB
  restano SOLO i nomi pieni, `_min` è convenzione che il frontend
  deriva (`fotoMini`); backfill idempotente all'avvio
  (`genera_miniature_mancanti`), la modifica cancella anche la
  gemella, Cache-Control di 1 giorno su /foto (i nomi sono
  versionati).
  `/foto` NON È PIÙ UNA DIRECTORY MONTATA (ago 2026, la prima voce
  alta dell'audit): era l'ultimo StaticFiles del progetto, l'unica
  cartella servita in blocco, mentre ogni altra rotta pubblica
  rispetta la regola ferrea 3 una per una. Non era sfruttabile
  (Starlette normalizza i `..` prima di arrivare a noi) ma la
  superficie era quella sbagliata: chi lasciava un file lì dentro lo
  pubblicava. Ora c'è `GET /foto/{nome}` con `NOME_FOTO`, e la cosa
  da capire è COS'È quella regex: non una sanificazione del percorso
  — quella difende da ciò che ci si immagina — ma una whitelist di
  FORME derivata da chi scrive davvero in quella cartella, che sono
  quattro punti e quattro soli: `_salva_una_foto` (annunci e import
  CSV), `scarica_foto` di importa_nostr (estensione dal Content-Type:
  png/webp/gif esistono), `_salva_avatar`, e `genera_miniature_
  mancanti` — che è quello che si dimentica, perché passa su OGNI
  `.jpg` della cartella e quindi faceva la `_min` anche agli avatar
  (75 file veri in produzione: la forma è saltata fuori dai dati, non
  dal codice letto, ed è la lezione del giro). CHI AGGIUNGE UNO
  SCRITTORE deve aggiungere la sua forma lì, o le sue foto non si
  vedranno: è il prezzo — voluto — di non montare una directory.
  QUEL QUARTO SCRITTORE NON SCRIVE PIÙ (ago 2026, trovato di striscio
  proprio contando quei 75 file): la passata d'avvio salta i nomi
  `av_`, e il motivo è che quella gemella non serviva a NESSUNO —
  `_salva_avatar` scrive già a `AVATAR_LATO` (128px) e
  `miniatura_jpeg` non ingrandisce mai, quindi la «miniatura» usciva
  della STESSA misura, cioè una copia; e nessuno la chiedeva, perché
  il `_min` lo deriva solo `fotoMini` per le foto degli annunci
  mentre `avatarImg` usa il nome pieno. L'altra metà del guaio era
  che `_scrivi_avatar` cancellava il francobollo vecchio ma non la
  sua gemella: un orfano a ogni cambio di foto profilo, e ora se ne
  vanno insieme (il pattern delle foto in `modifica()`). I file già
  sul disco li ha tolti `ripulisci_avatar_min.py`, girato in
  produzione: 0 gemelle rimaste, 613 file, avatar visibili — e il
  conto torna al file (688 − 75). Solo DOPO quella conferma la forma
  `av_..._min` è uscita da `NOME_FOTO`, ed è l'ordine da tenere se
  ricapita: finché quei file esistono sul disco sono roba pubblica, e
  toglierli dalla regex prima li farebbe sparire dalle facce di tutti.
  In `prove_foto()` il caso non è stato cancellato ma ha CAMBIATO
  LATO, da «si serve» a «non si serve»: è l'affermazione più forte
  delle due, e se un domani una gemella ricomparisse non sarebbe
  pubblica. Gli scrittori di `foto/` tornano tre. Non era un guasto
  visibile: nessuna immagine era rotta, si sprecava spazio e basta.
  L'alfabeto esadecimale degli avatar è legato a `secrets.token_hex`
  da una sentinella: cambiando generatore, TUTTE le facce
  sparirebbero in silenzio. IL 304 lo faceva StaticFiles, e senza
  rimpiazzo ogni foto sarebbe tornata a scaricarsi INTERA a ogni
  scadenza della cache: la formula dell'ETag (md5 di mtime-size,
  quella di Starlette) è ora `_file_con_etag` e la chiamano in due —
  `/foto` e le illustrazioni di Sfoglia — con la sentinella che
  verifica che resti UNA, o i due header divergerebbero e il 304
  delle illustrazioni smetterebbe di scattare in silenzio (e quello
  nacque da un caso vero). Le due cache restano diverse e giuste:
  revalidazione per le illustrazioni (nomi NON versionati), un giorno
  per le foto (versionati). Il middleware `cache_foto` è sparito:
  esisteva solo per mettere quell'header.
  LE ANTEPRIME DEI LINK (ago 2026): un link di Barattolo incollato su
  Telegram, WhatsApp o in un DM Nostr arrivava come una card vuota col
  titolo generico — dall'altra parte non c'è un browser ma un CRAWLER,
  che scarica i primi byte e non esegue una riga di JavaScript, mentre
  qui titolo, prezzo e foto nascono tutti da fetch + innerHTML. Le
  cinque rotte che servono `miniapp.html` (`/`, `/miniapp.html`,
  `/negozio/{chi}`, `/annuncio/{aid}`, `/sicurezza`) ci infilano ora in
  testa il loro blocchetto di meta: nessuna rotta nuova, la regola
  ferrea 3 non si tocca.
  LA REGOLA CHE HA APERTO IL CANTIERE: **un rimosso o uno in revisione
  NON raccontano niente di sé**, e ricadono sui tag GENERICI. Non è
  pignoleria — l'anteprima di Telegram resta in cache per giorni e
  viaggia RIPUBBLICATA da chi inoltra il messaggio, quindi un titolo
  finito lì dentro è un annuncio che continua a esistere in giro dopo
  che lo scudo anti-resurrezione l'ha spento: è lo stesso scudo, bucato
  da un'altra parte. Per questo la clausola sta nella WHERE di
  `_meta_annuncio` (dove non si può dimenticare) e la prova è
  ESEGUIBILE e non una sentinella sulla forma — il rimosso ci passa
  davvero, su un database vero, e il suo titolo si cerca nell'HTML che
  esce.
  IL VENDUTO INVECE HA LA SUA ANTEPRIMA VERA (decisione di Andrea): è
  uno SCAFFALE VUOTO, non un annuncio che non c'è — il link mandato a
  un amico non deve morire con le scorte, e la scheda esiste ancora
  (dal cantiere dello stock `/api/listings/{id}` serve
  `('attivo','venduto')`, spenta e col «rimetti in vendita» del suo
  venditore). Il confine dei due elenchi è LO STESSO, e una prova lo
  incrocia: quel che la scheda serve è quel che l'anteprima può
  nominare, o si manda in giro una bella card che poi atterra su un
  «non trovato». Ma la card non deve nemmeno MENTIRE, ed è il patto di
  `_caption_canale` che al venduto riscrive il post del canale: il
  «✅ Venduto ·» sta in TESTA alla descrizione, che è l'unico pezzo che
  nessuna piattaforma può troncare via. Fuori restano i due di sopra e
  l'annuncio che non esiste.
  IL BLOCCO VA IN CIMA, subito dopo `<meta charset>` — che per
  specifica deve restare nei primi 1024 byte, e quindi si resta suoi
  vicini invece di prendergli il posto: la pagina pesa quasi 900 KB e
  parecchi crawler smettono di scaricare molto prima della fine
  (misurato: l'ultimo meta cade al byte ~1300, li leggono tutti).
  SI LAVORA SUI BYTE e non sul testo, ed è la riga che sembra un
  dettaglio: la modalità testo normalizza i fine-riga, cioè 15 KB di
  differenza su ciò che scarica OGNI utente come effetto collaterale di
  un ornamento. `SEGNO_META` per la stessa ragione non nomina il
  fine-riga (sul VPS è `\n`, sul portatile di chi scrive `\r\n`) e ci
  si infila subito dopo il `>`. C'è la prova che la pagina esce
  identica al file, byte per byte.
  UN ORNAMENTO NON MANDA GIÙ IL MERCATINO, due volte: se il segno non
  si trova più (qualcuno ha ritoccato le prime righe di miniapp.html) i
  meta si perdono e la pagina VIVE — mai appesi in fondo, che sarebbe
  peggio del niente —, e `_meta_o_generici` è la cintura fail-open su
  qualunque cosa vada storta nel costruirli. Il template si legge una
  volta e resta in memoria spezzato in due, col timbro `(mtime, size)`:
  in sviluppo basta salvare il file perché la pagina cambi.
  L'IMMAGINE è il FRANCOBOLLO `_min` dell'annuncio — già la misura
  giusta per ogni piattaforma (640 quadrati, ~175 KB: dentro i limiti
  di Telegram, WhatsApp e Facebook, verificati) — col pieno come
  ripiego e il brand come ripiego del ripiego, perché un `og:image` che
  non risponde è PEGGIO di nessun og:image: diversi crawler, non
  trovandolo, non disegnano la card affatto. Per il NEGOZIO è sempre il
  brand: l'avatar è un francobollo da 128px, sotto il minimo delle card
  — ed è `icona-512.png` e non l'hero, che è l'UNICO asset di casa con
  l'alpha (un barattolo scontornato lo comporrebbe ogni client sul
  fondo che gli pare). `og:image:width`/`height` si dichiarano SOLO sul
  brand, dove le sappiamo: il lato del francobollo dipende dalla foto
  (`min(MINIATURA_LATO, lato corto)`) e un numero sbagliato è peggio di
  uno assente.
  E SOLO LE NOSTRE FOTO (ago 2026, M2 dell'audit): un URL remoto in
  colonna è l'host di chi pubblica su Nostr, e ci resta proprio quando
  lo scaricamento FALLISCE — cosa che chi pubblica può provocare (un
  403, un redirect, un corpo sopra il tetto). Messo in `og:image`
  quell'indirizzo diventa la CAMPANA di chiunque veda l'anteprima: ci
  bussano il crawler di ogni piattaforma e, nei client che risolvono
  l'immagine, il telefono di gente che Barattolo non l'ha mai aperto —
  ed è sostituibile DOPO la condivisione, a card già in giro. Quindi
  `_immagine_anteprima` lo SALTA e ripiega sul brand, e il salto è un
  `continue` e non un `return`: se sotto c'è una foto nostra la prende
  lo stesso.
  IL CLIENT IN VETRINA NON SI TOCCA, ed è una divergenza VOLUTA fra
  due superfici: lì `fotoMini` lascia passare l'URL intero (decisione
  già presa e dichiarata), perché quell'immagine la chiede il browser
  di chi ha APERTO una scheda, non quello di chiunque riceva un link.
  C'è una prova per lato, così nessuna delle due si sposta per
  distrazione credendo di allinearsi all'altra.
  IL `<title>` ORA SI TOCCA, e questa riga ROVESCIA quella che stava
  qui («non si tocca: dove conta og:title ha comunque la precedenza»).
  Era giusta quando l'unico pubblico erano i crawler social — lì
  og:title vince davvero — ed è diventata falsa il giorno in cui il
  pubblico sono anche i motori di ricerca, per cui il `<title>` è il
  segnale più forte che una pagina abbia. Vedi «FARSI TROVARE».
  L'og:url del negozio porta il CODICE letto dal database e mai il `chi`
  arrivato dall'URL; il tg_id serve solo a contare gli annunci e non
  esce (prova apposta). Tutto passa da `html.escape(quote=True)` — qui
  il testo dell'utente sta in un ATTRIBUTO, non in un nodo — e la prova
  non cerca le entità ma che il blocco resti fatto di attributi INTERI
  e rileggibili.
  IL PREZZO È IL LISTINO anche con una lampo viva, deliberato:
  l'anteprima resta in cache per giorni, quindi una cifra a tempo ci
  sopravviverebbe — meglio dire il prezzo che non scade che promettere
  uno sconto finito.
  FARSI TROVARE (ago 2026): l'Open Graph qui sopra risolve un problema
  VICINO MA DIVERSO — fa la card quando qualcuno incolla un link in
  chat, cioè serve un crawler GIÀ INVITATO. Chi cercava «bici usata
  Carmagnola» su un motore non ci trovava, e non ci avrebbe trovati
  mai: le card erano `<div onclick>` (nessun collegamento da seguire),
  il `<title>` era la stessa riga su tutto il sito, e il corpo della
  pagina era vuoto per chi non esegue JavaScript.
  1) INDIRIZZI PARLANTI `/annuncio/{id}-{slug}` e
  `/negozio/{chi}-{slug}`, con **l'id PRIMA** e lo slug come ornamento:
  è quella forma a rispondere da sola alle quattro domande — il titolo
  può cambiare (cambia lo slug, non l'id), due omonimi non litigano, e
  i vecchi indirizzi continuano a servire la pagina giusta. NON con un
  301 (i browser lo cachano, Chrome anche per sempre, e su un titolo
  modificabile punterebbe a uno slug morto) ma con un `rel=canonical`,
  che consolida lo stesso segnale senza toccare la barra degli
  indirizzi né il motore di navigazione. `_slug` si appoggia a
  `normalizza`, che scioglie già accenti, emoji e «&» — e lo fa NELLO
  STESSO MODO del filtro parole, cioè in un posto solo; un titolo di
  sole emoji dà stringa VUOTA e l'indirizzo resta quello di sempre,
  mai con un trattino orfano in coda. NON riusare `_taglia_meta` per il
  troncamento: aggiunge il puntino di sospensione, che in un URL non ci
  va — sembra lo stesso mestiere e non lo è. `_slug` e `slug_categoria`
  restano DUE COSE (la seconda è il nome di un file su disco:
  cambiarla spegne 27 illustrazioni), e il legame si dichiara con una
  prova che oggi passa e diventerà rossa il giorno che qualcuno
  aggiunge una categoria con dentro una «&».
  UN NOME PUÒ ESSERE UN RECAPITO (ago 2026, caso vero dal campo visto
  da Andrea nella sitemap): parecchi venditori bitcoin si chiamano come
  il loro Lightning address, e `normalizza` lo scioglieva docilmente in
  `doc557-marshylift40-phoenixwallet-me` — un recapito di pagamento
  diventato indirizzo web. E la parte peggiore non è l'URL: è che la
  SITEMAP lo **proponeva attivamente** ai motori. Un conto è che un
  dato pubblico stia su una pagina, un altro è andarlo a offrire a chi
  indicizza.
  `_pare_recapito` guarda il testo GREZZO — dopo `normalizza` chiocciola
  e punti sono spazi, e un Lightning address è indistinguibile da una
  frase, quindi chi spostasse il controllo dopo lo renderebbe INERTE
  senza rompere niente di visibile (c'è la sentinella) — e ha tre
  trigger: la chiocciola da sola (mail e LN address hanno la stessa
  forma, e un «@qualcosa» è comunque una maniglia verso una persona);
  la forma `dominio.tld` contro un elenco di TLD; e **due punti o più**,
  che è la regola che NON dipende dall'elenco e prende la forma esatta
  del caso dal campo anche con un dominio di primo livello mai visto.
  LA GUARDIA STA DENTRO `_slug`, non nei chiamanti, e la ereditano per
  costruzione l'indirizzo dell'annuncio, quello del negozio, la
  sitemap, il canonical e il campo `slug` che il client riceve — più
  ogni strada futura. Vale per i TITOLI come per i nomi: un annuncio
  può contenerne uno.
  L'ELENCO È UN'EURISTICA, non una verifica — nessuno può sapere se
  «casa.it» sia un dominio o due parole — e si allunga senza cerimonie.
  Il verso in cui sbaglia è quello giusto: un falso positivo costa UN
  ORNAMENTO (l'indirizzo resta nudo e funziona identico), un falso
  negativo costa il recapito di una persona dentro l'indice. Misurato
  prima di accenderla sugli 888 annunci e sui 24 negozi veri: ZERO
  falsi positivi. IMPERFEZIONE DICHIARATA: un «N.B.Leggere» senza lo
  spazio dopo il punto viene preso dalla regola dei due punti.
  E il vecchio indirizzo già indicizzato non muore né si redirige: il
  canonical lo consolida sul codice nudo — è precisamente il motivo per
  cui il canonical era la scelta giusta invece del 301.
  LA LEZIONE DELLA TORTURA, che vale più della regola: il primo caso di
  prova per i «due punti» era `tizio.wallet.qualcosa`, e a prenderlo
  era l'ELENCO (`wallet` è un TLD) — togliere la regola dei due punti
  non faceva diventare rossa nessuna prova. Un caso di prova va scelto
  in modo che possa fallire solo per la ragione che si vuole
  sorvegliare, e a dirlo è stata la mutazione, non la rilettura.
  IL CANONICO DEL NEGOZIO È IL CODICE, non lo username: quello è
  dell'utente, che può cambiarlo o perderlo, e un canonical che si
  muove butta via il segnale lasciandosi dietro un 404. È anche già
  quello che l'og:url usava. Bonus gratis: la ricerca username è
  COLLATE NOCASE, quindi `/negozio/Rosina` e `/negozio/rosina` erano
  già oggi due indirizzi con lo stesso contenuto, e il canonical chiude
  un doppione preesistente senza una riga in più.
  LO SPACCO SUL PRIMO TRATTINO è senza perdita e non è una speranza:
  il codice è `token_hex(4)` e gli username Telegram sono
  `[A-Za-z0-9_]` — nessuno dei due può contenere un trattino.
  `/annuncio/{aid}` è passata da `int` a TESTO con `_id_da_percorso`,
  che usa una regex e non `int()`: `int("١٣")` fa 13 (cifre
  arabo-indiane), `int("1_3")` pure (il trattino basso è un separatore
  legale), `" 5"` e `"+5"` passano, e `"9"*30` diventa un intero che
  sqlite3 rifiuta con OverflowError. Il tetto a nove cifre chiude anche
  la superficie «URL infinita che consuma query»: da quando la rotta
  accetta testo lo spazio degli indirizzi è illimitato, e ciò che non è
  un id torna indietro a ZERO letture del database. Cambio dichiarato:
  `/annuncio/pippo` era un 422 di FastAPI e ora è una pagina che si
  apre col noindex — un 404 sarebbe contro la costituzione fail-open
  del blocco.
  LA REGRESSIONE PIÙ GRAVE ERA INVISIBILE ALLE PROVE DEL SERVER: il
  client leggeva `/^\/negozio\/([^/]+)/` e avrebbe passato
  `ab12cd34-la-bottega` intero all'API, che confronta ESATTO — 404,
  cioè IL NEGOZIO NON SI APRE PER UNA PERSONA VERA mentre i meta sul
  crawler erano perfetti. Rimedio DOPPIO e vanno fatti tutt'e due:
  `/api/negozio/{chi}` spacca lato server (totale e idempotente) e la
  regex client diventa `([^/-]+)` — col trattino in FONDO alla classe,
  o diventa un intervallo e si rompe in silenzio. Per `/annuncio/` non
  serviva niente: `(\d+)` **non è ancorata in coda**, quindi digeriva
  già lo slug — ma è congelata da una sentinella, perché chi la
  «stringe» con un `$` ammazza ogni link parlante senza un errore.
  2) UN TITOLO PER PAGINA (vedi il rovesciamento qui sopra), e col
  titolo il canonical e il meta robots. `_pagina_con_meta` è passata a
  TRE FESSURE — meta, titolo, corpo — col nome INVARIATO, perché la
  sentinella delle rotte pubbliche cerca proprio quel nome. Il
  marcatore del corpo è un `<div id="cartello"></div>` VUOTO fra
  `<body>` e la prima vista, e l'invariante che rende sicuro il taglio
  è che **il tag di chiusura siano i byte immediatamente successivi
  all'apertura**: così senza iniezione l'uscita è LETTERALMENTE il
  file, e il giorno che qualcuno ci mette dentro qualcosa a mano la
  fessura si chiude e la pagina esce intatta invece che mescolata.
  Fail-open per fessura e IN ORDINE DI FILE: quando l'ordine si rompe
  si spegne sempre quella più a valle. `b"".join` e non `+=`: con `+=`
  su bytes si pagano quattro copie da 900 KB a richiesta, ed è la sola
  voce di costo CPU del cantiere. `titolo=""` vuol dire «non toccare il
  titolo», non «titolo vuoto» — è ciò che fa ricadere ogni cintura
  esattamente sul comportamento di ieri.
  3) COLLEGAMENTI VERI E MAPPA. Le card sono `<a>`: l'`<a>` avvolge
  foto e testo, i due BOTTONI (barattolino e rifornimento) restano
  FUORI — contenuto interattivo dentro un `<a>` è HTML non valido —
  mentre il badge di stato, che è un `<div>`, resta DENTRO, così le sue
  cinque regole CSS non si toccano. `.card{position:relative}` è
  OBBLIGATORIA: senza, i bottoni risalgono fino al blocco iniziale e
  TUTTI i barattolini della pagina si accatastano in alto a destra —
  e la trappola crudele è che **nel carrello sembrerebbe giusto**
  (`.pacco-cella` è già relative), quindi si prova lì, si conclude che
  va bene, e la vetrina è devastata. C'è la prova.
  IL CLICK: ctrl/cmd/shift e i tasti non-sinistri restano al browser
  (scheda nuova: è il guadagno voluto), il tocco normale fa
  `preventDefault` e apre in pagina. La ROTELLINA non passa nemmeno di
  qui — i browser mandano `auxclick`, non `click` — e NON va
  «aggiustata». `preventDefault` PRIMA di `openDetail`: invertirli vuol
  dire che un'eccezione ricarica 910 KB per davvero. Gestore INLINE e
  non delegato, perché `cardHTML` è la fabbrica unica e copre da sola i
  SETTE posti che disegnano card, compreso «Esauriti di recente» che
  vive in una griglia creata al volo.
  LO SLUG ARRIVA DAL SERVER (`arricchisci_righe_vetrina`, il collo di
  bottiglia di tutte e sei le rotte-card) e NON si ricalcola nel
  client: sarebbe il secondo posto da tenere allineato per sempre, e
  divergerebbe il giorno che il server cambia la traslitterazione.
  `slugCat` invece resta, ed è giustificato: serve a calcolare offline
  il nome di 27 file di illustrazione. C'è la sentinella d'architettura
  che vieta il gemello.
  4) IL CARTELLO nel corpo: titolo, prezzo, descrizione, foto e i
  COLLEGAMENTI INTERNI, che sono metà del valore — sono il modo in cui
  un crawler scopre ottocento annunci, ed è l'unica ragione per cui le
  pagine categoria esistono. Non è testo nascosto: è un pre-render
  vero, tolto dal client DURANTE il parse con uno scriptino adiacente
  al marcatore (non in fondo a 910 KB, o su rete lenta resterebbe a
  schermo per decine di ms). `?.remove()` senza ramo d'errore, più
  `#cartello:empty{display:none}` come cintura. MAI un `display:none`
  permanente: sarebbe un'altra cosa. IMPERFEZIONE DICHIARATA: Google
  indicizza il DOM RENDERIZZATO, quindi se un domani l'app non
  riuscisse a disegnare, il DOM sarebbe vuoto — oggi non può
  succedere (`avvia` cade in `avviaVetrina`, che cade in DEMO, e tutte
  e tre disegnano), e la via d'uscita è una riga: legare la rimozione
  al primo `go()` invece che al parse.
  27 PAGINE `/categoria/{slug}`, vocabolario CHIUSO su `SLUG_CATEGORIE`
  (uno slug inventato non diventa mai una query). Le piastrelle di
  Sfoglia sono `<a>`, e ATTERRARE SU UN REPARTO NON È UNA DISCESA: il
  tocco sulla piastrella viene DA Sfoglia e alza `navSpingi`, ma
  arrivarci da un motore non viene da nessun posto nostro e l'indietro
  deve riportare a chi ci ha mandati — quindi `apriCategoriaDaUrl` non
  tocca MAI `navSpingi`. `navRiflette()` a mano invece è OBBLIGATORIO:
  cambiare `ramoVetrina` e `activeCat` non tocca nessuna classe, quindi
  l'osservatore del motore non scatta e la cronologia continuerebbe a
  raccontare il mercatino intero. E servono DUE funzioni:
  `preparaCategoriaDaUrl` è SINCRONA e sta prima del primo giro di rete
  (così `paramsVetrina` scarica subito il reparto giusto, una richiesta
  sola invece di una vetrina intera buttata via), `apriCategoriaDaUrl`
  è il finale e va chiamata in ENTRAMBI gli avvii — dimenticarla in
  `avviaVetrina` vuol dire che funziona in Telegram e in collaudo e
  NON funziona esattamente per chi arriva dai motori.
  5) COSA RESTA FUORI. ROBOTS.TXT GOVERNA LA SCANSIONE, IL META ROBOTS
  L'INDICIZZAZIONE, e si confondono ogni volta: da cui la regola senza
  eccezioni — **non si blocca in robots.txt ciò che si vuole
  deindicizzare**, perché una pagina vietata non viene mai scaricata,
  quindi il suo noindex non viene mai letto, e Google indicizza lo
  stesso l'indirizzo nudo se qualcuno ci linka. Bloccare è l'unico modo
  affidabile di rendere una pagina NON deindicizzabile. In robots.txt
  c'è solo `/api/` (è JSON e non potrebbe portare un meta tag); NON si
  vietano `/annuncio/`, `/negozio/`, `/categoria/`, `/miniapp.html` né
  `/foto/`, e MAI «Disallow: /» perché siamo in rodaggio — il recupero
  si misura in settimane. La rotta è una costante PURA, senza database
  e senza modo di sollevare: un 5xx lì sospende la scansione di tutto
  il sito per ore. `noindex,follow` (mai `nofollow`) va su
  `/miniapp.html`, sugli annunci assenti/rimossi/in revisione — dalla
  STESSA condizione che produce già i meta generici, mai da un secondo
  «if» —, sui negozi vuoti o senza codice, sui reparti vuoti o finti, e
  su `offline.html`, che non passa da `_pagina_con_meta` e se lo scrive
  a mano. NOINDEX E CANONICAL NON CONVIVONO: su una pagina
  deindicizzata un canonical che punta ALTROVE può propagare il noindex
  all'indirizzo canonico — quindi `/miniapp.html` porta solo il
  noindex, mai un canonical verso «/».
  LA SITEMAP e il noindex NON POSSONO CONTRADDIRSI (Search Console lo
  segnala), quindi le due condizioni nascono dallo stesso fatto e c'è
  una prova che lo verifica pagina per pagina, chiamando il costruttore
  di ogni `<loc>`: è quella di maggior valore del cantiere. Dentro:
  home, `/sicurezza`, i reparti e i negozi con almeno un attivo, e
  tutti gli attivi. Fuori i VENDUTI (decisione di Andrea: il loro link
  non muore e la pagina resta indicizzabile, ma non siamo noi a
  proporla), i rimossi, quelli in revisione. Il `<loc>` è l'indirizzo
  CANONICO con lo slug, o si consegna a Google un rapporto di contenuti
  duplicati scritto di proprio pugno. `<lastmod>` = max(modificato,
  creato): `modificato` è 0 su quasi tutte le righe, e uno ingenuo
  daterebbe l'intero catalogo al 1970. `changefreq` e `priority` si
  omettono (Google dichiara di ignorarli). Il tetto dei 50.000 SI
  DICHIARA e non si costruisce: siamo sotto il 2%, c'è il `LIMIT`, un
  print d'allarme e la via d'uscita già scritta nel commento.
  GLI IMPORTATI DA NOSTR SI INDICIZZANO COME TUTTI (decisione di
  Andrea): nessuna eccezione e nessun ramo. Chi pubblica sui relay ha
  già scelto la propagazione, e se cancella l'evento la riga si spegne
  anche qui — il meccanismo esiste già, è quello delle lapidi NIP-09,
  e porta l'annuncio a `rimosso`, cioè dentro il noindex e fuori dalla
  sitemap SENZA una riga nuova. Il canonical di un importato punta alla
  NOSTRA pagina, mai all'esterno: siamo canonici del nostro URL, non
  della merce.
  6) JSON-LD `Product` + `Offer`, solo sugli annunci pubblici (su un
  rimosso sarebbe il bug della resurrezione in smoking). **sats → BTC è
  una conversione ESATTA di unità**, non un tasso — schema.org ammette
  i codici delle criptovalute — quindi qui non si inventa nessun
  numero; ma il valore va prodotto SENZA virgola mobile, che `sats/1e8`
  fa uscire `0.0008000000000000001` per ottantamila sats. L'euro solo
  per i listini NATI in euro. Compromesso a verbale: i risultati
  «merchant» di Google validano su una lista di valute e BTC non c'è —
  i listini in sats potranno essere mostrati senza prezzo, quelli in
  euro sono pienamente idonei. `come_nuovo` → `UsedCondition` e NON
  `RefurbishedCondition`: «ricondizionato» significa rimesso a nuovo
  professionalmente, ed è la mappatura sbagliata che verrebbe naturale;
  dove la scala non dice niente la proprietà SI OMETTE, e il giudice è
  `condizione_da_mostrare`. Ferie → `OutOfStock` + `availabilityStarts`
  con la data di rientro: l'oggetto c'è e il prezzo è vero, ma oggi non
  si compra, e chi arriva da un motore deve saperlo PRIMA di cliccare.
  MAI `aggregateRating` sul Product: quel voto è del VENDITORE, non
  dell'oggetto, ed è lo schema delle recensioni auto-attribuite che
  Google sanziona.
  I TRE REGIMI DI ESCAPE, che è la parte da non confondere: `_attr`
  (attributo), `_testo` (nodo: `<h1>`, `<p>`, **e il `<title>`**), `_ld`
  (dati strutturati). Il nome dice la DESTINAZIONE e non la tecnica, la
  lezione di `nome_pezzo`. Il terzo è quello che si sbaglia sempre:
  **dentro un `<script>` le entità HTML non vengono decodificate**, un
  `html.escape` lì non protegge niente e CORROMPE il dato (nel JSON
  comparirebbe `&amp;`), e l'unica cosa da neutralizzare è la sequenza
  che chiude l'elemento raw-text. IL TITOLO USCIVA CRUDO nella prima
  stesura — l'ha preso la prova, non la rilettura — e adesso c'è
  l'asserzione apposta.
  IL COSTO, misurato: +1,5 KB su un annuncio (+0,17%) e +6 KB su home e
  reparto (+0,66%) sopra i 910 KB di partenza. Query: `/annuncio` resta
  a UNA (stessa riga per meta, titolo e corpo — sbagliarlo la porta a
  due), `/miniapp.html` e `/sicurezza` restano a ZERO, `/robots.txt` a
  zero per costruzione, e la HOME passa da 0 a 2 dietro una cache di
  60s — è l'unico cambio di NATURA, sulla rotta più colpita di tutte.
  LA VOCE CHE NESSUNO GUARDA è la banda di scansione: con
  `HEADER_NO_CACHE` nessuno può conservare la pagina, quindi ~900 URL ×
  910 KB fanno **~820 MB per passata completa di Googlebot**. La cura
  tentante — `no-cache` con rivalidazione più un ETag sulla pagina —
  NON può riusare `_file_con_etag`: i byte ora dipendono dalla rotta E
  dal database, e `mtime-size` servirebbe un 304 su una scheda ormai
  cambiata; sarebbe una seconda formula, cioè la sentinella dell'ETag
  unico che si mette a urlare. Rimandata, e scritto qui.
  E DA QUI È NATO `_fmt_eur` (ago 2026): **un euro si scrive in un modo
  solo in tutta l'app**. Gemello di `_fmt_sats`, con la VIRGOLA dei
  decimali — col punto una cifra grande si legge per un fattore mille —
  e ci passa OGNI posto dove un euro diventa testo per una persona:
  `_prezzo_promo` (post del canale, note Nostr, anteprime),
  `_cifra_offerta` (notifiche delle offerte), `testo_prezzo` (le
  notifiche ai moderatori) e i due avvisi gemelli del drift del cambio.
  Il CLIENT lo diceva già giusto per conto suo (`fmtEur`,
  `toLocaleString('it-IT')`): il server era l'unico fuori riga, e la
  correzione è una convergenza, non una convenzione nuova.
  NON ci passano — e non è una dimenticanza — i valori dei TAG NIP-99
  (`price`, `delivery`), che non sono testo per una persona ma campi di
  protocollo che `importa_nostr` rilegge: lì il punto decimale è la
  SPECIFICA. Per la stessa ragione restano col punto le due righe di
  prosa del content (`Prezzo:`, `spedizione:`), che stanno nello stesso
  evento dei tag e li ripetono a parole — divergere da loro sarebbe
  peggio —, e la riga del catalogo che va in pasto ad Haiku, che una
  persona non legge. Il CSV la virgola ce l'ha già per conto suo.
  LA SENTINELLA che rende il principio verificabile invece che
  raccomandato conta tre cose: zero `:.2f} €`, tre `:.2f} EUR` (i soli
  che una persona non legge) e otto `:.2f}` in tutto, che è il
  censimento completo dei superstiti. Serve perché QUESTA FAMIGLIA SI
  NASCONDE: cercando il solo `€` il primo censimento ne aveva mancati
  tre, tutti che scrivevano «EUR» a parole, ed è stata la sentinella a
  prenderli — non la lettura del codice. Se quei numeri cambiano, o è
  nato un campo di protocollo nuovo, o qualcuno ha ricominciato a
  scrivere un euro a mano.
  E UN SATOSHI SI SCRIVE IN UN MODO SOLO (ago 2026, il giro dopo):
  `_fmt_sats` esisteva da sempre ma metà dell'app lo scavalcava, e i
  formati in giro erano **quattro** — `509000` grezzo, `509.000` dal
  giudice, `509,000` con la virgola INGLESE di `{n:,}`, e `509 000`
  con lo spazio fatto a mano. Ora ci passano tutte e 33 le cifre che
  una persona legge come parole di Barattolo (notifiche, avvisi ai
  moderatori, polso ordini, messaggi d'errore, memo della invoice).
  RESTANO FUORI QUATTRO, e sono la stessa famiglia delle eccezioni
  dell'euro: una riga di journal (log diagnostico, un lettore solo),
  la riga del catalogo che va in pasto ad Haiku, e le due righe di
  prosa del NIP-99 che ripetono i tag a parole.
  E IL RIFIUTO DI `paga_venditore` HA TRE MOTIVI, non uno, e ognuno
  vuole le sue parole: una bolt11 che non si decodifica NON «chiede
  None sats» — è **illeggibile**, e l'avviso lo dice. Sembra cosmesi e
  non lo è: chi legge quel 🧊 deve capire al primo sguardo se ha
  davanti un wallet rotto o un tentativo di prelievo, che sono due
  mestieri diversi. La cifra vera resta dov'era negli altri due casi
  (importo sbagliato, dovuto zero), e c'è una prova per ciascuna.
  `_fmt_sats` NON SOLLEVA PIÙ, ed è la riga da non togliere: da lì
  passano le cifre delle NOTIFICHE, e parecchie vivono dentro un
  `try/except` che protegge qualcosa di più importante — l'avviso ai
  moderatori di un pagamento rifiutato sta apposta sotto `except`
  perché una notifica non deve mai rompere un rifiuto. Il prezzo di
  quella scelta è che un formattatore che alza le mani lì dentro non
  fa un errore: **fa sparire l'allarme, in silenzio.** È successo
  davvero durante il cantiere — `importo_invoice` torna `None` sulla
  bolt11 illeggibile, e con `f"{None:,}"` l'avviso «importo storto»
  (o un wallet rotto, o un tentativo di prelievo) non partiva più. A
  prenderlo è stata la prova della cintura di `paga_venditore`. Su
  qualunque cosa non sia un numero si ripiega su `str()`, che è anche
  esattamente quel che si vedeva prima.
  LA SENTINELLA RICUCE LE STRINGHE SPEZZATE prima di cercare, e non è
  un vezzo: è nella piega — «… {netto} "» a capo «"sats …» — che due
  siti si erano nascosti al censimento a mano, ed è la stessa trappola
  dell'euro che si nascondeva dietro «EUR» a parole. Una sentinella che
  non guarda lì dentro certifica una pulizia che non c'è.
  DIVERGENZA DICHIARATA COL CLIENT, e non è una svista — **decisione di
  Andrea, ago 2026: due superfici, due vincoli**. Il server usa i
  PUNTINI (`509.000`), il client lo SPAZIO STRETTO U+202F (`509 000`),
  e il perché sta nella voce del toggle valuta — col separatore normale
  il mono di casa spezzava «905 000» in due blocchi lontani. È una
  ragione di RESA che in una notifica Telegram non esiste, quindi le
  due convenzioni convivono con un motivo, e la regola «un formato
  solo» vale DENTRO ogni superficie e non attraverso. Chi volesse
  uniformarle sappia che è una decisione di prodotto e non un riordino:
  la leva è `_fmt_sats`, e cambia l'aspetto di ogni notifica, nota
  Nostr e post di canale in un colpo.
  E CHI ESTRAE UNA FUNZIONE NE EREDITA LE DIPENDENZE (lezione ripagata
  qui): tre ambienti finti di `prove.py` montavano `paga_venditore` e
  `_sblocca_sats` senza `_fmt_sats`, e sono esplosi. Il rimedio è
  `reale(nome)` accanto a `pezzo()`, che dà il pezzo VERO invece di uno
  stub — perché il primo stub scritto a mano sollevava sul `None`
  esattamente come l'originale prima della cura, cioè imitava anche il
  bug, e la prova restava rossa a guasto riparato.
  ATTENZIONE AL COLLAUDO: Telegram e WhatsApp cachano le anteprime a
  lungo e non si bustano dal nostro lato, quindi si prova con URL
  USA-E-GETTA prima di condividere qualcosa di vero — e a farlo c'è
  `anteprime.py` (vedi più sotto), che ridisegna la card come la
  vedrebbe ognuno.
  Frontend: prima pagina da 30 (`LIMITE_PAGINA`) e
  scroll infinito con sentinelle + IntersectionObserver (vetrina,
  negozio, tuoi annunci; guardie DENTRO le callback: demo, ricerca
  AI, fine lista). ATTENZIONE alla separazione: `vetrina` = pagine
  accumulate, ciò che la griglia disegna; `listings` = CATALOGO per
  openDetail, ci confluiscono negozio/risultati AI/deep-link SENZA
  sversare in griglia (`inCatalogo` update-or-push; in DEMO stesso
  array, e chi riassegna `listings` in demo deve riallineare
  `vetrina`). Append con insertAdjacentHTML (niente flicker); i
  rebuild pieni di valuta/cambio ridisegnano l'accumulato; categoria
  e ricerca ripartono dalla prima pagina (setCat/doSearch rifanno
  `loadListings`). Le card montano la `_min` con ripiego `data-full`
  sull'originale via onerror + dataset (MAI l'URL dentro una stringa
  JS interpolata: è il patto anti-XSS del filtro-alfabeto); galleria
  del dettaglio lazy dopo la prima foto.
  IL GIRO DELLA VETRINA (lug 2026, da un bug vero: entrando in una
  categoria da Sfoglia ogni annuncio compariva DUE volte). Non era la
  griglia disegnata due volte — `renderGrid` riscrive sempre
  l'`innerHTML` — ma la PAGINA DOPO che arriva in ritardo e si
  appiccica in fondo a una griglia già rifatta da un'altra vista:
  `apriCategoria` svuota la griglia, quindi la sentinella si SCOPRE e
  chiede la pagina successiva col cursore della vista PRECEDENTE mentre
  la prima pagina della categoria è ancora per strada. E su una
  categoria piccola quella «pagina dopo» è ESATTAMENTE la prima — il
  cursore globale è più recente di tutti i suoi annunci, quindi il
  `creato <` li prende tutti. Il rimedio è `vetrinaGiro`, un numero che
  avanza a ogni ricarica di PRIMA pagina: `loadListings` lo fa avanzare
  e azzera SUBITO `vetrinaCursore` (la sentinella scoperta non ha più
  niente da chiedere e tace da sola), e tutte e due le funzioni buttano
  la propria risposta se il giro è cambiato — il che para anche i due
  tocchi svelti su due categorie: vince l'ultima, senza mescolare.
  REGOLA: chi aggiunge una vista paginata (negozio, miei) e la svuota
  prima di ricaricarla deve darle il suo giro, o si ricompra questo bug.
  Modifica annuncio (lug 2026): `POST /api/listings/{id}/modifica` —
  solo il proprietario su annunci attivi, 400 se esiste un ordine NON
  terminale (anche `creato`: chi sta pagando deve trovare l'annuncio
  com'era) e per gli annunci importati da Nostr (contatto_nostr pieno:
  l'import orario li sovrascriverebbe). Ripassa TUTTI gli strati di
  moderazione come una pubblicazione nuova — ma la modifica APPROVATA
  NON avvisa piu' i moderatori (ago 2026, decisione di Andrea: la
  «✏️» era rumore in un fiume gia' pieno e non chiedeva nessun gesto,
  visto che i tre strati l'avevano appena promossa). COSA NON SI
  PERDE, ed e' la ragione per cui si poteva togliere: il vietato
  blocca con la sua notifica, il dubbio manda in `stato='revisione'`
  e li' restano SIA la tastiera ✅/❌ di `avvisa_revisione` SIA la
  coda del pannello — che filtra per STATO e non per come ci si e'
  arrivati, quindi prende le modifiche senza una riga dedicata. Il
  fatto in se' resta scritto in `annunci.modificato`, che la scheda
  mostra. A sparire e' solo lo squillo. La modifica FIRMATA degli
  importati tiene ancora la sua «✏️🟣», che e' un altro evento (rara,
  e dice che abbiamo rispedito ai relay un evento firmato da altri);
  foto sostituite in blocco solo se il campo `foto` arriva (nomi
  versionati col timestamp anti-cache del browser, file vecchi
  cancellati dal disco), altrimenti restano; ripubblica su Nostr con
  `solo_aggiornamento=True` (il tag `d` stabile sostituisce l'evento).
  Frontend: form di Vendi riusato e precompilato (banner «Stai
  modificando» + bottone che diventa «Salva le modifiche»), bottone
  ✏️ nel dettaglio e badge nei tuoi annunci; le foto attuali si
  tengono o si sostituiscono tutte, mai a pezzi.
  Modifica FIRMATA degli importati (lug 2026): il doppio cittadino con
  `npub_accesso` ≡ `contatto_nostr` modifica anche gli annunci
  importati — Barattolo fa da client Nostr, la nsec resta nel browser
  (regola 2). Due fasi: `POST /api/listings/{id}/modifica-firmata/
  prepara` (stesse guardie di modifica + moderazione COMPLETA prima
  della firma — dopo sarebbe teatro, l'import riporterebbe dentro —
  chiavi sempre confrontate via `npub_to_hex` sui due lati) risponde
  `{biglietto, evento, relays, collaudo}`: evento NIP-99 NON firmato,
  senza pubkey, `d` = `annunci.nostr_origine_d` (sostituzione NIP-99),
  `image` verbatim da `nostr_origine_foto` (ripiego `_foto_url_nostr`),
  content = descrizione PURA (MAI il footer promozionale: rientrerebbe
  in descrizione al giro d'import); biglietto in
  `BIGLIETTI_MODIFICA_NOSTR` (TTL 10 min: l'auth_url del bunker è
  lento). Il client: firma SENZA rituale quando può (lug 2026) —
  ordine: sessione bunker conservata → estensione `window.nostr` →
  foglio (`apriNostrSheet(scopo)` / `scopoFirmatario`, titolo «Firma
  con la tua chiave») solo come ultima porta o quando la strada
  automatica è morta/ha un'altra chiave (mismatch in auto = si
  ripassa dal foglio, non è un errore dell'utente). La sessione
  NIP-46 (URI bunker + chiave del CLIENT) vive in
  `localStorage['barattolo_bunker']` (`ricordaBunker`/`bunkerSalvato`/
  `scordaBunker`, salvata a ogni connect riuscito, scordata se il
  bunker non risponde): EQUIVALENZA DICHIARATA col secret NWC già
  conservato — pari grado, può chiedere firme al bunker (che può
  sempre negarle o revocare la sessione), MAI derivare la chiave
  dell'utente, mai sul server. La nsec incollata resta il rito di
  sempre (mai conservata, by design; il foglio suggerisce il bunker).
  I passi comuni vivono in `firmaEConsegna`: pubkey controllata PRIMA
  di firmare (la nsec si azzera dopo UNA firma), id ricontrollato in
  pagina (firmatario che altera = stop), pubblicazione dal browser
  (`pubblicaEventoSuRelay`, serve ≥1 OK, relay = quelli dell'IMPORT
  col relay personale del venditore, non RELAYS_VERIFICA) e SOLO poi
  `POST …/modifica-firmata` con `{biglietto, pubkey, sig}`: il server
  RICOSTRUISCE l'evento dal biglietto (divergenza impossibile),
  verifica Schnorr, ri-esegue le guardie economiche (TOCTOU) ma non la
  moderazione, aggiorna la copia locale dal payload del biglietto e
  rispedisce l'evento come backstop. Relay muti → niente POST, nulla
  cambia; POST fallito dopo i relay → messaggio onesto, l'import
  orario riconcilia entro un'ora (per gli importati i relay SONO la
  fonte di verità). Foto immutabili (v1, il form lo dice), solo kind
  30402, Telegram-only senza chiave → 400 di sempre. In collaudo anche
  il BROWSER simula la pubblicazione (flag `collaudo` da prepara:
  imparato quando il primo collaudo ha pubblicato sui relay veri).
  L'import (importa_nostr.py) per questo RICORDA le coordinate:
  colonne `annunci.nostr_origine_d` e `nostr_origine_foto` (URL image
  originali) scritte su INSERT e UPDATE, e il match verso il DB è
  PRIMA per tag `d` (sopravvive ai titoli cambiati: prima duplicava),
  poi per titolo ma solo su righe non ancora battezzate
  (`nostr_origine_d=''`); scudo anti-resurrezione (lug 2026, da un
  bug vissuto in produzione): se la coordinata (o il titolo) matcha
  una riga NON attiva — rimossa o venduta su Barattolo — l'annuncio
  NON si ricrea (skip con riga ⛔ nel journal): prima il match
  guardava solo gli attivi e l'evento ancora vivo sui relay rifaceva
  l'INSERT a ogni giro; un tag `d` diverso resta un annuncio nuovo.
  Cantiere cancellazioni COMPLETO (lug 2026, tappe 2-3): `interroga`
  chiede anche i kind 5 (NIP-09) del venditore e li rispetta —
  cancellazione vista su QUALUNQUE relay = riga locale spenta
  ('rimosso', ordini 'creato' annullati via `spegni_annuncio`,
  gemello della rimozione Mini App, riga 🪦 nel journal) e LAPIDE
  nella tabella `nostr_lapidi` (PK hexkey+d+event_id, creata
  dall'import), riletta TUTTA a ogni giro: vale per sempre anche
  quando i relay scordano il kind 5, e rispegne perfino una riga
  riaccesa da un rimborso (per questo niente return secco a mani
  vuote). Tag `a` per coordinata (solo 30402/30018 della SUA chiave),
  tag `e` per id: risolto in coordinata se l'evento è tra i letti,
  altrimenti matcha la colonna `annunci.nostr_origine_id` (scritta a
  ogni INSERT/UPDATE). Sotto lapide non si re-importa MAI più,
  nemmeno ripubblicando lo stesso `d` (imperfezione dichiarata: per
  tornare serve un `d` nuovo). Lo status sold di un evento
  aggiornato SPEGNE la riga come 'venduto' (riga 🏷️; prima restava
  attiva e COMPRABILE) — niente lapide, ma lo scudo la tiene spenta
  anche se lo status tornasse active (dichiarato, stesso rimedio);
  sul match aggiorna anche
  titolo/descrizione/zona e valuta/prezzo_eur dal tag price (EUR →
  doppia valuta anche per gli importati), MAI la categoria
  (categoria_automatica ricoprirebbe la scelta del form); foto
  invariate (stessi URL di `nostr_origine_foto`) = niente ri-download
  orario.
  Deduplica dei doppioni su Nostr (lug 2026): il doppio cittadino può
  avere lo stesso oggetto DUE volte sui relay — l'importato firmato da
  LUI e il nativo ripubblicato dalla piattaforma (invariante:
  `contatto_nostr` e `nostr_event_id` mai sulla stessa riga).
  `trova_doppioni_nostr` (guardia EXISTS: chi non ha importati esce
  subito, e quasi nessuno li ha) rileva le coppie con match STRETTO,
  mai fuzzy: impronta del titolo identica (token di `normalizza`
  ordinati alfabeticamente: maiuscole, accenti e ordine parole non
  contano) + prezzo compatibile (EUR vs EUR scarto ≤10%; altrimenti
  sats ≤30%, largo perché l'import riconverte l'importato a ogni giro
  mentre il nativo resta al cambio di pubblicazione). Pochi match
  certi: il falso positivo residuo (due esemplari genuini identici) è
  coperto dalla conferma esplicita e dall'archivio. Le coppie escono
  in `/api/me.doppioni_nostr` → cassetto «🔁 Doppioni su Nostr» nel
  Profilo (`renderDoppioni`, sparisce se vuoto/DEMO/VETRINA); dopo la
  fusione il messaggio del bot CONTA i doppioni trovati invece del
  sospetto generico. «Non è un doppione» = riga in
  `doppioni_ignorati` (server-side: mai riproporlo vale su ogni
  dispositivo, non è roba da localStorage). Il ritiro
  (`POST /api/me/doppioni/{id_nativo}/ritira`, conferma esplicita,
  MAI automatico) manda la NIP-09 della PIATTAFORMA sul SUO evento —
  gli eventi dell'utente non si toccano mai — via
  `ritira_da_nostr(esigi_ok=True)`: senza ≥1 relay OK non cambia
  NULLA (502 onesto, si riprova); col successo `nostr_event_id` si
  svuota, il che spegne ogni ripubblicazione (i ganci sono tutti
  `solo_aggiornamento=True`) e fa sparire la coppia da sola
  (derivata dai dati veri, niente stato sul successo). L'annuncio su
  Barattolo resta attivo, solo-locale. Il ritiro fire-and-forget di
  rimozione/admin usa la stessa funzione col default di sempre
  (azzera comunque).
  Formati foto: la miniapp converte in JPEG 1200px via canvas tutto
  ciò che il browser decodifica (WebP ovunque, HEIC su iPhone).
  FILIERA A UNA SOLA COMPRESSIONE (lug 2026): il JPEG del canvas
  (imageSmoothingQuality 'high' + qualità 0.9 — senza il filtro
  'high' il resize mangiava ~1/4 del dettaglio) viene salvato da
  `salva_foto` COSÌ COM'È, mai riconvertito; i formati che passano
  dal server (`converti_in_jpeg`: LANCZOS, quality 88 +
  `ImageOps.exif_transpose`, che il canvas fa da solo e Pillow no)
  subiscono anche loro UNA sola compressione. Chi tocca la filiera
  non deve MAI aggiungere un passaggio JPEG→JPEG sul file pieno
  (~-2dB a giro); la `_min` deriva dal pieno salvato ed è l'unica
  seconda generazione ammessa (è un francobollo). Ciò
  che non sa leggere (HEIC su Android/desktop) parte grezzo in base64
  (max 15MB; MIME normalizzato a image/heic se il sistema non lo
  dichiara — Pillow riconosce comunque i byte) e va SUBITO a
  `POST /api/foto/anteprima`: endpoint autenticato e STATELESS
  (niente disco né database prima della pubblicazione) che converte
  con Pillow e restituisce il JPEG — anteprima VERA appena scelta la
  foto, ed è lo stesso identico JPEG che poi si pubblica, già
  leggero. Se il server non può, la foto si RIFIUTA lì (vedi «nessuna
  foto sparisce in silenzio»); la conversione vera vive comunque anche
  in `salva_foto` alla pubblicazione, con Pillow+pillow-heif, dentro
  `asyncio.to_thread` e fuori dalla transazione SQLite: secondi di
  CPU che non devono congelare il server mono-processo. La strada
  libheif-WASM in pagina è stata valutata e scartata: ~1MB di blob
  inauditabile nel repo per un caso raro, contro 25 righe che
  riusano `converti_in_jpeg`. Import
  fail-open: senza `pillow` tutto come prima (JPEG passano, limite
  2.5MB), senza `pillow-heif` le HEIC si saltano — e dall'ago 2026
  l'AVVIO lo dichiara con una riga, il patto della chiave dei
  contenuti digitali: un fail-open silenzioso anche per chi guarda il
  server non è dichiarato, è solo silenzio. Con Pillow anche i
  PNG/WebP grezzi diventano JPEG veri.
  NESSUNA FOTO SPARISCE IN SILENZIO (ago 2026, caso dal campo: «carico
  un JPG dal computer, qualche mega, e non succede NULLA — nessun
  errore, nessun chip»). La causa NON era il canvas, ed è la prima
  cosa da sapere perché è dove si guarda per istinto: il percorso del
  selettore file regge tutto, misurato — 6000×4000, 20000×15000 (300
  Mpx, che Chrome sottocampiona da solo) e HEIC vere; il canvas di
  uscita è sempre 1200px, quindi non è mai lui a essere grande. Era il
  TRASCINAMENTO: `.photo-drop` è un riquadro tratteggiato che si
  chiama photo-drop e sul desktop chiede di essere usato così, e aveva
  il solo `onclick`. Senza un `preventDefault` sul `dragover` il
  browser non emette NEMMENO l'evento `drop` — quindi niente foto,
  niente chip, nessun errore e nessuna navigazione: il nulla esatto
  che l'utente descriveva. Ora i quattro gestori stanno sul riquadro
  (`fotoSopra`/`fotoLasciate`, classe `.sopra` mentre il file ci passa
  sopra) e `aggiungiFoto(files)` è la strada UNICA dei due gesti,
  che `fotoScelte` ora si limita a chiamare. «o trascinale qui» si
  mostra solo sotto `(hover:hover) and (pointer:fine)`: sul telefono
  quel gesto non esiste e prometterlo sarebbe una bugia.
  Con lui gli ALTRI QUATTRO SILENZI, che erano il vero tema: 1)
  l'errore dell'anteprima si ingoiava (`if (r.ok)` senza else) e in
  pagina restava il segnaposto «verrà convertita alla pubblicazione»
  — ora si legge `detail` e la foto si rifiuta, e quel chip NON ESISTE
  PIÙ: era una promessa che nessuno aveva verificato e che alla
  pubblicazione veniva disattesa in silenzio; 2) il `FileReader` che
  fallisce lo dice; 3) gli scarti di `salva_foto` erano `continue`
  muti — adesso la funzione torna `(nomi, scarti)` coi MOTIVI, la
  risposta di pubblica() e modifica() porta `foto_salvate` e
  `foto_scarti`, e `avvisoFoto()` li attacca in coda al toast di
  conferma (mai un secondo toast: coprirebbe quello del successo;
  `foto_salvate` assente = server di ieri e non si dice niente); 4)
  il file che immagine NON È si rifiuta subito col suo nome. Su
  quest'ultimo la lezione da tenere: il `data:image/jpeg` lo scrive il
  BROWSER deducendo il tipo dall'ESTENSIONE, quindi un PDF rinominato
  .jpg arrivava etichettato image/jpeg, passava la regex e finiva
  SCRITTO in `foto/` e servito come immagine (riprodotto). Due
  guardie: nel client, se il browser non ha saputo decodificare un
  formato che sa decodificare (jpeg/png/webp/gif/bmp per tipo O
  estensione) il file non è quel che promette e si rifiuta SENZA
  chiedere niente al server — solo le HEIC hanno bisogno di lui, e i
  tipi sconosciuti ci provano lo stesso, che Pillow legge i byte; nel
  server `_e_immagine` (Pillow `verify()`, fail-open senza Pillow), da
  cui passa tutto il non-HEIC prima di toccare il disco.
  INVARIANTE che ne esce, ed è ciò che tiene semplice il resto: in
  `sellFoto` c'è SOLO il chip `caricando:` o un JPEG vero.
  IL CORPO DELLA POST non ha tetto né in uvicorn né in Caddy (che di
  default non ne mette, a differenza di nginx), e misurato non è un
  problema: 5 foto scelte da 216 MB di originali fanno **1,53 MB** di
  POST — il ridimensionamento a 1200px è il livellatore. Il 413 ha
  comunque il suo messaggio, che è l'unico errore che l'utente ripara
  da solo togliendo una foto.
  Badge Nostr: colonna `utenti.npub` auto-dichiarata via `/api/me/npub`
  (formato bech32, rifiuta le nsec) + verifica con NOTA PUBBLICA:
  `/api/me/npub/verifica-avvia` genera un codice (vale 1h), l'utente lo
  pubblica in una nota kind-1 dal SUO client, `verifica-controlla`
  interroga 4 relay (websocket-client è sincrono: gira dentro
  `asyncio.to_thread`, relay in parallelo) → `utenti.npub_verificata`,
  badge 🟣. Dal lug 2026 il badge pubblico (card, dettaglio, negozio)
  esiste SOLO con la npub verificata, come 🟣 semplice senza ✓ (il
  non-verificato non compare in pubblico, quindi la spunta non
  distingue più nulla); la npub dichiarata ma non verificata la vede
  solo il proprietario nel suo Profilo, con l'invito a verificarla.
  Cambiare o rimuovere la npub azzera la verifica.
  Rimozione della npub (lug 2026): `salva_npub` con stringa vuota è
  l'unica strada; nel cassetto Identità c'è il bottone esplicito
  «🗑 Rimuovi la npub dal profilo» (confirm SEMPRE, con l'avviso in
  più se la chiave era anche npub_accesso; il campo svuotato + Salva
  delega lì). La rimozione toglie npub, verifica e — se coincideva —
  npub_accesso (solo tg_id>0, com'era già); il NATIVO Nostr (tg_id<0)
  con badge ≡ npub_accesso è BLOCCATO con 400 «è il tuo unico modo di
  entrare: collega prima Telegram» (guardia doppia frontend+server);
  se il badge del nativo è DIVERSO dalla chiave d'ingresso, la
  rimozione del badge è lecita e l'accesso resta. Dopo ogni
  cambio/rimozione che lascia l'utente senza destinazione Nostr (né
  accesso né badge verificato), `canale_notifiche` in
  ('nostr','entrambi') torna '' automatico — il cassetto Avvisi non
  deve mentire — e la risposta porta `canale_azzerato` (il 'telegram'
  esplicito non si tocca). Reinserire una npub, anche la stessa,
  riparte SEMPRE da non verificata. Le due leve del cassetto hanno il
  sottotesto che le distingue: «Disabilita l'accesso» chiude solo la
  porta del login (npub, badge 🟣 e ponte restano), «Rimuovi la npub»
  toglie tutto da ovunque; NIENTE terzo bottone «Scollega tutto» —
  Rimuovi fa già entrambe quando l'accesso è attivo, un doppione
  rimetterebbe la confusione che i sottotesti tolgono.
  `venditore_npub` e `venditore_npub_verificata` sono in `CAMPI_VETRINA`
  (pubblici per natura) e nelle SELECT di `/api/search` e
  `/api/listings/miei`.
  Avatar dal social di provenienza (lug 2026): colonne `utenti.avatar`
  (nome file, '' = iniziale), `avatar_aggiornato` e `avatar_scelta`
  ('' = automatico, la catena; oppure telegram | nostr | nessuna —
  la levetta binaria `avatar_visibile` è vissuta solo nei DB di
  collaudo, migrata e lasciata inerte). MAI link agli originali (gli URL del Bot API
  portano il TOKEN e scadono in un'ora; quelli Nostr regalerebbero
  l'IP di ogni visitatore a host terzi): si scarica la NOSTRA copia —
  francobollo 128px q85 (`_salva_avatar`, seconda generazione ammessa
  dal patto della filiera come le `_min`) in foto/ come
  `av_{negozio}_{ts}.jpg` (chiave = codice negozio pubblico, MAI il
  tg_id; nome versionato → la cache 1g di /foto lavora gratis, il
  file vecchio si spazza in `_scrivi_avatar`). `aggiorna_avatar`
  rispetta `avatar_scelta`: con '' vale la catena dei doppi cittadini
  — prima la foto Telegram (getUserProfilePhotos→getFile; chi la
  nasconde ai non-contatti resta con l'iniziale, ed è il suo modo di
  dire no), poi la picture del kind-0 dai 4 relay ma SOLO da chiave
  dal possesso dimostrato (npub_accesso o badge verificato: la regola
  di `notifica()`), scaricata con `url_foto_ammesso` + tetto 8MB —
  con telegram/nostr espliciti SOLO quella gamba senza ripiego (la
  scelta si rispetta: social senza foto = iniziale), con 'nessuna'
  non si scarica proprio; senza nulla la colonna si svuota e torna
  l'iniziale (foto sparita dal social = sparita anche da noi;
  imperfezione dichiarata: anche l'errore transitorio di rete svuota,
  ripara il rinfresco successivo). Rinfresco opportunistico in
  `/api/me` (diventato async per questo): al più ogni `GIORNI_AVATAR`
  (7), mai con 'nessuna', in create_task fail-open con anti-valanga
  `_AVATAR_IN_CORSO`; in collaudo la gamba Telegram esce None da
  bot_api simulato, quella Nostr legge i relay veri. Selettore «La
  tua foto» nel cassetto Identità (`POST /api/me/avatar-scelta`,
  pattern canale-notifiche: si accetta solo una sorgente che esiste,
  e ogni cambio ≠ nessuna rifà subito il francobollo): pillole solo
  per le sorgenti vere (mono-canale = la sua + «Nessuna», il
  selettore pieno è dei doppi cittadini), attiva = sorgente EFFETTIVA
  con «(automatico)» quando la scelta è vuota — l'automatico si
  mostra come Telegram anche quando la catena è ripiegata su Nostr,
  semplificazione dichiarata. «Nessuna» = iniziale ovunque per il
  pubblico, reversibile: `venditore_avatar` in
  CAMPI_VETRINA/CAMPI_MIEI/search e `avatar` nel profilo di
  /api/negozio escono col CASE su 'nessuna' (il nome file non lascia
  il server, il file resta in dispensa) — mentre tappo e testata del
  Profilo mostrano sempre la PROPRIA foto (vista privata, `avatar`
  da /api/me). Frontend: `avatarImg()` (filtro-alfabeto sul nome file)
  posa l'<img> sopra l'iniziale nei cerchi `.avatar` di dettaglio,
  negozio e Profilo (onerror la toglie: mai un'immagine rotta);
  `renderAvatar()` mette la faccia nel tappo (`.con-foto` spegne
  l'iniziale, onerror ripiega sul tappo di sempre e poi
  sull'iniziale). Ordini e card della griglia SENZA avatar (deciso);
  in DEMO iniziali e basta.
  Presenza Nostr della piattaforma: `NOSTR_NSEC_PIATTAFORMA` in config
  (segnaposto = funzione spenta, fail-open). Alla pubblicazione il
  server firma un evento NIP-99 (kind 30402, tag `d` stabile
  `barattolo-{id}`) con coincurve (Schnorr BIP-340) e lo manda ai 4
  relay (stesso pattern sync→`asyncio.to_thread` della verifica);
  venduto (ordine locked) → ripubblica `status sold`, rimborso →
  di nuovo `active`, rimosso → deletion NIP-09 (kind 5). La colonna
  `annunci.nostr_event_id` traccia l'ultimo evento; i ganci di
  aggiornamento agiscono solo se è valorizzata, così gli annunci
  importati (contatto_nostr pieno) restano fuori. Tutto in
  `asyncio.create_task`: mai errori né attese per l'utente. In
  collaudo gli eventi si firmano ma si stampano soltanto
  (`🟣 [nostr simulato]`).
  MA LA CHIAVE DELLA PIATTAFORMA È IL RIPIEGO, NON LA REGOLA (ago 2026,
  «IL BIVIO» dentro `annuncio_su_nostr`, ed è la riga che si legge per
  ultima e andrebbe letta per prima): se il venditore ha una chiave
  Nostr di cui ha DIMOSTRATO il possesso (`chiave_nostr_provata` =
  `npub_accesso`, o il badge `npub` verificato) l'annuncio esce sul SUO
  account e non sul nostro — è la sua reputazione, non la nostra. La
  nsec ce l'ha solo lui, quindi qui non si firma niente: si ACCODA in
  `firme_nostr` e a firmare è il BROWSER alla prima apertura
  (`GET/POST /api/me/firme-nostr`, biglietto + evento non firmato,
  `sollecita_firme_nostr` nell'orologio per chi non torna). Il bivio
  sta DENTRO il funnel e non nei chiamanti, così prima pubblicazione e
  aggiornamenti lo ereditano tutti. `annunci.nostr_autore` dice CHI ha
  firmato ('' = noi), ed è il campo da guardare prima di affermare
  qualunque cosa su chi controlla un evento. Da quel momento la
  piattaforma NON tocca più quell'evento: anche il ritiro passa da una
  firma sua (azione 'ritira' = kind 5 dal suo browser).
  Post automatici (lug 2026): la piattaforma racconta i fatti — ogni
  nuovo annuncio in vetrina esce da solo come nota Nostr kind-1
  (chiave piattaforma, tag `t=barattolo`, foto come URL nel content)
  e post nel canale Telegram (`TELEGRAM_CANALE_ID` in config, il bot
  deve esserne ADMIN; vuoto = solo Nostr). Leve in config:
  `POST_AUTOMATICI` (default TRUE, deciso: canali giovani, collaudo
  in produzione) e `POST_MAX_ORA` (6). Anti-spam: `accoda_promo` +
  drenatore a finestra (`_drena_promo`: 90s, 5s in collaudo) — fino a
  3 annunci con budget orario capiente = post singoli (pausa 2s),
  altrimenti UN solo aggregato «📦 N nuovi annunci» (la valvola:
  passa sempre, non nomina nessuno, niente ciclo di vita). Il
  drenatore RILEGGE dal DB: rimossi/venduti in finestra e importati
  (`contatto_nostr` pieno) non escono mai; l'import CSV accoda tutto
  INSIEME a fine creazione = sempre un aggregato solo. NON si
  annunciano: ordini e vendite (privacy delle parti), annunci
  importati (l'originale è già sui relay), modifiche. Ciclo di vita
  dei post singoli (colonne `annunci.post_canale_id`/`post_nostr_id`):
  venduto = edit del post Telegram col «✅ Venduto» (caption
  RICOSTRUITA da `_caption_canale`, mai salvata; al rimborso il ✅
  sparisce — il post non deve mentire), la nota Nostr resta (è storia
  vera); rimosso = deleteMessage + NIP-09 kind-5 sulla nota e colonne
  azzerate. Il ciclo di vita ignora la leva: agisce solo su post già
  fatti. `bot_api` ora RESTITUISCE il JSON della risposta (serve il
  message_id; in collaudo un finto id negativo da contatore, così
  anche edit e delete si collaudano). Fail-open totale, ganci DOPO i
  commit, coda in memoria (un riavvio la perde, accettato).
  Negozio del venditore: colonna `utenti.negozio` = codice pubblico
  casuale di 8 caratteri (migrazione per chi c'era, `verifica_utente`
  per i nuovi; stabile per sempre, NON deriva dal tg_id).
  `GET /api/negozio/{chi}` risolve `chi` prima come username Telegram
  (case-insensitive), poi come codice → `{venditore, annunci attivi}`,
  auth facoltativa stile vetrina (`venditore_id` solo agli autenticati,
  il tg_id non esce mai). `venditore_negozio` è in `CAMPI_VETRINA` e
  nelle SELECT di `/api/search` e `/api/listings/miei`. La route
  `GET /negozio/{chi}` serve la solita miniapp.html (no-cache): è il
  link condivisibile barattolo.store/negozio/{username|codice}.
  Login web dal browser: `POST /api/login/telegram` riceve i dati
  firmati dal Login Widget ufficiale e apre una sessione — tabella
  `sessioni` (in DB SOLO l'hash SHA-256 del token), cookie
  `barattolo_sessione` HttpOnly + Secure (fuori collaudo) +
  SameSite=Lax, 30 giorni (`GIORNI_SESSIONE_WEB`), purga
  nell'orologio. ATTENZIONE, due derivazioni di chiave DIVERSE:
  widget = `SHA256(BOT_TOKEN)` (`verifica_login_widget`, auth_date
  entro 5 min), Mini App = `HMAC("WebAppData", BOT_TOKEN)`.
  L'INITDATA SCADE (ago 2026, la seconda voce alta dell'audit): la
  firma dice CHI, non QUANDO, e finché nessuno leggeva `auth_date`
  un initData catturato apriva quell'account per sempre — ed è la
  credenziale di OGNI chiamata dentro la Mini App, non di una sola.
  Leva `ORE_INITDATA` (24; 0 = spenta, cioè il buco riaperto: freno
  d'emergenza, non una scelta). VENTIQUATTRO ORE E NON I CINQUE
  MINUTI DEL WIDGET, e la differenza è strutturale, non una
  taratura: il widget firma UNA volta e poi vive di cookie, mentre
  l'initData NON si rinfresca finché la WebView resta aperta — solo
  riaprire la Mini App ne conia uno nuovo. Con una finestra corta chi
  tiene Barattolo minimizzato verrebbe buttato fuori di continuo, e
  un pagamento a metà si spezzerebbe (la invoice vive 15 minuti). Il
  controllo sta FUORI dal `try` e PRIMA dell'INSERT, e sono due
  ragioni distinte: là dentro l'`except Exception` si mangerebbe
  l'HTTPException riscrivendola col messaggio generico, e una
  credenziale scaduta non deve scrivere sul database. FAIL-CLOSED per
  costruzione come `importo_invoice`: `auth_date` assente o
  illeggibile vale 0, cioè vecchio di un'era, cioè rifiutato, senza
  un ramo apposta. Il 401 della scadenza ha un messaggio SUO
  (`MSG_INITDATA_SCADUTO`) e non è pignoleria: un 401 dentro Telegram
  faceva cadere `avvia()` nella VETRINA anonima, dove ogni tocco
  offre di entrare a chi è già dentro e nessuno dice che basta
  riaprire — ora la vetrina resta (il mercatino si sfoglia lo stesso)
  ma `BANNER_SCADUTO` dice la verità, e il suo CTA verso il bot È il
  rimedio. Le sessioni cookie non c'entrano: hanno già la loro
  scadenza a 30 giorni.
  `verifica_utente(init_data, sessione)` cade sul cookie SOLO a
  header vuoto (initData invalido resta 401); ogni endpoint dichiara
  `barattolo_sessione: str = Cookie("")` esplicitamente — niente
  middleware che concede auth. `guardia_csrf` (middleware) può solo
  NEGARE: sui metodi non-sicuri via cookie esige Origin ≡ Host
  (tutte le rotte `/api/login/*` incluse). `POST /api/logout` chiude
  solo la sessione del browser corrente. Il ramo collaudo di
  `/api/login/telegram` (`{"collaudo": true}`) vale solo con
  MODALITA_COLLAUDO.
  Login web con Nostr: `GET /api/login/nostr/sfida` emette una sfida
  monouso (dict in memoria, TTL 5 min: uvicorn è mono-processo);
  `POST /api/login/nostr` verifica un evento kind-22242 stile NIP-42
  con `verifica_evento_login` (sfida bruciata PRIMA della firma, tag
  `relay` ≡ Host, id ricalcolato NIP-01, Schnorr con `PublicKeyXOnly`
  di coincurve — 503 se il pacchetto manca) e apre la STESSA sessione
  cookie del login Telegram. Anagrafica: l'utente Nostr ha `tg_id`
  NEGATIVO derivato dalla pubkey (Telegram usa solo id positivi:
  tutto il resto funziona invariato; `notifica()` salta gli id
  negativi) e c'è la colonna `utenti.npub_accesso` = la chiave che
  può entrare in quella riga (credenziale, distinta dal badge `npub`
  che è una dichiarazione; indice unico parziale; è il terreno della
  futura doppia cittadinanza). Ordine di ricerca al login:
  npub_accesso → npub già VERIFICATA su UN solo account Telegram
  libero (proposta di collegamento con biglietto monouso,
  `POST /api/login/nostr/collega`; rifiuto = login annullato, mai
  doppioni) → account nativo nuovo (nome = npub abbreviata, badge
  🟣 da subito: la firma Schnorr dimostra il possesso). Un badge
  NON verificato non dà MAI accesso all'account che lo dichiara.
  `hex_to_npub` (bech32 con checksum vero) è il gemello speculare di
  `npub_to_hex`. `vendor/nostr.bundle.js` = nostr-tools 2.23.12
  committato a versione bloccata e servito da `GET /vendor/nostr.js`
  (file singolo, MAI CDN: nessun terzo deve poter cambiare la pagina
  dove si può incollare una nsec).
  Doppia cittadinanza (lug 2026): le due direzioni del collegamento.
  Telegram→Nostr: `POST /api/me/npub/abilita-accesso` promuove il
  badge VERIFICATO a `npub_accesso` (indice unico = giudice: 409 se
  la chiave apre già un altro account, e il messaggio indirizza alla
  fusione); `disabilita-accesso` è il contrario ma RIFIUTA i tg_id
  negativi (un nativo si chiuderebbe fuori); `salva_npub` che cambia
  o rimuove il badge azzera anche `npub_accesso` se coincideva (solo
  su tg_id>0, stessa ragione). Nostr→Telegram: il bot per la prima
  volta ASCOLTA — webhook `POST /api/telegram/aggiornamenti`
  (`TELEGRAM_WEBHOOK_SEGRETO` in config, segnaposto = spento;
  confronto `hmac.compare_digest` sull'header
  X-Telegram-Bot-Api-Secret-Token; si registra da solo all'avvio con
  setWebhook, MAI in collaudo: un test locale col token vero non deve
  rubare il campanello alla produzione). Flusso: dal web
  `POST /api/me/collega-telegram` (solo id negativi) emette un codice
  monouso TTL 5 min (`CODICI_FUSIONE` in memoria), il frontend apre
  t.me/ilbarattolobot?start=CODICE, il bot risponde con la CONFERMA a
  tastiera inline (token in `CONFERME_FUSIONE`, valido solo per quel
  from.id: il codice è un bearer token, se il link trapela serve
  comunque il tocco giusto), e `esegui_fusione` fonde l'account
  nativo in quello Telegram in UNA transazione `BEGIN IMMEDIATE`:
  annunci+ordini+sessioni+feedback migrano (il browser Nostr resta
  loggato), la riga negativa MUORE PRIMA che `npub_accesso` si accenda
  sulla positiva (indice unico), contatori sommati, rating ricalcolato
  dai feedback migrati. `_guardie_fusione` (ricontrollate DENTRO la
  transazione) rifiutano: P già collegato, P con badge verificato
  DIVERSO, affari ancora aperti tra i due (auto-ordine in escrow).
  `bot_api()` è il gemello completo di `notifica()` ma in collaudo
  simula SEMPRE (`🤖 [telegram simulato]`); il webhook in collaudo
  accetta il segreto fisso "collaudo" per suonarlo con curl.
  `gestisci_update` fa `upsert_utente` sul mittente (che può non
  aver mai aperto la Mini App) e risponde con garbo a /start nudo
  e ai messaggi qualsiasi.
  Notifiche multi-canale (lug 2026): `notifica()` legge
  `utenti.canale_notifiche` ('' = automatico: Telegram se tg_id>0,
  DM Nostr per i nativi; oppure telegram | nostr | entrambi, scelta
  via `POST /api/me/canale-notifiche` che accetta solo canali
  raggiungibili). Il DM è NIP-17 (scelto su NIP-04, deprecato e coi
  metadati in chiaro: nel 2026 Amethyst, Damus, Primal, 0xchat & co.
  parlano tutti NIP-17): rumor kind 14 NON firmato → sigillo kind 13
  firmato dalla piattaforma → pacco kind 1059 firmato da una chiave
  effimera nuova per messaggio, date arretrate a caso ≤2gg. Cifratura
  NIP-44 v2 in `nip44_cifra`: ECDH con la coordinata X NUDA via
  `ChiavePubblicaCompleta.multiply` (MAI `PrivateKey.ecdh()` di
  coincurve, che la hasherebbe), HKDF con hmac/hashlib, ChaCha20 dal
  pacchetto `cryptography` (import fail-open: senza, canale spento).
  La npub di DESTINAZIONE è solo dal possesso dimostrato:
  `npub_accesso`, o il badge `npub` se VERIFICATO — mai un badge
  nudo (i dettagli degli ordini di Tizio finirebbero nella inbox di
  Caio). Consegna ai relay del kind 10050 del destinatario (cache
  1h in memoria) con ripiego sui 4 standard; il ramo Nostr gira in
  `asyncio.create_task` (mai bloccare: notifica() vive anche
  nell'orologio) con ripiego Telegram se il DM non parte e la chat
  c'è. `spoglia_html` toglie i tag Telegram dal testo del DM. In
  collaudo il pacco si cifra davvero ma si stampa (`💌 [dm nostr
  simulato]`). Frontend: cassetto «🔔 Avvisi» nel Profilo
  (`renderAvvisi`); il sottotitolo dice SEMPRE il canale effettivo
  («Ricevi gli avvisi su: …», con «(automatico)» quando è il
  default), pillole di scelta solo se entrambi i canali sono
  disponibili, testo statico altrimenti; senza canali raggiungibili
  sparisce l'intero cassetto.
  Ponti di contatto tra le parti (lug 2026): NON una chat — bottoni
  verso i canali che esistono. Pagina del NEGOZIO e dettaglio ordine
  mostrano «✈️ Scrivi su Telegram» (t.me/username) e/o «🟣 Scrivi su
  Nostr» (profilo su njump.me: il DM parte dal client dell'utente)
  secondo l'identità della controparte; il doppio cittadino li ha
  entrambi, senza canali resta la riga onesta «le trattative non sono
  necessarie: l'escrow protegge» (solo nell'ordine). Dal DETTAGLIO
  ANNUNCIO i ponti sono USCITI con le rifiniture del riordino (lug
  2026): ci si arriva entrando nella scheda del venditore, e il
  riquadro nel dettaglio resta solo anagrafica. La npub del ponte è
  SOLO dal
  possesso dimostrato — npub_accesso o badge verificato, la regola di
  `notifica()`; per l'ordine `/api/orders` aggiunge
  `compratore_nostr`/`venditore_nostr` (CASE in SQL, escono solo alle
  parti e all'admin come il resto dell'ordine). Helper frontend
  `pontiContatto`/`pontiOrdine` (il vecchio `bottoneChat` non esiste
  più); username e npub negli onclick passano dal solito
  filtro-alfabeto.
  Avvisi di ricerca (lug 2026): «dimmi quando esce quello che cerco» —
  tabella `avvisi_ricerca` (max 5 per utente, `MAX_AVVISI_UTENTE`:
  categorie serializzate '|A|B|' coi pipe ai bordi per il LIKE,
  comune+raggio 10/25/50/100 km, prezzo max in sats O in eur mai
  entrambi, parole normalizzate al salvataggio, `attivo` per la
  pausa) + `avvisi_notificati` (dedup PERSISTENTE: lo stesso annuncio
  non suona mai due volte per lo stesso utente, nemmeno dopo un
  riavvio o una modifica; purga a 30gg nell'orologio,
  `pulisci_avvisi`). GEOGRAFIA: `dati/comuni.csv` committato (~7.900
  comuni ISTAT con lat/lon del centro, 258KB; fonte opendatasicilia,
  una tantum) letto in RAM da `carica_comuni()` — MAI Nominatim:
  zero rete nel percorso caldo di pubblica(), file assente =
  funzione geografica spenta e tutto il resto vive. Chiavi via
  `normalizza()`; i ~7 nomi contesi d'Italia (Castro, Peglio...)
  entrano solo come 'castro bg' (la chiave nuda ambigua si scarta);
  alias senza PREPOSIZIONI_COMUNI ('reggio emilia' ≡ «Reggio
  nell'Emilia», i nomi veri vincono sempre sugli alias); stoplist
  COMUNI_PAROLA (Paese, Vita, Sale, Calcio...) = matchano solo se la
  zona è ESATTAMENTE quel nome. `coordinate_da_zona` scandisce gli
  n-grammi del testo libero dal più lungo al più corto, a parità
  vince il primo nel testo («tra Pavia e Milano» → Pavia; «vicino
  Milano» → Milano, il raggio assorbe il vicino), secondo giro senza
  preposizioni («Cassano allo Ionio» trova «Cassano all'Ionio»).
  Colonne `annunci.lat/lon` ((0,0) = zona non riconosciuta: matcha
  solo i criteri non geografici, imperfezione dichiarata) scritte UNA
  volta in pubblica/modifica/modifica firmata/import CSV, ricalcolate
  per gli importati a ogni giro orario (le zone possono cambiare sui
  relay); `backfill_coordinate()` a ogni avvio (idempotente, solo
  righe a (0,0)); `distanza_km` = haversine. Il comune dell'UTENTE
  viene SEMPRE dal dataset (`GET /api/comuni` autocomplete + 400 sul
  nome sconosciuto: l'avviso ha sempre coordinate buone, il testo
  libero resta solo dal lato annunci).
  Città vere in Vendi (lug 2026): il campo Zona resta testo LIBERO ma
  suggerisce i comuni mentre si digita — datalist `zonaList` su
  /api/comuni (debounce 250ms, pattern avvisi) col valore nel formato
  «Comune (SIGLA)» («Carmagnola (TO)»: distingue gli omonimi, e
  normalizza('Pavia (PV)') = 'pavia pv' è una chiave GIÀ registrata
  da carica_comuni, riconosciuta senza codice nuovo; il valore si
  salva e si mostra così com'è). Al blur passa da
  `GET /api/zona-controlla` (autenticato): comune riconoscibile nel
  testo = silenzio; nulla di riconoscibile = riga `#zonaHint` col
  «forse Pavia (PV)?» quando il fuzzy ha un candidato, e la via
  d'uscita giusta secondo il caso ([Usa «Pavia (PV)»], oppure
  [lascia il campo vuoto] senza ritiro); il nome suggerito vive nella
  variabile `zonaSuggerita` e mai dentro l'onclick (gli apostrofi di
  Sant'Angelo). LA ZONA DEV'ESSERE UN LUOGO (lug 2026): il campo
  resta TESTO LIBERO, ma deve CONTENERE un comune riconosciuto —
  frazioni ok per costruzione («Frazione Salsasio, Carmagnola (TO)»
  passa: gli n-grammi trovano il comune), «Pvia» e «Spedisco in tutta
  Italia» no. Due severità: col RITIRO ('ritiro'/'entrambe') la zona
  è anche OBBLIGATORIA (chi viene a ritirare deve sapere dove);
  SENZA ritiro resta FACOLTATIVA — chi spedisce e basta la lascia
  vuota, e in card lo dice già il 🚚 — ma se la compila dev'essere
  vera. Fino al lug 2026 qui c'era solo un avviso MORBIDO col
  «Lascia così», e il campo Zona diventava un secondo posto dove
  scrivere la spedizione: è da lì che nascono le zone non-luogo che
  la vetrina deve poi nascondere. La regola vive in
  `guardia_zona_condizione` (giudice unico di pubblica e modifica;
  400 con `messaggio_zona_storta`, il messaggio UNICO che form,
  import e client dicono uguale; senza dataset si spegne, fail-open),
  nell'anteprima dell'import CSV (SCARTO con numero di riga e
  suggerimento, non più un avviso) e nel client (campo vuoto col
  ritiro fermato in publish(), che poi richiama `controllaZona()` e
  guarda `zonaStorta` — così l'errore arriva PRIMA del viaggio con le
  foto in base64; label dinamica «obbligatorio per il ritiro» da
  aggiornaConsegnaForm). CONSEGUENZA DICHIARATA: un annuncio storico
  con la zona storta viene fermato alla PRIMA MODIFICA finché non la
  sistema — lo stesso patto della condizione obbligatoria. Le
  migrazioni d'avvio invece non toccano nulla. Resta APERTA una sola
  porta, e non si può chiudere: l'import Nostr, che prende il tag
  `location` verbatim e lo riscrive DAI RELAY ogni ora — lì i relay
  sono la fonte di verità. Per questo il
  filtro giusto sta in VISUALIZZAZIONE, vedi «La zona si mostra solo
  se è un luogo» qui sotto. `suggerisci_comune` = difflib a
  soglia 0.8 sugli n-grammi (lunghi prima, primo nel testo a parità,
  come coordinate_da_zona), stoplist `PAROLE_ZONA` (senza, «spedisco»
  suggeriva Sedico BL — successo davvero), cache pigra `_comuni_fuzzy`
  («Nome (SIGLA)») solo sui nomi che coordinate_da_zona sa poi
  riconoscere (i contesi
  tipo Castro non si suggeriscono mai: sarebbe un vicolo cieco).
  Import CSV: righe col ritiro e zona vuota o irriconoscibile =
  SCARTO in anteprima («forse Pavia (PV)?»), senza ritiro resta
  l'AVVISO morbido. Dataset assente = tutto riconosciuto, la funzione
  si spegne in silenzio come il resto della geografia.
  La sigla in vetrina c'è SEMPRE (lug 2026): `arricchisci_zona`
  normalizza AL SALVATAGGIO (pubblica/modifica/import CSV) — se il
  testo contiene un comune riconosciuto senza ambiguità e la sigla
  manca, la aggiunge accanto al comune DENTRO il testo («Frazione
  Salsasio, Carmagnola» → «…, Carmagnola (TO)»), così il dato è pulito
  ovunque (vetrina, dettaglio, NIP-99, avvisi) senza rimedi in
  visualizzazione. MAI inventare: contesi nudi (Castro) e alias
  (Reggio Emilia) restano com'erano, chi ha la sigla non si tocca
  (idempotente), e il match che passerebbe solo dal secondo giro
  senza preposizioni («Cassano allo Ionio») non si arricchisce — lo
  span nel testo non sarebbe più suo, imperfezione dichiarata.
  Migrazione morbida `arricchisci_zone_esistenti` a ogni avvio
  (gemella del backfill coordinate, idempotente): solo i
  riconoscibili, MAI gli importati da Nostr (contatto_nostr pieno:
  la loro zona la riscrive l'import orario dai relay).
  Si mostra SOLO IL COMUNE riconosciuto (lug 2026), mai il testo
  intero, e se un comune non c'è non si mostra NIENTE. Vale in TUTTI
  i posti che il luogo lo mostrano: card, pillola del dettaglio,
  righe di «📋 I tuoi annunci» e «🫙 Nel tuo barattolo». Quindi
  «Frazione Salsasio, Carmagnola (TO) — spedisco ovunque» diventa
  «Carmagnola (TO)», «vicino Milano (MI)» diventa «Milano (MI)», e
  «Spedisco in tutta Italia» o «Nord Italia» non lasciano NULLA al
  loro posto — la strada di consegna la dicono già le icone accanto,
  e il vecchio ripiego `luogoMeta` «📦 Spedizione»/«💾 Online»/«📍 —»
  non esiste più. `luogoTesto` dice la regola, `luogoRiga` (riga
  discreta sotto il titolo del dettaglio — era `luogoPill`, la
  pillola è morta col riordino del dettaglio, vedi sotto) e
  `luogoPunto` (coda « · 📍 X» delle righe elenco,
  col separatore che sparisce insieme al luogo: mai un puntino
  orfano) la vestono — tre rese che non possono divergere, la stessa
  idea del cuore unico qui sotto. Il dato NON si perde: la zona resta
  intera nel database, il form di modifica la mostra per intero, e
  continua a servire per le coordinate e gli avvisi.
  IL TESTO INTERO NEL DETTAGLIO È DURATO UN GIORNO — e vale la pena
  dire perché non era tenibile, che è utile quanto la regola. La
  scelta di partenza era ragionevole: la card come INDICE (nomi
  confrontabili a colpo d'occhio) e la scheda come DICHIARAZIONE del
  venditore, col testo intero, per non perdere le frazioni —
  «Frazione Salsasio» serve a chi va a ritirare. Non regge, perché
  la frazione e la frase-spazzatura SONO LA STESSA COSA: testo
  libero attorno a un comune. Il «resto» di «Torino (TO) spedisco in
  tutta Italia» è esattamente ciò che si vuole nascondere, e non
  esiste modo di tenere l'uno senza l'altro. La via di mezzo —
  mostrare il testo intero solo con il RITIRO attivo, dove la
  frazione serve davvero — è stata valutata e scartata due volte:
  un annuncio col ritiro può avere lo stesso la frase-spazzatura
  nella zona, e una regola condizionale sulla modalità di consegna
  sarebbe impossibile da ricordare fra sei mesi. Chi ci tiene alla
  frazione la scrive in DESCRIZIONE, che nel dettaglio si legge
  tutta due righe più sotto e che il venditore controlla; e il punto
  d'incontro di un ritiro si concorda comunque tra le parti (ponti
  di contatto, poi il pannello dell'ordine): un indirizzo Barattolo
  non l'ha mai pubblicato. Dal compratore, in vetrina, la domanda è
  «è vicino a me?», non «in che via?».
  Il nome esce nella forma UFFICIALE del dataset, il che raddrizza
  gratis le maiuscole storte («torino (TO)» → «Torino (TO)») e dà la
  sigla anche agli alias che `arricchisci_zona` non sapeva servire
  («Reggio Emilia» → «Reggio nell'Emilia (RE)»).
  IL CUORE È UNO SOLO — `_chiave_comune` — e questo è il vincolo che
  ha guidato il disegno: `coordinate_da_zona` (le coordinate) e
  `comune_da_zona` (il nome per la vetrina) DEVONO dire la stessa
  cosa, o la card mostrerebbe un luogo per cui il filtro geografico
  degli avvisi non trova nulla, o viceversa. Un solo scanner a
  n-grammi, quindi, e le due funzioni ci si appoggiano entrambe;
  verificato sull'intero dataset (7.904 comuni × 3 forme, zero
  divergenze). `arricchisci_zona` invece NON passa di lì e tiene il
  suo giro: a lei serve la POSIZIONE del comune nel testo, che il
  secondo passaggio senza preposizioni perde. Il nome lo dà
  `_comuni_nome()`, gemello LARGO di `_comuni_fuzzy` (che tiene i
  soli nomi nudi perché lì sono i candidati del difflib): qui
  servono anche la chiave nome+sigla e gli alias, o il comune
  riconosciuto resterebbe senza un nome da mostrare.
  API: `CAMPI_VETRINA` espone `zona_comune` (il nome, '' = la zona
  non è un luogo) — che è ANCHE il flag «mostro il 📍?», quindi UN
  campo invece di due: il breve `zona_riconosciuta` (0/1 da
  `a.lat!=0 OR a.lon!=0`) è vissuto un giorno solo ed è stato
  assorbito da questo, che dice la stessa cosa e in più porta il
  nome. Si calcola in Python dentro `arricchisci_righe_vetrina` e
  non in SQL — il dizionario dei ~7.900 comuni vive in RAM, non nel
  database — ed è per riga una manciata di lookup su un dict: nulla,
  anche sulle 300 righe della shortlist AI.
  ATTENZIONE, e vale per ogni campo derivato che verrà dopo:
  `arricchisci_righe_vetrina` (si chiamava `espandi_distintivi_
  vetrina` finché faceva una cosa sola) è il COLLO DI BOTTIGLIA da
  cui passano tutte e sei le rotte che diventano card — vetrina,
  negozio, singolo, miei, ricerca AI, preferiti. È lì che si
  aggiungono i campi derivati, ed è per questo che `zona_comune` non
  ha bisogno di nessun ripiego lato client: le rotte che servono
  l'annuncio INTERO (`/api/search`, `/api/listings/miei`) passano da
  `a.*` e non avrebbero un alias SQL, ma passano di lì anche loro.
  In DEMO non c'è server che estragga il comune e l'approssimazione
  onesta è `comuneDemo` (il pezzo di testo che porta la sigla, che
  nel campo Zona è il formato suggerito).
  La REGIONE è DERIVATA (lug 2026): non è un campo del form e non si
  chiede MAI al venditore — si ricava dalla sigla che `arricchisci_zona`
  ha già messo nella zona. `regione_da_zona` prende la PRIMA sigla
  valida del testo (regola di coordinate_da_zona: «Roma (RM) o Milano
  (MI)» → Lazio; un «(kg)» non è una sigla e si ignora) contro la mappa
  fissa `REGIONI` (20 regioni → le 107 sigle, scritta per regione:
  `SIGLE_REGIONE` si deriva da lei, una sola fonte di verità —
  verificata contro dati/comuni.csv, zero buchi). Colonna
  `annunci.regione` ('' = sigla assente o sconosciuta: storici, alias
  tipo «Reggio Emilia», frazioni irriconoscibili — nessun blocco, il
  filtro non li vede, lo stesso patto di condizione e spedizione),
  scritta accanto a lat/lon in pubblica/modifica/modifica firmata/
  import CSV, ricalcolata per gli importati a ogni giro orario nel
  dopo-import (gemella delle coordinate) e data agli annunci di ieri
  da `deriva_regioni()` all'avvio — DOPO `arricchisci_zone_esistenti`,
  che l'ordine conta (prima la sigla nella zona, poi la regione);
  idempotente, tocca solo le righe ancora vuote. In CAMPI_VETRINA;
  param `regione` su /api/listings (sconosciuta = nessun filtro, mai un
  400) componibile con categoria, prezzo, condizione, spedizione e col
  cursore; `regioni` = {regione: quanti} nella busta di PRIMA pagina,
  conteggi GLOBALI come `conteggi` (non seguono categoria né ricerca) e
  senza le vuote. Frontend: foglio-picker `filtroRegSel` nel pannello
  Filtri, voci dal SERVER («Lombardia · 137», alfabetico, «Tutta
  l'Italia» prima) — la regione scelta resta in elenco anche a 0
  annunci (il campo non deve mentire), nessuna regione (server di ieri,
  vetrina vuota) = la riga sparisce del tutto, in DEMO si conta dai
  dati finti (`renderFiltroRegioni`); stato di sessione `filtroReg`
  come gli altri filtri. NON si mostra da nessuna parte in vetrina
  (deciso: la sigla nella zona la dice già a un lettore italiano, e la
  card resta pulita); se un giorno servisse, il posto è la fila di
  pillole del dettaglio. Due lezioni dal cantiere: `apriPicker` passa
  ora il valore in `data-val` invece che dentro la stringa JS
  dell'onclick — «Valle d'Aosta» spezzava l'apice, e il commento «i
  valori vengono dai cataloghi, l'onclick è sicuro» valeva finché nei
  cataloghi non c'erano apostrofi; e Applica/Azzera del pannello sono
  gemelli per `.filtri-riga .btn.ghost{margin-top:0}` (a pari
  specificità vinceva il `margin-top:10px` della ghost e in flex
  «stretch» stirava Applica di 10px) più la base flex al 50% (col
  basis 0 i 2px di bordo della ghost si sommano FUORI dalla base e la
  facevano larga 4px in più).
  «📍 VICINO A ME» È ESISTITO DUE GIORNI, ED È STATO TOLTO (lug 2026,
  decisione di Andrea) — la voce resta qui perché il motivo vale più
  della funzione, e perché è un'idea che torna in mente da sola.
  Era: comune di chi guarda (colonna `utenti.comune`) più un raggio,
  parametri `vicino`/`raggio_km` su /api/listings con l'haversine
  prestato a SQLite, foglio «Da dove cerchi?», e il comune riusato per
  precompilare la Zona di Vendi e gli avvisi di ricerca. Funzionava.
  È stato tolto perché IL FILTRO PER REGIONE COPRE GIÀ QUEL BISOGNO, e
  due strade per la stessa cosa non sono il doppio delle possibilità:
  sono un bivio davanti a chi cerca, che deve capire in che cosa
  differiscono prima di scegliere — e per un compratore italiano
  «Lombardia» e «entro 50 km da Milano» rispondono alla stessa
  domanda. Non era un problema di codice: era una voce di troppo nel
  pannello. Chi volesse riprovarci si chieda prima cosa TOGLIE, non
  cosa aggiunge.
  Restano in piedi, e sono roba d'altri cantieri: `distanza_km` e
  `RAGGI_AMMESSI` (li usano gli avvisi di ricerca), `comune_da_zona`
  e tutto il motore geografico, `GET /api/comuni` — che era stata
  aperta al pubblico per la vetrina anonima ed è tornata AUTENTICATA
  con la rimozione: non perché aprirla facesse danno (è l'elenco ISTAT
  committato in chiaro) ma perché una superficie pubblica senza più un
  motivo è solo superficie.
  COLONNA `utenti.comune`: INERTE. Nessuno la scrive, nessuno la
  legge; è rimasta per non fare una migrazione distruttiva su chi
  l'aveva valorizzata in quei due giorni, come `avatar_visibile` prima
  di lei. Non è un dato su cui contare: se un domani servisse davvero
  un comune dell'utente, va ripensato da capo.
  E LA ZONA DI VENDI NON SI PRECOMPILA (stessa decisione): il campo
  nasce vuoto e lo scrive l'utente con l'autocomplete. Con l'avviso
  «Ho scritto Milano (MI)…» se n'è andata anche `avvisoComune`, e con
  lei la proposta ricavata dagli ultimi annunci (`comune_suggerito` in
  /api/me). Il posto dove si dice da dove si vende è uno solo, ed è
  quel campo lì. MOTORE: gemello della coda
  promo — `accoda_match` in pubblica() accanto ad accoda_promo, nel
  loop finale dell'import CSV (accodati insieme = UN aggregato) e nel
  dopo-import Nostr (`creato>=t0`: gli importati CONTANO, «un
  annuncio è un annuncio»; importa_nostr.py resta intonso);
  `_drena_match` dorme ATTESA_RAGGRUPPO, rilegge dal DB (spariti nel
  frattempo = muti), prefiltro SQL sugli avvisi attivi (`tg_id !=
  venditore`: mai avvisato del proprio annuncio; categoria e prezzo
  sats in SQL) + verifica fine in Python: parole TUTTE in AND a
  prefisso di parola ('bici' prende 'bicicletta', 'ram' non affoga in
  'ceramica'), prezzo EUR col cambio corrente (cambio mai arrivato =
  l'avviso EUR NON scatta: meglio un match perso che uno sbagliato),
  haversine ≤ raggio. ANTI-MOLESTIA a tre strati: 1) dedup DB sopra;
  2) aggregazione per finestra — match singolo = messaggio ricco
  (titolo, prezzo via `_prezzo_promo`, 📍 zona, link /annuncio/{id}),
  2+ = UN solo «📬 N nuovi annunci corrispondono ai tuoi avvisi»;
  3) `TETTO_AVVISI_GIORNO` (5 in prod, 3 in collaudo) MESSAGGI al
  giorno per utente in `AVVISI_QUOTA` (memoria, pattern IMPORT_QUOTA:
  un riavvio azzera il conteggio, accettato — le raffiche vere le
  ferma l'aggregazione, che è strutturale); l'ultimo messaggio del
  giorno chiude con «per oggi mi fermo qui 🤫», onestà e non silenzio.
  Uscita SEMPRE via `notifica()`: multi-canale e DM NIP-17 gratis,
  nativi Nostr inclusi; 0.2s tra un utente e l'altro, fail-open
  totale (un errore nel matching non tocca mai la pubblicazione).
  `esegui_fusione` migra avvisi e dedup (UPDATE OR IGNORE).
  Endpoint (pattern canale-notifiche): GET/POST /api/me/avvisi-ricerca
  (POST con `id` = modifica del proprietario; ALMENO un criterio, un
  avviso vuoto sarebbe tutta la vetrina in chat; 400 oltre il tetto
  di 5), POST .../{id}/pausa e .../{id}/elimina, GET /api/comuni
  (autenticato, primi 10 per prefisso). Frontend: cassetto «🔎 Avvisi
  di ricerca» nel Profilo (`renderRicerche`, sparisce in
  DEMO/VETRINA; pillole categoria toggle senza re-render — il
  re-render pieno perderebbe i campi digitati —, comune con
  `<datalist>` e debounce 250ms su /api/comuni, select raggio, prezzo
  col toggle sats/€, riepiloghi sotto `esc()`, ✏️ precompila il form,
  conteggio «(N di 5)» nell'header) e CTA «🔔 Avvisami se arriva» in
  #gridEmpty dopo una ricerca a vuoto (mai in DEMO/VETRINA;
  passamano `ricercaPrecompila` con query e categoria attiva,
  consumato da renderRicerche, pattern hintPubblicazione).
  Feedback e stelle (lug 2026): tabella `feedback(ordine_id, da_tg_id,
  per_tg_id, voto 1-5, commento ≤200, creato)` con
  `UNIQUE(ordine_id, da_tg_id)` come giudice dei doppioni.
  `POST /api/orders/{id}/feedback`: solo le due parti, solo su
  `STATI_FEEDBACK = (released, refunded)` — anche gli affari finiti
  male sono affari veri, escluderli gonfierebbe i profili —
  definitivo (niente modifica: chiude il ricatto «cambia il
  feedback o…»; la valvola è `POST /api/admin/feedback/{id}/rimuovi`).
  Commento sotto `controlla_vietato` (niente AI: 200 caratteri legati
  a una transazione pagata). `utenti.rating` e `n_feedback` si
  aggiornano SEMPRE per RICALCOLO (`_ricalcola_rating`: AVG/COUNT
  dalla tabella, `round(…,1)`, dentro `BEGIN IMMEDIATE`): così
  rimozione admin e fusione si sistemano da sole. `esegui_fusione`
  migra i feedback (prima però cancella quelli sugli auto-scambi tra
  le due metà: eviterebbero la UNIQUE e sarebbero auto-voti) e
  ricalcola. `/api/orders` espone `mio_voto/mio_commento` e
  `suo_voto/suo_commento`; `/api/negozio/{chi}` aggiunge
  `n_feedback` al profilo e `feedback` = ultimi 10 ricevuti (voto,
  commento, data, ruolo «acquirente/venditore», e dall'ago 2026
  anche CHI l'ha scritto: `da_nome`, `da_avatar`, `da_negozio`;
  `f.id` è opaco e serve al bottone rimuovi dell'admin).
  I FEEDBACK NON SONO PIÙ ANONIMI (ago 2026, decisione di Andrea che
  ROVESCIA la regola di ieri — qui c'era scritto «MAI nomi: su una
  pagina pubblica rivelerebbero gli acquisti altrui»). Il motivo del
  rovesciamento è lo stesso che aveva fatto nascere il «da N
  persone»: un voto senza un volto non si può pesare, e quaranta voti
  dallo stesso account si vedevano identici a quaranta di quaranta
  persone. Il conteggio dice il sospetto, i nomi lo fanno vedere —
  e i due convivono, che il conteggio si legge a colpo d'occhio.
  DUE COSE RESTANO DENTRO, e sono la parte da non allentare: 1)
  l'OGGETTO comprato non esce MAI (si vede che quella persona ha
  fatto un affare lì, non che cosa ha preso — quello resta un fatto
  suo); 2) nessun RECAPITO nel payload: esce il codice del negozio,
  il nome ci porta (`.fb-chi` → `apriNegozio`), e i ponti
  Telegram/Nostr vivono di là con le loro regole di sempre (npub solo
  dal possesso dimostrato). Un contatto qui sarebbe una seconda porta
  da tenere allineata per sempre. L'avatar segue la scelta
  dell'utente col solito CASE su `avatar_scelta='nessuna'`, e
  `.av-foto` ha dovuto imparare un secondo genitore (`.fb-faccia`):
  era agganciato al solo `.avatar`, e altrove l'immagine sarebbe
  uscita a dimensione naturale. Invito ⭐ in coda alle
  notifiche di chiusura (sblocco manuale/automatico e rimborso).
  Frontend: `feedbackPanel(o)` nel dettaglio ordine (5 stelle
  cliccabili + textarea, `confirm` prima dell'invio, gira in
  «Feedback lasciato» + eventuale «ricevuto»), lista nel negozio
  (`#negozioFeedback`), conteggio `(N)` accanto alle stelle in
  negozio e profilo, commenti sempre sotto `esc()`.
  Distintivi 🏅 (lug 2026, gamification parte 2): catalogo `DISTINTIVI`
  nel codice (11 badge: id, emoji, nome, descrizione, `fiducia`,
  criterio-lambda) + tabella `badge_utente(tg_id, badge_id,
  ottenuto_il, PK(tg_id,badge_id))`. Append-only: non si revocano mai.
  `controlla_distintivi(con, tg_id)` è il giudice unico: RICALCOLA i
  criteri dai dati veri (stile `_ricalcola_rating`) e assegna con
  INSERT OR IGNORE; `premia_distintivi(tg_id)` (connessione propria,
  fail-open, notifica «🏅» DOPO il commit) è il gancio dal vivo in:
  `_sblocca_sats` (entrambe le parti), `verifica_npub_controlla`,
  `abilita_accesso_nostr`, `login_nostr` (nativo nuovo),
  `login_nostr_collega`, `pubblica`, `lascia_feedback` (entrambe).
  Passata retroattiva SILENZIOSA su tutti gli utenti a ogni avvio in
  `init_db` + catch-all silenzioso in `/api/me` (scrittura su GET ma
  idempotente: è ciò che rende il sistema auto-riparante). I criteri
  pesanti contano solo ordini `released` (sats veri dall'escrow:
  gonfiarli costa la commissione); `ordini.disputata` (nuova colonna,
  settata in `apri_disputa`, backfill sugli stati post-disputa) fa da
  memoria per Specchiato («10 affari senza dispute perse»: venditore
  perde se refunded+disputata, compratore se released+disputata).
  Fulmine usa `spedito_il-creato ≤ 24h+30min` (il reaper dei 30 min è
  il tetto fisico del pagamento: niente colonna `pagato_il`).
  Pioniere = posizione ≤100 per `(registrato ASC, tg_id)`, gli 0
  pre-migrazione contano come i più vecchi. `esegui_fusione` migra i
  badge in unione (UPDATE OR IGNORE + DELETE) e rivaluta. API:
  `/api/me.distintivi` = catalogo COMPLETO con `ottenuto` (ts o null,
  il frontend non hardcoda mai la lista); `/api/negozio` →
  `venditore.distintivi` e `venditore_distintivi` sugli annunci
  (subselect GROUP_CONCAT in `CAMPI_VETRINA` + SELECT di search e
  miei, espanso in {id, emoji, nome, descrizione} da
  `arricchisci_righe_vetrina`) = dal lug 2026 TUTTI i guadagnati
  (bacheca stile Vinted, deciso con Andrea: ⚡ Primo acquisto
  pubblico compreso — aggregati senza segreti); il flag `fiducia`
  non filtra più, decide solo la PRECEDENZA (i fiducia in testa al
  catalogo → in testa alla sfilza: il «+N» taglia i badge di
  percorso, mai quelli di affidabilità). Frontend:
  griglia `renderDistintivi()` nel cassetto «🏅 Distintivi» del
  Profilo (il conteggio «(N di M)» vive nell'header del cassetto,
  `#distintiviConta`; classe `.distintivo` — `.badge` è degli stati
  ordine — mancanti in grigio con la descrizione come molla), e in
  pubblico la SFILZA `sfilzaDistintivi(lista, max, tocca)`: emoji
  nude `.sfilza .medaglia` a 14.5px — la taglia del nome accanto,
  provata anche piu' grossa (19px) e tornata indietro — con un
  piccolo gap (niente
  cerchietti d'oro: nude e sovrapposte si impasterebbero — l'oro
  resta alle tessere del foglietto; `nostrano`
  sempre fuori: il 🟣 accanto al nome c'è già) — nel dettaglio
  annuncio prime 4 + «+N» dentro la card venditore che resta tutta
  cliccabile (nessun tocco sulla sfilza: un bersaglio solo), in
  testata negozio COMPLETA (flex-wrap, mai «+N»: è la bacheca) e
  toccabile → foglietto `#distintiviSheet` (pattern sheet, registrato
  in `closeSheet`, dati da `negozioCorrente`) con le tessere
  `.distintivo` di TUTTI i guadagnati, nome e descrizione — qui
  `nostrano` c'è, ed è il posto che spiega il pallino viola; i
  mancanti mai in pubblico. Cassetto nascosto in DEMO come il wallet.
  XP, coorti, livelli e titoli (ago 2026, gamification parte 3): il
  piano intero sta in `proposte/roadmap-gamification-aste.md`, coi
  motivi e le strade scartate.
  LA DIFFERENZA CHE GOVERNA TUTTO: distintivi e rating si RICALCOLANO
  dai dati veri, quindi una passata retroattiva li rimette in pari e
  un bug non lascia cicatrici. GLI XP NO — una visita giornaliera è
  un evento, e se non lo scrivi quando succede è perso per sempre.
  Quindi la verità è la tabella `xp_eventi` (append-only: tg_id, tipo,
  punti, riferimento, creato) e `utenti.xp` è solo la sua somma
  (cache, `_ricalcola_xp`). La `UNIQUE(tg_id, tipo, riferimento)` è il
  GIUDICE dell'idempotenza: non si chiede a chi scrive un gancio di
  ricordarsi «gliel'ho già dato?» — retry, doppio gancio e riavvio a
  metà ci sbattono contro. Lo stesso vincolo fa da TETTO GIORNALIERO
  senza che nessuno lo scriva: visita e primo annuncio del giorno
  hanno il giorno DENTRO il riferimento (`giorno:2026-08-05`), e il
  secondo annuncio non paga — serve, o la strada più veloce per
  salire sarebbe pubblicare spazzatura.
  LA FORMULA DEGLI ORDINI (decisioni di Andrea, da non rovesciare):
  `xp_ordine` = (FISSO_XP_ORDINE 10 + euro × XP_PER_EURO 1) ×
  XP_RUOLO (venditore 1.0, compratore 0.6), e la base è
  `ordini.prezzo_sats` INTERO — spedizione e protezione comprese:
  chi paga 300 € di spedizione ha speso 300 €. NESSUN TETTO: un
  acquisto da 4.000 € non è un'anomalia da limare, è qualcuno che ha
  affidato quella cifra al deposito di garanzia; frequenza e importo
  valgono ENTRAMBI (sul volume guadagniamo le fee, sull'importo la
  fiducia). NESSUNA regola della coppia: si può essere fidelizzati a
  un negozio e usare Barattolo proprio perché ci si fida dell'escrow,
  che per giunta è pagato. Il cambio è `ordini.cambio_eur`, appena
  scritto in colonna per l'export: nessun giro di rete in più; cambio
  a 0 = resta il solo fisso (mai un numero inventato, la regola
  dell'avviso EUR senza cambio). Il RUOLO sta nel riferimento
  (`ordine:42:venditore`) o le due parti si pesterebbero sulla
  UNIQUE. SOLO su `released`: rimborsato = merce tornata indietro.
  Ganci dove vivono già i distintivi: `_sblocca_sats`, `/api/me`
  (visita), `pubblica`, `lascia_feedback`, `ln-address`,
  `verifica_npub_controlla`, `login_nostr` nativo, `esegui_fusione`.
  `premia_xp` è il gemello fail-open di `premia_distintivi` (un
  errore negli XP non tocca MAI uno sblocco di sats); nessuna
  notifica, gli XP si guardano nel Profilo.
  ORDINI FASULLI TOLLERATI (decisione di Andrea): chi li crea paga la
  commissione a ogni giro — si compra la fama, ed è un cliente. Due
  cose da ricordare, perché il ragionamento regge a commissione
  ACCESA e oggi è SOSPESA: la CLASSIFICA aspetta quel giorno (finché
  farmare è gratis misurerebbe il tempo libero, non il commercio), e
  il «da N persone» qui sotto va tenuto, o nessuno può accorgersi di
  niente. NIENTE streak consecutivo: in un mercatino non c'è nulla da
  fare ogni giorno, e una fiammella che si spegne punisce chi ha
  lavorato invece di aprire l'app; se servirà, si contano i giorni
  TOTALI, che salgono e basta.
  COORTI: `COORTI` generalizza il distintivo Pioniere (posizione
  ≤100) in una scala — pioniere 100 · fondatore 500 · veterano 2000 ·
  bottegaio 10000. Chi entra oltre l'ultima soglia NON ha coorte, ed
  è giusto: è un FATTO, non un premio da dare a tutti — se ce l'hanno
  tutti non dice più niente. `utenti.coorte` si CONGELA al primo
  calcolo (`assegna_coorte`): la posizione in una fila non cambia mai
  più, e ricalcolarla sarebbe una scansione per chiamata a diecimila
  utenti. Backfill idempotente in `init_db` + `/api/me` per i nuovi.
  LIVELLI a DUE CHIAVI (`LIVELLI`, `livello_utente(xp, affari)`), ed
  è la conseguenza diretta del niente-tetto: senza il secondo
  requisito una vendita da 4.000 € basterebbe a fare un maestro, e il
  grado direbbe «ha venduto una cosa cara» invece di «commercia».
  Derivati, mai in colonna. Il client ripete le sole SOGLIE XP
  (`SOGLIE_LIV`) per disegnare la barra DENTRO il gradino, e
  `prove.py` le incrocia (lezione delle categorie senza condizione).
  TITOLI: il distintivo dice «ho fatto», il titolo dice «chi sono» —
  ed è l'unica cosa che l'utente SCEGLIE. `TITOLI` (requisito =
  coorte | distintivo | livello: fatti già calcolati altrove, qui non
  si giudica niente di nuovo), `utenti.titolo`, `POST /api/me/titolo`
  col pattern di canale-notifiche (si accetta solo un titolo
  SBLOCCATO) e `titoli_disponibili` giudice unico dell'elenco E della
  validazione, o si indosserebbe qualcosa che l'elenco non offre. I
  livelli sono una SCALA: chi è esperto porta anche i gradini sotto.
  IL CATALOGO RESTA CHIUSO: un titolo scritto a mano sarebbe
  impersonazione («Moderatore»), che non è un problema di `esc()` ma
  di significato. In pubblico esce col NOME e non con l'id, espanso
  in `arricchisci_righe_vetrina` (`NOMI_TITOLI`): il catalogo sta sul
  server. `venditore_titolo` in CAMPI_VETRINA, `titolo` e `livello`
  nel profilo di `/api/negozio`. Frontend: cassetto «🎖 Livello e
  titolo» sopra i distintivi (grado, barra `.barra-xp`, cosa manca al
  prossimo, pillole `.titolo-pill` — le non sbloccate restano in
  elenco spente col perché, la molla dei distintivi in grigio) e riga
  `.titolo-riga` sotto il nome in Profilo, testata negozio e riquadro
  venditore del dettaglio. Mai in card: la riga meta è già satura.
  Da quante PERSONE arrivano i feedback (ago 2026): sul negozio
  pubblico i voti escono senza nomi, di proposito — mostrare chi ha
  comprato rivelerebbe gli acquisti altrui —, ma senza un secondo
  numero un venditore con 40 voti dallo stesso account si vede
  IDENTICO a uno con 40 voti di 40 persone. Un CONTEGGIO, non dei
  nomi: la privacy resta intera e il giudizio torna a chi legge.
  Colonna `utenti.n_recensori`, `COUNT(DISTINCT da_tg_id)` dentro
  `_ricalcola_rating` accanto a rating e n_feedback (quindi rimozione
  admin e fusione si sistemano da sole), backfill idempotente
  all'avvio. LA SECONDA CIFRA COMPARE SOLO QUANDO I DUE NUMERI
  DIFFERISCONO — «(40 da 1 persona)» parla, «(40)» quando sono
  quaranta persone tace: è tutta la soglia, non c'è niente da tarare.
  Giudice unico `contaFeedback()`, due soli posti (negozio pubblico e
  Profilo); MAI nel dettaglio annuncio, dove la riga è già
  «4,8 (40) ·» e un secondo numero la rende illeggibile.
  Export dati contabili (lug 2026): colonna `ordini.cambio_eur` = EUR
  per BTC al momento della chiusura, scritta da `_sblocca_sats` e
  `_rimborsa_compratore` via `cambio_btc_eur()` (CoinGecko lato server
  — il ≈€ della vetrina resta lato client — cache 15 min, fail-open:
  0 = sconosciuto, e gli ordini storici restano onestamente vuoti nel
  CSV). `POST /api/me/export-biglietto` (autenticato) emette un
  biglietto TTL 5 min (`BIGLIETTI_EXPORT` in memoria, stile
  SFIDE_LOGIN: dentro Telegram il download non può portare l'header
  di auth); `GET /api/export/{biglietto}` (anche HEAD: la sonda di
  Telegram prima del popup) serve il CSV
  degli affari released/refunded dell'utente, da entrambe le parti.
  ATTENZIONE: il biglietto NON è monouso — il downloader di Telegram
  fa più richieste sullo stesso link (HEAD di sonda + GET, a volte a
  range) e bruciarlo alla prima gli farebbe scaricare un 410 (bug
  vero, successo su Android): vale i suoi 5 minuti, poi la purga
  (data, ruolo, annuncio, sats, esito, controvalore_eur) —
  separatore `;`, decimali con virgola e BOM UTF-8 per l'Excel
  italiano, quoting del titolo via csv.writer. Frontend: bottone
  «📄 Esporta i tuoi dati» in fondo a «⚡ Wallet e incassi» nel
  Profilo (`esportaDati()`: `tg.downloadFile` SOLO con initData vero
  e `isVersionAtLeast('8.0')` — nel browser lo stub di Telegram
  esiste comunque e mentirebbe — con ripiego `tg.openLink` se lancia;
  altrimenti `<a download>`; in DEMO sparisce col blocco wallet).
  Import in blocco da CSV (lug 2026): cassetto «📥 Importa in blocco»
  nel Profilo (in DEMO sparisce, il patto del wallet), per i
  commercianti coi cataloghi grandi. Due fasi col pattern biglietto:
  `POST /api/import/zip` (le foto in uno ZIP come CORPO BINARIO puro
  letto a chunk col tetto 50MB applicato DURANTE la lettura; controlli
  sulle sole intestazioni — ≤2000 voci, somma ≤200MB, ≤15MB/voce,
  niente path storti — e MAI extract: si legge per nome con zf.read)
  → `POST /api/import/prepara` (CSV come testo in JSON, ≤2MB, header
  per NOME quindi colonne riordinabili, ≤500 righe; ogni riga:
  `neutralizza_formula` anti CSV-injection su titolo/descrizione/zona
  — strappa =, +, @ iniziali, il `-` resta —, prezzo dal giudice
  unico `prezzo_da_payload` (stessi 400/503 di pubblica, EUR con
  virgola tradotta), `categoria_tollerante` coi `SINONIMI_CATEGORIA`
  e ripiego Altro, foto via URL (`url_foto_ammesso` = anti-SSRF: gli
  URL li scrive l'utente, host risolto e IP privati rifiutati — e dal
  l'ago 2026 ANCHE OGNI SALTO DEL REDIRECT, vedi sotto) o nomi
  nello ZIP (match case-insensitive sul basename), filtro parole su
  TUTTE le righe; anteprima {biglietto, valide, scarti, avvisi}
  numerata come nel file — intestazione = riga 1 — TTL 15 min) →
  `POST /api/import/avvia` (quota 1000 righe/giorno per utente e UN
  solo job in corso in TUTTO il server, 409 onesto: mono-processo su
  VPS piccolo) → `GET /api/import/stato/{biglietto}` (polling 2s del
  frontend). Il job `_lavoro_import`, tre fasi: moderazione AI
  COMPLETA ma a LOTTI (`moderazione_ai_lotto`: ~20 annunci per
  chiamata Haiku, semaforo a 3, verdetto per riga `<n>: OK|VIETATO:
  motivo` con parsing robusto — righe storte o numeri allucinati =
  fail-open per voce, errore = fail-open per lotto, ~0,13$ e ~1 min
  per 500 righe); creazione a gruppetti di 4 con COMMIT PER RIGA (un
  crash a metà lascia solo annunci COMPLETI; lo stato è in memoria
  come SFIDE_LOGIN: dopo un riavvio il polling prende 404 e il
  frontend dice la verità); foto nei thread con la filiera buona
  (`normalizza_foto_import`: JPEG già dritto e ≤1600px VERBATIM,
  tutto il resto UNA sola `converti_in_jpeg` — il patto della
  compressione unica vale anche qui; `scarica_foto_import` timeout
  10s tetto 8MB, foto morta = avviso, mai un annuncio perso); Nostr
  in coda a lotti di 5 eventi con pausa 1,5s (checkbox nel form,
  default acceso) quando gli annunci sono GIÀ in vetrina. DEROGA
  dichiarata allo strato 3 della moderazione: UNA notifica admin
  riassuntiva (intervallo id creati + titoli bocciati dall'AI, max
  10) invece di una per annuncio. `GET /api/import/modello` = CSV
  modello scaricabile (pubblico: BOM, `;`, tre righe demo).
  `pulisci_import` nell'orologio: lavori scaduti coi loro ZIP, file
  orfani >1h in `import_tmp/` (in .gitignore), quote dei giorni
  passati. `_salva_una_foto` è il nucleo di scrittura (pieno + `_min`)
  estratto da `salva_foto` e riusato dall'import.
  Spedizione e protezione acquisti (lug 2026, modello Vinted): a
  carico del COMPRATORE, il venditore incassa netto articolo +
  spedizione. Sull'annuncio: colonne `consegna` ('' = non specificata,
  cioè annunci storici e importati col flusso di sempre | spedizione |
  ritiro | entrambe — catalogo `MODALITA_CONSEGNA`),
  `spedizione_sats`/`spedizione_eur` (0 con modalità che spedisce =
  gratis). TRE semantiche del costo, decise dal venditore (lug 2026,
  l'ancora all'euro ha SUPERATO la conversione alla pubblicazione):
  1) listino sats + costo in sats = FISSO, qualunque cosa faccia il
  cambio; 2) listino sats + costo scritto in EURO (toggle `spedValuta`
  sul campo, che decide la SEMANTICA e non la comodità: l'hint lo
  dice) = ANCORATO — si salva spedizione_eur così com'è (sped_sats
  resta 0, niente cambio alla pubblicazione) e diventa sats SOLO in
  compra() col cambio corrente, registrato in `cambio_ordine`: i
  «5 €» del venditore valgono sempre 5 €; senza cambio all'acquisto
  503 onesto SOLO per la scelta spedizione, il ritiro resta sempre
  acquistabile e l'articolo sats non dipende mai dal cambio; i sats
  espliciti battono l'ancora; 3) listino EUR = tutto ancorato per
  natura, articolo e spedizione convertiti INSIEME all'acquisto.
  Nei conti il controvalore sats dell'ancorato è una STIMA
  live («≈», `satsSpedizione` keyed su spedEur>0; prefisso ≈ dei
  bottoni via `stimaCirca`) — dal lug 2026 il costo di spedizione da
  solo non si mostra più da nessuna parte, e con lui se n'è andato
  `spedTesto`: la spedizione entra nei totali e nel conto scomposto,
  sempre in sats; il valore vero si fissa alla creazione
  dell'ordine. Nel NIP-99 spedizione_eur piena parla euro. Gli annunci
  del breve periodo «convertito alla pubblicazione» hanno
  spedizione_eur=0 e restano fissi (caso 1). E `taglia_pacco`
  (`TAGLIE_PACCO` busta/piccolo/medio/grande/ingombrante, con gli
  esempi concreti nel form: servirà alle etichette corriere future; il
  gemello client è il catalogo `TAGLIE` — nome, esempio e `lato` del
  disegno — vedi la scala disegnata qui sotto);
  giudice unico `consegna_da_payload` (sconosciuto → '', mai 400 —
  in pubblica() si chiama PRIMA dello scudo anti-doppione: può
  attendere il cambio, e tra controllo e INSERT niente await).
  Sull'ordine: `ordini.prezzo_sats` RESTA il TOTALE in cassaforte
  (invoice, rimborso integrale e CSV non cambiano semantica); le
  quote `ordini.spedizione_sats`/`protezione_sats` si FISSANO alla
  creazione (il config può cambiare, l'ordine no) e l'articolo si
  deriva per sottrazione; `consegna_scelta` = spedizione|ritiro|''.
  compra(): body `consegna` validato contro la modalità (incompatibile
  = 400; annuncio '' la ignora; 'entrambe' senza scelta = spedizione,
  il client vecchio vede comunque i sats veri della risposta); EUR
  converte articolo+spedizione INSIEME al cambio corrente (un annuncio
  tutto-sats non dipende mai dal cambio); protezione =
  `PROTEZIONE_PERCENTO` (config, 0 = spenta) sul SOLO articolo, per
  difetto (floor), anche sul ritiro; drift/tetto sul solo articolo;
  risposta con `articolo_sats/spedizione_sats/protezione_sats/
  consegna` in più. Chiusure: incasso venditore =
  `netto_venditore(prezzo_sats - protezione_sats)` in _sblocca_sats e
  deposita_invoice (COMMISSIONE_PERCENTO resta leva DISTINTA e
  sottrattiva: compongono senza doppio conteggio); rimborso = totale
  (la protezione torna al compratore). Ritiro in zona SENZA stati
  nuovi: corriere-sentinella 'Ritiro in zona' (gemello di 'Consegna a
  mano', esente tracking, notifica sua) su segna_spedito;
  l'auto-sblocco a 10gg resta ancorato a spedito_il = momento della
  consegna a mano. Vetrina: i 4 campi in CAMPI_VETRINA; param
  `solo_spedizione` su /api/listings (gli storici '' restano fuori:
  il filtro promette un costo dichiarato) — e dal lug 2026 i suoi due
  gemelli `solo_ritiro` (consegna IN ritiro/entrambe) e
  `solo_digitale`, che è l'unico a guardare il SET delle strade
  (`consegna='digitale' OR anche_digitale=1`: la combo va presa, ed è
  la regola di `stradeConsegna()` nel client, dove la DEMO chiede
  proprio a lui invece di ripetere la condizione a mano). Tre spunte
  che si SOMMANO: spedizione+ritiro = solo chi offre tutte e due.
  Le etichette non dicono «Solo con…» (lug 2026): «🚚 Spedizione ·
  🤝 Ritiro in zona · 💾 Codice online · ⚡ In offerta» — sono spunte
  dentro un pannello che si chiama Filtri, il «solo» lo dice il posto;
  `protezione_percento`
  nella busta di prima pagina (la stima del client non hardcoda mai
  la cifra). NIP-99: la spedizione è una riga del CONTENT, nessun tag
  nuovo. Import CSV: colonne facoltative `consegna;spedizione;taglia`
  nel modello e nel parser. La modifica FIRMATA degli importati non
  offre i campi (v1: l'evento non li porta, il form li nasconde).
  Frontend: form Vendi con le TRE CASELLE indipendenti (lug 2026,
  decisione di Andrea, via il select + checkbox: 🚚 Spedizione ·
  🤝 Ritiro in zona · 💾 Invio del codice online, spunta tutte quelle
  che offri, ALMENO una — la validazione vive in publish(), il server
  resta tollerante con '' per i client vecchi; `consegnaForm()` mappa
  le spunte sulle strutture di sempre consegna+anche_digitale, che
  reggono tutte le 7 combinazioni senza colonne nuove, e
  `impostaConsegnaForm()` è il verso opposto per precompilazione e
  reset; costo e taglia compaiono solo con Spedizione spuntata;
  l'hint «una sola strada» con ≥2 spunte è vissuto un giorno e tolto
  come rumore — l'hint del codice online invece è OPERATIVO, dice al
  venditore cosa dovrà fare («lo consegnerai dentro Barattolo dopo il
  pagamento: niente chat private»); allineamento caselle: servono i
  selettori SPECIFICI `.field label.cons-riga`/`.field .cons-riga
  input`, le regole generiche di .field (maiuscoletto, padding da
  campo) vincerebbero sulla classe nuda; LE ICONE sono 20px contro i
  13,5 del testo (`.cons-ico`, `display:inline-block` e
  `line-height:1` o un'emoji da 20 dentro una riga da 13,5 raddoppia
  la casella; la spunta resta 17px, è un controllo e non un disegno):
  lì si sceglie COME arriva la roba, e le tre strade si distinguono
  dal disegno, non dalla riga di testo. La spedizione parla col 🚚 e
  non col 📦 (lug 2026): il camioncino è la spedizione in TUTTA l'app
  — icone della card, badge del dettaglio, spunta dei filtri — mentre
  il 📦 nel progetto è il pacco della TAGLIA, roba del corriere;
  erano due disegni per la stessa strada, e quello sbagliato stava
  proprio dove la strada si sceglie. La firmata
  degli importati salta la validazione, il campo resta nascosto) +
  costo (stessa valuta del listino, `consegnaPayload`) + taglia;
  dettaglio con le PILLOLE DELLE MODALITÀ (lug 2026, dopo il feedback
  di Andrea: il 🚚 muto della card qui diventa parola) —
  `pilloleModalita()` scrive una pillola per le strade DISCRETE
  («🤝 Ritiro in zona», «💾 Codice online»); la SPEDIZIONE dal
  riordino del dettaglio (sotto) non sta più lì: è il badge
  evidenziato `spedBadge()` accanto al prezzo. SENZA il costo
  nella fila delle pillole (lug 2026): una cifra sciolta tra le
  pillole si legge come un prezzo e non dice di che totale fa parte
  — il posto del costo è il momento del pagamento, dove c'era già
  (foglio «Come vuoi riceverlo?» col totale per strada, riga
  «Spedizione» del `contoScomposto`, e il totale dei bottoni compra
  che la spedizione l'ha sempre inclusa).
  [SUPERATA, ago 2026 — SFOLLAMENTO COLORI, decisione di Andrea: la
  gratuità si evidenzia col GRASSETTO, mai col colore. Il chip azzurro
  «Spedizione gratuita» è morto: le pillole di consegna sono TUTTE
  neutre (.pill, un solo cuore) con «gratuita» in grassetto, e il
  «🚚 gratis» in card parla l'inchiostro di casa (var(--ink), token:
  di notte è crema) in grassetto. E dall'ago 2026 la REGOLA CSS
  `.sped-badge` non c'è più: restava orfana a far credere a chi legge
  il foglio che qualcosa la usasse. I token --ship-soft/--ship-soft-on
  restano definiti — come --ship-card — ma senza più chi vestire: sono
  vestiti appesi, e toglierli è una decisione di palette e non la
  pulizia di una regola morta. La famiglia --ship VIVA è
  --ship-bg/--ship-text, che vestono il badge di stato «spedito».
  La storia sotto resta per i perché.
  ATTENZIONE al € del dettaglio d'asta: `.detail-price .unit.eur` sta
  PIÙ IN BASSO nel foglio a pari specificità — il token dell'asta lo
  vince nominando `.asta` E `.unit.eur` insieme, per specificità e non
  per ordine (bug visto da Andrea nei due temi).]
  UN SOLO CHIP COLORATO, ED È «GRATIS» (lug 2026, decisione di Andrea
  in quattro tempi — vale la pena tenere l'arrivo, non il percorso).
  Il colore veste UNA cosa sola: che la spedizione non si paga.
  «🚚 Spedizione disponibile», «🤝 Ritiro in zona» e «💾 Codice online»
  sono dati di FATTO e stanno tutti e tre in `.pill` normali; solo
  «🚚 Spedizione gratuita» è il chip azzurro `.sped-badge`. Il perché:
  due chip colorati in fila si facevano concorrenza, e quello che
  diceva meno era anche quello che compariva più spesso (quasi ogni
  annuncio spedisce, pochi lo fanno gratis). La gratuità invece è un
  argomento di vendita e non può aspettare il fondo pagina.
  Giudici unici `spedisce` e `spedGratis` — «gratis» si decide in un
  posto solo, e da lì lo legge anche la card.
  IL COLORE È UNO E NON CAMBIA SEGNO COL TEMA. `--ship-soft` (fondo) e
  `--ship-soft-on` (testo) vestono il chip del dettaglio: azzurro
  chiaro con testo blu, 5,62. Un colore che SIGNIFICA qualcosa non può
  cambiare tinta fra il giorno e la sera, o chi l'ha imparato di
  giorno non lo riconosce più; l'inversione al buio ha senso per una
  SUPERFICIE (l'etichetta prezzo, il toast, che di sera diventano di
  carta), mai per un codice colore. L'UNICA cosa che si tara di notte
  è la LUCE: al buio i due scendono a #AEC8E0/#0E4A80 perché sul bruno
  lo stesso chiaro rendeva più che sul crema (contro il fondo 13,59 →
  11,04 → 9,95, in due gradini, il secondo chiesto da Andrea dopo
  averlo visto a schermo; il testo scende con lui e tiene 5,25).
  Attenzione alla distinzione, che è tutta la regola: si abbassa la
  luce, non si cambia il segno.
  IN CARD la stessa idea si SCRIVE: «🚚 gratis» accanto alle altre
  icone, in `--ship-card` — terzo token, e l'unico dei tre che SEGUE
  IL TEMA (#12599E di giorno, #9FC9EA di sera). Non è un'eccezione: lì
  «gratis» è TESTO NUDO sulla carta della card, e un testo deve
  contrastare la superficie su cui sta — il blu scuro sulla card bruna
  farebbe 1,67, cioè sparirebbe (8,68 così). Il segno è il chip,
  questo è inchiostro, e l'inchiostro segue la carta come ovunque
  nell'app; la famiglia (blu) resta la stessa. Si SCRIVE e non si
  colora soltanto perché un cerchietto non insegna niente a chi guarda
  la prima volta, e da quando il chip è l'azzurro chiaro non c'era più
  nemmeno un colore forte da riecheggiare a 15px. Costa ~21px al
  comune, che nel caso a tre strade scende da 69 a 47px e si tronca
  prima («Carma…»): prezzo accettato e misurato — «gratis» fa cambiare
  idea a chi compra, le ultime lettere di un paese no. La regola di
  sempre non si tocca: a cedere è il luogo, mai il gruppo di icone.
  TRE COSE PROVATE E SCARTATE, da non rifare (i motivi, non solo i
  nomi): 1) il badge PIENO blu scuro per «gratuita» contro il tenue
  per «disponibile» — due gradi della stessa famiglia si somigliavano
  troppo, e al buio il tenue spariva nel fondo; 2) SCAMBIARE i due
  colori perché «il chiaro spicca di più» — spicca di più SOLO di
  sera: sul crema il chiaro fa 1,15 contro il fondo, cioè è una
  velatura, quindi scambiandoli nel tema di DEFAULT «gratuita»
  diventerebbe la cosa più muta della fila e «disponibile» la più
  forte, in concorrenza col prezzo; 3) il cerchietto colorato attorno
  alla 🚚 in card, sostituito dalla parola per la ragione qui sopra.
  E una valutata e scartata a tavolino: colorare il RITIRO invece
  della spedizione. Il ritiro vale solo per chi è vicino — colorarlo
  significherebbe gridare a tutti gli altri una cosa che non possono
  usare — mentre «gratis» è un risparmio che vale per chiunque guardi;
  e la località la dice già il comune, lì accanto nella stessa riga.
  Se un giorno si vorrà spingere lo scambio locale, la leva non è il
  colore di un chip ma un filtro «vicino a me».
  IL GEMELLO COL COSTO SOTTO ACQUISTA È VISSUTO UN GIORNO: nato per
  dire il QUANTO nel momento in cui si compra («🚚 Spedizione +
  5,00 €», dentro il recinto), è stato tolto subito dopo averlo visto
  — e la ragione vale anche per chi volesse rimetterlo. Il recinto è
  il posto della FIDUCIA, non del listino: una cifra là dentro fa
  nascere la domanda «di che totale fa parte?» senza rispondere, e
  spezza la riga sola che il recinto deve dire. Il QUANTO vive dove
  c'è un totale VERO accanto: il foglio «Come vuoi riceverlo?» del
  varco (`cifraVia`), la riga «Spedizione» del `contoScomposto` nel
  paySheet, e i bottoni compra, che la spedizione l'hanno sempre
  inclusa. Con lui se ne sono andati `spedBadgeCosto` e
  `spedCostoTesto` (e la classe `.sped-riga`).
  LACUNA CHIUSA (ago 2026 — era «TEMPORANEA, DICHIARATA» dal lug
  2026): il costo della spedizione non si vedeva da nessuna parte
  nella scheda, e chi aveva la sola spedizione lo scopriva nel
  paySheet a invoice già nata. Il rimedio è arrivato com'era stato
  dichiarato: LA PAGINA D'ACQUISTO (vedi la voce sua) — scelta della
  strada e conto del server in un posto solo, PRIMA della invoice, e
  Acquista ci porta SEMPRE, anche con una strada sola. Resta vero il
  perché di allora: non si rimedia rimettendo una cifra nella scheda
  (fila delle pillole e recinto provati e scartati, vedi sopra). Con la vecchia riga del
  costo nella fila delle pillole se n'era andata
  `rigaConsegna` — la riga «🛡️ protezione acquisti inclusa» era
  rumore: la protezione c'è SEMPRE, quindi non è un'informazione, e
  a raccontarla è il recinto escrow. Il dettaglio
  mostra SOLO: data · luogo (se c'è) · consegna · condizione ·
  disponibilità (se >1) · verifica Nostr (nel riquadro venditore).
  NON la categoria (ci si
  arriva dai filtri) e NON la taglia del pacco (è roba del
  venditore e del futuro tariffario per-taglia, al compratore non
  serve lì; via anche `tagliaPill`).
  RIORDINO DEL DETTAGLIO (lug 2026, stile Subito.it): dall'alto —
  foto · riga data `dataRiga()` (piccola e grigia, `.pub-data`): il
  «quando» e basta, «3 giorni fa» — la pubblicazione NON si nomina
  (a quel posto non può voler dire altro), il verbo resta solo
  all'«aggiornato N giorni fa», che è un fatto diverso · titolo con
  la pillola condizione IN CODA, come fosse l'ultima parola («Crema
  spalmabile NUOVO»): `titoloConCondizione()` la mette DENTRO l'h2,
  nel flusso del testo, e la lega all'ULTIMA PAROLA con un nowrap
  (`.fine-titolo`) — così se sull'ultima riga non c'è posto scendono
  INSIEME («Cuffie da studio AKG / K371 Come nuovo») invece di
  lasciare la pillola sola a capo. Ultima parola oltre 14 caratteri
  = non si lega (legate traboccherebbero). Il flex è stato provato
  due volte e non regge: con la base `auto` manda a capo la pillola
  PRIMA di stringere il titolo, con `flex:1 1 0` la incolla a destra
  lontano dalle parole · luogo come TESTO nudo
  `luogoRiga()` (niente pillola) · prezzo — col listino BARRATO
  della lampo SEMPRE sotto di lui, in euro come in sats
  (`.prezzo-col` è una colonna: di lato le due cifre si leggevano
  come una riga di conto; stesso mono, 24px contro 28, e la
  barratura taglia la cifra ma non la parola «sats», che è piccola e
  sembrava sottolineata — la ferma un `display:inline-block`, che
  dal figlio la decorazione ereditata non si toglie altrimenti) — e
  a DESTRA sulla stessa
  riga il toggle valuta €/₿ (`.prezzo-riga`, gemello di quello
  della searchbar: stesso `setValuta`, stessa preferenza; i due si
  accendono insieme perché `aggiornaCurToggle` li pesca per
  `data-cur` e non più per id, e `aggiornaPrezzoDettaglio` riscrive
  il prezzo IN PLACE senza riaprire la scheda — openDetail
  azzererebbe pezzi scelti e strada) · sotto, la riga ≈ dell'altra
  valuta · la fila delle pillole, che si apre col badge EVIDENZIATO
  della spedizione (`spedBadge()`, coppia azzurra
  la coppia azzurra --ship-soft/--ship-soft-on, sua e solo sua: AA nei
  due temi, non fa concorrenza né all'arancio del prezzo né al verde
  escrow;
  forma da pillola come le vicine — stava accanto al prezzo per un
  giorno, ma il suo posto sono le caratteristiche; i due gradi e il
  gemello col costo sotto Acquista sono spiegati sopra) ·
  le altre
  strade come pillole discrete · «DESCRIZIONE» col suo titolino
  `.desc-tit` · riquadro venditore SOLO anagrafica: avatar, nome col
  🟣 in fila coi badge (icona nuda, pattern della testata negozio —
  la scritta «verificato su Nostr» e i ponti di contatto non stanno
  più qui: la verifica è dell'utente e si racconta nel negozio, dove
  i ponti già vivono), sfilza, stelle e freccia. Da lì in giù tutto
  com'era (recinto — che dalle correzioni del lug 2026 ospita il solo
  «Acquista» arancio centrato, con «Fai un'offerta» fuori sotto e
  senza più le pillole di scelta —, altri oggetti, barra col
  richiamo escrow: vedi barra d'acquisto). LA DATA: colonna `annunci.modificato` (0 = mai
  toccato) scritta da modifica() e dalla modifica firmata; per gli
  IMPORTATI l'import ci mette la data dell'EVENTO Nostr
  (`evento_ts` = created_at, che per un replaceable è la
  pubblicazione vera) su INSERT e UPDATE, e il client la mostra
  sempre come «pubblicato» (l'update di là sostituisce l'evento
  intero; `creato` resta l'ora dell'import e ordina la vetrina,
  NON va toccato: il cursore keyset ci vive sopra). Leva
  `GIORNI_DATA_ANNUNCIO` (60, 0 = spenta) nella busta di PRIMA
  pagina come protezione_percento: oltre, la riga sparisce — un
  annuncio stagionato non deve auto-denunciarsi. `a.modificato` in
  CAMPI_VETRINA (search e miei gratis via a.*).
  Il disegno della taglia — che vive ancora nel foglio-picker di
  Vendi e nella stima del set — dal lug 2026 porta la SCALA
  DISEGNATA: `tagliaSVG(id, box)` invece delle emoji, perché 📦 era la
  stessa per piccolo, medio e grande e la gradazione non si vedeva.
  L'ingombro resta fisso (viewBox 22x22 per tutte le voci) e la
  scatola CRESCE DAL BASSO — come una cosa appoggiata sul banco: le
  voci del foglio restano incolonnate e il confronto si legge a colpo
  d'occhio. Lati 8/12/16/20 (il primo tentativo 10/13/16/20 era troppo
  timido) e SOLO quadro + riga del coperchio: il nastro verticale,
  provato, a 8px si riduceva a un puntino di rumore. Tratto a
  `currentColor` come `jarSVG` (chiaro e scuro gratis) con un velo
  dello stesso colore che dà corpo; la busta è un oggetto suo — piatta
  con la piega a V — non una scatola piccola, e nella pillola
  la busta, nei testi, non si fa chiamare «pacco busta» ma «busta
  imbottita». Scartate le emoji scalate via CSS: cambiano forma da un
  sistema all'altro, non seguono i token del tema e crescendo spostano
  le righe. `box` è solo la misura resa (22 nel foglio-picker e nel
  campo: il viewBox non cambia, quindi il rapporto fra le taglie
  resta identico a ogni misura). Per
  'entrambe' due pillole spedizione/ritiro DENTRO l'escrow-zone
  (`consegnaScelta`, si riparte da spedizione a ogni dettaglio; la
  cifra dei bottoni è `totaleStima`); conto scomposto
  (`contoScomposto`) nel paySheet e nella conferma NWC — stima
  subito, valori VERI dalla risposta di /orders; ordine con riga
  consegna+quote, pannello «🤝 Consegna in zona» con
  `markConsegnaMano` al posto di corriere/tracking, `payoutPanel` e
  testa released = totale − protezione; checkbox «🚚 Solo con
  spedizione» nei filtri (in DEMO client-side in renderGrid); icone
  discrete nella meta della card — il prezzo in griglia resta pulito.
  LA RIGA META DELLA CARD (lug 2026): il comune a sinistra, le icone
  in un GRUPPO stretto a destra (`iconeCard` → `<span class="ico">`,
  ordine 🚚 🤝 💾 come nel dettaglio; il 🤝 del ritiro prima in card
  non c'era). SOLO le strade di consegna: il pallino Nostr è USCITO
  dalle card (lug 2026) — in griglia lo spazio è poco, e la verifica
  riguarda il VENDITORE, non l'oggetto: vive nel dettaglio, accanto
  al suo profilo, che è dove uno se la chiede (il gruppo è passato da
  66 a 53px, e il comune ne ha guadagnati altrettanti prima di
  troncare). Prima le icone erano figli diretti di un flex
  `space-between` e si sparpagliavano per tutta la riga; ora a
  spartirsi lo spazio sono in due, e a cedere coi puntini è SEMPRE il
  comune (`.luogo` con `flex:1 1 auto` + `min-width:0`) mentre il
  gruppo non si stringe mai — a 360px con tutte e tre le icone
  insieme deve restare intero. `min-height:17px` sulla riga, che può
  essere vuota del tutto (zona non riconosciuta e nessuna icona) e le
  card resterebbero disallineate.
  La SPEDIZIONE GRATUITA si vede anche in griglia (lug 2026), e si
  SCRIVE: «🚚 gratis» accanto alle altre icone, nel blu `--ship-card`.
  Il perché della parola invece del solo colore, il costo misurato in
  pixel e le rese scartate stanno nella sezione della spedizione, sotto
  «UN SOLO CHIP COLORATO»: qui basti che a cedere resta il comune, mai
  il gruppo di icone.
  Consegna digitale 💾 (lug 2026, quarta voce di MODALITA_CONSEGNA):
  per buoni regalo, codici, licenze — il PRINCIPIO CARDINE è che il
  contenuto passa DENTRO Barattolo, mai fuori. La modalità è LIBERA
  dal tipo di bene (una gift card fisica si spedisce, un codice si
  consegna digitale: le tutele seguono la modalità, mai il tipo);
  niente costo spedizione né taglia (consegna_da_payload azzera anche
  la taglia arrivata per sbaglio). COMBO (lug 2026, la gift card in
  due modi «ti spedisco la tessera, oppure ti mando il codice»):
  colonna `annunci.anche_digitale`, ORTOGONALE di proposito —
  `consegna` tiene la semantica fisica di sempre e ogni check
  esistente resta vero; lecita solo accanto a una modalità fisica
  (con 'digitale' o '' il giudice la forza a 0). Le TUTELE seguono la
  SCELTA del compratore, non l'annuncio (già così per costruzione:
  finestre, blocco di segna_spedito, endpoint contenuto, tetto
  compratori e pannelli leggono `consegna_scelta`): compra() valida
  contro il SET delle strade offerte (spedizione/ritiro dal catalogo
  + digitale se esclusivo o anche_digitale), scelta sconosciuta non
  vuota = 400, scelta assente = default FISICO (spedizione batte
  ritiro, digitale solo se unica: il client vecchio in cache prende
  la strada che conosce); `guardia_venditore_digitale(tg_id,
  consegna, anche_digitale)` copre la combo, anche nell'import CSV
  dove la cella consegna parla col «+» (`spedizione+digitale`,
  riga d'esempio nel modello). `anche_digitale` è in CAMPI_VETRINA;
  NIP-99 aggiunge «o consegna digitale immediata» (e il ritiro combo
  perde il «solo»). Frontend: la combo nasce spuntando la casella
  «💾 Invio del codice online» accanto a una fisica (vedi le tre
  caselle nella sezione spedizione: il vecchio checkbox «Offro
  anche…» e il select non esistono più, «consegna digitale» era
  ambigua e i testi pubblici ora dicono «codice online»);
  la scelta della strada vive nel foglio «Come vuoi riceverlo?» del
  varco (`stradeConsegna` resta il giudice delle strade offerte; le
  vecchie pillole di scelta `pilloleConsegna` dentro l'escrow-zone
  sono morte con le correzioni del lug 2026 — in pagina restano solo
  le pillole INFORMATIVE, che raccontano e non si toccano);
  trust-note asimmetrica `#notaDigitale` visibile SOLO con la scelta
  digitale attiva (su una combo non deve spaventare chi sceglie la
  spedizione, `setConsegnaScelta` la accende/spegne); la pillola
  «💾 Codice online» di `pilloleModalita` (che ha sostituito il vecchio
  «o 💾 codice online» della riga sotto il prezzo, `rigaConsegna`,
  poi sparita del tutto); in card 🚚, 🤝 e 💾 possono convivere.
  NIENTE stati nuovi: locked→shipped
  = `POST /api/orders/{id}/consegna-digitale` (solo venditore,
  contenuto 1-4000 caratteri, corriere-sentinella 'Consegna digitale',
  riga journal con impronta sha256 troncata e MAI il testo);
  shipped→delivered = la RIVELAZIONE, `GET /api/orders/{id}/contenuto`
  — la PRIMA lettura del compratore scrive `consegnato` (= ricevuta di
  lettura) e fa la transizione, le successive sono idempotenti; il
  venditore rilegge ciò che ha consegnato senza effetti, l'admin legge
  solo negli stati di disputa. `ordini.contenuto_digitale` (colonna
  nuova) è cifrata a riposo con Fernet — `CHIAVE_CONTENUTI_DIGITALI`
  in config, prefisso **'f2:'** dall'ago 2026 (audit): la chiave si
  derivava con uno SHA-256 a passata singola e senza sale, che contro
  una passphrase debole costa un hash a tentativo; ora **scrypt**.
  Conta solo se la chiave è debole — con una casuale la ricetta di
  prima bastava — ma il config dice «una stringa segreta qualsiasi», e
  la promessa dev'essere vera anche per chi la prende alla lettera.
  Il sale è FISSO e in chiaro, ed è voluto: Fernet non ha dove
  metterne uno per riga, e un sale non è un segreto — il lavoro lo fa
  scrypt. Chiave vuota o cryptography assente =
  'plain:' in chiaro, fail-open — che ora l'AVVIO DICE con una riga:
  il caso silenzioso era anche quello di serie (`config_esempio.py`
  nasce con la chiave vuota), e un fail-open dichiarato va anche detto
  o è solo silenzio. I TRE formati convivono per sempre
  (_cifra_contenuto/_decifra_contenuto): un database scritto ieri non
  deve diventare illeggibile con un aggiornamento, e il meccanismo dei
  prefissi esisteva già apposta — nessuna migrazione. E NON esce MAI da
  /api/orders (strip con flag `contenuto_presente`): si legge solo
  dall'endpoint-ricevuta. `segna_spedito` su ordine digitale = 400
  (il timer non deve partire senza contenuto consegnato). Finestre
  CORTE in controlla_scadenze: ORE_CONFERMA_DIGITALE (24) dalla
  rivelazione, ORE_SILENZIO_DIGITALE (48) dalla consegna mai rivelata
  — i due rami fisici escludono il digitale. Il caso irriducibile
  (codice riscattato e poi negato) NON si risolve, si rende
  antieconomico: regola di default ASIMMETRICA dichiarata prima
  dell'acquisto («un codice rivelato non torna indietro: 24 ore per
  aprire una disputa, poi l'acquisto è definitivo» — trust-note nel
  dettaglio, confirm della rivelazione, notifica di consegna; dal
  lug 2026 MAI «salvo prove» né promesse di rimborso verso il
  compratore: Barattolo non può verificare i riscatti, deciso con
  Andrea — i consigli-screenshot al VENDITORE restano, sono le prove
  che porta lui), nota al moderatore in apri_disputa (conteggio
  dispute del compratore = le dispute-fotocopia si vedono, + invito
  a chiedere all'emittente quando/dove il codice è stato riscattato,
  e la precisazione che la regola «a zero prove vince chi ha
  consegnato» segue il BENE riscattabile, non il canale: vale anche
  per un buono spedito fisicamente), e leve config SPENTE di
  serie (default 0, pattern TETTO_SATS_ANNUNCIO):
  TETTO_DIGITALE_NUOVI (compratore con acquisti_ok=0 oltre il tetto =
  400, sul solo articolo, in compra()) e DIGITALE_MIN_VENDITE
  (`guardia_venditore_digitale` in pubblica/modifica, riga scartata
  nell'import CSV). SERVIZI ESCLUSI (decisione di prodotto, lug 2026):
  Barattolo vende COSE che esistono, fisiche o digitali — il
  PROMPT_MODERAZIONE vieta prestazioni e servizi («VIETATO: servizio»)
  e whitelista i prodotti digitali leciti (buoni regalo, gift card,
  codici sconto, licenze — nato dal buono Zalando bloccato per
  errore); `messaggio_rifiuto(motivo)` mappa il no dell'AI sui servizi
  al gentile MSG_RIFIUTO_SERVIZI («non ancora supportati»), 'servizi
  sessuali' resta col messaggio severo di sempre. Frontend: casella
  «💾 Invio del codice online» in Vendi con hint screenshot datato
  («in disputa le prove decidono», ripetuto nel pannello di
  consegna); dettaglio con riga «💾 codice inviato online, subito» +
  trust-note asimmetrica; 💾 nella meta della card; ordine con stepper
  «Contenuto consegnato → Rivelato» (finestra 24h nel testo), pannello
  venditore con textarea (`consegnaContenuto`), box «🔓 Rivela» col
  confirm-ricevuta (`rivelaContenuto`), rilettura `mostraContenuto` e
  copia di pagina `contenutoRivelato` (il testo non vive in orders:
  arriva solo da /contenuto); per il compratore niente «è arrivato»
  su shipped digitale (la strada è la rivelazione). NIP-99: riga
  «consegna digitale immediata» nel content, nessun tag nuovo; gli
  importati restano fuori per natura (consegna '': per consegnare il
  codice il venditore deve essere in piattaforma). Modello CSV con la
  riga d'esempio `digitale` (parser già coperto dal giudice unico).
  Offerte / contrattazione sul prezzo (lug 2026, modello Vinted; sara'
  la base del futuro «Lotto», fase 3): NON una chat — macchina a stati
  con al massimo UNA controproposta. Tabella `offerte` (annuncio,
  parti, `valuta` fotografata dal listino, importo_sats/importo_eur
  della proposta e contro_sats/contro_eur della controproposta — uno
  dei due campi sempre 0; UN solo campo `scadenza` riscritto a ogni
  transizione; `ordine_id` = ponte verso l'ordine). Stati: proposta →
  controproposta → accettata → conclusa, più rifiutata / scaduta /
  decaduta. REGOLA CARDINE: l'annuncio non si blocca mai — vince chi
  paga per primo, le offerte rimaste vive decadono con la notifica di
  garbo 🕊 (MAI al compratore vincente). L'accordo riguarda il SOLO
  articolo: spedizione e protezione si sommano sopra come per ogni
  ordine (protezione sull'articolo concordato). Leve config (pattern
  try/except): OFFERTA_MINIMA_PERCENTO (50, minimo per ECCESSO sui
  sats), ORE_RISPOSTA_OFFERTA (48), ORE_PAGAMENTO_OFFERTA (24),
  MAX_OFFERTE_ANNUNCIO (3 tentativi totali per compratore per
  annuncio, UNA attiva alla volta — count-guard senza await, patto
  anti-doppione). Endpoint: `POST /api/listings/{id}/offerta` (importo
  nella valuta del listino, virgola ammessa; ≥ listino = 400 «puoi
  comprare direttamente»; qui il cambio non serve MAI: mai 503),
  `POST /api/offerte/{id}/rispondi` (azione accetta|rifiuta|contro;
  gate di ruolo per stato: proposta = venditore, controproposta =
  compratore e il ping-pong finisce li'; contro > offerta e
  ≤ listino; scadenza controllata anche inline), `GET
  /api/me/offerte` (busta con le leve: il client non hardcoda cifre),
  `offerte_da_agire` in /api/me e `offerta_minima_percento` nella
  busta di prima pagina. L'acquisto: `compra()` con `offerta_id` =
  stessa strada di sempre ma articolo alla cifra pattuita
  (`_importo_accordo`: la contro se c'e', senno' la proposta; EUR
  convertito alla invoice col cambio_ordine, drift/tetto/protezione
  invariati); il legame `offerte.ordine_id` si scrive NELLA stessa
  transazione dell'INSERT; invoice viva gia' in corso = 400 (pagare
  la vecchia lascerebbe l'offerta orfana). `verifica_pagamento`:
  l'offerta dell'ordine pagato → 'conclusa', TUTTE le altre vive
  sull'annuncio → 'decaduta' (notifiche dopo il commit). Reaper e
  annulla_ordine azzerano `ordine_id` (l'offerta resta accettata fino
  alla SUA scadenza: si ripaga con invoice nuova). `scadenze_offerte`
  nell'orologio: scadenza passata → 'scaduta', annuncio non piu'
  attivo → 'decaduta' (copre le rimozioni senza ganci nei delete).
  `modifica()` col prezzo cambiato fa decadere le PENDENTI (erano una
  % di un prezzo che non esiste piu'); le ACCETTATE sopravvivono
  (l'accordo e' stretto). Dal lug 2026 valgono ANCHE per gli importati
  da Nostr (il catalogo e' uno solo, cambia solo chi firma il NIP-99):
  il venditore solo-Nostr riceve l'offerta via DM NIP-17 col link
  /annuncio/{id}, entra col login npub e risponde da qui. ATTENZIONE
  all'imperfezione dichiarata: l'import orario che riscrive il prezzo
  NON fa decadere le offerte pendenti (a differenza di `modifica()`) —
  la cifra e' assoluta, il venditore la giudica contro il nuovo listino
  e comunque scade da sola. `esegui_fusione`
  migra le offerte e cancella le auto-trattative tra le due meta'.
  Piu' offerte accettate possono coesistere: lecito, il confirm del
  venditore lo dichiara («accettare non riserva l'oggetto»). Frontend:
  «Fai un'offerta» subito FUORI dal recinto escrow (e a sinistra di
  Acquista nella barra; nascosto con accordo gia' fatto),
  foglio `#offertaSheet` (registrato in closeSheet) con miniatura+
  titolo+listino, chip −10%/−20% precalcolati, campo nella valuta del
  listino (virgola per EUR) e stima live «≈ N sats totali» (matematica
  di totaleStima con l'articolo offerto, onesta senza cambio); sezione
  «💰 Offerte» sopra gli ordini nella scheda Ordini (`renderOfferte`,
  solo trattative VIVE, azioni inline Accetta/Controproponi/Rifiuta
  con input che non si perde nei re-render, «⚡ Paga ora» per
  l'accettata) + pallino `.off-dot` sul tasto Ordini quando una
  offerta aspetta una MIA mossa; «Paga ora» RIAPRE il dettaglio, che
  con l'accordo mostra il banner 🤝 e i totali pattuiti (`artStima`
  dentro totaleStima) — pillole consegna, NWC, nota EUR ereditati
  gratis; startBuy e compraSubito mandano `offerta_id` (0 = ignorato).
  IL COMPRATORE RITIRA (ago 2026, caso vero: un'offerta mandata per
  sbaglio non si poteva togliere in nessun modo — si aspettava la
  scadenza o si chiedeva al venditore di rifiutarla, e intanto la
  guardia `attive` impediva perfino di rifarla giusta).
  `POST /api/offerte/{id}/ritira` + lo stato `ritirata`, che è una
  LAPIDE: la riga resta, come per gli ordini annullati.
  È IL GEMELLO SPECULARE DEL RIFIUTO — quello chiude dal lato del
  destinatario, questo dal lato del proponente — e per questo NON è
  un'azione di `rispondi_offerta`: il suo gate risponde alla domanda
  «di chi è il turno», e su una 'proposta' il turno è del VENDITORE,
  quindi infilarcelo dentro sarebbe un'eccezione al gate, cioè
  romperlo. Da rotta sua, in più, la guardia di proprietà sta dentro
  la WHERE col 400 dei fratelli (il patto dell'audit), che il gemello
  non ha: lui legge per solo id e risponde 404.
  SI RITIRA DA 'proposta' E DA 'accettata', mai da 'controproposta' —
  lì il compratore ha già «Rifiuta», che fa la stessa identica cosa e
  avvisa: due nomi per lo stesso gesto sarebbero un bivio senza
  risposta giusta davanti a chi deve scegliere.
  QUI NON C'È MAI ESCROW, ed è la riga da non ammorbidire: un'offerta
  è la cedola che serve a FABBRICARE un ordine, e finché l'ordine non
  c'è non si è mosso un sat. Quando l'ordine c'è già, IL PREZZO VIVE
  NELL'ORDINE (`ordini.prezzo_sats`, congelato alla invoice) e da qui
  non si tocca — chi un domani volesse «sistemare» dal ritiro un
  ordine appeso starebbe scrivendo il bug, non la cura. La prova più
  forte non elenca nomi: estrae con una regex TUTTE le scritture del
  corpo e chiede che il bersaglio sia sempre `offerte` (cattura anche
  un `UPDATE ordini` che nessuna lista vedrebbe), e l'ambiente della
  prova NON fornisce affatto i nomi dell'escrow — chi li tocca non fa
  una prova rossa, fa esplodere un NameError.
  A BLOCCARE È L'ORDINE VIVO, NON IL NUMERO, ed è la correzione che il
  cantiere ha fatto al proprio piano: con un `if off["ordine_id"]`
  secco un id appeso a un ordine non più 'creato' darebbe per sempre
  «prima annulla l'ordine», mentre `annulla_ordine` su un non-'creato'
  risponde «Operazione non permessa» — un vicolo cieco senza uscita.
  Si guarda `stato='creato'`, la forma già in casa in `compra()` e
  `_compra_set()`; così le due strade COMPONGONO SENZA CONOSCERSI
  (annulla l'ordine → `ordine_id=0`, plurale, che copre anche i set →
  l'offerta ridiventa ritirabile). C'è la prova apposta, e diventa
  rossa da sola se qualcuno rimette la guardia secca.
  IL CAS SULLO STATO LETTO serve, e il motivo NON è la concorrenza (qui
  non c'è un await in mezzo) ma il DOPPIO TAP su rete lenta: senza, il
  secondo POST manda al venditore una SECONDA notifica. Si confronta
  lo stato LETTO e mai un `IN (...)`: chi ha premuto guardando
  «proposta» mentre diventava un accordo prende il 409, rilegge e
  ritira consapevolmente. 409 e non 400 — nel progetto il 400 è «non
  ti è permesso», il 409 «il mondo si è mosso».
  IL GATE DELLA SCADENZA INLINE è copiato dal gemello e non è
  pignoleria: senza, il ritiro di un'accettata già morta manderebbe al
  venditore «ha ritirato l'accordo» mentre `scadenze_offerte` gli dice
  «non ha completato il pagamento in tempo» — due messaggi
  contraddittori sullo stesso fatto, e il bugiardo sarebbe questo.
  (Imperfezione EREDITATA dai tre chiamanti che già fanno così: quel
  timbro non notifica nessuno e l'orologio non ripesca più la riga,
  quindi la scadenza il venditore non la sente. Preesistente, non nasce
  qui, vale un cantiere suo.)
  IL VENDITORE LO SA SEMPRE (decisione di Andrea), con due testi: sulla
  proposta asciutto — non è un evento nuovo, è la correzione di uno
  vecchio, e lui la proposta l'aveva già ricevuta con «💰 Hai ricevuto
  un'offerta!», quindi il silenzio lo lascerebbe a rispondere a un
  fantasma; sull'accettata la riga che conta è «Nessun sat si era
  mosso», perché poteva credere di averli in arrivo.
  IL TETTO `MAX_OFFERTE_ANNUNCIO` CONTA LE RITIRATE, ed è già così per
  costruzione (`COUNT(*)` senza filtro di stato): non contarle
  aprirebbe uno spam illimitato — proponi 1 sat, il venditore riceve la
  notifica, ritiri, riproponi. E non toglie niente a nessuno: oggi chi
  sbaglia brucia comunque il tentativo E deve aspettare 48 ore, col
  ritiro ha gli stessi tentativi residui SUBITO. Il foglio lo dice, col
  numero preso dalla busta di `/api/me/offerte` e MAI un «te ne restano
  N» (quella busta ha un LIMIT: un numero contato lì potrebbe essere
  falso, e una promessa falsa è peggio di un'informazione mancante).
  NIENTE `guardia_ferie`: le accettate non decadono quando il venditore
  parte ma non si possono pagare, quindi il ritiro è l'unica via
  d'uscita pulita — vale il principio di `ritira_puntata`, «uscire coi
  propri sats non dipende da una leva». E ritirando il compratore
  LIBERA il venditore (il freno della lampo e la voce «stretta di mano
  già data» di `guardia_ferie` guardano `stato='accettata'`): non è
  solo un'uscita, è anche una restituzione — c'è la prova che quelle
  due eredità non si perdano.
  ZERO MIGRAZIONI: la colonna è TEXT, cambia solo il commento dello
  schema. Ereditano gratis `attive` e `totali` di fai_offerta,
  `offerte_da_agire`, `scadenze_offerte`, `_incassa_ordine`, i due
  preventivi e il filtro delle vive del client; e `rispondi_offerta` su
  una ritirata cade nel suo `else` col 400 «già chiusa».
  Frontend: «Ritira» (`.btn danger-ghost`, la veste di «Rifiuta») nei
  due rami del compratore — nel ramo accettata dentro un flex, che
  `.btn` è `width:100%` e due bottoni nudi si impilerebbero a tutta
  larghezza: è l'unico punto in cui il markup di `renderOfferte` cambia,
  e la card resta della stessa altezza (misurato prima/dopo).
  LA DOMANDA SI FA COL FOGLIO DI CASA — mai il `confirm()` del sistema
  operativo — e il foglio è quello UNICO, `#confermaSheet`: vedi «LA
  DOMANDA, UNA VOLTA SOLA» più sotto. Il gesto è spezzato in due:
  `ritiraOfferta` prepara i testi (che restano i due distinti: una
  proposta mai vista e un accordo che aspetta i sats non sono lo
  stesso gesto) e `inviaRitiro` esegue.
  LA DOMANDA, UNA VOLTA SOLA (ago 2026, `#confermaSheet`): i dialoghi
  del sistema operativo escono dall'app un gesto alla volta, e il
  foglio della conferma è UNO — chi apre passa titolo, testata
  facoltativa, corpo, etichetta del bottone e l'AZIONE, e
  `chiediConferma` fa il resto. Nasce col ritiro dell'offerta e serve
  subito accetta e rifiuta: tre fogli quasi identici sarebbero stati
  il difetto che il cantiere esiste per togliere, e i gesti che
  aspettano ancora (quelli sui sats) da qui costano una CHIAMATA e non
  un foglio. `confermaAzione` è anche la GUARDIA del bottone: si
  azzera prima di agire, o un doppio tocco manderebbe l'azione due
  volte (provato dal vivo). Il corpo si scrive con `textContent`,
  quindi i testi vanno NUDI — niente HTML da ricordarsi di scappare —
  mentre la testata è innerHTML e il titolo dell'annuncio ci passa da
  `esc()` dentro `testataOfferta`, che è un posto solo perché la
  vogliono tutti i chiamanti.
  IL FOGLIO SI CHIUDE PRIMA DI AGIRE, e ciò che l'azione ha da dire lo
  dice il toast. È il contrario del RIFORNIMENTO, ed è la distinzione
  da tenere quando si sceglie quale forma dare a un gesto: là dentro
  c'è un numero da CORREGGERE, quindi sull'errore il foglio resta
  aperto col valore dentro; qui non c'è niente da correggere (il 400
  del ritiro dice «paga o annulla l'ordine», il 409 «ricarica») e
  tenerlo aperto sarebbe solo un ostacolo in più.
  `#paccoSvuotaSheet` NON si è fuso dentro il generico, ed è
  deliberato: la ✕ del carrello ha una liturgia sua (svuota, chiude la
  pagina, più la guardia «niente da buttare») che dentro un generico
  diventerebbe un caso particolare — un generico serve dove i gesti si
  somigliano DAVVERO. La CONTROPROPOSTA non chiede niente: si sta già
  scrivendo una cifra in un campo, e una domanda in più sarebbe un
  ostacolo, non una tutela.
  E I DUE `prompt()` SONO MORTI nello stesso giro. Il primo era la
  durata del rilancio d'asta — un PICKER TRAVESTITO, cioè la cosa che
  questo progetto ha già tolto da ogni tendina: ora è `#rilancioSheet`
  con le pillole `consegna-pill` del form Vendi e le durate dalle
  leve, ma con una variabile SUA (`rilancioGiorni`) perché un rilancio
  non deve riscrivere la durata che il venditore ha impostato nel form
  per il prossimo annuncio — c'è la prova che non tocchi
  `sellAstaGiorni`. Il secondo era la riscossione col bolt11
  (`#riscuotiSheet`), e lì il guadagno è tutto nel comportamento
  d'errore: dentro si incolla una invoice di duecento caratteri e il
  rifiuto tipico è «l'importo non corrisponde», cioè una invoice da
  rifare — col `prompt()` si perdeva tutto, ora il foglio RESTA APERTO
  col testo dentro e il motivo scritto sotto (la ricetta del
  rifornimento). Campo `textarea`, che una bolt11 non sta su una riga.
  LA PROVA CHE VALE PIÙ DI TUTTE è il censimento: **zero `prompt()` di
  sistema in tutto il client**, con un predicato che esclude
  `ev.prompt()` (l'API d'installazione PWA, che ci deve restare) e i
  commenti che raccontano la storia — e che si tortura su un finto
  prompt, o certificherebbe una pulizia senza aver guardato.
  RESTANO i `confirm()` dei gesti sui sats e quelli admin: sono
  dichiarati e si affrontano a gruppi, non tutti insieme.
  L'OFFERTA SI PORTA DIETRO I PEZZI (ago 2026): il venditore accettava
  un prezzo unitario a quantita' INDETERMINATA — `articolo = unitario
  * richiesti` e `richiesti` arrivava dal client senza nessun legame
  con l'accordo, quindi poteva ritrovarsi a vendere un pezzo o TUTTO
  LO STOCK alla cifra scontata, e scoprirlo con l'ordine. Era
  dichiarato nel confirm dell'app ma NON nella notifica del bot, che
  e' il posto da cui si accetta piu' spesso. Colonna
  `offerte.quantita`, la PRIMA migrazione su quella tabella.
  LA CIFRA RESTA L'UNITARIO, ed e' la decisione che governa tutto il
  resto: 1) si confronta col LISTINO, che e' unitario come il minimo
  (`OFFERTA_MINIMA_PERCENTO`) e come i due estremi della
  controproposta — col totale quelle quattro comparazioni cambiano
  significato, e «offro 120.000 su un listino di 50.000» si legge come
  un errore; 2) un totale andrebbe DIVISO, e romperebbe in silenzio la
  divisione a ritroso di `_righe_ordine` — la trappola che dal 12 ago
  2026 è sorvegliata dal censimento delle divisioni (il mono sconta, e
  la divisione riaggiunge sconto_sats); 3) nel set le righe portano
  `unitario_sats`, e un
  totale per riga sarebbe l'unica cifra non unitaria del sistema.
  L'equivoco si toglie dicendo ENTRAMBE le facce ovunque i pezzi siano
  piu' di uno: giudice puro `_cifra_accordo(valuta, sats, eur,
  quantita)`, che prende i
  CAMPI e non la riga (il patto di `in_ferie`) e ha il gemello client
  `cifraPezzi` — se i due divergessero, meta' dell'app direbbe una cosa
  e meta' un'altra sullo stesso accordo. Con UN pezzo, o con la
  quantita' non dichiarata, la cifra e basta: aggiungere sarebbe
  rumore, e c'e' la prova che quella frase non contenga «al pezzo».
  IL TOTALE VIENE PRIMO (decisione di Andrea): «120.000 sats per 3
  pezzi (144.000 sats al pezzo)» e non «X al pezzo × 3 = Y», che si
  leggeva come un CALCOLO — la prima cosa che si vuole sapere e' quanto
  si paga (o si incassa) in tutto, e l'unitario resta in coda perche' e'
  la cifra che si confronta col listino. Nella riga del foglio le due
  cifre hanno anche una GERARCHIA (`.off-unitario`: il totale in
  grassetto, la parentesi piu' piccola e muted). L'unita' resta anche
  dentro la parentesi, ed e' l'unico punto in cui il testo di Andrea
  non si segue alla lettera: un numero nudo vorrebbe una seconda
  implementazione della regola del ≈ accanto a `cifraCtrl` — che ha
  apposta la sentinella «un solo `function cifraCtrl`» — oppure uno
  strip dell'HTML con una regex.
  0 = NON DICHIARATA, ed e' il mondo di ieri byte per byte: nessun
  DEFAULT 1 e nessun backfill, perche' sulle offerte gia' aperte al
  deploy nessuno ha mai concordato un numero e scriverne uno
  riscriverebbe un accordo stretto in due (il residuo si esaurisce da
  se' in ≤72 ore: 48 di risposta + 24 di pagamento). In scrittura la
  dichiarazione e' la PRESENZA della chiave nel payload e mai il valore
  — il patto di `spedizione_punto_dichiarata` — e il numero si LIMA
  allo stock (il patto di `quantita_tollerante`: un numero fuori scala
  non deve far fallire una trattativa). NON si usa
  `quantita_da_payload`: quello e' il giudice della quantita'
  dell'ANNUNCIO e solleva 400 sopra `MAX_QUANTITA_ANNUNCIO`, mentre qui
  il tetto vero e' lo stock, che e' piu' stretto.
  LA QUANTITA' COMANDA NEI QUATTRO PERCORSI del conto (`compra`,
  `_compra_set`, `preventivo_ordine`, `_preventivo_set`): il numero del
  client si IGNORA — puo' venire da una cache di ieri — ed e' ESATTA e
  non un tetto (decisione di Andrea: un significato solo da spiegare, e
  il venditore sa cosa ha accettato). Conseguenza in vetrina: lo
  stepper sparisce da «Acquista», che porta un `× N` statico, e la
  cella del carrello si PINNA (col «−» che toglie la riga intera: un
  accordo si prende o si lascia, non si lima — senza, il pezzo non si
  potrebbe piu' togliere).
  L'ORDINE DELLE GUARDIE NON SI TOCCA, ed e' la riga da non
  ammorbidire: portare il blocco dell'offerta SOPRA la RIPRESA sembra
  la mossa pulita ed e' una REGRESSIONE — la guardia `off["ordine_id"]`
  scatterebbe prima che la ripresa faccia il suo lavoro, e il
  compratore che ritenta con la sua stessa offerta prenderebbe un 400
  invece di ritrovarsi la sua fattura (provato: spostandolo, due
  sentinelle diventano rosse). Quindi il fail-fast di cortesia guarda
  ancora il numero del CLIENT, e subito dopo aver fissato `richiesti`
  si rifa' il controllo sul disponibile — una LETTURA e nessun DML,
  prima della invoice: il patto del ricontrollo resta intatto. Serve al
  caso «client manda 1, accordo 3, ne restano 2», che altrimenti
  prenderebbe il 409 secco del ricontrollo invece del 400 che dice
  quanti ne restano. CORNER DICHIARATO: un client che chiede PIU' pezzi
  dell'accordo con lo stock in mezzo fra i due prende il 400 del primo
  fail-fast — col client nuovo non puo' succedere (lo stepper non c'e'
  piu'), e l'esito e' comunque un rifiuto con un messaggio vero.
  STOCK SCESO SOTTO L'ACCORDO: il 400 onesto, e l'offerta resta
  'accettata' fino alla SUA scadenza — se il venditore rifornisce entro
  quelle ore, si paga. Mai un cambio silenzioso di un accordo stretto
  in due. NESSUNA guardia nuova su `rispondi_offerta`: accettare non
  riserva niente e l'accettazione non ha mai guardato lo stock, e non
  si aggiunge una regola al percorso dei soldi per questo.
  ACCETTARE NON RISERVA NIENTE, e va RIDETTO dove il numero si vede: un
  negozio con 4 pezzi puo' accettare tre offerte da 3 e trovarsi
  impegnato per 9. Il meccanismo e' identico a ieri — l'annuncio non si
  e' mai bloccato — ma col numero SCRITTO il venditore si sente piu'
  impegnato di quanto sia. Quindi la riga compare in tre posti e solo
  coi pezzi >1: il confirm (che gia' lo diceva), il pannello delle
  offerte (che non lo diceva) e la notifica del bot, da cui si accetta
  di piu'. Col pezzo singolo i testi restano quelli di sempre.
  IL FOGLIO RIFATTO nello stesso giro: tre pillole («−10%», «−20%»,
  «Personalizzato») SENZA il controvalore — erano due cifre in
  concorrenza con quella che conta.
  IL CAMPO È SEMPRE VISIBILE E MODIFICABILE (ago 2026, dal campo, e
  ROVESCIA la prima stesura in cui si vedeva solo sulla terza
  pillola): le pillole lo RIEMPIONO, non lo nascondono — chi parte da
  −10% e poi ritocca dev'essere libero di farlo, e «Personalizzato»
  mette a fuoco un campo che c'è già, col testo selezionato.
  E LA PILLOLA ACCESA NON SI RICORDA, SI DEDUCE dalla cifra: con una
  scelta memorizzata, dopo un ritocco l'etichetta direbbe il falso —
  «−10%» acceso su una cifra che −10% non è più. Derivata non può
  mentire, e la variabile che la teneva non esiste più.
  IL CAMPO DICE «AL PEZZO» mentre si digita (sotto l'unità, e SOLO
  coi pezzi scelti >1: col pezzo singolo sarebbe rumore). Il perché è
  un rischio vero: la cifra è l'unitario, ma chi vuole tre pezzi
  ragiona sul TOTALE e rischia di scrivere 120 intendendo il totale
  mentre ne sta offrendo 360 — e prima lo si scopriva dalla riga
  sotto, cioè DOPO aver scritto. Va a capo e non in riga, o a 320px
  il suffisso si mangia il campo (misurato: così resta largo 236px).
  IL MINIMO NON È UN CARTELLO PERMANENTE: compare SOLO quando la
  cifra ci finisce sotto, come avviso inline (la veste di
  `#zonaHint`). Dirlo prima che serva è rumore, e affiancava un
  numero che non c'entra con quello che si sta scrivendo; il client
  arrotonda per ECCESSO come il server, o direbbe «va bene» a una
  cifra che di là viene rifiutata. E SOTTO IL MINIMO SPARISCE IL
  TOTALE: calcolare il totale di un'offerta che non si può inviare è
  rumore, e affianca due righe dove ne serve una sola. Torna da sé
  appena la cifra risale.
  Toggle €/₿ in testata (`.sheet-testa`, col titolo che
  cede coi puntini): governa la LETTURA — listino, minimo e riga
  dell'offerta, che sono i tre numeri da confrontare e in due lingue
  diverse non si confrontano affatto (visto a schermo).
  E DAL 10 AGO 2026 GOVERNA ANCHE IL CAMPO, che ROVESCIA la riga che
  stava qui («il CAMPO resta nella valuta del listino»): era un mezzo
  bug e si è visto dal campo — si scriveva 40.000 in sats, si passava
  a euro, la riga sotto convertiva e il campo diceva ancora 40.000,
  che in euro è tutta un'altra offerta. Adesso il campo parla la
  valuta MOSTRATA e ne porta il simbolo accanto (`offSuffisso`), così
  si vede sempre in cosa si sta scrivendo. Resta vero il perché di
  allora — l'accordo esiste solo nella valuta del LISTINO, l'unica che
  il server accetta — e quindi la conversione avviene in `inviaOfferta`,
  UNA volta sola: il campo è una vista, il listino è la sostanza.
  L'ANCORA È CIÒ CHE IMPEDISCE ALLA CIFRA DI DERIVARE, ed è la riga da
  non ammorbidire: si tiene la cifra COM'È STATA SCRITTA (`offCifra`)
  insieme alla valuta in cui lo è stata (`offCifraValuta`), e il
  toggle non la riscrive MAI — la RILEGGE convertita (`offCifraIn`).
  Così dieci toggle di fila costano sempre UNA moltiplicazione
  sull'originale, invece di una catena in cui ognuna parte dal
  risultato della precedente, che è il modo in cui un numero se ne va
  di centesimo in centesimo a ogni tocco. A scrivere l'ancora sono TRE
  posti soli — l'apertura che azzera, la pillola, l'oninput
  (`offertaScritta`) — e il render NON è fra questi: se riscrivesse
  l'ancora con la propria conversione, l'originale sparirebbe e la
  deriva tornerebbe (c'è la sentinella, e la mutazione che la rimette
  fa rossa la prova). Per la stessa ragione il campo si riscrive SOLO
  quando la valuta cambia davvero (`offCampoValuta`): un tocco sullo
  stepper chiama lo stesso render, e senza quel confronto
  normalizzerebbe sotto le dita una cifra che si sta ancora scrivendo.
  LE PILLOLE si CONFRONTANO nella valuta MOSTRATA — è il numero che si
  vede, e con la tolleranza di quella valuta (il centesimo in euro,
  l'unità nei sats: una conversione non torna mai al sat esatto) — ma
  PIANTANO l'ancora in quella del LISTINO, così il −10% che parte è
  esattamente −10% al sat qualunque cosa il campo stia mostrando.
  IL MINIMO fa il contrario, e la coppia è il punto: si CONFRONTA nella
  valuta del listino, che è quella su cui giudica il server, e si DICE
  in quella del campo arrotondato per ECCESSO (`offMinimoIn`) — chi
  scrive esattamente la cifra che legge dev'essere ammesso, mai
  rifiutato per un centesimo di conversione.
  E LA RIGA ECHEGGIA IL CAMPO invece di riconvertire la cifra del
  listino: su un listino in euro «50000 sats» vale 27,70 €, che
  riletto in sats fa 50.008 — e un campo che dice 50.000 con sotto un
  «≈ 50 008» si legge come un guasto, non come i centesimi che sono.
  Senza cambio vivo il campo resta sulla valuta del listino, che è
  sempre esatta: mai una conversione fatta col valore di riserva (è la
  stessa regola che `cifraOfferta` aveva già per la lettura — qui il
  numero conta davvero, e un ≈ su un valore di riserva sarebbe un
  numero inventato in faccia a chi sta per impegnarsi).
  LA QUANTITA' SI CAMBIA NEL FOGLIO, con uno stepper sotto il toggle —
  al posto del numero statico accanto al titolo, non in aggiunta: due
  numeri per la stessa cosa nello stesso foglio sarebbero il difetto
  che il cantiere esiste per togliere. E' lo STESSO `stepperMini` e la
  STESSA `setQta` del gemello, quindi il tetto (lo stock) e il
  comportamento al limite arrivano gratis invece che da una seconda
  guardia da tenere in pari. Soprattutto NON C'E' UNA SECONDA
  VARIABILE: il foglio scrive in `qtaScelta`, quella del numero accanto
  ad «Acquista» — chiudendo il foglio la barra dice gia' il numero
  nuovo, e i due non possono divergere perche' sono uno. `setQta`
  richiama `aggiornaFoglioOfferta()` se il foglio e' aperto, cosi' riga
  e totale si riscrivono al volo (la sentinella guarda DENTRO `setQta`:
  cercare quella riga nel file intero non poteva fallire, perche' la
  stessa vive in `setValuta` — l'ha detto la tortura). E il listino
  nella testata ha perso il suo «al pezzo»: lo stepper accanto gli
  rubava la riga e il testo andava a capo (visto a schermo), ed era
  ridondante — a dirlo resta la parentesi della riga.
  Via la riga «se accetta pagheresti…», che
  diceva un totale SENZA la spedizione — cioe' una cosa incompleta —
  al suo posto la riga «Offri X al pezzo × 3 = Y». Via «Annulla», al
  suo posto la ✕ in alto a destra (`.pacco-x`, il ✕ di casa: un secondo
  nome per la stessa forma sarebbe peggio del nome che invecchia), che
  chiude con `navIndietro()` e mai `closeSheet()`.
  IL TASTO OFFERTA PORTA LA QUANTITA' come il suo gemello, cosi' i
  pezzi si vedono PRIMA di aprire il foglio. Non uno stepper — da li'
  la quantita' non si cambia, e due stepper in fila litigherebbero: un
  numero statico. L'etichetta si ACCORCIA quando lo porta, e la ragione
  e' misurata: a 320px la barra concede a quel tasto ~118px e «Fai
  un'offerta» ne chiede gia' ~110, quindi diventa «Offri × 3» —
  «Offri» non e' una parola nuova, e' il verbo del bottone d'invio del
  foglio. Giudice UNICO `etichettaOfferta(l)` delle DUE superfici (la
  barra su mobile, il gemello `.offerta-pagina` da 768px in su): sono
  la stessa cosa vista da due larghezze e non devono poter dire due
  numeri, e `setQta` le RISCRIVE entrambe (a un pezzo l'etichetta torna
  «Fai un'offerta»: non e' una cifra da sostituire). La ripartizione
  `.con-qta` e' passata da 60/40 a 56/44, rimisurata a schermo: nasceva
  quando l'altro lato era nudo, e lo stepper «− N +» resta piu' largo
  di un «× N» ma non di tutto quello di prima.
  Piu' il titolo scappato in `fai_offerta`, che mancava mentre i tre
  fratelli ce l'avevano (la famiglia di B6).
  LA TASTIERA NON COPRE PIÙ QUEL CHE SI SCRIVE (ago 2026, dal campo:
  nel foglio dell'offerta si digitava alla cieca), e il perché non è
  ovvio: la tastiera del telefono NON rimpicciolisce il layout
  viewport — un `position:fixed; bottom:0` resta ancorato al fondo
  dello SCHERMO, cioè sotto i tasti — e nemmeno `100dvh` si accorcia
  su iOS. L'unico che lo sa è `visualViewport`, e quanto copre è
  `innerHeight - vv.height - vv.offsetTop`: l'offset serve perché a
  pagina scrollata dalla tastiera il viewport visuale si sposta, e
  senza quel termine il foglio si alzerebbe di troppo. La misura si
  divide per `--fs-zoom`, che arriva in pixel di VIEWPORT e si spende
  dentro `html`, che è zoomato (la ragione dei `calc(100vh / ...)`).
  Vale per TUTTI i fogli, non solo per questo, e a tastiera chiusa la
  variabile è 0 — cioè non cambia niente.
  SI ALZA IL FOGLIO APERTO, COL TRANSFORM E NON COL `bottom`: alzando
  il bottom si alzano anche i fogli CHIUSI — nascosti con
  `translateY(100%)`, cioè la loro altezza sotto l'ancora — e con
  l'ancora più in alto rientrano in vista. Difetto introdotto e visto
  sullo screenshot: sotto il foglio dell'offerta spuntavano quello dei
  distintivi e quello Nostr.
  E MENTRE LA TASTIERA È SU LA TRANSIZIONE SI SPEGNE
  (`html.con-tastiera .sheet.open{transition:none}`): i 220ms di ease
  servono alla SCIVOLATA d'ingresso, ma il sollevamento passa dalla
  stessa proprietà e `visualViewport` emette un resize a ogni passo
  dell'animazione della tastiera — il foglio finiva a INSEGUIRE un
  bersaglio che si muove, sempre in ritardo e sempre a ri-puntare, ed
  è quello lo «scatto» visto nella PWA. Spegnendola il foglio È dove
  il viewport dice, fotogramma per fotogramma: non si rallenta niente,
  si toglie l'inseguimento. Più `preventScroll` sul fuoco del campo,
  che uno scroll automatico su un foglio fisso è l'altro modo in cui
  nasce uno scatto (la lezione del picker).
  ONESTÀ SULLA VERIFICA, e va tenuta perché riguarda il METODO: in
  headless lo scatto NON si può vedere — misurato, le transizioni non
  avanzano (300px istantanei già a 20ms), quindi lì non si riproduce
  né si esclude. Invece di scommettere su una causa sola si sono
  tolte TUTTE quelle plausibili. Se un giorno ricomparisse, il
  sospetto successivo è la `max-height` che cambia durante
  l'animazione: il foglio è ancorato in basso, quindi accorciandosi
  muove il bordo alto — e si vede solo sul telefono.
  LESSICO (deciso lug 2026): la scheda per gli utenti si chiama
  «Ordini», non piu' «Affari» — in TUTTI i testi (notifiche, UI,
  confirm); gli id interni (go('affari'), #nav-affari, view-affari)
  restano.
  IL NEGOZIO IN FERIE 🌴 (ago 2026): il venditore che parte chiude la
  bottega con la data di rientro. Gli annunci RESTANO in vetrina —
  prezzo in grigio, badge «🌴 In ferie» sulla card, la data nella
  scheda — e non si compra, non si offre, non si riempie il carrello,
  non si punta. Niente sparizioni: è tutta la differenza con la
  rimozione, ed è il motivo per cui non si tocca una riga di `annunci`.
  UNA COLONNA SOLA, `utenti.ferie_fino` (0 = aperto, altrimenti il
  timestamp del rientro), e il GATE È IN LETTURA come per lampo e
  asta: il negozio riapre DA SOLO alla data, senza che nessun orologio
  debba passare a girare un interruttore — se il server resta spento
  una settimana, al riavvio chi doveva riaprire è già aperto, e chi
  compra non aspetta nessun giro. È la scelta che porta via tutto il
  resto del lavoro; un booleano più una data avrebbe voluto un timer e
  due verità da tenere allineate. `scadenze_ferie` è la gemella esatta
  di `scadenze_lampo` e fa PULIZIA, NON è lei a riaprire (più il
  reset del timbro per le ferie successive). Giudice unico e PURO
  `in_ferie(ferie_fino, adesso)`, accanto a `_asta_viva`: prende un
  INT e non una riga, così lo stesso giudice serve la riga `utenti`,
  l'alias `venditore_ferie` della vetrina e la prova in CI; al filo
  esatto il negozio è APERTO, come `_asta_viva`.
  NON SI CHIUDE CON IMPEGNI APERTI, ed è la regola del cantiere:
  `_impegni_aperti` restituisce RIGHE LEGGIBILI e non un booleano —
  il messaggio deve dire COSA manca, e tutte insieme, o il venditore
  le scoprirebbe a una a una riprovando. Le cinque, ognuna con la sua
  via d'uscita: 1) ordini `locked` (merce pagata e mai partita: è il
  caso più grave, i sats di qualcuno aspettano lui); 2) aste vive
  (vincolanti: chi ha versato sta gareggiando); 3) offerte
  `accettata` (una stretta di mano già data, e in ferie il compratore
  non potrebbe pagare); 4) ordini `creato` freschi (<30 min, la
  soglia di `_riservati`: `verifica_pagamento` NON passa dai gate di
  `compra()`, quindi senza questa riga nascerebbe un `locked` proprio
  durante le ferie); 5) lampo in corso (uno sconto pubblico a tempo è
  una promessa in vetrina). Gli ordini GIÀ SPEDITI non trattengono: i
  loro promemoria seguono il corso normale. NESSUN AUTOMATISMO — la
  lampo non si annulla da sola, il venditore ha già il suo bottone.
  IL LEFT JOIN sugli ordini NON è un dettaglio: i SET hanno
  `annuncio_id=0` e con l'INNER sparirebbero in silenzio — un ordine
  pagato che non blocca le ferie è esattamente il buco che la
  funzione esiste per chiudere. È la lezione già pagata due volte
  (`sollecita_incassi`, `sollecita_venditori_fermi`), qui alla terza,
  col titolo sintetizzato da `_titolo_ordine` sulle righe.
  I VARCHI sono dieci, e la guardia sta SEMPRE prima della invoice (un
  rifiuto dopo `crea_invoice_escrow` lascerebbe una fattura orfana):
  `guardia_ferie(con, venditore_id)` in compra, `_compra_set`,
  `preventivo_ordine`, `_preventivo_set`, `fai_offerta`, più le due
  CINTURE dichiarate (`fai_puntata`, `rispondi_offerta`: per
  costruzione non ci si arriva — aste vive e accordi bloccano la
  partenza — ma una guardia che oggi non scatta è quella che regge
  domani se la regola cambia). Prende il `con` del chiamante come
  `_ordini_vivi_annuncio` (in `compra()` una connessione è già aperta
  e il vincolo è «nessun DML prima del ricontrollo»: una LETTURA è
  ammessa) e sulla via del rifiuto lo CHIUDE, come le guardie
  sorelle. 400 e NON 409, deliberatamente: nel progetto il 409 vuol
  dire «rileggi e riprova», e sul ramo set il client al 409 rilegge il
  negozio — qui non c'è niente da rileggere, c'è una data da
  aspettare. Il gemello `guardia_ferie_venditore` ha il messaggio SUO
  (è un'altra persona a leggerlo) e copre `lancia_lampo`, il ramo asta
  di `pubblica()` e `rilancia_asta_deserta`.
  PUBBLICARE un annuncio NORMALE resta lecito — si prepara il negozio
  per il rientro — ma i GANCI RESTANO TRATTENUTI: `_drena_promo` e
  `_drena_match` saltano i venditori in ferie (rileggono dal DB e ora
  portano `ferie_fino` nel giro), perché un post di canale o un
  avviso di ricerca su una cosa che non si compra è una promessa che
  la vetrina non mantiene. IMPERFEZIONE DICHIARATA: al rientro quei
  ganci non partono in differita.
  LE OFFERTE PENDENTI DECADONO (decisione di Andrea) nella stessa
  transazione della chiusura, col 🕊 di garbo che il meccanismo aveva
  già: lasciarle vive sarebbe la trappola «il venditore accetta dalle
  ferie e il compratore non può pagare». Notifiche DOPO il commit,
  `html.escape` sul titolo.
  IL PROMEMORIA del giorno prima (`avvisa_rientro_ferie`, leva
  `FERIE_PREAVVISO_ORE` 24, 0 = muto) è gemello della campagna
  spedizioniere: il TIMBRO `ferie_avvisato` si scrive PRIMA
  dell'invio — un errore di rete può perdere un avviso di cortesia,
  mai raddoppiarlo. Dice che si può prolungare.
  SUPERFICIE: `u.ferie_fino AS venditore_ferie` in `CAMPI_VETRINA` a
  costo ZERO (il JOIN su `u` c'era già), quindi arriva in un colpo
  solo a vetrina, negozio, singolo, miei, ricerca AI e preferiti;
  `ferie_fino` nel profilo di `/api/negozio`; `ferie_leve` in
  `/api/me` (il client non hardcoda mai un tetto, il patto di
  `max_barattolo`). Endpoint `POST /api/me/ferie` col pattern di
  canale-notifiche; `{fino: 0}` è il RIENTRO e non ha NESSUNA guardia
  — riaprire non è mai un problema.
  LEVE: `FERIE_ATTIVE` nasce ACCESA, al contrario di
  IMPORT_NOSTR_APERTO e ASTA_ABILITATA — quelle muovono denaro verso
  l'esterno e vogliono un gesto dal VPS, questa non muove niente,
  spegne soltanto; `FERIE_MAX_GIORNI` 90 (guardrail contro la data
  incollata per sbaglio, non un giudizio su quanto può durare una
  vacanza).
  FRONTEND: giudici `inFerie(l)`/`ferieData(ts)` accanto a
  lampoAttiva/astaViva, `ferie` in `mapListing` (unix come lampoFine e
  astaFine); classe `.card.in-ferie` SENZA outline (lampo e asta sono
  richiami, questo è il contrario di un richiamo) e badge `.card-ferie`
  nella coppia `--off-bg`/`--muted`, che nell'app veste già gli stati
  conclusi — nessun colore nuovo, le ferie non sono un'occasione da
  annunciare. Nella scheda `.detail-price.ferie` + riga `.ferie-riga`
  nella forma di `.asta-riga`, e al posto del recinto escrow la
  trust-note (il ramo esiste già identico per l'asta chiusa); la barra
  d'acquisto non nasce; cassetto «🌴 Negozio in ferie» nel Profilo col
  calco di «📦 Come spedisci», dove il 400 con gli impegni si rende
  DENTRO il cassetto e con `white-space:pre-line` — il server manda una
  voce per riga e senza quello l'elenco collassa in un muro di testo
  (misurato).
  IL GRIGIO DEL CARTELLINO È UN VALORE FISSO (#8A8271) e mai
  `var(--muted)`: `.tag-price` è di carta chiara nei DUE temi e il
  token di notte si schiarirebbe fino a sparire. MISURATO, ed è la
  parte da tenere: sulla carta rende 3,60 — e il prezzo ARANCIO di
  sempre, lì sopra, rende **3,01** (`--sats-deep` è #D97706; qui c'è
  stato scritto 3,59 per mesi, ed era un errore di trascrizione —
  ricontato ago 2026 col cantiere dello stock, che quel grigio se l'è
  preso in prestito). La conclusione non cambia e anzi si rafforza: lo
  stato spento si legge quanto quello acceso — un filo MEGLIO,
  perfino — e a distinguerli è la TINTA e non la luce; un grigio più
  scuro (4,8 e oltre, provati) renderebbe le ferie più leggibili di un
  prezzo vero, il contrario di quel che deve dire. Chi alzerà il
  contrasto del cartellino alzi PRIMA l'arancio.
  Nella scheda invece `var(--muted)` è giusto: lì il prezzo sta sulla
  pagina e l'inchiostro segue la carta. Nessuna delle due nomina
  `.unit`, la regola dichiarata. E dall'ago 2026 quei tre selettori
  sono CONDIVISI con l'esaurito (vedi «lo scaffale vuoto»): stessa
  frase, un posto solo da tarare.
  LA CARD DICE LO STATO, NON LA DATA (decisione di Andrea sui numeri):
  «🌴 In ferie — torna il 17 ago» in una pillola sola fa 117px, ma a
  360px — la larghezza di riferimento del progetto — la card ne
  concede 108 prima del barattolino, che sta a destra e non si stringe
  mai (misurato: sfora di 9px a 360 e di 29 a 320). Due strade provate
  e scartate coi motivi: la pillola su DUE righe (104×35, nessuna
  collisione) copre il 22% del lato della foto ed è il blocco più
  grosso della card proprio per lo stato che deve farsi notare di
  meno; e la data nella riga META, dove su una card con 🚚gratis+🤝
  restano 65px contro i 76 che «torna il 17 ago» chiede — si tronca
  coi puntini proprio sulla data, e CLAUDE.md quella riga la dichiara
  già satura. La data completa vive nella scheda, due volte.
  SU NOSTR NIENTE (decisione di Andrea): NIP-99 non ha uno stato «in
  pausa» e `sold` sarebbe una bugia; ripubblicare ogni annuncio due
  volte per ferie sarebbe una raffica verso i relay per
  un'informazione che lì non cambia nulla — su Nostr non si compra
  dentro Barattolo. Le ferie restano una regola di CASA.
  Offerta lampo ⚡ (lug 2026, modello Vinted «sconto ai follower»):
  sconto PUBBLICO a percentuale, a tempo, sul SOLO articolo —
  spedizione e protezione si sommano sopra, e il listino NON si tocca
  mai (prezzo_sats/prezzo_eur restano pieni, quindi il NIP-99 parla
  il prezzo pieno PER COSTRUZIONE: lo sconto e' un vantaggio di chi
  compra dentro Barattolo; dal lug 2026 vale anche per gli importati —
  lo sconto e' locale, le colonne lampo_* non toccano il listino e
  l'import orario non le riscrive: se il prezzo cambia sui relay la %
  segue il prezzo nuovo, che e' la natura di uno sconto a percentuale).
  Colonne
  `annunci.lampo_percento/lampo_scadenza/lampo_creato` (attiva =
  percento>0 e scadenza futura: OGNI lettura gatea sulla scadenza, la
  scopa `scadenze_lampo` nell'orologio azzera solo i numeri morti,
  senza notifiche) + `lampo_colpo_avvisato` (cooldown dell'avviso) +
  tabella `offerte_lampo` = storico dei lanci per il tetto
  settimanale (le colonne si sovrascrivono, non contano il passato).
  Leve config (try/except): LAMPO_ATTIVE (True), LAMPO_SCONTI
  [10,20,30], LAMPO_MIN/MAX_PERCENTO (5/70), ORE_LAMPO_OPZIONI
  [6,24,48], MAX_LAMPO_SETTIMANA (2), GIORNI_COLPO (7). «Ha fatto
  colpo»: gancio nel ramo INSERT di `toggle_preferito` (DOPO il
  commit, solo annunci attivi, mai i salvataggi propri; l'endpoint e'
  diventato async per il create_task, precedente /api/me) → valvola
  gemella dei promo `accoda_colpo`/`_drena_colpo` (rilettura dal DB:
  spariti/gia' in lampo/in cooldown = muti; cooldown
  timbrato PRIMA delle notifiche; per venditore ≤SOGLIA_AGGREGA
  messaggi singoli con link, oltre UN aggregato) — avviso ANONIMO:
  «qualcuno», mai chi ne' quanti, i preferiti restano privati per
  natura. Lancio: `POST /api/listings/{id}/lampo` (solo il
  proprietario su attivi, percento/ore dalle leve, count-guard senza
  await sul tetto; FRENO: offerta accettata viva = 400, la stretta di
  mano non si cambia in tavola — le pendenti invece NON decadono)
  scrive colonne+storico e avvisa i savers in create_task
  (`_avvisa_savers_lampo`: barrato → scontato, «hai tempo fino
  alle...» di `_quando_scade`, mai i nomi); `/lampo/annulla` = prezzo
  pieno subito ma il lancio resta nello storico (annullare non
  restituisce il gettone: lancia-e-annulla non dev'essere spam
  gratis). `compra()`: lampo viva = articolo al prezzo di
  `_prezzo_lampo` (giudice unico, valuta del listino; EUR converte
  alla invoice come sempre) col MINIMO sull'eventuale accordo
  individuale — chi paga paga sempre il meglio dei due. Superficie:
  lampo_percento/scadenza in CAMPI_VETRINA (search e miei gratis via
  a.*), param `solo_lampo`, ordinamento `lampo` in ORDINAMENTI
  (keyset (lampo_scadenza,id) ASC = chi scade prima in testa, IMPLICA
  il filtro; indice idx_annunci_lampo), leve in /api/me.lampo_leve.
  Frontend: `lampoAttiva`/`conLampo` (vista scontata del listino,
  gemello client di _prezzo_lampo)/`lampoResta`; in CARD il badge
  dice la SOLA percentuale «⚡ −20%», in alto a sinistra sulla foto
  (colori fissi nei due temi, MAI animazioni: patto reduced-motion;
  dal lug 2026 niente countdown lì — allungava il badge e chiedeva
  un aggiornamento al secondo per ogni card disegnata), cartellino
  col listino barrato; il TEMPO che resta vive solo nella scheda,
  sotto il badge e fuori da lui: «rimangono 2h 14m»
  (`.lampo-resta`, colore `--sats-text`, `flex-basis:100%` = SEMPRE
  una riga sua: in euro i tre pezzi ci stavano e in sats no — il
  barrato «180 000 sats» è largo il doppio di «≈ 166 €» — e la riga
  cambiava forma secondo la valuta; meglio una riga in più sempre
  che due rese diverse per la stessa cosa) — la vecchia riga «⚡
  Offerta lampo: ancora…, poi il prezzo torna pieno» è sparita, che
  diceva la stessa cosa due righe sotto. UN solo setInterval per
  tutta l'app aggiorna i `.lampo-count` in-place (ormai uno solo, nel
  dettaglio) e allo zero fa renderGrid + riapertura della scheda in
  sconto — che riconosce dal BARRATO ancora in pagina (`.lampo-was`,
  la sentinella era la riga sparita). La griglia non ha più contatori
  da leggere ma deve comunque tornare a prezzo pieno da sola: ci
  pensa `prossimaLampo`, la prima scadenza fra le card disegnate,
  riscritta in fondo a `renderGrid` — un numero da confrontare invece
  di frugare nel DOM ogni secondo; `artStima` passa da
  conLampo col min sull'accordo (bottoni compra e conto scomposto
  parlano da soli la cifra scontata); foglio `#lampoSheet` del
  proprietario (chip dalle leve, durate a pillole, anteprima
  barrato→scontato con l'ora di fine; nel dettaglio owner «⚡ Lancia
  un'offerta lampo» che con la lampo viva diventa «annullala» con
  confirm); filtro «⚡ Solo in offerta» + voce «⚡ In offerta» in
  Ordina, in DEMO client-side col seme dimostrativo (Cuffie Sony,
  scadenza calcolata al carico).
  L'ASTA 🔨 (ago 2026, «vendita al miglior offerente»): base + durata
  (1/3/7/14/30 giorni, in collaudo anche minuti), chi vuole comprare PUNTA
  versando sats nel deposito di garanzia, per superare chi è in testa
  si versa SOLO LA DIFFERENZA, alla scadenza la puntata più alta
  diventa un ordine normale GIÀ pagato e i perdenti vengono
  rimborsati. Il pregio che ha deciso il cantiere: il vincitore non
  può sparire, ha già pagato. PRINCIPIO ARCHITETTURALE: l'asta
  finisce esattamente dove inizia un ordine — il ciclo di vita degli
  ordini non si tocca; la chiusura invoca `crea_ordine_pagato`, LA
  PRIMITIVA «ordine già pagato» (nasce 'locked', scrive dentro la
  transazione del chiamante) che la futura pagina d'acquisto riuserà.
  SCHEMA: colonne `annunci.asta_base_sats/asta_scadenza/asta_creato/
  asta_avvisata_1h` (patto lampo: gate in LETTURA; `prezzo_sats` È la
  base e non si tocca mai; base>0 e scadenza=0 = DESERTA in mano al
  venditore) + tre tavoli: `puntate` (UNA riga per offerente per
  asta — versato, offerto, `saldo_seq`, etichetta anonima «Offerente
  A,B,C…» per ordine di primo saldo, stati attiva|vincitrice|chiusa,
  UNIQUE(annuncio_id,tg_id)), `rilanci` (una per FATTURA di
  versamento: il client dichiara il TOTALE, il server calcola il
  delta — mai fidarsi di importi dal client; fatture da 10 minuti,
  expiry parametrico su crea_invoice_escrow; stati creato|saldato|
  tardivo), `rimborsi_asta` (il REGISTRO «Da riscuotere» con le
  cinture d'idempotenza a indici parziali; motivi ritiro|perdente|
  tardivo|annullo_admin). INVARIANTI provati in CI: Σ delta saldati =
  versato del vincitore + Σ registro; versato==offerto per ogni
  puntata attiva.
  SALDO_SEQ, la lezione del collaudo: «fa fede l'orario di saldo» a
  risoluzione di secondo NON basta come tie-break (due saldi
  pari-cifra nello stesso secondo sono usciti subito, e vinceva chi
  aveva CREATO la fattura prima). È un progressivo GLOBALE assegnato
  nel blocco senza await della verifica: a parità di cifra comanda
  chi ha saldato prima — per prendere la testa bisogna SUPERARE.
  `_leader_asta` è il giudice UNICO di «chi è in testa» (guardie di
  punta, stato personale, notifiche, pallino, ritiro) e
  `conto_chiusura` è il gemello puro con lo STESSO ordine: sentinelle
  in prove.py, un MAX sulla cifra direbbe il contrario sul pari-cifra
  (successo in /api/me, preso in revisione).
  IL MOTORE: `POST /api/aste/{id}/punta` con la liturgia di compra()
  (guardie → unico await sulla fattura → ricontrollo → zero await al
  commit). Guardie: leva, asta viva (READ GATE: chiusa anche se
  l'orologio non è passato), mai la propria (tg_id E npub condivisa),
  LIGHTNING ADDRESS OBBLIGATORIO alla prima puntata (è il binario del
  rimborso), ritiro definitivo (409), una fattura pendente alla
  volta, minimo = `rilancio_minimo` (+5%, MAI meno di 1 sat: la
  funzione unica di endpoint, foglio e CTA delle notifiche), «sei già
  in testa» (rilanciare su sé stessi costerebbe senza motivo).
  `POST /api/rilanci/{id}/verifica` = poll col CAS: saldo valido =
  versato che si somma + etichetta al primo saldo + PROROGA
  ANTI-CECCHINO nel write path (`nuova_scadenza`: saldo negli ultimi
  ASTA_PROROGA_MINUTI → scadenza = saldo+proroga, NESSUN tetto: l'asta
  finisce con 10 minuti di silenzio) + l'annuncio entra nei preferiti
  da solo; la corsa non si respinge MAI — saldo con testa già più
  alta = puntata valida non in testa, notifica onesta; saldo FUORI
  TEMPO (asta chiusa O puntata ritirata: la fattura pagata nei suoi
  10 minuti ma mai verificata sopravvive alla finestra del ritiro —
  cintura con sentinella in CI) = dritto nel registro, mai versato su
  una puntata fuori gara, mai un ordine.
  IL RITIRO È DEFINITIVO (regola 6 emendata da Andrea): chi non è in
  testa esce quando vuole (CAS + riga registro nella stessa
  transazione, riscossione immediata, FUORI dal gate della leva), ma
  non rientra — mette un tetto per costruzione ai rimborsi (uno a
  offerente) e rende il gesto inequivocabile. Il leader non si ritira
  MAI. Il reaper delle fatture mai saldate (soglia 1200s) libera la
  riga UNIQUE di chi non ha mai pagato: quello non è un ritiro.
  «DA RISCUOTERE» = IL BINARIO DEGLI INCASSI, nessun tubo nuovo:
  `_paga_rimborso` (lock per rimborso, cascata invoice depositata →
  ln_address → fermo, MAI retry), ripiego `POST /api/rimborsi/{id}/
  invoice` a importo esatto, scandaglio di /api/me/ln-address ESTESO
  al registro, `sollecita_rimborsi_puntate` nell'orologio con le
  STESSE leve degli incassi (🧊 admin oltre il tetto, poi silenzio).
  Rimborso INTEGRALE al sat: le fee di routing le paga la
  piattaforma, come ogni uscita.
  LA CHIUSURA: `chiudi_aste` nell'orologio (gira ANCHE a leva spenta:
  i sats non sono ostaggio di ASTA_ABILITATA; il jitter dei 10 min
  ritarda solo l'aggiudicazione, mai un rilancio). Ogni asta è UNA
  transazione col RICONTROLLO DELLA SCADENZA DENTRO (la proroga
  arrivata tra la SELECT e la lavorazione salva l'asta dal giro);
  idempotente: il commit la porta fuori dalla SELECT in un colpo,
  crash dopo il commit = le righe da_riscuotere le recuperano
  solleciti/scandaglio/ripiego. Vincitrice → ordine 'locked'
  (payment_hash dell'ultimo saldo, cambio fotografato, quote 0,
  quantità 1) → annuncio 'venduto'+quantità 0; perdenti → registro +
  riscossione post-commit. IL VINCITORE SCEGLIE LA STRADA DENTRO
  L'ORDINE (`POST /api/orders/{id}/consegna`, dal varco; una strada
  sola = fissata alla nascita): finché `consegna_scelta` è vuota il
  venditore vede «in attesa della scelta» e segna_spedito rifiuta —
  NESSUNA finestra di tutela parte prima della scelta; gli ordini
  STORICI con consegna '' restano il flusso di sempre (la differenza
  la fa l'annuncio all'asta, flag `asta` in /api/orders). Le strade
  dell'asta sono SOLO a costo zero (ritiro, codice online, spedizione
  INCLUSA nel prezzo: il costo è forzato a 0): chi vince non paga mai
  nient'altro. Notifiche: vincitore 🏆, perdenti, venditore, avviso
  «scade tra 1h» ai partecipanti (timbro una tantum; la proroga oltre
  l'ora non lo riarma, dichiarato), polso ordini admin sull'ordine
  nato — nessuna notifica admin nuova oltre al polso.
  DESERTA: scadenza azzerata, base intatta, NON comprabile (compra()
  rifiuta su base>0, anche deserta); il venditore Rilancia
  (`/api/aste/{id}/rilancia`) o Converte a prezzo fisso alla base
  (`/converti` — lecito anche su asta viva SENZA puntate salde: è
  l'annullo del venditore che conserva l'annuncio). CON puntate salde
  l'asta è VINCOLANTE (`_puntate_attive_salde`): niente modifica
  (mai, nemmeno senza puntate: si ritira e si ripubblica), niente
  rimozione, niente riapertura in revisione — solo l'ANNULLO ADMIN
  (`/api/admin/aste/{id}/annulla`: tutte al registro, poi la
  rimozione ordinaria passa). `chiudi-ora` solo in collaudo, dalla
  STESSA chiusura. Un'asta nata in revisione riparte col CRONOMETRO A
  NUOVO alla pubblicazione (decidi_revisione: la coda dei moderatori
  non mangia la durata — regola di prodotto).
  ESCLUSIONI (predicato `_asta`): niente compra diretto, offerte,
  lampo, set (motivoEsclusione), quantità>1 (forzata 1), ricarica;
  solo sats; solo annunci nativi (l'import orario riscrive il
  prezzo); NIENTE NOSTR né promo né match (i loro testi direbbero un
  prezzo a cui non si può comprare — la scoperta è la vetrina col
  filtro «🔨 All'asta», l'ordinamento «chi scade prima» su
  idx_annunci_asta, il badge in card col tempo a grana grossa e il
  countdown vivo solo nel dettaglio, sul battito unico).
  LA LAMPO PARLA ROSSO DAPPERTUTTO (ago 2026, decisione di Andrea):
  prima il rosso era solo il badge ⚡ e la cornice della card era
  arancio ₿ — cioè il colore dei prezzi normali e delle azioni, che
  diceva «offerta» con la voce di «tutto il resto». Tre token, perché
  il rosso vive su tre superfici diverse, ed è la stessa famiglia
  dell'asta: `--lampo` #C0392B FISSO (il badge sulla foto, bianco
  sopra 5,44, e il chip del dettaglio — ciò che sta sulla foto non
  cambia di notte, come share-btn e pallini); `--lampo-tag` #A6301F
  FISSO (il prezzo sul CARTELLINO, che è di carta chiara nei due temi:
  6,48 su #FFF8EA — gemello esatto di `--asta-tag`, per la stessa
  ragione); `--lampo-text` INCHIOSTRO e quindi seguito dal tema
  (#A6301F / #FF8A6B: il numero grande del dettaglio, la riga «Scade
  tra …» e la CORNICE della card — misurati 6,24 su crema, 7,46 su
  bruno; la cornice fa 6,85 sul bianco della card e 6,57 sul bruno).
  ATTENZIONE all'asimmetria con l'asta, che la cornice la fa col suo
  `--asta`: quello è un token che si schiarisce di sera, il rosso
  della lampo no — qui l'inchiostro è la scelta giusta, e il segno
  resta rosso in tutti e due i temi. Si abbassa la luce, non si
  cambia il segno. In card la regola è `.card.in-lampo .tag-price
  .price`, nel dettaglio la classe `.detail-price.lampo` che
  `openDetail` mette accanto ad `.asta` — e nessuna delle due nomina
  `.unit`, vedi la regola qui sotto.
  L'UNITÀ DI MISURA NON SI COLORA MAI (ago 2026, decisione di Andrea,
  e SOSTITUISCE la regola opposta che stava scritta qui per l'asta).
  A prendere il colore del suo stato è il NUMERO; il simbolo € e la
  parola «sats» restano nel colore del testo — in vetrina e nel
  dettaglio, e per TUTTI gli stati: normale, lampo, asta. Prima il €
  era arancio perfino nello stato normale, e la correzione dell'asta
  l'aveva portato sul token INSIEME alla cifra per non avere «mezzo
  numero per famiglia»: l'argomento era vero ma guardava la simmetria
  sbagliata — quella che conta non è fra il numero e la sua unità, è
  fra le unità di tutti gli stati, che ora si somigliano tutte.
  IL CUORE È IL SELETTORE NUDO `.unit{color:var(--muted)}`, e sta lì
  apposta: così vale anche dove l'unità nasce DENTRO un elemento già
  colorato (le cifre in grassetto dei pannelli, delle offerte e della
  conferma NWC, che senza quella riga ereditavano l'arancio — erano il
  residuo che l'audit del punto 4 ha trovato). Unica deroga: il
  cartellino di carta, `.tag-price .price .unit`, col suo grigio fisso
  #8A8271 — la carta non cambia di notte. `.detail-price .unit` e
  `.price .unit` tengono solo la MISURA, non il colore.
  REGOLA PER CHI SCRIVE: chi mette un numero con la sua unità la
  avvolge in uno `<span class="unit">` e non ci pensa più; e nessuna
  regola di stato deve mai nominare `.unit` — se ne aggiungi una,
  falla finire sul solo `.price`. Verificato su 12 combinazioni
  (3 stati × 2 valute × 2 temi) in vetrina e nel dettaglio.
  L'ASTA PARLA PETROLIO (ago 2026, ritocchi di Andrea: prima blu, poi
  verde-blu scuro tenuto sul lato BLU della famiglia — tinta ~195°,
  col verde della protezione a ~151°: si toccano nel punto più
  delicato, il bottone dentro il recinto verde, e la prova del nove
  sugli screenshot ingranditi li distingue al primo sguardo): token
  `--asta` #0F6D8C (di sera si SCHIARISCE a #1D7FA0 — si alza la
  luce, non si cambia il segno; misurati: bianco sopra 5,86/4,57, vs
  crema 5,33, vs bruno 3,77), `--asta-text` #0B5570/#7FC4DC (7,51 su
  crema, 8,88 su bruno, distinto dal ghiaccio della spedizione),
  `--asta-tag` #0B5570 FISSO (vive sul cartellino di carta, che non
  cambia di notte: 7,80) — l'arancio è di Acquista, il rosso della
  lampo, il verde della protezione, il viola di Nostr. Anche il NUMERO
  GRANDE del dettaglio di un'asta parla il token (`.detail-price.asta`)
  — l'identità non si spezza sulla soglia card→dettaglio, l'arancio
  resta dei prezzi veri. Il SIMBOLO DI VALUTA no, e dall'ago 2026 è la
  regola generale: vedi «l'unità di misura non si colora mai», qui
  sopra, che rovescia quel che stava scritto in questo punto. ATTENZIONE
  alla trappola pagata qui: la riga d'asta del dettaglio NON deve
  prendere in prestito classi della lampo (`.lampo-resta` vinceva a
  pari specificità e la tingeva d'arancio). UN token per tutto: bottoni
  (`.btn.asta`, stessa forma dell'orange), chip del foglio, badge e
  cornice in card, riga/countdown del dettaglio, TARGHETTA prezzo in
  card (quel numero è la puntata in corso, non un prezzo). Il RECINTO
  resta VERDE anche sull'asta (il verde è della protezione, non
  dell'acquisto): dentro, il bottone è blu. I bottoni del foglio
  puntata sono rettangolari COME Acquista per selettore condiviso
  (`#detailContent .btn,#puntaSheet .btn` — un solo cuore, mai una
  copia).
  LA RADICE «🔨 ASTE» ESISTE (ago 2026): il martelletto SVG
  monocromatico (mano di tagliaSVG, inchiostro in [2,22], si accende
  in arancio con currentColor come le sorelle) prende lo SLOT VUOTO
  della nav. NON è una seconda vetrina (il patto di Sfoglia):
  `vaiAste` accende ramoVetrina='aste' + filtro + ordinamento «scade
  prima» sulla vetrina UNA; `voceNav` e la entry di navigazione
  conoscono il ramo; `vaiEsplora` uscendo dal ramo spegne ANCHE
  filtro e ordinamento che il tab aveva acceso lui (o Esplora
  mentirebbe). Stato vuoto suo («Nessuna asta in corso», CTA verso
  Vendi).
  IL TASTO C'È SEMPRE, ANCHE A LEVA SPENTA (ago 2026, decisione di
  Andrea): prima compariva solo ad `ASTA_ABILITATA` accesa e lo slot
  restava allo spaziatore. Adesso il martelletto prende quel posto in
  ogni caso e a leva spenta porta al COMING SOON (`view-astepresto`,
  markup fisso e nessun dato utente dentro — mai un esc() da
  ricordare; riusa lo stato vuoto di casa, `.empty` con la mascotte
  che fluttua, quindi zero token nuovi e chiaro/scuro gratis; il testo
  è DUE RIGHE — il primo elencava base, durata e deposito e suonava
  tradotto: qui basta dire che arrivano e qual è il bello, cioè che
  chi vince ha già pagato — e il bottone porta la LENTE della nav, la
  stessa icona di Esplora, che l'emoji 🛍️ cambiava forma da un
  telefono all'altro): le aste
  si annunciano prima di esistere, invece di apparire un giorno dal
  nulla. È una RADICE SORELLA — sta in `RADICI`, si sostituisce come
  le altre e l'indietro passa da Esplora — e `voceNav` la mappa su
  'aste', che la nav deve dire dove sei. Non tocca né filtro né
  ordinamento: non c'è niente da accendere e niente da spegnere
  uscendo. Il TOGGLE del form invece segue la leva sul serio: un'asta
  non si crea finché non è accesa.
  LA LEVA ARRIVA DA DUE FONTI, e questo chiude l'imperfezione
  dichiarata di ieri: `/api/me.asta_leve.abilitata` per chi è dentro,
  e `asta_abilitata` nella busta di PRIMA PAGINA di `/api/listings`
  per gli ANONIMI in vetrina, che /api/me non ce l'hanno. Senza la
  seconda l'anonimo vedrebbe il coming soon anche ad aste ACCESE — e
  sarebbe una bugia, non un'imperfezione. Il giudice unico è
  `asteAccese()`. In DEMO non arriva nessuna delle due e resta il
  coming soon, che lì è la verità (nel seme finto le aste non ci
  sono).
  FUSIONE con la REGOLA DELLA LAPIDE (Andrea, in revisione — il
  travaso cieco era un doppio conteggio): nelle collisioni
  stessa-asta si sommano SOLO le puntate ATTIVE (i sats di una
  ritirata sono GIÀ al registro) e il superstite gareggia con TUTTO
  il versato (offerto = somma: una persona, una cassaforte,
  versato==offerto sempre vero); l'auto-puntata post-fusione va nel
  registro, mai cancellata (ci sono sats dentro).
  LEVE (config, try/except): ASTA_ABILITATA nasce FALSE come
  IMPORT_NOSTR_APERTO (muove denaro in uscita: si accende dal VPS con
  un gesto, guardando il primo giro; spenta blocca creazione e
  puntate NUOVE, mai chiusure/ritiri/riscossioni),
  ASTA_DURATE_GIORNI [1,3,7,14,30] (nel form pillole compatte
  «24h·3g·7g·14g·30g» con 7 PRESELEZIONATO; tutto passa dall'elenco —
  validazione, avviso 1h, proroghe — mai un 3/7 assunto altrove, e la
  guardia fuori-elenco=400 ha la sua prova pura), ASTA_INCREMENTO_PERCENTO 5,
  ASTA_PROROGA_MINUTI 10, ASTA_MAX_ATTIVE_VENDITORE 3. Superficie:
  asta_base/scadenza in CAMPI_VETRINA + top e conteggio da
  arricchisci_righe_vetrina (offerenti MAI nominati), `asta_leve` e
  `aste_da_agire` in /api/me, `GET /api/aste/{id}` (cronologia
  anonima + mia posizione + strade), `GET /api/me/puntate` (sezione
  «🔨 Le tue puntate» + «Da riscuotere» negli Ordini), foglio
  #puntaSheet col conto «versi adesso: la differenza», barra «🔨
  Punta», toggle «Vendi all'asta» in Vendi (visibile solo a leva
  accesa). Lo SLOT VUOTO della nav resta destinato alla futura radice
  «🔨 Aste» (solo frontend su solo_asta+ordina=asta, pattern Sfoglia).
  STRADE SCARTATE, coi perché (non riproporle senza un motivo nuovo):
  rimborso immediato a ogni sorpasso (ucciderebbe il rilancio a
  differenza e moltiplicherebbe le transazioni); rimborso a tempo
  dopo N ore da superato (timer coi casi limite, rischia di
  rimborsare chi stava per rilanciare: il ritiro volontario ottiene
  lo stesso con la scelta in mano all'utente); tetto di 3 rilanci a
  testa (soffoca il rilancio a un tap e abbassa il prezzo finale — il
  freno naturale è il prezzo; leva aggiungibile a posteriori);
  rientro da zero dopo il ritiro (il definitivo mette un tetto per
  costruzione ai rimborsi e rende il gesto inequivocabile); fee di
  prelievo sull'uscita, es. 1% (la cassaforte restituisce sempre
  intero: far pagare l'uscita scoraggia le puntate, il costo vero è
  solo il routing); aste multi-pezzo e Compralo subito (fuori dalla
  v1).
  IL PROXY A BUDGET DEPOSITATO (ago 2026, nato dagli utenti): chi
  punta può depositare il suo MASSIMO e lasciare che il sistema
  rilanci per lui. È la versione SENZA mandati di spesa — la strada
  «proxy via NWC» è stata valutata e scartata: mandato di spesa
  complesso, e un wallet muto a metà gara lascerebbe una puntata
  fantasma — perché il budget è GIÀ nel deposito di garanzia: il
  proxy non versa mai niente, ESPONE il minimo necessario pescando
  dal versato. Nasce la distinzione VERSATO (il budget, SEGRETO) vs
  ESPOSTO (`offerto_sats`, la puntata in gara): invariante nuova
  `versato >= offerto`, uguali quando `puntate.proxy=0` — e per le
  manuali NON cambia niente, che è la prova regina del collaudo (la
  partita tutta-manuale identica a ieri, byte per byte).
  IL MOTORE è `esposizioni_proxy` (pura accanto a conto_chiusura):
  la CAPACITÀ che gareggia è il versato, ranking (versato, saldo_seq,
  id) — lo stesso tie-break di _leader_asta, e la coerenza dei due
  giudici sul campo post-motore è provata in CI; manuale: esposto =
  versato; proxy non in testa: esposto = versato (ha provato e perso:
  «budget esaurito», da lì è indistinguibile da una manuale); proxy
  in testa: min(versato, max(base, rilancio_minimo(versato del
  secondo))), senza un secondo la base. NESSUN esposto scende MAI
  (monotone: il ritiro di un rivale non richiede ricalcoli, il motore
  è già un punto fisso) ed è IDEMPOTENTE: due proxy convergono in UNA
  passata contabile dentro il saldo che l'ha scatenata — niente
  rincorsa di pagamenti, niente proroga eterna. Gira nel blocco senza
  await di verifica_rilancio (PRIMA di testa_dopo: proroga, notifiche
  e payload dicono la verità post-convergenza) e in coda al ramo
  puntate di esegui_fusione, DOPO la chiusura delle auto-puntate.
  TRE FUGHE DEL MASSIMO chiuse prima di nascere, ed è la parte da
  ricordare quando si tocca qualcosa: 1) la CRONOLOGIA leggeva
  `rilanci.offerto_sats` = il totale dichiarato, che per una fattura
  proxy È il budget — ora legge `rilanci.esposto_sats`, scritto al
  saldo post-motore (backfill = offerto per le righe di ieri, tutte
  manuali); 2) la notifica «Nuova puntata» al venditore diceva
  `ril['offerto_sats']` — ora dice l'esposto di testa_dopo, ed è MUTA
  sul top-up del leader (per lui non è successo niente); 3) il
  racconto di chiusura diceva il versato in quattro punti — ora dice
  l'esposto, che è il prezzo dell'ordine. Il flag proxy e il versato
  escono dal server SOLO in `mia` (stato_asta) e nelle righe di
  mie_puntate: pubblico e venditore NON distinguono mai una puntata
  proxy da una manuale.
  LA PROROGA HA UNA GUARDIA NUOVA: proroga solo se il saldante non
  era già leader o se (id, esposto) della testa è cambiato. Senza, il
  TOP-UP del leader (lecito: proxy=1 e totale>versato, il minimo non
  si applica — sale il massimo segreto, l'esposto no) comprerebbe
  proroghe a costo ZERO, perché la sua fattura è rimborsabile per
  costruzione (eccedenza). I rialzi automatici non prorogano mai e
  sono SILENZIOSI: il proxy esiste per non guardare l'asta, squilla
  solo il «budget esaurito» (la notifica «superato» arricchita) — il
  patto dei solleciti.
  L'ECCEDENZA: alla chiusura il vincitore paga l'ESPOSTO
  (crea_ordine_pagato riceve offerto_sats) e `conto_chiusura` mette
  la differenza nel registro con motivo 'eccedenza' — INVARIANTE
  aggiornata: Σ delta saldati = esposto della vincitrice + Σ registro.
  A gara viva il leader proxy può RITIRARLA (`POST /api/aste/{id}/
  ritira-eccedenza`, fuori dai gate delle leve come il ritiro): UNA
  volta per asta, la puntata torna SECCA (proxy=0, versato=offerto)
  e su quell'asta il proxy non si riaccende — «scesa l'eccedenza non
  risale», e la fusione lo rispetta (un'eccedenza ritirata su una
  metà forza proxy=0 sul superstite). I motivi sono DUE APPOSTA
  ('eccedenza_ritiro' e 'eccedenza'), ognuno col suo indice parziale
  UNIQUE: un motivo solo, con la fusione che riaccende il proxy,
  farebbe IGNORARE la riga di chiusura dall'indice = sats mai
  rimborsati in silenzio. La fusione inoltre non scrive più
  `offerto=somma` (sarebbe la fuga del massimo): versato = somma
  delle attive, esposto = MAX degli esposti attivi, proxy = OR, e il
  motore rimette in riga.
  LEVA `ASTA_PROXY_ATTIVO`, FALSE nel codice e in config_esempio:
  gatea le sole puntate proxy NUOVE (il motore continua per i proxy
  vivi — i sats non sono mai ostaggio di una leva). STRATEGIA
  D'ACCENSIONE (decisione di Andrea): resta spenta ANCHE quando
  ASTA_ABILITATA si accenderà — il proxy parte solo a gara manuale
  rodata. Frontend: pillole «Puntata secca» / «🤖 Rilancia per me
  fino a…» nel foglio puntata (solo a leva accesa, via
  asta_leve.proxy_attivo), stato personale con esposto + budget
  residuo «(lo vedi solo tu)», «➕ Aggiungi budget» e «🕊 Ritira
  l'eccedenza» per il leader proxy, righe di «Le tue puntate» col
  residuo. In DEMO niente leva = niente pillole, coerente.
  Quantità in stock (lug 2026, il mattone del futuro «set»): colonne
  `annunci.quantita` (pezzi disponibili ADESSO, default 1: gli storici
  restano un pezzo solo) e `ordini.quantita`. INVARIANTE: venduto <=>
  quantita=0 — l'esaurito RIUSA lo stato 'venduto', zero stati nuovi
  (filtri vetrina, decadenza offerte, anti-resurrezione dell'import e
  preferiti «non più disponibile» valgono gratis); riallineamento
  idempotente a ogni avvio in init_db. PRENOTAZIONE derivata, niente
  contatore: riservati = SUM(quantita) degli ordini 'creato' freschi
  (<30 min, la soglia del reaper, che copre la vita della invoice: 15)
  via `_riservati` + `idx_ordini_annuncio` (il primo indice su ordini);
  compra() fa il fail-fast di cortesia prima delle await e il
  ricontrollo COMPLETO (stato+quantita+SUM) DOPO crea_invoice_escrow
  senza await fino all'INSERT — chiude il buco storico del doppio
  acquisto (prima N invoice vive sullo stesso annuncio si potevano
  pagare TUTTE); VINCOLO: in compra() niente DML prima del ricontrollo
  (una transazione aperta congelerebbe la lettura). Il conto lavora
  sull'UNITARIO (offerte e lampo parlano il prezzo del singolo pezzo;
  per l'EUR si arrotonda l'unitario PRIMA di moltiplicare, così la
  divisione a ritroso di chi legge l'ordine è esatta) e moltiplica
  alla fine: spedizione UNA volta sola, protezione e
  TETTO_DIGITALE_NUOVI sull'articolo TOTALE, drift TETTO_SATS_ANNUNCIO
  sull'unitario (tre pezzi regolari non devono dare 409).
  `ordini.prezzo_sats` resta il TOTALE in cassaforte; l'unitario si
  deriva: (prezzo_sats − spedizione_sats − protezione_sats)/quantita.
  verifica_pagamento scala con MAX(quantita-?,0) nel ramo vincente del
  CAS; SOLO all'esaurimento partono stato venduto, nostr sold, ✅ sul
  canale e la decadenza delle ALTRE offerte — ATTENZIONE: quel blocco
  vive DENTRO il ramo esaurito, la vendita parziale lascia le
  trattative altrui VIVE e la notifica dice i pezzi rimasti. Il
  rimborso somma i pezzi dell'ordine (incremento RELATIVO) e riattiva
  come sempre. RICARICA: `POST /api/listings/{id}/quantita`
  (scrittura ASSOLUTA: quanti pezzi ho ORA; solo proprietario, stato
  attivo/venduto, mai importati né revisione, mai sotto i riservati) —
  NON aspetta gli affari in corso, a differenza della modifica: tocca
  solo il numero, e il negozio col miele sempre in spedizione deve
  poter ricaricare; l'esaurito riattivato rifà nostr active e toglie
  la spunta dal canale, niente promo/match (ricaricare non è
  pubblicare). `/api/listings/miei` porta anche i venduti: riga spenta
  «Venduto» + «↻ Rimetti in vendita» (`ricaricaAnnuncio`, prompt), il
  relist onesto anche per chi vendeva un pezzo solo. Giudici:
  `quantita_da_payload` (assente = default/conserva lo stock in
  modifica; oltre `MAX_QUANTITA_ANNUNCIO` — leva config, **999999**
  dal lug 2026: quanti pezzi ha in magazzino lo sa il venditore, non
  noi, e cento diceva «non ti credo» a chi ne ha davvero tanti. Quel
  che resta è un guardrail contro il numero incollato per sbaglio,
  non un giudizio sul negozio — e vale anche su ciò che arriva dai
  relay. ATTENZIONE: una riga esplicita nel config del VPS vince sul
  default. Coi numeri grandi non si rompe nulla — colonna INTEGER,
  conti interi Python — ma ogni posto che mostra una quantità passa da
  `fmt()`, o «999999 disponibili» diventa un muro di cifre) = 400
  e `quantita_tollerante` per il CSV (vuota o storta = 1, oltre il
  tetto si lima, mai uno scarto); colonna facoltativa `quantita` nel
  modello CSV con la riga del miele. Superficie: `a.quantita` in
  CAMPI_VETRINA (pubblica per natura), riga «— disponibili: N» nel
  content NIP-99 solo se N>1 (verificato: la spec non ha un tag stock;
  `evento_annuncio_importato` resta pulito e gli importati restano
  quantita=1 per sempre), «ne restano N» nel catalogo della ricerca
  AI. OFFERTE = prezzo UNITARIO (deciso da Andrea): minimo 50% e
  contro invariati sul listino unitario, al pagamento pattuito ×
  quantità scelta, e il confirm di accettazione del venditore lo
  dichiara («la cifra vale AL PEZZO»); con la lampo vince il minimo
  sull'unitario come sempre. Frontend: campo «Quantità disponibile»
  sempre visibile in Vendi (vuoto = 1, `qtaForm`; nascosto nella
  modifica firmata), pillola «N disponibili» + stepper `.qta-riga`
  nell'escrow-zone — la scelta sta PRIMA di startBuy, il patto del
  varco: la invoice nasce lì — con `qtaScelta` azzerata a 1 in
  openDetail; totaleStima/cifraVia × pezzi, cifre riscritte in-place
  da `aggiornaCifreCompra` (estratta da setConsegnaScelta), barra con
  «× N», conto scomposto «Articolo × N» (compare anche senza
  spedizione/protezione quando i pezzi sono >1), ordini con «N pezzi ×
  unitario», demo col Bitcoin Standard in 3 copie. Corner dichiarato:
  un ordine pagato ma verificato oltre i 30 minuti può superare lo
  stock (il MAX para il negativo, il doppio-escrow resta caso da
  moderatore — com'era il doppio acquisto di ieri, ma molto più raro).
  LO SCAFFALE VUOTO (ago 2026, «lo stock raccontato bene»): chi vende
  prodotti propri — il riso, lo shoyu, il miele — non vende pezzi
  unici, e l'annuncio esaurito non si butta. LA DIAGNOSI HA RIDOTTO IL
  CANTIERE, ed è la parte da leggere per prima: il riassortimento
  ESISTEVA GIÀ (`ricarica_quantita` accetta lo stato 'venduto', rimette
  'attivo', rifà l'evento Nostr `active` e toglie la ✅ dal canale) —
  non c'era da costruirlo, c'era da renderlo raggiungibile. NIENTE
  stato nuovo: l'esaurito resta 'venduto' e l'invariante venduto ⟺
  quantita=0 non si tocca, quindi filtri, offerte e import valgono
  gratis come sempre.
  IL GUASTO VERO era che `GET /api/listings/{id}` rispondeva **404**:
  un link mandato a un amico e un annuncio nel barattolo morivano
  insieme alle scorte. Ora serve `('attivo','venduto')` con `a.stato`
  nella SELECT (come già faceva il solo ramo preferiti), che è ciò che
  permette al client di disegnarlo spento — la barra d'acquisto non
  nasceva già oggi su uno stato diverso da 'attivo'. Il 'rimosso' e il
  'revisione' restano 404, e la ragione è che NON sono scaffali vuoti:
  il primo il venditore l'ha tolto apposta e un link pubblico non deve
  rovesciare la sua decisione, il secondo non è mai stato pubblico e
  servirlo aprirebbe a chiunque abbia un id una finestra sulla coda di
  moderazione.
  DOVE SI VEDE (decisione di Andrea): SOLO nella pagina del negozio,
  in fondo, sezione «Esauriti di recente» — chiave `esauriti` nel dict
  di `/api/negozio` (tetto `TETTO_ESAURITI` 12, `creato DESC`, una
  query a parte che NON tocca `totale` né il cursore: il numero della
  bottega continua a dire quanto si può comprare). Un negozio è una
  bottega e uno scaffale temporaneamente vuoto dice qualcosa della
  bottega; in vetrina, ricerca, filtri e conteggi resta FUORI — chi
  sfoglia non deve trovare cose che non può comprare. Niente COUNT
  degli esauriti: `vendite_ok` lo dice già nel profilo, e due numeri
  sulla stessa cosa da tabelle diverse divergono al primo caso storto.
  LA MEMORIA DEI PEZZI, `annunci.quantita_max`: il MASSIMO mai
  dichiarato, non «l'iniziale» — coi rifornimenti l'iniziale mentirebbe
  al secondo giro. Serve a UNA domanda sola, «la scarsità è una
  notizia?», e da lì nasce il badge. `riallinea_quantita_max(con)` è
  una riga (`UPDATE … SET quantita_max=quantita WHERE
  quantita>quantita_max`) ed è ANCHE IL BACKFILL ONESTO: «ne ha almeno
  tanti quanti ne ha adesso» è un limite INFERIORE vero, non un passato
  fabbricato. Gira in due posti — all'avvio accanto alla riparazione
  gemella dell'invariante, e nel DOPO-IMPORT Nostr, perché
  `importa_nostr.py` riscrive `quantita` dal tag `stock` scrivendo
  dritto nel database e deve restare CIECO alla colonna (dev'essere
  lanciabile anche su un Barattolo più vecchio: c'è la sentinella).
  IL MASSIMO NON SI ASSEGNA MAI SECCO: `quantita_max=MAX(quantita_max,?)`
  in `ricarica_quantita`, in `modifica_annuncio` e — questa è la falla
  che sembrava impossibile — nel RIMBORSO: 3 pezzi, venduti tutti,
  ricarica a 1, e una disputa ne rimborsa 3 = 4, sopra il massimo di
  ieri. I due INSERT sono DUE (pubblica e l'import CSV, che ha una vita
  sua ed è il punto che si dimentica); `_incassa_ordine` non lo tocca
  mai, perché lì la quantità SCENDE.
  IL NUMERO GREZZO NON ESCE: `arricchisci_righe_vetrina` lo legge,
  decide il flag `ultimo` col giudice puro `ultimo_pezzo(quantita,
  quantita_max)` e lo POPPA — grezzo racconterebbe «ne ha venduti N»,
  un dato nuovo che nessuno ha chiesto, e il pop copre anche le rotte
  che servono l'annuncio intero con `a.*` (ricerca AI, i tuoi annunci).
  È il pattern di `zona_comune`: un campo derivato che porta già dentro
  la risposta alla domanda.
  IL BADGE «ULTIMO» esiste solo dove la scarsità è una NOTIZIA — ne ha
  avuti più d'uno ed è sceso a uno. Su un mercatino dell'usato quasi
  tutto è unico, quindi un badge su `quantita == 1` sarebbe vero e
  insignificante, e smetterebbe di essere letto dopo il terzo. Dove il
  dato non c'è (storici mai ricaricati, importati appena nati) esce 0:
  nel dubbio si tace, mai un'urgenza inventata.
  NON PRENDE UN COLORE, e le tre strade scartate valgono più della
  scelta: il GRIGIO spento è la lingua delle cose FINITE (chi l'ha
  imparato così leggerebbe l'ultimo pezzo come già venduto, cioè il
  contrario); un colore NUOVO sarebbe il quarto segno colorato in card
  e il più FREQUENTE dei quattro — l'errore già pagato col chip
  «Spedizione disponibile», dove quello che diceva meno compariva di
  più; il rosso della lampo significa «sconto a tempo» e i due possono
  convivere. Quindi una SUPERFICIE già di casa, la CARTA del cartellino
  e dei cerchietti sulla foto, fissa nei due temi: misurato, 11,77
  sopra una foto nera e 14,18 sopra una bianca — il badge più leggibile
  dei cinque, ed è giusto, è l'unico che chiede di essere letto ADESSO.
  Quieto nel colore, forte nella luce: il rovescio esatto del
  cartellino in ferie. L'ombra c'è, come lampo e asta: deve staccare.
  IL TESTO È «Ne resta 1» E NON «Ultimo pezzo», e la ragione è
  MISURATA: a 320px quello fa 89px e tocca il barattolino (−1px
  d'aria), «Ultimo rimasto» lo scavalca di 12; questo ne fa 74 e ne
  lascia 14. «Ultimo» secco ci starebbe largo ma da solo, sopra un
  prezzo, si legge «ultimo A QUESTO PREZZO» — dice un'altra cosa. Nella
  SCHEDA invece la pillola dice «**Ultimo** disponibile», che lì è il
  singolare di «N disponibili» nella stessa fila, e parla col GRASSETTO
  e non col colore (la regola dello sfollamento, quella di «spedizione
  gratuita»): a cedere è il luogo, mai il significato.
  PRECEDENZA IN CARD: esaurito > ferie > asta > lampo > ultimo.
  L'esaurito vince ed è l'unica precedenza che non è una cintura ma una
  regola — le colonne `lampo_*` restano vive anche a scorte finite, e
  un «⚡ −30%» su una cosa che non si compra è una promessa che non si
  può mantenere (per la stessa ragione il countdown della lampo tace
  nella scheda di un esaurito). L'«ultimo» sta in coda: uno stato che
  dice «sbrigati» non deve mai coprirne uno che dice «non si può
  comprare».
  L'ASTA NON È MAI ESAURITA (`esaurito(l)` esclude `astaE(l)`): non ha
  stock, ha un aggiudicatario, e «🔨 conclusa» dice già tutto quel che
  direbbe «Esaurito» e in più dice di che cosa si tratta. Non è
  un'eccezione di comodo: è la STESSA riga che `ricarica_quantita` ha
  sempre avuto, dove l'asta è l'unico caso rifiutato per NATURA e non
  per stato. Chi toglie quel `&& !astaE(l)` deve togliere anche quel
  400, o «Rifornisci» comparirebbe dove non può funzionare.
  LA RESA parla la lingua delle FERIE, e per questo si AGGIUNGE ai loro
  selettori invece di ricopiarne i valori misurati (`.card-ferie,
  .card-esaurito`, `.tag-price.ferie .price, .tag-price.esaurito
  .price`, e le due sorelle): «è qui, non si compra» è una cosa sola
  detta per due ragioni. L'UNICA differenza è che la FOTO si spegne
  (`.card.esaurito .ph{filter:grayscale(1);opacity:.62}`) — le ferie
  sono una porta chiusa a ora nota e la merce resta bella da guardare,
  qui la merce non c'è; è lo stesso gesto delle righe «non più
  disponibile» del Profilo e del barattolo. VA SUL WRAPPER `.ph` e non
  sull'`img`: `html[data-tema="scuro"] .card .ph img{filter:
  brightness(.92)}` ha specificità più alta e di notte si mangerebbe il
  grigio — sul genitore i due filtri si compongono invece di litigare,
  e l'emoji-segnaposto si spegne con la foto.
  IL RIFORNIMENTO È UN GESTO, NON UNA RIPUBBLICAZIONE: foglio
  `#rifornisciSheet` (stepper `stepperMini`, campo numerico, scrittura
  ASSOLUTA come l'endpoint) al posto del `prompt()` — l'ultimo dialogo
  del sistema operativo rimasto su una strada battuta, in un'app che ha
  sostituito ogni tendina nativa. IL GUADAGNO NON È IL VESTITO: sul 400
  il foglio RESTA APERTO col numero ancora dentro da correggere («N
  pezzi sono in pagamento proprio ora: scegli un numero più alto»), che
  col prompt si perdeva tutto. Tre porte, un gesto solo: il badge «🔄
  Rifornisci» nel Profilo, il bottone ARANCIO nella scheda del proprio
  esaurito (dove il posto della CTA è vuoto: niente recinto, niente
  Acquista) e la pastiglia sulla card del proprio negozio — NELLO SLOT
  DEL BARATTOLINO, che sui propri annunci è libero per costruzione,
  così la card non guadagna un terzo bersaglio. Le sue guardie sono le
  righe del server (mai un'asta, mai un importato): un bottone che
  porta a un 400 è peggio di un bottone che non c'è. Dopo,
  `dopoRifornimento` ricarica i cataloghi PRIMA delle viste e riapre la
  scheda, che il ramo esaurito è cotto dentro l'HTML.
  SPENTO NON VUOL DIRE CHIUSO: in `rigaMioAnnuncio` l'esaurito ora si
  APRE (la foto resta grigia), perché il dettaglio è dove vive
  «Rifornisci»; il ramo revisione resta parola per parola quello di
  ieri — lì non c'è niente da vedere e niente da fare finché un
  moderatore non decide.
  LIBRO MASTRO: NESSUN controllo nuovo, e il perché è la domanda che
  decide — «esiste uno stato TRANSITORIO LEGITTIMO in cui è falsa?».
  Per `quantita > quantita_max` sì: l'import scrive `quantita` dritto
  nel database e aspetta la scopa. Un allarme su un caso normale è
  peggio di nessun allarme, ed è per giunta una condizione che una
  scopa programmata ripara per mestiere — misurerebbe il ritardo della
  scopa, non un guasto.
  CONSEGUENZA DA SAPERE AL DEPLOY: il badge è spento OVUNQUE il primo
  giorno — chi aveva 10 pezzi e oggi ne ha 1 viene riallineato a 1, e
  niente si accende finché non rifornisce. Non è un guasto: è il prezzo
  di non inventare un passato.
  Il SET «Riempi il barattolo» (lug 2026): più annunci DIVERSI dello
  stesso venditore in UN ordine solo — una invoice escrow, UNA
  spedizione, un tracking, una conferma. Modello «testata + righe»,
  MAI padre+figli (gonfierebbe distintivi e rischierebbe doppi
  sblocchi sullo stesso escrow): la testata resta in `ordini`
  (`annuncio_id=0` e `quantita` = somma dei pezzi), la merce vive in
  `ordine_righe(ordine_id, annuncio_id, quantita, unitario_sats,
  titolo)` — unitario GIÀ scontato (lampo/accordo, invariante:
  articolo = Σ unitario×qta, il futuro sconto-set sarà una voce di
  TESTATA sottratta dal totale, deciso e preparato), titolo
  FOTOGRAFATO all'acquisto (i tre JOIN caldi — /api/orders, CSV,
  sollecita_incassi — sono diventati LEFT: con l'INNER un set
  sparirebbe dalla lista, pagato e invisibile). I MONO non hanno
  righe MAI: le sintetizza `_righe_ordine` dalla testata, e ogni
  punto che cicla sugli oggetti dell'ordine passa da lì
  (`_titolo_ordine` = «primo pezzo + N altri»). Guardie:
  `_ordini_vivi_annuncio` è il giudice unico delle 5 guardie «affare
  in corso» (testata O riga), `_riservati` somma due query (la
  seconda sulle righe via idx_righe_annuncio: l'indice caldo non si
  tocca), rimozione/spegni_annuncio annullano anche i set 'creato'
  col pezzo dentro, reaper e annulla_ordine cancellano le righe
  (niente FK cascade: PRAGMA foreign_keys mai acceso).
  compra() col body `{righe:[{annuncio_id, quantita, offerta_id}]}`
  passa da `_compra_set` (2..MAX_RIGHE_SET, leva config, 8): stesso
  venditore E stessa ORIGINE (lug 2026, dopo l'anello: `venditore_id`
  dice a chi vanno i sats ma non da dove arriva la merce, e un account
  che raccogliesse roba di più persone passerebbe con un id solo —
  l'origine è `contatto_nostr`, '' = nato qui, altrimenti la chiave
  che l'ha firmato. ONESTÀ: NON avrebbe fermato il fantasma, che aveva
  una chiave sola per tutte le copie; a quello risponde il tappo, e
  questa è la cintura se un giorno il tappo salta),
  strade = INTERSEZIONE delle FISICHE (spedizione/ritiro;
  il digitale ha la colonna unica del contenuto e le finestre corte,
  gli annunci con consegna '' non dichiarano un costo: entrambi «si
  comprano da soli», 400 col nome del pezzo), lampo e offerte
  accettate PER RIGA sull'unitario, cambio UNO prima della invoice,
  SPEDIZIONE = MAX dei costi dichiarati (il pacco è uno; compromesso
  dichiarato del v1: 3 «medi» possono fare un «grande» e il
  venditore rimette la differenza — mitigato dalla stima mostrata
  prima di spedire; il tariffario per-taglia è la leva futura),
  protezione sull'articolo totale, ricontrollo post-invoice su OGNI
  riga nel blocco senza await e 409 che NOMINA il pezzo soffiato.
  verifica_pagamento scala/esaurisce/decade RIGA per riga (la
  vendita di un pezzo non spegne le trattative sugli altri; nostr
  sold e ✅ canale per annuncio esaurito); il rimborso resta
  INTEGRALE e riattiva TUTTI gli annunci del set. PER TESTATA (tutto
  o niente, dichiarato): disputa/reso, feedback (uno per parte),
  tracking, distintivi e contatori (1 set = 1 vendita/1 acquisto),
  una riga di CSV. STIMA TAGLIA: `PUNTI_TAGLIA` (busta 1, piccolo 3,
  medio 8, grande 18) + `stima_taglia_set` — somma×qta a soglie
  tarate perché un pezzo solo ricada nella SUA taglia, ingombrante =
  sempre ingombrante, taglia mancante = stima '' (mai una bugia);
  SOLO informativa (risposta di compra, /api/orders — letta fresca
  dagli annunci —, messaggio al venditore «verifica tu prima di
  spedire»), non prezza nulla. /api/orders: i set escono con
  `righe`, `taglia_stimata` e titolo sintetizzato; i mono non
  portano la chiave (client vecchio in cache: titolo e totali di
  sempre, il suo «N pezzi × unitario» mostrerebbe una media — per
  questo il client nuovo lo spegne sui set e mostra l'ELENCO).
  Frontend: `sezioneAltriOggetti` in coda a openDetail (card dal
  negozio limit 7, inCatalogo obbligatorio, guard anti-race,
  fail-open) + bottone «🛒 Aggiungi al carrello» — MAI il 🫙
  nell'etichetta: il barattolo è dei preferiti (il foglio `#setSheet`
  che ne portava il nome non esiste più dall'ago 2026, vedi «LA
  PAGINA CONTROLLA IL PACCO» più sotto).
  LO SCONTO CARRELLO 🎁 (ago 2026): il venditore premia chi compra più
  cose in un ordine solo — UNA regola per tutto il negozio, «da N
  articoli −X%», senza scaglioni: uno sconto che si spiega in mezza
  riga è uno sconto che si usa. Vale SOLO sul prezzo degli articoli,
  MAI sulla spedizione (il pacco costa quello che costa), e il conto è
  del SERVER: l'escrow nasce già scontata.
  LE QUATTRO DECISIONI DI ANDREA, che governano tutto il resto.
  1) [ROVESCIATA il 12 ago 2026 — vedi «IL MONO SCONTA, PUNTO», più
  sotto; il perché di ALLORA resta qui perché era vero e ha deciso la
  forma della cura.] IL MONO NON SCONTA MAI: tre copie dello stesso
  annuncio comprate dalla scheda non sono un carrello. Non era solo
  prodotto — era anche strutturale: `_righe_ordine` sintetizza
  l'unitario del mono per DIVISIONE A RITROSO
  (`(prezzo − spedizione − protezione) // qta`, «esatta per
  costruzione»), e uno sconto di testata l'avrebbe rotta in silenzio,
  sbagliando l'unitario nell'ordine, nelle notifiche e nel CSV. La
  garanzia era che `_sconto_pacco` la chiamassero SOLO i due rami set,
  e la ricetta per il giorno del rovesciamento stava già nel commento
  dentro `_righe_ordine` — ed è esattamente quella applicata.
  2) SI CUMULA con lampo e accordo accettato: è una promessa di
  NEGOZIO scritta in vetrina, e un pezzo che non la mantenesse non
  avrebbe un posto onesto dove dirlo — servirebbe una riga «questo no»
  per riga, e la soglia diventerebbe ambigua (quei pezzi contano?). Le
  vie d'uscita sono asimmetriche: il venditore ha due bottoni (non
  accetta l'offerta, o spegne lo sconto), il compratore che lo scopre
  alla cassa non ha niente. Non scappa di mano perché non è additivo —
  `_unitario_effettivo` fa già il MIN, e il carrello è UNA
  moltiplicazione sul totale che ne esce; il guardrail è il tetto
  della leva, e una prova dice ad alta voce il FONDO (lampo 70% +
  carrello 30% = il 21% del listino): chi alza il tetto la trova rossa.
  3) SI DICE IN PUBBLICO in due posti soli — testata della pagina
  negozio e sezione «Altri oggetti di questo venditore», che è il
  momento in cui uno sta per comporre. MAI nelle card (riga meta
  dichiarata satura, e la regola è del negozio: su otto card sarebbe
  la stessa frase otto volte) e MAI nelle pillole del dettaglio, che
  parlano di QUELL'oggetto — una percentuale lì si legge come sconto
  su QUEL prezzo, la confusione per cui il costo di spedizione è stato
  tolto da quella fila.
  4) LA SOGLIA CONTA I PEZZI (Σ quantità), non gli oggetti diversi:
  tre cose nella scatola sono tre cose, ed è già il significato di
  `ordini.quantita`. (Dal 12 ago 2026 vale fino in fondo: anche il
  mono conta i suoi — vedi «IL MONO SCONTA, PUNTO».)
  IL CRITERIO LO SCEGLIE IL VENDITORE, LA SOGLIA RESTA UNA (ago 2026,
  e questa voce EMENDA la 4: i pezzi restano il criterio di serie, non
  sono più l'unico). Nasce da un venditore vero: «se vendo un computer
  lo sconto lo do già da 2 pezzi, se vendo cianfrusaglie ne servono
  tante». Lui chiedeva una soglia per PRODOTTO, ed è stata SCARTATA —
  lo sconto è del carrello e vale sul totale, quindi con un computer
  (soglia 2) e cinque cianfrusaglie (soglia 10) nello stesso carrello
  nessuna regola sarebbe spiegabile a chi paga; e una soglia per riga
  romperebbe la divisione a ritroso dell'unitario di `_righe_ordine`
  (la stessa ragione che allora teneva fuori il mono — la soglia per
  PRODOTTO resta scartata anche dopo il rovesciamento: è la soglia
  UNICA, non il perimetro, a renderla insostenibile).
  Col CRITERIO l'asimmetria si ottiene lo stesso, con UNA regola sola:
  a PEZZI come sempre, o a VALORE degli articoli («da 100.000 sats nel
  carrello») — un computer ci arriva da solo, di cianfrusaglie ne
  servono venti.
  LA VALUTA DELLA SOGLIA A VALORE LA SCEGLIE IL VENDITORE (ago 2026,
  decisione di Andrea chiesta dalla comunità, che SUPERA quella di due
  giorni prima — «la soglia a valore è in euro» — la quale a sua volta
  aveva rovesciato il «sempre in sats» della nascita. Vanno tenuti tutti
  e due i perché, perché sono tutti e due veri e nessuno dei due è stato
  smentito). Vale per TUTTE E DUE le promesse, e ognuna ha la SUA: sono
  indipendenti, quindi un venditore può dichiarare lo sconto in euro e
  la spedizione gratis in sats.
  IL PERCHÉ DELL'EURO, CHE RESTA VERO: una soglia in sats DERIVA COL
  CAMBIO — chi scrive 100.000 pensando «una cinquantina di euro» si
  ritrova, sei mesi dopo, una promessa del doppio senza aver toccato
  niente. Le spedizioni nel mondo vero si pagano in euro, e la tariffa
  di un annuncio può già essere ancorata all'euro (`spedizione_eur`).
  IL PERCHÉ CHE LO SUPERA: quel difetto ce l'ha GIÀ il PREZZO di ogni
  annuncio in sats, e nessuno se ne lamenta; e la valuta in cui uno
  ragiona è una scelta sua, non nostra. Da qui la forma del cantiere:
  NON si torna ai sats — si AGGIUNGE la scelta, e accanto al toggle si
  dice cosa comporta in tutte e due le direzioni (`notaSoglia`) invece
  di deciderlo al posto suo.
  IL GUADAGNO CHE L'EURO NON POTEVA DARE, ed è ciò che rende la scelta
  più di un gusto: con la soglia in SATS la promessa NON HA BISOGNO DEL
  CAMBIO. Scatta anche a CoinGecko muto, l'invito del carrello smette di
  convertire (era l'unico posto dell'app dove il client converte una
  promessa, con la sua imperfezione dichiarata), e un negozio
  tutto-sats non paga più un giro di rete che non gli serve. È la stessa
  famiglia del criterio a PEZZI, che il cambio non l'ha mai guardato.
  L'ARGOMENTO PERDENTE DI VENERDÌ va tenuto perché era buono, e adesso è
  il MEZZO argomento che resta: a cambio muto una promessa in EURO non
  si sa valutare e non scatta. Resta vero, ma «muto» vuol dire
  pochissimo — `cambio_btc_eur` è fail-open e tiene l'ultimo valore
  noto, che sopravvive ai riavvii —, e soprattutto adesso chi non lo
  vuole correre quel rischio ha il toggle.
  LE PURE RESTANO PURE, ed è il perno: guadagnano ARGOMENTI
  (`articolo_eur`, `valuta`), non una chiamata. Il cambio lo prende il
  chiamante, dove lo prende già, e la conversione resta UNA —
  `_eur_interi(sats, cambio)`, specchio di `_sped_in_sats`: euro INTERI
  e per DIFETTO (49,99 è sotto una soglia da 50: nessuna promessa scatta
  per un arrotondamento), `None` quando il cambio manca. Si chiama UNA
  VOLTA per conto e il numero va a tutte e due le promesse.
  «LE DUE PROMESSE GUARDANO LO STESSO NUMERO» si RIFORMULA e resta una
  proprietà della struttura: guardano lo stesso ARTICOLO LORDO, ognuna
  nell'unità che ha dichiarato. I due giudici ricevono TUTTE E DUE le
  facce — i sats, che ci sono sempre per costruzione (è la cifra della
  invoice), e gli euro, che sono `None` senza conversione — e scelgono.
  Fail-closed dentro il giudice: euro senza conversione = non scatta,
  valuta fuori catalogo = non scatta, e mai un ripiego («sarà euro»)
  che misurerebbe un carrello in un'unità che nessuno ha promesso.
  IL MODELLO È DUE COLONNE PIÙ UNA, e il costo del cantiere è tutto lì:
  le colonne in SATS (`sconto_pacco_valore`, `sped_gratis_soglia`), che
  per due giorni non le ha lette nessuno, tornano VIVE col significato
  che hanno sempre avuto — un nome non cambia mai significato, ed è
  precisamente ciò che permette di riaccenderle invece di migrare dei
  dati. Accanto, `sconto_pacco_valore_valuta` e `sped_gratis_valuta`
  `TEXT DEFAULT 'eur'`: quel DEFAULT **È** LA MIGRAZIONE — SQLite
  riempie le righe di ieri e ogni soglia impostata oggi continua a
  significare quello che significa adesso, byte per byte. Nessuno
  script, nessuna promessa che cambia sotto i piedi di nessuno (il
  precedente è `sconto_pacco_criterio TEXT DEFAULT 'pezzi'`).
  IL TOGGLE CONSERVA, NON CONVERTE (decisione di Andrea), e le due
  colonne NON si tengono in pari: ognuna è l'ultima cifra scritta in
  quell'unità, e il toggle mostra quella — vuota la prima volta, cioè
  le pillole. Tre ragioni: 85 € → 92.391 sats è un numero che nessuno
  ha scelto e va riarrotondato a mano; ovunque nell'app il toggle €/₿ è
  una VISTA — cambia come si LEGGE un numero, mai cosa È (il foglio
  dell'offerta ha l'ancora `offCifra` apposta, contro la deriva di
  centesimo in centesimo) — mentre qui cambia la SOSTANZA della
  promessa, e convertire confonderebbe le due cose; e il toggle del
  criterio, un centimetro sopra, conserva già così. È il patto delle
  due tariffe di spedizione e delle tre soglie, e il `COALESCE` lo
  garantisce lato server.
  LA CIFRA CONSERVATA PUÒ ESSERE STALE, e va detto: chi è passato per il
  travaso di venerdì ha entrambe le colonne piene, e la sua cifra in
  sats è quella di mesi fa, al cambio di allora — precisamente il numero
  che il passaggio all'euro voleva seppellire. L'anteprima la fa leggere
  PRIMA di salvare e a salvare è il bottone: niente cambia in silenzio.
  L'UNITÀ IN USCITA LA DICE QUALE CHIAVE È PIENA. Nel DATABASE la valuta
  è una colonna esplicita (le due soglie coesistono perché si conservano
  a vicenda); in USCITA no — `_sconto_pubblico` e `_sped_gratis_pubblico`
  popolano la chiave in sats SOLO a valuta 'sats' e quella in euro SOLO
  a valuta 'eur', e le chiavi si escludono per costruzione. Così il
  client prende «quella piena» senza un «if» e non può sbagliare unità;
  e la retrocompat si chiude in cerchio, perché un client di PRIMA del
  passaggio all'euro — che quelle chiavi le legge in sats — su un
  negozio in sats le trova finalmente giuste, e altrove non trova
  niente (un'assenza, non una bugia). Le chiavi del preventivo
  esistevano già a zero (`sconto_valore`, `mancano_sats`,
  `sped_gratis_soglia`, `mancano_sped_sats`): non se n'è inventata
  nessuna.
  LE CHIAVI VECCHIE DEL BODY (`valore`, `soglia`) RESTANO IGNORATE PER
  SEMPRE — portavano sats senza dirlo, e scriverle oggi metterebbe una
  cifra in una colonna che la promessa magari non guarda, con la
  trappola che si presenta mesi dopo al primo tocco del toggle. Stessa
  ragione per i nomi delle leve: `_SATS` in coda, e i nomi nudi
  pre-venerdì restano inerti.
  MA «IGNORATA» NON DEVE VOLER DIRE «LETTA COME ZERO», ed è un difetto
  PREESISTENTE nato col passaggio all'euro e chiuso qui (la domanda di
  Andrea: «cosa succede in pratica a un venditore col client in cache
  che tocca Salva?»). Le due risposte erano diverse e tutte e due
  cattive: sullo SCONTO un 400 col messaggio SBAGLIATO («parte da almeno
  1 €» a chi ne ha scritti novantamila), che manda a cercare il guasto
  dalla parte opposta; sulla SPEDIZIONE GRATIS il caso peggiore —
  `int(d.get("soglia_eur") or 0)` faceva 0 su un body vecchio, e zero lì
  è lo SPEGNIMENTO: il venditore premeva «Aggiorna la soglia» e la
  promessa si spegneva in silenzio. LA REGOLA, una sola per tutti i
  casi: la chiave del valore NELL'UNITÀ DICHIARATA dev'essere PRESENTE
  nel body — assente = 400 esplicito che dice cosa fare
  (`MSG_CLIENT_VECCHIO`), mai un salvataggio muto. È il patto di
  `spedizione_punto_dichiarata` (la dichiarazione è la presenza della
  chiave, mai il suo valore) arrivato dove venerdì non era arrivato, e
  copre gratis anche la variante nuova (`{soglia_eur: 50, valuta:
  'sats'}`, la cifra nella chiave dell'altra unità). Lo spegnimento
  resta ESPLICITO: `percento: 0` per lo sconto, uno zero in una chiave
  RICONOSCIUTA per la spedizione, e azzera tutte le soglie — «spento» è
  uno stato solo.
  LA LEZIONE STRUTTURALE, che è la metà che conta: **«soglia euro a
  zero» ha smesso di voler dire «promessa spenta»**, e TRE posti lo
  codificavano — l'avviso d'avvio `avvisa_soglie_da_convertire` (che
  avrebbe mentito a OGNI riavvio, per sempre, rompendo il patto «si vede
  una volta, al deploy»), il controllo del LIBRO MASTRO (che avrebbe
  suonato su ogni negozio in sats: è così che gli allarmi muoiono) e la
  query dei SUGGERIMENTI (il bot che invita ad accendere ciò che è già
  acceso). Più i gemelli in `converti_soglie_euro.py` e
  `query_libro_mastro.sql`. A sorvegliarli non c'è un elenco ma un
  CENSIMENTO (la lezione del titolo nudo): ogni confronto con zero su
  quelle colonne dev'essere accompagnato dalla valuta della SUA famiglia
  o dalla colonna gemella, così il quarto posto di fra sei mesi entra
  nel conto da solo.
  IL LIBRO MASTRO guadagna un controllo NUOVO, e la nota che stava qui
  si rovescia: «per la spedizione gratis non c'è il gemello, perché c'è
  un intero >= 0 dove 0 significa spenta e non esiste un valore rotto da
  trovare» era vera fino a ieri — adesso una `sped_gratis_valuta` fuori
  catalogo è una promessa accesa che non scatta mai, in silenzio.
  IMPERFEZIONE DICHIARATA, ed è lo SPECCHIO di una già accettata: la
  promessa è esatta quando l'unità della soglia combacia con quella del
  listino, e deriva ai bordi altrimenti. Una soglia in sats su un
  listino in EURO guarda un `articolo` che si ricalcola a ogni tick,
  quindi al filo esatto preventivo e invoice possono non essere
  d'accordo; il caso opposto — soglia in euro su listino in sats —
  esiste da sempre. La novità è che adesso un negozio tutto-sats può
  essere ESATTO, cosa che prima non poteva.
  IL «≈» DELL'ALTRA VALUTA NON TORNA, né nel campo né sulle pillole: è
  esattamente il campo d'aiuto che venerdì è stato cancellato, e
  rimetterlo riporterebbe l'ambiguità «quale delle due è la promessa?»
  che il toggle esiste per togliere.
  A CAMBIO MUTO LA PROMESSA NON SCATTA, E LO SI DICE. Il precedente è
  già in casa, negli avvisi di ricerca: «cambio mai arrivato = l'avviso
  EUR NON scatta, meglio un match perso che uno sbagliato». Il `None`
  si gestisce DENTRO i due giudici (fail-closed come `importo_invoice`,
  un posto solo invece di quattro «if» nei percorsi del conto); il
  preventivo porta `promesse_sospese` — il motivo, mai un silenzio — e
  la pagina Paga mette una riga onesta al posto dell'invito. Le righe
  pubbliche RESTANO: dicono la regola del negozio, che è vera, non un
  verdetto su quel carrello. NESSUN 503 NUOVO: `serve_cambio_duro` è
  distinto dal bisogno della promessa — senza cambio un listino in
  euro non si sa CONVERTIRE e l'ordine non nasce, una promessa non si
  sa solo VALUTARE, e far fallire un acquisto perché non si riesce a
  regalare uno sconto sarebbe curare un male causandone uno peggiore.
  DUE CONSEGUENZE DICHIARATE: se il cambio muore fra preventivo e
  pagamento la invoice nasce senza promessa mentre la pagina la
  mostrava (il paySheet dice comunque le cifre vere della risposta, il
  pattern già accettato per la lampo che scade); e il costo cade sui
  negozi TUTTO-SATS, che il cambio non lo toccavano proprio.
  SCARTATO un cambio di riserva NOSTRO con scadenza: sbaglierebbe solo
  nella fascia stretta attorno alla soglia invece che su tutti i
  carrelli, ma sarebbe il primo numero inventato che decide del denaro.
  EURO INTERI, non centesimi e non `REAL`: il filo resta esatto senza
  una convenzione nuova, la colonna ha la stessa forma delle sorelle
  (`INTEGER DEFAULT 0`), e una soglia è una promessa di bottega — «da
  50 €», non «da 49,90», che è un trucco da listino.
  IL CASSETTO NON PARLA PIÙ UNA VALUTA SOLA, e la nota si è sdoppiata:
  `NOTA_SOGLIA_EURO` è diventata `notaSoglia(valuta)` — una FUNZIONE con
  due testi, in un posto solo e portata da tutti e due i cassetti (il
  patto di `AVVISO_INTERMEDIARIO`, che regge: due copie della stessa
  avvertenza un giorno divergono). In euro dice che la soglia non cambia
  da sola col cambio, in sats che è fissa in sats e che in compenso non
  ha bisogno del cambio per scattare; tutte e due finiscono con «tu
  incassi sempre in SATS», che è vero comunque ed è la riga che tiene
  onesto il cassetto di un negozio che promette in euro. Il campo
  d'aiuto in euro, i due `*DaEuro` e gli `≈` sulle pillole restano
  CANCELLATI. Per chi COMPRA non si aggiunge niente: le righe pubbliche
  restano una riga, e il momento in cui conta — il paySheet — parla sats
  da solo (`contoScomposto` scrive «sats» su ogni riga).
  LA MISURA È IL LORDO DEL CONTO, cioè l'articolo DOPO lampo e accordo
  (`_unitario_effettivo` li ha già applicati) e PRIMA dello sconto — o
  si morderebbe la coda. CONSEGUENZA VOLUTA, da sapere perché sembra
  un bug quando un venditore la nota: una lampo al −50% può far
  scendere SOTTO soglia un carrello che a listino ci arrivava. È
  giusto così — la soglia guarda quel che si paga davvero per la
  merce, non un listino che in quel momento non è il prezzo di
  nessuno — e scontare ancora un carrello che la soglia non la
  raggiunge più sarebbe la vera incoerenza. C'è la prova apposta, e il
  cassetto lo dice al venditore sotto l'anteprima.
  IL MONO SCONTA, PUNTO (12 ago 2026, decisione di Andrea che
  ROVESCIA PER INTERO la decisione 1 e le due voci che la
  presidiavano — e vanno tenuti TUTTI E DUE i perché, perché quello di
  allora era vero e ha deciso la forma della cura).
  LA REGOLA NUOVA in una frase: lo sconto vale su OGNI acquisto del
  negozio — tre copie dello stesso articolo comprate dalla scheda sono
  tre pezzi, e una soglia a valore superata è superata, anche con un
  pezzo solo. Tutti e due i criteri, tutte e due le valute.
  IL PERCHÉ DI ADESSO: è quello che la gente si aspetta (Andrea ci si
  è stupito lui stesso, due volte in due giorni), e la mezza regola
  era già una BUGIA IN VETRINA — l'invito del carrello conta Σ
  quantità, quindi un carrello con UNA riga × 10 mostrava «✅ Sconto
  −X% nel conto», poi `apriAcquistoSet` dirottava sul binario mono e
  la riga non nasceva. Il rovesciamento sana un disallineamento che
  esisteva già.
  IL PERCHÉ DI ALLORA, che resta a verbale: si temeva il malinteso
  «da 100.000 sats» letto come «di spesa» (curato coi testi, ora
  riscritti sul perimetro nuovo), e soprattutto la divisione a ritroso
  dell'unitario, che uno sconto di testata avrebbe rotto IN SILENZIO.
  Quel timore ha dettato la cura: la divisione ora RIAGGIUNGE
  `sconto_sats` (la ricetta che il commento di `_righe_ordine`
  prescriveva dal primo giorno) e le sue copie sono TRE —
  `_righe_ordine`, la RIPRESA del pentito in `compra()` che la rifà a
  mano, la riga «N pezzi × unitario» del client — sorvegliate da un
  CENSIMENTO in `prove_divisione_a_ritroso` (la lezione del titolo
  nudo: estrae dal sorgente la FORMA della sottrazione dalla testata,
  chiede che le copie siano esattamente quelle e che ognuna riaggiunga
  lo sconto — la quarta di domani entra nel conto da sola). Una copia
  dimenticata non fa fallire niente: mostra un unitario storto in
  ordine, notifiche e CSV, in silenzio — per questo il censimento e
  non un elenco.
  LA MEZZA VIA È QUELLA SCARTATA, e va tenuta perché torna in mente:
  «nel carrello sì, dalla scheda no» NON è applicabile — il carrello a
  una riga e la scheda sono la STESSA porta server-side (stesso body
  mono), e costruire la differenza vorrebbe dire far dipendere un
  prezzo da quale JSON manda il client. O il mono sconta, o non
  sconta: la decisione è per intero, mai a metà.
  COSA È CAMBIATO, il censimento del cantiere: 1) i chiamanti di
  `_sconto_pacco` sono QUATTRO (compra mono, compra set, i due
  preventivi) e la regola nel mono si legge FUORI dal gate della
  spedizione — vale anche su ritiro e codice online, e sul DIGITALE
  (è sugli articoli, non sulla strada); 2) `articolo_sats` nella
  risposta del mono è diventato il NETTO come nel set, con
  `articolo_lordo_sats` e le chiavi sconto accanto (il client di ieri
  somma comunque giusto, gli manca solo la riga del risparmio);
  3) il controllo «mono scontato» della ronda È MORTO (sarebbe un
  falso allarme permanente) e al suo posto ci sono DUE invarianti veri
  che al mono mancavano — «aritmetica del mono» (la divisibilità
  esatta) e «sconto fuori scala (mono)», coi loro casi rotti e il mono
  scontato SANO in db_sano; i controlli della ronda salgono a 16;
  4) i quattro testi-antidoto sono riscritti sul perimetro nuovo e le
  loro sentinelle ROVESCIATE («nello stesso carrello» è morto in
  frase, etichetta, cassetto e riga fissa; «Un oggetto solo paga
  pieno, per quanto costi» è vietato da una prova — e la sentinella
  legge anche i commenti, non citarcelo), più la sentinella NUOVA sul
  contenuto di `frasePromessaSconto`, che era il buco; 5) a cambio
  muto la promessa a valore in euro non scatta e l'ordine NASCE (mai
  un 503 nuovo, `promesse_sospese` lo dice — il pattern della
  spedizione gratis); 6) la RIPRESA porta le chiavi sconto con le
  cifre CONGELATE dell'ordine (la invoice viva è il lock del prezzo:
  una regola cambiata nel frattempo non riscrive).
  L'ANTEPRIMA DEL CASSETTO dice il perimetro nuovo dentro la frase in
  grassetto (la lezione dello stupore sul 14.000 resta: ciò che la
  promessa fa e non fa si dice DENTRO la frase, mai in grigio dopo il
  bottone): a pezzi «Da 3 pezzi in su, −10% — su ogni acquisto, anche
  più copie dello stesso articolo. Chi ne prende 2 paga pieno.» (il
  controesempio sotto soglia resta VERO e resta), a valore «Da 10 € di
  articoli, −15%. Vale su ogni acquisto, anche un oggetto solo.»
  L'ASIMMETRIA CON LA SPEDIZIONE GRATIS NON ESISTE PIÙ: le due
  promesse hanno lo stesso perimetro, e uniformare i testi — che ieri
  era l'errore da non fare — oggi è la verità. La decisione 3 invece
  RESTA: la promessa si dice in pubblico negli stessi posti di prima
  (testata negozio e «Altri oggetti»), mai nelle card né nelle pillole
  del dettaglio, e NIENTE badge nuovo in scheda — il verdetto lo dà la
  pagina Paga, che dal 12 ago 2026 ha L'INVITO DELLE DUE PROMESSE
  (chiesto da Andrea in due tempi: prima lo sconto — nel carrello
  c'era, lì no — poi la spedizione, che deve parlargli uguale): la
  stessa forma del carrello, in UNA fila dove
  ognuna ha il suo stato — sono indipendenti, quindi una verde e una
  no è uno stato normale. Sotto soglia «🚚 Ancora 12 € → spedizione
  gratis» e «🎁 Ancora N pezzi → −X%» (a valore la CIFRA che manca,
  via `cifraSoglia`, nell'unità della promessa); quando scatta il
  verde NUDO — «✅ Sconto −X%», «✅ Spedizione gratis»: la coda «nel
  conto» è caduta il 13 ago 2026 (deciso da Andrea con l'unitario
  scontato in pagina — lo sconto si vede da solo sul prezzo, e la
  spedizione ce l'ha la riga «gratuita» del conto due dita sotto: la
  pillola è il cartello, il conto è il fatto). E dal 13 ago 2026
  (secondo tempo, chiesto da Andrea) sono nude ANCHE NEL CARRELLO:
  la coda «nel conto» era portante finché il totale della barra
  restava al lordo — adesso il totale mostra lo scontato col lordo
  barrato (vedi la voce della barra del carrello) e la coda direbbe
  di cercare altrove una cosa già in vista; la sentinella ora conta
  che di code non ne resti NESSUNA. La fila sta SOPRA la riga della consegna
  (12 ago 2026, decisione di Andrea — è un fatto del negozio, si
  legge prima di scegliere la strada) e il suo ordine è quello di
  casa: vedi «L'ORDINE DELLA FILA È UNO SOLO», sotto «LE PROMESSE
  DIVENTANO BADGE».
  LA VESTE DELLA FILA DI PAGA È A RIGHE PIENE (ago 2026, decisione
  di Andrea): non più chip affiancati di larghezze diverse — che si
  leggevano come bottoni randagi fra la card e la Consegna — ma
  righe a tutta larghezza, tono quieto, angoli da riquadro come le
  vie sotto. Nacque solo-CSS su `#acqCorpo > .pills`; dal 13 ago
  2026 la veste è la CLASSE `.fila-promesse` sui TRE contenitori —
  Paga, carrello e «Altri oggetti» — un posto solo, e la quarta
  superficie di domani mette la classe e ha finito (le sentinelle
  contano i tre template e il display:block della pillola, che nel
  carrello vive dentro lo span-scatola e da inline non prenderebbe
  la larghezza). Il verde della conferma resta verde.
  LA STRADA SCARTATA, costruita e
  guardata a schermo prima di decidere: i badge DENTRO la card
  dell'articolo — stava più in ordine, ma costava il rovesciamento
  della decisione del 12 ago («la fila sopra la consegna»), spezzava
  l'uniformità della fila fra le quattro superfici, e nel SET non
  c'è una card sola che li ospiti; per un problema che era
  d'aspetto, la cura è stata la veste e non la posizione.
  E LE RIGHE SI RIEMPIONO COL PROGRESSO (13 ago 2026, decisione di
  Andrea, scelta su DUE prototipi guardati a schermo): la pillola
  sotto soglia si riempie di verde da sinistra, con un bordo
  NETTO, man mano che il carrello sale — `barraPromessa` scrive
  `--barra-p`/`--barra-c` sulla classe `.pill-barra` (dal 13 ago è
  un ferro CONDIVISO fuori da renderAcquisto, vedi sotto).
  IL COLORE VIRA COL PROGRESSO (terzo giro dello stesso 13 ago,
  chiesto da Andrea): la coppia `--barra-da`/`--barra-a` — slavato
  #DCEEE4 → acceso #8FCBAB di giorno, #243B2C → #35684A di sera —
  mescolata dal progresso stesso col color-mix nello style di
  `barraPromessa`. Il primo giro col `--trust-soft` nudo non si
  notava (è il FONDO della pill-trust, nato per stare sotto un testo,
  non per staccare da una carta quasi uguale); il secondo, a tinta
  fissa più carica, è durato mezza giornata. MAI dal rosso (nell'app
  il rosso è problema, e una promessa in corsa è un invito, non un
  fallimento) e MAI dal grigio, prototipato e SCARTATO a schermo: la
  mescola di mezzo fa un olivastro spento, e si perde la famiglia
  della fiducia. DAL QUARTO GIRO anche la tinta corre: il fill è un
  ::before ASSOLUTO — larghezza in `--barra-p`, colore in
  `--barra-c`, scritti da `barraPromessa` — perché width e
  background-color si transizionano davvero, mentre un gradiente no
  (prima il colore cambiava a scatti fra un render e l'altro).
  z-index:0 sul guscio e -1 sul fill, tutti e due necessari, e
  overflow:hidden per gli angoli. Contrasto dell'inchiostro
  sull'acceso pieno: 8,1 di giorno, 5,3 di sera.
  E LA SCATTATA È PIENA E ACCESA (quarto giro, visto da Andrea a
  schermo nei due temi — ROVESCIA il «la corsa chiama, il traguardo
  riposa» di mezza giornata prima): la barra si accendeva salendo e
  allo scatto la pillola tornava al verde tenue, cioè il traguardo
  PERDEVA forza — sembrava che qualcosa si fosse spento proprio nel
  momento più forte, e di sera l'inverso. Ora la pill-trust veste
  l'acceso pieno `--barra-a` con l'inchiostro sopra — nata «solo di
  Paga», dal 13 ago 2026 (secondo tempo) vale ANCHE nel carrello,
  che corre la stessa barra: due traguardi diversi per la stessa
  promessa erano una divergenza senza motivo, la regola vive sulla
  BASE `.pill.pill-trust` e il tenue di `.trust-soft` non lo veste
  più nessuno — e lo scatto corre l'ultimo tratto nello STESSO
  acceso (`.barra-scatto`: guscio a carta, fill al 100%; il suo
  selettore porta un `.pill` in più APPOSTA, deve battere la base
  per specificità e non per ordine): la tinta non
  salta, il traguardo guadagna. LA DISTINZIONE dalla barra quasi
  piena, ora che la tinta è una, è di FORMA e di TESTO: il tetto a
  99 lascia sempre la fetta di carta col bordo netto — una barra,
  mai un fondo — contro la pillola INTERA bordo a bordo, e
  «Ancora N → …» contro «✅ …».
  Il progresso è `(soglia − mancano)/soglia`, nell'unità della
  promessa: in Paga coi numeri che il preventivo porta GIÀ (il
  client riceve, non calcola), nel carrello — dal 13 ago — coi
  numeri del CLIENT, gli stessi che il testo «Ancora N» diceva già:
  la barra non aggiunge nessuna pretesa nuova, e la fascia del
  cambio a soglia in euro è quella dichiarata sul giudice
  `statoScontoPacco`. A pezzi sale a gradini, a VALORE è continuo — la barra
  dice la verità in tutti e due i casi senza un ramo, e a cambio muto
  la promessa in euro non è una pillola ma prosa, quindi lì la barra
  non esiste per costruzione. TRE righe da non ammorbidire: il TETTO
  A 99 (una barra piena su una pillola non-verde direbbe «scattata» a
  chi guarda solo il colore — piena è solo la pill-trust); lo style
  che c'è SEMPRE, anche a 0% (senza background-size esplicito il
  background-image coprirebbe la pillola intera, cioè il falso al
  primo pezzo); e LA CORSA MORBIDA (chiesta da Andrea, che rovescia
  il «niente transizione» della nascita): il «da» che a un nodo
  ricostruito manca si RECUPERA — prima del render si legge il
  computed del ::before delle pillole vive, larghezza E colore, che
  a metà corsa sono i valori INTERPOLATI — e i bersagli arrivano al
  SECONDO requestAnimationFrame, a fotogramma reso.
  LA DIAGNOSI DEL «SI ANIMA SOLO LA SPEDIZIONE» (caso dal campo,
  quarto giro, ed è la riga da rileggere prima di toccare qualunque
  FLIP a più elementi): la prima stesura faceva il giro PER PILLOLA
  con un `void offsetWidth` fra il «da» e il bersaglio — e il reflow
  della PRIMA pillola computava lo stile anche della SECONDA, che in
  quell'istante aveva ancora il bersaglio inline: il suo stile
  «prima» restava fissato al bersaglio e il suo FLIP diventava
  bersaglio→da→bersaglio, un no-op. Animava solo la prima della
  fila, la spedizione. Da qui la regola: PRIMA tutti i «da», POI
  tutti i bersagli in un colpo solo, mai un flush in mezzo — e il
  doppio rAF copre anche il nodo appena inserito, che senza un
  fotogramma reso può non far partire la transizione affatto. È
  anche ciò che tiene onesti i + veloci (le transizioni CSS non si
  accodano: ritargeting nativo dal valore interpolato) e il NUMERO
  non aspetta, si aggiorna secco al render. In discesa vale il
  simmetrico (da 100 e acceso); chi nasce senza un «da» non corre;
  reduced-motion spegne la transizione dal CSS e i bersagli arrivano
  comunque.
  E LA SCATOLA DELLA MISURA È clientWidth, MAI getBoundingClientRect
  (13 ago 2026, lo «scattino indietro a ogni tocco» visto dal
  telefono e trovato CAMPIONANDO i valori di partenza, non deducendo):
  il % del ::before si risolve sul PADDING BOX della pillola — il
  containing block di un absolute — mentre il rect porta anche il
  bordo (3px): ogni cattura usciva fino a ~1% del progresso più
  bassa del vero — 2-3px ad alto progresso, ridipinti INDIETRO secchi
  e ri-percorsi in avanti in 350ms, che è esattamente lo scattino —
  e la scattata reduce dal suo scatto si misurava 99,4 invece di 100
  e rifaceva una mini-corsa a ogni tocco: il rimbalzo del bordo
  destro. Con la scatola giusta la cattura a riposo È il valore di
  prima (misurato: 10,99982 contro 11) e la corsa che non serve non
  parte. ONESTÀ SULLA VERIFICA, per la seconda volta (la lezione
  della tastiera): in headless le transizioni NON AVANZANO — la
  corsa non si campiona né si fotografa, si prova la STRUTTURA
  (partenze in blocco, niente flush, bersagli a fotogramma reso) e
  il movimento lo dice il telefono.
  LA STRADA SCARTATA, prototipata e fotografata: il colore
  che si SATURA (color-mix verso il verde) — 67% e 73% si vedevano
  uguali, e il quasi-verde si leggeva come promessa già scattata.
  IL SECONDO PASSO È STATO FATTO (13 ago 2026, chiesto da Andrea):
  i badge del carrello corrono la STESSA barra — qui c'era scritto
  «restano senza barra, dichiarato» — coi ferri CONDIVISI
  `barraPromessa`/`barreCattura`/`barreCorri`, estratti da
  renderAcquisto proprio per questo: una seconda stesura della corsa
  è il posto dove il prossimo «si anima solo la spedizione»
  tornerebbe a nascondersi. Le due scatole del carrello passano dai
  ferri UNA alla volta e le partenze riunite reggono lo stesso: la
  cattura della seconda trova la prima già tutta alle partenze (i
  bersagli aspettano il rAF), mai a metà.
  E QUANDO LO SCONTO SCATTA SI VEDE ANCHE SULL'UNITARIO (ago 2026,
  decisione di Andrea — la via (c) fra le tre proposte): accanto
  all'unitario compare il tag verde «−X%» (`.sconto-tag`, la lingua
  della pillola di conferma), che dice la REGOLA, esatta per
  definizione. E DAL 13 AGO 2026 ANCHE LA CIFRA — l'unitario
  scontato, ripensamento di Andrea: il tag dice che lo sconto c'è,
  ma la cifra è quello che uno cerca — però SOLO QUANDO LA DIVISIONE
  È ESATTA, misurato PRIMA di decidere: in produzione ZERO inesatte
  su 52 annunci scontati (i prezzi veri sono tondi: al 10% basta un
  multiplo di 10, al 5/15% di 20, al 20% di 5), quindi la cifra si
  vede sempre e il ramo solo-tag è una CINTURA che oggi non scatta
  mai. La calcola il SERVER sulla faccia NATIVA — sats, o CENTESIMI
  per i listini in euro, la cui faccia sats è convertita e porta già
  il ≈ del cambio — nelle chiavi `articolo_unitario_netto_sats/_eur`
  (zero = niente cifra), e il client la MOSTRA col pieno BARRATO
  piccolo sotto, la resa della lampo (`.acq-barrato`, col `.unit`
  inline-block che ferma la barratura: la lezione del listino
  barrato). MAI UN ≈ DA ARROTONDAMENTO, ed è il motivo che ha chiuso
  la questione (Andrea): in quella casella il ≈ della conversione
  compare GIÀ, e due significati sulla stessa cifra nello stesso
  posto sono peggio di nessuna cifra — il perché di ieri («un numero
  che non torna moltiplicando si legge come un bug») resta vero e
  governa il caso inesatto, dove la cifra semplicemente non compare.
  Il tag resta gated su `sconto_sats>0` (mai sull'invito), i SET non
  hanno un unitario in card e restano fuori per costruzione, la DEMO
  non simula lo sconto e tace da sola. Sentinelle in CI. IL VERDE DELLA SPEDIZIONE CONVIVE con la
  riga «Spedizione: gratuita» del conto, ed è deciso guardando lo
  schermo: la riga dice il COSA, il verde dice il PERCHÉ (è la
  promessa del negozio a essere scattata) — e senza, nello stato
  misto la coppia si spezzerebbe e la promessa appena guadagnata
  sembrerebbe evaporata, la lezione dell'invito del carrello. MA COI
  NUMERI DEL SERVER (`mancano_*`): qui il preventivo c'è, quindi la
  fascia stretta del cambio che l'invito del carrello dichiara non
  esiste — e a CAMBIO MUTO la promessa in euro non si applica affatto
  e resta PROSA che lo dice («…ma adesso non riusciamo a fare il
  cambio: …»), OGNUNA gated sulla SUA valuta: `promesse_sospese` è un
  flag combinato, e senza il filtro una spedizione in SATS si sarebbe
  detta sospesa per colpa di uno sconto in euro — il bug preesistente
  del ramo spedizione, tolto col riordino. Vale su ogni via lo
  sconto (è sugli articoli), solo dove si spedisce la spedizione; in
  DEMO le chiavi non arrivano e il blocco tace da solo.
  E DALL'AGO 2026 LA 🚚 GUARDA ANCHE LA VIA SCELTA: sulla via
  «Ritiro in zona» o «Codice online» la pillola della spedizione
  gratis SPARISCE (e con lei la prosa del cambio muto, stesso if,
  stessa ragione), mentre la 🎁 dello sconto resta su ogni via e non
  prende NESSUN gate — c'è la sentinella nei due versi. ROVESCIA la
  decisione del 12 ago, e il motivo è che è cambiato il DEFAULT:
  allora il ritiro era il preselezionato-di-fatto e il badge serviva
  a far cambiare idea a chi non aveva scelto niente; ora che il
  default è il punto, chi sta su ritiro o codice online ci è
  arrivato TOCCANDO — e a quel punto un cartello sulla spedizione è
  rumore. LA CONDIZIONE CHE LEGA LE DUE DECISIONI, ed è quella da
  ricordare: il gate del 🚚 dipende da quale via è il default — se
  il default cambia ancora, questo gate va riguardato insieme.
  Restano
  invariati per scelta: il suggerimento del bot (chiede
  ancora ≥2 annunci — allargarlo è un'altra decisione), la DEMO
  (asciutta, non simula lo sconto) e le ASTE (`crea_ordine_pagato`
  non sconta: il vincitore paga l'esposto). La barra del carrello,
  che qui stava «al lordo», dal 13 ago 2026 mostra lo scontato col
  lordo barrato — vedi la voce sua, sotto lo sconto carrello.
  E I VENDITORI CHE AVEVANO GIÀ LA REGOLA ACCESA LO SANNO
  (`avvisa_sconto_su_mono`, campagna UNA-TANTUM GLOBALE col timbro
  nella tabella `timbri` e NON una colonna per utente: è un evento del
  deploy, non una condizione che ricorre — una colonna lascerebbe la
  campagna armata verso chi accende lo sconto il mese prossimo, che le
  regole nuove le trova già nel cassetto). Timbro PRIMA degli invii, il
  messaggio dice la LORO regola con le loro cifre e come spegnerla;
  imperfezione dichiarata: un crash a metà loop perde i restanti — sui
  cinque negozi di oggi si verifica dal journal, che nomina i
  destinatari.
  IL MODELLO: `utenti.sconto_pacco_soglia`/`sconto_pacco_percento`
  (0/0 = spento; nessun flag «dichiarata» come per la tariffa punto —
  lì lo zero era ambiguo, qui uno sconto dello 0% e nessuno sconto
  sono la stessa cosa) più `sconto_pacco_criterio TEXT DEFAULT 'pezzi'`
  e `sconto_pacco_valore` (ago 2026). TRE colonne e non due riscritte:
  `sconto_pacco_soglia` resta i PEZZI e non cambia MAI significato —
  chi legge il database a mano (il polso SQL) non deve incrociare due
  colonne per sapere cosa vuol dire un numero, e chi prova il criterio
  a valore e torna indietro ritrova la sua soglia. È il patto delle due
  tariffe di spedizione, tenute separate. Il `DEFAULT 'pezzi'` È la
  migrazione: SQLite riempie da sola le righe di ieri (il precedente è
  `valuta TEXT DEFAULT 'sats'`), e NIENTE si fotografa in `ordini` —
  il criterio non serve alla ricevuta, che il «−10%» ce l'ha già, e
  sarebbe una colonna nella tabella del denaro per un'informazione
  ornamentale. Sull'ordine restano `sconto_sats` + `sconto_percento`
  come voce di TESTATA — `ordine_righe` resta INTATTA, gli unitari
  LORDI. È la strada che questo file dichiarava già preparata: lo
  sconto è una proprietà del CARRELLO, non della cosa, e limare gli
  unitari vorrebbe dire distribuire un resto su N righe e poi
  litigarci in disputa. L'invariante nuovo è della testata, ed è
  scritto nel DDL: `prezzo_sats = Σ(unitario×qta) − sconto_sats +
  spedizione_sats + protezione_sats`. Il `sconto_percento` è la
  fotografia della REGOLA e non della cifra (dedurla da
  sconto/articolo direbbe 9,99%), e si scrive SOLO se lo sconto è
  scattato — altrimenti la ricevuta di un ordine sotto soglia
  dichiarerebbe uno sconto che non c'è.
  `ordini.sconto_sats` È UNA COLONNA TESTIMONE, NON UN MOTORE, ed è la
  riga da leggere prima di toccare qualunque strada del denaro:
  l'unico numero che comanda è `prezzo_sats`, che nasce già scontato —
  incasso del venditore, rimborso, XP e CSV leggono LUI e solo lui,
  quindi NESSUNA delle quattro va toccata (verificato: `_sblocca_sats`,
  `_rimborsa_compratore`, `deposita_invoice` e l'export sono intonsi).
  Chi qui leggesse «il venditore deve incassare il pieno» e ne facesse
  un `netto_venditore(prezzo + sconto)` farebbe uscire dall'escrow DI
  ALTRI ORDINI la differenza, e la cintura di `paga_venditore` non lo
  vedrebbe: per lei dovuto e bolt11 combacerebbero. Sentinella apposta.
  IL CONTO: due pure nuove accanto alle altre — `_sconto_pacco`
  (la DECISIONE) e `_sconto_pacco_eur` — più `_conto_ordine(…,
  sconto=0)`, che è dove la SOTTRAZIONE avviene e in nessun altro
  posto: chi legge il conto usa `netto`, e nessun chiamante sottrae
  per conto suo (due sottrazioni sono uno sconto doppio, e la invoice
  nasce di là). Il default a 0 tiene il ramo mono identico byte per
  byte. Protezione e commissione si calcolano sul NETTO: la
  percentuale sta sul prezzo che si paga davvero, ed è la stessa
  strada che già seguono lampo e accordo. ARROTONDAMENTO: il netto col
  floor e lo sconto per DIFFERENZA, la regola di `_prezzo_lampo` —
  così `articolo − sconto` È il netto per costruzione (mai un sat di
  scarto fra la riga mostrata e il totale) e il sat di dubbio resta a
  CHI PAGA (999 a −10% → sconto 100, non 99). `_regola_sconto(criterio,
  soglia_pezzi, soglia_valore, percento)` è il lettore unico e prende
  quattro campi e non una riga — il patto di `in_ferie`: così serve la
  riga di `utenti`, gli alias `venditore_sconto_*` della vetrina e la
  prova in CI; restituisce `(criterio, soglia, percento)` con la soglia
  GIÀ quella del criterio scelto, cioè un valore solo da guardare, e
  `('', 0, 0)` quando non c'è una regola vera.
  IL CRITERIO IGNOTO NON RIPIEGA SUI PEZZI (ago 2026): la colonna VUOTA
  vale 'pezzi' — è letteralmente il mondo di ieri, cioè la
  retrocompatibilità — ma una stringa SCRITTA e fuori catalogo spegne
  tutto, perché ripiegare applicherebbe una soglia in pezzi che il
  venditore non ha promesso in pezzi (una colonna scritta a mano, o il
  rollback da un criterio futuro, farebbero scontare a caso).
  Fail-closed come `importo_invoice`, e la stessa riga fa da
  kill-switch alla leva `SCONTO_PACCO_CRITERI`.
  IL GEMELLO IN EURO NON DECIDE PIÙ DA SOLO: a criterio valore la porta
  si apre guardando i SATS, che l'euro non ha. Quindi `_sconto_pacco_
  eur(articolo_eur, percento)` ha perso la condizione ed è il chiamante
  ad azionarla (`… if sconto else 0.0`) — prima era ripetuta identica
  nei due gemelli, e col criterio quella copia sarebbe diventata il
  posto esatto in cui i due possono divergere. La cintura di
  `_strade_preventivo` resta e ne esce rafforzata.
  LA REGOLA D'ORO DELLA RETROCOMPATIBILITÀ, e vive in una pura sua —
  `_sconto_pubblico`: la soglia in PEZZI esce maggiore di zero SOLO a
  criterio 'pezzi'. È lei il lucchetto del client vecchio rimasto in
  cache, che di campi ne legge uno solo (`venditore_sconto_soglia`) e
  chiede `soglia>0 && percento>0` prima di disegnare la promessa: con
  la soglia a zero non disegna niente, e un'assenza non è una bugia
  mentre un «−10% da 100000 pezzi» lo sarebbe. Sta in una funzione e
  non a mano nelle due superfici (vetrina e profilo del negozio) perché
  una regola ripetuta in due posti è una regola che un giorno uno dei
  due dimentica — e stando in una pura si tortura in CI invece di
  sperarci.
  L'EURO SI SCONTA IN EURO e non convertendo i sats: un carrello nato
  in euro con la protezione a zero ha oggi un `totale_eur` ESATTO, e
  uno sconto non deve poter peggiorare la QUALITÀ di un numero — chi
  mostra il ≈ dove non serve, prima o poi lo toglie dove serviva. La
  clausola `and (sconto == 0 or sconto_eur > 0)` nel gate di
  `_strade_preventivo` è LA RIGA PIÙ DELICATA del cantiere: è l'unico
  punto dove la modifica potrebbe produrre una cifra precisa e FALSA
  invece di un ≈.
  `articolo_sats` DIVENTA IL NETTO nella risposta del preventivo e di
  compra, col LORDO e lo sconto come chiavi in più (`articolo_lordo_
  sats`, `sconto_sats`, e la REGOLA — `sconto_percento`/`sconto_soglia`/
  `mancano_pezzi` — che esce anche quando non è scattata, perché serve
  all'invito). È un cambio di contratto deciso: quella chiave ha
  sempre voluto dire «quanto paghi per la merce» ed è ciò che con
  spedizione e protezione FA il totale, quindi un client fermo a ieri
  somma comunque giusto e gli manca solo la riga del risparmio — che
  è un'assenza, non una bugia. `mancano_pezzi` lo conta il server
  anche se il client potrebbe: è esattamente il numero dove vive un
  off-by-one.
  ENDPOINT `POST /api/me/sconto-pacco` (pattern spedizioniere).
  `percento <= 0` è lo SPEGNIMENTO e non ha NESSUNA guardia (il patto
  del rientro dalle ferie). NIENTE `_impegni_aperti`, e non è una
  dimenticanza: le ferie ce l'hanno perché chiudere toglie una via
  d'uscita a chi ha già pagato, qui non si toglie niente a nessuno —
  gli ordini nati portano il loro sconto fotografato e la loro escrow
  è già scontata, e l'unica cosa «aperta» è un carrello nella memoria
  di un client, che non sta nel database, non ha scadenza e non ha
  controparte. Vale il conto del momento dell'acquisto, come per il
  prezzo e per la lampo. E niente `guardia_ferie_venditore`: lampo e
  asta ce l'hanno perché sono atti di vendita, mentre sistemare il
  listino mentre si è via è esattamente ciò che si fa in ferie.
  IL BODY DELL'ENDPOINT è `{criterio, soglia, valore, percento}`, e le
  DUE SOGLIE SI CONSERVANO A VICENDA: chiave assente = conserva (il
  pattern dello stock), con un `COALESCE` che tiene tutto in UN solo
  UPDATE — una SELECT prima aprirebbe la finestra in cui la regola è
  letta e non ancora scritta. Così chi prova un criterio e torna
  indietro ritrova la sua soglia, e un client vecchio — che di `valore`
  non sa niente — non cancella a ogni salvataggio una colonna che non
  ha mai visto. La risposta RILEGGE dal database: col COALESCE non si
  può dedurre dal body. Lo SPEGNIMENTO azzera invece entrambe, criterio
  compreso: «spento» resta uno stato solo, e chi spegne non deve saper
  compilare un campo.
  LEVE: `SCONTO_PACCO_ATTIVO` nasce ACCESA (non muove denaro verso
  l'esterno, abbassa soltanto un conto in entrata),
  `SCONTO_PACCO_SOGLIE`/`SCONTO_PACCO_VALORI_EUR`/`SCONTO_PACCO_SCONTI`
  sono le pillole del venditore (il patto di LAMPO_SCONTI),
  `SCONTO_PACCO_CRITERI` è il kill-switch del criterio nuovo (toglierlo
  di lì lo spegne per chi l'aveva scelto, senza un deploy), e
  `MIN_SOGLIA` 2, `MIN_VALORE_EUR` 1 e `MAX_PERCENTO` 30 restano la
  cintura del server anche se le liste cambiano. Il minimo a valore è
  basso di proposito: è una cintura contro lo zero travestito, non un
  giudizio su quanto debba valere un carrello (la regola di
  MAX_QUANTITA_ANNUNCIO — quanto vale il suo negozio lo sa il
  venditore, non noi).
  I NOMI DELLE LEVE PORTANO `_EUR`, E NON È COSMESI (ago 2026): una
  riga `SCONTO_PACCO_VALORI = (25_000, …)` già scritta in un config
  verrebbe letta come EURO, e la promessa non scatterebbe più — in
  silenzio. Col nome nuovo la riga vecchia diventa INERTE, che è la
  stessa regola delle colonne: un nome non cambia mai significato.
  Vale per `SCONTO_PACCO_VALORI_EUR`, `SCONTO_PACCO_MIN_VALORE_EUR`,
  `SPED_GRATIS_SOGLIE_EUR`, `SPED_GRATIS_MIN_EUR`. Le pillole sono
  BASSE (10·25·50·100 €, decisione di Andrea) e non la conversione
  delle vecchie: Barattolo è un mercatino dell'usato e il carrello
  medio è piccolo — con soglie alte la promessa non scatterebbe quasi
  mai, cioè sarebbe una vetrina senza effetto.
  LE COLONNE NUOVE sono `sconto_pacco_valore_eur` e
  `sped_gratis_soglia_eur`; le due in sats restano dov'erano, INERTI —
  nessuno le legge più, e sono anche l'unico posto dove ritrovare cosa
  il venditore aveva scritto (precedenti in casa: `utenti.comune`,
  `avatar_visibile`). `ordini` NON si tocca: le tre colonne testimone
  sono la cifra vera in sats, e questo cantiere non passa da lì.
  IL TRAVASO LO FA UNO SCRIPT, `converti_soglie_euro.py` (anteprima di
  serie, `--scrivi`, `--cambio` a mano, percorso di database
  opzionale; arrotonda all'euro più VICINO — lì si traduce una
  promessa, non si misura un carrello — e clampa al minimo dicendolo).
  NON `init_db`: è sincrona e senza rete, e una migrazione che dipende
  da CoinGecko può restare a metà — non su una riga che decide del
  denaro. A ricordarlo c'è UNA riga all'avvio
  (`avvisa_soglie_da_convertire`, che LEGGE e basta) e il polso SQL
  17d; NON una voce del libro mastro, perché finché lo script non è
  girato quello è uno stato transitorio LEGITTIMO, e un allarme che
  suona su uno stato legittimo insegna a ignorarlo.
  LE CHIAVI VECCHIE ESCONO A ZERO, e sono due denti dello stesso
  lucchetto: `_sconto_pubblico` azzera `valore` (il client di ieri lo
  legge in sats e scriverebbe «da 25 sats», che non è una promessa
  avara — è assurda, e sembra un guasto) e nasce
  `_sped_gratis_pubblico`, il gemello che questo file dichiarava NON
  necessario «perché il campo è UNO»: col passaggio i campi sono due,
  e la nota si rovescia. Stessa cosa nel BODY degli endpoint —
  `valore_eur` e `soglia_eur` sono chiavi nuove, e le vecchie si
  IGNORANO: un client in cache prende un 400 onesto invece di
  scrivere una soglia da cinquantamila euro.
  Superficie: i QUATTRO alias in `CAMPI_VETRINA` a costo ZERO
  (il JOIN su `u` c'era già) e nel profilo di `/api/negozio`, TUTTI
  normalizzati da `_sconto_pubblico` — così la leva spenta li spegne in
  tutte le vetrine insieme e il client non deve ricordarsi i casi.
  Il preventivo porta `sconto_criterio`/`sconto_valore`/`mancano_sats`
  accanto alle chiavi di sempre, speculari: la soglia in pezzi e
  `mancano_pezzi` tacciono a criterio valore, e viceversa — nessuno può
  leggere dei sats come se fossero pezzi. Nella risposta di compra il
  criterio è la FOTOGRAFIA di cosa è scattato (`crit if sconto else ''`,
  gemella della percentuale).
  IL LIBRO MASTRO guadagna UN controllo solo, e non sugli ordini: «una
  promessa di sconto che non può scattare» (criterio fuori catalogo, o
  soglia sotto il minimo STRUTTURALE — 2 pezzi, 1 sat, e non le leve:
  un allarme agganciato a una leva suonerebbe al primo ritocco della
  leva, ed è così che gli allarmi muoiono). Qui non si perdono sats: si
  perde una vendita, e in silenzio. I quattro controlli sugli ordini
  NON cambiano di un carattere, ed è la prova che il criterio non tocca
  il denaro; il POLSO invece sì (query 17), o la colonna «soglia»
  mescolerebbe pezzi e sats ed è il primo posto dove un umano si
  sbaglia.
  FRONTEND: la riga «Sconto carrello −10%» entra in `contoRighe` fra
  Prezzo e Commissione, SOLO quando scatta (una riga a zero direbbe
  «non hai avuto niente», che non è un'informazione); il valore arriva
  POSITIVO e il meno lo mette `cifraCtrl`, che guadagna un quarto
  argomento e resta il GIUDICE UNICO — un negativo spegnerebbe il ≈
  (che guarda `sats>0`) proprio dove serve, e `fmt()` scriverebbe il
  trattino ASCII invece del meno tipografico. Niente colore, solo il
  grassetto sulla cifra: l'unico chip colorato del sistema resta il
  «gratis» della spedizione. L'INVITO nella pagina del carrello
  (`aggiornaInvitoSconto`, agganciato ad `aggiornaBarraPacco` perché è
  LEI a girare a ogni ±) dice quanto manca e poi SI TRASFORMA
  in conferma invece di sparire — se sparisse, chi ha appena
  guadagnato lo sconto non vedrebbe cambiare niente. Il dato viene
  dall'ANNUNCIO e non dal preventivo (che ha una firma e arriva in
  ritardo). A criterio VALORE una cifra la porta, e il patto si
  riformula onestamente: L'INVITO NON CALCOLA IL RISPARMIO, RICEVE il
  totale — glielo passa `aggiornaBarraPacco`, che quel numero lo mostra
  già due centimetri più sotto, quindi i due non possono divergere.
  (Il «resta VIETATO applicare la percentuale» che stava qui è
  ROVESCIATO dal 13 ago 2026: la percentuale si applica nel TOTALE
  della barra, come RESA e con la formula del server — vedi la voce
  della barra, sotto. L'invito continua a non calcolare niente.)
  MA COL PASSAGGIO ALL'EURO L'INVITO DEL CARRELLO CONVERTE (ago 2026),
  ed è l'UNICO posto dell'app dove il client fa una conversione su una
  promessa: il preventivo in quella pagina non c'è, e chiamarlo a ogni
  tocco dello stepper è già stato valutato e scartato (il debounce
  litiga con chi sale in fretta). IMPERFEZIONE DICHIARATA, nuova: in
  una fascia stretta attorno alla soglia il cambio del client e quello
  del server possono non combaciare, quindi la riga può dire «✅
  attivo» dove il conto non sconta. È tollerabile perché è un invito
  durante la COMPOSIZIONE e non un verdetto — lo dice da sé, «lo vedi
  nel conto» — e senza `cambioVivo` la riga non compare affatto (il
  patto del ≈). Il floor è quello di `_eur_interi`, cioè il verso
  prudente. L'invito della pagina PAGA invece è SERVER-DRIVEN
  (`mancano_sped_eur`) e lì la fascia non esiste: quell'asimmetria si
  tiene, non si uniforma.
  Le righe PUBBLICHE non seguono il toggle — `setValuta` non ridisegna
  il negozio — ma dall'euro non ne hanno più bisogno: scrivono la
  cifra che il venditore ha scritto, senza ≈ e senza cambio, quindi si
  disegnano anche a cambio muto. Nel client il giudice della
  regola è UNO (`regolaSconto`) e la frase pubblica pure
  (`frasePromessaSconto`), per la stessa ragione di
  `_sconto_pubblico`: sono quattro le superfici che la mostrano — e
  dall'ago 2026 lo stesso vale per la SECONDA promessa
  (`regolaSpedGratis`/`frasePromessaSpedGratis`), che quella sentinella
  non ce l'aveva: buco trovato proprio con questo cantiere.
  IL TOTALE DELLA BARRA DEL CARRELLO MOSTRA LO SCONTATO (13 ago
  2026, decisione di Andrea che ROVESCIA il «resta al lordo,
  dichiarato» — come l'unitario in Paga): a soglia scattata
  `paccoTot` dice il NETTO col tag «−X%» accanto (secondo giro dello
  stesso 13 ago, visto da Andrea: in Paga c'era e qui no — stessa
  classe `.sconto-tag`, mai una copia, e la prima riga della somma è
  un flex suo perché `.pacco-somma` è una colonna) e sotto compare
  il lordo barrato
  (`#paccoPieno`, la resa della lampo e dell'unitario di Paga; il
  badge scattato torna NUDO, che «nel conto» direbbe di cercare
  altrove una cosa in vista due dita sotto). LE DUE METÀ DA NON
  CONFONDERE: la MISURA delle promesse resta al LORDO — al giudice
  `statoScontoPacco` e ai due inviti va il totale così com'è, la
  regola del server («LA MISURA È IL LORDO»), o lo sconto si
  spegnerebbe da solo facendo scendere il totale sotto la soglia che
  l'ha acceso — e il netto è solo RESA, con la formula del server
  (`_sconto_pacco`: floor sul netto, il sat di dubbio a chi paga).
  L'onestà è quella del ✅ che c'era già: stesso scatto, stessa
  fascia dichiarata del cambio a soglia in euro — il netto la
  eredita e non ne aggiunge una sua; l'ordine nasce sempre dal conto
  del server. Il preventivo a ogni tocco dello stepper resta
  SCARTATO (il debounce litiga con chi sale in fretta), e resta vero
  che quel numero non è il totale da pagare (niente spedizione né
  protezione): a cambiare è solo che ora dice la merce al prezzo
  VERO. Cassetto «🎁 Sconto sul carrello» nel Profilo fra
  spedizioniere e ferie (due politiche sempre accese, poi
  l'interruzione): pillole dalle liste del server, e le pillole
  SCELGONO mentre a salvare è un bottone solo — soglia e percentuale
  sono UNA regola, e con un POST per tocco esisterebbe il mezzo
  secondo in cui il negozio ne ha una a metà, e in quel mezzo secondo
  qualcuno può comprare. Col criterio (ago 2026) in testa ci sono due
  pillole «A pezzi / A valore» e sotto cambiano le soglie, che dal
  passaggio all'euro sono pillole in EURO e basta: sono spariti il
  campo d'aiuto, i due `*DaEuro` e gli `≈` sulle pillole — con loro se
  n'è andato anche il difetto dell'≈ che spariva sulla pillola accesa,
  e al loro posto c'è `NOTA_SOGLIA_EURO` (vedi sopra). La bozza si butta a ogni `/api/me` (o
  resterebbe quella fissata da un render girato prima che la regola
  vera arrivasse: bug visto dal vivo). Il 400 si rende DENTRO il
  cassetto, la ricetta delle ferie. Più la riga nell'ORDINE, che non è
  opzionale: le righe lì sono LORDE, e senza la cifra del risparmio il
  compratore rifà la somma e conclude di essere stato derubato.
  In DEMO non si simula nulla (il carrello lì non esiste) e il ramo
  `totaleSet()` resta ASCIUTTO apposta: è l'unico posto dove un
  calcolo client sul denaro potrebbe filtrare se un giorno il gate
  della DEMO si spostasse.
  LA SPEDIZIONE GRATIS SOPRA SOGLIA 🚚 (ago 2026, richiesta dal campo
  subito dopo lo sconto: «si può fare come negli e-commerce?»): «da N
  € di articoli la spedizione la offro io», una regola per tutto il
  negozio. Soglia in EURO — le ragioni del rovesciamento sono quelle
  dello sconto, per intero, e vale per tutte e due o non varrebbe per
  nessuna. `_sped_gratis` resta pura: riceve gli euro da
  `_eur_interi`, non va a prendere il cambio.
  NON È UNA COPIA DELLO SCONTO, E LA DIFFERENZA È DI FORMA: lo sconto
  sottrae dal TOTALE come voce di testata, la spedizione gratis
  AZZERA UNA TARIFFA — scrive `spedizione_sats=0`, cioè lo stato che
  ogni annuncio con tariffa gratis dichiarata (e ogni ritiro) ha da
  sempre. (Fino al 12 ago 2026 la forma decideva anche il perimetro:
  il mono non scontava perché uno sconto di testata rompeva la
  divisione a ritroso di `_righe_ordine`, mentre questa valeva anche
  sul singolo; da quando la divisione riaggiunge `sconto_sats` le due
  promesse hanno lo stesso perimetro.) La divisione a ritroso resta
  esatta per costruzione, senza un ramo nuovo. Stessa verifica
  sull'uscita dei sats: il venditore incassa `prezzo_sats −
  protezione_sats`, quindi con la spedizione offerta incassa MENO — che
  è precisamente cosa vuol dire offrirla.
  LE DUE PROMESSE GUARDANO LO STESSO NUMERO (decisione di Andrea):
  l'articolo LORDO, dopo lampo e accordo e PRIMA dello sconto carrello.
  Così sono INDIPENDENTI — nessuna può spegnere l'altra facendo cadere
  l'altra sotto la sua soglia — e si spiegano a chi compra in una riga
  sola. C'è la prova apposta, e sceglie i numeri per il caso che
  smaschera una dipendenza: lordo 105.000 sopra entrambe le soglie, ma
  NETTO 94.500 sotto quella della spedizione — se un domani la
  spedizione misurasse il netto, quel carrello perderebbe la gratuità e
  la riga diventerebbe rossa. Come per lo sconto, una lampo generosa
  può far scendere sotto soglia (dichiarato, detto al venditore nel
  cassetto, con la sua prova).
  MODELLO: `utenti.sped_gratis_soglia_eur` (0 = spenta) — UNA colonna,
  niente criterio (il criterio È il valore) e niente percentuale
  (gratis è gratis) — più `ordini.sped_gratis_sats`, la tariffa che il
  compratore NON ha pagato. Quella è una **colonna TESTIMONE, NON UN
  MOTORE**, e vale parola per parola l'avvertimento di `sconto_sats`:
  `prezzo_sats` nasce già senza la spedizione, e un
  `netto_venditore(prezzo + sped_gratis_sats)` farebbe uscire
  dall'escrow DI ALTRI ORDINI la differenza senza che la cintura di
  `paga_venditore` se ne accorga (per lei dovuto e bolt11
  combacerebbero). Sentinelle apposta sulle tre strade d'uscita e sul
  CSV. A differenza dello sconto qui l'aritmetica quadrerebbe anche
  senza la colonna (spedizione 0 è tutta la verità del conto): serve a
  RACCONTARE — chi ha visto un costo nella scheda deve poter capire
  dove è finito — e a dare al libro mastro due invarianti veri.
  Giudici: `_sped_gratis(articolo, soglia)` fra le pure del conto (al
  filo esatto è GRATIS, come `_asta_viva` e `in_ferie`) e
  `_regola_sped_gratis(soglia)` fuori, che guarda le leve. NON esiste
  il gemello di `_sconto_pubblico`, e non è una dimenticanza: quello
  serve alla regola d'oro del client vecchio che di quattro campi ne
  legge uno — qui il campo è UNO e un client di ieri non lo conosce
  affatto, quindi non disegna niente, che è un'assenza e non una bugia.
  DOVE SI DECIDE, ed è il vincolo: nello STESSO punto logico nei
  quattro percorsi (`compra` mono, `_compra_set`, i due preventivi) —
  DOPO che la tariffa è stata contata, subito prima di `_conto_ordine`.
  Se il preventivo decidesse prima, la pagina direbbe «gratuita» dove
  la invoice risponde 503, e «preventivo == compra al sat» è il patto
  che regge la pagina d'acquisto. IMPERFEZIONE DICHIARATA che è il
  prezzo di questa scelta (decisione di Andrea): una tariffa ancorata
  all'EURO col cambio muto ferma la strada — 503 nel mono,
  `cambio_assente` nel preventivo — anche quando la spedizione sarebbe
  gratis. Serve tariffa-in-euro + CoinGecko giù + carrello sopra
  soglia: rara e transitoria, e il verso in cui sbagliare è quello di
  non far partire un ordine, mai quello di farne partire uno sbagliato.
  LA STRADA SCARTATA, e va tenuta perché torna in mente: decidere
  PRESTO, riordinando `compra()` e `_compra_set` così che una tariffa
  che non si paga non venga nemmeno convertita. Chiude il caso e
  semplificherebbe pure i due rami del cambio del mono, che oggi si
  sovrappongono — ma è chirurgia sul percorso dei soldi per un caso
  transitorio. Se le tariffe in euro diventassero la norma, è lì la
  leva.
  SUPERFICIE: `u.sped_gratis_soglia_eur AS venditore_sped_gratis_eur` in
  `CAMPI_VETRINA` a costo ZERO (il JOIN su `u` c'era già) e
  normalizzata in `arricchisci_righe_vetrina`, così la leva spenta la
  spegne in tutte le vetrine insieme; `sped_gratis_eur` nel profilo
  di `/api/negozio`; `sped_gratis_leve` in `/api/me` (il valore salvato
  esce GREZZO di proposito: è il suo negozio, deve vedere cosa ha
  scritto). Il preventivo porta `sped_gratis_eur`,
  `mancano_sped_eur` (che conta il SERVER anche se il client
  potrebbe: è il numero dove vive un off-by-one, la lezione di
  `mancano_pezzi`) e `sped_gratis_sats` dentro ogni strada casa/punto —
  che è anche ciò che rende la prova regina verificabile. Zero query in
  più: le due SELECT del venditore c'erano già; solo `compra` mono ne
  aggiunge una (lettura, prima della invoice, nessun DML — il vincolo
  del ricontrollo resta intatto).
  ENDPOINT `POST /api/me/spedizione-gratis`, il pattern dello sconto ma
  molto più corto: `soglia <= 0` è lo SPEGNIMENTO e non ha nessuna
  guardia; niente `_impegni_aperti` e niente `guardia_ferie_venditore`,
  per le due ragioni scritte per esteso nello sconto. LEVE:
  `SPED_GRATIS_ATTIVO` nasce ACCESA (non muove denaro verso l'esterno,
  abbassa un conto in entrata), `SPED_GRATIS_SOGLIE_EUR` le pillole,
  `SPED_GRATIS_MIN_EUR` 1 la cintura — più le gemelle `*_SATS` da
  quando la valuta si sceglie. ⚠️ LE LEVE-LISTA sono ormai OTTO
  (`SPED_GRATIS_SOGLIE_EUR` e `_SATS`, `SCONTO_PACCO_VALORI_EUR` e
  `_SATS`, `SCONTO_PACCO_SOGLIE`, `SCONTO_PACCO_SCONTI`,
  `SCONTO_PACCO_CRITERI`, `VALUTE_SOGLIA`): la prova del censimento in
  `prove.py` va aggiornata a mano, e chi ne aggiunge una senza farlo non
  vede una prova rossa ma la suite che ESPLODE (`_elenco(7)` su un
  intero) — è esattamente il modo in cui ci si inciampa.
  IL LIBRO MASTRO guadagna DUE controlli, e li apre la colonna
  testimone: «spedizione risparmiata e pagata insieme»
  (`sped_gratis_sats>0 AND spedizione_sats>0`) e «spedizione
  risparmiata dove non si spediva» (via ritiro/digitale). Superano
  tutti e due la domanda che decide — «esiste uno stato transitorio
  legittimo in cui sono false?» — perché le due colonne si scrivono
  nello stesso INSERT e si escludono per costruzione. NON c'è il
  gemello di «promessa che non può scattare»: lì il criterio poteva
  finire fuori catalogo, qui c'è un intero ≥ 0 dove 0 significa
  «spenta» — non esiste un valore rotto da trovare, e un allarme che
  non può suonare è peggio di nessun allarme. I quattro controlli
  sull'aritmetica NON cambiano di un carattere, ed è la prova che
  questa funzione non tocca il denaro; il polso guadagna chi promette
  la spedizione e da che soglia, accanto a chi sconta.
  CLIENT: le pillole delle vie dicevano GIÀ «gratuita» a costo zero
  (zero righe). `contoRighe` guadagna il flag `spedGratis` e con lui la
  riga dice «gratuita» invece di «0 sats» — ma solo su una via che
  SPEDISCE, e la stessa regola copre anche la tariffa dichiarata a zero
  dal venditore: un caso solo, nessun ramo per la funzione nuova (il
  ritiro continua a dire 0, che lì non c'è nessuna spedizione da
  offrire). La parola vuole `.ctrl-riga .via-gratis`, o dentro lo
  `.mono` della colonna delle cifre verrebbe scritta come un numero.
  Giudice unico `regolaSpedGratis` e frase unica
  `frasePromessaSpedGratis`, per la ragione delle gemelle dello sconto.
  TRE righe pubbliche — testata negozio, «Altri oggetti», e (la novità)
  la SCHEDA DELL'ANNUNCIO, che lo sconto non ha perché nel mono non
  esiste e questa sì. La riga della scheda DICE LA REGOLA, MAI UN
  VERDETTO SU QUELL'OGGETTO, ed è il punto dove è più facile scivolare:
  verrebbe da scrivere «questo è già sopra soglia» leggendo il prezzo
  accanto, ma quel prezzo non è il numero che il server confronta — una
  lampo viva, un accordo accettato o la quantità scelta lo spostano, e
  la riga direbbe una cosa che il conto poi non fa. Fuori in due casi:
  annuncio che NON spedisce, e spedizione già gratis SENZA condizioni
  (lì la pillola lo dice meglio, e una soglia accanto farebbe dubitare
  di una gratuità che è piena). Mai in card, e MAI FRA LE PILLOLE COL
  NUMERO — la regola tiene, e ha resistito a un giro che l'aveva
  rovesciata per un giorno: ad ago 2026 la promessa scritta è entrata
  nel badge e ne è subito riuscita, perché «da 200 €» accanto al prezzo
  dell'articolo si legge come una proprietà di quell'articolo anche
  quando si nomina «di articoli». Quel che nelle pillole c'è adesso è
  un ESITO senza cifra («Spedizione gratuita»), che è un'altra cosa —
  vedi «LE PROMESSE DIVENTANO BADGE». Più l'INVITO nella
  pagina Paga («Ancora N sats e la spedizione è gratis»), che si
  TRASFORMA in conferma invece di sparire (la lezione dell'invito dello
  sconto) e non calcola, riceve — ed è il posto unico e giusto, perché
  di lì passano sia il pezzo singolo sia il carrello; e la riga nella
  RICEVUTA dell'ordine, che dice quanti sats il venditore ha offerto.
  Cassetto «🚚 Spedizione gratis» fra «📦 Come spedisci» e «🎁 Sconto
  sul carrello»: il calco del gemello. Anche qui le pillole SCELGONO e
  a salvare è il bottone — questa riga per un po' ha detto il contrario
  («le pillole salvano davvero, che il numero è UNO»), ed era già stale
  col campo libero: con due modi di dire lo stesso numero un
  salvataggio per tocco lascerebbe il campo indietro, e dalla scelta
  della valuta i numeri da tenere in pari sono due (la soglia e la sua
  unità), cioè lo stesso mezzo secondo con una regola a metà che nello
  sconto è il motivo del bottone unico.
  LE PROMESSE DIVENTANO BADGE (ago 2026, decisione di Andrea): le due
  righe di prosa grigia passano a PILLOLE su tre superfici — scheda
  annuncio, «Altri oggetti», carrello. Erano righe che si leggono una
  volta e poi si smette di vederle, e soprattutto NON SI MUOVEVANO
  mentre il carrello cresce: non dicevano mai «ci sei quasi».
  NELLA SCHEDA IL BADGE HA DUE STATI E NON NOMINA LA SOGLIA: sopra
  soglia «🚚 Spedizione gratuita» — che RIUSA lo stato dei negozi che
  spediscono gratis senza condizioni, non uno stato nuovo — e sotto
  «🚚 Spedizione disponibile», nudo. Il «quanto manca» si legge dopo,
  quando si compone l'ordine (carrello e pagina Paga, dove c'è già), e
  la promessa COL NUMERO resta in «Altri oggetti», che parla del
  NEGOZIO e sta accanto al bottone del carrello.
  CI SI È ARRIVATI IN DUE GIRI, e il primo va tenuto perché è l'errore
  che torna in mente: per un giorno la promessa SCRITTA è stata dentro
  il badge («Spedizione gratis da 200 € di articoli»), col
  ragionamento che l'equivoco si toglie NOMINANDO — «di articoli»
  distingue il totale della merce dal prezzo che si ha davanti. Non
  basta: accanto al prezzo dell'articolo quella cifra si legge lo
  stesso come una proprietà di quell'articolo. E su un pezzo che la
  spedizione gratis ce l'ha già, dirla condizionata è una promessa più
  povera del vero. Quindi la regola «mai una CIFRA fra le pillole»
  tiene; quel che è cambiato è che adesso il badge dà un ESITO.
  IL VERDETTO SI PUÒ DARE PERCHÉ QUI IL CLIENT IL CONTO LO CONOSCE, ed
  è la sola cosa che rende lecito il rovesciamento: sul mono l'articolo
  è `artStima × pezzi`, e `artStima` è il gemello di
  `_unitario_effettivo` del server (il MIN fra lampo e accordo). Il
  giudice è `spedGratisQui(l, qta)`, e le sue tre decisioni (Andrea):
  1) LA CIFRA È QUELLA DEL SERVER, quindi DOPO lampo e accordo.
  Conseguenza accettata, la stessa già dichiarata per lo sconto: una
  lampo generosa può far scendere sotto soglia e TOGLIERE la spedizione
  gratis — corretto, e il caso che sembra un bug a chi lo nota.
  2) A CAMBIO MUTO SI TACE, cioè «disponibile», e non è prudenza: senza
  cambio il server la promessa non la applica affatto
  (`promesse_sospese`) e la spedizione si paga, quindi è la risposta
  VERA. Una riga sola da dire a voce — serve il cambio A MENO CHE
  soglia e listino siano tutti e due in sats — che copre anche il
  listino in EURO, portato in sats da `satsAnnuncio` col cambio (senza,
  userebbe quello di PUBBLICAZIONE, vecchio di mesi). Un filo
  conservativa su soglia-euro + listino-euro: si preferisce una regola
  a una matrice di quattro caselle, e sbaglia nel verso di non
  promettere.
  3) LA QUANTITÀ È QUELLA DELLO STEPPER, perché è quella che il server
  misura — e il badge si riscrive in `setQta`, dove già si riscrivono
  le cifre di Acquista e l'etichetta del tasto offerta. Si riscrive il
  CONTENUTO (`testoSpedBadge`, agganciato da `data-sped`) e non il
  guscio, o il nodo sparirebbe da sotto i piedi al giro dopo.
  AL FILO ESATTO È GRATIS, come `_sped_gratis` del server. IN FERIE
  nessun verdetto (lì non si compra, non c'è un conto con cui essere
  d'accordo), mentre la gratuità PIENA resta visibile anche in ferie:
  quella è una proprietà dell'annuncio, questo è un verdetto su un
  acquisto.
  IN «ALTRI OGGETTI» L'ORDINE È TITOLO → BOTTONE → BADGE, COL BLOCCO
  BOTTONE+BADGE APPICCICATO (13 ago 2026, TERZA rigirata chiesta da
  Andrea — e stavolta È PASSATA, perché il verbale chiedeva «un
  meccanismo nuovo» e il meccanismo c'è: la fila a RIGHE PIENE).
  LA STORIA INTERA, che è il modello di come si rigira una decisione
  misurata: i badge nacquero SOPRA il bottone perché sotto si
  SPEZZAVANO — il bottone è `position:sticky` col fondo opaco e li
  mangiava UNO ALLA VOLTA, a 90px di scroll restava la sola
  spedizione — e la strada «dentro `.altri-azione`» era stata
  scartata coi numeri: coi CHIP che vanno a capo il cartello fisso
  passava da 84 a 178px, il 23%, giudicato troppo. La seconda
  rigirata (12 ago) fu costruita, rimisurata e RITIRATA da Andrea
  davanti agli stessi numeri, col verbale «non rigirare una terza
  volta senza un meccanismo nuovo». Le righe piene SONO il
  meccanismo: in colonna non vanno mai a capo, e DENTRO il blocco
  appiccicato la coppia non può spezzarsi per costruzione —
  RIVERIFICATO a metà scorrimento su 320/360/375: due badge su due,
  interi, sempre.
  IL COSTO, MISURATO E DETTO COL NUMERO IN DUE TEMPI (la condizione
  posta da Andrea): alla nascita il blocco ancorato faceva **180px
  (24%) con due promesse** — due px sopra i 178 scartati allora —
  riportati col numero e ACCETTATI (le righe si leggono invece di
  essere chip accalcati, e i badge si vedono tutti e due a ogni
  scorrimento, che era il difetto d'origine), con la richiesta di
  stringere i SOLI respiri se si trovavano senza toccare la veste.
  Trovati — padding del blocco 10→8, margine dei badge 8→6, mai il
  gap della fila che è della veste — e il blocco fa **176px (23%)
  misurati**, con l'aria guardata a schermo prima di tenerla; 135 e
  84 (una promessa / nessuna) scendono degli stessi 4px; identico
  alle tre larghezze, perché le righe piene non vanno a capo. Se il
  numero un giorno non reggesse ancora, di respiri onesti ne restano
  pochi: la leva successiva è una decisione, non un ritocco.
  IL TITOLO STA SU UNA RIGA, E IL DIFETTO ERA PREESISTENTE (13 ago
  2026, dal campo: col gradino a 13px «Altri oggetti di questo
  venditore» andava a capo). MISURATO prima di scegliere, ed è la
  misura che ha deciso: a 320 quel testo andava a capo **anche agli
  11px di serie** (250px di testo contro 246 di budget) — il gradino
  non ha creato niente, ha solo reso visibile una cosa che c'era, e
  «tornare al corpo di prima» non sarebbe stata una cura. Anche a
  375 il 13px ci stava con 5px di puntini, cioè con la linea
  praticamente sparita. LA CURA HA DUE GAMBE, tutte e due dentro le
  leve concesse da Andrea («un corpo più piccolo, meno spazio ai
  lati, o una formula più corta»): 1) il PADDING LATERALE DOPPIO
  tolto — `.section-label` porta il suo `var(--pad)` perché di
  solito vive attaccato al bordo della vista, ma dentro
  `.detail-body` quel padding c'è già e i due si sommavano: il
  titolo rientrava di 16px rispetto a bottone e card, e toglierlo
  ALLINEA la colonna (left 32 → 16, verificato uguale ai tre) oltre
  a restituire 32px; 2) la FORMULA PIÙ CORTA, «Altri oggetti del
  venditore» — via il solo «questo», l'informazione resta intera.
  Risultato misurato: una riga a 320/360/375 nei due temi, con 36 /
  76 / 91px di linea puntinata. IL TESTO INTERO A 13px NON CI STA a
  320 in nessun modo onesto: nemmeno senza padding (296 contro 278),
  e le vie che lo farebbero entrare mangiano il letter-spacing del
  maiuscoletto (a `normal` entra, ma quel `.1em` è il tratto di
  famiglia di TUTTI i section-label) o riportano il corpo a 11,5px,
  cioè annullano il gradino. Col giro è cresciuto il TITOLO
  della sezione (`.altri-tit`, 13px contro gli 11 del section-label
  di serie). LA LEZIONE di ieri resta vera dove è nata: **contenuto
  corto e ATOMICO non va messo sotto un elemento sticky** — dentro,
  o sopra; sotto viene mangiato un pezzo alla volta.
  L'ORDINE DELLA FILA È UNO SOLO (12 ago 2026, decisione di Andrea):
  🚚 PRIMA della 🎁, ovunque le due promesse compaiano insieme —
  pagina Paga (dove la fila sta anche SOPRA la riga della consegna),
  «Altri oggetti», carrello e testata del negozio, che era il quarto
  posto e l'ha trovato il censimento: l'occhio impara UNA fila, e una
  superficie che la rovescia gliene fa trovare un'altra. In
  `renderAcquisto` i BLOCCHI sorgente restano sconto-poi-spedizione
  (le prove li affettano coi marcatori dei commenti): l'ordine reso
  lo decide la sola composizione `pillaSg + pillaSc`, e cinque
  sentinelle tengono fila, posizione e le quattro superfici. Chi
  aggiunge una QUINTA superficie con le due promesse la mette in
  quell'ordine e nel conto delle sentinelle. (In Paga, dall'ago 2026,
  sulla via ritiro/digitale la 🚚 può MANCARE per il gate della via —
  vedi la voce dell'invito: è la pillola che tace, mai la fila
  rovesciata.)
  NEL CARRELLO il badge porta il CONTO VIVO — «🚚 Ancora 145 € →
  spedizione gratis», «🎁 Ancora 2 pezzi → −15%» — e quando la soglia
  scatta diventa la conferma, dal 13 ago 2026 NUDA e piena e accesa
  come in Paga: la coda «nel conto» è morta col totale che mostra lo
  scontato (vedi la voce della barra del carrello), e i badge corrono
  la stessa barra col viraggio, sui ferri condivisi.
  IL VERDE VIVE SOLO DOVE LA PROMESSA È UN FATTO — carrello e Paga,
  le due superfici che emettono `pill-trust`, e dal 13 ago è l'ACCESO
  `--barra-a` sulla base `.pill.pill-trust` (il tenue di
  `.trust-note` non lo veste più nessuno: due traguardi diversi per
  la stessa promessa erano una divergenza senza motivo).
  In scheda e in «Altri oggetti» i badge restano NEUTRI, perché lì la
  promessa è una REGOLA e non un fatto compiuto; e nella fila del
  dettaglio il verde è già preso da `cond-nuovo`/`cond-come_nuovo`, che
  vuol dire un'altra cosa. E dal 13 ago 2026 anche i badge di «Altri
  oggetti» vestono `.fila-promesse` — righe a tutta larghezza come in
  Paga: SOLO la veste, niente barra e niente verde, perché lì non c'è
  una soglia da riempire (non è un verdetto sul carrello corrente);
  il costo dichiarato è che i due stanno sempre uno sotto l'altro —
  e dal terzo giro dello stesso 13 ago vivono DENTRO il blocco
  appiccicato, sotto il bottone: la storia e i numeri stanno nella
  voce «IN "ALTRI OGGETTI" L'ORDINE È TITOLO → BOTTONE → BADGE».
  DUE FUNZIONI E DUE SCATOLE nel carrello (`aggiornaInvitoSconto` e
  `aggiornaInvitoSpedGratis`, `#paccoSconto` e `#paccoSpedGratis`), e
  non è simmetria per il gusto: le due soglie hanno UNITÀ INDIPENDENTI
  — un negozio può promettere lo sconto in euro e la spedizione in
  SATS. Con una funzione sola il `return` di `!cambioVivo`, deciso
  dallo sconto, spegnerebbe anche un badge che di cambio non ha
  bisogno; e un `box.innerHTML=''` su un contenitore condiviso
  cancellerebbe la sorella. Il respiro sta sui FIGLI e non sul
  wrapper: a carrello vuoto sono tutti e due `display:none` e la fila
  non produce un pixel. Guardia in più sulla spedizione: un carrello di
  soli RITIRI non ha una spedizione da rendere gratis
  (`stradeSet().includes('spedizione')`), e la guardia va DOPO quella
  del vuoto — a carrello vuoto `stradeSet()` non filtra niente e messa
  sopra sarebbe vacuamente vera.
  LA CIFRA HA UN GIUDICE SOLO, `cifraSoglia(quanto, valuta)`: la prosa
  lunga e l'etichetta corta restano DUE funzioni (sono due registri, e
  derivare l'una dall'altra sarebbe chirurgia di stringhe su HTML), ma
  quello che non deve poter divergere non sono le parole — sono la
  cifra e la sua unità, che erano scritte a mano in sette posti e coi
  badge sarebbero diventate dieci. Porta anche il nowrap, che SI METTE
  SULLA CIFRA E MAI SULLA PILLOLA: misurato, «🚚 Spedizione gratis da
  25 € di articoli» fa ~293px contro i 288 disponibili a 320px, e un
  flex item con nowrap non scende sotto il min-content — farebbe
  scorrere di lato la PAGINA.
  DUE TESTI che dal 12 ago 2026 parlano UGUALE (il mono sconta, e
  l'asimmetria che qui era «voluta» non esiste più): «nel carrello» è
  morto in tutte e due le famiglie di testi — era la parola che
  restringeva, è diventata la parola che mente. E NELLE ETICHETTE dei
  badge è morto anche «DI ARTICOLI» (12 ago 2026, decisione di
  Andrea): «🎁 −15% da 25 €» e «🚚 Spedizione gratis da 25 €», la
  cifra e basta — le etichette vivono SOLO in «Altri oggetti», che
  parla del NEGOZIO, e lì l'equivoco col prezzo dell'oggetto non
  esiste. La parola RESTA dove è una parola di MISURA e non un
  ornamento: le prose lunghe (testata negozio e hint del form Vendi,
  che stanno accanto a un prezzo vero), le righe della pagina Paga
  (dove c'è un «Totale da pagare» a un centimetro) e l'anteprima del
  cassetto — in tutti quei posti distingue la merce dal totale con la
  spedizione dentro, ed è per questo che non si toglie ovunque per
  simmetria. C'è la sentinella nei due versi.
  NEL CARRELLO IL CONTO È DEL CLIENT, come già prima: i badge non
  calcolano, RICEVONO il totale che la barra mostra due centimetri più
  sotto, quindi i due non possono divergere (a calcolare, dal 13 ago,
  è solo il TOTALE della barra: il netto a soglia scattata, formula
  del server, vedi la voce sua). L'imperfezione è quella
  già dichiarata (solo a soglia in EURO si converte col cambio del
  client, e senza cambio si tace — e allora niente badge, niente
  barra e niente netto insieme); a soglia in SATS il confronto è
  esatto e il badge compare anche a CoinGecko muto.
  NEL FORM VENDI DUE RIGHE DELLE POLITICHE (ago 2026, chieste da
  Andrea): lo sconto sotto il Prezzo, la spedizione gratis sotto il
  Costo di spedizione. Non sono informazioni sul negozio, sono
  AVVERTIMENTI SUL NUMERO CHE SI HA SOTTO LE DITA — «questa cifra in un
  carrello scenderà del 15%», «sopra soglia questo costo lo metti tu».
  Andrea ha chiesto di valutare se UNIRLE in una riga sola quando sono
  tutte e due accese: SCARTATO, e le tre ragioni valgono più della
  decisione — 1) parlano di due CAMPI diversi, e una riga sola starebbe
  accanto a uno solo dei due, cioè fuori posto per l'altro, perdendo
  proprio ciò che le rende utili; 2) non compaiono quasi mai insieme,
  perché il campo del costo esiste solo con la spedizione spuntata e
  mai in asta, mentre il Prezzo c'è sempre — quindi la riga unita
  dovrebbe vivere sul Prezzo e parlare di un campo che spesso non è
  nemmeno a schermo; 3) è il pattern degli hint contestuali di casa (la
  riga «nessuno può scriverti» sopra Pubblica, quella dello
  spedizioniere accanto alla tariffa punto): la riga nasce dove nasce
  il dubbio. Il peso resta basso perché ognuna è UNA frase e compare
  solo a regola accesa. Scrittore unico `aggiornaHintPolitiche`,
  chiamato all'ingresso in Vendi (fra un ingresso e l'altro il
  venditore può essere passato dal Profilo a cambiarle) e dopo ognuno
  dei due salvataggi; la riga della spedizione vive DENTRO
  `#sellSpedField` e si nasconde da sola col suo campo.
  LA RONDA DEL LIBRO MASTRO (ago 2026): gli invarianti già dichiarati
  in questo file diventano un controllo dell'orologio invece di query
  da lanciare a mano — perché un controllo che dipende da qualcuno che
  si ricorda di lanciarlo è un controllo che un giorno non gira (la
  lezione del termometro delle sottocategorie). Catalogo
  `CONTROLLI_LIBRO_MASTRO` (nome, perché, SQL) + `controlla_libro_
  mastro()` in coda all'orologio.
  LEGGE E BASTA, ed è la regola: nessuna correzione automatica, mai —
  una macchina che «aggiusta» i conti nasconde la causa, e la seconda
  volta non se ne accorge nessuno. Una prova asserisce che nel
  catalogo non compaia un solo INSERT/UPDATE/DELETE.
  A LIBRO MASTRO SANO NON DICE NIENTE, nemmeno una riga nel journal:
  un «tutto bene» quotidiano è rumore, e il rumore è il modo in cui
  gli allarmi muoiono. Quando qualcosa non torna manda il 🧊 ai
  moderatori col nome del controllo, il perché e gli id (tetto di 10,
  poi «+N altri»: in chat deve restare leggibile, e per guardarli
  tutti c'è lo strumento a mano).
  IL TIMBRO È IL GIORNO e si scrive PRIMA delle query (il patto delle
  campagne, ma qui la ragione è sua): senza, l'allarme tornerebbe a
  ogni battito — 144 volte al giorno — e in una settimana nessuno lo
  leggerebbe più. STA NELLA TABELLA `timbri` dall'ago 2026: era in
  memoria, e qui c'era scritto che il prezzo era «al più un avviso
  doppio nello stesso giorno» — falso, era uno PER DEPLOY. Su un
  libro mastro sano non si vedeva (a database sano questa tace); si
  sarebbe visto l'unico giorno in cui parla, cioè quello in cui
  qualcosa non torna e qualcuno sta deployando per ripararlo.
  Una query che ESPLODE conta come un controllo fallito: se lo schema
  è cambiato sotto, è esattamente una cosa da sapere.
  QUALI INVARIANTI CI SONO (16, tutti già dichiarati altrove in questo
  file): l'aritmetica della testata col suo sconto e i suoi pezzi,
  l'aritmetica del MONO (la divisione a ritroso che si divide esatta —
  dal 12 ago 2026 ha preso il posto di «mono scontato», morto col
  rovesciamento: sarebbe un falso allarme su ogni ordine legittimo),
  gli sconti fuori scala nei due gusti (set e testata mono) e la coppia
  sconto/percentuale; la forma di `ordine_righe` (mono con righe,
  righe orfane, carrello senza merce); l'asta — la cassa della chiusa
  (Σ saldi = esposto della vincitrice + registro), la puntata chiusa
  senza rimborso, `versato >= offerto`, i doppi rimborsi da ritiro e
  la PRESENZA dei quattro indici UNIQUE parziali (non è un dato
  sbagliato: è la cintura caduta, e il prossimo crash a metà chiusura
  pagherebbe due volte); più l'annuncio a due teste (`contatto_nostr`
  e `nostr_event_id` insieme) e il dominio di `payout_stato`.
  QUALI RESTANO FUORI, ed è la parte da non rovesciare: la domanda che
  decide è «esiste uno stato TRANSITORIO LEGITTIMO in cui è falsa?»,
  perché un allarme che suona su un caso normale è peggio di nessun
  allarme — educa a ignorarlo. Quindi NON entrano: «venduto <=>
  quantita=0» (un venduto poi RIMOSSO resta a (rimosso, 0)
  legittimamente e suonerebbe per sempre), `payout_stato='incerto'`
  (non è un guasto: è la coda che aspetta un moderatore, cioè il
  funzionamento previsto), e «una fattura pendente alla volta» (due
  rilanci 'creato' sono leciti finché il reaper non passa: finestra
  mobile). La cassa dell'asta è ancorata a `stato='vincitrice'` per la
  stessa ragione: aste vive, deserte e annullate non hanno una
  vincitrice e restano fuori da sole.
  Leva `CONTROLLO_LIBRO_MASTRO` (True di serie: non muove niente,
  legge). Lo strumento a mano resta nel repo — `query_libro_mastro.sql`,
  le stesse 15 query più il POLSO che l'orologio non racconta perché
  non è un allarme (chi sconta, gli ordini scontati, i pagamenti
  congelati e da quanto) — e l'avviso lo nomina.
  IL PANNELLO ADMIN TIENE APERTO SOLO CIÒ CHE ASPETTA (ago 2026): le
  voci GIÀ DECISE stavano mescolate alla coda della revisione, e il
  registro di moderazione — che è storia per definizione — stava
  aperto sempre. Ora `cassettoAdm` (il pattern `.acc` del Profilo,
  `#adminStats .acc{margin-top:22px}` perché qui i cassetti stanno in
  fila con dei section-label) tiene chiusi «↩︎ Decisi di recente» e
  «🛡 Registro moderazione»; nel DATABASE non si tocca niente, cambia
  la sola vista. Misurato a 375px: il pannello passa da 2600 a 1529px.
  IL CENSIMENTO DELLE ALTRE CODE, che è la parte da non rifare: le
  altre tre — 🧊 pagamenti incerti, ⏳ in revisione, 🗂 categorie —
  sono TUTTE in attesa di una decisione e restano aperte; le dispute
  non sono una coda di questo pannello (vivono negli Ordini); statistiche
  e lista utenti non sono code ma il fondale su cui si decide, e la
  lista è pure il motore della ricerca di «Scrivi a un utente».
  I cassetti NASCONO CHIUSI ma RESTANO come li lasci (`accAdmAperti`,
  un Set che parte vuoto — e quello È il «chiuso di serie»): il
  pannello si ridisegna INTERO a ogni decisione, e senza memoria si
  richiuderebbe sotto le dita di chi sta sistemando il secondo
  sbaglio. La conta del registro dice «ultime 20 di N» e non «20
  righe», che di un append-only sarebbe falso — per questo
  `/api/admin/stats` porta `moderazione.registro_totale`.
  LO STATO DELLE LEVE (ago 2026, nato da «è già successo di ricordare
  male»): `GET /api/admin/leve` (solo moderatori) + cassetto
  «⚙️ Stato delle leve» in fondo al pannello — 69 leve in 12 gruppi
  col valore con cui il processo sta girando ADESSO. Si leggono i
  GLOBALI del modulo, cioè il valore già risolto fra la riga del
  config e il default del codice: un elenco dei default sarebbe una
  seconda bugia da leggere, ed è la trappola di MAX_PREFERITI.
  SI GUARDA E BASTA — nessuna rotta che scrive, e non è pigrizia:
  ASTA_ABILITATA, IMPORT_NOSTR_APERTO e AUTO_SBLOCCO_ATTIVO nascono
  spente nel codice perché accenderle costi un gesto, e una leva che
  si accende da un telefono è una leva che si accende per sbaglio.
  I SEGRETI NON ESCONO MAI (chiavi LNbits, token del bot, nsec,
  segreto del webhook, id del canale, percorso del DB, id dei
  moderatori — di cui esce il CONTEGGIO). Dove il segreto È
  l'interruttore esce il solo FATTO, chiesto alla stessa guardia che
  usa il server (`_NOSTR is not None`, `webhook_attivo()`): rispondono
  «funziona?», che è la domanda giusta e non rivela niente. Il NOME
  della chiave invece esce apposta — serve per andarla a cambiare, ed
  è in chiaro in config_esempio.py. Fuori dal censimento, dichiarato:
  i segreti di cui sopra, MODELLO_RICERCA (una stringa, non una leva)
  e NPUB_VENDITORE/VENDITORE_ID, che sono di importa_nostr.py lanciato
  a mano e non del server.
  Due cose tengono la pagina leggibile invece che un muro: `_leva`
  mostra la nota «cosa comporta» SOLO nello stato che la merita (11
  righe su 69 oggi — settanta spiegazioni in fila non le legge
  nessuno), e l'ALLARME è un'altra cosa dalla nota — il valore che fa
  paura non è sempre lo stesso (MODALITA_COLLAUDO spaventa ACCESA,
  ORE_INITDATA SPENTA), quindi lo decide il chiamante. La conta sull'header lo dice a cassetto CHIUSO
  («⚠️ N da guardare»): un cartello che si vede solo aprendo un
  cassetto non lo vede nessuno. `prove.py` gira il censimento due
  volte — tutto acceso e tutto spento — con segreti riconoscibili in
  un config finto e li cerca nel JSON: aggiungere una leva non
  richiede di aggiornare la prova (le chiavi non dichiarate valgono 7;
  se la leva nuova è una LISTA la prova esplode e va aggiunta a mano).
  PER GLI UTENTI SI CHIAMA CARRELLO (ago 2026, decisione di Andrea):
  la parola «pacco» nei testi resta SOLO dove significa la spedizione
  fisica (taglia del pacco, «segui il pacco», «Spedisci il set (un
  pacco solo)») — il concetto-composizione parla «carrello» con
  l'icona 🛒 ovunque (che in card non compare mai: nessuna collisione
  con 🚚 🤝 💾; l'unico altro 🛒 del progetto è la notifica admin del
  bot, superficie diversa). La sequenza dei bottoni dice il flusso:
  «🛒 Aggiungi al carrello» → «Controlla e paga» (la barra: porta al
  riepilogo «Controlla il carrello» PRIMA di pagare) → «Paga». I NOMI
  INTERNI restano «pacco» (paccoDati, view-controllapacco, .pacco-*,
  le chiavi di navigazione…), dichiarato: rinominarli sarebbe un
  refactor di massa contro la regola dei diff piccoli, e il commento
  in testa ad apriPacco lo dice. Vale anche per lo SCONTO CARRELLO
  nato dopo (ago 2026): i testi verso gli utenti dicono tutti
  «carrello» — cassetto, invito, riga del conto, riga dell'ordine — e
  i nomi interni restano `sconto_pacco_*` (colonne, leve, endpoint,
  funzioni), che è la stessa famiglia. IL SOTTOTITOLO dice il
  PERIMETRO e non più il modello (12 ago 2026, decisione di Andrea:
  via «un venditore alla volta, spedizione unica»): «articoli dello
  stesso venditore» — è il carrello di QUEL negozio, non del mercatino
  intero; la spedizione unica la racconta già il riepilogo, che ha la
  sua riga. Resta vero il perché storico del niente-nome: «di
  {venditore}» davanti troncava la riga a 375px, e il venditore è già
  su ogni card e nel riepilogo. Il CAMBIO VENDITORE si DICE:
  apriPacco da un altro venditore con una spesa in corso svuota come
  sempre ma col toast «Carrello nuovo: è di un venditore alla
  volta…» — è il modello, non un errore, e in silenzio sembrava roba
  sparita (il toast tiene la frase del modello: lì È la spiegazione).
  LA TESTATA E I BADGE RESTANO IN CIMA (12 ago 2026, decisione di
  Andrea, MISURATA prima di lasciarla): `.pacco-appiccicato` — un
  blocco sticky solo con dentro testata («Il carrello» + ✕ + toggle)
  e la fila dei badge, così i numeri che cambiano a ogni «Aggiungi»
  restano sotto gli occhi mentre si scorre la griglia. UN blocco e
  non due: la coppia è atomica per costruzione, la lezione di «Altri
  oggetti». IL COSTO, misurato collo stato più alto (i due inviti
  lunghi): 137px a 375 (17% dello schermo) e 158px a 320 (19%) —
  sotto i 178px (23%) giudicati troppi in «Altri oggetti», e coi
  verdi o senza promesse il blocco scende da solo; qui in più il
  blocco è il quadro di lavoro della pagina, non un cartello sopra la
  merce di un dettaglio. La griglia sta FUORI dal blocco (le card
  devono passarci sotto), il fondo è pieno, e da desktop si ferma
  sotto la topbar come `.altri-azione`. Sentinelle su ordine del
  markup e sottotitolo.
  IL CARRELLO A UNA RIGA VA FINO IN FONDO (ago 2026, decisione di
  Andrea): «Controlla e paga» con un solo articolo non blocca più con
  l'invito a comprare dalla scheda. Il set a una riga resta
  INESISTENTE per il server (2..MAX_RIGHE_SET, in _compra_set E nel
  preventivo: guardia dei soldi, non si ammorbidisce) — la strada è il
  BINARIO MONO DIETRO LE QUINTE: `apriAcquistoSet` con una riga passa
  il testimone ad `apriAcquisto` (qtaScelta dal carrello, il passamano
  dello stepper del dettaglio) e da lì pagina Paga, ordine e invoice
  sono quelli di sempre — offerte, lampo, ripresa del pentito e NWC
  funzionano gratis. `caricaPreventivoPacco` con una riga manda il
  body MONO (le chiavi della risposta sono le stesse e renderControlla
  non se ne accorge): il riepilogo dice comunque il conto del SERVER,
  mai la stima. La guardia `< 2` di startBuySet resta come cintura di
  un varco che con una riga non si imbocca più.
  I SOLO-DIGITALI SONO FUORI DALLA GRIGLIA di composizione (ago 2026):
  non entreranno mai nel carrello per regola, e una cella spenta per
  sempre non è un'informazione — è rumore. renderPacco li filtra
  (`consegna==='digitale'`) e al loro posto c'è UNA riga in fondo,
  «💾 Gli articoli digitali si comprano singolarmente»; gli esclusi
  TEMPORANEI (asta, incompatibili, consegna '' degli storici) restano
  visibili e spenti col motivo, come sempre — motivoEsclusione non
  cambia e resta la cintura sul pezzo di partenza. E se il venditore
  ha SOLO digitali la striscia non porta al carrello: `tuttoDigitale`
  in sezioneAltriOggetti (giudica l + i 7 della striscia — un pezzo
  fisico oltre il settimo al più nasconde un bottone in più,
  dichiarato).
  LE CIFRE DEL CONTO NON SI SPEZZANO MAI (ago 2026, bug visto in
  vista sats: con l'etichetta «Spedizione (dalla più economica)» il ≈
  andava a capo SOPRA il numero): nella grammatica `.ctrl-riga` la
  cifra col suo ≈ e la sua unità è un gruppo indivisibile
  (white-space:nowrap sul `.mono`) e a cedere, coi puntini, è
  l'ETICHETTA a sinistra — vale per riepilogo E pagina Paga, che
  vestono le stesse righe di contoRighe (verificato a 320/375/430
  nelle due valute).
  DA STRISCIA A GRIGLIA (ago 2026, decisione di Andrea): era una fila
  che si scorreva di LATO (`.altri-strip`) — un gesto che nessun'altra
  parte dell'app chiede, e che nasconde tutto quello che non ci sta
  nei primi 150px. Ora è la griglia della vetrina, stesse card e
  stesso passo: la classe `.grid` così com'è, non una copia
  (`.altri-griglia` toglie solo il padding orizzontale, che qui dentro
  lo mette già `.detail-body`). Tetto da 6 a 8 card, che con due
  colonne fanno quattro righe piene.
  IL BOTTONE SI INCOLLA IN CIMA (modello Vinted) mentre gli oggetti
  scorrono sotto, ed è `position:sticky` dentro `.altri-sez` — la
  scelta è STRUTTURALE e vale più del comportamento: un elemento
  sticky non esce MAI dal suo contenitore, quindi non può arrivare a
  coprire la foto o il titolo (che stanno fuori dalla sezione) e si
  stacca da solo, senza scatti e senza un ascoltatore di scroll,
  quando la sezione finisce. `top:0` e non «un filo d'aria»: con uno
  stacco, sopra il bottone si vedeva passare la fetta di card che gli
  scorreva dietro — l'aria la dà il padding, che fa parte del fondo e
  copre fino al bordo (notch compreso). Da desktop `top:60px`, sotto
  la topbar. z-index 5, cioè sotto la barra d'acquisto (30) e sotto i
  fogli: non le ruba mai un tocco.
  NIENTE PIÙ VESTITO DI CARTONE (stessa decisione): il bottone è il
  ghost di casa come ogni altro secondario — un accento in più su un
  secondario faceva concorrenza all'unico pieno del dettaglio, che è
  Acquista. La classe `.btn.carton` col token `--carton` resta
  DEFINITA ma non la porta più nessuno: non è codice morto da
  cancellare, è un vestito appeso. Composizione:
  `setScelte` Map id→qta (parte dal pezzo aperto), celle con
  Aggiungi/chip − N + nella pagina del pacco, spente col motivo
  scritto, pillole consegna su `stradeSet()`
  (intersezione), `totaleSet()` con la matematica di totaleStima
  (artStima per riga × qta + MAX spedizioni + protezione),
  `stimaTagliaSet` gemello client (il giudice resta il server),
  `setCirca()` per il ≈. `startBuySet` = gemello
  di startBuy: stesso paySheet e stesso pollTimer (chiusure
  MIRATE, mai closeSheet col poll vivo), body a righe con
  offertaAccettataPer per riga; sul 409/404 `rinfrescaSet` rilegge
  il negozio (limit 100), spegne localmente gli spariti, pota
  selezione e quantità e ridisegna la pagina: l'utente vede il buco,
  non un vicolo cieco (il pezzo solo RISERVATO resta selezionabile:
  il fail-fast lo ridirà, dichiarato). Ordine: elenco «titolo × qta
  — sats» al posto della media, venditore con «📦 Spedisci il set
  (un pacco solo)» + taglia stimata. In DEMO il set non esiste
  (toast), in VETRINA apre l'invito. Gli importati da Nostr restano
  fuori dai set per costruzione (consegna '').
  LA ✕ DELLA PAGINA DEL PACCO CHIUDE E BUTTA VIA (ago 2026, decisione
  di Andrea). Il pacco è STICKY per venditore — uscire e rientrare dal
  dettaglio non svuota niente, `apriPacco` lo dice: stesso venditore =
  ritrova il suo pacco com'era — e questo non cambia; serviva però una
  strada per ricominciare da capo, e la ✕ è quella. Conferma davanti
  perché non si torna indietro (`#paccoSvuotaSheet`, registrato in
  closeSheet: foglio nostro e non il `confirm()` di sistema perché i
  due bottoni SONO il punto — rettangolari come «Acquista», quello che
  distrugge sopra e il ripensamento sotto); `svuotaPacco` azzera
  `setScelte` E `paccoDati`, quindi il prossimo «Aggiungi al pacco» è
  un pacco nuovo anche dallo stesso venditore. A pacco già vuoto non
  si chiede nulla: una domanda su una cosa che non esiste è solo un
  ostacolo. La ✕ è NUDA e non più un cerchietto col bordo e l'ombra
  piena: il cerchio di carta è il linguaggio di ciò che fluttua SULLA
  foto (share-btn, back-float), non di una testata — il bersaglio
  resta largo col `::after`, che non occupa layout.
  IL GESTO INDIETRO NON CHIEDE E NON SVUOTA, ed è dichiarato: torna al
  dettaglio col pacco intatto, come sempre. Due ragioni, e la seconda
  decide. «Indietro» vuol dire tornare, non buttare — chiedere una
  conferma distruttiva a chi voleva solo fare un passo indietro è la
  trappola classica. E soprattutto: nella PWA installata il gesto è di
  SISTEMA e non passa da `navIndietro`, quindi non si può
  intercettare, solo preparare (vedi il motore di navigazione). Un
  ripensamento agganciato al gesto funzionerebbe dentro Telegram e NON
  nella PWA, cioè la stessa ✕ farebbe due cose diverse sui due
  telefoni. Fra una garanzia che c'è solo a metà e una regola onesta,
  la regola.
  LA PAGINA «CONTROLLA IL PACCO» (ago 2026): il riepilogo del set da
  foglio a pagina intera — il foglio `#setSheet` NON ESISTE PIÙ, e
  con lui spunte e stepper del riepilogo: la composizione si tocca
  SOLO nella pagina del pacco, e il gesto indietro ci riporta con la
  selezione intatta. Vista `view-controllapacco`, contenuto da
  `renderControlla()`, aperta da `controllaPacco()` (che riallinea
  currentListing alla provenienza: serve alla rilettura del negozio
  dopo un 409). Dall'alto: testata con ← (navIndietro), titolo, «di
  {venditore}» e il toggle €/₿ in alto a destra (stessa preferenza di
  sempre, `setValuta` ridisegna anche questa pagina); «N articoli»
  (N = pezzi totali) coi FRANCOBOLLI degli scelti in striscia
  scorrevole (`.ctrl-mini`, ×N in mono sui multipli); CONSEGNA a
  pillole sull'intersezione di `stradeSet()` — una strada sola = UNA
  pillola già accesa, l'altra non compare (il campo non mente) —
  SENZA la stima taglia (decisione di Andrea al primo sguardo: resta
  nell'ordine, dove la scrive il server; `stimaTagliaSet` è il
  gemello client che aspetta, il vestito appeso di .carton); IL CONTO
  in righe (`contoControlla`/`cifraCtrl`, nella valuta del toggle: in
  euro sempre ≈, in sats il circa di `setCirca`, lo zero mai col ≈):
  Prezzo, «Commissione Barattolo — 0 sats» con la pillolina «in
  promo» (`.promo-tag`: la riga esiste per DIRE che oggi è gratis, ed
  è il posto già pronto per la cifra il giorno che la commissione si
  accenderà), Spedizione (il MAX di sempre; col ritiro vale 0 e la
  riga RESTA, non sparisce), Protezione solo se >0, e TOTALE DA
  PAGARE evidenziato (`.ctrl-riga.tot`, numero in --sats-text, unità
  sempre in `.unit`); niente trust-note (stessa decisione della
  taglia: la pagina dice il conto e basta); IN FONDO ALLO SCHERMO
  «Acquista» arancio (→ `startBuySet`, stesso paySheet sopra la
  pagina: la pagina post-acquisto è un cantiere futuro) e i due
  secondari gemelli (basi al 50%): «Chiedi info» → pagina del
  venditore (`ctrlChiediInfo` → apriNegozio), «Fai un'offerta» →
  `view-offertapresto`, il «presto disponibile» in stile astepresto
  (l'offerta sull'intero set è un cantiere futuro, NON costruita).
  I bottoni stanno in FONDO ALLA PAGINA per costruzione (secondo
  giro, dal feedback di Andrea: la prima versione sottraeva una
  costante stimata dall'altezza e restavano a mezz'aria): la VISTA
  attiva è la colonna alta uno schermo (dvh con ripiego vh; da
  desktop sconta i 116px di #app), il corpo prende il resto con
  flex:1, Acquista porta `margin-top:auto`, e con la tab bar nascosta
  `body.senza-nav #app` azzera anche il padding-bottom dei suoi 84px
  — il fondo è quello VERO (misurato: 26px dal bordo, il padding del
  corpo, che in basso porta anche la safe-area). Su schermi corti i
  bottoni seguono il contenuto, mai coperti; il fiato minimo sopra
  Acquista lo dà il margin-bottom del conto.
  Navigazione: vista interna (spinge) con la chiave del pacco
  (origineId); la ricostruzione esige paccoDati suo E setScelte non
  vuoto, o si ripiega sulla vetrina; `body.senza-nav` nasconde la tab
  bar sotto i 768 (è una cassa, non una vetrina) senza barra propria.
  Sull'errore di startBuySet si chiude il paySheet e si resta sulla
  pagina rinfrescata; se la potatura ha svuotato il pacco,
  `rinfrescaSet` torna indietro da solo. CONSEGUENZA DICHIARATA: col
  foglio è morto anche il suo «⚡ Compra subito» NWC
  (`confermaSetSubito`, che del foglio era l'unico chiamante) — dal
  riepilogo si passa dal paySheet, dove il wallet paga la stessa
  invoice; sul singolo annuncio l'NWC vive come sempre. Con meno di
  due articoli Acquista risponde col toast onesto («per uno solo c'è
  l'acquisto di sempre»), come il vecchio foglio.
  Doppia valuta (lug 2026): il venditore sceglie la valuta del listino
  in Vendi — colonne `annunci.valuta` ('sats' default: zero impatti
  sugli annunci esistenti) e `annunci.prezzo_eur`. Per i listini EUR
  `prezzo_sats` resta l'EQUIVALENTE al cambio di pubblicazione (serve
  al tetto, alla ricerca AI e come ripiego display). Il pagamento è
  SEMPRE in sats: `compra()` converte al cambio corrente alla
  creazione della invoice (la vita della invoice, 15 min, È il lock
  del prezzo: scaduta, si riconverte; 503 se il cambio non è mai
  arrivato) e salva `ordini.prezzo_sats` = sats effettivi +
  `ordini.cambio_ordine` = cambio usato (colonna nuova: `cambio_eur`
  mantiene la semantica di CHIUSURA e il CSV non cambia). La risposta
  di POST /api/orders ora include `prezzo_sats`. `prezzo_da_payload`
  è il giudice unico di pubblica/modifica: valida, converte e applica
  `TETTO_SATS_ANNUNCIO` — leva SPENTA di serie (default 0 = nessun
  limite; si accende dal config, es. 100_000; NON copre
  importa_nostr.py che scrive dritto nel DB); la modifica
  scrive SEMPRE valuta+prezzo_eur (eur→sats azzera l'euro). Drift del
  cambio tra pubblicazione e acquisto: tolleranza +20% alla creazione
  della invoice, oltre 409 + notifica al venditore (che si ripara
  ri-salvando il prezzo: la modifica riconvalida al cambio di oggi).
  NIP-99: tag `price` nella valuta del listino (es.
  ["price","40.00","EUR"]) e content coerente — importa_nostr sa già
  rileggere quel formato. Ricerca AI: la riga di catalogo porta
  entrambe le valute. Frontend: toggle ₿/€ nella searchbar di
  Esplora e — dal lug 2026 — un gemello nella riga del prezzo del
  DETTAGLIO (`valutaVista` in localStorage['barattolo_valuta'], una
  sola preferenza per tutti e due),
  `prezzoParte(l)` rende la valuta dello spettatore grande e l'altra
  piccola sotto — il «≈» sta SEMPRE e solo sul prezzo convertito, mai
  sul listino. L'unità non porta più uno spazio nel markup: l'aria la
  dà `.unit{margin-left:4px}`, e il SIMBOLO € (`.unit.eur`) sta più
  stretto e nel dettaglio quasi grande quanto la cifra — un simbolo
  di valuta appartiene al numero, la parola «sats» no (feedback di
  Andrea: il € pareva una nota a piè di pagina). Le migliaia si
  separano con lo spazio stretto unificatore U+202F in `fmt`
  (l'escape, mai il carattere: nel sorgente sarebbe invisibile): con
  lo spazio normale il mono di casa spezzava «905 000» in due blocchi
  lontani, e questo per giunta non va mai a capo a metà numero.
  `cambioVivo` (il cambio arriva dal nostro server, vedi sotto);
  form Vendi col suffisso-bottone sats/€
  (`sellValuta`, virgola decimale tradotta); paySheet e conferma NWC
  mostrano la stima «≈» e poi i sats VERI da `prezzo_sats` della
  risposta di POST /orders (MAI da `l.price`, che per i listini EUR
  è solo l'equivalente di pubblicazione).
  IL CAMBIO NON MUORE A UN RIAVVIO (ago 2026, caso vero dal campo: due
  deploy alle 13:34 e alle 13:48, CoinGecko muto in tutti e due, e un
  compratore davanti alla pagina d'acquisto bloccata da «il cambio euro
  non è disponibile»). La cache era già fail-open e teneva l'ultimo
  valore noto: il buco era che NASCEVA VUOTA — se al riavvio la prima
  lettura non riusciva, l'app non sapeva più convertire finché non ne
  riusciva una, e nel frattempo ogni listino in euro era incomprabile.
  Adesso l'ultimo cambio letto vive nella tabella `cambio_noto` (una
  riga, oggi 'eur') e `carica_cambio_salvato()` lo rimette in cache
  nello startup `scalda_cambio`, che finisce PRIMA che uvicorn accetti
  connessioni: la primissima pagina d'acquisto dopo un deploy trova già
  un cambio. La riga NON è un dato di denaro e nessun conto ci poggia
  sopra — è il promemoria fra un riavvio e l'altro, e per questo si
  scrive fail-open (un database che fa i capricci non deve rompere una
  conversione).
  TRE ETÀ, ed è la struttura da tenere: FRESCO (< `CAMBIO_TTL`, 15 min)
  si usa e basta; VECCHIO ma dentro `ORE_CAMBIO_VALIDO` si prova a
  rinfrescarlo e vale lo stesso se la rete tace; TROPPO VECCHIO vale 0,
  cioè «non disponibile» — il ripiego dichiarato di sempre (503 onesto
  sui listini in euro, promesse di negozio che non scattano e lo
  dicono), mai una conversione sbagliata. Giudice PURO
  `_cambio_valido(valore, quando, adesso, ore)` — prende i campi e non
  la cache, il patto di `in_ferie`: così serve la memoria, la riga del
  database e la prova in CI; al filo esatto è ancora buono, come
  `_asta_viva`.
  VENTIQUATTRO ORE, e la scelta va letta così: fino a ieri il valore in
  memoria non scadeva MAI — un processo acceso da una settimana poteva
  convertire col cambio di sette giorni prima senza che nessuno lo
  sapesse — quindi QUALUNQUE soglia finita è una stretta, e le 24 ore
  non bloccano nessuna interruzione realistica di CoinGecko, che si
  misura in minuti. Più in là il numero mente troppo: in un giorno BTC
  si muove di qualche punto, in una settimana di parecchi. `0` = non
  scade mai, cioè il mondo di ieri: freno d'emergenza, non una scelta.
  NON SI RIBUSSA A OGNI RICHIESTA: `CAMBIO_RIPROVA_S` (60) è il
  raffreddamento dopo un buco — senza, durante un'interruzione ogni
  pagina d'acquisto pagherebbe i 10 secondi di timeout per farsi dire
  di nuovo di no.
  IL RINFRESCO HA UN GIRO SUO (`orologio_cambio`, leva
  `CAMBIO_RINFRESCO_S`, 60s) e NON quello da dieci minuti dell'orologio
  grande, dove era nato. La ragione è la fonte unica: da quando il
  client non chiama più CoinGecko per conto suo, LA CADENZA DEL SERVER
  È LA FRESCHEZZA CHE VEDE CHIUNQUE GUARDI UN PREZZO — prima il browser
  vedeva un numero fresco di secondi, e dieci minuti lì dentro erano un
  numero vecchio in mano a tutti. La fonte unica non si tocca (due
  letture diverse erano un difetto vero: il «≈» della vetrina e il
  conto della invoice potevano divergere); a stringersi è solo la
  finestra. Lo stesso giro è anche la riprova del boot — il primo giro
  parte subito e un buco si ribussa dopo un minuto — quindi la scaletta
  di pause crescenti di ieri (`_insisti_sul_cambio`) NON ESISTE PIÙ: a
  regime sarebbe stata più LENTA di questo giro.
  `CAMBIO_TTL` È DERIVATA e non un secondo numero da tenere in pari:
  `max(120, CAMBIO_RINFRESCO_S * 2)`, due giri di slack. Chi alza la
  leva non deve ricordarsi di alzare anche la soglia, e soprattutto le
  due non possono mettersi di traverso — una soglia più STRETTA della
  cadenza rimetterebbe la rete nel percorso caldo a ogni giro, che è
  esattamente ciò che il rinfresco esiste per evitare. C'è la prova che
  la tortura su quattro cadenze.
  E NON SI FORZA MAI UNA LETTURA AL MOMENTO DELLA FATTURA (decisione di
  Andrea): nel percorso caldo la rete si tocca in un posto solo e dietro
  il raffreddamento — è la rete di sicurezza per quando il giro di
  sfondo si ferma, non un giro di rete in mezzo a un acquisto. In più il
  giro di sfondo lo disinnesca gratis: timbra `tentato` a ogni battito,
  riuscito o no, quindi finché batte dal percorso caldo non parte una
  chiamata nemmeno per sbaglio. Due sentinelle lo sorvegliano.
  IL CARICO, misurato: un minuto = ~1.400 chiamate al giorno da un IP
  solo, comodamente dentro il limite al minuto dell'endpoint pubblico
  di CoinGecko — ma ~43.000 al mese, cioè BEN OLTRE le 10.000 di una
  chiave Demo gratuita: se un giorno se ne mette una, la leva va alzata
  (300s ≈ 9.000/mese). È anche il motivo per cui è una leva e non una
  costante: un 429 si cura con una riga nel config del VPS invece che
  con un deploy. `0` = niente giro di sfondo (una lettura all'avvio e
  poi se ne occupa il caldo).
  Tre righe di journal all'avvio, e vanno lette: «ripreso dal
  database», «l'ultimo salvato ha più di N ore», «nessun valore
  salvato»; più «letto: N €/BTC» alla prima lettura buona, e UNA sola
  riga per interruzione dopo dieci minuti di silenzio (il conto è in
  GIRI e non in secondi, o con una cadenza che non divide 600 quel
  momento non arriverebbe mai).
  DUE NUMERI, UNA SOLA ETÀ (ago 2026): la stessa GET porta euro E
  dollari (`vs_currencies=eur,usd`) senza costare un byte in più, e
  siccome arrivano insieme invecchiano insieme — quindi `quando` è UNO
  e non uno per valuta, e `_cambio_valido` non cambia di una riga. Il
  DOLLARO NON ENTRA IN NESSUN PERCORSO DEL DENARO: le invoice le fa
  `cambio_btc_eur`, che è e resta l'euro; il dollaro esce solo da
  `cambio_per_import()`. E l'euro COMANDA la lettura: se manca lui la
  lettura non vale, anche se il dollaro fosse arrivato.
  L'IMPORT DA NOSTR BEVE ALLA STESSA FONTE, ed era l'ultima verità
  doppia rimasta in piedi — si è fatta vedere nel journal: alle
  14:52:33 il server legge 56.313, alle 14:52:57 l'import stampa
  «⚠️ Cambio BTC non disponibile: gli annunci in EUR/USD verranno
  saltati». Due letture, due esiti, per convertire gli stessi bitcoin.
  E il guasto era più grosso di una chiamata doppia: quella lettura
  viveva DENTRO `importa_venditore`, che il giro orario chiama UNA
  VOLTA PER VENDITORE — cioè una raffica di chiamate a ogni giro, dallo
  stesso IP da cui bussa già il nostro rinfresco (probabile causa del
  429 osservato), e per giunta una conversione DIVERSA per ogni
  venditore dello stesso giro. Ora `importa_venditore` accetta
  `cambio`, il patto del `vaglio` e di `scarica`: il server lo legge
  UNA volta per giro con `cambio_per_import()` (dalla cache, mai dalla
  rete) e lo passa a tutti — quindi tutti gli annunci di un giro si
  convertono allo stesso cambio, che è anche quello delle invoice.
  Lo SCRIPT A MANO resta identico: `cambio=None` vuol dire «me lo leggo
  io», e `cambio_btc()` è ancora lì per lui (adesso col PERCHÉ nel
  messaggio d'errore — «non disponibile» può essere una rete giù o un
  429, e sono due problemi diversi). Un dizionario VUOTO passato
  apposta vuol dire «non ce l'ho», e l'import si comporta come ha
  sempre fatto: salta gli annunci in EUR/USD e LO DICE — il messaggio
  vive in `MSG_CAMBIO_MANCANTE`, un posto solo per le due strade, o il
  ramo nuovo avrebbe saltato in silenzio.
  UNA SOLA FONTE, ed è la parte che tocca il client: prima ogni browser
  chiamava CoinGecko per conto suo — N utenti N chiamate, e soprattutto
  DUE verità, perché il «≈» della vetrina poteva dire una cifra e il
  conto del server un'altra (erano due letture di momenti diversi).
  Adesso il cambio viaggia in `cambio_eur` nella busta di PRIMA PAGINA
  di `/api/listings`, che il client chiede già all'avvio: zero giri di
  rete in più, e la vetrina parla la stessa lingua della invoice. Il
  server ci mette `cambio_noto_ora()` — la cache, MAI la rete: chi
  sfoglia il mercatino non deve aspettare CoinGecko. Nel client
  `impostaCambio(eurPerBtc)` rifiuta lo 0 (mai un numero inventato) e
  arriva PRIMA del primo `renderGrid` (`loadListings` è atteso), quindi
  è sparito anche il giro di render che rimediava alla risposta in
  ritardo. IMPERFEZIONE DICHIARATA: in DEMO da `file://` non c'è
  nessuna busta, quindi resta il valore di riserva con `cambioVivo`
  falso — cioè il patto di sempre, dove il numero conta il «≈» si
  omette. Leva `ORE_CAMBIO_VALIDO` nel pannello «⚙️ Stato delle leve».
  IL GESTO INDIETRO (lug 2026): il tasto indietro di Android, lo swipe
  dal bordo e il tasto del browser tornano indietro di un passo invece
  di chiudere l'app — prima chiudono i fogli aperti, poi smontano le
  viste; si esce solo dalla RADICE. La freccia ← e la tab bar restano
  tutte: il gesto si aggiunge. Blocco `nav*` subito dopo `go()`, acceso
  da `navMotore()` una riga prima di `avvia()` (prima non si può: le
  variabili degli strati sono dichiarate più in basso e sarebbero in
  zona morta). Tre scelte da NON rovesciare:
  1) l'URL non si tocca MAI (`pushState` con `location.href`) — il
  server serve solo rotte esplicite (regola 3), un `/profilo` inventato
  darebbe 404 al reload, e le costanti deep-link `NEGOZIO_URL`/
  `ANNUNCIO_URL` si leggono una volta al parse;
  2) l'ascoltatore è DICHIARATIVO: `popstate` non dice «indietro», dice
  «il cursore si è spostato» — si sposta anche in AVANTI e può saltare
  più entry insieme (i browser marcano saltabili quelle spinte fuori da
  un gesto: il deep link dopo l'await, `openOrder` nel setTimeout del
  pagamento, il tour che parte da solo). `navApplica` RI-APPLICA la
  pila scritta nella entry (`history.state.pila`), non «toglie un
  livello»: degrada, non si rompe. Per la stessa ragione niente
  `history.go(-n)` con un contatore di debito — asincrono e coalescente,
  la fabbrica dei bug irriproducibili: le chiusure programmatiche usano
  `replaceState`, che è sincrono;
  3) la pila si DERIVA dal DOM (`navPila`: la vista in fondo, sopra gli
  strati per z-index — fogli, lightbox, tour, cartello; il picker
  forzato ultimo fra i fogli, è l'unico che si apre SOPRA un altro) e a
  rilevarla è un `MutationObserver` sulle classi. È ciò che tiene il
  diff piccolo: i 18 siti che aprono un foglio, `closeSheet()` e le tre
  chiusure mirate anti-`pollTimer` sono rimasti INTONSI. Il callback è
  un microtask (ancora dentro il task del gesto, e coalesce i cambi
  dello stesso giro: per questo foglio→foglio — invitoSheet→nostrSheet — è a
  saldo zero da solo).
  Si SPINGE solo entrando in una vista più interna (dettaglio, negozio,
  ordine, sicurezza); i quattro tab sono RADICI sorelle e si
  SOSTITUISCONO (girarli non costa quattro indietro, e dalla radice il
  gesto esce). `navChiudiStrato` chiude sempre con la funzione dedicata,
  MAI `closeSheet()`: il `pollTimer` si ferma solo col `paySheet`, che è
  più preciso di prima. `navRendiVista` ricostruisce col suo opener
  (`openDetail`/`openOrder`/`apriNegozio`) e controlla PRIMA che la
  vista non si sia svuotata — `openOrder` non ha guardie e ci morirebbe
  dentro: è il ripiego che prima era scritto due volte (in
  `tornaDaSicurezza` e nella ri-idratazione di `avvia()`) e ora vive in
  un posto solo. `navRiflette()` è richiamata a mano SOLO in coda a
  `openDetail`: dettaglio→dettaglio (le card della striscia «Altri
  oggetti») non cambia nessuna classe e l'osservatore non la vedrebbe.
  Ogni affordance di ritorno passa da `navIndietro()` = `history.back()`
  (le due «← Torna», il «← I tuoi ordini», la freccia sulla foto, ✕ e
  Annulla dei fogli, tocco sul velo, i tre Escape, «Salta» del tour):
  UNO SOLO smonta i livelli — l'ascoltatore di popstate — così gesto e
  freccia non possono divergere, e non restano gradini morti (un
  indietro che non fa niente). Per questo sono spariti `sicurezzaRitorno`
  e l'euristica di `tornaDalNegozio` su `currentListing`: la cronologia
  sa da dove si veniva meglio di loro. Restano programmatiche le
  chiusure che non sono un gesto (`closeSheet` dopo il pagamento, il
  foglio invito che lascia il posto a quello Nostr, `simulatePaid`).
  DALLA RADICE SI ESCE, E USCIRE VA DETTO (lug 2026, da un bug vero
  visto da Andrea sullo swipe da Sfoglia): `navIndietro` faceva
  `history.back()` alla CIECA, e dentro Telegram — come nella PWA
  installata — la nostra pagina è la PRIMA della sessione, quindi
  «indietro» non ha dove andare e il gesto moriva in silenzio, lo
  schermo fermo dov'era. Vale per OGNI radice; si notava su Sfoglia
  perché è quella da cui uno si aspetta un passo. Ora il gradino su cui
  si sta lo dice la cronologia stessa: `d` nello state (0 = sotto non
  c'è NIENTE di nostro), scritto da `navRiflette` accanto alla pila —
  +1 sul push, invariato sul replace — e seminato a 0 da `navMotore`.
  A `d=0` e a strati chiusi decide il patto della RADICE MADRE (sotto);
  su Esplora nuda, dentro Telegram, si chiama `tg.close()`, e fuori
  resta lo `history.back()` di sempre. NIENTE contatori di debito: `d`
  viaggia nella entry, come la pila — è la stessa ragione per cui
  l'ascoltatore è dichiarativo.
  DUE CONTESTI, E VANNO TENUTI DISTINTI (lug 2026, ed è la lezione che
  costa di più in questo cantiere — il primo giro di correzioni era
  scritto per il contesto sbagliato): dentro la **Mini App** il gesto
  lo intercetta il CLIENT Telegram, che ce lo gira come
  `backButtonClicked` solo se il `BackButton` è visibile, altrimenti
  chiude l'app; nella **PWA installata** (e nel browser, e nell'APK,
  cioè dove Andrea prova) non esiste né `tg.BackButton` né
  `tg.close()` né `disableVerticalSwipes`, e il gesto è quello di
  SISTEMA: non passa MAI da `navIndietro`, parla direttamente con la
  cronologia. Conseguenza da tenere sempre presente: quello che la
  PWA fa non si può INTERCETTARE, si può solo PREPARARE — se un passo
  indietro deve esistere, deve esistere come entry, prima che il gesto
  arrivi. Ogni rimedio scritto come «quando arriva il gesto, deviamo»
  funziona solo dentro Telegram.
  ESPLORA È LA RADICE MADRE (`RADICE_MADRE`, lug 2026, decisione di
  Andrea): da Sfoglia, Vendi, Ordini e Profilo l'indietro porta a
  Esplora, e solo da Esplora si esce. Il MECCANISMO è la cronologia,
  non un intercettatore: il PRIMO passo via da Esplora SPINGE
  (`primoPassoViaDaCasa` in `navRiflette`, e solo il primo — `giu===0`),
  così sotto ogni radice figlia c'è la madre e il gesto di sistema la
  trova da sé, in tutti e due i contesti. Da una figlia all'altra si
  sostituisce come sempre: girare tutti i tab costa UN indietro, mai
  uno a testa — il patto delle sorelle regge dove serviva davvero.
  Tornare alla madre col tab è un INDIETRO vero (`vaiEsplora` chiama
  `navIndietro` quando è l'unico gradino), non una sostituzione: sotto
  resterebbe una entry identica, cioè un indietro che non fa niente, e
  il gesto dopo ne chiederebbe due per uscire.
  LA ENTRY DELLA VETRINA DICE RAMO E CATEGORIA (`chiaveVetrina`): era
  l'imperfezione dichiarata «l'avanti dentro un reparto ricostruisce la
  vista ma non il filtro», e con la radice madre diventava una bugia —
  si tornava a Esplora col mercatino intero e la nav accesa su Sfoglia.
  Per tenerla onesta `setCat` chiama `navRiflette` (cambiare categoria
  non tocca nessuna classe, l'osservatore non se ne accorgerebbe), e
  siccome quella chiamata LEGGE-E-AZZERA `navSpingi`, in
  `apriCategoria` la bandierina si alza subito prima del `go()` che la
  usa e non in cima alla funzione — alzata prima se la mangiava quel
  giro, e la discesa nel reparto tornava a essere un cambio di tab.
  MENTRE SI RI-APPLICA UNA ENTRY NON SI SCRIVE (`navApplicando`): il
  giro di ricostruzione chiama `setCat` e `go`, che riflettono a metà
  strada — con la vista vecchia ancora attiva — e leggevano un cambio
  di radice che nessuno aveva chiesto, spingendo un gradino nuovo
  invece di consumarne uno. Si spegne in un `queueMicrotask`, dopo il
  giro dell'osservatore. La ragione che decide: su Subito
  e Vinted funziona esattamente così — la home è la radice madre, dalle
  sezioni l'indietro ci passa, e di lì si chiude. È la convenzione che
  i nostri utenti hanno GIÀ NELLE DITA, e vale più della simmetria fra
  radici sorelle: quella è una proprietà del nostro modello, questa
  un'abitudine di chi lo usa.
  L'ARGOMENTO PERDENTE sta qui perché fra sei mesi si sappia che è una
  scelta e non una svista — per un giorno la regola è stata l'opposta
  («ogni radice esce per conto suo»), e le ragioni erano: le radici
  sono sorelle e non parenti, la discesa su Esplora è una gerarchia che
  la cronologia non registra, e sarebbe la seconda deroga per Sfoglia,
  che ne ha già una (la piastrella è una discesa). Restano vere: hanno
  solo meno peso della convenzione. CONSEGUENZA ACCETTATA (era il caso
  sollevato contro): chi apre l'app dritto su un'altra radice
  all'indietro finisce in Esplora, dove non è mai passato — lo fanno
  anche loro.
  Il patto delle radici SORELLE resta intatto dove riguarda la
  cronologia: fra tab si SOSTITUISCE sempre, girarli tutti non costa un
  indietro a testa, e il passaggio da Esplora non spinge niente
  (`vaiEsplora` è un ritorno a una radice, quindi replaceState, e `d`
  resta 0). Ed è `vaiEsplora` e NON `go('esplora')` perché la madre è
  il mercatino INTERO: senza il ritorno a «Tutto» si atterrerebbe su
  una vetrina ancora filtrata con la nav accesa su Sfoglia, che è
  esattamente la bugia che `ramoVetrina` esiste per non dire.
  Telegram: `navFreccia` mostra il `BackButton` (Bot API 6.1) solo
  quando c'è dove tornare — ed è la STESSA domanda di `navIndietro`,
  quindi un giudice solo, o la freccia e il gesto divergono. Resta
  nascosto SOLO su Esplora nuda (`d=0`, nessuno strato), e lì il gesto
  chiude la Mini App, che È il patto. Sulle altre radici ora si vede,
  ed è OBBLIGATORIO: con la freccia nascosta il gesto lo intercetta il
  client, che chiuderebbe l'app per conto suo, e il passaggio da
  Esplora non avverrebbe mai. E si vede anche a `d>0` su Esplora — una
  categoria aperta da una piastrella è Esplora ma con Sfoglia sotto, e
  lì l'indietro deve riportare allo scaffale. Lo swipe VERTICALE si
  spegne SEMPRE con `disableVerticalSwipes` (7.7), anche alla radice, e
  dal lug 2026: finché restava acceso lì, tirare giù per aggiornare
  trascinava via la Mini App: un gesto che ovunque significa
  «rinfresca» qui significava «vattene», e chi lo faceva lo leggeva
  come un torna-indietro. Ora quel trascinamento è NOSTRO (vedi il
  gesto di aggiornamento). Non si perde nessuna via d'uscita: la
  chrome di Telegram non si tocca mai, lo dice la sua
  documentazione («the user will still be able to minimize and close
  the Mini App by swiping the Mini App's header»). Il tasto di Telegram
  chiama `history.back()` come tutti, con una serratura di 350ms contro
  il doppio canale (certi client potrebbero emettere sia
  `backButtonClicked` sia `popstate`). Deep link `/annuncio/{id}`:
  l'apertura spinge SOPRA la radice, quindi il primo indietro atterra
  sulla vetrina (deciso: un modello solo, e da un annuncio condiviso
  l'indietro fa scoprire il catalogo invece di buttare fuori). La
  semina della radice in `navMotore` serve perché `history.state`
  SOPRAVVIVE ai `location.reload()` del login e racconterebbe cose
  della vecchia identità. Su `file://` (la DEMO a mano) `STORIA` è
  falsa e il motore resta spento: `navIndietro` smonta lo strato in
  cima e, se non ce n'è, torna al mercatino — che è la stessa regola
  della radice madre, detta a mano perché lì la cronologia non c'è.
  IMPERFEZIONI DICHIARATE:
  dopo un pagamento riuscito resta un gradino morto (`closeSheet`
  programmatico sostituisce, non cancella la entry gemella); l'avanti
  del browser su uno strato non lo riapre (lightbox e tour vogliono
  dati che nella entry non ci sono) e ci pensa il `navRiflette`
  successivo a rimettere la entry in pari — sistema auto-guarente; il
  pannello Filtri è fuori di proposito (è in pagina, usa `style.display`
  che l'osservatore delle classi non vede, e non intrappola nessuno).
  TORNANDO INDIETRO LA VETRINA RIPARTE DA DOVE SI ERA (ago 2026), e la
  prima cosa da sapere è la DIAGNOSI, perché rovescia l'istinto: la
  griglia NON si perde mai. Aprire un annuncio non svuota `#grid` —
  misurato, 90 card prima, 90 durante, 90 dopo — quindi non c'era
  niente da ricaricare, e la cura è la più semplice delle due. A
  perdersi era la sola POSIZIONE, per due cause che si sommano:
  entrando nel dettaglio la vetrina va in `display:none`, il documento
  si accorcia da 13364 a 2273px e il browser CLAMPA lo scorrimento a
  zero — cioè la posizione è già persa prima di tornare — e poi `go()`
  lo riportava comunque in cima col suo `scrollTo(0,0)`.
  Quindi: `vetrinaPos` = `{y, n}`, salvato IN CIMA a `go()`, PRIMA del
  `remove('active')` (spostarlo sotto salverebbe sempre zero, ed è la
  trappola di questo cantiere: non romperebbe niente di visibile), e
  riletto dal giudice unico `posizioneDaRendere(view)`, che ha preso il
  posto dello `scrollTo(0,0)` nudo.
  IL GIUDICE DEL «RITORNO» È `navApplicando`, la bandierina che il
  motore alza mentre RI-APPLICA una entry — l'unica cosa che distingue
  un ritorno da un ingresso nuovo, e ci passano allo stesso modo lo
  swipe di sistema della PWA, il tasto di Telegram e la freccia ←. Da
  lì escono GRATIS le regole che nessuno ha scritto: la tirata di
  aggiornamento e il cambio di filtro non sono traversate; i percorsi
  che entrano da fuori (deep link, ritorno dopo il pagamento,
  ripristino d'identità) non hanno né entry né posizione salvata; e il
  tocco sul tab Esplora mentre si è GIÀ in Esplora torna in cima
  (non è un indietro), mentre arrivandoci da un'altra radice si ritrova
  la vetrina dov'era — che è la convenzione dei tab.
  DUE DENTI DELLO STESSO LUCCHETTO, e servono tutt'e due: il CONTO
  delle card (`n`) dice che la griglia è ancora quella — ricerca AI,
  potatura, un annuncio sparito fanno ripartire dalla cima invece di
  atterrare nel vuoto, che il cantiere dichiara peggio di niente — e
  `loadListings` BUTTA `vetrinaPos` accanto al giro, perché due vetrine
  diverse possono avere lo stesso numero di card (30 e 30): è il caso
  vero «modifico l'annuncio dal dettaglio e torno». Più
  `history.scrollRestoration='manual'` nel motore: con l'URL che non
  cambia mai le entry del browser si somigliano tutte e il suo
  tentativo arriverebbe dopo il nostro, diverso da un browser
  all'altro.
  COSA COPRE: la vetrina, da ogni strada che la lascia — dettaglio,
  negozio, carrello e riepilogo, pagina d'acquisto, ordine — e dentro
  qualunque ramo (Esplora, una categoria aperta da Sfoglia, il filtro
  delle Aste), salti multipli compresi. COSA NO, ed è dichiarato:
  negozio, Ordini, Profilo e «I tuoi annunci» si RIFANNO quando ci si
  torna (un fetch, e i dati arrivano dopo), quindi al momento dello
  scorrimento la pagina non è ancora alta come sarà e la posizione
  cadrebbe nel vuoto per davvero — chi vorrà aggiungerne una deve prima
  garantire che il suo markup sopravviva al ritorno, com'è per la
  vetrina. In DEMO da `file://` il motore è spento, quindi
  `navApplicando` non si accende mai e vale il comportamento di ieri.
  E NEMMENO IL FOCUS DEVE TRASCINARE LA PAGINA (trovato di striscia,
  ed era lì da sempre): chiudendo il picker, `pickerTrigger.focus()`
  riportava in cima — il campo-bottone «Ordina» vive lassù — cioè la
  stessa frustrazione per un'altra strada. `preventScroll:true` in
  tutt'e due i chiamanti (`closeSheet` e `chiudiPicker`, che devono
  restare allineati): il focus torna al campo, l'accessibilità del
  picker resta intera, la pagina no. Dove l'opzione non c'è (i Safari
  vecchi) si ignora e vale il comportamento di ieri: mai peggio.
  IL GESTO DI AGGIORNAMENTO (lug 2026): tirare giù dalla cima rilegge la
  vista e ci RESTA — pastiglia di carta `#ptr` che scende col dito
  (z-index 25: sopra l'header, o dietro sparirebbe; sotto nav, barra
  d'acquisto e fogli — è un segnale, non uno strato). Nasce perché quel
  trascinamento non era di nessuno: dentro Telegram era la presa che
  porta via la Mini App (vedi `disableVerticalSwipes` qui sopra), nel
  browser il ricarica nativo — che già non parte, `overscroll-behavior:
  none` sul body c'è da sempre, e comunque ripartirebbe da Esplora
  perdendo dov'eri. `aggiornaVista` rilegge la vetrina da sé; Ordini e
  Profilo li ricarica `go()`, che quelle viste le sa già caricare — un
  secondo posto che elenca i loro render divergerebbe al primo cassetto
  nuovo. Mezzo secondo minimo di pastiglia che gira, o su rete veloce
  lampeggerebbe e sembrerebbe non essere successo niente; fail-open.
  UN touchmove SU TUTTA LA PAGINA È UN ASCOLTATORE INVADENTE, quindi è
  timido PER COSTRUZIONE, e sono i tre recinti da non togliere:
  1) solo dalla CIMA (`scrollY<=0`) e a STRATI CHIUSI — lo dice
  `navPila().length===1`, nessuna seconda lista da tenere allineata;
  2) solo sulle viste che hanno davvero qualcosa da rileggere
  (`VISTE_PTR`: esplora, affari, profilo). Così la GALLERIA a
  scroll-snap del dettaglio resta fuori dal gesto senza doverla
  nominare — lì la foto è in cima, quindi `scrollY` è 0 e una diagonale
  avrebbe armato una tirata che poi non ricaricava niente: mezzo
  secondo di pastiglia per nulla. Chi aggiunge una vista ad
  `aggiornaVista` deve aggiungerla anche a `VISTE_PTR`, o il gesto gira
  a vuoto proprio dove lo si chiede;
  3) il gesto dev'essere VERTICALE: appena `dx > dy` la tirata si
  annulla e non torna fino al tocco dopo — è il recinto delle strisce
  che scorrono di fianco dentro le viste ammesse (pillole delle
  categorie, «Altri oggetti»).
  IL touchmove È NON-PASSIVO, MA SOLO MENTRE LA TIRATA È ARMATA (lug
  2026, dalla PWA di Andrea): un ascoltatore passivo non può chiamare
  `preventDefault`, quindi non poteva togliere di mezzo il
  pull-to-refresh NATIVO di Chrome — che ricaricava la pagina, e
  ricaricando si riparte da Esplora: il gesto sembrava un
  torna-indietro proprio mentre si chiedeva un aggiornamento. Si
  appende nel `touchstart` quando `ptrPuo()` dice di sì e si stacca al
  rilascio, così per tutto il resto dello scorrimento la strada veloce
  del compositor resta intatta — è la ragione per cui non ce n'è uno
  permanente. `overscroll-behavior` sull'html lo spegne comunque (vedi
  sotto), ma a decidere dev'essere il nostro gesto, non una proprietà
  che un domani qualcuno rimette ad `auto`.
  `OVERSCROLL-BEHAVIOR VA SULL'HTML`, non solo sul body: alla viewport
  arriva il valore dell'ELEMENTO RADICE, e finché l'html restava `auto`
  quel `none` sul body (che c'era da sempre) non spegneva NIENTE.
  Costava due bug insieme, e vale per i due assi: il pull-to-refresh
  nativo qui sopra, e l'incatenamento ORIZZONTALE della galleria a foto
  singola (vedi il dettaglio annuncio).
  Reduced-motion spegne transizione e giro. Il dettaglio NON si
  aggiorna di proposito: riaprirlo da capo azzererebbe pezzi scelti e
  strada di consegna, e non è quello che chiede un dito che tira giù.
  Cinque modalità, decise in `avvia()`: app vera dentro Telegram (auth
  via initData); WEB dal browser (cookie di sessione, app completa:
  `authHdr()` manda header vuoto e comanda il cookie; il sondaggio
  cookie viene PRIMA di quello collaudo); collaudo locale (identità
  finte + bottone "cookie web" per provare il login web senza widget);
  VETRINA pubblica in sola lettura dal browser (annunci veri, banner
  col widget "Entra con Telegram" — `data-request-access=write` chiede
  il permesso per gli avvisi — e ogni azione apre l'invito verso
  @ilbarattolobot, che dal lug 2026 offre anche la porta «🟣 …o entra
  con Nostr»: chi arriva dal link di un DM entra con la sua chiave e
  il reload riapre /annuncio/{id} autenticato, azione a un tocco);
  demo coi dati finti come riserva se il backend tace.
  Login Nostr nel foglio `#nostrSheet` (bottone 🟣 in vetrina e nella
  barra collaudo — a differenza del widget Telegram funziona anche in
  locale): astrazione `firmatario = {pubkey, firma}` con tre fabbriche
  — estensione NIP-07 (zero librerie), bunker NIP-46 (client fatto in
  casa coi mattoni del bundle: richieste kind-24133 cifrate NIP-44 su
  relay, `auth_url` in popup), nsec incollata che firma SOLO in pagina
  (chiave nella closure, azzerata dopo la firma: mai inviata, mai
  salvata, UI che la sconsiglia). Il bundle si carica pigro da
  `/vendor/nostr.js` solo per bunker/nsec. `barraWeb` con avviso
  onesto per chi entra da Nostr (che indica «Collega Telegram» nel
  Profilo); foglio `#collegaSheet` per la proposta di collegamento.
  Blocco «Le tue identità» nel Profilo (`renderIdentita()`, dati già in
  `/api/me`): riga Telegram (nome+username, o «Collega Telegram» per
  i tg_id negativi → `collegaTelegram()` apre il deep-link col codice,
  mai mostrato in chiaro) e riga Nostr (npub nei 4 stati: assente /
  da verificare / verificata con «Abilita l'accesso» / 🔑 attiva con
  «Disabilita» solo su tg_id positivi).
  Onboarding contestuale (lug 2026): niente wizard iniziale, righe
  `.hintline` che compaiono al momento del bisogno e SOLO se la
  funzione manca davvero; «Non ora» le spegne per sempre in
  `localStorage['barattolo_hint']` = {id: timestamp} (frontend puro,
  zero colonne DB: il dismiss del wallet NWC DEVE essere
  per-dispositivo perché il wallet stesso vive in localStorage), e
  con `hintAttivi()` (=!DEMO && !VETRINA) non esistono in demo e
  vetrina. Tre hint-evento: `nwc` nel paySheet (in fondo, sotto
  Annulla — il percorso di pagamento non si allunga; nel ripiego
  Compra subito la riga resta vuota: lì il wallet c'è), `lnaddr` e
  `npubverifica` sulla scheda dell'annuncio appena pubblicato
  (passamano `hintPubblicazione={id,annuncio}` consumato da
  `openDetail` solo su QUEL annuncio; max UN hint per evento,
  precedenza agli incassi). Il CTA positivo NON dismette (se
  l'azione si completa la condizione cade da sola) e porta al
  Profilo col cassetto giusto aperto (`apriCassettoProfilo`). Più
  la checklist «Completa il profilo (N di M)» sotto la testata del
  Profilo (`renderChecklist`, `#profiloChecklist`): M dinamico
  (ln_address, npub verificata, wallet NWC «su questo dispositivo»,
  + Telegram per i tg_id negativi), niente dismiss, a profilo
  completo sparisce del tutto.
  Tour di benvenuto (lug 2026, ha SOSTITUITO la riga one-shot
  `hintBenvenuto`): quattro tappe col riflettore alla PRIMA visita
  autenticata (mai DEMO/VETRINA), zero librerie. Meccanica: velo
  `#tour` (z-index 80, sopra lightbox 70; cattura ogni tocco e blocca
  wheel/touchmove) + riflettore `#tourLuce` (il buio è la SUA ombra:
  `box-shadow 0 0 0 9999px` — ritaglio con angoli morbidi gratis,
  passaggio di tappa = transition su top/left/width/height, classe
  `.tondo` per barattolino e tappo, anello `outline` arancio) +
  fumetto `#tourFumetto` sui token (dark gratis), sotto il bersaglio
  se c'è posto, sopra altrimenti, clampato ai bordi. Tappe
  (`TAPPE_TOUR`: `trova()` + testo): prima `.card` della griglia →
  primo `.card-jar` (NON per forza sulla prima card) → `.trust-line`
  di Esplora (il deposito di garanzia, con «(escrow)» da prima
  spiegazione) → `.avatar-btn.on` visibile (istanza header su mobile,
  topbar da desktop, filtro `offsetParent`). Le tappe si fotografano
  all'avvio (`tourTappe`): bersaglio assente = la tappa non entra nel
  giro (contatore «N di M» onesto), NESSUNA tappa viva (vista
  sbagliata, vetrina vuota) = non parte e NON consuma. Si consuma in
  `barattolo_hint.tour` APPENA parte (one-shot vero: Salta/Escape
  chiudono e basta); parte in `avvia()` dopo renderGrid, precedenza
  sul banner installa PWA (`tourInCorso` al posto del vecchio
  `benvenutoInVista`; alla chiusura si richiama `bannerInstallaPwa()`
  che riottiene la sua occasione nella stessa visita).
  Reduced-motion: niente transizioni né smooth scroll (`tourRidotto`).
  ATTENZIONE ai rAF: `posizionaTour()` va chiamata anche in SINCRONO
  (pagina in secondo piano = rAF fermi, il tour deve trovarsi
  posizionato comunque); classe `.subito` sul primo posizionamento
  per non far scivolare il riflettore dall'angolo. La checklist si
  apre da sola alla PRIMA visita del Profilo con profilo incompleto
  (`checklistvista` in barattolo_hint + `checklistPrimoSguardo` per
  pagina; a profilo completo la prima visita NON si consuma), dalla
  seconda torna chiusa com'era. Collaudo dal vivo: bottone admin
  «🧽 Trattami da nuovo» in fondo alle statistiche
  (`trattamiDaNuovo()`) — azzera barattolo_hint, va su Esplora (il
  tour vive lì) e riarma tour e checklist SUL DISPOSITIVO: gli hint
  sono localStorage puro, il server non c'entra (per questo non è un
  comando bot) e annunci/ordini/profilo non si toccano (azzera anche
  `barattolo_test`, la memoria del cartello qui sotto).
  Cartello «fase di test» (lug 2026): l'avviso di rodaggio
  all'apertura — modale a tutto schermo col velo SFOCATO
  (`#testModale`, z-index 90: sopra i fogli e sopra il tour), si
  chiude col bottone, con la ✕ o col GESTO INDIETRO — mai col tocco
  fuori né con Escape: deve essere letto, ma non si può fingere che
  l'indietro non esista (lug 2026, deciso con Andrea quando è nato il
  motore di navigazione: su Android un indietro che non fa niente si
  preme tre volte e la terza esce comunque dall'app, e alla prima
  apertura il cartello sta sulla RADICE, dove dentro Telegram il gesto
  chiude la Mini App e non c'è modo di intercettarlo — una regola
  onesta batte una garanzia che non c'è). Interruttore, testo e link vivono nel
  CONFIG (`BANNER_TEST`, `BANNER_TEST_TESTO`, `BANNER_TEST_LINK`) e
  arrivano al client da `GET /api/banner-test`, endpoint PUBBLICO come
  /api/listings (lo legge anche l'anonimo in vetrina; spento o testo
  vuoto = `{attivo:false}` e non si disegna nulla): a rodaggio finito
  basta un False nel config del VPS, senza cantieri. La PRIMA riga del
  testo è il titolo, il resto il messaggio (`white-space:pre-line` e
  `textContent` puro: nessun innerHTML sul testo); il bottone del
  canale compare solo con un link http(s) — la stringa vive in
  `linkCanaleTest`, mai dentro un onclick — e dentro Telegram passa da
  `tg.openTelegramLink`. Frequenza: UNA VOLTA AL GIORNO per
  dispositivo (`localStorage['barattolo_test']` = giorno LOCALE,
  consumato alla comparsa come il tour: i tester aprono l'app di
  continuo), mai in DEMO, sempre in vetrina anonima. PRECEDENZA:
  `modaleTest(dopo)` prende in carico ciò che veniva dopo — alla
  chiusura partono tour e banner installa, e `testModaleInCorso` è
  nelle guardie di `bannerInstallaPwa()`; server muto o interruttore
  spento = il giorno NON si consuma e il seguito parte comunque.
  Il cartello passa una volta al giorno, ma la porta al canale resta:
  fascia `#fasciaTest` sotto la trust-line di Esplora
  (`renderFasciaTest`, chiamata da `modaleTest`) — «🚧 Barattolo è in
  fase di test — 💬 Dicci la tua ›», stesso interruttore e stesso
  link, anche per gli anonimi, mai in DEMO, e senza link nel config
  resta un `<div>` che non finge di essere toccabile. Volutamente NON
  un CTA pieno: fondo `--sats-soft` col bordo ₿ da 1.5px e testo
  `--sats-text` (token, quindi chiaro e scuro gratis), niente ombra
  piena — l'arancione pieno resta del «+ Vendi» e dei bottoni
  d'acquisto, che non devono avere rivali. La risposta del server la
  legge `caricaBannerTest()` UNA volta per apertura e la tengono in
  comune cartello e fascia.
  Contatore dei pionieri (lug 2026): «830 oggetti» e «24 pionieri»
  sono un BLOCCO in colonna (`.conta-blocco`) DENTRO la riga di
  ordina+filtri, accanto ai controlli — il select è alto il triplo di
  una riga di testo, quindi la seconda riga non costa un pixel
  d'altezza alla vetrina (con o senza pionieri la prima card sta allo
  stesso posto: 371 a 360px). Il blocco a due righe SOPRA i controlli
  è stato provato e scartato, e così pure i conteggi appoggiati in
  fondo alla riga (`align-self:flex-end`): lasciavano un vuoto sopra.
  Interlinea 1.15 + gap 3px = blocco alto 31px contro i 33px del
  controllo d'ordinamento, con ~9px di bianco fra le maiuscole delle
  due righe. Resa
  compatta `.section-label.riga-conta` (numero arancione davanti,
  `::after` puntinato spento; la regola sta DOPO `.section-label`, che
  a pari specificità vincerebbe). Perché ci stia tutto a 360px: NIENTE
  emoji sui conteggi (📦 e 👥 provati e tolti, ~22px l'uno) e il
  blocco non si stringe mai (`flex:1 0 auto`) mentre a cedere è
  L'ORDINAMENTO (`min-width:0`; dal lug 2026 è un campo-bottone e non
  una select, quindi l'etichetta si accorcia coi puntini invece di
  troncare la voce del menu) — l'etichetta cresce, «830 RISULTATI» è
  più larga di «14 OGGETTI», e non deve mai finire sotto ai controlli.
  «Pionieri» e non «utenti»: in rodaggio è un club. Il numero è `COUNT(*)` sugli
  utenti con cache di 60s (`conta_pionieri`) e viaggia nella busta
  della PRIMA pagina di `/api/listings` accanto a `totale` e
  `conteggi` (nessun giro di rete in più, lo vede anche l'anonimo);
  è GLOBALE, non segue categoria né ricerca. Interruttore
  `CONTATORE_UTENTI` nel config (acceso di serie): spento, in DEMO o
  con un server vecchio la chiave non arriva e `renderPionieri()` non
  disegna la riga (e il blocco torna a una riga sola, com'era prima
  che i pionieri esistessero).
  Campanello dei nuovi iscritti (lug 2026): `avvisa_nuovi_iscritti()`
  avvisa i MODERATORI di ogni arrivo — mai il canale pubblico (il nome
  di chi si iscrive non si annuncia in piazza; i traguardi li racconta
  Andrea a mano). NIENTE coda in memoria come i post: il filo
  dell'acqua è la colonna `registrato` e a ogni giro d'orologio (10
  min, che è anche la finestra di raggruppamento) si legge chi è
  arrivato da `_ultimo_giro_iscritti` in poi — così copre da sola tutte
  e quattro le porte (Mini App, login web, nativo Nostr, /start del
  bot) e quelle di domani, senza ganci dentro l'autenticazione; il
  primo giro dopo l'avvio ARMA soltanto (un riavvio salta un battito,
  mai raffiche di recupero) e i confronti sono a secondi interi sui due
  estremi, quindi nessuno si perde né si ripete. Regola del drenatore
  promo, stessa `SOGLIA_AGGREGA`: fino a 3 un messaggio ciascuno (nome
  + @username + porta d'ingresso, `html.escape` che le notifiche sono
  HTML), oltre UN aggregato che non nomina nessuno; tetto
  `AVVISI_ISCRITTI_MAX_ORA` (6) sui SINGOLI, l'aggregato passa sempre.
  `TRAGUARDI_PIONIERI` (50/100/250/500/1000) dedotti dai dati senza
  stato: scattano solo nel giro in cui `prima < soglia <= totale`. Il
  conto del messaggio NON usa `conta_pionieri` (la sua cache di 60s
  direbbe «siamo in 24» mentre presenti il 25°). Interruttore
  `AVVISI_ISCRITTI`.
  Sollecito degli incassi fermi (lug 2026): un ordine 'confirmed'
  senza metodo d'incasso riceveva UNA sola notifica — ignorata, i
  sats restavano congelati nel silenzio. Ora l'orologio
  (`sollecita_incassi`) bussa al venditore ogni
  SOLLECITO_INCASSO_GIORNI (7; 0 = spento) con importo e strade
  (address o invoice); l'attesa riparte da MAX(aggiornato,
  sollecito_incasso_il). Dopo SOLLECITO_INCASSO_MAX (4) solleciti
  ignorati, UNA segnalazione 🧊 ai moderatori e poi silenzio: il caso
  e' in mani umane (contatore oltre il tetto = mai piu' riproposto).
  Colonne `ordini.sollecito_incasso_il`/`solleciti_incasso`
  (migrazione idempotente). Qui i sats non si muovono mai, solo
  parole; notifiche DOPO il commit, fail-open nell'orologio.
  Polso degli ordini per i moderatori (lug 2026):
  `polso_ordini_admin(riga)` manda una riga quando un ordine nasce
  (🛒 in verifica_pagamento, sats appena in cassaforte) o si chiude
  (✅ released, ⚖️ disputa vinta dal venditore — `ordini.disputata`
  decide la faccia —, ↩️ rimborso al compratore), sempre col conto
  degli ordini ancora aperti = stati fuori da
  creato/annullato/released/refunded. Il segnaposto {aperti} si
  riempie con replace, MAI format (i titoli possono avere graffe).
  Solo titolo e importi, mai nomi. Interruttore AVVISI_ORDINI_ADMIN,
  fail-open totale; a ~60 utenti il tempo reale basta, col volume si
  aggreghera' (pattern del drenatore promo).
  Redesign «mercatino di paese» (lug 2026, da Claude Design, solo
  CSS/markup): palette in `:root` — crema #FAF4E4, inchiostro #23282C,
  arancio ₿ #F7931A con i toni `--sats-deep/-text`, verde escrow
  #1B8B54, viola Nostr, oro distintivi; font Baloo 2 (titoli e logo) +
  Nunito (testi) + JetBrains Mono (numeri). Linguaggio: bottoni-pillola
  con ombra piena 0 3px 0 che si abbassano su :active (terziari =
  testo sottolineato, `.btn.link`/`.danger-ghost`); card annuncio
  «Etichetta» (cartellino prezzo ruotato −2° a cavallo della foto,
  `.tag-price` dentro `.ph-wrap`); il tratteggio verde è il SIGILLO
  dell'escrow e compare solo lì: `.escrow-zone` nel dettaglio (badge
  flottante «🔒 pagamento protetto»; il vecchio trucco
  `:first-of-type` è morto con la coppia d'acquisto — Acquista è
  arancio per classe), il richiamo `.bc-recinto` sulla barra
  d'acquisto e `.vault` del
  dettaglio ordine (step corrente = cerchio tratteggiato). Il «🔒
  escrow» è USCITO dalle card: la rassicurazione è la riga
  `.trust-line` sotto la searchbar e sopra la griglia del negozio.
  Logo = lockup `.bmark` (B che diventa ₿ con due pseudo-elementi);
  in topbar desktop è markup vero `.nav-logo` (il vecchio
  `nav::before` testuale non esiste più) e dall'ago 2026 TORNA AL
  MERCATINO: da desktop è la convenzione di ogni sito, e la strada
  c'era già — `vaiEsplora()`, la stessa del tab, che riporta alla
  radice madre con la categoria a «Tutto» e il ramo spento (mai un
  `go('esplora')` secco: si atterrerebbe su una vetrina ancora
  filtrata con la nav accesa su Sfoglia). Resta un `<div>` con role e
  tabindex e NON un `<button>`: `nav button` è il selettore delle
  VOCI — CSS e la spazzata di `go()` — e il logo non è una voce.
  Sotto i 768px è display:none, quindi è desktop per costruzione, e
  in testata mobile il logo sta già su Esplora. Badge stati: `refunded` ha
  la SUA classe grigia (non più il verde di released). Distintivi:
  tessere d'oro per i guadagnati, 2 colonne (non le 3 del mockup:
  le descrizioni sono contenuto vero). Stato vuoto con CTA
  «+ Metti in vendita» (riusa `go('vendi')`) e conteggio «N oggetti»
  nel `section-label` (entrambi concordati). Restano fuori (logica
  nuova, respinta): filtri negli Affari e riga «Prossimo:» nei
  distintivi. Dal mockup sono invece ENTRATE (lug 2026, dopo la dark
  mode) le medagliette accanto al nome nella card venditore del
  dettaglio (oggi la sfilza `.sfilza`, dati da `venditore_distintivi`,
  vedi distintivi; la vecchia `.chip-fiducia` non esiste più). La
  pillola-contatore «🏅 N/M» accanto al lockup è vissuta poco: i
  tester l'hanno bocciata e al suo posto (lug 2026) c'è il tasto
  Profilo `.avatar-btn` — il TAPPO del barattolo: `assets/tappo.jpeg`
  (128px, ritagliato con Pillow sul diametro così il cerchio
  inscritto di border-radius coincide col bordo e l'arancione del
  fondo sparisce negli angoli; rotta esplicita, regola 3) reso tondo
  da border-radius+cover, con sotto il tappo disegnato in CSS
  (gradienti radiale+conico mascherato ad anello) come ripiego
  onerror, e sopra l'iniziale dell'utente in Baloo scura con alone
  chiaro (spread sul nome: le emoji iniziali non si spezzano);
  due istanze come la pillola di prima (testata mobile,
  topbar desktop in coda alle voci), accese da `renderAvatar()`
  ovunque tranne che in VETRINA anonima (in demo c'è: il Profilo
  esiste). Micro-anello d'oro `.oro` col primo distintivo guadagnato,
  anello arancione `.attivo` quando la vista è il Profilo (che non ha
  più voce in nav: `go()` accende il tappo). Come l'etichetta prezzo,
  il metallo del tappo resta chiaro anche col tema scuro. Con Profilo
  in testata la nav è scesa a 3 voci (Esplora · Vendi+ · Affari, il +
  al centro geometrico). Sempre dal feedback dei tester (lug 2026):
  la searchbar è un `<form>` senza bottone «Cerca» — si cerca col
  submit, cioè Invio/lente della tastiera (`enterkeyhint=search`),
  placeholder «Cerca su Barattolo…», MAI rimettere un ascoltatore
  keydown sull'Invio (doppia ricerca), e dentro il campo a sinistra
  c'è la lente decorativa `.q-lente` (emoji sbiadita con
  grayscale+opacity, grigia in entrambi i temi); il banner web arancione ha la
  ✕ «ho capito» (`chiudiBarraWeb`, hint `barraweb` nel solito
  `localStorage['barattolo_hint']` — chiuso una volta, mai più su
  quel dispositivo; Esci resta nel banner finché visibile e comunque
  nel Profilo). Festa dei sats: all'apertura di un
  ordine released, monete ₿ con fisica da confetti dal messaggio di
  chiusura (`festaSats`: 20 al venditore, 10 mini al compratore,
  ~1.5s, rAF legato al tempo + rete di sicurezza sull'overlay, spenta
  con prefers-reduced-motion; una volta per ordine e dispositivo in
  localStorage['barattolo_festa'], il patto degli hint). Asset del
  brand (lug 2026): `assets/mascotte.jpeg` (480px) e
  `assets/barattolo.jpeg` (256px), JPEG su fondo arancione ₿ pieno
  resi a tessere arrotondate (niente scontorno), serviti da rotte
  esplicite stile /vendor con cache 1 giorno (regola 3 aggiornata).
  Il barattolo è favicon e iconcina del lockup (header e topbar); la
  mascotte fluttua (floaty, spenta con reduced-motion) negli stati
  vuoti — ripiego sull'emoji 🫙 via onerror+sibling CSS se l'immagine
  non arriva, es. demo da file://. La hero di Esplora (SOLO ≥768px,
  dentro Telegram non c'è) usa invece `assets/barattolo-hero.png`:
  PNG scontornato con alpha, niente tessera, drop-shadow sulla
  sagoma, rotazione −6° e floaty.
  Dark mode «mercatino di sera» (lug 2026, solo miniapp.html): UN solo
  blocco `html[data-tema="scuro"]` in testa al CSS rimappa i token —
  niente doppioni sotto media query, perché è il JS a risolvere SEMPRE
  il tema effettivo (la media query non vede il tema di Telegram).
  Fondo bruno caldo #211A10/card #2C2517 (mai nero piatto), `--ink`
  diventa crema, arancio ₿ e oro invariati (protagonisti), verde/viola
  ricalibrati, contrasti AA verificati. I vecchi colori fissi sono
  token con doppio valore: `--header-bg`, `--nav-bg`, `--ph-a/b`
  (placeholder foto), `--ship/warn/off-bg` (badge stati),
  `--trust-note/sub`, `--step-line`, `--tile-off`, `--toast-bg/text`
  (il toast si INVERTE: crema su fondo scuro), `--ink-soft`, `--desc`,
  `--shadow-card/hover`; `--on-ink`/`--on-trust` sono il testo sopra
  i fondi `--ink`/`--trust` pieni (bianco in chiaro, scuro al buio:
  MAI `#fff` fisso sopra quei fondi). L'etichetta prezzo `.tag-price`
  resta di carta CHIARA anche al buio (valori fissi, il token
  `--paper` non esiste più: un cartellino vero non cambia colore di
  notte, e il prezzo deve staccare). Restano fissi di proposito: il
  finto QR del paySheet (che NON è un QR vero: pattern decorativo CSS
  ink-su-bianco, e chiaro deve restare), i `#fff` sui fondi arancio
  pieni, gli accenti pesca e oro. Scelta utente: cassetto «🌗 Aspetto»
  nel Profilo (pillole Auto/Chiaro/Scuro, `.tema-pill`), preferenza in
  `localStorage['barattolo_tema']` (pattern del toggle valuta, default
  auto); «auto» = `tg.colorScheme` SOLO con initData vero (nel browser
  lo stub di Telegram mentirebbe, il patto di esportaDati), altrimenti
  `prefers-color-scheme`, con ascoltatori `themeChanged` e matchMedia
  (MQL tenuta in costante: certi WebKit la buttavano col GC). Snippet
  anti-flash inline nell'head prima del paint; `applicaTema()` aggiorna
  anche `<meta name="theme-color">` e `tg.setHeaderColor/
  setBackgroundColor`. Levetta in testata (lug 2026): cerchietto
  `.tema-btn` accanto al tappo (testata mobile + topbar desktop, il
  pattern delle due istanze del tappo; nella tab bar mobile è
  nascosto) — 🌙 col tema chiaro, ☀️ con lo scuro, un tocco alterna
  via `alternaTema()` = una riga su `setTema(temaEffettivo()…)`:
  stessa memoria e stesse pillole del Profilo, che passano su
  Chiaro/Scuro (Auto resta selezionabile solo dal Profilo; da Auto
  il primo tocco parte dal tema effettivo del momento). Icona e
  tooltip li aggiorna `applicaTema()` (mai divergenti dalle
  pillole); giratina dell'icona solo con prefers-reduced-motion
  assente. C'è SEMPRE, anche in VETRINA anonima (il tema è di chi
  guarda): il vecchio «in vetrina vale auto e basta» non è più vero.
  Scudo anti-XSS: helper `esc()` (vicino a `fmt`) — OGNI testo scritto
  da un utente che entra in un template `innerHTML` DEVE passarci
  (titoli, descrizioni, zone, nomi, corrieri, tracking…); username e
  npub che finiscono dentro stringhe JS negli onclick passano invece
  dal filtro-alfabeto in `mapListing`/`mapOrder` (l'entity-encoding lì
  non basterebbe). Obbligo nato col cantiere NWC: in localStorage vive
  una credenziale di spesa.
  Compra subito (NWC): la stringa `nostr+walletconnect://` incollata
  nel profilo (scheda Profilo) vive SOLO in `localStorage['barattolo_nwc']`
  del dispositivo, MAI trasmessa al server (stessa filosofia della nsec
  solo-in-pagina: il secret NWC può spendere, fino al budget scelto nel
  wallet — la UI consiglia di impostarlo). Al collegamento `infoNwc()`
  valida la stringa con una STRETTA DI MANO vera: chiamata `get_info`
  via NIP-47 (prova relay, secret e cifratura insieme), tentando
  nip04 (default storico) e poi nip44; una risposta d'errore del
  wallet conta comunque come connessione viva. L'evento info kind
  13194 è solo un suggerimento per la cifratura (tag `encryption`):
  Coinos e altri NON lo pubblicano (verificato lug 2026), mai
  pretenderlo. Log diagnostici `🟪 [nwc]` in console. `clientNwc()` è il
  gemello NIP-47 del bunker NIP-46: richieste kind-23194 cifrate sul
  relay del wallet, risposte 23195 agganciate per tag `e` = id della
  richiesta (il bunker usa msg.id). `compraSubito()`: conferma
  esplicita → ordine+invoice IDENTICI al flusso manuale → poll su
  LNbits subito attivo (è LUI la fonte di verità del successo, mai la
  risposta del wallet) → `pay_invoice`. Wallet muto o in errore =
  ripiego sul paySheet con la STESSA invoice e lo stesso ordine (mai
  doppioni; reaper 30 min per i non pagati). Bottone ⚡ solo con
  wallet collegato e mai in DEMO/VETRINA; senza wallet tutto è come
  prima.
  Vista negozio: il blocco venditore nel dettaglio è cliccabile →
  profilo + griglia dei suoi annunci (card riusate via `cardHTML`);
  all'avvio `avvia()` legge `/negozio/...` da `location.pathname` e
  apre direttamente il negozio; bottone condividi = clipboard + toast.
  Dettaglio annuncio (lug 2026, feedback tester): bottone condividi
  `.share-btn` sulla foto (cerchietto di carta, anche sul segnaposto
  emoji, MAI in DEMO) → `condividiAnnuncio()`, ripieghi a scalare:
  con initData vero prima il canale di Telegram (la WebView NON ha
  navigator.share) — `tg.shareURL` se il client lo offre, poi
  `tg.openTelegramLink` su t.me/share/url (selettore chat) — e fuori
  da Telegram `navigator.share`, clipboard+toast, link nel toast
  (anche senza clipboard: mai il silenzio);
  il link è `GET /annuncio/{id}` (rotta gemella di /negozio,
  serve miniapp.html no-cache; regola 3 aggiornata), il JS legge
  l'URL con `apriAnnuncioDaUrl()` (pattern di apriNegozioDaUrl,
  chiamata in avvia E avviaVetrina: per gli anonimi apre il
  dettaglio in vetrina con l'invito; annuncio sparito = toast e si
  resta in Esplora). Il link t.me/startapp è rimandato: servirebbe
  la Mini App nominata su BotFather e il link web copre già tutti.
  Galleria del dettaglio coi pallini stile Vinted (`.foto-dots`,
  via il vecchio badge 📷 N): uno per foto in basso al centro,
  l'attivo pieno, aggiornati sull'evento scroll della striscia
  scroll-snap già esistente; con una foto sola non esistono.
  E CON UNA FOTO SOLA LA STRISCIA NON È UNA STRISCIA (classe `.una`,
  lug 2026, da un bug vero: gli annunci a foto singola scorrevano di
  lato portandosi dietro tutta la pagina, col testo che slittava come
  in una vista desktop). Restava un contenitore scorrevole
  (`overflow-x:auto`) con lo snap acceso ma senza niente da scorrere —
  misurato, `scrollWidth == clientWidth` — quindi il trascinamento
  orizzontale non lo consumava nessuno e si INCATENAVA all'antenato
  fino alla viewport. NON era un overflow: la pagina non sborda in
  nessuno dei due casi (verificato, 0px). Ora a una foto niente
  overflow e niente snap, più `overscroll-behavior-x:contain` sulla
  striscia — che è la stessa cosa detta dove appartiene, mentre il
  `none` sull'html (vedi il gesto di aggiornamento) è la cintura.
  Pallini e bottone condividi vivono SULLA foto: colori fissi
  (bianco/carta+inchiostro), identici in chiaro e scuro.
  IL TESTO DELL'UTENTE NON PUÒ ALLARGARE LA PAGINA (lug 2026, da due
  annunci veri importati da Nostr che si trascinavano di lato col dito
  sul CORPO dell'annuncio): una parola lunga senza spazi non ha nessun
  punto dove andare a capo, esce dal suo riquadro e allarga il
  DOCUMENTO. Misurato a 375px con un token da 60 caratteri: titolo
  +324px, riquadro venditore +129, descrizione +43. Un URL e una
  chiave prodotto NON sbordano — hanno `/` e `-`, dove il browser sa
  spezzare —, quindi la rete serve solo per il token continuo.
  `overflow-wrap:break-word` sta sul CONTENITORE `.detail-body` e non
  sui tre figli, perché si EREDITA: copre anche il campo che qualcuno
  aggiungerà lì dentro fra sei mesi (stessa rete dei nomi delle
  categorie in Sfoglia). MA NON BASTA DOVE C'È UN FLEX, ed è la parte
  che si dimentica: `.seller .who` è un figlio flex e un figlio flex
  non scende mai sotto il proprio contenuto (`min-width:auto`) — la
  parola si spezzava e la SCATOLA restava larga, +129px col testo già
  sistemato dappertutto. `min-width:0`, lo stesso rimedio del comune
  nella riga meta della card. In griglia la pagina non sbordava già
  (l'`overflow:hidden` del clamp), ma il titolo veniva tagliato a metà
  della prima riga con la seconda vuota e senza puntini.
  Dettaglio immersivo (lug 2026): via il bottone statico sopra la
  foto — il «Torna al mercatino» è il cerchietto di carta
  `.back-float` in alto a sinistra sulla foto (gemello del condividi,
  c'è SEMPRE, anche in DEMO e sul segnaposto emoji) e la foto 1:1
  sale a filo dello schermo. Un tocco sulla foto apre il LIGHTBOX
  `#lightbox`: foto intera mai ritagliata su fondo scuro, pinch e
  trascinamento coi pointer events (le dita in una Map,
  touch-action:none sul palco, capture sotto try/catch), rotella e
  doppio click da desktop, swipe tra le foto coi pallini SOLO a zoom
  1 (ingrandito il dito muove la foto), ✕/tap fuori/Escape per
  chiudere. Vanilla puro, zero librerie; lo zoom (clamp 1–4) tiene
  fermo il punto toccato e la clamp del translate non fa mai perdere
  la foto; body senza scroll a lightbox aperto.
  Barra d'acquisto al posto della tab bar (lug 2026, modello Vinted):
  nel dettaglio di un annuncio COMPRABILE la tab bar sparisce e al suo
  posto compare `#barraCompra` — «Acquista» NUDO (ARANCIO ₿
  `.btn.orange`, il CTA di casa: il verde è del recinto tratteggiato
  che lo avvolge, vedi il richiamo escrow più sotto) + «Fai
  un'offerta» (ghost neutro, senza icona); i bottoni della barra sono
  RETTANGOLARI col
  raggio del riquadro venditore (`border-radius:var(--radius)` in
  `#barraCompra .btn`), non più pillole. Gemella della nav per
  costruzione (position fixed, `--nav-bg`, blur, safe-area, z-index 30
  e altezza allineata: 62px contro 61, nessun salto di layout). La
  regia è `aggiornaBarraCompra(view)`, chiamata da `go()` a ogni cambio
  vista — così copre gratis il ritorno dal negozio e la riapertura del
  dettaglio quando una lampo scade, e uscendo la tab bar torna da sola
  (la classe è `body.con-barra`, tutta la resa vive nel CSS). Nasce
  SOLO su annuncio non proprio e `stato==='attivo'`: altrimenti resta
  la tab bar. I bottoni chiamano `startBuy`/`apriOfferta` TAL QUALI —
  le guardie stanno già lì, quindi in VETRINA la barra c'è e apre il
  foglio-invito; con un accordo accettato il tasto Offerta si spegne
  come in pagina. Dalle correzioni del lug 2026 la barra è NUDA:
  «Acquista» senza prezzo né strada (`cifraBarra` e `NOMI_VIA` non
  esistono più — il conto vivrà nella pagina dedicata del cantiere
  successivo, oggi lo dicono il foglio del varco e il paySheet), e
  attorno al SOLO Acquista c'è il RICHIAMO DELL'ESCROW: contorno
  tratteggiato verde `.bc-recinto` (stesso verde e tratteggio del
  recinto in pagina) col lucchettino `.bc-lucchetto` a cavallo del
  bordo in alto a sinistra — per questo il bottone dice «Acquista»
  senza 🔒: il lucchetto sta sul bordo, come la flag del recinto,
  mai due volte. I due tasti della barra sono GEMELLI (metà e metà,
  stessa forma e misura, offerta a sinistra) e PIATTI: dentro la
  cornice tratteggiata l'ombra piena 0 3px 0 mangiava il respiro in
  basso e la faceva sembrare scentrata — niente ombre nella barra,
  la cornice ha 3px d'aria uguali su ogni lato.
  GEMELLI DAVVERO (lug 2026, feedback di Andrea: l'arancio veniva
  fuori 24px più stretto e 10 più basso, e sembrava un tasto minore).
  Due cause, tutte e due da ricordare: 1) il tratteggio era un
  `border` con `padding`, che si mangiava 5px per lato — ora è un
  `outline` con `outline-offset:3px`, che NON occupa layout, quindi
  il bottone dentro il recinto è grande esattamente quanto il vicino;
  2) le basi flex erano a 0, e con la base a zero il padding (e il
  bordo del ghost) si sommano FUORI dalla base — la stessa lezione
  già pagata sui bottoni Applica/Azzera del pannello Filtri. Ora le
  basi sono al 50% (con `box-sizing:border-box` globale la base È la
  misura finale) e col multi-pezzo diventano 60/40 a favore
  dell'arancio, che lo stepper vuole spazio: si spostano le BASI e
  non il `grow`, perché a spazio già pieno decide lo shrink, che
  segue la base. Il lucchettino sta un filo DENTRO l'angolo
  (`top/left:-12px` contro il tratteggio a -5): centrato sul vertice
  uscirebbe dalla barra. Il padding della barra (12px sopra, 8 sotto)
  è l'aria del lucchettino e del tratteggio, e l'altezza resta quella
  della nav — 61px esatti col pezzo singolo.
  «Acquista» ha il testo un gradino più grande degli altri bottoni
  (17px nel recinto, 16 in barra: è il CTA principale dell'app), e in
  barra lo stepper non porta margine — con la scritta e il chip
  centrati insieme, un margine in più spingeva «Acquista» a 7px dal
  bordo sinistro.
  IL VARCO È DIVENTATO LA PAGINA (ago 2026): il foglio «Come vuoi
  riceverlo?» — nato lug 2026 da una domanda di Andrea, la barra
  comprava con la strada decisa in silenzio — NON ESISTE PIÙ, e con
  lui sono morti `apriFoglioConsegna`, `scegliConsegnaFoglio`,
  `cifraVia`, `setConsegnaScelta` e `consegnaEsplicita` (nella pagina
  la scelta è esplicita per costruzione). La transizione era
  dichiarata fin dalla nascita del foglio; il flusso vivo è LA PAGINA
  D'ACQUISTO qui sotto. Resta vero e va ricordato il patto del foglio
  di PAGAMENTO: `startBuy` crea ordine E invoice con la consegna già
  cotta dentro (`spedizione_sats` e `cambio_ordine` si fissano alla
  creazione) — una scelta lì arriverebbe dopo la invoice, ed è per
  questo che la scelta vive PRIMA, nella pagina.
  LA PAGINA D'ACQUISTO (ago 2026, il cantiere che chiude la lacuna
  del costo invisibile): `view-acquisto`, la cassa dell'app — senza
  tab bar come il riepilogo del pacco, colonna 100dvh col fondo vero
  (`.ctrl-fondo` col margin-top:auto: il primo bottone può anche non
  esserci — il ⚡ senza wallet — e il fondo resta il fondo).
  L'ORDINE NASCE SOLO DA QUI: `compraDaBarra` (barra e recinto) porta
  SEMPRE alla pagina, anche con una strada sola — è lì che il costo
  si vede PRIMA della invoice; il ⚡ «Compra subito» NWC è USCITO dal
  recinto del dettaglio e vive in pagina (stesso body, stesse
  cifre del preventivo). Le ECCEZIONI sono le aste (il vincitore ha
  già pagato: `apriPunta`, `scegli_consegna_ordine` e
  `crea_ordine_pagato` intonsi, sentinella in CI) e i client vecchi
  in cache, per cui il server tiene il default silenzioso di sempre.
  Dall'alto: gli articoli (card singola o strip del set) · la
  CONSEGNA a vie-radio — 🤝 ritiro · 🏠 spedizione a casa ·
  «Spedizione a locker/punto di ritiro» con l'armadietto disegnato
  (13 ago 2026, decisione di Andrea in DUE giri: prima «locker»
  secco, che superava il camioncino del 12 — il 🚚 diceva la famiglia
  ma non la differenza con «a casa», che qui è tutta la scelta; prima
  ancora c'era la scatola, che diceva la taglia del pacco — poi la
  CORREZIONE: «locker» era PIÙ STRETTO DEL VERO, la via serve
  QUALUNQUE punto della rete e con Poste la rete è in gran parte
  tabaccherie col banco. I MARCHI sono stati scartati: Fermopoint è
  di BRT, Punto Poste di Poste, InPost ha i suoi — nominarne uno
  confonderebbe gli altri due terzi dei venditori. La doppia formula
  dice il caso migliore, il locker che si apre col solo codice, senza
  escludere nessuno — ed è quella che usa Subito.
  L'ETICHETTA della via è SENZA l'articolo, ed è una misura e non
  sciatteria: col «un» fa 276px nel font della via e a 320 la colonna
  ne dà 258, cioè due righe; senza fa 255 e sta su UNA riga a
  320/360/375, misurato — la PROSA delle notifiche tiene «a un», che
  lì è grammatica e non larghezza. Quando le cifre di casa/punto
  divergono la colonna si stringe e il nome può andare a capo lo
  stesso: a-capo pulito, dichiarato, mai un overflow.
  Non esiste un'emoji del locker: `ICO_LOCKER` è un SVG a
  currentColor come le icone della nav, inchiostro in [2,22], e va
  AVVOLTO in uno `<span>` con l'etichetta perché `.via-nome` è un
  flex in COLONNA — nudo, il disegno finirebbe SOPRA il testo.
  La formula vive in NOVE siti — pagina Paga, i tre hint dell'ordine
  (compratore senza punto, venditore col punto, venditore in attesa)
  più la riga della coda fermi, notifica «Hai venduto» e gemella,
  nota ai moderatori in disputa, campagna spedizioniere — mentre
  «punto di ritiro» RESTA dove indica il POSTO fisico: il bottone e
  il campo «Indica il punto di ritiro», la tariffa del form Vendi, il
  banner del pacco, la busta di consegna — lì «locker» sarebbe più
  falso, non più chiaro) ·
  💾 codice online, SOLO le
  offerte, ordine fisso di PRESENTAZIONE (il default lo dice
  `viaDefault`, vedi sotto) — dove la cifra a
  destra è il SOLO COSTO DI SPEDIZIONE (decisione di Andrea, ago
  2026: le pillole col totale si leggevano come «costo di
  spedizione» con dentro l'oggetto — il totale lo dice IL CONTO, che
  segue la via scelta: mai due totali in pagina; ritiro e codice
  online non spediscono e non portano cifra, lo 0 di casa/punto dice
  «gratuita» in grassetto, il patto della spedizione gratuita).
  E LE CIFRE COMPAIONO SOLO QUANDO DICONO QUALCOSA (ago 2026,
  decisione di Andrea): casa e punto che costano UGUALE = cifre
  MUTE, il costo lo dice già il conto sotto; diverse = restano,
  perché sono l'informazione che fa scegliere. Il giudice è
  `costiVieUguali`, e le sue regole sono la parte da non
  ammorbidire: si confronta il costo FINALE (la promessa gratis che
  azzera, o una tariffa dichiarata 0, riaccende le cifre da sola —
  «gratuita» contro una cifra si mostra anche a tariffe di base
  uguali) e SOLO nella stessa unità NATIVA — euro con euro
  (`spedizione_eur` su tutt'e due), sats puri con sats puri (niente
  `stima`): MAI attraverso una conversione, perché un'uguaglianza al
  cambio di adesso è di un istante e la invoice riconverte (5000
  sats e 2,75 € possono fare «≈ 5003» oggi e divergere domani — le
  cifre restano, col loro ≈). Lo zero è zero in ogni valuta (due
  gratis = mute), `fallback_casa` è un'IDENTITÀ e non un confronto
  (stessa tariffa per costruzione: è il caso comune, ed è quello che
  si voleva ripulire), e una via `cambio_assente` non si confronta —
  la viva mostra la sua cifra, il verso in cui sbagliare è mostrare
  · il campo del punto (DENTRO il riquadro della sua via, vedi il
  sesto giro sotto; il VARCO MAPPA — dal quarto giro c'è
  SEMPRE: con la rete dichiarata la sua mappa, senza tutte e due più
  la riga onesta) · le note
  oneste («Spedisce con InPost», la regola asimmetrica del digitale,
  il ≈ dei listini EUR) · IL CONTO in righe (Prezzo · Commissione
  «in promo» · Spedizione della via scelta · Protezione se >0 ·
  Totale, la grammatica `.ctrl-riga`/`contoRighe` condivisa col
  riepilogo del pacco) · «PAGA» in fondo (secondo giro, decisione di
  Andrea: da quel bottone parte la fattura, e il nome lo dice —
  «Acquista» resta sui varchi che PORTANO alla pagina: barra, recinto
  e il riepilogo del pacco).
  E IL FONDO È APPICCICATO (13 ago 2026, decisione di Andrea): «Paga»
  resta in vista mentre si scorre — `#view-acquisto .ctrl-fondo` è
  STICKY e mai fixed, ed è la parte da non rovesciare: niente
  matematica di viewport (dentro Telegram le misure mentono, la
  lezione della tastiera dei fogli), e un elemento sticky OCCUPA il
  suo spazio in layout, quindi a fine scorrimento l'ultima riga del
  conto non è mai coperta — il fiato sopra la barra lo dà già il
  margin-bottom del conto. Fondo opaco con blur, riga di confine e
  safe-area sono DELLA BARRA (il pattern di #barraPacco e della nav)
  e il padding-bottom del corpo passa a lei, o a fine pagina ci
  sarebbero due safe-area impilate. SOLO la pagina Paga: il riepilogo
  del pacco tiene il fondo di sempre (sentinelle su tutte e tre le
  righe). Col ⚡ NWC collegato si appiccica il fondo INTERO — è
  atomico, la lezione di «Altri oggetti» — e costa più schermo:
  dichiarato.
  IL DEFAULT DELLA VIA È IL PUNTO DI RITIRO (ago 2026, decisione di
  Andrea che AFFINA il 12 ago — precedenza punto → casa → ritiro →
  digitale). DUE STRATI DI PERCHÉ, e vanno tenuti tutti e due. Il
  primo (12 ago, correzione d'eredità coi numeri): alla nascita della
  pagina il default era «la prima strada viva», cioè il RITIRO —
  l'ordine di PRESENTAZIONE delle radio colato nel default, non una
  decisione — e misurato in produzione 51 attivi su 82 erano
  «entrambe», con 35 badge 🚚 sopra un ritiro preselezionato che
  nessuno aveva scelto: la SPEDIZIONE batte il ritiro, e resta vero
  (il punto È spedizione). Il secondo (ago 2026): fra le due
  spedizioni vince il PUNTO, perché è la via già marcata
  «Consigliato» — default e consiglio devono dire la stessa cosa,
  invece di indicare due strade diverse — e la casa espone
  l'indirizzo, il contrario di ciò per cui esiste la busta di
  consegna. Con la tariffa PUNTO morta per cambio muto subentra casa:
  la spedizione resta il default. Il giudice è `viaDefault`, il
  ripiego sulla prima viva copre lo storico (pseudo-via '') e ogni
  via futura fuori elenco — coi DUE chiamanti, la pagina vera e il
  ramo DEMO, così demo e vera non divergono (sentinelle su giudice e
  chiamanti, torturate). La via già scelta si conserva sui ± come
  sempre; l'ordine di PRESENTAZIONE delle radio NON cambia, quindi su
  «entrambe» la selezionata è la TERZA della lista — guardato a
  schermo a 320/360/375 nei due temi: la selezione è il riquadro
  pieno arancio e non si legge come un difetto. L'ARGOMENTO-CONTRO,
  trovato in sola lettura prima di decidere e RISOLTO dal cassetto
  (vedi il quinto giro del punto, sotto): col campo del punto sempre
  aperto, punto-default avrebbe trasformato la pagina da «conto da
  leggere» in «modulo da compilare» — per pagare col default serviva
  digitare un indirizzo a mano. Il campo chiuso dietro il bottone è
  ciò che rende il default sostenibile: chi cambia default riguardi
  anche il cassetto, sono UNA decisione in due pezzi.
  LA STRADA SCARTATA (12 ago), e va tenuta perché torna in mente:
  «nessuna preselezione con Paga spento finché non scegli». Costava
  un conto senza via che mente (articolo+protezione, il totale di
  nessuna strada), il gate sul ⚡ NWC (senza, `corpoConsegna()` vuoto
  fa nascere l'ordine col default del server, mai scelto) e un tocco
  in più su ogni acquisto multi-via — per un problema che il default
  giusto toglie da solo.
  LO STEPPER NELLA PAGINA (12 ago 2026, chiesto da Andrea: l'invito
  dice «ancora 1 pezzo → −10%» e il pezzo si deve poter aggiungere LÌ,
  non tornando alla scheda). Il ± sta nella card articoli
  (`stepperMini` con chiamate SUE, `acqPasso` — il modello del foglio
  rifornimento, mai `setQta(±1)`), e le quattro dichiarazioni:
  1) OGNI TOCCO RIFÀ IL CONTO SUL SERVER — quella pagina È il conto —
  e l'anti-raffica NON è un debounce (scartato nel carrello: litiga
  con chi sale in fretta) ma la RIASSEGNAZIONE di `acqDati`:
  l'oggetto nuovo è il token, le risposte dei tocchi precedenti
  muoiono sulla guardia `acqDati !== d0` che `caricaPreventivo` aveva
  GIÀ — mai `acqDati.qta = n`, la mutazione in place farebbe vincere
  l'ultima risposta ad ARRIVARE invece dell'ultima CHIESTA (c'è la
  sentinella). Cinque tocchi = cinque preventivi (SELECT pure): costo
  accettato, provato in raffica — vince l'ultimo.
  2) FATTURA GIÀ GENERATA: il paySheet resta SENZA stepper e mostra le
  cifre congelate; chi chiude il foglio, tocca ± e ripreme «Paga»
  incontra la RIPRESA di sempre — quantità diversa = richiesta
  diversa → lapide e fattura nuova, zero righe nuove su quel percorso.
  3) IL TETTO È LO STOCK, il clamp della scheda, e al limite SILENZIO:
  il bottone è `.off` e non si tocca, mai un toast.
  4) I BADGE SEGUONO coi numeri del SERVER, e l'attesa SI DICHIARA:
  `.acq-attesa` (opacity .55) su conto, badge e vie — le cifre che la
  quantità muove, supplemento compreso — mentre lo stepper resta
  vivo. IL VELO È RITARDATO di ~180ms, ed è la scelta guardata a
  schermo (la riserva di Andrea era giusta): secco, lampeggerebbe a
  OGNI tocco su rete viva; così sul caso normale non si vede mai, su
  rete lenta compare una volta — 180ms dopo l'ULTIMO tocco della
  salita, perché ogni tocco riarma il timer — e resta fermo finché il
  conto vero non arriva. Mai numeri vecchi spacciati per freschi, mai
  un lampeggio. Il timer muore in testa a `renderAcquisto`: il render
  È la risposta.
  IN PIÙ, trovato dal vivo e non dal piano: l'indietro RI-MOSTRA la
  scheda senza ri-renderizzarla, e lo stepper di là restava al numero
  vecchio — `setQta(0)` è il SINCRONIZZATORE (a delta zero riusa la
  regia in-place della scheda — stepper del dettaglio e della barra,
  badge spedizione, etichetta offerta — senza duplicarne i selettori),
  e `qtaScelta` resta UN solo stato. E L'ERRORE SU UN ± NON BUTTA LA
  PAGINA: il ramo distruttivo («← Torna») resta al solo primo carico;
  a conto buono già in mano si RIPIEGA (`acqRipiega`) — toast onesto e
  la quantità TORNA a quella dell'ultimo preventivo vero, mai numeri
  nuovi su un conto vecchio. Un ± non azzera la via già scelta (si
  conserva se ancora viva). Con l'ACCORDO lo stepper non nasce (la
  quantità è pinnata, resta il «× N»), con stock 1 nemmeno; in DEMO
  il ± ricalcola `preventivoDemo` sul posto, senza rete.
  E STA FUORI DAL TITOLO (12 ago 2026, bug dal campo il giorno stesso
  del deploy — annuncio 192): `.acq-tit` è un line-clamp a DUE righe
  con `overflow:hidden`, e stepper e «× N» dell'accordo — appesi in
  coda al titolo DENTRO quel div — finivano sulla terza riga,
  tagliata: nel DOM coi loro onclick vivi, ma invisibili. Ora titolo
  e `qtaUi` vivono nella colonna `.acq-col`: il titolo tiene tutta la
  sua larghezza col suo clamp — che NON si allenta, fa il suo lavoro
  sul testo — e lo stepper scende su una riga sua sotto (la strada
  «fratello in riga» è stata scartata misurando: avrebbe ristretto il
  titolo a ~67px a 360). LA LEZIONE È LA MISURA: si vedeva a 360px e
  NON a 375 — il collaudo del cantiere aveva guardato 320 e 375, e il
  difetto abitava esattamente nella larghezza saltata, che è pure
  quella di mezzo mondo Android. Il 360 era già «la larghezza di
  riferimento del progetto» per i conti di layout: da oggi (decisione
  di Andrea) ENTRA anche nel giro degli screenshot di ogni cantiere,
  accanto a 320 e 375 — tre misure, mai più due. E la regola generale
  è quella già pagata in «Altri oggetti»: un contenuto ATOMICO e
  interattivo non si appende mai in coda a un testo clampato.
  IL GIUDICE DEL «≈» È UNO, `cifraCtrl` (ago 2026, bug visto dal
  telefono: il ≈ compariva su ENTRAMBE le valute — le condizioni
  sparse sono il modo in cui è nato). La regola: il ≈ sta SOLO sulla
  valuta convertita, mai su quella NATIVA del prezzo, mai sullo zero
  — annuncio sats = sats esatti ed euro ≈, annuncio EUR = euro
  esatto e sats ≈. L'euro nativo lo dice il SERVER (il client
  mostra, mai calcola): `_eur_effettivo` (pura, il MIN lampo/accordo
  sul lato euro) → `articolo_eur`/`articolo_unitario_eur` nel
  preventivo e `spedizione_eur`/`totale_eur` per strada — il
  `totale_eur` esce SOLO quando è esatto (articolo nato in euro,
  tariffa in euro o zero, protezione zero: un totale misto non ha
  una valuta nativa e resta ≈ in tutte e due le viste, e nel set
  l'euro nativo esiste solo se OGNI riga è nata in euro). La doppia
  conversione non solo mentiva col ≈: sbagliava di un centesimo
  (38,49 per un listino da 38,50). Sentinelle: un solo
  `function cifraCtrl`, la resa convertita vive solo lì dentro.
  `prezzoParte` (vetrina/dettaglio) aveva già la regola giusta e
  resta suo. Toggle €/₿ in testata
  (ridisegno dal preventivo in CACHE, mai un secondo fetch — e
  ATTENZIONE alla trappola pagata qui: l'edit di setValuta era
  atterrato su rinfrescaViste, due righe adiacenti identiche).
  IL CONTO È DEL SERVER: `POST /api/orders/preventivo` (mono o set,
  stesso body di compra) — le guardie di compra in SOLA lettura
  (nessun INSERT, nessuna invoice, nemmeno il timbro dell'offerta
  scaduta: sentinelle in CI) e il conto PER OGNI strada disponibile
  in una chiamata, così cambiare pillola non rifà la rete. LA PROVA
  REGINA del collaudo: preventivo == compra a parità di via, al sat,
  perché passano ENTRAMBI dalle quattro pure del conto
  (`_unitario_effettivo` col MIN lampo/accordo, `_tariffa_dichiarata`,
  `_sped_in_sats`, `_conto_ordine` — accanto alle pure dell'asta,
  stessa ragione: prove in CI senza chiavi). La commissione nel conto
  è INFORMATIVA e mai nel totale (resta sottrattiva sull'incasso del
  venditore); una tariffa ancorata all'euro senza cambio spegne la
  SUA strada col motivo (`cambio_assente`), mai un 503 che spegne
  anche il ritiro — quello resta solo per l'articolo EUR. Annuncio
  storico (consegna '') = pseudo-via '' e il body non porta consegna.
  Errore del preventivo = pagina col messaggio e «← Torna», mai muta;
  in DEMO vale `preventivoDemo` (stima client, DICHIARATA in pagina);
  in VETRINA l'invito di sempre. Navigazione da vista interna:
  chiave = annuncio (mono) o 'set|origineId', ricostruzione con
  guardia e ripiego su Esplora; `verificaOrdine` a pagamento riuscito
  azzera `acqDati` e `ctrlPrev` col pacco.
  LE DUE TARIFFE DI SPEDIZIONE (decisioni di Andrea): il venditore
  dichiara il costo verso casa (le colonne di sempre) e quello verso
  un PUNTO DI RITIRO — colonne `annunci.spedizione_punto_sats/_eur`
  gemelle byte-per-byte delle prime (stessa semantica di valuta:
  sats fisso, euro ancorato) più il FLAG
  `spedizione_punto_dichiarata`, che distingue «non dichiarato» da
  «dichiarato 0 = gratis» (una sentinella -1 avrebbe sparso guardie
  >=0 ovunque). RETROCOMPAT: il costo unico già dichiarato vale per
  ENTRAMBE le strade finché il venditore non rifinisce
  (`_tariffa_dichiarata`, e il preventivo lo dice con
  `fallback_casa`). La dichiarazione è la PRESENZA di una chiave nel
  payload, mai il valore: vuoto ≠ zero — il form manda SEMPRE
  `spedizione_punto_dichiarata` (0 = campo svuotato apposta), così in
  modifica svuotare toglie la dichiarazione mentre il client vecchio,
  che non manda nessuna chiave, la CONSERVA (il pattern dello stock).
  Nel form Vendi il secondo campo sta sotto il primo e SEGUE il suo
  toggle di valuta (un interruttore solo per i due costi); import CSV
  con la colonna `spedizione_punto` IN CODA al modello (per nome: i
  file di ieri intonsi); la modifica FIRMATA non tocca le colonne
  punto per contratto (l'evento Nostr non le porta: le azzererebbe a
  ogni sync — commento sull'UPDATE e sentinella «un solo UPDATE»).
  IL PUNTO NON ESCE SU NOSTR: tariffa interna del checkout,
  `tag_commercio` ed `evento_annuncio` ciechi per sentinella
  (imperfezione dichiarata: un client Nostr vede la sola tariffa
  casa).
  IL SUPPLEMENTO PER PEZZO (ago 2026, caso dal campo: il riso da 4 kg
  venduto a sacchi con la spedizione di UNO solo dichiarata — chi ne
  comprava dieci pagava la spedizione di uno, e ci rimetteva il
  venditore). Terza tariffa, colonne `annunci.spedizione_extra_sats/
  _eur`, gemelle delle altre nella semantica di valuta (stesso toggle,
  sats fisso o euro ancorato) ma SENZA il flag delle punto, ed è la
  differenza da ricordare: là vuoto e zero dicono cose diverse (vuoto
  = vale la casa), qui «supplemento 0» e «nessun supplemento» sono la
  stessa cosa. UNO SOLO per annuncio, valido per casa E per punto
  (decisione di Andrea): dipende dall'OGGETTO, non dalla destinazione
  — un sacco di riso pesa uguale ovunque vada. È PER ANNUNCIO e non
  per negozio, a differenza di sconto carrello e spedizione gratis,
  per la stessa ragione.
  LA REGOLA, in una riga — **la spedizione più cara fa da base, e ogni
  altro pezzo aggiunge il suo supplemento**:
  `max(base_i) + Σ(qta_i × supp_i) − supp_del_vincitore`. 10 sacchi
  (base 6, supp 3) = 6 + 30 − 3 = 33; riso + collanina = 6 + 4 − 3 =
  7. Il MONO con quantità NON è un caso a parte: `base + (q−1)×supp`
  esce da sé. Pareggio nel MAX: vince `(base, supp)` lessicografico,
  cioè a parità di base si assorbe il supplemento più GRANDE, a favore
  di chi compra — *quale* riga vinca dipende dall'ordine della lista,
  il TOTALE no, e va detto perché qualcuno vorrà aggiungere un terzo
  criterio «per sicurezza».
  DUE PROPRIETÀ, provate e non sperate: a supplementi tutti a ZERO il
  risultato è IDENTICO al MAX di sempre (la retrocompat a costo zero),
  e il totale non scende MAI sotto quel MAX (`Σ qta·supp ≥ supp_w`
  perché `qta_w ≥ 1`) — nessun venditore incassa meno di prima.
  IL MAX NON È IL MINIMO, ED È GIUSTO: A(base 10, supp 0) + B(base 9,
  supp 5) fa 15, non 9 — partire da B darebbe meno di quanto costa
  spedire A da solo. Il primo che lo nota lo chiamerà bug; non lo è.
  IL CUORE È UNA PURA SOLA, `_sped_pacco(righe, via, cambio)` accanto
  alle altre del conto, che restituisce un DICT (sats|None, eur
  nativo, stima, supplemento, pezzi) e non una tupla — con cinque
  campi posizionali il terzo chiamante li scambia. Prima il MAX era
  scritto DUE volte (`_compra_set` e `_strade_preventivo`) più una
  terza forma nel mono di `compra()`: tenerne tre in pari col
  supplemento era il modo di farli divergere. `righe` è
  `[(annuncio, qta)]`, e LA QUANTITÀ NON È UN DETTAGLIO —
  `_strade_preventivo` riceveva i soli annunci, quindi il preventivo
  mono avrebbe detto la spedizione di UN pezzo e la invoice quella di
  dieci; col supplemento a zero i due numeri coincidono, ed è
  esattamente perché quel buco poteva restare a lungo invisibile. Nel
  set le righe si prendono da `richieste`, MAI zippando
  `tutti.values()` con `richieste.values()`: l'ordine di `tutti` viene
  dalla SELECT IN (...) e le quantità finirebbero sull'annuncio
  sbagliato in silenzio.
  L'EURO NATIVO ha una condizione da leggere due volte: «contribuisce
  in sats», NON «eur == 0». Una tariffa che vale ZERO non contribuisce
  e non deve azzerare il nativo (zero è zero in tutte le valute),
  mentre una con sats>0 nata in sats sì — scritta nell'altro modo,
  quello che viene in mente, un supplemento a zero farebbe comparire
  il ≈ su tutti i carrelli. E si converte PRIMA e si moltiplica DOPO,
  il patto di `_unitario_effettivo`: qui vale doppio, perché il numero
  finisce in `ordini.spedizione_sats` e `_righe_ordine` lo sottrae.
  LA DIVISIONE A RITROSO DEL MONO RESTA ESATTA, ed è il motivo per cui
  questa funzione si può fare mentre lo sconto carrello sul mono no:
  il supplemento finisce dentro `spedizione_sats`, che è una delle
  colonne SOTTRATTE da `_righe_ordine`, mentre `sconto_sats` sta
  fuori. Vale anche sul ramo della RIPRESA e con la spedizione gratis
  (che azzera la colonna: si sottrae 0). Per la stessa ragione NIENTE
  colonna nuova su `ordini` — l'aritmetica quadra già, e una colonna
  nella tabella del denaro per un dato ornamentale è ciò che questo
  file sconsiglia per `sconto_pacco_criterio`; la riga «spedizione per
  N pezzi» viaggia come CHIAVE nella risposta (`supplemento_sats`,
  `pezzi`) del preventivo E di compra/_compra_set, e quella seconda
  metà non è opzionale: senza, la riga comparirebbe nella pagina
  d'acquisto e sparirebbe nel paySheet un istante dopo, che si legge
  come «il prezzo è cambiato» un attimo prima di pagare.
  LA PROMESSA GRATIS OFFRE TUTTO, supplemento compreso: offrire la
  sola base romperebbe `sped_gratis_sats XOR spedizione_sats` e
  vorrebbe una colonna nuova. Quando scatta, il supplemento si azzera
  con la tariffa, o la pagina direbbe «gratuita» e sotto «spedizione
  per 10 pezzi».
  IL `None` NON SI PARA CON UN RAMO MA CON UNA PROVA: i due blocchi
  del cambio nominano TUTTE le tariffe ancorabili all'euro, e una
  sentinella incrocia quell'elenco con le colonne `spedizione*_eur`
  vere di `annunci` — la quarta tariffa che qualcuno aggiungerà lo
  sente dalla CI. Un retry difensivo è stato scritto e TOLTO: era
  codice morto e un terzo `raise 503` là dove la sentinella di ieri ne
  contava due, cioè un allarme che diceva la verità. Senza la
  guardia il conto esplode — `max(sped, None)` nel set, `netto + None`
  nel mono: un 500 col database aperto, non un 503 (riprodotto).
  IL SUPPLEMENTO NON ESCE SU NOSTR, per la ragione della tariffa punto
  (sentinelle), e la modifica firmata non lo tocca. Nel CSV è la
  colonna `spedizione_extra` IN CODA — le colonne di coda vuote si
  omettono, la convenzione che il modello ha già — e la riga del miele
  è quella che la INSEGNA (12 vasetti, 6,00 di base e 1,50 a vasetto:
  è il caso del riso). In `modifica()` si CONSERVA se il payload non
  la nomina, il patto della tariffa punto: il client vecchio in cache
  non sa che il campo esiste; si azzera mandando 0.
  CLIENT: terzo campo nel form sotto quello del punto, stesso toggle,
  più l'hint live «10 pezzi = X sats di spedizione» — la rete contro
  il refuso ×1000 amplificato dal ×q (nessun tetto: chi spedisce roba
  pesante ha supplementi veri alti). `spedGratis` guarda ANCHE il
  supplemento, ed è il punto in cui il cantiere poteva far mentire la
  vetrina: «il primo pezzo lo offro io» è base 0 + supplemento pieno,
  e senza quelle due condizioni la card avrebbe scritto «🚚 gratis» su
  un annuncio dove due pezzi si pagano — fail-closed, mai una
  gratuità che regge per un pezzo solo. `satsSpedPezzi` è il gemello
  client, e vive SOLO nelle stime (DEMO, foglio offerta, barra del
  carrello): il conto che si paga arriva sempre dal preventivo.
  `editListing` deduce la valuta da TUTTE E TRE le tariffe e non dalla
  sola base — con la base a 0 e il solo supplemento (o la sola tariffa
  punto) in euro il toggle tornava su sats e rileggeva euro come sats.
  NESSUN controllo nuovo del LIBRO MASTRO, e il perché va tenuto: i
  candidati non passano la domanda che decide («esiste uno stato
  transitorio LEGITTIMO in cui è falso?») o sono allarmi che non
  possono suonare — un supplemento su chi non spedisce non ha
  conseguenze (la pura si chiama solo sulla spedizione),
  `extra_sats>0 AND extra_eur>0` è legittimo sul listino EUR, e un
  supplemento su base 0 è una promessa vera. Soprattutto: un
  supplemento contato MALE la ronda non lo vedrebbe comunque, perché
  `prezzo_sats` quadra con qualunque numero dentro `spedizione_sats`.
  Il posto dove si prende è la prova regina.
  LO SPEDIZIONIERE È DEL NEGOZIO (decisione di Andrea): catalogo
  server `SPEDIZIONIERI` (InPost · Poste Italiane · Altro — NON è il
  catalogo CORRIERI del tracking né le sentinelle), colonna
  `utenti.spedizioniere` ('' = non dichiarato), endpoint
  `POST /api/me/spedizioniere` (pattern canale-notifiche), cassetto
  «📦 Come spedisci» nel Profilo con le voci da /api/me (mai
  hardcodate; in DEMO sparisce). Il compratore lo vede in pagina:
  «📦 Spedisce con InPost».
  LA VIA PUNTO SI OFFRE SEMPRE dove c'è la spedizione (secondo giro,
  ago 2026 — la decisione di Andrea che SUPERA quella del primo
  giro, «punto solo con spedizioniere dichiarato»; il perché:
  MEGLIO L'ACCORDO IN CHAT CHE LA PORTA CHIUSA). Il gate di ieri
  (400 «non spedisce ai punti» + filtro nel preventivo) è durato UN
  giro ed è morto con la sua sentinella rovesciata in CI: non deve
  tornare di soppiatto. Con la regola nuova la via punto vale anche
  per gli IMPORTATI.
  E LA SCELTA DEL PUNTO TORNA SEMPRE PRIMA DI «PAGA» (QUARTO giro,
  ago 2026 — la decisione di Andrea che ROVESCIA il terzo; il
  perché: è così che fanno Subito e Vinted, la convenzione che chi
  compra ha già nelle dita — e ciò che rende SOSTENIBILE scegliere
  un punto senza conoscere la rete è la rete di sicurezza che il
  terzo giro aveva già costruito, il campo dentro l'ordine dove il
  punto si corregge finché il venditore non spedisce). Il campo c'è
  SEMPRE nella pagina d'acquisto: con la rete dichiarata come
  sempre, con la sua mappa; SENZA rete con TUTTE E DUE le mappe e
  la riga onesta «stai scegliendo il punto senza sapere con che
  rete viaggerà il pacco — puoi correggerlo dall'ordine finché non
  spedisce». LA REGOLA VIVE NEL CLIENT (le due guardie di
  ctaAcquisto e compraSubito, senza più guardare la rete): il
  server continua a esigere il punto SOLO con la rete dichiarata,
  ed è TOLLERANZA per il client di ieri — che senza rete il campo
  non ce l'ha, e un 400 senza campo sarebbe un vicolo cieco — non
  la regola del prodotto. IL PERCHÉ DEL TERZO GIRO, che resta vero
  e ha perso solo il braccio di ferro con la convenzione: il
  venditore non deve ragionare di corrieri quando pubblica, e il
  compratore non deve indovinare la rete di un punto che non sa —
  la risposta nuova a quel problema non è nascondere il campo ma
  dirlo (la riga onesta) e rendere la scelta correggibile. La riga
  «il punto preciso lo indicherai dopo l'acquisto» è morta col suo
  flusso, e la sentinella in CI è rovesciata: non deve tornare.
  E DAL QUINTO GIRO IL CAMPO STA DIETRO UN BOTTONE (ago 2026, col
  punto diventato il DEFAULT della via): il campo a testo libero non
  sta più aperto in pagina — lo espande «Indica il punto di
  ritiro» (dal 13 ago 2026 NUDO, senza il 📍: il riquadro che lo
  ospita ha già il locker della via, e due icone nello stesso
  riquadro sono una di troppo — l'ha perso anche la riga compatta
  del punto scritto), così la pagina apre su un conto da leggere e
  non su un modulo da compilare, che era l'argomento contro il punto
  come default. È una RIGA ESPANSA e non un foglio, deliberato: niente
  registrazione in closeSheet né pila di navigazione, il campo resta
  adiacente a vie e conto, e il commento VARCO MAPPA resta vero
  parola per parola (il selettore futuro sostituirà lo stesso
  contenitore, il contratto — un testo in `acqDati.punto` — non
  cambia). LO STATO È `acqDati.puntoAperto`, MAI il DOM: il corpo si
  ridisegna a ogni ±/toggle/cambio via, e uno stato solo-DOM si
  richiuderebbe sotto le dita (i ± riassegnano con `{...d0}`, il flag
  sopravvive gratis). TRE STATI del contenitore `#acqPuntoCampo` su
  via punto: chiuso e vuoto = il bottone; chiuso col punto SCRITTO =
  la riga compatta «📍 {punto} — Cambia», che lo MOSTRA e riapre il
  campo PRECOMPILATO — mai ricominciare da capo; aperto = il campo di
  sempre con label, mappa e hint locker. L'indirizzo lungo nella riga
  compatta cede LUI coi puntini (figlio flex con `min-width:0`, la
  lezione del comune in card) e il «Cambia» non si stringe mai:
  misurato a 320 coi 120 caratteri pieni, zero overflow. LE
  TRANSIZIONI: la scelta ESPLICITA della radio punto a campo vuoto
  apre e mette il fuoco (si scrive subito, il focus di sempre), col
  punto già scritto resta la riga compatta senza tastiera; lasciando
  la via il cassetto si richiude. E LE DUE GUARDIE di «Paga»/⚡ a
  punto vuoto APRONO il cassetto PRIMA del fuoco (`apriPuntoAcquisto`,
  l'apertura vive in un posto solo): mai il fuoco su un campo
  nascosto — la vecchia forma `focus(); return;` è vietata da una
  sentinella. All'APERTURA della pagina invece NESSUN fuoco e nessuna
  tastiera: il default preseleziona il punto ma la digitazione arriva
  solo quando serve. Il campo DENTRO l'ordine (`puntoRitiroInp`) è
  una regione separata e non è cambiato di una riga.
  E DAL SESTO GIRO IL CASSETTO VIVE DENTRO IL RIQUADRO della via
  punto, sotto il «Consigliato» (ago 2026, decisione di Andrea): sta
  attaccato alla scelta a cui appartiene, e scegliendo un'altra via
  se ne va con lei — si disegna solo a via punto SELEZIONATA, e
  tutti e tre gli stati abitano lì dentro, una casa sola (anche la
  riga compatta: due case per lo stesso cassetto sarebbero il
  difetto che il trasloco toglie). LA MECCANICA da non rompere: la
  radio che lo ospita è un DIV `role="radio"` e non più un
  `<button>` — HTML vieta interattivi annidati, la lezione dello
  stepper dentro Acquista — e i tocchi restano separati per
  PROPAGAZIONE: il tocco sul riquadro seleziona la via, il cassetto
  (`#acqPuntoCampo`) la ferma con stopPropagation sul suo
  contenitore, così bottone, input e link mappe non riselezionano
  mai — un click dentro l'input, senza quel freno, rifarebbe il
  render sotto le dita di chi scrive. La tastiera ha la guardia
  gemella (`event.target===this` nell'onkeydown del DIV): l'Invio
  sul bottone interno non deve anche scegliere la via. Il layout: il
  riquadro ospite va in colonna (`.con-cassetto`) e la riga
  nome+cifra (`.via-riga`) tiene il layout dei fratelli, che restano
  `<button>` a una riga — le regole di `.via-opzione` non si
  toccano. Sentinelle in CI su tutte e quattro le righe.
  E LA NOTIFICA UNA-TANTUM (`avvisa_spedizioniere_mancante`,
  nell'orologio): ai venditori con annunci attivi che spediscono e
  senza spedizioniere — «da oggi i compratori possono scegliere il
  punto (locker): dichiara la rete nel Profilo, eviti gli accordi in
  chat». Il timbro è la colonna `utenti.avvisato_spedizioniere`
  (sopravvive ai riavvii) e si scrive PRIMA degli invii, il patto
  del cooldown della lampo: un errore di rete può perdere un avviso
  di cortesia, mai raddoppiarlo. UNA volta per venditore, per
  sempre; chi arriva dopo ha anche la riga discreta nel form Vendi
  (`#sellSpedizioniereHint`, solo a chi spedisce senza rete
  dichiarata).
  IL PUNTO NELL'ORDINE, SENZA UN VALORE NUOVO DI consegna_scelta (il
  precedente è anche_digitale, ortogonale): la strada punto è
  `consegna_scelta='spedizione'` + `ordini.punto_ritiro` (il testo)
  + `ordini.via_punto` (terzo giro: la STRADA — serve perché «via
  punto, punto non ancora indicato» deve esistere, e il testo da
  solo non lo sa dire) — timer, solleciti e la derivazione
  dell'unitario per sottrazione restano veri PER COSTRUZIONE, la
  tariffa scelta finisce in `spedizione_sats` come sempre. Il body
  di compra porta `spedizione_via` ('casa' default | 'punto',
  whitelist con sentinella) + `punto_ritiro` (testo libero del
  compratore: strip, spazi collassati, tetto 120 — il CLIENT lo
  esige sempre prima di «Paga», il 400 del server resta sul solo
  ramo con rete dichiarata per tolleranza verso il client di ieri,
  sentinella sul conteggio x2; il patto del ricontrollo senza await
  ha la sua sentinella in CI).
  IL PUNTO SI DICE UNA VOLTA SOLA, E DOVE SERVE (ago 2026): sotto il
  prezzo c'era anche il punto GIÀ scelto, mentre due dita più sotto lo
  stesso testo si può ancora CORREGGERE (e il venditore ce l'ha nel
  suo pannello «Spedisci») — quella riga era il dato ripetuto accanto
  al posto in cui si tocca. Via; resta il solo INVITO a indicarlo
  quando ancora non c'è, che non è il dato ma il cartello che ci
  porta.
  E RICOMPARE NEL BANNER DEL PACCO appena il venditore spedisce
  (`puntoBanner`), perché lì il campo si chiude e il pannello del
  venditore sparisce: senza quella riga chi ha comprato non avrebbe
  più da NESSUNA PARTE l'indirizzo dove andare a ritirare. Sta nel
  banner del pacco e non altrove perché è lì che si guarda «dov'è il
  mio pacco», e la frase è girata a chi legge («Il tuo punto di
  ritiro» / «Punto di ritiro dell'acquirente»), la regola del
  riquadro verde.
  E IL BANNER È DEL PUNTO, E DI NIENT'ALTRO (ago 2026, dal campo):
  diceva anche «Spedito con X — tracciamento Y», che è parola per
  parola il passo «Oggetto spedito» dentro il recinto due dita più su
  — un doppione, e per giunta quello che si legge dopo. Ora nasce sul
  solo `o.puntoRitiro`, e la prova che chiedeva «il banner nasce anche
  senza tracciamento» ha CAMBIATO LATO: senza punto non nasce affatto
  (la riga di ieri esisteva perché un ordine spedito senza codice non
  si portasse via il punto insieme al banner — oggi il punto è l'unica
  cosa che lo fa nascere, quindi quel caso è coperto per costruzione).
  LA TRACCIA DELLA CORREZIONE DEL MODERATORE HA SEGUITO IL CODICE, ed
  è la riga che si perde per distrazione svuotando un banner: sta nel
  passo, dove la vedono ENTRAMBE le parti come prima.
  MA IN DISPUTA IL CODICE NON SI LEGGEVA AFFATTO (ago 2026, dal
  campo, e va PRIMA della voce qui sotto perché la corregge): lo
  stepper ha DUE array di passi — il corso normale e la disputa — e
  quello della disputa non ha mai avuto un passo per la spedizione,
  quindi da `dispute` in poi il tracciamento spariva per tutti e tre
  (chi compra, chi vende, e il moderatore, che è quello che ne ha più
  bisogno: lì il codice è una PROVA). Ora c'è, dopo il deposito e
  prima dell'apertura — l'ordine in cui le cose sono successe — e solo
  se un tracciamento esiste: una disputa aperta da 'locked' o una
  consegna a mano non hanno niente da mostrare. Il bottone di
  @trackbot resta fuori da solo (`trackbotPossibile` guarda
  shipped/delivered), quindi lì il codice esce come TESTO: a pacco
  contestato non si offre di iscriversi alle notifiche.
  `progress` È UN INDICE dentro `steps`, quindi il passo in più sposta
  di uno tutti quelli dopo (`+ (o.tracking ? 1 : 0)`): chi ne aggiunge
  un altro e si dimentica quella riga accende il pallino «adesso» sul
  passo sbagliato, che è un difetto che leggendo non si vede.
  IL SOSPETTO ERA IL FILTRO DI TRACKBOT E NON ERA LUI, ed è la parte
  di METODO da tenere: il caso arrivava come «un codice SDA da 9 cifre
  non si vede più», cioè con una causa già scritta dentro la
  segnalazione — e il filtro era nato il giorno prima, quindi
  combaciava. Riprodotto invece di dedotto: in disputa il codice
  spariva con QUALUNQUE corriere, anche con quelli che il filtro lo
  passano (InPost 24, Poste S10), e la regione dello stepper è
  identica BYTE PER BYTE a prima del cantiere trackbot. Un buco
  vecchio, visto il giorno in cui qualcuno è andato a cercare il
  codice dove serve.
  LA PROVA CHE NE RESTA È UN CENSIMENTO e non un elenco: nella strada
  che RENDE il codice — `codiceTracking` e i due rami dello stepper —
  `passaTrackbot` e `FILTRO_TRACKBOT` non devono comparire MAI, così
  un codice fuori filtro si vede comunque anche nel ramo che qualcuno
  aggiungerà fra sei mesi. La mutazione che nasconde il codice fuori
  filtro fa rosse quattro righe.
  E UN CODICE SI LEGGE COME UN CODICE (11 ago 2026, dal caso di
  Luca): quando il riquadro `📦 Spedito con … · segui il pacco →` è
  sparito — vedi il giro del punto di ritiro — la motivazione era
  giusta sul CONTENUTO (era il doppione del passo due dita più su) e
  sbagliata sul PESO: quel che restava non era lo stesso testo in un
  altro posto, era lo stesso testo senza più niente addosso, quindici
  pixel di grigio in mezzo alla prosa. Due parti di un ordine vero
  hanno cercato il tracciamento e non l'hanno trovato, pur avendolo
  davanti. Ora il codice è `<b class="mono">` nei DUE rami — mono e
  grassetto come l'aveva nel riquadro — e il doppione non torna: si
  dà peso a dov'è, non si rimette dov'era. Il peso è uguale nei due
  rami per regola CSS (`.step .mono`), o il `<b>` nudo verrebbe 900 e
  quello toccabile 800: lo stesso codice con due pesi secondo chi
  guarda.
  IL CODICE SI TOCCA DOVE SI LEGGE (ago 2026): dentro quel passo il
  tracciamento è cliccabile e porta a @trackbot, e il link a 17track
  è USCITO dall'ordine — ne resta uno solo, quello del RESO (lato
  venditore: là chi aspetta è lui e il bottone di trackbot non è suo),
  e il conto in `prove.py` lo dichiara, così se un domani ne ricompare
  uno qui la riga diventa rossa. Due strade per seguire lo stesso
  pacco sono un bivio davanti a chi lo aspetta.
  IL GIUDICE È UNO, `trackbotPossibile(o, s)`, e lo usano tutti e due
  i posti da cui ci si arriva — il bottone e il codice: due strade che
  rispondessero diverso sullo stesso codice sarebbero una che promette
  quel che l'altra nega. Le sue domande restano due (solo mentre il
  pacco viaggia, solo col tracciamento) più quella
  dell'intermediario — la «quarta» di ieri, che l'11 ago 2026 SI È
  ROVESCIATA — qui sotto. IL RUOLO NON DECIDE PIÙ (12 ago 2026,
  decisione di Andrea in due passi nello stesso giorno): era «solo
  il compratore» con la motivazione «è il suo pacco» — che valeva
  per le notifiche, non per il bisogno — poi le due parti (il
  VENDITORE segue la stessa spedizione, e verso un punto di ritiro
  deve sapere quando il pacco arriva per mandare la busta), infine
  anche il MODERATORE: nei suoi stati (le dispute) il codice è
  comunque TESTO per la regola dello stato — «a pacco contestato non
  si offre di iscriversi alle notifiche», che vale per tutti e non
  si tocca — e l'unico posto dove la porta gli si apre è lo shipped
  aperto per numero, la superficie nata proprio per i tracciamenti
  storti, dove un tocco sul codice è una DIAGNOSI (trackbot che
  risponde «non lo conosco» conferma il codice sbagliato). La prova
  che lo sorveglia chiede che nel giudice il ruolo non compaia
  affatto, o rientrerebbe di soppiatto. Dove la
  porta non c'è il codice resta TESTO: un link a vuoto è peggio di
  nessun link.
  UN'EURISTICA INCOMPLETA NON DEVE MAI TOGLIERE NIENTE (11 ago 2026,
  decisione di Andrea da un caso vero, e questa voce ROVESCIA la
  quarta domanda di ieri — «solo con la FORMA del corriere
  dichiarato»). Il motivo di allora era buono e resta vero: a trackbot
  serve il codice del CORRIERE, e quello dell'intermediario (Packlink
  & co.) è l'errore già successo. Ma IL PREZZO LO PAGAVANO I CODICI
  CHE NON CONOSCIAMO, che sono esattamente quelli su cui sbagliamo
  noi: su un Poste `281665J056083` — vero, e fuori dalle nostre due
  forme di allora — al compratore sparivano insieme il grassetto e il
  bottone, in silenzio. E `FORME_TRACKING` è dichiarata «un'euristica,
  non una verifica» che «non blocca MAI»: attraverso quella guardia
  bloccava lo stesso, per interposta persona — è il modo in cui
  muoiono le regole, non abrogate ma aggirate da un'altra strada.
  ADESSO SI TOGLIE SU QUEL CHE SAPPIAMO, NON SU QUEL CHE NON SAPPIAMO:
  il bottone c'è SEMPRE, tranne dove riconosciamo un intermediario.
  L'ASIMMETRIA DEI DANNI è tutta la ragione — un bottone che porta
  trackbot a dire «non conosco questo codice» è un fallimento
  VISIBILE, che chi legge capisce da solo e semmai ci segnala; un
  bottone che non compare è un fallimento invisibile, e non lo segnala
  nessuno. È la stessa forma del fail-safe verso la coda di
  `_vietato_bloccante`: si sbaglia dalla parte in cui l'errore si
  vede.
  `intermediarioNoto` RICONOSCE PER NOME e non per forma, che è la
  sola cosa che sappiamo con certezza: un codice di corriere non
  contiene mai la parola «packlink». Si guardano le lettere dopo aver
  tolto cifre e punteggiatura, così «PACKLINK-4471» si riconosce; il
  catalogo è tutto MINUSCOLO o la voce è morta in silenzio (il
  tracciamento si abbassa, le voci si confrontano così come sono
  scritte), e c'è la prova che lo dice.
  ONESTÀ SU COSA NON PRENDE, ed è la metà da leggere: il caso vero —
  il venditore che incolla il NUMERO D'ORDINE nudo dell'intermediario,
  senza il nome — qui NON si riconosce, e non si prova nemmeno.
  Indovinarlo dalla forma è precisamente la mossa che è costata il
  caso Poste. A intercettarlo restano l'avviso nel form della
  spedizione e la domanda di `formaTracking`, tutti e due rivolti a
  CHI IL CODICE LO STA SCRIVENDO: è lì che l'errore si ripara — con
  chi l'ha fatto e col codice sotto le dita — non togliendo qualcosa
  a chi legge. L'euristica non ha perso il suo mestiere, ha perso solo
  quello che non era suo.
  LE FORME DI POSTE SI SONO ALLARGATE SUI CODICI VERI del registro
  (`^\d{6}[A-Z]\d{6}$` e `^[A-Z]{2}\d{11}$`, da 281665J055082,
  281665J056083, JF40001609169 — tutti e tre a 13 caratteri e tutti e
  tre fuori dalle forme di prima, che conoscevano solo le cifre e
  l'S10). Scritte STRETTE sui campioni e non allargate a intuito: da
  quando l'euristica non gatea più il bottone, il suo unico mestiere è
  CHIEDERE, e una domanda in più costa un tocco mentre una forma
  inventata insegna una cosa falsa. I tre codici stanno nel collaudo,
  ed è la tortura ad averlo chiesto: senza, togliere le forme nuove
  non faceva rossa nessuna prova.
  E IL LETTORE DEL CATALOGO IN `prove.py` LEGGE A VOCI, NON A RIGHE:
  prendeva una riga alla volta, e la prima voce che ha avuto bisogno
  di due righe — Poste, appunto — è sparita dal conto senza che
  nessuna prova sui suoi codici diventasse rossa. Erano semplicemente
  smesse di girare. Adesso si taglia fra una chiave e l'altra, e una
  prova in più chiede che nessuna voce sia rimasta VUOTA. Il colore NON è il
  verde-link di casa (`--trust` sul fondo della fiducia rende 3,84: va
  bene per un ornamento, non per ventiquattro cifre da leggere) ma
  `--trust-note`, l'inchiostro di quella superficie — 8,1 di giorno e
  10,5 di sera —, e a dire che si tocca sono il grassetto e la
  sottolineatura, l'unica della pagina.
  IL PAYLOAD CADEVA SUL FILTRO DI TRACKBOT (ago 2026, risposta loro,
  e questa voce ROVESCIA quella di ieri — «cosa faccia il bot di un
  `/start CODICE` non è documentato da nessuna parte, e dalla nostra
  parte non c'è niente da riparare»): la funzione c'è dal 2018, e il
  payload lo guarda contro `^[A-Z0-9]{8,26}$` (era `{10,22}`, e i
  due bordi si sono mossi tutti e due — vedi sotto). Da riparare dalla
  nostra parte c'era eccome — si passava il codice con
  `[^A-Z0-9_-]`, cioè tenendo trattini e trattini bassi perché li
  ammette TELEGRAM nel payload, e sul filtro cadevano in SILENZIO
  (la chat si apre lo stesso e non succede niente: esattamente quel
  che si vedeva dal campo). Ora si toglie tutto ciò che non è
  maiuscola o cifra, e SI NORMALIZZA SOLO QUEL CHE VA A TRACKBOT:
  quello che si MOSTRA e quello che sta nel DATABASE restano il codice
  come l'ha scritto il venditore, che è anche una prova in disputa.
  GLI APPUNTI STANNO COL LINK E NON CON LA PAGINA (decisione di
  Andrea), ed è la riga che si sbaglia leggendo «non si tocca quel che
  si mostra»: quel testo non lo legge nessuno, ha UN mestiere solo —
  essere incollato in trackbot — quindi con un parser di chat severo
  quanto quello del payload la copia fallirebbe per la stessa ragione
  per cui falliva il link, e sarebbe lo stesso difetto entrato da
  un'altra porta. È lo stesso codice: cambia solo che non porta la
  punteggiatura che il corriere ci stampa sopra. La prova ha CAMBIATO
  LATO — chiedeva `writeText(vero)` — e accanto ne è nata una che
  tiene l'altra metà: in pagina il codice resta quello del venditore.
  IL FILTRO NON DIVENTA UNA GUARDIA DEL BOTTONE, ed è la riga da non
  ammorbidire: chi non ci rientra nemmeno normalizzato ha comunque la
  strada di sempre — incollare a mano — e togliergli il bottone
  vorrebbe dire chiudere l'unica porta che gli resta. QUALI SONO, e
  si sanno per FORMA e non per caso: dal 12 ago 2026 NESSUNA forma
  del nostro catalogo sta sotto il minimo (la più corta è 9 contro un
  pavimento di 8), quindi restano fuori solo i codici liberi di
  «Altro corriere» sotto gli 8 caratteri. Il ramo «resta fuori» della
  didascalia è diventato raro e NON si toglie: un ramo che non
  promette è meglio di uno che mente, e i bordi del filtro non sono
  nostri.
  IL TETTO ERA 22 E TRACKBOT L'HA ALZATO A 26 (11 ago 2026), ed è la
  storia da tenere perché è il modello per la prossima volta: il
  cantiere aveva MISURATO sui codici veri di produzione (una passata
  in sola lettura sul VPS: 3 InPost su 3 fuori, tutti a 24 cifre, e
  3 Poste su 3 dentro — il resto erano codici di prova), Andrea ha
  scritto a trackbot con quel numero in mano chiedendo `{10,24}`, e
  loro hanno alzato a **26**, cioè più di quanto si chiedeva: così
  rientrano anche i DHL eCommerce lunghi (`JVGL` + 22 = 26 tondi),
  che erano l'altra famiglia trovata fuori. Provato dal vivo su un
  codice InPost vero: funziona. NON si è toccato nient'altro — la
  normalizzazione andava già bene e il bottone non aveva mai escluso
  nessuno — e a cambiare è stata UNA prova, che ha CAMBIATO LATO
  («i 24 dell'InPost restano fuori» → «ci rientrano»). Era il segnale
  armato apposta, ed è servito.
  E IL 12 AGO 2026 HANNO ABBASSATO ANCHE IL PAVIMENTO, da 10 a **8**,
  SENZA CHE GLIELO CHIEDESSIMO — quindi la storia intera è MISURATO →
  CHIESTO → ACCOLTO DUE VOLTE, e tutte e due le volte più larga della
  richiesta. Ci rientrano i GLS Europe a 9 cifre, che erano l'ultima
  famiglia di corriere rimasta fuori: il filtro ha smesso di tagliare
  qualcuno. Anche qui a cambiare è stata UNA prova che ha CAMBIATO
  LATO («i 9 cifre restano fuori» → «ci rientrano»), e accanto ne è
  nata una NUOVA sotto il pavimento (sette caratteri): un bordo che si
  muove va sorvegliato dai due lati, o il giorno che qualcuno lo
  abbassa per conto nostro non se ne accorge nessuno. La sentinella
  che guarda i numeri nel giudice del bottone è passata dal letterale
  a una regex (`\{\d+,`): scritta col numero, alla seconda volta che
  i bordi si muovono smette di dire qualcosa.
  IL RAPPORTO CON UN TERZO SI COLTIVA COSÌ, ed è la parte che vale
  oltre trackbot: si misura sui dati veri, si chiede con il numero in
  mano, si tiene aperta la strada di chi resta fuori, e si scrive nel
  file cosa si è chiesto e quando — perché la prova che diventa rossa
  dica «hanno risposto» e non «trackbot ha avuto un capriccio».
  LA LEZIONE DEL GIRO, che vale oltre trackbot: davanti a un filtro
  di TERZI che ci taglia fuori, la leva non è sempre adattarsi —
  qui adattarsi avrebbe voluto dire tagliare un codice, cioè
  spedirne uno sbagliato. Si misura sui dati veri, si chiede con il
  numero in mano, e intanto si tiene la strada di sempre aperta per
  chi resta fuori. Il costo dell'attesa era zero perché il bottone
  non è mai stato gatato dal filtro.
  IL FILTRO DECIDE LE PAROLE, MAI LA PRESENZA DEL BOTTONE (11 ago
  2026, decisione di Andrea, ed è la riga da non ammorbidire — la
  frase è la stessa del giorno prima, cambia solo cosa governa). La
  didascalia sotto il bottone si SDOPPIA su `passaTrackbot`: a chi il
  bot il codice lo prende dice «apri e il codice glielo passiamo
  noi», a chi resta fuori resta l'istruzione di ieri — «il codice te
  lo copiamo negli appunti, **incollalo nel bot**». Il perché è che
  un testo unico avrebbe mentito comunque, in un verso o nell'altro:
  dire «incollalo» a tutti racconta come strada principale quella di
  riserva, e dire «ci pensiamo noi» a tutti è il fallimento
  silenzioso di ieri riscritto in italiano — e fallirebbe allo stesso
  modo, cioè senza che nessuno se ne accorga. Scartato per questo il
  testo unico che nomina tutte e due le strade: renderebbe più
  confuso il caso normale per proteggere quello raro.
  «Le notifiche te le manda @trackbot, non Barattolo» sta nei DUE
  rami: è l'onestà sul terzo, e non dipende da com'è fatto il codice.
  IL TOAST SEGUE LE PAROLE e la COPIA no: la copia si fa sempre — è
  la rete se il bot fa i capricci, e non costa niente — ma la annuncia
  solo chi ne ha bisogno. Dove il bot prende il codice non si dice
  niente: il bot che si apre col codice dentro è già la risposta, e
  un toast lì inviterebbe a fare a mano una cosa appena fatta. Dove
  resta fuori la copia È la strada, quindi si dice, e se non riesce
  si dice anche quello.
  I DUE GIUDICI VIVONO IN UN POSTO SOLO — `nudoTrackbot` (la
  normalizzazione) e `passaTrackbot` (il filtro) — e sono due perché
  i posti che li chiedono vogliono cose diverse (le PAROLE e il
  LINK), ma la normalizzazione dev'essere la stessa o si direbbe una
  cosa e se ne farebbe un'altra. `FILTRO_TRACKBOT` è una costante e
  IL SUO NUMERO È LORO: la prova lo confronta col letterale, quindi
  se qualcuno lo allarga per conto suo diventa rossa — un filtro
  nostro più largo del loro rimette esattamente il fallimento
  silenzioso da cui è partito tutto.
  La prova non rilegge la riga: ESTRAE dal sorgente la classe di
  caratteri della normalizzazione e la applica ai codici come la
  gente li scrive (minuscole, spazi, trattini, trattino basso),
  chiedendo che il payload rientri nel filtro — chi rimette il
  trattino nella classe la fa rossa. E la LEGGE dal client anche il
  filtro, invece di ricopiarlo: una seconda copia in `prove.py`
  sarebbe il posto che un giorno dice un'altra cosa.
  LA TORTURA HA TROVATO UNA SENTINELLA CHE NON POTEVA FALLIRE, ed è
  la terza volta che capita così: «il tetto è quello che dicono
  loro» era scritta come `"{10,26}" in src` e trovava il numero
  DENTRO IL COMMENTO due righe sopra la costante — allargare il
  filtro non la faceva rossa. Ora guarda la costante. Una sentinella
  si scrive rompendo il codice, non rileggendola.
  `POST /api/orders/{id}/punto-ritiro` è la RETE DI SICUREZZA: solo
  il COMPRATORE, solo su 'locked', solo sulla via punto — il punto
  scelto in pagina si CORREGGE finché il venditore non spedisce (un
  refuso, o la rete scoperta dopo), e per gli ordini nati senza (i
  client di ieri) si scrive lì la prima volta; notifica STATICA al
  venditore a ogni cambio. IL VUOTO SI RIFIUTA (400): un punto
  scritto si corregge, non si svuota mai — quindi il gate qui sotto
  non può riscattare su un ordine già compilato. E `segna_spedito`
  RESTA BLOCCATO sulla via punto finché il punto non c'è (400 che
  rimanda al campo e alla chat): DOVE SPEDIREBBE? — col quarto giro
  il caso è quasi sparito (solo ordini dei client di ieri), ma la
  guardia resta, con la conseguenza accettata che un compratore che
  non indica mai il punto tiene l'ordine fermo in 'locked', dove i
  promemoria di `sollecita_venditori_fermi` e la disputa esistono
  già. La RIPRESA
  confronta punto E via: cambiarli è una richiesta diversa =
  rinnovo (la tariffa può cambiare). Il testo attraversa la filiera
  INTERO ma mai nudo: `esc()` a ogni resa client (ordine, pannello
  del venditore), MAI interpolato nell'HTML delle notifiche server —
  il venditore riceve la coda STATICA «trovi il punto nell'ordine»
  (collaudato con virgolette, tag, emoji e a-capo dentro). Il campo
  in pagina porta il commento-VARCO MAPPA: il selettore punti delle
  API corriere sostituirà il contenitore, il contratto resta un testo
  in `acqDati.punto`.
  LA BUSTA DI CONSEGNA (ago 2026, dal campo): per ritirare a un punto
  servono il NOME che il venditore ha messo come destinatario (di
  fantasia: il corriere esige un nome, noi non raccogliamo dati veri;
  serve al banco, e a entrambi se il pacco non viene ritirato e torna
  indietro) e il CODICE di ritiro (PIN/QR). Prima viaggiavano in chat
  privata — e chi non ha username Telegram né npub non è contattabile:
  l'ordine restava bloccato, successo davvero. Ora vivono DENTRO
  l'ordine: `POST/GET /api/orders/{id}/busta-ritiro`, colonne
  `busta_nome`/`busta_codice` cifrate col TRASPORTO dei contenuti
  digitali (`_cifra_contenuto`) ma MAI con la sua semantica, ed è la
  riga da non ammorbidire: APRIRE LA BUSTA NON È UNA RICEVUTA — il GET
  è PURO (zero scritture, `consegnato` e stato intonsi, sentinelle in
  CI), `consegna_scelta` resta 'spedizione' quindi le finestre corte
  del digitale non vedono mai questi ordini per costruzione, e i sats
  si muovono solo coi bottoni di conferma di sempre.
  NIENTE GATE SU segna_spedito (decisione di Andrea, che ha ROVESCIATO
  il brief del cantiere — e il perché va tenuto perché il gate torna
  in mente): il codice arriva al venditore quando il pacco è GIÀ al
  punto, quindi col gate non potrebbe dichiarare la spedizione per
  tutto il viaggio — 1-3 giorni in cui chi ha pagato vede il nulla. I
  due momenti restano separati come nella realtà, due messaggi
  distanti giorni: «in viaggio verso il punto» alla spedizione (con la
  coda «ti avviseremo quando il codice sarà pronto»), e «il tuo pacco
  ti aspetta» al deposito — quello che conta, con la giacenza ~3
  giorni dentro. Al posto del gate: la riga «⏳ in attesa del codice»
  visibile a ENTRAMBI nell'ordine, e `sollecita_buste_ferme`
  nell'orologio (leva `PROMEMORIA_BUSTA_GIORNI` 3, 0 = spenta; cadenza
  e tetto RIUSATI da PROMEMORIA_CONFERMA_* come le sorelle; ancora
  `spedito_il`, colonne SUE `sollecito_busta_il`/`solleciti_busta`;
  squilla SOLO il venditore — il compratore vede già l'attesa e ha i
  suoi bottoni — e al tetto 🧊 ai moderatori, poi silenzio).
  LA DEDUP DEL SEGNALE D'ARRIVO, per il caso raro dei due momenti
  coincidenti (codice immediato, spedizione da un punto):
  `MSG_BUSTA_PRONTA` è UNA costante e parte da UNA sola delle due
  strade — il deposito su 'locked' è SILENZIOSO e a parlare è
  segna_spedito, che col `busta_il` già pieno dice «ti aspetta» al
  posto di «in viaggio»; il deposito su 'shipped' parla da sé. Mai il
  doppione, e c'è la prova.
  IL DEPOSITO è del venditore su 'locked'/'shipped'/'dispute' —
  'dispute' è deliberato: un PIN sbagliato si corregge SOLO da lui,
  perché il moderatore la busta NON LA LEGGE MAI, da nessuna strada
  (a differenza del contenuto digitale: il GET autorizza le sole
  parti, e l'estraneo riceve la stessa risposta dell'ordine
  inesistente — niente oracolo). `busta_il` resta il PRIMO deposito;
  le correzioni si contano e si timbrano (`busta_correzioni`,
  `busta_corretta_il`, aggiunta di Andrea): in disputa la nota ai
  moderatori dice «depositate il X, poi corrette N volte (ultima il
  Y)» o «MAI depositate» — sempre e solo fatti, mai il contenuto.
  Campi obbligatori INSIEME, 400 espliciti sui limiti (80/1000) e MAI
  il troncamento silenzioso del punto_ritiro: un PIN troncato è un PIN
  rotto. Journal con sha256 troncata + lunghezze, il pattern del
  digitale. Lo strip di /api/orders poppa nome e codice; `busta_il` e
  le correzioni ESCONO (sono il SE e il QUANDO). Il libro mastro
  guadagna «busta fuori contratto» (flag/nome/codice si scrivono nello
  stesso UPDATE e solo sulla via punto); da NON aggiungere, e verrà in
  mente: «shipped via punto senza busta» — è lo stato NORMALE del
  transito, e sarebbe falso anche su tutto il pregresso. Le ASTE non
  hanno la busta per costruzione (scegli_consegna_ordine non scrive
  mai via_punto, dichiarato in _strade_asta). Client:
  `pannelloBustaRitiro(o)` accanto al pannello digitale, cache
  `bustaLetta`, «👁 Mostra» SENZA confirm (non è la rivelazione:
  leggere un bigliettino non muove niente), tutto sotto esc(), admin
  senza nemmeno il bottone.
  LA PAGINA ORDINI RISTRUTTURATA (ago 2026): filtro «Solo attivi»,
  pillole [Tutti|Acquisti|Vendite], la foto vera al posto del 📦, e il
  NASCONDERE degli affari conclusi. Le definizioni, dichiarate:
  ATTIVO = stato NOT IN (released, refunded, annullato) — un
  consegnato non confermato è attivissimo, una disputa pure,
  confirmed/refund sono il limbo che aspetta una invoice; annullato
  sta coi conclusi (è una lapide ≤1h del reaper). NASCONDIBILE =
  released/refunded E BASTA, gli unici stati ASSORBENTI: quindi «un
  nascosto che torna a muoversi» NON ESISTE per costruzione — il
  feedback della controparte può ancora arrivare e l'ordine RESTA
  nascosto (un feedback non è un movimento; lo si ritrova da
  «mostrali»). La parità dei due elenchi server↔client (gate e ✕) è
  sorvegliata da prove.py.
  I FILTRI SONO TUTTI CLIENT-SIDE e vivono SOLO in renderOrders:
  `orders` resta INTERO (openOrder fa orders.find senza guardie — deep
  link, ritorno post-pagamento, ripristino d'identità) e la WHERE di
  /api/orders NON si tocca (è una catena di OR senza parentesi: un AND
  in coda si legherebbe all'ultimo OR). Stato per SESSIONE (variabili
  ordini*, mai localStorage), markup dei controlli STATICO in
  view-affari: la tirata di aggiornamento riscrive solo #ordersList e
  le scelte sopravvivono da sole. All'apertura: Tutti + filtro spento
  (deciso da Andrea) = la lista di sempre, meno i nascosti. Le righe
  'admin' (dispute da moderare) passano solo con «Tutti». LIMITE NOTO,
  dichiarato (Andrea): coi filtri lato client la lista continua a
  SCARICARE anche gli ordini nascosti — nascondere alleggerisce la
  vista, non la risposta. Ai numeri di oggi va benissimo; chi un
  domani vedrà una lista lenta guardi qui invece di sospettare del
  filtro.
  LA DATA DELLA RIGA È QUELLA DELL'AFFARE (ago 2026, dal campo): era
  `aggiornato`, cioè il timbro dell'ULTIMO MOVIMENTO — e così un
  ordine del 7 agosto sembrava di oggi appena il venditore segnava la
  spedizione. Adesso è `creato`, che è il pagamento a meno di
  mezz'ora e non si muove più (gli unici scrittori sono l'INSERT e la
  resurrezione di `controlla_annullati`) — e senza ORARIO: a colpo
  d'occhio in una lista non serve a nessuno e ruba spazio al titolo.
  L'ORARIO RESTA DOVE MISURA UNA FINESTRA, ed è il criterio: la
  RIVELAZIONE del codice digitale («Rivelato il 10 ago, 14:32»), da
  cui contano le ORE_CONFERMA_DIGITALE, e il DEPOSITO della busta di
  ritiro, da cui si conta la giacenza al punto — più, in disputa, la
  prova di quando è successo. Il «tracciamento corretto il …» invece
  ha già la sola data, e va bene: lì non parte nessun conto.
  E IL BADGE DELLA LISTA DICE IL FATTO, non il posto: «Sats
  depositati» (`STATES.locked.label`, l'unico sito), mentre la testa
  del riquadro verde resta «Sats nel deposito di garanzia», che
  risponde a un'altra domanda — cos'è successo contro dove sono
  adesso. Uniformarle è l'errore che verrebbe naturale: c'è la prova
  che restino due.
  IL CENSIMENTO DELLE ALTRE DATE, perché non fosse un'eredità: il
  DETTAGLIO non ne mostra nessuna (è un fatto, non una svista: lì il
  quando lo raccontano lo stepper e i pannelli); nelle NOTIFICHE non
  compare mai la data di un ordine — le uniche sono `_quando_scade`
  (una scadenza futura) e il «Depositate il …» della busta, che
  hanno colonne loro; nell'EXPORT CSV la colonna `data` resta
  `aggiornato` ED È LA SCELTA GIUSTA, perché lì escono solo
  released/refunded e per la contabilità conta il giorno in cui i
  sats si sono mossi, non quello dell'acquisto.
  IL NUMERO DELL'ORDINE SI VEDE (ago 2026, dal campo: un utente
  segnala un problema e per ritrovare il suo ordine bisognava
  chiedergli il nome dell'oggetto e cercarlo nel database). È
  `ordini.id`, cioè LO STESSO numero che il moderatore batte in «Apri
  un ordine per numero» e lo stesso che il bot scrive già in qualche
  notifica («ordine #88») — un'identità sola, o mostrarlo non
  servirebbe a niente, ed è la prima cosa da riverificare se un
  domani nascesse un secondo riferimento.
  NEL DETTAGLIO sopra il titolo, dentro la stessa colonna della foto
  (`numeroOrdine`, `.ordine-testa .ord-col`): a titolo di una riga
  costa ZERO pixel di pagina — la foto è alta 48 e il titolo ne
  occupa 23, quindi lo spazio c'era già. Porta LA PAROLA («Ordine
  #88»), che è quel che dice cos'è quel numero a chi lo legge la
  prima volta; nella RIGA della lista resta NUDO («#88»), in testa
  alla meta, che lì il contesto lo dice il posto e incolonnato sotto
  le foto fa una colonna di riferimenti che si scorre con l'occhio.
  SI TOCCA SOLO NEL DETTAGLIO, ed è la regola di sempre: ciò che
  AGISCE vive dentro l'ordine, e la riga ha già il suo tocco (apri) e
  la sua ✕ — un terzo bersaglio su una card alta 60px si sbaglia e
  basta.
  NEGLI APPUNTI VA IL NUDO «#88» e non la frase intera: chi copia lo
  incolla dentro un messaggio che sta già scrivendo, e «…con l'ordine
  Ordine #88» è il modo in cui una comodità diventa un intoppo; il
  cancelletto invece resta, che un numero solo in mezzo a una chat
  non si riconosce come un riferimento. Se la copia non riesce
  (contesti non sicuri, permessi negati) il numero va NEL TOAST: mai
  far credere che sia negli appunti quando non c'è — la regola del
  codice di @trackbot, e il ramo si prova per davvero, in headless la
  clipboard è negata di default.
  IL COSTO IN LISTA È MISURATO e non stimato, sui 19 ordini veri del
  database di collaudo: **zero righe in più a 360, 375 e 390**, una
  riga in più a 320 — dove la meta era già a tre righe, perché la
  colonna del testo lì è larga 98px — e sulle 4 righe corte a 430.
  Il numero non allunga mai la riga da solo: la allunga il fatto che
  quella colonna è strettissima, che è una condizione preesistente.
  E IL `min-width:0` DELLA TESTA È TRASLOCATO SULLA COLONNA, che ora
  è lei il figlio flex: sull'h2, che flex non vede più, non farebbe
  niente, e senza una parola lunga senza spazi allarga la PAGINA
  (misurato: 375 → 780px). La sentinella storica si è spostata con
  lui invece di sdoppiarsi — una riga, una guardia.
  DUE «#N» CONVIVONO NEL MONDO, e va saputo prima di uniformarli: il
  MEMO della invoice LNbits è `Barattolo escrow #{id}` e quell'id è
  l'ANNUNCIO, non l'ordine — lo vede chi paga, nel suo wallet, e lo
  vede l'admin nel registro di LNbits, dove è anche il filo con cui
  si riconciliano gli incassi orfani. Non si tocca: cambiarlo
  spezzerebbe quel metodo.
E L'ORDINE DELLA LISTA SEGUE LA DATA (decisione di Andrea, subito
  dopo): `/api/orders` ordina per `o.creato DESC, o.id DESC` e non
  più per `aggiornato`. Le due cose vanno INSIEME — la data
  dell'affare sopra un ordinamento per movimento fa sembrare la lista
  disordinata, perché un ordine vecchio che si muove salta in cima
  esibendo la sua data vecchia. Così invece la lista è «i tuoi
  affari, dal più recente», e a dire che qualcosa si è mosso c'è già
  il badge di stato; a tenere su quel che aspetta chi guarda, il
  filtro «solo attivi».
  L'ID IN CODA È IL PAREGGIO e non un ornamento: `creato` è al
  secondo, e due ordini nati nello stesso istante (un carrello, le
  prove, un import) si scambierebbero di posto a ogni richiesta — la
  lista «balla» senza che sia cambiato niente. È il pattern del
  cursore keyset della vetrina, `creato DESC, id DESC`.
  E IL CONTROVALORE È QUELLO DEL SUO GIORNO (ago 2026, la stessa
  famiglia: di un affare concluso non si muove più niente, nemmeno
  quanto valeva). Il toggle €/₿ c'è anche negli Ordini — lista e
  scheda, stessa preferenza dei fratelli — ma l'euro NON è quello di
  oggi: un ordine di luglio dice quanto valeva a luglio.
  IL DATO C'ERA GIÀ A METÀ, ed è la parte che ha ridotto il cantiere:
  `ordini.cambio_ordine` esiste da sempre e vuol dire «EUR per BTC
  alla creazione della invoice» — solo che si riempiva SOLO dove
  serviva a convertire qualcosa (listino in EUR, tariffa ancorata),
  quindi di un ordine tutto-sats non restava scritto niente. Ora si
  scrive SEMPRE, nelle tre strade che creano un ordine.
  LA COLONNA SI ALLARGA, NON CAMBIA SIGNIFICATO, e per questo non ne
  nasce una seconda: dov'era piena era già il cambio di quel giorno,
  dov'era 0 non lo sappiamo — nessuna riga vecchia si rilegge male.
  Censito prima di toccare: quel valore non lo legge NESSUNO (né
  server, né client, né script, né libro mastro) e nessuno usa il suo
  zero come proxy. ATTENZIONE al vicino di casa, che il pattern ce
  l'ha davvero: `cambio_eur` (il cambio alla CHIUSURA) usa lo zero
  come segnale in due punti — il CSV e `xp_ordine` — e non si tocca.
  TRE COSE DA NON AMMORBIDIRE nel server. 1) La variabile che alimenta
  la MATEMATICA resta quella di prima: il cambio del giorno si congela
  in una riga sola (`cambio_ordine = cambio_misura or
  cambio_noto_ora()`), DOPO l'ultima riga di conto e prima
  dell'INSERT — spostata più su, il conto vedrebbe un cambio dove
  nessun 503 ne ha garantito il valore, e c'è la prova che l'ordine si
  rispetti. 2) DALLA CACHE E MAI DALLA RETE: `cambio_noto_ora` non
  attende, quindi il patto «niente await fra il ricontrollo e
  l'INSERT» resta intatto e un acquisto tutto-sats non si lega a
  CoinGecko per un dato che serve solo a raccontarlo. 3) Muto = 0,
  cioè «non lo sappiamo», mai un numero inventato.
  IN VETRINA il giudice è UNO, `_resaCifraOrdine` (lista e scheda sono
  la stessa cifra vista da due posti), e la prova regina è che non
  nomini `eurPerSat`: il cambio vivo lì dentro rimetterebbe l'affare
  che cambia valore ogni mattina. L'EURO PORTA SEMPRE IL «≈», e non è
  pigrizia: la valuta NATIVA di un ordine sono i SATS — l'escrow è in
  sats anche quando il listino era in euro, e il totale comprende
  spedizione e protezione — quindi non esiste il caso in cui quella
  cifra sia un prezzo che qualcuno ha pattuito.
  IL TOGGLE RISCRIVE LA SCHEDA IN PLACE (`aggiornaCifreOrdine`, il
  `data-sats` sugli involucri) e NON la riapre: `openOrder` butterebbe
  via il tracciamento a metà o il codice appena incollato — è la
  ragione per cui il dettaglio annuncio ha `aggiornaPrezzoDettaglio`,
  qui alla seconda volta.
  PARLA EURO CIÒ CHE RACCONTA, RESTANO SATS LE CIFRE CON CUI SI
  AGISCE: il pannello d'incasso non passa dal toggle, perché quel
  numero è l'importo della invoice da incollare e la cintura di
  `paga_venditore` lo confronta al sat.
  SENZA CAMBIO restano i sats più la riga «di questo giorno non
  abbiamo il cambio» (che nasce nascosta e la accende il giro delle
  cifre): non si ripiega su quello di oggi, che sarebbe il difetto
  rimesso proprio nel caso residuo, cioè dove non lo controlla
  nessuno.
  GLI ORDINI DI PRIMA li ha recuperati `recupera_cambi_ordini.py` dal
  prezzo STORICO di CoinGecko (16 ordini su 8 giorni in produzione,
  ago 2026): anteprima di serie e a ZERO chiamate — una per GIORNO
  distinto, non per ordine —, `--scrivi` per farla, commit giorno per
  giorno quindi interrompibile e ripartibile, e scrive solo
  `cambio_ordine` e solo dov'è a zero (quindi non ricopre mai il
  cambio VERO di un ordine in euro con lo snapshot, che è meno
  preciso). MISURATO su CoinGecko prima di sceglierlo, e da rimisurare
  se un domani si inceppa: l'endpoint storico è PUBBLICO e senza
  chiave, è deterministico (stesso giorno = stesso numero), arriva
  indietro 365 GIORNI e non oltre (oggi copre tutto; fra un anno no, e
  lo script lo dice invece di lasciare un buco in silenzio) e il rate
  limit è STRETTO — quattro chiamate di fila e arriva un 429.
  IMPERFEZIONE DICHIARATA: il prezzo storico è quello del GIORNO e non
  dell'istante, quindi su una giornata mossa il recuperato può
  scostarsi. Resta un fatto vero e fermo, vale solo per gli ordini di
  prima, e il «≈» lo dichiara già; i recuperati NON si distinguono in
  vetrina dagli esatti — sarebbe una seconda etichetta da spiegare per
  una differenza che sta dentro il «≈».
  DIVERGENZA DICHIARATA COL CSV, e le due non si uniformano: la vista
  dice il valore del giorno dell'ACQUISTO, il CSV quello del giorno
  della CHIUSURA (`cambio_eur`). Sono due domande diverse — «quanto
  valeva l'affare» e «quanto ho mosso in contabilità» — e ognuna ha il
  suo numero, tutti e due congelati. Fuori dal cantiere per la stessa
  ragione: notifiche (parlano sats e basta), XP, libro mastro (lo 0 è
  uno stato legittimo: un allarme che suona sul normale è peggio di
  nessun allarme) e la pagina d'acquisto, dove il ≈ è live perché lì
  si sta pagando ADESSO.
  LA FOTO: il server manda SOLO `foto0` (primo nome della lista JSON,
  pattern scheda() dei doppioni; la lista intera si poppa nello
  strip). Dall'ago 2026 la stessa foto sta anche IN TESTA AL
  DETTAGLIO, accanto al titolo, al posto del 📦 — stesso dato, stessa
  miniatura versionata, stessa catena: la fabbrica è UNA
  (`fotoOrdine(o, grande)`), perché la parte delicata è il RIPIEGO e
  due copie divergono al primo ritocco. Il raggio dell'`<img>` è
  `inherit`, così il quadratino da 38 della lista e quello da 48 del
  dettaglio non hanno una seconda misura da tenere in pari; e il
  titolo, che lì è un figlio flex, porta `min-width:0` — senza, una
  parola lunga senza spazi allargherebbe la PAGINA (la lezione del
  riquadro venditore). La catena degli ordini si riconosce dal 📦
  finale, e c'è la prova che di `replaceWith('📦')` ce ne sia UNO in
  tutto il file: le miniature delle altre liste hanno la loro, a due
  gradini e senza emoji. Per i SET è la foto del PRIMO pezzo — LEFT JOIN sulla query
  delle righe, coerente con _titolo_ordine che lo nomina; il mosaico è
  stato scartato (in 38px non si legge). Ripiego a catena nel client:
  _min → foto piena → il 📦 di sempre, mai un'immagine rotta; annuncio
  sparito = foto0 '' per costruzione. In DEMO resta l'emoji del
  listing (`o.listing.emoji`). Digitali e ordini d'asta non sono casi
  speciali: annunci con foto come gli altri.
  IL NASCONDERE, MAI CANCELLARE: la riga resta nel database — libro
  mastro, feedback, export e registro ci poggiano. DUE colonne
  per-parte (`nascosto_compratore`/`nascosto_venditore`, il patto
  delle sorelle sollecito_*: mai una colonna condivisa), e da
  /api/orders esce SOLO il PROPRIO flag (`nascosto`), mai quello
  dell'altra parte — è un fatto privato suo. Endpoint
  `POST /api/orders/{id}/nascondi` (body {nascosto:1|0}): guardia a
  due parti + stato nella STESSA WHERE col 400 anti-oracolo, UPDATE
  della sola colonna della parte, MAI `aggiornato` (nascondere non è
  un movimento: non riordina e non sposta ancore), nessuna notifica.
  Rimettere in vista non ha guardie in più (il patto delle ferie). La
  ✕ vive sulla riga (stopPropagation, bersaglio largo via ::after)
  SOLO sugli stati nascondibili, mai in DEMO; al nascondere parte il
  toast «Nascosto — lo ritrovi da "mostrali"» — non una conferma, un
  cartello: una riga che sparisce in silenzio la prima volta è quella
  che si cerca per dieci minuti. In fondo «N ordini nascosti —
  mostrali» (il conteggio segue i filtri correnti: con «solo attivi»
  acceso non compare, i nascosti sono tutti conclusi); da lì le righe
  escono SPENTE col «↩» che rimette in vista. Il libro mastro
  sorveglia «ordine nascosto su uno stato non finale» (passa la
  domanda che decide: il gate ammette solo stati assorbenti, non
  esiste transitorio legittimo) — anche in query_libro_mastro.sql
  (16d). Empty state SUO per i filtri a vuoto («Niente qui con questi
  filtri»), distinto dall'«Ancora nessun ordine».
  LE LAPIDI NON SI VEDONO (ago 2026, decisione di Andrea): gli ordini
  'annullato' spariscono dalla LISTA, e da nient'altro — il database
  e la scopa del reaper non si toccano, perché la lapide ha un
  mestiere: un saldo atterrato nella corsa annulla-vs-saldo deve
  avere una riga su cui posarsi (`controlla_annullati` la ripesca).
  Si nasconde la vista in UNA riga, `const vivi` in cima a
  `renderOrders`, e tutto il resto — filtri, conteggio dei nascosti,
  stato vuoto — parte da lì.
  SPARISCONO DEL TUTTO, anche dal velo dei nascosti, ed è la parte
  decisa e non ovvia: quel «mostrali» significa «le righe che HO
  nascosto io» (una colonna per-parte che l'utente scrive con la ✕),
  e mescolarci una lapide che nessuno ha nascosto farebbe mentire il
  conteggio e trasformerebbe un gesto dell'utente in un contenitore
  misto. In più la lapide vive al più un'ora, quindi «raggiungibile»
  sarebbe una promessa che scade da sola. Il fatto non si perde nel
  momento in cui conta: chi annulla ha già il suo confirm e la sua
  riga «nessun pagamento è stato trattenuto», e il riacciuffo avvisa.
  L'ANCORA DELLO STATO VUOTO si sposta con loro (`if (!vivi.length)`),
  o chi ha un checkout abbandonato e nient'altro leggerebbe «niente
  qui con questi filtri» senza aver acceso nessun filtro. Sorvegliato
  da una prova che conta gli `orders.filter` dentro renderOrders: UNO
  solo, quello che deriva i vivi — l'errore che verrebbe naturale è
  rileggere `orders` in una delle tre righe sotto, e non romperebbe
  niente di visibile finché non si guarda proprio quel caso.
  I VERBI SEGUONO IL TEMPO DELL'AFFARE (stessa decisione): finché è
  vivo «Stai comprando / Stai vendendo · X sats», quando è finito
  «Hai comprato per X» / «Hai venduto per X» — e la cifra entra nella
  frase invece di stare accanto, o si direbbe due volte. LA CIFRA È
  QUELLA CHE OGNUNO HA DAVVERO MOSSO: il TOTALE a chi paga, il NETTO
  a chi incassa (`nettoVenditore`, cioè il totale meno la protezione,
  che è della piattaforma). Sono numeri diversi e ognuno vede il suo:
  è già la regola della testa dell'ordine, e da qui in poi il netto
  ha UN giudice solo — la riga, la testa e il pannello d'incasso lo
  chiamano, così il giorno che la commissione si accende c'è un posto
  da correggere invece di tre.
  SUL RIMBORSO NON SI PORTA NESSUNA CIFRA («Acquisto non concluso» /
  «Vendita non conclusa»): lì nessuno ha comprato e nessuno ha
  venduto — il compratore ha riavuto tutto, il venditore non ha
  incassato niente — e un numero sarebbe l'unica bugia possibile in
  quella riga. E non si scrive «Rimborsato», che è il badge lì
  accanto: si aggiunge, non si ripete. Lo stesso ramo copre la lapide
  dell'annullato, che in lista non si vede ma resta onesta se un
  domani ci tornasse. IL CONCLUSO È `CONCLUSI`, la stessa lista del
  filtro «solo attivi»: una seconda definizione che oggi dice la
  stessa cosa, un giorno ne direbbe un'altra.
  IL DETTAGLIO PARLA A CHI LEGGE (ago 2026): la vista dell'ordine è
  UNA per tutti e due i lati, quindi ogni frase che nomina una parte
  va girata a chi la sta leggendo — «l'acquirente» resta solo per chi
  acquirente non è (il venditore, e il moderatore che guarda da
  fuori). Sistemati: il punto di ritiro («Il punto di ritiro che hai
  indicato» al compratore), i due passi che parlano al compratore (il
  reso da rispedire, la disputa vinta «a tuo favore»), i due che
  parlano al venditore (la consegna al corriere e quella del
  contenuto digitale) e la spedizione offerta («hai offerto N sats»).
  LA PROVA TIENE I DUE LATI INSIEME: per ogni testo girato chiede
  ANCHE che l'altro ramo continui a leggere la terza persona — con
  una vista condivisa il modo tipico di sbagliare non è dimenticare
  la correzione, è applicarla a tutti e due.
  RESTANO in terza persona, e non è una svista: i testi dentro
  pannelli già gatati per ruolo (il pannello «📦 Spedisci» del
  venditore, i bottoni del moderatore, i ponti di contatto, che della
  CONTROPARTE parlano apposta) e le frasi simmetriche («Vi incontrate
  e l'oggetto passa di mano»).
  E LA PRIMA RIGA DEL RIQUADRO DICE UN GESTO (ago 2026): «Sats nel
  deposito di garanzia» raccontava un fatto della piattaforma, non
  quel che è successo a chi legge. La riga è CONDIVISA, quindi vale la
  regola qui sopra e il verso in cui si sbaglia è dare l'«hai
  depositato» anche a chi VENDE: lui i sats non li ha depositati, ce
  li ha in garanzia. Quindi `passoDeposito` — «Hai depositato i sats»
  a chi compra, «Hai il pagamento in garanzia» a chi vende, la frase
  neutra di sempre al moderatore che guarda da fuori — e la riga
  sotto («Il pagamento è custodito dalla piattaforma») NON si tocca:
  è vera per tutti e due, ed è anche ciò che impedisce di leggere
  «garanzia» come «è nel tuo wallet». Il giudice è UNO e lo usano
  ENTRAMBI i rami del riquadro, quello normale e quello della
  disputa, che la stessa riga non può raccontare due storie.
  LA TESTA DEL RIQUADRO invece resta «Sats nel deposito di garanzia»,
  ed è deliberato (decisione di Andrea, guardando le due rese): quella
  dice lo STATO dell'affare, il passo dice la storia di chi lo guarda,
  e la ripetizione è il PREZZO di quella distinzione, non un difetto.
  Chi un domani vorrà girare anche la testa tolga prima la
  distinzione, o si ritroverà due volte la stessa frase in prima
  persona a un centimetro di distanza.
  E DALL'AGO 2026 QUELLA TESTA STA SOPRA IL RECINTO, non dentro
  (decisione di Andrea): dice lo STATO dell'affare, che è
  l'intestazione dell'ORDINE e non un contenuto della cassaforte. Il
  riquadro comincia dritto coi PASSI e NON prende una seconda testata,
  nemmeno più corta — ogni passo ha già il suo titolo, e una riga lì
  dentro ripeterebbe la frase appena letta un centimetro più su
  (che è, alla lettera, la ripetizione dichiarata qui sopra: adesso i
  due testi non sono più adiacenti e si legge meglio). Il sigillo
  dell'escrow resta il tratteggio verde, non era la testata a dirlo.
  DUE COSE DA NON DIMENTICARE quando si tocca: il CSS ha perso il
  discendente (`.vault .vault-head` → `.vault-head`, tre selettori) o
  la testata uscita dal recinto resterebbe senza vestito; e le monete
  della FESTA partono da `#orderContent .vault-head`, quindi la classe
  non si rinomina — c'è la prova per tutte e due. Il respiro fra i due
  lo dà il margine SOTTO la testata (il recinto ha perso il suo
  margin-top, o i due collasserebbero al più grande).
  E CON LEI LE ALTRE TRE RIGHE DEL RIQUADRO (ago 2026, stesso giro):
  1) l'attesa della conferma diceva «I sats restano nel deposito
  finché non confermi» — e «Restano ~N ore per confermare o aprire
  disputa» sul digitale — anche a CHI VENDE, cioè gli attribuiva un
  gesto che non ha: ora a lui e al moderatore vanno «finché
  l'acquirente non conferma» e «L'acquirente ha ~N ore…». Il taglio è
  `o.role==='buyer' ? tu : terza persona`, lo stesso della riga
  immediatamente sotto («Hai verificato che è tutto ok»), così il
  moderatore ci ricade da solo senza un ramo suo.
  2) la testa del RESO diceva «Rimborso alla restituzione: i sats
  restano congelati»: vera, ma muta proprio verso chi deve fare
  qualcosa. Ora è «Rispedisci l'oggetto: al rientro ti rimborsiamo» a
  chi ha comprato e «L'acquirente sta rispedendo l'oggetto» agli
  altri.
  MA I DUE STATI DEL RESO NON SI DICONO CON LA STESSA FRASE, ed è la
  correzione che il cantiere ha fatto alla proposta: a pacco già
  partito (`return_shipped`) «Rispedisci» sarebbe una bugia detta a
  chi ha appena fatto quel che gli si chiedeva — quindi lì diventa
  «Il reso è in viaggio: al rientro ti rimborsiamo» / «L'acquirente ha
  rispedito l'oggetto», e c'è la prova che i due stati restino
  distinti.
  CHE I SATS SIANO FERMI NON SI PERDE, cambia posto: lo dice il passo
  «Disputa aperta — I sats sono congelati: nessuno può toccarli», due
  righe più sotto nello stesso riquadro. È l'unica ragione per cui
  quella mezza frase si poteva togliere dalla testa.
  3) e il PASSO del reso parla a TRE, non a due — è l'ultima riga di
  questa famiglia e la più insidiosa, perché lì l'acquirente e il
  venditore sono nominati TUTTI E DUE nella stessa frase: col taglio
  buyer/non-buyer al venditore restava «L'acquirente deve rispedire
  l'oggetto **al venditore**», cioè una terza persona su SÉ STESSO —
  esattamente il difetto tolto un centimetro più su. Tre letture come
  in `passoDeposito`: «Devi rispedire l'oggetto al venditore» a chi
  compra, «L'acquirente deve rispedirti l'oggetto» a chi vende, la
  frase con tutti e due i nomi al moderatore che guarda da fuori (e,
  a reso partito, «Il reso è in viaggio verso di te» / «…verso il
  venditore»).
  LA REGOLA CHE NE ESCE, e vale per la riga che qualcuno scriverà
  domani: il taglio a DUE (`buyer ? tu : terza persona`) basta finché
  la frase nomina UNA parte sola; quando le nomina tutte e due servono
  TRE letture, o una delle due si ritrova a leggersi in terza persona.
  A dire quali righe sono a rischio è un censimento sulle righe dei
  passi e della testa che contengono «venditore» — fatto, e quella era
  l'ultima.
  LA MODALITÀ NON SI RIPETE (stesso giro): la riga sotto il prezzo
  diceva «🚚 con spedizione» / «📦 spedizione a un punto di ritiro»,
  che è già scritto due righe più sotto — dal punto di ritiro, dal
  pannello del ritiro in zona, dalla rivelazione del codice. Via.
  Resta il solo conto dei pezzi, che non lo dice nessun altro.
  E LA SPEDIZIONE È UN INCISO ACCANTO ALLA CIFRA, non una riga a sé
  (`incisoConto`): «130 000 sats · di cui 5 000 di spedizione» — è un
  dettaglio di com'è fatto quel totale, non un fatto suo. Con la
  protezione accesa entra anche lei nello stesso inciso, con la
  stessa forma. QUANDO LA SPEDIZIONE È GRATIS PER LA PROMESSA DEL
  NEGOZIO l'inciso TACE: «di cui 0» non direbbe niente, e a
  raccontarlo c'è già la riga «🚚 Spedizione gratuita», che in più
  dice quanto ha offerto chi vende. Il font si rimette a mano perché
  il prezzo è in mono e un inciso di prosa in mono si legge male.
  LA STRADA SCARTATA, decisa da Andrea davanti alle due rese: mettere
  nel dettaglio la frase col VERBO e la cifra del lato («Hai venduto
  per 128 800 sats, di cui…»). Sarebbe stata la stessa lingua della
  lista, ma sotto il prezzo grande — che è e resta il totale in
  cassaforte — avrebbe messo due numeri diversi a un centimetro di
  distanza. Il verbo resta della lista, il dettaglio dice la cifra
  dell'escrow col suo inciso.
  «CONTROLLA IL PACCO» HA PERSO LE PILLOLE DI SCELTA (decisione 3 di
  Andrea, stile Vinted): la scelta vive nella pagina d'acquisto
  (`#ctrlAcquista` → `apriAcquistoSet`), al loro posto la riga onesta
  «la scegli al passo dopo». Il conto arriva dallo STESSO preventivo
  (cache `ctrlPrev` per firma della composizione: mai due conti che
  divergono) con l'anteprima sulla strada PIÙ ECONOMICA, e la riga lo
  DICE («Spedizione (dalla più economica)»); in DEMO resta la stima
  client di `totaleSet` (per questo `consegnaSetScelta` sopravvive
  CONGELATA a 'spedizione'). `startBuy`/`startBuySet`/
  `confermaCompraSubito` restano i soli varchi POST (sentinella sul
  conteggio) e pescano le cifre del paySheet dal preventivo: foglio e
  pagina dicono gli stessi numeri per costruzione.
  ACQUISTA VIVE IN DUE POSTI (correzioni lug 2026, poi rifinite col
  feedback di Andrea): dentro il recinto escrow sta SOLO «Acquista»
  arancio ₿ — centrato, lungo (`min-width:76%`) ma mai a tutta
  fascia (`.escrow-zone .acquista-cta`, specificità doppia perché
  `.btn{width:100%}` sta più in basso nel foglio; raggio 12, più
  squadrato del riquadro: il 16 su un bottone basso leggeva tondo).
  Coi pezzi >1 lo STEPPER sta DENTRO il bottone: `stepperAcquista()`
  = chip traslucido «− N +» accanto alla scritta, span con role
  (mai <button> annidato) e stopPropagation sul gruppetto — il tocco
  sui più/meno non compra mai; due istanze gemelle (pagina e barra)
  aggiornate insieme da `setQta` per classe (`.qm-num/.qm-meno/
  .qm-piu`, il vecchio stepper `.qta-riga` del recinto è morto —
  `.qta-step` vive ancora nel foglio del set). «Fai un'offerta» è
  una trattativa e sta fuori dal tratteggio: su MOBILE vive SOLO
  nella barra (in pagina è nascosto, `#detailContent
  .offerta-pagina{display:none}` sotto i 768 — con l'ID, che
  `.btn{display:flex}` a pari peso lo riaccenderebbe), da desktop
  resta in pagina sotto il recinto perché lì la barra non esiste.
  Nella barra fissa: OFFERTA A SINISTRA, ACQUISTA A DESTRA, metà e
  metà (col multi-pezzo il lato Acquista cresce, `#barraCompra
  .con-qta`). Nel recinto restano le note — il «⚡ Compra subito» NWC
  dall'ago 2026 NON vive più lì: l'ordine nasce solo dalla pagina
  d'acquisto, e il wallet paga da là; il trucco
  `:first-of-type` che promuoveva il ghost a
  CTA è stato RIMOSSO: Acquista è arancio per classe, sempre. Le PILLOLE DI
  SCELTA consegna (`pilloleConsegna`) non esistono più: in pagina
  restano solo le pillole INFORMATIVE (spedBadge + pilloleModalita),
  la scelta vive nella pagina d'acquisto.
  LA FORMA DI «ACQUISTA» È LA FORMA DI TUTTI (ago 2026, decisione di
  Andrea, ed è la regola da non rovesciare). `.btn` nasceva PILLOLA
  (999px) e il rettangolo era una DEROGA scritta a mano in quattro
  punti — con due valori diversi per giunta: 12px nel recinto e nelle
  due barre, 16 (`--radius`) nel dettaglio e nel foglio puntata.
  Risultato: il pannello Filtri, tutti i fogli e la pagina del negozio
  erano rimasti tondi, e nella stessa schermata convivevano due forme
  per la stessa famiglia di bottoni. Adesso il verso è ROVESCIATO — la
  regola sta nella base `.btn`, le deroghe non ci sono — e il token è
  UNO, `--radius-btn` (12px): chi vuole un'altra curva lo tocca e
  tocca tutta l'app. Con lo stesso giro sono passati al rettangolo il
  pannello Filtri (Applica/Azzera), i bottoni del negozio, «← Torna»
  (`.back`) e il bottone delle celle del pacco, che aveva un 10px suo.
  RESTANO TONDI DI PROPOSITO, e sono classi loro, non `.btn`: `.pill`,
  `.chip`, `.badge`, `.escrow-flag`, i badge lampo/asta
  in card, il toggle €/₿, la nav col tondo del Vendi, le pillole
  «Ordina»/«Filtri» sopra la griglia (sono chip di filtro, famiglia
  delle categorie), più `.tour-avanti` e `.demo-cta`. Quelle non sono
  bottoni-oggetto, sono etichette e chrome. I testuali (`.btn.link`,
  `.danger-ghost`) non hanno fondo, quindi la curva non li riguarda.
  E I DUE PONTI SONO BOTTONI, NON LINK (stessa decisione): nel negozio
  erano testo sottolineato («btn link») mentre gli stessi due dentro
  l'ordine erano già ghost — la stessa azione con due vestiti secondo
  la pagina. Ora il vestito è uno solo, e `pontiOrdine` non passa più
  una classe sua.
  E PORTANO IL COLORE DEL LORO MONDO (ago 2026, decisione di Andrea):
  azzurro Telegram e viola Nostr, `.btn.ponte.tg` / `.ponte.nostr` —
  la classe la compone `pontiContatto`, perché a dire di che mondo si
  parla è il ponte, non la pagina. Stessa FORMA di ogni altro bottone
  (rettangolo, ombra piena, stesso peso): cambia solo il colore, che
  qui dice DOVE porta. Sono gli unici bottoni pieni che NON sono
  un'azione dentro Barattolo, e per questo non parlano arancio, che
  resta dell'acquisto.
  SBIADITI, NON PIENI (ritocco di Andrea guardandoli a schermo, ed è
  la versione che vale): il fondo è una VELATURA della tinta, e a
  portare l'identità sono il testo e il contorno. Nati saturi col
  testo bianco, due blocchi di colore in fila facevano concorrenza a
  tutta la pagina — e questi non sono nemmeno azioni dentro Barattolo:
  portano FUORI, quindi devono farsi trovare, non gridare. La ricetta
  è quella di `.btn.ghost`, che veste testo, bordo e ombra dello
  stesso colore: qui quel colore non è l'inchiostro, è il mondo dove
  il bottone porta — zero forme nuove.
  Il NOSTR riusa i token che c'erano già, `--nostr-soft` +
  `--nostr-text`, nati esattamente per una superficie velata (ed è
  anche il motivo per cui il `var(--nostr)` pieno non andava: su un
  fondo saturo col testo bianco, di sera scendeva a 2,72). Il
  TELEGRAM ha la sua coppia `--tg-soft` / `--tg-soft-on`
  (#E3F1FB/#1A6699 di giorno, #1B2A38/#8FC4E6 di sera — di notte la
  velatura si scurisce e il testo si schiarisce: si abbassa la luce,
  non si cambia il segno), e NON prende in prestito l'azzurro di casa,
  che è dei badge spedizione: un colore che significa una cosa non se
  ne prende un'altra. Misurati, testo su fondo: Telegram 5,36 e 7,81,
  Nostr 4,91 e 7,88 — AA pieno in entrambi i temi.
  E L'USCITA DI SICUREZZA HA LA STESSA RICETTA (ago 2026): «⚠️ C'è un
  problema — apri disputa» era un testuale sottolineato
  (`.danger-ghost`) e in fila coi due ponti colorati spariva — proprio
  il bottone che deve farsi trovare quando qualcosa va storto. Ora è
  `.btn.allarme`: la forma di tutti, fondo VELATO `--warn-bg`, testo e
  bordo `--danger` (4,83 di giorno, 5,28 di sera, AA in entrambi i
  temi). Il fondo resta una velatura e non il rosso pieno, ed è la
  riga da non ammorbidire: tre blocchi saturi in fila — rosso,
  azzurro, viola — sarebbero un semaforo, e questo non è un invito ma
  un'uscita. Più il `margin-bottom` che stacca il rosso dalla coppia
  dei ponti: guardati a schermo, tre blocchi colorati a filo l'uno
  sull'altro erano precisamente quel semaforo.
  ATTENZIONE se un domani si vorrà sbiadirli ancora: il fondo è già al
  livello «soft» di casa (contro la pagina fa 1,05–1,18, cioè si legge
  come una velatura e basta) ed è il CONTORNO a dire che è un bottone.
  La leva che resta è l'ombra piena, non il fondo.
  LO SPAZIO FRA DUE BOTTONI È DELLA COPPIA, NON DEL BOTTONE (ago
  2026): `.btn` di base NON ha margine — ce l'hanno solo `.ghost` e
  `.allarme` — quindi due bottoni adiacenti stanno staccati soltanto
  se il PRIMO è uno di quei due, e chi ne aggiunge uno di un'altra
  famiglia si ricompra il difetto senza accorgersene. Detto fra
  FRATELLI il buco si chiude per sempre — un `margin-top:10px` su
  `.btn + .btn`, scoped a `#orderContent` e `#detailContent` — più
  l'unica distanza diversa che esiste: l'USCITA, 18px, staccata
  apposta perché non è un'azione in fila con le altre.
  UN SELETTORE PER LE DUE COLONNE e non due regole gemelle: sono i
  due soli posti dove i bottoni si impilano davvero, e due numeri da
  tenere in pari divergono al primo ritocco.
  È INCIAMPATA DUE VOLTE IN DUE GIORNI, ed è la parte da tenere:
  nell'ordine (due `margin-top:0` più la didascalia di @trackbot, col
  gesto principale incollato al testo) e il giorno dopo nel dettaglio
  di un annuncio proprio, dove la regola non arrivava affatto e cinque
  margini a mano tenevano «Lancia un'offerta lampo» e «Modifica» a
  ZERO px. La causa è sempre la stessa e non è distrazione: sono righe
  scritte PRIMA che la regola esistesse, che un riordino non rompe e
  una rilettura non vede — si trovano solo MISURANDO la pagina vera.
  Per questo `prove.py` li CONTA invece di fidarsi: nel dettaglio non
  ne resta nessuno, nell'ordine uno solo — la didascalia di @trackbot,
  che appartiene al bottone SOPRA e si infila in mezzo alla coppia,
  quindi è lei a dover portare il 10 (e il commento dice che non è un
  valore suo).
  E IL ROSSO VELATO È IL VESTITO DI CHI TOGLIE (ago 2026): `.allarme`
  lo portano tutti e tre i bottoni che tolgono qualcosa e non si torna
  indietro — «⚠️ C'è un problema» nell'ordine, «🗑 Elimina l'annuncio»
  del proprietario e «🛡 Rimuovi (moderazione)» di chi modera l'altrui.
  Gli ultimi due fanno LA STESSA COSA su annunci di persone diverse e
  non si vedono MAI insieme: è proprio per questo che erano rimasti
  con due vestiti — la divergenza che nessuno vede è quella che
  sopravvive. Il testo dice solo cosa fa («Elimina l'annuncio»: che
  sia suo lo raccontano già la riga verde sopra e i bottoni accanto, e
  la frase lunga a 320px andava su due righe).
  IL VELATO È LA METÀ CHE CONTA: nella colonna del proprietario il
  pieno non ce l'ha nessuno, quindi un rosso saturo sarebbe il colore
  più forte della pagina per il gesto che si fa meno; e dove il pieno
  c'è — l'«Acquista» arancio del recinto, sopra il Rimuovi del
  moderatore — il velato tiene la sua distanza senza fargli
  concorrenza. Guardato a schermo nei due temi, mai dedotto.
  Col colore è venuto fuori un difetto che il ghost bianco
  nascondeva: `#negozioHeader` non aveva MARGINI su mobile (li metteva
  solo la media query da 768 in su) e i due blocchi pieni arrivavano a
  filo schermo — ora il rientro c'è, ed è lo stesso `--pad` del resto.
  Da ≥768px la barra non esiste proprio:
  la nav è una topbar e il dettaglio a due colonne ha già i bottoni
  sotto mano. I fogli (41) e il velo (40) le passano sopra senza che
  rubi tocchi; a lightbox aperto si nasconde con header e nav
  (`body.lb-aperto`); la scivolatina d'ingresso tace con
  prefers-reduced-motion.
  IL RECINTO PARLA POCO (lug 2026): dentro l'escrow-zone resta UNA
  riga — «I tuoi sats restano nel deposito di garanzia finché non
  confermi di aver ricevuto l'oggetto» — e sotto Acquista NIENTE, solo
  il «Scopri di più». Sono uscite: il paragrafo su
  disputa e moderatore, e la riga «Ricevi una invoice Lightning,
  paghi con qualsiasi wallet» (troppo lunga, e chi ha un wallet lo sa
  già). Il «(escrow)» della prima spiegazione lunga se n'è andato con
  loro: la spiegazione lunga adesso vive nella pagina dedicata (regola
  9 rispettata, cambia solo dove sta la prima volta). Il link «Scopri
  di più» (`.scopri-link`) la apre e sta IN LINEA, in coda alla frase
  («…di aver ricevuto l'oggetto. Scopri di più»): non è più il piede
  staccato sotto il bottone (`.escrow-piede`, morto lug 2026). Porta
  lo STESSO verde `--trust-note` del testo di fiducia — è la stessa
  frase che continua, e a dire che è un link bastano la sottolineatura
  e il grassetto in più (800 contro 600); l'inchiostro del piede
  serviva a staccarlo da un blocco che adesso non esiste. È legato
  all'ULTIMA PAROLA con un nowrap (`.fine-frase`, il trucco della
  pillola condizione in coda al titolo): sotto i 390px non ci sta in
  riga e scendono INSIEME — da solo a capo tornerebbe a somigliare al
  piede di prima.
  LA PAGINA «IL PAGAMENTO PROTETTO» (lug 2026, `view-sicurezza`): la
  spiegazione lunga che il recinto non può contenere — hero col
  barattolo, cosa succede quando paghi (4 passi), i tempi, la
  disputa, DOVE IL DEPOSITO NON PUÒ PROTEGGERE (il codice rivelato,
  nei due sensi: quello che non torna indietro e quello che non
  funziona; il ritiro a mano; il PACCO PERSO O ROVINATO; «l'oggetto
  promesso, non i gusti»), il
  pagamento Lightning, dove stanno i sats e SE BARATTOLO SPARISSE. Markup FISSO e nessun
  dato utente dentro: mai un `esc()` da ricordare. TRE PORTE —
  «Scopri di più» nel recinto, la riga di fiducia di Esplora e del
  negozio (ora un `<button class="trust-line">` col ›: il tour la
  cerca per classe e la classe non è cambiata), un bottone in fondo
  al Profilo — più il LINK CONDIVISIBILE `/sicurezza` (ago 2026, rotta
  esplicita gemella di `/annuncio/{id}`, letta da `apriSicurezzaDaUrl`
  in avvia E in avviaVetrina): l'ancora sta nel FRAMMENTO e senza
  prefisso (`/sicurezza#limiti` → l'id `sicu-limiti`), così
  l'indirizzo che si manda resta corto e il prefisso lo rimette il
  codice; un'ancora inesistente lascia la pagina in cima, senza un
  ramo d'errore. L'URL poi non si tocca più (il patto del motore di
  navigazione: `pushState` con `location.href`), quindi navigando
  altrove la barra resta su /sicurezza — innocuo, ed è la ragione per
  cui NON si apre una rotta per ogni vista. In fondo alla pagina
  «🔗 Condividi questa pagina» (`condividiSicurezza`), che il link si
  poteva raggiungere ma non PRENDERE: sparisce in DEMO, dove
  `location.origin` è "null" e uscirebbe rotto — il patto del bottone
  condividi sulla foto. La SCALA è ora una sola (`condividiLink`:
  Telegram shareURL → t.me/share/url → navigator.share → appunti →
  link nel toast, mai il silenzio), estratta quando i chiamanti sono
  diventati due; `condividiNegozio`/`condividiMioNegozio` restano di
  proposito i soli appunti — copiano e basta, e passare anche loro
  dalla scala aprirebbe il selettore chat di Telegram, che è un'altra
  cosa da quella che quel bottone promette oggi.
  E `apriSicurezza(ancora)`/`tornaDaSicurezza()` ricordano da
  dove si veniva (il patto di `tornaDalNegozio`, con la vista di
  partenza che può essersi svuotata). Vale anche per gli anonimi in
  vetrina: la fiducia si spiega prima di chiedere di entrare.
  ATTENZIONE AL TESTO su dove stanno i sats: dice «restano bloccati
  in un conto Lightning della piattaforma», MAI la parola
  «custodia» — che in ambito regolatorio ha un peso specifico
  (decisione di Andrea, da tenere se qualcuno riscrive quel
  paragrafo; il parere legale MiCA è nel backlog).
  BARATTOLO GARANTISCE LA TRANSAZIONE, NON IL PACCO (ago 2026, buco di
  testo: nessuna riga dell'app diceva cosa succede se il corriere perde
  o rovina la spedizione). Due voci nell'elenco «dove il deposito non
  può proteggerti» — il principio (che il venditore non incassi senza
  aver consegnato e il compratore non paghi senza ricevere; l'oggetto
  in viaggio no, il reclamo si apre col corriere) e il consiglio
  pratico (tracciamento sempre, copertura del corriere per le cose di
  valore, quella di base verso i punti di ritiro è bassa) — più UNA
  riga nel pannello «📦 Spedisci» del venditore, che è l'ultimo momento
  utile per comprare la copertura: il pattern degli hint contestuali,
  la riga nasce dove nasce il dubbio. MAI la parola «assicurato», né
  per il deposito (regola ferrea 9) né qui: si dice «copertura del
  corriere». Il pannello del RESO non la porta (il rischio è lo stesso
  ma sull'altra parte): si valuta se il caso si presenta.
  «SE BARATTOLO SPARISSE» (ago 2026, da una domanda di un utente sulla
  centralizzazione: la risposta si scrive invece di aspettare che la
  chiedano). In fondo alla pagina, dopo «Dove stanno i sats»: un server
  solo e un database solo, non ridondato; poi cosa NON si ferma con lui
  — ⚡ i sats (nodo Lightning nostro, seed offline), 🟣 gli annunci su
  Nostr, 📖 il codice, 💾 storico e reputazione col backup giornaliero
  fuori dal server. E FINISCE LÌ, SULL'ELENCO (ago 2026, decisione di
  Andrea): le due righe che chiudevano la sezione — «quello che resta
  fragile è l'infrastruttura, non i fondi… il passo dichiarato è un
  relay Nostr nostro» e la chiusa «oggi il punto di fiducia siamo noi
  due… la direzione è ridurlo, non nasconderlo» — sono state TOLTE.
  IL PERCHÉ DELLA PRIMA È UN FATTO CAMBIATO, ed è la parte da
  ricordare: oggi ci sono gli SNAPSHOT dell'intera macchina, un backup
  GIORNALIERO del database e una copia FUORI dal server — la macchina
  si rimette in piedi, quindi «resta fragile l'infrastruttura» era
  diventato falso quanto lo sarebbe promettere che non si ferma niente.
  La seconda se n'è andata con lei: era il commento di quella riga, e
  da sola avrebbe chiuso la pagina su una promessa invece che su un
  elenco di fatti — che è l'affermazione più forte delle due. Chi
  volesse rimetterci una terza riga si chieda prima quale FATTO
  racconta: la coda della pagina è il posto dove le frasi invecchiano
  per prime.
  OGNI RIGA È UN FATTO OPERATIVO, e chi la ritocca verifica il FATTO e
  non la frase — sono affermazioni sui soldi e sui dati di altri, e
  invecchiano fuori dal repo (nel codice non se ne vede nessuna). Le
  due delicate, confermate da Andrea il giorno in cui è stata scritta:
  l'istanza LNbits del config è OSPITATA (`*.lnbits.com`) ma la funding
  source è un nodo suo con la seed offline — per questo il testo dice
  «il gestionale che lo comanda è ospitato da terzi; il nodo e la seed
  no», e la scorciatoia «istanza nostra» sarebbe stata falsa; e il
  backup giornaliero fuori dal server esiste sul VPS, benché nel repo
  non ci sia niente che lo mostri. IL CATALOGO NON È DI TUTTI ALLO
  STESSO MODO, ed è la riga che si sbaglia per prima — chi scrive
  guardi `annuncio_su_nostr` e non `evento_annuncio`, o si sbaglia come
  ci si è sbagliati la prima volta: chi ha una chiave PROVATA vede
  l'annuncio uscire sul PROPRIO account, firmato dal suo browser
  («IL BIVIO», sopra), e quello resta suo anche senza di noi; chi non
  ce l'ha lo vede firmato dalla nostra chiave, leggibile in piazza ma
  governato da noi. Dirlo indistinto — in un verso o nell'altro —
  toglie a metà utenti una proprietà che hanno, o la promette all'altra
  metà che non ce l'ha. IL TESTO SI FERMA LÌ, e la ragione è la
  domanda che verrà subito dopo: «e allora posso aggiornarlo o
  ritirarlo da un client qualunque?». Su Nostr sì, l'autore è lui; su
  BARATTOLO no, ed è una scelta e non più un accidente (ago 2026, vedi
  «IL RIFLESSO NON È UNA FONTE»): l'annuncio nato qui si modifica e si
  ritira DA QUI, e l'import non tocca gli eventi che ha fatto firmare
  lui. La pagina promette quindi il possesso dell'EVENTO — che è vero
  e resta vero senza di noi — e non un flusso di modifica da fuori,
  che non esiste apposta.
  I TEMPI DELL'ESCROW STANNO IN UN POSTO SOLO (lug 2026): la costante
  `TEMPI` in cima al JS — `conferma` 72 ore, `autoSblocco` 10 giorni,
  `confermaDig` 24 ore, `silenzioDig` 48 ore, `invoice` 15 minuti —
  con accanto la tabella leva-del-config → chiave (ORE_CONFERMA,
  GIORNI_AUTO_SBLOCCO, ORE_CONFERMA_DIGITALE, ORE_SILENZIO_DIGITALE;
  la vita della invoice non è una leva, è `expiry: 900` in
  `crea_invoice_escrow`). Il client NON riceve quei numeri dal
  server: sono scritti a mano, ed erano sparsi in dodici stringhe
  (notifiche del pannello ordine, i quattro `confirm`, i toast, la
  nota digitale, il foglio del varco, la riga del cambio EUR).
  CHI CAMBIA UNA LEVA NEL CONFIG DEVE CAMBIARE `TEMPI`, e da lì in
  giù nessun numero di tempo si scrive più a mano. Il markup fisso
  della pagina porta segnaposto `<span data-tempo="...">` vuoti che
  riempie `scriviTempi()` all'avvio. (Fuori dal patto, di proposito:
  «l'anteprima vale 15 minuti» dell'import CSV — è il TTL del
  biglietto d'import, un'altra leva, che può cambiare da sola.)
  Preferiti «Nel tuo barattolo» (lug 2026): il simbolo è il
  BARATTOLINO 🫙 — MAI il cuore, MAI il fulmine (su Nostr è lo zap).
  Tabella `preferiti(tg_id, annuncio_id, creato, PK)`; toggle
  `POST /api/listings/{id}/preferito` (prima prova a togliere: il
  barattolo si svuota anche se l'annuncio è sparito del tutto, e
  anche da pieno); `GET /api/me/preferiti` = CAMPI_VETRINA +
  `a.stato` + venditore_id, dal salvato più recente, tetto 100 —
  escono ANCHE venduti/rimossi e il cassetto li mostra onesti «non
  più disponibile» (spenti, dettaglio non apribile, il 🫙 Togli
  resta) finché l'utente non li toglie lui. LIMITE 10
  (`MAX_PREFERITI`, dall'ago 2026 una LEVA del config col default 10
  nel codice — era 20 murato, decisione di Andrea: è una selezione,
  non una lista dei desideri infinita; ATTENZIONE, una riga esplicita
  nel config del VPS vince sul default): la guardia vive nel SERVER,
  nel ramo INSERT del toggle — `_conta_barattolo` conta solo gli
  annunci ATTIVI (venduti/rimossi non occupano posto: comprare
  qualcosa che c'è dentro libera spazio da solo), oltre = 400 che DICE
  il numero; niente await tra COUNT e INSERT (il patto
  anti-doppione). La risposta del POST porta anche `conteggio`
  (attivi dopo l'operazione: il frontend aggiorna il livello col
  numero del server). Il client NON tiene un gemello hardcodato del
  tetto: lo riceve da `/api/me.max_barattolo` e lo adotta — una copia
  a memoria divergerebbe al primo ritocco della leva, e il «(N/…)» e
  i messaggi direbbero un'altra cifra. La fusione può superare il
  tetto in unione, accettato: il limite blocca solo le aggiunte nuove.
  `esegui_fusione` migra in unione (UPDATE OR IGNORE + DELETE, il
  pattern degli avvisi).
  QUANTI, SÌ; CHI, MAI (ago 2026): il conteggio dei salvataggi di un
  annuncio è PUBBLICO e anonimo — `_conta_savers` e il campo
  `barattoli` aggiunto in `arricchisci_righe_vetrina` (UNA query per
  pagina sull'indice nuovo `idx_preferiti_annuncio`: la PK è
  (tg_id, annuncio_id) e senza quell'indice il conto per ANNUNCIO
  sarebbe una scansione di tutta la tabella) più `barattoli` nella
  risposta del toggle, così il numero accanto all'icona si aggiorna
  col dato del server e non con un ±1 a occhio. È la stessa regola
  dell'avviso «ha fatto colpo»: si dice quanti, mai chi — nessun
  nome, nessun id, da nessuna parte. La SOGLIA da cui mostrarlo la
  decide il CLIENT (`SOGLIA_SAVERS`, da 2 in su): il server dice
  sempre la verità, la soglia è una scelta di lettura e non di
  privacy — un «1» non è una prova sociale, è un numero che occupa
  spazio, e in griglia si moltiplica per trenta. IMPERFEZIONE
  DICHIARATA: il contatore vive attaccato al barattolino, quindi sui
  PROPRI annunci non compare (lì l'icona non c'è) — al venditore lo
  racconta già «ha fatto colpo»; per mostrarglielo servirebbe un
  secondo posto dove disegnare quel numero.
  Frontend: cerchietto `.jar-btn` sulla foto — dall'ago 2026 in BASSO
  A DESTRA e non più in alto accanto al condividi (modello Vinted,
  decisione di Andrea), un filo più grande (40 contro i 34 delle
  card) e con l'ombra più decisa, che sul bordo basso della foto
  capita di tutto. Solo autenticati veri (mai DEMO/VETRINA) e mai sui
  propri annunci, haptic + toast; Set `preferiti` e lista
  `myPreferiti` da `caricaPreferiti()` (in avvia() e a ogni apertura
  del Profilo: un salvato può essere stato venduto nel frattempo, e
  gli attivi entrano in `listings` via inCatalogo per openDetail).
  IL BOTTONE GRANDE «🫙 Metti nel barattolo» sotto il recinto NON
  ESISTE PIÙ (ago 2026, decisione di Andrea): un preferito non è
  un'azione dello stesso peso di un acquisto, e rubava spazio alla
  barra. Il gesto è UNO, ed è l'icona sulla foto — con lui se n'è
  andato `#jarCta`. La fabbrica è UNA per griglia e scheda
  (`bottoneJar`): stessa icona, stesso livello per-annuncio, stesso
  numero accanto, e `aggiornaJarCards` li riallinea tutti e due.
  Guardia di cortesia client (toast senza richiesta a barattolo
  pieno, la verità resta il 400).
  IL BARATTOLO SI RIEMPIE (lug 2026): le icone sono l'SVG inline di
  `jarSVG()` — vetro a stroke:currentColor, liquido = un rect
  arancione (`--jar-liquido`, default `--sats`) dentro la clipPath
  dell'interno (id univoco per istanza) — con 5 livelli a scatti
  `lv0-4` via translateY; transizione morbida spenta con
  prefers-reduced-motion.
  L'ANIMAZIONE SI È ROVESCIATA (ago 2026, decisione di Andrea): al
  tocco si accendeva d'arancio il FONDO del cerchietto e il liquido
  diventava crema — cioè a riempirsi era lo sfondo, e il barattolo si
  svuotava. Ora lo sfondo non cambia mai ed è il LIQUIDO ARANCIO che
  sale dentro il vetro, che è esattamente ciò che l'icona racconta;
  le due regole `.salvato{background:var(--sats)}` sono sparite. Una
  sola animazione, la stessa in vetrina e nel dettaglio — e il
  riempimento a scatti dal conteggio GLOBALE nel dettaglio non c'è
  più: lì non si capiva, e ora il livello è per-ANNUNCIO come in
  griglia (vuoto/pieno). Il globale resta solo dove racconta davvero
  il barattolo: il 🫙 dell'header del cassetto, `#preferitiJar`.
  LE SOGLIE SONO IN PROPORZIONE AL TETTO e non più scritte a mano
  (`livelloBarattolo`): con le vecchie (≤5→1, ≤10→2, poi 3) e il
  tetto a 10 il livello 3 non sarebbe esistito MAI — pieno a 10, ma
  «≤10» lo fermava a 2. Così la leva può valere 6 o 40 e il vetro si
  riempie lo stesso in quattro passi; `prove.py` lo verifica su tre
  tetti diversi leggendo la formula dal client, non ricopiandola.
  Regia unica `aggiornaBarattolo(n)`: porta al livello giusto i soli
  `.jar-ico` che NON stanno dentro un `.card-jar` o un `.jar-btn`
  (quelli raccontano l'annuncio) e scrive «(N/tetto)» in
  `#preferitiConta`. PRIMO cassetto del Profilo
  «🫙 Nel tuo barattolo» (`renderPreferiti`, stato vuoto che
  invita). Il 🫙 sulle card della vetrina, prima rimandato, dal
  lug 2026 c'è (stile cuoricino Vinted): cerchietto `.card-jar` in
  alto a destra sulla foto in `cardHTML` (quindi vetrina, negozio e
  risultati) — carta semi-trasparente da salvare, arancio pieno da
  salvato, colori fissi come tutto ciò che vive sulla foto; il
  cartellino prezzo sta in basso a sinistra, non si pestano. Il
  livello del barattolino in card è PER-ANNUNCIO (lv0 vuoto / lv4
  pieno: dice «questo l'hai già messo via»), NON quello globale:
  `aggiornaBarattolo` salta i `.jar-ico` dentro `.card-jar` e
  `.jar-btn`, la regia per-card è `aggiornaJarCards()` (chiamata dopo
  caricaPreferiti — le card possono nascere prima del Set — e dopo
  ogni toggle: card, dettaglio e cassetto mai divergenti). Tocco con
  stopPropagation (non apre il dettaglio), scossellina all'aggiunta
  (il loop esistente copre anche le card), stesse guardie del
  cerchietto (mai DEMO/VETRINA/annunci propri; per gli anonimi
  NIENTE icona, coerente col dettaglio dove il cerchietto in VETRINA
  non esiste), tap target ~46px via `::after` sul cerchietto da 34.
  RIFLESSO DEL VETRO (lug 2026): jarSVG ha due pennellate celesti
  `.jar-lux` sul fianco sinistro, colore dal token `--jar-riflesso`
  (#BFE3F0, di sera più tenue #7FA3B5) — ovunque il barattolino
  compare (card, cerchietto del dettaglio, cassetto); dettaglio, non
  protagonista: non copre la lettura del livello.
  Le stelle del rating si mostrano solo se rating > 0 ("0 ★" farebbe
  danno ai venditori appena arrivati); dal lug 2026 le accende il
  sistema di feedback (vedi server.py).
  Scheda Profilo 👤 (lug 2026): nata quarta voce di nav, dal lug 2026
  ci si arriva dal tasto-tappo in testata (vedi redesign: la nav è a
  3 voci; `view-profilo` e il ramo `profilo` in `go()` rilanciano i
  render come sempre, e in VETRINA non c'è proprio il tasto). È a CASSETTI
  richiudibili stile Vinted (CSS `.acc`, header cliccabile con
  emoji+titolo+freccia, `toggleAcc()`; tutti chiusi di default): dopo
  la testata sempre visibile `renderProfilo()` (nome, badge,
  vendite/acquisti conclusi da `/api/me`, stelle solo se rating>0,
  link del negozio con condividi), in ordine: «📋 I tuoi annunci»,
  «🆔 Identità» (righe identità + campo npub + verifica, riuniti
  nello stesso cassetto; si chiamava «Identità e Nostr», accorciato
  col feedback dei tester), «⚡ Incassi e pagamenti» (NWC +
  campo Lightning address `lnAddrProfilo`, che riusa
  `POST /api/me/ln-address`, + export CSV; il payoutPanel dentro
  l'ordine resta dov'è, e in DEMO l'intero cassetto — id
  `walletBlocco` — sparisce), «🔔 Avvisi», «🏅 Distintivi», stats
  admin, bottone Esci solo in modalità WEB. I cassetti senza nulla da
  mostrare spariscono interi; gli id interni dei blocchi sono gli
  stessi di sempre (arrivano da Vendi, traslocati TAL QUALI): Vendi è
  tornato SOLO il form di pubblicazione, e dopo pubblica/modifica si
  apre il dettaglio dell'annuncio appena salvato (l'id arriva da
  `{ok,id}`, ripiego su Esplora se non è in lista).
  PWA installabile (lug 2026, Fase 1 del percorso PWA→APK→Zapstore;
  percorso ormai completo: Fase 2 = icona adattiva, Fase 3 =
  «Distribuzione dell'APK», più sotto): `manifest.json` (id/
  start_url/scope "/", standalone, crema+arancio, 4 icone any+maskable
  generate da `genera_icone.py` — dal lug 2026 ritagliate da
  `assets/barattolo-icona-sorgente.jpeg` (2048px, barattolo già
  composto sul suo arancione: fondo CAMPIONATO dagli angoli, bbox a
  soglia con l'ombra dentro, mai upscale), any al 90% e maskable al
  67% del lato (intero nel cerchio di sicurezza 80%, verificato con
  l'anteprima); si rilancia quando la grafica cambia, e chi la
  rilancia alza VERSIONE in sw.js: le icone sono in dispensa) +
  `sw.js` PRUDENTE servito dalla RADICE, sempre
  no-cache. Il SW: dispensa `statica-{VERSIONE}` con addAll atomico
  (asset di casa + `/vendor/nostr.js` + `offline.html`), cache-first
  runtime SOLO per i Google Fonts (`font-{VERSIONE}`), navigazioni
  network-first con ripiego su `/offline.html` (mascotte dalla
  dispensa) a rete morta — gli header anti-cache di `/` restano
  sovrani. MAI toccate (nemmeno respondWith): `/api/*`, `/foto/*`
  (cache HTTP propria), telegram.org (script che gestiscono l'auth),
  metodi non-GET. Niente skipWaiting: la versione nuova aspetta la
  visita successiva; REGOLA: chi cambia un file in PRECACHE alza
  `VERSIONE`. VINCOLO DI FERRO: dentro la WebView di Telegram tutto
  identico — il SW si registra solo con `!tg?.initData` (e protocollo
  http: la DEMO da file:// non esplode); la WebView ha comunque
  storage separato dal browser, niente unregister (sarebbe esso
  stesso comportamento nuovo). Banner «🫙 Porta Barattolo in tasca»
  (`#installBanner` sotto l'header di Esplora, `bannerInstallaPwa()`):
  solo web MOBILE fuori da Telegram, mai se già standalone, mai in
  DEMO; NESSUNA dismissione persistente (le chiavi storiche
  installa_pwa e pwa_installata in barattolo_hint sono inerti): sia
  il «Non ora» sia appinstalled sono RINVII di pagina (variabile in
  memoria, mai localStorage) — alla visita successiva il banner
  torna, così dopo una disinstallazione ricompare da solo; il caso
  «app installata» lo coprono le guardie standalone, più il fatto
  che Chrome non rilancia beforeinstallprompt ad app installata (su
  iOS e Firefox, senza appinstalled né evento, chi ha installato
  rivedrà il banner nel browser: accettato); Android Chrome/Edge =
  beforeinstallprompt intercettato + prompt vero, iOS e Firefox
  Android (che beforeinstallprompt non ce l'ha) = foglietto
  `#installSheet` coi passi scritti da apriInstallSheet() secondo il
  browser (Safari: Condividi ⬆️; Firefox: menu ⋮ → Installa). Login
  in standalone
  (dichiarato): anonimo = vetrina completa con gli inviti di sempre;
  Nostr bunker/nsec = strada maestra (tutto in pagina, niente popup;
  su iOS lo storage è separato da Safari: login da rifare una volta);
  widget Telegram = da verificare in produzione (Android eredita il
  cookie dal profilo Chrome, il popup callback è fragile; su iOS
  probabilmente resta solo Nostr). Piano di riserva dichiarato e NON
  costruito: widget in modalità redirect (`data-auth-url` + endpoint
  GET che riusa `verifica_login_widget`), solo se il collaudo vero lo
  esige. Lighthouse: dalla v12 la categoria PWA non esiste più — il
  criterio è «installabile senza avvisi» nel pannello Application.
  Icona adattiva dell'APK (lug 2026, TWA): Bubblewrap (1.24.1) NON sa
  fare i due livelli — il suo ic_launcher.xml mette l'INTERA maskable
  nel background su bianco, foreground trasparente: niente parallasse
  e ai bordi il confine tra arancioni; il monochromeIconUrl del
  twa-manifest serve solo a notifiche e shortcut. `genera_icone_apk.py`
  patcha il progetto TWA generato (fuori dal repo, `..\..\barattolo-twa`,
  coi keystore: MAI portarlo dentro): campiona l'arancio con LA STESSA
  ricetta importata da genera_icone.py → `iconBackground` in colors.xml
  (#F78F19: sfondo e barattolo dalla stessa foto, il confine non può
  esistere); scontorna il barattolo (alpha a rampa dalla distanza dal
  fondo, fori interni richiusi col floodfill dall'esterno a 1/4 di
  risoluzione) → ic_launcher_foreground.png nei 5 mipmap (canvas
  108dp, barattolo ~51%: la presenza della maskable riportata al
  cerchio sicuro 66dp); silhouette bianca con la stessa alpha →
  ic_launcher_monochrome.png (temi Android 13+, esige compileSdk ≥33);
  riscrive ic_launcher.xml a tre livelli, allinea il fondo dello SPLASH
  allo stesso arancio campionato (twa-manifest `backgroundColor` + la
  copia in app/build.gradle: lo splash mostra l'immagine dell'icona, e
  sul crema del manifest faceva l'effetto francobollo — il crema resta
  giusto per la PWA, dove background_color è anche il fondo pagina
  pre-paint), ridisegna i drawable-*/splash.png col barattolo
  scontornato su trasparente a 160dp di lato massimo (~40% del lato
  corto; Bubblewrap ci metteva la tessera INTERA a 300dp fissi, un
  macigno, e nel twa-manifest NON esiste una leva di scala:
  splashScreenFadeOutDuration è solo la dissolvenza, l'immagine è
  disegnata centrata a dimensione intrinseca — l'unica leva sono i
  pixel dei PNG) e rimette da solo -Xmx1024m in gradle.properties. LITURGIA di ogni release APK, sempre in
  quest'ordine: `bubblewrap update --appVersionName=X.Y` (alza lui il
  versionCode) → `python genera_icone_apk.py` → `bubblewrap build`
  (le password del keystore le batte Andrea nel SUO terminale) —
  l'update cancella e riscrive proprio i file patchati, lo script va
  SEMPRE rilanciato dopo. ATTENZIONE: anche l'«apply» del web manifest
  (la domanda che `bubblewrap build` fa quando vede il manifest del
  sito cambiato) sovrascrive gli splash — se lo script è già stato
  applicato rispondere `n`; se si risponde `y`, rilanciare lo script
  PRIMA di rifare il build. Verificato sulla 1.2 aprendo l'APK firmato
  con aapt2: tre livelli, alpha vera, adattiva per tutte le densità;
  il medaglione residuo sul telefono è lo stile icone del launcher
  Oppo, non l'APK.
  Distribuzione dell'APK (lug 2026, Fase 3 del percorso PWA→APK→
  Zapstore): due canali, la release GitHub è la FONTE UNICA di verità.
  Repo pubblico `kreamistudio-crypto/barattolo-releases` (satmarket
  resta privato: Obtainium e Zapstore esigono download anonimi) con
  README per gli utenti e `zapstore.yaml` nella root; le release hanno
  tag `vX.Y`, UN solo APK per release (`barattolo-X.Y.apk`, copia
  rinominata di app-release-signed.apk) + `.sha256` + note scritte a
  mano con l'hash. Obtainium segue il repo da solo; Zapstore ci pesca
  l'APK. CLI `zsp` (github.com/zapstore/zsp, SOLO Linux/macOS → vive
  in WSL Ubuntu, `~/bin/zsp`; il progetto corre, ricontrollare il
  README a ogni uso) pubblica gli eventi NIP-82 (32267 app, 30063
  release, 3063 asset) su `relay.zapstore.dev` e carica i file sul suo
  Blossom. CHIAVE NOSTR DEDICATA E FREDDA (scelta deliberata: NON
  quella della piattaforma, per separarne i destini): vive SOLO su
  foglietti + Bitwarden («Barattolo release Nostr»), MAI su
  VPS/disco/repo/chat; si usa in WSL con `read -rs SIGN_WITH &&
  export SIGN_WITH` (prompt nascosto) e `unset SIGN_WITH` a fine rito;
  perderla = gli utenti Zapstore reinstallano (GitHub non è toccato);
  la npub sta in `zapstore.yaml` (campo `pubkey`, whitelisting del
  relay). Il certificato Android è legato alla chiave con la prova
  NIP-C1 (kind 30509, `zsp identity --link-key`): esige la CHIAVE
  PRIVATA del keystore (verificato nel sorgente: firma una prova di
  possesso) e zsp non legge i JKS → rito del p12 TEMPORANEO: `keytool
  -importkeystore` (il keytool è nel JDK di Bubblewrap) →
  `barattolo.p12` accanto al keystore → link-key → `Remove-Item`
  SUBITO. La prova SCADE DOPO UN ANNO: rito da ripetere (ma è
  facoltativo: scaduta, le release escono lo stesso). LITURGIA
  release completa, dopo il `bubblewrap build` di sempre: 1) sha256 e
  `gh release create vX.Y` su barattolo-releases con APK + .sha256;
  2) in WSL `SIGN_WITH` col prompt nascosto → `zsp publish` → unset.
  Prima GitHub, poi Zapstore, sempre. Gli script del rito
  (`genera_chiave_release.py`, `profilo_release.py`) vivono in
  `..\..\barattolo-twa` col keystore, fuori dal repo; nessuno dei due
  scrive segreti su disco.
  LEZIONE publisher nuovo (lug 2026, da un bug vissuto): il popup
  «Trust this app?» di Zapstore resta APPESO per sempre se la npub
  del publisher non ha un profilo kind-0 — il client cerca il profilo
  solo in cache locale, senza timeout né ramo d'errore (verificato
  nel sorgente, relevant_who_follow_container.dart), e la precarica
  dai relay "social" damus/primal/nos.lol. Quindi: per OGNI npub
  nuova che firma release, PRIMA il kind-0 su quei relay, POI lo
  `zsp publish`. Il campo pubkey in zapstore.yaml non c'entra (è il
  whitelisting lato relay, il client non lo guarda). Senza follower
  il secondo stadio (web-of-trust via DVM Vertex) dice solo «No
  reputation information found» ma NON blocca: un follow kind-3 dalla
  piattaforma e la nota di presentazione lo popolano —
  `presenta_release.py` nel repo fa entrambi (una tantum, idempotente,
  legge e ESTENDE la lista follow esistente senza mai sovrascriverla,
  gira sul VPS con la chiave della piattaforma dal config).
- `config.py` — TUTTE le chiavi e impostazioni. NON è nella repo
  (.gitignore) e NON deve MAI entrarci. `config_esempio.py` è il modello.
- `importa_nostr.py` — importa annunci NIP-99/NIP-15 da Nostr.
  Il cuore è `importa_venditore()`, importabile: lo usa anche
  l'orologio del server, che rilancia l'import OGNI ORA in
  `asyncio.to_thread` (fail-open totale: errori = una riga in
  console). Al primo giro scrive il
  badge 🟣 verificato sul profilo del venditore (npub canonica bech32 via
  `hex_to_npub`, gemella di quella di server.py; mai sovrascrivere
  una npub diversa già dichiarata): così il login Nostr lo riconosce
  invece di creargli un account nuovo.
  DUE VITE, e vanno tenute distinte: lanciato A MANO
  (`python importa_nostr.py`, npub e VENDITORE_ID dal config) è com'è
  sempre stato — scrive dritto nel database, bypassa `pubblica()` e
  non verifica le firme: la fiducia sta tutta nella npub scritta nel
  config, il che va bene per un amico e non per uno sconosciuto.
  Chiamato dal SERVER riceve invece il `vaglio` (vedi «Import aperto»
  più sotto), che è il pezzo che chiude quel buco.
  `interroga()` fa DUE REQ separate sullo stesso websocket, annunci e
  cancellazioni kind 5, con `limit` propri (`LIMITE_ANNUNCI` /
  `LIMITE_CANCELLAZIONI`, 500) e aspetta ENTRAMBI gli EOSE — più il
  ramo `CLOSED`, o si resterebbe ad aspettare un EOSE mai dovuto. Con
  una REQ sola il tetto valeva per l'INTERA richiesta e i relay
  servono i più recenti per primi: un venditore con molte
  cancellazioni si spingeva fuori dalla finestra i propri annunci, in
  silenzio (misurato su una chiave con 206 kind 5: dei 200 eventi che
  tornavano, 197 erano cancellazioni e gli annunci letti erano 3 su
  17). `interroga_aperto()` è invece la spazzata SENZA filtro
  d'autore, e serve solo alla scoperta.
  `testo_evento(e)` è il cuore condiviso che dà titolo e descrizione
  GIÀ TRONCATI come finiranno nel database: lo usa `estrai_annuncio`
  per scrivere e il server per capire se un evento è cambiato davvero.
  Se i due divergessero, un annuncio fermo sembrerebbe cambiare a ogni
  giro (o uno cambiato sembrerebbe fermo).
  LEZIONE foto importate (lug 2026): il download è VERBATIM (mai
  ricompresso da noi), ma i relay sono la fonte di verità — quando
  il venditore ripubblica da un client che gli ricomprime le foto
  (successo con Primal: originali nitidi → 1024px qualità ~60 su
  blossom, content-addressed: l'originale non esiste proprio online)
  l'import sovrascrive i pieni locali con quelli, e i vecchi nitidi
  sono persi. Da allora `scarica_foto` ha la SENTINELLA: se il nuovo
  file pesa <60% del locale, riga «📉» nel journal (mai in silenzio),
  e cancella la `_min` gemella ormai stantia (la card ripiega sul
  pieno, il backfill la rifà al riavvio). Riparazione possibile solo
  dal venditore (ri-upload degli originali da un host che non
  ricomprime, o file consegnati a mano: un file rimesso sotto lo
  stesso nome è stabile finché gli URL dell'evento non cambiano —
  ricordarsi di cancellare anche la `_min`).
- IMPORT APERTO da Nostr (lug 2026, cantiere di Alan + le correzioni
  decise da Andrea). Il codice sta in server.py, accanto all'orologio;
  qui perché è la seconda vita di importa_nostr.py.
  Non si importa più UN venditore scelto a mano: si importa chiunque
  pubblichi annunci NIP-99 in italiano, e i filtri sono due — la
  lingua e la legge.
  L'INTERRUTTORE `IMPORT_NOSTR_APERTO` nasce a FALSE nel codice e nel
  config d'esempio, al contrario di POST_AUTOMATICI e degli altri, ed
  è deliberato: il config del VPS non ha la chiave, quindi con un
  default True basterebbe un `git pull` e un riavvio perché la
  scoperta cominci ad aprire account e a mandare DM a estranei. Un
  salto così si fa con un gesto, non per distrazione — e quella riga
  è anche l'interruttore d'emergenza se il primo giro va storto.
  ZERO migrazioni di schema, e non è un risparmio furbo: essere su
  Barattolo È essere su Nostr, il mercatino è una VISTA degli eventi e
  non una copia. Quindi niente registro dei venditori (si deduce),
  niente flag «toglietemi da qui» — l'uscita esiste già ed è nativa
  del protocollo: un kind 5, che le lapidi rispettano per sempre. Un
  flag nostro sarebbe una seconda verità accanto a quella dei relay.
  DUE MESTIERI DISTINTI, e devono restarlo: la SCOPERTA
  (`scopri_venditori_nostr`, ogni 6h) setaccia i relay senza filtro
  d'autore per trovare npub nuove; l'IMPORT chiede chiave per chiave.
  Una spazzata sola non basta: i relay servono i più recenti e 500
  eventi coprono poche settimane di TUTTO Nostr — misurato, la
  spazzata globale non vedeva nessuno dei 17 annunci che la query
  mirata trovava tutti. Tetto `MAX_VENDITORI_NUOVI_GIRO` (10), i più
  prolifici per primi.
  CHI SI IMPORTA: `venditori_nostr_attivi()` = chiunque abbia una
  chiave di cui ha dimostrato il possesso — `npub_accesso` o badge
  `npub` VERIFICATO. È la regola di `notifica()` e dei ponti: mai una
  npub nuda. SCELTA DICHIARATA (decisione di Andrea): ci sono dentro
  anche gli utenti Telegram che avevano verificato la npub solo per il
  badge 🟣, e i loro annunci NIP-99 compaiono qui senza che nessuno
  glielo abbia chiesto. È corretto — se uno pubblica su Nostr è giusto
  che compaia su Barattolo — e i doppioni li prende la deduplica che
  esiste già.
  FILTRO LINGUA `annuncio_italiano`: tre prove dalla più forte alla
  più debole — la zona è un comune vero (passa dal motore geografico
  di casa, che sa che «Como» è un comune ma «como» in una frase
  spagnola no), la zona nomina l'Italia a PAROLA INTERA, oppure il
  testo ha ≥3 PAROLE FUNZIONE italiane (`PAROLE_FUNZIONE_IT`: «di»,
  «che», «per»… un annuncio inglese può dire «vendo» per caso, non
  dice quelle tre insieme). Il confronto è SEMPRE a parole intere: il
  vecchio filtro a sottostringhe prendeva «instal-LAZIO-ne» e
  «a-ROMA-tico», e su 1044 annunci veri ne dichiarava italiani 70 di
  cui 27 stranieri.
  FIRME VERIFICATE DAVVERO (`verifica_firma_nostr`): con un venditore
  fidato ci si poteva fidare del campo `authors` dei relay; da queste
  chiavi ora nascono ACCOUNT, e un relay bugiardo potrebbe attribuire
  annunci a chiunque. Ricetta di `verifica_evento_login` (id
  ricalcolato NIP-01, mai quello ricevuto), senza coincurve = False.
  L'ANELLO CHE SI CHIUDEVA (lug 2026, bug vissuto al primo giro vero:
  40 annunci fantasma — la sezione più importante di questa voce,
  perché è l'errore che la struttura del cantiere invitava a fare).
  La scoperta setaccia i relay SENZA filtro d'autore, e fra gli
  annunci NIP-99 italiani con firma valida ci sono anche i NOSTRI —
  quelli che la piattaforma firma per conto di chi pubblica da qui.
  Nessuno la escludeva: è nato un account intestato alla nostra stessa
  chiave, e l'import ha ricominciato a scaricare in casa ciò che
  avevamo appena pubblicato. Ogni annuncio nativo si è ritrovato una
  copia intestata a un venditore che non esiste, e il negozio di quel
  venditore pieno di roba di persone diverse — che è anche perché
  «Altri oggetti di questo venditore» mostrava oggetti di altri: la
  striscia faceva bene il suo mestiere su un negozio che era una
  discarica. Un solo bug, tre sintomi che sembravano tre bug.
  Il rimedio è `chiave_di_casa(chiave)` (hex o npub, maiuscole
  comprese), usata in DUE punti: `scopri_venditori_nostr`, che non ci
  adotta più, e `venditori_nostr_attivi`, che salta la nostra chiave
  ANCHE se in `utenti` la riga esiste già — ed è quella che ferma il
  danno al primo riavvio, senza aspettare la pulizia. Il confronto è
  sulla CHIAVE e non sul tag `d` ('barattolo-…') o sul tag `r`:
  quelli li può scrivere chiunque, la firma no.
  E IL BUCO VERO, che il fantasma ha solo reso visibile:
  `importa_venditore` credeva sulla parola al filtro `authors` della
  REQ. Ora confronta `e["pubkey"]` con la chiave chiesta e scarta il
  resto. La firma si verificava già, ma risponde a un'ALTRA domanda —
  «l'evento è firmato dalla chiave che DICHIARA?», non «quella chiave
  è il venditore che ho CHIESTO?»: le due insieme chiudono, una sola
  non chiude niente. L'autore di un evento decide A CHI VANNO I SATS
  di chi lo compra. Vale anche per i kind 5: una cancellazione altrui
  col tag `e` giusto avrebbe spento l'annuncio di un altro, perché il
  tag `e` non nomina l'autore. `prove.py` ha una SENTINELLA che
  verifica che quel confronto esista ancora dentro importa_venditore:
  è il tipo di riga che sparisce in un refactor.
  La pulizia delle copie già nate è `ripulisci_anello_nostr.py` (vedi
  sotto).
  IL RIFLESSO NON È UNA FONTE (ago 2026, la stessa lezione dell'anello
  con la chiave dell'ALTRO — trovata leggendo il codice e riprodotta
  prima di toccare niente). Dal BIVIO, l'annuncio di chi ha una chiave
  provata esce sul SUO account: lo componiamo noi (`evento_annuncio`)
  e a firmarlo è il suo browser. La riga resta NATIVA — `contatto_nostr`
  e `nostr_origine_d` vuoti, solo `nostr_event_id` e `nostr_autore` —
  ma quel venditore è in `venditori_nostr_attivi`, quindi l'import
  RILEGGE i suoi eventi, `barattolo-{id}` compresi. `chiave_di_casa`
  non lo para: esclude la chiave della PIATTAFORMA, e qui la chiave è
  la SUA.
  A scattare era il match per TITOLO (quello per `d` non può: la riga
  nativa ha `nostr_origine_d` vuoto), la cui clausola ammette proprio
  quel vuoto — e da lì la riga veniva ADOTTATA: `contatto_nostr` e
  coordinata scritte addosso, e l'annuncio nato qui diventava un
  importato a tutti gli effetti. Le conseguenze, tutte riprodotte:
  `modifica()` e la ricarica dello stock rispondono 400; la via di
  scampo `modifica-firmata` esige `npub_accesso`, quindi chi ha SOLO
  il badge 🟣 verificato resta senza NESSUNA strada; una sua NIP-09 da
  un client qualunque spegne la riga su Barattolo (prima non faceva
  niente); la descrizione si prende il FOOTER promozionale, perché il
  BIVIO firma con `evento_annuncio` — è esattamente ciò che la
  modifica firmata evita apposta, e il BIVIO non lo sapeva; le foto si
  riscaricano da noi stessi con nomi NON versionati, quindi la `_min`
  non combacia più; e la riga diventa «a due teste», che il libro
  mastro considera già un guasto suo.
  IL RICONOSCIMENTO È UNA DOMANDA AL DATABASE, NON AL TESTO
  DELL'EVENTO, ed è la parte da non ammorbidire: TRE condizioni
  insieme — il `d` è una coordinata nostra (`id_riflesso`), la riga
  che nomina è NATIVA, e quella riga l'abbiamo fatta firmare proprio a
  QUELLA chiave (`e_riflesso`, due giudici puri torturati in CI). Col
  solo prefisso `barattolo-` ci si affiderebbe a una convenzione di
  stringa che chiunque può scrivere; con tutte e tre, a mentire
  dovrebbe essere il nostro stesso database. `nostr_autore` vuoto non
  basta MAI (vuol dire riga mai firmata, e due vuoti che si somigliano
  non sono una prova) e la colonna è entrata nella lista delle
  migrazioni di `importa_nostr.py`, o lo script lanciato a mano su un
  database vecchio non filtrerebbe niente in silenzio.
  Il filtro sta PRIMA del vaglio, e non è un dettaglio: così non si
  paga l'AI per rigiudicare un testo che la moderazione ha già
  approvato quando l'annuncio è nato — e soprattutto un «dubbio» non
  può rimandare in revisione un annuncio VIVO e in vetrina, che era il
  modo peggiore in cui questo bug poteva presentarsi (l'evento non
  combacia mai col database finché l'adozione non avviene: il footer).
  LA PERDITA DICHIARATA: se il venditore modifica quell'evento da
  Amethyst — titolo, prezzo, zona — Barattolo non lo recepisce più e
  le due copie divergono in silenzio. È il verso giusto: quell'annuncio
  è NATO QUI e ha categoria, condizione, stock, spedizione e magari
  un'asta che sui relay non esistono, e lasciare che un evento li
  ricopra è proprio ciò che rompeva la modifica. Ma è una perdita
  vera, non un effetto collaterale gradito.
  LA STRADA SCARTATA, e va tenuta perché è quella che torna in mente:
  non adottare il contenuto ma OBBEDIRE LO STESSO AL KIND 5 (facendo
  matchare le cancellazioni anche su `nostr_event_id`), cioè
  «modifichi qui, ritiri da dove vuoi» — più nostr-nativo, e forse
  quello che un bitcoiner si aspetta. Scartata perché il kind 5 si usa
  con leggerezza: chi ripulisce la sua cronologia sui relay
  chiuderebbe il negozio qui senza volerlo, e la LAPIDE è per sempre —
  non potrebbe rimettere in vendita quell'annuncio senza ripubblicarlo
  con un `d` nuovo. Fra un ritiro che obbedisce a metà e una regola
  sola, la regola. Chi la riproponga porti il pezzo che manca: un modo
  di distinguere «ritiro questo annuncio» da «faccio pulizia».
  IL CASO VERO DEL CANTIERE, che spiega perché in produzione il
  contatore diceva zero: l'annuncio 173 (copia dell'89 nata
  dall'anello) porta `nostr_origine_d='barattolo-89'` ed era ancora
  ATTIVO, quindi intercettava il match per `d` a ogni giro e faceva da
  PARAFULMINE all'89. Toglierlo per primo avrebbe scoperto l'89 al giro
  successivo — l'ordine dei lavori era vincolante, prima il tappo e poi
  la pulizia, ed è la stessa trappola per chiunque ripulisca a mano dei
  doppioni: si guarda cosa stava riparando la riga che si sta togliendo.
  MODERAZIONE, e qui i due strati finiscono in modo DIVERSO:
  le PAROLE VIETATE restano uno scarto secco (deterministico: armi e
  droga non vogliono una coda ma una porta chiusa; resta nel registro,
  che i moderatori leggono); l'AI invece NON scarta più niente da sola
  — ogni verdetto diverso da OK, dubbio E bocciatura, fa nascere
  l'annuncio in `stato='revisione'`. È la terza via allargata al
  giudizio più delicato che abbiamo: annunci di gente che non è qui a
  difendersi, in un italiano che non abbiamo scelto noi, dove un'AI
  che sbaglia in silenzio fa perdere un venditore onesto senza saperlo
  mai. Meccanica: il vaglio MARCHIA l'evento (chiave `_revisione`) e
  l'import legge il marchio (stato alla nascita, e un annuncio già in
  vetrina il cui TESTO è cambiato e che non si sa più approvare torna
  in attesa, come una modifica dal form); `_apri_revisioni` gira DOPO
  l'import — quando l'id esiste, l'ordine di `pubblica()` — iscrive il
  motivo nel registro e manda la tastiera ✅/❌, idempotente sul
  registro (un annuncio fermo in coda una settimana non suona ogni
  ora); da lì in poi lo scudo anti-resurrezione lo salta da solo.
  Il ponte `_MOTIVI_REVISIONE` (titolo → motivo) sta in memoria: un
  riavvio lo perde e l'annuncio resta in coda col motivo generico.
  LA MODERAZIONE SI PAGA UNA VOLTA SOLA (`_da_giudicare`): prima si
  vagliava tutto a ogni giro, cioè ogni ora, per farsi ridire la stessa
  cosa sugli stessi testi. Si rigiudica quando cambia il TESTO, non
  l'evento: l'id è l'impronta di tutto (prezzo, foto, data) ma la
  moderazione legge solo titolo e descrizione, e un ritocco al prezzo
  non può cambiare un verdetto. Mai su ciò che non è più attivo (in
  revisione aspetta un umano, rimosso è deciso, e l'import li salta
  comunque). Il fail-CLOSED resta ma preciso: se l'AI tace non entra
  ciò che non è mai stato giudicato, mentre chi era già passato
  continua ad aggiornarsi.
  IL BENVENUTO È L'UNICO MESSAGGIO CHE MANDIAMO SENZA PERMESSO, e
  questa è la regola che governa tutto il resto. Chi viene scoperto
  riceve l'account nativo (la macchina del login Nostr) e UN messaggio
  (`BENVENUTO_NOSTR`, testo definitivo scritto da Andrea — chi lo
  ritocca tenga l'ordine: cos'è Barattolo (sats + deposito di
  garanzia), che facciamo da vetrina a Nostr, cosa si sblocca entrando
  (lampo, spedizione col costo suo, ritiro, buoni e codici online,
  condizioni/quantità/categoria), la reputazione che si costruisce
  vendendo, il progetto in fase di test con la sua npub, e in fondo la
  riga sui suggerimenti — «di serie non ti scriviamo più»).
  I SUGGERIMENTI SUGLI ANNUNCI (lug 2026 opt-in, ROVESCIATI ago 2026 —
  decisione di Andrea). Un evento NIP-99 non dice consegna, condizione
  e categoria — ed è proprio ciò su cui il compratore filtra — quindi
  `_chiedi_completamento` sa cosa manca e lo dice. Nacque automatico,
  poi divenne opt-in perché un consiglio mandato a chi non ha chiesto
  niente è spam; dall'ago 2026 torna ACCESO di serie, e la lezione del
  giro è che LA DIFFERENZA TRA UN CONSIGLIO E LO SPAM NON ERA
  L'OPT-IN, ERA LA FREQUENZA — l'opt-in non lo accendeva quasi
  nessuno, e intanto il tetto per ANNUNCIO faceva arrivare cinque
  messaggi a chi ne pubblicava cinque in un pomeriggio.
  IL RITMO È LA METÀ CHE CONTA, e va tenuto anche se un giorno il
  default tornasse spento: al massimo UNO ogni
  `SUGGERIMENTI_OGNI_GIORNI` (7) per PERSONA, qualunque sia la coda.
  Il perché va scritto perché è quello che rende la regola non
  negoziabile: CHI SI STUFA BLOCCA IL BOT, e col bot bloccato non
  riceve più le notifiche degli ordini, che sono portanti. Su Nostr il
  danno è identico e meno visibile — smette semplicemente di leggere i
  DM, e non se ne accorge nessuno. Nessun consiglio vale quel rischio.
  Giudice unico `_puo_suggerire` (interruttore + ritmo in una domanda
  sola, perché chi manda deve poterne fare UNA) e `_timbra_
  suggerimento`, che scrive `utenti.suggerito_il` PRIMA dell'invio —
  il patto delle campagne, e qui raddoppiare vorrebbe dire proprio la
  raffica che il ritmo esiste per togliere. La leva a 0 spegne il
  RITMO, non i suggerimenti: è la raffica di ieri, un freno
  d'emergenza e non una taratura.
  «MAI INSIEME» NON È UNA REGOLA SCRITTA, è quel timbro: due
  suggerimenti nello stesso giro passano dallo stesso giudice, e il
  secondo trova la porta che il primo ha appena chiuso. Un meccanismo
  solo per due garanzie — il ritmo fra i giri e il «mai insieme»
  dentro il giro — invece di due che un giorno divergono. Per la
  stessa ragione il COMPLETAMENTO ha la precedenza senza che nessuno
  scriva un ordine: gira dentro l'import, che nell'orologio viene
  prima di `suggerisci_funzioni`. Ed è giusto che vinca lui — un
  annuncio incompleto è già in vetrina e non lo trova nessuno, mentre
  lo sconto e la spedizione gratis sono occasioni che possono
  aspettare.
  COME SI DISTINGUE «MAI TOCCATO» DA «SPENTO DA LUI» (la domanda di
  Andrea, e la risposta ha due metà). La prima: una colonna del GESTO,
  `utenti.suggerimenti_scelti` (0 = non l'ha mai toccato), letta dal
  giudice `suggerimenti_accesi(scelti, valore)` — il valore vale solo
  se c'è stato un gesto, altrimenti comanda la leva. UNA COLONNA E NON
  UN TERZO STATO dentro l'altra: con «2 = spento esplicito» il primo
  `if u["suggerimenti_annunci"]` scritto distrattamente leggerebbe 2
  come ACCESO, cioè fallirebbe nel verso di scrivere a chi ha detto
  no; così invece il valore conserva per sempre il suo significato,
  che è il patto delle due soglie dello sconto e delle due tariffe di
  spedizione. Da qui il rovesciamento del default è REVERSIBILE: chi
  ha scelto non viene scavalcato mai, in nessuno dei due versi, e c'è
  la prova che lo tortura.
  LA SECONDA METÀ È QUELLA CHE NON SI PUÒ SAPERE, e va detta invece di
  far finta: del PREGRESSO il gesto non esiste. Fino all'ago 2026
  l'endpoint scriveva solo il valore, quindi chi è a 0 può essere chi
  non l'ha mai guardato O chi l'aveva acceso e poi spento, e nessuna
  traccia li distingue. `registra_gesti_suggerimenti()` (all'avvio,
  idempotente) fa l'unica cosa dimostrabile — chi è a 1 l'ha
  CERTAMENTE acceso lui, di serie era spento, quindi quello è un gesto
  e da adesso è registrato — e per gli altri si sceglie «mai toccato»,
  DICHIARANDOLO. Il prezzo è UN messaggio a chi l'aveva spento, e quel
  messaggio porta in fondo il modo di rispegnerlo: da lì il gesto è
  registrato e non si perde più.
  ATTENZIONE, il gate sta PRIMA di ogni lettura e non è pignoleria: a
  interruttore spento — o col ritmo ancora chiuso — non si timbra
  `completamento_avvisato`, o quegli annunci resterebbero «avvisati»
  senza che nessuno abbia avvisato niente, e il consiglio non
  partirebbe mai più.
  I DUE SUGGERIMENTI DI FUNZIONE (ago 2026) non dicono cosa manca a un
  annuncio, ma che c'è una leva del negozio ancora spenta: lo SCONTO
  CARRELLO e la SPEDIZIONE GRATIS. Catalogo `SUGGERIMENTI_FUNZIONE`
  (timbro, leva, SQL, testo) + `suggerisci_funzioni` nell'orologio;
  una volta sola per funzione e per sempre, coi timbri
  `suggerito_sconto`/`suggerito_sped` — colonne come le quattro
  sorelle di casa (`avvisato_contatto`, `avvisato_spedizioniere`…), che
  il ritmo è un'altra cosa e vive per conto suo. La condizione di
  ognuno dice anche A CHI NON SI MANDA, ed è la parte che li tiene
  onesti: lo sconto carrello vuole ALMENO DUE annunci attivi (sotto
  non potrebbe scattare mai, vale da due oggetti diversi in su) e la
  spedizione gratis solo a chi SPEDISCE davvero (al ritiro e al codice
  online non c'è nessuna spedizione da offrire). E ognuno guarda la
  SUA leva del server: suggerire una funzione spenta sarebbe mandare
  qualcuno a cercare un cassetto che non c'è.
  LA CIFRA DENTRO IL TESTO è passata dai sats agli euro col cantiere
  delle soglie (ago 2026): la voce della spedizione gratis diceva «Da
  100.000 sats di articoli la spedizione la offro io», adesso dice «Da
  25 €». I 12 venditori che l'avevano già ricevuta NON la ricevono di
  nuovo — il timbro `suggerito_sped` è già scritto per loro e nessuno
  lo tocca — e va bene così: la sostanza era ed è la stessa
  (decisione di Andrea). La voce dello SCONTO non si è toccata: il suo
  esempio è «da 3 articoli, −10%», cioè il criterio a pezzi, che di
  valute non parla.
  `TIMBRI_SUGGERIMENTO` è una whitelist e l'elenco È la guardia: il
  nome della colonna finisce dentro una query, e un nome che arriva da
  altrove non deve poterci entrare mai — nemmeno oggi che i chiamanti
  sono due e passano due letterali. Ha la sua sentinella.
  LA CODA CON L'INTERRUTTORE sta in fondo a OGNI messaggio e in un
  posto solo (`CODA_SUGGERIMENTI`): chi riceve un consiglio deve
  sempre vedere, nello stesso messaggio, come farlo smettere e ogni
  quanto arriverà. Il testo del benvenuto Nostr si è rovesciato con
  loro — diceva «di serie non ti scriviamo più», e lasciarlo sarebbe
  stata la bugia più facile del cantiere.
  `/api/me` dice lo STATO EFFETTIVO e non il valore grezzo, ed è la
  riga che sembra un dettaglio: col grezzo il bottone direbbe «Attiva»
  a chi li ha già accesi, e il suo tocco li SPEGNEREBBE. Il client
  riceve anche `suggerimenti_ogni_giorni` e non hardcoda mai il
  numero. Resta vero il resto: mai nel giro in cui l'annuncio è
  apparso (`creato < t0`), un messaggio per VENDITORE e non per
  annuncio, ogni voce dice A COSA SERVE (un motivo, non un
  rimprovero), il paragrafo sul codice online solo a chi non ha
  dichiarato nessuna consegna.
  RISCHIO DICHIARATO E ACCETTATO (decisione di Andrea): si può
  comprare in escrow da un venditore che non sa di essere qui. Prima
  valeva per un venditore consenziente, ora per chiunque venga
  scoperto. È accettato perché è esattamente il problema che il
  deposito di garanzia esiste per risolvere: i sats restano bloccati
  finché il compratore non conferma, e se il venditore non si fa vivo
  il rimborso è la via normale. Il DM di benvenuto arriva PRIMA che se
  ne accorga da solo, ed è il motivo per cui questo non è uno scippo.
  LIMITE NOTO: `venditori_nostr_attivi()` spende una query a vuoto
  ogni ora per ogni utente con badge verificato che non vende su
  Nostr. Irrilevante ai numeri di oggi; con migliaia di utenti servirà
  un tetto per giro.
  RESTANO FUORI dal cantiere, per scelta: il relay Barattolo
  (infrastruttura, cantiere a parte), la PR al repo dei NIP, e il form
  per completare i metadati direttamente sugli importati.
- METADATI DI COMMERCIO NEI TAG NIP-99 (lug 2026): la spec non dice
  nulla di spedizione, condizione e quantità, e finora le scrivevamo
  solo in prosa nel `content` — leggibili da un umano, invisibili a
  ogni macchina, comprese le NOSTRE al giro d'import successivo (è
  letteralmente il motivo per cui un annuncio importato arrivava senza
  consegna né condizione). In scrittura `tag_commercio` (server.py):
  `["delivery","shipping","5.00","EUR"]` ripetibile ·
  `["delivery","pickup"]` · `["delivery","digital"]` ·
  `["condition", new|like-new|good|fair|poor]` · `["stock","3"]`
  (assente = 1). `delivery` è RIPETIBILE apposta invece dell'enum
  chiuso di Shopstr: lì per dire «spedisco o ritiri» serve il valore
  composto "Free/Pickup", e un terzo modo vorrebbe enumerare tutti i
  sottoinsiemi. Il content continua a dire le stesse cose a parole
  (per le persone e per i client che il nostro vocabolario non lo
  conoscono): se un giorno divergessero, quella giusta è il TAG.
  In lettura `estrai_commercio` (importa_nostr.py) parla DUE dialetti,
  il nostro e quello de facto di Shopstr (`shipping` con l'enum,
  `quantity`, `pickup_location`). Due trappole collaudate: costo
  assente ≠ gratis («0» è gratuito, il tag senza importo è «da
  concordare»), e `weight` NON è un peso — per Shopstr è una VARIANTE
  di prodotto col suo prezzo, stessa arità e significato opposto, chi
  lo scambia scrive un dato falso. Restano fuori peso e dimensioni: la
  nostra taglia del pacco è una categoria di corriere italiana, non un
  fatto oggettivo, e ricavarne un peso sarebbe inventare.
  DUE GUARDIE che i relay non scavalcano (decisione di Andrea): lo
  stock si LIMA a `MAX_QUANTITA_ANNUNCIO` (l'import scrive dritto nel
  DB e non passa dai giudici dei payload; si lima e non si scarta,
  come `quantita_tollerante` del CSV — la merce c'è, è il numero a
  essere fuori scala) e la CONSEGNA DIGITALE non arriva mai dai relay
  (il codice passa DENTRO Barattolo, con endpoint, rivelazione-
  ricevuta e finestre di 24/48h: chi sta solo su Nostr non ha quel
  bottone, e promettere una consegna immediata che nessuno può fare
  sarebbe una bugia scoperta a sats già in cassaforte. Chi entra con
  la sua chiave la dichiara dal form, dove anche DIGITALE_MIN_VENDITE
  può dire la sua). CONSEGUENZA da ricordare: un annuncio importato
  che dichiara `delivery` ora ENTRA nei set — «gli importati restano
  fuori per costruzione» non è più vero, ed è giusto così: il catalogo
  è uno solo, cambia solo chi firma l'evento.
  Il disegno è documentato in `proposte/` (la PR al repo dei NIP resta
  in backlog).
- `ricategorizza.py` (lug 2026) — l'AI PROPONE, l'admin decide. Quando
  il catalogo è passato da 9 voci a 25, gli annunci di ieri sono
  rimasti nelle caselle di ieri (un portatile in «Elettronica» invece
  che in «Informatica», una Jade in «Elettronica» invece che in
  «Bitcoin») e quelli che arrivano da Nostr nascono TUTTI in «Altro».
  Lo script legge titolo e descrizione degli attivi, li manda a Haiku a
  lotti da 20 e scrive SOLO nella tabella `categoria_proposta`
  (annuncio_id PK, categoria_ora, categoria_nuova, stato
  proposta|applicata|scartata, deciso_da/deciso_il = anche il registro
  di cos'è successo). `annunci.categoria` non la tocca MAI: a spostare
  è un moderatore, dalla coda. Il catalogo lo legge dal TESTO di
  server.py (fonte unica) e non importando il modulo, che farebbe
  partire init_db e le migrazioni su un database magari diverso da
  quello passato a mano. Di serie non scrive (`--scrivi` riempie la
  coda; `--limite N`, `--rifai`, e un percorso di database come per
  ripulisci_anello). L'AI può rispondere NON SO ed è importante che
  possa: un annuncio lasciato dov'è non fa danno, uno spostato male sì
  — e una categoria inventata o un id fuori lotto si ignorano come nel
  parsing della moderazione a lotti. Idempotente: non richiede gli
  annunci che hanno già una riga fatta sulla categoria che hanno
  ADESSO (se l'ha spostato il venditore, la vecchia proposta non parla
  più di lui e si richiede). Costo misurato: ~0,005 $ a lotto, ~0,20 $
  per 800 annunci, e lo stampa contando i token veri.
  LA CODA (`GET /api/admin/categorie`, `POST
  /api/admin/categorie/decidi`, sezione «🗂 Categorie da sistemare» nel
  Profilo admin): le proposte escono RAGGRUPPATE per spostamento
  («Elettronica → Informatica: 23»), col gruppo più numeroso in testa.
  Il raggruppamento non è una comodità: trecento decisioni una per una
  sono una revisione che nessuno finisce, e il vincolo di Andrea —
  nessuna categoria cambia senza che un umano l'abbia vista — si
  rispetta mostrando i TITOLI dentro il gruppo, con la spunta per
  togliere dal mucchio quello che non convince (`ids` nel body).
  L'UPDATE è condizionato sulla categoria di partenza (il secondo
  moderatore trova il fatto compiuto, come per la revisione) e una
  proposta stantia — categoria cambiata nel frattempo — sparisce da
  sola dalla coda. Dopo lo spostamento gli annunci NATI qui aggiornano
  il loro evento NIP-99 (la categoria è il tag `t`, `solo_aggiornamento`
  sul `d` stabile); niente promo e niente match, che ricategorizzare
  non è pubblicare — la regola della ricarica dello stock. Il
  venditore NON riceve avvisi: la categoria è metadato NOSTRO (dai
  relay non arriva, e l'import non la ricopre mai, che è anche ciò che
  fa sopravvivere la decisione al giro orario). Il complemento è
  l'invito OPT-IN che esisteva già: `_chiedi_completamento` aveva la
  voce «la categoria giusta» ma la sua WHERE guardava solo
  `consegna='' OR condizione=''`, quindi un annuncio completo fermo in
  «Altro» non veniva pescato mai e quella voce non partiva mai —
  aggiunto `OR categoria='Altro'`. La stessa funzione non chiede più
  la condizione dove non vuol dire niente.
  DA SOLA, DOPO OGNI IMPORT (lug 2026, `ricategorizza_automatico` in
  server.py, in coda a `giro_import_nostr`): lo stesso mestiere dello
  script, ma senza che nessuno lo lanci. Il momento è l'import e non un
  orario fisso perché è l'import a creare il problema — gli annunci dai
  relay nascono tutti in «Altro» — e girare a vuoto non costa niente.
  CHI SI GUARDA: gli importati (`contatto_nostr!=''`) e chiunque stia
  in «Altro»; i nativi in una categoria vera hanno avuto un umano che
  l'ha scelta dal form, e la macchina non è lì per correggere le
  persone. I TRE FRENI, che sono la ragione per cui può girare ogni
  ora: 1) DECISO È DECISO — un annuncio su cui un moderatore si è già
  pronunciato, approvando O rifiutando, non si ripropone mai più da
  solo (`p.stato IN ('applicata','scartata')`, qualunque categoria
  abbia adesso); 2) e non si ripaga due volte ciò che è già in coda:
  niente chiamata se esiste già una proposta in attesa sulla categoria
  di ADESSO; 3) `MAX_RICATEGORIZZA_GIRO` (100 = 5 chiamate), che
  un'ondata la digerisce in più ore.
  IL FRENO 1 È NATO DA UN BUG VERO (lug 2026, visto da Andrea, e vale
  la pena tenerlo perché la trappola è sottile). Il freno di partenza
  era il solo 2, cioè «esiste una riga fatta sulla categoria di
  adesso»: copre il RIFIUTO — l'annuncio resta dov'era, la riga
  combacia — ma NON l'APPROVAZIONE, perché appena l'annuncio si sposta
  in «Sport e hobby» la riga vecchia dice «Altro» e non lo protegge
  più. Così l'AI riproponeva altrove un annuncio che una persona aveva
  appena sistemato, a ogni giro; e la nuova proposta SOVRASCRIVEVA la
  riga, cancellando la traccia di chi aveva deciso — quindi il registro
  si consumava da solo e il danno diventava anche invisibile. Il raggio
  era ristretto ai soli IMPORTATI: un nativo approvato esce dal raggio
  d'azione da sé (non è importato e non è più in «Altro»), un importato
  ci resta per sempre. Cintura in più: l'INSERT della macchina ha un
  `WHERE categoria_proposta.stato='proposta'` sul DO UPDATE, così una
  riga decisa non si sovrascrive nemmeno se un domani la query se ne
  dimenticasse. CONSEGUENZA DICHIARATA: un annuncio deciso resta deciso
  anche se il venditore ne riscrive il titolo. Riaprirlo al cambio del
  testo (una colonna con l'impronta, come `_da_giudicare` fa per la
  moderazione) è stato valutato e scartato: per gli importati il testo
  lo riscrivono i relay ogni ora, quindi sarebbe lo stesso giro, solo
  più lento e più difficile da vedere. Per riconsiderare si chiede a
  mano, `ricategorizza.py --rifai` — e la stessa regola vale ora anche
  nel default dello script, dove `--rifai` è il modo di chiederlo
  ESPLICITAMENTE. Più la leva `RICATEGORIZZA_AUTO`
  nel config (default **True**, al contrario di IMPORT_NOSTR_APERTO: qui
  non esce niente verso nessuno — si riempie una coda che un moderatore
  guarderà, e in vetrina non cambia nulla finché non approva). UNA
  notifica aggregata ai moderatori per giro, coi GRUPPI e non i titoli
  (chi modera decide sul gruppo, e venti righe in chat non si leggono),
  e solo se quel giro ha prodotto qualcosa: una coda ferma non suona
  ogni ora. Il prompt e il parsing NON si riscrivono: `_chiedi_categorie`
  importa `PROMPT` e `RIGA` da ricategorizza.py, perché un prompt in due
  copie è un prompt che diverge — si corregge una, si dimentica l'altra,
  e la coda si riempie di proposte diverse secondo chi le ha chieste.
  Fail-open totale come la moderazione: lotto saltato = si riprova al
  giro dopo.
- `sposta_a_mano.py` (lug 2026) — gli spostamenti che decidi tu, quando
  l'AI ha sbagliato o ha detto NON SO. Prende `pezzo di titolo=Categoria`
  (o `id=Categoria`), pesca gli attivi e scrive le proposte in coda come
  se le avesse fatte l'AI. NON tocca `annunci.categoria`, ed è il punto:
  lo spostamento vero resta UNO — il bottone della coda — perché è lì
  che vivono l'UPDATE condizionato, l'aggiornamento dell'evento NIP-99 e
  il registro di chi ha deciso; riscriverlo qui vorrebbe dire tenere
  allineati due posti che fanno la stessa cosa. Di serie non scrive
  (stampa id, titolo, categoria di adesso e venditore, così un frammento
  troppo largo si vede PRIMA); un frammento che pesca cinque poster li
  mette in coda tutti e cinque, ed è voluto.
- `ripulisci_anello_nostr.py` (lug 2026) — la pulizia una-tantum dopo
  l'anello (vedi sopra). Riconosce le copie dal marchio che solo NOI
  scriviamo — il tag `d` di un evento nostro è sempre `barattolo-{id}`,
  e l'id lì dentro è l'annuncio VERO da cui la copia discende, quindi
  ogni copia si lega al suo originale senza indovinare nulla. Di serie
  NON scrive: stampa cosa farebbe; accetta un percorso di database, e
  la prova generale si fa su una copia del file. Spegne le copie
  ('rimosso'), annulla gli ordini mai pagati, e NEUTRALIZZA il
  fantasma togliendogli le chiavi Nostr senza cancellarne la riga (una
  riga di utenti cancellata lascerebbe riferimenti ciechi in annunci,
  ordini e registro). MAI una NIP-09 verso i relay: quegli eventi sono
  i nostri, quelli degli annunci VERI — ritirarli cancellerebbe dalla
  piazza la merce buona. Tre guardie, e si ferma dicendolo: copia con
  affare in corso, account che ha anche annunci suoi (è una persona
  vera che ha raccolto copie per sbaglio), account con copie vive o
  ordini APERTI — quelli chiusi invece non fermano niente, la storia è
  storia e lasciargli la chiave vorrebbe dire tornare a importare per
  sempre. Idempotente.
- `ripulisci_avatar_min.py` (ago 2026) — la spazzata una-tantum dei
  francobolli gemelli degli avatar (il perché sta nella voce di
  `/foto`, sopra). Cancella da `foto/` i soli
  `av_{negozio}_{ts}_min.jpg`; NESSUNA riga di database si tocca — quei
  nomi nel database non ci sono mai stati, ed è esattamente il punto.
  LA GUARDIA è quella colonna: prima di cancellare legge
  `utenti.avatar` e se uno di quei file è la faccia di qualcuno lo
  lascia stare e lo DICE (vorrebbe dire che un `_min` ci è finito
  davvero, e allora non è spazzatura ma un dato); chi non ha la forma
  di `_salva_avatar` non si tocca e si nomina, mai una cancellazione
  silenziosa. Anteprima di serie, `--scrivi` per farla, percorso di
  database opzionale (il pattern di `ripulisci_anello_nostr.py`);
  idempotente, e si può girare a server ACCESO — un file che non
  chiede nessuno non manca a nessuno.
- `stima_coda_moderazione.py` (ago 2026) — quanto si allunga la coda
  da quando l'AI segnala invece di decidere. NON stima: prende i
  rifiuti VERI gia' registrati in `moderazione_log` e ci rifa' girare
  sopra il giudice nuovo (`_vietato_bloccante`, letto dal TESTO di
  server.py — mai importandolo, la lezione di ricategorizza.py),
  quindi dice il numero esatto e l'elenco dei motivi che passano in
  coda. È con QUEI motivi che il prompt si corregge a mano: se una
  famiglia si ripete, o è un falso positivo o merita una regola.
  LEGGE E BASTA — nessuna scrittura, si lancia a server acceso, e
  c'è la prova che nel suo corpo non compaia un INSERT.
- `anteprime.py` (ago 2026) — come si vede un link di Barattolo quando
  qualcuno lo incolla. Interroga un Barattolo (locale o vero) con gli
  User-Agent dei crawler di Telegram, WhatsApp, Facebook, Slack e dei
  client Nostr, legge SOLO i primi byte come fanno loro, ridisegna la
  card che ne verrebbe fuori, e misura l'og:image contro i limiti di
  ognuno (lato minimo e byte massimi, dove sotto/sopra la card grande
  non si disegna). Dice anche a che BYTE cade l'ultimo meta, che è
  l'invariante su cui poggia tutto: in cima, non in coda a 900 KB.
  Legge e basta, nessuna scrittura da nessuna parte. Serve al collaudo
  dopo il deploy, ed è lì che vale la regola scritta nella sua
  docstring: si prova con URL USA-E-GETTA — un annuncio di prova, da
  rimuovere subito — perché Telegram e WhatsApp cachano le card a lungo
  e dal nostro lato non si bustano; puntato sul dominio vero lo
  ricorda da solo in coda.
- `collaudo_impersonazione.py` (ago 2026) — la voce sull'impersonazione
  provata sul MODELLO vero, che è il pezzo che `prove.py` non può fare:
  la chiave Anthropic sta fuori dalla CI apposta. Prende
  `PROMPT_MODERAZIONE` dal TESTO di server.py (mai importandolo:
  l'import farebbe partire init_db e le migrazioni — la lezione di
  `ricategorizza.py`) e lo gira su 15 casi limite scelti dove la voce
  può sbagliare, con l'esito atteso accanto a ognuno. Va rilanciato a
  OGNI ritocco del prompt, e legge e basta.
  I FALSI POSITIVI sono la metà che conta, e la tabella è scritta per
  loro: un divieto sull'impersonazione formulato male diventa un filtro
  sulla parola «Barattolo», cioè un blocco su annunci legittimi. Il
  caso che lo dice meglio di ogni ragionamento è «Barattolo di vetro
  per conserve, 1 litro» — in italiano barattolo è anche un VASO, e chi
  ne vende sei non sta impersonando nessuno. Poi il titolo pulito con
  la descrizione avvelenata (la metà che un divieto scritto sul solo
  titolo perderebbe), una finta giacenza Poste (un ALTRO servizio), e
  tre regressioni: buoni leciti, servizi dubbi, armi vietate.
- `prove.py` + `.github/workflows/prove.yml` (lug 2026) — la rete di
  sicurezza, a ogni push e ogni PR. Solo pezzi PURI: niente config,
  database, relay o Anthropic — una CI che dipende da un server altrui
  diventa rossa quando quello ha il raffreddore, e a furia di rossi
  ingiusti si smette di guardarla. Le funzioni si estraggono da
  server.py per TESTO (`pezzo()`), senza importarlo: chi rifattorizza
  una funzione estratta deve aggiungere anche le sue dipendenze
  all'ambiente (è già successo con `_chiave_comune`, che
  `coordinate_da_zona` ha cominciato a usare). Il workflow fa anche
  `compileall` di tutti gli script (elenco a mano: chi ne aggiunge uno
  lo mette lì, o non lo guarda nessuno — ai tre nati il 3 ago 2026 è
  successo) e cerca segreti nella repo (la regola ferrea 1 in CI:
  `config.py`/`*.db`/`foto/` tracciati, nsec, token del bot Telegram e
  chiavi `sk-ant-`; lunghezze LARGHE apposta — meglio un falso allarme
  da guardare che un token vero che passa perché era un carattere più
  corto — e `grep -I` che salta i binari, o un byte messo per caso in
  una delle 52 illustrazioni fa diventare rossa la CI a caso, e una CI
  rossa a caso non la guarda più nessuno).
  DUE JOB E NON UNO (lug 2026, e il perché vale più della struttura):
  `prove` e `segreti` girano in PARALLELO, senza `needs`. Il controllo
  dei segreti era l'ultimo passo in coda alle prove, e da lì qualunque
  cosa fallisse prima lo nascondeva — non diceva «pulito» a torto: non
  parlava proprio. È successo per davvero: le prove si sono rotte alle
  13:20 del 3 ago 2026 e per 13 push di fila i segreti non li ha
  guardati nessuno, mentre GitHub diceva soltanto «rosso» — un semaforo
  solo per due domande diverse. Provato rompendo `prove.py` di
  proposito su un ramo usa-e-getta: `prove` fallito, `segreti` riuscito
  che dice «pulito». Entrambi `permissions: contents: read`.
  GLI SCRIPT «PURI» NON CHIEDONO IL CONFIG ALL'IMPORT, ed è LA regola
  che impedisce il bis. Chi importa un modulo per una costante non deve
  ritrovarsi il processo chiuso in faccia per una chiave che non gli
  serve: `ricategorizza.py` faceva `from config import DB,
  ANTHROPIC_API_KEY` in cima al file con un `sys.exit(1)` sotto, e
  `prove.py` lo importa per `catalogo()`, `PROMPT` e `RIGA` — roba pura
  che di chiavi non sa niente. In CI `config.py` non c'è PER PROGETTO,
  quindi le prove morivano sempre. Il config si chiede dentro `main()`
  (il modo di `sposta_a_mano.py`, che ha pure il ripiego a
  'satmarket.db'); il ripiego innocuo, tipo `MODELLO_RICERCA`, può
  restare in cima perché non chiude niente ed è un nome globale che
  serve alle funzioni. ATTENZIONE alla trappola che rende questa
  famiglia di bug invisibile: IN LOCALE PASSA SEMPRE, perché il config
  c'è — le 78 prove erano verdi sul portatile mentre la CI era rossa da
  nove ore. Non è una cosa che si becca girando le prove prima del
  push: si becca solo GUARDANDO la CI (`git push && sleep 4 && gh run
  watch --exit-status`), o provando in un clone senza `config.py`, che
  è la condizione vera.
  UNA PROVA SALTATA SI CONTA (ago 2026): il controllo del pareggio
  dell'inchiostro delle illustrazioni non era MAI girato in CI —
  Pillow non si installava, la prova si saltava da sola, e a dirlo
  c'era una riga discreta in mezzo a duecento spunte. In locale
  passava (in locale Pillow c'è), quindi guardare il verde non
  bastava: 211 prove invece di 212, e nessuno confronta i totali. La
  cura è a due strati perché il primo si può togliere per sbaglio
  come per sbaglio era stato omesso: `pillow` nel workflow, e
  `salta()` accanto a `prova()` con le saltate nella riga finale
  («252 passate, 0 fallite, 1 SALTATA») invece che nascoste nel
  totale. Più `PROVE_SEVERE`, acceso SOLO nel workflow: in CI le
  dipendenze si installano apposta, quindi lì una saltata vuol dire
  che qualcosa si è rotto e il job diventa rosso; in locale chi non
  ha Pillow gira le prove lo stesso e vede l'avviso contato. Chi
  aggiunge una prova che dipende da un pacchetto usi `salta()`, mai
  un `print` o un `return` muto: è quello il modo in cui una prova
  smette di esistere senza che nessuno lo sappia.
  IL PARSE DEL CLIENT È UNA PROVA (13 ago 2026, nata da un guasto
  VERO arrivato fino a main con la CI verde: un `*/` doppio in un
  commento JS — chiuso il commento a metà, la coda di prosa è
  diventata codice — ha ucciso l'INTERO script di miniapp.html al
  parse. App morta: niente card, niente barra collaudo, solo il
  markup statico. Le prove leggono miniapp.html come TESTO, quindi
  ~2900 sentinelle sulla forma erano verdi mentre il client non
  eseguiva UNA riga; l'ha visto il giro CDP successivo, non la CI).
  `prove_sintassi_client`: ogni `<script>` inline passa da
  `node --check`, e sw.js pure — parse puro, zero esecuzione, node
  c'è di serie sui runner GitHub; senza node in locale si SALTA
  contando, e in CI con PROVE_SEVERE una saltata vale una fallita,
  che per questa prova è esattamente il punto. Torturata rimettendo
  il `*/` doppio: rossa da sola. LA LEZIONE: una suite che legge un
  file come testo può certificare qualunque cosa TRANNE che quel
  file sia un programma — la prova più importante su un sorgente è
  che si lasci leggere dal suo motore.
  LO SCANNER DEI SEGRETI GUARDA ANCHE INDIETRO (ago 2026, audit):
  usava `git ls-files`, cioè i file tracciati ALLO STATO ATTUALE, e il
  checkout era shallow — un segreto committato e poi tolto passava per
  sempre, pur restando estraibile da `git log -p` da chiunque, che è
  esattamente il caso in cui la chiave va RUOTATA. Ora `fetch-depth: 0`
  e una passata sulle righe AGGIUNTE di tutta la cronologia (~2s per
  516 commit). E tre forme che nessuna regola guardava: le due chiavi
  LNbits (di cui una PAGA), il segreto del webhook e la chiave dei
  contenuti. Non hanno una forma propria — una invoice key sono 32
  esadecimali, che somigliano a mezzo mondo — quindi si ancorano al
  NOME della variabile con un valore non vuoto, e i segnaposto
  `INCOLLA_QUI` restano fuori: così la regola si estende da sola a
  ogni segreto futuro che rispetti quella convenzione. Le forme
  vivono in un posto solo (`env: FORME`), o i due passi
  divergerebbero. IMPERFEZIONE DICHIARATA nel file: `git log -p` non
  mostra i diff dei MERGE, quindi un segreto introdotto risolvendo un
  conflitto sfuggirebbe.
  Su Windows serve `PYTHONIOENCODING=utf-8`,
  o la console cp1252 esplode sulle spunte.

## Produzione

- VPS Hetzner Helsinki `46.62.162.103`, Ubuntu 26.04, servizio systemd
  `barattolo` (uvicorn su 127.0.0.1:8080 dietro Caddy con HTTPS).
- Dominio: https://barattolo.store — Bot: @ilbarattolobot (BotFather URL
  con `?v=2`, innocuo). Header anti-cache già attivi su `/` e
  `/miniapp.html`: non rimuoverli.
- La coda delle categorie si riempie da sola dopo ogni giro d'import
  (leva `RICATEGORIZZA_AUTO`, accesa di serie): nel journal la riga
  «🗂 Ricategorizzazione: N guardati, M proposte in coda», e ai
  moderatori arriva una notifica sola coi gruppi. Non cambia niente in
  vetrina finché un moderatore non approva. Per spegnerla, `False` nel
  config del VPS e riavvio.
- L'import aperto da Nostr si accende SOLO scrivendo
  `IMPORT_NOSTR_APERTO = True` nel config del VPS e riavviando: nel
  codice il default è False apposta (vedi Architettura). Prima di
  accenderlo vale la pena guardare il journal del primo giro — chi
  viene scoperto, quanti annunci entrano, quanti vanno in revisione —
  perché da lì partono account e DM verso persone che non ci
  conoscono. Rimettere False e riavviare è l'interruttore
  d'emergenza; gli annunci già importati restano dove sono.
- Se dall'import aperto nascono copie doppie: la diagnosi si fa in
  SOLA LETTURA prima di toccare (la query che decide è
  `SELECT COUNT(*) FROM annunci WHERE contatto_nostr!='' AND
  nostr_origine_d LIKE 'barattolo-%'`: se è >0 l'anello si è chiuso su
  noi stessi), poi si spegne l'import, poi `ripulisci_anello_nostr.py`
  — prima su una copia del database, poi su quello vero.
- Il Login Widget esige il dominio registrato: BotFather → `/setdomain`
  su @ilbarattolobot → `barattolo.store` (senza, il bottone non compare;
  su localhost non compare mai: si collauda col bottone "cookie web").
- Il tetto del barattolo (`MAX_PREFERITI`) ha il default 10 nel CODICE
  dall'ago 2026, ma una riga esplicita nel config del VPS vince su di
  lui — e finché c'è, il tetto nuovo non entra in vigore. Si guarda
  PRIMA del deploy, in sola lettura:
  `grep -n "MAX_PREFERITI" ~/satmarket/config.py` — nessuna riga = vale
  il default e non c'è niente da fare; una riga con 20 = va cambiata a
  mano (o cancellata) e poi riavviato.
- Deploy: commit+push su main → sul server `cd satmarket && git pull &&
  systemctl restart barattolo`. Config e database NON viaggiano mai.
- Webhook del bot: `TELEGRAM_WEBHOOK_SEGRETO` nel config del server
  (stringa casuale) e al riavvio si registra da solo (riga «🔔 Webhook
  Telegram» nel journal). ATTENZIONE: mai avviare MODALITA_COLLAUDO=False
  col BOT_TOKEN vero fuori dal VPS — ruberebbe il webhook (e quindi i
  /start) alla produzione.
- La verifica npub richiede `websocket-client` (pip) nell'ambiente del
  servizio: se manca, il server parte lo stesso e l'endpoint risponde 503.
- La pubblicazione su Nostr richiede anche `coincurve`: installarla con
  `pip install --only-binary :all: coincurve` (le versioni 20/21 senza
  wheel provano a compilare e falliscono; la 19.0.1 ha wheel ovunque).
  Se manca, o se `NOSTR_NSEC_PIATTAFORMA` resta il segnaposto, la
  funzione Nostr si spegne da sola e il resto vive normalmente.
  Anche il LOGIN Nostr dipende da coincurve (verifica Schnorr): senza,
  i suoi endpoint rispondono 503 e tutto il resto vive.
- Le notifiche via DM Nostr richiedono anche `cryptography` (ChaCha20
  per NIP-44): `pip install cryptography` nell'ambiente del servizio,
  PRIMA del restart. Se manca, il canale DM si spegne da solo (riga
  in console) e le notifiche Telegram vivono come sempre.
- Le foto HEIC degli iPhone (caricate da Android/desktop) richiedono
  `pip install pillow pillow-heif` nell'ambiente del servizio
  (entrambe hanno wheel, niente compilazioni). Se mancano, i JPEG
  vivono come sempre e solo le HEIC non convertibili si saltano.

## Regole ferree

1. MAI committare `config.py`, `*.db`, `foto/`, chiavi, token, npub private.
   Se una chiave viene esposta ovunque (chat, log, commit): va RUOTATA.
2. MAI chiedere o gestire nsec (chiave privata Nostr) degli utenti.
   Decisione permanente. La scala approvata: badge npub auto-dichiarato →
   verifica con nota pubblica (fatta, lug 2026) → login Nostr con firma
   di sfida (fatto, lug 2026: la nsec incollata nel login web firma
   SOLO nella pagina, mai trasmessa né salvata, e la UI la sconsiglia
   a favore di estensione/bunker — è l'estensione approvata della
   scala, NON un'eccezione) → wallet NWC solo-nel-browser (lug 2026:
   la stringa nostr+walletconnect:// è una credenziale di SPESA e
   vive solo in localStorage del dispositivo, mai sul server — un
   suo salvataggio server-side, anche cifrato, farebbe della
   piattaforma il custode dei wallet di tutti: da respingere) →
   DM di notifica NIP-17 (lug 2026: si CIFRA verso la chiave
   PUBBLICA dell'utente e si firma con la chiave della piattaforma,
   nessun segreto altrui coinvolto) → sessione bunker NIP-46
   conservata (lug 2026: URI + chiave del CLIENT in localStorage del
   dispositivo, pari grado del secret NWC — chiede firme al bunker,
   che può negarle o revocare; NON contiene né può derivare la chiave
   dell'utente, mai sul server) →
   mai custodia di segreti altrui, mai firme che richiedano di
   consegnare chiavi al server.
3. Il server pubblico serve SOLO `/`, `/miniapp.html`, `/negozio/*`,
   `/annuncio/*`, `/categoria/{slug}` (i 27 reparti, vocabolario CHIUSO
   su `SLUG_CATEGORIE`), `/sicurezza` (la pagina «Il pagamento
   protetto», link condivisibile con l'ancora facoltativa `#limiti`: si
   manda a chi chiede «mi fido?», cioè a chi Barattolo non ce l'ha
   ancora), `/robots.txt` e `/sitemap.xml` (ago 2026, cantiere «farsi
   trovare»: la prima è una costante PURA che non tocca il database e
   non può sollevare — un 5xx lì sospende la scansione di tutto il sito
   per ore),
   `/foto/*`, `/vendor/nostr.js`, `/vendor/qrcode.js`,
   `/assets/categorie/{slug}.webp` (le 27 illustrazioni di Sfoglia:
   il nome arriva dal client, quindi whitelist — `SLUG_CATEGORIE`,
   calcolata dal catalogo), `/assets/mascotte.jpeg`,
   `/assets/barattolo.jpeg`, `/assets/barattolo-hero.png`,
   `/assets/tappo.jpeg`, le rotte PWA (`/manifest.json`, `/sw.js`,
   `/offline.html`, `/assets/icona-192.png`, `/assets/icona-512.png`,
   `/assets/icona-192-maskable.png`, `/assets/icona-512-maskable.png`,
   `/assets/apple-touch-icon.png`) — tutti file singoli, rotte
   esplicite — e `/api/*`. Non montare mai StaticFiles sull'intera
   directory (config e .git diventerebbero pubblici — falla già
   successa e chiusa). Dall'ago 2026 non ce n'è più NESSUNO: anche
   `/foto/*`, che era l'ultimo montato, è una rotta esplicita con la
   sua whitelist di FORME (`NOME_FOTO`) — vedi la voce sua in
   Architettura. La regola è verificabile e non solo raccomandata:
   una sentinella di `prove.py` fallisce se in server.py ricompare
   `app.mount(` o l'import di StaticFiles.
   E L'ELENCO DELLE ROTTE-PAGINA SI CONTA (ago 2026): la lista in
   `prove_anteprime` era scritta a mano, quindi una rotta pubblica
   NUOVA non la sorvegliava nessuno finché qualcuno non si ricordava
   di aggiungerla. Adesso una prova confronta la sua lunghezza col
   numero di `return _pagina_con_meta(` nel sorgente: chi ne aggiunge
   una senza elencarla trova la CI rossa.
4. Stati ordine: creato | locked | shipped | delivered | confirmed |
   released | dispute | return_pending | return_shipped | refund |
   refunded | annullato. Non inventarne di nuovi senza aggiornare
   frontend (STATES, stepper cassaforte) e notifiche.
5. Solo l'ACQUIRENTE può segnare "consegnato" (anti-frode venditore).
   Il venditore è protetto dall'auto-sblocco a 10 giorni e dal sollecito
   (max 1 ogni 24h).
6. Testare sempre in locale (MODALITA_COLLAUDO=True, tre identità finte:
   Compratore 111, Venditore 222, Admin 999) prima del deploy.
   In produzione MODALITA_COLLAUDO deve restare False.
7. Stile del codice esistente: commenti e nomi in italiano, tono caldo,
   niente refactoring di massa non richiesti, diff piccoli e verificabili.
8. A fine cantiere, PRIMA del commit finale, valuta se il lavoro ha
   cambiato architettura, API, schema del database o regole del progetto:
   se sì, proponi l'aggiornamento di CLAUDE.md come commit separato,
   senza aspettare che Andrea lo chieda. Ritocchi minori (testi,
   tarature, fix) non lo richiedono.
9. Lessico dell'escrow (lug 2026): nei testi per gli utenti si dice
   sempre «deposito di garanzia» — «(escrow)» solo nella prima
   spiegazione lunga di ogni contesto; azione = «🔒 Compra in
   sicurezza» (era «Compra protetto», cambiata lug 2026);
   MAI «assicurato». «Escrow» resta solo dove il pubblico è bitcoiner:
   memo della invoice LNbits e testi verso Nostr (footer NIP-99,
   presenta_release). Il barattolo 🫙 è dei preferiti, mai metafora
   dell'escrow.

## Stato (lug 2026) e prossimi lavori

Lanciando in rodaggio su community italiana, senza limiti di prezzo
attivi (la leva `TETTO_SATS_ANNUNCIO` esiste ma è spenta, vedi sotto).
Fatti (lug 2026): banner sulla demo browser; vetrina pubblica in sola
lettura (annunci veri dal browser, azioni → invito al bot); moderazione
contenuti a tre strati (parole + AI + admin); badge npub auto-dichiarato
nel profilo e sugli annunci; verifica della npub via nota pubblica
(badge 🟣, dal lug 2026 pubblico SOLO da verificata e senza ✓, vedi
Architettura); pubblicazione degli annunci verso
Nostr con la chiave della piattaforma (NIP-99 + NIP-09, vedi
Architettura); pagina negozio del venditore, interna e pubblica
(`/negozio/{username|codice}`, vedi Architettura); login web col
Telegram Login Widget (sessioni cookie, app completa dal browser,
vedi Architettura — ricordarsi `/setdomain` su BotFather); login web
con Nostr (estensione NIP-07, bunker NIP-46, nsec solo-in-pagina;
tg_id negativi e npub_accesso, vedi Architettura — gli utenti Nostr
per ora restano senza notifiche: le vedono nei loro Affari); scudo
anti-XSS `esc()` su tutti i template; Compra subito col wallet NWC
(NIP-47 lato client, secret solo in localStorage, vedi Architettura
— il percorso felice va collaudato con un wallet vero a budget
minuscolo: in locale è verificato il ripiego, non il pagamento);
doppia cittadinanza completa (righe identità nel cassetto
«🆔 Identità» del Profilo,
badge verificato promuovibile a chiave d'accesso, webhook /start del
bot e fusione atomica Nostr→Telegram, vedi Architettura — in
produzione va provata una fusione vera con un account di test);
notifiche via DM Nostr NIP-17 con scelta del canale (i nativi Nostr
finalmente ricevono gli avvisi, cassetto «🔔 Avvisi» nel Profilo, vedi
Architettura — la cifratura è verificata contro nostr-tools, ma in
produzione va provato un DM vero verso la propria npub su 0xchat o
Amethyst; sul VPS serve `pip install cryptography`); modifica annuncio
del venditore (form di Vendi riusato, moderazione completa,
ripubblicazione Nostr, vedi Architettura); foto HEIC/HEIF e WebP
accettate e convertite in JPEG (client via canvas quando può, server
con Pillow altrimenti — sul VPS serve `pip install pillow
pillow-heif`); scheda Profilo 👤 (tutto ciò che
riguarda l'utente trasloca lì da Vendi, che torna solo form di
pubblicazione; Lightning address impostabile anche da lì; canale
avvisi sempre in chiaro; dal lug 2026 riorganizzata a cassetti
richiudibili stile Vinted, testata sempre visibile e npub+verifica
riuniti nel cassetto identità; vedi Architettura); feedback e stelle
(voto 1-5 + commento a affare concluso, rating per ricalcolo,
ultimi feedback anonimi nel negozio, rimozione admin, vedi
Architettura — parte 1 della gamification); distintivi 🏅 (parte 2:
11 badge auto-assegnati per ricalcolo dai dati veri, cassetto con
griglia e conteggio «N di M» nel Profilo, chip di fiducia nel negozio
pubblico, retroattivi a ogni
avvio, vedi Architettura); badge 🟣 pubblico semplificato (solo da
npub verificata, senza ✓; il non verificato lo vede solo il
proprietario col suo invito a verificare); export CSV contabile
degli affari conclusi (bottone nel Profilo, controvalore EUR
valorizzato alla chiusura da ora in poi, vedi Architettura);
doppia valuta (lug 2026: listino in sats o in EUR a scelta del
venditore, toggle ₿/€ per chi guarda, pagamento sempre in sats col
cambio bloccato dalla vita della invoice, e la leva del tetto per
annuncio con tolleranza +20% sul drift, vedi
Architettura — collaudato in locale da cima a fondo; la riga EUR
nella ricerca AI va provata in produzione, dove la chiave Anthropic
è vera; la leva del tetto `TETTO_SATS_ANNUNCIO` esiste nel codice
ma è SPENTA di default: nessun annuncio viene limitato finché non
la si accende dal config); onboarding contestuale (lug 2026:
suggerimenti discreti al momento del bisogno — wallet NWC nel
paySheet, Lightning address e verifica npub dopo la pubblicazione —
più la checklist «Completa il profilo (N di M)» nel Profilo; «Non
ora» memorizzato in localStorage, mai in demo/vetrina, vedi
Architettura); redesign «mercatino di paese» (lug 2026: palette crema/
arancio/verde sigillo, Baloo 2+Nunito, card «Etichetta», bottoni con
ombra piena, recinto escrow tratteggiato, festa dei sats, mascotte e
barattolo con route /assets, favicon e hero desktop, vedi
Architettura — collaudato in locale su tutte le viste e i tre
viewport; da rivedere dal vivo dentro Telegram dopo il deploy);
dark mode «mercatino di sera» (lug 2026: token scuri su fondo bruno
caldo, toggle Auto/Chiaro/Scuro nel cassetto «🌗 Aspetto» del Profilo,
tg.colorScheme dentro Telegram, vedi Architettura — collaudata in
locale con contrasti AA misurati; da provare dal vivo dentro Telegram
col tema scuro e il cambio tema a app aperta); tre completamenti del
redesign (lug 2026: etichetta prezzo sempre di carta chiara anche in
dark, medagliette di fiducia del venditore nella scheda annuncio via
`venditore_distintivi`, pillola-contatore «🏅 N/M» accanto al lockup
per gli autenticati, vedi Architettura); cinque ritocchi dal feedback
dei tester (lug 2026: via la pillola-contatore, al suo posto il
tasto-tappo del Profilo in testata e nav a 3 voci; searchbar che
cerca con Invio senza bottone; ✕ «ho capito» sul banner web; il
cassetto «🆔 Identità» perde il «e Nostr» — vedi Architettura,
redesign — collaudati in locale su mobile e desktop, chiaro e scuro,
web/vetrina/demo); categorie nuove a 9 voci con pillole ordinate per
contenuto (lug 2026: catalogo `CATEGORIE`, migrazione idempotente,
vuote nascoste, vedi Architettura — collaudate in locale con
migrazione sui dati veri; la ricerca AI col set nuovo va provata in
produzione, dove la chiave Anthropic è vera); tenuta al volume
(lug 2026: paginazione keyset su vetrina/negozio/miei con scroll
infinito, indici su annunci, miniature `_min` per le card con
backfill all'avvio, cache di un giorno su /foto, shortlist a 300
della ricerca AI, ricerca semplice anonima lato server e GET del
singolo annuncio per i link condivisi, vedi Architettura — misurato
in locale con 814 annunci seminati: pagina 25× più leggera di prima
[17KB vs 436KB], query tutte sugli indici, card da ~8-25KB invece
del JPEG pieno; da rivedere dal vivo dentro Telegram dopo il deploy,
e la shortlist AI va provata in produzione con la chiave vera);
modifica firmata degli annunci importati (lug 2026: il doppio
cittadino aggiorna i suoi eventi NIP-99 da Barattolo — due fasi con
moderazione prima della firma, firma nel browser col firmatario del
login, pubblicazione sui relay dal client e copia locale allineata
subito; l'import impara il match per tag `d` e le colonne origine,
vedi Architettura — collaudato in locale da cima a fondo, casi
negativi compresi; in produzione va provata una modifica vera con la
chiave del venditore consenziente, verificando su njump che l'evento
sostituisca il vecchio anche sul suo relay personale); deduplica dei
doppioni su Nostr (lug 2026: era nel backlog, sbloccata dal match a
impronta stretta — cassetto «🔁 Doppioni su Nostr» nel Profilo con le
coppie sospette, ritiro NIP-09 solo della copia della piattaforma con
conferma esplicita, «non è un doppione» persistente in
`doppioni_ignorati`, messaggio mirato del bot dopo la fusione, vedi
Architettura — collaudata in locale da cima a fondo, casi negativi e
soglie comprese; in produzione va provato un ritiro vero verificando
su njump che sparisca SOLO l'evento della piattaforma e che
l'originale del venditore resti); import in blocco da CSV (lug 2026:
cassetto nel Profilo per i commercianti — 70 negozi in arrivo al
lancio — con modello scaricabile, foto da URL o ZIP, moderazione
COMPLETA con AI a lotti, anteprima e conferma esplicita, job
asincrono con avanzamento e report, Nostr a lotti lenti con opt-out,
vedi Architettura — collaudato in locale da cima a fondo, TestClient
e browser; in produzione va provato un import vero con la chiave AI
e un catalogo reale, e il download del modello da dentro Telegram);
post automatici dei fatti (lug 2026: nota Nostr kind-1 + post nel
canale Telegram per ogni nuovo annuncio, anti-spam a drenatore con
aggregato per le raffiche, ciclo di vita ✅ Venduto/cancellazione,
vedi Architettura — collaudato in locale con 13 verifiche simulate;
in produzione serve creare il canale, mettere il bot come admin e
`TELEGRAM_CANALE_ID` nel config del VPS, poi verificare un post vero
su canale e relay); avvisi di ricerca personalizzati (lug 2026:
criteri salvati nel cassetto «🔎» del Profilo — categorie, comune con
raggio km sul dataset comuni committato, prezzo max, parole chiave —
matching alla pubblicazione col gemello della coda promo,
anti-molestia a tre strati (dedup persistente, aggregato per le
raffiche, tetto giornaliero) e CTA «Avvisami se arriva» dopo la
ricerca a vuoto, vedi Architettura — collaudato in locale da cima a
fondo: matching positivo e negativi per ogni criterio, distanze
Milano/Monza/Pavia/Napoli, dedup sulla modifica, aggregato da
raffica, tetto col messaggio onesto, form/pausa/elimina/precompila
nel browser; in produzione va provato un avviso vero con notifica
Telegram reale); gestione completa della npub nel Profilo (lug 2026:
bottone «Rimuovi la npub dal profilo» con conferma, guardia per il
nativo Nostr che ne sarebbe chiuso fuori, canale avvisi riportato
all'automatico quando la destinazione Nostr sparisce, sottotesti che
distinguono le due leve Disabilita/Rimuovi, vedi Architettura, badge
Nostr — collaudato in locale con TestClient [31 verifiche] e nel
browser su tutti gli stati della riga Nostr); dettaglio annuncio
immersivo e preferiti col barattolino (lug 2026: foto a filo con
ritorno flottante, lightbox a tutto schermo con pinch/rotella/swipe
in vanilla JS, cassetto «🫙 Nel tuo barattolo» primo nel Profilo con
gli stati onesti dei non più disponibili, vedi Architettura —
collaudato in locale su mobile e desktop, chiaro e scuro, con
venduto nel mezzo e DEMO/vetrina senza barattolino; il pinch va
riprovato dal vivo su un telefono vero dentro Telegram); PWA
installabile — Fase 1 (lug 2026: manifest con le icone del barattolo
su tessera arancio, service worker prudente con pagina offline e
mascotte, banner «installa» discreto solo su web mobile, dentro
Telegram tutto identico per costruzione, vedi Architettura —
collaudato in locale: dispensa completa senza /api, offline vero a
server spento, guardie del banner esercitate una a una, demo file://
pulita; in produzione vanno provate l'installazione vera su Android
e iPhone e la verifica del widget Telegram in standalone, il cui
esito decide l'eventuale piano di riserva redirect); APK distribuito
sui due canali pubblici (lug 2026, Fase 3: release v1.3 su
github.com/kreamistudio-crypto/barattolo-releases per Obtainium e
download diretto, e su Zapstore con chiave Nostr dedicata fredda e
certificato legato via NIP-C1 — eventi verificati sul relay, hash e
certificato coincidenti; vedi «Distribuzione dell'APK» — restano da
fare: screenshot nella scheda Zapstore, profilo kind-0 dell'identità
release, e la prova d'installazione dallo store sul telefono); avatar
dal social di provenienza (lug 2026, richiesta di Alan: la foto
profilo Telegram o la picture del kind-0 Nostr come francobollo 128px
servito da foto/, catena Telegram→Nostr→iniziale per i doppi
cittadini, selettore «La tua foto» nel cassetto Identità —
Telegram / Nostr / Nessuna, voci solo per le sorgenti vere, default
la catena automatica — vedi Architettura — collaudato in locale: 12
verifiche server comprese la gamba Nostr sui relay veri, rendering e
ripieghi nel browser, selettore avanti e indietro con la validazione
delle sorgenti; in produzione va vista una foto Telegram vera, che
in collaudo il bot simulato non può dare); cartello «fase di test»
all'apertura (lug 2026: modale col velo sfocato, testo e link del
canale scritti nel config, una volta al giorno per dispositivo,
precedenza sul tour di benvenuto, vedi Architettura — collaudato in
locale in tutti gli stati [acceso, spento, link vuoto o storto,
server muto, stesso giorno, giorno nuovo], chiaro e scuro, mobile e
desktop, demo e vetrina; a rodaggio finito si spegne con
`BANNER_TEST = False` nel config del VPS e un riavvio); spedizione e
protezione acquisti modello Vinted (lug 2026: modalità di consegna,
costo spedizione nella valuta del listino e taglia del pacco
sull'annuncio, conto scomposto a carico del compratore col totale in
cassaforte, ritiro in zona senza stati nuovi, filtro «solo con
spedizione», leva `PROTEZIONE_PERCENTO` SPENTA di serie, vedi
Architettura — collaudato in locale: 72 verifiche TestClient sui
quattro strati compreso il giro completo a tre identità con
spedizione EUR, ritiro con auto-sblocco a 72h/10gg e annuncio
storico, più il giro visivo in Chrome headless su chiaro e scuro; in
produzione va rivisto dal vivo dentro Telegram, e quando la
protezione si accenderà dal config vanno decisi i testi con la
cifra); offerte e contrattazione sul prezzo (lug 2026, modello
Vinted: foglio con chip −10%/−20% e stima live, una sola
controproposta, accettazione = 24h per pagare col flusso di sempre
alla cifra pattuita, l'annuncio non si blocca mai e vince chi paga,
sezione «💰 Offerte» in testa alla scheda Ordini col pallino sul nav,
leve config 50%/48h/24h/3, vedi Architettura — collaudato in locale
con 51 verifiche TestClient sui quattro strati: giro pieno sats con
controproposta, giro EUR con virgola e cambio_ordine, anti-abuso
completo, decadenza per vendita, sweep delle scadenze, reaper con
ripagamento, modifica prezzo, regressione dell'acquisto normale; in
produzione va provato un giro vero dentro Telegram con le notifiche
reali); offerta lampo ai barattoli (lug 2026, modello Vinted «sconto
ai follower»: avviso anonimo «ha fatto colpo» al venditore quando
qualcuno salva, sconto pubblico a percentuale e a tempo lanciato dal
foglio del dettaglio, avviso mirato a chi ha l'annuncio nel barattolo,
badge col countdown e prezzo barrato in vetrina e dettaglio, filtro e
ordinamento «⚡ In offerta», minimo con l'accordo individuale in
compra(), scadenza che ripristina tutto da sola anche a pagina
aperta, leve nel config, vedi Architettura — collaudato in locale da
cima a fondo: valvola e cooldown in console, guardie del lancio una a
una, acquisto scontato sats ed EUR, min nei due versi, superficie
pubblica con cursore, e il giro visivo nel browser vero via CDP da
venditore e in demo; in produzione va provato un giro vero dentro
Telegram con le notifiche reali); lampo e offerte anche sugli annunci
importati da Nostr (lug 2026, decisione di prodotto: il catalogo e' uno
solo, la differenza tra nato-qui e nato-su-Nostr e' SOLO chi firma
l'evento NIP-99 — via le guardie contatto_nostr da fai_offerta,
lancia_lampo e _drena_colpo e i due l.nostr dal dettaglio; porta
«🟣 …o entra con Nostr» nel foglio invito della vetrina per il
percorso DM → link → login npub → azione; la guardia di modifica_annuncio
resta: il contenuto degli importati si cambia sui relay, la lampo e'
un'altra strada che non lo tocca; vedi Architettura, offerte e lampo —
collaudato in locale con 16 verifiche TestClient su DB usa-e-getta:
giro offerta completo sull'importato con cifra pattuita nell'ordine,
lampo lanciata/comprata scontata/annullata, «ha fatto colpo» arrivato
al venditore dell'importato, regressioni su nativo e guardie
sopravvissute; in produzione va provato il giro vero: DM NIP-17 con
link a un venditore solo-Nostr, login npub dal foglio invito e
risposta all'offerta); consegna digitale 💾 (lug 2026: quarta modalità
per buoni regalo, codici e licenze — il contenuto passa dentro
Barattolo con consegna tracciata e rivelazione-ricevuta, cifratura a
riposo fail-open, finestre corte 24/48h, regola asimmetrica dichiarata
e leve anti-frode spente di serie, servizi esclusi dalla moderazione
col messaggio gentile e prodotti digitali leciti in whitelist, vedi
Architettura — collaudato in locale con 58 verifiche TestClient su DB
usa-e-getta: giro completo consegna→rivela→sblocco 24h, silenzio 48h,
regressione dei rami fisici, cifratura nei due formati, disputa con
nota admin, leve accese e spente, import CSV e NIP-99; in produzione
va provato un giro vero dentro Telegram, la voce «buono
regalo/servizio» della moderazione AI con la chiave vera, e sul VPS va
scelta CHIAVE_CONTENUTI_DIGITALI nel config — senza, i codici restano
in chiaro nel DB, dichiarato; dal lug 2026 anche in COMBO con una
modalità fisica via `anche_digitale`: il compratore sceglie la strada
con le pillole e le tutele seguono la sua scelta, vedi Architettura —
collaudata con 32 verifiche TestClient: tutele digitali sul ramo
digitale e fisiche sul ramo fisico dello STESSO annuncio, default
fisico per i client vecchi, guardie, NIP-99 e CSV col «+»); regione
derivata e cercabile (lug 2026: nessun campo nuovo nel form — la
regione si ricava dalla sigla della provincia con una mappa fissa,
colonna sua scritta accanto alle coordinate e backfill all'avvio, voce
«Regione» nel pannello Filtri con le sole regioni che hanno annunci e
il loro numero, vedi Architettura — collaudata in locale con 42
verifiche TestClient su DB usa-e-getta [mappa, pubblicazione, modifica,
import CSV, filtro combinato e paginato, risposta legacy, backfill
idempotente] e il giro nel browser vero su chiaro e scuro, coi dati
veri e in demo; in produzione basta il riavvio: la migrazione e il
backfill girano da soli); barra d'acquisto al posto della tab bar nel
dettaglio (lug 2026, modello Vinted: aperto un annuncio comprabile la
tab bar lascia il posto a «Compra in sicurezza» col totale e
«Offerta», stessa altezza e stessa carta — niente salto di layout —
con i gemelli in pagina spenti su mobile e il recinto escrow lasciato
alle spiegazioni; guardie e cifre riusate tal quali, da desktop non
esiste, vedi Architettura — collaudata in locale a 360/375/1280px e nei
due temi: altezza allineata, lampo −20% e cambio consegna sulla cifra,
invito in vetrina, annuncio proprio con la tab bar intatta, fogli e
lightbox che le passano sopra; in produzione va rivista dal vivo dentro
Telegram, dove contano la gesture bar del telefono e il tema del
client); il varco della barra (lug 2026, subito dopo: la barra si
raggiunge senza scorrere e comprava con la consegna decisa in silenzio
— ora la barra dice sempre la strada quando ce n'è più d'una, e il
primo tocco a scelta implicita apre il foglio «Come vuoi riceverlo?»
coi totali per strada, che scegliendo chiude e procede in un gesto
solo, vedi Architettura — collaudato in locale col giro vero a 360px:
foglio, scelta, paySheet coerente, secondo tocco diretto, Escape senza
ordine, combo digitale, vetrina e regressione dei picker); quantità in
stock per annuncio (lug 2026: campo quantità nel form Vendi, stepper e
conto × N all'acquisto con spedizione una volta sola, esaurito = stato
venduto con «Rimetti in vendita» dai tuoi annunci, prenotazione
derivata dagli ordini 'creato' che chiude anche il buco storico del
doppio acquisto — deployata per prima, da sola —, offerte a prezzo
unitario, riga «disponibili» nel NIP-99 e colonna CSV, vedi
Architettura — collaudata in locale con 60 verifiche TestClient su
quattro script [prenotazione con rivale nell'await, parziale/
esaurimento/decadenze, rimborso e ricarica, superficie e import] più
il giro nel browser vero a 375px con invoice LNbits reale; è il
mattone del futuro cantiere «set»); il set «Riempi il barattolo»
(lug 2026: più annunci diversi dello stesso venditore in un ordine
solo — sezione «Altri oggetti di questo venditore» nel dettaglio,
foglio di composizione con spunte e stepper, UNA spedizione al MAX
dei costi dichiarati con la stima della taglia del pacco solo
informativa, un escrow e una conferma con disputa/rimborso
tutto-o-niente dichiarati, modello testata+ordine_righe coi mono
intonsi byte per byte, vedi Architettura — collaudato in locale con
97 verifiche TestClient su quattro script [fondamenta e guardie,
compra a righe con EUR/offerte/lampo e 409 col nome del pezzo,
ciclo di vita completo con rimborso che riattiva tutto, tabella dei
casi della stima taglia] più il giro nel browser vero con invoice
LNbits reale, vista compratore e venditore e il rivale che soffia
il pezzo a metà composizione; in produzione va provato un set vero
dentro Telegram con le notifiche reali; gli SCONTI SET alla Vinted
sono il cantierino successivo, deciso: la preparazione è
l'invariante articolo = Σ unitario×qta, lo sconto sarà una voce di
testata); card più stretta e dettaglio spogliato (lug 2026: in card
le icone si raggruppano a destra e la zona si mostra solo se è un
LUOGO vero; nel dettaglio restano luogo, consegna, condizione,
disponibilità e Nostr, mentre escono categoria, taglia del pacco,
«protezione acquisti inclusa» e il costo dalla pillola della
spedizione, che vive già nel foglio della consegna e nel conto
scomposto; collaudato a 360/375/390 e 1280px, chiaro e scuro);
il luogo si fa pulito, dentro e fuori (lug 2026, subito dopo: il
pallino Nostr esce dalle card — riguarda il venditore, non
l'oggetto, e in griglia lo spazio è poco; si mostra il solo COMUNE
estratto dal dizionario invece del testo intero — in card, e dal
giorno dopo anche nella pillola del dettaglio e nelle righe-elenco
del Profilo: una regola sola ovunque, vedi in Architettura perché
tenere il testo intero nel dettaglio non era tenibile; e in INGRESSO
la zona, pur restando facoltativa senza
ritiro, dev'essere un comune vero — l'avviso morbido del form e
dell'import CSV è diventato bloccante, con un messaggio unico e il
«forse Pavia (PV)?»: chi spedisce e basta lascia il campo vuoto,
niente più «spedisco in tutta Italia» nel campo Zona. Superficie
API: `zona_comune` in CAMPI_VETRINA, che ASSORBE il
`zona_riconosciuta` del giorno prima — il nome è anche il flag —
calcolato nel collo di bottiglia `arricchisci_righe_vetrina`; zero
colonne nuove, in produzione basta il riavvio. Conseguenza
dichiarata: gli annunci storici con la zona storta si mettono in
regola alla prima modifica, come per la condizione. Vedi
Architettura per il vincolo del cuore unico `_chiave_comune`, che
serve al prossimo cantiere. Collaudato con 16 casi mirati più
l'invariante su tutto il dataset [7.904 comuni × 3 forme], 9 casi
TestClient sulla guardia, l'anteprima CSV, i 6 stati della riga di
hint e il gate end-to-end contando le POST); riordino del dettaglio
annuncio stile Subito.it (lug 2026: data relativa sotto la foto con la
colonna `annunci.modificato` e la leva GIORNI_DATA_ANNUNCIO, titolo
con la condizione accanto, luogo come testo nudo, badge azzurro
«Spedizione disponibile» accanto al prezzo con le altre strade
discrete, titolino «Descrizione», e il 🟣 dentro il riquadro
venditore, vedi Architettura — collaudato in locale via CDP a
360/375/390 e 1280px nei due temi e con reduced-motion, sui casi
senza luogo / senza spedizione / solo digitale / lampo attiva /
annuncio storico; in produzione basta il riavvio, la migrazione gira
da sola; più le quattro rifiniture del giorno dopo: badge spedizione
sulla stessa riga del prezzo, 🟣 solo icona in fila coi badge, via i
ponti di contatto dal riquadro venditore; e le correzioni del giorno
dopo ancora: «Acquista» arancio ₿ NUDO senza prezzo — solo lui e
centrato dentro il recinto escrow, «Fai un'offerta» fuori sotto — e
nella barra fissa i due tasti gemelli piatti (offerta a sinistra)
col richiamo tratteggiato verde e il lucchettino, via le
pillole di scelta consegna dal dettaglio (la strada si sceglie nel
foglio del varco, che diventerà la pagina dedicata del prossimo
cantiere), forme rettangolari col raggio del riquadro su TUTTI i
bottoni del dettaglio — riverificate a 360/375/390 nei due temi,
col varco esercitato dal vivo); il recinto parla poco e la spedizione
si vede (lug 2026: «Acquista» un gradino più grande e i due tasti
della barra finalmente gemelli — il tratteggio diventa un outline che
non occupa layout e le basi flex vanno al 50%, la stessa lezione dei
bottoni del pannello Filtri; la spedizione a due gradi dello stesso
azzurro nel solo chip «Spedizione gratuita» sopra il prezzo — le altre
strade restano pillole normali, perché il colore veste solo ciò che è
un vantaggio — con «🚚 gratis» scritto in vetrina; il gemello col costo sotto
Acquista è nato e morto nello stesso cantiere: il recinto è il posto
della fiducia, non del listino; il recinto ridotto a una riga,
via la riga sulla invoice, e tutto il resto nella pagina nuova «Il
pagamento protetto» raggiungibile da tre porte; i tempi dell'escrow
raccolti nella costante `TEMPI` con la tabella delle leve accanto —
erano sparsi in dodici stringhe; più «Riempi il pacco» col nuovo
accento cartone e lo «Scopri di più» in inchiostro. Vedi Architettura
— collaudato in locale via CDP a 360/375/390 e 1280px nei due temi,
sui casi spedizione a pagamento / gratuita / ritiro / digitale /
storico / lampo / multi-pezzo, in vetrina anonima, in DEMO e col
wallet NWC collegato, con le tre porte e i loro ritorni, il tour
ancora intero e zero errori JS; contrasti misurati AA su tutti i
token nuovi. In produzione basta il deploy: nessuna colonna, nessuna
leva nuova. RESTA DA DECIDERE A RODAGGIO: i testi della pagina sono
scritti oggi con la commissione sospesa e la protezione spenta —
quando si accenderanno vanno riletti, in particolare «Se qualcosa va
storto» e «Dove stanno i sats»); il gesto indietro torna indietro
(lug 2026: dentro Telegram, nella PWA e nel browser il tasto/gesto
indietro non chiude più l'app — prima chiude i fogli, poi smonta le
viste, e si esce solo dalla radice; freccia ← e tab bar restano tutte
e ora dicono la stessa cosa del gesto, che è come sono spariti
`sicurezzaRitorno` e l'euristica di `tornaDalNegozio`. Vedi
Architettura per le tre scelte da non rovesciare: URL mai toccato,
ascoltatore dichiarativo, pila derivata dal DOM con un
MutationObserver — che è come i 18 siti dei fogli, `closeSheet` e le
tre chiusure mirate sono rimasti intonsi — collaudato in locale nel
browser vero a 375px: catena viste con salti multipli e AVANTI del
browser, dieci giri di tab senza far crescere la cronologia, deep link
che atterra sulla vetrina, lightbox, tour, cartello e foglio-invito,
nessun gradino morto dopo ✕/velo/Escape, e il caso a cui teneva
Andrea — picker aperto SOPRA il paySheet con invoice LNbits vera: il
primo indietro chiude solo il picker e il pollTimer resta VIVO, il
secondo chiude il foglio e lo ferma. In produzione basta il deploy:
nessuna rotta, nessuna colonna. Da provare dal vivo dentro Telegram,
dove contano la freccia di sistema e il gesto del client); Barattolo
diventa una vetrina di Nostr (lug 2026, cantiere di Alan — PR #5 —
merged con sette correzioni decise da Andrea: si importa chiunque
pubblichi NIP-99 in italiano, con scoperta ogni 6h, firme verificate
davvero, moderazione completa prima che un evento diventi una riga,
metadati di commercio nei tag, catalogo a 25 categorie e la rete di
prove in CI. Le correzioni, che sono la parte da ricordare:
l'interruttore nasce SPENTO perché il salto non sia l'effetto di un
deploy; le categorie SI AGGIUNGONO e non si rinominano, quindi zero
migrazioni e nessun annuncio spostato; la moderazione si paga una
volta sola e si rifà solo quando cambia il TESTO; dubbi E bocciature
dell'AI vanno in una coda visibile agli admin invece di sparire, e la
decisione è REVERSIBILE («↩︎ Ripensaci»); lo stock dai relay si lima
al tetto e la consegna digitale dai relay non passa; i suggerimenti su
cosa manca a un annuncio sono OPT-IN e spenti di serie — il benvenuto
resta l'unico messaggio che mandiamo senza permesso. Più i tre
ritocchi del giorno dopo: quattro icone di categoria che dicevano un
prodotto invece del reparto, il tetto della quantità a 999999 (con
tutte le quantità che passano da `fmt()`), e i due testi definitivi.
Vedi Architettura —
collaudato in locale con 48 prove pure in `prove.py` [che ora coprono
anche il modello CSV, il testo condiviso degli eventi e le due
guardie] più 26 verifiche su DB usa-e-getta [`_da_giudicare` nei sei
casi, il marchio che fa nascere in revisione, il registro legato
all'annuncio e la sua idempotenza, il giro completo
rifiuta→riapri→pubblica→riapri, la guardia degli affari in corso, la
coda «decisi», e i suggerimenti nei loro cinque casi — spenti che non
scrivono e NON timbrano, accesi che scrivono una volta sola e mai nel
giro dell'apparizione], più il foglio delle 25 categorie e
l'interruttore nei due stati guardati nel browser. IN PRODUZIONE: il
deploy da solo non cambia NIENTE — girano le migrazioni delle due
colonne (`completamento_avvisato`, `suggerimenti_annunci`) e basta;
l'import aperto si accende scrivendo la riga nel config del VPS, e
quello è il momento da guardare col journal aperto. Se il config del
VPS ha una riga `MAX_QUANTITA_ANNUNCIO` esplicita, va alzata anche lì.
RESTA DA FARE: decidere se anche lo scarto per PAROLE VIETATE debba
finire in coda come quelli dell'AI — oggi non ci va, resta uno scarto
secco visibile solo nel registro);
il primo giro vero, e l'anello che si chiudeva (lug 2026: acceso
l'import in produzione sono comparsi 40 annunci doppi, articoli
intestati al venditore sbagliato e «Altri oggetti di questo venditore»
pieno di roba d'altri — TRE sintomi di UN bug solo, la scoperta che
adottava la chiave della piattaforma come se fosse un venditore
qualsiasi. Diagnosi fatta sui dati veri con query in sola lettura
PRIMA di toccare qualunque cosa, import spento subito, e zero denaro
coinvolto: nessun ordine aperto su annunci importati. Cura in due
tempi — il TAPPO (`chiave_di_casa` + il confronto dell'autore
nell'import, che è il buco vero: non ci si fida del filtro `authors`
del relay) e la PULIZIA (`ripulisci_anello_nostr.py`), più la cintura
sull'origine nella guardia del set. Vedi Architettura, «L'ANELLO CHE
SI CHIUDEVA» — collaudato con 57 prove pure [9 nuove, compresa la
sentinella sul confronto dell'autore] e 22 verifiche su DB
usa-e-getta che RICOSTRUISCONO il bug daccapo: il negozio del fantasma
con roba di due persone, il relay che risponde con eventi di un terzo,
l'anteprima che non scrive, la copia con l'ordine aperto lasciata
stare, il secondo giro che finisce il lavoro, il rilancio a vuoto.
LEZIONE da non perdere: un cantiere che legge da una fonte pubblica
deve chiedersi per prima cosa se in quella fonte c'è anche la propria
voce).
ritocchi ai filtri e al recinto (lug 2026: le due spunte di consegna
che mancavano — «🤝 Ritiro in zona» e «💾 Codice online», col digitale
che guarda il SET delle strade per prendere anche la combo — e le
etichette senza «Solo con…», che dentro un pannello che si chiama
Filtri il «solo» lo dice il posto; e lo «Scopri di più» che passa in
coda alla frase del recinto, nel verde del testo di fiducia, legato
all'ultima parola perché sotto i 390px scendano insieme. Collaudato
coi dati veri: conteggi dei filtri incrociati con le query sul
database, composizione con condizione e regione, paginazione, risposta
legacy senza `limit` ancora un array, e il ritorno a capo del link
misurato a 360/375/390/1280 nei due temi coi contrasti AA. In
produzione basta il deploy).
E in mezzo, «📍 Vicino a me»: nato, deployato e TOLTO nel giro di due
giorni perché si sovrapponeva al filtro per regione — la storia, il
motivo e cosa è rimasto in piedi stanno in Architettura, alla voce
omonima. Con lui se n'è andata la precompilazione della Zona in Vendi:
il campo nasce vuoto e lo scrive l'utente. Resta INERTE la colonna
`utenti.comune`, che nessuno scrive e nessuno legge.
Due migliorie prima di aprire la pagina «Sfoglia» (lug 2026, decisioni
di Andrea): LA RICATEGORIZZAZIONE — l'AI propone leggendo titolo e
descrizione, i moderatori confermano dalla coda «🗂 Categorie da
sistemare» raggruppata per spostamento, e nessun annuncio cambia
casella senza che un umano l'abbia visto (~0,20 $ per 800 annunci);
più il fix all'invito opt-in, che la voce «la categoria giusta» non la
faceva partire mai. E LA CONDIZIONE CHE NON SI CHIEDE dove non vuol
dire niente: «Alimenti e bevande» e i codici online consegnati dentro
Barattolo — il campo sparisce dal form, la pillola dal dettaglio, la
riga dal pannello Filtri, e gli alimentari di ieri non si migrano ma
smettono di mostrarla. Vedi Architettura per i due giudici unici
(`senza_condizione`, `_sposta_categoria`) — collaudate in locale con
20 prove pure nuove in `prove.py` (parità dei due elenchi
server↔client compresa) e 26 verifiche TestClient su DB usa-e-getta
(guardia nei quattro casi, alimentare storico fuori dal filtro ma in
vetrina, modifica che torna a chiedere la condizione cambiando
categoria, coda con spostamento parziale, proposta stantia, 409 e
scarto), più il giro nel browser vero a 375px: campo che compare e
sparisce sui quattro passaggi, filtro che dorme e si risveglia, coda
admin con «mostra tutti» che non perde le spunte tolte a mano. In
produzione basta il deploy — la tabella `categoria_proposta` la crea
init_db —, e la coda resta vuota finché non si lancia
`python ricategorizza.py --scrivi` sul VPS.
La pagina «Sfoglia» (lug 2026): le 26 categorie diventano una vetrina —
quarta radice della nav, griglia a due colonne di piastrelle
illustrate, dieci in una schermata come nel riferimento. Il tondo del
Vendi resta al centro esatto grazie al quinto posto vuoto, e l'indietro
da una categoria torna a Sfoglia (l'unica eccezione al patto delle
radici, con la sua bandierina). Vedi Architettura — collaudata in
locale a 360/375/390 e 1280px nei due temi: nav misurata (Vendi a
180.0 su 180.0, altezza invariata, nessuna etichetta troncata), catena
del gesto indietro compresi i cinque cambi di tab che non lasciano
gradini, categoria vuota che atterra sul suo «Avvisami se arriva», la
rotta che serve solo le 26 vere (404 su nomi inventati e su
`../../config.py`), il ripiego a emoji, e 77 prove verdi con le tre
nuove sulle illustrazioni. Due problemi veri trovati e chiusi
strada facendo: i nomi di una parola sola che sbordavano dove il
browser non ha il dizionario di sillabazione, e la guardia di
`renderChips` che rimangiava la categoria scelta quando era vuota.
In produzione basta il deploy: nessuna colonna, nessuna leva —
solo i 26 file in `assets/categorie/`, che viaggiano col commit.
L'avvertimento che stava qui — cache di un giorno su nomi NON
versionati, «una rifatta resta vecchia nei browser per 24 ore» — si è
incassato per davvero (ago 2026): la PWA di Andrea mostrava DUE
generazioni vecchie insieme (il biglietto della 27ª con l'alone
«attaccato al titolo», Animali senza il pareggio) mentre la Mini App,
che ha la SUA cache WebView, era giusta — e sembrava in tutto un
render diverso nei due contesti. Ed era STRUTTURALE, non un caso: ogni
illustrazione nuova sposta la mediana dell'inchiostro e il pareggio
riscrive delle sorelle, quindi i file cambiano a ogni categoria
aggiunta. La cura, per tutte e 27: la rotta risponde
`Cache-Control: public, no-cache` — il browser tiene la copia ma la
RICONTROLLA a ogni uso, e l'ETag che FileResponse già manda fa 304
finché il file non cambia — più il timbro una-tantum `?b=2` sugli URL
del client (renderSfoglia e icoCategoria), che ha ripulito le cache
scritte col regime vecchio e NON va più toccato. Il «nome col timbro»
delle foto resta la strada se un giorno servisse rimettere il max-age.
Tre lavori sulla nav, in un cantiere solo (lug 2026): la nav non mente
più entrando da Sfoglia — si accendeva «Esplora» su una vetrina
filtrata, e chi guardava credeva fosse il mercatino intero e lo
trovava vuoto (rimedio: `ramoVetrina`, una variabile e non una vetrina
duplicata, letta dal giudice unico `voceNav()` e spenta da
`setCat('Tutto')`, cioè dal filtro che la giustifica); gli Ordini
passano all'ESTREMA destra col posto vuoto in mezzo, che è solo uno
scambio nel markup perché i cinque slot sono tutti `flex:1`; e le tre
emoji della barra diventano SVG di casa — lente, piastrelle, pacco di
tre quarti — che si ACCENDONO invece di accendere una pillola sotto di
sé. Più le icone della consegna in Vendi, che crescono a 20px e in cui
la spedizione passa dal 📦 al 🚚, cioè al disegno che la spedizione ha
in tutto il resto dell'app. Vedi Architettura, alla voce Sfoglia, per
la taratura delle icone (26px come tetto, viewBox ritagliato a
`2 2 20 20`) e soprattutto per le TRE STRADE SCARTATE col loro perché
— pacco piatto, barattolo del logo, illustrazioni a 24px — che è la
parte che serve fra sei mesi. Collaudato nel browser vero a 360px nei
due temi: nav 61,2px invariata e Vendi a 180,0 su 180,0 dopo ogni
ritocco, giro completo del ramo Sfoglia (piastrella → dettaglio →
negozio → i due indietro → tab Esplora che rimette 837 oggetti con una
richiesta senza `cat`), caselle di consegna che aprono ancora costo e
taglia, e 78 prove verdi. In produzione basta il deploy: nessuna
colonna, nessuna leva, nessun asset nuovo. Resta da vedere dal vivo
dentro Telegram, dove contano la gesture bar del telefono e il tema
del client.
Tre difetti di navigazione nati con quei due cantieri (lug 2026, tutti
e tre visti da Andrea sull'app vera). 1) I DOPPIONI entrando in una
categoria da Sfoglia: non un doppio render ma la pagina-dopo che
arriva in ritardo col cursore della vetrina di prima — rimedio
`vetrinaGiro`, vedi «Tenuta al volume». 2) IL GESTO DI AGGIORNAMENTO,
che non era di nessuno e dentro Telegram portava via la Mini App: ora
`disableVerticalSwipes` vale anche alla radice e la tirata è nostra,
coi tre recinti che tengono fuori la galleria a scroll-snap. 3) LO
SWIPE INDIETRO che da Sfoglia non faceva niente: `history.back()` alla
cieca su una sessione che ha una entry sola — ora il gradino lo dice
`d` nello state e l'ultimo passo è esplicito. E l'ultimo passo è che
ESPLORA È LA RADICE MADRE: dalle altre radici l'indietro ci passa, e
solo da Esplora si esce. Deciso in due tempi, ed è la parte da
ricordare: per un giorno la regola è stata «ogni radice esce per conto
suo» (le radici sono sorelle, non parenti), poi Andrea l'ha rovesciata
perché su Subito e Vinted la home È la radice madre — la convenzione
che gli utenti hanno già nelle dita vale più della simmetria del nostro
modello. Tutte e due le ragioni stanno in Architettura, con la
conseguenza accettata (chi apre l'app dritto su un'altra radice
all'indietro finisce in Esplora senza esserci mai passato).
Vedi Architettura, «il gesto indietro» — riprodotti tutti e tre in
locale prima di toccare niente (i doppioni misurati: 60 card di cui 14
doppie, poi 30 su 30 uniche) e ricollaudati dopo: scroll infinito su
tre pagine, due tocchi svelti su due categorie, le sei guardie del
gesto di aggiornamento, `d` che conta giusto lungo tab → piastrella →
dettaglio → i due indietro, e 78 prove verdi. In produzione basta il
deploy: nessuna colonna, nessuna leva.
E POI IL SECONDO GIRO, dalla PWA installata di Andrea (lug 2026), che
è la lezione grossa del cantiere: i primi rimedi funzionavano dentro
Telegram e NON nella PWA, che è il contesto in cui lui prova davvero.
Tre correzioni. 1) La tirata non aggiornava: ricaricava la pagina, cioè
riportava a Esplora — `overscroll-behavior` stava solo sul body e alla
viewport arriva quello dell'HTML, quindi il pull-to-refresh nativo non
era mai stato spento; e i nostri ascoltatori passivi non potevano
chiamare `preventDefault`, ora il touchmove è non-passivo mentre la
tirata è armata. 2) Da Sfoglia la PWA si chiudeva senza passare da
Esplora: lì il gesto è di SISTEMA e non passa da `navIndietro`, quindi
il passaggio dalla madre non si può intercettare — va PREPARATO, e ora
il primo passo via da Esplora spinge una entry. 3) Gli annunci a foto
SINGOLA scorrevano di lato trascinando la pagina: la striscia restava
scorrevole senza niente da scorrere e l'incatenamento arrivava alla
viewport (stessa causa del punto 1, sull'asse X). Vedi Architettura
per la distinzione fra i due contesti, che è la cosa da non
dimenticare: nella PWA non c'è niente da intercettare.
Verificato in locale nel contesto PWA (senza `initData`, col gesto
simulato come `history.back()` diretto): la catena piastrella →
dettaglio risale a categoria, Sfoglia, Esplora-intera in tre gesti; i
tab costano un indietro solo; la tirata in categoria annulla il gesto
nativo, fa una chiamata e non si muove; la galleria a una foto non
scorre e la pagina non sborda. E POI PROVATO DA ANDREA SUL TELEFONO,
nei DUE contesti: tirata, galleria, radice madre e chiusura funzionano
in entrambi, `tg.close()` compreso.
Restava un terzo caso, che si presentava UGUALE nei due contesti — ed
è il modo in cui si è capito che era contenuto e non contesto: due
annunci importati si trascinavano di lato col dito sul corpo della
scheda, per una parola lunga senza spazi che allargava il documento.
Vedi «il testo dell'utente non può allargare la pagina» nel dettaglio
annuncio, e in particolare il `min-width:0` sul figlio flex, che è la
metà del rimedio che non viene in mente.
La 27ª categoria e l'albero dormiente (ago 2026, due cantierini in un
giorno): «Buoni ed esperienze» accesa subito — la merce vera che
moriva in «Altro» (pacchetto B&B, buoni Zalando) ha una casa, coi
sette posti, i gemelli SENZA_CONDIZIONE e le righe-voucher del
modello CSV traslocate — e l'albero delle SOTTOCATEGORIE definito ma
mostrato mai: 86 sottovoci su 26 categorie (l'86esima, «Mare e
piscina», nata dal Telo d'Amare vero), disegnate sui 46 annunci
veri di produzione, colonna e payload silenzioso già vivi, UI zero
(vedi Architettura per il patto, le regole di confine e la decisione
su Elettronica, che resta col contenuto suo invece di chiudere).
Collaudato: 38 prove pure nuove/aggiornate in prove.py, 16 verifiche
TestClient su DB usa-e-getta (giudici in pubblica/modifica, conserva/
azzera, la 27ª senza condizione, la vetrina che non mostra la
colonna) più il filo del CSV. IN PRODUZIONE basta il deploy (la
migrazione della colonna gira da sola); dopo il deploy gli
spostamenti veri — B&B e Zalando verso la voce nuova (il casco moto
citato nei primi appunti era merce del db di COLLAUDO, non di
produzione) — si mettono in coda con `sposta_a_mano.py` sul VPS e si
approvano dalla coda admin, che aggiorna anche il NIP-99.
Il GIUDICE SILENZIOSO (ago 2026, il giorno dopo): la colonna si
riempie da sola a parole chiave dentro la categoria scelta — misurato
prima di accenderlo (45/46 in produzione, 12/15 fuori campione, zero
sbagliati: si astiene, non sbaglia), agganciato a pubblica/modifica/
CSV/dopo-import Nostr, con `assegna_sottocategorie.py` per la passata
sul pregresso e il termometro `--conta` che dice dove arricchire il
dizionario coi dati veri. Collaudato: 11 prove pure nuove (dizionario
allineato all'albero voce per voce + il giudice nei suoi casi), 6
verifiche TestClient dei ganci su DB usa-e-getta, e lo script nei tre
modi su una copia del db locale (300 assegnate, idempotente al terzo
giro). IN PRODUZIONE: deploy, poi `python assegna_sottocategorie.py`
sul VPS per l'anteprima e `--scrivi` per la passata una tantum.
L'ACCENSIONE dell'albero è un cantiere futuro, solo frontend + param.
L'asta 🔨 (ago 2026, cantiere in sette passi con revisione di Andrea
sui passi dei soldi): vendita al miglior offerente con escrow
incrementale — puntare è pagare, si versa solo la differenza, il
vincitore diventa un ordine già pagato e i perdenti riscuotono dal
binario degli incassi. Vedi Architettura per schema, motore, chiusura,
regola della lapide e strade scartate. Collaudata in locale su DB
usa-e-getta lungo tutti i passi (partita a tre offerenti con la corsa
risolta al saldo, proroga anti-cecchino, tardivi nel registro, ritiro
definitivo con la cintura del saldo postumo, chiusura idempotente con
l'invariante dei totali, fusione con collisione e lapide, giro visivo
della demo) e con 19 prove pure in prove.py (127 totali). IN
PRODUZIONE: il deploy da solo non cambia niente (migrazioni additive);
le aste si accendono SOLO scrivendo `ASTA_ABILITATA = True` nel config
del VPS e riavviando — da fare guardando il primo giro col journal
aperto, e il primo giro vero dentro Telegram (puntata, sorpasso,
chiusura, riscossione con wallet reale a cifre minuscole) è il
collaudo che manca. RESTA DA DECIDERE a rodaggio: se e quando dare
alle aste la radice «🔨 Aste» nello slot vuoto della nav.
Il disarmo dell'auto-sblocco (ago 2026, decisione di Andrea presa
guardando un ordine vero): i sats non si muovono più senza un gesto
umano — leva `AUTO_SBLOCCO_ATTIVO` che nasce False, i due rami fisici
dell'orologio spenti, e al loro posto il promemoria al compratore coi
suoi due bottoni, poi il 🧊 ai moderatori. Le finestre del digitale e
i timer che RESTITUISCONO (chiusura d'asta, rimborsi, riacciuffo)
restano armati, ed è la regola precisa: nessun timer sposta sats da
una parte a un'altra. Vedi Architettura per il censimento completo,
le eccezioni motivate e il piano di rientro. Collaudato con 22
sentinelle nuove in prove.py (188 totali, una per riga del censimento
— quelle che devono tacere e quelle che devono restare accese) più un
collaudo eseguibile su DB usa-e-getta, 40 verdi: fisico/asta/set che
non si sbloccano, i due digitali che si sbloccano ancora, la cadenza
fino al tetto e poi il silenzio, il caso normale in cui il compratore
conferma e il promemoria smette da solo, e la regressione a leva
accesa. IN PRODUZIONE basta il deploy (le due colonne nascono da
sole) — fatto, e verificato sul caso che ha aperto il cantiere:
l'ordine #28, a 6,44 giorni su 10, è rimasto `shipped` con zero
squilli invece di sbloccarsi tre giorni e mezzo dopo.
Il venditore che non fa partire la merce (ago 2026, il giorno dopo, dopo
una verifica indipendente del disarmo che ha confermato tutte e cinque
le righe del censimento): chiuso il buco 1 — un ordine `locked` non
aveva nessun timer e nessuna parola, e il compratore non sapeva di poter
aprire una disputa — e con lui il gemello digitale che non era nemmeno
dichiarato. `sollecita_venditori_fermi` è una FUNZIONE SORELLA di
`sollecita_conferme_ferme` e non una sua popolazione, perché il buco è
preesistente al disarmo e quindi non deve stare dietro
`AUTO_SBLOCCO_ATTIVO`: così il diff sul codice dei soldi è ZERO, solo
aggiunte. Vedi Architettura per le due finestre (5 giorni / 48 ore) coi
loro perché, per le colonne che dicono CHI aspettiamo, e soprattutto per
la trappola di `aggiornato` — che `deposita_invoice` scrive proprio su
`locked`, cioè il venditore avrebbe potuto rimandare il proprio
promemoria ri-salvando la sua invoice d'incasso. Collaudato con 9
sentinelle nuove in prove.py (197 verdi) e un collaudo eseguibile su DB
usa-e-getta, 27 verdi: le due finestre al giorno e all'ora giusti, la
trappola dell'invoice ri-salvata provata sul serio, il set col titolo
sintetizzato, la cadenza fino al 🧊 e poi il silenzio, il venditore che
spedisce e il contatore del compratore che riparte da zero, le strade
che non ci riguardano, e la regressione a leva riaccesa. IN PRODUZIONE
basta il deploy (le due colonne nascono da sole, le due leve hanno un
default nel codice): il primo giro da guardare è un ordine `locked` con
più di 5 giorni sulle spalle — al primo battito dell'orologio arriva UNO
squillo al venditore e UNO al compratore.

L'importo di ogni bolt11 in uscita si controlla contro il dovuto (ago
2026, C-1 dell'audit di sicurezza — la prima voce chiusa, e l'unica
critica). Nel LNURL-pay la fattura la scrive il wallet del
beneficiario: il `ln_address` è auto-dichiarato, quindi un dominio
proprio poteva rispondere con qualunque cifra e usciva quella scritta
dentro la bolt11. Il controllo esisteva già sul ramo dell'invoice
incollata a mano — mancava solo su quello automatico. Ora il giudice è
uno (`importo_invoice`) e la cintura sta su `paga_venditore`, con
`atteso_sats` obbligatorio senza default così ogni strada d'uscita
futura la eredita. Vedi Architettura per il perché per esteso. Provato
in due sensi: 212 prove verdi (erano 197), dove le sei della cintura
asseriscono che la POST verso l'admin key **non è mai partita** — non
che una funzione «torna False» — più cinque sentinelle anti-refactor;
e un collaudo end-to-end su DB usa-e-getta sui tre chiamanti con
eccesso/difetto/onesto, che tiene ferma anche la regressione (wallet
onesto = tutto come prima). La falla è stata riprodotta sul codice di
HEAD prima di toccarla: 1 sat dovuto, 100 milioni usciti. IN
PRODUZIONE basta il deploy: nessuna colonna, nessuna leva, nessuna
rotta, nessuna migrazione.
DA RICORDARE QUANDO SI DECIDERÀ LA COMMISSIONE CON ALAN, ed è qui e
non solo in Architettura perché è lì che ci si inciamperà: la cintura
è RETROATTIVA sulle invoice già depositate. Oggi con
COMMISSIONE_PERCENTO e PROTEZIONE_PERCENTO a 0 non cambia niente, ma
il giorno che la percentuale si accende una invoice depositata col
vecchio netto e pagata col nuovo non combacia più e viene rifiutata:
il venditore riceve l'avviso e ne incolla una nuova, i sats restano in
cassaforte, nessuno perde niente. È il comportamento corretto — non si
paga la cifra sbagliata — ma va guardata la coda degli ordini
`confirmed` con una invoice già depositata prima di girare la leva, o
si scambieranno dei rifiuti giusti per un guasto.
Il secondo giro dell'audit (ago 2026) ha chiuso le due voci ALTE
rimaste, più il buco della CI che le prove stesse non vedevano.
1) L'INITDATA SCADE (24 ore, leva `ORE_INITDATA`): la firma dice CHI,
non QUANDO, e uno catturato apriva quell'account per sempre — vedi
Architettura, sotto il login web, per il perché delle 24 ore e non
dei 5 minuti del widget. 2) `/foto` NON È PIÙ MONTATA: rotta
esplicita con la whitelist delle forme, e la regola ferrea 3 diventa
verificabile invece che raccomandata. 3) LA CI INSTALLA PILLOW, e una
prova saltata si conta invece di sparire. 4) `MODALITA_COLLAUDO` nasce
`False` in `config_esempio.py` (in produzione era già False,
verificato: cambia da dove si parte, non cosa gira). Provate: 253
verdi (erano 212), il buco dell'initData riprodotto sul codice di
prima, il giro degli header fatto su un server vero — foto 200 e 304,
illustrazioni invariate, 404 a `..%2Fconfig.py`, `%00` e `%0A`. In
produzione basta il deploy: nessuna colonna, nessuna migrazione.
DA GUARDARE al primo deploy: il cartello «Sessione scaduta» dentro
Telegram vero — in locale si è verificato che il banner si disegna e
sta su una riga, ma il ramo che lo accende ha bisogno di un initData
vero, che solo Telegram conia.
Il terzo giro (ago 2026) ha chiuso le sette voci MEDIE, e la lista
dell'audit adesso è vuota. In ordine di gravità: 1) il timeout di
`paga_venditore`, che poteva far uscire i sats DUE volte — il caso
riprodotto sul codice di prima: due giri, due fatture diverse, due
richieste di pagamento per lo stesso ordine; 2) la disputa che
usciva dalla coda dei moderatori quando il pagamento falliva;
3) l'IDOR su `verifica-pagamento`, che era un oracolo sullo stato di
ogni ordine del mercatino; 4) lo scanner della CI cieco sulla
cronologia e su tre forme di segreto; 5) Fernet senza KDF e col
fail-open muto; 6) il guardiano anti-SSRF aggirabile con un `302`, e
l'import Nostr senza guardie affatto; 7) nessun freno su
`/api/search`. Più i timeout espliciti sui due tubi LNbits in
entrata. Tutte in Architettura, alle voci loro.
Provate: 320 verdi (erano 253), e i tre difetti dei soldi riprodotti
sul codice di prima prima di ripararli. Le prove nuove asseriscono
il NON FATTO: nessun secondo pagamento, nessuna fattura nuova
coniata, nessuno stato riscritto, zero domande a LNbits per conto
d'altri.
IN PRODUZIONE il deploy fa girare tre migrazioni additive
(`payout_stato`, `payout_hash`, `payout_verso` su `ordini` e su
`rimborsi_asta`) e niente altro. `TETTO_RICERCHE_AI_ORA` ha un
default nel codice; se in rodaggio 30 ricerche l'ora stanno strette
a qualcuno, è una riga nel config. DA GUARDARE al primo deploy: la
riga d'avvio sui contenuti digitali — se dice che si scrivono IN
CHIARO, sul VPS `CHIAVE_CONTENUTI_DIGITALI` è vuota.
IMPERFEZIONI DICHIARATE che restano: il DNS-rebinding fra controllo
e download (era già accettato), i commit di MERGE fuori dalla
scansione della cronologia, e il fatto che uno sconosciuto possa
ancora far bussare il nostro LNbits chiedendo la verifica dei PROPRI
ordini.

Giro di interfaccia (ago 2026, undici punti dal campo e dal feedback di
Andrea). La ✕ della pagina del pacco svuota davvero, con la conferma
davanti — il gesto indietro no, e il perché sta nella voce sua: nella
PWA è di sistema e non si può intercettare. IL TRACCIAMENTO su tre
gambe (prevenzione, forma euristica che non blocca mai, correzione solo
da moderatore con traccia visibile a tutt'e due le parti), col buco
trovato provandolo dal vivo: il moderatore non poteva nemmeno APRIRE un
ordine spedito fra estranei, e senza il parametro `ordine` il pannello
sarebbe rimasto irraggiungibile. Colori coerenti in vetrina (lampo
rossa anche nella cornice e nel prezzo, asta petrolio). Tetto del
barattolo da 20 a 10 ed è una LEVA; conteggio pubblico e anonimo dei
salvataggi accanto all'icona (da 2 in su, dichiarato); il barattolino
scende in basso a destra sulla foto, il liquido sale arancio invece di
rovesciare lo sfondo, e il bottone grande sotto Acquista è sparito.
«Altri oggetti» da striscia a griglia col bottone sticky. Il 🔨 in nav
c'è sempre e a leva spenta dice che le aste stanno arrivando (con la
leva nella busta di prima pagina, che chiude l'imperfezione degli
anonimi). Il logo torna al mercatino. E la forma di «Acquista» è la
forma di TUTTI: era una deroga scritta a mano in quattro punti con due
valori diversi, ora è la base con un token solo — vedi la voce per
l'elenco di cosa è passato al rettangolo e di cosa resta tondo di
proposito. Collaudato: 389 prove verdi (erano 320, con le tre famiglie
nuove — la correzione del tracciamento, il barattolo su tre tetti
diversi, le forme dei codici sui casi veri) più il giro visivo via CDP
a 375 e 1280px nei due temi, zero errori JS, e la catena del pacco
esercitata dal vivo (conferma, indietro che NON svuota, svuota che
azzera davvero). IN PRODUZIONE il deploy fa girare due migrazioni
additive (`tracking_corretto_il`, `tracking_reso_corretto_il`) e crea
`idx_preferiti_annuncio`; nient'altro. ATTENZIONE al tetto del
barattolo: il default 10 vive nel CODICE, e una riga `MAX_PREFERITI`
esplicita nel config del VPS vincerebbe su di lui — si verifica prima
del deploy (vedi Produzione).

La pagina d'acquisto (ago 2026, il cantiere annunciato qui sotto come
«prossimo», ora FATTO): il foglio del varco è morto e Acquista porta
sempre a `view-acquisto` — articoli, le vie col solo costo di
spedizione per pillola (ritiro / casa / punto di ritiro / codice
online; il totale lo dice il conto), il campo del punto col
varco-mappa, il conto DEL SERVER prima della invoice; il venditore
dichiara DUE costi di spedizione e lo spedizioniere del negozio, il
compratore scrive il punto che il venditore ritrova nell'ordine. Le
decisioni di Andrea: costo unico come fallback su entrambe le strade,
la via punto SEMPRE offerta (dal secondo giro: senza spedizioniere
dichiarato vale l'accordo in chat, detto in pagina — supera il gate
del primo giro), e il conto di «Controlla il
pacco» dallo stesso preventivo (mai due conti che divergono, anteprima
sulla più economica dichiarandolo). Vedi Architettura, «LA PAGINA
D'ACQUISTO», per il modello dati (punto in colonna, MAI un valore
nuovo di consegna_scelta; il flag della tariffa; le quattro pure del
conto) e i perché. Collaudato: 450 prove verdi in CI (61 nuove, con le
sentinelle sul preventivo-che-non-crea e sul patto del ricontrollo
senza await), 50 verifiche TestClient su DB usa-e-getta — LA PROVA
REGINA: preventivo == compra a parità di via, al sat, mono e set — coi
caratteri strani nel punto lungo tutta la filiera, e il giro visivo
CDP chiaro/scuro a 375/1280 con zero errori JS (che ha anche trovato
dal vivo il 409 dello stock con la sua pagina d'errore, e l'edit di
setValuta finito su rinfrescaViste). Col SECONDO GIRO (feedback di
Andrea sul primo): il bottone finale dice «Paga», le pillole della
consegna il solo costo di spedizione, e la via punto si offre SEMPRE
(la decisione che supera il gate del primo giro). Col TERZO GIRO il
punto si fissava quando il corriere era noto: con la rete dichiarata
si scriveva al pagamento, senza si sceglieva la sola strada e il
punto arrivava dal campo dentro l'ordine (`via_punto`,
`POST /api/orders/{id}/punto-ritiro`, spedito bloccato finché manca
— dove spedirebbe?). E col QUARTO GIRO (ago 2026) la scelta del punto
è tornata SEMPRE prima di «Paga», come su Subito e Vinted: il campo
c'è anche senza rete — due mappe e la riga onesta — la regola vive
nel client (il 400 del server resta sul solo ramo con rete,
tolleranza per il client di ieri), il campo dell'ordine è diventato
la rete di sicurezza della correzione e il gate di segna_spedito
resta per il residuo; vedi Architettura, «E LA SCELTA DEL PUNTO
TORNA SEMPRE PRIMA DI "PAGA"», coi perché di tutti e due i giri.
Collaudato il quarto giro dal vivo sul server locale: campo e mappe
nei due casi, guardia a punto vuoto (zero POST), ordine nato col
punto scritto anche senza rete, 1443 prove verdi (4 nuove, 1
rovesciata). IN PRODUZIONE il deploy fa girare le migrazioni
additive (tre colonne punto su annunci, punto_ritiro + via_punto su
ordini, spedizioniere + avvisato_spedizioniere su utenti) e al primo
battito dell'orologio parte la notifica UNA-TANTUM ai venditori che
spediscono senza spedizioniere — col timbro, mai due volte. DA
GUARDARE dal vivo dentro Telegram: il giro completo su un telefono
vero (pagina, punto, paySheet sopra la pagina), il primo ordine al
punto visto dal venditore — nei due flussi, rete e non — e il testo
della campagna nel journal del primo giro.
Il negozio in ferie 🌴 (ago 2026): il venditore che parte chiude la
bottega con la data di rientro, e gli annunci RESTANO in vetrina col
prezzo in grigio — si guardano, non si comprano. Le decisioni di
Andrea: cosa BLOCCA la chiusura (locked non spediti, aste vive,
accordi già stretti, pagamenti in viaggio, lampo in corso — gli
ordini già spediti no), le offerte pendenti che DECADONO col 🕊, il
rientro AUTOMATICO alla data col promemoria il giorno prima, e su
Nostr NIENTE. Il modello è una colonna sola col gate in LETTURA, lo
stesso patto di lampo e asta: il negozio riapre da solo, senza
orologio. Vedi Architettura per le cinque cose che trattengono coi
loro perché, per il LEFT JOIN dei set (la lezione alla terza volta) e
per le due strade scartate sul badge in card, misurate in pixel.
Collaudato: 47 prove nuove in `prove.py` (640 verdi, erano 593) — fra
cui gli impegni uno per uno su sqlite in memoria, il caso SET con
`annuncio_id=0`, e le sentinelle che la guardia stia PRIMA della
invoice in tutti e dieci i varchi — più un collaudo TestClient su DB
usa-e-getta (31 verdi) che verifica le due cose che contano davvero:
che a negozio chiuso non nasca NESSUNA invoice, e che il rientro sia
IMMEDIATO senza che la scopa sia mai girata. Più il giro visivo via
CDP a 320/360/750px nei due temi (badge che non tocca il barattolino,
prezzo grigio misurato contro la carta, cassetto e elenco degli
impegni che va a capo). IN PRODUZIONE basta il deploy: le due colonne
(`ferie_fino`, `ferie_avvisato`) nascono da sole e le tre leve hanno
il default nel codice — `FERIE_ATTIVE` è ACCESA, che qui non esce
niente verso nessuno. DA GUARDARE al primo giro: il journal del
promemoria di rientro, e il primo venditore vero che chiude (che
l'elenco degli impegni gli dica cose sensate).
Lo sconto carrello 🎁 (ago 2026): il venditore premia chi compra più
cose in un ordine solo — UNA regola per negozio, «da N articoli −X%»,
sul SOLO prezzo degli articoli e mai sulla spedizione. Le quattro
decisioni di Andrea: il MONO non sconta mai (e c'è anche la ragione
tecnica — la divisione a ritroso di `_righe_ordine` si romperebbe in
silenzio), si CUMULA con lampo e accordo, si dice in pubblico in due
posti soli (negozio e «Altri oggetti»), la soglia conta i PEZZI. Il
modello è la voce di TESTATA che questo file dichiarava già preparata:
`ordine_righe` resta intatta e gli unitari LORDI. Vedi Architettura,
«LO SCONTO CARRELLO», per il perché di ognuna, per la colonna
TESTIMONE (che è la riga da leggere prima di toccare una strada del
denaro) e per la clausola dell'euro nativo, che è l'unico punto dove
la modifica poteva produrre una cifra precisa e falsa.
Collaudato: 99 prove nuove in `prove.py` (738 verdi, erano 640) — le
pure del conto una per una (soglia esatta e soglia−1, arrotondamenti
col resto a chi paga, i limiti, l'invariante, la cascata col FONDO
detto ad alta voce) più 38 sentinelle di forma, fra cui quelle che
tengono lo sconto fuori dal mono, fuori dal payload del compratore e
fuori da ogni strada del denaro in uscita. Più un collaudo TestClient
su DB usa-e-getta (71 verdi) con in testa LA PROVA REGINA aggiornata:
preventivo == compra al sat su quattro combinazioni, e `prezzo_sats`
== l'importo della bolt11 CONIATA — il confronto che lega il libro
mastro al denaro vero — con l'identità di bilancio riletta dal
database a ogni ordine; e i casi chiesti da Andrea: sconto cambiato
fra preventivo e acquisto (nei due versi), cambiato a invoice viva
(il prezzo non si ricalcola), il mono a ×5 che non sconta, il netto
del venditore sul totale scontato, l'euro nativo che resta ESATTO, e
la leva spenta che non lascia niente in piedi. Più il giro visivo via
CDP a 320/375/750px nei due temi: il conto che quadra a mano nelle due
valute, l'invito che conta e si trasforma alla soglia, il paySheet che
dice la stessa cifra della pagina, la scheda ordine che torna, e il
cassetto avanti e indietro (dove il giro dal vivo ha trovato un bug
vero: la bozza si fissava prima che la regola arrivasse). IN
PRODUZIONE basta il deploy — le quattro colonne nascono a 0, cioè
regola spenta per tutti, e le leve hanno il default nel codice
(`SCONTO_PACCO_ATTIVO` è ACCESA: qui non esce niente verso nessuno).
DA GUARDARE al primo giro: il controllo del libro mastro in SQL (le
query sono pronte, le lancia Andrea), il primo acquisto scontato vero
dentro Telegram con la bolt11 su LNbits, e il primo payout di un
ordine scontato — se `paga_venditore` avvisa i moderatori, ci si ferma.
La ronda del libro mastro (ago 2026, il giorno dopo): le query che
sorvegliano gli invarianti non si lanciano più a mano — le gira
l'orologio una volta al giorno. 15 controlli, tutti già dichiarati in
questo file: l'aritmetica degli ordini col suo sconto, la forma di
`ordine_righe`, la cassa delle aste chiuse, le cinture d'idempotenza
dei rimborsi, l'annuncio a due teste. A libro mastro sano TACE — un
«tutto bene» quotidiano è rumore; quando qualcosa non torna manda il
🧊 coi nomi e gli id, una volta al giorno finché il problema esiste.
LEGGE E BASTA: nessuna correzione automatica. Vedi Architettura, «LA
RONDA DEL LIBRO MASTRO», soprattutto per quali invarianti sono stati
lasciati FUORI e perché (hanno stati transitori legittimi: suonerebbero
su casi normali, che è il modo in cui si impara a ignorare un allarme).
Collaudato: 164 prove nuove in `prove.py` (902 verdi, erano 738) — le
query girano DAVVERO su un database gemello in memoria, prima sano
(nessuno deve fiatare) e poi con una riga rotta piantata per OGNI
controllo, che deve trovarla col suo id: una query di controllo
sbagliata non fallisce, TACE, ed è il peggior modo di fallire. Più 15
verifiche dal vivo sul giro completo (silenzio a db sano, l'avviso
all'id giusto, il gate che non ripete a ogni battito ma ribussa il
giorno dopo, la riga rotta ancora rotta dopo la ronda, la leva che
spegne) e le 15 query lanciate in sola lettura sul database vero.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione, e
la leva ha il default nel codice. DA GUARDARE al primo giro: che nel
journal non compaia NIENTE — se arriva un 🧊 il primo giorno, quello è
il momento di guardare, non di sistemare la ronda.
Il criterio dello sconto carrello (ago 2026, il giorno dopo, da un
venditore vero): «se vendo un computer lo sconto lo do già da 2 pezzi,
se vendo cianfrusaglie ne servono tante». Lui chiedeva una soglia per
PRODOTTO — scartata, non sarebbe spiegabile su un carrello misto e
romperebbe la divisione a ritroso dell'unitario. La soglia resta UNA
per negozio e a cambiare è il CRITERIO: a pezzi come sempre, o a
VALORE degli articoli. Le decisioni di Andrea: la soglia a valore è in
SATS (l'euro è un aiuto per SCEGLIERE nel cassetto, mai l'unità della
soglia), colonne separate perché `sconto_pacco_soglia` non cambi mai
significato, e il valore si confronta col LORDO — cioè col carrello
DOPO lampo e accordo, quindi una lampo generosa può far scendere sotto
soglia un carrello che a listino ci arrivava: è voluto, ha la sua
prova e il cassetto lo dice al venditore. Vedi Architettura, «IL
CRITERIO LO SCEGLIE IL VENDITORE», per il perché dei sats e per la
regola d'oro della retrocompatibilità (`_sconto_pubblico`: la soglia
in pezzi esce >0 solo a criterio pezzi, ed è il lucchetto del client
vecchio in cache).
Collaudato: 118 prove nuove in `prove.py` (1020 verdi, erano 902) —
fra cui gli shim che fanno girare IDENTICHE le ~35 asserzioni di ieri
(la regressione dei negozi esistenti, gratis), il caso misto nei due
versi, la lampo che spegne lo sconto, il criterio ignoto che NON
ripiega sui pezzi, e le prime prove funzionali di `_regola_sconto`,
che la sua docstring prometteva dal giorno in cui è nata e non aveva
mai avuto. Più un collaudo eseguibile su DB usa-e-getta (58 verdi) con
in testa LA PROVA REGINA aggiornata — preventivo == compra AL SAT su
entrambi i criteri e al filo della soglia — l'identità di bilancio
riletta dal database, le due soglie che si conservano a vicenda anche
da un client vecchio, e la ronda che tace. Più il giro visivo via CDP
a 320 e 375px nei due temi, che ha trovato dal vivo l'unico difetto
del cantiere: sulla pillola accesa l'≈€ spariva, perché era una
`.unit`. IN PRODUZIONE basta il deploy — le due colonne nascono col
loro default (`'pezzi'`, 0), cioè tutti i negozi che scontano oggi
continuano identici, e le tre leve nuove hanno il default nel codice.
DA GUARDARE al primo giro: il primo venditore che passa a valore (che
il cassetto e la riga pubblica dicano la stessa cifra) e il polso SQL
17, che adesso dice anche il criterio.
La spedizione gratis sopra soglia (ago 2026, il giorno dopo, richiesta
dal campo): «da N sats di articoli la spedizione la offro io», la
seconda promessa di negozio. La cosa da sapere prima di tutte è che
VALE ANCHE SULL'ACQUISTO SINGOLO, e non per scelta ma per FORMA:
azzerare una tariffa scrive `spedizione_sats=0` — lo stato che ogni
annuncio con tariffa gratis dichiarata ha da sempre — mentre lo sconto
sottrae dal totale e romperebbe la divisione a ritroso dell'unitario,
che è il motivo per cui il mono non sconta. Le decisioni di Andrea: la
soglia in sats, le due promesse che guardano lo STESSO numero (l'
articolo lordo) e quindi non possono spegnersi a vicenda, la riga
pubblica in TRE posti — negozio, «Altri oggetti» e la scheda
dell'annuncio, che lo sconto non ha —, la colonna testimone
`ordini.sped_gratis_sats`, e la decisione TARDI sul cambio con la sua
imperfezione dichiarata. Più le due righe nel form Vendi, ognuna
attaccata al campo di cui parla (unirle è stato valutato e scartato:
il perché sta in Architettura, ed è la parte che vale). Vedi
Architettura, «LA SPEDIZIONE GRATIS SOPRA SOGLIA».
Collaudata: 100 prove nuove in `prove.py` (1120 verdi, erano 1020) —
le pure al filo della soglia, i quattro quadranti dell'indipendenza
col caso che smaschera una dipendenza (netto sotto soglia, lordo
sopra), la lampo che fa scendere sotto, e le sentinelle che tengono la
tariffa offerta fuori da ogni strada d'uscita del denaro e la
decisione nello stesso punto nei quattro percorsi. Più un collaudo
eseguibile su DB usa-e-getta (80 verdi) con in testa LA PROVA REGINA:
preventivo == compra AL SAT su mono e set, sopra e sotto soglia, in
sats e in EUR, e `prezzo_sats` == l'importo della bolt11 CONIATA — più
l'euro nativo che resta esatto, la soglia cambiata fra preventivo e
acquisto nei due versi, la leva spenta che spegne tutte le vetrine
insieme, e la ronda che tace. Più il giro visivo via CDP a 375px nei
due temi e nelle due valute, zero errori JS, che ha trovato dal vivo
tre cose: «gratuita» che usciva in monospazio (contro la regola di
casa per quella parola), il titolo del cassetto che andava a capo, e
la punteggiatura della riga dello sconto nel form. IN PRODUZIONE basta
il deploy — le due colonne nascono a 0, cioè promessa spenta per
tutti, e le tre leve hanno il default nel codice
(`SPED_GRATIS_ATTIVO` è ACCESA: non esce niente verso nessuno). DA
GUARDARE al primo giro: il primo venditore che l'accende, e il primo
ordine con spedizione offerta vero dentro Telegram con la bolt11 su
LNbits — se `paga_venditore` avvisa i moderatori, ci si ferma.
I suggerimenti dal bot diventano attivi di serie, ma col RITMO (ago
2026, decisione di Andrea): «💡 Suggerimenti sui miei annunci» nasce
acceso — l'opt-in non lo accendeva quasi nessuno — e a tenerli gentili
è il tetto di uno ogni 7 giorni per PERSONA, qualunque sia la coda
(prima era per annuncio, e chi ne pubblicava cinque in un pomeriggio
ne riceveva cinque). Il perché è la parte da non ammorbidire: chi si
stufa BLOCCA IL BOT, e col bot bloccato non riceve più le notifiche
degli ordini, che sono portanti; su Nostr il danno è identico e meno
visibile, perché smette di leggere i DM. Più due suggerimenti nuovi —
lo sconto carrello e la spedizione gratis a chi non li ha accesi —
una volta sola per funzione e mai insieme, che è una proprietà del
timbro del ritmo e non una regola scritta.
COME SI DISTINGUE «mai toccato» da «spento da lui» (la domanda di
Andrea): una colonna del GESTO, `utenti.suggerimenti_scelti`, e non un
terzo stato dentro il valore — con «2 = spento» il primo `if` scritto
distrattamente leggerebbe 2 come acceso, cioè fallirebbe nel verso di
scrivere a chi ha detto no. Del PREGRESSO però il gesto NON ESISTE, e
si dichiara: l'endpoint di ieri scriveva solo il valore, quindi chi è
a 0 può essere chi non l'ha mai guardato o chi l'ha spento. La
migrazione fa l'unica cosa dimostrabile (chi è acceso l'ha acceso lui)
e per gli altri sceglie «mai toccato»; il prezzo è UN messaggio a chi
l'aveva spento, con dentro il modo di rispegnerlo. Vedi Architettura,
«I SUGGERIMENTI SUGLI ANNUNCI».
Collaudati: 37 prove nuove in `prove.py` (1162 verdi, erano 1125) — i
quattro casi del giudice per entrambi i default, la prova che
rovesciare il default non tocca chi ha scelto, il ritmo su un database
di cartone (al sesto giorno chiuso, al settimo esatto riapre), la
whitelist dei timbri che rifiuta un nome fuori catalogo, e le
sentinelle sul timbro-prima-dell'invio e sul gate prima di
`completamento_avvisato`. Più un collaudo eseguibile su DB usa-e-getta
(28 verdi) che gira le funzioni VERE dell'orologio: la migrazione e la
sua idempotenza, chi riceve e chi no, un solo messaggio per giro, il
secondo che arriva solo dopo N giorni ed è l'ALTRA funzione, «una
volta per funzione per sempre», il bersaglio (un annuncio solo →
niente sconto; solo ritiro → niente spedizione gratis), le due leve
nei due stati, e `/api/me` che dice lo stato effettivo. Più il giro
visivo sul cassetto «🔔 Avvisi» nei due temi. IN PRODUZIONE il deploy
fa girare le quattro colonne nuove e la migrazione dei gesti (che
stampa quanti utenti ha registrato); le due leve hanno il default nel
codice. DA GUARDARE al primo giro: il journal della prima passata di
`suggerisci_funzioni` — quanti ne partono — e che nessuno riceva due
messaggi.
Le due soglie a valore passano all'EURO (ago 2026, cambio di rotta
deciso da Andrea il giorno dopo averle fatte in sats): una soglia in
sats DERIVA COL CAMBIO — chi scrive 100.000 pensando «una cinquantina
di euro» si ritrova, sei mesi dopo, una promessa del doppio senza aver
toccato niente. Vale per TUTTE E DUE le promesse, o avremmo due promesse
identiche in due valute diverse. Non cambia niente di sostanziale: si
paga sempre in sats, l'escrow è in sats, il conto è del server, e
`ordini` non si tocca di una riga.
Le tre cose da sapere. 1) LE PURE RESTANO PURE: guadagnano un
argomento (`articolo_eur`), non una chiamata — nasce `_eur_interi`,
che si invoca UNA volta per conto e serve tutte e due le promesse,
così «guardano lo stesso numero» diventa una proprietà della
struttura invece di un patto da ricordare. 2) A CAMBIO MUTO la
promessa NON scatta e lo si dice (fail-closed dentro il giudice,
`promesse_sospese` nel preventivo, riga onesta in pagina), MAI un 503
nuovo: senza cambio un listino in euro non si sa convertire e
l'ordine non nasce, una promessa non si sa solo valutare. E «muto»
vuol dire pochissimo — `cambio_btc_eur` è fail-open e tiene l'ultimo
valore noto, quindi lo 0 esce solo dopo un riavvio dentro
un'interruzione. 3) COLONNE E LEVE NUOVE col suffisso, le vecchie
inerti: una riga `SPED_GRATIS_SOGLIE = (50_000, …)` già scritta in un
config verrebbe letta come euro e spegnerebbe la promessa in silenzio.
Vedi Architettura, «LA SOGLIA A VALORE È IN EURO».
Collaudato: 1198 prove verdi in `prove.py` (erano 1162) — fra cui il
filo esatto nelle due unità, il floor che decide, il cambio muto sui
due giudici, il criterio a PEZZI che a cambio muto scatta lo stesso, e
le sentinelle nuove sulla purezza di `_eur_interi`, sui due 503 che
restano due, e su `cambio_ordine` che non si sporca con la misura. Più
un collaudo eseguibile su DB usa-e-getta (57 verdi) con in testa LA
PROVA REGINA aggiornata — preventivo == compra AL SAT su set e mono,
sotto/al filo/sopra soglia, in sats e in EUR, **e a cambio muto** — col
confronto fra `prezzo_sats` e l'importo della bolt11 coniata, e la
ronda del libro mastro che tace. Più il giro visivo via CDP a 375px nei
due temi (cassetti, tre righe pubbliche, invito del carrello nei suoi
quattro casi compreso il floor a 49 €), zero errori JS. Due difetti
trovati e chiusi strada facendo, tutti e due nelle PROVE e non nel
codice: una sentinella che non poteva fallire, e una finestra a
lunghezza fissa che aveva smesso di provare quel che diceva.
IN PRODUZIONE: il deploy fa nascere le due colonne `*_eur` a zero,
cioè **promesse spente per chi le aveva a valore** — ed è il momento
da guardare. Il rimedio è una riga: `python converti_soglie_euro.py`
in anteprima e poi `--scrivi`. Se non l'ha impostata nessuno (molto
probabile: le due funzioni sono nate ieri) stampa «nessuno» e si
chiude; a ricordarlo c'è la riga d'avvio e il polso SQL 17d. ⚠️ Se il
config del VPS ha righe esplicite `SCONTO_PACCO_VALORI`,
`SCONTO_PACCO_MIN_VALORE`, `SPED_GRATIS_SOGLIE` o `SPED_GRATIS_MIN`,
diventano INERTI: vanno riscritte coi nomi `*_EUR` e con cifre in
euro, o valgono i default del codice (10·25·50·100 €).
DA GUARDARE al primo giro: il primo venditore che rimette la soglia in
euro, e il primo ordine scontato vero con la bolt11 su LNbits.

...e due giorni dopo LA VALUTA TORNA AL VENDITORE (ago 2026, chiesto
dalla comunità): la soglia a valore si dichiara in EURO o in SATS, con
un toggle nel cassetto, e ogni promessa ha la SUA valuta. Non è un
ritorno indietro — si AGGIUNGE la scelta, e accanto al toggle si dice
cosa comporta in tutte e due le direzioni invece di deciderlo al posto
del venditore. Il perché di venerdì (la deriva col cambio) resta vero e
diventa l'avvertimento; il perché che lo supera è che quel difetto ce
l'ha già il prezzo di ogni annuncio in sats, e la valuta in cui uno
ragiona è una scelta sua. IL GUADAGNO che l'euro non poteva dare: in
sats la promessa NON HA BISOGNO DEL CAMBIO — scatta a CoinGecko muto,
l'invito del carrello smette di convertire (era l'unica conversione che
il client fa su una promessa) e un negozio tutto-sats non paga più un
giro di rete. Vedi Architettura, «LA VALUTA DELLA SOGLIA A VALORE LA
SCEGLIE IL VENDITORE», per il modello (le colonne in sats che tornano
vive col significato di sempre, il `DEFAULT 'eur'` che È la migrazione),
per il toggle che CONSERVA e non converte, e per la LEZIONE
STRUTTURALE — «soglia euro a zero» ha smesso di voler dire «promessa
spenta», e tre posti lo codificavano.
E UN DIFETTO PREESISTENTE CHIUSO QUI, dalla domanda di Andrea «cosa
succede in pratica a un venditore col client in cache che tocca
Salva?»: le risposte erano due e tutte e due cattive — sullo sconto un
400 col messaggio SBAGLIATO, sulla spedizione gratis uno SPEGNIMENTO
SILENZIOSO (la chiave assente valeva 0, che lì è lo spegnimento).
Adesso la chiave del valore nell'unità dichiarata dev'essere PRESENTE:
assente = 400 che dice di riaprire l'app, mai un salvataggio muto.
Collaudato: 2393 prove verdi in `prove.py` (erano 2220) — le due pure
sui quattro quadranti valuta × cambio muto, i due lettori con la loro
leva, la regola d'oro torturata su tutte le combinazioni, e una
famiglia NUOVA di prove ESEGUIBILI sui due endpoint (sqlite in memoria)
che asserisce il NON FATTO: body vecchio → 400 **e la colonna riletta
dal database ancora quella di prima**, su tutti e tre i casi, con le
due regressioni dello spegnimento esplicito. Più **DICIASSETTE
MUTAZIONI**, una riga alla volta, ognuna rossa da sola — e sono state
loro a trovare tre difetti veri nelle sentinelle: due fette di sorgente
troppo larghe (una guardia tolta al set passava perché quella del
preventivo era ancora nella stessa fetta) e una prova mancante sul
COALESCE dello sconto, che il client di casa nascondeva mandando sempre
tutte le chiavi. Più la migrazione provata su una COPIA del database
locale (24 righe, tutte a 'eur', promesse identiche prima e dopo) e il
giro dal vivo sul server locale: cassetto col toggle avanti e indietro
che ritrova i 50.000 sats scritti prima di venerdì (non una
conversione), salvataggio in sats end-to-end, le tre righe pubbliche e
la pagina Paga che dicono «sats», zero errori JS — e lì è saltato fuori
l'ultimo difetto, una frase sgrammaticata nella riga del form Vendi.
IN PRODUZIONE basta il deploy: le due colonne nascono con `DEFAULT
'eur'`, cioè **nessuna promessa cambia di un centesimo**, e le quattro
leve nuove (`VALUTE_SOGLIA`, `SCONTO_PACCO_VALORI_SATS`,
`SCONTO_PACCO_MIN_VALORE_SATS`, `SPED_GRATIS_SOGLIE_SATS`,
`SPED_GRATIS_MIN_SATS`) hanno il default nel codice. `converti_soglie_
euro.py` e il suo avviso d'avvio RESTANO e sono ancora giusti — lo
stato che descrivono esiste ancora — ma adesso quel negozio ha un
secondo rimedio: passare la sua soglia a sats, e ritrova il numero che
aveva scritto. DA GUARDARE al primo giro: il primo venditore che sceglie
i sats, e che il libro mastro continui a tacere.

Il supplemento di spedizione per pezzo (ago 2026, caso dal campo: il
riso da 4 kg venduto a sacchi con la spedizione di UNO dichiarata —
chi ne comprava dieci pagava la spedizione di uno). Un campo
facoltativo accanto al costo base, «ogni pezzo in più: +N», PER
ANNUNCIO e non per negozio: il supplemento dipende dall'oggetto, un
sacco di riso non è una collanina. La regola sta in una riga — la
spedizione più cara fa da base, e ogni altro pezzo aggiunge il suo
supplemento — e il mono con quantità ne è un caso particolare, non un
ramo. Le decisioni di Andrea: un supplemento SOLO (vale casa e punto),
la colonna nel CSV, e il fix del bug preesistente qui sotto nel suo
commit. Vedi Architettura, «IL SUPPLEMENTO PER PEZZO», per il MAX che
non è il minimo, l'euro nativo e la ragione per cui qui la divisione a
ritroso dell'unitario regge mentre lo sconto sul mono no.
DUE BUCHI TROVATI mentre si costruiva, tutti e due nel codice di ieri:
`preventivo_ordine` passava a `_strade_preventivo` l'annuncio SENZA la
quantità (col supplemento il preventivo mono avrebbe detto la
spedizione di un pezzo e la invoice quella di dieci — la prima
divergenza preventivo↔compra), e il `None` di una tariffa ancorata col
cambio muto sarebbe diventato un 500 (`max(sped, None)`) invece di un
503. Più la bugia chiusa in vetrina: con base 0 e supplemento, la card
avrebbe scritto «🚚 gratis» e la pagina Paga avrebbe chiesto 27.000
sats per dieci pezzi.
Collaudato: 1296 prove verdi in `prove.py` (erano 1267 — 31 pure sulla
formula, fra cui il fuzz a seme fisso sulle due proprietà strutturali,
il pareggio nelle due permutazioni e l'arrotondamento che si smaschera
solo a cambio non tondo, più le sentinelle di forma, quattro delle
quali torturate rompendole a una a una), e un collaudo eseguibile su
DB usa-e-getta (59 verdi) con in testa LA PROVA REGINA — preventivo ==
compra AL SAT su mono 1/10 pezzi, listino sats e EUR, via casa e
punto, carrello a quantità diverse, spedizione offerta — col confronto
fra `prezzo_sats` e l'importo della bolt11 CONIATA, la divisione a
ritroso verificata anche sul ramo della ripresa, il 503 che resta un
503, e la ronda del libro mastro che tace. Più il giro visivo via CDP
a 375px nei due temi.
IN PRODUZIONE basta il deploy: le due colonne nascono a 0, cioè
supplemento spento per tutti — nessuna migrazione, nessun ordine
esistente cambia di un sat. DA GUARDARE al primo giro: il primo
venditore che lo scrive, e il primo ordine con q≥2 e supplemento vero
dentro Telegram, con la bolt11 confrontata su LNbits.

La promessa della spedizione gratis si leggeva sulla cifra, non sulla
strada (ago 2026, commit suo, trovato col cantiere qui sopra): su un
listino in SATS con la tariffa ancorata all'EURO i sats in colonna
sono 0, quindi il gate `if sped:` non leggeva nemmeno la soglia del
venditore e la spedizione si pagava — mentre `preventivo_ordine` la
legge senza quel gate e la pagina Paga scriveva «gratuita».
Riprodotto su DB usa-e-getta prima di toccare: preventivo 100.000,
invoice 105.000. Ora la guardia è la STRADA. Va nel verso di chi
compra: dopo il deploy quelle spedizioni diventano gratis davvero.

L'import non adotta più gli annunci nati qui (ago 2026): un evento che
abbiamo composto noi e fatto firmare al venditore — il BIVIO — è il
RIFLESSO di una riga locale, non una sua fonte, e l'import lo salta.
Senza il tappo il match per TITOLO gli scriveva addosso
`contatto_nostr`: da lì niente più modifica dal form (e chi ha solo il
badge 🟣 restava senza nessuna strada, che `modifica-firmata` esige
`npub_accesso`), la descrizione si prendeva il footer promozionale, e
una sua NIP-09 da un client qualunque spegneva l'annuncio su Barattolo.
Vedi Architettura, «IL RIFLESSO NON È UNA FONTE», per le tre condizioni
del riconoscimento, la perdita dichiarata (una modifica fatta da un
altro client non arriva più) e la strada scartata del kind 5.
Riprodotto su DB usa-e-getta prima di toccare — adozione, NIP-09 che
spegne, footer nella descrizione e foto riscaricate da noi stessi —
poi verificato che la correzione chiuda tutti e quattro senza spegnere
l'import vero (un annuncio davvero importato entra e si aggiorna come
sempre). 1314 prove verdi, di cui 15 nuove: i due giudici puri sui loro
casi e due sentinelle di forma, TORTURATE con cinque mutazioni del
codice — chiamata tolta, filtro spostato dopo il vaglio, ognuna delle
tre condizioni rotta — e ognuna diventa rossa da sola. IN PRODUZIONE
basta il deploy: nessuna colonna nuova sul server, nessuna migrazione,
nessuna leva (la colonna `nostr_autore` è solo entrata nella lista di
`importa_nostr.py`, per lo script lanciato a mano su un database
vecchio). Il conto prima del cantiere: zero annunci già adottati, uno
esposto al giro dopo. L'ORDINE DEI LAVORI ERA VINCOLANTE e vale per
chiunque ripulisca a mano i doppioni dell'anello: prima il tappo, poi
la rimozione della copia — vedi il caso dell'annuncio 173, che faceva
da parafulmine all'89.

La busta di consegna nell'ordine (ago 2026, dal campo): sugli ordini
verso un punto di ritiro il venditore deposita nome del destinatario e
codice di ritiro DENTRO l'ordine, cifrati, e il compratore li legge da
lì — sostituisce la chat privata, non il corriere (niente mappa,
niente API, niente tracking). La decisione che governa il cantiere:
NIENTE gate su segna_spedito — il codice arriva quando il pacco è GIÀ
al punto, e i due momenti restano separati come nella realtà; al posto
del gate lo stato d'attesa visibile e il promemoria al venditore. La
riga da non ammorbidire: aprire la busta NON è una ricevuta — il GET è
puro, l'escrow si muove solo coi bottoni di sempre, e il moderatore la
busta non la legge mai (in disputa vede solo SE e QUANDO, correzioni
contate comprese). Vedi Architettura, «LA BUSTA DI CONSEGNA», per la
dedup del segnale d'arrivo e il controllo del libro mastro (col suo
gemello da NON fare). Collaudata: 1375 prove verdi (61 nuove, fra cui
la prova regina «la lettura non scrive niente» e la sentinella
rovesciata sul gate che non esiste), collaudo TestClient su DB
usa-e-getta (40 verdi: escrow immobile al deposito, admin respinto,
correzione fino in disputa, nota al moderatore senza mai il contenuto,
ronda che tace sul sano) e giro visivo CDP a 375px nei due temi, con
la verifica dal vivo che dopo l'apertura l'ordine resta `shipped`.
IN PRODUZIONE basta il deploy: sette colonne additive nascono da sole
e la leva ha il default nel codice. DA GUARDARE al primo giro vero: il
primo ordine al punto con la busta depositata dentro Telegram (i due
messaggi a giorni di distanza, mai il doppione) e il journal di
`sollecita_buste_ferme` al primo battito con un ordine oltre i 3
giorni.

La pagina Ordini ristrutturata (ago 2026): filtro «Solo attivi» e
pillole Tutti/Acquisti/Vendite (due assi indipendenti, stato di
sessione, tutto client-side — la WHERE di /api/orders non si tocca),
la foto vera dell'articolo al posto del 📦 (foto0 dal server, per i
set il primo pezzo, ripiego a catena fino al 📦), e il NASCONDERE
degli affari conclusi — mai cancellare: due colonne per-parte, gate
sui soli stati assorbenti released/refunded, ✕ sulla riga col toast
che dice dove ritrovarlo, «N nascosti — mostrali» col ↩ per
rimetterli in vista, controllo nuovo nella ronda del libro mastro.
Vedi Architettura, «LA PAGINA ORDINI RISTRUTTURATA», per le
definizioni dichiarate (cosa è attivo, perché confirmed/refund e
annullato NON si nascondono) e per il LIMITE NOTO: la lista scarica
anche i nascosti, nascondere alleggerisce la vista e non la risposta.
Collaudata: 1440 prove verdi (65 nuove — il gate su TUTTI i dieci
stati non assorbenti, il per-parte, l'anti-oracolo estraneo ==
inesistente, il dump prima/dopo che dimostra che nascondere non muove
niente, il GET vero con foto0 nei quattro casi e il flag che non esce
mai all'altra parte, la parità NASCONDIBILI server↔client, la riga
rotta della ronda trovata col suo id) più il giro visivo CDP a 375px
nei due temi, con e senza foto, zero errori JS: nascondi → toast →
mostrali → rimetti in vista esercitati dal vivo sul server locale.
IN PRODUZIONE basta il deploy: le due colonne nascono da sole a 0,
nessuna leva, nessun backfill; il client vecchio in cache ignora
foto0 e nascosto e vive come oggi.
Tornando indietro la vetrina riparte da dove si era (ago 2026): si apre
un annuncio, si torna, e ci si ritrova sulla stessa riga di card invece
che in cima. LA DIAGNOSI PRIMA DI TUTTO, perché ha deciso il cantiere e
rovescia l'istinto: la griglia non si perde MAI — 90 card prima, 90
durante, 90 dopo, misurate — quindi non c'era niente da ricaricare e la
cura è stata la più semplice delle due (salvare la posizione lasciando
la vetrina, rileggerla tornando). Il giudice del «ritorno» è
`navApplicando`, la bandierina che il motore alza già oggi mentre
ri-applica una entry: da lì escono gratis il pull-to-refresh e il
cambio filtro che ripartono dalla cima, i percorsi che entrano da fuori
che partono normalmente, e la convenzione dei tab. Vedi Architettura,
«TORNANDO INDIETRO LA VETRINA RIPARTE DA DOVE SI ERA», per i due denti
del lucchetto (il conto delle card e l'azzeramento in `loadListings`) e
per cosa NON si copre e perché.
Collaudato: 14 prove nuove in `prove.py` (1457 verdi, erano 1443) —
sentinelle di forma TORTURATE con nove mutazioni del codice, una per
riga sorvegliata (salvataggio spostato dopo il `display:none`, guardia
del ritorno tolta, cintura del conto card tolta, `scrollTo(0,0)`
rimesso, azzeramento spostato dopo il fetch…): ognuna diventa rossa da
sola, nessuna sopravvive. Più il giro dal vivo sul server locale con le
misure a mano — 90 card e 4200px ritrovati identici da dettaglio,
negozio, carrello e pagina d'acquisto, salto multiplo compreso; e i
casi che NON devono ripristinare, verificati uno per uno: vetrina
ricaricata mentre si è via (→ cima, mai il clamp in fondo), ricerca AI,
cambio categoria, tab Esplora su Esplora, deep link `/annuncio/{id}`.
Più due screenshot CDP prima/dopo identici pixel per pixel, e zero
errori JS. Un difetto PREESISTENTE trovato di striscia e chiuso qui: il
focus che torna al campo alla chiusura del picker trascinava la pagina
in cima (`preventScroll`). IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna leva, nessuna rotta — e lo stato vive per la sessione,
niente localStorage. DA GUARDARE dal vivo: il giro su un telefono vero
nei DUE contesti — Mini App (il tasto di Telegram) e PWA installata (lo
swipe di sistema) — che è dove i due cammini si sono già divisi in
passato.
Il cambio non muore a un riavvio (ago 2026, caso vero: due deploy alle
13:34 e alle 13:48, CoinGecko muto in tutti e due, e un compratore
davanti alla pagina d'acquisto bloccata). La cache era già fail-open e
teneva l'ultimo valore noto: il buco era che NASCEVA VUOTA. Ora
l'ultimo cambio letto vive nella tabella `cambio_noto` e torna in cache
nello startup, prima che il server risponda a chiunque; ha un'età oltre
la quale smette di valere (`ORE_CAMBIO_VALIDO`, 24 — fino a ieri non
scadeva mai, quindi qualunque soglia finita è una stretta); si tiene
fresco nell'orologio invece che nel percorso caldo, con la riprova a
pause crescenti al boot e il raffreddamento di un minuto dopo un buco;
e il client non chiama più CoinGecko per conto suo — il cambio viaggia
nella busta di prima pagina di `/api/listings`, una fonte sola, così il
«≈» della vetrina e il conto del server non possono più divergere. Vedi
Architettura, «IL CAMBIO NON MUORE A UN RIAVVIO», per le tre età e per
il perché delle 24 ore.
Poi la fonte unica è costata freschezza, e si è stretta la finestra
(ago 2026, il giorno dopo): il rinfresco ha un giro suo da 60 secondi
(`orologio_cambio`, leva `CAMBIO_RINFRESCO_S`) invece di stare
nell'orologio da dieci minuti — perché da quando la fonte è una sola,
la cadenza del server è la freschezza che vede chiunque guardi un
prezzo. La soglia si DERIVA dalla cadenza (due giri di slack, minimo
120s) invece di essere un secondo numero da tenere in pari, e al
momento della fattura non si forza nessuna lettura: nel percorso caldo
la rete resta la rete di sicurezza dietro il raffreddamento. Misurato
dal vivo: il valore sul disco non ha mai più di 60 secondi, e nell'arco
di due minuti si vede muovere (56.324 → 56.329 → 56.340 €/BTC).
E poi l'ultima verità doppia, trovata nel journal dopo il deploy (ago
2026): alle 14:52:33 il server legge il cambio, alle 14:52:57 l'import
Nostr dice che non è disponibile. `importa_nostr.cambio_btc()` era una
seconda lettura — e stava DENTRO `importa_venditore`, cioè una chiamata
PER VENDITORE a ogni giro orario, dallo stesso IP da cui bussa già il
nostro rinfresco. Ora il server legge il cambio una volta per giro e lo
passa a tutti (`cambio_per_import()`, il patto del `vaglio`), la stessa
GET porta anche il dollaro che all'import serve, e lo script a mano
resta identico. Vedi Architettura, «L'IMPORT DA NOSTR BEVE ALLA STESSA
FONTE».
Collaudato: 21 prove nuove/aggiornate (1512 verdi, erano 1499) più
cinque mutazioni del codice — import che torna a leggersi il cambio da
solo, cambio vuoto che passa in silenzio, lettura spostata dentro il
giro dei venditori, dollaro scaduto che esce lo stesso, euro che smette
di comandare — ognuna rossa da sola. E un collaudo eseguibile che gira
`importa_venditore` VERA su database usa-e-getta coi relay di cartone,
12 verdi: col cambio iniettato l'annuncio in EUR entra convertito al
cambio del server e CoinGecko non viene toccato; col cambio vuoto si
salta e lo si dice; con `cambio=None` la strada di ieri è intatta; e
l'annuncio in USD entra col dollaro del server e si salta senza. IN
PRODUZIONE basta il deploy: la riga 'usd' nasce da sola al primo
rinfresco.
Collaudato: 29 prove nuove in `prove.py` (1486 verdi, erano 1457) — il
giudice puro al filo esatto e un secondo dopo, l'andata e ritorno dal
disco, e il caso del cantiere provato per davvero (cache vuota + rete
muta = vale l'ultimo noto, e un buco non azzera niente) — con le
sentinelle di forma TORTURATE, cinque mutazioni del codice una per
riga sorvegliata, ognuna rossa da sola. Più il giro dal vivo sul
server locale con CoinGecko puntato su un host irraggiungibile: al
riavvio la riga «ripreso dal database», la vetrina che serve il cambio
lo stesso, e un preventivo su un listino da 38,50 € che esce a 68.455
sats invece del 503 di ieri; poi la stessa prova con la riga sul disco
invecchiata a 30 ore, che torna al 503 onesto invece di convertire con
un numero vecchio. E in browser: zero chiamate a CoinGecko, prezzi col
«≈» e nessun errore JS. IN PRODUZIONE basta il deploy: la tabella
nasce da sola (vuota, quindi il primo avvio dice «nessun valore
salvato» e lo chiede subito) e la leva ha il default nel codice. DA
GUARDARE al primo deploy: le due righe 💱 nel journal — al secondo
riavvio deve comparire «ripreso dal database».
Lo stock raccontato bene (ago 2026): l'annuncio esaurito non si butta
più — resta nel negozio in fondo, spento, e il venditore lo rifornisce
con un gesto invece di rifare la scheda da capo. La DIAGNOSI ha ridotto
il cantiere prima di scrivere una riga: il riassortimento esisteva già
(`ricarica_quantita` accettava lo stato 'venduto'), e il guasto vero
era che il deep-link `/annuncio/{id}` rispondeva 404 — un link mandato
a un amico moriva insieme alle scorte. Più il badge «Ne resta 1», che
parla SOLO dove la scarsità è una notizia: la colonna `quantita_max`
esiste per quella domanda sola, e la sua scopa è anche il backfill
onesto («ne ha almeno tanti quanti ne ha adesso» è un limite inferiore
vero, non un passato fabbricato). E il `prompt()` del sistema
operativo se n'è andato: un foglio di casa che sull'errore resta aperto
col numero da correggere. Vedi Architettura, «LO SCAFFALE VUOTO», per
le decisioni di Andrea (dove si vede l'esaurito, dove compare il badge,
il foglio al posto del prompt) e per le tre strade scartate sul colore.
QUATTRO CORREZIONI al piano approvato, tutte trovate costruendo:
1) il RIMBORSO alza il massimo — avevo dichiarato il caso impossibile,
e non lo è (3 pezzi, venduti tutti, ricarica a 1, una disputa ne
rimborsa 3 = 4, sopra il massimo di ieri); 2) l'ASTA non è mai
«esaurita», ed è la stessa riga che il server ha sempre avuto in
`ricarica_quantita`; 3) il badge non prende un colore ma la CARTA, e
dice «Ne resta 1» perché a 320px «Ultimo pezzo» tocca il barattolino
(misurato); 4) Esc NON arriva gratis ai fogli — solo picker, lightbox
e tour lo ascoltano, e aggiungerlo sarebbe un cantiere per tutti e
dodici o per nessuno. Più la correzione di un numero SBAGLIATO in
questo file da mesi: il prezzo arancio del cartellino rende 3,01 e non
3,59 (la conclusione regge e anzi si rafforza — vedi la voce ferie).
Collaudato: 1552 prove verdi (40 nuove, fra cui la scopa girata
DAVVERO su un database di cartone e il giudice puro sui sette casi che
decidono), 11 MUTAZIONI del codice una riga alla volta — massimo
assegnato secco, scopa che abbassa, pop tolto, guardie del bottone,
lampo che torna a parlare su un esaurito — e ognuna diventa rossa da
sola; 23 prove funzionali su DB usa-e-getta (il link condiviso che non
muore, lo scaffale che non entra nel totale, «ricaricare a UNO non
cancella la memoria dei quattro», la ronda che tace); giro visivo via
CDP a 375/360/320px nei due temi col rifornimento esercitato dal vivo.
IN PRODUZIONE basta il deploy: la colonna nasce da sola e la scopa la
riempie al primo avvio (misurato su 888 annunci veri in locale), nessuna
leva, nessuna rotta nuova, nessuno stato nuovo. DA GUARDARE al primo
giro: che il badge sia spento ovunque — è giusto così, si accende solo
su chi rifornisce da qui in avanti — e il primo venditore vero che
rifornisce (che il post di canale perda la ✅ e l'evento Nostr torni
`active`).

Le anteprime dei link (ago 2026): un link di Barattolo su Telegram,
WhatsApp o in un DM Nostr arrivava come una card vuota col titolo
generico — i crawler non eseguono JavaScript, e qui titolo, prezzo e
foto nascono tutti da fetch. Adesso le cinque rotte che servono
miniapp.html ci infilano in testa i loro meta Open Graph. La regola che
ha aperto il cantiere, e la sola da non ammorbidire: RIMOSSO E
REVISIONE non raccontano niente di sé — un rimosso in un'anteprima
cachata e inoltrata è lo scudo anti-resurrezione bucato da un'altra
parte. Il VENDUTO invece ha la sua card vera (decisione di Andrea: è
uno scaffale vuoto, non un annuncio che non c'è — il link non muore con
le scorte), col «✅ Venduto» in testa alla descrizione perché non
menta, e col confine tenuto allineato a quello di `/api/listings/{id}`
da una prova apposta. Vedi Architettura, «LE ANTEPRIME DEI LINK», per
le altre due cose da non rovesciare (i meta in cima a 900 KB di pagina,
l'escaping in attributo) e per la scelta dell'immagine coi suoi tre
ripieghi.
Col cantiere è arrivato `_fmt_eur` e la regola che un euro si scrive in
un modo solo in tutta l'app (il client lo faceva già: il server era
l'unico fuori riga) — coi tag NIP-99 fuori apposta, che lì il punto
decimale è la specifica. La sentinella che lo sorveglia ha preso tre
casi che il censimento a mano aveva mancato, perché scrivevano «EUR» a
parole invece del simbolo. Poi la stessa medicina ai SATS, che di
formati ne avevano quattro: 33 cifre riportate su `_fmt_sats`, e
soprattutto `_fmt_sats` che NON SOLLEVA PIÙ — un formattatore che alza
le mani dentro il `try/except` di una notifica non fa un errore, fa
sparire l'allarme, ed era successo davvero sull'avviso di pagamento
rifiutato (`importo_invoice` torna `None` sulla bolt11 illeggibile).
Collaudate: 78 prove nuove (1629 verdi), e quella sul rimosso è
ESEGUIBILE e non una sentinella sulla forma — passa da un database vero
e il titolo si cerca nell'HTML che esce. TORTURATE con ventuno mutazioni
del codice, una per riga sorvegliata (stato tolto dalla WHERE, rimosso
rimesso dentro, venduto tolto fuori, «✅ Venduto» che sparisce, euro
tornato al punto in tre modi diversi, `_fmt_sats` che torna a sollevare
sul `None`, sats scritti a mano — anche nascosti nella piega di una
stringa spezzata —, virgola inglese rimessa, escaping a quote=False,
rotta tornata al file nudo, francobollo scambiato col pieno, conto del
negozio senza stato, tg_id nell'anteprima, meta prima del charset,
cintura che rilancia, ripiego che appende in fondo, ritorno alla
modalità testo):
ognuna diventa rossa da sola, e la prima ne fa rosse cinque insieme. Più
il giro dal vivo sul server locale simulando gli User-Agent veri di
Telegram, WhatsApp, Facebook, Slack e dei client Nostr con la loro
lettura parziale — tutti vedono la stessa card, l'ultimo meta cade al
byte ~1300, e l'og:image sta dentro i limiti di tutti e tre —, la
verifica che la pagina esca IDENTICA al file byte per byte, e
l'escaping provato end-to-end con una riga usa-e-getta dal titolo
cattivo (virgolette, `<script>`, apostrofi: 13 meta interi, nessun tag
spezzato, e la riga poi cancellata), più il venduto vero e un listino
in euro guardati dal vivo («✅ Venduto · 50 sats (≈ 0,03 €)»,
«40,00 € (≈ 70.764 sats)»).
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva, nessuna rotta nuova. DA FARE AL PRIMO DEPLOY, ed è il
pezzo che in locale non si può fare: `python anteprime.py
https://barattolo.store /annuncio/N` e poi le card vere in chat, con
URL USA-E-GETTA — un annuncio di prova da rimuovere subito dopo —
perché Telegram e WhatsApp cachano a lungo e dal nostro lato non si
bustano; e verificare col rimosso VERO che la sua card sia quella
generica e col venduto VERO che porti il suo «✅ Venduto».
Tre correzioni dall'audit (ago 2026), tutte e tre sulla stessa idea:
un annuncio può raccontare cose a gente che Barattolo non l'ha mai
aperto. M1, CHI SI FINGE BARATTOLO — la card brandizzata è un link
autentico sul nostro dominio dove i testi li sceglie chi pubblica:
voce nuova nel prompt, VIETATO a chi SI RIVOLGE al lettore a nome
della piattaforma e DUBBIO a chi si intesta solo un ruolo, con le due
contro-regole («nominare è lecito», «raccontare come funziona pure»)
che sono la metà delicata, e il rifiuto che ora dice cosa si è
sbagliato invece dell'elenco di armi e droghe. M2, L'OG:IMAGE VERSO
HOST DI TERZI — l'URL remoto di chi pubblica su Nostr non ci finisce
più: diventava la campana di chiunque veda un'anteprima, ed è
sostituibile a card già in giro. B6, L'AVVISO CHE SPARIVA IN SILENZIO —
corriere e tracciamento scappati in `segna_spedito` e `reso_spedito`.
Vedi le voci loro in Architettura per i perché.
Collaudate: 53 prove nuove (1683 verdi, erano 1630) — quelle di B6
ESEGUIBILI sulle funzioni vere, quelle di M1 sulla forma del prompt
più la sentinella che il lotto non se ne sdoppi uno suo — e
QUATTORDICI mutazioni del codice, una per riga sorvegliata: ognuna
diventa rossa da sola. Due difetti trovati dalle prove e non dalla
lettura del codice: «finto» non è una declinazione di «finge» (la
lista dei motivi non lo prendeva, e «finto servizio clienti» cadeva
nel ramo dei servizi), e l'ordine dei due rami di `messaggio_rifiuto`,
che scambiato manderebbe a un impostore il messaggio di garbo.
E IL COLLAUDO COL MODELLO VERO HA PAGATO SUBITO (ago 2026, secondo
giro): 14/15, con un FALSO POSITIVO — la bici la cui descrizione
spiega l'escrow, bocciata perché «non descrive l'oggetto in vendita».
La causa era la formulazione, non il modello, e la storia con la cura
a tre gambe sta nella voce sua in Architettura; il caso è rimasto nel
collaudo come regressione permanente, con una gemella accanto. È
esattamente il motivo per cui quel collaudo esiste: nessuna prova di
CI l'avrebbe visto, e in vetrina si sarebbe visto solo quando un
venditore onesto avesse protestato.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva. DA FARE PRIMA DEL DEPLOY, ed è il pezzo che in locale
non si può fare perché vuole la chiave vera: `python
collaudo_impersonazione.py` sul VPS — se un OK atteso finisce in
VIETATO è un falso positivo, cioè annunci legittimi bloccati, e il
prompt si corregge A MANO. IMPERFEZIONE DICHIARATA che resta:
l'immagine remota la scarica comunque il browser di chi APRE la
scheda (è la regola della vetrina, dichiarata). Il titolo nudo dei
solleciti è invece chiuso — vedi più sotto, ed erano quindici siti.
Nessuna riga si cancella senza aver chiesto a LNbits (ago 2026,
trovato di striscia rispondendo a un'altra domanda — «al pagamento il
compratore riceve una notifica?» — e portato avanti prima di tutto il
resto): il reaper buttava via gli ordini 'creato' scaduti con un
DELETE secco, e con loro il `payment_hash`, cioè l'unico filo verso un
pagamento che nessuno aveva mai verificato. LA DIAGNOSI HA CAMBIATO LA
DOMANDA, ed è la parte da tenere: la fattura NON sopravvive alla riga
(muore a 900s, la riga a 1800s) — quindi il pericolo non era «paga
dopo la cancellazione» ma «paga prima, nessuno guarda, la riga sparisce
coi sats dentro». MAI SUCCESSO in produzione, verificato prima di
toccare qualunque cosa incrociando gli incassi di LNbits coi
payment_hash noti (zero orfani; il metodo è nella voce in
Architettura, e da SQL non si può fare). La cura è la regola delle
lapidi arrivata fino in fondo: il reaper i 'creato' non li tocca più e
a guardarli — solo a fattura morta — c'è `controlla_abbandonati`
nell'orologio, che è async e a LNbits ci può parlare. Vedi
Architettura, «E NESSUNA RIGA SI CANCELLA SENZA AVER CHIESTO A
LNBITS», per il fail-open nel verso giusto, il rilancio pagato che non
entra in gara e le due conseguenze — collaudata con 14 prove nuove
(1707 verdi), una sentinella ROVESCIATA e nove mutazioni del codice
una per riga sorvegliata, di cui la nona ha smascherato una sentinella
che non poteva fallire. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna migrazione, nessuna leva. DA GUARDARE al primo giro:
nel journal non deve comparire niente — un «⚠️ Ordine #N pagato e mai
verificato» vuol dire che il caso è appena successo per davvero, e
quello è il momento di guardare l'ordine, non la funzione.
La ricevuta del compratore (ago 2026, il giorno dopo — chiude
l'imperfezione che quel cantiere aveva dichiarato): chi paga riceve una
notifica appena i sats sono in cassaforte, e la riceve SEMPRE, non solo
quando l'accredito arriva dall'orologio. Il toast in-app se n'è andato:
durava tre secondi e non lasciava niente da ritrovare. La decisione che
governa il resto è «sempre» invece di «un ramo per l'orologio»: costa un
messaggio in più nel caso normale e in cambio la ricevuta vive nel
FUNNEL (`_incassa_ordine`), quindi tutte e tre le strade dell'accredito
la ereditano — e anche quelle di domani. La coda segue la STRADA SCELTA
o si dice il falso a metà degli ordini, e sul digitale non si promette
mai la conferma, che lì le finestre corte scattano da sole. Vedi
Architettura, «LA RICEVUTA DEL COMPRATORE».
Collaudata: 42 prove nuove (1748 verdi, erano 1706) — il giudice puro
strada per strada più `_incassa_ordine` chiamata DAVVERO su un database
vero, col titolo cattivo e i grassetti che restano pari — e DODICI
mutazioni del codice una per riga sorvegliata (ricevuta tolta, titolo
nudo, escape prima del troncamento, digitale che promette la conferma,
i tre rami della coda tolti a uno a uno, punto passato come testo,
toast rimesso, destinatario sbagliato, coda scritta a mano, e la
ricevuta traslocata sul poll — la regressione che rimetterebbe muto
l'orologio): ognuna diventa rossa da sola. Più il giro DAL VIVO sulle
sette strade con un database usa-e-getta — le cinque code, il titolo
con un «<» dentro, `controlla_abbandonati` e il riacciuffo di
`controlla_annullati`, che sono i due casi per cui il cantiere esiste —
e il controllo nel browser vero che il toast non si accenda più e
l'ordine si apra lo stesso. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna migrazione, nessuna leva, nessuna rotta. DA GUARDARE
al primo giro: la prima ricevuta vera dentro Telegram — e soprattutto
che chi compra un CODICE non si veda promettere un pacco.
Il titolo nudo nelle notifiche (ago 2026, subito dopo: la stessa
famiglia di B6, chiusa). Il conto vero era **quindici siti** e non i
«quattro solleciti fratelli» che questo file dichiarava — il polso 🛒
ai moderatori, quattro solleciti su sei, e altri otto che solo un
censimento ha tirato fuori; il più grave è il 🧊 di un pagamento
INCERTO, cioè l'avviso che dice che dei sats possono essere usciti
davvero. La lezione è quella: l'elenco a memoria di un buco dichiarato
rimpicciolisce, e a contare dev'essere una prova che guarda il file.
Una regola sola — si scappa all'assegnazione — più l'ultima rete in
fondo al tubo, che è la parte che risponde al danno vero: la risposta
di Telegram non la guardava nessuno, quindi il 400 «can't parse
entities» finiva nel nulla; ora il messaggio si rimanda SPOGLIO e la
cosa si STAMPA. Vedi Architettura, «IL TITOLO NUDO NELLE NOTIFICHE»,
per la strada scartata (l'escape dentro il polso, che avrebbe fatto
vivere la stessa variabile in due regimi) e per il rovescio — il 404
del carrello, dove scappare sarebbe stato il bug.
Collaudato: 36 prove nuove (1784 verdi, erano 1748) — in testa il
CENSIMENTO, che non è un elenco ma una passata su tutte le funzioni
del file, così il sollecito nuovo di domani entra nel conto da solo —
e NOVE mutazioni una per riga sorvegliata, di cui una ha smascherato
una sentinella che non poteva fallire (il `print` del collaudo la
teneva verde). Più il giro DAL VIVO con un titolo ostile
(`Cuffie <b>AKG</b> & "K371" <script>`) su ricevuta, polso e tre
solleciti: tutti scappati, `<b>` pari, e l'evento NIP-99 che tiene
giustamente il titolo grezzo. IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna leva, nessuna rotta. DA GUARDARE al primo giro: nel
journal non deve comparire nessun «⚠️ HTML rifiutato da Telegram» — se
compare, quella riga dice il sito da scappare alla fonte.

I timbri degli avvisi periodici (ago 2026, caso dal campo: il
termometro delle sottocategorie arrivato TRE volte in cinquanta minuti,
agli orari dei tre deploy di quel lunedì). Il timbro viveva in un
globale: un globale muore col processo, quindi non era un gate ma una
deduplica valida quanto il processo — e questo file prometteva «al più
due volte quel lunedì», che non era garantito da niente. Ora sta nella
tabella `timbri`. Erano TRE le funzioni con lo stesso ancoraggio, e la
peggiore non è quella che si è vista: `sollecita_revisioni` contava
24 ore da un globale SENZA nemmeno il gate del calendario — due deploy
a un minuto di distanza e suonava due volte. Più la riga nel journal su
tutti e tre, che era il secondo difetto: l'invio non si trovava da
nessuna parte, quindi un avviso che parte troppo non si poteva neanche
diagnosticare. Vedi Architettura, «I TIMBRI DEGLI AVVISI PERIODICI»,
per il fail-open nel verso del parlare e per i quattro gate in RAM che
RESTANO col loro perché.
Collaudato: 29 prove nuove (1814 verdi, erano 1785) — in testa quella
ESEGUIBILE che simula tre deploy (tre ambienti diversi, un database
solo) e chiede una notifica sola — più NOVE mutazioni una per riga
sorvegliata, ognuna rossa da sola. Più il giro DAL VIVO con tre
subprocess veri sullo stesso file di database: una notifica, la riga di
journal sul primo giro, e la tabella con dentro il suo timbro. E la
migrazione provata su una COPIA del database esistente: una tabella in
più, nessuna persa, `timbri` vuota.
IN PRODUZIONE basta il deploy (la tabella nasce da sola). ⚠️ DA SAPERE:
oggi è lunedì e la tabella nasce vuota, quindi il primo riavvio dopo il
deploy manda UN'ULTIMA notifica del termometro — dal secondo in poi
silenzio. Non si semina il timbro apposta: sarebbe un trucco una-tantum
dentro una migrazione, e su un'installazione nuova salterebbe il primo
lunedì per davvero.

Farsi trovare (ago 2026): Barattolo diventa indicizzabile. Indirizzi
parlanti `/annuncio/{id}-{slug}` e `/negozio/{chi}-{slug}` (i vecchi non
muoiono e non redirigono: rispondono 200 col canonical), un `<title>`
per pagina — che ROVESCIA una regola scritta in CLAUDE.md —, le card e
le piastrelle diventate collegamenti VERI, 27 pagine `/categoria/{slug}`,
il contenuto pre-renderizzato nel corpo dentro il «cartello», più
`robots.txt`, `sitemap.xml` (~900 URL) e il JSON-LD Product/Offer col
prezzo in BTC, che è una conversione esatta e non un cambio inventato.
Vedi Architettura, «FARSI TROVARE», per i tre regimi di escape, la
regola robots-vs-noindex e le imperfezioni dichiarate.
Collaudato: 1995 prove verdi (211 nuove) e — la parte che conta —
QUINDICI MUTAZIONI del codice, una per sentinella, che diventano rosse
tutte e quindici: card senza `position:relative`, bottoni rimessi dentro
l'`<a>`, `preventDefault` dopo `openDetail`, `navSpingi` all'atterraggio,
la chiamata tolta da `avviaVetrina`, la regex ancorata col `$`, lo spacco
del negozio tolto, `html.escape` dentro `_ld`, INNER JOIN al posto del
LEFT, un rimosso rimesso nella WHERE, «Disallow: /», `int(aid)`, il
titolo crudo, la lampo nella query, il canonical su una pagina
deindicizzata. Più il confronto PIXEL prima/dopo su cinque viste
(vetrina chiara e scura, negozio, Sfoglia chiara e scura) con un
worktree al commit precedente: **identiche byte per byte**, che è la
prova vera del «zero pixel di differenza» sulla card ristrutturata. E
`anteprime.py`: le anteprime social non cambiano, tutti e cinque i
crawler vedono la stessa cosa e l'ultimo meta sta al byte 1868.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuna leva. `sw.js` passa a v4 perché `offline.html` (in dispensa) ha
guadagnato il suo noindex. DA FARE DOPO IL DEPLOY, ed è il pezzo che in
locale non si può fare: inviare la sitemap a Search Console, e tenere
d'occhio la BANDA la prima settimana (~820 MB per passata completa: vedi
la voce del costo). DA GUARDARE: che `/robots.txt` risponda 200 sul
dominio vero, e che la prima card social condivisa dopo il deploy sia
identica a prima.

L'offerta si porta dietro i pezzi (ago 2026): il venditore accettava un
prezzo unitario a quantita' INDETERMINATA e poteva ritrovarsi a vendere
tutto lo stock alla cifra scontata, scoprendolo con l'ordine — e il
compratore che aveva scelto tre pezzi li perdeva per strada. Ora la
quantita' scelta accanto ad «Acquista» viaggia con l'offerta e comanda
nei quattro percorsi del conto. La cifra resta l'UNITARIO (si confronta
col listino, e un totale romperebbe la divisione a ritroso di
`_righe_ordine`) e le due facce si dicono INSIEME ovunque i pezzi siano
piu' di uno. Nello stesso giro il foglio si rifa': tre pillole senza
controvalore, toggle €/₿ che governa la lettura, la riga «Offri 120.000
sats per 3 pezzi (40.000 sats al pezzo)» al posto del totale incompleto
di prima — col TOTALE davanti, che e' quello che si vuole sapere per
primo —, lo stepper della quantita' dentro il foglio (che scrive nella
STESSA variabile del gemello: due numeri divergenti sono il difetto che
il cantiere toglie), la ✕ al posto di
«Annulla», e il tasto offerta che porta la quantita' come il suo
gemello. Vedi Architettura, «L'OFFERTA SI PORTA DIETRO I PEZZI», per la
decisione unitario-vs-totale coi suoi tre perche', per l'ordine delle
guardie che NON si tocca (spostare il blocco dell'offerta sopra la
ripresa e' una regressione, non una pulizia) e per il corner dichiarato
del client che chiede piu' pezzi dell'accordo. Collaudata: 2095 prove
verdi (56 nuove — il giudice puro, l'aritmetica con la divisione a
ritroso esatta, i quattro percorsi, l'ordine delle guardie, il gemello
client, il foglio, lo stepper e le due superfici del tasto) piu' SEDICI
mutazioni del codice una per riga sorvegliata, ognuna rossa da sola —
e due sentinelle sono state riscritte proprio perche' la tortura le ha
trovate VACUE (cercavano una stringa che vive anche altrove); e il giro
vero su database usa-e-getta col server acceso: offerta per 3 pezzi →
accordo → il client che chiede 5 e ottiene 3, preventivo == compra al
sat (215.000), unitario esatto a ritroso, stock sceso a 2 col 400
onesto e l'offerta ancora viva, offerta «di ieri» che si comporta come
allora, 99 pezzi limati a 2. Piu' gli screenshot a 320 e 375px nei due
temi (testata del foglio senza collisioni, barra coi due tasti a 3
pezzi, pannello del venditore, pagina d'acquisto). IN PRODUZIONE basta
il deploy: la colonna nasce a 0 — cioe' quantita' non dichiarata per
tutte le offerte gia' aperte — e non c'e' nessuna leva. DA GUARDARE al
primo giro: la prima offerta vera con piu' di un pezzo dentro Telegram,
e che il venditore legga nella notifica del bot sia il totale sia il
fatto che accettare non blocca niente.

L'AI segnala, non decide (ago 2026, giro urgente dal campo: un
venditore vero fermo). «Sat's Oil 🫒 GENESIS EDITION» bloccato per
impersonazione col motivo «il nome appare progettato per confondere
con Barattolo (associando "sat")» — su un mercatino che incassa in
satoshi. Due difetti e un cambio di rotta: la voce del prompt ora dice
che i sats sono la MONETA e che una somiglianza di NOME non è mai un
motivo; dice anche cosa fare quando il testo non c'è (lo stesso motivo
sosteneva che titolo e descrizione mancassero, mentre il titolo
c'era: il modello deduceva dal non detto); e la lista
`PAROLE_IMPERSONAZIONE` aveva un buco separato, «confondere», per cui
al venditore era arrivata pure la lista delle armi e delle droghe.
IL CAMBIO DI ROTTA (decisione di Andrea): un VIETATO dell'AI non basta
più a bloccare — ferma solo su QUATTRO famiglie (armi, droghe, sesso a
pagamento e sfruttamento, documenti e credenziali), tutto il resto va
in REVISIONE, dove non è pubblico e decide un umano. Vedi Architettura,
«L'AI SEGNALA, NON DECIDE», per l'elenco completo, per cosa ne è FUORI
e perché (refurtiva, contraffazione, farmaci, animali protetti: hanno
tutti una lettura innocente che il modello può aver frainteso), e per
la ragione che rende la scelta poco rischiosa — in revisione
l'annuncio non è pubblico, quindi il costo è la coda e non il rischio.
MISURATO, non stimato: il collaudo col modello vero dà **18/19 con
ZERO falsi positivi** (i tre casi nuovi sui sats passano tutti; l'unico
fuori posto era «Assistenza Barattolo — supporto agli utenti», atteso
VIETATO e risposta DUBBIO — un «caso cattivo passato», il tipo meno
grave, che ora finisce comunque in coda. L'atteso è stato rimesso a
DUBBIO, che è quello che il prompt insegna: col prossimo giro il conto
torna 19/19), e `stima_coda_moderazione.py` sui rifiuti
veri di 30 giorni dice che la coda passa da **7 a 14, cioè 0,2 annunci
in più al giorno**. 2171 prove verdi, nove mutazioni tutte rosse, e UNA
prova che ha cambiato lato: chiedeva che «VIETATO: impersonazione»
fosse un rifiuto secco, cioè certificava il comportamento che ha
fermato il venditore. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna migrazione, nessuna leva nuova — e `MODERAZIONE_REVISIONE`
spenta resta il freno d'emergenza che rimette il binario di ieri.
DA RIFARE quando il volume cresce: la stima della coda, che è il solo
numero su cui questa scelta poggia.

Il foglio dell'offerta, rifinito dal campo (ago 2026, tre giri): il
campo del prezzo è sempre visibile e modificabile — le pillole lo
riempiono, non lo nascondono — e la pillola accesa si DEDUCE dalla
cifra invece di ricordarsi, o dopo un ritocco direbbe il falso; il
campo dice «al pezzo» mentre si digita (solo coi pezzi >1: chi ne
vuole tre ragiona sul totale e rischia di scrivere 120 intendendo il
totale mentre ne offre 360); il minimo non è più un cartello
permanente ma un avviso che compare solo sotto soglia, e lì sparisce
anche la riga del totale — due righe dove ne serve una sola. Più la
tastiera, che non copre più quel che si scrive: vedi Architettura, «LA
TASTIERA NON COPRE PIÙ QUEL CHE SI SCRIVE», per il perché non basta
`100dvh`, per il difetto introdotto e visto sullo screenshot (i fogli
CHIUSI che rientravano in vista) e per l'ONESTÀ SULLA VERIFICA — in
headless lo scatto non si riproduce né si esclude, quindi invece di
scommettere su una causa sola si sono tolte tutte quelle plausibili.
IN PRODUZIONE basta il deploy. DA GUARDARE dal telefono: che lo scatto
sia sparito nella PWA — se sopravvive, il sospetto successivo è la
`max-height` che cambia durante l'animazione.
Il compratore ritira un'offerta (ago 2026, caso vero dal campo): chi ne
manda una per sbaglio non doveva più aspettare 48 ore o chiedere al
venditore di rifiutarla — e intanto non poteva nemmeno rifarla giusta,
che la guardia `attive` glielo impediva. Rotta sua
(`POST /api/offerte/{id}/ritira`), stato `ritirata` che è una lapide,
da 'proposta' e da 'accettata' ma mai da 'controproposta' (lì c'è già
«Rifiuta»). Le decisioni di Andrea: il venditore lo sa SEMPRE, e il
tetto dei 3 tentativi conta anche le ritirate — non contarle aprirebbe
uno spam illimitato, e il ritiro non toglie niente perché oggi chi
sbaglia brucia comunque il tentativo e in più aspetta due giorni. Vedi
Architettura, «IL COMPRATORE RITIRA», per il perché non è un'azione di
`rispondi_offerta` e per la correzione che il cantiere ha fatto al
proprio piano: a bloccare è l'ordine VIVO e non l'esistenza del numero,
o si apre un vicolo cieco da cui nessuna azione dell'utente esce.
Collaudato: 54 prove nuove (2246 verdi, erano 2192) e — la parte che
conta — DODICI MUTAZIONI del codice, una per riga sorvegliata (il CAS
tolto, la guardia di proprietà fuori dalla WHERE, il 404 rimesso, la
guardia dell'ordine riportata alla forma secca, il gate della scadenza
tolto, la controproposta ammessa, `'ritirata'` in un secondo posto, un
`UPDATE ordini` infilato nel ritiro, la scadenza non azzerata, il
titolo nudo, il bottone tolto dal client, il tetto hardcodato): ognuna
diventa rossa da sola. Più il giro dal vivo sul server locale — il
venditore respinto, l'anti-oracolo verificato sul database vero
(altrui e inesistente rispondono identico), il ritiro che libera
`attive` e permette di riprovare SUBITO, l'ordine vivo che blocca e la
lapide che non blocca, e gli ordini immobili prima e dopo — e il gesto
nel browser coi due confirm e zero errori JS. IN PRODUZIONE basta il
deploy: nessuna colonna, nessuna migrazione, nessuna leva.

Gli ordini si leggono meglio (ago 2026, due giri): gli ANNULLATI
spariscono dalla lista — la lapide resta nel database, dove serve alla
macchina — e i VERBI seguono il tempo dell'affare, con la cifra che
ognuno ha davvero mosso (totale a chi paga, netto a chi incassa) e
nessuna cifra sul rimborso, dove nessuno ha comprato e nessuno ha
venduto. Nel DETTAGLIO: via la modalità, che era già scritta due righe
sotto; la spedizione torna un inciso accanto alla cifra (muto quando la
promessa del negozio l'ha resa gratis, che «di cui 0» non dice niente);
e i testi parlano a chi legge — il compratore non si sente più chiamare
«l'acquirente» a casa sua. Vedi Architettura, «LE LAPIDI NON SI VEDONO»
e «IL DETTAGLIO PARLA A CHI LEGGE», per le decisioni di Andrea (dove
finiscono gli annullati, quale cifra per quale lato, la strada scartata
del verbo nel dettaglio) e per le terze persone che RESTANO tali.
Collaudati: 2433 prove verdi (37 nuove) e DICIASSETTE mutazioni del
codice, una per riga sorvegliata — annullati rimessi in lista, `orders`
riletto in una delle tre righe, verbo che scavalca il giudice, netto
ricopiato a mano, inciso che parla a spedizione gratis, terze persone
girate a tutti e due i lati —, ognuna rossa da sola. Più il giro dal
vivo via CDP a 390px nei due temi e dai due lati, con i casi che lo
screenshot non copre verificati a parte (spedizione gratis, rimborso,
sola spedizione su una riga). IN PRODUZIONE basta il deploy: nessuna
colonna, nessuna rotta, nessuna leva — solo client.

Chi ha pagato può bussare, e la disputa si vede (ago 2026): il bottone
«🔔 Ricorda al venditore di spedire» sull'ordine pagato e non ancora
partito — 48 ore dal pagamento (24 sul codice online), uno al giorno,
tre in tutto, poi resta la disputa — col testo che è un promemoria e
non un rimprovero, perché chi non ha spedito ha quasi sempre solo
avuto una giornata storta. I contatori dell'automatico non si toccano:
colonne sue e ancora `creato`, o chi bussa spesso allontanerebbe il 🧊
ai moderatori. E «⚠️ C'è un problema — apri disputa» prende la forma
di tutti gli altri col rosso velato dei ponti: era un testuale
sottolineato e in fila coi due blocchi colorati spariva. Vedi
Architettura, «E CHI HA PAGATO PUÒ BUSSARE PRIMA» e «E L'USCITA DI
SICUREZZA HA LA STESSA RICETTA». Più la prima riga del riquadro verde,
che ora dice un GESTO e lo gira a chi legge («Hai depositato i sats» /
«Hai il pagamento in garanzia»). Collaudati: 2485 prove verdi (52
nuove — l'endpoint girato DAVVERO su sqlite in memoria, con l'ambiente
POVERO che esplode con NameError se un domani imparasse a toccare i
sats) e DICIOTTO mutazioni del codice, una per riga sorvegliata,
ognuna rossa da sola; più il giro dal vivo sul server locale (le tre
finestre, la pausa, il tetto, l'anti-oracolo verificato sul database
vero) e gli screenshot dei quattro bottoni in fila nei due temi.
IN PRODUZIONE basta il deploy: le due colonne nascono a 0 e le quattro
leve hanno il default nel codice. DA GUARDARE al primo giro: il primo
promemoria vero dentro Telegram — che al venditore arrivi UN messaggio
e che si legga come un promemoria.

La coda degli ordini fermi, e la riga per chi ha pagato (ago 2026): il
🧊 ai moderatori era un messaggio Telegram e basta — dopo, un ordine
coi sats in cassaforte non compariva in nessuna lista e si raggiungeva
solo sapendone il numero; e il compratore veniva avvisato UNA volta
sola, al primo squillo. Adesso c'è la sezione «⏸ Ordini fermi» nel
pannello admin (regola in una frase: «i sats sono in cassaforte e
nessuno si muove da 10 giorni», il complemento dei terminali) e una
riga permanente nell'ordine di chi ha pagato. Nessun automatismo
nuovo: la coda LEGGE e basta, la riga racconta, e i sats continuano a
muoverli solo le persone. Vedi Architettura, «E DOPO IL 🧊 C'È UNA
CODA», per l'invariante della soglia, la regola dello zero sulle
ancore e le due popolazioni scoperte trovate costruendola (il `locked`
con `consegna_scelta=''` e lo `shipped` con `spedito_il=0`, che non
ricevono nessun promemoria e nessun 🧊). Incluso, su decisione di
Andrea, il buco latente che la coda avrebbe reso un vicolo cieco: il
pannello del moderatore sul caso incagliato.
Collaudato: 2674 prove verdi (73 nuove — l'endpoint girato DAVVERO su
un database gemello, col dump di `ordini` identico prima e dopo) e
VENTUNO MUTAZIONI del codice una per riga sorvegliata, ognuna rossa da
sola; la tortura ha trovato due sentinelle mie che non potevano
fallire, riscritte. Più il giro dal vivo sul server locale, che ha
mostrato la coda coi due `locked` veri fermi da 24 e 22 giorni,
entrambi «🔕 mai sollecitato» — cioè la popolazione scoperta si è
presentata al primo giro — il 403 al non-moderatore, la riga nell'ordine
del compratore nei due temi e il pannello del caso incagliato, con zero
errori JS e il database di collaudo intatto.
IN PRODUZIONE basta il deploy: nessuna colonna, nessuna migrazione,
nessuno stato nuovo, e la leva ha il default nel codice. DA GUARDARE
al primo giro: chi c'è già dentro la coda — se compare un ordine che
nessuno ha mai sollecitato, quello è il caso per cui il cantiere
esiste.

Il mono sconta, punto (12 ago 2026, decisione di Andrea che ROVESCIA
PER INTERO il «il mono non sconta mai» del 6 ago): lo sconto carrello
vale su ogni acquisto — tre copie dello stesso articolo dalla scheda
sono tre pezzi, una soglia a valore superata è superata anche con un
oggetto solo, tutti e due i criteri e tutte e due le valute. Il motivo:
è quello che la gente si aspetta (Andrea ci si è stupito due volte in
due giorni), e l'invito del carrello diceva già «✅ Sconto nel conto»
su un carrello a una riga che poi non scontava — la mezza regola era
una bugia in vetrina, e la mezza via «carrello sì, scheda no» è quella
SCARTATA: le due porte sono lo stesso endpoint, e costruire la
differenza farebbe dipendere un prezzo da quale JSON manda il client.
Vedi Architettura, «IL MONO SCONTA, PUNTO», per il censimento completo:
i quattro chiamanti di `_sconto_pacco`, la divisione a ritroso che
riaggiunge `sconto_sats` nelle sue TRE copie (`_righe_ordine`, la
ripresa, la riga client) sorvegliate dal CENSIMENTO
`prove_divisione_a_ritroso`, `articolo_sats` diventato NETTO anche sul
mono, il controllo «mono scontato» della ronda sostituito da due
invarianti veri (i controlli salgono a 16), i quattro testi-antidoto
riscritti con le sentinelle rovesciate, e la campagna una-tantum
`avvisa_sconto_su_mono` ai venditori con la regola già accesa (timbro
globale in `timbri`, il testo dice la LORO regola e come spegnerla).
Collaudato: 2830 prove verdi in CI (erano 2793 prima del cantiere, con
le rovesciate e le estese 2→4 percorsi), DODICI MUTAZIONI una per riga
sorvegliata — ognuna rossa da sola, e una ha smascherato una mutazione
che sbagliava bersaglio (il replace prendeva la SELECT identica di
`_compra_set`: la tortura va mirata quanto le sentinelle) — più il
collaudo eseguibile su DB usa-e-getta (117 verdi, con LNbits VERO e le
bolt11 decodificate al sat): LA PROVA REGINA preventivo == compra sul
mono scontato al filo della soglia nei due criteri e nelle due valute,
l'identità di bilancio riletta dal database, la divisione a ritroso
esatta anche sul ramo della RIPRESA, il digitale che sconta, la lampo
che fa scendere sotto soglia, il cambio muto senza 503 nuovi, la
regola cambiata fra preventivo e acquisto nei due versi, la ronda che
tace e la regressione del venditore senza regola. Più il giro visivo
via CDP a 375px: pagina Paga e paySheet con la riga «Sconto carrello»
e i totali che quadrano a mano (30.000 → −3.000 → 27.000), il cassetto
e la riga del negozio coi testi nuovi.
IN PRODUZIONE basta il deploy: ZERO colonne, ZERO migrazioni, ZERO
leve nuove (`sconto_sats`/`sconto_percento` esistevano già su `ordini`
a DEFAULT 0). Al primo battito dell'orologio parte la campagna — una
volta sola, il journal nomina i destinatari — e DA GUARDARE sono: quel
journal (i ~5 negozi con la regola accesa), il primo mono scontato
vero dentro Telegram con la bolt11 confrontata su LNbits, e che la
ronda TACCIA — se «aritmetica del mono» suona, si guarda l'ordine
prima della funzione.
E lo stesso giorno L'INVITO DELLE DUE PROMESSE nella pagina Paga
(chiesto da Andrea in due tempi: prima lo sconto — nel carrello c'era,
lì no — poi la spedizione gratis, che deve parlargli uguale): pillole
affiancate in una fila, ognuna col suo stato — «Ancora N → …» sotto
soglia, il verde «nel conto» quando scatta — coi numeri del SERVER, la
cifra a valore da `cifraSoglia`, il cambio muto detto invece che
taciuto e gated sulla valuta di OGNUNA (chiuso il bug preesistente del
flag combinato che sospendeva una spedizione in sats per colpa di uno
sconto in euro). Il verde della spedizione convive con la riga
«gratuita» del conto: il perché e il cosa, deciso a schermo. Più i
badge di «Altri oggetti» a cifra nuda («di articoli» resta dov'è una
misura), e la posizione dei badge sopra il bottone RICONFERMATA
MISURANDO dopo un tentativo vero di rovesciarla (il difetto dello
sticky torna, fotogramma agli atti — vedi la voce). Verificato con 9
sentinelle nuove (2838 verdi) e gli screenshot 320/375 × chiaro/scuro,
sotto/sopra soglia e stato misto.
E il ritocco del CARRELLO (12 ago 2026, sempre quel giorno): il
sottotitolo dice il perimetro («articoli dello stesso venditore»)
invece del modello, e testata+badge restano appiccicati in cima
mentre si scorre — misurato PRIMA di lasciarlo, com'era chiesto:
137px a 375 (17%) e 158px a 320 (19%) collo stato più alto, sotto i
178 (23%) del precedente scartato in «Altri oggetti». 5 sentinelle
nuove (2843 verdi), screenshot chiaro/scuro in cima e a metà scroll.
E LO STEPPER NELLA PAGINA PAGA (12 ago 2026, a chiudere la giornata):
il ± accanto al titolo dell'articolo — l'invito dice «ancora 1 pezzo»
e il pezzo si aggiunge lì. Ogni tocco rifà il preventivo; l'anti-race
è la riassegnazione di `acqDati` sulla guardia che c'era già (mai un
debounce), il velo d'attesa è RITARDATO di ~180ms (secco lampeggiava:
la riserva di Andrea, guardata a schermo con 800ms di latenza
artificiale), l'errore su un ± ripiega sull'ultimo conto buono invece
di buttare la pagina, e `setQta(0)` sincronizza la scheda al ritorno
(il difetto trovato dal vivo: l'indietro non ri-renderizza). 12
sentinelle nuove (2855 verdi), la raffica da 5 tocchi provata dal
vivo — vince l'ultima chiesta — e il limite dello stock in silenzio,
come nella scheda. Vedi «LO STEPPER NELLA PAGINA» nella voce della
pagina d'acquisto.

Il punto di ritiro diventa il default, e il campo diventa un bottone
(ago 2026, cambio di rotta di Andrea in due tempi: prima «il default
è il punto — default e "Consigliato" devono dire la stessa cosa», poi,
davanti all'argomento-contro trovato in sola lettura PRIMA di toccare
— col campo sempre aperto la pagina diventava un modulo da compilare —
il bottone che rende il default sostenibile). Tre pezzi: la precedenza
di `viaDefault` passa a punto → casa → ritiro → digitale (la
selezionata su «entrambe» diventa la TERZA della lista); il campo a
testo libero esce dalla pagina e lo espande «📍 Indica il punto di
ritiro» — riga espansa e non foglio, stato in `acqDati.puntoAperto`,
col punto scritto la riga compatta lo mostra col «Cambia» e il campo
riapre PRECOMPILATO, e le due guardie di «Paga»/⚡ a punto vuoto
APRONO il cassetto prima del fuoco; e la pillola 🚚 della spedizione
gratis tace sulla via ritiro/codice online — rovescia il 12 ago, ed è
legato al default: chi ci sta ci è arrivato toccando, la 🎁 resta su
ogni via. Il campo dentro l'ordine non cambia di una riga, e il VARCO
MAPPA resta vero parola per parola. Vedi Architettura: «IL DEFAULT
DELLA VIA È IL PUNTO DI RITIRO», «E DAL QUINTO GIRO IL CAMPO STA
DIETRO UN BOTTONE», e il gate nella voce dell'invito delle due
promesse. Collaudato: 2875 prove verdi (13 nuove, più la sentinella
della precedenza riscritta), SETTE mutazioni una per riga sorvegliata
— precedenza rigirata, gate tolto, gate copiato sulla 🎁, apertura
dopo il toast, esc() tolto dalla riga compatta, flag perso da un
costruttore, campo non più precompilato — ognuna rossa da sola; e il
giro dal vivo via CDP sul server locale, 71 verifiche su 320/360/375 ×
chiaro/scuro: default punto con la radio terza della lista, campo
chiuso senza autofocus e senza overflow, bottone→campo→riga
compatta→«Cambia» con l'indirizzo da 120 caratteri che cede coi
puntini e il «Cambia» in vista anche a 320, «Paga» a vuoto che apre il
cassetto senza NESSUN POST, gate 🚚 nei quattro stati delle vie, zero
errori JS e zero ordini nati dal giro. La guardia NWC a punto vuoto è
coperta dalle sentinelle ma non provata dal vivo (nessun wallet nel
collaudo), dichiarato. IN PRODUZIONE basta il deploy: nessuna colonna,
nessuna leva, nessuna rotta — solo client. DA GUARDARE dal vivo dentro
Telegram: che all'apertura della pagina la tastiera NON si alzi, e il
primo ordine al punto nato passando dal bottone.

La fila delle promesse parla una lingua sola (13 ago 2026, chiesto da
Andrea in tre punti): la veste di Paga — righe a tutta larghezza —
arriva su «Altri oggetti» e sul carrello; il carrello corre la STESSA
barra di Paga (riempimento, viraggio, scattata piena e accesa: tre
«solo di Paga» rovesciati in un giro solo); e il totale della barra
del carrello mostra lo SCONTATO col lordo barrato, come l'unitario in
Paga. Le tre cose da tenere: 1) la MISURA resta al LORDO — al giudice
`statoScontoPacco` (nuovo, unico: lo chiamano badge e totale) va il
totale così com'è, o lo sconto si spegnerebbe da solo — e il netto è
solo RESA con la formula del server; con lui è morta la coda «nel
conto» (diceva di aspettare il conto perché il totale restava al
lordo, e ora scende da solo: la sentinella conta ZERO code). 2) La
barra del carrello corre coi numeri del CLIENT — gli stessi del testo
«Ancora N», nessuna pretesa nuova, la fascia del cambio dichiarata sul
giudice — sui FERRI CONDIVISI `barraPromessa`/`barreCattura`/
`barreCorri`, estratti da renderAcquisto: una seconda stesura della
corsa è il posto dove il prossimo «si anima solo la spedizione»
tornerebbe a nascondersi. 3) In «Altri oggetti» cambia SOLO la veste
(classe `.fila-promesse` sui tre contenitori, un posto solo): niente
barra e niente verde — lì la promessa è una regola, non un verdetto
sul carrello corrente — e il costo dichiarato è la coppia sempre in
colonna, ~30px in più col negozio che promette due cose.
Collaudato: 2928 prove verdi (erano 2923 prima del cantiere, con le
rovesciate — «nel conto» a zero, la tenue che non veste più nessuno,
le OTTO pillole con la chiave della corsa) e NOVE mutazioni una per
riga sorvegliata, ognuna rossa da sola — la tortura ha trovato una
sentinella che non poteva fallire (il conteggio dei chiamanti dei
ferri contava anche la chiamata COMMENTATA: riscritta sulla riga
intera, la lezione del reaper, terza volta). Più il giro CDP a
320/375 nei due temi: fill 33%/10% misurati sulle pillole vere,
scattata accesa, totale 14,89 € col 16,54 barrato (−10% al floor),
doppio verde a carrello pieno, Paga byte-per-byte uguale e zero
errori JS. IN PRODUZIONE basta il deploy: nessuna colonna, nessuna
leva, nessuna rotta — solo client. E LA VIA DEL LOCKER RESTA SENZA
SPAZI (13 ago 2026, decisione di Andrea presa sui numeri): la barra
spaziata («Spedizione a locker / punto di ritiro») era stata chiesta,
MISURATA prima di applicarla — sta su una riga a 360/375, ma a 320 va
a capo (21→43px: la colonna lì è tappata a 258px e il testo spaziato
ne chiede ~264) — e RITIRATA davanti alla misura: due righe a 320 per
due spazi non le valgono, e uniformare gli altri otto siti di prosa
della formula costerebbe più di quanto renda. Chi la riproponesse
rimisuri prima a 320, che è la larghezza dove la via si gioca la riga.

Backlog concordato: commissione minima fissa; poi post-lancio: tracking
verificato via API corrieri (che porterà la MAPPA dei punti nel
varco-mappa della pagina), escrow on-chain 2-di-3, parere legale
MiCA prima di crescere.
