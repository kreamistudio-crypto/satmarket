"""
IL COLLAUDO DELLA MAPPA DEL RITIRO A MANO (14 nov 2026, cantiere
mappa-mercatino, richiesta di Andrea).

`prove.py` difende i pezzi — il conto per comune su un database montato
a mano, la leva, il client in node. Quello che non puo' fare e' far
girare la ROTTA vera: `/api/listings` e' `async`, vuole il database del
server e la sua WHERE, e la mappa vive dentro la sua busta di prima
pagina.

Qui il server VERO gira su un database usa-e-getta, e si chiedono le
sole cose che contano:

  · la busta porta `mappa_ritiro` coi comuni degli annunci ATTIVI col
    ritiro a mano, e solo loro (niente spedizione-sola, niente venduti);
  · la zona senza comune non diventa un pallino: si conta in `senza`;
  · la mappa segue la categoria, come la griglia;
  · `comune` restringe la griglia a quel comune, e la mappa NO — gli
    altri pallini restano, per cambiare idea;
  · un comune che non esiste da' una griglia vuota, mai un 400;
  · a leva spenta la busta e' quella di ieri e `comune` non conta.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete, nessuna chiave.

USO:  python collaudo_mappa_ritiro.py
"""

import asyncio
import os
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
        print(f"  ✗ {nome}\n      atteso: {atteso!r}"
              f"\n      avuto:  {avuto!r}")


def avvio():
    """Il config finto PRIMA di importare server, o si aprirebbe il
    database di casa. La leva della mappa NON si scrive: deve essere
    accesa di serie (decisione di Andrea, 14 nov 2026)."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-mappa-ritiro-"),
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
    SRV = server
    return db


# titolo, categoria, stato, consegna, zona
CATALOGO = [
    ("Divano in velluto", "Casa e giardino", "attivo", "ritiro", "Milano (MI)"),
    ("Libreria bianca", "Casa e giardino", "attivo", "entrambe", "Milano Navigli"),
    ("Bici da corsa", "Biciclette", "attivo", "ritiro", "Milano (MI)"),
    ("Tastiera", "Informatica", "attivo", "spedizione", "Milano (MI)"),
    ("Tavolo venduto", "Casa e giardino", "venduto", "ritiro", "Milano (MI)"),
    ("Letto singolo", "Casa e giardino", "attivo", "ritiro", "Roma (RM)"),
    ("Sedie", "Casa e giardino", "attivo", "ritiro", "dietro la stazione"),
    ("Codice regalo", "Informatica", "attivo", "digitale", "Roma (RM)"),
]


def semina():
    con = SRV.db()
    con.execute("DELETE FROM annunci")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                "registrato) VALUES(222,'La Bottega','labottega',"
                "'neg22222',1)")
    for n, (tit, cat, stato, consegna, zona) in enumerate(CATALOGO):
        lat, lon = SRV.coordinate_da_zona(zona)
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "regione,lat,lon) VALUES(222,?,'',10000,?,?,?,?,?,1,'sats','buono',"
            "?,?,?)",
            (tit, cat, zona, stato, 100 + n, consegna,
             SRV.regione_da_zona(zona), lat, lon))
    con.commit()
    con.close()


def vetrina(**extra):
    """La rotta vera, chiamata come la chiamerebbe FastAPI."""
    return asyncio.run(SRV.lista_annunci(
        q=extra.pop("q", ""), limit=30, cursore="",
        cat=extra.pop("cat", ""), ordina="", prezzo_min=0, prezzo_max=0,
        valuta_filtro="sats", regione="",
        solo_ritiro=extra.pop("solo_ritiro", 0),
        comune=extra.pop("comune", ""),
        x_tg_init_data="", barattolo_sessione="", **extra))


def pallini(r):
    m = r.get("mappa_ritiro")
    return None if m is None else [[c[2], c[3]] for c in m["comuni"]]


def titoli(r):
    return sorted(a["titolo"] for a in r["annunci"])


def main():
    db = avvio()
    print(f"Database usa-e-getta: {db}")
    semina()

    print("\n[la leva nasce accesa]")
    prova("senza una riga nel config la mappa c'e'", True,
          SRV.MERCATINO_MAPPA_RITIRO)

    print("\n[i pallini nella busta di prima pagina]")
    r = vetrina()
    prova("i comuni degli annunci attivi col ritiro, il piu' pieno in testa",
          [["Milano (MI)", 3], ["Roma (RM)", 1]], pallini(r))
    prova("la zona senza comune non e' un pallino: si conta a parte",
          1, r["mappa_ritiro"]["senza"])
    prova("il punto e' il centro del comune, a due decimali",
          [round(c, 2) for c in SRV.COMUNI["milano"]],
          r["mappa_ritiro"]["comuni"][0][:2])
    prova("la mappa segue la categoria, come la griglia",
          [["Milano (MI)", 2], ["Roma (RM)", 1]],
          pallini(vetrina(cat="Casa e giardino")))

    print("\n[il comune scelto]")
    r = vetrina(solo_ritiro=1, comune="Milano (MI)")
    prova("restringe la griglia agli annunci col ritiro di quel comune",
          ["Bici da corsa", "Divano in velluto", "Libreria bianca"], titoli(r))
    prova("...e il totale lo dice", 3, r["totale"])
    prova("...ma la mappa resta intera, per cambiare idea",
          [["Milano (MI)", 3], ["Roma (RM)", 1]], pallini(r))
    r = vetrina(solo_ritiro=1, comune="Atlantide")
    prova("un comune che non esiste da' una griglia vuota, mai un 400",
          [[], 0], [r["annunci"], r["totale"]])
    prova("con una ricerca la mappa conta la stessa rosa",
          [["Milano (MI)", 1]], pallini(vetrina(q="divano")))

    print("\n[a leva spenta: la vetrina di ieri]")
    SRV.MERCATINO_MAPPA_RITIRO = False
    try:
        r = vetrina(solo_ritiro=1, comune="Roma (RM)")
        prova("niente mappa nella busta", False, "mappa_ritiro" in r)
        prova("...e il comune non conta", 5, r["totale"])
    finally:
        SRV.MERCATINO_MAPPA_RITIRO = True

    print(f"\n{PASSATE} passate, {FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
