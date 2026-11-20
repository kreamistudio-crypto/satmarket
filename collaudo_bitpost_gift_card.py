# -*- coding: utf-8 -*-
"""
LE GIFT CARD DI BITPOST, IL GIRO VERO (20 nov 2026, cantiere
bitpost-gift-card).

Il server vero su un database usa-e-getta, con un BITPOST FINTO al posto
di `_bitpost_chiama` (nessuna rete: la gabbia dei collaudi lo pretende).
Il giro: chi compra (111) chiede due carte, il Bitworker (222) le prende,
il webhook firmato porta pagamento, carte e conferma, il Bitworker chiede
l'incasso e la firma passa solo dalla sua parte. In mezzo i cancelli che
non si devono rompere: la leva spenta, chi non e' admin, la firma HMAC
storta o vecchia, l'evento doppio, il webhook fuori ordine, il LINK DELLA
CARTA che non finisce mai nel database, le carte che vede solo chi
compra, le prove della disputa di una parte sola.

NON TOCCA NIENTE DI VERO: config di cartone dal banco dei pagamenti,
PRIMA dell'import del server.

USO:  python collaudo_bitpost_gift_card.py
"""
import hashlib
import hmac
import json
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
SEGRETO = "segreto-di-cartone-del-webhook"
XPUB_A = ("xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8Nqtwyb"
          "GhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8")
XPUB_B = ("xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9"
          "W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB")
LINK = "https://checkout.shopify.com/gift_cards/1/segretissimo-4f2a"


class BitpostFinto:
    """Il minimo di Bitpost che serve al giro, in memoria."""

    def __init__(self):
        self.ordini = {}
        self.chiamate = []
        self.prossimo = 12345

    def stato(self, o, sid, nome):
        o["status"] = {"id": sid, "name": nome}

    async def __call__(self, metodo, percorso, corpo=None, dati=None,
                       fuori_base=False):
        self.chiamate.append((metodo, percorso, corpo, dati))
        if percorso == "/gift-cards/shoppycode":
            return {"currency": "EUR", "denominations": [100, 500, 2500, 5000, 50000],
                    "max_order_price": 90000,
                    "networks": [{"network": "Bitcoin", "available": True,
                                  "min_order_price": 4200}]}
        if percorso == "/shoppycode/orders":
            oid = self.prossimo
            self.prossimo += 1
            o = {"id": oid, "reference": corpo["reference"],
                 "status": {"id": 1, "name": "Created"},
                 "denomination": corpo["denomination"], "quantity": corpo["quantity"],
                 "price": corpo["denomination"] * corpo["quantity"], "currency": "EUR",
                 "network": "Bitcoin", "buyer_fee": 250, "bitworker_fee": 250,
                 "total_fee": 500, "total_sats": None, "purchase": None,
                 "buyer_xpub": corpo["buyer_xpub"], "bitworker_xpub": None,
                 "created_at": "2026-11-20T10:00:00"}
            self.ordini[oid] = o
            return o
        parti = percorso.strip("/").split("/")
        oid = int(parti[1])
        o = self.ordini[oid]
        coda = "/".join(parti[2:])
        if coda == "select":
            if o["status"]["id"] != 1:
                from fastapi import HTTPException
                raise HTTPException(400, "Bitpost: Bad status")
            o["bitworker_xpub"] = corpo["bitworker_xpub"]
            o["total_sats"] = 11532
            self.stato(o, 2, "Processing")
            return o
        if coda == "":
            return o
        if coda == "payment":
            return {"network": "Bitcoin", "address": "bc1qfinto",
                    "destination": "bitcoin:bc1qfinto?amount=0.00011532",
                    "amount_sats": 11532}
        if coda == "cards":
            return {"quantity": 2, "denomination": 5000, "currency": "EUR",
                    "cards": [{"number": 1, "amount": 5000, "currency": "EUR",
                               "card_url": LINK, "expires_on": "2031-11-19"}],
                    "rejected_cards": [], "refunded_quantity": 0,
                    "missing_cards_deadline": None}
        if coda == "confirm":
            self.stato(o, 8, "Received")
            return o
        if coda == "dispute":
            if metodo == "GET":
                return {"open": True, "evidence": [
                    {"id": 1, "party": "buyer", "comment": "del compratore", "files": []},
                    {"id": 2, "party": "bitworker", "comment": "del bitworker", "files": []}]}
            self.stato(o, 9, "Disputed")
            return o
        if coda == "dispute/evidence":
            return {"open": True, "evidence": []}
        if coda == "cancel":
            if corpo["party"] == "bitworker":
                self.stato(o, 1, "Created")
            else:
                self.stato(o, 11, "Canceled")
            return o
        if coda == "payouts":
            if metodo == "GET":
                return {"network": "Bitcoin", "withdrawable": True, "payouts": [
                    {"party": "buyer", "state": "none", "owed_sats": 0},
                    {"party": "bitworker", "state": "available", "owed_sats": 11000}]}
            return {"party": corpo["party"], "network": "Bitcoin",
                    "state": "awaiting_signature", "amount_sats": 10650,
                    "session_id": 812, "psbt": "cHNidP8BAfinta"}
        if coda == "signature":
            return {"txid": "ab" * 32}
        raise AssertionError(f"rotta finta sconosciuta: {metodo} {percorso}")


def busta(tipo, dati, eid, quando, segreto=SEGRETO, t=None):
    corpo = json.dumps({"id": eid, "type": tipo, "created_at": quando,
                        "data": dati}).encode()
    t = int(time.time()) if t is None else t
    v1 = hmac.new(segreto.encode(), f"{t}.".encode() + corpo,
                  hashlib.sha256).hexdigest()
    return corpo, {"X-Bitpost-Signature": f"t={t},v1={v1}",
                   "Content-Type": "application/json"}


def main():
    print("=" * 58)
    print("  LE GIFT CARD DI BITPOST — il giro vero, col Bitpost finto")
    print("=" * 58)
    db = banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    finto = BitpostFinto()
    SRV._bitpost_chiama = finto
    SRV._BITPOST_CATALOGO.update(t=0, d=None)
    SRV.ADMIN_IDS = [111, 222, 999]
    SRV.BITPOST_API_KEY = "bpk_cartone"
    SRV.BITPOST_WEBHOOK_SEGRETO = SEGRETO
    SRV._frena = lambda *a, **k: None

    print("\n[il cancello]")
    SRV.BITPOST_ATTIVO = False
    banco.come(111, admin=True)
    prova("leva spenta: la pagina non esiste, nemmeno per un admin", 404,
          c.get("/api/bitpost/stato").status_code)
    SRV.BITPOST_ATTIVO = True
    SRV.ADMIN_IDS = [999]
    prova("accesa, solo admin: chi non lo e' non la vede", 404,
          c.get("/api/bitpost/stato").status_code)
    SRV.ADMIN_IDS = [111, 222, 999]
    d = c.get("/api/bitpost/stato").json()
    prova("admin: catalogo, tetto 250 € e il primo numero di conto",
          (5000 in d["catalogo"]["denominations"], 250, 0, []),
          (True, d["max_euro"], d["prossimo_indice"], d["miei"]))

    print("\n[chi compra chiede le carte]")
    r = c.post("/api/bitpost/ordini", json={"taglio": 50000, "quanti": 1,
                                            "xpub": XPUB_A, "indice": 0})
    prova("500 € oltre il nostro tetto di 250: no", (400, True),
          (r.status_code, "250" in r.json()["detail"]))
    r = c.post("/api/bitpost/ordini", json={"taglio": 500, "quanti": 1,
                                            "xpub": XPUB_A, "indice": 0})
    prova("5 € sotto il minimo di Bitcoin: no", 400, r.status_code)
    r = c.post("/api/bitpost/ordini", json={"taglio": 5000, "quanti": 2,
                                            "xpub": "tpubNONVA", "indice": 0})
    prova("una tpub non e' mainnet: no", 400, r.status_code)
    r = c.post("/api/bitpost/ordini", json={"taglio": 5000, "quanti": 2,
                                            "xpub": "xprv9s21ZrQH143K", "indice": 0})
    prova("una privata non entra", (400, True),
          (r.status_code, "PRIVATA" in r.json()["detail"]))
    r = c.post("/api/bitpost/ordini", json={"taglio": 5000, "quanti": 2,
                                            "xpub": XPUB_A, "indice": 0})
    prova("due carte da 50 €: l'ordine nasce", 200, r.status_code)
    oid = r.json()["ordine"]["id"]
    inviato = [x for x in finto.chiamate if x[1] == "/shoppycode/orders"][-1][2]
    prova("a Bitpost: la xpub, il webhook di casa, niente rete scelta",
          (XPUB_A, True, False),
          (inviato["buyer_xpub"], inviato["webhook_url"].endswith("/api/bitpost/webhook"),
           "network" in inviato))
    prova("la risposta non ripete la xpub", False,
          "buyer_xpub" in r.json()["ordine"])
    r = c.post("/api/bitpost/ordini", json={"taglio": 5000, "quanti": 2,
                                            "xpub": XPUB_A, "indice": 0})
    prova("lo stesso numero di conto due volte: no", 409, r.status_code)
    prova("...e il prossimo e' l'1", 1,
          c.get("/api/bitpost/stato").json()["prossimo_indice"])
    prova("chi compra non prende il suo ordine", 400,
          c.post(f"/api/bitpost/ordini/{oid}/prendi",
                 json={"xpub": XPUB_B, "indice": 1}).status_code)

    print("\n[il Bitworker lo prende]")
    banco.come(222, admin=True)
    d = c.get("/api/bitpost/stato").json()
    prova("in bacheca, senza xpub ne' reference", (1, False, False),
          (len(d["bacheca"]), "buyer_xpub" in d["bacheca"][0],
           "reference" in d["bacheca"][0]))
    banco.DETTO.clear()
    r = c.post(f"/api/bitpost/ordini/{oid}/prendi", json={"xpub": XPUB_B, "indice": 0})
    prova("preso", 200, r.status_code)
    prova("...e chi compra lo sa", [111], [x[0] for x in banco.DETTO])
    banco.come(333, admin=True)
    prova("un terzo non vede l'ordine", 404, c.get(f"/api/bitpost/ordini/{oid}").status_code)
    banco.come(111, admin=True)
    d = c.get(f"/api/bitpost/ordini/{oid}").json()
    prova("chi compra vede il pagamento, non `purchase`", (11532, False),
          (d["pagamento"]["amount_sats"], "purchase" in d["ordine"]))
    banco.come(222, admin=True)
    prova("il Bitworker il pagamento non lo vede", False,
          "pagamento" in c.get(f"/api/bitpost/ordini/{oid}").json())

    print("\n[il webhook: la firma]")
    o = dict(finto.ordini[oid])
    finto.stato(o, 1000, "GiftCardPurchasing")
    o["purchase"] = {"url": "https://thegiftcard.shoppycode.com/",
                     "recipient_email": "giftcard-x@gift.bitpost.shop",
                     "denomination": 5000, "quantity": 2, "currency": "EUR"}
    finto.ordini[oid] = o
    corpo, t = busta("order.status_changed", {"reason": "x", "order": o},
                     "ev-1", "2026-11-20T10:05:00Z", segreto="sbagliato")
    prova("firma storta: 401", 401,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)
    corpo, t = busta("order.status_changed", {"reason": "x", "order": o},
                     "ev-1", "2026-11-20T10:05:00Z", t=int(time.time()) - 600)
    prova("firma di dieci minuti fa: 401", 401,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)
    SRV.BITPOST_WEBHOOK_SEGRETO = "INCOLLA_QUI_IL_SEGRETO"
    corpo, t = busta("order.status_changed", {"reason": "x", "order": o},
                     "ev-1", "2026-11-20T10:05:00Z", segreto="INCOLLA_QUI_IL_SEGRETO")
    prova("col segnaposto nel config non passa niente", 401,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)
    SRV.BITPOST_WEBHOOK_SEGRETO = SEGRETO
    banco.DETTO.clear()
    corpo, t = busta("order.status_changed", {"reason": "x", "order": o},
                     "ev-1", "2026-11-20T10:05:00Z")
    prova("firma giusta: 200", 200,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)
    prova("...e il Bitworker sa che deve comprare", [222], [x[0] for x in banco.DETTO])
    prova("la stessa busta di nuovo: 200 e niente di nuovo", (200, True),
          (c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code,
           len(banco.DETTO) == 1))
    vecchio = dict(o)
    finto.stato(vecchio, 2, "Processing")
    corpo, t = busta("order.status_changed", {"reason": "x", "order": vecchio},
                     "ev-0", "2026-11-20T10:01:00Z")
    c.post("/api/bitpost/webhook", content=corpo, headers=t)
    con = SRV.db()
    prova("un evento piu' vecchio arrivato dopo non torna indietro", 1000,
          con.execute("SELECT stato FROM bitpost_ordini WHERE id=?", (oid,)).fetchone()[0])
    con.close()
    d = c.get(f"/api/bitpost/ordini/{oid}").json()
    prova("il Bitworker vede cosa comprare e dove regalarlo",
          "giftcard-x@gift.bitpost.shop", d["ordine"]["purchase"]["recipient_email"])

    print("\n[le carte]")
    banco.DETTO.clear()
    carta = {"number": 1, "amount": 5000, "currency": "EUR", "card_url": LINK,
             "expires_on": "2031-11-19", "received_at": "2026-11-20T11:00:00",
             "delivered_at": "2026-11-20T11:00:01"}
    corpo, t = busta("order.gift_card_delivered", {"card": carta, "order": o},
                     "ev-2", "2026-11-20T11:00:01Z")
    prova("carta arrivata: 200", 200,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)
    prova("...chi compra lo sa", [111], [x[0] for x in banco.DETTO])
    crudo = open(db, "rb").read()
    prova("IL LINK DELLA CARTA NON E' NEL DATABASE", False,
          b"segretissimo" in crudo)
    con = SRV.db()
    prova("...ma i suoi dati si'", (1, 5000, "2031-11-19"),
          tuple(con.execute("SELECT numero, importo, scade FROM bitpost_carte "
                            "WHERE ordine_id=?", (oid,)).fetchone()))
    con.close()
    prova("il Bitworker le carte non le vede", 403,
          c.get(f"/api/bitpost/ordini/{oid}/carte").status_code)
    banco.come(111, admin=True)
    r = c.get(f"/api/bitpost/ordini/{oid}/carte")
    prova("chi compra si', col link riletto da Bitpost", (200, LINK),
          (r.status_code, r.json()["carte"][0]["card_url"]))

    print("\n[conferma, disputa, prove]")
    finto.stato(finto.ordini[oid], 1002, "GiftCardWaitingConfirm")
    banco.come(222, admin=True)
    prova("il Bitworker non conferma al posto di chi compra", 403,
          c.post(f"/api/bitpost/ordini/{oid}/conferma").status_code)
    banco.come(111, admin=True)
    prova("disputa senza motivo: no", 400,
          c.post(f"/api/bitpost/ordini/{oid}/disputa", json={}).status_code)
    prova("disputa: si'", 200, c.post(f"/api/bitpost/ordini/{oid}/disputa",
          json={"motivo": "NotWorking", "note": "la 1 dice gia' usata"}).status_code)
    prova("...a Bitpost arrivano motivo e note",
          {"reason": "NotWorking", "notes": "la 1 dice gia' usata"},
          [x for x in finto.chiamate if x[1].endswith("/dispute")][-1][2])
    d = c.get(f"/api/bitpost/ordini/{oid}").json()
    prova("chi compra vede solo le SUE prove", ["del compratore"],
          [p["comment"] for p in d["disputa"]["prove"]])
    banco.come(222, admin=True)
    prova("il Bitworker manda la sua prova, come bitworker", (200, "bitworker"),
          (c.post(f"/api/bitpost/ordini/{oid}/prove",
                  json={"commento": "erano nuove"}).status_code,
           finto.chiamate[-1][3]["party"]))

    print("\n[l'incasso e la firma]")
    finto.stato(finto.ordini[oid], 8, "Received")
    d = c.get(f"/api/bitpost/ordini/{oid}").json()
    prova("il Bitworker ha il suo incasso disponibile", ("available", 11000),
          (d["incasso"]["state"], d["incasso"]["owed_sats"]))
    prova("un indirizzo di testnet non va", 400,
          c.post(f"/api/bitpost/ordini/{oid}/incasso",
                 json={"indirizzo": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"}).status_code)
    r = c.post(f"/api/bitpost/ordini/{oid}/incasso",
               json={"indirizzo": "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4"})
    prova("un bc1 maiuscolo va, e si manda minuscolo", (200, "bitworker",
          "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"),
          (r.status_code, finto.chiamate[-1][2]["party"], finto.chiamate[-1][2]["address"]))
    banco.come(111, admin=True)
    prova("chi compra non firma la sessione del Bitworker", 404,
          c.post(f"/api/bitpost/ordini/{oid}/firma",
                 json={"sessione": 812, "psbt": "cHNidP8"}).status_code)
    banco.come(222, admin=True)
    d = c.get(f"/api/bitpost/ordini/{oid}").json()
    prova("la firma aspetta il telefono del Bitworker", [812],
          [f["sessione"] for f in d["firme"]])
    r = c.post(f"/api/bitpost/ordini/{oid}/firma",
               json={"sessione": 812, "psbt": "cHNidP8firmata"})
    prova("il Bitworker firma: parte", (200, "ab" * 32), (r.status_code, r.json()["txid"]))
    prova("...e la firma non aspetta piu'", [],
          c.get(f"/api/bitpost/ordini/{oid}").json()["firme"])

    print("\n[la webhook di una firma chiesta, e un ordine non nostro]")
    corpo, t = busta("order.signature_requested",
                     {"session_id": 900, "network": "Bitcoin", "party": "buyer",
                      "pset": "cHNidP8BAaltra", "recipient": {"address": "bc1q", "amount_sats": 5},
                      "expires_at": "2026-11-21T10:00:00Z", "order": finto.ordini[oid]},
                     "ev-3", "2026-11-20T12:00:00Z")
    c.post("/api/bitpost/webhook", content=corpo, headers=t)
    banco.come(111, admin=True)
    prova("chi compra ritrova la sua firma da fare", [900],
          [f["sessione"] for f in c.get(f"/api/bitpost/ordini/{oid}").json()["firme"]])
    corpo, t = busta("order.status_changed", {"order": {"id": 1, "status": {"id": 8}}},
                     "ev-4", "2026-11-20T12:00:00Z")
    prova("un ordine che non e' nostro: 200 e basta", 200,
          c.post("/api/bitpost/webhook", content=corpo, headers=t).status_code)

    print("\n[il ponte vero: l'indirizzo e gli errori di Bitpost]")
    prova("in collaudo una base fuori casa non e' ammessa", False,
          SRV._bitpost_base_ammessa("https://beta.bitpost.shop/api/v1/barattolo", True))
    prova("...in collaudo il finto su loopback si'", True,
          SRV._bitpost_base_ammessa("http://127.0.0.1:9911/api/v1/barattolo", True))
    prova("...fuori dal collaudo serve https", (True, False),
          (SRV._bitpost_base_ammessa("https://beta.bitpost.shop/api/v1/barattolo", False),
           SRV._bitpost_base_ammessa("http://beta.bitpost.shop/api/v1/barattolo", False)))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
