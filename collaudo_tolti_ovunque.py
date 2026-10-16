# -*- coding: utf-8 -*-
"""
LA ✕ SU OGNI DISPOSITIVO, COL SERVER VERO E IL CLIENT VERO (7 ott 2026).

Dal campo, richiesta di Andrea: in «I miei scambi» la ✕ toglieva uno
scambio finito dal SOLO dispositivo dove la si premeva. Sugli altri dello
stesso account restava, e l'archivio del server gliela rifaceva nascere.
Adesso la ✕ chiede al server di ricordarlo per l'account
(`/api/p2p/scambi/togli`, tabella `p2p_tolti`: l'id e l'ora), e
l'archivio (`/api/p2p/scambi`) ne manda l'elenco: ogni dispositivo
toglie le sue righe alla prossima lettura.

`prove.py` difende i giudici e il client caso per caso
(`prove_tolti_ovunque`). Qui gira tutto INSIEME e DAVVERO: l'app FastAPI
vera — middleware compresi, la guardia CSRF e la sessione — su
127.0.0.1, e quattro dispositivi dello STESSO account (111) fatti dalle
funzioni vere di miniapp.html in node, ognuno col suo localStorage e le
sue `fetch` vere:
  A  la mini app di Telegram (initData di collaudo nell'intestazione)
  B  il sito col login web (cookie di sessione + Origin, come un browser),
     con la pagina aperta mentre A toglie
  C  un secondo sito col login web, CHIUSO mentre A toglie e riaperto dopo
  D  un dispositivo nuovo, che lo scambio non l'ha mai visto
Si guardano: la ✕ di A che toglie ovunque; lo scambio in corso che il
server rifiuta (409) e il telefono tiene; la rete giu' che non toglie
niente; la riga che vive solo li' (404) che se ne va solo li'; un
estraneo, un id storto, la CSRF da un'altra origine; la leva spenta; un
giro nuovo dopo la ✕ che torna a vedersi; «dimentica il profilo» e la
pulizia dei quaranta giorni.

IL SERVER SENZA UVICORN, ed e' voluto: la CI installa per i collaudi solo
`fastapi httpx anthropic`. Un ponte di libreria standard (`http.server`)
su una porta di 127.0.0.1 passa ogni richiesta, intestazioni comprese,
al `TestClient` dell'app vera — senza lifespan, quindi nessun compito
d'avvio e nessuna rete. Il barattolo dei cookie del TestClient si svuota
a ogni richiesta: i cookie li porta il dispositivo, come un browser.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_tolti_ovunque.py
"""

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse

import collaudo_pagamento_p2p as banco

CONCLUSO = "5a1e0000-7777-4a2b-9c3d-0000000000a1"
APERTO = "5a1e0000-7777-4a2b-9c3d-0000000000b2"
RITIRATO = "5a1e0000-7777-4a2b-9c3d-0000000000c3"
SOLO_QUI = "5a1e0000-7777-4a2b-9c3d-0000000000d4"
IO, ALTRO, ESTRANEO = banco.VENDE, banco.COMPRA, banco.ESTRANEO
CLIENT = None


class Ponte(http.server.BaseHTTPRequestHandler):
    """La richiesta di un dispositivo, passata intera all'app vera."""

    def _passa(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else b""
        h = {k: v for k, v in self.headers.items()
             if k.lower() not in ("content-length", "connection", "accept-encoding")}
        CLIENT.cookies.clear()
        r = CLIENT.request(self.command, self.path, content=corpo, headers=h,
                           follow_redirects=False)
        self.send_response(r.status_code)
        for k, v in r.headers.multi_items():
            if k.lower() not in ("content-length", "transfer-encoding", "connection",
                                 "content-encoding"):
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(r.content)))
        self.end_headers()
        self.wfile.write(r.content)

    do_GET = do_POST = do_DELETE = _passa

    def log_message(self, *a):
        pass


def avvia_ponte():
    global CLIENT
    from fastapi.testclient import TestClient
    CLIENT = TestClient(banco.SRV.app)
    srv = http.server.HTTPServer(("127.0.0.1", 0), Ponte)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def firma_widget(token, dati):
    import hashlib
    import hmac
    controllo = "\n".join(f"{k}={dati[k]}" for k in sorted(dati))
    chiave = hashlib.sha256(token.encode()).digest()
    return hmac.new(chiave, controllo.encode(), hashlib.sha256).hexdigest()


def login_web(chi):
    """Il cookie di sessione del sito: il Login Widget firmato col token di
    cartone, la stessa strada del sito e dell'APK."""
    dati = {"id": str(chi), "first_name": f"U{chi}", "auth_date": str(int(time.time()))}
    dati["hash"] = firma_widget("0:collaudo", dati)
    CLIENT.cookies.clear()
    r = CLIENT.get("/api/login/telegram/ritorno", params={**dati, "da": "/"},
                   follow_redirects=False)
    v = r.cookies.get("barattolo_sessione") or ""
    CLIENT.cookies.clear()
    return v


def semina():
    """Tre scambi di IO raccontati da mostrod con gli eventi veri: un sell
    concluso, uno con la garanzia pagata (in corso), e un suo ordine mai
    preso ritirato col suo «Annulla»."""
    con = banco.con_db()
    adesso = int(time.time())
    for ordine, stato in ((CONCLUSO, "in-progress"), (APERTO, "in-progress"),
                          (RITIRATO, "pending")):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                    "sats,euro,metodi) VALUES(?,?,?,?,'sell',1,30000,'20,00 €','[\"SEPA\"]')",
                    (ordine, IO, adesso - 3600, stato))
    con.commit()
    con.close()
    # dentro la finestra dell'orologio della rotta degli eventi
    t = adesso - 500
    for azione, q, attore, dett in (("taken", 0, "buyer", "take"),
                                    ("buyer-invoice-added", 10, "buyer", "hold-next"),
                                    ("hold-invoice-requested", 10, "mostro", "invoice"),
                                    ("hold-invoice-paid", 20, "seller", None)):
        banco.evento(CONCLUSO, azione, t + q, attore, dett)
        banco.evento(APERTO, azione, t + 100 + q, attore, dett)
    banco.evento(CONCLUSO, "fiat-sent", t + 30, "buyer")
    banco.evento(CONCLUSO, "released", t + 40, "seller", None,
                 sats=30000, sats_buyer=29700, sats_seller=30300)
    banco.evento(CONCLUSO, "success", t + 50, "mostro", None,
                 sats=30000, sats_buyer=29700, sats_seller=30300)
    banco.evento(RITIRATO, "canceled", t + 60, "seller", "pending", buyer=None)


def harness(mini):
    """IL DISPOSITIVO: le funzioni vere di miniapp.html che leggono
    l'archivio, tolgono, adottano e applicano i tolti, in node, con un
    localStorage che vive in un file (uno per dispositivo) e la `fetch`
    vera di node verso il ponte. Una invocazione = una sessione della
    pagina: la memoria (`p2pToltiServer`, l'archivio) vale fra i passi
    della stessa invocazione e riparte da zero alla successiva."""
    def js(firma, fine="\n}\n"):
        i = mini.index(firma)
        return mini[i:mini.index(fine, i) + len(fine)]

    def cost(nome, fine=";\n"):
        i = mini.index("const " + nome + " = ")
        return mini[i:mini.index(fine, i) + len(fine)]

    pezzi = "\n".join(
        [cost(n) for n in ("P2P_FINALI", "P2P_ORIZZONTE_S", "P2P_LAPIDE_TOLTO_S",
                           "P2P_LIBRO_FINESTRA_S", "MOSTRO_LAPIDI_CHIAVE", "P2P_FORMA_ORDINE",
                           "TETTO_TOGLI_P2P_MS", "P2P_DA_RESTORE", "P2P_RESTORE_FERMI",
                           "P2P_RIPRESA_PASSO", "P2P_INDICE_CERCA_MAX", "P2P_INDICE_CERCA_MIN",
                           "P2P_GIRO_APERTO")]
        + [cost("STATI_P2P", "\n};\n"), cost("P2P_PROGRESSO", "\n};\n")]
        + [js(f) for f in ("function ordiniP2P(){", "function scriviOrdineP2P(o){",
                           "function p2pTogliibile(o, adesso){", "function recensioneInSospesoP2P(o){",
                           "function lapidiP2P(){", "function lapideP2P(o){", "function lapidataP2P(id, giro){",
                           "function togliScambioP2P(id, ev){", "function cancellaRigaP2P(id){",
                           "function toltoAltroveP2P(id){", "function applicaToltiP2P(){",
                           "async function togliScambioServerP2P(ordine){",
                           "async function chiediScambiServerP2P(){",
                           # l'ora del server dalla risposta (16 ott 2026, orari-passi)
                           "function prendiOraServerP2P(s){",
                           "function statoDaRestoreP2P(o, statoMostro){",
                           "function fermoDaMomentiP2P(momenti){", "function indiceDaChiaveP2P(mz, pub, max){",
                           "function presenzeDaServerP2P(p, giro){", "function uniscePresenzeP2P(a, b){",
                           "function rigaDaServerP2P(id, s, tk, stato, adesso){",
                           "function chiaveScambioDaServerP2P(mz, id, s){",
                           "function adottaScambiServerP2P(locali){")]
        + [mini[mini.index("function tempoLettura(testo){"):
                mini.index("}\n", mini.index("function tempoLettura(testo){")) + 2],
           js("function p2pRitirato(o){", "\n}") + "\n"])
    return pezzi + r"""
const fs = require('fs');
const [STATO, MODO, BASE, BISCOTTO] = process.argv.slice(2, 6);
const PASSI = process.argv.slice(6);
const _box = fs.existsSync(STATO) ? JSON.parse(fs.readFileSync(STATO, 'utf-8')) : {};
const localStorage = {getItem: k => (k in _box ? _box[k] : null), setItem: (k, v) => { _box[k] = String(v); }};
function chiaveP2P(k){ return k; }
const MOSTRO_ORDINI_CHIAVE = 'barattolo_mostro_ordini';
const DEMO = false, VETRINA = false, myTgId = 111;
const API_BASE = BASE + '/api';
/* la mini app porta l'initData; il sito il cookie, e un browser sulla
   POST mette anche l'Origin: qui li mette la rete del dispositivo */
function authHdr(){ return MODO === 'tg' ? 'collaudo:111:Venditore' : ''; }
const fetchVera = fetch;
let reteGiu = false;
globalThis.fetch = (url, opz) => {
  if (reteGiu && String(url).indexOf('/p2p/scambi/togli') >= 0)
    return Promise.reject(new TypeError('Failed to fetch'));
  const o = Object.assign({}, opz || {});
  o.headers = Object.assign({}, o.headers || {});
  if (MODO === 'web') { o.headers['Cookie'] = 'barattolo_sessione=' + BISCOTTO; o.headers['Origin'] = BASE; }
  return fetchVera(url, o);
};
let p2pOrdineAperto = '', p2pMieiOrdini = null, p2pScambiServer = null, p2pScambiGiro = null, p2pToltiServer = null;
let detti = [], conferma = null;
function toast(m){ detti.push(m); }
function renderP2P(){}
function diarioP2P(){}
function chiediConferma(c){ conferma = c; }
function prendiCambiPubP2P(){}
function mazzoMostro(){ return null; }
function chiaveScambio(){ throw new Error('senza mazzo'); }
const window = {NostrTools: {}};
const log0 = console.log; console.log = () => {};
const foto = () => {
  const t = ordiniP2P(), righe = {};
  for (const k of Object.keys(t)) righe[k] = t[k].stato;
  return {righe: righe, lapidi: Object.keys(lapidiP2P()).sort(), tolti: p2pToltiServer, detti: detti.slice()};
};
(async () => {
  const fuori = [];
  for (const passo of PASSI) {
    detti = []; conferma = null;
    const [cosa, a, b] = passo.split('|');
    try {
      if (cosa === 'leggi') {
        /* quel che fa la pagina: la domanda all'archivio, e al render
           l'adozione e poi i tolti (`scambiP2P`) */
        const ok = await chiediScambiServerP2P();
        adottaScambiServerP2P(ordiniP2P());
        applicaToltiP2P();
        fuori.push(Object.assign({passo: passo, ok: ok}, foto()));
      } else if (cosa === 'togli') {
        togliScambioP2P(a, null);
        if (conferma) await conferma.poi();
        fuori.push(Object.assign({passo: passo, conferma: !!conferma}, foto()));
      } else if (cosa === 'rete') {
        reteGiu = a === 'giu';
        fuori.push({passo: passo});
      } else if (cosa === 'stato') {
        const r = ordiniP2P()[a]; if (r) { r.stato = b; scriviOrdineP2P(r); }
        fuori.push(Object.assign({passo: passo}, foto()));
      } else if (cosa === 'semina') {
        const ora = Math.floor(Date.now() / 1000);
        scriviOrdineP2P({id: a, lato: 'vendo', stato: b, mio: true, euro: 12, metodi: ['SEPA'],
                         creato: ora - 5400, aggiornato: ora - 5000, quando: ora - 5000});
        fuori.push(Object.assign({passo: passo}, foto()));
      }
    } catch(e) { fuori.push({passo: passo, ESPLOSO: String(e && e.stack || e)}); }
  }
  fs.writeFileSync(STATO, JSON.stringify(_box));
  console.log = log0;
  console.log(JSON.stringify(fuori));
})();
"""


def main():
    banco.avvio()
    banco.semina()
    prova = banco.prova
    node = shutil.which("node")
    if not node:
        prova("node c'e'", True, False)
        print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
        return 1
    semina()
    srv, base = avvia_ponte()
    cart = tempfile.mkdtemp(prefix="tolti_")
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    prog = os.path.join(cart, "dispositivo.js")
    open(prog, "w", encoding="utf-8").write(harness(mini))
    biscotti = {"B": login_web(IO), "C": login_web(IO)}
    modi = {"A": "tg", "B": "web", "C": "web", "D": "tg"}

    def dispositivo(nome, *passi):
        r = subprocess.run([node, prog, os.path.join(cart, nome + ".json"), modi[nome], base,
                            biscotti.get(nome, ""), *passi],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return [{"ERRORE": (r.stdout or "")[-300:] + (r.stderr or "")[-600:]}] * len(passi)

    def righe(f):
        """le righe di QUESTI scambi (il banco semina anche i suoi)"""
        if "righe" not in f:
            return f
        return {k: v for k, v in f["righe"].items() if k in (CONCLUSO, APERTO, RITIRATO, SOLO_QUI)}

    def tolti_db(chi=IO):
        con = banco.con_db()
        try:
            return sorted(r[0] for r in con.execute("SELECT ordine FROM p2p_tolti WHERE tg_id=?", (chi,)))
        finally:
            con.close()

    def chiama(metodo, via, corpo=None, intest=None):
        CLIENT.cookies.clear()
        return CLIENT.request(metodo, via, json=corpo, headers=intest or {})

    def archivio(chi):
        """la rotta dell'archivio dalla porta vera, come la vede `chi`
        (mai `banco.come`: sostituirebbe `verifica_utente` per sempre, e
        le richieste vere dopo — sessione, CSRF — direbbero il falso)"""
        r = chiama("POST", "/api/p2p/scambi", None, {"X-Tg-Init-Data": f"collaudo:{chi}:U{chi}"})
        return r.json() if r.status_code == 200 else {"ERRORE": r.status_code}

    tre = {CONCLUSO: "concluso", APERTO: "attivo", RITIRATO: "annullato"}
    try:
        print("\n1) i tre dispositivi leggono l'archivio: tre scambi su ognuno")
        prova("i due cookie del sito sono nati", [True, True],
              [len(biscotti["B"]) > 10, len(biscotti["C"]) > 10])
        a1, = dispositivo("A", "leggi")
        b1, = dispositivo("B", "leggi")
        c1, = dispositivo("C", "leggi")
        prova("A (Telegram) li ha, nati dall'archivio", tre, righe(a1))
        prova("B (il sito) pure", tre, righe(b1))
        prova("C (l'altro sito) pure", tre, righe(c1))

        print("\n2) A toglie il concluso con la ✕")
        a2, = dispositivo("A", "leggi", "togli|" + CONCLUSO)[1:]
        prova("A: via, con la lapide, «Scambio tolto»",
              [{APERTO: "attivo", RITIRATO: "annullato"}, True, ["Scambio tolto"]],
              [righe(a2), CONCLUSO in a2.get("lapidi", []), a2.get("detti")])
        prova("il server lo ricorda per l'account", [CONCLUSO], tolti_db())
        con = banco.con_db()
        q = con.execute("SELECT quando FROM p2p_tolti WHERE tg_id=? AND ordine=?",
                        (IO, CONCLUSO)).fetchone()
        con.close()
        prova("...con l'ora del gesto", True, bool(q) and abs(int(q[0]) - time.time()) < 120)
        v = archivio(IO)
        prova("l'archivio: lo scambio resta fra gli scambi, e c'e' nell'elenco dei tolti",
              [True, [CONCLUSO]], [CONCLUSO in v.get("scambi", {}), v.get("tolti")])
        w = archivio(ALTRO)
        prova("...l'altra parte dello scambio non ne sa niente: lo vede, e nessun tolto",
              ["concluso", []], [w.get("scambi", {}).get(CONCLUSO, {}).get("stato"), w.get("tolti")])

        print("\n3) gli altri dispositivi alla loro lettura")
        b2, = dispositivo("B", "leggi")
        prova("B, con la pagina aperta: alla lettura dopo se ne va, gli altri restano",
              {APERTO: "attivo", RITIRATO: "annullato"}, righe(b2))
        prova("...senza lapide (a non farlo rinascere e' l'elenco), e l'elenco l'ha",
              [False, [CONCLUSO]], [CONCLUSO in b2.get("lapidi", []), b2.get("tolti")])
        c2, = dispositivo("C", "leggi")
        prova("C, chiuso durante la ✕ e riaperto: se ne va alla prima lettura",
              {APERTO: "attivo", RITIRATO: "annullato"}, righe(c2))
        d1, = dispositivo("D", "leggi")
        prova("D, nuovo: non nasce, gli altri due si'",
              {APERTO: "attivo", RITIRATO: "annullato"}, righe(d1))
        a3, = dispositivo("A", "leggi")
        prova("A in una sessione nuova: non torna", {APERTO: "attivo", RITIRATO: "annullato"}, righe(a3))

        print("\n4) lo scambio in corso: il telefono dice finito, il server no (409)")
        a4 = dispositivo("A", "stato|" + APERTO + "|concluso", "togli|" + APERTO)[1]
        prova("la riga RESTA, e si dice perche'", [True, True],
              [APERTO in righe(a4), any("ancora in corso" in d for d in a4.get("detti", []))])
        prova("...e il server non ha scritto niente", [CONCLUSO], tolti_db())

        print("\n5) la rete giu' sulla ✕: niente tolto, da nessuna parte")
        a5 = dispositivo("A", "rete|giu", "togli|" + RITIRATO)[1]
        prova("la riga RESTA, «controlla la connessione»", [True, True],
              [RITIRATO in righe(a5), any("controlla la connessione" in d for d in a5.get("detti", []))])
        prova("...il server non sa niente", [CONCLUSO], tolti_db())
        a6, = dispositivo("A", "togli|" + RITIRATO)
        prova("tornata la rete, la ✕ riesce", [False, ["Scambio tolto"]],
              [RITIRATO in righe(a6), a6.get("detti")])
        prova("...e il server lo ricorda", sorted([CONCLUSO, RITIRATO]), tolti_db())
        b3, = dispositivo("B", "leggi")
        prova("...e B lo toglie alla lettura dopo", {APERTO: "attivo"}, righe(b3))

        print("\n6) la riga che vive solo li': via da li', e il server non ricorda niente")
        a7 = dispositivo("A", "semina|" + SOLO_QUI + "|annullato", "togli|" + SOLO_QUI)[1]
        prova("via da A, «Scambio tolto»", [False, ["Scambio tolto"]],
              [SOLO_QUI in righe(a7), a7.get("detti")])
        prova("...e niente sul server (404)", sorted([CONCLUSO, RITIRATO]), tolti_db())

        print("\n7) la rotta, dalla porta: estraneo, id storto, CSRF, leva spenta")
        tg = {"X-Tg-Init-Data": "collaudo:333:Estraneo"}
        r = chiama("POST", "/api/p2p/scambi/togli", {"ordine": CONCLUSO}, tg)
        prova("l'estraneo: 404 come per un ordine che non esiste, e niente scritto",
              [404, []], [r.status_code, tolti_db(ESTRANEO)])
        io = {"X-Tg-Init-Data": "collaudo:111:Venditore"}
        prova("un id storto e un corpo che non e' un oggetto: 400", [400, 400],
              [chiama("POST", "/api/p2p/scambi/togli", {"ordine": "../x"}, io).status_code,
               chiama("POST", "/api/p2p/scambi/togli", ["x"], io).status_code])
        prova("senza sessione: 401", 401,
              chiama("POST", "/api/p2p/scambi/togli", {"ordine": CONCLUSO}).status_code)
        host = urllib.parse.urlparse(base).netloc
        web = {"Cookie": "barattolo_sessione=" + biscotti["B"], "Host": host}
        prova("col cookie del sito da un'ALTRA origine: 403 (la guardia CSRF)", 403,
              chiama("POST", "/api/p2p/scambi/togli", {"ordine": CONCLUSO},
                     dict(web, Origin="https://altrove.example")).status_code)
        prova("...dalla sua: 200", 200,
              chiama("POST", "/api/p2p/scambi/togli", {"ordine": CONCLUSO},
                     dict(web, Origin="http://" + host)).status_code)
        banco.SRV.P2P_ATTIVO = False
        prova("a leva spenta la ✕ funziona lo stesso", 200,
              chiama("POST", "/api/p2p/scambi/togli", {"ordine": CONCLUSO}, io).status_code)
        banco.SRV.P2P_ATTIVO = True

        print("\n8) un giro nuovo DOPO la ✕ torna a vedersi")
        con = banco.con_db()
        dopo = int(time.time()) + 60
        con.execute("INSERT INTO p2p_momenti(ordine, momento, quando, fonte, giro, attore, dettaglio, "
                    "arrivato) VALUES(?, 'preso', ?, 'mostro', 2, 'buyer', 'take', ?)",
                    (RITIRATO, dopo, dopo))
        con.commit()
        con.close()
        v = archivio(IO)
        prova("l'archivio non lo mette piu' fra i tolti, e lo serve col giro nuovo",
              [[CONCLUSO], True], [v.get("tolti"), RITIRATO in v.get("scambi", {})])
        b4, = dispositivo("B", "leggi")
        prova("...e B, che l'aveva tolto per la ✕ di A, lo rivede: e' un altro scambio",
              "attesa_fattura_compratore", righe(b4).get(RITIRATO))
        con = banco.con_db()
        con.execute("DELETE FROM p2p_momenti WHERE ordine=? AND giro=2", (RITIRATO,))
        con.commit()
        con.close()

        print("\n9) la memoria ha una fine")
        prova("prima di «dimentica» il server ricorda i due tolti", sorted([CONCLUSO, RITIRATO]), tolti_db())
        r = chiama("DELETE", "/api/p2p/chiavi", None, io)
        prova("«Dimentica il profilo» li porta via subito", [200, []], [r.status_code, tolti_db()])
        con = banco.con_db()
        try:
            ora = int(time.time())
            con.execute("INSERT INTO p2p_tolti(tg_id, ordine, quando) VALUES(?,?,?)", (ALTRO, CONCLUSO, ora))
            con.commit()
            banco.SRV._pulisci_memoria_p2p(con, ora + banco.SRV.P2P_LIBRO_MEMORIA_S - 3600)
            prova("la pulizia: prima dei quaranta giorni il tolto resta", [CONCLUSO], tolti_db(ALTRO))
            banco.SRV._pulisci_memoria_p2p(con, ora + banco.SRV.P2P_LIBRO_MEMORIA_S + 3600)
            prova("...dopo, se ne va", [], tolti_db(ALTRO))
        finally:
            con.close()
    finally:
        srv.shutdown()
        shutil.rmtree(cart, ignore_errors=True)

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
