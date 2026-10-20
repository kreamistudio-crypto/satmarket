# -*- coding: utf-8 -*-
"""
LO SWAP, TAPPA 3: LO SWAP DAL TELEFONO (20 ott 2026, cantiere
swap-telefono).

Il codice VERO del telefono (`swap/boltz.js` e `swap/instradatore.js`
dal 20 ott 2026, prima `swap-telefono.js`; con la lettura delle
fatture di miniapp.html e la libreria `vendor/swap.bundle.js`) girato in
node, pagina per pagina, contro il SATS ROUTING DI CARTONE acceso su una
porta di questo computer: le chiamate passano davvero per HTTP, la
crittografia e' vera da tutt'e due le parti, e la firma del ritiro la
giudica il cartone in Python puro (BIP-340), non la libreria del telefono.

LE SCENE:
  - il server: in /api/me dove parlare e su quale rete; la CSP che a swap
    acceso ammette la sola origine di SATS Routing; le due rotte dei file;
  - la prima volta nascono le 12 parole, e senza la spunta «le ho scritte»
    non si va avanti;
  - un indirizzo sbagliato non chiede niente a nessuno;
  - SATS ROUTING CHE MENTE, cinque modi (importo, impronta, albero,
    indirizzo, meno on-chain): il telefono rifiuta, non salva niente, e
    l'indice della chiave non si riusa;
  - lo swap vero: col codice partner, e il telefono lo salva;
  - gli stati: a bitcoin bloccati il telefono ritira DA SOLO, cooperativo,
    e il cartone accetta la firma; poi «fatto»;
  - SATS Routing che non firma: si ritira dallo script;
  - la RIPRESA: uno swap lasciato a meta' si ritira alla riapertura;
  - il RECUPERO da 12 parole su un telefono vuoto: tutti gli swap, e il
    contatore delle chiavi riparte dopo il piu' alto;
  - LA SENTINELLA: nessuna chiamata verso il server di Barattolo, e in
    nessuna chiamata le parole o una chiave privata;
  - niente onclick nel markup del telefono: un solo ascoltatore delegato.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1 (in CI la gabbia di `collaudi_ci.py`); nessuno swap vero, nessun
sats: i bitcoin «bloccati» sono una transazione inventata dal cartone. Il
server di Barattolo in questa tappa non paga la fattura dello swap.

USO:  python collaudo_swap_telefono.py
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
PORTA = 0
INDIRIZZO = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"


def cartone(percorso):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}{percorso}",
                                timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def pezzi_pagina():
    """Dalla pagina: la lettura delle fatture (importo e impronta)."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    mini = mini.replace("\r\n", "\n")
    i = mini.index("function importoBolt11(pr){")
    j = mini.index("\n}\n", i) + 3
    k = mini.index("function leggiBolt11(pr){")
    m = mini.index("\n}\n", k) + 3
    return mini[i:j] + mini[k:m]


BANCO = r"""
const fs = require('fs');
const vm = require('vm');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const BUNDLE = fs.readFileSync(D.bundle, 'utf8');
/* i file del telefono (20 ott 2026, divisi dall'instradatore): il tipo
   del fornitore, poi l'instradatore, nell'ordine della pagina */
const TELEFONO = D.telefono.map(f => fs.readFileSync(f, 'utf8'));
const fetchVero = globalThis.fetch;
const chiamate = [];          // ogni chiamata di ogni pagina
const html = [];              // ogni markup scritto dal telefono
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = D.base;
const modo = m => fetchVero(`${BASE}/cartone/modo?m=${m}`).then(r => r.json());
const stato = (id, s) => fetchVero(`${BASE}/cartone/stato?id=${id}&s=${s}`).then(r => r.json());
const visto = () => fetchVero(`${BASE}/cartone/visto`).then(r => r.json());

/* UNA PAGINA: un contesto suo (le variabili della pagina), il cassetto
   del telefono passato da fuori (cosi' una riapertura lo ritrova) */
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
const avvisi = [];
function toast(m){ avvisi.push(m); }
let currentOrder = null;
function payoutPanel(){ return ''; }
let preventiviSwap = {}, sceltaIncassoSwap = {};
let disegni = 0;
function ridisegnaIncassoSwap(){ disegni++; }
/* il preventivo del server, di cartone: con un fornitore solo, la sua
   lettura e' quella di prima (l'instradatore la mette in preventiviSwap) */
async function leggiPreventivoSwap(n, fornitore){
  return Object.assign(${JSON.stringify(D.preventivo)}, {fornitore: fornitore || 'satsrouting', fornitore_nome: 'SATS Routing'});
}
function pannelloPreventivoSwap(){ return '<div>preventivo</div>'; }
const scelte = [];
function scegliIncassoSwap(n, s){ scelte.push([n, s]); }
function linguaSwap(){ return 'it'; }
const localStorage = {getItem: k => __memoria.has(k) ? __memoria.get(k) : null,
                      setItem: (k, v) => { __memoria.set(k, String(v)); },
                      removeItem: k => { __memoria.delete(k); }};
const ascoltatori = [];
const document = {addEventListener: (t, f) => ascoltatori.push([t, f]),
                  head: {appendChild(){}}, createElement(){ return {}; }};
const setInterval = () => 1, clearInterval = () => {};
`, Object.assign(ctx, {__memoria: memoria}));
  vm.runInContext(D.bolt11, ctx);
  for (const codice of TELEFONO) vm.runInContext(codice, ctx);
  const run = codice => vm.runInContext(codice, ctx);
  return {ctx, run};
}
const S = vm.runInNewContext(BUNDLE + ';BarattoloSwap', {crypto: globalThis.crypto, TextEncoder, TextDecoder});

(async () => {
  const out = {};
  const memA = new Map();
  const A = pagina(memA);
  const cassetto = () => JSON.parse(memA.get('barattolo_swap_222') || 'null');
  const lista = mem => JSON.parse(mem.get('barattolo_swap_lista_222') || '[]');
  out.ascoltatori = A.run('ascoltatori.map(a => a[0])');

  // --- la prima volta: le parole
  await A.run('swapAvanti(7)');
  const c0 = cassetto();
  out.parole = {quante: c0 && c0.parole.split(' ').length,
                valide: !!(c0 && S.validateMnemonic(c0.parole, S.wordlist)),
                copiata: c0 && c0.copiata, prossimo: c0 && c0.prossimo,
                passo: A.run('swapPassi[7]')};
  const p0 = A.run('pannelloSwapTelefono({id: 7})');
  html.push(p0);
  out.parolePannello = (p0.match(/<li>/g) || []).length;
  A.run("elementi.swapSpunta_7 = {checked: false}");
  A.run('swapParoleFatte(7)');
  out.senzaSpunta = [A.run('swapPassi[7]'), A.run('swapErrori[7]'), cassetto().copiata];
  A.run("elementi.swapSpunta_7 = {checked: true}");
  A.run('swapParoleFatte(7)');
  out.conSpunta = [A.run('swapPassi[7]'), cassetto().copiata];
  html.push(A.run('pannelloSwapTelefono({id: 7})'));

  // --- un indirizzo sbagliato non chiede niente
  const primaCh = chiamate.length;
  A.run("elementi.swapIndirizzo_7 = {value: 'bc1qnonvalido'}");
  await A.run('swapCrea(7)');
  out.indirizzoNo = [A.run('swapErrori[7]'), chiamate.length - primaCh, cassetto().prossimo,
                     /* ...e il campo, ridisegnato, ricorda quel che c'era scritto */
                     A.run('pannelloSwapTelefono({id: 7})').includes('value="bc1qnonvalido"')];

  // --- SATS Routing che mente
  A.run(`elementi.swapIndirizzo_7 = {value: '${D.indirizzo}'}`);
  out.bugie = {};
  for (const m of ['mente_importo', 'mente_impronta', 'mente_albero', 'mente_indirizzo', 'mente_meno']) {
    await modo(m);
    await A.run('swapCrea(7)');
    out.bugie[m] = [A.run('swapErrori[7] || ""'), lista(memA).length, A.run('swapPassi[7]')];
  }
  out.dopoBugie = cassetto().prossimo;
  await modo('normale');

  // --- lo swap vero
  await A.run('swapCrea(7)');
  const v1 = await visto();
  const l1 = lista(memA);
  out.creato = {quanti: l1.length, ordine: l1[0] && l1[0].ordine, indice: l1[0] && l1[0].indice,
                stato: l1[0] && l1[0].stato, ricevi: l1[0] && l1[0].ricevi,
                errore: A.run('swapErrori[7] || ""'), prossimo: cassetto().prossimo,
                referral: v1.creazione && v1.creazione.referralId,
                pairHash: v1.creazione && v1.creazione.pairHash,
                importo: v1.creazione && v1.creazione.invoiceAmount,
                chiaviCorpo: v1.creazione ? Object.keys(v1.creazione).sort() : []};
  const carta = A.run('pannelloSwapTelefono({id: 7})');
  html.push(carta);
  out.carta = carta.includes('Pronto e verificato');

  // --- gli stati e il ritiro cooperativo
  await A.run('swapGiro()');
  out.giroCreato = lista(memA)[0].stato;
  await stato(l1[0].id, 'transaction.mempool');
  await A.run('swapGiro()');
  const r1 = lista(memA)[0];
  const v2 = await visto();
  const t1 = v2.trasmesse[v2.trasmesse.length - 1] || {};
  const scriptDest = S.hex.encode(S.OutScript.encode(S.Address(S.NETWORK).decode(D.indirizzo)));
  out.coop = {txid: !!(r1.ritiro && r1.ritiro.txid), coop: r1.ritiro && r1.ritiro.cooperativo,
              errore: r1.errore || '', via: t1.via, uscite: t1.uscite && t1.uscite.length,
              sats: t1.uscite && t1.uscite[0].sats,
              dest: t1.uscite && t1.uscite[0].script === scriptDest,
              uguale: r1.ritiro && t1.txid === r1.ritiro.txid};
  await A.run('swapGiro()');
  out.fatto = [lista(memA)[0].stato, A.run('swapAperti().length')];
  html.push(A.run('pannelloSwapTelefono({id: 7})'));

  // --- SATS Routing che non firma: dallo script
  A.run(`elementi.swapIndirizzo_8 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(8)');
  out.secondaVolta = A.run('swapPassi[8]');
  await A.run('swapCrea(8)');
  const r8 = lista(memA).find(r => r.ordine === 8);
  await modo('non_firma');
  await stato(r8.id, 'transaction.confirmed');
  await A.run('swapGiro()');
  const r8b = lista(memA).find(r => r.ordine === 8);
  const v3 = await visto();
  const t3 = v3.trasmesse[v3.trasmesse.length - 1] || {};
  out.script = {txid: !!(r8b.ritiro && r8b.ritiro.txid), coop: r8b.ritiro && r8b.ritiro.cooperativo,
                via: t3.via, sats: t3.uscite && t3.uscite[0].sats, indice: r8.indice,
                errore: r8b.errore || ''};
  await modo('normale');

  // --- la ripresa: lo swap del 9 nasce, la pagina si chiude, i bitcoin
  // si bloccano, la pagina si riapre (stesso cassetto) e ritira da sola
  A.run(`elementi.swapIndirizzo_9 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(9)');
  await A.run('swapCrea(9)');
  const r9 = lista(memA).find(r => r.ordine === 9);
  await stato(r9.id, 'transaction.mempool');
  const B = pagina(memA);
  let r9b = null;
  for (let i = 0; i < 100; i++) {
    r9b = lista(memA).find(r => r.ordine === 9);
    if (r9b && r9b.ritiro && r9b.ritiro.txid) break;
    await sleep(100);
  }
  const v4 = await visto();
  out.ripresa = {ritirato: !!(r9b && r9b.ritiro && r9b.ritiro.txid),
                 trasmesse: v4.trasmesse.length, swapCartone: v4.swap};

  // --- il recupero su un telefono vuoto
  const parole = cassetto().parole;
  const memC = new Map();
  const C = pagina(memC);
  C.run(`elementi.swapRecupero = {value: 'non sono dodici parole'}; elementi.swapRecuperoNota = {textContent: ''}`);
  await C.run('swapRecupera()');
  out.recuperoNo = C.run('elementi.swapRecuperoNota.textContent');
  C.run(`elementi.swapRecupero = {value: ${JSON.stringify('  ' + parole.toUpperCase().split(' ').join('   ') + ' ')}}`);
  C.run(`elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}`);
  await C.run('swapRecupera()');
  const lc = lista(memC);
  const cc = JSON.parse(memC.get('barattolo_swap_222') || 'null');
  out.recupero = {nota: C.run('elementi.swapRecuperoNota.textContent'), quanti: lc.length,
                  prossimoA: cassetto().prossimo, prossimoC: cc && cc.prossimo,
                  parole: cc && cc.parole === parole, copiata: cc && cc.copiata,
                  indici: lc.map(r => r.indice).sort((a, b) => a - b),
                  stati: lc.map(r => r.stato).sort()};
  html.push(C.run('elementi.swapTelefono.innerHTML'));
  // ...e un telefono che ha GIA' altre parole con degli swap non le cambia
  const memD = new Map([['barattolo_swap_222', JSON.stringify({parole: 'abandon '.repeat(11) + 'about', prossimo: 1, copiata: true})],
                        ['barattolo_swap_lista_222', JSON.stringify([{id: 'x', ordine: 1, stato: 'invoice.settled'}])]]);
  const Dp = pagina(memD);
  Dp.run(`elementi.swapRecupero = {value: ${JSON.stringify(parole)}}; elementi.swapRecuperoNota = {textContent: ''}`);
  await Dp.run('swapRecupera()');
  out.recuperoAltre = [Dp.run('elementi.swapRecuperoNota.textContent'),
                       JSON.parse(memD.get('barattolo_swap_222')).parole.startsWith('abandon')];

  // --- la pagina Swap: le parole si mostrano solo a richiesta, col tocco
  A.run(`elementi.swapTelefono = {innerHTML: ''}; elementi.swapVuoto = {style: {}}`);
  A.run('renderSwapTelefono()');
  out.paroleNascoste = !A.run('elementi.swapTelefono.innerHTML').includes(parole.split(' ')[0] + '</li>');
  const tocco = A.run('ascoltatori[0][1]');
  tocco({target: {closest: () => ({dataset: {swap: 'mostra-parole'}})}});
  out.paroleMostrate = A.run('elementi.swapTelefono.innerHTML').includes(parole.split(' ')[0] + '</li>');
  html.push(A.run('elementi.swapTelefono.innerHTML'));
  tocco({target: {closest: () => ({dataset: {swap: 'scegli', ordine: '7', scelta: 'swap'}})}});
  tocco({target: {closest: () => null}});
  out.scelte = A.run('scelte');

  // --- un ritiro cooperativo rifiutato alla trasmissione: il giro dopo
  // si ritira dallo script, non si riprova all'infinito la stessa strada
  A.run(`elementi.swapIndirizzo_10 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(10)');
  await A.run('swapCrea(10)');
  const r10 = lista(memA).find(r => r.ordine === 10);
  await modo('rifiuta_cooperativo');
  await stato(r10.id, 'transaction.mempool');
  await A.run('swapGiro()');
  const r10a = lista(memA).find(r => r.ordine === 10);
  await A.run('swapGiro()');
  const r10b = lista(memA).find(r => r.ordine === 10);
  const v5 = await visto();
  out.rifiutoCoop = {primo: [!!r10a.ritiro, !!r10a.errore, !!r10a.coopRifiutato],
                     poi: [!!(r10b.ritiro && r10b.ritiro.txid), r10b.ritiro && r10b.ritiro.cooperativo,
                           (v5.trasmesse[v5.trasmesse.length - 1] || {}).via]};
  await modo('normale');

  // --- LA SENTINELLA: dove sono andate le chiamate, e cosa portavano
  const priv = [];
  for (let i = 0; i < 12; i++) {
    const k = S.HDKey.fromMasterSeed(S.mnemonicToSeedSync(parole)).derive(`m/44/0/0/0/${i}`);
    priv.push(S.hex.encode(k.privateKey));
  }
  /* i VALORI dei corpi (le chiavi del JSON e i percorsi sono fissi, e
     «swap», «claim», «index» sono anche parole BIP-39) */
  const valori = [];
  const raccogli = v => { if (v && typeof v === 'object') Object.values(v).forEach(raccogli);
                          else if (v !== undefined && v !== null) valori.push(String(v)); };
  for (const c of chiamate) { try { raccogli(JSON.parse(c.corpo || 'null')); } catch(e){ valori.push(c.corpo); } }
  const tutto = (valori.join('\n') + '\n' + chiamate.map(c => c.url).join('\n')).toLowerCase();
  const soloValori = valori.join('\n').toLowerCase();
  out.sentinella = {chiamate: chiamate.length,
                    fuori: chiamate.filter(c => !c.url.startsWith(BASE + '/v2/')).map(c => c.url),
                    api: chiamate.filter(c => c.url.includes('/api/')).length,
                    parole: tutto.includes(parole)
                      || parole.split(' ').some(p => new RegExp('\\b' + p + '\\b').test(soloValori)),
                    privata: priv.some(p => tutto.includes(p)),
                    xpub: chiamate.filter(c => c.corpo.includes('xpub')).map(c => c.url.replace(BASE, ''))};
  out.onclick = html.filter(h => /\son[a-z]+=/i.test(h)).length;
  out.dataSwap = html.join('').includes('data-swap="mostra-parole"');
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def telefono(base):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="swap_telefono_")
    try:
        p = os.path.join(cart, "banco.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(BANCO)
        open(d, "w", encoding="utf-8").write(json.dumps({
            "base": base, "indirizzo": INDIRIZZO,
            "bundle": os.path.join(banco.QUI, "vendor", "swap.bundle.js"),
            "telefono": [os.path.join(banco.QUI, "swap", "boltz.js"),
                         os.path.join(banco.QUI, "swap", "instradatore.js")],
            "bolt11": pezzi_pagina(),
            "leve": {"attivo": True, "api": base, "rete": "bitcoin",
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000},
            "preventivo": {"ok": True, "hash": "cartone-tariffa-16ott", "dovuto": 48_000,
                           "fattura": 48_000, "onchain": 47_388, "ricevi": 47_154,
                           "valido_s": 60, "righe": []}}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=300, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-1200:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def il_server(c, srv, base):
    print("\n[il server: dove parlare, la CSP, i file]")
    con = srv.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(999,'Admin','neg9990000',1,'')")
    con.commit()
    con.close()
    banco.come(999, admin=True)
    leve = (c.get("/api/me", headers=ADMIN).json() or {}).get("swap_leve") or {}
    prova("in /api/me dove parlare e su quale rete", (True, base, "bitcoin"),
          (leve.get("attivo"), leve.get("api"), leve.get("rete")))
    srv.SWAP_RETE = "regtest"
    banco.come(999, admin=True)
    prova("...la rete viene dal config (regtest sulla VM)", "regtest",
          ((c.get("/api/me", headers=ADMIN).json() or {}).get("swap_leve") or {}).get("rete"))
    srv.SWAP_RETE = "una rete inventata"
    prova("...una parola sconosciuta vale «bitcoin»", "bitcoin", srv.swap_rete())
    srv.SWAP_RETE = "bitcoin"
    csp = srv._csp_prova(True)
    connect = next(x for x in csp.split("; ") if x.startswith("connect-src"))
    prova("a swap acceso la CSP ammette la sola origine di SATS Routing",
          (True, 1), (connect.endswith(" " + base), connect.count("127.0.0.1")))
    srv.SWAP_ATTIVO = False
    prova("...a swap spento nessuna", False, base in srv._csp_prova(True))
    srv.SWAP_ATTIVO = True
    vero = srv.SWAP_API_BASE
    srv.SWAP_API_BASE = "https://api.satsrouting.exchange/qualcosa"
    connect = next(x for x in srv._csp_prova(True).split("; ")
                   if x.startswith("connect-src"))
    prova("...l'origine e' solo schema e casa, senza percorso",
          (True, False), (connect.endswith(" https://api.satsrouting.exchange"),
                          "qualcosa" in connect))
    srv.SWAP_API_BASE = "javascript:alert(1)"
    prova("...e una base che non e' http(s) non apre niente", "", srv.swap_origine_api())
    srv.SWAP_API_BASE = vero
    # (20 ott 2026, l'instradatore) i file del telefono stanno sotto
    # /swap/, una lista chiusa di nomi
    r1, r2 = c.get("/swap/instradatore.js"), c.get("/vendor/swap.js")
    prova("le due rotte dei file rispondono, javascript", (200, 200, True, True),
          (r1.status_code, r2.status_code,
           r1.headers.get("content-type", "").startswith("application/javascript"),
           "BarattoloSwap" in r2.text[:200]))
    prova("...anche il file del tipo «boltz», e un nome fuori lista no",
          (200, 404, 404),
          (c.get("/swap/boltz.js").status_code, c.get("/swap/server.js").status_code,
           c.get("/swap-telefono.js").status_code))


def il_telefono(base):
    r = telefono(base)
    if "ERRORE" in r:
        prova("il banco del telefono gira", "", r["ERRORE"])
        return
    print("\n[la prima volta: le 12 parole]")
    prova("un solo ascoltatore, delegato, sui click", ["click"], r["ascoltatori"])
    prova("nascono 12 parole valide, non ancora copiate, dal passo «parole»",
          {"quante": 12, "valide": True, "copiata": False, "prossimo": 0, "passo": "parole"},
          r["parole"])
    prova("...e il pannello le mostra tutte", 12, r["parolePannello"])
    prova("senza la spunta non si va avanti", ["parole", "Prima spunta «Le ho scritte su carta».", False],
          r["senzaSpunta"])
    prova("...con la spunta si passa all'indirizzo", ["indirizzo", True], r["conSpunta"])

    print("\n[l'indirizzo e le bugie]")
    prova("un indirizzo sbagliato: lo dice, nessuna chiamata, nessun indice speso, "
          "e il campo non si svuota",
          ["Questo non è un indirizzo valido per questa rete.", 0, 0, True], r["indirizzoNo"])
    rifiuto = "SATS Routing ha risposto con dati che non tornano: lo swap non parte, nessun sats si è mosso."
    for m in ("mente_importo", "mente_impronta", "mente_albero", "mente_indirizzo", "mente_meno"):
        prova(f"SATS Routing che mente ({m.split('_')[1]}): rifiutato, niente salvato",
              [rifiuto, 0, "indirizzo"], r.get("bugie", {}).get(m))
    prova("...e ogni tentativo ha speso il suo indice (mai un segreto riusato)", 5, r["dopoBugie"])

    print("\n[lo swap vero]")
    cr = r["creato"]
    prova("lo swap nasce col codice partner, l'impronta delle tariffe, la cifra della fattura",
          ("barattolo", "cartone-tariffa-16ott", 48_000), (cr.get("referral"), cr.get("pairHash"), cr.get("importo")))
    prova("...e la richiesta porta SOLO parti pubbliche",
          ["claimPublicKey", "from", "invoiceAmount", "pairHash", "preimageHash", "referralId", "to"],
          cr.get("chiaviCorpo"))
    prova("il telefono lo salva: ordine, indice 5, stato, quel che riceve",
          (1, 7, 5, "swap.created", 47_154, "", 6),
          (cr.get("quanti"), cr.get("ordine"), cr.get("indice"), cr.get("stato"), cr.get("ricevi"), cr.get("errore"), cr.get("prossimo")))
    prova("...e il pannello dell'incasso mostra lo swap", True, r["carta"])
    prova("la sorveglianza legge lo stato da SATS Routing", "swap.created", r["giroCreato"])

    print("\n[il ritiro]")
    co = r["coop"]
    prova("a bitcoin bloccati il telefono ritira da solo, cooperativo",
          (True, True, "", "cooperativo"), (co.get("txid"), co.get("coop"), co.get("errore"), co.get("via")))
    prova("...un'uscita sola, all'indirizzo di chi vende, coi sats del preventivo",
          (1, 47_154, True, True), (co.get("uscite"), co.get("sats"), co.get("dest"), co.get("uguale")))
    prova("...poi «fatto», e niente piu' da sorvegliare", ["invoice.settled", 0], r["fatto"])
    prova("la seconda volta le parole non si richiedono", "indirizzo", r["secondaVolta"])
    sc = r["script"]
    prova("SATS Routing che non firma: si ritira dallo script, e la firma regge",
          (True, False, "script", 47_154, ""), (sc.get("txid"), sc.get("coop"), sc.get("via"), sc.get("sats"), sc.get("errore")))

    print("\n[la ripresa e il recupero]")
    prova("uno swap lasciato a meta' si ritira alla riapertura della pagina",
          {"ritirato": True, "trasmesse": 3, "swapCartone": 8}, r["ripresa"])
    prova("12 parole storte: lo dice", "Queste non sono 12 parole valide.", r["recuperoNo"])
    rc = r["recupero"]
    prova("su un telefono vuoto le 12 parole ritrovano tutti gli swap",
          ("Recuperati 8 swap.", 8, list(range(8))), (rc.get("nota"), rc.get("quanti"), rc.get("indici")))
    prova("...il contatore riparte dopo il piu' alto, come sul telefono di prima",
          (8, 8, True, True), (rc.get("prossimoA"), rc.get("prossimoC"), rc.get("parole"), rc.get("copiata")))
    prova("un telefono con ALTRE parole e i suoi swap non le cambia",
          ["Su questo telefono ci sono già altre parole con degli swap: non le sostituisco.", True],
          r["recuperoAltre"])
    prova("le parole nella pagina Swap: nascoste, poi mostrate col tocco",
          (True, True), (r["paroleNascoste"], r["paroleMostrate"]))
    prova("l'ascoltatore delegato passa la scelta, e ignora il resto", [[7, "swap"]], r["scelte"])

    prova("un ritiro cooperativo rifiutato alla trasmissione: il giro dopo dallo script",
          {"primo": [False, True, True], "poi": [True, False, "script"]}, r.get("rifiutoCoop"))

    print("\n[la sentinella]")
    se = r["sentinella"]
    prova("ogni chiamata del telefono va a SATS Routing, nessuna al server",
          (True, [], 0), ((se.get("chiamate") or 0) > 10, se.get("fuori"), se.get("api")))
    prova("...in nessuna le 12 parole o una chiave privata", (False, False),
          (se.get("parole"), se.get("privata")))
    # (una volta sola: le parole storte e il telefono con altre parole
    # si fermano prima di chiedere)
    prova("...la xpub va solo al recupero", ["/v2/swap/restore"], se.get("xpub"))
    prova("nel markup del telefono nessun onclick: data-swap", (0, True),
          (r["onclick"], r["dataSwap"]))


def main():
    global PORTA
    print("=" * 58)
    print("  ₿ LO SWAP, TAPPA 3 — lo swap dal telefono")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    srv = banco.SRV
    _, PORTA = cartone_satsrouting.avvia(0)
    base = f"http://127.0.0.1:{PORTA}"
    srv.SWAP_ATTIVO = True
    srv.SWAP_SOLO_MODERATORI = True
    srv.SWAP_API_BASE = base
    srv.SWAP_REFERRAL_ID = "barattolo"
    srv.SWAP_RETE = "bitcoin"
    il_server(TestClient(srv.app), srv, base)
    il_telefono(base)
    prova("nessun pagamento e' uscito verso LNbits", [], banco.USCITE)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
