# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL GRUPPO DEGLI ADMIN (12 ott 2026, cantiere canale-admin).

`prove.py` fa girare la porta del gruppo con un trasporto finto in
memoria. Qui gira quel che le prove non vedono: il giro INTERO con
`_posta_gruppo_admin` e `bot_api` veri — httpx vero, JSON vero, il
codice HTTP vero — davanti a un TELEGRAM DI CARTONE che ascolta su
127.0.0.1 e risponde come risponde la Bot API: 200 col `message_id`,
403 al bot tolto dal gruppo, 400 «chat not found» all'id sbagliato,
400 «message thread not found» alla stanza cancellata, 400 «can't
parse entities» all'HTML rotto, 429 col `retry_after`. E il campanello
vero (`gestisci_update`) coi comandi scritti nel gruppo, `/dove`, e il
tocco su ✅ della revisione.

Le funzioni sono prese da server.py con `ast` (mai `import server`).
Di finto ci sono Telegram (il cartone), i timbri (un dizionario), il
database della revisione (una riga) e i comandi di servizio (rispondono
«fatto» con `bot_api`, come quelli veri). httpx e' quello vero con un
cartello stradale davanti: qualunque indirizzo chiami il server, la
richiesta arriva al cartone — stesso percorso, stesso corpo.

⚠️ NON SOSTITUISCE IL TELEGRAM VERO: le frasi degli errori qui le ho
scritte io, a memoria della Bot API. Che il Telegram vero dica proprio
«message thread not found» lo conferma solo il giro col bot vero, dopo
il push (il giudizio per questo cerca le parole, non la frase).

Uso:  python collaudo_canale_admin.py
"""
import ast
import asyncio
import contextvars
import html
import http.server
import json
import os
import re
import sys
import threading
import time
from urllib.parse import urlsplit

import httpx

QUI = os.path.dirname(os.path.abspath(__file__))
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


# ---------------- il Telegram di cartone ----------------------------
TOKEN = "123456:FINTO-di-cartone"
GRUPPO = -1001234567890
ALTRO_GRUPPO = -1009999999999
STANZE = {"dispute": 2, "liquidita": 4, "errori": 6, "moderazione": 8,
          "dm": 12, "riepiloghi": 14}
ANDREA, ALAN, ESTRANEO = 700000001, 700000002, 4242


class T:
    """Lo stato del cartone: cosa esiste, e cosa e' arrivato."""
    gruppi = {}
    piano = 0          # quante risposte 429 dare, da adesso
    arrivati = []      # (chat, stanza o None, metodo, corpo) — i consegnati
    bussate = []       # (metodo, chat) — ogni richiesta, consegnata o no
    token_visti = set()

    @classmethod
    def nuovo(cls):
        cls.gruppi = {GRUPPO: {"stanze": set(STANZE.values()), "bot": True},
                      ALTRO_GRUPPO: {"stanze": {3}, "bot": True}}
        cls.piano = 0
        cls.arrivati, cls.bussate = [], []


def _html_buono(testo):
    resto = re.sub(r"</?(b|i|u|s|code|pre)>|<a href=\"[^\"]*\">|</a>", "", testo)
    return "<" not in resto


def risposta_di_telegram(metodo, d):
    """(codice HTTP, corpo) come li darebbe la Bot API."""
    def no(codice, frase, **extra):
        return codice, dict({"ok": False, "error_code": codice,
                             "description": frase}, **extra)
    if metodo == "answerCallbackQuery":      # non ha una chat: e' un «ricevuto»
        return 200, {"ok": True, "result": True}
    chat = d.get("chat_id")
    T.bussate.append((metodo, chat))
    stanza = d.get("message_thread_id")
    if not (isinstance(chat, int) and chat > 0):
        g = T.gruppi.get(chat)
        if g is None:
            return no(400, "Bad Request: chat not found")
        if not g["bot"]:
            return no(403, "Forbidden: bot was kicked from the supergroup chat")
        if T.piano:
            T.piano -= 1
            return no(429, "Too Many Requests: retry after 7",
                      parameters={"retry_after": 7})
        if stanza is not None and stanza not in g["stanze"]:
            return no(400, "Bad Request: message thread not found")
    testo = d.get("text") or d.get("caption") or ""
    if d.get("parse_mode") == "HTML" and not _html_buono(testo):
        return no(400, "Bad Request: can't parse entities: Unsupported "
                       "start tag \"3\" at byte offset 14")
    T.arrivati.append((chat, stanza, metodo, d))
    return 200, {"ok": True, "result": {"message_id": len(T.arrivati)}}


class Cartone(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_POST(self):
        corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        m = re.fullmatch(r"/bot([^/]+)/(\w+)", self.path)
        if not m:
            codice, r = 404, {"ok": False, "error_code": 404,
                              "description": "Not Found"}
        else:
            T.token_visti.add(m.group(1))
            codice, r = risposta_di_telegram(m.group(2), json.loads(corpo or b"{}"))
        fuori = json.dumps(r).encode()
        self.send_response(codice)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(fuori)))
        self.end_headers()
        self.wfile.write(fuori)


class Deviato:
    """httpx vero, col cartello stradale: ogni POST va al cartone."""

    def __init__(self, base):
        self.base = base

    def AsyncClient(self, **k):
        vero, base = httpx.AsyncClient(**k), self.base

        class Cliente:
            async def __aenter__(self):
                await vero.__aenter__()
                return self

            async def __aexit__(self, *a):
                return await vero.__aexit__(*a)

            async def post(self, url, **kw):
                return await vero.post(base + urlsplit(url).path, **kw)
        return Cliente()


# ---------------- il server, coi pezzi veri -------------------------
class _Riga(dict):
    def __missing__(self, k):
        return ""


class _Con:
    def execute(self, *a):
        return self

    def fetchone(self):
        return _Riga(titolo="Bici da corsa", valuta="sats", prezzo_sats=90000,
                     venditore="Ada", venditore_id=222,
                     descrizione="telaio in acciaio")

    def close(self):
        pass


def monta(base, canale_id, argomenti, detto, timbri, fatti):
    """Un server in miniatura: le leve come le leggerebbe dal config."""
    i = SRC.index("ADMIN_ARGOMENTI = {")
    S = {"__name__": "collaudo", "asyncio": asyncio, "html": html, "json": json,
         "time": time, "contextvars": contextvars, "httpx": Deviato(base),
         "BOT_TOKEN": TOKEN, "MODALITA_COLLAUDO": False,
         "ADMIN_IDS": [ANDREA, ALAN], "URL_PUBBLICO": "https://barattolo.store",
         "LINK_LIBRO_P2P": "https://barattolo.store/p2p",
         "GUARDIANO_PONTE_AVVISA": [], "_finto_msg_id": 0,
         "_RISPOSTA_NEL_GRUPPO": contextvars.ContextVar("r", default=None),
         "print": lambda *a, **k: detto.append(" ".join(str(x) for x in a)),
         "timbro_letto": lambda n: timbri.get(n, ""),
         "timbro_scrivi": lambda n, v: timbri.__setitem__(n, v),
         "_link_dentro_telegram": lambda u: u,
         "spoglia_html": lambda t: html.unescape(re.sub(r"<[^>]+>", "", t)),
         "db": lambda: _Con(), "testo_prezzo": lambda *a: "90.000 sats",
         "riga_link_moderazione": lambda d: "",
         "upsert_utente": lambda u: None}
    exec(SRC[i:SRC.index("try:\n    from config import ADMIN_CANALE_ID", i)], S)
    for nome in ("_leggi_gruppo_admin", "gruppo_admin_id", "_posta_gruppo_admin",
                 "_giudizio_gruppo_admin", "_admin_in_privato",
                 "_gruppo_admin_giu", "_gruppo_admin_riprende",
                 "_al_gruppo_admin", "notifica_admin", "bot_api", "e_admin",
                 "e_admin_bot", "comando_dove", "_comando_nel_gruppo",
                 "gestisci_update", "gestisci_callback", "callback_revisione",
                 "avvisa_revisione", "_moderatori_p2p", "_avvisati_mod_p2p",
                 "_recapita_p2p", "_destinatari_ponte", "_avvisa_liquidita"):
        exec(pezzo(nome), S)
    gruppo, stanze, lamentele = S["_leggi_gruppo_admin"](canale_id, argomenti)
    S["_GRUPPO_ADMIN"] = {"id": gruppo, "stanze": stanze, "giu": None,
                          "piano_fino": 0.0}
    S["lamentele"] = lamentele

    # il privato: un messaggio del bot alla persona, col `bot_api` vero
    async def notifica(tg_id, testo, bottone=None):
        dati = {"chat_id": tg_id, "text": testo, "parse_mode": "HTML"}
        if bottone:
            dati["reply_markup"] = {"inline_keyboard": [[
                {"text": bottone[0], "url": bottone[1]}]]}
        r = await S["bot_api"]("sendMessage", dati)
        return "telegram ok" if (r or {}).get("ok") else "telegram NO"

    async def manda_telegram(tg_id, testo, bottone=None):
        return await notifica(tg_id, testo, bottone)

    def comando(nome):
        async def fa(mittente, testo):
            # come i comandi veri: a chi non e' admin la risposta di un
            # comando che non esiste. Nel gruppo non ci si deve ARRIVARE
            if not S["e_admin_bot"](mittente):
                return await S["_comando_sconosciuto"](mittente["id"])
            fatti.append((nome, testo))
            await S["bot_api"]("sendMessage", {
                "chat_id": mittente["id"], "text": f"✅ fatto: {nome}",
                "parse_mode": "HTML"})
        return fa

    async def decidi_revisione(annuncio_id, esito, admin_id):
        fatti.append(("decisione", annuncio_id, esito, admin_id))
        return True, f"✅ Annuncio #{annuncio_id} pubblicato"

    async def sconosciuto(chat):
        fatti.append(("sconosciuto", chat))

    S.update(notifica=notifica, _manda_telegram=manda_telegram,
             decidi_revisione=decidi_revisione, _comando_sconosciuto=sconosciuto)
    for nome in ("comando_anteprima", "comando_canale", "comando_sponsor",
                 "comando_vetrina", "comando_punti", "comando_canali"):
        S[nome] = comando(nome)
    return S


AVVISI = [("dispute", "⚠️ <b>Disputa aperta</b> sull'ordine #5."),
          ("liquidita", "⚠️ <b>Liquidità del nodo: c'è un problema</b>"),
          ("errori", "⚠️ <b>Pagamento in uscita FALLITO.</b> Ordine #5"),
          ("moderazione", "🆕 <b>Nuovo annuncio #7</b>"),
          ("dm", "📩 Nuovo DM su Nostr da Ada (npub1ada…zz)"),
          ("riepiloghi", "🛒 <b>Nuovo ordine:</b> «Bici»"),
          ("", "🔗 un avviso senza stanza")]


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Cartone)
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("\n[il gruppo degli admin, col Telegram di cartone]")

    def in_privato():
        return [(c, d["text"]) for c, _, _, d in T.arrivati
                if isinstance(c, int) and c > 0]

    def nel_gruppo(g=GRUPPO):
        return [(st, d.get("text") or d.get("caption")) for c, st, _, d
                in T.arrivati if c == g]

    def avvertimenti():
        return [c for c, t in in_privato() if "gruppo degli admin non riceve" in t]

    async def tutti(S):
        for stanza, testo in AVVISI:
            await S["notifica_admin"](testo, argomento=stanza)

    # --- 1. il conto: spento e acceso ---------------------------------
    T.nuovo()
    detto, timbri, fatti = [], {}, []
    spento = monta(base, 0, {}, detto, timbri, fatti)
    asyncio.run(tutti(spento))
    privato_di_ieri = sorted(in_privato())
    prova("leva spenta: ogni avviso a ogni admin, in privato; nel gruppo "
          "niente", (len(AVVISI) * 2, 0), (len(in_privato()), len(nel_gruppo())))
    T.nuovo()
    S = monta(base, GRUPPO, STANZE, detto, timbri, fatti)
    asyncio.run(tutti(S))
    prova("leva accesa: ogni avviso UNA volta nel gruppo, in privato "
          "niente", (len(AVVISI), 0), (len(nel_gruppo()), len(in_privato())))
    prova("IL CONTO, su Telegram: gli stessi avvisi con le stesse parole — "
          "cambia solo dove arrivano",
          sorted({t for _, t in privato_di_ieri}), sorted(t for _, t in nel_gruppo()))
    prova("...ognuno nella sua stanza, e quello senza stanza nel Generale",
          [(STANZE.get(s), t) for s, t in AVVISI], nel_gruppo())
    prova("...col token del bot nel percorso, e mai silenziosi",
          ({TOKEN}, True),
          (T.token_visti, all("disable_notification" not in d
                              for _, _, _, d in T.arrivati)))

    # --- 2. una stanza cancellata --------------------------------------
    T.nuovo()
    T.gruppi[GRUPPO]["stanze"].discard(STANZE["errori"])
    asyncio.run(S["notifica_admin"]("⚠️ pagamento", argomento="errori"))
    prova("stanza cancellata su Telegram: l'avviso arriva nel Generale, "
          "non in privato, e nessuno viene avvertito",
          ([(None, "⚠️ pagamento")], [], True),
          (nel_gruppo(), in_privato(),
           any("l'argomento «errori» non riceve" in r for r in detto)))

    # --- 3. il bot tolto dal gruppo ------------------------------------
    T.nuovo()
    T.gruppi[GRUPPO]["bot"] = False
    asyncio.run(tutti(S))
    prova("bot tolto dal gruppo: ogni avviso torna in privato a tutti e "
          "due, identico a leva spenta", privato_di_ieri,
          sorted(p for p in in_privato()
                 if "gruppo degli admin non riceve" not in p[1]))
    prova("...e lo si dice UNA volta a testa, non a ogni avviso",
          [ANDREA, ALAN], sorted(avvertimenti()))
    avv = next(t for _, t in in_privato() if "non riceve" in t)
    prova("...con la frase di Telegram, senza l'id del gruppo e senza il "
          "token", (True, False, False),
          ("bot was kicked from the supergroup chat" in avv,
           str(GRUPPO) in avv, TOKEN in avv))
    S["_GRUPPO_ADMIN"]["giu"] = None           # un deploy nel mezzo
    T.arrivati.clear()
    asyncio.run(S["notifica_admin"]("dopo il deploy", argomento="errori"))
    prova("dopo un riavvio, col bot ancora fuori: l'avviso arriva in "
          "privato e l'avvertimento non si ripete",
          (sorted([(ANDREA, "dopo il deploy"), (ALAN, "dopo il deploy")]), []),
          (sorted(in_privato()), avvertimenti()))
    T.gruppi[GRUPPO]["bot"] = True             # Andrea lo rimette
    T.arrivati.clear()
    asyncio.run(S["notifica_admin"]("bot rimesso", argomento="errori"))
    prova("bot rimesso nel gruppo: senza toccare niente gli avvisi "
          "tornano nel gruppo", ([(6, "bot rimesso")], [], ""),
          (nel_gruppo(), in_privato(), timbri.get("gruppo_admin_giu")))

    # --- 4. l'id sbagliato ---------------------------------------------
    T.nuovo()
    timbri.clear()
    storto = monta(base, -1005555555555, STANZE, detto, timbri, fatti)
    asyncio.run(storto["notifica_admin"]("⚠️ pagamento", argomento="errori"))
    prova("ADMIN_CANALE_ID di un gruppo che non esiste: l'avviso arriva in "
          "privato, e l'avvertimento dice «chat not found»",
          (2, True),
          (sum(1 for _, t in in_privato() if t == "⚠️ pagamento"),
           any("chat not found" in t for _, t in in_privato())))
    T.nuovo()
    persona = monta(base, ANDREA, STANZE, detto, timbri, fatti)
    asyncio.run(persona["notifica_admin"]("x", argomento="errori"))
    prova("ADMIN_CANALE_ID con l'id di una PERSONA: la leva non si accende "
          "(gli avvisi a tutti, in privato) e la lamentela lo dice",
          (0, sorted([(ANDREA, "x"), (ALAN, "x")]), 1),
          (persona["gruppo_admin_id"](), sorted(in_privato()),
           len(persona["lamentele"])))

    # --- 5. Telegram a briglia corta -----------------------------------
    T.nuovo()
    timbri.clear()
    S = monta(base, GRUPPO, STANZE, detto, timbri, fatti)
    T.piano = 1
    asyncio.run(S["notifica_admin"]("uno", argomento="errori"))
    asyncio.run(S["notifica_admin"]("due", argomento="errori"))
    prova("un 429 dal gruppo: i due avvisi arrivano in privato, il secondo "
          "non bussa nemmeno al gruppo, e nessuno dice che e' rotto",
          (4, 1, [], True),
          (len(in_privato()), sum(1 for m, c in T.bussate if c == GRUPPO),
           avvertimenti(), 0 < S["_GRUPPO_ADMIN"]["piano_fino"] - time.time() <= 7))
    S["_GRUPPO_ADMIN"]["piano_fino"] = 0.0     # i sette secondi sono passati
    asyncio.run(S["notifica_admin"]("tre", argomento="errori"))
    prova("...passata l'attesa, di nuovo nel gruppo", [(6, "tre")], nel_gruppo())

    # --- 6. l'HTML rotto -----------------------------------------------
    T.nuovo()
    asyncio.run(S["notifica_admin"]("🆕 <b>Tizio</b> scrive <3 a tutti",
                                    argomento="moderazione"))
    prova("un «<» storto nel testo: Telegram rifiuta l'HTML, e l'avviso "
          "arriva lo stesso nel gruppo, spoglio",
          ([(8, "🆕 Tizio scrive <3 a tutti")], []), (nel_gruppo(), in_privato()))

    # --- 7. le altre porte ---------------------------------------------
    T.nuovo()
    asyncio.run(S["avvisa_revisione"](7, "caso ambiguo"))
    tastiera = T.arrivati[0][3]["reply_markup"]["inline_keyboard"][0]
    prova("la revisione: UN messaggio nel gruppo, stanza «moderazione», "
          "coi bottoni ✅/❌", ((GRUPPO, 8), ["rev:ok:7", "rev:no:7"], 1),
          (T.arrivati[0][:2], [b["callback_data"] for b in tastiera],
           len(T.arrivati)))
    tocco = {"callback_query": {
        "id": "c1", "data": "rev:ok:7", "from": {"id": ESTRANEO},
        "message": {"message_id": 1, "chat": {"id": GRUPPO, "type": "supergroup"}}}}
    fatti.clear()
    asyncio.run(S["gestisci_update"](tocco))
    prova("il tocco su ✅ di chi NON e' admin (ma e' nel gruppo): non "
          "decide niente", [], fatti)
    tocco["callback_query"]["from"]["id"] = ALAN
    asyncio.run(S["gestisci_update"](tocco))
    prova("il tocco su ✅ di un admin: decide, e il messaggio del gruppo "
          "cambia sotto gli occhi di tutti",
          ([("decisione", 7, "pubblica", ALAN)],
           (GRUPPO, "editMessageText", "✅ Annuncio #7 pubblicato")),
          (fatti, (T.arrivati[-1][0], T.arrivati[-1][2], T.arrivati[-1][3]["text"])))
    T.nuovo()
    asyncio.run(S["_avvisa_liquidita"]("⚠️ <b>Liquidità del nodo</b>"))
    for mod in S["_avvisati_mod_p2p"]():
        asyncio.run(S["_recapita_p2p"](mod, "⚖️ <b>Disputa P2P aperta</b>"))
    asyncio.run(S["_recapita_p2p"](ESTRANEO, "il tuo scambio"))
    prova("la liquidita' e le dispute P2P: una volta sola, ognuna nella "
          "sua stanza; l'avviso a una parte dello scambio resta suo, in "
          "privato",
          ([(4, "⚠️ <b>Liquidità del nodo</b>"), (2, "⚖️ <b>Disputa P2P aperta</b>")],
           [(ESTRANEO, "il tuo scambio")]), (nel_gruppo(), in_privato()))

    # --- 8. i comandi nel gruppo ---------------------------------------
    def scrive(testo, chi=ANDREA, chat=GRUPPO, stanza=14, tipo="supergroup",
               bot=False):
        msg = {"message_id": 9, "text": testo,
               "from": {"id": chi, "is_bot": bot, "first_name": "X"},
               "chat": {"id": chat, "type": tipo,
                        "is_forum": tipo == "supergroup"}}
        if stanza:
            msg.update(message_thread_id=stanza, is_topic_message=True)
        T.arrivati.clear()
        fatti.clear()
        asyncio.run(S["gestisci_update"]({"update_id": 1, "message": msg}))
        return list(fatti), [(c, st, d["text"]) for c, st, _, d in T.arrivati]

    prova("Andrea scrive /canali nella stanza dei riepiloghi: il comando "
          "gira e la risposta esce lì, nel gruppo",
          ([("comando_canali", "/canali")],
           [(GRUPPO, 14, "✅ fatto: comando_canali")]), scrive("/canali"))
    prova("Alan scrive /sponsor@ilbarattolobot dal Generale: gira, e "
          "risponde nel Generale",
          ([("comando_sponsor", "/sponsor@ilbarattolobot negozio 7")],
           [(GRUPPO, None, "✅ fatto: comando_sponsor")]),
          scrive("/sponsor@ilbarattolobot negozio 7", chi=ALAN, stanza=0))
    prova("un estraneo invitato nel gruppo scrive /canali: niente, nemmeno "
          "una risposta", ([], []), scrive("/canali", chi=ESTRANEO))
    prova("un admin «anonimo» (Telegram lo presenta come un bot): niente",
          ([], []), scrive("/canali", chi=1087968824, bot=True))
    prova("Andrea scrive /canali in un ALTRO gruppo dove c'e' il bot: "
          "niente", ([], []), scrive("/canali", chat=ALTRO_GRUPPO))
    prova("due chiacchiere nel gruppo, /start e /sfoglia: il bot tace",
          [([], [])] * 3,
          [scrive("domani chi guarda le dispute?"), scrive("/start"),
           scrive("/sfoglia")])
    prova("in privato i comandi restano quelli di ieri, e rispondono in "
          "privato", ([("comando_canali", "/canali")],
                      [(ANDREA, None, "✅ fatto: comando_canali")]),
          scrive("/canali", chat=ANDREA, stanza=0, tipo="private"))
    f, u = scrive("/dove", stanza=12)
    prova("/dove nella stanza dei DM: i due numeri da scrivere nel config, "
          "e cosa arriva lì", (True, True, True, (GRUPPO, 12)),
          (f"Gruppo: <code>{GRUPPO}</code>" in u[0][2],
           "Argomento: <code>12</code>" in u[0][2],
           "Qui arrivano: 📩 DM Nostr." in u[0][2], u[0][:2]))
    f, u = scrive("/dove", chat=ALTRO_GRUPPO, stanza=3)
    prova("/dove in un gruppo non ancora scritto nel config: risponde lo "
          "stesso (serve a trovare il numero), senza il ✅",
          (True, False, (ALTRO_GRUPPO, 3)),
          (f"Gruppo: <code>{ALTRO_GRUPPO}</code>" in u[0][2], "✅" in u[0][2],
           u[0][:2]))
    prova("/dove da un estraneo, nel gruppo: silenzio", ([], []),
          scrive("/dove", chi=ESTRANEO))

    # --- 9. il journal -------------------------------------------------
    prova("nel journal mai il token del bot", False,
          any(TOKEN in r for r in detto))
    print("  --- le righe del journal, per chi legge ---")
    for r in dict.fromkeys(detto):
        print("    " + r[:150])

    srv.shutdown()
    srv.server_close()
    print(f"\n  {PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
