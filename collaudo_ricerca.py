# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLA RICERCA (ago 2026).

`prove.py` difende i pezzi — le radici, i termini, la forma della
domanda, il trigger che invalida — su un indice montato a mano. Quello
che non puo' fare e' far girare la ROTTA vera: la vetrina e' `async`,
vuole un database e passa da `arricchisci_righe_vetrina`.

Qui il server VERO gira su un database usa-e-getta, e si chiedono le
sole cose che contano davvero:

  · «collezionismo» trova l'annuncio che dice «collezione» e quelli
    della categoria Collezionismo — cioe' il caso che ha aperto il
    cantiere;
  · la ricerca SI COMPONE coi filtri (categoria, prezzo, regione), che
    e' la ragione per cui vive dentro `/api/listings` e non in una
    rotta sua;
  · scorrendo si vede tutta la rosa, UNA volta sola e nell'ordine di
    pertinenza — un difetto di paginazione non fallisce da solo: fa
    sparire dei risultati, e se ne accorge solo chi conta;
  · il TOTALE dice il vero (l'etichetta «N oggetti» ci poggia sopra);
  · un annuncio appena pubblicato si trova SUBITO, senza aspettare un
    giro d'orologio;
  · quel che non e' in vetrina — venduto, rimosso, in revisione — non
    esce MAI da una ricerca;
  · il ramo LEGACY (senza `limit`) e `/api/search` rispondono nella
    forma di ieri, per i client rimasti in cache.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Nessuna
rete, nessuna chiave: LNbits e Anthropic non si chiamano mai.

USO:  python collaudo_ricerca.py
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
    database di casa."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-ricerca-"),
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


# titolo, descrizione, categoria, stato, prezzo, zona
CATALOGO = [
    ("Album di figurine Panini", "un pezzo da collezione, anni '90",
     "Collezionismo", "attivo", 50_000, "Carmagnola (TO)"),
    ("Monete antiche romane", "ottimo per chi colleziona",
     "Collezionismo", "attivo", 300_000, "Milano (MI)"),
    ("Bicicletta da corsa Bianchi", "telaio in acciaio, 10 velocità",
     "Biciclette", "attivo", 900_000, "Torino (TO)"),
    ("Tastiera meccanica Keychron", "switch marroni, retroilluminata",
     "Informatica", "attivo", 200_000, "Torino (TO)"),
    ("Sedia da ufficio", "ci si appoggia bene anche la tastiera",
     "Casa e giardino", "attivo", 80_000, "Milano (MI)"),
    ("Set di tastiere vintage", "tre pezzi, funzionanti",
     "Informatica", "attivo", 400_000, "Napoli (NA)"),
    # IL CASO DELLA CATEGORIA NUDA: il testo non dice mai «collezione»
    # ne' niente che ci somigli — a farlo trovare e' SOLO la categoria
    # nell'indice. Senza di lui, togliere la categoria dai campi non
    # farebbe fallire niente (successo davvero, torturando).
    ("Soldatini di piombo", "dipinti a mano, scatola originale",
     "Collezionismo", "attivo", 120_000, "Torino (TO)"),
    # E IL CASO DEI PESI: il titolo non nomina la tastiera, la
    # descrizione la ripete quattro volte. Con i pesi appiattiti
    # salirebbe in cima; col titolo che pesa dieci, no.
    ("Poltrona relax", "comoda per usare la tastiera: tastiera a "
     "portata, tastiera sulle ginocchia, tastiera ovunque",
     "Casa e giardino", "attivo", 150_000, "Torino (TO)"),
    ("Album di francobolli", "collezione completa",
     "Collezionismo", "venduto", 70_000, "Torino (TO)"),
    ("Cartoline da collezione", "lotto misto",
     "Collezionismo", "rimosso", 20_000, "Torino (TO)"),
    ("Figurine rare in revisione", "collezione privata",
     "Collezionismo", "revisione", 30_000, "Torino (TO)"),
]


def semina():
    con = SRV.db()
    for t in ("annunci",):
        con.execute(f"DELETE FROM {t}")
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                "registrato) VALUES(222,'La Bottega','labottega',"
                "'neg22222',1)")
    for n, (tit, des, cat, stato, prezzo, zona) in enumerate(CATALOGO):
        cur = con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "regione) VALUES(222,?,?,?,?,?,?,?,'ritiro',?,'sats','buono',?)",
            (tit, des, prezzo, cat, zona, stato, 100 + n,
             0 if stato == "venduto" else 1,
             SRV.regione_da_zona(zona)))
        assert cur.lastrowid
    con.commit()
    con.close()
    return None


def cerca(q="", limit=30, cursore="", **extra):
    """La rotta vera, chiamata come la chiamerebbe FastAPI."""
    return asyncio.run(SRV.lista_annunci(
        q=q, limit=limit, cursore=cursore,
        cat=extra.pop("cat", ""), ordina=extra.pop("ordina", ""),
        prezzo_min=extra.pop("prezzo_min", 0),
        prezzo_max=extra.pop("prezzo_max", 0),
        valuta_filtro=extra.pop("valuta_filtro", "sats"),
        regione=extra.pop("regione", ""),
        x_tg_init_data="", barattolo_sessione="", **extra))


def titoli(r):
    righe = r["annunci"] if isinstance(r, dict) else r
    return [a["titolo"] for a in righe]


def main():
    db = avvio()
    print(f"Database usa-e-getta: {db}")
    print(f"Stemmer: {'sì' if SRV._STEMMER else 'NO (a troncamento)'}")
    semina()
    # la passata d'avvio non gira da sola qui (e' un evento di
    # startup): la si chiama come la chiamerebbe uvicorn
    asyncio.run(SRV.scalda_ricerca())

    print("\n[il caso che ha aperto il cantiere]")
    t = titoli(cerca("collezionismo"))
    prova("«collezionismo» trova chi dice «collezione»", True,
          "Album di figurine Panini" in t)
    prova("...e chi dice «colleziona»", True, "Monete antiche romane" in t)
    prova("...cercando «collezione» il risultato è lo stesso", sorted(t),
          sorted(titoli(cerca("collezione"))))

    print("\n[le desinenze e le due parole]")
    prova("«biciclette» trova «Bicicletta»", True,
          "Bicicletta da corsa Bianchi" in titoli(cerca("biciclette")))
    prova("«bici da corsa» pure", True,
          "Bicicletta da corsa Bianchi" in titoli(cerca("bici da corsa")))
    prova("«tastiere» trova «Tastiera»", True,
          "Tastiera meccanica Keychron" in titoli(cerca("tastiere")))
    # IL TITOLO PESA PIU' DELLA DESCRIZIONE: la sedia nomina la
    # tastiera di sfuggita e non deve stare in cima.
    prova("chi cerca «tastiera» trova prima la tastiera",
          "Tastiera meccanica Keychron", titoli(cerca("tastiera"))[0])
    prova("le due parole si legano in «e»",
          ["Tastiera meccanica Keychron"], titoli(cerca("tastiera meccanica")))
    prova("una parola che non c'è non pesca niente", [],
          titoli(cerca("elicottero")))

    print("\n[la categoria è nell'indice, coi suoi sinonimi]")
    # Il testo dei soldatini non nomina nessuna collezione: a farli
    # trovare e' la CATEGORIA.
    prova("la categoria si cerca anche se il testo non la dice", True,
          "Soldatini di piombo" in titoli(cerca("collezionismo")))
    # ...e i sinonimi della categoria, che vengono dal catalogo di
    # casa: «pc» e' un sinonimo di Informatica.
    prova("...e i suoi sinonimi: «pc» trova l'informatica", True,
          "Tastiera meccanica Keychron" in titoli(cerca("pc")))
    prova("...«hifi» trova l'audio e video", [],
          titoli(cerca("hifi")))   # nessun annuncio in quella categoria

    # I PESI: la poltrona ripete «tastiera» quattro volte in
    # descrizione e non deve battere chi ce l'ha nel titolo.
    ordine = titoli(cerca("tastiera"))
    prova("il titolo batte una descrizione che ripete la parola", True,
          ordine.index("Tastiera meccanica Keychron")
          < ordine.index("Poltrona relax"))

    print("\n[quel che non è in vetrina non esce mai]")
    for stato, tit in (("venduto", "Album di francobolli"),
                       ("rimosso", "Cartoline da collezione"),
                       ("in revisione", "Figurine rare in revisione")):
        prova(f"un annuncio {stato} non esce da una ricerca", False,
              tit in titoli(cerca("collezione")))

    print("\n[si compone coi filtri, che è il perché di dov'è]")
    # DUE risultati e non uno, ed e' giusto: «Set di tastiere» sta in
    # Informatica e il plurale combacia (era l'atteso sbagliato del
    # primo giro — il collaudo aveva ragione lui).
    prova("ricerca + categoria",
          ["Set di tastiere vintage", "Tastiera meccanica Keychron"],
          sorted(titoli(cerca("tastiera", cat="Informatica"))))
    prova("ricerca + prezzo", ["Sedia da ufficio"],
          titoli(cerca("tastiera", prezzo_max=100_000)))
    prova("ricerca + regione", ["Sedia da ufficio"],
          titoli(cerca("tastiera", regione="Lombardia")))
    prova("un filtro che svuota la rosa non esplode", [],
          titoli(cerca("tastiera", cat="Motori")))

    print("\n[la paginazione, che fallisce in silenzio]")
    tutti = titoli(cerca("collezione", limit=30))
    visti, cursore, giri = [], "", 0
    while giri < 20:
        r = cerca("collezione", limit=1, cursore=cursore)
        visti += titoli(r)
        cursore = r["cursore"]
        giri += 1
        if not cursore:
            break
    prova("l'unione delle pagine è esattamente la rosa", tutti, visti)
    prova("...e nessun risultato esce due volte", len(set(visti)), len(visti))
    prova("l'ultima pagina chiude il cursore", None, cursore)
    prova("il totale dice il vero", len(tutti),
          cerca("collezione", limit=1)["totale"])
    prova("un cursore storto riparte dalla prima pagina", tutti[:1],
          titoli(cerca("collezione", limit=1, cursore="pasticcio")))

    print("\n[l'indice si ripara da solo]")
    con = SRV.db()
    con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione)"
        " VALUES(222,'Trenino elettrico Märklin','scala H0',60000,"
        "'Collezionismo','Torino (TO)','attivo',999,'ritiro',1,'sats',"
        "'buono')")
    con.commit()
    con.close()
    prova("un annuncio appena pubblicato si trova subito", True,
          "Trenino elettrico Märklin" in titoli(cerca("trenino")))
    con = SRV.db()
    con.execute("UPDATE annunci SET titolo='Locomotiva a vapore' "
                "WHERE titolo='Trenino elettrico Märklin'")
    con.commit()
    con.close()
    prova("un titolo riscritto entra nell'indice al giro dopo", True,
          "Locomotiva a vapore" in titoli(cerca("locomotiva")))
    prova("...e il vecchio non si trova più", [], titoli(cerca("trenino")))

    print("\n[le forme di ieri, per i client in cache]")
    # la rosa si RICONTA: nel frattempo e' nata la locomotiva, che sta
    # in Collezionismo e quindi risponde a «collezione» — il perche'
    # per cui la categoria e' nell'indice
    adesso = titoli(cerca("collezione", limit=30))
    legacy = cerca("collezione", limit=0)
    prova("senza limit resta l'array di sempre", True, isinstance(legacy, list))
    prova("...e dice le stesse cose", sorted(adesso), sorted(titoli(legacy)))
    io = "collaudo:222:La Bottega"
    guscio = SRV.cerca(q="collezione", busta=0, x_tg_init_data=io,
                       barattolo_sessione="")
    prova("/api/search risponde ancora con l'array", True,
          isinstance(guscio, list) and len(guscio) == len(adesso))
    busta = SRV.cerca(q="collezione", busta=1, x_tg_init_data=io,
                      barattolo_sessione="")
    prova("...e con la busta dice che l'AI non c'è", False, busta["ai"])

    print("\n" + "=" * 58)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 58)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
