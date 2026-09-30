# -*- coding: utf-8 -*-
"""
SATMARKET — CONFIGURAZIONE D'ESEMPIO

QUESTO FILE NON CONTIENE SEGRETI: e' il modello da copiare.

PRIMA VOLTA:
  1. Copia questo file e rinominalo in  config.py
  2. Compila i campi qui sotto con le TUE chiavi
  3. config.py NON verra' mai caricato su GitHub (vedi .gitignore):
     le chiavi restano solo sul tuo computer/server.
"""

# --- Telegram -------------------------------------------------------
BOT_TOKEN = "INCOLLA_QUI_IL_TOKEN_DEL_BOT"      # da @BotFather
ADMIN_IDS = []               # es. [123456789]: il TUO user id Telegram
                             # (da @userinfobot): decide le dispute e
                             # riceve gli avvisi.
                             # Piu' moderatori? Elenca gli id separati da
                             # virgola: [123456789, 987654321]. Sono tutti
                             # pari grado (nessun super-admin) e la lista
                             # si cambia SOLO qui, sul server: nessun
                             # comando dell'app o del bot la tocca.
                             # VUOTO DI SERIE (set 2026): un id d'esempio
                             # scritto qui diventava un moderatore vero di
                             # ogni config copiato da questo file, e gli
                             # avvisi partivano verso uno sconosciuto. In
                             # collaudo l'Admin finto 999 c'e' comunque, e
                             # il pannello «Stato delle leve» segna in
                             # rosso una lista vuota.

# Chi ha FONDATO Barattolo (id Telegram, come sopra). Portano il
# titolo «🏛 Fondatore» sotto il nome, messo da solo alla prima
# apertura. Non e' un traguardo che si raggiunge e nessun altro
# potra' mai ottenerlo: e' un fatto, e per questo sta qui e non fra i
# criteri. Vuoto = nessuno, che e' il default del codice.
FONDATORI = []               # es. [123456789, 987654321]

# --- Bot Telegram in ricezione (doppia cittadinanza) -----------------
# Il segreto che Telegram ci rimanda in ogni update (header
# X-Telegram-Bot-Api-Secret-Token), cosi' il webhook sa che a suonare
# e' davvero Telegram. Genera una stringa casuale (1-256 caratteri,
# solo A-Za-z0-9_-) e incollala SOLO nel config.py del server.
# Finche' resta il segnaposto, il bot resta solo-invio come prima.
TELEGRAM_WEBHOOK_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"

# --- Anthropic (ricerca AI in linguaggio naturale) -------------------
ANTHROPIC_API_KEY = "INCOLLA_QUI_LA_API_KEY"
MODELLO_RICERCA = "claude-haiku-4-5"

# --- LNbits: la "cassaforte" escrow ----------------------------------
# Usa un wallet DEDICATO a SatMarket, non quello personale!
LNBITS_URL = "https://TUA-ISTANZA-LNBITS.com"
LNBITS_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY"   # per incassare
LNBITS_ADMIN_KEY = "INCOLLA_QUI_LA_ADMIN_KEY"       # per pagare (SEGRETA!)

# --- La SECONDA cassaforte (set 2026): LNbits nostro, col nodo dietro --
# Le tre righe sopra restano il LNbits di ieri finche' l'ultimo ordine
# nato la' non e' chiuso. Queste tre sono il LNbits self-hosted sul VPS
# (127.0.0.1:5001, dietro il ponte verso LND), e la leva decide dove
# nasce il denaro NUOVO: ogni riga ricorda la sua cassaforte in colonna.
# Con la leva False (o le tre righe assenti) tutto nasce sul SaaS come
# sempre. Vedi docs/CANTIERI.md, «Il doppio wallet».
LNBITS_NODO_URL = "http://127.0.0.1:5001"
LNBITS_NODO_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY_DEL_NODO"
LNBITS_NODO_ADMIN_KEY = "INCOLLA_QUI_LA_ADMIN_KEY_DEL_NODO"  # SEGRETA!
CASSAFORTE_NUOVA = False    # True = i nuovi ordini nascono sul nodo

# IL GUARDIANO DEL PONTE (set 2026): con le tre righe del nodo presenti,
# ogni minuto il server bussa a LND attraverso il ponte (lnd-ponte,
# 127.0.0.1:18080). Dopo due minuti di silenzio riavvia la strada in
# piedi — il tunnel WireGuard e il ponte dal 21 set 2026; tor solo se e'
# acceso il piano B, lnd-ponte-tor — riguarda dopo 90 secondi e lo dice
# su Telegram, al massimo un avviso ogni 15 minuti. Lo stato esce anche
# in /api/salute («ponte»).
GUARDIANO_PONTE = True       # False = nessun controllo e nessun riavvio
GUARDIANO_PONTE_AVVISA = []  # a chi scrive, per id Telegram: es.
                             # [123456789]. Vuota = ai moderatori
                             # (ADMIN_IDS): un guasto del denaro non
                             # deve poter restare senza nessuno che lo
                             # sappia, come il 18 set 2026

# LA VERITA' DEI PAGAMENTI IN USCITA (set 2026): prima di decidere o di
# ritentare un pagamento, il server chiede com'e' finito anche a LND,
# attraverso lo stesso ponte di LNbits. Serve un macaroon SUO, di SOLA
# LETTURA — sul nodo:
#   lncli bakemacaroon --root_key_id 2 --save_to lettura.macaroon offchain:read
#   xxd -p -c 9999 lettura.macaroon
# — perche' questo e' un server web pubblico, e una chiave che sa pagare
# qui dentro non ci entra. Vuoto = LND «spento»: decide LNbits da sola,
# come prima. Vedi docs/PRODUZIONE.md, «I PAGAMENTI DA VERIFICARE».
LND_PONTE_MACAROON_LETTURA = ""          # esadecimale, tutto su una riga
LND_PONTE_CERT = "/opt/lnbits/data/tls.cert"   # il tls.cert di LND
LND_PONTE_URL = "https://127.0.0.1:18080"      # lnd-ponte (socat + tor)

# --- Regole del mercatino --------------------------------------------
COMMISSIONE_PERCENTO = 0     # trattenuta a vendita conclusa (0 = sospesa: cifra da decidere)
PROTEZIONE_PERCENTO = 0      # protezione acquisti a carico del COMPRATORE
                             # (modello Vinted): % sul solo prezzo articolo,
                             # si aggiunge al conto e resta alla piattaforma.
                             # 0 = spenta
FEE_DINAMICA_TOTALE_PERCENTO = 5.0
                             # il 5% da spartire fra compratore e venditore
                             # secondo il sentiment di Bitcoin (set 2026).
                             # ANCORA IN ANTEPRIMA: si vede nel preventivo,
                             # non muove un sat vero finché la beta non
                             # finisce — vedi la nota sopra la costante
                             # in server.py, vicino a orologio_fee_dinamica.
GIORNI_DATA_ANNUNCIO = 60    # «pubblicato N giorni fa» nel dettaglio:
                             # oltre questi giorni la riga non si mostra
VETRINA_PER_VENDITORE = 3    # la finestra scorrevole (set 2026): in
VETRINA_FINESTRA = 12        # qualunque VETRINA_FINESTRA card consecutive
                             # un venditore ne ha al piu'
                             # VETRINA_PER_VENDITORE, e il successivo
                             # slitta al primo posto che lo permette. Per
                             # il resto «piu' recenti prima». Non e' un
                             # filtro: nessun annuncio sparisce, cambia
                             # solo l'ordine. VETRINA_PER_VENDITORE = 0
                             # spegne tutto; allargare la finestra stringe
                             # l'anti-valanga (a 12 un negozio da 200
                             # prodotti tiene 1 card su 4, a 30 1 su 10)
AUTO_SBLOCCO_ATTIVO = False  # IL DISARMO (ago 2026): False = i sats non
                             # si muovono MAI senza un gesto umano. Gatea
                             # i soli rami FISICI dell'orologio; le due
                             # finestre del DIGITALE qui sotto restano
                             # armate comunque. True = si torna allo
                             # sblocco d'ufficio di ieri, e allora vanno
                             # rimessi i testi (l'elenco dei posti e'
                             # nella voce sua in docs/)
ORE_CONFERMA = 72            # finestra dell'acquirente dopo la consegna:
                             # a leva spenta e' quando parte il PRIMO
                             # promemoria, non piu' quando partono i sats
GIORNI_AUTO_SBLOCCO = 10     # silenzio dopo la spedizione: idem, a leva
                             # spenta e' il primo promemoria
PROMEMORIA_CONFERMA_GIORNI = 3  # ogni quanto si ribussa al compratore
                             # dopo il primo squillo (0 = promemoria
                             # spenti: i sats restano fermi in silenzio)
PROMEMORIA_CONFERMA_MAX = 3  # promemoria ignorati prima che il caso
                             # venga segnalato ai moderatori, poi silenzio
                             # (la cadenza e il tetto qui sopra valgono
                             # anche per i due promemoria al VENDITORE)
PROMEMORIA_SPEDIZIONE_GIORNI = 5  # ordine 'locked' col pacco mai partito:
                             # dopo quanti giorni dal pagamento parte il
                             # primo squillo al venditore (0 = spento)
PROMEMORIA_DIGITALE_ORE = 48 # idem per il codice online mai consegnato:
                             # ore, non giorni — un codice si manda subito
PROMEMORIA_BUSTA_GIORNI = 3  # spedizione a un punto, istruzioni NON
                             # ancora depositate: dopo quanti giorni
                             # dalla spedizione si ricorda al venditore
                             # di mettere nome e codice di ritiro
                             # dentro l'ordine. Il transito dura 1-3
                             # giorni: al terzo o il pacco e' lento o
                             # il codice e' nel dimenticatoio.
                             # Nessun gate su «ho spedito»: i due
                             # momenti restano separati come nella
                             # realta' (0 = spento)
PROMEMORIA_RITIRO_GIORNI = 2 # spedizione a un punto, istruzioni gia'
                             # depositate: ogni quanti giorni si ricorda
                             # a chi ha comprato di andare a ritirare
                             # (fa da prima finestra E da passo: la
                             # giacenza dura pochi giorni, e un passo
                             # piu' lungo cadrebbe a pacco gia' tornato.
                             # 0 = spento, NON «piu' lento»)
PROMEMORIA_OBIEZIONE_GIORNI = 2  # il venditore ha detto che il punto
                             # indicato non va bene (un locker che non
                             # esiste, o di una rete che non serve):
                             # dopo quanti giorni si ricorda a chi ha
                             # comprato di indicarne un altro. Da li'
                             # in poi il promemoria della spedizione
                             # TACE — la palla non e' piu' del
                             # venditore. Due giorni perche' la
                             # risposta e' un tocco, e non subito: chi
                             # risponde in un'ora non merita un
                             # sollecito. Cadenza e tetto sono quelli
                             # di PROMEMORIA_CONFERMA_* (0 = spento)
SOLLECITO_MANUALE_ORE = 48   # il promemoria A COMANDO: dopo quante ore
                             # dal pagamento chi ha comprato puo'
                             # sollecitare lui la spedizione (0 = mai)
SOLLECITO_MANUALE_DIGITALE_ORE = 24  # idem per il codice online
SOLLECITO_MANUALE_PAUSA_ORE = 24  # e ogni quante ore puo' ripeterlo
SOLLECITO_MANUALE_MAX = 3    # quanti in tutto: oltre resta la disputa
                             # (0 = il bottone non compare mai). I
                             # contatori dell'automatico qui sopra non
                             # si toccano: i due convivono
SOLLECITO_MANUALE_BUSTA_ORE = 24  # e sugli ordini spediti verso un
                             # punto di ritiro senza busta depositata:
                             # dopo quante ore DALLA SPEDIZIONE chi ha
                             # comprato puo' ricordare al venditore il
                             # codice (0 = mai). Il transito piu' corto
                             # e' un giorno: prima, il pacco non puo'
                             # essere al punto e bussare e' rumore.
                             # Pausa e tetto sono quelli qui sopra, i
                             # contatori sono SUOI (la fase 'locked'
                             # puo' aver consumato i tre squilli)
SOLLECITO_INCASSO_GIORNI = 7 # ordine «Da incassare» fermo: ogni tot
                             # giorni un promemoria al venditore
                             # (0 = solleciti spenti)
SOLLECITO_INCASSO_MAX = 4    # solleciti ignorati prima che il caso
                             # venga segnalato ai moderatori
CODA_FERMI_GIORNI = 10       # da quanti giorni un ordine coi sats in
                             # cassaforte entra nella sezione «Ordini
                             # fermi» del pannello admin. Dieci
                             # precedono TUTTI i 🧊 delle leve qui
                             # sopra: se la segnalazione e' partita, la
                             # riga c'e'. (0 = coda spenta, e dopo il
                             # 🧊 quell'ordine torna raggiungibile solo
                             # per numero)
TERMOMETRO_SOTTOCATEGORIE = True  # il lunedi' UNA notifica agli admin
                                  # con gli annunci senza sottocategoria
                                  # (False = mai; tace comunque sotto il
                                  # minimo e a vetrina piena)
TERMOMETRO_SOTTOCATEGORIE_MINIMO = 5  # sotto questi vuoti non si disturba
TETTO_SATS_ANNUNCIO = 0      # prezzo massimo per annuncio: 0 = nessun
                             # limite (default). Mettici es. 100_000 per
                             # accendere il tetto; per gli annunci in EUR
                             # vale l'equivalente al cambio corrente
MAX_QUANTITA_ANNUNCIO = 999999  # pezzi massimi per annuncio (quantita'
                             # in stock). Alto apposta: quanti pezzi ha
                             # in magazzino lo sa il venditore, non noi.
                             # E' un guardrail contro il numero incollato
                             # per sbaglio, non un giudizio sul negozio
MAX_RIGHE_SET = 8            # annunci DIVERSI massimi in un set
                             # («Riempi il barattolo»): un pacco vero,
                             # non un camion
MAX_PREFERITI = 10           # quanti annunci ATTIVI stanno «nel tuo
                             # barattolo». Piccolo apposta: e' una
                             # selezione, non una lista dei desideri
                             # infinita. Contano solo gli attivi —
                             # comprare qualcosa che c'e' dentro
                             # libera spazio da solo

# --- Consegna digitale (buoni regalo, codici, licenze) ---------------
# Il codice passa DENTRO Barattolo: il venditore lo consegna in un
# campo dedicato dell'ordine, il compratore lo rivela con un tocco
# che fa da ricevuta di lettura. Finestre piu' corte del fisico:
# un codice si prova subito.
ORE_CONFERMA_DIGITALE = 24   # dopo la rivelazione: poi sblocco automatico
ORE_SILENZIO_DIGITALE = 48   # consegnato ma mai rivelato: poi sblocco
# Cifratura a riposo dei codici nel database: una stringa segreta
# qualsiasi (generane una casuale e incollala SOLO nel config.py del
# server). Vuota = i codici restano in chiaro nel DB: tutto funziona
# uguale, protegge meno un backup rubato — e il server lo dice con una
# riga all'avvio, cosi' non e' un silenzio.
# DUE COSE DA SAPERE PRIMA DI METTERLA: se la perdi, i contenuti gia'
# cifrati non si leggono piu' (nessuno puo' recuperarli, nemmeno noi);
# e accenderla non ricifra il passato — le righe gia' scritte in
# chiaro restano in chiaro, e vanno bene cosi' finche' esistono.
CHIAVE_CONTENUTI_DIGITALI = ""
# La stessa chiave cifra l'INDIRIZZO DI CASA che il compratore scrive
# nell'ordine per la spedizione (ago 2026) — ma li' il fail-open non
# c'e': senza chiave la spedizione a casa risponde 503 e chi compra
# ripiega sulla chat, invece di lasciare un'anagrafica in chiaro nel
# database. Un PIN di ritiro in chiaro e' una degradazione
# accettabile, il nome e la via di una persona no.
# L'indirizzo si cancella da solo APPENA il compratore conferma di
# aver ricevuto l'oggetto: da li' in poi non serve piu' a niente
# (garantiamo la transazione, non la consegna). Questi giorni valgono
# SOLO per gli ordini che si chiudono senza quella conferma — un
# rimborso, una disputa decisa da un moderatore — dove la conferma non
# arrivera' mai e serve comunque una scadenza.
# Si puo' allungare o accorciare (0 = alla prima passata dopo la
# chiusura), MAI spegnere: e' una promessa scritta nella pagina «Il
# pagamento protetto», e il numero che la pagina mostra viene da qui —
# se lo cambi, cambia anche la frase che leggono gli utenti.
GIORNI_INDIRIZZO = 10
# Leve anti-frode, SPENTE di serie (0 = nessun limite):
TETTO_DIGITALE_NUOVI = 0     # es. 50_000: un compratore senza acquisti
                             # conclusi non compra digitale sopra questa
                             # cifra (sats, sul solo articolo)
DIGITALE_MIN_VENDITE = 0     # es. 1: per pubblicare annunci digitali
                             # servono almeno N vendite concluse

# --- Offerte (contrattazione sul prezzo) -----------------------------
# Il compratore propone una cifra, il venditore accetta, rifiuta o fa
# UNA controproposta. Accettare = diritto di comprare a quel prezzo
# entro la scadenza; l'annuncio resta in vetrina e vince chi paga.
OFFERTA_MINIMA_PERCENTO = 50 # sotto questa % del listino l'offerta
                             # non parte proprio (anti-offerte-insulto)
ORE_RISPOSTA_OFFERTA = 48    # senza risposta l'offerta scade da sola
ORE_PAGAMENTO_OFFERTA = 24   # tempo per pagare dopo l'accettazione
MAX_OFFERTE_ANNUNCIO = 3     # tentativi totali per compratore per
                             # annuncio (una offerta attiva alla volta)
MAX_RILANCI_OFFERTA = 2      # quante volte chi compra puo' RILANCIARE
                             # invece di accettare o rifiutare una
                             # controproposta. NON consuma i tentativi
                             # qui sopra: resta la stessa trattativa.
                             # 0 = spento, cioe' il ping-pong di ieri.

# --- Negozio in ferie ------------------------------------------------
# Il venditore che parte chiude la bottega con la data di rientro. Gli
# annunci RESTANO in vetrina, col prezzo in grigio e la data scritta
# sopra: si guardano, non si comprano — niente acquisti, offerte,
# carrello, lampo ne' aste nuove. Non si chiude con affari da spedire,
# aste vive, accordi da pagare o pagamenti in corso.
# Il rientro e' AUTOMATICO alla data: il controllo e' in lettura, quindi
# il negozio riapre da solo anche se il server e' stato spento.
FERIE_ATTIVE = True          # interruttore generale (False = spento)
FERIE_MAX_GIORNI = 90        # quanto in la' puo' stare la data di rientro
FERIE_PREAVVISO_ORE = 24     # «domani riapri» (0 = nessun promemoria)

# --- Il banner del negozio -------------------------------------------
# L'insegna che il venditore appende sopra il suo catalogo: una foto e
# un link al suo sito. Vive SOLO sulla pagina del suo negozio.
# NASCE SPENTO, come SERVIZI_ATTIVI e ASTA_ABILITATA, e la ragione e'
# il LINK: e' la prima volta che Barattolo apre un indirizzo scritto da
# un utente davanti a un ALTRO utente. Si accende con un gesto qui,
# guardando il primo giro, mai per effetto di un deploy.
# Ogni banner — e ogni sua modifica — passa comunque da un MODERATORE:
# l'AI di casa legge testo e un banner e' un'immagine, quindi li' non
# ci sarebbe niente da leggere.
BANNER_NEGOZIO_ATTIVO = False   # interruttore generale (False = spento)
# LO SCONTO FEDELTA' PER LIVELLO (set 2026): il banner si paga SEMPRE
# — non c'e' piu' un livello che lo regala — e il livello sconta
# soltanto il prezzo qui sotto. MAI il 100%: il codice chiude a 99
# anche se qui si scrivesse per sbaglio un numero piu' alto.
# I gradini sono: nuovo · avviato · pratico · esperto · maestro.
# Tutti a zero = lo sconto fedelta' e' spento, si paga sempre lo
# stesso prezzo — il banner resta comunque a pagamento in ogni caso.
BANNER_SCONTI_LIVELLO = {"nuovo": 0, "avviato": 10, "pratico": 20,
                         "esperto": 35, "maestro": 50}
# Il PREZZO della porta (tappa 2): si paga UNA VOLTA e vale per
# sempre. E' il primo incasso che Barattolo fa per se', quindi ogni
# sblocco lascia una riga nella tabella `pagamenti`: senza, sembrerebbe
# un orfano al giro di riconciliazione con LNbits.
# 0 = il banner e' spento del tutto: nessuno puo' sbloccare la porta.
BANNER_PREZZO_SATS = 20_000
# Il prezzo PIENO, quello BARRATO accanto: dice che i 20.000 qui
# sopra sono un'offerta di lancio e non il listino. NON ENTRA MAI NEL
# CONTO — chi paga paga la cifra scontata, e la ricevuta la fotografa
# in colonna — quindi cambiarlo non muove un sat di quel che si
# incassa: cambia solo cosa si legge accanto.
# 0, o UGUALE al prezzo, spegne il barrato: la stessa cifra sopra se'
# stessa non e' una riga, e' un refuso. Un pieno piu' BASSO del prezzo
# non si barra mai (si leggerebbe come un aumento) e degrada in
# silenzio, senza allarmi.
# E il chip «−N%» accanto al barrato compare SOLO se lo sconto e'
# tondo: 40.000 → 20.000 fa −50% e si legge, 30.000 → 20.000
# farebbe −33,33% e resta il solo barrato. Non si arrotonda mai.
BANNER_PREZZO_PIENO_SATS = 40_000
# Gli accorciatori, ed e' la riga che regge la moderazione del link: un
# «bit.ly/xyz» si approva pulito e domani punta altrove, quindi il link
# dev'essere ISPEZIONABILE. Match sul dominio, sottodomini compresi.
BANNER_LINK_VIETATI = (
    "bit.ly", "t.co", "tinyurl.com", "is.gd", "cutt.ly", "ow.ly",
    "buff.ly", "rebrand.ly", "short.io", "rb.gy", "t.ly", "lnkd.in",
    "shorturl.at", "s.id", "bl.ink", "tiny.cc", "shorte.st")

# --- IL LINK DEL NEGOZIO A SCELTA (set 2026) --------------------------
# La personalizzazione SUBITO DOPO il banner: chi arriva al livello
# «avviato» — lo stesso gradino che apriva la porta del banner prima
# che diventasse sempre a pagamento — puo' scegliersi un indirizzo
# leggibile (/negozio/untempoperte) al posto del codice casuale.
# I gradini sono: nuovo · avviato · pratico · esperto · maestro.
SLUG_NEGOZIO_LIVELLO = "avviato"
# Il prezzo si paga OGNI VOLTA che si cambia idea sul nome — niente
# sconto di livello qui, a differenza del banner: e' il prezzo
# ripetuto a tenere la scelta rara, non un gradino piu' alto.
# 0 = la personalizzazione e' spenta del tutto.
SLUG_NEGOZIO_PREZZO_SATS = 5_000

# LA LISTA BIANCA DEI LINK NELLE DESCRIZIONI (set 2026): gli unici
# domini che una descrizione di annuncio rende TOCCABILI. Tutto il
# resto resta testo copiabile, cioe' la vita di sempre.
# BIANCA e non nera: una lista nera e' una rincorsa (ogni dominio di
# phishing nuovo passa finche' qualcuno non lo aggiunge), una bianca
# puo' sbagliare solo per difetto — e il suo errore e' un sito onesto
# che resta testo, che non fa male a nessuno.
# Coppia (dominio, percorsi ammessi). Il PERCORSO c'e' perche' un
# dominio fidato puo' ospitare un redirect aperto («youtube.com/
# redirect?q=...» e' una pagina YouTube vera). Tupla vuota = tutto il
# dominio, e si scrive solo dove ogni percorso e' un video.
# Svuotarla ( = () ) spegne la funzione: nessun link si tocca piu'.
LINK_DESCRIZIONE_AMMESSI = (
    ("youtube.com", ("/watch", "/shorts/", "/playlist", "/live/",
                     "/embed/", "/channel/", "/c/", "/user/", "/@")),
    ("youtu.be", ()),
    ("vimeo.com", ()),
)

# --- La ronda del libro mastro ---------------------------------------
# Una volta al giorno l'orologio ripassa gli INVARIANTI del database
# (l'aritmetica degli ordini, la cassa delle aste chiuse, la forma di
# ordine_righe...). Se torna tutto TACE — nemmeno una riga nel journal;
# se qualcosa non torna manda il 🧊 ai moderatori con la query che ha
# fallito e gli id. LEGGE E BASTA: non corregge mai niente.
# Gli stessi controlli si lanciano a mano con query_libro_mastro.sql.
CONTROLLO_LIBRO_MASTRO = True   # False = ronda spenta

# LA RONDA DEI PAYOUT: una volta al giorno chiede a LNbits, per hash,
# com'e' finito ogni pagamento in uscita che diamo per concluso, e alza
# il 🧊 su quelli che LNbits dichiara FALLITI. E' la protezione per
# ORDINE — quella di cassa su un wallet misto non torna mai e non e' un
# allarme. Legge e basta: non corregge e non ripaga niente.
RICONCILIA_PAYOUT = True        # False = i payout non si ricontrollano

# Quando il nostro nodo Lightning non risponde, un pagamento in uscita
# non parte e la riga si timbra «da riprovare» invece di dichiararsi
# fallita: la fattura del venditore resta buona e nessuno viene
# accusato. A ogni battito dell'orologio se ne riprendono al massimo
# tante — e comunque il giro si ferma alla prima che tace ancora,
# perche' se il nodo e' muto per una lo e' per tutte.
MAX_RIPRESE_GIRO = 20

# --- Sconto carrello (chi prende piu' cose paga meno) ----------------
# Il venditore premia chi compra piu' articoli in un ordine solo: UNA
# regola per tutto il suo negozio — «da N articoli, −X%» — senza
# scaglioni. Vale SOLO sul prezzo degli articoli, MAI sulla spedizione.
# Non vale su un annuncio comprato da solo, per quante copie se ne
# prendano: lo sconto e' del carrello.
# IL CRITERIO della soglia lo sceglie il venditore: a PEZZI («da 3
# articoli») o a VALORE degli articoli («da 100.000 sats nel
# carrello»), che e' il modo di dare lo sconto da due pezzi su un
# computer e da venti su una scatola di cianfrusaglie, con una regola
# sola. E la VALUTA della soglia a valore la sceglie sempre lui, in
# EURO o in SATS (ago 2026): in euro non deriva col cambio — chi scrive
# 100.000 sats pensando «una cinquantina di euro» si ritrova una
# promessa del doppio senza aver toccato niente — mentre in sats non ha
# bisogno del cambio, e scatta anche quando il cambio non risponde. Il
# cassetto lo dice, e sceglie il venditore. L'incasso resta sempre in
# sats.
# ATTENZIONE se questo file lo copi su un config gia' esistente: le
# leve si chiamano *_EUR e *_SATS apposta, cosi' una riga vecchia dal
# nome nudo resta INERTE invece di essere letta nell'unita' sbagliata
# (che sarebbe una promessa spenta in silenzio).
# Si cumula con la lampo e con le offerte accettate: e' una promessa di
# negozio, e un pezzo che non la mantenesse non avrebbe un posto onesto
# dove dirlo. Il tetto qui sotto e' il guardrail della cascata — e
# attenzione, a criterio valore la soglia guarda il carrello DOPO
# lampo e accordo: una lampo generosa puo' farlo scendere sotto soglia.
SCONTO_PACCO_ATTIVO = True      # interruttore generale (False = spento)
SCONTO_PACCO_CRITERI = ("pezzi", "valore", "entrambi")   # togliere un
                                # criterio da qui lo spegne per chi
                                # l'aveva scelto. 'entrambi' accende le
                                # due gambe insieme — «da 3 pezzi O da
                                # 25 € di articoli» — con UNA sola
                                # percentuale: due strade per lo stesso
                                # sconto, mai due sconti che si sommano.
SCONTO_PACCO_SOGLIE = (2, 3, 4, 5)      # le soglie proposte al venditore
# LA VALUTA DELLA SOGLIA A VALORE LA SCEGLIE IL VENDITORE (ago 2026,
# chiesto dalla comunita'). Vale per TUTTE E DUE le promesse, e ognuna
# ha la sua: sono indipendenti. Togliere una valuta da qui la spegne per
# chi l'aveva scelta — freno d'emergenza, non una taratura.
VALUTE_SOGLIA = ("eur", "sats")
SCONTO_PACCO_VALORI_EUR = (10, 25, 50, 100)  # a valore, in euro: basse
                                # apposta, che il carrello di un
                                # mercatino dell'usato e' piccolo
SCONTO_PACCO_VALORI_SATS = (10_000, 25_000, 50_000, 100_000)  # le
                                # gemelle in sats: numeri TONDI, non la
                                # conversione delle sorelle in euro
SCONTO_PACCO_SCONTI = (5, 10, 15, 20)   # le percentuali proposte
SCONTO_PACCO_MIN_SOGLIA = 2     # sotto non e' uno sconto carrello: e'
                                # un ribasso di listino, e quello si fa
                                # sul prezzo
SCONTO_PACCO_MIN_VALORE_EUR = 1  # la gemella a valore: una cintura
                                # contro lo zero travestito, non un
                                # giudizio su quanto debba valere un
                                # carrello
SCONTO_PACCO_MIN_VALORE_SATS = 1  # idem, in sats
SCONTO_PACCO_MIN_PERCENTO = 5   # sotto non e' un'offerta, e' rumore:
                                # lo stesso numero della lampo. Serve da
                                # quando la percentuale si scrive a mano
                                # (prima l'elenco partiva da 5 da se');
                                # NON tocca lo spegnimento, che e' un
                                # ramo suo senza guardie
SCONTO_PACCO_MAX_PERCENTO = 30  # sconto massimo consentito

# --- Spedizione gratis sopra soglia ----------------------------------
# La seconda promessa di negozio: «da N di articoli la spedizione la
# offro io». Anche qui la VALUTA la sceglie il venditore, e ne ha una
# SUA: le due promesse restano indipendenti, e un venditore puo'
# dichiarare lo sconto in euro e la spedizione gratis in sats.
# A DIFFERENZA DELLO SCONTO vale anche su un oggetto solo: azzerare una
# tariffa scrive spedizione_sats=0, cioe' lo stato che gli annunci con
# spedizione gratuita dichiarata hanno da sempre — mentre uno sconto di
# testata romperebbe il conto dell'unitario di un ordine a un annuncio
# solo. Il venditore incassa meno, che e' cosa vuol dire offrirla.
# Le due promesse guardano lo STESSO numero, il prezzo degli articoli
# prima dello sconto carrello: sono indipendenti, e nessuna delle due
# puo' spegnere l'altra. Attenzione, come per lo sconto: la soglia
# guarda il carrello DOPO lampo e accordi.
SPED_GRATIS_ATTIVO = True       # interruttore generale (False = spento)
SPED_GRATIS_SOGLIE_EUR = (10, 25, 50, 100)  # le soglie proposte al
                                # venditore, in euro
SPED_GRATIS_SOGLIE_SATS = (10_000, 25_000, 50_000, 100_000)  # e in sats,
                                # per chi dichiara la soglia cosi'
SPED_GRATIS_MIN_EUR = 1         # una cintura contro lo zero travestito:
                                # sotto, la spedizione sarebbe gratis
                                # sempre — e quella si dichiara nel
                                # prezzo dell'annuncio (costo 0)
SPED_GRATIS_MIN_SATS = 1        # idem, in sats

# --- Codici sconto del venditore -------------------------------------
# «SATOSHI10» scritto alla cassa vale -X% sugli articoli. E' la TERZA
# leva accanto allo sconto sugli articoli e alla spedizione gratis, ma
# di natura diversa: quelle sono promesse PUBBLICHE scritte in vetrina
# e uguali per tutti, un codice e' un SEGRETO che il venditore da' a
# chi vuole — e infatti non esce MAI da nessuna superficie pubblica.
# VINCE IL MAGGIORE fra il codice e lo sconto sugli articoli: si
# applica solo il piu' generoso, mai la somma.
CODICI_SCONTO_ATTIVI = True     # False = i codici non valgono piu' alla
                                # cassa e il cassetto risponde 400, ma
                                # le righe restano e tornano vive
CODICI_SCONTO_MAX_PERCENTO = 100  # NON e' piu' pari al gemello dello
                                # sconto articoli (ago 2026): quello e'
                                # una promessa in vetrina, questo un
                                # segreto dato a chi si vuole. Il fondo
                                # della cascata non si sposta — «vince
                                # il maggiore» non e' una somma — e il
                                # 100 non vuol dire gratis: resta 1 sat
CODICI_SCONTO_MIN_PERCENTO = 1   # quanto valga il regalo lo decide chi
                                # lo fa. Resta una cintura: a 0 il
                                # codice non scontera' mai niente
CODICI_SCONTO_PERCENTI = (5, 10, 15, 20)     # le pillole del venditore

# LO SCONTO A CIFRA FISSA (ago 2026): «−10 €» invece di «−10%». La
# valuta la sceglie il venditore, e le due liste sono due perche' un
# euro e un sat non si scrivono nella stessa scala.
CODICI_SCONTO_VALORI_EUR = (5, 10, 20, 50)   # le pillole in euro
CODICI_SCONTO_VALORI_SATS = (5_000, 10_000, 25_000, 50_000)
CODICI_SCONTO_MAX_VALORE_EUR = 10_000   # cinture larghe: il tetto VERO
CODICI_SCONTO_MAX_VALORE_SATS = 100_000_000   # e' l'articolo stesso —
                                # uno sconto piu' grande del carrello si
                                # LIMA, non si rifiuta
CODICI_SCONTO_DURATE_GIORNI = (7, 30, 90, 0)  # lo 0 = senza scadenza
CODICI_SCONTO_MAX_PER_VENDITORE = 20   # quanti codici puo' avere
CODICI_SCONTO_MAX_USI = 100_000        # cintura contro il numero
                                # incollato per sbaglio
CODICI_SCONTO_TENTATIVI_ORA = 20  # il freno a chi prova a indovinare i
                                # codici altrui: si consuma SOLO sui
                                # tentativi sbagliati (0 = nessun freno)

# --- Suggerimenti dal bot --------------------------------------------
# I consigli che il bot manda al venditore: cosa manca a un annuncio, e
# le leve del negozio che non ha ancora acceso. ACCESI di serie
# dall'ago 2026 (prima erano opt-in, e non li accendeva quasi nessuno).
# IL RITMO E' LA META' CHE CONTA, e va tenuto anche se un giorno il
# default tornasse spento: chi si stufa BLOCCA IL BOT, e col bot
# bloccato non riceve piu' le notifiche degli ordini, che sono
# portanti. Su Nostr il danno e' identico e meno visibile: smette
# semplicemente di leggere i DM, e non se ne accorge nessuno.
# Chi ha SCELTO — in un verso o nell'altro — non viene mai scavalcato
# dal default: lo garantisce la colonna utenti.suggerimenti_scelti.
SUGGERIMENTI_DI_SERIE = True    # False = tornano opt-in (chi ha gia'
                                # scelto resta com'e', in entrambi i sensi)
SUGGERIMENTI_OGNI_GIORNI = 7    # al massimo uno ogni N giorni PER
                                # PERSONA, qualunque sia la coda.
                                # 0 = nessun ritmo: e' la raffica di
                                # ieri, un freno d'emergenza e non una
                                # taratura

# --- L'invito a dichiarare i corrieri (ago 2026) ---------------------
# Chi pubblica una spedizione senza aver detto con quali corrieri
# spedisce trova un foglio al tocco di «Pubblica»: le reti da spuntare
# li' dentro, e «Pubblica lo stesso» che pubblica davvero — insistente,
# mai bloccante.
# IL TETTO E' LA META' CHE CONTA: dopo N volte il foglio smette e resta
# la riga nel form. Un cartello che compare SEMPRE uguale si impara a
# scavalcare senza leggerlo, e in quel form ci sono gia' nove righe che
# si contendono l'attenzione.
INVITO_CORRIERI_MAX = 3         # quante volte al massimo. 0 = niente
                                # foglio, resta la sola riga nel form

# --- Offerta lampo (sconto a tempo su tutto l'annuncio) --------------
# Modello Vinted «sconto ai follower»: quando qualcuno mette l'annuncio
# nel suo barattolo il venditore riceve un avviso anonimo e puo' lanciare
# uno sconto a tempo. E' PUBBLICO (chiunque compra nella finestra paga
# scontato) e a PERCENTUALE (non tocca mai il prezzo del listino).
LAMPO_ATTIVE = True          # interruttore generale (False = spento)
LAMPO_SCONTI = [10, 20, 30]  # le percentuali proposte come chip
LAMPO_MIN_PERCENTO = 5       # sconto minimo consentito
LAMPO_MAX_PERCENTO = 70      # sconto massimo consentito (anti-svendita)
ORE_LAMPO_OPZIONI = [6, 24, 48]  # le durate proposte
MAX_LAMPO_SETTIMANA = 2      # lanci per annuncio in 7 giorni
GIORNI_COLPO = 7             # cooldown dell'avviso «ha fatto colpo»

# --- I servizi (prestazioni definite, con un appuntamento) -----------
# Lezioni, consulenze, prestazioni con una durata e un contenuto
# stabiliti PRIMA. Il venditore propone l'appuntamento dentro
# l'ordine, il compratore lo conferma, e finche' non l'ha confermato
# nessuna finestra parte. Nessun timer sposta sats: a chiudere
# l'affare e' la conferma di chi ha comprato, come per il ritiro in
# zona; se non arriva, decide un moderatore.
# L'interruttore nasce SPENTO — non muove denaro in uscita, ma cambia
# COSA si vende qui dentro e allunga la permanenza dei sats in
# cassaforte: si accende con un gesto, guardando il primo giro.
SERVIZI_ATTIVI = False       # interruttore generale (False = spento)
SERVIZIO_MAX_GIORNI = 60     # quanto lontano puo' stare l'appuntamento
SERVIZIO_MAX_APERTI = 0      # ordini servizio aperti INSIEME per chi
                             # non ha vendite concluse (0 = spento).
                             # Non e' una soglia per pubblicare: e' il
                             # freno sulla raffica — il conteggio delle
                             # dispute smaschera il recidivo, non chi
                             # incassa cinquanta lezioni prima che la
                             # prima disputa sia decisa.

# --- Asta a tempo (vendita al miglior offerente) ---------------------
# Chi vuole comprare punta versando sats nel deposito di garanzia; per
# superare chi e' in testa si versa solo la differenza; alla scadenza
# la puntata piu' alta diventa un ordine gia' pagato e i perdenti
# vengono rimborsati nel loro «Da riscuotere». L'interruttore nasce
# SPENTO: le aste muovono denaro vero in uscita, si accende qui con un
# gesto consapevole guardando il primo giro (come l'import Nostr).
ASTA_ABILITATA = False       # interruttore generale (False = spento)
ASTA_DURATE_GIORNI = [1, 3, 7, 14, 30]  # le durate offerte al venditore
                             # (nel form: 7 giorni preselezionato)
ASTA_INCREMENTO_PERCENTO = 5 # rilancio minimo sopra la puntata in testa
ASTA_PROROGA_MINUTI = 10     # anti-cecchino: saldo negli ultimi N
                             # minuti = scadenza spostata a saldo + N
ASTA_MAX_ATTIVE_VENDITORE = 3  # aste vive per venditore (prudenza)
# Il proxy a budget depositato: chi punta deposita il suo MASSIMO e il
# sistema espone per lui il minimo necessario (il massimo resta
# segreto). Nasce SPENTO e resta spento anche quando ASTA_ABILITATA si
# accendera': il proxy parte solo a gara manuale rodata. Spegnerlo
# blocca le sole puntate proxy nuove, mai il motore dei proxy vivi.
ASTA_PROXY_ATTIVO = False    # rilancio automatico (False = spento)

# --- Scambio P2P: Barattolo come client di Mostro ---------------------
# Il tab «P2P» smette di essere un coming soon e apre il libro ordini
# del coordinator Mostro — un servizio INDIPENDENTE, su una macchina di
# Andrea, che custodisce in una hold invoice i sats di chi scambia
# euro<->bitcoin con un altro utente. Barattolo qui non tocca un sat:
# fa da bacheca (mostra il libro) e da campanello (avvisa chi ha uno
# scambio aperto). Le chiavi con cui si scambia nascono nel BROWSER di
# chi scambia, mai sul server.
# NASCE SPENTA, il patto di ASTA_ABILITATA: si accende qui con un gesto
# dopo il giro dal vivo sul coordinator, mai per effetto di un deploy.
# Spenta, il tab resta il coming soon e nessun relay viene toccato.
P2P_ATTIVO = False
# LA FASE CHIUSA, prima di aprire a tutti: i tg_id che vedono il P2P
# mentre gli altri leggono il coming soon di sempre. IL VUOTO E'
# L'APERTURA — lasciata cosi' (o non dichiarata affatto) il P2P vale
# per chiunque appena P2P_ATTIVO si accende, e il giorno dell'apertura
# si cancella la riga. Finche' c'e' qualcuno qui dentro, la campagna
# una-tantum a chi ha premuto «Avvisami» NON parte: e' l'annuncio
# dell'apertura, e si manda una volta sola.
# ⚠️ Una riga storta (una stringa, o qualcosa che non e' un numero)
# vale «chiusa a tutti» e lo dice all'avvio: qui sbagliare verso
# l'apertura vorrebbe dire uno scambio di denaro vero aperto al
# mercatino intero senza averlo deciso.
P2P_PROVA_IDS = []
# IL SEGRETO DEL PROFILO DI SCAMBIO (set 2026): da qui si ricava la
# chiave d'identita' Mostro di chi entra da Telegram, cosi' i suoi
# scambi si vedono uguali dal bot, dal sito e dall'app. Serve anche il
# SALE di ogni persona, che sta nel database (`p2p_semi`): chi si porta
# via il solo questo file non ricava niente.
# ⚠️ E' IL SEGRETO PIU' PESANTE DI QUESTO SERVER — chi lo ruba INSIEME
# al database puo' firmare uno scambio al posto di chi entra da
# Telegram, cioe' liberare sats e aprire dispute. Sta sul VPS come le
# chiavi LNbits, esce su carta + Bitwarden, e non si incolla MAI in una
# chat o in un canale Telegram (che non e' cifrato end-to-end).
# Si genera cosi', 32 byte:
#     python -c "import secrets; print(secrets.token_hex(32))"
# VUOTO O NON DICHIARATO = il mondo di ieri: il profilo di scambio
# nasce nel browser e vale per dispositivo. Non rompe niente.
# E' UN DIZIONARIO {versione: segreto} PERCHE' SI RUOTA AGGIUNGENDO,
# mai sostituendo: la versione entra nella derivazione, quindi
# cambiarla a tutti insieme cancellerebbe l'identita' di tutti in
# silenzio. La procedura sta in docs/PRODUZIONE.md.
SEGRETI_PROFILO_P2P = {}          # {1: "INCOLLA_QUI_32_BYTE_ESADECIMALI"}
# La versione con cui nascono i profili nuovi. Si sposta SOLO durante
# una rotazione, e solo dopo aver aggiunto la riga nuova qui sopra.
SEGRETO_PROFILO_P2P_VIVA = 1
# La npub del coordinator: e' PUBBLICA (firma il libro ordini che tutti
# leggono). Storta = lo scambio resta spento, e il journal lo dice.
MOSTRO_NPUB = "npub14l3aax4gv9khctnzavek6wsj0nua42d5fq4tr6fkr4wpwhfm3neswg6lg0"
# I relay su cui il coordinator PUBBLICA: il client legge il libro e
# manda le richieste da qui, e il suo relay dedicato va per primo. Non
# c'e' una lista di serie nel codice, apposta — vuota = spento.
MOSTRO_RELAY = [
    "wss://relay.mostro.network",
    "wss://relay.damus.io",
    "wss://nos.lol",
]
# LO SPECCHIO (set 2026): i relay che tengono una COPIA del libro senza
# essere il posto dove il coordinator vive — il nostro
# "wss://relay.barattolo.store" sta qui, e non nella lista qui sopra.
# LA DIVISIONE E' IL PUNTO, non un ordine diverso: di qui si LEGGE
# soltanto. Le richieste al coordinator (la gamba viva) scorrono
# MOSTRO_RELAY e non passano mai da questa lista — mostrod sullo
# specchio non ascolta, e uno scambio mandato li' morirebbe senza che
# niente fallisca.
# VUOTA E' IL MONDO DI IERI, byte per byte: il libro si legge dai soli
# relay del coordinator, come prima che questa riga esistesse.
MOSTRO_RELAY_SPECCHIO = []
# LA COMMISSIONE DI BARATTOLO SUL P2P (set 2026): il LISTINO, in
# percentuale sull'intero scambio. ⚠️ NON incassa niente: a incassare
# e' la `fee` del coordinator (settings.toml del nodo), che i client
# leggono viva dal suo 38385 e spartiscono meta' a testa nel conto.
# Questa dice solo QUANDO si e' ancora in BETA: fee viva sotto il
# listino = il conto del P2P mostra la pillola «beta».
# Sul VPS il listino e' 4 (set 2026); in beta il nodo tiene `fee = 0.03`.
P2P_COMMISSIONE_PERCENTO = 2
# IL TETTO IN EURO DEGLI ORDINI P2P (set 2026): il massimo che il
# foglio Pubblica accetta come importo, NOSTRO e sopra quello in
# sats del coordinatore (`max_order_amount` del 38385), che resta
# valido sotto, sempre. Lo giudica il CLIENT mentre si scrive la
# cifra: il coordinatore non lo conosce e non lo applica. 0 =
# spento, nessun tetto in euro.
P2P_MAX_EURO = 0
# IL MINIMO DI UN PAYCODE BARATTOZON (30 set 2026): sotto questa cifra
# in euro un ordine «Contanti al tabacchino» non si pubblica, a mercato
# come a prezzo fisso. Lo giudica il foglio Pubblica (dalla busta delle
# leve) e lo ripete la rotta del canale. Non dichiarata = 25; 0 = spento.
BARATTOZON_MIN_EURO = 25
# IL MINIMO DI UN PAYCODE BARATTOZON (30 set 2026): sotto questa cifra
# in euro un ordine «Contanti al tabacchino» non si pubblica, a mercato
# come a prezzo fisso. Lo giudica il foglio Pubblica (dalla busta delle
# leve) e lo ripete la rotta del canale. Non dichiarata = 25; 0 = spento.
BARATTOZON_MIN_EURO = 25
# IL TETTO DEL CONTANTI DI PERSONA (30 set 2026, decisione di Andrea):
# il massimo in euro di un ordine P2P col metodo «Contanti» — quello
# dell'incontro a mano, NON «Contanti al tabacchino» di Barattozon, che
# ha il suo tetto (i 999 € di Amazon). Vale sia per chi PUBBLICA sia per
# chi PRENDE, lo giudica il client come P2P_MAX_EURO, e sta SOTTO quello
# quando quello e' acceso. Perche' c'e': una banconota non lascia
# ricevuta, e sopra una cifra il rischio di un incontro andato male non
# lo copre nessuna garanzia (docs/STUDIO-CONTANTI-A-MANO-2026-09-25.md).
# ⚠️ IL DEFAULT NEL CODICE E' 250, e vale anche senza questa riga: 0 =
# spento, nessun tetto per il contanti.
P2P_CONTANTI_MAX_EURO = 250
# LE CARD P2P IN VETRINA (26 set 2026): gli ordini vivi del libro
# compaiono anche fra gli annunci del mercatino, come card.
# SPENTA le vedono solo i moderatori e chi e' in P2P_PROVA_IDS, per
# provarle. ACCESA le vedono tutti, ma solo con P2P_PROVA_IDS vuota:
# il giorno del lancio si svuota la lista E si mette True qui.
# Solo True accende: una stringa o un numero restano spenti.
P2P_IN_VETRINA = False
# LA CAUZIONE DI CHI PRENDE, NEL CONTANTI DI PERSONA (1 ott 2026): chi
# prende un ordine in contanti blocca una piccola cauzione (una seconda
# hold invoice, il 3% con un pavimento di 1.000 sats) che torna a fine
# scambio e si perde solo se un moderatore decide che non si e'
# presentato all'incontro. A CHIEDERLA E' IL COORDINATORE: la sezione
# `[anti_abuse_bond]` del suo settings.toml, con la patch 0008 del fork
# che la limita al metodo «Contanti» (deploy/mostro/README.md). Questa
# leva dice al CLIENT di mostrarla — la cifra prima della presa, il
# passo, la voce in «Info P2P» —, e il client crede solo a tutt'e due:
# la leva E il 38385 del coordinatore. Solo True accende.
P2P_CAUZIONE = False
# LO SCONTO FEDELTA' SUL P2P (set 2026): punti percentuali IN MENO
# sulla propria meta' per chi e' pioniere OPPURE ha il livello 5 (uno
# sconto solo, non si sommano). ⚠️ Lo sconto vero lo applica il
# coordinatore (patch 0005 del fork, `BARATTOLO_SCONTO_FEE` nel compose
# del nodo): questa leva dice al client che cifra mostrare, e le due
# devono combaciare (0.5 qui = 0.005 la'). 0 = spento.
P2P_SCONTO_FEDELTA_PERCENTO = 0
# Il segreto con cui il coordinatore chiede a /api/p2p/sconto se una
# trade key ha lo sconto. Lo stesso valore va nel compose del nodo
# (`BARATTOLO_SCONTO_SEGRETO`). Vuoto o segnaposto = la rotta NON
# ESISTE (404) e il coordinatore fa prezzo pieno a tutti.
P2P_SCONTO_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"
# Il segreto con cui il coordinatore RACCONTA a /api/p2p/evento ogni
# passo di ogni scambio (patch 0007 del fork): e' da li' che nascono gli
# avvisi precisi del P2P — «paga la garanzia», «gli euro sono partiti».
# Lo stesso valore va nel compose del nodo (`BARATTOLO_EVENTI_SEGRETO`).
# E' UN SEGRETO SUO, diverso da quello dello sconto qui sopra: quello fa
# una DOMANDA (chi lo ruba impara se una chiave ha lo sconto), questo fa
# PARTIRE AVVISI a persone vere — due porte, due chiavi, e si ruotano
# una alla volta. Vuoto o segnaposto = la rotta NON ESISTE (404): gli
# avvisi restano quelli del libro pubblico (presa, concluso, annullato,
# scaduto), che allora partono subito invece di aspettare il coordinatore.
P2P_EVENTI_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"
# Il segreto con cui la RONDA DEL NODO chiede a /api/nodo/pagamenti-noti
# se un pagamento uscito dal nodo e' un payout di Barattolo (28 set
# 2026): risponde solo si'/no per ogni hash. Lo stesso valore va sul nodo
# in /etc/ronda/barattolo.env (`RONDA_SEGRETO`). UN SEGRETO SUO, diverso
# dagli altri due: si ruota da solo. Si genera con `openssl rand -hex 32`.
# Vuoto o segnaposto = la rotta NON ESISTE (404), e la ronda allarma
# dopo tre ore di pagamenti che non ha potuto verificare.
RONDA_NODO_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_CASUALE"
# LA RIGA A OGNI PASSATA DELL'OROLOGIO P2P (17 set 2026): una al minuto
# nel journal, anche quando non trova niente — e' quella che distingue
# «gira a vuoto» da «non gira», che un giorno e' costata un'ora.
# False la spegne; le righe di partenza, di relay muto e di guasto
# restano comunque.
P2P_LOG_PASSATE = True

DB = "satmarket.db"

# --- I relay Nostr ----------------------------------------------------
# Dove Barattolo scrive e legge su Nostr. Erano cinque elenchi scritti
# a mano nel codice, e gia' divergevano fra loro: da qui si cambiano
# senza un deploy, che e' la regola di casa per tutto cio' che il VPS
# decide (l'id del canale, ONION_HOST, le leve dei connettori).
#
# Serve per tre cose vere: puntare a un relay NOSTRO il giorno che ci
# sara'; togliere di mezzo in un riavvio un relay che si comporta male
# invece di aspettare un commit; e i relay che rifiutano gli exit node
# di Tor, dove la strada e' sempre stata «cambiare relay» — cioe',
# finora, un deploy.
#
# ⚠️ SI AGGIUNGE, NON SI SOSTITUISCE: gli eventi vanno a TUTTI i relay
# della lista in parallelo e si contano gli OK, quindi un relay in piu'
# non toglie niente agli altri. Lasciarne almeno un paio di quelli
# grossi e' cio' che tiene gli annunci raggiungibili da chi ha i SUOI
# relay e non i nostri.
RELAY_NOSTR = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://nostr.mom",
]
# I relay che l'IMPORT interroga in piu' — quelli personali dei
# venditori, dove i loro annunci vivono e i grossi non arrivano. Sono
# una lista a parte e non quattro voci in fondo a quella sopra perche'
# hanno un mestiere diverso: qui NON si pubblica, si va a leggere. Un
# doppione fra le due liste si toglie da solo.
RELAY_NOSTR_IMPORT = [
    "wss://21milionidinostr.duckdns.org",   # il relay di un nostro venditore
]

# --- Il relay di Barattolo (chi ci puo' scrivere) --------------------
# Il segreto con cui il NOSTRO relay ci chiede, ogni dieci minuti, la
# lista delle chiavi ammesse a scrivere: la piattaforma e i venditori
# che hanno DIMOSTRATO il possesso della loro (npub_accesso, o il
# badge npub ma verificato). E' un blocco a parte da RELAY_NOSTR
# apposta: quelli sono i relay ALTRUI dove pubblichiamo, questa e' la
# porta da cui il relay nostro viene a chiedere chi far entrare.
#
# Vuoto o segnaposto = la rotta /api/relay/chiavi NON ESISTE (404).
# Il relay non ne muore: tiene la lista che ha gia' scaricato, e
# senza averne mai scaricata una accetta la sola piattaforma.
RELAY_CHIAVI_TOKEN = "INCOLLA_QUI_UN_SEGRETO_CASUALE"

# --- Import da Nostr (usato da importa_nostr.py) ---------------------
NPUB_VENDITORE = "INCOLLA_QUI_LA_NPUB_DEL_VENDITORE"  # npub1… oppure hex
VENDITORE_ID = 222   # a chi intestare gli annunci importati:
                     #  - collaudo: 222 (l'utente finto "Venditore")
                     #  - lancio: il VERO user id Telegram del venditore
                     #    (da @userinfobot); rilanciando lo script gli
                     #    annunci vengono re-intestati automaticamente

# --- Barattolo su Nostr (pubblicazione degli annunci) ----------------
# La chiave DELLA PIATTAFORMA (mai di utenti!) con cui il server firma
# gli annunci come eventi NIP-99. Generane una nuova con un client
# Nostr e incollala SOLO nel config.py del server: mai in chat, mai
# su GitHub. Finche' resta il segnaposto, la funzione e' spenta.
NOSTR_NSEC_PIATTAFORMA = "INCOLLA_QUI_LA_NSEC_DELLA_PIATTAFORMA"
# Chi una chiave Nostr sua ce l'ha vede i propri annunci uscire sul
# PROPRIO account, e a firmare e' il suo browser: la nsec ce l'ha solo
# lui. Se quella chiave non e' a portata di mano — bunker spento,
# estensione assente, o e' entrato con la nsec incollata, che per
# scelta non conserviamo — la firma resta in coda e senza un
# promemoria l'utente non sa nemmeno che quella coda esiste.
# UNO per persona e non per annuncio (dieci annunci farebbero dieci
# messaggi), e dopo il tetto silenzio: chi non collega la chiave ha
# deciso. Niente segnalazione ai moderatori — qui non ci sono sats
# fermi da nessuna parte, solo una vetrina in meno.
# ⚠️ Segue la levetta «💡 Suggerimenti sui miei annunci» del Profilo:
# e' un consiglio su come stanno i propri annunci, cioe' la famiglia
# di messaggi che quella levetta governa.
SOLLECITO_FIRME_GIORNI = 7   # ogni quanto si ribussa (0 = spento)
SOLLECITO_FIRME_MAX = 3      # quante volte in tutto, poi silenzio

# --- Import aperto da Nostr -------------------------------------------
# Barattolo mostra gli annunci NIP-99 che stanno su Nostr: chiunque
# pubblichi in italiano si ritrova in vetrina, e chi non ci vuole
# stare manda una cancellazione (kind 5) dal suo client, che qui
# viene rispettata per sempre. I filtri sono due: la lingua e la
# legge (parole vietate + AI, la stessa moderazione di chi pubblica
# da qui). NON serve elencare nessuna npub: i venditori si deducono
# dal database e la scoperta trova i nuovi da sola.
#
# Nasce SPENTA, ed e' voluto: acceso, il server apre account per
# venditori che non ci conoscono e manda loro un DM di benvenuto. Una
# cosa cosi' si accende di proposito, mai per il solo fatto di aver
# aggiornato il codice sul VPS. Questa riga e' anche l'interruttore
# d'emergenza: rimettila False e riavvia.
# False = nessun relay viene toccato e il mercatino vive come prima
# (l'import dell'unico venditore di ieri si lancia comunque a mano con
# `python importa_nostr.py`, che usa NPUB_VENDITORE / VENDITORE_ID).
IMPORT_NOSTR_APERTO = False

# --- Il trasloco degli annunci su Nostr -------------------------------
# Un annuncio pubblicato da chi NON aveva ancora una chiave Nostr sua
# esce in piazza firmato da BARATTOLO. Il giorno che quel venditore la
# chiave la dimostra (entra con Nostr, collega, abilita l'accesso o
# verifica la npub), gli annunci di ieri resterebbero intestati a NOI
# per sempre — il contrario di quel che il bivio esiste per dire.
# Questo giro li porta da lui: prima nasce il suo evento, POI muore il
# nostro, cosi' l'annuncio non sparisce mai dalla piazza.
#
# Nasce ACCESA, al contrario di IMPORT_NOSTR_APERTO: il deploy da solo
# non cancella NIENTE dai relay. Il giro accoda soltanto una firma, e
# la cancellazione del nostro evento parte dopo che l'utente ha firmato
# dal SUO browser — cioe' dopo un suo gesto, che puo' anche non fare.
# Resta un interruttore perche' cio' che si cancella dai relay non si
# disfa: se qualcosa va storto, False e riavvia.
# ⚠️ La nota kind-1 (Barattolo che RACCONTA l'annuncio ai suoi lettori,
# il gemello del post nel canale) non trasloca: quella resta nostra.
TRASLOCO_NOSTR = True
# Quanti annunci per giro d'orologio. Il primo giro dopo il deploy
# passa sul PREGRESSO, e ogni riga diventa una richiesta di firma a un
# venditore vero: il tetto e' quel che lo spalma invece di chiedere a
# qualcuno venti firme in una volta.
MAX_TRASLOCO_GIRO = 200

# --- La terza via della moderazione (l'AI segnala, l'admin decide) ----
# Un verdetto DUBBIO dell'AI non blocca e non pubblica: l'annuncio
# nasce in stato 'revisione' — invisibile al pubblico esattamente come
# se fosse stato rifiutato — e aspetta che un moderatore lo pubblichi o
# lo rifiuti, dai bottoni ✅/❌ del bot o dal Profilo.
# Il costo e' la CODA, non il rischio: in revisione non c'e' niente
# online. False = il binario di ieri, il dubbio torna a valere come
# vietato — e' il freno d'emergenza, non una scelta.
MODERAZIONE_REVISIONE = True
REVISIONE_ATTESA_ORE = 24    # serve SOLO ai testi onesti verso chi ha
                             # pubblicato («di solito entro N ore»):
                             # non e' una scadenza, non fa scattare
                             # niente — meglio un'attesa dichiarata che
                             # un silenzio
REVISIONE_SOLLECITO_GIORNI = 2  # una notifica aggregata al giorno ai
                             # moderatori finche' la coda non si
                             # svuota (0 = mai). L'annuncio RESTA in
                             # attesa: non va online da solo nemmeno
                             # dopo mille solleciti

# --- Categorie proposte da sola (la coda dei moderatori) --------------
# Dopo ogni giro d'import l'AI guarda gli annunci arrivati dai relay (e
# chiunque sia rimasto in "Altro") e propone dove starebbero meglio: le
# proposte finiscono nella coda "Categorie da sistemare" del Profilo, e
# un moderatore le approva a gruppi. In vetrina non cambia niente
# finche' non le approvi tu.
# Costa pochi centesimi al giorno perche' chiede solo per gli annunci
# NUOVI o cambiati, e non ripropone mai uno spostamento gia' rifiutato.
# False = coda ferma (restano ricategorizza.py e sposta_a_mano.py, che
# si lanciano quando vuoi).
RICATEGORIZZA_AUTO = True

# --- I connettori del negozio (Shopify e WooCommerce) -----------------
# Chi ha gia' un e-commerce lo collega dal Profilo, nella sezione
# «🏪 Catalogo esterno» di «📥 Importa in blocco / catalogo esterno»
# (fino al set 2026 era il cassetto «🏪 Il tuo negozio»; a chi si
# mostra lo decide CONNETTORI_NEGOZIO_PER_TUTTI, qui sotto), e i suoi
# prodotti compaiono qui: prezzo e
# giacenza si tengono in pari da soli, un giro all'ora. E' la terza
# fonte che viene da FUORI, dopo Nostr e l'import CSV.
#
# SOLA LETTURA (fase 1), ed e' la cosa da sapere prima di accendere:
# Barattolo il catalogo lo LEGGE e non lo SCRIVE. Quando si vende qui,
# il magazzino sul negozio dell'utente lo aggiorna LUI — glielo diciamo
# in coda a ogni notifica di vendita — e nel frattempo la giacenza di
# qui resta giusta lo stesso (le vendite non ancora riflesse stanno nel
# registro `connettori_uscite`). Il decremento a monte e' la fase 2, e
# si fara' quando i volumi o una lamentela lo chiederanno.
#
# Nasce SPENTA come IMPORT_NOSTR_APERTO e per la STESSA ragione:
# accesa, il server va a bussare all'API di un negozio di qualcun
# altro con le sue credenziali in mano, crea annunci e manda
# notifiche. Una cosa cosi' si accende di proposito, guardando il
# primo giro col journal aperto — mai per il solo fatto di aver
# aggiornato il codice sul VPS. Questa riga e' anche l'interruttore
# d'emergenza: rimettila False e riavvia (i collegamenti restano in
# tabella, gli annunci dove sono; semplicemente nessuno li rilegge).
# ⚠️ Serve anche CHIAVE_CONTENUTI_DIGITALI: senza, il collegamento si
# rifiuta con un 503 invece di scrivere in chiaro il token di un
# negozio — e' il patto dell'indirizzo di casa.
CONNETTORI_NEGOZIO_APERTI = False

# A CHI SI MOSTRA la porta, finche' il ponte qui sopra e' acceso (set
# 2026). Il collegamento vive in una sezione di «📥 Importa in blocco /
# catalogo esterno», e con questa riga a False la vedono SOLO i negozi
# gia' collegati (anche in pausa o rotti: devono poterli sistemare) e i
# moderatori; per tutti gli altri non c'e', e un collegamento nuovo si
# rifiuta anche se un client lo chiede. Il perche' e' il caso vero: un
# venditore normale trovava nel vecchio cassetto dei campi di
# spedizione, li prendeva per i SUOI costi, e il salvataggio gli
# rispondeva di no. True = la porta torna per tutti.
CONNETTORI_NEGOZIO_PER_TUTTI = False

# Quanti prodotti si leggono per collegamento a ogni giro. Il target
# dichiarato (cataloghi da ~200 articoli) passa tutto in un giro solo.
# ⚠️ ABBASSARLO NON DISTRIBUISCE NIENTE, ed e' la cosa da sapere prima
# di toccarlo: quel che non si legge non si puo' distinguere da quel
# che il venditore ha tolto dal negozio, quindi una lettura corta
# SOSPENDE le sparizioni per quel giro (fino ad ago 2026 le spegneva
# invece, per sempre: 'rimosso' non risorge). Il catalogo oltre il
# tetto semplicemente non entra, e il report lo dice al venditore.
# Per far entrare un catalogo grande un po' per volta c'e' la leva qui
# sotto, che e' un'altra cosa.
# ⚠️ Oltre 250 il catalogo di Shopify comincia a paginarsi davvero, e
# li' il suo limite di richieste al secondo torna a contare: prima di
# alzarlo tanto, va rimessa una pausa dentro il ciclo del lettore.
MAX_PRODOTTI_CONNETTORE = 200

# Quanti annunci NUOVI nascono per collegamento a ogni giro (0 =
# nessun tetto). Il catalogo si legge SEMPRE tutto — quindi le
# sparizioni restano vere e i prezzi di quel che vendi gia' si
# aggiornano come sempre — e a scaglioni entra solo l'INGRESSO in
# vetrina.
# IL CASO CHE LA CHIEDE: la vetrina e' ordinata per data, e un
# catalogo entra tutto nello stesso secondo. Cinque negozi collegati
# insieme sono mille annunci che si prendono le prime pagine, e chi
# vende una cosa sola sparisce. Con trenta all'ora un catalogo da
# duecento entra in una giornata, e la home resta di tutti.
# Non risolve il monopolio della prima pagina: lo diluisce.
MAX_NUOVI_CONNETTORE_GIRO = 30

# Dopo quanti giri falliti di FILA il collegamento si dichiara rotto e
# il venditore riceve UN avviso (uno solo: alla soglia, poi silenzio —
# il patto dei solleciti). Cinque giri sono cinque ore di silenzio, che
# e' un problema vero; un negozio che non risponde per mezz'ora no.
# Gli annunci non si spengono MAI per un errore di lettura: un negozio
# muto non e' un negozio vuoto.
CONNETTORI_ERRORI_MAX = 5

# Quanti negozi puo' collegare un venditore. Due sono il caso vero
# (uno Shopify e un Woo, oppure il negozio e il magazzino), tre
# lasciano aria; oltre non e' piu' «il mio negozio».
MAX_CONNETTORI_VENDITORE = 3

# Ogni quanto si puo' chiedere A MANO una rilettura col bottone
# «🔄 Aggiorna ora», in secondi. Il freno non e' per noi: e' per il
# server di qualcun altro, che ha i suoi limiti di richieste. Il
# timbro si scrive anche sui giri FALLITI, cosi' un negozio rotto non
# si puo' martellare col bottone; il giro automatico dell'ora resta
# comunque.
CONNETTORI_SYNC_MANUALE_S = 300

# Il tetto sulle tariffe di spedizione dichiarate nel cassetto, in
# euro. Non e' un giudizio su quanto costi spedire — quello lo sa il
# venditore, non noi, com'e' per MAX_QUANTITA_ANNUNCIO — e' la
# cintura contro lo zero in piu' battuto per sbaglio.
MAX_TARIFFA_CONNETTORE = 500.0
# ...e il gemello in SATS (set 2026), per chi dichiara le tariffe del
# negozio collegato in sats fissi col bottoncino sats ⇄ €: stessa
# cintura, stessa ragione.
MAX_TARIFFA_CONNETTORE_SATS = 1_000_000

# --- Post automatici (la piattaforma racconta i fatti) ----------------
# Ogni nuovo annuncio in vetrina viene annunciato dai canali di
# Barattolo: una nota Nostr (con la chiave piattaforma qui sopra) e un
# post nel canale Telegram. Attivo di default; False per spegnere tutto.
POST_AUTOMATICI = True
# Il canale Telegram di Barattolo: "@nomecanale" oppure l'id numerico
# (-100...). Il bot deve esserne AMMINISTRATORE. Vuoto = niente post
# sul canale (la nota Nostr vive comunque).
# ATTENZIONE (ago 2026): questo e' solo il valore di PARTENZA. Il
# canale si cambia dal bot con «/canale @nomecanale» (lo possono dare
# i moderatori e i due username in ADMIN_BOT_USERNAME), e da quel
# momento comanda la scelta salvata nel database — questa riga non la
# tocca piu'. «/canale» senza argomenti dice qual e' quello in uso.
TELEGRAM_CANALE_ID = ""
# Dove va il RIEPILOGO del lunedi': vuoto = dove vanno gli annunci.
# Anche questo e' solo il valore di PARTENZA — si cambia dal bot con
# «/canale riepilogo @nomecanale». Il bot dev'essere amministratore
# anche di questo, e puo' essere un canale diverso dall'altro.
TELEGRAM_CANALE_RIEPILOGO = ""
# Il canale della COMUNITA' (ago 2026): un canale di TERZI dove i
# nostri annunci nuovi compaiono per farci conoscere — oggi
# @subito_crypto_vetrina. Vuoto = non ci si posta, e NIENTE ripiego
# sul nostro: un canale altrui non e' un posto dove finire per
# distrazione. Si cambia dal bot con «/canale vetrina @nomecanale»,
# e il bot dev'essere amministratore di quel canale.
# LI' DENTRO ENTRANO SOLO gli annunci di chi ha un @username Telegram:
# e' la maniglia che quel pubblico si aspetta, e un post senza
# menzione in casa d'altri e' un volantino.
TELEGRAM_CANALE_VETRINA = ""
# ATTENZIONE (ago 2026): come per il canale, i tre numeri qui sotto
# sono il valore di PARTENZA. Il ritmo si sceglie dal bot con
# «/vetrina tutto | giorno | settimana» e da quel momento comanda la
# posizione salvata nel database; «/vetrina» senza argomenti dice
# dov'e' adesso, «/vetrina config» torna a queste righe.
# Anti-spam: quanti post SINGOLI al massimo in un'ora. Oltre (o per le
# raffiche, es. un import CSV) esce un solo post aggregato
# ("N nuovi annunci nel barattolo").
POST_MAX_ORA = 6
# UN POST PER VENDITORE OGNI N GIORNI: se il canale e' una selezione,
# un negozio che pubblica venti cose in un pomeriggio non deve
# prendersi venti post. Il post esce SUBITO (l'annuncio non aspetta
# una settimana per farsi vedere) e da li' il venditore tace per N
# giorni; se in quel momento ne ha pubblicati piu' d'uno, esce il piu'
# recente. 0 = nessun freno, cioe' la vetrina vera.
PROMO_GIORNI_VENDITORE = 7
# Gli SCONTI LAMPO nel canale: quando un venditore lancia uno sconto a
# tempo, il canale lo racconta con un post suo (il post dell'annuncio
# non si tocca — il listino e' ancora quello). Leva sua e non un ramo
# di POST_AUTOMATICI, cosi' si spengono gli sconti senza spegnere
# anche gli annunci nuovi. Consuma il budget di POST_MAX_ORA.
# SPENTA di serie (ago 2026): nel canale gli sconti non compaiono come
# messaggi nuovi — si vedono in vetrina, col badge e il prezzo
# barrato. True per raccontarli anche qui.
POST_LAMPO_CANALE = False

# --- Il riepilogo settimanale ----------------------------------------
# Il LUNEDI' il canale racconta la settimana: quanti annunci nuovi,
# quanti ordini e i tre articoli piu' venduti. Solo canale (su Nostr
# il pubblico e' un altro). Una volta per lunedi', anche con dieci
# deploy in mezzo.
RIEPILOGO_SETTIMANALE = True
# Sotto tanti annunci nuovi E senza nemmeno un ordine non esce niente:
# un riepilogo che dice «0 ordini» fa piu' danno del silenzio. Il
# turno della settimana si consuma lo stesso — il lunedi' dopo si
# ricomincia da capo con una finestra nuova.
RIEPILOGO_MINIMO = 3
# IL PODIO: i tre piu' venduti disegnati come tre barattoli, con
# dentro la foto dell'articolo, allegati al riepilogo. La didascalia
# resta quella di sempre coi titoli: la figura si AGGIUNGE, e se non si
# compone (manca Pillow, o non c'e' classifica) esce il post di testo.
# Un articolo senza una nostra foto — importato da Nostr, o senza foto
# — resta un barattolo di vetro vuoto, che nel nostro alfabeto e' una
# figura e non un buco.
RIEPILOGO_IMMAGINE = True

# --- La raffica raccontata per negozio --------------------------------
# Quando piu' annunci arrivano insieme, chi ne ha pubblicati almeno DUE
# ha un post SUO: la figura coi barattoli in fila e un link per
# annuncio, invece di sparire dentro un «N nuovi annunci» che non
# nomina nessuno. Il TETTO e' quel che tiene la valvola una valvola:
# oltre — e per chi ne ha pubblicato uno solo — resta l'aggregato
# anonimo di sempre.
MAX_NEGOZI_RAFFICA = 3
# Quanti link nella didascalia. Il tetto vero e' quello di Telegram
# (1024 caratteri per una caption): dieci righe con titolo e prezzo ci
# stanno comode, e oltre si dice quanti ne restano.
MAX_LINK_NEGOZIO = 10

# --- Avviso "fase di test" (il cartello all'apertura) ----------------
# Il cartello che accoglie chi apre l'app durante il rodaggio: si
# mostra UNA VOLTA AL GIORNO per dispositivo, a tutti (anche a chi
# guarda la vetrina da anonimo), mai nella demo coi dati finti.
# A rodaggio finito basta rimettere False: nessun cantiere.
BANNER_TEST = False
# La PRIMA riga diventa il titolo del cartello, il resto il messaggio.
BANNER_TEST_TESTO = """🚧 Barattolo è in fase di test.
Nei prossimi giorni integriamo il fornitore per le spedizioni (nel rispetto della privacy di ognuno) e sveleremo tutte le meccaniche d'acquisto.
Per ora esplora liberamente e contribuisci allo sviluppo: un feedback, un'opinione, una funzione che vorresti.
🎁 Un vantaggio dedicato ai primi 100 pionieri che ci aiuteranno a migliorarlo.
👉 Entra nel canale: dentro trovi il post fissato 📋 dove lasciare i tuoi feedback."""
# Dove porta il bottone "Entra nel canale". Vuoto = niente bottone.
BANNER_TEST_LINK = ""

# --- Contatore degli utenti (in vetrina, sotto gli oggetti) ----------
# "54 utenti": quante persone sono già entrate nel mercatino (tutti gli
# iscritti, non solo i primi 100 pionieri).
# In rodaggio è un invito ad esserci; False lo spegne, e la riga
# sparisce dalla vetrina senza altro da toccare.
CONTATORE_UTENTI = True

# --- Campanello dei nuovi iscritti (solo ai moderatori) --------------
# «👥 Nuovo pioniere: Marco (@marco_b) — da Telegram. Siamo in 25.»
# Arriva SOLO agli ADMIN_IDS, mai sul canale pubblico. Ogni 10 minuti
# il server guarda chi è entrato: pochi = un messaggio ciascuno, una
# raffica = un solo messaggio col conto, senza nomi. In più un avviso
# ai traguardi (50, 100, 250, 500, 1000 pionieri).
AVVISI_ISCRITTI = True
# Quanti messaggi SINGOLI al massimo in un'ora: oltre questo tetto
# restano solo gli aggregati (che non nominano nessuno).
AVVISI_ISCRITTI_MAX_ORA = 6

# Il polso degli ordini: una riga ai moderatori quando un ordine nasce
# (sats in cassaforte) o si chiude (released/rimborso/disputa), col
# conto di quelli ancora aperti. Solo titolo e importi, mai nomi.
AVVISI_ORDINI_ADMIN = True

# --- Sicurezza degli accessi ------------------------------------------
# Quanto vale un initData di Telegram: e' la credenziale di OGNI
# chiamata dentro la Mini App, quindi senza scadenza uno catturato
# oggi apre quell'account per sempre. Ventiquattro ore e non cinque
# minuti perche' l'initData NON si rinfresca finche' la Mini App resta
# aperta: solo riaprirla ne conia uno nuovo, e una finestra corta
# butterebbe fuori chi la tiene minimizzata.
# 0 = spenta, cioe' si torna a un initData che non scade mai: e' un
# freno d'emergenza, non una scelta.
ORE_INITDATA = 24

# PIU' ACCOUNT SULLO STESSO BROWSER (ago 2026): quante identita' si
# tengono aperte insieme e si scambiano dal Profilo senza rifare il
# login — il caso vero e' «il mio account e quello del negozio».
# Vale SOLO su web e PWA: dentro Telegram l'identita' la impone il
# client (l'initData firmato), e li' non c'e' niente da scegliere.
# Ogni account in piu' e' un token nel cookie del portachiavi (~43
# caratteri): il tetto non protegge dal peso, tiene corta una lista
# che si legge con un dito. Al limite cede il piu' VECCHIO, mai
# l'account su cui si e' appena entrati.
MAX_ACCOUNT_BROWSER = 5

# LA RICERCA NON HA PIU' UNA QUOTA (ago 2026): `TETTO_RICERCHE_AI_ORA`
# frenava le chiamate ad Anthropic della ricerca, e la ricerca non
# chiama piu' nessuno — e' un indice full-text dentro SQLite. Una riga
# rimasta qui e' inerte e si puo' togliere.
#
# Quel che le serve e' un PACCHETTO, non una leva:
#     pip install snowballstemmer
# E' lo stemmer italiano (Python puro, ~100 KB, nessuna dipendenza:
# l'algoritmo Snowball che sta sotto Lucene ed Elasticsearch), ed e'
# quello che fa trovare «collezione» cercando «collezionismo».
# Senza, il server parte lo stesso e la ricerca lavora a troncamento:
# piu' grossolana, mai muta — e l'avvio lo dice con una riga.

# --- La porta dell'iframe (ago 2026, col widget) ---------------------
# Accesa, nessun sito estraneo puo' incorniciare Barattolo in un
# iframe (tranne il widget, che esiste apposta). NASCE SPENTA, cioe'
# com'e' sempre stato: e' una stretta in piu' su una porta rimasta
# aperta, e il widget funziona identico senza.
# PRIMA DI ACCENDERLA, provare la Mini App da TELEGRAM WEB (il browser,
# non l'app): li' gira dentro un iframe di web.telegram.org, ed e' la
# sola strada che questa leva puo' chiudere.
PROTEGGI_IFRAME = False

# --- L'altra porta: il servizio nascosto Tor (ago 2026) --------------
# L'indirizzo `.onion` da cui Barattolo si raggiunge anche da Tor, SENZA
# schema e senza porta: e' un HOST e si confronta con l'header Host.
# Lo scrive Tor in /var/lib/tor/barattolo/hostname quando crea il
# servizio nascosto; il blocco che lo serve vive nel Caddyfile.
# VUOTO = la funzione non esiste, ed e' il patto delle leve che nascono
# spente: senza questa riga il server non ha modo di sapere che l'onion
# esiste, e ogni pagina esce esattamente com'e' sempre stata.
#
# CAMBIA UNA COSA SOLA, e solo alle richieste che arrivano da li': la
# pagina non porta lo script di telegram.org. Fuori da Tor quello
# script non protegge nessuno (si e' gia' su barattolo.store), ma su
# onion e' la contraddizione piu' grossa che ci sia — uno arriva dal
# tunnel e la prima richiesta del browser esce verso Telegram col suo
# IP vero.
#
# ⚠️ LA CHIAVE E' L'INDIRIZZO: un onion v3 non e' registrato da
# nessuna parte, l'indirizzo si DERIVA dalla chiave in
# /var/lib/tor/barattolo/. Persa quella, e' perso per sempre e va
# annunciato di nuovo. Sta nell'archivio cifrato di
# `deploy/backup-fuori.sh` insieme al torrc, ed e' li' che si guarda
# prima di migrare la macchina.
ONION_HOST = ""

# Quanto resta buono un cambio BTC/EUR che non riusciamo a rinfrescare.
# L'ultimo cambio letto vive nel database e torna in cache a ogni
# riavvio (prima la cache nasceva vuota, e un deploy dentro
# un'interruzione di CoinGecko lasciava l'app senza saper convertire:
# pagina d'acquisto bloccata sui listini in euro). Ma un valore che
# sopravvive ai riavvii puo' invecchiare per sempre, quindi oltre
# queste ore torna a essere «non disponibile» — il ripiego onesto di
# sempre — invece di far pagare a qualcuno la cifra di ieri.
# 0 = non scade mai: freno d'emergenza, non una scelta.
ORE_CAMBIO_VALIDO = 24

# Ogni quanti secondi si rilegge il cambio, in un giro di sfondo suo.
# Da quando la fonte e' UNA SOLA (il client non chiama piu' CoinGecko
# per conto suo, il cambio gli arriva dalla vetrina) questa cadenza e'
# la freschezza che vede chiunque guardi un prezzo: un minuto e' il
# ritmo con cui il numero cambia davvero. La soglia oltre la quale il
# percorso caldo va a rileggerlo da se' NON e' un secondo numero: si
# ricava da qui (due giri di slack, minimo 120s).
# Un minuto sono ~1.400 chiamate al giorno da un IP solo: comodamente
# dentro il limite al minuto dell'endpoint pubblico di CoinGecko, ma
# BEN OLTRE le 10.000 al mese di una chiave Demo gratuita — se un
# giorno se ne mette una, questo numero va alzato (300 = ~9.000/mese).
# Si alza anche se CoinGecko comincia a rispondere 429.
# 0 = niente giro di sfondo: una lettura all'avvio e poi se ne occupa
# il percorso caldo, col suo raffreddamento da un minuto.
CAMBIO_RINFRESCO_S = 60

# --- La classifica del mercatino --------------------------------------
# Chi sono i migliori, in una pagina sola: media pesata sulle PERSONE
# che ti hanno votato, moltiplicata per il commercio (i soli XP degli
# ordini, compressi col logaritmo). Entra chi ha almeno un affare
# concluso e almeno un voto da un «recensore reale» — uno che a sua
# volta ha commerciato con qualcun altro: chi si fabbrica venti
# identita' e se le fa votare non entra affatto.
# Il bonus del commercio si smorza con quante persone ti hanno
# votato: la fiducia di uno solo non amplifica come quella di venti.
# NASCE SPENTA, e non perche' muova denaro: perche' nessuno sa quante
# righe escono finche' non si guarda. Il conto lo da'
# `python classifica_prova.py`, che legge e basta.
CLASSIFICA_ATTIVA = False
CLASSIFICA_TOP = 20             # quanti nomi escono in pubblico. Chi sta
                                # sotto vede solo la SUA posizione, e a
                                # nessun altro esce.
CLASSIFICA_K = 5                # quanto pesa la media del mercatino su
                                # chi ha pochi voti: alto = piu' severo
                                # coi nuovi, basso = una recensione sola
                                # decide. 5 = servono ~5 persone perche'
                                # la tua media conti per meta' come tua,
                                # ed e' il valore MISURATO che fa passare
                                # «4,8 da 50 persone» davanti a «5,0 da
                                # 2»: con 3 vinceva ancora chi ha due voti.
CLASSIFICA_XP_RIF = 1000        # gli XP-ordine che valgono il bonus
                                # pieno (~1.000 € commerciati da
                                # venditore). Oltre si continua a
                                # salire, ma pianissimo: e' un
                                # logaritmo.
CLASSIFICA_PESO_XP = 0.25       # quanto puo' contare il commercio, al
                                # massimo: +25% sulla fiducia. 0 = la
                                # classifica torna la sola media.
CLASSIFICA_KD = 0               # quante persone servono perche' il bonus
                                # del commercio conti PIENO: con due, chi
                                # ha un recensore solo si prende un terzo
                                # del suo bonus, chi ne ha 5 cinque
                                # settimi, chi ne ha 20 quasi tutto —
                                # la fiducia di uno solo e' un'opinione,
                                # non un curriculum. Alzalo e il commercio
                                # parla solo a chi ha molta gente dietro.
                                # 0 = il bonus pieno per chiunque, cioe'
                                # la classifica di prima dello
                                # smorzamento; mai negativo (un meno vale
                                # come zero). Il valore si SCEGLIE
                                # guardando i numeri veri: la sezione 3
                                # di `classifica_prova.py` affianca le
                                # tarature sulla classifica vera.

# --- Collaudo ---------------------------------------------------------
# False = com'e' giusto che sia online: nessuna identita' finta.
# True  = test locale con gli utenti finti (Compratore/Venditore/Admin),
#         e si mette A MANO quando si lavora sul portatile.
# Nasce spento come IMPORT_NOSTR_APERTO e ASTA_ABILITATA, e per la
# stessa ragione: acceso, l'header «collaudo:111» apre l'account di
# chiunque senza una firma: chi copia questo modello per il server non
# deve poterselo portare dietro per distrazione. Accenderlo dev'essere
# un gesto, e in locale e' il primo che si fa.
MODALITA_COLLAUDO = False
