# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'INDIRIZZO DELLA QUOTA (19 ott 2026) — il giro col
SERVER VERO: swap@barattolo.store, dove SATS Routing manda a fine mese
la quota di Barattolo sugli swap.

`prove.py` guarda i pezzi uno per uno. Qui gira la STORIA, per HTTP
(TestClient, la app vera): un wallet bussa a `/.well-known/lnurlp/swap`,
chiede la fattura al callback, la paga, e l'orologio — un giro alla
volta, chiamato a mano — se ne accorge e manda UN avviso al gruppo
degli admin. Poi i no: la leva spenta, la chiave che e' quella degli
zap, i limiti, una richiesta di zap Nostr, un LNbits che tace. E la
SEPARAZIONE da zap@: acceso anche lui, ognuno conia sul suo wallet,
con la sua chiave e il suo tetto, e l'orologio dell'uno non chiede
mai delle fatture dell'altro.

DI CARTONE C'E' SOLO LNbits, ed e' lo stesso di
`collaudo_indirizzo_lightning`: conia fatture BOLT11 vere nella forma e
ricorda con QUALE chiave e' stato chiamato. Nessuna fattura vera,
nessuna rete: config di cartone e database usa-e-getta dal banco dei
pagamenti, PRIMA dell'import del server.

USO:  python collaudo_indirizzo_swap.py
"""
import asyncio
import contextlib
import hashlib
import io
import json
import sys
import time

import collaudo_lnbits_muto as banco
import collaudo_indirizzo_lightning as cartone

prova = banco.prova

# Le invoice key di cartone. In un DIZIONARIO e posate col setattr: la
# forma `NOME = "valore"` e' quella che lo scanner dei segreti cerca.
CHIAVI = {"SWAP_LNBITS_INVOICE_KEY": "collaudo-usa-e-getta-swap",
          "ZAP_LNBITS_INVOICE_KEY": "collaudo-usa-e-getta-zap"}
URL_NODO = cartone.URL_NODO
FATTURE, CHIAMATE, LNBITS = cartone.FATTURE, cartone.CHIAMATE, cartone.LNBITS
AVVISI = []         # (testo, argomento) di ogni notifica_admin
SRV = None


def righe(tabella, dove="1=1"):
    con = SRV._zap_db()             # le due tabelle nascono a chi arriva prima
    SRV._swap_prepara_tabella(con)
    try:
        return [dict(r) for r in con.execute(
            f"SELECT * FROM {tabella} WHERE {dove} ORDER BY id")]
    finally:
        con.close()


def scrivi(sql, *args):
    con = SRV.db()
    try:
        con.execute(sql, args)
        con.commit()
    finally:
        con.close()


def giro(quale="swap"):
    """Un giro di un orologio, col journal catturato."""
    carta = io.StringIO()
    with contextlib.redirect_stdout(carta):
        if quale == "swap":
            SRV._SWAP_STATO["attesa"] = True
            n = asyncio.run(SRV.giro_swap())
        else:
            SRV._ZAP_STATO["attesa"] = True
            n = asyncio.run(SRV.giro_zap())
    return n, carta.getvalue()


def main():
    global SRV
    print("=" * 58)
    print("  L'INDIRIZZO DELLA QUOTA (swap@) — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = cartone.SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.httpx = cartone.LNbitsDiCartone

    async def avvisa(testo, bottone=None, argomento=""):
        AVVISI.append((testo, argomento))
    SRV.notifica_admin = avvisa
    VIA, CALLBACK = "/.well-known/lnurlp/swap", "/api/lnurl/swap"
    journal = io.StringIO()

    def chiedi(**params):
        with contextlib.redirect_stdout(journal):
            return c.get(CALLBACK, params=params)

    # ---- 1) spento: il mondo di ieri ------------------------------
    print("\n[la leva spenta, la chiave che manca, la chiave degli zap]")
    prova("di serie la leva e' spenta e il tetto e' 2.000.000",
          (False, 2_000_000), (SRV.SWAP_INDIRIZZO_ATTIVO, SRV.swap_max_sats()))
    r = c.get(VIA)
    prova("a leva spenta il citofono risponde 404, nella forma di LUD-06",
          (404, "ERROR"), (r.status_code, r.json().get("status")))
    prova("...e il callback pure", 404,
          c.get(CALLBACK, params={"amount": "21000"}).status_code)
    SRV.SWAP_INDIRIZZO_ATTIVO = True
    SRV.LNBITS_NODO_URL = URL_NODO
    prova("la leva accesa SENZA l'invoice key vale spenta", (False, 404),
          (SRV.swap_vivo(), c.get(VIA).status_code))
    for nome, valore in CHIAVI.items():
        setattr(SRV, nome, valore)
    SRV.SWAP_LNBITS_INVOICE_KEY = CHIAVI["ZAP_LNBITS_INVOICE_KEY"]
    leve = {v["chiave"]: v for v in SRV._swap_quota_leve()}
    prova("con la STESSA chiave del salvadanaio degli zap vale spenta",
          (False, 404), (SRV.swap_vivo(), c.get(VIA).status_code))
    prova("...e il pannello delle leve lo dice, con l'allarme", (True, True),
          (leve["SWAP_LNBITS_INVOICE_KEY"].get("allarme"),
           "STESSA chiave" in leve["SWAP_LNBITS_INVOICE_KEY"].get("nota", "")))
    SRV.SWAP_LNBITS_INVOICE_KEY = CHIAVI["SWAP_LNBITS_INVOICE_KEY"]
    prova("con la chiave del SUO wallet l'indirizzo e' vivo", True,
          SRV.swap_vivo())
    prova("...sullo STESSO LNbits del nodo, se non si dice altro",
          (URL_NODO, CHIAVI["SWAP_LNBITS_INVOICE_KEY"]), SRV.swap_wallet())
    prova("nessuna chiamata a LNbits finora", [], CHIAMATE)

    # ---- 2) il citofono --------------------------------------------
    print("\n[il citofono, senza Nostr]")
    # zap@ acceso anche lui, CON la chiave della piattaforma: e' il caso
    # in cui un citofono che copiasse quello degli zap direbbe allowsNostr
    SRV.ZAP_ATTIVO = True
    SRV.ZAP_NPUB = SRV.hex_to_npub(cartone.PUB_BARATTOLO)
    SRV._NOSTR = (cartone.ChiaveDiCartone(cartone.SK_PIATTAFORMA),
                  cartone.PUB_PIATTAFORMA)
    r = c.get(VIA)
    d = r.json()
    prova("il citofono risponde 200: un payRequest col callback suo",
          (200, "payRequest", "https://barattolo.store/api/lnurl/swap"),
          (r.status_code, d.get("tag"), d.get("callback")))
    prova("...da 1 a 2.000.000 sat, in millisatoshi, commento a 140",
          (1000, 2_000_000_000, 140),
          (d.get("minSendable"), d.get("maxSendable"), d.get("commentAllowed")))
    prova("...con swap@barattolo.store nella metadata",
          [["text/plain", "Quota di SATS Routing a Barattolo"],
           ["text/identifier", "swap@barattolo.store"]],
          json.loads(d["metadata"]))
    prova("...e SENZA i campi Nostr, anche con gli zap Nostr accesi",
          (None, None, True), (d.get("allowsNostr"), d.get("nostrPubkey"),
                               SRV.zap_nostr_vivo()))
    prova("CORS aperto, e in cache per cinque minuti come quello degli zap",
          ("*", "public, max-age=300"),
          (r.headers.get("access-control-allow-origin"),
           r.headers.get("cache-control")))
    h = c.head(VIA)
    prova("la HEAD risponde 200 col corpo vuoto", (200, b""),
          (h.status_code, h.content))
    z = c.get("/.well-known/lnurlp/zap").json()
    prova("zap@ resta com'era: il suo callback, il suo tetto, i suoi campi Nostr",
          ("https://barattolo.store/api/lnurl/zap", 100_000_000, True),
          (z.get("callback"), z.get("maxSendable"), z.get("allowsNostr")))
    prova("ogni altro nome resta un 404", [404, 404, 404],
          [c.get("/.well-known/lnurlp/" + n).status_code
           for n in ("Swap", "swap2", "quota")])
    SRV.SWAP_MAX_SATS = 5_000_000
    prova("il tetto e' una leva: il citofono la legge viva", 5_000_000_000,
          c.get(VIA).json().get("maxSendable"))
    SRV.SWAP_MAX_SATS = 2_000_000

    # ---- 3) la fattura: due milioni sul wallet «swap» -----------------
    print("\n[la fattura, sul wallet «swap»]")
    r = chiedi(amount="2000000000", comment="quota di settembre")
    d = r.json()
    prova("il callback da' la fattura per 2.000.000 sat", (200, []),
          (r.status_code, d.get("routes")))
    letta = SRV.zap_leggi_bolt11(d["pr"])
    prova("...dell'importo chiesto", 2_000_000_000, letta.get("msat"))
    prova("...con l'impronta della metadata DEL CITOFONO di swap@",
          hashlib.sha256(c.get(VIA).json()["metadata"].encode()).hexdigest(),
          letta.get("h"))
    prova("LNbits chiamato UNA volta, con la invoice key del wallet «swap»",
          [("POST", URL_NODO + "/api/v1/payments",
            CHIAVI["SWAP_LNBITS_INVOICE_KEY"])], CHIAMATE)
    f = FATTURE[letta["payment_hash"]]
    prova("...per INCASSARE, con la scadenza di dieci minuti", (False, 600),
          (f["out"], f["scadenza"]))
    riga = righe("swap_quota")[0]
    prova("la riga nasce in attesa nella SUA tabella, col commento",
          ("attesa", 2_000_000, "quota di settembre"),
          (riga["stato"], riga["sats"], riga["commento"]))
    prova("...e nella tabella degli zap non c'e' niente", [], righe("zap"))
    prova("il journal dice i sats e l'inizio della fattura, non il commento",
          (True, False), ("🔄 swap@: fattura da 2.000.000 sats" in journal.getvalue(),
                          "quota di settembre" in journal.getvalue()))

    # ---- 4) i limiti: nessuno arriva a LNbits ------------------------
    print("\n[i limiti, e niente zap Nostr]")
    prima = len(CHIAMATE)
    storti = {"senza importo": {}, "non un numero": {"amount": "ventuno"},
              "sotto il sat": {"amount": "999"}, "zero": {"amount": "0"},
              "non sat interi": {"amount": "1500"},
              "oltre il tetto": {"amount": "2000001000"},
              "commento da 141": {"amount": "21000", "comment": "x" * 141},
              "una richiesta di zap": {"amount": "21000",
                                       "nostr": cartone.richiesta_zap(21000)}}
    esiti = {k: chiedi(**v).json() for k, v in storti.items()}
    prova("ogni richiesta storta e' un errore LUD-06",
          {k: "ERROR" for k in storti}, {k: v.get("status") for k, v in esiti.items()})
    prova("...e nessuna ha coniato", prima, len(CHIAMATE))
    prova("la richiesta di zap ha il suo perche'",
          "Questo indirizzo non riceve zap Nostr: solo pagamenti",
          esiti["una richiesta di zap"].get("reason"))
    prova("il tetto e' detto nel messaggio", "L'importo va da 1 a 2000000 sat",
          esiti["oltre il tetto"].get("reason"))

    # ---- 5) zap@ accanto: ognuno sul suo wallet --------------------------
    print("\n[zap@ accanto, ognuno col suo wallet]")
    rz = c.get("/api/lnurl/zap", params={"amount": "21000"})
    prova("zap@ conia sul SUO salvadanaio", (200, CHIAVI["ZAP_LNBITS_INVOICE_KEY"]),
          (rz.status_code, CHIAMATE[-1][2]))
    prova("...e oltre i 100.000 sat dice no (il tetto alto e' solo di swap@)",
          "ERROR", c.get("/api/lnurl/zap",
                         params={"amount": "2000000000"}).json().get("status"))
    hz = SRV.zap_leggi_bolt11(rz.json()["pr"])["payment_hash"]
    prima = len(CHIAMATE)
    giro("zap")
    chieste_zap = [(u, k) for _, u, k in CHIAMATE[prima:]]
    prova("l'orologio degli zap chiede SOLO della sua fattura, con la sua chiave",
          [(f"{URL_NODO}/api/v1/payments/{hz}", CHIAVI["ZAP_LNBITS_INVOICE_KEY"])],
          chieste_zap)
    scrivi("DELETE FROM zap")

    # ---- 6) il pagamento e l'avviso -----------------------------------
    print("\n[il pagamento, e l'avviso al gruppo]")
    n, out = giro()
    prova("prima del pagamento: niente incassato, niente avviso, in attesa",
          (0, [], "attesa"), (n, AVVISI, righe("swap_quota")[0]["stato"]))
    prima = len(CHIAMATE)
    cartone.paga(letta["payment_hash"])
    n, out = giro()
    prova("pagata: il giro la incassa", (1, "pagato"),
          (n, righe("swap_quota")[0]["stato"]))
    prova("...chiedendo a LNbits con la chiave del wallet «swap»",
          {CHIAVI["SWAP_LNBITS_INVOICE_KEY"]}, {k for _, _, k in CHIAMATE[prima:]})
    prova("...il journal lo dice, coi sats", True,
          "🔄 swap@: arrivati 2.000.000 sats" in out)
    prova("UN avviso, nella stanza 📊 Riepiloghi", (1, "riepiloghi"),
          (len(AVVISI), AVVISI[0][1] if AVVISI else ""))
    testo = AVVISI[0][0] if AVVISI else ""
    pagato_il = righe("swap_quota")[0]["pagato_il"]
    prova("...con l'importo e l'ora del pagamento", True,
          "2.000.000 sats" in testo and "swap@barattolo.store" in testo
          and SRV._quando_appuntamento(pagato_il) in testo)
    prova("...e mai il commento di chi paga", False, "settembre" in testo)
    prova("l'avviso non e' urgente: col gruppo giu' aspetta, non va in privato",
          False, SRV._gruppo_admin_urgente("riepiloghi"))
    n, _ = giro()
    prova("un secondo giro non manda un secondo avviso", (0, 1), (n, len(AVVISI)))

    # ---- 7) LNbits che tace, e la scadenza ------------------------------
    print("\n[LNbits che tace, e la fattura che scade]")
    r = chiedi(amount="50000")
    h2 = SRV.zap_leggi_bolt11(r.json()["pr"])["payment_hash"]
    LNBITS["chiedi"] = 500
    scrivi("UPDATE swap_quota SET scade=scade-10000, creato=creato-10000 "
           "WHERE payment_hash=?", h2)
    SRV._SWAP_VISTI.clear()
    n, out = giro()
    prova("LNbits che tace: niente scade, il journal lo dice", (0, "attesa", True),
          (n, righe("swap_quota", f"payment_hash='{h2}'")[0]["stato"],
           "⚠️ swap@: LNbits non risponde" in out))
    LNBITS["chiedi"] = 200
    SRV._SWAP_VISTI.clear()
    giro()
    prova("LNbits dice «non pagata» a tempo scaduto: la fattura scade",
          ("scaduto", 1), (righe("swap_quota", f"payment_hash='{h2}'")[0]["stato"],
                           len(AVVISI)))
    LNBITS["conia"] = 500
    r = chiedi(amount="21000")
    prova("LNbits che non conia: 503 nella forma di LUD-06, nessuna riga",
          (503, "ERROR", 2), (r.status_code, r.json().get("status"),
                              len(righe("swap_quota"))))
    LNBITS["conia"] = 201

    # ---- 8) il freno e il tetto delle attese ------------------------------
    print("\n[il freno, quello degli zap]")
    SRV._SECCHI.clear()
    SRV._SECCHI["zap:151.38.10.7"] = [time.time(), SRV.FRENI["zap"][0]]
    with contextlib.redirect_stdout(journal):
        r = c.get(CALLBACK, params={"amount": "1000"},
                  headers={"x-forwarded-for": "151.38.10.7"})
    prova("un IP che ha finito i gettoni degli zap e' fermo anche qui",
          (429, "ERROR"), (r.status_code, r.json().get("status")))
    SRV._SECCHI.clear()
    vero, SRV.SWAP_MAX_ATTESA = SRV.SWAP_MAX_ATTESA, 0
    prima = len(CHIAMATE)
    prova("col tetto delle fatture in attesa raggiunto non si conia",
          (429, prima), (chiedi(amount="1000").status_code, len(CHIAMATE)))
    SRV.SWAP_MAX_ATTESA = vero

    # ---- 9) la card dell'admin, le leve, i segreti ----------------------
    print("\n[la card, le leve, i segreti]")
    LNBITS["saldo_msat"] = 2_000_000_000
    S = asyncio.run(SRV.dati_swap_cruscotto())
    prova("la card: saldo vivo, quanti, quanto, il tetto, l'indirizzo",
          (2_000_000, 1, 2_000_000, 2_000_000, "swap@barattolo.store", True),
          (S["saldo_sats"], S["quanti"], S["totale_sats"], S["max_sats"],
           S["indirizzo"], S["vivo"]))
    prova("...con l'ultimo pagamento e il suo commento (che la pagina scappa)",
          [(2_000_000, "quota di settembre")],
          [(u["sats"], u["commento"]) for u in S["ultimi"]])
    prova("il saldo l'ha chiesto al wallet «swap»",
          ("GET", URL_NODO + "/api/v1/wallet", CHIAVI["SWAP_LNBITS_INVOICE_KEY"]),
          CHIAMATE[-1])
    pagina = open("admin.html", encoding="utf-8").read()
    prova("la pagina /admin disegna la card e scappa il commento", True,
          "${cardSwap(D.swap)}" in pagina and "esc(u.commento || '')" in
          pagina[pagina.index("function cardSwap("):])
    prova("il cruscotto resta chiuso a chi non e' admin", True,
          c.get("/api/admin/cruscotto").status_code in (401, 403))
    leve = SRV._swap_quota_leve()
    prova("le leve: tre voci, l'indirizzo acceso senza allarme, il tetto",
          (3, True, False, 2_000_000),
          (len(leve), leve[0]["valore"], bool(leve[0].get("allarme")),
           leve[2]["valore"]))
    chiave = CHIAVI["SWAP_LNBITS_INVOICE_KEY"]
    prova("la invoice key non sta nelle leve, nella card, negli avvisi, nel journal",
          [False, False, False, False],
          [chiave in json.dumps(leve), chiave in json.dumps(S),
           chiave in json.dumps(AVVISI), chiave in journal.getvalue()])
    prova("nessuna chiamata a LNbits e' stata un pagamento in uscita", True,
          all(f["out"] is False for f in FATTURE.values()))
    prova("il journal non porta mai una fattura intera", False,
          any(f"lnbc{f['sats'] * 10}n1" in journal.getvalue()
              for f in FATTURE.values()))
    import logging
    rec = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
        ("151.38.10.7:5555", "GET",
         "/api/lnurl/swap?amount=21000&comment=un%20segreto", "1.1", 200), None)
    logging.getLogger("uvicorn.access").filter(rec)
    prova("il registro degli accessi non porta la query del callback",
          '151.38.10.7:5555 - "GET /api/lnurl/swap?… HTTP/1.1" 200',
          rec.getMessage())

    SRV.SWAP_INDIRIZZO_ATTIVO = False
    prova("spenta di nuovo la leva: 404, e la card resta (ci sono righe)",
          (404, 404, False),
          (c.get(VIA).status_code, chiedi(amount="1000").status_code,
           asyncio.run(SRV.dati_swap_cruscotto())["vivo"]))
    prova("...e zap@ non se ne accorge", 200,
          c.get("/.well-known/lnurlp/zap").status_code)
    scrivi("DELETE FROM swap_quota")
    prova("spenta e senza righe: niente card", None,
          asyncio.run(SRV.dati_swap_cruscotto()))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
