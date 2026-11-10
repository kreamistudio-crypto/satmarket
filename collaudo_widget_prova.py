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
    scheda senza bottone e' il secondo tentativo;
  - `/ordini` (cantiere widget-ordini): ognuno riceve i SUOI ordini veri,
    gli attivi prima; la richiesta della scheda risponde con l'elenco
    fresco di chi chiede; in produzione niente di tutto questo esiste.

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

        print("\n[la scheda dei miei ordini: /ordini]")
        con = S.db()
        for chi_e in (111, 222, 333):
            con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                        "registrato,ln_address) VALUES(?,?,?,1,'')",
                        (chi_e, f"U{chi_e}", f"neg{chi_e}"))
        ann = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,'Lampada <b>vintage</b>','una cosa',30000,'Altro',"
            "'Pavia (PV)','attivo',1,'spedizione',5,'sats','nuovo')").lastrowid

        def ordine(stato, compra, vende, mosso):
            return con.execute(
                "INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,creato,aggiornato) VALUES(?,?,?,30000,?,?,?)",
                (ann, compra, vende, stato, mosso, mosso)).lastrowid
        concluso = ordine("released", 111, 222, 10)
        vivo = ordine("locked", 111, 222, 20)
        altrui = ordine("shipped", 333, 222, 30)
        con.commit()
        con.close()

        chiamate.clear()
        scrive(111, "/ordini")
        m, d = chiamate[0]
        e = json.loads(d["chat_data"])
        prova("chi compra riceve la scheda coi SUOI due ordini, il vivo "
              "prima del concluso", ("sendWidget", 111, [vivo, concluso], 1, 2, 1),
              (m, d["chat_id"], [r[0] for r in e["o"]], e["a"], e["n"],
               len(chiamate)))
        prova("...con le richieste accese, l'altezza fissa e il titolo "
              "dell'annuncio cosi' com'e' (l'escape lo fa la pagina)",
              (True, S.ALTEZZA_WIDGET_ORDINI, "Lampada <b>vintage</b>"),
              (d["allow_queries"], d["height"], e["o"][0][5]))
        prova("...e sta nei 1024 byte di chat_data", True,
              len(d["chat_data"].encode("utf-8")) <= 1024)
        url_vero = S.URL_PUBBLICO
        S.URL_PUBBLICO = "http://127.0.0.1:8000"
        prova("senza un https niente bottone «Apri in Barattolo», che non "
              "si aprirebbe", (True, False),
              ('U=""' in S.html_widget_ordini(), "__URL__" in d["html"]))
        S.URL_PUBBLICO = "https://collaudo.barattolo.store/"
        prova("...con un https il bottone porta a casa", True,
              'U="https://collaudo.barattolo.store"' in S.html_widget_ordini())
        S.URL_PUBBLICO = url_vero
        chiamate.clear()
        scrive(222, "/ordini")
        prova("chi non e' ammesso alla prova non riceve niente, nemmeno "
              "la scheda", [], metodi())
        S.PROVA_SOLO_IDS = {999, 111, 222, 333}
        scrive(222, "/ordini")
        e = json.loads(chiamate[0][1]["chat_data"])
        prova("chi vende vede i suoi tre, da venditore",
              ([altrui, vivo, concluso], {"s"}),
              ([r[0] for r in e["o"]], {r[2] for r in e["o"]}))
        chiamate.clear()
        scrive(999, "/ordini")
        prova("chi non ha ordini riceve la scheda vuota, non quella di un altro",
              {"a": 0, "n": 0, "o": []}, json.loads(chiamate[0][1]["chat_data"]))

        print("\n[la scheda chiede l'elenco: e' di chi chiede]")
        con = S.db()
        con.execute("UPDATE ordini SET stato='shipped', aggiornato=40 WHERE id=?",
                    (vivo,))
        con.commit()
        con.close()
        chiamate.clear()
        tocca(111, "o", 77)
        e = json.loads(chiamate[0][1]["data"])
        prova("la richiesta «o» risponde con l'elenco FRESCO di chi chiede, "
              "e non modifica niente", (["answerWidgetQuery"], [vivo, 2], 2),
              (metodi(), e["o"][0][:2], e["n"]))
        chiamate.clear()
        tocca(333, "o", 77)
        e = json.loads(chiamate[0][1]["data"])
        prova("...a un altro risponde coi SUOI, anche se tocca la scheda di "
              "un altro messaggio", [altrui], [r[0] for r in e["o"]])

        print("\n[in produzione la scheda degli ordini non esiste]")
        S.PROVA_SOLO_IDS = set()
        chiamate.clear()
        scrive(111, "/ordini")
        prova("/ordini e' un comando che non esiste",
              (["sendMessage"], True),
              (metodi(), "Non conosco questo comando" in chiamate[0][1]["text"]))
        chiamate.clear()
        tocca(111, "o", 77)
        prova("...e la richiesta «o» riceve una risposta vuota",
              [("answerWidgetQuery", "")],
              [(m, d.get("data")) for m, d in chiamate])
    finally:
        S.bot_api = vero
        S.PROVA_SOLO_IDS = set()

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
