# -*- coding: utf-8 -*-
"""
I MIEI SCAMBI SU OGNI DISPOSITIVO, SUL SERVER VERO (24 set 2026).

Dal campo: Andrea pubblica dall'app Android, Alan prende dal tablet; nella
mini app Telegram dello STESSO account di Andrea lo scambio non c'era, e
dal tablet di Alan e' anche sparito. La riga vive nel localStorage del
dispositivo che l'ha aperto; il server invece sa tutto (patch 0007), e
da oggi lo dice: `/api/p2p/scambi`.

`prove.py` difende i giudici estratti e il client (`prove_scambi_
ovunque`). Qui gira la ROTTA VERA, sul database vero e usa-e-getta, con
gli eventi di mostrod passati dai due giudici della rotta degli eventi,
e si cammina uno scambio intero guardandolo dai DUE lati a ogni passo:

  1. l'ordine in vetrina: chi l'ha pubblicato lo vede «pubblicato», chi
     compra e l'estraneo non vedono niente;
  2. la presa di chi compra: «di' dove ricevere» a lui, «aspetta la
     fattura» a chi vende — e le due trade key stanno in `p2p_scambi`,
     ognuna sul suo lato;
  3. fattura data (hold-next) e garanzia chiesta nello stesso secondo:
     tocca a chi vende bloccare; garanzia pagata: attivo per tutt'e due;
  4. euro inviati, liberati, il pagamento non passato (a chi compra la
     fattura nuova, chi vende resta in pagamento e lo sa), la fattura
     nuova, il pagamento riuscito coi tre importi;
  5. un ordine preso e poi TORNATO in vetrina: chi ha pubblicato torna a
     «pubblicato», chi aveva preso non e' piu' una parte e non lo vede;
  6. un ordine preso e poi annullato: annullato per tutt'e due, e con
     `preso` vero — e' storico, non un ritiro;
  7. un annullato di due mesi fa resta fuori (lo storico e' di 30 giorni);
  8. la rotta non guarda la leva del P2P, e risponde `no-store`.

E DAL 26 SET 2026 («Annulla» che dice non riuscito ma annulla, e
l'ordine annullato che non compariva sotto «Annullati»), con gli eventi
nella forma che la patch 0007 manda DAVVERO:

  9. il mio ordine mai preso annullato col mio «Annulla» (`canceled`,
     `pending`, la sola chiave di chi l'ha pubblicato), lo scaduto nel
     libro (`expired`, `book`) e l'annullato che il server sa dal solo
     libro: per chi l'ha pubblicato annullati, suoi, mai presi — per
     gli altri niente;
 10. IL CLIENT VERO SULLA RISPOSTA VERA: le funzioni di miniapp.html,
     girate in node sul JSON della rotta, fanno NASCERE quei tre sul
     dispositivo che non li ha mai visti, annullati e sotto «Annullati»
     (non nella lista di tutti i giorni), con la lapide e fuori dal
     libro; e sul dispositivo che li aveva «pubblicati» la riga passa ad
     annullata e la card esce dal libro;
 11. gli stati che l'attesa dei gesti rilegge quando la risposta di
     mostrod tarda — euro inviati, annullo chiesto e proposto, annullato
     d'accordo, liberati, disputa, e il ritiro di chi aveva preso (che la
     0007 manda con TUTTE e due le chiavi) — sono quelli che la tabella
     del client aspetta per quel gesto;
 12. (27 set 2026) le cifre di un annullato — l'intervallo e il premio
     che l'archivio porta — e il passo su cui si e' fermato, dal client
     vero.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_scambi_ovunque.py
"""

import asyncio
import json
import os
import sys
import time

import collaudo_pagamento_p2p as banco

ATTIVO = "5a1e0000-aaaa-4a2b-9c3d-0000000000a1"
TORNATO = "5a1e0000-bbbb-4a2b-9c3d-0000000000b1"
MORTO = "5a1e0000-cccc-4a2b-9c3d-0000000000c1"
VECCHIO = "5a1e0000-dddd-4a2b-9c3d-0000000000d1"
VETRINA = "5a1e0000-eeee-4a2b-9c3d-0000000000e1"
# 26 set 2026: l'annullo che rilegge e l'«Annullati» su ogni dispositivo
RITIRO = "5a1e0000-ffff-4a2b-9c3d-0000000000f1"
# 27 set 2026: un intervallo col premio, annullato dopo la garanzia
FORBICE = "5a1e0000-ffff-4a2b-9c3d-0000000000f8"
SCADUTO = "5a1e0000-ffff-4a2b-9c3d-0000000000f2"
MORTO_NEL_LIBRO = "5a1e0000-ffff-4a2b-9c3d-0000000000f3"
GESTI = "5a1e0000-ffff-4a2b-9c3d-0000000000f4"
LIBERATO = "5a1e0000-ffff-4a2b-9c3d-0000000000f5"
LASCIATO = "5a1e0000-ffff-4a2b-9c3d-0000000000f6"
DISPUTA = "5a1e0000-ffff-4a2b-9c3d-0000000000f7"


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for ordine, stato in ((ATTIVO, "in-progress"), (TORNATO, "in-progress"),
                          (VETRINA, "pending")):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,?,'sell',1,"
                    "15000,'10,00 €','[\"SEPA\", \"Revolut\"]')",
                    (ordine, banco.VENDE, adesso - 3600, stato))
    # il «buy» girato: lo pubblica chi compra, lo prende chi vende
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                "lato,maker,sats,euro,metodi) VALUES(?,?,?,'in-progress','buy',1,"
                "15000,'10,00 €','[\"SEPA\"]')",
                (MORTO, banco.COMPRA, adesso - 3600))
    # l'annullato di due mesi fa: fuori dallo storico. Nasce dal
    # database, che la rotta degli eventi non accetta un'ora cosi'
    # lontana (P2P_EVENTO_OROLOGIO_S)
    vecchio = adesso - 70 * 86400
    con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                "lato,maker,euro) VALUES(?,?,?,'canceled','sell',1,'7,00 €')",
                (VECCHIO, banco.VENDE, vecchio))
    con.execute("INSERT OR REPLACE INTO p2p_scambi(ordine,compratore,venditore,"
                "preso_dal,giro,aggiornato,chiave_compratore,chiave_venditore) "
                "VALUES(?,?,?,'buyer',1,?,?,?)",
                (VECCHIO, banco.COMPRA, banco.VENDE, vecchio + 100,
                 banco.CHIAVE_COMPRA, banco.CHIAVE_VENDE))
    con.execute("INSERT OR IGNORE INTO p2p_momenti(ordine,momento,quando,fonte,"
                "giro,attore,dettaglio,arrivato) VALUES(?,'preso',?,'mostro',1,'buyer','',?)",
                (VECCHIO, vecchio + 50, vecchio + 50))
    con.execute("INSERT OR IGNORE INTO p2p_momenti(ordine,momento,quando,fonte,"
                "giro,attore,dettaglio,arrivato) VALUES(?,'annullato',?,'mostro',1,'seller','',?)",
                (VECCHIO, vecchio + 100, vecchio + 100))
    # 26 set 2026: tre ordini in vetrina di chi vende, piu' uno che il
    # libro sa gia' morto (l'evento della 0007 perso per strada), e tre
    # da prendere per i gesti
    for ordine, stato in ((RITIRO, "pending"), (SCADUTO, "pending"),
                          (MORTO_NEL_LIBRO, "canceled"), (GESTI, "in-progress"),
                          (LIBERATO, "in-progress"), (LASCIATO, "in-progress"),
                          (DISPUTA, "in-progress"), (FORBICE, "in-progress")):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,"
                    "lato,maker,sats,euro,metodi) VALUES(?,?,?,?,'sell',1,"
                    "0,'20,00 €','[\"Revolut\"]')",
                    (ordine, banco.VENDE, adesso - 3000, stato))
    # l'intervallo e il premio come li scrive il lettore del libro
    con.execute("UPDATE p2p_ordini SET euro='da 20,00 a 100,00 €', premio=-2.5 "
                "WHERE ordine=?", (FORBICE,))
    con.commit()
    con.close()


def js(mini, firma, fine="\n}\n"):
    """Un pezzo di miniapp.html, dalla firma alla fine data compresa."""
    i = mini.index(firma)
    return mini[i:mini.index(fine, i) + len(fine)]


def client_sulla_risposta(risposta, locali, libro):
    """IL CLIENT VERO SULLA RISPOSTA VERA: le funzioni di miniapp.html che
    un dispositivo usa per l'archivio del server, girate in node sul JSON
    della rotta. `locali` e' l'archivio del dispositivo prima, `libro` gli
    id del libro in pagina. Torna, per ogni riga dopo l'adozione: stato,
    ritirato, gruppo, se si vede a filtro spento, se sotto «Annullati»,
    la lapide — e il libro dopo."""
    import shutil
    import subprocess
    import tempfile
    node = shutil.which("node")
    if not node:
        return {"ERRORE": "node non c'e'"}
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    riga = lambda firma: mini[mini.index(firma):mini.index("\n", mini.index(firma))]
    pezzi = "\n".join([
        "const _box = {}; const localStorage = {getItem: k => (k in _box ? _box[k] : null),"
        " setItem: (k, v) => { _box[k] = String(v); }};",
        "const chiaveP2P = k => k; const window = {NostrTools: {}};",
        "let archivio = {}; function ordiniP2P(){ return archivio; }"
        " function scriviOrdineP2P(o){ archivio[o.id] = o; return o; }",
        "let p2pMieiOrdini = null, p2pLibro = null, p2pScambiServer = null;",
        "function diarioP2P(){}",
        # un dispositivo che la chiave di QUESTI ordini non la sa: le
        # righe nascono da guardare, ed e' il caso piu' stretto
        "function mazzoMostro(){ return null; } function chiaveScambio(){ throw new Error('senza mazzo'); }",
        "function azioniDisponibili(){ return ''; }",
        riga("const P2P_FINALI = "), riga("const P2P_LIBRO_FINESTRA_S = "),
        riga("const MOSTRO_LAPIDI_CHIAVE = "),
        js(mini, "const STATI_P2P = {", "\n};\n"),
        # (27 set 2026) la scala dei passi: dove si e' fermato un annullato
        js(mini, "const P2P_PROGRESSO = {", "\n};\n"),
        js(mini, "function fermoAnnulloP2P(o){"),
        mini[mini.index("const P2P_DA_RESTORE = {"):
             mini.index("\n}\n", mini.index("function riprendiDaRestoreP2P(o, statoMostro){")) + 3],
        mini[mini.index("const P2P_INDICE_CERCA_MAX = "):
             mini.index("\n}\n", mini.index("function adottaScambiServerP2P(locali){")) + 3],
        mini[mini.index("function p2pRitirato(o){"):mini.index("\n}", mini.index("function p2pRitirato(o){")) + 2],
        js(mini, "function lapidiP2P(){"), js(mini, "function lapideP2P(o){"),
        js(mini, "function lapidataP2P(id){"), js(mini, "function archiviaRitiratoP2P(id){"),
        js(mini, "function giroArchiviatoP2P(locali, id){"),
        js(mini, "function gruppoScambioP2P(o){"), js(mini, "function passaStatoMieiP2P(o, f){"),
    ])
    prog = pezzi + """
const dati = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf-8'));
archivio = dati.locali;
p2pScambiServer = dati.risposta;
p2pLibro = {ordini: dati.libro.map(id => ({id}))};
adottaScambiServerP2P(archivio);
const out = {righe: {}, libro: p2pLibro.ordini.map(x => x.id)};
for (const id of Object.keys(archivio)) {
  const o = archivio[id];
  out.righe[id] = [o.stato, p2pRitirato(o), gruppoScambioP2P(o), passaStatoMieiP2P(o, []),
                   passaStatoMieiP2P(o, ['morti']), lapidataP2P(id)];
}
/* (27 set 2026) le cifre e il passo su cui si e' fermato */
out.cifre = {};
for (const id of Object.keys(archivio)) {
  const o = archivio[id];
  out.cifre[id] = [o.euro, o.euroMax || 0, o.premium || 0, fermoAnnulloP2P(o)];
}
process.stdout.write(JSON.stringify(out));
"""
    cart = tempfile.mkdtemp(prefix="annullati_")
    try:
        p = os.path.join(cart, "client.js")
        d = os.path.join(cart, "dati.json")
        open(p, "w", encoding="utf-8").write(prog)
        open(d, "w", encoding="utf-8").write(json.dumps(
            {"risposta": risposta, "locali": locali, "libro": libro}))
        r = subprocess.run([node, p, d], capture_output=True, text=True,
                           timeout=60, encoding="utf-8")
    finally:
        shutil.rmtree(cart, ignore_errors=True)
    if r.returncode or not r.stdout.strip():
        return {"ERRORE": (r.stderr or "")[-400:]}
    return json.loads(r.stdout)


def esiti_del_client():
    """La tabella `ESITI_GESTO_P2P` di miniapp.html: gesto -> stati."""
    import re
    mini = open(os.path.join(banco.QUI, "miniapp.html"), encoding="utf-8").read()
    t = js(mini, "const ESITI_GESTO_P2P = {", "\n};\n")
    return {k: re.findall(r"'(\w+)'", v)
            for k, v in re.findall(r"^  '?([\w-]+)'?: \{stati: \[([^\]]*)\]", t, re.M)}


def scambi(chi):
    """La rotta vera, come la vede `chi`: `{ordine: {...}}` piu' il
    Cache-Control sotto `__cache`."""
    banco.come(chi)
    r = asyncio.run(banco.SRV.scambi_p2p())
    fuori = json.loads(r.body)
    fuori["__cache"] = r.headers.get("cache-control", "")
    return fuori


def voce(chi, ordine, *campi):
    s = scambi(chi).get("scambi", {}).get(ordine)
    if s is None:
        return None
    return [s.get(c) for c in campi] if campi else s


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    prova = banco.prova
    t = int(time.time()) - 600
    V, C, E = banco.VENDE, banco.COMPRA, banco.ESTRANEO
    KV, KC = banco.CHIAVE_VENDE, banco.CHIAVE_COMPRA

    print("\n1) l'ordine in vetrina")
    prova("chi l'ha pubblicato lo vede «pubblicato», suo, mai preso, senza chiavi",
          ["pubblicato", "vendo", True, False, "", ""],
          voce(V, VETRINA, "stato", "lato", "mio", "preso", "chiave_mia", "chiave_peer"))
    prova("...con cifra, sats e metodi del libro", [10.0, 15000, ["SEPA", "Revolut"]],
          voce(V, VETRINA, "euro", "sats", "metodi"))
    prova("chi compra non lo vede", None, voce(C, VETRINA))
    prova("l'estraneo non vede niente di niente", {}, scambi(E)["scambi"])
    prova("la risposta e' no-store", "no-store", scambi(V)["__cache"])

    print("\n2) la presa di chi compra")
    banco.evento(ATTIVO, "taken", t + 10, "buyer", "take")
    prova("a chi compra: di' dove ricevere i sats", ["attesa_mia_fattura", "compro", False, True],
          voce(C, ATTIVO, "stato", "lato", "mio", "preso"))
    prova("a chi vende: aspetta la fattura", ["attesa_fattura_compratore", "vendo", True, True],
          voce(V, ATTIVO, "stato", "lato", "mio", "preso"))
    prova("le due trade key, ognuna sul suo lato", [[KV, KC], [KC, KV]],
          [voce(V, ATTIVO, "chiave_mia", "chiave_peer"), voce(C, ATTIVO, "chiave_mia", "chiave_peer")])
    con = banco.con_db()
    r = con.execute("SELECT chiave_compratore, chiave_venditore FROM p2p_scambi "
                    "WHERE ordine=?", (ATTIVO,)).fetchone()
    con.close()
    prova("...e stanno in p2p_scambi", [KC, KV], [r["chiave_compratore"], r["chiave_venditore"]])
    prova("l'estraneo continua a non vedere", None, voce(E, ATTIVO))

    print("\n3) la fattura, la garanzia")
    banco.evento(ATTIVO, "buyer-invoice-added", t + 20, "buyer", "hold-next")
    banco.evento(ATTIVO, "hold-invoice-requested", t + 20, "mostro", "invoice")
    prova("fattura data e garanzia chiesta insieme: chi vende blocca, chi compra aspetta",
          ["attesa_mia_hold", "attesa_hold_venditore"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    banco.evento(ATTIVO, "hold-invoice-paid", t + 30, "seller")
    prova("garanzia pagata: attivo per tutt'e due, con l'ora di mostrod",
          [["attivo", t + 30], ["attivo", t + 30]],
          [voce(V, ATTIVO, "stato", "quando"), voce(C, ATTIVO, "stato", "quando")])
    prova("la cronaca viaggia intera", ["take", "hold-next", "invoice", ""],
          [voce(V, ATTIVO, "momenti")[0][0]["d"]] + [m["d"] for m in voce(V, ATTIVO, "momenti")[0][1:]])

    print("\n4) euro inviati, liberati, il pagamento che non passa, riuscito")
    banco.evento(ATTIVO, "fiat-sent", t + 40, "buyer")
    prova("euro inviati", ["euro_inviati", "euro_inviati"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    banco.evento(ATTIVO, "released", t + 50, "seller", None,
                 sats=7300, sats_buyer=7228, sats_seller=7372)
    prova("liberati: in pagamento per tutt'e due", ["rilasciato", "rilasciato"],
          [voce(V, ATTIVO, "stato")[0], voce(C, ATTIVO, "stato")[0]])
    prova("...coi tre importi, ognuno il suo", [[7300, 7372], [7300, 7228]],
          [voce(V, ATTIVO, "sats_ordine", "sats_miei"), voce(C, ATTIVO, "sats_ordine", "sats_miei")])
    banco.evento(ATTIVO, "payout-failed", t + 60, "mostro", "NO_ROUTE")
    prova("pagamento non passato: a chi compra la fattura nuova, chi vende in pagamento — e il fatto lo leggono tutt'e due",
          [["fattura_nuova", True], ["rilasciato", True]],
          [voce(C, ATTIVO, "stato", "payout_fallito"), voce(V, ATTIVO, "stato", "payout_fallito")])
    banco.evento(ATTIVO, "buyer-invoice-added", t + 70, "buyer", "new-invoice")
    prova("la fattura nuova: di nuovo in pagamento, e chi vende non lo legge piu' fallito",
          [["rilasciato"], ["rilasciato", False]],
          [voce(C, ATTIVO, "stato"), voce(V, ATTIVO, "stato", "payout_fallito")])
    banco.evento(ATTIVO, "success", t + 80, "mostro", None,
                 sats=7300, sats_buyer=7228, sats_seller=7372)
    prova("riuscito: concluso per tutt'e due, datato al success",
          [["concluso", t + 80], ["concluso", t + 80]],
          [voce(V, ATTIVO, "stato", "quando"), voce(C, ATTIVO, "stato", "quando")])

    print("\n5) preso e poi tornato in vetrina")
    banco.evento(TORNATO, "taken", t + 100, "buyer", "take")
    prova("preso: chi compra e' una parte", "attesa_mia_fattura", voce(C, TORNATO, "stato")[0])
    banco.evento(TORNATO, "canceled", t + 110, "buyer", "republished", buyer=None)
    prova("tornato: chi ha pubblicato torna a «pubblicato», con l'ora del ritorno",
          ["pubblicato", True, t + 110], voce(V, TORNATO, "stato", "mio", "quando"))
    prova("...e chi aveva preso non e' piu' una parte: non lo vede", None, voce(C, TORNATO))
    prova("...ne' la chiave dell'altra parte resta a chi vende", "", voce(V, TORNATO, "chiave_peer")[0])

    print("\n6) preso e poi annullato: storico, non ritiro")
    banco.evento(MORTO, "taken", t + 200, "seller", "take")
    banco.evento(MORTO, "hold-invoice-requested", t + 200, "mostro", "take")
    prova("preso da chi vende (un buy girato): tocca a lui bloccare, e chi compra — che l'ha pubblicato — aspetta",
          [["attesa_mia_hold", "vendo", False], ["attesa_hold_venditore", "compro", True]],
          [voce(V, MORTO, "stato", "lato", "mio"), voce(C, MORTO, "stato", "lato", "mio")])
    banco.evento(MORTO, "canceled", t + 220, "buyer")
    prova("annullato per tutt'e due, e PRESO: e' storico, non un ritiro",
          [["annullato", True], ["annullato", True]],
          [voce(V, MORTO, "stato", "preso"), voce(C, MORTO, "stato", "preso")])

    print("\n7) lo storico e' di trenta giorni")
    prova("l'annullato di due mesi fa resta fuori, per tutt'e due", [None, None],
          [voce(V, VECCHIO), voce(C, VECCHIO)])
    miei = {ATTIVO, TORNATO, MORTO, VECCHIO, VETRINA}
    prova("chi vende vede quattro di questi scambi, chi compra due",
          [sorted([ATTIVO, MORTO, TORNATO, VETRINA]), sorted([ATTIVO, MORTO])],
          [sorted(o for o in scambi(V)["scambi"] if o in miei),
           sorted(o for o in scambi(C)["scambi"] if o in miei)])

    print("\n8) la leva non c'entra")
    banco.SRV.P2P_ATTIVO = False
    prova("a leva spenta la rotta risponde lo stesso: chi ha uno scambio a meta' lo vede",
          "concluso", voce(V, ATTIVO, "stato")[0])
    banco.SRV.P2P_ATTIVO = True

    print("\n9) il mio ordine mai preso: annullato, scaduto, morto nel libro")
    # la forma VERA: `cancel_pending_order_from_maker` manda `canceled`
    # col dettaglio `pending`, l'attore e' chi l'ha pubblicato (la sua
    # trade key e' il `seller` di un sell), e un ordine in vetrina ha
    # solo quella chiave
    banco.evento(RITIRO, "canceled", t + 300, "seller", "pending", buyer=None)
    prova("«Annulla» su un mio ordine mai preso: annullato, mio, mai preso, con l'ora di mostrod",
          ["annullato", True, False, t + 300], voce(V, RITIRO, "stato", "mio", "preso", "quando"))
    banco.evento(SCADUTO, "expired", t + 310, "mostro", "book", buyer=None)
    prova("...lo scaduto nel libro pure", ["annullato", True, False, t + 310],
          voce(V, SCADUTO, "stato", "mio", "preso", "quando"))
    prova("...e l'evento perso per strada: il server lo sa dal libro", ["annullato", True, False],
          voce(V, MORTO_NEL_LIBRO, "stato", "mio", "preso"))
    prova("chi compra e l'estraneo non vedono nessuno dei tre", [None, None, None, None, None, None],
          [voce(C, o) for o in (RITIRO, SCADUTO, MORTO_NEL_LIBRO)]
          + [voce(E, o) for o in (RITIRO, SCADUTO, MORTO_NEL_LIBRO)])

    print("\n10) il client vero sulla risposta vera: «Annullati» su ogni dispositivo")
    tre = (RITIRO, SCADUTO, MORTO_NEL_LIBRO)
    risposta = {o: v for o, v in scambi(V)["scambi"].items() if o in tre}
    nuovo = client_sulla_risposta(risposta, {}, list(tre) + [VETRINA])
    SOTTO_ANNULLATI = ["annullato", True, "morti", False, True, True]
    prova("il dispositivo che non li ha mai visti li fa NASCERE annullati, sotto «Annullati» e non "
          "nella lista di tutti i giorni, con la lapide",
          {o: SOTTO_ANNULLATI for o in tre}, nuovo.get("righe", nuovo))
    prova("...e le loro card escono dal libro in pagina (resta quella viva)", [VETRINA],
          nuovo.get("libro"))
    # il dispositivo da cui erano stati pubblicati: la riga c'era, «pubblicato»
    locali = {o: {"id": o, "lato": "vendo", "stato": "pubblicato", "mio": True, "indice": 0,
                  "pubTrade": "", "creato": t} for o in tre}
    risposta = {o: v for o, v in scambi(V)["scambi"].items() if o in tre}
    vecchio = client_sulla_risposta(risposta, locali, list(tre) + [VETRINA])
    prova("il dispositivo che li aveva «pubblicati»: la riga passa ad annullata e va sotto «Annullati»",
          {o: SOTTO_ANNULLATI for o in tre}, vecchio.get("righe", vecchio))
    prova("...e le card escono dal libro anche li'", [VETRINA], vecchio.get("libro"))

    print("\n11) gli stati che l'attesa dei gesti rilegge")
    esiti = esiti_del_client()
    prova("la tabella del client c'e', coi sei gesti",
          ["accetta", "chiedi", "dispute", "fiat-sent", "release", "ritira"], sorted(esiti))
    fatto = lambda gesto, chi, ordine: (voce(chi, ordine, "stato") or [""])[0] in esiti.get(gesto, [])
    banco.evento(GESTI, "taken", t + 400, "buyer", "take")
    banco.evento(GESTI, "buyer-invoice-added", t + 410, "buyer", "hold-next")
    banco.evento(GESTI, "hold-invoice-requested", t + 410, "mostro", "invoice")
    banco.evento(GESTI, "hold-invoice-paid", t + 420, "seller")
    banco.evento(GESTI, "fiat-sent", t + 430, "buyer")
    prova("«ho inviato gli euro»: per chi compra il server dice un esito del gesto", True,
          fatto("fiat-sent", C, GESTI))
    banco.evento(GESTI, "cancel-requested", t + 440, "buyer")
    prova("«chiedi di annullare»: a chi l'ha chiesto «annullo chiesto», un esito del gesto; "
          "all'altro «annullo proposto»", [True, "annullo_proposto"],
          [fatto("chiedi", C, GESTI), voce(V, GESTI, "stato")[0]])
    banco.evento(GESTI, "canceled", t + 450, "seller", "cooperative")
    prova("«accetta di annullare»: annullato per tutt'e due, esito dell'accetta e della richiesta",
          [True, True], [fatto("accetta", V, GESTI), fatto("chiedi", C, GESTI)])
    banco.evento(LIBERATO, "taken", t + 500, "buyer", "take")
    banco.evento(LIBERATO, "hold-invoice-paid", t + 510, "seller")
    banco.evento(LIBERATO, "fiat-sent", t + 520, "buyer")
    banco.evento(LIBERATO, "released", t + 530, "seller", None,
                 sats=7300, sats_buyer=7228, sats_seller=7372)
    prova("«libera i sats»: per chi vende un esito del gesto", True, fatto("release", V, LIBERATO))
    banco.evento(DISPUTA, "taken", t + 540, "buyer", "take")
    banco.evento(DISPUTA, "hold-invoice-paid", t + 550, "seller")
    banco.evento(DISPUTA, "dispute-opened", t + 560, "buyer")
    prova("la disputa: un esito del gesto per chi l'ha aperta", True, fatto("dispute", C, DISPUTA))
    # IL RITIRO DI CHI AVEVA PRESO, nella forma vera: la 0007 lo manda
    # PRIMA di cancellare le sue chiavi (`cancel_order_by_taker_inner`),
    # quindi l'evento porta TUTT'E DUE — il passo 5 qui sopra simula un
    # evento senza la sua, che mostrod non manda
    banco.evento(LASCIATO, "taken", t + 600, "buyer", "take")
    banco.evento(LASCIATO, "canceled", t + 610, "buyer", "republished")
    prova("chi aveva preso e ha chiesto di annullare lo vede annullato: il suo «chiedi» e' fatto",
          ["annullato", True], [voce(C, LASCIATO, "stato")[0], fatto("chiedi", C, LASCIATO)])
    prova("...e chi l'aveva pubblicato lo ritrova nel libro", "pubblicato", voce(V, LASCIATO, "stato")[0])

    print("\n12) le cifre di un annullato e dove si e' fermato (27 set 2026)")
    banco.evento(FORBICE, "taken", t + 700, "buyer", "take")
    banco.evento(FORBICE, "hold-invoice-paid", t + 710, "seller")
    banco.evento(FORBICE, "cancel-requested", t + 720, "buyer")
    banco.evento(FORBICE, "canceled", t + 730, "seller", "cooperative")
    prova("l'archivio porta i due capi e il premio col segno",
          ["annullato", 20.0, 100.0, -2.5], voce(V, FORBICE, "stato", "euro", "euro_max", "premium"))
    prova("...e il ritiro dell'ordine in vetrina porta la sua cifra", [20.0, 0.0, 0.0],
          voce(V, RITIRO, "euro", "euro_max", "premium"))
    risposta = {o: v for o, v in scambi(V)["scambi"].items() if o in (FORBICE, RITIRO)}
    nato = client_sulla_risposta(risposta, {}, [])
    prova("il client vero: nasce con le cifre, e si e' fermato A GARANZIA (2) o NEL LIBRO (0)",
          {FORBICE: [20, 100, -2.5, 2], RITIRO: [20, 0, 0, 0]}, nato.get("cifre", nato))

    print(f"\n{banco.PASSATE} ok, {banco.FALLITE} NO")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
