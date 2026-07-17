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
AVVIO:      uvicorn server:app --host 0.0.0.0 --port 8080
            (serve HTTPS pubblico per la Mini App: vedi LEGGIMI.md)
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import ssl
import sys
import time
import unicodedata
from urllib.parse import parse_qsl

import anthropic
import httpx
from fastapi import FastAPI, Header, HTTPException, Request

# websocket-client serve solo alla verifica npub: se manca il pacchetto
# il server parte lo stesso e la verifica risponde con un errore chiaro.
try:
    from websocket import create_connection
except ImportError:
    create_connection = None
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

# ===================================================================

app = FastAPI(title="Barattolo API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ------------------------- DATABASE --------------------------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


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
        vendite_ok INTEGER DEFAULT 0, acquisti_ok INTEGER DEFAULT 0,
        rating REAL DEFAULT 0, n_feedback INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS annunci(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venditore_id INTEGER, titolo TEXT, descrizione TEXT,
        categoria TEXT, prezzo_sats INTEGER, zona TEXT,
        foto TEXT DEFAULT '',              -- lista JSON: nomi file o URL
        contatto_nostr TEXT DEFAULT '',    -- npub del venditore (annunci importati)
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
    """)
    # Migrazione per database creati prima dell'introduzione degli
    # incassi automatici: aggiunge la colonna se manca.
    try:
        con.execute("ALTER TABLE utenti ADD COLUMN ln_address TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # Migrazioni per il badge Nostr (npub del profilo e sua verifica)
    for colonna in ("npub TEXT DEFAULT ''",
                    "npub_verificata INTEGER DEFAULT 0",
                    "verifica_codice TEXT DEFAULT ''",
                    "verifica_scade INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE utenti ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    # Migrazioni per foto e contatto Nostr degli annunci
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''"):
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

def verifica_utente(init_data: str) -> dict:
    # --- MODALITA' COLLAUDO: utenti finti per il test dal browser ---
    if MODALITA_COLLAUDO and init_data.startswith("collaudo:"):
        _, uid, nome = init_data.split(":", 2)
        user = {"id": int(uid), "first_name": nome, "username": nome.lower()}
        con = db()
        con.execute(
            "INSERT INTO utenti(tg_id, nome, username) VALUES(?,?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET nome=?, username=?",
            (user["id"], nome, nome.lower(), nome, nome.lower()))
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
            "INSERT INTO utenti(tg_id, nome, username) VALUES(?,?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET nome=?, username=?",
            (user["id"], user.get("first_name", ""), user.get("username", ""),
             user.get("first_name", ""), user.get("username", "")))
        con.commit()
        con.close()
        return user
    except Exception:
        raise HTTPException(401, "Autenticazione Telegram non valida")


def utente_se_autenticato(init_data: str) -> dict | None:
    """Autenticazione FACOLTATIVA, solo per le API di vetrina: chi
    arriva da Telegram (o dal collaudo) viene riconosciuto, chi guarda
    dal browser resta anonimo e viene servito lo stesso."""
    if not init_data:
        return None
    try:
        return verifica_utente(init_data)
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


async def notifica(tg_id: int, testo: str):
    """Manda un messaggio Telegram (il bot deve essere stato avviato
    dall'utente almeno una volta)."""
    if MODALITA_COLLAUDO and tg_id < 100000:
        # Utente finto del collaudo: la notifica si stampa in console
        print(f"📨 [notifica simulata per utente {tg_id}] {testo}")
        return
    async with httpx.AsyncClient() as c:
        await c.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     json={"chat_id": tg_id, "text": testo, "parse_mode": "HTML"})


async def notifica_admin(testo: str):
    """Avvisa tutti i moderatori (nel collaudo anche l'identita' 999,
    che stampa in console come le altre notifiche simulate)."""
    destinatari = set(ADMIN_IDS)
    if MODALITA_COLLAUDO:
        destinatari.add(999)
    for tg_id in destinatari:
        await notifica(tg_id, testo)


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
    "u.rating, u.vendite_ok")


@app.get("/api/listings")
def lista_annunci(cat: str = "", x_tg_init_data: str = Header("")):
    user = utente_se_autenticato(x_tg_init_data)
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
async def pubblica(req: Request, x_tg_init_data: str = Header("")):
    user = verifica_utente(x_tg_init_data)
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
    return {"ok": True, "id": annuncio_id}


@app.get("/api/listings/miei")
def miei_annunci(x_tg_init_data: str = Header("")):
    """Gli annunci attivi dell'utente che chiede (per gestirli)."""
    user = verifica_utente(x_tg_init_data)
    con = db()
    righe = [dict(r) for r in con.execute(
        "SELECT a.*, u.nome AS venditore, u.username AS venditore_username, "
        "u.npub AS venditore_npub, "
        "u.npub_verificata AS venditore_npub_verificata, "
        "u.rating, u.vendite_ok FROM annunci a "
        "JOIN utenti u ON u.tg_id=a.venditore_id "
        "WHERE a.venditore_id=? AND a.stato='attivo' ORDER BY a.creato DESC",
        (user["id"],))]
    con.close()
    return righe


@app.post("/api/listings/{annuncio_id}/rimuovi")
async def rimuovi_annuncio(annuncio_id: int, x_tg_init_data: str = Header("")):
    """Cancellazione 'morbida': l'annuncio sparisce dalla vetrina ma
    resta nel database (cosi' gli ordini passati non si rompono e le
    dispute restano ricostruibili). Regole:
    - solo il proprietario puo' rimuovere
    - se c'e' un affare in corso (sats in escrow), prima si chiude quello
    - gli ordini creati ma mai pagati vengono annullati"""
    user = verifica_utente(x_tg_init_data)
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
    return {"ok": True}


@app.post("/api/admin/listings/{annuncio_id}/rimuovi")
async def rimuovi_annuncio_admin(annuncio_id: int,
                                 x_tg_init_data: str = Header("")):
    """SOLO ADMIN (moderazione, strato 3): rimuove un annuncio che
    viola le regole. Stessa cancellazione morbida del proprietario e
    stessa guardia sugli affari in corso: con sats in escrow prima si
    chiude l'ordine (dalla disputa, se serve), poi si rimuove."""
    user = verifica_utente(x_tg_init_data)
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
    await notifica(a["venditore_id"],
                   f"🚫 <b>Il tuo annuncio «{a['titolo'][:60]}» è stato "
                   f"rimosso</b> perché viola le regole del mercatino. "
                   f"Se pensi sia un errore, scrivi ai moderatori.")
    return {"ok": True}


# ---------------------- API: RICERCA AI -----------------------------

@app.get("/api/search")
def cerca(q: str, x_tg_init_data: str = Header("")):
    """Ricerca in linguaggio naturale: l'AI legge la richiesta
    ("tastiera sotto i 100k vicino Milano") e seleziona gli annunci."""
    verifica_utente(x_tg_init_data)
    con = db()
    annunci = [dict(r) for r in con.execute(
        "SELECT a.*, u.nome AS venditore, u.username AS venditore_username, "
        "u.npub AS venditore_npub, "
        "u.npub_verificata AS venditore_npub_verificata, "
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
async def compra(req: Request, x_tg_init_data: str = Header("")):
    """L'acquirente avvia l'acquisto: creiamo la invoice escrow."""
    user = verifica_utente(x_tg_init_data)
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
async def verifica_pagamento(ordine_id: int, x_tg_init_data: str = Header("")):
    """La Mini App chiama questo endpoint dopo il pagamento:
    se la invoice risulta pagata, i sats sono in cassaforte -> LOCKED."""
    verifica_utente(x_tg_init_data)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
    if not o:
        raise HTTPException(404, "Ordine non trovato")
    if o["stato"] != "creato":
        return {"stato": o["stato"]}
    if await invoice_pagata(o["payment_hash"]):
        con.execute("UPDATE ordini SET stato='locked', aggiornato=? WHERE id=?",
                    (int(time.time()), ordine_id))
        con.execute("UPDATE annunci SET stato='venduto' WHERE id=?",
                    (o["annuncio_id"],))
        a = con.execute("SELECT contatto_nostr FROM annunci WHERE id=?",
                        (o["annuncio_id"],)).fetchone()
        con.commit()
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
                        x_tg_init_data: str = Header("")):
    """Il venditore segna la spedizione, con corriere e numero di
    tracciamento (l'acquirente li vedrà). Da qui parte il timer di
    sblocco d'ufficio: se dopo GIORNI_AUTO_SBLOCCO nessuno segnala
    nulla, i sats vanno al venditore."""
    user = verifica_utente(x_tg_init_data)
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
async def segna_consegnato(ordine_id: int, x_tg_init_data: str = Header("")):
    """SOLO L'ACQUIRENTE segnala l'arrivo del pacco: si apre la sua
    finestra di ORE_CONFERMA ore per controllare l'oggetto; allo
    scadere, sblocco automatico al venditore.
    (Il venditore NON puo' usarlo: potrebbe far partire il timer
    prima della consegna reale. La sua protezione e' lo sblocco
    d'ufficio a GIORNI_AUTO_SBLOCCO giorni. In futuro questo scatto
    arrivera' in automatico dal tracking del corriere.)"""
    user = verifica_utente(x_tg_init_data)
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
async def sollecita_acquirente(ordine_id: int, x_tg_init_data: str = Header("")):
    """Il venditore invia un promemoria Telegram all'acquirente
    (massimo uno ogni 24 ore, per non trasformarlo in molestia)."""
    user = verifica_utente(x_tg_init_data)
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
def mio_profilo(x_tg_init_data: str = Header("")):
    user = verifica_utente(x_tg_init_data)
    con = db()
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (user["id"],)).fetchone()
    con.close()
    profilo = dict(u) if u else {}
    profilo["admin"] = e_admin(user["id"])
    return profilo


@app.post("/api/me/ln-address")
async def salva_ln_address(req: Request, x_tg_init_data: str = Header("")):
    """Il venditore imposta (una volta sola) il suo Lightning address:
    da quel momento tutti gli incassi sono AUTOMATICI. Prima di
    salvarlo lo verifichiamo dal vivo con una richiesta di prova.
    Se il venditore ha ordini gia' confermati in attesa, i sats
    partono immediatamente."""
    user = verifica_utente(x_tg_init_data)
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
# verifica di proprieta' con firma di sfida e' un cantiere futuro).
RE_NPUB = re.compile(r"^npub1[023456789acdefghjklmnpqrstuvwxyz]{58}$")


@app.post("/api/me/npub")
async def salva_npub(req: Request, x_tg_init_data: str = Header("")):
    """Badge Nostr del profilo: l'utente dichiara la sua npub (chiave
    PUBBLICA) e i suoi annunci mostrano il badge. Stringa vuota = rimozione.
    REGOLA FERREA: mai chiedere ne' accettare nsec (chiavi private)."""
    user = verifica_utente(x_tg_init_data)
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
        "SELECT npub, npub_verificata FROM utenti WHERE tg_id=?",
        (user["id"],)).fetchone()
    verificata = bool(attuale and attuale["npub_verificata"])
    if not attuale or npub != attuale["npub"]:
        # npub nuova, cambiata o rimossa: la verifica riparte da zero
        verificata = False
        con.execute(
            "UPDATE utenti SET npub=?, npub_verificata=0, "
            "verifica_codice='', verifica_scade=0 WHERE tg_id=?",
            (npub, user["id"]))
    con.commit()
    con.close()
    return {"ok": True, "npub": npub, "npub_verificata": verificata}


# --- Verifica della npub con una nota pubblica -----------------------
# L'utente dimostra di POSSEDERE la npub pubblicando dal suo client una
# nota (kind 1) con un codice generato da noi. Nessuna nsec, nessuna
# firma da consegnare, MAI (regola ferrea): solo una nota pubblica, che
# dopo la verifica puo' anche cancellare senza conseguenze.
# Relay e conversione bech32->hex sono lo specchio di importa_nostr.py
# (che non si puo' importare: pretende NPUB_VENDITORE in config.py).

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
async def verifica_npub_avvia(x_tg_init_data: str = Header("")):
    """Primo passo: generiamo il codice univoco da pubblicare in una
    nota Nostr. Vale 1 ora."""
    user = verifica_utente(x_tg_init_data)
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
async def verifica_npub_controlla(x_tg_init_data: str = Header("")):
    """Secondo passo: cerchiamo sui relay una nota recente della npub
    che contenga il codice. Trovata = la npub e' davvero sua."""
    user = verifica_utente(x_tg_init_data)
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


@app.post("/api/orders/{ordine_id}/invoice")
async def deposita_invoice(ordine_id: int, req: Request,
                           x_tg_init_data: str = Header("")):
    """Deposita una invoice Lightning sull'ordine:
    - il VENDITORE (stati locked/shipped/confirmed) per incassare:
      importo = prezzo - commissione; se l'acquirente aveva gia'
      confermato, i sats partono immediatamente
    - l'ACQUIRENTE (stato refund, disputa vinta) per il rimborso:
      importo = prezzo pieno; il rimborso parte immediatamente."""
    user = verifica_utente(x_tg_init_data)
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


async def _sblocca_sats(ordine_id: int, automatico: bool = False) -> dict:
    """Consegna i sats al venditore, provando in ordine:
    1. la invoice che il venditore ha eventualmente depositato
    2. INCASSO AUTOMATICO: il suo Lightning address (se impostato)
    3. altrimenti l'ordine resta 'confirmed' e il venditore viene
       avvisato di fornire una invoice o impostare il suo address.
    Se un pagamento fallisce (es. invoice scaduta), i sats restano
    al sicuro in cassaforte e si riprova con metodo nuovo."""
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
    if not o:
        con.close()
        return {"ok": False, "stato": "?"}
    v = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                    (o["venditore_id"],)).fetchone()
    netto = netto_venditore(o["prezzo_sats"])

    bolt11 = o["invoice_venditore"]
    if not bolt11 and v and v["ln_address"]:
        bolt11 = await invoice_da_ln_address(v["ln_address"], netto)

    if bolt11 and await paga_venditore(bolt11):
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
                           "🔓 L'ordine si è concluso <b>automaticamente</b>: il "
                           "tempo per confermare o aprire una disputa è scaduto e "
                           "i sats sono stati sbloccati al venditore.")
        else:
            await notifica(o["venditore_id"],
                           f"🔓 <b>Sats sbloccati!</b> L'acquirente ha confermato la "
                           f"ricezione: <b>{netto} sats</b> sono in arrivo nel tuo "
                           f"wallet. Affare concluso! ⚡")
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
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=?", (ordine_id,)).fetchone()
    if not o:
        con.close()
        return {"ok": False, "stato": "?"}
    c_utente = con.execute("SELECT * FROM utenti WHERE tg_id=?",
                           (o["compratore_id"],)).fetchone()
    importo = o["prezzo_sats"]          # rimborso integrale, zero commissioni

    bolt11 = o["invoice_rimborso"]
    if not bolt11 and c_utente and c_utente["ln_address"]:
        bolt11 = await invoice_da_ln_address(c_utente["ln_address"], importo)

    if bolt11 and await paga_venditore(bolt11):
        con.execute("UPDATE ordini SET stato='refunded', aggiornato=? WHERE id=?",
                    (int(time.time()), ordine_id))
        con.execute("UPDATE annunci SET stato='attivo' WHERE id=?",
                    (o["annuncio_id"],))          # l'oggetto torna in vetrina
        con.commit()
        con.close()
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
                          x_tg_init_data: str = Header("")):
    """SOLO ADMIN: decide una disputa.
    - esito='venditore': i sats vanno al venditore (meno commissione)
    - esito='rimborso': rimborso immediato all'acquirente (es. oggetto
      mai arrivato)
    - esito='reso': rimborso PREVIA RESTITUZIONE: l'acquirente deve
      rispedire l'oggetto (con tracciamento); il rimborso parte solo
      quando il venditore conferma di averlo ricevuto.
    'venditore' e 'rimborso' funzionano anche come intervento d'ufficio
    su un reso che si e' incagliato."""
    user = verifica_utente(x_tg_init_data)
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
                       x_tg_init_data: str = Header("")):
    """L'acquirente ha rispedito l'oggetto: registra il tracciamento
    del reso e avvisa il venditore."""
    user = verifica_utente(x_tg_init_data)
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
async def reso_ricevuto(ordine_id: int, x_tg_init_data: str = Header("")):
    """Il venditore conferma di aver ricevuto il reso: parte il
    rimborso integrale all'acquirente."""
    user = verifica_utente(x_tg_init_data)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND venditore_id=? "
                    "AND stato='return_shipped'",
                    (ordine_id, user["id"])).fetchone()
    con.close()
    if not o:
        raise HTTPException(400, "Operazione non permessa")
    return await _rimborsa_compratore(ordine_id)


@app.post("/api/orders/{ordine_id}/conferma")
async def conferma_ricezione(ordine_id: int, x_tg_init_data: str = Header("")):
    """L'acquirente conferma la ricezione: i sats vengono consegnati
    automaticamente al venditore (invoice depositata o Lightning
    address). Se nessun metodo e' disponibile, l'ordine va in
    'confirmed' e partiranno appena il venditore ne fornisce uno."""
    user = verifica_utente(x_tg_init_data)
    con = db()
    o = con.execute("SELECT * FROM ordini WHERE id=? AND compratore_id=? "
                    "AND stato IN ('locked','shipped','delivered')",
                    (ordine_id, user["id"])).fetchone()
    con.close()
    if not o:
        raise HTTPException(400, "Operazione non permessa")
    return await _sblocca_sats(ordine_id)


@app.post("/api/orders/{ordine_id}/disputa")
async def apri_disputa(ordine_id: int, x_tg_init_data: str = Header("")):
    user = verifica_utente(x_tg_init_data)
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
async def annulla_ordine(ordine_id: int, x_tg_init_data: str = Header("")):
    """L'acquirente annulla un ordine non ancora pagato (nessun sat
    e' stato mosso: l'ordine sparisce e basta)."""
    user = verifica_utente(x_tg_init_data)
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
def miei_ordini(x_tg_init_data: str = Header("")):
    user = verifica_utente(x_tg_init_data)
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
    con.close()
    for oid in scaduti_consegna + scaduti_silenzio:
        print(f"⏰ Sblocco automatico dell'ordine #{oid}")
        await _sblocca_sats(oid, automatico=True)


async def orologio():
    while True:
        try:
            await controlla_scadenze()
        except Exception as e:
            print(f"Orologio sblocchi, errore (riprovo tra 10 min): {e}")
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


app.mount("/foto", StaticFiles(directory=FOTO_DIR), name="foto")
