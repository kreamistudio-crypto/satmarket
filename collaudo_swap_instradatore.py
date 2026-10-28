# -*- coding: utf-8 -*-
"""
LO SWAP, L'INSTRADATORE: DUE FORNITORI, IL MIGLIORE, IL RIPIEGO (20 ott
2026, cantiere swap-instradatore, decisione di Andrea).

Chi vende sceglie COSA vuole (ricevere bitcoin on-chain), non CHI lo fa:
il telefono chiede il preventivo a ogni fornitore che sa fare la strada e
sceglie quello che fa ricevere di piu'; se quello risponde con dati che non
tornano si ripiega sul secondo MOSTRANDO il suo preventivo e chiedendo una
nuova conferma; se non ce n'e' un altro ci si ferma, col perche'.

DUE SATS ROUTING DI CARTONE (`cartone_satsrouting.py`) su due porte di
questo computer: il primo e' «SATS Routing» (0,6 %, le leve di sempre), il
secondo e' «Cartone Due» (0,3 %, da `SWAP_FORNITORI_IN_PIU`). I preventivi
li calcola il server VERO (TestClient) per ogni ordine e ogni fornitore;
il codice VERO del telefono (`swap/boltz.js`, `swap/instradatore.js`, il
preventivo della pagina) gira in node contro i due cartoni per HTTP.

LE SCENE:
  - il server: in /api/me i due fornitori; il preventivo per fornitore
    (Cartone Due fa ricevere di piu'); un fornitore sconosciuto e' 404; la
    CSP apre le due origini; le voci storte di SWAP_FORNITORI_IN_PIU si
    saltano;
  - il migliore: l'instradatore sceglie Cartone Due, il preventivo dice
    «Eseguito da Cartone Due», le parole sono SUE, lo swap nasce li' e li'
    si ritira;
  - il ripiego: Cartone Due mente, si mostra il preventivo di SATS Routing
    con una nuova conferma, nascono le parole di SATS Routing, lo swap
    nasce li';
  - mentono tutt'e due: ci si ferma col perche', niente salvato;
  - il fuori-gioco vale per QUELL'ordine: su un ordine nuovo Cartone Due
    torna in gara; e se e' giu' vince SATS Routing;
  - il recupero per fornitore: le parole di Cartone Due ritrovano i SUOI
    swap, e la xpub va solo a lui;
  - LA SENTINELLA: nessuna chiamata al server di Barattolo dai file del
    telefono, in nessuna le parole o una chiave privata.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1; nessuno swap vero, nessun sats.

USO:  python collaudo_swap_instradatore.py
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
ADMIN = {"X-Tg-Init-Data": "collaudo:999:Admin"}
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
PORTE = {}


def cartone(chi, percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTE[chi]}{percorso}",
                                timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def semina():
    con = banco.SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((999, "Admin"), (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, f"neg{tg}0000"))
    ids = []
    for k in range(5):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(999,?,'una cosa',48000,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (f"Cosa {k}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    ordini = []
    for a in ids:
        oid = banco.ordine_pagato(a)
        con = banco.SRV.db()
        con.execute("UPDATE ordini SET stato='confirmed' WHERE id=?", (oid,))
        con.commit()
        con.close()
        ordini.append(oid)
    return ordini


def preventivo(c, oid, fornitore):
    banco.come(999, admin=True)
    r = c.get(f"/api/swap/preventivo/{oid}?fornitore={fornitore}", headers=ADMIN)
    return r.status_code, (r.json() if r.content else {})


def senza_copia(srv):
    srv._TARIFFE_SWAP.update(quando=0.0, dati=None)
    srv._TARIFFE_SWAP_ALTRI.clear()


def pezzi_pagina():
    """Dalla pagina: la lettura delle fatture, i testi e il preventivo
    della tappa 2 (con «eseguito da» e il ripiego)."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    mini = mini.replace("\r\n", "\n")

    def tra(a, b):
        i = mini.index(a)
        return mini[i:mini.index(b, i)]
    return (tra("function importoBolt11(pr){", "\n}\n") + "\n}\n"
            + tra("function leggiBolt11(pr){", "\n}\n") + "\n}\n"
            + tra("const SWAP_TESTI = {", "function linguaSwap(){")
            + tra("function percentoSwap(p){", "function renderSwap(){"))


BANCO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const BUNDLE = fs.readFileSync(D.bundle, 'utf8');
const TELEFONO = D.telefono.map(f => fs.readFileSync(f, 'utf8'));
const fetchVero = globalThis.fetch;
const chiamate = [];
const letti = [];             // i preventivi chiesti: [ordine, fornitore]
const html = [];
const [B1, B2] = [D.basi.satsrouting, D.basi.cartone2];
const modo = (b, m) => fetchVero(`${b}/cartone/modo?m=${m}`).then(r => r.json());
const stato = (b, id, s) => fetchVero(`${b}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const visto = b => fetchVero(`${b}/cartone/visto`).then(r => r.json());

function pagina(memoria){
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
let myTgId = 222;
const FOTO_BASE = '';
let swapLeve = ${JSON.stringify(D.leve)};
const swapAcceso = () => !!(swapLeve && swapLeve.attivo);
const elementi = {};
function el(id){ return elementi[id] || null; }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const fmt = n => String(n);
function haptic(){}
function toast(){}
let currentOrder = null;
let preventiviSwap = {}, sceltaIncassoSwap = {};
function ridisegnaIncassoSwap(){}
function linguaSwap(){ return 'it'; }
function testiSwap(){ return SWAP_TESTI.it; }
function scegliIncassoSwap(){}
const PREVENTIVI = ${JSON.stringify(D.preventivi)};
/* (24 ott 2026, tappa 4) il pagamento lo prova collaudo_swap_pagamento */
async function pagaSwapAlServer(){ return null; }
async function statoPagamentoSwap(){ return null; }
async function leggiPreventivoSwap(n, fornitore){
  __letti.push([Number(n), fornitore]);
  return JSON.parse(JSON.stringify(PREVENTIVI[n][fornitore]));
}
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const ascoltatori = [];
const document = {addEventListener: (t, f) => ascoltatori.push([t, f]),
                  head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
`, Object.assign(ctx, {__memoria: memoria, __letti: letti}));
  vm.runInContext(D.pagina, ctx);
  for (const codice of TELEFONO) vm.runInContext(codice, ctx);
  return {ctx, run: codice => vm.runInContext(codice, ctx)};
}
const S = vm.runInNewContext(BUNDLE + ';BarattoloSwap', {crypto: globalThis.crypto, TextEncoder, TextDecoder});
const O = D.ordini;

(async () => {
  const out = {};
  const mem = new Map();
  const A = pagina(mem);
  const lista = m => JSON.parse(m.get('barattolo_swap_lista_222') || '[]');
  const cass = (m, k) => JSON.parse(m.get(k) || 'null');
  const fornitori = A.run('swapFornitori().map(f => [f.id, f.nome, f.tipo, f.strade])');
  out.fornitori = fornitori;

  // --- il migliore: Cartone Due
  const o1 = O[0];
  await A.run(`swapInstradaPreventivo(${o1}, false)`);
  const p1 = A.run(`preventiviSwap[${o1}]`);
  const pann1 = A.run(`pannelloSwapTelefono({id: ${o1}})`);
  html.push(pann1);
  out.migliore = {chi: p1.dati.fornitore, ricevi: p1.dati.ricevi,
                  chiesti: letti.filter(l => l[0] === o1).map(l => l[1]).sort(),
                  eseguito: pann1.includes('Il cambio lo fa Cartone Due'),
                  voce: pann1.includes('Costo del cambio, Cartone Due (0,3\u00a0%)')};
  /* (27 ott 2026, grafica-swap) l'indirizzo sta sopra «Conferma» */
  A.run(`elementi.swapIndirizzo_${o1} = {value: '${D.indirizzo}'}`);
  await A.run(`swapAvanti(${o1})`);
  out.paroleSue = [A.run(`swapPassi[${o1}]`), !!cass(mem, 'barattolo_swap_cartone2_222'),
                   !!cass(mem, 'barattolo_swap_222')];
  const pp = A.run(`pannelloSwapTelefono({id: ${o1}})`);
  html.push(pp);
  out.titoloParole = pp.includes('Le tue 12 parole di riserva per Cartone Due');
  A.run(`elementi.swapSpunta_${o1} = {checked: true}`);
  /* «Continua» fa nascere lo swap da solo */
  await A.run(`swapParoleFatte(${o1})`);
  const r1 = lista(mem).find(r => r.ordine === o1) || {};
  const v2 = await visto(B2), v1 = await visto(B1);
  out.nato = {fornitore: r1.fornitore, ricevi: r1.ricevi, errore: A.run(`swapErrori[${o1}] || ''`),
              daDue: v2.swap, daUno: v1.swap};
  const carta = A.run(`pannelloSwapTelefono({id: ${o1}})`);
  html.push(carta);
  out.carta = carta.includes('Il cambio lo fa Cartone Due');
  await stato(B2, r1.id, 'transaction.mempool');
  await A.run('swapGiro()');
  await A.run('swapGiro()');
  const r1b = lista(mem).find(r => r.ordine === o1) || {};
  out.ritiro = {txid: !!(r1b.ritiro && r1b.ritiro.txid), stato: r1b.stato,
                dueTrasmesse: (await visto(B2)).trasmesse.length,
                unoTrasmesse: (await visto(B1)).trasmesse.length};

  // --- il ripiego: Cartone Due mente
  const o2 = O[1];
  await modo(B2, 'mente_indirizzo');
  await A.run(`swapInstradaPreventivo(${o2}, false)`);
  out.ripiegoPrima = A.run(`preventiviSwap[${o2}].dati.fornitore`);
  A.run(`elementi.swapIndirizzo_${o2} = {value: '${D.indirizzo}'}`);
  await A.run(`swapAvanti(${o2})`);
  const p2 = A.run(`preventiviSwap[${o2}]`);
  const pann2 = A.run(`pannelloSwapTelefono({id: ${o2}})`);
  html.push(pann2);
  out.ripiego = {passo: A.run(`swapPassi[${o2}]`), nota: p2.nota, chi: p2.dati.fornitore,
                 ricevi: p2.dati.ricevi, salvati: lista(mem).filter(r => r.ordine === o2).length,
                 frase: pann2.includes('Cartone Due ha dato cifre che non tornano: ecco quelle di SATS Routing.'),
                 eseguito: pann2.includes('Il cambio lo fa SATS Routing'),
                 conferma: pann2.includes('data-swap="avanti"')};
  await A.run(`swapAvanti(${o2})`);
  out.ripiegoParole = [A.run(`swapPassi[${o2}]`), !!cass(mem, 'barattolo_swap_222')];
  A.run(`elementi.swapSpunta_${o2} = {checked: true}`);
  await A.run(`swapParoleFatte(${o2})`);
  const r2 = lista(mem).find(r => r.ordine === o2) || {};
  out.ripiegoNato = {fornitore: r2.fornitore, ricevi: r2.ricevi, errore: A.run(`swapErrori[${o2}] || ''`),
                     daUno: (await visto(B1)).swap};

  // --- mentono tutt'e due
  const o3 = O[2];
  await modo(B1, 'mente_importo');
  await A.run(`swapInstradaPreventivo(${o3}, false)`);
  A.run(`elementi.swapIndirizzo_${o3} = {value: '${D.indirizzo}'}`);
  await A.run(`swapAvanti(${o3})`);
  out.tuttiPrimo = [A.run(`preventiviSwap[${o3}].nota`), A.run(`preventiviSwap[${o3}].dati.fornitore`)];
  await A.run(`swapAvanti(${o3})`);
  out.tutti = {passo: A.run(`swapPassi[${o3}]`), errore: A.run(`swapErrori[${o3}] || ''`),
               salvati: lista(mem).filter(r => r.ordine === o3).length};
  await modo(B1, 'normale');
  await modo(B2, 'normale');

  // --- il fuori-gioco vale per quell'ordine; e se Cartone Due e' giu'
  const o4 = O[3], o5 = O[4];
  await A.run(`swapInstradaPreventivo(${o4}, false)`);
  await A.run(`swapInstradaPreventivo(${o5}, false)`);
  out.nuovoOrdine = A.run(`preventiviSwap[${o4}].dati.fornitore`);
  out.dueGiu = A.run(`preventiviSwap[${o5}].dati.fornitore`);

  // --- la pagina Swap con due fornitori, e il recupero per fornitore
  A.run(`elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}`);
  A.run('renderSwapTelefono()');
  // (28 ott 2026, grafica-cambio) la riga delle 12 parole sta chiusa in fondo:
  // si apre col tocco, e solo allora parole e recupero si vedono
  const chiusa = A.run('elementi.swapTelefono.innerHTML');
  out.chiusa = [chiusa.includes('Le 12 parole e il recupero'), chiusa.includes('data-swap="riserva"'),
                chiusa.includes('Recupera da'), chiusa.includes('Le tue 12 parole di riserva')];
  A.run('swapRiservaAperta = true; renderSwapTelefono()');
  const pag = A.run('elementi.swapTelefono.innerHTML');
  html.push(pag);
  out.pagina = [pag.includes('Le tue 12 parole di riserva per SATS Routing'), pag.includes('Le tue 12 parole di riserva per Cartone Due'),
                pag.includes('Recupera da SATS Routing'), pag.includes('Recupera da Cartone Due'),
                pag.includes('data-fornitore="cartone2"')];
  const paroleDue = cass(mem, 'barattolo_swap_cartone2_222').parole;
  const memC = new Map();
  const C = pagina(memC);
  const primaDiC = chiamate.length;
  C.run(`elementi.swapRecupero = {value: ${JSON.stringify(paroleDue)}}; elementi.swapRecuperoNota = {textContent: ''}`);
  await C.run(`swapRecupera('cartone2')`);
  const lc = lista(memC);
  out.recupero = {nota: C.run('elementi.swapRecuperoNota.textContent'),
                  fornitori: [...new Set(lc.map(r => r.fornitore))],
                  prossimo: (cass(memC, 'barattolo_swap_cartone2_222') || {}).prossimo,
                  sats: !!cass(memC, 'barattolo_swap_222'),
                  dove: chiamate.slice(primaDiC).filter(c => c.corpo.includes('xpub')).map(c => c.url.startsWith(B2))};

  // --- la sentinella
  const valori = [];
  const raccogli = v => { if (v && typeof v === 'object') Object.values(v).forEach(raccogli);
                          else if (v !== undefined && v !== null) valori.push(String(v)); };
  for (const c of chiamate) { try { raccogli(JSON.parse(c.corpo || 'null')); } catch(e){ valori.push(c.corpo); } }
  const soloValori = valori.join('\n').toLowerCase();
  const tutte = [cass(mem, 'barattolo_swap_222').parole, paroleDue];
  const priv = [];
  for (const p of tutte) for (let i = 0; i < 6; i++)
    priv.push(S.hex.encode(S.HDKey.fromMasterSeed(S.mnemonicToSeedSync(p)).derive(`m/44/0/0/0/${i}`).privateKey));
  /* (20 ott 2026, swap-lockup) i due fornitori, e i loro finti mempool da
     cui si legge il lockup e su cui si trasmette il ritiro (dal 20 ott,
     swap-senza-api): mai fuori dal computer */
  out.sentinella = {fuori: chiamate.filter(c => ![B1 + '/v2/', B2 + '/v2/', B1 + '/esplora/', B2 + '/esplora/']
                                             .some(b => c.url.startsWith(b))).length,
                    parole: tutte.some(p => p.split(' ').some(w => new RegExp('\\b' + w + '\\b').test(soloValori))),
                    privata: priv.some(k => soloValori.includes(k) || chiamate.some(c => c.url.includes(k)))};
  out.onclick = html.filter(h => /\son[a-z]+=/i.test(h)).length;
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def telefono(dati):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="swap_instradatore_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO)
        open(d, "w", encoding="utf-8").write(json.dumps(dati))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1500:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def il_server(c, srv, basi, ordini):
    print("\n[il server: i fornitori, il preventivo per fornitore, la CSP]")
    banco.come(999, admin=True)
    leve = (c.get("/api/me", headers=ADMIN).json() or {}).get("swap_leve") or {}
    prova("in /api/me i due fornitori, SATS Routing per primo",
          [("satsrouting", "SATS Routing", "boltz", basi["satsrouting"], "barattolo"),
           ("cartone2", "Cartone Due", "boltz", basi["cartone2"], "")],
          [(f["id"], f["nome"], f["tipo"], f["api"], f["referral"])
           for f in leve.get("fornitori", [])])
    senza_copia(srv)
    c1, p1 = preventivo(c, ordini[0], "satsrouting")
    c2, p2 = preventivo(c, ordini[0], "cartone2")
    prova("il preventivo per fornitore: Cartone Due (0,3 %) fa ricevere di piu'",
          (200, 47_154, "SATS Routing", 200, 47_298, "Cartone Due", "cartone-tariffa-p0.3"),
          (c1, p1.get("ricevi"), p1.get("fornitore_nome"), c2, p2.get("ricevi"),
           p2.get("fornitore_nome"), p2.get("hash")))
    prova("...e il codice partner va solo dove c'e'", ("barattolo", None),
          (cartone("satsrouting", "/cartone/visto")["referral"],
           cartone("cartone2", "/cartone/visto")["referral"]))
    prova("un fornitore sconosciuto: 404", 404, preventivo(c, ordini[0], "chissa")[0])
    connect = next(x for x in srv._csp_prova(True).split("; ")
                   if x.startswith("connect-src"))
    prova("la CSP apre le due origini, una volta ciascuna", (1, 1),
          (connect.count(basi["satsrouting"]), connect.count(basi["cartone2"])))
    vero = srv.SWAP_FORNITORI_IN_PIU
    srv.SWAP_FORNITORI_IN_PIU = vero + [
        {"id": "satsrouting", "nome": "Doppione", "tipo": "boltz", "api": basi["cartone2"]},
        {"id": "x", "nome": "Corto", "tipo": "boltz", "api": basi["cartone2"]},
        {"id": "tipoignoto", "nome": "Ignoto", "tipo": "kaleido", "api": basi["cartone2"]},
        {"id": "senzaapi", "nome": "Senza", "tipo": "boltz", "api": "ftp://x"},
        "non e' nemmeno un dizionario"]
    prova("le voci storte di SWAP_FORNITORI_IN_PIU si saltano",
          ["satsrouting", "cartone2"], [f["id"] for f in srv.swap_fornitori()])
    srv.SWAP_FORNITORI_IN_PIU = vero


def il_telefono(dati):
    r = telefono(dati)
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return
    print("\n[il migliore]")
    # (cambio-libero, tappa 3: il tipo sa le due strade; quali si offrono
    # lo dice il server con le sue leve)
    prova("il telefono conosce i due fornitori, le stesse strade",
          [["satsrouting", "SATS Routing", "boltz", ["ln-btc", "btc-ln"]],
           ["cartone2", "Cartone Due", "boltz", ["ln-btc", "btc-ln"]]], r["fornitori"])
    m = r["migliore"]
    prova("chiede il preventivo a tutt'e due e sceglie chi fa ricevere di piu'",
          ("cartone2", 47_298, ["cartone2", "satsrouting"], True, True),
          (m.get("chi"), m.get("ricevi"), m.get("chiesti"), m.get("eseguito"),
           m.get("voce")))
    prova("le parole sono di Cartone Due, non di SATS Routing",
          (["parole", True, False], True), (r["paroleSue"], r["titoloParole"]))
    prova("lo swap nasce da Cartone Due, e solo li'",
          {"fornitore": "cartone2", "ricevi": 47_298, "errore": "", "daDue": 1, "daUno": 0},
          r["nato"])
    prova("...la carta dice chi lo esegue", True, r["carta"])
    prova("...e si ritira da Cartone Due",
          {"txid": True, "stato": "invoice.settled", "dueTrasmesse": 1, "unoTrasmesse": 0},
          r["ritiro"])

    print("\n[il ripiego]")
    prova("Cartone Due resta il migliore finche' non mente", "cartone2", r["ripiegoPrima"])
    rp = r["ripiego"]
    prova("quando mente: il preventivo di SATS Routing, con una nuova conferma, niente salvato",
          {"passo": "preventivo", "nota": "ripiego", "chi": "satsrouting", "ricevi": 47_154,
           "salvati": 0, "frase": True, "eseguito": True, "conferma": True}, rp)
    prova("...confermato, nascono le parole di SATS Routing", ["parole", True], r["ripiegoParole"])
    prova("...e lo swap nasce da SATS Routing",
          {"fornitore": "satsrouting", "ricevi": 47_154, "errore": "", "daUno": 1},
          r["ripiegoNato"])

    print("\n[mentono tutt'e due]")
    prova("il primo ripiego c'e'", ["ripiego", "satsrouting"], r["tuttiPrimo"])
    prova("poi ci si ferma col perche', niente salvato",
          {"passo": "preventivo",
           "errore": "SATS Routing ha risposto con dati che non tornano: non parte niente, nessun sats si è mosso.",
           "salvati": 0}, r["tutti"])
    prova("il fuori-gioco vale per quell'ordine: su un altro Cartone Due torna in gara",
          "cartone2", r["nuovoOrdine"])
    prova("...e con Cartone Due giu' vince SATS Routing", "satsrouting", r["dueGiu"])

    print("\n[la pagina Swap e il recupero per fornitore]")
    prova("le 12 parole stanno in una riga chiusa, che si apre col tocco",
          [True, True, False, False], r["chiusa"])
    prova("le parole e il recupero, uno per fornitore", [True] * 5, r["pagina"])
    rc = r["recupero"]
    prova("le parole di Cartone Due ritrovano i SUOI swap, e la xpub va solo a lui",
          {"nota": "Recuperati 3 incassi.", "fornitori": ["cartone2"], "prossimo": 3,
           "sats": False, "dove": [True]}, rc)

    print("\n[la sentinella]")
    prova("dal telefono nessuna chiamata fuori dai due fornitori", 0,
          r["sentinella"]["fuori"])
    prova("...in nessuna le parole o una chiave privata", (False, False),
          (r["sentinella"]["parole"], r["sentinella"]["privata"]))
    prova("nessun onclick nel markup", 0, r["onclick"])


def main():
    print("=" * 58)
    print("  ₿ LO SWAP, L'INSTRADATORE — due fornitori, il migliore")
    print("=" * 58)
    banco.avvio()
    import httpx
    from fastapi.testclient import TestClient

    srv = banco.SRV
    srv.httpx = httpx           # le tariffe vanno davvero ai cartoni
    _, PORTE["satsrouting"] = cartone_satsrouting.avvia(0)
    _, PORTE["cartone2"] = cartone_satsrouting.avvia(0, percento=0.3)
    basi = {k: f"http://127.0.0.1:{v}" for k, v in PORTE.items()}
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_MIN_SATS = 25_000
    srv.SWAP_MAX_SATS = 50_000
    srv.SWAP_FEE_PERCENTO = 0
    srv.SWAP_API_BASE = basi["satsrouting"]
    srv.SWAP_REFERRAL_ID = "barattolo"
    srv.SWAP_RETE = "bitcoin"
    # (20 ott 2026, swap-lockup) il lockup si legge dal finto mempool di
    # ogni cartone: in collaudo mai il mempool.space vero
    srv.SWAP_MEMPOOL_API = basi["satsrouting"] + "/esplora"
    srv.SWAP_FORNITORI_IN_PIU = [{"id": "cartone2", "nome": "Cartone Due",
                                  "tipo": "boltz", "api": basi["cartone2"],
                                  "referral": "", "rete": "bitcoin",
                                  "mempool": basi["cartone2"] + "/esplora"}]
    c = TestClient(srv.app)
    ordini = semina()
    il_server(c, srv, basi, ordini)

    # i preventivi del server, per ogni ordine e ogni fornitore; per
    # l'ultimo con Cartone Due giu'
    prev = {}
    for oid in ordini[:4]:
        senza_copia(srv)
        prev[oid] = {f: preventivo(c, oid, f)[1] for f in ("satsrouting", "cartone2")}
    cartone("cartone2", "/cartone/modo?m=giu")
    senza_copia(srv)
    prev[ordini[4]] = {f: preventivo(c, ordini[4], f)[1] for f in ("satsrouting", "cartone2")}
    cartone("cartone2", "/cartone/modo?m=normale")
    banco.come(999, admin=True)
    leve = (c.get("/api/me", headers=ADMIN).json() or {}).get("swap_leve") or {}
    il_telefono({
        "basi": basi, "indirizzo": INDIRIZZO, "ordini": ordini,
        "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
        "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                     os.path.join(banco.QUI, "swap", "instradatore.js")],
        "pagina": pezzi_pagina(), "leve": leve, "preventivi": prev})
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
