# -*- coding: utf-8 -*-
"""
CHI VENDE BITCOIN SU UNO SCAMBIO P2P ON-CHAIN PAGA IL DEPOSITO IN
LIGHTNING (1 nov 2026, cantiere presa-altra-rete, tappa 3; studio del 30
ott, caso B2; Andrea alle 19:59: «finire prima tutte le tappe») — il giro
col SERVER VERO (TestClient, la app vera), il SATS ROUTING DI CARTONE su
una porta di questo computer (rete testnet: le forme tb1…/lntb… del signet
dell'on-chain) e il TELEFONO VERO (i pezzi della pagina e swap/*.js col
bundle) in node.

LE SCENE:
  - il cancello: a leva spenta niente; accesa ma con l'on-chain e il
    fornitore su reti diverse niente lo stesso; con le reti giuste solo a
    chi ha PRESO vendendo (non a chi riceve, non a chi ha pubblicato);
  - il preventivo: quanto pagare perche' al deposito arrivi ALMENO
    l'importo, il costo, l'impronta; troppo vicino alla fine del deposito
    no; il biglietto e i suoi no;
  - il telefono: la scelta nel foglio del deposito, il conto, le parole
    prima, «Crea la richiesta» (biglietto, cambio dal cartone, nascita),
    il QR e il wallet collegato, il ritiro DRITTO all'indirizzo 2-di-3
    con almeno l'importo, la lista;
  - la ronda: UN avviso col bottone dello scambio on-chain;
  - l'annullo: un cambio che ha gia' bloccato i bitcoin ferma l'annullo,
    il fornitore muto pure (503), uno non pagato no;
  - il deposito arrivato: con una conferma lo scambio va avanti come
    sempre;
  - la leva rispenta: niente di nuovo, ma un cambio nato finisce.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco PRIMA dell'import del server; mempool di cartone; nessuna rete
fuori da 127.0.0.1; nessun sats.

USO:  python collaudo_deposito_ln_p2p.py
"""
import asyncio
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


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def pezzi_pagina():
    mini = open(os.path.join(banco.QUI, "miniapp.html"),
                encoding="utf-8").read().replace("\r\n", "\n")

    def tra(firma, fine="\n}\n", fino_a=""):
        i = mini.index(firma)
        if fino_a:
            return mini[i:mini.index(fino_a, i)]
        return mini[i:mini.index(fine, i) + len(fine)]
    return "\n".join([
        tra("function importoBolt11(pr){"), tra("function leggiBolt11(pr){"),
        tra("const SWAP_TESTI = {", fino_a="function linguaSwap(){"),
        tra("function tempoDepositoOnchainP2P(entro, adesso){"),
        tra("function renderDepositoOnchainP2P(){"),
        tra("function battitoFoglioDepositoOnchainP2P(){"),
        # il deposito in Lightning, intero
        tra("const p2pOcDepositoRete = {};",
            fino_a="/* I GESTI SEMPLICI: una POST, un toast, la scheda rifatta.")])


BANCO_TELEFONO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const BUNDLE = fs.readFileSync(D.bundle, 'utf8');
const TELEFONO = D.telefono.map(f => fs.readFileSync(f, 'utf8'));
const fetchVero = globalThis.fetch;
const chiamate = [];
const BASE = D.base;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finche = async (f, ms = 8000) => { const t0 = Date.now(); while (!f() && Date.now() - t0 < ms) await sleep(100); };
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const memoria = new Map();
const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL, URLSearchParams,
  Uint8Array, BigInt, setTimeout, clearTimeout, Promise, JSON, Date, Math,
  fetch: async (url, opz) => {
    chiamate.push({url: String(url), metodo: (opz && opz.method) || 'GET'});
    return fetchVero(url, opz);
  }};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(BUNDLE, ctx);
vm.runInContext(`
let myTgId = 999;
const FOTO_BASE = '';
let swapLeve = ${JSON.stringify(D.leve)};
const swapAcceso = () => !!(swapLeve && swapLeve.attivo);
const elementi = {};
function el(id){
  if (!elementi[id]) elementi[id] = {id, innerHTML: '', textContent: '', href: '', style: {}, value: '',
    classList: {contains: () => true, add(){}, remove(){}}};
  return elementi[id];
}
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const fmt = n => String(n);
function haptic(){}
const avvisi = [];
function toast(m){ avvisi.push(m); }
let currentOrder = null;
function payoutPanel(){ return ''; }
let preventiviSwap = {}, sceltaIncassoSwap = {};
let tg = {initDataUnsafe: {user: {language_code: 'it'}}};
function linguaSwap(){ return 'it'; }
function ridisegnaIncassoSwap(){}
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const document = {addEventListener(){}, head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
const navigator = {};
function onchainSemeLocale(){ return localStorage.getItem('barattolo_onchain_' + myTgId) || ''; }
async function onchainSemeAssicurato(){
  let p = onchainSemeLocale();
  if (p) return p;
  p = BarattoloSwap.generateMnemonic(BarattoloSwap.wordlist);
  localStorage.setItem('barattolo_onchain_' + myTgId, p);
  return p;
}
let paroleCoperte = true;
async function onchainSemeCoperto(){ return paroleCoperte; }
/* LE CHIAMATE AL SERVER DI BARATTOLO, finte e contate (il giro Python le
   rifa' sulla app vera) */
const server = [];
async function chiediBigliettoDepositoP2P(d){ server.push(['biglietto', d]); return {ok: true, id: ${Number(D.biglietto)}}; }
async function natoCambioP2PAlServer(id, rec){ server.push(['nato', id, {swap_id: rec.id, impronta: rec.impronta, indirizzo: rec.lockupAddress, onchain: rec.onchainAmount}]); return {ok: true, stato: 'nato'}; }
async function liberaBigliettoCambioP2P(id){ server.push(['annulla', id]); return {ok: true}; }
async function chiediBigliettoCambioP2P(d){ server.push(['biglietto-t1', d]); return null; }
async function pagaSwapAlServer(rec){ server.push(['paga', rec.ordine]); return null; }
async function statoPagamentoSwap(){ return null; }
async function chiediBigliettoCambio(d){ server.push(['cambio-libero', d]); return null; }
async function natoCambioAlServer(){ return null; }
async function liberaBigliettoCambio(){ return null; }
async function leggiPreventivoSwap(){ return {ok: false, motivo: 'non_risponde'}; }
async function leggiPreventivoCambioP2P(){ return {ok: false, motivo: 'non_risponde'}; }
const preventivi = [];
let preventivoServer = ${JSON.stringify(D.preventivo)};
async function leggiPreventivoDepositoP2P(scambio, fornitore, hash){
  preventivi.push({scambio, fornitore, hash});
  return Object.assign({}, preventivoServer, {cambiata: !!hash && hash !== preventivoServer.hash});
}
const qr = [];
async function disegnaQr(box, testo, modo){ qr.push([box.id, testo, modo]); return true; }
function portaWallet(a, inv){ a.href = 'lightning:' + inv; }
function onchainRete(){ return {prova: true}; }
function onchainUriPagamento(o){ return 'bitcoin:' + o.indirizzo.indirizzo; }
function copiaOnchainP2P(){}
function minutiSecondi(s){ return String(s); }
function bottoneInAttesa(){ return () => {}; }
let walletCollegato = null;
function walletNwcPaga(){ return walletCollegato; }
const pagate = [];
async function clientNwc(w){ return {paga: async inv => { pagate.push(inv); return {}; }}; }
let p2pOcDeposito = null, p2pOcDepositoOrologio = null;
`, Object.assign(ctx, {__memoria: memoria}));
vm.runInContext(D.pagina, ctx);
for (const codice of TELEFONO) vm.runInContext(codice, ctx);
const run = c => vm.runInContext(c, ctx);
const lista = () => JSON.parse(memoria.get('barattolo_swap_lista_999') || '[]');

(async () => {
  const out = {};
  const O = D.oc;
  run(`p2pOcDeposito = ${JSON.stringify(O)}`);
  const corpo = () => run("el('p2pOcDepositoCorpo').innerHTML");
  /* il foglio come si apre: la scelta, e il lato on-chain di sempre */
  run('renderDepositoOnchainP2P()');
  const c0 = corpo();
  out.apre = {scelta: c0.includes("scegliReteDepositoOnchainP2P(" + O.id + ", 'ln')") && c0.includes('⚡ Lightning'),
              ocPremuto: c0.includes('aria-pressed="true" onclick="scegliReteDepositoOnchainP2P(' + O.id + ", 'oc')"),
              onchain: c0.includes('Manda <b>' + O.importo_sats + ' sats</b>')};
  /* chi non puo' (chi ha pubblicato, o la leva spenta): niente scelta */
  run(`p2pOcDeposito = ${JSON.stringify(Object.assign({}, O, {deposito_ln_possibile: false}))}; renderDepositoOnchainP2P()`);
  out.senzaScelta = !corpo().includes('scegliReteDepositoOnchainP2P');
  run(`p2pOcDeposito = ${JSON.stringify(O)}`);
  /* «⚡ Lightning»: prima «Chiedo il prezzo», poi il conto */
  run(`scegliReteDepositoOnchainP2P(${O.id}, 'ln')`);
  out.chiedo = corpo().includes('Chiedo il prezzo del cambio');
  await finche(() => run(`(p2pOcDepositoLn[${O.id}] || {}).stato`) === 'pronto');
  run('renderDepositoOnchainP2P()');
  out.conto = corpo();
  out.preventivoChiesto = run('preventivi.slice()');
  /* le parole senza copia: prima il Profilo, e non nasce niente */
  run('paroleCoperte = false; swapParoleCoperte = ""');
  await run(`creaDepositoLnOnchainP2P({}, ${O.id})`);
  out.paroleNo = [corpo().includes('Prima di usare il cambio guarda le tue 12 parole'), run('server.length'), lista().length];
  run('paroleCoperte = true');
  /* l'indirizzo del foglio diverso da quello del preventivo: no */
  run(`p2pOcDeposito = ${JSON.stringify(Object.assign({}, O, {indirizzo: {indirizzo: D.altro}}))}`);
  await run(`creaDepositoLnOnchainP2P({}, ${O.id})`);
  out.indirizzoNo = [corpo().includes("L'indirizzo del deposito non torna"), run('server.length'), lista().length];
  run(`p2pOcDeposito = ${JSON.stringify(O)}`);
  /* «Crea la richiesta Lightning» */
  const v0 = (await (await fetchVero(BASE + '/cartone/visto')).json()).swap;
  await run(`creaDepositoLnOnchainP2P({}, ${O.id})`);
  const rec = lista().find(r => r.p2pDeposito === O.id) || {};
  out.nato = {ordini: run('server.map(s => s[0])'), biglietto: run('server[0] && server[0][1]'),
              swap: (await (await fetchVero(BASE + '/cartone/visto')).json()).swap - v0,
              record: {p2pDeposito: rec.p2pDeposito, ordine: rec.ordine === undefined ? 'nessuno' : rec.ordine,
                       p2p: rec.p2p === undefined ? 'nessuno' : rec.p2p, indirizzo: rec.indirizzo,
                       seme: rec.seme, biglietto: rec.biglietto, pagamento: rec.pagamento, tipo: rec.tipo || 'reverse'},
              ricevi: rec.ricevi, fattura: rec.invoice ? run('leggiBolt11(' + JSON.stringify(rec.invoice) + ').sats') : 0,
              natoPubblico: run('server[1] && server[1][2]'),
              diDeposito: run(`swapDiDepositoP2P(${O.id}) && swapDiDepositoP2P(${O.id}).id`) === rec.id,
              cambioLibero: run('swapDiOrdine(0)'), ordine0: run(`swapECambio(swapDiDepositoP2P(${O.id}))`),
              diP2P: run(`swapDiP2P(${JSON.stringify('oc:' + O.id)})`)};
  out.swapId = rec.id || '';
  /* il foglio adesso: la frase, il QR della richiesta, «Apri nel wallet», niente wallet collegato */
  run('renderDepositoOnchainP2P()');
  const c1 = corpo();
  out.foglio = {frase: c1.includes('Paga questa richiesta dal tuo wallet Lightning: SATS Routing prepara i bitcoin'),
                qr: run('qr.slice(-1)[0]'), richiesta: c1.includes(rec.invoice || 'x'),
                wallet: run("el('p2pOcDepositoLnWallet').href") === 'lightning:' + rec.invoice,
                collegato: c1.includes('Paga col wallet collegato'), copia: c1.includes('copiaDepositoLnOnchainP2P(' + O.id + ')')};
  /* col wallet collegato: il tasto c'e', e paga LA richiesta del cambio */
  run('walletCollegato = {uri: "nostr+walletconnect://x"}; renderDepositoOnchainP2P()');
  out.collegato = corpo().includes('Paga col wallet collegato');
  await run(`pagaDepositoLnOnchainP2P({}, ${O.id})`);
  out.pagata = run('pagate.slice()');
  /* un secondo «Crea»: niente cambio nuovo, il foglio resta sul primo */
  await run(`creaDepositoLnOnchainP2P({}, ${O.id})`);
  out.riuso = {biglietti: run('server.filter(s => s[0] === "biglietto").length'), swap: lista().length};
  /* tornato all'on-chain con la richiesta aperta: l'avvertenza */
  run(`scegliReteDepositoOnchainP2P(${O.id}, 'oc')`);
  out.avverte = corpo().includes('Hai una richiesta Lightning aperta per questo deposito');
  run(`scegliReteDepositoOnchainP2P(${O.id}, 'ln')`);
  /* pagata: il cartone blocca i bitcoin, la sorveglianza ritira nel deposito */
  await stato(out.swapId, 'transaction.mempool');
  await run('swapGiro()');
  const quello = () => lista().find(r => r.id === out.swapId) || {};
  await finche(() => (quello().ritiro || {}).txid || quello().errore);
  const dopo = quello();
  out.ritiro = {txid: (dopo.ritiro || {}).txid || '', errore: dopo.errore || '',
                frase: run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(out.swapId) + '))')};
  const visto = await (await fetchVero(BASE + '/cartone/visto')).json();
  out.trasmessa = (visto.trasmesse || []).filter(t => t.swap === out.swapId).pop() || null;
  run('renderDepositoOnchainP2P()');
  out.foglioDopo = corpo();
  /* nella lista della pagina «Cambio» si chiama «Scambio P2P» */
  run("elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}; elementi.swapCambio = {innerHTML: ''};");
  run('renderSwapTelefono()');
  out.lista = run('elementi.swapTelefono.innerHTML').includes('<b>Scambio P2P</b>');
  out.sentinella = {paga: run('server.filter(s => s[0] === "paga").length'),
                    libero: run('server.filter(s => s[0] === "cambio-libero" || s[0] === "biglietto-t1").length'),
                    fuori: chiamate.filter(c => !c.url.startsWith(BASE)).map(c => c.url)};
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def telefono(base, oc, prev, biglietto, altro):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="deposito_ln_p2p_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "oc": oc, "preventivo": prev, "biglietto": biglietto,
            "altro": altro,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "testnet",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000,
                     "mempool": base + "/esplora",
                     "fornitori": [{"id": "satsrouting", "nome": "SATS Routing",
                                    "tipo": "boltz", "api": base,
                                    "referral": "barattolo", "rete": "testnet",
                                    "mempool": base + "/esplora"}],
                     "cambio": {"attivo": False, "minimo": 25_000, "massimo": 500_000,
                                "al_giorno": 5, "oggi": 0, "strade": ["ln-btc"]},
                     "p2p": {"attivo": True, "minimo": 25_000, "massimo": 500_000}}}))
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
    print("  🔒 P2P ON-CHAIN: CHI VENDE PAGA IL DEPOSITO IN LIGHTNING")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import httpx
    from embit import bip32, bip39, script
    from embit.ec import PrivateKey
    from embit.networks import NETWORKS
    from fastapi.testclient import TestClient
    SRV.httpx = httpx           # il cartone e' vero, su 127.0.0.1
    _, PORTA = cartone_satsrouting.avvia(0, rete="testnet")
    base = f"http://127.0.0.1:{PORTA}"
    c = TestClient(SRV.app)
    N = NETWORKS["signet"]
    vett = json.load(open(os.path.join(banco.QUI, "vendor",
                                       "vettori-bip.json"), encoding="utf-8"))
    semi = {999: vett["bip39_english"][0]["parole"],
            888: vett["bip39_english"][1]["parole"]}

    def conto(tg):
        return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[tg]),
                                     version=N["xprv"]).derive(
            "m/48h/1h/0h/2h").to_public().to_string(version=N["xpub"])

    MONETE = {}

    async def utxo_finte(indirizzo):
        return list(MONETE.get(indirizzo, []))

    async def tariffa_finta():
        return 2.0
    SRV.onchain_mempool_utxo = utxo_finte
    SRV.onchain_mempool_tariffa = tariffa_finta

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
    SRV.SWAP_FEE_PERCENTO = 0.5       # accesa: qui non deve contare
    SRV.SWAP_API_BASE = base
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.SWAP_RETE = "bitcoin"
    SRV.CAMBIO_BTC_LN_ATTIVO = False  # l'altra strada: qui non serve
    SRV.P2P_ALTRA_RETE_ATTIVO = False
    SRV.P2P_ALTRA_RETE_SOLO_MODERATORI = True
    SRV.P2P_ALTRA_RETE_MAX_SATS = 500_000
    for nome in ("p2p_onchain_pubblica", "p2p_onchain_prendi",
                 "p2p_onchain_controlla", "onchain_cambio"):
        SRV.FRENI[nome] = (1000, 3600)

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def uno(tg, oid):
        come(tg)
        return c.get(f"/api/p2p/onchain/{oid}").json()

    def gesto(tg, oid, cosa, **d):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/{cosa}", json=d)

    def preventivo(tg, oid, **q):
        come(tg)
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        return c.get(f"/api/p2p/onchain/{oid}/deposito-ln/preventivo?{qs}")

    def biglietto(tg, oid, sats, **extra):
        come(tg)
        return c.post(f"/api/p2p/onchain/{oid}/deposito-ln",
                      json=dict({"sats": sats, "fornitore": "satsrouting"}, **extra))

    def nato(tg, cid, corpo):
        come(tg)
        return c.post(f"/api/swap/p2p/{cid}/nato", json=corpo)

    def scambio(prende_chi_vende=True):
        """Alan vuole comprare 100.000 sats e Andrea li vende prendendo
        l'ordine (il caso della tappa 3); o il contrario: Andrea pubblica
        la vendita e Alan prende comprando."""
        if prende_chi_vende:
            come(888)
            o = c.post("/api/p2p/onchain/pubblica", json={
                "lato": "buy", "sats": 100000, "euro_cent": 9000,
                "metodi": ["Bonifico"]}).json()
            gesto(999, o["id"], "prendi", recapito="IT00 X 1234")
        else:
            come(999)
            o = c.post("/api/p2p/onchain/pubblica", json={
                "lato": "sell", "sats": 100000, "euro_cent": 9000,
                "metodi": ["Bonifico"], "recapito": "IT00 X 1234"}).json()
            gesto(888, o["id"], "prendi")
        return o["id"]

    for tg in (999, 888):
        come(tg)
        c.post("/api/onchain/xpub", json={"xpub": conto(tg)})

    # ---- 1) il cancello ----------------------------------------------------
    print("\n[il cancello: la leva, le reti, chi ha preso vendendo]")
    oid = scambio()
    o = uno(999, oid)
    prova("preso: chi deve depositare e' chi ha preso (Andrea), a leva spenta niente "
          "Lightning", ("preso", "compratore", False),
          (o["stato"], o["ruolo"], o["deposito_ln_possibile"]))
    prova("a leva spenta il preventivo e il biglietto sono 403", (403, 403),
          (preventivo(999, oid).status_code, biglietto(999, oid, 120_000).status_code))
    SRV.P2P_ALTRA_RETE_ATTIVO = True
    prova("leva accesa, ma l'on-chain sta su signet e il fornitore su bitcoin: chiusa "
          "lo stesso", (False, 403),
          (uno(999, oid)["deposito_ln_possibile"], preventivo(999, oid).status_code))
    SRV.SWAP_RETE = "testnet"
    prova("con le reti giuste si apre, ma solo a chi deposita (non a chi riceve), e "
          "senza la strada bitcoin → Lightning", (True, False),
          (uno(999, oid)["deposito_ln_possibile"], uno(888, oid)["deposito_ln_possibile"]))
    prova("chi riceve non chiede il preventivo del deposito: 403", 403,
          preventivo(888, oid).status_code)
    oid_m = scambio(prende_chi_vende=False)
    prova("chi ha PUBBLICATO la vendita on-chain deposita on-chain: niente scelta, 409",
          (False, 409, True),
          (uno(999, oid_m)["deposito_ln_possibile"], preventivo(999, oid_m).status_code,
           "deposito si fa on-chain" in preventivo(999, oid_m).json().get("detail", "")))

    # ---- 2) il preventivo e il biglietto ----------------------------------
    print("\n[il preventivo: almeno l'importo nel deposito, senza la nostra fee]")
    p = preventivo(999, oid).json()
    importo = o["importo_sats"]
    prova("ok, con l'indirizzo del deposito e l'importo dello scambio",
          (True, o["indirizzo"]["indirizzo"], importo, "SATS Routing"),
          (p.get("ok"), p.get("indirizzo"), p.get("importo"), p.get("fornitore_nome")))
    prova("...al deposito arriva ALMENO l'importo, e al piu' un paio di sats in piu'",
          True, importo <= p.get("ricevi", 0) <= importo + 2)
    prova("...paghi = la fattura del cambio, costo = quel che paghi oltre l'importo",
          (p.get("fattura"), p.get("fattura", 0) - importo, True),
          (p.get("paghi"), p.get("costo"), 0 < p.get("costo", 0) < 3000))
    prova("...nelle righe c'e' solo il cambio: la nostra fee (accesa) qui non c'e'",
          ["commissione", "dovuto", "rete_invio", "rete_ritiro"],
          sorted(r["voce"] for r in p.get("righe") or []))
    prova("...con l'impronta di ieri dice «cambiata»", True,
          preventivo(999, oid, hash="vecchia").json().get("cambiata"))
    SRV.P2P_ALTRA_RETE_MAX_SATS = 50_000
    prova("sopra il massimo della leva: no, col perche'", (False, "sopra_tetto"),
          (preventivo(999, oid).json().get("ok"), preventivo(999, oid).json().get("motivo")))
    SRV.P2P_ALTRA_RETE_MAX_SATS = 500_000

    print("\n[il biglietto]")
    prova("una cifra che non supera l'importo (il cambio costa): «cifra»",
          {"ok": False, "motivo": "cifra"}, biglietto(999, oid, importo).json())
    prova("sopra il massimo / fornitore sconosciuto", ["sopra_tetto", "fornitore"],
          [biglietto(999, oid, 600_000).json().get("motivo"),
           biglietto(999, oid, p["fattura"], fornitore="nessuno").json().get("motivo")])
    prova("chi riceve non chiede il biglietto: 403", 403,
          biglietto(888, oid, p["fattura"]).status_code)
    ids = [biglietto(999, oid, p["fattura"]).json().get("id") for _ in range(3)]
    prova("tre biglietti vivi sullo stesso scambio, il quarto «troppi»",
          (True, {"ok": False, "motivo": "troppi"}),
          (all(isinstance(i, int) and i > 0 for i in ids), biglietto(999, oid, p["fattura"]).json()))
    con = SRV.db()
    r = con.execute("SELECT ordine, sats, tg_id FROM cambi_p2p WHERE id=?", (ids[0],)).fetchone()
    con.close()
    prova("...scritti come «oc:<numero>», che nessuno scambio di Mostro puo' avere",
          (f"oc:{oid}", p["fattura"], 999), tuple(r))
    for i in ids:
        come(999)
        c.post(f"/api/swap/p2p/{i}/annulla")
    prova("l'annullo della tappa 1 li libera", True,
          biglietto(999, oid, p["fattura"]).json().get("ok"))
    con = SRV.db()
    con.execute("UPDATE cambi_p2p SET stato='annullato' WHERE ordine=?", (f"oc:{oid}",))
    vecchio = con.execute("SELECT deposito_entro FROM p2p_onchain_ordini WHERE id=?",
                          (oid,)).fetchone()[0]
    con.execute("UPDATE p2p_onchain_ordini SET deposito_entro=? WHERE id=?",
                (int(time.time()) + 600, oid))
    con.commit()
    r = preventivo(999, oid)
    prova("a dieci minuti dalla fine del deposito: 409, deposita on-chain",
          (409, True, False), (r.status_code, "deposita on-chain" in r.json().get("detail", ""),
                               uno(999, oid)["deposito_ln_possibile"] is False))
    con.execute("UPDATE p2p_onchain_ordini SET deposito_entro=? WHERE id=?", (vecchio, oid))
    con.commit()
    con.close()

    # ---- 3) il telefono ---------------------------------------------------
    print("\n[il telefono: la scelta, il conto, «Crea la richiesta», il ritiro nel deposito]")
    o = uno(999, oid)
    p = preventivo(999, oid).json()
    b = biglietto(999, oid, p["fattura"]).json()
    altro = script.p2wpkh(bip32.HDKey.from_seed(bip39.mnemonic_to_seed(semi[888]),
                                                version=N["xprv"]).derive(
        "m/84h/1h/0h/0/3").key.get_public_key()).address(N)
    t = telefono(base, o, p, b["id"], altro)
    if "ERRORE" in t:
        prova("il banco del telefono gira", "", t["ERRORE"])
        return 1
    prova("il foglio del deposito si apre con la scelta, sul lato on-chain di sempre",
          {"scelta": True, "ocPremuto": True, "onchain": True}, t["apre"])
    prova("...chi non puo' non vede la scelta", True, t["senzaScelta"])
    cc = t["conto"]
    prova("«⚡ Lightning»: prima «Chiedo il prezzo», poi il conto — quanto paghi, quanto "
          "arriva al deposito, il costo, il ritorno ON-CHAIN, «Crea la richiesta»",
          (True, True, True, True, True, True),
          (t["chiedo"],
           f"Paghi <b>{p['paghi']} sats</b> dal tuo wallet Lightning" in cc,
           f"mette <b>{p['ricevi']} sats</b> nel deposito di garanzia (ne servono {importo})" in cc,
           f"costa <b>{p['costo']} sats</b>, li paghi tu. Barattolo non aggiunge niente" in cc,
           "i bitcoin tornano <b>on-chain</b> al tuo wallet di Barattolo, non in Lightning" in cc,
           f"creaDepositoLnOnchainP2P(this, {oid})" in cc))
    prova("...dal preventivo dello scambio", [{"scambio": oid, "fornitore": "", "hash": ""}],
          t["preventivoChiesto"][:1])
    prova("le 12 parole senza copia: prima il Profilo, e non nasce niente",
          [True, 0, 0], t["paroleNo"])
    prova("un indirizzo che non e' quello del preventivo: no, e non nasce niente",
          [True, 0, 0], t["indirizzoNo"])
    n = t["nato"]
    prova("«Crea»: PRIMA il biglietto (lo scambio, la cifra della fattura), poi UN cambio "
          "al cartone, poi la nascita",
          (["biglietto", "nato"], {"scambio": oid, "sats": p["fattura"], "fornitore": "satsrouting"}, 1),
          (n["ordini"], n["biglietto"], n["swap"]))
    prova("...il record e' del deposito: non un ordine, non uno scambio di Mostro; il "
          "ritiro va all'indirizzo 2-di-3, chiave dal wallet di Barattolo",
          {"p2pDeposito": oid, "ordine": "nessuno", "p2p": "nessuno",
           "indirizzo": o["indirizzo"]["indirizzo"], "seme": "onchain",
           "biglietto": b["id"], "pagamento": "", "tipo": "reverse"}, n["record"])
    prova("...la fattura porta quel che dice il preventivo, il ritiro almeno l'importo",
          (p["fattura"], True), (n["fattura"], n["ricevi"] >= importo))
    prova("...la nascita al server: le sole parti pubbliche", True,
          bool(n["natoPubblico"]) and set(n["natoPubblico"]) == {"swap_id", "impronta", "indirizzo", "onchain"})
    prova("...`swapDiDepositoP2P` lo ritrova; non e' il cambio libero, ne' l'«ordine 0», "
          "ne' un cambio della tappa 1", (True, None, False, None),
          (n["diDeposito"], n["cambioLibero"], n["ordine0"], n["diP2P"]))
    f = t["foglio"]
    prova("il foglio: la frase, il QR della richiesta (lightning:), la stringa, «Apri nel "
          "wallet», «Copia»; senza wallet collegato niente tasto",
          (True, "p2pOcDepositoLnQr", True, True, True, False),
          (f["frase"], (f["qr"] or [""])[0], f["richiesta"], f["wallet"], f["copia"], f["collegato"]))
    prova("...col wallet collegato il tasto c'e', e paga LA richiesta del cambio",
          (True, 1), (t["collegato"], len(t["pagata"])))
    prova("un secondo «Crea»: nessun biglietto nuovo, nessun cambio nuovo",
          {"biglietti": 1, "swap": 1}, t["riuso"])
    prova("tornato all'on-chain con la richiesta aperta: «non pagarla»", True, t["avverte"])
    rt = t["ritiro"]
    prova("pagata: il cartone blocca i bitcoin, la sorveglianza li ritira", (True, ""),
          (len(rt["txid"]) == 64, rt["errore"]))
    tr = t["trasmessa"] or {}
    spk = script.address_to_scriptpubkey(o["indirizzo"]["indirizzo"]).data.hex()
    usc = tr.get("uscite") or []
    prova("...il ritiro ha UNA uscita, DRITTA all'indirizzo 2-di-3, con almeno l'importo",
          (1, spk, True), (len(usc), usc[0]["script"] if usc else "",
                           bool(usc) and usc[0]["sats"] >= importo))
    prova("...e la frase dice che i bitcoin vanno al deposito", True,
          rt["frase"].startswith("Partiti verso il deposito di garanzia") or
          rt["frase"].startswith("Fatto: i bitcoin sono nel deposito"))
    prova("...il foglio non mostra piu' la richiesta", False,
          "p2pOcDepositoLnQr" in t["foglioDopo"])
    prova("nella lista della pagina «Cambio» si chiama «Scambio P2P»", True, t["lista"])
    prova("la sentinella: Barattolo non paga, il cambio libero e la tappa 1 non si "
          "toccano, il telefono parla solo col cartone",
          {"paga": 0, "libero": 0, "fuori": []}, t["sentinella"])

    # ---- 4) la ronda e l'annullo -------------------------------------------
    print("\n[la ronda dell'avviso e l'annullo con un cambio in volo]")
    swap_id = t.get("swapId") or ""
    prova("la nascita sul server vero", (200, {"ok": True, "stato": "nato"}),
          (lambda r: (r.status_code, r.json()))(nato(999, b["id"], {
              "swap_id": swap_id, "impronta": "cd" * 32, "indirizzo": "tb1pcartone",
              "onchain": n["ricevi"]})))
    avvisi = []

    async def notifica_finta(tg_id, testo, bottone=None):
        avvisi.append((tg_id, testo, bottone))
        return "telegram"
    vera = SRV.notifica
    SRV.notifica = notifica_finta
    try:
        cartone(f"/cartone/stato?id={swap_id}&s=transaction.mempool")
        prova("bitcoin bloccati: UN avviso", 1, asyncio.run(SRV.ronda_cambi_p2p()))
        tg, testo, bott = avvisi[-1] if avvisi else (0, "", None)
        prova("...a chi deposita, con le parole del deposito e il bottone sullo "
              "scambio on-chain",
              (999, True, True, (SRV.P2P_BOTTONE_DEPOSITO_LN,
                                 f"{SRV.LINK_LIBRO_P2P}?scambio={o['ordine']}")),
              (tg, testo.startswith("🔒 Il cambio del tuo deposito è pronto"),
               "mette i bitcoin nel deposito di garanzia" in testo, bott))
        r = gesto(999, oid, "annulla")
        prova("chi deposita non annulla mentre il cambio porta i bitcoin: 409", (409, True),
              (r.status_code, "sta portando i bitcoin nel deposito" in r.json().get("detail", "")))
        cartone("/cartone/modo?m=giu")
        r = gesto(999, oid, "annulla")
        prova("...e col fornitore muto non annulla alla cieca: 503", 503, r.status_code)
        cartone("/cartone/modo?m=normale")
        cartone(f"/cartone/stato?id={swap_id}&s=invoice.settled")
        asyncio.run(SRV.ronda_cambi_p2p())
        prova("in tutto un avviso solo, e la riga si chiude", (1, "finito"),
              (len(avvisi), SRV.db().execute("SELECT stato FROM cambi_p2p WHERE id=?",
                                             (b["id"],)).fetchone()[0]))
    finally:
        SRV.notifica = vera

    # ---- 5) il deposito arrivato ------------------------------------------
    print("\n[il deposito arrivato: lo scambio va avanti come sempre]")
    MONETE[o["indirizzo"]["indirizzo"]] = [{
        "txid": rt["txid"], "vout": 0, "value": usc[0]["sats"] if usc else 0,
        "status": {"confirmed": True}}]
    gesto(999, oid, "controlla")
    oo = uno(888, oid)
    prova("con una conferma: depositato, e chi compra lo sa", ("depositato", True, False),
          (oo["stato"], oo["ricevuti_sats"] >= importo, uno(999, oid)["deposito_ln_possibile"]))
    prova("...e il preventivo del deposito non c'e' piu': 409", 409,
          preventivo(999, oid).status_code)

    print("\n[l'annullo con un cambio non pagato, e la leva rispenta]")
    oid2 = scambio()
    p2 = preventivo(999, oid2).json()
    b2 = biglietto(999, oid2, p2["fattura"]).json()
    corpo = {"from": "BTC", "to": "BTC", "invoiceAmount": p2["fattura"],
             "preimageHash": secrets.token_hex(32), "claimPublicKey": PrivateKey(secrets.token_bytes(32)).get_public_key().sec().hex(),
             "pairHash": p2["hash"]}
    req = urllib.request.Request(f"{base}/v2/swap/reverse", data=json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as rr:
        sw = json.loads(rr.read().decode("utf-8"))
    nato(999, b2["id"], {"swap_id": sw["id"], "impronta": corpo["preimageHash"],
                         "indirizzo": sw["lockupAddress"], "onchain": sw["onchainAmount"]})
    SRV.P2P_ALTRA_RETE_ATTIVO = False
    prova("a leva spenta: niente scelta, 403 al preventivo", (False, 403),
          (uno(999, oid2)["deposito_ln_possibile"], preventivo(999, oid2).status_code))
    prova("...ma un cambio nato e non pagato non ferma l'annullo di chi deposita", 200,
          gesto(999, oid2, "annulla").status_code)
    prova("lo scambio e' annullato", "annullato", uno(999, oid2)["stato"])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
