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
# "fiducia" = si mostra anche nel negozio pubblico, accanto al nome.

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
         descrizione="Il primo acquisto concluso via escrow",
         criterio=lambda d: d["acquisti"] >= 1),
    dict(id="primo_baratto", emoji="🤝", nome="Primo baratto",
         fiducia=False,
         descrizione="La prima vendita conclusa via escrow",
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
                    "canale_notifiche TEXT DEFAULT ''"):
        try:
            con.execute(f"ALTER TABLE utenti ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
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
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''",
                    "nostr_event_id TEXT DEFAULT ''",
                    "valuta TEXT DEFAULT 'sats'",
                    "prezzo_eur REAL DEFAULT 0",
                    "nostr_origine_d TEXT DEFAULT ''",
                    "nostr_origine_foto TEXT DEFAULT ''"):
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
                    # CREAZIONE della invoice (solo annunci in EUR:
                    # e' il cambio che ha fissato i sats dell'ordine).
                    # 0 = annuncio in sats, nessuna conversione.
                    "cambio_ordine REAL DEFAULT 0"):
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


async def bot_api(metodo: str, dati: dict):
    """Chiama l'API del bot (sendMessage con tastiere,
    answerCallbackQuery, editMessageText...). In collaudo stampa e
    basta, SEMPRE — a differenza di notifica(), che simula solo gli
    id piccoli degli utenti finti."""
    if MODALITA_COLLAUDO:
        print(f"🤖 [telegram simulato] {metodo} "
              f"{json.dumps(dati, ensure_ascii=False)}")
        return
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            await c.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/{metodo}",
                json=dati)
    except Exception as e:
        print(f"⚠️ Bot Telegram, {metodo} non consegnato: {e}")


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
                    "avviso quando succede qualcosa nei tuoi affari. "
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
    "a.foto, a.contatto_nostr, a.creato, "
    "u.nome AS venditore, u.username AS venditore_username, "
    "u.npub AS venditore_npub, u.npub_verificata AS venditore_npub_verificata, "
    "u.negozio AS venditore_negozio, "
    "(SELECT GROUP_CONCAT(b.badge_id) FROM badge_utente b "
    " WHERE b.tg_id=a.venditore_id) AS venditore_distintivi, "
    "u.rating, u.vendite_ok")


def espandi_distintivi_vetrina(righe):
    """Il GROUP_CONCAT dei badge diventa la lista di chip di FIDUCIA
    {id, emoji, nome, descrizione} — gli stessi del negozio pubblico:
    la Mini App non hardcoda mai il catalogo, e i distintivi non di
    fiducia verso la vetrina non escono proprio."""
    for r in righe:
        presi = set((r.pop("venditore_distintivi", "") or "").split(","))
        r["venditore_distintivi"] = [
            dict(id=d["id"], emoji=d["emoji"], nome=d["nome"],
                 descrizione=d["descrizione"])
            for d in DISTINTIVI if d["fiducia"] and d["id"] in presi]
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


@app.get("/api/listings")
async def lista_annunci(cat: str = "", q: str = "", limit: int = 0,
                        cursore: str = "", ordina: str = "",
                        prezzo_min: float = 0, prezzo_max: float = 0,
                        valuta_filtro: str = "sats",
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
    con.close()
    return risposta


@app.post("/api/listings")
async def pubblica(req: Request, x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    valuta, prezzo_sats, prezzo_eur = await prezzo_da_payload(d)

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
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,valuta,prezzo_eur,creato) VALUES(?,?,?,?,?,?,?,?,?)",
        (user["id"], d["titolo"], d.get("descrizione", ""), categoria_valida(d.get("categoria")),
         prezzo_sats, d.get("zona", ""), valuta, prezzo_eur, int(time.time())))
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
                     "rating, n_feedback, vendite_ok, negozio FROM utenti ")
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
    # Sul profilo pubblico solo i distintivi "di fiducia": gli altri
    # affollerebbero e raccontano piu' del percorso che dell'affidabilita'
    presi = {r["badge_id"] for r in con.execute(
        "SELECT badge_id FROM badge_utente WHERE tg_id=?", (v["tg_id"],))}
    con.close()
    venditore = dict(v)
    venditore["distintivi"] = [
        dict(id=d["id"], emoji=d["emoji"], nome=d["nome"],
             descrizione=d["descrizione"])
        for d in DISTINTIVI if d["fiducia"] and d["id"] in presi]
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
    con.execute(
        "UPDATE annunci SET titolo=?, descrizione=?, categoria=?, "
        "prezzo_sats=?, zona=?, valuta=?, prezzo_eur=? WHERE id=?",
        (d["titolo"], d.get("descrizione", ""), categoria_valida(d.get("categoria")),
         prezzo_sats, d.get("zona", ""), valuta, prezzo_eur, annuncio_id))
    con.commit()
    con.close()
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
    con.execute(
        "UPDATE annunci SET titolo=?, descrizione=?, categoria=?, "
        "prezzo_sats=?, zona=?, valuta=?, prezzo_eur=? WHERE id=?",
        (b["titolo"], b["descrizione"], b["categoria"], b["prezzo_sats"],
         b["zona"], b["valuta"], b["prezzo_eur"], annuncio_id))
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

    # Per gli annunci in EUR i sats si decidono ADESSO, al cambio
    # corrente: la invoice vive 15 minuti, e quella e' la durata del
    # prezzo bloccato. Se scade, il prossimo tentativo riconverte.
    sats, cambio_ordine = a["prezzo_sats"], 0.0
    if a["valuta"] == "eur" and a["prezzo_eur"] > 0:
        cambio_ordine = await cambio_btc_eur()
        if cambio_ordine <= 0:
            con.close()
            raise HTTPException(503, "Il cambio euro non è disponibile in "
                                     "questo momento: riprova tra qualche "
                                     "minuto")
        sats = max(1, round(a["prezzo_eur"] / cambio_ordine * 100_000_000))
        # Il tetto di rodaggio con +20% di tolleranza: la volatilita'
        # ordinaria passa, un crollo del cambio no — e il venditore
        # si ripara da solo ritoccando il prezzo (la modifica
        # riconvalida al cambio di oggi).
        if TETTO_SATS_ANNUNCIO and sats > TETTO_SATS_ANNUNCIO * 1.2:
            con.close()
            await notifica(a["venditore_id"],
                f"📈 Il cambio si è mosso troppo: il tuo annuncio "
                f"«{a['titolo'][:60]}» ({a['prezzo_eur']:.2f} EUR) supera "
                f"ora il tetto di {TETTO_SATS_ANNUNCIO} sats e gli acquisti "
                f"sono in pausa. Ritocca il prezzo per riaprirli.")
            raise HTTPException(409, "Il cambio è cambiato troppo da quando "
                                     "l'annuncio è stato pubblicato: il "
                                     "venditore deve ritoccare il prezzo")

    inv = await crea_invoice_escrow(
        sats, f"Barattolo escrow #{a['id']}: {a['titolo'][:40]}")
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,prezzo_sats,"
        "stato,payment_hash,creato,aggiornato,cambio_ordine) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (a["id"], user["id"], a["venditore_id"], sats,
         "creato", inv["payment_hash"], int(time.time()), int(time.time()),
         cambio_ordine))
    con.commit()
    ordine_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.close()
    return {"ordine_id": ordine_id, "invoice": inv["payment_request"],
            "payment_hash": inv["payment_hash"], "prezzo_sats": sats}


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
        a = con.execute("SELECT contatto_nostr FROM annunci WHERE id=?",
                        (o["annuncio_id"],)).fetchone()
        con.commit()
        # Anche la piazza Nostr deve sapere che l'oggetto e' andato
        asyncio.create_task(annuncio_su_nostr(o["annuncio_id"], "sold",
                                              solo_aggiornamento=True))
        msg = ("🔒 <b>Hai venduto!</b> I sats dell'acquirente sono in escrow. "
               "Spedisci l'oggetto e segna l'ordine come spedito nella Mini App. 📦")
        if a and a["contatto_nostr"]:
            msg += ("\n\n🟣 Questo annuncio è pubblicato anche su <b>Nostr</b>: "
                    "ricordati di segnarlo come <b>venduto (sold)</b> dal tuo "
                    "client, così nessun altro proverà a comprarlo lì.")
        await notifica(o["venditore_id"], msg)
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
    if corriere != "Consegna a mano" and not tracking:
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


@app.get("/api/me")
def mio_profilo(x_tg_init_data: str = Header(""),
                barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
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
    con.close()
    profilo = dict(u) if u else {}
    profilo["admin"] = e_admin(user["id"])
    profilo["doppioni_nostr"] = doppioni
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
    verificata = bool(attuale and attuale["npub_verificata"])
    accesso_revocato = False
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
    con.commit()
    con.close()
    return {"ok": True, "npub": npub, "npub_verificata": verificata,
            "accesso_revocato": accesso_revocato}


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
    content = ((a["descrizione"] or a["titolo"]).strip() +
               f"\n\nPrezzo: {prezzo_txt} — zona: "
               f"{a.get('zona') or 'Italia'}"
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
        ruolo, atteso, colonna = "venditore", netto_venditore(o["prezzo_sats"]), \
            "invoice_venditore"
        spiegazione = f"{atteso} sats (prezzo meno l'1%)"
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
        netto = netto_venditore(o["prezzo_sats"])

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
                   "sicuro in escrow: apri l'ordine nella Mini App per riprovare "
                   f"con una invoice da <b>{netto} sats</b>.")
        else:
            msg = (f"✅ <b>L'acquirente ha confermato la ricezione!</b> Per incassare "
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
        importo = o["prezzo_sats"]      # rimborso integrale, zero commissioni

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
            con.close()
            # ...e torna disponibile anche sulla piazza Nostr
            asyncio.create_task(annuncio_su_nostr(o["annuncio_id"], "active",
                                                  solo_aggiornamento=True))
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
                   "vi contattera' entrambi. I sats restano in escrow.")
    return {"ok": True}


def pulisci_ordini_fantasma(con):
    """Elimina gli ordini MAI PAGATI piu' vecchi di 30 minuti: la loro
    invoice e' scaduta (15 min), quindi non possono piu' progredire.
    Nessun sat e' coinvolto, e' solo pulizia."""
    con.execute("DELETE FROM ordini WHERE stato='creato' AND creato < ?",
                (int(time.time()) - 1800,))


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
    importati, aggiornati, saltati = await asyncio.to_thread(
        importa_nostr.importa_venditore, NPUB_VENDITORE, VENDITORE_ID, DB)
    print(f"🔄 Import Nostr: {importati} nuovi, {aggiornati} aggiornati, "
          f"{saltati} saltati")


async def orologio():
    while True:
        try:
            await controlla_scadenze()
        except Exception as e:
            print(f"Orologio sblocchi, errore (riprovo tra 10 min): {e}")
        try:
            await importa_nostr_periodico()
        except Exception as e:
            print(f"⚠️ Import Nostr periodico saltato (riprovo tra "
                  f"un'ora): {e}")
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


app.mount("/foto", StaticFiles(directory=FOTO_DIR), name="foto")
