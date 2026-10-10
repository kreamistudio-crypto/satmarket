# -*- coding: utf-8 -*-
"""
IL PROMEMORIA DEL GESTO A TEMPO, SUL SERVER VERO, COL COORDINATORE E
TELEGRAM DI CARTONE (10 ott 2026, cantiere «promemoria garanzia»).

Il caso di stamattina: a chi vendeva arriva «Paga la garanzia: la
richiesta è nell'app» alle 10:04, il coordinatore gli da' un quarto
d'ora, alle 10:20 lo scambio si annulla; lui legge alle 10:48.

Le regole di Andrea: il tempo si legge DAL COORDINATORE (il suo 38385),
mai da un numero scritto qui; il primo avviso dice quanto tempo c'e'; a
meta' tempo, a chi deve ancora fare il gesto — bloccare la garanzia, o
dire dove ricevere i sats — un secondo avviso coi minuti che restano e
il bottone che apre lo scambio; uno solo per scambio e per gesto, mai
dopo il gesto e mai dopo l'annullo; e deve funzionare a 900 secondi come
a 1800, senza toccare niente.

`prove.py` difende i giudici estratti e le frasi (`prove_promemoria_gesto`).
Qui gira il SERVER VERO sul database usa-e-getta:
  • IL COORDINATORE DI CARTONE racconta lo scambio dalla rotta vera dei
    suoi eventi (`/api/p2p/evento`) e annuncia la sua finestra col 38385
    che la fotografia del libro tiene in memoria (`_P2P_FOTO["info"]`);
  • TELEGRAM DI CARTONE: `notifica` segna a chi, cosa e con quale
    bottone, e passa dal ramo Telegram VERO (`_manda_telegram`, che in
    collaudo stampa invece di bussare);
  • le lancette del server vanno avanti (il suo `time`, e solo il suo) e
    gira il battito vero delle attese, `_giro_attese_p2p`.

  1. le 10:04 di stamattina, a 900 secondi: il primo avviso dice «Hai 15
     minuti», a meta' tempo arriva il promemoria col bottone;
  2. lo stesso scambio a 1800 secondi, senza toccare niente: «Hai 30
     minuti», e il promemoria un quarto d'ora dopo;
  3. una volta sola: ripassando, e dopo un «riavvio»;
  4. chi compra e la sua fattura: il promemoria e' il suo;
  5. il gesto fatto prima della meta', l'annullo, il tempo scaduto: niente;
  6. l'interruttore degli avvisi P2P spento: niente, e non risulta detto;
  7. il coordinatore che non ha ancora annunciato niente: il ripiego, e
     nessuna cifra inventata.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore.

USO:  python collaudo_promemoria_gesto.py
"""

import asyncio
import contextlib
import io
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
V, C = banco.VENDE, banco.COMPRA
DETTO = []          # (chi, testo, bottone) di ogni avviso
STAMPE = []         # le righe del ramo Telegram vero, simulato


class Orologio:
    """Il `time` del server con le lancette che si spostano: tutto il
    resto e' il modulo vero (strftime, localtime...)."""

    def __init__(self, vero):
        self.vero = vero
        self.avanti = 0

    def time(self):
        return self.vero.time() + self.avanti

    def fissa(self, ora):
        """Le lancette su QUELL'ora, adesso: da li' camminano col tempo
        vero (i millisecondi di un battito)."""
        self.avanti = ora - self.vero.time()

    def __getattr__(self, nome):
        return getattr(self.vero, nome)


OROLOGIO = Orologio(time)
TAG = re.compile(r"</?[bi]>")


def ordine(n):
    return f"7b2f{n:04d}-c2c2-4a2b-9c3d-0000000000aa"


def annuncia(secondi):
    """Il 38385 di cartone del coordinatore: il solo tag che qui serve.
    `None` = non ha ancora annunciato niente."""
    banco.SRV._P2P_FOTO["info"] = None if secondi is None else {
        "kind": 38385, "created_at": int(time.time()),
        "tags": [["d", "cartone"], ["expiration_seconds", str(secondi)]]}


async def evento(o, azione, attore, dettaglio=""):
    b = banco.Busta({"v": 1, "order": o, "action": azione,
                     "ts": int(OROLOGIO.time()), "buyer": banco.CHIAVE_COMPRA,
                     "seller": banco.CHIAVE_VENDE, "actor": attore,
                     "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.3)
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)


def libro(o, lato, maker, taker):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "preso_da,sats,euro,metodi) VALUES(?,?,?,'in-progress',?,1,?,"
                "160000,'111,80 €','[\"Contanti al tabacchino 111.80\"]')",
                (o, maker, int(time.time()), lato, taker))
    con.commit()
    con.close()


def chiesto(o):
    """L'ora, per il coordinatore, dell'ultima richiesta di un gesto su
    quell'ordine: e' da li' che si contano i secondi di ogni battito. Il
    collaudo e' d'ORDINE e non di cronometro: le lancette si mettono a
    «richiesta + N secondi» esatti, quanto ci ha messo il banco non conta."""
    con = banco.con_db()
    q = con.execute("SELECT MAX(quando) FROM p2p_momenti WHERE ordine=? AND momento "
                    "IN ('garanzia_chiesta','fattura_chiesta')", (o,)).fetchone()[0]
    con.close()
    return int(q or 0)


async def vendita_presa(o):
    """Una vendita di chi vende, presa da chi compra, che ha gia' detto
    dove ricevere i sats: resta la garanzia, chiesta ADESSO. Torna gli
    avvisi partiti con la richiesta."""
    OROLOGIO.avanti = 0
    libro(o, "sell", V, C)
    await evento(o, "taken", "buyer", "invoice-next")
    await evento(o, "buyer-invoice-requested", "mostro")
    await evento(o, "buyer-invoice-added", "buyer", "hold-next")
    del DETTO[:]
    await evento(o, "hold-invoice-requested", "mostro", "invoice")
    return list(DETTO)


async def battito(o, secondi):
    """Le lancette a `secondi` dalla richiesta del gesto di quell'ordine,
    e un battito vero delle attese. Torna (avvisi partiti, journal)."""
    OROLOGIO.fissa(chiesto(o) + secondi)
    del DETTO[:]
    giornale = io.StringIO()
    # la leva accesa SOLO per il battito, come nel collaudo della
    # garanzia lunga: il resto del server resta col P2P spento del config
    # di cartone, e non cerca relay
    vera = banco.SRV._p2p_leve
    banco.SRV._p2p_leve = lambda *a, **k: dict(vera(), attivo=True)
    try:
        with contextlib.redirect_stdout(giornale):
            await banco.SRV._giro_attese_p2p()
    finally:
        banco.SRV._p2p_leve = vera
    return list(DETTO), giornale.getvalue()


def in_attesa(o):
    con = banco.con_db()
    r = [(x["momento"], x["tg_id"]) for x in con.execute(
        "SELECT momento, tg_id FROM p2p_attese WHERE ordine=? AND "
        "fonte='promemoria' ORDER BY id", (o,))]
    con.close()
    return r


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    SRV.time = OROLOGIO
    telegram_vero = SRV._manda_telegram

    async def notifica_di_cartone(chi, testo, bottone=None):
        DETTO.append((chi, TAG.sub("", testo), bottone))
        riga = io.StringIO()
        with contextlib.redirect_stdout(riga):
            if bottone:
                await telegram_vero(chi, testo, bottone)
            else:
                await telegram_vero(chi, testo)
        STAMPE.append(riga.getvalue())
        return "cartone"
    SRV.notifica = notifica_di_cartone
    link = SRV.LINK_LIBRO_P2P

    print("\n1) le 10:04 di stamattina, col coordinatore a 900 secondi")
    annuncia(900)
    a = ordine(1)
    primo = await vendita_presa(a)
    prova("il primo avviso va a chi vende, e dice quanto tempo ha",
          [(V, "🔒 Paga la garanzia: la richiesta è nell'app. Chi compra ha indicato "
               "dove ricevere i sats, ora tocca a te.\n\n⏳ Hai 15 minuti, poi lo "
               "scambio si annulla.", None)], primo)
    prova("in attesa c'e' il promemoria di chi vende, e quello di chi compra se n'e' "
          "andato con la sua fattura", [("garanzia_promemoria", V)], in_attesa(a))
    detti, _ = await battito(a, 7 * 60 + 29)
    prova("un secondo prima della meta' niente", [], detti)
    del STAMPE[:]
    detti, giornale = await battito(a, 7 * 60 + 30)
    prova("a 7 minuti e mezzo (la meta') il promemoria, coi minuti che restano",
          [(V, "⏳ Restano circa 8 minuti per bloccare la garanzia, altrimenti lo "
               "scambio si annulla.",
            ("⚡ Apri lo scambio", f"{link}?scambio={a}"))], detti)
    prova("...e il ramo Telegram vero lo manda col suo bottone", True,
          f"[bottone «⚡ Apri lo scambio» → {link}?scambio={a}]" in "".join(STAMPE))
    prova("...e il journal lo conta fra le attese partite", True,
          "📬 Attese P2P: avvisati 1" in giornale and "(promemoria)" in giornale)

    print("\n2) lo stesso scambio col coordinatore a 1800 secondi: non si tocca niente")
    annuncia(1800)
    b = ordine(2)
    primo = await vendita_presa(b)
    prova("il primo avviso dice mezz'ora, perche' lo dice il coordinatore", True,
          primo[0][1].endswith("⏳ Hai 30 minuti, poi lo scambio si annulla."))
    detti, _ = await battito(b, 7 * 60 + 30)
    prova("a 7 minuti e mezzo, adesso, niente", [], detti)
    detti, _ = await battito(b, 14 * 60 + 59)
    prova("un secondo prima del quarto d'ora niente", [], detti)
    detti, _ = await battito(b, 15 * 60)
    prova("al quarto d'ora il promemoria: restano 15 minuti, e il bottone",
          [(V, "⏳ Restano circa 15 minuti per bloccare la garanzia, altrimenti lo "
               "scambio si annulla.",
            ("⚡ Apri lo scambio", f"{link}?scambio={b}"))], detti)

    print("\n3) una volta sola")
    prova("un minuto dopo, niente", [], (await battito(b, 16 * 60))[0])
    prova("un battito nuovo sul database (quel che fa un server ripartito): niente",
          [], (await battito(b, 20 * 60))[0])
    con = banco.con_db()
    timbri = con.execute("SELECT COUNT(*) FROM p2p_avvisi WHERE ordine=? AND "
                         "momento='garanzia_promemoria'", (b,)).fetchone()[0]
    con.close()
    prova("il timbro dell'anti-doppione e' uno", 1, timbri)

    print("\n4) chi compra e la sua fattura")
    OROLOGIO.avanti = 0
    c = ordine(3)
    libro(c, "sell", V, C)
    await evento(c, "taken", "buyer", "invoice-next")
    await evento(c, "buyer-invoice-requested", "mostro")
    prova("la fattura chiesta mette in attesa il promemoria di chi compra",
          [("fattura_promemoria", C)], in_attesa(c))
    detti, _ = await battito(c, 15 * 60)
    prova("a meta' tempo arriva a lui, con le sue parole e il suo bottone",
          [(C, "⏳ Restano circa 15 minuti per indicare dove ricevere i sats, "
               "altrimenti lo scambio si annulla.",
            ("⚡ Apri lo scambio", f"{link}?scambio={c}"))], detti)

    print("\n5) il gesto fatto prima, l'annullo, il tempo scaduto")
    d = ordine(4)
    await vendita_presa(d)
    await evento(d, "hold-invoice-paid", "seller", "active")
    prova("garanzia pagata: l'attesa se ne va subito", [], in_attesa(d))
    detti, giornale = await battito(d, 15 * 60)
    prova("...e a meta' tempo non arriva niente", [], detti)
    prova("...ne' una riga di promemoria nel journal", False, "Promemoria P2P" in giornale)
    e = ordine(5)
    await vendita_presa(e)
    OROLOGIO.fissa(chiesto(e) + 5 * 60)
    await evento(e, "expired", "mostro", "maker-timeout")
    prova("lo scambio annullato dal coordinatore: l'attesa se ne va", [], in_attesa(e))
    detti, _ = await battito(e, 15 * 60)
    prova("...e il promemoria non parte", [], detti)
    f = ordine(6)
    await vendita_presa(f)
    detti, giornale = await battito(f, 29 * 60 + 30)
    prova("un server tornato su a mezzo minuto dalla fine non ricorda piu' niente",
          [], detti)
    prova("...e il journal dice perche'", True,
          f"Promemoria P2P: {f[:8]} «garanzia_promemoria» a {V} non parte: non resta "
          "nemmeno un minuto" in giornale)

    print("\n6) l'interruttore degli avvisi P2P spento")
    g = ordine(7)
    await vendita_presa(g)
    con = banco.con_db()
    con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (V,))
    con.commit()
    con.close()
    detti, giornale = await battito(g, 15 * 60)
    prova("chi li ha spenti non lo riceve", [], detti)
    prova("...e il journal lo dice", True, f"🔕 Attese P2P: {V} ha gli avvisi P2P SPENTI"
          in giornale)
    con = banco.con_db()
    timbri = con.execute("SELECT COUNT(*) FROM p2p_avvisi WHERE ordine=? AND "
                         "momento='garanzia_promemoria'", (g,)).fetchone()[0]
    con.execute("UPDATE utenti SET avvisi_p2p=1 WHERE tg_id=?", (V,))
    con.commit()
    con.close()
    prova("...e non risulta detto", 0, timbri)

    print("\n7) il coordinatore non ha ancora annunciato niente: il ripiego")
    annuncia(None)
    h = ordine(8)
    primo = await vendita_presa(h)
    prova("il primo avviso resta quello di sempre: nessun tempo inventato",
          [(V, "🔒 Paga la garanzia: la richiesta è nell'app. Chi compra ha indicato "
               "dove ricevere i sats, ora tocca a te.", None)], primo)
    detti, _ = await battito(h, 7 * 60 + 30)
    prova("il promemoria parte a meta' del ripiego, senza una cifra",
          [(V, "⏳ Il tempo per bloccare la garanzia sta finendo: fallo adesso, "
               "altrimenti lo scambio si annulla.",
            ("⚡ Apri lo scambio", f"{link}?scambio={h}"))], detti)
    i = ordine(9)
    await vendita_presa(i)
    annuncia(1800)
    detti, _ = await battito(i, 7 * 60 + 30)
    prova("se intanto il 38385 arriva, i minuti sono quelli VERI",
          [(V, "⏳ Restano circa 23 minuti per bloccare la garanzia, altrimenti lo "
               "scambio si annulla.",
            ("⚡ Apri lo scambio", f"{link}?scambio={i}"))], detti)

    print("\n8) a leva accesa il bottone, dentro Telegram, apre la Mini App")
    # I LINK DENTRO TELEGRAM (10 ott 2026): la leva `TELEGRAM_MINIAPP_LINK`
    # cambia SOLO quel che il ramo Telegram mette nel bottone. Chi chiama
    # `notifica` passa ancora l'indirizzo del sito — ed e' quello che va
    # nella riga in coda al DM Nostr, che Telegram non lo apre.
    SRV.TELEGRAM_MINIAPP_LINK = "https://t.me/ilbarattolobot"
    annuncia(900)
    m = ordine(10)
    await vendita_presa(m)
    del STAMPE[:]
    detti, _ = await battito(m, 7 * 60 + 30)
    prova("a `notifica` arriva ancora l'indirizzo del sito (e' quello del DM Nostr)",
          [("⚡ Apri lo scambio", f"{link}?scambio={m}")], [d[2] for d in detti])
    prova("...e il ramo Telegram vero mette nel bottone il link della Mini App", True,
          f"[bottone «⚡ Apri lo scambio» → https://t.me/ilbarattolobot?startapp=scambio_{m}]"
          in "".join(STAMPE))
    # ...e, sotto la stessa leva, i link di testo e la riga delle tastiere
    # (il secondo sì di Andrea): dal modulo VERO, coi suoi pezzi veri
    prova("la riga «🫙 Apri Barattolo» delle tastiere apre la Mini App",
          {"text": "🫙 Apri Barattolo", "url": "https://t.me/ilbarattolobot?startapp=casa"},
          SRV.tastiera_bot()["inline_keyboard"][0][0])
    nuovi = SRV._testo_avviso_nuovi_p2p(
        [{"tipo": "vendita", "conv": 3.0, "euro": "50,00 €", "metodi": "SEPA"}])
    prova("l'avviso dei nuovi ordini porta «🫙 Apri il libro ordini» verso la Mini App",
          True, '<a href="https://t.me/ilbarattolobot?startapp=p2p">🫙 Apri il libro ordini</a>'
          in nuovi)
    post = SRV._caption_canale_p2p("vendo", 100, "Revolut", {"venditore": "Rosina"})
    prova("il post P2P nel canale porta «🫙 Apri lo Scambio P2P su Barattolo» verso la Mini App",
          True, '<a href="https://t.me/ilbarattolobot?startapp=casa">'
                '🫙 Apri lo Scambio P2P su Barattolo</a>' in post)
    SRV.TELEGRAM_MINIAPP_LINK = ""
    prova("...e spenta la leva tornano tutti e tre al sito",
          [SRV.URL_PUBBLICO, True, True],
          [SRV.tastiera_bot()["inline_keyboard"][0][0]["url"],
           f'<a href="{link}">🫙 Apri il libro ordini</a>' in SRV._testo_avviso_nuovi_p2p(
               [{"tipo": "vendita", "conv": 3.0, "euro": "50,00 €", "metodi": "SEPA"}]),
           f'<a href="{SRV.URL_PUBBLICO}">🫙 Apri lo Scambio P2P su Barattolo</a>'
           in SRV._caption_canale_p2p("vendo", 100, "Revolut", {"venditore": "Rosina"})])
    n = ordine(11)
    await vendita_presa(n)
    del STAMPE[:]
    await battito(n, 7 * 60 + 30)
    prova("...spenta di nuovo, il bottone torna quello del sito", True,
          f"[bottone «⚡ Apri lo scambio» → {link}?scambio={n}]" in "".join(STAMPE))
    SRV.time = time


def main():
    banco.avvio()
    banco.semina()
    banco.SRV.P2P_RESPIRO_S = 1
    banco.SRV.P2P_RESPIRO_NOME_S = 1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
