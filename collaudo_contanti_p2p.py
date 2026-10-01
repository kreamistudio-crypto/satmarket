# -*- coding: utf-8 -*-
"""
IL CONTANTI DI PERSONA SUL SERVER VERO: «📍 SONO QUI» E L'APPUNTAMENTO
(30 set 2026 col QR; rifatto il 1 ott 2026 — il QR si inquadrava anche da
una foto, e se n'e' andato).

`prove.py` difende i giudici estratti (`prove_contanti_a_mano`,
`prove_luoghi_appuntamento`): qui gira il SERVER VERO — le rotte
`/api/p2p/sono-qui`, `/api/p2p/appuntamento`, `/api/p2p/luoghi` e
`/api/p2p/luoghi/vicino`, la rotta degli scambi, la card del moderatore,
«dimentica il profilo» — sul database usa-e-getta, con gli eventi nella
forma della patch 0007 e l'invio vero, e con FIRME VERE: le note le firma
questo script con `schnorr_puro`, e il server le verifica col suo giudice
(`verifica_firma_nostr`) — con coincurve dove c'e', e in CI, dove non c'e',
con lo stesso `schnorr_puro.ChiaveXOnly` montato al posto di
`ChiavePubblicaNostr`. Il patto del server non cambia: senza coincurve non
crede a niente, e qui lo si guarda PRIMA di montare il calco.

  1. a P2P spento le quattro rotte dicono 409, e non scrivono;
  2. lo scambio in contanti preso e in garanzia: chi vende fissa
     l'appuntamento, chi compra segna «Sono qui» con la posizione, chi vende
     senza e poi con: l'ora del server, le righe che ognuno vede;
  3. la rotta degli scambi porta le due righe, MAI una coordinata;
  4. gli storti: corpo, chiave estranea, coordinatore muto, appuntamento di
     chi compra;
  5. l'avviso a chi compra: «dove e quando vedervi», poi «ha cambiato
     l'appuntamento»;
  6. la disputa: la card del moderatore col confronto (incontro probabile,
     all'ora, a quanto dal luogo); uno scambio in contanti senza niente;
     la prova col QR di ieri ancora leggibile, sul suo giro;
  7. la chiusura scorda posizioni e punto, le distanze restano;
  8. la scopa gira; su uno scambio chiuso una presenza non entra;
  9. IL GIRO: l'ordine torna nel libro e lo riprende un altro — le presenze
     di prima non si vedono, e la chiave di ieri non vale piu';
 10. «dimentica il profilo»: sullo scambio aperto resta l'ora, sul chiuso
     non resta niente;
 11. i suggerimenti degli indirizzi contro un PHOTON DI CARTONE sul
     loopback: cosa gli arriva (solo il testo), la memoria, il freno, i
     silenzi (giu', redirect, risposta enorme), e niente testo nei registri;
     il comune vicino dal nostro elenco.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore, niente Photon vero.

USO:  python collaudo_contanti_p2p.py
"""

import asyncio
import contextlib
import hashlib
import http.server
import io
import json
import os
import sys
import threading
import time
from urllib.parse import parse_qs, urlparse

import collaudo_pagamento_p2p as banco
import schnorr_puro

ORD = ["c0a7a271-d15b-4a2b-9c3d-0000000000%02x" % n for n in range(1, 8)]
MOD = 999
SK_VENDE = hashlib.sha256(b"collaudo contanti: chi vende").digest()
SK_COMPRA = hashlib.sha256(b"collaudo contanti: chi compra").digest()
SK_ALTRO = hashlib.sha256(b"collaudo contanti: un altro").digest()
SK_NUOVO = hashlib.sha256(b"collaudo contanti: chi compra al secondo giro").digest()
PUB_VENDE = schnorr_puro.pubblica(SK_VENDE).hex()
PUB_COMPRA = schnorr_puro.pubblica(SK_COMPRA).hex()
PUB_ALTRO = schnorr_puro.pubblica(SK_ALTRO).hex()
PUB_NUOVO = schnorr_puro.pubblica(SK_NUOVO).hex()
GEO_C = {"lat": 45.46430, "lon": 9.19010, "acc": 8}
GEO_V = {"lat": 45.46420, "lon": 9.19000, "acc": 12}
PUNTO = {"lat": 45.46425, "lon": 9.19005}


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in ORD:
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                    "13603,'10,00 €','[\"Contanti\"]')",
                    (ordine, banco.VENDE, adesso - 3600))
    for chiave, tg in ((PUB_VENDE, banco.VENDE), (PUB_COMPRA, banco.COMPRA),
                       (PUB_NUOVO, banco.ESTRANEO)):
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                    "VALUES(?,?,?)", (chiave, tg, adesso))
    con.commit()
    con.close()


def manda(ordine, azione, ts, attore="mostro", dettaglio=None, compra=PUB_COMPRA, **extra):
    """L'evento di mostrod dalla porta vera e l'INVIO vero (il task che la
    rotta lancia), con le due chiavi dello scambio."""
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts,
         "buyer": compra, "seller": PUB_VENDE, "actor": attore, "detail": dettaglio}
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


def nota(sk, ordine, ruolo, ora, geo=None, quando=None, contenuto=None):
    """Una nota firmata come la fa il client (`notaSonoQuiP2P` /
    `notaAppuntamentoP2P` + finalizeEvent)."""
    SRV = banco.SRV
    if contenuto is None:
        contenuto = json.dumps({"v": 1, "ora": quando, "geo": geo} if ruolo == "appuntamento"
                               else {"v": 1, "nonce": "0011223344556677", "geo": geo},
                               separators=(",", ":"))
    ev = SRV.evento_non_firmato(schnorr_puro.pubblica(sk).hex(), SRV.P2P_KIND_PRESENZA,
                                [["d", ordine], ["ruolo", ruolo]], contenuto, ora)
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"]), os.urandom(32)).hex()
    return ev


def presenze_db(ordine):
    con = banco.con_db()
    try:
        return [dict(r) for r in con.execute("SELECT * FROM p2p_sono_qui WHERE ordine=? ORDER BY id",
                                             (ordine,))]
    finally:
        con.close()


def appuntamenti_db(ordine):
    con = banco.con_db()
    try:
        return [dict(r) for r in con.execute("SELECT * FROM p2p_appuntamenti WHERE ordine=? ORDER BY id",
                                             (ordine,))]
    finally:
        con.close()


def scambi(chi):
    banco.come(chi)
    d = json.loads(asyncio.run(banco.SRV.scambi_p2p()).body)
    return d.get("scambi") or {}


def moderazione():
    banco.come(MOD)
    return json.loads(asyncio.run(banco.SRV.moderazione_p2p()).body)


class Photon:
    """IL PHOTON DI CARTONE sul loopback: risponde come quello vero (le
    proprieta' lette il 1 ott 2026) e REGISTRA cosa gli arriva — l'indirizzo
    con la sua query e le intestazioni — perche' il punto e' sapere che
    fuori esce SOLO il testo cercato."""

    def __init__(self):
        self.chieste = []
        self.modo = "buono"
        cartone = self

        class Mano(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                cartone.chieste.append({"path": self.path, "headers": dict(self.headers)})
                if cartone.modo == "redirect":
                    self.send_response(302)
                    self.send_header("Location", "http://127.0.0.1:1/")
                    self.end_headers()
                    return
                if cartone.modo == "enorme":
                    corpo = b'{"features":[' + b",".join([b'{"x":1}'] * 60000) + b"]}"
                else:
                    q = parse_qs(urlparse(self.path).query).get("q", [""])[0]
                    corpo = json.dumps({"type": "FeatureCollection", "features": [
                        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.6859068, 45.070952]},
                         "properties": {"name": "Piazza Castello", "city": "Torino", "postcode": "10123",
                                        "countrycode": "IT", "osm_key": "place"}},
                        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.68, 45.07]},
                         "properties": {"name": "Bar " + q[:20], "street": "Via Roma", "housenumber": "1",
                                        "city": "Torino", "postcode": "10121"}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mano)
        self.url = "http://127.0.0.1:%d" % self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    SRV = banco.SRV
    t = int(time.time()) - 600
    V, C, E = banco.VENDE, banco.COMPRA, banco.ESTRANEO

    print("\n0) le firme: il patto del server, e il calco per dove coincurve non c'e'")
    ev = nota(SK_VENDE, ORD[0], "qui", t)
    if SRV.ChiavePubblicaNostr is None:
        prova("senza coincurve il server non crede a niente (fail-closed)", False, SRV.verifica_firma_nostr(ev))
        SRV.ChiavePubblicaNostr = schnorr_puro.ChiaveXOnly
        print("   (coincurve assente: monto schnorr_puro.ChiaveXOnly, come in CI)")
    else:
        print("   (coincurve presente: il server verifica con libsecp256k1)")
    prova("una nota firmata con schnorr_puro passa il giudice del server; ritoccata no", [True, False],
          [SRV.verifica_firma_nostr(ev), SRV.verifica_firma_nostr(dict(ev, content=ev["content"] + " "))])

    print("\n1) a P2P spento le quattro rotte dicono di no")
    banco.come(C)
    adesso = int(time.time())
    no = (409, "Lo scambio P2P non e' attivo")
    prova("409 «non e' attivo» su presenza, appuntamento, suggerimenti e comune vicino; e nessuna riga",
          [no, no, no, no, [], []],
          [banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[0], "nota": nota(SK_COMPRA, ORD[0], "qui", adesso)}),
           banco.errore(SRV.appuntamento_p2p, {"ordine": ORD[0], "nota": nota(SK_VENDE, ORD[0], "appuntamento", adesso, quando=adesso + 3600)}),
           banco.errore(SRV.luoghi_p2p, {"q": "piazza castello"}),
           banco.errore(SRV.luogo_vicino_p2p, {"lat": 45.07, "lon": 7.68}),
           presenze_db(ORD[0]), appuntamenti_db(ORD[0])])
    SRV.P2P_ATTIVO, SRV.MOSTRO_HEX, SRV.MOSTRO_RELAY = True, "a" * 64, ["ws://127.0.0.1:9"]
    prova("...acceso: la busta delle leve porta il tetto del contanti di serie, 250", 250,
          SRV._p2p_per(C)["maxEuroContanti"])

    print("\n2) lo scambio in contanti: l'appuntamento, «Sono qui» dai due lati")
    manda(ORD[0], "taken", t, "buyer", "take")
    manda(ORD[0], "hold-invoice-paid", t + 10, "seller")
    adesso = int(time.time())
    banco.come(V)
    ra = banco.esito(SRV.appuntamento_p2p, {"ordine": ORD[0], "nota": nota(
        SK_VENDE, ORD[0], "appuntamento", adesso, quando=adesso + 600, geo=PUNTO)})
    a = appuntamenti_db(ORD[0])
    prova("chi vende fissa l'appuntamento: 200, una versione con l'ora e il punto, e nessun testo d'indirizzo",
          [True, False, 1, adesso + 600, 45.46425, 1],
          [isinstance(ra, dict) and ra.get("ok"), isinstance(ra, dict) and ra.get("gia"), len(a),
           a[0]["ora_incontro"] if a else None, a[0]["lat"] if a else None, a[0]["punto"] if a else None])
    banco.come(C)
    rc = banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[0], "nota": nota(SK_COMPRA, ORD[0], "qui", adesso - 5, geo=GEO_C)})
    prova("chi compra segna «Sono qui» con la posizione: 200, l'ora del SERVER, la sua riga",
          [True, True, True, {"mia": {"ora": rc.get("ora") if isinstance(rc, dict) else None, "posizione": True, "volte": 1},
                              "altra": None}],
          [isinstance(rc, dict) and rc.get("ok"), isinstance(rc, dict) and abs(rc.get("ora", 0) - int(time.time())) <= 5,
           isinstance(rc, dict) and rc.get("posizione"), rc.get("presenze") if isinstance(rc, dict) else rc])
    banco.come(V)
    rv = banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[0], "nota": nota(SK_VENDE, ORD[0], "qui", adesso + 30)})
    prova("chi vende senza posizione: 200, «posizione» falso, e vede l'ORA di chi compra",
          [True, False, True],
          [isinstance(rv, dict) and rv.get("ok"), isinstance(rv, dict) and rv.get("posizione"),
           isinstance(rv, dict) and (rv.get("presenze") or {}).get("altra") == {"ora": rc.get("ora")}])
    rv2 = banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[0], "nota": nota(SK_VENDE, ORD[0], "qui", adesso + 40, geo=GEO_V)})
    righe = presenze_db(ORD[0])
    prova("...ripremuto con la posizione: una riga nuova, le distanze dal luogo e da chi compra calcolate all'arrivo",
          [True, 3, ["compra", "vende", "vende"], True, True],
          [isinstance(rv2, dict) and rv2.get("ok"), len(righe), [r["lato"] for r in righe],
           0 <= (righe[2]["dist_luogo"] or -1) <= 15,
           5 <= json.loads(righe[2]["vicine"] or "{}").get(str(righe[0]["id"]), -1) <= 30])

    print("\n3) la rotta degli scambi: le due righe, mai una coordinata")
    sc_c, sc_v = scambi(C), scambi(V)
    pc, pv = (sc_c.get(ORD[0]) or {}).get("presenze"), (sc_v.get(ORD[0]) or {}).get("presenze")
    prova("chi compra: la sua (con la posizione) e l'ultima di chi vende, solo l'ora",
          [True, True, rv2.get("ora") if isinstance(rv2, dict) else None],
          [bool(pc and pc["mia"]["posizione"]), bool(pc and set(pc["altra"]) == {"ora"}),
           pc and pc["altra"]["ora"]])
    prova("chi vende: la sua ultima (due volte), e l'ora di chi compra",
          [2, True], [pv and pv["mia"]["volte"], bool(pv and pv["altra"] == {"ora": rc.get("ora")})])
    testo = json.dumps(sc_c) + json.dumps(sc_v)
    prova("...e in tutta la risposta niente lat, lon, acc, distanze: le coordinate non escono",
          [False] * 5, [k in testo for k in ('"lat"', '"lon"', '"acc"', "dist_luogo", "vicine")])
    prova("...e la prova col QR non viaggia piu' alle parti", False, '"incontro"' in testo)

    print("\n4) gli storti")
    banco.come(C)
    prova("un corpo storto e' 400, con la sua frase", (400, "Nota illeggibile"),
          banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[1], "nota": "x"}))
    manda(ORD[1], "taken", t + 100, "buyer", "take")
    manda(ORD[1], "hold-invoice-paid", t + 110, "seller")
    prova("una firma vera ma di una chiave estranea: 403, e nessuna riga",
          [(403, "La firma non e' di una delle due chiavi di questo scambio"), []],
          [banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[1], "nota": nota(SK_ALTRO, ORD[1], "qui", int(time.time()))}),
           presenze_db(ORD[1])])
    prova("...uno scambio che il coordinatore non ha ancora raccontato aspetta: 409", 409,
          banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[2], "nota": nota(SK_COMPRA, ORD[2], "qui", int(time.time()))})[0])
    prova("...l'appuntamento lo fissa SOLO chi vende: chi compra prende 403",
          (403, "L'appuntamento lo fissa chi vende, con la sua chiave di questo scambio"),
          banco.errore(SRV.appuntamento_p2p, {"ordine": ORD[1], "nota": nota(
              SK_COMPRA, ORD[1], "appuntamento", int(time.time()), quando=int(time.time()) + 600)}))
    banco.come(E)
    re_ = banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[1], "nota": nota(SK_COMPRA, ORD[1], "qui", int(time.time()))})
    prova("uno sconosciuto che porta la nota buona passa: a provare e' la firma (e il lato lo dice la chiave)",
          [True, "compra", E], [isinstance(re_, dict) and re_.get("ok"),
                                (presenze_db(ORD[1]) or [{}])[0].get("lato"),
                                (presenze_db(ORD[1]) or [{}])[0].get("caricata_da")])

    print("\n5) l'avviso a chi compra: l'appuntamento detto, e cambiato")
    banco.come(V)
    pausa = SRV.P2P_RECAPITO_PAUSA_S
    SRV.P2P_RECAPITO_PAUSA_S = 0
    try:
        del banco.DETTO[:]
        banco.chiama(SRV.recapito_p2p, {"ordine": ORD[0], "attivo": True})
        primo = list(banco.DETTO)
        del banco.DETTO[:]
        banco.chiama(SRV.recapito_p2p, {"ordine": ORD[0], "attivo": True})
        secondo = list(banco.DETTO)
    finally:
        SRV.P2P_RECAPITO_PAUSA_S = pausa
    prova("la prima volta «dove e quando vedervi», poi «ha cambiato l'appuntamento» — a chi compra",
          [[C], True, [C], True],
          [[c for c, _ in primo], bool(primo) and "ti ha indicato dove e quando vedervi" in primo[0][1],
           [c for c, _ in secondo], bool(secondo) and "ha cambiato l'appuntamento" in secondo[0][1]])

    print("\n6) la disputa: il moderatore legge il confronto")
    detto = manda(ORD[0], "dispute-opened", t + 20, "buyer")
    prova("l'avviso ai moderatori parte", True, any(c == MOD for c, _ in detto or []))
    manda(ORD[3], "taken", t + 200, "buyer", "take")
    manda(ORD[3], "hold-invoice-paid", t + 210, "seller")
    manda(ORD[3], "dispute-opened", t + 220, "seller")
    # LA PROVA COL QR DI IERI su un terzo scambio, scritta com'era
    manda(ORD[4], "taken", t + 300, "buyer", "take")
    manda(ORD[4], "hold-invoice-paid", t + 310, "seller")
    con = banco.con_db()
    con.execute("INSERT INTO p2p_presenze(ordine, giro, chiave_mostra, chiave_legge, ora_mostra, ora_legge, "
                "distanza_m, posizioni, quando) VALUES(?,1,?,?,?,?,12,2,?)",
                (ORD[4], PUB_VENDE, PUB_COMPRA, t + 320, t + 330, t + 330))
    con.commit()
    con.close()
    manda(ORD[4], "dispute-opened", t + 340, "buyer")
    m = moderazione()
    per = {d["ordine"]: d for d in m["dispute"]}
    c0 = (per.get(ORD[0]) or {}).get("presenze") or {}
    prova("la card col confronto: incontro probabile, la coppia piu' vicina, i telefoni vicini",
          ["probabile", True, True],
          [c0.get("esito"), c0.get("scarto_s") is not None and c0["scarto_s"] <= 60,
           5 <= (c0.get("distanza") or -1) <= 30])
    prova("...e l'appuntamento: all'ora, a quanto dal luogo, una versione, non cambiato dopo",
          [True, True, 1, False],
          [((c0.get("compra") or {}).get("appuntamento") or {}).get("all_ora"),
           0 <= (((c0.get("compra") or {}).get("appuntamento") or {}).get("dist_luogo") or -1) <= 15,
           (c0.get("appuntamento") or {}).get("versioni"), (c0.get("appuntamento") or {}).get("cambiato_dopo")])
    prova("...uno scambio in contanti senza niente: nessun confronto e nessuna prova (il client dice «nessuna»)",
          [True, None, None], [ORD[3] in per, per[ORD[3]]["presenze"], per[ORD[3]]["incontro"]])
    prova("...la prova col QR di ieri resta leggibile, sul suo giro", [t + 330, 12],
          [((per.get(ORD[4]) or {}).get("incontro") or {}).get("ora"),
           ((per.get(ORD[4]) or {}).get("incontro") or {}).get("distanza")])
    prova("...a disputa aperta l'appuntamento non si cambia piu': 409", 409,
          (banco.come(V), banco.errore(SRV.appuntamento_p2p, {"ordine": ORD[0], "nota": nota(
              SK_VENDE, ORD[0], "appuntamento", int(time.time()), quando=int(time.time()) + 900)}))[1][0])

    print("\n7) la chiusura scorda le posizioni e il punto")
    manda(ORD[0], "released", t + 400, "mostro", "admin", sats=13603, sats_buyer=13467, sats_seller=13739)
    righe, a = presenze_db(ORD[0]), appuntamenti_db(ORD[0])
    prova("dalle presenze se ne vanno lat, lon e la copia della nota; restano ore, distanze, posizione detta",
          [[None] * 3, [""] * 3, True, True, [1, 0, 1]],
          [[r["lat"] for r in righe], [r["prova"] for r in righe], all(r["posizione_via"] > 0 for r in righe),
           righe[2]["dist_luogo"] is not None and bool(righe[2]["vicine"]), [r["posizione"] for r in righe]])
    prova("...dall'appuntamento il punto e la nota; resta l'ora", [None, "", True],
          [a[0]["lat"], a[0]["prova"], a[0]["ora_incontro"] > 0])
    m = moderazione()
    c0 = ({d["ordine"]: d for d in m["dispute"]}.get(ORD[0]) or {}).get("presenze") or {}
    prova("...e la card chiusa lo dice, con le distanze ancora li'", [True, "probabile", True],
          [c0.get("posizioni_via"), c0.get("esito"), c0.get("distanza") is not None])
    manda(ORD[1], "canceled", t + 500, "buyer", "cooperative")
    prova("anche un annullo d'accordo scorda la posizione", True,
          all(r["posizione_via"] > 0 for r in presenze_db(ORD[1])))

    print("\n8) la scopa, e lo scambio chiuso")
    try:
        SRV.pulisci_presenze_p2p()
        prova("la scopa gira senza rompere niente", True, True)
    except Exception as e:
        prova("la scopa gira senza rompere niente", "", f"{type(e).__name__}: {e}")
    prova("...e non toglie righe fresche", [3, 1], [len(presenze_db(ORD[0])), len(presenze_db(ORD[1]))])
    banco.come(C)
    prova("su uno scambio chiuso una presenza non entra: 409", 409,
          banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[0], "nota": nota(SK_COMPRA, ORD[0], "qui", int(time.time()))})[0])

    print("\n9) il giro: l'ordine torna nel libro e lo riprende un altro")
    manda(ORD[5], "taken", t + 600, "buyer", "take")
    manda(ORD[5], "hold-invoice-paid", t + 610, "seller")
    banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[5], "nota": nota(SK_COMPRA, ORD[5], "qui", int(time.time()), geo=GEO_C)})
    manda(ORD[5], "canceled", t + 620, "mostro", "republished")
    manda(ORD[5], "taken", t + 700, "buyer", "take", compra=PUB_NUOVO)
    manda(ORD[5], "hold-invoice-paid", t + 710, "seller", compra=PUB_NUOVO)
    sc_n, sc_v = scambi(E), scambi(V)
    prova("chi ha ripreso l'ordine non vede la presenza del giro di prima, e nemmeno chi vende",
          [True, None, None],
          [ORD[5] in sc_n, (sc_n.get(ORD[5]) or {}).get("presenze"), (sc_v.get(ORD[5]) or {}).get("presenze")])
    banco.come(C)
    prova("...la chiave di chi comprava ieri non vale piu' (403); quella di oggi si'", [403, True],
          [banco.errore(SRV.sono_qui_p2p, {"ordine": ORD[5], "nota": nota(SK_COMPRA, ORD[5], "qui", int(time.time()))})[0],
           (banco.come(E), isinstance(banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[5], "nota": nota(
               SK_NUOVO, ORD[5], "qui", int(time.time()))}), dict))[1]])

    print("\n10) «dimentica il profilo»")
    manda(ORD[6], "taken", t + 800, "buyer", "take")
    manda(ORD[6], "hold-invoice-paid", t + 810, "seller")
    banco.come(C)
    banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[6], "nota": nota(SK_COMPRA, ORD[6], "qui", int(time.time()), geo=GEO_C)})
    banco.come(V)
    banco.esito(SRV.sono_qui_p2p, {"ordine": ORD[6], "nota": nota(SK_VENDE, ORD[6], "qui", int(time.time()), geo=GEO_V)})
    banco.come(C)
    prima = (len(presenze_db(ORD[0])), [r["lato"] for r in presenze_db(ORD[6])])
    SRV.dimentica_chiavi_p2p()
    aperto = {r["lato"]: r for r in presenze_db(ORD[6])}
    prova("sullo scambio CHIUSO le mie presenze se ne vanno, quelle di chi vende restano",
          [3, ["vende", "vende"]], [prima[0], [r["lato"] for r in presenze_db(ORD[0])]])
    prova("...su quello APERTO della mia resta l'ora (l'altra persona l'ha vista), posizione e nota no; l'altra intatta",
          [True, None, "", True],
          ["compra" in aperto and aperto["compra"]["ora"] > 0, (aperto.get("compra") or {}).get("lat"),
           (aperto.get("compra") or {}).get("prova"), (aperto.get("vende") or {}).get("lat") is not None])

    print("\n11) i suggerimenti degli indirizzi, contro un Photon di cartone")
    ph = Photon()
    SRV.P2P_LUOGHI_URL = ph.url
    banco.come(V)
    fuori = io.StringIO()
    with contextlib.redirect_stdout(fuori):
        r = banco.esito(SRV.luoghi_p2p, {"q": "  piazza   castello\x00 "})
        r2 = banco.esito(SRV.luoghi_p2p, {"q": "piazza castello"})
    prova("200 coi suggerimenti in forma: nome, indirizzo, etichetta, cinque decimali",
          [True, "Piazza Castello, 10123 Torino", 45.07095, 7.68591, "no-store"],
          [isinstance(r, dict) and len(r.get("luoghi", [])) == 2,
           isinstance(r, dict) and r["luoghi"][0]["etichetta"], isinstance(r, dict) and r["luoghi"][0]["lat"],
           isinstance(r, dict) and r["luoghi"][0]["lon"], isinstance(r, dict) and r.get("__cache")])
    q = parse_qs(urlparse(ph.chieste[0]["path"]).query) if ph.chieste else {}
    h = {k.lower(): v for k, v in (ph.chieste[0]["headers"] if ph.chieste else {}).items()}
    prova("A PHOTON ARRIVA SOLO IL TESTO: q ripulito, quanti, il paese — niente posizione, cookie, IP, referer",
          [{"q": ["piazza castello"], "limit": ["10"], "countrycode": ["IT"]}, True, False, False, False, False],
          [q, h.get("user-agent", "").startswith("Barattolo/"), "cookie" in h, "x-forwarded-for" in h,
           "referer" in h, "x-tg-init-data" in h])
    prova("...la stessa ricerca di nuovo viene dalla memoria: Photon chiamato una volta sola", [1, True],
          [len(ph.chieste), isinstance(r2, dict) and r2.get("luoghi") == r.get("luoghi")])
    prova("...e nel registro non c'e' il testo cercato", False, "castello" in fuori.getvalue().lower())
    prova("sotto tre lettere nessuna domanda", [{"luoghi": [], "__cache": "no-store"}, 1],
          [banco.esito(SRV.luoghi_p2p, {"q": "pi"}), len(ph.chieste)])
    vecchio = SRV.P2P_LUOGHI_PER_PERSONA
    SRV.P2P_LUOGHI_PER_PERSONA = 3
    SRV._P2P_LUOGHI_PERSONE.clear()
    try:
        esiti = [banco.errore(SRV.luoghi_p2p, {"q": f"via roma {i}"}) for i in range(4)]
    finally:
        SRV.P2P_LUOGHI_PER_PERSONA = vecchio
    prova("il freno della persona: tre passano, la quarta 429", [None, None, None, 429],
          [e if e is None else e[0] for e in esiti])
    SRV._P2P_LUOGHI_PERSONE.clear()
    with contextlib.redirect_stdout(fuori):
        ph.modo = "redirect"
        e1 = banco.errore(SRV.luoghi_p2p, {"q": "via garibaldi"})
        ph.modo = "enorme"
        e2 = banco.errore(SRV.luoghi_p2p, {"q": "via mazzini"})
        ph.srv.shutdown()
        e3 = banco.errore(SRV.luoghi_p2p, {"q": "via cavour"})
    muti = (503, "I suggerimenti non rispondono: scrivi l'indirizzo a mano")
    prova("i silenzi: un redirect, una risposta enorme, Photon giu' — 503, mai un 500", [muti, muti, muti], [e1, e2, e3])
    prova("...e la riga del registro dice il perche', mai il testo", [True, False],
          ["i suggerimenti tacciono" in fuori.getvalue(), "garibaldi" in fuori.getvalue().lower()])
    SRV.carica_comuni()
    with contextlib.redirect_stdout(fuori):
        v = banco.esito(SRV.luogo_vicino_p2p, {"lat": 45.0709, "lon": 7.6859})
        v2 = banco.esito(SRV.luogo_vicino_p2p, {"lat": 0.5, "lon": -30.0})
    prova("il comune vicino dal nostro elenco: Torino da piazza Castello; in mezzo all'oceano niente",
          ["Torino (TO)", ""], [isinstance(v, dict) and v.get("vicino"), isinstance(v2, dict) and v2.get("vicino")])
    prova("...una posizione storta e' 400", (400, "Posizione illeggibile"),
          banco.errore(SRV.luogo_vicino_p2p, {"lat": "nord", "lon": 7}))

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
