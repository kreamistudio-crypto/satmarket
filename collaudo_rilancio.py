# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL RILANCIO: chi compra non paga la cifra che ha rifiutato.

`prove.py` difende la FORMA e monta le funzioni una per una; quello che
non puo' fare e' far girare la trattativa INTERA fino alla fattura.
Questo script chiude quel buco: fa partire il SERVER VERO su un
database usa-e-getta, con LNbits finto, e cammina il giro completo —
proposta, controproposta, rilancio, controproposta, rilancio,
accettazione, PAGAMENTO.

LA PROVA REGINA e' quella, e vale il cantiere: la bolt11 dev'essere
dell'importo del RILANCIO, non della controproposta che il compratore
aveva appena rifiutato. Quel guasto NON FALLISCE DA SOLO — preventivo e
invoice leggono la STESSA funzione (`_importo_accordo`) e
concorderebbero fra loro, quindi il patto «preventivo == compra al sat»
qui e' cieco. L'unico testimone sarebbe una notifica Telegram.

Accanto, le altre domande che si fanno insieme a quella:
  · la FORBICE si stringe da tutt'e due i lati, e non si apre mai;
  · il tetto dei giri chiude la partita;
  · il rilancio NON consuma i tentativi per annuncio (non fa INSERT);
  · la REGRESSIONE: una trattativa senza rilanci si comporta come
    ieri, byte per byte.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. LNbits non
viene mai chiamato — le invoice si contano, non si chiedono — quindi
gira anche senza rete e senza chiavi.

USO:  python collaudo_rilancio.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
INVOICES = []       # le cifre che la bolt11 finta ha chiesto
DETTI = []          # le notifiche partite, per leggerne le cifre

COMPRA = {"id": 111, "nome": "Compra", "username": "compra", "admin": False}
VENDE = {"id": 222, "nome": "Vende", "username": "vende", "admin": False}
CHI = {"ora": COMPRA}


def prova(nome, atteso, avuto):
    global PASSATE, FALLITE
    if atteso == avuto:
        PASSATE += 1
        print("  OK  " + nome)
    else:
        FALLITE += 1
        print("  NO  " + nome +
              "\n      atteso: " + repr(atteso) +
              "\n      avuto:  " + repr(avuto))


def avvio():
    global SRV
    if "server" in sys.modules:
        raise SystemExit("Attenzione: server e' gia' importato; questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-rilancio-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "INCOLLA_QUI"
    cfg.LNBITS_URL = "http://127.0.0.1:1"
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME con un valore non vuoto, e lascia
    # passare solo cio' che contiene INCOLLA_QUI. Qui il valore non
    # serve a niente (LNbits non si chiama mai), quindi si usa la
    # convenzione di casa invece di allargare lo scanner.
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
        """LNbits non si chiama mai: la cifra si annota e basta. E' lei
        che poi si confronta con `prezzo_sats`."""
        INVOICES.append(int(sats))
        return {"payment_hash": "hash" + str(len(INVOICES)),
                "payment_request": "lnbc" + str(sats) + "collaudo"}

    async def notifica_finta(tg_id, testo, **k):
        DETTI.append((tg_id, testo))

    server.crea_invoice_escrow = invoice_finta
    server.notifica = notifica_finta
    server.polso_ordini_admin = lambda *a, **k: None
    server.verifica_utente = lambda *a, **k: CHI["ora"]
    return db


def chiama(fn, corpo=None, *primi):
    """Gli endpoint leggono il body da leggi_json e l'utente da
    verifica_utente: si sostituiscono tutti e due e si chiamano
    davvero, invece di rifare a mano quello che fanno. La Request e'
    None: nessuno la tocca, il body arriva da leggi_json."""
    async def leggi(_req):
        return corpo or {}
    SRV.leggi_json = leggi
    return asyncio.run(fn(*(primi + (None,))))


def semina():
    """Il venditore e il compratore, e nient'altro: gli annunci li fa
    `annuncio()` uno per trattativa, cosi' ogni caso parte pulito."""
    con = SRV.db()
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(222,'Vende','neg22222',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,registrato)"
                " VALUES(111,'Compra','neg11111',1)")
    con.commit()
    con.close()


def annuncio(titolo, prezzo=100000):
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(222,?,'desc',?,'Altro','Torino (TO)','attivo',1,"
        "'ritiro',5,'sats','buono')", (titolo, prezzo))
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def offerta(aid, sats):
    CHI["ora"] = COMPRA
    return chiama(SRV.fai_offerta, {"importo": str(sats)}, aid)


# LA CIFRA DEL RIFIUTO SI LEGGE COL `str()`, ed e' la riga che
# rende questo file capace di fallire: quando una guardia cade,
# `rispondi` torna il DICT della risposta invece della stringa
# dell'errore — e un `esito.startswith` su un dict ESPLODE, cioe' il
# collaudo muore col traceback invece di stampare un NO. Lo dice la
# tortura: due mutazioni (il tetto tolto, il venditore che risale)
# sopravvivevano cosi', non perche' il caso non fosse coperto ma
# perche' la prova non arrivava a parlare.
def rispondi(oid, chi, azione, importo=None):
    CHI["ora"] = chi
    DETTI.clear()
    corpo = {"azione": azione}
    if importo is not None:
        corpo["importo"] = str(importo)
    try:
        return chiama(SRV.rispondi_offerta, corpo, oid)
    except Exception as e:
        return str(getattr(e, "status_code", "?")) + " " + \
            str(getattr(e, "detail", e))


def riga(oid):
    con = SRV.db()
    r = con.execute("SELECT * FROM offerte WHERE id=?", (oid,)).fetchone()
    con.close()
    return r


def main():
    db = avvio()
    print("Database usa-e-getta: " + db)
    semina()

    # ----------------------------------------------------------------
    print("")
    print("[il giro completo: due rilanci, e la forbice che si stringe]")
    aid = annuncio("Miele di castagno")
    oid = offerta(aid, 70000)["offerta_id"]
    r = riga(oid)
    prova("la proposta parte a 70.000, zero giri",
          ("proposta", 70000, 0), (r["stato"], r["importo_sats"], r["giri"]))

    rispondi(oid, VENDE, "contro", 90000)
    prova("il venditore chiede 90.000", ("controproposta", 90000),
          (riga(oid)["stato"], riga(oid)["contro_sats"]))

    rispondi(oid, COMPRA, "rilancia", 75000)
    r = riga(oid)
    prova("il compratore rilancia a 75.000, e il turno torna a chi vende",
          ("proposta", 75000, 1), (r["stato"], r["importo_sats"], r["giri"]))
    prova("...e il SOFFITTO resta in colonna per il giro dopo",
          90000, r["contro_sats"])
    prova("...e chi vende lo sente, con tutt'e due le cifre", True,
          len(DETTI) == 1 and DETTI[0][0] == 222
          and "75.000" in DETTI[0][1] and "90.000" in DETTI[0][1])

    esito = rispondi(oid, VENDE, "contro", 95000)
    prova("chi vende NON puo' risalire sopra la sua richiesta di prima",
          True, str(esito).startswith("400 La tua richiesta di prima"))
    prova("...e il rifiuto non ha mosso niente",
          90000, riga(oid)["contro_sats"])

    rispondi(oid, VENDE, "contro", 85000)
    prova("...ma puo' scendere: la forbice si stringe",
          ("controproposta", 85000),
          (riga(oid)["stato"], riga(oid)["contro_sats"]))

    esito = rispondi(oid, COMPRA, "rilancia", 70000)
    prova("non si rilancia sotto la propria offerta di prima",
          True, str(esito).startswith("400"))
    esito = rispondi(oid, COMPRA, "rilancia", 85000)
    prova("...ne' fino alla richiesta del venditore: li' si accetta",
          True, str(esito).startswith("400"))

    rispondi(oid, COMPRA, "rilancia", 80000)
    prova("secondo rilancio: 80.000, e i giri sono due",
          (80000, 2), (riga(oid)["importo_sats"], riga(oid)["giri"]))

    rispondi(oid, VENDE, "contro", 84000)
    esito = rispondi(oid, COMPRA, "rilancia", 82000)
    prova("al terzo rilancio il tetto chiude la partita",
          True, str(esito).startswith("400 Hai gi"))
    prova("...e la trattativa non si e' mossa",
          ("controproposta", 2, 80000),
          (riga(oid)["stato"], riga(oid)["giri"], riga(oid)["importo_sats"]))

    print("")
    print("[il rilancio non consuma i tentativi per annuncio]")
    con = SRV.db()
    quante = con.execute("SELECT COUNT(*) n FROM offerte WHERE annuncio_id=? "
                         "AND compratore_id=111", (aid,)).fetchone()["n"]
    con.close()
    prova("dopo due rilanci la riga e' sempre UNA", 1, quante)

    # ----------------------------------------------------------------
    print("")
    print("[LA PROVA REGINA: si paga il rilancio, non la cifra rifiutata]")
    aid2 = annuncio("Cera d'api")
    oid2 = offerta(aid2, 60000)["offerta_id"]
    rispondi(oid2, VENDE, "contro", 90000)
    rispondi(oid2, COMPRA, "rilancia", 70000)
    rispondi(oid2, VENDE, "accetta")
    r = riga(oid2)
    prova("il venditore accetta il rilancio", "accettata", r["stato"])
    prova("...e il CONSOLIDAMENTO spegne la richiesta vecchia",
          0, r["contro_sats"])
    prova("L'ACCORDO E' IL RILANCIO (70.000), non i 90.000 rifiutati",
          (70000, 0), SRV._importo_accordo(r))

    INVOICES.clear()
    CHI["ora"] = COMPRA
    ordine = chiama(SRV.compra, {"annuncio_id": aid2, "consegna": "ritiro",
                                 "quantita": 1, "offerta_id": oid2})
    con = SRV.db()
    ord_riga = con.execute("SELECT * FROM ordini WHERE id=?",
                           (ordine["ordine_id"],)).fetchone()
    con.close()
    prova("la BOLT11 chiede il rilancio, al sat", [70000], INVOICES)
    prova("...e in colonna finisce la stessa cifra",
          70000, ord_riga["prezzo_sats"])

    # ----------------------------------------------------------------
    print("")
    print("[la regressione: senza rilanci e' il mondo di ieri]")
    aid3 = annuncio("Propoli")
    oid3 = offerta(aid3, 60000)["offerta_id"]
    rispondi(oid3, VENDE, "contro", 80000)
    rispondi(oid3, COMPRA, "accetta")
    r = riga(oid3)
    prova("accettando la controproposta l'accordo resta la SUA cifra",
          (80000, 0), SRV._importo_accordo(r))
    prova("...e il consolidamento non l'ha toccata",
          80000, r["contro_sats"])
    INVOICES.clear()
    CHI["ora"] = COMPRA
    chiama(SRV.compra, {"annuncio_id": aid3, "consegna": "ritiro",
                        "quantita": 1, "offerta_id": oid3})
    prova("...e la fattura chiede quella, com'e' sempre stato",
          [80000], INVOICES)

    # ----------------------------------------------------------------
    print("")
    print("[la ronda del libro mastro deve TACERE]")
    con = SRV.db()
    trovati = []
    for nome, _perche, sql in SRV.CONTROLLI_LIBRO_MASTRO:
        try:
            righe = con.execute(sql).fetchall()
        except Exception as e:
            trovati.append(nome + ": ESPLOSA (" + str(e) + ")")
            continue
        if righe:
            trovati.append(nome + ": " + str([x[0] for x in righe]))
    con.close()
    prova("nessun controllo trova niente su partite sane", [], trovati)

    print("")
    print("  " + str(PASSATE) + " passate, " + str(FALLITE) + " fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
