# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA CASSETTA POSTALE NIP-46 (10 ott 2026).

Dal campo: su iPhone chi entra con Clave copia il link nostrconnect,
passa all'app, approva e torna — e mentre era via iOS ha sospeso la
pagina e chiuso le websocket. La risposta del firmatario (kind 24133,
effimero) e' arrivata sui relay in quel momento e nessuno l'ha sentita.
La cura e' sul server: la pagina deposita la sua chiave effimera e i
relay (`POST /api/login/nostr/cassetta`), il server ascolta al posto
suo e la pagina si porta via gli eventi quando torna (`GET`).

QUI GIRA IL SERVER VERO col banco di `collaudo_lnbits_muto` (config
finto, database usa-e-getta, MODALITA_COLLAUDO): le due rotte, il
giudice dei relay, il freno, e — con una connessione di CARTONE al posto
di `websocket-client` — l'orecchio che legge un 24133 dal relay e lo
mette nella cassetta giusta, scarta le copie, e aggiorna il filtro
quando una seconda cassetta nomina lo stesso relay. Verso un relay
pubblico vero, in collaudo, l'orecchio NON esce (`lettura_simulata`): lo
stato lo dice, e la pagina lo legge.

NESSUNA RETE: il relay e' una coda in memoria.

LE FIRME LE FA `schnorr_puro` (24 ott 2026, cantiere
collaudi-senza-coincurve): la chiave effimera della pagina firma con la
ricetta BIP-340 del repo, e il server verifica col suo giudice VERO —
coincurve dove c'e' (il PC, il VPS), e in CI, dove non c'e',
`schnorr_puro.ChiaveXOnly` montato al posto di `ChiavePubblicaNostr`,
come `collaudo_fusione_da_telegram`. Prima di montarlo si guarda che il
server, da solo, non spedisca niente.

USO:  python collaudo_cassetta_nip46.py
"""

import json
import os
import queue
import threading
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova
VIA = "/api/login/nostr/cassetta"
PUB_A = "a" * 64
PUB_B = "b" * 64
RELAY_CASA = "ws://127.0.0.1:7791"       # di casa: in collaudo l'orecchio esce


class WsCartone:
    """La websocket di cartone: tiene le REQ mandate e serve dalla
    coda quel che il banco ci mette. `recv` aspetta al massimo il
    timeout e poi alza come fa websocket-client."""
    mandate = []
    coda = queue.Queue()
    aperte = 0
    passi = []          # i timeout che l'orecchio chiede alla websocket

    def __init__(self, relay, timeout=10, sslopt=None):
        WsCartone.aperte += 1
        self.relay = relay
        self.t = timeout

    def settimeout(self, t):
        self.t = t
        WsCartone.passi.append(t)

    def send(self, s):
        WsCartone.mandate.append(json.loads(s))

    def recv(self):
        try:
            return WsCartone.coda.get(timeout=self.t)
        except queue.Empty:
            raise TimeoutError("timed out")

    def close(self):
        pass


class WsPostino:
    """IL SECONDO POSTINO DI CARTONE (20 ott 2026, cantiere nostr-da-
    telefono): la connessione con cui la cassetta SPEDISCE un 24133. Non
    pesca dalla coda dell'orecchio (gli ruberebbe la posta): tiene
    l'EVENT mandato e risponde l'OK che il banco ha deciso."""
    spediti = []
    risposta = True
    chiuse = 0

    def __init__(self, relay, timeout=5):
        self.relay = relay
        self.ultimo = None

    def settimeout(self, t):
        pass

    def send(self, s):
        self.ultimo = json.loads(s)
        WsPostino.spediti.append((self.relay, self.ultimo))

    def recv(self):
        return json.dumps(["OK", self.ultimo[1]["id"], WsPostino.risposta, ""])

    def close(self):
        WsPostino.chiuse += 1


def connetti(relay, timeout=10, **kw):
    """La porta del banco: l'orecchio passa `sslopt` e prende il cartone
    della coda; la spedizione a un relay di casa no, e prende il postino."""
    if "sslopt" in kw:
        return WsCartone(relay, timeout, kw["sslopt"])
    return WsPostino(relay, timeout)


def nuova_chiave() -> bytes:
    """Una chiave effimera usa-e-getta, 32 byte nella misura del BIP-340."""
    while True:
        sk = os.urandom(32)
        if 1 <= int.from_bytes(sk, "big") < schnorr_puro.N:
            return sk


def pubblica_hex(sk: bytes) -> str:
    return schnorr_puro.pubblica(sk).hex()


def ventiquattro(sk, verso, testo="cifrato", ora=None):
    """Un 24133 FIRMATO DAVVERO dalla chiave effimera `sk` (schnorr_puro):
    la spedizione ricontrolla id e firma, e un evento finto non passa."""
    import hashlib
    pub = pubblica_hex(sk)
    ev = {"pubkey": pub, "created_at": int(ora or time.time()), "kind": 24133,
          "tags": [["p", verso]], "content": testo}
    serial = json.dumps([0, pub, ev["created_at"], 24133, ev["tags"], testo],
                        separators=(",", ":"), ensure_ascii=False)
    ev["id"] = hashlib.sha256(serial.encode("utf-8")).hexdigest()
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"]),
                                   os.urandom(32)).hex()
    return ev


def evento(pub, ev_id, contenuto="cifrato"):
    return {"id": ev_id, "pubkey": "c" * 64, "created_at": int(time.time()),
            "kind": 24133, "tags": [["p", pub]], "content": contenuto,
            "sig": "d" * 128}


# IL TETTO DELL'ATTESA NON E' IL TEMPO DELL'ORECCHIO (13 ott 2026, cantiere
# cassetta-orecchio-sveglio): erano 3000 ms, e 3 secondi era anche la
# `recv` a vuoto dell'orecchio — un PARI. Una seconda cassetta depositata
# un attimo dopo l'inizio di una `recv` aspettava tutti e tre i secondi, e
# la riga «l'orecchio rimanda la REQ» cadeva per qualche millisecondo
# (una rossa su nove giri sotto carico, cinque verdi su cinque da solo).
# L'attesa torna appena la condizione e' vera, quindi un tetto largo non
# costa niente a un giro verde: dieci secondi, venti volte il passo.
def aspetta(cond, ms=10000):
    fine = time.time() + ms / 1000
    while time.time() < fine:
        if cond():
            return True
        time.sleep(0.02)
    return cond()


def main():
    print("=" * 58)
    print("  LA CASSETTA POSTALE NIP-46 — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient
    S = banco.SRV
    c = TestClient(S.app)
    S._cassetta_connetti = connetti         # il cartone al posto del filo
    S.CASSETTA_ORECCHIO_RIPOSO_S = 1        # senza cassette si chiude presto

    print("\n[la porta: cosa si accetta]")
    r = c.post(VIA, json={"pub": "zz", "relays": [RELAY_CASA]})
    prova("una chiave che non e' hex64 e' un 400", 400, r.status_code)
    r = c.post(VIA, json={"pub": PUB_A})
    prova("senza relay e' un 400", 400, r.status_code)
    r = c.post(VIA, json={"pub": PUB_A, "relays": ["http://x.example", "wss://1.2.3.4",
                                                  "wss://user:pw@relay.example",
                                                  "ws://relay.example"]})
    prova("solo relay non ammessi (http, un IP nudo, credenziali, ws:// "
          "non di casa) e' un 400 che lo dice", (400, True),
          (r.status_code, "wss://" in r.json().get("detail", "")))
    r = c.post(VIA, json={"pub": PUB_A, "relays": [RELAY_CASA, "wss://1.2.3.4",
                                                  "wss://relay.example"]})
    prova("si apre con i relay buoni e si nominano quelli scartati",
          (200, [RELAY_CASA, "wss://relay.example"], ["wss://1.2.3.4"]),
          (r.status_code, r.json().get("relays"), r.json().get("rifiutati")))
    prova("...e dice quanto vive", S.CASSETTA_VITA_S, r.json().get("vita"))

    print("\n[gli orecchi: di casa esce, verso un relay pubblico no]")
    prova("l'orecchio di casa si e' aperto sul cartone",
          True, aspetta(lambda: WsCartone.aperte >= 1))
    g = c.get(VIA, params={"pub": PUB_A, "dopo": 0})
    prova("la cassetta e' viva e vuota", (True, []),
          (g.json().get("viva"), g.json().get("eventi")))
    prova("...e lo stato dell'orecchio pubblico e' «simulato» (in collaudo "
          "non si esce dal computer), quello di casa «connesso»",
          ("simulato", "connesso"),
          (g.json()["orecchi"].get("wss://relay.example", {}).get("stato"),
           (aspetta(lambda: c.get(VIA, params={"pub": PUB_A}).json()
                    ["orecchi"][RELAY_CASA]["stato"] == "connesso")
            and "connesso")))
    req = [m for m in WsCartone.mandate if m[0] == "REQ"]
    prova("la REQ chiede i 24133 verso la chiave, con un since",
          ([24133], [PUB_A], True),
          (req[-1][2].get("kinds"), req[-1][2].get("#p"), "since" in req[-1][2]))

    print("\n[la posta: un evento entra, le copie no]")
    WsCartone.coda.put(json.dumps(["EVENT", "cassetta", evento(PUB_A, "1" * 64)]))
    prova("l'evento letto dal relay finisce nella cassetta",
          True, aspetta(lambda: len(c.get(VIA, params={"pub": PUB_A}).json()["eventi"]) == 1))
    g = c.get(VIA, params={"pub": PUB_A, "dopo": 0}).json()
    e = g["eventi"][0]
    prova("...con la forma di un evento Nostr, il relay di provenienza e "
          "il contatore", (24133, RELAY_CASA, 1, "cifrato"),
          (e["evento"]["kind"], e["via"], e["n"], e["evento"]["content"]))
    WsCartone.coda.put(json.dumps(["EVENT", "cassetta", evento(PUB_A, "1" * 64)]))
    WsCartone.coda.put(json.dumps(["EVENT", "cassetta", evento(PUB_B, "2" * 64)]))
    WsCartone.coda.put(json.dumps(["EVENT", "cassetta", evento(PUB_A, "3" * 64)]))
    prova("la copia (stesso id) non entra; quello per una cassetta che "
          "non c'e' si butta; il secondo entra",
          True, aspetta(lambda: c.get(VIA, params={"pub": PUB_A}).json()["n"] == 2))
    g = c.get(VIA, params={"pub": PUB_A, "dopo": 1}).json()
    prova("con `dopo` si prende solo il nuovo", (1, "3" * 64),
          (len(g["eventi"]), g["eventi"][0]["evento"]["id"]))
    g = c.get(VIA, params={"pub": PUB_B}).json()
    prova("la cassetta che non c'e' risponde «non viva», senza inventare",
          (False, []), (g.get("viva"), g.get("eventi")))

    print("\n[una seconda cassetta sullo stesso relay: il filtro si allarga]")
    prima = len([m for m in WsCartone.mandate if m[0] == "REQ"])
    r = c.post(VIA, json={"pub": PUB_B, "relays": [RELAY_CASA]})
    prova("si apre", 200, r.status_code)
    prova("...e l'orecchio rimanda la REQ con TUTTE E DUE le chiavi, "
          "senza aprire una seconda connessione", (True, 1),
          (aspetta(lambda: len([m for m in WsCartone.mandate if m[0] == "REQ"]) > prima
                   and sorted([m for m in WsCartone.mandate if m[0] == "REQ"][-1][2]["#p"])
                   == [PUB_A, PUB_B]),
           WsCartone.aperte))
    # IL PASSO DELL'ORECCHIO: finche' una `recv` a vuoto non torna
    # l'orecchio non guarda se le chiavi sono cambiate, quindi quel tempo
    # e' la finestra in cui la chiave nuova resta FUORI dal filtro — e un
    # 24133 e' effimero. Non si cronometra (su un runner lento ballerebbe):
    # si guarda il numero che l'orecchio ha chiesto alla websocket.
    prova("...e l'orecchio si sveglia almeno una volta al secondo: e' il tempo "
          "massimo in cui la chiave di una seconda cassetta resta senza ascolto",
          (True, S.CASSETTA_ORECCHIO_PASSO_S),
          (0 < S.CASSETTA_ORECCHIO_PASSO_S <= 1, WsCartone.passi[-1] if WsCartone.passi else None))
    WsCartone.coda.put(json.dumps(["EVENT", "cassetta", evento(PUB_B, "4" * 64)]))
    prova("...e adesso la posta di B entra", True,
          aspetta(lambda: c.get(VIA, params={"pub": PUB_B}).json()["n"] == 1))

    print("\n[il freno e il tetto]")
    r = c.post(VIA, json={"pub": "f" * 64, "relays": [RELAY_CASA]},
               headers={"host": "abcdefghijklmnop.onion",
                        "origin": "http://abcdefghijklmnop.onion"})
    prova("dall'onion si apre uguale (nessun freno per IP: l'IP non c'e')",
          200, r.status_code)
    with S._CASSETTE_LOCK:
        S._CASSETTE.pop("f" * 64, None)
    r = c.post(VIA, json={"pub": PUB_A, "relays": [RELAY_CASA]})
    prova("riaprire la stessa cassetta rinnova e basta", 200, r.status_code)
    tetto = S.CASSETTA_TETTO
    S.CASSETTA_TETTO = 2
    r = c.post(VIA, json={"pub": "e" * 64, "relays": [RELAY_CASA]})
    prova("al tetto delle cassette aperte si rifiuta con un 503 che lo dice",
          (503, True), (r.status_code, "Troppi" in r.json().get("detail", "")))
    S.CASSETTA_TETTO = tetto

    print("\n[i limiti: oltre, un errore e nessun thread nuovo]")
    IP = {"x-forwarded-for": "93.184.216.34"}
    orecchi_prima = len(S._orecchi_aperti())
    per_ip = S.CASSETTA_PER_IP
    S.CASSETTA_PER_IP = 2
    esiti = [c.post(VIA, json={"pub": f"{k}" * 64, "relays": [RELAY_CASA]},
                    headers=IP).status_code for k in ("1", "2", "3")]
    prova("per IP: due si aprono, la terza e' un 429", [200, 200, 429], esiti)
    r = c.post(VIA, json={"pub": "3" * 64, "relays": [RELAY_CASA]}, headers=IP)
    prova("...che lo dice", True, "questa rete" in r.json().get("detail", ""))
    prova("...e lo stesso IP puo' RINNOVARE una sua cassetta (non e' una "
          "nuova)", 200, c.post(VIA, json={"pub": "1" * 64, "relays": [RELAY_CASA]},
                               headers=IP).status_code)
    S.CASSETTA_PER_IP = per_ip
    orecchi_max = S.CASSETTA_ORECCHI_MAX
    S.CASSETTA_ORECCHI_MAX = len(S._orecchi_aperti())
    r = c.post(VIA, json={"pub": "4" * 64, "relays": ["wss://nuovo.relay.example"]})
    prova("al tetto degli orecchi un relay NUOVO si rifiuta: 503 che lo dice, "
          "e nessun thread", (503, True, orecchi_prima),
          (r.status_code, "relay in ascolto" in r.json().get("detail", ""),
           len(S._orecchi_aperti())))
    r = c.post(VIA, json={"pub": "4" * 64, "relays": [RELAY_CASA, "wss://nuovo.relay.example"]})
    prova("...con un relay gia' in ascolto accanto si apre su quello, e il "
          "nuovo e' fra i rifiutati con la ragione", (200, [RELAY_CASA], True),
          (r.status_code, r.json().get("relays"),
           any("troppi relay" in x for x in r.json().get("rifiutati", []))))
    S.CASSETTA_ORECCHI_MAX = orecchi_max
    tetto = S.CASSETTA_TETTO
    S.CASSETTA_TETTO = len(S._CASSETTE)
    r = c.post(VIA, json={"pub": "5" * 64, "relays": [RELAY_CASA]})
    prova("al tetto totale una cassetta nuova e' un 503, e nessun thread",
          (503, orecchi_prima), (r.status_code, len(S._orecchi_aperti())))
    S.CASSETTA_TETTO = tetto
    prova("i numeri scelti: 300 in tutto, 5 per IP, 6 relay per cassetta, "
          "20 relay in ascolto", (300, 5, 6, 20),
          (S.CASSETTA_TETTO, S.CASSETTA_PER_IP, S.CASSETTA_RELAY_MAX,
           S.CASSETTA_ORECCHI_MAX))
    secchio = S._SECCHI
    secchio.clear()
    esiti = [c.post(VIA, json={"pub": "6" * 64, "relays": [RELAY_CASA]},
                    headers={"x-forwarded-for": "8.8.8.8"}).status_code
             for _ in range(31)]
    prova("il deposito ha il freno delle porte del login: trenta al minuto "
          "per IP, il trentunesimo e' un 429", (30, 429),
          (esiti.count(200), esiti[-1]))
    secchio.clear()
    for k in ("1", "2", "3", "4", "5", "6"):
        with S._CASSETTE_LOCK:
            S._CASSETTE.pop(k * 64, None)

    print("\n[la chiusura dalla pagina]")
    r = c.post(VIA, json={"pub": "7" * 64, "relays": [RELAY_CASA]})
    biglietto = r.json().get("biglietto")
    prova("il deposito torna un biglietto", True, bool(biglietto) and len(biglietto) == 32)
    prova("...che resta lo stesso al rinnovo", biglietto,
          c.post(VIA, json={"pub": "7" * 64, "relays": [RELAY_CASA]}).json().get("biglietto"))
    r = c.post(VIA + "/chiudi", json={"pub": "7" * 64, "biglietto": "sbagliato"})
    prova("chiudere col biglietto sbagliato e' un 403, e la cassetta resta",
          (403, True), (r.status_code, c.get(VIA, params={"pub": "7" * 64}).json()["viva"]))
    r = c.post(VIA + "/chiudi", json={"pub": "7" * 64, "biglietto": biglietto})
    prova("col biglietto giusto si chiude", (200, True), (r.status_code, r.json().get("chiusa")))
    prova("...e non c'e' piu'", False, c.get(VIA, params={"pub": "7" * 64}).json()["viva"])
    r = c.post(VIA + "/chiudi", json={"pub": "7" * 64, "biglietto": biglietto})
    prova("chiuderla due volte non e' un errore: «chiusa: false»", (200, False),
          (r.status_code, r.json().get("chiusa")))
    prova("...una chiave storta si', un 400", 400,
          c.post(VIA + "/chiudi", json={"pub": "x", "biglietto": "b"}).status_code)

    print("\n[il secondo postino: la cassetta spedisce]")
    # LA CASSETTA CHE SPEDISCE (20 ott 2026, cantiere nostr-da-telefono):
    # la pagina passa un 24133 gia' cifrato e firmato dalla sua chiave
    # effimera, e il server lo consegna ai relay della cassetta.
    sk = nuova_chiave()
    mia = pubblica_hex(sk)
    FIRMATARIO = "9" * 64
    SP = VIA + "/spedisci"
    r = c.post(VIA, json={"pub": mia, "relays": [RELAY_CASA, "wss://relay.example"]})
    big = r.json().get("biglietto")
    prova("la cassetta della chiave effimera si apre", 200, r.status_code)
    if S.ChiavePubblicaNostr is None:
        # il patto del server senza coincurve: non crede a nessuna firma,
        # nemmeno a una giusta — e solo dopo averlo visto si monta il calco
        n = len(WsPostino.spediti)
        r = c.post(SP, json={"pub": mia, "biglietto": big,
                             "evento": ventiquattro(sk, FIRMATARIO, "senza")})
        prova("senza coincurve il server non spedisce niente, nemmeno un "
              "24133 firmato giusto (400)", (400, n),
              (r.status_code, len(WsPostino.spediti)))
        S.ChiavePubblicaNostr = schnorr_puro.ChiaveXOnly
        print("   (coincurve assente: monto schnorr_puro.ChiaveXOnly, come in CI)")
    else:
        print("   (coincurve presente: il server verifica con libsecp256k1)")
    ev = ventiquattro(sk, FIRMATARIO)
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": ev})
    prova("un 24133 firmato dalla chiave della cassetta parte: lo prende il "
          "relay di casa, verso quello pubblico in collaudo non si esce",
          (200, 1, [RELAY_CASA]),
          (r.status_code, r.json().get("presi"), r.json().get("relays")))
    ultimo = WsPostino.spediti[-1] if WsPostino.spediti else (None, [None, {}])
    prova("...ed e' arrivato IDENTICO, col suo id e la sua firma: il server "
          "non firma e non cifra niente",
          (RELAY_CASA, "EVENT", ev["id"], ev["sig"], "cifrato"),
          (ultimo[0], ultimo[1][0], ultimo[1][1].get("id"),
           ultimo[1][1].get("sig"), ultimo[1][1].get("content")))
    prova("...e la presa si e' chiusa", True, WsPostino.chiuse >= 1)
    n = len(WsPostino.spediti)
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": ev})
    prova("lo stesso evento due volte non riparte (le copie le fa gia' la "
          "pagina)", (200, True, n),
          (r.status_code, r.json().get("gia"), len(WsPostino.spediti)))
    r = c.post(SP, json={"pub": mia, "biglietto": "sbagliato",
                         "evento": ventiquattro(sk, FIRMATARIO, "altro")})
    prova("senza il biglietto del deposito e' un 403", 403, r.status_code)
    altra = nuova_chiave()
    r = c.post(SP, json={"pub": mia, "biglietto": big,
                         "evento": ventiquattro(altra, FIRMATARIO)})
    prova("un evento di un'ALTRA chiave non si spedisce: 400", 400, r.status_code)
    falso = dict(ventiquattro(sk, FIRMATARIO, "terzo"), content="cambiato")
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": falso})
    prova("un evento toccato dopo la firma (id sbagliato) e' un 400", 400,
          r.status_code)
    sfirmato = dict(ventiquattro(sk, FIRMATARIO, "quarto"), sig="0" * 128)
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": sfirmato})
    prova("...e una firma che non torna pure", 400, r.status_code)
    doppio = ventiquattro(sk, FIRMATARIO, "quinto")
    doppio["tags"] = [["p", FIRMATARIO], ["p", "8" * 64]]
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": doppio})
    prova("un evento verso due destinatari (o con altri tag) non si spedisce",
          400, r.status_code)
    r = c.post(SP, json={"pub": mia, "biglietto": big,
                         "evento": dict(ventiquattro(sk, FIRMATARIO), kind=1)})
    prova("solo 24133: una nota (kind 1) e' un 400", 400, r.status_code)
    vecchio = ventiquattro(sk, FIRMATARIO, "sesto", ora=time.time() - 3600)
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": vecchio})
    prova("un evento di un'ora fa e' un 400", 400, r.status_code)
    lungo = ventiquattro(sk, FIRMATARIO, "x" * (S.CASSETTA_SPEDISCI_BYTE + 1))
    r = c.post(SP, json={"pub": mia, "biglietto": big, "evento": lungo})
    prova("un testo oltre il tetto e' un 400", 400, r.status_code)
    sk2 = nuova_chiave()
    r = c.post(SP, json={"pub": pubblica_hex(sk2),
                         "biglietto": big,
                         "evento": ventiquattro(sk2, FIRMATARIO)})
    prova("senza una cassetta aperta per quella chiave e' un 404", 404,
          r.status_code)
    WsPostino.risposta = False
    r = c.post(SP, json={"pub": mia, "biglietto": big,
                         "evento": ventiquattro(sk, FIRMATARIO, "settimo")})
    prova("un relay che dice OK:false non conta fra i presi", (200, 0),
          (r.status_code, r.json().get("presi")))
    WsPostino.risposta = True
    tetto = S.CASSETTA_SPEDITI_MAX
    with S._CASSETTE_LOCK:
        S.CASSETTA_SPEDITI_MAX = len(S._CASSETTE[mia]["spediti"])
    r = c.post(SP, json={"pub": mia, "biglietto": big,
                         "evento": ventiquattro(sk, FIRMATARIO, "ottavo")})
    prova("al tetto per cassetta (un tentativo di login) e' un 429 che lo dice",
          (429, True), (r.status_code, "login" in r.json().get("detail", "")))
    S.CASSETTA_SPEDITI_MAX = tetto
    S._SECCHI.clear()
    S.CASSETTA_SPEDITI_MAX = 1000       # qui si prova il freno per IP, non il tetto
    esiti = [c.post(SP, json={"pub": mia, "biglietto": big,
                              "evento": ventiquattro(sk, FIRMATARIO, f"giro {k}")},
                    headers={"x-forwarded-for": "8.8.4.4"}).status_code
             for k in range(61)]
    prova("il freno per IP: sessanta al minuto, il sessantunesimo e' un 429",
          (True, 429), (esiti[:60].count(429) == 0, esiti[-1]))
    S._SECCHI.clear()
    S.CASSETTA_SPEDITI_MAX = tetto
    with S._CASSETTE_LOCK:
        S._CASSETTE.pop(mia, None)

    print("\n[la scadenza: la cassetta muore, l'orecchio si chiude]")
    with S._CASSETTE_LOCK:
        for cass in S._CASSETTE.values():
            cass["scade"] = time.time() - 1
    g = c.get(VIA, params={"pub": PUB_A}).json()
    prova("scaduta: non viva", False, g.get("viva"))
    prova("...e l'orecchio senza cassette si chiude da solo", True,
          aspetta(lambda: RELAY_CASA not in S._ORECCHI))
    S._cassette_chiudi_tutto()

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
