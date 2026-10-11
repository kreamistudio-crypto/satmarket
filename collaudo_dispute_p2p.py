# -*- coding: utf-8 -*-
"""
LE DISPUTE P2P PER I MODERATORI, SUL SERVER VERO (28 set 2026).

Dal campo: Alan apre una disputa di prova — 13.739 sats in garanzia — e
nessun moderatore riceve niente. mostrod raccontava `dispute-opened`, il
server avvisava l'altra parte, e basta.

`prove.py` difende i giudici estratti (`prove_dispute_p2p_moderatori`).
Qui gira il SERVER VERO, sul database vero e usa-e-getta, con gli eventi
nella forma che la patch 0007 manda davvero e l'INVIO VERO
(`_manda_evento_p2p`: quello che la rotta lancia nel suo task), con
Telegram di cartone che ricorda chi ha ricevuto cosa:

  1. la disputa si apre: l'altra parte riceve l'avviso di sempre, e il
     moderatore il SUO — ordine, chi l'ha aperta, le due persone,
     importo, metodo, da quando la garanzia e' bloccata; nasce la riga
     in `p2p_dispute` e la prima riga del registro;
  2. il retry di mostrod non suona due volte, a nessuno;
  3. le due parti annullano d'accordo a disputa aperta: i moderatori
     leggono «chiusa dalle parti», la riga si chiude;
  4. un moderatore decide (`admin-settle`) e nel registro la decisione
     NON C'E': ALLARME a tutti i moderatori, e la riga nel registro;
  5. un moderatore decide e la decisione a registro c'e': «decisa», col
     nome e col motivo — scappato;
  6. il moderatore che e' una delle parti lo legge nell'avviso;
  7. la parte che non e' dei nostri (un'altra app) si dice cosi';
  8. la garanzia arriva al capolinea a disputa aperta: «chiusa senza una
     decisione»; chi vende libera a disputa aperta: «chiusa dalle parti»;
  9. un annullo su un ordine che non era in disputa non dice niente ai
     moderatori.

E LE ROTTE DELLA SEZIONE «⚖️ Moderazione P2P», una per una, dal server
vero:

 10. chi non e' moderatore prende 403 da tutte e sei, e sulla settima
     (l'id della disputa, che e' di tutti) un si' che non scrive niente;
 11. il moderatore registra la sua chiave PUBBLICA, e l'elenco gliela
     ridice; l'id della disputa lo dichiara una delle parti;
 12. «Prendi la disputa» nei due tempi: prima della firma niente
     avvisi, dopo le due parti e nessun altro; le chiavi delle parti
     viaggiano solo a chi l'ha presa;
 13. la decisione senza motivo, senza conferma, o prima della presa non
     si scrive; quella buona va a registro — e quando mostrod racconta
     la chiusura i moderatori leggono «decisa», col motivo, e NESSUN
     allarme.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_dispute_p2p.py
"""

import asyncio
import sys
import time

import collaudo_pagamento_p2p as banco

D = ["5a1e0000-d15b-4a2b-9c3d-0000000000%02x" % n for n in range(1, 10)]
MOD = 999
CHIAVE_IGNOTA = "e5" * 32


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in D:
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                    "13603,'10,00 €','[\"Contanti\"]')",
                    (ordine, banco.VENDE, adesso - 3600))
    con.execute("UPDATE utenti SET username='chi_vende' WHERE tg_id=?", (banco.VENDE,))
    con.execute("UPDATE utenti SET nome='Chi <b>compra</b>' WHERE tg_id=?", (banco.COMPRA,))
    con.commit()
    con.close()


def manda(ordine, azione, ts, attore="mostro", dettaglio=None, **extra):
    """L'evento di mostrod dalla porta vera e l'INVIO vero: torna la
    lista `(chi, testo)` di quel che Telegram avrebbe ricevuto, o None
    se l'evento era gia' registrato."""
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts,
         "buyer": banco.CHIAVE_COMPRA, "seller": banco.CHIAVE_VENDE,
         "actor": attore, "detail": dettaglio}
    d.update(extra)
    con = banco.con_db()
    try:
        ev = banco.SRV._evento_p2p_pulito(d, int(time.time()))
        fatto = banco.SRV._registra_evento_p2p(con, ev, int(time.time()))
    finally:
        con.close()
    if fatto is None:
        return None
    del banco.DETTO[:]
    asyncio.run(banco.SRV._manda_evento_p2p(ev, fatto))
    return list(banco.DETTO)


def fino_alla_disputa(ordine, t, da="buyer", **extra):
    manda(ordine, "taken", t, "buyer", "take", **extra)
    manda(ordine, "hold-invoice-paid", t + 10, "seller", **extra)
    return manda(ordine, "dispute-opened", t + 20, da, **extra)


def riga(ordine):
    con = banco.con_db()
    try:
        r = con.execute("SELECT * FROM p2p_dispute WHERE ordine=?", (ordine,)).fetchone()
        return dict(r) if r else None
    finally:
        con.close()


def registro(ordine):
    con = banco.con_db()
    try:
        return [(r["gesto"], r["tg_id"], r["esito"], r["motivo"]) for r in con.execute(
            "SELECT * FROM p2p_dispute_registro WHERE ordine=? ORDER BY id", (ordine,))]
    finally:
        con.close()


def _errore_senza_corpo(fn):
    """Il rifiuto di una rotta che non legge un corpo, o None."""
    try:
        asyncio.run(fn())
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def a(chi, detto):
    return [t for c, t in (detto or []) if c == chi]


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    SRV = banco.SRV
    t = int(time.time()) - 600
    V, C = banco.VENDE, banco.COMPRA

    print("\n1) la disputa si apre")
    detto = fino_alla_disputa(D[0], t)
    prova("l'avviso parte a due persone: l'altra parte e il moderatore",
          [V, MOD], sorted(c for c, _ in detto))
    prova("all'altra parte la frase di sempre", True,
          "ha aperto una disputa" in a(V, detto)[0])
    m = a(MOD, detto)[0]
    prova("al moderatore: l'ordine e chi l'ha aperta", True,
          "Disputa P2P aperta</b> sull'ordine <code>" + D[0][:8] + "</code>, da <b>chi compra</b>." in m)
    prova("...le due persone, coi nomi SCAPPATI e lo @username", True,
          "• Compra: Chi &lt;b&gt;compra&lt;/b&gt;" in m and "• Vende: Chi vende (@chi_vende)" in m)
    prova("...importo e metodo", True,
          "• Importo: 13.603 sats per 10,00 €" in m and "• Metodo: Contanti" in m)
    prova("...e da quando la garanzia e' bloccata", True,
          "• Garanzia bloccata dal " + time.strftime("%d/%m/%Y %H:%M", time.localtime(t + 10)) in m)
    prova("...senza l'avviso di chi e' una parte", False, "Sei una delle due parti" in m)
    r = riga(D[0])
    prova("la riga della disputa: aperta, da chi compra, con le due parti",
          ["aperta", "compra", C, V, t + 20, "", 0],
          [r[k] for k in ("stato", "aperta_da", "compratore", "venditore", "aperta_il", "esito", "presa_da")])
    prova("...e il registro comincia", [("aperta", C, "", "")], registro(D[0]))

    print("\n2) il retry di mostrod")
    prova("lo stesso evento non suona due volte", None, manda(D[0], "dispute-opened", t + 20, "buyer"))
    prova("...e il registro non raddoppia", 1, len(registro(D[0])))

    print("\n3) le parti annullano d'accordo")
    detto = manda(D[0], "cancel-requested", t + 30, "seller")
    prova("la richiesta di annullo la sente l'altra parte, non i moderatori", [C],
          sorted(c for c, _ in detto))
    detto = manda(D[0], "canceled", t + 40, "buyer", "cooperative")
    prova("annullato d'accordo: i moderatori leggono che non c'e' piu' niente da decidere", True,
          len(a(MOD, detto)) == 1 and "chiusa dalle parti" in a(MOD, detto)[0]
          and "hanno annullato d'accordo, i sats tornano a chi vende" in a(MOD, detto)[0])
    r = riga(D[0])
    prova("la riga si chiude: i sats a chi vende, chiusa dalle parti",
          ["chiusa", "venditore", "parti", t + 40],
          [r[k] for k in ("stato", "esito", "chiusa_da", "chiusa_il")])
    prova("...e il registro lo dice", ("chiusa", 0, "venditore", "parti"), registro(D[0])[-1])

    print("\n4) una decisione da moderatore che a registro non c'e'")
    fino_alla_disputa(D[1], t + 100)
    detto = manda(D[1], "released", t + 130, "mostro", "admin",
                  sats=13603, sats_buyer=13467, sats_seller=13739)
    prova("ALLARME ai moderatori", True,
          len(a(MOD, detto)) == 1 and "chiusa SENZA una decisione a registro" in a(MOD, detto)[0]
          and "«i sats vanno a chi compra»" in a(MOD, detto)[0]
          and "va tolta dal nodo SUBITO" in a(MOD, detto)[0])
    prova("...e la riga nel registro e' un allarme", ("allarme", 0, "compratore", "moderatore"),
          registro(D[1])[-1])
    prova("...la disputa e' chiusa lo stesso: e' un fatto", ["chiusa", "compratore", "moderatore"],
          [riga(D[1])[k] for k in ("stato", "esito", "chiusa_da")])

    print("\n5) una decisione da moderatore, a registro")
    fino_alla_disputa(D[2], t + 200)
    con = banco.con_db()
    SRV._registro_disputa_p2p(con, D[2], "decisione", MOD, t + 225, "venditore",
                              "Nessun <euro> inviato: lo dicono tutti e due", "c0" * 32)
    con.commit()
    con.close()
    detto = manda(D[2], "canceled", t + 230, "mostro", "admin")
    m = a(MOD, detto)[0]
    prova("«decisa», con dove vanno i sats", True,
          "Disputa P2P decisa</b>" in m and "i sats tornano a chi vende" in m)
    prova("...col motivo SCAPPATO, e nessun allarme", [True, False],
          ["Motivo: «Nessun &lt;euro&gt; inviato: lo dicono tutti e due»" in m, "SENZA" in m])
    prova("...una decisione per l'ALTRO esito non copre questa", True,
          "chiusa SENZA" in SRV._testo_disputa_chiusa_p2p("x", "compratore", "moderatore", None))

    print("\n6) il moderatore che e' una delle parti")
    SRV.ADMIN_IDS = [999, C]
    detto = fino_alla_disputa(D[3], t + 300, "seller")
    prova("chi compra e' anche moderatore: riceve l'avviso della parte e quello del moderatore",
          [2, 1], [len(a(C, detto)), len(a(MOD, detto))])
    prova("...e nel suo c'e' scritto che non la decide lui; in quello dell'altro no", [True, False],
          [any("Sei una delle due parti" in x for x in a(C, detto)),
           "Sei una delle due parti" in a(MOD, detto)[0]])
    prova("...aperta da chi vende", "vende", riga(D[3])["aperta_da"])
    SRV.ADMIN_IDS = [999]

    print("\n7) una parte che non e' dei nostri")
    detto = fino_alla_disputa(D[4], t + 400, "buyer", seller=CHIAVE_IGNOTA)
    prova("chi vende scambia da un'altra app: si dice, e la riga porta 0", [True, 0],
          ["• Vende: non è un utente di Barattolo (scambia da un'altra app)" in a(MOD, detto)[0],
           riga(D[4])["venditore"]])

    print("\n8) la scadenza, e il rilascio di chi vende")
    fino_alla_disputa(D[5], t + 500)
    detto = manda(D[5], "expired", t + 530, "mostro", "escrow-deadline")
    prova("la garanzia al capolinea: «chiusa senza una decisione», i sats a chi vende", True,
          "chiusa senza una decisione" in a(MOD, detto)[0]
          and ["venditore", "scadenza"] == [riga(D[5])[k] for k in ("esito", "chiusa_da")])
    fino_alla_disputa(D[6], t + 540)
    detto = manda(D[6], "released", t + 570, "seller", None,
                  sats=13603, sats_buyer=13467, sats_seller=13739)
    prova("chi vende libera a disputa aperta: «chiusa dalle parti», i sats a chi compra", True,
          "chi vende ha liberato i sats, i sats vanno a chi compra" in a(MOD, detto)[0]
          and ["compratore", "parti"] == [riga(D[6])[k] for k in ("esito", "chiusa_da")])
    detto = manda(D[6], "success", t + 580, "mostro", None,
                  sats=13603, sats_buyer=13467, sats_seller=13739)
    prova("...e il pagamento riuscito, dopo, ai moderatori non ridice niente", [], a(MOD, detto))

    print("\n9) senza disputa, niente")
    manda(D[7], "taken", t + 590, "buyer", "take")
    detto = manda(D[7], "canceled", t + 595, "seller")
    prova("un annullo su un ordine mai in disputa non arriva ai moderatori", [[], None],
          [a(MOD, detto), riga(D[7])])

    print("\n10) le rotte della moderazione: chi non e' moderatore")
    R = D[8]
    fino_alla_disputa(R, t + 700)
    DISP = "d15b0000-aaaa-4bbb-8ccc-0000000000d1"
    KM = "c0" * 32
    rotte = [(SRV.moderazione_chiave_p2p, {"chiave": KM}),
             (SRV.moderazione_prendi_p2p, {"ordine": R, "chiave": KM}),
             (SRV.moderazione_lascia_p2p, {"ordine": R, "motivo": "x"}),
             (SRV.moderazione_decisione_p2p, {"ordine": R, "esito": "venditore", "conferma": True,
                                              "motivo": "un motivo lungo abbastanza", "chiave": KM}),
             (SRV.moderazione_esito_p2p, {"ordine": R, "esito": "venditore", "motivo": "x"})]
    banco.come(banco.ESTRANEO)
    prova("un utente qualunque: 403 da tutte le rotte dei moderatori, elenco compreso",
          [403] * 6,
          [(banco.errore(f, c) or (200,))[0] for f, c in rotte]
          + [(lambda: (lambda e: e[0] if e else 200)(_errore_senza_corpo(SRV.moderazione_p2p)))()])
    prova("...e sull'id della disputa, che e' di tutti, un si' che non scrive niente",
          [True, ""], [banco.esito(SRV.disputa_dichiarata_p2p, {"ordine": R, "disputa": DISP}).get("ok"),
                       riga(R)["disputa"]])
    prova("...e il registro non ha visto niente di lui", [("aperta", C, "", "")], registro(R))

    print("\n11) la chiave del moderatore, e l'id della disputa")
    banco.come(MOD)
    prova("la chiave si registra, ed e' quella pubblica",
          [True, True], (lambda r: [r.get("ok"), r.get("nuova")])(
              banco.esito(SRV.moderazione_chiave_p2p, {"chiave": KM})))
    prova("...ridirla non cambia niente", False,
          banco.esito(SRV.moderazione_chiave_p2p, {"chiave": KM}).get("nuova"))
    prova("...una chiave storta e' un 400", 400, banco.errore(SRV.moderazione_chiave_p2p, {"chiave": "nsec1abc"})[0])
    banco.come(C)
    banco.esito(SRV.disputa_dichiarata_p2p, {"ordine": R, "disputa": DISP})
    prova("una delle parti dichiara l'id della disputa", DISP, riga(R)["disputa"])
    banco.come(MOD)
    e = asyncio.run(SRV.moderazione_p2p())
    e = __import__("json").loads(e.body)
    d = [x for x in e["dispute"] if x["ordine"] == R][0]
    prova("l'elenco: la disputa, l'id, i nomi NUDI, la chiave del moderatore",
          ["aperta", DISP, "Chi <b>compra</b>", "Chi vende (@chi_vende)", KM, False, "", ""],
          [d["stato"], d["disputa"], d["compra"], d["vende"], e["chiave"], d["sei_parte"],
           d["chiave_compratore"], d["chiave_venditore"]])

    print("\n12) prendi la disputa, nei due tempi")
    del banco.DETTO[:]
    prova("prima della firma: si puo', e non parte nessun avviso",
          [True, [], "aperta"],
          [banco.esito(SRV.moderazione_prendi_p2p, {"ordine": R, "chiave": KM}).get("ok"),
           list(banco.DETTO), riga(R)["stato"]])
    prova("la decisione prima della presa non si scrive", 409,
          banco.errore(SRV.moderazione_decisione_p2p, rotte[3][1])[0])
    # (11 ott 2026, ea0af71a) la presa fallita DOPO la risposta del
    # coordinatore: il server la dice ancora aperta, ma sa che la MIA presa
    # e' fallita — e lo dice solo a me
    e = __import__("json").loads(asyncio.run(SRV.moderazione_p2p()).body)
    prova("prima di un fallimento l'elenco non propone la ripresa", False,
          [x for x in e["dispute"] if x["ordine"] == R][0]["presa_fallita_da_me"])
    banco.esito(SRV.moderazione_lascia_p2p, {"ordine": R, "motivo": "la disputa presa NON e' di questo ordine"})
    e = __import__("json").loads(asyncio.run(SRV.moderazione_p2p()).body)
    prova("dopo `lascia` l'elenco dice: la tua presa e' fallita, la disputa e' ancora aperta",
          [True, "aperta"], (lambda d: [d["presa_fallita_da_me"], d["stato"]])(
              [x for x in e["dispute"] if x["ordine"] == R][0]))
    banco.come(banco.ESTRANEO)
    SRV.ADMIN_IDS = [999, banco.ESTRANEO]
    e = __import__("json").loads(asyncio.run(SRV.moderazione_p2p()).body)
    prova("...e a un altro moderatore no: la presa fallita e' di chi l'ha tentata", False,
          [x for x in e["dispute"] if x["ordine"] == R][0]["presa_fallita_da_me"])
    SRV.ADMIN_IDS = [999]
    banco.come(MOD)
    # il solo secondo tempo, senza ripassare dal primo: e' il gesto della ripresa
    banco.esito(SRV.moderazione_prendi_p2p, {"ordine": R, "chiave": KM, "fatto": True})
    e = __import__("json").loads(asyncio.run(SRV.moderazione_p2p()).body)
    prova("...e il solo secondo tempo la registra presa, e la ripresa non si propone piu'",
          ["presa", False], (lambda d: [d["stato"], d["presa_fallita_da_me"]])(
              [x for x in e["dispute"] if x["ordine"] == R][0]))
    prova("dopo la firma: presa, e lo sanno le due parti (e nessun altro: il moderatore e' uno)",
          ["presa", MOD, [C, V]],
          [riga(R)["stato"], riga(R)["presa_da"], sorted(c for c, _ in banco.DETTO)[::-1]])
    prova("...con la frase che dice di scrivergli", True,
          all("Un moderatore ha preso la disputa" in x and "scrivergli" in x for _, x in banco.DETTO))
    e = __import__("json").loads(asyncio.run(SRV.moderazione_p2p()).body)
    d = [x for x in e["dispute"] if x["ordine"] == R][0]
    prova("...e adesso le chiavi delle parti viaggiano a chi l'ha presa",
          [banco.CHIAVE_COMPRA, banco.CHIAVE_VENDE, True],
          [d["chiave_compratore"], d["chiave_venditore"], d["presa_da_me"]])
    # il moderatore che e' una delle parti
    SRV.ADMIN_IDS = [999, C]
    banco.come(C)
    banco.esito(SRV.moderazione_chiave_p2p, {"chiave": "d1" * 32})
    fino_alla_disputa(D[7], t + 800)
    prova("il moderatore che e' una delle parti non prende: 403", 403,
          banco.errore(SRV.moderazione_prendi_p2p, {"ordine": D[7], "chiave": "d1" * 32})[0])
    SRV.ADMIN_IDS = [999]
    banco.come(MOD)

    print("\n13) la decisione, e il cerchio che si chiude")
    buona = dict(rotte[3][1])
    for nome, corpo, atteso in (("senza motivo", dict(buona, motivo=""), 400),
                                ("col motivo corto", dict(buona, motivo="corto"), 400),
                                ("senza la conferma", dict(buona, conferma=False), 400),
                                ("con un'altra chiave", dict(buona, chiave="d1" * 32), 409)):
        prova(f"la decisione {nome} non si scrive", atteso,
              banco.errore(SRV.moderazione_decisione_p2p, corpo)[0])
    prova("...e a registro non c'e' nessuna decisione", [],
          [x for x in registro(R) if x[0] == "decisione"])
    prova("quella buona si'", [True, ("decisione", MOD, "venditore", "un motivo lungo abbastanza")],
          [banco.esito(SRV.moderazione_decisione_p2p, buona).get("ok"), registro(R)[-1]])
    detto = manda(R, "canceled", t + 760, "mostro", "admin")
    prova("mostrod racconta la chiusura: «decisa», col motivo, e NESSUN allarme",
          [True, True, False],
          ["Disputa P2P decisa</b>" in a(MOD, detto)[0],
           "Motivo: «un motivo lungo abbastanza»" in a(MOD, detto)[0], "SENZA" in a(MOD, detto)[0]])
    prova("...e il registro finisce con la chiusura", "chiusa", registro(R)[-1][0])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
