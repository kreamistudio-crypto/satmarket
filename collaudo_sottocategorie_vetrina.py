# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE SOTTOCATEGORIE IN VETRINA (18 nov 2026, cantiere
sottocategorie, richiesta di Andrea).

`prove.py` guarda la forma: la leva, le copie del catalogo, i fili nel
client. Qui gira la ROTTA vera su un database usa-e-getta, e si chiede
quel che la tendina della striscia promette:

  · la busta di prima pagina porta la leva e i conteggi per scaffale,
    GLOBALI come quelli per categoria: soli attivi, una famiglia conta
    UNO, le righe senza sottocategoria (o con una storta) non contano;
  · lo scaffale filtra DENTRO la categoria, e il totale lo segue;
  · senza categoria lo scaffale non filtra, una voce inventata da' una
    vetrina vuota e mai un errore;
  · a leva spenta il server fa come quello di ieri: niente conteggi, lo
    scaffale ignorato;
  · la scheda dell'annuncio porta la sottocategoria (il form Vendi la
    ritrova in modifica);
  · la proposta del form (/api/sottocategoria) e' il giudice del server.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server. Nessuna rete, nessuna chiave.

USO:  python collaudo_sottocategorie_vetrina.py
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
    database di casa. Senza la riga SOTTOCATEGORIE_VETRINA: e' il caso
    del VPS, dove la leva nuova non c'e' e deve valere accesa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-sottocat-"),
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


# titolo, categoria, sottocategoria, stato, famiglia
CATALOGO = [
    ("MacBook Air M1", "Informatica", "computer", "attivo", ""),
    ("ThinkPad X230", "Informatica", "computer", "attivo", ""),
    ("Kindle Paperwhite", "Informatica", "tablet", "attivo", ""),
    ("Mouse senza fili", "Informatica", "", "attivo", ""),
    # una sottocategoria STORTA (di un'altra categoria): non conta e non
    # filtra, come se fosse vuota
    ("Cavo strano", "Informatica", "mtb", "attivo", ""),
    # venduto e rimosso non contano
    ("Dell venduto", "Informatica", "computer", "venduto", ""),
    ("HP rimosso", "Informatica", "computer", "rimosso", ""),
    # una FAMIGLIA di due varianti conta UNO, come la sua card
    ("Maglietta Bitcoin S", "Bitcoin", "merch", "attivo", "fam-1"),
    ("Maglietta Bitcoin M", "Bitcoin", "merch", "attivo", "fam-1"),
    ("Trezor Model T", "Bitcoin", "hardware-wallet", "attivo", ""),
]


def semina():
    con = SRV.db()
    con.execute("DELETE FROM annunci")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                "registrato) VALUES(222,'La Bottega','labottega',"
                "'neg22222',1)")
    for n, (tit, cat, sotto, stato, fam) in enumerate(CATALOGO):
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,sottocategoria,zona,stato,creato,consegna,quantita,"
            "valuta,condizione,famiglia) VALUES(222,?,'',1000,?,?,'Milano (MI)',"
            "?,?,'ritiro',?,'sats','buono',?)",
            (tit, cat, sotto, stato, 100 + n, 0 if stato == "venduto" else 1,
             fam))
    con.commit()
    con.close()


def vetrina(**extra):
    """La rotta vera, chiamata come la chiamerebbe FastAPI."""
    return asyncio.run(SRV.lista_annunci(
        q="", limit=100, cursore="", cat=extra.pop("cat", ""), ordina="",
        prezzo_min=0, prezzo_max=0, valuta_filtro="sats", regione="",
        x_tg_init_data="", barattolo_sessione="", **extra))


def titoli(r):
    return sorted(a["titolo"] for a in r["annunci"])


def main():
    avvio()
    semina()

    print("\n[la leva: accesa anche senza la riga nel config]")
    prova("SOTTOCATEGORIE_VETRINA vale True di serie", True,
          SRV.SOTTOCATEGORIE_VETRINA)
    busta = vetrina()
    prova("la busta lo dice alla pagina", True,
          busta.get("sottocategorie_vetrina"))

    print("\n[i conteggi della tendina]")
    prova("soli attivi, una famiglia conta uno, vuote e storte fuori",
          {"Informatica": {"computer": 2, "tablet": 1},
           "Bitcoin": {"merch": 1, "hardware-wallet": 1}},
          busta.get("sottoconteggi"))
    prova("«Tutta la categoria» resta il conteggio di sempre (vuote comprese)",
          5, busta["conteggi"].get("Informatica"))

    print("\n[il filtro]")
    r = vetrina(cat="Informatica", sottocategoria="computer")
    prova("lo scaffale filtra dentro la categoria",
          ["MacBook Air M1", "ThinkPad X230"], titoli(r))
    prova("...e il totale lo segue", 2, r["totale"])
    prova("la famiglia esce con la sua capofila, una volta",
          1, len(vetrina(cat="Bitcoin", sottocategoria="merch")["annunci"]))
    prova("senza scaffale la categoria e' intera (vuote e storte comprese)",
          5, len(vetrina(cat="Informatica")["annunci"]))
    prova("lo scaffale senza categoria non filtra",
          titoli(vetrina()), titoli(vetrina(sottocategoria="computer")))
    prova("uno scaffale inventato da' una vetrina vuota, mai un errore",
          [], titoli(vetrina(cat="Informatica", sottocategoria="boh")))

    print("\n[la scheda porta la sottocategoria, per il form in modifica]")
    con = SRV.db()
    mac = con.execute("SELECT id FROM annunci WHERE titolo='MacBook Air M1'"
                      ).fetchone()["id"]
    con.close()
    prova("la scheda dice «computer»", "computer",
          SRV.un_annuncio(mac, x_tg_init_data="",
                          barattolo_sessione="").get("sottocategoria"))

    print("\n[la proposta del form: il giudice del server]")
    prop = lambda **k: asyncio.run(SRV.sottocategoria_proposta(**k))
    prova("un portatile e' «computer»", {"sottocategoria": "computer"},
          prop(categoria="Informatica", titolo="Portatile Lenovo 14 pollici"))
    prova("una categoria piatta non propone", {"sottocategoria": ""},
          prop(categoria="Altro", titolo="Portatile Lenovo"))
    prova("una categoria inventata non propone", {"sottocategoria": ""},
          prop(categoria="Fantacategoria", titolo="Portatile Lenovo"))

    print("\n[leva spenta: il server di ieri]")
    SRV.SOTTOCATEGORIE_VETRINA = False
    spenta = vetrina()
    prova("la busta dice spenta e non porta conteggi", (False, None),
          (spenta.get("sottocategorie_vetrina"), spenta.get("sottoconteggi")))
    prova("lo scaffale non filtra piu'",
          titoli(vetrina(cat="Informatica")),
          titoli(vetrina(cat="Informatica", sottocategoria="computer")))
    prova("la proposta tace", {"sottocategoria": ""},
          prop(categoria="Informatica", titolo="Portatile Lenovo"))
    SRV.SOTTOCATEGORIE_VETRINA = True

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
