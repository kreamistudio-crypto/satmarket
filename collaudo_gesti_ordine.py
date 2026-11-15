# -*- coding: utf-8 -*-
"""
I GESTI DELL'ORDINE: LA PAGINA VERA CONTRO IL SERVER VERO (13 ott 2026,
cantiere gesti-subito, richiesta di Andrea).

Un gesto dell'ordine (segna come spedito, consegna a mano, reso, disputa,
feedback, incasso…) finisce con la pagina che si ridisegna. E la pagina
si ridisegna dalla riga della LISTA degli ordini: se la lista si e'
riletta mentre l'ordine era aperto, quel che il gesto scriveva sulla
copia aperta non si vedeva — il toast diceva «fatto» e il bottone era
ancora li'. Dal 13 ott ogni gesto scrive con un attrezzo solo
(`segnaOrdine`), sull'ordine aperto E sulla sua riga viva.

`prove.py` fa girare i gesti contro un server DI CARTONE che risponde
quel che gli si dice. Quello che non puo' dire e' se quel che la pagina
scrive e' quel che il server VERO ha fatto. Qui si': le funzioni vere di
miniapp.html girano in node, con la `fetch` vera, contro le rotte vere
(un ponte di libreria standard verso il TestClient: in CI non c'e'
uvicorn). Per ogni gesto la pagina apre l'ordine, la lista si RILEGGE
(la copia aperta diventa quella di prima: il caso che era rotto), parte
il gesto, e si guarda:

  - la riga della lista e il ridisegno portano il fatto nuovo;
  - e' lo STESSO fatto che il server dice a una rilettura fresca;
  - il database e' dove deve essere (lo stato, il corriere, il voto…).

In fila, sugli stessi ordini come capita davvero: spedito → disputa →
decisione del moderatore (reso) → reso spedito → reso ricevuto → il
rimborso che parte con l'indirizzo Lightning; consegna a mano; conferma
di ricezione → fattura d'incasso → feedback; conferma che paga subito;
indirizzo Lightning che sblocca un incasso; codice di ritiro; punto di
ritiro; scelta della consegna dopo un'asta.

E L'APPUNTAMENTO DI UN SERVIZIO, il caso da cui e' nata la regola del
server: chi compra guarda GIOVEDI', chi vende nel frattempo propone
VENERDI', chi compra tocca «Confermo, ci sono». Prima restava confermato
venerdi', una data mai vista. Adesso col tocco viaggia la data che si ha
davanti: il server rifiuta (409), la pagina rilegge, mostra venerdi' e
chiede «La data è cambiata: confermi questa?».

In coda le FERIE: la frase giusta per l'asta vinta in attesa della
scelta della consegna, e per le altre strade.

E I DUE CASI DEL SECONDO PUSH (13 ott 2026), quelli che toccano i soldi
come li vede chi usa l'app:
  - L'INCASSO E' DI UN ALTRO ORDINE. Chi vende ha due ordini: uno appena
    pagato da chi compra (da spedire) e uno confermato che aspetta
    l'incasso. Apre il PRIMO e li' scrive il suo indirizzo Lightning: il
    server paga il secondo. Prima la pagina segnava «incassato» l'ordine
    APERTO — quello ancora da spedire. Adesso rilegge: incassato e' solo
    quello che il server ha pagato davvero.
  - UN ALTRO ORDINE APERTO MENTRE LA RICHIESTA VIAGGIA. «Segna come
    spedito» su un ordine, e prima che il server risponda se ne apre un
    altro: il fatto va sull'ordine del gesto (quello che il server ha
    spedito davvero), l'altro non si tocca, e nessuno viene riportato
    indietro.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (database usa-e-getta), i pagamenti sono
controfigure con la firma del vero, niente rete, niente chiavi.

USO:  python collaudo_gesti_ordine.py
"""

import http.server
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
CLIENT = None
DETTO = []
COMPRA, VENDE, VENDE2, VENDE3, ADMIN = 111, 222, 333, 444, 999


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server, e le controfigure dei
    pagamenti con la firma del vero."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-gesti-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [ADMIN]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.SERVIZI_ATTIVI = True
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        return {"payment_hash": f"hash{int(time.time() * 1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    # la FIRMA del vero, parola per parola (`cassaforte` solo per nome,
    # `riga` dal 19 set 2026): un doppio con una firma sua esplode al
    # primo parametro nuovo
    async def paga_finto(bolt11, atteso_sats, diario=None, *, cassaforte,
                         riga=()):
        return SRV.PAGATO

    async def invoice_da_address(addr, sats):
        return f"lnbc{sats}address"

    # la fattura di cartone dice il suo importo nel nome: «lnbc50000collaudo»
    async def importo_finto(bolt11, dec=None, *a, **k):
        cifre = "".join(ch for ch in bolt11[4:] if ch.isdigit())
        return int(cifre) if cifre else None

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.paga_venditore = paga_finto
    server.invoice_da_ln_address = invoice_da_address
    server.importo_invoice = importo_finto
    server.rifiuto_scadenza = lambda bolt11, adesso=None: ""
    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.notifica_admin = zitto
    return db


class Ponte(http.server.BaseHTTPRequestHandler):
    """La richiesta della pagina, passata intera all'app vera."""

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
    CLIENT = TestClient(SRV.app)
    srv = http.server.HTTPServer(("127.0.0.1", 0), Ponte)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def chiedi(chi, percorso, corpo=None, metodo="POST", grezzo=None):
    """Una richiesta diretta alle rotte vere, con l'identita' di collaudo
    di `chi`: (codice, corpo della risposta)."""
    CLIENT.cookies.clear()
    h = {"X-Tg-Init-Data": f"collaudo:{chi}:U{chi}"}
    if grezzo is not None:
        r = CLIENT.request(metodo, percorso, content=grezzo,
                           headers={**h, "Content-Type": "application/json"})
    elif corpo is not None:
        r = CLIENT.request(metodo, percorso, json=corpo, headers=h)
    else:
        r = CLIENT.request(metodo, percorso, headers=h)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, None


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o) if o else {}


def scrivi(tabella, chiave, valore, **campi):
    con = SRV.db()
    con.execute(f"UPDATE {tabella} SET "
                + ", ".join(f"{k}=?" for k in campi) + f" WHERE {chiave}=?",
                tuple(campi.values()) + (valore,))
    con.commit()
    con.close()


def semina():
    con = SRV.db()
    for tg, nome in ((COMPRA, "Compra"), (VENDE, "Vende"), (VENDE2, "Vende2"),
                     (VENDE3, "Vende3"), (ADMIN, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                    "ln_address) VALUES(?,?,?,1,'')", (tg, nome, f"neg{tg}"))
    con.commit()
    con.close()


def ordine(titolo, strada, stato, vende=VENDE, annuncio=None, **campi):
    """Un affare gia' pagato, scritto dritto nel database: l'annuncio
    (venduto) e la sua riga d'ordine nello stato che serve. Come ci si
    arriva camminando lo provano gli altri collaudi; qui serve il punto
    di partenza del gesto."""
    con = SRV.db()
    adesso = int(time.time())
    ann = {"venditore_id": vende, "titolo": titolo, "descrizione": "una cosa vera",
           "prezzo_sats": 50000, "categoria": "Altro", "zona": "Pavia (PV)",
           "stato": "venduto", "creato": adesso - 7200,
           "consegna": strada or "entrambe", "foto": "[]"}
    ann.update(annuncio or {})
    aid = con.execute(
        f"INSERT INTO annunci({','.join(ann)}) VALUES({','.join('?' * len(ann))})",
        tuple(ann.values())).lastrowid
    o = {"annuncio_id": aid, "compratore_id": COMPRA, "venditore_id": vende,
         "prezzo_sats": 50000, "stato": stato, "payment_hash": f"hash{aid}",
         "creato": adesso - 3600, "aggiornato": adesso - 3600,
         "consegna_scelta": strada}
    o.update(campi)
    oid = con.execute(
        f"INSERT INTO ordini({','.join(o)}) VALUES({','.join('?' * len(o))})",
        tuple(o.values())).lastrowid
    con.commit()
    con.close()
    return oid


GESTI = ("async function inviaFeedback(btn){", "async function saveLnAddress(btn){",
         "async function saveSellerInvoice(btn){", "async function confirmReceived(btn){",
         "async function inviaSpedito(corriere, tracking, bustaDiretta){",
         "async function markConsegnaMano(){", "async function depositaBusta(btn){",
         "async function resoSpedito(){", "async function resoRicevuto(btn){",
         "async function openDispute(){", "async function adminResolve(esito, btn){",
         "async function scegliConsegnaOrdine(v){", "async function salvaPuntoRitiro(){",
         "async function proponiAppuntamento(btn){", "async function confermaAppuntamento(btn){",
         "async function depositaAccesso(btn){")


def harness(mini):
    """LA PAGINA: le funzioni vere di miniapp.html — la lista degli
    ordini, l'attrezzo, i sedici gesti, il riquadro dell'appuntamento —
    in node, con la `fetch` vera verso il ponte. Di cartone c'e' solo
    quel che non c'entra: il toast, la domanda di conferma (dice si'),
    i campi (portano il valore che il copione gli da'), e il ridisegno,
    che come quello vero riparte dalla riga della lista."""
    mini = mini.replace("\r\n", "\n")

    def js(firma, fine="\n}\n"):
        i = mini.index(firma)
        return mini[i:mini.index(fine, i) + len(fine)]

    def riga_js(inizio):
        i = mini.index(inizio)
        return mini[i:mini.index("\n", i)] + "\n"

    nomi = [f.split("function ")[1].split("(")[0] for f in GESTI]
    return r"""
const fs = require('fs');
const COPIONE = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let IO = 0, myTgId = 0;
const API_BASE = COPIONE.base + '/api';
function authHdr(){ return 'collaudo:' + IO + ':U' + IO; }
let DEMO = false, VETRINA = false;
function haptic(){}
const detti = [];
function toast(t){ detti.push(t); }
function bottoneInAttesa(){ return () => {}; }
function attesaRitardata(){ return () => {}; }
const NODI = {};
function el(id){ return NODI[id] || null; }
let ATTESE = [];
function chiediConferma(c){ ATTESE.push(c.poi()); }
const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
let currentOrder = null, orders = [];
const aperti = [];
/* il ridisegno, come quello vero: riparte dalla riga della lista */
function openOrder(id){ currentOrder = orders.find(o=>o.id===id);
  aperti.push(currentOrder ? JSON.parse(JSON.stringify(currentOrder)) : null); }
/* la lista ridisegnata: si conta */
let liste = 0;
function renderOrders(){ liste++; }
function trackingDaControllare(){ return true; }
let stellaScelta = 0, fbFoto = [], myLnAddress = '', bustaDoc = null, bustaLetta = {}, bustaDocVisto = {};
/* gli on-chain da pagare (27 ott 2026): qui l'on-chain e' spento */
let myOnchain = false;
/* le vendite della cassa in negozio (15 nov 2026): qui la cassa e' spenta */
let cassaAttiva = false;
""" + js("function mapOrder(o){") + js("async function loadOrders(ordine){") \
        + riga_js("let ordiniOnchainDaPagare = [];") \
        + js("async function caricaOnchainDaPagare(){") \
        + riga_js("let ordiniCassa = [];") \
        + js("async function caricaCassaOrdini(){") \
        + js("function segnaOrdine(o, campi){") + js("function ridisegnaOrdine(o){") \
        + riga_js("let appuntamentoCambiato = ") + js("function dataAppuntamento(ts){") \
        + js("function pannelloServizioCompratore(o){") + "".join(js(f) for f in GESTI) \
        + js("function testoFinestraFeedback(giorni, genere){") \
        + "const GESTI = {" + ", ".join(nomi) + "};\n" + r"""
const copia = x => (x === undefined ? null : JSON.parse(JSON.stringify(x)));
(async () => {
  const fuori = [];
  let aperta = null;
  for (const p of COPIONE.passi) {
    if (p.io) { IO = p.io; myTgId = p.io; }
    if (p.fa === 'carica') await loadOrders();
    else if (p.fa === 'apri') { currentOrder = orders.find(o => o.id === p.ordine); aperta = currentOrder; }
    else if (p.fa === 'chiama') {
      /* un ALTRO telefono (un'altra identita'), dritto sulla rotta */
      const r = await fetch(COPIONE.base + p.percorso, {method: 'POST',
        headers: {'X-Tg-Init-Data': 'collaudo:' + p.come + ':U' + p.come, 'Content-Type': 'application/json'},
        body: JSON.stringify(p.corpo || {})});
      fuori.push({stato: r.status, corpo: await r.json().catch(() => null)});
    }
    else if (p.fa === 'gesto') {
      for (const k of Object.keys(NODI)) delete NODI[k];
      for (const k of Object.keys(p.nodi || {})) NODI[k] = {value: p.nodi[k]};
      stellaScelta = p.stelle || 0;
      ATTESE = [];
      /* ALTROVE: appena il server ha risposto alla richiesta del gesto — e
         prima che il gesto riprenda — chi usa l'app ha gia' aperto un ALTRO
         ordine. La `fetch` resta quella vera. */
      if (p.altrove) {
        const vera = globalThis.fetch;
        globalThis.fetch = async (...a) => {
          const r = await vera(...a);
          globalThis.fetch = vera;
          currentOrder = orders.find(o => o.id === p.altrove);
          return r;
        };
      }
      const arg = p.bottone !== undefined ? [{dataset: {quando: String(p.bottone)}}] : (p.arg || [{}]);
      await GESTI[p.nome](...arg);
      await Promise.all(ATTESE);
    }
    else if (p.fa === 'leggi') {
      const riga = orders.find(o => o.id === p.ordine);
      fuori.push({riga: copia(riga), aperta: copia(aperta), staccata: aperta !== riga,
                  visto: aperti.length ? aperti[aperti.length - 1] : null, ridisegni: aperti.length,
                  detti: detti.splice(0), cambiata: copia(appuntamentoCambiato[p.ordine]),
                  riquadro: p.riquadro && riga ? pannelloServizioCompratore(riga) : null,
                  data: p.data ? dataAppuntamento(p.data) : null,
                  altra: p.altra ? copia(orders.find(o => o.id === p.altra)) : null,
                  aSchermo: currentOrder ? currentOrder.id : null, liste: liste});
      aperti.length = 0; liste = 0;
    }
  }
  console.log(JSON.stringify(fuori));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


def main():
    print("=" * 60)
    print("  I GESTI DELL'ORDINE — la pagina vera contro il server vero")
    print("=" * 60)
    avvio()
    node = shutil.which("node")
    if not node:
        prova("node c'e'", True, False)
        print(f"\n{PASSATE} ok, {FALLITE} NO")
        return 1
    semina()
    srv, base = avvia_ponte()
    cart = tempfile.mkdtemp(prefix="gesti_")
    prog = os.path.join(cart, "pagina.js")
    with open(prog, "w", encoding="utf-8") as f:
        f.write(harness(open(os.path.join(QUI, "miniapp.html"), encoding="utf-8").read()))
    giri = [0]

    def pagina(*passi):
        """Una sessione della pagina: i passi del copione, in fila, nello
        stesso node (la memoria della pagina vale fra un passo e l'altro)."""
        giri[0] += 1
        cop = os.path.join(cart, f"copione{giri[0]}.json")
        with open(cop, "w", encoding="utf-8") as f:
            json.dump({"base": base, "passi": list(passi)}, f)
        r = subprocess.run([node, prog, cop], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            raise SystemExit("⚠️  la pagina in node e' esplosa:\n"
                             + (r.stdout or "")[-400:] + (r.stderr or "")[-1200:])

    def gesto(chi, oid, nome, campi, parole, stato_db=None, *, arg=None, nodi=None,
              stelle=0, titolo="", rilegge=False):
        """UN GESTO, dal caso che era rotto: la pagina di `chi` apre
        l'ordine, la lista si RILEGGE (la copia aperta diventa quella di
        prima), parte il gesto. Poi una rilettura fresca dice la verita'
        del server."""
        dopo, vera = pagina(
            {"fa": "carica", "io": chi}, {"fa": "apri", "ordine": oid}, {"fa": "carica"},
            {"fa": "gesto", "nome": nome, "arg": arg, "nodi": nodi, "stelle": stelle},
            {"fa": "leggi", "ordine": oid}, {"fa": "carica"}, {"fa": "leggi", "ordine": oid})
        # `rilegge` (l'indirizzo Lightning, dal secondo push): il gesto non
        # scrive niente a mano, rilegge gli ordini — la copia di prima non la
        # tocca nessuno, e non serve: il ridisegno riparte dalla lista nuova
        prova(f"{titolo or nome}: la pagina aveva la copia di PRIMA; dopo il gesto la riga "
              f"della lista, la copia e il ridisegno (uno) dicono il fatto, con le parole di sempre",
              [True, campi, campi, campi, 1, parole],
              [dopo["staccata"], {k: (dopo["riga"] or {}).get(k) for k in campi},
               campi if rilegge else {k: (dopo["aperta"] or {}).get(k) for k in campi},
               {k: (dopo["visto"] or {}).get(k) for k in campi}, dopo["ridisegni"],
               dopo["detti"]])
        prova("...ed e' quel che il server dice a una rilettura fresca",
              campi, {k: (vera["riga"] or {}).get(k) for k in campi})
        if stato_db is not None:
            prova("...e il database e' li'", stato_db,
                  {k: riga(oid).get(k) for k in stato_db})
        return dopo, vera

    try:
        # =========== 1) SPEDITO → DISPUTA → MODERATORE → RESO ===========
        print("\n[1. segna come spedito, disputa, decisione del moderatore, reso]")
        o1 = ordine("Lampada da tavolo", "spedizione", "locked")
        gesto(VENDE, o1, "inviaSpedito",
              {"state": "shipped", "corriere": "Poste Italiane", "tracking": "AB123456789IT"},
              ["📦 Segnato come spedito"],
              {"stato": "shipped", "corriere": "Poste Italiane", "tracking": "AB123456789IT"},
              arg=["Poste Italiane", "AB123456789IT", False], titolo="«SEGNA COME SPEDITO»")
        gesto(COMPRA, o1, "openDispute", {"state": "dispute"},
              ["⚠️ Disputa aperta, ti contatterà un moderatore"], {"stato": "dispute"},
              titolo="LA DISPUTA")
        gesto(ADMIN, o1, "adminResolve", {"state": "return_pending"},
              ["📦 Deciso: rimborso previa restituzione"], {"stato": "return_pending"},
              arg=["reso", {}], titolo="LA DECISIONE DEL MODERATORE (reso)")
        gesto(COMPRA, o1, "resoSpedito",
              {"state": "return_shipped", "corriereReso": "Poste Italiane",
               "trackingReso": "RR123456789IT"},
              ["↩️ Reso registrato: rimborso alla consegna"],
              {"stato": "return_shipped", "corriere_reso": "Poste Italiane",
               "tracking_reso": "RR123456789IT"},
              nodi={"resoCorriere": "Poste Italiane", "resoTracking": " RR123456789IT "},
              titolo="IL RESO SPEDITO")
        gesto(VENDE, o1, "resoRicevuto", {"state": "refund"},
              ["↩️ Registrato: rimborso in attesa del metodo dell'acquirente"],
              {"stato": "refund"}, titolo="IL RESO RICEVUTO (chi compra non ha un metodo)")
        gesto(COMPRA, o1, "saveLnAddress", {"state": "refunded"},
              ["↩️ Rimborso in arrivo! ⚡"], {"stato": "refunded"},
              nodi={"lnAddrInput": "compra@wallet.example"}, rilegge=True,
              titolo="L'INDIRIZZO LIGHTNING che fa partire il rimborso")

        # =========== 2) LA CONSEGNA A MANO ===========
        print("\n[2. la consegna a mano]")
        o2 = ordine("Bicicletta", "ritiro", "locked")
        gesto(VENDE, o2, "markConsegnaMano",
              {"state": "shipped", "corriere": "Ritiro in zona"},
              ["🤝 Consegna a mano registrata"],
              {"stato": "shipped", "corriere": "Ritiro in zona"}, titolo="LA CONSEGNA A MANO")

        # =========== 3) CONFERMA → FATTURA → FEEDBACK ===========
        print("\n[3. conferma di ricezione, fattura d'incasso, feedback]")
        o3 = ordine("Libro raro", "spedizione", "shipped", corriere="Poste Italiane",
                    tracking="AB123456789IT", spedito_il=int(time.time()) - 86400)
        gesto(COMPRA, o3, "confirmReceived", {"state": "confirmed"},
              ["✅ Confermato! Ora tocca a Barattolo: i sats partono appena il venditore ci "
               "dice dove riceverli"], {"stato": "confirmed"},
              titolo="LA CONFERMA DI RICEZIONE (chi vende non ha un metodo d'incasso)")
        gesto(VENDE, o3, "saveSellerInvoice", {"state": "released"},
              ["🔓 Sats incassati! Affare concluso ⚡"], {"stato": "released"},
              nodi={"sellerInvoice": "lnbc50000collaudo"}, titolo="LA FATTURA D'INCASSO")
        gesto(COMPRA, o3, "inviaFeedback",
              {"mioVoto": 5, "mioCommento": "tutto bene", "mioFoto": []},
              ["⭐ Grazie per il feedback!"], None,
              nodi={"fbCommento": "  tutto bene  "}, stelle=5, titolo="IL FEEDBACK")
        con = SRV.db()
        voti = con.execute("SELECT da_tg_id, voto FROM feedback WHERE ordine_id=?",
                           (o3,)).fetchall()
        con.close()
        prova("...e il voto e' nel database, uno solo", [(COMPRA, 5)],
              [tuple(v) for v in voti])

        # =========== 4) I DUE INCASSI CHE PARTONO DA SOLI ===========
        print("\n[4. la conferma che paga subito, e l'indirizzo che sblocca un incasso]")
        # chi vende (333) ha gia' l'indirizzo: la conferma paga subito
        scrivi("utenti", "tg_id", VENDE2, ln_address="vende2@wallet.example")
        o4 = ordine("Cuffie", "spedizione", "shipped", vende=VENDE2, corriere="Poste Italiane",
                    tracking="AB123456789IT", spedito_il=int(time.time()) - 86400)
        gesto(COMPRA, o4, "confirmReceived", {"state": "released"},
              ["🔓 Sats sbloccati al venditore!"], {"stato": "released"},
              titolo="LA CONFERMA DI RICEZIONE che paga subito")
        # chi vende (222) non ce l'ha: l'ordine confermato aspetta, e l'indirizzo lo sblocca
        o5 = ordine("Zaino", "spedizione", "confirmed", corriere="Poste Italiane",
                    tracking="AB123456789IT", spedito_il=int(time.time()) - 86400,
                    consegnato=int(time.time()) - 3600)
        gesto(VENDE, o5, "saveLnAddress", {"state": "released"},
              ["🔓 Sats incassati automaticamente! ⚡"], {"stato": "released"},
              nodi={"lnAddrInput": "vende@wallet.example"}, rilegge=True,
              titolo="L'INDIRIZZO LIGHTNING che sblocca un incasso")
        scrivi("utenti", "tg_id", VENDE, ln_address="")

        # =========== 5) IL PUNTO DI RITIRO E IL SUO CODICE ===========
        print("\n[5. il punto di ritiro, il codice di ritiro]")
        o6 = ordine("Scarpe", "spedizione", "locked", via_punto=1)
        gesto(COMPRA, o6, "salvaPuntoRitiro", {"puntoRitiro": "Locker InPost Via Roma 1"},
              ["📦 Punto salvato: il venditore lo vede nell'ordine"],
              {"punto_ritiro": "Locker InPost Via Roma 1"},
              nodi={"puntoRitiroInp": "  Locker InPost Via Roma 1  "},
              titolo="IL PUNTO DI RITIRO")
        dopo, vera = pagina(
            {"fa": "carica", "io": VENDE}, {"fa": "apri", "ordine": o6}, {"fa": "carica"},
            {"fa": "gesto", "nome": "depositaBusta",
             "nodi": {"bustaNome": " Mario Rossi ", "bustaCodice": " AB12CD "}},
            {"fa": "leggi", "ordine": o6}, {"fa": "carica"}, {"fa": "leggi", "ordine": o6})
        prova("IL CODICE DI RITIRO: la copia era di prima; la riga, la copia e il ridisegno "
              "dicono che la busta c'e', con l'ora che dice il server",
              [True, True, True, True, 1, ["📦 Istruzioni depositate"]],
              [dopo["staccata"], dopo["riga"]["bustaIl"] > 0,
               dopo["aperta"]["bustaIl"] == dopo["riga"]["bustaIl"],
               (dopo["visto"] or {}).get("bustaIl") == dopo["riga"]["bustaIl"],
               dopo["ridisegni"], dopo["detti"]])
        prova("...ed e' quel che il server dice a una rilettura fresca, e sta nel database",
              [dopo["riga"]["bustaIl"], dopo["riga"]["bustaCorrezioni"], True],
              [vera["riga"]["bustaIl"], vera["riga"]["bustaCorrezioni"],
               riga(o6).get("busta_il") == dopo["riga"]["bustaIl"]])

        # =========== 6) LA SCELTA DELLA CONSEGNA DOPO UN'ASTA ===========
        print("\n[6. la scelta della consegna dopo un'asta]")
        o7 = ordine("Quadro a olio", "", "locked",
                    annuncio={"consegna": "entrambe", "asta_base_sats": 1000,
                              "asta_scadenza": int(time.time()) - 3600})
        gesto(COMPRA, o7, "scegliConsegnaOrdine", {"consegnaScelta": "ritiro"},
              ["✔ Scelta fatta: il venditore prepara la consegna"],
              {"consegna_scelta": "ritiro"}, arg=["ritiro"],
              titolo="LA SCELTA DELLA CONSEGNA DOPO UN'ASTA")

        # =========== 7) L'APPUNTAMENTO: GIOVEDI' VISTO, VENERDI' PROPOSTO ===========
        print("\n[7. l'appuntamento: giovedi' visto, venerdi' proposto nel frattempo]")
        o8 = ordine("Lezione di inglese", "servizio", "locked")
        # il prossimo GIOVEDI' alle 15:30 (nell'ora di questa macchina, che e'
        # anche quella del node che fa la pagina) e il VENERDI' dopo
        import datetime as _dt
        g = _dt.datetime.now().replace(hour=15, minute=30, second=0,
                                       microsecond=0) + _dt.timedelta(days=1)
        while g.weekday() != 3:
            g += _dt.timedelta(days=1)
        GIO, VEN = int(g.timestamp()), int((g + _dt.timedelta(days=1)).timestamp())
        c, _ = chiedi(VENDE, f"/api/orders/{o8}/appuntamento", {"quando": GIO})
        prova("chi vende propone giovedi'", [200, GIO, 0],
              [c, riga(o8)["appuntamento_il"], riga(o8)["appuntamento_confermato_il"]])
        v = pagina(
            {"fa": "carica", "io": COMPRA}, {"fa": "apri", "ordine": o8},
            {"fa": "leggi", "ordine": o8, "riquadro": True, "data": GIO},
            # ...e mentre chi compra guarda giovedi', chi vende propone venerdi'
            {"fa": "chiama", "come": VENDE, "percorso": f"/api/orders/{o8}/appuntamento",
             "corpo": {"quando": VEN}},
            {"fa": "gesto", "nome": "confermaAppuntamento", "bottone": GIO},
            {"fa": "leggi", "ordine": o8, "riquadro": True, "data": VEN},
            {"fa": "gesto", "nome": "confermaAppuntamento", "bottone": VEN},
            {"fa": "leggi", "ordine": o8, "riquadro": True, "data": VEN})
        prima, proposta, cambiata, confermata = v
        prova("le due date sono proprio un giovedi' e il venerdi' dopo, come le scrive la pagina",
              [True, True],
              [prima["data"].startswith("giovedì"), cambiata["data"].startswith("venerdì")])
        prova("chi compra guarda GIOVEDI': la proposta, e un bottone che porta giovedi'",
              [True, True],
              [f"Il venditore propone <b>{prima['data']}</b>" in prima["riquadro"],
               f'data-quando="{GIO}" onclick="confermaAppuntamento(this)">✅ Confermo, ci sono</button>'
               in prima["riquadro"]])
        prova("...nel frattempo chi vende propone VENERDI' (dal suo telefono)",
              [200, False], [proposta["stato"], (proposta["corpo"] or {}).get("confermato")])
        # (il database a meta' sessione non si puo' leggere da qui: lo dice la
        # riga che la pagina ha appena RILETTO dal server, e piu' sotto
        # l'avviso a chi vende — uno solo, per venerdi')
        prova("IL TOCCO SU «CONFERMO, CI SONO» CON GIOVEDI' DAVANTI: il server RIFIUTA. La "
              "pagina rilegge: la riga e il ridisegno (uno) dicono venerdi', NON "
              "confermato, e ricorda che si stava confermando giovedi'",
              [VEN, 0, VEN, 1, GIO, ["📅 La data è cambiata: guarda quella nuova"]],
              [cambiata["riga"]["appuntamentoIl"], cambiata["riga"]["appuntamentoConfermatoIl"],
               (cambiata["visto"] or {}).get("appuntamentoIl"), cambiata["ridisegni"],
               cambiata["cambiata"], cambiata["detti"]])
        prova("...e il riquadro CHIEDE: «La data è cambiata: confermi questa?», con venerdi', "
              "e un bottone che porta venerdi'",
              [True, True, False],
              [f"<b>La data è cambiata: confermi questa?</b> Il venditore ora propone "
               f"<b>{cambiata['data']}</b>." in cambiata["riquadro"],
               f'data-quando="{VEN}" onclick="confermaAppuntamento(this)">✅ Confermo, ci sono</button>'
               in cambiata["riquadro"],
               "— confermato." in cambiata["riquadro"]])
        r8 = riga(o8)
        prova("chi compra conferma VENERDI': adesso si', sul database e nella pagina",
              [VEN, True, True, True, ["✅ Appuntamento confermato"], None],
              [r8["appuntamento_il"], r8["appuntamento_confermato_il"] > 0,
               confermata["riga"]["appuntamentoConfermatoIl"] > 0,
               f"<b>{confermata['data']}</b> — confermato." in confermata["riquadro"],
               confermata["detti"], confermata["cambiata"]])
        prova("...a chi vende arriva UN SOLO avviso di conferma, e dice venerdi': il tocco su "
              "giovedi' non ha confermato niente",
              [1, True, False],
              [sum(1 for chi, t in DETTO if chi == VENDE and "Appuntamento confermato" in t),
               any(chi == VENDE and "Appuntamento confermato" in t
                   and SRV._quando_appuntamento(VEN) in t for chi, t in DETTO),
               any(chi == VENDE and "Appuntamento confermato" in t
                   and SRV._quando_appuntamento(GIO) in t for chi, t in DETTO)])
        # le rotte, dritte: la data sbagliata, la giusta, il corpo che manca o e' rotto
        o9 = ordine("Lezione di chitarra", "servizio", "locked")
        chiedi(VENDE, f"/api/orders/{o9}/appuntamento", {"quando": GIO})
        c, d = chiedi(COMPRA, f"/api/orders/{o9}/appuntamento/conferma", {"quando": VEN})
        prova("LA ROTTA: una data che non e' quella dell'ordine → 409, e non conferma niente",
              [409, "La data è cambiata mentre confermavi: guarda quella nuova", 0],
              [c, (d or {}).get("detail"), riga(o9)["appuntamento_confermato_il"]])
        c, d = chiedi(COMPRA, f"/api/orders/{o9}/appuntamento/conferma", {"quando": GIO})
        prova("...la data giusta → confermato", [200, GIO, True],
              [c, (d or {}).get("quando"), riga(o9)["appuntamento_confermato_il"] > 0])
        c, d = chiedi(COMPRA, f"/api/orders/{o9}/appuntamento/conferma", {"quando": GIO})
        prova("...confermare due volte la stessa non e' un errore", [200, GIO],
              [c, (d or {}).get("quando")])
        c, d = chiedi(COMPRA, f"/api/orders/{o9}/appuntamento/conferma", {"quando": VEN})
        prova("...ma a conferma data, una data DIVERSA resta un 409 (non «riconferma» per "
              "sbaglio)", 409, c)
        o10 = ordine("Lezione di piano", "servizio", "locked")
        chiedi(VENDE, f"/api/orders/{o10}/appuntamento", {"quando": GIO})
        c, _ = chiedi(COMPRA, f"/api/orders/{o10}/appuntamento/conferma")
        prova("...un client di ieri non manda il corpo: vale come ieri, conferma",
              [200, True], [c, riga(o10)["appuntamento_confermato_il"] > 0])
        o11 = ordine("Lezione di canto", "servizio", "locked")
        chiedi(VENDE, f"/api/orders/{o11}/appuntamento", {"quando": GIO})
        c, _ = chiedi(COMPRA, f"/api/orders/{o11}/appuntamento/conferma", grezzo=b"{non e' json")
        prova("...un corpo rotto vale come nessun corpo: mai un 400", 200, c)
        c, _ = chiedi(VENDE, f"/api/orders/{o9}/appuntamento/conferma", {"quando": GIO})
        prova("...e la conferma resta di chi COMPRA: chi vende prende 400", 400, c)

        # =========== 8) L'INCASSO E' DI UN ALTRO ORDINE ===========
        print("\n[8. l'indirizzo Lightning: l'incasso e' di un ALTRO ordine]")
        # chi vende (444) non ha un indirizzo. Due ordini: la tenda, appena
        # pagata da chi compra e ancora da spedire; il fornello, confermato,
        # che aspetta l'incasso
        tenda = ordine("Tenda da campeggio", "spedizione", "locked", vende=VENDE3)
        fornello = ordine("Fornello", "spedizione", "confirmed", vende=VENDE3,
                          corriere="Poste Italiane", tracking="AB123456789IT",
                          spedito_il=int(time.time()) - 86400,
                          consegnato=int(time.time()) - 3600)
        dopo, vera = pagina(
            {"fa": "carica", "io": VENDE3}, {"fa": "apri", "ordine": tenda}, {"fa": "carica"},
            {"fa": "gesto", "nome": "saveLnAddress",
             "nodi": {"lnAddrInput": "vende3@wallet.example"}},
            {"fa": "leggi", "ordine": tenda, "altra": fornello}, {"fa": "carica"},
            {"fa": "leggi", "ordine": tenda, "altra": fornello})
        prova("chi vende apre la TENDA (da spedire) e li' scrive il suo indirizzo: il server "
              "paga il FORNELLO, e solo quello",
              ["locked", "released", "vende3@wallet.example"],
              [riga(tenda)["stato"], riga(fornello)["stato"],
               SRV.db().execute("SELECT ln_address FROM utenti WHERE tg_id=?",
                                (VENDE3,)).fetchone()[0]])
        prova("LA PAGINA: la tenda — l'ordine aperto — NON diventa «incassato»: resta da "
              "spedire, nella lista e nel ridisegno (uno); incassato e' il fornello",
              ["locked", "locked", 1, "released"],
              [dopo["riga"]["state"], (dopo["visto"] or {}).get("state"), dopo["ridisegni"],
               dopo["altra"]["state"]])
        prova("...e le parole non dicono che i sats di QUESTO ordine sono arrivati: dicono "
              "che i pagamenti in attesa sono partiti",
              ["⚡ Incassi automatici attivati: i pagamenti in attesa sono partiti"], dopo["detti"])
        prova("...ed e' quel che il server dice a una rilettura fresca",
              ["locked", "released"], [vera["riga"]["state"], vera["altra"]["state"]])

        # =========== 9) UN ALTRO ORDINE APERTO MENTRE LA RICHIESTA VIAGGIA ===========
        print("\n[9. un altro ordine aperto mentre la richiesta viaggia]")
        sedia = ordine("Sedia a dondolo", "spedizione", "locked", vende=VENDE3)
        dopo, vera = pagina(
            {"fa": "carica", "io": VENDE3}, {"fa": "apri", "ordine": sedia},
            {"fa": "gesto", "nome": "inviaSpedito", "altrove": tenda,
             "arg": ["Poste Italiane", "CD123456789IT", False]},
            {"fa": "leggi", "ordine": sedia, "altra": tenda}, {"fa": "carica"},
            {"fa": "leggi", "ordine": sedia, "altra": tenda})
        prova("«SEGNA COME SPEDITO» sulla SEDIA, e prima della risposta si apre la TENDA: il "
              "server ha spedito la sedia, e solo quella",
              [["shipped", "Poste Italiane", "CD123456789IT"], ["locked", None]],
              [[riga(sedia)["stato"], riga(sedia)["corriere"], riga(sedia)["tracking"]],
               [riga(tenda)["stato"], riga(tenda)["corriere"] or None]])
        prova("LA PAGINA: il fatto sta sulla SEDIA (l'ordine del gesto); la tenda — quella a "
              "schermo — non e' «spedita» e non ha preso il corriere",
              [{"state": "shipped", "corriere": "Poste Italiane", "tracking": "CD123456789IT"},
               "locked", True],
              [{k: dopo["riga"].get(k) for k in ("state", "corriere", "tracking")},
               dopo["altra"]["state"], not dopo["altra"].get("corriere")])
        prova("...nessuno viene riportato indietro: a schermo resta la tenda, zero ridisegni "
              "dell'ordine; il messaggio compare e si ridisegna la lista",
              [tenda, 0, True, ["📦 Segnato come spedito"]],
              [dopo["aSchermo"], dopo["ridisegni"], dopo["liste"] >= 1, dopo["detti"]])
        prova("...ed e' quel che il server dice a una rilettura fresca",
              ["shipped", "locked"], [vera["riga"]["state"], vera["altra"]["state"]])

        # =========== 10) LE FERIE: A OGNUNO LA SUA FRASE ===========
        print("\n[10. le ferie: a ogni ordine pagato la sua via d'uscita]")
        o12 = ordine("Vaso antico", "", "locked",
                     annuncio={"consegna": "entrambe", "asta_base_sats": 1000,
                               "asta_scadenza": int(time.time()) - 3600})
        o13 = ordine("Tavolino", "ritiro", "locked")
        o14 = ordine("Corso di cucina", "servizio", "locked")
        o15 = ordine("Buono regalo", "digitale", "locked")
        o16 = ordine("Radio d'epoca", "spedizione", "locked")
        c, d = chiedi(VENDE, "/api/me/ferie", {"fino": int(time.time()) + 5 * 86400})
        testo = json.dumps(d, ensure_ascii=False)
        prova("chi vende prova a chiudere per ferie: 400, con l'elenco degli impegni", 400, c)
        prova("...L'ASTA VINTA IN ATTESA DELLA SCELTA: «aspetta che chi ha vinto l'asta "
              "scelga la consegna», non «segna la spedizione»",
              [True, False],
              [f"ordine #{o12} «Vaso antico»: aspetta che chi ha vinto l'asta scelga la consegna"
               in testo,
               f"ordine #{o12} «Vaso antico»: segna la spedizione" in testo])
        prova("...e le altre strade, ognuna con la sua: il ritiro a mano, il servizio, il "
              "codice, il pacco",
              [True, True, True, True],
              [f"ordine #{o13} «Tavolino»: segna la consegna a mano" in testo,
               f"ordine #{o14} «Corso di cucina»: porta a termine il servizio" in testo,
               f"ordine #{o15} «Buono regalo»: consegna il codice" in testo,
               f"ordine #{o16} «Radio d'epoca»: segna la spedizione" in testo])
        prova("...e il negozio NON si e' chiuso", 0,
              (lambda u: u[0])(SRV.db().execute(
                  "SELECT ferie_fino FROM utenti WHERE tg_id=?", (VENDE,)).fetchone()))
    finally:
        srv.shutdown()
        shutil.rmtree(cart, ignore_errors=True)

    print(f"\n{PASSATE} ok, {FALLITE} NO")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
