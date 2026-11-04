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
    lungo sono un 400, il freno morde al 21° messaggio dell'ora.

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
    c.post("/api/assistenza", json={"testo": "Mi aiutate?"}, headers=VENDE)
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
    prova("due conversazioni, una per utente, l'ultima mossa prima", [222, 111],
          [x["utente"] for x in el])
    prova("...tutte e due da rispondere", [True, True], [x["da_rispondere"] for x in el])
    prova("...coi nomi", ["Venditore", "Compratore"], [x["nome"] for x in el])
    prova("...e i conti dei messaggi", [1, 1], [x["messaggi"] for x in el])

    print("\n[lo staff risponde]")
    r = c.post("/api/admin/assistenza/111", json={"testo": "Guardo subito l'ordine 12"},
               headers=ADMIN)
    prova("la risposta entra", 200, r.status_code)
    prova("...e per gli admin dice chi ha risposto", "Admin", r.json()["messaggi"][-1].get("chi"))
    prova("l'utente riceve UN avviso", 1, len([a for a in avvisi if a[0] == 111]))
    prova("...che NON porta il testo della risposta", False,
          "Guardo subito" in avvisi[-1][1])
    prova("...e ha il bottone per aprire Barattolo", True, bool(avvisi[-1][2]))
    el = c.get("/api/admin/assistenza", headers=ADMIN).json()["conversazioni"]
    prova("la conversazione del compratore torna in cima, non piu' da rispondere",
          (111, False), (el[0]["utente"], el[0]["da_rispondere"]))
    prova("rispondere a chi non esiste e' un 404", 404,
          c.post("/api/admin/assistenza/424242", json={"testo": "ciao"},
                 headers=ADMIN).status_code)

    print("\n[l'utente legge la risposta]")
    prova("/api/me conta una risposta nuova", 1,
          c.get("/api/me", headers=COMPRA).json().get("assistenza_nuove"))
    msgs = c.get("/api/assistenza", headers=COMPRA).json()["messaggi"]
    prova("la risposta e' dello staff, senza il nome dell'admin", (True, None),
          (msgs[-1]["staff"], msgs[-1].get("chi")))
    prova("aperta la conversazione, il pallino si spegne", 0,
          c.get("/api/me", headers=COMPRA).json().get("assistenza_nuove"))

    print("\n[il freno: venti messaggi l'ora per persona]")
    S._SECCHI.clear()
    stati = [c.post("/api/assistenza", json={"testo": f"n. {i}"}, headers=VENDE).status_code
             for i in range(21)]
    prova("venti passano, il ventunesimo e' un 429", [200] * 20 + [429], stati)
    S._SECCHI.clear()

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
