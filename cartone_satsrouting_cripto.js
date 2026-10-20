/* LA CRITTOGRAFIA DEL SATS ROUTING DI CARTONE (20 ott 2026, cantiere
   swap-telefono, tappa 3).

   Il cartone (`cartone_satsrouting.py`) fa la parte di SATS Routing anche
   nella creazione di uno swap: la sua chiave, l'albero, l'indirizzo dove
   blocca i bitcoin, la fattura con l'impronta del segreto del telefono, la
   transazione di lockup, la sua meta' della firma MuSig2 del ritiro
   cooperativo, e il controllo della transazione di ritiro che gli si
   chiede di trasmettere. Tutto con la STESSA libreria del telefono
   (`vendor/swap.bundle.js`), qui in node: un SATS Routing che mente lo
   simula il cartone cambiando un pezzo, mai questa crittografia.

   Una chiamata = un processo: JSON sullo stdin ({op, ...}), JSON sullo
   stdout. Le chiavi del cartone nascono a caso a ogni swap: nel repo non
   c'e' nessuna chiave, e nessun esadecimale da 64.

   La firma della transazione di ritiro NON la giudica questo file: torna
   l'impronta firmata, la chiave e la firma, e il cartone le verifica in
   Python puro (BIP-340), con un'aritmetica che non e' quella del bundle. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const {randomBytes} = require('crypto');

const S = vm.runInThisContext(
  fs.readFileSync(path.join(__dirname, 'vendor', 'swap.bundle.js'), 'utf8') + ';BarattoloSwap');
const RETI = {
  bitcoin: S.NETWORK, testnet: S.TEST_NETWORK,
  regtest: {bech32: 'bcrt', pubKeyHash: 0x6f, scriptHash: 0xc4, wif: 0xef}};
const PREFISSO_FATTURA = {bitcoin: 'lnbc', testnet: 'lntb', regtest: 'lnbcrt'};
const h = S.hex;

/* ─── la fattura BOLT-11, quanto basta: importo, impronta, scadenza; la
   firma e' di zeri (il telefono non la guarda: guarda importo e impronta) */
const ALF = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';
function controllo(hrp, dati){
  const GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
  const v = [];
  for (const c of hrp) v.push(c.charCodeAt(0) >> 5);
  v.push(0);
  for (const c of hrp) v.push(c.charCodeAt(0) & 31);
  v.push(...dati, 0, 0, 0, 0, 0, 0);
  let chk = 1;
  for (const x of v) {
    const b = chk >>> 25;
    chk = ((chk & 0x1ffffff) << 5) ^ x;
    for (let i = 0; i < 5; i++) if ((b >> i) & 1) chk ^= GEN[i];
  }
  chk ^= 1;
  const out = [];
  for (let i = 0; i < 6; i++) out.push((chk >> (5 * (5 - i))) & 31);
  return out;
}
function a5(byte){
  let acc = 0, bit = 0;
  const out = [];
  for (const b of byte) {
    acc = (acc << 8) | b; bit += 8;
    while (bit >= 5) { bit -= 5; out.push((acc >> bit) & 31); }
  }
  if (bit) out.push((acc << (5 - bit)) & 31);
  return out;
}
function num5(n, quanti){
  const out = [];
  for (let i = quanti - 1; i >= 0; i--) out.push(Math.floor(n / 32 ** i) % 32);
  return out;
}
function fattura(rete, sats, impronta){
  const hrp = (PREFISSO_FATTURA[rete] || 'lnbc') + (Number(sats) * 10) + 'n';
  const p = a5(impronta);
  const dati = [...num5(Math.floor(Date.now() / 1000), 7),
                1, ...num5(p.length, 2), ...p,
                6, ...num5(3, 2), ...num5(3600, 3),
                ...Array(104).fill(0)];
  return hrp + '1' + [...dati, ...controllo(hrp, dati)].map(x => ALF[x]).join('');
}

/* ─── i pezzi di uno swap, rifatti dai dati che il cartone conserva */
function pezzi(d){
  const loro = h.decode(d.serverPriv);
  const lui = h.decode(d.claimPublicKey);
  const albero = S.SwapTreeSerializer.deserializeSwapTree(d.swapTree);
  const agg = S.TaprootUtils.tweakMusig(
    S.Musig.create(loro, [pubDa(loro), lui]),
    albero.tree);
  return {loro, lui, albero, agg, script: S.Scripts.p2trOutput(agg.aggPubkey)};
}
/* la chiave pubblica compressa di una privata, senza @noble: un HDKey con
   quella privata come chiave (il percorso non serve) */
function pubDa(priv){
  return new S.HDKey({privateKey: priv}).publicKey;
}

const OP = {
  /* la nascita di uno swap: chiave del cartone, albero, indirizzo, fattura */
  crea(d){
    const rete = RETI[d.rete] ? d.rete : 'bitcoin';
    const priv = randomBytes(32);
    const pub = pubDa(priv);
    const impronta = h.decode(d.preimageHash);
    const lui = h.decode(d.claimPublicKey);
    const scadenza = Number(d.timeoutBlockHeight);
    const albero = S.reverseSwapTree(false, impronta, lui, pub, scadenza);
    const agg = S.TaprootUtils.tweakMusig(S.Musig.create(priv, [pub, lui]), albero.tree);
    const indirizzo = S.Address(RETI[rete]).encode(S.OutScript.decode(S.Scripts.p2trOutput(agg.aggPubkey)));
    return {serverPriv: h.encode(priv), refundPublicKey: h.encode(pub),
            swapTree: S.SwapTreeSerializer.serializeSwapTree(albero),
            lockupAddress: indirizzo,
            invoice: fattura(rete, d.invoiceAmount, impronta)};
  },
  /* i pezzi d'appoggio per le bugie: una fattura qualsiasi, un albero con
     un'altra scadenza, un indirizzo di un'altra chiave */
  fattura(d){ return {invoice: fattura(d.rete, d.sats, d.impronta ? h.decode(d.impronta) : randomBytes(32))}; },
  albero_altro(d){
    const p = pezzi(d);
    const altro = S.reverseSwapTree(false, h.decode(d.preimageHash), p.lui, pubDa(p.loro),
                                    Number(d.timeoutBlockHeight) + 1);
    return {swapTree: S.SwapTreeSerializer.serializeSwapTree(altro)};
  },
  indirizzo_altro(d){
    const p = pezzi(d);
    const finto = pubDa(randomBytes(32));
    const agg = S.TaprootUtils.tweakMusig(S.Musig.create(p.loro, [pubDa(p.loro), finto]), p.albero.tree);
    const rete = RETI[d.rete] ? d.rete : 'bitcoin';
    return {lockupAddress: S.Address(RETI[rete]).encode(S.OutScript.decode(S.Scripts.p2trOutput(agg.aggPubkey)))};
  },
  /* il lockup: una transazione che paga l'indirizzo dello swap */
  lockup(d){
    const p = pezzi(d);
    const tx = new S.Transaction({allowUnknownInputs: true, allowUnknownOutputs: true});
    tx.addInput({txid: randomBytes(32), index: 0});
    /* (20 ott 2026, swap-lockup) la variante bugiarda: la stessa chiave
       MuSig, ma in un'uscita p2sh — una delle forme che `detectSwap` della
       5.0.0 accettava */
    const script = d.variante === 'altro_script' ? S.Scripts.p2shOutput(p.agg.aggPubkey) : p.script;
    tx.addOutput({script: script, amount: BigInt(d.onchainAmount)});
    const hex = h.encode(tx.unsignedTx);
    return {hex: hex, id: S.Transaction.fromRaw(tx.unsignedTx, {allowUnknownInputs: true, allowUnknownOutputs: true}).id};
  },
  /* la meta' della firma del cartone per il ritiro cooperativo */
  firma(d){
    const p = pezzi(d);
    const tx = S.Transaction.fromRaw(h.decode(d.transaction), {allowUnknownOutputs: true});
    const sh = tx.preimageWitnessV1(0, [p.script], S.SigHash.DEFAULT, [BigInt(d.onchainAmount)]);
    const m = p.agg.message(sh).generateNonce();
    const firmato = m.aggregateNonces([[p.lui, h.decode(d.pubNonce)]]).initializeSession().signPartial();
    return {pubNonce: h.encode(m.publicNonce), partialSignature: h.encode(firmato.ourPartialSignature)};
  },
  /* la transazione di ritiro da trasmettere: cosa spende, dove paga, e
     cosa e' stato firmato con quale chiave (la firma la giudica Python) */
  controlla(d){
    const p = pezzi(d);
    const lock = S.Transaction.fromRaw(h.decode(d.lockupHex), {allowUnknownInputs: true, allowUnknownOutputs: true});
    const tx = S.Transaction.fromRaw(h.decode(d.hex), {allowUnknownOutputs: true});
    const ing = tx.getInput(0);
    const testimone = ing.finalScriptWitness || [];
    const uscite = [];
    for (let i = 0; i < tx.outputsLength; i++) {
      const u = tx.getOutput(i);
      uscite.push({sats: Number(u.amount), script: h.encode(u.script)});
    }
    const base = {txid: tx.id, ingressi: tx.inputsLength,
                  spende: h.encode(ing.txid) === lock.id && ing.index === 0, uscite: uscite};
    const quanto = BigInt(d.onchainAmount);
    if (testimone.length === 1) {
      const sh = tx.preimageWitnessV1(0, [p.script], S.SigHash.DEFAULT, [quanto]);
      const x = p.agg.aggPubkey.length === 33 ? p.agg.aggPubkey.slice(1) : p.agg.aggPubkey;
      return Object.assign(base, {via: 'cooperativo', impronta: h.encode(sh),
        chiave: h.encode(x), firma: h.encode(testimone[0])});
    }
    if (testimone.length === 4) {
      const foglia = p.albero.claimLeaf.output;
      const sh = tx.preimageWitnessV1(0, [p.script], S.SigHash.DEFAULT, [quanto], -1, foglia, 0xc0);
      return Object.assign(base, {via: 'script', impronta: h.encode(sh),
        chiave: h.encode(p.lui.slice(1)), firma: h.encode(testimone[0]),
        segreto: h.encode(testimone[1]),
        foglia: h.encode(testimone[2]) === h.encode(foglia)});
    }
    return Object.assign(base, {via: 'storta'});
  },
  /* il recupero: le chiavi pubbliche m/44/0/0/0/i di una xpub di radice */
  chiavi_xpub(d){
    const radice = S.HDKey.fromExtendedKey(String(d.xpub));
    const out = [];
    for (let i = 0; i < Number(d.quante || 20); i++)
      out.push(h.encode(radice.derive(`m/44/0/0/0/${i}`).publicKey));
    return {chiavi: out};
  }
};

let ingresso = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => { ingresso += c; });
process.stdin.on('end', () => {
  let r;
  try {
    const d = JSON.parse(ingresso);
    if (!Object.prototype.hasOwnProperty.call(OP, d.op)) throw new Error('op sconosciuta');
    r = OP[d.op](d);
  } catch(e){ r = {errore: String((e && e.message) || e)}; }
  process.stdout.write(JSON.stringify(r));
});
