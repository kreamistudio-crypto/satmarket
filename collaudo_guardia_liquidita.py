# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA GUARDIA DELLA LIQUIDITA' (11 ott 2026, cantiere
allarme-liquidita).

`prove.py` fa girare i pezzi PURI (la grafica, il giudizio, il passo
degli stati). Qui gira quel che le prove non vedono: il giro intero e
`/canali`, con `_lnd_rest` VERO — il TLS col certificato guardato, il
macaroon nell'header, la GET dei canali, la POST delle strade col
`source_pub_key`, la coppia vietata in base64 e il tetto di Phoenix —
davanti a un LND di cartone che parla HTTPS su 127.0.0.1. Le funzioni
sono prese da server.py con `ast` (mai `import server`); di finto ci
sono il nodo, Telegram (una lista), i timbri (un dizionario) e
l'orologio, che si sposta a mano per vedere il silenzio, il promemoria
del giorno dopo e il rientro.

⚠️ NON SOSTITUISCE IL NODO VERO: la forma delle risposte di LND qui
l'ho scritta io, dal suo `lightning.proto` (v0.19.3) e dalla sonda
girata sul nodo l'11 ott (`deploy/nodo/sonda-rotte.py`). Che la strada
trovata da LND sia quella che il nodo di ACINQ sceglie davvero lo dice
solo un pagamento vero da Phoenix.

Uso:  python collaudo_guardia_liquidita.py
"""
import asyncio
import base64
import html
import http.server
import json
import os
import re
import ssl
import sys
import tempfile
import threading
import time
import types

import httpx

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
# il certificato usa-e-getta, il ritaglio per nome e le costanti del
# ponte: gli stessi del collaudo del controllo della fattura
from collaudo_controllo_fattura import (  # noqa: E402
    SRC, certificato, costanti, pezzo)

PASSATE = FALLITE = 0


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


MAC_PIENO = "0201036c6e64" + "ab" * 40     # offchain:read info:read
MAC_OGGI = "0201036c6e64" + "cd" * 40      # offchain:read e basta
NOI = "02" + "aa" * 32
ACINQ = "03864ef025fde8fb" + "b1" * 25
LNBIG = "03" + "c2" * 32
MEZZO = "02" + "d3" * 32


def canale(pk, nome, scid, cap, loc, rem, attivo=True, sospesi=()):
    # la forma della REST (`/v1/channels`): `chan_id` e' lo scid
    ris = str(cap // 100)
    return {"active": attivo, "remote_pubkey": pk, "peer_alias": nome,
            "channel_point": f"{scid}:0", "chan_id": str(scid),
            "capacity": str(cap), "local_balance": str(loc),
            "remote_balance": str(rem),
            "local_constraints": {"chan_reserve_sat": ris},
            "remote_constraints": {"chan_reserve_sat": ris},
            "pending_htlcs": list(sospesi)}


def canali(entra_acinq=618600, lnbig_vivo=True, entra_lnbig=4930000,
           esce_acinq=371400, nome_lnbig="LNBiG [Hub-2]"):
    return [canale(ACINQ, "ACINQ", 222, 400000, 390777, 8000),
            canale(ACINQ, "ACINQ", 333, 1000000, esce_acinq + 10000,
                   entra_acinq + 10000 - 4000,
                   sospesi=[{"incoming": True, "amount": "21000"}]),
            canale(LNBIG, nome_lnbig, 111, 5000000, 121703,
                   entra_lnbig + 50000, attivo=lnbig_vivo)]


# la scena: quel che il nodo di cartone risponde in questo momento
SCENA = {"canali": canali(), "strada": "ok", "costo": 750, "muto": False}
VISTI = []       # (metodo, percorso, macaroon, corpo)


class FintoLnd(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    def _rispondi(self, codice, corpo):
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        try:
            self.wfile.write((json.dumps(corpo) + "\n").encode())
        except OSError:
            pass      # chi chiedeva se n'e' andato (il caso «muto»)

    def _errore(self, messaggio, codice=500, grpc=2):
        return self._rispondi(codice, {"code": grpc, "message": messaggio,
                                       "details": []})

    def do_GET(self):
        self._servi("GET")

    def do_POST(self):
        self._servi("POST")

    def _servi(self, metodo):
        mac = self.headers.get("Grpc-Metadata-macaroon")
        n = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(n) or b"null") if n else None
        VISTI.append((metodo, self.path, mac, corpo))
        if SCENA["muto"]:
            time.sleep(3)                    # oltre l'attesa del collaudo
        if mac not in (MAC_PIENO, MAC_OGGI):
            return self._errore("verification failed: signature mismatch "
                                "after caveat verification")
        if metodo == "GET" and self.path.startswith("/v1/channels"):
            if "peer_alias_lookup=true" not in self.path:
                # senza la richiesta esplicita la REST non da' i nomi
                return self._rispondi(200, {"channels": [
                    dict(c, peer_alias="") for c in SCENA["canali"]]})
            return self._rispondi(200, {"channels": SCENA["canali"]})
        if mac != MAC_PIENO:                 # da qui serve info:read
            return self._errore("permission denied")
        if metodo == "GET" and self.path == "/v1/getinfo":
            return self._rispondi(200, {"identity_pubkey": NOI,
                                        "version": "0.19.3-beta"})
        m = re.fullmatch(r"/v1/graph/routes/([0-9a-f]{66})/(\d+)", self.path)
        if m and metodo == "POST":
            sats = int(m.group(2))
            corpo = corpo or {}
            if m.group(1) != NOI or corpo.get("source_pub_key") != ACINQ:
                return self._errore("unable to find a path to destination")
            vietate = [(base64.b64decode(p["from"]).hex(),
                        base64.b64decode(p["to"]).hex())
                       for p in corpo.get("ignored_pairs") or []]
            if (ACINQ, NOI) not in vietate:
                # il canale diretto: un salto, gratis
                return self._rispondi(200, {"routes": [{
                    "total_fees_msat": "0", "hops": [
                        {"chan_id": "333", "pub_key": NOI, "fee_msat": "0"}]}]})
            tetto = (corpo.get("fee_limit") or {}).get("fixed")
            if SCENA["strada"] == "nessuna" or (
                    tetto is not None and SCENA["costo"] > int(tetto)):
                return self._errore("unable to find a path to destination")
            costo = SCENA["costo"] * 1000
            return self._rispondi(200, {"routes": [{
                "total_fees_msat": str(costo), "total_amt": str(sats),
                "hops": [
                    {"chan_id": "999", "pub_key": MEZZO, "fee_msat": "1000"},
                    {"chan_id": "998", "pub_key": LNBIG,
                     "fee_msat": str(costo - 1000)},
                    {"chan_id": "111", "pub_key": NOI, "fee_msat": "0"}]}]})
        return self._errore("Not Found", 404, 5)


def costanti_guardia():
    """Le leve e le costanti della guardia, dal sorgente."""
    amb = {}
    i = SRC.index("try:\n    from config import GUARDIA_LIQUIDITA")
    exec(SRC[i:SRC.index("\n\n\ndef _sats_canale(", i)], amb)
    amb.pop("__builtins__", None)
    return amb


def main():
    print("\n[la guardia della liquidita' e /canali, contro un LND di cartone]")
    with tempfile.TemporaryDirectory() as tmp:
        cert, chiave = certificato(tmp, "lnd")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FintoLnd)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, chiave)
        srv.socket = tls.wrap_socket(srv.socket, server_side=True)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        porta = srv.server_address[1]

        detto, mandati, bot, timbri, fatti = [], [], [], {}, []
        ORA = [1_800_000_000.0]

        async def manda(chat, testo, bottone=None):
            fatti.append("invio")
            mandati.append((chat, testo))
            return "simulata (collaudo)"

        async def bot_api(metodo, dati):
            bot.append((metodo, dati))

        async def sconosciuto(chat):
            bot.append(("sconosciuto", chat))

        def timbro_scrivi(nome, valore):
            fatti.append("timbro")
            timbri[nome] = valore

        async def _senza_margine():
            return []

        amb = {**costanti(), **costanti_guardia(),
               "ssl": ssl, "httpx": httpx, "json": json, "re": re,
               "asyncio": asyncio, "base64": base64, "html": html,
               "time": types.SimpleNamespace(time=lambda: ORA[0]),
               "LND_PONTE_URL": f"https://127.0.0.1:{porta}",
               "LND_PONTE_CERT": cert,
               "LND_PONTE_MACAROON_LETTURA": MAC_PIENO,
               "LND_FATTURA_ATTESA_S": 2,
               "GUARDIA_LIQUIDITA": True, "LIQUIDITA_SCAMBIO_MAX": 500000,
               "LIQUIDITA_PHOENIX_MIN": 300000, "LIQUIDITA_USCITA_MIN": 0,
               "LIQUIDITA_PROMEMORIA_S": 86400,
               "GUARDIANO_PONTE_AVVISA": [], "ADMIN_IDS": [999],
               # il gruppo degli admin (12 ott 2026) qui e' SPENTO: la
               # porta vera risponde False e l'avviso prende la strada
               # di sempre; il gruppo acceso sta in collaudo_canale_admin
               "_GRUPPO_ADMIN": {"id": 0, "stanze": {}, "giu": None,
                                 "piano_fino": 0.0},
               "_manda_telegram": manda, "bot_api": bot_api,
               "_comando_sconosciuto": sconosciuto,
               "tastiera_bot": lambda *a: {"tastiera": True},
               "e_admin_bot": lambda m: m.get("id") == 999,
               "timbro_letto": lambda nome: timbri.get(nome, ""),
               "timbro_scrivi": timbro_scrivi,
               # (27 ott 2026) la sesta domanda, per cassaforte, qui tace:
               # la prova il collaudo del margine, sul server vero
               "_voci_margine": _senza_margine,
               "print": lambda *a, **k: detto.append(" ".join(map(str, a)))}
        for nome in ("_lnd_configurato", "_fmt_sats", "_destinatari_ponte",
                     "_lnd_rest", "_sats_canale", "_taglia_canale",
                     "_nome_canale", "_numeri_liquidita", "_grafica_canali",
                     "_tetto_phoenix", "_strada_phoenix",
                     "_giudizio_liquidita", "_liquidita_passo",
                     "_liquidita_stato_letto", "_da_quanto",
                     "_testo_liquidita", "_al_gruppo_admin",
                     "_avvisa_liquidita",
                     "_quadro_liquidita", "_giro_guardia_liquidita",
                     "_guardia_liquidita_attiva", "comando_canali"):
            exec(pezzo(nome), amb)

        def giro(ore=1.0):
            """Passano `ore`, poi un giro. Torna (azione, avvisi nuovi)."""
            ORA[0] += ore * 3600
            prima = len(mandati)
            azione = asyncio.run(amb["_giro_guardia_liquidita"]())
            return azione, [t for _, t in mandati[prima:]]

        def strade_chieste():
            return [v for v in VISTI if "/v1/graph/routes/" in v[1]]

        # --- 1. /canali ---------------------------------------------------
        asyncio.run(amb["comando_canali"]({"id": 111}, "/canali"))
        prova("/canali da chi non e' admin: la risposta di un comando "
              "sconosciuto, e LND non si disturba",
              ([("sconosciuto", 111)], 0), (bot, len(VISTI)))
        bot.clear()
        SCENA["canali"] = canali(nome_lnbig="LNBiG <b>[Hub-2]</b>")
        asyncio.run(amb["comando_canali"]({"id": 999}, "/canali"))
        testo = bot[-1][1]["text"]
        print("  --- /canali, com'e' partito ---")
        for r in testo.split("\n"):
            print("    " + r)
        prova("/canali dall'admin: un messaggio in HTML, a chi l'ha chiesto",
              ("sendMessage", 999, "HTML"),
              (bot[-1][0], bot[-1][1]["chat_id"], bot[-1][1]["parse_mode"]))
        prova("...i canali chiesti COI NOMI (la REST senza la richiesta "
              "non li da')", "/v1/channels?peer_alias_lookup=true",
              VISTI[0][1])
        prova("...il canale piu' grosso per primo, con la barretta, i sats "
              "e lo stato", True,
              "🟢 LNBiG &lt;b&gt;[Hub-2]&lt;/b&gt; · 5M\n"
              "[░░░░░░░░░░] ↑ 71.703 ↓ 4.930.000\n"
              "in linea · nessun HTLC in sospeso" in testo)
        prova("...il nome di un nodo NON diventa un tag di Telegram", False,
              "<b>[Hub-2]</b>" in testo)
        prova("...l'HTLC in sospeso, con la somma", True,
              "🟢 ACINQ · 1M\n[████░░░░░░] ↑ 371.400 ↓ 614.600\n"
              "in linea · 1 HTLC in sospeso (21.000 sats)" in testo)
        prova("...i totali dei canali in linea", True,
              "Totale, 3 in linea su 3:\n"
              "↑ esce 829.880 · ↓ entra 5.548.600" in testo)
        prova("...le tre domande, e la guardia dice che e' accesa", True,
              "✅ Entrata: 5.548.600 sats in tutto" in testo
              and "✅ Da Phoenix: canale ACINQ a 618.600 sats." in testo
              and "• Uscita: 829.880 sats in tutto (nessun minimo impostato)."
              in testo and "La guardia è accesa" in testo)
        prova("...con ACINQ sopra la soglia la strada NON si chiede a LND",
              [], strade_chieste())
        prova("/canali non timbra e non avvisa nessuno", ({}, []),
              (timbri, mandati))
        SCENA["canali"] = canali()

        # --- 2. il caso di oggi: ACINQ basso, ma la strada c'e' -----------
        VISTI.clear()
        azione, nuovi = giro()
        prova("nodo sano: la guardia tace", ("", []), (azione, nuovi))
        SCENA["canali"] = canali(entra_acinq=179616)
        azione, nuovi = giro()
        prova("ACINQ a 179.616 (l'allarme di ieri), 5 milioni da LNBiG e "
              "una strada da 750 sats: la guardia TACE",
              ("", [], {}), (azione, nuovi, timbri))
        s = strade_chieste()
        prova("...perche' l'ha chiesta a LND: una POST, da ACINQ a noi, per "
              "300.000", (1, f"/v1/graph/routes/{NOI}/300000", ACINQ, False),
              (len(s), s[-1][1], s[-1][3]["source_pub_key"],
               s[-1][3]["use_mission_control"]))
        prova("...col canale diretto VIETATO (la coppia da ACINQ a noi, in "
              "base64) e il tetto di Phoenix (4 + 0,4 % = 1.204)",
              ([{"from": base64.b64encode(bytes.fromhex(ACINQ)).decode(),
                 "to": base64.b64encode(bytes.fromhex(NOI)).decode()}],
               {"fixed": "1204"}),
              (s[-1][3]["ignored_pairs"], s[-1][3]["fee_limit"]))
        asyncio.run(amb["comando_canali"]({"id": 999}, "/canali"))
        prova("...e /canali lo racconta", True,
              "✅ Da Phoenix: canale ACINQ a 179.616 sats, ma 300.000 "
              "entrano da LNBiG [Hub-2] (costo 750 sats, Phoenix ne lascia "
              "1.204)." in bot[-1][1]["text"])

        # --- 3. la strada diventa troppo cara: UN avviso, poi silenzio ----
        SCENA["costo"] = 5000
        fatti.clear()
        VISTI.clear()
        azione, nuovi = giro()
        prova("la strada sale a 5.000 sats (oltre il tetto): ALLARME, uno",
              ("allarme", 1), (azione, len(nuovi)))
        prova("...due domande: col tetto («non c'e'»), poi senza (c'e', e "
              "costa)", [True, False],
              ["fee_limit" in v[3] for v in strade_chieste()])
        print("  --- l'allarme, com'e' partito ---")
        for r in nuovi[0].split("\n"):
            print("    " + r)
        prova("...dice cosa non va, con le cifre", True,
              nuovi[0].startswith("⚠️ <b>Liquidità del nodo: c'è un problema</b>")
              and "⚠️ Da Phoenix: canale ACINQ a 179.616 sats. L'altra "
                  "strada, da LNBiG [Hub-2], costa 5.000 sats: più dei 1.204 "
                  "che Phoenix lascia spendere per 300.000." in nuovi[0])
        prova("...porta la grafica dei canali e i totali", True,
              "🟢 ACINQ · 1M\n[███████░░░] ↑ 371.400 ↓ 175.616" in nuovi[0]
              and "Totale, 3 in linea su 3:" in nuovi[0])
        prova("...e dice che non lo ripetera'", True,
              "Non lo ripeto" in nuovi[0] and "24 ore" in nuovi[0])
        prova("...il timbro e' scritto PRIMA dell'invio", ["timbro", "invio"],
              fatti)
        prova("...ai moderatori (la leva del ponte e' vuota)", [999],
              [c for c, _ in mandati])
        for n in range(3):
            azione, nuovi = giro()
            if (azione, nuovi) != ("", []):
                break
        prova("le tre ore dopo, uguale: silenzio", ("", []), (azione, nuovi))
        azione, nuovi = giro(20.5)
        prova("a 23 ore e mezza dall'avviso: ancora silenzio", ("", []),
              (azione, nuovi))
        azione, nuovi = giro(0.5)
        prova("a 24 ore: UN promemoria, che dice da quanto",
              ("promemoria", True),
              (azione, nuovi and nuovi[0].startswith(
                  "⏰ <b>Liquidità del nodo: ancora da sistemare</b> "
                  "(da 24 ore)")))
        azione, nuovi = giro()
        prova("...e l'ora dopo di nuovo silenzio", ("", []), (azione, nuovi))

        # --- 4. un riavvio del server non raddoppia l'allarme -------------
        prova("lo stato vive nei timbri (un deploy non lo azzera)",
              ["phoenix"], json.loads(timbri["liquidita_stato"])["chiavi"])
        azione, nuovi = giro()
        prova("...e il primo giro dopo il riavvio tace", ("", []),
              (azione, nuovi))

        # --- 5. quel che non si puo' misurare non cambia lo stato ---------
        amb["LND_PONTE_MACAROON_LETTURA"] = MAC_OGGI
        SCENA["costo"] = 750
        azione, nuovi = giro()
        prova("macaroon senza info:read (la strada non si misura) mentre "
              "si era in allarme: NIENTE «rientrato»", ("", []),
              (azione, nuovi))
        asyncio.run(amb["comando_canali"]({"id": 999}, "/canali"))
        prova("...e /canali lo dice col punto di domanda", True,
              "❔ Da Phoenix: canale ACINQ a 179.616 sats. L'altra strada "
              "non l'ho potuta misurare (getinfo negato)."
              in bot[-1][1]["text"])
        amb["LND_PONTE_MACAROON_LETTURA"] = MAC_PIENO
        SCENA["muto"] = True
        azione, nuovi = giro()
        prova("LND muto: giro saltato, nessun avviso, stato com'era",
              ("saltato", [], ["phoenix"]),
              (azione, nuovi, json.loads(timbri["liquidita_stato"])["chiavi"]))
        asyncio.run(amb["comando_canali"]({"id": 999}, "/canali"))
        prova("...e /canali dice che il nodo non risponde", True,
              "il nodo non risponde dal ponte" in bot[-1][1]["text"])
        SCENA["muto"] = False

        # --- 6. torna buona: UN avviso, poi silenzio ----------------------
        azione, nuovi = giro()
        prova("la strada torna a 750 sats: RIENTRATO, uno, con la grafica",
              ("rientrato", True, True),
              (azione, nuovi and nuovi[0].startswith(
                  "✅ <b>Liquidità del nodo: tornata a posto</b> (dopo "),
               nuovi and "Totale, 3 in linea su 3:" in nuovi[0]))
        prova("...e lo stato e' pulito", {},
              json.loads(timbri["liquidita_stato"]))
        azione, nuovi = giro()
        prova("...l'ora dopo: silenzio", ("", []), (azione, nuovi))

        # --- 7. una domanda nuova che va male parla subito ----------------
        SCENA["strada"] = "nessuna"
        azione, nuovi = giro()
        prova("LND non trova piu' nessuna strada: ALLARME",
              ("allarme", True),
              (azione, nuovi and "LND non trova un'altra strada da ACINQ "
                                 "per 300.000 sats" in nuovi[0]))
        SCENA["canali"] = canali(entra_acinq=179616, lnbig_vivo=False)
        azione, nuovi = giro()
        prova("un'ora dopo LNBiG va fuori linea e l'entrata totale crolla: "
              "e' una notizia NUOVA, parla subito (non aspetta il promemoria)",
              ("allarme", True, True, True),
              (azione, "⚠️ Entrata: solo 179.616 sats in tutto. Una garanzia "
                       "da 500.000 non entra." in nuovi[0],
               "🔴 LNBiG [Hub-2] · 5M" in nuovi[0] and "FUORI LINEA" in nuovi[0],
               "Totale, 2 in linea su 3:" in nuovi[0]))
        SCENA["canali"] = canali(entra_acinq=179616)
        azione, nuovi = giro()
        prova("LNBiG torna, la strada no: una domanda in meno NON e' un "
              "rientro, silenzio", ("", [], ["phoenix"]),
              (azione, nuovi, json.loads(timbri["liquidita_stato"])["chiavi"]))
        SCENA["canali"] = canali()
        azione, nuovi = giro()
        prova("ACINQ risale sopra la soglia: rientrato, senza chiedere strade "
              "a LND", "rientrato", azione)

        # --- 8. il pavimento d'uscita, quando la leva e' scritta ----------
        amb["LIQUIDITA_USCITA_MIN"] = 900000
        azione, nuovi = giro()
        prova("LIQUIDITA_USCITA_MIN a 900.000 con 829.880 d'uscita: ALLARME",
              ("allarme", True),
              (azione, "⚠️ Uscita: 829.880 sats in tutto, sotto il minimo di "
                       "900.000." in nuovi[0]))
        amb["LIQUIDITA_USCITA_MIN"] = 0
        azione, nuovi = giro()
        prova("...leva di nuovo a zero: rientrato", "rientrato", azione)

        # --- 8-bis. la quarta domanda (15 ott 2026) ------------------------
        # il canale piu' carico in uscita e' ACINQ 400k: 386.777 spendibili
        exec(pezzo("_tetto_p2p_in_sats"), amb)
        CAMBIO = [100000.0]

        async def cambio_finto():
            return CAMBIO[0]
        amb.update(P2P_MAX_EURO=250, cambio_btc_eur=cambio_finto,
                   LIQUIDITA_USCITA_CANALE=True)
        azione, nuovi = giro()
        prova("quarta accesa, 250 € a 100.000 €/BTC = 250.000 sats, il canale "
              "piu' carico ne ha 386.777: silenzio", ("", []), (azione, nuovi))
        CAMBIO[0] = 60000.0
        azione, nuovi = giro()
        prova("...a 60.000 €/BTC fanno 416.667: ALLARME, col canale e le cifre",
              ("allarme", True),
              (azione, bool(nuovi) and "⚠️ Nessun canale regge da solo un ordine da "
               "250 € (416.667 sats): il più carico in uscita è ACINQ, con "
               "386.777 sats." in nuovi[0]))
        CAMBIO[0] = 0.0
        azione, nuovi = giro()
        prova("...il cambio non risponde: un «non so», niente rientro e niente "
              "allarme nuovo", ("", ["canale_uscita"]),
              (azione, json.loads(timbri["liquidita_stato"])["chiavi"]))
        CAMBIO[0] = 100000.0
        azione, nuovi = giro()
        prova("...il cambio torna a 100.000: rientrato", "rientrato", azione)
        amb["LIQUIDITA_USCITA_CANALE"] = False

        # --- 8-ter. la quinta domanda (15 ott 2026) ------------------------
        def con_tetti(cc, appesi_in=()):
            fuori = []
            for c in cc:
                c = json.loads(json.dumps(c))
                if c["remote_pubkey"] == ACINQ:
                    cap = int(c["capacity"])
                    c["local_constraints"]["max_pending_amt_msat"] = str(cap * 450)
                    c["remote_constraints"]["max_pending_amt_msat"] = str(cap * 990)
                    if c["chan_id"] == "333":
                        c["pending_htlcs"] += [{"incoming": True, "amount": str(a)}
                                               for a in appesi_in]
                fuori.append(c)
            return fuori
        amb["LIQUIDITA_ACINQ_TETTO"] = True
        SCENA.update(canali=con_tetti(canali()), strada="ok")
        prima_strade = len(strade_chieste())
        azione, nuovi = giro()
        prova("quinta accesa, posto 429.000 sul canale grande: silenzio, e nessuna "
              "strada chiesta", ("", [], 0),
              (azione, nuovi, len(strade_chieste()) - prima_strade))
        SCENA["canali"] = con_tetti(canali(), (200000,))
        azione, nuovi = giro()
        prova("...una garanzia da 200.000 appesa: posto 229.000, la strada da LNBiG "
              "c'e' (chiesta UNA volta): silenzio", ("", [], 1),
              (azione, nuovi, len(strade_chieste()) - prima_strade))
        SCENA["strada"] = "nessuna"
        azione, nuovi = giro()
        prova("...e senza strada: ALLARME, col posto, il tetto e gli appesi",
              ("allarme", True),
              (azione, bool(nuovi) and "⚠️ Tetto di ACINQ: dal canale diretto entrano "
               "solo 229.000 sats (tetto 450.000, appesi 221.000), e LND non trova "
               "un'altra strada da ACINQ per 300.000 sats." in nuovi[0]))
        SCENA["canali"] = canali()
        azione, nuovi = giro()
        prova("...LND smette di dire i tetti: un «non so», niente rientro e niente "
              "allarme nuovo", ("", ["acinq_tetto"]),
              (azione, json.loads(timbri["liquidita_stato"])["chiavi"]))
        SCENA["canali"] = con_tetti(canali())
        azione, nuovi = giro()
        prova("...la garanzia si chiude: rientrato", "rientrato", azione)
        SCENA.update(canali=canali(), strada="ok")
        amb["LIQUIDITA_ACINQ_TETTO"] = False

        # --- 9. il journal -------------------------------------------------
        prova("nel journal una riga per ogni cambio, e mai il macaroon",
              (True, False),
              (any(r.startswith("💧 Guardia della liquidità: allarme (phoenix)")
                   for r in detto),
               any(MAC_PIENO in r or MAC_OGGI in r for r in detto)))
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
