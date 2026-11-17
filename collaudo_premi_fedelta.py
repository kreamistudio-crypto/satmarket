# -*- coding: utf-8 -*-
"""I PREMI FEDELTA' DEL NEGOZIO, fatti girare per davvero (17 nov 2026,
cantiere premi-fedelta).

`prove.py` guarda i pezzi uno per uno (il giudice delle soglie, il
conto, l'aggancio). Qui gira la STORIA sulle rotte vere del server, su
un database usa-e-getta:

  · il venditore scrive i suoi gradini dal Profilo (POST
    /api/me/premi-fedelta), e i no: la chiave assente, le soglie fuori
    misura, il regalo vuoto, i doppioni, troppi gradini;
  · /api/me gli restituisce la lista pulita e le misure del cassetto;
  · la pagina del negozio li mostra a tutti, e a chi guarda da cliente
    dice quanto ha gia' speso li' (al venditore stesso no);
  · un affare concluso fa passare la soglia: l'avviso a tutti e due,
    una volta sola, e il premio compare sul prossimo ordine pagato in
    /api/orders, per le due parti e per nessun altro;
  · la leva spenta: la rotta dice no, la vetrina non promette niente.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server; nessuna rete, nessun LNbits, nessun avviso
spedito (la notifica e' di cartone).

USO:  python collaudo_premi_fedelta.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
AVVISI = []

COMPRA = 111
VENDE = 222
ALTRO = 333
NOMI = {COMPRA: "Compra", VENDE: "Un tempo per te", ALTRO: "Altro"}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def rifiuto(nome, codice, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        c = getattr(e, "status_code", None)
        t = str(getattr(e, "detail", e))
        if c == codice and (not dentro or dentro.lower() in t.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {codice} {dentro!r}\n      avuto:  {c} {t!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script deve "
                         "installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-premi-"),
                      "usa-e-getta.db")
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
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def zitta(chi=None, testo="", *a, **k):
        AVVISI.append((chi, testo))
    server.notifica = zitta
    server.init_db()
    return db


def testata(tg_id):
    return f"collaudo:{tg_id}:{NOMI.get(tg_id, 'Utente')}"


def salva(tg_id, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.imposta_premi_fedelta(
        None, x_tg_init_data=testata(tg_id), barattolo_sessione=""))


def vetrina(chi_guarda=None):
    return SRV.negozio("neg222", x_tg_init_data=(
        testata(chi_guarda) if chi_guarda else ""),
        barattolo_sessione="", limit=0, cursore="", da="",
        vista=0)["venditore"]


def ordini(tg_id):
    return {r["id"]: r for r in SRV.miei_ordini(
        0, x_tg_init_data=testata(tg_id), barattolo_sessione="")}


def semina(db):
    con = sqlite3.connect(db)
    for tg, nome in NOMI.items():
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                    "VALUES(?,?,?,?)", (tg, nome, f"u{tg}", f"neg{tg}"))
    con.execute("INSERT OR REPLACE INTO annunci(id,titolo,descrizione,prezzo_sats,"
                "venditore_id,stato,categoria,quantita,consegna,zona,valuta) "
                "VALUES(1,'La candela','x',100000,222,'attivo','Casa',50,"
                "'spedizione','Pavia (PV)','sats')")
    con.commit()
    con.close()


def ordine(db, stato, euro, compratore=COMPRA, cambio=50_000.0):
    con = sqlite3.connect(db)
    oid = con.execute(
        "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
        "prezzo_sats,stato,cambio_eur,creato,aggiornato) "
        "VALUES(1,?,222,?,?,?,1,1)",
        (compratore, int(euro / cambio * 100_000_000), stato, cambio)
    ).lastrowid
    con.commit()
    con.close()
    return oid


def main():
    print("=" * 58)
    print("  I PREMI FEDELTÀ DEL NEGOZIO — il giro vero")
    print("=" * 58)
    db = avvio()
    semina(db)

    print("\n[il venditore scrive i suoi gradini]")
    rifiuto("senza la chiave `premi`: 400, mai uno spegnimento muto", 400,
            lambda: salva(VENDE, {}))
    rifiuto("soglia sotto il minimo", 400,
            lambda: salva(VENDE, {"premi": [{"soglia": 5, "premio": "x"}]}),
            "da 10")
    rifiuto("regalo vuoto", 400,
            lambda: salva(VENDE, {"premi": [{"soglia": 100, "premio": " "}]}),
            "scrivi il regalo")
    rifiuto("due premi sulla stessa soglia", 400,
            lambda: salva(VENDE, {"premi": [{"soglia": 100, "premio": "a"},
                                            {"soglia": 100, "premio": "b"}]}),
            "stessa soglia")
    rifiuto("piu' di quattro gradini", 400,
            lambda: salva(VENDE, {"premi": [
                {"soglia": 10 * (i + 1), "premio": "p"} for i in range(5)]}),
            "al massimo")
    d = salva(VENDE, {"premi": [{"soglia": 200, "premio": "la tazza"},
                                {"soglia": 100, "premio": "la borsa"}]})
    prova("salvati, in ordine di soglia", [
        {"soglia": 100, "premio": "la borsa"},
        {"soglia": 200, "premio": "la tazza"}], d["premi"])
    me = asyncio.run(SRV.mio_profilo(x_tg_init_data=testata(VENDE),
                                     barattolo_sessione=""))
    prova("/api/me li restituisce puliti", d["premi"], me["premi_fedelta"])
    prova("...con le misure del cassetto", (True, 4, 10, 60), (
        me["premi_fedelta_leve"]["attivo"], me["premi_fedelta_leve"]["max"],
        me["premi_fedelta_leve"]["min_eur"],
        me["premi_fedelta_leve"]["testo_max"]))

    print("\n[la pagina del negozio]")
    v = vetrina()
    prova("chi passa vede i gradini", d["premi"], v["premi_fedelta"])
    prova("...ma nessun conto (non e' un cliente)", False,
          "speso_qui_eur" in v)
    prova("il venditore sul suo negozio: nessun conto", False,
          "speso_qui_eur" in vetrina(VENDE))
    ordine(db, "released", 60)
    prova("il cliente vede quanto ha speso li'", 60.0,
          vetrina(COMPRA).get("speso_qui_eur"))

    print("\n[l'affare che passa la soglia]")
    ordine(db, "released", 50)
    AVVISI.clear()
    asyncio.run(SRV.premia_fedelta_negozio(COMPRA, VENDE))
    prova("l'avviso a tutti e due", [COMPRA, VENDE], [a[0] for a in AVVISI])
    prova("...a chi compra: cosa trova e dove", True,
          "la borsa" in AVVISI[0][1] and "Un tempo per te" in AVVISI[0][1])
    prova("...a chi vende: cosa mettere nel pacco", True,
          "metti <b>la borsa</b>" in AVVISI[1][1])
    AVVISI.clear()
    asyncio.run(SRV.premia_fedelta_negozio(COMPRA, VENDE))
    prova("una volta sola", [], AVVISI)

    print("\n[il premio sul prossimo ordine]")
    nuovo = ordine(db, "locked", 20)
    altrui = ordine(db, "locked", 20, compratore=ALTRO)
    prova("chi compra lo vede sul suo ordine pagato",
          {"soglia": 100, "premio": "la borsa"},
          ordini(COMPRA)[nuovo].get("premio_fedelta"))
    prova("chi vende pure", "la borsa",
          (ordini(VENDE)[nuovo].get("premio_fedelta") or {}).get("premio"))
    prova("l'ordine di un altro cliente no", None,
          ordini(VENDE)[altrui].get("premio_fedelta"))
    prova("...e l'altro cliente non vede niente", None,
          ordini(ALTRO)[altrui].get("premio_fedelta"))

    print("\n[la leva spenta]")
    SRV.PREMI_FEDELTA_ATTIVI = False
    rifiuto("la rotta dice no", 400,
            lambda: salva(VENDE, {"premi": []}), "non sono attivi")
    prova("la vetrina non promette niente", [], vetrina()["premi_fedelta"])
    prova("il premio gia' attaccato resta scritto", "la borsa",
          (ordini(COMPRA)[nuovo].get("premio_fedelta") or {}).get("premio"))
    SRV.PREMI_FEDELTA_ATTIVI = True

    print("\n[togliere tutto]")
    prova("la lista vuota spegne", [], salva(VENDE, {"premi": []})["premi"])
    prova("...e la vetrina torna muta", [], vetrina()["premi_fedelta"])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
