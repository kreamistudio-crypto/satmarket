# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ACCESSO DI CASA (14 nov 2026, cantiere audit-account,
dal primo audit di sicurezza, Andrea: «tu cmq non mi cambi niente in
app, me la rendi solo più sicura»).

`prove_accesso_di_casa` fa girare i tre pezzi su banchi di cartone. Qui
si fa il giro VERO: il server intero, un browser per persona coi suoi
cookie, le firme Schnorr vere, il database vero (usa e getta).

Le domande a cui risponde:

  · LA FIRMA DEL LOGIN VALE SOLO A CASA. Un evento 22242 e' anche la
    forma dell'AUTH che un relay chiede ai suoi client: un relay puo'
    farsi firmare la NOSTRA sfida e ripresentarla qui col suo nome
    nell'Host. Si fa per davvero: stessa chiave, sfida nostra, tag
    `relay` del forestiero, `Host` del forestiero — e non si entra.
    Col nome di casa si entra come sempre.
  · IL BIGLIETTO DEL COLLEGAMENTO NON SOPRAVVIVE ALL'ACCOUNT CHE LO HA
    FATTO NASCERE: chi toglie la chiave dal profilo, o ne collega
    un'altra, mentre un biglietto e' in giro, non si ritrova in casa
    chi lo tiene in mano. Il si' di sempre collega ed entra.
  · A PORTA DEL BOT APERTA IL RITORNO DEL WIDGET TELEGRAM NON APRE
    SESSIONI, nemmeno con dati firmati bene: e' un indirizzo che si
    puo' mandare a un altro. A porta spenta e' il login di ieri.

LE FIRME (14 nov 2026, riparazione): il runner della CI non ha
coincurve, e la prima stesura lo pretendeva — in CI sarebbe uscita
rossa senza aver girato. Adesso fa come `collaudo_fusione_da_telegram`:
firma con la ricetta BIP-340 del repo (`schnorr_puro`), e il server
verifica col suo giudice VERO, coincurve dove c'e' e, dove non c'e',
`schnorr_puro.ChiaveXOnly` montato al posto di `ChiavePubblicaNostr`
(dopo aver guardato che da solo, senza, la porta Nostr risponde 503).
Nessun salto.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna chiave vera, nessuna rete, nessun relay.

USO:  python collaudo_accesso_di_casa.py
"""

import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
import types

import schnorr_puro

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
GETTONE = "0:collaudo"
PARTITI = []        # quel che sarebbe andato a Telegram (non ci va niente)


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
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-accesso-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    # I segreti si posano col setattr e mai come `NOME = "valore"`:
    # quella e' la forma di un file di configurazione, e lo scanner
    # della CI non puo' distinguere una chiave finta da una vera.
    for k, v in (("BOT_TOKEN", GETTONE),
                 ("ANTHROPIC_API_KEY", "INCOLLA_QUI"),
                 ("LNBITS_URL", "http://127.0.0.1:1"),
                 ("LNBITS_INVOICE_KEY", "INCOLLA_QUI"),
                 ("LNBITS_ADMIN_KEY", "INCOLLA_QUI"),
                 ("ADMIN_IDS", [999]),
                 ("MODALITA_COLLAUDO", True),
                 ("COMMISSIONE_PERCENTO", 0),
                 ("ORE_CONFERMA", 72),
                 ("GIORNI_AUTO_SBLOCCO", 10),
                 ("MODELLO_RICERCA", "claude-haiku-4-5-20251001"),
                 ("MOSTRO_RELAY", "ws://127.0.0.1:9"),
                 ("MOSTRO_RELAY_SPECCHIO", "ws://127.0.0.1:9"),
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server

    # (14 nov 2026, riparazione) QUESTO COLLAUDO, in due scene, fa credere
    # al server di essere in PRODUZIONE (`MODALITA_COLLAUDO = False`: e' il
    # solo modo di provare la porta col nome vero). Li' un avviso a una
    # persona non e' piu' simulato: `_manda_telegram` bussava davvero a
    # Telegram (col gettone finto non arrivava a nessuno, ma la
    # gabbia della CI lo vede e ha ragione: da un collaudo non esce
    # niente). Nel cloud non si vedeva, perche' col proxy acceso la
    # gabbia non vede il DNS. Le due strade verso Telegram qui sono finte
    # per tutta la durata, e i relay vanno a quello morto.
    async def telegram_finto(tg_id, testo, bottone=None):
        PARTITI.append((tg_id, testo))
        return "simulata (collaudo)"

    async def bot_finto(metodo, dati):
        PARTITI.append((metodo, dati))
        return {"ok": True}
    server._manda_telegram = telegram_finto
    server.bot_api = bot_finto
    return server


def nuova_chiave() -> bytes:
    """Una chiave privata usa-e-getta, 32 byte nella misura del BIP-340."""
    while True:
        sk = os.urandom(32)
        if 1 <= int.from_bytes(sk, "big") < schnorr_puro.N:
            return sk


def pubblica_hex(sk: bytes) -> str:
    return schnorr_puro.pubblica(sk).hex()


def firma_login(sk, sfida, origine):
    """L'evento 22242 firmato davvero (Schnorr), col tag `relay` che si
    vuole: e' lo stesso che compone la pagina, ed e' lo stesso che un
    relay chiede per la sua AUTH (NIP-42)."""
    pub = pubblica_hex(sk)
    ev = {"pubkey": pub, "created_at": int(time.time()), "kind": 22242,
          "tags": [["relay", origine], ["challenge", sfida]], "content": ""}
    ser = json.dumps([0, pub, ev["created_at"], 22242, ev["tags"], ""],
                     separators=(",", ":"), ensure_ascii=False)
    ev["id"] = hashlib.sha256(ser.encode()).hexdigest()
    ev["sig"] = schnorr_puro.firma(sk, bytes.fromhex(ev["id"]),
                                   os.urandom(32)).hex()
    return ev


def dati_widget(tg_id, quando=None):
    """I dati che Telegram mette nella query del ritorno, firmati come
    li firma lui: chiave = SHA256 del token del bot."""
    d = {"id": str(tg_id), "first_name": "Widget",
         "auth_date": str(int(quando or time.time()))}
    controllo = "\n".join(f"{k}={d[k]}" for k in sorted(d))
    d["hash"] = hmac.new(hashlib.sha256(GETTONE.encode()).digest(),
                         controllo.encode(), hashlib.sha256).hexdigest()
    return d


def main():
    server = avvio()
    from fastapi.testclient import TestClient

    print("=" * 58)
    print("  IL COLLAUDO DELL'ACCESSO DI CASA")
    print("=" * 58)

    print("\n[0) le firme: il patto del server, e il calco dove coincurve non c'e']")
    if server.ChiavePubblicaNostr is None:
        prova("senza coincurve il server non apre la porta Nostr (503)", 503,
              TestClient(server.app).get("/api/login/nostr/sfida").status_code)
        server.ChiavePubblicaNostr = schnorr_puro.ChiaveXOnly
        print("   (coincurve assente: monto schnorr_puro.ChiaveXOnly, come in CI)")
    else:
        print("   (coincurve presente: il server verifica con libsecp256k1)")

    def riga(tg_id):
        con = server.db()
        r = con.execute("SELECT npub, npub_verificata, npub_accesso FROM "
                        "utenti WHERE tg_id=?", (tg_id,)).fetchone()
        con.close()
        return (r["npub"], r["npub_verificata"], r["npub_accesso"])

    def sessioni_di(tg_id):
        con = server.db()
        n = con.execute("SELECT COUNT(*) FROM sessioni WHERE tg_id=?",
                        (tg_id,)).fetchone()[0]
        con.close()
        return n

    # ------------------------------------------------------------------
    # 1) LA FIRMA DEL LOGIN VALE SOLO A CASA
    # ------------------------------------------------------------------
    print("\n[la firma del login vale solo a casa]")
    vittima = nuova_chiave()
    npub_v = server.hex_to_npub(pubblica_hex(vittima))
    c = TestClient(server.app)
    sfida = c.get("/api/login/nostr/sfida").json()["sfida"]
    r = c.post("/api/login/nostr",
               json={"evento": firma_login(vittima, sfida, "http://testserver")})
    prova("IN COLLAUDO si entra come sempre (il nome e' quello della gabbia)",
          (200, True), (r.status_code, r.json().get("nuovo")))
    id_v = c.get("/api/me").json()["tg_id"]
    prova("...ed e' nato il nativo, con la sua sessione", (True, 1),
          (id_v < 0, sessioni_di(id_v)))

    # da qui il server si crede in PRODUZIONE, col suo nome vero: e' il
    # solo modo di provare la porta com'e' sul VPS. Si rimette a posto
    # in fondo alla scena.
    server.MODALITA_COLLAUDO = False
    nome_prima = server.URL_PUBBLICO
    server.URL_PUBBLICO = "https://barattolo.store"
    try:
        # IL RELAY CATTIVO: si e' fatto firmare la NOSTRA sfida come AUTH
        # (il tag `relay` e' il suo indirizzo, come vuole il NIP-42), e
        # la ripresenta qui scrivendo il suo nome nell'Host.
        ladro = TestClient(server.app)
        sfida = ladro.get("/api/login/nostr/sfida",
                          headers={"host": "barattolo.store"}).json()["sfida"]
        ev = firma_login(vittima, sfida, "wss://relay.cattivo.example/")
        r = ladro.post("/api/login/nostr", json={"evento": ev},
                       headers={"host": "relay.cattivo.example"})
        prova("IL RELAY CHE RIPRESENTA LA NOSTRA SFIDA COL SUO NOME: 401",
              (401, "Login Nostr non valido: riprova"),
              (r.status_code, r.json().get("detail")))
        prova("...nessun cookie di sessione nella risposta", False,
              "barattolo_sessione" in r.headers.get("set-cookie", ""))
        prova("...e nessuna sessione in piu' sull'account della vittima", 1,
              sessioni_di(id_v))
        # lo stesso con la porta nell'Host e nel tag
        sfida = ladro.get("/api/login/nostr/sfida",
                          headers={"host": "barattolo.store"}).json()["sfida"]
        ev = firma_login(vittima, sfida, "wss://relay.cattivo.example:7777")
        r = ladro.post("/api/login/nostr", json={"evento": ev},
                       headers={"host": "relay.cattivo.example:7777"})
        prova("...nemmeno con una porta nel nome", 401, r.status_code)
        # e dalla porta «Entra anche con Nostr» di un account Telegram:
        # la stessa firma forestiera non collega la chiave a nessuno
        server.MODALITA_COLLAUDO = True
        tg = TestClient(server.app)
        tg.post("/api/login/telegram",
                json={"collaudo": True, "id": 851, "first_name": "Telegram"})
        server.MODALITA_COLLAUDO = False
        altra = nuova_chiave()
        sfida = tg.get("/api/login/nostr/sfida",
                       headers={"host": "barattolo.store"}).json()["sfida"]
        ev = firma_login(altra, sfida, "wss://relay.cattivo.example/")
        r = tg.post("/api/me/npub/collega-firma", json={"evento": ev},
                    headers={"host": "relay.cattivo.example"})
        prova("«Entra anche con Nostr» con una firma forestiera: 401, e "
              "nessuna chiave collegata",
              (401, ("", 0, "")), (r.status_code, riga(851)))

        # IL NOME DI CASA: la pagina vera firma con la sua origine, e il
        # browser manda il nome del sito
        casa = TestClient(server.app, base_url="https://barattolo.store")
        sfida = casa.get("/api/login/nostr/sfida").json()["sfida"]
        r = casa.post("/api/login/nostr", json={
            "evento": firma_login(vittima, sfida, "https://barattolo.store")})
        prova("COL NOME DI CASA si entra come sempre", (200, True),
              (r.status_code, r.json().get("ok")))
        prova("...nell'account di chi ha firmato", id_v,
              casa.get("/api/me").json()["tg_id"])
        # IL WWW DEL SITO (14 nov 2026, audit-parole-bot): Caddy serve
        # l'app anche li', e chi entra da li' firma con quell'origine
        www = TestClient(server.app, base_url="https://www.barattolo.store")
        sfida = www.get("/api/login/nostr/sfida").json()["sfida"]
        r = www.post("/api/login/nostr", json={
            "evento": firma_login(vittima, sfida,
                                  "https://www.barattolo.store")})
        prova("...e anche dal www del sito, nello stesso account",
              (200, id_v), (r.status_code, www.get("/api/me").json()["tg_id"]))
        sfida = www.get("/api/login/nostr/sfida").json()["sfida"]
        r = www.post("/api/login/nostr", json={
            "evento": firma_login(vittima, sfida,
                                  "https://www.barattolo.store")},
            headers={"host": "barattolo.store"})
        prova("...ma la firma fatta sul www non vale presentata sull'altro "
              "nome (il tag e l'Host devono combaciare, come sempre)",
              401, r.status_code)
        sfida = tg.get("/api/login/nostr/sfida",
                       headers={"host": "barattolo.store"}).json()["sfida"]
        npub_a = server.hex_to_npub(pubblica_hex(altra))
        tg_casa = TestClient(server.app, base_url="https://barattolo.store")
        tg_casa.cookies.update(dict(tg.cookies))
        r = tg_casa.post("/api/me/npub/collega-firma", json={
            "evento": firma_login(altra, sfida, "https://barattolo.store")})
        prova("...e «Entra anche con Nostr» da casa collega la chiave",
              (200, (npub_a, 1, npub_a)), (r.status_code, riga(851)))
    finally:
        server.MODALITA_COLLAUDO = True
        server.URL_PUBBLICO = nome_prima

    # ------------------------------------------------------------------
    # 2) IL BIGLIETTO DEL COLLEGAMENTO
    # ------------------------------------------------------------------
    print("\n[il biglietto del collegamento]")

    def account_col_badge(tg_id):
        """Un account Telegram col badge VERIFICATO e l'accesso libero,
        fatto coi gesti veri: «Entra anche con Nostr» e poi «disabilita».
        Torna (il browser del titolare, la chiave)."""
        b = TestClient(server.app)
        b.post("/api/login/telegram",
               json={"collaudo": True, "id": tg_id, "first_name": "Badge"})
        sk = nuova_chiave()
        s = b.get("/api/login/nostr/sfida").json()["sfida"]
        b.post("/api/me/npub/collega-firma",
               json={"evento": firma_login(sk, s, "http://testserver")})
        b.post("/api/me/npub/disabilita-accesso")
        return b, sk

    def chiedi_biglietto(sk):
        """Un altro browser entra con la chiave: il server propone di
        collegarla all'account Telegram, e da' il biglietto."""
        b = TestClient(server.app)
        s = b.get("/api/login/nostr/sfida").json()["sfida"]
        d = b.post("/api/login/nostr", json={
            "evento": firma_login(sk, s, "http://testserver")}).json()
        return b, (d.get("collega") or {}).get("biglietto", "")

    # il gesto di sempre
    titolare, sk1 = account_col_badge(861)
    npub1 = server.hex_to_npub(pubblica_hex(sk1))
    prova("il banco: badge verificato, accesso libero", (npub1, 1, ""),
          riga(861))
    altro, biglietto = chiedi_biglietto(sk1)
    prova("chi entra con quella chiave riceve la proposta e il biglietto",
          True, len(biglietto) == 32)
    r = altro.post("/api/login/nostr/collega", json={"biglietto": biglietto})
    prova("IL SI' DI SEMPRE: collega ed entra",
          (200, {"ok": True, "collegato": True}), (r.status_code, r.json()))
    prova("...nell'account Telegram, con la chiave diventata d'accesso",
          (861, (npub1, 1, npub1)),
          (altro.get("/api/me").json()["tg_id"], riga(861)))
    r = altro.post("/api/login/nostr/collega", json={"biglietto": biglietto})
    prova("...e il biglietto resta monouso", 401, r.status_code)

    # il titolare TOGLIE la chiave mentre il biglietto e' in giro
    titolare, sk2 = account_col_badge(862)
    estraneo, biglietto = chiedi_biglietto(sk2)
    r = titolare.post("/api/me/npub", json={"npub": ""})
    prova("il titolare toglie la chiave dal profilo", (200, ("", 0, "")),
          (r.status_code, riga(862)))
    prima = sessioni_di(862)
    r = estraneo.post("/api/login/nostr/collega", json={"biglietto": biglietto})
    prova("CHIAVE TOLTA: il biglietto di prima non entra piu'",
          (401, "Invito scaduto: riprova il login"),
          (r.status_code, r.json().get("detail")))
    prova("...nessuna sessione nuova sull'account, nessun cookie",
          (prima, False),
          (sessioni_di(862), "barattolo_sessione" in estraneo.cookies))
    prova("...e la chiave NON e' tornata di nascosto come chiave d'accesso",
          ("", 0, ""), riga(862))

    # il titolare collega UN'ALTRA chiave mentre il biglietto e' in giro
    titolare, sk3 = account_col_badge(863)
    estraneo, biglietto = chiedi_biglietto(sk3)
    sk4 = nuova_chiave()
    npub4 = server.hex_to_npub(pubblica_hex(sk4))
    s = titolare.get("/api/login/nostr/sfida").json()["sfida"]
    r = titolare.post("/api/me/npub/collega-firma", json={
        "evento": firma_login(sk4, s, "http://testserver")})
    prova("il titolare collega un'altra chiave", (200, (npub4, 1, npub4)),
          (r.status_code, riga(863)))
    prima = sessioni_di(863)
    r = estraneo.post("/api/login/nostr/collega", json={"biglietto": biglietto})
    prova("UN'ALTRA CHIAVE NEL FRATTEMPO: il biglietto della vecchia non entra",
          401, r.status_code)
    prova("...nessuna sessione nuova, e la chiave d'accesso resta la nuova",
          (prima, (npub4, 1, npub4)), (sessioni_di(863), riga(863)))

    # ------------------------------------------------------------------
    # 3) IL RITORNO DEL WIDGET TELEGRAM
    # ------------------------------------------------------------------
    print("\n[il ritorno del widget Telegram]")
    leva_prima = server.LOGIN_DAL_BOT
    try:
        server.LOGIN_DAL_BOT = True
        w = TestClient(server.app, follow_redirects=False)
        prova("a leva accesa la pagina sa che la porta del bot c'e' (e il "
              "widget non lo disegna)", {"aperta": True},
              w.get("/api/login/bot").json())
        r = w.get("/api/login/telegram/ritorno", params=dati_widget(871))
        prova("A PORTA DEL BOT APERTA un ritorno FIRMATO BENE non apre "
              "niente: torna col segno del login non riuscito",
              (303, "/?accesso=no"),
              (r.status_code, r.headers.get("location")))
        con = server.db()
        nato = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id=871"
                           ).fetchone()[0]
        con.close()
        prova("...nessun cookie, nessun account nato, nessuna sessione",
              (False, 0, 0),
              ("barattolo_sessione" in r.headers.get("set-cookie", ""),
               nato, sessioni_di(871)))
        r = w.get("/api/login/telegram/ritorno",
                  params={**dati_widget(871), "da": "/negozio/ab12cd34"})
        prova("...e si torna alla pagina di partenza, col segno",
              "/negozio/ab12cd34?accesso=no", r.headers.get("location"))

        server.LOGIN_DAL_BOT = False
        w2 = TestClient(server.app, follow_redirects=False)
        prova("a leva spenta la porta del bot non c'e'", {"aperta": False},
              w2.get("/api/login/bot").json())
        r = w2.get("/api/login/telegram/ritorno", params=dati_widget(872))
        prova("A PORTA SPENTA il widget e' il login di ieri: 303 a casa",
              (303, "/"), (r.status_code, r.headers.get("location")))
        prova("...e si e' dentro, col proprio account", 872,
              w2.get("/api/me").json()["tg_id"])
        r = w2.get("/api/login/telegram/ritorno",
                   params={**dati_widget(873), "id": "874"})
        prova("...con la firma storta rifiutata come sempre",
              (303, "/?accesso=no"),
              (r.status_code, r.headers.get("location")))
    finally:
        server.LOGIN_DAL_BOT = leva_prima

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
