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

   LE CHIAVI SONO DEL TELEFONO. Dal 29 ott 2026 (cantiere parole-uniche)
   ogni cambio nuovo nasce dalle dodici parole del wallet di Barattolo,
   le stesse dell'on-chain (vedi «UNA CHIAVE SOLA», qui sotto), con una
   chiave nuova a ogni cambio. Prima ogni fornitore aveva dodici parole
   sue, nel localStorage sotto il conto (`barattolo_swap_<tg_id>` per
   SATS Routing, `barattolo_swap_<fornitore>_<tg_id>` per gli altri):
   quei cassetti restano per i cambi gia' nati con loro. Gli swap stanno
   in una lista sola, e ognuno porta il suo fornitore. Al server di
   Barattolo arriva solo la richiesta del preventivo
   (`leggiPreventivoSwap` della pagina): niente chiavi.

   Niente script inline e niente `onclick=` (arriva la fase 2 della CSP):
   i bottoni portano `data-swap="…"` e li ascolta UN solo ascoltatore
   delegato, in fondo, con la sua lista chiusa.

   DALLA TAPPA 4 (24 ott 2026) BARATTOLO PAGA LA FATTURA DELLO SWAP: nato e
   verificato lo swap, il telefono manda al server le sole parti pubbliche
   (`pagaSwapAlServer` della pagina) e il server la paga coi sats
   dell'ordine. Il segreto resta qui, e esce solo per il ritiro, dopo i
   tre controlli sul lockup (swap/boltz.js).

   IL CAMBIO LIBERO (27 ott 2026, cantiere cambio-libero, tappa 2): dalla
   pagina «Cambio» chi passa il cancello cambia i SUOI sats senza un
   ordine. E' «l'ordine numero 0»: gli stessi passi dell'incasso
   (preventivo, indirizzo, parole dove servono, nascita, sorveglianza,
   ritiro) con tre differenze — la cifra la scrive lui; prima di chiedere
   lo swap al fornitore si stacca un BIGLIETTO al server (i tetti del
   giorno: `chiediBigliettoCambio` della pagina); e la fattura la paga LUI
   col suo wallet (QR, «Copia», «Apri nel wallet»), non Barattolo. I sats
   non passano mai dalla cassaforte.

   Usa dalla pagina: swapLeve, swapAcceso, myTgId, tg, el, esc, fmt, haptic,
   toast, currentOrder, preventiviSwap, scegliIncassoSwap,
   leggiPreventivoSwap, pannelloPreventivoSwap, ridisegnaIncassoSwap,
   linguaSwap, pagaSwapAlServer, statoPagamentoSwap, chiediBigliettoCambio,
   natoCambioAlServer, liberaBigliettoCambio, disegnaQr, portaWallet,
   leggiBolt11. */

/* ─── 1. LE STRADE E I FORNITORI ────────────────────────────────────── */
/* la sola strada di oggi: i sats dell'incasso, ricevuti in bitcoin on-chain */
const SWAP_STRADA = 'ln-btc';
/* (tappa 3, cambio-libero) la direzione scelta nel riquadro del cambio;
   gli ordini veri vanno sempre per SWAP_STRADA */
let swapCambioStrada = 'ln-btc';
function swapCambioStradaScelta(){ return swapCambioStrada; }
function swapStradaDi(n){ return Number(n) === 0 ? swapCambioStrada : SWAP_STRADA; }
function swapESub(rec){ return !!rec && rec.tipo === 'sub'; }
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
/* UNA CHIAVE SOLA, IL WALLET DI BARATTOLO (29 ott 2026, cantiere
   parole-uniche, idea di Alan, ok di Andrea: «la chiave deve cambiare
   sempre, ma durante la costruzione del multisig il descrittore deve
   essere unico»). Ogni cambio nuovo — la pagina «Cambio», «Al tuo
   indirizzo bitcoin» negli ordini, la vendita on-chain verso Lightning —
   nasce dalle dodici parole del wallet on-chain (`onchainSemeAssicurato`
   della pagina), che nascono da sole e hanno gia' le loro copie: il
   cloud di Telegram e i relay Nostr. LE PAROLE SONO UNA, LE CHIAVI NO:
   ogni cambio prende la sua, m/44/0/0/0/i con l'indice prenotato prima
   di chiedere (`swapPrenotaIndice`), mai la stessa due volte; il 2-di-3
   sta su un'altra strada (m/48'/1'/0'/2', indurita: la xpub di radice
   che il recupero manda al fornitore non la raggiunge), e ogni suo
   indirizzo ha il suo descrittore. Le parole nel cambio NON si mostrano
   piu': stanno nel Profilo, «Il wallet di Barattolo». Unica eccezione:
   dove nessuna copia fuori da questo dispositivo ridà le STESSE parole
   (fuori da Telegram e senza Nostr) il passo 'parole' resta, una volta
   (`copiata`), perche' li' un telefono perso perderebbe i bitcoin di un
   cambio andato storto. Il contatore e lo stato stanno in
   `barattolo_swap_oc_<tg_id>`: {prossimo, copiata}. */
function swapCasaOnchain(){ return `barattolo_swap_oc_${myTgId || 'x'}`; }
function swapStatoSeme(){
  const c = swapLeggi(swapCasaOnchain(), {});
  return c && typeof c === 'object' && !Array.isArray(c) ? c : {};
}
function swapParoleOnchain(){
  return typeof onchainSemeLocale === 'function' ? String(onchainSemeLocale() || '').trim() : '';
}
/* l'indice della prossima chiave, PRENOTATO e salvato prima di chiedere:
   mai sotto uno gia' in lista (un telefono che ha perso il contatore non
   riusa). -1 se il telefono non riesce a salvarlo: allora non parte niente */
function swapPrenotaIndice(){
  const c = swapStatoSeme();
  const usati = swapLista().filter(r => r.seme === 'onchain').map(r => (Number(r.indice) || 0) + 1);
  const indice = Math.max(Number(c.prossimo) || 0, ...usati, 0);
  c.prossimo = indice + 1;
  return swapScrivi(swapCasaOnchain(), c) ? indice : -1;
}
/* le parole che una copia fuori da qui ridà, viste in questa apertura:
   chi le ha gia' viste coperte non le richiede a ogni cambio */
let swapParoleCoperte = '';
function swapSemeDaMostrare(parole){
  return parole !== swapParoleCoperte && !swapStatoSeme().copiata;
}
/* IL SEME PRONTO PER UN CAMBIO: le parole (ritrovate o nate adesso,
   dalla pagina) e se va mostrato il passo delle parole. Alza con
   `.tipo` 'seme' quando la pagina non lo da' (il cloud di Telegram che
   non risponde: lei non fa nascere una chiave nuova sopra una vecchia) */
async function swapSemePronto(){
  if (typeof onchainSemeAssicurato !== 'function') throw swapNoOnchain('seme');
  let parole = '';
  try { parole = String(await onchainSemeAssicurato() || '').trim(); }
  catch(e){ throw swapNoOnchain('seme'); }
  if (!parole) throw swapNoOnchain('seme');
  if (parole !== swapParoleCoperte && typeof onchainSemeCoperto === 'function') {
    let coperte = false;
    try { coperte = !!(await onchainSemeCoperto(parole)); } catch(e){ coperte = false; }
    if (coperte) swapParoleCoperte = parole;
  }
  return {parole: parole, mostrare: swapSemeDaMostrare(parole)};
}
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
  /* (cambio-libero) l'ordine 0 e' il cambio libero: conta solo quello
     ancora VIVO, cosi' finito uno se ne puo' fare un altro */
  if (n === 0) return swapLista().filter(x => Number(x.ordine) === 0 && !SWAP_FASI_FINALI.has(swapFase(x))).pop() || null;
  const r = swapLista().filter(x => Number(x.ordine) === n).pop() || null;
  return swapNonPagato(r) ? null : r;
}
function swapECambio(rec){ return !!rec && Number(rec.ordine) === 0; }
function swapFase(rec){
  const f = swapFornitore(swapDiChi(rec));
  return f ? f.fase(rec.stato, rec) : 'ignoto';
}

/* ─── 3. I TESTI, in italiano e in inglese ─────────────────────────────
   (27 ott 2026, cantiere grafica-swap, regola di Andrea) niente parole
   tecniche: niente «swap», «fornitore», «lockup», «on-chain». Quel che fa
   SATS Routing e' «il cambio»; le 12 parole sono «di riserva» e si
   spiegano con calma UNA volta, alla prima (il passo 'parole'). */
const SWAP_TESTI_T3 = {
  it: {
    paroleTit: 'Le tue 12 parole',
    paroleDi: n => `Le tue 12 parole per ${n}`,
    paroleSpiega: 'Se perdi il telefono, con queste riprendi i tuoi bitcoin. Qui non c\'è una copia: scrivile tu.',
    paroleRegole: ['Scrivile su carta e non darle a nessuno, nemmeno a noi.',
                   'Le ritrovi nel Profilo, in «Il wallet di Barattolo».'],
    paroleSpunta: 'Le ho scritte su carta',
    paroleFatto: 'Continua',
    paroleSpuntaPrima: 'Prima spunta «Le ho scritte su carta».',
    indirizzoTit: 'Il tuo indirizzo bitcoin',
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
    semeNo: 'Non riesco a preparare la chiave del tuo wallet di Barattolo: riprova fra un momento. Nessun sats si è mosso.',
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
    lista: 'I tuoi cambi',
    ordine: n => `Ordine #${n}`,
    recuperato: 'Recuperato',
    mostra: 'Mostra le 12 parole',
    nascondi: 'Nascondi',
    nessunaParola: 'Non hai ancora le parole: nascono col primo incasso in bitcoin.',
    recuperaTit: 'Recupera da 12 parole',
    recupera: 'Recupera',
    recuperaDa: n => `Recupera da ${n}`,
    recuperaNo: 'Queste non sono 12 parole valide.',
    recuperaAltre: 'Su questo telefono ci sono già altre parole in uso: non le sostituisco.',
    recuperaFatto: n => n === 0 ? 'Nessun incasso legato a queste parole.'
      : n === 1 ? 'Recuperato 1 incasso.' : `Recuperati ${n} incassi.`,
    ritiraA: 'Manda a questo indirizzo',
    /* (cambio-libero) il cambio dei propri sats, senza ordine */
    cambio: 'Cambio',
    /* (grafica-cambio, 28 ott 2026) il tondo fra i due riquadri dice
       dove porta; sotto «Conferma» le tre tesserine (la riga chiusa
       delle parole e del recupero che stava in fondo e' passata al
       Profilo il 29 ott 2026, cantiere parole-uniche) */
    direzioni: {'ln-btc': 'Da Lightning a bitcoin', 'btc-ln': 'Da bitcoin a Lightning'},
    cifraTra: (a, b, u) => `Da ${a} a ${b} ${u || 'sats'}`,
    oggi: (n, m) => `oggi ${n} di ${m}`,
    unita: 'Unità delle cifre',
    tessere: [['ln', 'Veloce'], ['scudo', 'Restano tuoi'], ['gira', 'Due strade']],
    /* (parole-uniche, 29 ott 2026) le parole stanno nel Profilo */
    riservaDove: 'Le 12 parole sono nel Profilo',
    ritrovaTit: 'I tuoi cambi',
    ritrovaSpiega: 'Hai cambiato telefono? Tocca qui e ritrovi i tuoi cambi.',
    ritrova: 'Ritrova i miei cambi',
    ritrovaFatto: n => n === 0 ? 'Nessun cambio nuovo da ritrovare.'
      : n === 1 ? 'Ritrovato 1 cambio.' : `Ritrovati ${n} cambi.`,
    vecchieTit: 'Le parole dei cambi di prima',
    vecchieSpiega: 'Servono solo per i cambi fatti prima del 29 ottobre 2026.',
    cifraNo: 'Scrivi quanti sats vuoi cambiare.',
    tettoGiorno: m => `Per oggi hai fatto i ${m} cambi possibili: riprova domani.`,
    cambioNonRisponde: n => `${n} ora non risponde: riprova fra poco.`,
    pagaTu: n => `Paga questa richiesta col tuo wallet Lightning: appena ${n} la vede, i bitcoin partono verso il tuo indirizzo.`,
    copia: 'Copia', copiata: 'Copiata', apriWallet: 'Apri nel wallet',
    valeFino: h => `Vale fino alle ${h}`,
    cambioScaduto: 'Scaduto: nessun sats si è mosso. Puoi fare un cambio nuovo.',
    cambioFallito: 'Non riuscito: nessun sats si è mosso. Puoi fare un cambio nuovo.',
    cambioRipreso: n => `${n} si è ripreso i bitcoin, e il tuo pagamento torna al tuo wallet.`,
    /* (tappa 3) la strada rovesciata: bitcoin → Lightning */
    fatturaTit: 'La tua richiesta Lightning',
    fatturaSpiega: (n, b) => `Dal tuo wallet Lightning crea una richiesta di ${n} sats esatti${b ? ` (${b} BTC)` : ''} e incollala qui.`,
    fatturaManca: 'Prima incolla la richiesta del tuo wallet Lightning: tocca «Incolla».',
    fatturaNo: 'Questa non sembra una richiesta Lightning: ricontrollala.',
    fatturaImporto: n => `La richiesta deve essere di ${n} sats esatti.`,
    fatturaRete: 'Questa richiesta è di un\'altra rete.',
    fatturaScaduta: 'Questa richiesta scade troppo presto: creane una nuova.',
    mandaTu: (sats, n) => `Manda esattamente ${sats} sats a questo indirizzo, dal tuo wallet bitcoin: quando la rete li conferma, ${n} paga la tua richiesta.`,
    /* (28 ott 2026, onchain-verso-lightning) il cambio di una vendita
       pagata on-chain: i bitcoin li manda il deposito di garanzia */
    subDaOrdine: n => `I bitcoin partono dal deposito di garanzia appena chi ha comprato mette la seconda firma: poi ${n} paga la tua richiesta Lightning.`,
    copiaIndirizzo: 'Copia l\'indirizzo',
    subBloccato: 'Bitcoin visti: aspetto la conferma della rete, di solito una decina di minuti.',
    subConfermato: n => `Confermati: ${n} sta pagando la tua richiesta.`,
    subPagata: 'Pagata: i sats sono nel tuo wallet Lightning.',
    subFatto: 'Fatto: i sats sono nel tuo wallet Lightning.',
    subFallito: 'Non riuscito: i tuoi bitcoin tornano a te. Scrivi sotto dove rimandarli.',
    subScaduto: 'Scaduto: i tuoi bitcoin tornano a te. Scrivi sotto dove rimandarli.',
    subScadutoNiente: 'Scaduto: nessun bitcoin si è mosso. Puoi fare un cambio nuovo.',
    subPresto: 'I bitcoin tornano a te alla scadenza: ci penso io, apri l\'app ogni tanto.',
    subRipreso: id => `Ripresi: i bitcoin sono tornati al tuo indirizzo (${id}).`,
    rimborsaA: 'Rimanda a questo indirizzo',
    passiSub: ['Mandati', 'Confermati', 'Pagato']},
  en: {
    paroleTit: 'Your 12 words',
    paroleDi: n => `Your 12 words for ${n}`,
    paroleSpiega: 'If you lose your phone, these get your bitcoin back. There is no copy here: write them down.',
    paroleRegole: ['Write them on paper and give them to no one, not even us.',
                   'You find them in the Profile, under «Your Barattolo wallet».'],
    paroleSpunta: 'I wrote them on paper',
    paroleFatto: 'Continue',
    paroleSpuntaPrima: 'First tick «I wrote them on paper».',
    indirizzoTit: 'Your bitcoin address',
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
    semeNo: 'I cannot prepare the key of your Barattolo wallet: try again in a moment. No sats moved.',
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
    lista: 'Your exchanges',
    ordine: n => `Order #${n}`,
    recuperato: 'Recovered',
    mostra: 'Show the 12 words',
    nascondi: 'Hide',
    nessunaParola: 'You have no words yet: they are born with the first bitcoin payout.',
    recuperaTit: 'Recover from 12 words',
    recupera: 'Recover',
    recuperaDa: n => `Recover from ${n}`,
    recuperaNo: 'These are not 12 valid words.',
    recuperaAltre: 'This phone already has other words in use: I will not replace them.',
    recuperaFatto: n => n === 0 ? 'No payouts tied to these words.'
      : n === 1 ? 'Recovered 1 payout.' : `Recovered ${n} payouts.`,
    ritiraA: 'Send to this address',
    cambio: 'Exchange',
    direzioni: {'ln-btc': 'From Lightning to bitcoin', 'btc-ln': 'From bitcoin to Lightning'},
    cifraTra: (a, b, u) => `From ${a} to ${b} ${u || 'sats'}`,
    oggi: (n, m) => `today ${n} of ${m}`,
    unita: 'Unit of the figures',
    tessere: [['ln', 'Fast'], ['scudo', 'Stays yours'], ['gira', 'Two ways']],
    riservaDove: 'The 12 words are in the Profile',
    ritrovaTit: 'Your exchanges',
    ritrovaSpiega: 'New phone? Tap here to find your exchanges.',
    ritrova: 'Find my exchanges',
    ritrovaFatto: n => n === 0 ? 'No new exchanges to find.'
      : n === 1 ? 'Found 1 exchange.' : `Found ${n} exchanges.`,
    vecchieTit: 'The words of earlier exchanges',
    vecchieSpiega: 'Needed only for exchanges made before 29 October 2026.',
    cifraNo: 'Write how many sats you want to exchange.',
    tettoGiorno: m => `You made the ${m} exchanges allowed for today: try again tomorrow.`,
    cambioNonRisponde: n => `${n} is not responding: try again shortly.`,
    pagaTu: n => `Pay this request with your Lightning wallet: as soon as ${n} sees it, the bitcoin leave for your address.`,
    copia: 'Copy', copiata: 'Copied', apriWallet: 'Open in wallet',
    valeFino: h => `Valid until ${h}`,
    cambioScaduto: 'Expired: no sats moved. You can start a new exchange.',
    cambioFallito: 'Failed: no sats moved. You can start a new exchange.',
    cambioRipreso: n => `${n} took the bitcoin back, and your payment returns to your wallet.`,
    fatturaTit: 'Your Lightning request',
    fatturaSpiega: (n, b) => `From your Lightning wallet create a request for exactly ${n} sats${b ? ` (${b} BTC)` : ''} and paste it here.`,
    fatturaManca: 'First paste the request from your Lightning wallet: tap «Paste».',
    fatturaNo: 'This does not look like a Lightning request: check it again.',
    fatturaImporto: n => `The request must be for exactly ${n} sats.`,
    fatturaRete: 'This request belongs to another network.',
    fatturaScaduta: 'This request expires too soon: create a new one.',
    mandaTu: (sats, n) => `Send exactly ${sats} sats to this address, from your bitcoin wallet: once the network confirms them, ${n} pays your request.`,
    subDaOrdine: n => `The bitcoin leave the escrow deposit as soon as the buyer adds the second signature: then ${n} pays your Lightning request.`,
    copiaIndirizzo: 'Copy the address',
    subBloccato: 'Bitcoin seen: waiting for the network to confirm, usually about ten minutes.',
    subConfermato: n => `Confirmed: ${n} is paying your request.`,
    subPagata: 'Paid: the sats are in your Lightning wallet.',
    subFatto: 'Done: the sats are in your Lightning wallet.',
    subFallito: 'Failed: your bitcoin come back to you. Write below where to send them.',
    subScaduto: 'Expired: your bitcoin come back to you. Write below where to send them.',
    subScadutoNiente: 'Expired: no bitcoin moved. You can start a new exchange.',
    subPresto: 'The bitcoin come back to you after the expiry: I take care of it, open the app now and then.',
    subRipreso: id => `Taken back: the bitcoin returned to your address (${id}).`,
    rimborsaA: 'Send back to this address',
    passiSub: ['Sent', 'Confirmed', 'Paid']}};
function t3(){ return SWAP_TESTI_T3[linguaSwap()]; }
/* (cambio-libero) «non risponde» dell'ordine 0 non dice «incassa in
   Lightning»: nel cambio non c'e' nessun incasso */
function swapNonRisponde(n, nome){ return n === 0 ? t3().cambioNonRisponde(nome) : t3().nonRisponde(nome); }
function swapCorto(s, n){ s = String(s || ''); return s.length > 2 * n + 1 ? `${s.slice(0, n)}…${s.slice(-n)}` : s; }
function swapPiuFornitori(){ return swapFornitori().length > 1; }
/* LE ICONE DEL CAMBIO (28 ott 2026, cantiere grafica-cambio, Andrea: «non
   mi piacciono le icone e ci sono troppi testi»): DISEGNATE, col tratto
   della barra in basso (griglia da 24, currentColor), al posto delle
   emoji, che cambiavano forma da un telefono all'altro e nel tema scuro
   restavano quelle. Il ₿ e' quello della cella P2P; il fulmine si
   riempie (classe `pieno`). La pagina le chiede con `swapIcona`, anche
   dal pannello dell'ordine, solo quando questo file e' arrivato. */
const SWAP_ICONE = {
  ln: '<path class="pieno" d="M13.6 2.6 5.2 13.4h6.1l-1 8 8.5-10.9h-6.2z"/>',
  btc: '<g transform="rotate(13 12 12)"><path d="M8.3 6h4.4a2.9 2.9 0 0 1 .1 5.8H8.3"/>'
    + '<path d="M8.3 11.8h5.1a3.1 3.1 0 0 1 0 6.2H8.3"/><path d="M8.3 6v12"/><path d="M10.5 6V3.7"/>'
    + '<path d="M13.2 6V3.9"/><path d="M10.5 20.3V18"/><path d="M13.2 20.1V18"/></g>',
  gira: '<path d="M7.5 4v16"/><path d="m4 16.5 3.5 3.5 3.5-3.5"/><path d="M16.5 20V4"/><path d="m13 7.5 3.5-3.5 3.5 3.5"/>',
  incolla: '<rect x="6" y="4.5" width="12" height="16" rx="2.5"/><path d="M9.5 4.5v-.7c0-.7.5-1.3 1.2-1.3h2.6c.7 0 1.2.6 1.2 1.3v.7"/>'
    + '<path d="M9.5 11h5M9.5 14.5h5"/>',
  copia: '<rect x="8.5" y="8.5" width="11" height="12" rx="2.3"/><path d="M15.5 8.5V6.3c0-1-.8-1.8-1.8-1.8H6.3c-1 0-1.8.8-1.8 1.8v7.4c0 1 .8 1.8 1.8 1.8h2.2"/>',
  qr: '<path d="M4 8.5v-3C4 4.7 4.7 4 5.5 4h3M15.5 4h3c.8 0 1.5.7 1.5 1.5v3M20 15.5v3c0 .8-.7 1.5-1.5 1.5h-3M8.5 20h-3C4.7 20 4 19.3 4 18.5v-3"/>'
    + '<path d="M7.5 12h9"/>',
  chiave: '<circle cx="8" cy="15.5" r="3.8"/><path d="m10.8 12.8 8.7-8.7M16.3 7.3l2.4 2.4M13.8 9.8l2 2"/>',
  scudo: '<path d="M12 3.2 5.5 5.6v5.7c0 4.3 2.8 7.6 6.5 9.2 3.7-1.6 6.5-4.9 6.5-9.2V5.6z"/><path d="m9.2 12.2 2 2 3.8-4"/>',
  freccia: '<path d="m9.5 6 6 6-6 6"/>',
  /* (unita-tendine) la freccina della tendina, e il simbolo dei sats:
     tre righe e il tratto che le attraversa sopra e sotto */
  giu: '<path d="m6.5 9.5 5.5 5.5 5.5-5.5"/>',
  sats: '<path d="M6.5 8.5h11M6.5 12h11M6.5 15.5h11M12 4.5v2.4M12 17.1v2.4"/>'};
function swapIcona(nome){
  return `<svg class="cambio-svg" viewBox="0 0 24 24" aria-hidden="true">${SWAP_ICONE[nome] || ''}</svg>`;
}
/* la moneta tonda dei riquadri e delle schede: fulmine o ₿ */
function swapMoneta(rete){
  return `<span class="cambio-moneta ${rete === 'ln' ? 'ln' : rete === 'btc' ? 'btc' : 'piana'}">${swapIcona(rete)}</span>`;
}

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
  return swapFornitori().filter(f => f.strade.includes(swapStradaDi(n)) && !fuori.has(f.id));
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
   dell'indirizzo) -> 'parole' (dal 29 ott 2026 solo dove le parole del
   wallet di Barattolo non hanno copia fuori da qui, una volta) -> 'creo'. Poi c'e' lo swap, e il pannello mostra il suo stato.
   I TOCCHI (27 ott 2026, cantiere grafica-swap, regola di Andrea: al piu'
   tre dopo la conferma): l'indirizzo si mette PRIMA di «Conferma», con
   «Incolla» o col QR; dopo la conferma non si tocca piu' niente, e solo
   chi non ha copia delle parole tocca, una volta, la spunta e «Continua». Il passo
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
/* (grafica-cambio) il campo e i suoi attrezzi su una riga: «Incolla» e il
   QR sono due icone dentro il bordo del campo, col loro nome detto al
   lettore di schermo; la spiegazione di dove si trova l'indirizzo non
   c'e' piu' (il segnaposto «bc1…» e gli avvisi bastano) */
function campoIndirizzoSwap(n, errore){
  const t = t3();
  return `<div class="swap-campo">
      <label class="cambio-campo-et" for="swapIndirizzo_${n}">${esc(t.indirizzoTit)}</label>
      ${errore}
      <div class="cambio-campo-riga">
        <input class="swap-indirizzo" id="swapIndirizzo_${n}" type="text" autocomplete="off"
          spellcheck="false" placeholder="bc1…" inputmode="text" value="${esc(swapIndirizziScritti[n] || '')}">
        <button class="cambio-ico" type="button" data-swap="incolla" data-ordine="${n}" aria-label="${esc(t.incolla)}" title="${esc(t.incolla)}">${swapIcona('incolla')}</button>
        ${swapQrPossibile() ? `<button class="cambio-ico" type="button" data-swap="qr" data-ordine="${n}" aria-label="${esc(t.qr)}" title="${esc(t.qr)}">${swapIcona('qr')}</button>` : ''}
      </div>
    </div>`;
}
/* (tappa 3) IL CAMPO DELLA RICHIESTA LIGHTNING, al posto dell'indirizzo
   nella strada bitcoin → Lightning: la crea il suo wallet per la cifra
   scritta, e qui si incolla. La riga che dice di quanti sats crearla
   resta: e' un gesto nuovo, e senza la cifra giusta il cambio non parte */
const swapFattureScritte = {};
function campoFatturaSwap(n, errore){
  const t = t3();
  return `<div class="swap-campo">
      <label class="cambio-campo-et" for="swapFattura_${n}">${esc(t.fatturaTit)}</label>
      <div class="hint" id="swapFatturaSpiega_${n}">${esc(swapCambioSpiega(swapCambioDovuto()))}</div>
      ${errore}
      <div class="cambio-campo-riga">
        <input class="swap-indirizzo" id="swapFattura_${n}" type="text" autocomplete="off"
          spellcheck="false" placeholder="lnbc…" value="${esc(swapFattureScritte[n] || '')}">
        <button class="cambio-ico" type="button" data-swap="incolla-fattura" data-ordine="${n}" aria-label="${esc(t.incolla)}" title="${esc(t.incolla)}">${swapIcona('incolla')}</button>
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
    /* LE 12 PAROLE, UNA VOLTA SOLA E CON CALMA, e dal 29 ott 2026 (cantiere
       parole-uniche) SOLO dove nessuna copia fuori da qui le ridà: a cosa
       servono (in due righe: 29 ott 2026, parole-corte), le due regole. Poi le
       parole del wallet di Barattolo, la spunta e «Continua», che fa
       partire tutto da solo. */
    const testo = swapParoleOnchain();
    const parole = testo ? testo.split(' ') : [];
    return `<div class="swap-prev swap-prima-volta">
      <h4 class="cambio-tit">${swapIcona('chiave')}${esc(t.paroleTit)}</h4>
      <p class="swap-calma">${esc(t.paroleSpiega)}</p>
      <ol class="swap-regole">${t.paroleRegole.map(r => `<li>${esc(r)}</li>`).join('')}</ol>
      ${errore}
      <ol class="swap-parole">${parole.map(p => `<li>${esc(p)}</li>`).join('')}</ol>
      <label class="swap-spunta"><input type="checkbox" id="swapSpunta_${n}"> ${esc(t.paroleSpunta)}</label>
      <button class="btn orange" type="button" data-swap="parole-fatte" data-ordine="${n}">${esc(t.paroleFatto)}</button>
    </div>`;
  }
  if (passo === 'creo') return `<div class="swap-prev">
      <h4 class="cambio-tit">${swapIcona(n === 0 ? 'gira' : 'btc')}${esc(n === 0 ? t.cambio : t.tuoSwap)}</h4>
      ${passiSwap(0, swapStradaDi(n) === 'btc-ln' ? {tipo: 'sub'} : null)}
      <div class="swap-stato" role="status">${esc(t.creo(nome))}</div>
    </div>`;
  if (swapStradaDi(n) === 'btc-ln') return pannelloPreventivoSwap(o, campoFatturaSwap(n, errore));
  return pannelloPreventivoSwap(o, campoIndirizzoSwap(n, errore));
}
/* I TRE PALLINI (27 ott 2026): quanti passi sono stati raggiunti fra
   «Pagato», «In arrivo» e «Arrivato»; -1 quando lo swap non va avanti
   (scaduto, non riuscito, rifiutato, speso da altri) e parla la frase
   da sola */
function swapTappa(rec){
  const fase = swapFase(rec);
  /* (tappa 3) il submarine: mandati -> confermati -> pagato */
  if (swapESub(rec)) {
    if (rec.spesoDa || ['scaduto', 'fallito', 'ripreso', 'ignoto'].includes(fase)) return -1;
    return fase === 'fatto' || fase === 'pagata' ? 3 : fase === 'confermato' ? 2
         : fase === 'bloccato' ? 1 : 0;
  }
  if (rec.spesoDa || ['scaduto', 'fallito', 'ripreso'].includes(fase)) return -1;
  if ((rec.ritiro && rec.ritiro.concluso) || fase === 'fatto') return 3;
  if ((rec.ritiro && rec.ritiro.txid) || SWAP_FASI_RITIRO.has(fase)) return 2;
  if (fase !== 'creato' || ['fallito', 'rifiutato'].includes(rec.pagamento)) return -1;
  return ['in_volo', 'pagato'].includes(rec.pagamento) ? 1 : 0;
}
function passiSwap(quanti, rec){
  if (quanti < 0) return '';
  const t = t3();
  const passi = swapESub(rec) ? t.passiSub : t.passi;
  return `<ol class="swap-passi" aria-label="${esc(t.passiEt)}">${passi.map((p, i) =>
    `<li class="${i < quanti ? 'fatto' : i === quanti ? 'ora' : ''}"${i === quanti ? ' aria-current="step"' : ''}>${esc(p)}</li>`).join('')}</ol>`;
}
/* (tappa 3) il submarine fallito coi bitcoin gia' mandati aspetta un
   indirizzo dove rimandarli; senza bitcoin mandati non c'e' niente da fare */
function swapDaRimborsare(rec){
  return swapESub(rec) && !!rec.bloccato && !(rec.rimborso && rec.rimborso.txid)
    && ['fallito', 'scaduto'].includes(swapFase(rec));
}
function frasestatoSwap(rec){
  const t = t3();
  if (swapESub(rec)) {
    const fase = swapFase(rec), n = swapNomeFornitore(swapDiChi(rec));
    if (rec.spesoDa) return t.spesoAltri(n);
    if (fase === 'ripreso') return t.subRipreso(swapCorto(rec.rimborso.txid, 8));
    if (fase === 'creato') return rec.onchain ? t.subDaOrdine(n) : t.mandaTu(fmt(rec.mandi || rec.onchainAmount || 0), n);
    if (fase === 'bloccato') return t.subBloccato;
    if (fase === 'confermato') return t.subConfermato(n);
    if (fase === 'pagata') return t.subPagata;
    if (fase === 'fatto') return t.subFatto;
    if (fase === 'fallito') return rec.aspettaScadenza ? t.subPresto : t.subFallito;
    if (fase === 'scaduto') return !rec.bloccato ? t.subScadutoNiente : rec.aspettaScadenza ? t.subPresto : t.subScaduto;
    return t.statoIgnoto;
  }
  /* (20 ott 2026, swap-spesa) la spesa del lockup letta dalla rete */
  if (rec.ritiro && rec.ritiro.concluso)
    return t.concluso(fmt(rec.ritiro.sats || rec.ricevi || 0), swapCorto(rec.ritiro.txid, 8));
  if (rec.spesoDa) return t.spesoAltri(swapNomeFornitore(swapDiChi(rec)));
  if (rec.ritiro && rec.ritiro.txid && swapFase(rec) !== 'fatto')
    return t.ritirato(swapCorto(rec.ritiro.txid, 8));
  /* (cambio-libero) nel cambio la fattura la paga lui: le frasi sono sue */
  if (swapECambio(rec)) {
    const fase = swapFase(rec), n = swapNomeFornitore(swapDiChi(rec));
    if (fase === 'creato') return t.pagaTu(n);
    if (fase === 'scaduto') return t.cambioScaduto;
    if (fase === 'fallito') return t.cambioFallito;
    if (fase === 'ripreso') return t.cambioRipreso(n);
  }
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
/* LA FATTURA DA PAGARE (cambio-libero): QR, «Copia» e «Apri nel wallet»,
   finche' il fornitore non vede il pagamento. Il QR lo disegna la pagina
   dopo il ridisegno (`disegnaQr`), come nel foglio di pagamento. */
function fatturaCambio(rec){
  const t = t3();
  if (!swapECambio(rec) || swapFase(rec) !== 'creato' || !rec.invoice) return '';
  let fino = '';
  try {
    const b = typeof leggiBolt11 === 'function' ? leggiBolt11(rec.invoice) : null;
    if (b && b.scade) fino = new Date(b.scade * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  } catch(e){ fino = ''; }
  return `<div class="swap-fattura">
    <div class="qr swap-qr-fattura" id="swapCambioQr" aria-label="QR"></div>
    <div class="swap-attrezzi">
      <button class="btn ghost" type="button" data-swap="cambio-copia" data-id="${esc(rec.id)}">${swapIcona('copia')}${esc(t.copia)}</button>
      <a class="btn orange" id="swapCambioWallet" href="lightning:${esc(rec.invoice)}">${swapIcona('ln')}${esc(t.apriWallet)}</a>
    </div>
    ${fino ? `<div class="hint">${esc(t.valeFino(fino))}</div>` : ''}
  </div>`;
}
/* (tappa 3) I BITCOIN DA MANDARE: il QR del link bitcoin: (lo disegna la
   pagina), l'indirizzo in chiaro con «Copia», «Apri nel wallet» (il link
   bitcoin: nudo: `portaWallet` e' solo per Lightning) */
function bitcoinDaMandare(rec){
  const t = t3();
  /* (onchain-verso-lightning) il cambio d'una vendita on-chain non si
     paga da qui: i bitcoin li manda il deposito di garanzia */
  if (!swapESub(rec) || rec.onchain || swapFase(rec) !== 'creato' || !rec.lockupAddress) return '';
  const link = rec.bip21 || `bitcoin:${rec.lockupAddress}?amount=${(Number(rec.mandi || rec.onchainAmount) / 1e8).toFixed(8)}`;
  return `<div class="swap-fattura">
    <div class="qr swap-qr-fattura" id="swapCambioQr" aria-label="QR"></div>
    <div class="mono swap-indirizzo-chiaro">${esc(rec.lockupAddress)}</div>
    <div class="swap-attrezzi">
      <button class="btn ghost" type="button" data-swap="cambio-copia-indirizzo" data-id="${esc(rec.id)}">${swapIcona('copia')}${esc(t.copiaIndirizzo)}</button>
      <a class="btn orange" id="swapCambioWallet" href="${esc(link)}">${swapIcona('btc')}${esc(t.apriWallet)}</a>
    </div>
  </div>`;
}
function cartaSwap(rec){
  const t = t3();
  return `<div class="swap-prev swap-carta" data-swap-id="${esc(rec.id)}">
    <h4 class="cambio-tit">${swapECambio(rec) ? swapIcona('gira') + esc(t.cambio) : swapIcona('btc') + esc(t.tuoSwap)}</h4>
    ${passiSwap(swapTappa(rec), rec)}
    <div class="swap-stato" role="status">${esc(frasestatoSwap(rec))}</div>
    ${fatturaCambio(rec)}
    ${bitcoinDaMandare(rec)}
    ${rec.ricevi && rec.indirizzo ? `<div class="hint">${esc(t.ricevi(fmt(rec.ricevi)))} <span class="mono">${esc(swapCorto(rec.indirizzo, 8))}</span></div>` : ''}
    ${rec.errore && !rec.spesoDa ? `<div class="hint">${esc(t.ritiroErrore)}</div>` : ''}
    <div class="swap-da">${esc(t.eseguitoDa(swapNomeFornitore(swapDiChi(rec))))}</div>
  </div>`;
}

/* ─── 6. LE AZIONI ──────────────────────────────────────────────────── */
/* «Conferma» del preventivo: l'indirizzo prima (si guarda in casa, senza
   rete), poi si ricontrollano le tariffe del fornitore scelto con
   l'impronta di quelle mostrate (la tappa 2); se reggono, la chiave del
   wallet di Barattolo (le parole solo dove non hanno copia), e lo swap
   parte subito */
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
/* (tappa 3) la richiesta Lightning scritta nel campo, pulita; '' se manca */
function swapFatturaScritta(n){
  const campo = el(`swapFattura_${n}`);
  if (campo) swapFattureScritte[n] = String(campo.value || '');
  return String(swapFattureScritte[n] || '').trim().replace(/^lightning:/i, '').trim();
}
/* il no del giudice della richiesta, nelle parole dell'utente */
function swapFatturaPerche(perche){
  const t = t3();
  return perche === 'importo' ? t.fatturaImporto(fmt(swapCambioDovuto()))
       : perche === 'rete' ? t.fatturaRete : perche === 'scaduta' ? t.fatturaScaduta : t.fatturaNo;
}
async function swapAvantiDentro(n){
  delete swapErrori[n];
  const t = t3();
  const prima = swapFornitore(swapScelto(n));
  if (swapStradaDi(n) === 'btc-ln') {
    /* la strada rovesciata: al posto dell'indirizzo, la richiesta
       Lightning del suo wallet, per la cifra scritta */
    const fattura = swapFatturaScritta(n);
    if (!fattura) { swapErrori[n] = t.fatturaManca; return ridisegnaIncassoSwap(); }
    swapFattureScritte[n] = fattura;
    const perche = prima && prima.fatturaValida ? prima.fatturaValida(fattura, swapCambioDovuto()) : 'fattura';
    if (perche) { swapErrori[n] = swapFatturaPerche(perche); return ridisegnaIncassoSwap(); }
  } else {
    const campo = el(`swapIndirizzo_${n}`);
    if (campo) swapIndirizziScritti[n] = String(campo.value || '');
    const indirizzo = swapEstraiIndirizzo(swapIndirizziScritti[n]);
    if (!indirizzo) { swapErrori[n] = t.indirizzoManca; return ridisegnaIncassoSwap(); }
    swapIndirizziScritti[n] = indirizzo;
    if (prima) {
      let valido;
      try { valido = await prima.indirizzoValido(indirizzo); }
      catch(e){ swapErrori[n] = swapNonRisponde(n, prima.nome); return ridisegnaIncassoSwap(); }
      if (!valido) { swapErrori[n] = t.indirizzoNo; return ridisegnaIncassoSwap(); }
    }
  }
  await swapInstradaPreventivo(n, true);
  const p = preventiviSwap[n] || {};
  if (!p.dati || !p.dati.ok || p.nota === 'cambiata') return;
  if (!swapFornitore(swapScelto(n))) return;
  /* (parole-uniche) la chiave e' quella del wallet di Barattolo: si
     ritrova o nasce qui, e le parole si mostrano solo dove non hanno
     nessuna copia fuori da questo dispositivo */
  let seme;
  try { seme = await swapSemePronto(); }
  catch(e){ swapErrori[n] = t.semeNo; return ridisegnaIncassoSwap(); }
  if (seme.mostrare) { swapPassi[n] = 'parole'; return ridisegnaIncassoSwap(); }
  return swapCreaDentro(n);
}
/* «Continua» delle parole: segnate come copiate, lo swap parte da solo
   con l'indirizzo gia' messo (niente terzo passo da toccare) */
function swapParoleFatte(n){
  haptic();
  if (swapInCorso.has(n) || swapDiOrdine(n)) return;
  const spunta = el(`swapSpunta_${n}`);
  if (!spunta || !spunta.checked) { swapErrori[n] = t3().paroleSpuntaPrima; return ridisegnaIncassoSwap(); }
  if (!swapParoleOnchain()) return;
  const c = swapStatoSeme();
  c.copiata = true;
  if (!swapScrivi(swapCasaOnchain(), c)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
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
  const sub = swapStradaDi(n) === 'btc-ln';
  const indirizzo = sub ? '' : swapEstraiIndirizzo(swapIndirizziScritti[n]);
  const fattura = sub ? swapFatturaScritta(n) : '';
  const p = ((preventiviSwap[n] || {}).dati) || {};
  const fid = swapScelto(n), f = swapFornitore(fid);
  if (!f) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  if (sub) {
    const perche = !fattura ? 'manca' : (f.fatturaValida ? f.fatturaValida(fattura, swapCambioDovuto()) : 'fattura');
    if (perche) { swapPassi[n] = 'preventivo'; swapErrori[n] = perche === 'manca' ? t.fatturaManca : swapFatturaPerche(perche); return ridisegnaIncassoSwap(); }
  } else {
    let valido;
    try { valido = !!indirizzo && await f.indirizzoValido(indirizzo); }
    catch(e){ swapPassi[n] = 'preventivo'; swapErrori[n] = swapNonRisponde(n, f.nome); return ridisegnaIncassoSwap(); }
    if (!valido) { swapPassi[n] = 'preventivo'; swapErrori[n] = indirizzo ? t.indirizzoNo : t.indirizzoManca; return ridisegnaIncassoSwap(); }
  }
  if (!p.ok || !p.hash) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  /* (parole-uniche) le parole del wallet di Barattolo, gia' pronte
     (`swapSemePronto` in «Conferma»): senza, o non ancora copiate dove
     non hanno copia, non nasce niente */
  const parole = swapParoleOnchain();
  if (!parole) { swapPassi[n] = 'preventivo'; swapErrori[n] = t.semeNo; return ridisegnaIncassoSwap(); }
  if (swapSemeDaMostrare(parole)) { swapPassi[n] = 'parole'; return ridisegnaIncassoSwap(); }
  /* L'INDICE SI PRENOTA PRIMA DI CHIEDERE: se il telefono si spegne a meta',
     al giro dopo si usa il successivo, mai lo stesso */
  const indice = swapPrenotaIndice();
  if (indice < 0) { swapPassi[n] = 'preventivo'; swapErrori[n] = t.nienteCasa; return ridisegnaIncassoSwap(); }
  swapPassi[n] = 'creo';
  delete swapErrori[n];
  ridisegnaIncassoSwap();
  /* (cambio-libero) IL BIGLIETTO, prima di chiedere lo swap: il server
     conta i cambi del giorno. Un no si dice col suo perche' e non parte
     niente (l'indice prenotato resta bruciato: mai un segreto riusato) */
  let biglietto = null;
  if (n === 0) {
    try { biglietto = await chiediBigliettoCambio({direzione: swapCambioStrada, sats: swapCambioDovuto(), fornitore: fid, hash: p.hash}); }
    catch(e){ biglietto = null; }
    if (!biglietto || !biglietto.ok) {
      swapPassi[n] = 'preventivo';
      swapErrori[n] = biglietto && biglietto.motivo === 'tetto_giorno'
        ? t.tettoGiorno(swapCambioLeve().al_giorno || 0) : t.cambioNonRisponde('Barattolo');
      return ridisegnaIncassoSwap();
    }
  }
  let nuovo;
  try {
    nuovo = sub ? await f.creaSub({parole: parole, indice: indice, preventivo: p, fattura: fattura})
                : await f.crea({parole: parole, indice: indice, preventivo: p, indirizzo: indirizzo});
  }
  catch(e){
    if (biglietto) { try { await liberaBigliettoCambio(biglietto.id); } catch(e2){} }
    if (e && e.tipo === 'mente') return swapRipiega(n, f);
    swapPassi[n] = 'preventivo';
    swapErrori[n] = swapNonRisponde(n, f.nome);
    return ridisegnaIncassoSwap();
  }
  const rec = Object.assign(nuovo, {fornitore: fid, ordine: n, indice: indice, seme: 'onchain',
    indirizzo: indirizzo, creato: Date.now(), pagamento: ''});
  if (biglietto) rec.cambio = Number(biglietto.id) || 0;
  swapSalvaRecord(rec);
  delete swapPassi[n];
  /* (grafica-cambio) nato il cambio, il riquadro di dopo riparte pulito:
     niente cifre, indirizzo o richiesta del cambio di prima (un indirizzo
     bitcoin riusato e' una cattiva abitudine) */
  if (n === 0) {
    swapCambioPulisci();
    swapCambioScritta = '';
    delete swapIndirizziScritti[0];
    delete swapFattureScritte[0];
  }
  ridisegnaIncassoSwap();
  if (n === 0) {
    /* il server sa che lo swap c'e' (le sole parti pubbliche): se non
       risponde, il biglietto resta «chiesto» e conta lo stesso per oggi */
    try { await natoCambioAlServer(rec.cambio, rec); } catch(e){}
  } else await swapPaga(rec);
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

/* ─── 6c. IL CAMBIO DI UNA VENDITA ON-CHAIN (28 ott 2026, cantiere
   onchain-verso-lightning, richiesta di Alan e Andrea) ─────────────────
   Chi ha venduto con un pagamento on-chain vuole i sats in Lightning: i
   bitcoin non li manda il suo wallet ma il deposito di garanzia 2-di-3,
   con la prima firma di chi vende e la seconda di chi compra. Qui nasce
   SOLO il cambio — la chiave di rimborso dal seme dell'on-chain (un
   indice nuovo, prenotato prima di chiedere), la richiesta Lightning letta, la
   risposta del fornitore verificata (`creaSub`) — e il record entra
   nella lista con `onchain` (il numero dell'ordine on-chain), sorvegliato
   come gli altri: a fattura pagata la meta' del ritiro a due, a cambio
   fallito coi bitcoin mandati il rimborso, da solo, al `rimborso`. Le firme
   e il server li fa la pagina (`onchainCambioConferma`): qui niente fetch.
   Alza con `.tipo`: 'seme' (niente chiave on-chain qui), 'fattura' (il perche'
   in `.perche`), 'casa', 'giu', 'mente'. */
function swapNoOnchain(tipo){ const e = new Error(tipo); e.tipo = tipo; return e; }
/* LO STESSO SEME DEL 2-DI-3 (29 ott 2026, Andrea: «lo stesso wallet
   autogenerato per l'onchain è lo stesso che in caso di problemi deve
   essere utilizzato nello swap»). Il cambio di una vendita on-chain non
   ha piu' 12 parole sue: la chiave di rimborso nasce dalle parole
   dell'on-chain (che hanno gia' le loro copie, Telegram e Nostr), sulla
   strada di SATS Routing (m/44/0/0/0/i, lontana da quella del 2-di-3), e
   se il cambio fallisce i bitcoin tornano DA SOLI a un indirizzo dello
   stesso seme (`rimborso`, lo sceglie la pagina): nessun passo in piu'
   per chi vende, nessun indirizzo da scrivere. Il contatore delle chiavi
   e' suo (`swapCasaOnchain`), e riparte mai sotto l'ultimo usato. Dal 29
   ott 2026 (parole-uniche) lo stesso seme e lo stesso contatore valgono
   per ogni cambio: vedi «UNA CHIAVE SOLA», in cima. */
/* le parole di uno swap: quelle del fornitore, o quelle dell'on-chain */
function swapParoleDi(rec){
  if (rec && rec.seme === 'onchain') {
    const parole = swapParoleOnchain();
    return parole ? {parole: parole} : null;
  }
  return swapCassetto(swapDiChi(rec));
}
async function swapCreaPerOnchain({ordine, onchain, fattura, preventivo, rimborso}){
  const f = swapFornitore(preventivo && preventivo.fornitore);
  if (!f || !f.creaSub) throw swapNoOnchain('giu');
  const perche = f.fatturaValida(fattura, Number(preventivo.ricevi));
  if (perche) { const e = swapNoOnchain('fattura'); e.perche = perche; throw e; }
  const parole = swapParoleOnchain();
  if (!parole) throw swapNoOnchain('seme');
  if (!rimborso) throw swapNoOnchain('seme');
  /* L'INDICE SI PRENOTA PRIMA DI CHIEDERE, come per gli altri: mai sotto
     uno gia' in lista (un telefono che ha perso il contatore non riusa) */
  const indice = swapPrenotaIndice();
  if (indice < 0) throw swapNoOnchain('casa');
  const nuovo = await f.creaSub({parole: parole, indice: indice, preventivo: preventivo, fattura: fattura});
  const rec = Object.assign(nuovo, {fornitore: f.id, ordine: Number(ordine) || null,
    onchain: Number(onchain), indice: indice, seme: 'onchain', indirizzo: String(rimborso),
    creato: Date.now(), pagamento: ''});
  swapSalvaRecord(rec);
  swapSorveglia();
  return rec;
}

/* ─── 7. LA SORVEGLIANZA E IL RITIRO ──────────────────────────────────
   Ogni 5 secondi, finche' c'e' uno swap non finito, si chiede al suo
   fornitore a che punto e'; quando i bitcoin sono bloccati si ritira.
   All'apertura dell'app si riprende da qui (`swapRiprendi`): chiudere
   l'app a meta' non perde niente. */
let swapTimer = null;
const swapRitirando = new Set();
/* (tappa 3) un submarine fallito coi bitcoin mandati resta aperto
   finche' l'utente non dice dove rimandarli e il rimborso non parte */
function swapAperti(){
  return swapLista().filter(r => !SWAP_FASI_FINALI.has(swapFase(r)) || (swapDaRimborsare(r) && r.indirizzo));
}
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
      /* (tappa 3) i bitcoin del submarine sono stati mandati: da qui in
         poi un fallimento vuole il rimborso */
      if (swapESub(rec) && ['transaction.mempool', 'transaction.confirmed', 'invoice.pending',
          'invoice.paid', 'transaction.claimed', 'transaction.lockupFailed'].includes(s)) rec.bloccato = true;
      swapSalvaRecord(rec);
      swapRidisegnaDove(rec);
    }
    if (swapESub(rec)) { await swapGiroSub(rec, f); continue; }
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
/* (tappa 3) IL GIRO DEL SUBMARINE: a fattura pagata la nostra meta' per
   il ritiro a due del fornitore (una volta); fallito coi bitcoin mandati
   e con l'indirizzo scritto, il rimborso */
async function swapGiroSub(rec, f){
  const fase = swapFase(rec);
  if (fase === 'pagata' && !rec.ritiro && f.aiutaRitiro) {
    const c = swapParoleDi(rec);
    try {
      if (!c || !c.parole) throw new Error('parole assenti');
      const fatto = await f.aiutaRitiro(rec, c.parole);
      rec.ritiro = {cooperativo: !!fatto.cooperativo, quando: Date.now()};
      delete rec.errore;
      swapSalvaRecord(rec);
      swapRidisegnaDove(rec);
    } catch(e){
      /* il fornitore ritira lo stesso dallo script: non e' un problema nostro */
      rec.errore = String((e && e.message) || e).slice(0, 120);
      swapSalvaRecord(rec);
    }
    return;
  }
  if (swapDaRimborsare(rec) && rec.indirizzo) await swapRimborsa(rec);
}
async function swapRimborsa(rec){
  if (swapRitirando.has(rec.id) || !rec.indirizzo) return;
  swapRitirando.add(rec.id);
  try {
    const fid = swapDiChi(rec), f = swapFornitore(fid);
    const c = swapParoleDi(rec);
    if (!f || !f.rimborsa) throw new Error('fornitore assente');
    if (!c || !c.parole) throw new Error('parole assenti');
    const fatto = await f.rimborsa(rec, c.parole);
    rec.rimborso = {txid: fatto.txid, cooperativo: fatto.cooperativo, quando: Date.now()};
    delete rec.errore;
    delete rec.spesoDa;
    delete rec.aspettaScadenza;
  } catch(e){
    rec.errore = String((e && e.message) || e).slice(0, 120);
    rec.aspettaScadenza = !!(e && e.tipo === 'presto');
    if (e && e.tipo === 'speso') rec.spesoDa = String(e.txid || '');
    else delete rec.spesoDa;
  } finally {
    swapRitirando.delete(rec.id);
    swapSalvaRecord(rec);
    swapRidisegnaDove(rec);
  }
}
async function swapRitira(rec){
  if (swapRitirando.has(rec.id) || !rec.indirizzo) return;
  swapRitirando.add(rec.id);
  try {
    const fid = swapDiChi(rec), f = swapFornitore(fid);
    /* (parole-uniche) le parole del SUO record: quelle del wallet di
       Barattolo, o il cassetto del fornitore per i cambi di prima */
    const c = swapParoleDi(rec);
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
  if (swapECambio(rec)) renderSwapCambio();
  if (currentOrder && Number(currentOrder.id) === Number(rec.ordine)
      && el('payoutIncasso')) ridisegnaIncassoSwap();
  if (el('view-swap') && el('view-swap').classList.contains('active')) renderSwapTelefono();
}

/* ─── 7b. IL CAMBIO LIBERO: il riquadro in cima alla pagina ─────────────
   (28 ott 2026, cantiere grafica-cambio, piano approvato da Andrea con due
   modifiche) SEMPRE APERTO, sul modello della pagina di SATS Routing: due
   riquadri, quel che MANDI sopra e quel che RICEVI sotto, il tondo in
   mezzo che inverte la strada, il costo in una riga, il campo e un solo
   «Conferma»; sotto, i tetti in piccolo e le tre tesserine. Niente piu'
   «🔁 Cambia», «Chiudi» e «Vedi quanto ricevi»: la cifra dell'altro
   riquadro si fa da sola, quando chi scrive SMETTE di scrivere (modifica 1
   di Andrea: mai un preventivo a ogni tasto, `SWAP_CAMBIO_ATTESA_MS`).
   Dove sta il campo che si scrive: nella strada verso l'indirizzo la
   cifra e' quella che si CAMBIA (sopra), in quella verso Lightning quella
   che si RICEVE (sotto), come vuole il conto del server (`dovuto`).
   Poi, alla conferma, il pannello dell'«ordine 0» (le parole la prima
   volta, obbligatorie come il 27 ott: modifica 2; la nascita) e la carta
   col QR da pagare. */
let swapCambioScritta = '';
let swapCambioTimer = null;
const SWAP_CAMBIO_ATTESA_MS = 800;
/* (28 ott 2026, cantiere cambio-due-riquadri, Andrea: «voglio che sia
   scrivibile in tutti e due i riquadri») si scrive in «Mandi» o in
   «Ricevi», e l'altro si fa da solo. `swapCambioLato` e' dove si e'
   scritto; il server fa il conto al contrario quando non e' il lato del
   suo `dovuto` (mai sotto la cifra scritta: un sat in piu', mai in meno).
   L'UNITA' (Andrea: «diamo la possibilita di selezionare sats o btc»,
   «senza scritte solo selettore»; dal cantiere unita-tendine la ₿ per i
   BTC e il segno dei sats come su SATS Routing):
   un selettore sotto i riquadri, la scelta resta sul telefono. In BTC le
   cifre hanno otto decimali, esatte al sat: niente arrotondamenti. */
let swapCambioLato = 'mandi';
/* la tendina aperta: 'mandi', 'ricevi' o nessuna (unita-tendine) */
let swapCambioTendina = null;
const SWAP_CAMBIO_UNITA_CASA = 'barattolo_cambio_unita';
let swapCambioUnita = (() => {
  try { return localStorage.getItem(SWAP_CAMBIO_UNITA_CASA) === 'btc' ? 'btc' : 'sats'; }
  catch(e){ return 'sats'; }
})();
function swapCambioLeve(){ return (swapLeve && swapLeve.cambio) || {}; }
function swapCambioAcceso(){ return !!swapCambioLeve().attivo; }
/* il lato del `dovuto` del server: verso l'indirizzo quel che mandi in
   Lightning, verso Lightning quel che ricevi */
function swapCambioLatoDovuto(){ return swapCambioStrada === 'btc-ln' ? 'ricevi' : 'mandi'; }
/* una cifra scritta, in sats interi (0 se non e' buona). In sats contano
   solo le cifre (i punti e gli spazi delle migliaia si buttano); in BTC
   la virgola o il punto sono i decimali, al piu' otto */
function swapCambioLeggi(testo, unita){
  const s = String(testo || '').replace(/\s/g, '');
  if (unita !== 'btc') {
    const n = parseInt(s.replace(/[^0-9]/g, ''), 10);
    return n > 0 ? n : 0;
  }
  const m = /^(\d*)(?:[.,](\d*))?$/.exec(s);
  if (!m || (!m[1] && !m[2])) return 0;
  const n = Number(m[1] || '0') * 100000000 + Number(((m[2] || '') + '00000000').slice(0, 8));
  return Number.isSafeInteger(n) && n > 0 ? n : 0;
}
/* sats → il numero nell'unita' scelta (senza il nome dell'unita') */
function swapCambioNum(sats){
  const n = Math.max(0, Math.round(Number(sats) || 0));
  if (swapCambioUnita !== 'btc') return fmt(n);
  return `${Math.floor(n / 100000000)},${String(n % 100000000).padStart(8, '0')}`;
}
function swapCambioUnitaNome(){ return swapCambioUnita === 'btc' ? 'BTC' : 'sats'; }
function swapCambioCifra(){ return swapCambioLeggi(swapCambioScritta, swapCambioUnita); }
/* IL PREVENTIVO E' DI ADESSO? Due risposte possono arrivare al contrario
   dell'ordine in cui sono partite (chi scrive in fretta): si mostra solo
   quella della cifra, del lato e della strada scritti ora. Il server
   ripete la cifra scritta in `scritta`, il lato in `lato` e la strada in
   `direzione`; una risposta senza (la rotta spenta, 403) e' sempre di
   adesso. */
function swapCambioDiAdesso(d){
  if (!d) return false;
  if (!Object.prototype.hasOwnProperty.call(d, 'dovuto')) return true;
  if (d.direzione && d.direzione !== swapCambioStrada) return false;
  if (Object.prototype.hasOwnProperty.call(d, 'scritta'))
    return Number(d.scritta) === swapCambioCifra() && d.lato === swapCambioLato;
  return Number(d.dovuto) === swapCambioCifra() && swapCambioLato === swapCambioLatoDovuto();
}
/* IL DOVUTO DEL CAMBIO, quello con cui nasce: la cifra scritta se e' dal
   lato del dovuto, sennò quello del conto al contrario (se e' di adesso) */
function swapCambioDovuto(){
  if (swapCambioLato === swapCambioLatoDovuto()) return swapCambioCifra();
  const p = preventiviSwap[0] || {};
  const d = p.dati && swapCambioDiAdesso(p.dati) ? p.dati : null;
  return d && d.ok ? Number(d.dovuto) || 0 : 0;
}
function swapCambioStrade(){
  const l = swapCambioLeve();
  const strade = Array.isArray(l.strade) && l.strade.length ? l.strade : [SWAP_STRADA];
  if (!strade.includes(swapCambioStrada)) swapCambioStrada = strade[0];
  return strade;
}
/* i pezzi che cambiano mentre si scrive: la cifra dell'altro riquadro, la
   riga del costo, l'avviso e «Conferma». Il campo della cifra NON si
   ridisegna mai mentre ci si scrive dentro (la tastiera del telefono si
   chiuderebbe a ogni risposta): vedi `renderSwapCambio`. */
function swapCambioPezzi(){
  const t = t3(), cifra = swapCambioCifra(), sub = swapCambioStrada === 'btc-ln';
  const p = preventiviSwap[0] || {};
  const d = p.dati && swapCambioDiAdesso(p.dati) ? p.dati : null;
  const attesa = !!cifra && (!d || p.stato === 'carico' || !!swapCambioTimer);
  const pronto = !!d && d.ok && !attesa;
  /* l'altro riquadro: la cifra del conto, «…» mentre si aspetta */
  const altraSats = pronto ? Number(swapCambioLato === 'mandi' ? d.ricevi : (sub ? d.mandi : d.dovuto)) || 0 : 0;
  const altra = pronto ? swapCambioNum(altraSats) : '';
  /* (cambio-euro) sotto ogni cifra il suo controvalore: quella scritta
     subito, a ogni tasto; quella del conto quando arriva */
  const euroMio = euroSwap(cifra), euroAltra = euroSwap(altraSats);
  const avviso = swapErrori[0] || (d && !d.ok && !attesa ? rifiutoSwap(0, d) : '');
  const dovuto = swapCambioDovuto();
  return {
    altra: altra,
    vuota: attesa ? '…' : '0',
    costo: pronto ? notaSwap(p, d) + costoSwap(0, d) : '',
    avviso: avviso ? `<div class="swap-rifiuto" role="status">${esc(avviso)}</div>` : '',
    pronto: pronto,
    euroMandi: swapCambioLato === 'mandi' ? euroMio : euroAltra,
    euroRicevi: swapCambioLato === 'mandi' ? euroAltra : euroMio,
    spiega: sub ? swapCambioSpiega(dovuto) : ''};
}
/* IL CONTROVALORE IN EURO (28 ott 2026, cantiere cambio-euro, Andrea:
   «voglio vedere il controvalore in euro sotto alla cifra in sats o btc
   proprio come su satsrouting»): «≈ 0,81 €», piccolo, sotto la cifra di
   ogni riquadro. Il cambio e' quello di tutta l'app (`eurPerSat`, dal
   nostro server); senza un cambio VERO in mano (`cambioVivo` falso) la
   riga resta vuota: mai un numero inventato, il patto di sempre */
function euroSwap(sats){
  const n = Number(sats) || 0;
  if (!(n > 0) || typeof cambioVivo === 'undefined' || !cambioVivo
      || typeof eurPerSat === 'undefined' || typeof fmtEur !== 'function') return '';
  return `≈ ${fmtEur(n * eurPerSat)} €`;
}
/* la frase della richiesta Lightning resta in sats (i wallet chiedono
   quelli), coi BTC accanto se si e' scelto BTC */
function swapCambioSpiega(dovuto){
  const t = t3();
  return t.fatturaSpiega(dovuto ? fmt(dovuto) : '…', dovuto && swapCambioUnita === 'btc' ? swapCambioNum(dovuto) : '');
}
/* (28 ott 2026, cantiere euro-ordine, Andrea: «affianco al toggle btc
   sats aggiungi anche un piccolo tasto ... con la scritta "onion"») il
   tasto porta a Barattolo sul sito Tor. Solo se il server ha un
   indirizzo .onion, e non a chi c'e' gia' sopra */
function onionSwap(){
  return typeof onionHost === 'string' && onionHost && !(typeof suOnion === 'function' && suOnion())
    ? '<button type="button" class="cambio-onion" data-swap="cambio-onion">onion</button>' : '';
}
function renderSwapCambio(){
  const box = el('swapCambio');
  if (!box) return;
  const forma = v => { if (box.dataset) box.dataset.forma = v; };
  if (!swapCambioAcceso()) { box.innerHTML = ''; forma(''); return; }
  const vivo = swapDiOrdine(0);
  if (vivo) {
    forma('');
    box.innerHTML = cartaSwap(vivo);
    const q = el('swapCambioQr');
    if (q && typeof disegnaQr === 'function' && !swapESub(vivo))
      disegnaQr(q, ('lightning:' + String(vivo.invoice).trim()).toUpperCase(), 'Alphanumeric');
    const a = el('swapCambioWallet');
    if (a && typeof portaWallet === 'function' && !swapESub(vivo)) portaWallet(a, vivo.invoice);
    /* (tappa 3) il QR del submarine e' il link bitcoin: (byte, com'e') */
    if (q && swapESub(vivo) && typeof disegnaQr === 'function')
      disegnaQr(q, vivo.bip21 || `bitcoin:${vivo.lockupAddress}`, 'Byte');
    return;
  }
  /* dopo «Conferma»: le parole (solo dove non hanno copia), poi «Preparo il cambio…» */
  if (swapPassi[0] === 'parole' || swapPassi[0] === 'creo') {
    forma('');
    box.innerHTML = pannelloSwapTelefono({id: 0});
    return;
  }
  const t = t3(), tp = testiSwap(), l = swapCambioLeve();
  const strade = swapCambioStrade();
  const sub = swapCambioStrada === 'btc-ln';
  const pz = swapCambioPezzi();
  /* GIA' DISEGNATO, STESSA STRADA E STESSA UNITA': si aggiornano solo i
     pezzi. Il riquadro dove si scrive non si tocca mai (la tastiera) */
  const forma0 = swapCambioStrada + '/' + swapCambioUnita;
  const altra = el(swapCambioLato === 'mandi' ? 'swapCambioRicevi' : 'swapCambioMandi');
  const costo = el('swapCambioCosto'), avviso = el('swapCambioAvviso'), vai = el('swapCambioVai');
  if (box.dataset && box.dataset.forma === forma0 && altra && costo && avviso && vai) {
    altra.value = pz.altra;
    altra.placeholder = pz.vuota;
    if (costo.innerHTML !== pz.costo) costo.innerHTML = pz.costo;
    if (avviso.innerHTML !== pz.avviso) avviso.innerHTML = pz.avviso;
    vai.disabled = !pz.pronto;
    const spiega = el('swapFatturaSpiega_0');
    if (spiega && sub) spiega.textContent = pz.spiega;
    const em = el('swapCambioEuroMandi'), er = el('swapCambioEuroRicevi');
    if (em) em.textContent = pz.euroMandi;
    if (er) er.textContent = pz.euroRicevi;
    /* (30 ott 2026, cantiere onion-tardi: Andrea non vedeva il tasto)
       l'indirizzo .onion arriva con la busta della vetrina, e chi apre
       il Cambio prima di lei l'aveva gia' disegnato senza: il tasto si
       aggiunge (o si toglie) qui accanto al selettore, senza ridisegnare
       i campi */
    const u = box.querySelector ? box.querySelector('.cambio-unita') : null;
    if (u) {
      const vicino = u.nextElementSibling, ce = !!(vicino && vicino.classList.contains('cambio-onion'));
      const serve = onionSwap();
      if (serve && !ce) u.insertAdjacentHTML('afterend', serve);
      else if (!serve && ce) vicino.remove();
    }
    return;
  }
  /* i due riquadri si scrivono tutti e due: in quello dove si e' scritto
     la cifra com'e', nell'altro quella del conto */
  const campoCifra = (lato, eti) => {
    const mio = lato === swapCambioLato;
    return `<input class="cambio-cifra-campo${swapCambioUnita === 'btc' ? ' btc' : ''}" id="${lato === 'mandi' ? 'swapCambioMandi' : 'swapCambioRicevi'}" data-lato="${lato}"`
      + ` type="text" inputmode="${swapCambioUnita === 'btc' ? 'decimal' : 'numeric'}" autocomplete="off"`
      + ` placeholder="${esc(mio ? '0' : pz.vuota)}" aria-label="${esc(eti)}" value="${esc(mio ? swapCambioScritta : pz.altra)}">`
      + `<small>${swapCambioUnitaNome()}</small>`
      + `<span class="cambio-euro" id="${lato === 'mandi' ? 'swapCambioEuroMandi' : 'swapCambioEuroRicevi'}">${esc(lato === 'mandi' ? pz.euroMandi : pz.euroRicevi)}</span>`;
  };
  /* (unita-tendine) LA TENDINA della pillola: con due strade si sceglie
     la rete di quel riquadro, e l'altro si gira da solo (scegliere «BTC» in
     «Mandi» e' la strada verso Lightning). Con una strada sola, niente
     tendina: la pillola dice e basta */
  const tendina = (lato, rete) => {
    if (strade.length < 2) return '';
    const aperta = swapCambioTendina === lato;
    const voci = ['ln', 'btc'].map(r => {
      const strada = (lato === 'mandi' ? r === 'ln' : r === 'btc') ? 'ln-btc' : 'btc-ln';
      if (!strade.includes(strada)) return '';
      return `<li><button type="button" role="option" aria-selected="${r === rete}" data-swap="cambio-rete" data-strada="${strada}">`
        + `${monetinaSwap(r)}${esc(tp.reti[r])}</button></li>`;
    }).join('');
    return `<span class="cambio-tendina"><button type="button" class="cambio-pillola" data-swap="cambio-tendina" data-lato="${lato}"`
      + ` aria-haspopup="listbox" aria-expanded="${aperta}">${monetinaSwap(rete)}<b>${esc(tp.reti[rete])}</b>${swapIcona('giu')}</button>`
      + (aperta ? `<ul class="cambio-menu" role="listbox">${voci}</ul>` : '') + '</span>';
  };
  const reteSopra = sub ? 'btc' : 'ln', reteSotto = sub ? 'ln' : 'btc';
  const sopra = latoSwap(reteSopra, tp.mandiBreve, campoCifra('mandi', sub ? tp.mandiBreve : tp.voci.cambi), 'scritto con-euro', tendina('mandi', reteSopra));
  const sotto = latoSwap(reteSotto, sub ? tp.riceviBreve : tp.ricevi, campoCifra('ricevi', sub ? tp.voci.ricevi_ln : tp.ricevi), 'arriva scritto con-euro', tendina('ricevi', reteSotto));
  /* il selettore dell'unita': due tondi senza scritte, la ₿ per i BTC
     e il segno dei sats (le parole stanno solo per chi legge lo schermo) */
  const unita = ['btc', 'sats'].map(u => `<button type="button" class="cambio-unita-tasto${u === swapCambioUnita ? ' scelta' : ''}"`
    + ` data-swap="cambio-unita" data-unita="${u}" aria-pressed="${u === swapCambioUnita}" aria-label="${u === 'btc' ? 'BTC' : 'sats'}">`
    + `${swapIcona(u)}</button>`).join('');
  const onion = onionSwap();
  const altraStrada = strade.find(x => x !== swapCambioStrada);
  const gira = altraStrada
    ? `<div class="cambio-gira"><button type="button" data-swap="cambio-gira" data-strada="${esc(altraStrada)}" aria-label="${esc(t.direzioni[altraStrada] || altraStrada)}">${swapIcona('gira')}</button></div>`
    : '<div class="cambio-gira"></div>';
  const campo = sub ? campoFatturaSwap(0, '') : campoIndirizzoSwap(0, '');
  const limiti = esc(t.cifraTra(swapCambioNum(l.minimo || 0), swapCambioNum(l.massimo || 0), swapCambioUnitaNome()))
    + (l.al_giorno ? ' · ' + esc(t.oggi(l.oggi || 0, l.al_giorno)) : '');
  const tessere = t.tessere.map(([ic, testo]) =>
    `<li><span class="cambio-tessera-ico">${swapIcona(ic)}</span>${esc(testo)}</li>`).join('');
  forma(forma0);
  box.innerHTML = `<div class="swap-cambio">
    <div class="cambio-carta" role="group" aria-label="${esc(sub ? tp.titoloPrevSub : tp.titoloPrev)}">
      ${sopra}${gira}${sotto}
      <div class="cambio-unita" role="group" aria-label="${esc(t.unita)}">${unita}</div>${onion}
      <div id="swapCambioCosto">${pz.costo}</div>
    </div>
    <div id="swapCambioAvviso">${pz.avviso}</div>
    ${campo}
    <button class="btn orange cambio-vai" id="swapCambioVai" type="button" data-swap="avanti" data-ordine="0"${pz.pronto ? '' : ' disabled'}>${esc(tp.conferma)}</button>
    <div class="cambio-limiti">${limiti}</div>
    <ul class="cambio-tessere">${tessere}</ul>
  </div>`;
}
/* LA CIFRA SCRITTA: a ogni tasto si ricorda e si mostra «…» nell'altro
   riquadro; il preventivo parte solo quando si smette di scrivere */
function swapCambioScrive(valore, lato){
  if (lato === 'mandi' || lato === 'ricevi') swapCambioLato = lato;
  swapCambioScritta = String(valore || '');
  delete swapErrori[0];
  if (swapCambioTimer) clearTimeout(swapCambioTimer);
  swapCambioTimer = setTimeout(() => { swapCambioTimer = null; swapCambioCalcola(true); }, SWAP_CAMBIO_ATTESA_MS);
  renderSwapCambio();
}
/* il conto della cifra scritta. `daSolo` = dall'attesa dopo l'ultimo
   tasto: a campo vuoto non rimprovera, toglie le cifre e basta */
async function swapCambioCalcola(daSolo){
  if (!daSolo) haptic();
  const c = el(swapCambioLato === 'mandi' ? 'swapCambioMandi' : 'swapCambioRicevi');
  if (c) swapCambioScritta = String(c.value || '');
  delete swapErrori[0];
  const cifra = swapCambioCifra(), strada = swapCambioStrada, lato = swapCambioLato;
  if (!cifra) {
    delete preventiviSwap[0];
    if (!daSolo) swapErrori[0] = t3().cifraNo;
    return renderSwapCambio();
  }
  await swapInstradaPreventivo(0, false);
  /* nel frattempo ha scritto ancora, o ha girato la strada: questa
     risposta e' vecchia. Se un'attesa e' gia' in corso ci pensa lei,
     sennò si richiede subito per la cifra di adesso */
  if (cifra !== swapCambioCifra() || strada !== swapCambioStrada || lato !== swapCambioLato) {
    if (!swapCambioTimer) return swapCambioCalcola(true);
    return;
  }
  renderSwapCambio();
}
/* finito un cambio, il riquadro riparte pulito: niente cifre vecchie */
function swapCambioPulisci(){
  delete preventiviSwap[0];
  delete swapErrori[0];
  delete swapPassi[0];
  delete dettagliSwap[0];
}
async function swapCambioCopia(id, cosa){
  haptic();
  const rec = swapLista().find(r => r.id === id);
  const testo = cosa === 'indirizzo' ? (rec && rec.lockupAddress) : (rec && rec.invoice);
  if (!testo) return;
  try { await navigator.clipboard.writeText(String(testo)); toast(t3().copiata); }
  catch(e){ toast(t3().appuntiChiusi); }
}
/* (tappa 3) LA STRADA: il tondo fra i due riquadri la gira. Le cifre di
   prima non valgono piu' (erano dell'altra strada): la cifra scritta
   resta, e il conto si rifa' subito per la strada nuova */
function swapCambioScegliStrada(strada){
  haptic();
  swapCambioTendina = null;
  if (strada === swapCambioStrada) return swapCambioRidisegna();
  swapCambioStrada = strada;
  swapCambioPulisci();
  if (swapCambioTimer) { clearTimeout(swapCambioTimer); swapCambioTimer = null; }
  renderSwapCambio();
  if (swapCambioCifra()) return swapCambioCalcola(true);
}
/* la tendina si apre e si chiude: il riquadro si ridisegna intero */
function swapCambioRidisegna(){
  const box = el('swapCambio');
  if (box && box.dataset) box.dataset.forma = '';
  renderSwapCambio();
}
function swapCambioApriTendina(lato){
  haptic();
  swapCambioTendina = swapCambioTendina === lato ? null : lato;
  swapCambioRidisegna();
}
/* IL SELETTORE DELL'UNITA': la cifra scritta resta la stessa in sats, e
   si riscrive nell'unita' nuova; il conto non cambia, cambia come si legge */
function swapCambioScegliUnita(unita){
  haptic();
  unita = unita === 'btc' ? 'btc' : 'sats';
  if (unita === swapCambioUnita) return;
  const n = swapCambioCifra();
  swapCambioUnita = unita;
  swapCambioScritta = n ? swapCambioNum(n) : '';
  try { localStorage.setItem(SWAP_CAMBIO_UNITA_CASA, unita); } catch(e){}
  renderSwapCambio();
}
/* «Incolla» della richiesta Lightning: quel che arriva va nel campo
   com'e' (il giudice parla a «Conferma»), senza «lightning:» davanti */
async function swapIncollaFattura(n){
  haptic();
  let testo = null;
  try { testo = await navigator.clipboard.readText(); } catch(e){ testo = null; }
  if (testo == null) {
    toast(t3().appuntiChiusi);
    const c = el(`swapFattura_${n}`);
    if (c) try { c.focus(); } catch(e){}
    return;
  }
  swapFattureScritte[n] = String(testo || '').trim().replace(/^lightning:/i, '');
  const c = el(`swapFattura_${n}`);
  if (c) c.value = swapFattureScritte[n];
  delete swapErrori[n];
  if (Number(n) === 0) renderSwapCambio(); else ridisegnaIncassoSwap();
}

/* ─── 8. LA PAGINA «SWAP» ───────────────────────────────────────────────
   La lista di tutti gli swap.
   (28 ott 2026, cantiere grafica-cambio) Il riquadro del cambio libero
   sta FUORI da qui, in un suo posto fisso della pagina (#swapCambio): il
   ridisegno della lista, che arriva anche da solo a ogni giro della
   sorveglianza, non tocca piu' il campo della cifra mentre ci si scrive.
   La lista e' a schede (la moneta di dove arriva, la frase, tre barrette
   e la cifra).
   (29 ott 2026, cantiere parole-uniche, Alan: «vorrei nascondere le 12
   parole dalla parte dello swap, le vede dalle impostazioni non lì») La
   riga chiusa delle parole e del recupero che stava in fondo e' MORTA:
   qui resta solo la porta verso il Profilo, dove «Il wallet di
   Barattolo» le mostra a richiesta e ritrova i cambi
   (`swapBloccoProfilo`, sotto). */
function barretteSwap(rec){
  const q = swapTappa(rec);
  if (q < 0) return '';
  return `<span class="cambio-barrette" aria-hidden="true">${[0, 1, 2].map(i => `<i class="${i < q ? 'fatto' : ''}"></i>`).join('')}</span>`;
}
function renderSwapTelefono(){
  const box = el('swapTelefono');
  if (!box) return;
  const t = t3(), piu = swapPiuFornitori();
  const lista = swapLista().slice().sort((a, b) => (b.creato || 0) - (a.creato || 0));
  /* con degli swap in lista, o col cambio libero acceso, il «per ora
     nessuno» della tappa 1 tace */
  if (el('swapVuoto')) el('swapVuoto').style.display = lista.length || swapCambioAcceso() ? 'none' : '';
  const righe = lista.map(rec => `<div class="cambio-voce">
      <div class="cambio-voce-riga">
        ${swapMoneta(swapESub(rec) ? 'ln' : 'btc')}
        <span class="cambio-voce-dati">
          <b>${esc(swapECambio(rec) ? t.cambio : rec.ordine ? t.ordine(rec.ordine) : t.recuperato)}</b>
          <span>${esc(frasestatoSwap(rec))}</span>
          ${piu ? `<span class="swap-da">${esc(t.eseguitoDa(swapNomeFornitore(swapDiChi(rec))))}</span>` : ''}
          ${barretteSwap(rec)}
        </span>
        ${Number(rec.ricevi) > 0 ? `<span class="cambio-voce-cifra">${fmt(rec.ricevi)}</span>` : ''}
      </div>
      ${(!rec.indirizzo && SWAP_FASI_RITIRO.has(swapFase(rec)) && !swapESub(rec)) || (swapDaRimborsare(rec) && !rec.indirizzo) ? `
        <input class="swap-indirizzo" id="swapIndirizzoR_${esc(rec.id)}" type="text" autocomplete="off" spellcheck="false" placeholder="bc1…">
        <button class="btn ghost" type="button" data-swap="ritira-a" data-id="${esc(rec.id)}">${esc(swapESub(rec) ? t.rimborsaA : t.ritiraA)}</button>` : ''}
    </div>`).join('');
  box.innerHTML = `
    ${lista.length ? `<h3 class="cambio-sez">${esc(t.lista)}</h3>${righe}` : ''}
    <button class="btn link cambio-al-profilo" type="button" data-swap="al-profilo">${swapIcona('chiave')}${esc(t.riservaDove)}</button>`;
  renderSwapCambio();
}
/* IL PEZZO DEL CAMBIO NEL PROFILO (29 ott 2026, parole-uniche): lo mette
   la pagina dentro «Il wallet di Barattolo», sotto le parole (quelle le
   mostra lei: sono del wallet, non del cambio). Qui «Ritrova i miei
   cambi», e — solo per chi ha dei cambi nati prima, con dodici parole
   loro — quelle parole a richiesta e il recupero scrivendole. */
function swapBloccoProfilo(){
  const t = t3(), piu = swapPiuFornitori();
  const vecchi = swapFornitori().filter(f => { const c = swapCassetto(f.id); return c && c.parole; });
  const vecchie = vecchi.map(f => {
    const c = swapCassetto(f.id), viste = !!swapParoleViste[f.id];
    const elenco = viste
      ? `<ol class="swap-parole">${String(c.parole).split(' ').map(p => `<li>${esc(p)}</li>`).join('')}</ol>` : '';
    return `<h4>${esc(piu ? t.paroleDi(f.nome) : t.paroleTit)}</h4>
    <button class="btn ghost" type="button" data-swap="mostra-parole" data-fornitore="${esc(f.id)}">${esc(viste ? t.nascondi : t.mostra)}</button>${elenco}`;
  }).join('');
  const bottoni = vecchi.map(f =>
    `<button class="btn ghost" type="button" data-swap="recupera" data-fornitore="${esc(f.id)}">${esc(piu ? t.recuperaDa(f.nome) : t.recupera)}</button>`).join('');
  return `<h4>${esc(t.ritrovaTit)}</h4>
    <div class="hint">${esc(t.ritrovaSpiega)}</div>
    <button class="btn ghost" type="button" data-swap="ritrova">${esc(t.ritrova)}</button>
    <div id="swapRecuperoNota" class="hint" role="status">${esc(swapNotaRecupero.testo)}</div>
    ${vecchi.length ? `<details class="payout swap-vecchie"${vecchi.some(f => swapParoleViste[f.id]) ? ' open' : ''}>
      <summary><b>${esc(t.vecchieTit)}</b></summary>
      <div class="hint">${esc(t.vecchieSpiega)}</div>
      ${vecchie}
      <h4>${esc(t.recuperaTit)}</h4>
      <textarea id="swapRecupero" rows="3" autocomplete="off" spellcheck="false"></textarea>
      ${bottoni}
    </details>` : ''}`;
}
/* dopo un gesto sulle parole o sul recupero si ridisegnano tutt'e due i
   posti dove possono stare: la pagina «Cambio» e il Profilo */
function swapRidisegnaRiserva(){
  renderSwapTelefono();
  if (typeof renderWalletBarattolo === 'function') renderWalletBarattolo();
}
/* la frase del recupero sopravvive al ridisegno della pagina (presa dal
   giro dal vivo: la pagina si riscrive subito dopo, e la cancellava) */
const swapNotaRecupero = {testo: ''};
function swapDiciRecupero(frase){
  swapNotaRecupero.testo = frase;
  const n = el('swapRecuperoNota');
  if (n) n.textContent = frase;
}
/* «RITROVA I MIEI CAMBI» (parole-uniche): la chiave del wallet di
   Barattolo (ritrovata dal backup su un telefono nuovo, dalla pagina),
   la sua xpub di radice a OGNI fornitore, e il contatore che riparte
   dopo l'indice piu' alto trovato da tutti: le chiavi sono una serie
   sola, e un indice riusato con un fornitore diverso sarebbe lo stesso
   segreto due volte. */
async function swapRitrovaCambi(){
  haptic();
  const t = t3();
  swapDiciRecupero('');
  let parole;
  try { parole = (await swapSemePronto()).parole; }
  catch(e){ swapDiciRecupero(t.semeNo); return; }
  let quanti = 0, prossimo = 0;
  for (const f of swapFornitori()) {
    if (!f.recupera) continue;
    let trovati;
    try { trovati = await f.recupera(parole); }
    catch(e){ swapDiciRecupero(t.nonRisponde(f.nome)); return; }
    prossimo = Math.max(prossimo, Number(trovati.prossimo) || 0);
    for (const s of trovati.swap) {
      if (swapLista().some(r => r.id === s.id)) continue;
      swapSalvaRecord(Object.assign(s, {fornitore: f.id, ordine: null, indirizzo: '', seme: 'onchain'}));
      quanti++;
    }
  }
  const c = swapStatoSeme();
  c.prossimo = Math.max(Number(c.prossimo) || 0, prossimo);
  swapScrivi(swapCasaOnchain(), c);
  swapDiciRecupero(t.ritrovaFatto(quanti));
  swapRidisegnaRiserva();
  swapSorveglia();
}
/* il recupero SCRIVENDO le parole: per i soli cambi di prima del 29 ott
   2026, che hanno dodici parole loro */
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
  if (c && c.parole && c.parole !== parole && swapLista().some(r => swapDiChi(r) === f.id && r.seme !== 'onchain')) {
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
  swapRidisegnaRiserva();
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
    /* (tappa 3) per un submarine l'indirizzo e' quello del rimborso */
    if (swapESub(rec)) { swapRimborsa(rec); swapSorveglia(); } else swapRitira(rec);
  }).catch(() => toast(t3().nonRisponde(f.nome)));
}

/* ─── 9. L'ASCOLTATORE DELEGATO: niente handler inline ──────────────── */
if (typeof document !== 'undefined') {
  document.addEventListener('click', ev => {
    const b = ev.target && ev.target.closest ? ev.target.closest('[data-swap]') : null;
    /* (unita-tendine) un tocco fuori dalla tendina aperta la chiude */
    if (swapCambioTendina && !(b && (b.dataset.swap === 'cambio-tendina' || b.dataset.swap === 'cambio-rete'))) {
      swapCambioTendina = null;
      swapCambioRidisegna();
    }
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
    else if (a === 'mostra-parole') { haptic(); swapParoleViste[fid] = !swapParoleViste[fid]; swapRidisegnaRiserva(); }
    else if (a === 'recupera') swapRecupera(fid);
    else if (a === 'ritrova') swapRitrovaCambi();
    else if (a === 'al-profilo' && typeof apriCassettoProfilo === 'function') { haptic(); apriCassettoProfilo('accOnchainIncasso'); }
    else if (a === 'ritira-a') swapRitiraA(String(b.dataset.id || ''));
    else if (a === 'cambio-gira') swapCambioScegliStrada(String(b.dataset.strada || 'ln-btc'));
    else if (a === 'cambio-unita') swapCambioScegliUnita(String(b.dataset.unita || 'sats'));
    else if (a === 'cambio-onion' && typeof apriSitoOnion === 'function') apriSitoOnion();
    else if (a === 'cambio-tendina') swapCambioApriTendina(String(b.dataset.lato || 'mandi'));
    else if (a === 'cambio-rete') swapCambioScegliStrada(String(b.dataset.strada || 'ln-btc'));
    else if (a === 'cambio-calcola') swapCambioCalcola();
    else if (a === 'dettagli') { haptic(); dettagliSwap[n] = !dettagliSwap[n]; ridisegnaIncassoSwap(); }
    else if (a === 'cambio-copia') swapCambioCopia(String(b.dataset.id || ''));
    else if (a === 'cambio-copia-indirizzo') swapCambioCopia(String(b.dataset.id || ''), 'indirizzo');
    else if (a === 'incolla-fattura') swapIncollaFattura(n);
  });
  /* il campo dell'indirizzo si ricorda a ogni lettera: il preventivo si
     ridisegna anche da solo, e un bc1 lungo non si riscrive */
  document.addEventListener('input', ev => {
    const c = ev.target;
    if (c && typeof c.id === 'string' && c.id.startsWith('swapIndirizzo_'))
      swapIndirizziScritti[Number(c.id.slice(14))] = String(c.value || '');
    if (c && (c.id === 'swapCambioMandi' || c.id === 'swapCambioRicevi')) swapCambioScrive(c.value, c.dataset.lato);
    if (c && typeof c.id === 'string' && c.id.startsWith('swapFattura_'))
      swapFattureScritte[Number(c.id.slice(12))] = String(c.value || '');
  });
  /* uscendo dal campo della cifra la si rilegge coi separatori, come la
     cifra dell'altro riquadro (mentre si scrive no: il cursore saltava).
     (cambio-due-riquadri) Se il conto al contrario ha dato un sat in piu',
     qui si vede la cifra vera: lo stesso conto, che resta di adesso */
  document.addEventListener('focusout', ev => {
    const c = ev.target;
    if (!c || (c.id !== 'swapCambioMandi' && c.id !== 'swapCambioRicevi') || c.dataset.lato !== swapCambioLato) return;
    let n = swapCambioCifra();
    const p = preventiviSwap[0] || {};
    const d = p.dati && swapCambioDiAdesso(p.dati) ? p.dati : null;
    if (d && d.ok && n && swapCambioLato !== swapCambioLatoDovuto() && !swapCambioTimer) {
      const vera = Number(swapCambioLato === 'mandi' ? d.mandi : d.ricevi) || n;
      d.scritta = vera;
      n = vera;
    }
    swapCambioScritta = n ? swapCambioNum(n) : '';
    c.value = swapCambioScritta;
  });
  /* la fotocamera non resta accesa ad app in secondo piano */
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && swapQrFlusso) swapQrChiudi();
  });
  swapRiprendi();
}
