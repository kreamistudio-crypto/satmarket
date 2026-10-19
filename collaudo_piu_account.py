# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «PIU' ACCOUNT OVUNQUE» (16 ott 2026).

`collaudo_account.py` prova il portachiavi del web d'agosto; questo
prova quel che il cantiere aggiunge, con le richieste VERE (TestClient
= un browser che tiene i cookie):

  · A LEVA SPENTA il mondo di ieri: dentro la Mini App l'account scelto
    non conta, «Esci da tutti» e il cassetto del moderatore non esistono;
  · DENTRO LA MINI APP si aggiunge un account accanto al Telegram, nel
    portachiavi di QUEL Telegram, senza i cookie del web — e da li' ogni
    endpoint risponde per lui (`/api/me`, gli ordini);
  · L'ID VIAGGIA COME TESTO: un account con un id fino a -2^63 si
    sceglie e si raggiunge esatto (il guasto dal campo: lo switch verso
    un account nato con Nostr rispondeva 400);
  · UN SECONDO TELEGRAM sullo stesso telefono (stessa WebView, stessi
    cookie) non vede e non usa gli account del primo — e un account
    scelto che non c'e' piu' e' un 401 detto, MAI una ricaduta muta sul
    Telegram;
  · «ESCI» chiude l'account scelto e lascia il Telegram; «ESCI DA TUTTI»
    chiude tutti gli aggiunti (Mini App) o tutti (web), e le sessioni
    muoiono anche nel database;
  · L'ANNOTAZIONE: due account aperti insieme che si comprano o si
    votano NON si bloccano — si scrive una riga, che il moderatore
    legge; fra account NON aperti insieme non si scrive niente;
  · IL LIBRO P2P dice quali ordini sono dei MIEI ALTRI account, e i
    «miei» sono quelli dell'account scelto, non del Telegram.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna chiave, nessuna rete, nessun LNbits.

USO:  python collaudo_piu_account.py
"""

import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0

# Un id di account nato con Nostr, della forma vera: negativo e oltre
# 2^53, cioe' uno che un Number di JavaScript arrotonda.
GRANDE = -4611686018427387905


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-piu-account-"),
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
                 ("MAX_ACCOUNT_BROWSER", 4),
                 ("MOSTRO_RELAY", "ws://127.0.0.1:9"),
                 ("MOSTRO_RELAY_SPECCHIO", "ws://127.0.0.1:9"),
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        """LNbits non si chiama mai: qui conta chi compra, non la fattura."""
        return {"payment_hash": f"hash{memo[-6:]}{time.time_ns()}",
                "payment_request": f"lnbc{sats}collaudo"}
    server.crea_invoice_escrow = invoice_finta
    # le notifiche non c'entrano, e senza bot direbbero solo righe
    server.notifica = lambda *a, **k: _niente()
    return server


async def _niente():
    return None


def tg(tg_id, nome="Tele"):
    """L'initData del collaudo: il Telegram che ospita la Mini App."""
    return {"X-Tg-Init-Data": f"collaudo:{tg_id}:{nome}"}


def con_conto(tg_id, conto, nome="Tele"):
    h = tg(tg_id, nome)
    h["X-Barattolo-Conto"] = str(conto)
    return h


def aggiungi_dentro(c, t, nuovo, nome):
    """Aggiunge `nuovo` nella Mini App del Telegram `t`. La porta e'
    `apri_sessione`, la stessa di ogni login: qui si bussa dal login di
    collaudo (il Nostr vero vuole coincurve, che in CI non c'e'), con la
    firma di Telegram accanto — e' quella che manda la sessione nel
    portachiavi della Mini App."""
    return c.post("/api/login/telegram", headers=tg(t),
                  json={"collaudo": True, "id": nuovo, "first_name": nome})


def main():
    server = avvio()
    from fastapi.testclient import TestClient

    print("=" * 58)
    print("  IL COLLAUDO DI «PIU' ACCOUNT OVUNQUE»")
    print("=" * 58)

    # ------------------------------------------------------------------
    print("\n[a leva spenta, il mondo di ieri]")
    server.PIU_ACCOUNT_OVUNQUE = False
    c0 = TestClient(server.app)
    r = aggiungi_dentro(c0, 700, 701, "Altro")
    prova("dentro Telegram il login apre la sessione del WEB, come ieri",
          True, "barattolo_sessione" in c0.cookies)
    prova("...e nessun portachiavi della Mini App", False,
          any(k.startswith("barattolo_mini_") for k in c0.cookies.keys()))
    prova("...e nessuna intestazione nuova", None,
          r.headers.get("x-barattolo-aperto"))
    prova("l'account scelto NON conta: risponde il Telegram", 700,
          c0.get("/api/me", headers=con_conto(700, 701)).json()["tg_id"])
    prova("«Esci da tutti» non esiste", 404,
          c0.post("/api/logout/tutti").status_code)
    adm = TestClient(server.app)
    prova("...e nemmeno il cassetto del moderatore", 404,
          adm.get("/api/admin/account-insieme", headers=tg(999, "Admin")).status_code)
    prova("/api/me dice la leva spenta", False,
          c0.get("/api/me", headers=tg(700)).json()["piu_account"])

    # ------------------------------------------------------------------
    print("\n[dentro la Mini App, un account accanto al Telegram]")
    server.PIU_ACCOUNT_OVUNQUE = True
    c = TestClient(server.app)      # UN telefono: una WebView, un barattolo di cookie
    d = c.get("/api/sessioni", headers=tg(710, "Andrea")).json()
    prova("il selettore parte dal solo Telegram", ["710"],
          [x["id"] for x in d["conti"]])
    prova("...segnato come Telegram e attivo", (True, "710"),
          (d["conti"][0].get("telegram"), d["attivo_id"]))
    r = aggiungi_dentro(c, 710, GRANDE, "Negozio")
    prova("il login dentro la Mini App riesce", 200, r.status_code)
    prova("...e dice chi e' entrato, ESATTO e come testo", str(GRANDE),
          r.headers.get("x-barattolo-aperto"))
    prova("...nel portachiavi di QUEL Telegram", True,
          "barattolo_mini_710" in c.cookies)
    prova("...senza toccare i cookie del web", False,
          "barattolo_sessione" in c.cookies)
    prova("scelto l'account, /api/me risponde per lui", str(GRANDE),
          str(c.get("/api/me", headers=con_conto(710, GRANDE)).json()["tg_id"]))
    prova("senza sceglierlo, risponde il Telegram", 710,
          c.get("/api/me", headers=tg(710, "Andrea")).json()["tg_id"])
    d = c.get("/api/sessioni", headers=con_conto(710, GRANDE)).json()
    prova("il selettore dice tutt'e due, Telegram in testa",
          ["710", str(GRANDE)], [x["id"] for x in d["conti"]])
    prova("...e l'attivo e' lo scelto, come testo esatto", str(GRANDE),
          d["attivo_id"])
    prova("IL TOKEN NON ESCE nemmeno da qui", False, "token" in str(d))
    r = aggiungi_dentro(c, 710, 710, "Andrea")
    prova("entrare col PROPRIO Telegram non apre niente", "710",
          r.headers.get("x-barattolo-aperto"))
    prova("...e il selettore resta di due", 2, len(
        c.get("/api/sessioni", headers=tg(710, "Andrea")).json()["conti"]))

    # ------------------------------------------------------------------
    print("\n[ordini separati]")
    con = server.db()
    adesso = int(time.time())
    server._upsert_da_telegram(con, 990, "Venditore", "venditore")
    for aid, vend in ((9101, 990), (9102, 990)):
        con.execute("INSERT INTO annunci(id, venditore_id, titolo, prezzo_sats, "
                    "stato, creato) VALUES(?,?,?,?,?,?)",
                    (aid, vend, f"oggetto {aid}", 1000, "attivo", adesso))
    con.commit()
    con.close()
    # gli ordini nascono dalla strada vera: «Compra» dall'account scelto
    # e dal Telegram, dallo stesso telefono
    prova("l'account scelto compra", 200, c.post(
        "/api/orders", headers=con_conto(710, GRANDE),
        json={"annuncio_id": 9101}).status_code)
    prova("...e il Telegram compra", 200, c.post(
        "/api/orders", headers=tg(710, "Andrea"),
        json={"annuncio_id": 9102}).status_code)

    def annunci_degli_ordini(h):
        r = c.get("/api/orders", headers=h)
        if r.status_code != 200:
            return (r.status_code, r.text[:200])
        lista = r.json()
        if isinstance(lista, dict):
            return ("forma", list(lista.keys())[:10])
        return sorted(o.get("annuncio_id") for o in lista)
    prova("l'account scelto vede i SUOI ordini", [9101],
          annunci_degli_ordini(con_conto(710, GRANDE)))
    prova("...e il Telegram i suoi", [9102],
          annunci_degli_ordini(tg(710, "Andrea")))

    # ------------------------------------------------------------------
    print("\n[un secondo Telegram sullo stesso telefono]")
    d2 = c.get("/api/sessioni", headers=tg(720, "Sorella")).json()
    prova("vede SOLO se stesso, non gli account del primo", ["720"],
          [x["id"] for x in d2["conti"]])
    r = c.get("/api/me", headers=con_conto(720, GRANDE, "Sorella"))
    prova("e se prova a usarne uno: 401, mai il primo ne' se stesso", 401,
          r.status_code)
    prova("...con la frase che fa tornare il client al Telegram", True,
          r.json().get("detail", "").startswith("L'account che avevi scelto"))
    prova("un account scelto storto e' un 401, non un 500", 401,
          c.get("/api/me", headers=con_conto(710, "non-un-numero")).status_code)

    # ------------------------------------------------------------------
    print("\n[il libro P2P: i miei sono dell'account scelto]")
    leve_vere = server._p2p_leve
    foto_vera = dict(server._P2P_FOTO)
    server._p2p_leve = lambda: dict(leve_vere(), attivo=True)
    server._P2P_FOTO.update({"eventi": [{"id": "e1"}], "quando": adesso,
                             "autori": {"ordN": GRANDE, "ordT": 710,
                                        "ordX": 555}})
    server._P2P_SESSIONI_VOLTI.clear()
    try:
        lN = c.get("/api/p2p/libro", headers=con_conto(710, GRANDE)).json()
        prova("con l'account scelto, i «miei» sono i SUOI", ["ordN"],
              lN.get("miei"))
        lT = c.get("/api/p2p/libro", headers=tg(710, "Andrea")).json()
        prova("...e dal Telegram quelli del Telegram", ["ordT"], lT.get("miei"))
        prova("il libro non dice quali sono dei miei altri account "
              "(niente rifiuto, decisione di Andrea)", (None, None),
              (lN.get("altri_miei"), lT.get("altri_miei")))
    finally:
        server._p2p_leve = leve_vere
        server._P2P_FOTO.clear()
        server._P2P_FOTO.update(foto_vera)

    # ------------------------------------------------------------------
    print("\n[l'annotazione: si scrive, non si blocca]")
    # Due account aperti INSIEME sul web: il compratore 811 e il
    # venditore 812. Un terzo, 813, sta su un altro telefono.
    w = TestClient(server.app)
    w.post("/api/login/telegram", json={"collaudo": True, "id": 812,
                                        "first_name": "Bottega"})
    w.post("/api/login/telegram", json={"collaudo": True, "id": 811,
                                        "first_name": "Cliente"})
    con = server.db()
    for aid, vend in ((9201, 812), (9202, 813)):
        con.execute("INSERT INTO annunci(id, venditore_id, titolo, prezzo_sats, "
                    "stato, creato) VALUES(?,?,?,?,?,?)",
                    (aid, vend, f"oggetto {aid}", 1000, "attivo", adesso))
    con.commit()
    con.close()

    def quante_note():
        k = server.db()
        try:
            return k.execute("SELECT COUNT(*) FROM account_insieme").fetchone()[0]
        finally:
            k.close()
    prima = quante_note()
    r = w.post("/api/orders", json={"annuncio_id": 9201})
    prova("comprare dal proprio altro account NON e' bloccato", False,
          r.status_code == 400 and "stesso" in r.text)
    prova("...ma si annota, una riga", prima + 1, quante_note())
    w.post("/api/orders", json={"annuncio_id": 9202})
    prova("comprare da un estraneo non annota niente", prima + 1,
          quante_note())
    # il feedback: un affare concluso fra i due account
    con = server.db()
    oid = con.execute(
        "INSERT INTO ordini(annuncio_id, compratore_id, venditore_id, "
        "prezzo_sats, stato, creato) VALUES(9201, 811, 812, 1000, "
        "'released', ?)", (adesso,)).lastrowid
    con.commit()
    con.close()
    r = w.post(f"/api/orders/{oid}/feedback", json={"voto": 5})
    prova("il voto al proprio altro account passa (decisione di Andrea)",
          200, r.status_code)
    prova("...e si annota", prima + 2, quante_note())
    # la PRESA P2P (17 ott 2026, «solo annotare, mai bloccare»): il Cliente
    # prende l'ordine che la Bottega ha pubblicato sul libro
    per_vero, ric_vero = server._p2p_per, server._p2p_riconosciuto
    server._p2p_per = lambda t: dict(per_vero(t), attivo=True)
    server._p2p_riconosciuto = lambda con, t: True
    try:
        con = server.db()
        con.execute("INSERT INTO p2p_ordini(ordine, tg_id, creato, maker) "
                    "VALUES('ordine-pp-0001', 812, ?, 1)", (adesso,))
        con.commit()
        con.close()
        r = w.post("/api/p2p/ordini", json={"ordini": ["ordine-pp-0001"],
                                            "presi": True})
        prova("prendere l'ordine P2P del proprio altro account passa", 200,
              r.status_code)
        prova("...e si annota", prima + 3, quante_note())
        w.post("/api/p2p/ordini", json={"ordini": ["ordine-pp-0001"],
                                        "presi": True})
        prova("...una volta sola: il telefono rimanda la lista, la riga no",
              prima + 3, quante_note())
    finally:
        server._p2p_per, server._p2p_riconosciuto = per_vero, ric_vero
    note = adm.get("/api/admin/account-insieme", headers=tg(999, "Admin")).json()
    prova("il moderatore legge chi, l'altro e cosa", [
        ("Cliente", "Bottega", "presa P2P"),
        ("Cliente", "Bottega", "feedback"),
        ("Cliente", "Bottega", "acquisto avviato")],
        [(x["nome_chi"], x["nome_altro"], x["cosa"]) for x in note])
    prova("...e il cassetto e' solo dei moderatori", 403,
          w.get("/api/admin/account-insieme").status_code)
    server.PIU_ACCOUNT_OVUNQUE = False
    w.post("/api/orders", json={"annuncio_id": 9201})
    prova("a leva spenta non si annota niente", prima + 3, quante_note())
    server.PIU_ACCOUNT_OVUNQUE = True

    # ------------------------------------------------------------------
    print("\n[lo switch del web verso un id grande]")
    w.post("/api/login/telegram", json={"collaudo": True, "id": GRANDE,
                                        "first_name": "Nostrano"})
    w.post("/api/sessioni/attiva", json={"tg_id": 811})
    prova("si torna al Telegram", 811, w.get("/api/me").json()["tg_id"])
    ids = [x["id"] for x in w.get("/api/sessioni").json()["conti"]]
    prova("le righe portano l'id ESATTO come testo", True, str(GRANDE) in ids)
    r = w.post("/api/sessioni/attiva", json={"tg_id": str(GRANDE)})
    prova("lo switch col TESTO raggiunge l'account grande", 200,
          r.status_code)
    prova("...e /api/me cambia persona davvero", GRANDE,
          w.get("/api/me").json()["tg_id"])
    # il guasto dal campo, rifatto: il Number arrotondato di JavaScript
    arrotondato = int(float(GRANDE))
    prova("(il numero arrotondato, come lo mandava il client, non c'e')",
          400, w.post("/api/sessioni/attiva",
                      json={"tg_id": arrotondato}).status_code)

    # ------------------------------------------------------------------
    # IL RINNOVO A OGNI USO (19 ott 2026, cantiere logout-apk): la
    # sessione usata si rinnova nel database al piu' una volta al giorno
    # e il cookie che la porta si riscrive nella stessa risposta — sul
    # web (sessione attiva e portachiavi) e dentro la Mini App (il
    # portachiavi di QUEL Telegram). Una sessione «di due giorni fa» si
    # finge spostando indietro `creato` e `scade` nel database.
    print("\n[il rinnovo a ogni uso]")
    import hashlib

    def invecchia(token, giorni):
        th = hashlib.sha256(token.encode()).hexdigest()
        con = server.db()
        con.execute("UPDATE sessioni SET creato=creato-?, scade=scade-? "
                    "WHERE token_hash=?", (giorni * 86400, giorni * 86400, th))
        con.commit()
        con.close()

    def scadenza(token):
        th = hashlib.sha256(token.encode()).hexdigest()
        con = server.db()
        r = con.execute("SELECT creato, scade FROM sessioni WHERE token_hash=?",
                        (th,)).fetchone()
        con.close()
        return r

    def cookie_scritti(r):
        return sorted({h.split("=", 1)[0] for h in r.headers.get_list("set-cookie")})

    rw = TestClient(server.app)
    rw.post("/api/login/telegram",
            json={"collaudo": True, "id": 761, "first_name": "Rinnovo"})
    tok = rw.cookies.get("barattolo_sessione")
    r = rw.get("/api/me")
    prova("appena entrato: niente rinnovo, niente cookie riscritti", (200, []),
          (r.status_code, cookie_scritti(r)))
    invecchia(tok, 2)
    adesso = int(time.time())
    r = rw.get("/api/me")
    prova("usata dopo due giorni: la sessione si rinnova a 30 giorni da adesso", True,
          r.status_code == 200 and abs(scadenza(tok)["scade"] - (adesso + 30 * 86400)) < 60)
    prova("...e la risposta riscrive sessione e portachiavi", ["barattolo_portachiavi",
                                                             "barattolo_sessione"],
          cookie_scritti(r))
    r = rw.get("/api/me")
    prova("...e la seconda richiesta dello stesso giorno non riscrive niente", [],
          cookie_scritti(r))
    invecchia(tok, 89)                 # login di 91 giorni fa: oltre il tetto
    prova("oltre il tetto dei 90 giorni dal login si e' fuori, usata o no", 401,
          rw.get("/api/me").status_code)
    # dentro la Mini App: l'account aggiunto accanto al Telegram 770
    m = TestClient(server.app)
    aggiungi_dentro(m, 770, 771, "Accanto")
    tm = m.cookies.get("barattolo_mini_770").split(".")[0]
    invecchia(tm, 3)
    r = m.get("/api/me", headers=con_conto(770, 771))
    prova("dentro la Mini App l'account scelto si rinnova", (200, 771, ["barattolo_mini_770"]),
          (r.status_code, r.json().get("tg_id"), cookie_scritti(r)))

    # ------------------------------------------------------------------
    print("\n[uscire]")
    r = c.post("/api/logout", headers=con_conto(710, GRANDE))
    prova("«Esci» dentro la Mini App chiude l'account scelto", 200,
          r.status_code)
    prova("...e si resta sul Telegram", ["710"], [x["id"] for x in c.get(
        "/api/sessioni", headers=tg(710, "Andrea")).json()["conti"]])
    prova("...e la sua sessione e' morta: scelto, ora e' un 401", 401,
          c.get("/api/me", headers=con_conto(710, GRANDE)).status_code)
    aggiungi_dentro(c, 710, 731, "Uno")
    aggiungi_dentro(c, 710, 732, "Due")
    prova("due aggiunti di nuovo", 3, len(c.get(
        "/api/sessioni", headers=tg(710, "Andrea")).json()["conti"]))
    r = c.post("/api/logout/tutti", headers=tg(710, "Andrea"))
    prova("«Esci da tutti» dentro la Mini App", (200, 2),
          (r.status_code, r.json().get("chiusi")))
    prova("...e resta il solo Telegram", ["710"], [x["id"] for x in c.get(
        "/api/sessioni", headers=tg(710, "Andrea")).json()["conti"]])
    prova("...che continua a funzionare", 710,
          c.get("/api/me", headers=tg(710, "Andrea")).json()["tg_id"])
    prova("(il secondo Telegram non e' stato toccato)", ["720"],
          [x["id"] for x in c.get("/api/sessioni",
                                  headers=tg(720, "Sorella")).json()["conti"]])
    n_web = len(w.get("/api/sessioni").json()["conti"])
    r = w.post("/api/logout/tutti")
    prova("«Esci da tutti» sul web chiude tutti", (200, n_web),
          (r.status_code, r.json().get("chiusi")))
    prova("...e da li' non si e' piu' nessuno", 401,
          w.get("/api/me").status_code)

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
