# -*- coding: utf-8 -*-
"""
IL FOGLIO DELLA GARANZIA SI CHIUDE COL SERVER VERO (15 ott 2026, cantiere
«garanzia-non-si-chiude», richiesta di Andrea).

Il caso: lo scambio 101e20d6. Chi vendeva ha pagato la garanzia con
Phoenix, il coordinatore l'aveva, e nella Mini App il foglio «🔒 Blocca
i sats» e' rimasto aperto con la richiesta sopra. Si chiudeva SOLO dal
messaggio del coordinatore via relay: se la notizia arrivava prima dal
server (o dalla restore), la riga passava ad «attivo» sotto il foglio e
il messaggio dopo non lo chiudeva piu'. Chiusa e riaperta l'app, il
passo risultava fatto.

`prove.py` difende i pezzi e la regola (`prove_foglio_pagato_p2p`). Qui
gira la ROTTA VERA (`/api/p2p/scambi`) sul database vero e usa-e-getta,
con gli eventi di mostrod passati dai due giudici della rotta degli
eventi, e sulle sue risposte gira il CLIENT VERO in node — la
sentinella del foglio, l'adozione dell'archivio, la scrittura della riga
e la chiusura — senza relay:

  1. lo scambio di 101e20d6 rifatto: un «vendi», preso da chi compra, la
     fattura data, la garanzia chiesta; il server dice a chi vende «tocca
     a te bloccare»;
  2. col foglio aperto la sentinella chiede: il server dice ancora «da
     pagare», il foglio resta aperto e zitto;
  3. mostrod racconta «garanzia pagata»: al battito dopo il server dice
     «attivo», la riga avanza, il FOGLIO SI CHIUDE e la pagina si
     ridisegna — senza nessun messaggio via relay;
  4. il messaggio del relay arrivato DOPO (la stessa riga, «attivo»)
     non riapre e non ripete niente;
  5. l'altro verso: il messaggio arriva PRIMA, chiude lui, e la
     risposta del server dopo non fa niente;
  6. il server muto per mezzo minuto: il foglio lo dice, e appena il
     server risponde con «attivo» si chiude.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_foglio_pagato.py
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

SCAMBIO = "101e2000-aaaa-4a2b-9c3d-0000000000d6"


def semina_ordine():
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                "56163,'40,00 €','[\"SEPA\"]')",
                (SCAMBIO, banco.VENDE, int(time.time()) - 3600))
    con.commit()
    con.close()


def scambi(chi):
    banco.come(chi)
    r = asyncio.run(banco.SRV.scambi_p2p())
    return json.loads(r.body)["scambi"]


def js(mini, firma, fine="\n}\n"):
    i = mini.index(firma)
    return mini[i:mini.index(fine, i) + len(fine)]


def client(locale, passi):
    """IL CLIENT VERO: la riga `locale` sul dispositivo di chi vende, il
    foglio della garanzia aperto su di lei, e i `passi` uno dopo l'altro.
    Un passo e' `{"server": <risposta della rotta o null = muto>, "dt": ms}`
    (un battito della sentinella), o `{"relay": "<stato>"}` (il messaggio
    del coordinatore che scrive la riga). Torna una fotografia per passo."""
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    riga = lambda firma: mini[mini.index(firma):mini.index("\n", mini.index(firma))]
    fino = lambda da, a: mini[mini.index(da):mini.index("\n}\n", mini.index(a)) + 3]
    pezzi = "\n".join([
        "const _box = {}; const localStorage = {getItem: k => (k in _box ? _box[k] : null),"
        " setItem: (k, v) => { _box[k] = String(v); }};",
        "const chiaveP2P = k => k; const MOSTRO_ORDINI_CHIAVE = 'o'; const window = {NostrTools: {}};",
        "let p2pMieiOrdini = null, p2pLibro = null, p2pScambiServer = null;",
        "let p2pOrdineAperto = '', p2pHoldOrdine = '', p2pHoldModo = 'hold';",
        "const diario = []; function diarioP2P(r){ diario.push(r); }",
        "const toasts = []; function toast(t){ toasts.push(t); } function haptic(){}",
        # un dispositivo che la chiave non la deriva: l'adozione muove lo
        # stato lo stesso, ed e' quel che serve qui
        "function mazzoMostro(){ return null; } function chiaveScambio(){ throw new Error('senza mazzo'); }",
        "const nodi = {};",
        "const nodo = id => nodi[id] || (nodi[id] = {id, textContent: '', style: {display: 'none'}, "
        "_cl: new Set(), get classList(){ const s = this._cl; return {"
        "add: c => s.add(c), remove: c => s.delete(c), contains: c => s.has(c)}; }});",
        "const el = id => nodo(id); function altroFoglioAperto(){ return false; }",
        "const document = {visibilityState: 'visible'};",
        "let ORA = Date.now(); Date.now = () => ORA;",
        "globalThis.setInterval = (f, ms) => 1; globalThis.clearInterval = () => {};",
        riga("const P2P_FINALI = "), riga("const P2P_LIBRO_FINESTRA_S = "),
        riga("const MOSTRO_LAPIDI_CHIAVE = "),
        js(mini, "const STATI_P2P = {", "\n};\n"),
        js(mini, "const P2P_PROGRESSO = {", "\n};\n"),
        js(mini, "function fermoAnnulloP2P(o){"),
        js(mini, "function ordiniP2P(){"), js(mini, "function scriviOrdineP2P(o){"),
        fino("const P2P_STATI_DA_PAGARE = ", "function chiudiFoglioPagatoP2P(prima, o){"),
        js(mini, "function chiudiFoglioP2P(idFoglio){"),
        fino("const P2P_DA_RESTORE = {", "function riprendiDaRestoreP2P(o, statoMostro){"),
        fino("const P2P_INDICE_CERCA_MAX = ", "function adottaScambiServerP2P(locali){"),
        js(mini, "function presenzeDaServerP2P(p, giro){"), js(mini, "function uniscePresenzeP2P(a, b){"),
        mini[mini.index("function p2pRitirato(o){"):mini.index("\n}", mini.index("function p2pRitirato(o){")) + 2],
        js(mini, "function lapidiP2P(){"), js(mini, "function lapideP2P(o){"),
        js(mini, "function lapidataP2P(id, giro){"), js(mini, "function archiviaRitiratoP2P(id){"),
        js(mini, "function giroArchiviatoP2P(locali, id){"),
        fino("let P2P_FOGLIO_OGNI_MS = ", "function mutoFoglioP2P(muto){"),
    ])
    prog = pezzi + """
const dati = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf-8'));
let prossima = null, chieste = 0, render = 0, restore = 0;
async function chiediScambiServerP2P(){
  chieste++;
  if (prossima === null) return false;
  p2pScambiServer = JSON.parse(JSON.stringify(prossima));
  return true;
}
function riallineaScambioP2P(){ restore++; return Promise.resolve(false); }
function renderOrdineP2P(){ render++; }
function vistaAttivaP2P(){ return 'view-p2pordine'; }
const id = dati.locale.id;
localStorage.setItem('o', JSON.stringify({[id]: dati.locale}));
p2pOrdineAperto = id; p2pHoldOrdine = id;
nodo('p2pHoldSheet').classList.add('open');
sentinellaFoglioP2P();
const foto = () => ({stato: ordiniP2P()[id].stato,
  aperto: nodo('p2pHoldSheet').classList.contains('open'), foglioDi: p2pHoldOrdine,
  muto: nodo('p2pHoldMuto').style.display === '' ? nodo('p2pHoldMuto').textContent : '',
  chieste, render, toasts: toasts.length,
  chiusure: diario.filter(r => r.indexOf('foglio ') === 0 && r.indexOf(': chiuso (') > 0).length});
(async () => {
  const out = [];
  for (const p of dati.passi) {
    if (p.relay) {
      const o = ordiniP2P()[id];
      o.stato = p.relay;
      scriviOrdineP2P(o);
    } else {
      ORA += p.dt || 5000;
      prossima = p.server;
      await chiediFoglioP2P();
    }
    out.push(foto());
  }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""
    cart = tempfile.mkdtemp(prefix="foglio_pagato_")
    try:
        p = os.path.join(cart, "client.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(prog)
        open(d, "w", encoding="utf-8").write(json.dumps({"locale": locale, "passi": passi}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=60, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-600:]}
    return json.loads(r.stdout)


def main():
    banco.avvio()
    banco.semina()
    semina_ordine()
    prova = banco.prova
    t = int(time.time()) - 600
    V = banco.VENDE
    KV, KC = banco.CHIAVE_VENDE, banco.CHIAVE_COMPRA

    print("\n1) lo scambio di 101e20d6, fino alla garanzia chiesta")
    banco.evento(SCAMBIO, "taken", t + 10, "buyer", "take")
    banco.evento(SCAMBIO, "buyer-invoice-added", t + 20, "buyer", "hold-next")
    banco.evento(SCAMBIO, "hold-invoice-requested", t + 20, "mostro", "invoice")
    prima = scambi(V)
    prova("a chi vende il server dice: tocca a te bloccare i sats",
          ["attesa_mia_hold", "vendo", True], [prima[SCAMBIO][k] for k in ("stato", "lato", "mio")])
    risposta_prima = {SCAMBIO: prima[SCAMBIO]}

    print("\n2-3) la garanzia pagata: il foglio si chiude col server, senza relay")
    banco.evento(SCAMBIO, "hold-invoice-paid", t + 30, "seller")
    dopo = scambi(V)
    prova("mostrod ha detto «garanzia pagata»: il server dice «attivo»",
          ["attivo", t + 30], [dopo[SCAMBIO]["stato"], dopo[SCAMBIO]["quando"]])
    risposta_dopo = {SCAMBIO: dopo[SCAMBIO]}
    locale = {"id": SCAMBIO, "lato": "vendo", "mio": True, "stato": "attesa_mia_hold",
              "pubTrade": KV, "peer": KC, "euro": 40, "metodi": ["SEPA"], "preso": True,
              "giro": 1, "creato": t, "ultimaMossa": t + 20,
              "hold": {"bolt11": "lnbc561630n1finta", "sats": 56163, "quando": t + 20}}
    r = client(locale, [{"server": risposta_prima}, {"server": risposta_dopo},
                        {"relay": "attivo"}])
    if "ERRORE" in r:
        prova("il client vero gira", "", r["ERRORE"])
    else:
        a, b, c = r
        prova("col server che dice ancora «da pagare»: foglio aperto, zitto, niente ridisegno",
              ["attesa_mia_hold", True, SCAMBIO, "", 0], [a[k] for k in ("stato", "aperto", "foglioDi", "muto", "render")])
        prova("al battito dopo: la riga va ad «attivo», il foglio si chiude UNA volta, la pagina si ridisegna",
              ["attivo", False, "", 1, 1, 2], [b[k] for k in ("stato", "aperto", "foglioDi", "chiusure", "render", "chieste")])
        prova("4) il messaggio del relay arrivato DOPO non riapre ne' ripete niente",
              ["attivo", False, 1, 0], [c[k] for k in ("stato", "aperto", "chiusure", "toasts")])

    print("\n5) l'altro verso: il relay prima, il server dopo")
    r = client(locale, [{"relay": "attivo"}, {"server": risposta_dopo}])
    if "ERRORE" in r:
        prova("il client vero gira", "", r["ERRORE"])
    else:
        a, b = r
        prova("il messaggio chiude il foglio", ["attivo", False, 1], [a[k] for k in ("stato", "aperto", "chiusure")])
        prova("...e la risposta del server dopo non fa niente (la sentinella si e' gia' spenta)",
              ["attivo", False, 1, 0], [b[k] for k in ("stato", "aperto", "chiusure", "chieste")])

    print("\n6) il server muto per mezzo minuto, poi risponde")
    r = client(locale, [{"server": None}] * 6 + [{"server": risposta_dopo}])
    if "ERRORE" in r:
        prova("il client vero gira", "", r["ERRORE"])
    else:
        prova("fino ai 25 s il foglio aspetta zitto", [["attesa_mia_hold", True, ""]] * 5,
              [[x["stato"], x["aperto"], x["muto"]] for x in r[:5]])
        prova("ai 30 s lo dice: non riesco a controllare, riprovo, non pagare due volte",
              [True, True, True], [r[5]["aperto"], "Non riesco a controllare" in r[5]["muto"],
                                   "Non pagare due volte." in r[5]["muto"]])
        prova("...e quando il server risponde «attivo» il foglio si chiude",
              ["attivo", False, 1], [r[6][k] for k in ("stato", "aperto", "chiusure")])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
