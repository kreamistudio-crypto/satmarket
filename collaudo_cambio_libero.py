# -*- coding: utf-8 -*-
"""
IL CAMBIO LIBERO, TAPPE 2 E 3: IL BIGLIETTO E IL PREVENTIVO, SUL SERVER
VERO (27 ott 2026, cantiere cambio-libero, piano approvato da Andrea).

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
    swap sotto non c'e' il cambio;
  - (tappa 3) LA STRADA BITCOIN → LIGHTNING: a leva spenta non c'e'
    (strade, 400, «direzione»); accesa, il preventivo di quanto MANDARE
    (ricevi + 0,5 % + 318), il minimo del submarine, il biglietto.
  Poi IL TELEFONO (il codice vero in node contro il cartone): la strada
  rovesciata con la richiesta Lightning al posto dell'indirizzo, la
  nascita verificata, i bitcoin visti → confermati → pagata (la nostra
  meta' del ritiro a due, col segreto che prova la fattura) → fatto; un
  cambio fallito rimborsato a due all'indirizzo scritto; uno scaduto
  rimborsato dallo script alla scadenza; uno scaduto senza bitcoin.

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

    print("\n[il conto al contrario: si scrive in «Ricevi» (cambio-due-riquadri)]")
    _, r = preventivo(c, 999, 98_842, lato="ricevi")
    prova("ricevere 98.842 vuol dire cambiarne 100.000; la busta ripete lato e cifra scritta",
          (True, 100_000, 98_842, "ricevi", 98_842),
          (r.get("ok"), r.get("dovuto"), r.get("ricevi"), r.get("lato"), r.get("scritta")))
    _, r = preventivo(c, 999, 98_000, lato="ricevi")
    prova("...98.000 da ricevere: 99.153 da cambiare, e arrivano 98.000 (mai di meno)",
          (99_153, 98_000), (r.get("dovuto"), r.get("ricevi")))
    _, r = preventivo(c, 999, 100_000, lato="mandi")
    prova("...«mandi» e' il lato di sempre, e senza lato pure",
          ((100_000, "mandi", 100_000), (100_000, "mandi")),
          ((r.get("dovuto"), r.get("lato"), r.get("scritta")),
           (lambda x: (x.get("dovuto"), x.get("lato")))(preventivo(c, 999, 100_000)[1])))
    _, r = preventivo(c, 999, 600_000, lato="ricevi")
    prova("...e i tetti valgono sulla cifra vera: 600.000 da ricevere e' sopra il tetto",
          (False, "sopra_tetto"), (r.get("ok"), r.get("motivo")))
    prova("un lato sconosciuto: 400", 400, preventivo(c, 999, 100_000, lato="destra")[0])

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

    print("\n[la strada bitcoin → Lightning (tappa 3)]")
    # (il 999 ha gia' i suoi cinque biglietti del giorno: qui si cambia
    # col 222, coi due cancelli aperti per lui)
    srv.CAMBIO_LIBERO_SOLO_MODERATORI = False
    srv.SWAP_SOLO_MODERATORI = False
    prova("a leva spenta la strada non c'e': strade, preventivo 400, biglietto «direzione»",
          (["ln-btc"], 400, "direzione"),
          (leve(c, 222).get("strade"), preventivo(c, 222, 100_000, direzione="btc-ln")[0],
           biglietto(c, 222, 100_000, direzione="btc-ln")[1].get("motivo")))
    srv.CAMBIO_BTC_LN_ATTIVO = True
    prova("...accesa, le due strade in /api/me", ["ln-btc", "btc-ln"], leve(c, 222).get("strade"))
    prima_sub = cartone("/cartone/visto").get("letture_sub", 0)
    codice, p = preventivo(c, 222, 100_000, direzione="btc-ln")
    prova("il preventivo di quanto MANDARE per ricevere 100.000: +0,5 % +318 = 100.818",
          (200, True, "btc-ln", 100_000, 100_818, "cartone-sub-16ott",
           [("ricevi_ln", 100_000, False), ("commissione", 500, True), ("rete_loro", 318, True)]),
          (codice, p.get("ok"), p.get("direzione"), p.get("ricevi"), p.get("mandi"), p.get("hash"),
           [(r["voce"], r["sats"], bool(r.get("piu"))) for r in p.get("righe", [])]))
    prova("...letto dalle tariffe del submarine del cartone, col codice partner",
          (1, "barattolo"), (cartone("/cartone/visto").get("letture_sub", 0) - prima_sub,
                             cartone("/cartone/visto").get("referral")))
    _, m = preventivo(c, 222, 100_818, direzione="btc-ln", lato="mandi")
    prova("(cambio-due-riquadri) scritti 100.818 da MANDARE: si ricevono 100.000",
          (True, 100_000, 100_818, "mandi", 100_818),
          (m.get("ok"), m.get("dovuto"), m.get("mandi"), m.get("lato"), m.get("scritta")))
    _, sub = preventivo(c, 222, 40_000, direzione="btc-ln")
    prova("...sotto il minimo del submarine (50.000, piu' alto del nostro)",
          (False, "sotto_minimo", 50_000), (sub.get("ok"), sub.get("motivo"), sub.get("minimo")))
    codice, b = biglietto(c, 222, 100_000, direzione="btc-ln")
    prova("il biglietto della strada rovesciata", (200, True), (codice, b.get("ok")))
    liberato = annulla(c, 222, b.get("id"))[1].get("ok")
    prova("...liberato subito (non conta per le scene dopo)", True, liberato)
    srv.CAMBIO_BTC_LN_ATTIVO = False
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
        # (28 ott 2026, grafica-cambio) i riquadri, il costo, i rifiuti
        tra("let dettagliSwap = {};", fino_a="/* (27 ott 2026, cantiere grafica-swap) `campo`"),
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
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finche = async (f, ms = 5000) => { const t0 = Date.now(); while (!f() && Date.now() - t0 < ms) await sleep(100); };
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
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
  const scritta = Number(n) === 0 ? swapCambioCifra() : 48000;
  const strada = Number(n) === 0 ? swapCambioStradaScelta() : 'ln-btc';
  /* (cambio-due-riquadri) scritta dall'altro lato: il dovuto piu' piccolo
     che non da' meno (il conto al contrario del server) */
  const lato = Number(n) === 0 ? swapCambioLato : 'mandi';
  const latoDovuto = strada === 'btc-ln' ? 'ricevi' : 'mandi';
  const esce = d => strada === 'btc-ln' ? d + Math.ceil(d * 5 / 1000) + 318 : d - Math.ceil(d * 6 / 1000) - 324 - 234;
  let sats = scritta;
  if (lato !== latoDovuto && scritta) { sats = 1; while (esce(sats) < scritta) sats++; }
  preventivi.push({n, fornitore, hash, sats, strada, lato, scritta});
  if (Number(n) === 0 && !sats) return {ok: false, motivo: 'cifra', oggi: 1, al_giorno: 5};
  if (Number(n) === 0 && tettoGiornoFinto) return {ok: false, motivo: 'tetto_giorno', oggi: 5, al_giorno: 5, fornitore_nome: 'SATS Routing'};
  if (strada === 'btc-ln') {
    /* il conto del server per la strada rovesciata (preventivo_sub) */
    const comm = Math.ceil(sats * 5 / 1000), mandi = sats + comm + 318;
    return {ok: true, hash: 'cartone-sub-16ott', dovuto: sats, fattura: sats, ricevi: sats, mandi,
            valido_s: 60, oggi: 1, al_giorno: 5, direzione: 'btc-ln', lato, scritta,
            fornitore: fornitore || 'satsrouting', fornitore_nome: 'SATS Routing',
            righe: [{voce: 'ricevi_ln', sats}, {voce: 'commissione', sats: comm, piu: true, percento: 0.5},
                    {voce: 'rete_loro', sats: 318, piu: true}]};
  }
  const comm = Math.ceil(sats * 6 / 1000), onchain = sats - comm - 324;
  return {ok: true, hash: 'cartone-tariffa-16ott', dovuto: sats, fattura: sats, onchain,
          ricevi: onchain - 234, valido_s: 60, oggi: 1, al_giorno: 5, direzione: 'ln-btc', lato, scritta,
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
  // --- a leva del cambio spenta: niente
  run('swapLeve.cambio.attivo = false'); run('renderSwapCambio()');
  out.spento = box();
  // --- (28 ott 2026, grafica-cambio) accesa: SUBITO APERTO, i due riquadri
  run('swapLeve.cambio.attivo = true'); run('renderSwapCambio()');
  const f1 = box();
  const senzaSvg = f1.replace(/<svg[\s\S]*?<\/svg>/g, '');
  out.aperto = {campo: f1.includes('id="swapCambioMandi" data-lato="mandi"') && f1.includes('id="swapCambioRicevi" data-lato="ricevi"'),
                /* (28 ott 2026, unita-tendine) le pillole di SATS Routing: il fulmine
                   «LN» e la moneta «BTC»; con una strada sola niente tendina */
                mandi: /<span class="cambio-eti">Mandi<\/span><span class="cambio-pillola"><span class="cambio-fulmine"><svg[^]*?<\/svg><\/span><b>LN<\/b><\/span>/.test(f1),
                ricevi: /<span class="cambio-eti">Ricevi circa<\/span><span class="cambio-pillola"><span class="cambio-moneta btc"><svg[^]*?<\/svg><\/span><b>BTC<\/b><\/span>/.test(f1),
                tendine: (f1.match(/data-swap="cambio-tendina"/g) || []).length,
                unita: [(f1.match(/data-swap="cambio-unita"/g) || []).length, f1.includes('data-unita="sats" aria-pressed="true" aria-label="sats"><svg'),
                        f1.includes('data-unita="btc" aria-pressed="false" aria-label="BTC"><svg'),
                        f1.indexOf('data-unita="btc"') < f1.indexOf('data-unita="sats"')],
                gira: (f1.match(/data-swap="cambio-gira"/g) || []).length,
                tra: f1.includes('Da 25000 a 500000 sats · oggi 0 di 5'),
                tessere: (f1.match(/<li><span class="cambio-tessera-ico"><svg/g) || []).length,
                indirizzo: f1.includes('id="swapIndirizzo_0"'),
                fermo: f1.includes('id="swapCambioVai" type="button" data-swap="avanti" data-ordine="0" disabled'),
                vecchi: ['data-swap="cambia"', 'cambio-chiudi', 'data-swap="cambio-calcola"', 'Cambia i tuoi sats'].filter(x => f1.includes(x)),
                emoji: (senzaSvg.match(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}₿]/gu) || [])};
  // --- senza cifra non si chiede niente
  run("elementi.swapCambioMandi = {value: ''}");
  await run('swapCambioCalcola()');
  out.senzaCifra = [box().includes('Scrivi quanti sats vuoi cambiare.'), preventivi().length];
  // --- 100.000 scritto tasto per tasto: UN preventivo solo, quando si
  // smette di scrivere (modifica 1 di Andrea), e intanto «…»
  run('delete elementi.swapCambioMandi');
  for (const v of ['1', '10', '100', '1000', '10.000', '100.000']) run(`swapCambioScrive('${v}', 'mandi')`);
  out.attesa = {subito: preventivi().length, puntini: /id="swapCambioRicevi"[^>]*placeholder="…"[^>]*value=""/.test(box()),
                fermo: box().includes('data-ordine="0" disabled')};
  await sleep(1500);
  await finche(() => run('!swapCambioTimer && (preventiviSwap[0] || {}).stato === "pronto"'));
  out.attesa.dopo = preventivi().length;
  const f2 = box();
  out.preventivo = {letto: preventivi()[0], cambi: f2.includes('<span>Cambi</span><b>100000</b>'),
                    spettano: f2.includes('Ti spettano'), ricevi: /id="swapCambioRicevi"[^>]*value="98842"><small>sats<\/small>/.test(f2),
                    costo: f2.includes('Costo <b>1158 sats</b> · SATS Routing'), chiuse: f2.includes('<div class="cambio-voci" hidden>'),
                    incassaLn: f2.includes('Incassa in Lightning'), campo: f2.includes('id="swapIndirizzo_0"'),
                    conferma: f2.includes('data-swap="avanti" data-ordine="0">Conferma'), calcola: f2.includes('data-swap="cambio-calcola"')};
  run('dettagliSwap[0] = true; renderSwapCambio()');
  out.dettagli = [box().includes('aria-expanded="true">Nascondi'), box().includes('<div class="cambio-voci" hidden>'),
                  box().includes('Cifre di adesso: si ricontrollano quando confermi. Il cambio lo fa SATS Routing.')];
  run('dettagliSwap[0] = false');
  // --- una risposta VECCHIA (di un'altra cifra) non si mostra e non si conferma
  run('preventiviSwap[0].dati.scritta = 50000; renderSwapCambio()');
  out.vecchia = [/id="swapCambioRicevi"[^>]*placeholder="…"[^>]*value=""/.test(box()), box().includes('data-ordine="0" disabled')];
  run('preventiviSwap[0].dati.scritta = 100000; preventiviSwap[0].dati.lato = "ricevi"; renderSwapCambio()');
  /* (cambio-due-riquadri) ...e nemmeno quella dell'altro riquadro */
  out.vecchia.push(box().includes('data-ordine="0" disabled'));
  run('preventiviSwap[0].dati.lato = "mandi"; renderSwapCambio()');
  // --- (cambio-due-riquadri) SI SCRIVE IN «RICEVI»: il conto al contrario,
  // e il cambio nasce col dovuto che ne esce, non con la cifra scritta
  const pR = preventivi().length;
  run("swapCambioScrive('98000', 'ricevi')");
  await sleep(1000);
  await finche(() => run('!swapCambioTimer && (preventiviSwap[0] || {}).stato === "pronto"'));
  const fR = box();
  out.riceviScritto = {chiesto: preventivi().slice(pR).map(x => [x.lato, x.scritta, x.sats]),
                       mandi: /id="swapCambioMandi"[^>]*value="99153"/.test(fR), ricevi: /id="swapCambioRicevi"[^>]*value="98000"/.test(fR),
                       dovuto: run('swapCambioDovuto()'), cifra: run('swapCambioCifra()'), conferma: !fR.includes('data-ordine="0" disabled')};
  run("swapCambioScrive('100000', 'mandi')");
  await sleep(1000);
  await finche(() => run('!swapCambioTimer && (preventiviSwap[0] || {}).stato === "pronto"'));
  // --- (cambio-due-riquadri) IL SELETTORE sats/BTC: le cifre si leggono in
  // BTC, otto decimali; il conto e la cifra in sats non cambiano
  const pU = preventivi().length;
  run("swapCambioScegliUnita('btc')");
  const fU = box();
  out.unita = {mandi: /id="swapCambioMandi"[^>]*inputmode="decimal"[^>]*value="0,00100000"><small>BTC<\/small>/.test(fU),
               ricevi: /id="swapCambioRicevi"[^>]*value="0,00098842"><small>BTC<\/small>/.test(fU),
               costo: fU.includes('Costo <b>0,00001158 BTC</b> · SATS Routing'), riga: fU.includes('<b>−0,00000600</b>'),
               limiti: fU.includes('Da 0,00025000 a 0,00500000 BTC · oggi 0 di 5'),
               acceso: fU.includes('data-unita="btc" aria-pressed="true"'), casa: memoria.get('barattolo_cambio_unita'),
               cifra: run('swapCambioCifra()'), richiesti: preventivi().length - pU};
  out.leggi = run("[['0,001','btc'],['0.00098842','btc'],['1,5','btc'],['0,123456789','btc'],['abc','btc'],['1,2,3','btc'],['10.000','sats']].map(([t, u]) => swapCambioLeggi(t, u))");
  run("swapCambioScegliUnita('sats')");
  out.unita.tornato = [/id="swapCambioMandi"[^>]*value="100000"/.test(box()), memoria.get('barattolo_cambio_unita')];
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
               paghi: f3.includes('Paga questa richiesta col tuo wallet Lightning'), cambio: /<h4 class="cambio-tit"><svg[^]*?<\/svg>Cambio<\/h4>/.test(f3),
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
  run('renderSwapCambio()');
  out.secondoMentreVivo = box().includes('data-swap="cambio-copia"');
  // --- a cambio pagato e finito, il riquadro torna al tasto
  const l2 = lista(); l2[0].stato = 'invoice.settled'; l2[0].ritiro = {txid: 'a'.repeat(64), concluso: true, sats: 98842};
  memoria.set('barattolo_swap_lista_999', JSON.stringify(l2));
  run('renderSwapCambio()');
  /* ...e riparte PULITO: la cifra e l'indirizzo del cambio di prima non restano */
  out.finito = [box().includes('id="swapCambioMandi"'), /id="swapCambioMandi" data-lato="mandi" type="text" inputmode="numeric" autocomplete="off" placeholder="0" aria-label="Cambi" value=""/.test(box()),
                box().includes('id="swapIndirizzo_0"') && !box().includes(D.indirizzo)];
  // --- il biglietto rifiutato (tetto del giorno): niente swap chiesto
  run('bigliettoRisposta = {ok: false, motivo: "tetto_giorno"}');
  run("elementi.swapCambioMandi = {value: '100000'}");
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
  // ═══ LA STRADA BITCOIN → LIGHTNING (tappa 3) ═══
  run("bigliettoRisposta = {ok: true, id: 51, oggi: 1}; swapLeve.cambio.strade = ['ln-btc', 'btc-ln']");
  const sub = {};
  const F = D.fattureSub;
  run('renderSwapCambio()');
  sub.pillole = [(box().match(/data-swap="cambio-gira" data-strada="btc-ln"/g) || []).length, box().includes('aria-label="Da bitcoin a Lightning"')];
  /* (unita-tendine) LA TENDINA della pillola: due reti, quella di adesso
     scelta; un tocco fuori la chiude; in «Ricevi» «BTC» e' la strada di
     sempre e «LN» quella rovesciata */
  const tocco = target => { for (const [tipo, f] of run('ascoltatori')) if (tipo === 'click') f({target}); };
  run("swapCambioApriTendina('mandi')");
  const fT = box();
  sub.tendina = {pillole: (fT.match(/data-swap="cambio-tendina"/g) || []).length,
                 menu: (fT.match(/role="option"/g) || []).length,
                 ln: /aria-selected="true" data-swap="cambio-rete" data-strada="ln-btc">[^]*?LN<\/button>/.test(fT),
                 btc: /aria-selected="false" data-swap="cambio-rete" data-strada="btc-ln">[^]*?BTC<\/button>/.test(fT),
                 aperta: fT.includes('data-lato="mandi" aria-haspopup="listbox" aria-expanded="true"')};
  tocco({closest: () => null});
  sub.tendina.chiusaFuori = !box().includes('role="listbox"') && run('swapCambioTendina') === null;
  run("swapCambioApriTendina('ricevi')");
  const fR2 = box();
  sub.tendina.ricevi = [/data-strada="ln-btc">[^]*?BTC<\/button>/.test(fR2), /data-strada="btc-ln">[^]*?LN<\/button>/.test(fR2)];
  /* scegliere la rete che c'e' gia' chiude e basta */
  run("swapCambioScegliStrada('ln-btc')");
  sub.tendina.stessa = [run('swapCambioTendina'), run('swapCambioStradaScelta()'), box().includes('role="listbox"')];
  /* il tondo gira la strada; la cifra scritta resta, e il conto si rifa' da solo */
  const pGira = preventivi().length;
  await run("swapCambioScegliStrada('btc-ln')");
  const fs1 = box();
  sub.scelta = [fs1.includes('data-swap="cambio-gira" data-strada="ln-btc"'),
                /<div class="cambio-lato arriva scritto con-euro"><span class="cambio-dati"><span class="cambio-eti">Ricevi<\/span><span class="cambio-tendina"><button[^>]*data-lato="ricevi"[^>]*>[^]*?<b>LN<\/b>/.test(fs1)
                  && fs1.indexOf('<span class="cambio-eti">Ricevi</span>') < fs1.indexOf('id="swapCambioRicevi"'),
                preventivi().length - pGira, preventivi()[preventivi().length - 1].strada];
  /* (cambio-due-riquadri) la cifra resta in «Mandi», ora on-chain: il
     conto al contrario dice quanto si riceve. Poi si scrive in «Ricevi» */
  sub.mandiScritto = [preventivi()[preventivi().length - 1].lato, preventivi()[preventivi().length - 1].sats,
                      /id="swapCambioMandi"[^>]*value="100000"/.test(fs1)];
  /* un sat in piu', mai in meno: 100.015 da mandare non si puo' (le
     commissioni saltano di due), il conto ne chiede 100.016; uscendo dal
     campo la cifra vera prende il posto di quella scritta, e il conto resta
     di adesso (nessun preventivo in piu') */
  run("elementi.swapCambioMandi = {value: '100015'}; swapCambioScrive('100015', 'mandi')");
  await sleep(1000);
  await finche(() => run('!swapCambioTimer && (preventiviSwap[0] || {}).stato === "pronto"'));
  const pF = preventivi().length;
  const campoM = {id: 'swapCambioMandi', dataset: {lato: 'mandi'}, value: '100015'};
  for (const [tipo, f] of run('ascoltatori')) if (tipo === 'focusout') f({target: campoM});
  run('renderSwapCambio()');
  sub.unSatInPiu = [campoM.value, run('swapCambioCifra()'), run('swapCambioDovuto()'),
                    !box().includes('data-ordine="0" disabled'), preventivi().length - pF];
  run("swapCambioLato = 'ricevi'; elementi.swapCambioRicevi = {value: '100000'}");
  await run('swapCambioCalcola()');
  const fs2 = box();
  sub.preventivo = {strada: preventivi()[preventivi().length - 1].strada,
                    titolo: fs2.includes('aria-label="Quanto mandi in bitcoin"'), piu: fs2.includes('<b>+500</b>') && fs2.includes('<b>+318</b>'),
                    mandi: /<span class="cambio-eti">Mandi<\/span><span class="cambio-tendina">[^]*?<b>BTC<\/b>[^]*?<\/span><\/span><span class="cambio-cifra"><input[^>]*id="swapCambioMandi"[^>]*value="100818">/.test(fs2),
                    riceviLn: fs2.includes('<span>Ricevi in Lightning</span><b>100000</b>'),
                    campoFattura: fs2.includes('id="swapFattura_0"') && fs2.includes('data-swap="incolla-fattura"'),
                    campoIndirizzo: fs2.includes('id="swapIndirizzo_0"'),
                    spiega: fs2.includes('crea una richiesta di 100000 sats esatti')};
  /* (cambio-euro) IL CONTROVALORE sotto ogni cifra: col cambio vero in
     mano «≈ … €» (100.818 e 100.000 sats a 95.000 €/BTC), senza niente */
  const euri = f => [(f.match(/<span class="cambio-euro" id="swapCambioEuroMandi">([^<]*)<\/span>/) || [])[1],
                     (f.match(/<span class="cambio-euro" id="swapCambioEuroRicevi">([^<]*)<\/span>/) || [])[1]];
  sub.euro = {senza: euri(fs2)};
  run("var cambioVivo = true, eurPerSat = 95000 / 100000000; var fmtEur = e => e.toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2});");
  run('renderSwapCambio()');
  sub.euro.con = euri(box());
  sub.euro.dentro = /<span class="cambio-cifra"><input[^>]*id="swapCambioMandi"[^>]*><small>sats<\/small><span class="cambio-euro"/.test(box());
  run('cambioVivo = false; renderSwapCambio()');
  sub.euro.spento = euri(box());
  /* «Conferma» coi no della richiesta: manca, storta, importo, rete */
  const noFattura = async v => { run(`elementi.swapFattura_0 = {value: ${JSON.stringify(v)}}`); await run('swapAvanti(0)'); return run("swapErrori[0] || ''"); };
  const sPrimaSub = server().length;
  sub.fatturaNo = [await noFattura(''), await noFattura('lnbc1storta'), await noFattura(F.importo.invoice), await noFattura(F.regtest.invoice),
                   server().length - sPrimaSub];
  /* «Incolla» con «lightning:» davanti */
  run("navigator = {clipboard: {readText: async () => 'lightning:' + " + JSON.stringify(F.buona.invoice) + ", writeText: async t => { avvisi.push('APPUNTI:' + t.slice(0, 4)); }}}");
  await run('swapIncollaFattura(0)');
  sub.incollata = run('swapFattureScritte[0]') === F.buona.invoice;
  /* la nascita rovesciata (le parole sono gia' copiate: stesso cassetto) */
  const vS1 = await visto();
  await run('swapAvanti(0)');
  const vS2 = await visto();
  const rS = lista().find(r => r.tipo === 'sub') || {};
  const nascita = server().filter(s => s[0] === 'nato').pop();
  sub.nata = {ordini: server().slice(sPrimaSub).map(s => s[0]), biglietto: (server().slice(sPrimaSub).find(s => s[0] === 'biglietto') || [])[1],
              swap: vS2.swap - vS1.swap, ordine: rS.ordine, tipo: rS.tipo, cambio: rS.cambio, mandi: rS.mandi, ricevi: rS.ricevi,
              impronta: rS.impronta === F.buona.impronta, indirizzoDelRimborso: rS.indirizzo, fattura: rS.fattura === F.buona.invoice,
              lockup: /^bc1p[0-9a-z]{58}$/.test(String(rS.lockupAddress || '')),
              nato: nascita && nascita[2] && [nascita[2].indirizzo === rS.lockupAddress, nascita[2].onchain, nascita[2].impronta === F.buona.impronta],
              fase: run('swapFase(swapLista().find(r => r.tipo === "sub"))'), errore: run("swapErrori[0] || ''")};
  const cS = box();
  sub.carta = {manda: cS.includes('Manda esattamente 100818 sats a questo indirizzo'), indirizzo: cS.includes(rS.lockupAddress),
               copia: cS.includes('data-swap="cambio-copia-indirizzo"'), wallet: cS.includes('href="bitcoin:' + rS.lockupAddress + '?amount=0.00100818'),
               passi: cS.includes('>Mandati<') && cS.includes('>Pagato<'), fatturaLn: cS.includes('data-swap="cambio-copia"'),
               qr: qr()[qr().length - 1]};
  /* «Copia l'indirizzo» */
  await run(`swapCambioCopia(${JSON.stringify(rS.id)}, 'indirizzo')`);
  sub.copiaIndirizzo = run('avvisi.slice(-2)');
  /* i bitcoin: visti, confermati, la fattura pagata, il ritiro a due, fatto */
  const frase = () => run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(rS.id) + '))');
  const rec = () => lista().find(r => r.id === rS.id);
  await stato(rS.id, 'transaction.mempool');
  await run('swapGiro()');
  sub.visti = [run('swapFase(swapLista().find(r => r.id === ' + JSON.stringify(rS.id) + '))'), rec().bloccato, frase()];
  await stato(rS.id, 'transaction.confirmed');
  await run('swapGiro()');
  sub.confermati = frase();
  const vP = await visto();
  await stato(rS.id, 'invoice.paid&preimage=' + F.buona.preimage);
  await run('swapGiro()');
  const vD = await visto();
  sub.pagata = {ritiri: vD.ritiri.filter(x => x === rS.id).length - vP.ritiri.filter(x => x === rS.id).length,
                ritiro: rec().ritiro && rec().ritiro.cooperativo, stato: (await fetchVero(`${BASE}/v2/swap/${rS.id}`).then(r => r.json())).status,
                spesa: (await fetchVero(`${BASE}/esplora/tx/${(await fetchVero(`${BASE}/v2/swap/submarine/${rS.id}/transaction`).then(r => r.json())).id}/outspend/0`).then(r => r.json())).spent};
  await run('swapGiro()');
  run('renderSwapCambio()');
  sub.fatto = [frase(), box().includes('id="swapCambioRicevi"'), rec().stato];
  run('renderSwapTelefono()');
  sub.lista = run('elementi.swapTelefono.innerHTML').includes('<b>Cambio</b>');
  /* IL CAMBIO FALLITO: i bitcoin tornano a due, all'indirizzo scritto */
  const nuovoSub = async f => {
    run("bigliettoRisposta = {ok: true, id: bigliettoRisposta.id + 1, oggi: 1}");
    run('renderSwapCambio()');
    run("swapCambioLato = 'ricevi'; elementi.swapCambioRicevi = {value: '100000'}");
    await run('swapCambioCalcola()');
    run(`elementi.swapFattura_0 = {value: ${JSON.stringify(f.invoice)}}`);
    await run('swapAvanti(0)');
    return lista().filter(r => r.tipo === 'sub').pop();
  };
  const r2 = await nuovoSub(F.fallita);
  await stato(r2.id, 'transaction.mempool');
  await run('swapGiro()');
  await stato(r2.id, 'invoice.failedToPay');
  await run('swapGiro()');
  const rec2 = () => lista().find(r => r.id === r2.id);
  const frase2 = () => run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(r2.id) + '))');
  run('renderSwapTelefono()');
  const pag2 = run('elementi.swapTelefono.innerHTML');
  sub.fallito = {fase: run('swapFase(swapLista().find(r => r.id === ' + JSON.stringify(r2.id) + '))'), frase: frase2(),
                 daRimborsare: run('swapDaRimborsare(swapLista().find(r => r.id === ' + JSON.stringify(r2.id) + '))'),
                 campo: pag2.includes(`id="swapIndirizzoR_${r2.id}"`) && pag2.includes('>Rimanda a questo indirizzo<'),
                 riquadro: (run('renderSwapCambio()'), box().includes('id="swapCambioRicevi"')), aperto: run('swapAperti().some(r => r.id === ' + JSON.stringify(r2.id) + ')')};
  run(`elementi.swapIndirizzoR_${r2.id} = {value: '${D.indirizzo}'}`);
  const scriptDest = run(`(() => { const S = window.BarattoloSwap; return S.hex.encode(S.OutScript.encode(S.Address(S.NETWORK).decode(${JSON.stringify(D.indirizzo)}))); })()`);
  const vR1 = await visto();
  await run(`swapRitiraA(${JSON.stringify(r2.id)})`);
  await finche(() => (rec2().rimborso || {}).txid || rec2().errore);
  const vR2 = await visto();
  const tR = vR2.trasmesse.find(x => rec2().rimborso && x.txid === rec2().rimborso.txid) || {};
  sub.rimborsato = {indirizzo: rec2().indirizzo, txid: /^[0-9a-f]{64}$/.test(String((rec2().rimborso || {}).txid || '')),
                    cooperativo: (rec2().rimborso || {}).cooperativo, firme: vR2.rimborsi.filter(x => x === r2.id).length - vR1.rimborsi.filter(x => x === r2.id).length,
                    errore: rec2().errore || '', via: tR.via, strade: (tR.strade || []).slice().sort(), aDest: !!(tR.uscite && tR.uscite[0] && tR.uscite[0].script === scriptDest),
                    fase: run('swapFase(swapLista().find(r => r.id === ' + JSON.stringify(r2.id) + '))'), frase: frase2(),
                    aperto: run('swapAperti().some(r => r.id === ' + JSON.stringify(r2.id) + ')')};
  /* LO SCADUTO coi bitcoin mandati e il fornitore che non firma: dallo
     script, alla scadenza */
  const r3 = await nuovoSub(F.scaduta);
  await stato(r3.id, 'transaction.mempool');
  await run('swapGiro()');
  await stato(r3.id, 'swap.expired');
  await run('swapGiro()');
  await modo('non_firma');
  run(`elementi.swapIndirizzoR_${r3.id} = {value: '${D.indirizzo}'}`);
  const rec3 = () => lista().find(r => r.id === r3.id);
  await run(`swapRitiraA(${JSON.stringify(r3.id)})`);
  await finche(() => rec3().aspettaScadenza || rec3().rimborso || rec3().errore);
  const frase3 = () => run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(r3.id) + '))');
  sub.presto = {rimborso: !!rec3().rimborso, aspetta: rec3().aspettaScadenza, frase: frase3(),
                aperto: run('swapAperti().some(r => r.id === ' + JSON.stringify(r3.id) + ')')};
  await fetchVero(`${BASE}/cartone/cima?h=${r3.timeoutBlockHeight}`).then(r => r.json());
  await run('swapGiro()');
  const vR3 = await visto();
  const tR3 = vR3.trasmesse.find(x => rec3().rimborso && x.txid === rec3().rimborso.txid) || {};
  sub.script = {txid: /^[0-9a-f]{64}$/.test(String((rec3().rimborso || {}).txid || '')), cooperativo: (rec3().rimborso || {}).cooperativo,
                via: tR3.via, strade: (tR3.strade || []).slice().sort(), aDest: !!(tR3.uscite && tR3.uscite[0] && tR3.uscite[0].script === scriptDest), fase: run('swapFase(swapLista().find(r => r.id === ' + JSON.stringify(r3.id) + '))'), frase: frase3()};
  await modo('normale');
  /* LO SCADUTO SENZA BITCOIN: niente da rimborsare */
  const r4 = await nuovoSub(F.vuota);
  await stato(r4.id, 'swap.expired');
  await run('swapGiro()');
  run('renderSwapTelefono()');
  sub.vuoto = {frase: run('frasestatoSwap(swapLista().find(r => r.id === ' + JSON.stringify(r4.id) + '))'),
               daRimborsare: run('swapDaRimborsare(swapLista().find(r => r.id === ' + JSON.stringify(r4.id) + '))'),
               campo: run('elementi.swapTelefono.innerHTML').includes(`id="swapIndirizzoR_${r4.id}"`),
               aperto: run('swapAperti().some(r => r.id === ' + JSON.stringify(r4.id) + ')')};
  /* il recupero dalla xpub ritrova anche i submarine, con la chiave di rimborso */
  const trovati = await fetchVero(`${BASE}/v2/swap/restore`, {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({xpub: run('(() => { const S = window.BarattoloSwap; return swapXpub(S, swapCassetto("satsrouting").parole); })()')})}).then(r => r.json());
  sub.recupero = trovati.filter(s => s.type === 'submarine').length;
  out.sub = sub;
  // --- la sentinella: il telefono ha chiamato solo il cartone
  out.sentinella = {fuori: chiamate.filter(c => !c.url.startsWith(BASE + '/v2/') && !c.url.startsWith(BASE + '/esplora/')).map(c => c.url),
                    paga: server().filter(s => s[0] === 'paga').length};
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def fatture_sub():
    """Le richieste Lightning «del wallet dell'utente» per la strada
    rovesciata: fatte dal cartone, col segreto che conosce il banco."""
    import hashlib
    import secrets
    out = {}
    for nome, sats, rete in (("buona", 100_000, "bitcoin"), ("fallita", 100_000, "bitcoin"),
                             ("scaduta", 100_000, "bitcoin"), ("vuota", 100_000, "bitcoin"),
                             ("importo", 99_000, "bitcoin"), ("regtest", 100_000, "regtest")):
        pre = secrets.token_bytes(32)
        imp = hashlib.sha256(pre).hexdigest()
        inv = cartone_satsrouting.cripto("fattura", rete=rete, sats=sats, impronta=imp)["invoice"]
        out[nome] = {"invoice": inv, "preimage": pre.hex(), "impronta": imp}
    return out


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
            "fattureSub": fatture_sub(),
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
    # (28 ott 2026, cantiere grafica-cambio) niente piu' tasto «🔁 Cambia»
    # ne' «Chiudi»: a leva accesa il riquadro e' gia' aperto
    prova("a leva del cambio spenta il riquadro e' vuoto", "", r["spento"])
    prova("accesa, SUBITO APERTO: «Mandi» col fulmine «LN» e «Ricevi circa» con la moneta "
          "«BTC» (unita-tendine; una strada sola: niente tendine, niente tondo), i due campi, "
          "il selettore ₿ / sats (sats scelto), i tetti, tre tesserine, l'indirizzo e "
          "«Conferma» spento; niente tasti di ieri, niente emoji fuori dalle icone disegnate",
          {"campo": True, "mandi": True, "ricevi": True, "tendine": 0, "unita": [2, True, True, True], "gira": 0, "tra": True, "tessere": 3,
           "indirizzo": True, "fermo": True, "vecchi": [], "emoji": []}, r["aperto"])
    prova("senza cifra: lo dice e non chiede niente", [True, 0], r["senzaCifra"])
    prova("la cifra scritta tasto per tasto: intanto «…» e «Conferma» spento, nessun "
          "preventivo; UNO solo quando si smette di scrivere",
          {"subito": 0, "puntini": True, "fermo": True, "dopo": 1}, r["attesa"])
    prova("100.000 (coi punti): la rotta del cambio, «Ricevi circa» 98.842, il costo in "
          "una riga (1.158 · SATS Routing) e le voci chiuse (dentro «Cambi», non «Ti "
          "spettano»), niente «Incassa in Lightning», l'indirizzo e «Conferma» acceso",
          {"letto": {"n": 0, "fornitore": "satsrouting", "hash": "", "sats": 100_000, "strada": "ln-btc",
                     "lato": "mandi", "scritta": 100_000},
           "cambi": True, "spettano": False, "ricevi": True, "costo": True, "chiuse": True,
           "incassaLn": False, "campo": True, "conferma": True, "calcola": False}, r["preventivo"])
    prova("«Dettagli» apre le voci, con le due frasi piccole", [True, False, True], r["dettagli"])
    prova("una risposta vecchia (di un'altra cifra, o dell'altro riquadro) non si mostra e "
          "non si conferma", [True, True, True], r["vecchia"])
    prova("(cambio-due-riquadri) scritti 98.000 in «Ricevi»: UN preventivo col lato "
          "«ricevi», «Mandi» si fa da solo (99.153), e il cambio nascerebbe con 99.153",
          {"chiesto": [["ricevi", 98_000, 99_153]], "mandi": True, "ricevi": True,
           "dovuto": 99_153, "cifra": 98_000, "conferma": True}, r["riceviScritto"])
    prova("il selettore sats/BTC: le cifre in BTC con otto decimali (riquadri, costo, "
          "voci, tetti), tastiera coi decimali, scelta salvata sul telefono; la cifra in "
          "sats e il conto non cambiano (nessun preventivo in piu'); poi si torna ai sats",
          {"mandi": True, "ricevi": True, "costo": True, "riga": True, "limiti": True,
           "acceso": True, "casa": "btc", "cifra": 100_000, "richiesti": 0,
           "tornato": [True, "sats"]}, r["unita"])
    prova("...le cifre scritte in BTC: virgola o punto, al piu' otto decimali; storte = 0",
          [100_000, 98_842, 150_000_000, 12_345_678, 0, 0, 10_000], r["leggi"])
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
    prova("la carta: «Cambio» con l'icona disegnata, la fattura da pagare col SUO wallet, «Copia», "
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
    prova("a cambio finito il riquadro torna aperto e PULITO: niente cifra ne' indirizzo di prima",
          [True, True, True], r["finito"])
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

    print("\n[il telefono, la strada bitcoin → Lightning (tappa 3)]")
    s = r.get("sub") or {}
    prova("con le due strade dal server, il tondo fra i riquadri (dice dove porta); "
          "girato: «Ricevi / LN» sotto, il tondo riporta indietro, e il conto si "
          "rifa' da solo per la strada nuova",
          ([1, True], [True, True, 1, "btc-ln"]), (s.get("pillole"), s.get("scelta")))
    prova("(cambio-due-riquadri) la cifra resta in «Mandi», ora on-chain: il conto al "
          "contrario dice quanto si riceve", ["mandi", 99_186, True], s.get("mandiScritto"))
    prova("(unita-tendine) con due strade la tendina in ogni pillola: LN e BTC, quella di "
          "adesso scelta; un tocco fuori la chiude; in «Ricevi» BTC e' la strada di sempre e "
          "LN quella rovesciata; la rete che c'e' gia' chiude e basta",
          {"pillole": 2, "menu": 2, "ln": True, "btc": True, "aperta": True, "chiusaFuori": True,
           "ricevi": [True, True], "stessa": [None, "ln-btc", False]}, s.get("tendina"))
    prova("...un sat in piu', mai in meno: scritti 100.015 da mandare, ne servono "
          "100.016; uscendo dal campo si vede la cifra vera, e il conto resta buono",
          ["100016", 100_016, 99_201, True, 0], s.get("unSatInPiu"))
    prova("il preventivo della strada rovesciata: quanto mandi, i costi col +, "
          "il campo della richiesta Lightning al posto dell'indirizzo",
          {"strada": "btc-ln", "titolo": True, "piu": True, "mandi": True, "riceviLn": True,
           "campoFattura": True, "campoIndirizzo": False, "spiega": True}, s.get("preventivo"))
    prova("(cambio-euro) sotto ogni cifra il controvalore, «≈ 95,78 €» e «≈ 95,00 €» "
          "a 95.000 €/BTC, dentro la cifra dopo l'unita'; senza un cambio vero in mano "
          "la riga resta vuota (mai un numero inventato)",
          {"senza": ["", ""], "con": ["≈ 95,78 €", "≈ 95,00 €"], "dentro": True, "spento": ["", ""]},
          s.get("euro"))
    prova("«Conferma» coi no della richiesta: manca, storta, importo sbagliato, altra "
          "rete; al server non va niente",
          ["Prima incolla la richiesta del tuo wallet Lightning: tocca «Incolla».",
           "Questa non sembra una richiesta Lightning: ricontrollala.",
           "La richiesta deve essere di 100000 sats esatti.",
           "Questa richiesta è di un'altra rete.", 0], s.get("fatturaNo"))
    prova("«Incolla» toglie «lightning:» davanti", True, s.get("incollata"))
    n = s.get("nata") or {}
    prova("la nascita rovesciata: biglietto (btc-ln), swap al cartone, nascita con "
          "l'indirizzo del lockup e quanto mandare; il record e' un «sub» dell'ordine 0",
          (["biglietto", "nato"], "btc-ln", 1, 0, "sub", 51, 100_818, 100_000, True, "", True, True,
           [True, 100_818, True], "creato", ""),
          (n.get("ordini"), (n.get("biglietto") or {}).get("direzione"), n.get("swap"), n.get("ordine"),
           n.get("tipo"), n.get("cambio"), n.get("mandi"), n.get("ricevi"), n.get("impronta"),
           n.get("indirizzoDelRimborso"), n.get("fattura"), n.get("lockup"), n.get("nato"),
           n.get("fase"), n.get("errore")))
    prova("la carta: «Manda esattamente 100818 sats…», l'indirizzo in chiaro, «Copia "
          "l'indirizzo», il link bitcoin: con la cifra, i passi Mandati → Pagato, niente "
          "fattura da pagare; il QR e' il link bitcoin: (byte)",
          {"manda": True, "indirizzo": True, "copia": True, "wallet": True, "passi": True,
           "fatturaLn": False, "qr": ["swapCambioQr", "bitcoin:bc1p", "Byte"]}, s.get("carta"))
    prova("«Copia l'indirizzo» negli appunti", ["APPUNTI:bc1p", "Copiata"], s.get("copiaIndirizzo"))
    prova("i bitcoin visti: «bloccato», il record lo ricorda, la frase", 
          ["bloccato", True, "Bitcoin visti: aspetto la conferma della rete, di solito una decina di minuti."],
          s.get("visti"))
    prova("confermati: «SATS Routing sta pagando la tua richiesta»",
          "Confermati: SATS Routing sta pagando la tua richiesta.", s.get("confermati"))
    prova("la fattura pagata: la nostra meta' del ritiro a due (una volta), il cartone "
          "ritira (transaction.claimed) e il lockup e' speso",
          {"ritiri": 1, "ritiro": True, "stato": "transaction.claimed", "spesa": True}, s.get("pagata"))
    prova("fatto: la frase, il riquadro torna aperto, lo stato",
          ["Fatto: i sats sono nel tuo wallet Lightning.", True, "transaction.claimed"], s.get("fatto"))
    prova("...e nella lista si chiama «Cambio»", True, s.get("lista"))
    prova("un cambio fallito coi bitcoin mandati: «fallito», la frase chiede dove rimandarli, "
          "il campo nella lista, il riquadro libero, e NON e' in sorveglianza senza indirizzo",
          {"fase": "fallito", "frase": "Non riuscito: i tuoi bitcoin tornano a te. Scrivi sotto dove rimandarli.",
           "daRimborsare": True, "campo": True, "riquadro": True, "aperto": False}, s.get("fallito"))
    prova("l'indirizzo scritto: il rimborso a due parte subito (sulle due strade, "
          "alla destinazione), «ripreso», e lo swap esce dalla sorveglianza",
          {"indirizzo": INDIRIZZO, "txid": True, "cooperativo": True, "firme": 1, "via": "cooperativo",
           "errore": "", "strade": ["fornitore", "rete"], "aDest": True, "fase": "ripreso", "frase": True, "aperto": False},
          dict(s.get("rimborsato") or {}, frase=str((s.get("rimborsato") or {}).get("frase", "")).startswith("Ripresi: i bitcoin sono tornati al tuo indirizzo (")))
    prova("lo scaduto col fornitore che non firma: prima della scadenza «ci penso io», "
          "resta in sorveglianza",
          {"rimborso": False, "aspetta": True,
           "frase": "I bitcoin tornano a te alla scadenza: ci penso io, apri l'app ogni tanto.", "aperto": True},
          s.get("presto"))
    prova("...alla scadenza il rimborso dalla foglia dello script, alla destinazione, «ripreso»",
          {"txid": True, "cooperativo": False, "via": "rimborso", "strade": ["fornitore", "rete"], "aDest": True,
           "fase": "ripreso", "frase": True},
          dict(s.get("script") or {}, frase=str((s.get("script") or {}).get("frase", "")).startswith("Ripresi:")))
    prova("lo scaduto senza bitcoin mandati: niente da rimborsare, nessun campo, fuori dalla sorveglianza",
          {"frase": "Scaduto: nessun bitcoin si è mosso. Puoi fare un cambio nuovo.", "daRimborsare": False,
           "campo": False, "aperto": False}, s.get("vuoto"))
    prova("il recupero dalla xpub ritrova anche i quattro submarine", 4, s.get("recupero"))

def main():
    global PORTA
    print("=" * 58)
    print("  🔁 IL CAMBIO LIBERO, TAPPE 2 E 3 — il biglietto, il giro vero")
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
