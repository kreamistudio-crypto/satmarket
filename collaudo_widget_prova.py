# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL WIDGET DI PROVA (10 nov 2026, cantiere widget-prova,
richiesta di Andrea: «fallo prima per il bot di collaudo»).

`prove.py` prova i giudici puri e i tetti della paginetta; qui risponde
il SERVER VERO, dal campanello del bot in giu':
  - a lista vuota (la produzione) `/provawidget` e' un comando che non
    esiste, nessun widget parte e un tocco nel widget non cambia niente;
  - sull'istanza di prova un admin riceve la scheda (sendWidget col suo
    HTML, il passo 0, le richieste accese), chi non e' admin no;
  - il tocco nel widget riceve SEMPRE la risposta, e prima della modifica;
    il passo cambia solo per l'admin; il comando gira la scheda dal lato
    del bot, dentro i cinque passi;
  - un rifiuto di Telegram si dice in chat con le sue parole, e la
    scheda senza bottone e' il secondo tentativo.

NON TOCCA NIENTE DI VERO: il config finto lo installa `avvio()` del banco
(MODALITA_COLLAUDO), e `bot_api` e' sostituita da un registro. Nessuna
rete.

USO:  python collaudo_widget_prova.py
"""

import json
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova
CAMPANELLO = {"X-Telegram-Bot-Api-Secret-Token": "collaudo"}


def main():
    print("=" * 58)
    print("  IL WIDGET DI PROVA — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    S = banco.SRV
    c = TestClient(S.app)
    chiamate = []
    rifiuta = set()          # i metodi che Telegram «rifiuta» al prossimo giro
    msg_id = [500]

    async def bot_finto(metodo, dati):
        chiamate.append((metodo, dati))
        if metodo in rifiuta:
            rifiuta.discard(metodo)
            return {"ok": False, "description": f"Bad Request: {metodo} finto"}
        msg_id[0] += 1
        return {"ok": True, "result": {"message_id": msg_id[0]}}

    vero = S.bot_api
    S.bot_api = bot_finto

    def scrive(chi, testo, n=[0]):
        n[0] += 1
        return c.post("/api/telegram/aggiornamenti", headers=CAMPANELLO,
                      json={"update_id": n[0], "message": {
                          "from": {"id": chi, "first_name": "Prova"},
                          "chat": {"id": chi, "type": "private"}, "text": testo}})

    def tocca(chi, dati, message_id, n=[1000]):
        n[0] += 1
        return c.post("/api/telegram/aggiornamenti", headers=CAMPANELLO,
                      json={"update_id": n[0], "widget_query": {
                          "id": f"q{n[0]}", "from": {"id": chi},
                          "chat": {"id": chi, "type": "private"},
                          "message_id": message_id, "data": dati}})

    metodi = lambda: [m for m, _ in chiamate]
    try:
        print("\n[in produzione il widget non esiste]")
        r = scrive(999, "/provawidget")
        prova("l'admin scrive /provawidget: 200, nessun widget, la risposta "
              "di un comando qualunque", (200, ["sendMessage"], True),
              (r.status_code, metodi(),
               "Non conosco questo comando" in chiamate[0][1]["text"]))
        chiamate.clear()
        tocca(999, "vai:2", 77)
        prova("un tocco nel widget riceve il «no» e non modifica niente",
              [("answerWidgetQuery", "no")],
              [(m, d.get("data")) for m, d in chiamate])
        prova("il webhook chiede gli update di ieri",
              ["message", "callback_query"], S.aggiornamenti_chiesti())

        print("\n[sull'istanza di prova, all'admin]")
        S.PROVA_SOLO_IDS = {999, 111}
        chiamate.clear()
        scrive(111, "/provawidget")
        prova("chi e' in lista ma non e' admin non riceve la scheda",
              ["sendMessage"], metodi())
        chiamate.clear()
        scrive(999, "/provawidget")
        m, d = chiamate[0]
        prova("l'admin la riceve: sendWidget, col suo HTML, passo 0, "
              "richieste accese, in chat privata",
              ("sendWidget", 999, True, {"passo": 0}, True, 1),
              (m, d["chat_id"], d["html"] == S.HTML_WIDGET_PROVA,
               json.loads(d["chat_data"]), d["allow_queries"], len(chiamate)))
        scheda = msg_id[0]
        prova("...e la scheda si ricorda", (scheda, 0), S._WIDGET_PROVA[999])
        prova("il webhook ora chiede anche i widget", True,
              "widget_query" in S.aggiornamenti_chiesti())

        print("\n[il tocco nel widget]")
        chiamate.clear()
        tocca(999, "vai:2", scheda)
        prova("risposta «ok» PRIMA, poi la modifica col passo 2",
              [("answerWidgetQuery", "ok"), ("editMessageWidgetData", {"passo": 2})],
              [(m, d.get("data") if m == "answerWidgetQuery"
                else json.loads(d["chat_data"])) for m, d in chiamate])
        prova("...sulla scheda giusta", (999, scheda),
              (chiamate[1][1]["chat_id"], chiamate[1][1]["message_id"]))
        chiamate.clear()
        tocca(111, "vai:4", scheda)
        prova("il tocco di chi non e' admin: «no», e la scheda resta al 2",
              ([("answerWidgetQuery", "no")], (scheda, 2)),
              ([(m, d.get("data")) for m, d in chiamate], S._WIDGET_PROVA[999]))
        chiamate.clear()
        tocca(999, "rubo:1", scheda)
        prova("una richiesta che non e' nostra: «no», niente modifica",
              ["answerWidgetQuery"], metodi())

        print("\n[il comando gira la scheda dal lato del bot]")
        passi = []
        for testo in ("/provawidget avanti", "/provawidget 5",
                      "/provawidget 9", "/provawidget indietro", "/provawidget 1"):
            chiamate.clear()
            scrive(999, testo)
            passi.append(json.loads(chiamate[0][1]["chat_data"])["passo"])
        prova("avanti, 5, 9 (dentro lo stepper), indietro, 1",
              [3, 4, 4, 3, 0], passi)
        chiamate.clear()
        scrive(999, "/provawidget boh")
        prova("un argomento storto: una riga che spiega, niente modifica",
              (["sendMessage"], True),
              (metodi(), "avanti, indietro" in chiamate[0][1]["text"]))

        print("\n[i rifiuti di Telegram si dicono in chat]")
        chiamate.clear()
        rifiuta.add("editMessageWidgetData")
        scrive(999, "/provawidget avanti")
        prova("modifica rifiutata: l'avviso porta le parole di Telegram, e "
              "il passo resta quello di prima",
              (["editMessageWidgetData", "sendMessage"], True, (scheda, 0)),
              (metodi(), "editMessageWidgetData finto" in chiamate[1][1]["text"],
               S._WIDGET_PROVA[999]))
        chiamate.clear()
        rifiuta.add("sendWidget")
        scrive(999, "/provawidget")
        prova("scheda rifiutata col bottone: lo dice, e riprova senza",
              (["sendWidget", "sendMessage", "sendWidget"], True, False),
              (metodi(), "reply_markup" in chiamate[0][1],
               "reply_markup" in chiamate[2][1]))
        prova("...e la scheda nuova prende il posto della vecchia",
              (msg_id[0], 0), S._WIDGET_PROVA[999])
    finally:
        S.bot_api = vero
        S.PROVA_SOLO_IDS = set()

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
