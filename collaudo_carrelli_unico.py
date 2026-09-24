# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL PAGAMENTO UNICO DI PIU' CARRELLI (24 set 2026): il giro
vero — due carrelli di due venditori, UNA fattura per la somma, il saldo
che fa nascere un ordine per venditore col suo deposito di garanzia — e
i quattro casi che il cantiere doveva chiudere:
  · l'articolo che si esaurisce fra la fattura e il saldo: quell'ordine
    non nasce e la sua parte torna al compratore, senza rimettere in
    vetrina merce mai uscita;
  · il rimborso di UN ordine dopo il saldo, senza toccare gli altri;
  · la fattura annullata, e quella scaduta (l'orologio), col saldo
    tardivo che riacciuffa la busta e ricontrolla la merce;
  · nessun doppio incasso: la busta e ogni ordine passano da un CAS, e
    il poll del singolo ordine chiede alla busta.
Piu' le guardie (un carrello solo, lo stesso venditore due volte, il
conto che cambia fra le due passate), «Paga ora» sull'ordine di busta,
la lista degli ordini con la cifra della fattura condivisa, e la ronda
del libro mastro che su tutto questo deve TACERE.

NON TOCCA NIENTE DI VERO: il config si sostituisce PRIMA dell'import di
server, LNbits e' finto (le fatture si contano e si pagano a comando),
le uscite si registrano, le notifiche si catturano in una lista.

USO:  python collaudo_carrelli_unico.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []       # (sats, memo, hash) delle fatture in ENTRATA coniate
PAGATE = {}         # hash -> True quando il compratore «ha pagato»
USCITE = []         # (bolt11, sats, taccuino) dei pagamenti in USCITA
NOTIFICHE = []      # (tg_id, testo)
ADMIN = []          # i messaggi ai moderatori

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE_A = {"id": 222, "nome": "Anna", "username": "anna", "admin": False}
VENDE_B = {"id": 333, "nome": "Bruno", "username": "bruno", "admin": False}
CHI = [COMPRA]


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-collaudo-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    cfg.PROTEZIONE_PERCENTO = 0
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        h = f"hash{len(INVOICES) + 1}"
        INVOICES.append((int(sats), memo, h))
        return {"payment_hash": h,
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def pagata_finta(payment_hash, _cassaforte=""):
        return bool(PAGATE.get(payment_hash))

    async def cambio_finto():
        return 100_000.0

    async def nota_finta(tg_id, testo, **k):
        NOTIFICHE.append((tg_id, testo))

    async def admin_finto(testo, **k):
        ADMIN.append(testo)

    async def paga_finto(invoice, atteso_sats, taccuino=None, cassaforte="",
                         riga=None, **k):
        USCITE.append((invoice, int(atteso_sats), cassaforte))
        if taccuino is not None:
            taccuino["hash"] = f"out{len(USCITE)}"
        return server.PAGATO

    async def address_finto(ln_address, sats):
        return f"lnbc{sats}rimborso_{ln_address}"

    async def zitto(*a, **k):
        return None

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = pagata_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = nota_finta
    server.notifica_admin = admin_finto
    server.polso_ordini_admin = zitto
    server.paga_venditore = paga_finto
    server.invoice_da_ln_address = address_finto
    server.annuncio_su_nostr = zitto
    server.promo_venduto = zitto
    server.promo_rimuovi = zitto
    server.ritira_da_nostr = zitto
    server.verifica_utente = lambda *a, **k: CHI[0]
    return db


def chiama(fn, corpo, chi=COMPRA, *args):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    CHI[0] = chi
    return asyncio.run(fn(*args, None) if args else fn(None))


def errore(fn, corpo, chi=COMPRA, *args):
    try:
        return "OK", chiama(fn, corpo, chi, *args)
    except SRV.HTTPException as e:
        return e.status_code, e.detail


def semina(qta=5, sconto_b=False):
    """Due venditori con due annunci a testa (ritiro e spedizione), il
    compratore senza Lightning address. Ogni sezione riparte pulita."""
    con = SRV.db()
    for t in ("offerte_righe", "offerte", "ordine_righe", "ordini",
              "pagamenti", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
                "sconto_pacco_criterio,sconto_pacco_soglia,"
                "sconto_pacco_percento) VALUES(222,'Anna','neg22222',1,"
                "'pezzi',2,?)", (10 if sconto_b else 0,))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(333,'Bruno','neg33333',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,ln_address) VALUES(111,'Compra','neg11111',1,'')")
    ids = {}
    for vid, titoli, prezzo in ((222, ("Cuffie", "Tazze"), 30_000),
                                (333, ("Lampada", "Sedia"), 20_000)):
        for t in titoli:
            cur = con.execute(
                "INSERT INTO annunci(venditore_id,titolo,descrizione,"
                "prezzo_sats,categoria,zona,stato,creato,consegna,quantita,"
                "valuta,condizione,spedizione_sats) "
                "VALUES(?,?,'desc',?,'Altro','Torino (TO)','attivo',1,"
                "'entrambe',?,'sats','buono',500)",
                (vid, t, prezzo, qta))
            ids[t] = cur.lastrowid
    con.commit()
    con.close()
    NOTIFICHE.clear()
    ADMIN.clear()
    USCITE.clear()
    return ids


def carrello(coppie):
    return {"righe": [{"annuncio_id": a, "quantita": q} for a, q in coppie],
            "consegna": "ritiro"}


def preventivo(coppie):
    return chiama(SRV.preventivo_ordine,
                  {**carrello(coppie), "pagamento_unico": True})


def totale(coppie):
    p = preventivo(coppie)
    return next(s["totale_sats"] for s in p["strade"] if s["via"] == "ritiro")


def riga(tabella, rid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    r = con.execute(f"SELECT * FROM {tabella} WHERE id=?", (rid,)).fetchone()
    con.close()
    return dict(r) if r else None


def annuncio(aid):
    return riga("annunci", aid)


def ordini_di(pid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    out = [dict(r) for r in con.execute(
        "SELECT * FROM ordini WHERE pagamento_id=? ORDER BY id", (pid,))]
    con.close()
    return out


def busta(ids, coppie_a=None, coppie_b=None):
    """La fattura unica di due carrelli: Anna (Cuffie ×2, Tazze ×1) e
    Bruno (Lampada ×1) di serie."""
    coppie_a = coppie_a or [(ids["Cuffie"], 2), (ids["Tazze"], 1)]
    coppie_b = coppie_b or [(ids["Lampada"], 1)]
    # i totali PRIMA della busta: gli ordini 'creato' prenotano lo
    # stock, e un preventivo chiesto dopo troverebbe i pezzi presi
    tot_a, tot_b = totale(coppie_a), totale(coppie_b)
    r = chiama(SRV.paga_carrelli,
               {"carrelli": [carrello(coppie_a), carrello(coppie_b)]})
    return r, tot_a, tot_b


def paga(r):
    PAGATE[r["payment_hash"]] = True


def prove_fattura_unica():
    print("\n[1] LA FATTURA UNICA — una per la somma, un ordine per venditore")
    ids = semina(sconto_b=True)
    r, tot_a, tot_b = busta(ids)
    prova("la fattura e' UNA, per la somma dei due preventivi", tot_a + tot_b,
          INVOICES[-1][0])
    prova("...e lo sconto del negozio di Anna e' dentro (2 pezzi da 30k "
          "e 1 -> 90k -10% = 81k)", 81_000, tot_a)
    prova("...col memo del pagamento unico", True,
          INVOICES[-1][1].startswith("Barattolo escrow carrello #111"))
    prova("la risposta porta la busta, la bolt11 e gli ordini",
          (True, INVOICES[-1][0], 2),
          (r["pagamento_id"] > 0, r["importo_sats"], len(r["ordini"])))
    p = riga("pagamenti", r["pagamento_id"])
    prova("la busta e' una riga di pagamenti, motivo carrello, creato",
          ("carrello", "creato", 111, tot_a + tot_b, r["payment_hash"]),
          (p["motivo"], p["stato"], p["tg_id"], p["importo_sats"],
           p["payment_hash"]))
    os_ = ordini_di(r["pagamento_id"])
    prova("due ordini 'creato', uno per venditore, con l'hash condiviso",
          [(222, "creato", r["payment_hash"]), (333, "creato", r["payment_hash"])],
          [(o["venditore_id"], o["stato"], o["payment_hash"]) for o in os_])
    prova("...e i loro prezzi sommano alla fattura", tot_a + tot_b,
          sum(o["prezzo_sats"] for o in os_))
    prova("...il carrello di Anna e' un set di due righe, quello di Bruno "
          "di UNA (lecita nella busta)", [2, 1],
          [len(SRV._righe_ordine(SRV.db(), o)) for o in os_])
    con = SRV.db()
    prova("lo stock e' prenotato dagli ordini 'creato'", (2, 1),
          (SRV._riservati(con, ids["Cuffie"]), SRV._riservati(con, ids["Lampada"])))
    con.close()
    # le guardie
    st, det = errore(SRV.paga_carrelli,
                     {"carrelli": [carrello([(ids["Cuffie"], 1)])]})
    prova("un carrello solo: 400 verso «Controlla e paga»", (400, True),
          (st, "almeno due" in det))
    # ...e la riga sola resta vietata FUORI dalla busta: la deroga e'
    # del pagamento unico, non del set
    st, det = errore(SRV.compra, carrello([(ids["Cuffie"], 1)]))
    prova("un set da una riga, senza busta, e' ancora un 400", (400, True),
          (st, "almeno due oggetti" in det))
    st, det = errore(SRV.preventivo_ordine, carrello([(ids["Cuffie"], 1)]))
    prova("...e il preventivo senza il flag pure", 400, st)
    st, det = errore(SRV.paga_carrelli, {"carrelli": [
        carrello([(ids["Cuffie"], 1)]), carrello([(ids["Tazze"], 1)])]})
    prova("lo stesso venditore due volte: 400", (400, True),
          (st, "stesso venditore" in det))
    lista = SRV.miei_ordini(0, "", "")
    mio = next(o for o in lista if o["id"] == os_[0]["id"])
    prova("la lista degli ordini porta la cifra della fattura condivisa",
          (tot_a + tot_b, "creato"),
          (mio.get("pagamento_unico_sats"), mio.get("pagamento_unico_stato")))
    # «Paga ora» sull'ordine di busta: la fattura condivisa, la cifra vera
    nf = chiama(SRV.nuova_fattura_ordine, {}, COMPRA, os_[0]["id"])
    prova("«Paga ora» ripresenta la fattura unica con l'importo intero",
          (r["invoice"], tot_a + tot_b, r["pagamento_id"], False),
          (nf["invoice"], nf["prezzo_sats"], nf.get("pagamento_unico"),
           nf["nuova"]))
    st, det = errore(SRV.annulla_ordine, {}, COMPRA, os_[0]["id"])
    prova("un ordine di busta non si annulla da solo", (400, True),
          (st, "pagamento unico" in det))
    return ids, r, os_


def prove_saldo():
    ids, r, os_ = prove_fattura_unica()
    print("\n[2] IL SALDO — due ordini nascono, ognuno col suo deposito")
    NOTIFICHE.clear()
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("prima del saldo: in attesa", "in_attesa", v["stato"])
    prova("...e il poll del singolo ordine pure", "in_attesa",
          chiama(SRV.verifica_pagamento, {}, COMPRA, os_[0]["id"])["stato"])
    paga(r)
    # IL POLL DEL SINGOLO ORDINE («Paga ora») chiede alla BUSTA: nasce
    # lui E il fratello, non lui solo con la busta ancora 'creato'
    v1 = chiama(SRV.verifica_pagamento, {}, COMPRA, os_[0]["id"])
    prova("il poll del singolo ordine, a saldo arrivato, fa nascere tutta "
          "la busta", ("locked", r["pagamento_id"], "pagato", ["locked", "locked"]),
          (v1["stato"], v1.get("pagamento_unico"),
           riga("pagamenti", r["pagamento_id"])["stato"],
           [o["stato"] for o in ordini_di(r["pagamento_id"])]))
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("al saldo: pagato, due nati, nessun morto",
          ("pagato", 2, 0), (v["stato"], len(v["nati"]), len(v["morti"])))
    # LA BUSTA PAGATA A META' (un giro morto fra il CAS e gli ordini): il
    # poll la trova 'pagato' con ordini fermi e li finisce lui
    ids2 = semina()
    r2, _, _ = busta(ids2)
    con = SRV.db()
    con.execute("UPDATE pagamenti SET stato='pagato', pagato_il=? WHERE id=?",
                (int(time.time()), r2["pagamento_id"]))
    con.commit()
    con.close()
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r2["pagamento_id"])
    prova("una busta pagata con ordini ancora fermi si finisce dal poll",
          ("pagato", 2, ["locked", "locked"]),
          (v["stato"], len(v["nati"]), [o["stato"] for o in ordini_di(r2["pagamento_id"])]))
    ids, r, os_ = prove_fattura_unica()
    NOTIFICHE.clear()
    paga(r)
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("i due ordini sono 'locked'", ["locked", "locked"],
          [o["stato"] for o in ordini_di(r["pagamento_id"])])
    prova("la busta e' 'pagato'", "pagato",
          riga("pagamenti", r["pagamento_id"])["stato"])
    prova("lo stock e' sceso riga per riga (5-2, 5-1, 5-1)", (3, 4, 4),
          (annuncio(ids["Cuffie"])["quantita"], annuncio(ids["Tazze"])["quantita"],
           annuncio(ids["Lampada"])["quantita"]))
    venduto = [n for n in NOTIFICHE if "Hai venduto" in n[1]]
    prova("ogni venditore riceve il SUO «Hai venduto»", {222, 333},
          {n[0] for n in venduto})
    prova("il compratore riceve le due ricevute E il riepilogo", (2, 1),
          (sum(1 for n in NOTIFICHE if n[0] == 111 and "Ordine pagato" in n[1]),
           sum(1 for n in NOTIFICHE if n[0] == 111
               and "Pagamento unico ricevuto" in n[1]
               and "2 ordini nati" in n[1])))
    n_prima = len(NOTIFICHE)
    v2 = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("un secondo poll legge l'esito e non rinotifica nessuno",
          ("pagato", 2, n_prima), (v2["stato"], len(v2["nati"]), len(NOTIFICHE)))
    # ...e nemmeno l'INCASSO chiamato a mano una seconda volta (il CAS
    # sulla busta: e' lui che tiene fuori il poll gemello e l'orologio)
    v3 = asyncio.run(SRV._incassa_carrello(r["pagamento_id"]))
    prova("l'incasso richiamato a cose fatte legge l'esito e tace",
          ("pagato", 2, n_prima), (v3["stato"], len(v3["nati"]), len(NOTIFICHE)))
    st, det = errore(SRV.annulla_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("a saldo arrivato la busta non si annulla piu'", 400, st)
    # il singolo ordine resta suo: il rimborso di UNO non tocca l'altro
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address='compra@wallet' WHERE tg_id=111")
    con.commit()
    con.close()
    o_a = next(o for o in ordini_di(r["pagamento_id"]) if o["venditore_id"] == 222)
    esito = asyncio.run(SRV._rimborsa_compratore(o_a["id"]))
    prova("il rimborso dell'ordine di Anna (per una disputa) esce dalla "
          "cassaforte per il SUO prezzo", (True, "refunded", o_a["prezzo_sats"]),
          (esito["ok"], esito["stato"], USCITE[-1][1]))
    prova("...la merce di Anna torna in vetrina", (5, 5),
          (annuncio(ids["Cuffie"])["quantita"], annuncio(ids["Tazze"])["quantita"]))
    prova("...e l'ordine di Bruno resta 'locked' com'era", ("locked", 4),
          (next(o["stato"] for o in ordini_di(r["pagamento_id"])
                if o["venditore_id"] == 333),
           annuncio(ids["Lampada"])["quantita"]))
    # il poll del singolo ordine, su una busta pagata, risponde lo stato suo
    o_b = next(o for o in ordini_di(r["pagamento_id"]) if o["venditore_id"] == 333)
    prova("il poll del singolo ordine dice il suo stato", "locked",
          chiama(SRV.verifica_pagamento, {}, COMPRA, o_b["id"])["stato"])


def prove_esaurito():
    print("\n[3] L'ESAURITO IN MEZZO — quell'ordine non nasce, la parte torna")
    ids = semina()
    r, tot_a, tot_b = busta(ids)
    # Bruno rimuove la Lampada mentre la fattura e' viva
    chiama(SRV.rimuovi_annuncio, {}, VENDE_B, ids["Lampada"])
    prova("la rimozione annulla l'ordine di Bruno e lascia quello di Anna",
          ["creato", "annullato"],
          [o["stato"] for o in ordini_di(r["pagamento_id"])])
    NOTIFICHE.clear()
    paga(r)
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("al saldo: uno nato, uno morto",
          ("pagato", 1, 1), (v["stato"], len(v["nati"]), len(v["morti"])))
    o_b = next(o for o in ordini_di(r["pagamento_id"]) if o["venditore_id"] == 333)
    o_a = next(o for o in ordini_di(r["pagamento_id"]) if o["venditore_id"] == 222)
    prova("l'ordine di Anna e' locked; quello di Bruno e' 'refund', mai "
          "incassato, senza Lightning address da pagare",
          ("locked", "refund", 1), (o_a["stato"], o_b["stato"], o_b["mai_incassato"]))
    prova("...il morto nomina il pezzo e la cifra", ("Lampada", tot_b),
          (v["morti"][0]["manca"], v["morti"][0]["prezzo_sats"]))
    prova("la Lampada resta 'rimosso' a 5: niente torna in vetrina",
          ("rimosso", 5), (annuncio(ids["Lampada"])["stato"],
                           annuncio(ids["Lampada"])["quantita"]))
    prova("lo stock di Anna e' sceso, il suo ordine e' nato davvero", 3,
          annuncio(ids["Cuffie"])["quantita"])
    prova("al compratore: il riepilogo dice che uno non e' nato e la parte "
          "torna, e la richiesta di un modo per riceverla", (1, 1),
          (sum(1 for n in NOTIFICHE if n[0] == 111 and "non è potuto nascere" in n[1]
               and "Lampada" in n[1]),
           sum(1 for n in NOTIFICHE if n[0] == 111
               and "imposta il tuo Lightning address" in n[1])))
    prova("...e a Bruno nessuna disputa inventata", 0,
          sum(1 for n in NOTIFICHE if n[0] == 333 and "disputa" in n[1].lower()))
    # il compratore mette l'address: la parte esce dalla cassaforte
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address='compra@wallet' WHERE tg_id=111")
    con.commit()
    con.close()
    USCITE.clear()
    esito = asyncio.run(SRV._rimborsa_compratore(o_b["id"]))
    prova("con l'address la parte di Bruno esce, per intero, dalla "
          "cassaforte della busta", (True, "refunded", tot_b, "saas"),
          (esito["ok"], esito["stato"], USCITE[-1][1], USCITE[-1][2]))
    prova("...e ancora niente torna in vetrina (mai uscito niente)",
          ("rimosso", 5), (annuncio(ids["Lampada"])["stato"],
                           annuncio(ids["Lampada"])["quantita"]))
    prova("il riepilogo del rimborso parla della parte, non di una disputa",
          (1, 0), (sum(1 for n in NOTIFICHE if n[0] == 111 and "Rimborso in arrivo" in n[1]),
                   sum(1 for n in NOTIFICHE if n[0] == 111 and "Disputa" in n[1])))


def prove_annullo_e_scadenza():
    print("\n[4] L'ANNULLO E LA SCADENZA — le lapidi, e il saldo tardivo")
    ids = semina()
    r, tot_a, tot_b = busta(ids)
    a = chiama(SRV.annulla_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("l'annullo seppellisce la busta e i suoi due ordini", (True, 2),
          (a["ok"], a["ordini_annullati"]))
    prova("...busta e ordini sono lapidi", ("annullato", ["annullato", "annullato"]),
          (riga("pagamenti", r["pagamento_id"])["stato"],
           [o["stato"] for o in ordini_di(r["pagamento_id"])]))
    con = SRV.db()
    prova("...e lo stock e' libero", 0, SRV._riservati(con, ids["Cuffie"]))
    con.close()
    v = chiama(SRV.verifica_carrelli, {}, COMPRA, r["pagamento_id"])
    prova("il poll dice annullato, con gli ordini in attesa", ("annullato", 2),
          (v["stato"], len(v["in_attesa"])))
    # il saldo tardivo: il compratore paga la fattura annullata
    paga(r)
    asyncio.run(SRV.controlla_annullati())
    prova("il riacciuffo: la busta torna pagata e gli ordini nascono",
          ("pagato", ["locked", "locked"]),
          (riga("pagamenti", r["pagamento_id"])["stato"],
           [o["stato"] for o in ordini_di(r["pagamento_id"])]))
    prova("...con lo stock sceso", (3, 4), (annuncio(ids["Cuffie"])["quantita"],
                                              annuncio(ids["Lampada"])["quantita"]))
    # la scadenza: la fattura muore senza saldo
    ids = semina()
    r, tot_a, tot_b = busta(ids)
    con = SRV.db()
    vecchio = int(time.time()) - 2000
    con.execute("UPDATE pagamenti SET creato=? WHERE id=?", (vecchio, r["pagamento_id"]))
    con.execute("UPDATE ordini SET creato=? WHERE pagamento_id=?", (vecchio, r["pagamento_id"]))
    con.commit()
    con.close()
    asyncio.run(SRV.controlla_abbandonati())
    prova("scaduta senza saldo: la busta e i suoi ordini sono lapidi",
          ("annullato", ["annullato", "annullato"]),
          (riga("pagamenti", r["pagamento_id"])["stato"],
           [o["stato"] for o in ordini_di(r["pagamento_id"])]))
    st, det = errore(SRV.nuova_fattura_ordine, {}, COMPRA,
                     ordini_di(r["pagamento_id"])[0]["id"])
    prova("«Paga ora» su un ordine sepolto: non si rigenera", 400, st)
    # la scadenza col saldo mai verificato: l'orologio incassa
    ids = semina()
    r, tot_a, tot_b = busta(ids)
    con = SRV.db()
    con.execute("UPDATE pagamenti SET creato=? WHERE id=?", (vecchio, r["pagamento_id"]))
    con.execute("UPDATE ordini SET creato=? WHERE pagamento_id=?", (vecchio, r["pagamento_id"]))
    con.commit()
    con.close()
    paga(r)
    asyncio.run(SRV.controlla_abbandonati())
    prova("scaduta ma pagata: l'ultimo sguardo incassa la busta e gli ordini",
          ("pagato", ["locked", "locked"]),
          (riga("pagamenti", r["pagamento_id"])["stato"],
           [o["stato"] for o in ordini_di(r["pagamento_id"])]))
    # il saldo tardivo su una lapide la cui merce e' andata ad altri
    ids = semina(qta=1)
    r, tot_a, tot_b = busta(ids, [(ids["Cuffie"], 1)], [(ids["Lampada"], 1)])
    chiama(SRV.annulla_carrelli, {}, COMPRA, r["pagamento_id"])
    # un altro ha in mano la Lampada: un suo ordine 'creato' la PRENOTA
    # (l'annuncio resta attivo con un pezzo, ma il pezzo e' suo)
    con = SRV.db()
    con.execute("INSERT INTO ordini(annuncio_id,compratore_id,venditore_id,"
                "prezzo_sats,stato,payment_hash,quantita,creato,aggiornato,"
                "cassaforte) VALUES(?,444,333,20000,'creato','hashaltro',1,?,?,'saas')",
                (ids["Lampada"], int(time.time()), int(time.time())))
    con.commit()
    con.close()
    paga(r)
    NOTIFICHE.clear()
    asyncio.run(SRV.controlla_annullati())
    os_ = ordini_di(r["pagamento_id"])
    prova("il saldo tardivo fa nascere Anna e rimborsa la parte di Bruno, "
          "la cui merce e' prenotata da un altro", ("locked", "refund", 1),
          (next(o["stato"] for o in os_ if o["venditore_id"] == 222),
           next(o["stato"] for o in os_ if o["venditore_id"] == 333),
           next(o["mai_incassato"] for o in os_ if o["venditore_id"] == 333)))


def prove_conto_che_cambia():
    print("\n[5] IL CONTO CHE CAMBIA fra le due passate: si seppellisce tutto")
    ids = semina()
    vero = SRV._compra_set

    async def storto(user, d, busta=None):
        if busta:
            busta = {**busta, "atteso": busta["atteso"] + 1}
        return await vero(user, d, busta)
    SRV._compra_set = storto
    try:
        st, det = errore(SRV.paga_carrelli, {"carrelli": [
            carrello([(ids["Cuffie"], 1)]), carrello([(ids["Lampada"], 1)])]})
    finally:
        SRV._compra_set = vero
    prova("409 che nomina il carrello", (409, True),
          (st, det.startswith("Carrello 1:") and "cambiato" in det))
    con = SRV.db()
    con.row_factory = sqlite3.Row
    p = con.execute("SELECT stato FROM pagamenti ORDER BY id DESC LIMIT 1").fetchone()
    vivi = con.execute("SELECT COUNT(*) AS n FROM ordini WHERE stato='creato'").fetchone()["n"]
    con.close()
    prova("la busta e' una lapide e nessun ordine e' rimasto 'creato'",
          ("annullato", 0), (p["stato"], vivi))
    # ...e il doppio saldo non esiste: la fattura coniata non ha ordini
    # vivi da far nascere, e il riacciuffo la trova con la merce
    # ricontrollata (qui: niente ordini -> niente da fare)


def prove_ronda():
    print("\n[6] LA RONDA DEL LIBRO MASTRO tace su tutto questo")
    con = SRV.db()
    suonati = {}
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        try:
            ids = [str(r[0]) for r in con.execute(sql).fetchall()]
        except sqlite3.OperationalError as e:
            ids = [f"ERRORE {e}"]
        if ids:
            suonati[nome] = ids
    con.close()
    prova("nessun controllo suona", {}, suonati)
    prova("...e le colonne del pagamento unico esistono nel database vero",
          True, "pagamento_id" in [r[1] for r in
                                    SRV.db().execute("PRAGMA table_info(ordini)")])


def main():
    db = avvio()
    print(__doc__.strip().splitlines()[0])
    print(f"  database usa-e-getta: {db}")
    prove_saldo()
    prove_esaurito()
    prove_annullo_e_scadenza()
    prove_conto_che_cambia()
    prove_ronda()
    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
