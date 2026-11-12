# -*- coding: utf-8 -*-
"""
PRENDERE UN ORDINE P2P LIGHTNING E RICEVERE ON-CHAIN, TAPPA 1: IL CAMBIO
DI CHI COMPRA, SUL SERVER VERO E NEL TELEFONO VERO (1 nov 2026, cantiere
presa-altra-rete; studio del 30 ott, ok di Andrea del 1 nov).

`prove.py` gira le sentinelle e i pezzi puri. Qui la STORIA, contro il
SATS ROUTING DI CARTONE acceso su una porta di questo computer.

LE SCENE DEL SERVER (TestClient, la app vera):
  - il cancello: in `/api/me` il 999 ha `swap_leve.p2p` (tetti), il 222
    no; le porte del preventivo e del biglietto glielo dicono;
  - il preventivo di 100.000 sats: la fattura porta 100.000 AL SAT anche
    con la nostra fee accesa (Mostro rifiuterebbe una cifra diversa),
    quanto arriva, le righe; i rifiuti (cifra, sotto il minimo, sopra il
    tetto, SATS Routing giu');
  - il biglietto: lo scambio storto, tre vivi sullo stesso scambio e il
    quarto «troppi», un altro scambio libero, l'annullo che libera;
  - la nascita: le parti pubbliche, idempotente, «doppio», 404 di un altro;
  - le leve: spenta (403, `attivo` False), senza lo swap sotto, aperta a
    tutti.
IL TELEFONO (il codice vero in node contro il cartone, coi pezzi veri
della pagina): il foglio «Dove ricevere i sats» con «₿ On-chain», il
conto, i no (indirizzo storto, senza preventivo); «Invia»: biglietto,
swap al cartone, nascita, e a Mostro parte LA FATTURA DEL CAMBIO, della
cifra esatta; il record e' dello scambio e non di un ordine (Barattolo non
paga niente, non e' il cambio libero); un secondo «Invia» riusa lo stesso
cambio; i bitcoin bloccati al rilascio → il ritiro all'indirizzo.
LA RONDA DELL'AVVISO (di nuovo il server, sullo swap nato nel telefono):
bitcoin bloccati → UN avviso col bottone sullo scambio, non due; cambio
finito → la riga si chiude e la ronda non chiama piu'.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1; nessun relay, nessun Mostro: l'`add-invoice` e' contato, non
mandato.

USO:  python collaudo_cambio_p2p.py
"""
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
TESTE = {999: {"X-Tg-Init-Data": "collaudo:999:Admin"},
         222: {"X-Tg-Init-Data": "collaudo:222:Venditore"}}
PORTA = 0
IMPRONTA = "cd" * 32
SCAMBIO = "4f1c2a9e-7b3d-4e21-9c0a-11aa22bb33cc"
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def modo(m):
    cartone(f"/cartone/modo?m={m}")
    banco.SRV._TARIFFE_SWAP.update(quando=0.0, dati=None)   # niente copia


def semina():
    con = banco.SRV.db()
    for tg, nome in ((999, "Admin"), (222, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    con.execute("DROP TABLE IF EXISTS cambi_p2p")
    con.commit()
    con.close()


def leve(c, chi):
    banco.come(chi, admin=(chi == 999))
    r = c.get("/api/me", headers=TESTE[chi])
    return ((r.json() or {}).get("swap_leve") or {}).get("p2p") or {}


def preventivo(c, chi, sats, **extra):
    banco.come(chi, admin=(chi == 999))
    q = "&".join(f"{k}={v}" for k, v in dict(sats=sats, **extra).items())
    r = c.get(f"/api/swap/p2p/preventivo?{q}", headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def biglietto(c, chi, sats, ordine=SCAMBIO, **extra):
    banco.come(chi, admin=(chi == 999))
    corpo = dict({"ordine": ordine, "sats": sats, "fornitore": "satsrouting"}, **extra)
    r = c.post("/api/swap/p2p", json=corpo, headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def nato(c, chi, cid, swap_id, **extra):
    banco.come(chi, admin=(chi == 999))
    corpo = dict({"swap_id": swap_id, "impronta": IMPRONTA,
                  "indirizzo": "bc1pcartone", "onchain": 99_076}, **extra)
    r = c.post(f"/api/swap/p2p/{cid}/nato", json=corpo, headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def annulla(c, chi, cid):
    banco.come(chi, admin=(chi == 999))
    r = c.post(f"/api/swap/p2p/{cid}/annulla", headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def giro(c):
    srv = banco.SRV
    semina()
    modo("normale")

    print("\n[il cancello per persona]")
    l999, l222 = leve(c, 999), leve(c, 222)
    prova("a solo-moderatori il 999 ha il cambio dello scambio, coi tetti",
          (True, 25_000, 500_000), (l999.get("attivo"), l999.get("minimo"), l999.get("massimo")))
    prova("...il 222 no", False, l222.get("attivo"))
    prova("...e la porta del preventivo glielo dice", 403, preventivo(c, 222, 100_000)[0])
    prova("...e quella del biglietto pure", 403, biglietto(c, 222, 100_000)[0])

    print("\n[il preventivo di 100.000 sats, con la nostra fee accesa]")
    srv.SWAP_FEE_PERCENTO = 0.5
    codice, p = preventivo(c, 999, 100_000)
    srv.SWAP_FEE_PERCENTO = 0
    prova("la fattura porta la cifra di Mostro AL SAT: la nostra fee qui non c'e'",
          (200, True, 100_000, 100_000, "SATS Routing"),
          (codice, p.get("ok"), p.get("dovuto"), p.get("fattura"), p.get("fornitore_nome")))
    prova("...riga per riga: 0,6 % di cambio, le due reti, nessuna commissione Barattolo",
          [("dovuto", 100_000), ("commissione", -600), ("rete_invio", -324), ("rete_ritiro", -234)],
          [(r["voce"], r["sats"]) for r in p.get("righe") or []])
    prova("...quanto arriva all'indirizzo, l'impronta delle tariffe, quanto vale",
          (98_842, "cartone-tariffa-16ott", 60), (p.get("ricevi"), p.get("hash"), p.get("valido_s")))
    prova("...con l'impronta di ieri dice «cambiata»", True,
          preventivo(c, 999, 100_000, hash="vecchia")[1].get("cambiata"))

    print("\n[i rifiuti del preventivo]")
    prova("senza cifra", (200, False, "cifra"),
          (lambda r: (r[0], r[1].get("ok"), r[1].get("motivo")))(preventivo(c, 999, "")))
    prova("sotto il minimo del cambio (25.000)", (False, "sotto_minimo"),
          (lambda r: (r[1].get("ok"), r[1].get("motivo")))(preventivo(c, 999, 10_000)))
    prova("sopra il tetto (500.000)", (False, "sopra_tetto"),
          (lambda r: (r[1].get("ok"), r[1].get("motivo")))(preventivo(c, 999, 600_000)))
    prova("un fornitore che non c'e'", 404, preventivo(c, 999, 100_000, fornitore="nessuno")[0])
    modo("giu")
    prova("SATS Routing giu'", (False, "non_risponde"),
          (lambda r: (r[1].get("ok"), r[1].get("motivo")))(preventivo(c, 999, 100_000)))
    modo("normale")

    print("\n[il biglietto]")
    prova("lo scambio storto", {"ok": False, "motivo": "ordine"},
          biglietto(c, 999, 100_000, ordine="ab c")[1])
    prova("sotto il minimo / sopra il tetto / fornitore sconosciuto",
          ["sotto_minimo", "sopra_tetto", "fornitore"],
          [biglietto(c, 999, 10_000)[1].get("motivo"), biglietto(c, 999, 600_000)[1].get("motivo"),
           biglietto(c, 999, 100_000, fornitore="nessuno")[1].get("motivo")])
    ids = [biglietto(c, 999, 100_000)[1].get("id") for _ in range(3)]
    prova("tre biglietti vivi sullo stesso scambio", True, all(isinstance(i, int) and i > 0 for i in ids))
    prova("...il quarto dice «troppi»", {"ok": False, "motivo": "troppi"}, biglietto(c, 999, 100_000)[1])
    prova("...su un altro scambio si stacca", True,
          biglietto(c, 999, 100_000, ordine="99887766-aaaa")[1].get("ok"))
    prova("l'annullo libera il posto", ({"ok": True, "stato": "annullato"}, True),
          (annulla(c, 999, ids[0])[1], biglietto(c, 999, 100_000)[1].get("ok")))
    prova("...e un annullato non si annulla due volte", {"ok": False, "motivo": "annullato"},
          annulla(c, 999, ids[0])[1])

    print("\n[la nascita]")
    prova("le parti pubbliche, il biglietto passa a «nato»", (200, {"ok": True, "stato": "nato"}),
          nato(c, 999, ids[1], "cartoneP2P1"))
    prova("...idempotente sullo stesso swap", {"ok": True, "stato": "nato"},
          nato(c, 999, ids[1], "cartoneP2P1")[1])
    prova("...lo stesso swap su un altro biglietto e' «doppio»", {"ok": False, "motivo": "doppio"},
          nato(c, 999, ids[2], "cartoneP2P1")[1])
    prova("...una forma storta no", {"ok": False, "motivo": "forma"},
          nato(c, 999, ids[2], "x y")[1])
    prova("...il biglietto di un altro e' 404", 404, nato(c, 222, ids[2], "cartoneP2P2")[0])
    prova("...un biglietto annullato non nasce", {"ok": False, "motivo": "annullato"},
          nato(c, 999, ids[0], "cartoneP2P3")[1])
    con = srv.db()
    r = con.execute("SELECT stato, swap_id, impronta, onchain, ordine, sats FROM cambi_p2p "
                    "WHERE id=?", (ids[1],)).fetchone()
    con.close()
    prova("...e sul server restano le sole parti pubbliche, con lo scambio",
          ("nato", "cartoneP2P1", IMPRONTA, 99_076, SCAMBIO, 100_000), tuple(r))

    print("\n[le leve]")
    srv.P2P_ALTRA_RETE_ATTIVO = False
    prova("spenta: niente busta, 403 al preventivo e al biglietto", (False, 403, 403),
          (leve(c, 999).get("attivo"), preventivo(c, 999, 100_000)[0], biglietto(c, 999, 100_000)[0]))
    prova("...ma un cambio gia' chiesto puo' ancora annullarsi", {"ok": True, "stato": "annullato"},
          annulla(c, 999, ids[2])[1])
    srv.P2P_ALTRA_RETE_ATTIVO = True
    srv.SWAP_ATTIVO = False
    prova("senza lo swap sotto non c'e'", False, leve(c, 999).get("attivo"))
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = False
    srv.P2P_ALTRA_RETE_SOLO_MODERATORI = False
    prova("aperta a tutti la vede anche il 222", True, leve(c, 222).get("attivo"))
    srv.P2P_ALTRA_RETE_SOLO_MODERATORI = True
    srv.SWAP_SOLO_MODERATORI = True
    prova("...e richiusa no", False, leve(c, 222).get("attivo"))
    # pulito per il telefono e la ronda
    semina()


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
        tra("const SWAP_TESTI = {", fino_a="function linguaSwap(){"),
        # il foglio del cambio dello scambio, intero
        tra("const p2pIncassoRete = {};", fino_a="/* la scorciatoia SCRIVE nel campo e basta")])


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
const finche = async (f, ms = 5000) => { const t0 = Date.now(); while (!f() && Date.now() - t0 < ms) await sleep(100); };
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const memoria = new Map();
const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL,
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
function el(id){ return elementi[id] || null; }
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
function onchainSemeLocale(){ return localStorage.getItem('barattolo_onchain_' + myTgId) || ''; }
async function onchainSemeAssicurato(){
  let p = onchainSemeLocale();
  if (p) return p;
  p = BarattoloSwap.generateMnemonic(BarattoloSwap.wordlist);
  localStorage.setItem('barattolo_onchain_' + myTgId, p);
  return p;
}
/* le parole hanno gia' una copia fuori da qui (il cloud di Telegram) */
let paroleCoperte = true;
async function onchainSemeCoperto(){ return paroleCoperte; }
/* LE CHIAMATE AL SERVER DI BARATTOLO, finte e contate */
const server = [];
let bigliettoRisposta = {ok: true, id: 71};
async function chiediBigliettoCambioP2P(d){ server.push(['biglietto', d]); return bigliettoRisposta; }
async function natoCambioP2PAlServer(id, rec){ server.push(['nato', id, {swap_id: rec.id, impronta: rec.impronta, indirizzo: rec.lockupAddress, onchain: rec.onchainAmount}]); return {ok: true, stato: 'nato'}; }
async function liberaBigliettoCambioP2P(id){ server.push(['annulla', id]); return {ok: true}; }
async function pagaSwapAlServer(rec){ server.push(['paga', rec.ordine]); return null; }
async function statoPagamentoSwap(){ return null; }
async function chiediBigliettoCambio(d){ server.push(['cambio-libero', d]); return null; }
async function natoCambioAlServer(){ return null; }
async function liberaBigliettoCambio(){ return null; }
async function leggiPreventivoSwap(){ return {ok: false, motivo: 'non_risponde'}; }
/* il preventivo del server, detto dal giro Python sulla app vera */
const preventivi = [];
let preventivoServer = ${JSON.stringify(D.preventivo)};
async function leggiPreventivoCambioP2P(sats, fornitore, hash){
  preventivi.push({sats, fornitore, hash});
  return Object.assign({}, preventivoServer, {cambiata: !!hash && hash !== preventivoServer.hash});
}
async function disegnaQr(){ return true; }
function portaWallet(){}
/* LO SCAMBIO DI MOSTRO, finto: chi compra aspetta di dire dove ricevere */
const ID = ${JSON.stringify(D.scambio)};
const scambi = {[ID]: {id: ID, lato: 'compro', stato: 'attesa_mia_fattura'}};
function ordiniP2P(){ return scambi; }
function satsDaRicevereP2P(o){ return 100000; }
let p2pIncassoOrdine = ID;
let p2pFatturaComunque = '';
const mostro = [], tentativi = [], fermi = [];
function attesaP2P(){ return () => {}; }
function finestraFatturaP2P(){ return 60; }
function vitaMinimaFatturaP2P(){ return 60; }
function avvisoReteBolt11(){ return ''; }
async function controlloFatturaP2P(){ return null; }
function mostraFermoFatturaP2P(f, dove){ fermi.push([f, dove]); }
async function chiamataOrdineP2P(o, azione, payload){ mostro.push([o.id, azione, payload]); return {}; }
function segnaTentativoP2P(id, cosa){ tentativi.push(cosa); }
function ricordaFatturaP2P(){}
function chiudiFoglioP2P(id){ elementi.chiuso = id; }
async function dopoGestoP2P(){ return false; }
function avvisoFatturaCortaP2P(){ return 'corta'; }
function ragioneGestoP2P(e){ return String(e); }
function renderIncassoP2P(){}
`, Object.assign(ctx, {__memoria: memoria}));
vm.runInContext(D.pagina, ctx);
for (const codice of TELEFONO) vm.runInContext(codice, ctx);
const run = c => vm.runInContext(c, ctx);
const lista = () => JSON.parse(memoria.get('barattolo_swap_lista_999') || '[]');

(async () => {
  const out = {};
  const campo = v => run(`elementi.p2pIncassoOcInp = {value: ${JSON.stringify(v)}}; elementi.p2pIncassoAvviso = {textContent: '', style: {}}; elementi.p2pCambioConto = {innerHTML: ''}; elementi.p2pIncassoBtn = {};`);
  /* il cancello del foglio: solo a chi compra, prima del rilascio */
  out.cancello = run(`[cambioP2PDisponibile(scambi[ID]),
    cambioP2PDisponibile({id: 'x', lato: 'vendo', stato: 'attesa_mia_fattura'}),
    cambioP2PDisponibile({id: 'x', lato: 'compro', stato: 'rilasciato'}),
    cambioP2PDisponibile({id: 'x', lato: 'compro', stato: 'fattura_nuova'}),
    (swapLeve.p2p.attivo = false, cambioP2PDisponibile(scambi[ID])),
    (swapLeve.p2p.attivo = true, swapLeve.attivo = false, cambioP2PDisponibile(scambi[ID])),
    (swapLeve.attivo = true, true)]`);
  /* la scelta e il foglio */
  const scelta = run('sceltaReteIncassoP2P(true)');
  out.scelta = {ln: scelta.includes("scegliReteIncassoP2P('ln')") && scelta.includes('⚡ Lightning'),
                oc: scelta.includes("scegliReteIncassoP2P('oc')") && scelta.includes('₿ On-chain'),
                premuto: scelta.includes('aria-pressed="true"')};
  const corpo0 = run('corpoCambioIncassoP2P(scambi[ID], 100000)');
  out.foglioPrima = {calcolo: corpo0.includes('Calcolo quanto ricevi'), cifra: corpo0.includes('<b>100000 sats</b>'),
                     campo: corpo0.includes('id="p2pIncassoOcInp"'), invia: corpo0.includes('onclick="inviaCambioP2P()"'),
                     costo: corpo0.includes('Barattolo non aggiunge niente'), bot: corpo0.includes('ti avvisiamo col bot')};
  out.senzaCifra = run('corpoCambioIncassoP2P(scambi[ID], 0)').includes('per lo swap serve');
  campo('');
  await run('inviaCambioP2P()');
  out.senzaPreventivo = [run('elementi.p2pIncassoAvviso.textContent'), run('server.length')];
  await run('caricaCambioP2P(ID)');
  out.conto = run('elementi.p2pCambioConto.innerHTML');
  out.preventivoChiesto = run('preventivi.slice()');
  campo('');
  await run('inviaCambioP2P()');
  out.senzaIndirizzo = run('elementi.p2pIncassoAvviso.textContent');
  campo('bc1qnonvalido');
  await run('inviaCambioP2P()');
  out.indirizzoNo = [run('elementi.p2pIncassoAvviso.textContent'), run('server.length'), run('mostro.length')];
  /* (2 nov 2026 sera, Andrea) le parole SENZA copia fuori da qui non
     fermano piu' niente: nessun «prima il Profilo», il cambio nasce */
  run('paroleCoperte = false; swapParoleCoperte = ""');
  /* «Invia»: biglietto, swap, nascita, la fattura del cambio a Mostro */
  campo(D.indirizzo);
  await run('inviaCambioP2P()');
  out.paroleNo = run('elementi.p2pIncassoAvviso.textContent || ""').includes('12 parole');
  run('paroleCoperte = true');
  const rec = lista().find(r => r.p2p === D.scambio);
  const m = run('mostro.slice()');
  out.nato = {ordini: run('server.map(s => s[0])'),
              biglietto: run('server[0][1]'),
              record: rec ? {p2p: rec.p2p, ordine: rec.ordine === undefined ? 'nessuno' : rec.ordine,
                             indirizzo: rec.indirizzo, seme: rec.seme, biglietto: rec.biglietto, pagamento: rec.pagamento} : null,
              natoPubblico: run('server[1] && server[1][2]'),
              mostro: m.length ? [m[0][0], m[0][1], m[0][2].payment_request[1] === (rec && rec.invoice)] : null,
              importo: rec ? run('leggiBolt11(' + JSON.stringify(rec.invoice) + ').sats') : 0,
              tentativi: run('tentativi.slice()'), chiuso: run('elementi.chiuso || ""'),
              avviso: run('avvisi.slice(-1)[0] || ""'),
              diP2P: run('swapDiP2P(ID) && swapDiP2P(ID).id') === (rec && rec.id),
              cambioLibero: run('swapDiOrdine(0)'), ordine0: run('swapECambio(swapDiP2P(ID))')};
  out.swapId = rec ? rec.id : '';
  /* un secondo «Invia» (la risposta di Mostro persa, il foglio ancora aperto):
     stesso cambio, niente biglietto nuovo */
  run('p2pIncassoOrdine = ID');
  campo(D.indirizzo);
  await run('inviaCambioP2P()');
  out.riuso = {biglietti: run('server.filter(s => s[0] === "biglietto").length'), swap: lista().length,
               mostro: run('mostro.length'), stessa: run('mostro[1] && mostro[1][2].payment_request[1] === mostro[0][2].payment_request[1]')};
  /* il prezzo cambiato: si dice, si rimostra, non nasce niente */
  run('preventivoServer = Object.assign({}, preventivoServer, {hash: "nuova", ricevi: 98000})');
  run('delete scambi[ID].x; swapLista().forEach(r => { if (r.p2p === ID) r.p2p = ID + "-vecchio"; })');
  run('swapScrivi(swapCasaLista(), swapLista().map(r => Object.assign(r, {p2p: r.p2p === ID ? ID + "-vecchio" : r.p2p})))');
  run('p2pIncassoOrdine = ID');
  campo(D.indirizzo);
  await run('inviaCambioP2P()');
  out.cambiata = [run('elementi.p2pIncassoAvviso.textContent'), run('elementi.p2pCambioConto.innerHTML').includes('98000'),
                  run('server.filter(s => s[0] === "biglietto").length')];
  /* la sentinella: Barattolo non paga, il cambio libero non c'entra, il telefono parla solo col cartone */
  out.sentinella = {paga: run('server.filter(s => s[0] === "paga").length'),
                    libero: run('server.filter(s => s[0] === "cambio-libero").length'),
                    fuori: chiamate.filter(c => !c.url.startsWith(BASE)).map(c => c.url)};
  /* il rilascio: Mostro paga, il cartone blocca i bitcoin, la sorveglianza li ritira */
  run('swapScrivi(swapCasaLista(), swapLista().map(r => Object.assign(r, {p2p: r.p2p === ID + "-vecchio" ? ID : r.p2p})))');
  await stato(out.swapId, 'transaction.mempool');
  await run('swapGiro()');
  /* il giro partito alla nascita puo' essere ancora in volo e ritirare
     lui: si aspetta l'esito, chiunque l'abbia fatto */
  const quello = () => lista().find(r => r.id === out.swapId) || {};
  await finche(() => (quello().ritiro || {}).txid || quello().errore);
  const dopo = quello();
  out.ritiro = {txid: !!(dopo && dopo.ritiro && dopo.ritiro.txid), errore: (dopo && dopo.errore) || '',
                frase: run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(out.swapId) + '))')};
  /* nella lista della pagina «Cambio» si chiama «Scambio P2P» */
  run("elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}; elementi.swapCambio = {innerHTML: ''};");
  run('renderSwapTelefono()');
  out.lista = run('elementi.swapTelefono.innerHTML').includes('<b>Scambio P2P</b>');
  console.log(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def telefono(base, prev):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="cambio_p2p_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "indirizzo": INDIRIZZO, "scambio": SCAMBIO, "preventivo": prev,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "bitcoin",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000,
                     "mempool": base + "/esplora",
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


def il_telefono(c, base):
    print("\n[il telefono: il foglio, «Invia», la fattura del cambio a Mostro, il ritiro]")
    prev = preventivo(c, 999, 100_000)[1]
    r = telefono(base, prev)
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return ""
    prova("il foglio col cambio solo a chi compra, prima del rilascio o dopo un pagamento "
          "fallito, con le due leve accese", [True, False, False, True, False, False, True], r["cancello"])
    prova("la scelta della rete: «⚡ Lightning» e «₿ On-chain», quella scelta premuta",
          {"ln": True, "oc": True, "premuto": True}, r["scelta"])
    prova("il foglio on-chain: la cifra di Mostro, «Calcolo…» finche' non c'e' il conto, il "
          "costo a carico di chi sceglie, l'avviso del bot, il campo e «Invia»",
          {"calcolo": True, "cifra": True, "campo": True, "invia": True, "costo": True, "bot": True},
          r["foglioPrima"])
    prova("...a cifra ignota niente cambio", True, r["senzaCifra"])
    prova("«Invia» senza preventivo: aspetta, e al server non va niente",
          ["Aspetta un attimo: sto calcolando quanto ricevi.", 0], r["senzaPreventivo"])
    prova("il conto: quanto arriva e il costo del cambio, dalla rotta del preventivo P2P",
          ("Ricevi circa <b>98842 sats</b> sul tuo indirizzo bitcoin · costo dello swap 1158 sats.",
           [{"sats": 100_000, "fornitore": "satsrouting", "hash": ""}]),
          (r["conto"], r["preventivoChiesto"]))
    prova("i no prima di tutto: senza indirizzo, indirizzo storto (niente biglietto, niente Mostro)",
          ["Prima scrivi il tuo indirizzo bitcoin.", ["Questo non è un indirizzo bitcoin valido.", 0, 0]],
          [r["senzaIndirizzo"], r["indirizzoNo"]])
    prova("le 12 parole senza una copia fuori dal telefono non fermano piu' il cambio "
          "(2 nov 2026 sera: stanno nel Profilo, nessun avviso)", False, r["paroleNo"])
    n = r["nato"]
    prova("«Invia»: PRIMA il biglietto (lo scambio, la cifra, il fornitore), poi lo swap al "
          "cartone, poi la nascita col biglietto",
          (["biglietto", "nato"], {"ordine": SCAMBIO, "sats": 100_000, "fornitore": "satsrouting"}),
          (n["ordini"], n["biglietto"]))
    prova("...a Mostro parte l'`add-invoice` con LA FATTURA DEL CAMBIO, della cifra esatta",
          ([SCAMBIO, "add-invoice", True], 100_000), (n["mostro"], n["importo"]))
    prova("...il record e' dello scambio, non di un ordine: chiave dal wallet di Barattolo, "
          "l'indirizzo scritto, il biglietto, nessun pagamento",
          {"p2p": SCAMBIO, "ordine": "nessuno", "indirizzo": INDIRIZZO, "seme": "onchain",
           "biglietto": 71, "pagamento": ""}, n["record"])
    prova("...la nascita al server: le sole parti pubbliche", True,
          bool(n["natoPubblico"]) and set(n["natoPubblico"]) == {"swap_id", "impronta", "indirizzo", "onchain"}
          and len(n["natoPubblico"]["impronta"]) == 64)
    prova("...il tentativo segnato, il foglio chiuso, l'avviso «Fatto»",
          (["fattura_inviata"], "p2pIncassoSheet", "₿ Fatto: al rilascio i bitcoin arrivano al tuo indirizzo"),
          (n["tentativi"], n["chiuso"], n["avviso"]))
    prova("...`swapDiP2P` lo ritrova; non e' il cambio libero ne' l'«ordine 0»",
          (True, None, False), (n["diP2P"], n["cambioLibero"], n["ordine0"]))
    prova("un secondo «Invia»: lo STESSO cambio e la stessa fattura, niente biglietto nuovo",
          {"biglietti": 1, "swap": 1, "mostro": 2, "stessa": True}, r["riuso"])
    prova("le tariffe mosse alla conferma: si dice, il conto nuovo si vede, nessun biglietto",
          ["Il costo dello swap è appena cambiato: guarda le cifre nuove e tocca di nuovo «Invia».", True, 1],
          r["cambiata"])
    prova("la sentinella: Barattolo non paga, il cambio libero non si tocca, il telefono parla "
          "solo col cartone", {"paga": 0, "libero": 0, "fuori": []}, r["sentinella"])
    prova("il rilascio: i bitcoin bloccati, la sorveglianza li ritira all'indirizzo",
          {"txid": True, "errore": ""}, {k: r["ritiro"][k] for k in ("txid", "errore")})
    prova("nella lista della pagina «Cambio» si chiama «Scambio P2P»", True, r["lista"])
    return r.get("swapId") or ""


def la_ronda(c, swap_id):
    print("\n[la ronda dell'avviso, sullo swap nato nel telefono]")
    srv = banco.SRV
    avvisi = []

    async def notifica_finta(tg_id, testo, bottone=None):
        avvisi.append((tg_id, testo, bottone))
        return "telegram"
    vera = srv.notifica
    srv.notifica = notifica_finta
    try:
        _, b = biglietto(c, 999, 100_000)
        nato(c, 999, b["id"], swap_id, onchain=99_076)
        cartone(f"/cartone/stato?id={swap_id}&s=swap.created")
        prova("swap nato, bitcoin non ancora bloccati: nessun avviso", 0,
              asyncio.run(srv.ronda_cambi_p2p()))
        cartone(f"/cartone/stato?id={swap_id}&s=transaction.mempool")
        prova("bitcoin bloccati: UN avviso", 1, asyncio.run(srv.ronda_cambi_p2p()))
        tg, testo, bott = avvisi[-1] if avvisi else (0, "", None)
        prova("...a chi deve ritirare, coi sats, e il bottone sullo scambio",
              (999, True, True, (srv.P2P_BOTTONE_RITIRO, f"{srv.URL_PUBBLICO}/p2p?scambio={SCAMBIO}")),
              (tg, testo.startswith("₿ I bitcoin del tuo scambio P2P sono pronti (99.076 sats)."),
               "Apri Barattolo per ritirarli" in testo, bott))
        cartone(f"/cartone/stato?id={swap_id}&s=transaction.confirmed")
        prova("...confermati: niente secondo avviso", 0, asyncio.run(srv.ronda_cambi_p2p()))
        cartone(f"/cartone/stato?id={swap_id}&s=invoice.settled")
        asyncio.run(srv.ronda_cambi_p2p())
        con = srv.db()
        r = con.execute("SELECT stato, visto, avvisato FROM cambi_p2p WHERE id=?", (b["id"],)).fetchone()
        con.close()
        prova("cambio finito: la riga si chiude", ("finito", "invoice.settled", 1), tuple(r))
        visto = cartone("/cartone/visto")
        prima = visto.get("letture", 0)
        asyncio.run(srv.ronda_cambi_p2p())
        prova("...e la ronda non chiama piu' il fornitore", prima,
              cartone("/cartone/visto").get("letture", 0))
        prova("in tutto un avviso solo", 1, len(avvisi))
    finally:
        srv.notifica = vera


def main():
    global PORTA
    print("=" * 58)
    print("  ₿ IL CAMBIO DI CHI COMPRA SU UN ORDINE P2P LIGHTNING")
    print("=" * 58)
    banco.avvio()
    import httpx
    from fastapi.testclient import TestClient

    srv = banco.SRV
    srv.httpx = httpx
    _, PORTA = cartone_satsrouting.avvia(0)
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_MIN_SATS = 25_000
    srv.SWAP_MAX_SATS = 50_000          # il tetto dell'INCASSO: qui non conta
    srv.SWAP_FEE_PERCENTO = 0
    srv.SWAP_API_BASE = f"http://127.0.0.1:{PORTA}"
    srv.SWAP_REFERRAL_ID = "barattolo"
    srv.P2P_ALTRA_RETE_ATTIVO = True
    srv.P2P_ALTRA_RETE_SOLO_MODERATORI = True
    srv.P2P_ALTRA_RETE_MAX_SATS = 500_000
    c = TestClient(srv.app)
    giro(c)
    swap_id = il_telefono(c, f"http://127.0.0.1:{PORTA}")
    if swap_id:
        la_ronda(c, swap_id)
    else:
        prova("il telefono ha fatto nascere uno swap per la ronda", True, False)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
