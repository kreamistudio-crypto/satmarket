# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'AVVISO DEI DM A BARATTOLO (11 ott 2026).

Richiesta di Andrea: quando qualcuno scrive un DM al profilo Nostr di
Barattolo, ai moderatori arriva «📩 Nuovo DM su Nostr da <chi>» — mai il
testo, niente doppioni, un tetto contro lo spam, niente avvisi per la
posta vecchia, e un relay che cade non porta giu' il server.

QUI GIRA IL SERVER VERO col banco di `collaudo_lnbits_muto` (config
finto, database usa-e-getta, MODALITA_COLLAUDO): l'orologio dell'avviso
in un loop suo, i fili veri, il setaccio vero, la busta NIP-17 aperta
davvero — con DUE relay di CARTONE al posto di `websocket-client`, e DM
firmati da chiavi usa-e-getta (`schnorr_puro`) e cifrati col NIP-44 del
server. Dove coincurve non c'e' (la CI) la matematica delle chiavi la
fa il calco `schnorr_puro.PuntoCompleto`; dove c'e', la libreria vera.

TUTTO QUEL CHE IL SERVER STAMPA SI TIENE, e alla fine ci si cerca il
testo dei messaggi e le chiavi di chi ha scritto: non devono esserci.

NESSUNA RETE: i relay sono code in memoria. Verso un relay pubblico
vero, in collaudo, il filo NON nasce (`lettura_simulata`).

USO:  python collaudo_avviso_dm_nostr.py
"""

import asyncio
import io
import json
import os
import queue
import sys
import threading
import time

import collaudo_lnbits_muto as banco
import schnorr_puro

prova = banco.prova
RELAY_A = "ws://127.0.0.1:7801"          # di casa: in collaudo il filo esce
RELAY_B = "ws://127.0.0.1:7802"
RELAY_VERO = "wss://relay.vero.example"  # non di casa: non si ascolta
SEGRETO = "TESTO-SEGRETO-del-messaggio"


class Tutto(io.TextIOBase):
    """Lo stdout del collaudo, che in piu' si ricorda ogni riga."""

    def __init__(self, vero):
        self.vero, self.detto = vero, []

    def write(self, s):
        self.detto.append(s)
        return self.vero.write(s)

    def flush(self):
        self.vero.flush()


class WsCartone:
    """La websocket di cartone, una coda PER RELAY: tiene le REQ
    mandate e serve quel che il banco ci mette. `recv` aspetta il
    timeout e poi alza come fa websocket-client; un'eccezione messa in
    coda cade dalla `recv` (e' il relay che butta giu' la linea); un
    relay fra i `rotti` rifiuta la connessione."""
    mandate = []
    code = {}
    aperte = {}
    rotti = set()

    def __init__(self, relay, timeout=10, sslopt=None):
        if relay in WsCartone.rotti:
            raise ConnectionRefusedError("relay di cartone spento")
        WsCartone.aperte[relay] = WsCartone.aperte.get(relay, 0) + 1
        self.relay, self.t = relay, timeout

    def settimeout(self, t):
        self.t = min(t, 0.05)            # il battito, ma svelto

    def send(self, s):
        msg = json.loads(s)
        WsCartone.mandate.append((self.relay, msg))
        if msg[0] == "REQ" and msg[1] == "polso":
            metti(self.relay, ["EOSE", "polso"])

    def recv(self):
        try:
            cosa = WsCartone.code[self.relay].get(timeout=self.t)
        except queue.Empty:
            raise TimeoutError("timed out")
        if isinstance(cosa, Exception):
            raise cosa
        return cosa

    def close(self):
        pass


def metti(relay, msg):
    WsCartone.code.setdefault(relay, queue.Queue()).put(
        msg if isinstance(msg, Exception) else json.dumps(msg))


def aspetta(cond, ms=4000):
    fine = time.time() + ms / 1000
    while time.time() < fine:
        if cond():
            return True
        time.sleep(0.02)
    return cond()


def chiave(n):
    """Una chiave usa-e-getta, costruita e mai scritta per esteso."""
    sk = bytes([n]) * 31 + bytes([n + 32])
    return sk, schnorr_puro.pubblica(sk).hex()


def main():
    tutto = Tutto(sys.stdout)
    sys.stdout = tutto
    print("=" * 58)
    print("  L'AVVISO DEI DM A BARATTOLO — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient
    S = banco.SRV
    adesso = int(time.time())
    sk_noi, NOI = chiave(3)
    sk_mario, MARIO = chiave(5)
    sk_lucia, LUCIA = chiave(7)
    sk_gino, GINO = chiave(9)
    sk_altro, ALTRO = chiave(11)

    # --- il cartone: i relay, la chiave di casa, chi riceve gli avvisi
    S._dm_connetti = WsCartone
    S.AVVISO_DM_NOSTR_RELAY = [RELAY_A, RELAY_B, RELAY_VERO]
    S.AVVISO_DM_PASSO_S = 0.05
    S.AVVISO_DM_ATTESA_S = 0.05
    S.AVVISO_DM_RITORNO_S = 1
    S._DM_AVVIO = adesso - 30
    AVVISI = []

    async def avvisa(testo, bottone=None):
        AVVISI.append((testo, bottone))
    S.notifica_admin = avvisa

    async def profilo(npub):
        if npub == S.hex_to_npub(MARIO):
            return {"display_name": "Mario  <b>Rossi</b>\n&co"}
        return {}
    profilo_vero = S._profilo_nostr
    S._profilo_nostr = profilo

    class _Noi:
        secret = sk_noi
    if S.ChiavePrivataNostr is not None:
        noi_chiave = S.ChiavePrivataNostr(sk_noi)
        prova("[coincurve] la chiave di casa del collaudo e' quella vera "
              "di coincurve", NOI, noi_chiave.public_key.format()[1:].hex())
    else:
        noi_chiave = _Noi()
        S.ChiavePubblicaCompleta = schnorr_puro.PuntoCompleto
        print("  · coincurve non c'e': la matematica delle chiavi la fa "
              "il calco di schnorr_puro")

    def firmato(sk, kind, tags, content, creato=None):
        ev = S.evento_non_firmato(schnorr_puro.pubblica(sk).hex(), kind, tags,
                                  content, creato or int(time.time()))
        ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"])).hex()
        return ev

    def busta(sk_mitt, n="", dest=None, dentro=None, creato=None):
        """Un DM NIP-17 intero: rumor (col SEGRETO) → sigillo → pacco,
        con la data del pacco arretrata come fa un client vero."""
        dest = dest or NOI
        pub = schnorr_puro.pubblica(sk_mitt).hex()
        rumor = S.evento_non_firmato(pub, 14, [["p", dest]], SEGRETO + n,
                                     int(time.time()))
        if dentro is None:
            dentro = S.nip44_cifra(sk_mitt, dest, json.dumps(rumor))
        sigillo = firmato(sk_mitt, 13, [], dentro, int(time.time()) - 7000)
        eff = os.urandom(32)
        return firmato(eff, 1059, [["p", NOI]],
                       S.nip44_cifra(eff, dest, json.dumps(sigillo)),
                       creato or int(time.time()) - 100000)

    def ai_due(ev):
        for r in (RELAY_A, RELAY_B):
            metti(r, ["EVENT", "dm", ev])

    print("\n[la leva: spenta non nasce niente]")
    S._NOSTR = (noi_chiave, NOI)
    S.AVVISO_DM_NOSTR = False
    asyncio.run(S.avvia_avviso_dm())
    prova("a leva spenta: nessun orologio, nessuna connessione",
          (None, {}), (S._TASK_AVVISO_DM, WsCartone.aperte))
    S.AVVISO_DM_NOSTR = True
    S._NOSTR = None
    asyncio.run(S.avvia_avviso_dm())
    prova("leva accesa SENZA la chiave della piattaforma: vale spenta",
          (None, {}, False),
          (S._TASK_AVVISO_DM, WsCartone.aperte, S.avviso_dm_vivo()))
    S._NOSTR = (noi_chiave, NOI)
    prova("leva accesa e chiave: viva", True, S.avviso_dm_vivo())

    print("\n[l'avvio: la posta che c'era gia' non parla]")
    vecchia = busta(sk_gino, "vecchia")
    for r in (RELAY_A, RELAY_B):
        metti(r, ["EVENT", "dm", vecchia])
        metti(r, ["EOSE", "dm"])
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    orologio = asyncio.run_coroutine_threadsafe(S.orologio_avviso_dm(), loop)
    prova("i due relay di casa sono in ascolto, quello pubblico vero e' "
          "«simulato»: nessuno gli ha bussato, e il suo filo non e' "
          "nemmeno nato",
          (True, "simulato", None, None),
          (aspetta(lambda: all(S._DM_ASCOLTO.get(r, {}).get("stato")
                               == "connesso" for r in (RELAY_A, RELAY_B))),
           S._DM_ASCOLTO.get(RELAY_VERO, {}).get("stato"),
           WsCartone.aperte.get(RELAY_VERO),
           S._DM_ASCOLTO.get(RELAY_VERO, {}).get("filo")))
    req = [m for r, m in WsCartone.mandate if r == RELAY_A and m[0] == "REQ"][0]
    prova("la REQ: le buste (1059) per noi degli ultimi tre giorni, i "
          "NIP-04 (4) per noi dall'avvio",
          ("dm", [1059], [NOI], True, [4], [NOI], adesso - 30),
          (req[1], req[2]["kinds"], req[2]["#p"],
           abs(req[2]["since"] - (time.time() - 3 * 86400)) < 60,
           req[3]["kinds"], req[3]["#p"], req[3]["since"]))
    time.sleep(0.4)
    prova("la busta che stava gia' sui relay all'avvio: nessun avviso",
          [], AVVISI)
    ai_due(vecchia)
    time.sleep(0.4)
    prova("...nemmeno se un relay la rimanda dopo", [], AVVISI)

    print("\n[un DM nuovo: un avviso solo, da due relay]")
    ai_due(busta(sk_mario, "uno"))
    prova("arriva UN avviso", True, aspetta(lambda: len(AVVISI) == 1))
    time.sleep(0.4)
    npub_m = S.hex_to_npub(MARIO)
    corta_m = f"{npub_m[:10]}…{npub_m[-6:]}"
    prova("...uno e non due (lo stesso DM dai due relay), col nome del "
          "profilo accorciato e scappato, e la npub abbreviata",
          [(f"📩 Nuovo DM su Nostr da Mario &lt;b&gt;Rossi&lt;/b&gt; &amp;co "
            f"({corta_m})", ("🟣 Apri in un client",
                             f"https://njump.me/{npub_m}"))], AVVISI)

    print("\n[il tetto per mittente]")
    metti(RELAY_A, ["EVENT", "dm", busta(sk_mario, "due")])
    metti(RELAY_B, ["EVENT", "dm", busta(sk_mario, "tre")])
    prova("altri due DM di Mario subito dopo: in coda, nessun avviso",
          (True, 1),
          (aspetta(lambda: S._DM_AVVISI["mittenti"].get(MARIO, {})
                   .get("attesa") == 2), len(AVVISI)))
    S._DM_AVVISI["mittenti"][MARIO]["ultimo"] -= S.AVVISO_DM_PAUSA_MITTENTE_S
    prova("...a pausa finita escono in una riga sola, col conto",
          (True, f"📩 2 nuovi DM su Nostr da Mario &lt;b&gt;Rossi&lt;/b&gt; "
                 f"&amp;co ({corta_m})"),
          (aspetta(lambda: len(AVVISI) == 2), AVVISI[-1][0]))

    print("\n[il vecchio NIP-04]")
    npub_l = S.hex_to_npub(LUCIA)
    corta_l = f"{npub_l[:10]}…{npub_l[-6:]}"
    metti(RELAY_B, ["EVENT", "dm", firmato(
        sk_lucia, 4, [["p", NOI]], SEGRETO + "-nip04?iv=abc")])
    prova("un kind 4 nuovo: l'avviso con la npub abbreviata (non ha un "
          "nome) e il bottone",
          (True, (f"📩 Nuovo DM su Nostr da {corta_l}",
                  ("🟣 Apri in un client", f"https://njump.me/{npub_l}"))),
          (aspetta(lambda: len(AVVISI) == 3), AVVISI[-1]))
    metti(RELAY_A, ["EVENT", "dm", firmato(
        sk_gino, 4, [["p", NOI]], "x?iv=y", adesso - 5000)])
    falso = firmato(sk_gino, 4, [["p", NOI]], "x?iv=z")
    falso["sig"] = falso["sig"][:-2] + ("00" if falso["sig"][-2:] != "00"
                                        else "11")
    metti(RELAY_A, ["EVENT", "dm", falso])
    metti(RELAY_A, ["EVENT", "dm", firmato(sk_gino, 4, [["p", ALTRO]], "x")])
    metti(RELAY_A, ["EVENT", "dm", firmato(sk_gino, 1, [["p", NOI]], "nota")])

    print("\n[quel che NON e' un DM per noi]")
    metti(RELAY_A, ["EVENT", "dm", busta(sk_noi, "nostra")])
    metti(RELAY_A, ["EVENT", "dm", busta(sk_gino, "per-altri", dest=ALTRO)])
    metti(RELAY_B, ["EVENT", "dm", {"kind": 1059, "id": "storto"}])
    metti(RELAY_B, ["NOTICE", "una riga del relay che non c'entra"])
    time.sleep(0.6)
    prova("un NIP-04 di prima dell'avvio, uno con la firma ritoccata, uno "
          "per un altro, una nota; la copia che ci siamo mandati da soli, "
          "una busta chiusa per un altro, un evento storto: nessun avviso",
          3, len(AVVISI))

    print("\n[il messaggio non si apre]")
    npub_g = S.hex_to_npub(GINO)
    metti(RELAY_A, ["EVENT", "dm", busta(
        sk_gino, dentro="questo non si puo' decifrare, e nessuno ci prova")])
    prova("una busta col sigillo firmato e DENTRO un contenuto che non si "
          "puo' aprire: l'avviso arriva lo stesso, col mittente — il "
          "server la seconda busta non la tocca",
          (True, f"📩 Nuovo DM su Nostr da {npub_g[:10]}…{npub_g[-6:]}"),
          (aspetta(lambda: len(AVVISI) == 4), AVVISI[-1][0]))

    print("\n[la raffica: il tetto e il riassunto]")
    prova("fin qui quattro avvisi nella finestra", 4,
          len(S._DM_AVVISI["mandati"]))
    for n in range(20, 26):
        metti(RELAY_A, ["EVENT", "dm", firmato(
            chiave(n)[0], 4, [["p", NOI]], f"raffica?iv={n}")])
    prova("sei mittenti nuovi insieme: ne passano due (il tetto e' sei in "
          "mezz'ora), gli altri quattro aspettano nel riassunto",
          (True, 6, 4),
          (aspetta(lambda: S._DM_AVVISI["folla"]["n"] == 4),
           len(AVVISI), len(S._DM_AVVISI["folla"]["chi"])))
    time.sleep(0.3)
    prova("...e finche' la finestra e' piena non esce altro", 6, len(AVVISI))
    S._DM_AVVISI["mandati"] = [t - S.AVVISO_DM_FINESTRA_S
                               for t in S._DM_AVVISI["mandati"]]
    prova("al primo posto libero: UN riassunto, senza nomi e senza bottone",
          (True, ("📩 4 nuovi DM su Nostr da 4 mittenti", None)),
          (aspetta(lambda: len(AVVISI) == 7), AVVISI[-1]))

    print("\n[il relay cade: si riconnette da solo, e il server risponde]")
    WsCartone.rotti.add(RELAY_A)
    metti(RELAY_A, ConnectionResetError("linea caduta"))
    prova("la linea cade e il relay non risponde: lo stato dice «giu'» e "
          "conta i tentativi", True,
          aspetta(lambda: S._DM_ASCOLTO[RELAY_A]["stato"] == "giu"
                  and S._DM_ASCOLTO[RELAY_A]["cadute"] >= 3))
    c = TestClient(S.app)
    prova("...e intanto il server risponde come sempre", 200,
          c.get("/api/salute").status_code)
    S._DM_AVVISI["mittenti"].pop(LUCIA, None)
    metti(RELAY_B, ["EVENT", "dm", busta(sk_lucia, "da-b")])
    prova("...e l'altro relay continua a portare la posta", True,
          aspetta(lambda: len(AVVISI) == 8))
    prima = WsCartone.aperte[RELAY_A]
    persa = busta(sk_gino, "arrivata-mentre-era-giu")
    S._DM_AVVISI["mittenti"].pop(GINO, None)
    metti(RELAY_A, ["EVENT", "dm", vecchia])
    metti(RELAY_A, ["EVENT", "dm", persa])
    metti(RELAY_A, ["EOSE", "dm"])
    WsCartone.rotti.discard(RELAY_A)
    prova("il relay torna: il filo si riconnette DA SOLO e rimanda la REQ",
          (True, True),
          (aspetta(lambda: S._DM_ASCOLTO[RELAY_A]["stato"] == "connesso"),
           WsCartone.aperte[RELAY_A] > prima))
    prova("...il DM arrivato mentre era giu' parla (uno), la posta gia' "
          "vista no", (True, 9),
          (aspetta(lambda: len(AVVISI) == 9),
           [time.sleep(0.4), len(AVVISI)][1]))
    req2 = [m for r, m in WsCartone.mandate if r == RELAY_A and m[0] == "REQ"
            and m[1] == "dm"][-1]
    prova("...e alla riconnessione i NIP-04 si richiedono da poco prima "
          "della caduta, non dall'avvio", True, req2[3]["since"] > adesso - 30)

    print("\n[la guardia: un filo morto si rifa']")
    vecchio_filo = S._DM_ASCOLTO[RELAY_B]["filo"]
    S._DM_ASCOLTO[RELAY_B]["ferma"].set()
    prova("un filo uscito viene rimpiazzato al giro dopo", True,
          aspetta(lambda: S._DM_ASCOLTO[RELAY_B]["filo"] is not vecchio_filo
                  and S._DM_ASCOLTO[RELAY_B]["filo"].is_alive()))
    metti(RELAY_B, ["EOSE", "dm"])
    polsi = S.AVVISO_DM_POLSO_S
    S.AVVISO_DM_POLSO_S = 0
    prova("il polso parte e torna: il filo resta su", (True, "connesso"),
          (aspetta(lambda: any(m[0] == "CLOSE" and m[1] == "polso"
                               for r, m in WsCartone.mandate)),
           S._DM_ASCOLTO[RELAY_A]["stato"]))
    S.AVVISO_DM_POLSO_S = polsi

    print("\n[il nome dal profilo vero: in collaudo non si esce]")
    S._profilo_nostr = profilo_vero
    S._DM_AVVISI["mandati"] = []
    S._DM_AVVISI["mittenti"].pop(MARIO, None)
    metti(RELAY_A, ["EVENT", "dm", busta(sk_mario, "senza-nome")])
    prova("col lettore vero del kind 0 (relay pubblici: in collaudo non "
          "risponde nessuno) l'avviso parte lo stesso, con la sola npub",
          (True, f"📩 Nuovo DM su Nostr da {corta_m}"),
          (aspetta(lambda: len(AVVISI) == 10, 15000), AVVISI[-1][0]))

    print("\n[il pannello delle leve]")
    voci = {v["chiave"]: v for v in S._dm_leve()}
    prova("la leva e' accesa e ogni relay dice il suo stato",
          (True, True, True),
          (voci["AVVISO_DM_NOSTR"]["valore"],
           "127.0.0.1:7801: connesso" in voci["AVVISO_DM_NOSTR_RELAY"]["valore"],
           "relay.vero.example: simulato"
           in voci["AVVISO_DM_NOSTR_RELAY"]["valore"]))

    # --- si spegne tutto ---
    orologio.cancel()
    for o in S._DM_ASCOLTO.values():
        if o.get("ferma"):
            o["ferma"].set()
    loop.call_soon_threadsafe(loop.stop)

    print("\n[il journal: mai il testo, mai chi scrive]")
    sys.stdout = tutto.vero
    detto = "".join(tutto.detto)
    prova("il server ha stampato le sue righe (in ascolto, caduto, avviso)",
          (True, True, True),
          ("📩 Avviso DM: in ascolto su " + RELAY_A in detto,
           "📩 Avviso DM: " + RELAY_A + " CADUTO" in detto,
           "📩 Avviso DM: un avviso ai moderatori" in detto))
    prova("...e in tutto quel che ha stampato il testo dei messaggi non "
          "c'e'", False, SEGRETO in detto)
    prova("...ne' la chiave di chi ha scritto, in nessuna forma",
          [False] * 6,
          [x in detto for k in (MARIO, LUCIA, GINO)
           for x in (k, S.hex_to_npub(k))])
    prova("...e nemmeno negli avvisi: il testo non c'e'", False,
          any(SEGRETO in t for t, _ in AVVISI))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
