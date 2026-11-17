# -*- coding: utf-8 -*-
"""
LE RACCOLTE IN SATS, fatte girare per davvero (17 nov 2026, cantiere
raccolta) — il giro col SERVER VERO, per HTTP (TestClient, la app vera):

  · chi apre: l'indirizzo Lightning, le vendite confermate, una alla
    volta, i tetti (euro e giorni), la bozza che solo lui e gli admin
    vedono, il via e il no di un moderatore (mai sulla propria);
  · lo zap: la fattura dal wallet di chi raccoglie col motore della
    mancia (wallet di cartone), LUD-21, la riga che sale, l'avviso una
    volta, l'anonimo, la barra che conta solo gli arrivati;
  · il deposito di garanzia: il 2-di-3 vero (embit, semi dei vettori del
    BIP-39), il minimo in euro, il wallet del rimborso che serve prima,
    il deposito visto su mempool (di cartone), la barra garantita;
  · la scadenza: raggiunta → Barattolo firma verso chi raccoglie e la
    seconda firma e' sua; mancata, fermata, arrivato tardi, incompleto
    → Barattolo firma il rimborso e la seconda firma e' di chi ha
    depositato. Mai l'altro;
  · la segnalazione, /api/me, il pannello delle leve, la leva spenta.

IL «TELEFONO» QUI E' EMBIT, come nel collaudo degli scambi P2P on-chain.
MEMPOOL E' DI CARTONE, il wallet Lightning di chi raccoglie anche (quello
del collaudo della mancia). Nessuna rete, nessun sats, nessun avviso
spedito. La chiave di Barattolo e' quella di cartone della gabbia.

USO:  python collaudo_raccolta.py
"""
import asyncio
import hashlib
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco
import collaudo_mancia as mancia

prova = banco.prova


def main():
    print("=" * 58)
    print("  LE RACCOLTE IN SATS — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    BOTTONI = []
    _notifica_del_banco = SRV.notifica

    async def notifica_coi_bottoni(chi, testo, bottone=None, *a, **k):
        BOTTONI.append((chi, testo, bottone))
        return await _notifica_del_banco(chi, testo, bottone, *a, **k)
    SRV.notifica = notifica_coi_bottoni
    ADMIN = []

    async def avvisa_admin(testo, *a, **k):
        ADMIN.append(testo)
    SRV.notifica_admin = avvisa_admin

    # il wallet Lightning di chi raccoglie: quello di cartone della mancia
    async def guardia(url):
        return url.startswith("https://") and "127.0.0.1" not in url

    async def importo(bolt11, dec=None, cassaforte=""):
        m = SRV.zap_leggi_bolt11(bolt11).get("msat")
        return None if m is None else m // 1000
    SRV.httpx = mancia.HttpxDiCartone
    SRV._url_lnurl_ammesso = guardia
    SRV.importo_invoice = importo

    from embit import bip32, bip39, script
    from embit.finalizer import finalize_psbt
    from embit.networks import NETWORKS
    from embit.psbt import PSBT
    from embit.transaction import Transaction
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    # la vetrina riconosce chi guarda solo se l'initData c'e' (senza, e'
    # la vetrina anonima): qui un segnaposto, e chi e' lo dice `come`
    c.headers.update({"X-Tg-Init-Data": "collaudo:segnaposto"})
    N = NETWORKS["signet"]
    vett = json.load(open(os.path.join(banco.QUI, "vendor",
                                       "vettori-bip.json"), encoding="utf-8"))
    semi = {222: vett["bip39_english"][0]["parole"],
            111: vett["bip39_english"][1]["parole"],
            333: vett["bip39_english"][3]["parole"],
            "wallet": vett["bip39_english"][2]["parole"]}

    def radice(tg):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=N["xprv"])

    def conto(tg):
        return radice(tg).derive("m/48h/1h/0h/2h").to_public().to_string(
            version=N["xpub"])

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

    MONETE, INVIATE = {}, []

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0

    async def invia_finta(tx_hex):
        INVIATE.append(tx_hex)
        return Transaction.from_string(tx_hex).txid().hex()

    async def scheda_vuota(indirizzo):
        return {"chain_stats": {"tx_count": 0}, "mempool_stats": {"tx_count": 0}}
    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta
    SRV.onchain_mempool_indirizzo = scheda_vuota
    SRV.onchain_mempool_invia = invia_finta

    con = SRV.db()
    for tg, nome, ln, vendite in (
            (222, "Raccoglie", "raccoglie@wallet.esempio", 3),
            (111, "Sostiene", "", 0), (333, "Terza", "", 0),
            (444, "Poche", "poche@wallet.esempio", 2),
            (555, "Senza", "", 9), (888, "Alan", "alan@wallet.esempio", 5),
            (999, "Andrea", "", 0)):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address,vendite_ok) VALUES(?,?,?,1,?,?)",
                    (tg, nome, f"neg{tg}{tg}", ln, vendite))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888]
    SRV.ONCHAIN_ATTIVO = True
    SRV.ONCHAIN_SOLO_ADMIN = False
    SRV.RACCOLTE_ATTIVE = True
    SRV.RACCOLTA_GARANTITA_ATTIVA = False
    for nome in ("raccolta_apri", "raccolta_zap", "raccolta_deposito",
                 "raccolta_segnala", "onchain_firma", "p2p_onchain_controlla",
                 "mancia_guarda"):
        SRV.FRENI[nome] = (1000, 3600)

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def apri(tg, **d):
        come(tg)
        base = {"titolo": "Il forno del paese", "giorni": 30, "euro": 500,
                "racconto": "Ricostruiamo il forno a legna della piazza: "
                            "i sats vanno in mattoni e nel tetto nuovo."}
        return c.post("/api/raccolte", json={**base, **d})

    def scheda(tg, rid):
        come(tg)
        return c.get(f"/api/raccolte/{rid}")

    def admin(tg, rid, gesto, **d):
        come(tg)
        return c.post(f"/api/admin/raccolte/{rid}/{gesto}", json=d)

    def detto_a(tg, pezzo):
        return any(pezzo in t for chi, t in banco.DETTO if chi == tg)

    def ronda():
        asyncio.run(SRV._raccolte_ronda())

    def invecchia(rid):
        """La scadenza arriva: la si porta a cinque secondi fa, e con lei
        quel che nella vita vera le sta prima (i depositi confermati prima
        della scadenza, quelli da pagare che scadono con lei)."""
        adesso = int(time.time())
        con = SRV.db()
        con.execute("UPDATE raccolte SET scade=? WHERE id=?", (adesso - 5, rid))
        con.execute("UPDATE raccolta_depositi SET depositato_il=? WHERE "
                    "raccolta_id=? AND depositato_il>0", (adesso - 10, rid))
        con.execute("UPDATE raccolta_depositi SET scade=? WHERE raccolta_id=? "
                    "AND stato='attesa'", (adesso - 5, rid))
        con.commit()
        con.close()

    def paga(dep, quanto=None, confermata=True):
        MONETE[dep["indirizzo"]["indirizzo"]] = [{
            "txid": f"{dep['id'] + 16:02x}" * 32, "vout": 0,
            "value": dep["importo_sats"] if quanto is None else quanto,
            "status": {"confirmed": confermata}}]

    def firme(tg):
        come(tg)
        return {d["id"]: d for d in c.get("/api/raccolte/mie-firme").json()["depositi"]}

    def cofirma(tg, dep):
        """Il telefono di chi riceve: firma la proposta di Barattolo col
        SUO seme e la manda finita."""
        p = PSBT.from_string(dep["proposta"]["psbt"])
        p.sign_with(radice(tg).derive(
            f"m/48h/1h/0h/2h/0/{dep['indirizzo']['mio_numero']}").key)
        come(tg)
        return c.post(f"/api/raccolte/depositi/{dep['id']}/firma",
                      json={"tx": finalize_psbt(p).serialize().hex()})

    def uscite(tx_hex):
        tx = Transaction.from_string(tx_hex)
        return sorted((o.script_pubkey.address(N), o.value) for o in tx.vout)

    # ---- 0) la leva spenta --------------------------------------------
    print("\n[la leva spenta: le raccolte non esistono]")
    SRV.RACCOLTE_ATTIVE = False
    come(222)
    prova("vetrina, apertura, admin: 404; /api/me non le dice",
          (404, 404, 404, None),
          (c.get("/api/raccolte").status_code, apri(222).status_code,
           admin(888, 1, "via").status_code,
           c.get("/api/me").json().get("raccolte")))
    SRV.RACCOLTE_ATTIVE = True

    # ---- 1) chi apre ----------------------------------------------------
    print("\n[chi apre: indirizzo Lightning, vendite, una alla volta, tetti]")
    P = SRV.raccolta_perche_non_apre
    prova("il giudice puro: leva, una alla volta, indirizzo, vendite; e il si'",
          [True, True, True, True, ""],
          ["non ci sono" in P(False, 9, "a@b", False),
           "una alla volta" in P(True, 9, "a@b", True),
           "indirizzo Lightning" in P(True, 9, "", False),
           "ne hai 2" in P(True, 2, "a@b", False),
           P(True, 3, "a@b", False)])
    r = apri(555)
    prova("senza indirizzo Lightning: 400 col perche'", (400, True),
          (r.status_code, "indirizzo Lightning" in r.json()["detail"]))
    r = apri(444)
    prova("con 2 vendite su 3: 400 col perche'", (400, True),
          (r.status_code, "almeno 3 vendite" in r.json()["detail"]))
    prova("obiettivo sopra 1.000 €, sotto 10 €, 61 giorni, 3 giorni, titolo "
          "corto, racconto corto: tutti 400", [400] * 6,
          [apri(222, euro=1001).status_code, apri(222, euro=5).status_code,
           apri(222, giorni=61).status_code, apri(222, giorni=3).status_code,
           apri(222, titolo="Ok").status_code,
           apri(222, racconto="troppo corto").status_code])
    come(222)
    io = c.get("/api/raccolte").json()["io"]
    prova("la vetrina dice a chi puo' che puo' (e la garantita no: leva spenta)",
          (True, False), (io["puo_aprire"], io["garantita_possibile"]))
    ADMIN.clear()
    r = apri(222, racconto="Ricostruiamo il forno: in cambio vi do il 10% "
                            "di interessi sul pane di tutto l'anno, promesso.")
    prova("si apre: nasce in revisione", (200, True),
          (r.status_code, r.json()["ok"]))
    R1 = r.json()["id"]
    prova("...gli admin lo sanno, con le parole da guardare e il bottone",
          (True, True), (any(f"#{R1}" in t and "interess" in t and "%" in t
                             for t in ADMIN), True))
    con = SRV.db()
    riga = con.execute("SELECT * FROM raccolte WHERE id=?", (R1,)).fetchone()
    con.close()
    prova("l'obiettivo e' fisso in sats al cambio di adesso (500 € a 100.000 "
          "€/BTC = 500.000 sats), gli euro restano scritti",
          (500_000, 50_000, 100_000.0, "revisione", 0),
          (riga["obiettivo_sats"], riga["obiettivo_cent"], riga["cambio"],
           riga["stato"], riga["scade"]))
    r = apri(222)
    prova("la seconda mentre la prima aspetta: 400, una alla volta", (400, True),
          (r.status_code, "una alla volta" in r.json()["detail"]))

    # ---- 2) il via ------------------------------------------------------
    print("\n[la bozza e il via di un moderatore]")
    come(111)
    prova("la bozza non e' in vetrina e la scheda e' 404 per gli altri",
          (0, 404), (len(c.get("/api/raccolte").json()["raccolte"]),
                     scheda(111, R1).status_code))
    prova("...chi l'ha scritta la vede, coi suoi dati", (200, "revisione", True),
          (scheda(222, R1).status_code, scheda(222, R1).json()["stato"],
           scheda(222, R1).json()["mia"]))
    prova("...e l'admin anche, con le parole sospette", True,
          "interess" in scheda(888, R1).json()["sospette"])
    prova("un non admin non da' il via: 403", 403, admin(111, R1, "via").status_code)
    r = admin(888, R1, "rifiuta", perche="no")
    prova("il no senza un perche' vero: 400", 400, r.status_code)
    r = admin(888, R1, "rifiuta", perche="Niente interessi: una raccolta non "
                                          "promette rendimenti")
    prova("il no col perche': la raccolta e' rifiutata e chi l'ha scritta lo "
          "legge", (200, "rifiutata", True),
          (r.status_code, scheda(222, R1).json()["stato"],
           detto_a(222, "Niente interessi")))
    prova("...e il perche' lo vede solo lui", (True, False),
          ("perche" in scheda(222, R1).json(), "perche" in scheda(888, R1).json()))
    r = apri(222)
    R2 = r.json()["id"]
    prova("dopo il no se ne puo' scrivere un'altra", 200, r.status_code)
    con = SRV.db()
    con.execute("UPDATE utenti SET vendite_ok=5 WHERE tg_id=999")
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888, 222]
    prova("un moderatore che e' anche chi raccoglie non decide: 403", 403,
          admin(222, R2, "via").status_code)
    SRV.ADMIN_IDS = [999, 888]
    prima = int(time.time())
    r = admin(888, R2, "via")
    s = scheda(111, R2).json()
    prova("il via: in vetrina, e la scadenza parte da adesso (30 giorni)",
          (200, "attiva", True, True),
          (r.status_code, s["stato"], 30 * 86400 - 5 <= s["scade"] - prima <= 30 * 86400 + 5,
           detto_a(222, "è in vetrina")))
    prova("un secondo via sulla stessa: 409", 409, admin(888, R2, "via").status_code)
    come(111)
    v = c.get("/api/raccolte").json()
    prova("la vetrina la mostra, senza indirizzo Lightning", (1, False),
          (len(v["raccolte"]), "raccoglie@wallet.esempio" in json.dumps(v)))
    prova("/api/me dice quante ce ne sono di vive", {"vive": 1},
          c.get("/api/me").json().get("raccolte"))

    # ---- 3) lo zap --------------------------------------------------------
    print("\n[lo zap: il motore della mancia]")
    s = scheda(111, R2).json()
    prova("chi guarda puo' mandare uno zap, ma non depositare (garantita no)",
          (True, False), (s["puo_zap"], s["puo_depositare"]))
    prova("chi raccoglie non manda zap a se stesso", False, scheda(222, R2).json()["puo_zap"])
    come(222)
    prova("...e la rotta glielo nega", 400,
          c.post(f"/api/raccolte/{R2}/zap", json={"sats": 1000}).status_code)
    come(111)
    prova("cifre fuori misura: 0 e oltre il tetto, 400", [400, 400],
          [c.post(f"/api/raccolte/{R2}/zap", json={"sats": 0}).status_code,
           c.post(f"/api/raccolte/{R2}/zap", json={"sats": 100_001}).status_code])
    mancia.WALLET["verify"] = "https://wallet.esempio/verify/{h}"
    z1 = c.post(f"/api/raccolte/{R2}/zap", json={"sats": 21000}).json()
    prova("la fattura viene dal wallet di chi raccoglie, con la cifra giusta e "
          "verificabile", (21000, True),
          (SRV.zap_leggi_bolt11(z1["invoice"])["msat"] // 1000, z1["verificabile"]))
    banco.DETTO.clear()
    e = c.post(f"/api/raccolte/{R2}/zap/{z1['id']}/esito", json={}).json()
    prova("non ancora pagata: resta chiesta, e nessun avviso", ("chiesta", False),
          (e["stato"], detto_a(222, "zap")))
    prova("una fattura solo chiesta non conta nella barra", 0,
          scheda(111, R2).json()["zap_sats"])
    h = SRV.zap_leggi_bolt11(z1["invoice"])["payment_hash"]
    mancia.WALLET["pagate"].add(h)
    e = c.post(f"/api/raccolte/{R2}/zap/{z1['id']}/esito", json={}).json()
    prova("LUD-21 dice settled: arrivata, e chi raccoglie lo sa (una volta)",
          ("arrivata", True), (e["stato"], detto_a(222, "già nel tuo wallet")))
    c.post(f"/api/raccolte/{R2}/zap/{z1['id']}/esito", json={"dichiarata": True})
    prova("...la riga non scende, e l'avviso non riparte", 1,
          sum(1 for chi, t in banco.DETTO if chi == 222 and "zap" in t))
    mancia.WALLET["verify"] = ""
    z2 = c.post(f"/api/raccolte/{R2}/zap", json={"sats": 500, "anonimo": True}).json()
    e = c.post(f"/api/raccolte/{R2}/zap/{z2['id']}/esito",
               json={"dichiarata": True}).json()
    s = scheda(333, R2).json()
    prova("lo zap «l'ho pagato» e' dichiarato: in elenco, NON nella barra",
          ("dichiarata", 21000, 1), (e["stato"], s["zap_sats"], s["sostenitori"]))
    prova("l'anonimo resta anonimo, il nome c'e' per chi l'ha voluto",
          [("", "dichiarata"), ("Sostiene", "arrivata")],
          [(z["nome"], z["stato"]) for z in s["zap"]])
    come(333)
    prova("l'esito di uno zap di un altro: 400", 400,
          c.post(f"/api/raccolte/{R2}/zap/{z1['id']}/esito", json={}).status_code)

    # ---- 4) il deposito di garanzia ---------------------------------------
    print("\n[il deposito di garanzia: il 2-di-3 del mercatino]")
    come(111)
    prova("a leva garantita spenta: 404", 404,
          c.post(f"/api/raccolte/{R2}/deposito", json={"euro": 100}).status_code)
    SRV.RACCOLTA_GARANTITA_ATTIVA = True
    prova("...accesa, ma la raccolta non e' garantita: 400", 400,
          c.post(f"/api/raccolte/{R2}/deposito", json={"euro": 100}).status_code)
    # una raccolta garantita: Alan (888) raccoglie
    r = apri(888, titolo="La biblioteca dei sats", euro=200, garantita=True)
    prova("una garantita senza la chiave on-chain: 409 col perche'", (409, True),
          (r.status_code, "wallet on-chain" in r.json()["detail"]))
    semi[888] = semi[222]
    for tg in (888, 111, 333):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    r = apri(888, titolo="La biblioteca dei sats", euro=200, garantita=True)
    prova("...con la chiave ma senza un wallet dove ricevere: 409", (409, True),
          (r.status_code, "dove ricevere" in r.json()["detail"]))
    INCASSO = dal_wallet(10)
    come(888)
    c.post("/api/onchain/incasso", json={"tipo": "indirizzo", "valore": INCASSO,
                                         "firma": firma_dest(888, "indirizzo", INCASSO)})
    r = apri(888, titolo="La biblioteca dei sats", euro=200, garantita=True)
    R3 = r.json()["id"]
    prova("...col suo wallet: la garantita nasce", 200, r.status_code)
    admin(999, R3, "via")
    s = scheda(111, R3).json()
    prova("chi guarda ora puo' zappare E depositare, col minimo di 50 €",
          (True, True, True, 50), (s["puo_zap"], s["puo_depositare"],
                                   s["garantita"], s["min_garantita_euro"]))
    come(111)
    r = c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 49})
    prova("sotto i 50 €: 400, e il consiglio dello zap", (400, True),
          (r.status_code, "zap" in r.json()["detail"]))
    r = c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 100})
    prova("senza il SUO wallet per il rimborso: 409 col perche'", (409, True),
          (r.status_code, "dove tornano i sats" in r.json()["detail"]))
    RIMB_111 = dal_wallet(20)
    c.post("/api/onchain/incasso", json={"tipo": "indirizzo", "valore": RIMB_111,
                                         "firma": firma_dest(111, "indirizzo", RIMB_111)})
    r = c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 250})
    prova("un deposito piu' grande dell'obiettivo intero: 400", 400, r.status_code)
    r = c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 120})
    D1 = r.json()
    prova("il deposito nasce: 120 € = 120.000 sats, piu' il margine, verso il "
          "wallet di chi raccoglie, il rimborso al mio",
          (200, "attesa", 120_000, True, INCASSO, RIMB_111, "compratore"),
          (r.status_code, D1["stato"], D1["prezzo_sats"],
           D1["importo_sats"] == 120_000 + D1["margine_sats"] and D1["margine_sats"] >= 500,
           D1["incasso"], D1["rimborso"], D1["ruolo"]))
    prova("...il 2-di-3 ha le tre chiavi e la rotta per il telefono",
          (True, f"/raccolte/depositi/{D1['id']}"),
          (set(D1["indirizzo"]["chiavi"]) == {"compratore", "venditore", "barattolo"},
           D1["rotta"]))
    prova("un secondo tocco ridà lo stesso deposito da pagare", D1["id"],
          c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 60}).json()["id"])
    come(888)
    prova("chi raccoglie non deposita nella sua", 400,
          c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 60}).status_code)
    paga(D1, confermata=False)
    ronda()
    prova("visto in mempool ma non confermato: non conta", ("attesa", 0),
          (firme(111)[D1["id"]]["stato"], scheda(111, R3).json()["garantiti_sats"]))
    paga(D1)
    banco.DETTO.clear()
    ronda()
    s = scheda(333, R3).json()
    prova("confermato: depositato, la barra garantita sale, i due lo sanno",
          ("depositato", 120_000, 1, True, True),
          (firme(111)[D1["id"]]["stato"], s["garantiti_sats"], s["depositi_n"],
           detto_a(111, "Deposito confermato"), detto_a(888, "Nuovo deposito")))
    come(111)
    prova("chi ha depositato non lo annulla piu'", 409,
          c.post(f"/api/raccolte/depositi/{D1['id']}/annulla").status_code)
    # Terza (333) deposita 90 €: l'obiettivo di 200 € arriva a 210
    RIMB_333 = dal_wallet(30)
    come(333)
    c.post("/api/onchain/incasso", json={"tipo": "indirizzo", "valore": RIMB_333,
                                         "firma": firma_dest(333, "indirizzo", RIMB_333)})
    D2 = c.post(f"/api/raccolte/{R3}/deposito", json={"euro": 90}).json()
    paga(D2)
    ronda()
    prova("con due depositi confermati la barra garantita e' 210.000",
          210_000, scheda(111, R3).json()["garantiti_sats"])

    # ---- 5) la scadenza: raggiunta ----------------------------------------
    print("\n[la scadenza: raggiunta → a chi raccoglie, la seconda firma e' sua]")
    prova("il giudice puro dell'esito: garantita = solo depositi; semplice = "
          "zap e depositi", ["mancata", "raggiunta", "raggiunta", "mancata"],
          [SRV.raccolta_esito(True, 100, 50, 999), SRV.raccolta_esito(True, 100, 100, 0),
           SRV.raccolta_esito(False, 100, 0, 100), SRV.raccolta_esito(False, 100, 0, 99)])
    V = SRV.raccolta_verso_deposito
    prova("il giudice puro del verso", ["venditore", "compratore", "compratore",
                                        "compratore", "", ""],
          [V("depositato", "chiusa", "raggiunta", 10, 20),
           V("depositato", "chiusa", "raggiunta", 30, 20),
           V("depositato", "chiusa", "mancata", 10, 20),
           V("depositato", "fermata", "mancata", 10, 20),
           V("depositato", "attiva", "", 10, 0),
           V("attesa", "chiusa", "raggiunta", 0, 20)])
    invecchia(R3)
    banco.DETTO.clear()
    ADMIN.clear()
    ronda()
    s = scheda(111, R3).json()
    f888 = firme(888)
    prova("chiusa e raggiunta; Barattolo ha firmato tutt'e due verso chi "
          "raccoglie, e lo dice a lui e agli admin",
          ("chiusa", "raggiunta", "venditore", "venditore", True, True),
          (s["stato"], s["esito"], f888[D1["id"]]["proposta"]["verso"],
           f888[D2["id"]]["proposta"]["verso"], detto_a(888, "Barattolo ha firmato"),
           any("2 uscite" in t for t in ADMIN)))
    prova("niente zap ne' depositi su una raccolta chiusa", (False, False),
          (s["puo_zap"], s["puo_depositare"]))
    r = cofirma(111, firme(111)[D1["id"]])
    prova("chi ha depositato NON mette la seconda firma sul rilascio: 409",
          409, r.status_code)
    r = cofirma(888, f888[D1["id"]])
    prova("chi raccoglie co-firma: rilasciato e trasmesso", (200, "rilasciato"),
          (r.status_code, r.json().get("stato")))
    u = uscite(INVIATE[-1])
    prova("...al suo wallet ESATTAMENTE il contributo, il resto del margine al "
          "wallet di chi ha depositato", (True, True),
          ((INCASSO, 120_000) in u, all(a in (INCASSO, RIMB_111) for a, _ in u)))
    prova("...e chi ha depositato lo sa", True, detto_a(111, "è arrivato a chi raccoglie"))
    prova("la barra garantita conta anche quel che e' gia' uscito", 210_000,
          scheda(111, R3).json()["garantiti_sats"])
    r = cofirma(888, f888[D1["id"]])
    prova("una seconda volta: niente da co-firmare (409)", 409, r.status_code)
    r = cofirma(888, f888[D2["id"]])
    prova("...e l'altro deposito", (200, "rilasciato"),
          (r.status_code, r.json().get("stato")))

    # ---- 6) mancata, arrivato tardi, incompleto, fermata ------------------
    print("\n[mancata e fermata: tutto torna a chi ha depositato]")
    r = apri(888, titolo="Le panchine del parco", euro=300, garantita=True)
    R4 = r.json()["id"]
    admin(999, R4, "via")
    come(111)
    D3 = c.post(f"/api/raccolte/{R4}/deposito", json={"euro": 100}).json()
    paga(D3)
    come(333)
    D4 = c.post(f"/api/raccolte/{R4}/deposito", json={"euro": 60}).json()
    paga(D4, quanto=D4["importo_sats"] - 10_000)
    ronda()
    prova("pagato meno dell'importo: resta in attesa finche' c'e' tempo",
          "attesa", firme(333)[D4["id"]]["stato"])
    invecchia(R4)
    con = SRV.db()
    con.execute("UPDATE raccolta_depositi SET scade=? WHERE id=?",
                (int(time.time()) - 5, D4["id"]))
    con.commit()
    con.close()
    banco.DETTO.clear()
    ronda()
    s = scheda(111, R4).json()
    f111, f333 = firme(111), firme(333)
    prova("100 € su 300: mancata; il deposito torna a chi l'ha messo, e "
          "l'incompleto anche", ("chiusa", "mancata", "compratore", "incompleto",
                                 "compratore", True),
          (s["stato"], s["esito"], f111[D3["id"]]["proposta"]["verso"],
           f333[D4["id"]]["stato"], f333[D4["id"]]["proposta"]["verso"],
           detto_a(111, "torna a te")))
    prova("l'incompleto non contava nella barra", 100_000, s["garantiti_sats"])
    r = cofirma(888, firme(888)[D3["id"]])
    prova("chi raccoglie NON co-firma il rimborso: 409", 409, r.status_code)
    r = cofirma(111, f111[D3["id"]])
    prova("chi ha depositato co-firma: rimborsato", (200, "rimborsato"),
          (r.status_code, r.json().get("stato")))
    u = uscite(INVIATE[-1])
    prova("...tutto al SUO wallet, meno la rete (dentro il margine)", (True, True),
          (all(a == RIMB_111 for a, _ in u),
           0 < D3["importo_sats"] - sum(v for _, v in u) <= D3["margine_sats"]))
    r = cofirma(333, f333[D4["id"]])
    prova("...e l'incompleto torna anche lui", (200, "rimborsato"),
          (r.status_code, r.json().get("stato")))
    print("\n[la raccolta fermata da un moderatore]")
    r = apri(888, titolo="Il campetto di calcio", euro=100, garantita=True)
    R5 = r.json()["id"]
    admin(999, R5, "via")
    come(111)
    D5 = c.post(f"/api/raccolte/{R5}/deposito", json={"euro": 100}).json()
    paga(D5)
    ronda()
    prova("un deposito pari all'obiettivo, raccolta ancora viva: nessuna firma",
          None, firme(111)[D5["id"]]["proposta"])
    r = admin(999, R5, "ferma", perche="Segnalata: non è chi dice di essere")
    banco.DETTO.clear()
    ronda()
    prova("fermata: anche se l'obiettivo c'era, tutto torna indietro",
          (200, "fermata", "compratore"),
          (r.status_code, scheda(111, R5).json()["stato"],
           firme(111)[D5["id"]]["proposta"]["verso"]))
    prova("...e chi raccoglie legge il perche'", True,
          scheda(888, R5).json().get("perche", "").startswith("Segnalata"))
    print("\n[il deposito arrivato dopo la scadenza]")
    r = apri(888, titolo="Le luci di Natale", euro=60, garantita=True)
    R6 = r.json()["id"]
    admin(999, R6, "via")
    come(111)
    D6 = c.post(f"/api/raccolte/{R6}/deposito", json={"euro": 60}).json()
    invecchia(R6)
    ronda()
    prova("scaduta senza depositi: mancata, e il deposito non pagato e' "
          "scaduto con lei", ("mancata", "scaduto"),
          (scheda(111, R6).json()["esito"],
           SRV.db().execute("SELECT stato FROM raccolta_depositi WHERE id=?",
                            (D6["id"],)).fetchone()[0]))
    D6 = c.post(f"/api/raccolte/depositi/{D6['id']}/controlla").json()
    paga(D6)
    banco.DETTO.clear()
    ronda()
    f = firme(111)[D6["id"]]
    prova("pagato DOPO: la ronda lo rilegge, non conta, e torna indietro con "
          "la firma di Barattolo", ("incompleto", "compratore", True, 0),
          (f["stato"], f["proposta"]["verso"], detto_a(111, "già scaduto"),
           scheda(111, R6).json()["garantiti_sats"]))
    r = cofirma(111, f)
    prova("...e chi l'ha mandato lo riprende", (200, "rimborsato"),
          (r.status_code, r.json().get("stato")))

    # ---- 7) la segnalazione e il pannello --------------------------------
    print("\n[la segnalazione, il pannello degli admin, le leve]")
    ADMIN.clear()
    come(111)
    r1 = c.post(f"/api/raccolte/{R2}/segnala", json={"motivo": "Sembra una truffa"})
    come(333)
    r2 = c.post(f"/api/raccolte/{R2}/segnala", json={"motivo": "Anche per me"})
    come(222)
    r3 = c.post(f"/api/raccolte/{R2}/segnala", json={})
    prova("due segnalazioni: la prima suona agli admin, la seconda no; chi "
          "raccoglie non segnala la sua", (200, 200, 400, 1),
          (r1.status_code, r2.status_code, r3.status_code,
           sum(1 for t in ADMIN if "segnalata" in t.lower())))
    come(888)
    pan = {x["id"]: x for x in c.get("/api/admin/raccolte").json()["raccolte"]}
    prova("il pannello: la raccolta viva con le sue 2 segnalazioni", (2, 3),
          (pan[R2]["segnalazioni"]["n"], pan[R2]["vendite_ok"]))
    come(111)
    prova("a un non admin il pannello e' 403", 403,
          c.get("/api/admin/raccolte").status_code)
    gruppi = SRV._leve_stato()
    voci = [v["chiave"] for g in gruppi if g["gruppo"].startswith("🎯")
            for v in g["voci"]]
    prova("il pannello delle leve ha il gruppo «🎯 Raccolte in sats»",
          ["RACCOLTE_ATTIVE", "RACCOLTA_GARANTITA_ATTIVA", "RACCOLTA_MAX_EURO",
           "RACCOLTA_GIORNI_MAX", "RACCOLTA_MIN_GARANTITA_EURO",
           "RACCOLTA_VENDITE_MIN", "RACCOLTA_ZAP_MAX_SATS"], voci)
    prova("i bottoni degli avvisi portano alla raccolta", True,
          any(b and b[1].endswith(f"/?raccolta={R3}") for _, _, b in BOTTONI))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    sys.exit(1 if banco.FALLITE else 0)


if __name__ == "__main__":
    main()
