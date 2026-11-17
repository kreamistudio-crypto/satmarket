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
# I LINK DENTRO TELEGRAM APRONO LA MINI APP (10 ott 2026): l'indirizzo
# con cui Telegram apre la Mini App, a cui il server attacca
# `?startapp=<parametro>` — nel bottone degli avvisi P2P («⚡ Apri lo
# scambio»), nel link «🫙 Apri il libro ordini» dell'avviso dei nuovi
# ordini, in «🫙 Apri lo Scambio P2P su Barattolo» del post P2P nel
# canale, nella riga «🫙 Apri Barattolo» delle tastiere del bot, in «🫙
# Sfoglia il mercatino» del riepilogo del lunedi', in «🫙 Apri Esplora»
# degli avvisi del mercatino (col reparto e il prezzo massimo di chi lo
# riceve) e nei link P2P che la Mini App condivide verso una chat. Chi li
# tocca dentro Telegram atterra nella Mini App, gia' entrato, sullo
# scambio, sull'ordine, sul libro, su Esplora o sulla home; fuori da Telegram (Nostr,
# WhatsApp, il browser) i link restano barattolo.store, e i link degli
# ANNUNCI restano sempre quelli del sito (portano la foto in anteprima).
# DUE FORME, e quale vale lo dice BotFather:
#   "https://t.me/ilbarattolobot"        la Mini App PRINCIPALE del bot:
#       va accesa in BotFather (/mybots > il bot > Bot Settings >
#       Configure Mini App > Enable Mini App), con l'indirizzo del sito;
#   "https://t.me/ilbarattolobot/<app>"  una Mini App col suo nome breve,
#       creata in BotFather. ⚠️ La procedura NON e' nella documentazione
#       ufficiale di Telegram (cercata il 10 ott 2026: ne' il comando ne'
#       le misure dell'immagine): la dice BotFather stesso, passo per
#       passo. Di ufficiale c'e' solo che l'app ha un titolo, una
#       descrizione, una FOTO obbligatoria, un'animazione facoltativa e
#       il nome breve, e che in chat il suo link mostra quella foto con
#       un bottone che apre la Mini App.
# ⚠️ VUOTA NEL CODICE, e si accende SOLO dopo aver guardato BotFather:
# un link `?startapp=` verso un bot senza la Mini App principale apre la
# chat del bot e basta, e la destinazione si perde. All'avvio il server
# lo chiede a Telegram (getMe): se il bot del link non e' questo bot, o
# la Mini App principale non c'e', la leva si spegne da sola e il
# journal dice perche' («⚠️ Link dentro Telegram SPENTI»). Una forma
# storta la spegne. Il valore vivo sta nel pannello «⚙️ Stato delle leve».
TELEGRAM_MINIAPP_LINK = ""
# L'INDIRIZZO DEL SITO E IL BOT (19 ott 2026): servono SOLO all'istanza
# di prova (sezione in fondo); in produzione non si scrivono, e valgono
# questi. URL_PUBBLICO e' dove il bot registra il webhook e dove puntano
# i link delle notifiche, della sitemap e delle condivisioni: https,
# minuscole, senza barra in fondo. LINK_BOT e' il bot dei link «apri il
# bot» e del login dal browser: il server ne scrive il nome anche nella
# Mini App. Scritti male restano questi, e il journal lo dice. Con
# TELEGRAM_MINIAPP_LINK accesa, il `getMe` dell'avvio controlla anche
# che LINK_BOT sia il bot del BOT_TOKEN («⚠️ LINK_BOT dice @…»).
URL_PUBBLICO = "https://barattolo.store"
LINK_BOT = "https://t.me/ilbarattolobot"
# Il bottone «💬 Chiedi a Tappo» nel bot (16 nov 2026): il link del bot di
# Tappo. Vuota ("") = niente bottone.
TAPPO_LINK = "https://t.me/TappoBarattoloBot"

# --- Anthropic (ricerca AI in linguaggio naturale) -------------------
ANTHROPIC_API_KEY = "INCOLLA_QUI_LA_API_KEY"
MODELLO_RICERCA = "claude-haiku-4-5"

# --- L'assistente del bot (28 ott 2026, cantiere bot-assistente) -----
# Chi scrive una domanda al bot riceve la risposta di Claude, che si
# presenta come assistente automatico, sa solo il libro del sapere
# (assistente/sapere.md, testi pubblici) e i numeri pubblici delle leve,
# non vede ne' nomi ne' ordini, e non fa niente: risponde a parole. Sotto
# ogni risposta c'e' «🙋 Parla con una persona» (la porta privata, e un
# avviso ai moderatori nell'argomento «assistenza»). SPENTO di serie.
ASSISTENTE_AI_ATTIVO = False
# a leva accesa, risponde solo agli admin: la prova in casa prima di
# aprirlo a tutti (False = a tutti)
ASSISTENTE_SOLO_MODERATORI = True
# LA SUA chiave, separata da quella della moderazione: nella Console di
# Anthropic le si da' un LIMITE DI SPESA, che e' il freno vero dei soldi.
# Sul VPS si scrive col read -s (PRODUZIONE), mai a mano in un editor.
ASSISTENTE_API_KEY = "INCOLLA_QUI_LA_API_KEY"
ASSISTENTE_MODELLO = "claude-sonnet-5-5"
ASSISTENTE_MAX_AL_GIORNO = 30    # domande al giorno per persona
ASSISTENTE_TETTO_GIORNO = 300    # domande al giorno in tutto (RAM: un
                                 # riavvio li azzera, il limite di spesa no)
# Tappo, il bot del canale su n8n (13 nov 2026, cantiere tappo-economico):
# il modello di BASE risponde a tutto, l'ESPERTO solo quando quello di
# base non e' sicuro. n8n li rilegge da /api/assistente/numeri; si
# cambiano anche dal pannello «⚙️ Stato delle leve».
TAPPO_MODELLO_BASE = "claude-haiku-5-5"
TAPPO_MODELLO_ESPERTO = "claude-sonnet-5-5"

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

# LA GUARDIA DELLA LIQUIDITA' (11 ott 2026): ogni ora il server legge i
# canali del nodo dal ponte (col macaroon di sola lettura qui sotto) e
# avvisa su Telegram — agli stessi del guardiano del ponte — quando il
# nodo non puo' piu' fare gli scambi, quando torna a posto, e in mezzo
# al massimo un promemoria al giorno. Ogni avviso porta la grafica dei
# canali; `/canali` nel bot (solo admin) la mostra quando si vuole,
# anche a guardia spenta. Tre domande: l'entrata totale regge la
# garanzia piu' grossa? chi paga da Phoenix ha una strada (il canale
# ACINQ diretto, o un'altra che LND trova)? l'uscita totale sta sopra il
# minimo? E, a leva accesa, il canale con piu' uscita regge da solo un
# ordine P2P al tetto? Vedi docs/PRODUZIONE.md, «LA GUARDIA DELLA
# LIQUIDITA'».
GUARDIA_LIQUIDITA = False          # True = accesa
LIQUIDITA_SCAMBIO_MAX = 500000     # la garanzia piu' grossa (sats): lo
                                   # specchio di max_order_amount del nodo
LIQUIDITA_PHOENIX_MIN = 300000     # quanto deve poter entrare da Phoenix
LIQUIDITA_USCITA_MIN = 0           # 0 = nessun minimo d'uscita
LIQUIDITA_USCITA_CANALE = False    # True = il canale con piu' uscita
                                   # regge da solo un ordine al tetto
                                   # P2P_MAX_EURO (al cambio di adesso)
LIQUIDITA_ACINQ_TETTO = False      # True = il tetto degli appesi di
                                   # ACINQ (450k sul canale da 1M) lascia
                                   # entrare LIQUIDITA_PHOENIX_MIN?
# La sesta domanda (27 ott 2026): per ogni cassaforte, saldo del wallet
# meno gli incassi in attesa sopra questa percentuale del totale in attesa
# più i sats fissi (LNbits tiene l'1 % per le commissioni, sennò i
# pagamenti si fermano). Tutt'e due a 0 = domanda spenta.
LIQUIDITA_MARGINE_PERCENTO = 1
LIQUIDITA_MARGINE_MIN_SATS = 10000
LIQUIDITA_PROMEMORIA_S = 86400     # fra un promemoria e l'altro
LIQUIDITA_OGNI_S = 3600            # ogni quanto guarda

# LA VERITA' DEI PAGAMENTI IN USCITA (set 2026): prima di decidere o di
# ritentare un pagamento, il server chiede com'e' finito anche a LND,
# attraverso lo stesso ponte di LNbits. Serve un macaroon SUO, di SOLA
# LETTURA — sul nodo:
#   lncli bakemacaroon --root_key_id 2 --save_to lettura.macaroon offchain:read info:read
#   xxd -p -c 9999 lettura.macaroon
# — perche' questo e' un server web pubblico, e una chiave che sa pagare
# qui dentro non ci entra. Vuoto = LND «spento»: decide LNbits da sola,
# come prima. Vedi docs/PRODUZIONE.md, «I PAGAMENTI DA VERIFICARE».
# `info:read` c'e' dal 10 ott 2026 (cantiere controllo-fattura): serve
# al controllo della fattura di chi compra nel P2P (`getnodeinfo` e
# `queryroutes`); col macaroon di prima, solo `offchain:read`, quel
# controllo risponde «non si sa» e lascia passare — vedi PRODUZIONE,
# «IL CONTROLLO DELLA FATTURA P2P».
LND_PONTE_MACAROON_LETTURA = ""          # esadecimale, tutto su una riga
LND_PONTE_CERT = "/opt/lnbits/data/tls.cert"   # il tls.cert di LND
LND_PONTE_URL = "https://127.0.0.1:18080"      # lnd-ponte (socat + tor)
# LE HOLD DI PROVA (10 ott 2026, cantiere prova-hold): i bottoni G e H di
# `/prova-wallet` coniano due hold invoice da 1 sat sul nodo, che si
# cancellano da sole dopo tre minuti e non si saldano MAI. Vogliono un
# macaroon SUO, cotto sul nodo coi soli tre metodi (niente settle per
# costruzione), `root_key_id 4` cosi' si revoca da solo:
#   lncli bakemacaroon --root_key_id 4 --save_to hold.macaroon uri:/invoicesrpc.Invoices/AddHoldInvoice uri:/invoicesrpc.Invoices/CancelInvoice uri:/lnrpc.Lightning/LookupInvoice
#   xxd -p -c 9999 hold.macaroon
# Vuoto = G e H «non attive», e la pagina esce lo stesso. Vedi
# docs/PRODUZIONE.md, «LE HOLD DI PROVA».
LND_PONTE_MACAROON_HOLD = ""             # esadecimale, tutto su una riga

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
DB_BUSY_TIMEOUT = 15         # secondi che una connessione aspetta sul
                             # lucchetto di sqlite prima di dire
                             # «database is locked» (1 ott 2026). Copre
                             # il backup che tiene il file in lettura;
                             # le scritture lunghe non si curano da qui
                             # ma rendendole brevi
SENTINELLA_ATTIVA = True     # la sentinella del server fermo (17 nov
                             # 2026): se /api/salute tace, la pila dei
                             # fili nel journal, e muto da 3 minuti il
                             # server esce e systemd lo rialza. False =
                             # spenta (solo per emergenza)
MAX_PREFERITI = 10           # quanti annunci ATTIVI stanno «nel tuo
                             # barattolo». Piccolo apposta: e' una
                             # selezione, non una lista dei desideri
                             # infinita. Contano solo gli attivi —
                             # comprare qualcosa che c'e' dentro
                             # libera spazio da solo
# LA MODIFICA DI PIU' ANNUNCI INSIEME (16 ott 2026): in «I tuoi
# annunci» il venditore ne sceglie fino a 100 e cambia in un colpo
# prezzo (fisso o in percentuale), quantita', costo standard di
# spedizione, categoria, pausa, riattivazione o li elimina — con
# l'anteprima e l'«↩︎ Annulla» per 24 ore. Nasce SPENTA finche' Andrea
# non l'ha provata; spenta, il bottone non c'e' e le rotte dicono 404.
# Solo True accende: una stringa o un numero restano spenti.
MODIFICA_MASSIVA_ATTIVA = False

# MERCATO E LAVORO (24 ott 2026, decisione di Andrea): in cima alla
# vetrina due schede, «🛍️ Mercato» e «💼 Lavoro», alla Subito.it; i
# servizi stanno solo in Lavoro, coi loro scaffali. Nasce SPENTA:
# spenta, la vetrina e' quella di sempre (niente schede, i servizi in
# «Tutto» e nella loro categoria). Sul collaudo e' accesa. Solo True
# accende.
MERCATO_LAVORO = False

# LA MAPPA DEL RITIRO A MANO (14 nov 2026, decisione di Andrea): in fondo
# alla barra di ricerca un tondo 🗺️ apre la mappa dell'Italia coi comuni
# degli annunci col ritiro a mano (il centro del comune della «Zona», mai
# l'indirizzo); un tocco su un comune mostra solo i suoi. Nasce ACCESA
# (Andrea, 14 nov: «fallo salire gia' con la leva accesa»): la riga serve
# per SPEGNERLA, e solo False spegne — spenta, niente tondo e la vetrina
# di sempre.
MERCATINO_MAPPA_RITIRO = True

# IL FEEDBACK SI MODIFICA E SI CANCELLA, PER UN PO' (14 nov 2026,
# decisione di Andrea): chi ha lasciato un feedback (o una recensione di
# uno scambio P2P) puo' modificarlo UNA volta o cancellarlo entro
# FEEDBACK_MODIFICA_GIORNI giorni da quando l'ha lasciato; poi e'
# definitivo. Cancellato, su quell'affare non se ne lascia un altro. Un
# voto da 1-2 stelle alzato o cancellato arriva ai moderatori
# (argomento «moderazione»). Nasce ACCESA (le leve nuove sono accese di
# serie): la riga serve per SPEGNERLA, e solo False spegne. I giorni:
# da 0 (nessuna finestra = definitivi) a 90.
FEEDBACK_MODIFICABILE = True
FEEDBACK_MODIFICA_GIORNI = 7

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
# UN CODICE ALLA VOLTA (16 nov 2026): da due pezzi in su (es. 10 buoni)
# chi vende scrive un codice per riquadro e chi compra vede il successivo
# solo dopo aver detto che il precedente funziona. In disputa i codici
# confermati sono pagati a chi vende, quelli mai aperti tornano a chi
# compra. Acceso di serie; False = interruttore d'emergenza: gli ordini
# nuovi tornano al campo unico (quelli gia' a riquadri restano cosi').
CODICI_UNO_ALLA_VOLTA = True

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
# L'invito del codice ai clienti (14 nov 2026): «📣 Condividi» sulla riga
# del codice, il venditore sceglie fra chi ha gia' comprato da lui e
# Barattolo recapita (bot, DM Nostr o avviso in app). ACCESO di serie.
CODICI_SCONTO_INVITI = True       # False = niente tasto, la rotta dice 409
CODICI_SCONTO_INVITI_GIORNI = 7   # al piu' un invito ogni N giorni dallo
                                  # stesso negozio (0 = nessuna cintura)
CODICI_SCONTO_INVITI_MAX = 200    # inviti per volta: gli altri restano
                                  # invitabili al giro dopo

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

# --- L'avviso «indica i tuoi corrieri» (12 ott 2026) -----------------
# Dal cantiere «punti-ritiro» il ritiro in un punto si offre solo dove
# il venditore ha dichiarato un corriere che a quei punti consegna
# (Poste Italiane, SDA, InPost). Accendendo questa leva parte UN
# messaggio in chat, una volta sola, ai venditori con annunci a
# spedizione attivi e nessun corriere dichiarato: «indica i tuoi
# corrieri per offrire anche il ritiro nei punti».
# SPENTA DI SERIE: un messaggio a tutti i venditori non parte da solo
# con un deploy. Si accende qui e si riavvia; partita una volta non
# riparte (timbro nel database), e rispegnerla non serve.
AVVISO_CORRIERI_PUNTI = False

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
# LO SWAP DEGLI INCASSI (ott 2026): il venditore potra' ricevere
# l'incasso in bitcoin on-chain con uno swap di SATS Routing, non
# custodial. Acceso, il quarto tasto della nav diventa «Swap» e le
# aste si raggiungono dal tasto «🔨 Aste» in cima a Esplora. Resta
# SPENTO in produzione finche' non ci sono il testo firmato di SATS
# Routing e il parere legale (MiCA/CASP).
SWAP_ATTIVO = False          # False = la cella resta «Aste»
# Il codice partner che SATS Routing crea per Barattolo: va in ogni
# chiamata API dello swap, e conta a nostro nome la quota del 10 % della
# loro commissione (accordo con Massimo, 19 ott 2026). Non e' un segreto.
SWAP_REFERRAL_ID = ""        # vuoto finche' non arriva da SATS Routing
# Le DUE CHIAVI per leggere la quota da SATS Routing (/v2/referral/fees,
# firmata con l'HMAC): SEGRETE. Non si scrivono qui ne' a mano: sul VPS
# le chiede il comando col `read -s` di PRODUZIONE («LE CHIAVI DEL
# CODICE PARTNER DI SATS ROUTING»). Vuote = la quota non si legge.
SWAP_REFERRAL_API_KEY = ""
SWAP_REFERRAL_API_SECRET = ""
# LA TAPPA 2, IL PREVENTIVO (ott 2026). A leva dello swap accesa, di
# serie lo vedono solo i moderatori (ADMIN_IDS): False = tutti i venditori.
SWAP_SOLO_MODERATORI = True
# I tetti di ogni swap sulla cifra che spetta al venditore (vale anche il
# limite di SATS Routing: vince il piu' stretto). 0 nel massimo = solo il loro.
SWAP_MIN_SATS = 25_000
SWAP_MAX_SATS = 50_000
# LA TAPPA 4 (24 ott 2026): Barattolo paga la fattura dello swap coi sats
# dell'ordine. I tetti sul giorno (ultime 24 ore, ogni pagamento non
# fallito): per chi vende e per tutti insieme.
SWAP_MAX_SATS_UTENTE_GIORNO = 100_000
SWAP_MAX_SATS_GIORNO = 200_000
# La nostra fee sullo swap, in percentuale: 0 = spenta (la quota del 10 %
# della loro commissione non costa niente a chi vende).
SWAP_FEE_PERCENTO = 0
# LO SWAP AUTOMATICO (2 nov 2026): chi vende in Lightning e ha scelto nel
# Profilo di ricevere on-chain conferma sull'ordine, e il cambio lo fa il
# server con le parole dello swap (pannello admin, 🔁). Spenta di serie;
# accesa, di serie solo per gli admin. La fee resta 0: sopra 0 si ferma.
SWAP_AUTO_ATTIVO = False
SWAP_AUTO_SOLO_ADMIN = True
SWAP_AUTO_FEE_PERCENTO = 0
# Dove si leggono le tariffe. Nel collaudo e sulla VM di collaudo: il
# SATS Routing di cartone, es. "http://127.0.0.1:9077" (cartone_satsrouting.py);
# in collaudo una base fuori dal computer non si legge mai.
SWAP_API_BASE = "https://api.satsrouting.exchange"
# La rete dello swap: "bitcoin" in produzione, "regtest" sulla VM di
# collaudo col regtest di Boltz (il telefono controlla da se' gli indirizzi).
SWAP_RETE = "bitcoin"
# Gli ALTRI fornitori dello swap oltre a SATS Routing (che resta sulle tre
# leve qui sopra): il telefono chiede il preventivo a tutti e sceglie il
# migliore. Una voce per fornitore, solo dati pubblici, per esempio
# {"id": "cartone2", "nome": "Cartone Due", "tipo": "boltz",
#  "api": "http://127.0.0.1:9078", "referral": "", "rete": "bitcoin"}.
# Vuota di serie.
SWAP_FORNITORI_IN_PIU = []
# Da dove il telefono legge il lockup di uno swap prima di mandare il
# segreto (mai dal fornitore): vuota = mempool.space della rete
# (`https://mempool.space/api` per bitcoin). Va scritta solo sul regtest
# (la VM di collaudo), dove un mempool pubblico non c'e'. Una voce di
# SWAP_FORNITORI_IN_PIU puo' portare la sua chiave "mempool".
SWAP_MEMPOOL_API = ""
# IL CAMBIO LIBERO (27 ott 2026, cantiere cambio-libero, decisione di
# Andrea): dalla pagina «Cambio» chi passa il cancello cambia i SUOI sats
# senza un ordine di mezzo — Lightning -> il suo indirizzo bitcoin (e,
# dalla tappa 3, bitcoin -> Lightning). I sats non passano MAI dalla
# cassaforte: partono e arrivano dal suo wallet, e Barattolo registra
# solo il biglietto (quando, quanto, con chi). Vuole SWAP_ATTIVO acceso.
# Nasce SPENTO; a leva accesa, di serie lo vedono solo i moderatori.
CAMBIO_LIBERO_ATTIVO = False
CAMBIO_LIBERO_SOLO_MODERATORI = True
# I tetti del cambio libero (decisione di Andrea): il massimo per cambio
# (il minimo e' SWAP_MIN_SATS) e quanti cambi al giorno per persona (le
# ultime 24 ore, contando i cambi nati e i biglietti ancora freschi).
CAMBIO_LIBERO_MAX_SATS = 500_000
CAMBIO_LIBERO_MAX_AL_GIORNO = 5
# La strada bitcoin → Lightning del cambio libero (tappa 3, 27 ott 2026):
# chi la sceglie manda bitcoin all'indirizzo del fornitore e riceve la
# sua richiesta Lightning pagata. Nasce SPENTA. Aspettava Massimo (SATS
# Routing) sulla quota partner del submarine e sui limiti di chiamate: ha
# risposto il 28 ott 2026 (la quota vale su tutti gli swap, sulla
# commissione finale; nessun limite di chiamate, solo il minimo e il
# massimo dell'importo). Si accende quando decide Andrea.
CAMBIO_BTC_LN_ATTIVO = False
# Prendere un ordine P2P Lightning e ricevere on-chain (1 nov 2026,
# cantiere presa-altra-rete, tappa 1): chi COMPRA sats su un ordine di
# Mostro sceglie «₿ On-chain» nel foglio «Dove ricevere i sats»; a Mostro
# parte la fattura di un cambio di SATS Routing nato dal suo telefono, e
# al rilascio i bitcoin arrivano al suo indirizzo (il costo del cambio lo
# paga solo lui, Barattolo non aggiunge niente). Mostro non cambia, la
# cassaforte non c'entra. Vuole SWAP_ATTIVO. Nasce SPENTA; a leva accesa,
# di serie la vedono solo i moderatori. Il massimo e' per cambio (il
# minimo e' SWAP_MIN_SATS).
# La stessa leva apre anche il contrario (1 nov 2026, tappa 2): sugli
# scambi P2P on-chain chi compra bitcoin sceglie «⚡ Lightning», e allo
# sblocco il 2-di-3 manda i bitcoin a un cambio di SATS Routing che paga
# la sua richiesta Lightning. Per questa strada servono in piu'
# P2P_ONCHAIN_ATTIVO, CAMBIO_BTC_LN_ATTIVO e l'on-chain sulla rete del
# fornitore (ONCHAIN_RETE = "mainnet" contro SATS Routing vero).
# E la tappa 3 (1 nov 2026): chi PRENDE un ordine on-chain vendendo
# bitcoin puo' pagare il deposito in Lightning; un cambio di SATS Routing
# porta i bitcoin dritti all'indirizzo 2-di-3. Serve l'on-chain sulla rete
# del fornitore; CAMBIO_BTC_LN_ATTIVO qui non serve (e' l'altra strada).
# E il caso 4 (1 nov 2026): chi VENDE su un ordine Lightning avendo solo
# bitcoin li cambia prima in Lightning (un cambio verso una richiesta del
# SUO wallet), poi prende l'ordine come sempre. Serve in piu'
# CAMBIO_BTC_LN_ATTIVO; niente on-chain di Barattolo di mezzo.
P2P_ALTRA_RETE_ATTIVO = False
P2P_ALTRA_RETE_SOLO_MODERATORI = True
P2P_ALTRA_RETE_MAX_SATS = 500_000
# Sopra 0 il massimo e' in EURO, rifatto in sats al cambio di adesso (12
# nov 2026); il tetto in sats qui sopra resta per quando il cambio manca.
P2P_ALTRA_RETE_MAX_EURO = 0
# Chi vende on-chain riceve in Lightning (28 ott 2026, cantiere
# onchain-verso-lightning): allo sblocco i bitcoin del 2-di-3 vanno a un
# cambio bitcoin → Lightning di SATS Routing, con la fattura di chi
# vende; nel Profilo sceglie «sempre on-chain», «sempre Lightning» o
# «ogni volta». Nasce SPENTA; vuole CAMBIO_BTC_LN_ATTIVO accesa, e resta
# ferma da sola finche' l'on-chain (oggi signet) e il fornitore (bitcoin)
# non stanno sulla stessa rete.
ONCHAIN_INCASSO_LN_ATTIVO = False
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
# CHI VEDE LE STATISTICHE DEL P2P (10 ott 2026): la sezione «Scambi
# P2P» del cruscotto /admin — scambi, volume, commissioni incassate —
# e' degli AMMINISTRATORI, non di tutti i moderatori. Qui vanno i loro
# user id Telegram, es. [123456789, 987654321]. Chi e' in lista deve
# essere ANCHE in ADMIN_IDS: la lista da sola non fa entrare nessuno.
# ⚠️ Il verso e' l'OPPOSTO della riga qui sopra: VUOTA (o assente, o
# scritta male) = non la vede NESSUNO, e il server risponde 403 a
# tutti. Si riempie sul VPS e si riavvia.
P2P_STATISTICHE_IDS = []
# LA SOGLIA DELLE DISPUTE P2P (12 ott 2026): la sezione «⚖️ Dispute P2P»
# del cruscotto /admin dice quanti scambi CON LA GARANZIA BLOCCATA (gli
# unici dove una disputa puo' nascere) finiscono in disputa.
# Sopra questa PERCENTUALE negli ultimi 30 giorni — e con almeno 3
# dispute, perche' una su dieci scambi non e' un segnale — i moderatori
# ricevono UN avviso su Telegram: uno per superamento, e si riarma solo
# quando la percentuale scende di un punto sotto la soglia.
# 0 = nessun avviso (i numeri nel cruscotto restano). Non dichiarata o
# scritta male vale 5.
P2P_DISPUTE_SOGLIA_PERCENTO = 5
# LE DISPUTE DA NON CONTARE (12 ott 2026): una disputa nata da un nostro
# bug o da una prova non e' una disputa vera. Qui vanno gli id dei loro
# ORDINI — interi, o accorciati agli 8 caratteri che si leggono nel
# cruscotto e negli avvisi, es. ["ea0af71a"] — e quelle dispute escono
# dalla percentuale della card «⚖️ Dispute P2P» e dall'avviso. Per i
# moderatori restano dove sono, e la card dice quali ha tolto.
# ⚠️ Almeno 8 caratteri per id (con meno, un capo ne prenderebbe piu'
# d'una). VUOTA, assente o scritta male = le conta TUTTE, e se e'
# scritta male lo dice all'avvio.
P2P_DISPUTE_ESCLUSE = []
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
# (12 ott 2026) Il NOSTRO relay sta nel coro: accetta da chiunque i
# soli messaggi indirizzati al coordinatore, cosi' le richieste dei
# telefoni hanno due strade di cui una nostra (docs/PRODUZIONE.md, «LA
# BUCA DEL COORDINATORE»). relay.damus.io NON va rimesso: ha bannato
# il coordinatore, e un suo OK non vale niente.
MOSTRO_RELAY = [
    "wss://relay.mostro.network",
    "wss://relay.barattolo.store",
    "wss://nos.lol",
]
# LO SPECCHIO (set 2026): i relay che tengono una COPIA del libro senza
# essere il posto dove il coordinator vive — il nostro
# "wss://relay.barattolo.store" sta qui (e, dal 12 ott 2026, ANCHE
# nella lista qui sopra: da questa il server prende l'ascolto dal vivo
# del libro, quindi qui resta).
# LA DIVISIONE E' IL PUNTO, non un ordine diverso: di qui si LEGGE
# soltanto. Le richieste al coordinator (la gamba viva) scorrono
# MOSTRO_RELAY e non passano mai da questa lista — mostrod sullo
# specchio non ascolta, e uno scambio mandato li' morirebbe senza che
# niente fallisca.
# VUOTA E' IL MONDO DI IERI, byte per byte: il libro si legge dai soli
# relay del coordinator, come prima che questa riga esistesse.
MOSTRO_RELAY_SPECCHIO = []
# I RELAY CHE CONTANO COME CONFERMA (12 ott 2026): la pagina manda ogni
# messaggio per il coordinator a tutti i relay di MOSTRO_RELAY, e lo
# considera «partito» solo quando lo conferma uno di QUESTI — quelli da
# cui mostrod legge di sicuro (si guarda nel suo journal: «Connected to
# relay», e con la sonda in sola lettura). Devono stare anche in
# MOSTRO_RELAY. VUOTA E' IL MONDO DI IERI: vale il primo OK di chiunque.
MOSTRO_RELAY_CONFERMA = []
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
# IL TETTO DEGLI ORDINI DAL COLLAUDO (20 ott 2026): sull'istanza di prova
# il P2P parla col coordinatore VERO (sats veri), e un ordine dal collaudo
# non supera questi sats, nel pubblicare e nel prendere. Vale SOLO quando
# PROVA_SOLO_IDS non e' vuota: in produzione non esiste. Il client lo
# traduce in euro al cambio vivo e vince il tetto piu' stretto. Non si
# spegne: uno zero o un refuso lasciano 10.000.
P2P_MAX_SATS_PROVA = 10_000
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
# LA CAMPAGNA A TUTTI (9 ott 2026, la vigilia del lancio): accesa, il
# giorno che il P2P e' aperto a tutti (P2P acceso e P2P_PROVA_IDS
# vuota, la condizione della campagna «Avvisami») parte UNA volta sola
# un messaggio a OGNI iscritto — Telegram o DM Nostr, il canale che
# ognuno ha scelto — TRANNE chi aveva premuto «Avvisami» sul P2P, che
# riceve gia' il suo: un messaggio a testa, mai due. Il timbro
# `campagna_p2p_tutti` (tabella `timbri`) la ferma per sempre dopo il
# primo giro, anche a leva accesa e riavvio dopo riavvio.
# Solo True accende: una stringa o un numero restano spenti.
P2P_CAMPAGNA_TUTTI = False
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
# LA CAUZIONE SUL METODO SCELTO (11 ott 2026): accesa, il client manda il
# metodo scelto nel take (`Payload::Order`) e promette la cauzione SOLO a
# chi sceglie «Contanti»; spenta, come ieri (la cauzione dell'ordine
# intero). Vuole la patch 0010 del fork sul nodo (`-bar7`, PRODUZIONE):
# accesa prima, un nodo senza la 0010 rifiuterebbe le prese sugli
# intervalli e chiederebbe la cauzione a chi aveva letto «niente».
P2P_CAUZIONE_SUL_METODO = False
# IL TEMPO DI CHI PUBBLICA (12 ott 2026): spenta di serie. Accesa, mette in
# campo la pausa degli ordini (ricorrente e una volta sola), il badge «⚡
# risponde in fretta», i quattro avvisi a chi pubblica quando gli prendono
# un ordine, e il «non completato» a chi pubblica e non risponde. Le ORE
# non stanno qui: le decide il nodo (`maker_expiration_seconds` nel suo
# settings.toml, patch 0011 del fork, `-bar8`) e le annuncia nel 38385; e
# il «non completato» a chi pubblica conta SOLO se il nodo gli da' piu'
# tempo di chi prende — accesa prima della `-bar8`, pausa e badge
# funzionano e la regola di ieri («mai a chi ha pubblicato») resta.
# Solo True accende.
P2P_TEMPO_DI_CHI_PUBBLICA = False
# IL PARACADUTE DEGLI ORDINI P2P (13 ott 2026): SPENTO di serie. Acceso,
# chi pubblica un ordine puo' scegliere una soglia (5, 10 o 20%): se il
# prezzo di BTC sale o scende piu' di cosi' rispetto alla pubblicazione,
# PRIMA che qualcuno lo prenda, l'ordine esce dal libro di Barattolo da
# solo, senza penalita', e lui riceve un avviso col tasto per
# ripubblicarlo. L'annullamento vero sul circuito lo firma il SUO
# telefono alla prima apertura: il server non firma al posto di nessuno.
# Il prezzo e' il cambio che il server legge gia' (nessuna chiamata in
# piu'); servono due letture di fila oltre la soglia, e una fonte muta
# non apre niente. Mai sugli ordini Barattozon. Solo True accende.
P2P_PARACADUTE = False
# LA RIPUBBLICA DEGLI ORDINI SCADUTI (16 nov 2026): ACCESA di serie. Chi
# pubblica scrive due prezzi di BTC («da X a Y»); quando l'ordine scade
# nel libro, se BTC sta dentro, si rifa' uguale: il Lightning lo firma il
# telefono alla prima apertura, l'on-chain lo rifa' la ronda del server.
# Spenta per ogni ordine finche' non si scrivono i due prezzi; mai su
# Barattozon ne' sugli ordini in moneta. Solo False spegne.
P2P_RIPUBBLICA = True
# LA CHAT NELLO SCAMBIO (12 ott 2026): ACCESA di serie. Dentro ogni
# scambio preso le due parti si scrivono; i messaggi passano dal server
# gia' chiusi dal telefono, stanno in un file a parte (`chat-scambi.db`,
# accanto al database: i backup NON lo copiano, ed e' voluto) e a scambio
# finito si cancellano. A False la chat sparisce dalla pagina dello
# scambio e il server non accetta buste nuove; quelle che ci sono se ne
# vanno come sempre, a scambio finito. Solo False spegne.
P2P_CHAT_SCAMBIO = True
# GLI AVVISI DEI NUOVI ORDINI DEL LIBRO (9 ott 2026): chi lo chiede dal
# bottone 🔔 della testata del libro o dal cassetto Avvisi del Profilo
# riceve un messaggio quando nel libro compaiono ordini nuovi — del tipo
# che vuole (vendita BTC, acquisto BTC, Barattozon) e, se lo chiede, solo
# da una certa convenienza in su. Per persona e' SPENTO di serie; questa
# e' la leva GLOBALE, accesa di serie: a False nessuno riceve niente e il
# bottone sparisce. Solo un booleano conta; un valore storto resta True.
P2P_AVVISI_NUOVI_ORDINI = True
# ...e la finestra del raggruppamento, in minuti: a una persona non
# arriva piu' di un messaggio ogni tanti minuti, e gli ordini nati nel
# mezzo escono insieme nel prossimo (quanti per tipo, il piu' conveniente
# per lei). Un intero da 1 in su; storto o sotto 1 vale 15.
P2P_AVVISI_NUOVI_MINUTI = 15
# GLI AVVISI DEL MERCATINO (9 ott 2026): chi lo chiede dal cassetto Avvisi
# del Profilo riceve un messaggio quando nel mercatino compaiono annunci
# nuovi — TUTTI i nuovi, con un filtro facoltativo di categorie e prezzo
# massimo, oppure quelli di un venditore che segue («🔔 Segui» sulla sua
# pagina). Per persona e' SPENTO di serie; questa e' la leva GLOBALE,
# accesa di serie: a False nessuno riceve niente, il blocco del cassetto e
# il bottone spariscono. Solo un booleano conta; un valore storto resta True.
MERCATINO_AVVISI_NUOVI = True
# ...e le due finestre del raggruppamento, in minuti: a una persona non
# arriva piu' di un messaggio «nuovi annunci» ogni tanti minuti (gli
# annunci nati nel mezzo escono insieme: quanti e i primi titoli), e per
# ogni venditore seguito non piu' di uno ogni tanti minuti. Interi da 1 in
# su; storti o sotto 1 valgono 60 e 15.
MERCATINO_AVVISI_NUOVI_MINUTI = 60
MERCATINO_AVVISI_SEGUI_MINUTI = 15
# LA CHAT NEGLI ORDINI DEL MERCATINO (16 ott 2026): SPENTA di serie. Accesa,
# da quando chi compra paga le due parti si scrivono nella pagina dell'ordine
# con la chat dello scambio P2P (cifrata sul telefono, foto e PDF, gli stessi
# tetti), nello stesso file a parte (`chat-scambi.db`, fuori dai backup); a
# ordine concluso — confermato, liberato, rimborsato — si cancella tutto. In
# disputa resta fino alla decisione, e il moderatore la legge con la sua
# chiave. Spenta, la chat sparisce dagli ordini; quelle che ci sono se ne
# vanno come sempre. Solo True accende.
MERCATINO_CHAT_ORDINI = False
# I SUGGERIMENTI DEGLI INDIRIZZI DELL'APPUNTAMENTO (1 ott 2026): mentre chi
# vende in contanti scrive dove vedersi, il server chiede indirizzi veri a
# Photon (dati OpenStreetMap) mandando SOLO il testo cercato, col freno e
# una memoria in RAM. Qui si puo' puntare un'altra istanza di Photon (una
# nostra, o quella di cartone dei collaudi). Il default nel codice e'
# quello pubblico e vale anche senza questa riga.
P2P_LUOGHI_URL = "https://photon.komoot.io"
# LA CARD «P2P IN ARRIVO» (30 set 2026): la prima card di «Da scoprire»,
# per tutti. Fino a questa data (compresa) dice «In arrivo il 10/10/26»;
# passata la data col P2P ancora chiuso dice «in arrivo a breve»; col P2P
# aperto a tutti (P2P_IN_VETRINA = True e P2P_PROVA_IDS vuota) dice «Ora
# disponibile» e porta al P2P vero, e 14 giorni dopo la data se ne va.
# Il default nel codice e' "2026-10-10" e vale anche senza questa riga.
# None o "" = card spenta. Solo AAAA-MM-GG: una data storta la spegne.
P2P_IN_ARRIVO_FINO = "2026-10-10"
# LE PRESE DALLE 10 (9 ott 2026, la vigilia del lancio): fino a quest'ora
# — ORA ITALIANA, «AAAA-MM-GG HH:MM» — chi non e' moderatore pubblica ma
# non prende ne' annulla (i bottoni restano, spenti, e dicono «Dalle
# 10:00 di domani»), e senza un ordine vivo suo nel libro vede il foglio
# «Pubblica» al posto del libro. I moderatori non la vedono. Passata
# l'ora la leva e' inerte da sola, senza riavvio: la riga si toglie con
# comodo. Assente o vuota = nessun blocco; un'ora storta = nessun
# blocco, e il journal lo dice all'avvio. La riga da mettere il 9 ott:
# P2P_PRESE_DA = "2026-10-10 10:00"
P2P_PRESE_DA = ""
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

# IL TETTO DI ROTTA DEL COORDINATORE (10 ott 2026, cantiere
# controllo-fattura): lo SPECCHIO di `max_routing_fee` nel settings.toml
# del nodo (0.01 dal 17 set 2026). Serve al controllo della fattura di
# chi compra, PRIMA che parta verso il coordinatore: se la strada piu'
# economica fino a quella fattura costa piu' di `sats × tetto`, il
# coordinatore non la pagherebbe, e lo si dice subito (con un «Usa
# comunque»). Se cambia la', va cambiato qui: il server non lo legge.
P2P_TETTO_ROTTA = 0.01
# I WALLET IL CUI INDIRIZZO NON PASSA (10 ott 2026, cantiere
# indirizzo-non-verificato): il coordinatore la Lightning address la
# verifica per conto suo, da dietro Tor, e a certi servizi non riesce
# ad arrivare — anche quando il nostro controllo, che esce in chiaro,
# dice «pagabile». Per i domini scritti qui il foglio «Dove ricevere i
# sats» ferma PRIMA dell'invio e manda alla fattura (che di quei wallet
# passa: non passa solo l'indirizzo). Dominio in minuscolo -> il nome
# da dire. Senza questa riga vale l'elenco del codice (il solo Wallet
# of Satoshi); scritta qui lo SOSTITUISCE: le voci vanno ripetute tutte.
P2P_INDIRIZZI_NON_PASSANO = {"walletofsatoshi.com": "Wallet of Satoshi"}

DB = "satmarket.db"

# --- Punti e dollari su RGB (hackathon di Torino, 17-18 ott 2026) -------
# Barattolo imparera' a parlare con asset RGB su signet — un ordine
# pagato in dollari di prova (USDB) su consiglio di «Consigliami»,
# l'aiutante locale che propone e l'utente approva; i punti del negozio
# (MOON) come bonus — e il regolamento vuole che il codice si scriva LA',
# in commit datati. Prima dell'evento c'e' SOLO il cancello, sul calco
# di P2P_ATTIVO / P2P_PROVA_IDS: nasce spento, si accende con un gesto
# qui dentro, mai per effetto di un deploy. Spento, nessuna rotta RGB
# risponde e nessun foglio compare. Il disegno sta in
# docs/STUDIO-HACKATHON-RGB-2026-10.md (parte seconda) e la lista di
# cosa si prepara prima in docs/HACKATHON-SETUP.md (sezione 10).
RGB_ATTIVO = False
# ── IL PAGAMENTO ON-CHAIN (16 ott 2026): il cancello, e niente altro.
# Lo studio — il 2-di-3 non custodial, le chiavi nel browser, la beta a
# 250 euro — sta in docs/CANTIERI.md, «Il pagamento on-chain come
# opzione». Oggi NON esiste nessuna rotta /api/onchain/* e nessun
# foglio: queste due righe sono il cancello che nasce PRIMA delle
# porte, cosi' il giorno in cui la prima porta si apre deve passare da
# qui per forza (lo pretende una prova). Spento e' no per CHIUNQUE,
# admin compresi.
ONCHAIN_ATTIVO = False
# ...e la decisione di Andrea del 16 ott: anche a funzione accesa, per
# ora l'on-chain lo vedono SOLO i moderatori di ADMIN_IDS — cioe' lui e
# Alan. Spegnere questa riga e' il gesto SEPARATO del giorno in cui la
# beta si allarga: due leve perche' sono due decisioni.
ONCHAIN_SOLO_ADMIN = True
# L'XPUB DI BARATTOLO, cioe' la TERZA chiave del 2-di-3 — quella che
# serve SOLO in disputa. Qui va la META' PUBBLICA e nient'altro.
# ⚠️ DAL 27 OTT 2026 DI SOLITO QUESTA RIGA RESTA VUOTA: la chiave di
# Barattolo nasce SUL VPS col bottone «Crea la chiave di Barattolo» del
# pannello admin (decisione di Andrea, cantiere onchain-disputa), vive
# in `chiavi/onchain-barattolo.json` ed entra nel backup fuori sede.
# Una xpub scritta qui E il file insieme sono due terze chiavi, e il
# server si ferma. Vuota e senza file: il server usa una xpub DI CARTONE, presa
# dai vettori di prova del BIP-32 — pubblicata in uno standard col suo
# seme, quindi CHIUNQUE ha la privata — e lo DICE al foglio, che la
# mostra scritto: «non mandarci niente».
# ⚠️ Una xpub vera qui deve essere della RETE di ONCHAIN_RETE (una
# `tpub...` su signet, una `xpub...` su mainnet): quella dell'altra rete
# il server la RIFIUTA, e un `xprv` o un `tprv` (privata) li rifiuta
# sempre, senza ripeterli da nessuna parte. L'indirizzo di ogni ordine
# si calcola sul server con la libreria `embit` (requirements.txt): se
# manca, le rotte on-chain rispondono 503 e il resto vive.
ONCHAIN_XPUB = ""
# LA RETE DELL'ON-CHAIN (30 ott 2026, cantiere onchain-mainnet, proposta
# di Alan: una prova vera da 5 € con l'on-chain acceso solo agli admin).
# "signet" = la rete di prova (indirizzi tb1…, chiavi tpub…, conto
# m/48'/1'/0'/2', i sats non valgono niente): e' il valore del codice e
# del collaudo. "mainnet" (o "bitcoin") = SATS VERI: indirizzi bc1…,
# chiavi xpub…, conto m/48'/0'/0'/2', mempool.space. Una parola storta
# resta signet e lo dice nel journal. Dal 30 ott anche dal pannello (vale al riavvio).
# ⚠️ SU MAINNET LA TERZA CHIAVE DI CARTONE NON SI USA: finche' la
# chiave di Barattolo non nasce dal pannello («⛓️ Crea la chiave di
# Barattolo», DOPO aver messo questa riga e riavviato) l'on-chain e'
# fermo — nessun indirizzo nasce, la cassa non offre ⛓️, il pannello
# delle leve e' in allarme. Una chiave nata su signet NON vale su
# mainnet (il file dice la sua rete): si sposta via prima, e se ne crea
# una nuova. La procedura intera: PRODUZIONE, «L'ON-CHAIN IN MAINNET».
# Le xpub dedicate date dai telefoni su signet non valgono su mainnet:
# l'app le rida' da sola alla prima apertura (si accende da sola).
# "testnet4" (3 nov 2026, cantiere onchain-testnet4) = la SECONDA rete di
# prova: le forme di signet (tb1…, tpub…, lo stesso conto), un'altra
# catena (https://mempool.space/testnet4/api; in Sparrow la modalita'
# Testnet4). Fra signet e testnet4 la chiave di Barattolo e le xpub dei
# telefoni restano buone. «testnet» da sola NON vale: sarebbe la
# testnet3, dismessa. Si sceglie anche dal pannello delle leve.
ONCHAIN_RETE = "signet"
# L'API mempool che guarda i pagamenti degli ordini on-chain (tappa 4) e
# trasmette le transazioni d'uscita. Vuota = quella di serie della rete
# (signet: https://mempool.space/signet/api; testnet4:
# https://mempool.space/testnet4/api; mainnet: https://mempool.space/api).
ONCHAIN_MEMPOOL_API = ""
# LA QUOTA FISSA DI BARATTOLO SULL'ON-CHAIN (27 ott 2026): sats che chi
# COMPRA aggiunge al conto (li vede prima di pagare) e che vanno a un
# indirizzo di Barattolo quando i sats vengono liberati; col rimborso
# tornano a lui. 0 = nessuna quota (il valore del codice); altrimenti
# fra 546 (sotto, polvere: la rete non trasmette) e 5000. SI CAMBIA
# ANCHE DAL PANNELLO («⚙️ Stato delle leve», ✏️), e il pannello vince su
# questa riga: qui c'e' solo il valore di partenza.
ONCHAIN_QUOTA_FISSA_SATS = 0
# IL TETTO DELLA BETA ON-CHAIN (27 ott 2026, decisione di Andrea: «il
# tetto rimane di 250 euro per un certo periodo ancora»): un ordine
# on-chain sopra questa cifra in euro (sul prezzo, senza il margine per
# la rete) non si paga on-chain, resta il Lightning. 0 = nessun tetto.
# Il valore del codice e' gia' 250: la riga serve il giorno che sale.
ONCHAIN_MAX_EURO = 250
# IL PAYJOIN DEGLI ACQUISTI ON-CHAIN (16 nov 2026, cantiere payjoin): il
# link di pagamento del mercatino porta `pj=` (BIP78), e il wallet di chi
# compra che lo sa fare lascia aggiungere a Barattolo una sua moneta (le
# quote fisse qui sopra). Acceso di serie; il link nasce solo se la
# chiave di Barattolo firma su questo server e c'e' una sua moneta
# pronta. False = interruttore d'emergenza: il link torna quello di ieri.
PAYJOIN_ATTIVO = True
# LA SCELTA DELLA RETE AL «PAGA» DEL MERCATINO (2 nov 2026, Andrea: «quando
# uno compra un oggetto e clicca su paga deve comparire esattamente come
# nel P2P il banner grosso on-chain o Lightning, e poi in alto nella
# pagina della fattura lo switch»): acceso, chi vede l'on-chain e compra
# un oggetto che si puo' pagare on-chain sceglie PRIMA fra i due tasti
# grandi della scelta del + del P2P, e nel foglio della fattura ha in
# cima l'interruttore On-chain/Lightning del P2P. Spento, il foglio si
# apre sul Lightning con le due porte ⚡/⛓️ di sempre. Vale solo per chi
# l'on-chain lo vede (ONCHAIN_ATTIVO e il suo cancello). Spento di serie,
# in produzione si accende col sì di Andrea. Sul collaudo: True.
MERCATINO_SCELTA_RETE = False
# GLI SCAMBI P2P CON LA GARANZIA 2-DI-3 (30 ott 2026, decisione di Andrea
# con Alan): nel P2P, accanto agli ordini Lightning di Mostro, gli scambi
# bitcoin on-chain ↔ euro in cui chi vende bitcoin li deposita nel 2-di-3
# non custodial dell'on-chain e li libera quando gli euro sono arrivati.
# Vivono NEL SERVER E NELL'APP (Mostro non si tocca), escono su Nostr
# come 38383 firmati dalla chiave del server. Vale solo con ONCHAIN_ATTIVO
# e il P2P accesi, per chi e' ammesso all'on-chain (oggi gli admin).
# Spento di serie: in produzione si accende dopo il parere MiCA e la
# revisione di Alan delle parti 2-di-3. Sul collaudo: True.
P2P_ONCHAIN_ATTIVO = False
# GLI ORDINI P2P IN USDT (1 nov 2026, decisione di Andrea: «Tron +
# Polygon mettiamo anche ethereum. tetto 250 €, NODO solo dopo le
# prove»): accanto agli ordini in euro, ordini Mostro in USDT. La
# garanzia resta la hold invoice Lightning di sempre; gli USDT viaggiano
# FUORI da Mostro, come gli euro del bonifico, su una delle due reti
# (Tron ed Ethereum; Polygon tolto il 2 nov, aveva gli indirizzi uguali
# a Ethereum). L'app controlla che l'indirizzo sia della rete scelta e chiede l'id della transazione a «Ho inviato». Serve
# anche il gesto sul nodo (USDT fra le valute accettate, provider
# pegged): sta in DA-FARE-ANDREA, si fa DOPO le prove. Spento di serie.
P2P_USDT_ATTIVO = False
# Con la leva accesa, gli USDT li vedono solo gli admin finche' questa
# resta True: la prima fase e' delle prove. False = tutti gli ammessi
# al P2P.
P2P_USDT_SOLO_ADMIN = True
# GLI USDT NEGLI SCAMBI ON-CHAIN (2 nov 2026, decisione di Andrea:
# «usdt onchain assolutamente è da fare», con la strada di Alan: la
# garanzia sta sempre e solo dal lato bitcoin). Negli scambi col 2-di-3
# chi compra bitcoin paga in USDT su Tron o Ethereum invece che in euro;
# i sats restano nel 2-di-3 di sempre, Barattolo gli USDT non li tocca.
# Vale solo per chi ha P2P_ONCHAIN_ATTIVO e gli USDT (P2P_USDT_ATTIVO,
# con P2P_USDT_SOLO_ADMIN). Spento di serie; sul collaudo si accende.
P2P_ONCHAIN_USDT_ATTIVO = False
# GLI ORDINI P2P IN FRANCHI SVIZZERI (14 nov 2026, cantiere p2p-chf,
# Andrea: «abbiamo stretto una collaborazione con Lugano»). Accanto agli
# ordini in euro e in USDT, ordini Mostro in CHF: la garanzia resta la
# hold invoice Lightning di sempre, i franchi viaggiano fuori da Mostro
# (TWINT, bonifico svizzero, Revolut, Wise, contanti). Il tetto resta
# quello in euro, tradotto in franchi al cambio. Serve anche il gesto sul
# nodo («CHF» fra le valute accettate): sta in DA-FARE-ANDREA. Spento di
# serie; sul collaudo si accende.
P2P_CHF_ATTIVO = False
# Con la leva accesa, i franchi li vedono solo gli admin finche' questa
# resta True. False = tutti gli ammessi al P2P.
P2P_CHF_SOLO_ADMIN = True
# ETH, MONERO E USDe COME METODI DEL P2P (16 nov 2026, cantiere
# p2p-monete). Negli ordini in euro chi paga puo' mandare l'equivalente
# in ETH (Ethereum), XMR (Monero) o USDe (Ethereum, Arbitrum, Base, BNB
# Chain, Solana), da persona a persona: la garanzia resta la hold invoice
# in sats, Barattolo le monete non le tocca. Nessun gesto sul nodo.
# ACCESA di serie (regola del 14 nov 2026): False la spegne in emergenza.
P2P_COIN_ATTIVO = True
# La fase chiusa, come per il P2P: i tg_id che vedono le cose RGB
# mentre gli altri non vedono niente. Vuota = aperta a chiunque appena
# RGB_ATTIVO si accende; una riga storta vale «chiusa a tutti» e lo dice.
RGB_PROVA_IDS = []
# IL NIP-05 DI CASA: /.well-known/nostr.json dice «questo nome su
# barattolo.store e' questa chiave Nostr». Serve agli EMITTENTI degli
# asset dell'hackathon (le due identita' di prova `usdb` e `tothemooon`)
# perche' un wallet possa scrivere «Emesso da … ✓». Qui vanno SOLO
# chiavi PUBBLICHE, in esadecimale minuscolo (64 caratteri): mai una
# nsec, mai una npub (il NIP-05 vuole l'hex). Vuoto o non dichiarato,
# la rotta risponde {"names": {}}, cioe' «qui nessuno».
#     NIP05_NOMI = {"usdb": "<hex>", "tothemooon": "<hex>"}
NIP05_NOMI = {}

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
#
# L'ORDINE CONTA (15 ott 2026): il primo e' il relay suggerito ai client,
# e i primi quattro ricevono i DM di chi non ha un kind 10050 — il
# relay di Barattolo in fondo (rifiuta le buste dei DM), nos.lol non in
# testa (frena con un 429 chi gli apre troppe connessioni). Questa lista
# e' anche il kind 10002 di Barattolo: se cambia qui, si ripubblica quello
# (PRODUZIONE, «IL KIND 10002 DI BARATTOLO»).
RELAY_NOSTR = [
    "wss://relay.primal.net",
    "wss://relay.nostr.net",
    "wss://nostr.oxtr.dev",
    "wss://nos.lol",
    "wss://relay.mostro.network",
    "wss://relay.barattolo.store",
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

# --- Le foto delle recensioni (ott 2026) -------------------------------
# Nel feedback di un affare si mettono fino a 3 foto: il server toglie i
# metadati (GPS compreso) e le carica su questo server Blossom, firmando
# con NOSTR_NSEC_PIATTAFORMA qui sopra (senza quella chiave le recensioni
# con foto rispondono «riprova, o invia senza foto»). Il default e' gia'
# questo: la riga serve solo per cambiarlo.
BLOSSOM_SERVER = "https://blossom.primal.net"

# --- La cassa di risonanza su X (ott 2026) ----------------------------
# I post di Barattolo su Nostr — le note kind 1 ORIGINALI della npub
# ufficiale (niente risposte, niente repost) — escono anche su X,
# ripubblicati dal server con l'API ufficiale (v2, contesto utente).
# Niente note di casa (le promo degli annunci che firma il server) e
# niente prodotti uno per uno: per quelli c'e' solo il riepilogo del
# giorno, qui sotto. NASCE SPENTA, il patto delle altre: si accende
# con un gesto, mai per effetto di un deploy. La procedura passo per
# passo (l'app su developer.x.com, il credito, le quattro chiavi) sta
# in docs/PRODUZIONE.md, «LA CASSA DI RISONANZA SU X».
X_RIPUBBLICA = False
# Il link njump alla nota, in coda a ogni post. X fa pagare 0,200 $ un
# post con un URL contro 0,015 $ senza (settembre 2026, pay-per-use):
# di serie i post escono SENZA link. I link che la persona scrive nel
# testo della nota restano suoi, e il journal dice la tariffa piena.
X_CON_LINK = False
# UN post al giorno «Nuovi arrivi di oggi nel mercatino: N annunci»,
# con fino a 4 foto e senza link, alle 18 ora italiana. Spento di serie.
X_RIEPILOGO_GIORNO = False
# La modalita' prova: il journal dice cosa AVREBBE pubblicato, X non
# viene chiamato e niente si paga. Si prova con questa a True (le
# chiavi possono anche mancare), poi si rimette False.
X_PROVA = False
# Le quattro chiavi dell'app su X (OAuth 1.0a, «Read and Write»). SOLO
# nel config del VPS, a mano: mai in chat, mai su GitHub, mai nei log.
X_API_KEY = "INCOLLA_QUI_LA_API_KEY_DI_X"
X_API_SECRET = "INCOLLA_QUI_LA_API_SECRET_DI_X"
X_ACCESS_TOKEN = "INCOLLA_QUI_L_ACCESS_TOKEN_DI_X"
X_ACCESS_SECRET = "INCOLLA_QUI_L_ACCESS_SECRET_DI_X"
# La npub ufficiale di Barattolo, quella ascoltata. E' gia' nel codice:
# la riga serve solo per cambiarla (un giro di prova con una chiave
# usa-e-getta).
X_NPUB = "npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy"
# La base dell'API di X. Si cambia SOLO nei collaudi (un X di cartone
# sul loopback): in produzione resta questa.
X_API_BASE = "https://api.x.com"

# --- L'indirizzo Lightning di casa: zap@barattolo.store (ott 2026) ---
# Un Lightning address di Barattolo, da scrivere nel profilo Nostr
# ufficiale (campo lud16) per ricevere gli zap. Acceso, il server
# risponde su /.well-known/lnurlp/zap e conia le fatture su un wallet
# LNbits A PARTE, il «salvadanaio»: mai quello delle garanzie.
# Nasce SPENTO: con la leva False (o senza l'invoice key qui sotto)
# quell'indirizzo risponde 404.
ZAP_ATTIVO = False
# La INVOICE key del wallet «zap» (LNbits del nodo → wallet «zap» →
# «API info» → «Invoice/read key»). SOLO quella: con lei il server
# conia e guarda, NON spende. La Admin key di quel wallet qui non si
# mette mai. Solo nel config del VPS, a mano: mai in chat, mai su GitHub.
ZAP_LNBITS_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY_DEL_WALLET_ZAP"
# Dove sta quel wallet: vuoto = lo stesso LNbits del nodo
# (LNBITS_NODO_URL). Si scrive solo se un giorno traslocasse.
ZAP_LNBITS_URL = ""
# Il massimo di un singolo pagamento, in sats (il minimo e' 1).
ZAP_MAX_SATS = 100_000
# A chi vanno gli zap: la npub ufficiale di Barattolo. E' gia' nel
# codice: la riga serve solo per un giro di prova con un'altra chiave.
ZAP_NPUB = "npub19ea0u0u6lrpaeyxkazk27ht64yn22ncvytcu24tswvyuqk07svds63txqy"

# --- L'indirizzo della quota: swap@barattolo.store (19 ott 2026) ---
# Dove SATS Routing manda a fine mese la quota di Barattolo sugli swap.
# E' un altro Lightning address, separato da zap@: wallet LNbits SUO
# («swap»), tetto piu' alto, niente zap Nostr, e un avviso nel gruppo
# degli admin (📊 Riepiloghi) a ogni pagamento. Nasce SPENTO: con la
# leva False (o senza l'invoice key) /.well-known/lnurlp/swap dice 404.
SWAP_INDIRIZZO_ATTIVO = False
# La INVOICE key del wallet «swap» (LNbits del nodo → wallet «swap» →
# «Invoice/read key»). SOLO quella, e NON quella del wallet «zap»: con
# la stessa chiave l'indirizzo vale spento. Solo nel config del VPS.
SWAP_LNBITS_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY_DEL_WALLET_SWAP"
# Dove sta quel wallet: vuoto = lo stesso LNbits del nodo.
SWAP_LNBITS_URL = ""
# Il massimo di un singolo pagamento, in sats. Il limite vero e' la
# liquidita' in entrata dei canali del nodo (/canali nel bot). (Non e'
# SWAP_MAX_SATS: quello e' il tetto di uno swap dei venditori, piu' su.)
SWAP_INDIRIZZO_MAX_SATS = 2_000_000

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

# Quanti prodotti si leggono per collegamento a ogni giro. MILLE dal 1
# ott 2026 (era 200: un negozio da mille prodotti non entrava mai per
# intero, i lettori si fermavano sempre allo stesso punto).
# ⚠️ ABBASSARLO NON DISTRIBUISCE NIENTE, ed e' la cosa da sapere prima
# di toccarlo: quel che non si legge non si puo' distinguere da quel
# che il venditore ha tolto dal negozio, quindi una lettura corta
# SOSPENDE le sparizioni per quel giro (fino ad ago 2026 le spegneva
# invece, per sempre: 'rimosso' non risorge). Il catalogo oltre il
# tetto semplicemente non entra, e il report lo dice al venditore.
# Per far entrare un catalogo grande un po' per volta c'e' la leva qui
# sotto, che e' un'altra cosa.
# Oltre 250 il catalogo di Shopify si pagina davvero: fra una pagina e
# l'altra il lettore aspetta mezzo secondo (il ritmo del suo limite di
# richieste). Un WooCommerce lento con tanti prodotti variabili non
# scade piu': la lettura delle varianti si ferma da sola a otto
# minuti e riprende da li' al giro dopo.
MAX_PRODOTTI_CONNETTORE = 1000

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

# IL RODAGGIO di un negozio appena collegato (1 ott 2026): nelle prime
# ORE_RODAGGIO_CONNETTORE ore ne nascono MAX_NUOVI_CONNETTORE_RODAGGIO
# ALL'ORA (non a giro: il bottone «🔄 Aggiorna ora» non li moltiplica)
# invece dei trenta a giro qui sopra — un catalogo da mille entra in
# dieci ore invece che in trentaquattro, poi torna il regime. Le ore
# si contano dal primo annuncio entrato (un negozio che aspetta i costi
# di spedizione non si legge, e non deve bruciarsi il rodaggio in
# attesa). Il rodaggio non rallenta mai: se il regime e' piu' alto vale
# lui. 0 su una delle due = niente rodaggio.
MAX_NUOVI_CONNETTORE_RODAGGIO = 100
ORE_RODAGGIO_CONNETTORE = 24

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
# Il canale @BitcoinPodcastTelegram (15 ott 2026): la TERZA
# destinazione degli annunci e degli scambi P2P nuovi. Vuoto = non ci
# si posta, e nessun ripiego sul nostro — come il canale della
# comunita' qui sopra, e per lo stesso motivo.
# A DIFFERENZA di quello, qui NON c'e' il filtro dell'@username: entra
# tutto, perche' quel pubblico e' di bitcoiner e la menzione Telegram
# non e' la maniglia che si aspetta.
# Anche questa riga e' solo il valore di PARTENZA: si cambia dal bot
# con «/canale bitcoinpodcast @nome», e da quel momento comanda la
# scelta salvata nel database. Il bot dev'essere amministratore di quel
# canale, col permesso di pubblicare e di modificare i propri messaggi
# (serve al ✅ Venduto).
TELEGRAM_CANALE_BITCOIN_PODCAST = ""
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

# IL GRUPPO DEGLI ADMIN (12 ott 2026): gli avvisi DA ADMIN — dispute,
# liquidita', pagamenti da guardare, moderazione, riepiloghi, i DM su
# Nostr — vanno in un gruppo Telegram privato invece che nella chat
# privata di ogni moderatore, dove restano i soli avvisi da utente (i
# tuoi ordini, i tuoi scambi). Nessun avviso si aggiunge e nessuno si
# toglie: cambia solo DOVE arriva.
# ADMIN_CANALE_ID e' il numero del gruppo, quello che dice il comando
# /dove scritto nel gruppo: e' negativo e comincia per -100 (un gruppo
# CON GLI ARGOMENTI accesi; il bot dev'esserci, come amministratore).
# 0 = spento: tutto come sempre, in privato. Un numero storto spegne la
# leva e lo dice nel journal ([admin] ...). Se il gruppo non riceve (bot
# tolto, numero sbagliato) gli avvisi ripiegano in privato da soli, e
# lo si viene a sapere una volta.
ADMIN_CANALE_ID = 0
# ...e i suoi argomenti: per ogni nome il numero che dice /dove scritto
# DENTRO quell'argomento. I nomi sono questi sette e non altri:
#   "dispute"      ⚖️ dispute del mercatino e del P2P, garanzie ferme
#   "liquidita"    💧 liquidita' del nodo e guardiano del ponte
#   "errori"       ⚠️ pagamenti falliti o da verificare, ordini fermi
#   "moderazione"  🛡️ revisioni e banner coi ✅/❌, filtri, annunci nuovi
#   "dm"           📩 «e' arrivato un DM su Nostr» (mai il testo)
#   "riepiloghi"   📊 polso degli ordini, nuovi iscritti, registro comandi
#   "assistenza"   🙋 chi chiede una persona all'assistente del bot
# Un nome che manca va nell'argomento Generale. (La 🔔 dei nuovi ordini
# del libro P2P non e' fra questi: e' una notifica da utente, e resta
# in privato a chi l'ha accesa.)
# Es.: {"dispute": 2, "liquidita": 4, "errori": 6, "moderazione": 8,
#       "dm": 10, "riepiloghi": 12, "assistenza": 14}
ADMIN_CANALE_ARGOMENTI = {}
# ...e la sua CODA (16 ott 2026): un avviso che il gruppo non prende (la
# rete che cade, Telegram che chiede di aspettare, il bot tolto) non
# ripiega subito in privato: si riprova dopo 30 secondi e dopo 2 minuti.
# Poi gli URGENTI (dispute, revisioni coi ✅/❌, liquidita', errori)
# arrivano in privato come prima; gli altri (annunci nuovi e moderazione,
# banner, riepiloghi, DM) in privato MAI: aspettano in coda, sul
# database, e arrivano nel gruppo quando riprende (dopo tre giorni si
# scartano). Ogni ripiego e ogni recupero ha la sua riga nel journal
# («Gruppo degli admin: ...»).
# False = come prima del 16 ott 2026: subito in privato. Vale solo col
# gruppo acceso (ADMIN_CANALE_ID).
GRUPPO_ADMIN_CODA = True

# L'avviso dei DM su Nostr (ott 2026): quando qualcuno scrive un DM al
# profilo Nostr di Barattolo (la chiave di NOSTR_NSEC_PIATTAFORMA) i
# moderatori ricevono un avviso che dice da chi e CHE COSA e' arrivato
# — «📩 Nuovo DM da …, lo trovi in Amethyst», «✉️ Nuova mail Nostr da
# …», un altro tipo col suo numero — con un bottone per aprirlo in un
# client. MAI il testo del messaggio: di una busta NIP-17 il server
# apre il sigillo per sapere chi scrive e il messaggio di dentro per
# leggerne il solo tipo (dal 15 ott 2026), in memoria, e il resto lo
# butta: niente nei log, nel database o negli avvisi. Al massimo un
# avviso ogni 10 minuti per mittente e 6 in mezz'ora in tutto: oltre,
# un riassunto senza nomi. Nasce SPENTO: True e riavvia per accenderlo.
AVVISO_DM_NOSTR = False
# I relay su cui ascoltare: quelli della lista DM di Barattolo (il suo
# kind 10050). Se un giorno quella lista cambia, si cambia anche qui.
# relay.damus.io NON va messo: i DM li consegna solo a chi si
# autentica, e la sua autenticazione oggi non funziona (ott 2026).
AVVISO_DM_NOSTR_RELAY = [
    "wss://nos.lol",
    "wss://relay.primal.net",
]

# Il vecchio DM NIP-04 di riserva (20 ott 2026): a chi entra con Nostr e
# NON pubblica la lista dei relay dei messaggi (kind 10050) gli avvisi
# partono come DM NIP-17 verso i relay di lettura del suo profilo e i
# nostri, e restano in «📬 I tuoi avvisi» dentro Barattolo. Con True a
# lui parte ANCHE un DM NIP-04 (kind 4), che Primal, Damus e altri
# leggono senza la lista. IL PREZZO: il testo e' cifrato, ma sul relay
# resta in chiaro che Barattolo ha scritto a quella npub, e quando —
# chiunque vede che e' un cliente e quando ha un ordine o una chat che
# si muove. Nasce SPENTA: True e riavvia per accenderla.
DM_NIP04_RISERVA = False

# Le notifiche sul telefono (web push, 14 nov 2026): nel cassetto Avvisi
# compare «📲 Notifiche sul telefono» (fuori da Telegram e da Tor), e chi
# lo accende riceve gli avvisi anche ad app chiusa: l'app di Zapstore, il
# sito aggiunto alla Home, il browser del PC. Nasce ACCESA (Andrea: quel
# che si prova sul collaudo arriva in produzione gia' acceso); False e
# riavvia (o il pannello) per spegnerla.
WEB_PUSH_ATTIVO = True
# Il timbro delle notifiche (chiave VAPID) lo crea il server da solo e lo
# tiene nel database: questa riga resta VUOTA. Serve solo per imporne uno
# (base64url della chiave privata P-256). E' un segreto: mai in chat.
WEB_PUSH_CHIAVE_PRIVATA = ""

# La mancia al venditore (14 nov 2026): nell'ordine pagato chi compra
# vede «🎁 Lascia una mancia», uno zap DIRETTO al Lightning address di
# chi vende (Barattolo non tocca i sats: niente fee, niente rimborso),
# con l'invito facoltativo a uno zap anche a Barattolo (zap@). Nasce
# ACCESA; False e riavvia (o il pannello) per spegnerla.
MANCIA_ATTIVA = True
# Il tetto di UNA mancia, in sats.
MANCIA_MAX_SATS = 100_000

# La cassa in negozio (15 nov 2026): nel Profilo chi vende trova «🏪 Cassa
# in negozio», batte un conto (importo e/o i suoi annunci) e mostra un QR
# Lightning o on-chain che va DRITTO al suo wallet: niente ordine, niente
# deposito, nessun account per chi compra. Nasce ACCESA; False e riavvia
# (o il pannello) per spegnerla.
CASSA_ATTIVA = True
# Il tetto di UNA vendita alla cassa, in sats (0 = nessuno: i sats non
# passano da Barattolo).
CASSA_MAX_SATS = 0

# La ronda dei relay di Mostro (12 ott 2026): ogni dieci minuti il
# server chiede ai relay che confermano (MOSTRO_RELAY_CONFERMA; senza,
# a tutto MOSTRO_RELAY) se rispondono e se il coordinatore ci scrive
# ancora. Un guasto visto due giri di seguito arriva nel gruppo degli
# admin, argomento "errori"; quando passa, arriva anche il ritorno.
# Nasce SPENTA: True e riavvia per accenderla.
RONDA_RELAY_MOSTRO = False
# Il canarino: ogni mezz'ora un messaggio di prova indirizzato al
# coordinatore (un kind 14 vuoto, firmato da una chiave usa-e-getta,
# che scade in dieci minuti), per sapere se il relay lo ACCETTA.
# ⚠️ SOLO IL NOSTRO RELAY: a un relay d'altri sarebbe spam. Vuota =
# niente canarino. Sul VPS: ["wss://relay.barattolo.store"]
RONDA_RELAY_CANARINO = []
# La ronda dei relay Nostr di casa (15 ott 2026): ogni dieci minuti il
# server chiede a ognuno dei relay di RELAY_NOSTR se risponde (una
# lettura, niente eventi), e guarda se accettano i nostri eventi veri.
# Un relay giù, o che ci rifiuta, da più di un'ora arriva nel gruppo
# degli admin, argomento "errori"; quando passa, anche il ritorno.
# Nasce SPENTA: True e riavvia per accenderla.
RONDA_RELAY_NOSTR = False

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
# Vale su web e PWA; dentro Telegram solo con PIU_ACCOUNT_OVUNQUE
# (qui sotto): li' l'identita' la impone l'initData firmato, e gli
# account in piu' si aggiungono accanto, mai al suo posto.
# Ogni account in piu' e' un token nel cookie del portachiavi (~43
# caratteri): il tetto non protegge dal peso, tiene corta una lista
# che si legge con un dito. Al limite cede il piu' VECCHIO, mai
# l'account su cui si e' appena entrati.
# Dentro la Mini App (con la leva qui sotto accesa) il Telegram occupa
# un posto: restano MAX_ACCOUNT_BROWSER - 1 account Nostr.
MAX_ACCOUNT_BROWSER = 5

# PIU' ACCOUNT OVUNQUE (16 ott 2026, richiesta di Andrea): il selettore
# anche DENTRO la Mini App (il proprio Telegram + account Nostr, un
# portachiavi per ogni Telegram del telefono), il volto dell'account
# attivo in ogni conferma coi soldi, «Esci da tutti», e le annotazioni
# per il moderatore quando due account aperti insieme si comprano, si
# votano o si prendono un ordine P2P (si ANNOTA, MAI si blocca: decisione
# di Andrea del 17 ott 2026). Il multi-account del web d'agosto vive
# anche a leva spenta. SPENTA di serie: si accende dopo la prova.
PIU_ACCOUNT_OVUNQUE = False

# LA CANCELLAZIONE DELL'ACCOUNT (1 nov 2026, cantiere cancella-account,
# decisione di Andrea): nel Profilo, sotto Privacy, «🗑 Cancella il mio
# account». Si puo' solo senza niente in corso (ordini, scambi P2P,
# dispute, aste, pagamenti in viaggio, cambi): il foglio dice cosa manca.
# Via i dati della persona; ordini e pagamenti chiusi restano senza nome
# («Utente cancellato»); del numero resta solo un'impronta lenta, che
# riattacca le penalita' P2P a chi rientra. SPENTA di serie: si accende
# sul collaudo, poi qui quando Andrea decide.
ACCOUNT_CANCELLABILE = False
# L'ASSISTENZA IN APP (3 nov 2026, richiesta di Andrea): in Profilo →
# Impostazioni la voce «💬 Assistenza», una chat fra chi usa Barattolo e
# lo staff; gli admin (ADMIN_IDS) vedono TUTTE le conversazioni, una per
# utente, nel gruppo Amministrazione, e rispondono da li'. Ogni
# messaggio nuovo avvisa OGNI admin sul canale scelto nel suo profilo
# (al piu' uno ogni 10 minuti per conversazione). SPENTA di serie: si
# accende dopo la prova sulla VM di collaudo.
ASSISTENZA_ATTIVA = False

# ENTRA DAL BOT (19 ott 2026, cantiere account-doppio-bot): sul web e
# nella PWA «Entra con Telegram» apre il bot con un codice monouso, e
# entra l'account ATTIVO nell'app di Telegram (il widget di Telegram
# entrava sempre con quello ricordato dal browser). Vuole il campanello
# del bot acceso (TELEGRAM_WEBHOOK_SEGRETO): senza, resta il widget.
# SPENTA di serie: si accende dopo la prova.
LOGIN_DAL_BOT = False

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

# LA CSP ACCESA (10 ott 2026): la Content-Security-Policy delle pagine
# e' VERA — il browser blocca script da host estranei, base-uri, plugin
# e form verso fuori, e riferisce a /api/csp-report (journal «🛡️ CSP:»).
# NASCE ACCESA nel codice, al contrario delle altre leve: il rischio e'
# stato misurato (nove giorni di sola prova) e la via di fuga e' questa
# riga. Se qualcosa si rompe: `CSP_ATTIVA = False` qui, riavvio, e la
# CSP torna in sola prova (Report-Only, stesse direttive, stesso
# cestino) senza deploy. Poi si legge il journal e si riaccende.
CSP_ATTIVA = True

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

# IL SEGNALE DEL TUNNEL (ott 2026): il segreto che il blocco onion del
# Caddyfile mette nell'header `X-Barattolo-Onion` e che il blocco pubblico
# cancella (`header_up -X-Barattolo-Onion`). Con ONION_HOST acceso e
# questo segreto qui e la', il cookie di sessione dato sul .onion esce
# SENZA l'attributo Secure — l'unico modo perche' il login regga anche su
# Chrome, Brave e Vanadium con Orbot, che un cookie Secure su http lo
# scartano (Tor Browser invece lo tiene). Sul dominio pubblico non cambia
# niente. VUOTO = com'e' sempre stato: il cookie resta Secure ovunque.
# Un valore lungo e a caso (`openssl rand -hex 24`), lo stesso nel
# Caddyfile; la procedura sta in PRODUZIONE, «IL COOKIE SUL TUNNEL».
ONION_SEGNALE = ""

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

# --- L'istanza di prova (collaudo dal telefono) ------------------------
# (19 ott 2026, cantiere collaudo-vm; il disegno:
# docs/STUDIO-ISTANZA-PROVA-2026-10-08.md.) Una copia di
# Barattolo che gira come quella vera, su un'ALTRA macchina, col SUO bot,
# per provare dal telefono i rami prima dell'ok al push.
# CHI PUO' USARLA: gli id Telegram in lista e le chiavi Nostr dei tester
# (la npub, o i 64 esadecimali: valgono il loro account nativo, e il
# login Nostr col bunker resta acceso per loro). Chi non e' in lista non
# vede NIENTE: le API rispondono 403 «Istanza di prova, privata», ogni
# altra pagina torna a `/`, dove la Mini App mostra la copertina
# «Collaudo privato» col login; restano aperti solo la salute, il
# webhook del bot, il login e il guscio della pagina (script e icone).
# Il bot non risponde loro, nemmeno al /start. Chi e' entrato riceve un
# cookie d'ammissione (30 giorni, firmato con una chiave che nasce dal
# BOT_TOKEN). Il pannello «⚙️ Stato delle leve» dice QUANTI sono, mai
# quali. VUOTA = nessun filtro, ed e' la produzione: qui resta vuota.
# Una lista scritta male (una stringa, un nome, una npub col checksum
# sbagliato) chiude la prova a TUTTI, e il journal lo dice.
PROVA_SOLO_IDS = []
# APRIRE LA PROVA A TUTTI (23 ott 2026): True e chiunque entra — le API
# rispondono, il bot risponde, niente copertina. La lista NON si
# svuota: resta il segno che questa e' una prova, e da lei dipendono il
# recinto dei relay (annunci e post mai sui relay veri), il tetto degli
# ordini P2P e la semina. Il P2P resta comunque di P2P_PROVA_IDS. In
# produzione non ha effetto (lista vuota = gia' aperta); qui False.
PROVA_APERTA = False
# IL CONFIG DELLA PROVA si scrive DA QUI e non copiando quello del VPS
# (che non lascia mai il VPS): sotto ci sono le righe che cambiano,
# tutto il resto resta com'e' in questo file. MAI una chiave vera — ne'
# il BOT_TOKEN di produzione (ruberebbe il webhook), ne' una chiave
# LNbits che paga sats veri, ne' una nsec. Sulla vm-2050 i segreti NON
# stanno nemmeno nel config: nascono sulla VM in /etc/barattolo-collaudo
# (root:collaudo 640) e il config li legge da li' con una funzione
# `_segreto(nome)` (docs/COLLAUDO.md, «Il config»).
#   MODALITA_COLLAUDO = False          # identita' Telegram vere, col bot di prova
#   DB = "dati/satmarket.db"
#   URL_PUBBLICO = "https://collaudo.barattolo.store"
#   LINK_BOT = "https://t.me/<bot di prova>"
#   TELEGRAM_MINIAPP_LINK = "https://t.me/<bot di prova>"
#   BOT_TOKEN = "<token del bot di prova, da BotFather>"
#   TELEGRAM_WEBHOOK_SEGRETO = "INCOLLA_QUI_UN_SEGRETO_NATO_SULLA_PROVA"
#   PROVA_SOLO_IDS = [<id di Andrea>, <id di Alan>]
#   ADMIN_IDS = [<id di Andrea>, <id di Alan>]
#   FONDATORI = [<id di Andrea>, <id di Alan>]
#   BANNER_TEST = True
#   BANNER_TEST_TESTO = "🧪 Questa è l'istanza di PROVA: dati finti, sats finti."
#   # i pagamenti: LNbits della prova col portafoglio FINTO (FakeWallet)
#   LNBITS_URL = "http://127.0.0.1:5001"
#   LNBITS_INVOICE_KEY = "INCOLLA_QUI_LA_INVOICE_KEY_DEL_WALLET_DI_PROVA"
#   LNBITS_ADMIN_KEY = "INCOLLA_QUI_LA_ADMIN_KEY_DEL_WALLET_DI_PROVA"
#   LNBITS_NODO_URL = "http://127.0.0.1:5001"
#   LNBITS_NODO_INVOICE_KEY = "INCOLLA_QUI_LA_STESSA_INVOICE_KEY"
#   LNBITS_NODO_ADMIN_KEY = "INCOLLA_QUI_LA_STESSA_ADMIN_KEY"
#   CASSAFORTE_NUOVA = True
#   LND_PONTE_MACAROON_LETTURA = ""    # LND «spento»: decide LNbits
#   LND_PONTE_MACAROON_HOLD = ""
#   GUARDIANO_PONTE = False
#   # Nostr: sull'istanza di prova il server parla SOLO coi relay di casa
#   # (il loopback), qualunque cosa ci sia scritto qui: vuota vuol dire
#   # NESSUNO, mai «quelli di serie». Fuori dal recinto restano solo il
#   # P2P (Mostro) e il login col bunker dei tester. La chiave e' NUOVA.
#   NOSTR_NSEC_PIATTAFORMA = "INCOLLA_QUI_LA_NSEC_NUOVA_DEL_COLLAUDO"
#   RELAY_NOSTR = ["ws://127.0.0.1:7777"]   # il relay di prova sulla VM, o []
#   RELAY_NOSTR_IMPORT = []
#   IMPORT_NOSTR_APERTO = False
#   TRASLOCO_NOSTR = False
#   # Il P2P (decisione di Andrea con Alan, 20 ott 2026): il coordinatore
#   # VERO, quindi ordini e sats veri, coi paletti: lo usano solo gli id
#   # in lista, ogni ordine al massimo P2P_MAX_SATS_PROVA, e sulla VM MAI
#   # la chiave di moderatore/solver ne' altre chiavi Mostro di
#   # produzione (le dispute degli ordini del collaudo si risolvono dal
#   # Barattolo vero). I relay sono le STESSE righe della produzione,
#   # relay.barattolo.store compreso (decisione di Andrea, 20 ott: i
#   # relay veri solo per il P2P; annunci, post e DM restano nel
#   # recinto). Le dice il VPS: grep -n "^MOSTRO_RELAY".
#   SEGRETI_PROFILO_P2P = {1: "INCOLLA_QUI_UN_SEGRETO_NATO_SULLA_PROVA"}
#   P2P_ATTIVO = True
#   P2P_PROVA_IDS = [<gli stessi di PROVA_SOLO_IDS>]
#   P2P_MAX_SATS_PROVA = 10_000
#   MOSTRO_RELAY = [<le stesse della produzione>]
#   MOSTRO_RELAY_SPECCHIO = [<le stesse della produzione>]
#   MOSTRO_RELAY_CONFERMA = [<le stesse della produzione>]
#   MERCATINO_CHAT_ORDINI = True       # la chat negli ordini, da provare
#   MERCATO_LAVORO = True              # le schede Mercato e Lavoro, da provare
#   AVVISO_DM_NOSTR = False
#   AVVISO_DM_NOSTR_RELAY = []
#   RONDA_RELAY_MOSTRO = False
#   RONDA_RELAY_NOSTR = False
#   RONDA_RELAY_CANARINO = []
#   ZAP_ATTIVO = False
#   X_RIPUBBLICA = False
#   # canali e post: niente esce verso i canali veri
#   TELEGRAM_CANALE_ID = ""
#   TELEGRAM_CANALE_RIEPILOGO = ""
#   TELEGRAM_CANALE_VETRINA = ""       # o il canale di prova, privato
#   TELEGRAM_CANALE_BITCOIN_PODCAST = ""
#   ADMIN_CANALE_ID = 0
#   POST_AUTOMATICI = False
#   RIEPILOGO_SETTIMANALE = False
#   # il resto del mondo: spento
#   ANTHROPIC_API_KEY = "INCOLLA_QUI_LA_API_KEY"
#   CONNETTORI_NEGOZIO_APERTI = False
#   CONNETTORI_NEGOZIO_PER_TUTTI = False
#   ONION_HOST = ""
#   CHIAVE_CONTENUTI_DIGITALI = "INCOLLA_QUI_UNA_CHIAVE_NATA_SULLA_PROVA"
