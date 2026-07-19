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
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import sqlite3
import ssl
import sys
import time
import unicodedata
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
    # Migrazioni annunci: foto, contatto Nostr e l'evento NIP-99
    # pubblicato dalla piattaforma
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''",
                    "nostr_event_id TEXT DEFAULT ''"):
        try:
            con.execute(f"ALTER TABLE annunci ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
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
                    "sollecito_il INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE ordini ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
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
    2) npub gia' VERIFICATA (badge 🟣✓) su UN account Telegram non
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
        # Il browser dell'utente Nostr resta loggato: le sue sessioni
        # migrano vive e al prossimo /api/me si risveglia qui.
        con.execute("UPDATE sessioni SET tg_id=? WHERE tg_id=?",
                    (id_telegram, id_nostr))
        # PRIMA muore la riga Nostr, POI la chiave si accende su quella
        # Telegram: l'indice unico su npub_accesso non ammette il
        # doppio valore nemmeno per un istante.
        con.execute("DELETE FROM utenti WHERE tg_id=?", (id_nostr,))
        con.execute(
            "UPDATE utenti SET npub=?, npub_verificata=1, npub_accesso=?, "
            "verifica_codice='', verifica_scade=0, "
            "ln_address=CASE WHEN ln_address!='' THEN ln_address ELSE ? END, "
            "vendite_ok=vendite_ok+?, acquisti_ok=acquisti_ok+?, "
            # rating: resta quello di P — le stelle non esistono ancora,
            # quando arriveranno andra' deciso come pesare i due passati
            "n_feedback=n_feedback+? WHERE tg_id=?",
            (n["npub"], n["npub_accesso"], n["ln_address"],
             n["vendite_ok"], n["acquisti_ok"], n["n_feedback"],
             id_telegram))
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
    await modifica(
        "🎉 <b>Fatto! I tuoi due account ora sono uno.</b>\n"
        f"Sono passati di qua {esito['annunci']} annunci e "
        f"{esito['ordini']} affari. Il link del tuo negozio ora e' "
        f"{URL_PUBBLICO}/negozio/{esito['negozio']} e gli avvisi "
        "Telegram arrivano anche per gli affari nati su Nostr.\n"
        "ℹ️ Se pubblicavi gli stessi oggetti anche dal tuo profilo "
        "Nostr, ora potresti avere qualche doppione sui relay.")
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


def salva_foto(annuncio_id: int, foto_lista: list) -> list:
    """Salva le foto dell'annuncio (arrivano dalla Mini App gia'
    ridimensionate, in formato base64). Ritorna i nomi dei file."""
    nomi = []
    for i, f in enumerate((foto_lista or [])[:5]):     # max 5 foto
        m = re.match(r"data:image/(jpeg|jpg|png|webp);base64,(.+)",
                     f or "", re.S)
        if not m:
            continue
        try:
            raw = base64.b64decode(m.group(2))
        except Exception:
            continue
        if len(raw) > 2_500_000:                       # max ~2.5MB l'una
            continue
        nome = f"a{annuncio_id}_{i}.jpg"
        with open(os.path.join(FOTO_DIR, nome), "wb") as out:
            out.write(raw)
        nomi.append(nome)
    return nomi


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


# La vetrina e' PUBBLICA (si guarda anche dal browser, senza Telegram):
# questi sono gli UNICI campi che escono verso gli anonimi. Niente
# venditore_id: l'ID Telegram del venditore non appare mai in vetrina.
# La npub invece e' pubblica per natura: e' fatta per essere condivisa.
CAMPI_VETRINA = (
    "a.id, a.titolo, a.descrizione, a.categoria, a.prezzo_sats, a.zona, "
    "a.foto, a.contatto_nostr, a.creato, "
    "u.nome AS venditore, u.username AS venditore_username, "
    "u.npub AS venditore_npub, u.npub_verificata AS venditore_npub_verificata, "
    "u.negozio AS venditore_negozio, "
    "u.rating, u.vendite_ok")


@app.get("/api/listings")
def lista_annunci(cat: str = "", x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    user = utente_se_autenticato(x_tg_init_data, barattolo_sessione)
    # venditore_id serve alla Mini App per "questo annuncio e' tuo"
    campi = CAMPI_VETRINA + (", a.venditore_id" if user else "")
    con = db()
    q = (f"SELECT {campi} FROM annunci a "
         "JOIN utenti u ON u.tg_id = a.venditore_id WHERE a.stato='attivo'")
    par = []
    if cat and cat != "Tutto":
        q += " AND a.categoria=?"
        par.append(cat)
    righe = [dict(r) for r in con.execute(q + " ORDER BY a.creato DESC", par)]
    con.close()
    return righe


@app.post("/api/listings")
async def pubblica(req: Request, x_tg_init_data: str = Header(""),
                                 barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    d = await leggi_json(req)
    if not d.get("titolo") or not int(d.get("prezzo_sats", 0)):
        raise HTTPException(400, "Titolo e prezzo obbligatori")

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
        "prezzo_sats,zona,creato) VALUES(?,?,?,?,?,?,?)",
        (user["id"], d["titolo"], d.get("descrizione", ""), d.get("categoria", "Altro"),
         int(d["prezzo_sats"]), d.get("zona", ""), int(time.time())))
    annuncio_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    nomi = salva_foto(annuncio_id, d.get("foto"))
    if nomi:
        con.execute("UPDATE annunci SET foto=? WHERE id=?",
                    (json.dumps(nomi), annuncio_id))
    con.commit()
    con.close()
    # --- Strato 3: i moderatori vedono tutto cio' che entra in vetrina ---
    await notifica_admin(
        f"🆕 <b>Nuovo annuncio #{annuncio_id}</b>\n"
        f"«{d['titolo'][:80]}» — {int(d['prezzo_sats'])} sats\n"
        f"Venditore: {user['first_name']} (id {user['id']})")
    # E parte anche verso la piazza Nostr, in sottofondo: se i relay
    # tacciono, chi pubblica non se ne accorge nemmeno.
    asyncio.create_task(annuncio_su_nostr(annuncio_id, "active"))
    return {"ok": True, "id": annuncio_id}


@app.get("/api/listings/miei")
def miei_annunci(x_tg_init_data: str = Header(""),
                 barattolo_sessione: str = Cookie("")):
    """Gli annunci attivi dell'utente che chiede (per gestirli)."""
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    righe = [dict(r) for r in con.execute(
        "SELECT a.*, u.nome AS venditore, u.username AS venditore_username, "
        "u.npub AS venditore_npub, "
        "u.npub_verificata AS venditore_npub_verificata, "
        "u.negozio AS venditore_negozio, "
        "u.rating, u.vendite_ok FROM annunci a "
        "JOIN utenti u ON u.tg_id=a.venditore_id "
        "WHERE a.venditore_id=? AND a.stato='attivo' ORDER BY a.creato DESC",
        (user["id"],))]
    con.close()
    return righe


@app.get("/api/negozio/{chi}")
def negozio(chi: str, x_tg_init_data: str = Header(""),
                      barattolo_sessione: str = Cookie("")):
    """La pagina-negozio di un venditore: profilo pubblico + i suoi
    annunci attivi. Si arriva con lo username Telegram (se ce l'ha) o
    col codice pubblico del negozio: mai col tg_id, che agli anonimi
    resta invisibile come in tutta la vetrina."""
    user = utente_se_autenticato(x_tg_init_data, barattolo_sessione)
    con = db()
    campi_profilo = ("SELECT tg_id, nome, username, npub, npub_verificata, "
                     "rating, vendite_ok, negozio FROM utenti ")
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
    annunci = [dict(r) for r in con.execute(
        f"SELECT {campi} FROM annunci a "
        "JOIN utenti u ON u.tg_id=a.venditore_id "
        "WHERE a.venditore_id=? AND a.stato='attivo' ORDER BY a.creato DESC",
        (v["tg_id"],))]
    con.close()
    venditore = dict(v)
    del venditore["tg_id"]         # il profilo che esce e' solo roba pubblica
    return {"venditore": venditore, "annunci": annunci}


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

@app.get("/api/search")
def cerca(q: str, x_tg_init_data: str = Header(""),
                  barattolo_sessione: str = Cookie("")):
    """Ricerca in linguaggio naturale: l'AI legge la richiesta
    ("tastiera sotto i 100k vicino Milano") e seleziona gli annunci."""
    verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    annunci = [dict(r) for r in con.execute(
        "SELECT a.*, u.nome AS venditore, u.username AS venditore_username, "
        "u.npub AS venditore_npub, "
        "u.npub_verificata AS venditore_npub_verificata, "
        "u.negozio AS venditore_negozio, "
        "u.rating FROM annunci a "
        "JOIN utenti u ON u.tg_id=a.venditore_id WHERE a.stato='attivo'")]
    con.close()
    if not annunci:
        return []

    catalogo = "\n".join(
        f"ID {a['id']}: {a['titolo']} | {a['categoria']} | "
        f"{a['prezzo_sats']} sats | {a['zona']} | {a['descrizione'][:120]}"
        for a in annunci)
    try:
        r = ai.messages.create(
            model=MODELLO_RICERCA, max_tokens=200,
            system=("Sei il motore di ricerca di un mercatino. Data la richiesta "
                    "dell'utente e il catalogo, rispondi SOLO con un array JSON "
                    "degli ID pertinenti, dal piu' rilevante. Capisci sinonimi "
                    "(bici=mtb=bicicletta) e vincoli di prezzo/zona. "
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

    inv = await crea_invoice_escrow(
        a["prezzo_sats"], f"Barattolo escrow #{a['id']}: {a['titolo'][:40]}")
    con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,prezzo_sats,"
        "stato,payment_hash,creato,aggiornato) VALUES(?,?,?,?,?,?,?,?)",
        (a["id"], user["id"], a["venditore_id"], a["prezzo_sats"],
         "creato", inv["payment_hash"], int(time.time()), int(time.time())))
    con.commit()
    ordine_id = con.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    con.close()
    return {"ordine_id": ordine_id, "invoice": inv["payment_request"],
            "payment_hash": inv["payment_hash"]}


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

@app.get("/api/me")
def mio_profilo(x_tg_init_data: str = Header(""),
                barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
    con.close()
    profilo = dict(u) if u else {}
    profilo["admin"] = e_admin(user["id"])
    return profilo


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
                   "🟣✓ <b>npub verificata!</b> Da adesso i tuoi annunci "
                   "portano il badge dei venditori verificati su Nostr. 🎉 "
                   "(La nota col codice ora puoi anche cancellarla.)")
    return {"ok": True, "verificata": True}


# --- Doppia cittadinanza: il badge diventa chiave d'ingresso ---------
# Un utente Telegram con la npub VERIFICATA puo' promuoverla a chiave
# d'accesso (npub_accesso): da quel momento entra nello STESSO account
# anche dal web col login Nostr. Il badge non verificato non basta mai:
# potrebbe essere la dichiarazione (falsa) di una chiave altrui.

@app.post("/api/me/npub/abilita-accesso")
def abilita_accesso_nostr(x_tg_init_data: str = Header(""),
                          barattolo_sessione: str = Cookie("")):
    user = verifica_utente(x_tg_init_data, barattolo_sessione)
    con = db()
    u = con.execute(
        "SELECT npub, npub_verificata, npub_accesso FROM utenti "
        "WHERE tg_id=?", (user["id"],)).fetchone()
    if not u or not u["npub"] or not u["npub_verificata"]:
        con.close()
        raise HTTPException(400, "Prima verifica la tua npub (badge 🟣✓): "
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
    tags = [["d", f"barattolo-{a['id']}"],
            ["title", a["titolo"]],
            ["summary", (a["descrizione"] or a["titolo"])[:200]],
            ["price", str(a["prezzo_sats"]), "sats"],
            ["status", status],
            ["published_at", str(a["creato"])],
            ["r", URL_PUBBLICO]]
    if a.get("categoria"):
        tags.append(["t", a["categoria"].lower()])
    if a.get("zona"):
        tags.append(["location", a["zona"]])
    for url in _foto_url_nostr(a.get("foto", "")):
        tags.append(["image", url])
    content = ((a["descrizione"] or a["titolo"]).strip() +
               f"\n\nPrezzo: {a['prezzo_sats']} sats — zona: "
               f"{a.get('zona') or 'Italia'}"
               f"\n\n🫙⚡ In vendita su Barattolo, il mercatino in sats "
               f"con escrow Lightning: {URL_PUBBLICO} · {LINK_BOT}")
    return firma_evento(30402, tags, content)


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


async def _spedisci_ai_relay(evento: dict) -> int:
    """Manda l'evento a tutti i relay in parallelo (ognuno nel suo
    thread) e ritorna quanti l'hanno accettato. Nel collaudo non esce
    nulla dal computer: l'evento si stampa e basta."""
    if MODALITA_COLLAUDO:
        print(f"🟣 [nostr simulato] "
              f"{json.dumps(evento, ensure_ascii=False)[:400]}…")
        return len(RELAYS_VERIFICA)
    esiti = await asyncio.gather(*[
        asyncio.to_thread(invia_evento_relay, r, evento)
        for r in RELAYS_VERIFICA])
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


async def ritira_da_nostr(annuncio_id: int):
    """Chiede ai relay di cancellare l'evento di un annuncio rimosso
    (NIP-09, kind 5). Come sopra: sottofondo, mai errori all'utente."""
    if not _NOSTR:
        return
    try:
        con = db()
        a = con.execute("SELECT nostr_event_id FROM annunci WHERE id=?",
                        (annuncio_id,)).fetchone()
        con.close()
        if not a or not a["nostr_event_id"]:
            return
        evento = firma_evento(5, [
            ["e", a["nostr_event_id"]],
            ["a", f"30402:{_NOSTR[1]}:barattolo-{annuncio_id}"],
            ["k", "30402"]],
            "Annuncio rimosso da Barattolo")
        ok = await _spedisci_ai_relay(evento)
        con = db()
        con.execute("UPDATE annunci SET nostr_event_id='' WHERE id=?",
                    (annuncio_id,))
        con.commit()
        con.close()
        print(f"🟣 Annuncio #{annuncio_id} ritirato da Nostr "
              f"({ok}/{len(RELAYS_VERIFICA)} relay)")
    except Exception as e:
        print(f"⚠️ Ritiro Nostr saltato per l'annuncio #{annuncio_id}: {e}")


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
            con.execute("UPDATE ordini SET stato='released', aggiornato=? WHERE id=?",
                        (int(time.time()), ordine_id))
            con.execute("UPDATE utenti SET vendite_ok=vendite_ok+1 WHERE tg_id=?",
                        (o["venditore_id"],))
            con.execute("UPDATE utenti SET acquisti_ok=acquisti_ok+1 WHERE tg_id=?",
                        (o["compratore_id"],))
            con.commit()
            con.close()
            if automatico:
                await notifica(o["venditore_id"],
                               f"🔓 <b>Sats sbloccati automaticamente!</b> Il tempo di "
                               f"conferma è scaduto senza problemi segnalati: "
                               f"<b>{netto} sats</b> sono in arrivo nel tuo wallet. ⚡")
                await notifica(o["compratore_id"],
                               f"✅ <b>Affare concluso:</b> «{titolo}». Il tempo per "
                               f"confermare o aprire una disputa è scaduto e i sats "
                               f"sono stati sbloccati al venditore. Grazie per aver "
                               f"usato Barattolo 🫙")
            else:
                await notifica(o["venditore_id"],
                               f"🔓 <b>Sats sbloccati!</b> L'acquirente ha confermato la "
                               f"ricezione: <b>{netto} sats</b> sono in arrivo nel tuo "
                               f"wallet. Affare concluso! ⚡")
                await notifica(o["compratore_id"],
                               f"✅ <b>Affare concluso:</b> «{titolo}». "
                               f"Grazie per aver usato Barattolo 🫙")
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
            con.execute("UPDATE ordini SET stato='refunded', aggiornato=? WHERE id=?",
                        (int(time.time()), ordine_id))
            con.execute("UPDATE annunci SET stato='attivo' WHERE id=?",
                        (o["annuncio_id"],))      # l'oggetto torna in vetrina
            con.commit()
            con.close()
            # ...e torna disponibile anche sulla piazza Nostr
            asyncio.create_task(annuncio_su_nostr(o["annuncio_id"], "active",
                                                  solo_aggiornamento=True))
            await notifica(o["compratore_id"],
                           f"↩️ <b>Disputa risolta a tuo favore:</b> il rimborso di "
                           f"<b>{importo} sats</b> è in arrivo nel tuo wallet.")
            await notifica(o["venditore_id"],
                           "⚖️ La disputa è stata risolta a favore dell'acquirente: "
                           "i sats gli sono stati rimborsati e l'annuncio è tornato "
                           "in vetrina.")
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
    con.execute("UPDATE ordini SET stato='dispute', aggiornato=? WHERE id=?",
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
         "uv.username AS venditore_username FROM ordini o "
         "JOIN annunci a ON a.id=o.annuncio_id "
         "JOIN utenti uc ON uc.tg_id=o.compratore_id "
         "JOIN utenti uv ON uv.tg_id=o.venditore_id "
         "WHERE o.compratore_id=? OR o.venditore_id=?")
    par = [user["id"], user["id"]]
    if e_admin(user["id"]):
        # I moderatori vedono dispute e resi in corso
        q += (" OR o.stato IN ('dispute','return_pending',"
              "'return_shipped','refund')")
    righe = [dict(r) for r in con.execute(q + " ORDER BY o.aggiornato DESC",
                                          par)]
    con.close()
    return righe


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


app.mount("/foto", StaticFiles(directory=FOTO_DIR), name="foto")
