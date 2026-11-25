# -*- coding: utf-8 -*-
"""
«CERCO», LE RICHIESTE DI CHI CERCA (25 nov 2026, cantiere richieste).

Andrea: chi non trova una cosa la scrive, e la richiesta va dai venditori
adatti invece di restare in bacheca; poi «Accendila già dappertutto, a
tutti». `prove.py` fa girare i giudici puri (le parole, la porta, il
prefiltro su un database gemello, la scelta AI fail-open); qui rispondono
le ROTTE VERE su un database usa-e-getta:
  1) la porta: aperta a tutti di serie, a solo-moderatori 404 agli altri;
  2) la nascita: testo corto, categoria inventata, parola vietata (col
     messaggio che dice la categoria), il budget; l'avviso di ricerca
     gemello coi soli termini veri;
  3) l'avviso ai venditori: i 5 piu' adatti (senza chiave AI, i primi del
     prefiltro), il testo col deposito di garanzia e la cifra coi puntini,
     il tasto «Offri» che apre la richiesta; nessuno due volte;
  4) il tetto: al piu' 3 avvisi al giorno per venditore, 3 richieste
     aperte a testa;
  5) la bacheca: le mie in testa, le offerte solo a chi cerca;
  6) l'offerta: si lega, chi cerca e' avvisato col titolo scappato; mai
     a se stessi, mai su una richiesta chiusa;
  7) chiudere: solo chi l'ha scritta, e il gemello se ne va; la scaduta
     si chiude da sola alla lettura;
  8) «🔕»: chi ha spento non e' piu' fra i candidati;
  9) la moderazione AI degli annunci, spenta di serie, non chiama niente.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete: le notifiche finiscono
in una lista.

USO:  python collaudo_richieste.py
"""

import asyncio
import sys
import time

import collaudo_lnbits_muto as banco

prova = banco.prova
CAT = "Buoni ed esperienze"
CERCA, ADMIN = 111, 999
VENDITORI = list(range(201, 208))    # sette che vendono buoni
ALTRO = 301                          # vende sedie: mai fra i candidati
DETTO = []                           # (chi, testo, bottone)


def _errore(fn):
    try:
        fn()
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", "")))
    return (200, "")


def main():
    print("=" * 58)
    print("  «CERCO»: LE RICHIESTE DI CHI CERCA")
    print("=" * 58)
    banco.avvio()
    S = banco.SRV

    async def notifica(chi, testo, bottone=None):
        DETTO.append((chi, testo, bottone))
    S.notifica = notifica

    ora = int(time.time())
    con = S.db()
    for tg in [CERCA, ADMIN, ALTRO, 112, 113, 114] + VENDITORI:
        con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, negozio, registrato) "
                    "VALUES(?,?,?,?)", (tg, f"U{tg}", f"neg{tg}", ora))
    for n, v in enumerate(VENDITORI):
        # i primi tre hanno «amazon» nel titolo: salgono in testa
        tit = f"Buono Amazon {10 * (n + 1)} euro" if n < 3 else f"Gift card {n}"
        con.execute(
            "INSERT INTO annunci(venditore_id, titolo, descrizione, prezzo_sats, "
            "categoria, zona, stato, creato, consegna, quantita, valuta, condizione) "
            "VALUES(?,?,'',10000,?,'Pavia (PV)','attivo',?,'digitale',1,'sats','nuovo')",
            (v, tit, CAT, ora))
    con.execute(
        "INSERT INTO annunci(venditore_id, titolo, descrizione, prezzo_sats, "
        "categoria, zona, stato, creato, consegna, quantita, valuta, condizione) "
        "VALUES(?,'Sedia di legno','',10000,'Casa e giardino','Pavia (PV)','attivo',?,"
        "'ritiro',1,'sats','usato')", (ALTRO, ora))
    con.commit()
    con.close()

    def lista(chi):
        banco.come(chi)
        return banco.chiama(S.lista_richieste, "", "")

    def crea(chi, corpo):
        """La rotta vera, e l'avviso che lancia in sottofondo lo si lascia
        finire come farebbe il server vivo (un asyncio.run che chiude
        subito lo cancellerebbe a meta')."""
        banco.come(chi)

        async def leggi(_req):
            return corpo
        S.leggi_json = leggi

        async def giro():
            r = await S.crea_richiesta(None, "", "")
            altri = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            await asyncio.gather(*altri)
            return r
        return asyncio.run(giro())

    def righe(sql, *a):
        con = S.db()
        try:
            return [tuple(r) for r in con.execute(sql, a).fetchall()]
        finally:
            con.close()

    print("\n[1) la porta]")
    prova("di serie aperta a tutti: chi non e' moderatore vede la bacheca", 200,
          _errore(lambda: lista(CERCA))[0])
    S.RICHIESTE_SOLO_MODERATORI = True
    prova("a solo-moderatori: 404 agli altri...", 404, _errore(lambda: lista(CERCA))[0])
    prova("...e il moderatore entra", 200, _errore(lambda: lista(ADMIN))[0])
    prova("...anche per scrivere", 404,
          _errore(lambda: crea(CERCA, {"testo": "un buono", "categoria": CAT}))[0])
    S.RICHIESTE_SOLO_MODERATORI = False

    print("\n[2) la nascita]")
    prova("testo troppo corto", (400, "Scrivi cosa cerchi"),
          _errore(lambda: crea(CERCA, {"testo": " ab ", "categoria": CAT})))
    prova("categoria inventata", (400, "Scegli la categoria"),
          _errore(lambda: crea(CERCA, {"testo": "un buono", "categoria": "Pozioni"})))
    e = _errore(lambda: crea(CERCA, {"testo": "Cerco cocaina buona", "categoria": CAT}))
    prova("la parola vietata si ferma, e il messaggio dice la categoria",
          (400, True), (e[0], "drogh" in e[1].lower()))
    prova("...ed entra nel registro della moderazione", 1,
          len(righe("SELECT id FROM moderazione_log WHERE strato='parole'")))
    prova("budget storto", 400,
          _errore(lambda: crea(CERCA, {"testo": "un buono", "categoria": CAT,
                                       "budget_sats": "tanti"}))[0])
    DETTO.clear()
    r = crea(CERCA, {"testo": "Cerco un buono Amazon da 50 €", "categoria": CAT,
                     "budget_sats": 55000})
    rid = r.get("id")
    prova("la richiesta nasce", True, bool(r.get("ok")) and rid > 0)
    riga = righe("SELECT stato, budget_sats, scade - creato, avviso_id FROM richieste "
                 "WHERE id=?", rid)[0]
    prova("...aperta, col budget, per 14 giorni", ("aperta", 55000, 14 * 86400),
          riga[:3])
    prova("...e col suo avviso di ricerca gemello: le parole vere, la categoria, "
          "il budget", [("buono amazon", f"|{CAT}|", 55000)],
          righe("SELECT parole, categorie, prezzo_max_sats FROM avvisi_ricerca "
                "WHERE id=?", riga[3]))

    print("\n[3) l'avviso ai venditori, partito da solo con la nascita]")
    chi = [d[0] for d in DETTO]
    prova("cinque avvisi, prima i tre che vendono buoni Amazon", 5, len(chi))
    prova("...i tre col titolo che combacia sono tutti dentro", True,
          set(VENDITORI[:3]) <= set(chi))
    prova("...mai chi chiede, mai chi vende sedie", True,
          CERCA not in chi and ALTRO not in chi)
    t = DETTO[0][1] if DETTO else ""
    prova("il testo: chi cerca cosa, il budget coi puntini, il deposito di garanzia",
          [True, True, True],
          ["Qualcuno cerca: <b>Cerco un buono Amazon da 50 €</b>" in t,
           "fino a 55.000 sats" in t, "deposito di garanzia" in t])
    prova("il tasto «Offri» apre la richiesta", ("Offri", f"cerco_{rid}"),
          (DETTO[0][2][0], DETTO[0][2][1].rsplit("startapp=", 1)[-1])
          if DETTO and DETTO[0][2] else None)
    prova("...e li conta", ([(5,)], 5),
          (righe("SELECT avvisati FROM richieste WHERE id=?", rid),
           len(righe("SELECT tg_id FROM richieste_avvisati WHERE richiesta_id=?", rid))))
    DETTO.clear()
    banco.chiama(S._avvisa_venditori_richiesta, rid)
    prova("un secondo giro non riavvisa nessuno dei cinque", set(),
          set(chi) & {d[0] for d in DETTO})

    print("\n[4) i tetti]")
    for altro in (112, 113, 114):
        crea(altro, {"testo": f"buono Amazon numero {altro}", "categoria": CAT})
    conti = righe("SELECT tg_id, COUNT(*) FROM richieste_avvisati WHERE creato>? "
                  "GROUP BY tg_id", ora - 86400)
    prova("nessun venditore riceve piu' di 3 avvisi in 24 ore", True,
          all(n <= 3 for _, n in conti))
    crea(CERCA, {"testo": "un buono carburante", "categoria": CAT})
    crea(CERCA, {"testo": "un voucher Ryanair", "categoria": CAT})
    prova("la quarta richiesta aperta no", 400,
          _errore(lambda: crea(CERCA, {"testo": "un buono Zalando", "categoria": CAT}))[0])

    print("\n[5) la bacheca]")
    b = lista(CERCA)
    prova("le mie in testa, segnate come mie", [True, True, True],
          [v["mia"] for v in b["richieste"][:3]])
    prova("...e le altre dopo", True, all(not v["mia"] for v in b["richieste"][3:]))
    b2 = lista(VENDITORI[0])
    prova("chi vende vede la richiesta, senza la lista delle offerte", (False, False),
          next(((v["mia"], "annunci" in v) for v in b2["richieste"] if v["id"] == rid), None))

    print("\n[6) l'offerta]")
    aid = righe("SELECT id FROM annunci WHERE venditore_id=?", VENDITORI[0])[0][0]
    DETTO.clear()
    banco.chiama(S.collega_offerta_richiesta, rid, aid, VENDITORI[0], True)
    prova("si lega", [(rid, aid, VENDITORI[0])],
          righe("SELECT richiesta_id, annuncio_id, tg_id FROM richieste_offerte"))
    prova("chi cerca e' avvisato, col tasto che apre l'annuncio",
          (CERCA, True, "Apri l'annuncio"),
          (DETTO[0][0], "C'è un'offerta per la tua richiesta" in DETTO[0][1],
           DETTO[0][2][0]) if DETTO else None)
    mia = next(v for v in lista(CERCA)["richieste"] if v["id"] == rid)
    prova("nella sua bacheca: l'offerta e il conto", ([aid], 1),
          ([a["id"] for a in mia.get("annunci", [])], mia["offerte"]))
    DETTO.clear()
    banco.chiama(S.collega_offerta_richiesta, rid, aid, CERCA, True)
    prova("mai un'offerta a se stessi", (1, 0),
          (len(righe("SELECT 1 FROM richieste_offerte")), len(DETTO)))
    banco.chiama(S.collega_offerta_richiesta, "x", aid, VENDITORI[1], True)
    prova("un id storto non fa niente (e non alza)", 1,
          len(righe("SELECT 1 FROM richieste_offerte")))
    con = S.db()
    con.execute("UPDATE annunci SET titolo='<b>Buono</b>' WHERE id=?", (aid,))
    con.commit()
    con.close()
    DETTO.clear()
    aid2 = righe("SELECT id FROM annunci WHERE venditore_id=?", VENDITORI[1])[0][0]
    con = S.db()
    con.execute("UPDATE annunci SET titolo='<b>Buono</b>' WHERE id=?", (aid2,))
    con.commit()
    con.close()
    banco.chiama(S.collega_offerta_richiesta, rid, aid2, VENDITORI[1], True)
    prova("il titolo del venditore arriva scappato", True,
          bool(DETTO) and "&lt;b&gt;Buono&lt;/b&gt;" in DETTO[0][1])
    DETTO.clear()
    banco.chiama(S.collega_offerta_richiesta, rid, aid2, VENDITORI[1], False)
    prova("in revisione si lega senza avviso", 0, len(DETTO))

    print("\n[7) chiudere e scadere]")
    avviso = righe("SELECT avviso_id FROM richieste WHERE id=?", rid)[0][0]
    banco.come(VENDITORI[0])
    prova("chiude solo chi l'ha scritta", 404,
          _errore(lambda: banco.chiama(S.chiudi_richiesta, rid, "", ""))[0])
    banco.come(CERCA)
    banco.chiama(S.chiudi_richiesta, rid, "", "")
    prova("chiusa, e il suo avviso di ricerca se ne va", ([("chiusa",)], []),
          (righe("SELECT stato FROM richieste WHERE id=?", rid),
           righe("SELECT id FROM avvisi_ricerca WHERE id=?", avviso)))
    prova("...e sparisce dalla bacheca", False,
          any(v["id"] == rid for v in lista(CERCA)["richieste"]))
    DETTO.clear()
    banco.chiama(S.collega_offerta_richiesta, rid, aid, VENDITORI[2], True)
    prova("a richiesta chiusa niente offerte nuove", 0, len(DETTO))
    vecchia = righe("SELECT id, avviso_id FROM richieste WHERE tg_id=? AND "
                    "stato='aperta' ORDER BY id LIMIT 1", CERCA)[0]
    con = S.db()
    con.execute("UPDATE richieste SET scade=? WHERE id=?", (ora - 1, vecchia[0]))
    con.commit()
    con.close()
    lista(CERCA)
    prova("la scaduta si chiude da sola alla lettura, col suo gemello",
          ([("chiusa",)], []),
          (righe("SELECT stato FROM richieste WHERE id=?", vecchia[0]),
           righe("SELECT id FROM avvisi_ricerca WHERE id=?", vecchia[1] or -1)))

    print("\n[8) «🔕»]")
    banco.come(VENDITORI[0])
    banco.chiama(S.muto_richieste, None, "", "", corpo={"muto": True})
    prova("la bacheca lo ricorda", True, lista(VENDITORI[0])["muto"])
    con = S.db()
    cand = S._candidati_richiesta(con, {"id": 0, "tg_id": CERCA,
                                        "testo": "buono Amazon",
                                        "categoria": CAT})
    con.close()
    prova("...e non e' piu' fra i candidati", False,
          VENDITORI[0] in [c["tg_id"] for c in cand])
    banco.come(VENDITORI[0])
    banco.chiama(S.muto_richieste, None, "", "", corpo={"muto": False})
    prova("riacceso torna", False, lista(VENDITORI[0])["muto"])

    print("\n[9) la moderazione AI spenta]")
    chiamate = []

    class _Ai:
        class messages:
            @staticmethod
            def create(**kw):
                chiamate.append(kw)
                raise RuntimeError("non doveva chiamare")
    S.ai, S.ANTHROPIC_API_KEY = _Ai, "sk-finta"
    prova("di serie e' spenta", False, S.MODERAZIONE_AI)
    prova("...e moderazione_ai non chiama niente", (None, 0),
          (asyncio.run(S.moderazione_ai("un armadio", "")), len(chiamate)))
    prova("...ne' il lotto", ({}, 0),
          (asyncio.run(S.moderazione_ai_lotto([{"id": 1, "titolo": "x",
                                                "descrizione": ""}])), len(chiamate)))

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
