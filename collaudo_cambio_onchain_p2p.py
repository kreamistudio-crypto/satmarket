# -*- coding: utf-8 -*-
"""
CHI COMPRA BITCOIN SU UNO SCAMBIO P2P ON-CHAIN RICEVE IN LIGHTNING (1 nov
2026, cantiere presa-altra-rete, tappa 2; Andrea: «Subito la tappa 2») —
il giro col SERVER VERO per HTTP (TestClient, la app vera), il SATS ROUTING
DI CARTONE acceso su una porta di questo computer (rete testnet: le forme
tb1…/lntb… del signet dell'on-chain), e il TELEFONO VERO (i pezzi della
pagina e swap/*.js coi due bundle) in node.

LE SCENE:
  - il cancello: a leva spenta niente; accesa ma con l'on-chain e il
    fornitore su reti diverse niente lo stesso; con le reti giuste si apre;
  - chi compra sceglie «⚡ Lightning»: l'incasso del Profilo si svuota, il
    preventivo dice quanto arriva, il cambio aspetta la conferma;
  - chi vende non libera verso un incasso che non c'e': conferma gli euro
    FIRMANDO col suo seme dal telefono, e i no del server;
  - il cambio nasce DAL TELEFONO di chi compra (verifica, firma della
    destinazione, prima firma) e i no del server;
  - la seconda firma DAL TELEFONO di chi vende, coi suoi no; il fornitore
    che tace (503) e quello vivo (rilasciato, il prezzo al cambio);
  - il cambio morto prima della seconda firma: non parte niente, si toglie;
  - la disputa porta via il cambio, e chi compra riceve on-chain;
  - chi compra torna all'on-chain dopo la conferma: il telefono di chi
    vende firma da solo il rilascio confermato;
  - la leva rispenta: il cambio sparisce, la via d'uscita resta.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco PRIMA dell'import del server; mempool di cartone; nessuna rete
fuori da 127.0.0.1; nessun sats.

USO:  python collaudo_cambio_onchain_p2p.py
"""
import copy
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time

import collaudo_lnbits_muto as banco
import cartone_satsrouting
import collaudo_onchain_verso_lightning as V
import schnorr_puro

prova = banco.prova


def pezzi_pagina():
    """I pezzi del mercatino (quelli del collaudo del 28 ott) piu' quelli
    dello scambio P2P on-chain e del suo cambio."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"),
                encoding="utf-8").read().replace("\r\n", "\n")

    def f(firma):
        i = mini.index(firma)
        return mini[i:mini.index("\n}\n", i) + 3]

    def riga(inizio):
        i = mini.index(inizio)
        return mini[i:mini.index("\n", i) + 1]
    firme = ["function onchainParolePerOrdine(B, parole, o){",
             "async function onchainFirmaProposta(oid, verso){",
             "function daFirmareOnchainP2P(o){",
             "function cambioDaFirmareOnchainP2P(o){",
             "function rilascioDaFirmareOnchainP2P(o){",
             "function incassoLnOnchainP2P(o){",
             "function ridisegnaLnOnchainP2P(id){",
             "async function leggiPreventivoOnchainP2P(id){",
             "async function caricaCambioOnchainP2P(id){",
             "async function confermaCambioOnchainP2P(btn, id){",
             "async function p2pOnchainCofirmeInAttesa(parole){"]
    return "\n".join([V.pezzi_pagina(), riga("const p2pOcCambi = {};")]
                     + [f(x) for x in firme])


BANCO_TELEFONO = V.BANCO_TELEFONO.replace(
    # il server finto risponde col preventivo vero dove serve
    """  if (String(url).startsWith('/api/')) {
    alServer.push([String(url), JSON.parse((o && o.body) || '{}')]);""",
    """  if (String(url).endsWith('/cambio/preventivo'))
    return {ok: true, status: 200, json: async () => (${JSON.stringify(D.preventivo || null)})};
  if (String(url).startsWith('/api/')) {
    alServer.push([String(url), JSON.parse((o && o.body) || '{}')]);""").replace(
    "for (const f of D.telefono) vm.runInContext(fs.readFileSync(f, 'utf8'), ctx);",
    """vm.runInContext(`
let p2pOnchainMiei = [], myP2POnchain = true;
async function leggiMieiOnchainP2P(){ return p2pOnchainMiei; }
function renderP2POnchain(){}
function t3(){ return {nienteCasa: 'niente casa'}; }
`, ctx);
for (const f of D.telefono) vm.runInContext(fs.readFileSync(f, 'utf8'), ctx);""").replace(
    "  if (D.fase === 'ricevuto') {",
    """  if (D.fase === 'p2p-conferma') {
    out.firma = await run(`onchainFirmaRicevuto(B0, PAROLE, ${JSON.stringify(D.oc)})`);
  } else if (D.fase === 'p2p-cambio') {
    const o = D.oc;
    run(`p2pOnchainMiei = [${JSON.stringify(o)}]`);
    /* il riquadro prima del preventivo, poi col preventivo */
    out.prima = run(`incassoLnOnchainP2P(p2pOnchainMiei[0])`);
    for (let i = 0; i < 50 && run(`(p2pOcCambi[${o.id}] || {}).stato`) !== 'pronto'; i++)
      await new Promise(r => setTimeout(r, 20));
    out.riquadro = run(`incassoLnOnchainP2P(p2pOnchainMiei[0])`);
    out.attesa = run(`incassoLnOnchainP2P(Object.assign({}, p2pOnchainMiei[0], {rilascio_chiesto_il: 0}))`);
    /* la richiesta che vive un'ora: no, e nessun cambio chiesto */
    const v0 = (await (await fetchVero(D.base + '/cartone/visto')).json()).swap;
    run(`elementi['p2pOcFattura_${o.id}'] = {value: ${JSON.stringify(D.corta)}}`);
    await run(`confermaCambioOnchainP2P(null, ${o.id})`);
    out.corta = {errore: run(`p2pOcCambi[${o.id}].errore || ''`),
                 swap: (await (await fetchVero(D.base + '/cartone/visto')).json()).swap - v0,
                 server: run('alServer.length')};
    run(`elementi['p2pOcFattura_${o.id}'] = {value: ${JSON.stringify(D.buona)}}`);
    await run(`confermaCambioOnchainP2P(null, ${o.id})`);
    out.errore = run(`(p2pOcCambi[${o.id}] || {}).errore || ''`);
    out.nato = run('alServer.slice()');
    const lista = JSON.parse(memoria.get('barattolo_swap_lista_' + D.tg) || '[]');
    const rec = lista.find(r => r.p2pOnchain === o.id) || {};
    out.rec = {tipo: rec.tipo, ordine: rec.ordine, onchain: rec.onchain, p2pOnchain: rec.p2pOnchain,
               ricevi: rec.ricevi, mandi: rec.mandi, lockup: rec.lockupAddress, seme: rec.seme,
               indirizzo: rec.indirizzo,
               incasso: run(`onchainMieChiavi(B0, PAROLE, ${JSON.stringify(o)}).incasso`),
               frase: rec.id ? run(`frasestatoSwap(swapLista().find(r => r.p2pOnchain === ${o.id}))`) : ''};
    out.avvisi = run('avvisi.slice()');
  } else if (D.fase === 'p2p-cofirma') {
    const oc = D.oc;
    out.daFirmare = run(`daFirmareOnchainP2P(${JSON.stringify(oc)})`);
    out.storta = await run(`onchainCofirma(${JSON.stringify(D.storta)}, PAROLE)`);
    out.altraConferma = await run(`onchainCofirma(${JSON.stringify(Object.assign({}, oc, {rilascio_firma: D.altraFirma}))}, PAROLE)`);
    out.prima = run('alServer.length');
    out.no = await run(`onchainCofirma(${JSON.stringify(oc)}, PAROLE)`);
    out.mandato = run('alServer.slice()');
  } else if (D.fase === 'p2p-riprendi') {
    run(`p2pOnchainMiei = ${JSON.stringify(D.miei)}`);
    out.giudice = run(`p2pOnchainMiei.map(rilascioDaFirmareOnchainP2P)`);
    out.fatte = await run(`p2pOnchainCofirmeInAttesa(PAROLE)`);
    out.mandato = run('alServer.slice()');
  } else if (D.fase === 'ricevuto') {""")


def telefono(fase, **dati):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="cambio_oc_p2p_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        base = f"http://127.0.0.1:{V.PORTA}"
        open(d, "w", encoding="utf-8").write(json.dumps(dict({
            "fase": fase, "base": base,
            "btc": os.path.join(banco.QUI, "vendor", "btc.bundle.js"),
            "swap": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "testnet",
                     "referral": "barattolo", "mempool": base + "/esplora",
                     "fornitori": [{"id": "satsrouting", "nome": "SATS Routing",
                                    "tipo": "boltz", "api": base,
                                    "referral": "barattolo", "rete": "testnet",
                                    "mempool": base + "/esplora"}]}}, **dati)))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1500:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    print("=" * 58)
    print("  ⚡ P2P ON-CHAIN: CHI COMPRA RICEVE IN LIGHTNING — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import httpx
    from embit import bip32, bip39, script
    from embit.ec import PublicKey
    from embit.finalizer import finalize_psbt
    from embit.networks import NETWORKS
    from embit.psbt import PSBT
    from embit.transaction import (Transaction, TransactionInput,
                                   TransactionOutput)
    from fastapi.testclient import TestClient
    SRV.httpx = httpx           # il cartone e' vero, su 127.0.0.1
    _, V.PORTA = cartone_satsrouting.avvia(0, rete="testnet")
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

    def chiave2(tg):
        return radice(tg).derive("m/48h/1h/0h/2h/2/0").key

    def firma_dest(tg, tipo, valore):
        return V.firma_compatta(chiave2(tg),
                                SRV.onchain_messaggio_destinazione(tipo, valore))

    def firma_ricevuto(tg, o):
        return V.firma_compatta(chiave2(tg), SRV.onchain_messaggio_ricevuto(
            o["id"], o["indirizzo"]["indirizzo"]))

    fisso = script.p2wpkh(radice("wallet").derive(
        "m/84h/1h/0h/0/3").key.get_public_key()).address(N)

    MONETE, TRASMESSE = {}, []

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0

    async def invia_finta(tx_hex):
        TRASMESSE.append(tx_hex)
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
    for tg, nome in ((999, "Andrea"), (888, "Alan")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888]
    SRV.ONCHAIN_ATTIVO = True
    SRV.P2P_ATTIVO = True
    SRV.P2P_ONCHAIN_ATTIVO = True
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.P2P_PROVA_IDS = []
    SRV.P2P_MAX_EURO = 250
    SRV.SWAP_ATTIVO = True
    SRV.SWAP_SOLO_MODERATORI = True
    SRV.SWAP_MIN_SATS = 25_000
    SRV.SWAP_API_BASE = f"http://127.0.0.1:{V.PORTA}"
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.CAMBIO_BTC_LN_ATTIVO = True
    SRV.SWAP_RETE = "bitcoin"
    SRV.P2P_ALTRA_RETE_ATTIVO = False
    SRV.P2P_ALTRA_RETE_SOLO_MODERATORI = True
    for nome in ("p2p_onchain_pubblica", "p2p_onchain_prendi", "onchain_firma",
                 "onchain_controlla", "p2p_onchain_controlla", "onchain_cambio",
                 "onchain_incasso", "p2p_onchain_disputa", "ln_address"):
        SRV.FRENI[nome] = (1000, 3600)
    sk_noi = os.urandom(32)
    while not 1 <= int.from_bytes(sk_noi, "big") < schnorr_puro.N:
        sk_noi = os.urandom(32)
    if SRV.ChiavePrivataNostr is not None:
        SRV._NOSTR = (SRV.ChiavePrivataNostr(sk_noi), schnorr_puro.pubblica(sk_noi).hex())

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def uno(tg, oid):
        come(tg)
        return c.get(f"/api/p2p/onchain/{oid}").json()

    def gesto(tg, oid, cosa, **d):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/{cosa}", json=d)

    def preventivo(tg, oid):
        come(tg)
        return c.get(f"/api/p2p/onchain/{oid}/cambio/preventivo")

    def detto_a(tg, pezzo):
        return any(pezzo in t for chi, t in banco.DETTO if chi == tg)

    def scambio(lightning=True, depositato=True):
        """Andrea vende 100.000 sats, Alan li prende (e sceglie il Lightning)"""
        come(999)
        o = c.post("/api/p2p/onchain/pubblica", json={
            "lato": "sell", "sats": 100000, "euro_cent": 9000,
            "metodi": ["Bonifico"], "recapito": "IT00 X 1234"}).json()
        gesto(888, o["id"], "prendi")
        if lightning:
            gesto(888, o["id"], "ricevi-lightning", si=True)
        if depositato:
            oa = uno(999, o["id"])
            MONETE[oa["indirizzo"]["indirizzo"]] = [{
                "txid": secrets.token_hex(32), "vout": 0,
                "value": oa["importo_sats"], "status": {"confirmed": True}}]
            gesto(999, o["id"], "controlla")
        return o["id"]

    def psbt_di(o, uscite, chi):
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
        p.sign_with(radice(chi).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        return p

    def uscite_cambio(o, lockup):
        vb = 11 + 105 * len(o["utxo"]) + 31 * 2 + 12
        resto = o["importo_sats"] - o["prezzo_sats"] - vb * 2
        return [(lockup, o["prezzo_sats"]), (o["rimborso"], resto)]

    def cambio_dal_banco(o, sats_fattura):
        """il telefono di chi compra fatto dal banco (embit + HTTP verso il
        cartone): per le scene dove il telefono vero l'ha gia' provato"""
        f = V.fattura(sats_fattura)
        tariffe = V.cartone("/v2/swap/submarine")
        chiave = radice(888).derive("m/44h/0h/0h/0/7").key.get_public_key()
        r = V.cartone("/v2/swap/submarine", {
            "from": "BTC", "to": "BTC", "invoice": f["invoice"],
            "refundPublicKey": chiave.sec().hex(),
            "pairHash": tariffe["BTC"]["BTC"]["hash"]})
        return {"cambio": {"fornitore": "satsrouting", "id": r["id"],
                           "lockup": r["address"], "ricevi": sats_fattura,
                           "mandi": r["expectedAmount"],
                           "scade_fattura": int(time.time()) + 86400,
                           "timeout": r["timeoutBlockHeight"]},
                "firma": firma_dest(888, "cambio", f"p2p:{o['id']}:{r['address']}"),
                "psbt": psbt_di(o, uscite_cambio(o, r["address"]), 888).to_string()}

    def nasce(oid, corpo, tg=888):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/cambio", json=corpo)

    def seconda_del_banco(oid, tg=999):
        o = uno(tg, oid)
        p = PSBT.from_string(o["proposta"]["psbt"])
        p.sign_with(radice(tg).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        return gesto(tg, oid, "firma", tx=finalize_psbt(p).serialize().hex())

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    come(888)
    r = c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": fisso,
        "firma": firma_dest(888, "indirizzo", fisso)})
    prova("chi compra ha un wallet on-chain suo nel Profilo", 200, r.status_code)

    # ---- 1) il cancello ----------------------------------------------------
    print("\n[il cancello: la leva, la strada bitcoin → Lightning, le reti]")
    oid1 = scambio(lightning=False, depositato=False)
    o1 = uno(888, oid1)
    prova("preso: l'incasso e' il wallet del Profilo, e il Lightning non c'e'",
          ("preso", fisso, False, False),
          (o1["stato"], o1["incasso"], o1["incasso_ln"], o1["ln_possibile"]))
    r = gesto(888, oid1, "ricevi-lightning", si=True)
    prova("a leva spenta «Ricevi in Lightning» e' 403, il preventivo 404",
          (403, 404), (r.status_code, preventivo(888, oid1).status_code))
    SRV.P2P_ALTRA_RETE_ATTIVO = True
    prova("leva accesa, ma l'on-chain sta su signet e il fornitore su bitcoin: "
          "chiusa lo stesso", (False, 403),
          (uno(888, oid1)["ln_possibile"],
           gesto(888, oid1, "ricevi-lightning", si=True).status_code))
    SRV.SWAP_RETE = "testnet"
    SRV.CAMBIO_BTC_LN_ATTIVO = False
    prova("reti giuste ma la strada bitcoin → Lightning spenta: chiusa", False,
          uno(888, oid1)["ln_possibile"])
    SRV.CAMBIO_BTC_LN_ATTIVO = True
    prova("con tutto acceso si apre, ma solo per chi compra", (True, False),
          (uno(888, oid1)["ln_possibile"], uno(999, oid1)["ln_possibile"]))

    # ---- 2) la scelta di chi compra ---------------------------------------
    print("\n[chi compra sceglie il Lightning]")
    prova("chi vende non sceglie al posto di chi compra: 403", 403,
          gesto(999, oid1, "ricevi-lightning", si=True).status_code)
    r = gesto(888, oid1, "ricevi-lightning", si=True)
    prova("«⚡ Ricevi in Lightning»: 200, l'incasso del Profilo si svuota",
          (200, True, "", None),
          (r.status_code, r.json()["incasso_ln"], r.json()["incasso"],
           r.json()["destinazione"]))
    p = preventivo(888, oid1).json()
    prova("il preventivo si vede gia' alla presa: 99.186 in Lightning, costo "
          "814, ma non e' ancora confermato",
          (True, 100_000, 99_186, 814, False, 82_800),
          (p.get("ok"), p.get("prezzo"), p.get("ricevi"), p.get("costo"),
           p.get("confermato"), p.get("vita_incollata_s")))
    prova("chi vende non lo chiede: 403", 403, preventivo(999, oid1).status_code)
    prova("la richiesta dal Lightning address prima della conferma: 409", 409,
          gesto(888, oid1, "cambio/fattura", sats=99_186).status_code)
    oa = uno(999, oid1)
    MONETE[oa["indirizzo"]["indirizzo"]] = [{
        "txid": secrets.token_hex(32), "vout": 0,
        "value": oa["importo_sats"], "status": {"confirmed": True}}]
    gesto(999, oid1, "controlla")
    prova("depositato, e l'incasso resta vuoto (il Profilo non lo riempie)",
          ("depositato", ""), (uno(888, oid1)["stato"], uno(888, oid1)["incasso"]))
    gesto(888, oid1, "euro-inviati")

    # ---- 3) chi vende conferma gli euro col seme ---------------------------
    print("\n[chi vende conferma gli euro, firmando col suo seme]")
    oa = uno(999, oid1)
    finta = psbt_di(oa, [(oa["rimborso"], oa["importo_sats"] - 600)], 999).to_string()
    r = gesto(999, oid1, "proposta", verso="venditore", psbt=finta)
    prova("«Libera i sats» senza un incasso: 409 col perche'", (409, True),
          (r.status_code, "conferma che hai ricevuto gli euro" in r.json()["detail"]))
    t = telefono("p2p-conferma", tg=999, parole=semi[999], oc=oa)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    prova("chi compra non conferma al posto di chi vende: 403", 403,
          gesto(888, oid1, "euro-ricevuti", firma=t["firma"]).status_code)
    prova("una conferma firmata da un ALTRO seme: 400", 400,
          gesto(999, oid1, "euro-ricevuti", firma=firma_ricevuto(888, oa)).status_code)
    banco.DETTO.clear()
    prova("quella del telefono di chi vende: 200", 200,
          gesto(999, oid1, "euro-ricevuti", firma=t["firma"]).status_code)
    o1 = uno(888, oid1)
    prova("...resta scritta, e chi compra lo sa: tocca a lui il cambio",
          (True, t["firma"], True, True),
          (bool(o1["rilascio_chiesto_il"]), o1["rilascio_firma"],
           detto_a(888, "Chi vende ha ricevuto gli euro"),
           preventivo(888, oid1).json().get("confermato")))

    # ---- 4) il cambio nasce dal telefono di chi compra ---------------------
    print("\n[il cambio nasce dal telefono di chi compra]")
    p = preventivo(888, oid1).json()
    buona = V.fattura(99_186)["invoice"]
    corta = V.fattura(99_186, vita=3600)["invoice"]
    t = telefono("p2p-cambio", tg=888, parole=semi[888], oc=o1, preventivo=p,
                 buona=buona, corta=corta)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    rq = t.get("riquadro", "")
    prova("il riquadro: prima il preventivo che arriva, poi il cambio col suo "
          "costo, la capienza, la richiesta da incollare, la via d'uscita",
          (True, True, True, True, True, True),
          ("Chiedo il prezzo del cambio" in t.get("prima", ""),
           "È un cambio, fatto da SATS Routing</b>: costa 814 sats" in rq,
           "Ricevi circa <b>99186 sats in Lightning</b> invece di 100000 on-chain" in rq,
           "deve poter ricevere 99186 sats in una volta" in rq,
           "✅ Conferma il cambio" in rq, "₿ Ricevi on-chain invece" in rq))
    prova("...e prima della conferma di chi vende niente richiesta da incollare",
          (True, False), ("Quando chi vende conferma gli euro" in t.get("attesa", ""),
                          "p2pOcFattura_" in t.get("attesa", "")))
    prova("una richiesta che vive un'ora: no, e non si chiede niente a nessuno",
          ("Questa richiesta scade fra meno di 23 ore: creane una che duri di più.", 0, 0),
          (t["corta"]["errore"], t["corta"]["swap"], t["corta"]["server"]))
    mandati = t.get("nato") or []
    url, corpo = mandati[-1] if mandati else ("", {})
    prova("con quella buona il cambio nasce, e al server va UNA chiamata con le "
          "sole parti pubbliche, la firma e la prima firma",
          (1, f"/api/p2p/onchain/{oid1}/cambio", ["cambio", "firma", "psbt"], ""),
          (len(mandati), url, sorted(corpo), t["errore"]))
    rec = t["rec"]
    prova("...il cambio entra nella lista del telefono, legato allo scambio, "
          "senza ordine del mercatino",
          ("sub", None, oid1, oid1, 99_186, 100_000, True),
          (rec["tipo"], rec["ordine"], rec["onchain"], rec["p2pOnchain"], rec["ricevi"],
           rec["mandi"], str(rec["lockup"]).startswith("tb1p")))
    prova("...la chiave di riserva e' dello STESSO seme, e il rimborso va al /1/n "
          "di chi compra", ("onchain", True),
          (rec["seme"], bool(rec["incasso"]) and rec["indirizzo"] == rec["incasso"]))
    prova("...e dice che i bitcoin partono alla seconda firma di CHI VENDE",
          "I bitcoin partono dal deposito di garanzia appena chi vende mette la "
          "seconda firma: poi SATS Routing paga la tua richiesta Lightning.",
          rec["frase"])

    print("\n[i no del server sul cambio]")
    altro = copy.deepcopy(corpo)
    altro["firma"] = firma_dest(888, "cambio", f"{oid1}:{corpo['cambio']['lockup']}")
    r = nasce(oid1, altro)
    prova("la firma senza il prefisso «p2p:» (quella di un ordine del mercatino): 400",
          (400, True), (r.status_code, "non è firmato dal tuo seme" in r.json()["detail"]))
    altro = copy.deepcopy(corpo)
    altro["firma"] = firma_dest(999, "cambio", f"p2p:{oid1}:{corpo['cambio']['lockup']}")
    prova("la destinazione firmata da un ALTRO seme: 400", 400,
          nasce(oid1, altro).status_code)
    altro = copy.deepcopy(corpo)
    altro["cambio"]["lockup"] = fisso
    r = nasce(oid1, altro)
    prova("un indirizzo che non e' un taproot: 400", (400, True),
          (r.status_code, "rete giusta" in r.json()["detail"]))
    altro = copy.deepcopy(corpo)
    altro["cambio"]["mandi"] = 100_001
    prova("cifre che superano il prezzo: 400", 400, nasce(oid1, altro).status_code)
    SRV.P2P_ALTRA_RETE_MAX_SATS = 50_000
    prova("sopra il massimo della leva: 400, e il preventivo lo dice",
          (400, False, "sopra_tetto"),
          (nasce(oid1, corpo).status_code, preventivo(888, oid1).json().get("ok"),
           preventivo(888, oid1).json().get("motivo")))
    SRV.P2P_ALTRA_RETE_MAX_SATS = 500_000
    o1v = uno(888, oid1)
    altro = copy.deepcopy(corpo)
    altro["psbt"] = psbt_di(o1v, [(corpo["cambio"]["lockup"], 99_000),
                                  (o1v["rimborso"], o1v["importo_sats"] - 99_400)],
                            888).to_string()
    prova("una prima firma che al cambio manda meno del prezzo: 400", 400,
          nasce(oid1, altro).status_code)
    prova("chi vende non fa il cambio di chi compra: 403", 403,
          nasce(oid1, corpo, tg=999).status_code)
    banco.DETTO.clear()
    prova("quello del telefono, intero: 200", 200, nasce(oid1, corpo).status_code)
    prova("...e una seconda volta no: 409", 409, nasce(oid1, corpo).status_code)
    prova("chi vende non propone al posto del cambio: 409", (409, True),
          (gesto(999, oid1, "proposta", verso="venditore", psbt=finta).status_code,
           "già firmato il cambio" in gesto(999, oid1, "proposta", verso="venditore",
                                            psbt=finta).json()["detail"]))
    o1 = uno(888, oid1)
    prova("nello scambio: il cambio, coi sats che arrivano in Lightning, e la "
          "prima firma di chi compra",
          ("cambio", 99_186, corpo["cambio"]["lockup"], True, "venditore"),
          (o1["destinazione"]["tipo"], (o1["cambio"] or {}).get("ricevi"),
           o1["incasso"], o1["proposta"]["mia"], o1["proposta"]["verso"]))
    prova("...e chi vende viene avvisato che tocca al suo telefono", True,
          detto_a(999, "Chi compra ha fatto il cambio in Lightning"))

    # ---- 5) la seconda firma dal telefono di chi vende -----------------------
    print("\n[la seconda firma dal telefono di chi vende]")
    o1c = uno(999, oid1)
    storta = copy.deepcopy(o1c)
    pt = PSBT.from_string(o1c["proposta"]["psbt"])
    pt.outputs[1].value -= 100     # la firma di chi compra resta, le uscite no
    storta["proposta"]["psbt"] = pt.to_string()
    altra = V.firma_compatta(chiave2(888), SRV.onchain_messaggio_ricevuto(
        oid1, o1c["indirizzo"]["indirizzo"]))
    t = telefono("p2p-cofirma", tg=999, parole=semi[999], oc=o1c, storta=storta,
                 altraFirma=altra)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    prova("il telefono di chi vende sa che tocca a lui", True, t["daFirmare"])
    prova("una proposta toccata dopo la prima firma: non co-firma",
          "la prima firma non è di chi vende", t["storta"])
    prova("una conferma che non ha firmato il suo seme: non co-firma",
          "non hai confermato tu di averlo ricevuto", t["altraConferma"])
    prova("...e in tutt'e due i casi al server non va niente", 0, t["prima"])
    mandato = t.get("mandato") or []
    prova("quella vera: co-firma e la manda alla rotta dello scambio",
          ("", 1, f"/api/p2p/onchain/{oid1}/firma"),
          (t["no"], len(mandato), mandato[0][0] if mandato else ""))
    tx = (mandato[0][1] if mandato else {}).get("tx", "")
    prova("chi compra non mette la seconda firma sul suo stesso cambio: 409", 409,
          gesto(888, oid1, "firma", tx=tx).status_code)
    V.cartone("/cartone/modo?m=giu")
    r = gesto(999, oid1, "firma", tx=tx)
    prova("SATS Routing tace: non si trasmette (503), e il cambio resta",
          (503, "cambio", 0),
          (r.status_code, uno(888, oid1)["destinazione"]["tipo"], len(TRASMESSE)))
    V.cartone("/cartone/modo?m=normale")
    banco.DETTO.clear()
    r = gesto(999, oid1, "firma", tx=tx)
    prova("vivo: rilasciato, e la transazione porta il prezzo al cambio",
          (200, "rilasciato", [(corpo["cambio"]["lockup"], 100_000)]),
          (r.status_code, r.json().get("stato"),
           [(o.script_pubkey.address(N), o.value)
            for o in Transaction.from_string(TRASMESSE[-1]).vout
            if o.value == 100_000] if TRASMESSE else []))
    prova("...e chi compra legge che paga SATS Routing, non «al tuo wallet»",
          (True, False), (detto_a(888, "SATS Routing paga la tua richiesta Lightning"),
                          detto_a(888, "i sats arrivano al tuo wallet")))

    # ---- 6) il cambio morto prima della seconda firma ----------------------
    print("\n[il cambio che muore prima della seconda firma]")
    oid2 = scambio()
    gesto(999, oid2, "euro-ricevuti", firma=firma_ricevuto(999, uno(999, oid2)))
    corpo2 = cambio_dal_banco(uno(888, oid2), 99_186)
    prova("il cambio nasce: 200", 200, nasce(oid2, corpo2).status_code)
    V.cartone(f"/cartone/stato?id={corpo2['cambio']['id']}&s=swap.expired")
    trasmesse = len(TRASMESSE)
    banco.DETTO.clear()
    r = seconda_del_banco(oid2)
    o2 = uno(888, oid2)
    prova("scaduto da SATS Routing: non si trasmette (409), il cambio si toglie, "
          "il Lightning resta scelto", (409, trasmesse, "", None, None, True),
          (r.status_code, len(TRASMESSE), o2["incasso"], o2["proposta"],
           o2["cambio"], o2["incasso_ln"]))
    prova("...e chi compra lo sa", True, detto_a(888, "non è partito"))
    prova("togliere un cambio che non c'e' piu': 409", 409,
          gesto(888, oid2, "cambio/togli").status_code)
    corpo2 = cambio_dal_banco(uno(888, oid2), 99_186)
    prova("si rifa': 200", 200, nasce(oid2, corpo2).status_code)
    prova("...e chi compra lo toglie da se': 200, lo scambio torna libero",
          (200, ""), (gesto(888, oid2, "cambio/togli").status_code,
                      uno(888, oid2)["incasso"]))

    # ---- 7) la disputa porta via il cambio ---------------------------------
    print("\n[la disputa porta via il cambio]")
    corpo2 = cambio_dal_banco(uno(888, oid2), 99_186)
    nasce(oid2, corpo2)
    r = gesto(888, oid2, "disputa", motivo="non arrivano")
    o2 = uno(888, oid2)
    prova("in disputa il cambio se ne va e chi compra riceve on-chain: il "
          "wallet del Profilo torna", (200, "disputa", fisso, False, None, None),
          (r.status_code, o2["stato"], o2["incasso"], o2["incasso_ln"], o2["cambio"],
           o2["proposta"]))
    prova("...e in disputa il Lightning non si risceglie: 409", 409,
          gesto(888, oid2, "ricevi-lightning", si=True).status_code)

    # ---- 8) chi compra torna all'on-chain dopo la conferma -----------------
    print("\n[chi compra torna all'on-chain dopo la conferma]")
    oid3 = scambio()
    gesto(999, oid3, "euro-ricevuti", firma=firma_ricevuto(999, uno(999, oid3)))
    banco.DETTO.clear()
    r = gesto(888, oid3, "ricevi-lightning", si=False)
    prova("«₿ Ricevi on-chain invece»: 200, torna il wallet del Profilo",
          (200, False, fisso), (r.status_code, r.json()["incasso_ln"], r.json()["incasso"]))
    prova("...e chi vende, che aveva gia' confermato, lo sa", True,
          detto_a(999, "Chi compra ha scelto dove ricevere"))
    miei = [uno(999, oid3), uno(999, oid1)]
    t = telefono("p2p-riprendi", tg=999, parole=semi[999], miei=miei)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    mandato = t.get("mandato") or []
    prova("il telefono di chi vende firma da solo il rilascio confermato (solo "
          "quello: lo scambio chiuso no)",
          ([True, False], 1, f"/api/p2p/onchain/{oid3}/proposta", "venditore"),
          (t["giudice"], len(mandato), mandato[0][0] if mandato else "",
           (mandato[0][1] if mandato else {}).get("verso")))
    r = gesto(999, oid3, "proposta", **(mandato[0][1] if mandato else {}))
    prova("...il server la prende: 200", 200, r.status_code)
    o3 = uno(888, oid3)
    p = PSBT.from_string(o3["proposta"]["psbt"])
    p.sign_with(radice(888).derive(
        f"m/48h/1h/0h/2h/0/{o3['indirizzo']['mio_numero']}").key)
    r = gesto(888, oid3, "firma", tx=finalize_psbt(p).serialize().hex())
    prova("...e la seconda di chi compra: rilasciato al suo wallet",
          (200, "rilasciato", True),
          (r.status_code, r.json().get("stato"),
           any(o.script_pubkey.address(N) == fisso and o.value == 100_000
               for o in Transaction.from_string(TRASMESSE[-1]).vout)))

    # ---- 9) la leva rispenta -------------------------------------------------
    print("\n[la leva rispenta]")
    oid4 = scambio()
    SRV.P2P_ALTRA_RETE_ATTIVO = False
    prova("a leva spenta il preventivo e il cambio sono 404, la scelta del "
          "Lightning 403", (404, 404, 403),
          (preventivo(888, oid4).status_code, nasce(oid4, {}).status_code,
           gesto(888, oid4, "ricevi-lightning", si=True).status_code))
    prova("...ma la via d'uscita resta: chi compra torna all'on-chain", (200, fisso),
          (gesto(888, oid4, "ricevi-lightning", si=False).status_code,
           uno(888, oid4)["incasso"]))

    print("\n[le sentinelle]")
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
