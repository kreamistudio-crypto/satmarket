# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELL'ABBONAMENTO A UN CANALE TELEGRAM (20 nov 2026, cantiere
abbonamento-canale, idea e ok di Andrea).

IL CASO: il negozio AndreAI vende un mese del canale privato «Bitcoin
On». Chi paga riceve da solo un link d'invito personale; quando ENTRA
nel canale l'acquisto si chiude e i sats vanno a chi vende (Andrea: «uno
puo' entrare, guardarsi i video riservati e dopo 24 ore dire che non gli
piace»); chi non rinnova riceve due promemoria e poi esce, tolto dal bot.

Gira la STORIA sul SERVER VERO con un database usa-e-getta, il nodo di
cartone del banco di casa (`collaudo_lnbits_muto`) e un Telegram di
cartone che ricorda ogni chiamata del bot: compra, incasso, lettura,
richiesta d'ingresso, sblocco, rinnovo e ronda sono quelli veri.

Le domande a cui risponde:
  1. chi puo' vendere: la mappa del config, la leva, la forma (solo
     codice online, niente asta), le chiavi-testo del pannello;
  2. la cassa: un mese per acquisto, niente on-chain, niente carrello,
     niente acquisto se il canale non c'e' piu';
  3. l'incasso: il link nasce da solo, e' il contenuto dell'ordine, col
     nome vero del canale; lo stock non scala; niente «spedisci»;
  4. chi vende non riscrive il link;
  5. l'ingresso: un estraneo col link non entra e non lo consuma; chi ha
     pagato entra, il link si revoca, la scadenza e' fra 30 giorni, e i
     sats partono SUBITO; il link usato non apre piu' niente;
  6. il rinnovo di chi e' dentro: niente link, un mese in piu', sats
     subito; chi era uscito riceve un link nuovo;
  7. la ronda: promemoria prima e il giorno della scadenza, una volta
     sola; dopo la tolleranza fuori (ban + unban); se il bot non puo',
     un avviso solo ai moderatori e nessuno segnato come uscito;
  8. il guasto al pagamento: niente link, moderatori avvisati, la ronda
     lo rifa';
  9. la disputa prima di entrare: il link non apre;
 10. chi compra con la sola Nostr: entra il primo che usa il link;
 11. il campanello chiede le richieste d'ingresso solo con un canale.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (lo fa `avvio()` del banco). Nessuna rete,
nessuna chiave.

USO:  python collaudo_abbonamento_canale.py
"""

import asyncio
import time

import collaudo_lnbits_muto as banco
from prove import bolt11_finta

prova = banco.prova
SRV = None

CANALE = -1001234567890
PREZZO = 40_000
A_COMPRA, A_VENDE = "compra@wallet.tld", "vende@wallet.tld"

FATTURE = {}
CHIESTE = []          # (a chi, sats, esito) di ogni richiesta di PAGAMENTO
_coniate = [0]

# IL TELEGRAM DI CARTONE: ogni chiamata del bot, e le risposte decise qui
BOT = []                       # (metodo, dati)
TG = {"stato_membro": {}, "rifiuta": set(), "titolo": "Bitcoin On"}
_link_n = [0]
TASTI = []                     # (a chi, etichetta, indirizzo) dei tasti


def fattura(chi, sats):
    _coniate[0] += 1
    b = bolt11_finta(sats, 3600, int(time.time()), phash=900 + _coniate[0])
    FATTURE[b] = {"chi": chi, "sats": sats}
    return b


def uscite():
    return sorted((c, s) for c, s, e in CHIESTE if e == "success")


def alza(nome, fn, codice, dentro=""):
    try:
        fn()
    except Exception as e:
        cod = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        dice = (not dentro) or dentro.lower() in testo.lower()
        prova(nome, (codice, True), (cod, dice))
        if not (cod == codice and dice):
            print(f"      testo: {testo!r}")
        return
    prova(nome, codice, "nessun rifiuto")


async def bot_finto(metodo, dati):
    BOT.append((metodo, dict(dati)))
    if metodo in TG["rifiuta"]:
        return {"ok": False, "description": "Bad Request: not enough rights"}
    if metodo == "createChatInviteLink":
        _link_n[0] += 1
        return {"ok": True, "result": {
            "invite_link": f"https://t.me/+cartone{_link_n[0]}",
            "name": dati.get("name", "")}}
    if metodo == "getChat":
        return {"ok": True, "result": {"title": TG["titolo"]}}
    if metodo == "getChatMember":
        return {"ok": True, "result": {
            "status": TG["stato_membro"].get(dati.get("user_id"), "left")}}
    return {"ok": True, "result": True}


def avvio():
    global SRV
    banco.avvio()
    SRV = banco.SRV
    SRV.CANALI_ABBONAMENTO = {222: CANALE}
    SRV.ABBONAMENTI_CANALE = True
    SRV.bot_api = bot_finto
    SRV._onchain_compra_ammesso = lambda tg: None

    async def fattura_da_address(addr, sats):
        return fattura("compratore" if addr == A_COMPRA else "venditore",
                       sats)

    async def zitto(*a, **k):
        return None

    async def notifica_col_tasto(chi, testo, bottone=None, *a, **k):
        banco.DETTO.append((chi, testo))
        if bottone:
            TASTI.append((chi, bottone[0], bottone[1]))

    SRV.notifica = notifica_col_tasto
    SRV.invoice_da_ln_address = fattura_da_address
    SRV.annuncio_su_nostr = zitto
    SRV.promo_venduto = zitto

    vero_post = banco._FintoHttpx.AsyncClient.post

    async def post(self, url, **kw):
        j = kw.get("json") or {}
        b = j.get("data") or j.get("bolt11") or ""
        if b in FATTURE:
            banco.NODO["sats"] = FATTURE[b]["sats"]
            banco.NODO["esito"] = "success"
            if "decode" not in url:
                CHIESTE.append((FATTURE[b]["chi"], FATTURE[b]["sats"],
                                "success"))
        return await vero_post(self, url, **kw)

    banco._FintoHttpx.AsyncClient.post = post


def db_esegui(sql, *args):
    con = SRV.db()
    con.execute(sql, args)
    con.commit()
    con.close()


def db_uno(sql, *args):
    con = SRV.db()
    r = con.execute(sql, args).fetchone()
    con.close()
    return r


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci", "payout_passi",
              "payout_tentati", "abbonamenti_link", "abbonati_canale"):
        try:
            con.execute(f"DELETE FROM {t}")
        except Exception:
            pass
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "ln_address) VALUES(222,'Vende','neg22222',1,?)", (A_VENDE,))
    for chi in (111, -5):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,'Compra',?,1,?)",
                    (chi, f"neg{abs(chi)}", A_COMPRA))
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,quantita_max,"
        "valuta,condizione,abbonamento) VALUES(222,'Bitcoin On, un mese',"
        "'desc',?,'Buoni ed esperienze','','attivo',1,'digitale',?,?,"
        "'sats','nuovo',1)",
        (PREZZO, SRV.MAX_QUANTITA_ANNUNCIO, SRV.MAX_QUANTITA_ANNUNCIO))
    aid = cur.lastrowid
    con.commit()
    con.close()
    return aid


def pulisci_giro():
    FATTURE.clear()
    CHIESTE.clear()
    BOT.clear()
    TASTI.clear()
    banco.PAGAMENTI.clear()
    banco.USCITE.clear()
    banco.NODO.update(codice=200, esito="success")
    banco.DETTO.clear()
    banco.AVVISI.clear()


def compra(aid, chi=111, pezzi=1):
    """Un ordine pagato, dai percorsi veri: la cassa e l'incasso."""
    banco.come(chi)
    c = banco.chiama(SRV.compra, None,
                     corpo={"annuncio_id": aid, "quantita": pezzi,
                            "consegna": "digitale"})
    oid = c["ordine_id"]
    pulisci_giro()
    banco.chiama(SRV._incassa_ordine, oid)
    return oid


def bussa(oid, chi):
    """La richiesta d'ingresso che Telegram manda al campanello."""
    r = db_uno("SELECT link FROM abbonamenti_link WHERE ordine_id=?", oid)
    upd = {"chat_join_request": {
        "chat": {"id": CANALE, "type": "channel"},
        "from": {"id": chi, "is_bot": False, "first_name": "X"},
        "invite_link": {"invite_link": r[0] if r else "",
                        "name": f"Barattolo ordine {oid}"}}}
    BOT.clear()
    asyncio.run(SRV.gestisci_update(upd))
    return [m for m, _d in BOT]


def detti_a(chi):
    return " || ".join(t for c, t in banco.DETTO if c == chi)


def abbonato(chi=111):
    return db_uno("SELECT * FROM abbonati_canale WHERE canale=? "
                  "AND compratore_id=?", CANALE, chi)


def stato(oid):
    return banco.riga(oid)["stato"]


# ---------------------------------------------------------------
def scena_chi_vende():
    print("\n── 1. CHI PUO' VENDERE ──")
    prova("il venditore nella mappa ha il suo canale, gli altri no",
          (CANALE, 0), (SRV.canale_abbonamento_di(222),
                        SRV.canale_abbonamento_di(111)))
    SRV.CANALI_ABBONAMENTO = {"222": str(CANALE)}
    prova("chiavi e valori come testo (una leva dal pannello) valgono",
          CANALE, SRV.canale_abbonamento_di(222))
    SRV.CANALI_ABBONAMENTO = {222: CANALE}
    SRV.ABBONAMENTI_CANALE = False
    prova("a leva spenta nessuno ha un canale", 0,
          SRV.canale_abbonamento_di(222))
    SRV.ABBONAMENTI_CANALE = True
    f = SRV.abbonamento_da_payload
    prova("casella accesa, codice online da solo: 1", 1,
          f({"abbonamento": 1}, 222, "digitale", 0))
    prova("casella assente o spenta: 0", (0, 0),
          (f({}, 222, "digitale", 0), f({"abbonamento": 0}, 111, "", 0)))
    alza("chi non ha un canale non la accende",
         lambda: f({"abbonamento": 1}, 111, "digitale", 0), 400, "canale")
    alza("con la spedizione si rifiuta",
         lambda: f({"abbonamento": 1}, 222, "spedizione", 0), 400,
         "prezzo fisso")
    alza("col codice accanto a una strada fisica si rifiuta",
         lambda: f({"abbonamento": 1}, 222, "ritiro", 1), 400, "prezzo fisso")
    alza("all'asta si rifiuta",
         lambda: f({"abbonamento": 1}, 222, "digitale", 0, 86400), 400,
         "prezzo fisso")


def scena_cassa(aid):
    print("\n── 2. LA CASSA ──")
    banco.come(111)
    c = banco.chiama(SRV.compra, None, corpo={
        "annuncio_id": aid, "quantita": 3, "consegna": "digitale"})
    prova("chi chiede tre pezzi compra un mese", 1,
          banco.riga(c["ordine_id"])["quantita"])
    db_esegui("DELETE FROM ordini")
    alza("on-chain si rifiuta", lambda: banco.chiama(SRV.compra, None, corpo={
        "annuncio_id": aid, "consegna": "digitale", "metodo": "onchain"}),
        400, "Lightning")
    alza("nel carrello si rifiuta", lambda: banco.chiama(
        SRV.compra, None, corpo={"righe": [
            {"annuncio_id": aid, "quantita": 1},
            {"annuncio_id": aid + 999, "quantita": 1}],
            "consegna": "digitale"}), 400)
    SRV.CANALI_ABBONAMENTO = {}
    alza("col canale tolto dal config non si compra",
         lambda: banco.chiama(SRV.compra, None, corpo={
             "annuncio_id": aid, "consegna": "digitale"}),
         400, "non è disponibile")
    SRV.CANALI_ABBONAMENTO = {222: CANALE}


def scena_incasso(aid):
    print("\n── 3. L'INCASSO ──")
    stock = db_uno("SELECT quantita FROM annunci WHERE id=?", aid)[0]
    oid = compra(aid)
    o = banco.riga(oid)
    prova("pagato: l'ordine e' gia' consegnato, col canale scritto",
          ("shipped", CANALE, "Consegna digitale"),
          (o["stato"], o["abbonamento_canale"], o["corriere"]))
    link = db_uno("SELECT link FROM abbonamenti_link WHERE ordine_id=?",
                  oid)[0]
    crea = [d for m, d in BOT if m == "createChatInviteLink"]
    prova("il link nasce col nome dell'ordine e la richiesta d'ingresso",
          (1, CANALE, f"Barattolo ordine {oid}", True),
          (len(crea), crea[0]["chat_id"], crea[0]["name"],
           crea[0]["creates_join_request"]))
    testo = SRV._decifra_contenuto(o["contenuto_digitale"])
    prova("il contenuto e' il link, col nome vero del canale",
          (True, True), (link in testo, "«Bitcoin On»" in testo))
    prova("lo stock non scala", stock,
          db_uno("SELECT quantita FROM annunci WHERE id=?", aid)[0])
    prova("chi compra sa che e' pagato, e che entrare chiude l'acquisto",
          (True, True, False),
          ("Abbonamento a «Bitcoin On» pagato" in detti_a(111),
           "l'acquisto è definitivo" in detti_a(111),
           "Ordine pagato" in detti_a(111)))
    prova("chi vende sa che il link e' partito, e nessuno gli dice di "
          "spedire", (True, False),
          ("link d'invito è partito" in detti_a(222),
           "Hai venduto" in detti_a(222)))
    return oid


def scena_chi_vende_non_riscrive(oid):
    print("\n── 4. IL LINK NON SI RISCRIVE ──")
    banco.come(222)
    alza("chi vende non consegna un altro contenuto",
         lambda: banco.chiama(SRV.consegna_digitale, oid, None, "", "",
                              corpo={"contenuto": "un altro link"}),
         400, "da solo")


def scena_ingresso(oid):
    print("\n── 5. L'INGRESSO ──")
    banco.come(111)
    banco.chiama(SRV.leggi_contenuto_digitale, oid, "", "", None)
    prova("chi compra rivela il link: 'delivered'", "delivered", stato(oid))
    pulisci_giro()
    prova("un estraneo col link viene rifiutato",
          ["declineChatJoinRequest"], bussa(oid, 555))
    prova("...e il link resta di chi ha pagato", 0,
          db_uno("SELECT usato_da FROM abbonamenti_link WHERE ordine_id=?",
                 oid)[0])
    prima = int(time.time())
    metodi = bussa(oid, 111)
    prova("chi ha pagato entra, e il link si revoca",
          ["approveChatJoinRequest", "revokeChatInviteLink"],
          [m for m in metodi if m != "getChat"])
    a = abbonato()
    trenta = SRV.ABBONAMENTO_GIORNI * 86400
    prova("e' un abbonato, fino a fra 30 giorni",
          (111, True), (a["membro_tg"],
                        prima + trenta <= a["scade"] <= prima + trenta + 5))
    prova("entrare chiude l'acquisto: i sats a chi vende, subito",
          ("released", [("venditore", PREZZO)]), (stato(oid), uscite()))
    prova("chi compra legge «Sei dentro», chi vende che e' entrato",
          (True, True), ("Sei dentro «Bitcoin On»" in detti_a(111),
                         "entrato in «Bitcoin On»" in detti_a(222)))
    prova("il link usato non apre piu' niente",
          ["declineChatJoinRequest"], bussa(oid, 111))


def scena_rinnovo(aid):
    print("\n── 6. IL RINNOVO ──")
    TG["stato_membro"][111] = "member"
    prima = abbonato()["scade"]
    oid = compra(aid)
    prova("chi e' dentro non riceve un link, e l'ordine si chiude subito",
          ("released", [], [("venditore", PREZZO)]),
          (stato(oid), [m for m, _d in BOT if m == "createChatInviteLink"],
           uscite()))
    prova("...con un mese in piu' sulla scadenza di prima",
          prima + SRV.ABBONAMENTO_GIORNI * 86400, abbonato()["scade"])
    prova("...e chi compra lo legge", True,
          "Abbonamento a «Bitcoin On» rinnovato" in detti_a(111))
    TG["stato_membro"][111] = "left"
    oid2 = compra(aid)
    prova("chi e' uscito da solo riceve un link nuovo",
          ("shipped", 1), (stato(oid2), len(
              [m for m, _d in BOT if m == "createChatInviteLink"])))
    TG["stato_membro"][111] = "member"
    return oid2


def ronda():
    pulisci_giro()
    asyncio.run(SRV.ronda_abbonamenti())
    return [m for m, _d in BOT if m != "getChat"]


def scena_ronda():
    print("\n── 7. LA RONDA ──")
    adesso = int(time.time())
    db_esegui("UPDATE abbonati_canale SET scade=?, avviso_prima_il=0, "
              "avviso_scaduto_il=0 WHERE compratore_id=111",
              adesso + 2 * 86400)
    ronda()
    prova("tre giorni prima: il promemoria, col tasto per rinnovare",
          (True, [(111, "🔑 Rinnova",
                   f"{SRV.URL_PUBBLICO}/annuncio/{AID[0]}")]),
          ("scade il" in detti_a(111), TASTI))
    ronda()
    prova("...una volta sola", "", detti_a(111))
    db_esegui("UPDATE abbonati_canale SET scade=? WHERE compratore_id=111",
              adesso - 3600)
    ronda()
    prova("il giorno della scadenza: il secondo promemoria", True,
          "è scaduto oggi" in detti_a(111))
    db_esegui("UPDATE abbonati_canale SET scade=? WHERE compratore_id=111",
              adesso - 4 * 86400)
    TG["rifiuta"].add("banChatMember")
    metodi = ronda()
    prova("il bot senza permessi: un avviso ai moderatori, nessuno fuori",
          (["banChatMember"], 1, 0),
          (metodi, len(banco.AVVISI), abbonato()["espulso_il"]))
    ronda()
    prova("...e l'avviso non si ripete a ogni giro", 0, len(banco.AVVISI))
    TG["rifiuta"].discard("banChatMember")
    metodi = ronda()
    prova("dopo la tolleranza: fuori, ma libero di rientrare",
          ["banChatMember", "unbanChatMember"], metodi)
    prova("...e tolto solo lui, col suo numero Telegram",
          [111, 111], [d["user_id"] for m, d in BOT if m.endswith("ChatMember")])
    prova("chi esce e chi vende lo sanno",
          (True, True, True), (abbonato()["espulso_il"] > 0,
                               "sei uscito da «Bitcoin On»" in detti_a(111),
                               "uscito da «Bitcoin On»" in detti_a(222)))
    prova("un uscito la ronda non lo tocca piu'", [], ronda())


def scena_guasto(aid):
    print("\n── 8. IL GUASTO AL PAGAMENTO ──")
    TG["rifiuta"].add("createChatInviteLink")
    TG["stato_membro"][111] = "left"
    oid = compra(aid)
    prova("Telegram dice di no: l'ordine resta pagato, i moderatori sanno",
          ("locked", 1), (stato(oid), len(banco.AVVISI)))
    TG["rifiuta"].discard("createChatInviteLink")
    ronda()
    prova("la ronda rifa' il link", ("shipped", 1), (stato(oid), db_uno(
        "SELECT COUNT(*) FROM abbonamenti_link WHERE ordine_id=?", oid)[0]))
    return oid


def scena_disputa(oid):
    print("\n── 9. LA DISPUTA PRIMA DI ENTRARE ──")
    banco.come(111)
    banco.chiama(SRV.apri_disputa, oid, "", "")
    prova("in disputa il link non apre", ["declineChatJoinRequest"],
          bussa(oid, 111))


def scena_nostr(aid):
    print("\n── 10. CHI COMPRA CON LA SOLA NOSTR ──")
    oid = compra(aid, chi=-5)
    metodi = bussa(oid, 777)
    prova("entra il primo che usa il link",
          ["approveChatJoinRequest", "revokeChatInviteLink"],
          [m for m in metodi if m != "getChat"])
    prova("...e il suo numero Telegram e' quello che la ronda togliera'",
          777, abbonato(-5)["membro_tg"])


def scena_campanello():
    print("\n── 11. IL CAMPANELLO ──")
    prova("con un canale chiede anche le richieste d'ingresso", True,
          "chat_join_request" in SRV.aggiornamenti_chiesti())
    SRV.CANALI_ABBONAMENTO = {}
    prova("senza, la richiesta e' quella di ieri", False,
          "chat_join_request" in SRV.aggiornamenti_chiesti())
    SRV.CANALI_ABBONAMENTO = {222: CANALE}
    BOT.clear()
    asyncio.run(SRV.gestisci_update({"chat_join_request": {
        "chat": {"id": -100999}, "from": {"id": 111},
        "invite_link": {"invite_link": "https://t.me/+altro"}}}))
    prova("un canale che non conosciamo non si tocca", [], BOT)
    # I LINK DI CHI AMMINISTRA (20 nov 2026, Andrea: gli iscritti da
    # YouTube entrano coi suoi link): nel NOSTRO canale una richiesta
    # che non viene da un link nostro resta a lui — niente rifiuto
    BOT.clear()
    asyncio.run(SRV.gestisci_update({"chat_join_request": {
        "chat": {"id": CANALE}, "from": {"id": 777},
        "invite_link": {"invite_link": "https://t.me/+youtube",
                        "name": "Iscritti YouTube"}}}))
    prova("nel nostro canale il link di chi amministra non si tocca",
          [], BOT)
    BOT.clear()
    asyncio.run(SRV.gestisci_update({"chat_join_request": {
        "chat": {"id": CANALE}, "from": {"id": 777},
        "invite_link": {"invite_link": "https://t.me/+finto",
                        "name": "Barattolo ordine 999999"}}}))
    prova("...nemmeno col nome di un ordine che non c'e'", [], BOT)


AID = [0]


def main():
    avvio()
    aid = semina()
    AID[0] = aid
    scena_chi_vende()
    scena_cassa(aid)
    oid = scena_incasso(aid)
    scena_chi_vende_non_riscrive(oid)
    scena_ingresso(oid)
    scena_rinnovo(aid)
    scena_ronda()
    oid = scena_guasto(aid)
    scena_disputa(oid)
    scena_nostr(aid)
    scena_campanello()
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    raise SystemExit(1 if banco.FALLITE else 0)


if __name__ == "__main__":
    main()
