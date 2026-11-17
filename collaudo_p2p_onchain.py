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
    # metti 500»): ONCHAIN_MAX_EURO, non P2P_MAX_EURO del Lightning
    vecchi = (SRV.ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO, SRV.p2p_onchain_giudica_nuovo)
    SRV.ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO = 500, 250
    visti = []
    def spia(*a, **k):
        visti.append(a[5])
        return vecchi[2](*a, **k)
    SRV.p2p_onchain_giudica_nuovo = spia
    try:
        r6 = pubblica(999, euro_cent=60000)
        busta = libro()["onchain"]
    finally:
        SRV.ONCHAIN_MAX_EURO, SRV.P2P_MAX_EURO, SRV.p2p_onchain_giudica_nuovo = vecchi
    prova("il tetto degli scambi on-chain e' ONCHAIN_MAX_EURO (500), non "
          "quello del P2P Lightning (250): 600 € no «fino a 500 €», e il "
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
    r = gesto(888, oid, "prendi")
    o = r.json()
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
           detto_a(999, "annullato lo scambio")))
    prova("niente sull'indirizzo: resta preso", "preso",
          gesto(999, oid, "controlla").json()["stato"])
    paga(oa, confermata=False)
    d = gesto(999, oid, "controlla").json()
    prova("visti ma non confermati: ancora preso, e lo si vede",
          ("preso", 101080, 0), (d["stato"], d["visti_sats"], d["ricevuti_sats"]))
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
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=? WHERE id=?",
                (int(time.time()) - 25 * 3600, o8["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("25 ore dopo il deposito, senza «Ho inviato»: la ronda avvisa tutt'e "
          "due, e lo scambio resta depositato (niente si annulla)",
          (True, True, "depositato"),
          (detto_a(999, "Il tempo per pagare è finito"),
           detto_a(888, "Il tempo per pagare è finito"), uno(999, o8["id"])["stato"]))
    prova("...e a chi paga non arriva anche il terzo promemoria: il tempo finito lo "
          "ha superato", False, detto_a(888, "Promemoria") or detto_a(888, "Mancano quattro ore"))
    banco.DETTO.clear()
    asyncio.run(SRV._p2p_onchain_ronda())
    prova("...la ronda dopo non lo ripete", (False, False),
          (detto_a(999, "tempo per pagare"), detto_a(888, "tempo per pagare")))
    # I PROMEMORIA (17 nov 2026, cantiere onchain-chat-sollecito)
    print("\n[la ronda: i promemoria a chi paga e a chi libera]")
    o9 = pubblica(999, sats=30000, euro_cent=2700, metodi=["Bonifico"]).json()
    gesto(888, o9["id"], "prendi")
    paga(uno(999, o9["id"]))
    gesto(999, o9["id"], "controlla")
    con = SRV.db()
    con.execute("UPDATE p2p_onchain_ordini SET depositato_il=? WHERE id=?",
                (int(time.time()) - 2 * 3600, o9["id"]))
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
    SRV.P2P_CONTANTI_MAX_EURO = tetto_c
    SRV.P2P_ONCHAIN_APERTI_MAX = tetto

    # ---- 12) gli avvisi, tutti ----------------------------------------------
    print("\n[ogni avviso a una parte porta il bottone del suo scambio]")
    # (17 nov 2026) l'avviso della recensione ricevuta e' quello di sempre,
    # del mercatino e di Lightning: non e' un avviso dello scambio
    nudi = [t[:60] for chi, t, b in BOTTONI
            if chi in (999, 888) and not (b and b[0] == "🟠 Apri lo scambio"
                                          and "?scambio=bar-onchain-" in b[1])
            and "Hai ricevuto una recensione" not in t]
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
