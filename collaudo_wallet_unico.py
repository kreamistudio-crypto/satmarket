# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL WALLET UNICO (2 nov 2026 sera, cantiere wallet-unico).

Alan, nella prova vera: due wallet diversi fra l'app e la mini app di
Telegram. Scelta di Andrea, «Ferma e incolla»: il server sa SE il wallet
c'e' (l'impronta, 8 caratteri pubblici) e il pavimento dei numeri dei
cambi, mai le parole. Qui le tre rotte col server VERO, per HTTP con la
TestClient, su un database usa-e-getta:
  1. un account nuovo non ha wallet (impronta vuota, pavimento 0);
  2. il primo dispositivo registra; la stessa impronta e' ok;
  3. un'ALTRA impronta si ferma (409 «altro», con quella che c'e') e non
     tocca niente — tranne col gesto esplicito `sostituisci`;
  4. le forme storte non passano (400);
  5. un numero si prenota solo per un wallet registrato (409 «nessuno»),
     e sale soltanto: max(minimo, pavimento), poi pavimento = numero + 1;
  6. sostituire il principale non abbassa il pavimento;
  7. due account non si vedono;
  8. nel database c'e' solo quel che si dice: nessuna colonna per parole
     o chiavi.

NON TOCCA NIENTE DI VERO: il `config` finto si installa PRIMA
dell'import di server, nessuna rete, nessun LNbits.

USO:  python collaudo_wallet_unico.py
"""

import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

PASSATE = FALLITE = 0
SRV = None

ALAN = 7111222333
ALTRO = 7444555666


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-wallet-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    # I segreti col setattr e mai come `NOME = "valore"` (lo scanner
    # della CI non distingue una chiave finta da una vera)
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
                 ("DB", db)):
        setattr(cfg, k, v)
    sys.modules["config"] = cfg
    os.chdir(QUI)
    import server
    return server


def h(tg, nome="Prova"):
    return {"X-Tg-Init-Data": f"collaudo:{tg}:{nome}"}


def main():
    global SRV
    SRV = avvio()
    from fastapi.testclient import TestClient
    # senza `with`: l'avvio vero chiederebbe il cambio a CoinGecko
    c = TestClient(SRV.app)

    print("\n[1. un account nuovo non ha wallet]")
    r = c.get("/api/wallet/unico", headers=h(ALAN, "Alan"))
    prova("GET 200", 200, r.status_code)
    prova("impronta vuota, pavimento 0", {"impronta": "", "prossimo": 0, "case": []},
          r.json())
    prova("senza identita' non si legge", True,
          c.get("/api/wallet/unico").status_code in (401, 403))

    print("\n[2. il primo dispositivo registra, la stessa impronta e' ok]")
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "73C5DA0A"})
    prova("registrata (maiuscole ammesse, salvata minuscola)",
          (200, "73c5da0a"), (r.status_code, r.json().get("impronta")))
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "73c5da0a"})
    prova("la stessa: ok", (200, True), (r.status_code, r.json().get("ok")))

    print("\n[3. un'ALTRA impronta si ferma]")
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "deadbeef"})
    prova("409 «altro» con quella che c'e'",
          (409, False, "altro", "73c5da0a"),
          (r.status_code, r.json().get("ok"), r.json().get("motivo"),
           r.json().get("impronta")))
    prova("...e non ha toccato niente", "73c5da0a",
          c.get("/api/wallet/unico", headers=h(ALAN)).json()["impronta"])
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "deadbeef", "sostituisci": "si"})
    prova("`sostituisci` vale solo se e' proprio true", 409, r.status_code)

    print("\n[4. le forme storte non passano]")
    for storta in ("", "73c5da0", "73c5da0a0", "zzzzzzzz", "73c5 da0",
                   None, 12345678):
        r = c.post("/api/wallet/unico", headers=h(ALAN),
                   json={"impronta": storta})
        prova(f"impronta {storta!r}: 400", 400, r.status_code)
    for storto in (-1, "x", 2 ** 31, 1.5e20):
        r = c.post("/api/wallet/unico/numero", headers=h(ALAN),
                   json={"minimo": storto})
        prova(f"minimo {storto!r}: 400", 400, r.status_code)

    print("\n[5. i numeri dei cambi salgono soltanto]")
    r = c.post("/api/wallet/unico/numero", headers=h(ALTRO, "Altro"),
               json={"minimo": 0})
    prova("senza wallet registrato: 409 «nessuno»", (409, "nessuno"),
          (r.status_code, r.json().get("motivo")))
    numeri = []
    for minimo in (0, 0, 7, 3, 8):
        r = c.post("/api/wallet/unico/numero", headers=h(ALAN),
                   json={"minimo": minimo})
        numeri.append(r.json().get("numero"))
    # 0 → 0, 0 → 1 (il pavimento), 7 → 7 (il telefono e' piu' avanti),
    # 3 → 8 (il pavimento vince), 8 → 9
    prova("max(minimo, pavimento), mai due volte lo stesso",
          [0, 1, 7, 8, 9], numeri)
    prova("il pavimento e' 10", 10,
          c.get("/api/wallet/unico", headers=h(ALAN)).json()["prossimo"])

    print("\n[5b. dove stanno le parole: solo il NOME della casa (19 nov 2026, parole-casa)]")
    casa = lambda imp, k, tg=ALAN: c.post("/api/wallet/unico/casa", headers=h(tg),
                                         json={"impronta": imp, "casa": k})
    r = casa("73c5da0a", "nuvola")
    prova("il cloud di Telegram: 200 con la casa", (200, ["nuvola"]),
          (r.status_code, r.json().get("case")))
    prova("...due volte la stessa non cambia niente", ["nuvola"],
          casa("73C5DA0A", "nuvola").json().get("case"))
    prova("...i relay si aggiungono, in ordine fisso", ["nuvola", "relay"],
          casa("73c5da0a", "relay").json().get("case"))
    prova("...e la lettura le dice", ["nuvola", "relay"],
          c.get("/api/wallet/unico", headers=h(ALAN)).json()["case"])
    r = casa("deadbeef", "nuvola")
    prova("un'impronta che non e' la registrata: 409, e non scrive", (409, "altro", ["nuvola", "relay"]),
          (r.status_code, r.json().get("motivo"),
           c.get("/api/wallet/unico", headers=h(ALAN)).json()["case"]))
    for imp, k in (("73c5da0a", "carta"), ("73c5da0a", ""), ("73c5da0a", None),
                   ("73c5da0a", ["nuvola"]), ("zzzz", "nuvola"), (None, "relay")):
        prova(f"casa {k!r} / impronta {imp!r}: 400", 400, casa(imp, k).status_code)
    prova("senza identita' non si scrive", True,
          c.post("/api/wallet/unico/casa", json={"impronta": "73c5da0a",
                 "casa": "nuvola"}).status_code in (401, 403))
    prova("su un account senza wallet: 409", 409, casa("73c5da0a", "nuvola", ALTRO).status_code)

    print("\n[5c. la cassetta della Mini App: il server tiene solo una busta chiusa (19 nov 2026, cassetta-telegram)]")
    P1, P2, DA = "a" * 64, "b" * 64, "c" * 64
    BUSTA = "QWxhZGRpbjpvcGVuIHNlc2FtZQ" * 3
    cas = lambda tg=ALAN: c.get("/api/wallet/cassetta", headers=h(tg)).json()
    chiave = lambda pub, tg=ALAN: c.post("/api/wallet/cassetta", headers=h(tg), json={"pub": pub})
    consegna = lambda imp="73c5da0a", da=DA, busta=BUSTA, tg=ALAN, verso=None: c.post(
        "/api/wallet/cassetta/consegna", headers=h(tg),
        json=dict({"da": da, "busta": busta, "impronta": imp}, **({"verso": verso} if verso else {})))
    prova("all'inizio non c'e' cassetta", {"pub": "", "consegna": None,
                                           "nostr": {"pub": "", "consegna": None}}, cas())
    prova("senza identita' non si legge", True, c.get("/api/wallet/cassetta").status_code in (401, 403))
    prova("il sito consegna prima che la cassetta esista: 409 «nessuna»", (409, "nessuna"),
          (consegna().status_code, consegna().json().get("motivo")))
    # LA PORTA: la pubblica la dice solo la Mini App, mai una sessione del sito
    sito = TestClient(SRV.app)
    sito.cookies.set("barattolo_sessione", SRV.crea_sessione(ALAN))
    prova("col solo cookie del sito la pubblica NON si mette: 403", 403,
          sito.post("/api/wallet/cassetta", json={"pub": P1}).status_code)
    prova("...e non resta scritta", "", cas()["pub"])
    prova("...un initData finto non declassa al cookie: 401", 401,
          sito.post("/api/wallet/cassetta", headers={"X-Tg-Init-Data": "query_id=x&hash=y"},
                    json={"pub": P1}).status_code)
    r = chiave(P1.upper())
    prova("dalla Mini App la pubblica si mette (in minuscolo)", (200, True, P1),
          (r.status_code, r.json().get("nuova"), cas()["pub"]))
    prova("...la stessa due volte non e' nuova", False, chiave(P1).json().get("nuova"))
    for pub in ("", "z" * 64, "a" * 63, None, ["a" * 64], 7):
        prova(f"pubblica {str(pub)[:12]!r}: 400", 400, chiave(pub).status_code)
    prova("un account senza wallet puo' preparare la cassetta", 200, chiave(P2, ALTRO).status_code)
    r = consegna("deadbeef")
    prova("una busta per un'impronta che non e' il principale: 409 «altro»", (409, "altro", None),
          (r.status_code, r.json().get("motivo"), cas()["consegna"]))
    prova("...e all'account senza wallet: 409", 409, consegna(tg=ALTRO).status_code)
    for nome, kw in (("da storto", {"da": "x" * 64}), ("busta corta", {"busta": "QUJD"}),
                     ("busta non base64", {"busta": "<script>" * 10}), ("busta lunga", {"busta": "A" * 4100}),
                     ("impronta storta", {"imp": "zz"}), ("busta assente", {"busta": None})):
        prova(f"consegna con {nome}: 400", 400, consegna(**kw).status_code)
    r = sito.post("/api/wallet/cassetta/consegna", json={"da": DA, "busta": BUSTA, "impronta": "73C5DA0A"})
    prova("IL SITO consegna col suo cookie: 200", 200, r.status_code)
    st = sito.get("/api/wallet/cassetta").json()
    prova("...la busta e' li', identica, con l'impronta", (P1, DA, BUSTA, "73c5da0a", True),
          (st["pub"], st["consegna"]["da"], st["consegna"]["busta"], st["consegna"]["impronta"],
           st["consegna"]["quando"] > 0))
    prova("...l'altro account non la vede", None, cas(ALTRO)["consegna"])
    r = c.post("/api/wallet/cassetta/ritirata", headers=h(ALAN), json={"verso": "tg"})
    prova("la Mini App l'ha ritirata: la busta si butta, la cassetta resta", (200, P1, None),
          (r.status_code, cas()["pub"], cas()["consegna"]))
    consegna()
    chiave(P2)
    prova("una pubblica NUOVA butta la busta chiusa verso la vecchia", (P2, None),
          (cas()["pub"], cas()["consegna"]))

    print("\n[5d. la seconda cassetta, verso la chiave Nostr d'accesso]")
    nb = lambda tg=ALAN: cas(tg)["nostr"]
    prova("senza npub d'accesso: nessuna pubblica, e la consegna dice «nessuna»", ("", 409, "nessuna"),
          (nb()["pub"], consegna(verso="nostr").status_code, consegna(verso="nostr").json().get("motivo")))
    U1, U2 = "1" * 63 + "2", "3" * 63 + "4"
    con = SRV.db()
    con.execute("UPDATE utenti SET npub_accesso=? WHERE tg_id=?", (SRV.hex_to_npub(U1), ALAN))
    con.commit()
    con.close()
    prova("con la npub d'accesso la pubblica e' lei, in esadecimale", (U1, None), (nb()["pub"], nb()["consegna"]))
    prova("un verso sconosciuto: 400", 400, consegna(verso="carta").status_code)
    prova("...un'impronta che non e' il principale: 409", 409, consegna("deadbeef", verso="nostr").status_code)
    r = consegna(verso="nostr")
    prova("LA MINI APP consegna verso Nostr: 200, e la busta e' li'", (200, DA, BUSTA, "73c5da0a"),
          (r.status_code, nb()["consegna"]["da"], nb()["consegna"]["busta"], nb()["consegna"]["impronta"]))
    prova("...la busta verso Telegram non si tocca", None, cas()["consegna"])
    con = SRV.db()
    con.execute("UPDATE utenti SET npub_accesso=? WHERE tg_id=?", (SRV.hex_to_npub(U2), ALAN))
    con.commit()
    con.close()
    prova("la npub d'accesso cambia: la busta chiusa verso la vecchia non si mostra", (U2, None),
          (nb()["pub"], nb()["consegna"]))
    consegna(verso="nostr")
    r = sito.post("/api/wallet/cassetta/ritirata", json={"verso": "nostr"})
    prova("il sito l'ha ritirata (i relay ce l'hanno): via", (200, None), (r.status_code, nb()["consegna"]))
    prova("ritirata con un verso sconosciuto, o senza corpo: 400", [400, 400],
          [c.post("/api/wallet/cassetta/ritirata", headers=h(ALAN), json={"verso": "x"}).status_code,
           c.post("/api/wallet/cassetta/ritirata", headers=h(ALAN)).status_code])
    prova("l'altro account non vede la busta di Alan", {"pub": "", "consegna": None}, nb(ALTRO))

    print("\n[6. sostituire il principale non abbassa il pavimento]")
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "deadbeef", "sostituisci": True})
    prova("sostituito", (200, True, "deadbeef"),
          (r.status_code, r.json().get("sostituito"), r.json().get("impronta")))
    prova("pavimento ancora 10, e le case ripartono da zero (erano dell'altro)",
          {"impronta": "deadbeef", "prossimo": 10, "case": []},
          c.get("/api/wallet/unico", headers=h(ALAN)).json())
    r = c.post("/api/wallet/unico/numero", headers=h(ALAN), json={"minimo": 0})
    prova("il numero dopo e' 10", 10, r.json().get("numero"))
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "73c5da0a"})
    prova("le parole di PRIMA non tornano principali da sole", 409,
          r.status_code)

    print("\n[7. due account non si vedono]")
    prova("l'altro e' ancora vuoto", {"impronta": "", "prossimo": 0, "case": []},
          c.get("/api/wallet/unico", headers=h(ALTRO)).json())
    r = c.post("/api/wallet/unico", headers=h(ALTRO, "Altro"),
               json={"impronta": "73c5da0a"})
    prova("la stessa impronta su un altro account: affar suo", 200,
          r.status_code)
    r = c.post("/api/wallet/unico/numero", headers=h(ALTRO), json={})
    prova("il suo primo numero e' 0", 0, r.json().get("numero"))
    prova("Alan non si e' mosso", 11,
          c.get("/api/wallet/unico", headers=h(ALAN)).json()["prossimo"])

    print("\n[8. nel database solo quel che si dice]")
    con = SRV.db()
    colonne = [x[1] for x in con.execute("PRAGMA table_info(wallet_unico)")]
    colonne_cassetta = [x[1] for x in con.execute("PRAGMA table_info(wallet_cassetta)")]
    con.close()
    # (19 nov 2026, parole-casa) `case_copie`: solo nomi di case
    prova("le colonne", ["tg_id", "impronta", "prossimo", "creato",
                         "aggiornato", "case_copie"], colonne)
    # (19 nov 2026, cassetta-telegram) la pubblica e la busta chiusa: mai parole
    prova("le colonne della cassetta", ["tg_id", "verso", "pub", "da", "busta", "impronta",
                                        "consegnata", "aggiornato"], colonne_cassetta)

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
