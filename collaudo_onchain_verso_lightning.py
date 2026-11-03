# -*- coding: utf-8 -*-
"""
CHI VENDE ON-CHAIN RICEVE IN LIGHTNING (28 ott 2026, cantiere
onchain-verso-lightning, piano in dieci righe approvato da Andrea) — il
giro col SERVER VERO per HTTP (TestClient, la app vera), il SATS ROUTING
DI CARTONE acceso su una porta di questo computer (rete testnet: le
forme tb1…/lntb… del signet dell'on-chain), e il TELEFONO VERO (il codice
della pagina e di swap/*.js, coi due bundle) in node.

LE SCENE:
  - il cancello: a leva spenta niente; accesa ma con l'on-chain e il
    fornitore su reti diverse (oggi: signet e bitcoin) niente lo stesso,
    e il pannello lo dice in rosso; con le reti giuste si apre;
  - la scelta nel Profilo: sempre on-chain / sempre Lightning / ogni
    volta, e l'esempio vero del costo su 100.000 sats;
  - la vendita di chi riceve in Lightning: l'incasso resta vuoto anche
    con un wallet scelto; «Ho ricevuto» FIRMATO dal telefono di chi
    compra; il preventivo (prezzo, quanto arriva, il costo del cambio);
    la richiesta dal Lightning address; il cambio che nasce DAL TELEFONO
    di chi vende (le 12 parole, la verifica, la firma della destinazione,
    la prima firma) e i no del server; la seconda firma DAL TELEFONO di
    chi compra, coi suoi no; il fornitore che tace (503) e quello vivo
    (rilasciato, il prezzo al cambio);
  - il cambio morto prima della seconda firma: non parte niente, si toglie;
  - «scelgo ogni volta» con l'on-chain allo sblocco: incasso adesso,
    prima firma di chi vende, seconda di chi compra;
  - sotto il minimo del cambio: si riceve on-chain;
  - di nuovo «sempre on-chain»: le vendite che aspettavano prendono il wallet.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco PRIMA dell'import del server; mempool di cartone; nessuna rete
fuori da 127.0.0.1; nessun sats.

USO:  python collaudo_onchain_verso_lightning.py
"""
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.request

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
PORTA = 0


def firma_compatta(chiave, messaggio: bytes) -> str:
    """La firma come la fa il telefono (@scure/bip32: r||s, 64 byte),
    dalla firma DER di embit."""
    der = chiave.sign(hashlib.sha256(messaggio).digest()).serialize()
    lr = der[3]
    r = der[4:4 + lr]
    s = der[6 + lr:]
    return (r[-32:].rjust(32, b"\0") + s[-32:].rjust(32, b"\0")).hex()


def cartone(percorso, corpo=None):
    dati = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORTA}{percorso}", data=dati,
        headers={"Content-Type": "application/json"} if dati else {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def fattura(sats, vita=86400):
    """Una richiesta Lightning «del wallet di chi vende», fatta dal
    cartone (testnet, lntb…), col segreto che conosce il banco."""
    pre = secrets.token_bytes(32)
    imp = hashlib.sha256(pre).hexdigest()
    inv = cartone_satsrouting.cripto("fattura", rete="testnet", sats=sats,
                                     impronta=imp, scadenza=vita)["invoice"]
    return {"invoice": inv, "preimage": pre.hex(), "impronta": imp}


# ──────────────────────────────────────────────────────────────────────
# IL TELEFONO: i pezzi veri della pagina (l'on-chain e il riquadro del
# cambio) e di swap/*.js, coi due bundle, in node. Le chiamate al server
# di Barattolo sono finte e REGISTRATE: quel che il telefono manda lo
# porta il banco al server vero, e il giudice e' lui (la prova doppia).
# Quelle al cartone sono vere.
# ──────────────────────────────────────────────────────────────────────
def pezzi_pagina():
    mini = open(os.path.join(banco.QUI, "miniapp.html"),
                encoding="utf-8").read().replace("\r\n", "\n")

    def f(firma):
        i = mini.index(firma)
        return mini[i:mini.index("\n}\n", i) + 3]

    def riga(inizio):
        i = mini.index(inizio)
        return mini[i:mini.index("\n", i) + 1]

    def blocco(inizio, fine):
        i = mini.index(inizio)
        return mini[i:mini.index(fine, i) + len(fine)]
    firme = [
        # (30 ott 2026, onchain-mainnet) la rete la dice il server: il
        # giudice e le due letture, prima di chi li usa
        "function onchainRete(){", "function onchainReteBtc(B){",
        "function onchainLeggiChiaveConto(B, s){",
        "function importoBolt11(pr){", "function leggiBolt11(pr){",
        "function onchainLeggiXpub(B, s){", "function onchainConto(B, parole, strada){",
        "function onchainMieChiavi(B, parole, o){", "function onchainScriptOrdine(B, o){",
        "function onchainMessaggioDestinazione(tipo, valore){",
        "function onchainNormaDestinazione(tipo, valore){",
        "function onchainChiaveDestinazione(B, parole){",
        "async function onchainFirmaDestinazione(B, parole, tipo, valore){",
        "async function onchainDestinazioneMia(B, parole, d){",
        "function onchainIndirizzoEsterno(B, d){",
        "async function onchainIncassoAtteso(B, parole, o, io){",
        "function onchainMessaggioRicevuto(oid, indirizzo){",
        "async function onchainFirmaRicevuto(B, parole, oc){",
        "async function onchainRicevutoMio(B, parole, oc){",
        "function onchainPrimaDiChiVende(o){", "function onchainDerACompatta(der){",
        "function onchainFirmataDaChiVende(B, tx, o, w){",
        "function onchainUsciteVersoVenditore(o, incasso, piuVb){",
        "function onchainPsbtFirmata(B, o, io, w, uscite){",
        "async function onchainCofirma(o, parole){",
        "function onchainNomeCambio(p){", "function onchainFatturaPerche(perche, p){",
        "function onchainCambioRidisegna(o){", "function onchainCambioBlocco(o){",
        "function onchainCambioLeggiCampo(oc){",
        "async function onchainCambioConferma(btn, o){"]
    return "\n".join([riga("const ONCHAIN_VERSIONI_PROVA = "),
                      blocco("const ONCHAIN_RETI = {", "\n};\n"),
                      riga("const ONCHAIN_QUOTA_TETTO = "),
                      riga("const ONCHAIN_POLVERE = "),
                      riga("const onchainCambi = {};")]
                     + [f(x) for x in firme])


BANCO_TELEFONO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const memoria = new Map();
const fetchVero = globalThis.fetch;
const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL,
  Uint8Array, BigInt, setTimeout, clearTimeout, setInterval, clearInterval, Promise, JSON, Date, Math,
  fetchVero: globalThis.fetch,
  localStorage: {getItem: k => memoria.has(k) ? memoria.get(k) : null,
                 setItem: (k, v) => { memoria.set(k, String(v)); }, removeItem: k => memoria.delete(k)}};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(D.btc, 'utf8'), ctx);
vm.runInContext(fs.readFileSync(D.swap, 'utf8'), ctx);
vm.runInContext(`
let myTgId = ${JSON.stringify(D.tg)};
const FOTO_BASE = '', API_BASE = '/api';
let swapLeve = ${JSON.stringify(D.leve)};
const swapAcceso = () => !!(swapLeve && swapLeve.attivo);
const elementi = {};
function el(id){ return elementi[id] || null; }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const fmt = n => String(n);
function haptic(){}
const avvisi = [];
function toast(m){ avvisi.push(m); }
let currentOrder = null, preventiviSwap = {}, sceltaIncassoSwap = {};
let tg = {initDataUnsafe: {user: {language_code: 'it'}}};
function linguaSwap(){ return 'it'; }
function ridisegnaIncassoSwap(){}
function renderSwap(){}
const B0 = BarattoloBTC;
const caricaBitcoin = async () => B0;
let onchainSrv = null, onchainOrdini = [], PAROLE = '';
const onchainSemeLocale = () => PAROLE;
async function onchainLeggiOrdini(){ return onchainOrdini; }
const onchainAttesa = () => () => {};
const authHdr = () => '';
async function caricaSwapTelefono(){ return true; }
async function loadOrders(){}
function renderOrders(){}
function openOrder(){}
/* il server di Barattolo: finto, e ogni corpo registrato */
const alServer = [];
const fetch = async (url, o) => {
  if (String(url).startsWith('/api/')) {
    alServer.push([String(url), JSON.parse((o && o.body) || '{}')]);
    return {ok: true, status: 200, json: async () => ({ok: true})};
  }
  return fetchVero(url, o);
};
`, ctx);
for (const f of D.telefono) vm.runInContext(fs.readFileSync(f, 'utf8'), ctx);
vm.runInContext(D.pagina, ctx);
const run = c => vm.runInContext(c, ctx);
(async () => {
  const out = {};
  run(`PAROLE = ${JSON.stringify(D.parole)}`);
  if (D.fase === 'ricevuto') {
    out.firma = await run(`onchainFirmaRicevuto(B0, PAROLE, ${JSON.stringify(D.oc)})`);
  } else if (D.fase === 'vende') {
    const oc = D.oc, o = {id: D.ordine, onchain: D.riassunto};
    run(`onchainOrdini = [${JSON.stringify(oc)}]; currentOrder = ${JSON.stringify(o)}`);
    run(`onchainCambi[${oc.id}] = {stato: 'pronto', p: ${JSON.stringify(D.preventivo)}, fattura: ${JSON.stringify(D.corta)}}`);
    out.riquadro = run(`onchainCambioBlocco(currentOrder)`);
    /* la richiesta che vive un'ora: no, e nessun cambio chiesto */
    const v0 = (await (await fetchVero(D.base + '/cartone/visto')).json()).swap;
    await run(`onchainCambioConferma(null, currentOrder)`);
    out.corta = {errore: run(`onchainCambi[${oc.id}].errore || ''`),
                 swap: (await (await fetchVero(D.base + '/cartone/visto')).json()).swap - v0,
                 server: run('alServer.length')};
    /* quella buona: niente 12 parole a parte (29 ott 2026), il cambio
       nasce al primo «Conferma» col seme dell'on-chain */
    run(`onchainCambi[${oc.id}].fattura = ${JSON.stringify(D.buona)}; elementi['ocCambioFattura_${oc.id}'] = {value: ${JSON.stringify(D.buona)}}`);
    out.nienteSpunta = !run(`onchainCambioBlocco(currentOrder)`).includes('ocCambioSpunta_');
    await run(`onchainCambioConferma(null, currentOrder)`);
    out.cassettoFornitore = memoria.get('barattolo_swap_' + D.tg) || null;
    out.nato = run('alServer.slice()');
    out.errore = run(`(onchainCambi[${oc.id}] || {}).errore || ''`);
    const lista = JSON.parse(memoria.get('barattolo_swap_lista_' + D.tg) || '[]');
    const rec = lista.find(r => r.onchain === oc.id) || {};
    out.rec = {tipo: rec.tipo, ordine: rec.ordine, onchain: rec.onchain, ricevi: rec.ricevi, mandi: rec.mandi,
               lockup: rec.lockupAddress, fase: run(`swapFase(swapLista().find(r => r.onchain === ${oc.id}))`),
               frase: run(`frasestatoSwap(swapLista().find(r => r.onchain === ${oc.id}))`),
               daMandare: run(`bitcoinDaMandare(swapLista().find(r => r.onchain === ${oc.id}))`),
               indice: rec.indice, seme: rec.seme, indirizzo: rec.indirizzo,
               prossimo: JSON.parse(memoria.get('barattolo_swap_oc_' + D.tg) || '{}').prossimo,
               incasso: run(`onchainMieChiavi(B0, PAROLE, ${JSON.stringify(oc)}).incasso`)};
    out.recId = rec.id;
    /* la sorveglianza lo segue come gli altri: i bitcoin visti */
    await fetchVero(`${D.base}/cartone/stato?id=${rec.id}&s=transaction.mempool`);
    await run('swapGiro()');
    out.visti = run(`frasestatoSwap(swapLista().find(r => r.onchain === ${oc.id}))`);
    /* IL CAMBIO FALLISCE (29 ott 2026): i bitcoin tornano DA SOLI, al
       giro dopo, al /1/n di chi vende, con la chiave dello stesso seme */
    await fetchVero(`${D.base}/cartone/stato?id=${rec.id}&s=invoice.failedToPay`);
    const recOra = () => swapLista().find(r => r.onchain === oc.id) || {};
    const swapLista = () => JSON.parse(memoria.get('barattolo_swap_lista_' + D.tg) || '[]');
    await run('swapGiro()');
    for (let i = 0; i < 50 && !(recOra().rimborso || {}).txid && !recOra().errore; i++)
      await new Promise(r => setTimeout(r, 100));
    const vR = (await (await fetchVero(D.base + '/cartone/visto')).json());
    const tR = (vR.trasmesse || []).find(x => recOra().rimborso && x.txid === recOra().rimborso.txid) || {};
    out.rimborso = {txid: /^[0-9a-f]{64}$/.test(String((recOra().rimborso || {}).txid || '')),
      errore: recOra().errore || '',
      aIncasso: !!(tR.uscite && tR.uscite[0] && tR.uscite[0].script === run(
        `B0.hex.encode(B0.OutScript.encode(B0.Address(B0.TEST_NETWORK).decode(${JSON.stringify(rec.indirizzo)})))`))};
    out.avvisi = run('avvisi.slice()');
  } else if (D.fase === 'compra') {
    const oc = D.oc;
    out.storta = await run(`onchainCofirma(${JSON.stringify(D.storta)}, PAROLE)`);
    out.altraConferma = await run(`onchainCofirma(${JSON.stringify(Object.assign({}, oc, {rilascio_firma: D.altraFirma}))}, PAROLE)`);
    out.prima = run('alServer.length');
    out.no = await run(`onchainCofirma(${JSON.stringify(oc)}, PAROLE)`);
    out.mandato = run('alServer.slice()');
    out.prima_di_chi_vende = run(`onchainPrimaDiChiVende(${JSON.stringify(oc)})`);
  }
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def telefono(fase, **dati):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="onchain_ln_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        base = f"http://127.0.0.1:{PORTA}"
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
    global PORTA
    print("=" * 58)
    print("  ⚡ CHI VENDE ON-CHAIN RICEVE IN LIGHTNING — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import httpx
    from embit import bip32, bip39, script
    from embit.finalizer import finalize_psbt
    from embit.networks import NETWORKS
    from embit.psbt import PSBT
    from embit.transaction import (Transaction, TransactionInput,
                                   TransactionOutput)
    from fastapi.testclient import TestClient
    SRV.httpx = httpx           # il cartone e' vero, su 127.0.0.1
    _, PORTA = cartone_satsrouting.avvia(0, rete="testnet")
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
        return firma_compatta(chiave2(tg),
                              SRV.onchain_messaggio_destinazione(tipo, valore))

    def firma_ricevuto(tg, o):
        return firma_compatta(chiave2(tg), SRV.onchain_messaggio_ricevuto(
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
    annunci = []
    for n, prezzo in enumerate((100_000, 100_000, 100_000, 40_000, 100_000)):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(888,?,'una cosa',?,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',1,'sats','nuovo')", (f"Cosa in Lightning {n}", prezzo))
        annunci.append(cur.lastrowid)
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999, 888]
    SRV.ONCHAIN_ATTIVO = True
    SRV.SWAP_ATTIVO = True
    SRV.SWAP_SOLO_MODERATORI = True
    SRV.SWAP_MIN_SATS = 25_000
    SRV.SWAP_API_BASE = f"http://127.0.0.1:{PORTA}"
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.CAMBIO_BTC_LN_ATTIVO = True
    SRV.ONCHAIN_INCASSO_LN_ATTIVO = False
    SRV.SWAP_RETE = "bitcoin"

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def busta(tg):
        come(tg)
        return c.get("/api/me").json().get("onchain_ln") or {}

    def modo(tg, m):
        come(tg)
        return c.post("/api/onchain/incasso/modo", json={"modo": m})

    def riga_leva():
        come(999)
        for g in c.get("/api/admin/leve").json()["gruppi"]:
            for v in g["voci"]:
                if v["chiave"] == "ONCHAIN_INCASSO_LN_ATTIVO":
                    return v
        return {}

    def compra(aid):
        come(999)
        r = c.post("/api/orders", json={"annuncio_id": aid, "consegna": "ritiro",
                                        "metodo": "onchain", "offerta_id": 0})
        o = r.json().get("onchain") or {}
        MONETE[o["indirizzo"]["indirizzo"]] = [{
            "txid": secrets.token_hex(32), "vout": 0,
            "value": o["importo_sats"], "status": {"confirmed": True}}]
        c.post(f"/api/onchain/ordini/{o['id']}/controlla")
        return ordine(999, o["id"])

    def ordine(tg, oid):
        come(tg)
        return next(x for x in c.get("/api/onchain/ordini").json()["ordini"]
                    if x["id"] == oid)

    def riassunto(tg, oid):
        come(tg)
        return next(x for x in c.get("/api/orders").json()
                    if (x.get("onchain") or {}).get("id") == oid)

    def ricevuto(oid, firma):
        come(999)
        return c.post(f"/api/onchain/ordini/{oid}/rilascio-chiesto",
                      json={"firma": firma})

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

    def seconda(oid, tg=999):
        o = ordine(tg, oid)
        p = PSBT.from_string(o["proposta"]["psbt"])
        p.sign_with(radice(tg).derive(
            f"m/48h/1h/0h/2h/0/{o['indirizzo']['mio_numero']}").key)
        come(tg)
        return c.post(f"/api/onchain/ordini/{oid}/firma",
                      json={"tx": finalize_psbt(p).serialize().hex()})

    def uscite_cambio(o, lockup):
        """le uscite del rilascio verso il cambio: il prezzo esatto, il
        resto a chi compra (la rete come il telefono: 12 vB del taproot)"""
        vb = 11 + 105 * len(o["utxo"]) + 31 * 2 + 12
        resto = o["importo_sats"] - o["prezzo_sats"] - vb * 2
        return [(lockup, o["prezzo_sats"]), (o["rimborso"], resto)]

    def cambio_dal_banco(o, sats_fattura):
        """il telefono di chi vende fatto dal banco (embit + HTTP verso il
        cartone): per le scene dove il telefono vero l'ha gia' provato"""
        f = fattura(sats_fattura)
        tariffe = cartone("/v2/swap/submarine")
        chiave = radice(888).derive("m/44h/0h/0h/0/7").key.get_public_key()
        r = cartone("/v2/swap/submarine", {
            "from": "BTC", "to": "BTC", "invoice": f["invoice"],
            "refundPublicKey": chiave.sec().hex(),
            "pairHash": tariffe["BTC"]["BTC"]["hash"]})
        return {"cambio": {"fornitore": "satsrouting", "id": r["id"],
                           "lockup": r["address"], "ricevi": sats_fattura,
                           "mandi": r["expectedAmount"],
                           "scade_fattura": int(time.time()) + 86400,
                           "timeout": r["timeoutBlockHeight"]},
                "firma": firma_dest(888, "cambio", f"{o['id']}:{r['address']}"),
                "psbt": psbt_di(o, uscite_cambio(o, r["address"]), 888).to_string()}

    def nasce(oid, corpo, tg=888):
        come(tg)
        return c.post(f"/api/onchain/ordini/{oid}/cambio", json=corpo)

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})
    come(888)
    r = c.post("/api/onchain/incasso", json={
        "tipo": "indirizzo", "valore": fisso,
        "firma": firma_dest(888, "indirizzo", fisso)})
    prova("chi vende ha un wallet on-chain suo, firmato dal seme", 200,
          r.status_code)

    # ---- 1) il cancello ----------------------------------------------------
    print("\n[il cancello: la leva, e le reti giuste]")
    prova("a leva spenta: niente busta, niente scelta, niente esempio",
          (False, 403, 404),
          (busta(888).get("attivo"), modo(888, "lightning").status_code,
           c.get("/api/onchain/cambio/esempio").status_code))
    SRV.ONCHAIN_INCASSO_LN_ATTIVO = True
    prova("accesa, ma l'on-chain sta su signet e il fornitore su bitcoin: "
          "chiusa lo stesso, e il pannello lo dice in rosso",
          (False, True, True),
          (busta(888).get("attivo"), riga_leva().get("allarme"),
           "FERMA" in str(riga_leva().get("nota") or riga_leva())))
    SRV.SWAP_RETE = "testnet"
    prova("con le reti giuste si apre: di serie «sempre on-chain»",
          (True, "onchain", 25_000, False),
          (busta(888).get("attivo"), busta(888).get("modo"),
           busta(888).get("minimo"), bool(riga_leva().get("allarme"))))

    # ---- 2) la scelta nel Profilo ----------------------------------------
    print("\n[la scelta nel Profilo e l'esempio del costo]")
    prova("una scelta che non c'e': 400", 400, modo(888, "boh").status_code)
    r = modo(888, "lightning")
    prova("«sempre Lightning»: 200, e /api/me lo rilegge", (200, "lightning"),
          (r.status_code, busta(888).get("modo")))
    come(888)
    e = c.get("/api/onchain/cambio/esempio?sats=100000").json()
    prova("l'esempio su 100.000 sats: arrivano 99.186 in Lightning, il "
          "cambio costa 814 (0,5 % + 318), lo fa SATS Routing",
          (True, 100_000, 99_186, 814, 100_000, "SATS Routing"),
          (e.get("ok"), e.get("prezzo"), e.get("ricevi"), e.get("costo"),
           e.get("mandi"), e.get("fornitore_nome")))

    # ---- 3) la vendita di chi riceve in Lightning --------------------------
    print("\n[la vendita: l'incasso resta vuoto fino allo sblocco]")
    o1 = compra(annunci[0])
    oid1 = o1["id"]
    prova("pagato, e l'incasso resta vuoto anche col wallet scelto",
          ("pagato", "", "lightning"),
          (o1["stato"], o1["incasso"], o1.get("modo_venditore")))
    come(888)
    prova("prima della conferma di chi compra, niente preventivo: 409", 409,
          c.get(f"/api/onchain/ordini/{oid1}/cambio/preventivo").status_code)
    print("\n[«Ho ricevuto», firmato dal telefono di chi compra]")
    t = telefono("ricevuto", tg=999, parole=semi[999], oc=o1)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    prova("la conferma del telefono la verifica il server: 200", 200,
          ricevuto(oid1, t["firma"]).status_code)
    o1 = ordine(999, oid1)
    prova("...resta scritta, con la firma", (True, t["firma"]),
          (bool(o1["rilascio_chiesto_il"]), o1["rilascio_firma"]))
    prova("...e chi vende viene avvisato col costo del cambio, non «scegli "
          "dove ricevere»", True,
          any(chi == 888 and "cambio in Lightning" in testo
              for chi, testo in banco.DETTO))
    ria = riassunto(888, oid1)["onchain"]
    prova("nell'ordine chi vende vede: in Lightning, confermato, niente incasso",
          ("lightning", True, False, None),
          (ria["modo_venditore"], ria["rilascio_chiesto"],
           ria["incasso_scelto"], ria["cambio"]))
    print("\n[il preventivo e la richiesta dal Lightning address]")
    come(888)
    p = c.get(f"/api/onchain/ordini/{oid1}/cambio/preventivo").json()
    prova("il preventivo dell'ordine: tutto il prezzo al cambio, 99.186 in "
          "Lightning, costo 814, avanzo 0, e le vite della richiesta",
          (True, 100_000, 99_186, 100_000, 814, 0, "lightning", False,
           82_800, 10_800),
          (p.get("ok"), p.get("prezzo"), p.get("ricevi"), p.get("mandi"),
           p.get("costo"), p.get("avanzo"), p.get("modo"), p.get("ln_address"),
           p.get("vita_incollata_s"), p.get("vita_address_s")))
    come(999)
    prova("chi compra non lo chiede: 403", 403,
          c.get(f"/api/onchain/ordini/{oid1}/cambio/preventivo").status_code)
    come(888)
    prova("senza Lightning address nel profilo la richiesta non si prende: 409",
          409, c.post(f"/api/onchain/ordini/{oid1}/cambio/fattura",
                      json={"sats": 99_186}).status_code)
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address='alan@cartone.example' WHERE tg_id=888")
    con.commit()
    con.close()
    dal_ln = fattura(99_186, vita=4 * 3600)["invoice"]
    chiesti = []

    async def ln_finto(ln, sats):
        chiesti.append((ln, sats))
        return dal_ln
    vero_ln = SRV.invoice_da_ln_address
    SRV.invoice_da_ln_address = ln_finto
    come(888)
    r = c.post(f"/api/onchain/ordini/{oid1}/cambio/fattura", json={"sats": 99_186})
    prova("col Lightning address: la chiede il server, per la cifra esatta",
          (200, dal_ln, [("alan@cartone.example", 99_186)]),
          (r.status_code, r.json().get("fattura"), chiesti))
    prova("...una cifra fuori misura: 400", 400,
          c.post(f"/api/onchain/ordini/{oid1}/cambio/fattura",
                 json={"sats": 100_000}).status_code)
    SRV.invoice_da_ln_address = vero_ln
    come(888)
    p = c.get(f"/api/onchain/ordini/{oid1}/cambio/preventivo").json()

    print("\n[il cambio nasce dal telefono di chi vende]")
    buona = fattura(99_186)["invoice"]
    corta = fattura(99_186, vita=3600)["invoice"]
    o1v = ordine(888, oid1)
    t = telefono("vende", tg=888, parole=semi[888], oc=o1v, ordine=o1v["ordine_id"],
                 riassunto=riassunto(888, oid1)["onchain"], preventivo=p,
                 buona=buona, corta=corta)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    rq = t.get("riquadro", "")
    prova("il riquadro dice che e' un cambio, quanto costa, quanto arriva, e "
          "avvisa della capienza", (True, True, True, True),
          ("È un cambio, fatto da SATS Routing</b>: costa 814 sats" in rq,
           "Ricevi <b>99186 sats in Lightning</b> invece di 100000 on-chain" in rq,
           "deve poter ricevere 99186 sats in una volta" in rq,
           "Prendila dal mio Lightning address" in rq))
    prova("una richiesta che vive un'ora: no, e non si chiede niente a nessuno",
          ("Questa richiesta scade fra meno di 23 ore: creane una che duri di più.", 0, 0),
          (t["corta"]["errore"], t["corta"]["swap"], t["corta"]["server"]))
    prova("niente 12 parole a parte: nessuna spunta nel riquadro, e nessun "
          "cassetto del fornitore nasce", (True, None),
          (t["nienteSpunta"], t["cassettoFornitore"]))
    mandati = t.get("nato") or []
    url, corpo = mandati[-1] if mandati else ("", {})
    prova("al primo «Conferma» il cambio nasce, e al server va UNA chiamata "
          "con le sole parti pubbliche, la firma e la prima firma",
          (1, f"/api/onchain/ordini/{oid1}/cambio", ["cambio", "firma", "psbt"], ""),
          (len(mandati), url, sorted(corpo), t["errore"]))
    rec = t["rec"]
    prova("...il cambio entra nella lista del telefono, legato all'ordine",
          ("sub", o1v["ordine_id"], oid1, 99_186, 100_000, True, 0, 1),
          (rec["tipo"], rec["ordine"], rec["onchain"], rec["ricevi"], rec["mandi"],
           str(rec["lockup"]).startswith("tb1p"), rec["indice"], rec["prossimo"]))
    prova("...la chiave di riserva e' dello STESSO seme dell'on-chain, e il "
          "rimborso va da solo al /1/n di chi vende", ("onchain", True),
          (rec["seme"], bool(rec["incasso"]) and rec["indirizzo"] == rec["incasso"]))
    # il «Recupera» della pagina Cambio: la xpub della radice delle STESSE
    # 12 parole del 2-di-3 ritrova il cambio, all'indice giusto
    trovati = cartone("/v2/swap/restore", {"xpub": bip32.HDKey.from_seed(
        bip39.mnemonic_to_seed(semi[888])).to_public().to_base58()})
    ritrovato = next((x for x in trovati if x["id"] == t["recId"]), {})
    prova("...e le 12 parole dell'on-chain lo ritrovano col «Recupera»",
          ("submarine", 0), (ritrovato.get("type"),
                             (ritrovato.get("refundDetails") or {}).get("keyIndex")))
    prova("...e dice che i bitcoin li manda il deposito di garanzia, senza «manda "
          "tu» e senza QR da pagare",
          ("creato", "I bitcoin partono dal deposito di garanzia appena chi ha "
           "comprato mette la seconda firma: poi SATS Routing paga la tua "
           "richiesta Lightning.", ""),
          (rec["fase"], rec["frase"], rec["daMandare"]))
    prova("...la sorveglianza lo segue come gli altri", t["visti"],
          "Bitcoin visti: aspetto la conferma della rete, di solito una decina di minuti.")
    prova("...e se il cambio fallisce i bitcoin tornano DA SOLI al /1/n di "
          "chi vende, senza parole a parte ne' indirizzo da scrivere",
          {"txid": True, "errore": "", "aIncasso": True}, t.get("rimborso"))
    cartone(f"/cartone/stato?id={corpo['cambio']['id']}&s=invoice.set")

    print("\n[i no del server sul cambio]")
    import copy
    altro = copy.deepcopy(corpo)
    altro["firma"] = firma_dest(999, "cambio", f"{oid1}:{corpo['cambio']['lockup']}")
    r = nasce(oid1, altro)
    prova("la destinazione firmata da un ALTRO seme: 400", (400, True),
          (r.status_code, "non è firmato dal tuo seme" in r.json()["detail"]))
    altro = copy.deepcopy(corpo)
    altro["cambio"]["lockup"] = fisso
    r = nasce(oid1, altro)
    prova("un indirizzo che non e' un taproot: 400", (400, True),
          (r.status_code, "rete giusta" in r.json()["detail"]))
    altro = copy.deepcopy(corpo)
    altro["cambio"]["scade_fattura"] = int(time.time()) + 600
    prova("una richiesta che scade fra dieci minuti: 400", 400,
          nasce(oid1, altro).status_code)
    altro = copy.deepcopy(corpo)
    altro["cambio"]["mandi"] = 100_001
    prova("cifre che superano il prezzo: 400", 400, nasce(oid1, altro).status_code)
    altro = copy.deepcopy(corpo)
    altro["psbt"] = psbt_di(o1v, [(corpo["cambio"]["lockup"], 99_000),
                                  (o1v["rimborso"], o1v["importo_sats"] - 99_400)],
                            888).to_string()
    prova("una prima firma che al cambio manda meno del prezzo: 400", 400,
          nasce(oid1, altro).status_code)
    prova("chi compra non fa il cambio di chi vende: 403", 403,
          nasce(oid1, corpo, tg=999).status_code)
    r = nasce(oid1, corpo)
    prova("quello del telefono, intero: 200", 200, r.status_code)
    prova("...e una seconda volta no: 409", 409, nasce(oid1, corpo).status_code)
    come(999)
    prova("chi compra non propone al posto del cambio: 409", 409,
          c.post(f"/api/onchain/ordini/{oid1}/proposta",
                 json={"verso": "venditore", "psbt": corpo["psbt"]}).status_code)
    ria = riassunto(888, oid1)["onchain"]
    prova("nell'ordine: il cambio, coi sats che arrivano in Lightning",
          ("cambio", 99_186, corpo["cambio"]["lockup"]),
          (ria["incasso_tipo"], (ria["cambio"] or {}).get("ricevi"),
           (ria["cambio"] or {}).get("lockup")))
    prova("...e chi compra viene avvisato che tocca al suo telefono", True,
          any(chi == 999 and "ricevere in Lightning" in testo
              for chi, testo in banco.DETTO))

    print("\n[la seconda firma dal telefono di chi compra]")
    o1c = ordine(999, oid1)
    storta = copy.deepcopy(o1c)
    pt = PSBT.from_string(o1c["proposta"]["psbt"])
    pt.outputs[1].value -= 100     # la firma di chi vende resta, le uscite no
    storta["proposta"]["psbt"] = pt.to_string()
    altra = firma_compatta(chiave2(888), SRV.onchain_messaggio_ricevuto(
        oid1, o1c["indirizzo"]["indirizzo"]))
    t = telefono("compra", tg=999, parole=semi[999], oc=o1c, storta=storta,
                 altraFirma=altra)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    prova("una proposta toccata dopo la firma di chi vende: non co-firma",
          "la prima firma non è di chi vende", t["storta"])
    prova("una conferma che non ha firmato il suo seme: non co-firma",
          "non hai confermato tu di averlo ricevuto", t["altraConferma"])
    prova("...e in tutt'e due i casi al server non va niente", 0, t["prima"])
    mandato = t.get("mandato") or []
    prova("quella vera: co-firma e la manda", (True, "", 1,
                                                f"/api/onchain/ordini/{oid1}/firma"),
          (t["prima_di_chi_vende"], t["no"], len(mandato),
           mandato[0][0] if mandato else ""))
    tx = (mandato[0][1] if mandato else {}).get("tx", "")
    cartone("/cartone/modo?m=giu")
    come(999)
    r = c.post(f"/api/onchain/ordini/{oid1}/firma", json={"tx": tx})
    prova("SATS Routing tace: non si trasmette (503), e il cambio resta", (503, "cambio", 0),
          (r.status_code, ordine(888, oid1)["destinazione"]["tipo"], len(TRASMESSE)))
    cartone("/cartone/modo?m=normale")
    come(999)
    r = c.post(f"/api/onchain/ordini/{oid1}/firma", json={"tx": tx})
    prova("vivo: rilasciato, e la transazione porta il prezzo al cambio",
          (200, "rilasciato", [(corpo["cambio"]["lockup"], 100_000)]),
          (r.status_code, r.json().get("stato"),
           [(o.script_pubkey.address(N), o.value)
            for o in Transaction.from_string(TRASMESSE[-1]).vout
            if o.value == 100_000] if TRASMESSE else []))

    # ---- 4) il cambio morto prima della seconda firma --------------------
    print("\n[il cambio che muore prima della seconda firma]")
    o2 = compra(annunci[1])
    oid2 = o2["id"]
    prova("conferma firmata: 200", 200,
          ricevuto(oid2, firma_ricevuto(999, o2)).status_code)
    corpo2 = cambio_dal_banco(ordine(888, oid2), 99_186)
    prova("il cambio nasce: 200", 200, nasce(oid2, corpo2).status_code)
    cartone(f"/cartone/stato?id={corpo2['cambio']['id']}&s=swap.expired")
    trasmesse = len(TRASMESSE)
    r = seconda(oid2)
    o2v = ordine(888, oid2)
    prova("scaduto da SATS Routing: non si trasmette (409), il cambio si "
          "toglie, l'ordine torna da scegliere", (409, trasmesse, "", None, None),
          (r.status_code, len(TRASMESSE), o2v["incasso"], o2v["proposta"],
           o2v["cambio"]))
    prova("...e chi vende lo sa", True,
          any(chi == 888 and "non è partito" in testo for chi, testo in banco.DETTO))
    come(888)
    prova("togliere un cambio che non c'e' piu': 409", 409,
          c.post(f"/api/onchain/ordini/{oid2}/cambio/togli").status_code)
    corpo2 = cambio_dal_banco(ordine(888, oid2), 99_186)
    prova("si rifa': 200", 200, nasce(oid2, corpo2).status_code)
    come(888)
    prova("...e chi vende lo toglie da se': 200, l'ordine torna libero",
          (200, ""), (c.post(f"/api/onchain/ordini/{oid2}/cambio/togli").status_code,
                      ordine(888, oid2)["incasso"]))

    # ---- 5) «scelgo ogni volta», on-chain allo sblocco ----------------------
    print("\n[«scelgo ogni volta»: l'on-chain allo sblocco]")
    prova("«ogni volta»: 200", 200, modo(888, "ogni_volta").status_code)
    o3 = compra(annunci[2])
    oid3 = o3["id"]
    uscite3 = [(fisso, 100_000), (o3["rimborso"], o3["importo_sats"] - 100_000 - 400)]
    come(888)
    prova("prima della conferma chi vende non firma per primo: 403", 403,
          c.post(f"/api/onchain/ordini/{oid3}/proposta", json={
              "verso": "venditore",
              "psbt": psbt_di(o3, uscite3, 888).to_string()}).status_code)
    prova("...ne' prende l'incasso adesso: 409", 409,
          c.post(f"/api/onchain/ordini/{oid3}/incasso-ora").status_code)
    prova("conferma firmata: 200", 200,
          ricevuto(oid3, firma_ricevuto(999, o3)).status_code)
    come(888)
    r = c.post(f"/api/onchain/ordini/{oid3}/incasso-ora")
    prova("«Ricevi on-chain»: l'incasso e' il suo wallet, con la firma del seme",
          (200, fisso, "indirizzo"),
          (r.status_code, (r.json().get("onchain") or {}).get("incasso"),
           ((r.json().get("onchain") or {}).get("destinazione") or {}).get("tipo")))
    o3v = ordine(888, oid3)
    come(888)
    r = c.post(f"/api/onchain/ordini/{oid3}/proposta", json={
        "verso": "venditore", "psbt": psbt_di(o3v, uscite3, 888).to_string()})
    prova("...la prima firma e' di chi vende: 200", 200, r.status_code)
    prova("...e chi compra la vede come «prima di chi vende»", (False, "venditore"),
          (ordine(999, oid3)["proposta"]["mia"], ordine(999, oid3)["proposta"]["verso"]))
    r = seconda(oid3)
    prova("la seconda di chi compra: rilasciato al suo wallet",
          (200, "rilasciato", True),
          (r.status_code, r.json().get("stato"),
           any(o.script_pubkey.address(N) == fisso and o.value == 100_000
               for o in Transaction.from_string(TRASMESSE[-1]).vout)))

    # ---- 6) sotto il minimo --------------------------------------------------
    print("\n[sotto il minimo del cambio si riceve on-chain]")
    prova("di nuovo «sempre Lightning»", 200, modo(888, "lightning").status_code)
    o4 = compra(annunci[3])
    oid4 = o4["id"]
    ricevuto(oid4, firma_ricevuto(999, o4))
    come(888)
    p4 = c.get(f"/api/onchain/ordini/{oid4}/cambio/preventivo").json()
    prova("40.000 sats: sotto il minimo di SATS Routing (50.000), lo si dice",
          (False, "sotto_minimo", 50_000),
          (p4.get("ok"), p4.get("motivo"), p4.get("minimo")))
    come(888)
    r = c.post(f"/api/onchain/ordini/{oid4}/incasso-ora")
    prova("...e si riceve on-chain anche da «sempre Lightning»", (200, fisso),
          (r.status_code, (r.json().get("onchain") or {}).get("incasso")))

    # ---- 7) di nuovo «sempre on-chain» --------------------------------------
    print("\n[di nuovo «sempre on-chain»: le vendite che aspettavano]")
    o5 = compra(annunci[4])
    prova("in Lightning la vendita nuova nasce senza incasso", "", o5["incasso"])
    r = modo(888, "onchain")
    prova("«sempre on-chain»: 200, e la vendita che aspettava prende il wallet "
          "(anche la 2, rimasta senza cambio)",
          (200, 2, fisso, fisso),
          (r.status_code, r.json().get("ordini_aggiornati"),
           ordine(888, o5["id"])["incasso"], ordine(888, oid2)["incasso"]))
    SRV.ONCHAIN_INCASSO_LN_ATTIVO = False
    prova("a leva rispenta tutti tornano «onchain», come ieri", "onchain",
          ordine(999, o5["id"]).get("modo_venditore"))

    print("\n[le sentinelle]")
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)
    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
