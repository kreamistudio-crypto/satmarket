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
    for n in range(4):
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
    con.close()
    prova("...lo stock e' sceso e l'annuncio e' venduto", (0, "venduto"),
          (a["quantita"], a["stato"]))
    prova("...e lo sanno tutti e due", [888, 999],
          sorted(chi for chi, t in banco.DETTO if "⛓️" in t))
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
    indietro = [(o8["rimborso"], o8["importo_sats"] - 400)]
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
