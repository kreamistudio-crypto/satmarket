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

Da lug 2026 il server rifa' questo import DA SOLO ogni ora (vedi
l'orologio in server.py, che importa questo modulo): lo script
manuale resta per il primo giro e per le prove.

REQUISITI: pip install websocket-client   (gia' installato)
"""

import json
import os
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

# Il modulo deve restare IMPORTABILE dal server (import periodico):
# se config.py o le sue righe mancano, qui entrano segnaposto vuoti
# e a fermarsi (con la guida di sempre) e' solo main().
try:
    from config import NPUB_VENDITORE, VENDITORE_ID
except ImportError:
    NPUB_VENDITORE, VENDITORE_ID = "", 0

DB = "satmarket.db"
FOTO_DIR = "foto"                    # stessa cartella degli annunci normali
MAX_FOTO_BYTES = 3_000_000           # oltre ~3 MB la foto resta un URL

RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://nostr.mom",
    "wss://21milionidinostr.duckdns.org",   # il relay del nostro venditore
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


def _bech32_polymod(valori: list) -> int:
    """Il cuore del checksum bech32 (BIP-173) — specchio di server.py."""
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
    """Gemella speculare di npub_to_hex (specchio di server.py): serve
    a scrivere il badge del venditore nella forma canonica npub1…"""
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
    return "npub1" + "".join(CHARSET[d] for d in dati + checksum)


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


def scarica_foto(url: str, annuncio_id: int, indice: int):
    """Scarica una foto esterna e la salva in foto/ con lo stesso
    schema nomi degli annunci normali (a{id}_{indice}.ext).
    Ritorna il nome del file locale, o None se qualcosa va storto."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Barattolo/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(MAX_FOTO_BYTES + 1)
            if len(raw) > MAX_FOTO_BYTES:
                print(f"    ⚠️  foto troppo grande, tengo l'URL: {url[:60]}")
                return None
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        est = {"image/png": "png", "image/webp": "webp",
               "image/gif": "gif"}.get(ctype, "jpg")
        nome = f"a{annuncio_id}_{indice}.{est}"
        with open(os.path.join(FOTO_DIR, nome), "wb") as out:
            out.write(raw)
        return nome
    except Exception as err:
        print(f"    ⚠️  foto non scaricata ({err}), tengo l'URL: {url[:60]}")
        return None


def localizza_foto(annuncio_id: int, foto_json: str) -> str:
    """Prende la lista foto (JSON) e scarica in locale gli URL esterni.
    Se un download fallisce, l'URL resta com'e' (meglio di niente)."""
    try:
        lista = json.loads(foto_json or "[]")
    except Exception:
        return foto_json
    nuove = []
    for i, f in enumerate(lista):
        if not isinstance(f, str) or not f.startswith("http"):
            nuove.append(f)                    # gia' un file locale
            continue
        nome = scarica_foto(f, annuncio_id, i)
        nuove.append(nome or f)
    return json.dumps(nuove) if nuove else ""


def categoria_automatica(testo: str) -> str:
    testo = testo.lower()
    MAPPA = [
        ("Elettronica", ["elettron", "electronic", "computer", "pc", "phone",
                         "telefono", "cuffie", "tastiera", "raspberry",
                         "hardware", "usb", "monitor", "console"]),
        ("Libri e media", ["libro", "book", "novel", "romanzo", "fumetto",
                           "manga", "rivista", "vinile", "blu-ray", "dvd"]),
        # Bambini prima di Motori: "seggiolino auto" e' roba da bimbi
        ("Bambini",     ["bambin", "bimbo", "bimba", "passeggino",
                         "giocattol", "peluche", "seggiolino", "neonat",
                         "lego"]),
        ("Animali",     ["per cani", "per gatti", "cucciol", "guinzaglio",
                         "acquario", "tiragraffi", "cuccia", "voliera"]),
        ("Motori",      ["scooter", "motorino", "vespa", "ricambi",
                         "cerchi in lega", "casco", "automobile",
                         "motociclett", "pneumatic"]),
        ("Sport e hobby", ["bici", "bike", "sport", "palestra", "fitness",
                           "montagna", "sci", "calcio", "chitarra",
                           "modellismo"]),
        ("Abbigliamento", ["shirt", "maglia", "felpa", "giacca", "scarpe",
                           "shoes", "cappello", "hat", "abbigliamento"]),
        ("Casa e giardino", ["casa", "sedia", "tavolo", "lampada", "cucina",
                             "arredo", "furniture", "candle", "candela",
                             "soap", "sapone", "butter", "giardino"]),
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
        importo, valuta = float(p[1]), p[2]
        sats = in_sats(importo, valuta, cambio)
        foto = [t[1] for t in e.get("tags", [])
                if t and t[0] == "image" and len(t) > 1][:5]
        # Le coordinate dell'evento origine: il tag "d" (serve alla
        # modifica firmata da Barattolo per SOSTITUIRE l'evento sui
        # relay) e gli URL originali delle foto (per non riscriverli
        # con URL nostri quando l'evento si ricostruisce).
        d = tag(e, "d")
        origine_d = d[1] if d else ""
        origine_foto = json.dumps(foto) if foto else ""
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
        importo = float(c["price"])
        sats = in_sats(importo, valuta, cambio)
        foto = [u for u in (c.get("images") or []) if isinstance(u, str)][:5]
        origine_d, origine_foto = "", ""       # la modifica firmata (v1)
                                               # parla solo NIP-99

    if not titolo or not sats or sats <= 0:
        return None
    return {"titolo": titolo.strip()[:120],
            "descrizione": (desc or "—").strip()[:1500],
            "zona": zona.strip()[:60],
            "prezzo_sats": sats,
            "foto": json.dumps(foto) if foto else "",
            "categoria": categoria_automatica(titolo + " " + desc),
            "origine_d": origine_d,
            "origine_foto": origine_foto,
            # la coppia del tag price: se il listino nasce in EUR la
            # vetrina deve dirlo (valuta/prezzo_eur), non solo i sats
            "valuta_orig": (valuta or "").upper(),
            "importo_orig": importo}


def importa_venditore(npub_venditore: str, venditore_id: int,
                      db: str = DB):
    """Il cuore dell'import, in forma riusabile: lo chiama lo script
    manuale (main, qui sotto) e ogni ora l'orologio del server.
    Ritorna la terna (importati, aggiornati, saltati)."""
    hexkey = npub_to_hex(npub_venditore)
    os.makedirs(FOTO_DIR, exist_ok=True)
    print(f"Cerco gli annunci di {npub_venditore[:20]}… sui relay:\n")
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
        return 0, 0, 0

    cambio = cambio_btc()
    # timeout generoso: quando gira dal server il database e' conteso
    con = sqlite3.connect(db, timeout=15)
    # Assicura che il database abbia le colonne nuove (foto, nostr).
    # Le due "origine" ricordano le coordinate dell'evento Nostr
    # (tag d e URL foto originali): servono alla modifica firmata.
    for colonna in ("foto TEXT DEFAULT ''", "contatto_nostr TEXT DEFAULT ''",
                    "nostr_origine_d TEXT DEFAULT ''",
                    "nostr_origine_foto TEXT DEFAULT ''",
                    "valuta TEXT DEFAULT 'sats'",
                    "prezzo_eur REAL DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE annunci ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome, username) "
                "VALUES(?, 'Venditore', 'venditore')", (venditore_id,))

    # Il badge del venditore: gli eventi importati sono firmati dalla
    # sua chiave, il possesso e' dimostrato. Se il profilo non dichiara
    # ancora una npub gliela scriviamo gia' verificata (cosi' il login
    # Nostr lo riconosce); una npub DIVERSA gia' presente non si tocca.
    for colonna in ("npub TEXT DEFAULT ''",
                    "npub_verificata INTEGER DEFAULT 0"):
        try:
            con.execute(f"ALTER TABLE utenti ADD COLUMN {colonna}")
        except sqlite3.OperationalError:
            pass
    npub_bech = hex_to_npub(hexkey)        # forma canonica del badge
    u = con.execute("SELECT npub, npub_verificata FROM utenti "
                    "WHERE tg_id=?", (venditore_id,)).fetchone()
    if u:
        attuale = (u[0] or "").strip()
        if not attuale:
            con.execute("UPDATE utenti SET npub=?, npub_verificata=1 "
                        "WHERE tg_id=?", (npub_bech, venditore_id))
            print("  🟣 Profilo venditore: npub scritta, badge verificato")
        elif attuale == npub_bech and not u[1]:
            con.execute("UPDATE utenti SET npub_verificata=1 "
                        "WHERE tg_id=?", (venditore_id,))
            print("  🟣 Profilo venditore: npub gia' dichiarata, "
                  "badge ora verificato")

    importati, aggiornati, saltati = 0, 0, 0
    npub = npub_venditore.strip()
    for e in prodotti:
        a = estrai_annuncio(e, valute_stall, cambio)
        if not a:
            saltati += 1
            continue
        # Se il listino Nostr parla EUR la vetrina lo dice (doppia
        # valuta); tutte le altre valute restano un listino in sats.
        if a["valuta_orig"] == "EUR":
            valuta, prezzo_eur = "eur", round(a["importo_orig"], 2)
        else:
            valuta, prezzo_eur = "sats", 0
        # Ritrova l'annuncio: PRIMA per tag "d" (la coordinata stabile
        # dell'evento: sopravvive a un cambio di titolo), poi per
        # titolo come una volta — ma senza toccare le righe gia'
        # "battezzate" con un d diverso, che appartengono a un ALTRO
        # evento omonimo.
        gia = None
        if a["origine_d"]:
            gia = con.execute(
                "SELECT id, foto, nostr_origine_foto FROM annunci "
                "WHERE nostr_origine_d=? AND stato='attivo' "
                "AND (venditore_id=? OR contatto_nostr=?)",
                (a["origine_d"], venditore_id, npub)).fetchone()
        if not gia:
            gia = con.execute(
                "SELECT id, foto, nostr_origine_foto FROM annunci "
                "WHERE titolo=? AND stato='attivo' "
                "AND (venditore_id=? OR contatto_nostr=?) "
                "AND (nostr_origine_d='' OR nostr_origine_d IS NULL "
                "     OR nostr_origine_d=?)",
                (a["titolo"], venditore_id, npub, a["origine_d"])).fetchone()
        if gia:
            # Gia' presente: aggiorna TUTTO il contenuto (l'evento sui
            # relay e' la fonte di verita', anche dopo una modifica
            # firmata da Barattolo) e il PROPRIETARIO (utile al lancio).
            # La categoria invece resta: categoria_automatica
            # ricoprirebbe ogni ora una scelta fatta a mano dal form.
            if a["origine_foto"] and a["origine_foto"] == gia[2]:
                foto_loc = gia[1]      # stesse foto: niente ri-download
            else:
                foto_loc = localizza_foto(gia[0], a["foto"])
            con.execute(
                "UPDATE annunci SET titolo=?, descrizione=?, zona=?, "
                "foto=?, contatto_nostr=?, prezzo_sats=?, valuta=?, "
                "prezzo_eur=?, venditore_id=?, nostr_origine_d=?, "
                "nostr_origine_foto=? WHERE id=?",
                (a["titolo"], a["descrizione"], a["zona"], foto_loc, npub,
                 a["prezzo_sats"], valuta, prezzo_eur, venditore_id,
                 a["origine_d"], a["origine_foto"], gia[0]))
            aggiornati += 1
            print(f"  ↻ aggiornato: {a['titolo'][:50]}")
            continue
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,categoria,"
            "prezzo_sats,zona,foto,contatto_nostr,valuta,prezzo_eur,"
            "nostr_origine_d,nostr_origine_foto,creato) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (venditore_id, a["titolo"], a["descrizione"], a["categoria"],
             a["prezzo_sats"], a["zona"], a["foto"], npub, valuta,
             prezzo_eur, a["origine_d"], a["origine_foto"],
             int(time.time())))
        # Le foto si scaricano DOPO l'insert: il nome file vuole l'id
        foto_loc = localizza_foto(cur.lastrowid, a["foto"])
        if foto_loc != a["foto"]:
            con.execute("UPDATE annunci SET foto=? WHERE id=?",
                        (foto_loc, cur.lastrowid))
        importati += 1
        n_foto = len(json.loads(foto_loc)) if foto_loc else 0
        print(f"  ⚡ {a['titolo'][:50]} — {a['prezzo_sats']} sats "
              f"[{a['categoria']}] {'📷x'+str(n_foto) if n_foto else ''}")

    con.commit()
    con.close()
    return importati, aggiornati, saltati


def main():
    if not NPUB_VENDITORE or not VENDITORE_ID:
        raise SystemExit(
            "\n⚠️  Manca config.py (o le righe NPUB_VENDITORE e VENDITORE_ID"
            "\n   al suo interno). Aggiungile e rilancia. Esempio:\n"
            '\n   NPUB_VENDITORE = "npub1..."'
            "\n   VENDITORE_ID = 222\n")
    importati, aggiornati, saltati = importa_venditore(
        NPUB_VENDITORE, VENDITORE_ID)
    print(f"\nFATTO: {importati} importati, {aggiornati} aggiornati, "
          f"{saltati} saltati (venduti o senza prezzo).")
    print("Riavvia il server e guardali in vetrina nella Mini App!")


if __name__ == "__main__":
    main()
