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
  3. il proprietario vede tutto lo stesso, il moderatore no (dal 23
     nov 2026: «Quelle nascoste le vedi sempre solo tu.»);
     3b. (23 nov) le CARD del P2P — il volto sul libro e quella
     dell'altra parte — tacciono «scambi P2P» e «risponde in fretta»
     per tutti; il marchio dei non completati resta;
     3c. (23 nov) le negative, 1 e 2 stelle, non si nascondono mai;
  4. nascoste quelle del mercatino: resta quella dello scambio (e la
     negativa del mercatino);
  5. tutte e due: resta solo la negativa, le stelle restano;
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

    print("\n[3. solo il proprietario vede tutto]")
    chi_guarda(222)
    neg = profilo()
    prova("il proprietario vede anche quella dello scambio",
          ["scambio", "utente", "utente"], provenienze(neg))
    prova("...e i numeri del P2P", 5, neg["venditore"]["scambi_completati"])
    # (23 nov 2026) il moderatore NO: Andrea ha scelto «Quelle nascoste le
    # vedi sempre solo tu.», via anche ai moderatori
    chi_guarda(999)
    neg = profilo()
    prova("il moderatore non vede quella dello scambio",
          ["utente", "utente"], provenienze(neg))
    prova("...ne' i numeri del P2P", (0, False),
          (neg["venditore"]["scambi_completati"],
           neg["venditore"]["risponde_in_fretta"]))

    print("\n[3b. le card del P2P tacciono i conclusi, per tutti]")
    # (23 nov 2026, cantiere scambi-p2p-nascosti-scheda; Andrea: «deve
    # sparire anche da lì [...] gli scambi non completati non devono
    # sparire, ma quelli conclusi sì»). Il volto sulla card del libro e
    # la card dell'altra parte: niente «✅ scambi P2P» né «⚡ risponde in
    # fretta», il marchio dei non completati resta. Qui non c'e' chi
    # guarda: sulle card vale per tutti, moderatore compreso.
    con = SRV.db()
    con.execute("INSERT INTO p2p_ordini(ordine, tg_id, creato) VALUES(?,?,?)",
                (SCAMBIO, 222, int(time.time())))
    con.commit()
    adesso = int(time.time())
    faccia = SRV._facce_ordini_p2p(con, [SCAMBIO], adesso)[SCAMBIO]
    volto = SRV._volti_persone(con, [222], adesso)[222]
    prova("la card del libro: niente «scambi P2P» né «risponde in fretta»",
          (False, False), ("completati" in faccia, "veloce" in faccia))
    prova("...il marchio dei non completati resta", 2, faccia.get("mancati"))
    prova("...stelle e numero restano", (stelle, quante),
          (faccia["media"], faccia["voti"]))
    prova("la card dell'altra parte: niente «scambi P2P» né «risponde in "
          "fretta»", (False, False), ("completati" in volto, "veloce" in volto))
    prova("...il marchio dei non completati resta", 2, volto.get("mancati"))
    con.close()

    print("\n[3c. una negativa dello scambio resta, con le P2P spente]")
    # (23 nov 2026) una da 1 stella da uno scambio: le P2P sono spente,
    # ma le negative non si nascondono mai
    con = SRV.db()
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, voto, "
                "commento, creato, scambio) VALUES(-8, 333, 222, 1, "
                "'Mai arrivati', ?, ?)", (int(time.time()) - 50,
                                         "992e288e-bbbb-4a2b-9c3d-00000000bbbb"))
    con.commit()
    con.close()
    chi_guarda(333)
    neg = profilo()
    prova("l'estraneo vede la negativa dello scambio, non la positiva",
          [("scambio", 1), ("utente", 2), ("utente", 5)],
          sorted((f["ruolo"], f["voto"]) for f in neg["feedback"]))
    con = SRV.db()
    con.execute("DELETE FROM feedback WHERE ordine_id=-8")
    con.commit()
    con.close()

    print("\n[4. nascoste quelle del mercatino]")
    chi_guarda(222)
    scegli({"mercatino": False, "p2p": True})
    chi_guarda(333)
    neg = profilo()
    # la negativa del mercatino («Lento», 2 stelle) NON si nasconde mai
    # (23 nov 2026, Andrea: «quelle da 1 o 2 stelle, devono restare
    # sempre visibili»)
    prova("resta quella dello scambio, e la negativa del mercatino",
          ["scambio", "utente"], provenienze(neg))
    prova("...che e' proprio «Lento», da 2 stelle", [2],
          [f["voto"] for f in neg["feedback"] if f["ruolo"] == "utente"])
    prova("...e i numeri del P2P tornano", (5, True),
          (neg["venditore"]["scambi_completati"],
           neg["venditore"]["risponde_in_fretta"]))
    con = SRV.db()
    faccia = SRV._facce_ordini_p2p(con, [SCAMBIO], int(time.time()))[SCAMBIO]
    volto = SRV._volti_persone(con, [222], int(time.time()))[222]
    con.close()
    prova("...anche sulle due card del P2P", (5, True, 5, True),
          (faccia.get("completati"), faccia.get("veloce"),
           volto.get("completati"), volto.get("veloce")))

    print("\n[5. tutte e due nascoste]")
    chi_guarda(222)
    scegli({"mercatino": False, "p2p": False})
    chi_guarda(333)
    neg = profilo()
    prova("resta solo la negativa, da 2 stelle", [("utente", 2)],
          [(f["ruolo"], f["voto"]) for f in neg["feedback"]])
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
    con = SRV.db()
    prova("...anche sulle card del P2P", (5, 5),
          (SRV._facce_ordini_p2p(con, [SCAMBIO], int(time.time()))[SCAMBIO]
           .get("completati"),
           SRV._volti_persone(con, [222], int(time.time()))[222]
           .get("completati")))
    con.close()
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
