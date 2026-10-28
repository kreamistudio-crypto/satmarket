# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ASSISTENTE DEL BOT (28 ott 2026, cantiere bot-assistente).

Chi scrive una frase al bot, a leva accesa, riceve la risposta di un
assistente automatico (Claude via API), presentato come tale, con sotto
il bottone «🙋 Parla con una persona». `prove.py` difende i pezzi uno
per uno; qui il giro VERO: il campanello del webhook suonato a mano con
gli update che manderebbe Telegram, il server vero, `bot_api` che si
segna cosa avrebbe detto, `notifica_admin` che si segna l'avviso, e al
posto di Anthropic un client di cartone che si segna la richiesta.

Le domande a cui risponde:

  · A LEVA SPENTA il bot e' quello di ieri: stesso benvenuto, stessa
    risposta a una frase, nessuna chiamata;
  · A LEVA ACCESA E SOLO-MODERATORI (di serie) risponde solo agli
    admin; gli altri hanno il bot di ieri;
  · APERTA A TUTTI: la presentazione alla prima risposta, il bottone
    sotto ogni risposta, la riga nel /start;
  · LA RICHIESTA che parte verso Anthropic non porta chi scrive: niente
    tg id, niente nome; nessuno strumento; il libro in cache;
  · UN COMANDO e UN GRUPPO non vanno all'assistente;
  · IL CAMPANELLO risponde 200 anche se Anthropic esplode, e la
    chiamata parte quando il campanello ha gia' finito;
  · «🙋 Parla con una persona»: i moderatori avvisati con l'ultima
    domanda, nell'argomento «assistenza», e chi chiede riceve la porta
    privata; anche a leva spenta;
  · IL PANNELLO DELLE LEVE mostra il gruppo, e della chiave dice solo
    se c'e'.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna chiave, nessuna rete, nessun Telegram,
nessuna chiamata ad Anthropic.

USO:  python collaudo_assistente_bot.py
"""

import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
DETTI = []      # quel che il bot avrebbe spedito: (metodo, dati)
AVVISI = []     # quel che i moderatori avrebbero letto: (testo, argomento)
CHIESTE = []    # le richieste che sarebbero partite verso Anthropic
CLAUDE = {"testo": "Si paga in sats, con il deposito di garanzia.",
          "stop": "end_turn", "esplodi": False}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


class _Blocco:
    def __init__(self, testo):
        self.type, self.text = "text", testo


class _Uso:
    input_tokens, cache_read_input_tokens, output_tokens = 120, 9000, 40


class _Risposta:
    def __init__(self, testo, stop):
        self.content = [_Blocco(testo)] if testo else []
        self.stop_reason = stop
        self.usage = _Uso()


def avvio():
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-assistente-"),
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

    async def avviso_finto(testo, bottone=None, argomento=None, **kw):
        AVVISI.append((testo, argomento))
    server.bot_api = bot_finto
    server.notifica_admin = avviso_finto

    class _Messaggi:
        def create(self, **kw):
            # il campanello ha gia' finito? (il segnaposto e' stato
            # tolto: la chiamata gira nel lavoro DOPO la risposta)
            kw["_dopo_il_200"] = server._DOPO_LA_RISPOSTA.get() is None
            CHIESTE.append(kw)
            if CLAUDE["esplodi"]:
                raise RuntimeError("anthropic e' giu'")
            return _Risposta(CLAUDE["testo"], CLAUDE["stop"])

    class _Cliente:
        messages = _Messaggi()
    server._cliente_assistente = lambda: _Cliente()
    return server


# ---------------- il telefono: gli update che manderebbe Telegram ----
CAMPANELLO = {"x-telegram-bot-api-secret-token": "collaudo"}
_UPD = [0]


def scrivi(tel, chi, testo, nome="Tizio", tipo="private"):
    """Una frase al bot da `chi`: torna (stato del campanello, i
    sendMessage del bot)."""
    _UPD[0] += 1
    DETTI.clear()
    chat = chi if tipo == "private" else -100777
    r = tel.post("/api/telegram/aggiornamenti", headers=CAMPANELLO, json={
        "update_id": _UPD[0], "message": {
            "message_id": _UPD[0],
            "from": {"id": chi, "is_bot": False, "first_name": nome,
                     "username": f"utente{chi}"},
            "chat": {"id": chat, "type": tipo},
            "text": testo}})
    return r.status_code, [d for m, d in DETTI if m == "sendMessage"]


def tocca(tel, chi, callback_data, nome="Tizio"):
    """Il tocco su un bottone della tastiera del bot, da `chi`."""
    _UPD[0] += 1
    DETTI.clear()
    r = tel.post("/api/telegram/aggiornamenti", headers=CAMPANELLO, json={
        "update_id": _UPD[0], "callback_query": {
            "id": f"cb{_UPD[0]}",
            "from": {"id": chi, "is_bot": False, "first_name": nome,
                     "username": f"utente{chi}"},
            "data": callback_data,
            "message": {"message_id": 1, "chat": {"id": chi}}}})
    return r.status_code, [d for m, d in DETTI if m == "sendMessage"]


def bottoni(msg):
    return [b.get("text") for riga in
            (msg.get("reply_markup") or {}).get("inline_keyboard", [])
            for b in riga]


def main():
    server = avvio()
    from fastapi.testclient import TestClient

    print("=" * 58)
    print("  IL COLLAUDO DELL'ASSISTENTE DEL BOT")
    print("=" * 58)
    tel = TestClient(server.app)      # Telegram che suona il campanello

    # ------------------------------------------------------------------
    print("\n[a leva spenta: il bot di ieri]")
    prova("la leva e' spenta di serie", False, server.ASSISTENTE_AI_ATTIVO)
    _, start_ieri = scrivi(tel, 4242424, "/start")
    prova("il /start non parla dell'assistente", False,
          "assistente" in start_ieri[0]["text"])
    st, m = scrivi(tel, 4242424, "come funziona il deposito di garanzia?")
    prova("una frase riceve la risposta di ieri", (200, True),
          (st, "Non sono un bot chiacchierone" in m[0]["text"]))
    prova("...e nessuna chiamata ad Anthropic", 0, len(CHIESTE))
    server.ASSISTENTE_AI_ATTIVO = True
    st, m = scrivi(tel, 999, "ciao")
    prova("accesa SENZA chiave: nemmeno a un admin", (0, True),
          (len(CHIESTE), "Non sono un bot chiacchierone" in m[0]["text"]))

    # ------------------------------------------------------------------
    print("\n[accesa, solo moderatori (di serie)]")
    setattr(server, "ASSISTENTE_API_KEY", "chiave-finta-del-collaudo")
    prova("solo-moderatori e' acceso di serie", True,
          server.ASSISTENTE_SOLO_MODERATORI)
    st, m = scrivi(tel, 4242424, "come funziona il deposito di garanzia?")
    prova("un utente qualunque ha ancora il bot di ieri", (0, True),
          (len(CHIESTE), "Non sono un bot chiacchierone" in m[0]["text"]))
    st, m = scrivi(tel, 999, "come funziona il deposito di garanzia?",
                   nome="Admin")
    prova("l'admin riceve la risposta dell'assistente", (200, 1, 1),
          (st, len(CHIESTE), len(m)))
    prova("...che si presenta come intelligenza artificiale", True,
          m[0]["text"].startswith(server.PRESENTAZIONE_ASSISTENTE)
          and "posso sbagliare" in m[0]["text"])
    prova("...col testo del modello", True, CLAUDE["testo"] in m[0]["text"])
    prova("...e sotto la porta per una persona", True,
          "🙋 Parla con una persona" in bottoni(m[0]))
    prova("...in testo semplice (niente parse_mode)", False,
          "parse_mode" in m[0])
    prova("la chiamata e' partita quando il campanello aveva finito", True,
          CHIESTE[-1]["_dopo_il_200"])

    # ------------------------------------------------------------------
    print("\n[aperta a tutti]")
    server.ASSISTENTE_SOLO_MODERATORI = False
    _, s = scrivi(tel, 4242424, "/start")
    prova("il /start dice che si puo' chiedere", True,
          "assistente automatico" in s[0]["text"])
    prova("...e il benvenuto di prima resta tutto, davanti", True,
          s[0]["text"].startswith(start_ieri[0]["text"]))
    CHIESTE.clear()
    st, m = scrivi(tel, 4242424, "quanto dura la fattura Lightning?",
                   nome="Gennarino")
    prova("un utente qualunque riceve la risposta", (200, 1, True),
          (st, len(CHIESTE), m[0]["text"].startswith(
              server.PRESENTAZIONE_ASSISTENTE)))
    rich = CHIESTE[-1]
    tutto = repr({k: v for k, v in rich.items() if k != "_dopo_il_200"})
    prova("la richiesta NON porta chi scrive (tg id, nome, username)",
          (False, False, False),
          ("4242424" in tutto, "Gennarino" in tutto, "utente4242424" in tutto))
    prova("...nessuno strumento: il modello puo' solo scrivere", False,
          "tools" in rich)
    prova("...il modello della leva", server.ASSISTENTE_MODELLO,
          rich["model"])
    prova("...il libro in cache nel primo blocco, i numeri nel secondo",
          ({"type": "ephemeral"}, True, True),
          (rich["system"][0].get("cache_control"),
           "LIBRO DEL SAPERE" in rich["system"][0]["text"],
           rich["system"][1]["text"].startswith("NUMERI DI OGGI")))
    prova("...e la domanda e' l'ultima battuta", "quanto dura la fattura "
          "Lightning?", rich["messages"][-1]["content"])
    st, m = scrivi(tel, 4242424, "e se scade?")
    prova("la seconda domanda porta la prima come memoria",
          ["user", "assistant", "user"],
          [x["role"] for x in CHIESTE[-1]["messages"]])
    prova("...e la presentazione non si ripete", False,
          m[0]["text"].startswith(server.PRESENTAZIONE_ASSISTENTE))

    # ------------------------------------------------------------------
    print("\n[quel che non va all'assistente]")
    CHIESTE.clear()
    st, m = scrivi(tel, 4242424, "/nonesiste")
    prova("un comando sconosciuto resta ai bottoni di ieri", (200, 0, True),
          (st, len(CHIESTE), "Non sono un bot chiacchierone" in m[0]["text"]))
    st, m = scrivi(tel, 4242424, "ciao a tutti", tipo="supergroup")
    prova("una frase in un gruppo non va all'assistente", (200, 0, 0),
          (st, len(CHIESTE), len(m)))

    # ------------------------------------------------------------------
    print("\n[quando Anthropic non risponde]")
    CLAUDE["esplodi"] = True
    st, m = scrivi(tel, 5151, "come vendo un oggetto?")
    prova("il campanello dice 200 lo stesso", 200, st)
    prova("...e chi ha scritto riceve una frase gentile col bottone",
          (True, True), ("non riesco a rispondere" in m[0]["text"],
                         "🙋 Parla con una persona" in bottoni(m[0])))
    CLAUDE["esplodi"] = False
    CLAUDE["stop"] = "refusal"
    st, m = scrivi(tel, 5151, "come vendo un oggetto?")
    prova("un rifiuto del modello passa a una persona", True,
          "non posso risponderti" in m[0]["text"])
    CLAUDE["stop"] = "end_turn"

    # ------------------------------------------------------------------
    print("\n[🙋 parla con una persona]")
    AVVISI.clear()
    st, m = tocca(tel, 4242424, server.CALLBACK_PERSONA, nome="Gennarino")
    prova("il tocco risponde 200", 200, st)
    prova("i moderatori avvisati una volta, nell'argomento «assistenza»",
          [("assistenza")], [a for _, a in AVVISI])
    prova("...con chi chiede e la sua ultima domanda", (True, True),
          ("utente4242424" in AVVISI[0][0], "e se scade?" in AVVISI[0][0]))
    prova("chi chiede riceve la porta privata di Barattolo",
          [{"text": "💬 Scrivi a Barattolo",
            "url": server.CONTATTO_PRIVATO}],
          m[0]["reply_markup"]["inline_keyboard"][0])
    st, m = tocca(tel, 4242424, server.CALLBACK_PERSONA, nome="Gennarino")
    prova("un secondo tocco ridà la porta ma non riavvisa i moderatori",
          (1, 1), (len(m), len(AVVISI)))
    server.ASSISTENTE_AI_ATTIVO = False
    AVVISI.clear()
    st, m = tocca(tel, 7777, server.CALLBACK_PERSONA)
    prova("a leva spenta il bottone gia' mandato funziona ancora", (1, 1),
          (len(m), len(AVVISI)))
    server.ASSISTENTE_AI_ATTIVO = True

    # ------------------------------------------------------------------
    print("\n[il pannello delle leve]")
    adm = TestClient(server.app)
    r = adm.get("/api/admin/leve",
                headers={"X-Tg-Init-Data": "collaudo:999:Admin"})
    gruppo = [g for g in r.json()["gruppi"]
              if g["gruppo"] == "🤖 Assistente del bot"]
    prova("il gruppo dell'assistente c'e'", (200, 1),
          (r.status_code, len(gruppo)))
    prova("...e la chiave non esce mai dal pannello", False,
          "chiave-finta-del-collaudo" in r.text)
    voci = {v.get("chiave"): v for v in gruppo[0]["voci"]}
    prova("...l'interruttore si gira dal pannello, la chiave no",
          (True, False),
          (bool(voci["ASSISTENTE_AI_ATTIVO"].get("scrivibile")),
           bool(voci["ASSISTENTE_API_KEY"].get("scrivibile"))))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
