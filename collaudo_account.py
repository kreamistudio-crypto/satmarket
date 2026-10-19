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
    login e il logout esattamente come prima;
  · LA SESSIONE DI IERI si adotta — chi era gia' dentro prima del
    deploy ha il cookie della sessione e nessun mazzo, e il menu gli si
    apriva VUOTO: qui il caso si riproduce invece di descriverlo;
  · LA PORTA NOSTR mette la sua riga nel mazzo senza buttare fuori chi
    c'era: e' quella da cui si entra col secondo account.
  · IL RIENTRO CHIUDE LA VECCHIA (19 ott 2026, cantiere account-doppio):
    chi rientra sullo stesso account prende una sessione nuova, e quella
    vecchia — uscita dal mazzo — non apre piu' niente, nemmeno da un
    altro browser che l'avesse copiata; l'altro account resta aperto. Lo
    stesso AL TETTO: chi cede il posto si chiude anche nel database.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
chiave, nessuna rete, nessun LNbits.

USO:  python collaudo_account.py
"""

import hashlib
import json
import os
import sys
import tempfile
import time
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
    chiavi = {}
    for i, n in enumerate(["Uno", "Due", "Tre", "Quattro"]):
        c3.post("/api/login/telegram",
                json={"collaudo": True, "id": 700 + i, "first_name": n})
        chiavi[700 + i] = c3.cookies.get("barattolo_sessione")
    conti = c3.get("/api/sessioni").json()["conti"]
    prova("al tetto (3) restano tre account", 3, len(conti))
    prova("...e a cedere e' il PIU' VECCHIO", [701, 702, 703],
          [x["tg_id"] for x in conti])
    prova("...mentre chi e' appena entrato c'e'", 703,
          c3.get("/api/me").json()["tg_id"])
    # CHI CEDE SI CHIUDE ANCHE NEL DATABASE (19 ott 2026, cantiere
    # account-doppio): la sua sessione, provata da un ALTRO browser che
    # l'avesse copiata, non apre piu' niente; gli altri tre si'.
    def da_fuori(tok):
        b = TestClient(server.app)
        b.cookies.set("barattolo_sessione", tok)
        return b.get("/api/me").status_code
    prova("la sessione di chi ha ceduto il posto: 401", 401, da_fuori(chiavi[700]))
    prova("...e gli altri tre restano 200", [200, 200, 200],
          [da_fuori(chiavi[k]) for k in (701, 702, 703)])

    # ------------------------------------------------------------------
    # LA SESSIONE DI IERI (ago 2026, il caso dal campo: «non riesco a
    # switchare nonostante il commit sia in prod»). Chi era gia' dentro
    # PRIMA del deploy ha il cookie della sessione e nessun mazzo: il
    # menu gli si apriva senza nemmeno il SUO account, cioe' senza
    # niente fra cui passare. Qui la sessione si crea A MANO come faceva
    # il codice di ieri, quindi il caso si RIPRODUCE invece di essere
    # descritto: se un domani l'adozione cade, questa riga lo MOSTRA.
    # ------------------------------------------------------------------
    print("\n[la sessione di ieri, adottata]")
    server.upsert_utente({"id": 811, "first_name": "Chi C'era",
                          "username": "prima"})
    c4 = TestClient(server.app)
    c4.cookies.set("barattolo_sessione", server.crea_sessione(811))
    d4 = c4.get("/api/sessioni").json()
    prova("chi era dentro da ieri si vede nel menu", [811],
          [x["tg_id"] for x in d4["conti"]])
    prova("...ed e' segnato come attivo", 811, d4["attivo"])
    c4.post("/api/login/telegram",
            json={"collaudo": True, "id": 812, "first_name": "L'Altro"})
    prova("...e aggiungendo un account resta con DUE", [811, 812],
          [x["tg_id"] for x in c4.get("/api/sessioni").json()["conti"]])
    c4.post("/api/sessioni/attiva", json={"tg_id": 811})
    prova("...con quello di ieri ancora raggiungibile", 811,
          c4.get("/api/me").json()["tg_id"])

    # ------------------------------------------------------------------
    # LA PORTA NOSTR, che il collaudo non copriva: e' quella da cui si
    # entra col secondo account, e passa da apri_sessione come le
    # sorelle — quindi deve mettere la sua riga nel mazzo senza buttare
    # fuori chi c'era. La firma e' VERA (Schnorr), o non si proverebbe
    # la porta ma un ramo di collaudo.
    # ------------------------------------------------------------------
    print("\n[la porta Nostr]")
    try:
        from coincurve import PrivateKey
    except ImportError:
        print("  · coincurve non c'e': la porta Nostr si SALTA")
    else:
        c5 = TestClient(server.app)
        c5.post("/api/login/telegram",
                json={"collaudo": True, "id": 821, "first_name": "Telegram"})
        sk = PrivateKey()
        pub = sk.public_key_xonly.format().hex()
        sfida = c5.get("/api/login/nostr/sfida").json()["sfida"]
        ev = {"pubkey": pub, "created_at": int(time.time()), "kind": 22242,
              "tags": [["relay", "http://testserver"], ["challenge", sfida]],
              "content": ""}
        ser = json.dumps([0, pub, ev["created_at"], 22242, ev["tags"], ""],
                         separators=(",", ":"), ensure_ascii=False)
        ev["id"] = hashlib.sha256(ser.encode()).hexdigest()
        ev["sig"] = sk.sign_schnorr(bytes.fromhex(ev["id"])).hex()
        prova("si entra con la chiave Nostr", 200,
              c5.post("/api/login/nostr", json={"evento": ev}).status_code)
        conti5 = c5.get("/api/sessioni").json()["conti"]
        prova("...e nel mazzo ci sono TUTTI E DUE", 2, len(conti5))
        prova("...col Telegram che c'era prima ancora al suo posto", True,
              821 in [x["tg_id"] for x in conti5])
        nativo = [x["tg_id"] for x in conti5 if x["tg_id"] != 821]
        prova("...e il nativo Nostr ha il tg_id NEGATIVO", True,
              bool(nativo) and nativo[0] < 0)
        c5.post("/api/sessioni/attiva", json={"tg_id": 821})
        prova("si torna sul Telegram con un tocco", 821,
              c5.get("/api/me").json()["tg_id"])

        # E il RIENTRO con la STESSA chiave, che e' un ramo DIVERSO
        # (npub_accesso: l'account c'e' gia'). Senza questo caso la
        # mutazione che gli toglie la sessione sopravvive, perche' la
        # parola la porta comunque il ramo del nativo nuovo.
        c6 = TestClient(server.app)
        c6.post("/api/login/telegram",
                json={"collaudo": True, "id": 831, "first_name": "Prima"})
        sfida2 = c6.get("/api/login/nostr/sfida").json()["sfida"]
        ev2 = {"pubkey": pub, "created_at": int(time.time()), "kind": 22242,
               "tags": [["relay", "http://testserver"], ["challenge", sfida2]],
               "content": ""}
        ser2 = json.dumps([0, pub, ev2["created_at"], 22242, ev2["tags"], ""],
                          separators=(",", ":"), ensure_ascii=False)
        ev2["id"] = hashlib.sha256(ser2.encode()).hexdigest()
        ev2["sig"] = sk.sign_schnorr(bytes.fromhex(ev2["id"])).hex()
        r6 = c6.post("/api/login/nostr", json={"evento": ev2})
        prova("si RIENTRA con una chiave gia' collegata", 200,
              r6.status_code)
        prova("...e anche di li' il mazzo resta di DUE", 2,
              len(c6.get("/api/sessioni").json()["conti"]))
        c6.post("/api/sessioni/attiva", json={"tg_id": 831})
        prova("...col Telegram di prima ancora raggiungibile", 831,
              c6.get("/api/me").json()["tg_id"])

        # LA SFIDA NEL DATABASE (19 ott 2026, cantiere logout-apk): sta
        # nella tabella e non in memoria, quindi un deploy fra la sfida
        # e la firma non la perde; e resta monouso.
        print("\n[la sfida nel database]")
        c8 = TestClient(server.app)
        sfida3 = c8.get("/api/login/nostr/sfida").json()["sfida"]
        con = server.db()
        n = con.execute("SELECT COUNT(*) n FROM sfide_login WHERE sfida=?",
                        (sfida3,)).fetchone()["n"]
        con.close()
        prova("la sfida chiesta sta nel database (sopravvive al riavvio)", 1, n)
        ev3 = {"pubkey": pub, "created_at": int(time.time()), "kind": 22242,
               "tags": [["relay", "http://testserver"], ["challenge", sfida3]],
               "content": ""}
        ser3 = json.dumps([0, pub, ev3["created_at"], 22242, ev3["tags"], ""],
                          separators=(",", ":"), ensure_ascii=False)
        ev3["id"] = hashlib.sha256(ser3.encode()).hexdigest()
        ev3["sig"] = sk.sign_schnorr(bytes.fromhex(ev3["id"])).hex()
        prova("...si entra con lei", 200,
              c8.post("/api/login/nostr", json={"evento": ev3}).status_code)
        con = server.db()
        n = con.execute("SELECT COUNT(*) n FROM sfide_login WHERE sfida=?",
                        (sfida3,)).fetchone()["n"]
        con.close()
        prova("...e dopo il login la sfida non c'e' piu'", 0, n)
        prova("...la stessa firma una seconda volta: no", 401,
              TestClient(server.app).post("/api/login/nostr",
                                          json={"evento": ev3}).status_code)

    print("\n[il rientro chiude la vecchia]")
    c7 = TestClient(server.app)
    c7.post("/api/login/telegram",
            json={"collaudo": True, "id": 151, "first_name": "AndreAI"})
    vecchia = c7.cookies.get("barattolo_sessione")
    c7.post("/api/login/telegram",
            json={"collaudo": True, "id": 152, "first_name": "Negozio"})
    altra = c7.cookies.get("barattolo_sessione")
    # il tocco sul widget con lo STESSO account: la porta e' la stessa
    c7.post("/api/login/telegram",
            json={"collaudo": True, "id": 151, "first_name": "AndreAI"})
    nuova = c7.cookies.get("barattolo_sessione")
    prova("il rientro da' una sessione nuova", True, nuova != vecchia)
    prova("...e il browser resta su di lui, col mazzo di DUE", (151, 2),
          (c7.get("/api/me").json()["tg_id"],
           len(c7.get("/api/sessioni").json()["conti"])))
    # un ALTRO browser con la vecchia copiata: e' la chiave in giro
    ladro = TestClient(server.app)
    ladro.cookies.set("barattolo_sessione", vecchia)
    prova("la sessione VECCHIA non apre piu' niente", 401,
          ladro.get("/api/me").status_code)
    altro_br = TestClient(server.app)
    altro_br.cookies.set("barattolo_sessione", altra)
    prova("...l'altro account del mazzo resta aperto", 152,
          altro_br.get("/api/me").json()["tg_id"])
    con = server.db()
    n151 = con.execute("SELECT COUNT(*) n FROM sessioni WHERE tg_id=151").fetchone()["n"]
    con.close()
    prova("...e nel database c'e' UNA sola sessione sua", 1, n151)

    # LA TRACCIA NEL JOURNAL (19 ott 2026, cantiere logout-apk): il
    # logout vero, per la rotta vera, scrive la sua riga — senza token.
    print("\n[la traccia delle chiusure]")
    import contextlib
    import io
    c9 = TestClient(server.app)
    c9.post("/api/login/telegram",
            json={"collaudo": True, "id": 161, "first_name": "Traccia"})
    tok9 = c9.cookies.get("barattolo_sessione")
    giornale = io.StringIO()
    with contextlib.redirect_stdout(giornale):
        r9 = c9.post("/api/logout")
    prova("il logout risponde come sempre", 200, r9.status_code)
    prova("...e il journal dice quante e perche'", True,
          "🔑 Sessioni chiuse: 1 (logout)" in giornale.getvalue())
    prova("...senza il token, senza l'id, senza il nome", False,
          any(x in giornale.getvalue() for x in (tok9, "161", "Traccia")))

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
