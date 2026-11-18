# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA VETRINA CHE SI PULISCE (18 nov 2026, cantiere
vetrina-pulita; un utente: «Avrebbe senso mettere i messaggi effimeri per
gli annunci di Barattolo Vetrina in modo tale che spariscano quando sono
scaduti o presi?», Andrea: «Sì, aprila»).

`prove.py` fa girare il giudice e le funzioni su un sqlite di banco; qui
risponde il SERVER VERO, col suo database e le sue migrazioni:
- `/api/p2p/canale` ricorda i post usciti nei tre canali (con l'id
  dell'ordine, o senza quando il telefono ha ancora il nome provvisorio);
- l'orologio collega il provvisorio all'ordine dichiarato, e toglie i post
  degli ordini che la fotografia del libro dice usciti;
- la parola di mostrod (preso) li toglie subito;
- l'annuncio venduto perde il post invece di prendere il ✅;
- a leva spenta tutto com'era.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco,
la fabbrica dei post e `bot_api` sono di cartone e annotano. Nessuna rete.

USO:  python collaudo_vetrina_pulita.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  LA VETRINA CHE SI PULISCE — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)

    # i tre canali di cartone: la fabbrica dei post da' un message_id nuovo
    # a ogni invio, `bot_api` annota cancellazioni e riscritture
    contatore = {"n": 100}
    mandati, telegram = [], []

    async def annota(dove, caption, foto):
        contatore["n"] += 1
        mandati.append((dove, contatore["n"]))
        return contatore["n"]

    risposta = {"f": lambda metodo: {"ok": True}}

    async def bot_api(metodo, dati):
        telegram.append((metodo, dati.get("chat_id"), dati.get("message_id")))
        return risposta["f"](metodo)

    S._manda_post_canale = annota
    S.bot_api = bot_api
    S.canale_id = lambda: "@casa"
    S.canale_vetrina = lambda: "@subito"
    S.canale_bitcoin_podcast = lambda: "@podcast"
    S._p2p_per = lambda tg: {"attivo": True}
    S._foto_subito_p2p = lambda *a: None
    con = S.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,registrato) "
                "VALUES(5501,'Tele','tele','neg5501',1)")
    con.commit()
    con.close()

    def posta(corpo, tg=5501):
        S._SECCHI.clear()
        S._CANALE_POSTATI.clear()
        con = S.db()
        con.execute("UPDATE utenti SET promo_canale_il=0, promo_vetrina_p2p_il=0 WHERE tg_id=?",
                    (tg,))
        con.commit()
        con.close()
        S.verifica_utente = lambda *a, **k: {"id": tg}
        mandati.clear()
        return c.post("/api/p2p/canale", json=corpo)

    def righe():
        con = S.db()
        r = sorted(tuple(x) for x in con.execute(
            "SELECT canale, message_id, ordine, tg_id FROM post_p2p_canale"))
        con.close()
        return r

    print("\n[la rotta del canale ricorda i post usciti]")
    A = "aaaaaaaa-1111-2222-3333-444444444444"
    r = posta({"lato": "vendo", "euro": 50, "metodo": "SEPA", "ordine": A})
    prova("il post esce nei tre canali, e il server ricorda dove, con l'id dell'ordine",
          (200, True, [("@casa", 101, A, 5501), ("@podcast", 103, A, 5501),
                       ("@subito", 102, A, 5501)]),
          (r.status_code, r.json().get("postato"), righe()))
    adesso = int(time.time())
    r = posta({"lato": "compro", "euro": 30, "metodo": "Revolut"})
    prova("...col nome ancora provvisorio il post si ricorda lo stesso, senza ordine",
          (200, [("@casa", 104, "", 5501), ("@podcast", 106, "", 5501), ("@subito", 105, "", 5501)]),
          (r.status_code, [x for x in righe() if x[2] == ""]))

    print("\n[l'orologio: collega il provvisorio e toglie l'ordine preso]")
    B = "bbbbbbbb-1111-2222-3333-444444444444"
    con = S.db()
    con.execute("INSERT INTO p2p_ordini(ordine, tg_id, creato, maker) VALUES(?,?,?,1)",
                (B, 5501, adesso + 20))
    con.commit()
    con.close()
    ev = lambda d, s: {"kind": 38383, "created_at": adesso, "tags": [["d", d], ["s", s]]}
    S._P2P_FOTO.update(quando=adesso, ultimi={A: ev(A, "in-progress"), B: ev(B, "pending")},
                       via={})
    telegram.clear()
    asyncio.run(S._giro_post_p2p_canale())
    prova("i tre post dell'ordine preso si cancellano; quelli del provvisorio prendono il suo "
          "ordine e restano, perche' e' vivo",
          ([("deleteMessage", "@casa", 101), ("deleteMessage", "@podcast", 103),
            ("deleteMessage", "@subito", 102)],
           [("@casa", 104, B, 5501), ("@podcast", 106, B, 5501), ("@subito", 105, B, 5501)]),
          (sorted(telegram), righe()))

    print("\n[la parola di mostrod: preso, e il post esce subito]")
    telegram.clear()
    prima_leve = S._p2p_leve
    S._p2p_leve = lambda: {"attivo": True}

    async def evento():
        S._foto_dopo_evento_p2p({"ordine": B, "momento": "preso", "ts": adesso + 30})
        await asyncio.gather(*list(S._TASK_POST_P2P))
    asyncio.run(evento())
    S._p2p_leve = prima_leve
    prova("i tre post dell'ordine preso escono dai canali, e il server li dimentica",
          ([("deleteMessage", "@casa", 104), ("deleteMessage", "@podcast", 106),
            ("deleteMessage", "@subito", 105)], []),
          (sorted(telegram), righe()))

    print("\n[oltre le 48 ore: il post si riscrive]")
    C = "cccccccc-1111-2222-3333-444444444444"
    posta({"lato": "vendo", "euro": 20, "metodo": "SEPA", "ordine": C})
    telegram.clear()
    risposta["f"] = lambda metodo: {"ok": metodo == "editMessageText",
                                    "description": "Bad Request: message can't be deleted"}
    S._P2P_FOTO.update(quando=adesso, ultimi={C: {"kind": 38383, "created_at": adesso,
                                                  "tags": [["d", C], ["s", "pending"],
                                                           ["expires_at", str(adesso - 1)]]}})
    asyncio.run(S._giro_post_p2p_canale())
    prova("l'ordine scaduto: la cancellazione non passa, ogni post si riscrive, e il server li "
          "dimentica", (["deleteMessage", "editMessageText"] * 3, []),
          ([m for m, _, _ in telegram], righe()))
    risposta["f"] = lambda metodo: {"ok": True}

    print("\n[a leva spenta, tutto com'era]")
    D = "dddddddd-1111-2222-3333-444444444444"
    posta({"lato": "vendo", "euro": 20, "metodo": "SEPA", "ordine": D})
    S.VETRINA_SI_PULISCE = False
    telegram.clear()
    S._P2P_FOTO.update(quando=adesso, ultimi={D: ev(D, "canceled")})
    asyncio.run(S._giro_post_p2p_canale())
    prova("nessun post si tocca, e i riferimenti restano", ([], 3),
          (telegram, len(righe())))

    print("\n[l'annuncio venduto: il post sparisce invece del ✅]")
    con = S.db()
    cur = con.execute("INSERT INTO annunci(venditore_id, titolo, descrizione, prezzo_sats, "
                      "categoria, stato, post_canale_id, post_vetrina_id, "
                      "post_bitcoin_podcast_id) VALUES(5501,'Lampada','x',1000,'casa',"
                      "'venduto',71,72,73)")
    aid = cur.lastrowid
    con.commit()
    con.close()

    def post_annuncio():
        con = S.db()
        r = tuple(con.execute("SELECT post_canale_id, post_vetrina_id, post_bitcoin_podcast_id "
                              "FROM annunci WHERE id=?", (aid,)).fetchone())
        con.close()
        return r
    telegram.clear()
    asyncio.run(S.promo_venduto(aid))
    prova("leva spenta: il venduto riscrive i tre post col ✅, come prima",
          (["editMessageText"] * 3, (71, 72, 73)),
          ([m for m, _, _ in telegram], post_annuncio()))
    # (venduto-resta, 18 nov 2026; Andrea: «Tieni il ✅ Venduto») di serie
    # la vetrina si pulisce ma il venduto del mercatino resta col ✅
    S.VETRINA_SI_PULISCE = True
    telegram.clear()
    asyncio.run(S.promo_venduto(aid))
    prova("di serie (leva del venduto spenta): il ✅ anche con la vetrina che si pulisce",
          (False, ["editMessageText"] * 3, (71, 72, 73)),
          (S.VETRINA_VENDUTI_SI_CANCELLANO, [m for m, _, _ in telegram], post_annuncio()))
    S.VETRINA_VENDUTI_SI_CANCELLANO = True
    telegram.clear()
    asyncio.run(S.promo_venduto(aid))
    prova("leva del venduto accesa: i tre post si cancellano, e le colonne tornano a zero",
          ([("deleteMessage", "@casa", 71), ("deleteMessage", "@subito", 72),
            ("deleteMessage", "@podcast", 73)], (0, 0, 0)),
          (telegram, post_annuncio()))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
