# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL PAYJOIN (16 nov 2026, cantiere payjoin, Andrea: «potremo
davvero sfruttarlo come PayJoin, però metterei una fee di 1k sats») — il
giro col SERVER VERO, per HTTP (TestClient, la app vera): la quota fissa
di un ordine rilasciato diventa una moneta di Barattolo, il link di
pagamento del prossimo ordine porta `pj=`, il wallet di chi compra manda
l'originale alla porta, il server ci aggiunge la sua moneta e firma, il
wallet rifirma e la transazione finale ha tutte le firme buone. Poi i no
(originale diverso, ingressi gia' visti, monete spese, gettone ignoto,
leva spenta), l'originale trasmessa da Barattolo quando il PayJoin non
arriva, la moneta che si libera di nuovo, e il resto di un PayJoin
andato in rete che diventa la moneta dopo.

IL WALLET QUI E' EMBIT, come nei collaudi dell'on-chain: i semi sono i
vettori del BIP-39, le firme si fanno con embit. MEMPOOL E' DI CARTONE:
monete degli indirizzi, transazioni, spese e trasmissione sono funzioni
sostituite. Nessuna rete, nessun sats.

USO:  python collaudo_payjoin.py
"""
import asyncio
import base64
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  IL PAYJOIN DEGLI ACQUISTI ON-CHAIN — il giro vero")
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
            888: vett["bip39_english"][1]["parole"],
            "wallet": vett["bip39_english"][2]["parole"]}

    def radice(tg):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=N["xprv"])

    def conto(tg):
        return radice(tg).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=N["xpub"])

    def chiave_wallet(i):
        return radice("wallet").derive(f"m/84h/1h/0h/0/{i}").key

    def dal_wallet(i):
        return script.p2wpkh(chiave_wallet(i).get_public_key()).address(N)

    def firma_dest(tg, tipo, valore):
        import hashlib
        msg = SRV.onchain_messaggio_destinazione(tipo, valore)
        der = radice(tg).derive("m/48h/1h/0h/2h/2/0").key.sign(
            hashlib.sha256(msg).digest()).serialize()
        lr = der[3]
        r, s_ = der[4:4 + lr], der[6 + lr:]
        return (r[-32:].rjust(32, b"\0") + s_[-32:].rjust(32, b"\0")).hex()

    # --- mempool di cartone ------------------------------------------
    MONETE, TX, SPESE, INVIATE = {}, {}, set(), []

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0

    async def scheda_vuota(indirizzo):
        return {"chain_stats": {"tx_count": 0}, "mempool_stats": {"tx_count": 0}}

    async def invia_finta(tx_hex):
        t = Transaction.from_string(tx_hex)
        txid = t.txid().hex()
        if any(f"{i.txid.hex()}:{i.vout}" in SPESE for i in t.vin):
            raise ValueError("bad-txns-inputs-missingorspent")
        INVIATE.append(tx_hex)
        TX[txid] = [{"value": o.value, "scriptpubkey": o.script_pubkey.data.hex()}
                    for o in t.vout]
        return txid

    async def moneta_finta(txid, vout):
        if txid not in TX or not 0 <= vout < len(TX[txid]):
            return {"c_e": False, "speso": False, "sats": 0, "script": ""}
        u = TX[txid][vout]
        return {"c_e": True, "speso": f"{txid}:{vout}" in SPESE,
                "sats": u["value"], "script": u["scriptpubkey"]}

    async def tx_finta(txid):
        return txid in TX

    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta
    SRV.onchain_mempool_indirizzo = scheda_vuota
    SRV.onchain_mempool_invia = invia_finta
    SRV.onchain_mempool_moneta = moneta_finta
    SRV.onchain_mempool_tx_c_e = tx_finta

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    annunci = []
    for n in range(8):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(888,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Cosa PayJoin {n}",))
        annunci.append(cur.lastrowid)
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888]
    SRV.ONCHAIN_ATTIVO = True
    # la fee di Andrea: 1.000 sats di quota fissa a ogni ordine on-chain
    SRV.ONCHAIN_QUOTA_FISSA_SATS = 1000

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def compra(aid):
        come(999)
        r = c.post("/api/orders", json={"annuncio_id": aid,
                                        "consegna": "ritiro",
                                        "metodo": "onchain"})
        return r.json()["onchain"]

    def ordine(tg, oid):
        come(tg)
        return next(o for o in c.get("/api/onchain/ordini").json()["ordini"]
                    if o["id"] == oid)

    def ronda():
        asyncio.run(SRV._payjoin_ronda())

    def sql(q, *a):
        con = SRV.db()
        try:
            r = con.execute(q, a).fetchall()
            con.commit()
            return r
        finally:
            con.close()

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    come(888)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": dal_wallet(40),
        "firma": firma_dest(888, "indirizzo", dal_wallet(40))})
    come(999)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": dal_wallet(50),
        "firma": firma_dest(999, "indirizzo", dal_wallet(50))})

    # ---- 1) la quota diventa una moneta di Barattolo ---------------------
    print("\n[la quota fissa: da un ordine rilasciato a una moneta di Barattolo]")
    a = compra(annunci[0])
    prova("l'ordine on-chain porta la quota di 1.000 sats, sul conto di chi "
          "compra: 50.000 + 1.000 + 1.080 di margine", (1000, 52080),
          (a["quota_sats"], a["importo_sats"]))
    prova("...ma nessuna moneta di Barattolo c'e' ancora: il link e' quello "
          "di ieri, senza pj=", "", a["payjoin"])
    # il rilascio con la quota (il giro vero delle firme sta in
    # collaudo_onchain_ordine): qui la riga e la moneta in catena
    sql("UPDATE onchain_ordini SET stato='rilasciato', txid_uscita=? "
        "WHERE id=?", "aa" * 32, a["id"])
    MONETE[a["quota_indirizzo"]] = [{"txid": "ab" * 32, "vout": 1,
                                     "value": 1000,
                                     "status": {"confirmed": True}}]
    TX["ab" * 32] = [{"value": 1, "scriptpubkey": ""},
                     {"value": 1000, "scriptpubkey": script.address_to_scriptpubkey(
                         a["quota_indirizzo"]).data.hex()}]
    ronda()
    m = sql("SELECT * FROM payjoin_monete")
    prova("la ronda la trova: una moneta viva da 1.000 sats, sulla catena "
          "delle quote (/1/n)", [("viva", 1000, 1, a["quota_indirizzo"])],
          [(x["stato"], x["sats"], x["catena"], x["indirizzo"]) for x in m])
    prova("...e il pannello delle leve lo dice", True,
          "monete pronte: 1" in SRV._payjoin_a_parole())

    # ---- 2) il PayJoin ------------------------------------------------------
    print("\n[il PayJoin: il link, l'originale, la proposta, la firma]")
    b = compra(annunci[1])
    gettone = b["payjoin"].rsplit("/", 1)[-1]
    prova("il prossimo ordine porta la porta del PayJoin, sul dominio "
          "pubblico, con un gettone a caso", (True, True),
          (b["payjoin"].startswith("https://barattolo.store/api/payjoin/"),
           len(gettone) >= 20))
    prova("...chi vende non la vede", "", ordine(888, b["id"])["payjoin"])

    escrow = script.address_to_scriptpubkey(b["indirizzo"]["indirizzo"])

    def moneta_wallet(i, sats=200_000):
        txid = f"{0xc0 + i:02x}" * 32
        TX[txid] = [{"value": sats, "scriptpubkey": script.p2wpkh(
            chiave_wallet(i).get_public_key()).data.hex()}]
        return txid

    def originale(i, verso=escrow, importo=None, resto=0):
        """L'originale come lo fa un wallet: la sua moneta, l'ordine, il
        resto al wallet, 2 sat/vB, firmato e finalizzato."""
        txid = moneta_wallet(i)
        u = TransactionOutput(200_000, script.p2wpkh(chiave_wallet(i).get_public_key()))
        imp = b["importo_sats"] if importo is None else importo
        tx = Transaction(vin=[TransactionInput(bytes.fromhex(txid), 0,
                                               sequence=0xFFFFFFFD)],
                         vout=[TransactionOutput(imp, verso),
                               TransactionOutput(200_000 - imp - 320 - resto,
                                                 script.address_to_scriptpubkey(dal_wallet(90 + i)))])
        p = PSBT(tx)
        p.inputs[0].witness_utxo = u
        p.sign_with(chiave_wallet(i))
        w = finalize_psbt(p).vin[0].witness
        q = PSBT(tx)
        q.inputs[0].witness_utxo = u
        q.inputs[0].final_scriptwitness = w
        return q

    def bussa(g, q, query="?v=1&additionalfeeoutputindex=1&maxadditionalfeecontribution=300"):
        return c.post(f"/api/payjoin/{g}{query}", content=q.to_string(),
                      headers={"Content-Type": "text/plain"})

    q = originale(1)
    r = bussa(gettone, q)
    prova("la porta risponde 200, testo, col CORS aperto", (200, True, "*"),
          (r.status_code, r.headers["content-type"].startswith("text/plain"),
           r.headers.get("access-control-allow-origin")))
    pr = PSBT.from_string(r.text)
    uscite = {o.script_pubkey.data: o.value for o in pr.tx.vout}
    ingressi = sorted(f"{i.txid.hex()}:{i.vout}" for i in pr.inputs)
    prova("la proposta: due ingressi (quello del wallet e la moneta di "
          "Barattolo), l'ordine riceve ESATTAMENTE il suo importo",
          (sorted([f"{'c1' * 32}:0", f"{'ab' * 32}:1"]), b["importo_sats"], 3),
          (ingressi, uscite[escrow.data], len(pr.tx.vout)))
    t = sql("SELECT * FROM payjoin_tentativi")[0]
    prova("...il tentativo e' scritto, coi suoi conti: Barattolo mette poco "
          "di tasca sua", (b["id"], "proposta", True),
          (t["onchain_id"], t["esito"], 0 <= t["spesa_sats"] <= 500))
    # il wallet rifirma il suo ingresso e trasmette
    for inp in pr.inputs:
        if inp.final_scriptwitness is None:
            inp.witness_utxo = q.inputs[0].witness_utxo
    pr.sign_with(chiave_wallet(1))
    for inp in pr.inputs:
        if inp.partial_sigs:
            pub, sig = list(inp.partial_sigs.items())[0]
            inp.final_scriptwitness = script.Witness([sig, pub.sec()])
            inp.partial_sigs.clear()
    fin = SRV.payjoin_leggi_originale(pr.to_string(), escrow.data, b["importo_sats"])
    prova("rifirmata dal wallet, la transazione finale ha tutte le firme "
          "buone (anche quella di Barattolo), ed e' quella del tentativo",
          (2, t["proposta_txid"]), (len(fin["punti"]), fin["txid"]))

    r2 = bussa(gettone, q)
    prova("lo stesso originale rimandato riprende la STESSA proposta (BIP78)",
          (200, r.text), (r2.status_code, r2.text))
    r3 = bussa(gettone, originale(1, resto=7))
    prova("un originale diverso per lo stesso ordine: no, col codice del BIP "
          "e la sua frase (mai il nostro perche')",
          (400, "original-psbt-rejected",
           SRV.PAYJOIN_ERRORI["original-psbt-rejected"]),
          (r3.status_code, r3.json()["errorCode"], r3.json()["message"]))
    prova("...e il link di questo ordine non porta piu' pj=", "",
          ordine(999, b["id"])["payjoin"])

    # ---- 3) i no -------------------------------------------------------------
    print("\n[i no della porta]")
    d = compra(annunci[2])
    prova("la moneta e' impegnata nel tentativo aperto: il prossimo ordine "
          "non porta pj=", "", d["payjoin"])
    prova("gettone ignoto o storto (corto, o con punti): 503 unavailable",
          [503, 503, 503],
          [bussa("x" * 24, q).status_code, bussa("corto", q).status_code,
           bussa("a.b.c.d.e.f.g.h.i.j", q).status_code])
    prova("il permesso del browser (OPTIONS) col CORS aperto", (204, "*"),
          (c.options(f"/api/payjoin/{gettone}").status_code,
           c.options(f"/api/payjoin/{gettone}").headers.get(
               "access-control-allow-origin")))
    prova("v=2: version-unsupported, con le versioni che sappiamo",
          (400, "version-unsupported", [1]),
          (bussa(gettone, q, "?v=2").status_code,
           bussa(gettone, q, "?v=2").json()["errorCode"],
           bussa(gettone, q, "?v=2").json()["supported"]))

    # ---- 4) l'originale trasmessa da Barattolo -----------------------------
    print("\n[il PayJoin non arriva: l'originale la trasmette Barattolo]")
    ronda()
    prova("prima dei tre minuti la ronda non trasmette niente", ([], "proposta"),
          (INVIATE, sql("SELECT esito FROM payjoin_tentativi")[0]["esito"]))
    sql("UPDATE payjoin_tentativi SET creato=creato-200")
    ronda()
    t = sql("SELECT * FROM payjoin_tentativi")[0]
    prova("dopo tre minuti, senza PayJoin in rete: l'originale va in rete "
          "da qui, il tentativo si chiude 'originale'",
          ([SRV.payjoin_leggi_originale(q.to_string(), escrow.data,
                                        b["importo_sats"])["hex"]], "originale"),
          (INVIATE, t["esito"]))
    prova("...il resto di quel PayJoin non nascera' ('mai')", "mai",
          sql("SELECT stato FROM payjoin_monete WHERE catena=3")[0]["stato"])
    d = ordine(999, d["id"])
    prova("...e la moneta di Barattolo e' di nuovo libera: l'ordine aperto "
          "riporta pj=", True, d["payjoin"].startswith("https://"))

    # ---- 5) il PayJoin che va in rete --------------------------------------
    print("\n[il PayJoin che va in rete, e il suo resto]")
    g2 = d["payjoin"].rsplit("/", 1)[-1]
    escrow_d = script.address_to_scriptpubkey(d["indirizzo"]["indirizzo"])
    rifatto = originale(1, verso=escrow_d, importo=d["importo_sats"])
    prova("ingressi gia' visti in un altro originale: no", (400, "original-psbt-rejected"),
          (lambda x: (x.status_code, x.json()["errorCode"]))(bussa(g2, rifatto)))
    speso = originale(2, verso=escrow_d, importo=d["importo_sats"])
    SPESE.add(f"{'c2' * 32}:0")
    prova("una moneta del wallet gia' spesa (l'originale non andrebbe in "
          "rete): no", 400, bussa(g2, speso).status_code)
    # i no prima della proposta non scrivono niente: il tentativo resta
    q3 = originale(3, verso=escrow_d, importo=d["importo_sats"])
    r = bussa(g2, q3)
    prova("un originale buono, con la stessa moneta di Barattolo tornata "
          "libera: 200", 200, r.status_code)
    t3 = sql("SELECT * FROM payjoin_tentativi WHERE onchain_id=?", d["id"])[0]
    # il wallet lo trasmette: in rete c'e' il PayJoin
    TX[t3["proposta_txid"]] = [{"value": 1, "scriptpubkey": ""}]
    SPESE.add(f"{'ab' * 32}:1")
    sql("UPDATE payjoin_tentativi SET creato=creato-200 WHERE id=?", t3["id"])
    ronda()
    prova("la ronda vede il PayJoin in rete: tentativo 'payjoin', la moneta "
          "di Barattolo spesa", ("payjoin", "spesa"),
          (sql("SELECT esito FROM payjoin_tentativi WHERE id=?", t3["id"])[0]["esito"],
           sql("SELECT stato FROM payjoin_monete WHERE catena=1")[0]["stato"]))
    resto = sql("SELECT * FROM payjoin_monete WHERE catena=3 AND stato='attesa'")[0]
    prova("...nessuna moneta pronta: il prossimo ordine non porta pj=", "",
          compra(annunci[3])["payjoin"])
    MONETE[resto["indirizzo"]] = [{"txid": t3["proposta_txid"], "vout": 2,
                                   "value": 950, "status": {"confirmed": True}}]
    sql("UPDATE payjoin_monete SET controllata_il=0")
    ronda()
    prova("confermato il PayJoin, il suo resto (/3/n) e' la moneta di "
          "Barattolo dopo", ("viva", 950, 1),
          (lambda x: (x["stato"], x["sats"], x["indice"]))(
              sql("SELECT * FROM payjoin_monete WHERE catena=3 AND "
                  "stato='viva'")[0]) if sql(
              "SELECT * FROM payjoin_monete WHERE catena=3 AND stato='viva'")
          else None)
    # la chiave che il server usera' per quel resto e' davvero sua
    conto_b = SRV._onchain_privata_barattolo(SRV.onchain_xpub_barattolo()[0])
    prova("...e la chiave di Barattolo rifa' quell'indirizzo (la prossima "
          "firma sara' buona)", resto["indirizzo"],
          script.p2wpkh(conto_b.derive([3, resto["indice"]]).key
                        .get_public_key()).address(N))
    # la sorveglianza dell'ordine non sa niente del PayJoin: vede la cifra
    MONETE[d["indirizzo"]["indirizzo"]] = [{"txid": t3["proposta_txid"], "vout": 0,
                                            "value": d["importo_sats"],
                                            "status": {"confirmed": True}}]
    come(999)
    prova("l'ordine pagato col PayJoin e' pagato come sempre", "pagato",
          c.post(f"/api/onchain/ordini/{d['id']}/controlla").json()["stato"])

    # ---- 6) la leva ------------------------------------------------------------
    print("\n[la leva d'emergenza]")
    e = compra(annunci[4])
    prova("con la moneta di nuovo pronta, il link porta pj=", True,
          e["payjoin"].startswith("https://"))
    # la moneta pronta la spende un'altra transazione, e la ronda non l'ha
    # ancora vista: la porta la rilegge in rete prima di offrirla
    viva = sql("SELECT * FROM payjoin_monete WHERE stato='viva'")[0]
    TX[viva["txid"]] = [{"value": 1, "scriptpubkey": ""}] * 2 + [
        {"value": int(viva["sats"]), "scriptpubkey": ""}]
    SPESE.add(f"{viva['txid']}:{viva['vout']}")
    r = bussa(e["payjoin"].rsplit("/", 1)[-1],
              originale(5, verso=script.address_to_scriptpubkey(
                  e["indirizzo"]["indirizzo"]), importo=e["importo_sats"]))
    prova("una moneta di Barattolo spesa da poco, che la ronda non ha ancora "
          "visto: riletta in rete prima di offrirla, unavailable e la moneta "
          "'spesa'", (503, "unavailable", "spesa", 0),
          (r.status_code, r.json()["errorCode"],
           sql("SELECT stato FROM payjoin_monete WHERE indirizzo=?",
               viva["indirizzo"])[0]["stato"],
           len(sql("SELECT * FROM payjoin_tentativi WHERE onchain_id=?", e["id"]))))
    SRV.PAYJOIN_ATTIVO = False
    prova("leva spenta: il link e' quello di ieri, e la porta dice "
          "unavailable", ("", 503),
          (ordine(999, e["id"])["payjoin"],
           bussa(e["payjoin"].rsplit("/", 1)[-1],
                 originale(4, verso=script.address_to_scriptpubkey(
                     e["indirizzo"]["indirizzo"]),
                     importo=e["importo_sats"])).status_code))
    SRV.PAYJOIN_ATTIVO = True

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
