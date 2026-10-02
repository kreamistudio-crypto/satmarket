# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE FOTO NELLE RECENSIONI (ott 2026, richiesta di Andrea).

Nel feedback di un affare del mercatino si mettono fino a tre foto, e il
SERVER le carica su un Blossom firmando l'autorizzazione kind 24242 con la
chiave della piattaforma. Qui si chiamano le ROTTE VERE contro un Blossom
DI CARTONE acceso su 127.0.0.1, che fa quel che farebbe quello vero e in
piu' controlla: la firma Schnorr dell'evento (vera, ricalcolata), il kind,
il verbo `t`, lo sha256 in `x` uguale ai byte arrivati, la scadenza.

  1. un feedback con DUE foto: arrivano a Blossom firmate, SENZA il GPS
     che avevano dentro, e la riga del database tiene i due URL;
  2. le foto escono nel profilo del negozio e nella lista degli ordini
     (le mie da una parte, le sue dall'altra);
  3. i rifiuti PRIMA di Blossom: quattro foto, una foto che non e' una
     foto, il feedback gia' lasciato, l'ordine di un altro — e il
     Blossom non vede arrivare niente;
  4. Blossom che risponde 500: il feedback NON nasce (le foto non
     spariscono in silenzio), e la foto gia' caricata si toglie;
  5. il feedback senza foto e' quello di sempre;
  6. il moderatore rimuove la recensione: le foto si tolgono da Blossom;
  7. in collaudo, verso un Blossom che non e' di casa, non si esce:
     l'URL e' quello che sarebbe, e nessuno ha bussato;
  8. `url_blob_ammesso`: la forma che entra in un <img> e basta.

NON TOCCA NIENTE DI VERO: config finto prima dell'import di server, un
database usa-e-getta, e la chiave della piattaforma e' una chiave di prova
che firma con `schnorr_puro` (in CI coincurve non c'e').

USO:  python collaudo_foto_recensioni.py
"""

import asyncio
import base64
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import schnorr_puro  # noqa: E402

PASSATE = FALLITE = 0
SRV = None
SK = hashlib.sha256(b"collaudo foto recensioni").digest()
PUB = schnorr_puro.pubblica(SK).hex()


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


# ------------------------- il Blossom di cartone -------------------------

class Cartone:
    blob = {}           # sha256 -> byte
    visti = []          # (verbo, sha, esito) di ogni richiesta
    guasto = False      # True = ogni upload risponde 500
    torti = []          # cosa non andava nelle autorizzazioni


def _giudica_auth(intestazione, verbo, sha):
    """Il controllo di BUD-01, fatto per davvero. Torna '' o il torto."""
    if not intestazione.startswith("Nostr "):
        return "manca «Nostr »"
    try:
        ev = json.loads(base64.b64decode(intestazione[6:]))
    except Exception:
        return "evento illeggibile"
    serial = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"],
                         ev["tags"], ev["content"]],
                        separators=(",", ":"), ensure_ascii=False)
    if hashlib.sha256(serial.encode()).hexdigest() != ev["id"]:
        return "id sbagliato"
    if not schnorr_puro.verifica(bytes.fromhex(ev["pubkey"]),
                                 bytes.fromhex(ev["id"]),
                                 bytes.fromhex(ev["sig"])):
        return "firma falsa"
    if ev["pubkey"] != PUB:
        return "non e' la chiave della piattaforma"
    if ev["kind"] != 24242:
        return f"kind {ev['kind']}"
    tag = {t[0]: t[1] for t in ev["tags"]}
    if tag.get("t") != verbo:
        return f"verbo {tag.get('t')}"
    if tag.get("x") != sha:
        return "x diverso dai byte"
    if not int(tag.get("expiration", 0)) > time.time():
        return "scaduta"
    return ""


class Porta(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _rispondi(self, codice, corpo=None):
        dati = json.dumps(corpo or {}).encode()
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def do_PUT(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        sha = hashlib.sha256(raw).hexdigest()
        if self.path != "/upload":
            return self._rispondi(404)
        if Cartone.guasto and Cartone.blob:
            # il guasto arriva DOPO la prima foto: cosi' si vede anche
            # la pulizia di quella gia' caricata
            Cartone.visti.append(("upload", sha, 500))
            return self._rispondi(500)
        torto = _giudica_auth(self.headers.get("Authorization", ""),
                              "upload", sha)
        if torto:
            Cartone.torti.append(torto)
            Cartone.visti.append(("upload", sha, 401))
            return self._rispondi(401)
        Cartone.blob[sha] = raw
        Cartone.visti.append(("upload", sha, 200))
        porta = self.server.server_address[1]
        self._rispondi(200, {"url": f"http://127.0.0.1:{porta}/{sha}.jpg",
                             "sha256": sha, "size": len(raw),
                             "type": self.headers.get("Content-Type")})

    def do_DELETE(self):
        sha = self.path.strip("/")
        torto = _giudica_auth(self.headers.get("Authorization", ""),
                              "delete", sha)
        if torto:
            Cartone.torti.append(torto)
            return self._rispondi(401)
        Cartone.blob.pop(sha, None)
        Cartone.visti.append(("delete", sha, 200))
        self._rispondi(200)


def accendi_cartone():
    s = ThreadingHTTPServer(("127.0.0.1", 0), Porta)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"


# ------------------------------- il banco -------------------------------

class FirmaPura:
    """Il posto di `coincurve.PrivateKey` nel `_NOSTR` del server."""
    def sign_schnorr(self, msg):
        return schnorr_puro.firma(SK, msg)


def avvio(blossom):
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato")
    cartella = tempfile.mkdtemp(prefix="barattolo-foto-recensioni-")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = os.path.join(cartella, "usa-e-getta.db")
    cfg.BLOSSOM_SERVER = blossom
    sys.modules["config"] = cfg
    os.chdir(QUI)
    import server
    SRV = server
    server._NOSTR = (FirmaPura(), PUB)

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        return {"payment_hash": f"hash{int(time.time()*1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def zitto(*a, **k):
        return None

    async def paga_finto(bolt11, atteso_sats, diario=None, *, cassaforte,
                         riga=()):
        return SRV.PAGATO

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = zitto
    server.paga_venditore = paga_finto
    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.notifica_admin = zitto


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": admin}


async def _chiama(fn, args, corpo):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    r = fn(*args)
    if asyncio.iscoroutine(r):
        r = await r
    # le pulizie in sottofondo (create_task) finiscono qui dentro
    attesa = [t for t in asyncio.all_tasks()
              if t is not asyncio.current_task()]
    if attesa:
        await asyncio.gather(*attesa, return_exceptions=True)
    return r


def chiama(fn, *args, corpo=None):
    return asyncio.run(_chiama(fn, args, corpo))


def errore(fn, *args, corpo=None):
    try:
        chiama(fn, *args, corpo=corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def scrivi(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET "
                + ", ".join(f"{k}=?" for k in campi) + " WHERE id=?",
                tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def feedback_di(oid, chi):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM feedback WHERE ordine_id=? AND "
                    "da_tg_id=?", (oid, chi)).fetchone()
    con.close()
    return dict(r) if r else None


def semina():
    con = SRV.db()
    for tg, nome, neg in ((222, "Vende", "neg22222"),
                          (111, "Compra", "neg11111"),
                          (333, "Terzo", "neg33333")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, neg))
    ids = []
    for n in range(4):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa vera',50000,'Altro','Pavia (PV)',"
            "'attivo',1,'spedizione',9,'sats','nuovo')", (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_concluso(annuncio_id):
    """Il giro vero fino a 'confirmed' (il venditore non ha come
    incassare): e' gia' un affare concluso per il feedback."""
    come(111)
    c = chiama(SRV.compra, None, corpo={
        "annuncio_id": annuncio_id, "consegna": "spedizione",
        "indirizzo": {"nome": "Mario Rossi", "via": "Via Roma 1",
                      "cap": "27100", "citta": "Pavia", "prov": "PV",
                      "tel": "3330000000"}})
    oid = c["ordine_id"]
    scrivi(oid, stato="locked")
    come(222)
    chiama(SRV.segna_spedito, oid, None,
           corpo={"corriere": "Poste Italiane", "tracking": "AB123456789IT"})
    come(111)
    chiama(SRV.conferma_ricezione, oid)
    stato = SRV.db().execute("SELECT stato FROM ordini WHERE id=?",
                             (oid,)).fetchone()[0]
    if stato != "confirmed":
        raise SystemExit(f"⚠️  ordine {oid} in '{stato}', non 'confirmed'")
    return oid


def foto(seme, gps=False):
    """Una foto VERA (un gradiente con del rumore: non e' «vuota»), in
    data URL. Con `gps` porta dentro un EXIF con la posizione."""
    from PIL import Image
    img = Image.new("RGB", (240, 180))
    px = img.load()
    for x in range(240):
        for y in range(180):
            px[x, y] = ((x * 7 + seme * 31) % 256, (y * 5 + seme) % 256,
                        ((x * y) // 7 + seme * 13) % 256)
    buf = io.BytesIO()
    if gps:
        exif = Image.Exif()
        exif[0x010F] = "MarcaDiProva"
        exif[0x8825] = {1: "N", 2: (45.0, 11.0, 0.0),
                        3: "E", 4: (9.0, 9.0, 0.0)}
        img.save(buf, "JPEG", quality=90, exif=exif)
    else:
        img.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def ha_gps(raw):
    from PIL import Image
    with Image.open(io.BytesIO(raw)) as im:
        e = im.getexif()
        return bool(e) and (0x8825 in e or 0x010F in e)


def main():
    print("=" * 60)
    print("  LE FOTO NELLE RECENSIONI, SU BLOSSOM")
    print("=" * 60)
    blossom = accendi_cartone()
    avvio(blossom)
    ann = semina()

    # ---- 1. un feedback con due foto ----------------------------------
    print("\n[1. il compratore vota con due foto]")
    oid = ordine_concluso(ann[0])
    con_gps = foto(1, gps=True)
    prova("(la foto di partenza ha davvero il GPS dentro)", True,
          ha_gps(base64.b64decode(con_gps.split(",", 1)[1])))
    come(111)
    d = chiama(SRV.lascia_feedback, oid, None, corpo={
        "voto": 5, "commento": "Arrivato benissimo", "foto": [con_gps, foto(2)]})
    prova("il feedback passa", True, d["ok"])
    prova("la risposta porta due URL", 2, len(d["foto"]))
    prova("nessun torto nelle autorizzazioni", [], Cartone.torti)
    prova("Blossom ha due blob", 2, len(Cartone.blob))
    prova("nessuno dei due ha EXIF o GPS", [False, False],
          [ha_gps(b) for b in Cartone.blob.values()])
    prova("gli URL sono i blob arrivati",
          sorted(f"{blossom}/{s}.jpg" for s in Cartone.blob), sorted(d["foto"]))
    riga = feedback_di(oid, 111)
    prova("la riga tiene gli URL", d["foto"], json.loads(riga["foto"]))
    prova("voto e commento come sempre", (5, "Arrivato benissimo"),
          (riga["voto"], riga["commento"]))

    # ---- 2. dove escono ------------------------------------------------
    print("\n[2. profilo del negozio e lista degli ordini]")
    n = chiama(SRV.negozio, "neg22222", 0, "", "", 0, "", "")
    prova("nel profilo del venditore, con le sue foto", d["foto"],
          n["feedback"][0]["foto"])
    come(111)
    mie = {o["id"]: o for o in chiama(SRV.miei_ordini, 0, "", "")}
    prova("nell'ordine di chi l'ha scritta: mio_foto", d["foto"],
          mie[oid]["mio_foto"])
    prova("...e suo_foto vuota", [], mie[oid]["suo_foto"])
    come(222)
    sue = {o["id"]: o for o in chiama(SRV.miei_ordini, 0, "", "")}
    prova("in quello di chi l'ha ricevuta: suo_foto", d["foto"],
          sue[oid]["suo_foto"])

    # ---- 3. i rifiuti prima di Blossom ---------------------------------
    print("\n[3. i rifiuti non bussano a Blossom]")
    prima = len(Cartone.visti)
    oid2 = ordine_concluso(ann[1])
    come(111)
    prova("quattro foto: 400",
          (400, "Al massimo 3 foto per recensione"),
          errore(SRV.lascia_feedback, oid2, None,
                 corpo={"voto": 4, "foto": [foto(3)] * 4}))
    e = errore(SRV.lascia_feedback, oid2, None, corpo={
        "voto": 4, "foto": [foto(4), "data:image/jpeg;base64,"
                            + base64.b64encode(b"%PDF-1.4 finto").decode()]})
    prova("una foto che non e' una foto: 400 che dice quale", (400, True),
          (e[0], e[1].startswith("La foto 2 non è stata accettata")))
    prova("'foto' che non e' una lista: 400", 400,
          errore(SRV.lascia_feedback, oid2, None,
                 corpo={"voto": 4, "foto": "ciao"})[0])
    come(111)
    prova("feedback gia' lasciato: 400",
          (400, "Hai già lasciato il feedback per questo ordine"),
          errore(SRV.lascia_feedback, oid, None,
                 corpo={"voto": 1, "foto": [foto(5)]}))
    come(333)
    prova("l'ordine di altri: 403", 403,
          errore(SRV.lascia_feedback, oid2, None,
                 corpo={"voto": 1, "foto": [foto(6)]})[0])
    prova("Blossom non ha visto arrivare niente", prima, len(Cartone.visti))
    prova("e il feedback non e' nato", None, feedback_di(oid2, 111))

    # ---- 4. Blossom giu' -------------------------------------------------
    print("\n[4. Blossom che risponde 500 alla seconda foto]")
    blob_prima = set(Cartone.blob)
    Cartone.guasto = True
    come(111)
    e = errore(SRV.lascia_feedback, oid2, None,
               corpo={"voto": 4, "foto": [foto(7), foto(8)]})
    Cartone.guasto = False
    prova("502 col messaggio che dice cosa fare",
          (502, SRV.MSG_BLOSSOM_GIU), e)
    prova("il feedback NON e' nato", None, feedback_di(oid2, 111))
    prova("la prima foto, caricata, e' stata tolta", blob_prima,
          set(Cartone.blob))

    # ---- 5. senza foto ----------------------------------------------------
    print("\n[5. il feedback senza foto e' quello di sempre]")
    prima = len(Cartone.visti)
    d2 = chiama(SRV.lascia_feedback, oid2, None,
                corpo={"voto": 4, "commento": "ok"})
    prova("passa", (True, []), (d2["ok"], d2["foto"]))
    prova("la colonna resta vuota", "", feedback_di(oid2, 111)["foto"])
    prova("Blossom non c'entra", prima, len(Cartone.visti))
    come(222)
    prova("e fuori la lista e' vuota", [],
          {o["id"]: o for o in chiama(SRV.miei_ordini, 0, "", "")}
          [oid2]["suo_foto"])

    # ---- 6. il moderatore rimuove --------------------------------------
    print("\n[6. il moderatore rimuove la recensione con le foto]")
    fid = feedback_di(oid, 111)["id"]
    come(999, admin=True)
    chiama(SRV.rimuovi_feedback_admin, fid, "", "")
    prova("la riga se n'e' andata", None, feedback_di(oid, 111))
    prova("e Blossom non ha piu' le due foto", 0, len(Cartone.blob))
    prova("tolte con la firma giusta", [], Cartone.torti)

    # ---- 7. in collaudo non si esce ------------------------------------
    print("\n[7. un Blossom che non e' di casa, in collaudo]")
    SRV.BLOSSOM_SERVER = "https://blossom.primal.net"
    prima = len(Cartone.visti)
    oid3 = ordine_concluso(ann[2])
    come(111)
    d3 = chiama(SRV.lascia_feedback, oid3, None,
                corpo={"voto": 5, "foto": [foto(9)]})
    prova("l'URL e' quello che sarebbe", True,
          d3["foto"][0].startswith("https://blossom.primal.net/")
          and d3["foto"][0].endswith(".jpg"))
    prova("il cartone non ha visto niente (e la gabbia nemmeno)", prima,
          len(Cartone.visti))

    # ---- 8. la forma ammessa --------------------------------------------
    print("\n[8. url_blob_ammesso]")
    h = "a" * 64
    for url, atteso in (
            (f"https://blossom.primal.net/{h}.jpg", True),
            (f"https://blossom.primal.net/{h}", True),
            (f"https://blossom.primal.net/{h}.jpg?x=1", False),
            (f"http://blossom.primal.net/{h}.jpg", False),
            (f"https://altro.net/{h}.jpg", False),
            (f"https://blossom.primal.net/{h[:-1]}.jpg", False),
            (f"https://blossom.primal.net/x/{h}.jpg", False),
            ("javascript:alert(1)", False),
            ("", False)):
        prova(f"{url[:50] or '(vuoto)'} → {atteso}", atteso,
              SRV.url_blob_ammesso(url))
    prova("foto_recensione scarta il JSON rotto", [],
          SRV.foto_recensione("{rotto"))
    prova("...e gli URL di altri", [f"https://blossom.primal.net/{h}.jpg"],
          SRV.foto_recensione(json.dumps(
              [f"https://altro.net/{h}.jpg",
               f"https://blossom.primal.net/{h}.jpg"])))

    print(f"\n{'=' * 60}\n  {PASSATE} passate, {FALLITE} fallite\n{'=' * 60}")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
