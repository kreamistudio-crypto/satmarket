/* ═══ LO SWAP DAL TELEFONO (20 ott 2026, cantiere swap-telefono, tappa 3)
   Lo swap Lightning -> on-chain di SATS Routing fatto DAL TELEFONO di chi
   vende. Le dodici parole e le chiavi nascono qui e non escono mai: a
   SATS Routing vanno solo le parti pubbliche (l'impronta del segreto, la
   chiave pubblica, la xpub al recupero), al server di Barattolo NIENTE di
   questo file. Il telefono parla DIRETTAMENTE con SATS Routing
   (`swapLeve.api`): la CSP della pagina, a swap acceso, ammette quella
   sola origine (server.py, `_csp_prova`).

   UN FILE SUO, e non un pezzo del grande <script> della pagina, apposta:
   arriva la fase 2 della CSP che toglie 'unsafe-inline', e questo codice
   non va rifatto — niente script inline, niente `onclick=`: i bottoni
   portano `data-swap="…"` e li ascolta UN solo ascoltatore delegato, in
   fondo. Lo carica la pagina solo quando `swapAcceso()` (oggi: i
   moderatori, a leva accesa); la libreria di crittografia
   (`/vendor/swap.js`, boltz-core 5.0.0 + @scure) la scarica questo file
   solo quando serve davvero.

   IN QUESTA TAPPA BARATTOLO NON PAGA LA FATTURA DELLO SWAP: lo swap si
   crea, si verifica e si sorveglia, e il ritiro e' pronto; il pagamento
   dal nodo arriva con la tappa 4 (coi tetti dei pagamenti appesi). Lo
   swap intero si prova sul regtest di Boltz sulla VM di collaudo.

   Usa dalla pagina: swapLeve, swapAcceso, myTgId, FOTO_BASE, el, esc, fmt,
   haptic, toast, currentOrder, payoutPanel, preventiviSwap,
   sceltaIncassoSwap, caricaPreventivoSwap, pannelloPreventivoSwap,
   leggiBolt11, linguaSwap. */

/* ─── 1. IL MOTORE: funzioni pure sopra la libreria `S` ─────────────────
   Lo schema delle chiavi e' quello del sito di SATS Routing (boltz-web-app
   `004f4077`, `rescueFile.ts` e `rescueDerivation.ts`): dodici parole,
   chiave dello swap numero i in m/44/0/0/0/i, segreto = sha256(chiave
   privata). Cosi' uno swap nato qui si ritrova anche dalla loro pagina
   «Rescue». Provato contro i LORO vettori in `prove_bundle_swap`. */
const SWAP_PERCORSO = 'm/44/0/0/0';
/* il regtest di Boltz (la VM di collaudo): btc-signer conosce solo bitcoin
   e testnet, e il regtest ha il suo prefisso */
const SWAP_RETE_REGTEST = {bech32: 'bcrt', pubKeyHash: 0x6f, scriptHash: 0xc4, wif: 0xef};
function swapRete(S, nome){
  return nome === 'regtest' ? SWAP_RETE_REGTEST
       : nome === 'testnet' ? S.TEST_NETWORK : S.NETWORK;
}
function swapRadice(S, parole){
  return S.HDKey.fromMasterSeed(S.mnemonicToSeedSync(String(parole || '').trim()));
}
/* le chiavi dello swap numero `indice`: la privata, la pubblica (33 byte),
   il segreto della fattura e la sua impronta */
function swapChiavi(S, parole, indice){
  const k = swapRadice(S, parole).derive(`${SWAP_PERCORSO}/${Number(indice)}`);
  const segreto = S.sha256(k.privateKey);
  return {privata: k.privateKey, pubblica: k.publicKey,
          segreto: segreto, impronta: S.sha256(segreto)};
}
/* la xpub della RADICE, come la manda il loro sito al recupero: col
   percorso di serie il server ritrova da se' le chiavi m/44/0/0/0/i */
function swapXpub(S, parole){ return swapRadice(S, parole).publicExtendedKey; }
function swapUguali(a, b){
  if (!a || !b || a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}
/* lo script di un indirizzo, o null se non e' un indirizzo di questa rete
   (il checksum lo controlla btc-signer) */
function swapScriptIndirizzo(S, rete, indirizzo){
  try { return S.OutScript.encode(S.Address(rete).decode(String(indirizzo || '').trim())); }
  catch(e){ return null; }
}
/* LA VERIFICA DELLA RISPOSTA DI SATS ROUTING, prima di fidarsi: null = tutto
   torna, altrimenti la ragione. Il calco di `validateReverse` del loro
   sito: la fattura porta l'importo che ci spetta e l'impronta del NOSTRO
   segreto (SATS Routing incassa solo quando noi ritiriamo), l'albero e'
   quello che rifacciamo da soli coi nostri pezzi, e l'indirizzo dove
   blocca i bitcoin e' quello che quell'albero e le due chiavi danno (la
   chiave di SATS Routing PER PRIMA nel MuSig, come nel loro
   `createMusig`). Piu' il nostro: on-chain non meno del preventivo. */
function swapVerifica(S, rete, r, chiavi, attesa){
  if (!r || typeof r !== 'object' || typeof r.invoice !== 'string') return 'risposta';
  const b = leggiBolt11(r.invoice);
  if (!b) return 'fattura';
  if (b.sats !== attesa.sats) return 'importo';
  if (!b.hash || b.hash !== S.hex.encode(chiavi.impronta)) return 'impronta';
  let loro, albero, atteso, agg;
  const scadenza = Number(r.timeoutBlockHeight);
  if (!(scadenza > 0)) return 'albero';
  try {
    loro = S.hex.decode(String(r.refundPublicKey || ''));
    albero = S.SwapTreeSerializer.deserializeSwapTree(r.swapTree);
    atteso = S.reverseSwapTree(false, chiavi.impronta, chiavi.pubblica, loro, scadenza);
  } catch(e){ return 'albero'; }
  if (!S.compareTrees(albero, atteso)) return 'albero';
  try {
    agg = S.TaprootUtils.tweakMusig(S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]), albero.tree);
  } catch(e){ return 'indirizzo'; }
  if (!swapUguali(S.Scripts.p2trOutput(agg.aggPubkey),
                  swapScriptIndirizzo(S, rete, r.lockupAddress))) return 'indirizzo';
  if (!(Number(r.onchainAmount) >= Number(attesa.onchainMin))) return 'meno';
  return null;
}
/* IL RITIRO: la transazione che porta i bitcoin bloccati da SATS Routing
   all'indirizzo di chi vende. `ricevi` e' quel che il preventivo ha
   promesso: la differenza col lockup e' la fee del ritiro (il calco di
   `createAdjustedClaim`). COOPERATIVO prima — una firma MuSig2 a due,
   SATS Routing manda la sua parte (`chiediFirma`) — e se non collabora
   DALLO SCRIPT, con la sola chiave nostra e il segreto: il loro permesso
   non serve. Torna {hex, id, cooperativo}. */
async function swapRitiro(S, rete, rec, chiavi, lockupHex, destinazione, ricevi, chiediFirma, cooperativo){
  if (cooperativo === undefined) cooperativo = true;
  const loro = S.hex.decode(String(rec.refundPublicKey || ''));
  const albero = S.SwapTreeSerializer.deserializeSwapTree(rec.swapTree);
  const keyAgg = S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]);
  const tweaked = S.TaprootUtils.tweakMusig(keyAgg, albero.tree);
  const lockup = S.Transaction.fromRaw(S.hex.decode(String(lockupHex || '')),
    {allowUnknownOutputs: true, allowUnknownInputs: true});
  const uscita = S.detectSwap(tweaked.aggPubkey, lockup);
  if (uscita === undefined) throw new Error('nel lockup non c\'e\' il nostro swap');
  const budget = Number(uscita.amount) - Number(ricevi);
  if (!(budget > 0)) throw new Error('il lockup non copre quel che il preventivo promette');
  const script = swapScriptIndirizzo(S, rete, destinazione);
  if (!script) throw new Error('indirizzo di destinazione non valido');
  const dettagli = [Object.assign({}, uscita, {
    cooperative: cooperativo, swapTree: albero, privateKey: chiavi.privata,
    type: S.OutputType.Taproot, transactionId: lockup.id,
    internalKey: keyAgg.aggPubkey, preimage: chiavi.segreto})];
  const tx = S.constructClaimTransaction(dettagli, script, BigInt(budget), true);
  if (!cooperativo) return {hex: tx.hex, id: tx.id, cooperativo: false};
  try {
    const sighash = tx.preimageWitnessV1(0, [uscita.script], S.SigHash.DEFAULT, [uscita.amount]);
    const conNonce = tweaked.message(sighash).generateNonce();
    const r = await chiediFirma(tx.hex, S.hex.encode(conNonce.publicNonce));
    const firma = conNonce
      .aggregateNonces([[loro, S.hex.decode(String(r.pubNonce))]])
      .initializeSession()
      .signPartial()
      .addPartial(loro, S.hex.decode(String(r.partialSignature)))
      .aggregatePartials();
    tx.updateInput(0, {finalScriptWitness: [firma]});
    return {hex: tx.hex, id: tx.id, cooperativo: true};
  } catch(e){
    return swapRitiro(S, rete, rec, chiavi, lockupHex, destinazione, ricevi, chiediFirma, false);
  }
}
/* gli stati di SATS Routing dopo i quali non c'e' piu' niente da fare */
const SWAP_STATI_FINALI = new Set(['invoice.settled', 'swap.expired', 'invoice.expired',
                                   'transaction.failed', 'transaction.refunded']);
/* gli stati in cui i bitcoin sono bloccati e si puo' ritirare */
const SWAP_STATI_RITIRO = new Set(['transaction.mempool', 'transaction.confirmed']);

/* ─── 2. LA LIBRERIA, pigra ──────────────────────────────────────────── */
const SWAP_BUNDLE_VER = '5.0.0-bar1';
let swapBundlePromessa = null;
function caricaBundleSwap(){
  if (window.BarattoloSwap) return Promise.resolve(window.BarattoloSwap);
  if (!swapBundlePromessa) swapBundlePromessa = new Promise((ok, no) => {
    const s = document.createElement('script');
    s.src = `${FOTO_BASE}/vendor/swap.js?v=${SWAP_BUNDLE_VER}`;
    s.onload = () => {
      if (window.BarattoloSwap) return ok(window.BarattoloSwap);
      swapBundlePromessa = null;
      no(new Error('libreria dello swap incompleta'));
    };
    s.onerror = () => { swapBundlePromessa = null;
                        no(new Error('libreria dello swap non raggiungibile')); };
    document.head.appendChild(s);
  });
  return swapBundlePromessa;
}

/* ─── 3. IL CASSETTO, sotto il CONTO ──────────────────────────────────
   Le parole e gli swap stanno nel localStorage di QUESTO telefono, sotto
   l'account Telegram (la lezione di `MOSTRO_CHIAVE`: due account sullo
   stesso telefono sono due persone). MAI al server. Il cassetto delle
   parole: {parole, prossimo, copiata}. `prossimo` e' l'indice della
   prossima chiave: si salva PRIMA di chiedere lo swap, perche' un indice
   riusato vorrebbe dire un segreto riusato. */
function swapCasaParole(){ return `barattolo_swap_${myTgId || 'x'}`; }
function swapCasaLista(){ return `barattolo_swap_lista_${myTgId || 'x'}`; }
function swapLeggi(k, vuoto){
  try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? vuoto : v; }
  catch(e){ return vuoto; }
}
function swapScrivi(k, v){
  try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch(e){ return false; }
}
function swapCassetto(){ return swapLeggi(swapCasaParole(), null); }
function swapLista(){ const l = swapLeggi(swapCasaLista(), []); return Array.isArray(l) ? l : []; }
function swapSalvaRecord(rec){
  const l = swapLista().filter(x => x.id !== rec.id);
  l.push(rec);
  return swapScrivi(swapCasaLista(), l);
}
function swapDiOrdine(ordine){
  const n = Number(ordine);
  return swapLista().filter(x => Number(x.ordine) === n).pop() || null;
}

/* ─── 4. SATS ROUTING, direttamente ─────────────────────────────────── */
async function swapApi(percorso, corpo){
  const base = String((swapLeve && swapLeve.api) || '').replace(/\/+$/, '');
  if (!base) throw new Error('SATS Routing non configurato');
  const opz = corpo === undefined ? {}
    : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(corpo)};
  const r = await fetch(base + percorso, opz);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) {
    const e = new Error((d && d.error) || ('HTTP ' + r.status));
    e.codice = r.status;
    throw e;
  }
  return d;
}

/* ─── 5. I TESTI, in italiano e in inglese ───────────────────────────── */
const SWAP_TESTI_T3 = {
  it: {
    paroleTit: 'Le tue 12 parole',
    paroleSpiega: 'Sono la chiave dei tuoi swap e stanno solo su questo telefono. Scrivile su carta: servono a recuperare uno swap se cambi telefono.',
    paroleSpunta: 'Le ho scritte su carta',
    paroleFatto: 'Ho salvato le parole',
    paroleSpuntaPrima: 'Prima spunta «Le ho scritte su carta».',
    indirizzoTit: 'Dove ricevi i bitcoin',
    indirizzoSpiega: 'Un indirizzo bitcoin del tuo wallet.',
    indirizzoNo: 'Questo non è un indirizzo valido per questa rete.',
    crea: 'Crea lo swap',
    creo: 'Creo lo swap e controllo la risposta di SATS Routing…',
    nienteCasa: 'Questo telefono non riesce a conservare le chiavi: lo swap non si può fare da qui.',
    rifiuto: 'SATS Routing ha risposto con dati che non tornano: lo swap non parte, nessun sats si è mosso.',
    nonRisponde: 'SATS Routing ora non risponde: riprova, o incassa in Lightning.',
    tuoSwap: 'Il tuo swap',
    ricevi: n => `Ricevi circa ${n} sats a`,
    riceviQui: n => `Ricevi circa ${n} sats a questo indirizzo.`,
    stati: {
      'swap.created': 'Pronto e verificato. Il pagamento da Barattolo arriva con la prossima versione: per ora nessun sats si muove.',
      'transaction.mempool': 'SATS Routing ha bloccato i bitcoin: ritiro in corso.',
      'transaction.confirmed': 'Bitcoin bloccati e confermati: ritiro in corso.',
      'invoice.settled': 'Fatto: i bitcoin sono tuoi.',
      'swap.expired': 'Scaduto: nessun sats si è mosso, l\'incasso torna disponibile.',
      'invoice.expired': 'Scaduto: nessun sats si è mosso, l\'incasso torna disponibile.',
      'transaction.failed': 'Non riuscito: l\'incasso torna disponibile.',
      'transaction.refunded': 'SATS Routing si è ripreso i bitcoin: l\'incasso torna disponibile.'},
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
    recuperaNo: 'Queste non sono 12 parole valide.',
    recuperaAltre: 'Su questo telefono ci sono già altre parole con degli swap: non le sostituisco.',
    recuperaFatto: n => n === 0 ? 'Nessuno swap legato a queste parole.'
      : n === 1 ? 'Recuperato 1 swap.' : `Recuperati ${n} swap.`,
    ritiraA: 'Ritira a questo indirizzo'},
  en: {
    paroleTit: 'Your 12 words',
    paroleSpiega: 'They are the key to your swaps and live only on this phone. Write them on paper: they recover a swap if you change phone.',
    paroleSpunta: 'I wrote them on paper',
    paroleFatto: 'I saved the words',
    paroleSpuntaPrima: 'First tick «I wrote them on paper».',
    indirizzoTit: 'Where you receive the bitcoin',
    indirizzoSpiega: 'A bitcoin address of your wallet.',
    indirizzoNo: 'This is not a valid address for this network.',
    crea: 'Create the swap',
    creo: 'Creating the swap and checking the SATS Routing answer…',
    nienteCasa: 'This phone cannot keep the keys: the swap cannot be done from here.',
    rifiuto: 'SATS Routing answered with data that does not add up: the swap does not start, no sats moved.',
    nonRisponde: 'SATS Routing is not responding: try again, or receive via Lightning.',
    tuoSwap: 'Your swap',
    ricevi: n => `You receive about ${n} sats at`,
    riceviQui: n => `You receive about ${n} sats at this address.`,
    stati: {
      'swap.created': 'Ready and verified. The payment from Barattolo comes with the next version: no sats move for now.',
      'transaction.mempool': 'SATS Routing locked the bitcoin: claiming.',
      'transaction.confirmed': 'Bitcoin locked and confirmed: claiming.',
      'invoice.settled': 'Done: the bitcoin are yours.',
      'swap.expired': 'Expired: no sats moved, the payout is available again.',
      'invoice.expired': 'Expired: no sats moved, the payout is available again.',
      'transaction.failed': 'Failed: the payout is available again.',
      'transaction.refunded': 'SATS Routing took the bitcoin back: the payout is available again.'},
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
    recuperaNo: 'These are not 12 valid words.',
    recuperaAltre: 'This phone already has other words with swaps: I will not replace them.',
    recuperaFatto: n => n === 0 ? 'No swaps tied to these words.'
      : n === 1 ? 'Recovered 1 swap.' : `Recovered ${n} swaps.`,
    ritiraA: 'Claim to this address'}};
function t3(){ return SWAP_TESTI_T3[linguaSwap()]; }
function swapCorto(s, n){ s = String(s || ''); return s.length > 2 * n + 1 ? `${s.slice(0, n)}…${s.slice(-n)}` : s; }

/* ─── 6. IL PANNELLO DELL'INCASSO, ramo swap ────────────────────────────
   I passi di un ordine: 'preventivo' (la tappa 2) -> 'parole' (solo la
   prima volta) -> 'indirizzo' -> 'creo'. Poi c'e' lo swap, e il pannello
   mostra il suo stato. */
const swapPassi = {};      // ordine -> passo
const swapErrori = {};     // ordine -> frase
/* l'indirizzo scritto, per ordine: un avviso ridisegna il pannello, e un
   bc1 lungo non si fa riscrivere da capo (preso dal giro dal vivo) */
const swapIndirizziScritti = {};
const swapParoleViste = {SI: false};
function pannelloSwapTelefono(o){
  const n = Number(o.id), t = t3();
  const rec = swapDiOrdine(n);
  if (rec) return cartaSwap(rec);
  const passo = swapPassi[n] || 'preventivo';
  const errore = swapErrori[n]
    ? `<div class="swap-rifiuto" role="status">${esc(swapErrori[n])}</div>` : '';
  if (passo === 'parole') {
    const c = swapCassetto();
    const parole = c && c.parole ? String(c.parole).split(' ') : [];
    return `<div class="swap-prev">
      <h4>🔑 ${esc(t.paroleTit)}</h4>
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
      <button class="btn orange" type="button" data-swap="crea" data-ordine="${n}"${passo === 'creo' ? ' disabled' : ''}>${esc(passo === 'creo' ? t.creo : t.crea)}</button>
    </div>`;
  }
  return pannelloPreventivoSwap(o);
}
function frasestatoSwap(rec){
  const t = t3();
  if (rec.ritiro && rec.ritiro.txid && rec.stato !== 'invoice.settled')
    return t.ritirato(swapCorto(rec.ritiro.txid, 8));
  return t.stati[rec.stato] || t.statoIgnoto;
}
function cartaSwap(rec){
  const t = t3();
  return `<div class="swap-prev swap-carta" data-swap-id="${esc(rec.id)}">
    <h4>₿ ${esc(t.tuoSwap)}</h4>
    <div class="swap-stato">${esc(frasestatoSwap(rec))}</div>
    ${rec.ricevi && rec.indirizzo ? `<div class="hint">${esc(t.ricevi(fmt(rec.ricevi)))} <span class="mono">${esc(swapCorto(rec.indirizzo, 8))}</span></div>` : ''}
    ${rec.errore ? `<div class="hint">${esc(t.ritiroErrore)}</div>` : ''}
  </div>`;
}

/* ─── 7. LE AZIONI ──────────────────────────────────────────────────── */
/* «Conferma lo swap» del preventivo: si ricontrollano le tariffe con
   l'impronta di quelle mostrate (la tappa 2); se reggono, la prima volta
   le parole, poi l'indirizzo */
async function swapAvanti(n){
  haptic();
  delete swapErrori[n];
  await caricaPreventivoSwap(n, true);
  const p = preventiviSwap[n] || {};
  if (!p.dati || !p.dati.ok || p.nota === 'cambiata') return;
  const c = swapCassetto();
  if (!c || !c.parole || !c.copiata) {
    let S;
    try { S = await caricaBundleSwap(); }
    catch(e){ swapErrori[n] = t3().nonRisponde; return ridisegnaIncassoSwap(); }
    if (!c || !c.parole) {
      const nuovo = {parole: S.generateMnemonic(S.wordlist), prossimo: 0, copiata: false};
      if (!swapScrivi(swapCasaParole(), nuovo)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
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
  const c = swapCassetto();
  if (!c) return;
  c.copiata = true;
  if (!swapScrivi(swapCasaParole(), c)) { swapErrori[n] = t3().nienteCasa; return ridisegnaIncassoSwap(); }
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
  let S;
  try { S = await caricaBundleSwap(); }
  catch(e){ swapErrori[n] = t.nonRisponde; return ridisegnaIncassoSwap(); }
  const rete = swapRete(S, swapLeve && swapLeve.rete);
  if (!swapScriptIndirizzo(S, rete, indirizzo)) {
    swapErrori[n] = t.indirizzoNo; return ridisegnaIncassoSwap();
  }
  if (!p.ok || !p.hash) { swapPassi[n] = 'preventivo'; return ridisegnaIncassoSwap(); }
  const c = swapCassetto();
  if (!c || !c.parole || !c.copiata) { swapPassi[n] = 'parole'; return ridisegnaIncassoSwap(); }
  /* L'INDICE SI PRENOTA PRIMA DI CHIEDERE: se il telefono si spegne a meta',
     al giro dopo si usa il successivo, mai lo stesso */
  const indice = Number(c.prossimo) || 0;
  c.prossimo = indice + 1;
  if (!swapScrivi(swapCasaParole(), c)) { swapErrori[n] = t.nienteCasa; return ridisegnaIncassoSwap(); }
  swapPassi[n] = 'creo';
  delete swapErrori[n];
  ridisegnaIncassoSwap();
  const chiavi = swapChiavi(S, c.parole, indice);
  const corpo = {from: 'BTC', to: 'BTC', invoiceAmount: p.fattura,
                 preimageHash: S.hex.encode(chiavi.impronta),
                 claimPublicKey: S.hex.encode(chiavi.pubblica), pairHash: p.hash};
  const codice = String((swapLeve && swapLeve.referral) || '').trim();
  if (codice) corpo.referralId = codice;
  let r;
  try { r = await swapApi('/v2/swap/reverse', corpo); }
  catch(e){ swapPassi[n] = 'indirizzo'; swapErrori[n] = t.nonRisponde; return ridisegnaIncassoSwap(); }
  const perche = swapVerifica(S, rete, r, chiavi, {sats: p.fattura, onchainMin: p.onchain});
  if (perche) {
    swapPassi[n] = 'indirizzo';
    swapErrori[n] = t.rifiuto;
    return ridisegnaIncassoSwap();
  }
  swapSalvaRecord({id: String(r.id), ordine: n, indice: indice, invoice: r.invoice,
    lockupAddress: r.lockupAddress, refundPublicKey: r.refundPublicKey,
    swapTree: r.swapTree, timeoutBlockHeight: Number(r.timeoutBlockHeight),
    onchainAmount: Number(r.onchainAmount), ricevi: Number(p.ricevi),
    indirizzo: indirizzo, stato: 'swap.created', creato: Date.now()});
  delete swapPassi[n];
  ridisegnaIncassoSwap();
  swapSorveglia();
}

/* ─── 8. LA SORVEGLIANZA E IL RITIRO ──────────────────────────────────
   Ogni 5 secondi, finche' c'e' uno swap non finito, si chiede a SATS
   Routing a che punto e' (`GET /v2/swap/<id>`); quando i bitcoin sono
   bloccati si ritira. All'apertura dell'app si riprende da qui
   (`swapRiprendi`): chiudere l'app a meta' non perde niente. */
let swapTimer = null;
const swapRitirando = new Set();
function swapAperti(){ return swapLista().filter(r => !SWAP_STATI_FINALI.has(r.stato)); }
function swapSorveglia(){
  if (swapTimer || !swapAperti().length) return;
  swapTimer = setInterval(swapGiro, 5000);
  swapGiro();
}
async function swapGiro(){
  const aperti = swapAperti();
  if (!aperti.length || !swapAcceso()) { clearInterval(swapTimer); swapTimer = null; return; }
  for (const rec of aperti) {
    let s;
    try { s = await swapApi(`/v2/swap/${encodeURIComponent(rec.id)}`); }
    catch(e){ continue; }
    if (s && s.status && s.status !== rec.stato) {
      rec.stato = String(s.status);
      swapSalvaRecord(rec);
      swapRidisegnaDove(rec);
    }
    if (SWAP_STATI_RITIRO.has(rec.stato) && !(rec.ritiro && rec.ritiro.txid))
      await swapRitira(rec);
  }
}
async function swapRitira(rec){
  if (swapRitirando.has(rec.id) || !rec.indirizzo) return;
  swapRitirando.add(rec.id);
  let fatto = null;
  try {
    const S = await caricaBundleSwap();
    const rete = swapRete(S, swapLeve && swapLeve.rete);
    const c = swapCassetto();
    if (!c || !c.parole) throw new Error('parole assenti');
    const chiavi = swapChiavi(S, c.parole, rec.indice);
    let ricevi = Number(rec.ricevi);
    if (!(ricevi > 0)) {
      /* uno swap recuperato non ha il preventivo: la fee del ritiro
         dalle tariffe di adesso */
      const tar = await swapApi('/v2/swap/reverse');
      ricevi = Number(rec.onchainAmount) - Number(tar.BTC.BTC.fees.minerFees.claim);
    }
    const lock = await swapApi(`/v2/swap/reverse/${encodeURIComponent(rec.id)}/transaction`);
    const chiediFirma = (txHex, nonce) => swapApi(
      `/v2/swap/reverse/${encodeURIComponent(rec.id)}/claim`,
      {index: 0, preimage: S.hex.encode(chiavi.segreto), pubNonce: nonce, transaction: txHex});
    /* un ritiro cooperativo gia' RIFIUTATO alla trasmissione (la firma
       messa insieme con SATS Routing non reggeva) non si ripete: dal giro
       dopo si ritira dallo script, che dipende solo da noi */
    fatto = await swapRitiro(S, rete, rec, chiavi, lock.hex, rec.indirizzo, ricevi, chiediFirma,
                             !rec.coopRifiutato);
    const inviata = await swapApi('/v2/chain/BTC/transaction', {hex: fatto.hex});
    rec.ritiro = {txid: String((inviata && inviata.id) || fatto.id),
                  cooperativo: fatto.cooperativo, quando: Date.now()};
    delete rec.errore;
  } catch(e){
    rec.errore = String((e && e.message) || e).slice(0, 120);
    if (fatto && fatto.cooperativo) rec.coopRifiutato = true;
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

/* ─── 9. LA PAGINA «SWAP» ───────────────────────────────────────────── */
function renderSwapTelefono(){
  const box = el('swapTelefono');
  if (!box) return;
  const t = t3();
  const lista = swapLista().slice().sort((a, b) => (b.creato || 0) - (a.creato || 0));
  /* con degli swap in lista, il «per ora nessuno» della tappa 1 tace */
  if (el('swapVuoto')) el('swapVuoto').style.display = lista.length ? 'none' : '';
  const righe = lista.map(rec => `<div class="swap-riga-lista">
      <b>${esc(rec.ordine ? t.ordine(rec.ordine) : t.recuperato)}</b>
      <span>${esc(frasestatoSwap(rec))}</span>
      ${!rec.indirizzo && SWAP_STATI_RITIRO.has(rec.stato) ? `
        <input class="swap-indirizzo" id="swapIndirizzoR_${esc(rec.id)}" type="text" autocomplete="off" spellcheck="false" placeholder="bc1…">
        <button class="btn ghost" type="button" data-swap="ritira-a" data-id="${esc(rec.id)}">${esc(t.ritiraA)}</button>` : ''}
    </div>`).join('');
  const c = swapCassetto();
  const parole = c && c.parole && swapParoleViste.SI
    ? `<ol class="swap-parole">${String(c.parole).split(' ').map(p => `<li>${esc(p)}</li>`).join('')}</ol>` : '';
  box.innerHTML = `
    ${lista.length ? `<h4>${esc(t.lista)}</h4>${righe}` : ''}
    <h4>🔑 ${esc(t.paroleTit)}</h4>
    ${c && c.parole
      ? `<button class="btn ghost" type="button" data-swap="mostra-parole">${esc(swapParoleViste.SI ? t.nascondi : t.mostra)}</button>${parole}`
      : `<div class="hint">${esc(t.nessunaParola)}</div>`}
    <h4>${esc(t.recuperaTit)}</h4>
    <div class="hint">${esc(t.recuperaSpiega)}</div>
    <textarea id="swapRecupero" rows="3" autocomplete="off" spellcheck="false"></textarea>
    <div id="swapRecuperoNota" class="hint" role="status">${esc(swapNotaRecupero.testo)}</div>
    <button class="btn orange" type="button" data-swap="recupera">${esc(t.recupera)}</button>`;
}
/* la frase del recupero sopravvive al ridisegno della pagina (presa dal
   giro dal vivo: la pagina si riscrive subito dopo, e la cancellava) */
const swapNotaRecupero = {testo: ''};
function swapDiciRecupero(frase){
  swapNotaRecupero.testo = frase;
  const n = el('swapRecuperoNota');
  if (n) n.textContent = frase;
}
async function swapRecupera(){
  haptic();
  const t = t3();
  swapDiciRecupero('');
  const parole = String((el('swapRecupero') || {}).value || '').trim().toLowerCase().split(/\s+/).join(' ');
  let S;
  try { S = await caricaBundleSwap(); }
  catch(e){ swapDiciRecupero(t.nonRisponde); return; }
  if (parole.split(' ').length !== 12 || !S.validateMnemonic(parole, S.wordlist)) {
    swapDiciRecupero(t.recuperaNo); return;
  }
  const c = swapCassetto();
  if (c && c.parole && c.parole !== parole && swapLista().length) {
    swapDiciRecupero(t.recuperaAltre); return;
  }
  let trovati;
  try { trovati = await swapApi('/v2/swap/restore', {xpub: swapXpub(S, parole)}); }
  catch(e){ swapDiciRecupero(t.nonRisponde); return; }
  /* il contatore riparte DOPO l'indice piu' alto trovato: mai un segreto
     riusato */
  let prossimo = c && c.parole === parole ? Number(c.prossimo) || 0 : 0;
  let quanti = 0;
  for (const s of (Array.isArray(trovati) ? trovati : [])) {
    const d = s && s.claimDetails;
    if (!d || s.type !== 'reverse' || s.from !== 'BTC' || s.to !== 'BTC') continue;
    prossimo = Math.max(prossimo, Number(d.keyIndex) + 1);
    if (swapLista().some(r => r.id === s.id)) continue;
    swapSalvaRecord({id: String(s.id), ordine: null, indice: Number(d.keyIndex),
      lockupAddress: d.lockupAddress, refundPublicKey: d.serverPublicKey,
      swapTree: d.tree, timeoutBlockHeight: Number(d.timeoutBlockHeight),
      onchainAmount: Number(d.amount) || 0, ricevi: null, indirizzo: '',
      stato: String(s.status || ''), creato: (Number(s.createdAt) || 0) * 1000});
    quanti++;
  }
  swapScrivi(swapCasaParole(), {parole: parole, prossimo: prossimo, copiata: true});
  swapDiciRecupero(t.recuperaFatto(quanti));
  renderSwapTelefono();
  swapSorveglia();
}
function swapRitiraA(id){
  haptic();
  const rec = swapLista().find(r => r.id === id);
  const v = String((el(`swapIndirizzoR_${id}`) || {}).value || '').trim();
  if (!rec || !v) return;
  caricaBundleSwap().then(S => {
    if (!swapScriptIndirizzo(S, swapRete(S, swapLeve && swapLeve.rete), v)) {
      toast(t3().indirizzoNo); return;
    }
    rec.indirizzo = v;
    swapSalvaRecord(rec);
    renderSwapTelefono();
    swapRitira(rec);
  }).catch(() => toast(t3().nonRisponde));
}

/* ─── 10. L'ASCOLTATORE DELEGATO: niente handler inline ──────────────── */
if (typeof document !== 'undefined') {
  document.addEventListener('click', ev => {
    const b = ev.target && ev.target.closest ? ev.target.closest('[data-swap]') : null;
    if (!b) return;
    const n = Number(b.dataset.ordine || 0);
    const a = b.dataset.swap;
    if (a === 'scegli') scegliIncassoSwap(n, b.dataset.scelta === 'swap' ? 'swap' : 'ln');
    else if (a === 'avanti') swapAvanti(n);
    else if (a === 'parole-fatte') swapParoleFatte(n);
    else if (a === 'crea') swapCrea(n);
    else if (a === 'mostra-parole') { haptic(); swapParoleViste.SI = !swapParoleViste.SI; renderSwapTelefono(); }
    else if (a === 'recupera') swapRecupera();
    else if (a === 'ritira-a') swapRitiraA(String(b.dataset.id || ''));
  });
  swapRiprendi();
}
