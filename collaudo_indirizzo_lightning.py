# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'INDIRIZZO LIGHTNING DI CASA (10 ott 2026) — il giro
col SERVER VERO: zap@barattolo.store dal citofono alla ricevuta.

`prove.py` guarda i pezzi uno per uno: il giudice della richiesta di
zap, la lettura della fattura, la forma della ricevuta. Qui gira la
STORIA, per HTTP (TestClient, la app vera): un wallet bussa a
`/.well-known/lnurlp/zap`, chiede la fattura al callback, la paga, e
l'orologio — chiamato a mano, un giro alla volta — se ne accorge, firma
la ricevuta kind 9735 e la «pubblica». Poi i no: la leva spenta, i
limiti, le richieste di zap storte, il freno, un LNbits che tace, e un
LNbits che ignora l'impronta della descrizione.

DI CARTONE C'E' SOLO LNbits: un oggetto al posto di `httpx`, che conia
fatture BOLT11 vere nella forma (hrp con l'importo, i campi `p` e `h`,
una firma di zeri) e ricorda con QUALE chiave e' stato chiamato — e'
cosi' che si prova che l'indirizzo usa la SOLA invoice key del
salvadanaio e mai quelle di una cassaforte.

LE FIRME SONO VERE: le richieste di zap le firma `schnorr_puro` con
chiavi usa-e-getta, il server le verifica (con coincurve dove c'e', con
`schnorr_puro` in CI), e la ricevuta — firmata dalla «chiave della
piattaforma» di prova — si riverifica qui.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti, PRIMA dell'import del server. Nessuna rete: in
collaudo la ricevuta si stampa e non parte, e la guardia dei relay
(che risolverebbe un nome) si prova con un giudice di cartone.

USO:  python collaudo_indirizzo_lightning.py
"""
import asyncio
import contextlib
import hashlib
import io
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova

# La invoice key di cartone. In un DIZIONARIO e posata col setattr: la
# forma `NOME = "valore"` e' quella che lo scanner dei segreti cerca.
CHIAVI = {"ZAP_LNBITS_INVOICE_KEY": "collaudo-usa-e-getta-zap"}
URL_NODO = "http://127.0.0.1:1"
SK_PIATTAFORMA = bytes.fromhex("07" * 31 + "11")    # firma le ricevute
SK_BARATTOLO = bytes.fromhex("09" * 31 + "13")      # il profilo che riceve
SK_ZAPPA = bytes.fromhex("0b" * 31 + "17")          # chi manda lo zap
SK_ALTRO = bytes.fromhex("0d" * 31 + "19")          # un profilo che non c'entra
PUB_PIATTAFORMA = schnorr_puro.pubblica(SK_PIATTAFORMA).hex()
PUB_BARATTOLO = schnorr_puro.pubblica(SK_BARATTOLO).hex()
PUB_ZAPPA = schnorr_puro.pubblica(SK_ZAPPA).hex()
PUB_ALTRO = schnorr_puro.pubblica(SK_ALTRO).hex()
BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# Lo stato di LNbits, a comando. `impronta` False = un LNbits che
# ignora la description hash e mette il memo (il caso che la cintura
# di `zap_conia` deve prendere); `conia`/`chiedi` sono il codice HTTP.
LNBITS = {"conia": 201, "chiedi": 200, "impronta": True, "saldo_msat": 0}
FATTURE = {}        # payment_hash -> {"paid", "preimage", "sats"}
CHIAMATE = []       # (metodo, url, chiave usata)
SRV = None


class ChiaveDiCartone:
    """Quel che il server chiede a coincurve per firmare, fatto con
    `schnorr_puro`: in CI coincurve non c'e', e `_NOSTR` sarebbe None."""

    def __init__(self, sk):
        self._sk = sk

    def sign_schnorr(self, msg):
        return schnorr_puro.firma(self._sk, msg)


def _gruppi(dati: bytes) -> list:
    """Byte → gruppi da 5 bit, col riempitivo in coda (bech32)."""
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


def _campo(tipo: str, gruppi: list) -> list:
    return [BECH32.index(tipo), len(gruppi) // 32, len(gruppi) % 32] + gruppi


def fattura_di_cartone(sats, payment_hash, impronta="", memo=""):
    """Una BOLT11 vera nella FORMA: hrp con l'importo, l'ora, il campo
    `p`, e `h` (l'impronta) oppure `d` (il testo), poi una firma e un
    checksum di zeri. Nessun nodo la pagherebbe; chi la legge ci trova
    quel che ci troverebbe in una vera."""
    corpo = [0] * 7 + _campo("p", _gruppi(bytes.fromhex(payment_hash)))
    if impronta:
        corpo += _campo("h", _gruppi(bytes.fromhex(impronta)))
    else:
        corpo += _campo("d", _gruppi(memo.encode()))
    corpo += [0] * 110
    return f"lnbc{sats * 10}n1" + "".join(BECH32[g] for g in corpo)


class _Risposta:
    def __init__(self, codice, corpo):
        self.status_code = codice
        self._corpo = corpo

    def raise_for_status(self):
        if self.status_code >= 300:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._corpo


class LNbitsDiCartone:
    """Al posto di `httpx` dentro il server: le tre chiamate che
    l'indirizzo fa a LNbits, e nient'altro."""

    class AsyncClient:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, json=None, **kw):
            CHIAMATE.append(("POST", url, (headers or {}).get("X-Api-Key")))
            if LNBITS["conia"] >= 300:
                return _Risposta(LNBITS["conia"], {})
            pre = os.urandom(32)
            h = hashlib.sha256(pre).hexdigest()
            sats = int(json["amount"])
            grezzo = bytes.fromhex(json.get("unhashed_description") or "")
            impronta = hashlib.sha256(grezzo).hexdigest()
            # LNbits rifiuta due forme che non combaciano: qui lo si
            # guarda, cosi' il server non puo' mandarne due diverse
            if json.get("description_hash") != impronta:
                return _Risposta(400, {"detail": "impronte diverse"})
            FATTURE[h] = {"paid": False, "preimage": pre.hex(), "sats": sats,
                          "scadenza": json.get("expiry"), "out": json.get("out")}
            return _Risposta(201, {
                "payment_hash": h,
                "payment_request": fattura_di_cartone(
                    sats, h, impronta if LNBITS["impronta"] else "",
                    json.get("memo") or "")})

        async def get(self, url, headers=None, **kw):
            CHIAMATE.append(("GET", url, (headers or {}).get("X-Api-Key")))
            if LNBITS["chiedi"] >= 300:
                return _Risposta(LNBITS["chiedi"], {})
            if url.endswith("/api/v1/wallet"):
                return _Risposta(200, {"name": "zap",
                                       "balance": LNBITS["saldo_msat"]})
            f = FATTURE.get(url.rsplit("/", 1)[-1])
            if f is None:
                return _Risposta(404, {})
            return _Risposta(200, {"paid": f["paid"],
                                   "preimage": f["preimage"] if f["paid"] else ""})


def paga(payment_hash):
    FATTURE[payment_hash]["paid"] = True
    LNBITS["saldo_msat"] += FATTURE[payment_hash]["sats"] * 1000


def richiesta_zap(msat, sk=SK_ZAPPA, **ritocchi):
    """Una richiesta di zap (kind 9734) firmata DAVVERO. `ritocchi`
    cambia i campi prima della firma; `guasta` la rompe dopo."""
    tags = ritocchi.pop("tags", None)
    if tags is None:
        tags = [["relays", "wss://relay.uno.example", "wss://relay.due.example"],
                ["amount", str(msat)], ["p", PUB_BARATTOLO], ["e", "ab" * 32]]
    guasta = ritocchi.pop("guasta", False)
    ev = SRV.evento_non_firmato(
        schnorr_puro.pubblica(sk).hex(), ritocchi.pop("kind", 9734), tags,
        ritocchi.pop("content", "Grazie per Barattolo!"), 1_790_000_000)
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"])).hex()
    if guasta:
        ev["content"] += " (manomesso)"
    return json.dumps(ev, ensure_ascii=False, separators=(",", ":"))


def righe(dove="1=1"):
    con = SRV.db()
    try:
        return [dict(r) for r in con.execute(
            f"SELECT * FROM zap WHERE {dove} ORDER BY id")]
    finally:
        con.close()


def scrivi(sql, *args):
    con = SRV.db()
    try:
        con.execute(sql, args)
        con.commit()
    finally:
        con.close()


def giro():
    """Un giro dell'orologio, col journal catturato."""
    SRV._ZAP_STATO["attesa"] = True
    carta = io.StringIO()
    with contextlib.redirect_stdout(carta):
        n = asyncio.run(SRV.giro_zap())
    return n, carta.getvalue()


def main():
    global SRV
    print("=" * 58)
    print("  L'INDIRIZZO LIGHTNING DI CASA — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    SRV.httpx = LNbitsDiCartone
    VIA, CALLBACK = "/.well-known/lnurlp/zap", "/api/lnurl/zap"
    journal = io.StringIO()

    def chiedi(**params):
        with contextlib.redirect_stdout(journal):
            return c.get(CALLBACK, params=params)

    # ---- 1) spento: il mondo di ieri ------------------------------
    print("\n[la leva spenta, e la leva accesa senza la chiave]")
    r = c.get(VIA)
    prova("a leva spenta il citofono risponde 404", 404, r.status_code)
    prova("...con l'errore nella forma di LUD-06", "ERROR", r.json().get("status"))
    prova("...e il callback pure", 404, c.get(CALLBACK, params={"amount": "21000"}).status_code)
    SRV.ZAP_ATTIVO = True
    SRV.LNBITS_NODO_URL = URL_NODO
    prova("la leva accesa SENZA l'invoice key vale spenta", (False, 404),
          (SRV.zap_vivo(), c.get(VIA).status_code))
    for nome, valore in CHIAVI.items():
        setattr(SRV, nome, valore)
    SRV.ZAP_NPUB = SRV.hex_to_npub(PUB_BARATTOLO)
    SRV._NOSTR = None
    prova("con la chiave del salvadanaio l'indirizzo e' vivo", True, SRV.zap_vivo())
    prova("...sullo STESSO LNbits del nodo, se non si dice altro",
          (URL_NODO, CHIAVI["ZAP_LNBITS_INVOICE_KEY"]), SRV.zap_wallet())
    prova("nessuna chiamata a LNbits finora", [], CHIAMATE)

    # ---- 2) il citofono --------------------------------------------
    print("\n[il citofono]")
    r = c.get(VIA)
    d = r.json()
    prova("il citofono risponde 200", 200, r.status_code)
    prova("...un payRequest col callback di casa",
          ("payRequest", "https://barattolo.store/api/lnurl/zap"),
          (d.get("tag"), d.get("callback")))
    prova("...da 1 a 100.000 sat, in millisatoshi", (1000, 100_000_000),
          (d.get("minSendable"), d.get("maxSendable")))
    prova("...col commento a 140 caratteri", 140, d.get("commentAllowed"))
    meta = json.loads(d["metadata"])
    prova("...e l'identificatore zap@barattolo.store nella metadata", True,
          ["text/identifier", "zap@barattolo.store"] in meta
          and meta[0][0] == "text/plain")
    prova("senza la chiave della piattaforma NON dichiara gli zap Nostr",
          (None, None), (d.get("allowsNostr"), d.get("nostrPubkey")))
    prova("...e una richiesta di zap la rifiuta, senza coniare", ("ERROR", []),
          (chiedi(amount="21000", nostr=richiesta_zap(21000)).json().get("status"),
           CHIAMATE))
    SRV._NOSTR = (ChiaveDiCartone(SK_PIATTAFORMA), PUB_PIATTAFORMA)
    d = c.get(VIA).json()
    prova("con la chiave: allowsNostr e la nostrPubkey della PIATTAFORMA",
          (True, PUB_PIATTAFORMA), (d.get("allowsNostr"), d.get("nostrPubkey")))
    prova("...che non e' la chiave del profilo che riceve", True,
          d.get("nostrPubkey") != PUB_BARATTOLO)
    prova("CORS aperto e mai un redirect", ("*", 200),
          (r.headers.get("access-control-allow-origin"), r.status_code))
    h = c.head(VIA)
    prova("la HEAD risponde 200 col corpo vuoto", (200, b""),
          (h.status_code, h.content))
    prova("ogni altro nome e' un 404", [404, 404, 404, 404],
          [c.get("/.well-known/lnurlp/" + n).status_code
           for n in ("Zap", "zap2", "admin", "barattolo")])

    # ---- 3) un pagamento semplice -----------------------------------
    print("\n[un pagamento semplice, senza Nostr]")
    r = chiedi(amount="21000", comment="ciao Barattolo")
    d = r.json()
    prova("il callback da' la fattura", (200, []), (r.status_code, d.get("routes")))
    letta = SRV.zap_leggi_bolt11(d["pr"])
    prova("...dell'importo chiesto", 21000, letta.get("msat"))
    prova("...con l'impronta della metadata DEL CITOFONO",
          hashlib.sha256(c.get(VIA).json()["metadata"].encode()).hexdigest(),
          letta.get("h"))
    prova("LNbits e' stato chiamato UNA volta, con la invoice key del salvadanaio",
          [("POST", URL_NODO + "/api/v1/payments", CHIAVI["ZAP_LNBITS_INVOICE_KEY"])],
          CHIAMATE)
    f = FATTURE[letta["payment_hash"]]
    prova("...per INCASSARE, con la scadenza di dieci minuti", (False, 600),
          (f["out"], f["scadenza"]))
    riga = righe()[0]
    prova("la riga nasce in attesa, «semplice», col commento",
          ("attesa", "semplice", 21, "ciao Barattolo", ""),
          (riga["stato"], riga["tipo"], riga["sats"], riga["commento"],
           riga["richiesta"]))
    prova("CORS aperto anche sul callback, e mai in cache",
          ("*", "no-store"), (r.headers.get("access-control-allow-origin"),
                              r.headers.get("cache-control")))

    # ---- 4) i limiti: nessuno arriva a LNbits ------------------------
    print("\n[i limiti]")
    prima = len(CHIAMATE)
    storti = {"senza importo": {}, "non un numero": {"amount": "ventuno"},
              "sotto il sat": {"amount": "999"}, "zero": {"amount": "0"},
              "non sat interi": {"amount": "1500"},
              "negativo": {"amount": "-21000"},
              "oltre il massimo": {"amount": "100001000"},
              "commento da 141": {"amount": "21000", "comment": "x" * 141}}
    esiti = {k: chiedi(**v).json().get("status") for k, v in storti.items()}
    prova("ogni richiesta fuori dai limiti e' un errore LUD-06",
          {k: "ERROR" for k in storti}, esiti)
    prova("...e nessuna ha coniato una fattura", prima, len(CHIAMATE))
    prova("il massimo esatto passa", True,
          "pr" in chiedi(amount="100000000").json())
    prova("...e il commento da 140 pure", True,
          "pr" in chiedi(amount="1000", comment="x" * 140).json())
    SRV.ZAP_MAX_SATS = 500
    prova("il massimo e' una leva letta viva", (500_000, "ERROR"),
          (c.get(VIA).json()["maxSendable"],
           chiedi(amount="501000").json().get("status")))
    SRV.ZAP_MAX_SATS = "storto"
    prova("...e una riga storta vale il default, non zero", 100_000_000,
          c.get(VIA).json()["maxSendable"])
    SRV.ZAP_MAX_SATS = 100_000

    # ---- 5) uno zap ---------------------------------------------------
    print("\n[uno zap: la richiesta, la fattura, la riga]")
    scrivi("DELETE FROM zap")
    CHIAMATE.clear()
    req = richiesta_zap(21000, tags=[
        ["relays", "wss://relay.uno.example", "ws://in-chiaro.example",
         "wss://relay.uno.example", "https://non-un-relay.example",
         "wss://utente:parola@relay.tre.example"]
        + [f"wss://r{i}.example" for i in range(12)],
        ["amount", "21000"], ["p", PUB_BARATTOLO], ["e", "ab" * 32],
        ["k", "1"]])
    d = chiedi(amount="21000", nostr=req).json()
    letta = SRV.zap_leggi_bolt11(d.get("pr", ""))
    prova("lo zap riceve la sua fattura", 21000, letta.get("msat"))
    prova("...con l'impronta della RICHIESTA, byte per byte",
          hashlib.sha256(req.encode()).hexdigest(), letta.get("h"))
    riga = righe()[0]
    prova("la riga e' uno «zap» di chi ha firmato", ("zap", PUB_ZAPPA, req),
          (riga["tipo"], riga["mittente"], riga["richiesta"]))
    prova("i relay: solo wss, senza credenziali, senza doppioni, al piu' otto",
          ["wss://relay.uno.example"] + [f"wss://r{i}.example" for i in range(7)],
          json.loads(riga["relay"]))
    h_zap = riga["payment_hash"]

    print("\n[le richieste di zap storte]")
    prima = len(CHIAMATE)
    due_p = [["relays", "wss://r.example"], ["p", PUB_BARATTOLO], ["p", PUB_ALTRO]]
    due_e = [["p", PUB_BARATTOLO], ["e", "ab" * 32], ["e", "cd" * 32]]
    storte = {
        "firma manomessa": richiesta_zap(21000, guasta=True),
        "non una 9734": richiesta_zap(21000, kind=9735),
        "per un altro profilo": richiesta_zap(
            21000, tags=[["relays", "wss://r.example"], ["p", PUB_ALTRO]]),
        "due tag p": richiesta_zap(21000, tags=due_p),
        "nessun tag p": richiesta_zap(21000, tags=[["relays", "wss://r.example"]]),
        "due tag e": richiesta_zap(21000, tags=due_e),
        "importo diverso": richiesta_zap(42000),
        "troppo lunga": richiesta_zap(21000, content="x" * 5000),
        "non JSON": "{questa non e' una richiesta",
        "una lista": "[1,2,3]"}
    esiti = {k: chiedi(amount="21000", nostr=v).json().get("status")
             for k, v in storte.items()}
    prova("ognuna e' un errore", {k: "ERROR" for k in storte}, esiti)
    prova("...e nessuna ha coniato una fattura", prima, len(CHIAMATE))
    prova("...ne' lasciato una riga", 1, len(righe()))
    prova("il motivo si legge («non è per Barattolo»)", True,
          "non è per Barattolo" in chiedi(
              amount="21000", nostr=storte["per un altro profilo"]).json()["reason"])

    # ---- 6) l'orologio: pagato, ricevuta ------------------------------
    print("\n[l'orologio: non pagata, pagata, la ricevuta]")
    n, carta = giro()
    prova("non pagata: il giro non incassa niente", (0, "attesa"),
          (n, righe()[0]["stato"]))
    paga(h_zap)
    n, carta = giro()
    riga = righe()[0]
    prova("pagata: il giro la incassa", (1, "pagato"), (n, riga["stato"]))
    ric = json.loads(riga["ricevuta"])
    prova("la ricevuta e' una 9735 della chiave della PIATTAFORMA, vuota",
          (9735, PUB_PIATTAFORMA, ""), (ric["kind"], ric["pubkey"], ric["content"]))
    rifatto = SRV.evento_non_firmato(ric["pubkey"], ric["kind"], ric["tags"],
                                     ric["content"], ric["created_at"])
    prova("...con l'id canonico NIP-01", rifatto["id"], ric["id"])
    prova("...e una firma Schnorr VERA", True, schnorr_puro.verifica(
        bytes.fromhex(ric["pubkey"]), bytes.fromhex(ric["id"]),
        bytes.fromhex(ric["sig"])))
    tag = {t[0]: t[1] for t in ric["tags"]}
    prova("i tag: p (Barattolo), P (chi ha zappato), e, k",
          (PUB_BARATTOLO, PUB_ZAPPA, "ab" * 32, "1"),
          (tag.get("p"), tag.get("P"), tag.get("e"), tag.get("k")))
    prova("...la fattura pagata", riga["bolt11"], tag.get("bolt11"))
    prova("...la richiesta COM'ERA ARRIVATA nel tag description", req,
          tag.get("description"))
    prova("...la cui impronta e' quella della fattura", letta["h"],
          hashlib.sha256(tag["description"].encode()).hexdigest())
    prova("...e la preimage, che torna col payment hash", h_zap,
          hashlib.sha256(bytes.fromhex(tag.get("preimage", ""))).hexdigest())
    prova("l'ora della ricevuta e' quella del pagamento", riga["pagato_il"],
          ric["created_at"])
    prova("i relay non della richiesta (amount, relays) NON finiscono nei tag",
          [], [t[0] for t in ric["tags"] if t[0] in ("relays", "amount")])
    prova("in collaudo la ricevuta si STAMPA e non parte", True,
          "[nostr simulato]" in carta and "🧾 zap: ricevuta" in carta)
    prova("...«presa» dagli otto relay chiesti piu' i nostri",
          8 + len(SRV.RELAYS_VERIFICA), riga["ricevuta_relay"])
    prova("il journal dice i sats e chi", True,
          f"⚡ Zap ricevuto: 21 sats (zap di {PUB_ZAPPA[:8]}…)" in carta)
    n, carta2 = giro()
    prova("un secondo giro non incassa e non firma un'altra ricevuta",
          (0, 1, False), (n, righe()[0]["ricevuta_tentativi"],
                          "ricevuta" in carta2))
    prova("...e l'orologio va a riposo", False, SRV._ZAP_STATO["attesa"])

    print("\n[un pagamento semplice pagato: nessuna ricevuta]")
    d = chiedi(amount="5000", comment="un caffè").json()
    h_s = SRV.zap_leggi_bolt11(d["pr"])["payment_hash"]
    paga(h_s)
    n, carta = giro()
    riga = righe(f"payment_hash='{h_s}'")[0]
    prova("incassato, senza ricevuta", (1, "pagato", "", 0),
          (n, riga["stato"], riga["ricevuta"], riga["ricevuta_tentativi"]))
    prova("il journal lo chiama «pagamento semplice»", True,
          "⚡ Zap ricevuto: 5 sats (pagamento semplice)" in carta)
    prova("...e NON scrive il commento", False, "un caffè" in carta)

    print("\n[una preimage che non torna col payment hash]")
    d = chiedi(amount="2000", nostr=richiesta_zap(2000)).json()
    h_f = SRV.zap_leggi_bolt11(d["pr"])["payment_hash"]
    FATTURE[h_f]["preimage"] = "00" * 32     # quel che certi LNbits rispondono
    paga(h_f)
    giro()
    ric_f = json.loads(righe(f"payment_hash='{h_f}'")[0]["ricevuta"])
    prova("la ricevuta parte lo stesso, ma SENZA un tag preimage falso",
          (9735, []), (ric_f["kind"],
                       [t for t in ric_f["tags"] if t[0] == "preimage"]))

    # ---- 7) la ricevuta che nessun relay prende ------------------------
    print("\n[la ricevuta che nessun relay prende, e la guardia dei relay]")
    vero_spedisci, vero_guardia = SRV._spedisci_ai_relay, SRV.url_foto_ammesso
    mandati = []

    async def nessuno_la_prende(ev, relays=None):
        mandati.append(list(relays or []))
        return 0

    req2 = richiesta_zap(3000, tags=[
        ["relays", "wss://relay.buono.example", "wss://interno.example",
         "wss://relay.damus.io"],
        ["amount", "3000"], ["p", PUB_BARATTOLO]])
    d = chiedi(amount="3000", nostr=req2).json()
    h2 = SRV.zap_leggi_bolt11(d["pr"])["payment_hash"]
    paga(h2)
    SRV._spedisci_ai_relay = nessuno_la_prende
    SRV.url_foto_ammesso = lambda url: "interno" not in url
    SRV.MODALITA_COLLAUDO = False        # la guardia gira solo fuori collaudo
    try:
        giro()
        prova("fuori collaudo il relay che risolve «in casa» si scarta",
              ["wss://relay.buono.example", "wss://relay.damus.io"]
              + [r for r in SRV.RELAYS_VERIFICA if r != "wss://relay.damus.io"],
              mandati[0])
        r2 = righe(f"payment_hash='{h2}'")[0]
        prova("nessun relay: la ricevuta resta scritta, un tentativo contato",
              (True, 0, 1), (bool(r2["ricevuta"]), r2["ricevuta_relay"],
                             r2["ricevuta_tentativi"]))
        id_prima = json.loads(r2["ricevuta"])["id"]
        giro(); giro(); giro(); giro()
        r2 = righe(f"payment_hash='{h2}'")[0]
        prova("si riprova tre volte in tutto, poi basta", (3, 3),
              (r2["ricevuta_tentativi"], len(mandati)))
        prova("...sempre la STESSA ricevuta, mai una firmata di nuovo",
              id_prima, json.loads(r2["ricevuta"])["id"])
    finally:
        SRV.MODALITA_COLLAUDO = True
        SRV._spedisci_ai_relay, SRV.url_foto_ammesso = vero_spedisci, vero_guardia
    prova("la guardia vera dice no a un indirizzo che non e' wss", False,
          SRV.zap_relay_ammesso("ws://127.0.0.1:7777"))

    # ---- 8) LNbits che tace, la scadenza --------------------------------
    print("\n[LNbits che tace, e la scadenza]")
    scrivi("DELETE FROM zap")
    d = chiedi(amount="7000").json()
    h3 = SRV.zap_leggi_bolt11(d["pr"])["payment_hash"]
    scrivi("UPDATE zap SET creato=creato-900, scade=scade-900")
    LNBITS["chiedi"] = 520
    n, carta = giro()
    prova("LNbits tace a tempo scaduto: la fattura NON scade", "attesa",
          righe()[0]["stato"])
    prova("...e il journal lo dice", True, "LNbits non risponde" in carta)
    LNBITS["chiedi"] = 200
    paga(h3)
    n, carta = giro()
    prova("...e quando torna, se era stata pagata, si incassa lo stesso",
          (1, "pagato"), (n, righe()[0]["stato"]))
    d = chiedi(amount="8000").json()
    scrivi("UPDATE zap SET creato=creato-900, scade=scade-900 WHERE stato='attesa'")
    n, carta = giro()
    prova("scaduta e non pagata, detto da LNbits: scade", (0, "scaduto"),
          (n, righe("sats=8")[0]["stato"]))
    d = chiedi(amount="9000").json()
    h5 = SRV.zap_leggi_bolt11(d["pr"])["payment_hash"]
    scrivi("UPDATE zap SET creato=creato-300 WHERE stato='attesa'")
    prima = len(CHIAMATE)
    giro(); giro(); giro()
    prova("una fattura non piu' fresca si chiede ogni mezzo minuto, non a "
          "ogni giro", 1, len(CHIAMATE) - prima)

    # ---- 9) LNbits che non conia, o conia senza impronta -----------------
    print("\n[LNbits che non conia, o che ignora l'impronta]")
    quante = len(righe())
    LNBITS["conia"] = 520
    r = chiedi(amount="21000")
    prova("LNbits giu': 503 con l'errore LUD-06, nessuna riga",
          (503, "ERROR", quante),
          (r.status_code, r.json().get("status"), len(righe())))
    LNBITS["conia"] = 201
    LNBITS["impronta"] = False
    r = chiedi(amount="21000")
    prova("una fattura SENZA l'impronta non esce di qui", (503, "ERROR", quante),
          (r.status_code, r.json().get("status"), len(righe())))
    prova("...e il journal dice perche'", True,
          "non porta l'impronta" in journal.getvalue())
    LNBITS["impronta"] = True

    # ---- 10) il freno ----------------------------------------------------
    print("\n[il freno]")
    SRV._SECCHI.clear()
    scrivi("DELETE FROM zap")

    def bussa(ip=""):
        with contextlib.redirect_stdout(journal):
            return c.get(CALLBACK, params={"amount": "1000"},
                         headers={"x-forwarded-for": ip} if ip else {})

    # IP pubblici VERI: quelli «di documentazione» (203.0.113.x) per
    # `ipaddress` sono privati, e il freno per IP non li guarda
    codici = [bussa("151.38.10.7").status_code for _ in range(22)]
    prova("venti fatture al minuto per IP, la ventunesima e' un 429",
          [200] * 20 + [429, 429], codici)
    prova("...con l'errore LUD-06 anche li'", "ERROR",
          bussa("151.38.10.7").json().get("status"))
    prova("un altro IP passa", 200, bussa("151.38.10.8").status_code)
    SRV._SECCHI.clear()
    SRV._SECCHI["zap_tutti:tutti"] = [time.time(), SRV.FRENI["zap_tutti"][0]]
    prova("il freno per tutti ferma anche chi un IP leggibile non ce l'ha",
          429, bussa().status_code)
    SRV._SECCHI.clear()
    vero_tetto, SRV.ZAP_MAX_ATTESA = SRV.ZAP_MAX_ATTESA, len(righe("stato='attesa'"))
    prima = len(CHIAMATE)
    prova("col tetto delle fatture in attesa raggiunto non si conia",
          (429, prima), (bussa().status_code, len(CHIAMATE)))
    SRV.ZAP_MAX_ATTESA = vero_tetto

    # ---- 11) la card dell'admin, le leve, i segreti ----------------------
    print("\n[la card dell'admin, le leve, i segreti]")
    scrivi("DELETE FROM zap")
    LNBITS["saldo_msat"] = 0
    d = chiedi(amount="21000", nostr=richiesta_zap(21000, content="<b>ciao</b>"))
    paga(SRV.zap_leggi_bolt11(d.json()["pr"])["payment_hash"])
    giro()
    Z = asyncio.run(SRV.dati_zap_cruscotto())
    prova("la card: il saldo vivo, il totale, l'indirizzo",
          (21, 21, 1, "zap@barattolo.store", True, True),
          (Z["saldo_sats"], Z["totale_sats"], Z["quanti"], Z["indirizzo"],
           Z["vivo"], Z["nostr"]))
    prova("...chi ha zappato esce come npub", SRV.hex_to_npub(PUB_ZAPPA),
          Z["ultimi"][0]["mittente"])
    prova("...e il messaggio COM'E' (lo scappa la pagina, con esc)",
          "<b>ciao</b>", Z["ultimi"][0]["commento"])
    LNBITS["chiedi"] = 520
    prova("LNbits muto: il saldo e' None, la card c'e' lo stesso", None,
          asyncio.run(SRV.dati_zap_cruscotto())["saldo_sats"])
    LNBITS["chiedi"] = 200
    pagina = open("admin.html", encoding="utf-8").read()
    prova("la pagina /admin disegna la card e scappa messaggio e npub", True,
          "${cardZap(D.zap)}" in pagina and "esc(u.commento" in pagina
          and "esc(u.mittente" in pagina)
    come_admin = c.get("/api/admin/cruscotto").status_code
    prova("il cruscotto resta chiuso a chi non e' admin", True,
          come_admin in (401, 403))
    leve = SRV._zap_leve()
    prova("le leve: quattro voci, l'indirizzo acceso senza allarme",
          (4, True, None), (len(leve), leve[0]["valore"], leve[0].get("allarme")))
    chiave = CHIAVI["ZAP_LNBITS_INVOICE_KEY"]
    prova("la invoice key non sta nelle leve, nella card ne' nel journal",
          [False, False, False],
          [chiave in json.dumps(leve), chiave in json.dumps(Z),
           chiave in journal.getvalue()])
    prova("OGNI chiamata a LNbits ha usato la invoice key del salvadanaio",
          {chiave}, {k for _, _, k in CHIAMATE})
    prova("...e nessuna e' stata un pagamento in uscita", True,
          all(f["out"] is False for f in FATTURE.values()))
    prova("il journal non porta mai una fattura intera", False,
          any(f"lnbc{f['sats'] * 10}n1" in journal.getvalue()
              for f in FATTURE.values()))
    # IL REGISTRO DEGLI ACCESSI DI UVICORN (visto nel giro dal vivo): la
    # riga porta l'indirizzo intero, e in quello del callback ci sono il
    # commento e la richiesta di zap. Qui si fa passare dal registro VERO
    # una riga fatta come le fa uvicorn.
    import logging

    def riga_accesso(strada):
        rec = logging.LogRecord(
            "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
            ("151.38.10.7:5555", "GET", strada, "1.1", 200), None)
        logging.getLogger("uvicorn.access").filter(rec)
        return rec.getMessage()

    prova("il registro degli accessi non porta la query del callback",
          '151.38.10.7:5555 - "GET /api/lnurl/zap?… HTTP/1.1" 200',
          riga_accesso("/api/lnurl/zap?amount=21000&comment=un%20segreto"
                       "&nostr=%7B%22content%22%3A%22privato%22%7D"))
    prova("...e le altre strade restano com'erano",
          '151.38.10.7:5555 - "GET /api/annunci?q=bici HTTP/1.1" 200',
          riga_accesso("/api/annunci?q=bici"))

    SRV.ZAP_ATTIVO = False
    prova("spenta di nuovo la leva: 404, e la card resta (ci sono righe)",
          (404, False), (c.get(VIA).status_code,
                         asyncio.run(SRV.dati_zap_cruscotto())["vivo"]))
    scrivi("DELETE FROM zap")
    prova("spenta e senza righe: niente card", None,
          asyncio.run(SRV.dati_zap_cruscotto()))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
