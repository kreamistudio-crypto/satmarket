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

   DALLA TAPPA 4 (24 ott 2026) BARATTOLO PAGA LA FATTURA DELLO SWAP: nato e
   verificato lo swap, il telefono manda al server le sole parti pubbliche
   (`pagaSwapAlServer` della pagina) e il server la paga coi sats
   dell'ordine. Il segreto resta qui, e esce solo per il ritiro, dopo i
   tre controlli sul lockup (swap/boltz.js).

   Usa dalla pagina: swapLeve, swapAcceso, myTgId, tg, el, esc, fmt, haptic,
   toast, currentOrder, preventiviSwap, scegliIncassoSwap,
   leggiPreventivoSwap, pannelloPreventivoSwap, ridisegnaIncassoSwap,
   linguaSwap, pagaSwapAlServer, statoPagamentoSwap. */

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
/* (tappa 4) uno swap che Barattolo NON ha pagato — rifiutato prima di
   partire, o fallito senza che uscisse niente — non tiene piu' l'incasso:
   chi vende sceglie di nuovo. Resta nella lista, e sorvegliato: se il
   fornitore bloccasse comunque i bitcoin, il telefono li ritira. */
function swapNonPagato(rec){
  return !!rec && ['rifiutato', 'fallito'].includes(rec.pagamento) && swapFase(rec) === 'creato';
}
function swapDiOrdine(ordine){
  const n = Number(ordine);
  const r = swapLista().filter(x => Number(x.ordine) === n).pop() || null;
  return swapNonPagato(r) ? null : r;
}
function swapFase(rec){
  const f = swapFornitore(swapDiChi(rec));
  return f ? f.fase(rec.stato) : 'ignoto';
}

/* ─── 3. I TESTI, in italiano e in inglese ─────────────────────────────
   (27 ott 2026, cantiere grafica-swap, regola di Andrea) niente parole
   tecniche: niente «swap», «fornitore», «lockup», «on-chain». Quel che fa
   SATS Routing e' «il cambio»; le 12 parole sono «di riserva» e si
   spiegano con calma UNA volta, alla prima (il passo 'parole'). */
const SWAP_TESTI_T3 = {
  it: {
    paroleTit: 'Le tue 12 parole di riserva',
    paroleDi: n => `Le tue 12 parole di riserva per ${n}`,
    paroleSpiega: 'Servono solo se qualcosa va storto: con queste riprendi i tuoi bitcoin anche da un altro telefono.',
    paroleRegole: ['Scrivile su carta, in ordine.',
                   'Non fotografarle e non darle a nessuno, nemmeno a noi.',
                   'Te le chiediamo una volta sola: le ritrovi nella pagina «Ricevi in bitcoin».'],
    paroleNessuno: 'Senza queste parole nessuno può recuperarli, nemmeno noi.',
    paroleSpunta: 'Le ho scritte su carta',
    paroleFatto: 'Continua',
    paroleSpuntaPrima: 'Prima spunta «Le ho scritte su carta».',
    indirizzoTit: 'Il tuo indirizzo bitcoin',
    indirizzoSpiega: 'Lo trovi nel tuo wallet, alla voce «Ricevi».',
    indirizzoManca: 'Prima metti il tuo indirizzo bitcoin: tocca «Incolla».',
    indirizzoNo: 'Questo non è un indirizzo bitcoin valido.',
    incolla: 'Incolla', qr: 'QR',
    appuntiChiusi: 'Non riesco a leggere gli appunti: tieni premuto sul campo e scegli «Incolla».',
    appuntiNo: 'Negli appunti non c\'è un indirizzo bitcoin valido: copialo dal tuo wallet.',
    qrTesto: 'Inquadra il QR del tuo indirizzo bitcoin',
    qrNo: 'Questo QR non è un indirizzo bitcoin valido.',
    qrCamera: 'Non riesco ad aprire la fotocamera: incolla l\'indirizzo.',
    qrChiudi: 'Chiudi',
    creo: n => `Preparo il cambio con ${n} e controllo la sua risposta…`,
    nienteCasa: 'Questo telefono non riesce a conservare le 12 parole: da qui si incassa solo in Lightning.',
    rifiuto: n => `${n} ha risposto con dati che non tornano: non parte niente, nessun sats si è mosso.`,
    nonRisponde: n => `${n} ora non risponde: riprova, o incassa in Lightning.`,
    tuoSwap: 'Il tuo incasso in bitcoin',
    eseguitoDa: n => `Il cambio lo fa ${n}`,
    ricevi: n => `Ricevi circa ${n} sats a`,
    /* i tre pallini della carta: a che punto e' */
    passi: ['Pagato', 'In arrivo', 'Arrivato'],
    passiEt: 'A che punto è',
    fasi: {
      creato: () => 'Barattolo sta pagando il cambio: poi i bitcoin partono verso il tuo indirizzo.',
      bloccato: n => `${n} ha preparato i tuoi bitcoin: li sto mandando al tuo indirizzo.`,
      confermato: () => 'I tuoi bitcoin sono pronti: li sto mandando al tuo indirizzo.',
      fatto: () => 'Fatto: i bitcoin sono al tuo indirizzo.',
      scaduto: () => 'Scaduto: nessun sats si è mosso, l\'incasso torna disponibile.',
      fallito: () => 'Non riuscito: l\'incasso torna disponibile.',
      ripreso: n => `${n} si è ripreso i bitcoin: l'incasso torna disponibile.`},
    statoIgnoto: 'In corso.',
    /* (tappa 4) il pagamento della fattura, finche' i bitcoin non sono pronti */
    pagamento: {
      pagato: n => `Pagato: aspetto che ${n} prepari i tuoi bitcoin.`,
      da_verificare: () => 'Pagamento da verificare: ci stiamo lavorando noi. I tuoi sats non si perdono.',
      fallito: () => 'Il pagamento non è partito: nessun sats si è mosso. Scegli di nuovo come incassare.',
      tetto_utente: () => 'Per oggi hai raggiunto il tetto degli incassi in bitcoin: incassa via Lightning.',
      tetto_giorno: () => 'Per oggi gli incassi in bitcoin sono al completo: incassa via Lightning.',
      cambiata: () => 'Le cifre sono cambiate: nessun sats si è mosso. Scegli di nuovo come incassare.',
      rifiutato: () => 'Barattolo non paga questo cambio: nessun sats si è mosso. Scegli di nuovo come incassare.'},
    ritirato: id => `Partiti verso il tuo indirizzo: transazione ${id}.`,
    concluso: (sats, id) => `Concluso: ${sats} sats arrivati (transazione ${id}).`,
    ritiroErrore: 'L\'invio al tuo indirizzo non è ancora riuscito: riprovo da solo.',
    spesoAltri: n => `Quei bitcoin li ha spesi un'altra transazione, non il tuo invio: scrivi a ${n}.`,
    lista: 'I tuoi incassi in bitcoin',
    ordine: n => `Ordine #${n}`,
    recuperato: 'Recuperato',
    mostra: 'Mostra le 12 parole',
    nascondi: 'Nascondi',
    nessunaParola: 'Non hai ancora le parole: nascono col primo incasso in bitcoin.',
    recuperaTit: 'Recupera da 12 parole',
    recuperaSpiega: 'Se avevi già degli incassi in bitcoin su un altro telefono, incolla qui le tue 12 parole.',
    recupera: 'Recupera',
    recuperaDa: n => `Recupera da ${n}`,
    recuperaNo: 'Queste non sono 12 parole valide.',
    recuperaAltre: 'Su questo telefono ci sono già altre parole in uso: non le sostituisco.',
    recuperaFatto: n => n === 0 ? 'Nessun incasso legato a queste parole.'
      : n === 1 ? 'Recuperato 1 incasso.' : `Recuperati ${n} incassi.`,
    ritiraA: 'Manda a questo indirizzo'},
  en: {
    paroleTit: 'Your 12 backup words',
    paroleDi: n => `Your 12 backup words for ${n}`,
    paroleSpiega: 'You need them only if something goes wrong: with them you get your bitcoin back, even from another phone.',
    paroleRegole: ['Write them on paper, in order.',
                   'Do not photograph them and do not give them to anyone, not even to us.',
                   'We ask you only once: you find them again on the «Receive in bitcoin» page.'],
    paroleNessuno: 'Without these words nobody can recover them, not even us.',
    paroleSpunta: 'I wrote them on paper',
    paroleFatto: 'Continue',
    paroleSpuntaPrima: 'First tick «I wrote them on paper».',
    indirizzoTit: 'Your bitcoin address',
    indirizzoSpiega: 'You find it in your wallet, under «Receive».',
    indirizzoManca: 'First add your bitcoin address: tap «Paste».',
    indirizzoNo: 'This is not a valid bitcoin address.',
    incolla: 'Paste', qr: 'QR',
    appuntiChiusi: 'I cannot read the clipboard: press and hold the field and choose «Paste».',
    appuntiNo: 'The clipboard holds no valid bitcoin address: copy it from your wallet.',
    qrTesto: 'Frame the QR of your bitcoin address',
    qrNo: 'This QR is not a valid bitcoin address.',
    qrCamera: 'I cannot open the camera: paste the address.',
    qrChiudi: 'Close',
    creo: n => `Preparing the exchange with ${n} and checking its answer…`,
    nienteCasa: 'This phone cannot keep the 12 words: from here you can only receive via Lightning.',
    rifiuto: n => `${n} answered with data that does not add up: nothing starts, no sats moved.`,
    nonRisponde: n => `${n} is not responding: try again, or receive via Lightning.`,
    tuoSwap: 'Your payout in bitcoin',
    eseguitoDa: n => `The exchange is done by ${n}`,
    ricevi: n => `You receive about ${n} sats at`,
    passi: ['Paid', 'On its way', 'Arrived'],
    passiEt: 'Where it is',
    fasi: {
      creato: () => 'Barattolo is paying the exchange: then the bitcoin leave for your address.',
      bloccato: n => `${n} prepared your bitcoin: sending them to your address.`,
      confermato: () => 'Your bitcoin are ready: sending them to your address.',
      fatto: () => 'Done: the bitcoin are at your address.',
      scaduto: () => 'Expired: no sats moved, the payout is available again.',
      fallito: () => 'Failed: the payout is available again.',
      ripreso: n => `${n} took the bitcoin back: the payout is available again.`},
    statoIgnoto: 'In progress.',
    pagamento: {
      pagato: n => `Paid: waiting for ${n} to prepare your bitcoin.`,
      da_verificare: () => 'Payment being checked: we are on it. Your sats are not lost.',
      fallito: () => 'The payment did not go out: no sats moved. Choose again how to receive.',
      tetto_utente: () => 'You reached the limit of bitcoin payouts for today: receive via Lightning.',
      tetto_giorno: () => 'Bitcoin payouts are full for today: receive via Lightning.',
      cambiata: () => 'The figures changed: no sats moved. Choose again how to receive.',
      rifiutato: () => 'Barattolo does not pay this exchange: no sats moved. Choose again how to receive.'},
    ritirato: id => `On their way to your address: transaction ${id}.`,
    concluso: (sats, id) => `Done: ${sats} sats arrived (transaction ${id}).`,
    ritiroErrore: 'Sending to your address did not go through yet: retrying by itself.',
    spesoAltri: n => `Those bitcoin were spent by another transaction, not by your sending: write to ${n}.`,
    lista: 'Your bitcoin payouts',
    ordine: n => `Order #${n}`,
    recuperato: 'Recovered',
    mostra: 'Show the 12 words',
    nascondi: 'Hide',
    nessunaParola: 'You have no words yet: they are born with the first bitcoin payout.',
    recuperaTit: 'Recover from 12 words',
    recuperaSpiega: 'If you had bitcoin payouts on another phone, paste your 12 words here.',
    recupera: 'Recover',
    recuperaDa: n => `Recover from ${n}`,
    recuperaNo: 'These are not 12 valid words.',
    recuperaAltre: 'This phone already has other words in use: I will not replace them.',
    recuperaFatto: n => n === 0 ? 'No payouts tied to these words.'
      : n === 1 ? 'Recovered 1 payout.' : `Recovered ${n} payouts.`,
    ritiraA: 'Send to this address'}};
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
   I passi di un ordine: 'preventivo' (le cifre, e sotto il campo
   dell'indirizzo) -> 'parole' (la prima volta con QUEL fornitore) ->
   'creo'. Poi c'e' lo swap, e il pannello mostra il suo stato.
   I TOCCHI (27 ott 2026, cantiere grafica-swap, regola di Andrea: al piu'
   tre dopo la conferma): l'indirizzo si mette PRIMA di «Conferma», con
   «Incolla» o col QR; dopo la conferma chi ha gia' le parole non tocca
   piu' niente, e la prima volta tocca la spunta e «Continua». Il passo
   'indirizzo' di ieri non c'e' piu': chi lo avesse in memoria torna al
   preventivo, che ha il campo. */
const swapPassi = {};      // ordine -> passo
const swapErrori = {};     // ordine -> frase
/* l'indirizzo scritto, per ordine: un avviso ridisegna il pannello, e un
   bc1 lungo non si fa riscrivere da capo (preso dal giro dal vivo). Lo
   tiene aggiornato l'ascoltatore dell'input, in fondo: il preventivo si
   ridisegna anche da solo (le cifre che si rileggono) */
const swapIndirizziScritti = {};
const swapParoleViste = {};   // fornitore -> true quando si vedono
function swapScelto(n){
  const d = ((preventiviSwap[n] || {}).dati) || {};
  return d.fornitore || 'satsrouting';
}
/* L'INDIRIZZO DA QUEL CHE ARRIVA: incollato, inquadrato o scritto, anche
   nella forma «bitcoin:bc1…?amount=…» dei wallet; un bech32 tutto
   maiuscolo (i QR lo fanno per stare piccoli) torna minuscolo. Il
   giudice resta `indirizzoValido` del fornitore, con la sua rete. */
function swapEstraiIndirizzo(testo){
  let s = String(testo || '').trim();
  if (/^bitcoin:/i.test(s)) s = s.slice(8);
  s = s.split('?')[0].replace(/\s+/g, '');
  if (/^(bc1|tb1|bcrt1)/i.test(s) && s === s.toUpperCase()) s = s.toLowerCase();
  return s.slice(0, 120);
}
/* IL QR: dentro Telegram, sul telefono, lo scanner di Telegram; fuori, la
   fotocamera della pagina SOLO se il browser sa leggere i QR da se'
   (BarcodeDetector: niente librerie nuove, decisione di Andrea). Dove non
   c'e' nessuno dei due il bottone non compare, e resta «Incolla». */
function swapQrTelegram(){
  try {
    return !!(typeof tg !== 'undefined' && tg && tg.initData
      && typeof tg.showScanQrPopup === 'function'
      && (!tg.isVersionAtLeast || tg.isVersionAtLeast('6.4'))
      && ['android', 'android_x', 'ios'].includes(String(tg.platform || '')));
  } catch(e){ return false; }
}
function swapQrBrowser(){
  return typeof window !== 'undefined' && 'BarcodeDetector' in window
    && !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}
function swapQrPossibile(){ return swapQrTelegram() || swapQrBrowser(); }
function campoIndirizzoSwap(n, errore){
  const t = t3();
  return `<div class="swap-campo">
      <h4>₿ ${esc(t.indirizzoTit)}</h4>
      <div class="hint">${esc(t.indirizzoSpiega)}</div>
      ${errore}
      <input class="swap-indirizzo" id="swapIndirizzo_${n}" type="text" autocomplete="off"
        spellcheck="false" placeholder="bc1…" inputmode="text" value="${esc(swapIndirizziScritti[n] || '')}">
      <div class="swap-attrezzi">
        <button class="btn ghost" type="button" data-swap="incolla" data-ordine="${n}">📋 ${esc(t.incolla)}</button>
        ${swapQrPossibile() ? `<button class="btn ghost" type="button" data-swap="qr" data-ordine="${n}">📷 ${esc(t.qr)}</button>` : ''}
      </div>
    </div>`;
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
    /* LE 12 PAROLE, UNA VOLTA SOLA E CON CALMA: a cosa servono, le tre
       regole, chi puo' recuperare senza (nessuno). Poi le parole, la
       spunta e «Continua», che fa partire tutto da solo. */
    const c = swapCassetto(fid);
    const parole = c && c.parole ? String(c.parole).split(' ') : [];
    return `<div class="swap-prev swap-prima-volta">
      <h4>🔑 ${esc(swapPiuFornitori() ? t.paroleDi(nome) : t.paroleTit)}</h4>
      <p class="swap-calma">${esc(t.paroleSpiega)}</p>
      <ol class="swap-regole">${t.paroleRegole.map(r => `<li>${esc(r)}</li>`).join('')}</ol>
      <p class="swap-calma forte">${esc(t.paroleNessuno)}</p>
      ${errore}
      <ol class="swap-parole">${parole.map(p => `<li>${esc(p)}</li>`).join('')}</ol>
      <label class="swap-spunta"><input type="checkbox" id="swapSpunta_${n}"> ${esc(t.paroleSpunta)}</label>
      <button class="btn orange" type="button" data-swap="parole-fatte" data-ordine="${n}">${esc(t.paroleFatto)}</button>
    </div>`;
  }
  if (passo === 'creo') return `<div class="swap-prev">
      <h4>₿ ${esc(t.tuoSwap)}</h4>
      ${passiSwap(0)}
      <div class="swap-stato" role="status">${esc(t.creo(nome))}</div>
    </div>`;
  return pannelloPreventivoSwap(o, campoIndirizzoSwap(n, errore));
}
/* I TRE PALLINI (27 ott 2026): quanti passi sono stati raggiunti fra
   «Pagato», «In arrivo» e «Arrivato»; -1 quando lo swap non va avanti
   (scaduto, non riuscito, rifiutato, speso da altri) e parla la frase
   da sola */
function swapTappa(rec){
  const fase = swapFase(rec);
  if (rec.spesoDa || ['scaduto', 'fallito', 'ripreso'].includes(fase)) return -1;
  if ((rec.ritiro && rec.ritiro.concluso) || fase === 'fatto') return 3;
  if ((rec.ritiro && rec.ritiro.txid) || SWAP_FASI_RITIRO.has(fase)) return 2;
  if (fase !== 'creato' || ['fallito', 'rifiutato'].includes(rec.pagamento)) return -1;
  return ['in_volo', 'pagato'].includes(rec.pagamento) ? 1 : 0;
}
function passiSwap(quanti){
  if (quanti < 0) return '';
  const t = t3();
  return `<ol class="swap-passi" aria-label="${esc(t.passiEt)}">${t.passi.map((p, i) =>
    `<li class="${i < quanti ? 'fatto' : i === quanti ? 'ora' : ''}"${i === quanti ? ' aria-current="step"' : ''}>${esc(p)}</li>`).join('')}</ol>`;
}
function frasestatoSwap(rec){
  const t = t3();
  /* (20 ott 2026, swap-spesa) la spesa del lockup letta dalla rete */
  if (rec.ritiro && rec.ritiro.concluso)
    return t.concluso(fmt(rec.ritiro.sats || rec.ricevi || 0), swapCorto(rec.ritiro.txid, 8));
  if (rec.spesoDa) return t.spesoAltri(swapNomeFornitore(swapDiChi(rec)));
  if (rec.ritiro && rec.ritiro.txid && swapFase(rec) !== 'fatto')
    return t.ritirato(swapCorto(rec.ritiro.txid, 8));
  /* (tappa 4) prima del lockup parla il pagamento della fattura */
  if (swapFase(rec) === 'creato') {
    const tiene = k => Object.prototype.hasOwnProperty.call(t.pagamento, k);
    const chiave = rec.pagamento === 'rifiutato'
      ? (tiene(rec.motivo) ? rec.motivo : 'rifiutato') : rec.pagamento;
    if (tiene(chiave)) return t.pagamento[chiave](swapNomeFornitore(swapDiChi(rec)));
  }
  const f = t.fasi[swapFase(rec)];
  return f ? f(swapNomeFornitore(swapDiChi(rec))) : t.statoIgnoto;
}
function cartaSwap(rec){
  const t = t3();
  return `<div class="swap-prev swap-carta" data-swap-id="${esc(rec.id)}">
    <h4>₿ ${esc(t.tuoSwap)}</h4>
    ${passiSwap(swapTappa(rec))}
    <div class="swap-stato" role="status">${esc(frasestatoSwap(rec))}</div>
    ${rec.ricevi && rec.indirizzo ? `<div class="hint">${esc(t.ricevi(fmt(rec.ricevi)))} <span class="mono">${esc(swapCorto(rec.indirizzo, 8))}</span></div>` : ''}
    ${rec.errore && !rec.spesoDa ? `<div class="hint">${esc(t.ritiroErrore)}</div>` : ''}
    <div class="swap-da">${esc(t.eseguitoDa(swapNomeFornitore(swapDiChi(rec))))}</div>
  </div>`;
}

/* ─── 6. LE AZIONI ──────────────────────────────────────────────────── */
/* «Conferma» del preventivo: l'indirizzo prima (si guarda in casa, senza
   rete), poi si ricontrollano le tariffe del fornitore scelto con
   l'impronta di quelle mostrate (la tappa 2); se reggono, la prima volta
   con quel fornitore le parole, sennò lo swap parte subito */
/* UN GIRO ALLA VOLTA PER ORDINE: da quando «Conferma» non ha piu' un
   secondo bottone dopo, un doppio tocco farebbe nascere due swap. Chi
   arriva mentre l'altro lavora, o quando lo swap c'e' gia', non fa niente. */
const swapInCorso = new Set();
async function swapAvanti(n){
  haptic();
  if (swapInCorso.has(n) || swapDiOrdine(n)) return;
  swapInCorso.add(n);
  try { await swapAvantiDentro(n); } finally { swapInCorso.delete(n); }
}
async function swapAvantiDentro(n){
  delete swapErrori[n];
  const t = t3();
  const campo = el(`swapIndirizzo_${n}`);
  if (campo) swapIndirizziScritti[n] = String(campo.value || '');
  const indirizzo = swapEstraiIndirizzo(swapIndirizziScritti[n]);
  if (!indirizzo) { swapErrori[n] = t.indirizzoManca; return ridisegnaIncassoSwap(); }
  swapIndirizziScritti[n] = indirizzo;
  const prima = swapFornitore(swapScelto(n));
  if (prima) {
    let valido;
    try { valido = await prima.indirizzoValido(indirizzo); }
    catch(e){ swapErrori[n] = t.nonRisponde(prima.nome); return ridisegnaIncassoSwap(); }
    if (!valido) { swapErrori[n] = t.indirizzoNo; return ridisegnaIncassoSwap(); }
  }
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
      catch(e){ swapErrori[n] = t.nonRisponde(f.nome); return ridisegnaIncassoSwap(); }
      const nuovo = {parole: parole, prossimo: 0, copiata: false};
      if (!swapScrivi(swapCasaParole(fid), nuovo)) { swapErrori[n] = t.nienteCasa; return ridisegnaIncassoSwap(); }
    }
    swapPassi[n] = 'parole';
    return ridisegnaIncassoSwap();
  }
  return swapCreaDentro(n);
}
/* «Continua» delle parole: segnate come copiate, lo swap parte da solo
   con l'indirizzo gia' messo (niente terzo passo da toccare) */
function swapParoleFatte(n){
  haptic();
  if (swapInCorso.has(n) || swapDiOrdine(n)) return;
  const spunta = el(`swapSpunta_${n}`);
  if (!spunta || !spunta.checked) { swapErrori[n] = t3().paroleSpuntaPrima; return ridisegnaIncassoSwap(); }
  const fid = swapScelto(n);
  const c = swapCassetto(fid);
  if (!c) return;
  c.copiata = true;
  if (!swapScrivi(swapCasaParole(fid), c)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
  delete swapErrori[n];
  return swapCrea(n);
}
/* LA NASCITA, senza tocco suo: la chiamano «Conferma» e «Continua». Ogni
   no riporta al preventivo col suo perche', e l'indirizzo resta nel campo */
async function swapCrea(n){
  if (swapInCorso.has(n) || swapDiOrdine(n)) return;
  swapInCorso.add(n);
  try { await swapCreaDentro(n); } finally { swapInCorso.delete(n); }
}
async function swapCreaDentro(n){
  const t = t3();
  const indirizzo = swapEstraiIndirizzo(swapIndirizziScritti[n]);
  const p = ((preventiviSwap[n] || {}).dati) || {};
  const fid = swapScelto(n), f = swapFornitore(fid);
  if (!f) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  let valido;
  try { valido = !!indirizzo && await f.indirizzoValido(indirizzo); }
  catch(e){ swapPassi[n] = 'preventivo'; swapErrori[n] = t.nonRisponde(f.nome); return ridisegnaIncassoSwap(); }
  if (!valido) { swapPassi[n] = 'preventivo'; swapErrori[n] = indirizzo ? t.indirizzoNo : t.indirizzoManca; return ridisegnaIncassoSwap(); }
  if (!p.ok || !p.hash) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  const c = swapCassetto(fid);
  if (!c || !c.parole || !c.copiata) { swapPassi[n] = 'parole'; return ridisegnaIncassoSwap(); }
  /* L'INDICE SI PRENOTA PRIMA DI CHIEDERE: se il telefono si spegne a meta',
     al giro dopo si usa il successivo, mai lo stesso */
  const indice = Number(c.prossimo) || 0;
  c.prossimo = indice + 1;
  if (!swapScrivi(swapCasaParole(fid), c)) { swapPassi[n] = 'preventivo'; swapErrori[n] = t.nienteCasa; return ridisegnaIncassoSwap(); }
  swapPassi[n] = 'creo';
  delete swapErrori[n];
  ridisegnaIncassoSwap();
  let nuovo;
  try { nuovo = await f.crea({parole: c.parole, indice: indice, preventivo: p, indirizzo: indirizzo}); }
  catch(e){
    if (e && e.tipo === 'mente') return swapRipiega(n, f);
    swapPassi[n] = 'preventivo';
    swapErrori[n] = t.nonRisponde(f.nome);
    return ridisegnaIncassoSwap();
  }
  const rec = Object.assign(nuovo, {fornitore: fid, ordine: n, indice: indice,
    indirizzo: indirizzo, creato: Date.now(), pagamento: ''});
  swapSalvaRecord(rec);
  delete swapPassi[n];
  ridisegnaIncassoSwap();
  await swapPaga(rec);
  swapSorveglia();
}
/* ─── 6a. «INCOLLA» E IL QR ───────────────────────────────────────────
   Quel che arriva si guarda subito col giudice del fornitore: buono, va
   nel campo; storto, lo si dice sopra il campo e il campo resta com'era. */
async function swapIndirizzoArrivato(n, testo, da){
  const t = t3();
  const indirizzo = swapEstraiIndirizzo(testo);
  const f = swapFornitore(swapScelto(n));
  let valido = false;
  try { valido = !!indirizzo && !!f && await f.indirizzoValido(indirizzo); }
  catch(e){ valido = false; }
  if (!valido) { swapErrori[n] = da === 'qr' ? t.qrNo : t.appuntiNo; return ridisegnaIncassoSwap(); }
  swapIndirizziScritti[n] = indirizzo;
  delete swapErrori[n];
  ridisegnaIncassoSwap();
}
/* dove il browser non lascia leggere gli appunti (certe WebView) lo dice,
   e mette il fuoco nel campo per il tieni-premuto-e-incolla (la strada
   del PayCode) */
async function swapIncolla(n){
  haptic();
  let testo = null;
  try { testo = await navigator.clipboard.readText(); } catch(e){ testo = null; }
  if (testo == null) {
    toast(t3().appuntiChiusi);
    const c = el(`swapIndirizzo_${n}`);
    if (c) try { c.focus(); } catch(e){}
    return;
  }
  return swapIndirizzoArrivato(n, testo, 'appunti');
}
/* LA FOTOCAMERA DELLA PAGINA, fuori da Telegram: uno strato a tutto
   schermo col video e «Chiudi». Il flusso si spegne SEMPRE alla chiusura
   (la lucina non resta accesa), e `swapQrGiro` numera le aperture: una
   risposta che arriva a strato chiuso spegne quel che ha avuto e tace
   (la lezione della fotocamera delle foto). */
let swapQrFlusso = null, swapQrGiro = 0, swapQrTimer = null;
function swapQr(n){
  haptic();
  const t = t3();
  if (swapQrTelegram()) {
    try {
      tg.showScanQrPopup({text: t.qrTesto}, testo => {
        swapIndirizzoArrivato(n, testo, 'qr');
        return true;
      });
      return;
    } catch(e){ /* questo Telegram non lo apre: si prova la pagina */ }
  }
  if (!swapQrBrowser()) { toast(t.qrCamera); return; }
  swapQrApri(n);
}
function swapQrStrato(){
  let s = el('swapQrStrato');
  if (s) return s;
  s = document.createElement('div');
  s.id = 'swapQrStrato';
  s.className = 'swap-qr-strato';
  s.setAttribute('role', 'dialog');
  s.setAttribute('aria-modal', 'true');
  document.body.appendChild(s);
  return s;
}
async function swapQrApri(n){
  const t = t3(), giro = ++swapQrGiro;
  const s = swapQrStrato();
  s.setAttribute('aria-label', t.qrTesto);
  s.innerHTML = `<video id="swapQrVideo" playsinline muted autoplay></video>
    <div class="swap-qr-mirino" aria-hidden="true"></div>
    <div class="swap-qr-piede">
      <div class="swap-qr-testo" role="status">${esc(t.qrTesto)}</div>
      <button class="swap-qr-btn" type="button" data-swap="qr-chiudi">✕ ${esc(t.qrChiudi)}</button>
    </div>`;
  s.classList.add('open');
  let flusso, lettore;
  try {
    lettore = new window.BarcodeDetector({formats: ['qr_code']});
    flusso = await navigator.mediaDevices.getUserMedia({audio: false,
      video: {facingMode: {ideal: 'environment'}}});
  } catch(e){
    if (giro === swapQrGiro) { swapQrChiudi(); toast(t.qrCamera); }
    return;
  }
  if (giro !== swapQrGiro) { flusso.getTracks().forEach(k => { try { k.stop(); } catch(e){} }); return; }
  swapQrFlusso = flusso;
  const v = el('swapQrVideo');
  v.srcObject = flusso;
  try { await v.play(); } catch(e){}
  const guarda = async () => {
    if (giro !== swapQrGiro) return;
    let letti = [];
    try { if (v.readyState >= 2) letti = await lettore.detect(v); } catch(e){ letti = []; }
    if (giro !== swapQrGiro) return;
    const primo = letti.find(x => x && x.rawValue);
    if (primo) { swapQrChiudi(); swapIndirizzoArrivato(n, primo.rawValue, 'qr'); return; }
    swapQrTimer = setTimeout(guarda, 250);
  };
  guarda();
}
function swapQrChiudi(){
  swapQrGiro++;
  clearTimeout(swapQrTimer);
  swapQrTimer = null;
  if (swapQrFlusso) swapQrFlusso.getTracks().forEach(k => { try { k.stop(); } catch(e){} });
  swapQrFlusso = null;
  const s = el('swapQrStrato');
  if (s) { s.classList.remove('open'); s.innerHTML = ''; }
}
/* ─── 6b. IL PAGAMENTO DELLA FATTURA (tappa 4) ────────────────────────
   Lo swap nato e verificato si salva PRIMA di chiedere il pagamento:
   chiudere l'app a meta' non perde niente, e al giro dopo si richiede.
   Il server e' idempotente sulla stessa fattura (la riconosce dalla sua
   impronta), quindi richiedere non paga mai due volte. Un «non risponde»
   del server, o della rete che il server legge, si riprova da solo, al
   massimo una volta al minuto; ogni altro no e' definitivo. */
const SWAP_PAGA_OGNI_MS = 60000;
const SWAP_NO_DI_PASSAGGIO = new Set(['mempool', 'non_risponde']);
const swapPagando = new Set();
const swapPagatoIl = {};
async function swapPaga(rec){
  if (!rec || !rec.ordine || swapPagando.has(rec.id)) return;
  swapPagando.add(rec.id);
  swapPagatoIl[rec.id] = Date.now();
  try {
    const d = await pagaSwapAlServer(rec);
    if (!d) return;
    if (d.ok) { rec.pagamento = String(d.stato || ''); delete rec.motivo; }
    else if (SWAP_NO_DI_PASSAGGIO.has(d.motivo)) { rec.pagamento = ''; rec.motivo = String(d.motivo); }
    else { rec.pagamento = 'rifiutato'; rec.motivo = String(d.motivo || ''); }
    swapSalvaRecord(rec);
    swapRidisegnaDove(rec);
  } finally { swapPagando.delete(rec.id); }
}
/* il giro del pagamento: prima del lockup si chiede al server a che punto
   e'; se il server non lo conosce (la richiesta non era arrivata) e non
   l'ha rifiutato, si richiede */
async function swapGiroPagamento(rec){
  if (!rec.ordine || swapFase(rec) !== 'creato' || swapNonPagato(rec)) return;
  let s;
  if (['', 'registrato'].includes(rec.pagamento || '')) {
    if (Date.now() - (swapPagatoIl[rec.id] || 0) < SWAP_PAGA_OGNI_MS) return;
    s = await statoPagamentoSwap(rec.ordine);
    if (s === '' || s === 'registrato') return swapPaga(rec);
  } else if (['in_volo', 'da_verificare'].includes(rec.pagamento)) {
    s = await statoPagamentoSwap(rec.ordine);
  } else return;
  if (!s || s === rec.pagamento) return;
  rec.pagamento = s;
  swapSalvaRecord(rec);
  swapRidisegnaDove(rec);
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
    swapPassi[n] = 'preventivo';
    swapErrori[n] = t.rifiuto(f.nome);
    return ridisegnaIncassoSwap();
  }
  swapPassi[n] = 'preventivo';
  await swapInstradaPreventivo(n, false);
  const p = preventiviSwap[n];
  p.nota = 'ripiego';
  p.ripiegoDa = f.nome;
  if (!p.dati || !p.dati.ok) {
    swapPassi[n] = 'preventivo';
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
    let s, tace = false;
    try { s = await f.stato(rec); }
    catch(e){ tace = true; }
    if (s && s !== rec.stato) {
      rec.stato = s;
      swapSalvaRecord(rec);
      swapRidisegnaDove(rec);
    }
    await swapGiroPagamento(rec);
    const daRitirare = !(rec.ritiro && rec.ritiro.txid);
    /* IL FORNITORE TACE (20 ott 2026, cantiere swap-senza-api): se la rete
       vede i bitcoin bloccati, si ritira lo stesso, senza la sua API */
    if (tace) {
      let inRete = false;
      if (daRitirare && f.lockupInRete) {
        try { inRete = await f.lockupInRete(rec); } catch(e){ inRete = false; }
      }
      if (inRete) await swapRitira(rec);
      continue;
    }
    if (SWAP_FASI_RITIRO.has(swapFase(rec)) && daRitirare)
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
    if (fatto.concluso) Object.assign(rec.ritiro, {concluso: true, sats: Number(fatto.sats) || 0});
    delete rec.errore;
    delete rec.spesoDa;
  } catch(e){
    rec.errore = String((e && e.message) || e).slice(0, 120);
    /* (swap-spesa) speso da un altro: lo si dice chiaro, non «riprovo» */
    if (e && e.tipo === 'speso') rec.spesoDa = String(e.txid || '');
    else delete rec.spesoDa;
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
    else if (a === 'incolla') swapIncolla(n);
    else if (a === 'qr') swapQr(n);
    else if (a === 'qr-chiudi') { haptic(); swapQrChiudi(); }
    else if (a === 'mostra-parole') { haptic(); swapParoleViste[fid] = !swapParoleViste[fid]; renderSwapTelefono(); }
    else if (a === 'recupera') swapRecupera(fid);
    else if (a === 'ritira-a') swapRitiraA(String(b.dataset.id || ''));
  });
  /* il campo dell'indirizzo si ricorda a ogni lettera: il preventivo si
     ridisegna anche da solo, e un bc1 lungo non si riscrive */
  document.addEventListener('input', ev => {
    const c = ev.target;
    if (c && typeof c.id === 'string' && c.id.startsWith('swapIndirizzo_'))
      swapIndirizziScritti[Number(c.id.slice(14))] = String(c.value || '');
  });
  /* la fotocamera non resta accesa ad app in secondo piano */
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && swapQrFlusso) swapQrChiudi();
  });
  swapRiprendi();
}
