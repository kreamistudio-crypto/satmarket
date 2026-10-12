# -*- coding: utf-8 -*-
"""
LE DISPUTE P2P NEL CRUSCOTTO, SUL SERVER VERO (12 ott 2026, cantiere
dispute-nel-cruscotto).

`prove.py` difende il giudice estratto (`prove_dispute_cruscotto_p2p`): i
conti finestra per finestra, la soglia, il timbro. Qui gira il SERVER
VERO, col suo schema, la sua rotta e il suo battito dell'ora, e gli
eventi nella forma che la patch 0007 manda davvero:

  1. la porta: il cruscotto e' dei moderatori — 403 all'utente normale —
     e la sezione delle dispute arriva a OGNI moderatore, anche a chi non
     vede i conti del P2P;
  2. cinque scambi presi dalla porta del coordinatore: uno non arriva
     alla garanzia (chiesta, mai pagata) e NON entra nel denominatore;
     degli altri quattro uno finisce in disputa: 1 su 4 con garanzia,
     25%, un'aperta col suo id ACCORCIATO, e nella risposta nessuna
     chiave, nessun id intero;
  3. un moderatore la decide a favore di chi compra: zero aperte, una a
     chi compra, una decisa da un moderatore;
  4. il battito VERO dell'ora: sotto le tre dispute tace anche al 25%;
     alla terza parte UN avviso ai moderatori; l'ora dopo tace; dopo un
     riavvio (la memoria del processo persa) tace ancora: il timbro sta
     nel database; a leva spenta tace del tutto;
  5. la scopa dei quaranta giorni: i conti di «da sempre» restano gli
     stessi — registro e `p2p_dispute` non si potano —, e la garanzia
     non e' piu' dedotta: sta SCRITTA nel registro, riga per riga.

E DAL 12 OTT 2026 (cantiere dispute-garanzia-escluse):

  0. il database di IERI: un registro senza la colonna `garanzia`, con
     una riga dentro; la migrazione vera (`init_db`) la aggiunge, la
     riga vecchia resta «non si sa» e la sezione la conta per deduzione,
     dicendolo (`dedotti`);
  4-bis. una disputa tolta dal conto con `P2P_DISPUTE_ESCLUSE`: esce da
     dispute e aperte, la sezione la nomina, il suo scambio resta — e il
     battito dell'ora TACE (due dispute); tolta la leva, parte.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente nodo.

USO:  python collaudo_dispute_cruscotto.py
"""

import asyncio
import json
import sys
import time

import collaudo_pagamento_p2p as banco
import collaudo_dispute_p2p as dispute

# il primo gruppo CAMBIA da un ordine all'altro: e' quello che si legge
# nell'id accorciato
O = ["d1c0%04x-5a1e-4a2b-9c3d-0000000000aa" % n for n in range(1, 9)]
AMMINISTRATORE, MODERATORE = 999, 500
AVVISATI = []          # i testi arrivati a `notifica_admin`


def cruscotto():
    """La rotta vera: la risposta, o il rifiuto come codice."""
    try:
        return asyncio.run(banco.SRV.cruscotto_admin(
            x_tg_init_data="", barattolo_sessione=""))
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


def concluso(ordine, t):
    """Uno scambio preso e arrivato in fondo senza storie."""
    dispute.manda(ordine, "taken", t, "buyer", "take")
    dispute.manda(ordine, "hold-invoice-paid", t + 10, "seller")
    dispute.manda(ordine, "fiat-sent", t + 20, "buyer")
    dispute.manda(ordine, "released", t + 30, "seller")
    dispute.manda(ordine, "success", t + 40, "mostro")


def battito(riavvio=False):
    """Un battito VERO delle attese con l'ora di pulizia scaduta: torna
    gli avvisi partiti verso i moderatori in QUESTO battito."""
    SRV = banco.SRV
    if riavvio:
        SRV._P2P_ATTESE.clear()
        SRV._P2P_ATTESE["scade"] = 0
    else:
        SRV._P2P_ATTESE["pulito"] = 0
    prima = len(AVVISATI)
    banco.giro_attese()
    return AVVISATI[prima:]


def main():
    banco.avvio()
    banco.semina()
    prova, SRV = banco.prova, banco.SRV
    adesso = int(time.time())
    t = adesso - 800            # dentro i 15 minuti d'orologio degli eventi
    con = banco.con_db()
    for ordine in O:
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                    "13603,'10,00 €','[\"SEPA\"]')", (ordine, banco.VENDE, t - 600))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(?,?,?,1,'')", (MODERATORE, "Chi modera", "negmod"))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [AMMINISTRATORE, MODERATORE]
    SRV.P2P_STATISTICHE_IDS = {AMMINISTRATORE}
    SRV.P2P_DISPUTE_SOGLIA_PERCENTO = 5.0
    SRV._p2p_leve = lambda *a, **k: {"attivo": True}

    async def lnd_finto(nostri, rimborsi=frozenset()):
        return {"stato": "assente", "motivo": "LND non configurato su questo server"}

    async def cambio_finto():
        return 0

    async def zap_finto():
        return None

    async def admin_finto(testo, *a, **k):
        AVVISATI.append(testo)
    SRV.dati_lnd_cruscotto = lnd_finto
    SRV.cambio_btc_eur = cambio_finto
    SRV.dati_zap_cruscotto = zap_finto
    SRV.notifica_admin = admin_finto

    print("\n0) il database di ieri: la colonna arriva con la migrazione")
    VECCHIA = "c0de0000-5a1e-4a2b-9c3d-0000000000aa"
    con = banco.con_db()
    con.execute("ALTER TABLE p2p_conti DROP COLUMN garanzia")
    con.execute("INSERT INTO p2p_conti(ordine, giro, esito, preso, chiuso) "
                "VALUES(?, 1, 'completato', ?, ?)",
                (VECCHIA, adesso - 50 * 86400, adesso - 50 * 86400 + 600))
    con.commit()
    prova("senza la colonna la sezione non c'e' (None) e niente alza", None,
          SRV.dati_dispute_p2p(con, adesso))
    con.close()
    SRV.init_db()
    con = banco.con_db()
    prova("la migrazione vera aggiunge la colonna, e la riga di ieri nasce "
          "a «non si sa»", [-1],
          [r[0] for r in con.execute("SELECT garanzia FROM p2p_conti")])
    SRV.init_db()
    prova("...due volte non fa danni", [-1],
          [r[0] for r in con.execute("SELECT garanzia FROM p2p_conti")])
    v = SRV.dati_dispute_p2p(con, adesso)
    prova("...e la sezione la conta per deduzione (concluso = con "
          "garanzia), dicendo che e' dedotta", (1, 1, 1),
          (v["periodi"]["tutto"]["presi"], v["periodi"]["tutto"]["con_garanzia"],
           v["dedotti"]))
    con.execute("DELETE FROM p2p_conti WHERE ordine=?", (VECCHIA,))
    con.commit()
    con.close()

    print("\n1) la porta")
    banco.come(banco.ESTRANEO)
    prova("l'utente normale: 403, nessun numero", 403, cruscotto())
    banco.come(MODERATORE)
    cr = cruscotto()
    prova("il moderatore che NON vede i conti del P2P riceve la sezione "
          "delle dispute", (False, True),
          (cr.get("p2p_statistiche"), isinstance(cr.get("dispute_p2p"), dict)))
    prova("...che su un mercatino senza scambi non inventa uno zero", (0, None),
          (cr["dispute_p2p"]["periodi"]["tutto"]["presi"],
           cr["dispute_p2p"]["periodi"]["tutto"]["percento"]))

    print("\n2) cinque scambi presi, quattro con garanzia, uno in disputa")
    for n in range(3):
        concluso(O[n], t + n * 100)
    dispute.fino_alla_disputa(O[3], t + 300)
    # una presa che non arriva alla garanzia: chiesta, mai pagata, e il
    # coordinatore chiude. E' uno scambio preso, non uno con garanzia
    dispute.manda(O[6], "taken", t + 350, "buyer", "take")
    dispute.manda(O[6], "hold-invoice-requested", t + 360, "mostro", "invoice")
    dispute.manda(O[6], "canceled", t + 370, "mostro", "maker-timeout")
    d = cruscotto()["dispute_p2p"]
    p30 = d["periodi"]["30"]
    prova("30 giorni: 5 scambi presi, 4 con garanzia, 1 disputa — e la "
          "percentuale e' sui 4: 25%", (5, 4, 1, 25.0),
          (p30["presi"], p30["con_garanzia"], p30["con_disputa"], p30["percento"]))
    prova("...lo stesso in 7 giorni e da sempre", [(5, 4, 1, 25.0)] * 2,
          [(d["periodi"][k]["presi"], d["periodi"][k]["con_garanzia"],
            d["periodi"][k]["con_disputa"], d["periodi"][k]["percento"])
           for k in ("7", "tutto")])
    prova("...aperta, col suo id accorciato, e nessun moderatore l'ha presa",
          [(O[3][:8], False)], [(a["ordine"], a["presa"]) for a in d["aperte"]])
    prova("...e prima non c'erano scambi: nessuna tendenza inventata", None,
          p30["tendenza"])
    prova("sotto le tre dispute non si e' «sopra», nemmeno al 25%", False,
          d["soglia"]["sopra"])
    testo = json.dumps(d)
    prova("nella sezione nessuna chiave e nessun id d'ordine intero",
          (False, False, False),
          (banco.CHIAVE_COMPRA in testo, banco.CHIAVE_VENDE in testo,
           any(o in testo for o in O)))
    prova("...e le sole voci previste",
          ["aperte", "dal", "dedotti", "escluse", "periodi", "soglia"], sorted(d))
    prova("...niente di dedotto (la cronaca c'e' tutta) e niente di escluso",
          (0, []), (d["dedotti"], d["escluse"]))
    banco.come(banco.ESTRANEO)
    prova("l'utente normale resta fuori anche coi numeri dentro", 403, cruscotto())
    banco.come(MODERATORE)

    print("\n3) un moderatore la decide a favore di chi compra")
    dispute.manda(O[3], "released", t + 400, "mostro", "admin")
    p30 = cruscotto()["dispute_p2p"]["periodi"]["30"]
    prova("zero aperte, una a chi compra, una decisa da un moderatore",
          (0, 1, 0, 1, 25.0),
          (p30["aperte"], p30["compratore"], p30["venditore"], p30["moderatore"],
           p30["percento"]))

    print("\n4) l'avviso, dal battito vero dell'ora")
    AVVISATI.clear()
    prova("una disputa su quattro scambi con garanzia: il battito tace", [],
          battito())
    dispute.fino_alla_disputa(O[4], t + 500, da="seller")
    prova("due su cinque (40%): tace ancora, mancano le tre dispute", [],
          battito())
    dispute.fino_alla_disputa(O[5], t + 600)
    partiti = battito()
    prova("tre su sei: parte UN avviso ai moderatori", 1, len(partiti))
    avviso = partiti[0] if partiti else ""
    prova("...coi numeri — 3 su 6, 50%, la soglia — e le due aperte per id "
          "corto", [],
          [x for x in ("3 scambi su 6 con garanzia", "<b>50%</b>",
                       "la soglia è 5%",
                       f"<code>{O[4][:8]}</code>", f"<code>{O[5][:8]}</code>")
           if x not in avviso])
    prova("...senza una chiave, senza un id intero, senza un nome",
          (False, False, False, False),
          (banco.CHIAVE_COMPRA in avviso, any(o in avviso for o in O),
           "Chi compra" in avviso, "Chi vende" in avviso))
    con = banco.con_db()
    prova("il timbro e' nel database", "sopra", con.execute(
        "SELECT valore FROM timbri WHERE nome=?",
        (SRV.TIMBRO_SOGLIA_DISPUTE_P2P,)).fetchone()[0])
    con.close()
    prova("l'ora dopo, ancora sopra: silenzio", [], battito())
    prova("dopo un riavvio (la memoria del processo persa): silenzio, il "
          "timbro e' nel database", [], battito(riavvio=True))
    banco.giro_attese()
    prova("...e dentro l'ora un altro battito: in tutto, un avviso solo", 1,
          len(AVVISATI))
    con = banco.con_db()
    con.execute("DELETE FROM timbri WHERE nome=?", (SRV.TIMBRO_SOGLIA_DISPUTE_P2P,))
    con.commit()
    con.close()
    SRV.P2P_DISPUTE_SOGLIA_PERCENTO = 0.0
    prova("a leva spenta (0) tace anche senza timbro", [], battito())
    SRV.P2P_DISPUTE_SOGLIA_PERCENTO = 5.0

    print("\n4-bis) una disputa tolta dal conto a mano")
    # il timbro non c'e' e la soglia e' accesa: se il battito tace, e'
    # la leva delle escluse che lo fa tacere
    SRV.P2P_DISPUTE_ESCLUSE = (O[5][:8],)
    d = cruscotto()["dispute_p2p"]
    p30 = d["periodi"]["30"]
    prova("esclusa per id accorciato: 2 dispute su 6 con garanzia (il suo "
          "scambio resta), una sola aperta", (7, 6, 2, 33.3, [O[4][:8]]),
          (p30["presi"], p30["con_garanzia"], p30["con_disputa"], p30["percento"],
           [a["ordine"] for a in d["aperte"]]))
    prova("...e la sezione dice quale ha tolto", [O[5][:8]], d["escluse"])
    prova("...con due dispute il battito dell'ora tace", [], battito())
    SRV.P2P_DISPUTE_ESCLUSE = (O[5],)
    prova("...lo stesso con l'id scritto intero", 2,
          cruscotto()["dispute_p2p"]["periodi"]["30"]["con_disputa"])
    prova("...e il battito tace ancora", [], battito())
    SRV.P2P_DISPUTE_ESCLUSE = ()
    partiti = battito()
    prova("tolta la leva la disputa torna nel conto, e l'avviso parte: era "
          "lei a farlo tacere", (1, True),
          (len(partiti), "3 scambi su 6 con garanzia" in (partiti or [""])[0]))

    print("\n5) la scopa dei quaranta giorni non cambia «da sempre»")
    prima = cruscotto()["dispute_p2p"]["periodi"]["tutto"]
    dopo_la_memoria = adesso + SRV.P2P_LIBRO_MEMORIA_S + 3600
    con = banco.con_db()
    prova("i conti sono in salvo", True, SRV._conti_salvi_p2p(con, dopo_la_memoria))
    tolte = SRV._pulisci_memoria_p2p(con, dopo_la_memoria)
    prova("la scopa porta via la cronaca", (True, 0),
          (tolte > 0, con.execute("SELECT COUNT(*) FROM p2p_momenti").fetchone()[0]))
    intero = SRV.dati_dispute_p2p(con, adesso)
    dopo = intero["periodi"]["tutto"]
    scritte = {r[0][:8]: r[1] for r in con.execute(
        "SELECT ordine, garanzia FROM p2p_conti WHERE esito IN "
        "('completato','annullato','tornato')")}
    con.close()
    prova("nel registro la garanzia e' SCRITTA: si' per i tre conclusi e "
          "per quello deciso dal moderatore, no per la presa che non l'ha "
          "mai pagata", {O[0][:8]: 1, O[1][:8]: 1, O[2][:8]: 1, O[3][:8]: 1,
                         O[6][:8]: 0}, scritte)
    prova("...e senza cronaca la sezione non deduce piu' niente", 0,
          intero["dedotti"])
    prova("...e i sette scambi presi, i sei con garanzia e le tre dispute "
          "ci sono ancora — anche i due ancora in disputa, che nel registro "
          "non sono entrati; la presa senza garanzia resta fuori dal "
          "denominatore anche letta dal registro",
          (prima, 7, 6, 3),
          (dopo, dopo["presi"], dopo["con_garanzia"], dopo["con_disputa"]))

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
