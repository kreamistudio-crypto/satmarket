# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ORDINE ON-CHAIN (23 ott 2026, cantiere onchain-tappa3) —
il giro col SERVER VERO, per HTTP (TestClient, la app vera), delle tappe
3, 4 e 5: la cassa che al posto della fattura da' un indirizzo 2-di-3, la
sorveglianza che vede arrivare i sats, la prima firma di chi propone e la
seconda di chi co-firma, poi la trasmissione. E i no: chi non e' ammesso,
lo stock prenotato, i PSBT storti, la firma che manca, la seconda firma
della stessa persona.

IL «TELEFONO» QUI E' EMBIT, come nel collaudo della tappa 2: i semi sono
i vettori ufficiali del BIP-39, le firme si fanno con embit. Che il
telefono vero (il bundle) firmi PSBT che embit legge lo dice
prove_ordine_onchain. MEMPOOL E' DI CARTONE: le monete di un indirizzo,
la tariffa e la trasmissione sono tre funzioni sostituite. Nessuna rete,
nessun sats.

DAL 27 OTT 2026 (cantiere onchain-ordini, la strada A di Andrea: «gli
step devono essere uguali, cambia solo il metodo di pagamento») quando i
sats arrivano nasce l'ORDINE DI SEMPRE in `ordini`, cassaforte 'onchain':
qui si prova che e' in «Ordini», che lo chiude per la porta di sempre la
seconda firma, che il rimborso passa da «Annulla la vendita», e che dal
Lightning non esce niente.

USO:  python collaudo_onchain_ordine.py
"""
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  L'ORDINE ON-CHAIN (tappe 3-5) — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from embit import bip32, bip39, script
    from embit.finalizer import finalize_psbt
    from embit.networks import NETWORKS
    from embit.psbt import PSBT
    from embit.transaction import (Transaction, TransactionInput,
                                   TransactionOutput)
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    N = NETWORKS["signet"]
    vett = json.load(open(os.path.join(banco.QUI, "vendor",
                                       "vettori-bip.json"), encoding="utf-8"))
    semi = {999: vett["bip39_english"][0]["parole"],
            888: vett["bip39_english"][1]["parole"]}

    def radice(tg):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=N["xprv"])

    def conto(tg):
        return radice(tg).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=N["xpub"])

    def incasso_mio(tg, n):
        k = radice(tg).derive(f"m/48h/1h/0h/2h/1/{n}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    # --- mempool di cartone ------------------------------------------
    MONETE, INVIATE = {}, []

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0

    async def invia_finta(tx_hex):
        INVIATE.append(tx_hex)
        return Transaction.from_string(tx_hex).txid().hex()

    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta
    SRV.onchain_mempool_invia = invia_finta

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan"), (777, "Terzo"),
                     (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    annunci = []
    for n in range(6):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(888,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Cosa on-chain {n}",))
        annunci.append(cur.lastrowid)
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888, 777]
    SRV.ONCHAIN_ATTIVO = True

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def compra(tg, aid, **piu):
        come(tg)
        return c.post("/api/orders", json={"annuncio_id": aid,
                                           "consegna": "ritiro", **piu})

    def ordine(tg, oid):
        come(tg)
        return next(o for o in c.get("/api/onchain/ordini").json()["ordini"]
                    if o["id"] == oid)

    def controlla(tg, oid):
        come(tg)
        return c.post(f"/api/onchain/ordini/{oid}/controlla")

    def paga(o, confermata=True, quanto=None):
        MONETE[o["indirizzo"]["indirizzo"]] = [{
            "txid": f"{o['id']:02x}" * 32, "vout": 0,
            "value": o["importo_sats"] if quanto is None else quanto,
            "status": {"confirmed": confermata}}]

    def psbt_di(o, uscite, firma=None, numero=None):
        """Il PSBT d'uscita di un ordine, come lo fa il telefono: le
        monete dell'ordine, il witness script dalle tre chiavi, e la
        firma di `firma` col SUO numero."""
        ch = o["indirizzo"]["chiavi"]
        from embit.ec import PublicKey
        pubs = sorted((PublicKey.parse(bytes.fromhex(ch[k]))
                       for k in ("compratore", "venditore", "barattolo")),
                      key=lambda p: p.sec())
        ws = script.multisig(2, pubs)
        tx = Transaction(
            vin=[TransactionInput(bytes.fromhex(u["txid"]), u["vout"])
                 for u in o["utxo"]],
            vout=[TransactionOutput(v, script.address_to_scriptpubkey(d))
                  for d, v in uscite])
        p = PSBT(tx)
        for i, u in zip(p.inputs, o["utxo"]):
            i.witness_utxo = TransactionOutput(u["value"], script.p2wsh(ws))
            i.witness_script = ws
        if firma:
            n = o["indirizzo"]["mio_numero"] if numero is None else numero
            p.sign_with(radice(firma).derive(f"m/48h/1h/0h/2h/0/{n}").key)
        return p

    def cofirma(tg, o):
        p = PSBT.from_string(o["proposta"]["psbt"])
        p.sign_with(radice(tg).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        return finalize_psbt(p).serialize().hex()

    def proponi(tg, oid, verso, p):
        come(tg)
        return c.post(f"/api/onchain/ordini/{oid}/proposta",
                      json={"verso": verso, "psbt": p.to_string()})

    def firma(tg, oid, tx_hex):
        come(tg)
        return c.post(f"/api/onchain/ordini/{oid}/firma", json={"tx": tx_hex})

    # ---- 1) la cassa ---------------------------------------------------
    print("\n[la cassa: la scelta on-chain e i suoi no]")
    r = compra(111, annunci[0], metodo="onchain")
    prova("chi non e' ammesso: 400, e nessun ordine nasce", (400, True),
          (r.status_code, "non è disponibile" in r.json()["detail"]))
    come(999)
    prova("la cassa chiede se il venditore e' pronto: non ancora",
          (False, "il venditore non ha ancora aperto Barattolo da "
                  "quando l'on-chain c'e': si accende da solo appena lo apre"),
          tuple(c.get("/api/onchain/pronto/888").json()[k]
                for k in ("pronto", "motivo")))
    r = compra(999, annunci[0], metodo="onchain")
    prova("...e se si prova lo stesso: 400 col perche'", (400, True),
          (r.status_code, "non ha ancora acceso" in r.json()["detail"]))
    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    come(999)
    prova("accesi tutti e due: pronto", True,
          c.get("/api/onchain/pronto/888").json()["pronto"])
    r = compra(999, annunci[0], metodo="onchain", offerta_id=0)
    o = r.json().get("onchain") or {}
    prova("l'ordine on-chain nasce: 200, in attesa, niente fattura", (200, "attesa", False),
          (r.status_code, o.get("stato"), "invoice" in r.json()))
    prova("...il prezzo e' quello del Lightning, piu' il margine di rete "
          "(3 x 2 sat/vB x 180 vB = 1080)", (50000, 1080, 51080),
          (o["prezzo_sats"], o["margine_sats"], o["importo_sats"]))
    prova("...l'indirizzo e' un 2-di-3 di signet, e chi compra e' il "
          "compratore", (True, "compratore"),
          (o["indirizzo"]["indirizzo"].startswith("tb1q"),
           o["indirizzo"]["ruolo"]))
    prova("...gli incassi sono chiavi dei LORO semi, al numero dell'ordine",
          (incasso_mio(888, 0), incasso_mio(999, 0)),
          (o["incasso"], o["rimborso"]))
    prova("...e nessuna xpub esce", [False, False],
          [conto(888) in r.text, conto(999) in r.text])
    r = compra(777, annunci[0])
    prova("lo stock e' prenotato: un altro al Lightning trova 409", 409,
          r.status_code)
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='attivo' WHERE id=?", (annunci[1],))
    con.commit()
    con.close()
    r = compra(999, annunci[1])
    prova("...e il Lightning di sempre non e' cambiato: una fattura", (200, True),
          (r.status_code, r.json().get("invoice", "").startswith("lnbc")))

    # ---- 2) la sorveglianza ------------------------------------------------
    print("\n[la sorveglianza: mempool vede, una conferma decide]")
    oid = o["id"]
    prova("niente sull'indirizzo: resta in attesa", "attesa",
          controlla(999, oid).json()["stato"])
    paga(o, confermata=False)
    d = controlla(999, oid).json()
    prova("visti ma non confermati: ancora attesa, e lo si vede",
          ("attesa", 51080, 0), (d["stato"], d["visti_sats"], d["ricevuti_sats"]))
    come(999)
    prova("...e ora annullare non si puo' piu': 409", 409,
          c.post(f"/api/onchain/ordini/{oid}/annulla").status_code)
    paga(o, quanto=50000)
    prova("confermati ma meno del dovuto: ancora attesa", "attesa",
          controlla(888, oid).json()["stato"])
    banco.DETTO.clear()
    paga(o)
    d = controlla(888, oid).json()
    prova("confermati tutti: pagato, con la sua moneta", ("pagato", 1),
          (d["stato"], len(d["utxo"])))
    con = SRV.db()
    a = con.execute("SELECT quantita, stato FROM annunci WHERE id=?",
                    (annunci[0],)).fetchone()
    nato = con.execute("SELECT o.* FROM ordini o JOIN onchain_ordini c "
                       "ON c.ordine_id=o.id WHERE c.id=?", (oid,)).fetchone()
    con.close()
    prova("...lo stock e' sceso e l'annuncio e' venduto", (0, "venduto"),
          (a["quantita"], a["stato"]))
    # LA STRADA A: l'ordine di sempre, passato a 'locked' da _incassa_ordine
    prova("...ed e' nato l'ordine di sempre: locked, cassaforte onchain, "
          "senza fattura", ("locked", "onchain", "", 999, 888, 50000, "ritiro"),
          (nato["stato"], nato["cassaforte"], nato["payment_hash"],
           nato["compratore_id"], nato["venditore_id"], nato["prezzo_sats"],
           nato["consegna_scelta"]))
    ord_id = nato["id"]
    prova("...e lo sanno tutti e due, con gli avvisi del Lightning "
          "(«Hai venduto»)", ([888, 999], True),
          (sorted({chi for chi, _ in banco.DETTO}),
           any("Hai venduto" in t for chi, t in banco.DETTO if chi == 888)))
    come(999)
    mio = next((x for x in c.get("/api/orders").json() if x["id"] == ord_id), {})
    prova("in «Ordini» di chi compra, col riassunto della sua cassaforte",
          ("locked", oid, "pagato", None),
          (mio.get("stato"), (mio.get("onchain") or {}).get("id"),
           (mio.get("onchain") or {}).get("stato"),
           (mio.get("onchain") or {}).get("proposta")))
    come(888)
    prova("...e in quelli di chi vende", True,
          any(x["id"] == ord_id for x in c.get("/api/orders").json()))
    prova("il foglio On-chain dice l'ordine di sempre", ord_id,
          ordine(999, oid)["ordine_id"])
    prova("un secondo «controlla» non fa nascere un secondo ordine", 1,
          (controlla(999, oid), SRV.db().execute(
              "SELECT COUNT(*) FROM ordini WHERE cassaforte='onchain' "
              "AND annuncio_id=?", (annunci[0],)).fetchone()[0])[1])
    come(999)
    r = c.post(f"/api/orders/{ord_id}/conferma")
    prova("«conferma» per la porta del Lightning: niente esce, e lo dice",
          (200, True, "locked"),
          (r.status_code, r.json().get("onchain"),
           SRV.db().execute("SELECT stato FROM ordini WHERE id=?",
                            (ord_id,)).fetchone()[0]))
    come(777)
    prova("chi non c'entra: 404", 404,
          c.post(f"/api/onchain/ordini/{oid}/controlla").status_code)

    # ---- 3) la prima firma ------------------------------------------------
    print("\n[la prima firma: Libera i sats]")
    o = ordine(999, oid)
    giusto = [(o["incasso"], 50000), (o["rimborso"], 51080 - 50000 - 300)]
    prova("il venditore non libera a se stesso: 403", 403,
          proponi(888, oid, "venditore", psbt_di(o, giusto, 888)).status_code)
    r = proponi(999, oid, "venditore", psbt_di(o, giusto))
    prova("senza la firma di chi propone: 400", (400, True),
          (r.status_code, "manca la tua firma" in r.json()["detail"]))
    r = proponi(999, oid, "venditore",
                psbt_di(o, [(o["incasso"], 49000), giusto[1]], 999))
    prova("al venditore meno del prezzo: 400", (400, True),
          (r.status_code, "esattamente il prezzo" in r.json()["detail"]))
    r = proponi(999, oid, "venditore",
                psbt_di(o, [giusto[0], (incasso_mio(888, 5), 780)], 999))
    prova("un'uscita verso un indirizzo estraneo: 400", (400, True),
          (r.status_code, "non conosce" in r.json()["detail"]))
    r = proponi(999, oid, "venditore",
                psbt_di(o, [giusto[0], (o["rimborso"], 10)], 999))
    prova("un resto sotto la polvere: 400", (400, True),
          (r.status_code, "polvere" in r.json()["detail"]))
    banco.DETTO.clear()
    r = proponi(999, oid, "venditore", psbt_di(o, giusto, 999))
    prova("la proposta giusta: 200, e il venditore e' avvisato", (200, [888]),
          (r.status_code, [chi for chi, _ in banco.DETTO]))
    come(999)
    mio = next(x for x in c.get("/api/orders").json() if x["id"] == ord_id)
    prova("...e in «Ordini» chi compra vede la sua firma", {"verso": "venditore",
                                                          "mia": True,
                                                          "barattolo": ""},
          mio["onchain"]["proposta"])

    # ---- 4) la seconda firma ------------------------------------------------
    print("\n[la seconda firma e la trasmissione]")
    o9, o8 = ordine(999, oid), ordine(888, oid)
    prova("la proposta la vedono tutti e due, ciascuno dal suo lato",
          (True, False, "venditore"),
          (o9["proposta"]["mia"], o8["proposta"]["mia"], o8["ruolo"]))
    prova("...e il venditore ritrova il suo incasso dal suo seme",
          incasso_mio(888, o8["indirizzo"]["mio_numero"]), o8["incasso"])
    pronta = cofirma(888, o8)
    prova("la transazione completa, mandata da chi ha proposto: 409 (le "
          "due firme sono di due persone)", 409,
          firma(999, oid, pronta).status_code)
    # una disputa aperta fra le due firme ferma la seconda
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='dispute' WHERE id=?", (ord_id,))
    con.commit()
    con.close()
    prova("a disputa aperta la seconda firma non passa: 409", 409,
          firma(888, oid, pronta).status_code)
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='locked' WHERE id=?", (ord_id,))
    con.commit()
    con.close()
    altra = psbt_di(o8, [(o["incasso"], 50000), (o["rimborso"], 700)], 888)
    altra.sign_with(radice(999).derive(
        f"m/48h/1h/0h/2h/0/{o9['indirizzo']['mio_numero']}").key)
    prova("una transazione diversa da quella proposta: 400", 400,
          firma(888, oid, finalize_psbt(altra).serialize().hex()).status_code)
    prova("...e niente e' partito", [], INVIATE)
    r = firma(888, oid, pronta)
    prova("la co-firma del venditore: 200, rilasciato, trasmessa", (200, "rilasciato", 1),
          (r.status_code, r.json().get("stato"), len(INVIATE)))
    t = Transaction.from_string(INVIATE[0])
    prova("...la transazione paga il prezzo al venditore e il resto torna",
          [(o["incasso"], 50000), (o["rimborso"], 780)],
          [(u.script_pubkey.address(N), u.value) for u in t.vout])
    prova("...e l'ordine porta il txid", r.json()["txid"],
          ordine(999, oid)["txid_uscita"])
    con = SRV.db()
    chiuso = con.execute("SELECT stato, payout_stato FROM ordini WHERE id=?",
                         (ord_id,)).fetchone()
    conti = [con.execute(f"SELECT {k} FROM utenti WHERE tg_id=?",
                         (tg,)).fetchone()[0]
             for k, tg in (("vendite_ok", 888), ("acquisti_ok", 999))]
    con.close()
    prova("l'ordine di sempre si chiude per la sua porta: released, coi "
          "conti delle due parti", ("released", "uscito", [1, 1]),
          (chiuso["stato"], chiuso["payout_stato"], conti))

    # ---- 5) il rimborso -------------------------------------------------
    print("\n[il rimborso: lo stesso gesto a parti invertite]")
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='attivo', quantita=1 WHERE id=?",
                (annunci[2],))
    con.commit()
    con.close()
    o = compra(999, annunci[2], metodo="onchain").json()["onchain"]
    paga(o)
    controlla(999, o["id"])
    o8 = ordine(888, o["id"])
    ord2 = o8["ordine_id"]
    indietro = [(o8["rimborso"], o8["importo_sats"] - 400)]
    prova("il rimborso non si propone a ordine vivo: parte da «Annulla la "
          "vendita»", (409, True),
          (lambda r: (r.status_code, "Annulla" in r.json()["detail"]))(
              proponi(888, o["id"], "compratore", psbt_di(o8, indietro, 888))))
    banco.DETTO.clear()
    come(888)
    r = c.post(f"/api/orders/{ord2}/annulla-vendita", json={"motivo": "spedizione"})
    prova("«Annulla la vendita»: refund, il Lightning non paga, e chi "
          "compra sa che firma il suo telefono", (200, "refund", True, True),
          (r.status_code, r.json().get("stato"),
           (r.json().get("rimborso") or {}).get("onchain"),
           any("seconda firma" in t for chi, t in banco.DETTO if chi == 999)))
    prova("chi compra non si propone il rimborso da solo: 403", 403,
          proponi(999, o["id"], "compratore",
                  psbt_di(ordine(999, o["id"]), indietro, 999)).status_code)
    r = proponi(888, o["id"], "compratore",
                psbt_di(o8, [(o8["rimborso"], 40000)], 888))
    prova("un rimborso che lascia alla rete piu' del margine: 400",
          (400, True), (r.status_code, "margine" in r.json()["detail"]))
    r = proponi(888, o["id"], "compratore", psbt_di(o8, indietro, 888))
    prova("il venditore propone il rimborso: 200", 200, r.status_code)
    o9 = ordine(999, o["id"])
    r = firma(999, o["id"], cofirma(999, o9))
    prova("chi compra co-firma: rimborsato, tutto a lui meno la rete",
          (200, "rimborsato", [(o9["rimborso"], o9["importo_sats"] - 400)]),
          (r.status_code, r.json().get("stato"),
           [(u.script_pubkey.address(N), u.value)
            for u in Transaction.from_string(INVIATE[-1]).vout]))
    prova("...i due ordini hanno chiavi nuove (numeri 1, non 0)", (1, 1),
          (o9["indirizzo"]["mio_numero"], o8["indirizzo"]["mio_numero"]))
    con = SRV.db()
    prova("...e l'ordine di sempre e' refunded", "refunded",
          con.execute("SELECT stato FROM ordini WHERE id=?",
                      (ord2,)).fetchone()[0])
    con.close()

    # ---- 5b) la disputa: decide un moderatore, firma Barattolo --------------
    # (27 ott 2026, cantiere onchain-disputa). Finche' la chiave sul VPS
    # non nasce, firma quella di cartone (vettori BIP-32, privata nota):
    # e' la stessa strada, con una chiave che tutti conoscono.
    print("\n[la disputa: il moderatore decide, Barattolo firma, chi vince co-firma]")
    from embit.ec import PublicKey

    def nuovo_pagato(aid):
        con = SRV.db()
        con.execute("UPDATE annunci SET stato='attivo', quantita=1 WHERE id=?",
                    (aid,))
        con.commit()
        con.close()
        o = compra(999, aid, metodo="onchain").json()["onchain"]
        paga(o)
        controlla(999, o["id"])
        return o["id"], ordine(999, o["id"])["ordine_id"]

    def risolvi(tg, ord_id, esito):
        come(tg)
        return c.post(f"/api/admin/orders/{ord_id}/risolvi", json={"esito": esito})

    def firmata_da_barattolo(o):
        p = PSBT.from_string(o["proposta"]["psbt"])
        k = o["indirizzo"]["chiavi"]["barattolo"]
        return all(k in {x.sec().hex() for x in i.partial_sigs} for i in p.inputs)

    def stato_di(ord_id):
        return SRV.db().execute("SELECT stato FROM ordini WHERE id=?",
                                (ord_id,)).fetchone()[0]

    oc3, ord3 = nuovo_pagato(annunci[4])
    come(999)
    prova("chi compra apre la disputa, come sul Lightning", 200,
          c.post(f"/api/orders/{ord3}/disputa").status_code)
    r = risolvi(999, ord3, "rimborso")
    prova("un moderatore che e' parte dell'ordine non lo decide: 403", 403,
          r.status_code)
    r = risolvi(777, ord3, "meno_spese")
    prova("«meno le spese» on-chain non c'e' ancora: 409 col perche'", (409, True),
          (r.status_code, "meno le spese" in r.json().get("detail", "")))
    banco.DETTO.clear()
    banco.AVVISI.clear()
    r = risolvi(777, ord3, "rimborso")
    prova("il moderatore da' ragione a chi compra: Barattolo firma, l'ordine "
          "resta in disputa", (200, True, "compratore", "dispute"),
          (r.status_code, r.json().get("onchain"), r.json().get("attesa_firma"),
           stato_di(ord3)))
    prova("...lo sanno le due parti e gli admin", ([888, 999], 1),
          (sorted({chi for chi, _ in banco.DETTO}),
           sum("Barattolo ha firmato" in t for t in banco.AVVISI)))
    o9 = ordine(999, oc3)
    prova("...la proposta e' di Barattolo, verso chi compra, con la sua firma",
          ("compratore", "disputa", False, True),
          (o9["proposta"]["verso"], o9["proposta"]["barattolo"],
           o9["proposta"]["mia"], firmata_da_barattolo(o9)))
    prova("...e tutto va al rimborso di chi compra, la rete dentro il margine",
          (True, True),
          (lambda t: (all(u.script_pubkey.address(N) == o9["rimborso"] for u in t.vout),
                      0 < o9["importo_sats"] - sum(u.value for u in t.vout)
                      <= o9["margine_sats"]))(PSBT.from_string(o9["proposta"]["psbt"]).tx))
    come(999)
    mio = next(x for x in c.get("/api/orders").json() if x["id"] == ord3)
    prova("...in «Ordini» si vede che manca la firma di chi vince",
          {"verso": "compratore", "mia": False, "barattolo": "disputa"},
          mio["onchain"]["proposta"])
    r = risolvi(777, ord3, "venditore")
    prova("una firma data non si ritira: dare poi ragione all'altro e' 409",
          (409, True), (r.status_code, "non si ritira" in r.json().get("detail", "")))
    prova("...la stessa decisione due volte non firma di nuovo", (200, True),
          (lambda r: (r.status_code, r.json().get("gia_firmata")))(
              risolvi(777, ord3, "rimborso")))
    o8 = ordine(888, oc3)
    prova("chi vende non sostituisce la proposta di Barattolo: 409", 409,
          proponi(888, oc3, "compratore",
                  psbt_di(o8, [(o8["rimborso"], o8["importo_sats"] - 400)],
                          888)).status_code)
    r = firma(999, oc3, cofirma(999, o9))
    prova("chi compra co-firma: rimborsato, e l'ordine di sempre e' refunded",
          (200, "rimborsato", "refunded"),
          (r.status_code, r.json().get("stato"), stato_di(ord3)))

    # a favore di chi vende, con la quota fissa di Barattolo nel conto
    SRV.ONCHAIN_QUOTA_FISSA_SATS = 1000
    oc4, ord4 = nuovo_pagato(annunci[5])
    SRV.ONCHAIN_QUOTA_FISSA_SATS = 0
    come(999)
    c.post(f"/api/orders/{ord4}/disputa")
    r = risolvi(777, ord4, "venditore")
    o8 = ordine(888, oc4)
    uscite = [(u.script_pubkey.address(N), u.value)
              for u in PSBT.from_string(o8["proposta"]["psbt"]).tx.vout]
    prova("ragione a chi vende: il prezzo a lui, la quota a Barattolo, il "
          "resto a chi compra", (200, [(o8["incasso"], 50000),
                                       (o8["quota_indirizzo"], 1000)], True),
          (r.status_code, uscite[:2],
           len(uscite) == 2 or uscite[2][0] == o8["rimborso"]))
    r = firma(888, oc4, cofirma(888, o8))
    prova("chi vende co-firma: rilasciato, e l'ordine e' released",
          (200, "rilasciato", "released"),
          (r.status_code, r.json().get("stato"), stato_di(ord4)))

    # ---- 5c) la chiave sul VPS, e il reso ------------------------------------
    print("\n[la chiave di Barattolo sul VPS, e il reso]")
    come(888)
    prova("la chiave la vede e la crea solo un moderatore... (888 lo e')", 200,
          c.get("/api/admin/onchain/chiave").status_code)
    come(111)
    prova("...chi non lo e': 403", (403, 403),
          (c.get("/api/admin/onchain/chiave").status_code,
           c.post("/api/admin/onchain/chiave").status_code))
    come(777)
    prova("prima del gesto la terza chiave e' di cartone", "cartone",
          c.get("/api/admin/onchain/chiave").json()["dove"])
    r = c.post("/api/admin/onchain/chiave")
    k = r.json()
    f = SRV._onchain_file_chiave()
    prova("«Crea la chiave»: sul VPS, tpub, impronta, non ancora nel backup",
          (200, "vps", True, 8, False),
          (r.status_code, k.get("dove"), k.get("xpub", "").startswith("tpub"),
           len(k.get("impronta", "")), k.get("nel_backup")))
    parole = json.load(open(f, encoding="utf-8"))["parole"]
    prova("...le dodici parole stanno nel file 0600, e nella risposta no",
          (12, "0o600", False),
          (len(parole.split()), oct(os.stat(f).st_mode & 0o777),
           parole.split()[0] in r.text and parole in r.text))
    prova("...si crea una volta sola: 409", 409,
          c.post("/api/admin/onchain/chiave").status_code)
    prova("...e la terza chiave nuova e' lei", k["xpub"],
          SRV.onchain_xpub_barattolo()[0])
    SRV.ONCHAIN_XPUB = conto(999)
    try:
        SRV.onchain_xpub_barattolo()
        due = False
    except ValueError:
        due = True
    SRV.ONCHAIN_XPUB = ""
    prova("...una ONCHAIN_XPUB diversa nel config: due terze chiavi, si ferma",
          True, due)
    fuori = os.path.join(os.path.dirname(os.path.abspath(SRV.DB)), "backup", "fuori")
    os.makedirs(fuori, exist_ok=True)
    with open(os.path.join(fuori, ".ultimo-successo"), "w") as h:
        h.write(str(int(time.time()) + 1))
    come(777)
    prova("...dopo un backup fuori sede riuscito, il pannello dice che c'e'",
          True, c.get("/api/admin/onchain/chiave").json()["nel_backup"])

    con = SRV.db()
    con.execute("UPDATE annunci SET stato='attivo', quantita=1 WHERE id=?",
                (annunci[4],))
    con.commit()
    con.close()
    oc5, ord5 = nuovo_pagato(annunci[4])
    o9 = ordine(999, oc5)
    prova("l'ordine nuovo ha la chiave del VPS come terza", k["xpub"],
          SRV.db().execute("SELECT i.xpub_barattolo FROM onchain_indirizzi i "
                           "JOIN onchain_ordini o ON o.indirizzo_id=i.id "
                           "WHERE o.id=?", (oc5,)).fetchone()[0])
    come(999)
    c.post(f"/api/orders/{ord5}/disputa")
    r = risolvi(777, ord5, "reso")
    prova("il reso on-chain fa la strada di sempre: return_pending", (200, "return_pending"),
          (r.status_code, stato_di(ord5)))
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='return_shipped' WHERE id=?", (ord5,))
    con.commit()
    con.close()
    banco.DETTO.clear()
    come(888)
    r = c.post(f"/api/orders/{ord5}/reso-ricevuto")
    o9 = ordine(999, oc5)
    prova("chi vende riceve il reso: Barattolo (dal VPS) firma il rimborso",
          (200, True, "compratore", "reso", True, [999]),
          (r.status_code, r.json().get("onchain"), o9["proposta"]["verso"],
           o9["proposta"]["barattolo"], firmata_da_barattolo(o9),
           [chi for chi, _ in banco.DETTO]))
    r = firma(999, oc5, cofirma(999, o9))
    prova("...chi compra co-firma: refunded", (200, "refunded"),
          (r.status_code, stato_di(ord5)))
    os.remove(f)

    # ---- 6) annullare, scadere ---------------------------------------------
    print("\n[annullare prima di pagare, e la scadenza]")
    con = SRV.db()
    con.execute("UPDATE annunci SET stato='attivo', quantita=1 WHERE id=?",
                (annunci[3],))
    con.commit()
    con.close()
    o = compra(999, annunci[3], metodo="onchain").json()["onchain"]
    come(888)
    prova("annulla solo chi compra: 403", 403,
          c.post(f"/api/onchain/ordini/{o['id']}/annulla").status_code)
    come(999)
    prova("chi compra annulla: 200, e lo stock torna libero", (200, 200),
          (c.post(f"/api/onchain/ordini/{o['id']}/annulla").status_code,
           compra(777, annunci[3]).status_code))
    con = SRV.db()
    con.execute("UPDATE ordini SET stato='annullato' WHERE annuncio_id=?",
                (annunci[3],))
    con.commit()
    con.close()
    o = compra(999, annunci[3], metodo="onchain").json()["onchain"]
    con = SRV.db()
    con.execute("UPDATE onchain_ordini SET scade=? WHERE id=?",
                (int(time.time()) - 1, o["id"]))
    con.commit()
    con.close()
    prova("scaduto senza un sats: scaduto", "scaduto",
          controlla(999, o["id"]).json()["stato"])

    # ---- 7) la leva ---------------------------------------------------------
    SRV.ONCHAIN_ATTIVO = False
    come(999)
    prova("leva spenta: le porte nuove dicono 404, la cassa 400",
          [404, 404, 404, 400],
          [c.get("/api/onchain/ordini").status_code,
           c.get("/api/onchain/pronto/888").status_code,
           c.post(f"/api/onchain/ordini/{oid}/controlla").status_code,
           compra(999, annunci[3], metodo="onchain").status_code])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
