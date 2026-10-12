# -*- coding: utf-8 -*-
"""
LA CHAT NELLO SCAMBIO, SUL SERVER VERO (12 ott 2026).

La decisione di Andrea con Alan: dentro ogni scambio P2P preso le due
parti si scrivono, con chiavi usa-e-getta; i messaggi passano dal server
GIA' CHIUSI dal telefono; il server fa il postino (tiene la busta, la
consegna, non la apre) e a scambio finito la CANCELLA; il moderatore la
legge solo se una delle due parti apre una disputa.

`prove.py` difende i giudici estratti e fa girare la crittografia vera
in node (`prove_chat_scambio`). Qui girano le ROTTE VERE —
`/api/p2p/chat/leggi`, `/invia`, `/moderatori`,
`/api/p2p/moderazione/chat` e, per lo scambio, `/api/p2p/evento` — su
database usa-e-getta, con l'autenticazione VERA (niente `come()`):

   1. le quattro coppie di accesso delle due parti — Telegram/Telegram,
      Telegram/Nostr, Nostr/Telegram, Nostr/Nostr: i saluti, un
      messaggio per parte, l'avviso senza testo a chi deve leggere;
   2. prima della presa e per un estraneo la chat non c'e';
   3. la consegna a chi e' offline, e il segnalibro;
   4. un avviso per ogni «c'e' da leggere», non uno per messaggio; chi
      sta guardando non viene disturbato, chi ha appena chiuso si';
   5. i tetti: busta troppo lunga, forma storta, raffica, tetto di
      messaggi, la stessa busta rimandata;
   6. la parte che scambia da UN'ALTRA APP (una chiave che non e' di
      nessun account di qui): la chat non si apre, e niente si scrive;
   7. la disputa: la busta per il moderatore solo verso una chiave vera,
      e il moderatore legge solo dopo aver preso la disputa;
   8. la fine: le buste spariscono dal file, non solo dall'elenco;
   9. l'ordine tornato nel libro e ripreso da un altro: riparte da zero;
  10. la scopa del minuto, per lo scambio finito senza che l'evento
      passasse di qui;
  11. niente nel database di tutti (quello dei backup), niente testo
      nel journal, e gli accessi riusciti fuori dal registro.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram, niente relay, niente
coordinatore. Le buste qui sono testo a caso: il server non le apre, e
la crittografia vera gira nel banco node di `prove.py`.

USO:  python collaudo_chat_scambio.py
"""

import asyncio
import contextlib
import io
import json
import logging
import os
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
TG_V, TG_C, ESTRANEO, ADMIN = 222, 111, 333, 999
N1, N2, N3, N4 = -7001, -7002, -7003, -7004
ACCESSO = {}
DETTI = []          # (destinatario, testo, bottone) di ogni notifica
# LE ATTESE SI SCRIVONO RISPETTO ALLA SOGLIA, e la soglia e' larga: il
# server conta i secondi INTERI, e con una soglia di un secondo un
# ritiro alle 10,99 e un invio alle 11,01 distano «un secondo» — il
# collaudo passava o falliva secondo dove cadeva il secondo.
PRESENTE = 3                 # chi ha ritirato da meno di cosi' sta guardando
ASSENTE = PRESENTE + 0.4     # dopo quest'attesa NON sta piu' guardando
RIPASSO = PRESENTE + 1 + 0.9 # il secondo sguardo del server e' gia' passato


def adesso():
    return int(time.time())


def ordine(n):
    return f"c4a70000-c2c2-4a2b-9c3d-{n:012d}"


def chiave(n):
    # mai 64 esadecimali scritti per esteso: si compongono
    return f"{n:02x}" * 32


def busta(testo):
    """Una busta finta: base64 di qualcosa, che il server non apre."""
    import base64
    return base64.b64encode((testo + " " * 40).encode()).decode()


class Rifiuto(tuple):
    """Il no di una rotta, come coppia (codice, messaggio). Ha anche il
    `get` di un dizionario — che non trova mai niente — cosi' un
    controllo che aspettava una risposta da' una rossa col suo nome
    invece di far esplodere il giro."""

    def get(self, chiave, ripiego=None):
        return ripiego


def no(r):
    """Il codice di un rifiuto — o la parola «accettata» quando la rotta
    ha detto di si': una rotta che doveva rifiutare e non lo fa diventa
    una rossa col suo nome, non un errore che si porta via la sezione."""
    return r[0] if isinstance(r, Rifiuto) else "accettata"


async def chiama(fn, chi, corpo):
    """La rotta vera con l'autenticazione vera; un rifiuto torna come
    `Rifiuto` (codice, messaggio)."""
    try:
        r = await fn(banco.Busta(corpo), **ACCESSO[chi])
    except banco.SRV.HTTPException as e:
        return Rifiuto((e.status_code, str(e.detail)))
    return json.loads(r.body)


async def evento(o, azione, attore, dettaglio="", compra="", vende=""):
    b = banco.Busta({"v": 1, "order": o, "action": azione, "ts": adesso(),
                     "buyer": compra, "seller": vende,
                     "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    await banco.SRV.evento_p2p(b)
    await asyncio.sleep(0.3)


def pubblica(o, venditore):
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                "sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,15000,"
                "'10,00 €','[\"SEPA\"]')", (o, venditore, adesso()))
    con.commit()
    con.close()


def registra_chiave(k, tg):
    con = banco.con_db()
    con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) "
                "VALUES(?,?,?)", (k, tg, adesso()))
    con.commit()
    con.close()


def cassetto(sql, *a):
    cc = banco.SRV.db_chat()
    try:
        return cc.execute(sql, a).fetchall()
    finally:
        cc.close()


def avvisi_chat():
    return [(chi, t, b) for chi, t, b in DETTI
            if t.startswith("💬 <b>Hai un nuovo messaggio")]


async def scambio(n, venditore, compratore, kv, kc):
    """Una vendita pubblicata e presa: da qui la chat e' aperta."""
    o = ordine(n)
    pubblica(o, venditore)
    registra_chiave(kv, venditore)
    if compratore:
        registra_chiave(kc, compratore)
    await evento(o, "taken", "buyer", "invoice-next", kc, kv)
    return o


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    SRV.P2P_EVENTI_SEGRETO = SEGRETO
    SRV._p2p_per = lambda *a, **k: {"attivo": True}
    leggi, invia = SRV.chat_leggi_p2p, SRV.chat_invia_p2p
    moderatori, mod_chat = SRV.chat_moderatori_p2p, SRV.moderazione_chat_p2p

    async def notifica_finta(chi, testo, bottone=None, *a, **k):
        DETTI.append((chi, testo, bottone))
    SRV.notifica = notifica_finta

    # --- le identita': due da Telegram (l'initData di collaudo), quattro
    # da Nostr (il cookie di sessione VERO, nato da `crea_sessione`)
    con = banco.con_db()
    for tg, nome in ((N1, "Nostr uno"), (N2, "Nostr due"), (N3, "Nostr tre"),
                     (N4, "Nostr quattro"), (ADMIN, "Admin")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                    "ln_address) VALUES(?,?,?,1,'')", (tg, nome, f"neg{abs(tg)}"))
    con.commit()
    con.close()
    for tg, nome in ((TG_V, "Venditore"), (TG_C, "Compratore"),
                     (ESTRANEO, "Estraneo"), (ADMIN, "Admin")):
        ACCESSO[tg] = {"x_tg_init_data": f"collaudo:{tg}:{nome}",
                       "barattolo_sessione": ""}
    for tg in (N1, N2, N3, N4):
        ACCESSO[tg] = {"x_tg_init_data": "",
                       "barattolo_sessione": SRV.crea_sessione(tg)}
    SRV.P2P_CHAT_PRESENTE_S = PRESENTE

    # quel che le sezioni condividono: la prima coppia, la chiave del
    # moderatore e il suo pacco (di cartone: il server non lo apre)
    o = ordine(10)
    V, C = TG_V, TG_C
    kmod = chiave(0xAB)
    pacco = busta("pacco-per-il-moderatore")

    async def sezione(numero, titolo, corpo_sezione):
        """Una sezione, col suo try: se esplode e' una rossa col suo
        nome, e le sorelle girano lo stesso."""
        print(f"\n{numero}) {titolo}")
        try:
            await corpo_sezione()
        except Exception as e:
            prova(f"{numero}) la sezione gira", "", f"{type(e).__name__}: {e}")

    async def s1():
        coppie = (("Telegram/Telegram", TG_V, TG_C), ("Telegram/Nostr", TG_V, N1),
                  ("Nostr/Telegram", N2, TG_C), ("Nostr/Nostr", N3, N4))
        for i, (nome, v, c) in enumerate(coppie):
            o = await scambio(10 + i, v, c, chiave(0x10 + i), chiave(0x30 + i))
            a = await chiama(leggi, v, {"ordine": o, "dopo": 0})
            b = await chiama(leggi, c, {"ordine": o, "dopo": 0})
            prova(f"{nome}: presa la vendita, la chat e' aperta per tutti e due, vuota",
                  [(True, 1, []), (True, 1, [])],
                  [(x.get("aperta"), x.get("giro"), x.get("buste")) for x in (a, b)])
            del DETTI[:]
            await asyncio.sleep(ASSENTE)          # nessuno dei due sta guardando
            sv = await chiama(invia, v, {"ordine": o, "tipo": "saluto", "busta": busta(f"saluto-v-{i}")})
            sc = await chiama(invia, c, {"ordine": o, "tipo": "saluto", "busta": busta(f"saluto-c-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: presentarsi non avvisa nessuno (un saluto non e' un messaggio)",
                  [], [chi for chi, _, _ in avvisi_chat()])
            m1 = await chiama(invia, v, {"ordine": o, "tipo": "msg", "busta": busta(f"msg-v-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: saluti e messaggio accettati, coi numeri in fila", True,
                  0 < (sv.get("n") or 0) < (sc.get("n") or 0) < (m1.get("n") or 0))
            b = await chiama(leggi, c, {"ordine": o, "dopo": 0})
            arrivate = b.get("buste") or []
            prova(f"{nome}: chi compra ritira le tre buste, e sa quali sono sue",
                  [("saluto", False), ("saluto", True), ("msg", False)],
                  [(x["tipo"], x["mia"]) for x in arrivate])
            prova(f"{nome}: ...e la busta arriva com'e' partita", busta(f"msg-v-{i}"),
                  arrivate[-1]["busta"] if arrivate else "")
            detti = avvisi_chat()
            prova(f"{nome}: a chi compra un avviso solo, senza il testo, col bottone",
                  [(c, True, (SRV.P2P_BOTTONE_SCAMBIO, f"{SRV.LINK_LIBRO_P2P}?scambio={o}"))],
                  [(chi, f"#{o[:4]}" in t and "msg-v" not in t and busta(f"msg-v-{i}") not in t, bt)
                   for chi, t, bt in detti])
            del DETTI[:]
            await asyncio.sleep(ASSENTE)
            await chiama(invia, c, {"ordine": o, "tipo": "msg", "busta": busta(f"msg-c-{i}")})
            await asyncio.sleep(0.4)
            prova(f"{nome}: ...e la risposta avvisa chi vende", [v],
                  [chi for chi, _, _ in avvisi_chat()])

    async def s2():
        libera = ordine(50)
        pubblica(libera, V)
        r = await chiama(leggi, V, {"ordine": libera, "dopo": 0})
        prova("ordine ancora nel libro: per chi l'ha pubblicato la chat non e' aperta",
              (False, True), (r.get("aperta"), r.get("finita")))
        prova("...e non si puo' spedire", 409,
              no(await chiama(invia, V, {"ordine": libera, "tipo": "msg", "busta": busta("x")})))
        prova("un estraneo: 403 su leggere, spedire e chiedere i moderatori", [403, 403, 403],
              [no(await chiama(leggi, ESTRANEO, {"ordine": o, "dopo": 0})),
               no(await chiama(invia, ESTRANEO, {"ordine": o, "tipo": "msg", "busta": busta("x")})),
               no(await chiama(moderatori, ESTRANEO, {"ordine": o}))])
        prova("un ordine in una forma storta: 400", 400,
              no(await chiama(leggi, V, {"ordine": "../../etc", "dopo": 0})))

    async def s3():
        fin_qui = (await chiama(leggi, C, {"ordine": o, "dopo": 0}))["fino"]
        for k in range(3):
            await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta(f"offline-{k}")})
        r = await chiama(leggi, C, {"ordine": o, "dopo": fin_qui})
        prova("tre messaggi scritti ad app chiusa: al ritorno arrivano tutti, in ordine",
              [busta(f"offline-{k}") for k in range(3)], [x["busta"] for x in r["buste"]])
        prova("...e col segnalibro nuovo non tornano una seconda volta", [],
              (await chiama(leggi, C, {"ordine": o, "dopo": r["fino"]}))["buste"])
        perso = await chiama(leggi, C, {"ordine": o, "dopo": 10 ** 9})
        prova("un segnalibro OLTRE l'ultima busta dello scambio (il file e' rinato): "
              "il server lo dice, e rida' tutto da capo", (True, True),
              (perso.get("perso"), len(perso["buste"]) >= 7))
        prova("...un segnalibro giusto no", False,
              (await chiama(leggi, C, {"ordine": o, "dopo": perso["fino"]})).get("perso"))

    async def s4():
        await asyncio.sleep(RIPASSO)
        del DETTI[:]
        await asyncio.sleep(ASSENTE)
        for k in range(3):
            await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta(f"raffica-{k}")})
        await asyncio.sleep(0.3)
        prova("tre messaggi di fila a chi non guarda: un avviso solo", [C],
              [chi for chi, _, _ in avvisi_chat()])
        del DETTI[:]
        await chiama(leggi, C, {"ordine": o, "dopo": 0})          # legge...
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("appena-chiuso")})
        await asyncio.sleep(0.3)
        prova("ha ritirato un attimo fa: subito non lo si disturba", [],
              [chi for chi, _, _ in avvisi_chat()])
        await asyncio.sleep(RIPASSO)                                   # ...e non torna
        prova("...ma se non torna a leggere, l'avviso parte poco dopo", [C],
              [chi for chi, _, _ in avvisi_chat()])
        del DETTI[:]
        r = await chiama(leggi, C, {"ordine": o, "dopo": 0})
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("sta-guardando")})
        await asyncio.sleep(0.5)
        await chiama(leggi, C, {"ordine": o, "dopo": r["fino"]})  # sta guardando: lo ritira
        await asyncio.sleep(RIPASSO)
        prova("chi tiene la chat aperta e ritira non riceve nessun avviso", [],
              [chi for chi, _, _ in avvisi_chat()])
        con = banco.con_db()
        con.execute("UPDATE utenti SET avvisi_p2p=0 WHERE tg_id=?", (C,))
        con.commit()
        con.close()
        await asyncio.sleep(ASSENTE)
        await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("avvisi-spenti")})
        await asyncio.sleep(0.3)
        prova("avvisi P2P spenti: la busta si consegna, l'avviso no", [],
              [chi for chi, _, _ in avvisi_chat()])
        con = banco.con_db()
        con.execute("UPDATE utenti SET avvisi_p2p=1 WHERE tg_id=?", (C,))
        con.commit()
        con.close()

    async def s5():
        prova("una busta oltre il tetto: 413", 413,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                       "busta": "A" * (SRV.P2P_CHAT_BUSTA_MAX + 4)})))
        prova("una busta che non e' una busta (testo in chiaro): 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                       "busta": "ciao, ti mando l'IBAN in chiaro " * 3})))
        prova("un tipo che non esiste: 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "foto", "busta": busta("x")})))
        prova("un messaggio con un destinatario: 400 (il `per` e' solo dei moderatori)", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": busta("x"),
                                       "per": chiave(0x77)})))
        stessa = busta("la-stessa-due-volte")
        a = await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": stessa})
        b = await chiama(invia, V, {"ordine": o, "tipo": "msg", "busta": stessa})
        prova("la stessa busta rimandata: stesso numero, una riga sola",
              (True, 1), (a["n"] == b["n"],
                          len(cassetto("SELECT 1 FROM buste WHERE busta=?", stessa))))
        r2 = ordine(51)
        await scambio(51, V, C, chiave(0x51), chiave(0x52))
        SRV.P2P_CHAT_RAFFICA = 5
        esiti = [await chiama(invia, V, {"ordine": r2, "tipo": "msg", "busta": busta(f"r-{k}")})
                 for k in range(7)]
        prova("la raffica: cinque passano, dalla sesta 429",
              [True] * 5 + [429, 429],
              [e.get("ok") if isinstance(e, dict) else e[0] for e in esiti])
        SRV.P2P_CHAT_RAFFICA = 1000
        SRV.P2P_CHAT_MSG_MAX = 8
        esiti = [await chiama(invia, C, {"ordine": r2, "tipo": "msg", "busta": busta(f"t-{k}")})
                 for k in range(5)]
        prova("il tetto di messaggi dello scambio: oltre, 409",
              [True, True, True, 409, 409],
              [e.get("ok") if isinstance(e, dict) else e[0] for e in esiti])
        SRV.P2P_CHAT_MSG_MAX = 200
        SRV.P2P_CHAT_RAFFICA = 20

    async def s6():
        fuori = await scambio(60, V, 0, chiave(0x60), chiave(0x61))
        r = await chiama(leggi, V, {"ordine": fuori, "dopo": 0})
        prova("dall'altra parte una chiave che non e' di nessun account: la chat non si apre",
              (False, False, True), (r.get("aperta"), r.get("finita"), r.get("senza_altro")))
        prova("...non si spedisce, e nel cassetto non si scrive niente",
              (409, 0), (no(await chiama(invia, V, {"ordine": fuori, "tipo": "saluto",
                                                  "busta": busta("s")})),
                         len(cassetto("SELECT 1 FROM buste WHERE ordine=?", fuori))))

    async def s7():
        con = banco.con_db()
        con.execute("INSERT OR REPLACE INTO p2p_moderatori(tg_id, chiave, creata) "
                    "VALUES(?,?,?)", (ADMIN, kmod, adesso()))
        con.commit()
        con.close()
        await evento(o, "hold-invoice-paid", "seller", "active", chiave(0x30), chiave(0x10))
        r = await chiama(moderatori, V, {"ordine": o})
        prova("a una delle due parti il server dice le chiavi pubbliche dei moderatori",
              [kmod], r.get("chiavi"))
        prova("una busta `mod` verso una chiave che non e' di un moderatore: 400", 400,
              no(await chiama(invia, V, {"ordine": o, "tipo": "mod", "busta": busta("pacco"),
                                       "per": chiave(0xEE)})))
        await evento(o, "dispute-opened", "seller", "", chiave(0x30), chiave(0x10))
        # la riga della disputa la scrive il task degli avvisi: la si aspetta,
        # invece di sperare che tre decimi bastino su una macchina carica
        for _ in range(50):
            con = banco.con_db()
            c_e = con.execute("SELECT 1 FROM p2p_dispute WHERE ordine=?", (o,)).fetchone()
            con.close()
            if c_e:
                break
            await asyncio.sleep(0.1)
        r = await chiama(leggi, V, {"ordine": o, "dopo": 0})
        prova("a disputa aperta la chat resta aperta", True, r.get("aperta"))
        r = await chiama(invia, V, {"ordine": o, "tipo": "mod", "busta": pacco, "per": kmod})
        prova("la busta per il moderatore si accetta", True, r.get("ok"))
        prova("...e alle parti non torna mai fra le buste da ritirare", False,
              pacco in json.dumps(await chiama(leggi, C, {"ordine": o, "dopo": 0})))
        prova("il moderatore PRIMA di prendere la disputa non legge: 409", 409,
              no(await chiama(mod_chat, ADMIN, {"ordine": o})))
        prova("chi non e' moderatore: 403", 403, no(await chiama(mod_chat, V, {"ordine": o})))
        con = banco.con_db()
        con.execute("UPDATE p2p_dispute SET stato='presa', presa_da=?, presa_il=?, "
                    "chiave_moderatore=? WHERE ordine=?", (ADMIN, adesso(), kmod, o))
        con.commit()
        righe_disputa = con.execute("SELECT stato FROM p2p_dispute WHERE ordine=?",
                                    (o,)).fetchall()
        con.close()
        prova("(il coordinatore ha raccontato la disputa, ed e' presa)", ["presa"],
              [x["stato"] for x in righe_disputa])
        letture_prima = [tuple(x) for x in cassetto(
            "SELECT tg_id, letto_fino FROM letture WHERE ordine=? ORDER BY tg_id", o)]
        r = await chiama(mod_chat, ADMIN, {"ordine": o})
        prova("presa la disputa, il moderatore riceve i messaggi chiusi e il SUO pacco",
              (True, [pacco], True),
              (len(r.get("buste", [])) >= 8, [x["busta"] for x in r.get("chiavi", [])],
               {x["lato"] for x in r["buste"]} == {"compra", "vende"}))
        prova("...e leggendo non sposta il segnalibro di nessuna delle due parti",
              letture_prima, [tuple(x) for x in cassetto(
                  "SELECT tg_id, letto_fino FROM letture WHERE ordine=? ORDER BY tg_id", o)])
        con = banco.con_db()
        con.execute("UPDATE p2p_dispute SET chiave_moderatore=? WHERE ordine=?",
                    (chiave(0xAC), o))
        con.commit()
        con.close()
        prova("un pacco chiuso per un'altra chiave non gli arriva", [],
              (await chiama(mod_chat, ADMIN, {"ordine": o}))["chiavi"])

    async def s8():
        segno = busta("offline-1").encode()
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("(prima della fine la busta nel file c'e')", True, segno in grezzo)
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await evento(o, "released", "mostro", "admin", chiave(0x30), chiave(0x10))
        prova("chiuso lo scambio (il moderatore ha deciso): nel cassetto non resta una riga",
              (0, 0), (len(cassetto("SELECT 1 FROM buste WHERE ordine=?", o)),
                       len(cassetto("SELECT 1 FROM letture WHERE ordine=?", o))))
        grezzo = open(SRV.DB_CHAT, "rb").read()
        prova("...e nel FILE i byte di quelle buste non ci sono piu' (secure_delete)",
              (False, False), (segno in grezzo, pacco.encode() in grezzo))
        prova("...il journal lo dice con una riga, senza una busta dentro",
              (True, False), ("🧹 Chat P2P: lo scambio " + o[:8] in giornale.getvalue(),
                              busta("offline-1") in giornale.getvalue()))
        r = await chiama(leggi, C, {"ordine": o, "dopo": 0})
        prova("al telefono il server dice che e' FINITA (e' li' che butta la chiave)",
              (False, True), (r.get("aperta"), r.get("finita")))
        dopo = await chiama(mod_chat, ADMIN, {"ordine": o})
        prova("...non si spedisce piu', e il moderatore non ha piu' niente da leggere",
              (409, True), (no(await chiama(invia, V, {"ordine": o, "tipo": "msg",
                                                     "busta": busta("dopo")})),
                            dopo[0] == 409 if isinstance(dopo, tuple)
                            else dopo.get("buste") == [] and dopo.get("chiavi") == []))

    async def s9():
        t = await scambio(90, V, C, chiave(0x90), chiave(0x91))
        await chiama(invia, V, {"ordine": t, "tipo": "msg", "busta": busta("giro-uno")})
        await chiama(leggi, C, {"ordine": t, "dopo": 0})
        await evento(t, "expired", "mostro", "taker-timeout", chiave(0x91), chiave(0x90))
        prova("chi aveva preso non ha proseguito: le buste di quel giro se ne vanno", 0,
              len(cassetto("SELECT 1 FROM buste WHERE ordine=?", t)))
        registra_chiave(chiave(0x92), N1)
        # UN SECONDO PIENO fra le due prese: stesso ordine, stesso momento e
        # stessa ora scritta sono, per la rotta degli eventi, il RETRY del
        # coordinatore — e la seconda presa non verrebbe registrata (il
        # collaudo passava o esplodeva secondo dove cadeva il secondo)
        await asyncio.sleep(1.1)
        await evento(t, "taken", "buyer", "invoice-next", chiave(0x92), chiave(0x90))
        r = await chiama(leggi, N1, {"ordine": t, "dopo": 0})
        prova("ripreso da un altro: giro nuovo, chat vuota", (True, 2, []),
              (r.get("aperta"), r.get("giro"), r.get("buste")))
        prova("...e chi l'aveva preso prima adesso e' un estraneo", 403,
              no(await chiama(leggi, C, {"ordine": t, "dopo": 0})))

    async def s10():
        s = await scambio(100, V, C, chiave(0xA0), chiave(0xA1))
        await chiama(invia, V, {"ordine": s, "tipo": "msg", "busta": busta("scopa")})
        await chiama(leggi, C, {"ordine": s, "dopo": 0})
        con = banco.con_db()
        con.execute("INSERT INTO p2p_momenti(ordine, momento, quando, fonte, giro) "
                    "VALUES(?,'annullato',?,'mostro',1)", (s, adesso()))
        con.execute("UPDATE p2p_ordini SET stato='canceled' WHERE ordine=?", (s,))
        con.commit()
        con.close()
        prova("(lo scambio e' finito senza che l'evento passasse dalla rotta: le buste ci sono)",
              1, len(cassetto("SELECT 1 FROM buste WHERE ordine=?", s)))
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await SRV._giro_chat_p2p()
        prova("la scopa le toglie, e lo dice", (0, 0, True),
              (len(cassetto("SELECT 1 FROM buste WHERE ordine=?", s)),
               len(cassetto("SELECT 1 FROM letture WHERE ordine=?", s)),
               "🧹 Chat P2P: cancellate le buste di 1 scambio finito" in giornale.getvalue()))
        vivo = cassetto("SELECT COUNT(*) FROM buste WHERE ordine=?", ordine(11))[0][0]
        prova("...e non tocca gli scambi ancora in corso", True, vivo >= 3)
        cc = SRV.db_chat()
        cc.execute("INSERT INTO buste(ordine, giro, da, tipo, busta, quando) VALUES(?,?,?,?,?,?)",
                   (ordine(11), 1, TG_V, "msg", busta("vecchissima"),
                    adesso() - SRV.P2P_CHAT_VITA_MAX_S - 60))
        cc.commit()
        cc.close()
        await SRV._giro_chat_p2p()
        prova("la rete sotto la scopa: una busta piu' vecchia di ogni scambio possibile se ne va",
              0, len(cassetto("SELECT 1 FROM buste WHERE busta=?", busta("vecchissima"))))

    async def s11():
        prova("il cassetto e' un file a parte, accanto al database di tutti",
              (True, True), (os.path.realpath(SRV.DB_CHAT) != os.path.realpath(SRV.DB),
                             os.path.dirname(os.path.realpath(SRV.DB_CHAT))
                             == os.path.dirname(os.path.realpath(SRV.DB))))
        viva = busta("msg-v-1").encode()
        prova("una busta viva sta nel cassetto e NON nel database di tutti (quello dei backup)",
              (True, False), (viva in open(SRV.DB_CHAT, "rb").read(),
                              viva in open(SRV.DB, "rb").read()))
        con = banco.con_db()
        tabelle = [x[0] for x in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND "
            "(name LIKE '%chat%' OR name IN ('buste', 'letture'))")]
        con.close()
        prova("...che di tabelle della chat non ne ha nessuna", [], tabelle)
        giornale = io.StringIO()
        with contextlib.redirect_stdout(giornale):
            await asyncio.sleep(ASSENTE)
            await chiama(invia, TG_V, {"ordine": ordine(11), "tipo": "msg",
                                       "busta": busta("nel-journal"),
                                       "testo": "IBAN SEGRETO IN CHIARO"})
            await asyncio.sleep(0.3)
        prova("un invio riuscito scrive nel journal la sola riga dell'avviso",
              (True, False, False),
              (f"💬 Chat P2P: nuovo messaggio sullo scambio {ordine(11)[:8]}, avvisato {N1}"
               in giornale.getvalue(), busta("nel-journal") in giornale.getvalue(),
               "SEGRETO" in giornale.getvalue()))
        prova("...e un campo `testo` messo nel corpo apposta non finisce da nessuna parte",
              False, b"SEGRETO" in open(SRV.DB_CHAT, "rb").read()
              or "SEGRETO" in json.dumps(DETTI, ensure_ascii=False))
        filtro = SRV._ChatFuoriDalJournal()

        def passa(strada, codice):
            return filtro.filter(logging.LogRecord(
                "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                ("127.0.0.1:1", "POST", strada, "1.1", codice), None))
        prova("gli accessi RIUSCITI della chat non vanno nel registro; gli errori e il resto si'",
              [False, False, False, False, True, True, True],
              [passa("/api/p2p/chat/leggi", 200), passa("/api/p2p/chat/invia", 200),
               passa("/api/p2p/chat/moderatori", 200), passa("/api/p2p/moderazione/chat", 200),
               passa("/api/p2p/chat/invia", 429), passa("/api/p2p/chat/leggi", 500),
               passa("/api/p2p/recapito", 200)])

    await sezione(1, "LE QUATTRO COPPIE DI ACCESSO", s1)
    await sezione(2, "PRIMA DELLA PRESA, E PER UN ESTRANEO", s2)
    await sezione(3, "LA CONSEGNA A CHI E' OFFLINE", s3)
    await sezione(4, "UN AVVISO PER OGNI «C'E' DA LEGGERE»", s4)
    await sezione(5, "I TETTI", s5)
    await sezione(6, "LA PARTE CHE SCAMBIA DA UN'ALTRA APP", s6)
    await sezione(7, "LA DISPUTA E IL MODERATORE", s7)
    await sezione(8, "LA FINE: LE BUSTE SPARISCONO DAL FILE", s8)
    await sezione(9, "L'ORDINE TORNATO NEL LIBRO E RIPRESO DA UN ALTRO", s9)
    await sezione(10, "LA SCOPA DEL MINUTO", s10)
    await sezione(11, "NIENTE ALTROVE", s11)
    for gruppo in (SRV._TASK_EVENTI_P2P, SRV._TASK_CHAT_P2P):
        if gruppo:
            await asyncio.gather(*list(gruppo), return_exceptions=True)


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
