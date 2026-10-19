# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «ENTRA DAL BOT» (19 ott 2026, cantiere account-doppio-bot).

Il guasto: due account Telegram sullo stesso telefono, e il widget sul
web entrava sempre col primo. La cura: si entra passando dal bot, cosi'
entra l'account che ha premuto Avvia. `prove.py` difende la forma; qui
il giro VERO, con le richieste vere (TestClient = un browser che tiene
i cookie) e il bot simulato — il campanello del webhook suonato a mano
con gli update che manderebbe Telegram, e `bot_api` che invece di
spedire si segna cosa avrebbe detto.

Le domande a cui risponde:

  · A LEVA SPENTA la porta non c'e' (e il client tiene il widget);
  · IL GIRO INTERO: il browser chiede, il bot riceve /start, mostra il
    NOME e tre figure, la figura giusta apre la sessione — e la apre
    solo al browser che l'ha chiesta;
  · DUE TELEGRAM SULLO STESSO TELEFONO: entra quello che ha premuto
    Avvia, e restano aperti tutt'e due, con lo switch di sempre;
  · IL LINK INOLTRATO: chi lo riceve non sa la figura, e uno sbaglio
    annulla tutto; un altro Telegram che arriva dopo trova il link
    gia' usato e non puo' confermare; un browser senza il legame non
    incassa niente;
  · MONOUSO E A SCADENZA: il link si brucia all'Avvia, un ingresso
    nuovo brucia il vecchio, uno scaduto non entra;
  · IL TETTO e IL RIENTRO sono quelli di ogni login: al tetto esce il
    piu' vecchio e la sua sessione si chiude nel database; chi rientra
    chiude la sua vecchia;
  · DENTRO LA MINI APP la porta non serve: si e' gia' dentro.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna chiave, nessuna rete, nessun Telegram.

USO:  python collaudo_login_bot.py
"""

import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
DETTI = []      # quel che il bot avrebbe spedito: (metodo, dati)


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-login-bot-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    # I segreti si posano col setattr e mai come `NOME = "valore"`:
    # quella e' la forma di un file di configurazione, e lo scanner
    # della CI non puo' distinguere una chiave finta da una vera.
    for k, v in (("BOT_TOKEN", "0:collaudo"),
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
                 ("MAX_ACCOUNT_BROWSER", 3),
                 ("LOGIN_DAL_BOT", False),
                 ("MOSTRO_RELAY", "ws://127.0.0.1:9"),
                 ("MOSTRO_RELAY_SPECCHIO", "ws://127.0.0.1:9"),
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server

    async def bot_finto(metodo, dati):
        """Il bot non parla con Telegram: si segna cosa avrebbe detto."""
        DETTI.append((metodo, dati))
        return {"ok": True}
    server.bot_api = bot_finto
    return server


# ---------------- il telefono: gli update che manderebbe Telegram ----
CAMPANELLO = {"x-telegram-bot-api-secret-token": "collaudo"}
_UPD = [0]


def avvia_bot(tel, chi, nome, carico, username=""):
    """Il tocco su Avvia: Telegram manda «/start CARICO» da `chi`."""
    _UPD[0] += 1
    mitt = {"id": chi, "is_bot": False, "first_name": nome}
    if username:
        mitt["username"] = username
    DETTI.clear()
    tel.post("/api/telegram/aggiornamenti", headers=CAMPANELLO, json={
        "update_id": _UPD[0], "message": {
            "message_id": _UPD[0], "from": mitt,
            "chat": {"id": chi, "type": "private"},
            "text": f"/start {carico}"}})
    return [d for m, d in DETTI if m == "sendMessage"]


def tocca(tel, chi, callback_data):
    """Il tocco su un bottone della tastiera del bot, da `chi`."""
    _UPD[0] += 1
    DETTI.clear()
    tel.post("/api/telegram/aggiornamenti", headers=CAMPANELLO, json={
        "update_id": _UPD[0], "callback_query": {
            "id": f"cb{_UPD[0]}", "from": {"id": chi, "is_bot": False},
            "data": callback_data,
            "message": {"message_id": 1, "chat": {"id": chi}}}})
    return " ".join(d.get("text", "") for m, d in DETTI
                    if m == "editMessageText")


def carico_dal_link(link):
    return link.split("?start=", 1)[1]


def figure_della_tastiera(msg):
    """Le tre figure e il «non sono io», come (testo, callback_data)."""
    righe = msg["reply_markup"]["inline_keyboard"]
    return ([(b["text"], b["callback_data"]) for b in righe[0]],
            righe[1][0]["callback_data"])


def entra(server, w, tel, chi, nome, username=""):
    """Il giro intero, da chi sa la figura: torna (risposta di stato,
    testo del bot dopo il tocco)."""
    d = w.post("/api/login/bot/inizia").json()
    msg = avvia_bot(tel, chi, nome, carico_dal_link(d["link"]), username)[0]
    figure, _ = figure_della_tastiera(msg)
    giusta = [cb for f, cb in figure if f == d["figura"]][0]
    detto = tocca(tel, chi, giusta)
    return w.post("/api/login/bot/stato").json(), detto


def main():
    server = avvio()
    from fastapi.testclient import TestClient

    print("=" * 58)
    print("  IL COLLAUDO DI «ENTRA DAL BOT»")
    print("=" * 58)
    tel = TestClient(server.app)      # Telegram che suona il campanello

    # ------------------------------------------------------------------
    print("\n[a leva spenta]")
    w0 = TestClient(server.app)
    prova("la porta non c'e': il client tiene il widget", {"aperta": False},
          w0.get("/api/login/bot").json())
    prova("chiedere un ingresso e' un 404", 404,
          w0.post("/api/login/bot/inizia").status_code)
    prova("...e bussare anche", 404,
          w0.post("/api/login/bot/stato").status_code)

    # ------------------------------------------------------------------
    print("\n[il giro intero]")
    server.LOGIN_DAL_BOT = True
    w = TestClient(server.app)        # il browser di Andrea
    prova("a leva accesa la porta c'e'", {"aperta": True},
          w.get("/api/login/bot").json())
    r = w.post("/api/login/bot/inizia")
    d = r.json()
    prova("l'ingresso nasce", 200, r.status_code)
    prova("...col link del bot e il prefisso suo", True,
          d["link"].startswith(server.LINK_BOT + "?start=entra_"))
    prova("...una figura da cercare", True,
          d["figura"] in server.FIGURE_INGRESSO)
    prova("...e due minuti di tempo", 120, d["valida_secondi"])
    prova("il LEGAME sta in un cookie del browser...", True,
          bool(w.cookies.get("barattolo_ingresso")))
    prova("...HttpOnly, e solo sulle rotte della porta", True,
          "httponly" in r.headers["set-cookie"].lower()
          and "path=/api/login/bot" in r.headers["set-cookie"].lower())
    prova("...e non sta nella risposta", False,
          w.cookies.get("barattolo_ingresso") in r.text)
    prova("prima dell'Avvia si aspetta", {"stato": "attesa"},
          w.post("/api/login/bot/stato").json())
    prova("...e nessuno e' ancora entrato", 401, w.get("/api/me").status_code)

    msgs = avvia_bot(tel, 501, "Andrea", carico_dal_link(d["link"]), "andrea")
    prova("all'Avvia il bot risponde una volta", 1, len(msgs))
    testo = msgs[0]["text"]
    prova("...col NOME dell'account che ha premuto Avvia", True,
          "Andrea" in testo and "@andrea" in testo)
    prova("...e da dove viene la richiesta", True, "Te lo chiede un" in testo)
    figure, no = figure_della_tastiera(msgs[0])
    prova("tre figure, fra cui quella della pagina", (3, True),
          (len(figure), d["figura"] in [f for f, _ in figure]))
    prova("...tre DIVERSE (una sola e' giusta)", 3,
          len({f for f, _ in figure}))
    prova("...e il «non sono stato io»", True, no.endswith(":x"))
    prova("il CODICE non viaggia nella tastiera", False,
          carico_dal_link(d["link"])[6:] in str(msgs[0]["reply_markup"]))
    prova("dopo l'Avvia la pagina lo sa", {"stato": "in_chat"},
          w.post("/api/login/bot/stato").json())

    # chi arriva dopo con lo stesso link (inoltrato, o il QR fotografato)
    altri = avvia_bot(tel, 502, "Intruso", carico_dal_link(d["link"]))
    prova("il link e' MONOUSO: un altro Telegram lo trova gia' usato", True,
          "scaduto o è già stato usato" in altri[0]["text"]
          and "reply_markup" not in altri[0])
    giusta = [cb for f, cb in figure if f == d["figura"]][0]
    prova("...e la tastiera non vale per un altro Telegram", True,
          "scaduto" in tocca(tel, 502, giusta))
    prova("...che non ha toccato niente: si aspetta ancora",
          {"stato": "in_chat"}, w.post("/api/login/bot/stato").json())
    ladro = TestClient(server.app)
    prova("un browser SENZA il legame non incassa niente",
          {"stato": "scaduto"}, ladro.post("/api/login/bot/stato").json())
    prova("...e non ha nessuna sessione", False,
          "barattolo_sessione" in ladro.cookies)

    detto = tocca(tel, 501, giusta)
    prova("la figura giusta: il bot dice fatto, col nome", True,
          "Fatto" in detto and "Andrea" in detto)
    prova("un secondo tocco non conta piu'", True,
          "scaduto" in tocca(tel, 501, giusta))
    prova("il browser che l'ha chiesto entra", {"stato": "dentro",
          "nome": "Andrea"}, w.post("/api/login/bot/stato").json())
    prova("...e da li' /api/me e' Andrea", 501, w.get("/api/me").json()["tg_id"])
    prova("...il legame se n'e' andato", None,
          w.cookies.get("barattolo_ingresso"))
    prova("...e bussare di nuovo non riapre niente", {"stato": "scaduto"},
          w.post("/api/login/bot/stato").json())
    vecchia_andrea = w.cookies.get("barattolo_sessione")

    # ------------------------------------------------------------------
    print("\n[due Telegram sullo stesso telefono]")
    # nell'app di Telegram Andrea passa al secondo account, e tocca di
    # nuovo «Entra con Telegram» sul web: entra QUELLO, non il primo
    s, _ = entra(server, w, tel, 503, "Negozio", "negozio_andrea")
    prova("entra l'account che ha premuto Avvia", {"stato": "dentro",
          "nome": "Negozio"}, s)
    prova("...e /api/me e' lui", 503, w.get("/api/me").json()["tg_id"])
    ss = w.get("/api/sessioni").json()
    prova("restano aperti TUTT'E DUE, nell'ordine d'ingresso",
          ["501", "503"], [c["id"] for c in ss["conti"]])
    prova("...l'attivo e' l'ultimo entrato", "503", ss["attivo_id"])
    prova("...e il token non esce", False, "token" in str(ss))
    prova("un tocco e si torna al primo", 200,
          w.post("/api/sessioni/attiva", json={"tg_id": 501}).status_code)
    prova("...e /api/me e' di nuovo Andrea", 501,
          w.get("/api/me").json()["tg_id"])

    # ------------------------------------------------------------------
    print("\n[il link inoltrato, la figura sbagliata, il no]")
    n_prima = len(w.get("/api/sessioni").json()["conti"])
    furbo = TestClient(server.app)     # chi manda il SUO link a un altro
    d = furbo.post("/api/login/bot/inizia").json()
    msg = avvia_bot(tel, 504, "Vittima", carico_dal_link(d["link"]))[0]
    figure, no = figure_della_tastiera(msg)
    sbagliata = [cb for f, cb in figure if f != d["figura"]][0]
    prova("la figura sbagliata annulla, e il bot lo dice", True,
          "Figura sbagliata" in tocca(tel, 504, sbagliata))
    prova("...e la giusta, dopo, non vale piu'", True, "scaduto" in tocca(
        tel, 504, [cb for f, cb in figure if f == d["figura"]][0]))
    prova("il browser di chi aveva inoltrato: annullato",
          {"stato": "annullato"}, furbo.post("/api/login/bot/stato").json())
    prova("...e NON e' entrato nell'account dell'altro", 401,
          furbo.get("/api/me").status_code)
    d = furbo.post("/api/login/bot/inizia").json()
    msg = avvia_bot(tel, 504, "Vittima", carico_dal_link(d["link"]))[0]
    _, no = figure_della_tastiera(msg)
    prova("«Non sono stato io» annulla", True,
          "nessuno è entrato" in tocca(tel, 504, no))
    prova("...e il browser lo sa", {"stato": "annullato"},
          furbo.post("/api/login/bot/stato").json())
    prova("il browser di Andrea non e' stato toccato", n_prima,
          len(w.get("/api/sessioni").json()["conti"]))

    # ------------------------------------------------------------------
    print("\n[monouso e scadenza]")
    b = TestClient(server.app)
    d1 = b.post("/api/login/bot/inizia").json()
    d2 = b.post("/api/login/bot/inizia").json()
    prova("un ingresso nuovo brucia il vecchio: il primo link e' morto", True,
          "scaduto" in avvia_bot(tel, 505, "Zia", carico_dal_link(d1["link"]))[0]["text"])
    prova("...il secondo vale", True, "reply_markup" in avvia_bot(
        tel, 505, "Zia", carico_dal_link(d2["link"]))[0])
    prova("...e c'e' un solo ingresso vivo per quel browser", 1, sum(
        1 for v in server.INGRESSI_BOT.values() if v["tg_id"] == 505))
    for v in server.INGRESSI_BOT.values():
        if v["tg_id"] == 505:
            v["scade"] = 1          # il tempo e' passato
    prova("scaduto, il browser non entra", {"stato": "scaduto"},
          b.post("/api/login/bot/stato").json())
    prova("...e non ha sessioni", 401, b.get("/api/me").status_code)
    d = b.post("/api/login/bot/inizia").json()
    for v in server.INGRESSI_BOT.values():
        if v["tg_id"] is None and v["figura"] == d["figura"]:
            v["scade"] = 1
    prova("un link scaduto, all'Avvia, lo dice", True, "scaduto" in avvia_bot(
        tel, 505, "Zia", carico_dal_link(d["link"]))[0]["text"])
    prova("un codice inventato: lo stesso", True, "scaduto" in avvia_bot(
        tel, 505, "Zia", "entra_" + "A" * 22)[0]["text"])
    prova("un codice storto: lo stesso, senza fermare il bot", True,
          "scaduto" in avvia_bot(tel, 505, "Zia", "entra_<b>x")[0]["text"])
    prova("l'/start nudo resta il benvenuto di sempre", True,
          "benvenuto" in avvia_bot(tel, 505, "Zia", "")[0]["text"].lower())

    # ------------------------------------------------------------------
    print("\n[il tetto e il rientro: le regole di ogni login]")
    # Il tetto del collaudo e' 3: Andrea e Negozio, piu' uno fa 3...
    s, _ = entra(server, w, tel, 506, "Terzo")
    prova("il terzo entra", "dentro", s["stato"])
    prova("...e sono in tre", ["501", "503", "506"],
          [c["id"] for c in w.get("/api/sessioni").json()["conti"]])
    # ...e il quarto, oltre il tetto, fa uscire il piu' vecchio
    altro = TestClient(server.app)
    altro.cookies.set("barattolo_sessione", vecchia_andrea)
    prova("(la sessione di Andrea copiata altrove vale, prima)", 501,
          altro.get("/api/me").json()["tg_id"])
    s, _ = entra(server, w, tel, 507, "Quarto")
    prova("oltre il tetto si entra lo stesso", "dentro", s["stato"])
    prova("...esce il piu' VECCHIO, mai quello appena entrato",
          ["503", "506", "507"],
          [c["id"] for c in w.get("/api/sessioni").json()["conti"]])
    prova("...e la sua sessione si chiude nel DATABASE", 401,
          altro.get("/api/me").status_code)
    copia_neg = TestClient(server.app)
    w.post("/api/sessioni/attiva", json={"tg_id": 503})
    copia_neg.cookies.set("barattolo_sessione", w.cookies.get("barattolo_sessione"))
    prova("(la sessione di Negozio copiata altrove vale, prima)", 503,
          copia_neg.get("/api/me").json()["tg_id"])
    s, _ = entra(server, w, tel, 503, "Negozio")
    prova("il RIENTRO dal bot riesce", "dentro", s["stato"])
    prova("...senza doppioni", ["506", "507", "503"],
          [c["id"] for c in w.get("/api/sessioni").json()["conti"]])
    prova("...e la vecchia sessione di Negozio e' chiusa", 401,
          copia_neg.get("/api/me").status_code)

    # ------------------------------------------------------------------
    print("\n[dentro la Mini App]")
    m = TestClient(server.app)
    prova("dentro Telegram la porta non serve: 400", 400, m.post(
        "/api/login/bot/inizia",
        headers={"X-Tg-Init-Data": "collaudo:600:Tele"}).status_code)

    # ------------------------------------------------------------------
    print("\n[da onion]")
    o = TestClient(server.app, base_url="http://barattoloxyz.onion")
    r = o.post("/api/login/bot/inizia")
    prova("anche da Tor l'ingresso nasce", 200, r.status_code)
    s, _ = (lambda d: (avvia_bot(tel, 811, "DaTor", carico_dal_link(d["link"])), d))(r.json())
    figure, _ = figure_della_tastiera(s[0])
    tocca(tel, 811, [cb for f, cb in figure if f == r.json()["figura"]][0])
    prova("...e il browser di Tor entra col Telegram che ha premuto Avvia",
          {"stato": "dentro", "nome": "DaTor"}, o.post("/api/login/bot/stato").json())
    prova("...e da li' /api/me e' lui", 811, o.get("/api/me").json()["tg_id"])

    # ------------------------------------------------------------------
    print("\n[la fusione Nostr→Telegram, dalla rotta async]")
    f = TestClient(server.app)
    f.post("/api/login/telegram", json={"collaudo": True, "id": -77, "first_name": "Nostrano"})
    con = server.db()
    con.execute("UPDATE utenti SET npub=?, npub_accesso=? WHERE tg_id=-77",
                ("npub1fintafusione", "npub1fintafusione"))
    con.commit()
    con.close()
    r = f.post("/api/me/collega-telegram")
    prova("il lasciapassare nasce dalla rotta (ora async)", (200, 32),
          (r.status_code, len(r.json().get("codice", ""))))
    vecchio = r.json()["codice"]
    r = f.post("/api/me/collega-telegram")
    prova("...chiederne un altro brucia il vecchio", (False, True),
          (vecchio in server.CODICI_FUSIONE, r.json()["codice"] in server.CODICI_FUSIONE))
    m = avvia_bot(tel, 812, "Tele", r.json()["codice"])
    prova("...e il bot lo riconosce: chiede la conferma della fusione", True,
          "Stai per collegare" in m[0]["text"] and "fondi:" in str(m[0]["reply_markup"]))

    # ------------------------------------------------------------------
    print("\n[a leva spenta di nuovo]")
    d = w.post("/api/login/bot/inizia").json()
    server.LOGIN_DAL_BOT = False
    prova("spegnere la leva chiude la porta anche a chi era in volo", 404,
          w.post("/api/login/bot/stato").status_code)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
