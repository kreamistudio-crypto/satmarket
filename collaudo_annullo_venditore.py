# -*- coding: utf-8 -*-
"""
L'ANNULLO DEL VENDITORE, A SATS GIA' IN CASSAFORTE (1 ott 2026).

Chi compra ha pagato, chi vende non puo' piu' consegnare (si e' rotto,
l'ha venduto altrove) e lo dice da solo: i sats tornano a chi ha
comprato SENZA passare da un moderatore. Non e' una hold invoice che
scade — l'escrow di Barattolo e' custodiale — e' un PAGAMENTO in uscita,
quello che `_rimborsa_compratore` fa gia' per una disputa vinta. Qui si
cammina il giro intero sul server VERO, con un database usa-e-getta:

  1. compratore CON Lightning address: il venditore annulla da 'locked'
     con un motivo → 'refunded' sul posto, stock e vetrina tornano, i
     due avvisi dicono «annullato» e MAI «disputa», `disputata` resta 0;
  2. compratore SENZA metodo: l'ordine resta in 'refund', chi compra
     viene invitato a dare un metodo, chi vende sa che il gesto e'
     fatto; poi chi compra incolla la fattura → 'refunded';
  3. le porte chiuse: chi compra, l'estraneo, 'creato', 'shipped',
     il secondo annullo, un pagamento gia' in volo (409);
  4. dopo l'annullo la spedizione e la conferma non passano piu';
  5. il motivo si ripulisce (spazi) e si tronca a MOTIVO_ANNULLO_MAX;
  6. il feedback: chi compra vota su 'refunded', non su 'refund';
  7. la ronda del libro mastro tace.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. LNbits non viene mai chiamato: gira senza rete.

USO:  python collaudo_annullo_venditore.py
"""

import asyncio
import html
import os
import sqlite3
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
DETTO = []          # (destinatario, testo) di ogni notifica


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-annullo-"),
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
    cfg.PROTEZIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
        return {"payment_hash": f"hash{int(time.time()*1000000)}",
                "payment_request": f"lnbc{sats}collaudo"}

    async def sempre_pagata(_hash, _cassaforte=""):
        return True

    async def cambio_finto():
        return 100_000.0

    async def notifica_finta(chi, testo, *a, **k):
        DETTO.append((chi, testo))

    # la FIRMA del vero, parola per parola (vedi
    # collaudo_feedback_confermato: un doppio con la firma vecchia
    # e' rimasto rosso tre giorni)
    async def paga_finto(bolt11, atteso_sats, diario=None, *, cassaforte,
                         riga=()):
        return SRV.PAGATO

    async def invoice_da_address(addr, sats):
        return f"lnbc{sats}address"

    async def importo_finto(bolt11, dec=None, cassaforte=""):
        # le fatture di cartone portano l'importo nel nome
        try:
            return int(bolt11[4:].split("x")[0])
        except ValueError:
            return None

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = sempre_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = notifica_finta
    server.paga_venditore = paga_finto
    server.invoice_da_ln_address = invoice_da_address
    server.importo_invoice = importo_finto
    server.rifiuto_scadenza = lambda bolt11, adesso=None: ""

    async def zitto(*a, **k):
        return None

    server.polso_ordini_admin = zitto
    server.premia_distintivi = zitto
    server.premia_xp = zitto
    server.notifica_admin = zitto
    server.annuncio_su_nostr = zitto
    server.promo_venduto = zitto
    return db


def come(tg_id, admin=False):
    SRV.verifica_utente = lambda *a, **k: {
        "id": tg_id, "nome": f"U{tg_id}", "first_name": f"U{tg_id}",
        "username": f"u{tg_id}", "admin": admin}


def chiama(fn, *args, corpo=None):
    if corpo is not None:
        async def leggi(_req):
            return corpo
        SRV.leggi_json = leggi
    return asyncio.run(fn(*args))


def errore(fn, *args, corpo=None):
    """Il codice e il messaggio di un rifiuto, o None se e' passato."""
    try:
        chiama(fn, *args, corpo=corpo)
        return None
    except Exception as e:
        return (getattr(e, "status_code", type(e).__name__),
                str(getattr(e, "detail", e)))


def riga(oid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    o = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return dict(o)


def annuncio(aid):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    a = con.execute("SELECT * FROM annunci WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(a)


def utente(tg_id):
    con = SRV.db()
    con.row_factory = sqlite3.Row
    u = con.execute("SELECT * FROM utenti WHERE tg_id=?", (tg_id,)).fetchone()
    con.close()
    return dict(u)


def scrivi(oid, **campi):
    con = SRV.db()
    con.execute("UPDATE ordini SET "
                + ", ".join(f"{k}=?" for k in campi) + " WHERE id=?",
                tuple(campi.values()) + (oid,))
    con.commit()
    con.close()


def address(tg_id, addr):
    con = SRV.db()
    con.execute("UPDATE utenti SET ln_address=? WHERE tg_id=?", (addr, tg_id))
    con.commit()
    con.close()


def semina():
    """Chi vende (222) e chi compra (111); l'estraneo (333) non ha
    niente. Un pezzo per annuncio: cosi' il pagamento lo porta a
    'venduto' e il rimborso DEVE rimetterlo in vetrina."""
    con = SRV.db()
    for t in ("feedback", "ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute("UPDATE utenti SET rating=0, n_feedback=0, n_recensori=0")
    for tg, nome, neg in ((222, "Vende", "neg22222"),
                          (111, "Compra", "neg11111"),
                          (333, "Estraneo", "neg33333")):
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                    "registrato,ln_address) VALUES(?,?,?,1,'')",
                    (tg, nome, neg))
    ids = []
    for n in range(8):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'una cosa vera',50000,'Altro','Pavia (PV)',"
            "'attivo',1,'spedizione',1,'sats','nuovo')", (f"Cosa {n}",))
        ids.append(cur.lastrowid)
    con.commit()
    con.close()
    return ids


def ordine_pagato(annuncio_id):
    """Il giro vero fino a 'locked': compra, e il poll trova la
    fattura pagata (`_incassa_ordine` scala lo stock da se')."""
    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": annuncio_id,
                                        "consegna": "spedizione",
                                        "indirizzo": {"nome": "Mario Rossi",
                                                      "via": "Via Roma 1",
                                                      "cap": "27100",
                                                      "citta": "Pavia",
                                                      "prov": "PV",
                                                      "tel": "3330000000"}})
    oid = c["ordine_id"]
    chiama(SRV.verifica_pagamento, oid)
    if riga(oid)["stato"] != "locked":
        raise SystemExit(f"⚠️  l'ordine {oid} e' in "
                         f"'{riga(oid)['stato']}' e non in 'locked'")
    return oid


def detti(a_chi):
    return [t for chi, t in DETTO if chi == a_chi]


def main():
    print("=" * 60)
    print("  L'ANNULLO DEL VENDITORE, A SATS GIA' IN CASSAFORTE")
    print("=" * 60)
    avvio()
    ann = semina()

    # ---- 1. Il compratore ha un address: rimborso sul posto ---------
    print("\n[1. chi compra ha un Lightning address: rimborso immediato]")
    address(111, "compra@wallet.tld")
    oid = ordine_pagato(ann[0])
    prova("il pagamento ha scalato lo stock e chiuso la vetrina",
          (0, "venduto"), (annuncio(ann[0])["quantita"],
                           annuncio(ann[0])["stato"]))
    DETTO.clear()
    come(222)
    d = chiama(SRV.annulla_da_venditore, oid, None,
               corpo={"motivo": "Si è rotto durante l'imballaggio"})
    prova("la risposta: ok, 'refunded', rimborsato", (True, "refunded", True),
          (d["ok"], d["stato"], d["rimborsato"]))
    r = riga(oid)
    prova("l'ordine chiude a 'refunded'", "refunded", r["stato"])
    prova("il timbro dell'annullo c'e'", True, r["annullato_venditore_il"] > 0)
    prova("...col motivo", "Si è rotto durante l'imballaggio",
          r["motivo_annullo"])
    prova("nessuna disputa: `disputata` resta 0", 0, r["disputata"])
    # (`payout_verso` lo scrive il `paga_venditore` VERO, qui sostituito)
    prova("il payout e' timbrato uscito", "uscito", r["payout_stato"])
    prova("lo stock torna e l'annuncio e' di nuovo in vetrina",
          (1, "attivo"), (annuncio(ann[0])["quantita"],
                          annuncio(ann[0])["stato"]))
    a_compra, a_vende = detti(111), detti(222)
    prova("un avviso a chi compra, uno a chi vende", (1, 1),
          (len(a_compra), len(a_vende)))
    prova("a chi compra: il venditore ha annullato, col motivo e la cifra",
          True,
          "ha annullato" in a_compra[0]
          # il motivo viaggia SCAPPATO (parse_mode HTML): l'apostrofo
          # diventa &#x27;, ed e' giusto cosi'
          and html.escape("Si è rotto durante l'imballaggio") in a_compra[0]
          and SRV._fmt_sats(50000) in a_compra[0])
    prova("a chi vende: hai annullato, e la vetrina", True,
          "Hai annullato" in a_vende[0] and "vetrina" in a_vende[0])
    prova("MAI la parola «disputa», da nessuna parte", [],
          [t for t in a_compra + a_vende if "isputa" in t])
    prova("il feedback e' aperto a chi compra", True,
          SRV._ammette_feedback("refunded", 0, 0))

    # ---- 2. Senza metodo: 'refund', poi la fattura ------------------
    print("\n[2. chi compra non ha un metodo: 'refund', poi la fattura]")
    address(111, "")
    oid2 = ordine_pagato(ann[1])
    DETTO.clear()
    come(222)
    d = chiama(SRV.annulla_da_venditore, oid2, None, corpo={})
    prova("la risposta: ok, 'refund', NON rimborsato", (True, "refund", False),
          (d["ok"], d["stato"], d["rimborsato"]))
    r = riga(oid2)
    prova("l'ordine e' in 'refund' col timbro e senza motivo",
          ("refund", True, ""), (r["stato"], r["annullato_venditore_il"] > 0,
                                 r["motivo_annullo"]))
    prova("la vetrina NON torna finche' i sats non sono tornati",
          (0, "venduto"), (annuncio(ann[1])["quantita"],
                           annuncio(ann[1])["stato"]))
    a_compra, a_vende = detti(111), detti(222)
    prova("a chi compra: annullato, e come riceverli", True,
          len(a_compra) == 1 and "ha annullato" in a_compra[0]
          and "Lightning address" in a_compra[0])
    prova("a chi vende: il gesto e' fatto, i sats aspettano un metodo", True,
          len(a_vende) == 1 and "Hai annullato" in a_vende[0]
          and "dove" in a_vende[0])
    prova("...e nessuno ha sentito «disputa»", [],
          [t for t in a_compra + a_vende if "isputa" in t])
    prova("su 'refund' il feedback resta chiuso", False,
          SRV._ammette_feedback("refund", 0, 0))
    # chi compra incolla la fattura: il rimborso parte da li'
    DETTO.clear()
    come(111)
    d = chiama(SRV.deposita_invoice, oid2, None,
               corpo={"invoice": "lnbc50000x"})
    prova("la fattura chiude a 'refunded'", ("refunded", True),
          (riga(oid2)["stato"], d["ok"]))
    prova("...e adesso la vetrina torna", (1, "attivo"),
          (annuncio(ann[1])["quantita"], annuncio(ann[1])["stato"]))
    prova("gli avvisi del rimborso fatto dicono ancora «annullato»", True,
          all("annullat" in t for _, t in DETTO)
          and not any("isputa" in t for _, t in DETTO))
    prova("chi vende sente che la vetrina e' tornata", True,
          any("vetrina" in t for t in detti(222)))

    # ---- 3. Le porte chiuse ----------------------------------------
    print("\n[3. chi resta fuori, e resta fuori per un motivo]")
    oid3 = ordine_pagato(ann[2])
    come(111)
    prova("chi compra non annulla da qui",
          (400, "Operazione non permessa"),
          errore(SRV.annulla_da_venditore, oid3, None, corpo={}))
    come(333)
    prova("l'estraneo nemmeno",
          (400, "Operazione non permessa"),
          errore(SRV.annulla_da_venditore, oid3, None, corpo={}))
    come(222)
    scrivi(oid3, payout_stato="incerto")
    prova("un pagamento gia' in volo ferma tutto, con un 409 che spiega",
          True,
          (lambda e: e is not None and e[0] == 409
           and "moderatori" in e[1])(
               errore(SRV.annulla_da_venditore, oid3, None, corpo={})))
    prova("...e l'ordine non si e' mosso", "locked", riga(oid3)["stato"])
    scrivi(oid3, payout_stato="")
    chiama(SRV.segna_spedito, oid3, None,
           corpo={"corriere": "Poste Italiane", "tracking": "AB123456789IT"})
    prova("a pacco partito ('shipped') la strada e' la disputa",
          (400, "Operazione non permessa"),
          errore(SRV.annulla_da_venditore, oid3, None, corpo={}))
    come(111)
    c = chiama(SRV.compra, None, corpo={"annuncio_id": ann[3],
                                        "consegna": "spedizione",
                                        "indirizzo": {"nome": "Mario Rossi",
                                                      "via": "Via Roma 1",
                                                      "cap": "27100",
                                                      "citta": "Pavia",
                                                      "prov": "PV",
                                                      "tel": "3330000000"}})
    come(222)
    prova("a sats mai arrivati ('creato') non c'e' niente da rendere",
          (400, "Operazione non permessa"),
          errore(SRV.annulla_da_venditore, c["ordine_id"], None, corpo={}))
    prova("il secondo annullo su 'refunded' non passa",
          (400, "Operazione non permessa"),
          errore(SRV.annulla_da_venditore, oid, None, corpo={}))

    # ---- 4. Dopo l'annullo le altre porte si chiudono ---------------
    print("\n[4. dopo l'annullo, spedire e confermare non si puo' piu']")
    address(111, "")
    oid4 = ordine_pagato(ann[4])
    come(222)
    chiama(SRV.annulla_da_venditore, oid4, None, corpo={"motivo": "x"})
    prova("l'ordine aspetta il metodo di chi compra", "refund",
          riga(oid4)["stato"])
    prova("chi vende non puo' piu' segnare la spedizione",
          (400, "Operazione non permessa"),
          errore(SRV.segna_spedito, oid4, None,
                 corpo={"corriere": "Poste Italiane", "tracking": "X1"}))
    come(111)
    e = errore(SRV.conferma_ricezione, oid4)
    prova("chi compra non puo' piu' confermare la ricezione", True,
          e is not None and e[0] == 400)
    prova("...e `_sblocca_sats` non parte da 'refund'", False,
          asyncio.run(SRV._sblocca_sats(oid4))["ok"])
    prova("l'ordine e' ancora in 'refund', coi sats in cassaforte",
          "refund", riga(oid4)["stato"])

    # ---- 5. Il motivo si ripulisce e si tronca ----------------------
    print("\n[5. il motivo: spazi collassati, tetto a MOTIVO_ANNULLO_MAX]")
    address(111, "compra@wallet.tld")
    oid5 = ordine_pagato(ann[5])
    come(222)
    lungo = "  troppo   lungo\n\n" + "a" * 500
    chiama(SRV.annulla_da_venditore, oid5, None, corpo={"motivo": lungo})
    m = riga(oid5)["motivo_annullo"]
    prova("gli spazi si collassano", True, m.startswith("troppo lungo a"))
    prova("e la frase si ferma al tetto", SRV.MOTIVO_ANNULLO_MAX, len(m))
    oid6 = ordine_pagato(ann[6])
    come(222)
    chiama(SRV.annulla_da_venditore, oid6, None, corpo={"motivo": 12345})
    prova("un motivo che non e' testo non rompe niente", "12345",
          riga(oid6)["motivo_annullo"])

    # ---- 6. Il feedback di chi compra -------------------------------
    print("\n[6. chi compra vota il venditore che ha annullato]")
    come(111)
    d = chiama(SRV.lascia_feedback, oid, None,
               corpo={"voto": 2, "commento": "Ha annullato dopo il pagamento"})
    prova("il voto passa su 'refunded'", True, d["ok"])
    prova("...e il venditore ne porta il segno", (2.0, 1),
          (utente(222)["rating"], utente(222)["n_recensori"]))
    e = errore(SRV.lascia_feedback, oid4, None, corpo={"voto": 1})
    prova("su 'refund' (sats non ancora tornati) il voto aspetta",
          (400, "Il feedback si lascia a affare concluso"), e)

    # ---- 7. La ronda del libro mastro tace -------------------------
    print("\n[7. e il libro mastro non ha niente da dire]")
    DETTO.clear()
    asyncio.run(SRV.controlla_libro_mastro())
    guai = [t for _, t in DETTO if "\U0001f9ca" in t or "libro" in t.lower()]
    prova("la ronda tace", [], guai)

    print("\n" + "=" * 60)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 60)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
