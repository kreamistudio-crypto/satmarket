# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEGLI USDT NEGLI SCAMBI P2P ON-CHAIN (2 nov 2026, cantiere
p2p-onchain-usdt, Andrea: «usdt onchain assolutamente è da fare»; la
strada di Alan: la garanzia sta sempre e solo dal lato bitcoin). Il giro
col SERVER VERO, per HTTP (TestClient), come `collaudo_p2p_onchain`: i
sats nel 2-di-3 di sempre, e chi compra bitcoin paga in USDT su Tron o
Ethereum invece che in euro. Qui: la leva sua e i due cancelli, la
valuta che si legge dai metodi (e non si mescola con l'euro), il tetto
tradotto in USDT, l'indirizzo sulla rete giusta (pubblicazione, presa,
recapito), il 38383 con `f` = USDT, il libro che li mostra solo a chi
li puo' prendere, «Ho inviato gli USDT» con l'id della transazione
giudicato sulla rete, gli avvisi del bot senza euro, il moderatore che
vede rete, indirizzo e id, e la liberazione con le due firme di sempre.

IL TELEFONO E' EMBIT, MEMPOOL E' DI CARTONE, i relay sono muti per
costruzione: nessuna rete, nessun sats, nessun USDT.

USO:  python collaudo_p2p_onchain_usdt.py
"""
import hashlib
import time
import json
import os
import sys

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova

# indirizzi di prova: il contratto USDT su Tron e' un indirizzo Tron
# valido col suo controllo, ma e' il CONTRATTO; questi due sono indirizzi
# Tron e Ethereum qualunque, ben formati
TRON = "TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy"
ETH = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
TXID_TRON = "a" * 64
TXID_ETH = "0x" + "b" * 64


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
    print("  GLI USDT NEGLI SCAMBI P2P ON-CHAIN — il giro vero")
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
                "metodi": ["USDT (Tron)"], "recapito": TRON}
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

    SRV.P2P_USDT_ATTIVO = True
    SRV.P2P_USDT_SOLO_ADMIN = True
    SRV.P2P_ONCHAIN_ATTIVO = True
    SRV.P2P_ONCHAIN_USDT_ATTIVO = False
    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    # (10 nov 2026, rimborso-wallet) chi mette i sats ha un wallet SUO per
    # i rimborsi e il resto: mai il seme di Barattolo
    RIMBORSO_999 = dal_wallet(50)
    come(999)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": RIMBORSO_999,
        "firma": firma_dest(999, "indirizzo", RIMBORSO_999)})

    # ---- 0) la leva spenta ------------------------------------------------
    print("\n[la leva spenta: gli USDT on-chain non esistono]")
    come(999)
    me = c.get("/api/me").json()
    prova("leva spenta: l'admin ha il P2P on-chain e gli USDT di Mostro, ma "
          "non gli USDT on-chain", (True, True, False),
          (me["p2p_onchain"], me["p2p_usdt"], me["p2p_onchain_usdt"]))
    r = pubblica(999)
    prova("...e un ordine on-chain in USDT non nasce: 400 col perche'", (400, True),
          (r.status_code, "USDT non sono accesi" in r.json()["detail"]))
    SRV.P2P_ONCHAIN_USDT_ATTIVO = True
    SRV.P2P_USDT_ATTIVO = False
    come(999)
    prova("leva accesa ma USDT di Mostro spenti: no lo stesso (i due cancelli)",
          (False, 400), (c.get("/api/me").json()["p2p_onchain_usdt"],
                         pubblica(999).status_code))
    SRV.P2P_USDT_ATTIVO = True
    come(999)
    prova("tutto acceso: l'admin e' ammesso", True,
          c.get("/api/me").json()["p2p_onchain_usdt"])

    # ---- 1) pubblicare: la valuta e la rete ------------------------------
    print("\n[pubblicare: la valuta dai metodi, la rete giusta]")
    r = pubblica(999)
    prova("senza i cambi di adesso il tetto in USDT non si sa: fermo (max 1 "
          "USDT), mai un via libera inventato", (400, True),
          (r.status_code, "fino a 1 USDT" in r.json()["detail"]))
    # IL TETTO TRADOTTO: 250 € a 90.000 €/BTC e 100.000 $/BTC = 277 USDT
    SRV._cambio_cache["valori"].update(eur=90000.0, usd=100000.0)
    SRV._cambio_cache["quando"] = time.time()
    r = pubblica(999, metodi=["USDT (Tron)", "SEPA"])
    prova("USDT mescolati coi metodi dell'euro: 400", (400, True),
          (r.status_code, "senza i metodi dell'euro" in r.json()["detail"]))
    r = pubblica(999, metodi=["USDT (Polygon)"])
    prova("una rete che non offriamo (Polygon): 400, e' un metodo dell'euro "
          "che dice USDT", (400, True),
          (r.status_code, "Tron o Ethereum" in r.json()["detail"]))
    r = pubblica(999, recapito=ETH)
    prova("chi vende su Tron e scrive un indirizzo Ethereum: 400, la rete "
          "sbagliata detta per nome", (400, True),
          (r.status_code, "indirizzo Ethereum, ma lo scambio è su Tron" in r.json()["detail"]))
    r = pubblica(999, recapito="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
    prova("...il contratto del token al posto del proprio indirizzo: 400",
          (400, True), (r.status_code, "contratto USDT" in r.json()["detail"]))
    r = pubblica(999, recapito=TRON[:-1] + ("z" if TRON[-1] != "z" else "y"))
    prova("...un carattere sbagliato (il controllo non torna): 400", (400, True),
          (r.status_code, "carattere sbagliato" in r.json()["detail"]))
    r = pubblica(999, recapito="bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
    prova("...un indirizzo bitcoin: 400", (400, True),
          (r.status_code, "indirizzo bitcoin" in r.json()["detail"]))
    r = pubblica(999, euro_cent=27800)
    prova("il tetto: 250 € al cambio di adesso sono 277 USDT, 278 no", (400, True),
          (r.status_code, "fino a 277 USDT" in r.json()["detail"]))
    banco.DETTO.clear()
    r = pubblica(999, euro_cent=9000)
    o = r.json()
    prova("vendo 100.000 sats per 90 USDT su Tron: nasce, in USDT, coi suoi "
          "dati di rete", (200, "pending", "USDT", "tron", ""),
          (r.status_code, o["stato"], o["fiat"], o["usdt"]["rete"], o["usdt"]["txid"]))
    oid = o["id"]
    con = SRV.db()
    riga = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    tags = {t[0]: t[1:] for t in SRV.p2p_onchain_tags(riga, 1000)}
    prova("il 38383: f = USDT, fa = 90, pm = la rete con la grafia del protocollo",
          (["USDT"], ["90"], ["USDT (Tron)"]), (tags["f"], tags["fa"], tags["pm"]))
    r = pubblica(999, metodi=["Bonifico"], recapito="IT00 X 1")
    oid_euro = r.json()["id"]
    prova("...e uno in euro accanto resta in euro", (200, ["EUR"]),
          (r.status_code, [t[1] for t in SRV.p2p_onchain_tags(
              SRV._p2p_onchain_carica(SRV._p2p_onchain_db(), oid_euro), 1000) if t[0] == "f"]))

    # ---- 2) il libro: solo a chi li puo' prendere -----------------------
    print("\n[il libro: gli USDT solo a chi li puo' prendere]")
    L = libro(888)["onchain"]["eventi"]
    prova("Alan (ammesso) vede i due ordini, quello in USDT col suo fiat",
          ({oid, oid_euro}, "USDT"),
          ({e["id"] for e in L}, [e for e in L if e["id"] == oid][0]["fiat"]))
    SRV.P2P_ONCHAIN_USDT_ATTIVO = False
    SRV._p2p_onchain_rifai_foto()
    prova("a leva spenta il libro mostra solo quello in euro, anche agli admin",
          [oid_euro], [e["id"] for e in libro(888)["onchain"]["eventi"]])
    prova("...e chi guarda senza entrare non vede gli USDT", [oid_euro],
          [e["id"] for e in libro(0)["onchain"]["eventi"]])
    prova("...e prenderlo e' 409", 409, gesto(888, oid, "prendi").status_code)
    SRV.P2P_ONCHAIN_USDT_ATTIVO = True
    SRV._p2p_onchain_rifai_foto()
    # chi prende senza gli USDT (e chi ha pubblicato si'): la porta di chi
    # prende, da sola
    vero = SRV.p2p_usdt_ammesso
    SRV.p2p_usdt_ammesso = lambda tg: int(tg) != 888 and vero(tg)
    r = gesto(888, oid, "prendi")
    prova("chi prende senza gli USDT trova 409 col perche', anche se chi ha "
          "pubblicato li ha", (409, True),
          (r.status_code, "che per te non sono accesi" in r.json()["detail"]))
    SRV.p2p_usdt_ammesso = vero
    gesto(999, oid_euro, "annulla")

    # ---- 3) prendere e depositare -----------------------------------------
    print("\n[prendere e depositare: il 2-di-3 di sempre]")
    banco.DETTO.clear()
    r = gesto(888, oid, "prendi")
    o = r.json()
    prova("Alan compra: preso, riceve sats, e vede l'indirizzo Tron di chi vende",
          (200, "preso", "venditore", TRON, "USDT"),
          (r.status_code, o["stato"], o["ruolo"], o["recapito"], o["fiat"]))
    presa = [t for chi, t in banco.DETTO if chi == 888]
    prova("...l'avviso della presa dice USDT e mai euro", (True, []),
          (any("90,00 USDT" in t for t in presa),
           [t[:60] for t in presa if "€" in t or " euro" in t]))
    oa = uno(999, oid)
    paga(oa)
    banco.DETTO.clear()
    prova("deposito confermato: depositato", "depositato",
          gesto(888, oid, "controlla").json()["stato"])
    dep = [t for chi, t in banco.DETTO if chi in (888, 999)]
    prova("...e gli avvisi del deposito parlano di USDT, non di euro ne' di conto",
          (True, []), (any("USDT" in t for t in dep),
                       [t[:60] for t in dep if "€" in t or "euro" in t or " conto" in t]))
    r = gesto(999, oid, "recapito", recapito=ETH)
    prova("chi vende cambia il recapito con un indirizzo dell'altra rete: 400",
          (400, True), (r.status_code, "rete sbagliata" in r.json()["detail"]))
    prova("...con un altro indirizzo Tron va", 200,
          gesto(999, oid, "recapito", recapito=TRON).status_code)

    # ---- 4) «Ho inviato gli USDT» con l'id ------------------------------
    print("\n[«Ho inviato gli USDT»: l'id della transazione, sulla rete giusta]")
    r = gesto(888, oid, "euro-inviati")
    prova("senza l'id: 400", (400, True),
          (r.status_code, "id della transazione" in r.json()["detail"]))
    r = gesto(888, oid, "euro-inviati", txid=TXID_ETH)
    prova("un id con la forma di Ethereum su uno scambio Tron: 400", (400, True),
          (r.status_code, "forma di Ethereum" in r.json()["detail"]))
    banco.DETTO.clear()
    r = gesto(888, oid, "euro-inviati", txid=TXID_TRON)
    prova("l'id giusto: euro_inviati, e chi vende lo riceve col suo id, senza €",
          (200, True, True, False),
          (r.status_code, detto_a(999, TXID_TRON), detto_a(999, "90,00 USDT su Tron"),
           detto_a(999, "€")))
    oa = uno(999, oid)
    prova("...l'id sta nello scambio, per le due parti", (TXID_TRON, TXID_TRON),
          (oa["usdt"]["txid"], uno(888, oid)["usdt"]["txid"]))
    come(777)
    t = c.get(f"/api/p2p/onchain/{oid}").json()
    prova("il moderatore vede rete, indirizzo USDT e id (un indirizzo di una "
          "catena, non un IBAN), ma non il campo recapito delle parti",
          ("tron", TRON, TXID_TRON, False),
          (t["usdt"]["rete"], t["usdt"].get("indirizzo"), t["usdt"]["txid"], "recapito" in t))
    prova("...e alle parti l'indirizzo non arriva due volte", False,
          "indirizzo" in uno(888, oid)["usdt"])

    # ---- 5) la liberazione: le due firme di sempre ----------------------
    print("\n[la liberazione: le due firme di sempre]")
    come(888)
    c.post("/api/onchain/incasso", json={"tipo": "xpub", "valore": vpub,
                                         "firma": firma_dest(888, "xpub", vpub)})
    o = uno(999, oid)
    giusto = [(o["incasso"], 100000), (o["rimborso"], o["importo_sats"] - 100000 - 300)]
    banco.DETTO.clear()
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, giusto, 999).to_string())
    prova("chi vende libera: la proposta passa, Alan e' chiamato a co-firmare",
          (200, True), (r.status_code, detto_a(888, "seconda firma")))
    r = gesto(888, oid, "firma", tx=cofirma(888, uno(888, oid)))
    prova("la seconda firma: rilasciato, la transazione bitcoin partita",
          (200, "rilasciato", 1), (r.status_code, uno(999, oid)["stato"], len(INVIATE)))
    tutti = [t for chi, t in banco.DETTO if chi in (888, 999)]
    prova("...e in tutto il giro gli avvisi alle parti non hanno detto euro",
          [], [t[:60] for t in tutti if "€" in t or "euro" in t])

    # ---- 6) Ethereum, e chi prende vendendo ------------------------------
    print("\n[Ethereum: chi prende un «compro» scrive dove vuole gli USDT]")
    come(888)
    r = c.post("/api/p2p/onchain/pubblica", json={
        "lato": "buy", "sats": 100000, "euro_cent": 9000,
        "metodi": ["USDT (Tron)", "USDT (Ethereum)"]})
    oid2 = r.json()["id"]
    prova("Alan compra bitcoin pagando USDT su Tron o Ethereum: nasce, rete "
          "da decidere", (200, "USDT", ""), (r.status_code, r.json()["fiat"],
                                            r.json()["usdt"]["rete"]))
    r = gesto(999, oid2, "prendi", recapito="bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
    prova("chi prende vendendo con un indirizzo bitcoin al posto degli USDT: 400",
          (400, True), (r.status_code, "indirizzo bitcoin" in r.json()["detail"]))
    r = gesto(999, oid2, "prendi", recapito=ETH)
    prova("...con un indirizzo Ethereum: preso, e la rete dello scambio e' "
          "Ethereum (la dice l'indirizzo)", (200, "ethereum"),
          (r.status_code, r.json()["usdt"]["rete"]))
    o2 = uno(999, oid2)
    paga(o2)
    gesto(999, oid2, "controlla")
    prova("su Ethereum un id di Tron non passa, uno di Ethereum si'", [400, 200],
          [gesto(888, oid2, "euro-inviati", txid=TXID_TRON).status_code,
           gesto(888, oid2, "euro-inviati", txid=TXID_ETH).status_code])

    # ---- 6) IN MONETA: l'id della transazione (17 nov 2026, Andrea:
    # «Perché per usde non si può incollare id transazione?») ---------------
    print("\n[in moneta: l'id della transazione, come gli USDT]")
    SRV.P2P_COIN_ATTIVO = True
    SRV._cambio_coin_cache.update(eth=3000.0, xmr=150.0, usde=0.92, quando=time.time())
    r = pubblica(999, metodi=["USDe (Ethereum) 50.00"], recapito=ETH, euro_cent=None)
    prova("chi vende bitcoin per USDe su Ethereum pubblica", 200, r.status_code)
    oid3 = r.json()["id"]
    come(888)
    gesto(888, oid3, "prendi")
    paga(uno(999, oid3))
    gesto(888, oid3, "controlla")
    r = gesto(888, oid3, "euro-inviati")
    prova("«Ho inviato gli USDe» senza l'id: 400", (400, True),
          (r.status_code, "id della transazione" in r.json()["detail"]))
    r = gesto(888, oid3, "euro-inviati", txid=TXID_TRON[:40])
    prova("...con un id storto: 400", (400, True),
          (r.status_code, "non sembra l'id" in r.json()["detail"]))
    banco.DETTO.clear()
    r = gesto(888, oid3, "euro-inviati", txid="c" * 64)
    prova("...con l'id senza 0x: passa, si salva col suo 0x, e chi vende lo "
          "riceve con la cifra in USDe", (200, "euro_inviati", "0x" + "c" * 64, True, True),
          (r.status_code, uno(999, oid3)["stato"], uno(999, oid3)["coin_tx"]["txid"],
           detto_a(999, "0x" + "c" * 64), detto_a(999, "50,00 USDe su Ethereum")))
    prova("...l'id lo vede anche chi l'ha mandato", "0x" + "c" * 64,
          uno(888, oid3)["coin_tx"]["txid"])
    come(777)
    t = c.get(f"/api/p2p/onchain/{oid3}").json()
    prova("il moderatore vede l'id e l'indirizzo di chi riceveva", ("0x" + "c" * 64, ETH),
          (t["coin_tx"]["txid"], t["coin_tx"].get("indirizzo")))
    # Monero vuole anche la chiave della transazione
    XMR = ("4AdUndXHHZ6cfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2684Rge")
    r = pubblica(999, metodi=["XMR (Monero) 0.300000"], recapito=XMR, euro_cent=None)
    if r.status_code == 200:
        oid4 = r.json()["id"]
        gesto(888, oid4, "prendi")
        paga(uno(999, oid4))
        gesto(888, oid4, "controlla")
        prova("in Monero l'id da solo non basta: serve la chiave; con tutt'e due passa",
              [400, 200, "d" * 64],
              [gesto(888, oid4, "euro-inviati", txid="e" * 64).status_code,
               gesto(888, oid4, "euro-inviati", txid="e" * 64, chiave="d" * 64).status_code,
               uno(999, oid4)["coin_tx"]["chiave"]])
    else:
        prova("l'ordine in Monero nasce (indirizzo di prova valido)", 200,
              (r.status_code, r.json().get("detail")))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
