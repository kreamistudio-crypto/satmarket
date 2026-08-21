# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE «DUE TESTE»: il 15 agosto, ricostruito (ago 2026).

`prove.py` difende la FORMA — che la clausola ci sia, che stia sul
match per TITOLO e non su quello per `d`, che la firma non scriva una
testa su una riga importata. Quello che non puo' fare e' far girare
l'IMPORT VERO su un database vero: le sue prove estraggono una query
dal sorgente e la interrogano, ma non vedono cosa succede dopo.

Questo script chiude quel buco, ed e' il calco di `collaudo_pausa.py`.
Ricostruisce il caso dal campo — il venditore 955197830 che il 15
agosto pubblica due annunci QUI, li firma col BIVIO, e pubblica gli
stessi due oggetti dal SUO client con un `d` suo — e chiede le sei
cose su cui il tappo si regge:

  · la riga NATIVA non viene adottata: `contatto_nostr` resta vuoto e
    la sua testa resta sua. E' la prova regina, e se un domani qualcuno
    allenta la clausola questa riga MOSTRA il difetto (la riga a due
    teste, stampata) invece di descriverlo;
  · al suo posto nasce una riga IMPORTATA nuova — le due restano DUE;
  · e la coppia compare nella DEDUPLICA col suo bottone, che e' quello
    che sarebbe dovuto succedere il 15 agosto;
  · il controllo del LIBRO MASTRO tace: nessuna riga a due teste;
  · il secondo giro non crea una terza riga (le nuove matchano per `d`);
  · il MONDO DI IERI e' intatto: l'importato legacy senza testa e senza
    coordinata si aggiorna ancora per TITOLO — e' il caso per cui quel
    match esiste — e un annuncio mai visto qui entra come sempre.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. I relay sono
di cartone (nessuna rete), gli eventi non portano foto (nessun
download) e il cambio si passa a mano, o l'import chiamerebbe CoinGecko.

USO:  python collaudo_due_teste.py
"""

import os
import sys
import tempfile
import time
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = IMP = None

VENDITORE = 955197830
CHIAVE = "bb" * 32                       # la sua, in esadecimale
NPUB = ""                                # la stessa in bech32 (in avvio)


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
    global SRV, IMP, NPUB
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-teste-"),
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
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    import importa_nostr
    SRV, IMP = server, importa_nostr
    NPUB = server.hex_to_npub(CHIAVE)
    # I relay di cartone: un solo «relay», e cosa risponde lo decide
    # ogni giro. Zero rete, zero foto, zero CoinGecko.
    IMP.RELAYS = ["wss://finto"]
    IMP.DB = db
    return db


def evento(d, titolo, sats=50_000, descrizione="Licenza annuale."):
    """Un NIP-99 suo: firmato dalla SUA chiave, con una coordinata sua
    (mai `barattolo-N`, che sarebbe un riflesso e lo filtra un'altra
    guardia). Niente tag `image`: cosi' non si scarica niente."""
    return {"id": "ff" * 32, "pubkey": CHIAVE, "kind": 30402,
            "created_at": int(time.time()), "content": descrizione,
            "tags": [["d", d], ["title", titolo],
                     ["price", str(sats), "SAT"],
                     ["location", "Pavia (PV)"]]}


def relay_risponde(eventi):
    IMP.interroga = lambda relay, hexkey: list(eventi)


def importa():
    """Il giro VERO. Il cambio si passa a mano (il patto del `vaglio`):
    con None se lo leggerebbe da CoinGecko."""
    return IMP.importa_venditore(NPUB, VENDITORE, db=SRV.DB,
                                 cambio={"EUR": 60_000.0, "USD": 65_000.0})


def semina():
    """Il 15 agosto: due annunci nati QUI, firmati col BIVIO (testa +
    autore), piu' un importato LEGACY senza testa e senza coordinata —
    quello per cui il match per titolo esiste — e niente altro."""
    con = SRV.db()
    for t in ("annunci", "doppioni_ignorati"):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,negozio,"
                "npub,npub_verificata,registrato) VALUES(?,?,?,?,?,?)",
                (VENDITORE, "Panda", "negozio1", NPUB, 1, 1))
    adesso = int(time.time())
    for aid, titolo in ((208, "Antivirus Panda Dome Essential"),
                        (209, "Antivirus Panda Dome Advanced")):
        con.execute(
            "INSERT INTO annunci(id,venditore_id,titolo,descrizione,"
            "categoria,prezzo_sats,zona,foto,contatto_nostr,"
            "nostr_event_id,nostr_autore,nostr_origine_d,stato,creato) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (aid, VENDITORE, titolo, "Licenza annuale.", "Informatica",
             50_000, "Pavia (PV)", "", "", f"ev-{aid}", CHIAVE, "",
             "attivo", adesso))
    con.execute(
        "INSERT INTO annunci(id,venditore_id,titolo,descrizione,categoria,"
        "prezzo_sats,zona,foto,contatto_nostr,nostr_event_id,nostr_autore,"
        "nostr_origine_d,stato,creato) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (300, VENDITORE, "Vecchio importato", "Roba di ieri.", "Altro",
         10_000, "", "", NPUB, "", "", "", "attivo", adesso))
    con.commit()
    con.close()


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT contatto_nostr, nostr_event_id, nostr_autore, "
                    "nostr_origine_d FROM annunci WHERE id=?",
                    (aid,)).fetchone()
    con.close()
    return None if not r else (r["contatto_nostr"], r["nostr_event_id"],
                               r["nostr_autore"], r["nostr_origine_d"])


def elenco():
    """Gli annunci del venditore: (id, titolo, importato?)."""
    con = SRV.db()
    righe = [(r["id"], r["titolo"], bool(r["contatto_nostr"]))
             for r in con.execute(
                 "SELECT id, titolo, contatto_nostr FROM annunci "
                 "WHERE venditore_id=? ORDER BY id", (VENDITORE,))]
    con.close()
    return righe


def due_teste():
    """La query del libro mastro, quella VERA presa dal catalogo."""
    sql = [c for c in SRV.CONTROLLI_LIBRO_MASTRO
           if c[0] == "annuncio a due teste"]
    if not sql:
        return "CONTROLLO SPARITO DAL CATALOGO"
    con = SRV.db()
    ids = [r[0] for r in con.execute(sql[0][2])]
    con.close()
    return ids


def doppioni():
    con = SRV.db()
    coppie = [(c["importato"]["id"], c["nativo"]["id"])
              for c in SRV.trova_doppioni_nostr(con, VENDITORE)]
    con.close()
    return coppie


def main():
    avvio()
    print("\n[il 15 agosto, ricostruito]")
    semina()
    prima = riga(208)
    # I suoi due eventi: stesso TITOLO delle righe native, coordinata
    # SUA. E' il match per titolo a scattare — quello per `d` non trova
    # niente, perche' una riga nativa non ha mai nostr_origine_d.
    relay_risponde([evento("panda-essential",
                           "Antivirus Panda Dome Essential"),
                    evento("panda-advanced",
                           "Antivirus Panda Dome Advanced")])
    importati, aggiornati, _ = importa()

    prova("la riga NATIVA non viene adottata: e' intatta", prima, riga(208))
    prova("...e nemmeno la sua gemella",
          ("", "ev-209", CHIAVE, ""), riga(209))
    prova("al loro posto nascono DUE righe importate nuove", 2, importati)
    nuove = [r for r in elenco() if r[0] not in (208, 209, 300)]
    prova("...e le due restano DUE, non una a due teste",
          [(True, "Antivirus Panda Dome Essential"),
           (True, "Antivirus Panda Dome Advanced")],
          sorted([(imp, tit) for _, tit, imp in nuove],
                 key=lambda x: x[1], reverse=True))
    prova("il libro mastro TACE: nessuna riga a due teste", [], due_teste())
    prova("e la coppia compare nella deduplica, col suo bottone",
          sorted([(n[0], 208) if "Essential" in n[1] else (n[0], 209)
                  for n in nuove]), sorted(doppioni()))

    print("\n[il giro dopo non ricomincia da capo]")
    importati2, aggiornati2, _ = importa()
    prova("il secondo giro non crea una terza riga", 0, importati2)
    prova("...le aggiorna per coordinata, come sempre", 2, aggiornati2)
    prova("gli annunci del venditore restano cinque", 5, len(elenco()))

    print("\n[il mondo di ieri]")
    semina()
    # L'importato LEGACY: contatto_nostr pieno, nessuna testa, nessuna
    # coordinata. E' il caso per cui il match per titolo esiste, e deve
    # continuare a funzionare.
    relay_risponde([evento("d-nuovo", "Vecchio importato", sats=12_000)])
    importati3, aggiornati3, _ = importa()
    prova("l'importato di ieri si ritrova ancora per TITOLO",
          (0, 1), (importati3, aggiornati3))
    prova("...e adesso ha la sua coordinata", "d-nuovo", riga(300)[3])
    relay_risponde([evento("d-mai-visto", "Mouse verticale", sats=30_000)])
    importati4, _, _ = importa()
    prova("un annuncio mai visto qui entra come sempre", 1, importati4)

    print(f"\n{'=' * 58}\n  {PASSATE} passate, {FALLITE} fallite\n{'=' * 58}")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
