# -*- coding: utf-8 -*-
"""
BARATTOZON ANCHE ON-CHAIN (17 nov 2026, cantiere barattozon-onchain,
Andrea: «Sì, mettiamolo in chain anche. Tanto un ordine che scade, per
esempio, il giorno dopo, non vedo dove sia il problema») — il giro col
SERVER VERO, per HTTP: il PayCode pubblicato nel libro on-chain coi suoi
rifiuti (meno di 12 ore, in compra, a leva spenta), la vita nel libro 8
ore prima della scadenza, niente ripubblica ne' paracadute ne' recapito,
il libro e il moderatore che non vedono il codice, chi prende che lo vede
SOLO col deposito confermato, gli avvisi senza il codice dentro, «Ho
pagato al tabacchino», e la presa chiusa quando il libro e' scaduto. La
stessa gabbia di collaudo_p2p_onchain (embit come telefono, mempool di
cartone, relay muti).

USO:  python collaudo_p2p_onchain_barattozon.py
"""
import asyncio
import hashlib
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova


def nuova_chiave() -> bytes:
    """Una chiave usa-e-getta, 32 byte nella misura del BIP-340."""
    while True:
        sk = os.urandom(32)
        if 1 <= int.from_bytes(sk, "big") < schnorr_puro.N:
            return sk


class ChiaveDiCalco:
    """La chiave della piattaforma dove coincurve non c'e' (il calco di
    collaudo_annunci_sul_profilo): `secret` e `sign_schnorr`."""

    def __init__(self, sk: bytes):
        self.secret = sk

    def sign_schnorr(self, msg: bytes) -> bytes:
        return schnorr_puro.firma(self.secret, msg, os.urandom(32))


def main():
    print("=" * 58)
    print("  BARATTOZON ANCHE ON-CHAIN — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    # i BOTTONI sotto gli avvisi (30 ott 2026): il banco tiene solo il
    # testo, e qui serve anche il bottone «🟠 Apri lo scambio»
    BOTTONI = []
    _notifica_del_banco = SRV.notifica

    async def notifica_coi_bottoni(chi, testo, bottone=None, *a, **k):
        BOTTONI.append((chi, testo, bottone))
        return await _notifica_del_banco(chi, testo, bottone, *a, **k)
    SRV.notifica = notifica_coi_bottoni
    from embit import bip32, bip39, script
    from embit.ec import PublicKey
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

    def rimborso_mio(tg, n):
        k = radice(tg).derive(f"m/48h/1h/0h/2h/1/{n}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    vpub = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi["wallet"]),
                                 version=b"\x04\x5f\x18\xbc").derive(
        "m/84h/1h/0h").to_public().to_base58()

    def dal_wallet(i):
        k = radice("wallet").derive(f"m/84h/1h/0h/0/{i}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    def firma_dest(tg, tipo, valore):
        msg = SRV.onchain_messaggio_destinazione(tipo, valore)
        der = radice(tg).derive("m/48h/1h/0h/2h/2/0").key.sign(
            hashlib.sha256(msg).digest()).serialize()
        lr = der[3]
        r, s_ = der[4:4 + lr], der[6 + lr:]
        return (r[-32:].rjust(32, b"\0") + s_[-32:].rjust(32, b"\0")).hex()

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
    # (3 nov 2026) la chiave di conto si legge sulla rete fino al primo
    # indirizzo mai usato: qui nessuno e' usato, e nessuna rete vera
    async def scheda_vuota(indirizzo):
        return {"chain_stats": {"tx_count": 0}, "mempool_stats": {"tx_count": 0}}
    SRV.onchain_mempool_indirizzo = scheda_vuota
    SRV.onchain_mempool_invia = invia_finta

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan"), (777, "Terzo"),
                     (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888, 777]
    SRV.ONCHAIN_ATTIVO = True
    SRV.P2P_ATTIVO = True
    # (16 nov 2026, p2p-onchain-commissione) la commissione del P2P
    # on-chain e' quella del 38385: qui ZERO, il giro di prima di
    # quel cantiere; la commissione vera la prova
    # collaudo_p2p_onchain_commissione
    SRV._P2P_INFO["fee"] = 0.0
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.P2P_PROVA_IDS = []
    SRV.P2P_MAX_EURO = 250
    # il giro pubblica e prende piu' volte di quanto un freno orario
    # conceda a una persona: qui i freni si allargano (il collaudo degli
    # avvisi fa lo stesso con «annunci»); che esistano lo dice prove.py
    for nome in ("p2p_onchain_pubblica", "p2p_onchain_prendi", "onchain_firma",
                 "onchain_controlla", "p2p_onchain_controlla"):
        SRV.FRENI[nome] = (1000, 3600)
    # la chiave della piattaforma, di prova: cosi' il 38383 esce firmato
    # anche nella gabbia (i relay restano muti per costruzione)
    sk_noi = nuova_chiave()
    SRV._NOSTR = ((SRV.ChiavePrivataNostr(sk_noi) if SRV.ChiavePrivataNostr
                   is not None else ChiaveDiCalco(sk_noi)),
                  schnorr_puro.pubblica(sk_noi).hex())

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def pubblica(tg, **d):
        come(tg)
        base = {"lato": "sell", "sats": 100000, "euro_cent": 9000,
                "metodi": ["Bonifico", "Revolut"], "recapito": "IT00 X 1234"}
        return c.post("/api/p2p/onchain/pubblica", json={**base, **d})

    def uno(tg, oid):
        come(tg)
        return c.get(f"/api/p2p/onchain/{oid}").json()

    def gesto(tg, oid, cosa, **d):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/{cosa}", json=d)

    def libro(tg=0):
        # il libro riconosce chi guarda da solo (`_chi_guarda_p2p` legge
        # l'initData): nella gabbia glielo si dice, come fa il collaudo
        # dei volti
        SRV._chi_guarda_p2p = lambda *a, **k: int(tg)
        return c.get("/api/p2p/libro").json()

    def paga(o, confermata=True, quanto=None):
        MONETE[o["indirizzo"]["indirizzo"]] = [{
            "txid": f"{o['id']:02x}" * 32, "vout": 0,
            "value": o["importo_sats"] if quanto is None else quanto,
            "status": {"confirmed": confermata}}]

    def psbt_di(o, uscite, firma=None):
        ch = o["indirizzo"]["chiavi"]
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
            n = o["indirizzo"]["mio_numero"]
            p.sign_with(radice(firma).derive(f"m/48h/1h/0h/2h/0/{n}").key)
        return p

    def cofirma(tg, o):
        p = PSBT.from_string(o["proposta"]["psbt"])
        p.sign_with(radice(tg).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        return finalize_psbt(p).serialize().hex()

    def tx_nuda(o):
        """La transazione della proposta SENZA firme: leggibile, stesso
        txid, ma e' il server a dover dire di no prima di guardarla."""
        return PSBT.from_string(o["proposta"]["psbt"]).tx.serialize().hex()

    def detto_a(tg, pezzo):
        return any(pezzo in t for chi, t in banco.DETTO if chi == tg)


    SRV.P2P_ONCHAIN_ATTIVO = True
    SRV.ONCHAIN_ATTIVO = True
    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    RIMBORSO_999 = dal_wallet(50)
    come(999)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": RIMBORSO_999,
        "firma": firma_dest(999, "indirizzo", RIMBORSO_999)})
    come(888)
    c.post("/api/onchain/incasso", json={
        "tipo": "xpub", "valore": vpub, "firma": firma_dest(888, "xpub", vpub)})
    SRV._P2P_INFO["fee"] = 0.0
    PC, N = "212802988", "0100860003622209216085740002128029880"

    def bz(tg=999, **d):
        adesso = int(time.time())
        base = {"lato": "sell", "sats": 50000, "euro_cent": 3999,
                "metodi": ["Contanti al tabacchino 39.99"], "recapito": "IT00 X 1234",
                "paracadute": 10,
                "tabacchino": {"paycode": "212-802-988", "scade": adesso + 24 * 3600,
                               "barre": N}}
        base.update(d)
        return pubblica(tg, **base)

    def nessun_codice(testo):
        return PC not in testo and "212-802-988" not in testo

    # ---- 1) i rifiuti ------------------------------------------------------
    print("\n[i rifiuti della pubblicazione]")
    adesso = int(time.time())
    r_corto = bz(tabacchino={"paycode": PC, "scade": adesso + 6 * 3600, "barre": ""})
    r_compra = bz(lato="buy")
    r_due = bz(metodi=["Contanti al tabacchino 39.99", "Revolut"])
    SRV.P2P_ONCHAIN_BARATTOZON = False
    r_spenta = bz()
    SRV.P2P_ONCHAIN_BARATTOZON = True
    # (17 nov 2026 sera) in compra Barattozon on-chain c'e', ma solo a mercato
    prova("meno di 12 ore, in compra a prezzo fisso, con un altro metodo, a leva spenta: 400 coi perche'",
          [(400, True), (400, True), 400, (400, True)],
          [(r_corto.status_code, "12 ore" in r_corto.json()["detail"]),
           (r_compra.status_code, "mercato" in r_compra.json()["detail"]),
           r_due.status_code,
           (r_spenta.status_code, "Lightning" in r_spenta.json()["detail"])])
    prova("...e il libro non ha preso niente", [], libro(888).get("onchain", {}).get("eventi", []))

    # ---- 2) la pubblicazione -------------------------------------------------
    print("\n[la pubblicazione]")
    adesso = int(time.time())
    scade_pc = adesso + 24 * 3600
    r = bz(tabacchino={"paycode": "212 802 988", "scade": scade_pc, "barre": N})
    prova("un PayCode che scade domani: 200", 200, r.status_code)
    oid = r.json()["id"]
    con = SRV.db()
    riga = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    prova("nel libro fino a 8 ore prima del PayCode; niente recapito, paracadute, ripubblica; "
          "il PayCode nella colonna sua",
          [scade_pc - 8 * 3600, "", 0, 0, {"pc": PC, "scade": scade_pc, "barre": N}],
          [int(riga["scade"]), riga["recapito"], int(riga["paracadute"]),
           int(riga["rip_massimo"]), json.loads(riga["paycode"])])
    prova("...e l'evento 38383 che va su Nostr non porta il codice", True,
          nessun_codice(json.dumps(SRV.p2p_onchain_tags(riga, adesso))))
    lib = libro(888)
    ev = [e for e in lib["onchain"]["eventi"] if int(e["id"]) == oid]
    prova("il libro lo mostra, col metodo e la leva, ma il PayCode no",
          [1, ["Contanti al tabacchino 39.99"], True, True],
          [len(ev), ev[0]["metodi"] if ev else None, lib["onchain"].get("barattozon"),
           nessun_codice(json.dumps(lib))])
    o999 = uno(999, oid)
    prova("chi l'ha pubblicato rivede il suo PayCode e il codice a barre",
          {"scade": scade_pc, "paycode": PC, "barre": N}, o999.get("tabacchino"))

    # ---- 3) la presa: il codice non c'e' ancora --------------------------------
    print("\n[la presa: prima del deposito il codice non si vede]")
    banco.DETTO.clear()
    r = gesto(888, oid, "prendi")
    prova("Alan prende: 200", 200, r.status_code)
    o888 = uno(888, oid)
    o777 = uno(777, oid)
    prova("chi prende vede la scadenza ma non il codice; il moderatore lo stesso",
          [{"scade": scade_pc}, {"scade": scade_pc}, True, True],
          [o888.get("tabacchino"), o777.get("tabacchino"),
           nessun_codice(json.dumps(o888)), nessun_codice(json.dumps(o777))])
    r = gesto(999, oid, "recapito", recapito="IT00 Y")
    prova("il recapito di un Barattozon non si scrive: 409", 409, r.status_code)

    # ---- 4) il deposito confermato: adesso si' ---------------------------------
    print("\n[il deposito confermato: il PayCode arriva a chi paga]")
    oa = uno(999, oid)
    paga(oa)
    banco.DETTO.clear()
    prova("deposito confermato", "depositato", gesto(999, oid, "controlla").json()["stato"])
    o888 = uno(888, oid)
    prova("ora chi prende vede PayCode e codice a barre, e il tempo per pagare finisce col PayCode",
          [PC, N, scade_pc],
          [(o888.get("tabacchino") or {}).get("paycode"), (o888.get("tabacchino") or {}).get("barre"),
           o888.get("paga_entro")])
    prova("...il moderatore continua a non vederlo", True, nessun_codice(json.dumps(uno(777, oid))))
    prova("gli avvisi: a chi paga «il PayCode è nello scambio» e il tabacchino, a chi vende Amazon; "
          "in nessun avviso il codice",
          [True, True, True],
          [detto_a(888, "Il <b>PayCode</b> adesso è nello scambio") and detto_a(888, "tabacchino"),
           detto_a(999, "su Amazon l'ordine risulta <b>pagato</b>"),
           all(nessun_codice(t) for _, t in banco.DETTO)])

    # ---- 5) «Ho pagato al tabacchino» -----------------------------------------
    print("\n[«Ho pagato al tabacchino»]")
    banco.DETTO.clear()
    r = gesto(888, oid, "euro-inviati")
    prova("il gesto e' quello di sempre, e a chi vende si dice di guardare Amazon",
          [200, "euro_inviati", True, True],
          [r.status_code, uno(999, oid)["stato"],
           detto_a(999, "aver pagato il PayCode al tabacchino"),
           all(nessun_codice(t) for _, t in banco.DETTO)])

    # ---- 6) il libro scaduto chiude la presa -------------------------------------
    print("\n[un PayCode vicino alla scadenza non si prende piu']")
    adesso = int(time.time())
    oid2 = bz(tabacchino={"paycode": PC, "scade": adesso + 13 * 3600, "barre": ""}).json()["id"]
    con = SRV.db()
    scade2 = int(con.execute("SELECT scade FROM p2p_onchain_ordini WHERE id=?", (oid2,)).fetchone()[0])
    con.execute("UPDATE p2p_onchain_ordini SET scade=? WHERE id=?", (adesso - 1, oid2))
    con.commit()
    con.close()
    r = gesto(888, oid2, "prendi")
    prova("13 ore di PayCode: 5 nel libro; passate quelle, la presa dice di no",
          [adesso + 5 * 3600, 409], [scade2, r.status_code])

    # ---- 7) Barattozon in «Compra BTC» (17 nov 2026 sera) ---------------------
    print("\n[Barattozon in «Compra BTC»: la fascia, e il PayCode di chi prende]")
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    SRV._cambio_cache["valori"]["eur"] = 50000.0
    SRV._cambio_cache["quando"] = time.time()

    def compra(**d):
        base = {"lato": "buy", "tipo": "mercato", "premio": 0, "euro_min_cent": 2500,
                "euro_cent": 25000, "metodi": ["Contanti al tabacchino"], "recapito": "",
                "tabacchino": None}
        base.update(d)
        base.pop("sats", None)
        return pubblica(888, **base)

    r_fisso = compra(tipo="fisso", sats=50000)
    r_senza = compra(euro_min_cent=0)
    r_poco = compra(euro_min_cent=500)
    prova("in compra: a prezzo fisso, senza fascia, sotto il minimo di Barattozon: 400",
          [400, 400, 400], [r_fisso.status_code, r_senza.status_code, r_poco.status_code])
    r = compra()
    prova("la fascia da 25 a 250 € a mercato: 200", 200, r.status_code)
    oc = r.json()["id"]
    lib = libro(999)
    ev = [e for e in lib["onchain"]["eventi"] if int(e["id"]) == oc]
    con = SRV.db()
    rc = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?", (oc,)).fetchone()
    con.close()
    prova("nel libro la fascia (euro_min e euro), nel 38383 i due capi, niente PayCode nella colonna",
          [25.0, 250.0, ["fa", "25", "250"], ""],
          [ev[0].get("euro_min") if ev else None, ev[0].get("euro") if ev else None,
           [t for t in SRV.p2p_onchain_tags(rc) if t[0] == "fa"][0], rc["paycode"]])
    adesso = int(time.time())
    no_pc = gesto(999, oc, "prendi")
    no_fuori = gesto(999, oc, "prendi", tabacchino={"paycode": PC, "scade": adesso + 24 * 3600,
                                                   "barre": "", "euro_cent": 30000})
    no_presto = gesto(999, oc, "prendi", tabacchino={"paycode": PC, "scade": adesso + 7 * 3600,
                                                    "barre": "", "euro_cent": 4730})
    prova("chi prende senza PayCode, fuori dalla fascia, o con meno di 8 ore: 400 coi perche'",
          [400, (400, True), (400, True)],
          [no_pc.status_code, (no_fuori.status_code, "da 25 a 250" in no_fuori.json()["detail"]),
           (no_presto.status_code, "8 ore" in no_presto.json()["detail"])])
    scade_c = adesso + 20 * 3600
    banco.DETTO.clear()
    r = gesto(999, oc, "prendi", tabacchino={"paycode": "212-802-988", "scade": scade_c,
                                             "barre": N, "euro_cent": 4730})
    prova("col PayCode da 47,30 € e 20 ore: 200", 200, r.status_code)
    con = SRV.db()
    rc = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?", (oc,)).fetchone()
    con.close()
    # 47,30 € a 50.000 €/BTC = 94.600 sats
    prova("la riga: l'importo e' quello del PayCode, i sats contati su quello, il PayCode nella "
          "colonna, chi prende deposita e chi ha pubblicato riceve",
          [4730, 94600, {"pc": PC, "scade": scade_c, "barre": N}, 999, 888, ""],
          [int(rc["euro_cent"]), int(rc["prezzo_sats"]), json.loads(rc["paycode"]),
           int(rc["depositante_id"]), int(rc["ricevente_id"]), rc["recapito"]])
    prova("chi prende rivede il suo PayCode; chi paga (chi ha pubblicato) e il moderatore no, "
          "prima del deposito; l'avviso a chi paga dice il PayCode, non gli euro",
          [PC, {"scade": scade_c}, True, True],
          [(uno(999, oc).get("tabacchino") or {}).get("paycode"), uno(888, oc).get("tabacchino"),
           nessun_codice(json.dumps(uno(777, oc))),
           detto_a(888, "vedi il PayCode da pagare al tabacchino")])
    paga(uno(999, oc))
    prova("deposito confermato", "depositato", gesto(999, oc, "controlla").json()["stato"])
    o888 = uno(888, oc)
    prova("ora chi paga vede PayCode e codice a barre, e il tempo finisce col PayCode",
          [PC, N, scade_c],
          [(o888.get("tabacchino") or {}).get("paycode"), (o888.get("tabacchino") or {}).get("barre"),
           o888.get("paga_entro")])
    prova("...e il libro non ha piu' la fascia (euro_min) dello scambio preso",
          False, any(int(e["id"]) == oc for e in libro(999)["onchain"]["eventi"]))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
