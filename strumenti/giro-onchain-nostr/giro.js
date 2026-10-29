/* Il copione: due browser veri (chi compra, chi vende) con account Nostr
   non admin, contro il server vero. Le firme le mette il codice vero
   della Mini App. Solo la rete Bitcoin e' finta (giro_server.py). */
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = process.argv[2] || 'http://127.0.0.1:8099';
const OUT = process.argv[3] || '.';
const ADMIN = {'X-Tg-Init-Data': 'collaudo:999:Admin', 'Content-Type': 'application/json'};
const esiti = [];
function prova(nome, atteso, avuto){
  const ok = JSON.stringify(atteso) === JSON.stringify(avuto);
  esiti.push({nome, ok, atteso, avuto});
  console.log((ok ? '  ✓ ' : '  ✗ ') + nome + (ok ? '' : `\n      atteso: ${JSON.stringify(atteso)}\n      avuto:  ${JSON.stringify(avuto)}`));
}
async function api(path, opt = {}){
  const r = await fetch(BASE + path, opt);
  const t = await r.text();
  let j; try { j = JSON.parse(t); } catch(e){ j = {raw: t.slice(0, 200)}; }
  return {status: r.status, ...(typeof j === 'object' && j ? {j} : {j: {}})};
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function nuovoBrowser(b, nome){
  const ctx = await b.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2});
  await ctx.routeWebSocket('**', ws => { ws.close(); });   // mai relay veri
  const p = await ctx.newPage();
  p.errs = [];
  p.on('pageerror', e => p.errs.push(nome + ': ' + String(e).slice(0, 200)));
  p.on('console', m => { if (m.type() === 'error') p.errs.push(nome + ' [console]: ' + m.text().slice(0, 200)); });
  p.nome = nome;
  return p;
}

async function entra(p){
  await p.goto(BASE + '/miniapp.html');
  await p.waitForFunction(() => typeof entraConNostr === 'function' && typeof caricaNostrTools === 'function');
  const {nsec, npub} = await p.evaluate(async () => {
    await caricaNostrTools();
    const NT = window.NostrTools;
    const sk = NT.generateSecretKey();
    return {nsec: NT.nip19.nsecEncode(sk), npub: NT.nip19.npubEncode(NT.getPublicKey(sk))};
  });
  await p.evaluate(async (nsec) => {
    const f = await firmatarioNsec(nsec);
    try { await entraConNostr(f); } finally { try { f.chiudi(); } catch(e){} }
  }, nsec).catch(e => console.log('   (login: ' + e.message.slice(0, 120) + ')'));
  await p.waitForLoadState('load');
  await p.waitForFunction(() => typeof myTgId !== 'undefined' && myTgId && WEB, null, {timeout: 20000});
  const me = await p.evaluate(async () => {
    for (let i = 0; i < 40; i++) {
      const r = await fetch(`${API_BASE}/onchain/prova`, {headers: {'X-Tg-Init-Data': authHdr()}});
      const d = r.ok ? await r.json() : {};
      if (d.mia_xpub) return {tgId: myTgId, myOnchain, xpub: d.mia_xpub, nato: typeof onchainNato !== 'undefined' ? onchainNato : null};
      await new Promise(r => setTimeout(r, 500));
    }
    return {tgId: myTgId, myOnchain, xpub: null};
  });
  const nome = npub.slice(0, 10) + '…' + npub.slice(-4);
  const u = ((await api('/_giro/utenti')).j.utenti || []).find(x => x.nome === nome);
  return {nsec, npub, ...me, tgId: u ? u.tgId || u.tg_id : me.tgId, tgIdJs: me.tgId};
}

async function compraOnchain(p, annuncioId){
  return p.evaluate(async (aid) => {
    const r = await fetch(`${API_BASE}/listings`, {headers: {'X-Tg-Init-Data': authHdr()}});
    const tutti = await r.json();
    const lista = Array.isArray(tutti) ? tutti : (tutti.listings || tutti.annunci || []);
    const grezzo = lista.find(x => x.id === aid);
    if (!grezzo) throw new Error('annuncio ' + aid + ' non in vetrina: ' + JSON.stringify(lista.map(x => x.id)));
    const l = mapListing(grezzo);
    listings = lista.map(mapListing); currentListing = l; qtaScelta = 1;
    acqDati = {tipo: 'mono', annuncioId: aid, qta: 1, via: 'ritiro'};
    await startBuy();
    await new Promise(r => setTimeout(r, 1500));
    const ln = el('payInvoice') ? el('payInvoice').textContent.slice(0, 20) : '';
    await payPassaA('onchain');
    for (let i = 0; i < 40 && !(payOc && payOc.o); i++) await new Promise(r => setTimeout(r, 250));
    const o = payOc && payOc.o;
    return {ln, metodo: acqMetodo, nota: (el('payMetodoNota') || {}).textContent, pronto: payOcPronto, ordine: o ? {id: o.id, stato: o.stato, indirizzo: o.indirizzo && o.indirizzo.indirizzo,
      prezzo: o.prezzo_sats, margine: o.margine_sats, importo: o.importo_sats, quota: o.quota_sats, incasso: o.incasso,
      descrittore: o.indirizzo && o.indirizzo.descrittore} : null,
      qrTesto: el('payQr') ? (el('payQr').getAttribute('data-testo') || '') : ''};
  }, annuncioId);
}

(async () => {
  const b = await chromium.launch();
  console.log('\n[preparazione: leve e chiave di Barattolo]');
  let r = await api('/api/admin/leve/ONCHAIN_SOLO_ADMIN', {method: 'POST', headers: ADMIN, body: JSON.stringify({valore: false})});
  prova('la porticina «solo admin» si spegne dal pannello', 200, r.status);
  r = await api('/api/admin/onchain/chiave', {method: 'POST', headers: ADMIN});
  prova('la chiave di Barattolo nasce sul server (una volta)', true, r.status === 200 || r.status === 409);
  r = await api('/api/admin/onchain/chiave', {headers: ADMIN});
  console.log('   chiave di Barattolo:', JSON.stringify(r.j).slice(0, 200));

  console.log('\n[due account Nostr non admin]');
  const C = await nuovoBrowser(b, 'compra'), V = await nuovoBrowser(b, 'vende');
  const c = await entra(C), v = await entra(V);
  prova('chi compra entra con Nostr, e l\'on-chain si accende da solo', [true, true], [!!c.tgId && c.tgId !== 999, !!c.xpub]);
  prova('chi vende entra con Nostr, e l\'on-chain si accende da solo', [true, true], [!!v.tgId && v.tgId !== 999, !!v.xpub]);
  prova('sono due account diversi, nessuno admin', true, c.tgId !== v.tgId && !['999','111','222'].includes(String(c.tgId)));
  prova('l\'id Nostr e\' lo stesso nel browser e sul server (niente arrotondamento)', [true, true], [String(c.tgIdJs) === String(c.tgId), String(v.tgIdJs) === String(v.tgId)]);
  console.log('   compra:', c.tgId, 'nato:', c.nato, '| vende:', v.tgId, 'nato:', v.nato);

  // chi vende sceglie dove ricevere: un indirizzo del SUO wallet (finto Sparrow)
  const DEST = 'tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx';
  const dest = await V.evaluate(async (dest) => {
    go('profilo');
    await new Promise(r => setTimeout(r, 500));
    renderIncassoOnchainProfilo();
    const campo = el('ocProfValore');
    if (!campo) return {errore: 'campo assente: myOnchain=' + myOnchain};
    campo.value = dest;
    await onchainIncassoSalva(el('ocProfSalva'), 'ocProf');
    const me = await (await fetch(`${API_BASE}/me`, {headers: {'X-Tg-Init-Data': authHdr()}})).json();
    return {incasso: me.onchain_incasso, esito: (el('ocProfEsito') || {}).textContent};
  }, DEST);
  prova('chi vende salva «dove ricevo» firmato dal suo seme', 'indirizzo', dest.incasso);
  if (dest.errore) console.log('   ', dest.errore);

  console.log('\n[due annunci di chi vende, e la faucet a chi compra]');
  const a1 = (await api('/_giro/annuncio', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({venditore: v.tgId, titolo: 'Lampada vintage', prezzo: 30000})})).j.id;
  const a2 = (await api('/_giro/annuncio', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({venditore: v.tgId, titolo: 'Radio a valvole', prezzo: 20000})})).j.id;
  r = await api('/_giro/faucet', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({sats: 200000})});
  prova('la faucet mette 200.000 sats nel wallet esterno di chi compra', true, r.j.ok);

  console.log('\n[GIRO 1: paga on-chain, conferma, due firme, sats a chi vende]');
  const g1 = await compraOnchain(C, a1);
  prova('il foglio apre ⚡ e al tocco su ⛓️ nasce l\'ordine 2-di-3 in attesa', ['onchain', 'attesa', true],
        [g1.metodo, g1.ordine && g1.ordine.stato, !!(g1.ordine && g1.ordine.indirizzo && g1.ordine.indirizzo.startsWith('tb1q'))]);
  console.log('   ordine', JSON.stringify(g1.ordine));
  await C.screenshot({path: OUT + '/g1-cassa.png'});
  r = await api('/_giro/paga', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({a: g1.ordine.indirizzo, sats: g1.ordine.importo})});
  prova('il wallet esterno paga l\'indirizzo 2-di-3 (importo esatto)', true, r.j.ok);
  const pagato = await C.evaluate(async (oid) => {
    await payOcControlla();
    await new Promise(r => setTimeout(r, 1500));
    const os = await onchainLeggiOrdini();
    const o = os.find(x => x.id === oid);
    await loadOrders();
    const ord = orders.find(x => x.onchain && x.onchain.id === o.id);
    return {stato: o.stato, ordine_id: o.ordine_id, vero: ord ? {id: ord.id, state: ord.state, role: ord.role} : null, foglioAperto: el('paySheet').classList.contains('open')};
  }, g1.ordine.id);
  console.log('   dopo «Ho pagato»: foglio aperto =', pagato.foglioAperto);
  prova('«Ho pagato»: pagato, e in «Ordini» c\'e\' l\'ordine di sempre, locked', ['pagato', 'locked', 'buyer'],
        [pagato.stato, pagato.vero && pagato.vero.state, pagato.vero && pagato.vero.role]);
  await C.evaluate(() => { closeSheet(); go('affari'); renderOrders(); });
  await sleep(500);
  await C.screenshot({path: OUT + '/g1-ordini-compra.png'});
  const lib = await C.evaluate(async (oid) => {
    await loadOrders();
    openOrder(oid);
    await new Promise(r => setTimeout(r, 500));
    const btn = document.createElement('button');
    await onchainLiberaDallOrdine(btn, currentOrder);
    const os = await onchainLeggiOrdini();
    const o = os.find(x => x.ordine_id === oid);
    return {proposta: o.proposta ? {verso: o.proposta.verso, mia: o.proposta.mia} : null, stato: o.stato};
  }, pagato.vero.id);
  prova('chi compra conferma: la PRIMA firma (la sua) e\' sul server', {verso: 'venditore', mia: true}, lib.proposta);
  await C.screenshot({path: OUT + '/g1-ordine-compra.png'});
  const cof = await V.evaluate(async () => {
    /* la strada vera dell'app all'apertura: legge gli ordini e co-firma */
    await onchainLeggiOrdini();
    const parole = onchainSemeLocale();
    const fatte = await onchainCofirmeInAttesa(parole);
    const os = await onchainLeggiOrdini();
    await loadOrders();
    const o = os[0];
    const ord = orders.find(x => x.onchain && x.onchain.id === o.id);
    return {fatte, stato: o.stato, txid: o.txid_uscita, vero: ord && ord.state};
  });
  prova('chi vende apre l\'app: la SECONDA firma da sola, transazione in rete, ordine released',
        ['rilasciato', true, 'released'], [cof.stato, !!cof.txid, cof.vero]);
  console.log('   co-firme:', JSON.stringify(cof.fatte));
  let cat = (await api('/_giro/catena')).j;
  const tx1 = cat.giornale.find(g => g.tx === cof.txid);
  prova('in rete: il prezzo va all\'indirizzo scelto da chi vende, la commissione sta nel margine',
        [true, true], [!!tx1 && tx1.uscite.some(u => u[0] === DEST && u[1] === g1.ordine.prezzo), !!tx1 && tx1.fee <= g1.ordine.margine]);
  console.log('   tx:', JSON.stringify(tx1));
  await V.evaluate(() => { go('affari'); renderOrders(); });
  await sleep(500);
  await V.screenshot({path: OUT + '/g1-ordini-vende.png'});

  console.log('\n[GIRO 2: paga, poi disputa; un admin decide; Barattolo firma; chi vince co-firma]');
  const g2 = await compraOnchain(C, a2);
  prova('il secondo ordine 2-di-3 nasce', 'attesa', g2.ordine && g2.ordine.stato);
  r = await api('/_giro/paga', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({a: g2.ordine.indirizzo, sats: g2.ordine.importo})});
  prova('pagato dal wallet esterno', true, r.j.ok);
  const p2 = await C.evaluate(async (oid) => {
    await payOcControlla();
    await new Promise(r => setTimeout(r, 1500));
    await loadOrders();
    const ord = orders.find(x => x.onchain && x.onchain.id === oid);
    closeSheet();
    const d = await fetch(`${API_BASE}/orders/${ord.id}/disputa`, {method: 'POST', headers: {'X-Tg-Init-Data': authHdr()}});
    await loadOrders();
    const dopo = orders.find(x => x.id === ord.id);
    return {id: ord.id, disputa: d.status, state: dopo.state};
  }, g2.ordine.id);
  prova('chi compra apre la disputa, come sul Lightning', [200, 'dispute'], [p2.disputa, p2.state]);
  // un admin che NON e' parte decide: rimborso a chi compra
  r = await api(`/api/admin/orders/${p2.id}/risolvi`, {method: 'POST', headers: ADMIN, body: JSON.stringify({esito: 'rimborso'})});
  prova('l\'admin decide «rimborsa chi compra»: Barattolo firma sul server', 200, r.status);
  console.log('   risposta:', JSON.stringify(r.j).slice(0, 300));
  const oc2 = (await api(`/_giro/ordine/${g2.ordine.id}`)).j.onchain;
  prova('sulla riga: proposta verso chi compra, firmata da Barattolo (decisione)', ['compratore', 0, true],
        [oc2.proposta_verso, oc2.proposta_da, !!oc2.decisione_da]);
  const cof2 = await C.evaluate(async () => {
    await onchainLeggiOrdini();
    const parole = onchainSemeLocale();
    const fatte = await onchainCofirmeInAttesa(parole);
    const os = await onchainLeggiOrdini();
    const o = os.find(x => x.proposta_verso === 'compratore' || x.stato === 'rimborsato' || x.stato === 'rilasciato') ;
    await loadOrders();
    return {fatte, stati: os.map(x => [x.id, x.stato, !!x.txid_uscita]), veri: orders.map(x => [x.id, x.state])};
  });
  console.log('   co-firme compra:', JSON.stringify(cof2.fatte), 'stati:', JSON.stringify(cof2.stati), 'veri:', JSON.stringify(cof2.veri));
  const o2fin = cof2.stati.find(x => x[0] === g2.ordine.id);
  prova('chi compra apre l\'app: seconda firma da sola, rimborso in rete', ['rimborsato', true], [o2fin && o2fin[1], o2fin && o2fin[2]]);
  cat = (await api('/_giro/catena')).j;
  const oc2b = (await api(`/_giro/ordine/${g2.ordine.id}`)).j.onchain;
  const tx2 = cat.giornale.find(g => g.tx === oc2b.txid_uscita);
  prova('in rete: tutto (meno la commissione) torna all\'indirizzo di rimborso di chi compra',
        true, !!tx2 && tx2.uscite.length === 1 && tx2.uscite[0][0] === oc2b.rimborso && tx2.uscite[0][1] >= g2.ordine.importo - g2.ordine.margine);
  console.log('   tx:', JSON.stringify(tx2));
  await C.evaluate(async () => { await loadOrders(); go('affari'); renderOrders(); });
  await sleep(500);
  await C.screenshot({path: OUT + '/g2-ordini-compra.png'});

  const detto = (await api('/_giro/detto')).j;
  console.log('\n[le notifiche che sarebbero partite dal bot]');
  for (const [chi, t] of detto.detto) console.log('   →', chi, ':', t.replace(/<[^>]+>/g, '').slice(0, 140));
  for (const t of detto.avvisi) console.log('   → admin:', String(t).replace(/<[^>]+>/g, '').slice(0, 140));
  const errs = [...C.errs, ...V.errs];
  console.log('\n[errori di pagina]', errs.length ? errs.join('\n   ') : 'nessuno');
  const ok = esiti.filter(e => e.ok).length, ko = esiti.length - ok;
  console.log(`\n${ok} passate, ${ko} fallite`);
  fs.writeFileSync(OUT + '/esiti.json', JSON.stringify({esiti, errs, giornale: cat.giornale, detto}, null, 1));
  await b.close();
  process.exit(ko ? 1 : 0);
})().catch(e => { console.error('COPIONE ROTTO:', e); process.exit(2); });
