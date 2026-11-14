# -*- coding: utf-8 -*-
"""
₿ LO SWAP AUTOMATICO, TAPPA 3: CHI VENDE SCEGLIE, CONFERMA, E I BITCOIN
ARRIVANO (2 nov 2026, cantiere swap-auto) — il giro col SERVER VERO.

`prove.py` gira i pezzi uno per uno (la curva, l'albero, la verifica, il
ritiro). Qui gira la STORIA, coi pezzi veri: le rotte, `_sblocca_sats`, la
porta dei pagamenti di sempre (`swap_registra_pagamento`), il battito che
ritira. Di cartone ci sono i due estremi: il SATS Routing (col suo finto
mempool, quello di `cartone_satsrouting`, che accetta un ritiro solo se il
bundle del telefono lo legge come spesa del lockup e la firma regge) e
LNbits (quello di `collaudo_swap_pagamento`: la fattura di uno swap resta
in volo finche' il fornitore non la chiude).

LE SCENE:
  1. la leva spenta: niente scelta, niente moneta sulle card, niente rotte;
  2. accesa e solo-admin: sceglie solo chi passa il cancello, e la busta
     di `/api/me` lo dice;
  3. LA MONETA SULLA CARD (Andrea, 14:43): «onchain» sull'annuncio di chi
     ha scelto on-chain, «ln» sotto il minimo del cambio o a scelta
     tolta, niente per chi non passa il cancello; anche nella vetrina
     anonima, che non riceve nessun id;
  4. alla conferma, chi ha scelto on-chain NON riceve sul Lightning
     address: gli si dice di aprire l'ordine e premere «Conferma». Chi non
     l'ha scelto, o vende sotto il minimo, riceve in Lightning come
     sempre;
  5. la carta dell'ordine: il preventivo di adesso, solo a chi vende;
  6. «Conferma»: senza parole non parte niente; un indirizzo storto o di
     un'altra rete, no; quello giusto fa nascere lo swap, lo paga la porta
     di sempre, e un secondo tocco non ne fa un altro;
  7. il battito: prima del lockup non fa niente; col lockup ritira, il
     cartone prende il ritiro, chi vende riceve l'id della transazione; il
     giro dopo non ritira due volte; la fattura chiusa chiude l'ordine;
  8. la fee della comodita' sopra 0: nessuno swap, nessun sats.

NON TOCCA NIENTE DI VERO: config di cartone e database usa-e-getta dal
banco dei pagamenti PRIMA dell'import del server; nessuna rete fuori da
127.0.0.1 (in CI la gabbia di `collaudi_ci.py`); le parole dello swap
nascono nella cartella usa-e-getta del database.

USO:  python collaudo_swap_auto.py
"""
import asyncio
import os
import time

import collaudo_lnbits_muto as banco
import collaudo_swap_pagamento as sp
import cartone_satsrouting as cart

prova = banco.prova
TESTE = {999: {"X-Tg-Init-Data": "collaudo:999:Admin"},
         222: {"X-Tg-Init-Data": "collaudo:222:Venditore"},
         111: {"X-Tg-Init-Data": "collaudo:111:Compratore"}}
INDIRIZZO = sp.INDIRIZZO                      # un bc1q di questa rete
REGTEST = "bcrt1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
SRV = None
CARTONE = None
LN_ADDRESS = []         # ogni volta che `_sblocca_sats` bussa a un address
VERIFICA_VERA = LEGGI_VERA = None


def semina():
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    for tg, nome in ((999, "Admin"), (222, "Vende"), (111, "Compra")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,?)",
                    (tg, nome, f"neg{tg}0000",
                     "vende@wallet.tld" if tg != 111 else ""))
    ids = {}
    for chi, nome, prezzo in ((999, "grande", 50_000), (999, "piccolo", 10_000),
                              (222, "altrui", 50_000), (999, "ln", 50_000),
                              (999, "conferma", 50_000), (999, "fee", 50_000)):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(?,?,'una cosa',?,'Altro','Pavia (PV)','attivo',1,"
            "'ritiro',5,'sats','nuovo')", (chi, f"Cosa {nome}", prezzo))
        ids[nome] = cur.lastrowid
    con.commit()
    con.close()
    return ids


def preferisce(c, tg, onchain):
    return c.post("/api/swap/auto/preferenza", json={"onchain": onchain},
                  headers=TESTE[tg])


def incasso_in_vetrina(c, testa=None):
    r = c.get("/api/listings", headers=testa or {})
    return {x["titolo"]: x.get("venditore_incasso") for x in r.json()}, r.json()


def confermato(aid):
    """Un ordine pagato e confermato da chi compra, coi percorsi veri."""
    oid = banco.ordine_pagato(aid)
    banco.DETTO.clear()
    banco.come(111)
    banco.chiama(SRV.conferma_ricezione, oid, None)
    # `banco.come` fissa chi chiama e `banco.chiama` il corpo: le rotte
    # per HTTP tornano a leggere la testa e il corpo della richiesta
    SRV.verifica_utente, SRV.leggi_json = VERIFICA_VERA, LEGGI_VERA
    return oid


def giro(c, ids):
    print("\n[1. la leva spenta]")
    SRV.SWAP_AUTO_ATTIVO = False
    me = c.get("/api/me", headers=TESTE[999]).json()
    prova("la busta di /api/me dice spento", False,
          ((me.get("swap_leve") or {}).get("auto") or {}).get("attivo"))
    prova("la scelta nel Profilo non esiste", 404, preferisce(c, 999, True).status_code)
    v, _ = incasso_in_vetrina(c)
    prova("nessuna card dice come preferisce ricevere", {""}, set(v.values()))

    print("\n[2. accesa, solo per gli admin]")
    SRV.SWAP_AUTO_ATTIVO = True
    SRV.SWAP_AUTO_SOLO_ADMIN = True
    prova("chi non e' admin non sceglie", 404, preferisce(c, 222, True).status_code)
    r = preferisce(c, 999, True)
    prova("l'admin sceglie on-chain", (200, True, True),
          (r.status_code, r.json().get("attivo"), r.json().get("onchain")))
    me = c.get("/api/me", headers=TESTE[999]).json()["swap_leve"]["auto"]
    prova("...e /api/me lo dice, coi tetti e il fornitore",
          (True, True, 25_000, 50_000, "SATS Routing"),
          (me["attivo"], me["onchain"], me["minimo"], me["massimo"], me["fornitore"]))
    me = c.get("/api/me", headers=TESTE[111]).json()["swap_leve"]["auto"]
    prova("chi compra non lo vede", False, me["attivo"])

    print("\n[3. la moneta sulla card]")
    for nome, testa in (("anonima", None), ("con sessione", TESTE[111])):
        v, righe = incasso_in_vetrina(c, testa)
        prova(f"vetrina {nome}: on-chain sull'annuncio di chi l'ha scelto",
              "onchain", v["Cosa grande"])
        prova(f"vetrina {nome}: Lightning sotto il minimo del cambio",
              "ln", v["Cosa piccolo"])
        prova(f"vetrina {nome}: niente per chi non passa il cancello",
              "", v["Cosa altrui"])
    _, righe = incasso_in_vetrina(c)
    prova("la vetrina anonima non riceve nessun id di chi vende", True,
          all("venditore_id" not in x for x in righe))
    preferisce(c, 999, False)
    v, _ = incasso_in_vetrina(c)
    prova("scelta tolta: Lightning", "ln", v["Cosa grande"])
    preferisce(c, 999, True)

    print("\n[4. alla conferma: il Lightning address si salta solo per chi ha scelto]")
    # (6 nov 2026, swap-auto-tasto) il TASTO sotto l'avviso: chi notifica
    # col bottone si annota qui, poi passa alla finta del banco
    TASTI = []
    finta = SRV.notifica

    async def col_tasto(chi, testo, *a, **k):
        TASTI.append((chi, a[0] if a else k.get("bottone")))
        return await finta(chi, testo)
    SRV.notifica = col_tasto
    LN_ADDRESS.clear()
    oid = confermato(ids["grande"])
    o = banco.riga(oid)
    prova("on-chain: il Lightning address non si tocca", 0, len(LN_ADDRESS))
    prova("...l'ordine resta confermato, nessuna uscita", ("confirmed", ""),
          (o["stato"], o["payout_stato"] or ""))
    detto = " ".join(t for chi, t in banco.DETTO if chi == 999)
    prova("...e chi vende sa che tocca a lui: «Conferma», non una fattura",
          (True, True, False), ("«Conferma»" in detto, "bitcoin on-chain" in detto,
                                "invoice" in detto))
    prova("...col tasto che apre l'ordine dritto all'incasso (Andrea, 6 nov)",
          [("₿ Controlla e conferma", f"{SRV.URL_PUBBLICO}/?ordine={oid}&incasso=1")],
          [b for chi, b in TASTI if chi == 999 and b])
    TASTI.clear()
    LN_ADDRESS.clear()
    confermato(ids["piccolo"])
    prova("sotto il minimo del cambio: il Lightning address come sempre",
          1, len(LN_ADDRESS))
    preferisce(c, 999, False)
    LN_ADDRESS.clear()
    confermato(ids["ln"])
    prova("chi non l'ha scelto: il Lightning address come sempre", 1, len(LN_ADDRESS))
    prova("...e sotto il minimo o senza la scelta, nessun tasto dell'incasso", [],
          [b for chi, b in TASTI if chi == 999 and b])
    SRV.notifica = finta
    preferisce(c, 999, True)

    print("\n[5. la carta dell'ordine]")
    d = c.get(f"/api/swap/auto/ordine/{oid}", headers=TESTE[999])
    p = d.json().get("preventivo") or {}
    prova("il preventivo di adesso, a chi vende", (200, True, 50_000, "bitcoin"),
          (d.status_code, p.get("ok"), p.get("dovuto"), d.json().get("rete")))
    prova("...ricevi meno del dovuto, piu' di zero", True, 0 < p["ricevi"] < 50_000)
    prova("chi compra non la vede", 404,
          c.get(f"/api/swap/auto/ordine/{oid}", headers=TESTE[111]).status_code)

    print("\n[6. «Conferma»]")
    sp.USCITE.clear()

    def conferma(indirizzo):
        return c.post(f"/api/swap/auto/ordine/{oid}", json={"indirizzo": indirizzo},
                      headers=TESTE[999]).json()

    prova("senza le parole dello swap non parte niente", (False, "parole", 0),
          (conferma(INDIRIZZO).get("ok"), conferma(INDIRIZZO).get("motivo"),
           len(sp.USCITE)))
    r = c.post("/api/admin/swap/parole", headers=TESTE[999])
    prova("l'admin crea le parole (una volta sola)", (200, 409),
          (r.status_code, c.post("/api/admin/swap/parole", headers=TESTE[999]).status_code))
    prova("...nella cartella del database, non in quella del codice", True,
          os.path.dirname(SRV._swap_auto_file()).startswith(
              os.path.dirname(os.path.abspath(SRV.DB))))
    prova("un indirizzo storto: no", "indirizzo", conferma("bc1qnonvalido").get("motivo"))
    prova("un indirizzo di un'altra rete: no", "indirizzo", conferma(REGTEST).get("motivo"))
    prova("...e nessun sats e' uscito", 0, len(sp.USCITE))
    r = conferma(INDIRIZZO)
    prova("l'indirizzo giusto: lo swap nasce e la porta lo paga",
          (True, "in_volo", INDIRIZZO, p["ricevi"], 1),
          (r.get("ok"), r.get("stato"), r.get("indirizzo"), r.get("ricevi"),
           len(sp.USCITE)))
    con = SRV.db()
    righe = [dict(x) for x in con.execute(
        "SELECT * FROM swap_auto WHERE ordine_id=?", (oid,))]
    con.close()
    prova("...una riga sola, con dove e quanto", [("nato", INDIRIZZO, p["ricevi"])],
          [(x["stato"], x["destinazione"], x["ricevi"]) for x in righe])
    r2 = conferma(INDIRIZZO)
    con = SRV.db()
    n = con.execute("SELECT COUNT(*) FROM swap_auto WHERE ordine_id=?",
                    (oid,)).fetchone()[0]
    con.close()
    prova("il secondo tocco non fa un altro swap ne' un altro pagamento",
          (True, 1, 1), (r2.get("ok"), n, len(sp.USCITE)))
    d = c.get(f"/api/swap/auto/ordine/{oid}", headers=TESTE[999]).json()
    prova("la carta dice «in corso», senza un preventivo nuovo",
          ("in_volo", INDIRIZZO, False),
          ((d.get("corso") or {}).get("pagamento"), (d.get("corso") or {}).get("indirizzo"),
           "preventivo" in d))

    print("\n[7. il battito ritira]")
    banco.DETTO.clear()
    prova("prima del lockup il giro non fa niente", 0, asyncio.run(SRV.swap_auto_giro()))
    prova("...e il battito si sveglia per lui", True, SRV._swap_auto_da_guardare())
    sid = righe[0]["swap_id"]
    cart.sposta(CARTONE.cartone, sid, "transaction.mempool")
    # (14 nov 2026, audit-swap-conferma; Andrea: «Aspetta una conferma»)
    # il lockup IN CODA si puo' ancora sostituire: il giro aspetta, il
    # segreto non esce, nessuno viene avvisato e il battito resta sveglio
    prova("col lockup solo in coda il giro NON ritira: niente al fornitore, niente "
          "a chi vende, e il battito resta sveglio",
          (0, 0, [], True),
          (asyncio.run(SRV.swap_auto_giro()), len(CARTONE.cartone["stato"]["trasmesse"]),
           list(banco.DETTO), SRV._swap_auto_da_guardare()))
    d = c.get(f"/api/swap/auto/ordine/{oid}", headers=TESTE[999]).json()
    prova("...e la carta resta «in corso»", ("in_volo", False),
          ((d.get("corso") or {}).get("pagamento"), bool((d.get("corso") or {}).get("ritirato"))))
    # a ridosso della scadenza, anche confermato, il segreto resta a casa
    # e gli admin lo sanno UNA volta
    cart.sposta(CARTONE.cartone, sid, "transaction.confirmed")
    cima_vera = CARTONE.cartone["stato"]["cima"]
    CARTONE.cartone["stato"]["cima"] = (CARTONE.cartone["swap"][sid]["timeoutBlockHeight"]
                                        - SRV.SWAP_AUTO_MARGINE_RITIRO + 1)
    SRV._SWAP_AUTO_DETTO_TARDI.clear()
    banco.AVVISI.clear()
    giri = (asyncio.run(SRV.swap_auto_giro()), asyncio.run(SRV.swap_auto_giro()))
    tardi = [t for t in banco.AVVISI if "non ritiro i bitcoin" in t]
    prova("confermato ma a 11 blocchi dalla scadenza: niente ritiro, niente al "
          "fornitore, niente a chi vende, e gli admin lo sanno una volta sola (due "
          "giri, un avviso)",
          ((0, 0), 0, [], 1, True),
          (giri, len(CARTONE.cartone["stato"]["trasmesse"]), list(banco.DETTO),
           len(tardi), bool(tardi) and f"#{oid}" in tardi[0]))
    CARTONE.cartone["stato"]["cima"] = cima_vera
    banco.DETTO.clear()
    prova("col lockup confermato, e la scadenza lontana, il giro ritira", 1,
          asyncio.run(SRV.swap_auto_giro()))
    swap = CARTONE.cartone["swap"][sid]
    prova("...il cartone l'ha preso e chiude la fattura", "invoice.settled",
          swap.get("stato"))
    con = SRV.db()
    rr = dict(con.execute("SELECT * FROM swap_auto WHERE ordine_id=?", (oid,)).fetchone())
    con.close()
    detto = " ".join(t for chi, t in banco.DETTO if chi == 999)
    prova("...chi vende riceve l'id della transazione",
          ("ritirato", True, True),
          (rr["stato"], bool(rr["ritiro_txid"]), rr["ritiro_txid"] in detto))
    prova("il giro dopo non ritira due volte", 0, asyncio.run(SRV.swap_auto_giro()))
    prova("...e il battito torna a dormire", False, SRV._swap_auto_da_guardare())

    print("\n[7b. il ritiro fermo si rilancia (6 nov 2026, ritiro a scalini)]")
    ctx = CARTONE.cartone
    lk = swap["lockup"]["id"]
    ctx["stato"]["tariffe"].update(halfHourFee=20)
    con = SRV.db()
    con.execute("UPDATE swap_auto SET aggiornato=? WHERE ordine_id=?",
                (int(time.time()) - 3 * 3600, oid))
    con.commit()
    con.close()
    SRV._SWAP_AUTO_GUARDATO.clear()
    banco.DETTO.clear()
    prova("fermo da tre ore con la coda piena: il battito si sveglia per lui", True,
          SRV._swap_auto_da_guardare())
    prova("...il giro non ritira niente di nuovo", 0, asyncio.run(SRV.swap_auto_giro()))
    con = SRV.db()
    r3 = dict(con.execute("SELECT * FROM swap_auto WHERE ordine_id=?", (oid,)).fetchone())
    con.close()
    detto = " ".join(t for chi, t in banco.DETTO if chi == 999)
    prova("...ma lo rilancia: la rete ha la nuova (RBF), la riga la segue con meno "
          "sats, chi vende lo sa con l'id nuovo",
          (True, r3["ritiro_txid"], True, True, True, [rr["ritiro_txid"]]),
          (r3["ritiro_txid"] != rr["ritiro_txid"], ctx["spese"][lk]["txid"],
           r3["ricevi"] < rr["ricevi"], r3["ritiro_txid"] in detto, "rilanciato" in detto,
           ctx["stato"]["sostituite"]))
    n_tr = len(ctx["stato"]["trasmesse"])
    prova("...e per dieci minuti il battito non lo riguarda", (False, n_tr),
          (SRV._swap_auto_da_guardare(), len(ctx["stato"]["trasmesse"])))
    ctx["spese"][lk]["confermata"] = True
    SRV._SWAP_AUTO_GUARDATO.clear()
    asyncio.run(SRV.swap_auto_giro())
    con = SRV.db()
    conf = con.execute("SELECT confermato FROM swap_auto WHERE ordine_id=?",
                       (oid,)).fetchone()[0]
    con.close()
    SRV._SWAP_AUTO_GUARDATO.clear()
    prova("confermato: la riga lo ricorda e il battito torna a dormire", (1, False),
          (conf, SRV._swap_auto_da_guardare()))
    # (14 nov 2026, audit-swap-conferma) «CONFERMATO» E' IL NOSTRO RITIRO.
    # La stessa riga, rimessa «da guardare», col lockup speso e confermato
    # da UN'ALTRA transazione (il rimborso del fornitore, per dire): non e'
    # «fatto», prende il 2, e gli admin lo sanno una volta. Poi tutto torna
    # com'era, per le scene dopo.
    nostra_spesa = dict(ctx["spese"][lk])
    cart.spendi(ctx, swap, "cd" * 32, [{"sats": swap["onchainAmount"] - 300,
                                        "script": "0014" + "22" * 20}])
    ctx["spese"][lk]["confermata"] = True
    con = SRV.db()
    con.execute("UPDATE swap_auto SET confermato=0 WHERE ordine_id=?", (oid,))
    con.commit()
    con.close()
    banco.AVVISI.clear()
    banco.DETTO.clear()
    for _ in range(2):
        SRV._SWAP_AUTO_GUARDATO.clear()
        asyncio.run(SRV.swap_auto_giro())
    con = SRV.db()
    conf = con.execute("SELECT confermato FROM swap_auto WHERE ordine_id=?",
                       (oid,)).fetchone()[0]
    con.close()
    SRV._SWAP_AUTO_GUARDATO.clear()
    altro = [t for t in banco.AVVISI if "NON è il nostro ritiro" in t]
    prova("il lockup speso e confermato da un altro: la riga prende il 2, gli admin lo "
          "sanno UNA volta (con l'ordine e l'id di chi ha speso), a chi vende non si "
          "scrive niente di falso, e il battito non la riguarda",
          (2, 1, True, [], False),
          (conf, len(altro), bool(altro) and f"#{oid}" in altro[0] and "cd" * 32 in altro[0],
           list(banco.DETTO), SRV._swap_auto_da_guardare()))
    ctx["spese"][lk] = nostra_spesa
    con = SRV.db()
    con.execute("UPDATE swap_auto SET confermato=1 WHERE ordine_id=?", (oid,))
    con.commit()
    con.close()
    ctx["stato"]["tariffe"].update(halfHourFee=2)
    con = SRV._swap_pag_db()
    h = con.execute("SELECT hash FROM swap_pagamenti WHERE ordine_id=?",
                    (oid,)).fetchone()[0]
    con.close()
    sp.PAGAMENTI[h] = "success"         # il fornitore ha chiuso la fattura
    asyncio.run(SRV.risolvi_pagamenti_in_volo(solo_in_volo=True))
    SRV.swap_pagamenti_ripassa()
    o = banco.riga(oid)
    prova("la fattura chiusa chiude l'ordine", ("released", "uscito"),
          (o["stato"], o["payout_stato"]))

    print("\n[8. la fee della comodita' sopra 0]")
    oid_fee = confermato(ids["fee"])
    SRV.SWAP_AUTO_FEE_PERCENTO = 1
    sp.USCITE.clear()
    r = c.post(f"/api/swap/auto/ordine/{oid_fee}", json={"indirizzo": INDIRIZZO},
               headers=TESTE[999]).json()
    prova("nessuno swap, nessun sats", (False, "fee", 0),
          (r.get("ok"), r.get("motivo"), len(sp.USCITE)))
    SRV.SWAP_AUTO_FEE_PERCENTO = 0


def main():
    global SRV, CARTONE, VERIFICA_VERA, LEGGI_VERA
    print("=" * 58)
    print("  ₿ LO SWAP AUTOMATICO, TAPPA 3 — il giro vero")
    print("=" * 58)
    banco.avvio()
    SRV = banco.SRV
    sp.SRV = SRV
    VERIFICA_VERA, LEGGI_VERA = SRV.verifica_utente, SRV.leggi_json
    CARTONE, porta = cart.avvia(0)
    sp.CARTONE = f"http://127.0.0.1:{porta}"
    SRV.httpx = sp._Misto
    SRV.SECONDI_FRA_ATTESE = 0
    SRV.SWAP_ATTIVO = False          # lo swap del TELEFONO: un altro cancello
    SRV.SWAP_MIN_SATS = 25_000
    SRV.SWAP_MAX_SATS = 50_000
    SRV.SWAP_FEE_PERCENTO = 0
    SRV.SWAP_AUTO_FEE_PERCENTO = 0
    SRV.SWAP_MAX_SATS_UTENTE_GIORNO = 200_000
    SRV.SWAP_MAX_SATS_GIORNO = 400_000
    SRV.SWAP_API_BASE = sp.CARTONE
    SRV.SWAP_REFERRAL_ID = "barattolo"
    SRV.SWAP_RETE = "bitcoin"
    SRV.SWAP_MEMPOOL_API = sp.CARTONE + "/esplora"

    async def address_contato(*a, **k):
        LN_ADDRESS.append(a)
        return None
    SRV.invoice_da_ln_address = address_contato
    from fastapi.testclient import TestClient

    c = TestClient(SRV.app)
    for t in TESTE.values():
        c.get("/api/me", headers=t)
    giro(c, semina())

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    raise SystemExit(main())
