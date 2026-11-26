# -*- coding: utf-8 -*-
"""
IL COLLAUDO DI «ALTRI OGGETTI DEL VENDITORE» A SCORRIMENTO CONTINUO
(ago 2026).

`prove.py` difende la FORMA — che la sentinella stia fuori da
#detailContent, che il giro si alzi prima della guardia `mio`, che
nessuno scriva in `vetrina`. Quello che non puo' fare e' far girare la
ROTTA vera: le sue prove non hanno un database e non hanno un endpoint.

Qui il server VERO gira su un database usa-e-getta e si chiede la sola
cosa che conta: **scorrendo si vede tutto il negozio, una volta sola e
nell'ordine giusto**. Un difetto di paginazione non fallisce da solo —
non alza eccezioni e non scrive log: fa sparire delle card, o le fa
comparire due volte, e se ne accorge solo chi conta.

Le domande, in ordine di gravita':
  · l'UNIONE delle pagine e' ESATTAMENTE il negozio: nessun annuncio
    perso, nessuno doppio, nell'ordine di sempre (creato DESC, id DESC);
  · l'ultima pagina chiude il cursore, e chi insiste non gira a vuoto;
  · col cursore le due liste TACCIONO — ma le chiavi restano, vuote e
    mai assenti (un client in cache che scriva `d.feedback.length` non
    deve esplodere);
  · la prima pagina e il ramo LEGACY (senza limit) rispondono come
    ieri, byte per byte nelle chiavi che contano: e' la regressione
    della pagina negozio, che passa dalla stessa rotta;
  · un venduto non entra MAI fra gli `annunci`, e resta nel suo
    scaffale.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete, nessuna chiave: LNbits e Anthropic non si chiamano mai.

USO:  python collaudo_altri_oggetti.py
"""

import os
import sqlite3
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None          # il modulo server, importato in avvio()

ATTIVI = 27         # quanti annunci ha il venditore in vetrina
VENDUTI = 3         # ...e quanti sullo scaffale vuoto
PAGINA = 12         # la pagina del server di prova: 27 = 12 + 12 + 3 (il client dal 26 nov 2026 chiede una pagina sola da 10: la rotta resta a cursore)


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
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa."""
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
    # i segnaposto del config d'esempio: lo scanner dei segreti in CI
    # cerca queste chiavi per NOME con un valore non vuoto, e lascia
    # passare solo cio' che contiene INCOLLA_QUI (vedi collaudo_conto)
    cfg.LNBITS_INVOICE_KEY = "INCOLLA_QUI"
    cfg.LNBITS_ADMIN_KEY = "INCOLLA_QUI"
    cfg.ADMIN_IDS = [999]
    cfg.MODALITA_COLLAUDO = True
    cfg.COMMISSIONE_PERCENTO = 0
    cfg.ORE_CONFERMA = 72
    cfg.GIORNI_AUTO_SBLOCCO = 10
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    return db


def semina():
    """Un venditore con la sua bottega: ATTIVI annunci in vetrina,
    VENDUTI sullo scaffale, e un feedback ricevuto. I `creato`
    crescono, cosi' l'ordine `creato DESC, id DESC` e' deterministico e
    l'atteso si puo' scrivere a mano invece di ricopiare la query."""
    con = SRV.db()
    for t in ("annunci", "feedback"):
        con.execute(f"DELETE FROM {t}")
    con.execute(
        "INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
        "registrato) VALUES(222,'La Bottega','labottega','neg22222',1)")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "registrato) VALUES(111,'Compra','neg11111',1)")
    attivi = []
    for n in range(ATTIVI):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'desc',1000,'Altro','Torino (TO)','attivo',?,"
            "'ritiro',1,'sats','buono')", (f"Cosa {n}", 100 + n))
        attivi.append(cur.lastrowid)
    for n in range(VENDUTI):
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
            " VALUES(222,?,'desc',1000,'Altro','Torino (TO)','venduto',?,"
            "'ritiro',0,'sats','buono')", (f"Finito {n}", 50 + n))
    con.execute("INSERT INTO feedback(ordine_id,da_tg_id,per_tg_id,voto,"
                "commento,creato) VALUES(1,111,222,5,'tutto bene',1)")
    con.commit()
    con.close()
    # l'ordine atteso: creato DESC, id DESC — cioe' l'ultimo seminato
    # per primo. Scritto a mano APPOSTA: ricopiare la query qui dentro
    # vorrebbe dire provare la query con se' stessa.
    return list(reversed(attivi))


def chiedi(chi="labottega", limit=0, cursore=""):
    """La rotta vera, chiamata come la chiamerebbe FastAPI."""
    return SRV.negozio(chi=chi, limit=limit, cursore=cursore,
                       x_tg_init_data="", barattolo_sessione="")


def ids(risposta):
    return [a["id"] for a in risposta["annunci"]]


def scorri_tutto(limit=PAGINA):
    """Scorre il negozio pagina per pagina, e torna (righe, giri,
    cursore finale).
    IL TETTO AI GIRI C'E' APPOSTA, ed e' in UN POSTO SOLO: il difetto
    di paginazione piu' tipico e' il cursore che non avanza, e con un
    `while True` nudo questa prova non fallirebbe — si PIANTEREBBE, che
    e' peggio: una prova che non finisce non dice niente e blocca la
    CI. (Successo davvero, torturando: il primo giro di questo file
    aveva due cicli e il tetto su uno solo.)"""
    righe, cursore, giri = [], "", 0
    while True:
        d = chiedi(limit=limit, cursore=cursore)
        giri += 1
        righe += d["annunci"]
        cursore = d.get("cursore")
        if not cursore or giri > 20:
            break
    return righe, giri, cursore


# ====================================================================
def prove_scorsa_intera(atteso):
    """LA PROVA REGINA: l'unione delle pagine e' esattamente il
    negozio. Nessun annuncio perso (il difetto che non si vede),
    nessuno doppio (quello che si vede e sembra un altro bug),
    nell'ordine di sempre."""
    print("\n[1] TUTTO IL NEGOZIO, UNA VOLTA SOLA")
    righe, giri, cursore = scorri_tutto()
    visti = [a["id"] for a in righe]
    prova("l'unione delle pagine E' il negozio, nell'ordine di sempre",
          atteso, visti)
    prova("...senza doppioni", len(set(visti)), len(visti))
    prova("...in tre pagine da 12, 12 e 3", 3, giri)
    prova("l'ultima pagina chiude il cursore", None, cursore)
    # e chi insiste dopo la fine non gira a vuoto: senza cursore si
    # torna alla prima pagina, che e' il patto del cursore storto
    prova("il totale lo dice solo la prima pagina", ATTIVI,
          chiedi(limit=PAGINA)["totale"])
    prova("...e le pagine dopo non lo ripetono", None,
          chiedi(limit=PAGINA, cursore=chiedi(limit=PAGINA)["cursore"]
                 ).get("totale"))


def prove_liste_tacciono():
    """COL CURSORE LE DUE LISTE TACCIONO, ma le chiavi restano."""
    print("\n[2] ESAURITI E FEEDBACK: VUOTI COL CURSORE, MAI ASSENTI")
    prima = chiedi(limit=PAGINA)
    prova("prima pagina: lo scaffale vuoto c'e'", VENDUTI,
          len(prima["esauriti"]))
    prova("prima pagina: i feedback ci sono", 1, len(prima["feedback"]))
    dopo = chiedi(limit=PAGINA, cursore=prima["cursore"])
    prova("pagina 2: gli esauriti tacciono", [], dopo["esauriti"])
    prova("pagina 2: i feedback tacciono", [], dopo["feedback"])
    prova("...ma LE CHIAVI CI SONO ANCORA (client in cache)", True,
          "esauriti" in dopo and "feedback" in dopo)
    prova("pagina 2: gli annunci invece ci sono", PAGINA,
          len(dopo["annunci"]))
    prova("pagina 2: il venditore resta pieno (serve a risolvere chi)",
          "La Bottega", dopo["venditore"]["nome"])


def prove_regressione(atteso):
    """La pagina negozio passa dalla STESSA rotta: quel che faceva
    ieri deve farlo oggi."""
    print("\n[3] LA REGRESSIONE: il negozio di ieri")
    legacy = chiedi()                      # senza limit: il ramo storico
    prova("senza limit: tutti gli annunci in un colpo", atteso,
          ids(legacy))
    prova("senza limit: nessun cursore", False, "cursore" in legacy)
    prova("senza limit: nessun totale", False, "totale" in legacy)
    prova("senza limit: lo scaffale vuoto c'e'", VENDUTI,
          len(legacy["esauriti"]))
    prova("senza limit: i feedback ci sono", 1, len(legacy["feedback"]))
    # un cursore storto non e' un errore: si torna alla prima pagina
    storto = chiedi(limit=PAGINA, cursore="questo-non-e-un-cursore")
    prova("un cursore storto vale come prima pagina", atteso[:PAGINA],
          ids(storto))
    # e si arriva col codice del negozio come con lo username
    prova("il codice del negozio apre la stessa bottega", atteso[:PAGINA],
          ids(chiedi(chi="neg22222", limit=PAGINA)))
    prova("...e l'indirizzo parlante pure", atteso[:PAGINA],
          ids(chiedi(chi="neg22222-la-bottega", limit=PAGINA)))


def prove_venduti_fuori(atteso):
    """Un venduto non entra MAI fra gli annunci: l'invariante che
    tiene separata la vetrina dallo scaffale."""
    print("\n[4] IL VENDUTO RESTA SULLO SCAFFALE")
    righe, _, _ = scorri_tutto()
    visti = [a["titolo"] for a in righe]
    prova("nessun «Finito» fra gli annunci", [],
          [t for t in visti if t.startswith("Finito")])
    prova("...e sono tutti e soli gli attivi", ATTIVI, len(visti))
    prova("il totale conta gli attivi, non lo scaffale", ATTIVI,
          chiedi(limit=PAGINA)["totale"])


def main():
    print("=" * 66)
    print("COLLAUDO «Altri oggetti del venditore» — la rotta vera")
    print("=" * 66)
    db = avvio()
    print(f"database usa-e-getta: {db}")
    atteso = semina()
    prove_scorsa_intera(atteso)
    prove_liste_tacciono()
    prove_regressione(atteso)
    prove_venduti_fuori(atteso)
    print("\n" + "=" * 66)
    print(f"{PASSATE} passate, {FALLITE} fallite")
    print("=" * 66)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
