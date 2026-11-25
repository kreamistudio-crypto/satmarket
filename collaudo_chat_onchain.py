# -*- coding: utf-8 -*-
"""
LA CHAT DELLO SCAMBIO ON-CHAIN, SUL SERVER VERO (17 nov 2026, cantiere
onchain-chat-sollecito, Andrea: «tutto deve essere come la parte
lighting»).

La chat dello scambio Lightning anche nel P2P on-chain, col motore del
mercatino: nell'on-chain non c'e' un coordinatore che dia le chiavi dello
scambio, e le chiavi d'ordine le presenta il server. L'id nel cassetto e'
il nome pubblico dello scambio («bar-onchain-» e sedici esadecimali), le
parti le dice la riga di `p2p_onchain_ordini` (chi deposita vende, chi
riceve compra), la chat c'e' dalla presa alla fine — disputa compresa —
e se ne va a sats rilasciati, rimborsati, o a scambio annullato/scaduto.

`prove.py` difende i pezzi estratti (`prove_chat_onchain`). Qui girano
le ROTTE VERE su database usa-e-getta, con l'autenticazione VERA:

   1. le leve: la chat del Lightning spenta, o l'on-chain spento;
   2. l'accensione: prima della presa no, dalla presa si', per un
      estraneo mai; la riga dello scambio dice 'aperta' alle parti;
   3. le chiavi d'ordine presentate dal server, e la scorta di lucchetti
      che vale anche qui (con la sola leva della chat del Lightning);
   4. il messaggio: arriva all'altra parte, l'avviso dice «scambio
      on-chain» col bottone «🟠 Apri lo scambio» dritto alla chat, MAI
      il testo;
   5. «vuole scriverti»: l'avviso, una volta sola, col suo bottone;
   6. la disputa: la chiave al moderatore solo a stato 'disputa', il
      moderatore legge solo allora, e la riga gli dice 'moderazione';
   7. il pallino e la fine: lo scambio nella domanda del pallino, e a
      sats rilasciati le righe spariscono DAL FILE e il pallino lo dice
      finito;
   8. IL CLIENT VERO IN NODE contro il server vero: due telefoni (chi
      compra col profilo di scambio, chi vende senza) aprono la pagina
      dello scambio on-chain, si scrivono cifrato nei due sensi, in
      disputa danno tutti e due la chiave al moderatore, che legge; alla
      fine il telefono butta chiave e messaggi.

NON TOCCA NIENTE DI VERO: il config di cartone di
`collaudo_pagamento_p2p`, niente Telegram, niente relay. Le buste delle
prime sezioni sono testo a caso; la crittografia vera gira nella 8.

USO:  python collaudo_chat_onchain.py
"""

import asyncio
import json
import os
import sys
import time

import collaudo_pagamento_p2p as banco
import collaudo_chat_scambio as cs

prova = banco.prova
V, C, X, ADMIN = 222, 111, 333, 999
DETTI = []
NUMERO = [0]


def adesso():
    return int(time.time())


def nuovo_scambio(stato="preso", venditore=V, compratore=C):
    """Una riga di `p2p_onchain_ordini`: chi vende (deposita) e chi compra
    (riceve). Torna `(id, ordine)`."""
    NUMERO[0] += 1
    ordine = "bar-onchain-" + f"{0xc4a7000000000000 + NUMERO[0]:016x}"
    con = banco.SRV._p2p_onchain_db()
    try:
        oid = con.execute(
            "INSERT INTO p2p_onchain_ordini(ordine, lato, maker_id, taker_id, depositante_id, "
            "ricevente_id, prezzo_sats, euro_cent, metodi, stato, scade, creato, aggiornato) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ordine, "sell", venditore, compratore if stato != "pending" else 0, venditore,
             compratore if stato != "pending" else 0, 100000, 9000, '["Revolut"]', stato,
             adesso() + 3600, adesso(), adesso())).lastrowid
        con.commit()
    finally:
        con.close()
    return oid, ordine


def metti(oid, stato):
    con = banco.con_db()
    con.execute("UPDATE p2p_onchain_ordini SET stato=? WHERE id=?", (stato, oid))
    con.commit()
    con.close()


def chat_della_riga(oid, chi, admin=False):
    """Cosa dice `_p2p_onchain_per` della chat, a chi guarda."""
    con = banco.SRV._p2p_onchain_db()
    try:
        o = con.execute("SELECT * FROM p2p_onchain_ordini WHERE id=?", (oid,)).fetchone()
        return banco.SRV._p2p_onchain_per(con, o, chi, admin=admin).get("chat")
    finally:
        con.close()


def righe_cassetto(o):
    return tuple(len(cs.cassetto(f"SELECT 1 FROM {t} WHERE ordine=?", o))
                 for t in ("buste", "letture", "allegati", "chiavi_ordine"))


def avvisi_chat():
    return [(chi, t, b) for chi, t, b in DETTI if t.startswith("💬 <b>Hai un nuovo messaggio")]


def scorta_pulita():
    cc = banco.SRV.db_chat()
    try:
        cc.execute("DELETE FROM scorta")
        cc.commit()
    finally:
        cc.close()


def dispositivo(mini):
    """IL TELEFONO, per la sezione 8: le funzioni VERE di miniapp.html —
    tutto il blocco della chat, con l'adattatore dell'on-chain — in node,
    col bundle vero, un localStorage in un file (uno per telefono) e la
    `fetch` vera verso il ponte. Di cartone c'e' la pagina dello scambio
    on-chain: il richiamo e il riquadro nascono come in `schedaOnchainP2P`
    (`chatOcRichiamoHTML`, `chatOcBloccoHTML`)."""
    def js(firma, fine="\n}\n"):
        i = mini.index(firma)
        return mini[i:mini.index(fine, i) + len(fine)]

    def cost(nome, fine=";\n"):
        i = mini.index("const " + nome + " = ")
        return mini[i:mini.index(fine, i) + len(fine)]

    blocco = mini[mini.rindex("/* ═══ LA CHAT NELLO SCAMBIO (12 ott 2026"):
                  mini.index("/* ═══ fine: la chat nello scambio ═══ */")]
    pezzi = "\n".join(
        [cost(n) for n in ("P2P_FINALI", "P2P_FORMA_ORDINE")]
        + [js(f) for f in ("function idMostroVero(id){", "function ordiniP2P(){")]
        + [js("function p2pRitirato(o){", "\n}") + "\n", blocco])
    return r"""
const fs = require('fs'), vm = require('vm');
const [BUNDLE, STATO, BASE, CONTO, NOME] = process.argv.slice(2, 7);
const PASSI = process.argv.slice(7);
vm.runInThisContext(fs.readFileSync(BUNDLE, 'utf8'));
const NT = NostrTools;
const window = {NostrTools: NT, innerHeight: 800};
/* I GESTI «SUBITO» DELLA PAGINA (24 nov 2026, cantiere chat-stabili-sorelle,
   la stessa cura di `collaudo_chat_scambio`): la pagina rimanda a un
   setTimeout(…, 0) il ritiro (`bloccoChatScambioP2P`). Finche' non e'
   partito niente e' «in volo», e `quieto` poteva fotografare prima del
   ritiro. Qui si contano: finche' uno non e' scattato la pagina non e'
   quieta. */
const tempoVero = setTimeout;
let subito = 0;
globalThis.setTimeout = (fn, ms, ...a) => {
  if (ms) return tempoVero(fn, ms, ...a);
  subito++;
  return tempoVero(() => { subito--; fn(...a); }, 0);
};
const _box = fs.existsSync(STATO) ? JSON.parse(fs.readFileSync(STATO, 'utf-8')) : {};
const localStorage = {getItem: k => (k in _box ? _box[k] : null), setItem: (k, v) => { _box[k] = String(v); }};
function chiaveP2P(k){ return k; }
const MOSTRO_ORDINI_CHIAVE = 'barattolo_mostro_ordini';
const DEMO = false, VETRINA = false;
let myTgId = Number(CONTO);
const API_BASE = BASE + '/api';
function authHdr(){ return 'collaudo:' + CONTO + ':' + NOME; }
const fetchVera = fetch;
let chiamate = [];
globalThis.fetch = (url, opz) => {
  const corpo = (opz && typeof opz.body === 'string') ? JSON.parse(opz.body) : {};
  chiamate.push(String(url).split('/api/')[1] + (corpo.tipo ? ':' + corpo.tipo : ''));
  return fetchVera(url, opz);
};
let p2pOrdineAperto = '', p2pLeve = {chat: true};
const DIARIO = [];
function diarioP2P(r){ DIARIO.push(String(r)); }
function toast(){} function haptic(){} function renderP2P(){} function renderModerazioneP2P(){}
function aggiornaPallinoScambiP2P(){} function renderOrders(){} function renderOrdineP2P(){}
function esc(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function nomeControparteP2P(o, ripiego){ return ripiego; }
function chiaveModeratoreP2P(){ return _box.MOD ? JSON.parse(_box.MOD) : null; } function archivioModP2P(){ return {}; }
function linkPdfPayCodeP2P(){ return null; } function payCodeScambioP2P(){ return ''; }
async function caricaNostrTools(){}
function vistaAttivaP2P(){ return 'view-p2ponchain'; }
function mazzoMostro(){ return _box.MAZZO ? JSON.parse(_box.MAZZO) : null; }
async function adottaProfiloContoP2P(){ return mazzoMostro(); }
function el(id){ return id === 'p2pChatScLista' ? {getBoundingClientRect: () => ({top: 300, bottom: 560, height: 260})} : null; }
let orders = [];
/* LA PAGINA DELLO SCAMBIO ON-CHAIN, di cartone: «I miei scambi» con una
   riga, e i due pezzi della chat come in `schedaOnchainP2P` */
let p2pOnchainMiei = _box.SCAMBIO ? [JSON.parse(_box.SCAMBIO)] : [];
let p2pOnchainAperto = p2pOnchainMiei.length ? p2pOnchainMiei[0].id : 0;
let ULTIMA = {richiamo: '', riquadro: ''};
function renderP2POnchain(){
  const oc = p2pOnchainMiei[0];
  ULTIMA = oc ? {richiamo: chatOcRichiamoHTML(oc), riquadro: chatOcBloccoHTML(oc)} : {richiamo: '', riquadro: ''};
}
""" + pezzi + r"""
globalThis.document = {visibilityState: 'visible', documentElement: {clientHeight: 800}, activeElement: null};
const log0 = console.log; console.log = () => {};
const dormi = ms => new Promise(r => setTimeout(r, ms));
async function quieto(){
  for (let i = 0; i < 80; i++) {
    await dormi(25);
    const inVolo = Object.keys(p2pChatScInVolo).length + (p2pChatScNovitaInVolo ? 1 : 0) + subito;
    if (!inVolo && i >= 4) return;
  }
}
const foto = () => {
  const id = p2pOnchainMiei.length ? String(p2pOnchainMiei[0].ordine) : '';
  const o = id ? chatScRigaP2P(id) : null;
  const c = id ? chatScDiP2P(id) : null;
  return {riquadro: !!ULTIMA.riquadro, richiamo: !!ULTIMA.richiamo, aperto: chatScApertoP2P(),
          chiave: !!(c && c.sk), modo: (o && chatScServeP2P(o)) ? chatScPiedeP2P(o, c).modo : '',
          msgs: c ? (c.msgs || []).filter(m => !m.sis).map(m => (m.mio ? 'io: ' : 'altro: ') + m.testo) : [],
          mie: o ? o.mie.length : 0, peers: o ? o.peers.length : 0, cassetto: !!c,
          caso: !!(c && c.ordineSk), modDato: c && c.modDato ? Object.keys(c.modDato).length : 0,
          avvisoScambio: ULTIMA.riquadro.indexOf('Non uscire dallo scambio') >= 0,
          avvisoOrdine: ULTIMA.riquadro.indexOf('Non pagare fuori dall') >= 0,
          chiamate: chiamate.slice(), diario: DIARIO.slice()};
};
(async () => {
  const fuori = [];
  for (const passo of PASSI) {
    const [cosa, a, b, c, d, e, f] = passo.split('|');
    try {
      if (cosa === 'profilo') {
        if (!_box.MAZZO) { const sk = NT.generateSecretKey();
          _box.MAZZO = JSON.stringify({sk: NT.utils.bytesToHex(sk), pub: NT.getPublicKey(sk), indice: 0}); }
        fuori.push({passo: passo, chiaveOrdine: chiaveOrdineMercatinoP2P(mazzoMostro().sk, a).pub});
      } else if (cosa === 'scambio') {
        /* la pagina dello scambio si apre: la riga com'e' in «I miei scambi» */
        p2pOnchainMiei = [{id: Number(a), ordine: b, ruolo: c, parte: d, stato: e, chat: f || '', altro: 'Vera Rossi'}];
        p2pOnchainAperto = Number(a);
        _box.SCAMBIO = JSON.stringify(p2pOnchainMiei[0]);
        renderP2POnchain(); await quieto(); await quieto();
        renderP2POnchain();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'battito') {
        chatScBattitoP2P(); await quieto(); await quieto(); renderP2POnchain();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'scrivi') {
        await chatScInviaP2P(String(p2pOnchainMiei[0].ordine), a); await quieto(); renderP2POnchain();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'moderatori') {
        p2pChatScModTentato = {};
        await chatScAiModeratoriP2P(String(p2pOnchainMiei[0].ordine)); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'novita') {
        p2pChatScNovitaInVolo = null;
        await chatScNovitaP2P(); await quieto(); renderP2POnchain();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'nuovomod') {
        if (!_box.MOD) { const sk = NT.generateSecretKey();
          _box.MOD = JSON.stringify({sk: NT.utils.bytesToHex(sk), pub: NT.getPublicKey(sk)}); }
        fuori.push({passo: passo, pub: JSON.parse(_box.MOD).pub});
      } else if (cosa === 'leggimod') {
        /* il moderatore legge lo scambio `a` dalla sua rotta, col motore vero */
        const k = JSON.parse(_box.MOD);
        const dd = await (await fetch(API_BASE + '/p2p/moderazione/chat', {method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-Tg-Init-Data': authHdr()},
          body: JSON.stringify({ordine: a})})).json();
        const l = chatPartiApriP2P(k, dd.lati || {}, a, dd);
        fuori.push({passo: passo, letti: l.msgs.map(m => m.lato + ': ' + m.testo), mute: l.mute,
                    html: chatOcModHTML({ruolo: 'moderatore', chat: 'moderazione', ordine: a}).indexOf('chatsc-mod') >= 0});
      }
    } catch(x) { fuori.push({passo: passo, ESPLOSO: String(x && x.stack || x)}); }
  }
  fs.writeFileSync(STATO, JSON.stringify(_box));
  console.log = log0;
  console.log(JSON.stringify(fuori));
  process.exit(0);
})();
"""


async def giro():
    SRV = banco.SRV
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    SRV.p2p_onchain_leva = lambda: True
    SRV.P2P_CHAT_SCAMBIO = True
    SRV.MERCATINO_CHAT_ORDINI = False
    leggi, invia = SRV.chat_leggi_p2p, SRV.chat_invia_p2p
    scorta, chiama = SRV.chat_scorta_p2p, SRV.chat_chiama_p2p
    novita, mod_chat = SRV.chat_novita_p2p, SRV.moderazione_chat_p2p

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        DETTI.append((chi, testo, bottone))
    SRV.notifica = notifica_finta
    SRV.ADMIN_IDS = list(set(list(getattr(SRV, "ADMIN_IDS", [])) + [ADMIN]))
    for tg, nome in ((V, "Venditore"), (C, "Compratore"), (X, "Estraneo"), (ADMIN, "Admin")):
        cs.ACCESSO[tg] = {"x_tg_init_data": f"collaudo:{tg}:{nome}", "barattolo_sessione": ""}
    con = banco.con_db()
    for tg, nome in ((V, "Vera Rossi"), (C, "Carlo Bianchi"), (X, "Estraneo"), (ADMIN, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                    "VALUES(?,?,?,1,'')", (tg, nome, f"neg{tg}"))
    con.commit()
    con.close()
    SRV.P2P_CHAT_PRESENTE_S = cs.PRESENTE

    async def sezione(numero, titolo, corpo_sezione):
        print(f"\n{numero}) {titolo}")
        try:
            await corpo_sezione()
        except Exception as e:
            import traceback
            traceback.print_exc()
            prova(f"{numero}) la sezione gira", "", f"{type(e).__name__}: {e}")

    async def s1():
        oid, o = nuovo_scambio("preso")
        SRV.P2P_CHAT_SCAMBIO = False
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("LA CHAT DEL LIGHTNING SPENTA: il ritiro on-chain dice «spenta» (la stessa leva)",
              (False, True), (r.get("aperta"), r.get("spenta")))
        prova("...l'invio e' un 409", 409, cs.no(await cs.chiama(invia, C, {
            "ordine": o, "tipo": "msg", "busta": cs.busta("x")})))
        prova("...la riga dello scambio non dice niente della chat", "", chat_della_riga(oid, C))
        SRV.P2P_CHAT_SCAMBIO = True
        SRV.p2p_onchain_leva = lambda: False
        prova("L'ON-CHAIN DEL P2P SPENTO: la chat on-chain non esiste (409)", 409,
              cs.no(await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})))
        SRV.p2p_onchain_leva = lambda: True
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("...riaccese: la chat dello scambio preso e' aperta", True, r.get("aperta"))

    async def s2():
        oid, o = nuovo_scambio("pending", compratore=0)
        r = await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("PRIMA DELLA PRESA la chat non c'e' (nel libro non c'e' ancora nessuno a cui scrivere)",
              (False, True), (r.get("aperta"), r.get("finita")))
        prova("...e la riga non la nomina", "", chat_della_riga(oid, V))
        oid, o = nuovo_scambio("preso")
        prova("DALLA PRESA: aperta per chi vende e per chi compra",
              (True, True), ((await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})).get("aperta"),
                             (await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})).get("aperta")))
        prova("...un estraneo e' un 403", 403, cs.no(await cs.chiama(leggi, X, {"ordine": o, "dopo": 0})))
        prova("...la riga dice 'aperta' alle due parti, niente all'estraneo e niente all'admin "
              "fuori dalla disputa", ("aperta", "aperta", "", ""),
              (chat_della_riga(oid, V), chat_della_riga(oid, C), chat_della_riga(oid, X),
               chat_della_riga(oid, ADMIN, admin=True)))
        for st in ("depositato", "euro_inviati", "disputa"):
            metti(oid, st)
            prova(f"...e resta aperta a '{st}'", True,
                  (await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})).get("aperta"))
        prova("UN ID STORTO non passa per una chat on-chain (e non arriva al giudice)", False,
              SRV._chat_chiavi_dal_server("bar-onchain-XYZ"))

    async def s3():
        scorta_pulita()
        oid, o = nuovo_scambio("preso")
        k_c, k_v = cs.chiave(0x31), cs.chiave(0x32)
        r = await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": k_c})
        prova("LE CHIAVI D'ORDINE: chi compra dichiara la sua, il server la tiene", True, r.get("nuova"))
        r = await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("...chi vende la ritrova come chiave dell'altra parte, e sa che non ha ancora la sua",
              ([k_c], [], False), (r.get("peers"), r.get("mie"), "altro_senza_chiave" in r))
        prova("...la stessa chiave non la prende l'altra parte", 409,
              cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": k_c})))
        # LA SCORTA: con la sola leva della chat del Lightning accesa
        r = await cs.chiama(scorta, V, {"lucchetti": [{"pub": k_v, "seme": ""}]})
        prova("LA SCORTA DI LUCCHETTI vale anche qui: a chat del mercatino SPENTA la si riempie lo stesso",
              (False, 1), (bool(r.get("spenta")), r.get("quante")))
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("...al ritiro di chi compra il lucchetto di chi vende diventa la sua chiave d'ordine: "
              "si scrive subito", [k_v], r.get("peers"))
        SRV.P2P_CHAT_SCAMBIO = False
        r = await cs.chiama(scorta, V, {"lucchetti": []})
        prova("...e a chat del Lightning spenta (e mercatino spento) la scorta dice «spenta»", True,
              bool(r.get("spenta")))
        SRV.P2P_CHAT_SCAMBIO = True

    async def s4():
        oid, o = nuovo_scambio("depositato")
        DETTI.clear()
        await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        await asyncio.sleep(cs.ASSENTE)
        r = await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta("ciao segreto")})
        prova("IL MESSAGGIO entra", True, isinstance(r.get("n"), int))
        await asyncio.sleep(0.5)
        r = await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("...e arriva a chi vende identico", [cs.busta("ciao segreto")],
              [b["busta"] for b in r.get("buste") or [] if b.get("tipo") == "msg"])
        a = avvisi_chat()
        prova("L'AVVISO: uno, a chi vende, «nello scambio on-chain»", [(V, True)],
              [(chi, "nello scambio on-chain" in t) for chi, t, b in a])
        prova("...col bottone «🟠 Apri lo scambio» che porta DRITTO alla chat",
              (SRV.P2P_ONCHAIN_BOTTONE, f"{SRV.LINK_LIBRO_P2P}?scambio={o}&chat=1"),
              a[0][2] if a else None)
        prova("...e il testo del messaggio non c'e'", False, any("segreto" in t for _, t, _ in a))
        prova("...dentro Telegram il bottone apre la Mini App sullo scambio, dritto alla chat",
              f"scambio_{o}_chat", SRV._startapp_da_link(a[0][2][1]) if a else None)

    async def s5():
        scorta_pulita()
        oid, o = nuovo_scambio("preso")
        DETTI.clear()
        await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x41)})
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("«VUOLE SCRIVERTI»: chi vende non ha nessuna chiave, chi compra lo sa", True,
              bool(r.get("altro_senza_chiave")))
        r = await cs.chiama(chiama, C, {"ordine": o})
        prova("...la chiamata parte", True, bool(r.get("avvisato")))
        d = [x for x in DETTI if "vuole scriverti" in x[1]]
        prova("...a chi vende, «nello scambio on-chain», col bottone dritto alla chat",
              [(V, True, (SRV.P2P_ONCHAIN_BOTTONE, f"{SRV.LINK_LIBRO_P2P}?scambio={o}&chat=1"))],
              [(chi, "nello scambio on-chain" in t, b) for chi, t, b in d])
        r = await cs.chiama(chiama, C, {"ordine": o})
        prova("...una volta sola", (True, 1), (bool(r.get("gia")), len([x for x in DETTI if "vuole scriverti" in x[1]])))

    async def s6():
        oid, o = nuovo_scambio("euro_inviati")
        con = banco.con_db()
        kmod = cs.chiave(0xAB)
        con.execute("INSERT OR REPLACE INTO p2p_moderatori(tg_id, chiave, creata) VALUES(?,?,0)",
                    (ADMIN, kmod))
        con.commit()
        con.close()
        prova("PRIMA DELLA DISPUTA la chiave al moderatore non parte (409)", 409,
              cs.no(await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": kmod,
                                               "busta": cs.busta("pacco")})))
        prova("...e il moderatore non legge (409)", 409, cs.no(await cs.chiama(mod_chat, ADMIN, {"ordine": o})))
        metti(oid, "disputa")
        prova("IN DISPUTA la chiave parte, da TUTTE E DUE le parti", (True, True),
              (isinstance((await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": kmod,
                                                       "busta": cs.busta("pacco c")})).get("n"), int),
               isinstance((await cs.chiama(invia, V, {"ordine": o, "tipo": "mod", "per": kmod,
                                                       "busta": cs.busta("pacco v")})).get("n"), int)))
        r = await cs.chiama(mod_chat, ADMIN, {"ordine": o})
        prova("...il moderatore legge: le due chiavi, una per lato", ["compra", "vende"],
              sorted(k["lato"] for k in r.get("chiavi") or []))
        prova("...un estraneo no (403)", 403, cs.no(await cs.chiama(mod_chat, X, {"ordine": o})))
        prova("...e la riga dice 'moderazione' al moderatore che non e' una parte", "moderazione",
              chat_della_riga(oid, ADMIN, admin=True))

    async def s7():
        oid, o = nuovo_scambio("depositato")
        await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta("pallino")})
        r = await cs.chiama(novita, C, {"ordine": o, "ordini": [o]})
        prova("IL PALLINO: lo scambio on-chain sta nella domanda, col numero dell'ultimo messaggio",
              (True, []), ((r.get("ultimi") or {}).get(o, 0) > 0, r.get("finite")))
        prova("...prima della fine le righe ci sono", True, righe_cassetto(o)[0] > 0)
        metti(oid, "rilasciato")
        SRV._chat_p2p_spazza(conti={})
        prova("A SATS RILASCIATI la scopa porta via tutto, DAL FILE", (0, 0, 0, 0), righe_cassetto(o))
        r = await cs.chiama(novita, C, {"ordine": o, "ordini": [o]})
        prova("...il pallino lo dice finito (il telefono butta chiave e messaggi)", [o], r.get("finite"))
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("...e il ritiro dice chiusa e finita", (False, True), (r.get("aperta"), r.get("finita")))
        prova("...la riga non nomina piu' la chat", "", chat_della_riga(oid, C))
        for st in ("rimborsato", "annullato", "scaduto"):
            oid2, o2 = nuovo_scambio("preso")
            await cs.chiama(invia, C, {"ordine": o2, "tipo": "msg", "busta": cs.busta("x")})
            metti(oid2, st)
            SRV._chat_p2p_spazza(conti={})
            prova(f"...lo stesso a '{st}'", 0, righe_cassetto(o2)[0])

    async def s8():
        import shutil
        import subprocess
        import tempfile
        import collaudo_tolti_ovunque as tolti
        node = shutil.which("node")
        if not node:
            prova("node c'e'", True, False)
            return
        scorta_pulita()
        oid, o = nuovo_scambio("depositato")
        srv, base = tolti.avvia_ponte()
        cart = tempfile.mkdtemp(prefix="chat_onchain_")
        mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
        prog = os.path.join(cart, "telefono.js")
        open(prog, "w", encoding="utf-8").write(dispositivo(mini))
        chi = {"C": (C, "Compratore"), "V": (V, "Venditore"), "M": (ADMIN, "Admin")}

        def telefono(nome, *passi):
            conto, come_si_chiama = chi[nome]
            r = subprocess.run([node, prog, os.path.join(banco.QUI, "vendor", "nostr.bundle.js"),
                                os.path.join(cart, nome + ".json"), base, str(conto), come_si_chiama, *passi],
                               capture_output=True, text=True, encoding="utf-8", timeout=120)
            try:
                fuori = json.loads(r.stdout.strip().splitlines()[-1])
            except Exception:
                fuori = [{"ERRORE": (r.stdout or "")[-300:] + (r.stderr or "")[-700:]}] * len(passi)
            return fuori[-1]

        def tipi(conto):
            return [r[0] for r in cs.cassetto("SELECT tipo FROM buste WHERE ordine=? AND da=? ORDER BY n", o, conto)]
        try:
            k = telefono("C", f"profilo|{o}").get("chiaveOrdine") or ""
            f = telefono("C", f"scambio|{oid}|{o}|venditore|compro|depositato|aperta")
            prova("CHI COMPRA (col profilo di scambio) apre lo scambio on-chain: il riquadro e il richiamo ci "
                  "sono, con l'avviso DELLO SCAMBIO (non dell'ordine); la chiave d'ordine e' quella del profilo",
                  (True, True, True, False, o, [k], ""),
                  (f.get("riquadro"), f.get("richiamo"), f.get("avvisoScambio"), f.get("avvisoOrdine"),
                   f.get("aperto"),
                   [r[0] for r in cs.cassetto("SELECT pub FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, C)],
                   f.get("ESPLOSO", "") or f.get("ERRORE", "")))
            prova("...chi vende non ha ancora nessuna chiave: «🔔 Avvisa»", "chiama", f.get("modo"))
            f = telefono("V", f"scambio|{oid}|{o}|compratore|vendo|depositato|aperta")
            prova("CHI VENDE, SENZA profilo: la chiave nasce a caso, si presenta, e scrive subito",
                  (True, True, "scrivi", ["chiave", "saluto"]),
                  (f.get("riquadro"), f.get("caso"), f.get("modo"), tipi(V)))
            f = telefono("C", "battito")
            prova("...chi compra al suo battito presenta la sua chiave e si scrive",
                  ("scrivi", ["chiave", "saluto"]), (f.get("modo"), tipi(C)))
            telefono("C", "scrivi|Ho mandato i 90 euro su Revolut")
            f = telefono("V", "battito", "scrivi|Arrivati, libero i sats")
            prova("I MESSAGGI viaggiano cifrati nei due sensi",
                  ["altro: Ho mandato i 90 euro su Revolut", "io: Arrivati, libero i sats"], f.get("msgs"))
            prova("...sul server, buste che non dicono niente", False,
                  any("Revolut" in r[0] for r in cs.cassetto("SELECT busta FROM buste WHERE ordine=?", o)))
            f = telefono("C", "battito")
            prova("...e chi compra le legge",
                  ["io: Ho mandato i 90 euro su Revolut", "altro: Arrivati, libero i sats"], f.get("msgs"))
            prova("PRIMA DELLA DISPUTA nessun telefono da' la chiave ai moderatori", [],
                  [t for t in tipi(C) + tipi(V) if t == "mod"])
            # LA DISPUTA: il moderatore con una chiave VERA
            pub = telefono("M", "nuovomod").get("pub")
            con = banco.con_db()
            con.execute("INSERT OR REPLACE INTO p2p_moderatori(tg_id, chiave, creata) VALUES(?,?,0)",
                        (ADMIN, pub))
            con.commit()
            con.close()
            metti(oid, "disputa")
            fc = telefono("C", f"scambio|{oid}|{o}|venditore|compro|disputa|aperta", "moderatori")
            fv = telefono("V", f"scambio|{oid}|{o}|compratore|vendo|disputa|aperta", "moderatori")
            prova("IN DISPUTA i telefoni di TUTTE E DUE le parti danno la chiave al moderatore",
                  (1, 1), (fc.get("modDato"), fv.get("modDato")))
            f = telefono("M", f"leggimod|{o}")
            prova("...e il moderatore LEGGE la chat, col lato giusto, col motore vero",
                  (["compra: Ho mandato i 90 euro su Revolut", "vende: Arrivati, libero i sats"], 0, True),
                  (f.get("letti"), f.get("mute"), f.get("html")))
            # LA FINE
            metti(oid, "rilasciato")
            SRV._chat_p2p_spazza(conti={})
            f = telefono("C", f"scambio|{oid}|{o}|venditore|compro|rilasciato|", "novita")
            prova("A SATS RILASCIATI: niente riquadro, e il pallino fa buttare chiave e messaggi",
                  (False, False, False), (f.get("riquadro"), f.get("richiamo"), f.get("cassetto")))
        finally:
            srv.shutdown()

    await sezione(1, "le leve", s1)
    await sezione(2, "l'accensione alla presa", s2)
    await sezione(3, "le chiavi d'ordine e la scorta", s3)
    await sezione(4, "il messaggio e l'avviso", s4)
    await sezione(5, "«vuole scriverti»", s5)
    await sezione(6, "la disputa e il moderatore", s6)
    await sezione(7, "il pallino e la fine", s7)
    await sezione(8, "il client vero in node", s8)


def main():
    banco.avvio()
    banco.semina()
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
