# -*- coding: utf-8 -*-
"""
LO STESSO ID, UN GIRO NUOVO — SUL SERVER VERO (7 ott 2026).

Dal campo: Andrea prende l'ordine f904185a di Alan dal telefono, lo
annulla, lo riprende. In Mostro chi prende e si ritira prima della
garanzia rimanda l'ordine nel libro con lo STESSO id, e la presa dopo e'
uno scambio nuovo (trade key nuova, giro nuovo per il server) sotto un
nome vecchio. Il telefono lo ha seguito; il PC, stesso account e stesso
profilo, teneva la riga «annullato» del primo giro, e lo scambio vivo
stava nascosto fra gli annullati.

`prove.py` difende il giudice e i casi in node (`prove_giro_nuovo_
stesso_id`). Qui gira il SERVER VERO, sul database usa-e-getta, con gli
eventi di mostrod passati dai due giudici della rotta degli eventi — la
presa, il ritiro con `republished`, la seconda presa con la seconda
chiave, la garanzia, gli euro — e il CLIENT VERO di miniapp.html in node
sulle risposte vere di `/api/p2p/scambi`:

  1. il server racconta i due giri: dopo il ritiro chi aveva preso legge
     «annullato» (giro 1, la sua prima chiave); dopo la seconda presa
     legge lo scambio vivo (giro 2, la seconda chiave), e chi ha
     pubblicato ha la controparte nuova;
  2. il PC di chi ha preso: la riga nata «annullato» al giro 1 va sotto
     «Annullati» col nome `id~…` e ne nasce una nuova, governabile con
     la seconda chiave, al giro 2; l'ascolto segue la chiave nuova;
  3. la riga vecchia come l'aveva il PC di Andrea — annullata, ma gia'
     con la chiave nuova e senza giro —: il momento del server dopo
     l'annullo basta;
  4. il dispositivo di chi ha PUBBLICATO che ha perso il giro: la riga
     riparte in place con controparte, giro e stato nuovi;
  5. l'eco vecchia: la foto del giro 1 su un dispositivo gia' al giro 2
     non riporta indietro niente, e lo dice una volta;
  6. la restore con l'indice piu' alto mette da parte la riga vecchia, e
     l'archivio fa nascere la nuova;
  7. le lapidi: la ✕ sul giro 1 non ferma la nascita del giro 2, quella
     sul giro 2 si'; e per il server la ✕ sulla riga vecchia e' «aperto»;
  8. lo stesso con lo SCADUTO di chi aveva preso (`expired`,
     `taker-timeout`), che rimette nel libro allo stesso modo.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_giro_nuovo.py
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

ORD = "f9040000-aaaa-4a2b-9c3d-0000000000a1"
SCAD = "f9040000-bbbb-4a2b-9c3d-0000000000b1"
# la seconda trade key della stessa persona che compra: quella della ripresa
CHIAVE_COMPRA_2 = "c3" * 32


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine in (ORD, SCAD):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','sell',1,"
                    "15000,'10,00 €','[\"SEPA\"]')", (ordine, banco.VENDE, adesso - 3600))
    con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)",
                (CHIAVE_COMPRA_2, banco.COMPRA, adesso))
    con.commit()
    con.close()


def js(mini, firma, fine="\n}\n"):
    i = mini.index(firma)
    return mini[i:mini.index(fine, i) + len(fine)]


def client(risposta, locali, chiavi, miei=None, lapidi=None):
    """IL CLIENT VERO SULLA RISPOSTA VERA: le adozioni di miniapp.html in
    node. `chiavi` sono le trade key del profilo per indice (la
    derivazione vera vuole il bundle: qui e' una tabella); `miei` la
    restore (`p2pMieiOrdini`), `lapidi` le lapidi gia' scritte. Torna le
    righe dopo (stato, indice, chiave, giro, controparte, ultima mossa,
    idVero, solo da guardare), l'ascolto e il diario."""
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    riga = lambda firma: mini[mini.index(firma):mini.index("\n", mini.index(firma))]
    fino = lambda da, a: mini[mini.index(da):mini.index("\n}\n", mini.index(a)) + 3]
    pezzi = "\n".join([
        "const _box = {}; const localStorage = {getItem: k => (k in _box ? _box[k] : null),"
        " setItem: (k, v) => { _box[k] = String(v); }};",
        "const chiaveP2P = k => k; const window = {NostrTools: {schnorr: true}};",
        "let p2pOrdineAperto = '', p2pHoldOrdine = '', p2pIncassoOrdine = '';",
        "let p2pMieiOrdini = null, p2pLibro = {ordini: []}, p2pScambiServer = null;",
        "let p2pDiario = []; function diarioP2P(r){ p2pDiario.push(r); }",
        "function rigaLibroP2P(){ return null; }",
        riga("const MOSTRO_ORDINI_CHIAVE = "), riga("const P2P_ORIZZONTE_S = "),
        riga("const P2P_LAPIDE_TOLTO_S = "), riga("const P2P_LIBRO_FINESTRA_S = "),
        riga("const MOSTRO_LAPIDI_CHIAVE = "), riga("const P2P_FINALI = "),
        js(mini, "const P2P_GIRO_APERTO = [", "];\n"),
        js(mini, "const STATI_P2P = {", "\n};\n"), js(mini, "const P2P_PROGRESSO = {", "\n};\n"),
        js(mini, "const P2P_DELLA_PRESA = [", "];\n"),
        js(mini, "function ordiniP2P(){"),
        fino("function nomeProvvisorioP2P(indice){", "function rinominaOrdineP2P(o, nuovoId){"),
        js(mini, "function scriviOrdineP2P(o){"),
        js(mini, "function lapidiP2P(){"), js(mini, "function lapideP2P(o){"),
        js(mini, "function lapidataP2P(id, giro){"),
        mini[mini.index("function p2pRitirato(o){"):mini.index("\n}", mini.index("function p2pRitirato(o){")) + 2],
        js(mini, "function archiviaRitiratoP2P(id){"),
        fino("const P2P_RESTORE_CHIUSI = ", "function giroArchiviatoP2P(locali, id){"),
        js(mini, "function ordiniAscoltoP2P(){"), js(mini, "function cauzioneAFineP2P(o){"),
        fino("const P2P_DA_RESTORE = {", "function riprendiDaRestoreP2P(o, statoMostro){"),
        js(mini, "function adottaOrdiniAltroveP2P(locali){"),
        fino("const P2P_INDICE_CERCA_MAX = ", "function adottaScambiServerP2P(locali){"),
        js(mini, "function presenzeDaServerP2P(p, giro){"), js(mini, "function uniscePresenzeP2P(a, b){"),
    ])
    prog = pezzi + """
const dati = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf-8'));
const mazzo = {sk: 'S', pub: 'P', indice: dati.chiavi.length};
function mazzoMostro(){ return mazzo; }
function chiaveScambio(sk, i){
  const pub = dati.chiavi[i - 1];
  if (!pub) throw new Error('indice senza chiave');
  return {sk: 'sk:' + pub, pub: pub, indice: i};
}
_box[MOSTRO_ORDINI_CHIAVE] = JSON.stringify(dati.locali);
if (dati.lapidi) _box[MOSTRO_LAPIDI_CHIAVE] = JSON.stringify(dati.lapidi);
p2pMieiOrdini = dati.miei || null;
p2pScambiServer = dati.risposta;
const n1 = p2pMieiOrdini ? adottaOrdiniAltroveP2P(ordiniP2P()) : 0;
const n2 = adottaScambiServerP2P(ordiniP2P());
const out = {n: [n1, n2], righe: {}, ascolto: Object.keys(ordiniAscoltoP2P()).sort(), diario: p2pDiario,
             locali: ordiniP2P(), lapidi: lapidiP2P()};
for (const [k, o] of Object.entries(ordiniP2P()))
  out.righe[k] = [o.stato, o.indice | 0, o.pubTrade || '', o.giro | 0, o.peer || '', o.ultimaMossa || 0,
                  o.idVero || '', !!o.soloVista];
process.stdout.write(JSON.stringify(out));
"""
    cart = tempfile.mkdtemp(prefix="giro_nuovo_")
    try:
        p = os.path.join(cart, "client.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(prog)
        open(d, "w", encoding="utf-8").write(json.dumps(
            {"risposta": risposta, "locali": locali, "chiavi": chiavi, "miei": miei, "lapidi": lapidi}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=60, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-600:]}
    return json.loads(r.stdout)


def scambi(chi):
    banco.come(chi)
    r = asyncio.run(banco.SRV.scambi_p2p())
    return json.loads(r.body).get("scambi", {})


def voce(chi, ordine, *campi):
    s = scambi(chi).get(ordine)
    if s is None:
        return None
    return [s.get(c) for c in campi] if campi else s


def solo(risposta, ordine):
    return {k: v for k, v in risposta.items() if k == ordine}


def messa_da_parte(righe, ordine):
    return next((v for k, v in righe.items() if v[6] == ordine), None)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    t = int(time.time()) - 600
    V, C = banco.VENDE, banco.COMPRA
    K1, K2, KV = banco.CHIAVE_COMPRA, CHIAVE_COMPRA_2, banco.CHIAVE_VENDE
    CHIAVI_C = [K1, K2]        # il profilo di chi compra: indice 1 e 2
    CHIAVI_V = [KV]            # il profilo di chi vende: indice 1

    print("\n1) il server racconta i due giri")
    banco.evento(ORD, "taken", t + 10, "buyer", "take")
    prova("giro 1: chi compra ha preso con la prima chiave",
          ["attesa_mia_fattura", 1, K1], voce(C, ORD, "stato", "giro", "chiave_mia"))
    foto_c_giro1 = solo(scambi(C), ORD)
    foto_v_giro1 = solo(scambi(V), ORD)
    prova("...e chi vende ha la prima controparte", ["attesa_fattura_compratore", K1],
          voce(V, ORD, "stato", "chiave_peer"))
    # il ritiro di chi aveva preso: la 0007 lo manda con TUTTE e due le
    # chiavi, e l'ordine torna nel libro con lo stesso id
    banco.evento(ORD, "canceled", t + 20, "buyer", "republished")
    prova("il ritiro con «republished»: chi aveva preso legge annullato, al giro 1, con l'ora del ritiro",
          ["annullato", 1, K1, t + 20], voce(C, ORD, "stato", "giro", "chiave_mia", "quando"))
    prova("...chi ha pubblicato torna a «pubblicato»", ["pubblicato", True], voce(V, ORD, "stato", "mio"))
    foto_c_annullato = solo(scambi(C), ORD)
    foto_v_tornato = solo(scambi(V), ORD)
    # la seconda presa, con la SECONDA chiave della stessa persona
    banco.evento(ORD, "taken", t + 30, "buyer", "take", buyer=K2)
    banco.evento(ORD, "buyer-invoice-added", t + 40, "buyer", "hold-next", buyer=K2)
    banco.evento(ORD, "hold-invoice-requested", t + 40, "mostro", "invoice", buyer=K2)
    banco.evento(ORD, "hold-invoice-paid", t + 50, "seller", None, buyer=K2)
    banco.evento(ORD, "fiat-sent", t + 60, "buyer", None, buyer=K2)
    prova("giro 2: chi compra legge lo scambio vivo con la seconda chiave e l'ora degli euro",
          ["euro_inviati", 2, K2, t + 60, True], voce(C, ORD, "stato", "giro", "chiave_mia", "quando", "preso"))
    prova("...e chi vende ha la controparte NUOVA, al giro 2",
          ["euro_inviati", 2, K2, KV], voce(V, ORD, "stato", "giro", "chiave_peer", "chiave_mia"))
    foto_c_vivo = solo(scambi(C), ORD)
    foto_v_vivo = solo(scambi(V), ORD)

    print("\n2) il PC di chi ha preso: dalla riga annullata del giro 1 alla presa nuova")
    r1 = client(foto_c_annullato, {}, CHIAVI_C)
    prova("il PC, durante il giro 1, fa nascere la riga annullata con la prima chiave e il giro 1",
          ["annullato", 1, K1, 1, KV, t + 20, "", False], r1.get("righe", {}).get(ORD, r1))
    r2 = client(foto_c_vivo, r1.get("locali", {}), CHIAVI_C)
    nuova = r2.get("righe", {}).get(ORD)
    vecchia = messa_da_parte(r2.get("righe", {}), ORD)
    prova("alla foto nuova la riga nuova nasce: viva, seconda chiave (indice 2), giro 2, con l'ora degli euro",
          ["euro_inviati", 2, K2, 2, KV, t + 60, "", False], nuova or r2)
    prova("...la riga di prima e' sotto «Annullati» col nome `id~…`, al giro 1 con la prima chiave",
          ["annullato", 1, K1, 1, KV, t + 20, ORD, False], vecchia or r2)
    prova("...due righe in tutto, l'ascolto segue la sola chiave nuova, il diario dice il segno",
          [2, [K2], True],
          [len(r2.get("righe", {})), r2.get("ascolto"),
           any("presa nuova" in d and "(giro:" in d for d in r2.get("diario", []))])
    r3 = client(foto_c_vivo, r2.get("locali", {}), CHIAVI_C)
    prova("...e la stessa foto, riapplicata, non fa niente di piu'", [[0, 0], 2],
          [r3.get("n"), len(r3.get("righe", {}))])

    print("\n3) la riga come l'aveva il PC di Andrea: annullata, GIA' con la chiave nuova, senza giro")
    legacy = {ORD: {"id": ORD, "lato": "compro", "stato": "annullato", "indice": 2, "pubTrade": K2,
                    "peer": KV, "euro": 10, "metodi": ["SEPA"], "preso": True, "creato": t,
                    "aggiornato": t + 25, "quando": t + 20, "ultimaMossa": t + 20, "fermoA": 1}}
    r = client(foto_c_vivo, legacy, CHIAVI_C)
    prova("il momento del server dopo l'annullo basta: la riga nuova nasce e quella vecchia va da parte",
          [["euro_inviati", 2, K2, 2], ["annullato", 2, K2, 0, ORD], True],
          [(r.get("righe", {}).get(ORD) or [None] * 4)[:4],
           ((messa_da_parte(r.get("righe", {}), ORD) or [None] * 7)[:4]
            + [(messa_da_parte(r.get("righe", {}), ORD) or [None] * 7)[6]]),
           any("(dopo:" in d for d in r.get("diario", []))])
    # ...e se il server fosse in RITARDO sul mio annullo (l'annullo dopo
    # l'ultima cosa che il server sa) non riaprirebbe niente
    tardi = dict(legacy)
    tardi[ORD] = dict(legacy[ORD], ultimaMossa=t + 70, quando=t + 70)
    r = client(foto_c_vivo, tardi, CHIAVI_C)
    prova("...mentre un server in ritardo sul mio annullo non riapre niente",
          [1, "annullato", None], [len(r.get("righe", {})), r.get("righe", {}).get(ORD, [None])[0],
                                    messa_da_parte(r.get("righe", {}), ORD)])

    print("\n4) il dispositivo di chi ha pubblicato che ha perso il giro")
    m1 = client(foto_v_giro1, {}, CHIAVI_V)
    prova("durante il giro 1 la riga del mio ordine ha la prima controparte",
          ["attesa_fattura_compratore", 1, KV, 1, K1], (m1.get("righe", {}).get(ORD) or [None] * 5)[:5])
    # la riga tiene anche cose della presa di prima: una hold e il «preso»
    loc = m1.get("locali", {})
    loc[ORD]["hold"] = {"bolt11": "lnbc-del-giro-1"}
    m2 = client(foto_v_vivo, loc, CHIAVI_V)
    rm = m2.get("righe", {}).get(ORD) or [None] * 8
    prova("alla foto nuova la riga riparte IN PLACE: controparte nuova, giro 2, stato e ora degli euro, stessa chiave",
          ["euro_inviati", 1, KV, 2, K2, t + 60, "", False], rm)
    prova("...una riga sola, senza la hold del giro prima, e il diario dice «ripreso»",
          [1, False, True],
          [len(m2.get("righe", {})), "hold" in m2.get("locali", {}).get(ORD, {}),
           any("ripreso" in d and "(giro:" in d for d in m2.get("diario", []))])
    # il dispositivo che ha visto il ritorno in vetrina ma non la presa
    # dopo: la riga e' a «pubblicato», e porta ANCORA la controparte di
    # prima (il ritiro della 0007 viaggia con tutt'e due le chiavi, e il
    # server le tiene finche' un evento non le riscrive) — alla foto
    # nuova e' il segno 'chiave' a farla ripartire
    mt = client(foto_v_tornato, {}, CHIAVI_V)
    prova("chi ha visto solo il ritorno in vetrina ha la riga «pubblicato», con la controparte di prima",
          ["pubblicato", K1], [(mt.get("righe", {}).get(ORD) or [None] * 5)[0], (mt.get("righe", {}).get(ORD) or [None] * 5)[4]])
    mt2 = client(foto_v_vivo, mt.get("locali", {}), CHIAVI_V)
    prova("...e alla foto nuova riparte in place (il giro, che la riga porta, parla per primo): controparte e giro nuovi",
          ["euro_inviati", 2, K2, True],
          [(mt2.get("righe", {}).get(ORD) or [None] * 5)[i] for i in (0, 3, 4)]
          + [any("ripreso" in d and "(giro:" in d for d in mt2.get("diario", []))])

    print("\n5) l'eco vecchia non riporta indietro")
    r = client(foto_c_annullato, r2.get("locali", {}), CHIAVI_C)
    prova("la foto del giro 1 sul PC gia' al giro 2: la riga viva resta com'e', e lo dice",
          [["euro_inviati", 2, K2, 2], 2, 1],
          [(r.get("righe", {}).get(ORD) or [None] * 4)[:4], len(r.get("righe", {})),
           sum(1 for d in r.get("diario", []) if "un'altra presa" in d)])
    r = client(foto_v_giro1, m2.get("locali", {}), CHIAVI_V)
    prova("...e la foto del giro 1 sul dispositivo di chi ha pubblicato, gia' al giro 2: ferma, controparte nuova",
          ["euro_inviati", K2, 2, 1],
          [(r.get("righe", {}).get(ORD) or [None] * 5)[0], (r.get("righe", {}).get(ORD) or [None] * 5)[4],
           (r.get("righe", {}).get(ORD) or [None] * 5)[3],
           sum(1 for d in r.get("diario", []) if "un'altra presa" in d)])

    print("\n6) la restore con l'indice piu' alto")
    miei = {ORD: {"indice": 2, "stato": "fiat-sent", "identita": "P"}}
    r = client(foto_c_vivo, r1.get("locali", {}), CHIAVI_C, miei=miei)
    prova("la restore (indice 2 > 1, fiat-sent) mette da parte la riga vecchia e l'archivio fa nascere la nuova",
          [["euro_inviati", 2, K2, 2], ["annullato", 1, K1], True],
          [(r.get("righe", {}).get(ORD) or [None] * 4)[:4],
           (messa_da_parte(r.get("righe", {}), ORD) or [None] * 3)[:3],
           any("ripresa" in d and "presa nuova" in d and "2 > 1" in d for d in r.get("diario", []))])

    print("\n7) le lapidi e la ✕")
    adesso = int(time.time())
    r = client(foto_c_vivo, {}, CHIAVI_C, lapidi={ORD: {"s": adesso + 1000, "g": 1}})
    prova("la lapide della ✕ sul giro 1 non ferma la nascita del giro 2", "euro_inviati",
          (r.get("righe", {}).get(ORD) or [None])[0])
    r = client(foto_c_vivo, {}, CHIAVI_C, lapidi={ORD: {"s": adesso + 1000, "g": 2}})
    prova("...quella sul giro 2 si'", {}, r.get("righe"))
    r = client(foto_c_vivo, {}, CHIAVI_C, lapidi={ORD: adesso + 1000})
    prova("...e una lapide vecchia (senza giro) ferma come sempre", {}, r.get("righe"))
    con = banco.con_db()
    try:
        esito = banco.SRV._togli_scambio_p2p(con, C, ORD, adesso)
    finally:
        con.close()
    prova("per il server la ✕ di chi compra sulla riga vecchia e' «aperto»: lo scambio vive",
          ["aperto", "euro_inviati"], [esito.get("esito"), esito.get("stato")])

    print("\n8) lo scaduto di chi aveva preso (taker-timeout) rimette nel libro allo stesso modo")
    banco.evento(SCAD, "taken", t + 100, "buyer", "take")
    foto_s1 = solo(scambi(C), SCAD)
    banco.evento(SCAD, "expired", t + 110, "mostro", "taker-timeout")
    prova("scaduto: chi aveva preso legge annullato al giro 1, chi ha pubblicato «pubblicato»",
          ["annullato", 1, "pubblicato"],
          voce(C, SCAD, "stato", "giro") + voce(V, SCAD, "stato"))
    foto_s_ann = solo(scambi(C), SCAD)
    banco.evento(SCAD, "taken", t + 120, "buyer", "take", buyer=K2)
    prova("la ripresa: giro 2 con la seconda chiave", ["attesa_mia_fattura", 2, K2],
          voce(C, SCAD, "stato", "giro", "chiave_mia"))
    s1 = client(foto_s_ann, client(foto_s1, {}, CHIAVI_C).get("locali", {}), CHIAVI_C)
    prova("il PC: la riga del giro 1 va ad annullata", "annullato", (s1.get("righe", {}).get(SCAD) or [None])[0])
    s2 = client(solo(scambi(C), SCAD), s1.get("locali", {}), CHIAVI_C)
    prova("...e alla ripresa la nuova nasce con la seconda chiave, la vecchia da parte",
          [["attesa_mia_fattura", 2, K2, 2], ["annullato", 1, K1, 1, SCAD]],
          [(s2.get("righe", {}).get(SCAD) or [None] * 4)[:4],
           ((messa_da_parte(s2.get("righe", {}), SCAD) or [None] * 7)[:4]
            + [(messa_da_parte(s2.get("righe", {}), SCAD) or [None] * 7)[6]])])

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
