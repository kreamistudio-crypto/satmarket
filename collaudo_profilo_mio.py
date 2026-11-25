# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL NOME E DELLA FOTO SCELTI SU BARATTOLO (23 nov 2026,
cantiere profilo-mio; Andrea: «implementiamo ora la possibilita' di
customizzare la foto, e di mettere il nome umano sul mercatino,
mantenendo l'uso del profilo Nostr». Gratis, col moderatore).

Il server VERO, per HTTP con la TestClient e l'identita' di collaudo
nell'header:
  1) la migrazione e la leva accesa di serie;
  2) la forma del nome: lunghezza, emoji, parole dello staff anche
     camuffate, parole del catalogo vietato; «Modena» passa;
  3) i sosia protetti: chi ha venduto 10 volte e lo staff;
  4) la proposta nasce in revisione e NON cambia niente finche' non e'
     approvata; la quarta scelta e' chiusa senza un cartellino;
  5) l'approvazione la applica: nome e foto ovunque, Telegram non lo
     riscrive, il giro del social nemmeno; il moderatore e' avvisato,
     e chi ha un ordine aperto con lui pure;
  6) un cambio ogni 30 giorni;
  7) si lascia e si rientra senza nuova revisione, la foto resta;
  8) il rifiuto: niente cambia, il motivo arriva, si riprova subito;
  9) le porte dei moderatori: 403 a chi non lo e', il tocco altrui non
     conta; «togli» rimette il nome di prima;
 10) la fusione porta il cartellino, la cancellazione porta via i file;
 11) a leva spenta niente proposte e niente quarta scelta.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, database e cartella delle foto sono usa-e-getta,
nessuna rete (bot e notifiche registrati in memoria).

USO:  python collaudo_profilo_mio.py
"""

import asyncio
import base64
import io
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None

ANNA, BRUNO, CARLA, DARIO, ADMIN = 111, 222, 333, 444, 999
NOSTR = -4243
AVVISI = []        # (tg_id, testo) di notifica()
BOT = []           # (metodo, dati) di bot_api()


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
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    cartella = tempfile.mkdtemp(prefix="barattolo-profilo-mio-")
    db = os.path.join(cartella, "usa-e-getta.db")
    vecchio = sqlite3.connect(db)
    vecchio.execute("CREATE TABLE segnaposto(x INTEGER)")
    vecchio.commit()
    vecchio.close()
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [ADMIN]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    foto = os.path.join(cartella, "foto")
    os.makedirs(foto)
    server.FOTO_DIR = foto

    async def zitto(*a, **k):
        return None

    async def registra_avviso(tg_id, testo, bottone=None):
        AVVISI.append((tg_id, testo))

    async def registra_bot(metodo, dati=None, *a, **k):
        BOT.append((metodo, dati or {}))
        return {"ok": True}

    async def niente_gruppo(*a, **k):
        return False

    for nome in ("notifica_admin", "annuncio_su_nostr", "premia_distintivi",
                 "premia_xp", "aggiorna_profilo_social"):
        if hasattr(server, nome):
            setattr(server, nome, zitto)
    server.notifica = registra_avviso
    server.bot_api = registra_bot
    server._al_gruppo_admin = niente_gruppo
    return db


def chi(tg_id):
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:Utente{tg_id}"}


def scrivi(sql, *arg):
    con = SRV.db()
    con.execute(sql, arg)
    con.commit()
    con.close()


def leggi(sql, *arg):
    con = SRV.db()
    r = con.execute(sql, arg).fetchone()
    con.close()
    return tuple(r) if r else None


def una_foto(seme=1):
    from PIL import Image
    img = Image.new("RGB", (300, 200), ((seme * 50) % 256, 120, 200))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def c_e(nome):
    return bool(nome) and os.path.exists(os.path.join(SRV.FOTO_DIR, nome))


def main():
    db = avvio()
    from fastapi.testclient import TestClient
    c = TestClient(SRV.app)
    me = lambda t: c.get("/api/me", headers=chi(t)).json()
    proponi = lambda t, **corpo: c.post("/api/me/profilo-mio",
                                        headers=chi(t), json=corpo)
    scegli = lambda t, s: c.post("/api/me/avatar-scelta", headers=chi(t),
                                 json={"scelta": s})
    decidi = lambda t, esito, motivo="", da=ADMIN: c.post(
        f"/api/admin/profilo-mio/{t}", headers=chi(da),
        json={"esito": esito, "motivo": motivo})

    # ------------------------------------------------------------------
    print("\n[1) la migrazione e la leva]")
    for t in (ANNA, BRUNO, CARLA, DARIO, ADMIN):
        me(t)
    con = sqlite3.connect(db)
    colonne = {r[1] for r in con.execute("PRAGMA table_info(utenti)")}
    con.close()
    prova("le colonne del cartellino sono nate all'avvio", set(),
          {"mio_nome", "mio_foto", "mio_nome_att", "mio_foto_att",
           "mio_stato", "mio_motivo", "mio_chiesto_il", "mio_approvato_il",
           "mio_nome_prima"} - colonne)
    prova("la leva e' accesa di serie, un cambio ogni 30 giorni",
          (True, 30), (SRV.PROFILO_MIO_ATTIVO, SRV.PROFILO_MIO_GIORNI))
    prova("/api/me lo dice", {"attivo": True, "giorni": 30, "prossimo": 0},
          me(ANNA)["profilo_mio"])
    voci = [v for g in SRV._leve_stato() for v in g.get("voci", [])]
    chiavi = {v["chiave"]: v["valore"] for v in voci}
    prova("il pannello delle leve mostra la leva e i giorni", (True, 30),
          (chiavi.get("PROFILO_MIO_ATTIVO"), chiavi.get("PROFILO_MIO_GIORNI")))

    # ------------------------------------------------------------------
    print("\n[2) la forma del nome]")
    for nome, passa in (("Al", False), ("x" * 31, False),
                        ("Anna 🙂", False), ("Аnna", False),
                        ("4dm1n Anna", False), ("Barattolo Shop", False),
                        ("$taff", False), ("Il m0deratore", False),
                        ("Team Rossi", False), ("Supporto clienti", False),
                        ("Tappo", False), ("123 456", False),
                        ("cocaina", False),
                        ("Modena Vintage", True), ("Steam Punk", True),
                        ("Anna Rossi", True), ("L'Òrto di Zé", True),
                        ("bottega_del-riuso.it", True)):
        prova(f"«{nome[:20]}» {'passa' if passa else 'no'}", passa,
              bool(SRV.nome_mio_forma(nome)[0]))
    prova("gli spazi doppi si stringono", "Anna Rossi",
          SRV.nome_mio_forma("  Anna    Rossi ")[0])

    # ------------------------------------------------------------------
    print("\n[3) i sosia protetti]")
    scrivi("UPDATE utenti SET nome='Bottega del Riuso' WHERE tg_id=?", BRUNO)
    for i in range(10):
        scrivi("INSERT INTO ordini(annuncio_id, venditore_id, compratore_id, "
               "stato, prova) VALUES(?,?,?, 'released', 0)", 9000 + i,
               BRUNO, DARIO)
    r = proponi(ANNA, nome="bottega-del riuso")
    prova("il nome di chi ha venduto 10 volte: 400 e lo dice", (400, True),
          (r.status_code, "troppo simile" in r.json().get("detail", "")))
    r = proponi(ANNA, nome="utente 999")
    prova("il nome dello staff: 400", 400, r.status_code)
    r = proponi(BRUNO, nome="Bottega del Riuso")
    prova("...ma chi ha gia' quel nome lo tiene", 200, r.status_code)
    decidi(BRUNO, "rifiuta")
    AVVISI.clear()

    # ------------------------------------------------------------------
    print("\n[4) la proposta nasce in revisione]")
    prova("senza nome ne' foto: 400", 400, proponi(ANNA).status_code)
    prova("la quarta scelta e' chiusa senza un cartellino approvato", 400,
          scegli(ANNA, "mia").status_code)
    BOT.clear()
    r = proponi(ANNA, nome=" Anna  Rossi ", foto=una_foto(1))
    j = r.json()
    prova("nome e foto: 200, in revisione", (200, "revisione", "Anna Rossi"),
          (r.status_code, j.get("stato"), j.get("nome")))
    foto1 = j.get("foto")
    prova("la foto e' un francobollo nella cartella delle foto", True,
          c_e(foto1) and bool(SRV.NOME_FOTO.match(foto1)))
    from PIL import Image
    with Image.open(os.path.join(SRV.FOTO_DIR, foto1)) as im:
        prova("...quadrato da 128", (128, 128), im.size)
    asyncio.run(asyncio.sleep(0))
    u = me(ANNA)
    prova("finche' non e' approvata non cambia niente",
          ("Utente111", ""), (u["nome"], u["avatar_scelta"]))
    prova("il moderatore riceve la foto coi due bottoni", True,
          any(m == "sendPhoto" and "pm:ok:111" in str(d.get("reply_markup"))
              and d.get("chat_id") == ADMIN for m, d in BOT))
    r = proponi(ANNA, nome="Anna R.", foto=una_foto(2))
    foto2 = r.json().get("foto")
    prova("riproporre in attesa sostituisce, e la foto vecchia se ne va",
          (200, "Anna R.", False, True),
          (r.status_code, leggi("SELECT mio_nome_att FROM utenti WHERE "
                                "tg_id=?", ANNA)[0], c_e(foto1), c_e(foto2)))

    # ------------------------------------------------------------------
    print("\n[5) l'approvazione la applica]")
    # Anna ha un ordine aperto con Dario: il nome nuovo gli va detto
    scrivi("INSERT INTO ordini(annuncio_id, venditore_id, compratore_id, "
           "stato, prova) VALUES(8000, ?, ?, 'locked', 0)", ANNA, DARIO)
    AVVISI.clear()
    r = decidi(ANNA, "approva")
    prova("il moderatore approva", (200, True),
          (r.status_code, r.json().get("ok")))
    u = me(ANNA)                 # la Mini App riscrive nome e username...
    prova("...e il nome scelto resta (Telegram non lo riscrive)",
          ("Anna R.", "mia", foto2, "approvato"),
          (u["nome"], u["avatar_scelta"], u["avatar"], u["mio_stato"]))
    prova("il prossimo cambio fra 30 giorni", True,
          u["profilo_mio"]["prossimo"] > 29 * 86400 + u["mio_approvato_il"])
    prova("ad Anna arriva il si'", True,
          any(t == ANNA and "online" in s for t, s in AVVISI))
    prova("a Dario, che ha l'ordine aperto con lei, il nome nuovo", True,
          any(t == DARIO and "Utente111" in s and "Anna R." in s
              for t, s in AVVISI))
    prova("...e a nessun altro", {ANNA, DARIO}, {t for t, _ in AVVISI})
    prova("il secondo moderatore trova il fatto compiuto", 409,
          decidi(ANNA, "approva").status_code)
    SRV._scrivi_nome_nostr(ANNA, "Nome dal kind-0")
    SRV._scrivi_avatar(ANNA, "")
    prova("il giro del social non scrive sopra il cartellino",
          ("Anna R.", foto2), leggi("SELECT nome, avatar FROM utenti "
                                    "WHERE tg_id=?", ANNA))
    prova("...e non porta via la sua foto", True, c_e(foto2))
    vetrina = c.get(f"/api/negozio/{leggi('SELECT negozio FROM utenti WHERE tg_id=?', ANNA)[0]}")
    prova("la pagina del negozio la chiama col nome nuovo", True,
          vetrina.status_code != 200 or "Anna R." in vetrina.text)

    # ------------------------------------------------------------------
    print("\n[6) un cambio ogni 30 giorni]")
    r = proponi(ANNA, nome="Anna Bianchi")
    prova("prima dei 30 giorni: 400 con la data", (400, True),
          (r.status_code, "Il prossimo cambio si può fare dal"
           in r.json().get("detail", "")))
    scrivi("UPDATE utenti SET mio_approvato_il=mio_approvato_il-31*86400 "
           "WHERE tg_id=?", ANNA)
    r = proponi(ANNA, nome="Anna Bianchi")
    prova("dopo i 30 giorni si propone; senza foto resta la sua",
          (200, foto2), (r.status_code, r.json().get("foto")))
    decidi(ANNA, "approva")
    prova("approvato il solo nome: la foto e' la stessa e c'e' ancora",
          ("Anna Bianchi", foto2, True),
          leggi("SELECT nome, avatar, 1 FROM utenti WHERE tg_id=?", ANNA)[:2]
          + (c_e(foto2),))

    # ------------------------------------------------------------------
    print("\n[7) si lascia e si rientra]")
    r = scegli(ANNA, "telegram")
    prova("torna a Telegram: il nome di Telegram, la foto si svuota",
          (200, "Utente111", ""),
          (r.status_code, r.json().get("nome"), r.json().get("avatar")))
    prova("...il cartellino resta, coi suoi file", ("Anna Bianchi", True),
          (leggi("SELECT mio_nome FROM utenti WHERE tg_id=?", ANNA)[0],
           c_e(foto2)))
    me(ANNA)
    prova("la Mini App lo riscrive col suo nome Telegram", "Utente111",
          leggi("SELECT nome FROM utenti WHERE tg_id=?", ANNA)[0])
    r = scegli(ANNA, "mia")
    prova("rientra su «mia» senza revisione", (200, "Anna Bianchi", foto2),
          (r.status_code, r.json().get("nome"), r.json().get("avatar")))
    prova("...e nessuna proposta nuova", "approvato",
          leggi("SELECT mio_stato FROM utenti WHERE tg_id=?", ANNA)[0])
    r = scegli(ANNA, "nessuna")
    prova("«Nessuna» nasconde la foto, il nome torna quello di prima",
          (200, "", "Utente111"),
          (r.status_code, r.json().get("avatar"), r.json().get("nome")))
    # da «Nessuna» la colonna tiene ancora la foto scelta: il giro del
    # social che la sostituisce (qui a mano) non deve cancellarne il file
    scrivi("UPDATE utenti SET avatar_scelta='telegram' WHERE tg_id=?", ANNA)
    SRV._scrivi_avatar(ANNA, "")
    prova("il giro del social dopo «Nessuna» lascia il file della foto scelta",
          ("", True), (leggi("SELECT avatar FROM utenti WHERE tg_id=?", ANNA)[0],
                       c_e(foto2)))
    scegli(ANNA, "mia")

    # ------------------------------------------------------------------
    print("\n[8) il rifiuto]")
    AVVISI.clear()
    r = proponi(CARLA, nome="Carla Verdi")
    prova("Carla propone il solo nome (non ha foto): 200", 200, r.status_code)
    r = decidi(CARLA, "rifiuta", "Scrivi il nome che usi davvero")
    prova("il moderatore rifiuta col motivo", 200, r.status_code)
    prova("niente cambia, lo stato dice rifiutato",
          ("Utente333", "", "rifiutato", "Scrivi il nome che usi davvero"),
          leggi("SELECT nome, avatar_scelta, mio_stato, mio_motivo FROM utenti "
                "WHERE tg_id=?", CARLA))
    prova("a Carla arriva il motivo", True,
          any(t == CARLA and "Scrivi il nome che usi davvero" in s
              for t, s in AVVISI))
    prova("il rifiuto non consuma il mese: si riprova subito", 200,
          proponi(CARLA, nome="Carla V.").status_code)

    # ------------------------------------------------------------------
    print("\n[9) le porte dei moderatori]")
    prova("la lista: 403 a chi non e' moderatore", 403,
          c.get("/api/admin/profilo-mio", headers=chi(BRUNO)).status_code)
    prova("la decisione: 403 a chi non e' moderatore", 403,
          decidi(CARLA, "approva", da=BRUNO).status_code)
    lista = c.get("/api/admin/profilo-mio", headers=chi(ADMIN)).json()
    prova("la lista del moderatore: prima chi aspetta", (CARLA, "revisione"),
          (lista[0]["tg_id"], lista[0]["mio_stato"]))
    asyncio.run(SRV.callback_profilo_mio(
        {"from": {"id": BRUNO}, "message": {}}, f"ok:{CARLA}"))
    prova("il tocco di chi non e' moderatore non conta", "revisione",
          leggi("SELECT mio_stato FROM utenti WHERE tg_id=?", CARLA)[0])
    asyncio.run(SRV.callback_profilo_mio(
        {"from": {"id": ADMIN}, "message": {}}, f"ok:{CARLA}"))
    prova("quello del moderatore si'", ("approvato", "Carla V."),
          leggi("SELECT mio_stato, nome FROM utenti WHERE tg_id=?", CARLA))
    r = decidi(ANNA, "togli", "Nome non adatto")
    prova("«togli»: via il cartellino, torna il nome di prima",
          (200, "Utente111", "", "", "tolto", False),
          (r.status_code,) + leggi(
              "SELECT nome, avatar_scelta, mio_nome, mio_stato FROM utenti "
              "WHERE tg_id=?", ANNA) + (c_e(foto2),))

    # ------------------------------------------------------------------
    print("\n[10) la fusione e la cancellazione]")
    npub = SRV.hex_to_npub("e5" * 32)        # chiave PUBBLICA di cartone
    scrivi("INSERT INTO utenti(tg_id, nome, negozio, registrato, npub_accesso, "
           "npub, npub_verificata, mio_nome, mio_foto, mio_stato, "
           "mio_approvato_il) VALUES(?, 'Nostr', 'negnostr', 1, ?, ?, 1, "
           "'Dario Blu', 'av_negnostr_1.jpg', 'approvato', 5)",
           NOSTR, npub, npub)
    esito = SRV.esegui_fusione(BRUNO, NOSTR)
    prova("la fusione va in porto", "", esito if isinstance(esito, str) else "")
    prova("il cartellino della meta' Nostr passa a Bruno, senza imporsi",
          ("Dario Blu", "av_negnostr_1.jpg", "approvato", "", "Utente222"),
          leggi("SELECT mio_nome, mio_foto, mio_stato, avatar_scelta, "
                "mio_nome_prima FROM utenti WHERE tg_id=?", BRUNO))
    scrivi("UPDATE utenti SET mio_approvato_il=0 WHERE tg_id=?", BRUNO)
    r = proponi(BRUNO, nome="Bruno B.", foto=una_foto(3))
    foto_b = r.json().get("foto")
    esito = SRV.esegui_cancellazione(BRUNO)
    prova("la cancellazione porta via anche la foto in attesa", True,
          foto_b in (esito or {}).get("foto", []))

    # ------------------------------------------------------------------
    print("\n[11) a leva spenta]")
    SRV.PROFILO_MIO_ATTIVO = False
    prova("niente proposte", 400, proponi(DARIO, nome="Dario D.").status_code)
    prova("niente quarta scelta", 400, scegli(DARIO, "mia").status_code)
    prova("chi ce l'ha la tiene", ("Carla V.", "mia"),
          leggi("SELECT nome, avatar_scelta FROM utenti WHERE tg_id=?", CARLA))
    prova("...e puo' sempre uscirne", 200, scegli(CARLA, "telegram").status_code)
    SRV.PROFILO_MIO_ATTIVO = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
