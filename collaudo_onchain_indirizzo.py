# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'INDIRIZZO DELL'ORDINE ON-CHAIN (20 ott 2026, cantiere
onchain-tappa2) — il giro col SERVER VERO, per HTTP (TestClient, la app
vera), della tappa 2: due admin accendono l'on-chain dando la loro xpub
dedicata, uno fa un indirizzo con l'altro, e il server lo calcola con
embit; poi i no.

`prove.py` guarda i pezzi uno per uno, e confronta embit col codice del
telefono byte per byte. Qui gira la STORIA: il cancello a leva spenta e
accesa, chi non e' admin, le chiavi private e quelle di mainnet
rifiutate senza ripeterle, la controparte che non ha acceso, i numeri
che crescono e non si ripetono da una parte e dall'altra, la xpub
dell'altro che non esce mai, la stessa xpub su due conti, embit che
manca (503, e la lettura vive lo stesso), la terza chiave storta nel
config, il pannello delle leve.

IL «TELEFONO» QUI E' EMBIT: le xpub dedicate si fanno con embit dai
vettori ufficiali del BIP-39 (semi pubblicati in uno standard, di
nessuno), e la chiave di ciascuno si rifa' da quel seme. Che il telefono
vero dia gli stessi byte lo dice prove_indirizzo_ordine_onchain. Nessuna
rete, nessun sats: signet, config di cartone e database usa-e-getta dal
banco dei pagamenti, PRIMA dell'import del server.

USO:  python collaudo_onchain_indirizzo.py
"""
import json
import os
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  L'INDIRIZZO DELL'ORDINE ON-CHAIN (tappa 2) — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from embit import bip32, bip39
    from embit.descriptor import Descriptor
    from embit.networks import NETWORKS
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    vett = json.load(open(os.path.join(banco.QUI, "vendor",
                                       "vettori-bip.json"), encoding="utf-8"))
    semi = [v["parole"] for v in vett["bip39_english"][:3]]

    def radice(parole):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(parole),
                                     version=NETWORKS["signet"]["xprv"])

    def conto(parole, rete="signet"):
        return radice(parole).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=NETWORKS[rete]["xpub"])

    def chiave_mia(parole, n):
        return radice(parole).derive(f"m/48h/1h/0h/2h/0/{n}").key.get_public_key().sec().hex()

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (888, "Alan"), (777, "Terzo"),
                     (111, "Compra")):
        con.execute("INSERT OR IGNORE INTO utenti(tg_id, nome) VALUES (?,?)",
                    (tg, nome))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888, 777]
    PROVA, XPUB = "/api/onchain/prova", "/api/onchain/xpub"
    INDIRIZZO = "/api/onchain/prova/indirizzo"

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def dai(tg, xpub):
        come(tg)
        return c.post(XPUB, json={"xpub": xpub})

    def fai(tg, altro):
        come(tg)
        return c.post(INDIRIZZO, json={"venditore_id": altro})

    def leggi(tg):
        come(tg)
        return c.get(PROVA)

    # ---- 1) il cancello ---------------------------------------------
    print("\n[il cancello: a leva spenta non esiste niente]")
    prova("di serie la leva e' spenta e la rete e' signet",
          (False, True, "signet"),
          (SRV.ONCHAIN_ATTIVO, SRV.ONCHAIN_SOLO_ADMIN, SRV.ONCHAIN_RETE))
    prova("...e le tre porte dicono 404, anche all'admin",
          [404, 404, 404],
          [leggi(999).status_code, dai(999, conto(semi[0])).status_code,
           fai(999, 888).status_code])
    SRV.ONCHAIN_ATTIVO = True
    prova("accesa: a chi non e' admin ancora 404, dalle tre porte",
          [404, 404, 404],
          [leggi(111).status_code, dai(111, conto(semi[0])).status_code,
           fai(111, 999).status_code])
    r = leggi(999)
    d = r.json()
    prova("all'admin la prova risponde: signet, il conto BIP-48, embit, "
          "niente ancora", (200, "signet", "m/48'/1'/0'/2'", True, "", [], []),
          (r.status_code, d["rete"], d["strada"], d["embit"], d["mia_xpub"],
           d["controparti"], d["indirizzi"]))

    # ---- 2) la xpub dedicata ------------------------------------------
    print("\n[accendi l'on-chain: solo la meta' pubblica, solo signet]")
    privata = radice(semi[0]).derive("m/48h/1h/0h/2h").to_string(
        version=NETWORKS["signet"]["xprv"])
    rifiuti = {"privata": privata, "mainnet": conto(semi[0], "main"),
               "storta": "tpubNONSONOUNACHIAVE"}
    risposte = {k: dai(999, v) for k, v in rifiuti.items()}
    prova("una privata, una di mainnet, una storta: 400", [400, 400, 400],
          [r.status_code for r in risposte.values()])
    prova("...la privata col suo motivo, e nessuna risposta ripete la chiave",
          (True, []),
          ("PRIVATA" in risposte["privata"].json()["detail"],
           [k for k, r in risposte.items() if rifiuti[k][:20] in r.text]))
    prova("...e niente e' stato scritto", "", leggi(999).json()["mia_xpub"])
    x999, x888 = conto(semi[0]), conto(semi[1])
    r = dai(999, x999)
    prova("la tpub del conto: 200, e la risposta non la ripete",
          (200, {"ok": True}), (r.status_code, r.json()))
    prova("...la prova la ridice a lui, e a lui solo", (x999, ""),
          (leggi(999).json()["mia_xpub"], leggi(888).json()["mia_xpub"]))
    prova("...ridarla uguale (un altro telefono, lo stesso seme) va bene", 200,
          dai(999, x999).status_code)

    # ---- 3) l'indirizzo -------------------------------------------------
    print("\n[un indirizzo vero fra due admin]")
    r = fai(999, 888)
    prova("con chi non ha acceso l'on-chain: 400, e lo dice",
          (400, True), (r.status_code, "non ha ancora acceso" in r.json()["detail"]))
    r = fai(999, 111)
    prova("con chi non e' ammesso: 400", (400, True),
          (r.status_code, "non può usare" in r.json()["detail"]))
    prova("con se stesso: 400", 400, fai(999, 999).status_code)
    dai(888, x888)
    prova("acceso anche Alan: Andrea lo vede fra le controparti, e non vede "
          "se stesso", [{"id": 888, "nome": "Alan"}],
          leggi(999).json()["controparti"])
    uno, due = fai(999, 888), fai(999, 888)
    a, b = uno.json(), due.json()
    prova("due indirizzi: 200, compratore, numeri 0 e 1, controparte per nome",
          (200, 200, "compratore", 0, 1, "Alan"),
          (uno.status_code, due.status_code, a["ruolo"], a["mio_numero"],
           b["mio_numero"], a["controparte"]))
    prova("...di signet, col checksum, e diversi fra loro", (True, True, True),
          (a["indirizzo"].startswith("tb1q"), a["descrittore"][-9] == "#",
           a["indirizzo"] != b["indirizzo"]))
    prova("...la chiave del compratore e' quella del SUO seme a quel numero "
          "(il telefono la ritrova)",
          [chiave_mia(semi[0], 0), chiave_mia(semi[0], 1)],
          [a["chiavi"]["compratore"], b["chiavi"]["compratore"]])
    corpo = a["descrittore"].split("#")[0]
    prova("...e l'indirizzo e' quello del descrittore", a["indirizzo"],
          Descriptor.from_string(corpo).address(NETWORKS["signet"]))
    prova("...e le xpub delle persone NON escono, ne' da lui ne' dalla prova",
          [False, False],
          [x888 in uno.text, x888 in leggi(999).text])
    r = leggi(888).json()
    prova("Alan li vede da venditore, coi SUOI numeri 0 e 1, e le stesse "
          "chiavi", (["venditore", "venditore"], [1, 0], [True, True],
                     [chiave_mia(semi[1], 1), chiave_mia(semi[1], 0)]),
          ([x["ruolo"] for x in r["indirizzi"]],
           [x["mio_numero"] for x in r["indirizzi"]],
           [x["indirizzo"] in (a["indirizzo"], b["indirizzo"])
            for x in r["indirizzi"]],
           [x["chiavi"]["venditore"] for x in r["indirizzi"]]))
    tre = fai(888, 999).json()
    prova("al contrario (Alan compra): i numeri proseguono la fila di "
          "ciascuno, 2 e 2, e Barattolo 2", (2, 2, True),
          (tre["mio_numero"], leggi(999).json()["indirizzi"][0]["mio_numero"],
           tre["chiavi"]["barattolo"] == SRV.onchain_chiave(SRV.XPUB_CARTONE, 2)))
    dai(777, x999)
    r = fai(999, 777)
    prova("la STESSA xpub su due conti: 400 (sarebbe una persona con due "
          "firme)", (400, True),
          (r.status_code, "stessa chiave" in r.json()["detail"]))

    # ---- 4) embit che manca, la terza chiave storta ---------------------
    print("\n[embit che manca, la terza chiave, il pannello]")
    SRV.EMBIT = False
    prova("senza embit: le due porte che fanno i conti dicono 503, la "
          "lettura vive e lo dice", [503, 503, 200, False],
          [dai(999, x999).status_code, fai(999, 888).status_code,
           leggi(999).status_code, leggi(999).json()["embit"]])
    voci = {v["chiave"]: v for g in SRV._leve_stato() for v in g["voci"]}
    prova("...e il pannello lo dice con l'allarme", (False, True),
          (voci["pip install embit"]["valore"],
           voci["pip install embit"].get("allarme")))
    SRV.EMBIT = True
    SRV.ONCHAIN_XPUB = conto(semi[2], "main")
    r = fai(999, 888)
    prova("una terza chiave di MAINNET nel config: 503, senza ripeterla",
          (503, False), (r.status_code, SRV.ONCHAIN_XPUB[:20] in r.text))
    SRV.ONCHAIN_XPUB = conto(semi[2])
    r = fai(999, 888).json()
    prova("una tpub vera: l'indirizzo nasce, non di cartone, con la chiave "
          "numero 0 della SUA fila", (False, True),
          (r["cartone"], r["chiavi"]["barattolo"]
           == SRV.onchain_chiave(SRV.ONCHAIN_XPUB, 0)))
    voci = {v["chiave"]: v for g in SRV._leve_stato() for v in g["voci"]}
    prova("il pannello dice «vera» e non stampa la chiave", (True, False),
          (voci["ONCHAIN_XPUB"]["valore"].startswith("vera"),
           SRV.ONCHAIN_XPUB[:20] in json.dumps(voci)))
    SRV.ONCHAIN_XPUB = ""

    # ---- 5) la leva rispenta --------------------------------------------
    SRV.ONCHAIN_ATTIVO = False
    prova("rispenta: tutto torna 404, anche con gli indirizzi nel database",
          [404, 404, 404],
          [leggi(999).status_code, dai(999, x999).status_code,
           fai(999, 888).status_code])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
