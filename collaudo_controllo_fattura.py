# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL CONTROLLO DELLA FATTURA P2P (10 ott 2026, cantiere
controllo-fattura).

`prove.py` fa girare i giudici con un `chiedi` di cartone: l'unica
funzione che non vede mai girare e' `_lnd_rest`, quella che parla
davvero col nodo — il TLS col certificato guardato, il macaroon
nell'header, una GET con la fattura nel percorso, una POST coi route
hints nel corpo, e le TRE voci che LND puo' avere: un 200 col JSON, un
errore con dentro il suo `message` («unable to find node», «unable to
find a path to destination»), e un «permission denied» quando il
macaroon non ha il permesso — che e' il caso del macaroon di OGGI sul
VPS (`offchain:read` e basta: `getnodeinfo` e `queryroutes` vogliono
`info:read`), e deve lasciar passare la fattura, mai fermarla.

Qui `_lnd_rest` e i giudici sono quelli VERI, presi da server.py con
`ast` (mai `import server`). Di finto c'e' un LND che parla HTTPS su
127.0.0.1 con un certificato fatto al momento e risponde come la REST
di LND a `/v1/payreq/{pr}`, `/v1/graph/node/{pk}` e
`/v1/graph/routes/{pk}/{amt}`, con tre macaroon: quello PIENO
(`offchain:read info:read`), quello di OGGI (`offchain:read`) e uno
che non apre niente. Le fatture sono quelle di `bolt11_finta`
(checksum vero, firma di zeri): il lettore locale le passa, e il
«DecodePayReq» di cartone le riconosce per testo.

⚠️ NON SOSTITUISCE LA PROVA SUL NODO VERO: la forma delle risposte di
LND qui dentro l'ho scritta IO, dal suo sorgente e a memoria della sua
REST. Questo collaudo prova che il NOSTRO lato e' giusto, e che ogni
guasto finisce in «non si sa» e lascia passare; che LND risponda
davvero cosi' lo dice la verifica di PRODUZIONE, «IL CONTROLLO DELLA
FATTURA P2P».

Uso:  python collaudo_controllo_fattura.py
"""
import ast
import asyncio
import datetime
import http.server
import ipaddress
import json
import os
import re
import ssl
import sys
import tempfile
import threading
import time

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from prove import bolt11_finta   # noqa: E402  (il conio delle fatture finte)

SRC = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
ALBERO = ast.parse(SRC)
PASSATE = FALLITE = 0


def pezzo(nome):
    for n in ALBERO.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and n.name == nome:
            return ast.get_source_segment(SRC, n)
    raise KeyError(nome)


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def certificato(cartella, nome):
    """Un certificato usa-e-getta per 127.0.0.1, come il tls.cert di LND
    copiato sul VPS (SAN `127.0.0.1`)."""
    chiave = ec.generate_private_key(ec.SECP256R1())
    chi = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "lnd finto")])
    ora = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(chi).issuer_name(chi)
            .public_key(chiave.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(ora - datetime.timedelta(minutes=5))
            .not_valid_after(ora + datetime.timedelta(hours=1))
            .add_extension(x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                           True)
            .sign(chiave, hashes.SHA256()))
    pc, pk = (os.path.join(cartella, nome + ".cert"),
              os.path.join(cartella, nome + ".key"))
    open(pc, "wb").write(cert.public_bytes(serialization.Encoding.PEM))
    open(pk, "wb").write(chiave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return pc, pk


# i tre macaroon di cartone: PIENO (offchain:read info:read), quello di
# OGGI sul VPS (offchain:read), uno che non apre niente
MAC_PIENO = "0201036c6e64" + "ab" * 40
MAC_OGGI = "0201036c6e64" + "cd" * 40
ADESSO = int(time.time())
# i nodi: PUBBLICO (nel grafo, con strade), LONTANO (nel grafo, nessuna
# strada), CARO (nel grafo, strada sopra il tetto), PRIVATO (non nel
# grafo), LENTO (nel grafo, ma le strade non arrivano mai)
PUBBLICO, LONTANO, CARO, PRIVATO, LENTO, HINT = (
    "02" + "11" * 32, "02" + "22" * 32, "02" + "33" * 32, "02" + "44" * 32,
    "02" + "55" * 32, "03" + "66" * 32)
NEL_GRAFO = {PUBBLICO, LONTANO, CARO, LENTO}
# le fatture, per testo: il «DecodePayReq» di cartone le riconosce
F = {
    "pubblica": (bolt11_finta(1000, 86400, ADESSO, phash=1), PUBBLICO, []),
    "lontana": (bolt11_finta(1000, 86400, ADESSO, phash=2), LONTANO, []),
    "cara": (bolt11_finta(100000, 86400, ADESSO, phash=3), CARO, []),
    "privata": (bolt11_finta(1000, 86400, ADESSO, phash=4), PRIVATO, []),
    "privata_con_hint": (bolt11_finta(1000, 86400, ADESSO, phash=5), PRIVATO,
                         [{"hop_hints": [{"node_id": HINT, "chan_id": "12345",
                                          "fee_base_msat": 1000,
                                          "fee_proportional_millionths": 1,
                                          "cltv_expiry_delta": 40}]}]),
    "lenta": (bolt11_finta(1000, 86400, ADESSO, phash=6), LENTO, []),
    "senza_importo": (bolt11_finta(0, 86400, ADESSO, phash=7), PUBBLICO, []),
}
# LA STRADA A PEZZI (16 ott 2026, cantiere strada-phoenix): la fattura
# Phoenix da 270.030 sats — nodo privato, un hint via ACINQ con un alias
# oltre l'int64, MPP facoltativo — e il suo gemello senza MPP. Le strade
# verso PHOENIX fanno come QueryRoutes coi nostri canali del 16 ott: una
# strada sola, e solo se la cifra sta in UN canale (LARGO).
PHOENIX, ACINQ = "03" + "77" * 32, "03" + "88" * 32
HINT_PHX = [{"hop_hints": [{"node_id": ACINQ, "chan_id": "18436044651096163129",
                            "fee_base_msat": 1000, "fee_proportional_millionths": 100,
                            "cltv_expiry_delta": 144}]}]
F["phoenix"] = (bolt11_finta(270030, 604800, ADESSO, phash=8), PHOENIX, HINT_PHX)
F["phoenix_intera"] = (bolt11_finta(270030, 604800, ADESSO, phash=9), PHOENIX, HINT_PHX)
CON_MPP = {F["phoenix"][0]}
LARGO = 240_952


def canale_finto(esce, riserva, tetto_loro, capienza):
    return {"active": True, "capacity": str(capienza), "remote_pubkey": ACINQ,
            "local_balance": str(esce), "remote_balance": "0",
            "local_constraints": {"chan_reserve_sat": str(riserva),
                                  "max_pending_amt_msat": str(tetto_loro * 1000)},
            "remote_constraints": {"chan_reserve_sat": str(riserva),
                                   "max_pending_amt_msat": str(capienza * 990)},
            "pending_htlcs": []}


CANALI_OGGI = [canale_finto(250_952, 10_000, 450_000, 1_000_000),
               canale_finto(303_479, 3_100, 139_500, 310_000)]
CANALI_CORTI = [canale_finto(150_000, 10_000, 450_000, 1_000_000),
                canale_finto(110_000, 3_100, 139_500, 310_000)]
CANALI = {"ora": CANALI_OGGI}
DECODIFICHE = {pr: (dest, hints) for pr, dest, hints in F.values()}
VISTI = []       # (metodo, percorso, macaroon, corpo)


class FintoLnd(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"null") if n else None

    def _rispondi(self, codice, corpo):
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write((json.dumps(corpo) + "\n").encode())

    def _errore(self, messaggio, codice=500, grpc=2):
        # la forma del gateway REST di LND: code, message, details
        return self._rispondi(codice, {"code": grpc, "message": messaggio,
                                       "details": []})

    def do_GET(self):
        self._servi("GET")

    def do_POST(self):
        self._servi("POST")

    def _servi(self, metodo):
        mac = self.headers.get("Grpc-Metadata-macaroon")
        corpo = self._corpo() if metodo == "POST" else None
        VISTI.append((metodo, self.path, mac, corpo))
        if mac not in (MAC_PIENO, MAC_OGGI):
            return self._errore("verification failed: signature mismatch "
                                "after caveat verification")
        m = re.fullmatch(r"/v1/payreq/([a-z0-9]+)", self.path)
        if m and metodo == "GET":
            dec = DECODIFICHE.get(m.group(1))
            if not dec:
                return self._errore("checksum failed.")
            sats = re.match(r"lnbc(\d+)n", m.group(1))
            return self._rispondi(200, {
                "destination": dec[0], "payment_hash": "00" * 32,
                "num_satoshis": str(int(sats.group(1)) // 10 if sats else 0),
                "timestamp": str(ADESSO), "expiry": "86400",
                "description": "", "cltv_expiry": "80",
                "route_hints": dec[1], "features": (
                    {"17": {"name": "multi-path-payments", "is_required": False,
                            "is_known": True},
                     "149": {"name": "", "is_required": False, "is_known": False}}
                    if m.group(1) in CON_MPP else {})})
        # i canali vogliono `offchain:read`, che il macaroon di oggi ha
        if self.path == "/v1/channels?active_only=true" and metodo == "GET":
            return self._rispondi(200, {"channels": CANALI["ora"]})
        # da qui in poi serve `info:read`: il macaroon di oggi non ce l'ha
        if mac != MAC_PIENO:
            return self._errore("permission denied")
        m = re.fullmatch(r"/v1/graph/node/([0-9a-f]{66})", self.path)
        if m and metodo == "GET":
            if m.group(1) not in NEL_GRAFO:
                return self._errore("unable to find node")
            return self._rispondi(200, {"node": {"pub_key": m.group(1),
                                                 "alias": "nodo finto"},
                                        "num_channels": 3,
                                        "total_capacity": "5000000"})
        m = re.fullmatch(r"/v1/graph/routes/([0-9a-f]{66})/(\d+)", self.path)
        if m and metodo == "POST":
            dest, amt = m.group(1), int(m.group(2))
            if dest == LENTO:
                time.sleep(4)        # oltre l'attesa del collaudo (2 s)
            hint = bool((corpo or {}).get("route_hints"))
            if dest == LONTANO or (dest in (PRIVATO, PHOENIX) and not hint)                     or (dest == PHOENIX and amt > LARGO):
                return self._errore("unable to find a path to destination")
            if dest == PHOENIX:      # il hint: 1 sat + 100 ppm
                fee_msat = 1000 + amt * 100 // 1000
                return self._rispondi(200, {"routes": [{
                    "total_time_lock": 800288, "total_fees": str(fee_msat // 1000),
                    "total_amt": str(amt + fee_msat // 1000), "hops": [{}, {}],
                    "total_fees_msat": str(fee_msat),
                    "total_amt_msat": str(amt * 1000 + fee_msat)}],
                    "success_prob": 0.9})
            fee = amt * 5 // 100 if dest == CARO else 3   # 5% o 3 sats
            return self._rispondi(200, {"routes": [{
                "total_time_lock": 800000, "total_fees": str(fee),
                "total_amt": str(amt + fee), "hops": [{}],
                "total_fees_msat": str(fee * 1000),
                "total_amt_msat": str((amt + fee) * 1000)}],
                "success_prob": 0.9})
        return self._errore("Not Found", 404, 5)


def costanti():
    """Il blocco delle costanti del controllo, dal sorgente — come
    `costanti_controllo_fattura` in prove.py."""
    amb = {"re": re}
    i = SRC.index("try:\n    from config import P2P_TETTO_ROTTA")
    exec(SRC[i:SRC.index("\n\n\nasync def _lnd_rest(", i)], amb)
    for inizio in ("_BECH32_ALFABETO = ", "_BECH32_GEN = ", "DOMINI_BIP353 = ",
                   "FORMA_LN_NOME = ", "FORMA_LN_DOMINIO = ",
                   "LND_ASSENTE, LND_MUTO, LND_SPENTO = "):
        j = SRC.index("\n" + inizio) + 1
        exec(SRC[j:SRC.index("\n", j)], amb)
    amb.pop("__builtins__", None)
    return amb


def main():
    print("\n[il controllo della fattura P2P, dal vivo contro un LND di cartone]")
    with tempfile.TemporaryDirectory() as tmp:
        cert, chiave = certificato(tmp, "lnd")
        altro_cert, _ = certificato(tmp, "un-altro")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLnd)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, chiave)
        srv.socket = tls.wrap_socket(srv.socket, server_side=True)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        porta = srv.server_address[1]

        detto = []
        amb = {**costanti(), "ssl": ssl, "httpx": httpx, "json": json,
               "re": re, "time": time, "asyncio": asyncio,
               "LND_PONTE_URL": f"https://127.0.0.1:{porta}",
               "LND_PONTE_CERT": cert,
               "LND_PONTE_MACAROON_LETTURA": MAC_PIENO,
               "print": lambda *a, **k: detto.append(" ".join(map(str, a)))}
        amb["LND_FATTURA_ATTESA_S"] = 2       # il LENTO dorme 4
        for nome in ("_lnd_configurato", "leggi_bolt11", "importo_bolt11",
                     "rete_bolt11", "_fmt_sats",
                     "_controllo_locale_fattura_p2p", "_risposta_fattura_p2p",
                     "_fee_rotta_msat", "_pezzo_lnd", "_fattura_si_divide",
                     "_uscita_utilizzabile", "_sats_canale"):
            exec(pezzo(nome), amb)
        for nome in ("_lnd_rest", "_controllo_rete_fattura_p2p",
                     "_controllo_indirizzo_p2p", "controlla_fattura_p2p"):
            exec(pezzo(nome), amb)

        async def risolvi(addr, sats):
            # il wallet dell'indirizzo, di cartone: MAI un giro di rete
            return F["privata"][0] if addr.startswith("privato@") else F["pubblica"][0]

        diagnosi = lambda dominio: "muto"

        def giudica(testo, deve=1000, finestra=3600):
            return asyncio.run(amb["controlla_fattura_p2p"](
                testo, deve, finestra, ADESSO, None, risolvi, diagnosi))

        def esito(v):
            return v["esito"]

        # --- 1. col macaroon PIENO: i verdetti --------------------------
        v = giudica(F["pubblica"][0])
        prova("fattura di un nodo pubblico con strada: ok, con la fee e il tetto",
              ("ok", 3, 10, PUBBLICO), (esito(v), v["fee"], v["tetto"], v["dest"]))
        prova("...tre domande a LND: la decodifica in GET, il nodo in GET, le strade in POST",
              [("GET", "/v1/payreq/" + F["pubblica"][0]),
               ("GET", "/v1/graph/node/" + PUBBLICO),
               ("POST", f"/v1/graph/routes/{PUBBLICO}/1000")],
              [(x[0], x[1]) for x in VISTI[-3:]])
        prova("...col macaroon nell'header e i route hints (vuoti) nel corpo della POST",
              (MAC_PIENO, {"route_hints": []}), (VISTI[-1][2], VISTI[-1][3]))
        v = giudica(F["privata"][0])
        prova("fattura di un nodo PRIVATO senza hint («unable to find node»): nodo_assente, FERMA",
              ("nodo_assente", amb["MSG_NODO_ASSENTE"]), (esito(v), v["messaggio"]))
        prova("...senza chiedere strade", "/v1/graph/node/" + PRIVATO, VISTI[-1][1])
        VISTI.clear()
        v = giudica(F["privata_con_hint"][0])
        prova("lo stesso nodo privato CON i route hints: ok (il nodo non si cerca, la strada passa dal hint)",
              ("ok", ["/v1/payreq/", "/v1/graph/routes/"]),
              (esito(v), [x[1][:len(p)] for x, p in zip(VISTI, ("/v1/payreq/", "/v1/graph/routes/"))]))
        prova("...e i hint sono arrivati a LND cosi' come la decodifica li ha dati",
              F["privata_con_hint"][2], VISTI[-1][3]["route_hints"])
        v = giudica(F["lontana"][0])
        prova("nodo nel grafo ma «unable to find a path»: senza_strada, AVVISA",
              ("senza_strada", amb["MSG_SENZA_STRADA"]), (esito(v), v["messaggio"]))
        v = giudica(F["cara"][0], 100000)
        prova("strada da 5.000 sats su 100.000 col tetto all'1%: costo, AVVISA",
              ("costo", 5000, 1000), (esito(v), v["fee"], v["tetto"]))
        t0 = time.time()
        v = giudica(F["lenta"][0])
        prova("LND che non risponde sulle strade: non_disponibile (passa), entro l'attesa",
              ("non_disponibile", True, True),
              (esito(v), v["perche"].startswith("rotte muto"), time.time() - t0 < 4))
        VISTI.clear()
        v = giudica(F["senza_importo"][0], 0)
        prova("senza importo e cifra ignota: ok senza chiedere strade", ("ok", 2),
              (esito(v), len(VISTI)))
        v = giudica(F["senza_importo"][0], 2500)
        prova("...con la cifra dovuta, la strada si prova su quella", f"/v1/graph/routes/{PUBBLICO}/2500",
              VISTI[-1][1])
        VISTI.clear()
        v = giudica("lnbc1ciao")
        prova("una fattura che non si legge si ferma PRIMA di LND", ("illeggibile", 0), (esito(v), len(VISTI)))
        v = giudica(F["pubblica"][0], 1200)
        prova("...e l'importo diverso pure", ("importo", 0), (esito(v), len(VISTI)))

        # --- 1-bis. la strada a pezzi (16 ott 2026) ----------------------
        VISTI.clear()
        v = giudica(F["phoenix"][0], 270030, 3600)
        prova("LA FATTURA PHOENIX DA 270.030: intera non passa da un canale, a pezzi si' — ok, nessun avviso",
              ("ok", 43, 2700), (esito(v), v.get("fee"), v.get("tetto")))
        prova("...le domande: decodifica, strada intera, strada del PEZZO (16.877), canali in linea",
              [("GET", "/v1/payreq/" + F["phoenix"][0]),
               ("POST", f"/v1/graph/routes/{PHOENIX}/270030"),
               ("POST", f"/v1/graph/routes/{PHOENIX}/16877"),
               ("GET", "/v1/channels?active_only=true")],
              [(x[0], x[1]) for x in VISTI])
        prova("...il hint con l'alias e' arrivato a LND intatto, nelle due POST",
              [HINT_PHX, HINT_PHX], [x[3]["route_hints"] for x in VISTI if x[0] == "POST"])
        r = amb["_risposta_fattura_p2p"](v, 111, "phx00001")
        prova("...al client ok senza messaggio, e il journal dice il pezzo e l'uscita",
              (True, "", True), (r["ok"], r["messaggio"],
                                 detto[-1].startswith("✅") and "a pezzi da 16.877, uscita 380.452" in detto[-1]))
        CANALI["ora"] = CANALI_CORTI
        v = giudica(F["phoenix"][0], 270030, 3600)
        r = amb["_risposta_fattura_p2p"](v, 111, "phx00002")
        prova("il pezzo passa ma la SOMMA dei canali non basta: uscita_corta, ok al client, «·» nel journal",
              ("uscita_corta", True, "", True),
              (esito(v), r["ok"], r["messaggio"], detto[-1].startswith("· Fattura P2P")))
        CANALI["ora"] = CANALI_OGGI
        v = giudica(F["phoenix_intera"][0], 270030, 3600)
        prova("la stessa fattura SENZA MPP: pezzo_solo, AVVISA col suo motivo",
              ("pezzo_solo", amb["MSG_PEZZO_SOLO"]), (esito(v), v["messaggio"]))

        # --- 2. col macaroon di OGGI (senza info:read): passa, e lo dice --
        amb["LND_PONTE_MACAROON_LETTURA"] = MAC_OGGI
        v = giudica(F["privata"][0])
        prova("il macaroon di oggi: la decodifica passa, il nodo e' NEGATO → non_disponibile, la fattura PASSA",
              ("non_disponibile", "nodo negato (permission denied)"), (esito(v), v["perche"]))
        r = amb["_risposta_fattura_p2p"](v, 111, "ordine01")
        prova("...e al client arriva ok=true senza messaggio", {"ok": True, "esito": "non_disponibile",
                                                              "comunque": False, "messaggio": ""}, r)
        prova("...col journal che dice «negato» e «permission denied», cosi' si capisce che e' il macaroon",
              True, detto[-1].startswith("· Fattura P2P: ordine ordine01, da 111, fattura, 1.000 sats, dest 024444444444…, nodo negato (permission denied): non_disponibile"))
        v = giudica(F["privata_con_hint"][0])
        prova("...coi hint le strade sono negate: non_disponibile", ("non_disponibile", "rotte negato (permission denied)"),
              (esito(v), v["perche"]))
        amb["LND_PONTE_MACAROON_LETTURA"] = MAC_PIENO

        # --- 3. i guasti del ponte: tutti «non si sa», mai un fermo -------
        amb["LND_PONTE_MACAROON_LETTURA"] = "0201036c6e64" + "ef" * 40
        v = giudica(F["privata"][0])
        prova("un macaroon che non apre (signature mismatch): non_disponibile, con la decodifica in errore",
              ("non_disponibile", True), (esito(v), v["perche"].startswith("decodifica errore (verification failed")))
        amb["LND_PONTE_MACAROON_LETTURA"] = ""
        visti = len(VISTI)
        prova("senza macaroon nel config: spento, senza bussare", ("non_disponibile", "decodifica spento", visti),
              (lambda v: (esito(v), v["perche"], len(VISTI)))(giudica(F["privata"][0])))
        amb["LND_PONTE_MACAROON_LETTURA"] = MAC_PIENO
        amb["LND_PONTE_CERT"] = altro_cert
        visti = len(VISTI)
        v = giudica(F["privata"][0])
        prova("un certificato che non e' quello guardato: muto, e il macaroon NON e' partito",
              ("non_disponibile", "decodifica muto", visti), (esito(v), v["perche"], len(VISTI)))
        amb["LND_PONTE_CERT"] = cert
        amb["LND_PONTE_URL"] = f"https://127.0.0.1:{porta}/rotta-sbagliata"
        v = giudica(F["privata"][0])
        prova("una ROTTA sbagliata (404 del gateway): non_disponibile, MAI nodo_assente",
              ("non_disponibile", True), (esito(v), "Not Found" in v["perche"]))
        amb["LND_PONTE_URL"] = f"https://127.0.0.1:{porta}"

        # --- 4. la Lightning address: il wallet di cartone, la rete vera --
        v = giudica("privato@wallet.example", 1000)
        prova("un indirizzo il cui wallet da' una fattura di un nodo privato: nodo_assente con la frase dell'indirizzo",
              ("nodo_assente", amb["MSG_INDIRIZZO"]["nodo_assente"], "indirizzo"),
              (esito(v), v["messaggio"], v["tramite"]))
        v = giudica("mario@wallet.example", 1000)
        prova("...uno che da' una fattura raggiungibile: ok", ("ok", "indirizzo"), (esito(v), v["tramite"]))

        # --- 5. il journal non porta mai la fattura ------------------------
        detto.clear()
        for nome in ("pubblica", "privata", "lontana", "cara"):
            amb["_risposta_fattura_p2p"](giudica(F[nome][0], 100000 if nome == "cara" else 1000),
                                         111, "3fcdb207")
        prova("quattro righe di journal, una per controllo, con l'esito in coda",
              ["ok", "nodo_assente", "senza_strada", "costo"],
              [r.rsplit(": ", 1)[1] for r in detto if r.startswith(("✅", "⛔", "⚠️", "·"))])
        prova("...e nessuna porta la fattura, nemmeno un pezzo", False,
              any(F[n][0][:24] in r for n in F for r in detto))
        print("  --- le righe del journal, per chi legge ---")
        for r in detto:
            print("    " + r)

        srv.shutdown()
        srv.server_close()
    print(f"\n  {PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
