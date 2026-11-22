# -*- coding: utf-8 -*-
"""
LE RECENSIONI NASCONDIBILI DAL PROFILO PUBBLICO (22 nov 2026, cantiere
recensioni-nascondibili).

Un utente: «se vado sul profilo di un altro utente, tra le sue
recensioni posso vedere se ha fatto acquisti P2P, di conseguenza so che
lui possiede Bitcoin». Decisione di Andrea: una scelta per utente, di
serie si vede tutto come prima; ognuno puo' nascondere le recensioni
del mercatino, quelle degli scambi P2P, o tutte e due. Le stelle e il
numero restano (nascondere toglie il racconto, mai il voto).

`prove.py` difende la FORMA (i giudici puri, le sentinelle del client).
Qui si cammina su un database vero, con la rotta del negozio vera:

  1. di serie: chi guarda vede tutto, come prima, e le scelte non
     escono dalla risposta;
  2. nascoste le P2P: l'estraneo e l'anonimo non vedono la recensione
     dello scambio, ne' «✅ scambi P2P» ne' «⚡ risponde in fretta»;
     stelle e numero restano; i marchi dei non completati restano;
  3. il proprietario e il moderatore vedono tutto lo stesso;
  4. nascoste quelle del mercatino: resta solo quella dello scambio;
  5. tutte e due: nessuna recensione, le stelle restano;
  6. la rotta: una chiave assente vale «mostra»;
  7. a leva spenta si vede tutto e la rotta risponde 404.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna rete.

USO:  python collaudo_recensioni_nascoste.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
SCAMBIO = "992e288e-aaaa-4a2b-9c3d-00000000aaaa"


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ok {nome}")
    else:
        FALLITE += 1
        print(f"  NO {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


class Busta:
    def __init__(self, dati):
        self.dati = dati

    async def json(self):
        return self.dati


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("ATTENTO: server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-rec-nascoste-"),
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
    # I NUMERI DEL P2P DAL LORO GIUDICE, FINTI: qui non c'e' un libro
    # degli scambi, e quel che si guarda e' se la rotta del negozio li
    # spegne quando le P2P sono nascoste
    server._completati_p2p = lambda con, ids: {222: 5}
    server._veloci_p2p = lambda con, ids, adesso: {222}
    server._marchi_mancati_p2p = lambda con, ids, adesso: {222: 2}
    return db


def chi_guarda(tg_id):
    """Chi apre il profilo (0 = anonimo) e chi tocca l'interruttore."""
    SRV.utente_se_autenticato = (
        (lambda *a, **k: None) if not tg_id
        else (lambda *a, **k: {"id": tg_id}))
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}"}


def scegli(corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.scegli_recensioni_nascoste(Busta(corpo)))


def errore_scelta(corpo):
    try:
        scegli(corpo)
        return None
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


def semina():
    con = SRV.db()
    adesso = int(time.time())
    for tg, nome, neg in ((111, "Compratore", "neg11111"),
                          (222, "Venditore", "neg22222"),
                          (333, "Estraneo", "neg33333"),
                          (999, "Admin", "neg99999")):
        con.execute("INSERT INTO utenti(tg_id, nome, negozio, registrato) "
                    "VALUES(?,?,?,?)", (tg, nome, neg, adesso))
    # due del mercatino e una dello scambio, tutte per il venditore
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato) VALUES(1, 111, 222, 5, 'Pacco perfetto', ?)",
                (adesso - 300,))
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato) VALUES(2, 333, 222, 2, 'Lento', ?)",
                (adesso - 200,))
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato, scambio) VALUES(-7, 111, 222, 5, "
                "'Sats arrivati', ?, ?)", (adesso - 100, SCAMBIO))
    SRV._ricalcola_rating(con, 222)
    con.commit()
    con.close()


def profilo():
    return SRV.negozio("neg22222")


def provenienze(neg):
    return sorted(f["ruolo"] for f in neg["feedback"])


def main():
    avvio()
    semina()

    print("\n[1. di serie si vede tutto, come prima]")
    chi_guarda(333)
    neg = profilo()
    v = neg["venditore"]
    stelle, quante = v["rating"], v["n_feedback"]
    prova("tre recensioni, una dallo scambio", ["scambio", "utente", "utente"],
          provenienze(neg))
    prova("...e i numeri del P2P ci sono", (5, True),
          (v["scambi_completati"], v["risponde_in_fretta"]))
    prova("le due scelte non escono dalla risposta", (False, False),
          ("recensioni_mercatino_nascoste" in v, "recensioni_p2p_nascoste" in v))
    prova("...e le stelle sono la media di tutte e tre", (4.0, 3),
          (stelle, quante))

    print("\n[2. il venditore nasconde le P2P]")
    chi_guarda(222)
    r = scegli({"mercatino": True, "p2p": False})
    prova("la rotta conferma la scelta", {"ok": True, "mercatino": True,
                                          "p2p": False}, r)
    for tg, chi in ((333, "l'estraneo"), (0, "l'anonimo"), (111, "chi l'ha scritta")):
        chi_guarda(tg)
        neg = profilo()
        v = neg["venditore"]
        prova(f"{chi} non vede la recensione dello scambio",
              ["utente", "utente"], provenienze(neg))
        prova(f"...ne' «scambi P2P» ne' «risponde in fretta»", (0, False),
              (v["scambi_completati"], v["risponde_in_fretta"]))
        prova(f"...mentre stelle e numero restano interi", (stelle, quante),
              (v["rating"], v["n_feedback"]))
    prova("il marchio dei non completati RESTA (decisione del 10 ott)", 2,
          v["non_completati"])
    prova("...e le scelte non escono nemmeno adesso", False,
          "recensioni_p2p_nascoste" in v)

    print("\n[3. il proprietario e il moderatore vedono tutto]")
    for tg, chi in ((222, "il proprietario"), (999, "il moderatore")):
        chi_guarda(tg)
        neg = profilo()
        prova(f"{chi} vede anche quella dello scambio",
              ["scambio", "utente", "utente"], provenienze(neg))
        prova(f"...e i numeri del P2P", 5, neg["venditore"]["scambi_completati"])

    print("\n[4. nascoste quelle del mercatino]")
    chi_guarda(222)
    scegli({"mercatino": False, "p2p": True})
    chi_guarda(333)
    neg = profilo()
    prova("resta solo quella dello scambio", ["scambio"], provenienze(neg))
    prova("...e i numeri del P2P tornano", (5, True),
          (neg["venditore"]["scambi_completati"],
           neg["venditore"]["risponde_in_fretta"]))

    print("\n[5. tutte e due nascoste]")
    chi_guarda(222)
    scegli({"mercatino": False, "p2p": False})
    chi_guarda(333)
    neg = profilo()
    prova("nessuna recensione", [], neg["feedback"])
    prova("...le stelle restano", (stelle, quante),
          (neg["venditore"]["rating"], neg["venditore"]["n_feedback"]))

    print("\n[6. una chiave assente vale «mostra»]")
    chi_guarda(222)
    r = scegli({})
    prova("corpo vuoto = tutto visibile", {"ok": True, "mercatino": True,
                                          "p2p": True}, r)
    chi_guarda(333)
    prova("...e il profilo torna come prima",
          ["scambio", "utente", "utente"], provenienze(profilo()))

    print("\n[7. a leva spenta si vede tutto]")
    chi_guarda(222)
    scegli({"mercatino": False, "p2p": False})
    SRV.RECENSIONI_NASCONDIBILI = False
    chi_guarda(333)
    neg = profilo()
    prova("le scelte salvate non contano", ["scambio", "utente", "utente"],
          provenienze(neg))
    prova("...e i numeri del P2P si vedono", 5,
          neg["venditore"]["scambi_completati"])
    chi_guarda(222)
    prova("la rotta della scelta risponde 404", 404,
          errore_scelta({"p2p": False}))
    con = SRV.db()
    salvate = con.execute("SELECT recensioni_mercatino_nascoste, "
                          "recensioni_p2p_nascoste FROM utenti WHERE tg_id=222"
                          ).fetchone()
    con.close()
    prova("...e le scelte restano salvate", (1, 1), tuple(salvate))
    SRV.RECENSIONI_NASCONDIBILI = True

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
