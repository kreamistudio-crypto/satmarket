# -*- coding: utf-8 -*-
"""
IL SATS ROUTING DI CARTONE (19 ott 2026, cantiere swap-preventivo; dal 20
ott 2026, tappa 3, anche la creazione e il ritiro).

Un SATS Routing finto, su una porta di questo computer, per provare lo
swap SENZA sats e senza bussare al servizio vero: nel collaudo, nei giri
dal vivo e sulla VM di collaudo (regola di Andrea: ogni tappa dello swap
si prova li' prima di accendere SWAP_ATTIVO in produzione). Il server lo
trova con `SWAP_API_BASE = "http://127.0.0.1:<porta>"`; in MODALITA_COLLAUDO
una base fuori dal computer non si legge mai. Dalla tappa 3 lo chiama
anche il TELEFONO, direttamente: per questo risponde alle domande CORS
del browser.

COSA RISPONDE, col calco dei documenti di SATS Routing (Boltz v2):
  - `GET  /v2/swap/reverse` le tariffe, coi NUMERI VERI del 16 ott 2026
    (0,6 %, 324 di rete per il loro invio, ~234 per il ritiro, da 2.142 a
    5.000.000 sats). L'impronta della tariffa (`hash`) e' INVENTATA e non
    e' esadecimale: un esadecimale da 64 in un file del repo fa rossa la
    CI, e qui non serve che sia vera, serve che CAMBI con le tariffe;
  - `POST /v2/swap/reverse` la nascita di uno swap (tappa 3): chiave del
    cartone, albero, indirizzo del lockup, fattura con l'impronta del
    segreto del telefono. La crittografia la fa `cartone_satsrouting_cripto.js`
    con la STESSA libreria del telefono, in node;
  - `GET  /v2/swap/<id>` lo stato;
  - `GET  /v2/swap/reverse/<id>/transaction` il lockup, a bitcoin bloccati;
  - `POST /v2/swap/reverse/<id>/claim` la meta' della firma del cartone
    per il ritiro cooperativo, solo col segreto giusto;
  - `POST /v2/chain/BTC/transaction` la trasmissione del ritiro: il
    cartone la accetta SOLO se spende il lockup e la firma regge (BIP-340
    verificata QUI, in Python puro, non con la libreria del telefono);
  - `POST /v2/swap/restore` il recupero dalla xpub di radice.

I MODI, a comando (`GET /cartone/modo?m=...`):
  - `normale`  le tariffe del 16 ott;
  - `cambiata` stesse tariffe con 0,7 % e un'impronta diversa: e' il
               caso «le tariffe sono cambiate» del preventivo;
  - `giu`      risponde 503, come un servizio che non c'e';
  - `storta`   risponde 200 con una forma che non e' quella vera;
  - `mente_importo`, `mente_impronta`, `mente_albero`, `mente_indirizzo`,
    `mente_meno`: la creazione risponde con UN pezzo falso (la fattura di
    un altro importo, con un'altra impronta, l'albero con un'altra
    scadenza, l'indirizzo di un'altra chiave, meno on-chain del
    preventivo): il telefono deve rifiutarlo;
  - `non_firma` il ritiro cooperativo e' rifiutato: il telefono deve
    ritirare dallo script;
  - `rifiuta_cooperativo` la firma a due c'e', ma la trasmissione di un
    ritiro cooperativo e' rifiutata (come una rete che non lo accetta):
    il giro dopo il telefono deve ritirare dallo script;
  - (20 ott 2026, cantiere swap-lockup) tre LOCKUP BUGIARDI, che il
    telefono deve rifiutare PRIMA di mandare il segreto:
    `lockup_altro_script` blocca i bitcoin su un'uscita p2sh della stessa
    chiave (una delle quattro forme che `detectSwap` della 5.0.0
    accettava), `lockup_meno` blocca 100 sats meno della promessa,
    `lockup_fantasma` da' al telefono una transazione che la «rete» non
    ha mai visto.
  - (20 ott 2026, cantiere swap-senza-api) `giu_dopo_firma`: la richiesta
    di firma cooperativa arriva (col segreto) e si conta, poi il cartone
    si SPEGNE (503, e da li' in avanti il modo e' `giu`): il telefono deve
    ritirare lo stesso, dallo script, trasmettendo sulla rete.
  - (20 ott 2026, cantiere swap-spesa) `giu_rete_muta`: il fornitore e'
    giu e la rete PRENDE la trasmissione ma la risposta si perde (502):
    il giro dopo il telefono deve riconoscere il suo ritiro nella spesa
    del lockup. E `GET /cartone/spendi_altro?id=...` fa spendere il
    lockup a un'altra transazione (verso un altro script): il telefono
    deve dirlo chiaro, senza mandare il segreto.
IL FINTO MEMPOOL, come l'API di mempool.space, vivo anche nel modo `giu`
(la rete non e' il fornitore): `GET /esplora/tx/<id>/hex` coi soli lockup
«trasmessi» (tutti, tranne il fantasma); `GET /esplora/address/<a>/utxo`
i lockup non ancora spesi che pagano quell'indirizzo (quello «altro
script» paga un indirizzo diverso, e li' non compare); `POST /esplora/tx`
la trasmissione del ritiro, in testo semplice, con le stesse regole di
quella del fornitore; `GET /esplora/v1/fees/recommended` la fee del
momento; (dal 20 ott, swap-spesa) `GET /esplora/address/<a>/txs` le
transazioni dell'indirizzo (il lockup e chi l'ha speso), `GET
/esplora/tx/<id>` una transazione in JSON, `GET
/esplora/tx/<id>/outspend/<n>` chi ha speso quell'uscita; (dal 24 ott,
swap tappa 4) `GET /esplora/blocks/tip/height` l'altezza della rete, che
`GET /cartone/cima?h=...` sposta. `/cartone/visto` conta le richieste di firma cooperativa
(`firme`: lì arriva il segreto) e le trasmissioni tentate (`tentate`);
ogni ritiro accettato sta in `trasmesse` una volta sola, con le `strade`
da cui e' arrivato («rete», «fornitore»).
Lo stato di uno swap si sposta a comando come lo sposterebbe SATS Routing
(`GET /cartone/stato?id=...&s=transaction.mempool`: a bitcoin bloccati
nasce il lockup). `GET /cartone/visto` dice letture, l'ultima intestazione
`Referral`, l'ultima richiesta di creazione e le trasmissioni.

USO:  python cartone_satsrouting.py [--porta 9077] [--rete regtest] [--percento 0.3]

DUE CARTONI (20 ott 2026, cantiere swap-instradatore): ogni `avvia()` e'
un cartone NUOVO, col suo stato; `percento` gli da' una commissione sua
(e un'impronta delle tariffe che la dice). E' il secondo fornitore delle
prove dell'instradatore.
"""
import hashlib
import json
import math
import os
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Le tariffe lette dall'API vera il 16 ott 2026 (studio swap, voce
# «Gli swap di SATS Routing dentro Barattolo»), con l'impronta finta.
TARIFFE_16_OTT = {
    "BTC": {
        "BTC": {"hash": "cartone-tariffa-16ott", "rate": 1,
                "limits": {"maximal": 5_000_000, "minimal": 2_142},
                "fees": {"percentage": 0.6,
                         "minerFees": {"claim": 234, "lockup": 324}}},
        "L-BTC": {"hash": "cartone-tariffa-liquid-16ott", "rate": 1,
                  "limits": {"maximal": 5_000_000, "minimal": 100},
                  "fees": {"percentage": 0.4,
                           "minerFees": {"claim": 20, "lockup": 27}}}}}

STATO = {"modo": "normale", "letture": 0, "referral": None,
         "rete": "bitcoin", "creazione": None, "trasmesse": []}
SWAP = {}           # id -> lo swap come lo ricorda il cartone
CHIAVE = threading.Lock()
MODI = ("normale", "cambiata", "giu", "storta",
        "mente_importo", "mente_impronta", "mente_albero",
        "mente_indirizzo", "mente_meno", "non_firma", "rifiuta_cooperativo",
        "lockup_altro_script", "lockup_meno", "lockup_fantasma",
        "giu_dopo_firma", "giu_rete_muta")
GIU = ("giu", "giu_rete_muta")     # i modi in cui il fornitore non risponde
STATI = ("swap.created", "transaction.mempool", "transaction.confirmed",
         "invoice.settled", "invoice.expired", "swap.expired",
         "transaction.failed", "transaction.refunded")
SCADENZA_BLOCCO = 900_144
CRIPTO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "cartone_satsrouting_cripto.js")


def spendi(c, s, txid, uscite):
    """La «rete» registra chi ha speso il lockup di `s`: l'uscita 0 del
    lockup va a `txid`, che paga `uscite` ([{sats, script}])."""
    c["spese"][s["lockup"]["id"]] = {
        "txid": txid,
        "vout": [{"scriptpubkey": u["script"], "value": u["sats"]} for u in uscite]}


def tariffe_del_modo(modo, percento=None):
    """La risposta di `/v2/swap/reverse` nel modo chiesto (None = giu).
    `percento` = la commissione di QUESTO cartone (20 ott 2026: il
    secondo fornitore delle prove dell'instradatore), con un'impronta
    che la dice; None = lo 0,6 % del 16 ott."""
    if modo in GIU:
        return None
    if modo == "storta":
        return {"BTC": {"BTC": {"hash": "x", "fees": "zero"}}}
    dati = json.loads(json.dumps(TARIFFE_16_OTT))
    if modo == "cambiata":
        c = dati["BTC"]["BTC"]
        c["hash"] = "cartone-tariffa-cambiata"
        c["fees"]["percentage"] = 0.7
    if percento is not None and modo != "cambiata":
        coppia = dati["BTC"]["BTC"]
        coppia["hash"] = f"cartone-tariffa-p{percento}"
        coppia["fees"]["percentage"] = float(percento)
    return dati


def cripto(op, **dati):
    """Una chiamata all'aiutante in node (la libreria del telefono)."""
    r = subprocess.run(["node", CRIPTO], input=json.dumps(dict(dati, op=op)),
                       capture_output=True, encoding="utf-8", timeout=60)
    esito = json.loads(r.stdout or "{}")
    if "errore" in esito or r.returncode:
        raise RuntimeError(esito.get("errore") or r.stderr[:300])
    return esito


# ─── BIP-340 in Python puro: chi trasmette il ritiro deve averlo FIRMATO
# davvero, e lo giudica un'aritmetica che non e' quella del bundle.
# (Le costanti di secp256k1 spezzate in due: nel repo nessun esadecimale
# da 64 di fila, la regola dello scanner dei segreti.)
_P = 2 ** 256 - 2 ** 32 - 977
_N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE" "BAAEDCE6AF48A03BBFD25E8CD0364141", 16)
_G = (int("79BE667EF9DCBBAC55A06295CE870B07" "029BFCDB2DCE28D959F2815B16F81798", 16),
      int("483ADA7726A3C4655DA4FBFC0E1108A8" "FD17B448A68554199C47D08FFB10D4B8", 16))


def _somma(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a[0] == b[0] and (a[1] + b[1]) % _P == 0:
        return None
    if a == b:
        k = 3 * a[0] * a[0] * pow(2 * a[1], _P - 2, _P) % _P
    else:
        k = (b[1] - a[1]) * pow(b[0] - a[0], _P - 2, _P) % _P
    x = (k * k - a[0] - b[0]) % _P
    return (x, (k * (a[0] - x) - a[1]) % _P)


def _per(punto, n):
    r = None
    while n:
        if n & 1:
            r = _somma(r, punto)
        punto = _somma(punto, punto)
        n >>= 1
    return r


def _etichettato(etichetta, dati):
    e = hashlib.sha256(etichetta.encode()).digest()
    return hashlib.sha256(e + e + dati).digest()


def schnorr_verifica(messaggio: bytes, chiave: bytes, firma: bytes) -> bool:
    """La verifica BIP-340 di una firma da 64 byte su una chiave x-only."""
    if len(messaggio) != 32 or len(chiave) != 32 or len(firma) != 64:
        return False
    x = int.from_bytes(chiave, "big")
    if x >= _P:
        return False
    y = pow((pow(x, 3, _P) + 7) % _P, (_P + 1) // 4, _P)
    if (y * y - x ** 3 - 7) % _P:
        return False
    punto = (x, y if y % 2 == 0 else _P - y)
    r = int.from_bytes(firma[:32], "big")
    s = int.from_bytes(firma[32:], "big")
    if r >= _P or s >= _N:
        return False
    e = int.from_bytes(_etichettato("BIP0340/challenge",
                                    firma[:32] + chiave + messaggio), "big") % _N
    R = _somma(_per(_G, s), _per(punto, _N - e))
    return R is not None and R[1] % 2 == 0 and R[0] == r


def onchain_di(importo, tariffa):
    """Quel che il cartone blocca on-chain per una fattura da `importo`: la
    commissione per eccesso e la rete del suo invio, come il preventivo."""
    f = tariffa["fees"]
    return (importo - math.ceil(importo * f["percentage"] / 100)
            - f["minerFees"]["lockup"])


def crea_swap(c, corpo):
    """La nascita di uno swap: (codice, risposta)."""
    tariffa = tariffe_del_modo("cambiata" if c["stato"]["modo"] == "cambiata"
                               else "normale", c["percento"])["BTC"]["BTC"]
    try:
        importo = int(corpo["invoiceAmount"])
        impronta = str(corpo["preimageHash"])
        chiave = str(corpo["claimPublicKey"])
        bytes.fromhex(impronta)
        bytes.fromhex(chiave)
    except (KeyError, TypeError, ValueError):
        return 400, {"error": "richiesta storta"}
    if (corpo.get("from"), corpo.get("to")) != ("BTC", "BTC"):
        return 400, {"error": "coppia sconosciuta"}
    if len(impronta) != 64 or len(chiave) != 66:
        return 400, {"error": "impronta o chiave della lunghezza sbagliata"}
    if corpo.get("pairHash") not in (None, tariffa["hash"]):
        return 400, {"error": "invalid pair hash"}
    lim = tariffa["limits"]
    if not lim["minimal"] <= importo <= lim["maximal"]:
        return 400, {"error": "importo fuori dai limiti"}
    rete = c["stato"]["rete"]
    pezzi = cripto("crea", rete=rete, preimageHash=impronta,
                   claimPublicKey=chiave, invoiceAmount=importo,
                   timeoutBlockHeight=SCADENZA_BLOCCO)
    onchain = onchain_di(importo, tariffa)
    sid = secrets.token_hex(6)
    vero = {"id": sid, "invoice": pezzi["invoice"],
            "swapTree": pezzi["swapTree"],
            "lockupAddress": pezzi["lockupAddress"],
            "refundPublicKey": pezzi["refundPublicKey"],
            "timeoutBlockHeight": SCADENZA_BLOCCO, "onchainAmount": onchain}
    c["swap"][sid] = dict(vero, serverPriv=pezzi["serverPriv"],
                          claimPublicKey=chiave, preimageHash=impronta,
                          stato="swap.created", creato=int(time.time()),
                          referral=corpo.get("referralId"), lockup=None)
    risposta = dict(vero)
    m = c["stato"]["modo"]
    base = dict(serverPriv=pezzi["serverPriv"], claimPublicKey=chiave,
                swapTree=pezzi["swapTree"], preimageHash=impronta,
                timeoutBlockHeight=SCADENZA_BLOCCO, rete=rete)
    if m == "mente_importo":
        risposta["invoice"] = cripto("fattura", rete=rete, sats=importo - 1000,
                                     impronta=impronta)["invoice"]
    elif m == "mente_impronta":
        risposta["invoice"] = cripto("fattura", rete=rete, sats=importo)["invoice"]
    elif m == "mente_albero":
        risposta["swapTree"] = cripto("albero_altro", **base)["swapTree"]
    elif m == "mente_indirizzo":
        risposta["lockupAddress"] = cripto("indirizzo_altro", **base)["lockupAddress"]
    elif m == "mente_meno":
        risposta["onchainAmount"] = onchain - 500
    return 201, risposta


def sposta(c, sid, stato):
    """Lo stato di uno swap, spostato come lo sposterebbe SATS Routing: a
    bitcoin bloccati nasce il lockup."""
    s = c["swap"].get(sid)
    if not s or stato not in STATI:
        return False
    if stato in ("transaction.mempool", "transaction.confirmed") and not s["lockup"]:
        m = c["stato"]["modo"]
        s["lockup"] = cripto("lockup", serverPriv=s["serverPriv"],
                             claimPublicKey=s["claimPublicKey"],
                             swapTree=s["swapTree"],
                             onchainAmount=s["onchainAmount"]
                             - (100 if m == "lockup_meno" else 0),
                             variante="altro_script"
                             if m == "lockup_altro_script" else "")
        s["lockup"]["valore"] = s["onchainAmount"] - (100 if m == "lockup_meno" else 0)
        s["lockup"]["sull_indirizzo"] = m != "lockup_altro_script"
        # la «rete» lo vede, tranne il fantasma
        if m != "lockup_fantasma":
            c["rete"][s["lockup"]["id"]] = s["lockup"]["hex"]
    s["stato"] = stato
    return True


def firma_ritiro(c, s, corpo):
    # chi chiede la firma cooperativa manda il SEGRETO: si conta per swap
    c["stato"]["firme"].append(s["id"])
    if c["stato"]["modo"] == "giu_dopo_firma":
        c["stato"]["modo"] = "giu"
        return 503, {"error": "cartone giu"}
    if c["stato"]["modo"] == "non_firma":
        return 400, {"error": "swap not eligible for a cooperative claim"}
    if not s["lockup"]:
        return 400, {"error": "nessun lockup"}
    try:
        segreto = bytes.fromhex(str(corpo["preimage"]))
    except (KeyError, ValueError):
        return 400, {"error": "segreto storto"}
    if hashlib.sha256(segreto).hexdigest() != s["preimageHash"]:
        return 400, {"error": "il segreto non e' quello della fattura"}
    return 200, cripto("firma", serverPriv=s["serverPriv"],
                       claimPublicKey=s["claimPublicKey"],
                       swapTree=s["swapTree"],
                       onchainAmount=s["onchainAmount"],
                       transaction=str(corpo.get("transaction", "")),
                       pubNonce=str(corpo.get("pubNonce", "")))


def trasmetti(c, corpo, strada="fornitore"):
    """La trasmissione del ritiro: si accetta solo se spende il lockup di
    uno swap del cartone e la firma regge. `strada` = da dove arriva (la
    «rete», cioe' il finto mempool, o il «fornitore»): lo stesso ritiro
    trasmesso sulle due si conta una volta, con le due strade."""
    hex_ = str(corpo.get("hex", ""))
    c["stato"]["tentate"] += 1
    for s in c["swap"].values():
        if not s["lockup"]:
            continue
        try:
            esito = cripto("controlla", serverPriv=s["serverPriv"],
                           claimPublicKey=s["claimPublicKey"],
                           swapTree=s["swapTree"],
                           onchainAmount=s["onchainAmount"],
                           lockupHex=s["lockup"]["hex"], hex=hex_)
        except Exception:
            continue
        if not esito.get("spende"):
            continue
        buona = esito.get("via") in ("cooperativo", "script") and schnorr_verifica(
            bytes.fromhex(esito["impronta"]), bytes.fromhex(esito["chiave"]),
            bytes.fromhex(esito["firma"]))
        if esito.get("via") == "script":
            buona = buona and esito.get("foglia") and (
                hashlib.sha256(bytes.fromhex(esito["segreto"])).hexdigest()
                == s["preimageHash"])
        if not buona:
            return 400, {"error": "firma non valida"}
        if c["stato"]["modo"] == "rifiuta_cooperativo" and esito.get("via") == "cooperativo":
            return 400, {"error": "transazione rifiutata"}
        s["stato"] = "invoice.settled"
        if s["lockup"]["id"] not in c["spese"]:
            spendi(c, s, esito["txid"], esito["uscite"])
        gia = next((x for x in c["stato"]["trasmesse"]
                    if x["txid"] == esito["txid"]), None)
        if gia:
            if strada not in gia["strade"]:
                gia["strade"].append(strada)
        else:
            c["stato"]["trasmesse"].append({"swap": s["id"], "txid": esito["txid"],
                                            "via": esito["via"],
                                            "uscite": esito["uscite"],
                                            "strade": [strada]})
        return 201, {"id": esito["txid"]}
    return 400, {"error": "non spende nessun lockup conosciuto"}


def tx_json(c, txid):
    """Una transazione come la dice mempool.space (le parti che servono):
    un lockup, o chi l'ha speso. None = la rete non la conosce."""
    for s in c["swap"].values():
        lk = s["lockup"]
        if lk and lk["id"] == txid and txid in c["rete"]:
            return {"txid": txid, "vin": [],
                    "vout": [{"scriptpubkey_address": s["lockupAddress"]
                              if lk["sull_indirizzo"] else "", "value": lk["valore"]}],
                    "status": {"confirmed": s["stato"] == "transaction.confirmed"}}
    for lockup, spesa in c["spese"].items():
        if spesa["txid"] == txid:
            return {"txid": txid, "vin": [{"txid": lockup, "vout": 0}],
                    "vout": spesa["vout"], "status": {"confirmed": False}}
    return None


def recupera(c, corpo):
    chiavi = cripto("chiavi_xpub", xpub=str(corpo.get("xpub", "")),
                    quante=20)["chiavi"]
    out = []
    for s in c["swap"].values():
        if s["claimPublicKey"] not in chiavi:
            continue
        out.append({"id": s["id"], "type": "reverse", "status": s["stato"],
                    "createdAt": s["creato"], "from": "BTC", "to": "BTC",
                    "preimageHash": s["preimageHash"],
                    "claimDetails": {
                        "tree": s["swapTree"],
                        "keyIndex": chiavi.index(s["claimPublicKey"]),
                        "lockupAddress": s["lockupAddress"],
                        "serverPublicKey": s["refundPublicKey"],
                        "timeoutBlockHeight": s["timeoutBlockHeight"],
                        "amount": s["onchainAmount"]}})
    return 200, out


class Sportello(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass        # zitto: il collaudo ha le sue righe

    def _cors(self):
        # il telefono parla col cartone direttamente, da un'altra origine
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Referral")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _rispondi(self, codice, corpo):
        dati = json.dumps(corpo).encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dati)))
        self._cors()
        self.end_headers()
        self.wfile.write(dati)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        c = self.server.cartone
        u = urlparse(self.path)
        q = parse_qs(u.query)
        pezzi = u.path.strip("/").split("/")
        with c["chiave"]:
            if u.path == "/v2/swap/reverse":
                c["stato"]["letture"] += 1
                c["stato"]["referral"] = self.headers.get("Referral")
                dati = tariffe_del_modo(c["stato"]["modo"], c["percento"])
                if dati is None:
                    return self._rispondi(503, {"error": "cartone giu"})
                return self._rispondi(200, dati)
            if c["stato"]["modo"] in GIU and u.path.startswith("/v2/"):
                return self._rispondi(503, {"error": "cartone giu"})
            if len(pezzi) == 3 and pezzi[:2] == ["v2", "swap"]:
                s = c["swap"].get(pezzi[2])
                if not s:
                    return self._rispondi(404, {"error": "swap sconosciuto"})
                return self._rispondi(200, {"status": s["stato"]})
            if (len(pezzi) == 5 and pezzi[:3] == ["v2", "swap", "reverse"]
                    and pezzi[4] == "transaction"):
                s = c["swap"].get(pezzi[3])
                if not s or not s["lockup"]:
                    return self._rispondi(404, {"error": "nessun lockup"})
                return self._rispondi(200, {
                    "id": s["lockup"]["id"], "hex": s["lockup"]["hex"],
                    "timeoutBlockHeight": s["timeoutBlockHeight"]})
            if u.path == "/cartone/modo":
                m = (q.get("m") or [""])[0]
                if m not in MODI:
                    return self._rispondi(400, {"modi": list(MODI)})
                c["stato"]["modo"] = m
                return self._rispondi(200, {"modo": m})
            if u.path == "/cartone/stato":
                sid = (q.get("id") or [""])[0]
                if sid == "ultimo" and c["swap"]:
                    sid = max(c["swap"].values(), key=lambda s: s["creato"])["id"]
                ok = sposta(c, sid, (q.get("s") or [""])[0])
                return self._rispondi(200 if ok else 400, {"ok": ok, "id": sid})
            if u.path == "/cartone/cima":
                # (tappa 4) l'altezza della rete, a comando
                c["stato"]["cima"] = int((q.get("h") or ["0"])[0])
                return self._rispondi(200, {"cima": c["stato"]["cima"]})
            if u.path == "/esplora/blocks/tip/height":
                # come mempool.space: un numero in testo semplice
                dati = str(c["stato"]["cima"]).encode("ascii")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(dati)))
                self._cors()
                self.end_headers()
                self.wfile.write(dati)
                return
            if u.path == "/cartone/visto":
                return self._rispondi(200, dict(c["stato"], swap=len(c["swap"])))
            if (len(pezzi) == 4 and pezzi[0] == "esplora" and pezzi[1] == "address"
                    and pezzi[3] == "utxo"):
                # i lockup visti dalla rete, non ancora spesi, che pagano
                # quell'indirizzo
                spesi = {x["swap"] for x in c["stato"]["trasmesse"]} | {
                    s["id"] for s in c["swap"].values()
                    if s["lockup"] and s["lockup"]["id"] in c["spese"]}
                return self._rispondi(200, [
                    {"txid": s["lockup"]["id"], "vout": 0,
                     "value": s["lockup"]["valore"],
                     "status": {"confirmed": s["stato"] == "transaction.confirmed"}}
                    for s in c["swap"].values()
                    if s["lockup"] and s["lockup"]["id"] in c["rete"]
                    and s["lockup"]["sull_indirizzo"]
                    and s["lockupAddress"] == pezzi[2] and s["id"] not in spesi])
            if (len(pezzi) == 4 and pezzi[0] == "esplora" and pezzi[1] == "address"
                    and pezzi[3] == "txs"):
                # le transazioni dell'indirizzo, le piu' nuove prima: chi
                # ha speso il lockup, poi il lockup
                out = []
                for s in c["swap"].values():
                    if not (s["lockup"] and s["lockup"]["id"] in c["rete"]
                            and s["lockup"]["sull_indirizzo"]
                            and s["lockupAddress"] == pezzi[2]):
                        continue
                    spesa = c["spese"].get(s["lockup"]["id"])
                    if spesa:
                        out.append(tx_json(c, spesa["txid"]))
                    out.append(tx_json(c, s["lockup"]["id"]))
                return self._rispondi(200, out)
            if len(pezzi) == 3 and pezzi[0] == "esplora" and pezzi[1] == "tx":
                j = tx_json(c, pezzi[2])
                return self._rispondi(*((200, j) if j else (404, {"error": "Transaction not found"})))
            if (len(pezzi) == 5 and pezzi[0] == "esplora" and pezzi[1] == "tx"
                    and pezzi[3] == "outspend"):
                if pezzi[2] not in c["rete"]:
                    return self._rispondi(404, {"error": "Transaction not found"})
                spesa = c["spese"].get(pezzi[2])
                if pezzi[4] != "0" or not spesa:
                    return self._rispondi(200, {"spent": False})
                return self._rispondi(200, {"spent": True, "txid": spesa["txid"], "vin": 0,
                                            "status": {"confirmed": False}})
            if u.path == "/cartone/spendi_altro":
                sid = (q.get("id") or [""])[0]
                s = c["swap"].get(sid)
                if not s or not s["lockup"]:
                    return self._rispondi(400, {"ok": False})
                spendi(c, s, secrets.token_hex(32),
                       [{"sats": s["onchainAmount"] - 300, "script": "0014" + "11" * 20}])
                return self._rispondi(200, {"ok": True})
            if u.path == "/esplora/v1/fees/recommended":
                return self._rispondi(200, {"fastestFee": 2, "halfHourFee": 2,
                                            "hourFee": 1, "economyFee": 1,
                                            "minimumFee": 1})
            if (len(pezzi) == 4 and pezzi[0] == "esplora" and pezzi[1] == "tx"
                    and pezzi[3] == "hex"):
                # il finto mempool: testo semplice, come mempool.space
                hex_ = c["rete"].get(pezzi[2])
                if hex_ is None:
                    return self._rispondi(404, {"error": "Transaction not found"})
                dati = hex_.encode("ascii")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(dati)))
                self._cors()
                self.end_headers()
                self.wfile.write(dati)
                return
        return self._rispondi(404, {"error": "non c'e'"})

    def do_POST(self):
        c = self.server.cartone
        u = urlparse(self.path)
        pezzi = u.path.strip("/").split("/")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            grezzo = self.rfile.read(n).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return self._rispondi(400, {"error": "corpo storto"})
        if u.path == "/esplora/tx":
            # la trasmissione sulla «rete»: testo semplice, risponde l'id
            # in testo, come mempool.space; vive anche a fornitore giu
            with c["chiave"]:
                try:
                    codice, esito = trasmetti(c, {"hex": grezzo.strip()}, "rete")
                except Exception as e:
                    codice, esito = 500, {"error": str(e)[:200]}
                muta = c["stato"]["modo"] == "giu_rete_muta"
            if muta:
                # presa, ma la risposta non arriva al telefono
                self.send_response(502)
                self.send_header("Content-Length", "0")
                self._cors()
                self.end_headers()
                return
            dati = str(esito.get("id") if codice < 300 else
                       "sendrawtransaction RPC error: " + esito.get("error", "")).encode("utf-8")
            self.send_response(200 if codice < 300 else 400)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(dati)))
            self._cors()
            self.end_headers()
            self.wfile.write(dati)
            return
        try:
            corpo = json.loads(grezzo or "{}")
        except ValueError:
            return self._rispondi(400, {"error": "json storto"})
        if not isinstance(corpo, dict):
            return self._rispondi(400, {"error": "json storto"})
        with c["chiave"]:
            if c["stato"]["modo"] in GIU:
                return self._rispondi(503, {"error": "cartone giu"})
            try:
                if u.path == "/v2/swap/reverse":
                    c["stato"]["creazione"] = corpo
                    return self._rispondi(*crea_swap(c, corpo))
                if (len(pezzi) == 5 and pezzi[:3] == ["v2", "swap", "reverse"]
                        and pezzi[4] == "claim"):
                    s = c["swap"].get(pezzi[3])
                    if not s:
                        return self._rispondi(404, {"error": "swap sconosciuto"})
                    return self._rispondi(*firma_ritiro(c, s, corpo))
                if u.path == "/v2/chain/BTC/transaction":
                    return self._rispondi(*trasmetti(c, corpo))
                if u.path == "/v2/swap/restore":
                    return self._rispondi(*recupera(c, corpo))
            except Exception as e:      # il cartone non muore per una domanda
                return self._rispondi(500, {"error": str(e)[:200]})
        return self._rispondi(404, {"error": "non c'e'"})


def nuovo_cartone(rete="bitcoin", percento=None):
    """Lo stato di UN cartone: i suoi swap, il suo modo, la sua
    commissione (20 ott 2026: due cartoni nello stesso collaudo sono due
    fornitori diversi)."""
    return {"stato": {"modo": "normale", "letture": 0, "referral": None,
                      "rete": rete, "creazione": None, "trasmesse": [],
                      "firme": [], "tentate": 0,
                      # (24 ott 2026, swap tappa 4) l'altezza della rete:
                      # 144 blocchi prima della scadenza degli swap
                      "cima": SCADENZA_BLOCCO - 144},
            "swap": {}, "chiave": threading.Lock(), "percento": percento,
            "rete": {}, "spese": {}}


def avvia(porta=0, rete="bitcoin", percento=None):
    """Accende un cartone NUOVO in un filo suo, su 127.0.0.1. Torna
    (server, porta): porta 0 = la sceglie il sistema, e il collaudo la
    legge. `percento` = la sua commissione (None = lo 0,6 % del 16 ott)."""
    srv = ThreadingHTTPServer(("127.0.0.1", int(porta)), Sportello)
    srv.cartone = nuovo_cartone(rete, percento)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main(argv):
    porta = 9077
    if "--porta" in argv:
        porta = int(argv[argv.index("--porta") + 1])
    if "--rete" in argv:
        STATO["rete"] = argv[argv.index("--rete") + 1]
    percento = None
    if "--percento" in argv:
        percento = float(argv[argv.index("--percento") + 1])
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Sportello)
    STATO.update(firme=[], tentate=0)
    srv.cartone = {"stato": STATO, "swap": SWAP, "chiave": CHIAVE,
                   "percento": percento, "rete": {}, "spese": {}}
    print(f"🧃 SATS Routing di cartone su http://127.0.0.1:{porta} "
          f"(rete «{STATO['rete']}», modo «{STATO['modo']}»; si cambia con "
          f"/cartone/modo?m=...)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
