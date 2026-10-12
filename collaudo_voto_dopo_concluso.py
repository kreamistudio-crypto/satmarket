# -*- coding: utf-8 -*-
"""
IL VOTO DOPO IL CONCLUSO, SUL SERVER VERO (12 ott 2026, cantiere
voto-dopo-concluso, dal campo: lo scambio a3f57b19 — «nel mio profilo
non compare il fatto che ho portato a termine uno scambio», e il foglio
del solo voto comparso al posto della recensione).

La meta' del cantiere che vive nel browser — l'invito al voto che arriva
dopo il concluso, la conferma che si sente, i relay che contano — gira
nel banco del motore di `prove.py` col coordinatore di cartone. Qui
girano le ROTTE VERE sul database usa-e-getta:

  1. `/api/me` porta `scambi_completati`: zero prima, UNO a tutte e due
     le parti dopo il `success` di mostrod (patch 0007), zero a chi non
     c'entra — e' il numero che la scheda Profilo scrive accanto a
     vendite e acquisti;
  2. la risposta PROVVISORIA: chi chiede «posso recensire?» a sats
     rilasciati ma PRIMA del `success` riceve `non_conclusa` — ed e' la
     risposta su cui la pagina non deve piu' aprire il foglio del solo
     voto; dopo il `success` il posto c'e', nei due versi;
  3. la leva `MOSTRO_RELAY_CONFERMA`: al client arrivano solo le voci
     che stanno anche nel coro, nella busta di `_p2p_leve` e in
     `/api/me`; vuota e' il mondo di ieri;
  4. IL CASO DI AMBER (dal campo: chi ha segnalato entra con Nostr
     tramite un bunker, e' uscito, ha chiuso, e' rientrato): il
     dispositivo 1 nasce col bunker, copia il profilo sui relay e
     prende; lo scambio si conclude; AL RIENTRO, a memoria vuota, il
     MOTORE VERO in node ritrova lo stesso profilo dalla copia, la riga
     conclusa dall'archivio del server con la sua chiave, RIASCOLTA
     l'invito al voto dai relay del coordinatore di cartone, vota con la
     trade key che il coordinatore conosce (che a un'altra direbbe di
     no) e sente la conferma; e nel profilo di scambio lo scambio
     completato c'e', coi numeri della rotta vera. Il controllo
     negativo: il profilo mai copiato sui relay (com'era prima dell'11
     ott) non torna, la riga resta solo da guardare e il voto da li'
     non parte — ma lo scambio nel profilo di scambio c'e' lo stesso.
     E l'account Telegram con la npub collegata (numero POSITIVO) che
     entra con Amber — il profilo glielo ricava il server, e dopo
     l'uscita e il rientro il voto parte uguale.
  5. «VOTO GIA' DATO, RIPROVO» (lo scambio 44c46ddf, quello di chi ha
     segnalato): un nativo che entra con Amber ha VENDUTO prendendo un
     ordine d'acquisto prima del 12 ott (presa non annotata: niente
     recensione, il foglio del solo voto); il suo voto era arrivato, la
     pagina di allora non ne sentiva la conferma, e a un secondo voto
     Mostro non risponde niente. Al rientro la conferma di allora si
     riascolta: «Hai gia' votato questo scambio», nessun bottone,
     niente che parte; e chi tocca lo stesso prima che arrivi legge la
     stessa frase, e il secondo tocco non manda niente.

NON TOCCA NIENTE DI VERO: config di cartone, niente Telegram, niente
relay, niente coordinatore.

USO:  python collaudo_voto_dopo_concluso.py
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import collaudo_pagamento_p2p as banco
import collaudo_chiavi_ritrovate as cr

TG_V, TG_C = banco.VENDE, banco.COMPRA           # 111, 222: due Telegram
TERZO = -711                                      # uno che non c'entra
K = {TG_V: "c1" * 32, TG_C: "c2" * 32, TERZO: "d7" * 32}
ORD = lambda n: f"5a1e0000-7071-4a2b-9c3d-0000000a{n:04x}"


def semina():
    con = banco.con_db()
    adesso = int(time.time())
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,npub,npub_verificata) "
                "VALUES(?,?,?,1,'',?,1)", (TERZO, "Terzo", "negterzo", "npub1xterzo"))
    for tg, k in K.items():
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)", (k, tg, adesso))
    con.commit()
    con.close()


def pubblica(ordine, maker, lato="sell"):
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,visto,preso_da,euro) "
                "VALUES(?,?,?,'pending',?,1,?,0,'10,00 €')", (ordine, maker, int(time.time()), lato, int(time.time())))
    con.commit()
    con.close()


def prende(ordine, taker):
    banco.come(taker)
    banco.esito(banco.SRV.registra_ordini_p2p, {"ordini": [ordine], "presi": True})


def evento(ordine, azione, ts, attore="mostro", dettaglio=None, **extra):
    """Un POST di mostrod come lo tratta la rotta `/api/p2p/evento`: i
    due giudici che registrano E gli esiti (`_segna_esiti_p2p`) — che
    `banco.evento` non chiama, e sono proprio la riga «completato»."""
    d = {"v": 1, "order": ordine, "action": azione, "ts": ts, "actor": attore,
         "detail": dettaglio}
    d.update(extra)
    adesso = int(time.time())
    con = banco.con_db()
    try:
        ev = banco.SRV._evento_p2p_pulito(d, adesso)
        fatto = banco.SRV._registra_evento_p2p(con, ev, adesso)
        if fatto is not None:
            banco.SRV._segna_esiti_p2p(con, ev, fatto, adesso)
        return fatto
    finally:
        con.close()


def mostrod(ordine, maker, taker, t, da="preso", fino="concluso", prende="buyer"):
    """Quel che mostrod racconta al server, a pezzi: `da` e `fino` dicono
    quale tratto mandare ('preso' → 'rilasciato' → 'concluso'). `prende`
    dice il lato di chi ha preso: 'buyer' su un ordine di vendita (chi
    pubblica vende), 'seller' su un ordine d'acquisto (chi prende vende)."""
    kb, ks = (K[taker], K[maker]) if prende == "buyer" else (K[maker], K[taker])
    if da == "preso":
        evento(ordine, "taken", t + 10, prende, "take", buyer=kb, seller=ks)
        evento(ordine, "buyer-invoice-added", t + 20, "buyer", "hold-next", buyer=kb, seller=ks)
        evento(ordine, "hold-invoice-requested", t + 20, "mostro", "invoice", buyer=kb, seller=ks)
        evento(ordine, "hold-invoice-paid", t + 30, "seller", buyer=kb, seller=ks)
        evento(ordine, "fiat-sent", t + 40, "buyer", buyer=kb, seller=ks)
        evento(ordine, "released", t + 50, "seller", None, buyer=kb, seller=ks,
               sats=7300, sats_buyer=7228, sats_seller=7372)
    if fino == "concluso":
        evento(ordine, "success", t + 60, "mostro", None, buyer=kb, seller=ks,
               sats=7300, sats_buyer=7228, sats_seller=7372)


def recensibile(chi, ordine):
    banco.come(chi)
    r = banco.esito(banco.SRV.recensibile_p2p, {"ordine": ordine})
    return (r.get("si"), r.get("motivo", "")) if isinstance(r, dict) else ("ERRORE", r)


def me(chi):
    banco.come(chi)
    r = asyncio.run(banco.SRV.mio_profilo())
    return r if isinstance(r, dict) else json.loads(r.body)


# ==================== IL CASO DI AMBER: USCITA, RIENTRO, VOTO ====================
# (12 ott 2026, dal campo: chi ha segnalato entra con Nostr tramite Amber
# — un bunker —, e' uscito, ha chiuso, e' rientrato.) Il dispositivo 1 e'
# quello di `collaudo_chiavi_ritrovate` (il profilo nato col bunker, la
# copia cifrata sui relay di cartone, la presa). Qui gira il RIENTRO a
# memoria vuota col MOTORE VERO in node: il profilo dalla copia, la riga
# dall'archivio del server (rotta vera), l'invito al voto riascoltato dai
# relay del coordinatore di cartone, il voto firmato con la trade key che
# il coordinatore conosce, e la riga del profilo di scambio coi numeri
# della rotta vera.
NATIVO_AMBER = -778
COLLEGATO = 8800000001            # un account Telegram con la npub collegata: POSITIVO, e sopra 2^31
ORD_AMBER = {"torna": "5a1e0000-7071-4a2b-9c3d-0000000a00a1",
             "perso": "5a1e0000-7071-4a2b-9c3d-0000000a00a2",
             "collegato": "5a1e0000-7071-4a2b-9c3d-0000000a00a3",
             "riprovo": "5a1e0000-7071-4a2b-9c3d-0000000a00a4"}

PROLOGO_MOTORE = r"""
const fs = require('fs'), vm = require('vm');
vm.runInThisContext(fs.readFileSync(process.argv[3], 'utf8'));
const dati = JSON.parse(fs.readFileSync(process.argv[2], 'utf-8'));
const NT0 = NostrTools;
const {bytesToHex, hexToBytes} = NT0.utils;
/* IL COORDINATORE DI CARTONE: la sua chiave nasce qui, firma e cifra
   come quello vero, e col voto fa quel che fa `rate_user.rs` di Mostro
   0.19.0: lo accetta SOLO dalla trade key che ha visto nello scambio e
   SOLO la prima volta (allora risponde `rate-received`); a una chiave
   che non conosce e a un voto gia' dato NON RISPONDE NIENTE — ne'
   conferma ne' rifiuto */
const MOSTRO_SK = NT0.generateSecretKey();
const MOSTRO_PUB = NT0.getPublicKey(MOSTRO_SK);
const URL_COORD = 'wss://coordinatore.test';
const relayStore = new Map(Object.entries(dati.relay || {}));
let subs = [], ricevuti = [];
function daMostro(msg, versoPub, quando){
  return NT0.finalizeEvent({kind: 14, created_at: quando, tags: [['p', versoPub]],
    content: NT0.nip44.encrypt(JSON.stringify([msg, null, null]),
                               NT0.nip44.getConversationKey(MOSTRO_SK, versoPub))}, MOSTRO_SK);
}
function ordineMsg(azione, rid, id, payload){
  const m = {version: 2, request_id: rid === undefined ? null : rid, trade_index: null};
  if (id) m.id = id;
  m.action = azione;
  m.payload = payload === undefined ? null : payload;
  return azione === 'cant-do' ? {'cant-do': m} : {order: m};
}
/* LA STORIA SUI RELAY DEL COORDINATORE: quel che scrisse a chi comprava
   quando lo scambio si e' chiuso — il concluso, e subito dopo l'invito */
const STORIA = dati.storia || [['purchase-completed', 0], ['rate', 0]];
const storia = dati.tradePub ? STORIA.map(([azione, dopo]) => ({azione: azione, ev: daMostro(
  ordineMsg(azione, null, dati.ordine, azione === 'rate-received' ? {rating_user: 5} : null),
  dati.tradePub, dati.quando + dopo)})) : [];
/* il flag del coordinatore: «questa parte ha gia' votato» */
let votoGiaDato = !!dati.giaVotato;
function combacia(f, ev){
  if (f.kinds && f.kinds.indexOf(ev.kind) < 0) return false;
  if (f.authors && f.authors.indexOf(ev.pubkey) < 0) return false;
  if (f['#d'] && !ev.tags.some(t => t[0] === 'd' && f['#d'].indexOf(t[1]) >= 0)) return false;
  if (f['#p'] && !ev.tags.some(t => t[0] === 'p' && f['#p'].indexOf(t[1]) >= 0)) return false;
  if (f.since && ev.created_at < f.since) return false;
  return true;
}
class RelayCartone {
  constructor(url){ this.url = url; this.connected = false; this.onclose = null; }
  static async connect(url){ const r = new RelayCartone(url); await r.connect(); return r; }
  async connect(){ this.connected = true; if (!relayStore.has(this.url)) relayStore.set(this.url, []); }
  close(){ this.connected = false; }
  subscribe(filtri, h){
    const s = {filtri: filtri, h: h, url: this.url, chiuso: false, close(){ this.chiuso = true; }};
    subs.push(s);
    if (this.url === URL_COORD) {
      /* la conferma di allora puo' arrivare TARDI — un relay lento, e la
         persona che tocca prima. Con `confermaAlVoto` qui NON si
         consegna: la porta il relay DOPO che il voto doppio e' partito
         (vedi `publish`). E' un ORDINE e non un cronometro: su un runner
         lento un ritardo a tempo arriverebbe prima del tocco. */
      for (const v of storia) {
        if (v.azione === 'rate-received' && dati.confermaAlVoto) continue;
        setTimeout(() => { if (!s.chiuso && filtri.some(f => combacia(f, v.ev))) h.onevent(v.ev); }, 1);
      }
      setTimeout(() => { if (h.oneose) h.oneose(); }, 2);
      return s;
    }
    const miei = relayStore.get(this.url) || [];
    setTimeout(() => {
      for (const ev of miei) if (!s.chiuso && filtri.some(f => combacia(f, ev))) h.onevent(ev);
      if (h.oneose) h.oneose();
    }, 1);
    return s;
  }
  async publish(ev){
    if (this.url !== URL_COORD) { relayStore.get(this.url).push(ev); return 'ok'; }
    let dentro = null;
    try {
      const arr = JSON.parse(NT0.nip44.decrypt(ev.content, NT0.nip44.getConversationKey(MOSTRO_SK, ev.pubkey)));
      dentro = arr[0].order || arr[0].rate || null;
    } catch(e) {}
    ricevuti.push({da: ev.pubkey, azione: dentro && dentro.action, payload: dentro && dentro.payload});
    if (dentro && dentro.action === 'rate-user' && votoGiaDato && dati.confermaAlVoto) {
      /* il coordinatore TACE; e' il relay che, intanto, consegna la conferma di allora */
      const vecchia = storia.filter(v => v.azione === 'rate-received').map(v => v.ev);
      setTimeout(() => { for (const r of vecchia) for (const s of subs)
        if (!s.chiuso && s.url === URL_COORD && s.filtri.some(f => combacia(f, r))) s.h.onevent(r); }, 30);
    }
    if (dentro && dentro.action === 'rate-user' && ev.pubkey === dati.tradePub && !votoGiaDato) {
      votoGiaDato = true;
      const r = daMostro(ordineMsg('rate-received', dentro.request_id, dentro.id, dentro.payload),
                         ev.pubkey, Math.floor(Date.now() / 1000));
      setTimeout(() => { for (const s of subs) if (!s.chiuso && s.url === URL_COORD && s.filtri.some(f => combacia(f, r))) s.h.onevent(r); }, 5);
    }
    return 'ok';
  }
}
const NT = Object.assign({}, NT0, {Relay: RelayCartone});
const window = {NostrTools: NT};
/* la memoria del browser: VUOTA, come dopo l'uscita e la chiusura */
const store = new Map();
const localStorage = {getItem: k => store.has(k) ? store.get(k) : null,
  setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k)};
let tg = null;
let DEMO = false, VETRINA = false, myTgId = dati.tgId, myLnAddress = '', myNpubAccesso = '';
const API_BASE = '/api';
function authHdr(){ return 'x'; }
const fetches = [], corpi = [];
async function fetch(url, opt){
  fetches.push(String(url));
  if (opt && opt.body) corpi.push({url: String(url), corpo: JSON.parse(opt.body)});
  if (String(url).endsWith('/p2p/seme'))
    return dati.seme ? {ok: true, status: 200, json: async () => dati.seme} : {ok: false, status: 409};
  if (String(url).endsWith('/p2p/chiavi')) return {ok: true, json: async () => ({ok: true, indice: dati.pavimento || 0})};
  return {ok: true, json: async () => ({})};
}
let toasts = []; function toast(m){ toasts.push(String(m)); }
function haptic(){}
function esc(s){ return String(s); }
function fmt(n){ return String(n); }
function fmtEur(n){ return String(n); }
const log = []; const console = {log: m => log.push(String(m)), warn: m => log.push(String(m)), error: m => log.push(String(m))};
const nodi = {};
function el(id){ return nodi[id] || (nodi[id] = {id, value: '', innerHTML: '', textContent: '', style: {}, focus(){}, _c: new Set(),
  classList: {add(c){ nodi[id]._c.add(c); }, remove(c){ nodi[id]._c.delete(c); }, contains(c){ return nodi[id]._c.has(c); }}}); }
const document = {querySelector: s => null, hidden: false};
const navigator = {clipboard: {writeText: async t => {}}};
async function caricaNostrTools(){}
function altroFoglioAperto(){ return false; }
function chiediConferma(o){ if (o.poi) o.poi(); }
function invitoTelegram(){}
const INVITO_ONION = {p2p: 'x'};
function copiaLink(){}
function go(){}
async function disegnaQr(){}
function bottoneInAttesa(){ return () => {}; }
function attesaP2P(){ return () => {}; }
function renderP2P(){}
async function registraOrdiniP2P(){ return true; }
function intestaOrdiniP2P(){ return Promise.resolve(true); }
let p2pRecensioni = {};
async function chiediRecensibileP2P(){ return false; }
function repRigaP2P(){ return ''; }
let P2P_LIBRO_MS = 8000;
let p2pInfo = {fee: 0.02, pow: 0, powPrimo: 0, maxSats: 1000000, minSats: 100, valute: ['EUR'],
               versione: '2', quando: 0, oreVita: 168, scadenzaSec: 86400, holdFinestra: 300, fattFinestra: 3600};
let p2pLibro = {ordini: []};
function p2pCoord(){ return {mostro: MOSTRO_PUB, relay: [URL_COORD]}; }
async function caricaLibroP2P(){}
function tagValore(ev, n){ const t = (ev.tags || []).filter(x => x[0] === n)[0]; return t ? t[1] : ''; }
function suOnion(){ return true; }
let relayCopiaP2P = ['wss://casa.test'];
let pubCasa = '';
/* l'account aperto: Amber, cioe' un bunker — firma e cifra LUI, la
   chiave d'accesso nel browser non c'e' */
const conto = {sk: hexToBytes(dati.contoSk), pub: NT0.getPublicKey(hexToBytes(dati.contoSk))};
function nsecSalvate(){ return {}; }
async function pubAccount(){ return conto.pub; }
async function firmatarioAutomatico(){
  return {f: {pubkey: async () => conto.pub, firma: async ev => NT0.finalizeEvent(ev, conto.sk),
    cifra44: async (pub, t) => NT0.nip44.encrypt(t, NT0.nip44.getConversationKey(conto.sk, pub)),
    decifra44: async (pub, t) => NT0.nip44.decrypt(t, NT0.nip44.getConversationKey(conto.sk, pub)), chiudi(){}},
    chiudi: true};
}
"""

EPILOGO_MOTORE = r"""
const pausa = ms => new Promise(r => setTimeout(r, ms || 20));
const finoA = async (f, ms) => { const t0 = Date.now(); while (!f() && Date.now() - t0 < (ms || 4000)) await pausa(20); };
(async () => {
  const out = {};
  if (dati.passo === 'nasce') {
    /* IL DISPOSITIVO 1 di chi ha il profilo LEGATO ALL'ACCOUNT: il seme
       dal server, e la presa (l'indice sale, la trade key nasce) */
    let mz = await adottaProfiloContoP2P();
    if (!mz) mz = await assicuraMazzo();
    out.origine = mz.origine;
    const indice = (Number(mazzoMostro().indice) || 0) + 1;
    ricordaMazzo(Object.assign({}, mazzoMostro(), {indice}));
    const tk = chiaveScambio(mazzoMostro().sk, indice);
    await registraChiaviP2P([tk.pub]);
    out.mazzoPub = mazzoMostro().pub; out.tradePub = tk.pub; out.indice = indice;
    out.chiaviRegistrate = corpi.filter(c => c.url.endsWith('/p2p/chiavi')).map(c => c.corpo.pubkeys);
    out.copieSuiRelay = [...relayStore.values()].reduce((n, l) => n + l.length, 0);
    process.stdout.write(JSON.stringify(out));
    return;
  }
  /* IL RIENTRO: il profilo torna dalla copia cifrata sui relay (o no) */
  const mz = await adottaProfiloContoP2P();
  out.profilo = mz ? mz.pub : null;
  out.origine = mz ? mz.origine : null;
  /* ...e la riga dello scambio dall'archivio del server (rotta vera) */
  p2pScambiServer = dati.risposta;
  adottaScambiServerP2P(ordiniP2P());
  let o = ordiniP2P()[dati.ordine];
  out.riga = o ? {stato: o.stato, soloVista: !!o.soloVista, chiaveGiusta: o.pubTrade === dati.tradePub,
                  votabile: o.votabile === true} : null;
  if (!o) { process.stdout.write(JSON.stringify(out)); return; }
  out.gesto = gestoRecensioneP2P(o, dati.recensibile);
  out.inAttesaVoto = Object.keys(ordiniVotoP2P()).length;
  /* la pagina dello scambio concluso riprende il voto */
  out.ripresa = riprendiVotoP2P(o);
  await finoA(() => (ordiniP2P()[dati.ordine] || {}).votabile === true, 2500);
  o = ordiniP2P()[dati.ordine];
  out.invitoRiascoltato = o.votabile === true;
  out.statoDopo = o.stato;
  if (dati.giaVotato) {
    /* IL VOTO C'ERA GIA' (lo scambio 44c46ddf): la conferma di allora
       sta ancora sui relay, e riascoltata accende `votato` */
    if (!dati.impaziente) await finoA(() => (ordiniP2P()[dati.ordine] || {}).votato === true, 2500);
    o = ordiniP2P()[dati.ordine];
    out.giaVotato = {votato: o.votato === true, gesto: gestoRecensioneP2P(o, dati.recensibile),
                     riquadro: riquadroRecensioneP2P(o, dati.recensibile),
                     aspettaAncora: Object.keys(ordiniVotoP2P()).length};
    if (dati.impaziente) {
      /* ...e CHI RIPROVA LO STESSO, subito: il voto parte, il
         coordinatore tace (flag gia' alzato), e intanto arriva la conferma
         di allora — la pagina dice che il voto c'era, e il secondo tocco
         non manda piu' niente */
      p2pOrdineAperto = dati.ordine;
      renderOrdineP2P = function(){};
      P2P_ATTESA_MS = 2500;
      toasts = [];
      await votaP2P(5);
      const dopoUno = ricevuti.filter(x => x.azione === 'rate-user').length;
      await votaP2P(5);
      out.riprovo = {toast: toasts.slice(), mandatiAlPrimo: dopoUno,
                     mandatiInTutto: ricevuti.filter(x => x.azione === 'rate-user').length,
                     votato: (ordiniP2P()[dati.ordine] || {}).votato === true};
    }
  }
  /* il voto: lo manda la persona */
  P2P_ATTESA_MS = 2500;
  let esito = 'ok';
  if (dati.giaVotato) esito = 'non mandato';
  else if (o.pubTrade) {
    try { await stelleCircuitoP2P(o, 5); } catch(e) { esito = String(e && e.message || e); }
  } else esito = 'senza chiave';
  const voti = ricevuti.filter(x => x.azione === 'rate-user');
  out.voto = {esito: esito, votato: (ordiniP2P()[dati.ordine] || {}).votato === true,
              arrivati: voti.length, daChiaveGiusta: voti.length ? voti.every(x => x.da === dati.tradePub) : null,
              stelle: voti.length ? voti[0].payload.rating_user : 0};
  /* il profilo di scambio: i numeri della rotta vera, nella riga vera */
  prendiPrendibiliP2P(dati.reputazione, []);
  out.rigaProfilo = rigaMiaReputazioneP2P();
  out.seme = fetches.filter(u => u.endsWith('/p2p/seme')).length;
  process.stdout.write(JSON.stringify(out));
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def pezzi_motore():
    """Il client vero del rientro: il blocco del mazzo e il MOTORE intero,
    piu' i tre pezzi fuori dalle due fette che la copia sui relay chiama."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()

    def fn(firma):
        i = mini.index(firma)
        return mini[i:mini.index("\n}\n", i) + 3]
    mazzo = mini[mini.index("const MOSTRO_CHIAVE = "):
                 mini.index("/* ---- export CSV degli affari conclusi")]
    motore = mini[mini.index("const MOSTRO_ORDINI_CHIAVE"):
                  mini.index("/* ============ fine del motore dello scambio")]
    fuori = "\n".join(fn(f) for f in ("async function pubblicaEventoSuRelay(relays, evento){",
                                      "async function firmatarioNsec(nsec){",
                                      "function firmatarioEstensione(){"))
    return mazzo + "\n" + motore + "\n" + fuori + "\n"


def rientro(dati):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="voto_rientro_")
    try:
        p = os.path.join(cart, "client.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(PROLOGO_MOTORE + pezzi_motore() + EPILOGO_MOTORE)
        open(d, "w", encoding="utf-8").write(json.dumps(dati))
        r = subprocess.run([node, p, d, os.path.join(banco.QUI, "vendor", "nostr.bundle.js")],
                           capture_output=True, text=True, timeout=120, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-700:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def caso_amber(prova, t):
    import secrets
    SRV = banco.SRV
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,npub,npub_verificata) "
                "VALUES(?,?,?,1,'',?,1)", (NATIVO_AMBER, "Nativo Amber", "negamber", "npub1xamber"))
    con.commit()
    con.close()
    prova("chi entra con Amber da nativo ha il numero NEGATIVO, e il seme del server per lui e' un 409",
          409, cr.seme(NATIVO_AMBER))
    for caso, copia_sui_relay in (("torna", True), ("perso", False)):
        ordine = ORD_AMBER[caso]
        pubblica(ordine, TG_V)
        chiave = secrets.token_hex(32)
        # IL DISPOSITIVO 1, con Amber: il profilo, la copia cifrata, la presa
        uno = cr.client({"passo": "nasce", "modo": "bunker", "contoSk": chiave, "tgId": NATIVO_AMBER,
                         "relay": {}, "pavimento": 0})
        prova(f"[{caso}] il dispositivo 1 con Amber gira e copia il profilo sui relay",
              [None, "copia", 1], [uno.get("ERRORE"), uno.get("copia"), uno.get("copie")])
        if uno.get("ERRORE"):
            continue
        banco.come(NATIVO_AMBER)
        for pubkeys in uno["chiaviRegistrate"]:
            banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
        banco.esito(SRV.registra_ordini_p2p, {"ordini": [ordine], "presi": True})
        kb = uno["tradePub"]
        K[NATIVO_AMBER] = kb
        mostrod(ordine, TG_V, NATIVO_AMBER, t + 300)
        risposta = cr.scambi(NATIVO_AMBER).get("scambi", {})
        voce = risposta.get(ordine)
        prova(f"[{caso}] l'archivio del server (rotta vera): lo scambio di chi e' entrato con Amber, "
              "concluso, con la sua trade key",
              ["concluso", "compro", kb], voce and [voce["stato"], voce["lato"], voce["chiave_mia"]])
        rep = banco.esito(SRV.posso_prendere_p2p, {"ordini": []})
        prova(f"[{caso}] i suoi numeri (rotta vera): lo scambio completato e' contato al suo account",
              True, isinstance(rep, dict) and rep.get("completati", 0) >= 1 or rep)
        rec = banco.esito(SRV.recensibile_p2p, {"ordine": ordine})
        prova(f"[{caso}] ...e la recensione ha un posto", True, isinstance(rec, dict) and rec.get("si") is True or rec)
        # L'USCITA E IL RIENTRO: memoria vuota, di nuovo Amber
        due = rientro({"contoSk": chiave, "tgId": NATIVO_AMBER, "ordine": ordine, "tradePub": kb,
                       "relay": uno["relay"] if copia_sui_relay else {}, "risposta": risposta,
                       "reputazione": rep if isinstance(rep, dict) else {}, "recensibile": rec if isinstance(rec, dict) else {},
                       "quando": t + 360, "pavimento": uno["indice"]})
        prova(f"[{caso}] il rientro gira (il motore vero in node)", None, due.get("ERRORE"))
        if due.get("ERRORE"):
            continue
        if copia_sui_relay:
            prova("[torna] rientrato con Amber a memoria vuota: LO STESSO profilo, dalla copia, senza chiedere il seme "
                  "piu' di quanto gli tocchi (che e' un 409)", uno["mazzoPub"], due["profilo"])
            prova("[torna] la riga torna dall'archivio conclusa, con la SUA chiave e non solo da guardare — "
                  "e senza l'invito al voto, che la riga del server non porta",
                  {"stato": "concluso", "soloVista": False, "chiaveGiusta": True, "votabile": False}, due["riga"])
            prova("[torna] la pagina gli offre la recensione, e lo scambio aspetta il voto",
                  ["recensisci", 1], [due["gesto"], due["inAttesaVoto"]])
            prova("[torna] la ripresa RIASCOLTA la chiave, e l'invito di allora arriva adesso: il voto si accende, "
                  "lo scambio resta concluso", ["ascolto", True, "concluso"],
                  [due["ripresa"], due["invitoRiascoltato"], due["statoDopo"]])
            prova("[torna] il voto parte firmato con la trade key che il coordinatore conosce, UNA volta, e la "
                  "conferma si sente", {"esito": "ok", "votato": True, "arrivati": 1, "daChiaveGiusta": True, "stelle": 5},
                  due["voto"])
            prova("[torna] nel profilo di scambio lo scambio completato c'e'", True,
                  "scambio completato" in due["rigaProfilo"] or "scambi completati" in due["rigaProfilo"])
            prova("[torna] ...col numero della rotta vera", True,
                  "<b>%d</b>" % rep["completati"] in due["rigaProfilo"])
        else:
            # IL CONTROLLO NEGATIVO: il profilo di prima della cura dell'11 ott, mai copiato sui relay
            prova("[perso] senza la copia sui relay il profilo NON torna, e non ne nasce uno finto", None, due["profilo"])
            prova("[perso] la riga torna conclusa ma SOLO DA GUARDARE, senza chiave",
                  {"stato": "concluso", "soloVista": True, "chiaveGiusta": False, "votabile": False}, due["riga"])
            prova("[perso] da quel dispositivo il voto al circuito non puo' partire: nessun messaggio, nessuna "
                  "chiave inventata", ["", "senza chiave", 0], [due["ripresa"], due["voto"]["esito"], due["voto"]["arrivati"]])
            prova("[perso] ...ma lo scambio nel profilo di scambio c'e' lo stesso: e' dell'account, non del dispositivo",
                  True, "<b>%d</b>" % rep["completati"] in due["rigaProfilo"])
    caso_collegato(prova, t)
    caso_gia_votato(prova, t)


def caso_gia_votato(prova, t):
    """«VOTO GIA' DATO, RIPROVO» (12 ott 2026, sera: e' lo scambio 44c46ddf
    di chi ha segnalato). Un nativo Nostr che entra con Amber PRENDE un
    ordine d'acquisto, cioe' VENDE, prima della regola del 12 ott: la sua
    presa non e' annotata, il server non gli offre la recensione e la
    pagina gli apre il foglio del solo voto. Vota: il coordinatore lo
    accetta (`seller_sent_rate` a 1) e conferma — ma la pagina di allora
    non sentiva la conferma, e diceva «non e' partito». Riprova: a un
    voto gia' dato Mostro NON RISPONDE (letto su `rate_user.rs` della
    0.19.0), e la pagina ridiceva lo stesso. ADESSO: al rientro la
    conferma di allora si riascolta dai relay, la pagina dice «Hai gia'
    votato questo scambio» e non offre piu' il voto; e chi tocca lo
    stesso prima che arrivi si sente dire la stessa cosa, e il secondo
    tocco non manda niente."""
    import secrets
    SRV = banco.SRV
    ordine = ORD_AMBER["riprovo"]
    pubblica(ordine, TG_C, lato="buy")           # chi pubblica COMPRA
    chiave = secrets.token_hex(32)
    uno = cr.client({"passo": "nasce", "modo": "bunker", "contoSk": chiave, "tgId": NATIVO_AMBER,
                     "relay": {}, "pavimento": 0})
    prova("[riprovo] il dispositivo 1 con Amber gira", None, uno.get("ERRORE"))
    if uno.get("ERRORE"):
        return
    banco.come(NATIVO_AMBER)
    for pubkeys in uno["chiaviRegistrate"]:
        banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
    # LA PRESA NON SI DICHIARA: prima del 12 ott chi entrava da Nostr e
    # prendeva non veniva annotato
    kv = uno["tradePub"]
    K[NATIVO_AMBER] = kv
    prima = me(NATIVO_AMBER).get("scambi_completati")
    mostrod(ordine, TG_C, NATIVO_AMBER, t + 700, prende="seller")
    con = banco.con_db()
    riga = con.execute("SELECT tg_id, preso_da, stato FROM p2p_ordini WHERE ordine=?", (ordine,)).fetchone()
    esito_suo = con.execute("SELECT esito, ruolo FROM p2p_esiti WHERE ordine=? AND tg_id=?",
                            (ordine, NATIVO_AMBER)).fetchone()
    con.close()
    prova("[riprovo] il server, com'era per 44c46ddf: l'ordine e' di chi ha pubblicato, la presa non e' di nessuno",
          [TG_C, 0], [riga["tg_id"], riga["preso_da"]])
    prova("[riprovo] ...ma il «completato» c'e', a chi ha VENDUTO: la chiave dello scambio e' del suo account",
          ("completato", "vende"), esito_suo and (esito_suo["esito"], esito_suo["ruolo"]))
    prova("[riprovo] ...e /api/me glielo conta: e' la riga che la scheda Profilo ora scrive",
          (prima or 0) + 1, me(NATIVO_AMBER).get("scambi_completati"))
    rec = banco.esito(SRV.recensibile_p2p, {"ordine": ordine})
    prova("[riprovo] la recensione per lui non ha un posto: per questo la pagina apre il foglio del solo voto",
          False, isinstance(rec, dict) and rec.get("si"))
    risposta = cr.scambi(NATIVO_AMBER).get("scambi", {})
    voce = risposta.get(ordine)
    prova("[riprovo] l'archivio del server gli da' lo scambio, concluso, dal lato di chi vende, con la sua chiave",
          ["concluso", "vendo", kv], voce and [voce["stato"], voce["lato"], voce["chiave_mia"]])
    rep = banco.esito(SRV.posso_prendere_p2p, {"ordini": []})
    # quel che il coordinatore scrisse ALLORA a chi vendeva: la garanzia
    # liberata, l'invito al voto, e la CONFERMA del voto (40 secondi dopo)
    base = {"contoSk": chiave, "tgId": NATIVO_AMBER, "ordine": ordine, "tradePub": kv,
            "relay": uno["relay"], "risposta": risposta,
            "reputazione": rep if isinstance(rep, dict) else {},
            "recensibile": rec if isinstance(rec, dict) else {},
            "quando": t + 760, "pavimento": uno["indice"], "giaVotato": True,
            "storia": [["hold-invoice-payment-settled", 0], ["rate", 1], ["rate-received", 40]]}
    due = rientro(base)
    prova("[riprovo] il rientro gira (il motore vero in node)", None, due.get("ERRORE"))
    if not due.get("ERRORE"):
        prova("[riprovo] rientrato con Amber: lo stesso profilo, e la riga conclusa con la SUA chiave",
              [uno["mazzoPub"], {"stato": "concluso", "soloVista": False, "chiaveGiusta": True, "votabile": False}],
              [due["profilo"], due["riga"]])
        prova("[riprovo] riaprendo lo scambio la CONFERMA di allora si riascolta: il voto risulta dato, "
              "e lo scambio non aspetta piu' niente", [True, 0],
              [due["giaVotato"]["votato"], due["giaVotato"]["aspettaAncora"]])
        prova("[riprovo] la pagina dice «Hai gia' votato questo scambio» e NON offre il voto",
              [True, ""], ["Hai già votato questo scambio" in due["giaVotato"]["riquadro"], due["giaVotato"]["gesto"]])
        prova("[riprovo] ...e al coordinatore non parte niente", ["non mandato", 0],
              [due["voto"]["esito"], due["voto"]["arrivati"]])
        prova("[riprovo] nel profilo di scambio lo scambio completato c'e'", True,
              isinstance(rep, dict) and "<b>%d</b>" % rep.get("completati", -1) in due["rigaProfilo"])
    tre = rientro(dict(base, impaziente=True, confermaAlVoto=True))
    prova("[riprovo] chi riprova lo stesso: il giro gira", None, tre.get("ERRORE"))
    if not tre.get("ERRORE"):
        r = tre.get("riprovo") or {}
        prova("[riprovo] il primo tocco parte (la conferma non era ancora arrivata), il coordinatore TACE, "
              "e la pagina dice «Hai gia' votato» — non «non e' partito», non «riprova»",
              [1, ["⭐ Hai già votato questo scambio", "⭐ Hai già votato questo scambio"]],
              [r.get("mandatiAlPrimo"), r.get("toast")])
        prova("[riprovo] ...e il secondo tocco non manda piu' niente", [1, True],
              [r.get("mandatiInTutto"), r.get("votato")])


def caso_collegato(prova, t):
    """IL CASO DEL CAMPO, PRECISO (12 ott 2026, la sera: chi ha segnalato e'
    chi COMPRAVA in a3f57b19, ha il numero POSITIVO e la npub collegata —
    un account Telegram che entra con Amber). A lui il profilo di scambio
    lo ricava il SERVER (`/api/p2p/seme`, rotta vera, col numero sopra
    2^31 come i suoi): nessuna copia sui relay, nessuna chiave chiesta al
    bunker. Uscito e rientrato a memoria vuota ritrova lo stesso profilo,
    la riga conclusa con la sua chiave, e da li' il voto."""
    import secrets
    SRV = banco.SRV
    ordine = ORD_AMBER["collegato"]
    SRV.SEGRETI_PROFILO_P2P = {1: secrets.token_hex(32)}
    SRV.SEGRETO_PROFILO_P2P_VIVA = 1
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,npub,npub_verificata,npub_accesso) "
                "VALUES(?,?,?,1,'',?,1,?)", (COLLEGATO, "Collegato", "negcollegato", "npub1xcollegato", "npub1xcollegato"))
    con.commit()
    con.close()
    pubblica(ordine, TG_V)
    r = cr.seme(COLLEGATO)
    seme = json.loads(r.body) if hasattr(r, "body") else {}
    prova("[collegato] a un account col numero POSITIVO il seme lo da' il server, anche se entra con Amber",
          [True, 64], [seme.get("ok"), len(seme.get("seme", ""))])
    prova("[collegato] ...ed e' lo stesso a ogni richiesta: il profilo non dipende dal dispositivo",
          seme.get("seme"), json.loads(cr.seme(COLLEGATO).body).get("seme"))
    base = {"contoSk": secrets.token_hex(32), "tgId": COLLEGATO, "seme": {"ok": True, "seme": seme.get("seme"),
            "versione": seme.get("versione")}, "relay": {}, "ordine": ordine}
    uno = rientro(dict(base, passo="nasce", pavimento=0))
    prova("[collegato] il dispositivo 1 gira: il profilo viene dal conto, e sui relay non va nessuna copia",
          [None, "conto", 0], [uno.get("ERRORE"), uno.get("origine"), uno.get("copieSuiRelay")])
    if uno.get("ERRORE"):
        return
    banco.come(COLLEGATO)
    for pubkeys in uno["chiaviRegistrate"]:
        banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
    banco.esito(SRV.registra_ordini_p2p, {"ordini": [ordine], "presi": True})
    kb = uno["tradePub"]
    K[COLLEGATO] = kb
    mostrod(ordine, TG_V, COLLEGATO, t + 500)
    risposta = cr.scambi(COLLEGATO).get("scambi", {})
    voce = risposta.get(ordine)
    prova("[collegato] l'archivio del server: il suo scambio, concluso, con la sua trade key",
          ["concluso", "compro", kb], voce and [voce["stato"], voce["lato"], voce["chiave_mia"]])
    prova("[collegato] /api/me gli conta lo scambio: e' la riga della scheda Profilo", 1,
          me(COLLEGATO).get("scambi_completati"))
    rep = banco.esito(SRV.posso_prendere_p2p, {"ordini": []})
    rec = banco.esito(SRV.recensibile_p2p, {"ordine": ordine})
    due = rientro(dict(base, tradePub=kb, risposta=risposta,
                       reputazione=rep if isinstance(rep, dict) else {},
                       recensibile=rec if isinstance(rec, dict) else {},
                       quando=t + 560, pavimento=uno["indice"]))
    prova("[collegato] il rientro gira (il motore vero in node)", None, due.get("ERRORE"))
    if due.get("ERRORE"):
        return
    prova("[collegato] uscito e rientrato a memoria vuota: LO STESSO profilo, dal conto",
          [uno["mazzoPub"], "conto"], [due["profilo"], due["origine"]])
    prova("[collegato] la riga torna conclusa, con la SUA chiave, senza l'invito al voto",
          {"stato": "concluso", "soloVista": False, "chiaveGiusta": True, "votabile": False}, due["riga"])
    prova("[collegato] riaprendo lo scambio l'invito di allora si riascolta e il voto si accende",
          ["recensisci", "ascolto", True, "concluso"],
          [due["gesto"], due["ripresa"], due["invitoRiascoltato"], due["statoDopo"]])
    prova("[collegato] il voto parte con la trade key che il coordinatore conosce, UNA volta, e la conferma si sente",
          {"esito": "ok", "votato": True, "arrivati": 1, "daChiaveGiusta": True, "stelle": 5}, due["voto"])
    prova("[collegato] nel profilo di scambio lo scambio completato c'e'", True,
          isinstance(rep, dict) and "<b>%d</b>" % rep.get("completati", -1) in due["rigaProfilo"])


def main():
    banco.avvio()
    banco.semina()
    semina()
    prova = banco.prova
    SRV = banco.SRV
    SRV.P2P_ATTIVO = True
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.MOSTRO_RELAY_CONFERMA = []
    SRV.P2P_PROVA_IDS = []
    t = int(time.time()) - 900

    print("\n1) /api/me porta gli scambi P2P completati: e' la riga della scheda Profilo")
    prova("prima di ogni scambio il numero c'e' e vale zero, per tutti",
          [0, 0, 0], [me(TG_V).get("scambi_completati"), me(TG_C).get("scambi_completati"),
                      me(TERZO).get("scambi_completati")])
    o1 = ORD(1)
    pubblica(o1, TG_V)
    prende(o1, TG_C)
    mostrod(o1, TG_V, TG_C, t, fino="rilasciato")
    prova("a sats rilasciati ma senza il `success` non si conta ancora niente",
          [0, 0], [me(TG_V)["scambi_completati"], me(TG_C)["scambi_completati"]])

    print("\n2) la risposta provvisoria: «non ancora conclusa», e poi il posto c'e'")
    prova("chi chiede prima del `success` riceve `non_conclusa`, nei due versi",
          [(False, "non_conclusa"), (False, "non_conclusa")],
          [recensibile(TG_V, o1), recensibile(TG_C, o1)])
    mostrod(o1, TG_V, TG_C, t, da="rilasciato", fino="concluso")
    prova("...e dopo il `success` la recensione ha un posto, nei due versi",
          [(True, ""), (True, "")], [recensibile(TG_V, o1), recensibile(TG_C, o1)])
    prova("a scambio concluso il numero e' UNO a chi ha venduto e a chi ha comprato",
          [1, 1], [me(TG_V)["scambi_completati"], me(TG_C)["scambi_completati"]])
    prova("...e resta zero a chi non c'entra", 0, me(TERZO)["scambi_completati"])
    o2 = ORD(2)
    pubblica(o2, TG_C)
    prende(o2, TG_V)
    mostrod(o2, TG_C, TG_V, t + 200)
    prova("un secondo scambio a parti rovesciate fa DUE a tutti e due",
          [2, 2], [me(TG_V)["scambi_completati"], me(TG_C)["scambi_completati"]])
    prova("lo stesso `success` raccontato due volte non conta due volte",
          2, (mostrod(o2, TG_C, TG_V, t + 200, da="rilasciato"), me(TG_V)["scambi_completati"])[1])

    print("\n3) la leva MOSTRO_RELAY_CONFERMA: solo le voci che stanno nel coro")
    prova("vuota e' il mondo di ieri: al client arriva una lista vuota",
          [[], []], [SRV._p2p_leve()["conferma"], me(TG_V)["p2p_leve"]["conferma"]])
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9", "ws://127.0.0.1:10"]
    SRV.MOSTRO_RELAY_CONFERMA = ["ws://127.0.0.1:10", "ws://127.0.0.1:11"]
    prova("accesa: arriva la voce che sta anche nel coro, e non quella fuori",
          [["ws://127.0.0.1:10"], ["ws://127.0.0.1:10"]],
          [SRV._p2p_leve()["conferma"], me(TG_C)["p2p_leve"]["conferma"]])
    prova("...e il coro resta intero: l'evento parte verso tutti",
          ["ws://127.0.0.1:9", "ws://127.0.0.1:10"], SRV._p2p_leve()["relay"])
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.MOSTRO_RELAY_CONFERMA = []

    print("\n4) Amber: uscita, rientro a memoria vuota, il voto dopo il concluso, lo scambio nel profilo di scambio")
    caso_amber(prova, t)

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
