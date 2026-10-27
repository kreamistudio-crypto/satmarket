# -*- coding: utf-8 -*-
"""
IL CAMBIO LIBERO, TAPPA 2: IL BIGLIETTO E IL PREVENTIVO, SUL SERVER VERO
(27 ott 2026, cantiere cambio-libero, piano approvato da Andrea).

`prove.py` gira i pezzi puri (la cifra, il conto del giorno, il tetto).
Qui la STORIA per HTTP (TestClient, la app vera) contro il SATS ROUTING
DI CARTONE acceso su una porta di questo computer, coi tetti di Andrea:
500.000 sats per cambio, 5 cambi al giorno, all'inizio solo moderatori.

LE SCENE:
  - il cancello: in `/api/me` il 999 ha la busta del cambio (tetti,
    strade, quanti oggi), il 222 no; la porta del preventivo glielo dice;
  - il preventivo di 100.000 sats: le righe (cambi, costo del cambio,
    le due reti), quanto ricevi, la busta del giorno;
  - i rifiuti del preventivo: cifra assente, sopra il tetto, sotto il
    minimo, SATS Routing giu';
  - il biglietto: cinque in fila, il sesto dice «tetto_giorno», e anche
    il preventivo; un biglietto annullato libera il posto; i rifiuti del
    biglietto (direzione, fornitore, cifra);
  - la nascita: le parti pubbliche, idempotente sullo stesso swap, lo
    stesso swap su due biglietti e' «doppio», il biglietto di un altro
    e' 404, un biglietto annullato non nasce;
  - le leve: aperta a tutti, spenta (403 e `attivo: False`), e senza lo
    swap sotto non c'e' il cambio.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1; nessuno swap vero, nessun sats: la fattura, quando ci sara',
la paga l'utente col SUO wallet.

USO:  python collaudo_cambio_libero.py
"""
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
IMPRONTA = "ab" * 32


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def modo(m):
    cartone(f"/cartone/modo?m={m}")
    banco.SRV._TARIFFE_SWAP.update(quando=0.0, dati=None)   # niente copia


def semina():
    con = banco.SRV.db()
    for tg, nome in ((999, "Admin"), (222, "Vende")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    con.execute("DROP TABLE IF EXISTS cambi_liberi")
    con.commit()
    con.close()


def leve(c, chi):
    banco.come(chi, admin=(chi == 999))
    r = c.get("/api/me", headers=TESTE[chi])
    return ((r.json() or {}).get("swap_leve") or {}).get("cambio") or {}


def preventivo(c, chi, sats, **extra):
    banco.come(chi, admin=(chi == 999))
    q = "&".join(f"{k}={v}" for k, v in dict(sats=sats, **extra).items())
    r = c.get(f"/api/swap/cambio/preventivo?{q}", headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def biglietto(c, chi, sats, **extra):
    banco.come(chi, admin=(chi == 999))
    corpo = dict({"direzione": "ln-btc", "sats": sats, "fornitore": "satsrouting"}, **extra)
    r = c.post("/api/swap/cambio", json=corpo, headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def nato(c, chi, cid, swap_id, **extra):
    banco.come(chi, admin=(chi == 999))
    corpo = dict({"swap_id": swap_id, "impronta": IMPRONTA,
                  "indirizzo": "bcrt1qcartone", "onchain": 99_000}, **extra)
    r = c.post(f"/api/swap/cambio/{cid}/nato", json=corpo, headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def annulla(c, chi, cid):
    banco.come(chi, admin=(chi == 999))
    r = c.post(f"/api/swap/cambio/{cid}/annulla", headers=TESTE[chi])
    return r.status_code, (r.json() if r.content else {})


def giro(c):
    srv = banco.SRV
    semina()
    modo("normale")

    print("\n[il cancello per persona]")
    l999, l222 = leve(c, 999), leve(c, 222)
    prova("a solo-moderatori il 999 ha il cambio, coi tetti di Andrea",
          (True, 25_000, 500_000, 5, 0, ["ln-btc"]),
          (l999.get("attivo"), l999.get("minimo"), l999.get("massimo"),
           l999.get("al_giorno"), l999.get("oggi"), l999.get("strade")))
    prova("...il 222 no", False, l222.get("attivo"))
    prova("...e la porta del preventivo glielo dice", 403,
          preventivo(c, 222, 100_000)[0])
    prova("...e quella del biglietto pure", 403, biglietto(c, 222, 100_000)[0])

    print("\n[il preventivo di 100.000 sats]")
    codice, p = preventivo(c, 999, 100_000)
    prova("risponde col conto e con la busta del giorno",
          (200, True, 100_000, "ln-btc", 0, 5, "SATS Routing"),
          (codice, p.get("ok"), p.get("dovuto"), p.get("direzione"),
           p.get("oggi"), p.get("al_giorno"), p.get("fornitore_nome")))
    prova("...riga per riga: 0,6 % di cambio, le due reti, nessuna "
          "commissione Barattolo",
          [("dovuto", 100_000), ("commissione", -600),
           ("rete_invio", -324), ("rete_ritiro", -234)],
          [(r["voce"], r["sats"]) for r in p.get("righe", [])])
    prova("...ricevi 98.842", (98_842, "cartone-tariffa-16ott"),
          (p.get("ricevi"), p.get("hash")))
    prova("la cifra con punti e spazi si legge lo stesso", (True, 100_000),
          (lambda s: (s.get("ok"), s.get("dovuto")))(preventivo(c, 999, "100.000")[1]))

    print("\n[i rifiuti del preventivo]")
    _, s = preventivo(c, 999, "")
    prova("senza cifra: «cifra»", (False, "cifra"), (s.get("ok"), s.get("motivo")))
    _, s = preventivo(c, 999, 600_000)
    prova("sopra il tetto del cambio (500.000)", (False, "sopra_tetto", 500_000),
          (s.get("ok"), s.get("motivo"), s.get("massimo")))
    _, s = preventivo(c, 999, 10_000)
    prova("sotto il minimo dello swap", (False, "sotto_minimo", 25_000),
          (s.get("ok"), s.get("motivo"), s.get("minimo")))
    prova("una direzione sconosciuta: 400", 400,
          preventivo(c, 999, 100_000, direzione="btc-ln")[0])
    prova("un fornitore sconosciuto: 404", 404,
          preventivo(c, 999, 100_000, fornitore="pinco")[0])
    modo("giu")
    _, s = preventivo(c, 999, 100_000)
    prova("SATS Routing giu': non risponde", (False, "non_risponde"),
          (s.get("ok"), s.get("motivo")))
    modo("normale")

    print("\n[il biglietto e il tetto del giorno]")
    _, b = biglietto(c, 999, 100_000, direzione="btc-ln")
    prova("una direzione che il server non sa", (False, "direzione"),
          (b.get("ok"), b.get("motivo")))
    _, b = biglietto(c, 999, 100_000, fornitore="pinco")
    prova("un fornitore che non c'e'", (False, "fornitore"),
          (b.get("ok"), b.get("motivo")))
    _, b = biglietto(c, 999, 10_000)
    prova("sotto il minimo", (False, "sotto_minimo"), (b.get("ok"), b.get("motivo")))
    _, b = biglietto(c, 999, 600_000)
    prova("sopra il tetto", (False, "sopra_tetto"), (b.get("ok"), b.get("motivo")))
    _, b = biglietto(c, 999, "")
    prova("senza cifra", (False, "sotto_minimo"), (b.get("ok"), b.get("motivo")))
    presi, ids = [], []
    for _ in range(5):
        codice, b = biglietto(c, 999, 100_000)
        presi.append((codice, b.get("ok"), b.get("oggi")))
        ids.append(b.get("id"))
    prova("cinque biglietti in fila, e il conto del giorno sale",
          [(200, True, n) for n in range(1, 6)], presi)
    _, b = biglietto(c, 999, 100_000)
    prova("il sesto: «tetto_giorno»", (False, "tetto_giorno", 5),
          (b.get("ok"), b.get("motivo"), b.get("oggi")))
    _, s = preventivo(c, 999, 100_000)
    prova("...e lo dice anche il preventivo, prima di far scrivere l'indirizzo",
          (False, "tetto_giorno", 5, 5),
          (s.get("ok"), s.get("motivo"), s.get("oggi"), s.get("al_giorno")))
    prova("...e /api/me", 5, leve(c, 999).get("oggi"))
    codice, a = annulla(c, 999, ids[4])
    prova("un biglietto annullato prima di nascere libera il posto",
          (200, True, "annullato", 4),
          (codice, a.get("ok"), a.get("stato"), leve(c, 999).get("oggi")))
    _, a = annulla(c, 999, ids[4])
    prova("...e non si annulla due volte", (False, "annullato"),
          (a.get("ok"), a.get("motivo")))
    prova("...e il biglietto di un altro non si annulla: 404 (la nascita e "
          "l'annullo non hanno cancello: un biglietto nato prima di una leva "
          "spenta deve poter finire)", 404, annulla(c, 222, ids[0])[0])
    codice, b = biglietto(c, 999, 100_000)
    prova("il posto liberato si riprende", (200, True, 5),
          (codice, b.get("ok"), b.get("oggi")))
    sesto = b.get("id")

    print("\n[la nascita]")
    codice, n = nato(c, 999, ids[0], "swapcartone01")
    prova("lo swap c'e': il biglietto passa a «nato»", (200, True, "nato"),
          (codice, n.get("ok"), n.get("stato")))
    con = srv.db()
    riga = con.execute("SELECT stato, swap_id, impronta, indirizzo, onchain, "
                       "fornitore FROM cambi_liberi WHERE id=?", (ids[0],)).fetchone()
    con.close()
    prova("...con le sole parti pubbliche",
          ("nato", "swapcartone01", IMPRONTA, "bcrt1qcartone", 99_000, "satsrouting"),
          tuple(riga))
    _, n = nato(c, 999, ids[0], "swapcartone01")
    prova("la stessa nascita due volte: idempotente", (True, "nato"),
          (n.get("ok"), n.get("stato")))
    _, n = nato(c, 999, ids[0], "swapcartone99")
    prova("...ma un altro swap sullo stesso biglietto nato: ok False",
          (False, "nato"), (n.get("ok"), n.get("stato")))
    _, n = nato(c, 999, ids[1], "swapcartone01")
    prova("lo stesso swap su un secondo biglietto: «doppio»", (False, "doppio"),
          (n.get("ok"), n.get("motivo")))
    _, n = nato(c, 999, ids[1], "swap cartone")
    prova("un id dalla forma storta: «forma»", (False, "forma"),
          (n.get("ok"), n.get("motivo")))
    _, n = nato(c, 999, ids[1], "swapcartone02", impronta="zz")
    prova("...e un'impronta storta pure", (False, "forma"),
          (n.get("ok"), n.get("motivo")))
    _, n = nato(c, 999, ids[4], "swapcartone05")
    prova("un biglietto annullato non nasce", (False, "annullato"),
          (n.get("ok"), n.get("motivo")))
    _, a = annulla(c, 999, ids[0])
    prova("un biglietto nato non si annulla", (False, "nato"),
          (a.get("ok"), a.get("motivo")))

    print("\n[il biglietto di un altro]")
    srv.CAMBIO_LIBERO_SOLO_MODERATORI = False
    prova("aperto a tutti ma con lo swap ancora solo-moderatori: il 222 "
          "non ha il cambio (sta SOPRA il cancello dello swap)", False,
          leve(c, 222).get("attivo"))
    srv.SWAP_SOLO_MODERATORI = False
    prova("...aperti tutti e due: il 222 ha il cambio", True,
          leve(c, 222).get("attivo"))
    prova("...ma il biglietto del 999 per lui non esiste: 404 alla nascita "
          "e all'annullo", (404, 404),
          (nato(c, 222, ids[1], "swapcartone02")[0], annulla(c, 222, sesto)[0]))
    codice, b = biglietto(c, 222, 100_000)
    prova("...e il suo conto del giorno e' suo", (200, True, 1),
          (codice, b.get("ok"), b.get("oggi")))
    srv.CAMBIO_LIBERO_SOLO_MODERATORI = True
    srv.SWAP_SOLO_MODERATORI = True

    print("\n[le leve]")
    srv.CAMBIO_LIBERO_ATTIVO = False
    prova("cambio spento: nessuno, nemmeno il moderatore, e lo swap resta",
          (403, 403, False, True),
          (preventivo(c, 999, 100_000)[0], biglietto(c, 999, 100_000)[0],
           leve(c, 999).get("attivo"),
           (lambda: (banco.come(999, admin=True),
                     c.get("/api/me", headers=TESTE[999]).json()
                     ["swap_leve"]["attivo"])[1])()))
    srv.CAMBIO_LIBERO_ATTIVO = True
    srv.SWAP_ATTIVO = False
    prova("senza lo swap sotto non c'e' il cambio", (403, False),
          (preventivo(c, 999, 100_000)[0], leve(c, 999).get("attivo")))
    srv.SWAP_ATTIVO = True
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)
    prova("il cartone non ha visto nessuno swap", 0,
          cartone("/cartone/visto").get("swap", 0))



# ──────────────────────────────────────────────────────────────────────
# IL TELEFONO: il codice VERO dell'instradatore e del tipo (swap/*.js),
# coi pezzi veri della pagina (SWAP_TESTI, pannelloPreventivoSwap, la
# lettura delle fatture), girato in node contro il cartone. Le tre
# chiamate al server di Barattolo (biglietto, nascita, annullo) sono
# finte e CONTATE: qui si guarda che il telefono le faccia nell'ordine
# giusto, con le sole parti pubbliche; il server vero sta sopra.
# ──────────────────────────────────────────────────────────────────────
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"


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
        tra("function testiSwap(){", "\n"), tra("function percentoSwap(p){"),
        tra("function etichettaVoceSwap(r, t, fornitore){"),
        tra("function pannelloPreventivoSwap(o, campo){"),
        tra("function ridisegnaIncassoSwap(){")])


BANCO_TELEFONO = r"""
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
const memoria = new Map();
const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL,
  Uint8Array, BigInt, setTimeout, clearTimeout, Promise, JSON, Date, Math,
  fetch: async (url, opz) => {
    chiamate.push({url: String(url), metodo: (opz && opz.method) || 'GET',
                   corpo: String((opz && opz.body) || '')});
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
/* LE TRE CHIAMATE AL SERVER DI BARATTOLO, finte e contate */
const server = [];
let bigliettoRisposta = {ok: true, id: 41, oggi: 1};
let tettoGiornoFinto = false;
async function chiediBigliettoCambio(d){ server.push(['biglietto', d]); return bigliettoRisposta; }
async function natoCambioAlServer(id, rec){ server.push(['nato', id, {swap_id: rec.id, impronta: rec.impronta, indirizzo: rec.lockupAddress, onchain: rec.onchainAmount, chiavi: Object.keys(rec).sort()}]); return {ok: true, stato: 'nato'}; }
async function liberaBigliettoCambio(id){ server.push(['annulla', id]); return {ok: true}; }
async function pagaSwapAlServer(rec){ server.push(['paga', rec.ordine]); return null; }
async function statoPagamentoSwap(){ return null; }
/* il preventivo: la rotta del cambio per l'ordine 0, contata */
const preventivi = [];
async function leggiPreventivoSwap(n, fornitore, hash){
  const sats = Number(n) === 0 ? swapCambioCifra() : 48000;
  preventivi.push({n, fornitore, hash, sats});
  if (Number(n) === 0 && !sats) return {ok: false, motivo: 'cifra', oggi: 1, al_giorno: 5};
  if (Number(n) === 0 && tettoGiornoFinto) return {ok: false, motivo: 'tetto_giorno', oggi: 5, al_giorno: 5, fornitore_nome: 'SATS Routing'};
  const comm = Math.ceil(sats * 6 / 1000), onchain = sats - comm - 324;
  return {ok: true, hash: 'cartone-tariffa-16ott', dovuto: sats, fattura: sats, onchain,
          ricevi: onchain - 234, valido_s: 60, oggi: 1, al_giorno: 5, direzione: 'ln-btc',
          fornitore: fornitore || 'satsrouting', fornitore_nome: 'SATS Routing',
          righe: [{voce: 'dovuto', sats}, {voce: 'commissione', sats: -comm, percento: 0.6},
                  {voce: 'rete_invio', sats: -324}, {voce: 'rete_ritiro', sats: -234}]};
}
const qr = [], wallet = [];
async function disegnaQr(box, testo, modo){ qr.push([box && box.id, testo.slice(0, 12), modo]); box.classList.add('pronto'); return true; }
function portaWallet(a, inv){ wallet.push([a && a.id, String(inv).slice(0, 4)]); }
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const ascoltatori = [];
const document = {addEventListener: (t, f) => ascoltatori.push([t, f]),
                  head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
`, Object.assign(ctx, {__memoria: memoria}));
vm.runInContext(D.pagina, ctx);
for (const codice of TELEFONO) vm.runInContext(codice, ctx);
const run = c => vm.runInContext(c, ctx);
const box = () => run('elementi.swapCambio.innerHTML');
const lista = () => JSON.parse(memoria.get('barattolo_swap_lista_999') || '[]');

(async () => {
  const out = {};
  const server = () => run('server'), preventivi = () => run('preventivi'), qr = () => run('qr'), wallet = () => run('wallet');
  run("elementi.swapCambio = {innerHTML: ''}; elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}};");
  // --- a leva del cambio spenta: niente, nemmeno il tasto
  run('swapLeve.cambio.attivo = false'); run('renderSwapCambio()');
  out.spento = box();
  run('swapLeve.cambio.attivo = true'); run('renderSwapCambio()');
  out.chiuso = box();
  // --- aperto: la direzione, la cifra, i tetti del giorno
  run('swapCambioApri()');
  const f1 = box();
  out.aperto = {tasto: f1.includes('data-swap="cambio-calcola"'), campo: f1.includes('id="swapCambioCifra_0"'),
                pillole: (f1.match(/data-swap="cambio-strada"/g) || []).length,
                tra: f1.includes('Da 25000 a 500000 sats') , oggi: f1.includes('Oggi: 0 di 5'),
                chiudi: f1.includes('data-swap="cambio-chiudi"'), titolo: f1.includes('Cambia i tuoi sats')};
  // --- senza cifra non si chiede niente
  run("elementi.swapCambioCifra_0 = {value: ''}");
  await run('swapCambioCalcola()');
  out.senzaCifra = [box().includes('Scrivi quanti sats vuoi cambiare.'), preventivi().length];
  // --- 100.000: il preventivo del cambio, con le parole del cambio
  run("elementi.swapCambioCifra_0 = {value: '100.000'}");
  await run('swapCambioCalcola()');
  const f2 = box();
  out.preventivo = {letto: preventivi()[0], cambi: f2.includes('<span>Cambi</span><b>100000</b>'),
                    spettano: f2.includes('Ti spettano'), ricevi: f2.includes('<b>98842<span class="unit">sats</span></b>'),
                    incassaLn: f2.includes('Incassa in Lightning'), campo: f2.includes('id="swapIndirizzo_0"'),
                    conferma: f2.includes('data-swap="avanti" data-ordine="0"'), calcola: f2.includes('data-swap="cambio-calcola"')};
  // --- «Conferma» senza indirizzo: lo dice, niente biglietto
  await run('swapAvanti(0)');
  out.senzaIndirizzo = [run("swapErrori[0] || ''"), server().length];
  // --- con l'indirizzo: la prima volta le parole, poi «Continua»
  run(`elementi.swapIndirizzo_0 = {value: '${D.indirizzo}'}`);
  await run('swapAvanti(0)');
  out.parole = [run("swapPassi[0] || ''"), box().includes('class="swap-parole"'), box().includes('pagina «Cambio»'), server().length];
  run("elementi.swapSpunta_0 = {checked: true}");
  const vPrima = await visto();
  await run('swapParoleFatte(0)');
  const vDopo = await visto();
  const l1 = lista();
  const r1 = l1[0] || {};
  out.nato = {ordini: server().map(s => s[0]), biglietto: server()[0] && server()[0][1],
              natoId: server()[1] && server()[1][1], natoPubblico: server()[1] && server()[1][2],
              swap: vDopo.swap - vPrima.swap, record: {ordine: r1.ordine, cambio: r1.cambio, indice: r1.indice, pagamento: r1.pagamento},
              referral: vDopo.creazione && vDopo.creazione.referralId, importo: vDopo.creazione && vDopo.creazione.invoiceAmount,
              bigliettoPrimaDiCreare: chiamate.findIndex(c => c.url.endsWith('/v2/swap/reverse') && c.metodo === 'POST') >= 0};
  // --- la carta: QR, «Copia», «Apri nel wallet», la fattura la paga lui
  const f3 = box();
  out.carta = {qr: qr()[0], wallet: wallet()[0], copia: f3.includes('data-swap="cambio-copia"'),
               paghi: f3.includes('Paga questa richiesta col tuo wallet Lightning'), cambio: f3.includes('<h4>🔁 Cambio</h4>'),
               apri: f3.includes('href="lightning:lnbc'), vale: f3.includes('Vale fino alle')};
  run("elementi.swapCambioQr = {id: 'swapCambioQr', classList: {add(){}}}; elementi.swapCambioWallet = {id: 'swapCambioWallet'}");
  run('renderSwapCambio()');
  out.cartaDisegnata = {qr: qr()[qr().length - 1], wallet: wallet()[wallet().length - 1]};
  /* «Copia» mette la fattura negli appunti */
  run("navigator = {clipboard: {writeText: async t => { avvisi.push('APPUNTI:' + t.slice(0, 4)); }}}");
  await run(`swapCambioCopia(${JSON.stringify(r1.id)})`);
  out.copia = run('avvisi.slice(-2)');
  // --- la lista della pagina lo chiama «Cambio», e la frase e' la sua
  run('renderSwapTelefono()');
  const pag = run('elementi.swapTelefono.innerHTML');
  out.pagina = {cambio: pag.includes('<b>Cambio</b>'), frase: run('frasestatoSwap(swapLista()[0])'),
                vuotoNascosto: run("elementi.swapVuoto.style.display")};
  // --- un secondo cambio mentre il primo e' vivo: il riquadro mostra il primo
  run('swapCambioApri()');
  out.secondoMentreVivo = box().includes('data-swap="cambio-copia"');
  // --- a cambio pagato e finito, il riquadro torna al tasto
  const l2 = lista(); l2[0].stato = 'invoice.settled'; l2[0].ritiro = {txid: 'a'.repeat(64), concluso: true, sats: 98842};
  memoria.set('barattolo_swap_lista_999', JSON.stringify(l2));
  run('swapCambioChiudi()');
  out.finito = box().includes('data-swap="cambia"');
  // --- il biglietto rifiutato (tetto del giorno): niente swap chiesto
  run('bigliettoRisposta = {ok: false, motivo: "tetto_giorno"}');
  run('swapCambioApri()');
  run("elementi.swapCambioCifra_0 = {value: '100000'}");
  await run('swapCambioCalcola()');
  run(`elementi.swapIndirizzo_0 = {value: '${D.indirizzo}'}`);
  const sPrima = server().length, vP2 = await visto();
  await run('swapAvanti(0)');
  const vD2 = await visto();
  out.tettoGiorno = {errore: run("swapErrori[0] || ''"), passo: run("swapPassi[0] || 'preventivo'"),
                     swap: vD2.swap - vP2.swap, server: server().slice(sPrima).map(s => s[0]),
                     mostrato: box().includes('Per oggi hai fatto i 5 cambi possibili'), indice: JSON.parse(memoria.get('barattolo_swap_999')).prossimo};
  // --- il fornitore non risponde dopo il biglietto: l'annullo
  run('bigliettoRisposta = {ok: true, id: 42, oggi: 2}');
  await modo('giu');
  const sPrima3 = server().length;
  await run('swapAvanti(0)');
  out.annullo = {server: server().slice(sPrima3).map(s => s[0] + (s[0] === 'annulla' ? ':' + s[1] : '')), errore: run("swapErrori[0] || ''"),
                 quanti: lista().length};
  await modo('normale');
  // --- la sentinella: il telefono ha chiamato solo il cartone
  out.sentinella = {fuori: chiamate.filter(c => !c.url.startsWith(BASE + '/v2/') && !c.url.startsWith(BASE + '/esplora/')).map(c => c.url),
                    paga: server().filter(s => s[0] === 'paga').length};
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def telefono(base, tetto_giorno=False):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="cambio_libero_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO_TELEFONO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "indirizzo": INDIRIZZO, "tettoGiorno": tetto_giorno,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "bitcoin",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000,
                     "mempool": base + "/esplora",
                     "cambio": {"attivo": True, "minimo": 25_000, "massimo": 500_000,
                                "al_giorno": 5, "oggi": 0, "strade": ["ln-btc"]}}}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1500:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def il_telefono(base):
    print("\n[il telefono: il tasto, la cifra, il preventivo, la fattura]")
    r = telefono(base)
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return
    prova("a leva del cambio spenta il riquadro e' vuoto; accesa, il tasto «🔁 Cambia»",
          ("", True), (r["spento"], r["chiuso"].endswith('data-swap="cambia">🔁 Cambia</button>')))
    prova("aperto: la cifra, una direzione sola (per ora), i tetti e il conto del giorno, «Chiudi»",
          {"tasto": True, "campo": True, "pillole": 1, "tra": True, "oggi": True,
           "chiudi": True, "titolo": True}, r["aperto"])
    prova("senza cifra: lo dice e non chiede niente", [True, 0], r["senzaCifra"])
    prova("100.000 (coi punti): la rotta del cambio, la riga «Cambi» e non «Ti spettano», "
          "ricevi 98.842, niente «Incassa in Lightning», l'indirizzo e «Conferma»",
          {"letto": {"n": 0, "fornitore": "satsrouting", "hash": "", "sats": 100_000},
           "cambi": True, "spettano": False, "ricevi": True, "incassaLn": False,
           "campo": True, "conferma": True, "calcola": False}, r["preventivo"])
    prova("«Conferma» senza indirizzo: lo dice, e al server non va niente",
          ["Prima metti il tuo indirizzo bitcoin: tocca «Incolla».", 0], r["senzaIndirizzo"])
    prova("con l'indirizzo, la prima volta le 12 parole (che citano la pagina «Cambio»)",
          ["parole", True, True, 0], r["parole"])
    n = r["nato"]
    prova("«Continua»: PRIMA il biglietto, poi lo swap al cartone, poi la nascita; "
          "mai il pagamento di Barattolo",
          ["biglietto", "nato"], n["ordini"])
    prova("...il biglietto porta direzione, cifra, fornitore e impronta delle tariffe",
          {"direzione": "ln-btc", "sats": 100_000, "fornitore": "satsrouting",
           "hash": "cartone-tariffa-16ott"}, n["biglietto"])
    prova("...lo swap e' nato al cartone, col codice partner e la cifra",
          (1, "barattolo", 100_000, True), (n["swap"], n["referral"], n["importo"],
                                             n["bigliettoPrimaDiCreare"]))
    prova("...la nascita porta le sole parti pubbliche, sul biglietto 41",
          (41, True, True, True, True),
          (n["natoId"], n["natoPubblico"]["swap_id"] == n["natoPubblico"]["swap_id"] and
           bool(n["natoPubblico"]["swap_id"]), len(n["natoPubblico"]["impronta"]) == 64,
           bool(n["natoPubblico"]["indirizzo"]), n["natoPubblico"]["onchain"] == 99_076))
    prova("...e il record e' dell'«ordine 0», col biglietto, senza pagamento",
          {"ordine": 0, "cambio": 41, "indice": 0, "pagamento": ""}, n["record"])
    c = r["carta"]
    prova("la carta: «🔁 Cambio», la fattura da pagare col SUO wallet, «Copia», "
          "«Apri nel wallet», «Vale fino alle»",
          (True, True, True, True, True), (c["cambio"], c["paghi"], c["copia"], c["apri"], c["vale"]))
    prova("...il QR della fattura (alfanumerico, LIGHTNING: maiuscolo) e il wallet",
          {"qr": ["swapCambioQr", "LIGHTNING:LN", "Alphanumeric"], "wallet": ["swapCambioWallet", "lnbc"]},
          r["cartaDisegnata"])
    prova("«Copia» mette la fattura negli appunti e lo dice", ["APPUNTI:lnbc", "Copiata"], r["copia"])
    prova("nella lista della pagina si chiama «Cambio», con la frase sua",
          (True, True, "none"), (r["pagina"]["cambio"],
                                 r["pagina"]["frase"].startswith("Paga questa richiesta col tuo wallet Lightning"),
                                 r["pagina"]["vuotoNascosto"]))
    prova("un secondo cambio mentre il primo aspetta: si vede il primo", True, r["secondoMentreVivo"])
    prova("a cambio finito il riquadro torna al tasto", True, r["finito"])
    t = r["tettoGiorno"]
    prova("il biglietto rifiutato (tetto del giorno): lo dice, niente swap chiesto, "
          "l'indice della chiave resta bruciato",
          {"errore": "Per oggi hai fatto i 5 cambi possibili: riprova domani.", "passo": "preventivo",
           "swap": 0, "server": ["biglietto"], "mostrato": True, "indice": 2}, t)
    prova("il fornitore giu' DOPO il biglietto: l'annullo, e niente in lista",
          {"server": ["biglietto", "annulla:42"], "errore": "SATS Routing ora non risponde: riprova fra poco.",
           "quanti": 1}, r["annullo"])
    prova("la sentinella: il telefono parla solo col cartone, e Barattolo non paga mai",
          {"fuori": [], "paga": 0}, r["sentinella"])

def main():
    global PORTA
    print("=" * 58)
    print("  🔁 IL CAMBIO LIBERO, TAPPA 2 — il biglietto, il giro vero")
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
    srv.CAMBIO_LIBERO_ATTIVO = True
    srv.CAMBIO_LIBERO_SOLO_MODERATORI = True
    srv.CAMBIO_LIBERO_MAX_SATS = 500_000
    srv.CAMBIO_LIBERO_MAX_AL_GIORNO = 5
    giro(TestClient(srv.app))
    il_telefono(f"http://127.0.0.1:{PORTA}")

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
