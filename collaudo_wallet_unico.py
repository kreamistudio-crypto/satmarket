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
    prova("impronta vuota, pavimento 0", {"impronta": "", "prossimo": 0},
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

    print("\n[6. sostituire il principale non abbassa il pavimento]")
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "deadbeef", "sostituisci": True})
    prova("sostituito", (200, True, "deadbeef"),
          (r.status_code, r.json().get("sostituito"), r.json().get("impronta")))
    prova("pavimento ancora 10", {"impronta": "deadbeef", "prossimo": 10},
          c.get("/api/wallet/unico", headers=h(ALAN)).json())
    r = c.post("/api/wallet/unico/numero", headers=h(ALAN), json={"minimo": 0})
    prova("il numero dopo e' 10", 10, r.json().get("numero"))
    r = c.post("/api/wallet/unico", headers=h(ALAN, "Alan"),
               json={"impronta": "73c5da0a"})
    prova("le parole di PRIMA non tornano principali da sole", 409,
          r.status_code)

    print("\n[7. due account non si vedono]")
    prova("l'altro e' ancora vuoto", {"impronta": "", "prossimo": 0},
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
    con.close()
    prova("le colonne", ["tg_id", "impronta", "prossimo", "creato",
                         "aggiornato"], colonne)

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
