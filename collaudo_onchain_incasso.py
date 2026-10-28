# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'INCASSO SU UN WALLET PROPRIO E DELLA QUOTA (27 ott 2026,
cantiere onchain-incasso-esterno, richiesta di Andrea) — il giro col
SERVER VERO, per HTTP (TestClient, la app vera):
- «Dove ricevi i sats»: chi vende sceglie una vpub del suo wallet o un
  indirizzo suo, la scelta e' firmata dal suo seme (chiave `/2/0` del
  conto del 2-di-3) e il server la verifica; senza firma, o con la firma
  di un altro seme, no. Un seme nuovo la cancella.
- la cassa: l'incasso dell'ordine nasce dalla destinazione (un indirizzo
  nuovo della vpub a ogni vendita), e la quota fissa entra nell'importo;
- la quota si cambia dal pannello (solo admin, pavimento e tetto, una
  riga nel registro), e il pannello vince sul config;
- il rilascio: il PSBT deve portare la quota esatta a Barattolo;
- «Solo gli admin» si spegne dal pannello, e torna al config.

IL «TELEFONO» QUI E' EMBIT, come negli altri collaudi on-chain: che il
telefono vero (il bundle) firmi destinazioni che il server legge lo dice
prove_incasso_esterno_onchain. MEMPOOL E' DI CARTONE. Nessuna rete,
nessun sats.

USO:  python collaudo_onchain_incasso.py
"""
import hashlib
import json
import os
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def firma_compatta(chiave, messaggio: bytes) -> str:
    """La firma come la fa il telefono (@scure/bip32: r||s, 64 byte),
    dalla firma DER di embit."""
    der = chiave.sign(hashlib.sha256(messaggio).digest()).serialize()
    lr = der[3]
    r = der[4:4 + lr]
    s = der[6 + lr:]
    return (r[-32:].rjust(32, b"\0") + s[-32:].rjust(32, b"\0")).hex()


def main():
    print("=" * 58)
    print("  L'INCASSO SU UN WALLET PROPRIO E LA QUOTA — il giro vero")
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
            # il wallet del venditore FUORI da Barattolo, e il suo seme nuovo
            "wallet": vett["bip39_english"][2]["parole"],
            "nuovo": vett["bip39_english"][3]["parole"]}

    def radice(tg, versione=None):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=versione or N["xprv"])

    def conto(tg):
        return radice(tg).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=N["xpub"])

    def firma_dest(tg, tipo, valore):
        msg = SRV.onchain_messaggio_destinazione(tipo, valore)
        return firma_compatta(radice(tg).derive("m/48h/1h/0h/2h/2/0").key, msg)

    vpub = radice("wallet", b"\x04\x5f\x18\xbc").derive(
        "m/84h/1h/0h").to_public().to_base58()

    def dal_wallet(i):
        k = radice("wallet").derive(f"m/84h/1h/0h/0/{i}")
        return script.p2wpkh(k.key.get_public_key()).address(N)

    MONETE = {}

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0

    async def invia_finta(tx_hex):
        return Transaction.from_string(tx_hex).txid().hex()

    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta
    SRV.onchain_mempool_invia = invia_finta

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan"), (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    annunci = []
    for n in range(5):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(888,?,'una cosa',50000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Cosa per il wallet {n}",))
        annunci.append(cur.lastrowid)
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888]
    SRV.ONCHAIN_ATTIVO = True

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def scegli(tg, **corpo):
        come(tg)
        return c.post("/api/onchain/incasso", json=corpo)

    def compra(tg, aid):
        come(tg)
        return c.post("/api/orders", json={"annuncio_id": aid,
                                           "consegna": "ritiro",
                                           "metodo": "onchain",
                                           "offerta_id": 0})

    def leva(tg, **corpo):
        come(tg)
        return c.post("/api/admin/leve/ONCHAIN_QUOTA_FISSA_SATS", json=corpo)

    def riga_leva():
        come(999)
        for g in c.get("/api/admin/leve").json()["gruppi"]:
            for v in g["voci"]:
                if v["chiave"] == "ONCHAIN_QUOTA_FISSA_SATS":
                    return v
        return {}

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})

    # ---- 1) dove ricevi --------------------------------------------------
    print("\n[«Dove ricevi i sats»: la scelta firmata dal seme]")
    come(888)
    prova("di serie: nessuna destinazione, quota 0", (None, 0),
          tuple(c.get("/api/onchain/prova").json()[k]
                for k in ("incasso", "quota_sats")))
    r = scegli(888, tipo="xpub", valore=vpub, firma="00" * 64)
    prova("una firma qualunque: 400", (400, True),
          (r.status_code, "non è firmata dal tuo seme" in r.json()["detail"]))
    r = scegli(888, tipo="xpub", valore=vpub,
               firma=firma_dest(999, "xpub", vpub))
    prova("la firma di un ALTRO seme: 400", 400, r.status_code)
    r = scegli(888, tipo="xpub", valore=conto(888),
               firma=firma_dest(888, "xpub", conto(888)))
    prova("la chiave del 2-di-3 al posto del wallet: 400", (400, True),
          (r.status_code, "2-di-3" in r.json()["detail"]))
    r = scegli(888, tipo="indirizzo",
               valore="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", firma="")
    prova("un indirizzo mainnet: 400", 400, r.status_code)
    r = scegli(888, tipo="xpub", valore=vpub, firma=firma_dest(888, "xpub", vpub))
    prova("la vpub del suo wallet, firmata dal suo seme: 200", 200,
          r.status_code)
    come(888)
    prova("...e il foglio la rilegge com'e', firma compresa", "xpub",
          (c.get("/api/onchain/prova").json()["incasso"] or {}).get("tipo"))

    # ---- 2) la quota dal pannello ----------------------------------------
    print("\n[la quota fissa: dal pannello, con i suoi no]")
    prova("chi non e' admin: 403", 403, leva(111, valore=600).status_code)
    come(999)
    # dal 27 ott 2026 si aprono quasi tutte: la terza chiave e' una «mai»
    prova("una leva che resta del VPS: 404", 404,
          c.post("/api/admin/leve/ONCHAIN_XPUB", json={"valore": "x"}).status_code)
    r = leva(999, valore=500)
    prova("500 sats: 400, sotto la polvere la rete non trasmette", (400, True),
          (r.status_code, "polvere" in r.json()["detail"]))
    prova("sopra il tetto: 400", 400, leva(999, valore=5001).status_code)
    prova("il pannello la dice com'e': 0, dal codice", (0, "codice"),
          (riga_leva().get("valore"),
           (riga_leva().get("scrivibile") or {}).get("origine")))
    r = leva(999, valore=600)
    prova("600 sats: 200, e vince sul config", (200, 600, "pannello"),
          (r.status_code, r.json().get("valore"), r.json().get("origine")))
    prova("...il pannello la rilegge", (600, "pannello"),
          (riga_leva().get("valore"),
           (riga_leva().get("scrivibile") or {}).get("origine")))
    con = SRV.db()
    reg = con.execute("SELECT motivo, deciso_da FROM moderazione_log WHERE "
                      "strato='leva' ORDER BY rowid DESC LIMIT 1").fetchone()
    con.close()
    prova("...e il registro sa chi e da quanto a quanto",
          ("ONCHAIN_QUOTA_FISSA_SATS: 0 → 600 (pannello)", 999),
          (reg["motivo"], reg["deciso_da"]) if reg else None)
    come(999)
    prova("la cassa la dice PRIMA di pagare", 600,
          c.get("/api/onchain/pronto/888").json().get("quota_sats"))

    # ---- 3) la cassa -------------------------------------------------------
    print("\n[la cassa: l'incasso dal wallet, la quota nell'importo]")
    r = compra(999, annunci[0])
    o = r.json().get("onchain") or {}
    prova("l'ordine nasce: prezzo + quota + margine (50000 + 600 + 1080)",
          (200, 50000, 600, 51680),
          (r.status_code, o.get("prezzo_sats"), o.get("quota_sats"),
           o.get("importo_sats")))
    prova("...l'incasso e' il primo indirizzo del wallet (/0/0)",
          (dal_wallet(0), "xpub", 0),
          (o.get("incasso"), (o.get("destinazione") or {}).get("tipo"),
           (o.get("destinazione") or {}).get("indice")))
    xb = SRV.onchain_xpub_barattolo()[0]
    prova("...e la quota va a un indirizzo di Barattolo (/1/n della sua xpub)",
          True, o.get("quota_indirizzo", "").startswith("tb1q")
          and o["quota_indirizzo"] == SRV.onchain_incasso(xb, 0))
    o2 = compra(999, annunci[1]).json().get("onchain") or {}
    prova("la vendita dopo prende l'indirizzo dopo (/0/1)", dal_wallet(1),
          o2.get("incasso"))

    # ---- 4) il rilascio con la quota ---------------------------------------
    print("\n[il rilascio: la quota esatta a Barattolo]")
    oid = o["id"]
    MONETE[o["indirizzo"]["indirizzo"]] = [{
        "txid": "ee" * 32, "vout": 0, "value": o["importo_sats"],
        "status": {"confirmed": True}}]
    come(999)
    c.post(f"/api/onchain/ordini/{oid}/controlla")
    come(999)
    o = next(x for x in c.get("/api/onchain/ordini").json()["ordini"]
             if x["id"] == oid)
    prova("pagato", "pagato", o["stato"])

    def psbt_di(o, uscite, chi):
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
        p.sign_with(radice(chi).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        return p

    def proponi(p):
        come(999)
        return c.post(f"/api/onchain/ordini/{oid}/proposta",
                      json={"verso": "venditore", "psbt": p.to_string()})

    resto = o["importo_sats"] - 50000 - 600 - 400
    r = proponi(psbt_di(o, [(o["incasso"], 50000), (o["rimborso"], resto + 600)], 999))
    prova("senza la quota: 400", (400, True),
          (r.status_code, "quota" in r.json()["detail"]))
    r = proponi(psbt_di(o, [(o["incasso"], 50000), (o["quota_indirizzo"], 1000),
                            (o["rimborso"], resto - 400)], 999))
    prova("con una quota piu' grossa: 400", 400, r.status_code)
    r = proponi(psbt_di(o, [(o["incasso"], 50000), (o["quota_indirizzo"], 600),
                            (o["rimborso"], resto)], 999))
    prova("prezzo al wallet, quota a Barattolo, resto a chi compra: 200",
          200, r.status_code)
    come(888)
    o8 = next(x for x in c.get("/api/onchain/ordini").json()["ordini"]
              if x["id"] == oid)
    p = PSBT.from_string(o8["proposta"]["psbt"])
    p.sign_with(radice(888).derive(
        f"m/48h/1h/0h/2h/0/{o8['indirizzo']['mio_numero']}").key)
    come(888)
    r = c.post(f"/api/onchain/ordini/{oid}/firma",
               json={"tx": finalize_psbt(p).serialize().hex()})
    prova("la seconda firma del venditore: rilasciato", (200, "rilasciato"),
          (r.status_code, r.json().get("stato")))

    # ---- 5) l'indirizzo fisso, il ritorno, il seme nuovo --------------------
    print("\n[l'indirizzo fisso, il conto di serie, il seme nuovo]")
    fisso = dal_wallet(7).upper()
    r = scegli(888, tipo="indirizzo", valore=fisso,
               firma=firma_dest(888, "indirizzo", fisso.lower()))
    prova("un indirizzo fisso (anche scritto in maiuscolo): 200", 200,
          r.status_code)
    o3 = compra(999, annunci[2]).json().get("onchain") or {}
    prova("...e la vendita arriva li'", dal_wallet(7), o3.get("incasso"))
    prova("togliere la scelta: 200, senza firme", 200,
          scegli(888, tipo="barattolo").status_code)
    come(888)
    prova("...e il profilo lo dice: dove ricevo = ''", "",
          c.get("/api/me").json().get("onchain_incasso"))
    # MAI NEL CONTO DI BARATTOLO, MA SI PAGA LO STESSO (27 ott 2026,
    # Andrea: «un utente paga [...] quello è solo l'output finale ma può
    # definirlo in un secondo momento, l'importante è che il multisig si
    # crei con i 3 wallet già predefiniti»): il 2-di-3 nasce, l'incasso
    # resta VUOTO, e verso chi vende non esce niente finche' non sceglie
    print("\n[chi vende sceglie dove ricevere DOPO il pagamento]")
    come(999)
    prova("la cassa: pronto anche senza destinazione", True,
          c.get("/api/onchain/pronto/888").json()["pronto"])
    r = compra(999, annunci[4])
    o5 = r.json().get("onchain") or {}
    prova("l'ordine nasce: 200, 2-di-3 vero, incasso vuoto, nessuna "
          "destinazione", (200, True, "", None),
          (r.status_code, o5.get("indirizzo", {}).get("indirizzo", "").startswith("tb1q"),
           o5.get("incasso"), o5.get("destinazione")))
    oid5 = o5["id"]
    MONETE[o5["indirizzo"]["indirizzo"]] = [{
        "txid": "dd" * 32, "vout": 0, "value": o5["importo_sats"],
        "status": {"confirmed": True}}]
    come(999)
    c.post(f"/api/onchain/ordini/{oid5}/controlla")
    come(999)
    o5 = next(x for x in c.get("/api/onchain/ordini").json()["ordini"]
              if x["id"] == oid5)
    prova("pagato, e nato in «Ordini»", ("pagato", True),
          (o5["stato"], bool(o5.get("ordine_id"))))
    come(888)
    riass = next(x["onchain"] for x in c.get("/api/orders").json()
                 if (x.get("onchain") or {}).get("id") == oid5)
    prova("...e chi vende lo vede nell'ordine: incasso non scelto", False,
          riass.get("incasso_scelto"))
    come(999)
    prova("una proposta verso chi vende senza incasso: 409 col perche'",
          (409, SRV.ONCHAIN_MSG_SENZA_DESTINAZIONE),
          (lambda r: (r.status_code, r.json().get("detail")))(
              c.post(f"/api/onchain/ordini/{oid5}/proposta",
                     json={"verso": "venditore", "psbt": "cHNidP8="})))
    # la conferma si firma col seme di chi compra (28 ott 2026)
    ricevuto5 = firma_compatta(
        radice(999).derive("m/48h/1h/0h/2h/2/0").key,
        SRV.onchain_messaggio_ricevuto(oid5, o5["indirizzo"]["indirizzo"]))
    come(888)
    prova("«ho ricevuto» lo dice solo chi compra: 403", 403,
          c.post(f"/api/onchain/ordini/{oid5}/rilascio-chiesto",
                 json={"firma": ricevuto5}).status_code)
    come(999)
    prova("...una conferma senza la firma del suo seme: 400", 400,
          c.post(f"/api/onchain/ordini/{oid5}/rilascio-chiesto",
                 json={}).status_code)
    prova("...una firma d'un altro seme: 400", 400,
          c.post(f"/api/onchain/ordini/{oid5}/rilascio-chiesto",
                 json={"firma": firma_compatta(
                     radice(888).derive("m/48h/1h/0h/2h/2/0").key,
                     SRV.onchain_messaggio_ricevuto(
                         oid5, o5["indirizzo"]["indirizzo"]))}).status_code)
    prova("chi compra conferma: 200, la conferma resta scritta", 200,
          c.post(f"/api/onchain/ordini/{oid5}/rilascio-chiesto",
                 json={"firma": ricevuto5}).status_code)
    fisso9 = dal_wallet(9)
    r = scegli(888, tipo="indirizzo", valore=fisso9,
               firma=firma_dest(888, "indirizzo", fisso9))
    prova("chi vende sceglie adesso: 200, e l'ordine che aspettava si "
          "aggiorna", (200, 1), (r.status_code, r.json().get("ordini_aggiornati")))
    come(999)
    o5 = next(x for x in c.get("/api/onchain/ordini").json()["ordini"]
              if x["id"] == oid5)
    prova("...l'incasso e' quello scelto, con la firma del suo seme",
          (fisso9, "indirizzo", True),
          (o5["incasso"], (o5.get("destinazione") or {}).get("tipo"),
           bool(o5.get("rilascio_chiesto_il"))))
    q5 = int(o5.get("quota_sats") or 0)
    uscite5 = [(o5["incasso"], 50000)]
    if q5:
        uscite5.append((o5["quota_indirizzo"], q5))
    uscite5.append((o5["rimborso"], o5["importo_sats"] - 50000 - q5 - 400))
    come(999)
    r = c.post(f"/api/onchain/ordini/{oid5}/proposta",
               json={"verso": "venditore",
                     "psbt": psbt_di(o5, uscite5, 999).to_string()})
    prova("...e la firma di chi compra verso quell'incasso passa: 200", 200,
          r.status_code)
    r = scegli(888, tipo="barattolo")
    prova("di nuovo senza scelta (per il resto del giro)", 200, r.status_code)

    # IL CONTROLLO DI QUEL CHE SI INCOLLA (27 ott 2026)
    print("\n[il controllo di un indirizzo incollato: buono? gia' usato?]")
    SCHEDE = {}

    async def scheda_finta(indirizzo):
        if indirizzo not in SCHEDE:
            raise RuntimeError("mempool muto")
        return SCHEDE[indirizzo]

    SRV.onchain_mempool_indirizzo = scheda_finta

    def guarda(**corpo):
        come(888)
        return c.post("/api/onchain/incasso/controlla", json=corpo).json()

    nuovo, usato = dal_wallet(20), dal_wallet(21)
    SCHEDE[nuovo] = {"chain_stats": {"tx_count": 0}, "mempool_stats": {"tx_count": 0}}
    SCHEDE[usato] = {"chain_stats": {"tx_count": 2}, "mempool_stats": {"tx_count": 1}}
    prova("un indirizzo mai usato: buono, non usato", (True, False, 0),
          tuple(guarda(tipo="indirizzo", valore=nuovo)[k] for k in ("ok", "usato", "tx")))
    prova("uno gia' passato in rete: buono, ma usato (3 tx)", (True, True, 3),
          tuple(guarda(tipo="indirizzo", valore=usato.upper())[k]
                for k in ("ok", "usato", "tx")))
    prova("mempool muto: buono, e «non so»", (True, None),
          tuple(guarda(tipo="indirizzo", valore=dal_wallet(22))[k] for k in ("ok", "usato")))
    x = guarda(tipo="indirizzo", valore="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
    prova("un indirizzo mainnet: no, col perche'", (False, True),
          (x["ok"], "tb1" in x["motivo"]))
    prova("la vpub del wallet: buona (la domanda «usato» non c'e')",
          (True, False), tuple(guarda(tipo="xpub", valore=vpub)[k] for k in ("ok", "usato")))
    x = guarda(tipo="xpub", valore=radice("wallet").derive("m/84h/1h/0h").to_base58())
    prova("una chiave PRIVATA: no, e lo dice", (False, True),
          (x["ok"], "PRIVATA" in x["motivo"]))
    prova("...e il controllo non scrive niente", None,
          (lambda: (come(888), c.get("/api/onchain/prova").json()["incasso"])[1])())

    r = scegli(888, tipo="xpub", valore=vpub, firma=firma_dest(888, "xpub", vpub))
    come(888)
    prova("di nuovo la vpub: il profilo dice «xpub»", (200, "xpub"),
          (r.status_code, c.get("/api/me").json().get("onchain_incasso")))
    o4 = compra(999, annunci[3]).json().get("onchain") or {}
    prova("...e la vendita torna a nascere, sul wallet", (True, "xpub"),
          (o4.get("incasso", "").startswith("tb1"),
           (o4.get("destinazione") or {}).get("tipo")))
    scegli(888, tipo="xpub", valore=vpub, firma=firma_dest(888, "xpub", vpub))
    semi[888] = semi["nuovo"]
    come(888)
    c.post("/api/onchain/xpub", json={"xpub": conto(888)})
    prova("un seme nuovo: la destinazione firmata dal vecchio si cancella",
          None, c.get("/api/onchain/prova").json()["incasso"])

    # ---- 6) la porticina dal pannello (27 ott 2026) ----------------------
    print("\n[«Solo gli admin» dal pannello]")
    come(111)
    prova("chi non e' admin: l'on-chain non esiste", 404,
          c.get("/api/onchain/prova").status_code)
    come(999)
    r = c.post("/api/admin/leve/ONCHAIN_SOLO_ADMIN", json={"valore": "forse"})
    prova("una parola che non e' si' o no: 400", 400, r.status_code)
    r = c.post("/api/admin/leve/ONCHAIN_SOLO_ADMIN", json={"valore": False})
    prova("l'admin la spegne dal pannello: 200, dal pannello",
          (200, False, "pannello"),
          (r.status_code, r.json().get("valore"), r.json().get("origine")))
    come(111)
    prova("...e chi non e' admin vede l'on-chain", 200,
          c.get("/api/onchain/prova").status_code)
    come(999)
    c.post("/api/admin/leve/ONCHAIN_SOLO_ADMIN", json={"torna_al_config": True})
    come(111)
    prova("«Torna al config»: di nuovo solo gli admin", 404,
          c.get("/api/onchain/prova").status_code)

    # ---- 7) la leva torna al config -----------------------------------------
    r = leva(999, torna_al_config=True)
    prova("«Torna al config»: 0, dal codice", (200, 0, "codice"),
          (r.status_code, r.json().get("valore"), r.json().get("origine")))

    SRV.ONCHAIN_ATTIVO = False
    prova("leva spenta: «Dove ricevi» dice 404", 404,
          scegli(888, tipo="barattolo").status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
