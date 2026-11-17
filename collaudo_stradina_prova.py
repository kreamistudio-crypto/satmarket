# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE CASELLE DI PROVA DELLA STRADINA 🧪 (17 nov 2026,
cantiere stradina).

Andrea: «prima di metterlo in produzione voglio provarlo tutto: lo
segnerò come raggiunto in maniera fittizia, così proseguo e vedo cosa
succede; almeno me e Alan che siamo amministratori». Qui il server VERO,
per HTTP con la TestClient e l'identita' di collaudo nell'header:
  1) chi non e' admin prende 403 e la tabella non nasce nemmeno;
  2) l'admin segna una casella: sul SUO tabellone si accende, porta
     `finta`, e Tappo va avanti; il tabellone dice `prova`;
  3) gli XP e il livello non si muovono (non e' un fatto);
  4) il tabellone di un altro non la vede, e non ha `prova`;
  5) si toglie una casella, si azzera tutto; un id storto e' un 400.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, nessuna rete.

USO:  python collaudo_stradina_prova.py
"""

import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None

ADMIN, ANNA = 999, 111


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-stradina-prova-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [ADMIN]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.STRADINA_ATTIVA = True        # spenta di serie (17 nov 2026): qui si prova accesa
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def zitto(*a, **k):
        return None

    for nome in ("notifica", "notifica_admin", "annuncio_su_nostr",
                 "premia_distintivi", "premia_xp", "aggiorna_profilo_social"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    return db


def chi(tg_id):
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:Utente{tg_id}"}


def tabella_c_e(db):
    con = sqlite3.connect(db)
    try:
        return bool(con.execute("SELECT 1 FROM sqlite_master WHERE "
                                "type='table' AND name='stradina_prova'").fetchone())
    finally:
        con.close()


def main():
    db = avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    c.get("/api/me", headers=chi(ADMIN))
    c.get("/api/me", headers=chi(ANNA))
    strada = lambda t: c.get("/api/me/stradina", headers=chi(t)).json()
    segna = lambda t, corpo: c.post("/api/me/stradina/prova", headers=chi(t),
                                    json=corpo)
    tappa = lambda d, tid: next((x for x in d["tappe"] if x["id"] == tid), None)

    print("\n[1) chi non e' admin non entra]")
    r = segna(ANNA, {"tappa": "foto"})
    prova("Anna prende 403", 403, r.status_code)
    prova("...e la tabella delle prove non nasce", False, tabella_c_e(db))
    prova("il tabellone di Anna non ha `prova`", False, strada(ANNA)["prova"])

    print("\n[2) l'admin segna una casella]")
    d0 = strada(ADMIN)
    prova("il tabellone dell'admin dice `prova`", True, d0["prova"])
    da_fare = next(x for x in d0["tappe"] if x["fatto"] is False)
    xp0 = d0["livello"]
    r = segna(ADMIN, {"tappa": da_fare["id"], "fatto": True})
    prova("segnata: 200 e torna nell'elenco", (200, [da_fare["id"]]),
          (r.status_code, r.json().get("finte")))
    d1 = strada(ADMIN)
    t1 = tappa(d1, da_fare["id"])
    prova("sul suo tabellone e' accesa e porta `finta`", (True, True),
          (t1["fatto"], t1.get("finta")))
    prossima = lambda d: next((x["id"] for x in d["tappe"] if x["fatto"] is False), None)
    prova("...e la prossima da fare non e' piu' lei", True,
          prossima(d1) != da_fare["id"])

    print("\n[3) non e' un fatto]")
    prova("livello e XP restano quelli di prima", xp0, d1["livello"])

    print("\n[4) e' solo sua]")
    dA = strada(ANNA)
    tA = tappa(dA, da_fare["id"])
    prova("sul tabellone di Anna la stessa casella non e' accesa",
          (False, None), (tA["fatto"] if tA else False, tA.get("finta") if tA else None))

    print("\n[5) togliere, azzerare, id storti]")
    segna(ADMIN, {"tappa": "foto", "fatto": True})
    r = segna(ADMIN, {"tappa": da_fare["id"], "fatto": False})
    prova("tolta una: resta l'altra", ["foto"], r.json().get("finte"))
    r = segna(ADMIN, {"azzera": True})
    prova("azzerate tutte", [], r.json().get("finte"))
    prova("...e il tabellone torna com'era", d0["tappe"], strada(ADMIN)["tappe"])
    for storto in ("FOTO", "x" * 41, "foto; DROP", "", 7, None):
        prova(f"id storto {storto!r}: 400", 400,
              segna(ADMIN, {"tappa": storto, "fatto": True}).status_code)

    print("\n[6) la leva spenta (17 nov 2026, Andrea: «lascialo spento»)]")
    prova("/api/me la manda accesa", True,
          c.get("/api/me", headers=chi(ADMIN)).json().get("stradina"))
    SRV.STRADINA_ATTIVA = False
    try:
        prova("spenta: il tabellone e' un 404", 404,
              c.get("/api/me/stradina", headers=chi(ADMIN)).status_code)
        prova("spenta: anche la prova dell'admin e' un 404", 404,
              segna(ADMIN, {"tappa": "foto", "fatto": True}).status_code)
        prova("spenta: /api/me la manda spenta", False,
              c.get("/api/me", headers=chi(ADMIN)).json().get("stradina"))
    finally:
        SRV.STRADINA_ATTIVA = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
