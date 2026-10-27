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
/* (24 ott 2026, tappa 4) il pagamento della fattura lo prova
   collaudo_swap_pagamento: qui il server non c'e', e il telefono non lo
   raggiunge (null = non si e' potuto chiedere) */
async function pagaSwapAlServer(){ return null; }
async function statoPagamentoSwap(){ return null; }
async function leggiPreventivoSwap(n, fornitore){
  return Object.assign(${JSON.stringify(D.preventivo)}, {fornitore: fornitore || 'satsrouting', fornitore_nome: 'SATS Routing'});
}
function pannelloPreventivoSwap(o, campo){ return '<div>preventivo</div>' + (campo || ''); }
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

  // --- (27 ott 2026, grafica-swap) «Conferma» senza indirizzo non va
  // avanti: lo dice, e le parole non nascono
  await A.run('swapAvanti(7)');
  out.senzaIndirizzo = [A.run('swapErrori[7] || ""'), cassetto(), A.run('swapPassi[7] || ""')];

  // --- la prima volta: le parole (l'indirizzo sta sopra «Conferma»)
  A.run(`elementi.swapIndirizzo_7 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(7)');
  const c0 = cassetto();
  out.parole = {quante: c0 && c0.parole.split(' ').length,
                valide: !!(c0 && S.validateMnemonic(c0.parole, S.wordlist)),
                copiata: c0 && c0.copiata, prossimo: c0 && c0.prossimo,
                passo: A.run('swapPassi[7]')};
  const p0 = A.run('pannelloSwapTelefono({id: 7})');
  html.push(p0);
  /* le parole sole: sopra ci sono le tre regole, anche loro in lista */
  const elenco0 = (p0.split('class="swap-parole"')[1] || '').split('</ol>')[0];
  out.parolePannello = (elenco0.match(/<li>/g) || []).length;
  out.paroleCalma = [p0.includes('Servono solo se qualcosa va storto'),
                     (p0.match(/class="swap-regole"/g) || []).length,
                     p0.includes('Senza queste parole nessuno può recuperarli, nemmeno noi.'),
                     p0.includes('>Continua<')];
  A.run("elementi.swapSpunta_7 = {checked: false}");
  A.run('swapParoleFatte(7)');
  out.senzaSpunta = [A.run('swapPassi[7]'), A.run('swapErrori[7]'), cassetto().copiata];
  /* «Continua» fa partire lo swap da solo: qui con un indirizzo storto,
     che lo ferma al preventivo col suo perche' (le bugie, sotto, vogliono
     lo swap ancora da fare) */
  A.run("swapIndirizziScritti[7] = 'bc1qnonvalido'");
  A.run("elementi.swapSpunta_7 = {checked: true}");
  await A.run('swapParoleFatte(7)');
  out.conSpunta = [A.run('swapPassi[7]'), cassetto().copiata, A.run('swapErrori[7] || ""')];
  html.push(A.run('pannelloSwapTelefono({id: 7})'));

  // --- un indirizzo sbagliato non chiede niente
  const primaCh = chiamate.length;
  A.run("elementi.swapIndirizzo_7 = {value: 'bc1qnonvalido'}");
  await A.run('swapAvanti(7)');
  out.indirizzoNo = [A.run('swapErrori[7]'), chiamate.length - primaCh, cassetto().prossimo,
                     /* ...e il campo, ridisegnato, ricorda quel che c'era scritto */
                     A.run('pannelloSwapTelefono({id: 7})').includes('value="bc1qnonvalido"')];

  // --- SATS Routing che mente
  A.run(`elementi.swapIndirizzo_7 = {value: '${D.indirizzo}'}`);
  out.bugie = {};
  for (const m of ['mente_importo', 'mente_impronta', 'mente_albero', 'mente_indirizzo', 'mente_meno']) {
    await modo(m);
    await A.run('swapAvanti(7)');
    out.bugie[m] = [A.run('swapErrori[7] || ""'), lista(memA).length, A.run('swapPassi[7]')];
  }
  out.dopoBugie = cassetto().prossimo;
  await modo('normale');

  // --- lo swap vero
  await A.run('swapAvanti(7)');
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
  out.carta = carta.includes('Barattolo sta pagando il cambio');

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
  /* la seconda volta «Conferma» fa nascere lo swap e basta: nessun passo
     dopo; e un secondo tocco (o un giro rientrato) non ne fa un altro */
  const quanti8 = lista(memA).length;
  await A.run('swapAvanti(8)');
  await A.run('swapCrea(8)');
  out.secondaVolta = [A.run('swapPassi[8] || ""'), !!A.run('swapDiOrdine(8)'),
                      lista(memA).length - quanti8];
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

  // --- (20 ott 2026, swap-lockup) TRE LOCKUP BUGIARDI: il telefono non
  // manda il segreto a nessuno — niente firma chiesta, niente trasmissione
  out.lockup = {};
  let ord = 11;
  for (const m of ['lockup_altro_script', 'lockup_meno', 'lockup_fantasma']) {
    A.run(`elementi.swapIndirizzo_${ord} = {value: '${D.indirizzo}'}`);
    await A.run(`swapAvanti(${ord})`);
    const rL = lista(memA).find(r => r.ordine === ord);
    await modo(m);
    const vPrima = await visto();
    await stato(rL.id, 'transaction.mempool');
    await A.run('swapGiro()');
    await A.run('swapGiro()');
    const rL2 = lista(memA).find(r => r.ordine === ord);
    const vDopo = await visto();
    out.lockup[m] = {ritirato: !!(rL2.ritiro && rL2.ritiro.txid), errore: rL2.errore || '',
                     firme: vDopo.firme.filter(id => id === rL.id).length,
                     tentate: vDopo.tentate - vPrima.tentate};
    await modo('normale');
    ord++;
  }

  // --- (20 ott 2026, swap-senza-api) L'API DEL FORNITORE SI SPEGNE.
  // Prima: subito dopo aver ricevuto il segreto (la richiesta di firma
  // cooperativa). Il telefono ritira lo stesso, dallo script, sulla rete.
  const spenta = async (ordine, prima) => {
    A.run(`elementi.swapIndirizzo_${ordine} = {value: '${D.indirizzo}'}`);
    await A.run(`swapAvanti(${ordine})`);
    const rS = lista(memA).find(r => r.ordine === ordine);
    const vPrima = await visto();
    await prima(rS);
    const giaCh = chiamate.length;
    await A.run('swapGiro()');
    const rS2 = lista(memA).find(r => r.ordine === ordine);
    const vDopo = await visto();
    const tS = vDopo.trasmesse.find(x => rS2.ritiro && x.txid === rS2.ritiro.txid) || {};
    const nuove = chiamate.slice(giaCh);
    await modo('normale');
    return {ritirato: !!(rS2.ritiro && rS2.ritiro.txid), coop: rS2.ritiro && rS2.ritiro.cooperativo,
            errore: rS2.errore || '', via: tS.via, strade: tS.strade,
            sats: tS.uscite && tS.uscite[0].sats,
            firme: vDopo.firme.filter(id => id === rS.id).length,
            trasmesseInPiu: vDopo.trasmesse.length - vPrima.trasmesse.length,
            perIndirizzo: nuove.filter(c => c.url.includes(`/esplora/address/${rS.lockupAddress}/`)).length,
            sullaRete: nuove.filter(c => c.metodo === 'POST' && c.url === BASE + '/esplora/tx').length};
  };
  out.spentaDopoSegreto = await spenta(14, async rS => {
    await modo('giu_dopo_firma');
    await stato(rS.id, 'transaction.mempool');
  });
  /* Poi: spenta PRIMA che i bitcoin si blocchino. Lo stato non arriva piu',
     ma la rete vede il lockup: il giro ritira lo stesso. Lo swap e' come
     uno recuperato (senza «ricevi»): la fee viene dalla rete. */
  out.spentaPrima = await spenta(15, async rS => {
    await modo('giu');
    await stato(rS.id, 'transaction.mempool');
    const l = lista(memA);
    delete l.find(r => r.id === rS.id).ricevi;
    memA.set('barattolo_swap_lista_222', JSON.stringify(l));
  });
  /* E a fornitore giu, uno swap senza lockup sulla rete resta fermo:
     niente ritiro tentato, niente firma chiesta */
  A.run(`elementi.swapIndirizzo_16 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(16)');
  await modo('giu');
  const gia16 = chiamate.length;
  await A.run('swapGiro()');
  const r16 = lista(memA).find(r => r.ordine === 16);
  out.spentaSenzaLockup = {ritirato: !!r16.ritiro, errore: r16.errore || '',
                           claim: chiamate.slice(gia16).filter(c => c.url.endsWith('/claim')).length};
  await modo('normale');

  // --- (20 ott 2026, swap-spesa) LA RISPOSTA DEL RITIRO PERSA, a fornitore
  // giu: la rete prende la trasmissione e il telefono non lo sa. Il giro
  // dopo riconosce il suo ritiro nella spesa del lockup: concluso.
  const frase = ordine => A.run(`frasestatoSwap(swapLista().find(r => r.ordine === ${ordine}))`);
  A.run(`elementi.swapIndirizzo_17 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(17)');
  const r17 = lista(memA).find(r => r.ordine === 17);
  await modo('giu_rete_muta');
  await stato(r17.id, 'transaction.mempool');
  await A.run('swapGiro()');
  const r17a = lista(memA).find(r => r.ordine === 17);
  const presa = (await visto()).trasmesse.find(x => x.swap === r17.id) || {};
  await A.run('swapGiro()');
  const r17b = lista(memA).find(r => r.ordine === 17);
  out.rispostaPersa = {
    primo: [!!r17a.ritiro, !!r17a.errore, (r17a.firmati || []).includes(presa.txid),
            (presa.strade || []).join(',')],
    poi: {concluso: !!(r17b.ritiro && r17b.ritiro.concluso),
          stessoTxid: !!r17b.ritiro && r17b.ritiro.txid === presa.txid,
          sats: r17b.ritiro && r17b.ritiro.sats, errore: r17b.errore || '',
          frase: frase(17).startsWith('Concluso: 47154 sats arrivati')},
    unaVolta: (await visto()).trasmesse.filter(x => x.swap === r17.id).length};
  /* ...e un telefono che quella transazione non l'ha firmata (le stesse
     parole altrove): la riconosce dall'indirizzo di chi vende */
  const l17 = lista(memA);
  const s17 = l17.find(r => r.ordine === 17);
  delete s17.ritiro;
  delete s17.firmati;
  memA.set('barattolo_swap_lista_222', JSON.stringify(l17));
  await A.run('swapGiro()');
  const r17c = lista(memA).find(r => r.ordine === 17);
  out.dallIndirizzo = {concluso: !!(r17c.ritiro && r17c.ritiro.concluso),
                       stessoTxid: !!r17c.ritiro && r17c.ritiro.txid === presa.txid,
                       sats: r17c.ritiro && r17c.ritiro.sats, errore: r17c.errore || ''};
  await modo('normale');
  /* LO SPESO DA UN ALTRO: errore chiaro, nessuna firma chiesta, niente
     trasmesso */
  A.run(`elementi.swapIndirizzo_18 = {value: '${D.indirizzo}'}`);
  await A.run('swapAvanti(18)');
  const r18 = lista(memA).find(r => r.ordine === 18);
  await modo('giu');
  await stato(r18.id, 'transaction.mempool');
  await fetchVero(`${BASE}/cartone/spendi_altro?id=${r18.id}`);
  const g18 = chiamate.length;
  await A.run('swapGiro()');
  const r18b = lista(memA).find(r => r.ordine === 18);
  out.spesoDaAltri = {ritirato: !!r18b.ritiro, errore: r18b.errore || '',
                      spesoDa: /^[0-9a-f]{64}$/.test(r18b.spesoDa || ''),
                      claim: chiamate.slice(g18).filter(c => c.url.endsWith('/claim')).length,
                      post: chiamate.slice(g18).filter(c => c.metodo === 'POST').length,
                      frase: frase(18),
                      riprovo: A.run('cartaSwap(swapLista().find(r => r.ordine === 18))').includes('riprovo da solo')};
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
                    /* (20 ott 2026) il fornitore, e il finto mempool da cui si
                       legge il lockup */
                    fuori: chiamate.filter(c => !c.url.startsWith(BASE + '/v2/')
                                             && !c.url.startsWith(BASE + '/esplora/')).map(c => c.url),
                    mempool: chiamate.filter(c => c.url.startsWith(BASE + '/esplora/tx/')).length,
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
                     "referral": "barattolo", "minimo": 25_000, "massimo": 50_000,
                     # (20 ott 2026) il finto mempool del cartone
                     "mempool": base + "/esplora"},
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
    # (20 ott 2026, swap-lockup) e l'origine del mempool da cui il telefono
    # legge il lockup: di serie mempool.space, la stessa dell'on-chain
    prova("a swap acceso la CSP ammette l'origine di SATS Routing e quella del mempool",
          (True, 1, True), (connect.endswith(" " + base + " https://mempool.space"),
                            connect.count("127.0.0.1"), "mempool.space/" not in connect))
    srv.SWAP_ATTIVO = False
    prova("...a swap spento nessuna", False, base in srv._csp_prova(True))
    srv.SWAP_ATTIVO = True
    vero = srv.SWAP_API_BASE
    srv.SWAP_API_BASE = "https://api.satsrouting.exchange/qualcosa"
    connect = next(x for x in srv._csp_prova(True).split("; ")
                   if x.startswith("connect-src"))
    prova("...l'origine e' solo schema e casa, senza percorso",
          (True, False), (connect.endswith(" https://api.satsrouting.exchange https://mempool.space"),
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
    # (27 ott 2026, grafica-swap) tre ascoltatori: i click, l'input del campo
    # dell'indirizzo, la fotocamera spenta ad app in secondo piano
    prova("un ascoltatore delegato sui click, piu' l'input e la visibilita'",
          ["click", "input", "visibilitychange"], r["ascoltatori"])
    prova("«Conferma» senza indirizzo: lo dice, e le parole non nascono",
          ["Prima metti il tuo indirizzo bitcoin: tocca «Incolla».", None, ""],
          r["senzaIndirizzo"])
    prova("nascono 12 parole valide, non ancora copiate, dal passo «parole»",
          {"quante": 12, "valide": True, "copiata": False, "prossimo": 0, "passo": "parole"},
          r["parole"])
    prova("...e il pannello le mostra tutte", 12, r["parolePannello"])
    prova("...spiegate con calma: a cosa servono, le tre regole, nessuno senza, "
          "e «Continua»", [True, 1, True, True], r["paroleCalma"])
    prova("senza la spunta non si va avanti", ["parole", "Prima spunta «Le ho scritte su carta».", False],
          r["senzaSpunta"])
    prova("...con la spunta lo swap parte da solo: qui l'indirizzo storto lo "
          "ferma al preventivo, col perche'",
          ["preventivo", True, "Questo non è un indirizzo bitcoin valido."], r["conSpunta"])

    print("\n[l'indirizzo e le bugie]")
    prova("un indirizzo sbagliato: lo dice, nessuna chiamata, nessun indice speso, "
          "e il campo non si svuota",
          ["Questo non è un indirizzo bitcoin valido.", 0, 0, True], r["indirizzoNo"])
    rifiuto = "SATS Routing ha risposto con dati che non tornano: non parte niente, nessun sats si è mosso."
    for m in ("mente_importo", "mente_impronta", "mente_albero", "mente_indirizzo", "mente_meno"):
        prova(f"SATS Routing che mente ({m.split('_')[1]}): rifiutato, niente salvato",
              [rifiuto, 0, "preventivo"], r.get("bugie", {}).get(m))
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
    prova("la seconda volta «Conferma» fa nascere lo swap, senza altri passi; "
          "un secondo tocco non ne fa un altro", ["", True, 0], r["secondaVolta"])
    sc = r["script"]
    prova("SATS Routing che non firma: si ritira dallo script, e la firma regge",
          (True, False, "script", 47_154, ""), (sc.get("txid"), sc.get("coop"), sc.get("via"), sc.get("sats"), sc.get("errore")))

    print("\n[la ripresa e il recupero]")
    prova("uno swap lasciato a meta' si ritira alla riapertura della pagina",
          {"ritirato": True, "trasmesse": 3, "swapCartone": 8}, r["ripresa"])
    prova("12 parole storte: lo dice", "Queste non sono 12 parole valide.", r["recuperoNo"])
    rc = r["recupero"]
    prova("su un telefono vuoto le 12 parole ritrovano tutti gli swap",
          ("Recuperati 8 incassi.", 8, list(range(8))), (rc.get("nota"), rc.get("quanti"), rc.get("indici")))
    prova("...il contatore riparte dopo il piu' alto, come sul telefono di prima",
          (8, 8, True, True), (rc.get("prossimoA"), rc.get("prossimoC"), rc.get("parole"), rc.get("copiata")))
    prova("un telefono con ALTRE parole e i suoi swap non le cambia",
          ["Su questo telefono ci sono già altre parole in uso: non le sostituisco.", True],
          r["recuperoAltre"])
    prova("le parole nella pagina Swap: nascoste, poi mostrate col tocco",
          (True, True), (r["paroleNascoste"], r["paroleMostrate"]))
    prova("l'ascoltatore delegato passa la scelta, e ignora il resto", [[7, "swap"]], r["scelte"])

    prova("un ritiro cooperativo rifiutato alla trasmissione: il giro dopo dallo script",
          {"primo": [False, True, True], "poi": [True, False, "script"]}, r.get("rifiutoCoop"))

    print("\n[i lockup bugiardi: nessun segreto esce]")
    for m, motivo in (("lockup_altro_script", "nel lockup non c'e' il nostro swap"),
                      ("lockup_meno", "il lockup porta meno di quanto promesso"),
                      ("lockup_fantasma", "il lockup non si vede sulla rete")):
        prova(f"{m}: niente ritiro, il perche', nessuna firma chiesta, nessuna trasmissione",
              {"ritirato": False, "errore": motivo, "firme": 0, "tentate": 0},
              (r.get("lockup") or {}).get(m))

    print("\n[l'API del fornitore si spegne: il ritiro regge]")
    prova("spenta dopo il segreto: si ritira lo stesso, dallo script, sulla rete",
          {"ritirato": True, "coop": False, "errore": "", "via": "script",
           "strade": ["rete"], "sats": 47_154, "firme": 1, "trasmesseInPiu": 1,
           "perIndirizzo": 1, "sullaRete": 1},
          r.get("spentaDopoSegreto"))
    prova("spenta prima del lockup: la rete lo vede, il giro ritira, la fee dalla rete",
          {"ritirato": True, "coop": False, "errore": "", "via": "script",
           "strade": ["rete"], "sats": 47_388 - 2 * 160, "firme": 0, "trasmesseInPiu": 1,
           "perIndirizzo": 2, "sullaRete": 1},
          r.get("spentaPrima"))
    prova("...e senza lockup sulla rete niente ritiro tentato, niente firma chiesta",
          {"ritirato": False, "errore": "", "claim": 0}, r.get("spentaSenzaLockup"))

    print("\n[la spesa del lockup: chi l'ha speso]")
    prova("la risposta del ritiro si perde a fornitore giu: errore, ma la transazione e' ricordata",
          [False, True, True, "rete"], (r.get("rispostaPersa") or {}).get("primo"))
    prova("...il giro dopo riconosce il suo ritiro nella spesa del lockup: concluso, coi sats arrivati",
          {"concluso": True, "stessoTxid": True, "sats": 47_154, "errore": "", "frase": True},
          (r.get("rispostaPersa") or {}).get("poi"))
    prova("...e il ritiro sulla rete c'e' una volta sola", 1,
          (r.get("rispostaPersa") or {}).get("unaVolta"))
    prova("un telefono che non l'ha firmato lo riconosce dall'indirizzo di chi vende",
          {"concluso": True, "stessoTxid": True, "sats": 47_154, "errore": ""},
          r.get("dallIndirizzo"))
    prova("lockup speso da un altro: errore chiaro, nessuna firma, niente trasmesso",
          {"ritirato": False, "errore": "il lockup l'ha speso un'altra transazione",
           "spesoDa": True, "claim": 0, "post": 0,
           "frase": "Quei bitcoin li ha spesi un'altra transazione, non il tuo invio: scrivi a SATS Routing.",
           "riprovo": False},
          r.get("spesoDaAltri"))

    print("\n[la sentinella]")
    se = r["sentinella"]
    prova("il lockup si legge dal mempool, non solo dal fornitore", True,
          (se.get("mempool") or 0) >= 4)
    prova("ogni chiamata del telefono va a SATS Routing o al mempool, nessuna al server",
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
