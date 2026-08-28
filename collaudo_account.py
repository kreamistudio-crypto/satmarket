# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL PORTACHIAVI: piu' account sullo stesso browser
(ago 2026).

`prove.py` difende la FORMA — che il token non esca, che lo switch non
scriva, che la porta del login sia una sola — e fa girare i ferri puri
su un database di cartone. Quello che non puo' fare e' il giro VERO:
un browser che tiene i cookie, quattro rotte vere in fila, e la domanda
che conta davvero — DOPO lo switch, `/api/me` dice l'altro account?

Quella domanda non e' una forma. Il cantiere si regge tutto li': il
cookie attivo si riscrive, e da quel momento OGNI endpoint dell'app —
che non e' stato toccato di una riga — deve riconoscere l'altra
persona. Una sentinella non lo puo' dire; solo le richieste vere.

Le domande a cui risponde:

  · due login di fila NON si sovrascrivono: restano aperti tutti e due,
    ed e' la ragione per cui il cantiere esiste;
  · dopo lo switch `/api/me` cambia persona davvero — vetrina, ordini
    e permessi seguono, perche' seguono il cookie;
  · IL TOKEN NON ESCE MAI dal JSON di `/api/sessioni`: e' la riga da
    non ammorbidire, e qui si guarda la risposta VERA e non il codice;
  · l'ANTI-ORACOLO risponde identico a un account che non c'e' e a uno
    che non e' nel portachiavi — provato sul database vero, dove il
    secondo esiste per davvero;
  · il LOGOUT esce da UNO: chiude l'attivo, passa a chi resta, e solo
    all'ultimo saluta come ha sempre fatto;
  · IL MONDO DI IERI e' intatto: un browser con un account solo fa il
    login e il logout esattamente come prima.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
chiave, nessuna rete, nessun LNbits.

USO:  python collaudo_account.py
"""

import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-account-"),
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
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    return server


def main():
    server = avvio()
    from fastapi.testclient import TestClient

    print("=" * 58)
    print("  IL COLLAUDO DEL PORTACHIAVI")
    print("=" * 58)

    # UN client = UN browser: tiene i cookie fra una richiesta e
    # l'altra, che e' esattamente cio' che questo cantiere governa.
    c = TestClient(server.app)

    print("\n[due account, aperti insieme]")
    r = c.post("/api/login/telegram",
               json={"collaudo": True, "id": 111, "first_name": "Alan"})
    prova("il primo login riesce", 200, r.status_code)
    prova("...e /api/me dice lui", 111, c.get("/api/me").json()["tg_id"])
    prova("...e il portachiavi nasce", True,
          "barattolo_portachiavi" in c.cookies)

    r = c.post("/api/login/telegram",
               json={"collaudo": True, "id": 222, "first_name": "To The Mooon"})
    prova("il secondo login riesce", 200, r.status_code)
    prova("...e ora si e' l'altro", 222, c.get("/api/me").json()["tg_id"])

    d = c.get("/api/sessioni").json()
    prova("il primo NON e' stato buttato fuori", [111, 222],
          [x["tg_id"] for x in d["conti"]])
    prova("...e l'attivo e' il secondo", 222, d["attivo"])
    prova("...coi nomi giusti", ["Alan", "To The Mooon"],
          [x["nome"] for x in d["conti"]])

    # LA RIGA DA NON AMMORBIDIRE, guardata sulla risposta vera e non
    # sul sorgente: il token sta in un cookie HttpOnly, e se uscisse
    # di qui finirebbe in mano al JavaScript.
    prova("IL TOKEN NON ESCE dal JSON", [],
          [k for x in d["conti"] for k in x if "token" in k])
    prova("...e nemmeno in fondo alla busta", False,
          "token" in str(d))

    print("\n[lo switch]")
    r = c.post("/api/sessioni/attiva", json={"tg_id": 111})
    prova("lo switch riesce", 200, r.status_code)
    # LA DOMANDA DEL CANTIERE: da qui in poi ogni endpoint dell'app
    # deve vedere l'altra persona, senza che nessuno di loro sia stato
    # toccato di una riga.
    prova("...e /api/me e' cambiato persona DAVVERO", 111,
          c.get("/api/me").json()["tg_id"])
    prova("...e la lista dice il nuovo attivo", 111,
          c.get("/api/sessioni").json()["attivo"])
    prova("...e restano aperti tutti e due", 2,
          len(c.get("/api/sessioni").json()["conti"]))

    # Lo switch e' una LETTURA: le sessioni sul database non cambiano
    # di numero, perche' non se ne aprono e non se ne chiudono.
    con = server.db()
    quante = con.execute("SELECT COUNT(*) n FROM sessioni").fetchone()["n"]
    con.close()
    prova("lo switch non ha aperto nessuna sessione nuova", 2, quante)

    print("\n[l'anti-oracolo]")
    # 333 ESISTE sul database (lo creiamo apposta) ma non e' nel
    # portachiavi di questo browser: deve rispondere IDENTICO a un
    # tg_id che non e' mai esistito, o l'endpoint direbbe chi c'e'.
    server.upsert_utente({"id": 333, "first_name": "Estraneo",
                          "username": "estraneo"})
    a = c.post("/api/sessioni/attiva", json={"tg_id": 333})
    b = c.post("/api/sessioni/attiva", json={"tg_id": 999_999})
    prova("un account non aperto qui: 400", 400, a.status_code)
    prova("un account inesistente: 400", 400, b.status_code)
    # Identici nel CODICE e nelle parole: un 404 contro un 400 direbbe
    # «questo esiste» anche a messaggio uguale.
    prova("...e i due si raccontano IDENTICI",
          (a.status_code, a.json()), (b.status_code, b.json()))
    prova("un tg_id storto non esplode", 400,
          c.post("/api/sessioni/attiva", json={"tg_id": "pippo"}).status_code)
    prova("...e nemmeno uno che manca", 400,
          c.post("/api/sessioni/attiva", json={}).status_code)
    prova("dopo i rifiuti si e' ancora dove si era", 111,
          c.get("/api/me").json()["tg_id"])

    print("\n[il logout esce da UNO]")
    r = c.post("/api/logout")
    prova("il logout riesce", 200, r.status_code)
    prova("...e si atterra sull'altro account", 222,
          c.get("/api/me").json()["tg_id"])
    prova("...che e' rimasto solo", [222],
          [x["tg_id"] for x in c.get("/api/sessioni").json()["conti"]])

    r = c.post("/api/logout")
    prova("il secondo logout riesce", 200, r.status_code)
    prova("...e ora non si e' piu' nessuno", 401,
          c.get("/api/me").status_code)
    prova("...e la lista e' vuota", [],
          c.get("/api/sessioni").json()["conti"])

    print("\n[il mondo di ieri, intatto]")
    c2 = TestClient(server.app)
    c2.post("/api/login/telegram",
            json={"collaudo": True, "id": 444, "first_name": "Solo"})
    prova("un browser con un account solo entra come sempre", 444,
          c2.get("/api/me").json()["tg_id"])
    c2.post("/api/logout")
    prova("...e il suo logout lo saluta come sempre", 401,
          c2.get("/api/me").status_code)

    print("\n[il tetto]")
    c3 = TestClient(server.app)
    for i, n in enumerate(["Uno", "Due", "Tre", "Quattro"]):
        c3.post("/api/login/telegram",
                json={"collaudo": True, "id": 700 + i, "first_name": n})
    conti = c3.get("/api/sessioni").json()["conti"]
    prova("al tetto (3) restano tre account", 3, len(conti))
    prova("...e a cedere e' il PIU' VECCHIO", [701, 702, 703],
          [x["tg_id"] for x in conti])
    prova("...mentre chi e' appena entrato c'e'", 703,
          c3.get("/api/me").json()["tg_id"])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
