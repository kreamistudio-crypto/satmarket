# -*- coding: utf-8 -*-
"""
IMPORTA DA NOSTR — prende gli annunci di un venditore Nostr
(con il suo consenso!) e li inserisce nel database di SatMarket.

Supporta entrambi i formati:
  - kind 30402 (NIP-99, annunci "classified")
  - kind 30018 (NIP-15, prodotti dei negozi tipo Shopstr/Plebeian)

I prezzi in EUR/USD vengono convertiti in sats col cambio attuale.

COME SI USA:
  1. Compila NPUB_VENDITORE qui sotto con la npub del tuo amico
  2. (Meglio a server spento) nella cartella MERCATINO:
       python importa_nostr.py
  3. Riavvia il server: gli annunci sono in vetrina, intestati
     al "Venditore" del collaudo (che li gestisce dalla Mini App)

REQUISITI: pip install websocket-client   (gia' installato)
"""

import json
import sqlite3
import ssl
import time
import urllib.request

from websocket import create_connection

# ======================= CONFIGURAZIONE =======================
# La npub del venditore e l'id a cui intestare gli annunci vivono
# in config.py (insieme alle chiavi del server), cosi' questo script
# si aggiorna senza mai dover ricopiare nulla.
# Nel tuo config.py devono esserci queste due righe:
#   NPUB_VENDITORE = "npub1..."   # la chiave pubblica Nostr del venditore
#   VENDITORE_ID = 222            # 222 nel collaudo; al lancio il suo
#                                 # VERO user id Telegram (da @userinfobot)

try:
    from config import NPUB_VENDITORE, VENDITORE_ID
except ImportError:
    raise SystemExit(
        "\n⚠️  Manca config.py (o le righe NPUB_VENDITORE e VENDITORE_ID"
        "\n   al suo interno). Aggiungile e rilancia. Esempio:\n"
        '\n   NPUB_VENDITORE = "npub1..."'
        "\n   VENDITORE_ID = 222\n")

DB = "satmarket.db"

RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://nostr.mom",
]

# ==============================================================

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"   # alfabeto bech32


def npub_to_hex(npub: str) -> str:
    """Converte la npub (bech32) nella chiave esadecimale dei relay."""
    npub = npub.strip().lower()
    if len(npub) == 64 and all(c in "0123456789abcdef" for c in npub):
        return npub                      # e' gia' in esadecimale
    if not npub.startswith("npub1"):
        raise ValueError("La chiave deve iniziare con 'npub1' (o essere hex)")
    dati = [CHARSET.find(c) for c in npub[5:]]
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


def tag(e, nome):
    for t in e.get("tags", []):
        if t and t[0] == nome and len(t) > 1:
            return t
    return None


def interroga(relay, hexkey):
    eventi = []
    try:
        ws = create_connection(relay, timeout=10,
                               sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.send(json.dumps(["REQ", "imp", {
            "kinds": [30402, 30018, 30017], "authors": [hexkey], "limit": 200}]))
        inizio = time.time()
        while time.time() - inizio < 20:
            try:
                msg = json.loads(ws.recv())
            except Exception:
                break
            if msg[0] == "EVENT" and msg[1] == "imp":
                eventi.append(msg[2])
            elif msg[0] == "EOSE":
                break
        ws.close()
        print(f"  ✓ {relay}: {len(eventi)} eventi")
    except Exception as err:
        print(f"  ✗ {relay}: non raggiungibile ({err})")
    return eventi


def cambio_btc():
    """Prezzo del Bitcoin in EUR e USD (per convertire i prezzi in sats)."""
    try:
        with urllib.request.urlopen(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin&vs_currencies=eur,usd", timeout=15) as r:
            d = json.loads(r.read())["bitcoin"]
            return {"EUR": d["eur"], "USD": d["usd"]}
    except Exception:
        print("⚠️  Cambio BTC non disponibile: gli annunci in EUR/USD "
              "verranno saltati.")
        return {}


def in_sats(importo: float, valuta: str, cambio: dict):
    valuta = (valuta or "").upper()
    if valuta in ("SAT", "SATS"):
        return int(importo)
    if valuta == "BTC":
        return int(importo * 100_000_000)
    if valuta in cambio:                       # EUR / USD
        return int(importo / cambio[valuta] * 100_000_000)
    return None


def categoria_automatica(testo: str) -> str:
    testo = testo.lower()
    MAPPA = [
        ("Elettronica", ["elettron", "electronic", "computer", "pc", "phone",
                         "telefono", "cuffie", "tastiera", "raspberry",
                         "hardware", "usb", "monitor", "console"]),
        ("Libri",       ["libro", "book", "novel", "romanzo", "fumetto",
                         "manga", "rivista"]),
        ("Sport",       ["bici", "bike", "sport", "palestra", "fitness",
                         "montagna", "sci", "calcio"]),
        ("Abbigliamento", ["shirt", "maglia", "felpa", "giacca", "scarpe",
                           "shoes", "cappello", "hat", "abbigliamento"]),
        ("Casa",        ["casa", "sedia", "tavolo", "lampada", "cucina",
                         "arredo", "furniture", "candle", "candela", "soap",
                         "sapone", "butter"]),
    ]
    for cat, parole in MAPPA:
        if any(p in testo for p in parole):
            return cat
    return "Altro"


def estrai_annuncio(e, valute_stall, cambio):
    """Trasforma un evento Nostr in un annuncio SatMarket (o None)."""
    if e["kind"] == 30402:                     # NIP-99 classified
        t = tag(e, "title")
        titolo = t[1] if t else ""
        s = tag(e, "summary")
        desc = e.get("content", "") or (s[1] if s else "")
        st = tag(e, "status")
        if st and st[1] == "sold":
            return None
        loc = tag(e, "location")
        zona = loc[1] if loc else ""
        p = tag(e, "price")
        if not p or len(p) < 3:
            return None
        sats = in_sats(float(p[1]), p[2], cambio)
        foto = [t[1] for t in e.get("tags", [])
                if t and t[0] == "image" and len(t) > 1][:5]
    else:                                      # NIP-15 prodotto (30018)
        try:
            c = json.loads(e.get("content", "{}"))
        except Exception:
            return None
        titolo = c.get("name", "")
        desc = c.get("description", "")
        zona = ""
        valuta = c.get("currency") or valute_stall.get(c.get("stall_id"), "")
        if c.get("price") is None:
            return None
        sats = in_sats(float(c["price"]), valuta, cambio)
        foto = [u for u in (c.get("images") or []) if isinstance(u, str)][:5]

    if not titolo or not sats or sats <= 0:
        return None
    return {"titolo": titolo.strip()[:120],
            "descrizione": (desc or "—").strip()[:1500],
            "zona": zona.strip()[:60],
            "prezzo_sats": sats,
            "foto": json.dumps(foto) if foto else "",
            "categoria": categoria_automatica(titolo + " " + desc)}


def main():
    hexkey = npub_to_hex(NPUB_VENDITORE)
    print(f"Cerco gli annunci di {NPUB_VENDITORE[:20]}… sui relay:\n")
    eventi = []
    for r in RELAYS:
        eventi += interroga(r, hexkey)

    # dedup: tieni la versione piu' recente di ogni annuncio
    unici = {}
    for e in eventi:
        d = tag(e, "d")
        chiave = (e["kind"], d[1] if d else e["id"])
        if chiave not in unici or e["created_at"] > unici[chiave]["created_at"]:
            unici[chiave] = e

    # valute dei negozi NIP-15 (stall, kind 30017)
    valute_stall = {}
    for e in unici.values():
        if e["kind"] == 30017:
            try:
                c = json.loads(e["content"])
                valute_stall[c.get("id")] = c.get("currency", "")
            except Exception:
                pass

    prodotti = [e for e in unici.values() if e["kind"] in (30402, 30018)]
    print(f"\nTrovati {len(prodotti)} annunci unici. Converto e importo…\n")
    if not prodotti:
        print("Nessun annuncio trovato: controlla la npub, o prova ad "
              "aggiungere ai RELAYS quello usato dal tuo amico.")
        return

    cambio = cambio_btc()
    con = sqlite3.connect(DB)
    # Assicura che il database abbia le colonne nuove (foto, nostr)
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''"):
        try:
            con.execute(f"ALTER TABLE annunci ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome, username) "
                "VALUES(?, 'Venditore', 'venditore')", (VENDITORE_ID,))

    importati, aggiornati, saltati = 0, 0, 0
    npub = NPUB_VENDITORE.strip()
    for e in prodotti:
        a = estrai_annuncio(e, valute_stall, cambio)
        if not a:
            saltati += 1
            continue
        gia = con.execute(
            "SELECT id FROM annunci WHERE titolo=? AND stato='attivo' "
            "AND (venditore_id=? OR contatto_nostr=?)",
            (a["titolo"], VENDITORE_ID, npub)).fetchone()
        if gia:
            # Gia' presente: aggiorna foto, contatto, prezzo e
            # PROPRIETARIO (utile per re-intestare al lancio)
            con.execute(
                "UPDATE annunci SET foto=?, contatto_nostr=?, prezzo_sats=?, "
                "venditore_id=? WHERE id=?",
                (a["foto"], npub, a["prezzo_sats"], VENDITORE_ID, gia[0]))
            aggiornati += 1
            print(f"  ↻ aggiornato: {a['titolo'][:50]}")
            continue
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
            "prezzo_sats,zona,foto,contatto_nostr,creato) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (VENDITORE_ID, a["titolo"], a["descrizione"], a["categoria"],
             a["prezzo_sats"], a["zona"], a["foto"], npub, int(time.time())))
        importati += 1
        n_foto = len(json.loads(a["foto"])) if a["foto"] else 0
        print(f"  ⚡ {a['titolo'][:50]} — {a['prezzo_sats']} sats "
              f"[{a['categoria']}] {'📷x'+str(n_foto) if n_foto else ''}")

    con.commit()
    con.close()
    print(f"\nFATTO: {importati} importati, {aggiornati} aggiornati, "
          f"{saltati} saltati (venduti o senza prezzo).")
    print("Riavvia il server e guardali in vetrina nella Mini App!")


if __name__ == "__main__":
    main()
