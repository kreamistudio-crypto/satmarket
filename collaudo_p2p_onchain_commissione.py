# -*- coding: utf-8 -*-
"""
LA COMMISSIONE DEGLI SCAMBI P2P ON-CHAIN (16 nov 2026, cantiere
p2p-onchain-commissione, Andrea: «Deve essere uguale, come commissione
deve essere uguale a quella del lighting»; «nel mercatino rimane a zero la
commissione») — il giro col SERVER VERO, per HTTP, della commissione nel
2-di-3: la presa che senza fee del coordinatore non parte, le due meta' (lo
sconto del pioniere sulla sua), l'importo di chi deposita, l'incasso di
chi riceve, l'uscita verso Barattolo sulla sua xpub, il giudice dei PSBT
che dice i no, la seconda firma e la transazione uscita, il rimborso che
restituisce tutto, la disputa decisa con la firma di Barattolo, lo scambio
piccolo sotto la polvere senza commissione. La stessa gabbia di
collaudo_p2p_onchain (embit come telefono, mempool di cartone, relay muti).

USO:  python collaudo_p2p_onchain_commissione.py
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
    print("  LA COMMISSIONE DEL P2P ON-CHAIN — il giro vero")
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
    # Andrea e' pioniere: lo sconto fedelta' di mezzo punto sulla SUA meta'
    SRV.P2P_SCONTO_FEDELTA_PERCENTO = 0.5
    con = SRV.db()
    con.execute("UPDATE utenti SET coorte='pioniere' WHERE tg_id=999")
    con.commit()
    con.close()

    # ---- 1) senza la fee del coordinatore la presa non parte -------------
    print("\n[senza la fee del 38385 la presa non parte]")
    SRV._P2P_INFO["fee"] = None
    oid = pubblica(999).json()["id"]
    r = gesto(888, oid, "prendi")
    prova("fee non letta: 503 col perche', e l'ordine resta nel libro",
          (503, True, "pending"),
          (r.status_code, "commissione" in r.json()["detail"], uno(999, oid)["stato"]))

    # ---- 2) la presa: le due meta' ---------------------------------------
    print("\n[la presa: meta' a testa, lo sconto del pioniere sulla sua]")
    SRV._P2P_INFO["fee"] = 0.03
    banco.DETTO.clear()
    r = gesto(888, oid, "prendi")
    ob = r.json()
    oa = uno(999, oid)
    # Andrea (pioniere, deposita) 100.000 x (3% - 1%) / 2 = 1.000; Alan
    # (riceve) 100.000 x 3% / 2 = 1.500; margine 3 x 2 x 180 = 1.080
    prova("Alan prende: quota 2.500 a Barattolo, 1.500 la meta' di Alan, importo "
          "100.000 + 1.080 + 1.000", (200, 2500, 1500, 1080, 102080),
          (r.status_code, ob["quota_sats"], ob["quota_ricevente_sats"],
           ob["margine_sats"], ob["importo_sats"]))
    con = SRV.db()
    ind = con.execute("SELECT * FROM onchain_indirizzi WHERE id=?",
                      (oa["indirizzo"]["id"],)).fetchone()
    con.close()
    prova("...l'uscita di Barattolo e' il /1/n della SUA xpub, col numero di "
          "Barattolo dell'indirizzo, e i due la leggono uguale",
          (SRV.onchain_incasso(ind["xpub_barattolo"], ind["numero_barattolo"]),) * 2,
          (oa["quota_indirizzo"], ob["quota_indirizzo"]))
    prova("...l'avviso a chi deposita conta anche la sua meta'", True,
          detto_a(999, "102.080 sats</b> (prezzo + margine di rete + la tua metà della commissione)"))
    con = SRV.db()
    ricevente = SRV._onchain_incasso_sats(con.execute(
        "SELECT * FROM p2p_onchain_ordini WHERE id=?", (oid,)).fetchone())
    con.close()
    prova("il giudice dell'incasso: 100.000 - 1.500 = 98.500; una riga del "
          "mercatino (senza la colonna) il prezzo intero", (98500, 7000),
          (ricevente, SRV._onchain_incasso_sats({"prezzo_sats": 7000})))

    # ---- 3) il deposito e il rilascio -------------------------------------
    print("\n[il deposito e le due firme, con la commissione]")
    paga(oa, quanto=101080)
    prova("senza la meta' di chi deposita il deposito non basta: resta preso",
          "preso", gesto(999, oid, "controlla").json()["stato"])
    paga(oa)
    prova("con tutto l'importo: depositato", "depositato",
          gesto(999, oid, "controlla").json()["stato"])
    gesto(888, oid, "euro-inviati")
    o = uno(999, oid)
    rete = (11 + 105 + 31 * 3) * 2
    resto_ = 102080 - 98500 - 2500 - rete
    giusto = [(o["incasso"], 98500), (o["quota_indirizzo"], 2500), (o["rimborso"], resto_)]
    no = []
    for uscite in ([(o["incasso"], 100000), (o["rimborso"], 102080 - 100000 - 356)],
                   [(o["incasso"], 98500), (o["rimborso"], 102080 - 98500 - 356)],
                   [(o["incasso"], 98500), (o["quota_indirizzo"], 2000),
                    (o["rimborso"], 102080 - 98500 - 2000 - rete)]):
        r = gesto(999, oid, "proposta", verso="venditore",
                  psbt=psbt_di(o, uscite, 999).to_string())
        no.append((r.status_code, r.json().get("detail", "")[:30]))
    prova("il giudice dice i no: il prezzo intero a chi riceve, la quota che manca, "
          "la quota sbagliata", [400, 400, 400], [x[0] for x in no])
    banco.DETTO.clear()
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, giusto, 999).to_string())
    prova("la proposta giusta passa: 98.500 a chi riceve, 2.500 a Barattolo, il "
          "resto a chi ha depositato", (200, True), (r.status_code, detto_a(888, "seconda firma")))
    r = gesto(888, oid, "firma", tx=cofirma(888, uno(888, oid)))
    prova("la seconda firma di Alan: rilasciato", (200, "rilasciato", 1),
          (r.status_code, r.json()["stato"], len(INVIATE)))
    tx = Transaction.from_string(INVIATE[0])
    prova("...la transazione uscita paga 98.500 ad Alan, 2.500 a Barattolo e "
          "%d ad Andrea" % resto_,
          sorted([(o["incasso"], 98500), (o["quota_indirizzo"], 2500), (RIMBORSO_999, resto_)]),
          sorted((script.Script(v.script_pubkey.data).address(N), v.value) for v in tx.vout))

    # ---- 4) il rimborso: torna tutto, commissione compresa -----------------
    print("\n[la rinuncia: il rimborso restituisce anche la commissione]")
    INVIATE.clear()
    oid2 = pubblica(999, sats=50000, euro_cent=4500).json()["id"]
    gesto(888, oid2, "prendi")
    oa = uno(999, oid2)
    # 50.000 x 2% / 2 = 500, 50.000 x 3% / 2 = 750: 1.250 sopra la polvere
    prova("50.000 sats: 500 + 750, importo 50.000 + 1.080 + 500", (1250, 750, 51580),
          (oa["quota_sats"], oa["quota_ricevente_sats"], oa["importo_sats"]))
    paga(oa)
    gesto(999, oid2, "controlla")
    ob = uno(888, oid2)
    r = gesto(888, oid2, "proposta", verso="compratore",
              psbt=psbt_di(ob, [(ob["rimborso"], 51580 - 300)], 888).to_string())
    r2 = gesto(999, oid2, "firma", tx=cofirma(999, uno(999, oid2)))
    tx = Transaction.from_string(INVIATE[0])
    prova("Alan rinuncia: rimborsato, e ad Andrea torna l'importo intero meno la rete "
          "(la sua meta' compresa)", (200, "rimborsato", [51280]),
          (r.status_code, r2.json()["stato"], [v.value for v in tx.vout]))

    # ---- 5) la disputa decisa: Barattolo firma con la commissione ---------
    print("\n[la disputa decisa: la firma di Barattolo porta la commissione]")
    INVIATE.clear()
    oid3 = pubblica(999, sats=60000, euro_cent=5400, metodi=["Bonifico"]).json()["id"]
    gesto(888, oid3, "prendi")
    oa = uno(999, oid3)
    # 60.000: 600 + 900 = 1.500; importo 60.000 + 1.080 + 600
    paga(oa)
    gesto(999, oid3, "controlla")
    gesto(888, oid3, "euro-inviati")
    gesto(999, oid3, "disputa", motivo="Gli euro non sono mai arrivati")
    r = gesto(777, oid3, "decidi", verso="venditore")
    ob = uno(888, oid3)
    r2 = gesto(888, oid3, "firma", tx=cofirma(888, ob))
    tx = Transaction.from_string(INVIATE[0])
    rete3 = (11 + 105 + 31 * 3) * 2
    prova("il moderatore decide per chi compra: 59.100 ad Alan, 1.500 a Barattolo, il "
          "resto ad Andrea meno la rete misurata da Barattolo",
          (200, "rilasciato", sorted([(ob["incasso"], 59100), (ob["quota_indirizzo"], 1500),
                                      (RIMBORSO_999, 61680 - 59100 - 1500 - rete3)])),
          (r.status_code, r2.json()["stato"],
           sorted((script.Script(v.script_pubkey.data).address(N), v.value) for v in tx.vout)))

    # ---- 6) sotto la polvere si sale alla polvere ---------------------------
    # (20 nov 2026, cantiere fee-minima-oc; Andrea: «Il livello pioniere
    # paga comunque una fee, seppur ridotta». Prima qui era tutto zero)
    print("\n[lo scambio piccolo: sotto la polvere la commissione sale a 546]")
    oid4 = pubblica(999, sats=12000, euro_cent=1100).json()["id"]
    r = gesto(888, oid4, "prendi")
    o4 = r.json()
    # 12.000 x 1% = 120 + 12.000 x 1,5% = 180: 300 < 546, quindi 546 divisi
    # in proporzione: 546 x 120/300 = 218 al pioniere che deposita, 328
    # all'altro che riceve
    prova("12.000 sats: 120 + 180 = 300 sotto i 546, quindi 546 in proporzione "
          "(218 al pioniere, 328 all'altro), con l'uscita verso Barattolo e la "
          "meta' di chi deposita nell'importo", (200, 546, 328, True, 12000 + 1080 + 218),
          (r.status_code, o4["quota_sats"], o4["quota_ricevente_sats"],
           bool(o4["quota_indirizzo"]), o4["importo_sats"]))

    # ---- 7) la commissione pura -------------------------------------------
    print("\n[il conto puro delle due meta']")
    con = SRV.db()
    K = SRV._p2p_onchain_commissioni
    prova("pioniere e no, fee zero, sotto la polvere (546 in proporzione, nei due "
          "versi), fee non letta",
          [(1000, 1500), (1500, 1000), (0, 0), (218, 328), (328, 218), "x"],
          [K(con, 999, 888, 100000, 0.03), K(con, 888, 999, 100000, 0.03),
           K(con, 999, 888, 100000, 0.0), K(con, 999, 888, 12000, 0.03),
           K(con, 888, 999, 12000, 0.03), "x"])
    try:
        K(con, 999, 888, 100000, None)
        senza = "passata"
    except ValueError as e:
        senza = str(e)
    con.close()
    prova("...e senza fee un ValueError col perche'", "la commissione del P2P non si legge", senza)
    SRV.P2P_SCONTO_FEDELTA_PERCENTO = 0.0

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
