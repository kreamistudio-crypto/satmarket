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

import asyncio
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
EV_ESS, EV_ADV = "1a" * 32, "2b" * 32    # gli id dei suoi due eventi

# L'UPDATE che si lancia in produzione, VERBATIM. La WHERE e' la query
# del libro mastro parola per parola — «cura tutte le righe che
# l'allarme segnala» — quindi e' idempotente per costruzione: dopo,
# quell'insieme e' vuoto. Sta qui perche' un collaudo che prova una
# SQL DIVERSA da quella che si lancia non prova niente.
CURA = ("UPDATE annunci SET contatto_nostr='', nostr_origine_d='', "
        "nostr_origine_id='', nostr_origine_foto='' "
        "WHERE contatto_nostr <> '' AND nostr_event_id <> ''")


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

    # I ganci verso il mondo di fuori: contatori, mai rete. Servono a
    # `ricarica_quantita`, che e' il modo VERO di dimostrare che il
    # venditore ha riavuto in mano il suo annuncio.
    async def muto(*a, **k):
        return None
    server.annuncio_su_nostr = muto
    server.promo_venduto = muto
    server.notifica = muto
    server.verifica_utente = lambda *a, **k: {"id": VENDITORE}
    return db


def chiama(fn, *args, corpo=None):
    """Una rotta vera, col suo corpo JSON. I ganci sono create_task:
    senza cedere il controllo almeno una volta il loop si chiuderebbe
    prima che partano (il patto di collaudo_pausa)."""
    async def leggi(_req):
        return corpo if corpo is not None else {}
    SRV.leggi_json = leggi

    async def giro():
        r = await fn(*args)
        await asyncio.sleep(0.02)
        return r
    return asyncio.run(giro())


def rifornisce(aid, quanti):
    """Il gesto che l'adozione gli aveva tolto: torna il numero nuovo,
    o il codice dell'errore se la porta e' ancora chiusa."""
    try:
        d = chiama(SRV.ricarica_quantita, aid, None,
                   corpo={"quantita": quanti})
        return d.get("quantita")
    except Exception as e:
        return f"{getattr(e, 'status_code', '?')}"


def evento(d, titolo, sats=50_000, descrizione="Licenza annuale.",
           venduto=False, eid=None):
    """Un NIP-99 suo: firmato dalla SUA chiave, con una coordinata sua
    (mai `barattolo-N`, che sarebbe un riflesso e lo filtra un'altra
    guardia). Il tag `image` c'e' dall'11 ott 2026 (cantiere
    foto-obbligatorie: un evento mai visto senza foto non nasce), e
    non si scarica niente lo stesso: `importa()` passa uno scaricatore
    di cartone, e resta l'indirizzo."""
    tags = [["d", d], ["title", titolo], ["price", str(sats), "SAT"],
            ["location", "Pavia (PV)"],
            ["image", f"https://foto.test/{d}.jpg"]]
    if venduto:
        tags.append(["status", "sold"])
    return {"id": eid or ("ff" * 32), "pubkey": CHIAVE, "kind": 30402,
            "created_at": int(time.time()), "content": descrizione,
            "tags": tags}


def cancellazione(eid):
    """Una NIP-09 sua (kind 5) sull'evento `eid`: e' cosi' che un suo
    ripensamento su Amethyst arriva fin qui."""
    return {"id": "ee" * 32, "pubkey": CHIAVE, "kind": 5,
            "created_at": int(time.time()), "content": "",
            "tags": [["e", eid]]}


def relay_risponde(eventi):
    IMP.interroga = lambda relay, hexkey: list(eventi)


def importa():
    """Il giro VERO. Il cambio si passa a mano (il patto del `vaglio`):
    con None se lo leggerebbe da CoinGecko."""
    return IMP.importa_venditore(NPUB, VENDITORE, db=SRV.DB,
                                 cambio={"EUR": 60_000.0, "USD": 65_000.0},
                                 scarica=lambda url: None)


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


def semina_adottate():
    """Lo stato di PRODUZIONE del 20 agosto: le due righe native
    ADOTTATE dall'import — `contatto_nostr` scritto sopra, la loro
    testa ancora li' (e' la riga a due teste) e le coordinate
    dell'evento di LUI addosso."""
    semina()
    con = SRV.db()
    for aid, d, eid in ((208, "panda-essential", EV_ESS),
                        (209, "panda-advanced", EV_ADV)):
        con.execute(
            "UPDATE annunci SET contatto_nostr=?, nostr_origine_d=?, "
            "nostr_origine_id=?, nostr_origine_foto=? WHERE id=?",
            (NPUB, d, eid, '["http://suo/1.jpg"]', aid))
    con.commit()
    con.close()


def cura():
    """L'UPDATE di produzione, VERBATIM. Torna quante righe ha toccato."""
    con = SRV.db()
    n = con.execute(CURA).rowcount
    con.commit()
    con.close()
    return n


def riga(aid):
    con = SRV.db()
    r = con.execute("SELECT contatto_nostr, nostr_event_id, nostr_autore, "
                    "nostr_origine_d FROM annunci WHERE id=?",
                    (aid,)).fetchone()
    con.close()
    return None if not r else (r["contatto_nostr"], r["nostr_event_id"],
                               r["nostr_autore"], r["nostr_origine_d"])


def stato(aid):
    con = SRV.db()
    r = con.execute("SELECT stato FROM annunci WHERE id=?",
                    (aid,)).fetchone()
    con.close()
    return None if not r else r["stato"]


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
    coppie = [(c["importato"]["id"], c["nativo"]["id"],
               c["firmato_da_te"])
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
          sorted([(n[0], 208, True) if "Essential" in n[1]
                  else (n[0], 209, True) for n in nuove]),
          sorted(doppioni()))

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

    print("\n[il ramo «sold»]")
    semina()
    # Il suo annuncio Amethyst si vende. La riga NATIVA omonima e' un
    # ALTRO annuncio, col suo stock e la sua storia: spegnerla come
    # «venduto» le toglierebbe la vetrina, e al riavvio dopo la
    # riparazione dell'invariante le azzererebbe anche i pezzi.
    relay_risponde([evento("panda-essential",
                           "Antivirus Panda Dome Essential", venduto=True)])
    importa()
    prova("un `sold` suo non spegne la riga nativa con la sua testa",
          "attivo", stato(208))
    # ...ma sull'importato di ieri, senza testa, deve spegnere ancora
    relay_risponde([evento("d-suo", "Vecchio importato", venduto=True)])
    importa()
    prova("...e spegne ancora l'importato di ieri", "venduto", stato(300))

    print("\n[la cura, provata prima di lanciarla]")
    semina_adottate()
    prova("si parte dallo stato di produzione: due righe a due teste",
          [208, 209], due_teste())
    prova("...e da li' il venditore non puo' rifornire", "400",
          rifornisce(208, 5))
    prova("l'UPDATE tocca esattamente quelle due righe", 2, cura())
    prova("il libro mastro tace", [], due_teste())
    prova("rilanciarlo non tocca piu' niente (e' idempotente)", 0, cura())
    prova("la riga e' tornata NATIVA, con la sua testa e il suo autore",
          ("", "ev-208", CHIAVE, ""), riga(208))
    prova("...e il venditore puo' rifornirla di nuovo", 5,
          rifornisce(208, 5))
    # E adesso il giro d'import vero: le due native restano, nascono le
    # due importate, e la coppia arriva nella deduplica col flag.
    relay_risponde([evento("panda-essential",
                           "Antivirus Panda Dome Essential", eid=EV_ESS),
                    evento("panda-advanced",
                           "Antivirus Panda Dome Advanced", eid=EV_ADV)])
    importati5, aggiornati5, _ = importa()
    prova("l'import non le ri-adotta e crea due righe nuove",
          (2, 0), (importati5, aggiornati5))
    prova("...e le due curate sono ancora native", ["", ""],
          [riga(208)[0], riga(209)[0]])
    coppie = doppioni()
    prova("la coppia arriva nella deduplica", 2, len(coppie))
    prova("...e dice che l'evento del nativo l'ha firmato LUI",
          [True, True], [c[2] for c in coppie])
    prova("il libro mastro tace anche dopo l'import", [], due_teste())
    # La ragione per cui si azzera anche `nostr_origine_id`: e'
    # l'aggancio delle NIP-09. Lasciandolo addosso alla riga curata, un
    # suo ripensamento su Amethyst spegnerebbe l'annuncio nato QUI —
    # adesso spegne il solo importato, che e' la riga di quell'evento.
    # (Va per ULTIMO: la lapide vale per sempre, e messo prima si
    # portava via l'evento dal giro d'import qui sopra.)
    nuovo = [r[0] for r in elenco() if r[2] and r[1].endswith("Essential")]
    relay_risponde([cancellazione(EV_ESS)])
    importa()
    prova("una sua NIP-09 non spegne piu' la riga nata qui",
          "attivo", stato(208))
    prova("...e spegne l'importato, che e' la riga di quell'evento",
          ["rimosso"], [stato(i) for i in nuovo])

    print(f"\n{'=' * 58}\n  {PASSATE} passate, {FALLITE} fallite\n{'=' * 58}")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
