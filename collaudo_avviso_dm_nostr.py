# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'AVVISO DEI DM A BARATTOLO (11 ott 2026).

Richiesta di Andrea: quando qualcuno scrive un DM al profilo Nostr di
Barattolo, ai moderatori arriva «📩 Nuovo DM su Nostr da <chi>» — mai il
testo, niente doppioni, un tetto contro lo spam, niente avvisi per la
posta vecchia, e un relay che cade non porta giu' il server.
Dal 15 ott 2026 (cantiere dm-o-mail) l'avviso dice anche CHE COSA e'
arrivato: una chat (lo trovi in Amethyst), una mail Nostr (un client di
posta), un altro tipo col suo numero, o un tipo illeggibile.

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
    relay fra i `rotti` rifiuta la connessione.
    I `modi` (NIP-42) ne fanno un relay che chiede l'autenticazione, e
    risponde da solo come farebbe uno vero, nell'ordine in cui riceve:
      auth          manda la sfida alla connessione; senza AUTH chiude la
                    richiesta con «auth-required», dopo la serve
      auth-pigro    come sopra, ma la sfida la manda solo quando chiude
      ok-muto       accetta l'AUTH senza rispondere OK
      auth-rifiuta  accetta l'AUTH e poi chiude lo stesso («restricted»)
      auth-no       respinge l'AUTH (OK false)
      senza-sfida   chiude con «auth-required» e la sfida non la manda
      polso-chiuso  serve i DM a tutti, ma al «ci sei?» risponde CLOSED
    La `posta` di un relay e' quel che consegna prima dell'EOSE."""
    mandate = []
    code = {}
    aperte = {}
    rotti = set()
    modi = {}
    posta = {}
    CHIUSA = "ERROR: auth-required: requested filter requires authentication"

    def __init__(self, relay, timeout=10, sslopt=None):
        if relay in WsCartone.rotti:
            raise ConnectionRefusedError("relay di cartone spento")
        WsCartone.aperte[relay] = WsCartone.aperte.get(relay, 0) + 1
        self.relay, self.t = relay, timeout
        self.autenticato = WsCartone.modi.get(relay) == "polso-chiuso"
        if WsCartone.modi.get(relay) in ("auth", "ok-muto", "auth-rifiuta",
                                         "auth-no"):
            metti(relay, ["AUTH", "sfida-di-" + relay[-4:]])

    def settimeout(self, t):
        self.t = min(t, 0.05)            # il battito, ma svelto

    def send(self, s):
        msg = json.loads(s)
        WsCartone.mandate.append((self.relay, msg))
        modo = WsCartone.modi.get(self.relay)
        if msg[0] == "REQ" and msg[1] == "polso":
            metti(self.relay, ["CLOSED", "polso", WsCartone.CHIUSA]
                  if modo == "polso-chiuso" else ["EOSE", "polso"])
        elif modo and msg[0] == "AUTH":
            if modo == "auth-no":
                metti(self.relay, ["OK", msg[1]["id"], False,
                                   "restricted: questa chiave non entra"])
                return
            self.autenticato = True
            if modo != "ok-muto":
                metti(self.relay, ["OK", msg[1]["id"], True, ""])
        elif modo and msg[0] == "REQ" and msg[1] == "dm":
            if not self.autenticato:
                metti(self.relay, ["CLOSED", "dm", WsCartone.CHIUSA])
                if modo == "auth-pigro":
                    metti(self.relay, ["AUTH", "sfida-di-" + self.relay[-4:]])
            elif modo == "auth-rifiuta":
                metti(self.relay, ["CLOSED", "dm",
                                   "restricted: non sei fra gli ammessi"])
            else:
                for ev in WsCartone.posta.get(self.relay, []):
                    metti(self.relay, ["EVENT", "dm", ev])
                metti(self.relay, ["EOSE", "dm"])

    def recv(self):
        try:
            cosa = WsCartone.code.setdefault(
                self.relay, queue.Queue()).get(timeout=self.t)
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

    async def avvisa(testo, bottone=None, **k):   # k: la stanza del gruppo degli admin
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

        def sign_schnorr(self, msg):
            return schnorr_puro.firma(sk_noi, msg)
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

    def busta(sk_mitt, n="", dest=None, dentro=None, creato=None,
              kind_rumor=14):
        """Un DM NIP-17 intero: rumor (col SEGRETO) → sigillo → pacco,
        con la data del pacco arretrata come fa un client vero.
        `kind_rumor`: 14 la chat, 1301/2024 una mail Nostr..."""
        dest = dest or NOI
        pub = schnorr_puro.pubblica(sk_mitt).hex()
        rumor = S.evento_non_firmato(pub, kind_rumor, [["p", dest]],
                                     SEGRETO + n, int(time.time()))
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
          [(f"📩 Nuovo DM da Mario &lt;b&gt;Rossi&lt;/b&gt; &amp;co "
            f"({corta_m}), lo trovi in Amethyst", ("🟣 Apri in un client",
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
          (True, f"📩 2 nuovi DM da Mario &lt;b&gt;Rossi&lt;/b&gt; "
                 f"&amp;co ({corta_m}), li trovi in Amethyst"),
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
          "puo' aprire: l'avviso arriva lo stesso, col mittente, e dice "
          "che il tipo non si legge",
          (True, f"📨 Nuovo messaggio cifrato da {npub_g[:10]}…{npub_g[-6:]} "
                 "(tipo illeggibile)"),
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

    print("\n[la mail Nostr e il tipo sconosciuto (15 ott 2026, dm-o-mail)]")
    S._DM_AVVISI["mandati"] = []
    S._DM_AVVISI["mittenti"].pop(GINO, None)
    S._DM_AVVISI["mittenti"].pop(LUCIA, None)
    metti(RELAY_A, ["EVENT", "dm", busta(sk_gino, "mail", kind_rumor=1301)])
    metti(RELAY_B, ["EVENT", "dm", busta(sk_lucia, "ignoto", kind_rumor=7777)])
    prova("una busta con dentro una mail (1301) e una con un kind che non "
          "conosciamo (7777): due avvisi, ognuno col suo genere",
          (True, {(f"✉️ Nuova mail Nostr da {npub_g[:10]}…{npub_g[-6:]}: si "
                   "legge con un client di posta, es. Nmail",
                   ("🟣 Apri in un client", f"https://njump.me/{npub_g}")),
                  (f"📨 Messaggio cifrato di tipo 7777 da {corta_l}",
                   ("🟣 Apri in un client", f"https://njump.me/{npub_l}"))}),
          (aspetta(lambda: len(AVVISI) == 11), set(AVVISI[-2:])))

    print("\n[il nome dal profilo vero: in collaudo non si esce]")
    S._profilo_nostr = profilo_vero
    S._DM_AVVISI["mandati"] = []
    S._DM_AVVISI["mittenti"].pop(MARIO, None)
    metti(RELAY_A, ["EVENT", "dm", busta(sk_mario, "senza-nome")])
    prova("col lettore vero del kind 0 (relay pubblici: in collaudo non "
          "risponde nessuno) l'avviso parte lo stesso, con la sola npub",
          (True, f"📩 Nuovo DM da {corta_m}, lo trovi in Amethyst"),
          (aspetta(lambda: len(AVVISI) == 12, 15000), AVVISI[-1][0]))

    print("\n[il pannello delle leve]")
    voci = {v["chiave"]: v for v in S._dm_leve()}
    prova("la leva e' accesa e ogni relay dice il suo stato",
          (True, True, True),
          (voci["AVVISO_DM_NOSTR"]["valore"],
           "127.0.0.1:7801: connesso" in voci["AVVISO_DM_NOSTR_RELAY"]["valore"],
           "relay.vero.example: simulato"
           in voci["AVVISO_DM_NOSTR_RELAY"]["valore"]))

    # ================= NIP-42 (11 ott 2026, sera) =================
    # Acceso in produzione, relay.damus.io ha chiuso la sottoscrizione
    # con «ERROR: auth-required: requested filter requires
    # authentication». Qui i relay di cartone la chiedono in sei modi.
    def aggiungi(porta, modo):
        relay = f"ws://127.0.0.1:{porta}"
        WsCartone.modi[relay] = modo
        S.AVVISO_DM_NOSTR_RELAY.append(relay)
        return relay

    def di(relay, tipo, sub=None):
        return [m for r, m in list(WsCartone.mandate) if r == relay
                and m[0] == tipo and (sub is None or m[1] == sub)]

    def stato(relay):
        return S._DM_ASCOLTO.get(relay, {}).get("stato")

    S.AVVISO_DM_RELAY_MAX = 12
    S._DM_AVVISI["mandati"] = []

    print("\n[NIP-42: il relay chiede l'autenticazione, il server risponde]")
    n0 = len(AVVISI)
    RELAY_C = "ws://127.0.0.1:7803"
    WsCartone.posta[RELAY_C] = [busta(sk_gino, "vecchia-sul-relay-chiuso")]
    aggiungi(7803, "auth")
    prova("un relay che chiude con «auth-required» e manda la sfida: il "
          "filo si autentica e arriva in ascolto", True,
          aspetta(lambda: stato(RELAY_C) == "connesso"))
    risposte = di(RELAY_C, "AUTH")
    ev = risposte[0][1] if risposte else {}
    prova("...con UNA risposta: il kind 22242 firmato dalla chiave della "
          "piattaforma, col relay che abbiamo scritto NOI e la sua sfida",
          (1, 22242, NOI, [["relay", RELAY_C], ["challenge", "sfida-di-7803"]],
           "", True, True),
          (len(risposte), ev.get("kind"), ev.get("pubkey"), ev.get("tags"),
           ev.get("content"), S._x_firma_valida(ev),
           abs(ev.get("created_at", 0) - time.time()) < 60))
    richieste = di(RELAY_C, "REQ", "dm")
    prova("...e la sottoscrizione RIFATTA dopo l'OK: due richieste uguali, "
          "una prima e una dopo", (2, True),
          (len(richieste), richieste[0] == richieste[-1]))
    time.sleep(0.3)
    prova("...la posta che stava gia' su quel relay non avvisa", n0,
          len(AVVISI))
    metti(RELAY_C, ["EVENT", "dm", busta(chiave(40)[0], "dopo-l-auth")])
    prova("...e un DM nuovo arrivato li', dopo l'autenticazione, avvisa",
          True, aspetta(lambda: len(AVVISI) == n0 + 1))
    prova("ai relay che non la chiedono non si manda nessuna firma",
          [0, 0, 0], [len(di(r, "AUTH")) for r in (RELAY_A, RELAY_B,
                                                   RELAY_VERO)])

    RELAY_D = aggiungi(7804, "auth-pigro")
    prova("la sfida mandata solo DOPO la chiusura (il relay pigro): uguale, "
          "una firma e in ascolto", (True, 1, 2),
          (aspetta(lambda: stato(RELAY_D) == "connesso"),
           len(di(RELAY_D, "AUTH")), len(di(RELAY_D, "REQ", "dm"))))

    S.AVVISO_DM_AUTH_OK_S = 0.3
    RELAY_H = aggiungi(7808, "ok-muto")
    prova("un relay che accetta l'AUTH senza dire OK: dopo l'attesa si "
          "riprova lo stesso, e va", (True, 1, 2),
          (aspetta(lambda: stato(RELAY_H) == "connesso"),
           len(di(RELAY_H, "AUTH")), len(di(RELAY_H, "REQ", "dm"))))

    print("\n[NIP-42: il relay che rifiuta anche dopo: un'ora, non un minuto]")
    S.AVVISO_DM_RIFIUTO_S = 1.5
    S.AVVISO_DM_RIPOSO_PASSO_S = 0.05
    fermo = S.AVVISO_DM_FERMO_S
    S.AVVISO_DM_FERMO_S = 0.4
    RELAY_E = aggiungi(7805, "auth-rifiuta")
    prova("autenticato e chiuso lo stesso: lo stato e' «rifiutato», col "
          "perche' del relay", (True, True),
          (aspetta(lambda: stato(RELAY_E) == "rifiutato"),
           "non sei fra gli ammessi" in S._DM_ASCOLTO[RELAY_E]["perche"]))
    prova("...dopo UNA sola richiesta in piu' (la chiusura poteva essere "
          "quella di prima, arrivata tardi): tre in tutto, una firma",
          (3, 1), (len(di(RELAY_E, "REQ", "dm")), len(di(RELAY_E, "AUTH"))))
    filo_e = S._DM_ASCOLTO[RELAY_E]["filo"]
    time.sleep(0.8)
    prova("...e NON si riprova subito: dopo otto decimi (una caduta "
          "normale qui ne avrebbe fatti una decina) la connessione e' "
          "ancora una, e la guardia non ha scambiato l'attesa per un filo "
          "fermo", (1, True, True),
          (WsCartone.aperte[RELAY_E],
           S._DM_ASCOLTO[RELAY_E]["filo"] is filo_e, filo_e.is_alive()))
    prova("...passata l'attesa lunga riprova, UNA volta, e resta "
          "«rifiutato»", (True, "rifiutato"),
          (aspetta(lambda: WsCartone.aperte[RELAY_E] == 2, 3000),
           [time.sleep(0.3), stato(RELAY_E)][1]))
    S.AVVISO_DM_FERMO_S = fermo

    RELAY_F = aggiungi(7806, "auth-no")
    prova("un relay che RESPINGE la firma (OK false): «rifiutato», senza "
          "rifare la richiesta", (True, True, 1),
          (aspetta(lambda: stato(RELAY_F) == "rifiutato"),
           "autenticazione respinta" in S._DM_ASCOLTO[RELAY_F]["perche"],
           len(di(RELAY_F, "REQ", "dm"))))

    eose = S.AVVISO_DM_EOSE_S
    S.AVVISO_DM_EOSE_S = 0.4
    RELAY_G = aggiungi(7807, "senza-sfida")
    prova("un relay che chiede l'autenticazione e la sfida non la manda: "
          "niente da firmare, «rifiutato»", (True, True, 0),
          (aspetta(lambda: stato(RELAY_G) == "rifiutato"),
           "non c'e' una sfida" in S._DM_ASCOLTO[RELAY_G]["perche"],
           len(di(RELAY_G, "AUTH"))))
    RELAY_I = aggiungi(7809, "polso-chiuso")
    aspetta(lambda: stato(RELAY_I) == "connesso")
    S.AVVISO_DM_POLSO_S = 0.1
    time.sleep(1.2)
    prova("un relay che al «ci sei?» risponde CLOSED invece di EOSE ha "
          "risposto: e' vivo, e il filo non cade (tre volte l'attesa del "
          "polso, una connessione sola)", ("connesso", 1, True),
          (stato(RELAY_I), WsCartone.aperte[RELAY_I],
           len(di(RELAY_I, "REQ", "polso")) >= 3))
    S.AVVISO_DM_POLSO_S = polsi
    S.AVVISO_DM_EOSE_S = eose

    WsCartone.modi[RELAY_C] = None
    metti(RELAY_C, ["AUTH", 12345])
    metti(RELAY_C, ["AUTH", "x" * 300])
    metti(RELAY_C, ["AUTH", "una-seconda-sfida"])
    time.sleep(0.3)
    prova("una sfida che non e' una stringa, una troppo lunga, una seconda "
          "a connessione gia' autenticata: nessuna firma in piu'", 1,
          len(di(RELAY_C, "AUTH")))
    voci = {v["chiave"]: v for v in S._dm_leve()}
    prova("il pannello delle leve dice chi e' rifiutato", True,
          "127.0.0.1:7805: rifiutato"
          in voci["AVVISO_DM_NOSTR_RELAY"]["valore"])

    # LA FIRMA LENTA NON SI MANGIA L'ATTESA DELL'OK (24 ott 2026, cantiere
    # collaudi-senza-coincurve). In CI, senza coincurve, la firma la fa
    # il calco di schnorr_puro, e su una macchina carica puo' durare piu'
    # dell'attesa dell'OK: l'orologio partiva PRIMA della firma, il filo
    # dava l'OK per perso, «si prova lo stesso», e il NO del relay gia'
    # arrivato restava senza risposta (tre richieste, il perche' sbagliato).
    # Qui la firma dura apposta piu' dell'attesa: e' il caso da
    # provocare, non un sonno per farlo passare. La guardia dei fili
    # fermi e' tornata al suo valore di serie: non c'entra.
    print("\n[NIP-42: una firma lenta non si mangia l'attesa dell'OK]")
    S.AVVISO_DM_AUTH_OK_S = 0.3
    vera = S._NOSTR[0]

    class _Lenta:
        secret = getattr(vera, "secret", sk_noi)

        def sign_schnorr(self, msg):
            time.sleep(0.5)
            return vera.sign_schnorr(msg)
    S._NOSTR = (_Lenta(), NOI)
    RELAY_L = aggiungi(7810, "auth-no")
    prova("una firma piu' lenta dell'attesa e un relay che la respinge: "
          "«rifiutato» col perche' giusto, una richiesta e una firma",
          (True, True, 1, 1),
          (aspetta(lambda: stato(RELAY_L) == "rifiutato", 5000),
           "autenticazione respinta" in S._DM_ASCOLTO[RELAY_L]["perche"],
           len(di(RELAY_L, "REQ", "dm")), len(di(RELAY_L, "AUTH"))))
    S._NOSTR = (vera, NOI)
    firme =[m[1]["sig"] for r, m in list(WsCartone.mandate) if m[0] == "AUTH"]

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
    prova("che si e' autenticato lo dice la riga «in ascolto», e solo per "
          "chi l'ha fatto", (True, False),
          (f"📩 Avviso DM: in ascolto su {RELAY_C} (autenticato, NIP-42)"
           in detto,
           f"in ascolto su {RELAY_A} (autenticato" in detto))
    prova("il relay che rifiuta lascia nel journal UNA riga in tutto — "
          "«RIFIUTA … riprovo fra un'ora» — anche se nel frattempo ha "
          "riprovato (e si e' riautenticato)", (1, 1, True),
          (sum(1 for r in detto.splitlines() if RELAY_E in r),
           detto.count(f"📩 Avviso DM: {RELAY_E} RIFIUTA ("),
           WsCartone.aperte[RELAY_E] >= 2))
    prova("...e le firme delle risposte AUTH nel journal non ci sono",
          (True, False), (len(firme) >= 5, any(f in detto for f in firme)))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
