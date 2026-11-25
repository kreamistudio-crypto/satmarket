# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ASSISTENZA IN APP (3 nov 2026, richiesta di Andrea:
«una chat di assistenza dentro Barattolo, nelle impostazioni; le chat
accessibili a tutti gli admin e viste per utente»). Il SERVER VERO su un
database usa-e-getta:
  · a leva spenta le rotte non esistono (404), e /api/me non accende la voce;
  · l'utente scrive e rilegge la SUA conversazione, e solo quella;
  · un non-admin non legge l'elenco (403), un admin si';
  · l'elenco e' per utente, «da rispondere» finche' l'ultima parola e'
    dell'utente;
  · la risposta dello staff arriva all'utente come «Staff», senza il nome
    dell'admin, e l'avviso parte SENZA il testo;
  · il pallino delle risposte nuove si accende e si spegne;
  · il testo resta testo (niente HTML costruito dal server), vuoto e troppo
    lungo sono un 400, il freno morde al 21° messaggio dell'ora;
  · IL PASSO 2 (5 nov 2026): un messaggio avvisa ogni admin (con `notifica`,
    cioe' il suo canale), col testo SCAPPATO e il tasto alla conversazione;
    un secondo messaggio entro dieci minuti non riavvisa; la risposta di un
    admin azzera la pausa; i link dei tasti si traducono per Telegram.
  · GLI SCREENSHOT (17 nov 2026): fino a tre per messaggio, anche senza
    testo; il tipo dai byte, i metadati via, cifrati sul disco; li legge
    solo chi li ha mandati e gli admin (agli altri un 404 uguale per
    tutti); agli admin arrivano nel bot anche dentro la pausa; con
    l'account cancellato se ne vanno anche i file. Dalla sera del 17 nov
    anche lo staff risponde con uno screenshot, che l'utente apre.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco,
e `notifica` e' sostituita da un registro.

USO:  python collaudo_assistenza.py
"""

import sys

import collaudo_lnbits_muto as banco

prova = banco.prova

COMPRA = {"X-Tg-Init-Data": "collaudo:111:Compratore"}
VENDE = {"X-Tg-Init-Data": "collaudo:222:Venditore"}
ADMIN = {"X-Tg-Init-Data": "collaudo:999:Admin"}


def main():
    print("=" * 58)
    print("  L'ASSISTENZA IN APP — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    S._SECCHI.clear()
    avvisi = []
    import asyncio

    def aspetta_sottofondo():
        # l'avviso agli admin parte con create_task: il TestClient ha il
        # suo loop, e un giro di richiesta in piu' lo lascia finire
        c.get("/api/salute")

    async def registra(tg_id, testo, bottone=None):
        avvisi.append((tg_id, testo, bottone))
        return "registrato"
    S.notifica = registra

    con = S.db()
    for tg, nome in ((111, "Compratore"), (222, "Venditore"), (999, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
                    "VALUES(?,?,?,1)", (tg, nome, f"neg{tg}"))
    con.execute("DELETE FROM assistenza")
    con.execute("DELETE FROM assistenza_letture")
    con.commit()
    con.close()

    print("\n[a leva spenta l'assistenza non esiste]")
    S.ASSISTENZA_ATTIVA = False
    prova("GET /api/assistenza e' un 404", 404, c.get("/api/assistenza", headers=COMPRA).status_code)
    prova("POST /api/assistenza e' un 404", 404,
          c.post("/api/assistenza", json={"testo": "ciao"}, headers=COMPRA).status_code)
    prova("l'elenco degli admin e' un 404 anche per l'admin", 404,
          c.get("/api/admin/assistenza", headers=ADMIN).status_code)
    prova("...e /api/me dice assistenza: false", False,
          c.get("/api/me", headers=COMPRA).json().get("assistenza"))

    S.ASSISTENZA_ATTIVA = True
    print("\n[l'utente scrive allo staff]")
    prova("/api/me accende la voce, senza risposte nuove", (True, 0),
          (c.get("/api/me", headers=COMPRA).json().get("assistenza"),
           c.get("/api/me", headers=COMPRA).json().get("assistenza_nuove")))
    r = c.get("/api/assistenza", headers=COMPRA)
    prova("la conversazione vuota si apre", (200, []), (r.status_code, r.json().get("messaggi")))
    furbo = "<img src=x onerror=alert(1)> il mio ordine 12 non arriva"
    r = c.post("/api/assistenza", json={"testo": "  " + furbo + "\x00  "}, headers=COMPRA)
    prova("il messaggio entra", 200, r.status_code)
    prova("...com'e' scritto (spazi e caratteri di controllo tolti, HTML lasciato testo)",
          furbo, r.json()["messaggi"][-1]["testo"])
    prova("...e non e' dello staff", False, r.json()["messaggi"][-1]["staff"])
    aspetta_sottofondo()
    agli_admin = [a for a in avvisi if a[0] == 999]
    prova("PASSO 2: il primo messaggio avvisa l'admin, una volta", 1, len(agli_admin))
    prova("...col messaggio SCAPPATO dentro (niente tag vivi)", (True, False),
          ("&lt;img src=x onerror=alert(1)&gt;" in agli_admin[0][1],
           "<img" in agli_admin[0][1]))
    prova("...chi scrive e il suo numero", True,
          "Compratore" in agli_admin[0][1] and "(n. 111)" in agli_admin[0][1])
    prova("...e il tasto alla conversazione", S.URL_PUBBLICO + "/?assistenza=111",
          agli_admin[0][2][1])
    c.post("/api/assistenza", json={"testo": "Ci siete?"}, headers=COMPRA)
    aspetta_sottofondo()
    prova("un secondo messaggio entro dieci minuti NON riavvisa", 1,
          len([a for a in avvisi if a[0] == 999]))
    con = S.db()
    con.execute("UPDATE assistenza_avvisi SET quando=quando-? WHERE utente=111",
                (S.ASSISTENZA_AVVISO_PAUSA_S + 1,))
    con.commit()
    con.close()
    c.post("/api/assistenza", json={"testo": "Ancora io"}, headers=COMPRA)
    aspetta_sottofondo()
    prova("...passati i dieci minuti si'", 2, len([a for a in avvisi if a[0] == 999]))
    c.post("/api/assistenza", json={"testo": "Mi aiutate?"}, headers=VENDE)
    aspetta_sottofondo()
    prova("un'altra conversazione ha la sua pausa: avvisa subito", 3,
          len([a for a in avvisi if a[0] == 999]))
    prova("un messaggio vuoto e' un 400", 400,
          c.post("/api/assistenza", json={"testo": "   "}, headers=COMPRA).status_code)
    prova("uno troppo lungo e' un 400", 400,
          c.post("/api/assistenza", json={"testo": "x" * (S.ASSISTENZA_TESTO_MAX + 1)},
                 headers=COMPRA).status_code)
    prova("il venditore vede SOLO la sua conversazione", ["Mi aiutate?"],
          [m["testo"] for m in c.get("/api/assistenza", headers=VENDE).json()["messaggi"]])

    print("\n[l'elenco degli admin, per utente]")
    prova("un non-admin non legge l'elenco (403)", 403,
          c.get("/api/admin/assistenza", headers=COMPRA).status_code)
    prova("...ne' la conversazione di un altro (403)", 403,
          c.get("/api/admin/assistenza/222", headers=COMPRA).status_code)
    prova("...ne' risponde come staff (403)", 403,
          c.post("/api/admin/assistenza/222", json={"testo": "sono lo staff"},
                 headers=COMPRA).status_code)
    el = c.get("/api/admin/assistenza", headers=ADMIN).json()["conversazioni"]
    prova("due conversazioni, una per utente, l'ultima mossa prima (l'id come testo)",
          ["222", "111"],
          [x["utente"] for x in el])
    prova("...tutte e due da rispondere", [True, True], [x["da_rispondere"] for x in el])
    prova("...coi nomi", ["Venditore", "Compratore"], [x["nome"] for x in el])
    prova("...e i conti dei messaggi", [1, 3], [x["messaggi"] for x in el])

    print("\n[lo staff risponde]")
    r = c.post("/api/admin/assistenza/111", json={"testo": "Guardo subito l'ordine 12"},
               headers=ADMIN)
    prova("la risposta entra", 200, r.status_code)
    prova("...e per gli admin dice chi ha risposto", "Admin", r.json()["messaggi"][-1].get("chi"))
    prova("l'utente riceve UN avviso", 1, len([a for a in avvisi if a[0] == 111]))
    prova("...che NON porta il testo della risposta", False,
          "Guardo subito" in avvisi[-1][1])
    prova("...e il tasto porta alla SUA chat", S.URL_PUBBLICO + "/?assistenza=mia",
          avvisi[-1][2][1])
    el = c.get("/api/admin/assistenza", headers=ADMIN).json()["conversazioni"]
    prova("la conversazione del compratore torna in cima, non piu' da rispondere",
          ("111", False), (el[0]["utente"], el[0]["da_rispondere"]))
    gia = len([a for a in avvisi if a[0] == 999])
    c.post("/api/assistenza", json={"testo": "Grazie!"}, headers=COMPRA)
    aspetta_sottofondo()
    prova("dopo la risposta dello staff il messaggio nuovo riavvisa subito", gia + 1,
          len([a for a in avvisi if a[0] == 999]))
    prova("l'admin che scrive nella sua conversazione non avvisa se stesso", gia + 1,
          (c.post("/api/assistenza", json={"testo": "prova mia"}, headers=ADMIN),
           aspetta_sottofondo(), len([a for a in avvisi if a[0] == 999]))[2])

    print("\n[i tasti dentro Telegram]")
    vecchio = S.TELEGRAM_MINIAPP_LINK
    S.TELEGRAM_MINIAPP_LINK = "https://t.me/ilbarattolobot"
    prova("la propria chat e la conversazione, anche di un account Nostr",
          ["https://t.me/ilbarattolobot?startapp=assistenza",
           "https://t.me/ilbarattolobot?startapp=assistenza_111",
           "https://t.me/ilbarattolobot?startapp=assistenza_-42"],
          [S._link_dentro_telegram(S.URL_PUBBLICO + q) for q in
           ("/?assistenza=mia", "/?assistenza=111", "/?assistenza=-42")])
    prova("...e una forma storta resta il link del sito",
          S.URL_PUBBLICO + "/?assistenza=0x1",
          S._link_dentro_telegram(S.URL_PUBBLICO + "/?assistenza=0x1"))
    S.TELEGRAM_MINIAPP_LINK = vecchio
    prova("rispondere a chi non esiste e' un 404", 404,
          c.post("/api/admin/assistenza/424242", json={"testo": "ciao"},
                 headers=ADMIN).status_code)

    print("\n[l'utente legge la risposta]")
    prova("/api/me conta una risposta nuova", 1,
          c.get("/api/me", headers=COMPRA).json().get("assistenza_nuove"))
    msgs = c.get("/api/assistenza", headers=COMPRA).json()["messaggi"]
    prova("la risposta e' dello staff, senza il nome dell'admin", (True, None),
          (msgs[-2]["staff"], msgs[-2].get("chi")))
    prova("aperta la conversazione, il pallino si spegne", 0,
          c.get("/api/me", headers=COMPRA).json().get("assistenza_nuove"))

    print("\n[il freno: venti messaggi l'ora per persona]")
    S._SECCHI.clear()
    stati = [c.post("/api/assistenza", json={"testo": f"n. {i}"}, headers=VENDE).status_code
             for i in range(21)]
    prova("venti passano, il ventunesimo e' un 429", [200] * 20 + [429], stati)
    S._SECCHI.clear()

    gli_screenshot(c, S, avvisi, aspetta_sottofondo)
    il_nativo_nostr(c, S, avvisi, aspetta_sottofondo)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


# Il numero di Zzap, il caso vero del 23 nov 2026: un nativo Nostr ha l'id
# fino a -2^63, 19 cifre, oltre il 2^53 di JavaScript (come numero JSON
# diventerebbe -5945373116987485696, un utente che non esiste).
NATIVO = -5945373116987485543
NATIVO_JSON_ARROTONDATO = -5945373116987485696


def il_nativo_nostr(c, S, avvisi, aspetta_sottofondo):
    """IL NATIVO NOSTR (23 nov 2026, cantiere assistenza-id-nostr):
    l'elenco e la conversazione danno l'id ESATTO come testo, la
    risposta dello staff arriva, e il tasto dell'avviso porta dentro la
    conversazione anche dentro Telegram (fino a 19 cifre)."""
    print("\n[il nativo Nostr, 19 cifre: il caso di Zzap]")
    con = S.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
                "VALUES(?,?,?,1)", (NATIVO, "Zzap", "negzzap"))
    con.execute("INSERT INTO assistenza(utente, autore, admin, testo, quando, "
                "immagini) VALUES(?,?,0,?,?,'')",
                (NATIVO, NATIVO, "Quale il canale preferenziale?",
                 int(S.time.time())))
    con.commit()
    con.close()
    el = c.get("/api/admin/assistenza", headers=ADMIN).json()["conversazioni"]
    prova("l'elenco lo da' come TESTO, cifra per cifra", str(NATIVO),
          el[0]["utente"])
    prova("...e il testo non passa per un numero (la causa del guasto)",
          True, isinstance(el[0]["utente"], str))
    r = c.get(f"/api/admin/assistenza/{el[0]['utente']}", headers=ADMIN)
    prova("la conversazione si apre con l'id dell'elenco", (200, "Zzap", str(NATIVO)),
          (r.status_code, r.json().get("nome"), r.json().get("utente")))
    prova("...mentre l'id arrotondato non esiste (cosi' si vedeva il guasto)",
          404, c.get(f"/api/admin/assistenza/{NATIVO_JSON_ARROTONDATO}",
                     headers=ADMIN).status_code)
    prima = len([a for a in avvisi if a[0] == NATIVO])
    r = c.post(f"/api/admin/assistenza/{el[0]['utente']}",
               json={"testo": "Scrivi pure qui"}, headers=ADMIN)
    prova("lo staff gli risponde", (200, "Scrivi pure qui"),
          (r.status_code, r.json()["messaggi"][-1]["testo"]))
    prova("...e il nativo riceve l'avviso", prima + 1,
          len([a for a in avvisi if a[0] == NATIVO]))
    vecchio = S.TELEGRAM_MINIAPP_LINK
    S.TELEGRAM_MINIAPP_LINK = "https://t.me/ilbarattolobot"
    prova("il tasto dell'avviso porta dentro la conversazione, 19 cifre",
          f"https://t.me/ilbarattolobot?startapp=assistenza_{NATIVO}",
          S._link_dentro_telegram(f"{S.URL_PUBBLICO}/?assistenza={NATIVO}"))
    prova("...anche col numero piu' lungo possibile, -2^63",
          f"https://t.me/ilbarattolobot?startapp=assistenza_{-2**63}",
          S._link_dentro_telegram(f"{S.URL_PUBBLICO}/?assistenza={-2**63}"))
    prova("...ma venti cifre restano il link del sito",
          f"{S.URL_PUBBLICO}/?assistenza=-12345678901234567890",
          S._link_dentro_telegram(f"{S.URL_PUBBLICO}/?assistenza=-12345678901234567890"))
    S.TELEGRAM_MINIAPP_LINK = vecchio


def _png(colore=(200, 40, 40)) -> bytes:
    import io
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (60, 40), colore).save(out, "PNG")
    return out.getvalue()


def _jpeg_col_gps() -> bytes:
    """Un JPEG con l'EXIF dentro (un GPS finto): deve uscire nudo."""
    import io
    from PIL import Image
    img = Image.new("RGB", (60, 40), (10, 120, 200))
    exif = Image.Exif()
    exif[0x010F] = "MarcaFinta"          # Make
    exif[0x8825] = {1: "N", 2: (45.0, 4.0, 0.0)}   # GPSInfo
    out = io.BytesIO()
    img.save(out, "JPEG", exif=exif.tobytes())
    return out.getvalue()


def _dataurl(raw: bytes, tipo="image/png") -> str:
    import base64
    return f"data:{tipo};base64," + base64.b64encode(raw).decode()


def gli_screenshot(c, S, avvisi, aspetta_sottofondo):
    import os
    import tempfile
    print("\n[gli screenshot all'assistenza]")
    S._SECCHI.clear()
    S.ASSISTENZA_IMG_DIR = tempfile.mkdtemp(prefix="barattolo-assist-img-")
    cartella = S.ASSISTENZA_IMG_DIR
    foto_bot = []

    async def registra_foto(chat_id, raw, tipo, didascalia, bottone=None):
        foto_bot.append((chat_id, raw, tipo, didascalia, bottone))
        return "registrata"
    S._foto_al_bot = registra_foto
    TERZO = {"X-Tg-Init-Data": "collaudo:333:Terzo"}
    con = S.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato) "
                "VALUES(333,'Terzo','neg333',1)")
    con.execute("DELETE FROM assistenza_avvisi")
    con.commit()
    con.close()

    png = _png()
    r = c.post("/api/assistenza", headers=COMPRA,
               json={"testo": "Ecco l'errore", "immagini": [_dataurl(png)]})
    prova("un messaggio con uno screenshot entra", 200, r.status_code)
    ultimo = r.json()["messaggi"][-1]
    prova("...e porta UN nome con la forma giusta", (1, True),
          (len(ultimo["immagini"]),
           bool(ultimo["immagini"] and S.NOME_IMG_ASSISTENZA.match(ultimo["immagini"][0]))))
    nome = ultimo["immagini"][0]
    with open(os.path.join(cartella, nome), "rb") as f:
        sul_disco = f.read()
    prova("sul disco non c'e' un PNG leggibile da fuori (busta del blob)", (False, True),
          (sul_disco.startswith(b"\x89PNG"), sul_disco.split(b":", 1)[0] in (b"plain", b"f2")))
    aspetta_sottofondo()
    prova("l'avviso all'admin dice lo screenshot", True,
          "📎 1 screenshot allegato" in [a for a in avvisi if a[0] == 999][-1][1])
    prova("...e lo screenshot arriva all'admin nel bot", [999],
          [x[0] for x in foto_bot])
    prova("...coi byte giusti, chi l'ha mandato e il tasto", (True, True, True),
          (foto_bot[0][1][:8] == b"\x89PNG\r\n\x1a\n", "(n. 111)" in foto_bot[0][3],
           foto_bot[0][4][1] == S.URL_PUBBLICO + "/?assistenza=111"))

    r = c.get(f"/api/assistenza/immagine/{nome}", headers=COMPRA)
    prova("chi l'ha mandato lo rilegge", (200, "image/png", True),
          (r.status_code, r.headers.get("content-type"), r.content == png))
    prova("...mai in cache, mai eseguito", (True, True, True),
          ("no-store" in r.headers.get("cache-control", ""),
           r.headers.get("x-content-type-options") == "nosniff",
           "sandbox" in r.headers.get("content-security-policy", "")))
    prova("un admin lo legge", 200,
          c.get(f"/api/assistenza/immagine/{nome}", headers=ADMIN).status_code)
    prova("un altro utente NO: 404", 404,
          c.get(f"/api/assistenza/immagine/{nome}", headers=VENDE).status_code)
    prova("un nome storto e' lo stesso 404", 404,
          c.get("/api/assistenza/immagine/..%2Fserver.py", headers=ADMIN).status_code)
    prova("...e uno con la forma giusta che non esiste pure", 404,
          c.get("/api/assistenza/immagine/as" + "0" * 24 + ".jpg",
                headers=ADMIN).status_code)
    conv = c.get("/api/admin/assistenza/111", headers=ADMIN).json()
    prova("nella conversazione dell'admin il messaggio porta lo screenshot", [nome],
          conv["messaggi"][-1]["immagini"])

    gia = len(foto_bot)
    avvisi_prima = len([a for a in avvisi if a[0] == 999])
    r = c.post("/api/assistenza", headers=COMPRA,
               json={"testo": "", "immagini": [_dataurl(png), _dataurl(_png((1, 2, 3)))]})
    prova("solo screenshot, senza testo: entra", (200, ""),
          (r.status_code, r.json()["messaggi"][-1]["testo"] if r.status_code == 200 else None))
    aspetta_sottofondo()
    prova("dentro la pausa niente avviso col testo...", avvisi_prima,
          len([a for a in avvisi if a[0] == 999]))
    nuove = foto_bot[gia:]
    prova("...ma i due screenshot arrivano lo stesso, contati", (2, True),
          (len(nuove), len(nuove) == 2 and "1/2" in nuove[0][3] and "2/2" in nuove[1][3]))
    el = c.get("/api/admin/assistenza", headers=ADMIN).json()["conversazioni"]
    prova("nell'elenco l'ultimo messaggio vuoto dice lo screenshot", "📎 Screenshot",
          [x for x in el if x["utente"] == "111"][0]["ultimo"])

    file_prima = sorted(os.listdir(cartella))
    prova("quattro screenshot sono un 400", 400,
          c.post("/api/assistenza", headers=COMPRA,
                 json={"testo": "x", "immagini": [_dataurl(png)] * 4}).status_code)
    prova("un testo travestito da PNG e' un 400", 400,
          c.post("/api/assistenza", headers=COMPRA,
                 json={"testo": "x", "immagini": [_dataurl(b"<html>ciao</html>")]}).status_code)
    prova("uno buono e uno cattivo: 400, e il buono NON resta sul disco", (400, file_prima),
          (c.post("/api/assistenza", headers=COMPRA,
                  json={"testo": "x", "immagini": [_dataurl(png), "data:image/png;base64,@@"]}
                  ).status_code, sorted(os.listdir(cartella))))
    prova("un elenco che non e' un elenco e' un 400", 400,
          c.post("/api/assistenza", headers=COMPRA,
                 json={"testo": "x", "immagini": "ciao"}).status_code)
    prova("niente testo e niente screenshot resta un 400", 400,
          c.post("/api/assistenza", headers=COMPRA,
                 json={"testo": " ", "immagini": []}).status_code)

    r = c.post("/api/assistenza", headers=COMPRA,
               json={"testo": "foto", "immagini": [_dataurl(_jpeg_col_gps(), "image/jpeg")]})
    n_jpg = r.json()["messaggi"][-1]["immagini"][0]
    letto = c.get(f"/api/assistenza/immagine/{n_jpg}", headers=COMPRA).content
    prova("il JPEG col GPS esce NUDO (niente EXIF, ne' la marca)", (True, False, False),
          (letto[:3] == b"\xff\xd8\xff", b"Exif" in letto, b"MarcaFinta" in letto))

    gia = len(foto_bot)
    c.post("/api/assistenza", headers=ADMIN, json={"testo": "", "immagini": [_dataurl(png)]})
    aspetta_sottofondo()
    prova("l'admin che allega nella SUA conversazione non manda la foto a se stesso",
          [], [x[0] for x in foto_bot[gia:] if x[0] == 999])

    print("\n[lo staff risponde con uno screenshot]")
    file_prima = sorted(os.listdir(cartella))
    prova("un non-admin non risponde come staff nemmeno con uno screenshot (403)",
          (403, file_prima),
          (c.post("/api/admin/assistenza/111", headers=VENDE,
                  json={"testo": "", "immagini": [_dataurl(png)]}).status_code,
           sorted(os.listdir(cartella))))
    gia_avvisi = len([a for a in avvisi if a[0] == 111])
    r = c.post("/api/admin/assistenza/111", headers=ADMIN,
               json={"testo": "", "immagini": [_dataurl(_png((0, 200, 0)))]})
    prova("la risposta dello staff fatta solo di uno screenshot entra", 200,
          r.status_code)
    rsp = r.json()["messaggi"][-1]
    prova("...e' dello staff e porta un nome con la forma giusta", (True, 1, True),
          (rsp["staff"], len(rsp["immagini"]),
           bool(rsp["immagini"] and S.NOME_IMG_ASSISTENZA.match(rsp["immagini"][0]))))
    n_staff = rsp["immagini"][0]
    prova("l'utente riceve l'avviso di sempre", gia_avvisi + 1,
          len([a for a in avvisi if a[0] == 111]))
    msgs = c.get("/api/assistenza", headers=COMPRA).json()["messaggi"]
    prova("l'utente lo trova nella sua conversazione", [n_staff],
          msgs[-1]["immagini"])
    prova("...e lo apre", 200,
          c.get(f"/api/assistenza/immagine/{n_staff}", headers=COMPRA).status_code)
    prova("un altro utente no: 404", 404,
          c.get(f"/api/assistenza/immagine/{n_staff}", headers=VENDE).status_code)
    prova("uno screenshot storto dello staff e' un 400 senza file lasciati",
          (400, sorted(os.listdir(cartella))),
          (c.post("/api/admin/assistenza/111", headers=ADMIN,
                  json={"testo": "x", "immagini": [_dataurl(png), "data:image/png;base64,@@"]}
                  ).status_code, sorted(os.listdir(cartella))))
    prova("rispondere con uno screenshot a chi non esiste: 404 senza file lasciati",
          (404, sorted(os.listdir(cartella))),
          (c.post("/api/admin/assistenza/424242", headers=ADMIN,
                  json={"testo": "x", "immagini": [_dataurl(png)]}).status_code,
           sorted(os.listdir(cartella))))
    prova("niente testo e niente screenshot resta un 400 anche per lo staff", 400,
          c.post("/api/admin/assistenza/111", headers=ADMIN,
                 json={"testo": "", "immagini": []}).status_code)

    print("\n[gli screenshot se ne vanno con l'account]")
    r = c.post("/api/assistenza", headers=TERZO,
               json={"testo": "ciao", "immagini": [_dataurl(png)]})
    n_terzo = r.json()["messaggi"][-1]["immagini"][0]
    prova("il file c'e'", True, os.path.exists(os.path.join(cartella, n_terzo)))
    import asyncio
    esito = S.esegui_cancellazione(333)
    prova("la cancellazione nomina il suo screenshot", [n_terzo],
          esito.get("assistenza_img"))
    asyncio.run(S._dopo_cancellazione(esito))
    prova("...e il file se ne va dal disco", False,
          os.path.exists(os.path.join(cartella, n_terzo)))
    prova("gli screenshot degli altri restano", True,
          os.path.exists(os.path.join(cartella, nome)))

    S.ASSISTENZA_ATTIVA = False
    prova("a leva spenta anche lo screenshot e' un 404", 404,
          c.get(f"/api/assistenza/immagine/{nome}", headers=ADMIN).status_code)
    S.ASSISTENZA_ATTIVA = True
    S._SECCHI.clear()


if __name__ == "__main__":
    sys.exit(main())
