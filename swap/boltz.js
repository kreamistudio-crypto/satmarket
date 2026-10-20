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
     ritira(rec, parole)             -> {txid, cooperativo}
     recupera(parole)                -> {swap: [...], prossimo}
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
   delle altre tre forme che `detectSwap` della 5.0.0 accettava (la
   correzione di boltz-core #196, che il bundle ora porta, e in piu' il
   nostro confronto: le due difese si sommano); (2) l'importo non e' meno
   di quello promesso alla nascita (`rec.onchainAmount`). Il terzo
   controllo — il lockup esiste davvero sulla rete — lo fa `ritira`,
   prima di arrivare qui. */
async function swapRitiro(S, rete, rec, chiavi, lockupHex, destinazione, ricevi, chiediFirma, cooperativo){
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

/* ─── 3. IL FORNITORE, direttamente ─────────────────────────────────────
   Una delle due `fetch` di questo file: verso l'`api` del fornitore (la
   seconda, in `ritira`, legge il lockup da mempool), mai verso il server
   di Barattolo. */
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
    id: cfg.id, nome: cfg.nome, tipo: 'boltz', strade: ['ln-btc'],
    fase: stato => SWAP_FASI_BOLTZ[stato] || 'ignoto',
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
        stato: 'swap.created'};
    },
    async stato(rec){
      const s = await api(`/v2/swap/${id(rec.id)}`);
      return s && s.status ? String(s.status) : null;
    },
    /* IL RITIRO. Un ritiro cooperativo gia' RIFIUTATO alla trasmissione
       (la firma messa insieme col fornitore non reggeva) non si ripete:
       dal giro dopo si ritira dallo script, che dipende solo da noi */
    async ritira(rec, parole){
      const S = await caricaBundleSwap();
      const rete = swapRete(S, cfg.rete);
      const chiavi = swapChiavi(S, parole, rec.indice);
      let ricevi = Number(rec.ricevi);
      if (!(ricevi > 0)) {
        /* uno swap recuperato non ha il preventivo: la fee del ritiro
           dalle tariffe di adesso */
        const tar = await api('/v2/swap/reverse');
        ricevi = Number(rec.onchainAmount) - Number(tar.BTC.BTC.fees.minerFees.claim);
      }
      /* IL TERZO CONTROLLO (20 ott 2026, cantiere swap-lockup): il lockup
         si legge dalla RETE, non dal fornitore. Dal fornitore si prende
         solo l'id della transazione; i suoi byte li da' mempool (l'API
         della rete del fornitore, `cfg.mempool`, la stessa scelta per
         l'on-chain). Se la rete non la conosce, o la conosce diversa,
         niente ritiro e niente segreto: si riprova al giro dopo. Senza un
         indirizzo di mempool non si ritira affatto. */
      const lock = await api(`/v2/swap/reverse/${id(rec.id)}/transaction`);
      const base = String(cfg.mempool || '').replace(/\/+$/, '');
      if (!base) throw new Error('nessuna rete da cui leggere il lockup');
      const txid = String((lock && lock.id) || '');
      if (!/^[0-9a-f]{64}$/.test(txid)) throw new Error('il lockup non ha un id');
      const vista = await fetch(`${base}/tx/${txid}/hex`);
      const lockHex = vista.ok ? String(await vista.text()).trim() : '';
      if (!lockHex) throw new Error('il lockup non si vede sulla rete');
      if (S.Transaction.fromRaw(S.hex.decode(lockHex),
            {allowUnknownOutputs: true, allowUnknownInputs: true}).id !== txid)
        throw new Error('la rete risponde con un altro lockup');
      const chiediFirma = (txHex, nonce) => api(
        `/v2/swap/reverse/${id(rec.id)}/claim`,
        {index: 0, preimage: S.hex.encode(chiavi.segreto), pubNonce: nonce, transaction: txHex});
      const fatto = await swapRitiro(S, rete, rec, chiavi, lockHex, rec.indirizzo, ricevi,
                                     chiediFirma, !rec.coopRifiutato);
      try {
        const inviata = await api('/v2/chain/BTC/transaction', {hex: fatto.hex});
        return {txid: String((inviata && inviata.id) || fatto.id), cooperativo: fatto.cooperativo};
      } catch(e){
        if (fatto.cooperativo) rec.coopRifiutato = true;
        throw e;
      }
    },
    /* IL RECUPERO dalla xpub di radice. Il contatore riparte DOPO
       l'indice piu' alto trovato: mai un segreto riusato */
    async recupera(parole){
      const S = await caricaBundleSwap();
      const trovati = await api('/v2/swap/restore', {xpub: swapXpub(S, parole)});
      let prossimo = 0;
      const swap = [];
      for (const s of (Array.isArray(trovati) ? trovati : [])) {
        const d = s && s.claimDetails;
        if (!d || s.type !== 'reverse' || s.from !== 'BTC' || s.to !== 'BTC') continue;
        prossimo = Math.max(prossimo, Number(d.keyIndex) + 1);
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
