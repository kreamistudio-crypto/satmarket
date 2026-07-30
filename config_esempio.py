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
ADMIN_IDS = [123456789]      # il TUO user id Telegram (da @userinfobot):
                             # decide le dispute e riceve gli avvisi.
                             # Piu' moderatori? Elenca gli id separati da
                             # virgola: [123456789, 987654321]. Sono tutti
                             # pari grado (nessun super-admin) e la lista
                             # si cambia SOLO qui, sul server: nessun
                             # comando dell'app o del bot la tocca.

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

# --- Regole del mercatino --------------------------------------------
COMMISSIONE_PERCENTO = 0     # trattenuta a vendita conclusa (0 = sospesa: cifra da decidere)
PROTEZIONE_PERCENTO = 0      # protezione acquisti a carico del COMPRATORE
                             # (modello Vinted): % sul solo prezzo articolo,
                             # si aggiunge al conto e resta alla piattaforma.
                             # 0 = spenta
ORE_CONFERMA = 72            # finestra dell'acquirente dopo la consegna
GIORNI_AUTO_SBLOCCO = 10     # sblocco d'ufficio dopo la spedizione
SOLLECITO_INCASSO_GIORNI = 7 # ordine «Da incassare» fermo: ogni tot
                             # giorni un promemoria al venditore
                             # (0 = solleciti spenti)
SOLLECITO_INCASSO_MAX = 4    # solleciti ignorati prima che il caso
                             # venga segnalato ai moderatori
TETTO_SATS_ANNUNCIO = 0      # prezzo massimo per annuncio: 0 = nessun
                             # limite (default). Mettici es. 100_000 per
                             # accendere il tetto; per gli annunci in EUR
                             # vale l'equivalente al cambio corrente
MAX_QUANTITA_ANNUNCIO = 100  # pezzi massimi per annuncio (quantita' in
                             # stock): para gli errori di battitura senza
                             # limitare i commercianti veri

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
# uguale, protegge meno un backup rubato.
CHIAVE_CONTENUTI_DIGITALI = ""
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

DB = "satmarket.db"

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

# --- Import aperto da Nostr -------------------------------------------
# Barattolo mostra gli annunci NIP-99 che stanno su Nostr: chiunque
# pubblichi in italiano si ritrova in vetrina, e chi non ci vuole
# stare manda una cancellazione (kind 5) dal suo client, che qui
# viene rispettata per sempre. I filtri sono due: la lingua e la
# legge (parole vietate + AI, la stessa moderazione di chi pubblica
# da qui). NON serve elencare nessuna npub: i venditori si deducono
# dal database e la scoperta trova i nuovi da sola.
# False = nessun relay viene toccato e il mercatino vive come prima.
IMPORT_NOSTR_APERTO = True

# --- Post automatici (la piattaforma racconta i fatti) ----------------
# Ogni nuovo annuncio in vetrina viene annunciato dai canali di
# Barattolo: una nota Nostr (con la chiave piattaforma qui sopra) e un
# post nel canale Telegram. Attivo di default; False per spegnere tutto.
POST_AUTOMATICI = True
# Il canale Telegram di Barattolo: "@nomecanale" oppure l'id numerico
# (-100...). Il bot deve esserne AMMINISTRATORE. Vuoto = niente post
# sul canale (la nota Nostr vive comunque).
TELEGRAM_CANALE_ID = ""
# Anti-spam: quanti post SINGOLI al massimo in un'ora. Oltre (o per le
# raffiche, es. un import CSV) esce un solo post aggregato
# ("N nuovi annunci nel barattolo").
POST_MAX_ORA = 6

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

# --- Contatore dei pionieri (in vetrina, sotto gli oggetti) ----------
# "👥 54 pionieri": quante persone sono già entrate nel mercatino.
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

# --- Collaudo ---------------------------------------------------------
# True  = test locale con utenti finti (Compratore/Venditore/Admin)
# False = OBBLIGATORIO prima di andare online!
MODALITA_COLLAUDO = True
