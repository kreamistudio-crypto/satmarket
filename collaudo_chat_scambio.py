# -*- coding: utf-8 -*-
"""
LA CHAT NELLO SCAMBIO, SUL SERVER VERO (12 ott 2026).

La decisione di Andrea con Alan: dentro ogni scambio P2P preso le due
parti si scrivono, con chiavi usa-e-getta; i messaggi passano dal server
GIA' CHIUSI dal telefono; il server fa il postino (tiene la busta, la
consegna, non la apre) e a scambio finito la CANCELLA; il moderatore la
legge solo se una delle due parti apre una disputa.

`prove.py` difende i giudici estratti e fa girare la crittografia vera
in node (`prove_chat_scambio`). Qui girano le ROTTE VERE —
`/api/p2p/chat/leggi`, `/invia`, `/moderatori`,
`/api/p2p/moderazione/chat` e, per lo scambio, `/api/p2p/evento` — su
database usa-e-getta, con l'autenticazione VERA (niente `come()`):

   1. le quattro coppie di accesso delle due parti — Telegram/Telegram,
      Telegram/Nostr, Nostr/Telegram, Nostr/Nostr: i saluti, un
      messaggio per parte, l'avviso senza testo a chi deve leggere;
   2. prima della presa e per un estraneo la chat non c'e';
   3. la consegna a chi e' offline, e il segnalibro;
   4. un avviso per ogni «c'e' da leggere», non uno per messaggio; chi
      sta guardando non viene disturbato, chi ha appena chiuso si';
   5. i tetti: busta troppo lunga, forma storta, raffica, tetto di
      messaggi, la stessa busta rimandata;
   6. la parte che scambia da UN'ALTRA APP (una chiave che non e' di
      nessun account di qui): la chat non si apre, e niente si scrive;
   7. la disputa: la busta per il moderatore solo verso una chiave vera,
      e il moderatore legge solo dopo aver preso la disputa;
   8. la fine: le buste spariscono dal file, non solo dall'elenco;
   9. l'ordine tornato nel libro e ripreso da un altro: riparte da zero;
  10. la scopa del minuto, per lo scambio finito senza che l'evento
      passasse di qui;
  11. niente nel database di tutti (quello dei backup), niente testo
      nel journal, e gli accessi riusciti fuori dal registro;
  12. il pallino dei messaggi non letti: la domanda che non sposta
      nessun segnalibro e non ferma l'avviso fuori dall'app;
  13. la leva `P2P_CHAT_SCAMBIO` spenta: niente buste nuove, quelle che
      ci sono restano e se ne vanno a scambio finito; riaccesa, riprende.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore. Le buste qui sono testo a caso: il server non le apre, e
la crittografia vera gira nel banco node di `prove.py`.

USO:  python collaudo_chat_scambio.py
"""

import asyncio
import contextlib
import io
import json
import logging
import os
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
TG_V, TG_C, ESTRANEO, ADMIN = 222, 111, 333, 999
N1, N2, N3, N4 = -7001, -7002, -7003, -7004
ACCESSO = {}
DETTI = []          # (destinatario, testo, bottone) di ogni notifica
# LE ATTESE SI SCRIVONO RISPETTO ALLA SOGLIA, e la soglia e' larga: il
# server conta i secondi INTERI, e con una soglia di un secondo un
# ritiro alle 10,99 e un invio alle 11,01 distano «un secondo» — il
# collaudo passava o falliva secondo dove cadeva il secondo.
PRESENTE = 3                 # chi ha ritirato da meno di cosi' sta guardando
ASSENTE = PRESENTE + 0.4     # dopo quest'attesa NON sta piu' guardando
RIPASSO = PRESENTE + 1 + 0.9 # il secondo sguardo del server e' gia' passato


def adesso():
    return int(time.time())


def ordine(n):
    return f"c4a70000-c2c2-4a2b-9c3d-{n:012d}"


def chiave(n):
    # mai 64 esadecimali scritti per esteso: si compongono
    return f"{n:02x}" * 32


def sullo_scambio(f):
    """(20 ott 2026, chat-dalla-notifica) Le domande che la pagina fa SULLO
    SCAMBIO. Il battito chiede anche della scorta di lucchetti della chat
    degli ordini (`p2p/chat/scorta`, una volta ogni dieci minuti, su ogni
    pagina): non riguarda lo scambio, e qui non si conta."""
    return [x for x in (f.get("chiamate") or []) if x != "p2p/chat/scorta"]


def busta(testo):
    """Una busta finta: base64 di qualcosa, che il server non apre."""
    import base64
    return base64.b64encode((testo + " " * 40).encode()).decode()


class Rifiuto(tuple):
    """Il no di una rotta, come coppia (codice, messaggio). Ha anche il
    `get` di un dizionario — che non trova mai niente — cosi' un
    controllo che aspettava una risposta da' una rossa col suo nome
    invece di far esplodere il giro."""

    def get(self, chiave, ripiego=None):
        return ripiego


def no(r):
    """Il codice di un rifiuto — o la parola «accettata» quando la rotta
    ha detto di si': una rotta che doveva rifiutare e non lo fa diventa
    una rossa col suo nome, non un errore che si porta via la sezione."""
    return r[0] if isinstance(r, Rifiuto) else "accettata"


async def chiama(fn, chi, corpo):
    """La rotta vera con l'autenticazione vera; un rifiuto torna come
    `Rifiuto` (codice, messaggio)."""
    try:
        r = await fn(banco.Busta(corpo), **ACCESSO[chi])
    except banco.SRV.HTTPException as e:
        return Rifiuto((e.status_code, str(e.detail)))
    return json.loads(r.body)


async def evento(o, azione, attore, dettaglio="", compra="", vende=""):
    b = banco.Busta({"v": 1, "order": o, "action": azione, "ts": adesso(),
                     "buyer": compra, "seller": vende,
                     "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.3)


def pubblica(o, venditore):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,15000,"
                "'10,00 €','[\"SEPA\"]')", (o, venditore, adesso()))
    con.commit()
    con.close()


def registra_chiave(k, tg):
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                "VALUES(?,?,?)", (k, tg, adesso()))
    con.commit()
    con.close()


def cassetto(sql, *a):
    cc = banco.SRV.db_chat()
    try:
        return cc.execute(sql, a).fetchall()
    finally:
        cc.close()


def avvisi_chat():
    return [(chi, t, b) for chi, t, b in DETTI
            if t.startswith("💬 <b>Hai un nuovo messaggio")]


async def scambio(n, venditore, compratore, kv, kc):
    """Una vendita pubblicata e presa: da qui la chat e' aperta."""
    o = ordine(n)
    pubblica(o, venditore)
    registra_chiave(kv, venditore)
    if compratore:
        registra_chiave(kc, compratore)
    await evento(o, "taken", "buyer", "invoice-next", kc, kv)
    return o


def dispositivo_chat(mini):
    """IL TELEFONO, per la sezione 16: le funzioni VERE di miniapp.html —
    tutto il blocco della chat, la domanda all'archivio del server e la
    sua adozione, la chiave dello scambio — in node, col bundle vero, un
    localStorage che vive in un file (uno per telefono) e la `fetch` vera
    verso il ponte. Di cartone ci sono solo la pagina (uno schermo alto
    800 con la lista della chat IN FONDO, fuori vista finche' non si
    «scorre») e il ridisegno, che fa nascere i due pezzi della chat come
    `renderOrdineP2P`: il richiamo e il riquadro."""
    def js(firma, fine="\n}\n"):
        i = mini.index(firma)
        return mini[i:mini.index(fine, i) + len(fine)]

    def cost(nome, fine=";\n"):
        i = mini.index("const " + nome + " = ")
        return mini[i:mini.index(fine, i) + len(fine)]

    blocco = mini[mini.rindex("/* ═══ LA CHAT NELLO SCAMBIO (12 ott 2026"):
                  mini.index("/* ═══ fine: la chat nello scambio ═══ */")]
    pezzi = "\n".join(
        [cost(n) for n in ("MAZZO_INFO", "P2P_FINALI", "P2P_ORIZZONTE_S", "P2P_LAPIDE_TOLTO_S",
                           "P2P_LIBRO_FINESTRA_S", "MOSTRO_LAPIDI_CHIAVE", "P2P_FORMA_ORDINE",
                           "P2P_DA_RESTORE", "P2P_RESTORE_FERMI", "P2P_RIPRESA_PASSO",
                           "P2P_INDICE_CERCA_MAX", "P2P_INDICE_CERCA_MIN", "P2P_GIRO_APERTO")]
        + [cost("STATI_P2P", "\n};\n"), cost("P2P_PROGRESSO", "\n};\n")]
        + [js(f) for f in ("function idMostroVero(id){", "function chiaveScambio(",
                           "function ordiniP2P(){", "function scriviOrdineP2P(o){",
                           "function lapidiP2P(){", "function lapidataP2P(id, giro){",
                           "function toltoAltroveP2P(id){",
                           "async function chiediScambiServerP2P(){",
                           # l'ora del server dalla risposta (16 ott 2026, orari-passi)
                           "function prendiOraServerP2P(s){",
                           "function statoDaRestoreP2P(o, statoMostro){",
                           "function fermoDaMomentiP2P(momenti){", "function indiceDaChiaveP2P(mz, pub, max){",
                           "function presenzeDaServerP2P(p, giro){", "function uniscePresenzeP2P(a, b){",
                           "function rigaDaServerP2P(id, s, tk, stato, adesso){",
                           "function chiaveScambioDaServerP2P(mz, id, s){",
                           "function adottaScambiServerP2P(locali){",
                           "function testoContropartePerMotivoP2P(motivo){")]
        + [js("function p2pRitirato(o){", "\n}") + "\n", blocco])
    return r"""
const fs = require('fs'), vm = require('vm');
const [BUNDLE, STATO, MODO, BASE, BISCOTTO, CONTO, NOME] = process.argv.slice(2, 9);
const PASSI = process.argv.slice(9);
vm.runInThisContext(fs.readFileSync(BUNDLE, 'utf8'));
const NT = NostrTools;
const window = {NostrTools: NT, innerHeight: 800};
const _box = fs.existsSync(STATO) ? JSON.parse(fs.readFileSync(STATO, 'utf-8')) : {};
const localStorage = {getItem: k => (k in _box ? _box[k] : null), setItem: (k, v) => { _box[k] = String(v); }};
function chiaveP2P(k){ return k; }
const MOSTRO_ORDINI_CHIAVE = 'barattolo_mostro_ordini';
const DEMO = false, VETRINA = false;
let myTgId = Number(CONTO);
const API_BASE = BASE + '/api';
/* la Mini App porta l'initData; il sito il cookie (e sulla POST l'Origin) */
function authHdr(){ return MODO === 'tg' ? 'collaudo:' + CONTO + ':' + NOME : ''; }
const fetchVera = fetch;
let chiamate = [];
globalThis.fetch = (url, opz) => {
  chiamate.push(String(url).split('/api/')[1]);
  const o = Object.assign({}, opz || {});
  o.headers = Object.assign({}, o.headers || {});
  if (MODO === 'web') { o.headers['Cookie'] = 'barattolo_sessione=' + BISCOTTO; o.headers['Origin'] = BASE; }
  return fetchVera(url, o);
};
let p2pOrdineAperto = _box.APERTO || '', p2pMieiOrdini = null, p2pScambiServer = null, p2pScambiGiro = null,
    p2pToltiServer = null, p2pLeve = {chat: true};
const DIARIO = [];
function diarioP2P(r){ DIARIO.push(String(r).replace(/[0-9a-f]{8}/, 'ID')); }
function toast(){} function haptic(){} function renderP2P(){} function renderModerazioneP2P(){}
function aggiornaPallinoScambiP2P(){} function prendiCambiPubP2P(){}
function esc(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function nomeControparteP2P(o, ripiego){ return ripiego; }
function chiaveModeratoreP2P(){ return null; } function archivioModP2P(){ return {}; }
async function caricaNostrTools(){}
function vistaAttivaP2P(){ return 'view-p2pordine'; }
function mazzoMostro(){ return _box.MAZZO ? JSON.parse(_box.MAZZO) : null; }
/* LA PAGINA, di cartone: la lista della chat sta IN FONDO, sotto lo
   schermo, finche' non si scorre */
let RETT = {top: 1200, bottom: 1460, height: 260};
const LISTA = {getBoundingClientRect: () => RETT};
function el(id){ return id === 'p2pChatScLista' ? LISTA : null; }
/* IL RIDISEGNO: i due pezzi della chat nascono qui, come in `renderOrdineP2P` */
let ridisegni = 0, ULTIMA = {richiamo: '', riquadro: ''};
function renderOrdineP2P(){
  ridisegni++;
  const o = ordiniP2P()[p2pOrdineAperto];
  ULTIMA = o ? {richiamo: chatScRichiamoP2P(o), riquadro: bloccoChatScambioP2P(o)} : {richiamo: '', riquadro: ''};
}
""" + pezzi + r"""
globalThis.document = {visibilityState: 'visible', documentElement: {clientHeight: 800}, activeElement: null};
const scartoOra = Number(_box.AVANTI || 0); const oraVera = Date.now; let avanti = scartoOra;
Date.now = () => oraVera() + avanti;
const log0 = console.log; console.log = () => {};
const dormi = ms => new Promise(r => setTimeout(r, ms));
/* si aspetta che la pagina abbia finito quel che ha fatto partire */
async function quieto(){
  for (let i = 0; i < 80; i++) {
    await dormi(25);
    const inVolo = Object.keys(p2pChatScInVolo).length
      + Object.values(p2pChatScCerca).filter(x => x && x.volo).length
      + (p2pScambiGiro ? 1 : 0) + (p2pChatScNovitaInVolo ? 1 : 0);
    if (!inVolo && i >= 4) return;
  }
}
const foto = () => {
  const o = ordiniP2P()[p2pOrdineAperto] || {};
  const c = chatScDiP2P(p2pOrdineAperto);
  const richiamo = o.id ? chatScRichiamoP2P(o) : '';
  return {stato: o.stato || '', controparte: !!o.peer, riquadro: !!ULTIMA.riquadro, chiave: !!(c && c.sk),
          laSua: !!(c && c.loro), modo: (o.id && chatScServeP2P(o)) ? chatScPiedeP2P(o, c).modo : '',
          msgs: c ? (c.msgs || []).filter(m => !m.sis).map(m => (m.mio ? 'io: ' : 'altro: ') + m.testo) : [],
          daLeggere: chatScDaLeggereP2P(c), richiamo: richiamo ? (richiamo.match(/aria-label="([^"]*)"/) || [])[1] : '',
          conto: (richiamo.match(/chatsc-conto">([^<]*)</) || [])[1] || '', inVista: chatScInVistaP2P(),
          chiamate: chiamate.slice(), diario: DIARIO.slice()};
};
(async () => {
  const fuori = [];
  for (const passo of PASSI) {
    /* le domande al server si contano su TUTTI i passi di questa accensione */
    const [cosa, a, b, c, d, e] = passo.split('|');
    try {
      if (cosa === 'mazzo') {
        if (!_box.MAZZO) { const sk = NT.generateSecretKey();
          _box.MAZZO = JSON.stringify({sk: NT.utils.bytesToHex(sk), pub: NT.getPublicKey(sk), indice: 3}); }
        fuori.push({passo: passo, scambio: chiaveScambio(mazzoMostro().sk, Number(a)).pub});
      } else if (cosa === 'riga') {
        /* la riga com'e' quando la pagina si apre: SENZA la controparte */
        const ora = Math.floor(oraVera() / 1000);
        scriviOrdineP2P({id: a, lato: b, indice: Number(c), pubTrade: chiaveScambio(mazzoMostro().sk, Number(c)).pub,
          stato: d, mio: e === 'mio', peer: '', euro: 10, euroMax: 0, sats: 15000, satsNetti: 0, metodi: ['SEPA'],
          premium: 0, hold: null, contattato: true, cantDo: '', errore: '', creato: ora, aggiornato: ora});
        p2pOrdineAperto = a; _box.APERTO = a;
        renderOrdineP2P(); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'stato') {
        /* il coordinatore ha risposto: la riga cambia passo e la pagina si ridisegna */
        const r = ordiniP2P()[a]; r.stato = b; scriviOrdineP2P(r);
        renderOrdineP2P(); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'avanti') {
        avanti += Number(a); _box.AVANTI = String(avanti);
        fuori.push({passo: passo});
      } else if (cosa === 'battito') {
        chatScBattitoP2P(); await quieto(); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'scrivi') {
        await chatScInviaP2P(a, b); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'scorri') {
        RETT = {top: 300, bottom: 560, height: 260}; chatScGuardataP2P(); await quieto();
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'foto') {
        fuori.push(Object.assign({passo: passo}, foto()));
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
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    leggi, invia = SRV.chat_leggi_p2p, SRV.chat_invia_p2p
    moderatori, mod_chat = SRV.chat_moderatori_p2p, SRV.moderazione_chat_p2p

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        DETTI.append((chi, testo, bottone))
    SRV.notifica = notifica_finta

    # --- le identita': due da Telegram (l'initData di collaudo), quattro
    # da Nostr (il cookie di sessione VERO, nato da `crea_sessione`)
    con = banco.con_db()
    for tg, nome in ((N1, "Nostr uno"), (N2, "Nostr due"), (N3, "Nostr tre"),
                     (N4, "Nostr quattro"), (ADMIN, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                    "ln_address) VALUES(?,?,?,1,'')", (tg, nome, f"neg{abs(tg)}"))
    con.commit()
    con.close()
    for tg, nome in ((TG_V, "Venditore"), (TG_C, "Compratore"),
                     (ESTRANEO, "Estraneo"), (ADMIN, "Admin")):
        ACCESSO[tg] = {"x_tg_init_data": f"collaudo:{tg}:{nome}",
                       "barattolo_sessione": ""}
    for tg in (N1, N2, N3, N4):
        ACCESSO[tg] = {"x_tg_init_data": "",
                       "barattolo_sessione": SRV.crea_sessione(tg)}
    SRV.P2P_CHAT_PRESENTE_S = PRESENTE

    # quel che le sezioni condividono: la prima coppia, la chiave del
    # moderatore e il suo pacco (di cartone: il server non lo apre)
    o = ordine(10)
    V, C = TG_V, TG_C
    kmod = chiave(0xAB)
    pacco = busta("pacco-per-il-moderatore")

    async def sezione(numero, titolo, corpo_sezione):
        """Una sezione, col suo try: se esplode e' una rossa col suo
        nome, e le sorelle girano lo stesso."""
        print(f"\n{numero}) {titolo}")
        try:
            await corpo_sezione()
        except Exception as e:
            prova(f"{numero}) la sezione gira", "", f"{type(e).__name__}: {e}")

    async def s1():
        coppie = (("Telegram/Telegram", TG_V, TG_C), ("Telegram/Nostr", TG_V, N1),
                  ("Nostr/Telegram", N2, TG_C), ("Nostr/Nostr", N3, N4))
        for i, (nome, v, c) in enumerate(coppie):
            o = await scambio(10 + i, v, c, chiave(0x10 + i), chiave(0x30 + i))
            a = await chiama(leggi, v, {"ordine": o, "dopo": 0})
            b = await chiama(leggi, c, {"ordine": o, "dopo": 0})
            prova(f"{nome}: presa la vendita, la chat e' aperta per tutti e due, vuota",
                  [(True, 1, []), (True, 1, [])],
                  [(x.get("aperta"), x.get("giro"), x.get("buste")) for x in (a, b)])
            del DETTI[:]
            await asyncio.sleep(ASSENTE)          # nessuno dei due sta guardando
            sv = await chiama(invia, v, {"ordine": o, "tipo": "saluto", "busta": busta(f"saluto-v-{i}")})
            sc = await chiama(invia, c, {"ordine": o, "tipo": "saluto", "busta": busta(f"saluto-c-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: presentarsi non avvisa nessuno (un saluto non e' un messaggio)",
                  [], [chi for chi, _, _ in avvisi_chat()])
            m1 = await chiama(invia, v, {"ordine": o, "tipo": "msg", "busta": busta(f"msg-v-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: saluti e messaggio accettati, coi numeri in fila", True,
                  0 < (sv.get("n") or 0) < (sc.get("n") or 0) < (m1.get("n") or 0))
            b = await chiama(leggi, c, {"ordine": o, "dopo": 0})
            arrivate = b.get("buste") or []
            prova(f"{nome}: chi compra ritira le tre buste, e sa quali sono sue",
                  [("saluto", False), ("saluto", True), ("msg", False)],
                  [(x["tipo"], x["mia"]) for x in arrivate])
            prova(f"{nome}: ...e la busta arriva com'e' partita", busta(f"msg-v-{i}"),
                  arrivate[-1]["busta"] if arrivate else "")
            detti = avvisi_chat()
            prova(f"{nome}: a chi compra un avviso solo, senza il testo, col bottone",
                  # (20 ott 2026, chat-dalla-notifica) il tasto porta dritto alla chat: `&chat=1`
                  [(c, True, (SRV.P2P_BOTTONE_SCAMBIO, f"{SRV.LINK_LIBRO_P2P}?scambio={o}&chat=1"))],
                  [(chi, f"#{o[:4]}" in t and "msg-v" not in t and busta(f"msg-v-{i}") not in t, bt)
                   for chi, t, bt in detti])
            del DETTI[:]
            await asyncio.sleep(ASSENTE)
            await chiama(invia, c, {"ordine": o, "tipo": "msg", "busta": busta(f"msg-c-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: ...e la risposta avvisa chi vende", [v],
                  [chi for chi, _, _ in avvisi_chat()])

    async def s2():
        libera = ordine(50)
        pubblica(libera, V)
        r = await chiama(leggi, V, {"ordine": libera, "dopo": 0})
        prova("ordine ancora nel libro: per chi l'ha pubblicato la chat non e' aperta",
              (False, True), (r.get("aperta"), r.get("finita")))
        prova("...e non si puo' spedire", 409,
              no(await chiama(invia, V, {"ordine": libera, "tipo": "msg", "busta": busta("x")})))
        prova("un estraneo: 403 su leggere, spedire e chiedere i moderatori", [403, 403, 403],
              [no(await chiama(leggi, ESTRANEO, {"ordine": o, "dopo": 0})),
               no(await chiama(invia, ESTRANEO, {"ordine": o, "tipo": "msg", "busta": busta("x")})),
               no(await chiama(moderatori, ESTRANEO, {"ordine": o}))])
        prova("un ordine in una forma storta: 400", 400,
              no(await chiama(leggi, V, {"ordine": "../../etc", "dopo": 0})))

    async def s3():
        fin_qui = (await chiama(leggi, C, {"ordine": o, "dopo": 0}))["fino"]
        for k in range(3):
            await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta(f"offline-{k}")})
        r = await chiama(leggi, C, {"ordine": o, "dopo": fin_qui})
        prova("tre messaggi scritti ad app chiusa: al ritorno arrivano tutti, in ordine",
              [busta(f"offline-{k}") for k in range(3)], [x["busta"] for x in r["buste"]])
        prova("...e col segnalibro nuovo non tornano una seconda volta", [],
              (await chiama(leggi, C, {"ordine": o, "dopo": r["fino"]}))["buste"])
        perso = await chiama(leggi, C, {"ordine": o, "dopo": 10 ** 9})
        prova("un segnalibro OLTRE l'ultima busta dello scambio (il file e' rinato): "
              "il server lo dice, e rida' tutto da capo", (True, True),
              (perso.get("perso"), len(perso["buste"]) >= 7))
        prova("...un segnalibro giusto no", False,
              (await chiama(leggi, C, {"ordine": o, "dopo": perso["fino"]})).get("perso"))

    async def s4():
        await asyncio.sleep(RIPASSO)
        del DETTI[:]
        await asyncio.sleep(ASSENTE)
        for k in range(3):
            await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta(f"raffica-{k}")})
        await asyncio.sleep(0.3)
        prova("tre messaggi di fila a chi non guarda: un avviso solo", [C],
              [chi for chi, _, _ in avvisi_chat()])
        del DETTI[:]
        await chiama(leggi, C, {"ordine": o, "dopo": 0})          # legge...
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("appena-chiuso")})
        await asyncio.sleep(0.3)
        prova("ha ritirato un attimo fa: subito non lo si disturba", [],
              [chi for chi, _, _ in avvisi_chat()])
        await asyncio.sleep(RIPASSO)                                   # ...e non torna
        prova("...ma se non torna a leggere, l'avviso parte poco dopo", [C],
              [chi for chi, _, _ in avvisi_chat()])
        del DETTI[:]
        r = await chiama(leggi, C, {"ordine": o, "dopo": 0})
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("sta-guardando")})
        await asyncio.sleep(0.5)
        await chiama(leggi, C, {"ordine": o, "dopo": r["fino"]})  # sta guardando: lo ritira
        await asyncio.sleep(RIPASSO)
        prova("chi tiene la chat aperta e ritira non riceve nessun avviso", [],
              [chi for chi, _, _ in avvisi_chat()])
        con = banco.con_db()
        con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (C,))
        con.commit()
        con.close()
        await asyncio.sleep(ASSENTE)
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("avvisi-spenti")})
        await asyncio.sleep(0.3)
        prova("avvisi P2P spenti: la busta si consegna, l'avviso no", [],
              [chi for chi, _, _ in avvisi_chat()])
        con = banco.con_db()
        con.execute("UPDATE utenti SET avvisi_p2p=1 WHERE tg_id=?", (C,))
        con.commit()
        con.close()

    async def s5():
        prova("una busta oltre il tetto: 413", 413,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                       "busta": "A" * (SRV.P2P_CHAT_BUSTA_MAX + 4)})))
        prova("una busta che non e' una busta (testo in chiaro): 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                       "busta": "ciao, ti mando l'IBAN in chiaro " * 3})))
        prova("un tipo che non esiste: 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "foto", "busta": busta("x")})))
        prova("un messaggio con un destinatario: 400 (il `per` e' solo dei moderatori)", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("x"),
                                       "per": chiave(0x77)})))
        stessa = busta("la-stessa-due-volte")
        a = await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": stessa})
        b = await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": stessa})
        prova("la stessa busta rimandata: stesso numero, una riga sola",
              (True, 1), (a["n"] == b["n"],
                          len(cassetto("SELECT 1 FROM buste WHERE busta=?", stessa))))
        r2 = ordine(51)
        await scambio(51, V, C, chiave(0x51), chiave(0x52))
        SRV.P2P_CHAT_RAFFICA = 5
        esiti = [await chiama(invia, V, {"ordine": r2, "tipo": "msg", "busta": busta(f"r-{k}")})
                 for k in range(7)]
        prova("la raffica: cinque passano, dalla sesta 429",
              [True] * 5 + [429, 429],
              [e.get("ok") if isinstance(e, dict) else e[0] for e in esiti])
        SRV.P2P_CHAT_RAFFICA = 1000
        SRV.P2P_CHAT_MSG_MAX = 8
        esiti = [await chiama(invia, V, {"ordine": r2, "tipo": "msg", "busta": busta(f"t-{k}")})
                 for k in range(5)]
        prova("il tetto di messaggi dello scambio: oltre, 409",
              [True, True, True, 409, 409],
              [e.get("ok") if isinstance(e, dict) else e[0] for e in esiti])
        # (14 nov 2026, audit) il tetto e' di chi scrive: l'altra parte no
        e = await chiama(invia, C, {"ordine": r2, "tipo": "msg", "busta": busta("c-1")})
        prova("...e l'altra parte scrive ancora: il tetto e' di chi scrive",
              True, e.get("ok") if isinstance(e, dict) else e[0])
        SRV.P2P_CHAT_MSG_MAX = 200
        SRV.P2P_CHAT_RAFFICA = 20

    async def s6():
        fuori = await scambio(60, V, 0, chiave(0x60), chiave(0x61))
        r = await chiama(leggi, V, {"ordine": fuori, "dopo": 0})
        prova("dall'altra parte una chiave che non e' di nessun account: la chat non si apre",
              (False, False, True), (r.get("aperta"), r.get("finita"), r.get("senza_altro")))
        prova("...non si spedisce, e nel cassetto non si scrive niente",
              (409, 0), (no(await chiama(invia, V, {"ordine": fuori, "tipo": "saluto",
                                                  "busta": busta("s")})),
                         len(cassetto("SELECT 1 FROM buste WHERE ordine=?", fuori))))

    async def s7():
        con = banco.con_db()
        con.execute("INSERT OR REPLACE INTO p2p_moderatori(tg_id, chiave, creata) "
                    "VALUES(?,?,?)", (ADMIN, kmod, adesso()))
        con.commit()
        con.close()
        await evento(o, "hold-invoice-paid", "seller", "active", chiave(0x30), chiave(0x10))
        r = await chiama(moderatori, V, {"ordine": o})
        prova("a una delle due parti il server dice le chiavi pubbliche dei moderatori",
              [kmod], r.get("chiavi"))
        prova("una busta `mod` verso una chiave che non e' di un moderatore: 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "mod", "busta": busta("pacco"),
                                       "per": chiave(0xEE)})))
        await evento(o, "dispute-opened", "seller", "", chiave(0x30), chiave(0x10))
        # la riga della disputa la scrive il task degli avvisi: la si aspetta,
        # invece di sperare che tre decimi bastino su una macchina carica
        for _ in range(50):
            con = banco.con_db()
            c_e = con.execute("SELECT 1 FROM p2p_dispute WHERE ordine=?", (o,)).fetchone()
            con.close()
            if c_e:
                break
            await asyncio.sleep(0.1)
        r = await chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("a disputa aperta la chat resta aperta", True, r.get("aperta"))
        r = await chiama(invia, V, {"ordine": o, "tipo": "mod", "busta": pacco, "per": kmod})
        prova("la busta per il moderatore si accetta", True, r.get("ok"))
        prova("...e alle parti non torna mai fra le buste da ritirare", False,
              pacco in json.dumps(await chiama(leggi, C, {"ordine": o, "dopo": 0})))
        prova("il moderatore PRIMA di prendere la disputa non legge: 409", 409,
              no(await chiama(mod_chat, ADMIN, {"ordine": o})))
        prova("chi non e' moderatore: 403", 403, no(await chiama(mod_chat, V, {"ordine": o})))
        con = banco.con_db()
        con.execute("UPDATE p2p_dispute SET stato='presa', presa_da=?, presa_il=?, "
                    "chiave_moderatore=? WHERE ordine=?", (ADMIN, adesso(), kmod, o))
        con.commit()
        righe_disputa = con.execute("SELECT stato FROM p2p_dispute WHERE ordine=?",
                                    (o,)).fetchall()
        con.close()
        prova("(il coordinatore ha raccontato la disputa, ed e' presa)", ["presa"],
              [x["stato"] for x in righe_disputa])
        letture_prima = [tuple(x) for x in cassetto(
            "SELECT tg_id, letto_fino FROM letture WHERE ordine=? ORDER BY tg_id", o)]
        r = await chiama(mod_chat, ADMIN, {"ordine": o})
        prova("presa la disputa, il moderatore riceve i messaggi chiusi e il SUO pacco",
              (True, [pacco], True),
              (len(r.get("buste", [])) >= 8, [x["busta"] for x in r.get("chiavi", [])],
               {x["lato"] for x in r["buste"]} == {"compra", "vende"}))
        prova("...e leggendo non sposta il segnalibro di nessuna delle due parti",
              letture_prima, [tuple(x) for x in cassetto(
                  "SELECT tg_id, letto_fino FROM letture WHERE ordine=? ORDER BY tg_id", o)])
        con = banco.con_db()
        con.execute("UPDATE p2p_dispute SET chiave_moderatore=? WHERE ordine=?",
                    (chiave(0xAC), o))
        con.commit()
        con.close()
        prova("un pacco chiuso per un'altra chiave non gli arriva", [],
              (await chiama(mod_chat, ADMIN, {"ordine": o}))["chiavi"])

    async def s8():
        segno = busta("offline-1").encode()
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("(prima della fine la busta nel file c'e')", True, segno in grezzo)
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await evento(o, "released", "mostro", "admin", chiave(0x30), chiave(0x10))
        prova("chiuso lo scambio (il moderatore ha deciso): nel cassetto non resta una riga",
              (0, 0), (len(cassetto("SELECT 1 FROM buste WHERE ordine=?", o)),
                       len(cassetto("SELECT 1 FROM letture WHERE ordine=?", o))))
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("...e nel FILE i byte di quelle buste non ci sono piu' (secure_delete)",
              (False, False), (segno in grezzo, pacco.encode() in grezzo))
        prova("...il journal lo dice con una riga, senza una busta dentro",
              (True, False), ("🧹 Chat P2P: lo scambio " + o[:8] in giornale.getvalue(),
                              busta("offline-1") in giornale.getvalue()))
        r = await chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("al telefono il server dice che e' FINITA (e' li' che butta la chiave)",
              (False, True), (r.get("aperta"), r.get("finita")))
        dopo = await chiama(mod_chat, ADMIN, {"ordine": o})
        prova("...non si spedisce piu', e il moderatore non ha piu' niente da leggere",
              (409, True), (no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                                     "busta": busta("dopo")})),
                            dopo[0] == 409 if isinstance(dopo, tuple)
                            else dopo.get("buste") == [] and dopo.get("chiavi") == []))

    async def s9():
        t = await scambio(90, V, C, chiave(0x90), chiave(0x91))
        await chiama(invia, V, {"ordine": t, "tipo": "msg", "busta": busta("giro-uno")})
        await chiama(leggi, C, {"ordine": t, "dopo": 0})
        await evento(t, "expired", "mostro", "taker-timeout", chiave(0x91), chiave(0x90))
        prova("chi aveva preso non ha proseguito: le buste di quel giro se ne vanno", 0,
              len(cassetto("SELECT 1 FROM buste WHERE ordine=?", t)))
        registra_chiave(chiave(0x92), N1)
        # UN SECONDO PIENO fra le due prese: stesso ordine, stesso momento e
        # stessa ora scritta sono, per la rotta degli eventi, il RETRY del
        # coordinatore — e la seconda presa non verrebbe registrata (il
        # collaudo passava o esplodeva secondo dove cadeva il secondo)
        await asyncio.sleep(1.1)
        await evento(t, "taken", "buyer", "invoice-next", chiave(0x92), chiave(0x90))
        r = await chiama(leggi, N1, {"ordine": t, "dopo": 0})
        prova("ripreso da un altro: giro nuovo, chat vuota", (True, 2, []),
              (r.get("aperta"), r.get("giro"), r.get("buste")))
        prova("...e chi l'aveva preso prima adesso e' un estraneo", 403,
              no(await chiama(leggi, C, {"ordine": t, "dopo": 0})))

    async def s10():
        s = await scambio(100, V, C, chiave(0xA0), chiave(0xA1))
        await chiama(invia, V, {"ordine": s, "tipo": "msg", "busta": busta("scopa")})
        await chiama(leggi, C, {"ordine": s, "dopo": 0})
        con = banco.con_db()
        con.execute("INSERT INTO p2p_momenti(ordine, momento, quando, fonte, giro) "
                    "VALUES(?,'annullato',?,'mostro',1)", (s, adesso()))
        con.execute("UPDATE p2p_ordini SET stato='canceled' WHERE ordine=?", (s,))
        con.commit()
        con.close()
        prova("(lo scambio e' finito senza che l'evento passasse dalla rotta: le buste ci sono)",
              1, len(cassetto("SELECT 1 FROM buste WHERE ordine=?", s)))
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await SRV._giro_chat_p2p()
        prova("la scopa le toglie, e lo dice", (0, 0, True),
              (len(cassetto("SELECT 1 FROM buste WHERE ordine=?", s)),
               len(cassetto("SELECT 1 FROM letture WHERE ordine=?", s)),
               "🧹 Chat P2P: cancellate le buste di 1 scambio finito" in giornale.getvalue()))
        vivo = cassetto("SELECT COUNT(*) FROM buste WHERE ordine=?", ordine(11))[0][0]
        prova("...e non tocca gli scambi ancora in corso", True, vivo >= 3)
        cc = SRV.db_chat()
        cc.execute("INSERT INTO buste(ordine, giro, da, tipo, busta, quando) VALUES(?,?,?,?,?,?)",
                   (ordine(11), 1, TG_V, "msg", busta("vecchissima"),
                    adesso() - SRV.P2P_CHAT_VITA_MAX_S - 60))
        cc.commit()
        cc.close()
        await SRV._giro_chat_p2p()
        prova("la rete sotto la scopa: una busta piu' vecchia di ogni scambio possibile se ne va",
              0, len(cassetto("SELECT 1 FROM buste WHERE busta=?", busta("vecchissima"))))

    async def s11():
        prova("il cassetto e' un file a parte, accanto al database di tutti",
              (True, True), (os.path.realpath(SRV.DB_CHAT) != os.path.realpath(SRV.DB),
                             os.path.dirname(os.path.realpath(SRV.DB_CHAT))
                             == os.path.dirname(os.path.realpath(SRV.DB))))
        viva = busta("msg-v-1").encode()
        prova("una busta viva sta nel cassetto e NON nel database di tutti (quello dei backup)",
              (True, False), (viva in open(SRV.DB_CHAT, "rb").read(),
                              viva in open(SRV.DB, "rb").read()))
        con = banco.con_db()
        tabelle = [x[0] for x in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND "
            "(name LIKE '%chat%' OR name IN ('buste', 'letture'))")]
        con.close()
        prova("...che di tabelle della chat non ne ha nessuna", [], tabelle)
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await asyncio.sleep(ASSENTE)
            await chiama(invia, TG_V, {"ordine": ordine(11), "tipo": "msg",
                                       "busta": busta("nel-journal"),
                                       "testo": "IBAN SEGRETO IN CHIARO"})
            await asyncio.sleep(0.3)
        prova("un invio riuscito scrive nel journal la sola riga dell'avviso",
              (True, False, False),
              (f"💬 Chat P2P: nuovo messaggio sullo scambio {ordine(11)[:8]}, avvisato {N1}"
               in giornale.getvalue(), busta("nel-journal") in giornale.getvalue(),
               "SEGRETO" in giornale.getvalue()))
        prova("...e un campo `testo` messo nel corpo apposta non finisce da nessuna parte",
              False, b"SEGRETO" in open(SRV.DB_CHAT, "rb").read()
              or "SEGRETO" in json.dumps(DETTI, ensure_ascii=False))
        filtro = SRV._ChatFuoriDalJournal()

        def passa(strada, codice):
            return filtro.filter(logging.LogRecord(
                "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                ("127.0.0.1:1", "POST", strada, "1.1", codice), None))
        prova("gli accessi RIUSCITI della chat non vanno nel registro; gli errori e il resto si'",
              [False, False, False, False, True, True, True],
              [passa("/api/p2p/chat/leggi", 200), passa("/api/p2p/chat/invia", 200),
               passa("/api/p2p/chat/moderatori", 200), passa("/api/p2p/moderazione/chat", 200),
               passa("/api/p2p/chat/invia", 429), passa("/api/p2p/chat/leggi", 500),
               passa("/api/p2p/recapito", 200)])

    async def s12():
        novita = SRV.chat_novita_p2p
        o11, o12 = ordine(11), ordine(12)
        prima = [tuple(x) for x in cassetto("SELECT * FROM letture ORDER BY ordine, tg_id")]
        r = await chiama(novita, N1, {"ordini": [o11, o12, ordine(999)]})
        ultimo = cassetto("SELECT MAX(n) FROM buste WHERE ordine=? AND tipo='msg' AND da=?",
                          o11, TG_V)[0][0]
        prova("a chi compra il numero dell'ultimo messaggio di chi vende, e solo per i SUOI scambi",
              ({o11: ultimo}, False, True), (r.get("ultimi"), r.get("spenta"), (ultimo or 0) > 0))
        prova("...e la domanda non sposta nessun segnalibro", prima,
              [tuple(x) for x in cassetto("SELECT * FROM letture ORDER BY ordine, tg_id")])
        prova("un estraneo non impara niente degli scambi altrui", {},
              (await chiama(novita, ESTRANEO, {"ordini": [o11, o12]})).get("ultimi"))
        prova("una domanda storta: 400", [400, 400, 400],
              [no(await chiama(novita, N1, {"ordini": "tutti"})),
               no(await chiama(novita, N1, {"ordini": [o11] * (SRV.P2P_CHAT_NOVITA_MAX + 1)})),
               no(await chiama(novita, N1, {"ordini": ["../etc"]}))])
        # chi ha l'app aperta su un'ALTRA pagina: il pallino chiede, ma
        # l'avviso fuori dall'app deve partire lo stesso
        await chiama(leggi, N1, {"ordine": o11, "dopo": 0})
        del DETTI[:]
        await asyncio.sleep(ASSENTE)
        await chiama(novita, N1, {"ordini": [o11]})
        await chiama(invia, TG_V, {"ordine": o11, "tipo": "msg", "busta": busta("dopo-il-pallino")})
        await asyncio.sleep(0.4)
        prova("la domanda del pallino non dice «sta guardando»: l'avviso fuori dall'app parte lo stesso",
              [N1], [chi for chi, _, _ in avvisi_chat()])
        r = await chiama(novita, N1, {"ordini": [o11]})
        prova("...e il pallino vede il messaggio nuovo", True,
              (r.get("ultimi") or {}).get(o11, 0) > (ultimo or 0))

    async def s13():
        novita = SRV.chat_novita_p2p
        o11, o12 = ordine(11), ordine(12)
        quante = len(cassetto("SELECT 1 FROM buste WHERE ordine=?", o12))
        SRV.P2P_CHAT_SCAMBIO = False
        try:
            r = await chiama(leggi, N1, {"ordine": o11, "dopo": 0})
            prova("leva spenta: la chat non si apre, e il server dice che e' SPENTA (non finita)",
                  (False, True, False), (r.get("aperta"), r.get("spenta"), r.get("finita")))
            prova("...non accetta buste nuove, di nessun tipo", [409, 409],
                  [no(await chiama(invia, TG_V, {"ordine": o11, "tipo": "msg",
                                                 "busta": busta("a-leva-spenta")})),
                   no(await chiama(invia, TG_V, {"ordine": o11, "tipo": "saluto",
                                                 "busta": busta("saluto-a-leva-spenta")}))])
            r = await chiama(novita, N1, {"ordini": [o11]})
            prova("...il pallino tace", ({}, True), (r.get("ultimi"), r.get("spenta")))
            prova("...la busta delle leve lo dice al telefono", False, SRV._p2p_leve().get("chat"))
            prova("...le buste che c'erano restano dov'erano", (True, quante),
                  (quante > 0, len(cassetto("SELECT 1 FROM buste WHERE ordine=?", o12))))
            await evento(o12, "released", "seller", "", chiave(0x32), chiave(0x12))
            prova("...e a scambio finito se ne vanno come sempre: la scopa non guarda la leva", 0,
                  len(cassetto("SELECT 1 FROM buste WHERE ordine=?", o12)))
        finally:
            SRV.P2P_CHAT_SCAMBIO = True
        prova("riaccesa, la busta delle leve lo ridice", True, SRV._p2p_leve().get("chat"))
        r = await chiama(leggi, N1, {"ordine": o11, "dopo": 0})
        prova("...e la chat di uno scambio in corso riprende con le sue buste", (True, True),
              (r.get("aperta"), len(r.get("buste") or []) >= 4))

    async def s14():
        # IL CASO DAL CAMPO (12 ott 2026, notte): un account Telegram
        # COLLEGATO a una npub, con TRE PORTE sullo stesso telefono — la
        # web app installata entrata con Telegram (un cookie), la stessa
        # entrata con Nostr (un altro cookie, STESSO account: il login
        # Nostr di un account collegato apre quello), e la Mini App
        # dentro Telegram, dove porta il tasto dell'avviso (l'initData).
        # Dall'altra parte un nativo Nostr. La copia sigillata e' una
        # busta di cartone: il server non la apre, la riconsegna.
        novita = SRV.chat_novita_p2p
        TG_L, WEB, NOSTR, MINI = 444, "web-444", "nostr-444", "mini-444"
        npub = "npub1" + "collaudo" * 6
        con = banco.con_db()
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,"
                    "npub,npub_verificata,npub_accesso) VALUES(?,?,?,1,'',?,1,?)",
                    (TG_L, "Collegato", "neg444", npub, npub))
        con.commit()
        con.close()
        ACCESSO[WEB] = {"x_tg_init_data": "", "barattolo_sessione": SRV.crea_sessione(TG_L)}
        ACCESSO[NOSTR] = {"x_tg_init_data": "", "barattolo_sessione": SRV.crea_sessione(TG_L)}
        ACCESSO[MINI] = {"x_tg_init_data": f"collaudo:{TG_L}:Collegato", "barattolo_sessione": ""}
        prova("le tre porte sono lo stesso account: due cookie e l'initData di Telegram",
              [TG_L, TG_L, TG_L],
              [SRV.verifica_utente(ACCESSO[p]["x_tg_init_data"], ACCESSO[p]["barattolo_sessione"])["id"]
               for p in (WEB, NOSTR, MINI)])
        t = await scambio(140, N1, TG_L, chiave(0x41), chiave(0x42))
        copia, copia_altro = busta("copia-sigillata-di-444"), busta("copia-sigillata-di-N1")
        del DETTI[:]
        r = await chiama(invia, WEB, {"ordine": t, "tipo": "chiave", "busta": copia})
        prova("la web app installata lascia la COPIA SIGILLATA della sua chiave: il postino la prende",
              True, (r.get("n") or 0) > 0)
        await chiama(invia, WEB, {"ordine": t, "tipo": "saluto", "busta": busta("saluto-444")})
        await chiama(invia, N1, {"ordine": t, "tipo": "chiave", "busta": copia_altro})
        await chiama(invia, N1, {"ordine": t, "tipo": "saluto", "busta": busta("saluto-N1")})
        await asyncio.sleep(0.4)
        prova("...una copia (come un saluto) non avvisa nessuno: avvisa solo un messaggio", [], avvisi_chat())
        prova("...e non porta un destinatario: con `per` e' una richiesta storta", 400,
              no(await chiama(invia, WEB, {"ordine": t, "tipo": "chiave", "busta": copia,
                                           "per": chiave(0xAB)})))
        await chiama(invia, WEB, {"ordine": t, "tipo": "msg", "busta": busta("dalla-web-app")})
        await chiama(invia, N1, {"ordine": t, "tipo": "msg", "busta": busta("dal-nativo")})

        def vede(r):
            return sorted((b["tipo"], b["mia"], b["busta"]) for b in (r.get("buste") or []))
        tutto_444 = sorted([("chiave", True, copia), ("saluto", True, busta("saluto-444")),
                            ("saluto", False, busta("saluto-N1")), ("msg", True, busta("dalla-web-app")),
                            ("msg", False, busta("dal-nativo"))])
        r = await chiama(leggi, WEB, {"ordine": t, "dopo": 0})
        fino = r.get("fino") or 0
        prova("STESSA PORTA: ritira la sua copia, i due saluti e i due messaggi", tutto_444, vede(r))
        r = await chiama(leggi, WEB, {"ordine": t, "dopo": fino})
        prova("CHIUDI E RIAPRI SENZA LOGIN (stesso cookie, stesso segnalibro): niente di nuovo, niente di perso",
              (True, [], False), (r.get("aperta"), r.get("buste"), bool(r.get("perso"))))
        prova("LA MEMORIA DEL BROWSER CANCELLATA (stesso cookie, segnalibro a zero): torna tutto, copia compresa",
              tutto_444, vede(await chiama(leggi, WEB, {"ordine": t, "dopo": 0})))
        prova("LA MINI APP DENTRO TELEGRAM (il tasto dell'avviso): stesso account, ritrova la copia e tutta la chat",
              tutto_444, vede(await chiama(leggi, MINI, {"ordine": t, "dopo": 0})))
        prova("LA WEB APP ENTRATA CON NOSTR (account collegato): lo stesso",
              tutto_444, vede(await chiama(leggi, NOSTR, {"ordine": t, "dopo": 0})))
        r = await chiama(leggi, N1, {"ordine": t, "dopo": 0})
        prova("L'ALTRA PARTE ritira la SUA copia e mai quella di chi compra",
              ([copia_altro], False),
              ([b["busta"] for b in (r.get("buste") or []) if b["tipo"] == "chiave"],
               copia in json.dumps(r)))
        prova("...un estraneo resta fuori", 403, no(await chiama(leggi, ESTRANEO, {"ordine": t, "dopo": 0})))
        await chiama(invia, MINI, {"ordine": t, "tipo": "msg", "busta": busta("dalla-mini-app")})
        r = await chiama(leggi, WEB, {"ordine": t, "dopo": fino})
        prova("un messaggio scritto dalla Mini App la web app lo ritira come SUO, e l'altra parte lo riceve",
              ([("msg", True, busta("dalla-mini-app"))], True),
              (vede(r), busta("dalla-mini-app") in json.dumps(await chiama(leggi, N1, {"ordine": t, "dopo": 0}))))
        # in disputa: il moderatore riceve i messaggi chiusi e il pacco, MAI le copie
        await evento(t, "dispute-opened", "buyer", "", chiave(0x42), chiave(0x41))
        for _ in range(50):
            con = banco.con_db()
            c_e = con.execute("SELECT 1 FROM p2p_dispute WHERE ordine=?", (t,)).fetchone()
            con.close()
            if c_e:
                break
            await asyncio.sleep(0.1)
        con = banco.con_db()
        con.execute("UPDATE p2p_dispute SET stato='presa', presa_da=?, presa_il=?, chiave_moderatore=? "
                    "WHERE ordine=?", (ADMIN, adesso(), kmod, t))
        con.commit()
        con.close()
        m = await chiama(mod_chat, ADMIN, {"ordine": t})
        prova("IL MODERATORE che ha preso la disputa riceve i messaggi chiusi, e nessuna copia sigillata",
              (3, False, False), (len(m.get("buste") or []), copia in json.dumps(m), copia_altro in json.dumps(m)))
        # le chat finite: l'unica cosa che fa buttare una chiave al telefono
        ignoto = ordine(149)
        r = await chiama(novita, WEB, {"ordini": [t, ignoto]})
        prova("LE CHAT FINITE: a scambio in corso nessuna — tranne lo scambio che il server non conosce",
              [ignoto], r.get("finite"))
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("(prima della fine la copia nel file c'e', e nel database di tutti no)", (True, False),
              (copia.encode() in grezzo, copia.encode() in open(SRV.DB, "rb").read()))
        await evento(t, "released", "mostro", "admin", chiave(0x42), chiave(0x41))
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("LA FINE: le copie sigillate se ne vanno con le buste, anche dai byte del file",
              (0, False, False), (len(cassetto("SELECT 1 FROM buste WHERE ordine=?", t)),
                                  copia.encode() in grezzo, copia_altro.encode() in grezzo))
        prova("...e il server lo dice a tutte le porte delle due parti, non a chi non c'entra",
              [[t], [t], [t], [t], []],
              [(await chiama(novita, p, {"ordini": [t]})).get("finite")
               for p in (WEB, NOSTR, MINI, N1, ESTRANEO)])
        SRV.P2P_CHAT_SCAMBIO = False
        try:
            r = await chiama(novita, MINI, {"ordini": [t]})
            prova("...anche a leva spenta: uno scambio finito e' finito", ([t], True, {}),
                  (r.get("finite"), r.get("spenta"), r.get("ultimi")))
        finally:
            SRV.P2P_CHAT_SCAMBIO = True
        prova("...e a scambio finito una copia non entra piu'", 409,
              no(await chiama(invia, WEB, {"ordine": t, "tipo": "chiave", "busta": busta("copia-tardi")})))

    async def s15():
        # LE QUATTRO COPPIE DI ACCESSO, con la copia: a ognuno torna la
        # SUA, da qualunque porta sia entrato l'altro
        coppie = [("Telegram e Telegram", TG_V, TG_C), ("Telegram e Nostr", TG_V, N2),
                  ("Nostr e Telegram", N3, TG_C), ("Nostr e Nostr", N3, N4)]
        esiti = []
        for i, (nome, vende, compra) in enumerate(coppie):
            t = await scambio(150 + i, vende, compra, chiave(0x50 + i), chiave(0x60 + i))
            cv, cc_ = busta(f"copia-di-chi-vende-{i}"), busta(f"copia-di-chi-compra-{i}")
            await chiama(invia, vende, {"ordine": t, "tipo": "chiave", "busta": cv})
            await chiama(invia, compra, {"ordine": t, "tipo": "chiave", "busta": cc_})
            rv = await chiama(leggi, vende, {"ordine": t, "dopo": 0})
            rc = await chiama(leggi, compra, {"ordine": t, "dopo": 0})
            esiti.append((nome,
                          [b["busta"] for b in (rv.get("buste") or []) if b["tipo"] == "chiave"] == [cv],
                          [b["busta"] for b in (rc.get("buste") or []) if b["tipo"] == "chiave"] == [cc_]))
            await evento(t, "canceled", "buyer", "", chiave(0x60 + i), chiave(0x50 + i))
        prova("la copia sigillata torna solo a chi l'ha spedita, con tutte e quattro le coppie di accesso",
              [(n, True, True) for n, _, _ in coppie], esiti)

    async def s16():
        # «LA CHAT SI ATTIVA SOLO SE SCORRI» (12 ott 2026, notte, dal campo di
        # Andrea). Lo scorrimento non c'entrava: una pagina dello scambio
        # GIA' APERTA non chiedeva al server chi fosse l'altra parte — chi ha
        # appena preso resta sulla pagina che la presa ha aperto, chi ha
        # pubblicato puo' averla davanti quando l'ordine viene preso — e
        # senza la controparte non c'e' riquadro, non c'e' chiave, e l'altra
        # persona legge «Si apre appena … apre lo scambio» fino al battito
        # dei due minuti. QUI: il client VERO in node contro il server VERO,
        # la pagina aperta e MAI riaperta, la lista della chat in fondo e mai
        # scorsa (finche' non lo si dice), la controparte non ancora nota.
        import shutil
        import subprocess
        import tempfile
        import collaudo_tolti_ovunque as tolti
        node = shutil.which("node")
        if not node:
            prova("node c'e'", True, False)
            return
        t = ordine(160)
        pubblica(t, TG_V)
        srv, base = tolti.avvia_ponte()
        cart = tempfile.mkdtemp(prefix="chat_subito_")
        mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
        prog = os.path.join(cart, "telefono.js")
        open(prog, "w", encoding="utf-8").write(dispositivo_chat(mini))
        # chi compra e' nella WEB APP (il cookie del Login Widget), chi vende nella Mini App
        chi = {"T": ("web", tolti.login_web(TG_C), TG_C, "Compratore"),
               "M": ("tg", "", TG_V, "Venditore")}

        def telefono(nome, *passi):
            modo, biscotto, conto, come_si_chiama = chi[nome]
            r = subprocess.run([node, prog, os.path.join(banco.QUI, "vendor", "nostr.bundle.js"),
                                os.path.join(cart, nome + ".json"), modo, base, biscotto,
                                str(conto), come_si_chiama, *passi],
                               capture_output=True, text=True, encoding="utf-8", timeout=120)
            try:
                fuori = json.loads(r.stdout.strip().splitlines()[-1])
            except Exception:
                fuori = [{"ERRORE": (r.stdout or "")[-300:] + (r.stderr or "")[-700:]}] * len(passi)
            return fuori[-1]

        def buste_di(conto):
            return [r[0] for r in cassetto("SELECT tipo FROM buste WHERE ordine=? AND da=? ORDER BY n",
                                           t, conto)]
        kt = km = ""
        try:
            kt = telefono("T", "mazzo|1").get("scambio") or ""
            km = telefono("M", "mazzo|1").get("scambio") or ""
            prova("i due telefoni hanno ognuno il suo profilo e la sua chiave di scambio", (64, 64, True),
                  (len(kt), len(km), kt != km))
            registra_chiave(km, TG_V)
            registra_chiave(kt, TG_C)
            # CHI HA APPENA PRESO: la pagina si apre alla presa («prendo»)
            f = telefono("T", f"riga|{t}|compro|1|prendo|", "battito")
            prova("PRIMA che il coordinatore risponda la pagina non chiede niente a nessuno: non c'e' "
                  "ancora uno scambio", ([], False, False),
                  (sullo_scambio(f), f.get("controparte"), f.get("riquadro")))
            f = telefono("T", f"stato|{t}|attesa_mia_fattura")
            prova("IL COORDINATORE HA RISPOSTO e il server non sa ancora della presa: la pagina CHIEDE "
                  "SUBITO la controparte (una domanda all'archivio), e non la trova",
                  (["p2p/scambi"], False, False, ""),
                  (sullo_scambio(f), f.get("controparte"), f.get("riquadro"), f.get("ERRORE", "") or f.get("ESPLOSO", "")))
            await evento(t, "taken", "buyer", "invoice-next", kt, km)
            f = telefono("T", "avanti|5000", "battito")
            prova("AL BATTITO DOPO (cinque secondi), a pagina aperta e MAI riaperta, con la chat in fondo e "
                  "MAI scorsa: la controparte arriva, il riquadro nasce, la chiave pure",
                  (True, True, True, False, "p2p/scambi"),
                  (f.get("controparte"), f.get("riquadro"), f.get("chiave"), f.get("inVista"),
                   (sullo_scambio(f) or [""])[0]))
            prova("...sul server ci sono la sua copia sigillata e il suo saluto, e il diario lo dice",
                  (["chiave", "saluto"], True),
                  (buste_di(TG_C), any("controparte arrivata dal server" in r for r in f.get("diario") or [])))
            # (20 ott 2026, chat-dalla-notifica) ...e intanto SCRIVE: per la chiave dello
            # scambio dell'altra persona, che il coordinatore ha gia' detto
            prova("...e intanto si scrive gia': per la chiave dello scambio dell'altra persona", "scrivi",
                  f.get("modo"))
            # CHI HA PUBBLICATO ha la pagina del suo ordine gia' davanti quando viene preso
            f = telefono("M", f"riga|{t}|vendo|1|pubblicato|mio", "battito")
            prova("CHI HA PUBBLICATO, con la pagina del suo ordine gia' aperta: finche' il passo e' «nel "
                  "libro» non chiede niente", ([], False), (sullo_scambio(f), f.get("riquadro")))
            f = telefono("M", f"stato|{t}|attesa_mia_hold")
            prova("...gli arriva «blocca i sats»: la pagina chiede la controparte, la chat parte SUBITO — "
                  "senza riaprire, senza scorrere — e trova gia' la chiave dell'altra persona",
                  (True, True, True, True, "scrivi", False),
                  (f.get("controparte"), f.get("riquadro"), f.get("chiave"), f.get("laSua"), f.get("modo"),
                   f.get("inVista")))
            prova("...anche la sua copia e il suo saluto sono sul server", ["chiave", "saluto"], buste_di(TG_V))
            f = telefono("T", "battito")
            prova("...e chi aveva preso smette di aspettare al suo battito: si scrive", "scrivi", f.get("modo"))
            prova("IL RICHIAMO IN CIMA c'e' dalla presa, senza numero finche' non c'e' niente di nuovo",
                  ("Vai alla chat", "", 0), (f.get("richiamo"), f.get("conto"), f.get("daLeggere")))
            telefono("M", f"scrivi|{t}|Ho bloccato i sats")
            f = telefono("T", "battito")
            prova("ARRIVA UN MESSAGGIO a chi ha la pagina aperta e la chat in fondo, fuori dallo schermo: "
                  "non e' «visto», e il richiamo porta il numero",
                  (["altro: Ho bloccato i sats"], 1, "1", "Chat: 1 messaggio nuovo", False),
                  (f.get("msgs"), f.get("daLeggere"), f.get("conto"), f.get("richiamo"), f.get("inVista")))
            f = telefono("T", "scorri")
            prova("...scorre fino alla chat (o tocca il richiamo): il messaggio e' visto e il numero se ne va",
                  (0, "", "Vai alla chat", True),
                  (f.get("daLeggere"), f.get("conto"), f.get("richiamo"), f.get("inVista")))
        finally:
            srv.shutdown()
            # i compiti nati nel giro del ponte non sono di questo: non si aspettano qui
            qui = asyncio.get_running_loop()
            for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
                for c in list(gruppo):
                    if c.get_loop() is not qui:
                        gruppo.discard(c)
            await evento(t, "canceled", "buyer", "", kt or chiave(0x71), km or chiave(0x72))

    await sezione(1, "LE QUATTRO COPPIE DI ACCESSO", s1)
    await sezione(2, "PRIMA DELLA PRESA, E PER UN ESTRANEO", s2)
    await sezione(3, "LA CONSEGNA A CHI E' OFFLINE", s3)
    await sezione(4, "UN AVVISO PER OGNI «C'E' DA LEGGERE»", s4)
    await sezione(5, "I TETTI", s5)
    await sezione(6, "LA PARTE CHE SCAMBIA DA UN'ALTRA APP", s6)
    await sezione(7, "LA DISPUTA E IL MODERATORE", s7)
    await sezione(8, "LA FINE: LE BUSTE SPARISCONO DAL FILE", s8)
    await sezione(9, "L'ORDINE TORNATO NEL LIBRO E RIPRESO DA UN ALTRO", s9)
    await sezione(10, "LA SCOPA DEL MINUTO", s10)
    await sezione(11, "NIENTE ALTROVE", s11)
    await sezione(12, "IL PALLINO: LA DOMANDA CHE NON SEGNA NIENTE", s12)
    await sezione(13, "LA LEVA SPENTA", s13)
    await sezione(14, "LA CHAT SEGUE LO SCAMBIO: LA COPIA SIGILLATA E LE TRE PORTE DELLO STESSO ACCOUNT", s14)
    await sezione(15, "LA COPIA, CON LE QUATTRO COPPIE DI ACCESSO", s15)
    await sezione(16, "LA CHAT PARTE SUBITO: PAGINA APERTA, MAI SCORSA, CONTROPARTE NON ANCORA NOTA (il client vero contro il server vero)", s16)
    for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
        if gruppo:
            await asyncio.gather(*list(gruppo), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    banco.SRV.P2P_RESPIRO_S = 1
    banco.SRV.P2P_RESPIRO_NOME_S = 1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
