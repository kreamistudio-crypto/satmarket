# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE RETI: chi spedisce dichiara, chi compra sceglie
(ago 2026).

`prove.py` difende la FORMA — che il giudice sia puro, che le due
colonne si scrivano insieme, che una guardia non sparisca in un
riordino. Quello che non puo' fare e' far girare la cosa VERA: le sue
prove non hanno un database, non hanno un endpoint e non coniano una
invoice.

Questo script chiude quel buco, ed e' il calco di `collaudo_conto.py`.
Le domande a cui risponde sono quattro, e sono quelle su cui il
cantiere si regge:

  · il BACKFILL: chi aveva dichiarato UNA rete la ritrova dentro la
    colonna nuova — se sbagliasse, sedici venditori veri perderebbero
    la mappa il giorno del deploy, in silenzio;
  · le DUE COLONNE si scrivono insieme e non possono divergere;
  · la RETE SCELTA e' validata contro le reti di QUEL venditore: chi
    ne dichiara due non puo' ricevere un ordine per una terza —
    sarebbe esattamente il caso che il cantiere esiste per chiudere;
  · il MONDO DI IERI e' intatto: venditore con una rete sola, o senza
    nessuna, si comporta come prima byte per byte.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
lo script gira anche senza rete e senza chiavi.

USO:  python collaudo_reti.py
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
INVOICES = []

CAMBIO = 100_000.0
UTENTE = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}


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
    """Come `prova`, ma per i rifiuti: chiede che alzi 400 e che il
    messaggio dica la cosa giusta. Il messaggio conta quanto il
    codice — «scegli il corriere» e «quel corriere non ce l'ha» sono
    due problemi diversi per chi legge."""
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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-reti-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME e lascia passare solo INCOLLA_QUI
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

    async def invoice_finta(sats, memo, expiry=None):
        INVOICES.append(int(sats))
        return {"payment_hash": f"hash{len(INVOICES)}",
                "payment_request": f"lnbc{sats}collaudo{len(INVOICES)}"}

    async def cambio_finto():
        return CAMBIO

    server.crea_invoice_escrow = invoice_finta
    server.cambio_btc_eur = cambio_finto
    server.notifica = lambda *a, **k: None
    server.polso_ordini_admin = lambda *a, **k: None
    server.verifica_utente = lambda *a, **k: UTENTE
    return db


def chiama(fn, corpo):
    async def leggi(_req):
        return corpo
    SRV.leggi_json = leggi
    return asyncio.run(fn(None))


def semina(reti_venditore_txt, prezzo=30_000):
    """Un venditore con le sue reti e un annuncio che si spedisce."""
    con = SRV.db()
    for t in ("ordine_righe", "ordini", "annunci"):
        con.execute(f"DELETE FROM {t}")
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato,"
        "spedizionieri,spedizioniere) VALUES(222,'Vende','neg22222',1,?,?)",
        (reti_venditore_txt,
         [s for s in reti_venditore_txt.split("|") if s][0]
         if reti_venditore_txt else ""))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "spedizione_sats) VALUES(222,'Cosa','desc',?,'Altro',"
        "'Torino (TO)','attivo',1,'spedizione',5,'sats','buono',1000)",
        (prezzo,))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def compra(aid, corpo_extra):
    corpo = {"annuncio_id": aid, "quantita": 1,
             "consegna": "spedizione", "spedizione_via": "punto"}
    corpo.update(corpo_extra)
    return chiama(SRV.compra, corpo)


def riga_ordine(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM ordini WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


# ---------------------------------------------------------------
def prove_backfill():
    print("\n── IL BACKFILL: chi aveva una rete la ritrova ──")
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,spedizioniere,spedizionieri) "
                "VALUES(777,'Vecchio','neg77777',1,'InPost','')")
    # e uno che una rete non l'ha mai dichiarata: non deve nascere
    # dal nulla una '||' , che sarebbe «dichiarato niente»
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato,spedizioniere,spedizionieri) "
                "VALUES(778,'Mai','neg77778',1,'','')")
    con.commit()
    SRV.riallinea_spedizionieri(con)
    con.commit()
    r = con.execute("SELECT spedizionieri FROM utenti "
                    "WHERE tg_id=777").fetchone()
    prova("la rete di ieri finisce nella colonna nuova, coi pipe",
          "|InPost|", r["spedizionieri"])
    r2 = con.execute("SELECT spedizionieri FROM utenti "
                     "WHERE tg_id=778").fetchone()
    prova("chi non aveva niente resta senza (mai un '||' dal nulla)",
          "", r2["spedizionieri"])
    prova("...e il giudice la legge come una rete sola",
          ["InPost"], SRV.reti_venditore(r["spedizionieri"], ""))

    # IDEMPOTENZA, e non e' una formalita': il backfill gira a OGNI
    # avvio, quindi un secondo giro non deve poter ricoprire una
    # scelta multipla fatta nel frattempo
    con.execute("UPDATE utenti SET spedizionieri='|InPost|Poste Italiane|' "
                "WHERE tg_id=777")
    con.commit()
    SRV.riallinea_spedizionieri(con)
    con.commit()
    r3 = con.execute("SELECT spedizionieri FROM utenti "
                     "WHERE tg_id=777").fetchone()
    prova("un secondo giro NON ricopre la scelta multipla",
          "|InPost|Poste Italiane|", r3["spedizionieri"])
    con.close()


def prove_endpoint():
    print("\n── IL CASSETTO: le due colonne si scrivono INSIEME ──")
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(222,'Vende','neg22222',1)")
    con.commit()
    con.close()
    UTENTE["id"] = 222
    chiama(SRV.scegli_spedizioniere,
           {"spedizionieri": ["Poste Italiane", "InPost"]})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("le reti vanno in colonna NELL'ORDINE DEL CATALOGO",
          "|InPost|Poste Italiane|", r["spedizionieri"])
    prova("...e la singolare tiene la PRIMA voce (per il client vecchio)",
          "InPost", r["spedizioniere"])

    chiama(SRV.scegli_spedizioniere,
           {"spedizionieri": ["InPost", "InPost", "Poste Italiane"]})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("i doppioni si buttano", "|InPost|Poste Italiane|",
          r["spedizionieri"])

    alza("una rete fuori catalogo si rifiuta",
         lambda: chiama(SRV.scegli_spedizioniere,
                        {"spedizionieri": ["Bartolini"]}),
         "sconosciuta")
    alza("e un formato che non e' una lista pure",
         lambda: chiama(SRV.scegli_spedizioniere,
                        {"spedizionieri": "InPost"}),
         "formato")

    # IL CLIENT DI IERI: manda la chiave vecchia, una stringa sola.
    # Deve continuare a funzionare — porta lo stesso significato.
    chiama(SRV.scegli_spedizioniere, {"spedizioniere": "Poste Italiane"})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("il client di IERI (chiave singolare) scrive ancora",
          ("|Poste Italiane|", "Poste Italiane"),
          (r["spedizionieri"], r["spedizioniere"]))

    chiama(SRV.scegli_spedizioniere, {"spedizionieri": []})
    con = SRV.db()
    r = con.execute("SELECT spedizionieri, spedizioniere FROM utenti "
                    "WHERE tg_id=222").fetchone()
    con.close()
    prova("lo spegnimento azzera TUTTE E DUE le colonne",
          ("", ""), (r["spedizionieri"], r["spedizioniere"]))
    UTENTE["id"] = 111


def prove_scelta():
    print("\n── LA RETE LA SCEGLIE CHI COMPRA ──")

    # --- DUE reti: il compratore deve dirlo -----------------------
    aid = semina("|InPost|Poste Italiane|")
    alza("due reti, nessuna scelta: si rifiuta e si dice quali",
         lambda: compra(aid, {"punto_ritiro": "Via Roma 1"}),
         "scegli con quale corriere")
    alza("...e una rete che il venditore NON ha si rifiuta",
         lambda: compra(aid, {"punto_ritiro": "Via Roma 1",
                              "rete_punto": "Altro"}),
         "non spedisce con quel corriere")
    r = compra(aid, {"punto_ritiro": "Via Roma 1",
                     "rete_punto": "Poste Italiane"})
    prova("la rete scelta torna nella risposta",
          "Poste Italiane", r.get("rete_punto"))
    riga = riga_ordine(r["ordine_id"])
    prova("...e finisce in colonna",
          "Poste Italiane", riga["rete_punto"])
    prova("...senza toccare consegna_scelta, che resta 'spedizione'",
          ("spedizione", 1),
          (riga["consegna_scelta"], riga["via_punto"]))

    # --- UNA rete: si fissa alla nascita, senza chiedere ----------
    aid = semina("|InPost|")
    r = compra(aid, {"punto_ritiro": "Locker A"})
    prova("una rete sola: si fissa alla nascita, il client non la manda",
          "InPost", riga_ordine(r["ordine_id"])["rete_punto"])

    # --- ZERO reti: il mondo di ieri, byte per byte ---------------
    aid = semina("")
    r = compra(aid, {"punto_ritiro": "Un punto qualunque"})
    riga = riga_ordine(r["ordine_id"])
    prova("nessuna rete dichiarata: la colonna resta vuota",
          "", riga["rete_punto"])
    prova("...e il punto si scrive lo stesso (via punto sempre offerta)",
          ("Un punto qualunque", 1),
          (riga["punto_ritiro"], riga["via_punto"]))
    # e senza reti il punto NON e' obbligatorio: e' il patto del
    # quarto giro, il residuo lo copre il campo dentro l'ordine
    aid = semina("")
    r = compra(aid, {})
    prova("...e senza reti il punto puo' arrivare dopo (400 solo con rete)",
          "", riga_ordine(r["ordine_id"])["punto_ritiro"])

    # --- la via CASA non si porta dietro nessuna rete -------------
    aid = semina("|InPost|Poste Italiane|")
    r = chiama(SRV.compra, {"annuncio_id": aid, "quantita": 1,
                            "consegna": "spedizione",
                            "spedizione_via": "casa",
                            "indirizzo": {"nome": "Mario Rossi",
                                          "via": "Via Roma 1",
                                          "cap": "10100",
                                          "citta": "Torino",
                                          "provincia": "TO",
                                          "telefono": "3330000000"}})
    riga = riga_ordine(r["ordine_id"])
    prova("la via CASA non scrive nessuna rete",
          ("", 0), (riga["rete_punto"], riga["via_punto"]))


def prove_libro_mastro():
    print("\n── LA RONDA DEVE TACERE ──")
    guasti = []
    con = SRV.db()
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        righe = con.execute(sql).fetchall()
        if righe:
            guasti.append((nome, [dict(r) for r in righe]))
    con.close()
    prova("nessun controllo del libro mastro ha qualcosa da dire",
          [], guasti)


def main():
    db = avvio()
    print("=" * 66)
    print("COLLAUDO DELLE RETI — database usa-e-getta, LNbits finto")
    print("=" * 66)
    prove_backfill()
    prove_endpoint()
    prove_scelta()
    prove_libro_mastro()
    print("\n" + "=" * 66)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    try:
        os.remove(db)
    except OSError:
        pass
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
