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
(6 nov 2026, ritiro a scalini) La coda si sposta a comando, `GET
/cartone/tariffa?hourFee=..&halfHourFee=..&fastestFee=..`; un ritiro
trasmesso di nuovo con un'altra transazione la SOSTITUISCE come in
bitcoind (RBF) solo se paga almeno 100 sats in piu' e se la vecchia non
e' confermata (`sostituite` le ricorda); `GET
/cartone/conferma_spesa?lockup=<id>` mette la spesa in un blocco.
Lo stato di uno swap si sposta a comando come lo sposterebbe SATS Routing
(`GET /cartone/stato?id=...&s=transaction.mempool`: a bitcoin bloccati
nasce il lockup). `GET /cartone/visto` dice letture, l'ultima intestazione
`Referral`, l'ultima richiesta di creazione e le trasmissioni.

IL SUBMARINE (27 ott 2026, cantiere cambio-libero, tappa 1): la strada
bitcoin -> Lightning del cambio libero, col calco dei documenti di Boltz v2:
  - `GET  /v2/swap/submarine` le tariffe, coi NUMERI VERI del 16 ott 2026
    (0,5 %, 318 di rete, da 50.000 a 5.000.000 sats, zero-conf a 0);
  - `POST /v2/swap/submarine` la nascita: il telefono manda la SUA fattura
    (del suo wallet) e la sua chiave di RIMBORSO; il cartone risponde con la
    sua chiave di RITIRO, l'albero, l'indirizzo dove il telefono deve
    mandare i bitcoin e quanto (`expectedAmount` = fattura + commissione +
    rete). La fattura la legge da se' (importo e impronta: `leggi_fattura`);
  - `GET  /v2/swap/submarine/<id>/transaction` i bitcoin mandati dal
    telefono, quando la rete li vede;
  - `GET  /v2/swap/submarine/<id>/preimage` il segreto, a fattura pagata;
  - `GET  /v2/swap/submarine/<id>/claim` e `POST .../claim`: il ritiro A DUE
    del cartone (la strada cooperativa di Boltz): il cartone da' l'impronta
    da firmare e il suo nonce, il telefono porta la sua meta', e la firma
    intera la giudica il BIP-340 in Python;
  - `POST /v2/swap/submarine/<id>/refund` la meta' della firma del cartone
    per il RIMBORSO cooperativo del telefono, solo a swap fallito
    (`invoice.failedToPay`, `swap.expired`, `transaction.lockupFailed`);
    il rimborso dallo script (tre pezzi di testimone, foglia del rimborso)
    passa dalla trasmissione di sempre, e il cartone lo accetta SOLO con
    il locktime alla scadenza e la cima della rete arrivata li' («non-final»
    altrimenti, come bitcoind);
  - `POST /v2/swap/restore` ritrova anche i submarine (`refundDetails`).
  A comando: `GET /cartone/stato?id=...&s=transaction.mempool` fa vedere
  alla rete i bitcoin del telefono (nel modo `lockup_meno` ne manda 100 di
  meno, e lo swap e' `transaction.lockupFailed`); `s=invoice.paid&preimage=
  <hex>` e' il wallet del telefono che si fa pagare (il segreto deve essere
  quello della fattura); `s=invoice.failedToPay` la fattura che non si
  paga. Le bugie `mente_importo`, `mente_albero`, `mente_indirizzo` valgono
  anche qui (un `expectedAmount` piu' alto, un altro albero, un altro
  indirizzo); `non_firma` nega il rimborso cooperativo.

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
import re
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

# Le tariffe del submarine (bitcoin -> Lightning) lette il 16 ott 2026:
# nel submarine la rete e' UN numero (il ritiro del fornitore), e c'e' il
# tetto dello zero-conf (0: chi manda aspetta una conferma).
TARIFFE_SUB_16_OTT = {
    "BTC": {
        "BTC": {"hash": "cartone-sub-16ott", "rate": 1,
                "limits": {"maximal": 5_000_000, "minimal": 50_000,
                           "maximalZeroConf": 0},
                "fees": {"percentage": 0.5, "minerFees": 318}}}}

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
STATI_SUB = ("invoice.set", "transaction.mempool", "transaction.confirmed",
             "invoice.pending", "invoice.paid", "transaction.claimed",
             "invoice.failedToPay", "swap.expired", "transaction.lockupFailed")
RIMBORSABILI = ("invoice.failedToPay", "swap.expired", "transaction.lockupFailed")
SCADENZA_BLOCCO = 900_144
PREFISSI_FATTURA = {"bitcoin": "lnbc", "testnet": "lntb", "regtest": "lnbcrt"}
_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_GEN = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
CRIPTO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "cartone_satsrouting_cripto.js")


def spendi(c, s, txid, uscite, nostra=False):
    """La «rete» registra chi ha speso il lockup di `s`: l'uscita 0 del
    lockup va a `txid`, che paga `uscite` ([{sats, script}]). `nostra` =
    arrivata da una trasmissione (la sola che un rilancio RBF puo'
    sostituire; quella di `spendi_altro` no)."""
    c["spese"][s["lockup"]["id"]] = {
        "txid": txid, "nostra": nostra, "confermata": False,
        "vout": [{"scriptpubkey": u["script"], "value": u["sats"]} for u in uscite]}


def leggi_fattura(bolt11, rete="bitcoin"):
    """Importo in sats e impronta di una bolt11, letti dal cartone come
    farebbe SATS Routing (il calco di `leggi_bolt11` e `importo_bolt11` del
    server, ridotto): None se non si legge, non e' della rete, chiede una
    frazione di sat o non porta l'impronta."""
    s = str(bolt11 or "").strip().lower()
    sep = s.rfind("1")
    if sep < 2:
        return None
    hrp, corpo = s[:sep], s[sep + 1:]
    m = re.match(r"^(lnbcrt|lntb|lnbc)(\d+)?([munp])?$", hrp)
    if not m or m.group(1) != PREFISSI_FATTURA.get(rete) or not m.group(2):
        return None
    decimi = int(m.group(2)) * {"": 10 ** 12, "m": 10 ** 9, "u": 10 ** 6,
                                "n": 10 ** 3, "p": 1}[m.group(3) or ""]
    if decimi % 10_000:
        return None
    try:
        v = [_BECH32.index(c) for c in corpo]
    except ValueError:
        return None
    chk = 1
    for x in ([ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + v):
        alto = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ x
        for i, g in enumerate(_BECH32_GEN):
            if (alto >> i) & 1:
                chk ^= g
    if chk != 1:
        return None
    d = v[:-6]
    if len(d) < 7 + 104:
        return None

    def num(gruppi):
        n = 0
        for g in gruppi:
            n = n * 32 + g
        return n
    fine, i, impronta = len(d) - 104, 7, ""
    while i + 3 <= fine:
        tipo, lung = d[i], d[i + 1] * 32 + d[i + 2]
        if i + 3 + lung > fine:
            break
        if tipo == 1 and lung == 52 and not impronta:
            impronta = f"{num(d[i + 3:i + 3 + lung]) >> 4:064x}"
        i += 3 + lung
    if not impronta:
        return None
    return decimi // 10_000, impronta


def tariffe_sub_del_modo(modo, percento=None):
    """La risposta di `/v2/swap/submarine` nel modo chiesto (None = giu),
    con le stesse regole delle tariffe del reverse."""
    if modo in GIU:
        return None
    if modo == "storta":
        return {"BTC": {"BTC": {"hash": "x", "fees": "zero"}}}
    dati = json.loads(json.dumps(TARIFFE_SUB_16_OTT))
    coppia = dati["BTC"]["BTC"]
    if modo == "cambiata":
        coppia["hash"] = "cartone-sub-cambiata"
        coppia["fees"]["percentage"] = 0.6
    elif percento is not None:
        coppia["hash"] = f"cartone-sub-p{percento}"
        coppia["fees"]["percentage"] = float(percento)
    return dati


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


def _base_cripto(s):
    """I pezzi di uno swap che ogni chiamata all'aiutante vuole: la chiave
    del cartone, la chiave DELL'ALTRO (nel reverse quella di ritiro del
    telefono, nel submarine quella di rimborso), l'albero, l'importo."""
    altra = s["refundPublicKey"] if s.get("tipo") == "submarine" else s["claimPublicKey"]
    return dict(serverPriv=s["serverPriv"], loroChiave=altra,
                swapTree=s["swapTree"], onchainAmount=s["onchainAmount"])


def crea_sub(c, corpo):
    """La nascita di un submarine (27 ott 2026, cambio-libero): la fattura
    e' del telefono, la chiave di ritiro del cartone: (codice, risposta)."""
    tariffa = tariffe_sub_del_modo("cambiata" if c["stato"]["modo"] == "cambiata"
                                   else "normale", c["percento"])["BTC"]["BTC"]
    try:
        fattura = str(corpo["invoice"])
        chiave = str(corpo["refundPublicKey"])
        bytes.fromhex(chiave)
    except (KeyError, TypeError, ValueError):
        return 400, {"error": "richiesta storta"}
    if (corpo.get("from"), corpo.get("to")) != ("BTC", "BTC"):
        return 400, {"error": "coppia sconosciuta"}
    if len(chiave) != 66:
        return 400, {"error": "chiave della lunghezza sbagliata"}
    if corpo.get("pairHash") not in (None, tariffa["hash"]):
        return 400, {"error": "invalid pair hash"}
    rete = c["stato"]["rete"]
    letta = leggi_fattura(fattura, rete)
    if not letta:
        return 400, {"error": "invalid invoice"}
    importo, impronta = letta
    lim = tariffa["limits"]
    if not lim["minimal"] <= importo <= lim["maximal"]:
        return 400, {"error": "importo fuori dai limiti"}
    if any(s.get("preimageHash") == impronta for s in c["swap"].values()):
        return 400, {"error": "a swap with this invoice exists already"}
    pezzi = cripto("crea_sub", rete=rete, preimageHash=impronta,
                   refundPublicKey=chiave, timeoutBlockHeight=SCADENZA_BLOCCO)
    f = tariffa["fees"]
    atteso = importo + math.ceil(importo * f["percentage"] / 100) + f["minerFees"]
    sid = secrets.token_hex(6)
    vero = {"id": sid, "address": pezzi["address"],
            "bip21": f"bitcoin:{pezzi['address']}?amount={atteso / 1e8:.8f}&label=cartone",
            "swapTree": pezzi["swapTree"], "claimPublicKey": pezzi["claimPublicKey"],
            "timeoutBlockHeight": SCADENZA_BLOCCO, "acceptZeroConf": False,
            "expectedAmount": atteso}
    c["swap"][sid] = {"id": sid, "tipo": "submarine", "invoice": fattura,
                      "serverPriv": pezzi["serverPriv"],
                      "claimPublicKey": pezzi["claimPublicKey"],
                      "refundPublicKey": chiave, "preimageHash": impronta,
                      "swapTree": pezzi["swapTree"], "lockupAddress": pezzi["address"],
                      "timeoutBlockHeight": SCADENZA_BLOCCO, "onchainAmount": atteso,
                      "fattura_sats": importo, "stato": "invoice.set",
                      "creato": int(time.time()), "referral": corpo.get("referralId"),
                      "lockup": None, "preimage": None, "ritiro": None}
    risposta = dict(vero)
    m = c["stato"]["modo"]
    base = dict(_base_cripto(c["swap"][sid]), preimageHash=impronta,
                timeoutBlockHeight=SCADENZA_BLOCCO, rete=rete)
    if m == "mente_importo":
        risposta["expectedAmount"] = atteso + 1000
    elif m == "mente_albero":
        risposta["swapTree"] = cripto("albero_altro_sub", **base)["swapTree"]
    elif m == "mente_indirizzo":
        risposta["address"] = cripto("indirizzo_altro", **base)["lockupAddress"]
    return 201, risposta


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


def sposta(c, sid, stato, preimage=""):
    """Lo stato di uno swap, spostato come lo sposterebbe SATS Routing: a
    bitcoin bloccati nasce il lockup. Nel submarine (cambio-libero) il
    lockup e' quel che il TELEFONO manda, e `invoice.paid` e' il suo wallet
    che si fa pagare: vuole il segreto della fattura (`preimage`), che da
    li' in poi il cartone conosce."""
    s = c["swap"].get(sid)
    sub = bool(s) and s.get("tipo") == "submarine"
    if not s or stato not in (STATI_SUB if sub else STATI):
        return False
    if stato in ("transaction.mempool", "transaction.confirmed") and not s["lockup"]:
        m = c["stato"]["modo"]
        s["lockup"] = cripto("lockup", **dict(_base_cripto(s),
                             onchainAmount=s["onchainAmount"]
                             - (100 if m == "lockup_meno" else 0),
                             variante="altro_script"
                             if m == "lockup_altro_script" else ""))
        s["lockup"]["valore"] = s["onchainAmount"] - (100 if m == "lockup_meno" else 0)
        s["lockup"]["sull_indirizzo"] = m != "lockup_altro_script"
        # la «rete» lo vede, tranne il fantasma
        if m != "lockup_fantasma":
            c["rete"][s["lockup"]["id"]] = s["lockup"]["hex"]
        if sub and m == "lockup_meno":
            stato = "transaction.lockupFailed"
    if sub and stato == "invoice.paid":
        try:
            segreto = bytes.fromhex(str(preimage or ""))
        except ValueError:
            return False
        if hashlib.sha256(segreto).hexdigest() != s["preimageHash"]:
            return False
        s["preimage"] = segreto.hex()
    s["stato"] = stato
    return True


def firma_rimborso(c, s, corpo):
    """La meta' del cartone per il rimborso cooperativo di un submarine:
    solo a swap fallito, e mai nel modo `non_firma`."""
    c["stato"]["rimborsi"].append(s["id"])
    if c["stato"]["modo"] == "non_firma":
        return 400, {"error": "swap not eligible for a cooperative refund"}
    if s["stato"] not in RIMBORSABILI:
        return 400, {"error": "swap not eligible for a cooperative refund"}
    if not s["lockup"]:
        return 400, {"error": "nessun lockup"}
    return 200, cripto("firma", **dict(_base_cripto(s),
                       transaction=str(corpo.get("transaction", "")),
                       pubNonce=str(corpo.get("pubNonce", ""))))


def ritiro_sub_dettagli(c, s):
    """`GET /claim` di un submarine: cosa il cartone chiede al telefono di
    firmare per il suo ritiro a due. Solo a segreto noto e lockup visto."""
    if not s["preimage"] or not s["lockup"]:
        return 400, {"error": "swap not eligible for a cooperative claim"}
    if not s["ritiro"]:
        s["ritiro"] = cripto("ritiro_sub_inizio", **dict(_base_cripto(s),
                             lockupHex=s["lockup"]["hex"]))
    r = s["ritiro"]
    return 200, {"preimage": s["preimage"], "pubNonce": r["pubNonce"],
                 "publicKey": s["claimPublicKey"], "transactionHash": r["transactionHash"]}


def ritiro_sub_chiudi(c, s, corpo):
    """`POST /claim`: la meta' del telefono. La firma intera la giudica il
    BIP-340 in Python; buona, i bitcoin sono spesi e lo swap e' ritirato."""
    c["stato"]["ritiri"].append(s["id"])
    if not s["ritiro"]:
        return 400, {"error": "swap not eligible for a cooperative claim"}
    try:
        esito = cripto("ritiro_sub_fine", **dict(_base_cripto(s),
                       hex=s["ritiro"]["hex"], nonce=s["ritiro"]["nonce"],
                       pubNonceLui=str(corpo.get("pubNonce", "")),
                       partialLui=str(corpo.get("partialSignature", ""))))
    except RuntimeError as e:
        return 400, {"error": "invalid partial signature: " + str(e)[:80]}
    if not schnorr_verifica(bytes.fromhex(esito["impronta"]),
                            bytes.fromhex(esito["chiave"]),
                            bytes.fromhex(esito["firma"])):
        return 400, {"error": "firma non valida"}
    if s["lockup"]["id"] not in c["spese"]:
        spendi(c, s, esito["txid"], esito["uscite"])
    s["stato"] = "transaction.claimed"
    return 200, {}


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
    return 200, cripto("firma", **dict(_base_cripto(s),
                       transaction=str(corpo.get("transaction", "")),
                       pubNonce=str(corpo.get("pubNonce", ""))))


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
            esito = cripto("controlla", **dict(_base_cripto(s),
                           lockupHex=s["lockup"]["hex"], hex=hex_))
        except Exception:
            continue
        if not esito.get("spende"):
            continue
        sub = s.get("tipo") == "submarine"
        # nel reverse si RITIRA (cooperativo o dallo script col segreto);
        # nel submarine chi trasmette e' il telefono che si RIMBORSA
        # (cooperativo, o dallo script alla scadenza)
        vie = ("cooperativo", "rimborso") if sub else ("cooperativo", "script")
        buona = esito.get("via") in vie and schnorr_verifica(
            bytes.fromhex(esito["impronta"]), bytes.fromhex(esito["chiave"]),
            bytes.fromhex(esito["firma"]))
        if esito.get("via") == "script":
            buona = buona and esito.get("foglia") and (
                hashlib.sha256(bytes.fromhex(esito["segreto"])).hexdigest()
                == s["preimageHash"])
        if esito.get("via") == "rimborso":
            buona = buona and esito.get("foglia")
        if not buona:
            return 400, {"error": "firma non valida"}
        if esito.get("via") == "rimborso" and not (
                esito.get("locktime", 0) >= s["timeoutBlockHeight"]
                and c["stato"]["cima"] >= esito.get("locktime", 0)
                and esito.get("sequenza", 0) < 0xffffffff):
            # come bitcoind: il CLTV non e' ancora maturo
            return 400, {"error": "non-final"}
        if c["stato"]["modo"] == "rifiuta_cooperativo" and esito.get("via") == "cooperativo":
            return 400, {"error": "transazione rifiutata"}
        if not sub:
            s["stato"] = "invoice.settled"
        prima = c["spese"].get(s["lockup"]["id"])
        if prima and prima["txid"] != esito["txid"] and prima.get("nostra"):
            # (6 nov 2026, ritiro a scalini) IL RILANCIO RBF, come
            # bitcoind: la stessa uscita spesa di nuovo sostituisce la
            # vecchia solo se paga di piu' (qui: almeno 100 sats, il
            # sat/vB in piu' di un ritiro), e mai una gia' confermata
            fee = lambda us: s["lockup"]["valore"] - sum(
                int(u.get("value", u.get("sats", 0))) for u in us)
            if prima.get("confermata"):
                return 400, {"error": "bad-txns-inputs-missingorspent"}
            if fee(esito["uscite"]) < fee(prima["vout"]) + 100:
                return 400, {"error": "insufficient fee"}
            c["stato"]["sostituite"].append(prima["txid"])
            spendi(c, s, esito["txid"], esito["uscite"], True)
        elif not prima:
            spendi(c, s, esito["txid"], esito["uscite"], True)
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
            # (26 ott 2026) come mempool.space: l'ingresso porta l'uscita
            # che spende (`prevout`), col suo indirizzo e il suo valore
            s = next((x for x in c["swap"].values()
                      if x["lockup"] and x["lockup"]["id"] == lockup), None)
            prevout = ({"scriptpubkey_address": s["lockupAddress"],
                        "value": s["lockup"]["valore"]} if s else {})
            return {"txid": txid,
                    "vin": [{"txid": lockup, "vout": 0, "prevout": prevout}],
                    "vout": spesa["vout"],
                    "status": {"confirmed": bool(spesa.get("confermata"))}}
    return None


def recupera(c, corpo):
    chiavi = cripto("chiavi_xpub", xpub=str(corpo.get("xpub", "")),
                    quante=20)["chiavi"]
    out = []
    for s in c["swap"].values():
        if s.get("tipo") == "submarine":
            if s["refundPublicKey"] not in chiavi:
                continue
            out.append({"id": s["id"], "type": "submarine", "status": s["stato"],
                        "createdAt": s["creato"], "from": "BTC", "to": "BTC",
                        "refundDetails": {
                            "tree": s["swapTree"],
                            "keyIndex": chiavi.index(s["refundPublicKey"]),
                            "lockupAddress": s["lockupAddress"],
                            "serverPublicKey": s["claimPublicKey"],
                            "timeoutBlockHeight": s["timeoutBlockHeight"]}})
            continue
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
            if u.path == "/v2/swap/submarine":
                c["stato"]["letture_sub"] += 1
                c["stato"]["referral"] = self.headers.get("Referral")
                dati = tariffe_sub_del_modo(c["stato"]["modo"], c["percento"])
                if dati is None:
                    return self._rispondi(503, {"error": "cartone giu"})
                return self._rispondi(200, dati)
            if c["stato"]["modo"] in GIU and u.path.startswith("/v2/"):
                return self._rispondi(503, {"error": "cartone giu"})
            if len(pezzi) == 3 and pezzi[:2] == ["v2", "swap"]:
                s = c["swap"].get(pezzi[2])
                if not s:
                    return self._rispondi(404, {"error": "swap sconosciuto"})
                r = {"status": s["stato"]}
                if s["stato"] == "invoice.failedToPay":
                    r["failureReason"] = "invoice could not be paid"
                return self._rispondi(200, r)
            if len(pezzi) == 5 and pezzi[:3] == ["v2", "swap", "submarine"]:
                s = c["swap"].get(pezzi[3])
                if not s or s.get("tipo") != "submarine":
                    return self._rispondi(404, {"error": "swap sconosciuto"})
                if pezzi[4] == "transaction":
                    if not s["lockup"]:
                        return self._rispondi(404, {"error": "no lockup transaction"})
                    return self._rispondi(200, {
                        "id": s["lockup"]["id"], "hex": s["lockup"]["hex"],
                        "timeoutBlockHeight": s["timeoutBlockHeight"],
                        "timeoutEta": int(time.time()) + 600 * max(
                            0, s["timeoutBlockHeight"] - c["stato"]["cima"])})
                if pezzi[4] == "preimage":
                    if not s["preimage"]:
                        return self._rispondi(404, {"error": "preimage not available"})
                    return self._rispondi(200, {"preimage": s["preimage"]})
                if pezzi[4] == "claim":
                    return self._rispondi(*ritiro_sub_dettagli(c, s))
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
                ok = sposta(c, sid, (q.get("s") or [""])[0],
                            (q.get("preimage") or [""])[0])
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
                                            "status": {"confirmed": bool(
                                                spesa.get("confermata"))}})
            if u.path == "/cartone/spendi_altro":
                sid = (q.get("id") or [""])[0]
                s = c["swap"].get(sid)
                if not s or not s["lockup"]:
                    return self._rispondi(400, {"ok": False})
                spendi(c, s, secrets.token_hex(32),
                       [{"sats": s["onchainAmount"] - 300, "script": "0014" + "11" * 20}])
                return self._rispondi(200, {"ok": True})
            if u.path == "/esplora/v1/fees/recommended":
                return self._rispondi(200, dict(c["stato"]["tariffe"]))
            if u.path == "/cartone/tariffa":
                # (6 nov 2026) la coda della rete, a comando:
                # ?hourFee=..&halfHourFee=..&fastestFee=..
                for k in list(c["stato"]["tariffe"]):
                    if k in q:
                        c["stato"]["tariffe"][k] = float(q[k][0])
                return self._rispondi(200, dict(c["stato"]["tariffe"]))
            if u.path == "/cartone/conferma_spesa":
                # (6 nov 2026) la spesa del lockup entra in un blocco
                spesa = c["spese"].get((q.get("lockup") or [""])[0])
                if spesa:
                    spesa["confermata"] = True
                return self._rispondi(200 if spesa else 400, {"ok": bool(spesa)})
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
                if u.path == "/v2/swap/submarine":
                    c["stato"]["creazione"] = corpo
                    return self._rispondi(*crea_sub(c, corpo))
                if len(pezzi) == 5 and pezzi[:3] == ["v2", "swap", "submarine"]:
                    s = c["swap"].get(pezzi[3])
                    if not s or s.get("tipo") != "submarine":
                        return self._rispondi(404, {"error": "swap sconosciuto"})
                    if pezzi[4] == "refund":
                        return self._rispondi(*firma_rimborso(c, s, corpo))
                    if pezzi[4] == "claim":
                        return self._rispondi(*ritiro_sub_chiudi(c, s, corpo))
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
                      # (cambio-libero) il submarine: le letture delle sue
                      # tariffe, le richieste di rimborso cooperativo, le
                      # meta' di firma portate per il ritiro a due
                      "letture_sub": 0, "rimborsi": [], "ritiri": [],
                      # (6 nov 2026, ritiro a scalini) la coda della rete
                      # e i ritiri sostituiti da un rilancio RBF
                      "tariffe": {"fastestFee": 2, "halfHourFee": 2,
                                  "hourFee": 1, "economyFee": 1,
                                  "minimumFee": 1},
                      "sostituite": [],
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
    STATO.update(firme=[], tentate=0, letture_sub=0, rimborsi=[], ritiri=[],
                 tariffe=dict(nuovo_cartone()["stato"]["tariffe"]),
                 sostituite=[], cima=SCADENZA_BLOCCO - 144)
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
