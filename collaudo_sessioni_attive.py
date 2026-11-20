# -*- coding: utf-8 -*-
"""
LE SESSIONI ATTIVE, SUL SERVER VERO (20 nov 2026, audit del venerdi'
giro 4; Alan: «da una sessione piu vecchia si possono chiudere le
sessioni piu giovani e si possono sempre vedere le sessioni attive»).

Qui rispondono le due rotte vere, `/api/me/sessioni-attive` e
`/api/me/sessioni-attive/chiudi`, su tre sessioni web dello stesso
account nate in tre momenti diversi:

  1. dalla sessione di MEZZO: le vede tutte e tre, la sua e' «questa»,
     chiude solo la piu' GIOVANE (la piu' vecchia: 403);
  2. la sessione chiusa non entra piu' (401);
  3. dalla Mini App (initData del proprio Telegram) si chiudono tutte;
  4. un id che non e' dell'account: 404; un id storto: 400;
  5. il nome del dispositivo nasce con la sessione, dallo user agent.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_sessioni_attive.py
"""

import hashlib
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  LE SESSIONI ATTIVE")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient
    SRV = banco.SRV
    TG, ALTRO = 701, 702
    mini = {"X-Tg-Init-Data": f"collaudo:{TG}:Anna"}

    c = TestClient(SRV.app)
    r = c.get("/api/me/sessioni-attive", headers=mini)
    prova("dalla Mini App, senza sessioni nel browser: mini e lista vuota",
          (200, True, []), (r.status_code, r.json().get("mini"), r.json().get("sessioni")))
    c.get("/api/me/sessioni-attive", headers={"X-Tg-Init-Data": f"collaudo:{ALTRO}:Bruno"})

    # tre sessioni dello stesso account, nate in tre momenti
    adesso = int(time.time())
    tok = [SRV.crea_sessione(TG) for _ in range(3)]
    altro = SRV.crea_sessione(ALTRO)
    con = SRV.db()
    for n, t in enumerate(tok):
        con.execute("UPDATE sessioni SET creato=? WHERE token_hash=?",
                    (adesso - 300 + n * 100, hashlib.sha256(t.encode()).hexdigest()))
    con.commit()
    con.close()
    ids = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in tok]
    id_altro = hashlib.sha256(altro.encode()).hexdigest()[:16]

    print("\n[dalla sessione di mezzo]")
    web = TestClient(SRV.app)
    web.cookies.set("barattolo_sessione", tok[1])
    d = web.get("/api/me/sessioni-attive").json()
    prova("le vede tutte e tre, dalla piu' vecchia; non e' la Mini App",
          (False, ids), (d["mini"], [s["id"] for s in d["sessioni"]]))
    prova("...la sua e' «questa»; si chiude solo la piu' giovane",
          ([False, True, False], [False, False, True]),
          ([s["questa"] for s in d["sessioni"]], [s["chiudibile"] for s in d["sessioni"]]))
    prova("...senza l'altro account", True, id_altro not in [s["id"] for s in d["sessioni"]])
    prova("...e il token non esce mai", True,
          all(t not in str(d) for t in tok))
    prova("la piu' vecchia da qui non si chiude: 403", 403,
          web.post("/api/me/sessioni-attive/chiudi", json={"id": ids[0]}).status_code)
    prova("...e nemmeno la propria (si esce con «Esci»): 403", 403,
          web.post("/api/me/sessioni-attive/chiudi", json={"id": ids[1]}).status_code)
    r = web.post("/api/me/sessioni-attive/chiudi", json={"id": ids[2]})
    prova("la piu' giovane si chiude: 200, una", (200, 1), (r.status_code, r.json().get("chiuse")))
    giovane = TestClient(SRV.app)
    giovane.cookies.set("barattolo_sessione", tok[2])
    prova("...e quel browser non entra piu': 401", 401,
          giovane.get("/api/me/sessioni-attive").status_code)
    prova("un id dell'altro account: 404", 404,
          web.post("/api/me/sessioni-attive/chiudi", json={"id": id_altro}).status_code)
    prova("un id storto: 400", [400, 400],
          [web.post("/api/me/sessioni-attive/chiudi", json={"id": "zz"}).status_code,
           web.post("/api/me/sessioni-attive/chiudi", json={}).status_code])

    print("\n[dalla Mini App]")
    d = c.get("/api/me/sessioni-attive", headers=mini).json()
    prova("la Mini App le chiude tutte (anche la piu' vecchia)",
          (True, [True, True]), (d["mini"], [s["chiudibile"] for s in d["sessioni"]]))
    r = c.post("/api/me/sessioni-attive/chiudi", headers=mini, json={"id": ids[0]})
    prova("...e la piu' vecchia si chiude", 200, r.status_code)
    prova("...l'altro account resta aperto", 200,
          TestClient(SRV.app, cookies={"barattolo_sessione": altro})
          .get("/api/me/sessioni-attive").status_code)

    print("\n[il nome del dispositivo]")
    con = SRV.db()
    riga = con.execute("SELECT dispositivo FROM dispositivi_sessione WHERE token_hash=?",
                       (hashlib.sha256(tok[1].encode()).hexdigest(),)).fetchone()
    con.close()
    prova("nasce con la sessione (fuori da una richiesta: «Browser»)", "Browser",
          riga and riga[0])
    prova("dallo user agent, solo browser e sistema",
          ["Chrome su Windows", "Safari su iPhone", "Firefox su Linux",
           "Edge su Windows", "Browser"],
          [SRV.nome_dispositivo("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"),
           SRV.nome_dispositivo("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 "
                                "Mobile/15E148 Safari/604.1"),
           SRV.nome_dispositivo("Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 "
                                "Firefox/133.0"),
           SRV.nome_dispositivo("Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/131.0 "
                                "Safari/537.36 Edg/131.0"),
           SRV.nome_dispositivo("")])

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
