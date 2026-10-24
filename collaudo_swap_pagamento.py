# -*- coding: utf-8 -*-
"""
LO SWAP, TAPPA 4: BARATTOLO PAGA LA FATTURA DELLO SWAP (24 ott 2026,
cantiere swap-tappa-4).

Lo swap INTERO, coi pezzi veri: il codice del telefono (`swap/boltz.js`,
`swap/instradatore.js`, e le funzioni della pagina che parlano col server:
il preventivo, `pagaSwapAlServer`, `statoPagamentoSwap`) girato in node;
il SERVER VERO (le rotte, `paga_venditore`, la ronda dei pagamenti in volo)
dietro un ponte HTTP di questo computer; il SATS ROUTING DI CARTONE col suo
finto mempool (lista delle transazioni, transazione, spesa, altezza); e un
LNbits di cartone che fa quel che fa una fattura di swap: resta IN VOLO
finche' il fornitore non la chiude, cioe' finche' il telefono non ha
ritirato i bitcoin.

LE SCENE:
  - lo swap intero: preventivo, parole, swap creato e verificato, le sole
    parti pubbliche al server, i controlli, la riga registrata PRIMA del
    pagamento, il pagamento in volo, il lockup, il ritiro, la fattura che
    si chiude, l'ordine chiuso, «Fatto»;
  - la risposta del nodo mancata: in volo, il telefono che riapre e
    richiede (nessun secondo pagamento), mezz'ora passata senza 🧊 (la
    fattura di uno swap vola fino alla scadenza), poi la scadenza: 🧊 e
    «Pagamento da verificare»;
  - IL CASO DEL #241: un pagamento fallito con zero tentativi, poi pagato a
    mano: lo swap nuovo dello stesso ordine NON si paga, l'ordine si chiude
    col pagamento di prima;
  - i controlli prima di pagare, ognuno col suo no e nessun sats uscito:
    la forma, l'impronta, l'indirizzo (un altro tipo, un checksum rotto),
    l'importo, la scadenza, un on-chain meno del dichiarato, la fee
    accesa, le tariffe che non arrivano, il mempool giu (e il telefono che
    riprovera'), l'indirizzo del lockup gia' usato, la leva spenta;
  - i tetti: per chi vende, per tutti, e il pagamento che passa a tetto
    alzato;
  - il doppio tocco: due richieste insieme, un pagamento solo;
  - il journal: una riga per passo, nessuna fattura intera, nessuna parola;
  - LA SENTINELLA: al server solo le sette parti pubbliche.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1 (in CI la gabbia di `collaudi_ci.py`); nessun sats: i pagamenti
li «fa» il LNbits di cartone, i bitcoin «bloccati» sono una transazione
inventata dal cartone.

USO:  python collaudo_swap_pagamento.py
"""
import asyncio
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import collaudo_lnbits_muto as banco
import cartone_satsrouting

prova = banco.prova
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
CARTONE = ""
SRV = None

# --- IL LNBITS DI CARTONE, con le fatture trattenute -------------------
# `prossimo` e' come finisce la PROSSIMA richiesta di pagamento: pending
# (la fattura di uno swap: resta in volo), success, failed (il caso del
# #241: zero tentativi), timeout (il nodo non risponde in tempo).
ESITO = {"prossimo": "pending"}
PAGAMENTI = {}        # hash -> stato, come lo direbbe LNbits
USCITE = []           # l'hash di ogni richiesta di pagamento


class _Risposta:
    def __init__(self, codice, corpo):
        self.status_code = codice
        self._corpo = corpo
        self.text = json.dumps(corpo)

    def json(self):
        return self._corpo


def _lnbits_post(url, kw):
    corpo = kw.get("json") or {}
    if "decode" in url:
        b = corpo.get("data", "")
        sats = SRV.importo_bolt11(b)
        letta = SRV.leggi_bolt11(b, con_hash=True)
        if sats is None or not letta:
            return _Risposta(400, {"detail": "non si legge"})
        return _Risposta(200, {"amount_msat": sats * 1000,
                               "payment_hash": letta["hash"]})
    letta = SRV.leggi_bolt11(corpo.get("bolt11", ""), con_hash=True) or {}
    h = letta.get("hash", "")
    USCITE.append(h)
    esito = ESITO["prossimo"]
    if esito == "timeout":
        PAGAMENTI[h] = "pending"
        raise _VERO.ReadTimeout("il nodo di cartone non risponde")
    PAGAMENTI[h] = esito
    return _Risposta(201, {"payment_hash": h, "status": esito})


def _lnbits_get(url):
    h = url.rsplit("/", 1)[-1]
    if h not in PAGAMENTI:
        return _Risposta(404, {})
    s = PAGAMENTI[h]
    return _Risposta(200, {"status": s, "paid": s == "success"})


import httpx as _VERO


class _Misto:
    """httpx per il server: verso il cartone (tariffe e mempool) quello
    VERO, per HTTP; verso LNbits quello di cartone qui sopra."""

    class AsyncClient:
        def __init__(self, **kw):
            self._kw, self._vero = kw, None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            if self._vero is not None:
                await self._vero.aclose()
            return False

        def _di_casa(self, url):
            return CARTONE and str(url).startswith(CARTONE)

        async def _v(self):
            if self._vero is None:
                self._vero = _VERO.AsyncClient(**self._kw)
            return self._vero

        async def get(self, url, **kw):
            if self._di_casa(url):
                return await (await self._v()).get(url, **kw)
            return _lnbits_get(url)

        async def post(self, url, **kw):
            if self._di_casa(url):
                return await (await self._v()).post(url, **kw)
            return _lnbits_post(url, kw)


for _n in dir(_VERO):
    if not _n.startswith("_") and not hasattr(_Misto, _n):
        setattr(_Misto, _n, getattr(_VERO, _n))


# --- IL JOURNAL: tutto quel che il server stampa -------------------------
class _Tee(io.TextIOBase):
    def __init__(self, vero):
        self.vero, self.righe = vero, []

    def write(self, s):
        self.righe.append(s)
        return self.vero.write(s)

    def flush(self):
        self.vero.flush()


# --- IL PONTE: il server vero raggiungibile dal telefono in node ---------
def _gira(coro):
    return asyncio.run(coro)


def _ordine(oid):
    o = banco.riga(oid)
    return {"stato": o["stato"], "payout_stato": o["payout_stato"] or "",
            "payout_hash": o["payout_hash"] or "",
            "invoice": bool(o["invoice_venditore"])}


def _righe(oid):
    SRV._swap_pag_dell_ordine(oid)
    con = SRV._swap_pag_db()
    try:
        return [{"stato": r["stato"], "hash": r["hash"], "sats": r["sats"],
                 "lungo": r["vola_fino"] - r["creato"] > SRV.IN_VOLO_LIMITE_S}
                for r in con.execute("SELECT * FROM swap_pagamenti WHERE "
                                     "ordine_id=? ORDER BY id", (oid,))]
    finally:
        con.close()


def _leva(nome, v):
    vecchio = getattr(SRV, nome)
    if isinstance(vecchio, bool):
        v = v in ("1", "true", "True")
    elif isinstance(vecchio, (int, float)):
        v = float(v) if "." in v else int(v)
    setattr(SRV, nome, v)
    return {nome: v}


def _controllo(cosa, q):
    a = {k: v[0] for k, v in q.items()}
    if cosa == "post":
        ESITO["prossimo"] = a["esito"]
        return ESITO
    if cosa == "lnbits":
        PAGAMENTI[a["h"]] = a["s"]
        return {"ok": True}
    if cosa == "ronda":
        _gira(SRV.risolvi_pagamenti_in_volo())
        SRV.swap_pagamenti_ripassa()
        return {"ok": True}
    if cosa == "ordine":
        return _ordine(int(a["id"]))
    if cosa == "righe":
        return _righe(int(a["ordine"]))
    if cosa == "uscite":
        return {"tutte": len(USCITE), "per": a.get("h") and USCITE.count(a["h"])}
    if cosa == "invecchia":
        con = SRV.db()
        con.execute("UPDATE ordini SET payout_ultimo=payout_ultimo-7200 "
                    "WHERE id=?", (int(a["ordine"]),))
        if a.get("cosa") == "scadenza":
            con.execute("UPDATE swap_pagamenti SET vola_fino=1 WHERE "
                        "ordine_id=?", (int(a["ordine"]),))
        con.commit()
        con.close()
        return {"ok": True}
    if cosa == "leva":
        return _leva(a["nome"], a["v"])
    if cosa == "tariffe_via":
        SRV._TARIFFE_SWAP.update(quando=0.0, dati=None)
        return {"ok": True}
    if cosa == "avvisi":
        return {"ghiaccio": sum("🧊" in t for t in banco.AVVISI)}
    return {"sconosciuto": cosa}


class _Ponte(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _rispondi(self, codice, corpo):
        dati = json.dumps(corpo).encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def _passa(self, fn):
        try:
            return self._rispondi(200, fn())
        except SRV.HTTPException as e:
            return self._rispondi(e.status_code, {"detail": e.detail})
        except Exception as e:
            return self._rispondi(500, {"detail": f"{type(e).__name__}: {e}"})

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        pz = u.path.strip("/").split("/")
        banco.come(999, admin=True)
        if pz[:3] == ["api", "swap", "preventivo"]:
            return self._passa(lambda: _gira(SRV.swap_preventivo(
                int(pz[3]), (q.get("hash") or [""])[0],
                (q.get("fornitore") or ["satsrouting"])[0], "", "")))
        if pz[:3] == ["api", "swap", "pagamento"]:
            return self._passa(lambda: _gira(SRV.swap_pagamento_stato(
                int(pz[3]), "", "")))
        if pz[0] == "ctl":
            return self._passa(lambda: _controllo(pz[1], q))
        return self._rispondi(404, {})

    def do_POST(self):
        u = urlparse(self.path)
        pz = u.path.strip("/").split("/")
        n = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        banco.come(999, admin=True)
        PONTE["corpi"].append(corpo)

        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
        if pz[:3] == ["api", "swap", "paga"]:
            return self._passa(lambda: _gira(SRV.swap_paga(
                int(pz[3]), None, "", "")))
        return self._rispondi(404, {})


PONTE = {"corpi": []}


def pezzi_pagina():
    """Dalla pagina: la lettura delle fatture e le tre funzioni che
    parlano col server dello swap (preventivo, pagamento, stato)."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"),
                encoding="utf-8").read().replace("\r\n", "\n")
    pezzi = []
    for inizio, fine in (("function importoBolt11(pr){", "\n}\n"),
                         ("function leggiBolt11(pr){", "\n}\n"),
                         ("async function leggiPreventivoSwap(",
                          "async function caricaPreventivoSwap(")):
        i = mini.index(inizio)
        j = mini.index(fine, i) + (3 if fine == "\n}\n" else 0)
        pezzi.append(mini[i:j])
    return "\n".join(pezzi)


BANCO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const BUNDLE = fs.readFileSync(D.bundle, 'utf8');
const TELEFONO = D.telefono.map(f => fs.readFileSync(f, 'utf8'));
const fetchVero = globalThis.fetch;
const chiamate = [];
const BASE = D.base;
const ctl = p => fetchVero(`${D.ponte}/ctl/${p}`).then(r => r.json());
const modo = m => fetchVero(`${BASE}/cartone/modo?m=${m}`).then(r => r.json());
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const visto = () => fetchVero(`${BASE}/cartone/visto`).then(r => r.json());
const cima = h => fetchVero(`${BASE}/cartone/cima?h=${h}`).then(r => r.json());

function pagina(memoria){
  const ctx = {console, crypto: globalThis.crypto, TextEncoder, TextDecoder, URL,
    URLSearchParams, Uint8Array, BigInt, setTimeout, clearTimeout, Promise, JSON,
    Date, Math,
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
const API_BASE = ${JSON.stringify(D.ponte + '/api')};
function authHdr(){ return 'collaudo:999:Admin'; }
let swapLeve = ${JSON.stringify(D.leve)};
const swapAcceso = () => !!(swapLeve && swapLeve.attivo);
const elementi = {};
function el(id){ return elementi[id] || null; }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const fmt = n => String(n);
function haptic(){}
function toast(m){}
let currentOrder = null;
let preventiviSwap = {};
function ridisegnaIncassoSwap(){}
function pannelloPreventivoSwap(){ return '<div>preventivo</div>'; }
function scegliIncassoSwap(){}
function linguaSwap(){ return 'it'; }
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const document = {addEventListener(){}, head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
`, Object.assign(ctx, {__memoria: memoria}));
  vm.runInContext(D.pagina, ctx);
  for (const codice of TELEFONO) vm.runInContext(codice, ctx);
  return {ctx, run: codice => vm.runInContext(codice, ctx)};
}

(async () => {
  const out = {};
  const mem = new Map();
  const A = pagina(mem);
  const lista = () => JSON.parse(mem.get('barattolo_swap_lista_999') || '[]');
  const ultimo = n => lista().filter(r => r.ordine === n).pop() || null;
  const frase = n => A.run(`frasestatoSwap(swapLista().filter(r => r.ordine === ${n}).pop())`);
  async function nuovoSwap(P, n){
    P.run(`elementi.swapIndirizzo_${n} = {value: '${D.indirizzo}'}`);
    await P.run(`swapAvanti(${n})`);
    if (P.run(`swapPassi[${n}]`) === 'parole') {
      P.run(`elementi.swapSpunta_${n} = {checked: true}`);
      P.run(`swapParoleFatte(${n})`);
    }
    await P.run(`swapCrea(${n})`);
    return ultimo(n);
  }
  const paga = (n, varia) => A.run(
    `pagaSwapAlServer(Object.assign({}, swapLista().filter(r => r.ordine === ${n}).pop(), ${JSON.stringify(varia || {})}))`);
  const O = D.ordini;

  // ─── A. LO SWAP INTERO ────────────────────────────────────────────
  await ctl('post?esito=pending');
  const r1 = await nuovoSwap(A, O.intero);
  const v0 = await visto();
  out.intero = {pagamento: r1 && r1.pagamento, motivo: (r1 && r1.motivo) || '',
                frase: frase(O.intero), ordine: await ctl(`ordine?id=${O.intero}`),
                righe: await ctl(`righe?ordine=${O.intero}`),
                uscite: (await ctl(`uscite?h=${r1.impronta}`)).per,
                impronta: r1.impronta, fattura: r1.invoice,
                creazione: v0.creazione && v0.creazione.preimageHash === r1.impronta};
  await stato(r1.id, 'transaction.mempool');
  await A.run('swapGiro()');
  const r1b = ultimo(O.intero);
  const v1 = await visto();
  out.ritiro = {txid: !!(r1b.ritiro && r1b.ritiro.txid), trasmesse: v1.trasmesse.length,
                ordine: await ctl(`ordine?id=${O.intero}`)};
  await ctl(`lnbits?h=${r1.impronta}&s=success`);
  await stato(r1.id, 'invoice.settled');
  await ctl('ronda');
  await A.run('swapGiro()');
  out.chiuso = {ordine: await ctl(`ordine?id=${O.intero}`),
                righe: await ctl(`righe?ordine=${O.intero}`),
                fase: A.run(`swapFase(swapLista().filter(r => r.ordine === ${O.intero}).pop())`),
                frase: frase(O.intero),
                uscite: (await ctl(`uscite?h=${r1.impronta}`)).per};

  // ─── B. LA RISPOSTA DEL NODO MANCATA ─────────────────────────────
  await ctl('post?esito=timeout');
  const r2 = await nuovoSwap(A, O.volo);
  out.volo = {pagamento: r2.pagamento, ordine: await ctl(`ordine?id=${O.volo}`),
              righe: await ctl(`righe?ordine=${O.volo}`)};
  await ctl('post?esito=pending');
  const B = pagina(mem);            // il telefono riapre, stesso cassetto
  out.voloRichiesto = await B.run(`pagaSwapAlServer(swapLista().filter(r => r.ordine === ${O.volo}).pop())`);
  out.voloUscite = (await ctl(`uscite?h=${r2.impronta}`)).per;
  await ctl(`invecchia?ordine=${O.volo}`);
  await ctl('ronda');
  out.voloMezzora = {ordine: await ctl(`ordine?id=${O.volo}`),
                     ghiaccio: (await ctl('avvisi')).ghiaccio};
  await ctl(`invecchia?ordine=${O.volo}&cosa=scadenza`);
  await ctl('ronda');
  out.voloScaduto = {ordine: await ctl(`ordine?id=${O.volo}`),
                     righe: await ctl(`righe?ordine=${O.volo}`),
                     ghiaccio: (await ctl('avvisi')).ghiaccio};
  await A.run('swapGiro()');
  out.voloTelefono = {pagamento: ultimo(O.volo).pagamento, frase: frase(O.volo)};
  out.voloDiNuovo = await paga(O.volo);
  out.voloUsciteFine = (await ctl(`uscite?h=${r2.impronta}`)).per;

  // ─── C. IL CASO DEL #241 ──────────────────────────────────────────
  await ctl('post?esito=failed');
  const r3 = await nuovoSwap(A, O.caso241);
  out.fallito = {pagamento: r3.pagamento, frase: frase(O.caso241),
                 scegliDiNuovo: A.run(`swapDiOrdine(${O.caso241}) === null`),
                 ordine: await ctl(`ordine?id=${O.caso241}`),
                 righe: await ctl(`righe?ordine=${O.caso241}`)};
  await ctl(`lnbits?h=${r3.impronta}&s=success`);     // pagato a mano
  await ctl('post?esito=pending');
  const r3b = await nuovoSwap(A, O.caso241);
  out.aMano = {nuovo: r3b.impronta !== r3.impronta, pagamento: r3b.pagamento,
               ordine: await ctl(`ordine?id=${O.caso241}`),
               righe: await ctl(`righe?ordine=${O.caso241}`),
               usciteNuovo: (await ctl(`uscite?h=${r3b.impronta}`)).per,
               usciteVecchio: (await ctl(`uscite?h=${r3.impronta}`)).per,
               vecchio: r3.impronta};

  // ─── D. I CONTROLLI PRIMA DI PAGARE ──────────────────────────────
  await ctl(`leva?nome=SWAP_MEMPOOL_API&v=http://127.0.0.1:9`);
  const r4 = await nuovoSwap(A, O.controlli);
  out.mempoolGiu = {pagamento: r4.pagamento, motivo: r4.motivo || '',
                    righe: (await ctl(`righe?ordine=${O.controlli}`)).length};
  await ctl(`leva?nome=SWAP_MEMPOOL_API&v=${BASE}/esplora`);
  const prima = (await ctl('uscite')).tutte;
  const no = {};
  no.forma = await paga(O.controlli, {impronta: ''});
  const altra = r4.impronta.slice(0, -1) + (r4.impronta.endsWith('0') ? '1' : '0');
  no.impronta = await paga(O.controlli, {impronta: altra});
  no.altroTipo = await paga(O.controlli, {lockupAddress: D.indirizzo});
  const rotto = r4.lockupAddress.slice(0, -1) + (r4.lockupAddress.endsWith('q') ? 'p' : 'q');
  no.checksum = await paga(O.controlli, {lockupAddress: rotto});
  no.importo = await paga(O.controlli, {ordine: O.altroPrezzo});
  no.meno = await paga(O.controlli, {onchainAmount: r4.onchainAmount - 1});
  await cima(D.scadenza - 10);
  no.scadenza = await paga(O.controlli);
  await cima(D.scadenza - 144);
  await ctl('leva?nome=SWAP_FEE_PERCENTO&v=0.5');
  no.fee = await paga(O.controlli);
  await ctl('leva?nome=SWAP_FEE_PERCENTO&v=0');
  await modo('giu');
  await ctl('tariffe_via');
  no.tariffe = await paga(O.controlli);
  await modo('normale');
  await ctl('tariffe_via');
  await ctl('leva?nome=SWAP_ATTIVO&v=0');
  no.spento = await paga(O.controlli);
  await ctl('leva?nome=SWAP_ATTIVO&v=1');
  await stato(r4.id, 'transaction.mempool');    // il lockup c'e' gia'
  no.usato = await paga(O.controlli);
  out.no = no;
  out.noUscite = (await ctl('uscite')).tutte - prima;
  out.noRighe = (await ctl(`righe?ordine=${O.controlli}`)).length
              + (await ctl(`righe?ordine=${O.altroPrezzo}`)).length;

  // ─── E. I TETTI ───────────────────────────────────────────────────
  const r5 = await nuovoSwap(A, O.tetti);
  out.tettoUtente = {pagamento: r5.pagamento, motivo: r5.motivo || '', frase: frase(O.tetti),
                     scegliDiNuovo: A.run(`swapDiOrdine(${O.tetti}) === null`)};
  await ctl('leva?nome=SWAP_MAX_SATS_UTENTE_GIORNO&v=0');
  await ctl('leva?nome=SWAP_MAX_SATS_GIORNO&v=100000');
  const r5b = await nuovoSwap(A, O.tetti);
  out.tettoGiorno = {pagamento: r5b.pagamento, motivo: r5b.motivo || '', frase: frase(O.tetti)};
  await ctl('leva?nome=SWAP_MAX_SATS_GIORNO&v=200000');
  const r5c = await nuovoSwap(A, O.tetti);
  out.tettoAlzato = {pagamento: r5c.pagamento, ordine: await ctl(`ordine?id=${O.tetti}`),
                     uscite: (await ctl(`uscite?h=${r5c.impronta}`)).per};
  await ctl('leva?nome=SWAP_MAX_SATS_UTENTE_GIORNO&v=100000');

  // ─── F. PER IL DOPPIO TOCCO: uno swap creato col mempool giu ──────
  await ctl(`leva?nome=SWAP_MEMPOOL_API&v=http://127.0.0.1:9`);
  const r7 = await nuovoSwap(A, O.doppio);
  await ctl(`leva?nome=SWAP_MEMPOOL_API&v=${BASE}/esplora`);
  out.doppio = {fornitore: 'satsrouting', swap_id: r7.id, invoice: r7.invoice,
                impronta: r7.impronta, indirizzo: r7.lockupAddress,
                scade_blocco: r7.timeoutBlockHeight, onchain: r7.onchainAmount};

  // ─── LA SENTINELLA ────────────────────────────────────────────────
  const parole = JSON.parse(mem.get('barattolo_swap_999') || '{}').parole || '';
  const alServer = chiamate.filter(c => c.url.startsWith(D.ponte));
  const pagamenti = alServer.filter(c => c.url.includes('/swap/paga/'));
  out.sentinella = {
    rotte: [...new Set(alServer.map(c => c.url.replace(D.ponte, '').replace(/\/\d+.*$/, '').replace(/\?.*$/, '')))].sort(),
    chiavi: [...new Set(pagamenti.map(c => Object.keys(JSON.parse(c.corpo || '{}')).sort().join(',')))],
    parole: !!parole && alServer.some(c => parole.split(' ').some(p => p.length > 3 && c.corpo.includes(p + ' '))),
    tutteLeParole: !!parole && chiamate.some(c => c.corpo.includes(parole)),
    parolaLunga: parole.split(' ').filter(p => p.length > 5)[0] || ''};
  console.log(JSON.stringify(out));
})().catch(e => { console.log(JSON.stringify({ERRORE: String(e && e.stack || e)})); });
"""


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((999, "Admin"), (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    ids = {}
    for nome, prezzo in (("intero", 30_000), ("volo", 30_000),
                         ("caso241", 30_000), ("controlli", 30_000),
                         ("altroPrezzo", 31_000), ("tetti", 30_000),
                         ("doppio", 30_000)):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(999,?,'una cosa',?,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (f"Cosa {nome}", prezzo))
        ids[nome] = cur.lastrowid
    con.commit()
    con.close()
    ordini = {}
    for nome, aid in ids.items():
        oid = banco.ordine_pagato(aid)
        con = SRV.db()
        con.execute("UPDATE ordini SET stato='confirmed' WHERE id=?", (oid,))
        con.commit()
        con.close()
        ordini[nome] = oid
    return ordini


def telefono(base, ponte, ordini):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="swap_pagamento_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "ponte": ponte, "indirizzo": INDIRIZZO,
            "ordini": ordini, "scadenza": cartone_satsrouting.SCADENZA_BLOCCO,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "pagina": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "bitcoin",
                     "referral": "barattolo", "minimo": 25_000,
                     "massimo": 50_000, "mempool": base + "/esplora"}}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1500:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def primo(righe):
    """Lo stato della prima riga, o None: una riga che manca e' un rosso,
    non un banco che esplode."""
    return righe[0]["stato"] if righe else None


def il_giro(r, ordini, tee):
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return
    P = "Barattolo sta pagando lo swap: poi SATS Routing blocca i bitcoin e li ritiro."
    print("\n[lo swap intero]")
    i = r["intero"]
    prova("lo swap nasce col segreto del telefono e il server lo paga: in volo",
          ("in_volo", "", True), (i["pagamento"], i["motivo"], i["creazione"]))
    prova("...la carta dice che Barattolo sta pagando", P, i["frase"])
    prova("...l'ordine resta confermato, in volo col NOME di quella fattura",
          {"stato": "confirmed", "payout_stato": "in_volo",
           "payout_hash": i["impronta"], "invoice": True}, i["ordine"])
    prova("...una riga registrata, coi sats di chi vende, che vola fino alla scadenza",
          [{"stato": "in_volo", "hash": i["impronta"], "sats": 30_000, "lungo": True}],
          i["righe"])
    prova("...e una sola richiesta di pagamento", 1, i["uscite"])
    prova("bitcoin bloccati: il telefono ritira, l'ordine aspetta ancora",
          (True, 1, "in_volo"),
          (r["ritiro"]["txid"], r["ritiro"]["trasmesse"],
           r["ritiro"]["ordine"]["payout_stato"]))
    c = r["chiuso"]
    prova("la fattura si chiude: la ronda chiude l'ordine come pagato",
          ("released", "uscito"),
          (c["ordine"]["stato"], c["ordine"]["payout_stato"]))
    prova("...la riga dice pagato, la carta «Fatto», sempre un pagamento solo",
          ("pagato", "fatto", "Fatto: i bitcoin sono tuoi.", 1),
          (primo(c["righe"]), c["fase"], c["frase"], c["uscite"]))

    print("\n[la risposta del nodo mancata]")
    v = r["volo"]
    prova("il nodo non risponde: in volo, col nome, nessun 🧊",
          ("in_volo", "in_volo", "in_volo"),
          (v["pagamento"], v["ordine"]["payout_stato"], primo(v["righe"])))
    prova("il telefono riapre e richiede: stesso pagamento, nessuna uscita in piu'",
          ({"ok": True, "stato": "in_volo"}, 1), (r["voloRichiesto"], r["voloUscite"]))
    prova("mezz'ora passata: la fattura di uno swap vola ancora, nessun 🧊",
          ("in_volo", 0), (r["voloMezzora"]["ordine"]["payout_stato"],
                           r["voloMezzora"]["ghiaccio"]))
    vs = r["voloScaduto"]
    prova("passata la scadenza dello swap: 🧊 Pagamenti da verificare",
          ("incerto", "da_verificare", 1),
          (vs["ordine"]["payout_stato"], primo(vs["righe"]), vs["ghiaccio"]))
    prova("...il telefono lo dice",
          ("da_verificare", "Pagamento da verificare: ci stiamo lavorando noi. "
                            "I tuoi sats non si perdono."),
          (r["voloTelefono"]["pagamento"], r["voloTelefono"]["frase"]))
    prova("...e richiederlo non paga: resta da verificare, sempre un'uscita",
          ({"ok": True, "stato": "da_verificare"}, 1),
          (r["voloDiNuovo"], r["voloUsciteFine"]))

    print("\n[il caso del #241]")
    f = r["fallito"]
    prova("fallito con zero tentativi: la riga dice fallito, la fattura e' tolta",
          ("fallito", "fallito", "confirmed", False),
          (f["pagamento"], primo(f["righe"]), f["ordine"]["stato"],
           f["ordine"]["invoice"]))
    prova("...il telefono lo dice e chi vende sceglie di nuovo",
          ("Il pagamento non è partito: nessun sats si è mosso. Scegli di nuovo "
           "come incassare.", True), (f["frase"], f["scegliDiNuovo"]))
    m = r["aMano"]
    prova("pagato a mano, poi uno swap nuovo: NON si paga, nessuna uscita per lui",
          (True, 0, 1), (m["nuovo"], m["usciteNuovo"], m["usciteVecchio"]))
    prova("...l'ordine si chiude col pagamento di prima",
          ("released", m["vecchio"]),
          (m["ordine"]["stato"], m["ordine"]["payout_hash"]))
    prova("...la riga vecchia dice pagato, la nuova fallito",
          ["pagato", "fallito"], [x["stato"] for x in m["righe"]])

    print("\n[i controlli prima di pagare]")
    prova("mempool giu: non si paga, niente registrato, il telefono riprovera'",
          {"pagamento": "", "motivo": "mempool", "righe": 0}, r["mempoolGiu"])
    attesi = {"forma": "forma", "impronta": "impronta", "altroTipo": "indirizzo",
              "checksum": "indirizzo", "importo": "importo", "meno": "cambiata",
              "scadenza": "scadenza", "fee": "fee", "tariffe": "non_risponde",
              "usato": "usato"}
    for k, motivo in attesi.items():
        prova(f"no «{k}»: {motivo}", {"ok": False, "motivo": motivo},
              r["no"].get(k))
    prova("leva spenta: la porta e' chiusa", None, r["no"].get("spento"))
    prova("...in tutti questi nessun sats e' uscito e nessuna riga e' nata",
          (0, 0), (r["noUscite"], r["noRighe"]))

    print("\n[i tetti]")
    prova("oltre i 100.000 di chi vende in 24 ore: no, lo dice, e si sceglie di nuovo",
          {"pagamento": "rifiutato", "motivo": "tetto_utente",
           "frase": "Per oggi hai raggiunto il tetto degli swap: incassa via Lightning.",
           "scegliDiNuovo": True}, r["tettoUtente"])
    prova("oltre il tetto di tutti: no, lo dice",
          {"pagamento": "rifiutato", "motivo": "tetto_giorno",
           "frase": "Oggi lo swap è al completo: incassa via Lightning."},
          r["tettoGiorno"])
    prova("a tetto alzato lo stesso ordine passa: in volo, un'uscita",
          ("in_volo", "in_volo", 1),
          (r["tettoAlzato"]["pagamento"], r["tettoAlzato"]["ordine"]["payout_stato"],
           r["tettoAlzato"]["uscite"]))

    print("\n[il doppio tocco]")
    s = SRV._swap_parti(r["doppio"])
    chi = SRV.swap_fornitore("satsrouting")
    oid = ordini["doppio"]
    prima = USCITE.count(s["impronta"])
    # i tetti di chi vende li hanno gia' riempiti le scene di prima
    SRV.SWAP_MAX_SATS_UTENTE_GIORNO = 0

    async def due():
        return await asyncio.gather(
            SRV.swap_registra_pagamento(999, oid, chi, dict(s)),
            SRV.swap_registra_pagamento(999, oid, chi, dict(s)))
    a, b = asyncio.run(due())
    prova("due richieste insieme: tutt'e due ok, un pagamento solo, una riga",
          (True, True, 1, 1),
          (a.get("ok"), b.get("ok"), USCITE.count(s["impronta"]) - prima,
           len(_righe(oid))))

    print("\n[il journal]")
    testo = "".join(tee.righe)
    righe_swap = [x for x in testo.splitlines() if "Swap dell'ordine" in x]
    prova("una riga per passo: controlli, registrazione, ogni cambio, ogni no",
          (True, True, True, True),
          (any("controlli passati" in x for x in righe_swap),
           any("registrato (pagamento" in x for x in righe_swap),
           any("da «in_volo» a «pagato»" in x for x in righe_swap),
           any("non si paga — tetto_utente" in x for x in righe_swap)))
    prova("nessuna fattura intera nel journal", False,
          any(x in testo for x in (r["intero"]["fattura"],)))
    prova("nessuna parola delle dodici nel journal", False,
          bool(r["sentinella"]["parolaLunga"])
          and r["sentinella"]["parolaLunga"] in testo.lower().split())

    print("\n[la sentinella]")
    se = r["sentinella"]
    prova("il telefono parla col server solo per preventivo, pagamento e stato",
          ["/api/swap/paga", "/api/swap/pagamento", "/api/swap/preventivo"],
          se["rotte"])
    prova("...e al pagamento manda SOLO le sette parti pubbliche",
          ["fornitore,impronta,indirizzo,invoice,onchain,scade_blocco,swap_id"],
          se["chiavi"])
    prova("...in nessuna chiamata le dodici parole", (False, False),
          (se["parole"], se["tutteLeParole"]))


def main():
    global CARTONE, SRV
    print("=" * 58)
    print("  ₿ LO SWAP, TAPPA 4 — Barattolo paga la fattura")
    print("=" * 58)
    tee = _Tee(sys.stdout)
    sys.stdout = tee
    banco.avvio()
    SRV = banco.SRV
    _, porta = cartone_satsrouting.avvia(0)
    CARTONE = f"http://127.0.0.1:{porta}"
    SRV.httpx = _Misto
    SRV.SECONDI_FRA_ATTESE = 0
    SRV.SWAP_ATTIVO = True
    SRV.SWAP_SOLO_MODERATORI = True
    SRV.SWAP_MIN_SATS = 25_000
    SRV.SWAP_MAX_SATS = 50_000
    SRV.SWAP_FEE_PERCENTO = 0
    SRV.SWAP_MAX_SATS_UTENTE_GIORNO = 100_000
    SRV.SWAP_MAX_SATS_GIORNO = 200_000
    SRV.SWAP_API_BASE = CARTONE
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.SWAP_RETE = "bitcoin"
    SRV.SWAP_MEMPOOL_API = CARTONE + "/esplora"
    ordini = semina()
    ponte = HTTPServer(("127.0.0.1", 0), _Ponte)
    threading.Thread(target=ponte.serve_forever, daemon=True).start()
    base_ponte = f"http://127.0.0.1:{ponte.server_address[1]}"
    r = telefono(CARTONE, base_ponte, ordini)
    ponte.shutdown()
    il_giro(r, ordini, tee)
    sys.stdout = tee.vero

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
