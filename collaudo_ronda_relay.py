# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA RONDA DEI RELAY DI MOSTRO (12 ott 2026, cantiere
relay-per-mostro).

Richiesta di Andrea: i messaggi dei telefoni al coordinatore (presa,
rilascio, voto) devono passare da almeno due relay, di cui uno nostro;
il nostro accetta da chiunque SOLO quelli indirizzati al coordinatore; e
se smette di accettarli, o se relay.mostro.network non risponde, lo
devono sapere i moderatori nel gruppo, argomento Errori.

QUI GIRA IL SERVER VERO col banco di `collaudo_lnbits_muto` (config
finto, database usa-e-getta, MODALITA_COLLAUDO): il giro vero della
ronda, la lettura vera, il canarino vero firmato davvero — contro DUE
relay di CARTONE al posto di `websocket-client`.
IL RELAY NOSTRO DI CARTONE FA GIUDICARE OGNI EVENTO AL PLUGIN VERO
(`deploy/relay/policy/chi-scrive.py`, caricato dal file) dopo averne
verificato la firma come fa strfry: le due meta' del cantiere stanno su
due macchine, e si incontrano qui.

TUTTO QUEL CHE IL SERVER STAMPA SI TIENE, e alla fine ci si cercano i
canarini: non devono esserci, in nessuna forma.

NESSUNA RETE: i relay sono liste in memoria. Verso un relay pubblico
vero, in collaudo, non parte ne' la lettura ne' il canarino
(`lettura_simulata`).

USO:  python collaudo_ronda_relay.py
"""

import asyncio
import hashlib
import importlib.util
import io
import json
import os
import sys
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova
QUI = os.path.dirname(os.path.abspath(__file__))
NOSTRO = "ws://127.0.0.1:7821"           # di casa: il relay di Barattolo
LORO = "ws://127.0.0.1:7822"             # di casa: fa relay.mostro.network
VERO = "wss://relay.vero.example"        # non di casa: non lo tocca nessuno
IP_VPS = "203.0.113.7"


class Tutto(io.TextIOBase):
    """Lo stdout del collaudo, che in piu' si ricorda ogni riga."""

    def __init__(self, vero):
        self.vero, self.detto = vero, []

    def write(self, s):
        self.detto.append(s)
        return self.vero.write(s)

    def flush(self):
        self.vero.flush()


def plugin_vero():
    """Il plugin del relay, dal FILE: lo stesso che gira sulla macchina."""
    spec = importlib.util.spec_from_file_location(
        "chi_scrive_collaudo",
        os.path.join(QUI, "deploy", "relay", "policy", "chi-scrive.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.CHIAVI = os.path.join(QUI, "non-esiste", "chiavi.txt")
    return m


def firma_buona(ev):
    """Quel che strfry controlla prima di chiedere al plugin: l'id e'
    quello del NIP-01 e la firma Schnorr regge."""
    seriale = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"],
                          ev["tags"], ev["content"]],
                         separators=(",", ":"), ensure_ascii=False)
    return (ev["id"] == hashlib.sha256(seriale.encode("utf-8")).hexdigest()
            and schnorr_puro.verifica(bytes.fromhex(ev["pubkey"]),
                                      bytes.fromhex(ev["id"]),
                                      bytes.fromhex(ev["sig"])))


class WsCartone:
    """La websocket di cartone. Ogni relay ha un MAGAZZINO (gli eventi
    che serve) e un GIUDICE delle scritture; un relay fra gli `spenti`
    rifiuta la connessione, uno fra i `sordi` apre e non risponde.
    A una REQ risponde come un relay vero: gli eventi che combaciano
    col filtro, dal piu' fresco, entro il `limit`, e poi EOSE. A un
    EVENT verifica la firma, chiede al giudice e risponde OK."""
    aperte = []
    magazzino = {}
    giudici = {}
    spenti = set()
    sordi = set()
    arrivati = {}          # relay -> gli EVENT mandati dal server
    accettati = {}         # relay -> quelli entrati

    def __init__(self, relay, timeout=10, sslopt=None):
        WsCartone.aperte.append(relay)
        if relay in WsCartone.spenti:
            raise ConnectionRefusedError("relay di cartone spento")
        self.relay, self.coda = relay, []

    def send(self, s):
        msg = json.loads(s)
        if self.relay in WsCartone.sordi:
            return
        if msg[0] == "REQ":
            f = msg[2]
            trovati = sorted(
                (e for e in WsCartone.magazzino.get(self.relay, [])
                 if e["kind"] in f.get("kinds", [e["kind"]])
                 and e["pubkey"] in f.get("authors", [e["pubkey"]])),
                key=lambda e: -e["created_at"])[:f.get("limit", 500)]
            self.coda += [json.dumps(["EVENT", msg[1], e]) for e in trovati]
            self.coda.append(json.dumps(["EOSE", msg[1]]))
        elif msg[0] == "EVENT":
            ev = msg[1]
            WsCartone.arrivati.setdefault(self.relay, []).append(ev)
            if not firma_buona(ev):
                ok, perche = False, "invalid: bad signature"
            else:
                ok, perche = WsCartone.giudici[self.relay](ev)
            if ok:
                WsCartone.accettati.setdefault(self.relay, []).append(ev)
            self.coda.append(json.dumps(["OK", ev["id"], ok, perche]))

    def recv(self):
        if not self.coda:
            raise TimeoutError("timed out")
        return self.coda.pop(0)

    def close(self):
        pass


def main():
    tutto = Tutto(sys.stdout)
    sys.stdout = tutto
    print("=" * 58)
    print("  LA RONDA DEI RELAY DI MOSTRO — il giro vero")
    print("=" * 58)
    banco.avvio()
    S = banco.SRV
    sk_mostro = bytes([21]) * 31 + bytes([53])
    MOSTRO = schnorr_puro.pubblica(sk_mostro).hex()

    def del_coordinatore(quando, kind=38385):
        ev = S.evento_non_firmato(MOSTRO, kind, [["d", "info"]], "", quando)
        ev["sig"] = schnorr_puro.firma(sk_mostro, bytes.fromhex(ev["id"])).hex()
        return ev

    def ripubblica(*relay, fa=30):
        """mostrod che scrive le sue impostazioni: su quei relay, adesso."""
        for r in relay:
            WsCartone.magazzino[r] = [del_coordinatore(int(time.time()) - fa)]

    # --- il cartone: il plugin VERO sul relay nostro ---
    P = plugin_vero()
    P.MOSTRO = MOSTRO                  # il coordinatore di questo collaudo
    WsCartone.giudici[NOSTRO] = lambda ev: P.giudica(
        {"type": "new", "event": ev, "sourceType": "IP4",
         "sourceInfo": IP_VPS}, time.time())
    WsCartone.giudici[LORO] = lambda ev: (True, "")
    WsCartone.giudici[VERO] = lambda ev: (True, "")
    S._ronda_relay_connetti = WsCartone
    S.MOSTRO_HEX = MOSTRO
    S.MOSTRO_RELAY = [NOSTRO, LORO, VERO]
    S.MOSTRO_RELAY_CONFERMA = [NOSTRO, LORO, VERO]
    S.RONDA_RELAY_CANARINO = [NOSTRO, VERO]
    S.RONDA_RELAY_TETTO_S = 0.5
    S.RONDA_RELAY_CANARINO_S = 0       # il canarino a ogni giro, qui
    AVVISI = []

    async def avvisa(testo, bottone=None, argomento=""):
        AVVISI.append((testo, argomento))
    S.notifica_admin = avvisa

    if S.ChiavePrivataNostr is None:
        class _Priv:
            def __init__(self, sk):
                self.sk, self.public_key = sk, self

            def format(self):
                return b"\x02" + schnorr_puro.pubblica(self.sk)

            def sign_schnorr(self, msg):
                return schnorr_puro.firma(self.sk, msg)
        S.ChiavePrivataNostr = _Priv
        print("  · coincurve non c'e': il canarino lo firma il calco di "
              "schnorr_puro")
    else:
        print("  · [coincurve] il canarino lo firma la libreria vera, e "
              "il relay di cartone lo verifica con schnorr_puro")

    class Avvisi(list):
        """Gli avvisi di UN giro. `testo` e `stanza` sono quelli del
        primo, o vuoti: a codice mutato il collaudo dev'essere ROSSO,
        non esplodere a meta' portandosi via i passi dopo."""
        testo = property(lambda self: self[0][0] if self else "")
        stanza = property(lambda self: self[0][1] if self else "")

    def giro():
        prima = (len(WsCartone.aperte), len(AVVISI))
        asyncio.run(S._ronda_relay_giro())
        return ([r for r in WsCartone.aperte[prima[0]:]],
                Avvisi(AVVISI[prima[1]:]))

    print("\n[la leva: spenta non nasce niente]")
    S.RONDA_RELAY_MOSTRO = False
    asyncio.run(S.avvia_ronda_relay())
    prova("a leva spenta: nessun orologio, nessuna connessione, e la "
          "ronda non e' viva", (None, [], False),
          (S._TASK_RONDA_RELAY, WsCartone.aperte, S.ronda_relay_viva()))
    S.RONDA_RELAY_MOSTRO = True
    S.MOSTRO_HEX = ""
    asyncio.run(S.avvia_ronda_relay())
    prova("leva accesa SENZA la chiave del coordinatore: vale spenta",
          (None, [], False),
          (S._TASK_RONDA_RELAY, WsCartone.aperte, S.ronda_relay_viva()))
    S.MOSTRO_HEX = MOSTRO
    prova("leva accesa e coordinatore: viva; si guardano i tre relay "
          "che confermano, il canarino ha i suoi due",
          (True, [NOSTRO, LORO, VERO], [NOSTRO, VERO]),
          (S.ronda_relay_viva(), S._ronda_relay_guardati(),
           S._ronda_relay_canarini()))

    print("\n[tutto a posto: il canarino entra dalla buca, nessuno parla]")
    ripubblica(NOSTRO, LORO)
    bussati, avvisi = giro()
    prova("il giro bussa ai due relay di casa — lettura a tutti e due, "
          "canarino al nostro — e MAI al relay pubblico vero",
          ([NOSTRO, NOSTRO, LORO], False),
          (sorted(bussati), VERO in WsCartone.aperte))
    can = WsCartone.arrivati[NOSTRO][0]
    prova("il canarino arrivato al relay nostro: firma buona, kind 14, "
          "UN tag `p` col coordinatore, la scadenza a dieci minuti",
          (True, 14, [["p", MOSTRO]], True),
          (firma_buona(can), can["kind"],
           [t for t in can["tags"] if t[0] == "p"],
           [t[1] for t in can["tags"] if t[0] == "expiration"]
           == [str(can["created_at"] + 600)]))
    prova("IL PLUGIN VERO LO HA FATTO ENTRARE, da una chiave che non sta "
          "in nessuna lista", (1, False),
          (len(WsCartone.accettati.get(NOSTRO, [])),
           can["pubkey"] in P._ammesse))
    prova("...al relay d'altri (relay.mostro.network) e a quello vero "
          "nessun canarino: sarebbe spam", ([], []),
          (WsCartone.arrivati.get(LORO, []), WsCartone.arrivati.get(VERO, [])))
    prova("nessun avviso, e lo stato dice «a posto» per i due di casa e "
          "«in collaudo non si chiede» per quello vero",
          ([], {NOSTRO: "a posto", LORO: "a posto",
                VERO: "in collaudo non si chiede"}),
          (avvisi, S._RONDA_RELAY["stati"]))
    for _ in range(3):
        ripubblica(NOSTRO, LORO)
        giro()
    prova("altri tre giri sani: quattro canarini entrati, quattro "
          "chiavi diverse, e ancora nessun avviso", (4, 4, []),
          (len(WsCartone.accettati[NOSTRO]),
           len({e["pubkey"] for e in WsCartone.accettati[NOSTRO]}), AVVISI))

    print("\n[il relay nostro torna quello di ieri: rifiuta i telefoni]")
    WsCartone.giudici[NOSTRO] = lambda ev: (
        False, "restricted: solo <Barattolo> e i suoi venditori")
    _, avvisi = giro()
    prova("al primo no ancora niente ai moderatori (un giro storto non "
          "e' una notizia)", [], avvisi)
    _, avvisi = giro()
    prova("al secondo no di fila parte UN avviso, nell'argomento Errori",
          (1, "errori"), (len(avvisi), avvisi.stanza))
    prova("...dice quale relay, che NON ACCETTA i messaggi per il "
          "coordinatore, con le parole del relay rese innocue",
          (True, True, False),
          ("<code>127.0.0.1:7821</code> NON ACCETTA i messaggi per il "
           "coordinatore («restricted: solo &lt;Barattolo&gt; e i suoi "
           "venditori»)" in avvisi.testo,
           "⚠️ <b>Relay di Mostro</b>" in avvisi.testo,
           "<Barattolo>" in avvisi.testo))
    _, a3 = giro()
    _, a4 = giro()
    prova("...e finche' dura non lo ripete", ([], []), (a3, a4))
    no_di_ieri = (len(WsCartone.arrivati[NOSTRO])
                  - len(WsCartone.accettati[NOSTRO]))
    prova("...mentre il canarino ha continuato a provare a ogni giro: "
          "quattro giri, quattro no", 4, no_di_ieri)
    WsCartone.giudici[NOSTRO] = lambda ev: P.giudica(
        {"type": "new", "event": ev, "sourceType": "IP4",
         "sourceInfo": IP_VPS}, time.time())
    ripubblica(NOSTRO, LORO)
    _, avvisi = giro()
    prova("rimesso il plugin nuovo arriva il ritorno, uno",
          (1, True, "errori"),
          (len(avvisi),
           "✅ <code>127.0.0.1:7821</code> accetta di nuovo i messaggi per "
           "il coordinatore" in avvisi.testo, avvisi.stanza))

    print("\n[relay.mostro.network non risponde]")
    WsCartone.spenti.add(LORO)
    _, a1 = giro()
    WsCartone.spenti.discard(LORO)
    ripubblica(NOSTRO, LORO)
    _, a2 = giro()
    prova("cade per UN giro e torna: nessuno ne sa niente", ([], []),
          (a1, a2))
    WsCartone.spenti.add(LORO)
    giro()
    _, avvisi = giro()
    prova("cade per due giri di fila: «non risponde», in Errori",
          (1, True, "errori"),
          (len(avvisi), "<code>127.0.0.1:7822</code> non risponde"
           in avvisi.testo, avvisi.stanza))
    prova("...e intanto il canarino al relay nostro ha continuato a "
          "entrare: i due guasti non si confondono", True,
          WsCartone.accettati[NOSTRO][-1]["created_at"] >= int(time.time()) - 5)
    WsCartone.spenti.discard(LORO)
    WsCartone.sordi.add(LORO)
    _, avvisi = giro()
    prova("un relay che apre e poi tace e' lo stesso guasto: nessun "
          "avviso nuovo, nessun ritorno falso", [], avvisi)
    WsCartone.sordi.discard(LORO)
    ripubblica(NOSTRO, LORO)
    _, avvisi = giro()
    prova("quando torna, lo dice", (1, True),
          (len(avvisi), "✅ <code>127.0.0.1:7822</code> è tornato a posto"
           in avvisi.testo))

    print("\n[il relay risponde, ma il coordinatore non ci scrive piu']")
    ripubblica(NOSTRO)
    ripubblica(LORO, fa=6 * 86400)        # nos.lol a ottobre: sei giorni
    giro()
    ripubblica(NOSTRO)
    _, avvisi = giro()
    prova("fermo da sei giorni: «risponde, ma il coordinatore non ci "
          "scrive da 6 giorni»", (1, True),
          (len(avvisi), "<code>127.0.0.1:7822</code> risponde, ma il "
           "coordinatore non ci scrive da 6 giorni" in avvisi.testo))
    WsCartone.magazzino[LORO] = []
    _, avvisi = giro()
    prova("...e se si svuota del tutto resta lo STESSO guasto: non si "
          "ridice", [], avvisi)
    ripubblica(NOSTRO, LORO)
    _, avvisi = giro()
    prova("mostrod ci riscrive: torna a posto", (1, True),
          (len(avvisi), "è tornato a posto" in avvisi.testo))

    print("\n[il relay nostro giu' del tutto]")
    WsCartone.spenti.add(NOSTRO)
    prima = len(WsCartone.arrivati[NOSTRO])
    giro()
    _, avvisi = giro()
    prova("non risponde alla lettura: UNA riga per quel relay (il "
          "canarino non si manda a chi non risponde)",
          (1, 1, True, prima),
          (len(avvisi), avvisi.testo.count("\n• "),
           "<code>127.0.0.1:7821</code> non risponde" in avvisi.testo,
           len(WsCartone.arrivati[NOSTRO])))
    WsCartone.spenti.discard(NOSTRO)
    ripubblica(NOSTRO, LORO)
    _, avvisi = giro()
    prova("torna su: il ritorno, e il canarino riparte subito",
          (1, prima + 1),
          (len(avvisi), len(WsCartone.arrivati[NOSTRO])))

    print("\n[i freni del plugin e il canarino]")
    S.RONDA_RELAY_CANARINO_S = 1800
    entrati = len(WsCartone.accettati[NOSTRO])
    for _ in range(4):
        ripubblica(NOSTRO, LORO)
        giro()
    prova("col ritmo vero (uno ogni mezz'ora) quattro giri di fila non "
          "mandano altri canarini", entrati,
          len(WsCartone.accettati[NOSTRO]))
    prova("...e in tutto il collaudo il plugin non ha mai frenato il "
          "canarino: quelli arrivati col plugin nuovo sono tutti entrati",
          True, len(WsCartone.accettati[NOSTRO])
          == len(WsCartone.arrivati[NOSTRO]) - no_di_ieri)

    print("\n[il pannello delle leve]")
    leve = {v["chiave"]: v for v in S._ronda_relay_leve()}
    prova("la leva e' viva, dice lo stato dell'ultimo giro e dove va il "
          "canarino", (True, True, True),
          (leve["RONDA_RELAY_MOSTRO"]["valore"],
           "127.0.0.1:7821: a posto" in leve["RONDA_RELAY_MOSTRO"]["nota"],
           "127.0.0.1:7821" in leve["RONDA_RELAY_CANARINO"]["valore"]))

    print("\n[il journal: mai il canarino]")
    sys.stdout = tutto.vero
    detto = "".join(tutto.detto)
    canarini = WsCartone.arrivati[NOSTRO]
    prova("il server ha stampato le sue righe (lo stato che cambia)",
          True, "🛰️ Ronda dei relay di Mostro: " in detto)
    prova("...e in tutto quel che ha stampato non c'e' nessun canarino: "
          "ne' la chiave, ne' l'id, ne' la firma, ne' il contenuto",
          (True, []),
          (len(canarini) >= 10,
           [c["id"][:8] for c in canarini
            if any(c[k] in detto for k in ("pubkey", "id", "sig", "content"))]))
    prova("...ne' negli avvisi ai moderatori", [],
          [c["id"][:8] for c in canarini
           if any(c[k] in t for t, _ in AVVISI
                  for k in ("pubkey", "id", "sig", "content"))])
    prova("al relay pubblico vero, in tutto il collaudo, non ha bussato "
          "nessuno", 0, WsCartone.aperte.count(VERO))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
