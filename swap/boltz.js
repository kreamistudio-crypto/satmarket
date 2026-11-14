/* ═══ IL FORNITORE DI TIPO «BOLTZ» (20 ott 2026, cantiere
   swap-instradatore; il motore e' quello della tappa 3, cantiere
   swap-telefono)
   Un fornitore che parla il protocollo di Boltz v2: oggi SATS Routing, e
   nelle prove un secondo cartone con prezzi diversi. La strada che sa
   fare: Lightning -> bitcoin on-chain (`ln-btc`, lo swap «reverse»). Le
   dodici parole e le chiavi nascono nel telefono e non escono mai: al
   fornitore vanno solo le parti pubbliche (l'impronta del segreto, la
   chiave pubblica, la xpub al recupero), al server di Barattolo NIENTE di
   questo file. Il telefono parla DIRETTAMENTE col fornitore (`api` della
   sua voce in `swapLeve.fornitori`) e con la rete (`mempool`, per leggere
   il lockup da una fonte che non e' il fornitore): la CSP della pagina, a
   swap acceso, ammette le sole origini di quei due (server.py,
   `_csp_prova`).

   L'INTERFACCIA che l'instradatore (swap/instradatore.js) chiede a ogni
   fornitore, qualunque sia il tipo:
     id, nome, tipo, strade          chi e', cosa sa fare
     fase(stato)                     lo stato suo -> creato | bloccato |
                                     confermato | fatto | scaduto |
                                     fallito | ripreso | ignoto
     nuoveParole(), paroleValide(p)  la chiave di ritiro e recupero
     indirizzoValido(indirizzo)      dove si ricevono i bitcoin
     crea({parole, indice, preventivo, indirizzo})  -> lo swap da salvare;
                                     un errore con `.tipo` = 'mente' (la
                                     risposta non torna) o 'giu'
     stato(rec)                      lo stato di adesso, o null
     lockupInRete(rec)               (facoltativo) i bitcoin sono bloccati
                                     sulla rete? per ritirare anche quando
                                     l'API del fornitore tace
     ritira(rec, parole)             -> {txid, cooperativo}, o {txid,
                                     concluso: true, sats} se il lockup
                                     l'ha gia' speso il nostro ritiro;
                                     un errore con `.tipo` = 'speso' (e
                                     `.txid`) se l'ha speso un altro
     recupera(parole)                -> {swap: [...], prossimo}
   LA STRADA ROVESCIATA, bitcoin -> Lightning (`btc-ln`, lo swap
   «submarine»; 27 ott 2026, cantiere cambio-libero, tappa 3; si accende
   solo dalla leva del server, CAMBIO_BTC_LN_ATTIVO). I record di questa
   strada portano `tipo: 'sub'`:
     fatturaValida(fattura, sats)    la richiesta Lightning dell'utente:
                                     null se buona, sennò il perche'
                                     ('fattura' | 'importo' | 'rete' |
                                     'scaduta')
     creaSub({parole, indice, preventivo, fattura}) -> lo swap da salvare
                                     (dove MANDARE i bitcoin e quanti)
     fase(stato, rec)                per un `rec.tipo === 'sub'` le fasi
                                     sue: creato (aspetta i bitcoin) |
                                     bloccato | confermato | pagata |
                                     fatto | fallito | scaduto | ripreso
     aiutaRitiro(rec, parole)        la nostra meta' della firma per il
                                     ritiro a due del fornitore, SOLO col
                                     segreto che prova la fattura pagata
     rimborsa(rec, parole)           i bitcoin tornano a `rec.indirizzo`:
                                     cooperativo, o dallo script dopo la
                                     scadenza (`.tipo` = 'presto' se la
                                     rete non e' ancora arrivata li')
   Il PREVENTIVO non sta qui: lo fa il server di Barattolo per fornitore
   (la rotta del preventivo della tappa 2, con `?fornitore=<id>`), e
   l'instradatore sceglie il migliore.

   Niente script inline e niente `onclick=` (arriva la fase 2 della CSP):
   questo file non disegna niente. La libreria di crittografia
   (`/vendor/swap.js`, boltz-core 5.0.0 + @scure) la scarica solo quando
   serve davvero. */

/* ─── 1. IL MOTORE: funzioni pure sopra la libreria `S` ─────────────────
   Lo schema delle chiavi e' quello del sito di SATS Routing (boltz-web-app
   `004f4077`, `rescueFile.ts` e `rescueDerivation.ts`): dodici parole,
   chiave dello swap numero i in m/44/0/0/0/i, segreto = sha256(chiave
   privata). Cosi' uno swap nato qui si ritrova anche dalla loro pagina
   «Rescue». Provato contro i LORO vettori in `prove_swap_telefono`. */
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
/* LA VERIFICA DELLA RISPOSTA DEL FORNITORE, prima di fidarsi: null = tutto
   torna, altrimenti la ragione. Il calco di `validateReverse` del sito di
   SATS Routing: la fattura porta l'importo che ci spetta e l'impronta del
   NOSTRO segreto (il fornitore incassa solo quando noi ritiriamo),
   l'albero e' quello che rifacciamo da soli coi nostri pezzi, e
   l'indirizzo dove blocca i bitcoin e' quello che quell'albero e le due
   chiavi danno (la chiave del fornitore PER PRIMA nel MuSig, come nel loro
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
/* LA VERIFICA DI UNO SWAP RITROVATO (14 nov 2026, cantiere
   audit-pagamenti-2, dal secondo audit di sicurezza). «Ritrova i miei
   cambi» prendeva dal fornitore albero, indirizzo, chiave e indice e li
   riscattava senza nessuno dei controlli della nascita: un fornitore
   bugiardo poteva farsi dare il segreto di un indice vivo contro un
   lockup disegnato da lui. Qui si rifanno i controlli che si possono
   rifare senza la fattura (che dopo un recupero non abbiamo): l'impronta
   del NOSTRO segreto se il fornitore la dice, l'albero rifatto coi
   nostri pezzi, l'indirizzo che ne viene, e un importo vero. null =
   torna, altrimenti la ragione. */
function swapVerificaRitrovato(S, rete, d, chiavi, impronta){
  if (!d || typeof d !== 'object') return 'risposta';
  if (impronta && String(impronta).toLowerCase() !== S.hex.encode(chiavi.impronta)) return 'impronta';
  const scadenza = Number(d.timeoutBlockHeight);
  if (!(scadenza > 0)) return 'albero';
  let loro, albero, atteso, agg;
  try {
    loro = S.hex.decode(String(d.serverPublicKey || ''));
    albero = S.SwapTreeSerializer.deserializeSwapTree(d.tree);
    atteso = S.reverseSwapTree(false, chiavi.impronta, chiavi.pubblica, loro, scadenza);
  } catch(e){ return 'albero'; }
  if (!S.compareTrees(albero, atteso)) return 'albero';
  try {
    agg = S.TaprootUtils.tweakMusig(S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]), albero.tree);
  } catch(e){ return 'indirizzo'; }
  if (!swapUguali(S.Scripts.p2trOutput(agg.aggPubkey),
                  swapScriptIndirizzo(S, rete, d.lockupAddress))) return 'indirizzo';
  if (!(Number(d.amount) > 0)) return 'importo';
  return null;
}
/* IL RITIRO: la transazione che porta i bitcoin bloccati dal fornitore
   all'indirizzo di chi vende. `ricevi` e' quel che il preventivo ha
   promesso: la differenza col lockup e' la fee del ritiro (il calco di
   `createAdjustedClaim`). COOPERATIVO prima — una firma MuSig2 a due, il
   fornitore manda la sua parte (`chiediFirma`) — e se non collabora
   DALLO SCRIPT, con la sola chiave nostra e il segreto: il loro permesso
   non serve. Torna {hex, id, cooperativo}.
   I DUE CONTROLLI SUL LOCKUP PRIMA DI QUALUNQUE SEGRETO (20 ott 2026,
   cantiere swap-lockup, dopo la chiusura di Boltz): il segreto esce di
   qui (nella richiesta della firma, o nella transazione dallo script), e
   un fornitore che mente se lo farebbe dare senza aver bloccato davvero
   i bitcoin. Quindi: (1) l'uscita del lockup e' ESATTAMENTE quella dello
   script atteso — il p2tr della chiave MuSig con l'albero — e non una
   delle altre tre forme che `detectSwap` della 5.0.0 accetta. La difesa
   e' il NOSTRO confronto, e basta da sola: dal 20 ott 2026 (cantiere
   swap-bundle-500, consiglio di Massimo) il bundle e' di nuovo la 5.0.0 di
   npm, che ignora il terzo argomento di `detectSwap`; lo passiamo lo
   stesso, per un bundle che un giorno porti la #196; (2) l'importo non e' meno
   di quello promesso alla nascita (`rec.onchainAmount`). Il terzo
   controllo — il lockup esiste davvero sulla rete — lo fa `ritira`,
   prima di arrivare qui. */
async function swapRitiro(S, rete, rec, chiavi, lockupHex, destinazione, ricevi, chiediFirma, cooperativo, attendi){
  if (cooperativo === undefined) cooperativo = true;
  const loro = S.hex.decode(String(rec.refundPublicKey || ''));
  const albero = S.SwapTreeSerializer.deserializeSwapTree(rec.swapTree);
  const keyAgg = S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]);
  const tweaked = S.TaprootUtils.tweakMusig(keyAgg, albero.tree);
  const lockup = S.Transaction.fromRaw(S.hex.decode(String(lockupHex || '')),
    {allowUnknownOutputs: true, allowUnknownInputs: true});
  const atteso = S.Scripts.p2trOutput(tweaked.aggPubkey);
  const uscita = S.detectSwap(tweaked.aggPubkey, lockup, atteso);
  if (uscita === undefined || !swapUguali(uscita.script, atteso))
    throw new Error('nel lockup non c\'e\' il nostro swap');
  if (!(Number(uscita.amount) >= Number(rec.onchainAmount)))
    throw new Error('il lockup porta meno di quanto promesso');
  const budget = Number(uscita.amount) - Number(ricevi);
  if (!(budget > 0)) throw new Error('il lockup non copre quel che il preventivo promette');
  const script = swapScriptIndirizzo(S, rete, destinazione);
  if (!script) throw new Error('indirizzo di destinazione non valido');
  /* (14 nov 2026, secondo audit) la conferma e il margine, DOPO i due
     controlli sul lockup e PRIMA che il segreto entri in una transazione:
     li porta `ritira`, che sa leggere la rete */
  if (attendi) await attendi();
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
/* gli stati di Boltz v2 nel vocabolario dell'instradatore */
const SWAP_FASI_BOLTZ = {
  'swap.created': 'creato', 'transaction.mempool': 'bloccato',
  'transaction.confirmed': 'confermato', 'invoice.settled': 'fatto',
  'swap.expired': 'scaduto', 'invoice.expired': 'scaduto',
  'transaction.failed': 'fallito', 'transaction.refunded': 'ripreso'};
/* IL MARGINE DEL RITIRO (14 nov 2026, secondo audit): come il server
   (SWAP_AUTO_MARGINE_RITIRO), un paio d'ore di blocchi prima della
   scadenza dello swap; sotto, il segreto non esce piu'. */
const SWAP_MARGINE_RITIRO = 12;
/* (14 nov 2026, audit) quanti blocchi al massimo fra adesso e la scadenza
   del rimborso di un submarine: quattro settimane, ben oltre quelle vere */
const SWAP_SCADENZA_MAX = 4032;
/* (tappa 3) gli stati del submarine: «creato» aspetta i bitcoin
   dell'utente; «pagata» e' la fattura pagata, il fornitore chiede la
   nostra meta' per ritirare; «fatto» quando ha ritirato */
const SWAP_FASI_SUB = {
  'invoice.set': 'creato', 'transaction.mempool': 'bloccato',
  'transaction.confirmed': 'confermato', 'invoice.pending': 'confermato',
  'invoice.paid': 'pagata', 'transaction.claimed': 'fatto',
  'invoice.failedToPay': 'fallito', 'transaction.lockupFailed': 'fallito',
  'swap.expired': 'scaduto'};
/* la rete di una fattura dal suo prefisso (BOLT-11) */
function swapReteFattura(fattura){
  const f = String(fattura || '').trim().toLowerCase();
  return f.startsWith('lnbcrt') ? 'regtest' : f.startsWith('lntb') ? 'testnet'
       : f.startsWith('lnbc') ? 'bitcoin' : '';
}
/* LA VERIFICA DELLA RISPOSTA DEL SUBMARINE (il calco di `validateSubmarine`
   del loro sito, rovesciato: qui il fornitore RITIRA con la sua chiave e
   noi RIMBORSIAMO con la nostra): l'albero rifatto da soli con l'impronta
   DELLA FATTURA, l'indirizzo dalle due chiavi e dall'albero, e quanto
   mandare non piu' del preventivo. null = tutto torna, sennò la ragione. */
function swapVerificaSub(S, rete, r, chiavi, impronta, mandiMax){
  if (!r || typeof r !== 'object' || typeof r.address !== 'string') return 'risposta';
  let loro, albero, atteso, agg;
  const scadenza = Number(r.timeoutBlockHeight);
  if (!(scadenza > 0)) return 'albero';
  try {
    loro = S.hex.decode(String(r.claimPublicKey || ''));
    albero = S.SwapTreeSerializer.deserializeSwapTree(r.swapTree);
    atteso = S.swapTree(false, impronta, loro, chiavi.pubblica, scadenza);
  } catch(e){ return 'albero'; }
  if (!S.compareTrees(albero, atteso)) return 'albero';
  try {
    agg = S.TaprootUtils.tweakMusig(S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]), albero.tree);
  } catch(e){ return 'indirizzo'; }
  if (!swapUguali(S.Scripts.p2trOutput(agg.aggPubkey),
                  swapScriptIndirizzo(S, rete, r.address))) return 'indirizzo';
  if (!(Number(r.expectedAmount) > 0 && Number(r.expectedAmount) <= Number(mandiMax))) return 'importo';
  return null;
}
/* IL RIMBORSO DEL SUBMARINE: la transazione che riporta i bitcoin
   dell'utente dal lockup al SUO indirizzo. Cooperativo (la meta' del
   fornitore, `chiediFirma`) se lo swap e' fallito; dallo script, con la
   sola chiave nostra, dopo la scadenza (`cima` >= timeoutBlockHeight). Il
   lockup e' quello che la rete ci da' in byte: si controlla che porti il
   NOSTRO script. `fee` in sats. Torna {hex, id, cooperativo}. */
function swapRimborsoSub(S, rete, rec, chiavi, lockupHex, destinazione, fee, cooperativo){
  const loro = S.hex.decode(String(rec.claimPublicKey || ''));
  const albero = S.SwapTreeSerializer.deserializeSwapTree(rec.swapTree);
  const keyAgg = S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]);
  const tweaked = S.TaprootUtils.tweakMusig(keyAgg, albero.tree);
  const lockup = S.Transaction.fromRaw(S.hex.decode(String(lockupHex || '')),
    {allowUnknownOutputs: true, allowUnknownInputs: true});
  const atteso = S.Scripts.p2trOutput(tweaked.aggPubkey);
  const uscita = S.detectSwap(tweaked.aggPubkey, lockup, atteso);
  if (uscita === undefined || !swapUguali(uscita.script, atteso))
    throw new Error('nel lockup non c\'e\' il nostro swap');
  const script = swapScriptIndirizzo(S, rete, destinazione);
  if (!script) throw new Error('indirizzo di destinazione non valido');
  if (!(Number(uscita.amount) > Number(fee))) throw new Error('il lockup non copre la fee del rimborso');
  const dettagli = [Object.assign({}, uscita, {
    cooperative: cooperativo, swapTree: albero, privateKey: chiavi.privata,
    type: S.OutputType.Taproot, transactionId: lockup.id,
    internalKey: keyAgg.aggPubkey, preimage: new Uint8Array(0)})];
  const tx = S.constructClaimTransaction(dettagli, script, BigInt(Number(fee)), true,
    cooperativo ? undefined : Number(rec.timeoutBlockHeight), true);
  return {tx: tx, uscita: uscita, tweaked: tweaked, loro: loro};
}

/* ─── 2. LA LIBRERIA, pigra ──────────────────────────────────────────── */
/* -bar2 (27 ott 2026, cantiere cambio-libero): un nome in piu', `swapTree` */
const SWAP_BUNDLE_VER = '5.0.0-bar2';
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

/* ─── 3. IL FORNITORE, direttamente ─────────────────────────────────────
   Una delle due `fetch` di questo file: verso l'`api` del fornitore (la
   seconda, in `swapMempool`, parla con la rete), mai verso il server di
   Barattolo. */
async function swapApiBoltz(base, percorso, corpo){
  base = String(base || '').replace(/\/+$/, '');
  if (!base) throw new Error('fornitore senza indirizzo');
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
/* LA RETE (20 ott 2026, cantiere swap-senza-api): l'API mempool della rete
   del fornitore (`cfg.mempool`, di serie mempool.space, la stessa origine
   dell'on-chain). Da qui il telefono trova il lockup per indirizzo, ne legge
   i byte, la fee del momento, e ci trasmette il ritiro: cosi' il ritiro
   regge anche se l'API del fornitore si spegne. `corpo` = testo da
   trasmettere (POST, text/plain: niente richiesta preventiva CORS). */
async function swapMempool(base, percorso, corpo){
  base = String(base || '').replace(/\/+$/, '');
  if (!base) throw new Error('nessuna rete da cui leggere il lockup');
  const opz = corpo === undefined ? {} : {method: 'POST', body: String(corpo)};
  const r = await fetch(base + percorso, opz);
  const testo = String(await r.text().catch(() => '')).trim();
  if (!r.ok) throw new Error(testo.slice(0, 80) || ('rete: HTTP ' + r.status));
  return testo;
}
/* il lockup di uno swap, cercato sulla rete per indirizzo: l'id della
   transazione che paga `lockupAddress` e non e' ancora spesa, o '' */
async function swapLockupPerIndirizzo(base, indirizzo, minimo){
  if (!indirizzo) return '';
  let uscite;
  try { uscite = JSON.parse(await swapMempool(base, `/address/${encodeURIComponent(indirizzo)}/utxo`)); }
  catch(e){ return ''; }
  if (!Array.isArray(uscite)) return '';
  const buone = uscite.filter(u => u && /^[0-9a-f]{64}$/.test(String(u.txid || '')));
  const piena = buone.find(u => Number(u.value) >= Number(minimo || 0));
  return String(((piena || buone[0]) || {}).txid || '');
}
/* LA SPESA DEL LOCKUP (20 ott 2026, cantiere swap-spesa): quando la rete
   non vede piu' il lockup come non speso, chi l'ha speso? Il lockup si
   trova fra le transazioni dell'indirizzo dello swap, e chi spende la sua
   uscita lo dice `/tx/<id>/outspend/<n>`. null = la rete non ne sa niente
   (non ancora bloccato, non ancora visto, o non risponde); sennò {txid,
   nostro, sats}: `nostro` se la spesa e' una transazione firmata qui
   (`rec.firmati`) o se paga l'indirizzo di chi vende (`destinazione` =
   il suo script in esadecimale, o '' per guardare il solo indirizzo). */
async function swapSpesaDelLockup(base, rec, destinazione){
  if (!rec.lockupAddress) return null;
  let movimenti;
  try { movimenti = JSON.parse(await swapMempool(base, `/address/${encodeURIComponent(rec.lockupAddress)}/txs`)); }
  catch(e){ return null; }
  if (!Array.isArray(movimenti)) return null;
  const esa = /^[0-9a-f]{64}$/;
  for (const t of movimenti) {
    const n = ((t && t.vout) || []).findIndex(o => o && o.scriptpubkey_address === rec.lockupAddress);
    if (n < 0 || !esa.test(String(t.txid || ''))) continue;
    let spesa;
    try { spesa = JSON.parse(await swapMempool(base, `/tx/${t.txid}/outspend/${n}`)); }
    catch(e){ continue; }
    if (!spesa || !spesa.spent || !esa.test(String(spesa.txid || ''))) continue;
    const chi = String(spesa.txid);
    let uscite = ((movimenti.find(x => x && x.txid === chi) || {}).vout);
    if (!uscite) {
      try { uscite = (JSON.parse(await swapMempool(base, `/tx/${chi}`)) || {}).vout; }
      catch(e){ uscite = null; }
    }
    const nostre = (Array.isArray(uscite) ? uscite : []).filter(o => o && (
      (destinazione && String(o.scriptpubkey || '').toLowerCase() === destinazione)
      || (rec.indirizzo && o.scriptpubkey_address === rec.indirizzo)));
    return {txid: chi, nostro: (rec.firmati || []).includes(chi) || nostre.length > 0,
            sats: nostre.reduce((s, o) => s + (Number(o.value) || 0), 0)};
  }
  return null;
}
function swapErrore(tipo, perche){
  const e = new Error(perche || tipo);
  e.tipo = tipo;
  return e;
}

/* ─── 4. LA FABBRICA: un fornitore Boltz dalla sua voce delle leve ──────
   `cfg` = {id, nome, api, referral, rete}, dal server (`swap_fornitori`). */
window.SWAP_TIPI = window.SWAP_TIPI || {};
window.SWAP_TIPI.boltz = function(cfg){
  const api = (percorso, corpo) => swapApiBoltz(cfg.api, percorso, corpo);
  const id = encodeURIComponent;
  return {
    id: cfg.id, nome: cfg.nome, tipo: 'boltz', strade: ['ln-btc', 'btc-ln'],
    /* (tappa 3) un record del submarine (`tipo: 'sub'`) ha le fasi sue; un
       rimborso trasmesso e' «ripreso» qualunque cosa dica il fornitore */
    fase: (stato, rec) => rec && rec.tipo === 'sub'
      ? ((rec.rimborso && rec.rimborso.txid) ? 'ripreso' : (SWAP_FASI_SUB[stato] || 'ignoto'))
      : (SWAP_FASI_BOLTZ[stato] || 'ignoto'),
    /* LA RICHIESTA LIGHTNING DELL'UTENTE (tappa 3): si legge qui, senza
       rete; deve portare ESATTAMENTE la cifra, la rete del fornitore, e
       non essere scaduta (ne' scadere entro dieci minuti: i bitcoin
       vogliono una conferma) */
    fatturaValida(fattura, sats){
      const b = leggiBolt11(fattura);
      if (!b || !b.hash) return 'fattura';
      if (swapReteFattura(fattura) !== (cfg.rete || 'bitcoin')) return 'rete';
      if (b.sats !== Number(sats)) return 'importo';
      if (b.scade < Date.now() / 1000 + 600) return 'scaduta';
      return null;
    },
    /* LA NASCITA ROVESCIATA (tappa 3): la richiesta dell'utente e la
       nostra chiave di RIMBORSO; torna dove mandare i bitcoin e quanti,
       verificato prima di fidarsi */
    async creaSub({parole, indice, preventivo, fattura}){
      let S;
      try { S = await caricaBundleSwap(); }
      catch(e){ throw swapErrore('giu', e.message); }
      const rete = swapRete(S, cfg.rete);
      const chiavi = swapChiavi(S, parole, indice);
      const b = leggiBolt11(fattura);
      if (!b || !b.hash) throw swapErrore('mente', 'fattura');
      const corpo = {from: 'BTC', to: 'BTC', invoice: String(fattura).trim(),
                     refundPublicKey: S.hex.encode(chiavi.pubblica), pairHash: preventivo.hash};
      const codice = String(cfg.referral || '').trim();
      if (codice) corpo.referralId = codice;
      let r;
      try { r = await api('/v2/swap/submarine', corpo); }
      catch(e){ throw swapErrore('giu', e.message); }
      const perche = swapVerificaSub(S, rete, r, chiavi, S.hex.decode(b.hash), preventivo.mandi);
      if (perche) throw swapErrore('mente', perche);
      /* (14 nov 2026, audit) LA SCADENZA DEL RIMBORSO NON PUO' ESSERE
         LONTANA A PIACERE: e' il blocco dopo cui i bitcoin dell'utente
         tornano indietro da soli, e la sceglie il fornitore. Oltre
         SWAP_SCADENZA_MAX blocchi dalla cima della rete lo swap non
         parte. Se la rete non risponde si va come ieri */
      let cima = 0;
      const baseRete = String(cfg.mempool || '').replace(/\/+$/, '');
      if (baseRete) {
        try { cima = Number(await swapMempool(baseRete, '/blocks/tip/height')) || 0; } catch(e){ cima = 0; }
      }
      if (cima > 0 && Number(r.timeoutBlockHeight) - cima > SWAP_SCADENZA_MAX)
        throw swapErrore('mente', 'scadenza');
      return {id: String(r.id), tipo: 'sub', fattura: String(fattura).trim(),
        lockupAddress: r.address, claimPublicKey: r.claimPublicKey,
        swapTree: r.swapTree, timeoutBlockHeight: Number(r.timeoutBlockHeight),
        onchainAmount: Number(r.expectedAmount), mandi: Number(r.expectedAmount),
        ricevi: Number(preventivo.ricevi), bip21: String(r.bip21 || ''),
        impronta: b.hash, stato: 'invoice.set'};
    },
    /* LA NOSTRA META' PER IL RITIRO A DUE (tappa 3): il fornitore ha
       pagato la fattura e vuole ritirare i bitcoin senza lo script; noi
       firmiamo SOLO se il segreto che ci mostra e' quello della fattura
       (sha256 = l'impronta): la prova che ha pagato davvero */
    async aiutaRitiro(rec, parole){
      const S = await caricaBundleSwap();
      const chiavi = swapChiavi(S, parole, rec.indice);
      const det = await api(`/v2/swap/submarine/${id(rec.id)}/claim`);
      const segreto = S.hex.decode(String((det && det.preimage) || ''));
      if (segreto.length !== 32 || S.hex.encode(S.sha256(segreto)) !== String(rec.impronta || ''))
        throw new Error('il segreto non e\' quello della fattura');
      const loro = S.hex.decode(String(rec.claimPublicKey || ''));
      const albero = S.SwapTreeSerializer.deserializeSwapTree(rec.swapTree);
      const tweaked = S.TaprootUtils.tweakMusig(S.Musig.create(chiavi.privata, [loro, chiavi.pubblica]), albero.tree);
      const m = tweaked.message(S.hex.decode(String(det.transactionHash || ''))).generateNonce();
      const sessione = m.aggregateNonces([[loro, S.hex.decode(String(det.pubNonce || ''))]])
        .initializeSession().signPartial();
      await api(`/v2/swap/submarine/${id(rec.id)}/claim`,
        {pubNonce: S.hex.encode(m.publicNonce), partialSignature: S.hex.encode(sessione.ourPartialSignature)});
      return {cooperativo: true};
    },
    /* IL RIMBORSO (tappa 3): i bitcoin tornano a `rec.indirizzo`. Il
       lockup si legge dalla rete (per indirizzo), i byte pure; la fee dal
       mempool del momento. Cooperativo prima; dallo script solo quando la
       rete e' arrivata alla scadenza (`.tipo` = 'presto' prima). */
    async rimborsa(rec, parole){
      const S = await caricaBundleSwap();
      const rete = swapRete(S, cfg.rete);
      const chiavi = swapChiavi(S, parole, rec.indice);
      const base = String(cfg.mempool || '').replace(/\/+$/, '');
      if (!base) throw new Error('nessuna rete da cui leggere il lockup');
      if (!rec.indirizzo) throw new Error('manca l\'indirizzo del rimborso');
      let txid = await swapLockupPerIndirizzo(base, rec.lockupAddress, 0);
      if (!txid) {
        const spesa = await swapSpesaDelLockup(base, rec, '');
        if (spesa && spesa.nostro) return {txid: spesa.txid, cooperativo: null, concluso: true};
        if (spesa) { const e = new Error('il lockup l\'ha speso un\'altra transazione'); e.tipo = 'speso'; e.txid = spesa.txid; throw e; }
        try { txid = String(((await api(`/v2/swap/submarine/${id(rec.id)}/transaction`)) || {}).id || ''); }
        catch(e){ txid = ''; }
      }
      if (!/^[0-9a-f]{64}$/.test(txid)) throw new Error('il lockup non si trova');
      let lockHex = '';
      try { lockHex = await swapMempool(base, `/tx/${txid}/hex`); } catch(e){ lockHex = ''; }
      if (!lockHex) throw new Error('il lockup non si vede sulla rete');
      let fee = 0;
      try { fee = Math.ceil(Number(JSON.parse(await swapMempool(base, '/v1/fees/recommended')).fastestFee) * 160); }
      catch(e){ fee = 0; }
      if (!(fee > 0)) fee = 1000;
      const firma = async (coop) => {
        const p = swapRimborsoSub(S, rete, rec, chiavi, lockHex, rec.indirizzo, fee, coop);
        if (!coop) return {hex: p.tx.hex, id: p.tx.id, cooperativo: false};
        const sighash = p.tx.preimageWitnessV1(0, [p.uscita.script], S.SigHash.DEFAULT, [p.uscita.amount]);
        const m = p.tweaked.message(sighash).generateNonce();
        const r = await api(`/v2/swap/submarine/${id(rec.id)}/refund`,
          {index: 0, pubNonce: S.hex.encode(m.publicNonce), transaction: p.tx.hex});
        const sig = m.aggregateNonces([[p.loro, S.hex.decode(String(r.pubNonce))]])
          .initializeSession().signPartial()
          .addPartial(p.loro, S.hex.decode(String(r.partialSignature))).aggregatePartials();
        p.tx.updateInput(0, {finalScriptWitness: [sig]});
        return {hex: p.tx.hex, id: p.tx.id, cooperativo: true};
      };
      let fatto = null;
      if (!rec.coopRifiutato) { try { fatto = await firma(true); } catch(e){ fatto = null; } }
      if (!fatto) {
        let cima = 0;
        try { cima = Number(await swapMempool(base, '/blocks/tip/height')); } catch(e){ cima = 0; }
        if (!(cima >= Number(rec.timeoutBlockHeight))) throw swapErrore('presto', 'la rete non e\' ancora alla scadenza');
        fatto = await firma(false);
      }
      rec.firmati = (rec.firmati || []).filter(x => x !== fatto.id).concat(fatto.id).slice(-4);
      const esiti = await Promise.allSettled([
        swapMempool(base, '/tx', fatto.hex),
        api('/v2/chain/BTC/transaction', {hex: fatto.hex})]);
      if (esiti.some(e => e.status === 'fulfilled'))
        return {txid: fatto.id, cooperativo: fatto.cooperativo};
      if (fatto.cooperativo) rec.coopRifiutato = true;
      throw esiti[0].reason || esiti[1].reason;
    },
    async nuoveParole(){
      const S = await caricaBundleSwap();
      return S.generateMnemonic(S.wordlist);
    },
    async paroleValide(parole){
      const S = await caricaBundleSwap();
      return parole.split(' ').length === 12 && S.validateMnemonic(parole, S.wordlist);
    },
    async indirizzoValido(indirizzo){
      const S = await caricaBundleSwap();
      return !!swapScriptIndirizzo(S, swapRete(S, cfg.rete), indirizzo);
    },
    /* LA NASCITA: le chiavi dell'indice gia' prenotato, la richiesta col
       codice partner, e la VERIFICA prima di fidarsi */
    async crea({parole, indice, preventivo, indirizzo}){
      let S;
      try { S = await caricaBundleSwap(); }
      catch(e){ throw swapErrore('giu', e.message); }
      const rete = swapRete(S, cfg.rete);
      const chiavi = swapChiavi(S, parole, indice);
      const corpo = {from: 'BTC', to: 'BTC', invoiceAmount: preventivo.fattura,
                     preimageHash: S.hex.encode(chiavi.impronta),
                     claimPublicKey: S.hex.encode(chiavi.pubblica), pairHash: preventivo.hash};
      const codice = String(cfg.referral || '').trim();
      if (codice) corpo.referralId = codice;
      let r;
      try { r = await api('/v2/swap/reverse', corpo); }
      catch(e){ throw swapErrore('giu', e.message); }
      const perche = swapVerifica(S, rete, r, chiavi,
                                  {sats: preventivo.fattura, onchainMin: preventivo.onchain});
      if (perche) throw swapErrore('mente', perche);
      return {id: String(r.id), invoice: r.invoice,
        lockupAddress: r.lockupAddress, refundPublicKey: r.refundPublicKey,
        swapTree: r.swapTree, timeoutBlockHeight: Number(r.timeoutBlockHeight),
        onchainAmount: Number(r.onchainAmount), ricevi: Number(preventivo.ricevi),
        /* (tappa 4) l'impronta del NOSTRO segreto, gia' confrontata con la
           fattura: al server va lei, per il suo controllo prima di pagare */
        impronta: S.hex.encode(chiavi.impronta),
        stato: 'swap.created'};
    },
    async stato(rec){
      const s = await api(`/v2/swap/${id(rec.id)}`);
      return s && s.status ? String(s.status) : null;
    },
    /* IL RITIRO. Un ritiro cooperativo gia' RIFIUTATO alla trasmissione
       (la firma messa insieme col fornitore non reggeva) non si ripete:
       dal giro dopo si ritira dallo script, che dipende solo da noi */
    /* IL LOCKUP E' SULLA RETE? (20 ott 2026, swap-senza-api) Per il giro,
       quando l'API del fornitore non risponde: se la rete vede i bitcoin
       bloccati, si ritira lo stesso. */
    async lockupInRete(rec){
      if (await swapLockupPerIndirizzo(cfg.mempool, rec.lockupAddress, rec.onchainAmount))
        return true;
      /* ...o gia' speso (swap-spesa): il ritiro dira' da chi */
      return !!(await swapSpesaDelLockup(cfg.mempool, rec, ''));
    },
    async ritira(rec, parole){
      const S = await caricaBundleSwap();
      const rete = swapRete(S, cfg.rete);
      const chiavi = swapChiavi(S, parole, rec.indice);
      const base = String(cfg.mempool || '').replace(/\/+$/, '');
      if (!base) throw new Error('nessuna rete da cui leggere il lockup');
      /* IL TERZO CONTROLLO (20 ott 2026, cantiere swap-lockup) e il ritiro
         SENZA LA LORO API (swap-senza-api): il lockup si legge dalla RETE.
         L'id si cerca prima sulla rete, per indirizzo; solo se la rete non
         lo dice si chiede al fornitore. I byte vengono sempre dalla rete:
         se non li conosce, o li conosce diversi, niente ritiro e niente
         segreto, si riprova al giro dopo. */
      let txid = await swapLockupPerIndirizzo(base, rec.lockupAddress, rec.onchainAmount);
      if (!txid) {
        /* LA SPESA DEL LOCKUP (20 ott 2026, cantiere swap-spesa): se la
           rete non lo vede piu' come non speso, si chiede chi l'ha speso.
           Il nostro ritiro (la risposta della trasmissione persa, o un
           altro telefono con le stesse parole): lo swap e' concluso, coi
           sats arrivati, mai un errore. Un altro: errore chiaro, e niente
           segreto a nessuno. */
        let dest = '';
        try { dest = S.hex.encode(S.OutScript.encode(S.Address(rete).decode(rec.indirizzo))); }
        catch(e){ dest = ''; }
        const spesa = await swapSpesaDelLockup(base, rec, dest);
        if (spesa && spesa.nostro)
          return {txid: spesa.txid, cooperativo: null, concluso: true,
                  sats: spesa.sats || Number(rec.ricevi) || 0};
        if (spesa) {
          const e = new Error('il lockup l\'ha speso un\'altra transazione');
          e.tipo = 'speso';
          e.txid = spesa.txid;
          throw e;
        }
        try { txid = String(((await api(`/v2/swap/reverse/${id(rec.id)}/transaction`)) || {}).id || ''); }
        catch(e){ txid = ''; }
      }
      if (!/^[0-9a-f]{64}$/.test(txid)) throw new Error('il lockup non si trova');
      let ricevi = Number(rec.ricevi);
      if (!(ricevi > 0)) {
        /* uno swap recuperato non ha il preventivo: la fee del ritiro
           dalle tariffe di adesso; se il fornitore tace, da quella della
           rete (160 vbyte bastano anche al ritiro dallo script) */
        let fee;
        try {
          const tar = await api('/v2/swap/reverse');
          fee = Number(tar.BTC.BTC.fees.minerFees.claim);
        } catch(e){
          const f = JSON.parse(await swapMempool(base, '/v1/fees/recommended'));
          fee = Math.ceil(Number(f.fastestFee) * 160);
        }
        ricevi = Number(rec.onchainAmount) - fee;
      }
      let lockHex = '';
      try { lockHex = await swapMempool(base, `/tx/${txid}/hex`); } catch(e){ lockHex = ''; }
      if (!lockHex) throw new Error('il lockup non si vede sulla rete');
      if (S.Transaction.fromRaw(S.hex.decode(lockHex),
            {allowUnknownOutputs: true, allowUnknownInputs: true}).id !== txid)
        throw new Error('la rete risponde con un altro lockup');
      /* UNA CONFERMA E UN MARGINE PRIMA DEL SEGRETO (14 nov 2026, cantiere
         audit-pagamenti-2, dal secondo audit di sicurezza): il gemello di
         quel che fa il server dal primo audit. Il segreto partiva appena
         il lockup era in mempool, e senza guardare quanto mancava alla
         scadenza: un lockup mai confermato (sostituito, o scaduto) e il
         segreto in mano al fornitore = Lightning incassato da lui e
         bitcoin mai arrivati. Ora il lockup dev'essere CONFERMATO e la
         scadenza lontana almeno SWAP_MARGINE_RITIRO blocchi; se no si
         aspetta il giro dopo (un errore che non e' un guasto). Vicino
         alla scadenza non si ritira piu': la fattura Lightning, mai
         incassata, torna indietro da sola. */
      const attendi = async () => {
        let conferma = null;
        try { conferma = (JSON.parse(await swapMempool(base, `/tx/${txid}`)) || {}).status; }
        catch(e){ conferma = null; }
        if (!conferma || conferma.confirmed !== true) {
          const e = new Error('aspetto la prima conferma del blocco del fornitore');
          e.tipo = 'attesa';
          throw e;
        }
        const scade = Number(rec.timeoutBlockHeight) || 0;
        if (scade > 0) {
          let cima = 0;
          try { cima = Number(await swapMempool(base, '/blocks/tip/height')); } catch(e){ cima = 0; }
          if (!(cima > 0)) {
            const e = new Error('la rete non dice l\'altezza: riprovo fra poco');
            e.tipo = 'attesa';
            throw e;
          }
          if (scade - cima < SWAP_MARGINE_RITIRO) {
            const e = new Error('troppo vicino alla scadenza: il ritiro non parte, '
                                + 'i sats Lightning tornano da soli');
            e.tipo = 'scadenza';
            throw e;
          }
        }
      };
      const chiediFirma = (txHex, nonce) => api(
        `/v2/swap/reverse/${id(rec.id)}/claim`,
        {index: 0, preimage: S.hex.encode(chiavi.segreto), pubNonce: nonce, transaction: txHex});
      const fatto = await swapRitiro(S, rete, rec, chiavi, lockHex, rec.indirizzo, ricevi,
                                     chiediFirma, !rec.coopRifiutato, attendi);
      /* le transazioni firmate qui si ricordano PRIMA di trasmetterle: se
         la risposta si perde, il giro dopo le riconosce nella spesa */
      rec.firmati = (rec.firmati || []).filter(x => x !== fatto.id).concat(fatto.id).slice(-4);
      /* LA TRASMISSIONE, su due strade insieme: la rete e il fornitore (il
         calco del rimborso della loro web app). Basta che una la prenda. */
      const esiti = await Promise.allSettled([
        swapMempool(base, '/tx', fatto.hex),
        api('/v2/chain/BTC/transaction', {hex: fatto.hex})]);
      if (esiti.some(e => e.status === 'fulfilled'))
        return {txid: fatto.id, cooperativo: fatto.cooperativo};
      if (fatto.cooperativo) rec.coopRifiutato = true;
      throw esiti[0].reason || esiti[1].reason;
    },
    /* IL RECUPERO dalla xpub di radice. Il contatore riparte DOPO
       l'indice piu' alto trovato: mai un segreto riusato */
    async recupera(parole){
      const S = await caricaBundleSwap();
      const rete = swapRete(S, cfg.rete);
      const trovati = await api('/v2/swap/restore', {xpub: swapXpub(S, parole)});
      let prossimo = 0;
      const swap = [];
      for (const s of (Array.isArray(trovati) ? trovati : [])) {
        /* (tappa 3) i submarine, con la chiave di rimborso: da rimborsare
           se falliti, con l'indirizzo che l'utente scrivera' */
        const rd = s && s.type === 'submarine' && s.refundDetails;
        if (rd && s.from === 'BTC' && s.to === 'BTC') {
          prossimo = Math.max(prossimo, Number(rd.keyIndex) + 1);
          swap.push({id: String(s.id), tipo: 'sub', indice: Number(rd.keyIndex),
            lockupAddress: rd.lockupAddress, claimPublicKey: rd.serverPublicKey,
            swapTree: rd.tree, timeoutBlockHeight: Number(rd.timeoutBlockHeight),
            onchainAmount: Number(rd.amount) || 0, ricevi: null, bloccato: true,
            stato: String(s.status || ''), creato: (Number(s.createdAt) || 0) * 1000});
          continue;
        }
        const d = s && s.claimDetails;
        if (!d || s.type !== 'reverse' || s.from !== 'BTC' || s.to !== 'BTC') continue;
        prossimo = Math.max(prossimo, Number(d.keyIndex) + 1);
        /* il contatore sale comunque (mai un segreto riusato), ma uno
           swap che non torna coi NOSTRI pezzi non diventa riscattabile */
        let perche;
        try {
          perche = swapVerificaRitrovato(S, rete, d, swapChiavi(S, parole, Number(d.keyIndex)),
                                         s.preimageHash);
        } catch(e){ perche = 'chiavi'; }
        if (perche) continue;
        swap.push({id: String(s.id), indice: Number(d.keyIndex),
          lockupAddress: d.lockupAddress, refundPublicKey: d.serverPublicKey,
          swapTree: d.tree, timeoutBlockHeight: Number(d.timeoutBlockHeight),
          onchainAmount: Number(d.amount) || 0, ricevi: null,
          stato: String(s.status || ''), creato: (Number(s.createdAt) || 0) * 1000});
      }
      return {swap: swap, prossimo: prossimo};
    }
  };
};
