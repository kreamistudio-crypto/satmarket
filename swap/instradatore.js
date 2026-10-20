/* ═══ L'INSTRADATORE DELLO SWAP (20 ott 2026, cantiere swap-instradatore;
   nato dal file della tappa 3, cantiere swap-telefono)
   Chi vende sceglie solo COSA vuole — oggi ricevere bitcoin on-chain
   (`ln-btc`); domani anche USDT, o pagare con USDT — e non CHI lo fa: il
   fornitore lo sceglie questo file. Se piu' fornitori fanno la stessa
   strada vince il preventivo migliore (chi fa ricevere di piu'); se quello
   scelto risponde con dati che non tornano, si ripiega sul secondo
   MOSTRANDO il suo preventivo e chiedendo una nuova conferma; se non ce
   n'e' un altro ci si ferma, col perche' (decisione di Andrea).

   I FORNITORI vengono dal server (`swapLeve.fornitori`: id, nome, tipo,
   api, codice partner, rete) e il loro codice dal file del loro TIPO
   (`swap/boltz.js`: SATS Routing e chi parla lo stesso protocollo), che
   registra una fabbrica in `window.SWAP_TIPI`. L'interfaccia che ogni
   fornitore offre e' scritta in testa a `swap/boltz.js`. Un server di
   ieri senza `fornitori` vale «SATS Routing, coi campi di sempre».

   LE CHIAVI SONO DEL TELEFONO, per fornitore: dodici parole per ognuno,
   nel localStorage sotto il conto (`barattolo_swap_<tg_id>` per SATS
   Routing, come dalla tappa 3; `barattolo_swap_<fornitore>_<tg_id>` per
   gli altri). Gli swap stanno in una lista sola, e ognuno porta il suo
   fornitore. Al server di Barattolo arriva solo la richiesta del
   preventivo (`leggiPreventivoSwap` della pagina): niente chiavi.

   Niente script inline e niente `onclick=` (arriva la fase 2 della CSP):
   i bottoni portano `data-swap="…"` e li ascolta UN solo ascoltatore
   delegato, in fondo, con la sua lista chiusa.

   IN QUESTA TAPPA BARATTOLO NON PAGA LA FATTURA DELLO SWAP (tappa 4).

   Usa dalla pagina: swapLeve, swapAcceso, myTgId, el, esc, fmt, haptic,
   toast, currentOrder, preventiviSwap, scegliIncassoSwap,
   leggiPreventivoSwap, pannelloPreventivoSwap, ridisegnaIncassoSwap,
   linguaSwap. */

/* ─── 1. LE STRADE E I FORNITORI ────────────────────────────────────── */
/* la sola strada di oggi: i sats dell'incasso, ricevuti in bitcoin on-chain */
const SWAP_STRADA = 'ln-btc';
const SWAP_FASI_FINALI = new Set(['fatto', 'scaduto', 'fallito', 'ripreso']);
const SWAP_FASI_RITIRO = new Set(['bloccato', 'confermato']);
let swapFornitoriCopia = null, swapFornitoriDa = null;
function swapFornitori(){
  if (swapFornitoriCopia && swapFornitoriDa === swapLeve) return swapFornitoriCopia;
  const l = swapLeve || {};
  const voci = Array.isArray(l.fornitori) && l.fornitori.length ? l.fornitori
    : [{id: 'satsrouting', nome: 'SATS Routing', tipo: 'boltz',
        api: l.api, referral: l.referral, rete: l.rete, mempool: l.mempool}];
  const tipi = window.SWAP_TIPI || {};
  swapFornitoriCopia = voci
    .filter(v => v && v.id && Object.prototype.hasOwnProperty.call(tipi, v.tipo))
    .map(v => tipi[v.tipo](v));
  swapFornitoriDa = swapLeve;
  return swapFornitoriCopia;
}
function swapFornitore(id){
  const l = swapFornitori();
  return l.find(f => f.id === (id || 'satsrouting')) || null;
}
function swapNomeFornitore(id){ const f = swapFornitore(id); return f ? f.nome : String(id || ''); }

/* ─── 2. IL CASSETTO, sotto il CONTO e per FORNITORE ──────────────────
   Il cassetto delle parole: {parole, prossimo, copiata}. `prossimo` e'
   l'indice della prossima chiave: si salva PRIMA di chiedere lo swap,
   perche' un indice riusato vorrebbe dire un segreto riusato. */
function swapCasaParole(fid){
  return (!fid || fid === 'satsrouting') ? `barattolo_swap_${myTgId || 'x'}`
    : `barattolo_swap_${fid}_${myTgId || 'x'}`;
}
function swapCasaLista(){ return `barattolo_swap_lista_${myTgId || 'x'}`; }
function swapLeggi(k, vuoto){
  try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? vuoto : v; }
  catch(e){ return vuoto; }
}
function swapScrivi(k, v){
  try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch(e){ return false; }
}
function swapCassetto(fid){ return swapLeggi(swapCasaParole(fid), null); }
function swapLista(){ const l = swapLeggi(swapCasaLista(), []); return Array.isArray(l) ? l : []; }
function swapDiChi(rec){ return (rec && rec.fornitore) || 'satsrouting'; }
function swapSalvaRecord(rec){
  const l = swapLista().filter(x => x.id !== rec.id);
  l.push(rec);
  return swapScrivi(swapCasaLista(), l);
}
function swapDiOrdine(ordine){
  const n = Number(ordine);
  return swapLista().filter(x => Number(x.ordine) === n).pop() || null;
}
function swapFase(rec){
  const f = swapFornitore(swapDiChi(rec));
  return f ? f.fase(rec.stato) : 'ignoto';
}

/* ─── 3. I TESTI, in italiano e in inglese ───────────────────────────── */
const SWAP_TESTI_T3 = {
  it: {
    paroleTit: 'Le tue 12 parole',
    paroleDi: n => `Le tue 12 parole per ${n}`,
    paroleSpiega: 'Sono la chiave dei tuoi swap e stanno solo su questo telefono. Scrivile su carta: servono a recuperare uno swap se cambi telefono.',
    paroleSpunta: 'Le ho scritte su carta',
    paroleFatto: 'Ho salvato le parole',
    paroleSpuntaPrima: 'Prima spunta «Le ho scritte su carta».',
    indirizzoTit: 'Dove ricevi i bitcoin',
    indirizzoSpiega: 'Un indirizzo bitcoin del tuo wallet.',
    indirizzoNo: 'Questo non è un indirizzo valido per questa rete.',
    crea: 'Crea lo swap',
    creo: n => `Creo lo swap e controllo la risposta di ${n}…`,
    nienteCasa: 'Questo telefono non riesce a conservare le chiavi: lo swap non si può fare da qui.',
    rifiuto: n => `${n} ha risposto con dati che non tornano: lo swap non parte, nessun sats si è mosso.`,
    nonRisponde: n => `${n} ora non risponde: riprova, o incassa in Lightning.`,
    tuoSwap: 'Il tuo swap',
    eseguitoDa: n => `Eseguito da ${n}`,
    ricevi: n => `Ricevi circa ${n} sats a`,
    riceviQui: n => `Ricevi circa ${n} sats a questo indirizzo.`,
    fasi: {
      creato: () => 'Pronto e verificato. Il pagamento da Barattolo arriva con la prossima versione: per ora nessun sats si muove.',
      bloccato: n => `${n} ha bloccato i bitcoin: ritiro in corso.`,
      confermato: () => 'Bitcoin bloccati e confermati: ritiro in corso.',
      fatto: () => 'Fatto: i bitcoin sono tuoi.',
      scaduto: () => 'Scaduto: nessun sats si è mosso, l\'incasso torna disponibile.',
      fallito: () => 'Non riuscito: l\'incasso torna disponibile.',
      ripreso: n => `${n} si è ripreso i bitcoin: l'incasso torna disponibile.`},
    statoIgnoto: 'In corso.',
    ritirato: id => `Ritirato: transazione ${id}.`,
    ritiroErrore: 'Il ritiro non è ancora riuscito: riprovo da solo.',
    lista: 'I tuoi swap',
    ordine: n => `Ordine #${n}`,
    recuperato: 'Recuperato',
    mostra: 'Mostra le 12 parole',
    nascondi: 'Nascondi',
    nessunaParola: 'Non hai ancora le parole: nascono col primo swap.',
    recuperaTit: 'Recupera da 12 parole',
    recuperaSpiega: 'Se avevi già degli swap su un altro telefono, incolla qui le tue 12 parole.',
    recupera: 'Recupera',
    recuperaDa: n => `Recupera da ${n}`,
    recuperaNo: 'Queste non sono 12 parole valide.',
    recuperaAltre: 'Su questo telefono ci sono già altre parole con degli swap: non le sostituisco.',
    recuperaFatto: n => n === 0 ? 'Nessuno swap legato a queste parole.'
      : n === 1 ? 'Recuperato 1 swap.' : `Recuperati ${n} swap.`,
    ritiraA: 'Ritira a questo indirizzo'},
  en: {
    paroleTit: 'Your 12 words',
    paroleDi: n => `Your 12 words for ${n}`,
    paroleSpiega: 'They are the key to your swaps and live only on this phone. Write them on paper: they recover a swap if you change phone.',
    paroleSpunta: 'I wrote them on paper',
    paroleFatto: 'I saved the words',
    paroleSpuntaPrima: 'First tick «I wrote them on paper».',
    indirizzoTit: 'Where you receive the bitcoin',
    indirizzoSpiega: 'A bitcoin address of your wallet.',
    indirizzoNo: 'This is not a valid address for this network.',
    crea: 'Create the swap',
    creo: n => `Creating the swap and checking the ${n} answer…`,
    nienteCasa: 'This phone cannot keep the keys: the swap cannot be done from here.',
    rifiuto: n => `${n} answered with data that does not add up: the swap does not start, no sats moved.`,
    nonRisponde: n => `${n} is not responding: try again, or receive via Lightning.`,
    tuoSwap: 'Your swap',
    eseguitoDa: n => `Run by ${n}`,
    ricevi: n => `You receive about ${n} sats at`,
    riceviQui: n => `You receive about ${n} sats at this address.`,
    fasi: {
      creato: () => 'Ready and verified. The payment from Barattolo comes with the next version: no sats move for now.',
      bloccato: n => `${n} locked the bitcoin: claiming.`,
      confermato: () => 'Bitcoin locked and confirmed: claiming.',
      fatto: () => 'Done: the bitcoin are yours.',
      scaduto: () => 'Expired: no sats moved, the payout is available again.',
      fallito: () => 'Failed: the payout is available again.',
      ripreso: n => `${n} took the bitcoin back: the payout is available again.`},
    statoIgnoto: 'In progress.',
    ritirato: id => `Claimed: transaction ${id}.`,
    ritiroErrore: 'The claim did not go through yet: retrying by itself.',
    lista: 'Your swaps',
    ordine: n => `Order #${n}`,
    recuperato: 'Recovered',
    mostra: 'Show the 12 words',
    nascondi: 'Hide',
    nessunaParola: 'You have no words yet: they are born with the first swap.',
    recuperaTit: 'Recover from 12 words',
    recuperaSpiega: 'If you had swaps on another phone, paste your 12 words here.',
    recupera: 'Recover',
    recuperaDa: n => `Recover from ${n}`,
    recuperaNo: 'These are not 12 valid words.',
    recuperaAltre: 'This phone already has other words with swaps: I will not replace them.',
    recuperaFatto: n => n === 0 ? 'No swaps tied to these words.'
      : n === 1 ? 'Recovered 1 swap.' : `Recovered ${n} swaps.`,
    ritiraA: 'Claim to this address'}};
function t3(){ return SWAP_TESTI_T3[linguaSwap()]; }
function swapCorto(s, n){ s = String(s || ''); return s.length > 2 * n + 1 ? `${s.slice(0, n)}…${s.slice(-n)}` : s; }
function swapPiuFornitori(){ return swapFornitori().length > 1; }

/* ─── 4. IL PREVENTIVO INSTRADATO ───────────────────────────────────────
   Il conto lo fa il server, per fornitore (`leggiPreventivoSwap` della
   pagina); qui si sceglie. Fra i preventivi buoni vince chi fa RICEVERE
   di piu'; a pari, il primo dell'elenco del server. Nessuno buono: si
   mostra il rifiuto del primo (il perche' piu' utile: sotto il minimo,
   sopra il tetto, non risponde). I fornitori che su quest'ordine hanno
   risposto con dati che non tornano restano fuori (`swapEsclusi`). */
const swapEsclusi = {};    // ordine -> Set di id
function swapCandidati(n){
  const fuori = swapEsclusi[n] || new Set();
  return swapFornitori().filter(f => f.strade.includes(SWAP_STRADA) && !fuori.has(f.id));
}
function swapMigliore(letti){
  const buoni = letti.filter(d => d && d.ok && Number(d.ricevi) > 0);
  if (buoni.length) return buoni.reduce((a, b) => Number(b.ricevi) > Number(a.ricevi) ? b : a);
  return letti.find(d => d) || {ok: false, motivo: 'non_risponde'};
}
async function swapInstradaPreventivo(n, ricontrolla){
  const prima = preventiviSwap[n];
  preventiviSwap[n] = Object.assign({}, prima, {stato: 'carico'});
  ridisegnaIncassoSwap();
  let d;
  const scelto = prima && prima.dati && prima.dati.ok && prima.dati.fornitore;
  if (ricontrolla && scelto) {
    /* la conferma ricontrolla le tariffe del fornitore SCELTO, con
       l'impronta di quelle mostrate */
    d = await leggiPreventivoSwap(n, scelto, prima.dati.hash);
  } else {
    const candidati = swapCandidati(n);
    const letti = await Promise.all(candidati.map(f => leggiPreventivoSwap(n, f.id, '')));
    d = swapMigliore(letti);
  }
  const nota = ricontrolla && d.cambiata ? 'cambiata' : '';
  preventiviSwap[n] = {stato: 'pronto', dati: d, quando: Date.now(), nota: nota};
  if (currentOrder && Number(currentOrder.id) === Number(n)) ridisegnaIncassoSwap();
}

/* ─── 5. IL PANNELLO DELL'INCASSO, ramo swap ────────────────────────────
   I passi di un ordine: 'preventivo' (la tappa 2) -> 'parole' (la prima
   volta con QUEL fornitore) -> 'indirizzo' -> 'creo'. Poi c'e' lo swap,
   e il pannello mostra il suo stato. */
const swapPassi = {};      // ordine -> passo
const swapErrori = {};     // ordine -> frase
/* l'indirizzo scritto, per ordine: un avviso ridisegna il pannello, e un
   bc1 lungo non si fa riscrivere da capo (preso dal giro dal vivo) */
const swapIndirizziScritti = {};
const swapParoleViste = {};   // fornitore -> true quando si vedono
function swapScelto(n){
  const d = ((preventiviSwap[n] || {}).dati) || {};
  return d.fornitore || 'satsrouting';
}
function pannelloSwapTelefono(o){
  const n = Number(o.id), t = t3();
  const rec = swapDiOrdine(n);
  if (rec) return cartaSwap(rec);
  const passo = swapPassi[n] || 'preventivo';
  const fid = swapScelto(n), nome = swapNomeFornitore(fid);
  const errore = swapErrori[n]
    ? `<div class="swap-rifiuto" role="status">${esc(swapErrori[n])}</div>` : '';
  if (passo === 'parole') {
    const c = swapCassetto(fid);
    const parole = c && c.parole ? String(c.parole).split(' ') : [];
    return `<div class="swap-prev">
      <h4>🔑 ${esc(swapPiuFornitori() ? t.paroleDi(nome) : t.paroleTit)}</h4>
      <div class="hint">${esc(t.paroleSpiega)}</div>
      ${errore}
      <ol class="swap-parole">${parole.map(p => `<li>${esc(p)}</li>`).join('')}</ol>
      <label class="swap-spunta"><input type="checkbox" id="swapSpunta_${n}"> ${esc(t.paroleSpunta)}</label>
      <button class="btn orange" type="button" data-swap="parole-fatte" data-ordine="${n}">${esc(t.paroleFatto)}</button>
    </div>`;
  }
  if (passo === 'indirizzo' || passo === 'creo') {
    const p = (preventiviSwap[n] || {}).dati || {};
    return `<div class="swap-prev">
      <h4>₿ ${esc(t.indirizzoTit)}</h4>
      <div class="hint">${esc(t.indirizzoSpiega)}</div>
      ${errore}
      <input class="swap-indirizzo" id="swapIndirizzo_${n}" type="text" autocomplete="off"
        spellcheck="false" placeholder="bc1…" inputmode="text" value="${esc(swapIndirizziScritti[n] || '')}">
      ${p.ricevi ? `<div class="hint">${esc(t.riceviQui(fmt(p.ricevi)))}</div>` : ''}
      <button class="btn orange" type="button" data-swap="crea" data-ordine="${n}"${passo === 'creo' ? ' disabled' : ''}>${esc(passo === 'creo' ? t.creo(nome) : t.crea)}</button>
      <div class="swap-da">${esc(t.eseguitoDa(nome))}</div>
    </div>`;
  }
  return pannelloPreventivoSwap(o);
}
function frasestatoSwap(rec){
  const t = t3();
  if (rec.ritiro && rec.ritiro.txid && swapFase(rec) !== 'fatto')
    return t.ritirato(swapCorto(rec.ritiro.txid, 8));
  const f = t.fasi[swapFase(rec)];
  return f ? f(swapNomeFornitore(swapDiChi(rec))) : t.statoIgnoto;
}
function cartaSwap(rec){
  const t = t3();
  return `<div class="swap-prev swap-carta" data-swap-id="${esc(rec.id)}">
    <h4>₿ ${esc(t.tuoSwap)}</h4>
    <div class="swap-stato">${esc(frasestatoSwap(rec))}</div>
    ${rec.ricevi && rec.indirizzo ? `<div class="hint">${esc(t.ricevi(fmt(rec.ricevi)))} <span class="mono">${esc(swapCorto(rec.indirizzo, 8))}</span></div>` : ''}
    ${rec.errore ? `<div class="hint">${esc(t.ritiroErrore)}</div>` : ''}
    <div class="swap-da">${esc(t.eseguitoDa(swapNomeFornitore(swapDiChi(rec))))}</div>
  </div>`;
}

/* ─── 6. LE AZIONI ──────────────────────────────────────────────────── */
/* «Conferma lo swap» del preventivo: si ricontrollano le tariffe del
   fornitore scelto con l'impronta di quelle mostrate (la tappa 2); se
   reggono, la prima volta con quel fornitore le parole, poi l'indirizzo */
async function swapAvanti(n){
  haptic();
  delete swapErrori[n];
  await swapInstradaPreventivo(n, true);
  const p = preventiviSwap[n] || {};
  if (!p.dati || !p.dati.ok || p.nota === 'cambiata') return;
  const fid = swapScelto(n), f = swapFornitore(fid);
  if (!f) return;
  const c = swapCassetto(fid);
  if (!c || !c.parole || !c.copiata) {
    if (!c || !c.parole) {
      let parole;
      try { parole = await f.nuoveParole(); }
      catch(e){ swapErrori[n] = t3().nonRisponde(f.nome); return ridisegnaIncassoSwap(); }
      const nuovo = {parole: parole, prossimo: 0, copiata: false};
      if (!swapScrivi(swapCasaParole(fid), nuovo)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
    }
    swapPassi[n] = 'parole';
  } else {
    swapPassi[n] = 'indirizzo';
  }
  ridisegnaIncassoSwap();
}
function swapParoleFatte(n){
  haptic();
  const spunta = el(`swapSpunta_${n}`);
  if (!spunta || !spunta.checked) { swapErrori[n] = t3().paroleSpuntaPrima; return ridisegnaIncassoSwap(); }
  const fid = swapScelto(n);
  const c = swapCassetto(fid);
  if (!c) return;
  c.copiata = true;
  if (!swapScrivi(swapCasaParole(fid), c)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
  delete swapErrori[n];
  swapPassi[n] = 'indirizzo';
  ridisegnaIncassoSwap();
}
async function swapCrea(n){
  haptic();
  const t = t3();
  const indirizzo = String((el(`swapIndirizzo_${n}`) || {}).value || '').trim();
  swapIndirizziScritti[n] = indirizzo;
  const p = ((preventiviSwap[n] || {}).dati) || {};
  const fid = swapScelto(n), f = swapFornitore(fid);
  if (!f) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  let valido;
  try { valido = await f.indirizzoValido(indirizzo); }
  catch(e){ swapErrori[n] = t.nonRisponde(f.nome); return ridisegnaIncassoSwap(); }
  if (!valido) { swapErrori[n] = t.indirizzoNo; return ridisegnaIncassoSwap(); }
  if (!p.ok || !p.hash) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  const c = swapCassetto(fid);
  if (!c || !c.parole || !c.copiata) { swapPassi[n] = 'parole'; return ridisegnaIncassoSwap(); }
  /* L'INDICE SI PRENOTA PRIMA DI CHIEDERE: se il telefono si spegne a meta',
     al giro dopo si usa il successivo, mai lo stesso */
  const indice = Number(c.prossimo) || 0;
  c.prossimo = indice + 1;
  if (!swapScrivi(swapCasaParole(fid), c)) { swapErrori[n] = t.nienteCasa; return ridisegnaIncassoSwap(); }
  swapPassi[n] = 'creo';
  delete swapErrori[n];
  ridisegnaIncassoSwap();
  let nuovo;
  try { nuovo = await f.crea({parole: c.parole, indice: indice, preventivo: p, indirizzo: indirizzo}); }
  catch(e){
    if (e && e.tipo === 'mente') return swapRipiega(n, f);
    swapPassi[n] = 'indirizzo';
    swapErrori[n] = t.nonRisponde(f.nome);
    return ridisegnaIncassoSwap();
  }
  swapSalvaRecord(Object.assign(nuovo, {fornitore: fid, ordine: n, indice: indice,
    indirizzo: indirizzo, creato: Date.now()}));
  delete swapPassi[n];
  ridisegnaIncassoSwap();
  swapSorveglia();
}
/* IL RIPIEGO: il fornitore ha risposto con dati che non tornano. Se
   un altro fa la stessa strada, si mostra il SUO preventivo e si chiede
   una nuova conferma (il prezzo e' diverso: mai cambiato di nascosto);
   se non ce n'e' un altro, ci si ferma col perche'. */
async function swapRipiega(n, f){
  const t = t3();
  const fuori = swapEsclusi[n] || (swapEsclusi[n] = new Set());
  fuori.add(f.id);
  if (!swapCandidati(n).length) {
    /* nessun altro: ci si ferma, e il fornitore resta riprovabile (un
       secondo tentativo usa comunque una chiave nuova) */
    fuori.delete(f.id);
    swapPassi[n] = 'indirizzo';
    swapErrori[n] = t.rifiuto(f.nome);
    return ridisegnaIncassoSwap();
  }
  swapPassi[n] = 'preventivo';
  await swapInstradaPreventivo(n, false);
  const p = preventiviSwap[n];
  p.nota = 'ripiego';
  p.ripiegoDa = f.nome;
  if (!p.dati || !p.dati.ok) {
    swapPassi[n] = 'indirizzo';
    swapErrori[n] = t.rifiuto(f.nome);
  }
  ridisegnaIncassoSwap();
}

/* ─── 7. LA SORVEGLIANZA E IL RITIRO ──────────────────────────────────
   Ogni 5 secondi, finche' c'e' uno swap non finito, si chiede al suo
   fornitore a che punto e'; quando i bitcoin sono bloccati si ritira.
   All'apertura dell'app si riprende da qui (`swapRiprendi`): chiudere
   l'app a meta' non perde niente. */
let swapTimer = null;
const swapRitirando = new Set();
function swapAperti(){ return swapLista().filter(r => !SWAP_FASI_FINALI.has(swapFase(r))); }
function swapSorveglia(){
  if (swapTimer || !swapAperti().length) return;
  swapTimer = setInterval(swapGiro, 5000);
  swapGiro();
}
async function swapGiro(){
  const aperti = swapAperti();
  if (!aperti.length || !swapAcceso()) { clearInterval(swapTimer); swapTimer = null; return; }
  for (const rec of aperti) {
    const f = swapFornitore(swapDiChi(rec));
    if (!f) continue;
    let s;
    try { s = await f.stato(rec); }
    catch(e){ continue; }
    if (s && s !== rec.stato) {
      rec.stato = s;
      swapSalvaRecord(rec);
      swapRidisegnaDove(rec);
    }
    if (SWAP_FASI_RITIRO.has(swapFase(rec)) && !(rec.ritiro && rec.ritiro.txid))
      await swapRitira(rec);
  }
}
async function swapRitira(rec){
  if (swapRitirando.has(rec.id) || !rec.indirizzo) return;
  swapRitirando.add(rec.id);
  try {
    const fid = swapDiChi(rec), f = swapFornitore(fid);
    const c = swapCassetto(fid);
    if (!f) throw new Error('fornitore assente');
    if (!c || !c.parole) throw new Error('parole assenti');
    const fatto = await f.ritira(rec, c.parole);
    rec.ritiro = {txid: fatto.txid, cooperativo: fatto.cooperativo, quando: Date.now()};
    delete rec.errore;
  } catch(e){
    rec.errore = String((e && e.message) || e).slice(0, 120);
  } finally {
    swapRitirando.delete(rec.id);
    swapSalvaRecord(rec);
    swapRidisegnaDove(rec);
  }
}
function swapRiprendi(){ if (swapAcceso()) swapSorveglia(); }
function swapRidisegnaDove(rec){
  if (currentOrder && Number(currentOrder.id) === Number(rec.ordine)
      && el('payoutIncasso')) ridisegnaIncassoSwap();
  if (el('view-swap') && el('view-swap').classList.contains('active')) renderSwapTelefono();
}

/* ─── 8. LA PAGINA «SWAP» ───────────────────────────────────────────────
   La lista di tutti gli swap; poi, per ogni fornitore, le sue parole (a
   richiesta) e il suo bottone di recupero. Un campo solo per le parole:
   la xpub va SOLO al fornitore del bottone toccato. */
function renderSwapTelefono(){
  const box = el('swapTelefono');
  if (!box) return;
  const t = t3(), piu = swapPiuFornitori();
  const lista = swapLista().slice().sort((a, b) => (b.creato || 0) - (a.creato || 0));
  /* con degli swap in lista, il «per ora nessuno» della tappa 1 tace */
  if (el('swapVuoto')) el('swapVuoto').style.display = lista.length ? 'none' : '';
  const righe = lista.map(rec => `<div class="swap-riga-lista">
      <b>${esc(rec.ordine ? t.ordine(rec.ordine) : t.recuperato)}</b>
      <span>${esc(frasestatoSwap(rec))}</span>
      ${piu ? `<span class="swap-da">${esc(t.eseguitoDa(swapNomeFornitore(swapDiChi(rec))))}</span>` : ''}
      ${!rec.indirizzo && SWAP_FASI_RITIRO.has(swapFase(rec)) ? `
        <input class="swap-indirizzo" id="swapIndirizzoR_${esc(rec.id)}" type="text" autocomplete="off" spellcheck="false" placeholder="bc1…">
        <button class="btn ghost" type="button" data-swap="ritira-a" data-id="${esc(rec.id)}">${esc(t.ritiraA)}</button>` : ''}
    </div>`).join('');
  const parole = swapFornitori().map(f => {
    const c = swapCassetto(f.id), viste = !!swapParoleViste[f.id];
    const elenco = c && c.parole && viste
      ? `<ol class="swap-parole">${String(c.parole).split(' ').map(p => `<li>${esc(p)}</li>`).join('')}</ol>` : '';
    return `<h4>🔑 ${esc(piu ? t.paroleDi(f.nome) : t.paroleTit)}</h4>
    ${c && c.parole
      ? `<button class="btn ghost" type="button" data-swap="mostra-parole" data-fornitore="${esc(f.id)}">${esc(viste ? t.nascondi : t.mostra)}</button>${elenco}`
      : `<div class="hint">${esc(t.nessunaParola)}</div>`}`;
  }).join('');
  const bottoni = swapFornitori().map(f =>
    `<button class="btn orange" type="button" data-swap="recupera" data-fornitore="${esc(f.id)}">${esc(piu ? t.recuperaDa(f.nome) : t.recupera)}</button>`).join('');
  box.innerHTML = `
    ${lista.length ? `<h4>${esc(t.lista)}</h4>${righe}` : ''}
    ${parole}
    <h4>${esc(t.recuperaTit)}</h4>
    <div class="hint">${esc(t.recuperaSpiega)}</div>
    <textarea id="swapRecupero" rows="3" autocomplete="off" spellcheck="false"></textarea>
    <div id="swapRecuperoNota" class="hint" role="status">${esc(swapNotaRecupero.testo)}</div>
    ${bottoni}`;
}
/* la frase del recupero sopravvive al ridisegno della pagina (presa dal
   giro dal vivo: la pagina si riscrive subito dopo, e la cancellava) */
const swapNotaRecupero = {testo: ''};
function swapDiciRecupero(frase){
  swapNotaRecupero.testo = frase;
  const n = el('swapRecuperoNota');
  if (n) n.textContent = frase;
}
async function swapRecupera(fid){
  haptic();
  const t = t3();
  const f = swapFornitore(fid || (swapFornitori()[0] || {}).id);
  swapDiciRecupero('');
  if (!f) return;
  const parole = String((el('swapRecupero') || {}).value || '').trim().toLowerCase().split(/\s+/).join(' ');
  let valide;
  try { valide = await f.paroleValide(parole); }
  catch(e){ swapDiciRecupero(t.nonRisponde(f.nome)); return; }
  if (!valide) { swapDiciRecupero(t.recuperaNo); return; }
  const c = swapCassetto(f.id);
  if (c && c.parole && c.parole !== parole && swapLista().some(r => swapDiChi(r) === f.id)) {
    swapDiciRecupero(t.recuperaAltre); return;
  }
  let trovati;
  try { trovati = await f.recupera(parole); }
  catch(e){ swapDiciRecupero(t.nonRisponde(f.nome)); return; }
  let prossimo = c && c.parole === parole ? Number(c.prossimo) || 0 : 0;
  prossimo = Math.max(prossimo, Number(trovati.prossimo) || 0);
  let quanti = 0;
  for (const s of trovati.swap) {
    if (swapLista().some(r => r.id === s.id)) continue;
    swapSalvaRecord(Object.assign(s, {fornitore: f.id, ordine: null, indirizzo: ''}));
    quanti++;
  }
  swapScrivi(swapCasaParole(f.id), {parole: parole, prossimo: prossimo, copiata: true});
  swapDiciRecupero(t.recuperaFatto(quanti));
  renderSwapTelefono();
  swapSorveglia();
}
function swapRitiraA(id){
  haptic();
  const rec = swapLista().find(r => r.id === id);
  const v = String((el(`swapIndirizzoR_${id}`) || {}).value || '').trim();
  if (!rec || !v) return;
  const f = swapFornitore(swapDiChi(rec));
  if (!f) return;
  f.indirizzoValido(v).then(ok => {
    if (!ok) { toast(t3().indirizzoNo); return; }
    rec.indirizzo = v;
    swapSalvaRecord(rec);
    renderSwapTelefono();
    swapRitira(rec);
  }).catch(() => toast(t3().nonRisponde(f.nome)));
}

/* ─── 9. L'ASCOLTATORE DELEGATO: niente handler inline ──────────────── */
if (typeof document !== 'undefined') {
  document.addEventListener('click', ev => {
    const b = ev.target && ev.target.closest ? ev.target.closest('[data-swap]') : null;
    if (!b) return;
    const n = Number(b.dataset.ordine || 0);
    const a = b.dataset.swap;
    const fid = String(b.dataset.fornitore || (swapFornitori()[0] || {}).id || '');
    if (a === 'scegli') scegliIncassoSwap(n, b.dataset.scelta === 'swap' ? 'swap' : 'ln');
    else if (a === 'avanti') swapAvanti(n);
    else if (a === 'parole-fatte') swapParoleFatte(n);
    else if (a === 'crea') swapCrea(n);
    else if (a === 'mostra-parole') { haptic(); swapParoleViste[fid] = !swapParoleViste[fid]; renderSwapTelefono(); }
    else if (a === 'recupera') swapRecupera(fid);
    else if (a === 'ritira-a') swapRitiraA(String(b.dataset.id || ''));
  });
  swapRiprendi();
}
