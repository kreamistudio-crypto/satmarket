# -*- coding: utf-8 -*-
"""
IL TEMPO DI CHI PUBBLICA SUL SERVER VERO, CON GLI EVENTI FINTI DEL
COORDINATORE (12 ott 2026, cantiere tempo-di-chi-pubblica, decisioni di
Andrea dopo lo studio).

Il caso: chi PUBBLICA un ordine non sa quando glielo prenderanno, e con
la mezz'ora di tutti chi dormiva si ritrovava l'ordine annullato. Da qui
il pacchetto: il coordinatore gli da' piu' tempo e, se non risponde,
rimette l'ordine nel libro (patch 0011 del fork); il server — dietro la
leva P2P_TEMPO_DI_CHI_PUBBLICA — porta la pausa degli ordini, il «non
completato» a chi pubblica e non risponde (con le sue tutele), il badge
«⚡ risponde in fretta» e i quattro avvisi. `prove.py` difende i giudici
estratti (`prove_tempo_di_chi_pubblica`); qui girano le ROTTE VERE —
`/api/p2p/evento` col bearer di mostrod, `/api/p2p/pausa` (lettura e
scrittura), `/api/p2p/posso-prendere`, `/api/p2p/facce`, «dimentica il
profilo» — su un database usa-e-getta, e si guarda cosa resta scritto:

  1. A LEVA SPENTA e' come ieri: la pausa non si legge e non si scrive,
     e il tempo scaduto di chi pubblica non conta a nessuno;
  2. la pausa: le forme storte sono un 400, quella buona si rilegge, e
     `fino` dice quando finisce;
  3. in pausa l'ordine esce coi volti (`pause`) e «posso prendere?» lo
     ferma col motivo `pausa` — ma non a chi l'ha pubblicato;
  4. una presa arrivata IN PAUSA e lasciata scadere non conta;
  5. tolta la pausa: il tempo scaduto di chi pubblica (`maker-
     republished`) e' un «mancato» a LUI e niente a chi ha preso; i
     promemoria sono tre; le due frasi sono quelle giuste;
  6. la seconda di fila sullo stesso ordine non conta due volte, e la
     frase dice che l'ordine e' stato tolto;
  7. l'annullo a mano dopo una presa conta, e dal secondo la scritta
     compare sul volto dei suoi ordini;
  8. il badge: tre scambi conclusi con tre persone diverse, risposta
     entro dieci minuti → `veloce` sul volto e nei propri numeri;
  8-ter. chi e' NATO SU NOSTR (id negativo) in pausa esce dal libro e
     non si prende, come tutti (13 ott 2026, cantiere pausa-nativi);
  9. «dimentica il profilo» porta via la pausa.

NON TOCCA NIENTE DI VERO: il config e' di cartone (quello di
`collaudo_pagamento_p2p`), niente Telegram (le notifiche finiscono in
una lista), niente relay, niente coordinatore.

USO:  python collaudo_tempo_pubblica.py
"""

import asyncio
import json
import re
import sys
import time

import collaudo_pagamento_p2p as banco

SEGRETO = "collaudo-segreto"
A = "7e3a0000-0a0a-4a2b-9c3d-00000000000a"      # vendita di 111: leva spenta
B = "7e3a0000-0b0b-4a2b-9c3d-00000000000b"      # vendita di 111: presa in pausa
C = "7e3a0000-0c0c-4a2b-9c3d-00000000000c"      # vendita di 111: due mancate di fila
D = "7e3a0000-0d0d-4a2b-9c3d-00000000000d"      # vendita di 111: annullata a mano dopo la presa
V1 = "7e3a0000-0101-4a2b-9c3d-000000000011"     # tre vendite di 333, concluse in fretta
V2 = "7e3a0000-0202-4a2b-9c3d-000000000012"
V3 = "7e3a0000-0303-4a2b-9c3d-000000000013"
PUBBLICA, PRENDE, VELOCE = banco.VENDE, banco.COMPRA, banco.ESTRANEO
ALTRI = {444: "c3" * 32, 555: "d4" * 32}
CHIAVE_VELOCE = "e5" * 32
_TAG = re.compile(r"</?[bi]>")


def info(prende=1800, pubblica=10800, limite=2):
    """Il 38385 di cartone: i soli tag che servono."""
    tags = [["d", "x"], ["expiration_seconds", str(prende)]]
    if pubblica:
        tags.append(["maker_expiration_seconds", str(pubblica)])
    if limite:
        tags.append(["maker_timeout_limit", str(limite)])
    return {"kind": 38385, "tags": tags}


def busta(ordine, azione, ts, attore, dettaglio, buyer=banco.CHIAVE_COMPRA,
          seller=banco.CHIAVE_VENDE):
    b = banco.Busta({"v": 1, "order": ordine, "action": azione, "ts": ts, "buyer": buyer,
                     "seller": seller, "actor": attore, "detail": dettaglio})
    b.headers = {"authorization": f"Bearer {SEGRETO}"}
    return b


async def posta(b):
    """Il POST di mostrod alla rotta vera, e i suoi avvisi lasciati finire."""
    try:
        r = await banco.SRV.evento_p2p(b)
    except Exception as e:
        return getattr(e, "status_code", type(e).__name__)
    if banco.SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(banco.SRV._TASK_EVENTI_P2P), return_exceptions=True)
    return json.loads(r.body)


async def presa(ordine, t, buyer=banco.CHIAVE_COMPRA, seller=banco.CHIAVE_VENDE):
    """Una vendita presa da chi compra, fino alla garanzia chiesta a chi
    l'ha pubblicata."""
    await posta(busta(ordine, "taken", t, "buyer", "invoice-next", buyer, seller))
    await posta(busta(ordine, "buyer-invoice-requested", t, "mostro", "", buyer, seller))
    await posta(busta(ordine, "buyer-invoice-added", t + 1, "buyer", "hold-next", buyer, seller))
    await posta(busta(ordine, "hold-invoice-requested", t + 1, "mostro", "invoice", buyer, seller))


def esiti(tg, ordine=None):
    con = banco.con_db()
    q, a = "SELECT esito, dettaglio FROM p2p_esiti WHERE tg_id=?", [tg]
    if ordine:
        q, a = q + " AND ordine=?", a + [ordine]
    r = sorted(tuple(x) for x in con.execute(q, a))
    con.close()
    return r


def attese(ordine, tg):
    con = banco.con_db()
    r = [(x[0], int(x[1])) for x in con.execute(
        "SELECT momento, scade FROM p2p_attese WHERE ordine=? AND tg_id=? AND "
        "fonte='promemoria' ORDER BY scade", (ordine, tg))]
    con.close()
    return r


def detto(a_chi, frammento):
    """L'ultima notifica a quella persona che contiene il frammento, senza tag."""
    for chi, testo in reversed(banco.DETTO):
        t = _TAG.sub("", testo)
        if chi == a_chi and frammento in t:
            return t
    return ""


async def chiama(fn, corpo=None):
    d = corpo if corpo is not None else {}

    async def leggi(_req):
        if not isinstance(d, dict):
            raise banco.SRV.HTTPException(400, "Richiesta malformata")
        return d
    banco.SRV.leggi_json = leggi
    try:
        r = await fn(banco.Busta(d))
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))
    return json.loads(r.body) if hasattr(r, "body") else r


def leggi_pausa(chi):
    banco.come(chi)
    return json.loads(banco.SRV.mia_pausa_p2p().body)


async def scrivi_pausa(chi, corpo):
    banco.come(chi)
    return await chiama(banco.SRV.scrivi_pausa_p2p, corpo)


async def posso(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.posso_prendere_p2p, {"ordini": ordini})


async def facce(chi, ordini):
    banco.come(chi)
    return await chiama(banco.SRV.facce_ordini_p2p, {"ordini": ordini})


def semina_ordini():
    con = banco.con_db()
    adesso = int(time.time())
    for tg, chiave in list(ALTRI.items()) + [(VELOCE, CHIAVE_VELOCE)]:
        con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                    "VALUES(?,?,?,1,'')", (tg, f"Persona {tg}", f"neg{tg}"))
        con.execute("INSERT OR REPLACE INTO chiavi_p2p(pubkey, tg_id, creato) VALUES(?,?,?)",
                    (chiave, tg, adesso))
    for ordine, chi in ((A, PUBBLICA), (B, PUBBLICA), (C, PUBBLICA), (D, PUBBLICA),
                        (V1, VELOCE), (V2, VELOCE), (V3, VELOCE)):
        con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,"
                    "metodi) VALUES(?,?,?,'pending','sell',1,15000,'10,00 €',?)",
                    (ordine, chi, adesso, json.dumps(["SEPA"])))
    con.commit()
    con.close()


async def giro():
    SRV = banco.SRV
    prova = banco.prova
    t0 = int(time.time()) - 600

    print("\n1) a leva spenta e' come ieri")
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = False
    SRV._P2P_FOTO["info"] = info()
    prova("la pausa non si legge: `attiva` falsa e niente altro", {"attiva": False},
          leggi_pausa(PUBBLICA))
    prova("...e non si scrive: 409", 409, (await scrivi_pausa(PUBBLICA, {"fasce": []}))[0])
    await presa(A, t0)
    prova("il tempo scaduto di chi pubblica entra", True,
          (await posta(busta(A, "expired", t0 + 5, "mostro", "maker-republished")))["nuovo"])
    prova("...e non scrive niente a nessuno: la regola del 10 ott",
          ([], []), (esiti(PUBBLICA), esiti(PRENDE)))
    prova("...ma le due frasi sono gia' quelle del ritorno per colpa di chi ha pubblicato",
          (True, True),
          (detto(PUBBLICA, "Non hai risposto in tempo").startswith(
              "⏰ Non hai risposto in tempo: il tuo ordine è tornato nel libro."),
           detto(PRENDE, "Chi aveva pubblicato").endswith(
               "lo scambio è annullato, non devi fare niente.")))

    print("\n2) la pausa: le forme, la scrittura, la rilettura")
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True
    prova("senza una pausa si legge la forma vuota",
          (True, [], 0, 6, 7),
          tuple(leggi_pausa(PUBBLICA)[k] for k in
                ("attiva", "fasce", "fino", "massimo_fasce", "massimo_giorni")))
    prova("una fascia senza giorni e' un 400, e lo dice", (400, "Scegli almeno un giorno per ogni fascia"),
          await scrivi_pausa(PUBBLICA, {"fasce": [{"g": [], "da": 60, "a": 120}]}))
    prova("...e una pausa una tantum di otto giorni pure", 400,
          (await scrivi_pausa(PUBBLICA, {"una_fino": int(time.time()) + 8 * 86400}))[0])
    # una fascia che copre ADESSO, tutti i giorni, nel fuso UTC: da dieci
    # minuti fa a fra un'ora
    minuti = (int(time.time()) // 60) % 1440
    fascia = {"g": [0, 1, 2, 3, 4, 5, 6], "da": (minuti - 10) % 1440, "a": (minuti + 60) % 1440}
    r = await scrivi_pausa(PUBBLICA, {"fasce": [fascia], "fuso": "UTC", "scarto": 0})
    fra_un_ora = (int(time.time()) // 60 + 60) * 60
    prova("la pausa buona si salva, e `fino` e' la fine della fascia di adesso",
          (True, [fascia], True), (r.get("attiva"), r.get("fasce"),
                                   abs(int(r.get("fino") or 0) - fra_un_ora) <= 60))
    prova("...e si rilegge uguale", [fascia], leggi_pausa(PUBBLICA)["fasce"])
    prova("...chi non l'ha messa non la vede: la pausa e' di chi chiede", [],
          leggi_pausa(PRENDE)["fasce"])

    print("\n3) in pausa l'ordine non si prende da qui")
    r = await posso(PRENDE, [B, V1])
    prova("«posso prendere?» lo ferma col motivo `pausa` e l'ora del ritorno",
          (False, "pausa", True, True),
          (r["ordini"][B]["ok"], r["ordini"][B]["motivo"],
           abs(int(r["ordini"][B].get("fino") or 0) - fra_un_ora) <= 60, r["ordini"][V1]["ok"]))
    prova("...ma a chi l'ha pubblicato il SUO ordine non dice «pausa»", True,
          (await posso(PUBBLICA, [B]))["ordini"][B]["motivo"] != "pausa")
    f = await facce(PRENDE, [B, V1])
    prova("...e coi volti esce la mappa delle pause: quell'ordine si', l'altro no",
          (True, False), (B in f.get("pause", {}), V1 in f.get("pause", {})))

    print("\n4) una presa arrivata in pausa non conta")
    await presa(B, t0 + 20)
    await posta(busta(B, "expired", t0 + 25, "mostro", "maker-republished"))
    prova("ne' il «mancato» ne' la riga del badge", [], esiti(PUBBLICA, B))

    print("\n5) tolta la pausa: il «non completato» a chi pubblica e non risponde")
    r = await scrivi_pausa(PUBBLICA, {"fasce": []})
    prova("una pausa vuota la TOGLIE", ([], 0), (r.get("fasce"), r.get("fino")))
    await presa(C, t0 + 40)
    prova("i promemoria a chi pubblica sono tre: a 10 minuti, a un'ora, mezz'ora prima della fine",
          [("garanzia_promemoria", t0 + 41 + 600), ("garanzia_promemoria2", t0 + 41 + 3600),
           ("garanzia_promemoria3", t0 + 41 + 10800 - 1800)], attese(C, PUBBLICA))
    # l'evento e' di dieci minuti fa (l'orologio di mostrod): delle sue tre
    # ore ne restano due e una cinquantina di minuti, e la frase dice quelle
    prova("...e il primo avviso gli dice le SUE ore — quelle che restano — e cosa succede dopo",
          True, bool(re.search(
              r"⏳ Hai 2 ore e \d+ minuti, poi l'ordine torna nel libro e ti conta come "
              r"scambio non completato\.$", detto(PUBBLICA, "Paga la garanzia"))))
    await posta(busta(C, "expired", t0 + 50, "mostro", "maker-republished"))
    prova("allo scadere: «mancato» a chi ha PUBBLICATO (con la riga del badge), niente a chi ha preso",
          ([("mancato", "maker-republished"), ("senza_risposta", "maker-republished")], []),
          (esiti(PUBBLICA, C), esiti(PRENDE, C)))
    prova("...glielo si dice, con la riga del conto", True,
          "Questo conta come scambio non completato" in detto(PUBBLICA, "tornato nel libro"))
    prova("...e i promemoria rimasti se ne vanno", [], attese(C, PUBBLICA))

    print("\n6) la seconda di fila sullo stesso ordine")
    await presa(C, t0 + 60, buyer=ALTRI[444])
    await posta(busta(C, "expired", t0 + 70, "mostro", "maker-timeout", buyer=ALTRI[444]))
    prova("non si conta due volte: un «mancato» solo su quell'ordine",
          [("mancato", "maker-republished"), ("senza_risposta", "maker-republished"),
           ("senza_risposta", "maker-timeout")], esiti(PUBBLICA, C))
    prova("...e la frase dice che l'ordine e' stato tolto",
          "⏰ Non hai risposto a due prese di fila: il tuo ordine è stato tolto dal libro. "
          "Puoi ripubblicarlo quando vuoi.", detto(PUBBLICA, "due prese di fila"))

    print("\n7) l'annullo a mano dopo una presa")
    # la scusa del tentativo ha la sua prova: qui nessuno ci ha provato
    await presa(D, t0 + 80)
    await posta(busta(D, "canceled", t0 + 90, "seller", ""))
    prova("conta come mancata risposta", [("mancato", "maker-annullo"),
                                          ("senza_risposta", "maker-annullo")],
          esiti(PUBBLICA, D))
    f = await facce(PRENDE, [D])
    prova("...e dal secondo la scritta compare sul volto dei suoi ordini", 2,
          f["facce"].get(D, {}).get("mancati"))
    prova("...chi ha preso, in tutto questo, non ha nessun esito", [], esiti(PRENDE))

    print("\n8) il badge «⚡ risponde in fretta»")
    for ordine, chiave in ((V1, banco.CHIAVE_COMPRA), (V2, ALTRI[444]), (V3, ALTRI[555])):
        t = t0 + 100 + (10 * (ordine[-1] == "2")) + (20 * (ordine[-1] == "3"))
        await presa(ordine, t, buyer=chiave, seller=CHIAVE_VELOCE)
        await posta(busta(ordine, "hold-invoice-paid", t + 3, "seller", "active", chiave, CHIAVE_VELOCE))
        await posta(busta(ordine, "success", t + 5, "mostro", "", chiave, CHIAVE_VELOCE))
        if ordine == V2:
            prova("due scambi conclusi non bastano", None,
                  (await facce(PRENDE, [V1]))["facce"].get(V1, {}).get("veloce"))
    con = banco.con_db()
    con.execute("INSERT INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,sats,euro,metodi) "
                "VALUES('7e3a0000-0404-4a2b-9c3d-000000000014',?,?,'pending','sell',1,15000,"
                "'10,00 €','[\"SEPA\"]')", (VELOCE, int(time.time())))
    con.commit()
    con.close()
    NUOVO = "7e3a0000-0404-4a2b-9c3d-000000000014"
    f = await facce(PRENDE, [NUOVO, C])
    prova("tre scambi conclusi con tre persone diverse, risposta in pochi secondi: il volto "
          "dei suoi ordini porta `veloce`; quello di chi non ha risposto no",
          (True, None), (f["facce"].get(NUOVO, {}).get("veloce"),
                         f["facce"].get(C, {}).get("veloce")))
    prova("...e chi ce l'ha lo legge fra i suoi numeri", (True, False),
          ((await posso(VELOCE, []))["veloce"], (await posso(PUBBLICA, []))["veloce"]))

    print("\n8-bis) la pausa in vista: Barattozon resta nel libro, e il bottone sotto la presa")
    # (12 ott 2026, sera, cantiere pausa-in-vista) tre ordini nuovi di chi
    # pubblica: una vendita Barattozon e due vendite SEPA
    BZ = "7e3a0000-0e0e-4a2b-9c3d-00000000000e"
    N1 = "7e3a0000-0f0f-4a2b-9c3d-00000000000f"
    N2 = "7e3a0000-1010-4a2b-9c3d-000000000010"
    con = banco.con_db()
    for ordine, metodi in ((BZ, ["Contanti al tabacchino 23.47"]), (N1, ["SEPA"]), (N2, ["SEPA"])):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                    "sats,euro,metodi) VALUES(?,?,?,'pending','sell',1,15000,'10,00 €',?)",
                    (ordine, PUBBLICA, int(time.time()), json.dumps(metodi)))
    con.commit()
    con.close()
    SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True
    await scrivi_pausa(PUBBLICA, {"una_fino": int(time.time()) + 3600})
    f = await facce(PRENDE, [BZ, N1])
    prova("in pausa la vendita SEPA esce fra le pause del libro, la Barattozon NO",
          ([N1], False), (sorted(f["pause"]), BZ in f["pause"]))
    p = (await posso(PRENDE, [BZ, N1]))["ordini"]
    prova("...e «posso prendere?» ferma la prima e lascia prendere la Barattozon",
          ("pausa", True, ""), (p[N1]["motivo"], p[BZ]["ok"], p[BZ]["motivo"]))
    await scrivi_pausa(PUBBLICA, {})
    # il bottone che `notifica()` riceve davvero, destinatario per destinatario
    BOTTONI, vera = [], SRV.notifica

    async def spia(chi, testo, *a, **k):
        BOTTONI.append((chi, a[0] if a else k.get("bottone")))
        return await vera(chi, testo, *a, **k)
    SRV.notifica = spia
    try:
        atteso = ("⏸ Imposta la pausa", SRV.URL_PUBBLICO + "/p2p?pausa=1")

        # (13 ott 2026, notifica-porta-allo-scambio) sotto ogni avviso alle
        # parti c'e' anche «⚡ Apri lo scambio»: alla presa, a chi ha
        # pubblicato, sopra la pausa. Qui si guarda la PAUSA, dovunque stia
        def scambio(o):
            return ("⚡ Apri lo scambio", f"{SRV.LINK_LIBRO_P2P}?scambio={o}")

        def pause():
            return [b for _, bb in BOTTONI
                    for b in (bb if isinstance(bb, list) else [bb] if bb else [])
                    if b == atteso]
        t = int(time.time())
        await posta(busta(N1, "taken", t, "buyer", "invoice-next"))
        prova("l'avviso «Il tuo ordine è stato preso» porta a chi ha PUBBLICATO il "
              "bottone che apre il foglio della pausa — e a nessun altro (sopra, lo scambio)",
              ([(PUBBLICA, [scambio(N1), atteso])], True),
              (BOTTONI, bool(detto(PUBBLICA, "Il tuo ordine è stato preso"))))
        del BOTTONI[:]
        await posta(busta(N1, "buyer-invoice-added", t + 1, "buyer", "hold-next"))
        await posta(busta(N1, "hold-invoice-requested", t + 1, "mostro", "invoice"))
        prova("...gli avvisi DOPO la presa non lo portano (portano solo lo scambio)",
              ([], True), (pause(), all(b == scambio(N1) for _, b in BOTTONI if b)))
        del BOTTONI[:]
        await posta(busta(BZ, "taken", t + 2, "buyer", "invoice-next"))
        prova("...e sotto la presa di un ordine BARATTOZON non c'e': li' la pausa non "
              "si applica", ([PUBBLICA], [], [scambio(BZ)]),
              ([chi for chi, _ in BOTTONI], pause(), [b for _, b in BOTTONI if b]))
        del BOTTONI[:]
        SRV.P2P_TEMPO_DI_CHI_PUBBLICA = False
        await posta(busta(N2, "taken", t + 3, "buyer", "invoice-next"))
        prova("...e a leva spenta l'avviso della presa porta il solo scambio",
              ([PUBBLICA], [], [scambio(N2)]),
              ([chi for chi, _ in BOTTONI], pause(), [b for _, b in BOTTONI if b]))
    finally:
        SRV.notifica = vera
        SRV.P2P_TEMPO_DI_CHI_PUBBLICA = True
    prova("il link del bottone e' uno di quelli che dentro Telegram aprono la Mini App",
          "pausa", SRV._startapp_da_link(SRV.URL_PUBBLICO + "/p2p?pausa=1"))

    print("\n8-ter) un nativo Nostr in pausa: l'id negativo e' dei nostri come gli altri")
    # (13 ott 2026, cantiere pausa-nativi, il notato verificato su
    # richiesta di Andrea) chi e' NATO SU NOSTR ha un id negativo: la
    # pausa la scriveva e il foglio gliela diceva, ma il giudice del libro
    # chiedeva `tg_id > 0` e i suoi ordini restavano in vetrina
    NATIVO = -7301234567890123
    NA1 = "7e3a0000-1111-4a2b-9c3d-000000000021"
    NA2 = "7e3a0000-1212-4a2b-9c3d-000000000022"
    FUORI = "7e3a0000-1313-4a2b-9c3d-000000000023"
    con = banco.con_db()
    # CHI CHIEDE E' UNA PERSONA NUOVA: PRENDE a questo punto ha tre prese
    # aperte, e il suo «no» sarebbe `prese` qualunque cosa dica la pausa
    PASSA = 777
    for tg, nome, negozio in ((NATIVO, "Nata su Nostr", "nostrina"), (PASSA, "Passante", "neg777")):
        con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,negozio,registrato,ln_address) "
                    "VALUES(?,?,?,1,'')", (tg, nome, negozio))
    for ordine, chi in ((NA1, NATIVO), (NA2, NATIVO), (FUORI, 0)):
        con.execute("INSERT OR REPLACE INTO p2p_ordini(ordine,tg_id,creato,stato,lato,maker,"
                    "sats,euro,metodi) VALUES(?,?,?,'pending','sell',?,15000,'10,00 €',?)",
                    (ordine, chi, int(time.time()), 1 if chi else 0, json.dumps(["SEPA"])))
    con.commit()
    con.close()
    f = await facce(PASSA, [NA1, NA2, FUORI])
    p = (await posso(PASSA, [NA1, NA2, FUORI]))["ordini"]
    prova("senza pausa i suoi ordini stanno nel libro e si prendono",
          ([], [True, True, True]), (sorted(f["pause"]), [p[o]["ok"] for o in (NA1, NA2, FUORI)]))
    r = await scrivi_pausa(NATIVO, {"una_fino": int(time.time()) + 3600})
    prova("la sua pausa si scrive dalla rotta vera, e il suo foglio dice fino a quando",
          (True, True), (r["attiva"], r["fino"] > time.time()))
    f = await facce(PASSA, [NA1, NA2, FUORI])
    prova("IN PAUSA i suoi due ordini escono fra le pause del libro, con la stessa fine "
          "del suo foglio; quello di chi non e' dei nostri no",
          ([NA1, NA2], r["fino"], r["fino"]),
          (sorted(f["pause"]), f["pause"].get(NA1), f["pause"].get(NA2)))
    p = (await posso(PASSA, [NA1, NA2, FUORI]))["ordini"]
    prova("...«posso prendere?» li ferma col motivo `pausa`, e l'altro si prende",
          ("pausa", "pausa", r["fino"], True),
          (p[NA1]["motivo"], p[NA2]["motivo"], p[NA1].get("fino"), p[FUORI]["ok"]))
    prova("...a LEI il suo ordine non dice «pausa»", True,
          (await posso(NATIVO, [NA1]))["ordini"][NA1]["motivo"] != "pausa")
    await scrivi_pausa(NATIVO, {})
    f = await facce(PASSA, [NA1, NA2])
    p = (await posso(PASSA, [NA1, NA2]))["ordini"]
    prova("tolta la pausa tornano da soli: fuori dalle pause, e si prendono",
          ([], True, True), (sorted(f["pause"]), p[NA1]["ok"], p[NA2]["ok"]))

    print("\n9) dimentica il profilo")
    await scrivi_pausa(PUBBLICA, {"una_fino": int(time.time()) + 3600})
    prova("la pausa una volta sola c'e'", True, leggi_pausa(PUBBLICA)["fino"] > 0)
    banco.come(PUBBLICA)
    SRV.dimentica_chiavi_p2p()
    prova("...e «dimentica il profilo» la porta via; gli esiti restano", (0, 0, True),
          (leggi_pausa(PUBBLICA)["fino"], leggi_pausa(PUBBLICA)["una_fino"],
           len(esiti(PUBBLICA)) > 0))
    if SRV._TASK_EVENTI_P2P:
        await asyncio.gather(*list(SRV._TASK_EVENTI_P2P), return_exceptions=True)


def main():
    banco.avvio()
    banco.semina()
    semina_ordini()
    banco.SRV.P2P_EVENTI_SEGRETO = SEGRETO
    banco.SRV.P2P_RESPIRO_S = 0.2
    banco.SRV.P2P_RESPIRO_NOME_S = 0.1
    asyncio.run(giro())
    print(f"\n{banco.PASSATE} passate, {banco.FALLITE} fallite")
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
