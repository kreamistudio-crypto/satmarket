# -*- coding: utf-8 -*-
"""
I CONTI DEL P2P, SUL SERVER VERO (10 ott 2026, cantiere statistiche-p2p).

`prove.py` difende i giudici estratti (`prove_statistiche_p2p`): i conti
con scambi di ogni tipo, i periodi, il registro. Qui gira il SERVER
VERO, col suo schema e la sua rotta, e si guarda quel che una sentinella
sul testo non puo' dire — che il rifiuto AVVIENE:

  1. la porta: a lista vuota la rotta dice 403 anche all'admin; con la
     lista piena passa l'amministratore, e NON il moderatore che non e'
     in lista, NON l'utente normale, NON chi e' in lista senza essere
     moderatore; un periodo inventato e' un 400;
  2. i due scambi di controllo di Andrea, raccontati dalla porta del
     coordinatore coi suoi tre importi (50 €: 64.960 / 63.352, 100 €:
     123.127 / 120.689): 4.046 sats di commissioni; senza il nodo il
     routing e' «non disponibile» e le nette non hanno una cifra;
  3. la risposta si tiene un minuto — e il moderatore prende 403 anche
     quando la risposta dell'amministratore e' gia' in cache;
  4. col nodo (LND di cartone): routing 7 + 243 = 250, nette 3.796;
  5. il cruscotto dice a ognuno il suo si' o no, e non porta le uscite
     di LND a nessuno;
  6. la scopa dei quaranta giorni passa SOLO dopo i conti, e dopo di
     lei i numeri sono gli stessi.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente nodo.

USO:  python collaudo_statistiche_p2p.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco

A = "5a1e0000-c0c0-4a2b-9c3d-0000000000a1"      # 50 €
B = "5a1e0000-c0c0-4a2b-9c3d-0000000000b2"      # 100 €
C = "5a1e0000-c0c0-4a2b-9c3d-0000000000c3"      # in corso
AMMINISTRATORE, MODERATORE = 999, 500
LND = {"stato": "assente", "motivo": "LND non configurato su questo server"}


def conti(periodo="7"):
    """La rotta vera: la risposta, o il rifiuto come (codice, frase)."""
    SRV = banco.SRV
    try:
        r = asyncio.run(SRV.statistiche_p2p_admin(
            periodo=periodo, x_tg_init_data="", barattolo_sessione=""))
        return json.loads(r.body)
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def codice(risposta):
    return risposta[0] if isinstance(risposta, tuple) else 200


def scambio(ordine, t, **importi):
    for n, (azione, attore, dettaglio) in enumerate((
            ("taken", "buyer", None), ("buyer-invoice-added", "buyer", "hold-next"),
            ("hold-invoice-requested", "mostro", "invoice"),
            ("hold-invoice-paid", "seller", "active"), ("fiat-sent", "buyer", None))):
        banco.evento(ordine, azione, t + n * 10, attore, dettaglio)
    if importi:
        banco.evento(ordine, "released", t + 60, "seller", None, **importi)
        banco.evento(ordine, "success", t + 70, "mostro", None, **importi)
    return t + 60


def main():
    banco.avvio()
    banco.semina()
    prova, SRV = banco.prova, banco.SRV
    adesso = int(time.time())
    t = adesso - 600
    con = banco.con_db()
    for ordine, euro, metodi in ((A, "50,00 €", '["SEPA"]'),
                                 (B, "100,00 €", '["Revolut"]'),
                                 (C, "20,00 €", '["Contanti"]')):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                    "visto,preso_da,euro,metodi) VALUES(?,?,?,?,'sell',1,?,?,?,?)",
                    (ordine, banco.VENDE, t, "in-progress" if ordine == C else
                     "success", adesso, banco.COMPRA, euro, metodi))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(?,?,?,1,'')", (MODERATORE, "Chi modera", "negmod"))
    con.execute("UPDATE utenti SET coorte='pioniere' WHERE tg_id=?", (banco.COMPRA,))
    con.commit()
    con.close()
    # chi modera: l'admin del collaudo e un moderatore in piu'
    SRV.ADMIN_IDS = [AMMINISTRATORE, MODERATORE]
    SRV.P2P_SCONTO_FEDELTA_PERCENTO = 0.5

    async def lnd_finto(nostri, rimborsi=frozenset()):
        return dict(LND)

    async def cambio_finto():
        return 0
    SRV.dati_lnd_cruscotto = lnd_finto
    SRV.cambio_btc_eur = cambio_finto
    chiuso_a = scambio(A, t, sats=64000, sats_buyer=63352, sats_seller=64960)
    chiuso_b = scambio(B, t + 100, sats=121908, sats_buyer=120689, sats_seller=123127)
    scambio(C, t + 200)

    print("\n1) la porta")
    SRV.P2P_STATISTICHE_IDS = set()
    banco.come(AMMINISTRATORE)
    prova("lista vuota: 403 anche all'admin del collaudo", 403, codice(conti()))
    prova("...e non ha scritto niente nel registro", 0, banco.con_db().execute(
        "SELECT COUNT(*) FROM p2p_conti").fetchone()[0])
    SRV.P2P_STATISTICHE_IDS = {AMMINISTRATORE}
    banco.come(MODERATORE)
    prova("il moderatore che non e' in lista: 403", (403, "Riservato agli amministratori"),
          conti())
    banco.come(banco.ESTRANEO)
    prova("l'utente normale: 403", 403, codice(conti()))
    SRV.P2P_STATISTICHE_IDS = {AMMINISTRATORE, banco.ESTRANEO}
    prova("...anche se e' finito in lista: non e' un moderatore", 403, codice(conti()))
    SRV.P2P_STATISTICHE_IDS = {AMMINISTRATORE}
    prova("nessuno dei rifiutati ha fatto nascere una riga o una cache", (0, {}),
          (banco.con_db().execute("SELECT COUNT(*) FROM p2p_conti").fetchone()[0],
           dict(SRV._p2p_conti_cache)))
    banco.come(AMMINISTRATORE)
    prova("l'amministratore con un periodo inventato: 400", 400,
          codice(conti("sempre")))

    print("\n2) i due scambi di controllo, senza il nodo")
    d = conti()
    prova("l'amministratore passa", 200, codice(d))
    if codice(d) != 200:
        print(f"\n{banco.PASSATE} ok, {banco.FALLITE + 1} NO")
        return 1
    prova("2 completati, 1 in corso, tasso 100%", (2, 0, 1, 100.0),
          (d["scambi"]["completati"], d["scambi"]["annullati"],
           d["scambi"]["in_corso"], d["scambi"]["tasso"]))
    prova("150 € e 185.908 sats", (150.0, 185908),
          (d["volume"]["euro"], d["volume"]["sats"]))
    prova("commissioni incassate: 4.046 sats", 4046, d["commissioni"]["lorde_sats"])
    prova("chi vende a fee piena, chi compra da pioniere",
          ((2, 960 + 1219), (2, 648 + 1219)),
          tuple((d["commissioni"]["fette"][k]["meta"], d["commissioni"]["fette"][k]["sats"])
                for k in ("piena", "pioniere")))
    prova("routing «non disponibile», col perche' — e le nette senza cifra",
          ("assente", None, "LND non configurato su questo server"),
          (d["commissioni"]["routing"]["stato"], d["commissioni"]["nette_sats"],
           d["lnd"]["motivo"]))
    prova("gli ultimi scambi portano iniziali, mai un nome",
          [("V.", "C."), ("V.", "C.")],
          [(u["pubblica"], u["prende"]) for u in d["ultimi"]])
    prova("la risposta non si tiene nel browser", "no-store",
          asyncio.run(SRV.statistiche_p2p_admin(
              periodo="7", x_tg_init_data="", barattolo_sessione=""))
          .headers.get("cache-control"))

    print("\n3) la cache di un minuto, e la porta davanti a lei")
    LND.update(stato="ok", motivo="")
    h = lambda c: c * 64                       # mai un esadecimale intero nel sorgente
    SRV._cruscotto_lnd["uscite"] = SRV.uscite_altrui_lnd([
        {"payment_hash": h("a"), "status": "SUCCEEDED", "value_sat": "63352",
         "fee_msat": "7000", "creation_time_ns": str((chiuso_a + 3) * 10 ** 9)},
        {"payment_hash": h("b"), "status": "SUCCEEDED", "value_sat": "120689",
         "fee_msat": "243000", "creation_date": str(chiuso_b + 5)}], set())
    prova("dentro il minuto la risposta e' quella di prima: il nodo non si richiama",
          "assente", conti()["commissioni"]["routing"]["stato"])
    banco.come(MODERATORE)
    prova("...e il moderatore prende 403 anche con la risposta gia' in cache", 403,
          codice(conti()))
    banco.come(AMMINISTRATORE)

    print("\n4) col nodo")
    SRV._p2p_conti_cache.clear()
    d = conti()
    prova("routing 7 + 243 = 250 sats, nette 3.796",
          ({"stato": "ok", "sats": 250, "abbinati": 2, "mancanti": 0}, 3796),
          (d["commissioni"]["routing"], d["commissioni"]["nette_sats"]))
    prova("...riga per riga", [(2438, 243), (1608, 7)],
          [(u["commissione"], u["routing"]) for u in d["ultimi"]])
    prova("nel registro, del pagamento, resta solo il capo dell'hash",
          ["a" * 16, "b" * 16],
          sorted(r[0] for r in banco.con_db().execute(
              "SELECT routing_rif FROM p2p_conti WHERE esito='completato'")))

    print("\n5) il cruscotto dice a ognuno il suo si' o no")

    def cruscotto():
        return asyncio.run(SRV.cruscotto_admin(x_tg_init_data="", barattolo_sessione=""))
    cr = cruscotto()
    prova("all'amministratore si'", True, cr.get("p2p_statistiche"))
    banco.come(MODERATORE)
    cr = cruscotto()
    prova("al moderatore no", False, cr.get("p2p_statistiche"))
    prova("...e le uscite di LND non viaggiano a nessuno", False,
          "uscite" in json.dumps(cr))
    banco.come(AMMINISTRATORE)

    print("\n6) i conti prima della scopa")
    prima = conti("tutto")
    dopo_la_memoria = adesso + SRV.P2P_LIBRO_MEMORIA_S + 3600
    con = banco.con_db()
    prova("i conti sono in salvo", True, SRV._conti_salvi_p2p(con, dopo_la_memoria))
    tolte = SRV._pulisci_memoria_p2p(con, dopo_la_memoria)
    prova("la scopa porta via la cronaca e le parti", (True, 0, 0),
          (tolte > 0,
           con.execute("SELECT COUNT(*) FROM p2p_momenti").fetchone()[0],
           con.execute("SELECT COUNT(*) FROM p2p_scambi").fetchone()[0]))
    con.close()
    SRV._p2p_conti_cache.clear()
    dopo = conti("tutto")
    prova("...e i conti di «tutto» sono gli stessi, tranne chi era in corso",
          (prima["scambi"]["completati"], prima["volume"], prima["commissioni"], 0),
          (dopo["scambi"]["completati"], dopo["volume"], dopo["commissioni"],
           dopo["scambi"]["in_corso"]))

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
