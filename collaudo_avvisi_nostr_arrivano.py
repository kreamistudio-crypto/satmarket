# -*- coding: utf-8 -*-
"""
GLI AVVISI NOSTR ARRIVANO, SUL SERVER VERO (20 ott 2026, cantiere
avvisi-nostr-arrivano, decisione di Andrea: «gli avvisi devono arrivare»).

Il caso vero: un account entrato SOLO da Nostr, il cui profilo non
pubblica la lista dei relay dei messaggi (kind 10050). I suoi avvisi
partivano come DM NIP-17 verso quattro relay di serie che il suo client
non legge: non sapeva niente di un ordine ne' di un messaggio, e nel
journal non restava traccia. Qui si guarda, sul server vero, che:

  1. LA LETTURA DELLE LISTE: `chiedi_relay_dm` sa leggere il 10050 e i
     relay di LETTURA del 10002 (NIP-65: senza segno o «read», mai
     «write»), e dice `[]` a chi risponde senza lista e None a chi tace;
  2. DOVE VA IL DM: col 10050 ai suoi relay (i primi quattro); senza,
     ai relay di lettura del suo 10002 e poi ai nostri, mai a un ws://
     o a un relay di casa scritto da lui, al piu' otto; coi relay muti
     la riserva lo stesso, ma «non si sa»;
  3. IL JOURNAL: a chi non ha il 10050 la riga 📭, sempre; a chi ce
     l'ha niente di nuovo;
  4. IL NIP-04 DI RISERVA: a leva spenta non parte mai; accesa, parte
     solo a chi non ha il 10050, sugli stessi relay;
  5. «📬 I TUOI AVVISI»: la `notifica()` VERA salva l'avviso per chi
     entra senza Telegram (testo spoglio, i soli bottoni web) e NON per
     chi ha Telegram, che riceve com'e' sempre ricevuto; la lista, il
     conto dei nuovi in /api/me, «letti»; il tetto e la scadenza;
  6. IL 10050 ALL'INGRESSO: /api/me di chi non ce l'ha scrive 'no' (e
     la riga 📭 una volta), di chi ce l'ha 'si', coi relay muti niente;
     il cartello si segna visto una volta e non si riscrive; a chi ha
     Telegram non parte nessuno sguardo.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, il database e' usa-e-getta, e non esce niente: le
letture dai relay e gli invii sono di cartone (le liste stanno in un
dizionario, le buste finiscono in una lista). La sola connessione aperta
e' una websocket di CARTONE, che non apre nessuna porta.

USO:  python collaudo_avvisi_nostr_arrivano.py
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
RIGHE = []        # quel che il server ha stampato
TELEGRAM = []     # (tg_id, testo, bottone) del trasporto di cartone
BUSTE = []        # (relay, kind) di ogni evento «spedito»

TG, CON_LISTA, SOLO_LETTURA, SENZA, MUTI = 111, -501, -502, -503, -504
HEX = {CON_LISTA: "a1" * 32, SOLO_LETTURA: "b2" * 32, SENZA: "c3" * 32,
       MUTI: "d4" * 32}
SUOI_DM = ["wss://dm.uno.example", "wss://dm.due.example",
           "wss://dm.tre.example", "wss://dm.quattro.example",
           "wss://dm.cinque.example"]
# il 10002 di chi non ha il 10050: due di lettura buoni, uno doppione
# (la barra in fondo), un ws:// e uno di casa (fuori), uno di sola
# scrittura (non arriva nemmeno: lo scarta la lettura del 10002)
SUOI_LETTURA = ["wss://legge.uno.example", "wss://legge.due.example/",
                "wss://legge.uno.example/", "ws://legge.chiaro.example",
                "wss://127.0.0.1:7777"]


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    tmp = tempfile.mkdtemp(prefix="barattolo-avvisi-nostr-")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = os.path.join(tmp, "usa-e-getta.db")
    sys.modules["config"] = cfg
    if "anthropic" not in sys.modules:
        finto = types.ModuleType("anthropic")
        finto.Anthropic = lambda **k: types.SimpleNamespace(messages=None)
        sys.modules["anthropic"] = finto
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    def stampa(*a, **k):
        RIGHE.append(" ".join(str(x) for x in a))
        print(*a, **k)
    server.print = stampa

    async def telegram_finto(tg_id, testo, bottone=None):
        TELEGRAM.append((tg_id, testo, bottone))
        return "telegram ok (cartone)"
    server._manda_telegram = telegram_finto

    # LE LISTE DEI RELAY, DI CARTONE: (chiave, kind) -> la risposta che
    # darebbe ognuno dei relay di serie. None = muto.
    liste = {(HEX[CON_LISTA], 10050): SUOI_DM,
             (HEX[SOLO_LETTURA], 10050): [],
             (HEX[SOLO_LETTURA], 10002): SUOI_LETTURA,
             (HEX[SENZA], 10050): [], (HEX[SENZA], 10002): [],
             (HEX[MUTI], 10050): None, (HEX[MUTI], 10002): None}
    server._chiedi_vero = server.chiedi_relay_dm
    server.chiedi_relay_dm = lambda relay, hexkey, kind=10050: \
        liste.get((hexkey, kind))

    def invia_finto(relay, evento):
        BUSTE.append((relay, evento.get("kind")))
        return True
    server.invia_evento_relay = invia_finto
    # la chiave della piattaforma e i pacchi: di cartone, che la busta
    # vera la prova prove.py (e coincurve in CI non c'e')
    server._NOSTR = ("chiave di cartone", "f" * 64)
    server.impacchetta_dm = lambda dest, testo: {"kind": 1059, "dest": dest}
    server.impacchetta_dm_nip04 = lambda dest, testo: {"kind": 4, "dest": dest}
    return tmp


def utenti():
    con = SRV.db()
    adesso = int(time.time())
    con.execute("INSERT INTO utenti(tg_id, nome, registrato) VALUES(?,?,?)",
                (TG, "Telegrammo", adesso))
    for tg in (CON_LISTA, SOLO_LETTURA, SENZA, MUTI):
        con.execute("INSERT INTO utenti(tg_id, nome, registrato, npub_accesso) "
                    "VALUES(?,?,?,?)",
                    (tg, f"Nostr{-tg}", adesso, SRV.hex_to_npub(HEX[tg])))
    con.commit()
    con.close()


def come(tg_id):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "username": f"u{tg_id}",
        "admin": False}


async def lascia_finire():
    """I lavori in sottofondo del server (l'avviso in app, lo sguardo
    al 10050) finiscono prima che il loop si chiuda."""
    for _ in range(200):
        altri = [t for t in asyncio.all_tasks()
                 if t is not asyncio.current_task() and not t.done()]
        if not altri:
            return
        await asyncio.sleep(0.02)


def riga_utente(tg):
    con = SRV.db()
    r = con.execute("SELECT relay_dm, relay_dm_visto, relay_dm_avvisato "
                    "FROM utenti WHERE tg_id=?", (tg,)).fetchone()
    con.close()
    return dict(r)


def avvisi_di(tg):
    con = SRV.db()
    r = [dict(x) for x in con.execute(
        "SELECT testo, bottoni, letto FROM avvisi_app WHERE tg_id=? "
        "ORDER BY id", (tg,))]
    con.close()
    return r


class _WsDiCartone:
    """Una websocket che non apre niente: risponde alla REQ con le
    righe preparate, poi tace (recv alza, come un relay che cade)."""

    def __init__(self, risposte):
        self.risposte = list(risposte)
        self.mandati = []

    def send(self, m):
        self.mandati.append(json.loads(m))

    def recv(self):
        if not self.risposte:
            raise TimeoutError("relay di cartone: zitto")
        return json.dumps(self.risposte.pop(0))

    def close(self):
        pass


def main():
    print("=" * 58)
    print("  GLI AVVISI NOSTR ARRIVANO — il giro vero")
    print("=" * 58)
    tmp = avvio()
    utenti()
    SERIE = list(SRV.RELAYS_VERIFICA)

    # ---- 1) LA LETTURA DELLE LISTE ----------------------------------------
    print("\n[1) chiedi_relay_dm: il 10050, il 10002, niente e zitto]")
    CASA = "ws://127.0.0.1:9"      # di casa: il giudice delle letture lo lascia
    vera_conn = SRV.create_connection

    def chiedi(risposte, kind=10050):
        ws = _WsDiCartone(risposte)
        SRV.create_connection = lambda *a, **k: ws
        try:
            return SRV._chiedi_vero(CASA, "e5" * 32, kind), ws.mandati
        finally:
            SRV.create_connection = vera_conn
    ev_10002 = {"kind": 10002, "tags": [
        ["r", "wss://a.example"], ["r", "wss://b.example", "read"],
        ["r", "wss://c.example", "write"], ["p", "x"], ["r", "https://no"]]}
    trovati, mandati = chiedi([["EVENT", "dm", ev_10002], ["EOSE", "dm"]], 10002)
    prova("il 10002: i relay senza segno e quelli «read», mai «write», "
          "mai un indirizzo che non e' un relay",
          ["wss://a.example", "wss://b.example"], trovati)
    prova("...e la domanda e' sul kind 10002 della persona",
          [["REQ", "dm", {"kinds": [10002], "authors": ["e5" * 32],
                          "limit": 1}]], mandati)
    ev_10050 = {"kind": 10050, "tags": [["relay", "wss://dm.example"],
                                        ["r", "wss://non-e-questo.example"]]}
    prova("il 10050: i tag «relay», come sempre",
          ["wss://dm.example"],
          chiedi([["EVENT", "dm", ev_10050], ["EOSE", "dm"]])[0])
    prova("un relay che risponde SENZA la lista dice [] («non ce l'ha»)",
          [], chiedi([["EOSE", "dm"]])[0])
    prova("...uno che tace dice None («non si sa»)", None, chiedi([])[0])
    # LO STESSO COL POSTINO (la connessione tenuta viva dei relay di serie):
    # una sottoscrizione CHIUSA senza EOSE (auth-required) non e' un «no»
    vero_postino = SRV._posta_per

    class _Postino:
        def __init__(self, letto):
            self.letto = letto

        def leggi(self, filtro, tetto=None):
            return self.letto
    esiti = []
    for letto in (([], True), ([], False), None,
                  ([{"tags": [["relay", "wss://dm.example"]]}], False)):
        SRV._posta_per = lambda relay, _l=letto: _Postino(_l)
        try:
            esiti.append(SRV._chiedi_vero(CASA, "e5" * 32))
        finally:
            SRV._posta_per = vero_postino
    prova("col postino: EOSE vuoto = [], chiusa senza EOSE = None, muto = "
          "None, una lista arrivata prima della chiusura vale",
          [[], None, None, ["wss://dm.example"]], esiti)

    # ---- 2) DOVE VA IL DM -------------------------------------------------
    print("\n[2) relay_dm_dove: col 10050, col solo 10002, senza niente, muti]")
    dove = {tg: asyncio.run(SRV.relay_dm_dove(HEX[tg]))
            for tg in (CON_LISTA, SOLO_LETTURA, SENZA, MUTI)}
    prova("col 10050: i suoi relay, i primi quattro", (SUOI_DM[:4], "si"),
          dove[CON_LISTA])
    prova("col solo 10002: prima i suoi di lettura (senza doppioni, ws:// e "
          "di casa fuori), poi i nostri quattro",
          (["wss://legge.uno.example", "wss://legge.due.example/"]
           + SERIE[:4], "no"), dove[SOLO_LETTURA])
    prova("senza niente: i nostri quattro, e «no»", (SERIE[:4], "no"),
          dove[SENZA])
    prova("coi relay muti: la riserva lo stesso, ma «non si sa»",
          (SERIE[:4], "?"), dove[MUTI])
    prova("il tetto: mai piu' di otto relay", True,
          all(len(d[0]) <= SRV.DM_RISERVA_MAX_RELAY == 8 for d in dove.values()))

    # ---- 3) IL JOURNAL, e 4) IL NIP-04 -------------------------------------
    print("\n[3) la riga 📭 nel journal, 4) il NIP-04 di riserva]")
    SRV.MODALITA_COLLAUDO = False          # solo qui: gli invii sono di cartone

    def manda(tg):
        del BUSTE[:]
        prima = len(RIGHE)
        ok = asyncio.run(SRV.manda_dm_nostr(HEX[tg], "🔔 Prova"))
        # in ordine: le buste partono da thread paralleli, e chi arriva
        # prima lo decide il sistema
        return ok, sorted(BUSTE), RIGHE[prima:]
    try:
        ok, buste, righe = manda(CON_LISTA)
        prova("col 10050: la busta NIP-17 ai suoi relay, e il journal tace",
              [True, sorted((r, 1059) for r in SUOI_DM[:4]), []], [ok, buste, righe])
        ok, buste, righe = manda(SENZA)
        prova("senza 10050: la busta NIP-17 alla riserva, e niente NIP-04 a "
              "leva spenta", [True, sorted((r, 1059) for r in SERIE[:4])], [ok, buste])
        prova("...e il journal lo dice: «📭 … nessun 10050, busta NIP-17 su 4/4 "
              "relay di riserva»", True,
              len(righe) == 1 and righe[0].startswith(f"📭 DM Nostr a {HEX[SENZA][:16]}…")
              and "nessun 10050, busta NIP-17 su 4/4 relay di riserva" in righe[0]
              and "NIP-04" not in righe[0])
        ok, buste, righe = manda(MUTI)
        prova("coi relay muti la riga dice «10050 non letto»", True,
              len(righe) == 1 and "10050 non letto (relay muti)" in righe[0])
        SRV.DM_NIP04_RISERVA = True
        ok, buste, righe = manda(SENZA)
        prova("A LEVA ACCESA, senza 10050: la busta NIP-17 E il NIP-04, sugli "
              "stessi relay", sorted([(r, 1059) for r in SERIE[:4]]
                                     + [(r, 4) for r in SERIE[:4]]), sorted(buste))
        prova("...e la riga lo conta", True,
              len(righe) == 1 and ", NIP-04 su 4" in righe[0])
        ok, buste, righe = manda(CON_LISTA)
        prova("...a chi ha il 10050 il NIP-04 non parte nemmeno a leva accesa",
              sorted((r, 1059) for r in SUOI_DM[:4]), buste)
        SRV.DM_NIP04_RISERVA = False
        rifiuta = SRV.invia_evento_relay
        SRV.invia_evento_relay = lambda relay, ev: False
        ok, buste, righe = manda(SENZA)
        prova("nessun relay accetta: la 📭 e la ⚠️ di sempre, e l'esito falso",
              [False, True, True], [ok, any(r.startswith("📭") for r in righe),
                                    any("nessun relay l'ha accettato" in r for r in righe)])
        SRV.invia_evento_relay = rifiuta
    finally:
        SRV.MODALITA_COLLAUDO = True
        SRV.DM_NIP04_RISERVA = False

    # ---- 5) «📬 I TUOI AVVISI» -------------------------------------------
    print("\n[5) la notifica vera: l'avviso resta in app per chi non ha Telegram]")
    BOTT = [("⚡ Apri lo scambio", "https://barattolo.store/p2p?scambio=x"),
            ("🤖 Nel bot", "tg://resolve?domain=ilbarattolobot")]

    async def due_avvisi():
        await SRV.notifica(SENZA, "📦 <b>Il tuo ordine #7</b> &amp; è partito",
                           BOTT)
        await SRV.notifica(TG, "📦 <b>Il tuo ordine #8</b> è partito", BOTT)
        await lascia_finire()
    asyncio.run(due_avvisi())
    prova("chi entra senza Telegram ha l'avviso in app: testo spoglio, il solo "
          "bottone web", [{"testo": "📦 Il tuo ordine #7 & è partito",
                           "bottoni": json.dumps([list(BOTT[0])],
                                                 ensure_ascii=False),
                           "letto": 0}], avvisi_di(SENZA))
    prova("chi ha Telegram: nessuna riga in app, e il bot riceve come sempre "
          "(testo e bottoni com'erano)",
          [[], [(TG, "📦 <b>Il tuo ordine #8</b> è partito", BOTT)]],
          [avvisi_di(TG), TELEGRAM])

    print("\n[5b) la lista, i nuovi in /api/me, «letti»]")
    come(SENZA)
    lista = asyncio.run(SRV.miei_avvisi_app())
    prova("/api/me/avvisi: l'avviso, i bottoni come lista, uno nuovo",
          [1, [list(BOTT[0])], False, 1],
          [len(lista["avvisi"]), lista["avvisi"][0]["bottoni"],
           lista["avvisi"][0]["letto"], lista["nuovi"]])

    async def profilo():
        p = await SRV.mio_profilo()
        await lascia_finire()
        return p
    prova("/api/me di chi entra senza Telegram dice quanti avvisi sono nuovi",
          1, asyncio.run(profilo()).get("avvisi_app_nuovi"))
    asyncio.run(SRV.avvisi_app_letti())
    prova("«letti»: zero nuovi, e l'avviso resta nella lista", [0, 1],
          [asyncio.run(SRV.miei_avvisi_app())["nuovi"], len(avvisi_di(SENZA))])
    come(TG)
    p_tg = asyncio.run(profilo())
    prova("/api/me di chi ha Telegram non porta la chiave nuova",
          False, "avvisi_app_nuovi" in p_tg)

    print("\n[5c) il tetto e la scadenza]")
    con = SRV.db()
    vecchio = int(time.time()) - (SRV.AVVISI_APP_GIORNI + 1) * 86400
    con.execute("INSERT INTO avvisi_app(tg_id, testo, quando) VALUES(?,?,?)",
                (SENZA, "vecchio", vecchio))
    con.commit()
    con.close()
    for i in range(SRV.AVVISI_APP_MAX + 5):
        SRV._avviso_in_app(SENZA, f"avviso {i}")
    testi = [a["testo"] for a in avvisi_di(SENZA)]
    prova(f"ne restano {SRV.AVVISI_APP_MAX}, i piu' nuovi, e quello di oltre "
          f"{SRV.AVVISI_APP_GIORNI} giorni se n'e' andato",
          [SRV.AVVISI_APP_MAX, f"avviso {SRV.AVVISI_APP_MAX + 4}", False],
          [len(testi), testi[-1], "vecchio" in testi])

    # ---- 6) IL 10050 ALL'INGRESSO ------------------------------------------
    print("\n[6) il 10050 si guarda all'ingresso, e il cartello passa una volta]")
    # da capo: le /api/me di qui sopra hanno gia' guardato chi passava
    SRV._RELAY_DM_CACHE.clear()
    SRV._RELAY_DM_TENTATO.clear()
    con = SRV.db()
    con.execute("UPDATE utenti SET relay_dm='', relay_dm_visto=0")
    con.commit()
    con.close()
    prima = len(RIGHE)
    for tg in (SENZA, CON_LISTA, MUTI):
        come(tg)
        asyncio.run(profilo())
    prova("senza 10050: 'no'; col 10050: 'si'; relay muti: non si scrive niente",
          ["no", "si", ""],
          [riga_utente(tg)["relay_dm"] for tg in (SENZA, CON_LISTA, MUTI)])
    prova("...e il journal dice il 'no', una riga", 1,
          sum(1 for r in RIGHE[prima:]
              if r.startswith(f"📭 L'utente {SENZA} (solo Nostr) non pubblica un 10050")))
    come(SENZA)
    p = asyncio.run(profilo())
    prova("/api/me porta 'no' e il cartello mai visto; un secondo /api/me nello "
          "stesso giorno non riguarda i relay", ["no", 0, 1],
          [p["relay_dm"], p["relay_dm_avvisato"],
           sum(1 for r in RIGHE[prima:] if r.startswith(f"📭 L'utente {SENZA}"))])
    asyncio.run(SRV.relay_dm_avvisato())
    visto = riga_utente(SENZA)["relay_dm_avvisato"]
    time.sleep(1.1)
    asyncio.run(SRV.relay_dm_avvisato())
    prova("il cartello si segna visto, e un secondo segno non lo riscrive",
          [True, visto], [visto > 0, riga_utente(SENZA)["relay_dm_avvisato"]])
    come(TG)
    asyncio.run(profilo())
    prova("a chi ha Telegram nessuno sguardo ai relay", [False, ""],
          [TG in SRV._RELAY_DM_TENTATO, riga_utente(TG)["relay_dm"]])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    print(f"  (database usa-e-getta in {tmp})")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
