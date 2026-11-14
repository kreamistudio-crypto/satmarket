# -*- coding: utf-8 -*-
"""LA MANCIA AL VENDITORE, fatta girare per davvero (14 nov 2026,
cantiere mancia-venditore).

`prove.py` guarda i pezzi uno per uno (il giudice, le parole, la
preimage). Qui gira la STORIA sulle funzioni vere del server, su un
database usa-e-getta:

  · chi compra un ordine pagato vede la mancia possibile in
    /api/orders, chi vende no (finche' non ne riceve una);
  · la fattura la chiede `invoice_da_ln_address` VERO al wallet del
    venditore (di cartone, al posto di httpx), e il `verify` di LUD-21
    arriva fino alla riga SOLO se passa la guardia;
  · i no: chi vende, l'ordine da pagare, le cifre fuori misura, il
    venditore senza indirizzo, la leva spenta, il wallet che conia
    un'altra cifra, il nostro nodo che tace;
  · la riga sale e non scende (chiesta → dichiarata → arrivata), e
    l'avviso a chi vende parte UNA volta sola, con le parole giuste;
  · la regressione: gli incassi chiamano `invoice_da_ln_address` senza
    `extra`, e per loro non cambia niente.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server; nessuna rete (httpx e la guardia sono di
cartone), nessun LNbits, nessun avviso spedito.

USO:  python collaudo_mancia.py
"""

import asyncio
import hashlib
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
AVVISI = []
BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}

# lo stato del wallet di cartone del venditore
WALLET = {"verify": "https://wallet.esempio/verify/{h}", "pagate": set(),
          "bara": False, "chiamate": []}
PREIMAGE = {}          # payment_hash -> preimage, per le fatture coniate


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def rifiuto(nome, codice, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        c = getattr(e, "status_code", None)
        t = str(getattr(e, "detail", e))
        if c == codice and (not dentro or dentro.lower() in t.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso {codice} {dentro!r}\n      avuto:  {c} {t!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def _gruppi(dati: bytes) -> list:
    n, bits, fuori = 0, 0, []
    for b in dati:
        n = (n << 8) | b
        bits += 8
        while bits >= 5:
            bits -= 5
            fuori.append((n >> bits) & 31)
    if bits:
        fuori.append((n << (5 - bits)) & 31)
    return fuori


def _campo(tipo, gruppi):
    return [BECH32.index(tipo), len(gruppi) // 32, len(gruppi) % 32] + gruppi


def fattura_di_cartone(sats, payment_hash):
    """Una BOLT11 vera nella FORMA (hrp con l'importo, il campo `p`),
    firma e checksum di zeri: chi la legge ci trova quel che ci
    troverebbe in una vera."""
    corpo = [0] * 7 + _campo("p", _gruppi(bytes.fromhex(payment_hash)))
    corpo += _campo("d", _gruppi(b"mancia"))
    corpo += [0] * 110
    return f"lnbc{sats * 10}n1" + "".join(BECH32[g] for g in corpo)


class _Risposta:
    def __init__(self, codice, corpo):
        self.status_code = codice
        self._corpo = corpo
        self.content = b"x"

    def raise_for_status(self):
        if self.status_code >= 300:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._corpo


class HttpxDiCartone:
    """Al posto di `httpx` dentro il server: il citofono LNURL del
    wallet del venditore, il suo callback e il suo verify (LUD-21)."""

    class AsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, params=None):
            WALLET["chiamate"].append(url)
            if "/.well-known/lnurlp/" in url:
                return _Risposta(200, {"tag": "payRequest",
                                       "callback": "https://wallet.esempio/cb",
                                       "minSendable": 1000,
                                       "maxSendable": 10**11})
            if url.endswith("/cb"):
                sats = int(params["amount"]) // 1000
                n = len(PREIMAGE) + 1
                pre = hashlib.sha256(f"pre{n}".encode()).hexdigest()
                h = hashlib.sha256(bytes.fromhex(pre)).hexdigest()
                PREIMAGE[h] = pre
                pr = fattura_di_cartone(sats + (1 if WALLET["bara"] else 0), h)
                corpo = {"pr": pr, "routes": []}
                if WALLET["verify"]:
                    corpo["verify"] = WALLET["verify"].format(h=h)
                return _Risposta(200, corpo)
            if "/verify/" in url:
                h = url.rsplit("/", 1)[1]
                pagata = h in WALLET["pagate"]
                return _Risposta(200, {"status": "OK", "settled": pagata,
                                       "preimage": PREIMAGE[h] if pagata else None,
                                       "pr": ""})
            return _Risposta(404, {})


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script deve "
                         "installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-mancia-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def zitta(chi=None, testo="", *a, **k):
        AVVISI.append((chi, testo))

    async def guardia(url):
        # la guardia vera risolve il DNS: qui si giudica la forma, e
        # l'indirizzo di casa resta fuori come farebbe quella vera
        return url.startswith("https://") and "127.0.0.1" not in url

    async def importo(bolt11, dec=None, cassaforte=""):
        if MUTO[0]:
            raise server.LnbitsMuto("il nodo tace")
        m = server.zap_leggi_bolt11(bolt11).get("msat")
        return None if m is None else m // 1000

    server.notifica = zitta
    server.httpx = HttpxDiCartone
    server._url_lnurl_ammesso = guardia
    server.importo_invoice = importo
    return db


MUTO = [False]


def chi(u):
    SRV.verifica_utente = lambda *a, **k: u


def chiama(fn, *args, corpo=None):
    async def leggi(_req):
        return corpo or {}
    SRV.leggi_json = leggi
    return asyncio.run(fn(*args, None))


def ordini(u):
    chi(u)
    return {r["id"]: r for r in SRV.miei_ordini(0, "", "")}


def semina(db):
    con = sqlite3.connect(db)
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,ln_address) "
                "VALUES(222,'Vende','vende','vende@wallet.esempio')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username) "
                "VALUES(111,'Compra','compra')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username) "
                "VALUES(333,'Senza','senza')")
    con.execute("INSERT OR REPLACE INTO annunci(id,titolo,descrizione,prezzo_sats,"
                "venditore_id,stato,categoria,quantita,consegna,zona,valuta) "
                "VALUES(1,'Il libro','x',11000,222,'attivo','Libri',5,"
                "'spedizione','Pavia (PV)','sats')")
    for oid, vend, stato in ((1, 222, "locked"), (2, 222, "creato"),
                             (3, 333, "released"), (4, 222, "refunded"),
                             (5, 222, "released")):
        con.execute("INSERT OR REPLACE INTO ordini(id,annuncio_id,compratore_id,"
                    "venditore_id,prezzo_sats,stato,creato,aggiornato) "
                    "VALUES(?,1,111,?,11000,?,1,1)", (oid, vend, stato))
    con.commit()
    con.close()


def main():
    print("=" * 58)
    print("  LA MANCIA AL VENDITORE — il giro vero")
    print("=" * 58)
    db = avvio()
    semina(db)
    vero = sqlite3.connect(db)
    vero.row_factory = sqlite3.Row

    def riga(mid):
        return dict(vero.execute("SELECT * FROM mance WHERE id=?", (mid,)).fetchone())

    print("\n[la lista ordini: chi compra la vede, chi vende no]")
    o = ordini(COMPRA)
    prova("ordine pagato: la mancia si puo' lasciare", True,
          (o[1].get("mancia") or {}).get("possibile"))
    prova("il tetto viaggia col bottone", 100_000, o[1]["mancia"]["max"])
    prova("senza zap@ configurato, niente invito a Barattolo", False,
          o[1]["mancia"]["zap_barattolo"])
    prova("l'indirizzo del venditore NON esce", False,
          "vende@wallet.esempio" in repr(o[1]))
    prova("ordine da pagare: niente mancia", None, o[2].get("mancia"))
    prova("venditore senza indirizzo: niente mancia", None, o[3].get("mancia"))
    prova("ordine rimborsato: niente mancia", None, o[4].get("mancia"))
    prova("a chi vende, senza mance, niente riquadro", None,
          ordini(VENDE)[1].get("mancia"))

    print("\n[la fattura: dal wallet del venditore, col verify di LUD-21]")
    chi(COMPRA)
    d = chiama(SRV.chiedi_mancia, 1, corpo={"sats": 500})
    prova("torna la fattura da 500 sats", 500,
          SRV.zap_leggi_bolt11(d["invoice"])["msat"] // 1000)
    prova("verificabile: il wallet da' LUD-21", True, d["verificabile"])
    r1 = riga(d["id"])
    prova("la riga nasce «chiesta»", "chiesta", r1["stato"])
    prova("col payment hash letto dalla fattura", True,
          r1["payment_hash"] in PREIMAGE)
    prova("e il verify passato dalla guardia", True,
          r1["verify"].startswith("https://wallet.esempio/verify/"))
    prova("nessun avviso per una fattura solo chiesta", [], AVVISI)
    prova("la partenza e' il citofono LUD-16 del venditore", True,
          "https://wallet.esempio/.well-known/lnurlp/vende" in WALLET["chiamate"])

    print("\n[i no]")
    chi(VENDE)
    rifiuto("chi vende non si lascia una mancia", 400,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 500}))
    chi(COMPRA)
    rifiuto("zero sats", 400,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 0}), "va da")
    rifiuto("sopra il tetto", 400,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 100_001}), "va da")
    rifiuto("cifra che non e' un numero", 400,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": "tanti"}))
    rifiuto("ordine ancora da pagare", 400,
            lambda: chiama(SRV.chiedi_mancia, 2, corpo={"sats": 500}))
    rifiuto("venditore senza Lightning address", 400,
            lambda: chiama(SRV.chiedi_mancia, 3, corpo={"sats": 500}))
    rifiuto("ordine che non esiste", 400,
            lambda: chiama(SRV.chiedi_mancia, 99, corpo={"sats": 500}))
    WALLET["bara"] = True
    rifiuto("il wallet conia un'altra cifra: scartata", 400,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 700}),
            "non ci ha dato una fattura")
    WALLET["bara"] = False
    MUTO[0] = True
    rifiuto("il nostro nodo tace: 503, non e' colpa di nessuno", 503,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 700}),
            "non risponde")
    MUTO[0] = False
    SRV.MANCIA_ATTIVA = False
    rifiuto("leva spenta: la rotta non c'e'", 404,
            lambda: chiama(SRV.chiedi_mancia, 1, corpo={"sats": 500}))
    rifiuto("leva spenta: nemmeno l'esito", 404,
            lambda: chiama(SRV.esito_mancia, 1, d["id"], corpo={}))
    prova("leva spenta: niente bottone in lista", None,
          ordini(COMPRA)[1].get("mancia"))
    SRV.MANCIA_ATTIVA = True
    chi(VENDE)
    rifiuto("l'esito lo dice solo chi l'ha chiesta", 400,
            lambda: chiama(SRV.esito_mancia, 1, d["id"], corpo={"dichiarata": True}))

    print("\n[la riga sale, l'avviso parte una volta]")
    chi(COMPRA)
    e = chiama(SRV.esito_mancia, 1, d["id"],
               corpo={"preimage": "00" * 32})
    prova("preimage sbagliata e verify non pagato: resta chiesta", "chiesta",
          e["stato"])
    e = chiama(SRV.esito_mancia, 1, d["id"], corpo={"dichiarata": True})
    prova("«L'ho pagata»: dichiarata", "dichiarata", e["stato"])
    prova("un avviso a chi vende", 1, len(AVVISI))
    prova("...a chi vende", 222, AVVISI[0][0])
    prova("...che dice di controllare il wallet", True,
          "Controlla il wallet" in AVVISI[0][1] and "500" in AVVISI[0][1])
    e = chiama(SRV.esito_mancia, 1, d["id"], corpo={"dichiarata": True})
    prova("ridirlo non manda un secondo avviso", 1, len(AVVISI))
    WALLET["pagate"].add(r1["payment_hash"])
    e = chiama(SRV.esito_mancia, 1, d["id"], corpo={})
    prova("LUD-21 la vede pagata: arrivata", "arrivata", e["stato"])
    prova("e niente secondo avviso", 1, len(AVVISI))
    e = chiama(SRV.esito_mancia, 1, d["id"], corpo={"dichiarata": True})
    prova("da arrivata non si scende", "arrivata", e["stato"])

    d2 = chiama(SRV.chiedi_mancia, 5, corpo={"sats": 2100})
    h2 = riga(d2["id"])["payment_hash"]
    e = chiama(SRV.esito_mancia, 5, d2["id"], corpo={"preimage": PREIMAGE[h2]})
    prova("con la preimage del wallet collegato: arrivata subito", "arrivata",
          e["stato"])
    prova("avviso «già nel tuo wallet», col titolo", True,
          len(AVVISI) == 2 and "già nel tuo wallet" in AVVISI[1][1]
          and "Il libro" in AVVISI[1][1])
    rifiuto("l'esito di una mancia di un altro ordine no", 400,
            lambda: chiama(SRV.esito_mancia, 1, d2["id"], corpo={}))

    print("\n[il verify fuori dalla guardia non entra]")
    WALLET["verify"] = "https://127.0.0.1:5001/verify/{h}"
    d3 = chiama(SRV.chiedi_mancia, 1, corpo={"sats": 10})
    prova("verify verso casa: non verificabile", False, d3["verificabile"])
    prova("...e la riga non lo tiene", "", riga(d3["id"])["verify"])
    WALLET["verify"] = ""

    print("\n[nell'ordine: le mance lasciate, mai quelle solo chieste]")
    ov = ordini(VENDE)
    prova("chi vende vede la mancia arrivata", [(500, "arrivata")],
          [(m["sats"], m["stato"]) for m in ov[1]["mancia"]["mance"]])
    prova("...e per lui non e' «possibile»", False, ov[1]["mancia"]["possibile"])
    oc = ordini(COMPRA)
    prova("chi compra la vede anche lui", [(500, "arrivata")],
          [(m["sats"], m["stato"]) for m in oc[1]["mancia"]["mance"]])
    prova("sull'ordine concluso: quella da 2100", [2100],
          [m["sats"] for m in oc[5]["mancia"]["mance"]])

    print("\n[regressione: gli incassi non passano extra]")
    WALLET["verify"] = "https://wallet.esempio/verify/{h}"
    pr = asyncio.run(SRV.invoice_da_ln_address("vende@wallet.esempio", 321))
    prova("invoice_da_ln_address senza extra torna la sola fattura", 321,
          SRV.zap_leggi_bolt11(pr)["msat"] // 1000)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
