# -*- coding: utf-8 -*-
"""
VENDERE SU UN ORDINE P2P LIGHTNING AVENDO SOLO BITCOIN (1 nov 2026,
cantiere presa-altra-rete, caso 4; studio del 30 ott §9-12, la risposta di
Massimo del 1 nov) — il giro col SERVER VERO (TestClient, la app vera), il
SATS ROUTING DI CARTONE su una porta di questo computer (rete testnet) e il
TELEFONO VERO (i pezzi della pagina e swap/*.js col bundle) in node.

LE SCENE:
  - il cancello: la leva della presa sull'altra rete E la strada bitcoin →
    Lightning del Cambio, solo moderatori; `swap_leve.p2p.presa` lo dice
    alla pagina;
  - il preventivo: quanti bitcoin mandare perche' nel SUO wallet arrivino
    i sats della garanzia, il costo, i tetti;
  - il biglietto: la forma dell'ordine, i tetti, i troppi;
  - il telefono: il riquadro nella pagina dell'ordine, il conto, la
    richiesta incollata (o chiesta al wallet collegato), «Crea il cambio»
    (biglietto, submarine dal cartone, nascita), il QR del link bitcoin:,
    niente doppioni, la richiesta sbagliata respinta, il cambio riuscito
    che dice di toccare «Vendi», la lista;
  - la ronda: richiesta pagata → UN avviso «Prendi l'ordine»; fallito coi
    bitcoin mandati → UN avviso «Riprenditi i bitcoin»; scaduto senza
    bitcoin → niente;
  - la leva rispenta: niente di nuovo, ma un cambio nato finisce.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco PRIMA dell'import del server; nessuna rete fuori da 127.0.0.1;
nessun sats.

USO:  python collaudo_presa_ln_p2p.py
"""
import asyncio
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import urllib.request

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
PORTA = 0
ORDINE = "a1b2c3d4-e5f6-4711-8899-aabbccddeeff"


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def fattura(sats):
    """Una richiesta «del wallet Lightning dell'utente», fatta dal cartone."""
    pre = secrets.token_bytes(32)
    imp = hashlib.sha256(pre).hexdigest()
    inv = cartone_satsrouting.cripto("fattura", rete="testnet", sats=sats,
                                     impronta=imp)["invoice"]
    return {"invoice": inv, "preimage": pre.hex(), "impronta": imp}


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
        # il cambio prima della presa, intero
        tra("const p2pPresaOc = {};",
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
const VETRINA = false;
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
async function onchainSemeCoperto(){ return true; }
/* LE CHIAMATE AL SERVER DI BARATTOLO, finte e contate (il giro Python le
   rifa' sulla app vera) */
const server = [];
async function chiediBigliettoPresaP2P(d){ server.push(['biglietto', d]); return {ok: true, id: ${Number(D.biglietto)}}; }
async function natoCambioP2PAlServer(id, rec){ server.push(['nato', id, {swap_id: rec.id, impronta: rec.impronta, indirizzo: rec.lockupAddress, onchain: rec.onchainAmount}]); return {ok: true, stato: 'nato'}; }
async function liberaBigliettoCambioP2P(id){ server.push(['annulla', id]); return {ok: true}; }
async function chiediBigliettoCambioP2P(d){ server.push(['biglietto-t1', d]); return null; }
async function chiediBigliettoDepositoP2P(d){ server.push(['biglietto-t3', d]); return null; }
async function pagaSwapAlServer(rec){ server.push(['paga', rec.ordine]); return null; }
async function statoPagamentoSwap(){ return null; }
async function chiediBigliettoCambio(d){ server.push(['cambio-libero', d]); return null; }
async function natoCambioAlServer(){ return null; }
async function liberaBigliettoCambio(){ return null; }
async function leggiPreventivoSwap(){ return {ok: false, motivo: 'non_risponde'}; }
const preventivi = [];
let preventivoServer = ${JSON.stringify(D.preventivo)};
async function leggiPreventivoPresaP2P(sats, fornitore, hash){
  preventivi.push({sats, fornitore, hash});
  return Object.assign({}, preventivoServer, {cambiata: !!hash && hash !== preventivoServer.hash});
}
const qr = [];
async function disegnaQr(box, testo, modo){ qr.push([box.id, testo, modo]); return true; }
function copiaOnchainP2P(){}
function bottoneInAttesa(){ return () => {}; }
function vaiSwap(){}
/* la pagina dell'ordine: la riga del libro, la fee, il cambio */
const cambioVivo = true, eurPerSat = 0.001;
let p2pLibro = {ordini: [${JSON.stringify(D.riga)}]};
let p2pDettOrdine = ${JSON.stringify(D.riga.id)}, p2pDettImporto = 0;
function rigaLibroP2P(id){ return p2pLibro.ordini.find(x => x.id === id) || null; }
function feeMiaP2P(){ return 0.01; }
function satsMercatoP2P(o){ return Math.round(o.euro / eurPerSat * (1 - o.premium / 100)); }
function renderDettaglioP2P(){ el('p2pDettCorpo').innerHTML = rigaPresaOcP2P(rigaLibroP2P(p2pDettOrdine)); qrPresaOcP2P(p2pDettOrdine); }
const P2P_NWC_ATTESA_MS = 2000;
let walletCollegato = null;
function walletNwcFattura(){ return walletCollegato; }
const chieste = [];
let fatturaDelWallet = '';
async function clientNwc(w){ return {fattura: async (sats, desc, sec) => { chieste.push([sats, desc, sec]); return {invoice: fatturaDelWallet}; }, chiudi(){ chieste.push('chiuso'); }}; }
`, Object.assign(ctx, {__memoria: memoria}));
vm.runInContext(D.pagina, ctx);
for (const codice of TELEFONO) vm.runInContext(codice, ctx);
const run = c => vm.runInContext(c, ctx);
const lista = () => JSON.parse(memoria.get('barattolo_swap_lista_999') || '[]');

(async () => {
  const out = {};
  const ID = D.riga.id;
  const corpo = () => { run('renderDettaglioP2P()'); return run("el('p2pDettCorpo').innerHTML"); };
  /* chiuso: la domanda e il tasto */
  const c0 = corpo();
  out.chiuso = c0.includes('Hai solo bitcoin on-chain?') && c0.includes('Caricali in Lightning');
  /* la garanzia: la cifra fissa piu' meta' della commissione */
  out.garanzia = run(`garanziaVendoP2P(rigaLibroP2P(${JSON.stringify(ID)}))`);
  out.garanziaRange = run(`garanziaVendoP2P(Object.assign({}, rigaLibroP2P(${JSON.stringify(ID)}), {euroMax: 200}))`);
  out.garanziaMercato = run(`garanziaVendoP2P({id: 'x', sats: 0, euro: 90, premium: 0})`);
  /* aperto: il preventivo per quei sats, e il conto */
  await run(`apriPresaOcP2P(${JSON.stringify(ID)})`);
  out.preventivoChiesto = run('preventivi.slice()');
  const c1 = corpo();
  out.conto = {servono: c1.includes('ti servono <b>' + out.garanzia.sats + ' sats</b>'),
               mandi: c1.includes('Mandi <b>' + D.preventivo.mandi + ' sats</b> on-chain'),
               costo: c1.includes('costa ' + D.preventivo.costo + ' sats'),
               campo: c1.includes('id="p2pPresaOcFattura"'),
               tasto: c1.includes('creaPresaOcP2P(this, ')};
  /* una richiesta della cifra sbagliata: no, e non nasce niente */
  run(`el('p2pPresaOcFattura').value = ${JSON.stringify(D.sbagliata)}`);
  await run(`creaPresaOcP2P({}, ${JSON.stringify(ID)})`);
  out.sbagliata = [corpo().includes('role="alert"'), run('server.length'), lista().length];
  /* la richiesta giusta, incollata: «Crea il cambio» */
  const v0 = (await (await fetchVero(BASE + '/cartone/visto')).json()).swap;
  run(`el('p2pPresaOcFattura').value = ${JSON.stringify(D.buona)}`);
  await run(`creaPresaOcP2P({}, ${JSON.stringify(ID)})`);
  const rec = lista().find(r => r.p2pPresa === ID) || {};
  out.nato = {ordini: run('server.map(s => s[0])'), biglietto: run('server[0] && server[0][1]'),
              swap: (await (await fetchVero(BASE + '/cartone/visto')).json()).swap - v0,
              record: {p2pPresa: rec.p2pPresa, tipo: rec.tipo, indirizzo: rec.indirizzo, seme: rec.seme,
                       biglietto: rec.biglietto, ordine: rec.ordine === undefined ? 'nessuno' : rec.ordine,
                       p2p: rec.p2p === undefined ? 'nessuno' : rec.p2p},
              mandi: rec.mandi, ricevi: rec.ricevi,
              natoPubblico: run('server[1] && server[1][2]'),
              diPresa: run(`(swapDiPresaP2P(${JSON.stringify(ID)}) || {}).id`) === rec.id,
              cambioLibero: run('swapDiOrdine(0)'), ordine0: run(`swapECambio(swapDiPresaP2P(${JSON.stringify(ID)}))`)};
  out.swapId = rec.id || '';
  out.lockup = rec.lockupAddress || '';
  /* il riquadro adesso: la frase, il QR del link bitcoin:, l'indirizzo */
  const c2 = corpo();
  out.riquadro = {manda: c2.includes('Manda esattamente ' + rec.mandi + ' sats'),
                  qr: run('qr.slice(-1)[0]'), indirizzo: c2.includes(rec.lockupAddress || 'x'),
                  apri: c2.includes('₿ Apri nel wallet'), avvisa: c2.includes('ti avvisiamo col bot')};
  /* un secondo «Crea»: niente cambio nuovo */
  await run(`creaPresaOcP2P({}, ${JSON.stringify(ID)})`);
  out.riuso = {biglietti: run('server.filter(s => s[0] === "biglietto").length'), swap: lista().length};
  /* i bitcoin arrivati e la richiesta pagata: il riquadro dice «Vendi» */
  await stato(out.swapId, 'transaction.claimed');
  await run('swapGiro()');
  await finche(() => run(`swapFase(swapDiPresaP2P(${JSON.stringify(ID)}))`) === 'fatto');
  out.fase = run(`swapFase(swapDiPresaP2P(${JSON.stringify(ID)}))`);
  out.riuscito = corpo().includes('I sats sono nel tuo wallet Lightning');
  /* nella lista della pagina «Cambio» si chiama «Scambio P2P» */
  run("elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}; elementi.swapCambio = {innerHTML: ''};");
  run('renderSwapTelefono()');
  out.lista = run('elementi.swapTelefono.innerHTML').includes('<b>Scambio P2P</b>');
  /* un altro ordine, col wallet collegato: la richiesta la chiede il telefono */
  const ID2 = ID.replace(/^a/, 'b');
  run(`p2pLibro.ordini.push(Object.assign({}, rigaLibroP2P(${JSON.stringify(ID)}), {id: ${JSON.stringify(ID2)}})); p2pDettOrdine = ${JSON.stringify(ID2)}`);
  run(`walletCollegato = {uri: 'nostr+walletconnect://x', metodi: ['make_invoice']}; fatturaDelWallet = ${JSON.stringify(D.buona2)}`);
  await run(`apriPresaOcP2P(${JSON.stringify(ID2)})`);
  const c3 = corpo();
  out.collegato = {frase: c3.includes('La richiesta la chiedo al tuo wallet collegato'), campo: c3.includes('id="p2pPresaOcFattura"')};
  await run(`creaPresaOcP2P({}, ${JSON.stringify(ID2)})`);
  out.chieste = run('chieste.slice()');
  out.nato2 = !!(lista().find(r => r.p2pPresa === ID2) || {}).id;
  /* il wallet collegato che non da' la richiesta: si dice, e niente cambio */
  const ID3 = ID.replace(/^a/, 'c');
  run(`p2pLibro.ordini.push(Object.assign({}, rigaLibroP2P(${JSON.stringify(ID)}), {id: ${JSON.stringify(ID3)}})); p2pDettOrdine = ${JSON.stringify(ID3)}; fatturaDelWallet = ''`);
  await run(`apriPresaOcP2P(${JSON.stringify(ID3)})`);
  await run(`creaPresaOcP2P({}, ${JSON.stringify(ID3)})`);
  out.muto = [corpo().includes('Il wallet collegato non ha dato la richiesta'), !!lista().find(r => r.p2pPresa === ID3)];
  /* la leva spenta: il riquadro non c'e' (senza un cambio vivo) */
  run('swapLeve.p2p.presa = false');
  out.spento = corpo() === '';
  out.sentinella = {paga: run('server.filter(s => s[0] === "paga").length'),
                    altri: run('server.filter(s => ["cambio-libero", "biglietto-t1", "biglietto-t3"].includes(s[0])).length'),
                    fuori: chiamate.filter(c => !c.url.startsWith(BASE)).map(c => c.url)};
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def telefono(base, riga, prev, biglietto, buona, buona2, sbagliata):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="presa_ln_p2p_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "riga": riga, "preventivo": prev, "biglietto": biglietto,
            "buona": buona, "buona2": buona2, "sbagliata": sbagliata,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "testnet",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 500_000,
                     "mempool": base + "/esplora",
                     "fornitori": [{"id": "satsrouting", "nome": "SATS Routing",
                                    "tipo": "boltz", "api": base,
                                    "referral": "barattolo", "rete": "testnet",
                                    "mempool": base + "/esplora"}],
                     "cambio": {"attivo": False, "minimo": 25_000, "massimo": 500_000,
                                "al_giorno": 5, "oggi": 0, "strade": ["ln-btc", "btc-ln"]},
                     "p2p": {"attivo": True, "presa": True, "minimo": 25_000,
                             "massimo": 500_000}}}))
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
    print("  ₿ P2P: VENDERE SU UN ORDINE LIGHTNING AVENDO SOLO BITCOIN")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    import httpx
    from embit.ec import PrivateKey
    from fastapi.testclient import TestClient
    SRV.httpx = httpx           # il cartone e' vero, su 127.0.0.1
    _, PORTA = cartone_satsrouting.avvia(0, rete="testnet")
    base = f"http://127.0.0.1:{PORTA}"
    c = TestClient(SRV.app)

    con = SRV.db()
    for tg, nome in ((999, "Andrea"), (111, "Compratore")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}{tg}"))
    con.commit()
    con.close()
    SRV.ADMIN_IDS = [999]
    SRV.P2P_ATTIVO = True
    SRV.SWAP_ATTIVO = True
    SRV.SWAP_SOLO_MODERATORI = True
    SRV.SWAP_MIN_SATS = 25_000
    SRV.SWAP_FEE_PERCENTO = 0.5       # accesa: qui non deve contare
    SRV.SWAP_API_BASE = base
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.SWAP_RETE = "testnet"
    SRV.CAMBIO_BTC_LN_ATTIVO = False
    SRV.P2P_ALTRA_RETE_ATTIVO = False
    SRV.P2P_ALTRA_RETE_SOLO_MODERATORI = True
    SRV.P2P_ALTRA_RETE_MAX_SATS = 500_000

    def come(tg):
        banco.come(tg, admin=tg in SRV.ADMIN_IDS)

    def preventivo(tg, sats, **q):
        come(tg)
        qs = "&".join(f"{k}={v}" for k, v in dict(q, sats=sats).items())
        return c.get(f"/api/swap/p2p/presa/preventivo?{qs}")

    def biglietto(tg, sats, ordine=ORDINE, **extra):
        come(tg)
        return c.post("/api/swap/p2p/presa",
                      json=dict({"ordine": ordine, "sats": sats,
                                 "fornitore": "satsrouting"}, **extra))

    def nato(tg, cid, corpo):
        come(tg)
        return c.post(f"/api/swap/p2p/{cid}/nato", json=corpo)

    def presa_di(tg):
        come(tg)
        return ((c.get("/api/me").json().get("swap_leve") or {}).get("p2p") or {}).get("presa")

    # ---- 1) il cancello ----------------------------------------------------
    print("\n[il cancello: la leva della presa sull'altra rete e la strada bitcoin → Lightning]")
    prova("a leva spenta: 403 al preventivo e al biglietto, e la pagina lo sa",
          (403, 403, False),
          (preventivo(999, 100_000).status_code, biglietto(999, 100_000).status_code,
           presa_di(999)))
    SRV.P2P_ALTRA_RETE_ATTIVO = True
    prova("la leva accesa ma la strada bitcoin → Lightning del Cambio spenta: 403 lo stesso",
          (403, False), (preventivo(999, 100_000).status_code, presa_di(999)))
    SRV.CAMBIO_BTC_LN_ATTIVO = True
    prova("tutte e due accese: il moderatore si', gli altri no (solo moderatori)",
          (200, True, 403, False),
          (preventivo(999, 100_000).status_code, presa_di(999),
           preventivo(111, 100_000).status_code, presa_di(111)))

    # ---- 2) il preventivo --------------------------------------------------
    print("\n[il preventivo: quanti bitcoin mandare perche' arrivino i sats della garanzia]")
    p = preventivo(999, 101_000).json()
    prova("il conto del submarine: ricevi la garanzia, mandi di piu', il costo e' la "
          "differenza, niente fee nostra",
          (True, 101_000, True, p.get("mandi", 0) - 101_000, "satsrouting"),
          (p.get("ok"), p.get("ricevi"), p.get("mandi", 0) > 101_000, p.get("costo"),
           p.get("fornitore")))
    prova("...con l'impronta delle tariffe, e «cambiata» se il telefono ne aveva un'altra",
          (False, True), (preventivo(999, 101_000, hash=p["hash"]).json()["cambiata"],
                          preventivo(999, 101_000, hash="vecchia").json()["cambiata"]))
    prova("i no del preventivo: cifra mancante, sotto il minimo, sopra il tetto",
          ["cifra", "sotto_minimo", "sopra_tetto"],
          [preventivo(999, 0).json().get("motivo"), preventivo(999, 10_000).json().get("motivo"),
           preventivo(999, 600_000).json().get("motivo")])

    # ---- 3) il biglietto ---------------------------------------------------
    print("\n[il biglietto: l'ordine, i tetti, i troppi]")
    prova("i no del biglietto: l'ordine storto, sotto il minimo, sopra il tetto",
          ["ordine", "sotto_minimo", "sopra_tetto"],
          [biglietto(999, 101_000, ordine="../x").json().get("motivo"),
           biglietto(999, 10_000).json().get("motivo"),
           biglietto(999, 600_000).json().get("motivo")])
    b = biglietto(999, 101_000).json()
    riga = SRV.db().execute("SELECT * FROM cambi_p2p WHERE id=?", (b.get("id", 0),)).fetchone()
    prova("il biglietto c'e': lo scambio scritto «presa:<ordine>», chiesto, i sats della garanzia",
          (True, f"presa:{ORDINE}", "chiesto", 101_000, 999),
          (b.get("ok"), riga["ordine"] if riga else "", riga["stato"] if riga else "",
           riga["sats"] if riga else 0, riga["tg_id"] if riga else 0))
    biglietto(999, 101_000)
    biglietto(999, 101_000)
    prova("al quarto biglietto vivo sullo stesso ordine: troppi", "troppi",
          biglietto(999, 101_000).json().get("motivo"))
    prova("...ma un altro ordine ha i suoi", True,
          biglietto(999, 101_000, ordine="ffff0000-1111").json().get("ok"))

    # ---- 4) il telefono ----------------------------------------------------
    print("\n[il telefono: il riquadro, il conto, la richiesta, il cambio]")
    rigalibro = {"id": ORDINE, "lato": "buy", "sats": 100_000, "euro": 90,
                 "euroMax": 0, "premium": 0, "metodi": ["Bonifico"]}
    garanzia = 100_000 + round(100_000 * 0.01 / 2)
    pt = preventivo(999, garanzia).json()
    buona, buona2 = fattura(garanzia), fattura(garanzia)
    sbagliata = fattura(garanzia - 1000)
    t = telefono(base, rigalibro, pt, 41, buona["invoice"], buona2["invoice"],
                 sbagliata["invoice"])
    if t.get("ERRORE"):
        print(t["ERRORE"])
    prova("chiuso: la domanda «Hai solo bitcoin on-chain?» e il tasto", True, t.get("chiuso"))
    prova("la garanzia: la cifra fissa piu' meta' della commissione, non una stima; "
          "su un intervallo senza cifra niente; a mercato il 2% in piu'",
          ({"sats": garanzia, "stima": False}, 0, True),
          (t.get("garanzia"), (t.get("garanziaRange") or {}).get("sats"),
           (t.get("garanziaMercato") or {}).get("stima")))
    prova("aperto: il preventivo chiesto per quei sats", [{"sats": garanzia, "fornitore": "", "hash": ""}],
          t.get("preventivoChiesto"))
    prova("il conto: quanti sats servono, quanti bitcoin mandare, il costo, il campo della "
          "richiesta e il tasto",
          {"servono": True, "mandi": True, "costo": True, "campo": True, "tasto": True},
          t.get("conto"))
    prova("una richiesta della cifra sbagliata: l'errore, e non parte niente", [True, 0, 0],
          t.get("sbagliata"))
    n = t.get("nato") or {}
    prova("«Crea il cambio»: biglietto poi nascita, UN submarine sul cartone", (["biglietto", "nato"], 1),
          (n.get("ordini"), n.get("swap")))
    prova("...il biglietto porta l'ordine e i sats della richiesta",
          {"ordine": ORDINE, "sats": garanzia, "fornitore": "satsrouting"}, n.get("biglietto"))
    prova("il record: p2pPresa, submarine, rimborso da scrivere nel Cambio, seme di Barattolo, "
          "il suo biglietto, NIENTE ordine del mercatino ne' scambio P2P",
          {"p2pPresa": ORDINE, "tipo": "sub", "indirizzo": "", "seme": "onchain", "biglietto": 41,
           "ordine": "nessuno", "p2p": "nessuno"}, n.get("record"))
    prova("...manda quel che dice il preventivo e riceve la garanzia, e alla nascita il server "
          "ha le sole parti pubbliche",
          (pt.get("mandi"), garanzia, True),
          (n.get("mandi"), n.get("ricevi"),
           sorted((n.get("natoPubblico") or {}).keys()) == ["impronta", "indirizzo", "onchain", "swap_id"]))
    prova("il cambio prima della presa non si confonde col Cambio libero", (True, None, False),
          (n.get("diPresa"), n.get("cambioLibero"), n.get("ordine0")))
    r = t.get("riquadro") or {}
    prova("il riquadro: «Manda esattamente…», il QR del link bitcoin: (byte), l'indirizzo, "
          "«Apri nel wallet», l'avviso del bot",
          (True, "p2pPresaOcQr", True, "Byte", True, True, True),
          (r.get("manda"), (r.get("qr") or [""])[0], str((r.get("qr") or ["", ""])[1]).startswith("bitcoin:"),
           (r.get("qr") or ["", "", ""])[2], r.get("indirizzo"), r.get("apri"), r.get("avvisa")))
    prova("un secondo «Crea» non fa un cambio nuovo", {"biglietti": 1, "swap": 1}, t.get("riuso"))
    prova("i sats arrivati: il riquadro dice di toccare «Vendi»", ("fatto", True),
          (t.get("fase"), t.get("riuscito")))
    prova("nella lista del Cambio si chiama «Scambio P2P»", True, t.get("lista"))
    prova("col wallet collegato: la richiesta la chiede il telefono (i sats, 24 ore), e il "
          "client si chiude",
          ({"frase": True, "campo": False}, [garanzia, "Barattolo: sats per vendere nel P2P", 86400], "chiuso", True),
          (t.get("collegato"), (t.get("chieste") or [None])[0], (t.get("chieste") or [None, None])[1],
           t.get("nato2")))
    prova("...il wallet che non da' la richiesta: si dice, e non nasce niente", [True, False],
          t.get("muto"))
    prova("a leva spenta (e senza cambio vivo) il riquadro non c'e'", True, t.get("spento"))
    prova("sentinella: nessun pagamento al server, nessun altro cambio, niente fuori da 127.0.0.1",
          {"paga": 0, "altri": 0, "fuori": []}, t.get("sentinella"))

    # ---- 5) la ronda ---------------------------------------------------------
    print("\n[la ronda: la richiesta pagata, il cambio fallito coi bitcoin mandati]")
    avvisi = []

    async def notifica_finta(tg_id, testo, bottone=None):
        avvisi.append((tg_id, testo, bottone))
        return "telegram"
    vera = SRV.notifica
    SRV.notifica = notifica_finta

    PRE = {}

    def nasce(ordine):
        """un biglietto e un submarine vero sul cartone, nato sul server"""
        bb = biglietto(999, 101_000, ordine=ordine).json()
        f = fattura(101_000)
        corpo = {"from": "BTC", "to": "BTC", "invoice": f["invoice"],
                 "refundPublicKey": PrivateKey(secrets.token_bytes(32)).get_public_key().sec().hex(), "pairHash": p["hash"]}
        req = urllib.request.Request(f"{base}/v2/swap/submarine", data=json.dumps(corpo).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as rr:
            sw = json.loads(rr.read().decode("utf-8"))
        esito = nato(999, bb["id"], {"swap_id": sw["id"], "impronta": f["impronta"],
                                     "indirizzo": sw["address"], "onchain": sw["expectedAmount"]})
        PRE[sw["id"]] = f["preimage"]
        return bb["id"], sw["id"], esito.json()

    def riga_di(cid):
        return SRV.db().execute("SELECT stato, avvisato FROM cambi_p2p WHERE id=?",
                                (cid,)).fetchone()
    try:
        o1 = "1111aaaa-bbbb"
        cid, sid, esito = nasce(o1)
        prova("la nascita sul server vero", {"ok": True, "stato": "nato"}, esito)
        prova("i bitcoin in viaggio: nessun avviso ancora", 0, asyncio.run(SRV.ronda_cambi_p2p()))
        cartone(f"/cartone/stato?id={sid}&s=invoice.paid&preimage={PRE[sid]}")
        prova("la richiesta pagata: UN avviso", 1, asyncio.run(SRV.ronda_cambi_p2p()))
        tg, testo, bott = avvisi[-1] if avvisi else (0, "", None)
        prova("...a chi vende, «tocca per prendere l'ordine», col bottone sull'ordine del libro",
              (999, True, True, (SRV.P2P_BOTTONE_PRESA_PRONTA, f"{SRV.LINK_LIBRO_P2P}?ordine={o1}")),
              (tg, testo.startswith("⚡ I tuoi sats sono arrivati nel tuo wallet Lightning"),
               "i sats restano tuoi" in testo, bott))
        cartone(f"/cartone/stato?id={sid}&s=transaction.claimed")
        asyncio.run(SRV.ronda_cambi_p2p())
        prova("il cambio finito: in tutto un avviso solo, e la riga si chiude", (1, "finito"),
              (len(avvisi), riga_di(cid)[0]))

        o2 = "2222aaaa-bbbb"
        cid2, sid2, _ = nasce(o2)
        cartone(f"/cartone/stato?id={sid2}&s=transaction.mempool")
        asyncio.run(SRV.ronda_cambi_p2p())
        cartone(f"/cartone/stato?id={sid2}&s=swap.expired")
        prova("scaduto coi bitcoin visti partire: UN avviso", 1, asyncio.run(SRV.ronda_cambi_p2p()))
        tg, testo, bott = avvisi[-1]
        prova("...«Riprenditi i bitcoin», dalla pagina dello Swap",
              (True, True, SRV.P2P_BOTTONE_PRESA_RIMBORSO, "finito"),
              (testo.startswith("₿ Lo swap dei tuoi bitcoin non è riuscito"),
               "nella pagina «Swap»" in testo, bott[0], riga_di(cid2)[0]))

        o3 = "3333aaaa-bbbb"
        cid3, sid3, _ = nasce(o3)
        cartone(f"/cartone/stato?id={sid3}&s=invoice.failedToPay")
        prova("la richiesta non pagata (i bitcoin c'erano per forza): UN avviso di rimborso",
              (1, SRV.P2P_BOTTONE_PRESA_RIMBORSO), (asyncio.run(SRV.ronda_cambi_p2p()),
                                                    avvisi[-1][2][0]))

        o4 = "4444aaaa-bbbb"
        cid4, sid4, _ = nasce(o4)
        cartone(f"/cartone/stato?id={sid4}&s=swap.expired")
        quanti = len(avvisi)
        prova("scaduto senza bitcoin mandati: nessun avviso, e la riga si chiude", (0, quanti, "finito"),
              (asyncio.run(SRV.ronda_cambi_p2p()), len(avvisi), riga_di(cid4)[0]))

        # ---- 6) la leva rispenta ---------------------------------------
        print("\n[la leva rispenta: niente di nuovo, ma un cambio nato finisce]")
        o5 = "5555aaaa-bbbb"
        cid5, sid5, _ = nasce(o5)
        SRV.P2P_ALTRA_RETE_ATTIVO = False
        prova("a leva spenta: 403 al preventivo e al biglietto", (403, 403),
              (preventivo(999, 101_000).status_code, biglietto(999, 101_000, ordine="6666aaaa-bbbb").status_code))
        cartone(f"/cartone/stato?id={sid5}&s=invoice.paid&preimage={PRE[sid5]}")
        prova("...ma il cambio nato prima ha il suo avviso", 1, asyncio.run(SRV.ronda_cambi_p2p()))
    finally:
        SRV.notifica = vera

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
