"""IL DOVE DEL SERVIZIO — il giro vero (ago 2026).

Tre cose dal campo, e una quarta trovata costruendo:
1) le pillole «online / di persona» non si illuminavano (classe `on`
   invece di `attiva`: quella la sorveglia prove.py, qui no);
2) la ZONA non e' piu' obbligatoria «di persona»: un servizio a
   domicilio si fa a casa del cliente, e il venditore non sa dove;
3) il DOVE e' FACOLTATIVO, terzo stato '' = «Su appuntamento»;
4) `servizio_dove` e `durata_min` NON SI SCRIVEVANO — il giudice
   calcolava il dove per la sola guardia della zona e lo buttava, e
   INSERT e UPDATE non nominavano le colonne: la scheda leggeva il
   DEFAULT per sempre. Le sentinelle dicono che adesso le colonne
   stanno nelle query; QUI si pubblica per davvero e si RILEGGE dal
   database, che e' l'unica cosa che dimostra che il valore arriva.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (database usa-e-getta), la moderazione AI e le
notifiche sono stub. Zero rete, zero chiavi.
"""
import asyncio
import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print(f"  ✓ {nome}")
    else:
        FALLITE += 1
        print(f"  ✗ {nome}\n      atteso: {atteso!r}\n      avuto:  {avuto!r}")


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-dove-"),
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
    cfg.SERVIZI_ATTIVI = True          # il cantiere vive dietro la leva
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server

    async def ok_ai(*a, **k):
        return None

    async def zitta(*a, **k):
        return None

    async def invoice_finta(sats, memo, expiry=None):
        return {"payment_hash": "hashcollaudo",
                "payment_request": f"lnbc{sats}collaudo"}

    async def cambio_finto():
        return 100_000.0

    server.moderazione_ai = ok_ai
    server.notifica = zitta
    server.crea_invoice_escrow = invoice_finta
    server.invoice_pagata = lambda *a, **k: False
    server.cambio_btc_eur = cambio_finto
    server.polso_ordini_admin = lambda *a, **k: None
    server.avvisa_admin_annuncio = zitta if hasattr(server, "avvisa_admin_annuncio") else None
    return db


def chi(u):
    SRV.verifica_utente = lambda *a, **k: u


def pubblica(corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.pubblica(None))


def modifica(aid, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.modifica_annuncio(aid, None))


def compra(corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.compra(None))


def preventivo(corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.preventivo_ordine(None))


def main():
    print("=" * 58)
    print("  IL DOVE DEL SERVIZIO — il giro vero")
    print("=" * 58)
    db = avvio()
    con = sqlite3.connect(db)
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio) "
                "VALUES(222,'Vende','vende','negozio22')")
    con.commit()
    con.close()
    vero = sqlite3.connect(db)
    vero.row_factory = sqlite3.Row

    def riga(aid):
        return vero.execute("SELECT servizio_dove, durata_min, zona, consegna "
                            "FROM annunci WHERE id=?", (aid,)).fetchone()

    chi({"id": 222, "nome": "Vende", "first_name": "Vende", "username": "vende"})
    base = {"titolo": "Lezione di inglese", "descrizione": "un'ora",
            "prezzo_sats": 50000, "categoria": "Lezioni e corsi",
            "consegna": "servizio", "foto": []}

    # --- 2) di persona SENZA zona: passa
    r = pubblica({**base, "servizio_dove": "presenza", "durata_min": 60,
                  "zona": ""})
    a1 = r["id"]
    prova("di persona senza zona: l'annuncio nasce", True, bool(a1))
    # --- 4) e le due colonne sono SCRITTE
    x = riga(a1)
    prova("...con servizio_dove='presenza' in colonna", "presenza",
          x["servizio_dove"])
    prova("...e durata_min=60 in colonna", 60, x["durata_min"])
    prova("...sulla strada 'servizio'", "servizio", x["consegna"])

    # --- 3) il terzo stato: non dichiarato resta ''
    r = pubblica({**base, "titolo": "Consulenza", "durata_min": 30})
    a2 = r["id"]
    x = riga(a2)
    prova("non dichiarato: '' in colonna (terzo stato)", "", x["servizio_dove"])
    prova("...e la durata arriva lo stesso", 30, x["durata_min"])

    # --- online
    r = pubblica({**base, "titolo": "Conversazione", "servizio_dove": "online",
                  "durata_min": "45"})
    a3 = r["id"]
    prova("online si scrive (anche se arriva come stringa)",
          ("online", 45), (riga(a3)["servizio_dove"], riga(a3)["durata_min"]))

    # --- la zona STORTA blocca ancora, come per tutti
    if SRV.COMUNI:
        alza("zona storta: la seconda regola resta accesa",
             lambda: pubblica({**base, "titolo": "Ripetizioni",
                               "servizio_dove": "presenza", "zona": "Pvia"}),
             "comune")
    else:
        print("  (dataset comuni assente: la zona storta non si prova)")

    # --- la modifica RISCRIVE le colonne
    modifica(a1, {**base, "titolo": "Lezione di inglese",
                  "servizio_dove": "online", "durata_min": 90})
    x = riga(a1)
    prova("modifica: il dove cambia", "online", x["servizio_dove"])
    prova("...e la durata pure", 90, x["durata_min"])
    # ...e se la strada cambia, il dove si azzera (la forma di anche_digitale)
    modifica(a1, {**base, "titolo": "Lezione di inglese", "consegna": "ritiro",
                  "zona": "Pavia (PV)", "condizione": "buono",
                  "servizio_dove": "online", "durata_min": 90})
    x = riga(a1)
    prova("cambiata strada: dove e durata si azzerano", ("", 0),
          (x["servizio_dove"], x["durata_min"]))

    # --- LA STRADA ESISTE (ago 2026, con la leva gia' accesa in
    # produzione): `strade_annuncio` non conosceva 'servizio', quindi
    # l'ordine nasceva su '' — senza appuntamento, senza solleciti, e
    # segna_spedito lo accettava. Qui il giro VERO: preventivo e compra.
    chi({"id": 111, "nome": "Compra", "first_name": "Compra",
         "username": "compra"})
    prv = preventivo({"annuncio_id": a3, "quantita": 1})
    vie = [v["via"] for v in prv["strade"]]
    prova("il preventivo enumera la via 'servizio'", ["servizio"], vie)
    ordine = compra({"annuncio_id": a3, "quantita": 1})
    o = vero.execute("SELECT consegna_scelta, spedizione_sats FROM ordini "
                     "WHERE id=?", (ordine["ordine_id"],)).fetchone()
    prova("compra senza scelta: l'ordine nasce su 'servizio'", "servizio",
          o["consegna_scelta"])
    prova("...senza spedizione", 0, o["spedizione_sats"])
    alza("una via che non offre: 400",
         lambda: compra({"annuncio_id": a3, "quantita": 1,
                         "consegna": "spedizione"}), "modalit")
    alza("il carrello la rifiuta, col suo messaggio",
         lambda: compra({"righe": [{"annuncio_id": a3, "quantita": 1},
                                   {"annuncio_id": a2, "quantita": 1}]}),
         "prestazione")
    chi({"id": 222, "nome": "Vende", "first_name": "Vende",
         "username": "vende"})

    # --- la vetrina li porta (CAMPI_VETRINA)
    v = asyncio.run(SRV.annuncio_singolo(a3)) if hasattr(SRV, "annuncio_singolo") else None
    if v is not None:
        prova("la vetrina porta il dove", "online", v.get("servizio_dove"))

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
