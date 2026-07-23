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
                             # decide le dispute e riceve gli avvisi

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
ORE_CONFERMA = 72            # finestra dell'acquirente dopo la consegna
GIORNI_AUTO_SBLOCCO = 10     # sblocco d'ufficio dopo la spedizione
TETTO_SATS_ANNUNCIO = 0      # prezzo massimo per annuncio: 0 = nessun
                             # limite (default). Mettici es. 100_000 per
                             # accendere il tetto; per gli annunci in EUR
                             # vale l'equivalente al cambio corrente

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

# --- Collaudo ---------------------------------------------------------
# True  = test locale con utenti finti (Compratore/Venditore/Admin)
# False = OBBLIGATORIO prima di andare online!
MODALITA_COLLAUDO = True
