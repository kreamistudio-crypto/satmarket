# -*- coding: utf-8 -*-
"""LE SCELTE «QUALSIASI» DEI NEGOZI COLLEGATI, fatte girare per davvero
(19 nov 2026, cantiere scelte-negozio).

Il difetto dal campo: il negozio Uhmami (WooCommerce) vende una box con
due tendine — il gusto della pallina, la composta — e le sue sei
variazioni sono tutte «Qualsiasi / Qualsiasi», stesso prezzo, stesso
codice articolo «025». Entravano sei annunci «Box — 025» e chi
comprava non poteva dire che gusto voleva.

`prove.py` (prove_scelte_negozio) fa girare le pure e i giudici. Qui
gira il SERVER VERO, su un database usa-e-getta, e si chiedono le cose
che solo la filiera intera puo' dire:

  · il catalogo di Uhmami, passato dalla riconciliazione vera dentro la
    tabella VERA, fa UN annuncio col titolo pulito e le tendine in
    colonna (la colonna nasce dalla migrazione del server, non da noi);
  · la scheda pubblica e il preventivo le mandano;
  · «Paga» senza scelta, o con una voce che non c'e', e' un 400 — e
    prima della invoice: nessuna fattura orfana;
  · con la scelta l'ordine nasce, e la scelta e' nella NOTA, cioe' dove
    il venditore la legge gia' su ogni strada;
  · nel carrello, pezzo per pezzo, col titolo davanti;
  · la regressione: un annuncio senza tendine compra come ieri.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. LNbits non viene mai chiamato (le invoice si
contano), niente rete, niente relay.

USO:  python collaudo_scelte_negozio.py
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
PALLINE = ["peperoncino", "curry - sesamo", "rosmarino-zenzero"]
COMPOSTE = ["Arancia", "Fragola", "Pera"]
CASA = {"nome": "Mario Rossi", "via": "Via Roma 1", "cap": "27100",
        "citta": "Pavia"}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def alza(nome, fn, dentro=""):
    global PASSATE, FALLITE
    try:
        fn()
    except Exception as e:
        codice = getattr(e, "status_code", None)
        testo = str(getattr(e, "detail", e))
        if codice == 400 and (not dentro or dentro.lower() in testo.lower()):
            PASSATE += 1
            print(f"  ✓ {nome}")
            return
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso 400 con {dentro!r}"
              f"\n      avuto:  {codice} {testo!r}")
        return
    FALLITE += 1
    print(f"  ✗ {nome}\n      atteso un rifiuto, non e' arrivato")


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-scelte-"),
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
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return 100_000.0

    async def zitta(*a, **k):
        return None

    async def mai_pagata(_hash, _cassaforte=""):
        return False

    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = mai_pagata
    server.cambio_btc_eur = cambio_finto
    server.notifica = zitta
    server.polso_ordini_admin = lambda *a, **k: None
    return db


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    SRV.verifica_utente = lambda *a, **k: COMPRA
    return asyncio.run(fn(None))


def catalogo_uhmami():
    """Il prodotto com'e' sul negozio (letto dalla pagina il 19 nov 2026):
    sei variazioni tutte «Qualsiasi», la giacenza sul padre."""
    variazioni = [{"id": 1623 + i, "sku": "025", "price": "17.00",
                   "regular_price": "17.00", "manage_stock": "parent",
                   "stock_status": "instock", "status": "publish",
                   "attributes": []} for i in range(6)]
    return [{"id": 1600, "name": "Box Natale La Sfiziosa (pre-ordine)",
             "type": "variable", "status": "publish",
             "description": "<p>Un'idea regalo</p>",
             "manage_stock": True, "stock_quantity": 10,
             "images": [{"src": "https://cdn.invalid/box.jpg"}],
             "attributes": [
                 {"id": 0, "name": "Palline Uhmami", "variation": True,
                  "options": PALLINE},
                 {"id": 0, "name": "Composta di Frutta", "variation": True,
                  "options": COMPOSTE}],
             "_variazioni": variazioni}]


def main():
    print("=" * 58)
    print("  LE SCELTE «QUALSIASI» DEI NEGOZI — il giro vero")
    print("=" * 58)
    db = avvio()
    import importa_negozio
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(222,'Uhmami','uhmami','uhmami')")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(111,'Compra','compra','compra11')")
    con.commit()

    # ---- 1. l'import, sulla tabella vera ----------------------------
    print("\n[il catalogo di Uhmami entra: un annuncio, due tendine]")
    connettore = {"id": 4, "fonte": "woo", "tg_id": 222,
                  "zona": "Senago (MI)", "consegna": "spedizione",
                  "spedizione_eur": 5.0, "spedizione_punto_eur": 0.0,
                  "spedizione_punto_dichiarata": 0,
                  "spedizione_extra_eur": 0.0}
    righe = importa_negozio.traduci(catalogo_uhmami(), "woo",
                                    {"EUR": 100_000.0})
    importa_negozio.riconcilia_connettore(con, connettore, righe,
                                          lambda *a: "box.jpg", {}, completo=True)
    con.commit()
    nati = con.execute("SELECT * FROM annunci WHERE connettore_id=4"
                       ).fetchall()
    prova("un annuncio solo, non sei", 1, len(nati))
    box = nati[0]
    prova("...col titolo del negozio, senza «— 025»",
          "Box Natale La Sfiziosa (pre-ordine)", box["titolo"])
    prova("...le tendine in colonna",
          [["Palline Uhmami", PALLINE], ["Composta di Frutta", COMPOSTE]],
          json.loads(box["scelte"]))
    prova("...e 10 box in giacenza, non 60", 10, box["quantita"])
    # il secondo giro, identico, non riscrive niente (il patto di _aggiorna)
    prima = con.total_changes
    importa_negozio.riconcilia_connettore(
        con, connettore, importa_negozio.traduci(
            catalogo_uhmami(), "woo", {"EUR": 100_000.0}),
        lambda *a: "box.jpg", {}, completo=True)
    con.commit()
    prova("il giro dopo, a catalogo fermo, non scrive niente", prima,
          con.total_changes)
    # si mette in vetrina come farebbe la moderazione, con la consegna
    # e le tariffe di un annuncio semplice
    con.execute("UPDATE annunci SET stato='attivo', consegna='spedizione', "
                "spedizione_sats=4000, valuta='sats', prezzo_sats=17000 "
                "WHERE id=?", (box["id"],))
    # un secondo oggetto dello stesso negozio, SENZA tendine, per il
    # carrello e per la regressione (dallo stesso collegamento: un set
    # non mescola le origini, `chiave_origine`)
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats,fonte,connettore_id,origine_chiave) "
        "VALUES(222,'Composta di pere','x',9000,'Altro',"
        "'Senago (MI)','attivo',1,'spedizione',5,'sats','nuovo',4000,"
        "'woo',4,'1700')")
    semplice = cur.lastrowid
    con.commit()
    bid = box["id"]

    # ---- 2. la scheda e il preventivo -------------------------------
    print("\n[la scheda e la cassa le sanno]")
    SRV.verifica_utente = lambda *a, **k: COMPRA
    scheda = SRV.un_annuncio(bid, "", "")
    prova("la scheda pubblica porta le tendine come lista",
          [["Palline Uhmami", PALLINE], ["Composta di Frutta", COMPOSTE]],
          scheda.get("scelte"))
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": bid, "quantita": 1})
    prova("il preventivo del singolo le manda alla cassa",
          ["Palline Uhmami", "Composta di Frutta"],
          [s[0] for s in p.get("scelte") or []])
    p = chiama(SRV.preventivo_ordine, {
        "righe": [{"annuncio_id": bid, "quantita": 1},
                  {"annuncio_id": semplice, "quantita": 1}]})
    prova("...e quello del carrello per id, solo per chi ne ha",
          [str(bid)], list((p.get("scelte") or {}).keys()))
    p = chiama(SRV.preventivo_ordine, {"annuncio_id": semplice,
                                       "quantita": 1})
    prova("un annuncio senza tendine non ne manda", [], p.get("scelte"))

    # ---- 3. Paga senza scelta: il no, prima della invoice -----------
    print("\n[senza la scelta non si paga]")
    base = {"annuncio_id": bid, "quantita": 1, "consegna": "spedizione",
            "spedizione_via": "casa", "indirizzo": dict(CASA),
            "indirizzo_confermato": True}
    quante = len(INVOICES)
    alza("l'app vecchia (niente chiave) si sente dire di aggiornare",
         lambda: chiama(SRV.compra, dict(base)), "aggiorna l'app")
    alza("una tendina vuota: si dice quale",
         lambda: chiama(SRV.compra, dict(base, scelte={
             "Palline Uhmami": "peperoncino"})), "Composta di Frutta")
    alza("una voce che il negozio non ha",
         lambda: chiama(SRV.compra, dict(base, scelte={
             "Palline Uhmami": "aglio", "Composta di Frutta": "Pera"})),
         "voci dell'elenco")
    prova("...e nessun rifiuto ha coniato una fattura", quante,
          len(INVOICES))

    # ---- 4. con la scelta l'ordine nasce, e la scelta e' nella nota -
    print("\n[con la scelta l'ordine nasce, e il venditore la legge]")
    r = chiama(SRV.compra, dict(base, scelte={
        "Palline Uhmami": "peperoncino", "Composta di Frutta": "Arancia"},
        nota_compratore="è un regalo"))
    nota = con.execute("SELECT nota_compratore FROM ordini WHERE id=?",
                       (r["ordine_id"],)).fetchone()[0]
    prova("la scelta e' nella nota, davanti a quel che ha scritto",
          "Palline Uhmami: peperoncino, Composta di Frutta: Arancia · "
          "è un regalo", nota)
    prova("...e nella risposta", nota, r.get("nota_compratore"))

    # ---- 5. il carrello, pezzo per pezzo ----------------------------
    print("\n[nel carrello: pezzo per pezzo, col titolo davanti]")
    carrello = {"righe": [{"annuncio_id": bid, "quantita": 1},
                          {"annuncio_id": semplice, "quantita": 1}],
                "consegna": "spedizione", "spedizione_via": "casa",
                "indirizzo": dict(CASA), "indirizzo_confermato": True}
    alza("senza la scelta della box il carrello non si paga",
         lambda: chiama(SRV.compra, dict(carrello)), "Palline Uhmami")
    r = chiama(SRV.compra, dict(carrello, scelte_righe={str(bid): {
        "Palline Uhmami": "curry - sesamo", "Composta di Frutta": "Pera"}}))
    nota = con.execute("SELECT nota_compratore FROM ordini WHERE id=?",
                       (r["ordine_id"],)).fetchone()[0]
    prova("la nota dice di quale pezzo e cosa",
          "«Box Natale La Sfiziosa (pre-ordine)» Palline Uhmami: curry - "
          "sesamo, Composta di Frutta: Pera", nota)

    # ---- 6. la regressione ------------------------------------------
    print("\n[la regressione: senza tendine si compra come ieri]")
    r = chiama(SRV.compra, {"annuncio_id": semplice, "quantita": 1,
                            "consegna": "spedizione",
                            "spedizione_via": "casa",
                            "indirizzo": dict(CASA),
                            "indirizzo_confermato": True})
    prova("l'ordine nasce, con la nota vuota", "", con.execute(
        "SELECT nota_compratore FROM ordini WHERE id=?",
        (r["ordine_id"],)).fetchone()[0])

    con.close()
    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
