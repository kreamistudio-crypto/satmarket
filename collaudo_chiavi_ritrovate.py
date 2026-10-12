# -*- coding: utf-8 -*-
"""
LE CHIAVI DELLO SCAMBIO DOPO LA MEMORIA SVUOTATA, SUL SERVER VERO
(11 ott 2026, cantiere «tor-chiavi-scambio», decisione di Andrea).

Dal campo: un nativo Nostr entra dal .onion con Tor Browser, prende un
ordine Barattozon, paga il PayCode; Tor Browser svuota la memoria alla
chiusura, e al rientro le chiavi dello scambio non ci sono piu' — la
riga ricostruita dall'archivio del server e' «solo da guardare», i
gesti spenti. `prove.py` (`prove_tor_chiavi_scambio`) difende i giudici
e il banco coi tre firmatari; qui gira il SERVER VERO, sul database
usa-e-getta, col CLIENT VERO in node (il bundle di nostr-tools, la
derivazione vera) nei tre casi, e si cammina la cura intera:

  1. il seme dal server per un nativo Nostr e' un 409 (apposta), oggi
     come ieri;
  2. NSEC NEL BROWSER: il dispositivo 1 deriva il profilo dalla nsec e
     prende un ordine (la trade key 1); le due pubbliche vanno a
     `/api/p2p/chiavi` (rotta vera); mostrod racconta la presa e la
     garanzia (gli eventi della patch 0007, coi due giudici della rotta);
     `/api/p2p/scambi` (rotta vera) porta la riga con `chiave_mia`;
     IL BROWSER SI SVUOTA; il dispositivo 2, con la stessa nsec, deriva
     lo stesso profilo, ritrova la trade key dalla pubblica detta dal
     server, e la riga NON e' solo da guardare: i gesti ci sono;
  3. BUNKER: il dispositivo 1 ha un profilo nato a caso, lo copia
     cifrato sui relay (di cartone, in node); il dispositivo 2 vuoto
     col bunker riprende la copia dai relay, e la riga ha le chiavi;
  4. ESTENSIONE (il vero `firmatarioEstensione` su un `window.nostr` di
     cartone): lo stesso;
  5. IL CONTROLLO NEGATIVO: un dispositivo senza nsec, senza copia e con
     un'estensione che non cifra resta solo da guardare, coi gesti
     spenti — e' il caso del campo, e la riga lo dice onesta.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore, niente rete (i relay della copia sono un oggetto in node).

USO:  python collaudo_chiavi_ritrovate.py
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

NATIVO = -777                    # un nativo Nostr: tg_id NEGATIVO
ORD = {"nsec": "5a1e0000-7071-4a2b-9c3d-0000000000c1",
       "bunker": "5a1e0000-7071-4a2b-9c3d-0000000000c2",
       "estensione": "5a1e0000-7071-4a2b-9c3d-0000000000c3",
       "spento": "5a1e0000-7071-4a2b-9c3d-0000000000c4",
       # (12 ott 2026) i passaggi fra i modi di entrare, stessa npub
       "nsec-bunker": "5a1e0000-7071-4a2b-9c3d-0000000000c5",
       "bunker-nsec": "5a1e0000-7071-4a2b-9c3d-0000000000c6",
       "estensione-nsec": "5a1e0000-7071-4a2b-9c3d-0000000000c7"}


def js(mini, firma, fine="\n}\n"):
    i = mini.index(firma)
    return mini[i:mini.index(fine, i) + len(fine)]


def semina_ordini():
    """Quattro ordini di chi vende, nel libro, e il nativo in `utenti`."""
    con = banco.con_db()
    adesso = int(time.time())
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,ln_address,"
                "npub,npub_verificata) VALUES(?,?,?,1,'',?,1)",
                (NATIVO, "Nativo Nostr", "negnativo", "npub1nativo"))
    for ordine in ORD.values():
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,visto,"
                    "preso_da,euro) VALUES(?,?,?,'pending','sell',1,?,0,'10,00 €')",
                    (ordine, banco.VENDE, adesso, adesso))
    con.commit()
    con.close()


def scambi(chi):
    banco.come(chi)
    r = asyncio.run(banco.SRV.scambi_p2p())
    return json.loads(r.body)


def seme(chi):
    """La rotta vera del seme, come la vede `chi`: la risposta, o il
    codice del rifiuto."""
    banco.come(chi)
    try:
        return banco.SRV.seme_profilo_p2p()
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)


PEZZI = None


def pezzi_client():
    """Il client vero: il blocco del mazzo intero (seme, copia, rete di
    sicurezza), l'adozione dell'archivio del server, i firmatari e il
    giudice dei bottoni."""
    global PEZZI
    if PEZZI is not None:
        return PEZZI
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    riga = lambda firma: mini[mini.index(firma):mini.index("\n", mini.index(firma))]
    fino = lambda da, a: mini[mini.index(da):mini.index("\n}\n", mini.index(a)) + 3]
    PEZZI = "\n".join([
        mini[mini.index("const MOSTRO_CHIAVE = "):
             mini.index("/* ---- export CSV degli affari conclusi")],
        riga("const P2P_FINALI = "), riga("const MOSTRO_ORDINI_CHIAVE = "),
        riga("const MOSTRO_LAPIDI_CHIAVE = "), riga("const P2P_LIBRO_FINESTRA_S = "),
        js(mini, "const STATI_P2P = {", "\n};\n"),
        js(mini, "const P2P_PROGRESSO = {", "\n};\n"),
        js(mini, "function ordiniP2P(){"), js(mini, "function scriviOrdineP2P(o){"),
        fino("function nomeProvvisorioP2P(indice){", "function rinominaOrdineP2P(o, nuovoId){"),
        js(mini, "function giroArchiviatoP2P(locali, id){"),
        js(mini, "function rigaDiQuestoMazzoP2P(o, m){"),
        js(mini, "function ordineDiUnAltroMazzoP2P(o, m){"),
        fino("const P2P_DA_RESTORE = {", "function riprendiDaRestoreP2P(o, statoMostro){"),
        fino("function indiceMakerP2P(id, mz, o){", "function riparaChiaveMakerP2P(id, locali){"),
        fino("const P2P_INDICE_CERCA_MAX = ", "function adottaScambiServerP2P(locali){"),
        js(mini, "function presenzeDaServerP2P(p, giro){"), js(mini, "function uniscePresenzeP2P(a, b){"),
        js(mini, "function lapidiP2P(){"), js(mini, "function lapidataP2P(id, giro){"),
        js(mini, "function azioniDisponibili(o){"), js(mini, "function recapitoEuroArrivatoP2P(o){"),
        js(mini, "async function pubblicaEventoSuRelay(relays, evento){"),
        js(mini, "async function firmatarioNsec(nsec){"), js(mini, "function firmatarioEstensione(){"),
    ])
    return PEZZI


BANCO = r"""
const fs = require('fs'), vm = require('vm');
vm.runInThisContext(fs.readFileSync(process.argv[3], 'utf8'));
const dati = JSON.parse(fs.readFileSync(process.argv[2], 'utf-8'));
/* i relay di cartone: uno per url, con gli eventi che il passo prima ha
   lasciato (viaggiano nel JSON fra un dispositivo e l'altro) */
const relayStore = new Map(Object.entries(dati.relay || {}));
const pubblicati = [];
function combacia(f, ev){
  if (f.kinds && f.kinds.indexOf(ev.kind) < 0) return false;
  if (f.authors && f.authors.indexOf(ev.pubkey) < 0) return false;
  if (f['#d'] && !ev.tags.some(t => t[0] === 'd' && f['#d'].indexOf(t[1]) >= 0)) return false;
  return true;
}
class RelayCartone {
  constructor(url){ this.url = url; this.connected = true; }
  static async connect(url){ if (!relayStore.has(url)) relayStore.set(url, []); return new RelayCartone(url); }
  async publish(ev){ pubblicati.push(ev); relayStore.get(this.url).push(ev); return 'ok'; }
  subscribe(filtri, opz){
    const miei = relayStore.get(this.url) || [];
    setTimeout(() => { for (const ev of miei) if (filtri.some(f => combacia(f, ev))) opz.onevent(ev); if (opz.oneose) opz.oneose(); }, 1);
    return {close(){}};
  }
  close(){}
}
const NT = Object.assign({}, NostrTools, {Relay: RelayCartone});
const window = {NostrTools: NT};
const {bytesToHex, hexToBytes} = NT.utils;
/* la memoria del browser: VUOTA, come dopo la chiusura di Tor Browser */
const store = new Map();
const localStorage = {getItem: k => store.has(k) ? store.get(k) : null,
  setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k)};
let tg = null;
let DEMO = false, VETRINA = false, myTgId = dati.tgId;
const API_BASE = '/api';
function authHdr(){ return 'x'; }
const fetches = [];
async function fetch(url, opt){
  fetches.push({url, corpo: opt && opt.body ? JSON.parse(opt.body) : null});
  if (String(url).endsWith('/p2p/seme')) return {ok: false, status: 409};
  if (String(url).endsWith('/p2p/chiavi')) return {ok: true, json: async () => ({ok: true, indice: dati.pavimento || 0})};
  return {ok: true};
}
let toasts = []; function toast(m){ toasts.push(m); }
function haptic(){}
const esc = s => String(s);
const log = []; const console = {log: m => log.push(String(m)), warn: m => log.push(String(m)), error: m => log.push(String(m))};
const nodi = {};
function el(id){ return nodi[id] || (nodi[id] = {id, value: '', innerHTML: '', _c: new Set(),
  classList: {add(c){ nodi[id]._c.add(c); }, remove(c){ nodi[id]._c.delete(c); }, contains(c){ return nodi[id]._c.has(c); }}}); }
function chiudiFoglioP2P(id){ el(id).classList.remove('open'); }
async function caricaNostrTools(){}
function renderProfiloP2P(){} function renderP2P(){}
function suOnion(){ return true; }
let relayCopiaP2P = ['wss://casa.test'];
let pubCasa = '';
/* le finte dell'adozione che qui non servono */
function diarioP2P(){} function rigaLibroP2P(){ return null; }
let p2pMieiOrdini = null, p2pLibro = {ordini: []}, p2pScambiServer = null;
let p2pOrdineAperto = '';
function cauzioneVivaP2P(){ return false; }
/* l'account aperto: la chiave d'accesso del nativo */
const conto = {sk: hexToBytes(dati.contoSk), skHex: dati.contoSk, pub: NT.getPublicKey(hexToBytes(dati.contoSk))};
const nsecInBrowser = dati.modo === 'nsec' ? {[conto.pub]: conto.skHex} : {};
function nsecSalvate(){ return nsecInBrowser; }
async function pubAccount(){ return conto.pub; }
function bunkerCartone(c){
  return {pubkey: async () => c.pub, firma: async ev => NT.finalizeEvent(ev, c.sk),
    cifra44: async (pub, t) => NT.nip44.encrypt(t, NT.nip44.getConversationKey(c.sk, pub)),
    decifra44: async (pub, t) => NT.nip44.decrypt(t, NT.nip44.getConversationKey(c.sk, pub)), chiudi(){}};
}
function nostrCartone(c, con44){
  const n = {getPublicKey: async () => c.pub, signEvent: async ev => NT.finalizeEvent(ev, c.sk)};
  if (con44) n.nip44 = {encrypt: async (pub, t) => NT.nip44.encrypt(t, NT.nip44.getConversationKey(c.sk, pub)),
                        decrypt: async (pub, t) => NT.nip44.decrypt(t, NT.nip44.getConversationKey(c.sk, pub))};
  return n;
}
async function firmatarioAutomatico(){
  if (dati.modo === 'nsec') return {f: await firmatarioNsec(NT.nip19.nsecEncode(conto.sk)), chiudi: true};
  if (dati.modo === 'bunker') return {f: bunkerCartone(conto), chiudi: true};
  if (dati.modo === 'estensione' || dati.modo === 'spento') { window.nostr = nostrCartone(conto, dati.modo === 'estensione'); return {f: firmatarioEstensione(), chiudi: false}; }
  return null;
}
(async () => {
  const out = {};
  if (dati.passo === 'nasce') {
    /* IL DISPOSITIVO 1: il profilo, la copia (se il caso la vuole), la presa */
    let mz = await adottaProfiloContoP2P();
    if (!mz) mz = await assicuraMazzo();
    out.origine = mz.origine; out.conto = numeroConto(mz.conto);
    out.copia = await assicuraCopiaProfiloP2P({gesto: true});
    /* la porta della presa: se apre il foglio, qui si salva il codice
       (il gesto della persona) e la porta si riapre */
    const portaP = garantisciCopiaProfiloP2P(mazzoMostro());
    await new Promise(r => setTimeout(r, 5));
    out.foglio = !!(nodi.p2pCopiaSheet && el('p2pCopiaSheet').classList.contains('open'));
    if (out.foglio) await copiaP2PSalvata();
    out.porta = await portaP;
    /* la presa, come eseguiPresaP2P: l'indice sale, la trade key nasce */
    const indice = (Number(mazzoMostro().indice) || 0) + 1;
    ricordaMazzo(Object.assign({}, mazzoMostro(), {indice}));
    const tk = chiaveScambio(mazzoMostro().sk, indice);
    await registraChiaviP2P([tk.pub]);
    out.mazzoPub = mazzoMostro().pub; out.tradePub = tk.pub; out.indice = indice;
    out.chiaviRegistrate = fetches.filter(f => String(f.url).endsWith('/p2p/chiavi') && f.corpo).map(f => f.corpo.pubkeys);
    out.semeChiesto = fetches.filter(f => String(f.url).endsWith('/p2p/seme')).length;
    out.relay = Object.fromEntries(relayStore);
    out.copie = pubblicati.filter(e => e.kind === 30078).length;
  } else {
    /* IL DISPOSITIVO 2, a memoria vuota: il profilo torna (o no), e la
       riga dell'archivio del server prende le chiavi (o resta da guardare) */
    const mz = await adottaProfiloContoP2P();
    out.profilo = mz ? {pub: mz.pub, origine: mz.origine, copiaRelay: (mz.copiaRelay | 0) > 0} : null;
    out.copiaEsito = p2pCopiaEsito;
    p2pScambiServer = dati.risposta;
    const locali = ordiniP2P();
    adottaScambiServerP2P(locali);
    const o = ordiniP2P()[dati.ordine] || null;
    out.riga = o ? {stato: o.stato, lato: o.lato, soloVista: !!o.soloVista, pubTrade: o.pubTrade || '',
                    indice: o.indice | 0, azione: azioniDisponibili(Object.assign({}, o, {recapitoAltrove: true})),
                    azioneNuda: azioniDisponibili(o)} : null;
    out.semeChiesto = fetches.filter(f => String(f.url).endsWith('/p2p/seme')).length;
  }
  out.log = log.filter(l => l.indexOf('[p2p]') >= 0);
  process.stdout.write(JSON.stringify(out));
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def client(dati):
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="chiavi_ritrovate_")
    try:
        p = os.path.join(cart, "client.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(pezzi_client() + BANCO)
        open(d, "w", encoding="utf-8").write(json.dumps(dati))
        r = subprocess.run([node, p, d, os.path.join(banco.QUI, "vendor", "nostr.bundle.js")],
                           capture_output=True, text=True, timeout=120, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-600:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def cammina_presa(ordine, trade_pub, t):
    """mostrod racconta la presa del nativo (la sua trade key) fino alla
    garanzia pagata: gli stessi eventi del collaudo dei miei scambi."""
    banco.evento(ordine, "taken", t + 10, "buyer", "take", buyer=trade_pub)
    banco.evento(ordine, "buyer-invoice-added", t + 20, "buyer", "hold-next", buyer=trade_pub)
    banco.evento(ordine, "hold-invoice-requested", t + 20, "mostro", "invoice", buyer=trade_pub)
    banco.evento(ordine, "hold-invoice-paid", t + 30, "seller", buyer=trade_pub)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    SRV = banco.SRV
    # LA LEVA ACCESA, PER TUTTI: la registrazione delle chiavi (rotta vera)
    # vuole il P2P attivo — leva, coordinatore e relay — e nessuna lista
    # di prova che tenga fuori il nativo. Il coordinatore e il relay sono
    # di cartone: nessuno li tocca, qui si registra e basta.
    SRV.P2P_ATTIVO = True
    SRV.MOSTRO_HEX = "cd" * 32
    SRV.MOSTRO_RELAY = ["ws://127.0.0.1:9"]
    SRV.P2P_PROVA_IDS = []
    t = int(time.time()) - 600
    # una chiave d'accesso usa-e-getta per caso: nata qui, mai vera
    import secrets
    conti = {c: secrets.token_hex(32) for c in ("nsec", "bunker", "estensione", "spento",
                                                 "nsec-bunker", "bunker-nsec", "estensione-nsec")}
    # una chiave d'accesso valida e' uno scalare: con 64 hex a caso lo e'
    # quasi sempre, e per il resto c'e' il bundle che lo dice; qui basta

    print("\n1) il seme dal server, per un nativo Nostr")
    prova("un nativo Nostr prende 409 dal seme: la strada derivata e' solo di chi entra da Telegram", 409, seme(NATIVO))

    for caso in ("nsec", "bunker", "estensione"):
        print(f"\n2) {caso}: il dispositivo 1 prende, il browser si svuota, il dispositivo 2 riprende")
        ordine = ORD[caso]
        uno = client({"passo": "nasce", "modo": caso, "contoSk": conti[caso], "tgId": NATIVO,
                      "relay": {}, "pavimento": 0})
        prova(f"[{caso}] il client vero gira", None, uno.get("ERRORE"))
        if uno.get("ERRORE"):
            continue
        if caso == "nsec":
            prova("[nsec] il profilo deriva dalla chiave (origine 'conto', col conto negativo), senza chiedere il seme, senza copia sui relay",
                  ["conto", NATIVO, 0, "copia", 1], [uno["origine"], uno["conto"], uno["semeChiesto"], uno["copia"], uno["copie"]])
        else:
            # il seme si chiede due volte: la gamba dell'app e poi il gesto, e
            # tutt'e due prendono il 409
            prova(f"[{caso}] il profilo nasce a caso dopo il 409 del seme, e la copia cifrata va sui relay",
                  ["", 2, "copia", 1], [uno["origine"], uno["semeChiesto"], uno["copia"], uno["copie"]])
        prova(f"[{caso}] la porta della presa passa senza il foglio: il profilo e' coperto",
              [True, False], [uno["porta"], uno["foglio"]])
        # le pubbliche che il client manderebbe vanno alla rotta VERA, come il nativo
        banco.come(NATIVO)
        for pubkeys in uno["chiaviRegistrate"]:
            r = banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
            prova(f"[{caso}] la rotta vera registra le pubbliche del client ({len(pubkeys)})",
                  True, isinstance(r, dict) and r.get("ok", True) is not False or r)
        con = banco.con_db()
        tg_di = con.execute("SELECT tg_id FROM chiavi_p2p WHERE pubkey=?", (uno["tradePub"],)).fetchone()
        con.close()
        prova(f"[{caso}] ...e la trade key e' intestata al nativo", NATIVO, tg_di and tg_di["tg_id"])
        cammina_presa(ordine, uno["tradePub"], t)
        risposta = scambi(NATIVO)
        voce = risposta.get("scambi", {}).get(ordine)
        prova(f"[{caso}] l'archivio del server: la riga del nativo, attiva, con la sua trade key",
              ["attivo", "compro", uno["tradePub"], banco.CHIAVE_VENDE],
              voce and [voce["stato"], voce["lato"], voce["chiave_mia"], voce["chiave_peer"]])
        # IL BROWSER SI SVUOTA: il dispositivo 2, con la stessa chiave d'accesso
        due = client({"passo": "rientra", "modo": caso, "contoSk": conti[caso], "tgId": NATIVO,
                      "relay": uno["relay"], "risposta": risposta.get("scambi", {}), "ordine": ordine,
                      "pavimento": uno["indice"]})
        prova(f"[{caso}] il dispositivo 2 gira", None, due.get("ERRORE"))
        if due.get("ERRORE"):
            continue
        # (12 ott 2026) anche con la nsec torna dalla copia sui relay: una npub, un profilo
        prova(f"[{caso}] lo STESSO profilo torna a memoria vuota, dalla copia sui relay",
              [uno["mazzoPub"], True],
              [due["profilo"] and due["profilo"]["pub"], bool(due["profilo"] and due["profilo"]["copiaRelay"])])
        prova(f"[{caso}] la riga dell'archivio NON e' solo da guardare: la trade key e' ritrovata, i gesti ci sono",
              ["attivo", "compro", False, uno["tradePub"], uno["indice"], "euro-inviati"],
              due["riga"] and [due["riga"]["stato"], due["riga"]["lato"], due["riga"]["soloVista"],
                               due["riga"]["pubTrade"], due["riga"]["indice"], due["riga"]["azione"]])

    print("\n3) i passaggi fra i modi di entrare, stessa npub (12 ott 2026, «chiavi-stesso-profilo»)")
    for da, a in (("nsec", "bunker"), ("bunker", "nsec"), ("estensione", "nsec")):
        ordine = ORD[da + "-" + a]
        chiave = conti[da + "-" + a]
        uno = client({"passo": "nasce", "modo": da, "contoSk": chiave, "tgId": NATIVO, "relay": {}, "pavimento": 0})
        prova(f"[{da}→{a}] il dispositivo 1 ({da}) gira e pubblica la copia", [None, "copia", 1],
              [uno.get("ERRORE"), uno.get("copia"), uno.get("copie")])
        if uno.get("ERRORE"):
            continue
        banco.come(NATIVO)
        for pubkeys in uno["chiaviRegistrate"]:
            banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
        cammina_presa(ordine, uno["tradePub"], t)
        risposta = scambi(NATIVO)
        due = client({"passo": "rientra", "modo": a, "contoSk": chiave, "tgId": NATIVO,
                      "relay": uno["relay"], "risposta": risposta.get("scambi", {}), "ordine": ordine,
                      "pavimento": uno["indice"]})
        prova(f"[{da}→{a}] il dispositivo 2 ({a}) ritrova LO STESSO profilo dalla copia, e la riga ha le chiavi e i gesti",
              [None, uno["mazzoPub"], True, "attivo", False, uno["tradePub"], "euro-inviati"],
              [due.get("ERRORE"), due.get("profilo") and due["profilo"]["pub"],
               bool(due.get("profilo") and due["profilo"]["copiaRelay"]),
               due.get("riga") and due["riga"]["stato"], due.get("riga") and due["riga"]["soloVista"],
               due.get("riga") and due["riga"]["pubTrade"], due.get("riga") and due["riga"]["azione"]])

    print("\n4) il controllo negativo: senza nsec, senza copia, un'estensione che non cifra")
    ordine = ORD["spento"]
    uno = client({"passo": "nasce", "modo": "spento", "contoSk": conti["spento"], "tgId": NATIVO,
                  "relay": {}, "pavimento": 0})
    prova("[spento] il client vero gira", None, uno.get("ERRORE"))
    if not uno.get("ERRORE"):
        prova("[spento] senza un firmatario che cifri non c'e' copia; la porta apre il foglio della rete di sicurezza, e passa solo dopo «L'ho salvato»",
              ["niente", 0, True, True], [uno["copia"], uno["copie"], uno["porta"], uno["foglio"]])
        banco.come(NATIVO)
        for pubkeys in uno["chiaviRegistrate"]:
            banco.esito(SRV.registra_chiavi_p2p, {"pubkeys": pubkeys})
        cammina_presa(ordine, uno["tradePub"], t)
        risposta = scambi(NATIVO)
        due = client({"passo": "rientra", "modo": "spento", "contoSk": conti["spento"], "tgId": NATIVO,
                      "relay": {}, "risposta": risposta.get("scambi", {}), "ordine": ordine,
                      "pavimento": uno["indice"]})
        prova("[spento] il dispositivo 2 gira", None, due.get("ERRORE"))
        if not due.get("ERRORE"):
            prova("[spento] a memoria vuota nessun profilo torna, e la riga resta SOLO DA GUARDARE coi gesti spenti: il caso del campo",
                  [None, "niente", True, "", ""],
                  [due["profilo"], due["copiaEsito"], due["riga"] and due["riga"]["soloVista"],
                   due["riga"] and due["riga"]["azione"], due["riga"] and due["riga"]["azioneNuda"]])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
