# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ISTANZA DI PROVA (19 ott 2026, cantiere «collaudo-vm»,
richiesta di Andrea; il disegno e' docs/STUDIO-ISTANZA-PROVA-2026-10-08.md).

`prove.py` prova i giudici puri (`_prova_decide`, `_prova_esente`,
`_bot_nella_pagina`) e le leve lette dal config; qui risponde il SERVER
VERO, col middleware davanti a tutte le rotte:
  - a leva spenta (la produzione) nessuno riceve il 403 della prova;
  - a leva accesa chi e' in lista passa, chi si fa riconoscere e non c'e'
    riceve 403 — anche col cookie del login web — e NON finisce nemmeno
    scritto nel database; chi non si fa riconoscere legge e basta;
  - la salute, il campanello del bot e il login restano come sono;
  - la pagina porta il bot della leva LINK_BOT nella sua riga, e col bot
    di serie esce identica.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco
(MODALITA_COLLAUDO, le identita' «collaudo:<id>:<nome>»). Le leve si
girano sul modulo gia' importato: il middleware le legge a ogni
richiesta, la pagina a ogni rilettura. Nessuna rete.

USO:  python collaudo_istanza_prova.py
"""

import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def chi(n, nome="Prova"):
    return {"X-Tg-Init-Data": f"collaudo:{n}:{nome}"}


def main():
    print("=" * 58)
    print("  L'ISTANZA DI PROVA — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    PRIVATA = {"detail": S.MSG_PROVA_PRIVATA}

    print("\n[a leva spenta: la produzione, nessun filtro]")
    prova("la leva nasce vuota (il config finto non la dichiara)", set(),
          S.PROVA_SOLO_IDS)
    prova("chiunque si riconosca entra: 222 apre /api/me", 200,
          c.get("/api/me", headers=chi(222, "Venditore")).status_code)
    prova("...e anche 444", 200, c.get("/api/me", headers=chi(444)).status_code)
    spento_post = c.post("/api/orders", json={})
    prova("un gesto senza identita' non e' il 403 della prova (e' quello di sempre)",
          False, spento_post.json() == PRIVATA)
    webhook_spento = c.post("/api/telegram/aggiornamenti", json={})
    sfida_spenta = c.get("/api/login/nostr/sfida").status_code
    token_222 = S.crea_sessione(222)
    token_111 = None

    print("\n[a leva accesa: solo 111]")
    S.PROVA_SOLO_IDS = {111}
    prova("111 entra", 200, c.get("/api/me", headers=chi(111, "Compratore")).status_code)
    token_111 = S.crea_sessione(111)
    r = c.get("/api/me", headers=chi(222, "Venditore"))
    prova("222 si riconosce ma non e' in lista: 403 col suo perche'",
          (403, PRIVATA), (r.status_code, r.json()))
    prova("...anche per un gesto", 403,
          c.post("/api/orders", json={}, headers=chi(222)).status_code)
    prova("...e col solo cookie del login web", 403,
          c.get("/api/me", cookies={"barattolo_sessione": token_222}).status_code)
    prova("...mentre il cookie di 111 apre", 200,
          c.get("/api/me", cookies={"barattolo_sessione": token_111}).status_code)
    con = S.db()
    try:
        prima = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id=333").fetchone()[0]
    finally:
        con.close()
    prova("333 non c'e' nel database", 0, prima)
    prova("333 bussa: 403", 403, c.get("/api/me", headers=chi(333)).status_code)
    con = S.db()
    try:
        dopo = con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id=333").fetchone()[0]
    finally:
        con.close()
    prova("...e NON e' stato scritto: il middleware gira prima della rotta", 0, dopo)

    print("\n[chi non si fa riconoscere: legge, non fa]")
    prova("la pagina si apre (serve a Telegram per dire chi sei)", 200, c.get("/").status_code)
    prova("...e la vetrina si legge", 200, c.get("/api/listings").status_code)
    prova("...ma un gesto si ferma qui", (403, PRIVATA),
          (c.post("/api/orders", json={}).status_code, c.post("/api/orders", json={}).json()))
    prova("una firma rotta vale «nessuno»: legge, ma non fa", 403,
          c.post("/api/orders", json={}, headers={"X-Tg-Init-Data": "rotta"}).status_code)

    print("\n[le porte che restano aperte]")
    prova("la salute risponde anche a chi non e' in lista", 200,
          c.get("/api/salute", headers=chi(222)).status_code)
    w = c.post("/api/telegram/aggiornamenti", json={})
    prova("il campanello del bot risponde come a leva spenta",
          (webhook_spento.status_code, webhook_spento.json()), (w.status_code, w.json()))
    prova("...e il login pure", sfida_spenta,
          c.get("/api/login/nostr/sfida", headers=chi(222)).status_code)

    print("\n[la leva storta e' chiusa a tutti]")
    S.PROVA_SOLO_IDS = {0}
    prova("con {0} nemmeno 111 entra", 403,
          c.get("/api/me", headers=chi(111)).status_code)
    S.PROVA_SOLO_IDS = set()
    prova("rimessa vuota, 222 rientra", 200,
          c.get("/api/me", headers=chi(222)).status_code)

    print("\n[il bot nella pagina]")
    riga_serie = "const BOT_TG = 'ilbarattolobot';"
    S._PAGINA_CACHE["timbro"] = False
    pagina = c.get("/").text
    prova("col bot di serie la riga resta quella del file", 1, pagina.count(riga_serie))
    S.BOT_NOME = "barattolo_prova_bot"
    S._PAGINA_CACHE["timbro"] = False
    for via in ("/", "/miniapp.html"):
        p = c.get(via).text
        prova(f"{via}: col bot di prova la riga porta il suo nome",
              (1, 0), (p.count("const BOT_TG = 'barattolo_prova_bot';"),
                       p.count("ilbarattolobot")))
    S.BOT_NOME = "ilbarattolobot"
    S._PAGINA_CACHE["timbro"] = False
    prova("rimesso il bot di serie, la pagina torna identica a prima",
          pagina, c.get("/").text)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
