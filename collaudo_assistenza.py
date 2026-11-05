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
    prova("due conversazioni, una per utente, l'ultima mossa prima", [222, 111],
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
          (111, False), (el[0]["utente"], el[0]["da_rispondere"]))
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

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
