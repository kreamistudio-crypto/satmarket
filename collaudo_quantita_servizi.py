"""LA QUANTITA' DEI SERVIZI — il giro vero (cantiere quantita-servizi,
set 2026).

`prove.py` difende i giudici estratti e le sentinelle sul sorgente.
Qui gira il SERVER VERO (`pubblica`, `modifica_annuncio`,
`ricarica_quantita`, `compra`, `preventivo_ordine`, `fai_offerta`) su
un database usa-e-getta, e si cammina:

  1. un servizio nasce con `quantita: 5` nel payload — il client mente
     o e' vecchio, non importa: la colonna in database resta al
     sentinel (MAX_QUANTITA_ANNUNCIO), MAI 5;
  2. `servizio_limite_ordine` si scrive com'e' dichiarato, e senza
     dichiararlo resta 0 (nessun limite);
  3. il preventivo e la compra, SENZA limite dichiarato: 3 unita' si
     comprano, il totale e' l'unitario per tre, la spedizione resta 0;
  4. CON un limite dichiarato: sotto il tetto passa, sopra il tetto un
     400 col numero giusto — preventivo e compra dicono lo stesso;
  5. `ricarica_quantita` su un servizio: 400, non tocca niente;
  6. `modifica_annuncio` cambia il limite e NON lo stock (che resta al
     sentinel anche se il client manda un altro numero);
  7. un'offerta con piu' pezzi di quelli permessi si LIMA al limite,
     mai un rifiuto;
  8. il riallineamento d'avvio: un servizio scritto DIRETTAMENTE nel
     database con `quantita=1` (il mondo di prima di questo cantiere)
     torna al sentinel al prossimo `init_db()`.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server (database usa-e-getta), la moderazione AI, le
notifiche e la invoice sono stub. Zero rete, zero chiavi, zero sats
veri — il vincolo del cantiere.

USO:  python collaudo_quantita_servizi.py
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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-qserv-"),
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
    # LA FOTO DI CARTONE (11 ott 2026, cantiere foto-obbligatorie):
    # senza almeno una foto un annuncio non si pubblica piu', e questo
    # collaudo non parla di foto. La rotta ne riceve una finta e
    # `salva_foto` risponde col nome, senza scrivere nessun file.
    server.salva_foto = lambda aid, foto, versione="": (
        [f"a{aid}_0.jpg"], [])

    async def ok_ai(*a, **k):
        return None

    async def zitta(*a, **k):
        return None

    async def invoice_finta(sats, memo, expiry=None, cassaforte=""):
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


def ricarica(aid, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.ricarica_quantita(aid, None))


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


def offerta(aid, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(SRV.fai_offerta(aid, None))


def main():
    print("=" * 58)
    print("  LA QUANTITA' DEI SERVIZI — il giro vero")
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
        return vero.execute(
            "SELECT quantita, quantita_max, servizio_limite_ordine, "
            "consegna, stato FROM annunci WHERE id=?", (aid,)).fetchone()

    SENTINEL = SRV.MAX_QUANTITA_ANNUNCIO
    chi({"id": 222, "nome": "Vende", "first_name": "Vende", "username": "vende"})
    base = {"titolo": "Consulenza 30 min", "descrizione": "call di mezz'ora",
            "prezzo_sats": 30000, "categoria": "Lezioni e corsi",
            "consegna": "servizio", "foto": ["foto-di-cartone"]}

    # --- 1-3: pubblica IGNORA lo stock del client, scrive il limite --
    r = pubblica({**base, "quantita": 5})
    a1 = r["id"]
    x = riga(a1)
    prova("pubblica: il client manda 5, il database resta al sentinel",
          SENTINEL, x["quantita"])
    prova("...e il massimo pure", SENTINEL, x["quantita_max"])
    prova("...nessun limite dichiarato: 0", 0, x["servizio_limite_ordine"])

    r = pubblica({**base, "titolo": "Consulenza (limitata)",
                  "servizio_limite_ordine": 3})
    a2 = r["id"]
    x = riga(a2)
    prova("pubblica: il limite dichiarato si scrive", 3,
          x["servizio_limite_ordine"])
    prova("...e lo stock resta comunque il sentinel", SENTINEL,
          x["quantita"])

    # --- 4-8: compra/preventivo SENZA limite: quantita' libera -------
    chi({"id": 111, "nome": "Compra", "first_name": "Compra",
         "username": "compra"})
    prv = preventivo({"annuncio_id": a1, "quantita": 3})
    prova("preventivo senza limite: 3 unita' passano", True, bool(prv))
    ordine = compra({"annuncio_id": a1, "quantita": 3})
    o = vero.execute("SELECT quantita, prezzo_sats, spedizione_sats "
                     "FROM ordini WHERE id=?",
                     (ordine["ordine_id"],)).fetchone()
    prova("compra: l'ordine porta 3 unita'", 3, o["quantita"])
    prova("...il totale e' l'unitario per tre", 30000 * 3, o["prezzo_sats"])
    prova("...nessuna spedizione su un servizio", 0, o["spedizione_sats"])
    # l'annuncio non si e' mosso: un servizio non "si esaurisce"
    x = riga(a1)
    prova("dopo la compra lo stock resta il sentinel (non e' stock "
          "vero)", True, x["quantita"] > SENTINEL - 100)
    prova("...e l'annuncio resta attivo, non 'venduto'", "attivo",
          x["stato"])

    # --- 9-12: compra/preventivo CON limite: sotto passa, sopra 400 --
    prv2 = preventivo({"annuncio_id": a2, "quantita": 3})
    prova("preventivo al limite esatto: passa", True, bool(prv2))
    alza("preventivo oltre il limite: 400 col numero giusto",
         lambda: preventivo({"annuncio_id": a2, "quantita": 4}),
         "massimo per ordine è 3")
    alza("compra oltre il limite: lo stesso 400",
         lambda: compra({"annuncio_id": a2, "quantita": 4}),
         "massimo per ordine è 3")
    ordine2 = compra({"annuncio_id": a2, "quantita": 3})
    prova("compra al limite esatto: passa davvero", True,
          bool(ordine2.get("ordine_id")))

    # --- 13-15: ricarica_quantita rigetta, modifica cambia il limite -
    # (un annuncio FRESCO: a1 ha un ordine 'creato' pendente dal passo
    # sopra, e modifica_annuncio rifiuta con un affare in corso — lo
    # stesso motivo per cui esiste "Aggiorna i pezzi" ad affare aperto,
    # che per un servizio non c'e' piu': vedi il rigetto qui sotto)
    chi({"id": 222, "nome": "Vende", "first_name": "Vende",
         "username": "vende"})
    alza("ricarica_quantita su un servizio: 400, niente scorte",
         lambda: ricarica(a1, {"quantita": 10}), "scorte")
    r = pubblica({**base, "titolo": "Consulenza (da modificare)"})
    a3 = r["id"]
    modifica(a3, {**base, "titolo": "Consulenza (da modificare)",
                  "servizio_limite_ordine": 7, "quantita": 2})
    x = riga(a3)
    prova("modifica: il limite si aggiorna", 7,
          x["servizio_limite_ordine"])
    prova("...ma lo stock IGNORA il 2 del client: resta il sentinel",
          SENTINEL, x["quantita"])

    # --- 16-17: l'offerta con piu' pezzi del limite si LIMA ----------
    chi({"id": 333, "nome": "Offre", "first_name": "Offre",
         "username": "offre"})
    off = offerta(a3, {"importo": 25000, "quantita": 50})
    riga_off = vero.execute("SELECT quantita FROM offerte WHERE id=?",
                            (off["offerta_id"],)).fetchone()
    prova("l'offerta di 50 su un limite di 7 si LIMA a 7", 7,
          riga_off["quantita"])

    # --- 18-20: il riallineamento d'avvio, sul database vero ---------
    vero.execute("INSERT INTO annunci(venditore_id,titolo,prezzo_sats,"
                "consegna,quantita,quantita_max,stato,creato) "
                "VALUES(222,'Vecchio servizio',20000,'servizio',1,1,"
                "'attivo',0)")
    vero.commit()
    a_vecchio = vero.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    prova("prima del riallineamento: e' bloccato a 1 pezzo", 1,
          riga(a_vecchio)["quantita"])
    SRV.init_db()
    x = riga(a_vecchio)
    prova("dopo init_db(): il servizio pre-cantiere sale al sentinel",
          SENTINEL, x["quantita"])
    prova("...e il massimo con lui", SENTINEL, x["quantita_max"])

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    sys.exit(1 if FALLITE else 0)


if __name__ == "__main__":
    main()
