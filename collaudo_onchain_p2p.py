# -*- coding: utf-8 -*-
"""
⛓️ NEL P2P: LA GARANZIA DI MOSTRO PAGATA IN BITCOIN (28 ott 2026, cantiere
onchain-p2p, richiesta di Andrea: «lo stesso metodo di pagamento LN/onchain
deve comparire anche nel p2p»).

Mostro sa solo Lightning (la garanzia e' una hold invoice). La porta ⛓️ del
foglio «Blocca i sats» la fa pagare in bitcoin con la strada bitcoin →
Lightning del cambio (lo swap submarine del telefono). Qui:

IL SERVER (TestClient, la app vera, contro il SATS ROUTING DI CARTONE):
  - il cancello: `swap_leve.p2p` in /api/me, spento di serie; acceso, solo
    ai moderatori; senza la strada bitcoin → Lightning o senza lo swap
    sotto, spento per tutti;
  - il preventivo `/api/swap/p2p/preventivo`: quanto mandare per bloccare
    100.000 sats (+0,5 % +318 = 100.818), senza il tetto del cambio libero;
    i suoi no (cifra, sotto il minimo del submarine, cartone giu', 403).

IL TELEFONO (il codice VERO in node contro il cartone: swap/boltz.js,
swap/instradatore.js, il blocco ⛓️ della pagina e il vero `renderHoldP2P`):
  - a leva spenta il foglio e' quello di sempre, senza schede;
  - accesa, le due schede; con 30 minuti (chi PRENDE) ⛓️ e' spenta e il
    tocco dice perche'; con 3 ore si apre, chiede il conto, lo mostra;
  - «Paga in bitcoin»: la prima volta le 12 parole, poi lo swap al cartone
    con la richiesta di MOSTRO come fattura, il QR `bitcoin:`;
  - con i bitcoin chiesti, ⚡ dice di no (mai due pagamenti);
  - visti → confermati → la garanzia pagata (la nostra meta' del ritiro a
    due) → fatto;
  - lo scambio annullato: il pagamento torna indietro, il foglio chiede
    dove rimandare i bitcoin, il rimborso a due all'indirizzo scritto;
  - a foglio chiuso un avviso, una volta; la pagina «Cambio» lo chiama
    «Scambio P2P ⛓️», e un cambio P2P vivo non blocca il cambio libero;
  - la sentinella: il telefono parla col cartone e con la sola rotta del
    preventivo, e Barattolo non paga niente.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1; nessun Mostro (la richiesta di garanzia e' una fattura del
cartone), nessun relay, nessun sats.

USO:  python collaudo_onchain_p2p.py
"""
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
TESTE = {999: {"X-Tg-Init-Data": "collaudo:999:Admin"},
         222: {"X-Tg-Init-Data": "collaudo:222:Venditore"}}
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"


def leve(c, chi):
    banco.come(chi, admin=(chi == 999))
    r = c.get("/api/me", headers=TESTE[chi])
    return ((r.json() or {}).get("swap_leve") or {}).get("p2p") or {}


def preventivo(c, chi, sats, **extra):
    banco.come(chi, admin=(chi == 999))
    q = "&".join(f"{k}={v}" for k, v in dict(sats=sats, **extra).items())
    r = c.get(f"/api/swap/p2p/preventivo?{q}", headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def giro(c, porta):
    srv = banco.SRV
    con = srv.db()
    for tg, nome in ((999, "Admin"), (222, "Vende")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    con.commit()
    con.close()

    print("\n[il cancello]")
    prova("di serie la porta e' spenta, per tutti, coi suoi 60 minuti",
          ({"attivo": False, "minuti": 60}, {"attivo": False, "minuti": 60}),
          (leve(c, 999), leve(c, 222)))
    prova("...e la rotta del preventivo dice 403", 403, preventivo(c, 999, 100_000)[0])
    srv.P2P_ONCHAIN_ATTIVO = True
    prova("accesa ma senza la strada bitcoin → Lightning del cambio: spenta",
          (False, 403), (leve(c, 999).get("attivo"), preventivo(c, 999, 100_000)[0]))
    srv.CAMBIO_BTC_LN_ATTIVO = True
    prova("con la strada: solo il moderatore (solo-moderatori di serie)",
          (True, False, 200, 403),
          (leve(c, 999).get("attivo"), leve(c, 222).get("attivo"),
           preventivo(c, 999, 100_000)[0], preventivo(c, 222, 100_000)[0]))
    srv.P2P_ONCHAIN_SOLO_MODERATORI = False
    prova("...aperta a tutti ma con lo swap solo-moderatori: il 222 no (sta "
          "SOPRA il cancello dello swap)", False, leve(c, 222).get("attivo"))
    srv.SWAP_SOLO_MODERATORI = False
    prova("...aperti tutti e due: il 222 si'", True, leve(c, 222).get("attivo"))
    srv.SWAP_ATTIVO = False
    prova("senza lo swap sotto: nessuno", (False, False, 403),
          (leve(c, 999).get("attivo"), leve(c, 222).get("attivo"),
           preventivo(c, 999, 100_000)[0]))
    srv.SWAP_ATTIVO = True
    srv.P2P_ONCHAIN_SOLO_MODERATORI = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.P2P_ONCHAIN_MINUTI_MIN = 45
    prova("i minuti si leggono dalla leva", 45, leve(c, 999).get("minuti"))
    srv.P2P_ONCHAIN_MINUTI_MIN = 60

    print("\n[il preventivo]")
    codice, p = preventivo(c, 999, 100_000)
    prova("per bloccare 100.000 sats si mandano 100.818 (+0,5 % +318), letti "
          "dalle tariffe del submarine del cartone",
          (200, True, 100_000, 100_818, "cartone-sub-16ott", "SATS Routing",
           [("ricevi_ln", 100_000), ("commissione", 500), ("rete_loro", 318)]),
          (codice, p.get("ok"), p.get("ricevi"), p.get("mandi"), p.get("hash"),
           p.get("fornitore_nome"), [(r["voce"], r["sats"]) for r in p.get("righe", [])]))
    _, p = preventivo(c, 999, 600_000)
    prova("600.000: niente tetto del cambio libero (500.000), vale quello del P2P",
          (True, 600_000), (p.get("ok"), p.get("ricevi")))
    _, p = preventivo(c, 999, 40_000)
    prova("sotto il minimo del submarine (50.000)", (False, "sotto_minimo", 50_000),
          (p.get("ok"), p.get("motivo"), p.get("minimo")))
    _, p = preventivo(c, 999, "")
    prova("senza cifra", (False, "cifra"), (p.get("ok"), p.get("motivo")))
    prova("un fornitore sconosciuto: 404", 404, preventivo(c, 999, 100_000, fornitore="pinco")[0])
    import urllib.request
    urllib.request.urlopen(f"http://127.0.0.1:{porta}/cartone/modo?m=giu", timeout=5).read()
    srv._TARIFFE_SUB.clear()
    _, p = preventivo(c, 999, 100_000)
    prova("SATS Routing giu': «non_risponde»", (False, "non_risponde"),
          (p.get("ok"), p.get("motivo")))
    urllib.request.urlopen(f"http://127.0.0.1:{porta}/cartone/modo?m=normale", timeout=5).read()
    srv._TARIFFE_SUB.clear()
    srv.P2P_ONCHAIN_ATTIVO = False
    srv.CAMBIO_BTC_LN_ATTIVO = False
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)


# ──────────────────────────────────────────────────────────────────────
# IL TELEFONO
# ──────────────────────────────────────────────────────────────────────
def pezzi_pagina():
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    mini = mini.replace("\r\n", "\n")

    def tra(firma, fine="\n}\n", fino_a=""):
        i = mini.index(firma)
        if fino_a:
            return mini[i:mini.index(fino_a, i)]
        return mini[i:mini.index(fine, i) + len(fine)]
    return "\n".join([
        tra("function importoBolt11(pr){"), tra("function leggiBolt11(pr){"),
        tra("function scadenzaFoglioP2P(o, modo){"),
        tra("function renderHoldP2P(){"),
        tra("/* ============ ⛓️ NEL P2P (28 ott 2026",
            fino_a="/* ============ fine del ⛓️ nel P2P")])


BANCO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const BUNDLE = fs.readFileSync(D.bundle, 'utf8');
const TELEFONO = D.telefono.map(f => fs.readFileSync(f, 'utf8'));
const fetchVero = globalThis.fetch;
const chiamate = [];
const BASE = D.base;
const modo = m => fetchVero(`${BASE}/cartone/modo?m=${m}`).then(r => r.json());
const visto = () => fetchVero(`${BASE}/cartone/visto`).then(r => r.json());
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finche = async (f, ms = 5000) => { const t0 = Date.now(); while (!f() && Date.now() - t0 < ms) await sleep(100); };
const memoria = new Map();
const preventivi = [];
const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL,
  Uint8Array, BigInt, setTimeout, clearTimeout, Promise, JSON, Date, Math,
  fetch: async (url, opz) => {
    chiamate.push({url: String(url), metodo: (opz && opz.method) || 'GET'});
    /* LA ROTTA DEL PREVENTIVO DI BARATTOLO, finta e contata: il conto
       vero del server (preventivo_sub) lo prova la parte di sopra */
    if (String(url).startsWith('/api/swap/p2p/preventivo')) {
      const q = new URL('http://x' + String(url)).searchParams;
      const sats = Number(q.get('sats')), comm = Math.ceil(sats * 5 / 1000), mandi = sats + comm + 318;
      preventivi.push({sats, fornitore: q.get('fornitore'), auth: !!(opz && opz.headers && opz.headers['X-Tg-Init-Data'])});
      const d = {ok: true, hash: 'cartone-sub-16ott', dovuto: sats, fattura: sats, ricevi: sats, mandi, valido_s: 60,
                 fornitore: 'satsrouting', fornitore_nome: 'SATS Routing',
                 righe: [{voce: 'ricevi_ln', sats}, {voce: 'commissione', sats: comm, piu: true, percento: 0.5},
                         {voce: 'rete_loro', sats: 318, piu: true}]};
      return {ok: true, json: async () => d};
    }
    return fetchVero(url, opz);
  }};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(BUNDLE, ctx);
vm.runInContext(`
let myTgId = 999;
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
function copiaLink(t, m){ avvisi.push('APPUNTI:' + String(t).slice(0, 4)); avvisi.push(m); }
function authHdr(){ return 'collaudo:999:Admin'; }
let currentOrder = null;
let preventiviSwap = {}, sceltaIncassoSwap = {};
let tg = {initDataUnsafe: {user: {language_code: 'it'}}};
function linguaSwap(){ return 'it'; }
function ridisegnaIncassoSwap(){}
function renderSwapCambio(){}
async function pagaSwapAlServer(rec){ pagati.push(rec.ordine); return null; }
async function statoPagamentoSwap(){ return null; }
const pagati = [];
/* IL MOTORE DEL P2P, quanto basta: un ordine, il foglio aperto */
let p2pHoldOrdine = null, p2pHoldModo = 'hold';
let p2pInfo = {scadenzaSec: 1800};
let finestra = 1800;
function finestraMiaP2P(){ return finestra; }
function tempoParoleP2P(s){ return Math.round(s / 60) + ' minuti'; }
const ORDINI = {};
function ordiniP2P(){ return ORDINI; }
function rigaWosHoldP2P(){ return ''; }
function rigaPhoenixHoldP2P(){ return ''; }
function orologioHoldP2P(){}
const qr = [];
async function disegnaQr(box, testo, modo){ qr.push([box && box.id, String(testo).slice(0, 12), modo]); return true; }
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const document = {addEventListener(){}, head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
`, Object.assign(ctx, {__memoria: memoria}));
vm.runInContext(D.pagina, ctx);
for (const codice of TELEFONO) vm.runInContext(codice, ctx);
const run = c => vm.runInContext(c, ctx);
const corpo = () => run('elementi.p2pHoldCorpo.innerHTML');
const lista = () => JSON.parse(memoria.get('barattolo_swap_lista_999') || '[]');
const apri = id => run(`p2pHoldOrdine = ${JSON.stringify(id)}; p2pHoldModo = 'hold'; apriPorteP2P(${JSON.stringify(id)}); renderHoldP2P()`);

(async () => {
  const out = {};
  run("elementi.p2pHoldCorpo = {innerHTML: ''}; elementi.p2pHoldTit = {textContent: ''}; elementi.p2pHoldInvoice = {textContent: ''};"
    + "elementi.p2pHoldQr = {id: 'p2pHoldQr'}; elementi.p2pHoldSheet = {classList: {contains: () => aperto}};"
    + "elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}};");
  run('var aperto = true');
  run(`ORDINI.uno = {id: 'uno', stato: 'attesa_mia_hold', lato: 'vendo', hold: {bolt11: ${JSON.stringify(D.hold.uno.invoice)}, sats: 100000, quando: Math.floor(Date.now()/1000)}};`
    + `ORDINI.due = {id: 'due', stato: 'attesa_mia_hold', lato: 'vendo', hold: {bolt11: ${JSON.stringify(D.hold.due.invoice)}, sats: 100000, quando: Math.floor(Date.now()/1000)}};`);
  // --- a leva spenta: il foglio di sempre, senza schede
  run('swapLeve.p2p = {attivo: false, minuti: 60}');
  apri('uno');
  out.spenta = {schede: corpo().includes('pay-metodo'), ln: corpo().includes('bloccati in garanzia')};
  // --- accesa, 30 minuti (chi PRENDE): ⛓️ spenta, il tocco dice perche'
  run('swapLeve.p2p = {attivo: true, minuti: 60}; finestra = 1800');
  apri('uno');
  const c1 = corpo();
  out.trenta = {schede: (c1.match(/role="tab"/g) || []).length, lnAttiva: c1.includes('class="ln attiva"'),
                ocSpenta: c1.includes('class="oc spento"'), nonAdesso: c1.includes('non adesso'), ln: c1.includes('bloccati in garanzia')};
  run("passaPortaP2P('onchain')");
  out.trentaTocco = {porta: run('p2pPorta'), nota: run('p2pOcErrore'), preventivi: preventivi.length};
  // --- 3 ore (chi PUBBLICA): ⛓️ si apre e chiede il conto
  run('finestra = 10800');
  apri('uno');
  run("passaPortaP2P('onchain')");
  await finche(() => !corpo().includes('Chiedo il conto'));
  const c2 = corpo();
  out.conto = {porta: run('p2pPorta'), preventivo: preventivi[0], ocAttiva: c2.includes('class="oc attiva"'),
               garanzia: c2.includes('<span>In garanzia</span><span class="mono">100000 sats</span>'),
               commissione: c2.includes('<span>Commissione del cambio</span><span class="mono">500 sats</span>'),
               rete: c2.includes('<span>Rete del cambio</span><span class="mono">318 sats</span>'),
               mandi: c2.includes('<span>Da mandare in bitcoin</span><span class="mono">100818 sats</span>'),
               bottone: c2.includes('onclick="creaOnchainP2P()">⛓️ Paga in bitcoin'),
               spiega: c2.includes('i tuoi bitcoin tornano a te'), niente_ln: c2.includes('bloccati in garanzia')};
  // --- «Paga in bitcoin»: la prima volta le 12 parole
  await run('creaOnchainP2P()');
  const c3 = corpo();
  out.parole = {passo: run('p2pOcParole'), parole: (c3.match(/<li>/g) || []).length, spunta: c3.includes('id="p2pOcSpunta"'),
                swap: lista().length};
  run("elementi.p2pOcSpunta = {checked: false}");
  await run('paroleFatteOnchainP2P()');
  out.senzaSpunta = [run('avvisi[avvisi.length - 1]'), lista().length];
  run("elementi.p2pOcSpunta = {checked: true}");
  const v1 = await visto();
  await run('paroleFatteOnchainP2P()');
  const v2 = await visto();
  const r1 = lista()[0] || {};
  const c4 = corpo();
  out.nato = {swap: v2.swap - v1.swap, referral: v2.creazione && v2.creazione.referralId,
              fattura: v2.creazione && v2.creazione.invoice === D.hold.uno.invoice,
              record: {ordine: r1.ordine, p2p: r1.p2p, tipo: r1.tipo, indice: r1.indice, mandi: r1.mandi, indirizzo: r1.indirizzo},
              impronta: r1.impronta === D.hold.uno.impronta, copiata: JSON.parse(memoria.get('barattolo_swap_999')).copiata,
              frase: c4.includes('Manda i bitcoin a questo indirizzo'), cifra: c4.includes('<b>100818 sats</b> in bitcoin'),
              indirizzo: c4.includes(r1.lockupAddress), copia: c4.includes('copiaOnchainP2P()'),
              wallet: c4.includes('href="bitcoin:' + r1.lockupAddress + '?amount=0.00100818'),
              qr: run('qr[qr.length - 1]'), pagati: run('pagati.length')};
  run('copiaOnchainP2P()');
  out.copia = run('avvisi.slice(-2)');
  // --- con i bitcoin chiesti, ⚡ dice di no
  run("passaPortaP2P('ln')");
  out.lnNo = [run('p2pPorta'), run('p2pOcErrore')];
  // --- riaperto il foglio: si riapre sulla porta dei bitcoin
  apri('uno');
  out.riaperto = [run('p2pPorta'), corpo().includes(r1.lockupAddress)];
  // --- la pagina «Cambio»: «Scambio P2P ⛓️», e il cambio libero non e' bloccato
  run('renderSwapTelefono()');
  out.pagina = {etichetta: run('elementi.swapTelefono.innerHTML').includes('<b>Scambio P2P ⛓️</b>'),
                cambioLibero: run('swapDiOrdine(0)'), eCambio: run('swapECambio(swapLista()[0])')};
  // --- visti, confermati, la garanzia pagata (la nostra meta' del ritiro), fatto
  await stato(r1.id, 'transaction.mempool'); await run('swapGiro()');
  out.visti = [corpo().includes('Bitcoin visti'), lista()[0].bloccato];
  await stato(r1.id, 'transaction.confirmed'); await run('swapGiro()');
  out.confermati = corpo().includes('il cambio sta bloccando la garanzia');
  const vP = await visto();
  await stato(r1.id, 'invoice.paid&preimage=' + D.hold.uno.preimage); await run('swapGiro()');
  const vD = await visto();
  out.pagata = {ritiri: vD.ritiri.filter(x => x === r1.id).length - vP.ritiri.filter(x => x === r1.id).length,
                ritiro: (lista()[0].ritiro || {}).cooperativo, frase: corpo().includes('Garanzia bloccata')};
  await run('swapGiro()');
  out.fatto = run('swapFase(swapLista()[0])');
  // --- LO SCAMBIO ANNULLATO: la garanzia sciolta, i bitcoin tornano
  run('p2pPorta = "ln"');
  apri('due');
  run("passaPortaP2P('onchain')");
  await finche(() => corpo().includes('Paga in bitcoin'));
  await run('creaOnchainP2P()');   /* le parole ci sono gia': nasce subito */
  const r2 = lista().find(r => r.p2p === 'due') || {};
  out.secondo = {nato: !!r2.id, indice: r2.indice, parole: run('p2pOcParole')};
  await stato(r2.id, 'transaction.mempool'); await run('swapGiro()');
  await stato(r2.id, 'invoice.failedToPay'); await run('swapGiro()');
  const c5 = corpo();
  out.annullato = {frase: c5.includes('La garanzia non è servita: i tuoi bitcoin tornano a te'),
                   campo: c5.includes('id="p2pOcRimborso"'), porta: run('p2pPorta')};
  run(`elementi.p2pOcRimborso = {value: '${D.indirizzo}'}`);
  const vR1 = await visto();
  run('rimborsoOnchainP2P()');
  const rec2 = () => lista().find(r => r.id === r2.id);
  await finche(() => (rec2().rimborso || {}).txid || rec2().errore);
  const vR2 = await visto();
  out.rimborso = {indirizzo: rec2().indirizzo, cooperativo: (rec2().rimborso || {}).cooperativo,
                  firme: vR2.rimborsi.filter(x => x === r2.id).length - vR1.rimborsi.filter(x => x === r2.id).length,
                  errore: rec2().errore || '', fase: run('swapFase(swapLista().find(r => r.p2p === "due"))')};
  run('renderHoldP2P()');
  out.dopoRimborso = corpo().includes('Paga in bitcoin');
  // --- A FOGLIO CHIUSO: un avviso, una volta sola
  run('aperto = false; p2pHoldOrdine = null');
  run(`ORDINI.tre = {id: 'tre', stato: 'attesa_mia_hold', lato: 'vendo', hold: {bolt11: ${JSON.stringify(D.hold.tre.invoice)}, sats: 100000, quando: Math.floor(Date.now()/1000)}};`);
  run('aperto = true'); apri('tre'); run("passaPortaP2P('onchain')");
  await finche(() => corpo().includes('Paga in bitcoin'));
  await run('creaOnchainP2P()');
  const r3 = lista().find(r => r.p2p === 'tre') || {};
  run('aperto = false');
  const nAvvisi = run('avvisi.length');
  await stato(r3.id, 'transaction.mempool'); await run('swapGiro()');
  await stato(r3.id, 'invoice.failedToPay'); await run('swapGiro()'); await run('swapGiro()');
  out.avviso = {quanti: run('avvisi.length') - nAvvisi, testo: run('avvisi[avvisi.length - 1]'),
                segnato: !!(lista().find(r => r.id === r3.id) || {}).avvisato};
  out.sentinella = {fuori: chiamate.filter(c => !c.url.startsWith(BASE + '/v2/') && !c.url.startsWith(BASE + '/esplora/')
                                              && !c.url.startsWith('/api/swap/p2p/preventivo?')).map(c => c.url),
                    pagati: run('pagati.length'), auth: preventivi.every(p => p.auth)};
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def richieste_mostro():
    """Le richieste di garanzia «di Mostro»: fatture del cartone da
    100.000 sats, col segreto che conosce il banco."""
    out = {}
    for nome in ("uno", "due", "tre"):
        pre = secrets.token_bytes(32)
        imp = hashlib.sha256(pre).hexdigest()
        inv = cartone_satsrouting.cripto("fattura", rete="bitcoin", sats=100_000,
                                         impronta=imp)["invoice"]
        out[nome] = {"invoice": inv, "preimage": pre.hex(), "impronta": imp}
    return out


def telefono(base):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="onchain_p2p_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "indirizzo": INDIRIZZO,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "hold": richieste_mostro(),
            "leve": {"attivo": True, "api": base, "rete": "bitcoin",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000,
                     "mempool": base + "/esplora",
                     "cambio": {"attivo": False, "strade": ["ln-btc", "btc-ln"]},
                     "p2p": {"attivo": False, "minuti": 60}}}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1500:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def il_telefono(base):
    print("\n[il telefono: le due schede del foglio «Blocca i sats»]")
    r = telefono(base)
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return
    prova("a leva spenta il foglio di sempre, senza schede",
          {"schede": False, "ln": True}, r["spenta"])
    prova("accesa, con 30 minuti: due schede, ⚡ accesa, ⛓️ spenta «non adesso», "
          "sotto il foglio Lightning",
          {"schede": 2, "lnAttiva": True, "ocSpenta": True, "nonAdesso": True, "ln": True}, r["trenta"])
    prova("...il tocco su ⛓️ dice perche' e non chiede niente",
          {"porta": "ln", "nota": "⛓️ Servono almeno 60 minuti (i bitcoin vogliono una "
                                  "conferma): ne restano 29. Paga con ⚡.", "preventivi": 0},
          r["trentaTocco"])
    prova("con 3 ore: ⛓️ si apre, chiede il conto al server (col suo cancello) e lo "
          "mostra riga per riga; il foglio Lightning non c'e'",
          {"porta": "onchain", "preventivo": {"sats": 100_000, "fornitore": "satsrouting", "auth": True},
           "ocAttiva": True, "garanzia": True, "commissione": True, "rete": True, "mandi": True,
           "bottone": True, "spiega": True, "niente_ln": False}, r["conto"])
    prova("«Paga in bitcoin» la prima volta: le 12 parole e la spunta, nessuno swap",
          {"passo": True, "parole": 12, "spunta": True, "swap": 0}, r["parole"])
    prova("...«Continua» senza spunta: lo dice, nessuno swap",
          ["Prima spunta «Le ho scritte»", 0], r["senzaSpunta"])
    prova("...con la spunta: lo swap al cartone con la richiesta DI MOSTRO come "
          "fattura, il record «p2p» di quello scambio, il QR bitcoin:, «Copia», "
          "«Apri nel wallet»; Barattolo non paga niente",
          {"swap": 1, "referral": "barattolo", "fattura": True,
           "record": {"ordine": "p2p", "p2p": "uno", "tipo": "sub", "indice": 0,
                      "mandi": 100_818, "indirizzo": ""},
           "impronta": True, "copiata": True, "frase": True, "cifra": True, "indirizzo": True,
           "copia": True, "wallet": True, "qr": ["p2pHoldQr", "bitcoin:bc1p", "Byte"], "pagati": 0},
          r["nato"])
    prova("«Copia l'indirizzo»", ["APPUNTI:bc1p", "Indirizzo copiato 📋"], r["copia"])
    prova("con i bitcoin chiesti ⚡ dice di no: mai due pagamenti",
          ["onchain", "Hai già chiesto di pagare in bitcoin: aspetta che arrivino, o che tornino a te."],
          r["lnNo"])
    prova("riaperto il foglio, si riapre sui bitcoin", ["onchain", True], r["riaperto"])
    prova("la pagina «Cambio» lo chiama «Scambio P2P ⛓️», e un cambio P2P vivo non "
          "blocca il cambio libero",
          {"etichetta": True, "cambioLibero": None, "eCambio": False}, r["pagina"])
    prova("i bitcoin visti, poi confermati: il foglio lo dice", ([True, True], True),
          (r["visti"], r["confermati"]))
    prova("la garanzia pagata: la nostra meta' del ritiro a due, una volta; poi fatto",
          ({"ritiri": 1, "ritiro": True, "frase": True}, "fatto"), (r["pagata"], r["fatto"]))
    prova("il secondo scambio: le parole ci sono gia', nasce subito con la chiave dopo",
          {"nato": True, "indice": 1, "parole": False}, r["secondo"])
    prova("lo scambio annullato (la garanzia sciolta): il foglio dice che i bitcoin "
          "tornano e chiede dove", {"frase": True, "campo": True, "porta": "onchain"},
          r["annullato"])
    prova("...l'indirizzo scritto: il rimborso a due, «ripreso»",
          {"indirizzo": INDIRIZZO, "cooperativo": True, "firme": 1, "errore": "", "fase": "ripreso"},
          r["rimborso"])
    prova("...e dopo, il foglio torna a offrire «Paga in bitcoin»", True, r["dopoRimborso"])
    prova("a foglio chiuso: un avviso, una volta sola, che manda a «Cambio»",
          {"quanti": 1, "testo": "↩️ Lo scambio P2P si è chiuso senza la tua garanzia in bitcoin: "
                                 "i bitcoin tornano a te. Apri «Cambio» e scrivi dove rimandarli.",
           "segnato": True}, r["avviso"])
    prova("la sentinella: il telefono parla col cartone e con la sola rotta del "
          "preventivo; Barattolo non paga mai", {"fuori": [], "pagati": 0, "auth": True},
          r["sentinella"])


def main():
    print("=" * 58)
    print("  ⛓️ NEL P2P — la garanzia di Mostro pagata in bitcoin")
    print("=" * 58)
    banco.avvio()
    import httpx
    from fastapi.testclient import TestClient

    srv = banco.SRV
    srv.httpx = httpx
    _, porta = cartone_satsrouting.avvia(0)
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_MIN_SATS = 25_000
    srv.SWAP_MAX_SATS = 50_000
    srv.SWAP_API_BASE = f"http://127.0.0.1:{porta}"
    srv.SWAP_REFERRAL_ID = "barattolo"
    srv.CAMBIO_BTC_LN_ATTIVO = False
    srv.P2P_ONCHAIN_ATTIVO = False
    srv.P2P_ONCHAIN_SOLO_MODERATORI = True
    srv.P2P_ONCHAIN_MINUTI_MIN = 60
    giro(TestClient(srv.app), porta)
    il_telefono(f"http://127.0.0.1:{porta}")

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
