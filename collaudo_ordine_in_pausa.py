# -*- coding: utf-8 -*-
"""
L'ORDINE PUBBLICATO DENTRO LA PAUSA (12 ott 2026, notte, cantiere
libro-vuoto, dal campo di Andrea).

IL CASO, rifatto con le sue ore. Alle 23:24:32 di lunedi' 12 ottobre una
persona salva dal foglio che pubblica la pausa «ogni giorno 22:00-07:00»,
e dodici secondi dopo pubblica una vendita da 50 a 100 euro (SEPA
Instant, Revolut, premio 8). La pausa valeva GIA': nel libro di
Barattolo l'ordine non lo vedeva nessuno — ma la 🔔 «1 nuovo ordine nel
libro P2P» e' arrivata a tutti, e chi apriva il libro leggeva «0
offerte», «Ci sono 1 offerte, ma nessuna passa il filtro» e un «Togli il
filtro» che non faceva niente, perche' un filtro non c'era.

LA DECISIONE DI ANDREA (13 ott): l'ordine di chi e' in pausa NON sparisce
dal libro. Resta, grigio, con la scritta arancio «⏸ Puoi prenderlo tra 6
h 35 min» che scende da sola; al tocco non si apre — la carta si scuote
e il telefono da' la vibrazione d'avviso (anche coi movimenti ridotti,
dove lo scuotimento non c'e'); alla fine della pausa torna normale da
sola. Il conto «N offerte» lo conta. La 🔔 aspetta la fine della pausa.

Qui girano il SERVER VERO — le rotte della pausa, dei volti e di «posso
prendere?», e il giro degli avvisi dei nuovi ordini com'e' —, su un
database usa-e-getta e con l'OROLOGIO FERMO alle ore del caso; e i
GIUDICI VERI DELLA PAGINA, ritagliati da miniapp.html e fatti girare in
node sulle risposte del server:

  1. la pausa salvata alle 23:24 e' gia' aperta, fino alle 07:00;
  2. l'ordine pubblicato dentro la pausa: nel libro di chi guarda C'E',
     si conta («1 offerta»), ed e' FERMO — la scritta «⏸ Puoi prenderlo
     tra 7 h 27 min», il tocco rifiutato con scuotimento e vibrazione
     d'avviso, i minuti che scendono da soli; chi l'ha pubblicato lo
     vede com'era e lo apre; «posso prendere?» dice `pausa` — e LA 🔔
     NON PARTE;
  3. ...nemmeno un quarto d'ora dopo: aspetta in coda;
  4. alle 07:00 la pausa finisce: la carta torna normale DA SOLA (il
     battito ridisegna il libro una volta), si prende, e la 🔔 parte,
     con «da 50,00 a 100,00 €» (un «da» solo);
  5. un ordine pubblicato in pausa e SPARITO prima della fine non si
     annuncia mai;
  6. chi pubblica in pausa vede l'avviso con le due strade, e «Togli la
     pausa per stanotte» lascia le fasce: l'ordine si vede e si annuncia
     subito, e la sera dopo la pausa e' quella di sempre;
  7. salvare una pausa nuova rimette tutto a zero;
  8. a leva spenta non si ferma niente.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), le notifiche finiscono in una lista, il
cambio e' un numero, niente relay, niente coordinatore.

USO:  python collaudo_ordine_in_pausa.py
"""

import asyncio
import calendar
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time as _time

import collaudo_pagamento_p2p as banco

PUBBLICA, GUARDA = banco.VENDE, banco.COMPRA
ORD = "fa17a63d-0e0e-4a2b-9c3d-0000000000e1"      # quello di stasera
ORD2 = "fa17a63d-0e0e-4a2b-9c3d-0000000000e2"     # pubblicato in pausa, sparito prima della fine
ORD3 = "fa17a63d-0e0e-4a2b-9c3d-0000000000e3"     # pubblicato dopo «togli la pausa per stanotte»
ORD4 = "fa17a63d-0e0e-4a2b-9c3d-0000000000e4"     # a leva spenta
NOTTI = {"g": [0, 1, 2, 3, 4, 5, 6], "da": 22 * 60, "a": 7 * 60}


def utc(giorno, ora, minuto, secondo=0):
    """Un'ora di ottobre 2026 in UTC: a Roma sono due ore di piu'."""
    return calendar.timegm((2026, 10, giorno, ora, minuto, secondo))


class Orologio:
    """Il modulo `time` del server, con `time()` fermo dove dice il
    collaudo: tutto il resto (sleep, monotonic, strftime) e' quello vero."""
    def __init__(self):
        self.ora = int(_time.time())

    def time(self):
        return float(self.ora)

    def __getattr__(self, nome):
        return getattr(_time, nome)


OROLOGIO = Orologio()


def evento_libro(ordine, creato):
    """Il 38383 del caso: vendita, 50-100 euro, SEPA Instant e Revolut,
    premio 8."""
    return {"kind": 38383, "created_at": creato,
            "tags": [["d", ordine], ["s", "pending"], ["k", "sell"], ["f", "EUR"],
                     ["amt", "0"], ["fa", "50", "100"],
                     ["pm", "SEPA Instant", "Revolut"], ["premium", "8"],
                     ["expires_at", str(creato + 2 * 86400)]]}


def pubblica(ordine, chi=None):
    """L'ordine entra nel libro: la riga di chi l'ha pubblicato e la
    scheda nella fotografia, all'ora dell'orologio."""
    chi = PUBBLICA if chi is None else chi
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                "metodi,premio) VALUES(?,?,?,'pending','sell',1,0,"
                "'da 50,00 a 100,00 €',?,8)",
                (ordine, chi, OROLOGIO.ora, json.dumps(["SEPA Instant", "Revolut"])))
    con.commit()
    con.close()
    ev = evento_libro(ordine, OROLOGIO.ora)
    F = banco.SRV._P2P_FOTO
    F["ultimi"][ordine] = ev
    F["eventi"] = list(F["ultimi"].values())


def togli_dal_libro(ordine):
    F = banco.SRV._P2P_FOTO
    F["ultimi"].pop(ordine, None)
    F["eventi"] = list(F["ultimi"].values())


async def giro():
    """Un battito degli avvisi dei nuovi ordini, quello VERO. Torna i
    messaggi partiti in questo battito: [(a chi, testo)]."""
    banco.SRV._P2P_FOTO["quando"] = OROLOGIO.ora
    prima = len(banco.DETTO)
    await banco.SRV._giro_avvisi_nuovi_p2p()
    return banco.DETTO[prima:]


def in_coda(ordine):
    con = banco.con_db()
    try:
        return [r[0] for r in con.execute(
            "SELECT mandato FROM p2p_avvisi_nuovi WHERE ordine=? ORDER BY tg_id", (ordine,))]
    finally:
        con.close()


async def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    banco.SRV.leggi_json = leggi
    try:
        r = await fn(banco.Busta(corpo))
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__), str(getattr(e, "detail", e)))
    return json.loads(r.body) if hasattr(r, "body") else r


async def scrivi_pausa(chi, corpo):
    banco.come(chi)
    return await chiama(banco.SRV.scrivi_pausa_p2p, corpo)


def leggi_pausa(chi):
    banco.come(chi)
    return json.loads(banco.SRV.mia_pausa_p2p().body)


async def posso(chi, ordine):
    banco.come(chi)
    return (await chiama(banco.SRV.posso_prendere_p2p, {"ordini": [ordine]}))["ordini"][ordine]


async def pause_viste(chi, ordini):
    """La mappa `pause` come arriva al libro di `chi`, coi volti."""
    banco.come(chi)
    return (await chiama(banco.SRV.facce_ordini_p2p, {"ordini": ordini})).get("pause") or {}


# ---- la pagina vera, in node ----------------------------------------
GIUDICI = ("idMostroVero", "filtroVuotoP2P", "filtroAccesoP2P", "passaFiltroP2P",
           "passaRepP2P", "vuotoLibroP2P", "prendiPauseP2P", "pausaOrdineP2P",
           "nascostoPerPausaP2P", "quandoPausaP2P", "bozzaPausaP2P",
           "traQuantoP2P", "etichettaPausaP2P", "rifiutaPerPausaP2P",
           "scuotiCartaP2P", "battitoPausaLibroP2P",
           "finePausaLocaleP2P", "finoMiaPausaP2P", "rigaAdessoPausaP2P",
           "avvisoPausaPubblicaP2P")

BANCO_JS = r"""
const P2P_PREMIO_MAX = 20;
let p2pPause = {}, p2pFiltro = null, p2pMiaPausa = null;
let MIEI = new Set();
function ordineTuoP2P(id){ return MIEI.has(String(id)); }
const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
/* la vibrazione di casa, di cartone: segna il tipo e se e' chiesta
   ANCHE coi movimenti ridotti */
let VIBRA = [];
function haptic(tipo, anche){ VIBRA.push([tipo || 'tocco', anche === true]); }
/* il libro a schermo, di cartone: le carte ferme e le loro scritte */
let CARTE = [], SCRITTE = [], RIDISEGNI = 0, LIBRO = [];
function rigaLibroP2P(id){ return LIBRO.find(o => o.id === id) || null; }
function renderP2P(){ RIDISEGNI++; }
const document = {querySelectorAll(sel){
  return sel.indexOf('p2p-pausa-tra') >= 0 ? SCRITTE : CARTE; }};
function carta(id, html){
  const classi = new Set(['p2p-ord', 'p2p-in-pausa']);
  const b = {textContent: (/<b>([^<]*)<\/b>/.exec(html) || [])[1] || ''};
  CARTE.push({dataset: {id: id}, offsetWidth: 1, classi: classi,
    classList: {add: c => classi.add(c), remove: c => classi.delete(c)}});
  SCRITTE.push({dataset: {fine: (/data-fine="(\d+)"/.exec(html) || [])[1]}, b: b,
    querySelector(){ return b; }});
}
const dati = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const out = [];
for (const s of dati) {
  const _now = Date.now;
  Date.now = () => s.adesso * 1000;
  p2pPause = {}; prendiPauseP2P(s.pause || {});
  MIEI = new Set(s.miei || []);
  p2pFiltro = s.filtro || null;
  p2pMiaPausa = s.miaPausa || null;
  VIBRA = []; CARTE = []; SCRITTE = []; RIDISEGNI = 0;
  const vivi = LIBRO = s.libro || [];
  const candidati = vivi.filter(o => passaFiltroP2P(o, p2pFiltro));
  const mostrati = candidati.filter(o => passaRepP2P(p2pFiltro, undefined));
  const r = {mostrati: mostrati.map(o => o.id),
             pillola: mostrati.length + ' offert' + (mostrati.length === 1 ? 'a' : 'e'),
             filtroAcceso: filtroAccesoP2P(p2pFiltro)};
  if (!mostrati.length) r.vuoto = vuotoLibroP2P(vivi, p2pFiltro, 'compro');
  /* le carte: ferma = porta la scritta (e la classe grigia, che nel
     disegno vero e' la stessa condizione) */
  r.scritte = mostrati.map(o => {
    const h = etichettaPausaP2P(o, s.adesso);
    if (h) carta(o.id, h);
    return h.replace(/<[^>]+>/g, '');
  });
  if (s.tocca) {
    const rifiutato = rifiutaPerPausaP2P(s.tocca);
    const c = CARTE.find(x => x.dataset.id === s.tocca);
    r.tocco = {rifiutato: rifiutato, vibra: VIBRA.slice(), scossa: !!c && c.classi.has('p2p-scuoti')};
  }
  if (s.battiti) r.battiti = s.battiti.map(t => {
    Date.now = () => t * 1000;
    battitoPausaLibroP2P();
    return {scritta: SCRITTE.map(x => x.b.textContent), ridisegni: RIDISEGNI,
            ferma: mostrati.map(o => !!etichettaPausaP2P(o, t))};
  });
  Date.now = () => s.adesso * 1000;
  if (s.miaPausa) {
    r.finoMia = finoMiaPausaP2P(s.adesso);
    r.avviso = r.finoMia ? avvisoPausaPubblicaP2P(r.finoMia, s.adesso) : null;
    const b = bozzaPausaP2P(s.miaPausa);
    r.rigaFoglio = rigaAdessoPausaP2P(b, s.adesso, Number(s.miaPausa.salta_fino) || 0, true);
  }
  if (s.bozza) r.rigaBozza = rigaAdessoPausaP2P(s.bozza, s.adesso, 0, false);
  Date.now = _now;
  out.push(r);
}
process.stdout.write(JSON.stringify(out));
"""


def pezzi_pagina():
    """I giudici VERI, ritagliati da miniapp.html: ogni funzione dalla
    sua firma alla graffa che la chiude a capo riga."""
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    mini = mini.replace("\r\n", "\n")
    pezzi = []
    for nome in GIUDICI:
        i = mini.index("\nfunction " + nome + "(")
        pezzi.append(mini[i:mini.index("\n}\n", i) + 3])
    return "\n".join(pezzi)


def pagina(scene):
    """Fa girare i giudici della pagina sulle scene: una lista di
    {adesso, libro, pause, miei, filtro, miaPausa, bozza}."""
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    cart = tempfile.mkdtemp(prefix="ordine_in_pausa_")
    try:
        p = os.path.join(cart, "pagina.js")
        d = os.path.join(cart, "scene.json")
        open(p, "w", encoding="utf-8").write(pezzi_pagina() + BANCO_JS)
        open(d, "w", encoding="utf-8").write(json.dumps(scene))
        # il telefono del caso sta a Roma: «alle 07:00» e' l'ora di chi legge
        r = subprocess.run([node, p, d], capture_output=True, text=True, timeout=120,
                           encoding="utf-8", env=dict(os.environ, TZ="Europe/Rome"))
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-800:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def riga_libro(ordine):
    """L'ordine come lo tiene il libro della pagina."""
    return {"id": ordine, "lato": "sell", "fiat": "EUR", "stato": "pending",
            "premium": 8, "metodi": ["SEPA Instant", "Revolut"]}


async def prove():
    SRV = banco.SRV
    prova = banco.prova
    SRV.time = OROLOGIO
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True
    SRV.P2P_AVVISI_NUOVI_ORDINI = True
    # il P2P acceso, come in produzione: sono i cancelli della leva, non
    # la cosa che si prova
    SRV._p2p_leve = lambda *a, **k: {"attivo": True}
    SRV._p2p_per = lambda tg: {"attivo": True}

    async def cambio():
        return 100000.0
    SRV.cambio_btc_eur = cambio
    con = banco.con_db()
    # chi guarda ha acceso la 🔔 dei nuovi ordini; chi pubblica no
    con.execute("UPDATE utenti SET avvisi_nuovi_p2p=1 WHERE tg_id=?", (GUARDA,))
    con.commit()
    con.close()
    F = SRV._P2P_FOTO
    F["ultimi"], F["eventi"] = {}, []

    print("\n1) le 23:24:32 a Roma: la pausa «ogni giorno 22-7» si salva, ed e' gia' aperta")
    OROLOGIO.ora = utc(12, 21, 24, 0)
    prova("il primo sguardo degli avvisi impara il libro, e non annuncia niente", [],
          await giro())
    OROLOGIO.ora = utc(12, 21, 24, 32)
    r = await scrivi_pausa(PUBBLICA, {"fasce": [NOTTI], "fuso": "Europe/Rome", "scarto": 120})
    prova("la pausa salvata dice SUBITO fino a quando: le 07:00 di domani a Roma",
          utc(13, 5, 0), r.get("fino"))
    scena = pagina([{"adesso": OROLOGIO.ora, "bozza": {"fasce": [NOTTI], "unaFino": 0}},
                    {"adesso": utc(12, 12, 0), "bozza": {"fasce": [NOTTI], "unaFino": 0}},
                    {"adesso": OROLOGIO.ora, "bozza": {"fasce": [], "unaFino": 0}}])
    prova("la pagina risponde (node)", False, isinstance(scena, dict) and "ERRORE" in scena)
    if isinstance(scena, dict):
        print("      ", scena.get("ERRORE"))
        return
    prova("...e il foglio lo diceva gia' PRIMA di salvare, sotto le fasce: attiva adesso",
          "⏸ Attiva adesso: nessuno può prendere i tuoi ordini fino a domani alle 07:00.",
          scena[0]["rigaBozza"])
    prova("...la stessa pausa composta alle 14:00 dice che adesso non lo e'",
          "Adesso non è attiva: i tuoi ordini si possono prendere.", scena[1]["rigaBozza"])
    prova("...e senza niente di scritto la riga non c'e'", "", scena[2]["rigaBozza"])

    print("\n2) dodici secondi dopo l'ordine e' nel libro: chi lo vede, e chi no")
    OROLOGIO.ora = utc(12, 21, 24, 44)
    pubblica(ORD)
    pause = await pause_viste(GUARDA, [ORD])
    prova("al libro di chi guarda arriva che quell'ordine e' in pausa fino alle 07:00",
          {ORD: utc(13, 5, 0)}, pause)
    v = await posso(GUARDA, ORD)
    prova("«posso prendere?» lo ferma col motivo `pausa`", (False, "pausa"),
          (v["ok"], v["motivo"]))
    OROLOGIO.ora = utc(12, 21, 33, 0)                 # le 23:33: l'ora della 🔔 di stasera
    SATISPAY = {"valute": [], "metodi": ["Satispay"], "premioDa": -20, "premioA": 20,
                "repDa": 0, "repA": 5}
    scena = pagina([
        {"adesso": OROLOGIO.ora, "libro": [riga_libro(ORD)], "pause": pause, "tocca": ORD,
         "battiti": [utc(12, 21, 33, 20), utc(12, 21, 58, 0), utc(13, 4, 59, 30),
                     utc(13, 5, 0, 1)]},
        {"adesso": OROLOGIO.ora, "libro": [riga_libro(ORD)], "pause": pause, "miei": [ORD],
         "tocca": ORD},
        {"adesso": OROLOGIO.ora, "libro": [riga_libro(ORD)], "pause": pause,
         "filtro": SATISPAY},
        {"adesso": OROLOGIO.ora, "libro": [riga_libro(ORD), riga_libro(ORD2)],
         "pause": {ORD: utc(13, 5, 0), ORD2: utc(12, 22, 8)}}])
    chi_guarda, autore, filtrato, due = scena
    prova("IL LIBRO DI CHI GUARDA: l'ordine C'E' e si conta — «1 offerta», filtro spento",
          ("1 offerta", False, [ORD]),
          (chi_guarda["pillola"], chi_guarda["filtroAcceso"], chi_guarda["mostrati"]))
    prova("...ed e' FERMO: la scritta dice fra quanto si potra' prendere",
          ["⏸ Puoi prenderlo tra 7 h 27 min"], chi_guarda["scritte"])
    prova("IL TOCCO NON LO APRE: rifiutato, la carta si scuote, e la vibrazione e' l'AVVISO "
          "— chiesto anche coi movimenti ridotti, dove lo scuotimento non c'e'",
          {"rifiutato": True, "vibra": [["warning", True]], "scossa": True},
          chi_guarda["tocco"])
    b = chi_guarda["battiti"]
    prova("IL CONTO SCENDE DA SOLO, in place e senza ridisegnare: 7 h 27 min, poi 7 h 2 min, "
          "e a mezzo minuto dalla fine «1 min»",
          ([["7 h 27 min"], ["7 h 2 min"], ["1 min"]], [0, 0, 0]),
          ([x["scritta"] for x in b[:3]], [x["ridisegni"] for x in b[:3]]))
    prova("ALLO SCADERE il battito ridisegna il libro UNA volta, e la carta non e' piu' ferma",
          (1, [False]), (b[3]["ridisegni"], b[3]["ferma"]))
    prova("CHI L'HA PUBBLICATO lo vede com'era: nessuna scritta «puoi prenderlo», e il suo "
          "tocco non e' rifiutato ne' vibra d'avviso",
          ([ORD], [""], {"rifiutato": False, "vibra": [], "scossa": False}),
          (autore["mostrati"], autore["scritte"], autore["tocco"]))
    prova("un filtro che non lo lascia passare lo ferma come ogni altra offerta: «C'è 1 "
          "offerta, ma non passa il filtro.» col suo «Togli il filtro»",
          ("Nessun ordine col tuo filtro", "C'è 1 offerta, ma non passa il filtro.", True),
          (filtrato["vuoto"]["titolo"], filtrato["vuoto"]["frase"], filtrato["vuoto"]["togli"]))
    prova("con due ordini in pausa ognuno dice il SUO tempo, e sotto l'ora si dice in minuti",
          ("2 offerte", ["⏸ Puoi prenderlo tra 7 h 27 min", "⏸ Puoi prenderlo tra 35 min"]),
          (due["pillola"], due["scritte"]))
    prova("LA 🔔 NON PARTE: l'ordine e' nuovo, ma chi l'ha pubblicato e' in pausa", [],
          await giro())
    prova("...e la riga resta in coda per chi la voleva", [0], in_coda(ORD))

    print("\n3) un quarto d'ora dopo e' ancora in pausa: la 🔔 aspetta")
    OROLOGIO.ora = utc(12, 21, 50, 0)
    prova("nessun messaggio, e la riga e' ancora in coda", ([], [0]),
          (await giro(), in_coda(ORD)))

    print("\n4) le 07:00: la pausa finisce, l'ordine torna e la 🔔 parte")
    OROLOGIO.ora = utc(13, 4, 59, 0)
    prova("un minuto prima ancora niente", [], await giro())
    OROLOGIO.ora = utc(13, 5, 0, 30)
    prova("la mappa delle pause e' vuota", {}, await pause_viste(GUARDA, [ORD]))
    partiti = await giro()
    prova("UN messaggio, a chi guarda e non a chi ha pubblicato", [GUARDA],
          [chi for chi, _ in partiti])
    testo = partiti[0][1] if partiti else ""
    prova("...dice «1 nuovo ordine nel libro P2P», la cifra con UN «da» solo, i metodi e "
          "la convenienza", [True, True, False, True],
          ["<b>1 nuovo ordine nel libro P2P</b>" in testo,
           # (18 nov 2026, vetrina-pulita) una riga per ordine, dal lato di
           # chi legge: chi ha pubblicato vende, chi legge «Compra BTC»
           # (stesso giorno, apri-ordine-notifica) e il lato apre l'ordine
           "🟢 <b>Compra BTC</b></a> · da 50,00 a 100,00 € · SEPA Instant, Revolut · "
           "8% meno conveniente" in testo,
           # ...e con un ordine solo il tocco in fondo e' «Apri l'ordine»
           "da da" in testo, f"?ordine={ORD}\">🫙 Apri l'ordine</a>" in testo])
    prova("...la riga e' timbrata, e al giro dopo non riparte", (True, []),
          (in_coda(ORD)[0] > 1, await giro()))
    scena = pagina([{"adesso": OROLOGIO.ora, "libro": [riga_libro(ORD)], "pause": {},
                     "tocca": ORD}])
    prova("...nel libro di chi guarda la carta e' tornata normale: nessuna scritta, e il "
          "tocco passa", ([ORD], "1 offerta", [""], False, []),
          (scena[0]["mostrati"], scena[0]["pillola"], scena[0]["scritte"],
           scena[0]["tocco"]["rifiutato"], scena[0]["tocco"]["vibra"]))
    prova("«posso prendere?» adesso dice di si'", True, (await posso(GUARDA, ORD))["ok"])

    print("\n5) pubblicato in pausa e sparito prima della fine: non si annuncia mai")
    OROLOGIO.ora = utc(13, 20, 30, 0)                 # le 22:30 di martedi'
    prova("la sera dopo la pausa e' di nuovo aperta, fino alle 07:00 di mercoledi'",
          utc(14, 5, 0), leggi_pausa(PUBBLICA)["fino"])
    pubblica(ORD2)
    prova("la 🔔 del secondo ordine non parte", ([], [0]), (await giro(), in_coda(ORD2)))
    togli_dal_libro(ORD2)
    OROLOGIO.ora = utc(14, 5, 1, 0)
    prova("...l'ordine se n'e' andato nella notte: alla fine della pausa niente messaggio, "
          "e la riga e' consumata", ([], [1]), (await giro(), in_coda(ORD2)))

    print("\n6) «Togli la pausa per stanotte»: l'avviso prima di pubblicare, e le fasce che restano")
    OROLOGIO.ora = utc(14, 21, 10, 0)                 # le 23:10 di mercoledi'
    mia = leggi_pausa(PUBBLICA)
    scena = pagina([{"adesso": OROLOGIO.ora, "miaPausa": mia},
                    # la lettura e' di PRIMA delle 22: `fino` era 0, ma le fasce ci sono
                    {"adesso": OROLOGIO.ora, "miaPausa": dict(mia, fino=0)},
                    # una pausa di giorno, tolta a mezzogiorno: non e' una notte
                    {"adesso": utc(14, 10, 0), "miaPausa": {
                        "fasce": [{"g": [0, 1, 2, 3, 4, 5, 6], "da": 480, "a": 1200}],
                        "una_fino": 0, "fino": utc(14, 18, 0), "salta_fino": 0}}])
    prova("chi sta per pubblicare e' in pausa fino alle 07:00, e la pagina lo sa",
          utc(15, 5, 0), scena[0]["finoMia"])
    prova("...anche se l'ultima lettura era di prima che la pausa cominciasse",
          utc(15, 5, 0), scena[1]["finoMia"])
    prova("L'AVVISO PRIMA DI PUBBLICARE: la frase, e i due tasti",
          {"titolo": "Pubblichi durante la pausa?",
           "corpo": "Sei in pausa fino a domani alle 07:00: il tuo ordine si vedrà in "
                    "grigio e si potrà prendere solo da allora.",
           "etichetta": "Pubblica lo stesso", "altra": "Togli la pausa per stanotte"},
          scena[0]["avviso"])
    prova("...di giorno il secondo tasto non parla di notte", "Togli la pausa per adesso",
          scena[2]["avviso"]["altra"])
    r = await scrivi_pausa(PUBBLICA, {"salta": True})
    prova("«Togli la pausa per stanotte»: adesso non e' in pausa, LE FASCE RESTANO, e il "
          "salto finisce alle 07:00", (0, [NOTTI], utc(15, 5, 0)),
          (r.get("fino"), r.get("fasce"), r.get("salta_fino")))
    scena = pagina([{"adesso": OROLOGIO.ora, "miaPausa": r}])
    prova("...la pagina non ferma piu' chi pubblica, e il foglio dice che per stanotte e' tolta",
          (0, None, "Tolta fino a domani alle 07:00: adesso i tuoi ordini si possono prendere."),
          (scena[0]["finoMia"], scena[0]["avviso"], scena[0]["rigaFoglio"]))
    pubblica(ORD3)
    prova("l'ordine pubblicato subito dopo NON e' in pausa, e si prende",
          ({}, True), (await pause_viste(GUARDA, [ORD3]), (await posso(GUARDA, ORD3))["ok"]))
    prova("...e la sua 🔔 parte al primo giro", [GUARDA], [chi for chi, _ in await giro()])
    OROLOGIO.ora = utc(15, 5, 0, 30)
    prova("alle 07:00 il salto e' finito: nessuna pausa aperta", (0, 0),
          (leggi_pausa(PUBBLICA)["fino"], leggi_pausa(PUBBLICA)["salta_fino"]))
    OROLOGIO.ora = utc(15, 20, 30, 0)                 # le 22:30 di giovedi'
    prova("LA SERA DOPO la pausa e' quella di sempre, e l'ordine e' di nuovo fermo",
          (utc(16, 5, 0), {ORD3: utc(16, 5, 0)}),
          (leggi_pausa(PUBBLICA)["fino"], await pause_viste(GUARDA, [ORD3])))
    r = await scrivi_pausa(GUARDA, {"salta": True})
    prova("chi non e' in pausa e chiede di saltarla non scrive niente", (0, [], 0),
          (r.get("fino"), r.get("fasce"), r.get("salta_fino")))

    print("\n7) una pausa salvata di nuovo e' un'intenzione nuova")
    await scrivi_pausa(PUBBLICA, {"salta": True})
    prova("saltata la notte di giovedi'...", 0, leggi_pausa(PUBBLICA)["fino"])
    r = await scrivi_pausa(PUBBLICA, {"fasce": [NOTTI], "fuso": "Europe/Rome", "scarto": 120})
    prova("...risalvare le stesse fasce la riapre subito: il salto torna a zero",
          (utc(16, 5, 0), 0), (r.get("fino"), r.get("salta_fino")))
    una = await scrivi_pausa(GUARDA, {"una_fino": OROLOGIO.ora + 3600})
    prova("una pausa «una volta sola» aperta adesso...", OROLOGIO.ora + 3600, una.get("fino"))
    r = await scrivi_pausa(GUARDA, {"salta": True})
    prova("...tolta «per stanotte» se ne va del tutto: era proprio lei", (0, 0, 0),
          (r.get("fino"), r.get("una_fino"), r.get("salta_fino")))

    print("\n8) a leva spenta non si ferma niente")
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = False
    pubblica(ORD4)
    prova("l'ordine di chi sarebbe in pausa si annuncia subito, come ieri", [GUARDA],
          [chi for chi, _ in await giro()])
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True


def main():
    banco.avvio()
    banco.semina()
    asyncio.run(prove())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
