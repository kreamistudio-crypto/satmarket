# -*- coding: utf-8 -*-
"""
BARATTOLO - BACKEND v1 (Mini App Telegram + Escrow Lightning)
Il server che fa funzionare la Mini App: annunci, ricerca AI,
ordini con escrow in sats via LNbits, notifiche Telegram.

COME FUNZIONA L'ESCROW:
1. L'acquirente clicca "Compra" -> il server crea una invoice Lightning
   sul wallet LNbits della piattaforma (la "cassaforte")
2. L'acquirente paga -> LNbits avvisa il server (webhook) -> ordine LOCKED
3. Il venditore spedisce -> segna "spedito" -> ordine SHIPPED
   (e in qualsiasi momento deposita la SUA invoice Lightning di
   importo = prezzo - commissione: e' l'"IBAN" dove incassare)
4. L'acquirente conferma la ricezione -> se la invoice del venditore
   c'e', il server la paga subito -> ordine RELEASED; se non c'e'
   ancora -> ordine CONFIRMED, e i sats partono appena il venditore
   la deposita
5. In caso di problemi -> DISPUTE: i sats restano fermi finche' un
   admin non decide con /rimborsa o /paga_venditore

AVVERTENZA: questo e' un modello CUSTODIAL (i sats passano dal wallet
della piattaforma). Per un test in community con piccoli importi ok;
per volumi reali serve un parere legale (normativa MiCA).

REQUISITI:  pip install fastapi uvicorn httpx anthropic python-telegram-bot
            (per Nostr, opzionali: websocket-client coincurve)
AVVIO:      uvicorn server:app --host 0.0.0.0 --port 8080
            (serve HTTPS pubblico per la Mini App: vedi LEGGIMI.md)
"""

import asyncio
import base64
import csv
import hashlib
import hmac
import html
import io
import ipaddress
import json
import math
import os
import re
import secrets
import socket
import sqlite3
import ssl
import sys
import time
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from urllib.parse import parse_qsl, urlparse

import anthropic
import httpx
from fastapi import Cookie, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

# websocket-client serve solo alla verifica npub: se manca il pacchetto
# il server parte lo stesso e la verifica risponde con un errore chiaro.
try:
    from websocket import create_connection
except ImportError:
    create_connection = None
# coincurve serve a firmare gli annunci pubblicati verso Nostr e a
# VERIFICARE le firme di chi entra col login Nostr: se manca, quelle
# funzioni restano spente e il server parte lo stesso.
try:
    from coincurve import PrivateKey as ChiavePrivataNostr
    from coincurve import PublicKeyXOnly as ChiavePubblicaNostr
    from coincurve import PublicKey as ChiavePubblicaCompleta
except ImportError:
    ChiavePrivataNostr = None
    ChiavePubblicaNostr = None
    ChiavePubblicaCompleta = None
# cryptography (il cifrario ChaCha20) serve SOLO ai DM Nostr cifrati
# (NIP-44): se manca, le notifiche via DM restano spente e tutto il
# resto vive normalmente (pip install cryptography).
try:
    from cryptography.hazmat.primitives.ciphers import Cipher as CifrarioDM
    from cryptography.hazmat.primitives.ciphers.algorithms import \
        ChaCha20 as ChaCha20DM
except ImportError:
    CifrarioDM = None
    ChaCha20DM = None
# Pillow serve a convertire in JPEG le foto nei formati che i browser
# non sanno leggere (HEIC degli iPhone, e i PNG/WebP arrivati grezzi);
# pillow-heif e' il suo occhio per HEIC/HEIF. Se mancano, le foto
# JPEG gia' pronte passano come sempre e le altre si saltano
# (pip install pillow pillow-heif).
try:
    from PIL import Image as ImmaginePillow
    from PIL import ImageOps
except ImportError:
    ImmaginePillow = None
    ImageOps = None
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pillow_heif = None
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Le stampe del server contengono emoji (⚠️ 📨 ⏰): sulle console
# Windows in cp1252 manderebbero in crash l'avvio o il collaudo.
# Chiediamo l'UTF-8 una volta per tutte; su Linux e' gia' cosi'
# e non cambia nulla.
for _canale in (sys.stdout, sys.stderr):
    if _canale is not None and hasattr(_canale, "reconfigure"):
        _canale.reconfigure(encoding="utf-8", errors="replace")

# ========================= CONFIGURAZIONE =========================
# TUTTE le chiavi e le impostazioni vivono in config.py, che NON va
# mai condiviso ne' caricato su GitHub (e' nel .gitignore).
# Prima volta? Copia config_esempio.py, rinominalo config.py e
# compila i campi.

try:
    from config import (BOT_TOKEN, ANTHROPIC_API_KEY, LNBITS_URL,
                        LNBITS_INVOICE_KEY, LNBITS_ADMIN_KEY,
                        ADMIN_IDS, MODALITA_COLLAUDO,
                        COMMISSIONE_PERCENTO, ORE_CONFERMA,
                        GIORNI_AUTO_SBLOCCO, MODELLO_RICERCA, DB)
except ImportError:
    raise SystemExit(
        "\n⚠️  Manca il file config.py!\n"
        "   Copia 'config_esempio.py', rinominalo in 'config.py' e\n"
        "   compila le chiavi al suo interno. Poi riavvia il server.\n")

# La chiave Nostr della piattaforma e' nata dopo: i config.py gia'
# compilati possono non averla. Se manca (o resta il segnaposto) la
# pubblicazione su Nostr e' semplicemente spenta, senza drammi.
try:
    from config import NOSTR_NSEC_PIATTAFORMA
except ImportError:
    NOSTR_NSEC_PIATTAFORMA = ""

# Anche il segreto del webhook e' arrivato dopo: se manca (o resta il
# segnaposto) il bot continua a SOLO mandare messaggi, come ha sempre
# fatto, e il campanello in entrata resta spento.
try:
    from config import TELEGRAM_WEBHOOK_SEGRETO
except ImportError:
    TELEGRAM_WEBHOOK_SEGRETO = ""

# La leva del tetto per annuncio: nata col cantiere doppia valuta ma
# SPENTA di serie (0 = nessun limite). Si accende dal config in un
# minuto, se un giorno servisse. Per gli annunci in EUR varrebbe
# l'equivalente in sats al cambio di pubblicazione (con +20% di
# tolleranza al momento dell'acquisto). NON copre importa_nostr.py,
# che scrive dritto nel database.
try:
    from config import TETTO_SATS_ANNUNCIO
except ImportError:
    TETTO_SATS_ANNUNCIO = 0   # 0 = spento; es. 100_000 per accenderlo

# La protezione acquisti (lug 2026, modello Vinted): percentuale a
# carico del COMPRATORE sul solo prezzo articolo, si aggiunge al conto
# e resta alla piattaforma quando l'affare si chiude bene. Distinta da
# COMMISSIONE_PERCENTO (che si SOTTRAE dal netto del venditore): leve
# su lati diversi del banco, compongono senza doppio conteggio.
try:
    from config import PROTEZIONE_PERCENTO
except ImportError:
    PROTEZIONE_PERCENTO = 0   # 0 = spenta

# I post automatici (la piattaforma che racconta i fatti) sono nati
# dopo: i config.py gia' compilati possono non avere le chiavi. I
# default valgono da soli: post ACCESI (i canali sono giovani, il
# collaudo avviene sul campo), canale Telegram spento finche' non c'e'
# l'id, tetto anti-spam a 6 post singoli l'ora.
try:
    from config import POST_AUTOMATICI
except ImportError:
    POST_AUTOMATICI = True
try:
    from config import TELEGRAM_CANALE_ID
except ImportError:
    TELEGRAM_CANALE_ID = ""
try:
    from config import POST_MAX_ORA
except ImportError:
    POST_MAX_ORA = 6

# Il cartello «siamo in fase di test»: interruttore, testo e link del
# canale vivono nel config, cosi' si cambiano senza cantieri e a
# rodaggio finito basta un False. Se le chiavi mancano, il cartello e'
# semplicemente spento (fail-open come tutto il resto).
try:
    from config import BANNER_TEST
except ImportError:
    BANNER_TEST = False
try:
    from config import BANNER_TEST_TESTO
except ImportError:
    BANNER_TEST_TESTO = ""
try:
    from config import BANNER_TEST_LINK
except ImportError:
    BANNER_TEST_LINK = ""

# Il contatore dei «pionieri» in vetrina: quante persone sono gia'
# entrate nel mercatino. Acceso di serie (in rodaggio il numero e' un
# invito, non una statistica); un False nel config lo spegne quando
# non servira' piu', senza cantieri.
try:
    from config import CONTATORE_UTENTI
except ImportError:
    CONTATORE_UTENTI = True

# Il campanello dei nuovi iscritti: i moderatori sanno chi entra.
# Acceso di serie; il tetto vale sui messaggi SINGOLI, oltre resta
# l'aggregato che non nomina nessuno.
try:
    from config import AVVISI_ISCRITTI
except ImportError:
    AVVISI_ISCRITTI = True
try:
    from config import AVVISI_ISCRITTI_MAX_ORA
except ImportError:
    AVVISI_ISCRITTI_MAX_ORA = 6

# Il sollecito degli incassi fermi (lug 2026): un ordine 'confirmed'
# senza metodo d'incasso tiene i sats in cassaforte, e la notifica
# della conferma parte una volta sola. Ogni SOLLECITO_INCASSO_GIORNI
# l'orologio ricorda al venditore importo e strade per incassare;
# dopo SOLLECITO_INCASSO_MAX solleciti ignorati, UNA segnalazione ai
# moderatori e poi silenzio: il caso e' in mani umane.
try:
    from config import SOLLECITO_INCASSO_GIORNI
except ImportError:
    SOLLECITO_INCASSO_GIORNI = 7   # 0 = solleciti spenti
try:
    from config import SOLLECITO_INCASSO_MAX
except ImportError:
    SOLLECITO_INCASSO_MAX = 4      # poi la palla passa ai moderatori

# Il polso degli ordini (lug 2026): i moderatori sentono nascere e
# chiudersi ogni ordine, col conto di quanti hanno ancora sats in
# cassaforte. A ~60 utenti il tempo reale va bene; se il volume
# crescera', qui si aggreghera' (pattern del drenatore promo).
try:
    from config import AVVISI_ORDINI_ADMIN
except ImportError:
    AVVISI_ORDINI_ADMIN = True     # interruttore: False = silenzio

# Le Offerte (lug 2026, contrattazione stile Vinted): il compratore
# propone una cifra, il venditore accetta/rifiuta/contropropone UNA
# volta, l'accordo da' il diritto di comprare a quel prezzo entro la
# scadenza. L'annuncio non si blocca mai: vince chi paga per primo.
try:
    from config import OFFERTA_MINIMA_PERCENTO
except ImportError:
    OFFERTA_MINIMA_PERCENTO = 50   # sotto questa % del listino non si parte
try:
    from config import ORE_RISPOSTA_OFFERTA
except ImportError:
    ORE_RISPOSTA_OFFERTA = 48      # proposta/controproposta senza risposta -> scaduta
try:
    from config import ORE_PAGAMENTO_OFFERTA
except ImportError:
    ORE_PAGAMENTO_OFFERTA = 24     # accettata ma non pagata -> scaduta
try:
    from config import MAX_OFFERTE_ANNUNCIO
except ImportError:
    MAX_OFFERTE_ANNUNCIO = 3       # tentativi totali per compratore per annuncio

# L'offerta lampo (lug 2026, modello Vinted «sconto ai follower»): il
# venditore sconta a tempo TUTTO l'annuncio; chi l'ha nel barattolo
# viene avvisato in modo anonimo. Lo sconto e' PUBBLICO (vale per
# chiunque compri nella finestra) e a PERCENTUALE (neutro rispetto
# alla valuta del listino, come le offerte). Non tocca mai il prezzo
# del listino: il NIP-99 resta col prezzo pieno, per costruzione.
try:
    from config import LAMPO_ATTIVE
except ImportError:
    LAMPO_ATTIVE = True            # interruttore generale (spento = tutto come prima)
try:
    from config import LAMPO_SCONTI
except ImportError:
    LAMPO_SCONTI = [10, 20, 30]    # le percentuali proposte come chip
try:
    from config import LAMPO_MIN_PERCENTO
except ImportError:
    LAMPO_MIN_PERCENTO = 5         # sotto: uno sconto che non si nota
try:
    from config import LAMPO_MAX_PERCENTO
except ImportError:
    LAMPO_MAX_PERCENTO = 70        # sopra: si svende (freno di sicurezza)
try:
    from config import ORE_LAMPO_OPZIONI
except ImportError:
    ORE_LAMPO_OPZIONI = [6, 24, 48]   # le durate proposte
try:
    from config import MAX_LAMPO_SETTIMANA
except ImportError:
    MAX_LAMPO_SETTIMANA = 2        # lanci per annuncio in 7 giorni (freno)
try:
    from config import GIORNI_COLPO
except ImportError:
    GIORNI_COLPO = 7              # cooldown dell'avviso «ha fatto colpo» per annuncio

# ===================================================================

app = FastAPI(title="Barattolo API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


@app.middleware("http")
async def guardia_csrf(request, call_next):
    """Cintura oltre le bretelle di SameSite=Lax: quando l'identita'
    viaggia nel cookie di sessione (login web), le richieste che
    cambiano stato devono nascere dal nostro stesso sito. Questa
    guardia puo' solo dire di NO, mai concedere nulla: un suo bug
    al massimo blocca una richiesta legittima, mai apre una porta.
    Confrontiamo solo host:porta (netloc): dietro Caddy lo schema
    visto da uvicorn puo' ballare, l'Host inoltrato e' affidabile."""
    if (request.method in ("POST", "PUT", "PATCH", "DELETE")
            and request.url.path.startswith("/api")
            and not request.headers.get("x-tg-init-data")
            and ("barattolo_sessione" in request.cookies
                 or request.url.path.startswith("/api/login/"))):
        origin = request.headers.get("origin", "")
        if origin and urlparse(origin).netloc != request.headers.get("host", ""):
            return JSONResponse({"detail": "Origine non consentita"},
                                status_code=403)
    return await call_next(request)


@app.middleware("http")
async def cache_foto(request, call_next):
    """Le foto degli annunci si possono tenere in tasca un giorno,
    come gli asset: i nomi sono versionati (alla modifica cambia il
    timestamp nel nome), quindi un file non cambia mai sotto lo
    stesso nome e il browser puo' fidarsi della sua copia."""
    risposta = await call_next(request)
    if request.url.path.startswith("/foto/") and risposta.status_code == 200:
        risposta.headers["Cache-Control"] = "public, max-age=86400"
    return risposta


# ------------------------- DATABASE --------------------------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def nuovo_codice_negozio(con) -> str:
    """Codice pubblico del negozio: 8 caratteri casuali, assegnati una
    volta e stabili per sempre. Non deriva dal tg_id, quindi si puo'
    mettere in un URL senza rivelare nulla del venditore."""
    while True:
        codice = secrets.token_hex(4)
        if not con.execute("SELECT 1 FROM utenti WHERE negozio=?",
                           (codice,)).fetchone():
            return codice


# --------------------------- DISTINTIVI -----------------------------
# Si guadagnano USANDO il mercatino e non si perdono mai (append-only:
# se l'admin rimuove un feedback e la media scende, il distintivo gia'
# dato resta — un premio che sparisce ferisce piu' di un raro
# immeritato). Ogni criterio si RICALCOLA dai dati veri, mai contatori
# incrementali: cosi' fusioni e rimozioni si sistemano da sole. I
# criteri "pesanti" contano solo ordini released = sats veri passati
# dall'escrow con la sua commissione: gonfiarli costa piu' del premio.
# "fiducia" = parla di affidabilita' (non di percorso); dal lug 2026
# in pubblico escono TUTTI i guadagnati, e il flag decide solo la
# precedenza: i fiducia stanno in testa al catalogo, quindi in testa
# alla sfilza — quando il dettaglio annuncio tronca a «+N», restano.

DISTINTIVI = [
    dict(id="nostrano", emoji="🟣", nome="Nostrano", fiducia=True,
         descrizione="Npub Nostr verificata con nota pubblica",
         criterio=lambda d: d["npub_verificata"]),
    dict(id="doppia_cittadinanza", emoji="🔗", nome="Doppia cittadinanza",
         fiducia=True,
         descrizione="Telegram e Nostr collegati allo stesso account",
         criterio=lambda d: d["tg_id"] > 0 and d["npub_accesso"]),
    dict(id="specchiato", emoji="🛡️", nome="Specchiato", fiducia=True,
         descrizione="Almeno 10 affari conclusi senza mai perdere "
                     "una disputa",
         criterio=lambda d: d["vendite"] + d["acquisti"] >= 10
                            and d["dispute_perse"] == 0),
    dict(id="pioniere", emoji="🫙", nome="Pioniere", fiducia=False,
         descrizione="Tra i primi 100 iscritti del Barattolo",
         criterio=lambda d: d["posizione"] <= 100),
    dict(id="primo_acquisto", emoji="⚡", nome="Primo acquisto",
         fiducia=False,
         descrizione="Il primo acquisto concluso col deposito di garanzia",
         criterio=lambda d: d["acquisti"] >= 1),
    dict(id="primo_baratto", emoji="🤝", nome="Primo baratto",
         fiducia=False,
         descrizione="La prima vendita conclusa col deposito di garanzia",
         criterio=lambda d: d["vendite"] >= 1),
    dict(id="bottega_avviata", emoji="📦", nome="Bottega avviata",
         fiducia=False,
         descrizione="Almeno 5 annunci pubblicati in vetrina",
         criterio=lambda d: d["annunci"] >= 5),
    dict(id="stimato", emoji="⭐", nome="Stimato", fiducia=False,
         descrizione="Almeno 5 feedback ricevuti con media da 4.5 in su",
         criterio=lambda d: d["fb_ricevuti"] >= 5 and d["fb_media"] >= 4.5),
    dict(id="venditore_rodato", emoji="🏪", nome="Venditore rodato",
         fiducia=False,
         descrizione="Almeno 10 vendite concluse",
         criterio=lambda d: d["vendite"] >= 10),
    dict(id="buon_vicino", emoji="💌", nome="Buon vicino", fiducia=False,
         descrizione="Almeno 5 feedback lasciati agli altri",
         criterio=lambda d: d["fb_lasciati"] >= 5),
    dict(id="fulmine", emoji="🚀", nome="Fulmine", fiducia=False,
         descrizione="3 spedizioni partite entro un giorno dal pagamento",
         criterio=lambda d: d["lampo"] >= 3),
]


def _dati_distintivi(con, tg_id: int) -> dict | None:
    """I numeri veri su cui si giudicano i criteri, ricalcolati sempre
    dalle tabelle (mai da contatori)."""
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    if not u:
        return None
    q = lambda sql, *p: con.execute(sql, p).fetchone()[0]
    fb = con.execute("SELECT COUNT(*) AS n, AVG(voto) AS media "
                     "FROM feedback WHERE per_tg_id=?", (tg_id,)).fetchone()
    return dict(
        tg_id=tg_id,
        npub_verificata=u["npub_verificata"],
        npub_accesso=u["npub_accesso"],
        # posizione d'iscrizione: registrato=0 (chi c'era prima della
        # colonna) = i piu' vecchi di tutti; i nuovi arrivano sempre
        # dopo, quindi la posizione di chi c'e' non peggiora mai
        posizione=q("SELECT COUNT(*) FROM utenti WHERE registrato<? "
                    "OR (registrato=? AND tg_id<=?)",
                    u["registrato"], u["registrato"], tg_id),
        vendite=q("SELECT COUNT(*) FROM ordini WHERE venditore_id=? "
                  "AND stato='released'", tg_id),
        acquisti=q("SELECT COUNT(*) FROM ordini WHERE compratore_id=? "
                   "AND stato='released'", tg_id),
        # disputa persa: il venditore se fini' in rimborso, il
        # compratore se i sats andarono comunque al venditore
        dispute_perse=q("SELECT COUNT(*) FROM ordini WHERE disputata=1 "
                        "AND ((venditore_id=? AND stato='refunded') OR "
                        "(compratore_id=? AND stato='released'))",
                        tg_id, tg_id),
        annunci=q("SELECT COUNT(*) FROM annunci WHERE venditore_id=? "
                  "AND stato!='rimosso'", tg_id),
        fb_ricevuti=fb["n"], fb_media=fb["media"] or 0,
        fb_lasciati=q("SELECT COUNT(*) FROM feedback WHERE da_tg_id=?",
                      tg_id),
        # pagato_il non esiste, ma un ordine mai pagato muore in 30
        # minuti (pulisci_ordini_fantasma): creato+30min e' il tetto
        # fisico del pagamento. Margine a favore del venditore.
        lampo=q("SELECT COUNT(*) FROM ordini WHERE venditore_id=? "
                "AND stato='released' AND spedito_il>0 "
                "AND spedito_il-creato <= ?", tg_id, 86400 + 1800))


def controlla_distintivi(con, tg_id: int) -> list[str]:
    """Il giudice unico: valuta TUTTI i criteri e assegna cio' che
    manca (INSERT OR IGNORE: idempotente, mai doppioni). Niente
    commit, e' del chiamante. Ritorna gli id appena guadagnati,
    per le notifiche 🏅 dei ganci dal vivo."""
    d = _dati_distintivi(con, tg_id)
    if not d:
        return []
    nuovi = []
    for dd in DISTINTIVI:
        if dd["criterio"](d):
            r = con.execute(
                "INSERT OR IGNORE INTO badge_utente"
                "(tg_id, badge_id, ottenuto_il) VALUES(?,?,?)",
                (tg_id, dd["id"], int(time.time())))
            if r.rowcount:
                nuovi.append(dd["id"])
    return nuovi


def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS utenti(
        tg_id INTEGER PRIMARY KEY, nome TEXT, username TEXT,
        ln_address TEXT DEFAULT '',   -- es. mario@walletofsatoshi.com: incassi automatici
        npub TEXT DEFAULT '',         -- npub Nostr auto-dichiarata (badge)
        npub_verificata INTEGER DEFAULT 0,  -- 1 = nota di verifica trovata sui relay
        verifica_codice TEXT DEFAULT '',    -- codice da pubblicare in una nota
        verifica_scade INTEGER DEFAULT 0,   -- il codice vale 1 ora
        registrato INTEGER DEFAULT 0, -- quando l'utente e' entrato la prima volta
        negozio TEXT DEFAULT '',      -- codice pubblico del negozio (URL condivisibile)
        vendite_ok INTEGER DEFAULT 0, acquisti_ok INTEGER DEFAULT 0,
        rating REAL DEFAULT 0, n_feedback INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS annunci(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venditore_id INTEGER, titolo TEXT, descrizione TEXT,
        categoria TEXT, prezzo_sats INTEGER, zona TEXT,
        foto TEXT DEFAULT '',              -- lista JSON: nomi file o URL
        contatto_nostr TEXT DEFAULT '',    -- npub del venditore (annunci importati)
        nostr_event_id TEXT DEFAULT '',    -- evento NIP-99 firmato dalla piattaforma
        stato TEXT DEFAULT 'attivo',      -- attivo | venduto | rimosso
        creato INTEGER
    );
    CREATE TABLE IF NOT EXISTS ordini(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annuncio_id INTEGER, compratore_id INTEGER, venditore_id INTEGER,
        prezzo_sats INTEGER,
        stato TEXT DEFAULT 'creato',
        -- creato | locked | shipped | delivered | confirmed | released
        -- | dispute | return_pending | return_shipped | refund
        -- | refunded | annullato
        -- (delivered = consegnato, finestra di conferma aperta;
        --  return_pending/shipped = rimborso previa restituzione)
        payment_hash TEXT,                 -- invoice dell'acquirente (escrow)
        invoice_venditore TEXT,            -- dove sbloccare i sats
        invoice_rimborso TEXT DEFAULT '',  -- dove rimborsare l'acquirente
        corriere TEXT DEFAULT '', tracking TEXT DEFAULT '',
        corriere_reso TEXT DEFAULT '', tracking_reso TEXT DEFAULT '',
        spedito_il INTEGER DEFAULT 0,      -- per l'auto-sblocco a 10 giorni
        consegnato INTEGER DEFAULT 0,      -- per la finestra delle 72 ore
        sollecito_il INTEGER DEFAULT 0,    -- ultimo promemoria del venditore
        sollecito_incasso_il INTEGER DEFAULT 0, -- ultimo promemoria «incassa!»
        solleciti_incasso INTEGER DEFAULT 0,    -- quanti ne ha ignorati
        creato INTEGER, aggiornato INTEGER
    );
    CREATE TABLE IF NOT EXISTS sessioni(
        -- login web dal browser: nel DB c'e' SOLO l'hash del token,
        -- il token vero vive nel cookie dell'utente e basta
        token_hash TEXT PRIMARY KEY,
        tg_id INTEGER,
        creato INTEGER,
        scade INTEGER
    );
    CREATE TABLE IF NOT EXISTS feedback(
        -- il giudizio reciproco a affare concluso: da qui nascono
        -- rating e n_feedback dell'utente (sempre per RICALCOLO,
        -- mai per incremento: cosi' rimozioni e fusioni si sistemano
        -- da sole)
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ordine_id INTEGER NOT NULL,
        da_tg_id INTEGER NOT NULL,   -- chi lo lascia
        per_tg_id INTEGER NOT NULL,  -- chi lo riceve
        voto INTEGER NOT NULL CHECK(voto BETWEEN 1 AND 5),
        commento TEXT DEFAULT '',
        creato INTEGER,
        UNIQUE(ordine_id, da_tg_id)  -- uno per ordine per parte
    );
    CREATE INDEX IF NOT EXISTS idx_feedback_per
        ON feedback(per_tg_id, creato DESC);
    CREATE TABLE IF NOT EXISTS badge_utente(
        -- i distintivi guadagnati; le definizioni (nome, emoji,
        -- criterio) vivono nel codice, in DISTINTIVI: qui solo
        -- chi, cosa, quando
        tg_id INTEGER NOT NULL,
        badge_id TEXT NOT NULL,
        ottenuto_il INTEGER,
        PRIMARY KEY(tg_id, badge_id)
    );
    CREATE TABLE IF NOT EXISTS doppioni_ignorati(
        -- «non e' un doppione»: la coppia archiviata non si ripropone
        -- mai piu', su nessun dispositivo (per questo vive nel DB e
        -- non in localStorage)
        id_importato INTEGER NOT NULL,  -- riga con contatto_nostr pieno
        id_nativo INTEGER NOT NULL,     -- riga ripubblicata dalla piattaforma
        tg_id INTEGER,
        creato INTEGER,
        PRIMARY KEY(id_importato, id_nativo)
    );
    CREATE TABLE IF NOT EXISTS avvisi_ricerca(
        -- «dimmi quando esce quello che cerco»: i criteri salvati
        -- dall'utente. Il matching gira alla pubblicazione (coda +
        -- drenatore, gemello dei post automatici)
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER NOT NULL,
        categorie TEXT DEFAULT '',    -- '|Elettronica|Motori|' ('' = tutte)
        comune TEXT DEFAULT '',       -- nome dal dataset ('' = tutta Italia)
        lat REAL DEFAULT 0, lon REAL DEFAULT 0,
        raggio_km INTEGER DEFAULT 0,  -- 0 = tutta Italia
        prezzo_max_sats INTEGER DEFAULT 0,  -- tetto in sats (0 = nessuno)
        prezzo_max_eur REAL DEFAULT 0,      -- OPPURE in EUR (mai entrambi)
        parole TEXT DEFAULT '',       -- gia' normalizzate, spazio-separate
        attivo INTEGER DEFAULT 1,     -- 0 = in pausa
        creato INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_avvisi_ricerca_tg
        ON avvisi_ricerca(tg_id);
    CREATE TABLE IF NOT EXISTS avvisi_notificati(
        -- dedup: lo stesso annuncio non suona MAI due volte per lo
        -- stesso utente (modifiche, re-import). Nel DB e non in
        -- memoria: un riavvio non deve far risuonare nulla.
        tg_id INTEGER NOT NULL,
        annuncio_id INTEGER NOT NULL,
        creato INTEGER,
        PRIMARY KEY(tg_id, annuncio_id)
    );
    CREATE TABLE IF NOT EXISTS preferiti(
        -- «nel tuo barattolo»: gli annunci messi da parte col 🫙.
        -- Privati per natura: nessun conteggio pubblico, il
        -- venditore non sa chi ne' quanti (v1)
        tg_id INTEGER NOT NULL,
        annuncio_id INTEGER NOT NULL,
        creato INTEGER,
        PRIMARY KEY(tg_id, annuncio_id)
    );
    CREATE TABLE IF NOT EXISTS offerte(
        -- la contrattazione strutturata (MAI una chat): proposta del
        -- compratore, al massimo UNA controproposta del venditore,
        -- accettazione = diritto di comprare al prezzo concordato
        -- entro la scadenza. L'annuncio NON si blocca mai: vince chi
        -- paga per primo. L'accordo riguarda il SOLO articolo:
        -- spedizione e protezione si sommano sopra come sempre.
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annuncio_id INTEGER NOT NULL,
        compratore_id INTEGER NOT NULL,
        venditore_id INTEGER NOT NULL,
        valuta TEXT DEFAULT 'sats',      -- fotografia della valuta del listino
        importo_sats INTEGER DEFAULT 0,  -- la proposta (l'altro campo resta 0)
        importo_eur REAL DEFAULT 0,
        contro_sats INTEGER DEFAULT 0,   -- la controproposta (0 = nessuna)
        contro_eur REAL DEFAULT 0,
        stato TEXT DEFAULT 'proposta',   -- proposta | controproposta | accettata |
                                         -- rifiutata | scaduta | decaduta | conclusa
        scadenza INTEGER DEFAULT 0,      -- il prossimo appuntamento:
                                         -- risposta oppure pagamento
        ordine_id INTEGER DEFAULT 0,     -- l'ordine nato dall'offerta
        creato INTEGER, aggiornato INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_offerte_annuncio
        ON offerte(annuncio_id, stato);
    CREATE INDEX IF NOT EXISTS idx_offerte_scadenza
        ON offerte(stato, scadenza);
    CREATE INDEX IF NOT EXISTS idx_offerte_compratore
        ON offerte(compratore_id);
    CREATE INDEX IF NOT EXISTS idx_offerte_venditore
        ON offerte(venditore_id);
    CREATE TABLE IF NOT EXISTS offerte_lampo(
        -- lo STORICO dei lanci: la lampo attiva vive sulle colonne
        -- annunci.lampo_* (una sola per annuncio, lettura pubblica
        -- veloce), ma quelle si sovrascrivono e non contano il
        -- passato — questo registro serve al tetto settimanale.
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annuncio_id INTEGER NOT NULL,
        venditore_id INTEGER NOT NULL,
        percento INTEGER, scadenza INTEGER, creato INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_lampo_annuncio
        ON offerte_lampo(annuncio_id, creato);
    """)
    # Migrazione per database creati prima dell'introduzione degli
    # incassi automatici: aggiunge la colonna se manca.
    try:
        con.execute("ALTER TABLE utenti ADD COLUMN ln_address TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # Migrazioni utenti: badge Nostr (npub e verifica), data di
    # registrazione (chi c'era gia' resta senza data: si mostra "—")
    # e npub_accesso = la chiave Nostr che puo' ENTRARE in questa riga
    # (login Nostr). Diversa dal badge npub: quella e' una dichiarazione
    # pubblica, questa e' una credenziale. Oggi la valorizza il login
    # Nostr; domani anche un account Telegram potra' riceverla (doppia
    # cittadinanza) senza toccare lo schema.
    for colonna in ("npub TEXT DEFAULT ''",
                    "npub_verificata INTEGER DEFAULT 0",
                    "verifica_codice TEXT DEFAULT ''",
                    "verifica_scade INTEGER DEFAULT 0",
                    "registrato INTEGER DEFAULT 0",
                    "negozio TEXT DEFAULT ''",
                    "npub_accesso TEXT DEFAULT ''",
                    # canale_notifiche: '' = automatico (Telegram se
                    # tg_id>0, DM Nostr per i nativi), oppure la scelta
                    # esplicita 'telegram' | 'nostr' | 'entrambi'
                    "canale_notifiche TEXT DEFAULT ''",
                    # avatar (lug 2026): il francobollo della foto
                    # profilo, preso dal social di provenienza (foto
                    # Telegram, o picture del kind-0 Nostr). Nome file
                    # in foto/ ('' = niente foto, resta l'iniziale);
                    # avatar_scelta e' il selettore «La tua foto» del
                    # cassetto Identita': '' = automatico (la catena
                    # Telegram → Nostr → iniziale), oppure la scelta
                    # esplicita 'telegram' | 'nostr' | 'nessuna'
                    "avatar TEXT DEFAULT ''",
                    "avatar_aggiornato INTEGER DEFAULT 0",
                    "avatar_scelta TEXT DEFAULT ''"):
        try:
            con.execute(f"ALTER TABLE utenti ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    # La levetta binaria avatar_visibile e' vissuta solo nei DB di
    # collaudo (mai deployata): chi l'aveva spenta passa a 'nessuna'
    # nel selettore che l'ha sostituita, la colonna vecchia resta
    # inerte dov'era
    try:
        con.execute("UPDATE utenti SET avatar_scelta='nessuna' "
                    "WHERE avatar_visibile=0 AND avatar_scelta=''")
    except sqlite3.OperationalError:
        pass   # DB nato dopo la levetta: la colonna vecchia non c'e'
    # Due account non possono condividere la stessa chiave di accesso:
    # lo garantisce il database stesso, non solo il codice.
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_utenti_npub_accesso "
        "ON utenti(npub_accesso) WHERE npub_accesso != ''")
    # Ogni utente riceve il codice pubblico del negozio, una volta sola
    # (i nuovi lo prendono all'ingresso, in verifica_utente)
    for r in con.execute(
            "SELECT tg_id FROM utenti WHERE negozio=''").fetchall():
        con.execute("UPDATE utenti SET negozio=? WHERE tg_id=?",
                    (nuovo_codice_negozio(con), r["tg_id"]))
    # Migrazioni annunci: foto, contatto Nostr, l'evento NIP-99
    # pubblicato dalla piattaforma e la doppia valuta (il venditore
    # sceglie se il listino e' in sats o in EUR; per gli annunci EUR
    # prezzo_sats resta l'equivalente al cambio di pubblicazione)
    # nostr_origine_d/foto: le coordinate dell'evento importato (tag d
    # e URL foto originali), scritte dall'import — servono alla
    # modifica firmata per ricostruire l'evento da sostituire sui relay
    # post_canale_id/post_nostr_id: i riferimenti dei post automatici
    # (message_id nel canale Telegram, event id della nota kind-1),
    # scritti solo dai post singoli — servono al ciclo di vita
    # (✏️ "Venduto" sul canale, cancellazione alla rimozione)
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''",
                    "nostr_event_id TEXT DEFAULT ''",
                    "valuta TEXT DEFAULT 'sats'",
                    "prezzo_eur REAL DEFAULT 0",
                    "nostr_origine_d TEXT DEFAULT ''",
                    "nostr_origine_foto TEXT DEFAULT ''",
                    "post_canale_id INTEGER DEFAULT 0",
                    "post_nostr_id TEXT DEFAULT ''",
                    # lat/lon: coordinate del comune riconosciuto nella
                    # zona (0,0 = non riconosciuta). Scritte una volta
                    # alla pubblicazione/modifica, mai a ogni match; il
                    # backfill vive in backfill_coordinate(), che gira
                    # dopo carica_comuni()
                    "lat REAL DEFAULT 0",
                    "lon REAL DEFAULT 0",
                    # consegna e spedizione (lug 2026, modello Vinted):
                    # la modalita' la sceglie il venditore ('' = non
                    # specificata: annunci storici e importati, per loro
                    # tutto resta come prima che la spedizione esistesse);
                    # il costo e' nella valuta del listino, con
                    # l'equivalente sats al cambio di pubblicazione (lo
                    # stesso patto di prezzo_sats); la taglia del pacco
                    # servira' alle etichette automatiche di domani
                    "consegna TEXT DEFAULT ''",
                    "spedizione_sats INTEGER DEFAULT 0",
                    "spedizione_eur REAL DEFAULT 0",
                    "taglia_pacco TEXT DEFAULT ''",
                    # offerta lampo (lug 2026): lo sconto a tempo su
                    # tutto l'annuncio. percento>0 e scadenza nel futuro
                    # = attiva; oltre la scadenza torna prezzo pieno da
                    # solo (la lettura gatea su scadenza, l'orologio
                    # ripulisce). Non tocca mai prezzo_sats/prezzo_eur.
                    # colpo_avvisato: memoria del cooldown dell'avviso
                    # anonimo «ha fatto colpo» al venditore.
                    "lampo_percento INTEGER DEFAULT 0",
                    "lampo_scadenza INTEGER DEFAULT 0",
                    "lampo_creato INTEGER DEFAULT 0",
                    "lampo_colpo_avvisato INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE annunci ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    # Migrazione categorie (lug 2026): il set nuovo rinomina tre voci
    # vecchie, le altre restano com'erano. COLLATE NOCASE raddrizza
    # anche le maiuscole storte dei vecchi import ('casa' minuscola,
    # vista nei dati veri). Idempotente: su un database gia' migrato
    # questi UPDATE non trovano piu' nulla.
    for vecchia, nuova in (
            ("Sport", "Sport e hobby"), ("Casa", "Casa e giardino"),
            ("Libri", "Libri e media"), ("Elettronica", "Elettronica"),
            ("Abbigliamento", "Abbigliamento"), ("Motori", "Motori"),
            ("Bambini", "Bambini"), ("Animali", "Animali"),
            ("Altro", "Altro")):
        con.execute(
            "UPDATE annunci SET categoria=? "
            "WHERE categoria=? COLLATE NOCASE AND categoria!=?",
            (nuova, vecchia, nuova))
    # Indici per la vetrina a volume (lug 2026): con centinaia di
    # annunci le liste ordinate per data non devono piu' scandire
    # tutta la tabella. Coprono le tre strade calde: vetrina per
    # stato, filtro per categoria, negozio del venditore. Il DESC
    # combacia con l'ORDER BY delle query (e col cursore keyset).
    con.execute("CREATE INDEX IF NOT EXISTS idx_annunci_vetrina "
                "ON annunci(stato, creato DESC, id DESC)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_annunci_categoria "
                "ON annunci(categoria, stato, creato DESC, id DESC)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_annunci_venditore "
                "ON annunci(venditore_id, stato, creato DESC, id DESC)")
    # L'ordinamento per prezzo della vetrina (lug 2026): stesso
    # keyset, chiavi (prezzo_sats, id). L'indice serve i due versi.
    con.execute("CREATE INDEX IF NOT EXISTS idx_annunci_prezzo "
                "ON annunci(stato, prezzo_sats, id)")
    # Il filtro/ordinamento «⚡ In offerta» (lug 2026): keyset su
    # (lampo_scadenza, id) per le lampo vive.
    con.execute("CREATE INDEX IF NOT EXISTS idx_annunci_lampo "
                "ON annunci(stato, lampo_scadenza, id)")
    # Migrazione per i rimborsi delle dispute
    try:
        con.execute("ALTER TABLE ordini ADD COLUMN invoice_rimborso TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # Migrazioni per spedizione, consegna e resi
    for colonna in ("corriere TEXT DEFAULT ''", "tracking TEXT DEFAULT ''",
                    "corriere_reso TEXT DEFAULT ''",
                    "tracking_reso TEXT DEFAULT ''",
                    "spedito_il INTEGER DEFAULT 0",
                    "consegnato INTEGER DEFAULT 0",
                    "sollecito_il INTEGER DEFAULT 0",
                    # il sollecito degli incassi fermi (lug 2026):
                    # quando e' partito l'ultimo e quanti ne sono
                    # gia' partiti (al tetto la palla va ai moderatori)
                    "sollecito_incasso_il INTEGER DEFAULT 0",
                    "solleciti_incasso INTEGER DEFAULT 0",
                    # disputata: 1 se sull'ordine e' stata aperta una
                    # disputa, anche se poi risolta (lo stato viene
                    # sovrascritto: senza questa traccia il distintivo
                    # Specchiato non saprebbe chi ha perso una disputa)
                    "disputata INTEGER DEFAULT 0",
                    # cambio_eur: EUR per BTC al momento della chiusura
                    # (released/refunded). 0 = sconosciuto: gli ordini
                    # storici restano cosi', e nel CSV il campo e' vuoto.
                    "cambio_eur REAL DEFAULT 0",
                    # cambio_ordine: EUR per BTC al momento della
                    # CREAZIONE della invoice — annunci in EUR, e dal
                    # lug 2026 anche i listini sats con la spedizione
                    # ancorata all'euro (e' il cambio che ha fissato i
                    # sats dell'ordine). 0 = nessuna conversione.
                    "cambio_ordine REAL DEFAULT 0",
                    # il conto scomposto (lug 2026, modello Vinted):
                    # prezzo_sats resta il TOTALE in cassaforte (invoice
                    # e rimborso non cambiano semantica), le due quote si
                    # FISSANO alla creazione — il config puo' cambiare,
                    # l'ordine no. L'articolo si deriva per sottrazione.
                    # consegna_scelta: spedizione | ritiro | '' (ordini
                    # storici e annunci senza modalita')
                    "consegna_scelta TEXT DEFAULT ''",
                    "spedizione_sats INTEGER DEFAULT 0",
                    "protezione_sats INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE ordini ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    # Backfill di disputata: questi stati esistono SOLO a valle di una
    # disputa, quindi gli ordini storici che ci si trovano sono marcabili
    # a colpo sicuro. I released passati da una disputa prima della
    # colonna sono irrecuperabili: si perdona, a favore dell'utente.
    con.execute("UPDATE ordini SET disputata=1 WHERE disputata=0 AND stato "
                "IN ('dispute','return_pending','return_shipped',"
                "'refund','refunded')")
    # Distintivi: passata silenziosa su TUTTI gli utenti, a ogni avvio.
    # E' idempotente (INSERT OR IGNORE) e auto-riparante: fusioni,
    # rimozioni e criteri nuovi si sistemano al riavvio successivo.
    # Le notifiche 🏅 spettano solo ai ganci dal vivo, mai a questa.
    for r in con.execute("SELECT tg_id FROM utenti").fetchall():
        controlla_distintivi(con, r["tg_id"])
    con.commit()
    con.close()


init_db()

if MODALITA_COLLAUDO:
    print("=" * 60)
    print("⚠️  MODALITA' COLLAUDO ATTIVA: autenticazione simulata!")
    print("   Metti MODALITA_COLLAUDO = False prima di andare online.")
    print("=" * 60)


# --------------- SICUREZZA: verifica initData Telegram --------------
# Ogni richiesta della Mini App porta l'initData firmato da Telegram:
# cosi' sappiamo CON CERTEZZA chi e' l'utente, senza login/password.

# ----------------------- LOGIN WEB (BROWSER) ------------------------
# Chi apre barattolo.store dal browser puo' entrare col bottone
# "Entra con Telegram" (Login Widget ufficiale). Il server verifica la
# firma di Telegram e apre una SESSIONE: un token casuale nel cookie
# (HttpOnly: il JavaScript non lo vede mai), il suo hash nel database.
# Da li' in poi le API riconoscono l'utente dal cookie, esattamente
# come dentro Telegram lo riconoscono dall'initData.

GIORNI_SESSIONE_WEB = 30   # quanto dura il login dal browser


def upsert_utente(user: dict):
    """Il benvenuto standard: crea l'utente al primo ingresso (con data
    di registrazione e codice negozio), aggiorna nome e username se
    esiste gia'. Stessa accoglienza della Mini App."""
    con = db()
    con.execute(
        "INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
        "VALUES(?,?,?,?,?) "
        "ON CONFLICT(tg_id) DO UPDATE SET nome=?, username=?",
        (user["id"], user.get("first_name", ""), user.get("username", ""),
         int(time.time()), nuovo_codice_negozio(con),
         user.get("first_name", ""), user.get("username", "")))
    con.commit()
    con.close()


def crea_sessione(tg_id: int) -> str:
    """Apre una sessione web: restituisce il token da mettere nel
    cookie, in DB finisce solo il suo hash."""
    token = secrets.token_urlsafe(32)
    adesso = int(time.time())
    con = db()
    con.execute(
        "INSERT INTO sessioni(token_hash, tg_id, creato, scade) "
        "VALUES(?,?,?,?)",
        (hashlib.sha256(token.encode()).hexdigest(), tg_id, adesso,
         adesso + GIORNI_SESSIONE_WEB * 86400))
    con.commit()
    con.close()
    return token


def imposta_cookie_sessione(response: Response, token: str):
    """Il cookie di sessione, identico per ogni porta d'ingresso
    (login Telegram, login Nostr, collegamento account)."""
    response.set_cookie(
        "barattolo_sessione", token,
        max_age=GIORNI_SESSIONE_WEB * 86400, httponly=True,
        secure=not MODALITA_COLLAUDO,   # in locale siamo su http
        samesite="lax", path="/")


def utente_da_sessione(token: str) -> dict | None:
    """Riconosce il browser dal cookie di sessione (login web).
    Confronto tra hash: il token in chiaro non tocca mai il DB."""
    if not token:
        return None
    th = hashlib.sha256(token.encode()).hexdigest()
    con = db()
    r = con.execute(
        "SELECT s.tg_id, u.nome, u.username FROM sessioni s "
        "JOIN utenti u ON u.tg_id = s.tg_id "
        "WHERE s.token_hash=? AND s.scade > ?",
        (th, int(time.time()))).fetchone()
    con.close()
    if not r:
        return None
    return {"id": r["tg_id"], "first_name": r["nome"],
            "username": r["username"]}


def verifica_login_widget(dati: dict) -> dict:
    """Verifica la firma del Login Widget (bottone 'Entra con Telegram'
    nel browser). ATTENZIONE: la chiave e' DIVERSA da quella della
    Mini App! Qui: chiave = SHA256(BOT_TOKEN). Nella Mini App
    (verifica_utente): chiave = HMAC('WebAppData', BOT_TOKEN).
    Controlla anche che il login sia fresco (auth_date entro 5 minuti):
    un payload vecchio non si puo' riusare all'infinito."""
    try:
        dati = dict(dati)
        hash_ricevuto = dati.pop("hash")
        controllo = "\n".join(f"{k}={dati[k]}" for k in sorted(dati))
        chiave = hashlib.sha256(BOT_TOKEN.encode()).digest()
        calcolato = hmac.new(chiave, controllo.encode(),
                             hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calcolato, hash_ricevuto):
            raise ValueError("firma non valida")
        if int(time.time()) - int(dati["auth_date"]) > 300:
            raise ValueError("login troppo vecchio")
        return dati
    except Exception:
        raise HTTPException(401, "Login Telegram non valido")


def verifica_utente(init_data: str, sessione: str = "") -> dict:
    # --- browser col cookie di sessione (login web): niente initData.
    #     Il fallback scatta SOLO a header vuoto: un initData presente
    #     ma invalido resta 401, nessun "declassamento" possibile. ---
    if not init_data:
        user = utente_da_sessione(sessione)
        if user:
            return user
        raise HTTPException(401, "Autenticazione Telegram non valida")
    # --- MODALITA' COLLAUDO: utenti finti per il test dal browser ---
    if MODALITA_COLLAUDO and init_data.startswith("collaudo:"):
        _, uid, nome = init_data.split(":", 2)
        user = {"id": int(uid), "first_name": nome, "username": nome.lower()}
        con = db()
        con.execute(
            "INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
            "VALUES(?,?,?,?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET nome=?, username=?",
            (user["id"], nome, nome.lower(), int(time.time()),
             nuovo_codice_negozio(con), nome, nome.lower()))
        con.commit()
        con.close()
        return user
    # --- flusso normale: initData firmato da Telegram ---
    try:
        dati = dict(parse_qsl(init_data))
        hash_ricevuto = dati.pop("hash")
        controllo = "\n".join(f"{k}={v}" for k, v in sorted(dati.items()))
        chiave = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        hash_calcolato = hmac.new(chiave, controllo.encode(), hashlib.sha256).hexdigest()
        if hash_calcolato != hash_ricevuto:
            raise ValueError("firma non valida")
        user = json.loads(dati["user"])
        con = db()
        con.execute(
            "INSERT INTO utenti(tg_id, nome, username, registrato, negozio) "
            "VALUES(?,?,?,?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET nome=?, username=?",
            (user["id"], user.get("first_name", ""), user.get("username", ""),
             int(time.time()), nuovo_codice_negozio(con),
             user.get("first_name", ""), user.get("username", "")))
        con.commit()
        con.close()
        return user
    except Exception:
        raise HTTPException(401, "Autenticazione Telegram non valida")


def utente_se_autenticato(init_data: str, sessione: str = "") -> dict | None:
    """Autenticazione FACOLTATIVA, solo per le API di vetrina: chi
    arriva da Telegram (o dal collaudo, o col cookie del login web)
    viene riconosciuto, chi guarda dal browser resta anonimo e viene
    servito lo stesso."""
    if not init_data and not sessione:
        return None
    try:
        return verifica_utente(init_data, sessione)
    except HTTPException:
        return None


async def leggi_json(req: Request) -> dict:
    """Legge il body JSON della richiesta. Body rotto (non-JSON, non
    UTF-8, o non un oggetto) = colpa del mittente: 400, non 500."""
    try:
        d = await req.json()
    except Exception:
        raise HTTPException(400, "Richiesta malformata")
    if not isinstance(d, dict):
        raise HTTPException(400, "Richiesta malformata")
    return d


# ------------------- API: LOGIN WEB DAL BROWSER ---------------------

@app.post("/api/login/telegram")
async def login_telegram(req: Request, response: Response):
    """Riceve i dati firmati dal Login Widget, li verifica e apre la
    sessione: da qui in poi il browser e' riconosciuto dal cookie.
    In collaudo accetta anche un'identita' finta ({"collaudo": true}),
    perche' il widget vero pretende il dominio registrato su BotFather
    e su localhost non si fa nemmeno vedere."""
    d = await leggi_json(req)
    if MODALITA_COLLAUDO and d.get("collaudo"):
        user = {"id": int(d["id"]),
                "first_name": str(d.get("first_name", "Tester")),
                "username": str(d.get("first_name", "tester")).lower()}
    else:
        user = verifica_login_widget(d)
    upsert_utente(user)
    token = crea_sessione(int(user["id"]))
    imposta_cookie_sessione(response, token)
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response, barattolo_sessione: str = Cookie("")):
    """Chiude SOLO la sessione di questo browser (altri dispositivi
    restano collegati). Funziona anche con un cookie ormai scaduto:
    pulisce e saluta."""
    if barattolo_sessione:
        con = db()
        con.execute(
            "DELETE FROM sessioni WHERE token_hash=?",
            (hashlib.sha256(barattolo_sessione.encode()).hexdigest(),))
        con.commit()
        con.close()
    response.delete_cookie("barattolo_sessione", path="/")
    return {"ok": True}


# --- Login Nostr: le fondamenta della verifica -----------------------
# Chi vive su Nostr entra dimostrando di possedere la sua chiave: il
# server emette una sfida casuale, il client la firma dentro un evento
# kind-22242 (stile NIP-42, il kind di autenticazione: effimero, i
# relay non lo conservano) e il server controlla la firma Schnorr.
# La nsec NON viaggia mai: arriva solo l'evento gia' firmato.
# Le sfide vivono in memoria: uvicorn e' mono-processo, e se il server
# riparte la sfida muore — il client ne chiede semplicemente un'altra.

SFIDE_LOGIN: dict[str, int] = {}     # sfida -> scadenza (unix)
SECONDI_SFIDA_LOGIN = 300            # 5 minuti per firmare, poi si rifa'

RE_HEX_64 = re.compile(r"[0-9a-f]{64}")
RE_HEX_128 = re.compile(r"[0-9a-f]{128}")


def nuova_sfida_login() -> str:
    """Emette una sfida monouso e fa pulizia di quelle scadute.
    Il tetto a 1000 tiene a bada i bot: oltre, via le piu' vecchie."""
    adesso = int(time.time())
    for s in [s for s, scade in SFIDE_LOGIN.items() if scade < adesso]:
        SFIDE_LOGIN.pop(s, None)
    while len(SFIDE_LOGIN) >= 1000:
        SFIDE_LOGIN.pop(next(iter(SFIDE_LOGIN)))
    sfida = secrets.token_hex(16)
    SFIDE_LOGIN[sfida] = adesso + SECONDI_SFIDA_LOGIN
    return sfida


def verifica_evento_login(evento, host: str) -> str:
    """Controlla l'evento di login firmato dal client, campo per campo,
    e ritorna la pubkey (esadecimale) di chi ha firmato. Qualsiasi cosa
    storta = 401: mai dire all'esterno QUALE controllo e' fallito."""
    err = HTTPException(401, "Login Nostr non valido: riprova")
    if not isinstance(evento, dict):
        raise err
    pubkey, sig = evento.get("pubkey"), evento.get("sig")
    ev_id, tags = evento.get("id"), evento.get("tags")
    creato = evento.get("created_at")
    if evento.get("kind") != 22242 or evento.get("content") != "":
        raise err
    if not (isinstance(pubkey, str) and RE_HEX_64.fullmatch(pubkey)):
        raise err
    if not (isinstance(sig, str) and RE_HEX_128.fullmatch(sig)):
        raise err
    if not (isinstance(ev_id, str) and RE_HEX_64.fullmatch(ev_id)):
        raise err
    if not isinstance(creato, int) or abs(int(time.time()) - creato) > 300:
        raise HTTPException(401, "Login Nostr scaduto: riprova")
    if not (isinstance(tags, list)
            and all(isinstance(t, list)
                    and all(isinstance(x, str) for x in t) for t in tags)):
        raise err
    # La sfida si brucia PRIMA di controllare la firma: monouso anche
    # se il tentativo poi fallisce (chi sbaglia ne chiede un'altra).
    sfida = next((t[1] for t in tags
                  if len(t) >= 2 and t[0] == "challenge"), None)
    if not sfida or SFIDE_LOGIN.pop(sfida, 0) < int(time.time()):
        raise HTTPException(401, "Sfida scaduta: riprova il login")
    # Il tag "relay" porta l'origine della pagina: legare la firma al
    # NOSTRO sito blocca il riuso su altri servizi. Confronto solo su
    # host:porta, come in guardia_csrf (dietro Caddy lo schema balla).
    origine = next((t[1] for t in tags
                    if len(t) >= 2 and t[0] == "relay"), "")
    if not host or urlparse(origine).netloc != host:
        raise err
    # L'id si RICALCOLA con la serializzazione canonica NIP-01 (la
    # stessa di firma_evento): mai fidarsi di quello ricevuto.
    serial = json.dumps([0, pubkey, creato, 22242, tags, ""],
                        separators=(",", ":"), ensure_ascii=False)
    if hashlib.sha256(serial.encode("utf-8")).hexdigest() != ev_id:
        raise err
    try:
        firma_buona = ChiavePubblicaNostr(bytes.fromhex(pubkey)).verify(
            bytes.fromhex(sig), bytes.fromhex(ev_id))
    except Exception:
        firma_buona = False
    if not firma_buona:
        raise err
    return pubkey


# --- Login Nostr: le porte d'ingresso --------------------------------
# Un utente Nostr non ha tg_id: gli diamo un id NEGATIVO derivato
# dalla sua pubkey. Telegram garantisce id positivi, quindi lo spazio
# negativo e' libero per sempre: sessioni, ordini, annunci e admin
# funzionano invariati. La derivazione serve SOLO alla creazione:
# i login successivi trovano la riga per npub_accesso.

BIGLIETTI_COLLEGAMENTO: dict[str, tuple] = {}  # biglietto -> (tg_id, npub, scade)


def tg_id_da_pubkey(pubkey: str, con) -> int:
    """Deriva l'id negativo, sempre in [-2^63, -1]. Una collisione tra
    due chiavi diverse e' fantascienza (compleanno su 2^63), ma se mai
    capitasse si rideriva con un contatore di sale."""
    for sale in range(1000):
        seme = pubkey if sale == 0 else f"{pubkey}:{sale}"
        n = int.from_bytes(hashlib.sha256(seme.encode()).digest()[:8], "big")
        tg_id = -(n >> 1) - 1
        if not con.execute("SELECT 1 FROM utenti WHERE tg_id=?",
                           (tg_id,)).fetchone():
            return tg_id
    raise HTTPException(500, "Riprova tra un attimo")


def crea_utente_nostr(pubkey: str, npub: str) -> int:
    """Nuova riga nativa Nostr: stesso benvenuto di upsert_utente
    (registrato, codice negozio), nome = npub abbreviata. Il badge
    nasce gia' verificato: la firma Schnorr dimostra il possesso
    ancora meglio della nota pubblica."""
    con = db()
    tg_id = tg_id_da_pubkey(pubkey, con)
    con.execute(
        "INSERT INTO utenti(tg_id, nome, username, registrato, negozio, "
        "npub, npub_verificata, npub_accesso) VALUES(?,?,?,?,?,?,1,?)",
        (tg_id, npub[:10] + "…" + npub[-4:], "", int(time.time()),
         nuovo_codice_negozio(con), npub, npub))
    con.commit()
    con.close()
    return tg_id


@app.get("/api/login/nostr/sfida")
def login_nostr_sfida():
    """Primo passo del login Nostr: una sfida fresca da firmare."""
    if ChiavePubblicaNostr is None:
        raise HTTPException(503, "Login Nostr non disponibile: sul "
                                 "server manca il pacchetto coincurve")
    return {"sfida": nuova_sfida_login(),
            "valida_secondi": SECONDI_SFIDA_LOGIN}


@app.post("/api/login/nostr")
async def login_nostr(req: Request, response: Response):
    """Secondo passo: arriva l'evento firmato. Tre strade, in ordine:
    1) npub_accesso conosciuta -> si entra nel suo account;
    2) npub gia' VERIFICATA (badge 🟣) su UN account Telegram non
       ancora collegato -> proponiamo di usare quello (la firma
       dimostra il possesso: collegare e' legittimo), con un
       biglietto monouso e NESSUNA sessione finche' non accetta;
    3) altrimenti nasce un account nativo Nostr. Un badge NON
       verificato non conta: potrebbe essere la dichiarazione falsa
       di qualcun altro, mai dare accesso a quell'account."""
    if ChiavePubblicaNostr is None:
        raise HTTPException(503, "Login Nostr non disponibile: sul "
                                 "server manca il pacchetto coincurve")
    d = await leggi_json(req)
    pubkey = verifica_evento_login(d.get("evento"),
                                   req.headers.get("host", ""))
    npub = hex_to_npub(pubkey)
    con = db()
    r = con.execute("SELECT tg_id FROM utenti WHERE npub_accesso=?",
                    (npub,)).fetchone()
    if r:
        con.close()
        imposta_cookie_sessione(response, crea_sessione(r["tg_id"]))
        return {"ok": True}
    righe = con.execute(
        "SELECT tg_id, nome, username FROM utenti "
        "WHERE npub=? AND npub_verificata=1 AND npub_accesso=''",
        (npub,)).fetchall()
    con.close()
    if len(righe) == 1:
        adesso = int(time.time())
        for b in [b for b, v in BIGLIETTI_COLLEGAMENTO.items()
                  if v[2] < adesso]:
            BIGLIETTI_COLLEGAMENTO.pop(b, None)
        biglietto = secrets.token_hex(16)
        BIGLIETTI_COLLEGAMENTO[biglietto] = (
            righe[0]["tg_id"], npub, adesso + SECONDI_SFIDA_LOGIN)
        return {"collega": {"nome": righe[0]["nome"],
                            "username": righe[0]["username"],
                            "biglietto": biglietto}}
    tg_id = crea_utente_nostr(pubkey, npub)
    imposta_cookie_sessione(response, crea_sessione(tg_id))
    # Il nativo nasce gia' verificato (la firma dimostra il possesso):
    # Nostrano e Pioniere possono scattare subito, avvisati via DM
    await premia_distintivi(tg_id)
    return {"ok": True, "nuovo": True}


@app.post("/api/login/nostr/collega")
async def login_nostr_collega(req: Request, response: Response):
    """L'utente ha accettato: la sua chiave Nostr diventa la chiave
    d'accesso dell'account Telegram esistente, e si entra li'.
    Se invece rifiuta, il client chiude il foglio e basta: il
    biglietto muore da solo, nessun doppione."""
    d = await leggi_json(req)
    dati = BIGLIETTI_COLLEGAMENTO.pop(d.get("biglietto") or "", None)
    if not dati or dati[2] < int(time.time()):
        raise HTTPException(401, "Invito scaduto: riprova il login")
    tg_id, npub = dati[0], dati[1]
    con = db()
    try:
        con.execute("UPDATE utenti SET npub_accesso=? WHERE tg_id=? "
                    "AND npub_accesso=''", (npub, tg_id))
        con.commit()
    except sqlite3.IntegrityError:
        # qualcun altro ha preso quella chiave nel frattempo: mai due
        # account con la stessa npub_accesso (indice unico)
        con.close()
        raise HTTPException(401, "Riprova il login")
    con.close()
    imposta_cookie_sessione(response, crea_sessione(tg_id))
    await premia_distintivi(tg_id)   # doppia cittadinanza appena nata
    return {"ok": True, "collegato": True}


# ------------------------- LNBITS (escrow) --------------------------

async def crea_invoice_escrow(sats: int, memo: str) -> dict:
    """Crea la invoice che l'acquirente paghera': i sats finiscono
    nel wallet della piattaforma (la cassaforte). Scade in 15 minuti:
    se non viene pagata, l'ordine si autodistrugge poco dopo."""
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{LNBITS_URL}/api/v1/payments",
                         headers={"X-Api-Key": LNBITS_INVOICE_KEY},
                         json={"out": False, "amount": sats, "memo": memo,
                               "expiry": 900})
        r.raise_for_status()
        return r.json()  # contiene payment_hash e payment_request (la invoice)


async def invoice_pagata(payment_hash: str) -> bool:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{LNBITS_URL}/api/v1/payments/{payment_hash}",
                        headers={"X-Api-Key": LNBITS_INVOICE_KEY})
        return r.status_code == 200 and r.json().get("paid", False)


async def paga_venditore(invoice: str) -> bool:
    """Sblocca i sats: paga la invoice fornita dal venditore."""
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{LNBITS_URL}/api/v1/payments",
                         headers={"X-Api-Key": LNBITS_ADMIN_KEY},
                         json={"out": True, "bolt11": invoice})
        return r.status_code < 300


def netto_venditore(prezzo_sats: int) -> int:
    """Quanto incassa il venditore: prezzo meno la commissione."""
    return int(prezzo_sats * (100 - COMMISSIONE_PERCENTO) / 100)


async def decodifica_invoice(bolt11: str) -> dict | None:
    """Chiede a LNbits di leggere la invoice del venditore, per
    controllare che l'importo sia giusto PRIMA di salvarla.
    Ritorna il JSON decodificato, o None se la invoice non e' valida."""
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{LNBITS_URL}/api/v1/payments/decode",
                         headers={"X-Api-Key": LNBITS_INVOICE_KEY},
                         json={"data": bolt11})
        if r.status_code >= 300:
            return None
        return r.json()


async def invoice_da_ln_address(ln_address: str, sats: int) -> str | None:
    """INCASSO AUTOMATICO: dato il Lightning address del venditore
    (es. mario@walletofsatoshi.com), chiede al suo wallet una invoice
    dell'importo giusto, senza che il venditore debba fare nulla.
    E' il protocollo standard LNURL-pay. Ritorna la invoice (bolt11)
    oppure None se qualcosa non va."""
    try:
        nome, dominio = ln_address.strip().lower().split("@")
        msat = sats * 1000
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            r = await c.get(f"https://{dominio}/.well-known/lnurlp/{nome}")
            r.raise_for_status()
            meta = r.json()
            if meta.get("tag") != "payRequest":
                return None
            if not (meta.get("minSendable", 0) <= msat <= meta.get("maxSendable", 0)):
                return None   # il wallet non accetta questo importo
            r = await c.get(meta["callback"], params={"amount": msat})
            r.raise_for_status()
            return r.json().get("pr") or None
    except Exception:
        return None


# ----------------------- CAMBIO BTC/EUR -----------------------------
# Serve al controvalore in euro degli affari conclusi (export CSV).
# Cache di 15 minuti; se la rete non risponde si tiene l'ultimo valore
# noto, e se non c'e' mai stato resta 0 = "non disponibile".

_cambio_eur_cache = {"valore": 0.0, "quando": 0.0}


async def cambio_btc_eur() -> float:
    adesso = time.time()
    if (_cambio_eur_cache["valore"] > 0
            and adesso - _cambio_eur_cache["quando"] < 900):
        return _cambio_eur_cache["valore"]
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",
                            params={"ids": "bitcoin", "vs_currencies": "eur"})
            r.raise_for_status()
            valore = float(r.json()["bitcoin"]["eur"])
            if valore > 0:
                _cambio_eur_cache.update(valore=valore, quando=adesso)
    except Exception:
        pass          # fail-open: meglio un cambio vecchio che un errore
    return _cambio_eur_cache["valore"]


async def prezzo_da_payload(d: dict) -> tuple[str, int, float]:
    """Legge il prezzo dal form di pubblicazione/modifica e restituisce
    (valuta, prezzo_sats, prezzo_eur), gia' validati e col tetto di
    rodaggio applicato.

    - 'sats' (default, i client di ieri non sanno di valute): il
      prezzo intero com'e' sempre stato, prezzo_eur resta 0.
    - 'eur': il listino e' prezzo_eur (2 decimali) e prezzo_sats
      diventa l'equivalente al cambio di ADESSO — serve al tetto,
      alla ricerca AI e come ripiego quando il browser non ha il
      cambio. Senza cambio (CoinGecko mai risposto dal boot) non si
      puo' ne' fissare l'equivalente ne' applicare il tetto: 503
      onesto, con l'alternativa di pubblicare in sats."""
    valuta = d.get("valuta", "sats")
    if valuta not in ("sats", "eur"):
        raise HTTPException(400, "Valuta non riconosciuta")
    if valuta == "eur":
        try:
            prezzo_eur = round(float(d.get("prezzo_eur", 0)), 2)
        except (TypeError, ValueError):
            prezzo_eur = 0.0
        if not d.get("titolo") or prezzo_eur <= 0:
            raise HTTPException(400, "Titolo e prezzo obbligatori")
        cambio = await cambio_btc_eur()
        if cambio <= 0:
            raise HTTPException(503, "Il cambio euro non è disponibile in "
                                     "questo momento: riprova tra qualche "
                                     "minuto, oppure pubblica il prezzo "
                                     "in sats")
        prezzo_sats = max(1, round(prezzo_eur / cambio * 100_000_000))
    else:
        prezzo_eur = 0.0
        try:
            prezzo_sats = int(d.get("prezzo_sats", 0))
        except (TypeError, ValueError):
            prezzo_sats = 0
        if not d.get("titolo") or prezzo_sats <= 0:
            raise HTTPException(400, "Titolo e prezzo obbligatori")
    if TETTO_SATS_ANNUNCIO and prezzo_sats > TETTO_SATS_ANNUNCIO:
        raise HTTPException(400, f"Nel rodaggio il prezzo massimo è "
                                 f"{TETTO_SATS_ANNUNCIO:,} sats per annuncio"
                                 .replace(",", " "))
    return valuta, prezzo_sats, prezzo_eur


async def consegna_da_payload(d: dict, valuta: str):
    """Il giudice unico dei campi di consegna (lug 2026): legge il
    payload di pubblica/modifica e ritorna la quaterna
    (consegna, spedizione_sats, spedizione_eur, taglia_pacco), gia'
    normalizzata. Pattern categoria: i valori sconosciuti si
    normalizzano a '' (mai un 400 — i client di ieri non sanno di
    consegne, e non devono rompersi).

    Il costo di spedizione vive nella STESSA valuta del listino:
    - listino sats: spedizione_sats intera, spedizione_eur resta 0
    - listino eur: spedizione_eur (2 decimali) e l'equivalente sats
      al cambio di ADESSO, il patto di prezzo_sats
    Con modalita' che non spedisce ('' o ritiro) il costo e' 0 per
    forza; costo 0 con modalita' che spedisce = spedizione gratuita."""
    consegna = d.get("consegna", "")
    if consegna not in MODALITA_CONSEGNA:
        consegna = ""
    taglia = d.get("taglia_pacco", "")
    if taglia not in TAGLIE_PACCO:
        taglia = ""
    sped_sats, sped_eur = 0, 0.0
    if consegna in ("spedizione", "entrambe"):
        if valuta == "eur":
            try:
                sped_eur = max(0.0, round(float(d.get("spedizione_eur", 0)), 2))
            except (TypeError, ValueError):
                sped_eur = 0.0
            if sped_eur > 0:
                # Il cambio c'e' di sicuro: prezzo_da_payload e' appena
                # passato di qui (503 altrimenti). La guardia resta per
                # prudenza: senza cambio l'equivalente resta 0 e ci
                # pensera' compra() a convertire al momento vero.
                cambio = await cambio_btc_eur()
                if cambio > 0:
                    sped_sats = round(sped_eur / cambio * 100_000_000)
        else:
            try:
                sped_sats = max(0, int(d.get("spedizione_sats", 0)))
            except (TypeError, ValueError):
                sped_sats = 0
            # Sul listino sats il costo scritto in euro resta ANCORATO
            # all'euro (deciso lug 2026, supera la conversione alla
            # pubblicazione): spedizione_eur si salva cosi' com'e' e
            # diventa sats SOLO all'acquisto, col cambio del momento —
            # i «5 €» del venditore valgono sempre 5 €. Qui niente
            # cambio e niente 503: la dipendenza si paga in compra(),
            # e solo per chi sceglie la spedizione. I sats espliciti
            # vincono: fisso batte ancorato. Gli annunci gia'
            # pubblicati col vecchio comportamento (convertiti in
            # sats) hanno spedizione_eur=0 e restano fissi.
            if not sped_sats:
                try:
                    sped_eur = max(0.0, round(float(d.get("spedizione_eur", 0)), 2))
                except (TypeError, ValueError):
                    sped_eur = 0.0
    return consegna, sped_sats, sped_eur, taglia


def testo_prezzo(valuta: str, prezzo_sats: int, prezzo_eur: float) -> str:
    """Il prezzo come lo leggono i moderatori nelle notifiche."""
    if valuta == "eur":
        return f"{prezzo_eur:.2f} EUR (≈ {prezzo_sats} sats)"
    return f"{prezzo_sats} sats"


def spoglia_html(testo: str) -> str:
    """Le notifiche nascono con l'HTML di Telegram (<b>, <i>...): per
    il DM Nostr, che e' testo puro, i tag si tolgono e le entita' si
    sciolgono."""
    return html.unescape(re.sub(r"<[^>]+>", "", testo))


async def _manda_telegram(tg_id: int, testo: str):
    """Il ramo Telegram di notifica(): il messaggio via bot (l'utente
    deve averlo avviato almeno una volta), simulato nel collaudo."""
    if MODALITA_COLLAUDO and tg_id < 100000:
        # Utente finto del collaudo: la notifica si stampa in console
        print(f"📨 [notifica simulata per utente {tg_id}] {testo}")
        return
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     json={"chat_id": tg_id, "text": testo, "parse_mode": "HTML"})


async def _dm_nostr_con_ripiego(npub: str, testo: str, ripiego_tg_id: int):
    """Il ramo Nostr di notifica(), in sottofondo: prova il DM cifrato
    e, se non parte e c'e' una chat Telegram di riserva, usa quella."""
    try:
        ok = await manda_dm_nostr(npub_to_hex(npub), spoglia_html(testo))
    except Exception as e:
        print(f"⚠️ DM Nostr saltato: {e}")
        ok = False
    if not ok and ripiego_tg_id > 0:
        try:
            await _manda_telegram(ripiego_tg_id, testo)
        except Exception as e:
            print(f"⚠️ Anche il ripiego Telegram e' fallito: {e}")


async def notifica(tg_id: int, testo: str):
    """Recapita un avviso sul canale che l'utente preferisce: Telegram,
    DM Nostr cifrato (NIP-17), o entrambi. Senza preferenza decide il
    buon senso: chi ha Telegram riceve li', il nativo Nostr riceve il
    DM. Fail-open totale: mai un errore al flusso chiamante."""
    riga = None
    try:
        con = db()
        riga = con.execute(
            "SELECT canale_notifiche, npub, npub_verificata, npub_accesso "
            "FROM utenti WHERE tg_id=?", (tg_id,)).fetchone()
        con.close()
    except Exception:
        pass          # admin mai registrato o DB in affanno: si va di bot
    # La npub di DESTINAZIONE: solo chiavi dal possesso DIMOSTRATO
    # (credenziale d'accesso, o badge VERIFICATO). Un badge non
    # verificato e' una dichiarazione: mandarci i dettagli degli ordini
    # di Tizio recapiterebbe tutto nella inbox di Caio.
    dest_npub = ""
    if riga:
        dest_npub = riga["npub_accesso"] or \
            (riga["npub"] if riga["npub_verificata"] else "")
    canale = (riga["canale_notifiche"] if riga else "") or \
        ("nostr" if tg_id < 0 else "telegram")
    via_nostr = canale in ("nostr", "entrambi") and bool(dest_npub)
    via_telegram = canale in ("telegram", "entrambi") and tg_id > 0
    if canale == "nostr" and not via_nostr and tg_id > 0:
        via_telegram = True   # preferiva Nostr ma la npub non c'e' piu'
    if via_nostr:
        # In sottofondo: i relay possono metterci secondi e notifica()
        # gira anche dentro l'orologio e gli sblocchi. Il ripiego
        # Telegram scatta solo se non stiamo gia' avvisando li'.
        asyncio.create_task(_dm_nostr_con_ripiego(
            dest_npub, testo, 0 if via_telegram else max(tg_id, 0)))
    if via_telegram:
        await _manda_telegram(tg_id, testo)
    elif not via_nostr and MODALITA_COLLAUDO:
        print(f"🔕 [utente {tg_id}: nessun canale per la notifica] {testo}")


async def notifica_admin(testo: str):
    """Avvisa tutti i moderatori (nel collaudo anche l'identita' 999,
    che stampa in console come le altre notifiche simulate)."""
    destinatari = set(ADMIN_IDS)
    if MODALITA_COLLAUDO:
        destinatari.add(999)
    for tg_id in destinatari:
        await notifica(tg_id, testo)


async def polso_ordini_admin(riga: str):
    """Il polso degli ordini per i moderatori (leva AVVISI_ORDINI_ADMIN):
    una riga quando un ordine nasce o si chiude, col conto di quelli
    che hanno ancora sats in cassaforte. Il segnaposto {aperti} si
    riempie qui con un replace (mai format: i titoli possono avere
    graffe). Solo titolo e importi, mai nomi. Fail-open totale: una
    notifica di cortesia non deve mai toccare il flusso dei soldi."""
    if not AVVISI_ORDINI_ADMIN:
        return
    try:
        con = db()
        aperti = con.execute(
            "SELECT COUNT(*) FROM ordini WHERE stato NOT IN "
            "('creato','annullato','released','refunded')").fetchone()[0]
        con.close()
        await notifica_admin(riga.replace("{aperti}", str(aperti)))
    except Exception as e:
        print(f"⚠️ Polso ordini admin saltato: {e}")


async def premia_distintivi(tg_id: int):
    """Il gancio standard dei distintivi: valuta, committa e POI avvisa
    (mai una notifica dentro una transazione). Fail-open totale: un
    errore qui non deve mai fermare il flusso che stava premiando."""
    try:
        con = db()
        nuovi = controlla_distintivi(con, tg_id)
        con.commit()
        con.close()
    except Exception as e:
        print(f"⚠️ Distintivi saltati per {tg_id}: {e}")
        return
    for did in nuovi:
        dd = next(d for d in DISTINTIVI if d["id"] == did)
        await notifica(tg_id,
                       f"🏅 <b>Nuovo distintivo: {dd['emoji']} "
                       f"{dd['nome']}!</b>\n{dd['descrizione']}. "
                       f"Lo trovi nel tuo Profilo. 🫙")


# ---------------- IL CAMPANELLO DEL BOT (webhook) --------------------
# Per la prima volta il bot non solo parla: ASCOLTA. Telegram consegna
# ogni messaggio a POST /api/telegram/aggiornamenti (webhook con
# segreto condiviso), e il bot risponde a /start. Serve a una cosa
# sola, per ora: il deep-link t.me/ilbarattolobot?start=CODICE con cui
# un utente nato su Nostr (tg_id negativo) FONDE il suo account
# nell'identita' Telegram — annunci, ordini e chiave npub migrano, e
# da quel momento gli arrivano anche gli avvisi Telegram.
# Fail-open come sempre: segnaposto in config = campanello spento,
# bot solo-invio come e' sempre stato.

def webhook_attivo() -> bool:
    return bool(TELEGRAM_WEBHOOK_SEGRETO
                and not TELEGRAM_WEBHOOK_SEGRETO.startswith("INCOLLA"))


_finto_msg_id = 0   # contatore dei message_id simulati in collaudo


async def bot_api(metodo: str, dati: dict):
    """Chiama l'API del bot (sendMessage con tastiere,
    answerCallbackQuery, editMessageText...) e ne restituisce la
    risposta JSON (None su errore: chi non la usa non se ne accorge).
    In collaudo stampa e basta, SEMPRE — a differenza di notifica(),
    che simula solo gli id piccoli degli utenti finti — ma restituisce
    un message_id finto (negativo), cosi' anche il ciclo di vita dei
    post sul canale si collauda in console."""
    global _finto_msg_id
    if MODALITA_COLLAUDO:
        print(f"🤖 [telegram simulato] {metodo} "
              f"{json.dumps(dati, ensure_ascii=False)}")
        _finto_msg_id -= 1
        return {"ok": True, "result": {"message_id": _finto_msg_id}}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/{metodo}",
                json=dati)
            return r.json()
    except Exception as e:
        print(f"⚠️ Bot Telegram, {metodo} non consegnato: {e}")
        return None


# I lasciapassare della fusione, monouso e a vita breve (in memoria,
# come SFIDE_LOGIN: uvicorn e' mono-processo). Due passi, due dizionari:
# il CODICE viaggia nel deep-link t.me/...?start=..., il TOKEN vive
# solo nella tastiera di conferma dentro la chat col bot.
CODICI_FUSIONE: dict[str, tuple[int, int]] = {}       # codice -> (tg_id_nostr, scade)
CONFERME_FUSIONE: dict[str, tuple[int, int, int]] = {}  # token -> (tg_telegram, tg_nostr, scade)
SECONDI_CODICE_FUSIONE = 300


def _pulisci_fusioni():
    """Via i lasciapassare scaduti; il tetto tiene a bada i bot."""
    adesso = int(time.time())
    for d in (CODICI_FUSIONE, CONFERME_FUSIONE):
        for k in [k for k, v in d.items() if v[-1] < adesso]:
            d.pop(k, None)
        while len(d) >= 1000:
            d.pop(next(iter(d)))


@app.post("/api/me/collega-telegram")
def collega_telegram(x_tg_init_data: str = Header(""),
                     barattolo_sessione: str = Cookie("")):
    """L'utente Nostr chiede il lasciapassare per il bot: il frontend
    apre t.me/ilbarattolobot?start=CODICE e il resto succede in chat."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if user["id"] >= 0:
        raise HTTPException(400, "Il tuo Telegram e' gia' collegato: "
                                 "questo bottone serve a chi e' entrato con Nostr")
    _pulisci_fusioni()
    # Un solo invito vivo per account: chiederne uno nuovo brucia i vecchi
    for c in [c for c, v in CODICI_FUSIONE.items() if v[0] == user["id"]]:
        CODICI_FUSIONE.pop(c, None)
    codice = secrets.token_hex(16)
    CODICI_FUSIONE[codice] = (user["id"],
                              int(time.time()) + SECONDI_CODICE_FUSIONE)
    return {"codice": codice, "valida_secondi": SECONDI_CODICE_FUSIONE}


def _guardie_fusione(con, n, p) -> str | None:
    """I motivi per dire di no, ognuno con la sua frase gentile.
    Si chiamano due volte: al /start (feedback immediato) e DENTRO la
    transazione (la parola finale). None = via libera.
    Nota: se P e' un moderatore non c'e' nulla da guardare — e_admin
    ragiona sull'id positivo, che e' proprio quello che sopravvive."""
    if not n or n["tg_id"] >= 0 or not n["npub_accesso"]:
        return ("⏳ Questo account Nostr non esiste piu' (forse e' gia' "
                "stato collegato). Rifai «Collega Telegram» dal sito.")
    if not p:
        return ("🤔 Non ti trovo nell'anagrafe: apri prima la Mini App "
                "del Barattolo, poi riprova col link.")
    if p["npub_accesso"]:
        return ("🔗 Questo Telegram e' gia' collegato a una chiave "
                "Nostr: un account, una chiave.")
    if p["npub"] and p["npub_verificata"] and p["npub"] != n["npub"]:
        # Fondere qui creerebbe un profilo col badge di una chiave e
        # la porta d'ingresso di un'altra: confusione d'identita'.
        # (Un badge NON verificato invece non blocca: e' solo una
        # dichiarazione, e verra' sostituito da quella verificata.)
        return ("🟣 Il tuo profilo dichiara (verificata) un'altra npub: "
                "rimuovila prima dalla scheda Vendi, poi riprova.")
    aperti = con.execute(
        "SELECT COUNT(*) FROM ordini WHERE ((compratore_id=? AND "
        "venditore_id=?) OR (compratore_id=? AND venditore_id=?)) "
        "AND stato NOT IN ('released','refunded','annullato')",
        (n["tg_id"], p["tg_id"], p["tg_id"], n["tg_id"])).fetchone()[0]
    if aperti:
        # Un affare pendente diventerebbe un auto-ordine con sats in
        # cassaforte e regole senza piu' senso. Quelli gia' chiusi
        # invece passano: restano una curiosita' nello storico.
        return ("⚖️ C'e' un affare ancora aperto tra questi due account: "
                "chiudetelo prima, poi collegatevi.")
    return None


def esegui_fusione(id_telegram: int, id_nostr: int):
    """L'atto della fusione: tutto cio' che era dell'account Nostr
    passa all'account Telegram, in UNA transazione — o tutto o niente.
    Ritorna il riepilogo, oppure la frase gentile del rifiuto."""
    con = db()
    try:
        # Lock di scrittura subito: niente corse con l'orologio o con
        # una seconda conferma arrivata nello stesso istante.
        con.execute("BEGIN IMMEDIATE")
        n = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                        (id_nostr,)).fetchone()
        p = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                        (id_telegram,)).fetchone()
        errore = _guardie_fusione(con, n, p)
        if errore:
            con.rollback()
            return errore
        annunci = con.execute(
            "UPDATE annunci SET venditore_id=? WHERE venditore_id=?",
            (id_telegram, id_nostr)).rowcount
        acquisti = con.execute(
            "UPDATE ordini SET compratore_id=? WHERE compratore_id=?",
            (id_telegram, id_nostr)).rowcount
        vendite = con.execute(
            "UPDATE ordini SET venditore_id=? WHERE venditore_id=?",
            (id_telegram, id_nostr)).rowcount
        # I feedback sugli auto-scambi tra le due meta' muoiono: dopo la
        # migrazione quegli ordini avrebbero compratore = venditore, e
        # il voto a se stessi non ha senso (previene anche la collisione
        # UNIQUE quando entrambe le meta' avevano votato lo stesso ordine).
        con.execute("DELETE FROM feedback WHERE ordine_id IN "
                    "(SELECT id FROM ordini WHERE compratore_id=? "
                    " AND venditore_id=?)", (id_telegram, id_telegram))
        con.execute("UPDATE feedback SET da_tg_id=? WHERE da_tg_id=?",
                    (id_telegram, id_nostr))
        con.execute("UPDATE feedback SET per_tg_id=? WHERE per_tg_id=?",
                    (id_telegram, id_nostr))
        # Il browser dell'utente Nostr resta loggato: le sue sessioni
        # migrano vive e al prossimo /api/me si risveglia qui.
        con.execute("UPDATE sessioni SET tg_id=? WHERE tg_id=?",
                    (id_telegram, id_nostr))
        # I distintivi migrano in unione: se entrambe le meta' avevano
        # lo stesso, la PK lo tiene una volta sola (resta quello
        # dell'account Telegram, il doppione Nostr muore sotto)
        con.execute("UPDATE OR IGNORE badge_utente SET tg_id=? "
                    "WHERE tg_id=?", (id_telegram, id_nostr))
        con.execute("DELETE FROM badge_utente WHERE tg_id=?", (id_nostr,))
        # Gli avvisi di ricerca seguono l'utente; il dedup delle
        # notifiche migra in unione come i distintivi (se entrambe le
        # meta' erano gia' state avvisate di un annuncio, una riga basta)
        con.execute("UPDATE avvisi_ricerca SET tg_id=? WHERE tg_id=?",
                    (id_telegram, id_nostr))
        con.execute("UPDATE OR IGNORE avvisi_notificati SET tg_id=? "
                    "WHERE tg_id=?", (id_telegram, id_nostr))
        con.execute("DELETE FROM avvisi_notificati WHERE tg_id=?",
                    (id_nostr,))
        # Il barattolo dei preferiti segue l'utente, in unione come i
        # distintivi (stesso annuncio salvato da entrambe le meta':
        # una riga basta)
        con.execute("UPDATE OR IGNORE preferiti SET tg_id=? WHERE tg_id=?",
                    (id_telegram, id_nostr))
        con.execute("DELETE FROM preferiti WHERE tg_id=?", (id_nostr,))
        # Le offerte seguono l'utente da entrambi i lati del banco;
        # le trattative tra le due meta' (auto-offerte, dopo la
        # fusione) muoiono qui, come i feedback degli auto-scambi.
        con.execute("UPDATE offerte SET compratore_id=? WHERE compratore_id=?",
                    (id_telegram, id_nostr))
        con.execute("UPDATE offerte SET venditore_id=? WHERE venditore_id=?",
                    (id_telegram, id_nostr))
        con.execute("DELETE FROM offerte WHERE compratore_id=? AND "
                    "venditore_id=?", (id_telegram, id_telegram))
        # PRIMA muore la riga Nostr, POI la chiave si accende su quella
        # Telegram: l'indice unico su npub_accesso non ammette il
        # doppio valore nemmeno per un istante.
        con.execute("DELETE FROM utenti WHERE tg_id=?", (id_nostr,))
        con.execute(
            "UPDATE utenti SET npub=?, npub_verificata=1, npub_accesso=?, "
            "verifica_codice='', verifica_scade=0, "
            "ln_address=CASE WHEN ln_address!='' THEN ln_address ELSE ? END, "
            "vendite_ok=vendite_ok+?, acquisti_ok=acquisti_ok+? "
            "WHERE tg_id=?",
            (n["npub"], n["npub_accesso"], n["ln_address"],
             n["vendite_ok"], n["acquisti_ok"], id_telegram))
        # I due passati si pesano da soli: il ricalcolo sulle righe
        # appena migrate fa media e conteggio in un colpo.
        _ricalcola_rating(con, id_telegram)
        # I contatori sommati possono far scattare distintivi nuovi
        # (Specchiato, rodato...): valutazione silenziosa, li vedra'
        # al prossimo giro di Profilo.
        controlla_distintivi(con, id_telegram)
        con.commit()
        return {"annunci": annunci, "ordini": acquisti + vendite,
                "npub": n["npub"], "negozio": p["negozio"]}
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _npub_breve(npub: str) -> str:
    return npub[:10] + "…" + npub[-4:] if len(npub) > 15 else npub


async def avvia_fusione(id_telegram: int, codice: str):
    """/start CODICE: il codice si brucia subito (monouso anche se poi
    qualcosa va storto), le guardie danno il feedback immediato, e la
    parola finale spetta alla conferma sulla tastiera."""
    dati = CODICI_FUSIONE.pop(codice, None)
    if not dati or dati[1] < int(time.time()):
        return await bot_api("sendMessage", {"chat_id": id_telegram,
            "text": "⏳ Questo invito e' scaduto o gia' usato: rifai "
                    "«Collega Telegram» dal sito e riprova col link fresco."})
    id_nostr = dati[0]
    con = db()
    n = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (id_nostr,)).fetchone()
    p = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (id_telegram,)).fetchone()
    errore = _guardie_fusione(con, n, p)
    con.close()
    if errore:
        return await bot_api("sendMessage",
                             {"chat_id": id_telegram, "text": errore})
    _pulisci_fusioni()
    token = secrets.token_hex(16)   # 32 char: nei 64 di callback_data ci sta
    CONFERME_FUSIONE[token] = (id_telegram, id_nostr,
                               int(time.time()) + SECONDI_CODICE_FUSIONE)
    await bot_api("sendMessage", {
        "chat_id": id_telegram, "parse_mode": "HTML",
        "text": (f"🔗 Stai per collegare l'account Nostr "
                 f"<b>{_npub_breve(n['npub'])}</b> a QUESTO account "
                 "Telegram: i suoi annunci, i suoi affari e la sua "
                 "chiave diventeranno tuoi, per sempre (non si puo' "
                 "annullare). Sei tu?"),
        "reply_markup": {"inline_keyboard": [[
            {"text": "✅ Si', collega", "callback_data": f"fondi:{token}"},
            {"text": "❌ No, annulla", "callback_data": f"annulla:{token}"},
        ]]}})


async def gestisci_callback(cb: dict):
    """Il tocco sulla tastiera di conferma. Il token vale solo per il
    Telegram a cui era destinato: il tocco di chiunque altro non conta."""
    await bot_api("answerCallbackQuery", {"callback_query_id": cb.get("id")})
    azione, _, token = (cb.get("data") or "").partition(":")
    if azione not in ("fondi", "annulla"):
        return
    msg = cb.get("message") or {}
    chat = (msg.get("chat") or {}).get("id")
    modifica = lambda testo: bot_api("editMessageText", {
        "chat_id": chat, "message_id": msg.get("message_id"),
        "text": testo, "parse_mode": "HTML"})
    dati = CONFERME_FUSIONE.pop(token, None)
    if (not dati or dati[2] < int(time.time())
            or dati[0] != (cb.get("from") or {}).get("id")):
        return await modifica("⏳ Conferma scaduta: rifai «Collega "
                              "Telegram» dal sito e riprova.")
    if azione == "annulla":
        return await modifica("👌 Annullato: non e' cambiato nulla.")
    esito = esegui_fusione(dati[0], dati[1])
    if isinstance(esito, str):
        return await modifica(esito)
    # Con i due account fusi possiamo finalmente CONTARE i doppioni
    # invece di limitarci al sospetto generico: se il match stretto
    # ne trova, l'avviso diventa un invito concreto.
    con = db()
    doppioni = len(trova_doppioni_nostr(con, dati[0]))
    con.close()
    coda = ("ℹ️ Se pubblicavi gli stessi oggetti anche dal tuo profilo "
            "Nostr, ora potresti avere qualche doppione sui relay.")
    if doppioni:
        quanti = ("un possibile doppione" if doppioni == 1
                  else f"{doppioni} possibili doppioni")
        coda = (f"🔁 Ho trovato {quanti} sui relay (lo stesso oggetto "
                "pubblicato due volte): aprili dal Profilo su Barattolo "
                "per sistemarli con un tocco.")
    await modifica(
        "🎉 <b>Fatto! I tuoi due account ora sono uno.</b>\n"
        f"Sono passati di qua {esito['annunci']} annunci e "
        f"{esito['ordini']} affari. Il link del tuo negozio ora e' "
        f"{URL_PUBBLICO}/negozio/{esito['negozio']} e gli avvisi "
        "Telegram arrivano anche per gli affari nati su Nostr.\n"
        + coda)
    await notifica_admin(f"🔗 Doppia cittadinanza: "
                         f"{_npub_breve(esito['npub'])} → tg {dati[0]}")


async def gestisci_update(update: dict):
    """Smista quel che arriva dal campanello: solo chat private, solo
    testo. Chi scrive al bot potrebbe non aver MAI aperto la Mini App:
    prima di tutto il benvenuto standard in anagrafe."""
    if "callback_query" in update:
        return await gestisci_callback(update["callback_query"])
    msg = update.get("message") or {}
    testo = (msg.get("text") or "").strip()
    mittente = msg.get("from") or {}
    if (not testo or not mittente.get("id") or mittente.get("is_bot")
            or (msg.get("chat") or {}).get("type") != "private"):
        return
    upsert_utente({"id": mittente["id"],
                   "first_name": mittente.get("first_name", ""),
                   "username": mittente.get("username", "")})
    if testo.startswith("/start"):
        parti = testo.split(maxsplit=1)
        if len(parti) == 2:
            return await avvia_fusione(mittente["id"], parti[1].strip())
        return await bot_api("sendMessage", {"chat_id": mittente["id"],
            "text": "🫙 Ciao! Sono il campanello del Barattolo: ti "
                    "avviso quando succede qualcosa nei tuoi ordini. "
                    "Il mercatino vero e' nella Mini App: aprila dal "
                    f"bottone del menu qui sotto, o su {URL_PUBBLICO}"})
    await bot_api("sendMessage", {"chat_id": mittente["id"],
        "text": "Non sono un bot chiacchierone 😅 — tutto il mercatino "
                "vive nella Mini App: aprila dal bottone del menu!"})


@app.post("/api/telegram/aggiornamenti")
async def telegram_aggiornamenti(req: Request):
    """Il campanello: Telegram suona qui per ogni messaggio al bot.
    Superato il controllo del segreto si risponde SEMPRE 200: un
    errore nostro non deve far accodare tentativi a Telegram.
    guardia_csrf non c'entra (niente cookie in queste richieste).
    In collaudo il segreto atteso e' la stringa fissa 'collaudo':
    cosi' il campanello si suona a mano con curl."""
    if not MODALITA_COLLAUDO and not webhook_attivo():
        raise HTTPException(404, "Campanello spento")
    atteso = "collaudo" if MODALITA_COLLAUDO else TELEGRAM_WEBHOOK_SEGRETO
    segreto = req.headers.get("x-telegram-bot-api-secret-token", "")
    if not hmac.compare_digest(segreto, atteso):
        raise HTTPException(403, "Segreto sbagliato")
    try:
        await gestisci_update(await req.json())
    except Exception as e:
        print(f"⚠️ Update Telegram indigesto: {e}")
    return {"ok": True}


_TASK_WEBHOOK = None   # il riferimento tiene vivo il task (senza, il
#                        garbage collector puo' cancellarlo a meta' volo)


@app.on_event("startup")
async def registra_webhook_telegram():
    """Dice a Telegram dove suonare. Idempotente: ogni riavvio ripete
    la stessa registrazione. GUARDIE anti-pasticcio: in collaudo NON
    si tocca MAI il webhook (un test locale col token vero non deve
    rubare il campanello alla produzione), e col segnaposto in config
    non si registra nulla. Ogni strada, presa o saltata, lascia una
    riga nel journal: flush=True perche' sotto systemd lo stdout di
    Python e' bufferizzato e un print senza flush puo' restare
    invisibile a lungo."""
    if MODALITA_COLLAUDO:
        print("🔕 Webhook Telegram: saltato, siamo in collaudo "
              "(il campanello di produzione non si tocca mai da qui)",
              flush=True)
        return
    if not webhook_attivo():
        print("🔕 Webhook Telegram: saltato, TELEGRAM_WEBHOOK_SEGRETO "
              "mancante o ancora segnaposto nel config "
              f"(letto: {len(TELEGRAM_WEBHOOK_SEGRETO)} caratteri). "
              "Il bot resta solo-invio.", flush=True)
        return
    print(f"🔔 Webhook Telegram: registro "
          f"{URL_PUBBLICO}/api/telegram/aggiornamenti …", flush=True)

    async def _registra():
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                    json={"url": f"{URL_PUBBLICO}/api/telegram/aggiornamenti",
                          "secret_token": TELEGRAM_WEBHOOK_SEGRETO,
                          "allowed_updates": ["message", "callback_query"]})
                print("🔔 Webhook Telegram: "
                      f"{r.json().get('description', '?')}", flush=True)
        except Exception as e:
            print(f"⚠️ Webhook Telegram non registrato (il bot resta "
                  f"solo-invio): {e}", flush=True)

    global _TASK_WEBHOOK
    _TASK_WEBHOOK = asyncio.create_task(_registra())


# ------------------------- API: ANNUNCI -----------------------------

FOTO_DIR = "foto"
os.makedirs(FOTO_DIR, exist_ok=True)


def converti_in_jpeg(raw: bytes):
    """Riporta ai ranghi qualsiasi formato che Pillow sa leggere
    (HEIC compreso, se c'e' pillow-heif): un JPEG max 1200px, come
    quelli che il telefono prepara da solo. None se non si apre.
    Questa e' l'UNICA compressione della filiera per i formati che
    passano dal server (il file che esce e' definitivo, mai
    riconvertito): quindi qualita' alta, 88."""
    try:
        img = ImmaginePillow.open(io.BytesIO(raw))
        # L'orientamento EXIF va applicato QUI: il canvas del browser
        # lo fa da solo, Pillow no — senza, le foto verticali degli
        # iPhone arriverebbero sdraiate
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        # LANCZOS anche qui: il filtro di default e' piu' morbido
        img.thumbnail((1200, 1200), ImmaginePillow.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, "JPEG", quality=88)
        return out.getvalue()
    except Exception:
        return None


# La ricetta delle miniature: QUADRATE, ritagliate al centro come la
# card le mostra (aspect-ratio 1:1 + object-fit:cover). La lezione
# della sgranatura (lug 2026): thumbnail() limita il lato LUNGO, cosi'
# una 1200x900 diventava 480x360 e il cover della card quadrata
# ingrandiva il lato corto del 60-70% sugli schermi retina. Col
# ritaglio quadrato il lato corto E' il lato della ricetta. 640 q87
# LANCZOS (il filtro fine, non il BICUBIC frettoloso di default):
# ~60-90KB, nitida anche a 300px CSS per 2x di densita', e sempre
# molto meno del JPEG pieno. Se si ritocca ancora, il backfill
# rigenera da solo le miniature piu' piccole del lato nuovo.
MINIATURA_LATO = 640
MINIATURA_QUALITA = 87


def miniatura_jpeg(raw: bytes):
    """La versione francobollo per le card della vetrina (vedi ricetta
    qui sopra). None senza Pillow o su errore: la card ripiega da
    sola sulla foto grande (fail-open)."""
    if not ImmaginePillow:
        return None
    try:
        img = ImmaginePillow.open(io.BytesIO(raw))
        img = img.convert("RGB")
        # Quadrata senza mai ingrandire: se la foto e' piccola, il
        # quadrato si adatta al suo lato corto
        lato = min(MINIATURA_LATO, min(img.size))
        img = ImageOps.fit(img, (lato, lato),
                           ImmaginePillow.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, "JPEG", quality=MINIATURA_QUALITA, optimize=True)
        return out.getvalue()
    except Exception:
        return None


def _salva_una_foto(annuncio_id: int, indice: int, raw: bytes,
                    versione: str = "") -> str | None:
    """Il nucleo della filiera: scrive il JPEG pieno (gia' pronto,
    QUI non si converte ne' si ricomprime mai) e accanto la gemella
    _min per le card. Nel database resta SOLO il nome pieno: il
    suffisso _min e' una convenzione di nome che il frontend deriva
    da solo. Ritorna il nome del file, o None se non c'era nulla."""
    if not raw:
        return None
    nome = f"a{annuncio_id}_{indice}{versione}.jpg"
    with open(os.path.join(FOTO_DIR, nome), "wb") as out:
        out.write(raw)
    mini = miniatura_jpeg(raw)
    if mini:
        with open(os.path.join(FOTO_DIR,
                               f"a{annuncio_id}_{indice}{versione}_min.jpg"),
                  "wb") as out:
            out.write(mini)
    return nome


def salva_foto(annuncio_id: int, foto_lista: list, versione: str = "") -> list:
    """Salva le foto dell'annuncio. Dalla Mini App di solito arrivano
    gia' ridimensionate in JPEG (base64); quelle che il browser non ha
    saputo leggere (le HEIC degli iPhone) arrivano grezze e le converte
    Pillow qui, se e' installata. Ritorna i nomi dei file."""
    nomi = []
    for i, f in enumerate((foto_lista or [])[:5]):     # max 5 foto
        m = re.match(r"data:image/(jpeg|jpg|png|webp|heic|heif);base64,(.+)",
                     f or "", re.S)
        if not m:
            continue
        try:
            raw = base64.b64decode(m.group(2))
        except Exception:
            continue
        # I JPEG del telefono pesano poco; agli originali da convertire
        # (mai ridimensionati dal browser: gli iPhone moderni superano
        # i 6MB senza sforzo) si concede piu' spazio, tanto Pillow li
        # riporta comunque a un JPEG da 1200px
        if len(raw) > (15_000_000 if ImmaginePillow else 2_500_000):
            continue
        if m.group(1) in ("heic", "heif"):
            if not (ImmaginePillow and pillow_heif):
                print(f"⚠️ Foto HEIC saltata (annuncio #{annuncio_id}): "
                      f"servono i pacchetti pillow e pillow-heif")
                continue
            raw = converti_in_jpeg(raw)
        elif m.group(1) not in ("jpeg", "jpg") and ImmaginePillow:
            # PNG/WebP grezzi: gia' prima finivano in un file .jpg;
            # con Pillow diventano JPEG per davvero
            raw = converti_in_jpeg(raw) or raw
        nome = _salva_una_foto(annuncio_id, i, raw, versione)
        if nome:
            nomi.append(nome)
    return nomi


def _miniatura_da_rifare(percorso_min, percorso_pieno) -> bool:
    """Una miniatura di una ricetta vecchia (lato piu' corto del
    catalogo attuale) va rifatta: si leggono solo le intestazioni
    dei file, non costa niente. Il metro e' il lato CORTO della foto
    piena: e' quello che governa il ritaglio quadrato, e cosi' gli
    originali gia' piccoli non si rifanno a ogni avvio. In dubbio
    si tiene quella che c'e'."""
    try:
        with ImmaginePillow.open(percorso_min) as img:
            lato_min = max(img.size)
        with ImmaginePillow.open(percorso_pieno) as img:
            lato_pieno = min(img.size)
        return lato_min < min(MINIATURA_LATO, lato_pieno)
    except Exception:
        return False


def genera_miniature_mancanti():
    """Passata di recupero all'avvio (in un thread): le foto nate
    prima delle miniature ne ricevono una, e quelle fatte con una
    ricetta vecchia (piu' piccole di oggi) si rifanno da sole.
    Idempotente e fail-open: un errore = una riga in console e si
    va avanti."""
    if not ImmaginePillow:
        return
    fatte = 0
    for nome in os.listdir(FOTO_DIR):
        if not nome.endswith(".jpg") or nome.endswith("_min.jpg"):
            continue
        percorso_pieno = os.path.join(FOTO_DIR, nome)
        percorso_min = os.path.join(FOTO_DIR, nome[:-4] + "_min.jpg")
        if (os.path.exists(percorso_min)
                and not _miniatura_da_rifare(percorso_min, percorso_pieno)):
            continue
        try:
            with open(percorso_pieno, "rb") as f:
                mini = miniatura_jpeg(f.read())
            if mini:
                with open(percorso_min, "wb") as out:
                    out.write(mini)
                fatte += 1
        except OSError as e:
            print(f"⚠️ Miniatura saltata per {nome}: {e}")
    if fatte:
        print(f"🖼️ Miniature generate o aggiornate: {fatte}")


# Le foto dell'import in blocco (da URL o da ZIP) non arrivano dal
# canvas della Mini App: nessuno le ha gia' ridimensionate. Questi
# helper le portano nella filiera buona rispettando il patto della
# SOLA compressione: un JPEG gia' in formato da telefono passa
# verbatim, tutto il resto subisce l'unica conversione di
# converti_in_jpeg. Senza Pillow si accettano solo JPEG piccoli.

def url_foto_ammesso(url: str) -> bool:
    """Guardiano anti-SSRF: gli URL delle foto li scrive l'utente nel
    suo CSV, non un venditore fidato scelto in config come per
    l'import Nostr. Solo http/https, e l'host non deve risolvere a
    indirizzi privati, loopback o link-local: senza questo controllo
    un CSV ostile farebbe bussare il server alla sua stessa rete
    (LNbits, il DB admin del vicino di VPS...). Il DNS-rebinding tra
    controllo e download resta un rischio residuo accettato."""
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.hostname:
            return False
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_multicast or ip.is_reserved
                    or ip.is_unspecified):
                return False
        return True
    except Exception:
        return False


def scarica_foto_import(url: str) -> bytes | None:
    """Scarica una foto per l'import (timeout 10s, tetto 8MB sul file
    grezzo: tanto poi lo ridimensiona la filiera). Ritorna i bytes o
    None, mai eccezioni: una foto morta e' un avviso nel report, non
    un annuncio perso. Sincrona: va chiamata in asyncio.to_thread."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Barattolo/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read(8_000_001)
        if len(raw) > 8_000_000:
            print(f"⚠️ Foto import troppo pesante (> 8MB): {url[:80]}")
            return None
        return raw or None
    except Exception as e:
        print(f"⚠️ Foto import non scaricata ({url[:80]}): {e}")
        return None


def normalizza_foto_import(raw: bytes) -> bytes | None:
    """Porta i bytes grezzi (ZIP o URL) al JPEG definitivo della
    filiera. Un JPEG gia' in misura da telefono (<=1600px sul lato
    lungo) passa VERBATIM: ricomprimerlo sarebbe il passaggio
    JPEG->JPEG vietato dal patto della filiera. Tutto il resto passa
    da converti_in_jpeg, la sua UNICA compressione. Senza Pillow non
    si puo' ne' riconoscere ne' convertire: si accettano solo file
    coi magici del JPEG entro 2.5MB, gli altri si saltano."""
    if not raw:
        return None
    e_jpeg = raw[:3] == b"\xff\xd8\xff"
    if not ImmaginePillow:
        return raw if e_jpeg and len(raw) <= 2_500_000 else None
    if e_jpeg:
        try:
            with ImmaginePillow.open(io.BytesIO(raw)) as img:
                # Verbatim solo se anche DRITTO (orientamento EXIF
                # assente o normale): miniatura_jpeg non ruota, e una
                # foto di macchina fotografica passata verbatim avrebbe
                # la _min sdraiata. Le altre le raddrizza la conversione.
                dritto = img.getexif().get(0x0112, 1) == 1
                if max(img.size) <= 1600 and dritto:
                    return raw
        except Exception:
            return None
    return converti_in_jpeg(raw)


# ------------------- MODERAZIONE CONTENUTI --------------------------
# Tre strati, dal piu' economico al piu' fine:
#   1. filtro parole (qui sotto): gratis, istantaneo, alta precisione
#   2. parere dell'AI (se la chiave e' configurata): capisce contesto
#      e storpiature, e se non risponde si lascia passare (fail-open)
#   3. i moderatori: avvisati di ogni annuncio, possono rimuovere

def normalizza(testo: str) -> str:
    """Prepara il testo al confronto: minuscole, via gli accenti,
    tutto cio' che non e' lettera o cifra diventa uno spazio singolo.
    Cosi' 'Cocaìna!' e 'cocaina' diventano la stessa cosa."""
    t = unicodedata.normalize("NFKD", (testo or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


# Termini GIA' in forma normalizzata (minuscole, senza accenti,
# apostrofi e trattini come spazi). Lista volutamente ad alta
# precisione: dentro solo cio' che in un mercatino non ha quasi mai
# un uso lecito; i casi ambigui (cannabis light, pistola sparachiodi,
# softair, erba del giardino...) li valuta lo strato AI dal contesto.
PAROLE_VIETATE = {
    "armi": ("arma da fuoco", "armi da fuoco", "munizioni", "proiettili",
             "revolver", "glock", "kalashnikov", "ak 47", "silenziatore",
             "tirapugni", "coltello a scatto", "storditore elettrico",
             "taser", "pistola calibro", "canna mozza"),
    "droghe": ("cocaina", "eroina", "marijuana", "hashish", "hascisc",
               "ganja", "mdma", "ecstasy", "anfetamina", "anfetamine",
               "metanfetamina", "ketamina", "lsd", "ghb", "oppio",
               "funghi allucinogeni", "psilocibina"),
    "servizi sessuali": ("escort", "prostituta", "prostitute",
                         "prostituzione", "gigolo", "sesso a pagamento",
                         "prestazioni sessuali", "prestazione sessuale",
                         "massaggio erotico", "massaggi erotici",
                         "incontri hard"),
    "refurtiva": ("refurtiva", "rubato", "rubata", "rubati", "rubate",
                  "provenienza furtiva", "icloud bloccato",
                  "imei bloccato", "blacklist imei"),
    "contraffazioni": ("contraffatto", "contraffatta", "contraffatti",
                       "contraffatte", "replica 1 1", "tarocco",
                       "tarocca", "patacca", "super fake"),
    "documenti falsi": ("documenti falsi", "documento falso",
                        "patente falsa", "patente senza esame",
                        "passaporto falso", "carta d identita falsa",
                        "permesso di soggiorno falso", "diploma falso",
                        "certificato falso", "banconote false",
                        "soldi falsi"),
    "dati personali e account": ("account rubato", "account rubati",
                                 "account hackerato", "account hackerati",
                                 "credenziali rubate", "carta clonata",
                                 "carte clonate", "carding",
                                 "database rubato", "dati rubati"),
    "farmaci": ("viagra", "cialis", "anabolizzanti", "steroidi",
                "xanax", "valium", "rivotril", "ossicodone", "morfina",
                "tramadolo", "metadone", "ozempic", "senza ricetta"),
    "animali protetti": ("avorio", "zanna di elefante",
                         "zanne di elefante", "corno di rinoceronte",
                         "pelle di tigre", "pelle di leopardo",
                         "pelliccia di leopardo", "specie protetta",
                         "specie protette"),
}

MSG_RIFIUTO = ("Questo annuncio non rispetta le regole del mercatino: "
               "su Barattolo è vietato vendere armi, droghe, servizi "
               "sessuali, refurtiva, contraffazioni, documenti, dati "
               "personali, farmaci e animali protetti.")


def controlla_vietato(titolo: str, descrizione: str) -> str | None:
    """Strato 1: il filtro parole. Ritorna la categoria violata,
    oppure None se il testo e' pulito. Il confronto e' a parole
    intere: con gli spazi ai lati, 'erbario' non contiene ' erba '."""
    testo = f" {normalizza(titolo)} {normalizza(descrizione)} "
    for categoria, termini in PAROLE_VIETATE.items():
        for t in termini:
            if f" {t} " in testo:
                return categoria
    return None


# ---------------------------------------------------------------
# GEOGRAFIA — la mappa dei comuni per gli avvisi di ricerca.
# Un CSV committato (dati/comuni.csv, ~7.900 comuni con lat/lon dal
# centro del comune) letto in memoria all'avvio: zero rete, zero
# latenza. Niente Nominatim nel percorso caldo di pubblica().
# La zona degli annunci resta testo libero: se non ci riconosciamo
# un comune, l'annuncio semplicemente non ha coordinate e matcha
# solo i criteri non geografici degli avvisi (imperfezione dichiarata).

COMUNI: dict[str, tuple[float, float]] = {}   # chiave normalizzata -> (lat, lon)
COMUNI_LISTA: list[dict] = []                  # per l'autocomplete del form

# Comuni che sono anche parole comuni: dentro una zona tipo "vendo in
# paese" non devono diventare Paese (TV). Matchano solo se la zona e'
# ESATTAMENTE quel nome. Meglio nessuna coordinata che una sbagliata.
COMUNI_PAROLA = {"paese", "vita", "sale", "calcio", "none", "parete",
                 "ora", "bella", "dolce"}

# Preposizioni e articoli dei nomi ufficiali: 'Reggio nell'Emilia' deve
# rispondere anche a 'reggio emilia', e viceversa la zona scritta
# 'Cassano allo Ionio' deve trovare 'Cassano all'Ionio'.
PREPOSIZIONI_COMUNI = {"di", "del", "della", "dell", "delle", "dei",
                       "degli", "nel", "nell", "nella", "nello",
                       "sul", "sull", "sulla", "sullo", "in",
                       "al", "all", "allo", "alla", "agli", "alle",
                       "la", "lo", "l", "de", "d"}


def carica_comuni():
    """Legge dati/comuni.csv (nome;provincia;lat;lon) e riempie il
    dizionario. Fail-open: file assente o storto = dict vuoto, la
    funzione geografica si spegne e tutto il resto vive. I ~7 nomi
    duplicati d'Italia (Castro, Peglio, Livo...) entrano solo con la
    provincia ('castro bg'): la chiave nuda ambigua si scarta."""
    global COMUNI, COMUNI_LISTA
    try:
        visti: dict[str, tuple[float, float] | None] = {}
        alias: dict[str, tuple[float, float] | None] = {}
        lista = []
        with open(os.path.join("dati", "comuni.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                nome, prov = r["nome"].strip(), r["provincia"].strip()
                coord = (float(r["lat"]), float(r["lon"]))
                chiave = normalizza(nome)
                # None = nome conteso tra piu' province: via dal dict
                visti[chiave] = None if chiave in visti else coord
                visti[normalizza(f"{nome} {prov}")] = coord
                # alias senza preposizioni: 'Reggio nell'Emilia' deve
                # rispondere anche a 'reggio emilia' (e' come lo
                # scrivono tutti). Collisioni tra alias = via.
                corto = " ".join(p for p in chiave.split()
                                 if p not in PREPOSIZIONI_COMUNI)
                if corto and corto != chiave:
                    alias[corto] = None if corto in alias else coord
                lista.append({"nome": nome, "provincia": prov})
        COMUNI = {k: v for k, v in visti.items() if v is not None}
        # i nomi veri vincono sempre: un alias non li tocca ne' li
        # resuscita (se 'castro' e' conteso, resta fuori e basta)
        for k, v in alias.items():
            if v is not None and k not in visti:
                COMUNI[k] = v
        COMUNI_LISTA = lista
        print(f"🗺️ Comuni caricati: {len(lista)}")
    except Exception as e:
        COMUNI, COMUNI_LISTA = {}, []
        print(f"🗺️ Comuni non caricati ({e}): avvisi solo non-geografici")


def coordinate_da_zona(zona: str) -> tuple[float, float]:
    """Estrae le coordinate dal testo libero della zona. Scansione
    degli n-grammi dal piu' lungo al piu' corto ('San Valentino in
    Abruzzo Citeriore' prima di 'Abruzzo'), a parita' vince il primo
    nel testo (la gente scrive prima il proprio paese: 'tra Pavia e
    Milano' -> Pavia). 'vicino Milano' -> Milano: il raggio
    dell'avviso assorbe il 'vicino'. (0,0) = non riconosciuta."""
    token = normalizza(zona).split()
    if not token or not COMUNI:
        return (0.0, 0.0)
    intera = " ".join(token)
    if intera in COMUNI:            # zona = esattamente un comune,
        return COMUNI[intera]       # vale anche per i COMUNI_PAROLA

    def scandisci(parole):
        for lung in range(min(6, len(parole)), 0, -1):
            for i in range(len(parole) - lung + 1):
                chiave = " ".join(parole[i:i + lung])
                if lung == 1 and chiave in COMUNI_PAROLA:
                    continue
                if chiave in COMUNI:
                    return COMUNI[chiave]
        return None

    trovato = scandisci(token)
    if trovato is None:             # secondo giro senza preposizioni:
        asciutti = [p for p in token if p not in PREPOSIZIONI_COMUNI]
        if asciutti and asciutti != token:
            trovato = scandisci(asciutti)
    return trovato or (0.0, 0.0)


def distanza_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine: chilometri in linea d'aria tra due punti."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = rlat2 - rlat1
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def backfill_coordinate():
    """Da' le coordinate agli annunci nati prima delle colonne lat/lon.
    Idempotente e leggero: riprova solo le righe ancora a (0,0) con una
    zona scritta — quelle irriconoscibili si riscandiscono a ogni avvio,
    costo di pochi millisecondi (e un domani un dataset piu' ricco le
    puo' ripescare)."""
    try:
        con = db()
        righe = con.execute("SELECT id, zona FROM annunci "
                            "WHERE lat=0 AND lon=0 AND zona!=''").fetchall()
        trovate = 0
        for r in righe:
            lat, lon = coordinate_da_zona(r["zona"])
            if lat or lon:
                con.execute("UPDATE annunci SET lat=?, lon=? WHERE id=?",
                            (lat, lon, r["id"]))
                trovate += 1
        con.commit()
        con.close()
        if trovate:
            print(f"🗺️ Coordinate date a {trovate} annunci esistenti")
    except Exception as e:
        print(f"🗺️ Backfill coordinate saltato: {e}")


carica_comuni()
backfill_coordinate()


PROMPT_MODERAZIONE = (
    "Sei il moderatore di un mercatino dell'usato italiano. Valuta se "
    "l'annuncio e' lecito. E' VIETATO vendere: armi da fuoco VERE e "
    "funzionanti, munizioni, armi bianche da offesa; droghe; servizi "
    "sessuali o prostituzione; refurtiva; contraffazioni; documenti "
    "falsi; dati personali o account; farmaci con obbligo di ricetta; "
    "animali protetti. NON e' vietato l'uso legittimo: attrezzi da "
    "lavoro (sparachiodi, pistole per silicone o vernice), giocattoli, "
    "softair e repliche, fucili subacquei, coltelli da cucina, oggetti "
    "da collezione disattivati, farmaci da banco citati di passaggio "
    "nella descrizione di altro. Riconosci storpiature e mascheramenti "
    "(numeri al posto di lettere, spazi o simboli in mezzo alle "
    "parole). Se l'annuncio e' ambiguo ma plausibilmente lecito "
    "rispondi OK: ogni annuncio pubblicato viene comunque notificato "
    "a un moderatore umano che puo' rimuoverlo. Riserva VIETATO ai "
    "casi chiari. Esempi: 'Pistola sparachiodi Bosch' -> OK. 'Pistola "
    "softair a molla' -> OK. 'Revolver calibro 38 funzionante con "
    "munizioni' -> VIETATO: arma da fuoco. 'Serata speciale con "
    "tr0mb4mic1' -> VIETATO: servizi sessuali mascherati. Rispondi "
    "con UNA sola riga: OK se l'annuncio va bene, oppure VIETATO: "
    "seguito dal motivo in poche parole. Nessun altro testo.")


async def moderazione_ai(titolo: str, descrizione: str) -> str | None:
    """Strato 2: il secondo paio d'occhi. Ritorna il motivo se
    VIETATO, None se ok. Se la chiave API non c'e' o la chiamata
    fallisce si lascia passare senza bloccare nessuno: il filtro
    parole ha gia' fatto la sua parte."""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("INCOLLA"):
        return None
    try:
        r = await asyncio.to_thread(
            ai.messages.create,
            model=MODELLO_RICERCA, max_tokens=60, timeout=10,
            system=PROMPT_MODERAZIONE,
            messages=[{"role": "user", "content":
                       f"TITOLO: {titolo[:200]}\n"
                       f"DESCRIZIONE: {descrizione[:600]}"}])
        verdetto = "".join(b.text for b in r.content if b.type == "text").strip()
        if verdetto.upper().startswith("VIETATO"):
            return verdetto.split(":", 1)[-1].strip() or "contenuto vietato"
        return None                    # "OK" o risposta strana: si passa
    except Exception as e:
        print(f"⚠️ Moderazione AI saltata (nessun blocco): {e}")
        return None


# L'import in blocco porterebbe 200-500 chiamate di moderazione una in
# fila all'altra: minuti di attesa per spiccioli di testo. A LOTTI
# (~20 annunci per chiamata) la stessa copertura completa costa un
# decimo di dollaro e un minuto per 500 righe. Il prompt e' lo stesso
# del singolo, con l'appendice sul formato a piu' righe.
APPENDICE_LOTTO = (
    " ORA VALUTERAI PIU' ANNUNCI IN UN COLPO SOLO. Rispondi con UNA "
    "riga per ciascun annuncio, nel formato esatto:\n"
    "<numero>: OK\n"
    "oppure\n"
    "<numero>: VIETATO: <motivo in poche parole>\n"
    "dove <numero> e' quello indicato dopo la parola ANNUNCIO. "
    "Nessun altro testo prima o dopo le righe dei verdetti.")

_RIGA_VERDETTO = re.compile(
    r"^\s*(?:ANNUNCIO\s+)?(\d+)\s*[:.\)\-]\s*(OK|VIETATO.*)$",
    re.IGNORECASE)


async def moderazione_ai_lotto(voci: list) -> dict:
    """Strato 2 per l'import in blocco. voci = [(numero, titolo,
    descrizione)]; ritorna {numero: motivo} SOLO per i VIETATO.
    Fail-open come la sorella singola: chiave assente, errore,
    timeout o risposta interamente storta = dict vuoto (il lotto
    passa, lo strato 1 ha gia' fatto la sua parte) e una riga in
    console. Una riga di verdetto malformata o mancante = quella
    voce passa; i numeri che non appartengono al lotto (allucinati)
    si ignorano."""
    if not voci:
        return {}
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("INCOLLA"):
        return {}
    corpo = "\n\n".join(
        f"ANNUNCIO {n}\nTITOLO: {(t or '')[:200]}\n"
        f"DESCRIZIONE: {(d or '')[:400]}"
        for n, t, d in voci)
    try:
        r = await asyncio.to_thread(
            ai.messages.create,
            model=MODELLO_RICERCA, max_tokens=800, timeout=30,
            system=PROMPT_MODERAZIONE + APPENDICE_LOTTO,
            messages=[{"role": "user", "content": corpo}])
        testo = "".join(b.text for b in r.content if b.type == "text")
        nel_lotto = {n for n, _, _ in voci}
        bocciati = {}
        for riga in testo.splitlines():
            m = _RIGA_VERDETTO.match(riga)
            if not m or int(m.group(1)) not in nel_lotto:
                continue
            verdetto = m.group(2)
            if verdetto.upper().startswith("VIETATO"):
                motivo = verdetto.split(":", 1)[-1].strip()
                bocciati[int(m.group(1))] = motivo or "contenuto vietato"
        return bocciati
    except Exception as e:
        print(f"⚠️ Moderazione AI a lotti saltata (nessun blocco): {e}")
        return {}


# Le categorie del mercatino: UNICA lista lato server, la stessa del
# form di Vendi e delle pillole della vetrina ("Tutto" e' solo una
# vista del frontend, non una categoria). Una categoria sconosciuta
# nel payload finisce in "Altro": il client non decide il catalogo.
CATEGORIE = ("Elettronica", "Casa e giardino", "Abbigliamento",
             "Sport e hobby", "Motori", "Bambini", "Animali",
             "Libri e media", "Altro")


def categoria_valida(c) -> str:
    return c if c in CATEGORIE else "Altro"


# --- Consegna e taglia del pacco (lug 2026, modello Vinted) ----------
# La modalita' di consegna la dichiara il venditore sull'annuncio;
# '' = non specificata (annunci storici e importati da Nostr): per
# loro il flusso resta quello di sempre. I cataloghi sono del server,
# come CATEGORIE: il client non li decide mai.
MODALITA_CONSEGNA = ("spedizione", "ritiro", "entrambe")
TAGLIE_PACCO = ("busta", "piccolo", "medio", "grande", "ingombrante")


def neutralizza_formula(testo: str) -> str:
    """Anti CSV-injection per i testi che arrivano dall'import: una
    cella che inizia con =, + o @ diventerebbe una formula viva se il
    CSV venisse riesportato e aperto in Excel. Si strappano in ciclo i
    caratteri d'innesco iniziali (tab e CR compresi). Il trattino si
    lascia stare: troppi titoli legittimi iniziano con '-', e l'export
    passa comunque dal quoting di csv.writer."""
    t = (testo or "").strip()
    while t and t[0] in "=+@\t\r":
        t = t[1:].lstrip()
    return t


# Il CSV dell'import lo scrivono commercianti, non il form: la
# categoria va presa con tolleranza. Prima il match esatto, poi il
# case-insensitive sul catalogo, poi i sinonimi ovvi (sulla prima
# parola), e chi resta fuori finisce in Altro: il client non decide
# il catalogo, come sempre.
SINONIMI_CATEGORIA = {
    "elettronica": "Elettronica", "electronics": "Elettronica",
    "tech": "Elettronica", "informatica": "Elettronica",
    "telefonia": "Elettronica",
    "casa": "Casa e giardino", "giardino": "Casa e giardino",
    "arredamento": "Casa e giardino", "cucina": "Casa e giardino",
    "abbigliamento": "Abbigliamento", "vestiti": "Abbigliamento",
    "moda": "Abbigliamento", "scarpe": "Abbigliamento",
    "sport": "Sport e hobby", "hobby": "Sport e hobby",
    "collezionismo": "Sport e hobby",
    "motori": "Motori", "auto": "Motori", "moto": "Motori",
    "ricambi": "Motori",
    "bambini": "Bambini", "bimbi": "Bambini", "infanzia": "Bambini",
    "giocattoli": "Bambini",
    "animali": "Animali", "pet": "Animali",
    "libri": "Libri e media", "media": "Libri e media",
    "musica": "Libri e media", "film": "Libri e media",
    "fumetti": "Libri e media",
    "altro": "Altro", "varie": "Altro",
}


def categoria_tollerante(c: str) -> str:
    c = (c or "").strip()
    if c in CATEGORIE:
        return c
    basso = c.lower()
    for cat in CATEGORIE:
        if basso == cat.lower():
            return cat
    prima = basso.split()[0] if basso.split() else ""
    return SINONIMI_CATEGORIA.get(basso) or \
        SINONIMI_CATEGORIA.get(prima, "Altro")


# La vetrina e' PUBBLICA (si guarda anche dal browser, senza Telegram):
# questi sono gli UNICI campi che escono verso gli anonimi. Niente
# venditore_id: l'ID Telegram del venditore non appare mai in vetrina.
# La npub invece e' pubblica per natura: e' fatta per essere condivisa.
CAMPI_VETRINA = (
    "a.id, a.titolo, a.descrizione, a.categoria, a.prezzo_sats, a.zona, "
    "a.valuta, a.prezzo_eur, "
    "a.consegna, a.spedizione_sats, a.spedizione_eur, a.taglia_pacco, "
    "a.foto, a.contatto_nostr, a.creato, "
    # l'offerta lampo e' pubblica per natura (il prezzo barrato deve
    # vedersi in vetrina): percento e scadenza, il resto lo fa il client
    "a.lampo_percento, a.lampo_scadenza, "
    "u.nome AS venditore, u.username AS venditore_username, "
    "u.npub AS venditore_npub, u.npub_verificata AS venditore_npub_verificata, "
    "u.negozio AS venditore_negozio, "
    # il francobollo esce solo con la levetta «Mostra la mia foto»
    # accesa: spenta, il nome file non lascia proprio il server
    "(CASE WHEN u.avatar_scelta='nessuna' THEN '' ELSE u.avatar END) "
    "AS venditore_avatar, "
    "(SELECT GROUP_CONCAT(b.badge_id) FROM badge_utente b "
    " WHERE b.tg_id=a.venditore_id) AS venditore_distintivi, "
    "u.rating, u.vendite_ok")


def espandi_distintivi_vetrina(righe):
    """Il GROUP_CONCAT dei badge diventa la lista di chip
    {id, emoji, nome, descrizione} — gli stessi del negozio pubblico:
    la Mini App non hardcoda mai il catalogo. Dal lug 2026 escono
    TUTTI i guadagnati (bacheca stile Vinted, deciso con Andrea);
    l'ordine e' quello del catalogo, che mette i fiducia per primi —
    quando il frontend tronca a «+N», a sparire sono i badge di
    percorso, mai quelli di affidabilita'."""
    for r in righe:
        presi = set((r.pop("venditore_distintivi", "") or "").split(","))
        r["venditore_distintivi"] = [
            dict(id=d["id"], emoji=d["emoji"], nome=d["nome"],
                 descrizione=d["descrizione"])
            for d in DISTINTIVI if d["id"] in presi]
    return righe


# Paginazione della vetrina (lug 2026): con centinaia di annunci non
# si serve piu' tutto in un colpo. Il cursore e' un segnalibro
# "riparti da qui": '{creato}_{id}' dell'ultima riga vista. Meglio
# dell'OFFSET perche' un annuncio pubblicato mentre l'utente scorre
# non fa slittare le pagine (niente doppioni ne' buchi), e l'indice
# idx_annunci_* lo serve dritto senza contare righe da saltare.
LIMITE_PAGINA_MAX = 100   # nessun client onesto chiede di piu'
TETTO_LEGACY = 500        # rete di sicurezza per chi chiama senza limit


# Gli ordinamenti della vetrina: chiave del keyset + verso. Il
# default sono i piu' recenti; per prezzo si ordina su prezzo_sats,
# che per i listini EUR e' l'equivalente al cambio di PUBBLICAZIONE
# (compromesso dichiarato: il drift del cambio puo' spostare di
# qualche posizione un annuncio in euro, mai di molto).
ORDINAMENTI = {
    "":           ("creato",      "DESC", "<"),
    "prezzo_su":  ("prezzo_sats", "ASC",  ">"),
    "prezzo_giu": ("prezzo_sats", "DESC", "<"),
    # «In offerta»: le lampo che scadono prima in testa (l'urgenza e'
    # la notizia). Implica il filtro solo-lampo: senza, gli annunci a
    # scadenza 0 affollerebbero la testa della lista.
    "lampo":      ("lampo_scadenza", "ASC", ">"),
}


def pagina_annunci(con, campi, dove, par, limit, cursore, ordina=""):
    """Una pagina di annunci nell'ordine chiesto (default: nuovi
    prima). Chiede una riga in piu' del limite: se arriva, c'e'
    un'altra pagina e l'ultima riga tenuta diventa il prossimo
    segnalibro '{chiave}_{id}'. Un cursore storto (o un ordinamento
    sconosciuto) vale come il default: mai un errore (fail-safe
    verso client vecchi o link rotti)."""
    chiave, verso, op = ORDINAMENTI.get(ordina, ORDINAMENTI[""])
    q = (f"SELECT {campi} FROM annunci a "
         f"JOIN utenti u ON u.tg_id = a.venditore_id WHERE {dove}")
    if cursore:
        try:
            c, i = cursore.split("_")
            par = par + [int(c), int(i)]
            q += f" AND (a.{chiave}, a.id) {op} (?, ?)"
        except (ValueError, AttributeError):
            pass
    q += f" ORDER BY a.{chiave} {verso}, a.id {verso} LIMIT ?"
    righe = [dict(r) for r in con.execute(q, par + [limit + 1])]
    prossimo = None
    if len(righe) > limit:
        righe = righe[:limit]
        prossimo = f"{righe[-1][chiave]}_{righe[-1]['id']}"
    return righe, prossimo


# --------------------- CONTATORE PIONIERI ---------------------------
# Quante persone sono entrate nel mercatino: il numero che la vetrina
# mostra sotto il conteggio degli oggetti. In fase di rodaggio si
# chiamano «pionieri» — suona come un club, e lo sono. Cache breve: il
# numero cresce piano e la prima pagina della vetrina si chiede di
# continuo (categorie, filtri, ogni riapertura dell'app).
_pionieri_cache = {"quanti": 0, "quando": 0.0}
CACHE_PIONIERI = 60          # secondi


def conta_pionieri(con) -> int:
    # (il campanello che avvisa i moderatori di ogni nuovo iscritto sta
    #  piu' sotto, in compagnia del drenatore dei post automatici)
    adesso = time.time()
    if adesso - _pionieri_cache["quando"] < CACHE_PIONIERI:
        return _pionieri_cache["quanti"]
    quanti = con.execute("SELECT COUNT(*) AS n FROM utenti").fetchone()["n"]
    _pionieri_cache.update(quanti=quanti, quando=adesso)
    return quanti


@app.get("/api/banner-test")
def banner_test():
    """Il cartello «Barattolo e' in fase di test» che la Mini App mostra
    all'apertura. PUBBLICA come /api/listings: lo deve vedere anche chi
    guarda la vetrina da anonimo, senza Telegram. Interruttore spento o
    testo vuoto = {"attivo": False} e il frontend non disegna nulla."""
    testo = (BANNER_TEST_TESTO or "").strip()
    if not BANNER_TEST or not testo:
        return {"attivo": False}
    return {"attivo": True, "testo": testo,
            "link": (BANNER_TEST_LINK or "").strip()}


@app.get("/api/listings")
async def lista_annunci(cat: str = "", q: str = "", limit: int = 0,
                        cursore: str = "", ordina: str = "",
                        prezzo_min: float = 0, prezzo_max: float = 0,
                        valuta_filtro: str = "sats",
                        solo_spedizione: int = 0, solo_lampo: int = 0,
                        x_tg_init_data: str = Header(""),
                        barattolo_sessione: str = Cookie("")):
    user = utente_se_autenticato(x_tg_init_data, barattolo_sessione)
    # venditore_id serve alla Mini App per "questo annuncio e' tuo"
    campi = CAMPI_VETRINA + (", a.venditore_id" if user else "")
    dove = "a.stato='attivo'"
    par = []
    if cat and cat != "Tutto":
        dove += " AND a.categoria=?"
        par.append(cat)
    if solo_spedizione:
        # Il filtro promette un costo di spedizione DICHIARATO: gli
        # annunci storici ('') restano fuori finche' il venditore non
        # si dichiara con una modifica.
        dove += " AND a.consegna IN ('spedizione','entrambe')"
    if solo_lampo or ordina == "lampo":
        # Solo le offerte lampo VIVE: la scadenza si giudica adesso,
        # senza aspettare la scopa dell'orologio. L'ordinamento
        # «lampo» implica il filtro (vedi ORDINAMENTI).
        dove += " AND a.lampo_percento>0 AND a.lampo_scadenza>?"
        par.append(int(time.time()))
    if q.strip():
        # Ricerca semplice per la vetrina anonima (l'AI resta riservata
        # agli autenticati): LIKE su titolo, descrizione e zona.
        dove += " AND (a.titolo LIKE ? OR a.descrizione LIKE ? OR a.zona LIKE ?)"
        par += [f"%{q.strip()}%"] * 3
    # Filtro prezzo min/max: chi guarda in euro scrive euro, e la
    # conversione la fa il server col cambio corrente (la stessa
    # fonte del pagamento). Il confronto e' sempre su prezzo_sats:
    # per i listini EUR e' l'equivalente al cambio di pubblicazione.
    if (prezzo_min > 0 or prezzo_max > 0) and valuta_filtro == "eur":
        cambio = await cambio_btc_eur()
        if cambio <= 0:
            raise HTTPException(503, "Il cambio euro non è disponibile in "
                                     "questo momento: riprova tra qualche "
                                     "minuto")
        if prezzo_min > 0:
            prezzo_min = round(prezzo_min / cambio * 100_000_000)
        if prezzo_max > 0:
            prezzo_max = round(prezzo_max / cambio * 100_000_000)
    if prezzo_min > 0:
        dove += " AND a.prezzo_sats >= ?"
        par.append(int(prezzo_min))
    if prezzo_max > 0:
        dove += " AND a.prezzo_sats <= ?"
        par.append(int(prezzo_max))
    con = db()
    if not limit:
        # Client senza paginazione (JS vecchio in cache): l'array puro
        # di sempre, col tetto di sicurezza. Sotto i 500 annunci la
        # risposta e' IDENTICA a prima.
        righe = [dict(r) for r in con.execute(
            f"SELECT {campi} FROM annunci a "
            "JOIN utenti u ON u.tg_id = a.venditore_id "
            f"WHERE {dove} ORDER BY a.creato DESC, a.id DESC LIMIT ?",
            par + [TETTO_LEGACY])]
        con.close()
        return espandi_distintivi_vetrina(righe)
    limit = min(limit, LIMITE_PAGINA_MAX)
    righe, prossimo = pagina_annunci(con, campi, dove, par, limit, cursore,
                                     ordina)
    risposta = {"annunci": espandi_distintivi_vetrina(righe),
                "cursore": prossimo}
    if not cursore:
        # Solo in prima pagina: il totale della vista corrente (per
        # l'etichetta "N oggetti") e i conteggi GLOBALI per categoria
        # (le pillole devono dire la verita' anche a pagine parziali).
        risposta["totale"] = con.execute(
            f"SELECT COUNT(*) AS n FROM annunci a WHERE {dove}",
            par).fetchone()["n"]
        risposta["conteggi"] = {
            r["categoria"]: r["n"] for r in con.execute(
                "SELECT categoria, COUNT(*) AS n FROM annunci "
                "WHERE stato='attivo' GROUP BY categoria")}
        # I pionieri viaggiano insieme (niente giro di rete in piu');
        # a interruttore spento la chiave non c'e' e il frontend non
        # disegna la riga.
        if CONTATORE_UTENTI:
            risposta["pionieri"] = conta_pionieri(con)
        # La percentuale della protezione acquisti: cosi' la stima del
        # conto nel client non hardcoda mai la cifra (oggi 0).
        risposta["protezione_percento"] = PROTEZIONE_PERCENTO
        # La soglia minima delle offerte, per l'hint del foglio
        # (stesso patto: mai cifre hardcodate nel client).
        risposta["offerta_minima_percento"] = OFFERTA_MINIMA_PERCENTO
    con.close()
    return risposta


# La finestra dello scudo anti-doppione: stesso venditore, stesso
# titolo e stesso prezzo entro questi secondi = quasi certamente un
# retry (doppio tocco sul bottone, rete che riprova), non un annuncio
# nuovo. Chi ha davvero due oggetti identici aspetta mezzo minuto.
FINESTRA_ANTIDOPPIONE = 30

@app.post("/api/listings")
async def pubblica(req: Request, x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    valuta, prezzo_sats, prezzo_eur = await prezzo_da_payload(d)
    # Qui e non piu' in basso: consegna_da_payload puo' attendere il
    # cambio, e tra lo scudo anti-doppione e l'INSERT non deve esserci
    # nessun await (il patto del server mono-processo).
    consegna, sped_sats, sped_eur, taglia = await consegna_da_payload(d, valuta)

    # --- Moderazione, strato 1: filtro parole (gratis, istantaneo) ---
    categoria = controlla_vietato(d["titolo"], d.get("descrizione", ""))
    if categoria:
        await notifica_admin(
            f"🚫 <b>Annuncio bloccato dal filtro</b> ({categoria})\n"
            f"«{d['titolo'][:80]}» — {user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)

    # --- Strato 2: parere dell'AI (solo se la chiave e' configurata) ---
    motivo = await moderazione_ai(d["titolo"], d.get("descrizione", ""))
    if motivo:
        await notifica_admin(
            f"🚫 <b>Annuncio bloccato dall'AI</b> ({motivo})\n"
            f"«{d['titolo'][:80]}» — {user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)

    con = db()
    # --- Scudo anti-doppione: se lo stesso venditore ha gia' un
    # annuncio ATTIVO identico (titolo+prezzo) nato da pochi secondi,
    # questo submit e' un retry — si risponde con l'annuncio gia' nato
    # invece di crearne un gemello (idempotente: per il client e'
    # indistinguibile). Nessun await tra controllo e INSERT: nel
    # server mono-processo il blocco resta atomico. ---
    gemello = con.execute(
        "SELECT id FROM annunci WHERE venditore_id=? AND titolo=? "
        "AND prezzo_sats=? AND stato='attivo' AND creato>=? "
        "ORDER BY id DESC LIMIT 1",
        (user["id"], d["titolo"], prezzo_sats,
         int(time.time()) - FINESTRA_ANTIDOPPIONE)).fetchone()
    if gemello:
        con.close()
        return {"ok": True, "id": gemello["id"]}
    lat, lon = coordinate_da_zona(d.get("zona", ""))
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,valuta,prezzo_eur,lat,lon,"
        "consegna,spedizione_sats,spedizione_eur,taglia_pacco,creato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (user["id"], d["titolo"], d.get("descrizione", ""), categoria_valida(d.get("categoria")),
         prezzo_sats, d.get("zona", ""), valuta, prezzo_eur,
         lat, lon, consegna, sped_sats, sped_eur, taglia, int(time.time())))
    annuncio_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.commit()
    con.close()
    # Le foto in un thread: convertire una HEIC da 15MB costa secondi
    # di CPU e non deve congelare il server (che e' mono-processo).
    # Il commit e' gia' fatto: niente lock del database nel frattempo.
    nomi = await asyncio.to_thread(salva_foto, annuncio_id, d.get("foto"))
    if nomi:
        con = db()
        con.execute("UPDATE annunci SET foto=? WHERE id=?",
                    (json.dumps(nomi), annuncio_id))
        con.commit()
        con.close()
    # --- Strato 3: i moderatori vedono tutto cio' che entra in vetrina ---
    await notifica_admin(
        f"🆕 <b>Nuovo annuncio #{annuncio_id}</b>\n"
        f"«{d['titolo'][:80]}» — {testo_prezzo(valuta, prezzo_sats, prezzo_eur)}\n"
        f"Venditore: {user['first_name']} (id {user['id']})")
    # E parte anche verso la piazza Nostr, in sottofondo: se i relay
    # tacciono, chi pubblica non se ne accorge nemmeno.
    asyncio.create_task(annuncio_su_nostr(annuncio_id, "active"))
    # I canali di Barattolo lo annunceranno da soli (coda anti-spam:
    # il drenatore decide tra post singolo e aggregato).
    accoda_promo(annuncio_id)
    # ...e chi ha un avviso di ricerca che matcha ricevera' il suo
    # «e' arrivato» (stessa coda-e-finestra, notifiche aggregate).
    accoda_match(annuncio_id)
    await premia_distintivi(user["id"])   # bottega avviata?
    return {"ok": True, "id": annuncio_id}


@app.post("/api/foto/anteprima")
async def anteprima_foto(req: Request, x_tg_init_data: str = Header(""),
                                       barattolo_sessione: str = Cookie("")):
    """Conversione STATELESS per l'anteprima: il browser non sa
    mostrare le HEIC, quindi le manda qui appena scelte e riceve
    indietro il JPEG — lo stesso identico che poi verra' salvato
    alla pubblicazione, che a quel punto viaggia gia' leggero.
    Non scrive NULLA, ne' su disco ne' nel database: prima della
    pubblicazione non deve esistere niente di definitivo."""
    verifica_utente(x_tg_init_data, barattolo_sessione)
    if not ImmaginePillow:
        raise HTTPException(503, "Conversione non disponibile sul server")
    d = await leggi_json(req)
    m = re.match(r"data:image/(jpeg|jpg|png|webp|heic|heif);base64,(.+)",
                 d.get("foto") or "", re.S)
    if not m:
        raise HTTPException(400, "Formato non riconosciuto")
    if m.group(1) in ("heic", "heif") and not pillow_heif:
        raise HTTPException(503, "Conversione HEIC non disponibile sul server")
    try:
        raw = base64.b64decode(m.group(2))
    except Exception:
        raise HTTPException(400, "Foto illeggibile")
    if len(raw) > 15_000_000:
        raise HTTPException(400, "Foto troppo grande (max 15MB)")
    jpeg = await asyncio.to_thread(converti_in_jpeg, raw)
    if not jpeg:
        raise HTTPException(400, "Non riesco a leggere questa foto")
    return {"foto": "data:image/jpeg;base64,"
                    + base64.b64encode(jpeg).decode()}


# I campi degli annunci "di proprieta'" (miei): tutto l'annuncio, non
# la whitelist di vetrina — il proprietario vede casa sua per intero.
CAMPI_MIEI = (
    "a.*, u.nome AS venditore, u.username AS venditore_username, "
    "u.npub AS venditore_npub, "
    "u.npub_verificata AS venditore_npub_verificata, "
    "u.negozio AS venditore_negozio, "
    "(CASE WHEN u.avatar_scelta='nessuna' THEN '' ELSE u.avatar END) "
    "AS venditore_avatar, "
    "(SELECT GROUP_CONCAT(b.badge_id) FROM badge_utente b "
    " WHERE b.tg_id=a.venditore_id) AS venditore_distintivi, "
    "u.rating, u.vendite_ok")


@app.get("/api/listings/miei")
def miei_annunci(limit: int = 0, cursore: str = "",
                 x_tg_init_data: str = Header(""),
                 barattolo_sessione: str = Cookie("")):
    """Gli annunci attivi dell'utente che chiede (per gestirli).
    Con limit risponde a pagine come la vetrina; senza, l'array di
    sempre (tetto di sicurezza per i client vecchi)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    dove = "a.venditore_id=? AND a.stato='attivo'"
    con = db()
    if limit:
        righe, prossimo = pagina_annunci(
            con, CAMPI_MIEI, dove, [user["id"]],
            min(limit, LIMITE_PAGINA_MAX), cursore)
        con.close()
        return {"annunci": espandi_distintivi_vetrina(righe),
                "cursore": prossimo}
    righe = [dict(r) for r in con.execute(
        f"SELECT {CAMPI_MIEI} FROM annunci a "
        "JOIN utenti u ON u.tg_id=a.venditore_id "
        f"WHERE {dove} ORDER BY a.creato DESC, a.id DESC LIMIT ?",
        (user["id"], TETTO_LEGACY))]
    con.close()
    return espandi_distintivi_vetrina(righe)


# ATTENZIONE all'ordine di registrazione: questa rotta col parametro
# nel percorso DEVE stare dopo /api/listings/miei, altrimenti "miei"
# verrebbe letto come id. Serve al link condiviso /annuncio/{id}:
# con la vetrina a pagine l'annuncio puo' non essere tra i caricati.
@app.get("/api/listings/{annuncio_id}")
def un_annuncio(annuncio_id: int, x_tg_init_data: str = Header(""),
                barattolo_sessione: str = Cookie("")):
    user = utente_se_autenticato(x_tg_init_data, barattolo_sessione)
    campi = CAMPI_VETRINA + (", a.venditore_id" if user else "")
    con = db()
    r = con.execute(f"SELECT {campi} FROM annunci a "
                    "JOIN utenti u ON u.tg_id = a.venditore_id "
                    "WHERE a.id=? AND a.stato='attivo'",
                    (annuncio_id,)).fetchone()
    con.close()
    if not r:
        raise HTTPException(404, "Annuncio non trovato")
    return espandi_distintivi_vetrina([dict(r)])[0]


# ---- Preferiti: «nel tuo barattolo» 🫙 -------------------------------
# Un tocco sul barattolino mette da parte l'annuncio, un altro lo
# toglie. Il toggle vive sul server: lo stesso barattolo da ogni
# dispositivo. Privato per natura: nessun conteggio pubblico, il
# venditore non vede chi ne' quanti (v1).
MAX_PREFERITI = 20   # il barattolo e' piccolo apposta: contano solo gli attivi

def _conta_barattolo(con, tg_id):
    """Quanti annunci ATTIVI nel barattolo: i venduti/rimossi non
    occupano posto (comprare qualcosa che c'e' dentro libera spazio)."""
    return con.execute(
        "SELECT COUNT(*) FROM preferiti p "
        "JOIN annunci a ON a.id = p.annuncio_id AND a.stato='attivo' "
        "WHERE p.tg_id=?", (tg_id,)).fetchone()[0]

@app.post("/api/listings/{annuncio_id}/preferito")
async def toggle_preferito(annuncio_id: int, x_tg_init_data: str = Header(""),
                           barattolo_sessione: str = Cookie("")):
    # Async dal lug 2026 (offerta lampo): accoda_colpo avvia il suo
    # drenatore con create_task, che vuole il loop — il precedente e'
    # /api/me, diventato async per l'avatar. Le query restano un lampo,
    # e senza await tra COUNT e INSERT il blocco e' ancora atomico.
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    # Prima si prova a togliere: cosi' il barattolo si svuota anche
    # se nel frattempo l'annuncio e' sparito del tutto (e anche da pieno).
    tolto = con.execute(
        "DELETE FROM preferiti WHERE tg_id=? AND annuncio_id=?",
        (user["id"], annuncio_id)).rowcount
    salvato_attivo = False
    if not tolto:
        a = con.execute("SELECT id, venditore_id, stato FROM annunci "
                        "WHERE id=?", (annuncio_id,)).fetchone()
        if not a:
            con.close()
            raise HTTPException(404, "Annuncio non trovato")
        # Limite: niente await tra COUNT e INSERT, nel server
        # mono-processo il blocco e' atomico (il patto anti-doppione).
        if _conta_barattolo(con, user["id"]) >= MAX_PREFERITI:
            con.close()
            raise HTTPException(400, "Il barattolo è pieno! Svuotalo un po' "
                                     "o compra qualcosa che c'è dentro 🫙")
        con.execute("INSERT INTO preferiti(tg_id, annuncio_id, creato) "
                    "VALUES(?,?,?)",
                    (user["id"], annuncio_id, int(time.time())))
        # L'avviso «ha fatto colpo» parte solo per i salvataggi veri:
        # annuncio attivo e MAI il proprio (il venditore che si salva
        # da solo non si applaude da solo).
        salvato_attivo = (a["stato"] == "attivo"
                          and a["venditore_id"] != user["id"])
    con.commit()
    if salvato_attivo:
        accoda_colpo(annuncio_id)   # dopo il commit, fail-open
    # Il conteggio fresco viaggia nella risposta: il frontend aggiorna
    # il livello di riempimento col numero del server, non con una stima.
    conteggio = _conta_barattolo(con, user["id"])
    con.close()
    return {"ok": True, "salvato": not tolto, "conteggio": conteggio}


@app.get("/api/me/preferiti")
def miei_preferiti(x_tg_init_data: str = Header(""),
                   barattolo_sessione: str = Cookie("")):
    """Il contenuto del barattolo, dal salvato piu' di recente.
    Escono anche i non piu' attivi (venduti/rimossi), con lo stato:
    il cassetto li mostra onesti come «non piu' disponibili» —
    sparire in silenzio sarebbe peggio. Tetto 100: e' un barattolo,
    non un magazzino."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    righe = [dict(r) for r in con.execute(
        f"SELECT {CAMPI_VETRINA}, a.stato, a.venditore_id "
        "FROM preferiti p "
        "JOIN annunci a ON a.id = p.annuncio_id "
        "JOIN utenti u ON u.tg_id = a.venditore_id "
        "WHERE p.tg_id=? ORDER BY p.creato DESC LIMIT 100",
        (user["id"],))]
    con.close()
    return espandi_distintivi_vetrina(righe)


@app.get("/api/negozio/{chi}")
def negozio(chi: str, limit: int = 0, cursore: str = "",
            x_tg_init_data: str = Header(""),
            barattolo_sessione: str = Cookie("")):
    """La pagina-negozio di un venditore: profilo pubblico + i suoi
    annunci attivi. Si arriva con lo username Telegram (se ce l'ha) o
    col codice pubblico del negozio: mai col tg_id, che agli anonimi
    resta invisibile come in tutta la vetrina. Con limit gli annunci
    arrivano a pagine (chiavi cursore/totale IN PIU' nella risposta:
    i client vecchi le ignorano e vivono felici)."""
    user = utente_se_autenticato(x_tg_init_data, barattolo_sessione)
    con = db()
    campi_profilo = ("SELECT tg_id, nome, username, npub, npub_verificata, "
                     "rating, n_feedback, vendite_ok, negozio, "
                     "(CASE WHEN avatar_scelta='nessuna' THEN '' ELSE avatar "
                     "END) AS avatar FROM utenti ")
    v = con.execute(campi_profilo + "WHERE username=? COLLATE NOCASE "
                    "AND username!='' LIMIT 1", (chi,)).fetchone()
    if not v:
        v = con.execute(campi_profilo + "WHERE negozio=? LIMIT 1",
                        (chi,)).fetchone()
    if not v:
        con.close()
        raise HTTPException(404, "Negozio non trovato")
    # venditore_id in piu' solo agli autenticati ("questo annuncio e' tuo")
    campi = CAMPI_VETRINA + (", a.venditore_id" if user else "")
    dove = "a.venditore_id=? AND a.stato='attivo'"
    prossimo, totale = None, None
    if limit:
        righe, prossimo = pagina_annunci(
            con, campi, dove, [v["tg_id"]],
            min(limit, LIMITE_PAGINA_MAX), cursore)
        if not cursore:
            totale = con.execute(
                f"SELECT COUNT(*) AS n FROM annunci a WHERE {dove}",
                (v["tg_id"],)).fetchone()["n"]
    else:
        righe = [dict(r) for r in con.execute(
            f"SELECT {campi} FROM annunci a "
            "JOIN utenti u ON u.tg_id=a.venditore_id "
            f"WHERE {dove} ORDER BY a.creato DESC, a.id DESC LIMIT ?",
            (v["tg_id"], TETTO_LEGACY))]
    annunci = espandi_distintivi_vetrina(righe)
    # Gli ultimi feedback ricevuti: stelle + commento + data + ruolo di
    # chi scrive («acquirente»/«venditore»), MAI il nome — su una pagina
    # pubblica rivelerebbe gli acquisti di chi non ha scelto di apparire.
    # f.id e' un numero opaco: serve solo al bottone rimuovi dell'admin.
    feedback = [dict(r) for r in con.execute(
        "SELECT f.id, f.voto, f.commento, f.creato, "
        "CASE WHEN o.id IS NULL THEN 'utente' "
        "WHEN f.da_tg_id=o.compratore_id THEN 'acquirente' "
        "ELSE 'venditore' END AS ruolo "
        "FROM feedback f LEFT JOIN ordini o ON o.id=f.ordine_id "
        "WHERE f.per_tg_id=? ORDER BY f.creato DESC LIMIT 10",
        (v["tg_id"],))]
    # Sul profilo pubblico TUTTI i distintivi guadagnati (lug 2026,
    # bacheca stile Vinted): sono aggregati senza segreti, e il
    # foglietto del negozio li racconta uno a uno. L'ordine del
    # catalogo mette i fiducia per primi.
    presi = {r["badge_id"] for r in con.execute(
        "SELECT badge_id FROM badge_utente WHERE tg_id=?", (v["tg_id"],))}
    con.close()
    venditore = dict(v)
    venditore["distintivi"] = [
        dict(id=d["id"], emoji=d["emoji"], nome=d["nome"],
             descrizione=d["descrizione"])
        for d in DISTINTIVI if d["id"] in presi]
    del venditore["tg_id"]         # il profilo che esce e' solo roba pubblica
    risposta = {"venditore": venditore, "annunci": annunci,
                "feedback": feedback}
    if limit:
        risposta["cursore"] = prossimo
        if totale is not None:
            risposta["totale"] = totale
    return risposta


@app.post("/api/listings/{annuncio_id}/rimuovi")
async def rimuovi_annuncio(annuncio_id: int, x_tg_init_data: str = Header(""),
                                             barattolo_sessione: str = Cookie("")):
    """Cancellazione 'morbida': l'annuncio sparisce dalla vetrina ma
    resta nel database (cosi' gli ordini passati non si rompono e le
    dispute restano ricostruibili). Regole:
    - solo il proprietario puo' rimuovere
    - se c'e' un affare in corso (sats in escrow), prima si chiude quello
    - gli ordini creati ma mai pagati vengono annullati"""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND venditore_id=? "
                    "AND stato='attivo'", (annuncio_id, user["id"])).fetchone()
    if not a:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    in_corso = con.execute(
        "SELECT COUNT(*) AS n FROM ordini WHERE annuncio_id=? AND stato IN "
        "('locked','shipped','confirmed','dispute')",
        (annuncio_id,)).fetchone()["n"]
    if in_corso:
        con.close()
        raise HTTPException(400, "C'è un affare in corso su questo annuncio: "
                                 "va concluso prima di poterlo eliminare")
    con.execute("UPDATE annunci SET stato='rimosso' WHERE id=?", (annuncio_id,))
    con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                "WHERE annuncio_id=? AND stato='creato'",
                (int(time.time()), annuncio_id))
    con.commit()
    con.close()
    # Se era in piazza su Nostr, si chiede ai relay di toglierlo
    asyncio.create_task(ritira_da_nostr(annuncio_id))
    # E anche i post automatici dei canali si ritirano da soli
    asyncio.create_task(promo_rimuovi(annuncio_id))
    return {"ok": True}


@app.post("/api/listings/{annuncio_id}/modifica")
async def modifica_annuncio(annuncio_id: int, req: Request,
                            x_tg_init_data: str = Header(""),
                            barattolo_sessione: str = Cookie("")):
    """Il venditore ritocca un suo annuncio attivo. Regole:
    - solo il proprietario, solo su annunci attivi
    - mai con ordini in corso: chi ha pagato (o sta pagando) deve
      trovare l'annuncio cosi' com'era, non uno diverso sotto i piedi
    - la modifica ripassa da TUTTI gli strati di moderazione, come
      una pubblicazione nuova
    - foto: se ne arrivano di nuove sostituiscono le vecchie in blocco,
      se il campo manca restano quelle attuali"""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    valuta, prezzo_sats, prezzo_eur = await prezzo_da_payload(d)
    consegna, sped_sats, sped_eur, taglia = await consegna_da_payload(d, valuta)
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND venditore_id=? "
                    "AND stato='attivo'", (annuncio_id, user["id"])).fetchone()
    if not a:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    if a["contatto_nostr"]:
        con.close()
        raise HTTPException(400, "Questo annuncio è importato da Nostr: "
                                 "modificalo dal tuo client Nostr, qui si "
                                 "aggiorna da solo entro un'ora")
    in_corso = con.execute(
        "SELECT COUNT(*) AS n FROM ordini WHERE annuncio_id=? AND stato "
        "NOT IN ('released','refunded','annullato')",
        (annuncio_id,)).fetchone()["n"]
    con.close()
    if in_corso:
        raise HTTPException(400, "C'è un affare in corso su questo annuncio: "
                                 "potrai modificarlo quando sarà concluso "
                                 "(chi compra deve trovare l'annuncio così "
                                 "com'era quando ha deciso di pagare)")

    # --- Stessa moderazione di una pubblicazione nuova ---
    categoria = controlla_vietato(d["titolo"], d.get("descrizione", ""))
    if categoria:
        await notifica_admin(
            f"🚫 <b>Modifica bloccata dal filtro</b> ({categoria})\n"
            f"Annuncio #{annuncio_id} «{d['titolo'][:80]}» — "
            f"{user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)
    motivo = await moderazione_ai(d["titolo"], d.get("descrizione", ""))
    if motivo:
        await notifica_admin(
            f"🚫 <b>Modifica bloccata dall'AI</b> ({motivo})\n"
            f"Annuncio #{annuncio_id} «{d['titolo'][:80]}» — "
            f"{user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)

    con = db()
    # valuta e prezzo_eur si scrivono SEMPRE entrambe: un annuncio che
    # torna in sats deve azzerare l'euro, o resterebbero residui.
    # Stesso patto per i campi di consegna (gia' normalizzati sopra).
    # Le coordinate seguono la zona: se cambia, cambiano con lei.
    lat, lon = coordinate_da_zona(d.get("zona", ""))
    con.execute(
        "UPDATE annunci SET titolo=?, descrizione=?, categoria=?, "
        "prezzo_sats=?, zona=?, valuta=?, prezzo_eur=?, lat=?, lon=?, "
        "consegna=?, spedizione_sats=?, spedizione_eur=?, taglia_pacco=? "
        "WHERE id=?",
        (d["titolo"], d.get("descrizione", ""), categoria_valida(d.get("categoria")),
         prezzo_sats, d.get("zona", ""), valuta, prezzo_eur,
         lat, lon, consegna, sped_sats, sped_eur, taglia, annuncio_id))
    # Il prezzo cambiato fa decadere le trattative APERTE: erano una
    # percentuale di un prezzo che non esiste piu'. Le offerte gia'
    # ACCETTATE sopravvivono — l'accordo e' stretto.
    decadute_prezzo = []
    if (valuta != a["valuta"] or prezzo_sats != a["prezzo_sats"]
            or prezzo_eur != a["prezzo_eur"]):
        decadute_prezzo = con.execute(
            "SELECT compratore_id FROM offerte WHERE annuncio_id=? AND "
            "stato IN ('proposta','controproposta')",
            (annuncio_id,)).fetchall()
        if decadute_prezzo:
            con.execute("UPDATE offerte SET stato='decaduta', aggiornato=? "
                        "WHERE annuncio_id=? AND stato IN "
                        "('proposta','controproposta')",
                        (int(time.time()), annuncio_id))
    con.commit()
    con.close()
    # La notifica DOPO il commit, come sempre
    for riga in decadute_prezzo:
        await notifica(riga["compratore_id"],
            f"✏️ Il venditore ha ritoccato il prezzo di "
            f"«{d['titolo'][:60]}»: la tua offerta decade. Se ti "
            f"interessa ancora, riproponi sul prezzo nuovo."
            f"\n{URL_PUBBLICO}/annuncio/{annuncio_id}")
    if isinstance(d.get("foto"), list):
        # Nomi nuovi a ogni giro (il timestamp): cosi' il browser non
        # puo' mostrare per sbaglio la foto vecchia dalla sua cache.
        # E in un thread, come in pubblica(): la conversione HEIC non
        # deve congelare il server.
        nomi = await asyncio.to_thread(salva_foto, annuncio_id, d["foto"],
                                       versione=f"_{int(time.time())}")
        try:
            vecchie = json.loads(a["foto"]) if a["foto"] else []
        except Exception:
            vecchie = []
        for v in vecchie:
            if v.startswith("http") or v in nomi:
                continue
            # Con la foto piena se ne va anche la miniatura gemella
            for da_togliere in (v, v[:-4] + "_min.jpg"):
                try:
                    os.remove(os.path.join(FOTO_DIR, da_togliere))
                except OSError:
                    pass
        con = db()
        con.execute("UPDATE annunci SET foto=? WHERE id=?",
                    (json.dumps(nomi) if nomi else "", annuncio_id))
        con.commit()
        con.close()
    # --- Strato 3: i moderatori vedono anche cio' che cambia ---
    await notifica_admin(
        f"✏️ <b>Annuncio #{annuncio_id} modificato</b>\n"
        f"«{d['titolo'][:80]}» — {testo_prezzo(valuta, prezzo_sats, prezzo_eur)}\n"
        f"Venditore: {user['first_name']} (id {user['id']})")
    # Se era in piazza su Nostr, l'evento riparte aggiornato: il tag d
    # stabile fa si' che sostituisca il precedente da solo
    asyncio.create_task(annuncio_su_nostr(annuncio_id, "active",
                                          solo_aggiornamento=True))
    return {"ok": True, "id": annuncio_id}


# --- Modifica FIRMATA degli annunci importati da Nostr ---------------
# Il doppio cittadino con la chiave d'accesso Nostr E' l'autore degli
# eventi importati: puo' aggiornarli sui relay con la SUA firma. La
# firma pero' avviene SOLO nel suo browser (regola ferrea 2: la nsec
# non arriva mai qui — e l'evento firmato in transito e' pubblico per
# natura, finira' sui relay). Due fasi:
#   1) "prepara" valida e MODERA il contenuto (prima della firma: se
#      moderassimo dopo, un rifiuto sarebbe teatro — il client avrebbe
#      gia' pubblicato e l'import orario riporterebbe tutto dentro) e
#      restituisce l'evento NON firmato con un biglietto a scadenza;
#   2) il client firma, pubblica sui relay e riconsegna SOLO
#      {biglietto, pubkey, sig}: l'evento si RICOSTRUISCE dai dati del
#      biglietto e la firma si verifica su quello, cosi' un contenuto
#      diverso da cio' che la moderazione ha visto non puo' esistere.
# TTL 10 minuti (non 5: il giro auth_url del bunker puo' essere lento).
# Se i relay accettano ma la fase 2 non arriva, la copia locale resta
# indietro al massimo un'ora: per gli importati i relay SONO la fonte
# di verita' e l'import orario e' la riconciliazione.

BIGLIETTI_MODIFICA_NOSTR: dict[str, dict] = {}


def _relays_import() -> list:
    """La lista relay dell'import, che include il relay personale del
    venditore: e' li' che l'evento aggiornato deve arrivare, o il
    resto di Nostr continuerebbe a leggere la versione vecchia."""
    try:
        from importa_nostr import RELAYS
        return RELAYS
    except Exception:
        return RELAYS_VERIFICA


@app.post("/api/listings/{annuncio_id}/modifica-firmata/prepara")
async def modifica_firmata_prepara(annuncio_id: int, req: Request,
                                   x_tg_init_data: str = Header(""),
                                   barattolo_sessione: str = Cookie("")):
    """Fase 1: valida, modera e prepara l'evento NIP-99 da firmare."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    valuta, prezzo_sats, prezzo_eur = await prezzo_da_payload(d)
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND venditore_id=? "
                    "AND stato='attivo'", (annuncio_id, user["id"])).fetchone()
    if not a:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    if not a["contatto_nostr"]:
        con.close()
        raise HTTPException(400, "Questo annuncio non è importato da Nostr: "
                                 "usa la modifica normale")
    if not a["nostr_origine_d"]:
        con.close()
        raise HTTPException(400, "L'import non ha ancora registrato le "
                                 "coordinate Nostr di questo annuncio: "
                                 "riprova tra un'ora")
    in_corso = con.execute(
        "SELECT COUNT(*) AS n FROM ordini WHERE annuncio_id=? AND stato "
        "NOT IN ('released','refunded','annullato')",
        (annuncio_id,)).fetchone()["n"]
    u = con.execute("SELECT npub_accesso FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
    con.close()
    if in_corso:
        raise HTTPException(400, "C'è un affare in corso su questo annuncio: "
                                 "potrai modificarlo quando sarà concluso "
                                 "(chi compra deve trovare l'annuncio così "
                                 "com'era quando ha deciso di pagare)")
    # La chiave: sempre normalizzata in esadecimale su ENTRAMBI i lati
    # (contatto_nostr arriva dal config cosi' com'e', npub o hex).
    try:
        hex_evento = npub_to_hex(a["contatto_nostr"])
    except ValueError:
        raise HTTPException(400, "La chiave Nostr di questo annuncio non è "
                                 "leggibile: contatta un admin")
    npub_acc = (u["npub_accesso"] or "").strip() if u else ""
    try:
        hex_utente = npub_to_hex(npub_acc) if npub_acc else ""
    except ValueError:
        hex_utente = ""
    if not hex_utente or hex_utente != hex_evento:
        raise HTTPException(400, "Per modificare un annuncio importato serve "
                                 "l'accesso Nostr con la STESSA chiave che "
                                 "l'ha pubblicato: abilitalo dal Profilo "
                                 "(cassetto 🆔 Identità)")
    if ChiavePubblicaNostr is None:
        raise HTTPException(503, "Firma Nostr non disponibile: sul server "
                                 "manca il pacchetto coincurve")

    # --- Stessa moderazione di una pubblicazione nuova ---
    cat_vietata = controlla_vietato(d["titolo"], d.get("descrizione", ""))
    if cat_vietata:
        await notifica_admin(
            f"🚫 <b>Modifica firmata bloccata dal filtro</b> ({cat_vietata})\n"
            f"Annuncio #{annuncio_id} «{d['titolo'][:80]}» — "
            f"{user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)
    motivo = await moderazione_ai(d["titolo"], d.get("descrizione", ""))
    if motivo:
        await notifica_admin(
            f"🚫 <b>Modifica firmata bloccata dall'AI</b> ({motivo})\n"
            f"Annuncio #{annuncio_id} «{d['titolo'][:80]}» — "
            f"{user['first_name']} (id {user['id']})")
        raise HTTPException(400, MSG_RIFIUTO)

    categoria = categoria_valida(d.get("categoria"))
    evento = evento_annuncio_importato(
        a, d["titolo"], d.get("descrizione", ""), categoria,
        d.get("zona", ""), valuta, prezzo_sats, prezzo_eur,
        int(time.time()))
    adesso = time.time()
    for b in [b for b, v in BIGLIETTI_MODIFICA_NOSTR.items()
              if v["scade"] < adesso]:
        BIGLIETTI_MODIFICA_NOSTR.pop(b, None)
    while len(BIGLIETTI_MODIFICA_NOSTR) >= 1000:
        BIGLIETTI_MODIFICA_NOSTR.pop(next(iter(BIGLIETTI_MODIFICA_NOSTR)))
    biglietto = secrets.token_urlsafe(32)
    BIGLIETTI_MODIFICA_NOSTR[biglietto] = {
        "annuncio_id": annuncio_id, "tg_id": user["id"],
        "titolo": d["titolo"], "descrizione": d.get("descrizione", ""),
        "categoria": categoria, "zona": d.get("zona", ""),
        "valuta": valuta, "prezzo_sats": prezzo_sats,
        "prezzo_eur": prezzo_eur, "created_at": evento["created_at"],
        "tags": evento["tags"], "content": evento["content"],
        "scade": adesso + 600}
    # In collaudo anche il BROWSER deve simulare: senza questo flag
    # pubblicherebbe l'evento di prova sui relay veri (successo al
    # primo collaudo, mai piu': "si firma ma si stampa" vale ovunque).
    return {"biglietto": biglietto, "evento": evento,
            "relays": _relays_import(), "collaudo": MODALITA_COLLAUDO}


@app.post("/api/listings/{annuncio_id}/modifica-firmata")
async def modifica_firmata(annuncio_id: int, req: Request,
                           x_tg_init_data: str = Header(""),
                           barattolo_sessione: str = Cookie("")):
    """Fase 2: il client ha firmato e pubblicato sui relay; qui arriva
    {biglietto, pubkey, sig}, si verifica la firma sull'evento
    RICOSTRUITO dal biglietto e si allinea subito la copia locale."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    # Monouso: si brucia SUBITO, anche se il tentativo poi fallisce
    # (chi sbaglia riparte dalla fase 1) — pattern SFIDE_LOGIN.
    b = BIGLIETTI_MODIFICA_NOSTR.pop(str(d.get("biglietto") or ""), None)
    if (not b or b["scade"] < time.time()
            or b["annuncio_id"] != annuncio_id or b["tg_id"] != user["id"]):
        raise HTTPException(400, "La firma ha aspettato troppo: "
                                 "ricomincia la modifica")
    pubkey = str(d.get("pubkey") or "").lower()
    sig = str(d.get("sig") or "").lower()
    if not RE_HEX_64.fullmatch(pubkey) or not RE_HEX_128.fullmatch(sig):
        raise HTTPException(400, "Firma malformata")
    if ChiavePubblicaNostr is None:
        raise HTTPException(503, "Firma Nostr non disponibile: sul server "
                                 "manca il pacchetto coincurve")
    # Ri-guardie economiche (tra le due fasi puo' succedere di tutto:
    # un ordine che si apre, l'annuncio che si vende). La moderazione
    # invece NO: il contenuto e' congelato nel biglietto.
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND venditore_id=? "
                    "AND stato='attivo'", (annuncio_id, user["id"])).fetchone()
    if not a or not a["contatto_nostr"]:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    in_corso = con.execute(
        "SELECT COUNT(*) AS n FROM ordini WHERE annuncio_id=? AND stato "
        "NOT IN ('released','refunded','annullato')",
        (annuncio_id,)).fetchone()["n"]
    if in_corso:
        con.close()
        raise HTTPException(400, "Nel frattempo si è aperto un affare su "
                                 "questo annuncio: la modifica locale "
                                 "aspetta, i relay si allineano da soli")
    # L'autorizzazione VERA: la firma Schnorr della chiave che ha
    # pubblicato l'evento originale (riletta fresca dalla riga).
    try:
        if pubkey != npub_to_hex(a["contatto_nostr"]):
            raise ValueError
    except ValueError:
        con.close()
        raise HTTPException(400, "La firma non è della chiave che ha "
                                 "pubblicato questo annuncio")
    ev = evento_non_firmato(pubkey, 30402, b["tags"], b["content"],
                            b["created_at"])
    try:
        firma_buona = ChiavePubblicaNostr(bytes.fromhex(pubkey)).verify(
            bytes.fromhex(sig), bytes.fromhex(ev["id"]))
    except Exception:
        firma_buona = False
    if not firma_buona:
        con.close()
        raise HTTPException(400, "Firma non valida")
    # Copia locale allineata SUBITO dal payload gia' validato e
    # moderato in fase 1 (mai ri-parsare l'evento: sarebbe un giro
    # con perdita). Le foto non si toccano: v1, restano le sue.
    lat, lon = coordinate_da_zona(b["zona"])
    con.execute(
        "UPDATE annunci SET titolo=?, descrizione=?, categoria=?, "
        "prezzo_sats=?, zona=?, valuta=?, prezzo_eur=?, lat=?, lon=? "
        "WHERE id=?",
        (b["titolo"], b["descrizione"], b["categoria"], b["prezzo_sats"],
         b["zona"], b["valuta"], b["prezzo_eur"], lat, lon, annuncio_id))
    con.commit()
    con.close()
    # Backstop: l'evento firmato riparte anche da qui verso i relay
    # dell'import (fail-open, mai attese per l'utente). Il client lo
    # ha gia' pubblicato dal browser: doppia consegna innocua, i relay
    # deduplicano per id.
    ev["sig"] = sig
    asyncio.create_task(_spedisci_ai_relay(ev, _relays_import()))
    await notifica_admin(
        f"✏️🟣 <b>Annuncio importato #{annuncio_id} modificato</b> "
        f"(firmato dal venditore su Nostr)\n"
        f"«{b['titolo'][:80]}» — "
        f"{testo_prezzo(b['valuta'], b['prezzo_sats'], b['prezzo_eur'])}\n"
        f"Venditore: {user['first_name']} (id {user['id']})")
    return {"ok": True, "id": annuncio_id}


@app.post("/api/admin/listings/{annuncio_id}/rimuovi")
async def rimuovi_annuncio_admin(annuncio_id: int,
                                 x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    """SOLO ADMIN (moderazione, strato 3): rimuove un annuncio che
    viola le regole. Stessa cancellazione morbida del proprietario e
    stessa guardia sugli affari in corso: con sats in escrow prima si
    chiude l'ordine (dalla disputa, se serve), poi si rimuove."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if not e_admin(user["id"]):
        raise HTTPException(403, "Riservato ai moderatori")
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND stato='attivo'",
                    (annuncio_id,)).fetchone()
    if not a:
        con.close()
        raise HTTPException(400, "Annuncio non trovato o già rimosso")
    in_corso = con.execute(
        "SELECT COUNT(*) AS n FROM ordini WHERE annuncio_id=? AND stato IN "
        "('locked','shipped','confirmed','dispute')",
        (annuncio_id,)).fetchone()["n"]
    if in_corso:
        con.close()
        raise HTTPException(400, "C'è un affare in corso su questo annuncio: "
                                 "risolvi prima l'ordine (o la disputa), poi "
                                 "potrai rimuoverlo")
    con.execute("UPDATE annunci SET stato='rimosso' WHERE id=?", (annuncio_id,))
    con.execute("UPDATE ordini SET stato='annullato', aggiornato=? "
                "WHERE annuncio_id=? AND stato='creato'",
                (int(time.time()), annuncio_id))
    con.commit()
    con.close()
    # Se era in piazza su Nostr, si chiede ai relay di toglierlo
    asyncio.create_task(ritira_da_nostr(annuncio_id))
    # E anche i post automatici dei canali si ritirano da soli
    asyncio.create_task(promo_rimuovi(annuncio_id))
    await notifica(a["venditore_id"],
                   f"🚫 <b>Il tuo annuncio «{a['titolo'][:60]}» è stato "
                   f"rimosso</b> perché viola le regole del mercatino. "
                   f"Se pensi sia un errore, scrivi ai moderatori.")
    return {"ok": True}


@app.get("/api/admin/stats")
def statistiche_admin(x_tg_init_data: str = Header(""),
                      barattolo_sessione: str = Cookie("")):
    """SOLO ADMIN: i numeri del mercatino a colpo d'occhio."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if not e_admin(user["id"]):
        raise HTTPException(403, "Riservato ai moderatori")
    con = db()
    utenti = con.execute("SELECT COUNT(*) AS n FROM utenti").fetchone()["n"]
    annunci = con.execute("SELECT COUNT(*) AS n FROM annunci "
                          "WHERE stato='attivo'").fetchone()["n"]
    conclusi = con.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(prezzo_sats),0) AS volume "
        "FROM ordini WHERE stato IN ('released','refunded')").fetchone()
    lista = [dict(r) for r in con.execute(
        "SELECT u.tg_id, u.nome, u.username, u.registrato, "
        "  (SELECT COUNT(*) FROM annunci a WHERE a.venditore_id=u.tg_id "
        "     AND a.stato='attivo') AS annunci_attivi, "
        "  (SELECT COUNT(*) FROM ordini o WHERE o.stato IN "
        "     ('released','refunded') AND (o.venditore_id=u.tg_id "
        "     OR o.compratore_id=u.tg_id)) AS affari_conclusi "
        "FROM utenti u ORDER BY u.registrato DESC")]
    con.close()
    return {"utenti": utenti, "annunci_attivi": annunci,
            "affari_conclusi": conclusi["n"], "volume_sats": conclusi["volume"],
            "lista_utenti": lista}


# ---------------------- API: RICERCA AI -----------------------------

# Con centinaia di annunci il catalogo intero non entra piu' nel
# prompt: all'AI arriva una SHORTLIST — prima i match letterali sulle
# parole della richiesta, poi i piu' recenti a riempire. Compromesso
# dichiarato: un annuncio che combacia SOLO per sinonimo e non e' tra
# i piu' freschi puo' sfuggire. L'AI continua a fare la parte fine
# (sinonimi, prezzo, zona) dentro la rosa.
TETTO_CATALOGO_AI = 300


@app.get("/api/search")
def cerca(q: str, x_tg_init_data: str = Header(""),
                  barattolo_sessione: str = Cookie("")):
    """Ricerca in linguaggio naturale: l'AI legge la richiesta
    ("tastiera sotto i 100k vicino Milano") e seleziona gli annunci."""
    verifica_utente(x_tg_init_data, barattolo_sessione)
    base = ("SELECT a.*, u.nome AS venditore, u.username AS venditore_username, "
            "u.npub AS venditore_npub, "
            "u.npub_verificata AS venditore_npub_verificata, "
            "u.negozio AS venditore_negozio, "
            "(CASE WHEN u.avatar_scelta='nessuna' THEN '' ELSE u.avatar END) "
            "AS venditore_avatar, "
            "(SELECT GROUP_CONCAT(b.badge_id) FROM badge_utente b "
            " WHERE b.tg_id=a.venditore_id) AS venditore_distintivi, "
            "u.rating FROM annunci a "
            "JOIN utenti u ON u.tg_id=a.venditore_id WHERE a.stato='attivo'")
    con = db()
    # Le parole "sostanziose" della richiesta (>=3 lettere, max 6)
    parole = [p for p in re.findall(r"\w+", q.lower()) if len(p) >= 3][:6]
    annunci = []
    if parole:
        cond = " OR ".join("(a.titolo LIKE ? OR a.descrizione LIKE ? "
                           "OR a.categoria LIKE ? OR a.zona LIKE ?)"
                           for _ in parole)
        par = [f"%{p}%" for p in parole for _ in range(4)]
        annunci = [dict(r) for r in con.execute(
            base + f" AND ({cond}) ORDER BY a.creato DESC LIMIT ?",
            par + [TETTO_CATALOGO_AI])]
    if len(annunci) < TETTO_CATALOGO_AI:
        # Si riempie la rosa coi piu' freschi: l'AI vede sempre un
        # catalogo pieno e puo' pescare i sinonimi che il LIKE non sa.
        ids = tuple(a["id"] for a in annunci) or (0,)
        annunci += [dict(r) for r in con.execute(
            base + f" AND a.id NOT IN ({','.join('?' * len(ids))}) "
            "ORDER BY a.creato DESC LIMIT ?",
            list(ids) + [TETTO_CATALOGO_AI - len(annunci)])]
    annunci = espandi_distintivi_vetrina(annunci)
    con.close()
    if not annunci:
        return []

    catalogo = "\n".join(
        f"ID {a['id']}: {a['titolo']} | {a['categoria']} | "
        f"{a['prezzo_sats']} sats"
        + (f" ({a['prezzo_eur']:.2f} EUR)" if a["valuta"] == "eur" else "")
        + f" | {a['zona']} | {a['descrizione'][:120]}"
        for a in annunci)
    try:
        r = ai.messages.create(
            model=MODELLO_RICERCA, max_tokens=200,
            system=("Sei il motore di ricerca di un mercatino. Data la richiesta "
                    "dell'utente e il catalogo, rispondi SOLO con un array JSON "
                    "degli ID pertinenti, dal piu' rilevante. Capisci sinonimi "
                    "(bici=mtb=bicicletta) e vincoli di prezzo/zona. "
                    "Le categorie del catalogo sono: "
                    + ", ".join(CATEGORIE) + ". Se la richiesta indica una "
                    "categoria (es. 'giochi per bambini'), privilegiala. "
                    "Nessun risultato pertinente = []"),
            messages=[{"role": "user",
                       "content": f"RICHIESTA: {q}\n\nCATALOGO:\n{catalogo}"}])
        ids = json.loads("".join(b.text for b in r.content if b.type == "text")
                         .replace("```json", "").replace("```", "").strip())
        per_id = {a["id"]: a for a in annunci}
        return [per_id[i] for i in ids if i in per_id]
    except Exception as e:
        print(f"Ricerca AI fallita, uso filtro semplice: {e}")
        ql = q.lower()
        return [a for a in annunci if ql in (a["titolo"] + a["descrizione"]).lower()]


# ------------------------- API: OFFERTE -----------------------------
# La contrattazione sul prezzo (lug 2026, modello Vinted): proposta ->
# risposta -> acquisto alla cifra pattuita. NON e' una chat: e' una
# macchina a stati con al massimo UNA controproposta del venditore.
# L'annuncio non si blocca mai durante la trattativa: vince chi paga
# per primo, e le offerte rimaste vive decadono con garbo. L'accordo
# riguarda il SOLO articolo: spedizione e protezione si sommano sopra
# al momento dell'acquisto, come per ogni altro ordine.

STATI_OFFERTA_VIVI = ("proposta", "controproposta", "accettata")


def _importo_accordo(off) -> tuple[int, float]:
    """La cifra pattuita: la controproposta se c'e' (solo il compratore
    puo' accettarla, quindi se c'e' l'accordo e' quello), altrimenti la
    proposta. In (sats, eur): uno dei due e' sempre 0, come in colonna."""
    if off["contro_sats"] > 0 or off["contro_eur"] > 0:
        return off["contro_sats"], off["contro_eur"]
    return off["importo_sats"], off["importo_eur"]


def _cifra_offerta(valuta: str, sats: int, eur: float) -> str:
    """«80.000 sats» oppure «15.50 €»: la valuta del listino."""
    return f"{eur:.2f} €" if valuta == "eur" else f"{_fmt_sats(sats)} sats"


@app.post("/api/listings/{annuncio_id}/offerta")
async def fai_offerta(annuncio_id: int, req: Request,
                      x_tg_init_data: str = Header(""),
                      barattolo_sessione: str = Cookie("")):
    """Il compratore propone la sua cifra, nella valuta del listino.
    Qui il cambio non serve mai: offerta e listino si confrontano
    nella stessa valuta (la conversione, per i listini EUR, avviene
    solo alla creazione della invoice, come sempre)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND stato='attivo'",
                    (annuncio_id,)).fetchone()
    if not a:
        con.close()
        raise HTTPException(404, "Annuncio non disponibile")
    if a["venditore_id"] == user["id"]:
        con.close()
        raise HTTPException(400, "Non puoi fare un'offerta sul tuo "
                                 "stesso annuncio")
    # Gli importati da Nostr sono trattabili come tutti: il venditore
    # solo-Nostr riceve l'offerta via DM NIP-17 col link all'annuncio,
    # entra col login Nostr e risponde da qui.
    # La cifra, nella valuta del listino (EUR con la virgola tradotta)
    grezzo = str(d.get("importo", "")).strip()
    imp_sats, imp_eur = 0, 0.0
    if a["valuta"] == "eur":
        try:
            imp_eur = round(float(grezzo.replace(",", ".")), 2)
        except ValueError:
            imp_eur = 0.0
        importo, listino = imp_eur, a["prezzo_eur"]
    else:
        try:
            imp_sats = int(float(grezzo))
        except ValueError:
            imp_sats = 0
        importo, listino = imp_sats, a["prezzo_sats"]
    if importo <= 0:
        con.close()
        raise HTTPException(400, "Importo non valido")
    if importo >= listino:
        con.close()
        raise HTTPException(400, "La tua offerta è pari o superiore al "
                                 "prezzo dell'annuncio: puoi comprare "
                                 "direttamente 🙂")
    # Il paletto anti-offerte-insulto: sotto la soglia non si parte.
    # Sui sats il minimo si arrotonda per ECCESSO (mai un'offerta
    # ammessa sotto la percentuale promessa al venditore).
    if a["valuta"] == "eur":
        minimo = round(listino * OFFERTA_MINIMA_PERCENTO / 100, 2)
    else:
        minimo = (listino * OFFERTA_MINIMA_PERCENTO + 99) // 100
    if importo < minimo:
        con.close()
        raise HTTPException(400, "Le offerte per questo annuncio partono "
                                 f"da {_cifra_offerta(a['valuta'], minimo, minimo)}")
    # Le due guardie di conteggio: una offerta attiva alla volta, e un
    # numero chiuso di tentativi totali. Niente await tra i COUNT e
    # l'INSERT: nel server mono-processo il blocco e' atomico (il
    # patto anti-doppione di pubblica e del barattolo).
    attive = con.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE annuncio_id=? AND "
        "compratore_id=? AND stato IN ('proposta','controproposta',"
        "'accettata')", (annuncio_id, user["id"])).fetchone()["n"]
    if attive:
        con.close()
        raise HTTPException(400, "Hai già un'offerta in corso su questo "
                                 "annuncio: aspetta la risposta del "
                                 "venditore")
    totali = con.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE annuncio_id=? AND "
        "compratore_id=?", (annuncio_id, user["id"])).fetchone()["n"]
    if totali >= MAX_OFFERTE_ANNUNCIO:
        con.close()
        raise HTTPException(400, f"Hai già fatto {MAX_OFFERTE_ANNUNCIO} "
                                 "offerte su questo annuncio: è il "
                                 "momento del prezzo pieno 🙂")
    adesso = int(time.time())
    scadenza = adesso + ORE_RISPOSTA_OFFERTA * 3600
    con.execute(
        "INSERT INTO offerte(annuncio_id,compratore_id,venditore_id,"
        "valuta,importo_sats,importo_eur,stato,scadenza,creato,aggiornato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (annuncio_id, user["id"], a["venditore_id"], a["valuta"],
         imp_sats, imp_eur, "proposta", scadenza, adesso, adesso))
    con.commit()
    offerta_id = con.execute(
        "SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.close()
    # La notifica DOPO il commit, come sempre
    await notifica(a["venditore_id"],
        f"💰 <b>Hai ricevuto un'offerta!</b> Qualcuno ti offre "
        f"{_cifra_offerta(a['valuta'], imp_sats, imp_eur)} per "
        f"«{a['titolo'][:60]}» (listino "
        f"{_cifra_offerta(a['valuta'], a['prezzo_sats'], a['prezzo_eur'])}). "
        f"Rispondi dalla scheda Ordini: puoi accettare, rifiutare o fare "
        f"una controproposta. Senza risposta entro "
        f"{ORE_RISPOSTA_OFFERTA} ore l'offerta scade da sola."
        f"\n{URL_PUBBLICO}/annuncio/{annuncio_id}")
    return {"ok": True, "offerta_id": offerta_id, "scadenza": scadenza}


@app.get("/api/me/offerte")
def mie_offerte(x_tg_init_data: str = Header(""),
                barattolo_sessione: str = Cookie("")):
    """Le offerte in cui sono una delle parti, dalle piu' fresche.
    La busta porta anche le leve: il client non hardcoda mai le cifre."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    righe = con.execute(
        "SELECT o.*, a.titolo, a.foto, a.stato AS stato_annuncio, "
        "a.prezzo_sats AS listino_sats, a.prezzo_eur AS listino_eur, "
        "a.consegna, uc.nome AS compratore_nome, uv.nome AS venditore_nome "
        "FROM offerte o "
        "JOIN annunci a ON a.id = o.annuncio_id "
        "LEFT JOIN utenti uc ON uc.tg_id = o.compratore_id "
        "LEFT JOIN utenti uv ON uv.tg_id = o.venditore_id "
        "WHERE o.compratore_id=? OR o.venditore_id=? "
        "ORDER BY o.aggiornato DESC LIMIT 30",
        (user["id"], user["id"])).fetchall()
    con.close()
    return {"offerte": [dict(r) for r in righe],
            "minima_percento": OFFERTA_MINIMA_PERCENTO,
            "ore_risposta": ORE_RISPOSTA_OFFERTA,
            "ore_pagamento": ORE_PAGAMENTO_OFFERTA,
            "max_offerte": MAX_OFFERTE_ANNUNCIO}


@app.post("/api/offerte/{offerta_id}/rispondi")
async def rispondi_offerta(offerta_id: int, req: Request,
                           x_tg_init_data: str = Header(""),
                           barattolo_sessione: str = Cookie("")):
    """La mossa sull'offerta. Su una proposta muove il VENDITORE
    (accetta, rifiuta o fa la sua UNICA controproposta); su una
    controproposta muove il COMPRATORE (accetta o rifiuta, il
    ping-pong finisce qui). Accettare apre la finestra di pagamento —
    ma non riserva l'oggetto: l'annuncio resta in vetrina."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    azione = d.get("azione", "")
    con = db()
    off = con.execute(
        "SELECT o.*, a.stato AS stato_annuncio, a.titolo, "
        "a.prezzo_sats AS listino_sats, a.prezzo_eur AS listino_eur "
        "FROM offerte o JOIN annunci a ON a.id = o.annuncio_id "
        "WHERE o.id=?", (offerta_id,)).fetchone()
    if not off:
        con.close()
        raise HTTPException(404, "Offerta non trovata")
    adesso = int(time.time())
    # La scadenza si controlla anche qui, non solo nell'orologio: chi
    # risponde a un'offerta gia' morta merita un no onesto subito.
    if off["stato"] in STATI_OFFERTA_VIVI and 0 < off["scadenza"] < adesso:
        con.execute("UPDATE offerte SET stato='scaduta', aggiornato=? "
                    "WHERE id=?", (adesso, offerta_id))
        con.commit()
        con.close()
        raise HTTPException(400, "Questa offerta è scaduta")
    # Chi puo' fare cosa dipende dallo stato: il protocollo e' rigido
    # apposta (non e' una chat).
    if off["stato"] == "proposta":
        chi_muove, ammesse = off["venditore_id"], ("accetta", "rifiuta",
                                                   "contro")
    elif off["stato"] == "controproposta":
        chi_muove, ammesse = off["compratore_id"], ("accetta", "rifiuta")
    else:
        con.close()
        raise HTTPException(400, "Questa offerta è già chiusa")
    if user["id"] != chi_muove or azione not in ammesse:
        con.close()
        raise HTTPException(400, "Operazione non permessa")

    titolo = off["titolo"][:60]
    link = f"\n{URL_PUBBLICO}/annuncio/{off['annuncio_id']}"
    cifra_proposta = _cifra_offerta(off["valuta"], off["importo_sats"],
                                    off["importo_eur"])

    if azione == "accetta":
        # L'annuncio deve essere ancora in vetrina: su uno gia' venduto
        # o rimosso l'accordo non ha piu' oggetto.
        if off["stato_annuncio"] != "attivo":
            con.execute("UPDATE offerte SET stato='decaduta', aggiornato=? "
                        "WHERE id=?", (adesso, offerta_id))
            con.commit()
            con.close()
            raise HTTPException(400, "L'annuncio non è più disponibile")
        con.execute("UPDATE offerte SET stato='accettata', scadenza=?, "
                    "aggiornato=? WHERE id=?",
                    (adesso + ORE_PAGAMENTO_OFFERTA * 3600, adesso,
                     offerta_id))
        con.commit()
        con.close()
        if off["stato"] == "proposta":
            await notifica(off["compratore_id"],
                f"🎉 <b>Offerta accettata!</b> Puoi comprare «{titolo}» a "
                f"{cifra_proposta}: hai {ORE_PAGAMENTO_OFFERTA} ore per "
                f"pagare dalla scheda Ordini. I tuoi sats finiscono nel "
                f"deposito di garanzia, come sempre. Occhio: l'annuncio "
                f"resta in vetrina, se qualcuno paga il prezzo pieno prima "
                f"di te l'offerta decade.{link}")
        else:
            contro = _cifra_offerta(off["valuta"], off["contro_sats"],
                                    off["contro_eur"])
            await notifica(off["venditore_id"],
                f"🤝 La tua controproposta di {contro} per «{titolo}» è "
                f"stata accettata: l'acquirente ha "
                f"{ORE_PAGAMENTO_OFFERTA} ore per pagare. Ti avvisiamo "
                f"appena i sats sono nel deposito di garanzia.")
        return {"ok": True, "stato": "accettata"}

    if azione == "rifiuta":
        con.execute("UPDATE offerte SET stato='rifiutata', scadenza=0, "
                    "aggiornato=? WHERE id=?", (adesso, offerta_id))
        con.commit()
        con.close()
        if off["stato"] == "proposta":
            await notifica(off["compratore_id"],
                f"Il venditore ha rifiutato la tua offerta di "
                f"{cifra_proposta} per «{titolo}». Se vuoi puoi riprovare "
                f"con una cifra diversa, o comprare a prezzo pieno.{link}")
        else:
            await notifica(off["venditore_id"],
                f"L'acquirente ha rifiutato la tua controproposta per "
                f"«{titolo}». L'annuncio resta in vetrina come sempre.")
        return {"ok": True, "stato": "rifiutata"}

    # Controproposta: la cifra del venditore, sopra l'offerta ricevuta
    # e mai sopra il listino (a quel punto tanto vale il prezzo pieno).
    grezzo = str(d.get("importo", "")).strip()
    contro_sats, contro_eur = 0, 0.0
    if off["valuta"] == "eur":
        try:
            contro_eur = round(float(grezzo.replace(",", ".")), 2)
        except ValueError:
            contro_eur = 0.0
        contro, offerto, listino = (contro_eur, off["importo_eur"],
                                    off["listino_eur"])
    else:
        try:
            contro_sats = int(float(grezzo))
        except ValueError:
            contro_sats = 0
        contro, offerto, listino = (contro_sats, off["importo_sats"],
                                    off["listino_sats"])
    if contro <= offerto:
        con.close()
        raise HTTPException(400, "La controproposta deve superare "
                                 "l'offerta ricevuta — altrimenti "
                                 "accettala 🙂")
    if contro > listino:
        con.close()
        raise HTTPException(400, "La controproposta non può superare il "
                                 "prezzo dell'annuncio")
    con.execute("UPDATE offerte SET stato='controproposta', contro_sats=?, "
                "contro_eur=?, scadenza=?, aggiornato=? WHERE id=?",
                (contro_sats, contro_eur,
                 adesso + ORE_RISPOSTA_OFFERTA * 3600, adesso, offerta_id))
    con.commit()
    con.close()
    await notifica(off["compratore_id"],
        f"🤝 <b>Controproposta!</b> Per «{titolo}» il venditore ti propone "
        f"{_cifra_offerta(off['valuta'], contro_sats, contro_eur)} (avevi "
        f"offerto {cifra_proposta}). Accetta o rifiuta dalla scheda Ordini "
        f"entro {ORE_RISPOSTA_OFFERTA} ore.{link}")
    return {"ok": True, "stato": "controproposta"}


# ------------------------ API: OFFERTA LAMPO ------------------------
# Lo sconto a tempo su TUTTO l'annuncio (modello Vinted «sconto ai
# follower»): pubblico — chiunque compri nella finestra paga scontato —
# ma l'avviso arriva solo a chi ha l'annuncio nel barattolo, senza che
# il venditore sappia mai chi ne' quanti. Non tocca mai il listino:
# prezzo_sats/prezzo_eur restano pieni (e il NIP-99 con loro), lo
# sconto vive nelle colonne lampo_* e si applica alla invoice.

def _prezzo_lampo(a, percento: int):
    """Il prezzo scontato nella valuta del listino: (sats, eur), uno
    dei due a zero come nelle offerte. Mai sotto 1 sat / 0.01 €."""
    if a["valuta"] == "eur" and a["prezzo_eur"] > 0:
        return 0, max(0.01, round(a["prezzo_eur"] * (100 - percento) / 100, 2))
    return max(1, a["prezzo_sats"] * (100 - percento) // 100), 0.0


def _quando_scade(ts: int) -> str:
    """«alle 18:30», «alle 18:30 di domani», «alle 18:30 del 02/08»:
    l'ora della scadenza detta come la direbbe una persona."""
    s = time.localtime(ts)
    oggi = time.localtime()
    ora = time.strftime("%H:%M", s)
    if (s.tm_year, s.tm_yday) == (oggi.tm_year, oggi.tm_yday):
        return f"alle {ora}"
    domani = time.localtime(time.time() + 86400)
    if (s.tm_year, s.tm_yday) == (domani.tm_year, domani.tm_yday):
        return f"alle {ora} di domani"
    return f"alle {ora} del {time.strftime('%d/%m', s)}"


async def _avvisa_savers_lampo(a: dict, percento: int, scadenza: int,
                               savers: list):
    """L'avviso ai barattoli: uno per uno e con calma, mai i nomi —
    nessuno sa chi altro ce l'ha nel barattolo. Fail-open: un errore
    qui non tocca la lampo, che e' gia' in vetrina."""
    try:
        s_sats, s_eur = _prezzo_lampo(a, percento)
        vecchio = _cifra_offerta(a["valuta"], a["prezzo_sats"],
                                 a["prezzo_eur"])
        nuovo = _cifra_offerta(a["valuta"], s_sats, s_eur)
        for tg in savers:
            await notifica(tg, (
                f"⚡ <b>L'annuncio nel tuo barattolo è in sconto!</b>\n"
                f"«{html.escape(a['titolo'][:60])}»: <s>{vecchio}</s> → "
                f"<b>{nuovo}</b> (−{percento}%)\n"
                f"Hai tempo fino {_quando_scade(scadenza)}.\n"
                f"{URL_PUBBLICO}/annuncio/{a['id']}"))
            await asyncio.sleep(0.2)
    except Exception as e:
        print(f"⚠️ Avvisi lampo saltati: {e}")


@app.post("/api/listings/{annuncio_id}/lampo")
async def lancia_lampo(annuncio_id: int, req: Request,
                       x_tg_init_data: str = Header(""),
                       barattolo_sessione: str = Cookie("")):
    """Il venditore lancia lo sconto: percentuale e durata dalle
    opzioni del config. L'annuncio non si blocca e il listino non
    cambia; alla scadenza il prezzo torna pieno da solo."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    if not LAMPO_ATTIVE:
        raise HTTPException(400, "Le offerte lampo non sono attive")
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND stato='attivo'",
                    (annuncio_id,)).fetchone()
    if not a:
        con.close()
        raise HTTPException(404, "Annuncio non disponibile")
    if a["venditore_id"] != user["id"]:
        con.close()
        raise HTTPException(403, "Solo il venditore può lanciare "
                                 "un'offerta lampo")
    # Vale anche per gli importati da Nostr: lo sconto e' locale (le
    # colonne lampo_*, mai il listino), l'evento sui relay resta col
    # prezzo pieno e l'import orario non tocca la lampo.
    try:
        percento = int(d.get("percento", 0))
        ore = int(d.get("ore", 0))
    except (TypeError, ValueError):
        percento, ore = 0, 0
    if not (LAMPO_MIN_PERCENTO <= percento <= LAMPO_MAX_PERCENTO):
        con.close()
        raise HTTPException(400, f"Lo sconto va dal {LAMPO_MIN_PERCENTO}% "
                                 f"al {LAMPO_MAX_PERCENTO}%")
    if ore not in ORE_LAMPO_OPZIONI:
        con.close()
        raise HTTPException(400, "Durata non valida")
    adesso = int(time.time())
    if a["lampo_scadenza"] > adesso:
        con.close()
        raise HTTPException(400, "C'è già un'offerta lampo in corso su "
                                 "questo annuncio")
    # Il freno delle trattative: con un accordo gia' stretto (offerta
    # accettata in attesa di pagamento) niente lampo — il compratore
    # dell'accordo pagherebbe comunque il meglio dei due (compra() fa
    # il minimo), ma il venditore non deve potersi rimangiare la
    # stretta di mano cambiando le carte in tavola.
    accordo = con.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE annuncio_id=? AND "
        "stato='accettata' AND scadenza>?", (annuncio_id, adesso)).fetchone()["n"]
    if accordo:
        con.close()
        raise HTTPException(400, "C'è una trattativa accettata in corso: "
                                 "aspetta che si concluda o scada")
    # Il tetto settimanale: count-guard senza await (patto anti-doppione).
    lanci = con.execute(
        "SELECT COUNT(*) AS n FROM offerte_lampo WHERE annuncio_id=? AND "
        "creato>=?", (annuncio_id, adesso - 7 * 86400)).fetchone()["n"]
    if lanci >= MAX_LAMPO_SETTIMANA:
        con.close()
        raise HTTPException(400, f"Hai già lanciato {MAX_LAMPO_SETTIMANA} "
                                 "offerte lampo su questo annuncio negli "
                                 "ultimi 7 giorni: riprova più avanti")
    scadenza = adesso + ore * 3600
    con.execute("UPDATE annunci SET lampo_percento=?, lampo_scadenza=?, "
                "lampo_creato=? WHERE id=?",
                (percento, scadenza, adesso, annuncio_id))
    con.execute("INSERT INTO offerte_lampo(annuncio_id,venditore_id,"
                "percento,scadenza,creato) VALUES(?,?,?,?,?)",
                (annuncio_id, user["id"], percento, scadenza, adesso))
    con.commit()
    # I destinatari si leggono ORA (la lista e' gia' vera), l'invio va
    # in create_task: i relay Nostr sono lenti e la risposta no.
    savers = [r["tg_id"] for r in con.execute(
        "SELECT tg_id FROM preferiti WHERE annuncio_id=? AND tg_id!=?",
        (annuncio_id, user["id"]))]
    con.close()
    if savers:
        asyncio.create_task(
            _avvisa_savers_lampo(dict(a), percento, scadenza, savers))
    return {"ok": True, "percento": percento, "scadenza": scadenza}


@app.post("/api/listings/{annuncio_id}/lampo/annulla")
def annulla_lampo(annuncio_id: int, x_tg_init_data: str = Header(""),
                  barattolo_sessione: str = Cookie("")):
    """Il ripensamento del venditore: il prezzo torna pieno subito.
    Nessun avviso ai barattoli (sarebbe solo rumore) e il lancio resta
    nello storico: annullare non restituisce il gettone del tetto
    settimanale, altrimenti lancia-e-annulla sarebbe spam gratis."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    a = con.execute("SELECT venditore_id, lampo_scadenza FROM annunci "
                    "WHERE id=?", (annuncio_id,)).fetchone()
    if not a:
        con.close()
        raise HTTPException(404, "Annuncio non trovato")
    if a["venditore_id"] != user["id"]:
        con.close()
        raise HTTPException(403, "Solo il venditore può annullare")
    if a["lampo_scadenza"] <= int(time.time()):
        con.close()
        raise HTTPException(400, "Non c'è nessuna offerta lampo in corso")
    con.execute("UPDATE annunci SET lampo_percento=0, lampo_scadenza=0 "
                "WHERE id=?", (annuncio_id,))
    con.commit()
    con.close()
    return {"ok": True}


# ---------------------- API: ORDINI / ESCROW ------------------------

@app.post("/api/orders")
async def compra(req: Request, x_tg_init_data: str = Header(""),
                               barattolo_sessione: str = Cookie("")):
    """L'acquirente avvia l'acquisto: creiamo la invoice escrow."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    con = db()
    a = con.execute("SELECT * FROM annunci WHERE id=? AND stato='attivo'",
                    (d["annuncio_id"],)).fetchone()
    if not a:
        raise HTTPException(404, "Annuncio non disponibile")
    if a["venditore_id"] == user["id"]:
        raise HTTPException(400, "Non puoi comprare il tuo stesso annuncio")

    # L'acquisto alla cifra pattuita: con offerta_id nel body il prezzo
    # dell'articolo diventa quello dell'accordo. L'offerta deve essere
    # MIA, su QUESTO annuncio, accettata e ancora nei tempi.
    off = None
    if d.get("offerta_id"):
        off = con.execute(
            "SELECT * FROM offerte WHERE id=? AND compratore_id=? AND "
            "annuncio_id=? AND stato='accettata'",
            (d["offerta_id"], user["id"], a["id"])).fetchone()
        if not off:
            con.close()
            raise HTTPException(404, "Offerta non trovata o non più valida")
        adesso = int(time.time())
        if 0 < off["scadenza"] < adesso:
            con.execute("UPDATE offerte SET stato='scaduta', aggiornato=? "
                        "WHERE id=?", (adesso, off["id"]))
            con.commit()
            con.close()
            raise HTTPException(400, "Il tempo per pagare questa offerta "
                                     "è finito: l'offerta è scaduta")
        if off["ordine_id"]:
            # Una invoice viva c'e' gia'? Pagare quella VECCHIA
            # bloccherebbe un ordine che nessun gancio riconduce piu'
            # all'offerta: meglio un no adesso.
            viva = con.execute(
                "SELECT id FROM ordini WHERE id=? AND stato='creato'",
                (off["ordine_id"],)).fetchone()
            if viva:
                con.close()
                raise HTTPException(400, "C'è già una invoice in corso "
                                         "per questa offerta: pagala, "
                                         "oppure annulla quell'ordine e "
                                         "riprova")

    # La scelta della consegna, validata contro la modalita'
    # dell'annuncio: il compratore non puo' chiedere cio' che il
    # venditore non offre. Annuncio senza modalita' ('') = flusso
    # storico, la scelta si ignora; 'entrambe' senza scelta (client
    # vecchio in cache) = spedizione — e nessuna sorpresa, perche' il
    # client mostra comunque i sats veri della risposta.
    scelta = d.get("consegna", "")
    if not a["consegna"]:
        scelta = ""
    elif a["consegna"] == "entrambe":
        if scelta not in ("spedizione", "ritiro"):
            scelta = "spedizione"
    elif scelta and scelta != a["consegna"]:
        con.close()
        raise HTTPException(400, "Questo annuncio non prevede questa "
                                 "modalità di consegna")
    else:
        scelta = a["consegna"]

    # Per gli annunci in EUR i sats si decidono ADESSO, al cambio
    # corrente: la invoice vive 15 minuti, e quella e' la durata del
    # prezzo bloccato. Se scade, il prossimo tentativo riconverte.
    # Articolo e spedizione si convertono INSIEME, allo stesso cambio;
    # un annuncio tutto-sats non dipende mai dal cambio.
    prezzo_sats_eff, prezzo_eur_eff = a["prezzo_sats"], a["prezzo_eur"]
    if off:
        # La cifra pattuita sostituisce il listino — SOLO l'articolo:
        # spedizione e protezione si calcolano come per ogni ordine.
        prezzo_sats_eff, prezzo_eur_eff = _importo_accordo(off)
    if a["lampo_percento"] > 0 and a["lampo_scadenza"] > int(time.time()):
        # L'offerta lampo e' PUBBLICA: vale per chiunque paghi nella
        # finestra, anche senza barattolo. Se coesiste un accordo
        # individuale vince il MINIMO: chi compra paga sempre il
        # meglio dei due, mai una lampo che peggiora l'accordo.
        l_sats, l_eur = _prezzo_lampo(a, a["lampo_percento"])
        if a["valuta"] == "eur" and a["prezzo_eur"] > 0:
            prezzo_eur_eff = min(prezzo_eur_eff, l_eur)
        else:
            prezzo_sats_eff = min(prezzo_sats_eff, l_sats)
    articolo, cambio_ordine = prezzo_sats_eff, 0.0
    sped = a["spedizione_sats"] if scelta == "spedizione" else 0
    # Spedizione ANCORATA all'euro su listino sats (spedizione_eur
    # piena): i sats si decidono ADESSO, col cambio corrente. Senza
    # cambio l'ordine con spedizione non puo' partire — 503 onesto,
    # SOLO per questa scelta: il ritiro resta sempre acquistabile e
    # l'articolo in sats non dipende mai dal cambio.
    if (scelta == "spedizione" and a["valuta"] != "eur"
            and a["spedizione_eur"] > 0):
        cambio_ordine = await cambio_btc_eur()
        if cambio_ordine <= 0:
            con.close()
            raise HTTPException(503, "La spedizione di questo annuncio ha "
                                     "il prezzo in euro e il cambio non è "
                                     "disponibile in questo momento: "
                                     "riprova tra poco")
        sped = round(a["spedizione_eur"] / cambio_ordine * 100_000_000)
    if a["valuta"] == "eur" and a["prezzo_eur"] > 0:
        cambio_ordine = await cambio_btc_eur()
        if cambio_ordine <= 0:
            con.close()
            raise HTTPException(503, "Il cambio euro non è disponibile in "
                                     "questo momento: riprova tra qualche "
                                     "minuto")
        articolo = max(1, round(prezzo_eur_eff / cambio_ordine * 100_000_000))
        if scelta == "spedizione":
            sped = round(a["spedizione_eur"] / cambio_ordine * 100_000_000)
        # Il tetto di rodaggio con +20% di tolleranza: la volatilita'
        # ordinaria passa, un crollo del cambio no — e il venditore
        # si ripara da solo ritoccando il prezzo (la modifica
        # riconvalida al cambio di oggi). Il tetto guarda il solo
        # articolo, come alla pubblicazione.
        if TETTO_SATS_ANNUNCIO and articolo > TETTO_SATS_ANNUNCIO * 1.2:
            con.close()
            await notifica(a["venditore_id"],
                f"📈 Il cambio si è mosso troppo: il tuo annuncio "
                f"«{a['titolo'][:60]}» ({a['prezzo_eur']:.2f} EUR) supera "
                f"ora il tetto di {TETTO_SATS_ANNUNCIO} sats e gli acquisti "
                f"sono in pausa. Ritocca il prezzo per riaprirli.")
            raise HTTPException(409, "Il cambio è cambiato troppo da quando "
                                     "l'annuncio è stato pubblicato: il "
                                     "venditore deve ritoccare il prezzo")

    # La protezione acquisti: percentuale sul SOLO articolo, per
    # difetto (mai un sat piu' del promesso), anche sul ritiro in zona
    # (copre il deposito di garanzia, non il trasporto). Oggi la leva
    # e' a 0: il ramo esiste ma non scatta. Il compratore paga il
    # TOTALE nel deposito; al rilascio il venditore riceve
    # articolo+spedizione e la protezione resta alla piattaforma.
    prot = articolo * PROTEZIONE_PERCENTO // 100
    totale = articolo + sped + prot

    inv = await crea_invoice_escrow(
        totale, f"Barattolo escrow #{a['id']}: {a['titolo'][:40]}")
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,prezzo_sats,"
        "stato,payment_hash,creato,aggiornato,cambio_ordine,"
        "consegna_scelta,spedizione_sats,protezione_sats) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (a["id"], user["id"], a["venditore_id"], totale,
         "creato", inv["payment_hash"], int(time.time()), int(time.time()),
         cambio_ordine, scelta, sped, prot))
    ordine_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    if off:
        # Il legame ordine-offerta nella STESSA transazione: nessuna
        # finestra in cui l'uno esiste senza l'altro.
        con.execute("UPDATE offerte SET ordine_id=?, aggiornato=? "
                    "WHERE id=?", (ordine_id, int(time.time()), off["id"]))
    con.commit()
    con.close()
    # prezzo_sats resta il TOTALE (i client di ieri leggono quello);
    # le quote scomposte sono in piu', per il conto in chiaro.
    return {"ordine_id": ordine_id, "invoice": inv["payment_request"],
            "payment_hash": inv["payment_hash"], "prezzo_sats": totale,
            "articolo_sats": articolo, "spedizione_sats": sped,
            "protezione_sats": prot, "consegna": scelta,
            "offerta_id": off["id"] if off else 0}


@app.post("/api/orders/{ordine_id}/verifica-pagamento")
async def verifica_pagamento(ordine_id: int, x_tg_init_data: str = Header(""),
                                             barattolo_sessione: str = Cookie("")):
    """La Mini App chiama questo endpoint dopo il pagamento:
    se la invoice risulta pagata, i sats sono in cassaforte -> LOCKED."""
    verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
    if not o:
        raise HTTPException(404, "Ordine non trovato")
    if o["stato"] != "creato":
        return {"stato": o["stato"]}
    if await invoice_pagata(o["payment_hash"]):
        # Passaggio ATOMICO: la Mini App chiama in polling e coi bottoni
        # "ho pagato", quindi qui possono arrivare piu' chiamate insieme
        # (la richiesta a LNbits qui sopra e' lenta). Vince solo chi
        # flippa DAVVERO la riga da 'creato' a 'locked': gli altri escono
        # senza rinotificare il venditore.
        cur = con.execute(
            "UPDATE ordini SET stato='locked', aggiornato=? "
            "WHERE id=? AND stato='creato'",
            (int(time.time()), ordine_id))
        if cur.rowcount == 0:
            con.commit()
            con.close()
            return {"stato": "locked"}
        con.execute("UPDATE annunci SET stato='venduto' WHERE id=?",
                    (o["annuncio_id"],))
        a = con.execute("SELECT contatto_nostr, titolo FROM annunci "
                        "WHERE id=?", (o["annuncio_id"],)).fetchone()
        # Le offerte su questo annuncio si chiudono col pagamento:
        # quella che ha generato l'ordine si conclude, tutte le altre
        # ancora vive decadono — l'annuncio non si e' mai bloccato,
        # e ha vinto chi ha pagato per primo.
        adesso = int(time.time())
        con.execute("UPDATE offerte SET stato='conclusa', aggiornato=? "
                    "WHERE ordine_id=? AND stato='accettata'",
                    (adesso, ordine_id))
        decadute = con.execute(
            "SELECT id, compratore_id FROM offerte WHERE annuncio_id=? "
            "AND stato IN ('proposta','controproposta','accettata')",
            (o["annuncio_id"],)).fetchall()
        if decadute:
            con.execute(
                "UPDATE offerte SET stato='decaduta', aggiornato=? "
                "WHERE annuncio_id=? AND stato IN "
                "('proposta','controproposta','accettata')",
                (adesso, o["annuncio_id"]))
        con.commit()
        # Anche la piazza Nostr deve sapere che l'oggetto e' andato
        asyncio.create_task(annuncio_su_nostr(o["annuncio_id"], "sold",
                                              solo_aggiornamento=True))
        # ...e il post nel canale si aggiorna col ✅ Venduto
        asyncio.create_task(promo_venduto(o["annuncio_id"]))
        msg = ("🔒 <b>Hai venduto!</b> I sats dell'acquirente sono bloccati "
               "nel deposito di garanzia. "
               "Spedisci l'oggetto e segna l'ordine come spedito nella Mini App. 📦")
        if a and a["contatto_nostr"]:
            msg += ("\n\n🟣 Questo annuncio è pubblicato anche su <b>Nostr</b>: "
                    "ricordati di segnarlo come <b>venduto (sold)</b> dal tuo "
                    "client, così nessun altro proverà a comprarlo lì.")
        await notifica(o["venditore_id"], msg)
        # Il polso dei moderatori: e' nato un ordine, sats in cassaforte
        await polso_ordini_admin(
            f"🛒 <b>Nuovo ordine:</b> «{(a['titolo'] if a else '?')[:60]}» — "
            f"{o['prezzo_sats']} sats. Ordini aperti: {{aperti}}")
        # Il garbo verso chi restava in trattativa: l'oggetto e' andato.
        # MAI al compratore che ha appena pagato: se aveva un'altra
        # offerta sua, decade in silenzio (dirgli «venduto a qualcun
        # altro» sarebbe falso).
        for riga in decadute:
            if riga["compratore_id"] == o["compratore_id"]:
                continue
            await notifica(riga["compratore_id"],
                f"🕊 «{a['titolo'][:60]}» è appena stato venduto a "
                f"qualcun altro: la tua offerta decade. In vetrina ci "
                f"sono altre occasioni che aspettano!")
        con.close()
        return {"stato": "locked"}
    con.close()
    return {"stato": "in_attesa"}


@app.post("/api/orders/{ordine_id}/spedito")
async def segna_spedito(ordine_id: int, req: Request,
                        x_tg_init_data: str = Header(""),
                        barattolo_sessione: str = Cookie("")):
    """Il venditore segna la spedizione, con corriere e numero di
    tracciamento (l'acquirente li vedrà). Da qui parte il timer di
    sblocco d'ufficio: se dopo GIORNI_AUTO_SBLOCCO nessuno segnala
    nulla, i sats vanno al venditore."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    corriere = (d.get("corriere") or "").strip()[:40]
    tracking = (d.get("tracking") or "").strip()[:60]
    # 'Ritiro in zona' e' il gemello di 'Consegna a mano' per gli
    # ordini col ritiro scelto dal compratore: niente pacco, niente
    # tracciamento — ma il timer di sblocco d'ufficio parte uguale.
    if corriere not in ("Consegna a mano", "Ritiro in zona") and not tracking:
        raise HTTPException(400, "Inserisci il numero di tracciamento "
                                 "(o scegli 'Consegna a mano')")
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND venditore_id=? "
                    "AND stato='locked'", (ordine_id, user["id"])).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    con.execute("UPDATE ordini SET stato='shipped', corriere=?, tracking=?, "
                "spedito_il=?, aggiornato=? WHERE id=?",
                (corriere, tracking, int(time.time()), int(time.time()),
                 ordine_id))
    con.commit()
    con.close()
    if corriere == "Ritiro in zona":
        await notifica(o["compratore_id"],
                       f"🤝 <b>Il venditore ha segnato la consegna a mano</b>. "
                       f"Se hai ritirato l'oggetto, confermalo nella Mini App "
                       f"per sbloccare i sats al venditore.")
        return {"ok": True}
    dettaglio = (f"con <b>{corriere}</b>, tracciamento <b>{tracking}</b>"
                 if tracking else "in consegna a mano")
    await notifica(o["compratore_id"],
                   f"📦 <b>Il tuo oggetto è in viaggio</b> {dettaglio}! "
                   f"Quando arriva, conferma nella Mini App per sbloccare i "
                   f"sats al venditore.")
    return {"ok": True}


@app.post("/api/orders/{ordine_id}/consegnato")
async def segna_consegnato(ordine_id: int, x_tg_init_data: str = Header(""),
                                           barattolo_sessione: str = Cookie("")):
    """SOLO L'ACQUIRENTE segnala l'arrivo del pacco: si apre la sua
    finestra di ORE_CONFERMA ore per controllare l'oggetto; allo
    scadere, sblocco automatico al venditore.
    (Il venditore NON puo' usarlo: potrebbe far partire il timer
    prima della consegna reale. La sua protezione e' lo sblocco
    d'ufficio a GIORNI_AUTO_SBLOCCO giorni. In futuro questo scatto
    arrivera' in automatico dal tracking del corriere.)"""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND stato='shipped' "
                    "AND compratore_id=?",
                    (ordine_id, user["id"])).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    con.execute("UPDATE ordini SET stato='delivered', consegnato=?, "
                "aggiornato=? WHERE id=?",
                (int(time.time()), int(time.time()), ordine_id))
    con.commit()
    con.close()
    await notifica(o["venditore_id"],
                   f"📬 L'acquirente ha segnalato la <b>consegna del pacco</b>: "
                   f"ha {ORE_CONFERMA} ore per controllare l'oggetto, poi i "
                   f"sats si sbloccano automaticamente.")
    return {"ok": True, "stato": "delivered"}


@app.post("/api/orders/{ordine_id}/sollecita")
async def sollecita_acquirente(ordine_id: int, x_tg_init_data: str = Header(""),
                                               barattolo_sessione: str = Cookie("")):
    """Il venditore invia un promemoria Telegram all'acquirente
    (massimo uno ogni 24 ore, per non trasformarlo in molestia)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND venditore_id=? "
                    "AND stato IN ('shipped','delivered')",
                    (ordine_id, user["id"])).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    if o["sollecito_il"] and o["sollecito_il"] > int(time.time()) - 86400:
        con.close()
        raise HTTPException(400, "Hai già inviato un promemoria nelle "
                                 "ultime 24 ore")
    con.execute("UPDATE ordini SET sollecito_il=? WHERE id=?",
                (int(time.time()), ordine_id))
    con.commit()
    con.close()
    await notifica(o["compratore_id"],
                   "🔔 <b>Promemoria dal venditore:</b> se il pacco è arrivato, "
                   "apri l'ordine nella Mini App e conferma la ricezione (o "
                   "segnala un problema). Grazie! 🙏")
    return {"ok": True}


def e_admin(tg_id: int) -> bool:
    """L'utente e' un moderatore? (nel collaudo: l'identita' 999)"""
    return tg_id in ADMIN_IDS or (MODALITA_COLLAUDO and tg_id == 999)


# ---------------------- API: PROFILO / INCASSI ----------------------

# ------------------- DOPPIONI SU NOSTR ------------------------------
# Il doppio cittadino puo' avere lo stesso oggetto due volte sui
# relay: l'annuncio importato (evento firmato da LUI) e quello nativo
# ripubblicato dalla piattaforma. Qui si RILEVANO le coppie sospette;
# il ritiro — sempre e solo della copia della piattaforma, mai
# dell'originale dell'utente — lo decide l'utente con un click
# esplicito, mai il codice da solo.

def _impronta_titolo(titolo: str) -> str:
    """Le parole del titolo normalizzato, in ordine alfabetico:
    'iPhone 13 Pro usato' e 'Usato iphone 13 pro' hanno la stessa
    impronta. Niente fuzzy: meglio pochi match certi che tanti dubbi."""
    return " ".join(sorted(normalizza(titolo).split()))


def _prezzi_compatibili(a, b) -> bool:
    """La conferma sul prezzo (il criterio primario e' il titolo).
    EUR contro EUR e' un confronto tra numeri stabili (scarto <=10%);
    sui sats si tollera di piu' (<=30%) perche' l'import riconverte
    il prezzo dell'importato al cambio di ogni ora mentre il nativo
    resta fissato al cambio di pubblicazione."""
    if a["prezzo_eur"] and b["prezzo_eur"]:
        x, y, tolleranza = a["prezzo_eur"], b["prezzo_eur"], 0.10
    else:
        x, y, tolleranza = a["prezzo_sats"], b["prezzo_sats"], 0.30
    return abs(x - y) <= max(x, y) * tolleranza


def trova_doppioni_nostr(con, tg_id: int) -> list:
    """Le coppie (importato, nativo) dello stesso venditore che
    sembrano lo stesso oggetto. Restano fuori le coppie archiviate
    con «non e' un doppione». Guardia d'ingresso: chi non ha annunci
    importati — la quasi totalita' degli utenti — esce subito."""
    campi = "id, titolo, prezzo_sats, valuta, prezzo_eur, foto"
    importati = con.execute(
        f"SELECT {campi} FROM annunci WHERE venditore_id=? "
        "AND stato='attivo' AND contatto_nostr!=''", (tg_id,)).fetchall()
    if not importati:
        return []
    nativi = con.execute(
        f"SELECT {campi} FROM annunci WHERE venditore_id=? "
        "AND stato='attivo' AND contatto_nostr='' AND nostr_event_id!=''",
        (tg_id,)).fetchall()
    if not nativi:
        return []
    ignorate = {(r["id_importato"], r["id_nativo"]) for r in con.execute(
        "SELECT id_importato, id_nativo FROM doppioni_ignorati")}

    def scheda(r):
        try:
            foto0 = (json.loads(r["foto"]) or [""])[0]
        except Exception:
            foto0 = ""
        return dict(id=r["id"], titolo=r["titolo"],
                    prezzo_sats=r["prezzo_sats"], valuta=r["valuta"],
                    prezzo_eur=r["prezzo_eur"], foto0=foto0)

    coppie = []
    for imp in importati:
        for nat in nativi:
            if ((imp["id"], nat["id"]) in ignorate
                    or _impronta_titolo(imp["titolo"])
                    != _impronta_titolo(nat["titolo"])
                    or not _prezzi_compatibili(imp, nat)):
                continue
            coppie.append({"importato": scheda(imp), "nativo": scheda(nat)})
    return coppie


# ------------------- AVATAR DEL PROFILO (lug 2026) ------------------
# La foto accanto al nome, presa dal social di provenienza: la foto
# profilo Telegram per chi entra da Telegram, la picture del kind-0
# per chi entra con Nostr. MAI un link agli originali: gli URL delle
# foto via Bot API contengono il TOKEN del bot e scadono in un'ora,
# quelli Nostr sono host esterni arbitrari (e ogni visitatore della
# vetrina gli regalerebbe il suo IP). Quindi: si scarica, si riduce a
# un francobollo 128px e si serve la NOSTRA copia da foto/ col nome
# 'av_{negozio}_{ts}.jpg' — chiave = codice negozio pubblico (mai il
# tg_id, che non deve uscire), timestamp = versione anti-cache: la
# cache di 1 giorno su /foto lavora gratis come per le _min. Il
# francobollo e' seconda generazione ammessa dal patto della filiera,
# come le miniature. Fail-open totale: tutto gira in create_task e
# senza foto resta l'iniziale di sempre.
AVATAR_LATO = 128
AVATAR_QUALITA = 85
GIORNI_AVATAR = 7                    # rinfresco opportunistico
_AVATAR_IN_CORSO: set[int] = set()   # anti-valanga: un fetch per utente


def _salva_avatar(negozio: str, raw: bytes | None) -> str:
    """Il francobollo: quadrato ritagliato al centro come le _min
    (il CSS poi lo fa tondo). '' = niente foto."""
    if not ImmaginePillow or not raw or not negozio:
        return ""
    try:
        img = ImmaginePillow.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, (AVATAR_LATO, AVATAR_LATO),
                           ImmaginePillow.Resampling.LANCZOS)
        nome = f"av_{negozio}_{int(time.time())}.jpg"
        img.save(os.path.join(FOTO_DIR, nome), "JPEG",
                 quality=AVATAR_QUALITA)
        return nome
    except Exception:
        return ""


def _scrivi_avatar(tg_id: int, nome_nuovo: str):
    """Aggiorna la colonna e spazza il file vecchio (i nomi sono
    versionati: il vecchio non serve piu' a nessuno). Si scrive anche
    il '' — la foto rimossa dal social sparisce anche da noi — e
    avatar_aggiornato si segna comunque: niente ritentativi a raffica
    per chi una foto non ce l'ha proprio."""
    con = db()
    r = con.execute("SELECT avatar FROM utenti WHERE tg_id=?",
                    (tg_id,)).fetchone()
    vecchio = r["avatar"] if r else ""
    con.execute("UPDATE utenti SET avatar=?, avatar_aggiornato=? "
                "WHERE tg_id=?", (nome_nuovo, int(time.time()), tg_id))
    con.commit()
    con.close()
    if vecchio and vecchio != nome_nuovo:
        try:
            os.remove(os.path.join(FOTO_DIR, vecchio))
        except OSError:
            pass


async def _foto_profilo_telegram(tg_id: int) -> bytes | None:
    """La foto profilo che il bot vede (se l'utente la nasconde ai
    non-contatti, il bot non vede nulla: e' il suo modo di dire no).
    L'URL del file va scaricato subito e mai esposto: porta il token.
    In collaudo bot_api simula e qui esce None, come deve."""
    r = await bot_api("getUserProfilePhotos",
                      {"user_id": tg_id, "limit": 1})
    try:
        taglie = r["result"]["photos"][0]
        # le misure arrivano in ordine crescente: la prima che copre
        # il francobollo basta, e pesa meno
        t = next((t for t in taglie
                  if t.get("width", 0) >= AVATAR_LATO), taglie[-1])
        f = await bot_api("getFile", {"file_id": t["file_id"]})
        percorso = f["result"]["file_path"]
        async with httpx.AsyncClient(timeout=15) as c:
            resp = await c.get("https://api.telegram.org/file/"
                               f"bot{BOT_TOKEN}/{percorso}")
            resp.raise_for_status()
            return resp.content
    except Exception:
        return None    # niente foto, privacy o rete che manca: pari sono


def _kind0_picture(relay: str, hexkey: str):
    """Chiede a UN relay il profilo kind-0 e ne estrae 'picture'.
    Sincrona: va in asyncio.to_thread (pattern chiedi_relay_dm)."""
    try:
        ws = create_connection(relay, timeout=5,
                               sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.send(json.dumps(["REQ", "av", {
            "kinds": [0], "authors": [hexkey], "limit": 1}]))
        url, inizio = None, time.time()
        while time.time() - inizio < 6:
            msg = json.loads(ws.recv())
            if msg[0] == "EVENT" and msg[1] == "av":
                trovata = (json.loads(msg[2].get("content") or "{}")
                           .get("picture") or "").strip()
                url = trovata or url
            elif msg[0] == "EOSE":
                break
        ws.close()
        return url
    except Exception:
        return None


async def _foto_profilo_nostr(npub: str) -> bytes | None:
    """La picture del kind-0 dai 4 relay, scaricata con le stesse
    guardie delle foto da URL dell'import (anti-SSRF + tetto 8MB):
    l'URL lo scrive l'utente nel suo profilo, non un fidato."""
    if not create_connection:
        return None
    try:
        hexkey = npub_to_hex(npub)
    except Exception:
        return None
    risposte = await asyncio.gather(*[
        asyncio.to_thread(_kind0_picture, r, hexkey)
        for r in RELAYS_VERIFICA])
    url = next((u for u in risposte if u), None)
    if not url or not url_foto_ammesso(url):
        return None
    return await asyncio.to_thread(scarica_foto_import, url)


async def aggiorna_avatar(tg_id: int):
    """Rinfresca il francobollo dal social scelto in avatar_scelta:
    '' = automatico, la catena dei doppi cittadini — prima la foto
    Telegram (l'anagrafica comanda: dopo la fusione nome e username
    vengono da li'), poi la picture Nostr, e senza nulla l'iniziale;
    'telegram' | 'nostr' = solo quella gamba, senza ripiego (la
    scelta esplicita si rispetta: il social senza foto = iniziale);
    'nessuna' = non si scarica proprio. La gamba Nostr SOLO da chiave
    dal possesso dimostrato, la regola di notifica(): mai pescare la
    foto di Caio perche' Tizio ne ha dichiarato la npub."""
    if tg_id in _AVATAR_IN_CORSO:
        return
    _AVATAR_IN_CORSO.add(tg_id)
    try:
        con = db()
        u = con.execute(
            "SELECT negozio, npub, npub_verificata, npub_accesso, "
            "avatar_scelta FROM utenti WHERE tg_id=?",
            (tg_id,)).fetchone()
        con.close()
        if not u or not u["negozio"] or u["avatar_scelta"] == "nessuna":
            return
        scelta = u["avatar_scelta"]
        raw = None
        if tg_id > 0 and scelta in ("", "telegram"):
            raw = await _foto_profilo_telegram(tg_id)
        if not raw and scelta in ("", "nostr"):
            npub = u["npub_accesso"] or \
                (u["npub"] if u["npub_verificata"] else "")
            if npub:
                raw = await _foto_profilo_nostr(npub)
        _scrivi_avatar(tg_id, _salva_avatar(u["negozio"], raw))
    except Exception as e:
        print(f"⚠️ Avatar non aggiornato ({tg_id}): {e}")
    finally:
        _AVATAR_IN_CORSO.discard(tg_id)


@app.get("/api/me")
async def mio_profilo(x_tg_init_data: str = Header(""),
                      barattolo_sessione: str = Cookie("")):
    # async (era def) per il rinfresco dell'avatar in create_task:
    # il resto e' identico, sqlite qui e' questione di millisecondi
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
    # Rinfresco opportunistico del francobollo: alla prima apertura e
    # poi al piu' una volta a settimana, in sottofondo (fail-open:
    # questa risposta non lo aspetta, la foto compare al giro dopo).
    # Con 'nessuna' non si scarica nulla: la scelta si rispetta.
    if u and u["avatar_scelta"] != "nessuna" \
            and (int(time.time()) - (u["avatar_aggiornato"] or 0)
                 > GIORNI_AVATAR * 86400):
        asyncio.create_task(aggiorna_avatar(user["id"]))
    if u:
        # Passata silenziosa dei distintivi: cosi' Pioniere e compagni
        # compaiono al primo sguardo al Profilo, senza aspettare un
        # gancio. Scrittura su GET ma idempotente (INSERT OR IGNORE):
        # e' cio' che rende il sistema auto-riparante. Niente notifiche
        # qui: quelle spettano ai ganci dal vivo.
        controlla_distintivi(con, user["id"])
        con.commit()
    presi = {r["badge_id"]: r["ottenuto_il"] for r in con.execute(
        "SELECT badge_id, ottenuto_il FROM badge_utente WHERE tg_id=?",
        (user["id"],))}
    # Doppioni su Nostr: coppie importato/nativo che sembrano lo
    # stesso oggetto (vedi trova_doppioni_nostr). Per quasi tutti
    # la guardia interna esce subito con la lista vuota.
    doppioni = trova_doppioni_nostr(con, user["id"])
    # Le offerte che aspettano una MIA mossa: da venditore una proposta
    # da valutare, da compratore una controproposta o un'accettata da
    # pagare. Un numero solo, per il pallino sulla scheda Ordini.
    da_agire = con.execute(
        "SELECT COUNT(*) AS n FROM offerte WHERE "
        "(venditore_id=? AND stato='proposta') OR "
        "(compratore_id=? AND stato IN ('controproposta','accettata'))",
        (user["id"], user["id"])).fetchone()["n"]
    con.close()
    profilo = dict(u) if u else {}
    profilo["admin"] = e_admin(user["id"])
    profilo["doppioni_nostr"] = doppioni
    profilo["offerte_da_agire"] = da_agire
    # Le leve dell'offerta lampo per il foglio di lancio (solo il
    # proprietario lo apre): il client non hardcoda mai le cifre.
    profilo["lampo_leve"] = {
        "attive": bool(LAMPO_ATTIVE), "sconti": LAMPO_SCONTI,
        "minimo": LAMPO_MIN_PERCENTO, "massimo": LAMPO_MAX_PERCENTO,
        "ore": ORE_LAMPO_OPZIONI}
    # Il catalogo COMPLETO, con la data per i guadagnati e null per gli
    # altri: il frontend non deve mai conoscere la lista a memoria.
    profilo["distintivi"] = [
        dict(id=d["id"], emoji=d["emoji"], nome=d["nome"],
             descrizione=d["descrizione"], fiducia=d["fiducia"],
             ottenuto=presi.get(d["id"]))
        for d in DISTINTIVI]
    return profilo


@app.post("/api/me/doppioni/{annuncio_id}/ritira")
async def ritira_doppione(annuncio_id: int,
                          x_tg_init_data: str = Header(""),
                          barattolo_sessione: str = Cookie("")):
    """Ritira dai relay la copia del doppione firmata dalla
    PIATTAFORMA (mai l'originale dell'utente, che non si tocca).
    L'annuncio su Barattolo resta com'e': diventa solo-locale, e con
    nostr_event_id vuoto nessun gancio lo ripubblichera' piu'.
    Lo stato non conta: ritirare l'evento di un nativo nel frattempo
    venduto o rimosso e' innocuo e deduplica comunque."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if not _NOSTR:
        raise HTTPException(503, "La funzione Nostr non e' attiva sul server")
    con = db()
    a = con.execute(
        "SELECT venditore_id, contatto_nostr, nostr_event_id "
        "FROM annunci WHERE id=?", (annuncio_id,)).fetchone()
    con.close()
    if not a or a["venditore_id"] != user["id"]:
        raise HTTPException(404, "Annuncio non trovato")
    if a["contatto_nostr"]:
        raise HTTPException(400, "Questo e' l'annuncio importato: "
                                 "l'originale non si tocca mai")
    if not a["nostr_event_id"]:
        raise HTTPException(400, "Gia' sistemato: questo annuncio non "
                                 "e' piu' pubblicato su Nostr")
    # Qui si ASPETTA il risultato dei relay (niente create_task):
    # l'utente ha chiesto un'azione e merita una risposta onesta.
    ok = await ritira_da_nostr(annuncio_id, esigi_ok=True)
    if not ok:
        raise HTTPException(502, "I relay non rispondono: non e' "
                                 "cambiato nulla, riprova tra poco")
    return {"ok": True, "relay": ok}


@app.post("/api/me/doppioni/ignora")
async def ignora_doppione(req: Request, x_tg_init_data: str = Header(""),
                          barattolo_sessione: str = Cookie("")):
    """«Non e' un doppione»: la coppia si archivia per sempre, su
    ogni dispositivo (per questo sta nel DB e non in localStorage)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    try:
        id_imp = int(d.get("id_importato") or 0)
        id_nat = int(d.get("id_nativo") or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, "Coppia non valida")
    if id_imp <= 0 or id_nat <= 0 or id_imp == id_nat:
        raise HTTPException(400, "Coppia non valida")
    con = db()
    miei = {r["id"] for r in con.execute(
        "SELECT id FROM annunci WHERE venditore_id=? AND id IN (?,?)",
        (user["id"], id_imp, id_nat))}
    if miei != {id_imp, id_nat}:
        con.close()
        raise HTTPException(404, "Annuncio non trovato")
    con.execute("INSERT OR IGNORE INTO doppioni_ignorati"
                "(id_importato, id_nativo, tg_id, creato) VALUES(?,?,?,?)",
                (id_imp, id_nat, user["id"], int(time.time())))
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/me/ln-address")
async def salva_ln_address(req: Request, x_tg_init_data: str = Header(""),
                                         barattolo_sessione: str = Cookie("")):
    """Il venditore imposta (una volta sola) il suo Lightning address:
    da quel momento tutti gli incassi sono AUTOMATICI. Prima di
    salvarlo lo verifichiamo dal vivo con una richiesta di prova.
    Se il venditore ha ordini gia' confermati in attesa, i sats
    partono immediatamente."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    addr = (d.get("ln_address") or "").strip().lower()

    if addr:
        if "@" not in addr or "." not in addr.split("@")[-1]:
            raise HTTPException(400, "Formato non valido: dev'essere tipo nome@wallet.com")
        # Verifica dal vivo: il wallet risponde e accetta almeno 100 sats?
        if not await invoice_da_ln_address(addr, 100):
            raise HTTPException(400,
                "Questo Lightning address non risponde: controlla di averlo "
                "scritto giusto (lo trovi nel tuo wallet, tipo nome@walletofsatoshi.com)")

    con = db()
    con.execute("UPDATE utenti SET ln_address=? WHERE tg_id=?",
                (addr, user["id"]))
    # Ci sono incassi o rimborsi rimasti in sospeso? Ora possiamo sbloccarli.
    incassi = [r["id"] for r in con.execute(
        "SELECT id FROM ordini WHERE venditore_id=? AND stato='confirmed'",
        (user["id"],))] if addr else []
    rimborsi = [r["id"] for r in con.execute(
        "SELECT id FROM ordini WHERE compratore_id=? AND stato='refund'",
        (user["id"],))] if addr else []
    con.commit()
    con.close()
    sbloccati = 0
    for oid in incassi:
        r = await _sblocca_sats(oid)
        if r.get("ok"):
            sbloccati += 1
    for oid in rimborsi:
        r = await _rimborsa_compratore(oid)
        if r.get("ok"):
            sbloccati += 1
    return {"ok": True, "ln_address": addr, "incassi_sbloccati": sbloccati}


# La npub e' "npub1" + 58 caratteri del charset bech32. Controllo di
# SOLO FORMATO: la npub resta AUTO-DICHIARATA e NON verificata (la
# proprieta' si dimostra con la nota pubblica qui sotto, oppure
# entrando col login Nostr, che firma una sfida).
RE_NPUB = re.compile(r"^npub1[023456789acdefghjklmnpqrstuvwxyz]{58}$")


@app.post("/api/me/npub")
async def salva_npub(req: Request, x_tg_init_data: str = Header(""),
                                   barattolo_sessione: str = Cookie("")):
    """Badge Nostr del profilo: l'utente dichiara la sua npub (chiave
    PUBBLICA) e i suoi annunci mostrano il badge. Stringa vuota = rimozione.
    REGOLA FERREA: mai chiedere ne' accettare nsec (chiavi private)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    npub = (d.get("npub") or "").strip().lower().removeprefix("nostr:")
    if npub.startswith("nsec"):
        raise HTTPException(400,
            "Quella e' una chiave PRIVATA (nsec): non incollarla MAI, qui "
            "o altrove! Serve la npub, la chiave pubblica (inizia con npub1)")
    if npub and not RE_NPUB.fullmatch(npub):
        raise HTTPException(400,
            "Formato non valido: la npub inizia con npub1 ed e' lunga 63 caratteri")
    con = db()
    attuale = con.execute(
        "SELECT npub, npub_verificata, npub_accesso FROM utenti WHERE tg_id=?",
        (user["id"],)).fetchone()
    # REGOLA nativo Nostr: se questa npub e' anche la SUA chiave
    # d'ingresso e non c'e' una chat Telegram (tg_id<0), rimuoverla
    # lo chiuderebbe fuori per sempre. Prima si collega Telegram.
    if not npub and attuale and user["id"] < 0 \
            and attuale["npub"] \
            and attuale["npub"] == attuale["npub_accesso"]:
        con.close()
        raise HTTPException(400,
            "Questa npub e' il tuo unico modo di entrare: collega prima "
            "Telegram dal blocco «Identita'», poi potrai rimuoverla")
    verificata = bool(attuale and attuale["npub_verificata"])
    accesso_revocato = False
    canale_azzerato = False
    if not attuale or npub != attuale["npub"]:
        # npub nuova, cambiata o rimossa: la verifica riparte da zero.
        # E se quel badge era anche la chiave d'accesso web, la revoca
        # del badge revoca pure l'accesso (la credenziale era nata DA
        # quel badge verificato). SOLO su account Telegram (tg_id>0):
        # a un nativo Nostr la chiave d'ingresso non si toglie mai,
        # resterebbe chiuso fuori per sempre.
        verificata = False
        accesso_revocato = bool(attuale and user["id"] > 0
                                and attuale["npub_accesso"]
                                and attuale["npub_accesso"] == attuale["npub"])
        con.execute(
            "UPDATE utenti SET npub=?, npub_verificata=0, "
            "verifica_codice='', verifica_scade=0, "
            "npub_accesso=CASE WHEN tg_id>0 AND npub_accesso=? "
            "THEN '' ELSE npub_accesso END WHERE tg_id=?",
            (npub, attuale["npub"] if attuale else "", user["id"]))
        # Se il canale avvisi scelto era Nostr ma la destinazione non
        # esiste piu' (niente chiave d'accesso ne' badge verificato),
        # si torna all'automatico: il cassetto Avvisi non deve mentire.
        cur = con.execute(
            "UPDATE utenti SET canale_notifiche='' WHERE tg_id=? "
            "AND canale_notifiche IN ('nostr','entrambi') "
            "AND npub_accesso='' AND (npub='' OR npub_verificata=0)",
            (user["id"],))
        canale_azzerato = cur.rowcount > 0
    con.commit()
    con.close()
    return {"ok": True, "npub": npub, "npub_verificata": verificata,
            "accesso_revocato": accesso_revocato,
            "canale_azzerato": canale_azzerato}


@app.post("/api/me/canale-notifiche")
async def scegli_canale_notifiche(req: Request,
                                  x_tg_init_data: str = Header(""),
                                  barattolo_sessione: str = Cookie("")):
    """L'utente sceglie dove ricevere gli avvisi: 'telegram', 'nostr'
    (DM cifrato NIP-17), 'entrambi', oppure '' = automatico (Telegram
    se c'e' la chat, DM Nostr per i nativi). Si accetta solo un canale
    che puo' davvero raggiungerlo."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    canale = (d.get("canale") or "").strip().lower()
    if canale not in ("", "telegram", "nostr", "entrambi"):
        raise HTTPException(400, "Canale sconosciuto: telegram, nostr, "
                                 "entrambi o vuoto (automatico)")
    con = db()
    u = con.execute(
        "SELECT npub, npub_verificata, npub_accesso FROM utenti "
        "WHERE tg_id=?", (user["id"],)).fetchone()
    if not u:
        con.close()
        raise HTTPException(404, "Profilo non trovato")
    ha_nostr = bool(u["npub_accesso"] or
                    (u["npub"] and u["npub_verificata"]))
    if canale in ("nostr", "entrambi") and not ha_nostr:
        con.close()
        raise HTTPException(400,
            "Prima verifica la tua npub (o entra con Nostr): i DM si "
            "mandano solo a una chiave di cui hai dimostrato il possesso")
    if canale in ("telegram", "entrambi") and user["id"] < 0:
        con.close()
        raise HTTPException(400,
            "Questo account non ha una chat Telegram: collegala dal "
            "blocco «Le tue identita'»")
    con.execute("UPDATE utenti SET canale_notifiche=? WHERE tg_id=?",
                (canale, user["id"]))
    con.commit()
    con.close()
    return {"ok": True, "canale": canale}


@app.post("/api/me/avatar-scelta")
async def scegli_avatar(req: Request,
                        x_tg_init_data: str = Header(""),
                        barattolo_sessione: str = Cookie("")):
    """Il selettore «La tua foto» del cassetto Identita': da quale
    social prendere il francobollo — '' = automatico (la catena
    Telegram → Nostr → iniziale), 'telegram' | 'nostr' espliciti per
    chi ha entrambe le sorgenti, 'nessuna' = iniziale ovunque per il
    pubblico (reversibile: il file resta in dispensa e il CASE nelle
    SELECT lo tiene in casa). Si accetta solo una sorgente che esiste
    davvero — il pattern di canale-notifiche."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    scelta = (d.get("scelta") or "").strip().lower()
    if scelta not in ("", "telegram", "nostr", "nessuna"):
        raise HTTPException(400, "Scelta sconosciuta: telegram, nostr, "
                                 "nessuna o vuoto (automatico)")
    con = db()
    u = con.execute(
        "SELECT npub, npub_verificata, npub_accesso FROM utenti "
        "WHERE tg_id=?", (user["id"],)).fetchone()
    if not u:
        con.close()
        raise HTTPException(404, "Profilo non trovato")
    if scelta == "telegram" and user["id"] < 0:
        con.close()
        raise HTTPException(400,
            "Questo account non ha una chat Telegram: collegala dal "
            "blocco «Le tue identita'»")
    ha_nostr = bool(u["npub_accesso"] or
                    (u["npub"] and u["npub_verificata"]))
    if scelta == "nostr" and not ha_nostr:
        con.close()
        raise HTTPException(400,
            "Prima verifica la tua npub (o entra con Nostr): la foto si "
            "prende solo da una chiave di cui hai dimostrato il possesso")
    con.execute("UPDATE utenti SET avatar_scelta=? WHERE tg_id=?",
                (scelta, user["id"]))
    con.commit()
    con.close()
    # La sorgente e' cambiata: il francobollo in dispensa puo' venire
    # dall'altro social, si rifa' subito (con 'nessuna' non si scarica)
    if scelta != "nessuna":
        asyncio.create_task(aggiorna_avatar(user["id"]))
    return {"ok": True, "scelta": scelta}


# --- Avvisi di ricerca: «dimmi quando esce quello che cerco» ---------
# L'utente salva fino a 5 ricerche (categorie, comune+raggio, prezzo
# max, parole chiave) e il matching alla pubblicazione lo avvisa via
# notifica() multi-canale. Il motore vive accanto ai post automatici.

MAX_AVVISI_UTENTE = 5
RAGGI_AMMESSI = (10, 25, 50, 100)


def _avviso_pubblico(r) -> dict:
    """La riga del DB come la vede il frontend: categorie da
    '|A|B|' a lista, il resto com'e'."""
    return {"id": r["id"],
            "categorie": [c for c in r["categorie"].split("|") if c],
            "comune": r["comune"], "raggio_km": r["raggio_km"],
            "prezzo_max_sats": r["prezzo_max_sats"],
            "prezzo_max_eur": r["prezzo_max_eur"],
            "parole": r["parole"], "attivo": r["attivo"]}


@app.get("/api/comuni")
async def cerca_comuni(q: str = "",
                       x_tg_init_data: str = Header(""),
                       barattolo_sessione: str = Cookie("")):
    """Suggerimenti per il campo comune del form avvisi: primi 10
    comuni per prefisso. Autenticato come tutto cio' che non e'
    vetrina."""
    verifica_utente(x_tg_init_data, barattolo_sessione)
    prefisso = normalizza(q)
    if len(prefisso) < 2:
        return {"comuni": []}
    trovati = [c for c in COMUNI_LISTA
               if normalizza(c["nome"]).startswith(prefisso)][:10]
    return {"comuni": trovati}


@app.get("/api/me/avvisi-ricerca")
async def lista_avvisi_ricerca(x_tg_init_data: str = Header(""),
                               barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    righe = con.execute("SELECT * FROM avvisi_ricerca WHERE tg_id=? "
                        "ORDER BY creato DESC, id DESC",
                        (user["id"],)).fetchall()
    con.close()
    return {"avvisi": [_avviso_pubblico(r) for r in righe],
            "max": MAX_AVVISI_UTENTE,
            "comuni_attivi": bool(COMUNI)}


@app.post("/api/me/avvisi-ricerca")
async def salva_avviso_ricerca(req: Request,
                               x_tg_init_data: str = Header(""),
                               barattolo_sessione: str = Cookie("")):
    """Crea un avviso di ricerca, o lo aggiorna se il payload porta
    un id (solo il proprietario). Ogni criterio e' facoltativo, ma
    almeno uno ci vuole: un avviso vuoto sarebbe tutta la vetrina
    in chat."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)

    # categorie: si tengono solo quelle del catalogo, senza doppioni
    grezze = d.get("categorie") or []
    if not isinstance(grezze, list):
        raise HTTPException(400, "Categorie in formato sbagliato")
    scelte = [c for c in CATEGORIE if c in grezze]
    categorie = ("|" + "|".join(scelte) + "|") if scelte else ""

    # comune + raggio: il comune deve venire dal dataset, cosi'
    # l'avviso ha SEMPRE coordinate buone (il testo libero resta
    # solo dal lato annunci, dov'e' dichiarato)
    comune = (d.get("comune") or "").strip()
    raggio = d.get("raggio_km") or 0
    lat = lon = 0.0
    if comune:
        if not COMUNI:
            raise HTTPException(400, "La ricerca per zona ora non e' "
                                     "disponibile: riprova senza comune")
        coord = COMUNI.get(normalizza(comune))
        if not coord:
            raise HTTPException(400, f"Non conosco il comune «{comune[:40]}»: "
                                     "scegli un nome dai suggerimenti")
        lat, lon = coord
        if raggio not in RAGGI_AMMESSI:
            raise HTTPException(400, "Scegli un raggio tra 10, 25, 50 "
                                     "o 100 km")
    else:
        comune, raggio = "", 0

    # prezzo massimo nella valuta scelta (mai entrambe)
    prezzo_max_sats, prezzo_max_eur = 0, 0.0
    try:
        prezzo_max = float(str(d.get("prezzo_max") or 0).replace(",", "."))
    except ValueError:
        raise HTTPException(400, "Prezzo massimo non valido")
    if prezzo_max < 0:
        raise HTTPException(400, "Prezzo massimo non valido")
    if prezzo_max:
        if (d.get("valuta") or "sats") == "eur":
            prezzo_max_eur = round(prezzo_max, 2)
        else:
            prezzo_max_sats = int(prezzo_max)

    # parole chiave: normalizzate ORA, mai a ogni match
    parole = [p for p in normalizza(d.get("parole") or "").split()
              if len(p) >= 2][:6]
    parole_txt = " ".join(parole)

    if not (categorie or comune or prezzo_max_sats or prezzo_max_eur
            or parole_txt):
        raise HTTPException(400, "Dimmi almeno un criterio: categoria, "
                                 "comune, prezzo o parole chiave")

    con = db()
    avviso_id = d.get("id")
    if avviso_id:
        mio = con.execute("SELECT id FROM avvisi_ricerca WHERE id=? "
                          "AND tg_id=?", (avviso_id, user["id"])).fetchone()
        if not mio:
            con.close()
            raise HTTPException(404, "Avviso non trovato")
        con.execute("UPDATE avvisi_ricerca SET categorie=?, comune=?, "
                    "lat=?, lon=?, raggio_km=?, prezzo_max_sats=?, "
                    "prezzo_max_eur=?, parole=? WHERE id=?",
                    (categorie, comune, lat, lon, raggio,
                     prezzo_max_sats, prezzo_max_eur, parole_txt,
                     avviso_id))
    else:
        quanti = con.execute("SELECT COUNT(*) AS n FROM avvisi_ricerca "
                             "WHERE tg_id=?", (user["id"],)).fetchone()["n"]
        if quanti >= MAX_AVVISI_UTENTE:
            con.close()
            raise HTTPException(400, f"Hai gia' {MAX_AVVISI_UTENTE} avvisi: "
                                     "eliminane uno per farne di nuovi")
        con.execute("INSERT INTO avvisi_ricerca(tg_id, categorie, comune, "
                    "lat, lon, raggio_km, prezzo_max_sats, prezzo_max_eur, "
                    "parole, attivo, creato) VALUES(?,?,?,?,?,?,?,?,?,1,?)",
                    (user["id"], categorie, comune, lat, lon, raggio,
                     prezzo_max_sats, prezzo_max_eur, parole_txt,
                     int(time.time())))
    con.commit()
    con.close()
    return {"ok": True}


@app.post("/api/me/avvisi-ricerca/{avviso_id}/pausa")
async def pausa_avviso_ricerca(avviso_id: int,
                               x_tg_init_data: str = Header(""),
                               barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    r = con.execute("SELECT attivo FROM avvisi_ricerca WHERE id=? AND "
                    "tg_id=?", (avviso_id, user["id"])).fetchone()
    if not r:
        con.close()
        raise HTTPException(404, "Avviso non trovato")
    nuovo = 0 if r["attivo"] else 1
    con.execute("UPDATE avvisi_ricerca SET attivo=? WHERE id=?",
                (nuovo, avviso_id))
    con.commit()
    con.close()
    return {"ok": True, "attivo": nuovo}


@app.post("/api/me/avvisi-ricerca/{avviso_id}/elimina")
async def elimina_avviso_ricerca(avviso_id: int,
                                 x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    con.execute("DELETE FROM avvisi_ricerca WHERE id=? AND tg_id=?",
                (avviso_id, user["id"]))
    con.commit()
    con.close()
    return {"ok": True}


# --- Verifica della npub con una nota pubblica -----------------------
# L'utente dimostra di POSSEDERE la npub pubblicando dal suo client una
# nota (kind 1) con un codice generato da noi. Nessuna nsec, nessuna
# firma da consegnare, MAI (regola ferrea): solo una nota pubblica, che
# dopo la verifica puo' anche cancellare senza conseguenze.
# Relay e conversione bech32->hex sono lo specchio di importa_nostr.py
# (oggi importabile, ma i gemelli restano: il server non deve dipendere
# da uno script che vive di vita propria).

RELAYS_VERIFICA = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://nostr.mom",
]
CHARSET_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def npub_to_hex(npub: str) -> str:
    """Converte la npub (bech32) nella chiave esadecimale dei relay."""
    dati = [CHARSET_BECH32.find(c) for c in npub[5:]]
    if -1 in dati:
        raise ValueError("npub non valida: carattere sconosciuto")
    dati = dati[:-6]                     # togli il checksum
    bits, val, out = 0, 0, []
    for d in dati:                       # da gruppi di 5 bit a byte
        val = (val << 5) | d
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((val >> bits) & 0xFF)
    hexkey = bytes(out).hex()
    if len(hexkey) != 64:
        raise ValueError("npub non valida: lunghezza sbagliata")
    return hexkey


def _bech32_polymod(valori: list) -> int:
    """Il cuore del checksum bech32 (BIP-173): un registro a scorrimento
    che 'mastica' i valori a 5 bit. Serve solo a hex_to_npub."""
    gen = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
    chk = 1
    for v in valori:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= gen[i]
    return chk


def hex_to_npub(hexkey: str) -> str:
    """Gemella SPECULARE di npub_to_hex: dalla chiave esadecimale alla
    npub bech32, checksum vero incluso (a differenza della decodifica,
    qui il checksum va CALCOLATO, non buttato). Proprieta' di sanita':
    npub_to_hex(hex_to_npub(h)) == h."""
    dati, bits, val = [], 0, 0
    for byte in bytes.fromhex(hexkey):   # da byte a gruppi di 5 bit
        val = (val << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            dati.append((val >> bits) & 31)
    if bits:
        dati.append((val << (5 - bits)) & 31)
    # hrp "npub" espansa come vuole lo standard: bit alti, zero, bit bassi
    hrp = [ord(c) >> 5 for c in "npub"] + [0] + [ord(c) & 31 for c in "npub"]
    polymod = _bech32_polymod(hrp + dati + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return "npub1" + "".join(CHARSET_BECH32[d] for d in dati + checksum)


def cerca_nota_verifica(relay: str, hexkey: str, codice: str, da: int) -> bool:
    """Chiede a UN relay le note recenti della npub e guarda se una
    contiene il codice. E' SINCRONA (websocket-client): il server e'
    async, quindi va chiamata dentro asyncio.to_thread."""
    try:
        ws = create_connection(relay, timeout=5,
                               sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.send(json.dumps(["REQ", "verifica", {
            "kinds": [1], "authors": [hexkey], "since": da, "limit": 50}]))
        inizio = time.time()
        while time.time() - inizio < 6:
            msg = json.loads(ws.recv())
            if msg[0] == "EVENT" and msg[1] == "verifica":
                if codice in msg[2].get("content", ""):
                    ws.close()
                    return True
            elif msg[0] == "EOSE":
                break
        ws.close()
    except Exception:
        pass                  # relay muto o irraggiungibile: pazienza
    return False


@app.post("/api/me/npub/verifica-avvia")
async def verifica_npub_avvia(x_tg_init_data: str = Header(""),
                              barattolo_sessione: str = Cookie("")):
    """Primo passo: generiamo il codice univoco da pubblicare in una
    nota Nostr. Vale 1 ora."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute("SELECT npub, npub_verificata FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
    if not u or not u["npub"]:
        con.close()
        raise HTTPException(400, "Prima salva la tua npub nel profilo")
    if u["npub_verificata"]:
        con.close()
        return {"ok": True, "gia_verificata": True}
    codice = f"barattolo-verify-{secrets.token_hex(3)}"
    con.execute("UPDATE utenti SET verifica_codice=?, verifica_scade=? "
                "WHERE tg_id=?", (codice, int(time.time()) + 3600, user["id"]))
    con.commit()
    con.close()
    return {"ok": True, "codice": codice,
            "istruzioni": ("Pubblica dal tuo client Nostr (Damus, Amethyst, "
                           "Primal…) una nota con questo codice, poi torna "
                           "qui e premi «Ho pubblicato, controlla». Dopo la "
                           "verifica puoi cancellare la nota.")}


@app.post("/api/me/npub/verifica-controlla")
async def verifica_npub_controlla(x_tg_init_data: str = Header(""),
                                  barattolo_sessione: str = Cookie("")):
    """Secondo passo: cerchiamo sui relay una nota recente della npub
    che contenga il codice. Trovata = la npub e' davvero sua."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if create_connection is None:
        raise HTTPException(503, "Verifica non disponibile: sul server "
                                 "manca il pacchetto websocket-client")
    con = db()
    u = con.execute(
        "SELECT npub, npub_verificata, verifica_codice, verifica_scade "
        "FROM utenti WHERE tg_id=?", (user["id"],)).fetchone()
    con.close()
    if not u or not u["npub"]:
        raise HTTPException(400, "Prima salva la tua npub nel profilo")
    if u["npub_verificata"]:
        return {"ok": True, "verificata": True}
    if not u["verifica_codice"]:
        raise HTTPException(400, "Prima avvia la verifica per avere il codice")
    if time.time() > u["verifica_scade"]:
        raise HTTPException(400,
            "Il codice e' scaduto (vale 1 ora): avvia una nuova verifica")
    try:
        hexkey = npub_to_hex(u["npub"])
    except ValueError:
        raise HTTPException(400, "La npub salvata non e' valida: reinseriscila")
    # Tutti i relay in parallelo (ognuno nel suo thread): basta un si'.
    # "da" = poco prima dell'avvio della verifica, per note recenti.
    da = u["verifica_scade"] - 3600 - 600
    esiti = await asyncio.gather(*[
        asyncio.to_thread(cerca_nota_verifica, r, hexkey,
                          u["verifica_codice"], da)
        for r in RELAYS_VERIFICA])
    if not any(esiti):
        return {"ok": True, "verificata": False,
                "msg": ("Nota non ancora trovata: i relay a volte tardano "
                        "qualche minuto. Riprova tra poco!")}
    con = db()
    con.execute("UPDATE utenti SET npub_verificata=1, verifica_codice='', "
                "verifica_scade=0 WHERE tg_id=?", (user["id"],))
    con.commit()
    con.close()
    await notifica(user["id"],
                   "🟣 <b>npub verificata!</b> Da adesso i tuoi annunci "
                   "portano il badge dei venditori verificati su Nostr. 🎉 "
                   "(La nota col codice ora puoi anche cancellarla.)")
    await premia_distintivi(user["id"])
    return {"ok": True, "verificata": True}


# --- Doppia cittadinanza: il badge diventa chiave d'ingresso ---------
# Un utente Telegram con la npub VERIFICATA puo' promuoverla a chiave
# d'accesso (npub_accesso): da quel momento entra nello STESSO account
# anche dal web col login Nostr. Il badge non verificato non basta mai:
# potrebbe essere la dichiarazione (falsa) di una chiave altrui.

@app.post("/api/me/npub/abilita-accesso")
async def abilita_accesso_nostr(x_tg_init_data: str = Header(""),
                                barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute(
        "SELECT npub, npub_verificata, npub_accesso FROM utenti "
        "WHERE tg_id=?", (user["id"],)).fetchone()
    if not u or not u["npub"] or not u["npub_verificata"]:
        con.close()
        raise HTTPException(400, "Prima verifica la tua npub (badge 🟣): "
                                 "solo un badge verificato puo' aprire l'account")
    if u["npub_accesso"]:
        con.close()
        raise HTTPException(400, "L'accesso con Nostr e' gia' attivo")
    try:
        # Le condizioni si ripetono nella WHERE: tra la lettura sopra e
        # questa scrittura non deve essere cambiato nulla.
        con.execute("UPDATE utenti SET npub_accesso=npub WHERE tg_id=? "
                    "AND npub_accesso='' AND npub_verificata=1",
                    (user["id"],))
        con.commit()
    except sqlite3.IntegrityError:
        # L'indice unico fa da giudice: quella chiave apre gia' un altro
        # account (probabilmente il suo account nativo Nostr) e la
        # strada giusta e' la fusione, non un doppione.
        con.close()
        raise HTTPException(409,
            "Questa chiave apre gia' un altro account: se e' il tuo "
            "account Nostr, entra dal web con Nostr e usa «Collega Telegram»")
    con.close()
    await premia_distintivi(user["id"])
    return {"ok": True, "npub_accesso": True}


@app.post("/api/me/npub/disabilita-accesso")
def disabilita_accesso_nostr(x_tg_init_data: str = Header(""),
                             barattolo_sessione: str = Cookie("")):
    """Il gesto contrario: l'account torna apribile solo da Telegram."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if user["id"] < 0:
        # Doppia cintura col tg_id>0 nella WHERE qui sotto: un nativo
        # Nostr e' entrato PROPRIO con questa chiave, togliergliela
        # significherebbe chiuderlo fuori per sempre.
        raise HTTPException(400, "Sei entrato proprio con questa chiave: "
                                 "toglierla ti chiuderebbe fuori per sempre")
    con = db()
    con.execute("UPDATE utenti SET npub_accesso='' WHERE tg_id=? AND tg_id>0",
                (user["id"],))
    con.commit()
    con.close()
    return {"ok": True, "npub_accesso": False}


# --- Barattolo su Nostr: gli annunci in piazza -----------------------
# Quando un annuncio supera la moderazione, il server lo firma con la
# chiave DELLA PIATTAFORMA (mai degli utenti: regola ferrea) e lo
# pubblica come "classified listing" NIP-99 (kind 30402) sugli stessi
# 4 relay della verifica. Venduto -> si ripubblica con status "sold"
# (stesso tag "d": i relay sostituiscono il vecchio evento). Rimosso ->
# richiesta di cancellazione NIP-09 (kind 5). Tutto fail-open: se la
# chiave e' il segnaposto, mancano coincurve/websocket-client o i relay
# tacciono, l'annuncio su Barattolo vive normalmente e resta solo un
# avviso in console. Gli utenti solo-Telegram non vedono nulla.

URL_PUBBLICO = "https://barattolo.store"
LINK_BOT = "https://t.me/ilbarattolobot"


def nsec_to_bytes(nsec: str) -> bytes:
    """Converte la nsec (bech32) nei 32 byte della chiave privata.
    Gemella di npub_to_hex qui sopra, ma per la chiave segreta."""
    if not nsec.startswith("nsec1"):
        raise ValueError("deve iniziare con nsec1")
    dati = [CHARSET_BECH32.find(c) for c in nsec[5:]]
    if -1 in dati:
        raise ValueError("carattere sconosciuto")
    dati = dati[:-6]                     # togli il checksum
    bits, val, out = 0, 0, []
    for d in dati:                       # da gruppi di 5 bit a byte
        val = (val << 5) | d
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((val >> bits) & 0xFF)
    if len(out) != 32:
        raise ValueError("lunghezza sbagliata")
    return bytes(out)


def _prepara_nostr():
    """Prepara (chiave privata, pubkey esadecimale) della piattaforma,
    oppure None se la funzione Nostr e' spenta."""
    if not NOSTR_NSEC_PIATTAFORMA or NOSTR_NSEC_PIATTAFORMA.startswith("INCOLLA"):
        return None                      # segnaposto: funzione spenta
    if ChiavePrivataNostr is None or create_connection is None:
        print("⚠️ Nostr spento: mancano i pacchetti "
              "(pip install coincurve websocket-client)")
        return None
    try:
        sk = ChiavePrivataNostr(nsec_to_bytes(NOSTR_NSEC_PIATTAFORMA))
        # La pubkey per Nostr e' "x-only": via il primo byte dei 33
        pubkey = sk.public_key.format()[1:].hex()
        print(f"🟣 Barattolo pubblica su Nostr (pubkey {pubkey[:16]}…)")
        return sk, pubkey
    except Exception as e:
        print(f"⚠️ Nostr spento: NOSTR_NSEC_PIATTAFORMA non valida ({e})")
        return None


_NOSTR = _prepara_nostr()


def evento_non_firmato(pubkey: str, kind: int, tags: list, content: str,
                       creato: int) -> dict:
    """Costruisce un evento Nostr con l'id canonico NIP-01 ma SENZA
    firma. Serve a firma_evento e ai DM NIP-17, dove il messaggio
    interno (il "rumor") resta volutamente non firmato."""
    serial = json.dumps([0, pubkey, creato, kind, tags, content],
                        separators=(",", ":"), ensure_ascii=False)
    ev_id = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    return {"id": ev_id, "pubkey": pubkey, "created_at": creato,
            "kind": kind, "tags": tags, "content": content}


def firma_evento(kind: int, tags: list, content: str) -> dict:
    """Crea e firma un evento Nostr con la chiave della piattaforma.
    L'id e' lo sha256 della serializzazione canonica (NIP-01), la
    firma e' Schnorr BIP-340 (coincurve = libsecp256k1)."""
    sk, pubkey = _NOSTR
    ev = evento_non_firmato(pubkey, kind, tags, content, int(time.time()))
    ev["sig"] = sk.sign_schnorr(bytes.fromhex(ev["id"])).hex()
    return ev


def _foto_url_nostr(foto_json: str) -> list:
    """Dai nomi file salvati in DB agli URL assoluti che un client
    Nostr puo' mostrare (gli annunci importati hanno gia' URL http)."""
    try:
        nomi = json.loads(foto_json or "[]")
    except Exception:
        return []
    return [(n if n.startswith("http") else f"{URL_PUBBLICO}/foto/{n}")
            for n in nomi if n and not n.startswith("data:")]


def evento_annuncio(a: dict, status: str) -> dict:
    """Costruisce l'evento NIP-99 (kind 30402) di un annuncio. Il tag
    "d" stabile rende l'evento sostituibile: ripubblicare con lo stesso
    "d" aggiorna lo stato sui relay (e' il meccanismo NIP-99)."""
    # Il tag price parla la valuta scelta dal venditore (la spec NIP-99
    # supporta il codice valuta): per gli annunci EUR il listino resta
    # in euro anche in piazza, e importa_nostr.py sa gia' rileggerlo.
    if a.get("valuta") == "eur" and a.get("prezzo_eur"):
        prezzo_tag = ["price", f"{a['prezzo_eur']:.2f}", "EUR"]
        prezzo_txt = f"{a['prezzo_eur']:.2f} EUR"
    else:
        prezzo_tag = ["price", str(a["prezzo_sats"]), "sats"]
        prezzo_txt = f"{a['prezzo_sats']} sats"
    tags = [["d", f"barattolo-{a['id']}"],
            ["title", a["titolo"]],
            ["summary", (a["descrizione"] or a["titolo"])[:200]],
            prezzo_tag,
            ["status", status],
            ["published_at", str(a["creato"])],
            ["r", URL_PUBBLICO]]
    if a.get("categoria"):
        # Il tag "t" e' un hashtag: niente spazi. Delle categorie
        # composte in piazza va la prima parola ("Casa e giardino"
        # diventa "casa"), che e' anche quella che si cerca davvero.
        tags.append(["t", a["categoria"].lower().split()[0]])
    if a.get("zona"):
        tags.append(["location", a["zona"]])
    for url in _foto_url_nostr(a.get("foto", "")):
        tags.append(["image", url])
    # La consegna nel content, non nei tag: nessun tag nuovo da far
    # digerire a importa_nostr.py o ai client altrui.
    if a.get("consegna") in ("spedizione", "entrambe"):
        # spedizione_eur piena = costo in euro (listino EUR, oppure
        # l'ancora all'euro dei listini sats): in piazza parla euro
        if a.get("spedizione_eur"):
            consegna_txt = f" — spedizione: {a['spedizione_eur']:.2f} EUR"
        elif a.get("spedizione_sats"):
            consegna_txt = f" — spedizione: {a['spedizione_sats']} sats"
        else:
            consegna_txt = " — spedizione gratuita"
        if a.get("consegna") == "entrambe":
            consegna_txt += " o ritiro in zona"
    elif a.get("consegna") == "ritiro":
        consegna_txt = " — solo ritiro in zona"
    else:
        consegna_txt = ""
    content = ((a["descrizione"] or a["titolo"]).strip() +
               f"\n\nPrezzo: {prezzo_txt} — zona: "
               f"{a.get('zona') or 'Italia'}{consegna_txt}"
               f"\n\n🫙⚡ In vendita su Barattolo, il mercatino in sats "
               f"con escrow Lightning: {URL_PUBBLICO} · {LINK_BOT}")
    return firma_evento(30402, tags, content)


def evento_annuncio_importato(a: dict, titolo: str, descrizione: str,
                              categoria: str, zona: str, valuta: str,
                              prezzo_sats: int, prezzo_eur: float,
                              creato: int) -> dict:
    """L'evento NIP-99 aggiornato di un annuncio IMPORTATO, pronto per
    la firma del suo AUTORE (il doppio cittadino, nel suo browser):
    senza pubkey ne' id (li mette il firmatario) e col tag "d"
    ORIGINALE dell'evento — ripubblicare con lo stesso d sostituisce
    il vecchio sui relay (NIP-99). Diversamente da evento_annuncio,
    il content e' la descrizione PURA: niente footer promozionale ne'
    riga prezzo — non si scrive pubblicita' dentro un evento che firma
    un altro, e il footer rientrerebbe in descrizione al giro d'import
    successivo (estrai_annuncio legge il content)."""
    if valuta == "eur" and prezzo_eur:
        prezzo_tag = ["price", f"{prezzo_eur:.2f}", "EUR"]
    else:
        prezzo_tag = ["price", str(prezzo_sats), "sats"]
    tags = [["d", a["nostr_origine_d"]],
            ["title", titolo],
            ["summary", (descrizione or titolo)[:200]],
            prezzo_tag,
            ["status", "active"]]
    if categoria:
        tags.append(["t", categoria.lower().split()[0]])
    if zona:
        tags.append(["location", zona])
    # Le foto ripartono con gli URL ORIGINALI del venditore (v1: nella
    # modifica firmata non si cambiano). Se la colonna origine e' vuota
    # ma le foto ci sono (riga battezzata prima della colonna), ripiego
    # sugli URL nostri: mai un evento SENZA tag image per un annuncio
    # che le foto le ha, o l'import successivo le toglierebbe anche qui.
    try:
        originali = json.loads(a["nostr_origine_foto"] or "[]")
    except Exception:
        originali = []
    for url in (originali or _foto_url_nostr(a["foto"] or "")):
        tags.append(["image", url])
    return {"kind": 30402, "created_at": creato, "tags": tags,
            "content": (descrizione or titolo).strip()}


def invia_evento_relay(relay: str, evento: dict) -> bool:
    """Consegna un evento firmato a UN relay e aspetta il suo "OK".
    E' SINCRONA (websocket-client): va chiamata in asyncio.to_thread."""
    try:
        ws = create_connection(relay, timeout=5,
                               sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.send(json.dumps(["EVENT", evento]))
        inizio = time.time()
        while time.time() - inizio < 6:
            msg = json.loads(ws.recv())
            if msg[0] == "OK" and msg[1] == evento["id"]:
                ws.close()
                return bool(msg[2])
        ws.close()
    except Exception:
        pass                  # relay muto o irraggiungibile: pazienza
    return False


async def _spedisci_ai_relay(evento: dict, relays: list = None) -> int:
    """Manda l'evento a tutti i relay in parallelo (ognuno nel suo
    thread) e ritorna quanti l'hanno accettato. Nel collaudo non esce
    nulla dal computer: l'evento si stampa e basta. La lista relay di
    serie e' la nostra; la modifica firmata passa quella dell'import
    (che include il relay personale del venditore)."""
    relays = relays or RELAYS_VERIFICA
    if MODALITA_COLLAUDO:
        print(f"🟣 [nostr simulato] "
              f"{json.dumps(evento, ensure_ascii=False)[:400]}…")
        return len(relays)
    esiti = await asyncio.gather(*[
        asyncio.to_thread(invia_evento_relay, r, evento)
        for r in relays])
    return sum(esiti)


# ------------------- DM NOSTR CIFRATI (NIP-17) -----------------------
# Le notifiche possono arrivare come messaggi privati Nostr. Si CIFRA
# verso la chiave PUBBLICA dell'utente e si firma con la chiave della
# piattaforma: nessuna nsec altrui, mai (regola ferrea). Tre scatole
# cinesi: il "rumor" (kind 14, non firmato) col testo, il "sigillo"
# (kind 13, firmato da Barattolo) che lo contiene cifrato, e il "pacco
# regalo" (kind 1059, firmato da una chiave usa-e-getta) che viaggia
# sui relay senza rivelare nulla, nemmeno il mittente.


def _hkdf_estrai(sale: bytes, seme: bytes) -> bytes:
    """HKDF-extract (RFC 5869): dal segreto condiviso alla chiave."""
    return hmac.new(sale, seme, hashlib.sha256).digest()


def _hkdf_espandi(chiave: bytes, info: bytes, quanti: int) -> bytes:
    """HKDF-expand (RFC 5869): dalla chiave ai byte di lavoro."""
    fuori, blocco, giro = b"", b"", 1
    while len(fuori) < quanti:
        blocco = hmac.new(chiave, blocco + info + bytes([giro]),
                          hashlib.sha256).digest()
        fuori += blocco
        giro += 1
    return fuori[:quanti]


def _imbottisci(dati: bytes) -> bytes:
    """Il padding di NIP-44: 2 byte di lunghezza vera + testo + zeri
    fino alla misura a scalini (nasconde la lunghezza del messaggio)."""
    n = len(dati)
    if not 1 <= n <= 65535:
        raise ValueError("messaggio vuoto o troppo lungo per NIP-44")
    if n <= 32:
        totale = 32
    else:
        prossima_potenza = 1 << (n - 1).bit_length()
        passo = 32 if prossima_potenza <= 256 else prossima_potenza // 8
        totale = passo * ((n - 1) // passo + 1)
    return n.to_bytes(2, "big") + dati + b"\x00" * (totale - n)


def nip44_cifra(sk_bytes: bytes, dest_hex: str, testo: str) -> str:
    """Cifra un testo verso una chiave pubblica secondo NIP-44 v2.
    ATTENZIONE: il segreto condiviso e' la coordinata X NUDA del punto
    ECDH (mai PrivateKey.ecdh() di coincurve, che la passa per sha256:
    per Nostr sarebbe una chiave sbagliata)."""
    punto = ChiavePubblicaCompleta(
        b"\x02" + bytes.fromhex(dest_hex)).multiply(sk_bytes)
    x_condivisa = punto.format(compressed=True)[1:33]
    chiave_conv = _hkdf_estrai(b"nip44-v2", x_condivisa)
    nonce = secrets.token_bytes(32)
    lavoro = _hkdf_espandi(chiave_conv, nonce, 76)
    # ChaCha20 in cryptography vuole 16 byte di nonce: i primi 4 sono
    # il contatore iniziale (zero), poi i 12 byte veri di NIP-44
    cifratore = CifrarioDM(
        ChaCha20DM(lavoro[:32], b"\x00" * 4 + lavoro[32:44]),
        mode=None).encryptor()
    cifrato = cifratore.update(_imbottisci(testo.encode("utf-8")))
    mac = hmac.new(lavoro[44:], nonce + cifrato, hashlib.sha256).digest()
    return base64.b64encode(b"\x02" + nonce + cifrato + mac).decode()


def impacchetta_dm(dest_hex: str, testo: str) -> dict:
    """Confeziona un DM NIP-17 completo per il destinatario: rumor →
    sigillo → pacco regalo. Le date del sigillo e del pacco arretrano
    a caso fino a 2 giorni: cosi' nessuno correla i tempi di invio."""
    sk, pubkey = _NOSTR
    adesso = int(time.time())
    compatto = dict(separators=(",", ":"), ensure_ascii=False)
    rumor = evento_non_firmato(pubkey, 14, [["p", dest_hex]], testo, adesso)
    sigillo = evento_non_firmato(
        pubkey, 13, [],
        nip44_cifra(sk.secret, dest_hex, json.dumps(rumor, **compatto)),
        adesso - secrets.randbelow(172800))
    sigillo["sig"] = sk.sign_schnorr(bytes.fromhex(sigillo["id"])).hex()
    effimera = ChiavePrivataNostr()      # nuova per ogni messaggio
    pacco = evento_non_firmato(
        effimera.public_key.format()[1:].hex(), 1059, [["p", dest_hex]],
        nip44_cifra(effimera.secret, dest_hex,
                    json.dumps(sigillo, **compatto)),
        adesso - secrets.randbelow(172800))
    pacco["sig"] = effimera.sign_schnorr(bytes.fromhex(pacco["id"])).hex()
    return pacco


def chiedi_relay_dm(relay: str, hexkey: str):
    """Chiede a UN relay dove il destinatario vuole ricevere i DM
    (kind 10050, NIP-17). E' SINCRONA: va in asyncio.to_thread."""
    try:
        ws = create_connection(relay, timeout=5,
                               sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.send(json.dumps(["REQ", "dm", {
            "kinds": [10050], "authors": [hexkey], "limit": 1}]))
        inizio = time.time()
        trovati = None
        while time.time() - inizio < 6:
            msg = json.loads(ws.recv())
            if msg[0] == "EVENT" and msg[1] == "dm":
                lista = [t[1] for t in msg[2].get("tags", [])
                         if len(t) > 1 and t[0] == "relay"
                         and t[1].startswith("ws")]
                trovati = lista or trovati
            elif msg[0] == "EOSE":
                break
        ws.close()
        return trovati
    except Exception:
        return None               # relay muto o irraggiungibile: pazienza


_RELAY_DM_CACHE = {}   # hex destinatario -> (scadenza, lista relay)


async def relay_dm_di(dest_hex: str) -> list:
    """I relay dove consegnare il DM: quelli dichiarati dal destinatario
    (kind 10050) se li pubblica, altrimenti i nostri 4 standard — la
    specifica direbbe di NON inviare, ma per una notifica un tentativo
    e' meglio di zero. Cache in memoria 1h (uvicorn e' mono-processo)."""
    voce = _RELAY_DM_CACHE.get(dest_hex)
    if voce and voce[0] > time.time():
        return voce[1]
    risposte = await asyncio.gather(*[
        asyncio.to_thread(chiedi_relay_dm, r, dest_hex)
        for r in RELAYS_VERIFICA])
    relays = next((r for r in risposte if r), None)
    if not relays:
        relays = RELAYS_VERIFICA
    _RELAY_DM_CACHE[dest_hex] = (time.time() + 3600, relays[:4])
    return relays[:4]


async def manda_dm_nostr(dest_hex: str, testo: str) -> bool:
    """Recapita un DM NIP-17 al destinatario. Fail-open totale: ogni
    intoppo e' una riga in console, mai un errore al chiamante. Nel
    collaudo il pacco si confeziona davvero (cifratura compresa) ma
    non esce nulla dal computer."""
    if not _NOSTR or ChaCha20DM is None:
        return False
    try:
        pacco = impacchetta_dm(dest_hex, testo)
        if MODALITA_COLLAUDO:
            print(f"💌 [dm nostr simulato per {dest_hex[:16]}…] {testo}")
            return True
        esiti = await asyncio.gather(*[
            asyncio.to_thread(invia_evento_relay, r, pacco)
            for r in await relay_dm_di(dest_hex)])
        if not sum(esiti):
            print(f"⚠️ DM Nostr: nessun relay l'ha accettato "
                  f"({dest_hex[:16]}…)")
        return bool(sum(esiti))
    except Exception as e:
        print(f"⚠️ DM Nostr saltato ({dest_hex[:16]}…): {e}")
        return False


async def annuncio_su_nostr(annuncio_id: int, status: str,
                            solo_aggiornamento: bool = False):
    """Pubblica (o ripubblica con nuovo status) un annuncio su Nostr.
    Gira in sottofondo e non deve MAI disturbare chi usa la Mini App:
    qualsiasi intoppo finisce in console e basta.
    solo_aggiornamento=True: agisci solo se l'evento esiste gia'."""
    if not _NOSTR:
        return
    try:
        con = db()
        a = con.execute("SELECT * FROM annunci WHERE id=?",
                        (annuncio_id,)).fetchone()
        con.close()
        if not a or a["contatto_nostr"]:
            return   # importato da Nostr: l'evento e' gia' del venditore
        if solo_aggiornamento and not a["nostr_event_id"]:
            return
        evento = evento_annuncio(dict(a), status)
        ok = await _spedisci_ai_relay(evento)
        if not ok:
            print(f"⚠️ Annuncio #{annuncio_id}: nessun relay ha "
                  f"accettato l'evento Nostr ({status})")
            return
        con = db()
        con.execute("UPDATE annunci SET nostr_event_id=? WHERE id=?",
                    (evento["id"], annuncio_id))
        con.commit()
        con.close()
        print(f"🟣 Annuncio #{annuncio_id} su Nostr ({status}, "
              f"{ok}/{len(RELAYS_VERIFICA)} relay)")
    except Exception as e:
        print(f"⚠️ Pubblicazione Nostr saltata per l'annuncio "
              f"#{annuncio_id}: {e}")


async def ritira_da_nostr(annuncio_id: int, esigi_ok: bool = False) -> int:
    """Chiede ai relay di cancellare l'evento di un annuncio
    (NIP-09, kind 5). Di serie e' fire-and-forget come sopra
    (sottofondo, mai errori all'utente) e azzera comunque
    nostr_event_id; con esigi_ok=True — il ritiro di un doppione,
    chiesto esplicitamente dall'utente — serve almeno un relay che
    accetti, altrimenti non cambia NULLA e si puo' riprovare (il
    patto della modifica firmata: relay muti, messaggio onesto).
    Ritorna quanti relay hanno accettato."""
    if not _NOSTR:
        return 0
    try:
        con = db()
        a = con.execute("SELECT nostr_event_id FROM annunci WHERE id=?",
                        (annuncio_id,)).fetchone()
        con.close()
        if not a or not a["nostr_event_id"]:
            return 0
        evento = firma_evento(5, [
            ["e", a["nostr_event_id"]],
            ["a", f"30402:{_NOSTR[1]}:barattolo-{annuncio_id}"],
            ["k", "30402"]],
            "Annuncio rimosso da Barattolo")
        ok = await _spedisci_ai_relay(evento)
        if esigi_ok and not ok:
            print(f"⚠️ Ritiro #{annuncio_id}: nessun relay ha accettato, "
                  "non e' cambiato nulla")
            return 0
        con = db()
        con.execute("UPDATE annunci SET nostr_event_id='' WHERE id=?",
                    (annuncio_id,))
        con.commit()
        con.close()
        print(f"🟣 Annuncio #{annuncio_id} ritirato da Nostr "
              f"({ok}/{len(RELAYS_VERIFICA)} relay)")
        return ok
    except Exception as e:
        print(f"⚠️ Ritiro Nostr saltato per l'annuncio #{annuncio_id}: {e}")
        return 0


# ---------- I POST AUTOMATICI: la piattaforma racconta i fatti -------
# Quando un annuncio nuovo entra in vetrina, Barattolo lo annuncia da
# solo sui suoi canali: una nota Nostr kind-1 (firmata dalla chiave
# piattaforma) e un post nel canale Telegram (TELEGRAM_CANALE_ID, il
# bot deve esserne amministratore). Zero AI, zero editoriale: solo
# fatti veri, formattati bene.
# L'anti-spam e' una coda con drenatore a finestra: chi pubblica si
# limita ad accodare, il drenatore dorme ATTESA_RAGGRUPPO secondi e
# poi decide — pochi annunci e budget orario capiente = post singoli,
# una raffica (l'import CSV da 500 righe) = UN solo post aggregato.
# Fail-open totale: post fallito = riga in console, mai un errore per
# chi pubblica. In collaudo si simula tutto in console (bot_api e
# _spedisci_ai_relay lo fanno gia' da soli).

CODA_PROMO: list[int] = []              # annunci in attesa di annuncio
_drenatore_promo_avviato = False
_post_promo_recenti: list[float] = []   # timestamp dei post singoli
ATTESA_RAGGRUPPO = 5 if MODALITA_COLLAUDO else 90   # finestra (secondi)
SOGLIA_AGGREGA = 3         # piu' di cosi' in una finestra = aggregato
PAUSA_TRA_PROMO = 2        # secondi tra un post singolo e l'altro


def _fmt_sats(n: int) -> str:
    """80000 -> '80.000': i puntini delle migliaia all'italiana."""
    return f"{n:,}".replace(",", ".")


def _prezzo_promo(a: dict, cambio: float) -> str:
    """Il prezzo del post: la valuta del listino per prima, l'altra
    col ≈. Se il cambio non c'e' (CoinGecko muto) il ≈ si omette."""
    if a.get("valuta") == "eur" and a.get("prezzo_eur"):
        return (f"{a['prezzo_eur']:.2f} € "
                f"(≈ {_fmt_sats(a['prezzo_sats'])} sats)")
    prezzo = f"{_fmt_sats(a['prezzo_sats'])} sats"
    if cambio > 0:
        eur = a["prezzo_sats"] / 100_000_000 * cambio
        prezzo += f" (≈ {eur:.2f} €)"
    return prezzo


def _slug_categoria(a: dict) -> str:
    """La categoria come hashtag: minuscola e senza spazi
    ("Casa e giardino" -> "casaegiardino")."""
    return (a.get("categoria") or "").lower().replace(" ", "")


def _hashtag_promo(a: dict) -> str:
    """Gli hashtag in coda al post: la categoria (se c'e') e sempre
    #barattolo."""
    slug = _slug_categoria(a)
    return (f"#{slug} " if slug else "") + "#barattolo"


def _nota_promo(a: dict, cambio: float) -> str:
    """Il testo della nota Nostr kind-1: una riga di fatto, la zona
    col 📍, l'immagine come URL su una riga sua (i client la mostrano
    inline), il link e gli hashtag in coda."""
    testo = f"🫙 Nuovo nel barattolo: {a['titolo']} — {_prezzo_promo(a, cambio)}"
    if a.get("zona"):
        testo += f"\n📍 {a['zona']}"
    foto = _foto_url_nostr(a.get("foto", ""))
    if foto:
        testo += f"\n\n{foto[0]}"
    testo += f"\n{URL_PUBBLICO}/annuncio/{a['id']}"
    testo += f"\n\n{_hashtag_promo(a)}"
    return testo


def _caption_canale(a: dict, cambio: float, venduto: bool = False) -> str:
    """La caption HTML del post nel canale Telegram (usata anche per
    RICOSTRUIRE il testo quando si edita col ✅ Venduto: cosi' non
    serve salvarlo da nessuna parte)."""
    testo = f"🫙 <b>{html.escape(a['titolo'])}</b>\n{_prezzo_promo(a, cambio)}"
    if a.get("zona"):
        testo += f"\n📍 {html.escape(a['zona'])}"
    testo += f"\n{URL_PUBBLICO}/annuncio/{a['id']}"
    testo += f"\n\n{_hashtag_promo(a)}"
    if venduto:
        testo += "\n\n✅ Venduto"
    return testo


def accoda_promo(annuncio_id: int):
    """Mette l'annuncio in coda per i post automatici e, se dorme,
    sveglia il drenatore. Leggera e sincrona: si chiama DOPO il commit,
    mai dentro una transazione."""
    global _drenatore_promo_avviato
    if not POST_AUTOMATICI:
        return
    CODA_PROMO.append(annuncio_id)
    if not _drenatore_promo_avviato:
        _drenatore_promo_avviato = True
        asyncio.create_task(_drena_promo())


async def _drena_promo():
    """Il drenatore: dorme la finestra di raggruppamento, prende TUTTO
    quel che si e' accumulato e applica la regola unica — post singoli
    se sono pochi e il budget orario regge, un solo aggregato
    altrimenti. Rilegge ogni annuncio dal database: chi e' stato
    venduto o rimosso durante l'attesa non viene mai annunciato."""
    global _drenatore_promo_avviato
    await asyncio.sleep(ATTESA_RAGGRUPPO)
    ids = list(dict.fromkeys(CODA_PROMO))   # senza doppioni, in ordine
    CODA_PROMO.clear()
    _drenatore_promo_avviato = False   # chi arriva ora fa un giro nuovo
    try:
        annunci = []
        con = db()
        for i in ids:
            a = con.execute("SELECT * FROM annunci WHERE id=?",
                            (i,)).fetchone()
            if a and a["stato"] == "attivo" and not a["contatto_nostr"]:
                annunci.append(dict(a))
        con.close()
        if not annunci:
            return
        adesso = time.time()
        _post_promo_recenti[:] = [t for t in _post_promo_recenti
                                  if adesso - t < 3600]
        if (len(annunci) <= SOGLIA_AGGREGA and
                len(_post_promo_recenti) + len(annunci) <= POST_MAX_ORA):
            for a in annunci:
                await _posta_promo_singolo(a)
                _post_promo_recenti.append(time.time())
                await asyncio.sleep(PAUSA_TRA_PROMO)
        else:
            # La valvola anti-spam: un solo post, passa sempre (non
            # puo' spammare — al massimo uno a finestra, e solo se
            # qualcuno pubblica davvero).
            await _posta_promo_aggregato(len(annunci))
    except Exception as e:
        print(f"⚠️ Post automatici saltati: {e}")


async def _posta_promo_singolo(a: dict):
    """Un annuncio, un post per canale. Ogni canale fallisce per conto
    suo; i riferimenti (message_id, event id) si salvano per il ciclo
    di vita (✅ Venduto, cancellazione)."""
    cambio = await cambio_btc_eur()
    post_nostr_id, post_canale_id = "", 0
    if _NOSTR:
        try:
            tags = [["t", "barattolo"]]
            if _slug_categoria(a):
                tags.append(["t", _slug_categoria(a)])
            evento = firma_evento(1, tags, _nota_promo(a, cambio))
            if await _spedisci_ai_relay(evento):
                post_nostr_id = evento["id"]
        except Exception as e:
            print(f"⚠️ Nota promo Nostr #{a['id']} saltata: {e}")
    if TELEGRAM_CANALE_ID:
        caption = _caption_canale(a, cambio)
        foto = _foto_url_nostr(a.get("foto", ""))
        r = None
        if foto:
            r = await bot_api("sendPhoto", {
                "chat_id": TELEGRAM_CANALE_ID, "photo": foto[0],
                "caption": caption, "parse_mode": "HTML"})
        if not (r and r.get("ok")):
            r = await bot_api("sendMessage", {
                "chat_id": TELEGRAM_CANALE_ID, "text": caption,
                "parse_mode": "HTML"})
        if r and r.get("ok"):
            post_canale_id = r["result"]["message_id"]
    if post_nostr_id or post_canale_id:
        con = db()
        con.execute(
            "UPDATE annunci SET post_nostr_id=?, post_canale_id=? "
            "WHERE id=?", (post_nostr_id, post_canale_id, a["id"]))
        con.commit()
        con.close()


async def _posta_promo_aggregato(n: int):
    """Il post valvola delle raffiche: niente nomi, solo il conto e il
    link alla vetrina. Nessun ciclo di vita (non nomina nessuno)."""
    conto = "1 nuovo annuncio" if n == 1 else f"{n} nuovi annunci"
    testo = f"📦 {conto} nel barattolo → {URL_PUBBLICO}"
    if _NOSTR:
        try:
            await _spedisci_ai_relay(
                firma_evento(1, [["t", "barattolo"]], testo))
        except Exception as e:
            print(f"⚠️ Nota promo aggregata saltata: {e}")
    if TELEGRAM_CANALE_ID:
        await bot_api("sendMessage",
                      {"chat_id": TELEGRAM_CANALE_ID, "text": testo})


# ---------- IL CAMPANELLO DEI NUOVI ISCRITTI (solo moderatori) -------
# In rodaggio ogni persona che entra e' una notizia. La ricevono i
# moderatori nel loro Telegram e SOLO loro: il nome di chi si iscrive
# non si annuncia in piazza, e anche i traguardi (100 pionieri!) sono
# roba da annunciare a mano, quando e come si vuole.
# Niente coda in memoria come i post: qui il filo dell'acqua e' la
# colonna `registrato`, e a ogni giro d'orologio si guarda chi e'
# arrivato da quando abbiamo guardato l'ultima volta. Cosi' il
# campanello copre da solo TUTTE le porte d'ingresso — Mini App, login
# web, nativo Nostr, /start del bot — comprese quelle di domani, senza
# un gancio dentro l'autenticazione. Un riavvio salta un battito e
# riparte da adesso: mai una raffica di recuperi all'avvio.
# La finestra di raggruppamento e' il giro dell'orologio (10 minuti).

_ultimo_giro_iscritti = 0.0             # filo dell'acqua (0 = da armare)
_iscritti_annunciati: list[float] = []  # timestamp dei messaggi singoli
TRAGUARDI_PIONIERI = (50, 100, 250, 500, 1000)


def _riga_pioniere(u: dict) -> str:
    """Chi e' arrivato, in una riga: il nome, l'eventuale @username e
    la porta da cui e' entrato (i tg_id negativi sono i nativi Nostr).
    Il nome lo scrive l'utente: passa da html.escape, che le notifiche
    viaggiano in parse_mode HTML."""
    nome = html.escape(u["nome"] or "senza nome")
    if u["tg_id"] < 0:
        return f"{nome} — da Nostr"
    if u["username"]:
        return f"{nome} (@{html.escape(u['username'])}) — da Telegram"
    return f"{nome} — da Telegram"


async def avvisa_nuovi_iscritti():
    """Un giro d'orologio: pochi arrivi = un messaggio ciascuno, con
    nome e provenienza; una raffica (il link finito in un gruppo) = UN
    messaggio solo col conto, che non nomina nessuno — la valvola del
    drenatore promo, stessa soglia. Fail-open: la chiama l'orologio, e
    un campanello muto non deve mai fermare gli sblocchi."""
    global _ultimo_giro_iscritti
    if not AVVISI_ISCRITTI:
        return
    adesso = time.time()
    if not _ultimo_giro_iscritti:
        _ultimo_giro_iscritti = adesso     # primo giro: si arma e basta
        return
    con = db()
    nuovi = [dict(r) for r in con.execute(
        "SELECT tg_id, nome, username FROM utenti "
        "WHERE registrato >= ? AND registrato < ? "
        "ORDER BY registrato, tg_id",
        (int(_ultimo_giro_iscritti), int(adesso)))]
    # Il conto lo rifacciamo qui e non con conta_pionieri(): la sua
    # cache di un minuto potrebbe non vedere ancora chi stiamo
    # annunciando, e «siamo in 24» mentre presenti il 25° e' una bugia.
    totale = con.execute("SELECT COUNT(*) AS n FROM utenti").fetchone()["n"]
    con.close()
    _ultimo_giro_iscritti = adesso
    if not nuovi:
        return
    # I traguardi scattano solo nel giro in cui il numero li supera: si
    # deducono dai dati, nessuno stato da tenere (e se una fusione
    # cancella una riga proprio in quel giro, il traguardo salta — pace,
    # il numero vero resta quello del contatore in vetrina).
    prima = totale - len(nuovi)
    for soglia in TRAGUARDI_PIONIERI:
        if prima < soglia <= totale:
            await notifica_admin(f"🎉 <b>Traguardo: {soglia} pionieri!</b>\n"
                                 f"Il barattolo si riempie. 🫙")
    # Il tetto orario vale sui messaggi SINGOLI; oltre resta
    # l'aggregato, che passa sempre (al massimo uno per giro, e solo se
    # qualcuno e' davvero arrivato).
    _iscritti_annunciati[:] = [t for t in _iscritti_annunciati
                               if adesso - t < 3600]
    if (len(nuovi) <= SOGLIA_AGGREGA
            and len(_iscritti_annunciati) + len(nuovi) <= AVVISI_ISCRITTI_MAX_ORA):
        for u in nuovi:
            await notifica_admin(f"👥 <b>Nuovo pioniere:</b> {_riga_pioniere(u)}\n"
                                 f"Siamo in {totale}.")
            _iscritti_annunciati.append(time.time())
    else:
        conto = ("1 nuovo pioniere" if len(nuovi) == 1
                 else f"{len(nuovi)} nuovi pionieri")
        await notifica_admin(f"👥 <b>{conto}</b> negli ultimi minuti.\n"
                             f"Siamo in {totale}.")


# --- Il motore degli avvisi di ricerca -------------------------------
# Gemello della coda promo qui sopra: chi pubblica accoda e basta, il
# drenatore dorme la stessa finestra e poi confronta gli annunci nuovi
# coi criteri salvati. Anti-molestia a tre strati: dedup persistente
# (avvisi_notificati: lo stesso annuncio non suona mai due volte per lo
# stesso utente, nemmeno dopo un riavvio), aggregazione (2+ match in
# finestra = UN solo messaggio: l'import da 500 righe non mitraglia
# nessuno) e tetto giornaliero di messaggi per utente (in memoria: un
# riavvio lo azzera, al peggio qualche messaggio in piu' una tantum —
# le raffiche vere le ferma l'aggregazione, che e' strutturale).
# A differenza dei promo, gli annunci IMPORTATI restano dentro: per
# chi cerca, un annuncio e' un annuncio.

CODA_MATCH: list[int] = []
_drenatore_match_avviato = False
TETTO_AVVISI_GIORNO = 3 if MODALITA_COLLAUDO else 5   # messaggi/giorno
AVVISI_QUOTA: dict[int, list] = {}    # tg_id -> [giorno, messaggi]


def accoda_match(annuncio_id: int):
    """Mette l'annuncio in coda per il matching degli avvisi e, se
    dorme, sveglia il drenatore. Come accoda_promo: leggera e
    sincrona, DOPO il commit, mai dentro una transazione."""
    global _drenatore_match_avviato
    CODA_MATCH.append(annuncio_id)
    if not _drenatore_match_avviato:
        _drenatore_match_avviato = True
        asyncio.create_task(_drena_match())


def _match_avviso(avviso, a: dict, token_annuncio: list,
                  cambio: float) -> bool:
    """La verifica fine, dopo il prefiltro SQL (categoria e prezzo in
    sats sono gia' passati): parole chiave, prezzo in EUR, distanza.
    Ogni criterio non impostato lascia passare."""
    # parole chiave: TUTTE (e' un AND), a prefisso di parola — 'bici'
    # prende 'bicicletta', ma 'ram' non affoga in 'ceramica'
    for parola in avviso["parole"].split():
        if not any(t.startswith(parola) for t in token_annuncio):
            return False
    # prezzo massimo in EUR: il listino EUR si confronta com'e', il
    # listino sats si converte col cambio di adesso; cambio mai
    # arrivato = criterio non valutabile = niente avviso (meglio un
    # match perso che uno sbagliato)
    if avviso["prezzo_max_eur"]:
        if a.get("valuta") == "eur" and a.get("prezzo_eur"):
            eur = a["prezzo_eur"]
        elif cambio > 0:
            eur = a["prezzo_sats"] / 100_000_000 * cambio
        else:
            return False
        if eur > avviso["prezzo_max_eur"]:
            return False
    # raggio: un annuncio senza coordinate (zona non riconosciuta)
    # non matcha mai i criteri geografici — imperfezione dichiarata
    if avviso["raggio_km"]:
        if not (a.get("lat") or a.get("lon")):
            return False
        if distanza_km(avviso["lat"], avviso["lon"],
                       a["lat"], a["lon"]) > avviso["raggio_km"]:
            return False
    return True


async def _drena_match():
    """Il drenatore del matching: dorme la finestra, rilegge gli
    annunci accumulati dal database (chi e' sparito nel frattempo non
    suona) e confronta ciascuno coi criteri salvati — prefiltro SQL
    sulla tabella minuscola degli avvisi, verifica fine in Python.
    Fail-open totale: un errore qui non tocca mai la pubblicazione."""
    global _drenatore_match_avviato
    await asyncio.sleep(ATTESA_RAGGRUPPO)
    ids = list(dict.fromkeys(CODA_MATCH))
    CODA_MATCH.clear()
    _drenatore_match_avviato = False
    try:
        cambio = await cambio_btc_eur()
        per_utente: dict[int, list] = {}
        con = db()
        for i in ids:
            a = con.execute("SELECT * FROM annunci WHERE id=?",
                            (i,)).fetchone()
            if not a or a["stato"] != "attivo":
                continue
            a = dict(a)
            token = normalizza(f"{a['titolo']} {a['descrizione']}").split()
            candidati = con.execute(
                "SELECT * FROM avvisi_ricerca WHERE attivo=1 "
                "AND tg_id != ? "
                "AND (categorie='' OR categorie LIKE '%|' || ? || '|%') "
                "AND (prezzo_max_sats=0 OR prezzo_max_sats >= ?)",
                (a["venditore_id"], a["categoria"],
                 a["prezzo_sats"])).fetchall()
            gia_suoi = set()
            for avviso in candidati:
                if avviso["tg_id"] in gia_suoi:   # un utente, una voce
                    continue
                if _match_avviso(avviso, a, token, cambio):
                    gia_suoi.add(avviso["tg_id"])
                    per_utente.setdefault(avviso["tg_id"], []).append(a)
        # dedup persistente: conta solo chi entra DAVVERO adesso
        adesso = int(time.time())
        da_avvisare: dict[int, list] = {}
        for tg_id, annunci in per_utente.items():
            nuovi = []
            for a in annunci:
                cur = con.execute(
                    "INSERT OR IGNORE INTO avvisi_notificati"
                    "(tg_id, annuncio_id, creato) VALUES(?,?,?)",
                    (tg_id, a["id"], adesso))
                if cur.rowcount:
                    nuovi.append(a)
            if nuovi:
                da_avvisare[tg_id] = nuovi
        con.commit()
        con.close()
        for tg_id, annunci in da_avvisare.items():
            await _notifica_match(tg_id, annunci, cambio)
            await asyncio.sleep(0.2)   # mai raffiche sull'API Telegram
    except Exception as e:
        print(f"⚠️ Matching avvisi saltato: {e}")


async def _notifica_match(tg_id: int, annunci: list, cambio: float):
    """Il messaggio all'utente: uno solo per finestra — ricco se il
    match e' singolo, il conto e basta se sono di piu'. Il tetto
    giornaliero chiude con onesta', mai in silenzio muto."""
    oggi = time.strftime("%Y-%m-%d")
    voce = AVVISI_QUOTA.get(tg_id)
    if not voce or voce[0] != oggi:
        voce = [oggi, 0]
        AVVISI_QUOTA[tg_id] = voce
    if voce[1] >= TETTO_AVVISI_GIORNO:
        return
    if len(annunci) == 1:
        a = annunci[0]
        testo = (f"🔎 Un annuncio fa per te!\n"
                 f"<b>{html.escape(a['titolo'])}</b> — "
                 f"{_prezzo_promo(a, cambio)}")
        if a.get("zona"):
            testo += f"\n📍 {html.escape(a['zona'])}"
        testo += f"\n{URL_PUBBLICO}/annuncio/{a['id']}"
    else:
        testo = (f"📬 {len(annunci)} nuovi annunci corrispondono ai "
                 f"tuoi avvisi di ricerca → {URL_PUBBLICO}")
    voce[1] += 1
    if voce[1] >= TETTO_AVVISI_GIORNO:
        testo += ("\n\n(per oggi mi fermo qui 🤫: il resto lo "
                  "trovi nel mercatino)")
    await notifica(tg_id, testo)


def pulisci_avvisi():
    """La scopa degli avvisi, chiamata dall'orologio: via le righe di
    dedup piu' vecchie di 30 giorni (un annuncio non rinasce dopo un
    mese) e i contatori dei giorni passati."""
    try:
        con = db()
        con.execute("DELETE FROM avvisi_notificati WHERE creato < ?",
                    (int(time.time()) - 30 * 86400,))
        con.commit()
        con.close()
    except Exception as e:
        print(f"⚠️ Pulizia avvisi saltata: {e}")
    oggi = time.strftime("%Y-%m-%d")
    for tg_id in [t for t, v in AVVISI_QUOTA.items() if v[0] != oggi]:
        AVVISI_QUOTA.pop(tg_id, None)


# ------------------- offerta lampo: «ha fatto colpo» -----------------
# Quando qualcuno mette un annuncio nel suo barattolo, il VENDITORE
# riceve un avviso ANONIMO («qualcuno», mai chi ne' quanti: i preferiti
# restano privati per natura) con l'invito a lanciare un'offerta lampo.
# Stessa valvola dei post promo: finestra di raggruppamento, rilettura
# dal DB, aggregato oltre la soglia. In piu' un cooldown PER ANNUNCIO
# (GIORNI_COLPO, colonna lampo_colpo_avvisato): dieci salvataggi in una
# settimana = un solo avviso, l'entusiasmo non deve diventare molestia.

CODA_COLPO: list[int] = []       # annunci appena messi nel barattolo
_drenatore_colpo_avviato = False


def accoda_colpo(annuncio_id: int):
    """Mette l'annuncio in coda per l'avviso «ha fatto colpo» e, se
    dorme, sveglia il drenatore. Leggera e sincrona: si chiama DOPO il
    commit del salvataggio, mai dentro la transazione."""
    global _drenatore_colpo_avviato
    if not LAMPO_ATTIVE:
        return
    CODA_COLPO.append(annuncio_id)
    if not _drenatore_colpo_avviato:
        _drenatore_colpo_avviato = True
        asyncio.create_task(_drena_colpo())


async def _drena_colpo():
    """Il drenatore: dorme la finestra, rilegge ogni annuncio dal DB
    (spariti, importati, in cooldown o gia' in lampo = muti), raggruppa
    per venditore e applica la regola di sempre — un messaggio per
    annuncio fino alla soglia, un solo aggregato oltre. Il timbro del
    cooldown si scrive PRIMA di notificare (il pattern dei commit)."""
    global _drenatore_colpo_avviato
    await asyncio.sleep(ATTESA_RAGGRUPPO)
    ids = list(dict.fromkeys(CODA_COLPO))
    CODA_COLPO.clear()
    _drenatore_colpo_avviato = False   # chi arriva ora fa un giro nuovo
    try:
        adesso = int(time.time())
        per_venditore: dict[int, list] = {}
        con = db()
        for i in ids:
            a = con.execute("SELECT * FROM annunci WHERE id=?",
                            (i,)).fetchone()
            if (not a or a["stato"] != "attivo"
                    or a["lampo_scadenza"] > adesso   # lampo gia' in corso
                    or adesso - a["lampo_colpo_avvisato"]
                        < GIORNI_COLPO * 86400):
                continue
            per_venditore.setdefault(a["venditore_id"], []).append(dict(a))
        # Il timbro del cooldown prima delle notifiche: se una notifica
        # inciampa, meglio un avviso perso che uno ripetuto.
        for annunci in per_venditore.values():
            for a in annunci:
                con.execute("UPDATE annunci SET lampo_colpo_avvisato=? "
                            "WHERE id=?", (adesso, a["id"]))
        con.commit()
        con.close()
        for venditore, annunci in per_venditore.items():
            if len(annunci) <= SOGLIA_AGGREGA:
                for a in annunci:
                    await notifica(venditore, (
                        f"🫙 Il tuo annuncio ha fatto colpo!\n"
                        f"<b>{html.escape(a['titolo'])}</b>: qualcuno "
                        f"l'ha appena messo nel suo barattolo.\n"
                        f"💰 Se vuoi dargli una spinta, lancia "
                        f"un'offerta lampo dalla scheda dell'annuncio:\n"
                        f"{URL_PUBBLICO}/annuncio/{a['id']}"))
            else:
                # La valvola: un solo messaggio, non nomina nessuno.
                await notifica(venditore, (
                    f"🫙 {len(annunci)} tuoi annunci hanno fatto colpo: "
                    f"qualcuno li ha messi nel suo barattolo.\n"
                    f"💰 Dalle loro schede puoi lanciare un'offerta "
                    f"lampo → {URL_PUBBLICO}"))
            await asyncio.sleep(0.2)
    except Exception as e:
        print(f"⚠️ Avviso «ha fatto colpo» saltato: {e}")


# Il ciclo di vita agisce solo su post GIA' fatti (le colonne piene):
# per questo non guarda la leva POST_AUTOMATICI — un post esistente va
# tenuto vero (o tolto) anche se nel frattempo la leva e' stata spenta.

async def promo_venduto(annuncio_id: int, venduto: bool = True):
    """L'annuncio e' stato venduto: il post nel canale si aggiorna col
    ✅ Venduto. La nota Nostr resta com'e': e' storia vera. Con
    venduto=False fa il viaggio inverso (rimborso: l'oggetto torna in
    vetrina e il post non deve mentire)."""
    try:
        con = db()
        a = con.execute("SELECT * FROM annunci WHERE id=?",
                        (annuncio_id,)).fetchone()
        con.close()
        if not a or not a["post_canale_id"] or not TELEGRAM_CANALE_ID:
            return
        caption = _caption_canale(dict(a), await cambio_btc_eur(),
                                  venduto=venduto)
        dati = {"chat_id": TELEGRAM_CANALE_ID,
                "message_id": a["post_canale_id"], "parse_mode": "HTML"}
        # Con la foto il testo vive nella caption, senza nel body — ma
        # il ripiego sendMessage di _posta_promo_singolo rende il tipo
        # ambiguo: si tenta il piu' probabile e poi l'altro.
        campo = {"editMessageCaption": "caption", "editMessageText": "text"}
        tentativi = (["editMessageCaption", "editMessageText"]
                     if _foto_url_nostr(a["foto"])
                     else ["editMessageText", "editMessageCaption"])
        for metodo in tentativi:
            r = await bot_api(metodo, {**dati, campo[metodo]: caption})
            if r and r.get("ok"):
                break
    except Exception as e:
        print(f"⚠️ Aggiornamento post venduto #{annuncio_id} saltato: {e}")


async def promo_rimuovi(annuncio_id: int):
    """L'annuncio e' sparito dalla vetrina: il post nel canale si
    cancella e la nota Nostr riceve la sua NIP-09 (fail-open: se un
    relay la ignora, pazienza — la nota non mente, l'annuncio c'era)."""
    try:
        con = db()
        a = con.execute(
            "SELECT post_canale_id, post_nostr_id, foto FROM annunci "
            "WHERE id=?", (annuncio_id,)).fetchone()
        con.close()
        if not a or not (a["post_canale_id"] or a["post_nostr_id"]):
            return
        if a["post_canale_id"] and TELEGRAM_CANALE_ID:
            await bot_api("deleteMessage",
                          {"chat_id": TELEGRAM_CANALE_ID,
                           "message_id": a["post_canale_id"]})
        if a["post_nostr_id"] and _NOSTR:
            await _spedisci_ai_relay(
                firma_evento(5, [["e", a["post_nostr_id"]], ["k", "1"]],
                             "Annuncio rimosso da Barattolo"))
        con = db()
        con.execute("UPDATE annunci SET post_canale_id=0, "
                    "post_nostr_id='' WHERE id=?", (annuncio_id,))
        con.commit()
        con.close()
    except Exception as e:
        print(f"⚠️ Ritiro post automatici #{annuncio_id} saltato: {e}")


@app.post("/api/orders/{ordine_id}/invoice")
async def deposita_invoice(ordine_id: int, req: Request,
                           x_tg_init_data: str = Header(""),
                           barattolo_sessione: str = Cookie("")):
    """Deposita una invoice Lightning sull'ordine:
    - il VENDITORE (stati locked/shipped/confirmed) per incassare:
      importo = prezzo - commissione; se l'acquirente aveva gia'
      confermato, i sats partono immediatamente
    - l'ACQUIRENTE (stato refund, disputa vinta) per il rimborso:
      importo = prezzo pieno; il rimborso parte immediatamente."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    bolt11 = (d.get("invoice") or "").strip()
    if not bolt11.lower().startswith("ln"):
        raise HTTPException(400, "Questa non sembra una invoice Lightning")

    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
    if o and o["venditore_id"] == user["id"] \
            and o["stato"] in ("locked", "shipped", "confirmed"):
        # L'incasso del venditore: il totale meno la protezione (che
        # resta alla piattaforma), cioe' articolo + spedizione.
        ruolo, atteso, colonna = "venditore", \
            netto_venditore(o["prezzo_sats"] - o["protezione_sats"]), \
            "invoice_venditore"
        spiegazione = f"{atteso} sats (il tuo incasso)"
    elif o and o["compratore_id"] == user["id"] and o["stato"] == "refund":
        ruolo, atteso, colonna = "compratore", o["prezzo_sats"], "invoice_rimborso"
        spiegazione = f"{atteso} sats (rimborso integrale)"
    else:
        con.close()
        raise HTTPException(400, "Operazione non permessa")

    dec = await decodifica_invoice(bolt11)
    if dec is None:
        con.close()
        raise HTTPException(400, "Invoice non valida o illeggibile")
    importo_sats = int(dec.get("amount_msat", 0)) // 1000
    if importo_sats != atteso:
        con.close()
        raise HTTPException(400,
            f"Importo sbagliato: la invoice e' di {importo_sats} sats, "
            f"deve essere esattamente {spiegazione}")

    con.execute(f"UPDATE ordini SET {colonna}=?, aggiornato=? WHERE id=?",
                (bolt11, int(time.time()), ordine_id))
    con.commit()
    con.close()

    if ruolo == "compratore":                      # rimborso: parte subito
        return await _rimborsa_compratore(ordine_id)
    if o["stato"] == "confirmed":                  # incasso: parte subito
        return await _sblocca_sats(ordine_id)
    return {"ok": True, "stato": o["stato"], "netto": atteso}


# Un lucchetto per ordine: sblocco e rimborso MUOVONO FONDI e possono
# partire insieme da strade diverse (orologio, conferma dell'acquirente,
# invoice appena depositata). Il server e' un processo solo: il lucchetto
# asyncio mette le chiamate in fila, e la guardia sullo stato fa uscire
# a mani vuote chi arriva a cose gia' fatte. Senza, due invoice diverse
# (via Lightning address) potrebbero essere pagate entrambe.
_lucchetti_ordine = defaultdict(asyncio.Lock)


async def _sblocca_sats(ordine_id: int, automatico: bool = False) -> dict:
    """Consegna i sats al venditore, provando in ordine:
    1. la invoice che il venditore ha eventualmente depositato
    2. INCASSO AUTOMATICO: il suo Lightning address (se impostato)
    3. altrimenti l'ordine resta 'confirmed' e il venditore viene
       avvisato di fornire una invoice o impostare il suo address.
    Se un pagamento fallisce (es. invoice scaduta), i sats restano
    al sicuro in cassaforte e si riprova con metodo nuovo."""
    async with _lucchetti_ordine[ordine_id]:
        con = db()
        o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
        if not o:
            con.close()
            return {"ok": False, "stato": "?"}
        if o["stato"] in ("released", "refunded", "refund", "creato", "annullato"):
            con.close()          # gia' risolto (o mai pagato): niente doppioni
            return {"ok": o["stato"] == "released", "stato": o["stato"]}
        v = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                        (o["venditore_id"],)).fetchone()
        # Al venditore va articolo + spedizione: la protezione del
        # compratore resta in cassaforte, alla piattaforma. Sugli
        # ordini di ieri la quota e' 0 e non cambia nulla.
        netto = netto_venditore(o["prezzo_sats"] - o["protezione_sats"])

        bolt11 = o["invoice_venditore"]
        if not bolt11 and v and v["ln_address"]:
            bolt11 = await invoice_da_ln_address(v["ln_address"], netto)

        if bolt11 and await paga_venditore(bolt11):
            t = con.execute("SELECT titolo FROM annunci WHERE id=?",
                            (o["annuncio_id"],)).fetchone()
            titolo = t["titolo"] if t else "il tuo acquisto"
            cambio = await cambio_btc_eur()
            con.execute("UPDATE ordini SET stato='released', cambio_eur=?, "
                        "aggiornato=? WHERE id=?",
                        (cambio, int(time.time()), ordine_id))
            con.execute("UPDATE utenti SET vendite_ok=vendite_ok+1 WHERE tg_id=?",
                        (o["venditore_id"],))
            con.execute("UPDATE utenti SET acquisti_ok=acquisti_ok+1 WHERE tg_id=?",
                        (o["compratore_id"],))
            con.commit()
            con.close()
            invito = ("⭐ Com'è andata? Apri l'ordine nella Mini App "
                      "e lascia un feedback.")
            if automatico:
                await notifica(o["venditore_id"],
                               f"🔓 <b>Sats sbloccati automaticamente!</b> Il tempo di "
                               f"conferma è scaduto senza problemi segnalati: "
                               f"<b>{netto} sats</b> sono in arrivo nel tuo wallet. ⚡ "
                               f"{invito}")
                await notifica(o["compratore_id"],
                               f"✅ <b>Affare concluso:</b> «{titolo}». Il tempo per "
                               f"confermare o aprire una disputa è scaduto e i sats "
                               f"sono stati sbloccati al venditore. Grazie per aver "
                               f"usato Barattolo 🫙 {invito}")
            elif o["disputata"]:
                # Lo sblocco arriva da una disputa decisa al venditore:
                # il messaggio dice la verita', non «ha confermato».
                await notifica(o["venditore_id"],
                               f"⚖️ <b>La disputa è stata decisa a tuo favore:</b> "
                               f"<b>{netto} sats</b> sono in arrivo nel tuo wallet. "
                               f"Affare concluso! ⚡ {invito}")
                await notifica(o["compratore_id"],
                               f"⚖️ <b>La disputa su «{titolo}» è stata decisa a "
                               f"favore del venditore:</b> i sats gli sono stati "
                               f"sbloccati. {invito}")
            else:
                await notifica(o["venditore_id"],
                               f"🔓 <b>Sats sbloccati!</b> L'acquirente ha confermato la "
                               f"ricezione: <b>{netto} sats</b> sono in arrivo nel tuo "
                               f"wallet. Affare concluso! ⚡ {invito}")
                await notifica(o["compratore_id"],
                               f"✅ <b>Affare concluso:</b> «{titolo}». "
                               f"Grazie per aver usato Barattolo 🫙 {invito}")
            # Un affare concluso puo' far scattare distintivi a
            # ENTRAMBE le parti (primo baratto, primo acquisto...)
            await premia_distintivi(o["venditore_id"])
            await premia_distintivi(o["compratore_id"])
            # Il polso dei moderatori: ordine chiuso, sats consegnati
            if o["disputata"]:
                await polso_ordini_admin(
                    f"⚖️ <b>Disputa chiusa a favore del venditore:</b> "
                    f"«{titolo[:60]}» — {netto} sats sbloccati. "
                    f"Restano {{aperti}} ordini aperti.")
            else:
                await polso_ordini_admin(
                    f"✅ <b>Ordine concluso:</b> «{titolo[:60]}» — {netto} "
                    f"sats al venditore. Restano {{aperti}} ordini aperti.")
            return {"ok": True, "stato": "released"}

        # Niente pagamento riuscito: l'ordine resta/va in 'confirmed',
        # la invoice (se c'era) viene ripulita, il venditore avvisato.
        con.execute("UPDATE ordini SET invoice_venditore='', stato='confirmed', "
                    "aggiornato=? WHERE id=?", (int(time.time()), ordine_id))
        con.commit()
        con.close()
        if o["invoice_venditore"] or (v and v["ln_address"]):
            msg = ("⚠️ Il pagamento automatico dei tuoi sats e' <b>fallito</b> "
                   "(invoice scaduta o wallet non raggiungibile). I sats sono al "
                   "sicuro nel deposito di garanzia: apri l'ordine nella Mini App "
                   "per riprovare "
                   f"con una invoice da <b>{netto} sats</b>.")
        else:
            testa = ("⚖️ <b>La disputa è stata decisa a tuo favore!</b>"
                     if o["disputata"] else
                     "✅ <b>L'acquirente ha confermato la ricezione!</b>")
            msg = (f"{testa} Per incassare "
                   f"i tuoi <b>{netto} sats</b>: apri l'ordine nella Mini App e "
                   f"imposta il tuo Lightning address (incassi automatici, per "
                   f"sempre) oppure incolla una invoice di esattamente quell'importo. 💰")
        await notifica(o["venditore_id"], msg)
        return {"ok": False, "stato": "confirmed"}


async def _rimborsa_compratore(ordine_id: int) -> dict:
    """Rimborsa integralmente l'acquirente (disputa decisa a suo
    favore), provando: 1. la sua invoice di rimborso, 2. il suo
    Lightning address. Se non c'e' un metodo, l'ordine va in 'refund'
    e l'acquirente viene invitato a fornirne uno nella Mini App.
    L'annuncio torna in vetrina."""
    async with _lucchetti_ordine[ordine_id]:
        con = db()
        o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
        if not o:
            con.close()
            return {"ok": False, "stato": "?"}
        if o["stato"] in ("refunded", "released", "creato", "annullato"):
            con.close()          # gia' risolto (o mai pagato): niente doppioni
            return {"ok": o["stato"] == "refunded", "stato": o["stato"]}
        c_utente = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                               (o["compratore_id"],)).fetchone()
        # Rimborso integrale: articolo, spedizione e protezione tornano
        # tutti al compratore (l'affare e' saltato, la protezione non
        # si e' consumata) — e' il totale, zero commissioni.
        importo = o["prezzo_sats"]

        bolt11 = o["invoice_rimborso"]
        if not bolt11 and c_utente and c_utente["ln_address"]:
            bolt11 = await invoice_da_ln_address(c_utente["ln_address"], importo)

        if bolt11 and await paga_venditore(bolt11):
            cambio = await cambio_btc_eur()
            con.execute("UPDATE ordini SET stato='refunded', cambio_eur=?, "
                        "aggiornato=? WHERE id=?",
                        (cambio, int(time.time()), ordine_id))
            con.execute("UPDATE annunci SET stato='attivo' WHERE id=?",
                        (o["annuncio_id"],))      # l'oggetto torna in vetrina
            con.commit()
            t = con.execute("SELECT titolo FROM annunci WHERE id=?",
                            (o["annuncio_id"],)).fetchone()
            titolo = (t["titolo"] if t else "?")[:60]
            con.close()
            # ...e torna disponibile anche sulla piazza Nostr
            asyncio.create_task(annuncio_su_nostr(o["annuncio_id"], "active",
                                                  solo_aggiornamento=True))
            # ...e il post nel canale toglie il ✅ Venduto: l'oggetto
            # e' di nuovo in vetrina, il post non deve mentire
            asyncio.create_task(promo_venduto(o["annuncio_id"],
                                              venduto=False))
            await notifica(o["compratore_id"],
                           f"↩️ <b>Disputa risolta a tuo favore:</b> il rimborso di "
                           f"<b>{importo} sats</b> è in arrivo nel tuo wallet. "
                           f"⭐ Com'è andata? Apri l'ordine nella Mini App e "
                           f"lascia un feedback.")
            await notifica(o["venditore_id"],
                           "⚖️ La disputa è stata risolta a favore dell'acquirente: "
                           "i sats gli sono stati rimborsati e l'annuncio è tornato "
                           "in vetrina. ⭐ Puoi lasciare un feedback dall'ordine "
                           "nella Mini App.")
            # Il polso dei moderatori: anche gli esiti storti contano
            await polso_ordini_admin(
                f"↩️ <b>Ordine rimborsato al compratore:</b> «{titolo}» — "
                f"{importo} sats. Restano {{aperti}} ordini aperti.")
            return {"ok": True, "stato": "refunded"}

        # Nessun metodo di rimborso disponibile: si mette in attesa
        con.execute("UPDATE ordini SET invoice_rimborso='', stato='refund', "
                    "aggiornato=? WHERE id=?", (int(time.time()), ordine_id))
        con.commit()
        con.close()
        await notifica(o["compratore_id"],
                       f"⚖️ <b>Disputa risolta a tuo favore!</b> Per ricevere il "
                       f"rimborso di <b>{importo} sats</b>: apri l'ordine nella "
                       f"Mini App e imposta il tuo Lightning address, oppure "
                       f"incolla una invoice di esattamente quell'importo.")
        return {"ok": False, "stato": "refund"}


@app.post("/api/admin/orders/{ordine_id}/risolvi")
async def risolvi_disputa(ordine_id: int, req: Request,
                          x_tg_init_data: str = Header(""),
                          barattolo_sessione: str = Cookie("")):
    """SOLO ADMIN: decide una disputa.
    - esito='venditore': i sats vanno al venditore (meno commissione)
    - esito='rimborso': rimborso immediato all'acquirente (es. oggetto
      mai arrivato)
    - esito='reso': rimborso PREVIA RESTITUZIONE: l'acquirente deve
      rispedire l'oggetto (con tracciamento); il rimborso parte solo
      quando il venditore conferma di averlo ricevuto.
    'venditore' e 'rimborso' funzionano anche come intervento d'ufficio
    su un reso che si e' incagliato."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if not e_admin(user["id"]):
        raise HTTPException(403, "Riservato ai moderatori")
    d = await leggi_json(req)
    esito = d.get("esito", "")
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND stato IN "
                    "('dispute','return_pending','return_shipped')",
                    (ordine_id,)).fetchone()
    con.close()
    if not o:
        raise HTTPException(400, "Questa disputa non esiste o è già chiusa")
    if esito == "venditore":
        return await _sblocca_sats(ordine_id)
    if esito == "rimborso":
        return await _rimborsa_compratore(ordine_id)
    if esito == "reso" and o["stato"] == "dispute":
        con = db()
        con.execute("UPDATE ordini SET stato='return_pending', aggiornato=? "
                    "WHERE id=?", (int(time.time()), ordine_id))
        con.commit()
        con.close()
        await notifica(o["compratore_id"],
                       "⚖️ <b>Disputa decisa: rimborso previa restituzione.</b> "
                       "Rispedisci l'oggetto al venditore (accordatevi in chat "
                       "per l'indirizzo) e inserisci il tracciamento del reso "
                       "nella Mini App: il rimborso partirà alla consegna.")
        await notifica(o["venditore_id"],
                       "⚖️ <b>Disputa decisa: reso.</b> L'acquirente ti "
                       "rispedirà l'oggetto; quando lo ricevi, confermalo "
                       "nella Mini App e i sats gli verranno rimborsati.")
        return {"ok": True, "stato": "return_pending"}
    raise HTTPException(400, "Esito non valido")


@app.post("/api/orders/{ordine_id}/reso-spedito")
async def reso_spedito(ordine_id: int, req: Request,
                       x_tg_init_data: str = Header(""),
                       barattolo_sessione: str = Cookie("")):
    """L'acquirente ha rispedito l'oggetto: registra il tracciamento
    del reso e avvisa il venditore."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    corriere = (d.get("corriere") or "").strip()[:40]
    tracking = (d.get("tracking") or "").strip()[:60]
    if corriere != "Consegna a mano" and not tracking:
        raise HTTPException(400, "Inserisci il numero di tracciamento del reso")
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND compratore_id=? "
                    "AND stato='return_pending'",
                    (ordine_id, user["id"])).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    con.execute("UPDATE ordini SET stato='return_shipped', corriere_reso=?, "
                "tracking_reso=?, aggiornato=? WHERE id=?",
                (corriere, tracking, int(time.time()), ordine_id))
    con.commit()
    con.close()
    dettaglio = (f"con <b>{corriere}</b>, tracciamento <b>{tracking}</b>"
                 if tracking else "in consegna a mano")
    await notifica(o["venditore_id"],
                   f"↩️ <b>Il reso è in viaggio</b> {dettaglio}. Quando ricevi "
                   f"l'oggetto, conferma nella Mini App: a quel punto "
                   f"l'acquirente verrà rimborsato.")
    return {"ok": True, "stato": "return_shipped"}


@app.post("/api/orders/{ordine_id}/reso-ricevuto")
async def reso_ricevuto(ordine_id: int, x_tg_init_data: str = Header(""),
                                        barattolo_sessione: str = Cookie("")):
    """Il venditore conferma di aver ricevuto il reso: parte il
    rimborso integrale all'acquirente."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND venditore_id=? "
                    "AND stato='return_shipped'",
                    (ordine_id, user["id"])).fetchone()
    con.close()
    if not o:
        raise HTTPException(400, "Operazione non permessa")
    return await _rimborsa_compratore(ordine_id)


@app.post("/api/orders/{ordine_id}/conferma")
async def conferma_ricezione(ordine_id: int, x_tg_init_data: str = Header(""),
                                             barattolo_sessione: str = Cookie("")):
    """L'acquirente conferma la ricezione: i sats vengono consegnati
    automaticamente al venditore (invoice depositata o Lightning
    address). Se nessun metodo e' disponibile, l'ordine va in
    'confirmed' e partiranno appena il venditore ne fornisce uno."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND compratore_id=? "
                    "AND stato IN ('locked','shipped','delivered')",
                    (ordine_id, user["id"])).fetchone()
    con.close()
    if not o:
        raise HTTPException(400, "Operazione non permessa")
    return await _sblocca_sats(ordine_id)


@app.post("/api/orders/{ordine_id}/disputa")
async def apri_disputa(ordine_id: int, x_tg_init_data: str = Header(""),
                                       barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND compratore_id=? "
                    "AND stato IN ('locked','shipped','delivered')",
                    (ordine_id, user["id"])).fetchone()
    if not o:
        raise HTTPException(400, "Operazione non permessa")
    # disputata resta 1 per sempre, anche a disputa risolta: e' la
    # memoria su cui si giudica il distintivo Specchiato
    con.execute("UPDATE ordini SET stato='dispute', disputata=1, "
                "aggiornato=? WHERE id=?",
                (int(time.time()), ordine_id))
    con.commit()
    con.close()
    for admin in ADMIN_IDS:
        await notifica(admin, f"⚠️ <b>Disputa aperta</b> sull'ordine #{ordine_id}. "
                              "I sats restano bloccati in attesa della tua decisione.")
    await notifica(o["venditore_id"],
                   "⚠️ L'acquirente ha aperto una <b>disputa</b>. Un moderatore "
                   "vi contattera' entrambi. I sats restano nel deposito "
                   "di garanzia.")
    return {"ok": True}


def pulisci_ordini_fantasma(con):
    """Elimina gli ordini MAI PAGATI piu' vecchi di 30 minuti: la loro
    invoice e' scaduta (15 min), quindi non possono piu' progredire.
    Nessun sat e' coinvolto, e' solo pulizia."""
    soglia = int(time.time()) - 1800
    # L'offerta che aveva generato l'ordine si scioglie dal legame e
    # resta 'accettata' fino alla SUA scadenza: il compratore puo'
    # riprovare a pagare con una invoice nuova.
    con.execute("UPDATE offerte SET ordine_id=0 WHERE ordine_id IN "
                "(SELECT id FROM ordini WHERE stato='creato' AND creato < ?)",
                (soglia,))
    con.execute("DELETE FROM ordini WHERE stato='creato' AND creato < ?",
                (soglia,))


@app.post("/api/orders/{ordine_id}/annulla")
async def annulla_ordine(ordine_id: int, x_tg_init_data: str = Header(""),
                                         barattolo_sessione: str = Cookie("")):
    """L'acquirente annulla un ordine non ancora pagato (nessun sat
    e' stato mosso: l'ordine sparisce e basta)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND compratore_id=? "
                    "AND stato='creato'", (ordine_id, user["id"])).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Operazione non permessa")
    # Se l'ordine veniva da un'offerta, l'offerta torna libera (resta
    # 'accettata' fino alla sua scadenza: si puo' ripagare)
    con.execute("UPDATE offerte SET ordine_id=0 WHERE ordine_id=?",
                (ordine_id,))
    con.execute("DELETE FROM ordini WHERE id=?", (ordine_id,))
    con.commit()
    con.close()
    return {"ok": True}


@app.get("/api/orders")
def miei_ordini(x_tg_init_data: str = Header(""),
                barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    pulisci_ordini_fantasma(con)
    con.commit()
    q = ("SELECT o.*, a.titolo, a.zona, "
         "uc.username AS compratore_username, "
         "uv.username AS venditore_username, "
         # il ponte Nostr verso la controparte: solo chiavi dal
         # possesso DIMOSTRATO (chiave d'accesso o badge verificato),
         # la stessa regola di notifica(). Esce solo alle parti.
         "CASE WHEN uc.npub_accesso!='' THEN uc.npub_accesso "
         "     WHEN uc.npub_verificata=1 THEN uc.npub "
         "     ELSE '' END AS compratore_nostr, "
         "CASE WHEN uv.npub_accesso!='' THEN uv.npub_accesso "
         "     WHEN uv.npub_verificata=1 THEN uv.npub "
         "     ELSE '' END AS venditore_nostr, "
         # il feedback che HO lasciato su quest'ordine e quello ricevuto
         # (per l'admin che guarda le dispute restano NULL: innocuo)
         "(SELECT voto FROM feedback WHERE ordine_id=o.id "
         " AND da_tg_id=?) AS mio_voto, "
         "(SELECT commento FROM feedback WHERE ordine_id=o.id "
         " AND da_tg_id=?) AS mio_commento, "
         "(SELECT voto FROM feedback WHERE ordine_id=o.id "
         " AND per_tg_id=?) AS suo_voto, "
         "(SELECT commento FROM feedback WHERE ordine_id=o.id "
         " AND per_tg_id=?) AS suo_commento FROM ordini o "
         "JOIN annunci a ON a.id=o.annuncio_id "
         "JOIN utenti uc ON uc.tg_id=o.compratore_id "
         "JOIN utenti uv ON uv.tg_id=o.venditore_id "
         "WHERE o.compratore_id=? OR o.venditore_id=?")
    par = [user["id"]] * 4 + [user["id"], user["id"]]
    if e_admin(user["id"]):
        # I moderatori vedono dispute e resi in corso
        q += (" OR o.stato IN ('dispute','return_pending',"
              "'return_shipped','refund')")
    righe = [dict(r) for r in con.execute(q + " ORDER BY o.aggiornato DESC",
                                          par)]
    con.close()
    return righe


# ----------------------- EXPORT DATI (CSV) --------------------------
# Gli affari CONCLUSI dell'utente (released e refunded, da entrambe le
# parti) in un CSV per la propria contabilita'. Due passi: un biglietto
# a scadenza (dentro Telegram il download non puo' portare l'header di
# autenticazione), poi il GET che lo controlla e serve il file.
# ATTENZIONE: il biglietto NON e' monouso. Il downloader di Telegram
# fa piu' richieste sullo stesso link (una HEAD di sonda prima del
# popup, poi il GET vero, a volte a range): bruciarlo alla prima
# gli farebbe scaricare un 410. Vale 5 minuti, poi la purga.

BIGLIETTI_EXPORT: dict[str, tuple[int, float]] = {}  # biglietto -> (tg_id, scadenza)


@app.post("/api/me/export-biglietto")
def export_biglietto(x_tg_init_data: str = Header(""),
                     barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    adesso = time.time()
    for b in [b for b, (_, scade) in BIGLIETTI_EXPORT.items() if scade < adesso]:
        BIGLIETTI_EXPORT.pop(b, None)
    while len(BIGLIETTI_EXPORT) >= 1000:
        BIGLIETTI_EXPORT.pop(next(iter(BIGLIETTI_EXPORT)))
    biglietto = secrets.token_urlsafe(32)
    BIGLIETTI_EXPORT[biglietto] = (user["id"], adesso + 300)
    return {"biglietto": biglietto}


@app.get("/api/export/{biglietto}")
@app.head("/api/export/{biglietto}")   # la sonda di Telegram, prima del popup
def scarica_export(biglietto: str):
    dati = BIGLIETTI_EXPORT.get(biglietto)
    if not dati or dati[1] < time.time():
        BIGLIETTI_EXPORT.pop(biglietto, None)
        raise HTTPException(410, "Link scaduto: riprova dal Profilo")
    tg_id = dati[0]
    con = db()
    righe = con.execute(
        "SELECT o.aggiornato, o.prezzo_sats, o.stato, o.cambio_eur, "
        "o.venditore_id, a.titolo FROM ordini o "
        "JOIN annunci a ON a.id=o.annuncio_id "
        "WHERE (o.venditore_id=? OR o.compratore_id=?) "
        "AND o.stato IN ('released','refunded') "
        "ORDER BY o.aggiornato DESC", (tg_id, tg_id)).fetchall()
    con.close()
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")    # il ; e' il CSV che Excel italiano apre bene
    w.writerow(["data", "ruolo", "annuncio", "sats", "esito", "controvalore_eur"])
    for r in righe:
        eur = ""
        if r["cambio_eur"]:               # 0 = ordine storico: campo vuoto, onesto
            eur = (f"{r['prezzo_sats'] * r['cambio_eur'] / 100_000_000:.2f}"
                   .replace(".", ","))
        w.writerow([time.strftime("%Y-%m-%d", time.localtime(r["aggiornato"])),
                    "vendita" if r["venditore_id"] == tg_id else "acquisto",
                    r["titolo"], r["prezzo_sats"],
                    "concluso" if r["stato"] == "released" else "rimborsato",
                    eur])
    nome = time.strftime("barattolo-affari-%Y%m%d.csv")
    return Response(content="\ufeff" + buf.getvalue(),   # BOM: cosi' Excel legge l'UTF-8
                    media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             f'attachment; filename="{nome}"'})


# --------------------- IMPORT IN BLOCCO (CSV) -----------------------
# I commercianti coi cataloghi grandi caricano un CSV (piu' eventuale
# ZIP di foto) e l'app crea gli annunci in blocco. Due fasi col
# pattern del biglietto: prepara (validazione riga per riga +
# anteprima, sotto i 2 secondi) e avvia (job asincrono: moderazione
# AI a lotti -> creazione con commit per riga -> Nostr a lotti lenti).
# La moderazione e' la STESSA delle pubblicazioni normali, con una
# deroga dichiarata: gli admin ricevono UNA notifica riassuntiva
# (con l'intervallo di id e i titoli bocciati), non una per annuncio.
# Tutto lo stato vive in memoria (uvicorn mono-processo, come
# SFIDE_LOGIN): un riavvio a meta' lascia nel database solo annunci
# COMPLETI (commit per riga) e il frontend lo dice con onesta'.

IMPORT_DIR = "import_tmp"          # gli ZIP in attesa, purgati dall'orologio
os.makedirs(IMPORT_DIR, exist_ok=True)

TETTO_RIGHE_IMPORT = 500           # righe dati per file
TETTO_RIGHE_GIORNO = 1000          # per utente al giorno (in memoria)
TETTO_CSV_BYTES = 2_000_000
TETTO_ZIP_BYTES = 50_000_000
TETTO_ZIP_SCOMPATTATO = 200_000_000   # somma dei file dichiarati (anti-bomba)
TETTO_ZIP_VOCI = 2000
LOTTO_MODERAZIONE = 20             # annunci per chiamata Haiku
PARALLELI_MODERAZIONE = 3          # chiamate AI in volo
LOTTO_NOSTR = 5                    # eventi per lotto verso i relay
PAUSA_NOSTR = 1.5                  # secondi di respiro tra i lotti

IMPORT_LAVORI: dict[str, dict] = {}       # biglietto -> lavoro
IMPORT_ZIP: dict[str, tuple[int, float]] = {}   # token -> (tg_id, scadenza)
IMPORT_QUOTA: dict[int, tuple[str, int]] = {}   # tg_id -> (giorno, righe)


def _quota_usata(tg_id: int) -> int:
    giorno, usate = IMPORT_QUOTA.get(tg_id, ("", 0))
    return usate if giorno == time.strftime("%Y-%m-%d") else 0


def _percorso_zip(token: str) -> str:
    return os.path.join(IMPORT_DIR, f"{token}.zip")


def _cancella_zip(percorso: str):
    try:
        if percorso and os.path.exists(percorso):
            os.remove(percorso)
    except OSError:
        pass


def _purga_lavori():
    """Via i lavori scaduti (mai quelli in corso) coi loro ZIP, e un
    tetto totale che nessun uso onesto raggiunge."""
    adesso = time.time()
    for b in [b for b, l in IMPORT_LAVORI.items()
              if l["scade"] < adesso and l["stato"] != "in_corso"]:
        _cancella_zip(IMPORT_LAVORI[b].get("zip_path", ""))
        IMPORT_LAVORI.pop(b, None)
    while len(IMPORT_LAVORI) >= 20:
        vecchi = [b for b, l in IMPORT_LAVORI.items()
                  if l["stato"] != "in_corso"]
        if not vecchi:
            break
        _cancella_zip(IMPORT_LAVORI[vecchi[0]].get("zip_path", ""))
        IMPORT_LAVORI.pop(vecchi[0], None)
    for t in [t for t, (_, scade) in IMPORT_ZIP.items() if scade < adesso]:
        IMPORT_ZIP.pop(t, None)


MODELLO_IMPORT = (
    "titolo;descrizione;prezzo;valuta;categoria;zona;foto;"
    "consegna;spedizione;taglia\n"
    "Tastiera meccanica 60%;Come nuova, switch rossi, scatola "
    "originale;35000;sats;Elettronica;Milano;;spedizione;450;piccolo\n"
    "Giacca in pelle vintage;Taglia M, vera pelle anni 90;45,00;eur;"
    "Abbigliamento;Roma;https://esempio.it/giacca-fronte.jpg|"
    "https://esempio.it/giacca-retro.jpg;entrambe;5,50;busta\n"
    "Trapano avvitatore Bosch;Con due batterie e valigetta;80000;sats;"
    "Casa e giardino;Torino;trapano.jpg|valigetta.jpg;ritiro;;medio\n")


@app.get("/api/import/modello")
def modello_import():
    """Il CSV modello da compilare: separatore ; (l'Excel italiano),
    BOM per l'UTF-8, tre righe d'esempio che mostrano le tre vie
    delle foto (nessuna, URL separati da |, nomi file nello ZIP).
    Pubblico come il download dell'export: dentro Telegram il
    download non porta l'header di autenticazione, e qui non c'e'
    nulla di segreto."""
    return Response(content="\ufeff" + MODELLO_IMPORT,
                    media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             'attachment; filename="modello-import-barattolo.csv"'})


@app.post("/api/import/zip")
async def import_zip(req: Request, x_tg_init_data: str = Header(""),
                     barattolo_sessione: str = Cookie("")):
    """Riceve lo ZIP delle foto come corpo BINARIO puro (niente
    multipart, niente base64 che gonfia di un terzo): il browser fa
    fetch del file com'e'. Letto a pezzi col tetto applicato DURANTE
    la lettura: un corpo oltre misura si ferma li', non dopo averlo
    tenuto tutto in pancia. Risponde un token da passare a prepara."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    _purga_lavori()
    token = secrets.token_urlsafe(16)
    percorso = _percorso_zip(token)
    letti = 0
    try:
        with open(percorso, "wb") as out:
            async for pezzo in req.stream():
                letti += len(pezzo)
                if letti > TETTO_ZIP_BYTES:
                    raise HTTPException(
                        413, "ZIP troppo grande (massimo 50MB): dividi "
                             "l'import in piu' file")
                out.write(pezzo)
    except HTTPException:
        _cancella_zip(percorso)
        raise
    except Exception:
        _cancella_zip(percorso)
        raise HTTPException(400, "Caricamento interrotto: riprova")

    def _controlla_zip():
        if not zipfile.is_zipfile(percorso):
            return "Il file non \u00e8 uno ZIP valido"
        with zipfile.ZipFile(percorso) as zf:
            voci = zf.infolist()
            if len(voci) > TETTO_ZIP_VOCI:
                return f"Troppi file nello ZIP (massimo {TETTO_ZIP_VOCI})"
            totale = 0
            for v in voci:
                nome = v.filename.replace("\\", "/")
                if nome.startswith("/") or ".." in nome.split("/"):
                    return "Lo ZIP contiene percorsi non ammessi"
                totale += v.file_size
                if v.file_size > 15_000_000:
                    return (f"Il file {os.path.basename(nome)[:40]} "
                            f"supera i 15MB")
            if totale > TETTO_ZIP_SCOMPATTATO:
                return "Il contenuto dello ZIP supera i 200MB"
        return None

    errore = await asyncio.to_thread(_controlla_zip)
    if errore:
        _cancella_zip(percorso)
        raise HTTPException(400, errore)
    IMPORT_ZIP[token] = (user["id"], time.time() + 900)
    return {"zip": token}


def _indice_zip(percorso: str) -> dict:
    """L'indice {nome_file_minuscolo: voce_interna} dello ZIP, cosi'
    'Trapano.JPG' nel CSV trova 'foto/trapano.jpg' nell'archivio.
    Sui doppioni vince la prima voce."""
    indice = {}
    with zipfile.ZipFile(percorso) as zf:
        for nome in zf.namelist():
            if nome.endswith("/"):
                continue
            base = os.path.basename(nome.replace("\\", "/")).lower()
            if base and base not in indice:
                indice[base] = nome
    return indice


@app.post("/api/import/prepara")
async def import_prepara(req: Request, x_tg_init_data: str = Header(""),
                         barattolo_sessione: str = Cookie("")):
    """Fase 1: il CSV si valida riga per riga e si risponde con
    l'anteprima onesta (valide, scarti col numero di riga e il
    motivo, avvisi non bloccanti). Il filtro parole gira QUI su
    tutte le righe; la moderazione AI aspetta il job, cosi'
    l'anteprima arriva in un paio di secondi. Nessun annuncio viene
    creato prima della conferma esplicita."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    _purga_lavori()
    if any(l["stato"] == "in_corso" and l["tg_id"] == user["id"]
           for l in IMPORT_LAVORI.values()):
        raise HTTPException(409, "Hai gi\u00e0 un import in corso: aspetta "
                                 "che finisca")
    d = await leggi_json(req)
    testo = str(d.get("csv", ""))
    if len(testo.encode("utf-8", "ignore")) > TETTO_CSV_BYTES:
        raise HTTPException(400, "CSV troppo grande (massimo 2MB)")
    testo = testo.lstrip("\ufeff")
    if not testo.strip():
        raise HTTPException(400, "Il file \u00e8 vuoto")

    # Lo ZIP, se c'e': deve essere dell'utente e ancora in vita
    zip_token = str(d.get("zip", "") or "")
    zip_path, indice_zip = "", {}
    if zip_token:
        voce = IMPORT_ZIP.get(zip_token)
        if not voce or voce[0] != user["id"] or voce[1] < time.time():
            raise HTTPException(410, "ZIP scaduto o non trovato: "
                                     "ricaricalo")
        zip_path = _percorso_zip(zip_token)
        try:
            indice_zip = await asyncio.to_thread(_indice_zip, zip_path)
        except Exception:
            raise HTTPException(400, "Il file non \u00e8 uno ZIP valido")

    righe_csv = list(csv.reader(io.StringIO(testo), delimiter=";"))
    if not righe_csv:
        raise HTTPException(400, "Il file \u00e8 vuoto")
    intestazione = [c.strip().lstrip("\ufeff").lower()
                    for c in righe_csv[0]]
    if "titolo" not in intestazione or "prezzo" not in intestazione:
        raise HTTPException(400, "Manca l'intestazione (titolo;"
                                 "descrizione;prezzo;valuta;categoria;"
                                 "zona;foto): scarica il modello dal "
                                 "Profilo e riparti da quello")
    colonna = {nome: i for i, nome in enumerate(intestazione)}
    dati = [(n, r) for n, r in enumerate(righe_csv[1:], start=2)
            if any(c.strip() for c in r)]      # le righe vuote non contano
    if len(dati) > TETTO_RIGHE_IMPORT:
        raise HTTPException(400, f"Massimo {TETTO_RIGHE_IMPORT} righe "
                                 f"per import: il tuo file ne ha "
                                 f"{len(dati)}. Dividilo in pi\u00f9 file")

    def cella(riga, nome):
        i = colonna.get(nome)
        return riga[i].strip() if i is not None and i < len(riga) else ""

    righe, scarti, avvisi = [], [], []
    for numero, r in dati:
        titolo = neutralizza_formula(cella(r, "titolo"))
        descrizione = neutralizza_formula(cella(r, "descrizione"))
        zona = neutralizza_formula(cella(r, "zona"))
        if not titolo:
            scarti.append({"riga": numero, "motivo": "titolo mancante"})
            continue

        # Prezzo e valuta: il giudice e' lo stesso di pubblica()
        valuta = (cella(r, "valuta") or "sats").lower()
        prezzo_testo = cella(r, "prezzo").replace(" ", "")
        payload = {"titolo": titolo, "valuta": valuta}
        if valuta == "eur":
            payload["prezzo_eur"] = prezzo_testo.replace(",", ".")
        else:
            payload["prezzo_sats"] = prezzo_testo
        try:
            valuta, prezzo_sats, prezzo_eur = await prezzo_da_payload(payload)
        except HTTPException as e:
            scarti.append({"riga": numero, "motivo": str(e.detail)})
            continue

        # Le foto, tre vie: URL, nome nello ZIP, oppure niente
        foto = []
        voci_foto = [v.strip() for v in cella(r, "foto").split("|")
                     if v.strip()]
        if len(voci_foto) > 5:
            avvisi.append({"riga": numero,
                           "motivo": "pi\u00f9 di 5 foto: tengo le prime 5"})
            voci_foto = voci_foto[:5]
        for v in voci_foto:
            if v.lower().startswith(("http://", "https://")):
                if url_foto_ammesso(v):
                    foto.append(("url", v))
                else:
                    avvisi.append({"riga": numero,
                                   "motivo": f"URL foto non ammesso: "
                                             f"{v[:60]}"})
            elif not zip_path:
                avvisi.append({"riga": numero,
                               "motivo": f"foto \u00ab{v[:40]}\u00bb indicata ma "
                                         f"nessuno ZIP caricato"})
            elif os.path.basename(v.replace("\\", "/")).lower() \
                    not in indice_zip:
                avvisi.append({"riga": numero,
                               "motivo": f"foto \u00ab{v[:40]}\u00bb non trovata "
                                         f"nello ZIP"})
            else:
                foto.append(
                    ("zip",
                     indice_zip[os.path.basename(v.replace("\\", "/"))
                                .lower()]))

        # Consegna, spedizione e taglia: colonne facoltative, giudice
        # unico di pubblica() — i valori sconosciuti diventano annuncio
        # senza modalita', mai uno scarto (i CSV di ieri non le hanno)
        sped_testo = cella(r, "spedizione").replace(" ", "").replace(",", ".")
        payload_consegna = {"consegna": cella(r, "consegna").lower(),
                            "taglia_pacco": cella(r, "taglia").lower()}
        if valuta == "eur":
            payload_consegna["spedizione_eur"] = sped_testo or 0
        else:
            payload_consegna["spedizione_sats"] = sped_testo or 0
        consegna, sped_sats, sped_eur, taglia = \
            await consegna_da_payload(payload_consegna, valuta)

        # Moderazione strato 1, su TUTTE le righe, prima della conferma
        violata = controlla_vietato(titolo, descrizione)
        if violata:
            scarti.append({"riga": numero,
                           "motivo": f"filtro contenuti ({violata})"})
            continue

        righe.append({"riga": numero, "titolo": titolo,
                      "descrizione": descrizione,
                      "categoria": categoria_tollerante(cella(r, "categoria")),
                      "zona": zona, "valuta": valuta,
                      "prezzo_sats": prezzo_sats, "prezzo_eur": prezzo_eur,
                      "consegna": consegna, "spedizione_sats": sped_sats,
                      "spedizione_eur": sped_eur, "taglia_pacco": taglia,
                      "foto": foto})

    if not righe:
        return {"valide": 0, "totale": len(dati),
                "scarti": scarti, "avvisi": avvisi}

    usate = _quota_usata(user["id"])
    if usate + len(righe) > TETTO_RIGHE_GIORNO:
        raise HTTPException(400, f"Superato il limite giornaliero di "
                                 f"{TETTO_RIGHE_GIORNO} annunci importati "
                                 f"(ne hai gi\u00e0 caricati {usate} oggi)")

    # Un nuovo prepara dello stesso utente sostituisce il suo lavoro
    # in attesa (e il vecchio ZIP se ne va con lui)
    for b in [b for b, l in IMPORT_LAVORI.items()
              if l["tg_id"] == user["id"] and l["stato"] == "pronto"]:
        if IMPORT_LAVORI[b].get("zip_path") != zip_path:
            _cancella_zip(IMPORT_LAVORI[b].get("zip_path", ""))
        IMPORT_LAVORI.pop(b, None)

    biglietto = secrets.token_urlsafe(32)
    IMPORT_LAVORI[biglietto] = {
        "tg_id": user["id"], "nome": user["first_name"],
        "creato": time.time(), "scade": time.time() + 900,
        "stato": "pronto", "fase": "",
        "nostr": bool(d.get("nostr", True)),
        "zip_path": zip_path, "righe": righe,
        "scarti": scarti, "avvisi": avvisi,
        "totale": len(righe), "fatte": 0, "ok": [],
        "falliti": [], "nostr_fatti": 0,
    }
    return {"biglietto": biglietto, "valide": len(righe),
            "totale": len(dati), "scarti": scarti, "avvisi": avvisi}


def _foto_riga_import(annuncio_id: int, foto: list, zip_path: str):
    """Le foto di UNA riga: pesca dallo ZIP o scarica dall'URL, porta
    tutto nella filiera buona e scrive pieno + miniatura. Sincrona
    (gira in un thread). Ritorna (nomi, problemi): una foto morta e'
    un avviso, mai un annuncio perso."""
    nomi, problemi = [], []
    zf = None
    try:
        for indice, (tipo, voce) in enumerate(foto[:5]):
            raw = None
            if tipo == "zip" and zip_path:
                try:
                    if zf is None:
                        zf = zipfile.ZipFile(zip_path)
                    raw = zf.read(voce)
                except Exception:
                    problemi.append(f"foto «{os.path.basename(voce)[:40]}» "
                                    f"illeggibile nello ZIP")
            elif tipo == "url":
                raw = scarica_foto_import(voce)
                if raw is None:
                    problemi.append(f"foto non scaricata: {voce[:60]}")
            if not raw:
                continue
            pronto = normalizza_foto_import(raw)
            if not pronto:
                problemi.append(f"foto {indice + 1} non riconosciuta "
                                f"come immagine")
                continue
            nome = _salva_una_foto(annuncio_id, indice, pronto)
            if nome:
                nomi.append(nome)
    finally:
        if zf:
            zf.close()
    return nomi, problemi


async def _crea_riga_import(lavoro: dict, riga: dict):
    """UNA riga diventa un annuncio: INSERT identico a pubblica(),
    commit subito (un crash a meta' import lascia solo annunci
    completi), poi le foto in un thread fuori dalla transazione,
    come sempre."""
    con = db()
    lat, lon = coordinate_da_zona(riga["zona"])
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,valuta,prezzo_eur,lat,lon,"
        "consegna,spedizione_sats,spedizione_eur,taglia_pacco,creato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (lavoro["tg_id"], riga["titolo"], riga["descrizione"],
         riga["categoria"], riga["prezzo_sats"], riga["zona"],
         riga["valuta"], riga["prezzo_eur"], lat, lon,
         riga.get("consegna", ""), riga.get("spedizione_sats", 0),
         riga.get("spedizione_eur", 0), riga.get("taglia_pacco", ""),
         int(time.time())))
    annuncio_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.commit()
    con.close()
    if riga["foto"]:
        nomi, problemi = await asyncio.to_thread(
            _foto_riga_import, annuncio_id, riga["foto"], lavoro["zip_path"])
        if nomi:
            con = db()
            con.execute("UPDATE annunci SET foto=? WHERE id=?",
                        (json.dumps(nomi), annuncio_id))
            con.commit()
            con.close()
        for p in problemi:
            lavoro["avvisi"].append({"riga": riga["riga"], "motivo": p})
    lavoro["ok"].append(annuncio_id)


async def _crea_riga_con_guardia(lavoro: dict, riga: dict):
    try:
        await _crea_riga_import(lavoro, riga)
    except Exception as e:
        lavoro["falliti"].append({"riga": riga["riga"],
                                  "titolo": riga["titolo"],
                                  "motivo": f"errore interno: {str(e)[:80]}"})
    finally:
        lavoro["fatte"] += 1


async def _lavoro_import(biglietto: str):
    """Il job in sottofondo, tre fasi: moderazione AI a lotti,
    creazione a gruppetti (il grosso del tempo sono foto e download,
    che vivono nei thread), pubblicazione Nostr a lotti LENTI in
    coda quando gli annunci sono gia' in vetrina. Qualsiasi
    eccezione = stato 'errore' e una riga in console: mai un task
    che muore muto."""
    lavoro = IMPORT_LAVORI.get(biglietto)
    if not lavoro:
        return
    try:
        # --- Fase 1: moderazione AI, stessa copertura di pubblica() ---
        lavoro["fase"] = "moderazione"
        voci = [(r["riga"], r["titolo"], r["descrizione"])
                for r in lavoro["righe"]]
        lotti = [voci[i:i + LOTTO_MODERAZIONE]
                 for i in range(0, len(voci), LOTTO_MODERAZIONE)]
        respiro = asyncio.Semaphore(PARALLELI_MODERAZIONE)

        async def _un_lotto(lotto):
            async with respiro:
                return await moderazione_ai_lotto(lotto)

        bocciati = {}
        for esito in await asyncio.gather(*[_un_lotto(l) for l in lotti]):
            bocciati.update(esito)
        approvate = []
        for r in lavoro["righe"]:
            if r["riga"] in bocciati:
                lavoro["falliti"].append(
                    {"riga": r["riga"], "titolo": r["titolo"],
                     "motivo": f"moderazione AI: {bocciati[r['riga']]}"})
                lavoro["fatte"] += 1
            else:
                approvate.append(r)

        # --- Fase 2: creazione, a gruppetti di 4 ---
        lavoro["fase"] = "creazione"
        for gruppo in [approvate[i:i + 4]
                       for i in range(0, len(approvate), 4)]:
            await asyncio.gather(*[_crea_riga_con_guardia(lavoro, r)
                                   for r in gruppo])
        # I canali di Barattolo: tutti in coda INSIEME a foto finite,
        # cosi' la finestra del drenatore li vede in un colpo solo e
        # un import fa sempre UN solo post aggregato, mai una raffica.
        # Stessa cosa per gli avvisi di ricerca: chi matcha 12 righe
        # dell'import riceve UN «12 nuovi annunci», mai 12 messaggi.
        for annuncio_id in lavoro["ok"]:
            accoda_promo(annuncio_id)
            accoda_match(annuncio_id)

        # --- Fase 3: la piazza Nostr, senza fretta ---
        if lavoro["nostr"] and lavoro["ok"] and _NOSTR:
            lavoro["fase"] = "nostr"
            for gruppo in [lavoro["ok"][i:i + LOTTO_NOSTR]
                           for i in range(0, len(lavoro["ok"]),
                                          LOTTO_NOSTR)]:
                await asyncio.gather(*[annuncio_su_nostr(a, "active")
                                       for a in gruppo])
                lavoro["nostr_fatti"] += len(gruppo)
                await asyncio.sleep(PAUSA_NOSTR)
        lavoro["stato"] = "finito"
    except Exception as e:
        lavoro["stato"] = "errore"
        print(f"⚠️ Import in blocco fallito (biglietto …{biglietto[-6:]},"
              f" utente {lavoro['tg_id']}): {e}")
    finally:
        lavoro["fase"] = ""
        lavoro["scade"] = time.time() + 3600   # il report resta leggibile 1h
        _cancella_zip(lavoro.get("zip_path", ""))
        lavoro["zip_path"] = ""

    # Le notifiche di chiusura, fail-open: il report nel Profilo c'e'
    # comunque
    try:
        creati, ko = len(lavoro["ok"]), len(lavoro["falliti"])
        if lavoro["stato"] == "finito":
            testo = f"📥 Import completato: <b>{creati}</b> annunci pubblicati"
            if ko:
                testo += f", {ko} non passati (il dettaglio è nel report)"
            await notifica(lavoro["tg_id"], testo + ".")
        else:
            await notifica(lavoro["tg_id"],
                           f"📥 L'import si è interrotto: {creati} annunci "
                           f"erano già entrati, controlla i tuoi annunci "
                           f"e ricarica le righe mancanti.")
        await premia_distintivi(lavoro["tg_id"])
        # Strato 3 in versione riassunto: UNA notifica ai moderatori
        # con l'intervallo di id (per le stats e le rimozioni) e i
        # titoli bocciati dall'AI
        riassunto = (f"📥 <b>Import in blocco</b> di {lavoro['nome']} "
                     f"(id {lavoro['tg_id']})\n"
                     f"✅ {creati} annunci creati")
        if lavoro["ok"]:
            riassunto += f" (#{min(lavoro['ok'])}–#{max(lavoro['ok'])})"
        bocciati_ai = [f for f in lavoro["falliti"]
                       if f["motivo"].startswith("moderazione AI")]
        if bocciati_ai:
            riassunto += f"\n🚫 {len(bocciati_ai)} bloccati dall'AI: " + \
                "; ".join(f"«{f['titolo'][:40]}»" for f in bocciati_ai[:10])
        if lavoro["scarti"]:
            riassunto += (f"\n⚠️ {len(lavoro['scarti'])} righe scartate "
                          f"in anteprima")
        await notifica_admin(riassunto)
    except Exception as e:
        print(f"⚠️ Notifiche di fine import saltate: {e}")


@app.post("/api/import/avvia")
async def import_avvia(req: Request, x_tg_init_data: str = Header(""),
                       barattolo_sessione: str = Cookie("")):
    """Fase 2: la conferma esplicita. Da qui in poi il lavoro va da
    solo e il frontend lo segue col polling di /stato."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    lavoro = IMPORT_LAVORI.get(str(d.get("biglietto", "")))
    if not lavoro or lavoro["scade"] < time.time():
        raise HTTPException(404, "Anteprima scaduta: ricarica il file")
    if lavoro["tg_id"] != user["id"]:
        raise HTTPException(403, "Operazione non permessa")
    if lavoro["stato"] != "pronto":
        raise HTTPException(409, "Questo import è già partito")
    # Un solo import in corso in TUTTO il server: siamo mono-processo
    # su una macchina piccola, e un job dura pochi minuti
    if any(l["stato"] == "in_corso" for l in IMPORT_LAVORI.values()):
        raise HTTPException(409, "C'è già un import in corso sul "
                                 "mercatino: riprova tra qualche minuto")
    oggi = time.strftime("%Y-%m-%d")
    IMPORT_QUOTA[user["id"]] = (oggi,
                                _quota_usata(user["id"]) + lavoro["totale"])
    lavoro["stato"] = "in_corso"
    lavoro["scade"] = time.time() + 7200   # mai scaduto a meta' corsa
    lavoro["_task"] = asyncio.create_task(
        _lavoro_import(str(d.get("biglietto"))))
    return {"ok": True}


@app.get("/api/import/stato/{biglietto}")
def import_stato(biglietto: str, x_tg_init_data: str = Header(""),
                 barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    lavoro = IMPORT_LAVORI.get(biglietto)
    if not lavoro or lavoro["scade"] < time.time():
        raise HTTPException(404, "Import non trovato (forse il server "
                                 "è ripartito): controlla i tuoi annunci")
    if lavoro["tg_id"] != user["id"]:
        raise HTTPException(403, "Operazione non permessa")
    return {"stato": lavoro["stato"], "fase": lavoro["fase"],
            "totale": lavoro["totale"], "fatte": lavoro["fatte"],
            "ok_n": len(lavoro["ok"]), "nostr": lavoro["nostr"],
            "nostr_fatti": lavoro["nostr_fatti"],
            "falliti": lavoro["falliti"], "avvisi": lavoro["avvisi"]}


# ----------------------- FEEDBACK E STELLE --------------------------
# A affare concluso le due parti si giudicano a vicenda: voto 1-5 +
# commento breve. Anche 'refunded' conta: e' una transazione vera, e
# nascondere proprio quelle andate male gonfierebbe tutti i profili.

STATI_FEEDBACK = ("released", "refunded")   # gli stati che ammettono il voto


def _ricalcola_rating(con, tg_id: int):
    """Rifa' i conti di rating e n_feedback dalla tabella feedback.
    Nessun commit qui dentro: la transazione e' del chiamante."""
    r = con.execute("SELECT COUNT(*) AS n, AVG(voto) AS media "
                    "FROM feedback WHERE per_tg_id=?", (tg_id,)).fetchone()
    con.execute("UPDATE utenti SET rating=?, n_feedback=? WHERE tg_id=?",
                (round(r["media"] or 0, 1), r["n"], tg_id))


@app.post("/api/orders/{ordine_id}/feedback")
async def lascia_feedback(ordine_id: int, req: Request,
                          x_tg_init_data: str = Header(""),
                          barattolo_sessione: str = Cookie("")):
    """Una delle due parti lascia il feedback sull'altra. Uno solo per
    ordine per parte, definitivo (la valvola e' la rimozione admin):
    il vincolo UNIQUE del database e' il giudice dei doppioni."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    try:
        voto = int(d.get("voto", 0))
    except (TypeError, ValueError):
        voto = 0
    if not 1 <= voto <= 5:
        raise HTTPException(400, "Il voto va da 1 a 5 stelle")
    commento = str(d.get("commento", "")).strip()
    if len(commento) > 200:
        raise HTTPException(400, "Commento troppo lungo (max 200 caratteri)")
    if commento:
        categoria = controlla_vietato(commento, "")
        if categoria:
            await notifica_admin(
                f"🚫 <b>Commento di feedback bloccato dal filtro</b> "
                f"({categoria})\nOrdine #{ordine_id} — "
                f"{user['first_name']} (id {user['id']})")
            raise HTTPException(400, "Il commento contiene termini non "
                                     "ammessi sul mercatino")

    con = db()
    try:
        # Lock di scrittura subito: l'ordine va riletto DENTRO la
        # transazione (una fusione account potrebbe spostarlo proprio ora)
        con.execute("BEGIN IMMEDIATE")
        o = con.execute("SELECT * FROM ordini WHERE id=?",
                        (ordine_id,)).fetchone()
        if not o:
            con.rollback()
            raise HTTPException(404, "Ordine non trovato")
        if user["id"] not in (o["compratore_id"], o["venditore_id"]):
            con.rollback()
            raise HTTPException(403, "Operazione non permessa")
        if o["stato"] not in STATI_FEEDBACK:
            con.rollback()
            raise HTTPException(400, "Il feedback si lascia a affare concluso")
        per = (o["venditore_id"] if user["id"] == o["compratore_id"]
               else o["compratore_id"])
        if per == user["id"]:
            # auto-ordine (puo' nascere da una fusione): niente auto-voti
            con.rollback()
            raise HTTPException(400, "Operazione non permessa")
        try:
            con.execute("INSERT INTO feedback(ordine_id, da_tg_id, "
                        "per_tg_id, voto, commento, creato) "
                        "VALUES(?,?,?,?,?,?)",
                        (ordine_id, user["id"], per, voto, commento,
                         int(time.time())))
        except sqlite3.IntegrityError:
            con.rollback()
            raise HTTPException(400, "Hai già lasciato il feedback "
                                     "per questo ordine")
        _ricalcola_rating(con, per)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    stelle = "★" * voto
    await notifica(per,
                   f"⭐ <b>Hai ricevuto un feedback:</b> {stelle} ({voto}/5) "
                   f"per l'affare #{ordine_id}."
                   + (f"\n«{commento}»" if commento else ""))
    # Un feedback puo' premiare entrambi: chi lo lascia (buon vicino)
    # e chi lo riceve (stimato)
    await premia_distintivi(user["id"])
    await premia_distintivi(per)
    return {"ok": True, "voto": voto}


@app.post("/api/admin/feedback/{feedback_id}/rimuovi")
async def rimuovi_feedback_admin(feedback_id: int,
                                 x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    """SOLO ADMIN: rimuove un commento di feedback abusivo. Il rating
    di chi lo riceveva si rifa' i conti da solo (ricalcolo)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    if not e_admin(user["id"]):
        raise HTTPException(403, "Riservato ai moderatori")
    con = db()
    try:
        con.execute("BEGIN IMMEDIATE")
        f = con.execute("SELECT * FROM feedback WHERE id=?",
                        (feedback_id,)).fetchone()
        if not f:
            con.rollback()
            raise HTTPException(404, "Feedback non trovato")
        con.execute("DELETE FROM feedback WHERE id=?", (feedback_id,))
        _ricalcola_rating(con, f["per_tg_id"])
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    await notifica(f["da_tg_id"],
                   "🧹 Un moderatore ha rimosso il tuo feedback "
                   f"sull'affare #{f['ordine_id']} perché non rispettava "
                   "le regole del mercatino.")
    return {"ok": True}


# --------------------- L'OROLOGIO DEGLI SBLOCCHI --------------------
# Un compito in sottofondo controlla ogni 10 minuti le scadenze:
#  - finestra di conferma scaduta (delivered da piu' di ORE_CONFERMA)
#  - silenzio totale dopo la spedizione (shipped da piu' di
#    GIORNI_AUTO_SBLOCCO giorni)
# In entrambi i casi i sats vengono sbloccati d'ufficio al venditore.
# NOTA: funziona solo finche' il server e' acceso.

import asyncio


async def controlla_scadenze():
    adesso = int(time.time())
    con = db()
    scaduti_consegna = [r["id"] for r in con.execute(
        "SELECT id FROM ordini WHERE stato='delivered' AND consegnato>0 "
        "AND consegnato < ?", (adesso - ORE_CONFERMA * 3600,))]
    scaduti_silenzio = [r["id"] for r in con.execute(
        "SELECT id FROM ordini WHERE stato='shipped' AND spedito_il>0 "
        "AND spedito_il < ?", (adesso - GIORNI_AUTO_SBLOCCO * 86400,))]
    # Spazzatura: via le sessioni web ormai scadute
    con.execute("DELETE FROM sessioni WHERE scade < ?", (adesso,))
    con.commit()
    con.close()
    for oid in scaduti_consegna + scaduti_silenzio:
        print(f"⏰ Sblocco automatico dell'ordine #{oid}")
        await _sblocca_sats(oid, automatico=True)


async def sollecita_incassi():
    """Il promemoria degli incassi fermi: un ordine 'confirmed' senza
    metodo d'incasso non fa rumore da solo — la notifica della
    conferma parte una volta sola, e se il venditore la ignora i sats
    restano congelati nel silenzio. Ogni SOLLECITO_INCASSO_GIORNI gli
    si ricorda importo e strade (Lightning address o invoice); dopo
    SOLLECITO_INCASSO_MAX solleciti ignorati parte UNA segnalazione ai
    moderatori, poi silenzio: il caso e' in mani umane. Qui i sats non
    si muovono mai, solo parole; le notifiche partono DOPO il commit."""
    if SOLLECITO_INCASSO_GIORNI <= 0:
        return                       # leva a zero = funzione spenta
    adesso = int(time.time())
    passo = SOLLECITO_INCASSO_GIORNI * 86400
    con = db()
    # L'attesa riparte dall'ultimo segno di vita: l'ingresso in
    # 'confirmed' (aggiornato) o il sollecito precedente. Chi ha gia'
    # passato la segnalazione ai moderatori (contatore oltre il tetto)
    # non compare piu'.
    righe = con.execute(
        "SELECT o.id, o.venditore_id, o.prezzo_sats, o.protezione_sats, "
        "o.solleciti_incasso, a.titolo FROM ordini o "
        "JOIN annunci a ON a.id = o.annuncio_id "
        "WHERE o.stato='confirmed' AND o.solleciti_incasso <= ? "
        "AND MAX(o.aggiornato, o.sollecito_incasso_il) < ?",
        (SOLLECITO_INCASSO_MAX, adesso - passo)).fetchall()
    if not righe:
        con.close()
        return
    for r in righe:
        con.execute("UPDATE ordini SET sollecito_incasso_il=?, "
                    "solleciti_incasso=solleciti_incasso+1 WHERE id=?",
                    (adesso, r["id"]))
    con.commit()
    con.close()
    for r in righe:
        netto = netto_venditore(r["prezzo_sats"] - r["protezione_sats"])
        titolo = r["titolo"][:60]
        try:
            if r["solleciti_incasso"] < SOLLECITO_INCASSO_MAX:
                await notifica(r["venditore_id"],
                    f"💰 <b>Hai sats da incassare!</b> L'affare «{titolo}» "
                    f"è concluso e i tuoi <b>{netto} sats</b> ti aspettano "
                    f"nel deposito di garanzia. Per riceverli apri l'ordine "
                    f"nella Mini App e imposta il tuo Lightning address "
                    f"(incassi automatici, per sempre) oppure incolla una "
                    f"invoice di esattamente quell'importo. ⚡")
            else:
                # Il tetto e' passato da un altro giro di attesa:
                # M solleciti ignorati, tocca a un umano.
                await notifica_admin(
                    f"🧊 <b>Incasso fermo:</b> ordine #{r['id']} "
                    f"(«{titolo}»), <b>{netto} sats</b> in cassaforte. "
                    f"Il venditore ha ignorato {SOLLECITO_INCASSO_MAX} "
                    f"solleciti in ~{(SOLLECITO_INCASSO_MAX + 1) * SOLLECITO_INCASSO_GIORNI} "
                    f"giorni: serve un occhio umano.")
        except Exception as e:
            print(f"⚠️ Sollecito incasso saltato (#{r['id']}): {e}")


# --- L'import periodico da Nostr ------------------------------------
# Ogni ora l'orologio riusa la logica di importa_nostr.py per tenere
# freschi gli annunci dei venditori consenzienti (per ora uno solo:
# NPUB_VENDITORE / VENDITORE_ID in config.py — quando serviranno di
# piu', qui basta far diventare la coppia una lista). Fail-open
# totale: se qualcosa va storto resta una riga in console e il
# mercatino vive. Il lavoro e' sincrono (websocket-client, download
# foto): gira dentro asyncio.to_thread come la verifica npub.

try:
    from config import NPUB_VENDITORE, VENDITORE_ID
except ImportError:
    NPUB_VENDITORE, VENDITORE_ID = "", 0

SECONDI_IMPORT_NOSTR = 3600
_prossimo_import_nostr = 0.0     # 0 = primo giro subito all'avvio


async def importa_nostr_periodico():
    global _prossimo_import_nostr
    if (not NPUB_VENDITORE or NPUB_VENDITORE.startswith("INCOLLA")
            or not VENDITORE_ID):
        return                   # segnaposto in config = funzione spenta
    if time.time() < _prossimo_import_nostr:
        return
    # L'appuntamento si fissa PRIMA di provare: anche un errore
    # aspetta la prossima ora, niente tempeste di tentativi.
    _prossimo_import_nostr = time.time() + SECONDI_IMPORT_NOSTR
    import importa_nostr         # qui e non in cima: se manca
    #                              websocket-client il server vive lo stesso
    t0 = int(time.time())
    importati, aggiornati, saltati = await asyncio.to_thread(
        importa_nostr.importa_venditore, NPUB_VENDITORE, VENDITORE_ID, DB)
    print(f"🔄 Import Nostr: {importati} nuovi, {aggiornati} aggiornati, "
          f"{saltati} saltati")
    # Il dopo-import, senza toccare importa_nostr.py (che scrive
    # dritto nel DB): le coordinate seguono le zone arrivate dai relay
    # (anche quelle cambiate su righe vecchie) e i soli annunci NUOVI
    # (creato>=t0: gli UPDATE non lo cambiano) vanno al matching degli
    # avvisi — per chi cerca, un annuncio e' un annuncio.
    try:
        con = db()
        for r in con.execute("SELECT id, zona, lat, lon FROM annunci "
                             "WHERE contatto_nostr!='' AND stato='attivo'"
                             ).fetchall():
            lat, lon = coordinate_da_zona(r["zona"])
            if (lat, lon) != (r["lat"], r["lon"]):
                con.execute("UPDATE annunci SET lat=?, lon=? WHERE id=?",
                            (lat, lon, r["id"]))
        con.commit()
        nuovi = con.execute("SELECT id FROM annunci WHERE creato>=? "
                            "AND contatto_nostr!='' AND stato='attivo'",
                            (t0,)).fetchall()
        con.close()
        for r in nuovi:
            accoda_match(r["id"])
    except Exception as e:
        print(f"⚠️ Dopo-import (coordinate/avvisi) saltato: {e}")


def pulisci_import():
    """La scopa dell'import in blocco: via i lavori scaduti (mai
    quelli in corsa), gli ZIP orfani rimasti in import_tmp da piu'
    di un'ora (un crash a meta' upload li lascerebbe li' per sempre)
    e le quote dei giorni passati."""
    _purga_lavori()
    adesso = time.time()
    try:
        for nome in os.listdir(IMPORT_DIR):
            percorso = os.path.join(IMPORT_DIR, nome)
            if os.path.isfile(percorso) and \
                    adesso - os.path.getmtime(percorso) > 3600:
                _cancella_zip(percorso)
    except OSError:
        pass
    oggi = time.strftime("%Y-%m-%d")
    for tg_id in [t for t, (giorno, _) in IMPORT_QUOTA.items()
                  if giorno != oggi]:
        IMPORT_QUOTA.pop(tg_id, None)


async def scadenze_offerte():
    """Il giro delle offerte: quelle su annunci spariti dalla vetrina
    decadono, quelle rimaste senza risposta (o senza pagamento nella
    finestra) scadono. Le notifiche partono DOPO il commit; le vendite
    hanno gia' il loro gancio in verifica-pagamento, qui arrivano solo
    le code (rimozioni e scadenze vere)."""
    con = db()
    adesso = int(time.time())
    righe = con.execute(
        "SELECT o.*, a.titolo, a.stato AS stato_annuncio "
        "FROM offerte o JOIN annunci a ON a.id = o.annuncio_id "
        "WHERE o.stato IN ('proposta','controproposta','accettata') AND "
        "(a.stato != 'attivo' OR (o.scadenza > 0 AND o.scadenza < ?))",
        (adesso,)).fetchall()
    if not righe:
        con.close()
        return
    for r in righe:
        nuovo = "decaduta" if r["stato_annuncio"] != "attivo" else "scaduta"
        con.execute("UPDATE offerte SET stato=?, aggiornato=? WHERE id=?",
                    (nuovo, adesso, r["id"]))
    con.commit()
    con.close()
    for r in righe:
        titolo = r["titolo"][:60]
        try:
            if r["stato_annuncio"] != "attivo":
                await notifica(r["compratore_id"],
                    f"«{titolo}» non è più disponibile: la tua offerta "
                    f"decade.")
            elif r["stato"] == "proposta":
                cifra = _cifra_offerta(r["valuta"], r["importo_sats"],
                                       r["importo_eur"])
                await notifica(r["compratore_id"],
                    f"⏳ La tua offerta di {cifra} per «{titolo}» è "
                    f"scaduta senza risposta. L'annuncio è ancora in "
                    f"vetrina, se vuoi riprovare.")
            elif r["stato"] == "controproposta":
                await notifica(r["venditore_id"],
                    f"⏳ La tua controproposta per «{titolo}» è scaduta "
                    f"senza risposta dell'acquirente.")
            else:  # accettata, ma il pagamento non e' mai arrivato
                cifra = _cifra_offerta(r["valuta"], *_importo_accordo(r))
                await notifica(r["compratore_id"],
                    f"⏳ Il tempo per comprare «{titolo}» a {cifra} è "
                    f"finito: l'offerta è scaduta.")
                await notifica(r["venditore_id"],
                    f"L'acquirente non ha completato il pagamento in "
                    f"tempo: l'offerta su «{titolo}» è scaduta e "
                    f"l'annuncio resta in vetrina.")
        except Exception as e:
            print(f"⚠️ Notifica di scadenza offerta saltata: {e}")


def scadenze_lampo():
    """La scopa delle offerte lampo: le colonne si azzerano quando la
    scadenza e' passata. Non e' questione di correttezza (ogni lettura
    gatea gia' sulla scadenza) ma di pulizia: la vetrina non porta in
    giro numeri morti, e l'annuncio torna pronto per un lancio nuovo.
    Nessuna notifica: lo sconto finito non e' una novita' per nessuno."""
    con = db()
    con.execute("UPDATE annunci SET lampo_percento=0, lampo_scadenza=0 "
                "WHERE lampo_percento>0 AND lampo_scadenza<=?",
                (int(time.time()),))
    con.commit()
    con.close()


async def orologio():
    while True:
        try:
            await controlla_scadenze()
        except Exception as e:
            print(f"Orologio sblocchi, errore (riprovo tra 10 min): {e}")
        try:
            await sollecita_incassi()
        except Exception as e:
            print(f"⚠️ Solleciti incasso saltati: {e}")
        try:
            await scadenze_offerte()
        except Exception as e:
            print(f"⚠️ Scadenze offerte saltate: {e}")
        try:
            scadenze_lampo()
        except Exception as e:
            print(f"⚠️ Scadenze lampo saltate: {e}")
        try:
            await importa_nostr_periodico()
        except Exception as e:
            print(f"⚠️ Import Nostr periodico saltato (riprovo tra "
                  f"un'ora): {e}")
        try:
            pulisci_import()
        except Exception as e:
            print(f"⚠️ Pulizia import in blocco saltata: {e}")
        try:
            pulisci_avvisi()
        except Exception as e:
            print(f"⚠️ Pulizia avvisi saltata: {e}")
        try:
            await avvisa_nuovi_iscritti()
        except Exception as e:
            print(f"⚠️ Campanello dei nuovi iscritti saltato: {e}")
        await asyncio.sleep(600)


@app.on_event("startup")
async def avvia_orologio():
    asyncio.create_task(orologio())
    # Le foto nate prima delle miniature ne ricevono una, in un
    # thread: l'avvio non aspetta nessuno (oggi i file sono pochi)
    asyncio.create_task(asyncio.to_thread(genera_miniature_mancanti))


# ------------------- FILE SERVITI AL PUBBLICO -----------------------
# SICUREZZA: il server NON espone piu' l'intera cartella (che sul VPS
# contiene anche config.py, il database e .git!). Al pubblico vanno
# SOLO la Mini App e le foto degli annunci: tutto il resto e'
# invisibile per costruzione.

from fastapi.responses import FileResponse

# Header anti-cache: la WebView di Telegram (e ogni browser) non deve mai
# conservare la pagina HTML — così ogni push arriva subito fresco a tutti.
# Si applicano SOLO alla pagina: API e foto restano fuori, zero impatto.
HEADER_NO_CACHE = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@app.get("/")
def home():
    return FileResponse("miniapp.html", media_type="text/html", headers=HEADER_NO_CACHE)


@app.get("/miniapp.html")
def pagina_miniapp():
    return FileResponse("miniapp.html", media_type="text/html", headers=HEADER_NO_CACHE)


@app.get("/negozio/{chi}")
def pagina_negozio(chi: str):
    """Link condivisibile del negozio: e' sempre la stessa Mini App,
    il JS legge /negozio/... dall'URL e apre la vista giusta."""
    return FileResponse("miniapp.html", media_type="text/html", headers=HEADER_NO_CACHE)


@app.get("/annuncio/{aid}")
def pagina_annuncio(aid: int):
    """Link condivisibile di un annuncio (bottone condividi del
    dettaglio): stessa Mini App, il JS legge /annuncio/{id} dall'URL
    e apre il dettaglio — in vetrina anonima per chi non e' entrato."""
    return FileResponse("miniapp.html", media_type="text/html", headers=HEADER_NO_CACHE)


@app.get("/vendor/nostr.js")
def vendor_nostr():
    """La libreria nostr-tools, servita da casa nostra e mai da una CDN:
    nessun terzo deve poter cambiare il codice della pagina dove
    qualcuno puo' incollare una nsec. File singolo committato a
    versione bloccata, rotta esplicita: mai StaticFiles su una
    directory (regola ferrea 3). Si puo' tenere in cache: cambia solo
    quando aggiorniamo il file apposta (e col ?v= nel src si sveglia)."""
    return FileResponse("vendor/nostr.bundle.js",
                        media_type="application/javascript",
                        headers={"Cache-Control": "public, max-age=86400"})


# Le due immagini del brand (redesign lug 2026): mascotte per hero e
# stati vuoti, barattolo per favicon e iconcina del logo. Stesso patto
# di /vendor: rotte esplicite per singolo file, MAI StaticFiles su una
# directory (regola ferrea 3), cache lunga perche' cambiano solo
# quando le cambiamo apposta.
@app.get("/assets/mascotte.jpeg")
def asset_mascotte():
    return FileResponse("assets/mascotte.jpeg", media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/barattolo.jpeg")
def asset_barattolo():
    return FileResponse("assets/barattolo.jpeg", media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/barattolo-hero.png")
def asset_barattolo_hero():
    """Il barattolo scontornato (PNG con trasparenza) per la hero
    desktop: fluttua senza tessera, come nel mockup."""
    return FileResponse("assets/barattolo-hero.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/tappo.jpeg")
def asset_tappo():
    """Il tappo del barattolo (128px, ritagliato sul diametro): e' il
    tasto-avatar del Profilo, reso tondo dal CSS della pagina."""
    return FileResponse("assets/tappo.jpeg", media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


# --- PWA (lug 2026): Barattolo installabile dal browser -------------------
# Stesso patto di /vendor e /assets: rotte esplicite per singolo file,
# MAI StaticFiles su una directory (regola ferrea 3). Dentro la WebView
# di Telegram tutto questo e' inerte: il manifest non attiva nulla da
# solo e il service worker si registra SOLO fuori (guardia in pagina).


@app.get("/manifest.json")
def pwa_manifest():
    """La carta d'identita' dell'app installabile: nome, icone, colori.
    Cache di un'ora: un ritocco si propaga in giornata."""
    return FileResponse("manifest.json",
                        media_type="application/manifest+json",
                        headers={"Cache-Control": "public, max-age=3600"})


@app.get("/sw.js")
def pwa_service_worker():
    """Il service worker, servito dalla RADICE (cosi' il suo raggio
    d'azione copre tutta l'origine). SEMPRE fresco: e' il file che
    governa le cache degli altri, ogni deploy deve vederlo subito."""
    return FileResponse("sw.js", media_type="application/javascript",
                        headers=HEADER_NO_CACHE)


@app.get("/offline.html")
def pwa_offline():
    """La pagina di cortesia a rete morta: la scarica solo il service
    worker quando fa la dispensa, la freschezza non costa nulla."""
    return FileResponse("offline.html", media_type="text/html",
                        headers=HEADER_NO_CACHE)


# Le icone dell'app: generate da genera_icone.py (barattolo su tessera
# arancio; le -maskable hanno il margine per i ritagli di Android).
@app.get("/assets/icona-192.png")
def icona_192():
    return FileResponse("assets/icona-192.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/icona-512.png")
def icona_512():
    return FileResponse("assets/icona-512.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/icona-192-maskable.png")
def icona_192_maskable():
    return FileResponse("assets/icona-192-maskable.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/icona-512-maskable.png")
def icona_512_maskable():
    return FileResponse("assets/icona-512-maskable.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/assets/apple-touch-icon.png")
def icona_apple():
    """L'icona per «Aggiungi alla schermata Home» di iOS (180px, fondo
    pieno: iOS non gestisce la trasparenza e arrotonda da solo)."""
    return FileResponse("assets/apple-touch-icon.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=86400"})


# --- TWA (lug 2026): l'APK Android che incarta il sito --------------------
@app.get("/.well-known/assetlinks.json")
def twa_assetlinks():
    """La stretta di mano tra il dominio e l'APK (Fase 2 della PWA):
    dice ad Android che l'app firmata con la NOSTRA chiave puo' aprire
    barattolo.store a tutto schermo, senza barra del browser. Dentro
    c'e' solo l'impronta PUBBLICA del certificato di firma (la chiave
    vera vive fuori dal repo, coi suoi backup). Stesso patto di sempre:
    rotta esplicita per file singolo (regola ferrea 3). Cache di
    un'ora come il manifest: un cambio d'impronta si propaga presto."""
    return FileResponse(".well-known/assetlinks.json",
                        media_type="application/json",
                        headers={"Cache-Control": "public, max-age=3600"})


app.mount("/foto", StaticFiles(directory=FOTO_DIR), name="foto")
