# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEGLI SCAMBI P2P ON-CHAIN (30 ott 2026, cantiere
p2p-onchain-2di3) — il giro col SERVER VERO, per HTTP (TestClient, la app
vera), della garanzia 2-di-3 negli scambi bitcoin ↔ euro: il libro
accanto a quello di Mostro, l'ordine che nasce e va su Nostr (38383),
la presa che fa nascere il 2-di-3, il deposito visto su mempool, «ho
inviato gli euro», la prima firma di chi vende bitcoin e la seconda di
chi li compra, il rimborso, la disputa decisa da un moderatore con la
firma di Barattolo, l'annullo prima del deposito e il ritardatario, la
scadenza nel libro, i tetti e la leva spenta.

IL «TELEFONO» QUI E' EMBIT, come nel collaudo dell'ordine on-chain: i
semi sono i vettori ufficiali del BIP-39 e le firme si fanno con embit.
MEMPOOL E' DI CARTONE (monete, tariffa, trasmissione sostituite), i
relay sono muti per costruzione (MODALITA_COLLAUDO: `_spedisci_ai_relay`
non apre niente). Nessuna rete, nessun sats. La chiave di Barattolo e'
quella di cartone della gabbia: la stessa strada del VPS (`_onchain_
psbt_barattolo`), solo con un seme pubblicato in uno standard.

USO:  python collaudo_p2p_onchain.py
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
    print("  GLI SCAMBI P2P ON-CHAIN (2-di-3) — il giro vero")
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

    # ---- 0) la leva spenta ------------------------------------------------
    print("\n[la leva spenta: niente esiste]")
    SRV.P2P_ONCHAIN_ATTIVO = False
    come(999)
    prova("a leva spenta /api/me dice p2p_onchain False, anche all'admin",
          False, c.get("/api/me").json().get("p2p_onchain"))
    prova("...il libro non ha la busta onchain", False, "onchain" in libro(999))
    prova("...e pubblicare, prendere e moderare sono 404", [404, 404, 404],
          [pubblica(999).status_code,
           c.post("/api/p2p/onchain/1/prendi", json={}).status_code,
           c.get("/api/p2p/onchain/moderazione/aperte").status_code])
    # il tetto di prova scritto: 250 € (17 nov 2026, il P2P on-chain ha il
    # suo tetto, 999 di serie; questo collaudo misura i suoi no a 250)
    SRV.P2P_ONCHAIN_MAX_EURO = 250
    SRV.P2P_ONCHAIN_ATTIVO = True
    SRV.ONCHAIN_ATTIVO = False
    prova("leva P2P accesa ma on-chain spento: non esiste lo stesso "
          "(il 2-di-3 non c'e')", (False, 404),
          (SRV.p2p_onchain_leva(), pubblica(999).status_code))
    SRV.ONCHAIN_ATTIVO = True

    # ---- 1) chi e' ammesso --------------------------------------------------
    print("\n[chi e' ammesso: il cancello dell'on-chain e del P2P]")
    come(999)
    prova("leva accesa: l'admin e' ammesso", True,
          c.get("/api/me").json()["p2p_onchain"])
    come(111)
    prova("...chi non e' ammesso all'on-chain (ONCHAIN_SOLO_ADMIN) no", False,
          c.get("/api/me").json()["p2p_onchain"])
    prova("...e per lui pubblicare e' 404", 404, pubblica(111).status_code)
    r = pubblica(999)
    prova("l'admin senza la chiave on-chain: 409 col perche'", (409, True),
          (r.status_code, "chiave on-chain" in r.json()["detail"]))
    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    # (10 nov 2026, rimborso-wallet) chi deposita ha un wallet SUO per i
    # rimborsi e il resto: mai il seme di Barattolo. Un indirizzo fisso,
    # cosi' i suoi incassi da chi compra restano un'altra storia
    RIMBORSO_999 = dal_wallet(50)
    come(999)
    prova("Andrea sceglie il suo wallet (rimborsi e resti), firmato dal "
          "suo seme", 200, c.post("/api/onchain/incasso", json={
              "tipo": "indirizzo", "valore": RIMBORSO_999,
              "firma": firma_dest(999, "indirizzo", RIMBORSO_999)}).status_code)

    # ---- 2) pubblicare ------------------------------------------------------
    print("\n[pubblicare: il giudice e il libro]")
    G = SRV.p2p_onchain_giudica_nuovo
    prova("il giudice puro dice i no: lato, minimo, euro, metodi, tetto, "
          "tetto sats di prova, metodo storto; e il si'",
          [True, True, True, True, True, True, True, ""],
          [G("x", 1, 1, ["a"], "", 0, 0).startswith("Di' se vendi"),
           G("sell", 5000, 100, ["a"], "", 0, 0).startswith("Minimo 10.000"),
           G("sell", 50000, 0, ["a"], "", 0, 0).startswith("Scrivi quanti euro"),
           G("sell", 50000, 100, [], "", 0, 0).startswith("Scegli almeno"),
           "fino a 250 €" in G("sell", 50000, 30000, ["a"], "", 250, 0),
           "oltre 40.000" in G("sell", 50000, 100, ["a"], "", 0, 40000),
           "non si legge" in G("sell", 50000, 100, ["a,b"], "", 0, 0),
           G("sell", 50000, 9000, ["Bonifico"], "", 250, 0)])
    prova("per HTTP: sotto il minimo 400, euro sopra il tetto 400, metodi "
          "vuoti 400", [400, 400, 400],
          [pubblica(999, sats=5000).status_code,
           pubblica(999, euro_cent=30000).status_code,
           pubblica(999, metodi=[]).status_code])
    # IL TETTO E' QUELLO DELL'ON-CHAIN (12 nov 2026, Andrea: «p2p onchain
    # metti 500»): non P2P_MAX_EURO del Lightning, e dal 17 nov 2026
    # (Andrea: «separalo») nemmeno ONCHAIN_MAX_EURO del mercatino
    vecchi = (SRV.P2P_ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO, SRV.p2p_onchain_giudica_nuovo,
              SRV.ONCHAIN_MAX_EURO)
    SRV.P2P_ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO, SRV.ONCHAIN_MAX_EURO = 500, 250, 3000
    visti = []
    def spia(*a, **k):
        visti.append(a[5])
        return vecchi[2](*a, **k)
    SRV.p2p_onchain_giudica_nuovo = spia
    try:
        r6 = pubblica(999, euro_cent=60000)
        busta = libro()["onchain"]
    finally:
        (SRV.P2P_ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO, SRV.p2p_onchain_giudica_nuovo,
         SRV.ONCHAIN_MAX_EURO) = vecchi
    prova("il tetto degli scambi on-chain e' P2P_ONCHAIN_MAX_EURO (500), non "
          "quello del P2P Lightning (250) ne' quello del mercatino (3000): "
          "600 € no «fino a 500 €», e il "
          "libro lo dice al foglio", ([500], 400, True, 500),
          (visti, r6.status_code, "fino a 500 €" in r6.json().get("detail", ""),
           busta.get("maxEuro")))
    r = pubblica(999)
    o = r.json()
    prova("vendo 100.000 sats per 90 €: nasce nel libro, pending, mio, "
          "con la rotta per il telefono",
          (200, "pending", "sell", True, True, "maker"),
          (r.status_code, o["stato"], o["lato"], o["mio"],
           o["ordine"].startswith("bar-onchain-"), o["ruolo"]))
    oid = o["id"]
    prova("...il recapito lo vede chi l'ha scritto", "IT00 X 1234", o["recapito"])
    L = libro()
    prova("il libro anonimo ha la busta onchain con l'ordine, senza nome "
          "ne' recapito ne' «miei»", (1, 100000, 90.0, False, False, False, "signet"),
          (len(L["onchain"]["eventi"]), L["onchain"]["eventi"][0]["sats"],
           L["onchain"]["eventi"][0]["euro"], "nome" in L["onchain"]["eventi"][0],
           "recapito" in L["onchain"]["eventi"][0], "miei" in L["onchain"],
           L["onchain"]["rete"]))
    prova("...e ogni riga porta il NUMERO (quello che la card tocca e la "
          "rotta vuole) e il nome pubblico (quello di «miei»)",
          (oid, o["ordine"], True),
          (L["onchain"]["eventi"][0]["id"], L["onchain"]["eventi"][0]["ordine"],
           isinstance(L["onchain"]["eventi"][0]["id"], int)))
    prova("...a chi e' entrato dice il nome di chi pubblica e quali sono suoi",
          ("Andrea", [o["ordine"]], []),
          (libro(888)["onchain"]["eventi"][0]["nome"], libro(999)["onchain"]["miei"],
           libro(888)["onchain"]["miei"]))
    # LA PORTA DEL VOLTO (12 nov 2026, Andrea: «quando clicco sulla faccia
    # si apre l'ordine e non l'utente»): il negozio di chi pubblica, con
    # la sessione come il nome, mai al libro anonimo
    prova("...e il suo negozio, perche' la faccia apra quello; l'anonimo no",
          ("neg999999", False),
          (libro(888)["onchain"]["eventi"][0].get("negozio"),
           "negozio" in libro()["onchain"]["eventi"][0]))
    con = SRV.db()
    riga = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?",
                       (oid,)).fetchone()
    con.close()
    tags = {t[0]: t[1:] for t in SRV.p2p_onchain_tags(riga, 1000)}
    prova("il 38383 NIP-69: d, k, f, s, amt, fa, pm, premium + layer/network",
          ([riga["ordine"]], ["sell"], ["EUR"], ["pending"], ["100000"],
           ["90"], ["Bonifico", "Revolut"], ["onchain"], ["signet"],
           [str(riga["scade"])], ["barattolo"]),
          (tags["d"], tags["k"], tags["f"], tags["s"], tags["amt"], tags["fa"],
           tags["pm"], tags["layer"], tags["network"], tags["expiration"],
           tags["y"]))
    ev = SRV.p2p_onchain_evento(riga)
    prova("...l'evento e' un 38383 firmato dalla chiave del server, senza "
          "contenuto, e la firma regge", (38383, SRV._NOSTR[1], "", True),
          (ev["kind"], ev["pubkey"], ev["content"],
           schnorr_puro.verifica(bytes.fromhex(ev["pubkey"]), bytes.fromhex(ev["id"]),
                                 bytes.fromhex(ev["sig"]))))
    con = SRV.db()
    riga = con.execute("SELECT evento_id, pubblicato_stato FROM p2p_onchain_ordini"
                       " WHERE id=?", (oid,)).fetchone()
    con.close()
    prova("...e la riga ricorda l'evento partito (pubblicato come pending)",
          (64, "pending"), (len(riga["evento_id"] or ""), riga["pubblicato_stato"]))
    come(999)
    prova("«I miei scambi» di chi ha pubblicato lo ha; per un altro e' vuoto",
          (1, 0), (len(c.get("/api/p2p/onchain/miei").json()["ordini"]),
                   (come(888), len(c.get("/api/p2p/onchain/miei").json()["ordini"]))[1]))

    prova("nel libro, prima della presa, nessun volto dell'altro", None,
          uno(999, oid).get("controparte"))

    # ---- 3) prendere --------------------------------------------------------
    print("\n[prendere: nasce il 2-di-3]")
    prova("chi l'ha pubblicato non lo prende: 409", 409,
          gesto(999, oid, "prendi").status_code)
    come(111)
    prova("chi non e' ammesso: 404", 404,
          c.post(f"/api/p2p/onchain/{oid}/prendi", json={}).status_code)
    banco.DETTO.clear()
    # (18 nov 2026, mercato-onchain) un cambio noto alla presa: a prezzo
    # fisso si timbra lo stesso, metro di «Rispetto al mercato della presa»
    cambio_prima = (dict(SRV._cambio_cache["valori"]), SRV._cambio_cache["quando"])
    SRV._cambio_cache["valori"]["eur"] = 95000.0
    SRV._cambio_cache["quando"] = time.time()
    r = gesto(888, oid, "prendi")
    SRV._cambio_cache["valori"], SRV._cambio_cache["quando"] = cambio_prima
    o = r.json()
    prova("a prezzo fisso il cambio della presa si timbra lo stesso, e chi "
          "ha preso lo legge (il metro di «Rispetto al mercato della presa»)",
          95000.0, o.get("cambio_presa"))
    prova("Alan compra: preso, lui e' il «venditore» del 2-di-3 (riceve), "
          "il margine di rete e' 3 x 2 x 180 = 1080",
          (200, "preso", "venditore", "compro", 1080, 101080),
          (r.status_code, o["stato"], o["ruolo"], o["parte"],
           o["margine_sats"], o["importo_sats"]))
    prova("...l'indirizzo e' un 2-di-3 di signet; chi compra non ha ancora "
          "scelto dove ricevere (incasso vuoto), il rimborso torna al "
          "wallet di chi vende bitcoin (mai al seme)",
          (True, "", RIMBORSO_999, "Andrea"),
          (o["indirizzo"]["indirizzo"].startswith("tb1q"), o["incasso"],
           o["rimborso"], o["altro"]))
    prova("...e il recapito per gli euro lo legge", "IT00 X 1234", o["recapito"])
    oa = uno(999, oid)
    prova("Andrea e' il «compratore» del 2-di-3 (deposita), parte 'vendo'",
          ("compratore", "vendo", "Alan", True),
          (oa["ruolo"], oa["parte"], oa["altro"], oa["deposito_entro"] > oa["preso_il"]))
    # CHI E' L'ALTRO (17 nov 2026, cantiere onchain-controparte): il volto
    # della card, lo stesso del Lightning, alle due parti dalla presa
    prova("...e tutt'e due vedono il VOLTO dell'altro (la card col negozio)",
          ("Andrea", "neg999999", "Alan"),
          ((o.get("controparte") or {}).get("nome"),
           (o.get("controparte") or {}).get("negozio"),
           (oa.get("controparte") or {}).get("nome")))
    prova("...tutt'e due avvisati, nessuna xpub in giro",
          (True, True, False, False),
          (detto_a(999, "tocca a te depositare"), detto_a(888, "appena chi vende deposita"),
           conto(999) in r.text, conto(888) in r.text))
    prova("il libro non lo mostra piu'", 0, len(libro()["onchain"]["eventi"]))
    # GLI AVVISI COME QUELLI DEL LIGHTNING (30 ott 2026, Andrea alla prima
    # prova): chi ha pubblicato legge «Il tuo ordine on-chain è stato
    # preso!», chi ha preso «Hai preso l'ordine on-chain di …!», con cosa si
    # scambia e il bottone dello scambio sotto
    presa = {chi: (t, b) for chi, t, b in BOTTONI if "preso" in t}
    prova("la presa: due avvisi nella forma del Lightning, il cerchio arancione 🟠 in testa, "
          "cosa si scambia, il tempo del deposito a chi deposita",
          (True, True, True, True, True, True),
          (presa[999][0].startswith("🟠 <b>Il tuo ordine on-chain è stato preso!</b> Vendi 100.000 sats per 90,00 € via Bonifico, Revolut."),
           presa[888][0].startswith("🟠 <b>Hai preso l'ordine on-chain di Andrea!</b> Compri 100.000 sats"),
           "\n\nApri Barattolo: tocca a te depositare" in presa[999][0],
           "⏳ <b>Hai 6 ore</b>" in presa[999][0],
           "⏳" not in presa[888][0],
           "\n\nApri Barattolo:" in presa[888][0]))
    prova("...e sotto tutti e due il bottone «🟠 Apri lo scambio» col nome "
          "pubblico dello scambio, che la Mini App sa aprire",
          (("🟠 Apri lo scambio", f"{SRV.LINK_LIBRO_P2P}?scambio={o['ordine']}"),) * 2
          + (f"scambio_{o['ordine']}",),
          (presa[999][1], presa[888][1], SRV._startapp_da_link(presa[999][1][1])))
    con = SRV.db()
    prova("l'indirizzo e' marcato come del P2P (ordine_id negativo)", -oid,
          con.execute("SELECT ordine_id FROM onchain_indirizzi WHERE id=?",
                      (o["indirizzo"]["id"],)).fetchone()[0])
    con.close()
    come(777)
    t = c.get(f"/api/p2p/onchain/{oid}").json()
    prova("un moderatore terzo lo vede, ma senza recapito e con le parti",
          ("moderatore", False, "Andrea", "Alan"),
          (t["ruolo"], "recapito" in t, t["parti"]["vende"], t["parti"]["compra"]))
    prova("...e senza il volto della card: quello e' delle due parti", False,
          "controparte" in t)

    # ---- 4) il deposito -----------------------------------------------------
    print("\n[il deposito: mempool vede, una conferma decide]")
    # (17 nov 2026) chi compra annulla quando vuole, finche' niente e'
    # visto in rete: su uno scambio a parte, questo deve andare avanti
    ox = pubblica(999).json()
    gesto(888, ox["id"], "prendi")
    r = gesto(888, ox["id"], "annulla")
    prova("chi compra annulla anche prima della fine della finestra del "
          "deposito (niente in rete): annullato, e chi vende avvisato",
          (200, "annullato", True),
          (r.status_code, uno(999, ox["id"])["stato"],
           detto_a(999, "Il tuo ordine è tornato nel libro")))
    # (19 nov 2026, ritorno-nel-libro) l'ordine non sparisce: ne rinasce uno
    # uguale nel libro, e lo scambio chiuso dice il suo nome
    con = SRV.db()
    figlio = con.execute("SELECT id, ordine, stato, prezzo_sats, recapito FROM p2p_onchain_ordini"
                         " WHERE rinato_da=?", (ox["id"],)).fetchone()
    con.close()
    prova("...e l'ordine torna nel libro: uno nuovo, uguale, che lo scambio chiuso nomina",
          ("pending", 100000, "IT00 X 1234", True),
          (figlio["stato"], figlio["prezzo_sats"], figlio["recapito"],
           uno(999, ox["id"]).get("rinato_in") == figlio["ordine"]))
    prova("...e chi l'ha pubblicato lo ritira con un tocco («Non ripubblicarlo»)", 200,
          gesto(999, figlio["id"], "annulla").status_code)
    prova("niente sull'indirizzo: resta preso", "preso",
          gesto(999, oid, "controlla").json()["stato"])
    banco.DETTO.clear()
    paga(oa, confermata=False)
    d = gesto(999, oid, "controlla").json()
    prova("visti ma non confermati: ancora preso, e lo si vede",
          ("preso", 101080, 0), (d["stato"], d["visti_sats"], d["ricevuti_sats"]))
    # (19 nov 2026, Andrea alla prova: «non arriva neanche un messaggio»)
    prova("IL DEPOSITO VISTO SI DICE: a chi ha depositato «non depositare di nuovo», a "
          "chi compra «non mandare ancora niente»; una seconda occhiata non lo ripete",
          (True, True, 1),
          (detto_a(999, "La rete ha visto il tuo deposito"),
           detto_a(888, "Non mandare ancora niente"),
           (gesto(888, oid, "controlla"),
            sum(1 for x in banco.DETTO if "La rete ha visto il tuo deposito" in str(x)))[1]))
    prova("...e ora nessuno dei due annulla: 409", [409, 409],
          [gesto(999, oid, "annulla").status_code,
           gesto(888, oid, "annulla").status_code])
    paga(oa, quanto=100000)
    prova("confermati ma meno del dovuto: ancora preso", "preso",
          gesto(888, oid, "controlla").json()["stato"])
    prova("gli euro non si mandano prima del deposito: 409", 409,
          gesto(888, oid, "euro-inviati").status_code)
    banco.DETTO.clear()
    paga(oa)
    d = gesto(888, oid, "controlla").json()
    prova("confermati tutti: depositato, con la sua moneta", ("depositato", 1),
          (d["stato"], len(d["utxo"])))
    prova("...chi compra sa di mandare gli euro, chi vende di aspettarli",
          (True, True), (detto_a(888, "deposito di garanzia 2-di-3"),
                         detto_a(999, "Deposito confermato")))
    od = uno(888, oid)
    prova("IL TEMPO PER PAGARE (17 nov 2026; 24 ore anche in euro dalla sera): 24 ore dal "
          "deposito confermato, e tutt'e due lo leggono nell'avviso; il tempo del bonifico "
          "non e' ancora partito",
          (24, od["depositato_il"] + 24 * 3600, True, True, 0, 48),
          (od["ore_pagamento"], od["paga_entro"], detto_a(888, "Hai 24 ore"),
           detto_a(999, "Chi compra ha <b>24 ore</b>"), od["bonifico_entro"], od["ore_bonifico"]))

    # ---- 5) gli euro e le due firme --------------------------------------
    print("\n[gli euro, poi la prima e la seconda firma]")
    prova("«ho inviato gli euro» lo dice chi compra bitcoin: 403 a chi vende",
          403, gesto(999, oid, "euro-inviati").status_code)
    banco.DETTO.clear()
    prova("...Alan lo dice: euro_inviati, e Andrea e' avvisato", (200, True),
          (gesto(888, oid, "euro-inviati").status_code, detto_a(999, "dice di averti inviato")))
    prova("...una volta sola: 409", 409, gesto(888, oid, "euro-inviati").status_code)
    o = uno(999, oid)
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, [(o["rimborso"], 100780)], 999).to_string())
    prova("Alan non ha ancora scelto dove ricevere: la liberazione aspetta "
          "(409), i sats restano nel 2-di-3", (409, True),
          (r.status_code, "non ha ancora scelto dove ricevere" in r.json()["detail"]))
    come(888)
    prova("Alan sceglie il suo wallet (firmato dal suo seme)...", 200,
          c.post("/api/onchain/incasso", json={
              "tipo": "xpub", "valore": vpub,
              "firma": firma_dest(888, "xpub", vpub)}).status_code)
    o = uno(999, oid)
    prova("...e lo scambio preso prima prende la destinazione: il primo "
          "indirizzo del suo wallet", dal_wallet(0), o["incasso"])
    giusto = [(o["incasso"], 100000), (o["rimborso"], 101080 - 100000 - 300)]
    prova("i sats li libera chi vende bitcoin: Alan che prova a liberarseli "
          "da solo trova 403", 403,
          gesto(888, oid, "proposta", verso="venditore",
                psbt=psbt_di(uno(888, oid), giusto, 888).to_string()).status_code)
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, giusto).to_string())
    prova("senza la firma di chi propone: 400", (400, True),
          (r.status_code, "manca la tua firma" in r.json()["detail"]))
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, [(o["incasso"], 99000), giusto[1]], 999).to_string())
    prova("a chi compra meno del prezzo: 400 (lo stesso giudice del mercatino)",
          (400, True), (r.status_code, "esattamente il prezzo" in r.json()["detail"]))
    banco.DETTO.clear()
    r = gesto(999, oid, "proposta", verso="venditore",
              psbt=psbt_di(o, giusto, 999).to_string())
    prova("la proposta giusta passa, e Alan e' chiamato a co-firmare", (200, True),
          (r.status_code, detto_a(888, "seconda firma")))
    ob = uno(888, oid)
    prova("...Alan la vede: verso venditore, non sua", ("venditore", False),
          (ob["proposta"]["verso"], ob["proposta"]["mia"]))
    prova("chi ha proposto non mette anche la seconda: 409", 409,
          gesto(999, oid, "firma", tx=tx_nuda(uno(999, oid))).status_code)
    prova("una transazione diversa da quella proposta: 400", 400,
          gesto(888, oid, "firma", tx=cofirma_storta(ob, 888, radice, PSBT,
                                                      finalize_psbt, psbt_di)).status_code)
    banco.DETTO.clear()
    r = gesto(888, oid, "firma", tx=cofirma(888, ob))
    prova("la seconda firma di Alan: trasmessa, rilasciato, txid",
          (200, "rilasciato", 1, True),
          (r.status_code, r.json()["stato"], len(INVIATE),
           r.json()["txid"] == uno(999, oid)["txid_uscita"]))
    prova("...chiuso per tutt'e due, avvisati", ("rilasciato", True, True),
          (uno(888, oid)["stato"], detto_a(999, "concluso"), detto_a(888, "concluso")))
    # LO SCAMBIO ON-CHAIN COME QUELLO LIGHTNING (17 nov 2026)
    prova("...l'avviso invita tutt'e due alla recensione, come su Lightning",
          (True, True), (detto_a(888, "Lascia una recensione"),
                         detto_a(999, "Lascia una recensione")))
    ordine1 = uno(999, oid)["ordine"]
    con = SRV.db()
    esiti = sorted(tuple(r) for r in con.execute(
        "SELECT tg_id, esito, ruolo FROM p2p_esiti WHERE ordine=?", (ordine1,)))
    con.close()
    prova("...e conta nella reputazione di tutt'e due: chi deposita vende, chi "
          "riceve compra", [(888, "completato", "compra"), (999, "completato", "vende")],
          esiti)
    come(888)
    r1 = c.post("/api/p2p/recensibile", json={"ordine": ordine1}).json()
    r2 = c.post("/api/p2p/recensione", json={"ordine": ordine1, "voto": 5,
                                             "commento": "Tutto liscio"})
    r3 = c.post("/api/p2p/recensibile", json={"ordine": ordine1}).json()
    con = SRV.db()
    fb = con.execute("SELECT da_tg_id, per_tg_id, voto FROM feedback WHERE scambio=?",
                     (ordine1,)).fetchone()
    con.close()
    prova("LA RECENSIONE ON-CHAIN: Alan puo', la lascia (va ad Andrea), poi "
          "risulta lasciata", (True, 200, True, False, (888, 999, 5)),
          (r1["si"], r2.status_code, r3["gia"], r3["si"], tuple(fb) if fb else None))
    come(777)
    prova("...un terzo non c'entra: per lui lo scambio non esiste", (False, "ignota"),
          (lambda d: (d["si"], d["motivo"]))(
              c.post("/api/p2p/recensibile", json={"ordine": ordine1}).json()))
    prova("dopo: niente da co-firmare, niente da liberare", [409, 409],
          [gesto(888, oid, "firma", tx=cofirma(888, ob)).status_code,
           gesto(999, oid, "proposta", verso="venditore",
                 psbt=psbt_di(o, giusto, 999).to_string()).status_code])
    tx = Transaction.from_string(INVIATE[0])
    prova("la transazione uscita paga il wallet di Alan e il resto ad Andrea",
          sorted([100000, 780]), sorted(v.value for v in tx.vout))

    # ---- 6) compro bitcoin, poi rinuncio: il rimborso ---------------------
    print("\n[lato buy: chi prende deposita; la rinuncia di chi compra]")
    INVIATE.clear()
    r = pubblica(888, lato="buy", sats=50000, euro_cent=4500,
                 metodi=["Satispay"], recapito="")
    ob = r.json()
    prova("Alan pubblica «compro 50.000 sats»: pending", (200, "buy"),
          (r.status_code, ob["lato"]))
    oid2 = ob["id"]
    r = gesto(999, oid2, "prendi", recapito="Revolut @andrea")
    oa = r.json()
    prova("Andrea prende vendendo: deposita lui (compratore del 2-di-3), col "
          "suo recapito", (200, "compratore", "vendo", "Revolut @andrea"),
          (r.status_code, oa["ruolo"], oa["parte"], oa["recapito"]))
    prova("...Alan riceve: ruolo venditore, e legge il recapito",
          ("venditore", "Revolut @andrea"),
          (uno(888, oid2)["ruolo"], uno(888, oid2)["recapito"]))
    prova("il recapito lo cambia solo chi vende bitcoin", [403, 200, "IBAN nuovo"],
          [gesto(888, oid2, "recapito", recapito="x").status_code,
           gesto(999, oid2, "recapito", recapito="IBAN nuovo").status_code,
           uno(888, oid2)["recapito"]])
    paga(oa)
    prova("deposito confermato", "depositato",
          gesto(999, oid2, "controlla").json()["stato"])
    # (20 nov 2026, audit giro 4) svuotato, chi compra non toccherebbe piu'
    # «Ho inviato» e la ronda del recapito nel tempo lo leggerebbe «mai scritto»
    prova("dopo il deposito chi vende non SVUOTA il recapito: 409, e resta quello di prima",
          (409, "IBAN nuovo"),
          (gesto(999, oid2, "recapito", recapito="  ").status_code,
           uno(888, oid2)["recapito"]))
    prova("chi vende bitcoin non propone il rimborso a se stesso: 403", 403,
          gesto(999, oid2, "proposta", verso="compratore",
                psbt=psbt_di(uno(999, oid2), [(oa["rimborso"], 51080 - 300)], 999)
                .to_string()).status_code)
    ob = uno(888, oid2)
    prova("...prima di rinunciare la riga dice ad Alan che ADESSO conterebbe (deposito "
          "confermato, recapito scritto)", True, ob["rinuncia_conta"])
    banco.DETTO.clear()
    r = gesto(888, oid2, "proposta", verso="compratore",
              psbt=psbt_di(ob, [(ob["rimborso"], 51080 - 300)], 888).to_string())
    prova("Alan rinuncia (rimborso a chi ha depositato): 200, Andrea avvisato",
          (200, True), (r.status_code, detto_a(999, "Rimborso proposto")))
    prova("...la seconda firma e' di Andrea: rimborsato", (200, "rimborsato", 1),
          (lambda r: (r.status_code, r.json()["stato"], len(INVIATE)))(
              gesto(999, oid2, "firma", tx=cofirma(999, uno(999, oid2)))))
    tx = Transaction.from_string(INVIATE[0])
    prova("...tutto torna al rimborso di Andrea, meno la rete",
          [(oa["rimborso"], 51080 - 300)],
          [(script.Script(v.script_pubkey.data).address(N), v.value) for v in tx.vout])
    come(888)
    # CHI SI RITIRA DOPO IL DEPOSITO (17 nov 2026 sera, cantiere onchain-
    # ritiro; Andrea: «si prende la penalità e il rischio di un giudizio
    # negativo, punto»). Fino a quel giorno questa prova diceva il
    # contrario: «un rimborso d'accordo non apre la recensione e non conta».
    ord2 = uno(999, oid2)["ordine"]
    k = SRV.db()
    esiti2 = [tuple(x) for x in k.execute(
        "SELECT tg_id, esito, ruolo, dettaglio FROM p2p_esiti WHERE ordine=?", (ord2,))]
    k.close()
    prova("...la rinuncia a deposito confermato e col recapito scritto conta a chi si e' "
          "ritirato: UN «mancato», a lui solo, e nessun «completato»",
          [(888, "mancato", "compra", "onchain-rinuncia")], esiti2)
    prova("...glielo dice il bot con la riga del conto del Lightning, e a chi aveva "
          "depositato dice che puo' lasciare una recensione",
          (True, True, False),
          (detto_a(888, "Questo conta come scambio non completato"),
           detto_a(999, "puoi lasciargli una recensione"),
           detto_a(888, "puoi lasciargli una recensione")))
    come(999)
    da_chi_vende = c.post("/api/p2p/recensibile", json={"ordine": ord2}).json()
    come(888)
    da_chi_rinuncia = c.post("/api/p2p/recensibile", json={"ordine": ord2}).json()
    prova("...la recensione e' A SENSO UNICO: la lascia chi aveva bloccato i sats, non chi "
          "si e' ritirato", ((True, ""), (False, "non_conclusa")),
          ((da_chi_vende["si"], da_chi_vende["motivo"]),
           (da_chi_rinuncia["si"], da_chi_rinuncia["motivo"])))
    prova("...e la riga dello scambio lo porta a tutti e due, ognuno dal suo lato",
          (("altro", "onchain-rinuncia"), ("io", "onchain-rinuncia")),
          ((uno(999, oid2)["non_completato"], uno(999, oid2)["non_completato_perche"]),
           (uno(888, oid2)["non_completato"], uno(888, oid2)["non_completato_perche"])))

    # ---- 7) la disputa e la firma di Barattolo ----------------------------
    print("\n[la disputa: decide un moderatore, firma Barattolo]")
    INVIATE.clear()
    o3 = pubblica(999, sats=60000, euro_cent=5400, metodi=["Bonifico"]).json()
    oid3 = o3["id"]
    gesto(888, oid3, "prendi")
    oa = uno(999, oid3)
    prova("disputa prima del deposito: 409 (niente da contendere)", 409,
          gesto(999, oid3, "disputa", motivo="x").status_code)
    paga(oa)
    gesto(999, oid3, "controlla")
    gesto(888, oid3, "euro-inviati")
    # Alan propone il rimborso... poi Andrea apre la disputa: la proposta decade
    ob = uno(888, oid3)
    gesto(888, oid3, "proposta", verso="compratore",
          psbt=psbt_di(ob, [(ob["rimborso"], 61080 - 300)], 888).to_string())
    banco.DETTO.clear()
    banco.AVVISI.clear() if hasattr(banco, "AVVISI") else None
    r = gesto(999, oid3, "disputa", motivo="Gli euro non sono mai arrivati")
    oa = uno(999, oid3)
    prova("Andrea apre la disputa: stato disputa, la proposta di parte decade, "
          "Alan e i moderatori avvisati",
          (200, "disputa", None, "io", True, True),
          (r.status_code, oa["stato"], oa["proposta"], oa["disputa"]["da"],
           detto_a(888, "aperto una disputa"),
           any("Disputa P2P on-chain" in t for t in banco.AVVISI)))
    prova("in disputa nessuno propone: 409", 409,
          gesto(999, oid3, "proposta", verso="venditore",
                psbt=psbt_di(oa, [(oa["incasso"], 60000), (oa["rimborso"], 780)], 999)
                .to_string()).status_code)
    come(777)
    ap = c.get("/api/p2p/onchain/moderazione/aperte").json()["dispute"]
    prova("il moderatore terzo la vede, con le parti e SENZA recapito",
          (1, "Andrea", "Alan", False, "Gli euro non sono mai arrivati"),
          (len(ap), ap[0]["parti"]["vende"], ap[0]["parti"]["compra"],
           "recapito" in ap[0], ap[0]["disputa"]["motivo"]))
    prova("una parte non decide il proprio scambio, anche se admin: 403", 403,
          gesto(999, oid3, "decidi", verso="venditore").status_code)
    banco.DETTO.clear()
    r = gesto(777, oid3, "decidi", verso="venditore")
    prova("il terzo decide per chi compra: Barattolo firma, aspetta Alan",
          (200, "venditore", True, True),
          (r.status_code, r.json()["attesa_firma"], detto_a(888, "a tuo favore"),
           detto_a(999, "ragione all'altra parte")))
    ob = uno(888, oid3)
    prova("...Alan vede la proposta di Barattolo (disputa), non sua, verso di lui",
          ("venditore", False, "disputa", "venditore"),
          (ob["proposta"]["verso"], ob["proposta"]["mia"], ob["proposta"]["barattolo"],
           ob["decisione"]["verso"]))
    prova("un verso diverso dopo la firma: 409, una firma data non si ritira",
          (409, True), (lambda r: (r.status_code, "non si ritira" in r.json()["detail"]))(
              gesto(777, oid3, "decidi", verso="compratore")))
    prova("lo stesso verso: gia' firmata", True,
          gesto(777, oid3, "decidi", verso="venditore").json().get("gia_firmata"))
    prova("Andrea (che ha perso) non co-firma: 409", 409,
          gesto(999, oid3, "firma", tx=cofirma(999, uno(999, oid3))).status_code)
    r = gesto(888, oid3, "firma", tx=cofirma(888, ob))
    prova("Alan co-firma la firma di Barattolo: rilasciato", (200, "rilasciato", 1),
          (r.status_code, r.json()["stato"], len(INVIATE)))
    con = SRV.db()
    esiti = sorted(tuple(r) for r in con.execute(
        "SELECT tg_id, esito FROM p2p_esiti WHERE ordine=?", (uno(999, oid3)["ordine"],)))
    con.close()
    prova("...dopo una disputa conta solo a chi ha vinto e ricevuto", [(888, "completato")],
          esiti)
    tx = Transaction.from_string(INVIATE[0])
    # l'indirizzo di Alan e' il TERZO del suo wallet (0 e 1 li hanno presi i
    # due scambi prima: la fila e' una sola), la rete e' la misura di
    # `_onchain_psbt_barattolo`: (11 + 105 + 31 x 2) x 2 sat/vB = 356
    prova("...60.000 al wallet di Alan (il suo terzo indirizzo), il resto ad "
          "Andrea meno la rete che Barattolo ha misurato",
          sorted([(dal_wallet(2), 60000), (oa["rimborso"], 61080 - 60000 - 356)]),
          sorted((script.Script(v.script_pubkey.data).address(N), v.value)
                 for v in tx.vout))
    come(777)
    prova("la coda dei moderatori e' vuota", 0,
          len(c.get("/api/p2p/onchain/moderazione/aperte").json()["dispute"]))

    # ---- 8) l'annullo prima del deposito, e il ritardatario ---------------
    print("\n[annullare prima del deposito; i sats che arrivano dopo]")
    INVIATE.clear()
    o4 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    oid4 = o4["id"]
    prova("nel libro lo ritira solo chi l'ha pubblicato (per gli altri non "
          "esiste nemmeno: 404)", [404, 200],
          [gesto(888, oid4, "annulla").status_code,
           gesto(999, oid4, "annulla").status_code])
    prova("...annullato, fuori dal libro", ("annullato", 0),
          (uno(999, oid4)["stato"], len(libro()["onchain"]["eventi"])))
    o5 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    oid5 = o5["id"]
    gesto(888, oid5, "prendi")
    oa = uno(999, oid5)
    banco.DETTO.clear()
    prova("preso, senza un sats: chi deve depositare annulla quando vuole, "
          "e l'altro lo sa", (200, "annullato", True),
          (gesto(999, oid5, "annulla").status_code, uno(888, oid5)["stato"],
           detto_a(888, "annullato")))
    paga(oa)   # i sats arrivano DOPO l'annullo: il ritardatario
    asyncio.run(SRV._p2p_onchain_controlla(oid5))
    oa = uno(999, oid5)
    prova("i sats arrivati dopo si vedono, lo stato resta annullato",
          ("annullato", 31080), (oa["stato"], oa["ricevuti_sats"]))
    come(777)
    ap = c.get("/api/p2p/onchain/moderazione/aperte").json()["dispute"]
    prova("...e il moderatore lo trova nella coda", [oid5], [x["id"] for x in ap])
    ob = uno(888, oid5)
    prova("chi compra puo' proporre il rimborso anche cosi'", 200,
          gesto(888, oid5, "proposta", verso="compratore",
                psbt=psbt_di(ob, [(ob["rimborso"], 31080 - 300)], 888).to_string())
          .status_code)
    prova("...o decide il moderatore (a favore di chi ha depositato)", 200,
          gesto(777, oid5, "decidi", verso="compratore").status_code)
    prova("Andrea co-firma: rimborsato, e la coda si svuota", ("rimborsato", 0),
          (gesto(999, oid5, "firma", tx=cofirma(999, uno(999, oid5))).json()["stato"],
           (come(777), len(c.get("/api/p2p/onchain/moderazione/aperte").json()["dispute"]))[1]))
    o6 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    gesto(888, o6["id"], "prendi")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET deposito_entro=? WHERE id=?",
                (int(time.time()) - 1, o6["id"]))
    con.commit()
    con.close()
    prova("rinunciare dopo la finestra del deposito, senza sats: si puo'",
          (200, "annullato"),
          (gesto(888, o6["id"], "annulla").status_code, uno(999, o6["id"])["stato"]))
    con = SRV.db()
    figlio = con.execute("SELECT id FROM p2p_onchain_ordini WHERE rinato_da=?",
                         (o6["id"],)).fetchone()
    con.close()
    prova("...e anche questo torna nel libro, e chi l'ha pubblicato lo ritira", (True, 200),
          (figlio is not None, gesto(999, figlio["id"], "annulla").status_code if figlio else 0))

    # IL DEPOSITO COL TEMPO DI CHI PUBBLICA (19 nov 2026, cantiere onchain-
    # tempo-deposito; Andrea: «Sì, deve inviarlo entro quel tempo», minimo 30)
    print("\n[il deposito col tempo di chi pubblica]")
    prima_tempo = SRV.P2P_TEMPO_PER_PAGARE
    SRV.P2P_TEMPO_PER_PAGARE = True
    o6b = pubblica(999, sats=30000, euro_cent=2700, metodi=["Revolut"],
                   minuti_pagare=15).json()
    banco.DETTO.clear()
    gesto(888, o6b["id"], "prendi")
    ob6 = uno(999, o6b["id"])
    prova("una vendita on-chain con 15 minuti ne vale 30, e chi vende ha 30 minuti per "
          "INVIARE il deposito, detto nell'avviso della presa",
          (30, 1800, True),
          (ob6["minuti_pagamento"], ob6["deposito_entro"] - ob6["preso_il"],
           detto_a(999, "Hai 30 minuti</b> per inviarlo")))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET preso_il=?, deposito_entro=? WHERE id=?",
                (int(time.time()) - 1800 - 6 * 60, int(time.time()) - 6 * 60, o6b["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    ob6 = uno(999, o6b["id"])
    con = SRV.db()
    rinato6 = con.execute("SELECT id FROM p2p_onchain_ordini WHERE rinato_da=?",
                          (o6b["id"],)).fetchone()
    con.close()
    prova("finito il tempo senza un sats in rete: la ronda annulla, lo dice a tutt'e due, "
          "e l'ordine NON torna nel libro (era chi vende a dover inviare)",
          ("annullato", "invio-scaduto", True, True, None),
          (ob6["stato"], ob6.get("chiuso_perche"),
           detto_a(999, "Il tempo per inviare il deposito è finito"),
           detto_a(888, "Chi vende non ha inviato il deposito"), rinato6))
    SRV.P2P_TEMPO_PER_PAGARE = prima_tempo

    # ---- 9) la scadenza nel libro e la ronda ------------------------------
    print("\n[la ronda: la scadenza nel libro]")
    o7 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET scade=? WHERE id=?",
                (int(time.time()) - 1, o7["id"]))
    con.commit()
    con.close()
    SRV._p2p_onchain_rifai_foto()
    prova("scaduto: sparisce dal libro prima ancora della ronda", 0,
          len(libro()["onchain"]["eventi"]))
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...e la ronda lo marca scaduto", "scaduto", uno(999, o7["id"])["stato"])
    prova("prendere uno scaduto: 409", 409, gesto(888, o7["id"], "prendi").status_code)

    # IL TEMPO PER PAGARE FINITO (17 nov 2026): la ronda avvisa, una volta
    print("\n[la ronda: il tempo per pagare finito]")
    o8 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    gesto(888, o8["id"], "prendi")
    paga(uno(999, o8["id"]))
    gesto(999, o8["id"], "controlla")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 25 * 3600, int(time.time()) - 26 * 3600, o8["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    # (20 nov 2026, ritorno-da-solo-oc) la strada di prima, a leva spenta:
    # quella accesa e' il pezzo subito sotto
    prima_ritorno = SRV.P2P_ONCHAIN_RITORNO_DA_SOLO
    SRV.P2P_ONCHAIN_RITORNO_DA_SOLO = False
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("25 ore dopo il deposito, senza «Ho inviato», col ritorno da solo SPENTO: la "
          "ronda avvisa tutt'e due, e lo scambio resta depositato (niente si annulla)",
          (True, True, "depositato"),
          (detto_a(999, "Il tempo per pagare è finito"),
           detto_a(888, "Il tempo per pagare è finito"), uno(999, o8["id"])["stato"]))
    prova("...e a chi paga non arriva anche il terzo promemoria: il tempo finito lo "
          "ha superato", False, detto_a(888, "Promemoria") or detto_a(888, "Mancano quattro ore"))
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...la ronda dopo non lo ripete", (False, False),
          (detto_a(999, "tempo per pagare"), detto_a(888, "tempo per pagare")))
    SRV.P2P_ONCHAIN_RITORNO_DA_SOLO = prima_ritorno
    # ...e la leva riaccesa chiude anche questo, che aveva gia' avuto
    # l'avviso: la ronda riprova a ogni giro
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...riaccesa la leva, la ronda dopo lo chiude lei (tempo-scaduto)",
          ("annullato", "tempo-scaduto"),
          (uno(999, o8["id"])["stato"], uno(999, o8["id"]).get("chiuso_perche")))

    # IL RITORNO DA SOLO (20 nov 2026, cantiere ritorno-da-solo-oc; Andrea:
    # «nell'on-chain deve succedere uguale al lighting», scheda «Da solo,
    # come Lightning»)
    print("\n[la ronda: il tempo per pagare finito, i sats tornano da soli]")
    prova("di serie la leva e' accesa", True, SRV.P2P_ONCHAIN_RITORNO_DA_SOLO)
    o8b = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    prova("il libro di chi prende lo dice (la pagina scrive la frase del Lightning)", True,
          next((e for e in libro(888)["onchain"]["eventi"] if e.get("id") == o8b["id"]),
               {}).get("ritorno_da_solo"))
    gesto(888, o8b["id"], "prendi")
    banco.DETTO.clear()
    paga(uno(999, o8b["id"]))
    gesto(999, o8b["id"], "controlla")
    prova("al deposito confermato chi paga legge la regola del Lightning, non la disputa",
          (True, False), (detto_a(888, "allo scadere lo scambio scade e l'ordine torna nel libro"),
                          detto_a(888, "poi chi vende può aprire una disputa")))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 2 * 3600, int(time.time()) - 3 * 3600, o8b["id"]))
    con.commit()
    con.close()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("col tempo che corre la ronda non chiude niente", "depositato",
          uno(999, o8b["id"])["stato"])
    rim8 = uno(999, o8b["id"])["rimborso"]
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=?, rimborso=''"
                " WHERE id=?", (int(time.time()) - 25 * 3600, int(time.time()) - 26 * 3600,
                                o8b["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("tempo finito ma SENZA l'indirizzo di ritorno: non si firma niente, resta "
          "depositato e arriva l'avviso di prima (disputa)",
          ("depositato", True, ""),
          (uno(999, o8b["id"])["stato"], detto_a(888, "Il tempo per pagare è finito"),
           uno(999, o8b["id"]).get("chiuso_perche") or ""))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET rimborso=? WHERE id=?",
                (rim8, o8b["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    d8 = uno(999, o8b["id"])
    prova("scritto l'indirizzo, la ronda dopo chiude: annullato per tempo-scaduto, e "
          "Barattolo ha firmato il rimborso senza moderatore e senza bottone",
          ("annullato", "tempo-scaduto", "compratore", "tempo-scaduto"),
          (d8["stato"], d8.get("chiuso_perche"), (d8.get("proposta") or {}).get("verso"),
           (d8.get("proposta") or {}).get("barattolo")))
    prova("...chi compra sa che e' chiuso e di non mandare niente, chi vende di mettere la "
          "seconda firma; a nessuno «libera i sats» (lo scambio e' gia' chiuso)",
          (True, True, True, False),
          (detto_a(888, "Il tempo per pagare è finito"), detto_a(888, "non mandare niente"),
           detto_a(999, "Metti la seconda firma"), detto_a(999, "libera i sats")))
    uscite = PSBT.from_string(d8["proposta"]["psbt"]).tx.vout
    prova("...un'uscita sola, verso il wallet di chi ha depositato", (1, d8["rimborso"]),
          (len(uscite), script.Script(uscite[0].script_pubkey.data).address(N)))
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...la ronda dopo non firma di nuovo e non ridice niente; «Ho inviato» adesso "
          "non passa piu'", (False, False, 409),
          (detto_a(999, "Barattolo ha firmato"), detto_a(888, "tempo per pagare"),
           gesto(888, o8b["id"], "euro-inviati").status_code))
    r = gesto(999, o8b["id"], "firma", tx=cofirma(999, uno(999, o8b["id"])))
    con = SRV.db()
    figlio8 = con.execute("SELECT id FROM p2p_onchain_ordini WHERE rinato_da=?",
                          (o8b["id"],)).fetchone()
    con.close()
    prova("la seconda firma di chi ha depositato: rimborsato, a chi non ha pagato il "
          "«non completato», e l'ordine torna nel libro",
          (200, "rimborsato", "altro", True),
          (r.status_code, r.json()["stato"], uno(999, o8b["id"]).get("non_completato") or "",
           figlio8 is not None))
    if figlio8:
        gesto(999, figlio8["id"], "annulla")
    # dopo «Ho inviato» la ronda non tocca niente
    o8c = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    gesto(888, o8c["id"], "prendi")
    paga(uno(999, o8c["id"]))
    gesto(999, o8c["id"], "controlla")
    gesto(888, o8c["id"], "euro-inviati")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 25 * 3600, int(time.time()) - 26 * 3600, o8c["id"]))
    con.commit()
    con.close()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("con «Ho inviato gli euro» toccato la ronda non riprende niente: resta a chi "
          "vende liberare (o alla disputa)", ("euro_inviati", ""),
          (uno(999, o8c["id"])["stato"], uno(999, o8c["id"]).get("chiuso_perche") or ""))
    # non resti aperto: conta nel tetto degli scambi a testa, piu' avanti
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='rilasciato', chiuso_il=? WHERE id=?",
                (int(time.time()), o8c["id"]))
    con.commit()
    con.close()
    # I PROMEMORIA (17 nov 2026, cantiere onchain-chat-sollecito)
    print("\n[la ronda: i promemoria a chi paga e a chi libera]")
    o9 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    gesto(888, o9["id"], "prendi")
    paga(uno(999, o9["id"]))
    gesto(999, o9["id"], "controlla")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 2 * 3600, int(time.time()) - 3 * 3600, o9["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("due ore dopo il deposito: a chi paga il primo promemoria (24 ore in euro), a "
          "chi vende niente", (True, True, False),
          (detto_a(888, "Promemoria: i sats sono nel 2-di-3 da un'ora"),
           detto_a(888, "Hai 24 ore in tutto"), detto_a(999, "Promemoria")))
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...la ronda dopo non lo ripete", False, detto_a(888, "Promemoria"))
    prova("«Ho inviato gli euro» ferma quelli di chi paga", 200,
          gesto(888, o9["id"], "euro-inviati").status_code)
    o9d = uno(999, o9["id"])
    prova("...e da li' parte IL TEMPO DEL BONIFICO (17 nov 2026 sera): 48 ore a chi vende "
          "per vederlo arrivare, scritte nell'avviso e nella riga dello scambio",
          (True, o9d["euro_inviati_il"] + 48 * 3600, 48),
          (detto_a(999, "Un bonifico può metterci fino a 48 ore"),
           o9d["bonifico_entro"], o9d["ore_bonifico"]))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, euro_inviati_il=? WHERE id=?",
                (int(time.time()) - 30 * 3600, int(time.time()) - 7 * 3600, o9["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("sette ore dopo il «Ho inviato»: a chi vende il secondo promemoria del Lightning "
          "(uno solo, non due di fila), a chi paga niente piu'", (True, 1, False),
          (detto_a(999, "Sono passate sei ore da quando chi compra ha detto di aver"),
           sum(1 for tg, t in banco.DETTO if tg == 999 and any(
               x in t for x in ("Promemoria", "Sono passate sei ore", "Venti ore"))),
           detto_a(888, "Sono passate sei ore")))
    # LE 48 ORE DEL BONIFICO PASSATE (17 nov 2026 sera): la ronda lo dice
    # a tutti e due, una volta, e non annulla ne' libera niente
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET euro_inviati_il=? WHERE id=?",
                (int(time.time()) - 47 * 3600, o9["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("47 ore dopo «Ho inviato»: del tempo del bonifico ancora niente", (False, False),
          (detto_a(999, "Sono passate 48 ore"), detto_a(888, "Sono passate 48 ore")))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET euro_inviati_il=? WHERE id=?",
                (int(time.time()) - 49 * 3600, o9["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("49 ore dopo «Ho inviato», senza rilascio: la ronda lo dice a tutt'e due e a "
          "tutt'e due indica la disputa; lo scambio resta «euro inviati»",
          (True, True, True, True, "euro_inviati"),
          (detto_a(999, "Sono passate 48 ore da «Ho inviato gli euro»"),
           detto_a(888, "Sono passate 48 ore da «Ho inviato gli euro»"),
           detto_a(999, "apri una disputa"), detto_a(888, "«⚖️ Apri una disputa»"),
           uno(999, o9["id"])["stato"]))
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...la ronda dopo non lo ripete", (False, False),
          (detto_a(999, "Sono passate 48 ore"), detto_a(888, "Sono passate 48 ore")))
    # fuori dai piedi: i tetti qui sotto contano gli scambi aperti
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='rimborsato', chiuso_il=? WHERE id IN (?, ?)",
                (int(time.time()), o8["id"], o9["id"]))
    con.commit()
    con.close()

    # ---- 10) i tetti ---------------------------------------------------------
    print("\n[i tetti: ordini aperti, euro]")
    aperti = [pubblica(999, sats=20000, euro_cent=1800, metodi=["Bonifico"]).status_code
              for _ in range(SRV.P2P_ONCHAIN_APERTI_MAX)]
    r = pubblica(999, sats=20000, euro_cent=1800, metodi=["Bonifico"])
    prova(f"al massimo {SRV.P2P_ONCHAIN_APERTI_MAX} scambi aperti a testa: poi 409",
          ([200] * SRV.P2P_ONCHAIN_APERTI_MAX, 409, True),
          (aperti, r.status_code, "aperti" in r.json()["detail"]))
    SRV.P2P_MAX_EURO = 0
    prova("a tetto euro spento la cifra grande passa dal giudice", "",
          SRV.p2p_onchain_giudica_nuovo("sell", 50000, 30000, ["a"], "", 0, 0))
    SRV.P2P_MAX_EURO = 250

    # ---- 11) la leva spenta, di nuovo ----------------------------------------
    print("\n[la leva spenta a scambi in corso]")
    SRV.P2P_ONCHAIN_ATTIVO = False
    prova("le rotte dicono 404 e il libro perde la busta", ([404, 404, 404], False),
          ([gesto(999, oid, "controlla").status_code,
            (come(999), c.get("/api/p2p/onchain/miei").status_code)[1],
            (come(999), c.get(f"/api/p2p/onchain/{oid}").status_code)[1]],
           "onchain" in libro(999)))
    prova("...e la ronda non tocca niente", None, asyncio.run(SRV._p2p_onchain_ronda()))
    SRV.P2P_ONCHAIN_ATTIVO = True

    # ---- 11-bis) «Togli» dove si riceve (30 ott 2026, Andrea e Alan) ----------
    print("\n[togliere dove si riceve: i prossimi scambi aspettano una scelta]")
    come(888)
    prova("Alan toglie il suo wallet di ricezione: 200, e /api/me non lo dice piu'",
          (200, ""), (c.post("/api/onchain/incasso", json={"tipo": "barattolo"}).status_code,
                      c.get("/api/me").json().get("onchain_incasso") or ""))
    con = SRV.db()
    try:
        xa = con.execute("SELECT xpub FROM onchain_xpub WHERE tg_id=888").fetchone()[0]
        vuoto = SRV._p2p_onchain_incasso_di(con, 888, xa)
    finally:
        con.close()
    prova("...e per uno scambio nuovo l'incasso nasce vuoto: la pagina glielo chiede",
          ("", "", "", "", 0), vuoto)

    # ---- 11-ter) l'indirizzo al volo, solo per lo scambio (30 ott 2026, Andrea)
    print("\n[l'indirizzo al volo: vale per lo scambio, il Profilo non si tocca]")
    # il giro ha gia' riempito i cinque posti aperti di Andrea: qui se ne
    # allarga uno (che il tetto esista lo prova la sezione sua)
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto + 5
    o4 = pubblica(999, sats=60000, euro_cent=5400, metodi=["Bonifico"]).json()
    oid4 = o4["id"]
    gesto(888, oid4, "prendi")
    qui = dal_wallet(7)
    prova("Alan prende senza un posto dove ricevere: l'incasso e' vuoto", "",
          uno(888, oid4)["incasso"])
    prova("l'indirizzo dello scambio lo scrive solo chi compra: 403 ad Andrea", 403,
          gesto(999, oid4, "incasso", valore=qui,
                firma=firma_dest(999, "indirizzo", qui)).status_code)
    prova("...qui solo un indirizzo: la chiave del conto e' un 400", 400,
          gesto(888, oid4, "incasso", valore=vpub,
                firma=firma_dest(888, "xpub", vpub)).status_code)
    prova("...firmato da un altro seme: 400", 400,
          gesto(888, oid4, "incasso", valore=qui,
                firma=firma_dest(999, "indirizzo", qui)).status_code)
    r = gesto(888, oid4, "incasso", valore=qui, firma=firma_dest(888, "indirizzo", qui))
    prova("...giusto e firmato dal suo seme: 200, lo scambio riceve li', "
          "e il Profilo resta vuoto",
          (200, qui, "indirizzo", ""),
          (r.status_code, uno(888, oid4)["incasso"],
           (uno(888, oid4)["destinazione"] or {}).get("tipo"),
           c.get("/api/me").json().get("onchain_incasso") or ""))
    prova("...e scritto non si cambia: 409", 409,
          gesto(888, oid4, "incasso", valore=dal_wallet(8),
                firma=firma_dest(888, "indirizzo", dal_wallet(8))).status_code)
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 11-quater) il foglio di Lightning (30 ott 2026, cantiere oc-identico,
    # Andrea: «deve essere identico allaltro»): prezzo di mercato col premio,
    # chi puo' prendere, la pausa, il paracadute
    print("\n[il foglio di Lightning: mercato, chi può prendere, pausa, paracadute]")
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = 100

    def cambio(eur, eta=0):
        SRV._cambio_cache["valori"]["eur"] = float(eur)
        SRV._cambio_cache["quando"] = time.time() - eta

    def riga_db(oid):
        con = SRV.db()
        try:
            return dict(con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?",
                                    (oid,)).fetchone())
        finally:
            con.close()

    def nel_libro(oid):
        return next((e for e in libro(888)["onchain"]["eventi"] if e["id"] == oid), None)
    cambio(90000)
    prova("i sats a mercato: la formula del coordinatore (90 € a 90.000 €/BTC, "
          "premio +2% = 98.000; −2% = 102.000; senza cambio 0)",
          (98000, 102000, 0),
          (SRV.p2p_onchain_sats_mercato(9000, 2, 90000),
           SRV.p2p_onchain_sats_mercato(9000, -2, 90000),
           SRV.p2p_onchain_sats_mercato(9000, 2, 0)))
    r = pubblica(999, tipo="mercato", premio=2, sats=None)
    om = r.json()
    prova("a mercato: nasce senza sats (0 fino alla presa), col premio e la stima "
          "al cambio di adesso", (200, True, 2, 0, 98000),
          (r.status_code, om.get("mercato"), om.get("premio"), om.get("sats"),
           om.get("stima")))
    e = nel_libro(om["id"]) or {}
    prova("...nel libro: mercato, premio, stima; niente paracadute a chi guarda",
          (True, 2, 98000, 0, False), (e.get("mercato"), e.get("premio"),
                                       e.get("stima"), e.get("sats"), "paracadute" in e))
    tags = {t[0]: t[1:] for t in SRV.p2p_onchain_tags(riga_db(om["id"]), 1000)}
    prova("...e il 38383 dice amt 0 e premium 2, come un ordine a mercato di Mostro",
          (["0"], ["2"]), (tags["amt"], tags["premium"]))
    prova("i no del mercato: pochi euro (sotto il minimo al cambio), premio "
          "oltre il 20%, tipo inventato", [400, 400, 400],
          [pubblica(999, tipo="mercato", euro_cent=500).status_code,
           pubblica(999, tipo="mercato", premio=25).status_code,
           pubblica(999, tipo="baratto").status_code])
    cambio(100000, eta=3600)
    r = gesto(888, om["id"], "prendi")
    prova("alla presa con un cambio vecchio di un'ora: 503, e l'ordine resta nel libro",
          (503, "pending"), (r.status_code, riga_db(om["id"])["stato"]))
    cambio(100000)
    r = gesto(888, om["id"], "prendi")
    d = riga_db(om["id"])
    prova("alla presa i sats nascono al cambio di ADESSO (90 € a 100.000 = 90.000, "
          "−2% = 88.200), prima dell'indirizzo, e l'importo e' prezzo + margine",
          (200, "preso", 88200, 88200 + d["margine_sats"], 100000.0, True),
          (r.status_code, d["stato"], d["prezzo_sats"], d["importo_sats"],
           d["cambio_presa"], d["indirizzo_id"] > 0))
    prova("...e chi ha preso legge i sats veri", (88200, 88200),
          (uno(888, om["id"])["sats"], r.json().get("sats")))
    # chi puo' prendere
    of = pubblica(999, filtro=3).json()
    e = nel_libro(of["id"]) or {}
    r = gesto(888, of["id"], "prendi")
    prova("«3+ scambi»: il libro lo dice, e chi non ne ha tre non prende (409 "
          "col perche')", (3, 409, True, "pending"),
          (e.get("filtro"), r.status_code, "almeno 3 scambi" in r.json().get("detail", ""),
           riga_db(of["id"])["stato"]))
    prova("...una soglia fuori dal catalogo vale «tutti»", 0,
          pubblica(999, filtro=4).json().get("filtro"))
    # la pausa di chi pubblica
    op = pubblica(999).json()
    adesso = int(time.time())
    con = SRV.db()
    SRV._scrivi_pausa_p2p(con, 999, {"fasce": [], "fuso": "Europe/Rome", "scarto": 0,
                                     "una_da": adesso - 60, "una_fino": adesso + 3600},
                          adesso)
    con.close()
    SRV._p2p_onchain_rifai_foto()
    e = nel_libro(op["id"]) or {}
    r = gesto(888, op["id"], "prendi")
    prova("chi ha pubblicato e' in pausa: la card dice fino a quando, e la presa "
          "dice di no", (adesso + 3600, 409, True),
          (e.get("pausa_fino"), r.status_code, "pausa" in r.json().get("detail", "")))
    con = SRV.db()
    SRV._scrivi_pausa_p2p(con, 999, {"fasce": [], "fuso": "", "scarto": 0,
                                     "una_da": 0, "una_fino": 0}, adesso)
    con.close()
    SRV._p2p_onchain_rifai_foto()
    prova("...finita la pausa la card torna normale e si prende", (False, 200),
          ("pausa_fino" in (nel_libro(op["id"]) or {}),
           gesto(888, op["id"], "prendi").status_code))
    # il paracadute
    SRV.P2P_PARACADUTE = False
    prova("a leva del paracadute spenta la soglia non si scrive", 0,
          pubblica(999, paracadute=5).json().get("paracadute"))
    SRV.P2P_PARACADUTE = True
    cambio(100000)
    o5 = pubblica(999, paracadute=5).json()
    o20 = pubblica(999, paracadute=20).json()
    prova("col paracadute al 5%: la scheda di chi pubblica lo porta, il libro no, "
          "e la partenza la scrive il server", (5, False, 100000.0),
          (uno(999, o5["id"])["paracadute"], "paracadute" in (nel_libro(o5["id"]) or {}),
           riga_db(o5["id"])["para_partenza"]))
    prima = len(BOTTONI)
    # una lettura DOPO quella della partenza: nello stesso secondo il
    # giudice la prenderebbe per la stessa (e ha ragione)
    cambio(106000)
    SRV._cambio_cache["quando"] = time.time() + 1
    asyncio.run(SRV._p2p_onchain_ronda())
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("una lettura oltre il 5% (+6%), contata una volta sola anche con due "
          "giri: l'ordine resta nel libro", ("pending", 1),
          (riga_db(o5["id"])["stato"], riga_db(o5["id"])["para_oltre"]))
    SRV._cambio_cache["quando"] = time.time() + 2
    asyncio.run(SRV._p2p_onchain_ronda())
    d5 = riga_db(o5["id"])
    nuovi = BOTTONI[prima:]
    prova("la seconda lettura di fila oltre la soglia lo annulla: annullato dal "
          "paracadute, fuori dal libro, e chi l'ha pubblicato e' avvisato col "
          "bottone dello scambio", ("annullato", "paracadute", None, True),
          (d5["stato"], d5["chiuso_perche"], nel_libro(o5["id"]),
           any(chi == 999 and "paracadute si è aperto" in t and b
               and b[1].endswith(o5["ordine"]) for chi, t, b in nuovi)))
    prova("...e quello al 20% resta nel libro", "pending", riga_db(o20["id"])["stato"])
    prova("...la scheda dice perche' si e' chiuso", "paracadute",
          uno(999, o5["id"]).get("chiuso_perche"))
    # (17 nov 2026, cantiere paracadute-su-giu) due soglie, una per verso
    cambio(100000)
    o_giu = pubblica(999, paracadute={"su": 0, "giu": 5}).json()
    o_su = pubblica(999, paracadute={"su": 10, "giu": 0}).json()
    prova("DUE SOGLIE: la scheda di chi pubblica le porta una per verso, e la riga le "
          "tiene", [(0, 5), (10, 0), (0, 5, 5), (10, 0, 10)],
          [(uno(999, o_giu["id"])["paracadute_su"], uno(999, o_giu["id"])["paracadute_giu"]),
           (uno(999, o_su["id"])["paracadute_su"], uno(999, o_su["id"])["paracadute_giu"]),
           tuple(riga_db(o_giu["id"])[k] for k in ("para_su", "para_giu", "paracadute")),
           tuple(riga_db(o_su["id"])[k] for k in ("para_su", "para_giu", "paracadute"))])
    prova("...e l'ordine di prima (una soglia sola) le ha uguali", (5, 5),
          (uno(999, o5["id"])["paracadute_su"], uno(999, o5["id"])["paracadute_giu"]))
    cambio(112000)
    SRV._cambio_cache["quando"] = time.time() + 3
    asyncio.run(SRV._p2p_onchain_ronda())
    SRV._cambio_cache["quando"] = time.time() + 4
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("BTC +12% due volte: si annulla «se sale 10%», NON «se scende 5%»",
          ("annullato", "pending"), (riga_db(o_su["id"])["stato"], riga_db(o_giu["id"])["stato"]))
    cambio(94000)
    SRV._cambio_cache["quando"] = time.time() + 5
    asyncio.run(SRV._p2p_onchain_ronda())
    SRV._cambio_cache["quando"] = time.time() + 6
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("BTC −6% due volte: ora si annulla «se scende 5%»", ("annullato", "paracadute"),
          (riga_db(o_giu["id"])["stato"], riga_db(o_giu["id"])["chiuso_perche"]))
    SRV.P2P_PARACADUTE = False
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 11-sexies) il rimborso che non si incaglia (17 nov 2026, cantiere
    # onchain-rimborso-liscio; un utente all'assistenza: «la persona che ha
    # depositato deve indicare dove ricevere di ritorno i sats») ---------------
    print("\n[il rimborso che non si incaglia: l'indirizzo al volo di chi "
          "deposita, e la rinuncia registrata]")
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    # il freno delle destinazioni (10 l'ora) il giro l'ha gia' consumato:
    # qui si prova la rotta, non il freno
    SRV.FRENI["onchain_incasso"] = (1000, 3600)
    come(888)
    c.post("/api/onchain/incasso", json={"tipo": "barattolo"})   # Alan senza wallet
    INVIATE.clear()
    oid7 = pubblica(888, sats=70000, euro_cent=6300, metodi=["Bonifico"]).json()["id"]
    gesto(999, oid7, "prendi")
    o7 = uno(888, oid7)
    prova("Alan vende senza un wallet suo: lo scambio nasce col rimborso vuoto",
          ("compratore", "", None, 0),
          (o7["ruolo"], o7["rimborso"], o7["destinazione_rimborso"],
           o7["rinuncia_chiesta_il"]))
    prova("prima del deposito non c'e' niente a cui rinunciare: 409", 409,
          gesto(999, oid7, "rinuncia-chiesta").status_code)
    torna = dal_wallet(31)
    prova("dove tornano i sats lo scrive solo chi deposita: 403 a chi compra", 403,
          gesto(999, oid7, "rimborso", valore=torna,
                firma=firma_dest(999, "indirizzo", torna)).status_code)
    prova("...solo un indirizzo (la chiave del conto e' del Profilo): 400", 400,
          gesto(888, oid7, "rimborso", valore=vpub,
                firma=firma_dest(888, "xpub", vpub)).status_code)
    prova("...firmato da un altro seme: 400, e non si scrive niente", (400, ""),
          (gesto(888, oid7, "rimborso", valore=torna,
                 firma=firma_dest(999, "indirizzo", torna)).status_code,
           uno(888, oid7)["rimborso"]))
    paga(o7)
    prova("il deposito parte lo stesso (un indirizzo in rete non si ferma): "
          "depositato, col rimborso ancora vuoto", ("depositato", ""),
          (lambda d: (d["stato"], d["rimborso"]))(gesto(888, oid7, "controlla").json()))
    o7b = uno(999, oid7)
    prova("un rimborso verso «niente» il giudice non lo firma: 400", 400,
          gesto(999, oid7, "proposta", verso="compratore",
                psbt=psbt_di(o7b, [(torna, 71080 - 300)], 999).to_string()).status_code)
    prova("la rinuncia la chiede solo chi compra: 403 a chi ha depositato", 403,
          gesto(888, oid7, "rinuncia-chiesta").status_code)
    banco.DETTO.clear()
    n_bottoni = len(BOTTONI)
    r = gesto(999, oid7, "rinuncia-chiesta")
    prova("chi compra tocca «Rinuncio»: non e' un errore, si registra, e chi ha "
          "depositato lo sa dal bot (col bottone dello scambio)",
          (200, False, True, True, True),
          (r.status_code, r.json()["pronto"], r.json()["avvisato"],
           detto_a(888, "Chi compra vuole rinunciare") and detto_a(888, "Dove tornano i sats?"),
           any(chi == 888 and b and "?scambio=bar-onchain-" in b[1]
               for chi, t, b in BOTTONI[n_bottoni:])))
    prova("...lo scambio se lo ricorda, per tutt'e due", (True, True),
          (uno(999, oid7)["rinuncia_chiesta_il"] > 0,
           uno(888, oid7)["rinuncia_chiesta_il"] > 0))
    banco.DETTO.clear()
    r = gesto(999, oid7, "rinuncia-chiesta")
    prova("un secondo tocco entro l'ora non manda un secondo avviso",
          (200, False, []),
          (r.status_code, r.json()["avvisato"], [t[:30] for chi, t in banco.DETTO]))
    con = SRV._p2p_onchain_db()
    try:
        con.execute("UPDATE p2p_onchain_ordini SET rinuncia_chiesta_il="
                    "rinuncia_chiesta_il-? WHERE id=?",
                    (SRV.P2P_ONCHAIN_RINUNCIA_RIAVVISO + 5, oid7))
        con.commit()
    finally:
        con.close()
    prova("...passata l'ora si' (un sollecito, non una raffica)", (True, True),
          (gesto(999, oid7, "rinuncia-chiesta").json()["avvisato"],
           detto_a(888, "Chi compra vuole rinunciare")))
    banco.DETTO.clear()
    r = gesto(888, oid7, "rimborso", valore=torna,
              firma=firma_dest(888, "indirizzo", torna))
    o7 = uno(888, oid7)
    come(888)
    prova("chi ha depositato scrive l'indirizzo, firmato dal suo seme: 200, lo "
          "scambio rimborsa li', il Profilo resta vuoto, il segno si toglie",
          (200, torna, "indirizzo", "", 0),
          (r.status_code, o7["rimborso"],
           (o7["destinazione_rimborso"] or {}).get("tipo"),
           c.get("/api/me").json().get("onchain_incasso") or "",
           o7["rinuncia_chiesta_il"]))
    prova("...e chi aspettava di rinunciare lo sa: «Ora puoi rinunciare», una volta",
          1, sum(1 for chi, t in banco.DETTO if chi == 999 and "Ora puoi rinunciare" in t))
    prova("...scritto non si cambia: 409", 409,
          gesto(888, oid7, "rimborso", valore=dal_wallet(32),
                firma=firma_dest(888, "indirizzo", dal_wallet(32))).status_code)
    r = gesto(999, oid7, "rinuncia-chiesta")
    prova("adesso «Rinuncio» trova l'indirizzo: `pronto`, nessun avviso in piu'",
          (200, True, False),
          (r.status_code, r.json()["pronto"], r.json()["avvisato"]))
    o7b = uno(999, oid7)
    prova("...la rinuncia si firma e la seconda firma di chi ha depositato "
          "rimborsa", (200, "rimborsato"),
          (gesto(999, oid7, "proposta", verso="compratore",
                 psbt=psbt_di(o7b, [(torna, 71080 - 300)], 999).to_string()).status_code,
           gesto(888, oid7, "firma", tx=cofirma(888, uno(888, oid7))).json()["stato"]))
    prova("...e i sats tornano all'indirizzo scritto li', meno la rete",
          [(torna, 71080 - 300)],
          [(script.Script(v.script_pubkey.data).address(N), v.value)
           for v in Transaction.from_string(INVIATE[-1]).vout])
    # dal Profilo: la scelta del wallet sblocca la rinuncia che aspettava
    oid8 = pubblica(888, sats=40000, euro_cent=3600, metodi=["Bonifico"]).json()["id"]
    gesto(999, oid8, "prendi")
    paga(uno(888, oid8))
    gesto(888, oid8, "controlla")
    gesto(999, oid8, "rinuncia-chiesta")
    banco.DETTO.clear()
    casa = dal_wallet(33)
    come(888)
    r = c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": casa,
        "firma": firma_dest(888, "indirizzo", casa)})
    o8 = uno(888, oid8)
    prova("la stessa rinuncia, e chi ha depositato sceglie il wallet dal "
          "Profilo: il rimborso si riempie, il segno si toglie, chi compra lo sa",
          (200, casa, 0, 1),
          (r.status_code, o8["rimborso"], o8["rinuncia_chiesta_il"],
           sum(1 for chi, t in banco.DETTO if chi == 999 and "Ora puoi rinunciare" in t)))
    banco.DETTO.clear()
    come(888)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": casa,
        "firma": firma_dest(888, "indirizzo", casa)})
    prova("...salvare di nuovo il Profilo non lo ridice", 0,
          sum(1 for chi, t in banco.DETTO if "Ora puoi rinunciare" in t))
    # in disputa il moderatore non poteva rimborsare senza indirizzo
    come(888)
    c.post("/api/onchain/incasso", json={"tipo": "barattolo"})
    oid9 = pubblica(888, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()["id"]
    gesto(999, oid9, "prendi")
    paga(uno(888, oid9))
    gesto(888, oid9, "controlla")
    gesto(999, oid9, "disputa", motivo="non risponde")
    prova("in disputa la rinuncia non si chiede (decide un moderatore): 409", 409,
          gesto(999, oid9, "rinuncia-chiesta").status_code)
    banco.AVVISI.clear()
    qua = dal_wallet(34)
    r = gesto(888, oid9, "rimborso", valore=qua,
              firma=firma_dest(888, "indirizzo", qua))
    prova("...ma chi ha depositato l'indirizzo lo scrive anche li', e i "
          "moderatori lo sanno", (200, qua, True),
          (r.status_code, uno(888, oid9)["rimborso"],
           any("dove riavere i sats" in str(a) for a in banco.AVVISI)))
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 11-sexies-bis) l'indirizzo di chi compra, detto a chi libera (17
    # nov 2026, cantiere avviso-indirizzo; un utente: «hai liberato i sats
    # prima che abbia inserito l'indirizzo») -------------------------------------
    print("\n[l'indirizzo di chi compra: il sollecito di chi libera, e "
          "l'avviso quando arriva]")
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    prova("la leva nasce accesa", True, SRV.P2P_ONCHAIN_AVVISO_INCASSO)
    come(999)
    c.post("/api/onchain/incasso", json={"tipo": "barattolo"})   # Andrea senza wallet
    come(888)
    c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": dal_wallet(40),
        "firma": firma_dest(888, "indirizzo", dal_wallet(40))})   # i resti di Alan

    def depositato(sats):
        oid_ = pubblica(888, sats=sats, euro_cent=sats * 9 // 100,
                        metodi=["Bonifico"]).json()["id"]
        gesto(999, oid_, "prendi")
        paga(uno(888, oid_))
        gesto(888, oid_, "controlla")
        return oid_

    oid10 = pubblica(888, sats=50000, euro_cent=4500, metodi=["Bonifico"]).json()["id"]
    gesto(999, oid10, "prendi")
    o10 = uno(888, oid10)
    prova("Andrea compra senza un wallet: incasso vuoto, e chi deposita vede "
          "«Ricordaglielo» (chi compra no)", ("", True, False, 0),
          (o10["incasso"], o10["sollecito_incasso"],
           uno(999, oid10)["sollecito_incasso"], o10["incasso_sollecito_il"]))
    prova("prima del deposito non si sollecita: 409", 409,
          gesto(888, oid10, "sollecita-incasso").status_code)
    paga(o10)
    gesto(888, oid10, "controlla")
    prova("...a deposito fatto lo sollecita solo chi ha depositato: 403 a chi compra",
          ("depositato", 403),
          (uno(888, oid10)["stato"], gesto(999, oid10, "sollecita-incasso").status_code))
    banco.DETTO.clear()
    n_bottoni = len(BOTTONI)
    r = gesto(888, oid10, "sollecita-incasso")
    prova("Alan tocca «🔔 Ricordaglielo»: Andrea lo sa dal bot, col bottone "
          "dello scambio, e lo scambio se lo ricorda",
          (200, False, True, True, True, True),
          (r.status_code, r.json()["pronto"], r.json()["avvisato"],
           detto_a(999, "Chi vende vuole liberarti i sats")
           and detto_a(999, "Dove ricevi i bitcoin?"),
           any(chi == 999 and b and "?scambio=bar-onchain-" in b[1]
               for chi, t, b in BOTTONI[n_bottoni:]),
           uno(888, oid10)["incasso_sollecito_il"] > 0))
    banco.DETTO.clear()
    r = gesto(888, oid10, "sollecita-incasso")
    prova("un secondo tocco entro l'ora non manda niente, e dice da quando si "
          "puo' rifare", (200, False, [], True),
          (r.status_code, r.json()["avvisato"], [t[:30] for chi, t in banco.DETTO],
           r.json()["prossimo"] > time.time() + 3000))
    con = SRV._p2p_onchain_db()
    try:
        con.execute("UPDATE p2p_onchain_ordini SET incasso_sollecito_il="
                    "incasso_sollecito_il-? WHERE id=?",
                    (SRV.P2P_ONCHAIN_INCASSO_RIAVVISO + 5, oid10))
        con.commit()
    finally:
        con.close()
    prova("...passata l'ora si' (un sollecito, non una raffica)", (True, True),
          (gesto(888, oid10, "sollecita-incasso").json()["avvisato"],
           detto_a(999, "Chi vende vuole liberarti i sats")))
    SRV.P2P_ONCHAIN_AVVISO_INCASSO = False
    prova("leva spenta: il bottone non c'e' e la rotta non esiste (404)",
          (False, 404),
          (uno(888, oid10)["sollecito_incasso"],
           gesto(888, oid10, "sollecita-incasso").status_code))
    SRV.P2P_ONCHAIN_AVVISO_INCASSO = True
    banco.DETTO.clear()
    qui10 = dal_wallet(41)
    r = gesto(999, oid10, "incasso", valore=qui10,
              firma=firma_dest(999, "indirizzo", qui10))
    prova("Andrea incolla l'indirizzo nello scambio: Alan lo sa dal bot, una "
          "volta, col bottone", (200, qui10, 1),
          (r.status_code, uno(888, oid10)["incasso"],
           sum(1 for chi, t in banco.DETTO
               if chi == 888 and "Chi compra ha scelto dove ricevere" in t)))
    r = gesto(888, oid10, "sollecita-incasso")
    prova("...e adesso «Ricordaglielo» risponde `pronto`, senza avvisi", (200, True, False),
          (r.status_code, r.json()["pronto"], r.json()["avvisato"]))
    o10 = uno(888, oid10)
    prova("...e «Ricevuti: libera i sats» trova dove mandarli: la prima firma passa",
          200, gesto(888, oid10, "proposta", verso="venditore",
                     psbt=psbt_di(o10, [(qui10, 50000), (o10["rimborso"], 51080 - 50000 - 300)],
                                  888).to_string()).status_code)
    # a leva spenta l'indirizzo arriva in silenzio, come prima
    oid11 = depositato(30000)
    SRV.P2P_ONCHAIN_AVVISO_INCASSO = False
    banco.DETTO.clear()
    qui11 = dal_wallet(42)
    gesto(999, oid11, "incasso", valore=qui11, firma=firma_dest(999, "indirizzo", qui11))
    prova("leva spenta: l'indirizzo arriva e chi ha depositato non riceve niente",
          (qui11, 0), (uno(888, oid11)["incasso"],
                       sum(1 for chi, t in banco.DETTO if chi == 888)))
    SRV.P2P_ONCHAIN_AVVISO_INCASSO = True
    # dal Profilo: avvisa chi ha depositato, non chi deve ancora depositare
    oid12 = depositato(20000)
    oid13 = pubblica(888, sats=25000, euro_cent=2250, metodi=["Bonifico"]).json()["id"]
    gesto(999, oid13, "prendi")
    banco.DETTO.clear()
    come(999)
    r = c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": RIMBORSO_999,
        "firma": firma_dest(999, "indirizzo", RIMBORSO_999)})
    prova("Andrea sceglie il wallet dal Profilo: i due scambi lo prendono, e "
          "Alan riceve un avviso solo per quello gia' depositato",
          (200, RIMBORSO_999, RIMBORSO_999, 1, True),
          (r.status_code, uno(888, oid12)["incasso"], uno(888, oid13)["incasso"],
           sum(1 for chi, t in banco.DETTO
               if chi == 888 and "Chi compra ha scelto dove ricevere" in t),
           detto_a(888, "20.000 sats")))
    come(888)
    c.post("/api/onchain/incasso", json={"tipo": "barattolo"})   # Alan come prima
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 11-septies) il contanti di persona col luogo, come su Lightning (17
    # nov 2026, cantiere onchain-contanti; Andrea: «non c'è neanche il luogo
    # dello scambio») -----------------------------------------------------------
    print("\n[il contanti di persona: la zona di scambio e il suo tetto]")
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    tetto_c, SRV.P2P_CONTANTI_MAX_EURO = SRV.P2P_CONTANTI_MAX_EURO, 250
    r = pubblica(888, metodi=["Contanti"], recapito="")
    prova("in contanti senza la zona non si pubblica: 400 con la frase del foglio",
          (400, True), (r.status_code, "Scrivi la zona di scambio" in r.text))
    # il tetto del contanti sta SOTTO quello generale: qui lo si abbassa a
    # 50 €, cosi' i 90 € di sempre passano il primo e inciampano nel secondo
    SRV.P2P_CONTANTI_MAX_EURO = 50
    r = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro")
    rb = pubblica(888, metodi=["Bonifico"])
    prova("...e sopra il tetto del contanti nemmeno: 400 col tetto; un bonifico della "
          "stessa cifra passa", (400, True, 200),
          (r.status_code, "In contanti di persona il massimo è 50 €" in r.text,
           rb.status_code))
    SRV.P2P_CONTANTI_MAX_EURO = 250
    r = pubblica(888, metodi=["Contanti"], recapito="", zona="  Milano \n centro ")
    oc_c = r.json().get("id")
    r2 = pubblica(888, metodi=["Bonifico"], zona="Roma")
    oc_s = r2.json().get("id")
    nel = {x["id"]: x for x in libro(999)["onchain"]["eventi"]}
    prova("con la zona si pubblica, e la zona esce ripulita nel libro e nella scheda; "
          "senza «Contanti» la zona non si tiene",
          (200, "Milano centro", "Milano centro", 200, None, ""),
          (r.status_code, nel.get(oc_c, {}).get("zona"), uno(888, oc_c)["zona"],
           r2.status_code, nel.get(oc_s, {}).get("zona"), uno(888, oc_s)["zona"]))

    # ---- 11-octies) lo scambio in contanti: l'appuntamento, «📍 Sono qui», le
    # parole di «Ho consegnato i contanti» e il confronto del moderatore (17 nov
    # 2026, onchain-contanti secondo pezzo; Andrea: «Dovrebbe funzionare
    # esattamente come Lightning anche l'on-chain contanti») --------------------
    print("\n[lo scambio in contanti: appuntamento, «Sono qui», consegna, moderatore]")
    prova("la scheda dice se lo scambio e' in contanti: il solo «Contanti» si', un bonifico no",
          (True, False), (uno(888, oc_c)["contanti"], uno(888, oc_s)["contanti"]))
    banco.DETTO.clear()
    gesto(999, oc_c, "prendi")
    prova("prima del deposito la presenza non si segna: 409 con la frase",
          (409, True), (lambda r: (r.status_code, "quando i sats sono nel deposito" in r.text))(
              gesto(999, oc_c, "sono-qui", geo={"lat": 45.4642, "lon": 9.19, "acc": 10})))
    fra_un_ora = int(time.time()) + 3600
    testo_app = ("Contanti alla mano — propongo di vederci: Bar Sport, piazza Duomo\n"
                 "Quando: 01/01/2030 alle 18:30\nCoordinate: 45.46420, 9.19000")
    prova("un'ora dell'incontro fuori misura non passa: 400, e il recapito non cambia",
          (400, ""), (gesto(888, oc_c, "recapito", recapito=testo_app,
                            appuntamento={"ora": int(time.time()) + 30 * 86400}).status_code,
                      uno(888, oc_c)["recapito"]))
    r = gesto(888, oc_c, "recapito", recapito=testo_app,
              appuntamento={"ora": fra_un_ora, "geo": {"lat": 45.4642, "lon": 9.19}})
    prova("chi vende scrive dove vedervi: 200, chi compra lo legge e l'avviso dice «dove vedervi»",
          (200, testo_app, True, False),
          (r.status_code, uno(999, oc_c)["recapito"], detto_a(999, "ha scritto dove vedervi"),
           detto_a(999, "dove vuole gli euro")))
    con = SRV.db()
    try:
        app_n = con.execute("SELECT COUNT(*) FROM p2p_appuntamenti WHERE ordine=?",
                            (uno(888, oc_c)["ordine"],)).fetchone()[0]
    finally:
        con.close()
    gesto(888, oc_c, "recapito", recapito=testo_app,
          appuntamento={"ora": fra_un_ora, "geo": {"lat": 45.4642, "lon": 9.19}})
    con = SRV.db()
    try:
        app_n2 = con.execute("SELECT COUNT(*) FROM p2p_appuntamenti WHERE ordine=?",
                             (uno(888, oc_c)["ordine"],)).fetchone()[0]
    finally:
        con.close()
    prova("l'appuntamento e' una versione, e lo stesso salvato due volte non ne fa una seconda",
          (1, 1), (app_n, app_n2))
    banco.DETTO.clear()
    paga(uno(888, oc_c))
    gesto(888, oc_c, "controlla")
    prova("a deposito confermato i due avvisi parlano dell'incontro, non del conto",
          ("depositato", True, True, False),
          (uno(888, oc_c)["stato"], detto_a(999, "in contanti"),
           detto_a(888, "lui tocca «Ho consegnato i contanti»: allora contali"),
           detto_a(888, "sul tuo conto")))
    prova("un terzo non segna niente: 404; su uno scambio non in contanti: 409",
          (404, 409), (gesto(777, oc_c, "sono-qui").status_code,
                       (lambda: (gesto(999, oc_s, "prendi"),
                                 gesto(999, oc_s, "sono-qui").status_code)[1])()))
    r = gesto(999, oc_c, "sono-qui", geo={"lat": 45.4643, "lon": 9.1901, "acc": 10})
    d = r.json()
    prova("chi compra segna «Sono qui» con la posizione: 200, la sua riga con l'ora",
          (200, True, True, 1, None),
          (r.status_code, d["posizione"], d["presenze"]["mia"]["posizione"],
           d["presenze"]["mia"]["volte"], d["presenze"]["altra"]))
    vista_v = uno(888, oc_c)
    prova("chi vende vede SOLO l'ora dell'altro: mai una coordinata nella sua scheda",
          (True, None, False, False),
          (vista_v["presenze"]["altra"]["ora"] > 0, vista_v["presenze"]["mia"],
           "45.4643" in json.dumps(vista_v["presenze"]), "lat" in json.dumps(vista_v["presenze"])))
    r = gesto(888, oc_c, "sono-qui")
    prova("chi vende la segna senza posizione: 200, e lo dice",
          (200, False, True), (r.status_code, r.json()["posizione"],
                               r.json()["presenze"]["altra"]["ora"] > 0))
    for _ in range(4):
        gesto(999, oc_c, "sono-qui", geo={"lat": 45.4643, "lon": 9.1901, "acc": 10})
    prova("al sesto tocco dello stesso lato: 429", 429, gesto(999, oc_c, "sono-qui").status_code)
    banco.DETTO.clear()
    r = gesto(999, oc_c, "euro-inviati", contanti=True)
    prova("«Ho consegnato i contanti»: a chi vende le parole della consegna, non del conto",
          (200, True, False),
          (r.status_code, detto_a(888, "consegnato 90,00 € in contanti")
           or detto_a(888, "consegnato 90 € in contanti"), detto_a(888, "Controlla il tuo conto")))
    prova("...e la presenza si segna ancora (i contanti si stanno contando)", 200,
          gesto(888, oc_c, "sono-qui").status_code)
    gesto(888, oc_c, "disputa", motivo="Non mi ha dato i contanti")
    come(777)
    ap = [x for x in c.get("/api/p2p/onchain/moderazione/aperte").json()["dispute"]
          if x["id"] == oc_c]
    cf = (ap[0].get("confronto") or {}) if ap else {}
    prova("in disputa il moderatore terzo ha il confronto delle presenze, con l'appuntamento "
          "e la distanza dal luogo di chi compra; le parti no",
          (1, "probabile", "incontro", True, True, False, False),
          (len(ap), cf.get("esito"), cf.get("regola"),
           ((cf.get("compra") or {}).get("appuntamento") or {}).get("dist_luogo") is not None,
           (cf.get("appuntamento") or {}).get("punto"),
           "presenze" in (ap[0] if ap else {}), "confronto" in uno(888, oc_c)))
    prova("a disputa aperta la presenza non si segna piu': 409", 409,
          gesto(999, oc_c, "sono-qui").status_code)
    con = SRV.db()
    try:
        nome = uno(888, oc_c)["ordine"]
        prima = con.execute("SELECT COUNT(*) FROM p2p_sono_qui WHERE ordine=? AND lat IS NOT NULL",
                            (nome,)).fetchone()[0]
        via0 = SRV._p2p_onchain_scorda_incontri(con, int(time.time()))
        con.execute("UPDATE p2p_onchain_ordini SET stato='rimborsato' WHERE id=?", (oc_c,))
        SRV._scopa_presenze_p2p(con, int(time.time()))
        dopo = con.execute("SELECT COUNT(*), SUM(posizione), SUM(posizione_via>0), "
                           "SUM(dist_luogo IS NOT NULL) FROM p2p_sono_qui WHERE ordine=? "
                           "AND lat IS NULL", (nome,)).fetchone()
        punto = con.execute("SELECT lat, punto, posizione_via>0 FROM p2p_appuntamenti "
                            "WHERE ordine=?", (nome,)).fetchone()
        con.execute("UPDATE p2p_onchain_ordini SET stato='disputa' WHERE id=?", (oc_c,))
        con.commit()
    finally:
        con.close()
    prova("a scambio aperto (anche in disputa) le posizioni restano; chiuso, la scopa le "
          "scorda e restano le ore e la distanza dal luogo; il punto dell'appuntamento pure",
          (True, 0, True, True, True, (None, 1, 1)),
          (prima >= 1, via0, dopo[0] >= 7, dopo[1] >= 1, dopo[3] >= 1, tuple(punto)))
    SRV.P2P_CONTANTI_MAX_EURO = tetto_c
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 11-novies) il metodo scelto alla presa e la cauzione in Lightning del
    # contanti on-chain, contro un LND di cartone (17 nov 2026 sera, onchain-
    # contanti terzo pezzo; Andrea: «Quando ci clicco poi non mi fa mettere la
    # cauzione», «Anche la questione QR, tutto quanto») -------------------------
    print("\n[il metodo scelto alla presa e la cauzione in Lightning del contanti]")
    import base64
    import http.server
    import threading
    import urllib.parse
    import httpx as httpx_vero
    MAC_C = "0201036c6e64" + "cd" * 40
    LND = {"fatture": {}, "visti": [], "muto": False}

    class FintoLndCauzioni(http.server.BaseHTTPRequestHandler):
        """La REST di LND per le hold: `hodl` conia, `GET /v1/invoice/{hash}`
        dice lo stato, `cancel` annulla (e la seconda volta dice «already
        canceled»)."""
        def log_message(self, *a):
            pass

        def _rispondi(self, codice, d):
            dati = json.dumps(d).encode()
            self.send_response(codice)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)

        def _porta(self):
            if self.headers.get("Grpc-Metadata-macaroon", "") != MAC_C:
                self._rispondi(401, {"code": 16, "message": "permission denied"})
                return False
            if LND["muto"]:
                self._rispondi(500, {"code": 2, "message": "cartone muto"})
                return False
            return True

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            LND["visti"].append(("GET", u.path, dict(urllib.parse.parse_qsl(u.query))))
            if not self._porta():
                return
            if not u.path.startswith("/v1/invoice/"):
                return self._rispondi(404, {"code": 5, "message": "Not Found"})
            h = u.path.rsplit("/", 1)[1]
            f = LND["fatture"].get(h)
            if not f:
                return self._rispondi(404, {"code": 5, "message": "there are no existing invoices"})
            return self._rispondi(200, {"state": f["state"], "value": str(f["value"])})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            corpo = json.loads(self.rfile.read(n) or b"{}")
            LND["visti"].append(("POST", self.path, corpo))
            if not self._porta():
                return
            if self.path == "/v2/invoices/hodl":
                h = base64.b64decode(corpo["hash"]).hex()
                LND["fatture"][h] = {"state": "OPEN", "value": int(corpo["value"])}
                return self._rispondi(200, {"payment_request": "lnbc1cauzione" + h[:24]})
            if self.path == "/v2/invoices/cancel":
                h = base64.b64decode(corpo["payment_hash"]).hex()
                f = LND["fatture"].get(h)
                if f and f["state"] == "SETTLED":
                    return self._rispondi(500, {"code": 2, "message": "invoice already settled"})
                if not f or f["state"] == "CANCELED":
                    return self._rispondi(500, {"code": 2, "message": "invoice already canceled"})
                f["state"] = "CANCELED"
                return self._rispondi(200, {})
            if self.path == "/v2/invoices/settle":
                h = hashlib.sha256(base64.b64decode(corpo["preimage"])).hexdigest()
                f = LND["fatture"].get(h)
                if not f:
                    return self._rispondi(500, {"code": 2, "message": "unable to locate invoice"})
                if f["state"] == "SETTLED":
                    return self._rispondi(500, {"code": 2, "message": "invoice already settled"})
                if f["state"] != "ACCEPTED":
                    return self._rispondi(500, {"code": 2, "message": "invoice still open"})
                f["state"] = "SETTLED"
                return self._rispondi(200, {})
            return self._rispondi(404, {"code": 5, "message": "Not Found"})

    lnd_srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLndCauzioni)
    lnd_srv.daemon_threads = True
    threading.Thread(target=lnd_srv.serve_forever, daemon=True).start()
    httpx_del_banco, ponte_prima = SRV.httpx, SRV.LND_PONTE_URL
    SRV.httpx = httpx_vero
    SRV.LND_PONTE_URL = f"http://127.0.0.1:{lnd_srv.server_address[1]}"
    SRV.FRENI["p2p_onchain_cauzione"] = (1000, 3600)
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = 100

    def hodl_visti():
        return [v for v in LND["visti"] if v[1] == "/v2/invoices/hodl"]

    def busta_oc(tg):
        # come `libro`: nella gabbia chi guarda glielo si dice
        SRV._chi_guarda_p2p = lambda *a, **k: int(tg)
        come(tg)
        return c.get("/api/p2p/onchain/libro").json()

    def cauz(tg, oid, metodo=None):
        come(tg)
        if metodo is None:
            return c.get(f"/api/p2p/onchain/{oid}/cauzione")
        return c.post(f"/api/p2p/onchain/{oid}/cauzione", json={"metodo": metodo})

    def riga_cauz(oid):
        con = SRV.db()
        try:
            r = con.execute("SELECT * FROM p2p_onchain_cauzioni WHERE ordine_id=? "
                            "ORDER BY id DESC LIMIT 1", (oid,)).fetchone()
            return dict(r) if r else None
        finally:
            con.close()

    def misto(**d):
        return pubblica(888, metodi=["Bonifico", "Contanti"], zona="Milano centro",
                        **d).json().get("id")

    prova("i sats della cauzione: il 3% col mezzo che sale, mai sotto i 1000; storta = 0",
          (3000, 1000, 1001, 0, 0),
          (SRV.p2p_onchain_cauzione_sats(100000), SRV.p2p_onchain_cauzione_sats(10000),
           SRV.p2p_onchain_cauzione_sats(33350), SRV.p2p_onchain_cauzione_sats(0),
           SRV.p2p_onchain_cauzione_sats("x")))
    # IL TETTO (22 nov 2026, cantiere tetto-cauzione): di serie, senza riga
    prova("...e mai oltre il tetto di serie di 50.000 sats",
          (50000, 50000, 49998, 48000),
          (SRV.P2P_ONCHAIN_CAUZIONE_TETTO_SATS, SRV.p2p_onchain_cauzione_sats(2000000),
           SRV.p2p_onchain_cauzione_sats(1666600), SRV.p2p_onchain_cauzione_sats(1600000)))
    # -- a leva SPENTA: la scelta del metodo c'e', la cauzione no
    SRV.P2P_ONCHAIN_CAUZIONE, SRV.LND_PONTE_MACAROON_CAUZIONE = False, MAC_C
    # la porticina degli admin resta CHIUSA, com'e' di serie e come sara'
    # in produzione (Andrea, 17 nov: «In produzione, solo tu e Alan»): chi
    # prende in tutto il giro e' il 999, un moderatore; il 111 non lo e'
    porticina = SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN
    SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = True
    # (19 nov 2026) la meta' mandata DA SOLA ha il suo passo, in fondo alla
    # sezione: fin li' il giro a mano di prima, che resta la strada oltre il tetto
    meta_auto_prima = SRV.P2P_ONCHAIN_CAUZIONE_META_AUTO
    SRV.P2P_ONCHAIN_CAUZIONE_META_AUTO = False
    # ...mentre l'on-chain e' aperto a tutti, com'e' in produzione dal 16
    # nov: il 111 deve poter prendere, sennò la porticina non si vede
    solo_admin_oc = SRV.ONCHAIN_SOLO_ADMIN
    SRV.ONCHAIN_SOLO_ADMIN = False
    semi[111] = vett["bip39_english"][3]["parole"]
    come(111)
    c.post("/api/onchain/xpub", json={"xpub": conto(111)})
    prova("la porticina dei moderatori e' chiusa di serie", True, porticina)
    prova("la leva vuole la riga E il macaroon: una senza l'altro e' spenta",
          (False, False, True),
          (SRV.p2p_onchain_cauzione_accesa(999),
           (setattr(SRV, "P2P_ONCHAIN_CAUZIONE", True), setattr(SRV, "LND_PONTE_MACAROON_CAUZIONE", ""),
            SRV.p2p_onchain_cauzione_accesa(999))[2],
           (setattr(SRV, "LND_PONTE_MACAROON_CAUZIONE", MAC_C), SRV.p2p_onchain_cauzione_accesa(999))[1]))
    prova("...e a porticina chiusa e' accesa SOLO per un moderatore: non per il 111, "
          "non per un ospite, non per un id storto",
          (True, True, False, False, False),
          (SRV.p2p_onchain_cauzione_accesa(999), SRV.p2p_onchain_cauzione_accesa(888),
           SRV.p2p_onchain_cauzione_accesa(111), SRV.p2p_onchain_cauzione_accesa(),
           SRV.p2p_onchain_cauzione_accesa("x")))
    SRV.P2P_ONCHAIN_CAUZIONE = False
    SRV._p2p_onchain_rifai_foto()
    prova("a leva spenta la busta del libro on-chain lo dice",
          False, busta_oc(999).get("cauzione", {}).get("accesa"))
    m1, m2, m3, m4 = misto(), misto(), misto(), misto()
    prova("a leva spenta la cauzione non si chiede: 409, e a LND non bussa nessuno",
          (409, 0), (cauz(999, m1, "Contanti").status_code, len(LND["visti"])))
    r = gesto(999, m1, "prendi", metodo="Contanti")
    prova("«Contanti» scelto su un ordine con piu' metodi: lo scambio e' in contanti, "
          "il metodo resta scritto e l'IBAN lascia il posto all'appuntamento",
          (200, True, "Contanti", ""),
          (r.status_code, r.json().get("contanti"), r.json().get("metodo_scelto"),
           uno(888, m1)["recapito"]))
    r = gesto(999, m2, "prendi", metodo="Bonifico")
    prova("«Bonifico» scelto: non e' in contanti, e il recapito di chi vende resta",
          (200, False, "Bonifico", "IT00 X 1234"),
          (r.status_code, r.json().get("contanti"), r.json().get("metodo_scelto"),
           uno(888, m2)["recapito"]))
    r, r4 = gesto(999, m3, "prendi"), gesto(999, m4, "prendi", metodo="Satispay")
    prova("senza scelta (un telefono di ieri), o con un metodo che non e' dell'ordine: "
          "si prende come ieri, non in contanti",
          (200, False, "", 200, False, ""),
          (r.status_code, r.json().get("contanti"), r.json().get("metodo_scelto"),
           r4.status_code, r4.json().get("contanti"), r4.json().get("metodo_scelto")))
    # -- a leva ACCESA
    SRV.P2P_ONCHAIN_CAUZIONE = True
    SRV._p2p_onchain_rifai_foto()
    busta_c = busta_oc(999).get("cauzione", {})
    prova("a leva accesa la busta porta la regola: 3%, almeno 1000 sats, quindici minuti",
          (True, 3, 1000, 900),
          (busta_c.get("accesa"), busta_c.get("pct"), busta_c.get("base"), busta_c.get("finestra")))
    # -- LA PORTICINA: a leva accesa, chi non e' moderatore non vede niente
    g1 = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro").json().get("id")
    g2 = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro").json().get("id")
    n_hodl = len(hodl_visti())
    prova("a porticina chiusa la busta del 111 dice «spenta», quella del moderatore «accesa»",
          (False, True),
          (busta_oc(111).get("cauzione", {}).get("accesa"),
           busta_oc(999).get("cauzione", {}).get("accesa")))
    prova("...il 111 non puo' chiedere la cauzione (409) e LND non conia niente",
          (409, n_hodl), (cauz(111, g1, "Contanti").status_code, len(hodl_visti())))
    r = gesto(111, g1, "prendi")
    prova("...e prende in contanti SENZA cauzione, come a leva spenta: nessuna riga, "
          "nessun riquadro nella scheda",
          (200, "preso", True, None, None),
          (r.status_code, r.json().get("stato"), r.json().get("contanti"),
           riga_cauz(g1), uno(111, g1).get("cauzione")))
    SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = False
    prova("porticina APERTA (un False scritto): vale per tutti, e il 111 senza cauzione "
          "non prende piu'",
          (True, True, 409, True),
          (SRV.p2p_onchain_cauzione_accesa(111), busta_oc(111).get("cauzione", {}).get("accesa"))
          + (lambda r: (r.status_code, "serve la cauzione" in r.text))(gesto(111, g2, "prendi")))
    SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = True
    prova("richiusa, il 111 torna a non vederla",
          False, busta_oc(111).get("cauzione", {}).get("accesa"))
    c1 = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro").json().get("id")
    prova("in contanti senza cauzione non si prende: 409 con la frase, e l'ordine resta nel libro",
          (409, True, "pending"),
          (lambda r: (r.status_code, "serve la cauzione" in r.text, uno(888, c1)["stato"]))(
              gesto(999, c1, "prendi")))
    prova("chi ha pubblicato non chiede la cauzione sul suo ordine: 409",
          409, cauz(888, c1, "Contanti").status_code)
    r = cauz(999, c1, "Contanti")
    cz = r.json().get("cauzione") or {}
    h1 = hodl_visti()
    prova("la richiesta: 200, in attesa, 3000 sats su 100.000, con la fattura da pagare",
          (200, "attesa", 3000, True, False),
          (r.status_code, cz.get("stato"), cz.get("sats"),
           str(cz.get("bolt11", "")).startswith("lnbc1cauzione"), cz.get("in_gioco")))
    prova("...e LND ha visto UNA hodl: 3000 sats, quindici minuti, cltv 576, hash di 32 byte",
          (1, "3000", "900", "576", 32),
          (len(h1), h1[0][2]["value"], h1[0][2]["expiry"], h1[0][2]["cltv_expiry"],
           len(base64.b64decode(h1[0][2]["hash"]))))
    r = cauz(999, c1, "Contanti")
    prova("chiesta due volte torna la STESSA richiesta: nessuna seconda hold",
          (cz.get("bolt11"), 1), ((r.json().get("cauzione") or {}).get("bolt11"), len(hodl_visti())))
    prova("non ancora pagata: lo stato resta in attesa, e la presa dice di pagarla",
          ("attesa", 409, True),
          ((cauz(999, c1).json().get("cauzione") or {}).get("stato"),) +
          (lambda r: (r.status_code, "non risulta ancora bloccata" in r.text))(
              gesto(999, c1, "prendi")))
    riga1 = riga_cauz(c1)
    prova("il preimage resta sul server e fa l'hash che LND conosce; al telefono non esce mai",
          (True, False),
          (hashlib.sha256(bytes.fromhex(riga1["preimage"])).hexdigest() == riga1["hash"]
           and riga1["hash"] in LND["fatture"], "preimage" in cauz(999, c1).text))
    LND["fatture"][riga1["hash"]]["state"] = "ACCEPTED"     # il wallet ha pagato: HTLC fermo
    cz = cauz(999, c1).json().get("cauzione") or {}
    prova("pagata: LND dice ACCEPTED, la cauzione e' TENUTA e la fattura non serve piu'",
          ("tenuta", False, False), (cz.get("stato"), "bolt11" in cz, cz.get("in_gioco")))
    r = gesto(999, c1, "prendi")
    prova("con la cauzione tenuta la presa passa, e la cauzione entra in gioco",
          (200, "preso", True, 1),
          (r.status_code, r.json().get("stato"), r.json().get("contanti"),
           riga_cauz(c1)["in_gioco"]))
    prova("la scheda: a chi l'ha messa «tenuta, 3000, mia»; all'altra parte niente; "
          "al moderatore senza «mia»",
          ({"stato": "tenuta", "sats": 3000, "mia": True}, None,
           {"stato": "tenuta", "sats": 3000, "mia": False}),
          (uno(999, c1).get("cauzione"), uno(888, c1).get("cauzione"),
           uno(777, c1).get("cauzione")))
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata())
    prova("a scambio vivo il giro non tocca niente",
          ({"tenute": 0, "tornate": 0, "scadute": 0}, "ACCEPTED"),
          (conto, LND["fatture"][riga1["hash"]]["state"]))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='disputa' WHERE id=?", (c1,))
    con.commit()
    con.close()
    asyncio.run(SRV.p2p_onchain_cauzioni_passata())
    prova("...nemmeno in disputa: la cauzione resta ferma finche' qualcuno decide",
          "ACCEPTED", LND["fatture"][riga1["hash"]]["state"])
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='rimborsato' WHERE id=?", (c1,))
    con.commit()
    con.close()
    banco.DETTO.clear()
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata())
    r1 = riga_cauz(c1)
    prova("a scambio chiuso il giro la rimanda indietro: cancel su LND, «tornata», col perche'",
          (1, "CANCELED", "tornata", "scambio chiuso", "tornata"),
          (conto["tornate"], LND["fatture"][riga1["hash"]]["state"], r1["stato"], r1["perche"],
           (uno(999, c1).get("cauzione") or {}).get("stato")))
    # (19 nov 2026, Andrea dopo la prova in produzione) ...e chi l'aveva messa lo sa
    prova("...e a chi l'aveva bloccata arriva «La cauzione è tornata nel tuo wallet» coi "
          "sats; all'altra parte niente; un giro dopo nessun doppione",
          (True, True, False, False),
          (detto_a(999, "La cauzione è tornata nel tuo wallet"), detto_a(999, "3.000 sats"),
           detto_a(888, "La cauzione è tornata"),
           (banco.DETTO.clear(), asyncio.run(SRV.p2p_onchain_cauzioni_passata()),
            detto_a(999, "La cauzione è tornata"))[2]))
    # -- le cauzioni che non arrivano alla presa
    c2 = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro",
                  sats=20000, euro_cent=1800).json().get("id")
    cz2 = cauz(999, c2, "Contanti").json().get("cauzione") or {}
    r2 = riga_cauz(c2)
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata(r2["scade"] + 1))
    prova("su 20.000 sats la cauzione e' il minimo, 1000; mai pagata e scaduta, il giro la "
          "annulla e la scrive «scaduta»",
          (1000, 1, "scaduta", "CANCELED"),
          (cz2.get("sats"), conto["scadute"], riga_cauz(c2)["stato"],
           LND["fatture"][r2["hash"]]["state"]))
    cauz(999, c2, "Contanti")
    r2 = riga_cauz(c2)
    LND["fatture"][r2["hash"]]["state"] = "ACCEPTED"
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata(r2["scade"] + 1))
    prova("pagata all'ultimo secondo a telefono chiuso: il giro la vede e la scrive tenuta",
          (1, "tenuta", 0), (conto["tenute"], riga_cauz(c2)["stato"], riga_cauz(c2)["in_gioco"]))
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata(
        r2["scade"] + 1 + SRV.P2P_ONCHAIN_CAUZIONE_PRESA_S + 1))
    prova("tenuta ma mai usata: dopo un quarto d'ora torna da sola («non usata»)",
          (1, "tornata", "non usata", "CANCELED"),
          (conto["tornate"], riga_cauz(c2)["stato"], riga_cauz(c2)["perche"],
           LND["fatture"][r2["hash"]]["state"]))
    cauz(999, c2, "Contanti")
    r2 = riga_cauz(c2)
    LND["fatture"][r2["hash"]]["state"] = "ACCEPTED"
    cauz(999, c2)
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='annullato' WHERE id=?", (c2,))
    con.commit()
    con.close()
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata())
    prova("tenuta, e l'ordine esce dal libro prima della presa: torna subito",
          (1, "tornata", "non usata"),
          (conto["tornate"], riga_cauz(c2)["stato"], riga_cauz(c2)["perche"]))
    # -- in gioco, e il nodo la rimanda indietro da solo (i 576 blocchi)
    c3 = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro").json().get("id")
    cauz(999, c3, "Contanti")
    r3 = riga_cauz(c3)
    LND["fatture"][r3["hash"]]["state"] = "ACCEPTED"
    gesto(999, c3, "prendi")
    LND["fatture"][r3["hash"]]["state"] = "CANCELED"
    conto = asyncio.run(SRV.p2p_onchain_cauzioni_passata(
        int(time.time()) + SRV.P2P_ONCHAIN_CAUZIONE_GUARDA_S + 1))
    prova("in gioco, ma il nodo l'ha gia' rimandata: il giro lo scrive com'e'",
          (1, "tornata", "tornata da sola dal nodo"),
          (conto["tornate"], riga_cauz(c3)["stato"], riga_cauz(c3)["perche"]))
    # -- LA CAUZIONE PERSA (quarto pezzo): la brucia un moderatore, solo in
    #    disputa; meta' all'altra persona, mandata a mano
    def brucia(tg, oid):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/cauzione/brucia")

    def mandata(tg, oid):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/cauzione/meta-mandata")

    def saldate():
        return [v for v in LND["visti"] if v[1] == "/v2/invoices/settle"]

    def in_disputa(oid):
        con = SRV.db()
        con.execute("UPDATE p2p_onchain_ordini SET stato='disputa' WHERE id=?", (oid,))
        con.commit()
        con.close()

    def presa_con_cauzione():
        oid = pubblica(888, metodi=["Contanti"], recapito="", zona="Milano centro").json().get("id")
        cauz(999, oid, "Contanti")
        LND["fatture"][riga_cauz(oid)["hash"]]["state"] = "ACCEPTED"
        gesto(999, oid, "prendi")
        return oid

    c5 = presa_con_cauzione()
    r5 = riga_cauz(c5)
    prova("a scambio vivo ma NON in disputa la cauzione non si brucia: 409, e LND non vede niente",
          (409, True, 0),
          (lambda r: (r.status_code, "solo a scambio in disputa" in r.text, len(saldate())))(brucia(777, c5)))
    in_disputa(c5)
    prova("chi non e' moderatore non ha la strada (404), e chi e' parte dello scambio non "
          "decide il suo (403): ne' chi ha preso ne' chi ha pubblicato",
          (404, 403, 403, 0),
          (brucia(111, c5).status_code, brucia(999, c5).status_code,
           brucia(888, c5).status_code, len(saldate())))
    LND["muto"] = True
    r = brucia(777, c5)
    prova("LND muto: 503 con la frase, e la cauzione resta TENUTA (si puo' riprovare)",
          (503, True, "tenuta", 0),
          (r.status_code, "ancora bloccata" in r.text, riga_cauz(c5)["stato"],
           riga_cauz(c5)["persa_da"]))
    LND["muto"] = False
    n_b = len(BOTTONI)       # (mai svuotarla: la sezione 12 la legge intera)
    banco.AVVISI.clear()
    r = brucia(777, c5)
    riga5 = riga_cauz(c5)
    prova("il moderatore la brucia: 200, 3000 sats persi, 1500 all'altra persona",
          (200, 3000, 1500), (r.status_code, r.json().get("sats"), r.json().get("meta")))
    prova("...LND l'ha SALDATA col preimage della riga, e la riga dice persa, da chi, "
          "e la meta' di chi ha pubblicato",
          ("SETTLED", "persa", 777, 1500, 888, True),
          (LND["fatture"][r5["hash"]]["state"], riga5["stato"], riga5["persa_da"],
           riga5["meta_sats"], riga5["meta_a"],
           hashlib.sha256(base64.b64decode(saldate()[-1][2]["preimage"])).hexdigest() == r5["hash"]))
    prova("...avvisati tutti e tre: chi l'ha persa, chi riceve la meta', e i moderatori "
          "con la cifra da mandare a mano",
          (True, True, True),
          (any(chi == 999 and "Cauzione persa" in t for chi, t, _ in BOTTONI[n_b:]),
           any(chi == 888 and "Metà della cauzione" in t and "1.500" in t.replace("\u202f", ".").replace(" ", ".")
               for chi, t, _ in BOTTONI[n_b:]),
           any("DA MANDARE A MANO" in str(a) and "(888)" in str(a) for a in banco.AVVISI)))
    prova("bruciata due volte no: 409, e LND non vede una seconda saldatura",
          (409, True, 2),
          (lambda r: (r.status_code, "già stata bruciata" in r.text, len(saldate())))(brucia(777, c5)))
    prova("la scheda: a chi l'ha messa «persa»; a chi ha pubblicato la meta' da ricevere; "
          "al moderatore quanto mandare e a chi",
          ({"stato": "persa", "sats": 3000, "mia": True},
           {"sats": 1500, "mandata": False, "auto": False, "ln": False},
           {"sats": 1500, "a": 888, "nome": "Alan", "ln_address": "", "mandata": False,
            "auto": False}),
          (uno(999, c5).get("cauzione"), uno(888, c5).get("cauzione_meta"),
           (uno(777, c5).get("cauzione") or {}).get("meta")))
    prova("...e a chi ha preso nessuna meta', a chi ha pubblicato nessuna cauzione",
          (None, None), (uno(999, c5).get("cauzione_meta"), uno(888, c5).get("cauzione")))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='rimborsato' WHERE id=?", (c5,))
    con.commit()
    con.close()
    n_cancel = len([v for v in LND["visti"] if v[1] == "/v2/invoices/cancel"])
    asyncio.run(SRV.p2p_onchain_cauzioni_passata())
    prova("a scambio chiuso il giro NON tocca una cauzione persa: nessuna cancel, resta saldata",
          ("persa", "SETTLED", n_cancel),
          (riga_cauz(c5)["stato"], LND["fatture"][r5["hash"]]["state"],
           len([v for v in LND["visti"] if v[1] == "/v2/invoices/cancel"])))
    prova("una cancel su una hold gia' SALDATA non vale «tornata»",
          False, asyncio.run(SRV._p2p_onchain_cauzione_annulla(r5["hash"])))
    n_b = len(BOTTONI)
    prova("«Metà mandata»: non chi la riceve (403), non chi non e' moderatore (404); il "
          "moderatore si', una volta, e l'altra persona lo sa",
          (403, 404, 200, True, True, True),
          (mandata(888, c5).status_code, mandata(111, c5).status_code,
           mandata(777, c5).status_code, mandata(777, c5).json().get("gia"),
           uno(888, c5)["cauzione_meta"]["mandata"],
           any(chi == 888 and "mandata" in t for chi, t, _ in BOTTONI[n_b:])))
    # -- il gesto morto a meta': la riga resta «saldando», e decide LND
    c6 = presa_con_cauzione()
    in_disputa(c6)
    r6 = riga_cauz(c6)

    def saldando(oid, quando):
        con = SRV.db()
        con.execute("UPDATE p2p_onchain_cauzioni SET stato='saldando', saldando_il=?, persa_da=777"
                    " WHERE ordine_id=?", (quando, oid))
        con.commit()
        con.close()

    ora = int(time.time())
    saldando(c6, ora)
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 30))
    prova("una «saldando» fresca il giro la lascia stare; al telefono e' ancora «tenuta», "
          "e un secondo moderatore non la brucia sopra",
          ("saldando", "tenuta", 409),
          (riga_cauz(c6)["stato"], uno(999, c6)["cauzione"]["stato"], brucia(777, c6).status_code))
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + SRV.P2P_ONCHAIN_CAUZIONE_SALDANDO_S + 1))
    prova("appesa da due minuti e LND dice ancora ACCEPTED: torna TENUTA, senza moderatore",
          ("tenuta", 0), (riga_cauz(c6)["stato"], riga_cauz(c6)["persa_da"]))
    saldando(c6, ora)
    LND["fatture"][r6["hash"]]["state"] = "SETTLED"
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + SRV.P2P_ONCHAIN_CAUZIONE_SALDANDO_S + 1))
    prova("appesa e LND dice SETTLED: e' PERSA, con la meta' scritta",
          ("persa", 1500, 888),
          (riga_cauz(c6)["stato"], riga_cauz(c6)["meta_sats"], riga_cauz(c6)["meta_a"]))
    # -- un ordine con piu' metodi, a leva accesa
    m5, m6 = misto(), misto()
    n_hodl = len(hodl_visti())
    r = gesto(999, m5, "prendi", metodo="Bonifico")
    prova("a leva accesa chi sceglie «Bonifico» prende senza cauzione, e LND non conia niente",
          (200, False, n_hodl), (r.status_code, r.json().get("contanti"), len(hodl_visti())))
    prova("...chi sceglie «Contanti» no: 409 finche' non la blocca; e «Bonifico» non ne ha una",
          (409, 409),
          (gesto(999, m6, "prendi", metodo="Contanti").status_code,
           cauz(999, m6, "Bonifico").status_code))
    # -- LA CAUZIONE A SCELTA DI CHI PUBBLICA (18 nov 2026, cantiere tempo-
    # pagamento; Andrea: «chi pubblica un ordine decide se chiedere una
    # cauzione a chi gli prende l'ordine»): con qualunque metodo
    k1 = pubblica(888, cauzione=True).json()
    k0 = pubblica(888).json()
    k111 = pubblica(111, cauzione=True).json()
    prova("chi pubblica chiede la cauzione e la riga lo dice; senza la scelta no; e a "
          "porticina chiusa chi non e' moderatore non la puo' chiedere",
          (True, False, False),
          (k1.get("cauzione_chiesta"), k0.get("cauzione_chiesta"), k111.get("cauzione_chiesta")))
    SRV._p2p_onchain_rifai_foto()
    prova("...la busta del libro porta la leva per il foglio Pubblica",
          True, busta_oc(999).get("cauzione", {}).get("aScelta"))
    # LA SCELTA ARRIVA NEL LIBRO DI CHI PRENDE (19 nov 2026, cantiere
    # cauzione-nel-libro; prova dal vivo con Alan in produzione): fino a
    # ieri solo la scheda di chi pubblica portava `cauzione_chiesta` e
    # `minuti_pagamento`, la riga del libro no — e il telefono di chi
    # prende non mostrava 🔐 ne' «Blocca la cauzione», mentre il server la
    # pretendeva e rifiutava la presa
    k60 = pubblica(888, metodi=["Revolut"], minuti_pagare=60, cauzione=True).json()
    SRV._p2p_onchain_rifai_foto()
    righe_oc = {int(e["id"]): e for e in busta_oc(999).get("eventi", [])}
    prova("...e la riga del libro di chi PRENDE porta la cauzione chiesta (si' e no) e i "
          "minuti per pagare scelti (60 coi metodi veloci, 24 ore coi lenti)",
          (True, False, True, 1440, 60),
          (righe_oc.get(int(k1["id"]), {}).get("cauzione_chiesta"),
           righe_oc.get(int(k0["id"]), {}).get("cauzione_chiesta"),
           righe_oc.get(int(k60["id"]), {}).get("cauzione_chiesta"),
           righe_oc.get(int(k1["id"]), {}).get("minuti_pagamento"),
           righe_oc.get(int(k60["id"]), {}).get("minuti_pagamento")))
    gesto(888, k60["id"], "annulla")
    prova("...e con «Bonifico» chi prende non prende senza cauzione: 409 con la frase, "
          "e l'ordine resta nel libro",
          (409, True, "pending"),
          (lambda r: (r.status_code, "serve la cauzione" in r.text, uno(888, k1["id"])["stato"]))(
              gesto(999, k1["id"], "prendi")))
    n_hodl = len(hodl_visti())
    r = cauz(999, k1["id"], "")
    prova("...la richiesta si conia anche senza contanti, coi sats della regola",
          (200, n_hodl + 1, 3000),
          (r.status_code, len(hodl_visti()), (r.json().get("cauzione") or {}).get("sats")))
    prova("...mentre sull'ordine senza la scelta non serve", 409, cauz(999, k0["id"], "").status_code)
    SRV.P2P_ONCHAIN_CAUZIONE_A_SCELTA = False
    prova("a leva `P2P_ONCHAIN_CAUZIONE_A_SCELTA` spenta la scelta tace anche sugli ordini "
          "gia' pubblicati, e si prende senza",
          (False, 200),
          (uno(888, k1["id"]).get("cauzione_chiesta"), gesto(999, k1["id"], "prendi").status_code))
    SRV.P2P_ONCHAIN_CAUZIONE_A_SCELTA = True
    k_buy = pubblica(888, lato="buy", recapito="", cauzione=True).json()
    prova("...e solo chi VENDE la chiede: su un «Compra BTC» la scelta non si scrive",
          (True, False), (bool(k_buy.get("id")), k_buy.get("cauzione_chiesta")))
    # -- ...E SI PERDE DA SOLA (Andrea: «la perde solo se annulla lo scambio
    #    o se lascia passare troppo tempo, in base alla scadenza»)
    def presa_chiesta():
        oid = pubblica(888, cauzione=True).json().get("id")
        cauz(999, oid, "")
        LND["fatture"][riga_cauz(oid)["hash"]]["state"] = "ACCEPTED"
        gesto(999, oid, "prendi")
        return oid

    def metti(oid, **campi):
        con = SRV.db()
        con.execute("UPDATE p2p_onchain_ordini SET " + ", ".join(f"{k}=?" for k in campi)
                    + " WHERE id=?", (*campi.values(), oid))
        con.commit()
        con.close()

    k2, k3, k4 = presa_chiesta(), presa_chiesta(), presa_chiesta()
    ora = int(time.time())
    prova("presa con la cauzione chiesta: in gioco, tenuta, messa da chi riceve i bitcoin",
          ("tenuta", 1, 999),
          (riga_cauz(k2)["stato"], riga_cauz(k2)["in_gioco"], riga_cauz(k2)["tg_id"]))
    for k in (k2, k3, k4):
        metti(k, stato="depositato", depositato_il=ora)
    n_s = len(saldate())
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 10))
    prova("a deposito confermato e col tempo che corre il giro non la tocca",
          ("tenuta", "tenuta", "tenuta", n_s),
          (riga_cauz(k2)["stato"], riga_cauz(k3)["stato"], riga_cauz(k4)["stato"],
           len(saldate())))
    # (19 nov 2026, Andrea alla prova) il foglio di «Rinuncio» dice PRIMA la
    # cauzione che si perde: il numero lo da' la pagina, a chi l'ha messa
    prova("a deposito confermato la pagina dice a chi ha preso la cauzione che perderebbe "
          "rinunciando; a chi vende niente; con l'annullo chiesto da chi vende niente",
          (3000, None, None),
          (uno(999, k2).get("cauzione_rinuncia"), uno(888, k2).get("cauzione_rinuncia"),
           (metti(k3, annullo_chiesto_il=ora), uno(999, k3).get("cauzione_rinuncia"),
            metti(k3, annullo_chiesto_il=0))[1]))
    metti(k2, pagamento_scaduto_il=ora)                       # tempo finito, niente «Ho inviato»
    metti(k3, pagamento_scaduto_il=ora, euro_inviati_il=ora)  # tempo finito ma «Ho inviato» c'era
    metti(k4, stato="rimborsato", mancato_perche="onchain-rinuncia", chiuso_il=ora)
    n_b = len(BOTTONI)
    banco.AVVISI.clear()
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 20))
    r2, r3, r4 = riga_cauz(k2), riga_cauz(k3), riga_cauz(k4)
    prova("il tempo per pagare scaduto senza «Ho inviato» la fa perdere DA SOLA: saldata, "
          "persa, da nessuno, meta' a chi vende",
          ("SETTLED", "persa", 0, 1500, 888),
          (LND["fatture"][r2["hash"]]["state"], r2["stato"], r2["persa_da"], r2["meta_sats"], r2["meta_a"]))
    prova("...la rinuncia dopo il deposito pure; con «Ho inviato» toccato resta tenuta",
          ("persa", 888, "tenuta"), (r4["stato"], r4["meta_a"], r3["stato"]))
    prova("...avvisati chi la perde (col perche'), chi vende (la meta') e i moderatori "
          "(da mandare a mano)",
          (True, True, True, True),
          (any(chi == 999 and "Cauzione persa" in t and "scadere il tempo" in t for chi, t, _ in BOTTONI[n_b:]),
           any(chi == 999 and "Cauzione persa" in t and "rinunciato" in t for chi, t, _ in BOTTONI[n_b:]),
           any(chi == 888 and "Metà della cauzione" in t for chi, t, _ in BOTTONI[n_b:]),
           any("persa da sola" in str(a) and "DA MANDARE A MANO" in str(a) for a in banco.AVVISI)))
    metti(k3, recapito="", pagamento_scaduto_il=ora, euro_inviati_il=0)
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 30))
    prova("...e senza il recapito di chi vende non si perde mai (la regola del «non completato»)",
          "tenuta", riga_cauz(k3)["stato"])
    # (20 nov 2026, ritorno-da-solo-oc) lo scambio che la ronda ha GIA'
    # chiuso per il tempo finito, prima della seconda firma: e' «annullato»,
    # e senza la cura il giro lo vedeva chiuso e la cauzione tornava
    k5 = presa_chiesta()
    metti(k5, stato="annullato", chiuso_perche="tempo-scaduto", chiuso_il=ora,
          depositato_il=ora, pagamento_scaduto_il=ora)
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 35))
    r5 = riga_cauz(k5)
    prova("...anche a scambio gia' chiuso dalla ronda per il tempo finito (prima della "
          "seconda firma) si perde: saldata, meta' a chi vende",
          ("SETTLED", "persa", 1500), (LND["fatture"][r5["hash"]]["state"], r5["stato"],
                                       r5["meta_sats"]))
    # -- LA META' MANDATA DA SOLA (19 nov 2026, Andrea: «Sì, in automatico con
    #    un tetto»): una riga nel registro «da riscuotere», la strada d'uscita
    #    di sempre; qui la si guarda da fuori (la strada ha i suoi collaudi)
    print("\n[la metà della cauzione persa mandata da sola]")
    SRV.P2P_ONCHAIN_CAUZIONE_META_AUTO = True
    k7, k8, k9 = presa_chiesta(), presa_chiesta(), presa_chiesta()
    for k in (k7, k8, k9):            # vivi e col recapito: nessuna si perde ancora
        metti(k, stato="depositato", depositato_il=ora)
    metti(k7, stato="rimborsato", mancato_perche="onchain-rinuncia", chiuso_il=ora)

    def registro(k):
        con = SRV.db()
        try:
            rid = con.execute("SELECT meta_rimborso_id FROM p2p_onchain_cauzioni WHERE ordine_id=?",
                              (k,)).fetchone()[0]
            r = con.execute("SELECT * FROM rimborsi_asta WHERE id=?", (rid,)).fetchone()
            return dict(r) if r else None
        finally:
            con.close()

    # senza indirizzo Lightning (Alan non l'ha): la riga nasce, il pagamento
    # non parte, resta «da riscuotere» e nessuno la manda a mano
    n_b = len(BOTTONI)
    banco.AVVISI.clear()
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 40))
    rg = registro(k7) or {}
    prova("SENZA INDIRIZZO: la meta' entra nel registro di chi vende (1500, motivo suo, "
          "da riscuotere), chi vende sa di scrivere l'indirizzo, i moderatori leggono «NON "
          "mandatela a mano», e «Metà mandata» a mano dice 409",
          (1500, 888, "cauzione_p2p", "da_riscuotere", True, True, False, 409),
          (rg.get("importo_sats"), rg.get("tg_id"), rg.get("motivo"), rg.get("stato"),
           any(chi == 888 and "metà di una cauzione" in t for chi, t in banco.DETTO[-200:])
           or any(chi == 888 and "metà di una cauzione" in t for chi, t, _ in BOTTONI[n_b:]),
           any("NON mandatela a mano" in str(a) for a in banco.AVVISI),
           any("DA MANDARE A MANO" in str(a) for a in banco.AVVISI),
           mandata(777, k7).status_code))
    prova("...la scheda: a chi vende «arriva da sola», al moderatore niente tasto",
          (True, False, True),
          (uno(888, k7)["cauzione_meta"]["auto"], uno(888, k7)["cauzione_meta"]["mandata"],
           (uno(777, k7).get("cauzione") or {}).get("meta", {}).get("auto")))
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 50))
    con = SRV.db()
    n_righe = con.execute("SELECT COUNT(*) FROM rimborsi_asta WHERE motivo='cauzione_p2p'").fetchone()[0]
    con.close()
    prova("...un altro giro non ne fa una seconda", 1, n_righe)
    # il pagamento andato e quello incerto: la strada d'uscita finta, per
    # guardare la colla (la riga, il timbro, le parole)
    paga_vera = SRV._paga_rimborso
    async def paga_ok(rid):
        con = SRV.db()
        con.execute("UPDATE rimborsi_asta SET stato='riscosso', payout_stato='uscito' WHERE id=?", (rid,))
        con.commit()
        con.close()
        return {"ok": True, "stato": "riscosso"}
    async def paga_incerta(rid):
        return {"ok": False, "stato": "da_riscuotere", "incerto": True}
    SRV._paga_rimborso = paga_ok
    banco.AVVISI.clear()
    metti(k8, stato="rimborsato", mancato_perche="onchain-rinuncia", chiuso_il=ora)
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 60))
    prova("PAGATA: la cauzione e' timbrata «mandata» (da nessuno), la scheda lo dice e i "
          "moderatori leggono «mandata da sola»",
          (True, 0, True, True),
          (bool(riga_cauz(k8)["meta_mandata_il"]), riga_cauz(k8)["meta_mandata_da"],
           uno(888, k8)["cauzione_meta"]["mandata"],
           any("Metà mandata da sola" in str(a) for a in banco.AVVISI)))
    SRV._paga_rimborso = paga_incerta
    metti(k9, stato="rimborsato", mancato_perche="onchain-rinuncia", chiuso_il=ora)
    n_b = len(BOTTONI)
    banco.AVVISI.clear()
    asyncio.run(SRV.p2p_onchain_cauzioni_passata(ora + 70))
    prova("INCERTA: niente timbro, chi vende sa che e' in verifica, i moderatori «NON "
          "mandatela a mano»",
          (False, True, True),
          (bool(riga_cauz(k9)["meta_mandata_il"]),
           any(chi == 888 and "in verifica" in t for chi, t, _ in BOTTONI[n_b:]),
           any("Metà in verifica" in str(a) for a in banco.AVVISI)))
    SRV._paga_rimborso = paga_vera
    tetto_meta = SRV.P2P_ONCHAIN_CAUZIONE_META_TETTO
    prova("DI SERIE NESSUN TETTO (Andrea: «Nessun tetto»): parte qualunque cifra; con un "
          "tetto scritto, oltre resta a mano; a leva spenta pure",
          (0, True, False, False, True),
          (tetto_meta, SRV.p2p_onchain_meta_automatica(10 ** 6, 888),
           (setattr(SRV, "P2P_ONCHAIN_CAUZIONE_META_TETTO", 5000),
            SRV.p2p_onchain_meta_automatica(5001, 888))[1],
           (setattr(SRV, "P2P_ONCHAIN_CAUZIONE_META_TETTO", tetto_meta),
            setattr(SRV, "P2P_ONCHAIN_CAUZIONE_META_AUTO", False),
            SRV.p2p_onchain_meta_automatica(1500, 888))[2],
           (setattr(SRV, "P2P_ONCHAIN_CAUZIONE_META_AUTO", True),
            SRV.p2p_onchain_meta_automatica(1500, 888))[1]))
    SRV.P2P_ONCHAIN_CAUZIONE_META_AUTO = meta_auto_prima
    # -- LND muto
    LND["muto"] = True
    r = cauz(999, m6, "Contanti")
    prova("LND muto: la richiesta dice di riprovare (503) e niente si scrive",
          (503, None), (r.status_code, riga_cauz(m6)))
    LND["muto"] = False
    prova("col macaroon sbagliato LND dice di no e la rotta non esplode: 503",
          503, (setattr(SRV, "LND_PONTE_MACAROON_CAUZIONE", "0201036c6e64" + "ef" * 40),
                cauz(999, m6, "Contanti").status_code)[1])
    SRV.LND_PONTE_MACAROON_CAUZIONE = MAC_C
    prova("al nodo passano solo hodl, cancel, la lettura di una fattura e le DUE saldature "
          "chieste dal moderatore (una a LND muto), le TRE della cauzione chiesta persa da "
          "sola (20 nov 2026: anche a scambio chiuso dalla ronda per il tempo) e le TRE "
          "della meta' mandata da sola: nient'altro salda una cauzione",
          (set(), 8),
          ({v[1] for v in LND["visti"] if not v[1].startswith("/v1/invoice/")}
           - {"/v2/invoices/hodl", "/v2/invoices/cancel", "/v2/invoices/settle"},
           len(saldate())))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET stato='annullato' WHERE id IN (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (m1, m2, m3, m4, m5, m6, c3, c1, g1, g2, c5, c6, k1["id"], k0["id"], k111["id"]))
    con.execute("UPDATE p2p_onchain_ordini SET stato='annullato' WHERE id IN (?,?,?,?,?,?,?)",
                (k_buy.get("id") or 0, k2, k3, k4, k7, k8, k9))
    con.commit()
    con.close()
    SRV.P2P_ONCHAIN_CAUZIONE, SRV.LND_PONTE_MACAROON_CAUZIONE = False, ""
    SRV.P2P_ONCHAIN_CAUZIONE_SOLO_ADMIN = porticina
    SRV.ONCHAIN_SOLO_ADMIN = solo_admin_oc
    SRV.httpx, SRV.LND_PONTE_URL = httpx_del_banco, ponte_prima
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto
    SRV._p2p_onchain_rifai_foto()
    lnd_srv.shutdown()

    # ---- 11b) l'ammanco tollerato (18 nov 2026) ----------------------------
    print("\n[l'ammanco tollerato: pochi sats in meno da uno swap li copre il margine]")
    tetto = SRV.P2P_ONCHAIN_APERTI_MAX
    SRV.P2P_ONCHAIN_APERTI_MAX = 100
    FISSO_AMMANCO = "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"   # BIP-173
    # lo scambio vero: 270.503 chiesti, 270.444 arrivati da Chainflip
    om = pubblica(999).json()
    gesto(888, om["id"], "prendi")
    om = uno(999, om["id"])
    tollera = om["ammanco_ok_sats"]
    prova("la pagina sa quanti ne possono mancare: meta' del margine, al "
          "piu' il tetto", min(SRV.P2P_ONCHAIN_AMMANCO_MAX_SATS,
                               om["margine_sats"] // 2), tollera)
    prova("...e su una riga senza margine niente: PURA",
          0, SRV.p2p_onchain_ammanco_tollerato({"margine_sats": 0}))
    paga(om, quanto=om["importo_sats"] - tollera - 1)
    prova("un sats oltre la tolleranza: resta preso (serve un'altra "
          "transazione)", "preso", gesto(999, om["id"], "controlla").json()["stato"])
    banco.DETTO.clear()
    paga(om, quanto=om["importo_sats"] - 59)
    d = gesto(999, om["id"], "controlla").json()
    prova("59 sats in meno: depositato, e chi compra manda gli euro",
          ("depositato", om["importo_sats"] - 59, True),
          (d["stato"], d["ricevuti_sats"],
           detto_a(888, "deposito di garanzia 2-di-3")))
    prova("...chi vende sa che l'ammanco lo copre il margine, chi compra "
          "non ne sente parlare", (True, False),
          (detto_a(999, "<b>59 sats in meno</b>"), detto_a(888, "in meno")))
    om = uno(999, om["id"])
    # chi compra, a questo punto del giro, non ha un wallet vivo: gliene
    # si da' uno fisso, quel che conta qui e' il conto delle uscite
    con = SRV._p2p_onchain_db()
    con.execute("UPDATE p2p_onchain_ordini SET incasso=? WHERE id IN (?, ?)",
                (FISSO_AMMANCO, om["id"], om["id"]))
    con.commit()
    con.close()
    om = uno(999, om["id"])
    resto = om["margine_sats"] - 59 - 300
    giusto_m = [(om["incasso"], om["sats"])] + (
        [(om["rimborso"], resto)] if resto >= SRV.ONCHAIN_POLVERE else [])
    r = gesto(999, om["id"], "proposta", verso="venditore",
              psbt=psbt_di(om, giusto_m, 999).to_string())
    prova("il rilascio passa dal giudice di sempre: il prezzo esatto a chi "
          "compra, la rete dentro il margine che resta", 200, r.status_code)
    om2 = pubblica(999).json()
    gesto(888, om2["id"], "prendi")
    om2 = uno(999, om2["id"])
    paga(om2, quanto=om2["importo_sats"] - 59)
    gesto(999, om2["id"], "controlla")
    con = SRV._p2p_onchain_db()
    con.execute("UPDATE p2p_onchain_ordini SET incasso=? WHERE id=?",
                (FISSO_AMMANCO, om2["id"]))
    con.commit()
    con.close()
    om2 = uno(999, om2["id"])
    r = gesto(999, om2["id"], "proposta", verso="venditore",
              psbt=psbt_di(om2, [(om2["incasso"], om2["sats"]),
                                 (om2["rimborso"], om2["margine_sats"] - 50)],
                           999).to_string())
    prova("...ma il resto non puo' fingere che i 59 ci siano: rete a zero o "
          "sotto, 400", 400, r.status_code)

    print("\n[annulla e riprendi i sats: il deposito che non vale non resta chiuso]")
    prova("su un deposito valido non si riprende: 409", 409,
          gesto(999, om["id"], "riprendi").status_code)
    o3 = pubblica(999).json()
    gesto(888, o3["id"], "prendi")
    o3 = uno(999, o3["id"])
    corto = o3["importo_sats"] - 5000
    paga(o3, confermata=False, quanto=corto)
    r = gesto(999, o3["id"], "riprendi")
    prova("visti ma non confermati: 409, si aspetta la prima conferma",
          (409, True), (r.status_code, "prima conferma" in r.json()["detail"]))
    paga(o3, quanto=corto)
    r = gesto(999, o3["id"], "annulla")
    prova("«Annulla» con i sats sull'indirizzo indica a chi ha depositato "
          "il tasto nuovo", (409, True),
          (r.status_code, "Annulla e riprendi" in r.json()["detail"]))
    prova("chi compra bitcoin non riprende i sats di un altro: 403", 403,
          gesto(888, o3["id"], "riprendi").status_code)
    banco.DETTO.clear()
    r = gesto(999, o3["id"], "riprendi")
    d = r.json()
    prova("5.000 sats in meno, confermati: annullato, e Barattolo ha firmato "
          "il rimborso verso chi ha depositato",
          (200, "annullato", "compratore", "deposito-incompleto"),
          (r.status_code, d["stato"], (d.get("proposta") or {}).get("verso"),
           (d.get("proposta") or {}).get("barattolo")))
    prova("...chi compra sa di non mandare niente, chi vende di aprire l'app",
          (True, True), (detto_a(888, "Non mandare niente"),
                         detto_a(999, "Barattolo ha firmato il rimborso")))
    uscite = PSBT.from_string(d["proposta"]["psbt"]).tx.vout
    prova("...un'uscita sola, al wallet di chi ha depositato, dentro il margine",
          (1, True), (len(uscite),
                      0 < corto - uscite[0].value <= o3["margine_sats"]))
    prova("...una seconda volta: 409", 409,
          gesto(999, o3["id"], "riprendi").status_code)
    r = gesto(999, o3["id"], "firma", tx=cofirma(999, uno(999, o3["id"])))
    prova("la seconda firma del suo telefono: rimborsato, e nessuno ci "
          "rimette la reputazione", (200, "rimborsato", ""),
          (r.status_code, r.json()["stato"],
           uno(999, o3["id"]).get("non_completato") or ""))

    # «RIPRENDI I SATS» COL TEMPO FINITO (19 nov 2026, cantiere
    # riprendi-scaduto; Andrea: «nell'on-chain non si può far tornare da
    # solo?», poi «facciamo così»)
    print("\n[riprendi i sats: il tempo per pagare finito senza «Ho inviato»]")
    o5r = pubblica(999).json()
    gesto(888, o5r["id"], "prendi")
    paga(uno(999, o5r["id"]))
    gesto(999, o5r["id"], "controlla")
    r = gesto(999, o5r["id"], "riprendi-scaduto")
    prova("a tempo che corre no: 409, e la pagina non mostra il bottone",
          (409, True, False), (r.status_code, "non è ancora finito" in r.json()["detail"],
                               uno(999, o5r["id"])["riprendi_scaduto"]))
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 25 * 3600, int(time.time()) - 26 * 3600, o5r["id"]))
    con.commit()
    con.close()
    prova("a tempo finito il bottone lo vede solo chi ha depositato", (True, False),
          (uno(999, o5r["id"])["riprendi_scaduto"], uno(888, o5r["id"])["riprendi_scaduto"]))
    prova("chi compra bitcoin non riprende i sats dell'altro: 403", 403,
          gesto(888, o5r["id"], "riprendi-scaduto").status_code)
    prova("...a porticina chiusa, un non moderatore non lo vede nemmeno: 404", 404,
          (lambda vecchio: (setattr(SRV, "e_admin", lambda t: False),
                            gesto(999, o5r["id"], "riprendi-scaduto").status_code,
                            setattr(SRV, "e_admin", vecchio))[1])(SRV.e_admin))
    banco.DETTO.clear()
    r = gesto(999, o5r["id"], "riprendi-scaduto")
    d = r.json()
    prova("tempo finito senza «Ho inviato»: annullato, e Barattolo ha firmato il "
          "rimborso senza moderatore",
          (200, "annullato", "compratore", "tempo-scaduto", "tempo-scaduto"),
          (r.status_code, d["stato"], (d.get("proposta") or {}).get("verso"),
           (d.get("proposta") or {}).get("barattolo"), d.get("chiuso_perche")))
    prova("...chi compra sa che e' chiuso e di non mandare niente, chi vende di aprire l'app",
          (True, True, True), (detto_a(888, "Il tempo per pagare è finito"),
                               detto_a(888, "non mandare niente"),
                               detto_a(999, "Barattolo ha firmato il rimborso")))
    uscite = PSBT.from_string(d["proposta"]["psbt"]).tx.vout
    prova("...un'uscita sola, verso il wallet di chi ha depositato", (1, d["rimborso"]),
          (len(uscite), script.Script(uscite[0].script_pubkey.data).address(N)))
    prova("...una seconda volta: 409; e «Ho inviato» adesso non passa piu'", (409, 409),
          (gesto(999, o5r["id"], "riprendi-scaduto").status_code,
           gesto(888, o5r["id"], "euro-inviati").status_code))
    r = gesto(999, o5r["id"], "firma", tx=cofirma(999, uno(999, o5r["id"])))
    con = SRV.db()
    figlio = con.execute("SELECT id FROM p2p_onchain_ordini WHERE rinato_da=?",
                         (o5r["id"],)).fetchone()
    con.close()
    prova("la seconda firma: rimborsato, a chi non ha pagato il «non completato», e "
          "l'ordine torna nel libro",
          (200, "rimborsato", "altro", True),
          (r.status_code, r.json()["stato"], uno(999, o5r["id"]).get("non_completato") or "",
           figlio is not None))
    if figlio:
        gesto(999, figlio["id"], "annulla")
    o5s = pubblica(999).json()
    gesto(888, o5s["id"], "prendi")
    paga(uno(999, o5s["id"]))
    gesto(999, o5s["id"], "controlla")
    gesto(888, o5s["id"], "euro-inviati")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=?, recapito_il=? WHERE id=?",
                (int(time.time()) - 25 * 3600, int(time.time()) - 26 * 3600, o5s["id"]))
    con.commit()
    con.close()
    r = gesto(999, o5s["id"], "riprendi-scaduto")
    prova("dopo «Ho inviato gli euro» non si riprende niente: 409, si va in disputa",
          (409, True, False), (r.status_code, "disputa" in r.json()["detail"],
                               uno(999, o5s["id"])["riprendi_scaduto"]))

    # OGNI PASSO NEL TEMPO SCELTO (19 nov 2026, cantiere recapito-nel-tempo;
    # Andrea: «ogni passo deve durare 15 minuti», «stessa cosa nell'onchain»)
    print("\n[«dove vuoi gli euro» nel tempo scelto: promemoria, poi il rimborso]")
    prima_tempo = SRV.P2P_TEMPO_PER_PAGARE
    SRV.P2P_TEMPO_PER_PAGARE = True
    o5t = pubblica(999, metodi=["Revolut"], recapito="", minuti_pagare=30).json()
    gesto(888, o5t["id"], "prendi")
    paga(uno(999, o5t["id"]))
    gesto(999, o5t["id"], "controlla")
    ot = uno(999, o5t["id"])
    prova("deposito confermato senza recapito: chi ha depositato e chi compra leggono "
          "entro quando va scritto (30 minuti dal deposito)",
          ("depositato", ot["depositato_il"] + 1800, ot["depositato_il"] + 1800),
          (ot["stato"], ot.get("recapito_entro"), uno(888, o5t["id"]).get("recapito_entro")))

    def indietro_oc(oid, secondi):
        con = SRV.db()
        con.execute("UPDATE p2p_onchain_ordini SET depositato_il=depositato_il-?,"
                    " preso_il=preso_il-? WHERE id=?", (secondi, secondi, oid))
        con.commit()
        con.close()
    # L'OROLOGIO FERMO (20 nov 2026, cantiere collaudo-orologio-recapito): la
    # ronda legge l'ora vera, e «Hai ancora 14 minuti» diventava «13» appena
    # passava un secondo fra la conferma del deposito e la ronda (sotto carico,
    # coi collaudi in parallelo). Qui la ronda gira a un'ora DETTA, contata dal
    # deposito: il server vede un `time` il cui `time()` e' fermo, il resto
    # (e asyncio, che usa il suo orologio) resta quello vero.
    class OrologioFermo:
        def __init__(self, quando):
            self.quando = quando

        def time(self):
            return float(self.quando)

        def __getattr__(self, nome):
            return getattr(time, nome)

    def ronda_alle(quando):
        vero = SRV.time
        SRV.time = OrologioFermo(quando)
        try:
            asyncio.run(SRV._p2p_onchain_ronda())
        finally:
            SRV.time = vero
    indietro_oc(o5t["id"], 16 * 60)
    dep_t = int(uno(999, o5t["id"])["depositato_il"])
    banco.DETTO.clear()
    ronda_alle(dep_t + 16 * 60)
    prova("a meta' tempo il promemoria a chi ha depositato, col tempo che resta; a chi "
          "compra niente", (True, False),
          (detto_a(999, "Hai ancora 14 minuti per scrivere dove vuoi gli euro"),
           detto_a(888, "Hai ancora")))
    banco.DETTO.clear()
    ronda_alle(dep_t + 16 * 60 + 30)
    prova("...la ronda dopo non lo ripete", False, detto_a(999, "Hai ancora"))
    indietro_oc(o5t["id"], 15 * 60)
    banco.DETTO.clear()
    ronda_alle(dep_t + 16 * 60 + 60)
    ot = uno(999, o5t["id"])
    prova("finito il tempo senza recapito: annullato, e Barattolo ha firmato il rimborso "
          "verso chi ha depositato, detto a tutt'e due",
          ("annullato", "recapito-scaduto", "compratore", True, True, True),
          (ot["stato"], ot.get("chiuso_perche"), (ot.get("proposta") or {}).get("verso"),
           bool((ot.get("proposta") or {}).get("psbt")),
           detto_a(999, "Non hai scritto in tempo dove vuoi gli euro"),
           detto_a(888, "Non mandare niente")))
    uscite = PSBT.from_string(ot["proposta"]["psbt"]).tx.vout
    prova("...un'uscita sola, verso il wallet di chi ha depositato", (1, ot["rimborso"]),
          (len(uscite), script.Script(uscite[0].script_pubkey.data).address(N)))
    prova("...e «Ho inviato» o un recapito adesso non passano piu'", (409, True),
          (gesto(888, o5t["id"], "euro-inviati").status_code,
           gesto(999, o5t["id"], "recapito", recapito="IBAN tardi").status_code >= 400))
    r = gesto(999, o5t["id"], "firma", tx=cofirma(999, uno(999, o5t["id"])))
    con = SRV.db()
    figlio_t = con.execute("SELECT id FROM p2p_onchain_ordini WHERE rinato_da=?",
                           (o5t["id"],)).fetchone()
    con.close()
    prova("la seconda firma: rimborsato, a NESSUNO il «non completato» (chi compra non "
          "sapeva dove pagare), e l'ordine NON torna nel libro",
          (200, "rimborsato", "", "", None),
          (r.status_code, r.json()["stato"], uno(999, o5t["id"]).get("non_completato") or "",
           uno(888, o5t["id"]).get("non_completato") or "", figlio_t))
    SRV.P2P_TEMPO_PER_PAGARE = prima_tempo

    print("\n[il conto alla rovescia nel bot: un messaggio solo, riscritto]")
    # (19 nov 2026, regole-sulla-card) chi deve pagare riceve UN messaggio che
    # si riscrive ogni minuto: qui il giro si chiama a mano e il bot si ascolta
    chiamate = []
    vecchio_bot = SRV.bot_api

    async def bot_finto(metodo, dati):
        chiamate.append((metodo, dati))
        return {"ok": True, "result": {"message_id": dati.get("message_id") or 4242}}
    SRV.bot_api = bot_finto
    try:
        # il giro guarda TUTTI gli scambi vivi del banco (quelli delle sezioni
        # di prima compresi): qui si contano solo le chiamate di questo
        asyncio.run(SRV._giro_conto_p2p())
        o5c = pubblica(999).json()
        # a chi paga (888); dal 20 nov 2026 (conto-chi-aspetta) anche chi ha
        # depositato (999) ha il suo conto, contato a parte
        tutte_o5c = lambda: [c for c in chiamate if o5c["ordine"] in json.dumps(c[1])]
        mie = lambda: [c for c in tutte_o5c() if c[1].get("chat_id") == 888]
        sue = lambda: [c for c in tutte_o5c() if c[1].get("chat_id") == 999]
        gesto(888, o5c["id"], "prendi")
        asyncio.run(SRV._giro_conto_p2p())
        prova("prima del deposito il tempo non corre: nessun messaggio", [], tutte_o5c())
        paga(uno(999, o5c["id"]))
        gesto(999, o5c["id"], "controlla")
        asyncio.run(SRV._giro_conto_p2p())
        con = SRV.db()
        riga = con.execute("SELECT * FROM p2p_conto_rovescia WHERE chiave=?",
                           (f"oc:{o5c['id']}",)).fetchone()
        con.close()
        prova("deposito confermato: a chi deve pagare (888) UN messaggio col tempo che "
              "resta e il bottone dello scambio, e il suo id salvato",
              (1, "sendMessage", 888, True, True, 4242),
              (len(mie()), mie()[0][0], mie()[0][1]["chat_id"],
               "Tempo per pagare: mancano" in mie()[0][1]["text"],
               "?scambio=bar-onchain-" in json.dumps(mie()[0][1].get("reply_markup")),
               riga["messaggio"] if riga else 0))
        # (20 nov 2026, tasto-rosso-conto) il rosso e' solo fino a un'ora: questo
        # scambio ha il tempo di sempre, e il bottone resta quello normale
        con_oc = SRV._p2p_onchain_db()
        try:
            minuti_o5c = SRV._p2p_onchain_minuti(SRV._p2p_onchain_carica(con_oc, o5c["id"]))
        finally:
            con_oc.close()
        prova("un tempo per pagare di ore: il bottone NON e' rosso (il rosso e' fino a "
              "un'ora)", (True, False),
              (minuti_o5c > 60, '"style"' in json.dumps(mie()[0][1].get("reply_markup"))))
        # IL CONTO ANCHE A CHI ASPETTA (20 nov 2026, cantiere conto-chi-aspetta;
        # Andrea: «il tempo può aggiornarsi da solo in modo tale da sapere
        # solamente già da Telegram quanto manca?»)
        con = SRV.db()
        riga_v = con.execute("SELECT * FROM p2p_conto_rovescia WHERE chiave=?",
                             (f"oc:{o5c['id']}:v",)).fetchone()
        con.close()
        prova("...e a chi ha depositato (999) il SUO messaggio «Chi compra ha ancora … per "
              "pagare», col bottone dello scambio, mai rosso, con la stessa fine",
              (1, "sendMessage", True, True, False, True),
              (len(sue()), sue()[0][0] if sue() else "",
               bool(sue()) and "Chi compra ha ancora" in sue()[0][1]["text"],
               bool(sue()) and "?scambio=bar-onchain-" in json.dumps(sue()[0][1].get("reply_markup")),
               bool(sue()) and '"style"' in json.dumps(sue()[0][1].get("reply_markup")),
               bool(riga_v) and bool(riga) and int(riga_v["fine"]) == int(riga["fine"])))
        asyncio.run(SRV._giro_conto_p2p())
        prova("un giro subito dopo, stesso minuto: niente di nuovo (non si riscrive "
              "un testo uguale)", 1, len(mie()))
        asyncio.run(SRV._giro_conto_p2p(int(time.time()) + 600))
        prova("dieci minuti dopo: lo STESSO messaggio riscritto (editMessageText, "
              "che non suona), mai un messaggio nuovo",
              (2, "editMessageText", 4242, True),
              (len(mie()), mie()[-1][0], mie()[-1][1].get("message_id"),
               "reply_markup" in mie()[-1][1]))
        gesto(888, o5c["id"], "euro-inviati")
        asyncio.run(SRV._giro_conto_p2p())
        con = SRV.db()
        riga = con.execute("SELECT * FROM p2p_conto_rovescia WHERE chiave=?",
                           (f"oc:{o5c['id']}",)).fetchone()
        con.close()
        prova("«Ho inviato gli euro»: il messaggio dice che il tempo si e' fermato, e "
              "il conto e' chiuso", (3, True, True),
              (len(mie()), "si è fermato" in mie()[-1][1]["text"],
               int(riga["finito"]) > 0))
        asyncio.run(SRV._giro_conto_p2p(int(time.time()) + 1200))
        prova("...e dopo non si tocca piu'", 3, len(mie()))
        prova("...e a chi ha depositato lo stesso giro: riscritto dieci minuti dopo, poi "
              "«Chi compra ha toccato «Ho inviato gli euro»», chiuso, e non si tocca piu'",
              (3, "editMessageText", True, True),
              (len(sue()), sue()[1][0] if len(sue()) > 1 else "",
               bool(sue()) and "Chi compra ha toccato «Ho inviato gli euro»" in sue()[-1][1]["text"],
               (lambda c: bool(c) and int(c["finito"]) > 0)(
                   (lambda k: k.execute("SELECT finito FROM p2p_conto_rovescia WHERE chiave=?",
                                        (f"oc:{o5c['id']}:v",)).fetchone())(SRV.db()))))
        SRV.P2P_CONTO_ALLA_ROVESCIA = False
        prima = len(chiamate)
        o5d = pubblica(999).json()
        gesto(888, o5d["id"], "prendi")
        paga(uno(999, o5d["id"]))
        gesto(999, o5d["id"], "controlla")
        asyncio.run(SRV._giro_conto_p2p())
        prova("a leva spenta nessun messaggio", prima, len(chiamate))
        gesto(999, o5d["id"], "chiedi-annullo")
        SRV.P2P_CONTO_ALLA_ROVESCIA = True
        o5e = pubblica(999).json()
        mie_e = lambda: [c for c in chiamate if o5e["ordine"] in json.dumps(c[1])]
        gesto(888, o5e["id"], "prendi")
        paga(uno(999, o5e["id"]))
        gesto(999, o5e["id"], "controlla")
        asyncio.run(SRV._giro_conto_p2p())
        # (20 nov 2026) l'avviso che suona a un minuto dalla fine, una volta sola
        con_oc = SRV._p2p_onchain_db()
        try:
            fine_o5c = SRV.p2p_onchain_paga_entro(SRV._p2p_onchain_carica(con_oc, o5e["id"]))
        finally:
            con_oc.close()
        n_prima = len(mie_e())
        asyncio.run(SRV._giro_conto_p2p(fine_o5c - 60))
        asyncio.run(SRV._giro_conto_p2p(fine_o5c - 20))
        uno_min = [c for c in mie_e()[n_prima:] if c[0] == "sendMessage"
                   and c[1].get("chat_id") == 888]
        prova("A UN MINUTO dalla fine: UN messaggio nuovo (che suona) «Manca 1 minuto» con "
              "le parole dell'on-chain e il bottone dello scambio (non rosso: tempo di ore); "
              "il giro dopo non lo ripete", (1, True, True, False),
              (len(uno_min), bool(uno_min) and "⏰ Manca 1 minuto: hai già mandato gli"
               in uno_min[0][1]["text"],
               bool(uno_min) and "?scambio=bar-onchain-" in json.dumps(
                   uno_min[0][1].get("reply_markup")),
               bool(uno_min) and '"style"' in json.dumps(uno_min[0][1].get("reply_markup"))))
        prova("...e a chi aspetta (999) l'avviso a un minuto NON arriva: e' di chi paga",
              [], [c for c in mie_e()[n_prima:] if c[0] == "sendMessage"
                   and c[1].get("chat_id") == 999])
        gesto(999, o5e["id"], "chiedi-annullo")
    finally:
        SRV.bot_api = vecchio_bot
        SRV.P2P_CONTO_ALLA_ROVESCIA = True

    print("\n[chiedi di annullare: chi ha depositato lo chiede, chi compra decide]")
    o4 = pubblica(999).json()
    gesto(888, o4["id"], "prendi")
    r = gesto(999, o4["id"], "chiedi-annullo")
    prova("niente depositato: si annulla da soli, 409", (409, True),
          (r.status_code, "usa «Annulla»" in r.json()["detail"]))
    o4 = uno(999, o4["id"])
    paga(o4)
    gesto(999, o4["id"], "controlla")
    prova("lo chiede solo chi ha depositato: 403", 403,
          gesto(888, o4["id"], "chiedi-annullo").status_code)
    banco.DETTO.clear()
    r = gesto(999, o4["id"], "chiedi-annullo")
    prova("deposito valido: chiesto, e chi compra lo sa col bottone, con "
          "l'avvertenza di non rinunciare se ha gia' pagato",
          (200, True, True, True),
          (r.status_code, r.json()["avvisato"], detto_a(888, "ti chiede di annullare"),
           detto_a(888, "non rinunciare")))
    prova("...e la pagina lo dice a tutt'e due", (True, True),
          (uno(999, o4["id"])["annullo_chiesto_il"] > 0,
           uno(888, o4["id"])["annullo_chiesto_il"] > 0))
    # (18 nov 2026, Andrea: «Sì, toglilo») ...e a chi compra la rinuncia non
    # conta piu': il foglio di «Rinuncio» non lo minaccia
    prova("...e chiesto l'annullo, la rinuncia di chi compra non gli conta piu'",
          False, uno(888, o4["id"])["rinuncia_conta"])
    banco.DETTO.clear()
    r = gesto(999, o4["id"], "chiedi-annullo")
    prova("una seconda volta subito: nessun avviso nuovo (uno all'ora)",
          (200, False, False), (r.status_code, r.json()["avvisato"],
                                detto_a(888, "ti chiede di annullare")))
    gesto(888, o4["id"], "euro-inviati")
    r = gesto(999, o4["id"], "chiedi-annullo")
    prova("dopo «Ho inviato gli euro» non si chiede piu': 409 (sarebbe un "
          "trucco per farsi regalare il rimborso)", (409, True),
          (r.status_code, "già pagato" in r.json()["detail"]))
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 12) gli avvisi, tutti ----------------------------------------------
    print("\n[ogni avviso a una parte porta il bottone del suo scambio]")
    # (17 nov 2026) l'avviso della recensione ricevuta e' quello di sempre,
    # del mercatino e di Lightning: non e' un avviso dello scambio
    nudi = [t[:60] for chi, t, b in BOTTONI
            if chi in (999, 888) and not (b and b[0] in ("🟠 Apri lo scambio",
                                                         "🚫 Non ripubblicarlo")
                                          and "?scambio=bar-onchain-" in b[1])
            and "Hai ricevuto una recensione" not in t
            # (19 nov 2026) la meta' della cauzione la dice il registro «da
            # riscuotere», la strada di sempre: non e' un avviso dello scambio
            and "della metà di una cauzione da incassare" not in t]
    prova("in tutto il giro nessun avviso alle parti parte senza il bottone, "
          "e il segno della catena ⛓️ non c'e' piu' in nessuno",
          ([], [], True),
          (nudi, [t[:60] for chi, t, b in BOTTONI if "⛓️" in t], len(BOTTONI) >= 12))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


def cofirma_storta(o, tg, radice, PSBT, finalize_psbt, psbt_di):
    """Una transazione completa ma DIVERSA dalla proposta: stesse monete,
    un'uscita in meno. Serve a provare che il server confronta i txid."""
    p = psbt_di(o, [(o["rimborso"], o["importo_sats"] - 300)], tg)
    # la seconda firma con la chiave dell'altra parte non c'e': basta che
    # sia leggibile e che il txid non torni
    p.sign_with(radice(tg).derive(
        f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
    try:
        return finalize_psbt(p).serialize().hex()
    except Exception:
        return p.tx.serialize().hex()


if __name__ == "__main__":
    sys.exit(main())
