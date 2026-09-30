# -*- coding: utf-8 -*-
"""
IL CONTANTI DI PERSONA: LA PROVA D'INCONTRO SUL SERVER VERO (30 set 2026).

`prove.py` difende i giudici estratti (`prove_contanti_a_mano`): qui gira
il SERVER VERO — la rotta `/api/p2p/presenza`, la rotta degli scambi, le
rotte della moderazione — sul database usa-e-getta, con gli eventi nella
forma della patch 0007 e l'invio vero, e con FIRME VERE: le due note le
firma questo script con `schnorr_puro`, e il server le verifica col suo
giudice (`verifica_firma_nostr`) — con coincurve dove c'e', e in CI, dove
non c'e', con lo stesso `schnorr_puro.ChiaveXOnly` montato al posto di
`ChiavePubblicaNostr`. Il patto del server non cambia: senza coincurve
non crede a niente, e qui lo si guarda PRIMA di montare il calco.

  1. a P2P spento la rotta dice 409, e non scrive;
  2. uno scambio in contanti preso e con la garanzia bloccata: chi
     compra carica le due note (la sua e quella letta dal QR di chi
     vende) e riceve «incontro confermato», con l'ora e la distanza;
  3. l'altro telefono — e il dispositivo che non ha caricato niente —
     la ritrova dalla rotta degli scambi (`incontro`), nei due versi;
  4. una seconda prova torna la prima (`gia`); un corpo storto e' 400,
     due chiavi che non sono dello scambio 403, uno sconosciuto con le
     note buone passa (a provare sono le firme, non chi le porta);
  5. la disputa si apre: il moderatore legge la prova nella sua card
     (`incontro`), e un ordine in contanti SENZA prova dice None;
  6. mostrod racconta la chiusura: le posizioni se ne vanno dalla riga,
     l'ora e la distanza restano, e la card lo dice (`posizioni_via`);
  7. la scopa dell'orologio gira senza rompere niente;
  8. una prova su uno scambio gia' chiuso non entra (409).

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_contanti_p2p.py
"""

import asyncio
import hashlib
import json
import os
import sys
import time

import collaudo_pagamento_p2p as banco
import schnorr_puro

ORD = ["c0a7a271-d15b-4a2b-9c3d-0000000000%02x" % n for n in range(1, 6)]
MOD = 999
SK_VENDE = hashlib.sha256(b"collaudo contanti: chi vende").digest()
SK_COMPRA = hashlib.sha256(b"collaudo contanti: chi compra").digest()
SK_ALTRO = hashlib.sha256(b"collaudo contanti: un altro").digest()
PUB_VENDE = schnorr_puro.pubblica(SK_VENDE).hex()
PUB_COMPRA = schnorr_puro.pubblica(SK_COMPRA).hex()
PUB_ALTRO = schnorr_puro.pubblica(SK_ALTRO).hex()
GEO_V = {"lat": 45.46420, "lon": 9.19000, "acc": 12}
GEO_C = {"lat": 45.46430, "lon": 9.19010, "acc": 8}


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in ORD:
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                    "13603,'10,00 €','[\"Contanti\"]')",
                    (ordine, banco.VENDE, adesso - 3600))
    for chiave, tg in ((PUB_VENDE, banco.VENDE), (PUB_COMPRA, banco.COMPRA)):
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                    "VALUES(?,?,?)", (chiave, tg, adesso))
    con.commit()
    con.close()


def manda(ordine, azione, ts, attore="mostro", dettaglio=None, **extra):
    """L'evento di mostrod dalla porta vera e l'INVIO vero (il task che la
    rotta lancia), con le DUE chiavi di questo collaudo."""
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts,
         "buyer": PUB_COMPRA, "seller": PUB_VENDE, "actor": attore, "detail": dettaglio}
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


def nota(sk, ordine, ruolo, ora, geo=None, ref=None, nonce="0011223344556677"):
    """Una nota firmata come la fa il client (`notaMostraP2P`/`notaLeggeP2P`
    + finalizeEvent): kind, tag d e ruolo, il tag e per chi legge."""
    SRV = banco.SRV
    tags = [["d", ordine], ["ruolo", ruolo]] + ([["e", ref]] if ref else [])
    contenuto = json.dumps({"v": 1, "nonce": nonce if ruolo == "mostra" else "", "geo": geo},
                           separators=(",", ":"))
    ev = SRV.evento_non_firmato(schnorr_puro.pubblica(sk).hex(), SRV.P2P_KIND_PRESENZA,
                                tags, contenuto, ora)
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"]), os.urandom(32)).hex()
    return ev


def coppia(ordine, ora, geo_v=GEO_V, geo_c=GEO_C, sk_legge=SK_COMPRA):
    """Chi vende mostra, chi compra legge e controfirma: il corpo del POST."""
    m = nota(SK_VENDE, ordine, "mostra", ora, geo_v)
    l = nota(sk_legge, ordine, "legge", ora + 20, geo_c, ref=m["id"])
    return {"ordine": ordine, "mostrata": m, "letta": l}


def presenza_db(ordine):
    con = banco.con_db()
    try:
        r = con.execute("SELECT * FROM p2p_presenze WHERE ordine=?", (ordine,)).fetchone()
        return dict(r) if r else None
    finally:
        con.close()


def scambi(chi):
    banco.come(chi)
    d = json.loads(asyncio.run(banco.SRV.scambi_p2p()).body)
    return d.get("scambi") or {}


def moderazione():
    banco.come(MOD)
    return json.loads(asyncio.run(banco.SRV.moderazione_p2p()).body)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    SRV = banco.SRV
    t = int(time.time()) - 600
    V, C, E = banco.VENDE, banco.COMPRA, banco.ESTRANEO

    print("\n0) le firme: il patto del server, e il calco per dove coincurve non c'e'")
    ev = nota(SK_VENDE, ORD[0], "mostra", t)
    if SRV.ChiavePubblicaNostr is None:
        prova("senza coincurve il server non crede a niente (fail-closed)", False, SRV.verifica_firma_nostr(ev))
        SRV.ChiavePubblicaNostr = schnorr_puro.ChiaveXOnly
        print("   (coincurve assente: monto schnorr_puro.ChiaveXOnly, come in CI)")
    else:
        print("   (coincurve presente: il server verifica con libsecp256k1)")
    prova("una nota firmata con schnorr_puro passa il giudice del server; ritoccata no", [True, False],
          [SRV.verifica_firma_nostr(ev), SRV.verifica_firma_nostr(dict(ev, content=ev["content"] + " "))])

    print("\n1) a P2P spento la rotta dice di no")
    banco.come(C)
    prova("409 «non e' attivo», e nessuna riga", [(409, "Lo scambio P2P non e' attivo"), None],
          [banco.errore(SRV.presenza_p2p, coppia(ORD[0], int(time.time()))), presenza_db(ORD[0])])
    SRV.P2P_ATTIVO, SRV.MOSTRO_HEX, SRV.MOSTRO_RELAY = True, "a" * 64, ["ws://127.0.0.1:9"]
    prova("...acceso: la busta delle leve porta il tetto del contanti di serie, 250", 250,
          SRV._p2p_per(C)["maxEuroContanti"])

    print("\n2) lo scambio in contanti: preso, garanzia bloccata, «Siamo insieme»")
    manda(ORD[0], "taken", t, "buyer", "take")
    manda(ORD[0], "hold-invoice-paid", t + 10, "seller")
    banco.come(C)
    adesso = int(time.time())
    r = banco.esito(SRV.presenza_p2p, coppia(ORD[0], adesso - 30))
    prova("chi compra carica le due note: 200, incontro confermato, l'ora della nota letta, due posizioni, la distanza",
          [True, False, adesso - 10, 2, True, 12],
          [r.get("ok"), r.get("gia"), r["incontro"]["ora"], r["incontro"]["posizioni"],
           5 <= (r["incontro"]["distanza"] or 0) <= 30, r["incontro"]["precisione"]])
    riga = presenza_db(ORD[0])
    prova("la riga: le chiavi di chi ha mostrato e di chi ha letto, chi ha caricato, il giro, le posizioni",
          [PUB_VENDE, PUB_COMPRA, C, 1, 45.4642, 9.1901, 0],
          [riga["chiave_mostra"], riga["chiave_legge"], riga["caricata_da"], riga["giro"],
           riga["lat_mostra"], riga["lon_legge"], riga["posizioni_via"]])

    print("\n3) la prova si ritrova dalla rotta degli scambi, nei due versi")
    sc = scambi(V)
    prova("chi vende — che non ha caricato niente — la legge: ora e distanza", [True, adesso - 10, True],
          [ORD[0] in sc, sc[ORD[0]]["incontro"]["ora"] if ORD[0] in sc else None,
           bool(sc.get(ORD[0], {}).get("incontro", {}).get("distanza"))])
    sc = scambi(C)
    prova("...e chi compra pure", adesso - 10, sc[ORD[0]]["incontro"]["ora"] if ORD[0] in sc else None)

    print("\n4) i doppioni, gli storti, gli sconosciuti")
    r2 = banco.esito(SRV.presenza_p2p, coppia(ORD[0], adesso - 5))
    prova("una seconda prova sullo stesso ordine torna la PRIMA", [True, adesso - 10], [r2.get("gia"), r2["incontro"]["ora"]])
    prova("un corpo storto e' 400, con la sua frase", (400, "Nota illeggibile"),
          banco.errore(SRV.presenza_p2p, {"ordine": ORD[1], "mostrata": "x", "letta": "y"}))
    manda(ORD[1], "taken", t + 100, "buyer", "take")
    manda(ORD[1], "hold-invoice-paid", t + 110, "seller")
    prova("due firme vere ma NON delle chiavi dello scambio: 403", (403, "Le firme non sono delle due chiavi di questo scambio"),
          banco.errore(SRV.presenza_p2p, coppia(ORD[1], adesso - 30, sk_legge=SK_ALTRO)))
    prova("...e non hanno scritto niente", None, presenza_db(ORD[1]))
    banco.come(E)
    r3 = banco.esito(SRV.presenza_p2p, coppia(ORD[1], adesso - 30))
    prova("uno sconosciuto con le note buone passa: a provare sono le firme, non chi le porta", [True, E],
          [r3.get("ok"), presenza_db(ORD[1])["caricata_da"]])
    prova("...e uno scambio che il coordinatore non ha ancora raccontato aspetta: 409", 409,
          banco.errore(SRV.presenza_p2p, coppia(ORD[2], adesso - 30))[0])

    print("\n5) la disputa: il moderatore legge la prova")
    detto = manda(ORD[0], "dispute-opened", t + 20, "buyer")
    prova("l'avviso ai moderatori parte", True, any(c == MOD for c, _ in detto))
    manda(ORD[3], "taken", t + 200, "buyer", "take")
    manda(ORD[3], "hold-invoice-paid", t + 210, "seller")
    manda(ORD[3], "dispute-opened", t + 220, "seller")
    m = moderazione()
    per = {d["ordine"]: d for d in m["dispute"]}
    prova("la card della disputa con la prova: ora, distanza, posizioni", [True, adesso - 10, True, 2, False],
          [ORD[0] in per, per[ORD[0]]["incontro"]["ora"], bool(per[ORD[0]]["incontro"]["distanza"]),
           per[ORD[0]]["incontro"]["posizioni"], per[ORD[0]]["incontro"]["posizioni_via"]])
    prova("...e quella in contanti SENZA prova dice None", [True, None],
          [ORD[3] in per, per[ORD[3]]["incontro"]])

    print("\n6) la chiusura scorda le posizioni")
    manda(ORD[0], "released", t + 300, "mostro", "admin", sats=13603, sats_buyer=13467, sats_seller=13739)
    riga = presenza_db(ORD[0])
    prova("dalla riga se ne vanno le posizioni e la copia delle note; restano ora, distanza e chiavi",
          [None, None, None, None, "", True, True, adesso - 10, PUB_VENDE],
          [riga["lat_mostra"], riga["lon_mostra"], riga["acc_legge"], riga["lon_legge"], riga["prova"],
           riga["posizioni_via"] > 0, riga["distanza_m"] is not None, riga["ora_legge"], riga["chiave_mostra"]])
    m = moderazione()
    per = {d["ordine"]: d for d in m["dispute"]}
    prova("...e la card chiusa lo dice: `posizioni_via`, la distanza ancora li', la precisione no",
          [True, True, None], [per[ORD[0]]["incontro"]["posizioni_via"], bool(per[ORD[0]]["incontro"]["distanza"]),
                               per[ORD[0]]["incontro"]["precisione"]])
    manda(ORD[1], "canceled", t + 400, "buyer", "cooperative")
    prova("anche un annullo d'accordo scorda le posizioni", True, presenza_db(ORD[1])["posizioni_via"] > 0)

    print("\n7) la scopa dell'orologio")
    try:
        SRV.pulisci_presenze_p2p()
        prova("gira senza rompere niente", True, True)
    except Exception as e:
        prova("gira senza rompere niente", "", f"{type(e).__name__}: {e}")
    prova("...e non tocca una riga fresca", 2, len([o for o in ORD if presenza_db(o)]))

    print("\n8) su uno scambio chiuso una prova non entra")
    banco.come(C)
    prova("409 «chiuso»", 409, banco.errore(SRV.presenza_p2p, coppia(ORD[0], adesso))[0])
    manda(ORD[4], "taken", t + 500, "buyer", "take")
    manda(ORD[4], "hold-invoice-paid", t + 510, "seller")
    manda(ORD[4], "released", t + 520, "seller", sats=13603, sats_buyer=13467, sats_seller=13739)
    manda(ORD[4], "success", t + 530, "mostro", sats=13603, sats_buyer=13467, sats_seller=13739)
    prova("...anche concluso senza disputa", 409, banco.errore(SRV.presenza_p2p, coppia(ORD[4], adesso))[0])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
