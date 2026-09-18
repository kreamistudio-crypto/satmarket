"""Collaudo della FINESTRA SCORREVOLE della vetrina (set 2026, al posto
delle tornate «3 ogni 30» d'agosto): la rotta VERA di /api/listings su
un database usa-e-getta.

Il caso e' quello dei connettori: un negozio che entra con DUECENTO
righe a `creato` IDENTICO (il giro scrive `adesso` una volta per tutto
il catalogo) sopra una vetrina di venditori piccoli. Senza riordino si
prende le prime sette pagine in blocco; con la finestra, in qualunque
12 card consecutive ne ha al piu' 3.

Si verifica quello che `prove.py` non puo' — la rotta intera, con i
suoi filtri e le sue buste:
  · in 12 card consecutive un venditore ne ha al piu' 3, finche' gli
    altri hanno qualcosa da mostrare;
  · lo scorrimento ricompone ESATTAMENTE la rosa, senza doppioni, e
    `totale` (il COUNT di sempre) dice quante card scorrono davvero —
    anche se a meta' scorrimento qualcuno pubblica;
  · un reparto e i filtri COMPONGONO con la finestra (si riordina la
    rosa filtrata);
  · l'ordine esplicito e la ricerca NON riordinano;
  · il negozio del venditore mostra il SUO catalogo intero, nell'ordine
    di sempre (la finestra e' della vetrina, non della bottega);
  · il client di ieri senza `limit` legge lo stesso ordine;
  · a leva spenta e' il mondo di prima.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA di
importare server, quindi si apre un database vuoto in una cartella
temporanea. Niente rete, niente chiavi.

    python collaudo_finestra.py
"""
import asyncio
import os
import sys
import tempfile
import types
from collections import Counter

QUI = os.path.dirname(os.path.abspath(__file__))
SRV = None
PASSATE = FALLITE = 0


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
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-finestra-"),
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


GROSSO = 1000          # il negozio collegato: 200 righe, stesso secondo
PICCOLI = range(1, 16)  # quindici venditori con 1..4 annunci


def semina():
    con = SRV.db()
    con.execute("DELETE FROM annunci")
    ADESSO = 2_000_000
    for v in PICCOLI:
        con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                    "registrato) VALUES(?,?,?,?,1)",
                    (v, f"Piccolo {v}", f"piccolo{v}", f"neg{v:05d}"))
        for k in range(1 + v % 4):
            con.execute(
                "INSERT INTO annunci(venditore_id,titolo,descrizione,"
                "prezzo_sats,categoria,zona,stato,creato,consegna,quantita,"
                "valuta,condizione,regione) VALUES(?,?,?,?,?,?,'attivo',?,"
                "'spedizione',1,'sats','buono','Piemonte')",
                (v, f"Oggetto {v}-{k}", "usato", 10_000 * v + k,
                 "Casa e giardino" if v % 2 else "Informatica",
                 "Torino (TO)", ADESSO - 1000 * v - k))
    con.execute("INSERT OR REPLACE INTO utenti(tg_id,nome,username,negozio,"
                "registrato) VALUES(?,?,?,?,1)",
                (GROSSO, "Il Negozio", "ilnegozio", "neg99999"))
    for k in range(200):
        con.execute(
            "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
            "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
            "regione) VALUES(?,?,?,?,?,?,'attivo',?,'spedizione',1,'sats',"
            "'nuovo','Lombardia')",
            (GROSSO, f"Prodotto {k:03d}", "dal catalogo", 5_000 + k,
             "Informatica" if k % 2 else "Casa e giardino", "Milano (MI)",
             ADESSO + 10))   # TUTTI piu' recenti dei piccoli, stesso secondo
    con.commit()
    con.close()


def semina_uno(v, creato):
    """Un annuncio in piu', pubblicato adesso: il mondo che cambia
    mentre qualcuno scorre."""
    con = SRV.db()
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "regione) VALUES(?,'Appena pubblicato','nuovo',1234,'Altro',"
        "'Torino (TO)','attivo',?,'spedizione',1,'sats','buono','Piemonte')",
        (v, creato))
    con.commit()
    i = cur.lastrowid
    con.close()
    return i


def elimina(i):
    con = SRV.db()
    con.execute("DELETE FROM annunci WHERE id=?", (i,))
    con.commit()
    con.close()


def peggio(vend, n=12):
    """Il massimo di card di UN venditore in n card consecutive."""
    return max((max(Counter(vend[i:i + n]).values())
                for i in range(max(1, len(vend) - n + 1))), default=0)


def chiedi(limit=30, cursore="", **extra):
    """La rotta vera, chiamata come la chiamerebbe FastAPI."""
    return asyncio.run(SRV.lista_annunci(
        limit=limit, cursore=cursore,
        q=extra.pop("q", ""), cat=extra.pop("cat", ""),
        ordina=extra.pop("ordina", ""),
        x_tg_init_data="", barattolo_sessione="", **extra))


def scorri(tetto=60, **extra):
    """Tutte le pagine come `caricaAltri`: un solo cursore, mai una
    rilettura della prima pagina."""
    pagine, cursore, giri = [], "", 0
    prima = None
    while True:
        d = chiedi(cursore=cursore, **extra)
        if prima is None:
            prima = d
        pagine.append([(a["id"], a.get("venditore_id")) for a in d["annunci"]])
        cursore = d.get("cursore")
        giri += 1
        if not cursore or giri > tetto:
            break
    return pagine, prima


def ids_rosa(**dove):
    con = SRV.db()
    w = "stato='attivo'" + ("".join(f" AND {k}=?" for k in dove))
    r = {x[0] for x in con.execute(f"SELECT id FROM annunci WHERE {w}",
                                  list(dove.values()))}
    con.close()
    return r


def main():
    db = avvio()
    print(f"Database usa-e-getta: {db}")
    print(f"Leve: VETRINA_PER_VENDITORE {SRV.VETRINA_PER_VENDITORE}, "
          f"VETRINA_FINESTRA {SRV.VETRINA_FINESTRA}")
    semina()
    # venditore_id esce solo agli autenticati e qui la rotta si chiama
    # da anonimo: lo si RILEGGE dal database per id — che e' anche la
    # prova che il campo non esce a chi non deve.
    con = SRV.db()
    di_chi = {r[0]: r[1] for r in con.execute(
        "SELECT id, venditore_id FROM annunci")}
    crea = {r[0]: (r[1], r[0]) for r in con.execute(
        "SELECT id, creato FROM annunci")}
    con.close()

    def vend(pagina):
        return [di_chi[i] for i, _ in pagina]

    print("\n[il caso dei connettori: 200 righe nello stesso secondo]")
    pagine, prima = scorri()
    prova("l'anonimo non vede venditore_id", True,
          all(v is None for _, v in pagine[0]))
    tutti = [v for p in pagine for v in vend(p)]
    # i piccoli sono 39 annunci: a 9 ogni 12 durano ~52 card, e da li'
    # in giu' resta solo il negozio (la regola si piega in fondo)
    prova("nelle prime 48 card: in 12 consecutive nessuno piu' di 3", 3,
          peggio(tutti[:48]))
    prova("...e il negozio nelle prime 12 ne ha 3, nelle prime 30 nove",
          (3, 9), (tutti[:12].count(GROSSO), tutti[:30].count(GROSSO)))
    prova("la prima pagina e' piena", 30, len(pagine[0]))
    visti = [i for p in pagine for i, _ in p]
    rosa = ids_rosa()
    prova("lo scorrimento ricompone ESATTAMENTE la rosa", rosa, set(visti))
    prova("zero doppioni", len(rosa), len(visti))
    prova("`totale` dice quante card scorrono davvero", len(visti),
          prima["totale"])
    prova("il 200º prodotto del negozio arriva, in coda", True,
          visti[-1] in {i for i, v in di_chi.items() if v == GROSSO})
    prova("i tre del negozio aprono la pagina", [GROSSO] * 3,
          vend(pagine[0])[:3])
    # (quelli da 4 annunci — v%4 == 3 — sforano anche loro, e il loro
    # 4º slitta: non fanno parte di questa domanda)
    piccoli = [i for i in visti if di_chi[i] != GROSSO and di_chi[i] % 4 != 3]
    prova("i piccoli da 1-3 annunci restano in ordine di data",
          sorted(piccoli, key=lambda i: crea[i], reverse=True), piccoli)

    print("\n[la fotografia: si pubblica mentre si scorre]")
    d = chiedi()
    nuovo = semina_uno(PICCOLI[0], 3_000_000)
    visti, cursore = [a["id"] for a in d["annunci"]], d["cursore"]
    while cursore:
        d = chiedi(cursore=cursore)
        visti += [a["id"] for a in d["annunci"]]
        cursore = d.get("cursore")
    prova("chi scorreva: zero doppioni e zero buchi", (rosa, len(rosa)),
          (set(visti), len(visti)))
    prova("...e il nuovo apre la prossima prima pagina", nuovo,
          chiedi()["annunci"][0]["id"])
    elimina(nuovo)

    print("\n[la finestra compone coi filtri]")
    pagine, prima = scorri(cat="Informatica")
    v1 = [v for p in pagine for v in vend(p)]
    # nel reparto i piccoli hanno 15 annunci: a 9 ogni 12 durano ~20 card
    prova("dentro un reparto: in 12 consecutive nessuno piu' di 3", 3,
          peggio(v1[:18]))
    prova("...e la pagina resta piena", 30, len(pagine[0]))
    visti = [i for p in pagine for i, _ in p]
    prova("...e la rosa del reparto torna intera",
          ids_rosa(categoria="Informatica"), set(visti))
    prova("...senza doppioni e col totale giusto",
          (len(set(visti)), len(visti)), (len(visti), prima["totale"]))
    pagine, _ = scorri(regione="Lombardia")
    prova("un filtro che pesca SOLO il negozio: tutto suo, nessuna "
          "pagina corta", [30] * 6 + [20], [len(p) for p in pagine])

    print("\n[dove la finestra NON si applica]")
    d = chiedi(ordina="prezzo_su")
    prova("ordina=prezzo: i suoi 30 prodotti piu' economici, in fila", 30,
          Counter(di_chi[a["id"]] for a in d["annunci"])[GROSSO])
    prova("...col cursore di ieri, a due pezzi", 2,
          len(d["cursore"].split("_")))
    asyncio.run(SRV.scalda_ricerca())
    d = chiedi(q="prodotto")
    prova("la ricerca: ordine di pertinenza, tutti del negozio", 30,
          Counter(di_chi[a["id"]] for a in d["annunci"])[GROSSO])
    neg = SRV.negozio(chi="ilnegozio", limit=30, cursore="",
                      x_tg_init_data="", barattolo_sessione="")
    prova("il negozio del venditore: il suo catalogo, 30 per pagina", 30,
          len(neg["annunci"]))
    prova("...col cursore di ieri", 2, len(neg["cursore"].split("_")))
    legacy = chiedi(limit=0)
    prova("il client di ieri (senza limit) legge un array", True,
          isinstance(legacy, list))
    prova("...nello STESSO ordine della vetrina paginata",
          [i for p, _ in [scorri()] for pg in p for i, _ in pg][:len(legacy)],
          [a["id"] for a in legacy])
    prova("un cursore delle tornate (tre pezzi): prima pagina, non un "
          "errore", [a["id"] for a in chiedi()["annunci"]],
          [a["id"] for a in chiedi(cursore="0_2000010_239")["annunci"]])

    print("\n[la leva spenta e' il mondo di ieri]")
    SRV.VETRINA_PER_VENDITORE = 0
    d = chiedi()
    prova("a leva 0 la prima pagina e' tutta del negozio", 30,
          Counter(di_chi[a["id"]] for a in d["annunci"])[GROSSO])
    prova("...col cursore a due pezzi", 2, len(d["cursore"].split("_")))
    SRV.VETRINA_PER_VENDITORE = 3

    print(f"\n{'=' * 58}\n  {PASSATE} passate, {FALLITE} fallite\n{'=' * 58}")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
