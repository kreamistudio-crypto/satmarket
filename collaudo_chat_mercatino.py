# -*- coding: utf-8 -*-
"""
LA CHAT NEGLI ORDINI DEL MERCATINO, SUL SERVER VERO (16 ott 2026,
cantiere chat-mercatino, decisione di Andrea).

La chat dello scambio P2P, esattamente com'e', anche negli ordini del
mercatino: si ACCENDE quando chi compra paga, si CHIUDE e si CANCELLA
(messaggi, file, chiavi) a ordine concluso; in disputa resta fino alla
decisione e il moderatore la legge, perche' i telefoni di tutte e due
le parti gli danno la chiave. Un ordine nel cassetto si chiama
`m<numero>`; le rotte sono quelle della chat dello scambio.

`prove.py` difende i giudici estratti (`prove_chat_mercatino`). Qui
girano le ROTTE VERE — `/api/p2p/chat/leggi`, `/invia`, `/allegato`,
`/allegato/leggi`, `/novita`, `/moderatori`, `/api/p2p/moderazione/chat`
e `/chat/allegato`, `/api/orders` — su database usa-e-getta, con
l'autenticazione VERA, e il P2P SPENTO per tutti (la chat del mercatino
non lo chiede):

   1. la leva spenta: niente chat, e nessuna riga la nomina;
   2. l'accensione al pagamento: prima no, da 'locked' si', e per un
      estraneo mai;
   3. le chiavi d'ordine: le presenta il server, una chiave e' di una
      parte sola, e c'e' un tetto;
   4. messaggi e allegati: arrivano all'altra parte identici, a un
      estraneo no;
   5. l'avviso: un «c'e' da leggere» col numero dell'ordine e il tasto che
      lo apre, MAI il testo; e nel journal niente del messaggio;
   6. la disputa: la chiave al moderatore solo a ordine in disputa; il
      moderatore legge solo con la sua chiave dichiarata; la chat resta
      aperta in disputa e nel reso;
   7. la cancellazione a ordine concluso — confermato, liberato,
      rimborsato, deciso — le righe spariscono DAL FILE, e la riga
      dell'ordine dice «chiusa»; 'annullato' (mai pagato) non ne ha;
   8. la rete dei 30 giorni non tocca un ordine del mercatino aperto;
   9. il pallino: gli ordini del mercatino nella stessa domanda;
  10. IL CLIENT VERO IN NODE contro il server vero: chi compra col profilo
      di scambio, chi vende senza (la chiave nasce a caso), i messaggi in
      due sensi, il secondo dispositivo di chi vende che «continua la chat
      qui», la chiave ai moderatori dai due telefoni in disputa, e la
      fine: il telefono butta chiave e messaggi e mostra «chat chiusa».

NON TOCCA NIENTE DI VERO: il config di cartone di
`collaudo_pagamento_p2p`, niente Telegram, niente relay. Le buste delle
prime sezioni sono testo a caso: il server non le apre; la crittografia
vera gira nella sezione 10.

USO:  python collaudo_chat_mercatino.py
"""

import asyncio
import contextlib
import io
import json
import os
import sys
import time

import collaudo_pagamento_p2p as banco
import collaudo_chat_scambio as cs
import collaudo_allegati_chat as ca

prova = banco.prova
V, C, X, ADMIN, ADMIN2 = 222, 111, 333, 999, 998
DETTI = []


def adesso():
    return int(time.time())


def nuovo_ordine(stato="creato", venditore=V, compratore=C):
    """Una riga di `ordini`, com'e' dopo il checkout. Torna il numero."""
    con = banco.con_db()
    n = con.execute("INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, prezzo_sats, "
                    "stato, creato, aggiornato) VALUES(0,?,?,15000,?,?,?)",
                    (compratore, venditore, stato, adesso(), adesso())).lastrowid
    con.commit()
    con.close()
    return n


def metti(n, stato):
    con = banco.con_db()
    con.execute("UPDATE ordini SET stato=? WHERE id=?", (stato, n))
    con.commit()
    con.close()


def righe_cassetto(o):
    """Quante righe di quest'ordine ci sono nel cassetto, tabella per tabella."""
    return tuple(len(cs.cassetto(f"SELECT 1 FROM {t} WHERE ordine=?", o))
                 for t in ("buste", "letture", "allegati", "chiavi_ordine"))


def chat_della_riga(chi, n):
    """Cosa dice `/api/orders` della chat dell'ordine `n`, a chi chiede."""
    righe = banco.SRV.miei_ordini(ordine=n if chi in (ADMIN, ADMIN2) else 0, **cs.ACCESSO[chi])
    for r in righe:
        if r["id"] == n:
            return r.get("chat")
    return None


def scorta_pulita():
    """(20 ott 2026) TELEFONI NUOVI: la scorta di lucchetti lasciata dai
    telefoni di una sezione di prima non e' di questi (ogni sezione ha le
    sue memorie), e un lucchetto bruciato per un ordine nuovo andrebbe a un
    telefono che non ce l'ha. Lo stesso caso, nella vita vera, e' un
    dispositivo perso senza profilo di scambio: «Continua la chat qui»."""
    cc = banco.SRV.db_chat()
    try:
        cc.execute("DELETE FROM scorta")
        cc.commit()
    finally:
        cc.close()


def avvisi_chat():
    return [(chi, t, b) for chi, t, b in DETTI if t.startswith("💬 <b>Hai un nuovo messaggio")]


def dispositivo(mini):
    """IL TELEFONO, per la sezione 10: le funzioni VERE di miniapp.html —
    tutto il blocco della chat, con l'adattatore del mercatino — in node,
    col bundle vero, un localStorage che vive in un file (uno per
    telefono) e la `fetch` vera verso il ponte. Di cartone ci sono la
    pagina dell'ordine (il richiamo e il riquadro nascono come in
    `openOrder`) e il profilo di scambio (c'e' o non c'e')."""
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
function chiaveModeratoreP2P(){ return null; } function archivioModP2P(){ return {}; }
function linkPdfPayCodeP2P(){ return null; } function payCodeScambioP2P(){ return ''; }
async function caricaNostrTools(){}
function vistaAttivaP2P(){ return 'view-ordine'; }
/* IL PROFILO DI SCAMBIO: c'e' se il passo `profilo` l'ha fatto nascere */
function mazzoMostro(){ return _box.MAZZO ? JSON.parse(_box.MAZZO) : null; }
async function adottaProfiloContoP2P(){ return mazzoMostro(); }
function el(id){ return id === 'p2pChatScLista' ? {getBoundingClientRect: () => ({top: 300, bottom: 560, height: 260})} : null; }
/* LA PAGINA DELL'ORDINE, di cartone: i due pezzi della chat nascono come in `openOrder` */
let orders = _box.ORDINE ? [JSON.parse(_box.ORDINE)] : [], currentOrder = orders[0] || null, ULTIMA = {richiamo: '', riquadro: ''};
function ridisegnaOrdine(o){
  currentOrder = orders.find(x => x.id === o.id) || o;
  ULTIMA = {richiamo: chatMercRichiamoHTML(currentOrder), riquadro: chatMercBloccoHTML(currentOrder)};
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
  const id = currentOrder ? 'm' + currentOrder.id : '';
  const o = id ? chatScRigaP2P(id) : null;
  const c = id ? chatScDiP2P(id) : null;
  return {riquadro: !!ULTIMA.riquadro, chiusa: ULTIMA.riquadro.indexOf(CHATSC_MERC_CHIUSA) >= 0,
          richiamo: !!ULTIMA.richiamo, chiave: !!(c && c.sk), laSua: !!(c && c.loro),
          modo: (o && chatScServeP2P(o)) ? chatScPiedeP2P(o, c).modo : '',
          msgs: c ? (c.msgs || []).filter(m => !m.sis).map(m => (m.mio ? 'io: ' : 'altro: ') + m.testo) : [],
          sis: c ? (c.msgs || []).filter(m => m.sis).length : 0, muti: c ? (c.muti | 0) : 0,
          mie: o ? o.mie.length : 0, peers: o ? o.peers.length : 0, cassetto: !!c,
          caso: !!(c && c.ordineSk), modDato: c && c.modDato ? Object.keys(c.modDato).length : 0,
          avviso: ULTIMA.riquadro.indexOf('Non pagare fuori dall') >= 0,
          chiamate: chiamate.slice(), diario: DIARIO.slice()};
};
(async () => {
  const fuori = [];
  for (const passo of PASSI) {
    const [cosa, a, b, c, d] = passo.split('|');
    try {
      if (cosa === 'stessoprofilo') {
        /* un altro dispositivo dello STESSO profilo di scambio (il seme dell'account) */
        _box.MAZZO = JSON.stringify({sk: a, pub: NT.getPublicKey(NT.utils.hexToBytes(a)), indice: 0});
        fuori.push({passo: 'stessoprofilo'});
      } else if (cosa === 'profilo') {
        if (!_box.MAZZO) { const sk = NT.generateSecretKey();
          _box.MAZZO = JSON.stringify({sk: NT.utils.bytesToHex(sk), pub: NT.getPublicKey(sk), indice: 0}); }
        fuori.push({passo: passo, chiaveOrdine: chiaveOrdineMercatinoP2P(mazzoMostro().sk, a).pub});
      } else if (cosa === 'ordine') {
        /* la pagina dell'ordine si apre: l'ordine com'e' nella lista */
        orders = [{id: Number(a), role: b, state: c, chat: d,
                   voltoVenditore: {nome: 'Vera Rossi'}, voltoCompratore: {nome: 'Carlo Bianchi'}}];
        _box.ORDINE = JSON.stringify(orders[0]);
        ridisegnaOrdine(orders[0]); await quieto(); await quieto();
        ridisegnaOrdine(orders[0]);
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'battito') {
        chatScBattitoP2P(); await quieto(); await quieto(); ridisegnaOrdine(currentOrder);
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'scrivi') {
        await chatScInviaP2P('m' + currentOrder.id, a); await quieto(); ridisegnaOrdine(currentOrder);
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'continua') {
        await continuaChatScambioP2P(); await quieto(); await quieto(); ridisegnaOrdine(currentOrder);
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'moderatori') {
        p2pChatScModTentato = {};
        await chatScAiModeratoriP2P('m' + currentOrder.id); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'foto') {
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'scorta') {
        /* (20 ott 2026) Barattolo aperto su un'altra pagina: la scorta di lucchetti si riempie */
        await chatScortaP2P(true);
        fuori.push({passo: passo});
      } else if (cosa === 'nuovomod') {
        /* un moderatore con una chiave VERA, nata qui */
        if (!_box.MOD) { const sk = NT.generateSecretKey();
          _box.MOD = JSON.stringify({sk: NT.utils.bytesToHex(sk), pub: NT.getPublicKey(sk)}); }
        fuori.push({passo: passo, pub: JSON.parse(_box.MOD).pub});
      } else if (cosa === 'leggimod') {
        /* il moderatore legge l'ordine `a` dalla sua rotta; poi le chiavi del
           pacco di `a` contro le buste dell'ordine `b` */
        const k = JSON.parse(_box.MOD);
        const leggi = async o => (await fetch(API_BASE + '/p2p/moderazione/chat', {method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-Tg-Init-Data': authHdr()},
          body: JSON.stringify({ordine: o})})).json();
        const d1 = await leggi(a), d2 = await leggi(b);
        const l1 = chatPartiApriP2P(k, d1.lati || {}, a, d1);
        const lati1 = [].concat((d1.lati || {}).compra || [], (d1.lati || {}).vende || []);
        const segreti = [];
        for (const p of (d1.chiavi || [])) for (const t of lati1) {
          try { const pacco = JSON.parse(NT.nip44.decrypt(p.busta, NT.nip44.getConversationKey(NT.utils.hexToBytes(k.sk), t)));
                (pacco.chiavi || []).forEach(x => segreti.push(x.k)); break; } catch(e) {}
        }
        let aperte = 0;
        for (const s of segreti) for (const bb of (d2.buste || []))
          try { NT.nip44.decrypt(bb.busta, NT.utils.hexToBytes(s)); aperte++; } catch(e) {}
        const l2 = chatPartiApriP2P(k, d2.lati || {}, b, {buste: d2.buste || [], chiavi: d1.chiavi || []});
        fuori.push({passo: passo, letti: l1.msgs.map(m => m.lato + ': ' + m.testo), mute: l1.mute,
                    segreti: segreti.length, buste2: (d2.buste || []).length, aperteAltro: aperte,
                    altroLetti: l2.msgs.length, altroMute: l2.mute});
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
    # IL P2P E' SPENTO PER TUTTI: la chat del mercatino non lo chiede
    SRV._p2p_per = lambda *a, **k: {"attivo": False}
    leggi, invia = SRV.chat_leggi_p2p, SRV.chat_invia_p2p
    moderatori, mod_chat = SRV.chat_moderatori_p2p, SRV.moderazione_chat_p2p

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        DETTI.append((chi, testo, bottone))
    SRV.notifica = notifica_finta
    SRV.ADMIN_IDS = list(set(list(getattr(SRV, "ADMIN_IDS", [])) + [ADMIN, ADMIN2]))
    for tg, nome in ((V, "Venditore"), (C, "Compratore"), (X, "Estraneo"),
                     (ADMIN, "Admin"), (ADMIN2, "Admindue")):
        cs.ACCESSO[tg] = {"x_tg_init_data": f"collaudo:{tg}:{nome}", "barattolo_sessione": ""}
    con = banco.con_db()
    for tg, nome in ((V, "Vera Rossi"), (C, "Carlo Bianchi"), (X, "Estraneo"),
                     (ADMIN, "Admin"), (ADMIN2, "Admindue")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                    "VALUES(?,?,?,1,'')", (tg, nome, f"neg{tg}"))
    kmod = cs.chiave(0xAB)
    con.execute("INSERT OR REPLACE INTO p2p_moderatori(tg_id, chiave, creata) VALUES(?,?,0)",
                (ADMIN, kmod))
    con.commit()
    con.close()
    SRV.P2P_CHAT_PRESENTE_S = cs.PRESENTE

    async def sezione(numero, titolo, corpo_sezione):
        print(f"\n{numero}) {titolo}")
        try:
            await corpo_sezione()
        except Exception as e:
            prova(f"{numero}) la sezione gira", "", f"{type(e).__name__}: {e}")

    async def s1():
        SRV.MERCATINO_CHAT_ORDINI = False
        n = nuovo_ordine("locked")
        o = f"m{n}"
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("LEVA SPENTA (di serie): il ritiro dice «spenta», niente da leggere",
              (False, True), (r.get("aperta"), r.get("spenta")))
        prova("...l'invio e' un 409", 409, cs.no(await cs.chiama(invia, C, {"ordine": o, "tipo": "msg",
                                                                            "busta": cs.busta("x")})))
        prova("...e la riga dell'ordine non nomina nessuna chat", ("", ""),
              (chat_della_riga(C, n), chat_della_riga(V, n)))
        prova("...nel config d'esempio sta spenta", True,
              "\nMERCATINO_CHAT_ORDINI = False\n" in open(os.path.join(banco.QUI, "config_esempio.py"),
                                                          encoding="utf-8").read())
        SRV.MERCATINO_CHAT_ORDINI = True

    async def s2():
        n = nuovo_ordine("creato")
        o = f"m{n}"
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("PRIMA DEL PAGAMENTO la chat non c'e': il ritiro dice chiusa, e la riga niente",
              (False, False, "", ""), (r.get("aperta"), r.get("spenta"), chat_della_riga(C, n),
                                       chat_della_riga(V, n)))
        prova("...e non si scrive", 409, cs.no(await cs.chiama(invia, C, {"ordine": o, "tipo": "msg",
                                                                         "busta": cs.busta("x")})))
        metti(n, "locked")
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        b = await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("CHI COMPRA HA PAGATO ('locked'): aperta per tutti e due, vuota, a P2P spento",
              [(True, [], [], []), (True, [], [], [])],
              [(x.get("aperta"), x.get("buste"), x.get("mie"), x.get("peers")) for x in (a, b)])
        prova("...la riga dell'ordine lo dice alle due parti", ("aperta", "aperta"),
              (chat_della_riga(C, n), chat_della_riga(V, n)))
        prova("UN ESTRANEO: 403, sempre", (403, 403),
              (cs.no(await cs.chiama(leggi, X, {"ordine": o, "dopo": 0})),
               cs.no(await cs.chiama(invia, X, {"ordine": o, "tipo": "msg", "busta": cs.busta("x")}))))
        prova("...l'admin non e' una parte: niente chat da leggere fuori dalla disputa", ("", 403),
              (chat_della_riga(ADMIN, n), cs.no(await cs.chiama(leggi, ADMIN, {"ordine": o, "dopo": 0}))))
        prova("un ordine che non c'e': nessuno ne e' una parte, 403 come per uno scambio sconosciuto", 403,
              cs.no(await cs.chiama(leggi, C, {"ordine": "m987654", "dopo": 0})))
        prova("una forma storta non passa: 400 (a P2P spento il 409 del P2P)", True,
              cs.no(await cs.chiama(leggi, C, {"ordine": "m0", "dopo": 0})) in (400, 409))

    async def s3():
        n = nuovo_ordine("locked")
        o = f"m{n}"
        kc, kv = cs.chiave(0x31), cs.chiave(0x32)
        r = await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": kc})
        prova("LA CHIAVE D'ORDINE: chi compra dichiara la sua parte pubblica", (True, True),
              (r.get("ok"), r.get("nuova")))
        prova("...ridichiarata non conta due volte", False,
              (await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": kc})).get("nuova"))
        prova("...una chiave gia' dell'altra parte non si prende: 409", 409,
              cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": kc})))
        prova("...una forma storta: 400", 400,
              cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": "z" * 64})))
        await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": kv})
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        b = await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("IL SERVER LE PRESENTA: a ognuno le sue (mie) e quelle dell'altra parte (peers)",
              [([kc], [kv]), ([kv], [kc])], [(x.get("mie"), x.get("peers")) for x in (a, b)])
        for i in range(SRV.CHAT_MERCATINO_CHIAVI_MAX - 1):
            await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x40 + i)})
        prova(f"IL TETTO: {SRV.CHAT_MERCATINO_CHIAVI_MAX} chiavi per parte, la successiva e' un 409", 409,
              cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x4F)})))
        prova("...e l'ultima dichiarata e' l'ultima che l'altra parte vede", cs.chiave(0x40 + SRV.CHAT_MERCATINO_CHIAVI_MAX - 2),
              ((await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})).get("peers") or [""])[-1])
        prova("la chiave d'ordine e' solo del mercatino: in uno scambio P2P non e' un tipo", True,
              "chiave_ordine" not in SRV.P2P_CHAT_TIPI)

    async def s4_5():
        n = nuovo_ordine("locked")
        o = f"m{n}"
        await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        await cs.chiama(invia, C, {"ordine": o, "tipo": "saluto", "busta": cs.busta("saluto-c")})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "saluto", "busta": cs.busta("saluto-v")})
        del DETTI[:]
        await asyncio.sleep(cs.ASSENTE)
        giornale = io.StringIO()
        segreto = "IL-MIO-INDIRIZZO-SEGRETO"
        with contextlib.redirect_stdout(giornale):
            m = await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta(segreto)})
            await asyncio.sleep(0.5)
            f = await ca.manda(V, o, os.urandom(40 * 1024))
        b = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        arrivate = b.get("buste") or []
        prova("I MESSAGGI: chi compra ritira i due saluti e il messaggio, com'e' partito",
              ([("saluto", True), ("saluto", False), ("msg", False)], cs.busta(segreto)),
              ([(x["tipo"], x["mia"]) for x in arrivate], arrivate[-1]["busta"] if arrivate else ""))
        prova("GLI ALLEGATI: il file entra, e l'altra parte lo riprende identico; un estraneo no",
              (True, True, 403),
              (bool(f.get("id")), isinstance(await ca.ritira(C, o, f.get("id", "")), bytes),
               cs.no(await ca.ritira(X, o, f.get("id", "")))))
        detti = avvisi_chat()
        # (20 ott 2026, chat-dalla-notifica) il tasto porta dritto alla chat: `&chat=1`
        prova("L'AVVISO: uno solo, a chi compra, col NUMERO DELL'ORDINE e il tasto che lo apre",
              [(C, True, (SRV.CHAT_MERCATINO_BOTTONE, f"{SRV.URL_PUBBLICO}/?ordine={n}&chat=1"))],
              [(chi, f"nell'ordine #{n}." in t, bt) for chi, t, bt in detti])
        prova("...e il testo del messaggio non c'e', ne' la busta", [False],
              [segreto in t or cs.busta(segreto) in t for _, t, _ in detti])
        prova("...il tasto, dentro Telegram, apre la Mini App sull'ordine", "mercatino_" + str(n),
              SRV._startapp_da_link(f"{SRV.URL_PUBBLICO}/?ordine={n}"))
        riga = giornale.getvalue()
        prova("NEL JOURNAL niente del messaggio: ne' il testo ne' la busta", (False, False),
              (segreto in riga, cs.busta(segreto) in riga))
        prova("...per l'allegato il solo peso", True, "40 KB" in riga)
        prova("la raffica e il tetto dei messaggi sono quelli della chat dello scambio", True,
              m.get("n", 0) > 0 and SRV.P2P_CHAT_MSG_MAX == 200 and SRV.P2P_CHAT_FILE_MAX == 20 * 1024 * 1024)

    async def s6():
        n = nuovo_ordine("shipped")
        o = f"m{n}"
        await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x51)})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x52)})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta("prima della disputa")})
        f = await ca.manda(C, o, os.urandom(2048))
        pacco = cs.busta("pacco-per-il-moderatore")
        prova("PRIMA DELLA DISPUTA la chiave al moderatore non parte: 409", 409,
              cs.no(await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": kmod, "busta": pacco})))
        prova("...e il moderatore non legge: 409, anche con la sua chiave", 409,
              cs.no(await cs.chiama(mod_chat, ADMIN, {"ordine": o})))
        prova("...e la riga dell'ordine non gli dice niente", "", chat_della_riga(ADMIN, n))
        metti(n, "dispute")
        prova("IN DISPUTA la chat resta aperta per le due parti", (True, True),
              ((await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})).get("aperta"),
               (await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})).get("aperta")))
        prova("...le chiavi pubbliche dei moderatori si chiedono", [kmod],
              (await cs.chiama(moderatori, V, {"ordine": o})).get("chiavi"))
        prova("...la chiave al moderatore parte, da TUTTE E DUE le parti", (True, True),
              ((await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": kmod, "busta": pacco})).get("ok"),
               (await cs.chiama(invia, V, {"ordine": o, "tipo": "mod", "per": kmod,
                                           "busta": cs.busta("pacco-di-chi-vende")})).get("ok")))
        prova("...mai verso una chiave che non e' di un moderatore: 400", 400,
              cs.no(await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": cs.chiave(0x77), "busta": pacco})))
        letta = await cs.chiama(mod_chat, ADMIN, {"ordine": o})
        prova("IL MODERATORE (admin con la sua chiave dichiarata) legge: le buste chiuse, i due pacchi, "
              "e le chiavi d'ordine di ogni parte",
              (1, "vende", ["compra", "vende"], {"compra": [cs.chiave(0x51)], "vende": [cs.chiave(0x52)]}),
              (len(letta.get("buste") or []), ((letta.get("buste") or [{}])[0]).get("lato"),
               [k["lato"] for k in letta.get("chiavi") or []], letta.get("lati")))
        prova("...la riga dell'ordine gli dice 'moderazione'", "moderazione", chat_della_riga(ADMIN, n))
        prova("...il file lo ritira dalla sua rotta", True,
              isinstance(await ca.ritira(ADMIN, o, f.get("id", ""), mod=True), bytes))
        prova("UN ADMIN SENZA la chiave da moderatore dichiarata: 409, e lo dice", (409, True),
              (cs.no(await cs.chiama(mod_chat, ADMIN2, {"ordine": o})),
               "chiave da moderatore" in str((await cs.chiama(mod_chat, ADMIN2, {"ordine": o}))[1])))
        prova("CHI NON E' MODERATORE: 403", 403, cs.no(await cs.chiama(mod_chat, C, {"ordine": o})))
        for stato in ("return_pending", "return_shipped"):
            metti(n, stato)
            prova(f"NEL RESO ('{stato}') la chat resta, e il moderatore legge ancora", (True, 1),
                  ((await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})).get("aperta"),
                   len((await cs.chiama(mod_chat, ADMIN, {"ordine": o})).get("buste") or [])))
        SRV._chat_p2p_spazza(mercatino=True)
        prova("...e la scopa del minuto non la tocca", True, righe_cassetto(o)[0] > 0)
        metti(n, "refunded")
        SRV._chat_mercatino_dopo_stato(n)
        prova("ALLA DECISIONE (rimborsato) via tutto: buste, segnalibri, file, chiavi d'ordine",
              (0, 0, 0, 0), righe_cassetto(o))
        prova("...e il moderatore non ha piu' niente da leggere: 409", 409,
              cs.no(await cs.chiama(mod_chat, ADMIN, {"ordine": o})))

    async def s7():
        for stato in ("confirmed", "released", "refund", "refunded"):
            n = nuovo_ordine("delivered")
            o = f"m{n}"
            await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x61)})
            await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta(f"ciao {stato}")})
            await ca.manda(C, o, os.urandom(4096))
            await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
            prima = righe_cassetto(o)
            metti(n, stato)
            if stato in ("confirmed", "refund"):
                # dal gesto che conclude (la conferma, la decisione): subito
                SRV._chat_mercatino_dopo_stato(n)
            else:
                # da una strada che non passa dalle rotte: la scopa del minuto
                SRV._chat_p2p_spazza(mercatino=True)
            prova(f"'{stato}': c'era tutto, e adesso nel cassetto non c'e' piu' niente",
                  (True, (0, 0, 0, 0)), (all(prima), righe_cassetto(o)))
            r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
            prova(f"...il ritiro dice FINITA (e il telefono butta chiave e messaggi), la riga 'chiusa'",
                  (False, True, "chiusa", "chiusa"),
                  (r.get("aperta"), r.get("finita"), chat_della_riga(C, n), chat_della_riga(V, n)))
        # i byte non restano nel file: secure_delete
        n = nuovo_ordine("locked")
        o = f"m{n}"
        segno = b"SEGNO-DA-CANCELLARE-" * 64
        r = await ca.manda(C, o, segno)
        dentro = segno in open(SRV.DB_CHAT, "rb").read()
        metti(n, "released")
        SRV._chat_mercatino_dopo_stato(n)
        prova("I BYTE SPARISCONO DAL FILE del cassetto, non solo dall'elenco", (True, True, False),
              (bool(r.get("id")), dentro, segno in open(SRV.DB_CHAT, "rb").read()))
        prova("'annullato' (mai pagato) non ha mai avuto chat, e la riga non dice niente", "",
              chat_della_riga(C, nuovo_ordine("annullato")))
        prova("I GESTI CHE CONCLUDONO chiamano la scopa: la conferma, la decisione, il reso ricevuto",
              5, open(os.path.join(banco.QUI, "server.py"), encoding="utf-8").read()
              .count("return await _poi_chat_mercatino(ordine_id, "))

    async def s8():
        n = nuovo_ordine("dispute")
        o = f"m{n}"
        await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta("disputa lunga")})
        cc = SRV.db_chat()
        cc.execute("UPDATE buste SET quando=? WHERE ordine=?", (adesso() - 40 * 86400, o))
        cc.execute("UPDATE allegati SET quando=? WHERE ordine=?", (adesso() - 40 * 86400, o))
        cc.commit()
        cc.close()
        SRV._chat_p2p_spazza()
        prova("LA RETE DEI 30 GIORNI non tocca un ordine del mercatino ancora in disputa", 1,
              righe_cassetto(o)[0])
        metti(n, "refunded")
        SRV._chat_p2p_spazza()
        prova("...la scopa piena lo porta via appena e' deciso (il giudice e' lo stesso)", (0, 0, 0, 0),
              righe_cassetto(o))

    async def s9():
        n = nuovo_ordine("locked")
        o = f"m{n}"
        await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta("per il pallino")})
        finito = nuovo_ordine("released")
        r = await cs.chiama(SRV.chat_novita_p2p, C, {"ordini": [o, f"m{finito}"]})
        prova("IL PALLINO, a P2P spento: l'ultimo messaggio dell'altra parte, e l'ordine concluso fra le finite",
              (True, [f"m{finito}"], False), ((r.get("ultimi") or {}).get(o, 0) > 0, r.get("finite"),
                                              r.get("spenta_mercatino")))
        prova("...senza ordini del mercatino, a P2P spento, resta il 409 di sempre", 409,
              cs.no(await cs.chiama(SRV.chat_novita_p2p, C, {"ordini": []})))

    async def s11():
        # LA RIAPERTURA VERA (19 ott 2026, cantiere chat-mercatino-2): un
        # ordine deciso il cui pagamento non va a segno resta riapribile, e
        # la chat resta — in sola lettura — finche' i sats non arrivano; il
        # moderatore la rilegge, la riapre con la rotta vera, e alla fine
        # se ne va.
        n = nuovo_ordine("dispute")
        o = f"m{n}"
        await cs.chiama(invia, C, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x71)})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x72)})
        await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta("il telaio e' crepato")})
        await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta("era integro")})
        f = await ca.manda(C, o, os.urandom(2048))
        await cs.chiama(invia, C, {"ordine": o, "tipo": "mod", "per": kmod,
                                   "busta": cs.busta("pacco-di-chi-compra")})
        prima = righe_cassetto(o)
        # LA DECISIONE il cui pagamento non va a segno: 'refund' con la disputa alle spalle
        con = banco.con_db()
        con.execute("UPDATE ordini SET stato='refund', disputata=1 WHERE id=?", (n,))
        con.commit()
        con.close()
        SRV._chat_mercatino_dopo_stato(n)
        SRV._chat_p2p_spazza(mercatino=True)
        prova("DECISO MA RIAPRIBILE ('refund' dopo la disputa): la chat NON si cancella, ne' dal gesto ne' "
              "dalla scopa del minuto", (prima, True), (righe_cassetto(o), prima[0] > 0 and prima[2] > 0))
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("...si legge (aperta e ferma), e la riga dell'ordine lo dice: 'ferma' alle parti, "
              "'moderazione' al moderatore",
              (True, True, 2, "ferma", "ferma", "moderazione"),
              (r.get("aperta"), r.get("ferma"), len(r.get("buste") or []), chat_della_riga(C, n),
               chat_della_riga(V, n), chat_della_riga(ADMIN, n)))
        rif = await cs.chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": cs.busta("ancora una cosa")})
        prova("...SOLA LETTURA: un messaggio nuovo e' un 409 con la frase del piede",
              (409, SRV.CHAT_MERCATINO_FERMA_TESTO), (cs.no(rif), rif[1] if isinstance(rif, cs.Rifiuto) else ""))
        prova("...e cosi' un file, un saluto, una chiave d'ordine nuova", (409, 409, 409),
              (cs.no(await ca.manda(V, o, os.urandom(64))),
               cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "saluto", "busta": cs.busta("s")})),
               cs.no(await cs.chiama(invia, V, {"ordine": o, "tipo": "chiave_ordine", "busta": cs.chiave(0x73)}))))
        letta = await cs.chiama(mod_chat, ADMIN, {"ordine": o})
        prova("...il moderatore la RILEGGE prima di ridecidere: i due messaggi, il pacco, il file",
              (2, ["compra"], True),
              (len(letta.get("buste") or []), [k["lato"] for k in letta.get("chiavi") or []],
               isinstance(await ca.ritira(ADMIN, o, f.get("id", ""), mod=True), bytes)))
        # LA RIAPERTURA VERA: la rotta del moderatore, «rimborso previa restituzione»
        try:
            esito = await SRV.risolvi_disputa(n, banco.Busta({"esito": "reso"}), **cs.ACCESSO[ADMIN])
        except SRV.HTTPException as e:
            esito = {"errore": (e.status_code, e.detail)}
        prova("IL MODERATORE RIAPRE (la rotta vera, «reso»): l'ordine va in 'return_pending'",
              "return_pending", esito.get("stato") if isinstance(esito, dict) else esito)
        r = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("...e la chat RITROVA TUTTO: le buste di prima, non piu' ferma, si riscrive",
              (True, False, 2, True, "aperta"),
              (r.get("aperta"), r.get("ferma"), len(r.get("buste") or []),
               bool((await cs.chiama(invia, V, {"ordine": o, "tipo": "msg",
                                                "busta": cs.busta("ok, aspetto il reso")})).get("ok")),
               chat_della_riga(V, n)))
        prova("...il moderatore legge ancora, coi pacchi consegnati in disputa", (3, ["compra"]),
              (len((await cs.chiama(mod_chat, ADMIN, {"ordine": o})).get("buste") or []),
               [k["lato"] for k in (await cs.chiama(mod_chat, ADMIN, {"ordine": o})).get("chiavi") or []]))
        # IL TIMER: 'confirmed' chiuso dalla macchina e' riapribile, quello di persona no
        nt = nuovo_ordine("locked")
        await cs.chiama(invia, C, {"ordine": f"m{nt}", "tipo": "msg", "busta": cs.busta("timer")})
        con = banco.con_db()
        con.execute("UPDATE ordini SET stato='confirmed', sbloccato_auto_il=? WHERE id=?", (adesso(), nt))
        con.commit()
        con.close()
        SRV._chat_mercatino_dopo_stato(nt)
        prova("CHIUSO DAL TIMER ('confirmed' con lo sblocco automatico): ferma, non si cancella",
              (1, "ferma"), (righe_cassetto(f"m{nt}")[0], chat_della_riga(C, nt)))
        # LA FINE VERA: i sats arrivano
        giornale = io.StringIO()
        metti(n, "refunded")
        with contextlib.redirect_stdout(giornale):
            SRV._chat_mercatino_dopo_stato(n)
        prova("I SATS ARRIVANO ('refunded'): via tutto, e la riga dice «chiusa»", ((0, 0, 0, 0), "chiusa"),
              (righe_cassetto(o), chat_della_riga(C, n)))
        prova("IL JOURNAL dice l'ordine col suo numero, non «scambio m…»",
              (True, False), (f"🧹 Chat degli ordini: l'ordine {n} e' concluso, buste cancellate" in giornale.getvalue(),
                              f"scambio m{n}" in giornale.getvalue()))
        prova("I RIFIUTI DICONO «ordine»: l'estraneo", "Non sei una delle due parti di questo ordine",
              (await cs.chiama(leggi, X, {"ordine": f"m{nt}", "dopo": 0}))[1])

    async def s12():
        # LA CHAT «ALTROVE» PER SBAGLIO (19 ott 2026, cantiere chat-mercatino-3,
        # richiesta di Andrea). Il cassetto del server rinasce (un ripristino,
        # un trasloco, il file perso): il telefono di chi NON ha un profilo di
        # scambio ha la sua chiave d'ordine solo nella memoria della chat — e
        # la memoria della chat, al «cassetto perso», si buttava intera, chiave
        # compresa. La chiave era gia' stata ridichiarata al server nuovo: al
        # giro dopo il server la diceva sua, il telefono non l'aveva piu', e la
        # chat diventava «aperta su un altro dispositivo». E se il server
        # rinasce e riceve piu' buste di quante il telefono ne aveva viste, il
        # «perso» non si accorge di niente: il telefono crede che il suo saluto
        # e la sua copia siano ancora la', e non li rimanda.
        import shutil
        import subprocess
        import tempfile
        import collaudo_tolti_ovunque as tolti
        node = shutil.which("node")
        if not node:
            prova("node c'e'", True, False)
            return
        scorta_pulita()
        n = nuovo_ordine("locked")
        o = f"m{n}"
        srv, base = tolti.avvia_ponte()
        cart = tempfile.mkdtemp(prefix="chat_rinasce_")
        mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
        prog = os.path.join(cart, "telefono.js")
        open(prog, "w", encoding="utf-8").write(dispositivo(mini))
        chi = {"C": (C, "Compratore"), "V": (V, "Venditore")}

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

        def rinasce():
            # il file del cassetto se ne va, e il prossimo `db_chat` lo rifa' vuoto
            for suff in ("", "-wal", "-shm", "-journal"):
                if os.path.exists(SRV.DB_CHAT + suff):
                    os.remove(SRV.DB_CHAT + suff)
            SRV._CHAT_PRONTA["file"] = ""
        try:
            telefono("C", f"profilo|{o}")
            telefono("V", f"ordine|{n}|seller|locked|aperta")
            telefono("C", f"ordine|{n}|buyer|locked|aperta", "battito")
            telefono("V", "battito", "scrivi|Prima della rinascita")
            f = telefono("C", "battito")
            prova("PRIMA: chi vende (senza profilo, chiave a caso) e chi compra (col profilo) si scrivono",
                  ("scrivi", ["altro: Prima della rinascita"]), (f.get("modo"), f.get("msgs")))
            # 1) IL CASSETTO RINASCE VUOTO: il telefono ha visto piu' buste di quante il server ne ha
            rinasce()
            f = telefono("V", "battito", "battito")
            prova("IL CASSETTO RINASCE VUOTO: chi vende NON resta «altrove», tiene la sua chiave d'ordine "
                  "e la ridichiara", ("non altrove", True, 1),
                  ("altrove" if f.get("modo") == "altrove" else "non altrove", f.get("caso"), f.get("mie")))
            f = telefono("C", "battito", "battito")
            telefono("V", "battito")
            telefono("V", "scrivi|Dopo la rinascita")
            f = telefono("C", "battito")
            prova("...e la chat riparte: chi compra legge il messaggio nuovo", True,
                  "altro: Dopo la rinascita" in (f.get("msgs") or []))
            # 2) IL CASSETTO RINASCE E SI RIEMPIE PRIMA CHE IL TELEFONO TORNI: il
            # segnalibro del telefono e' sotto il numero piu' alto del server
            # nuovo, e il «perso» non lo vede
            telefono("V", "battito")
            rinasce()
            cc = SRV.db_chat()
            # il file nuovo ha gia' una busta di quest'ordine, col numero 901:
            # piu' alto di ogni segnalibro dei due telefoni, quindi `perso` tace
            cc.execute("INSERT INTO buste(n, ordine, giro, da, tipo, per, busta, quando) "
                       "VALUES(901, ?, 0, ?, 'msg', '', ?, ?)", (o, C, cs.busta("da un cassetto rinato"), adesso()))
            cc.commit()
            cc.close()
            telefono("C", "battito", "battito")
            f = telefono("V", "battito", "battito")
            prova("IL CASSETTO RINASCE E SI RIEMPIE PRIMA (numeri piu' alti del segnalibro): chi vende se ne "
                  "accorge lo stesso e si ripresenta (copia e saluto sul server nuovo)", (True, True),
                  ("saluto" in [r[0] for r in cs.cassetto("SELECT tipo FROM buste WHERE ordine=? AND da=?", o, V)],
                   "chiave" in [r[0] for r in cs.cassetto("SELECT tipo FROM buste WHERE ordine=? AND da=?", o, V)]))
            telefono("C", "battito")
            telefono("V", "battito", "scrivi|Dopo la seconda rinascita")
            f = telefono("C", "battito")
            prova("...e chi compra legge il messaggio nuovo", True,
                  "altro: Dopo la seconda rinascita" in (f.get("msgs") or []))
            # LE RIGHE DEL CASSETTO E DELLA SCOPA (19 ott 2026, chat-mercatino-3)
            metti(n, "released")
            giornale = io.StringIO()
            with contextlib.redirect_stdout(giornale):
                await SRV._giro_chat_p2p()
                rinasce()
                SRV.db_chat().close()
            riga = giornale.getvalue()
            prova("LA SCOPA DELL'OROLOGIO P2P, su una chat d'ordine: «Chat degli ordini … 1 ordine concluso», "
                  "mai «scambio finito»", (True, False),
                  ("🧹 Chat degli ordini: cancellate le buste di 1 ordine concluso" in riga, "scambio finito" in riga))
            prova("IL CASSETTO che rinasce si dice per tutti e due: «Chat (scambi e ordini)», non «Chat P2P»",
                  (True, False), ("🧹 Chat (scambi e ordini): il cassetto restituisce" in riga,
                                  "Chat P2P: il cassetto" in riga))
        finally:
            srv.shutdown()
            qui = asyncio.get_running_loop()
            for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
                for c in list(gruppo):
                    if c.get_loop() is not qui:
                        gruppo.discard(c)

    async def s13():
        # DRITTI ALLA CHAT, E SI SCRIVE SUBITO (20 ott 2026, cantiere
        # chat-dalla-notifica, richiesta di Andrea): prima si poteva scrivere
        # solo quando ANCHE l'altra parte aveva aperto la pagina dell'ordine.
        # Adesso ogni telefono lascia al server una SCORTA di lucchetti
        # usa-e-getta, e a ogni ordine nuovo il server ne brucia uno come
        # chiave d'ordine di chi non si e' ancora presentato. Due utenti: il
        # secondo NON HA MAI APERTO LA PAGINA. E il moderatore di una disputa
        # legge quell'ordine e nessun altro della stessa persona.
        import shutil
        import subprocess
        import tempfile
        import collaudo_tolti_ovunque as tolti
        node = shutil.which("node")
        if not node:
            prova("node c'e'", True, False)
            return
        SRV.MERCATINO_CHAT_ORDINI = True
        scorta_pulita()
        n1, n2, n3 = nuovo_ordine("locked"), nuovo_ordine("locked"), nuovo_ordine("locked", venditore=X)
        o1, o2, o3 = f"m{n1}", f"m{n2}", f"m{n3}"
        srv, base = tolti.avvia_ponte()
        cart = tempfile.mkdtemp(prefix="chat_dalla_notifica_")
        mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
        prog = os.path.join(cart, "telefono.js")
        open(prog, "w", encoding="utf-8").write(dispositivo(mini))
        chi = {"C": (C, "Compratore"), "V": (V, "Venditore"), "A": (ADMIN, "Admin")}

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

        def conta(sql, *a):
            return len(cs.cassetto(sql, *a))

        async def avvisi_a(chi_riceve, inizio, numero):
            # l'avviso parte in un compito del server: si aspetta che arrivi, e
            # si guardano solo quelli di QUESTO ordine (un compito di una
            # sezione di prima puo' arrivare adesso)
            suo = lambda d: d[0] == chi_riceve and f"nell'ordine #{numero}." in d[1]
            for _ in range(80):
                v = [d for d in DETTI[inizio:] if suo(d)]
                if v:
                    return v
                await asyncio.sleep(0.05)
            return [d for d in DETTI[inizio:] if suo(d)]
        try:
            # 1) chi vende apre Barattolo (non l'ordine): la scorta si riempie
            f = telefono("V", f"profilo|{o1}", "scorta")
            prova("CHI VENDE apre Barattolo, non l'ordine: venti lucchetti in scorta, ognuno col suo seme "
                  "(e' nato dal profilo), nessuno ancora bruciato", (20, 20, 0, ""),
                  (conta("SELECT 1 FROM scorta WHERE tg_id=? AND ordine=''", V),
                   conta("SELECT 1 FROM scorta WHERE tg_id=? AND length(seme)=32", V),
                   conta("SELECT 1 FROM chiavi_ordine WHERE tg_id=?", V), f.get("ESPLOSO", "") or f.get("ERRORE", "")))
            # 2) chi compra apre per primo, e scrive SUBITO
            f = telefono("C", f"profilo|{o1}", f"ordine|{n1}|buyer|locked|aperta", "battito")
            prova("CHI COMPRA apre l'ordine pagato e SCRIVE SUBITO, anche se chi vende non ha MAI aperto "
                  "la pagina: la sua chiave d'ordine e' il lucchetto che il server ha bruciato",
                  ("scrivi", 1, 1, 19),
                  (f.get("modo"), f.get("peers"), conta("SELECT 1 FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o1, V),
                   conta("SELECT 1 FROM scorta WHERE tg_id=? AND ordine=''", V)))
            inizio = len(DETTI)
            telefono("C", "battito", "scrivi|Ciao, prima che tu apra l'ordine")
            av = await avvisi_a(V, inizio, n1)
            prova("...l'avviso arriva a chi vende, col tasto che porta DRITTO alla chat",
                  [("💬 Apri l'ordine", f"{SRV.URL_PUBBLICO}/?ordine={n1}&chat=1")], [d[2] for d in av])
            # 3) chi vende apre per la prima volta, e legge
            f = telefono("V", f"ordine|{n1}|seller|locked|aperta")
            prova("CHI VENDE apre l'ordine per la PRIMA volta e legge quel che gli hanno scritto prima, e scrive",
                  ("scrivi", ["altro: Ciao, prima che tu apra l'ordine"], 0, 1),
                  (f.get("modo"), f.get("msgs"), f.get("muti"),
                   conta("SELECT 1 FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o1, V)))
            telefono("V", "scrivi|Eccomi, la spedisco oggi")
            f = telefono("C", "battito")
            prova("...e chi compra legge la risposta", ["io: Ciao, prima che tu apra l'ordine", "altro: Eccomi, la spedisco oggi"],
                  f.get("msgs"))
            # 4) un secondo ordine della stessa persona: un altro lucchetto
            telefono("C", f"ordine|{n2}|buyer|locked|aperta", "battito", "scrivi|Secondo ordine: spedisci insieme?")
            p1 = [r[0] for r in cs.cassetto("SELECT pub FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o1, V)]
            p2 = [r[0] for r in cs.cassetto("SELECT pub FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o2, V)]
            prova("UN SECONDO ORDINE DELLA STESSA PERSONA: un lucchetto DIVERSO, bruciato anche lui", (1, 1, True, 18),
                  (len(p1), len(p2), p1 != p2, conta("SELECT 1 FROM scorta WHERE tg_id=? AND ordine=''", V)))
            f = telefono("V", f"ordine|{n2}|seller|locked|aperta")
            prova("...e chi vende lo legge", ["altro: Secondo ordine: spedisci insieme?"], f.get("msgs"))
            # 5) la disputa sul primo: il moderatore legge quello, e solo quello
            fm = telefono("A", "nuovomod")
            con = banco.con_db()
            con.execute("UPDATE p2p_moderatori SET chiave=? WHERE tg_id=?", (fm.get("pub") or "", ADMIN))
            con.commit()
            con.close()
            metti(n1, "dispute")
            metti(n2, "dispute")
            telefono("C", f"ordine|{n1}|buyer|dispute|aperta", "moderatori")
            telefono("V", f"ordine|{n1}|seller|dispute|aperta", "moderatori")
            f = telefono("A", f"leggimod|{o1}|{o2}")
            prova("IN DISPUTA il moderatore legge la chat di quell'ordine, compreso il messaggio scritto prima "
                  "che chi vende aprisse", (["compra: Ciao, prima che tu apra l'ordine", "vende: Eccomi, la spedisco oggi"], 0),
                  (f.get("letti"), f.get("mute")))
            prova("LA PROVA DI ANDREA, sul server vero: le chiavi che il moderatore ha avuto per un ordine non "
                  "aprono NESSUNA busta dell'altro ordine della stessa persona",
                  (True, 1, 0, 0, 1), (f.get("segreti", 0) > 0, f.get("buste2"), f.get("aperteAltro"),
                                       f.get("altroLetti"), f.get("altroMute")))
            # 6) chi non ha mai aperto Barattolo: niente lucchetti, «vuole scriverti»
            f = telefono("C", f"ordine|{n3}|buyer|locked|aperta", "battito")
            prova("CHI VENDE NON HA MAI APERTO BARATTOLO (nessun lucchetto): al posto del campo «🔔 Avvisa»",
                  ("chiama", 0), (f.get("modo"), f.get("peers")))
            inizio = len(DETTI)
            r1 = await cs.chiama(SRV.chat_chiama_p2p, C, {"ordine": o3})
            r2 = await cs.chiama(SRV.chat_chiama_p2p, C, {"ordine": o3})
            av = [d for d in DETTI[inizio:] if d[0] == X]
            prova("...il tocco manda UN avviso «vuole scriverti», col tasto dritto alla chat; il secondo no",
                  (True, True, ["💬 <b>Chi compra vuole scriverti nell'ordine #%d.</b>" % n3],
                   [("💬 Apri la chat", f"{SRV.URL_PUBBLICO}/?ordine={n3}&chat=1")]),
                  (r1.get("avvisato"), r2.get("gia"), [d[1].split("\n")[0] for d in av], [d[2] for d in av]))
            f = telefono("C", "battito")
            prova("...e il piede dice che e' avvisato", "chiamato", f.get("modo"))
            r3 = await cs.chiama(SRV.chat_chiama_p2p, C, {"ordine": o1})
            r4 = await cs.chiama(SRV.chat_chiama_p2p, X, {"ordine": o1})
            prova("...chi ha gia' una chiave non si chiama (si scrive e basta); un estraneo non chiama nessuno",
                  (False, 403), (r3.get("serve"), r4[0] if isinstance(r4, tuple) else r4))
            # 7) la scopa: a ordine concluso via i lucchetti bruciati e le chiamate
            for n in (n1, n2, n3):
                metti(n, "released")
                SRV._chat_mercatino_dopo_stato(n)
            prova("A ORDINE CONCLUSO i lucchetti bruciati e le chiamate se ne vanno; la scorta resta",
                  (0, 0, 18), (conta("SELECT 1 FROM scorta WHERE ordine IN (?,?,?)", o1, o2, o3),
                               conta("SELECT 1 FROM chiamate WHERE ordine=?", o3),
                               conta("SELECT 1 FROM scorta WHERE tg_id=? AND ordine=''", V)))
        finally:
            srv.shutdown()
            qui = asyncio.get_running_loop()
            for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
                for c in list(gruppo):
                    if c.get_loop() is not qui:
                        gruppo.discard(c)

    async def s10():
        import shutil
        import subprocess
        import tempfile
        import collaudo_tolti_ovunque as tolti
        node = shutil.which("node")
        if not node:
            prova("node c'e'", True, False)
            return
        scorta_pulita()
        n = nuovo_ordine("locked")
        o = f"m{n}"
        srv, base = tolti.avvia_ponte()
        cart = tempfile.mkdtemp(prefix="chat_mercatino_")
        mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
        prog = os.path.join(cart, "telefono.js")
        open(prog, "w", encoding="utf-8").write(dispositivo(mini))
        chi = {"C": (C, "Compratore"), "C2": (C, "Compratore"), "V": (V, "Venditore"), "V2": (V, "Venditore")}

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
            f = telefono("C", f"ordine|{n}|buyer|locked|aperta")
            prova("CHI COMPRA (col profilo di scambio) apre l'ordine pagato: il riquadro c'e', con l'avviso "
                  "dell'ordine; la chiave d'ordine e' quella del PROFILO, dichiarata da sola",
                  (True, True, True, False, [k], ""),
                  (f.get("riquadro"), f.get("richiamo"), f.get("avviso"), f.get("caso"),
                   cs.cassetto("SELECT pub FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, C) and
                   [r[0] for r in cs.cassetto("SELECT pub FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, C)],
                   f.get("ESPLOSO", "") or f.get("ERRORE", "")))
            # (20 ott 2026, chat-dalla-notifica) chi vende non ha ne' una chiave ne' una
            # scorta di lucchetti (non ha mai aperto Barattolo): al posto del campo «🔔 Avvisa»
            prova("...l'altra parte non c'e' ancora e non ha nessuna chiave: «🔔 Avvisa», e il saluto non "
                  "parte senza la sua chiave", ("chiama", []), (f.get("modo"), tipi(C)))
            f = telefono("V", f"ordine|{n}|seller|locked|aperta")
            # (20 ott 2026, chat-dalla-notifica) e scrive SUBITO, per la chiave d'ordine
            # di chi compra: non aspetta piu' il suo saluto
            prova("CHI VENDE, SENZA profilo: la chiave d'ordine nasce A CASO sul telefono, si presenta, e "
                  "scrive subito, senza aspettare il saluto di chi compra",
                  (True, True, True, "scrivi", ["chiave", "saluto"]),
                  (f.get("riquadro"), f.get("caso"), f.get("laSua") is not None, f.get("modo"), tipi(V)))
            f = telefono("C", "battito")
            prova("...chi compra al suo battito presenta la sua chiave e si scrive",
                  ("scrivi", ["chiave", "saluto"]), (f.get("modo"), tipi(C)))
            telefono("C", "scrivi|Ciao, quando spedisci?")
            f = telefono("V", "battito", "scrivi|Domani mattina")
            prova("I MESSAGGI viaggiano cifrati nei due sensi", ["altro: Ciao, quando spedisci?", "io: Domani mattina"],
                  f.get("msgs"))
            prova("...sul server, buste che non dicono niente", False,
                  any("spedisci" in r[0] for r in cs.cassetto("SELECT busta FROM buste WHERE ordine=?", o)))
            f = telefono("C", "battito")
            prova("...e chi compra le legge", ["io: Ciao, quando spedisci?", "altro: Domani mattina"], f.get("msgs"))
            prova("PRIMA DELLA DISPUTA nessun telefono chiede le chiavi dei moderatori (ne' da' la sua)",
                  (False, []), (any("chat/moderatori" in x for x in f.get("chiamate") or []),
                                tipi(C) and [t for t in tipi(C) + tipi(V) if t == "mod"]))
            # IL SECONDO DISPOSITIVO di chi vende: senza profilo, senza la chiave a caso del primo
            f = telefono("V2", f"ordine|{n}|seller|locked|aperta")
            prova("UN ALTRO DISPOSITIVO di chi vende (senza profilo): la chat e' aperta altrove, non dichiara "
                  "niente da solo", ("altrove", False, 1), (f.get("modo"), f.get("caso"),
                                                          len(cs.cassetto("SELECT 1 FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, V))))
            f = telefono("V2", "continua")
            # (20 ott 2026, chat-dalla-notifica) ...e si scrive subito, per la chiave
            # d'ordine di chi compra
            prova("...«Continua la chat qui»: una chiave d'ordine nuova, presentata, e si scrive subito, "
                  "senza aspettare che chi compra risaluti", ("scrivi", True, 2),
                  (f.get("modo"), f.get("caso"),
                   len(cs.cassetto("SELECT 1 FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, V))))
            f = telefono("C", "battito")
            prova("...chi compra, al suo battito, rifa' il saluto per la chiave nuova (e vede la riga «ha ripreso»)",
                  (["chiave", "saluto", "msg", "saluto"], 1), (tipi(C), f.get("sis")))
            f = telefono("V2", "battito")
            prova("...e dall'altro dispositivo si scrive; i messaggi di prima qui non si leggono",
                  ("scrivi", [], True), (f.get("modo"), [m for m in f.get("msgs") or [] if "spedisci" in m],
                                         f.get("muti", 0) > 0))
            telefono("V2", "scrivi|Scrivo dall'altro telefono")
            f = telefono("C", "battito")
            prova("...chi compra legge tutto: i messaggi di prima e quello nuovo, e la riga «ha ripreso»",
                  (["io: Ciao, quando spedisci?", "altro: Domani mattina", "altro: Scrivo dall'altro telefono"], 1),
                  (f.get("msgs"), f.get("sis")))
            # UN ALTRO DISPOSITIVO di chi compra, COL SUO PROFILO (il tasto dell'avviso apre la Mini App:
            # un'altra memoria): la chiave d'ordine e' la stessa, la usa-e-getta torna dalla copia
            # sigillata, e si rilegge TUTTO da capo — anche i saluti di chi vende chiusi per la sua
            # chiave d'ordine di PRIMA
            sk_c = json.loads(json.load(open(os.path.join(cart, "C.json"), encoding="utf-8"))["MAZZO"])["sk"]
            telefono("C2", f"stessoprofilo|{sk_c}")
            f = telefono("C2", f"ordine|{n}|buyer|locked|aperta", "battito")
            prova("UN ALTRO DISPOSITIVO DI CHI COMPRA, col suo profilo: nessuna chiave nuova, la chat si ritrova "
                  "INTERA (anche i messaggi chiusi per la chiave di prima di chi vende), e si scrive",
                  (["io: Ciao, quando spedisci?", "altro: Domani mattina", "altro: Scrivo dall'altro telefono"],
                   "scrivi", 1),
                  (f.get("msgs"), f.get("modo"),
                   len(cs.cassetto("SELECT 1 FROM chiavi_ordine WHERE ordine=? AND tg_id=?", o, C))))
            # LA DISPUTA: i due telefoni danno la chiave al moderatore
            metti(n, "dispute")
            fc = telefono("C", f"ordine|{n}|buyer|dispute|aperta", "moderatori")
            fv = telefono("V2", f"ordine|{n}|seller|dispute|aperta", "moderatori")
            prova("IN DISPUTA i telefoni di TUTTE E DUE le parti danno la chiave al moderatore",
                  (1, 1, ["compra", "vende"]),
                  (fc.get("modDato"), fv.get("modDato"),
                   sorted({k["lato"] for k in (await cs.chiama(mod_chat, ADMIN, {"ordine": o})).get("chiavi") or []})))
            # LA FINE
            metti(n, "released")
            SRV._chat_mercatino_dopo_stato(n)
            f = telefono("C", f"ordine|{n}|buyer|released|chiusa")
            prova("ORDINE CONCLUSO: la pagina mostra «chat chiusa», senza riquadro", (True, False),
                  (f.get("chiusa"), f.get("richiamo")))
            f = telefono("V2", f"ordine|{n}|seller|locked|aperta")
            prova("...un telefono che la credeva ancora aperta chiede, il server dice finita: chiave e "
                  "messaggi buttati, e la riga «chat chiusa»", (False, True, True),
                  (f.get("cassetto"), f.get("chiusa"),
                   any("ordine concluso per il server" in r for r in f.get("diario") or [])))
            prova("...e nel cassetto del server non resta niente", (0, 0, 0, 0), righe_cassetto(o))
        finally:
            srv.shutdown()
            qui = asyncio.get_running_loop()
            for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
                for c in list(gruppo):
                    if c.get_loop() is not qui:
                        gruppo.discard(c)

    async def s14():
        # LE SPUNTE (26 nov 2026, cantiere chat-spunte): le cifre che il
        # ritiro porta, sulla rotta vera — per tutte e tre le chat e' la
        # stessa rotta, quindi qui basta il mercatino
        SRV.CHAT_SPUNTE = True
        n = nuovo_ordine("locked")
        o = f"m{n}"
        await cs.chiama(invia, C, {"ordine": o, "tipo": "saluto", "busta": cs.busta("sp-saluto-c")})
        n1 = (await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta("sp-uno")})).get("n", 0)
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("✓: chi compra ha scritto, chi vende non ha ritirato — arrivato e visto a zero",
              {"arrivato": 0, "visto": 0}, a.get("spunte"))
        await cs.chiama(leggi, V, {"ordine": o, "dopo": 0})
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": n1})
        prova("✓✓: il telefono di chi vende ha ritirato — arrivato fino al messaggio, visto no",
              (True, 0), ((a.get("spunte") or {}).get("arrivato", 0) >= n1, (a.get("spunte") or {}).get("visto")))
        await cs.chiama(leggi, V, {"ordine": o, "dopo": n1, "visto": n1})
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": n1})
        prova("✓✓ arancioni: chi vende ha visto, e chi compra lo legge", n1, (a.get("spunte") or {}).get("visto"))
        await cs.chiama(leggi, V, {"ordine": o, "dopo": n1, "visto": n1 + 999})
        a = await cs.chiama(leggi, C, {"ordine": o, "dopo": n1})
        prova("...un «visto» oltre quel che ha ritirato non passa", True,
              (a.get("spunte") or {}).get("visto", 0) <= (a.get("spunte") or {}).get("arrivato", 0))
        prova("...un estraneo non le chiede: 403", 403,
              cs.no(await cs.chiama(leggi, X, {"ordine": o, "dopo": 0, "visto": 5})))
        SRV.CHAT_SPUNTE = False
        try:
            n2 = (await cs.chiama(invia, C, {"ordine": o, "tipo": "msg", "busta": cs.busta("sp-due")})).get("n", 0)
            await cs.chiama(leggi, V, {"ordine": o, "dopo": 0, "visto": n2})
            a = await cs.chiama(leggi, C, {"ordine": o, "dopo": n2})
            prova("LEVA SPENTA: il ritiro non porta le cifre, e il visto non si scrive", (False, n1),
                  ("spunte" in a, cs.cassetto("SELECT visto_fino FROM letture WHERE ordine=? AND tg_id=?",
                                              o, V)[0][0]))
        finally:
            SRV.CHAT_SPUNTE = True

    await sezione(1, "LA LEVA SPENTA", s1)
    await sezione(2, "L'ACCENSIONE AL PAGAMENTO", s2)
    await sezione(3, "LE CHIAVI D'ORDINE", s3)
    await sezione("4-5", "MESSAGGI, ALLEGATI, AVVISI E JOURNAL", s4_5)
    await sezione(6, "LA DISPUTA E IL MODERATORE", s6)
    await sezione(7, "LA CANCELLAZIONE A ORDINE CONCLUSO", s7)
    await sezione(8, "LA RETE DEI 30 GIORNI", s8)
    await sezione(9, "IL PALLINO", s9)
    await sezione(10, "IL CLIENT VERO CONTRO IL SERVER VERO", s10)
    await sezione(11, "LA RIAPERTURA VERA: LA CHAT FERMA, RILETTA E RITROVATA", s11)
    await sezione(12, "IL CASSETTO DEL SERVER RINASCE: NESSUNA CHAT «ALTROVE» PER SBAGLIO", s12)
    await sezione(13, "DRITTI ALLA CHAT, E SI SCRIVE SUBITO: IL SECONDO NON HA MAI APERTO LA PAGINA", s13)
    await sezione(14, "LE SPUNTE: ARRIVATO E VISTO, SULLA ROTTA VERA", s14)
    for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
        if gruppo:
            await asyncio.gather(*list(gruppo), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
