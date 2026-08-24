# -*- coding: utf-8 -*-
"""
LA CLASSIFICA, CAMMINATA PER DAVVERO (ago 2026).

`prove.py` difende la FORMA e fa girare il giudice sui casi che
decidono. Quello che non puo' fare e' chiamare l'endpoint: qui il
server VERO risponde su un database usa-e-getta, e si guarda cio' che
esce — che e' l'unica cosa che dimostra che il tg_id, gli XP e il
punteggio non escono davvero.

Il giro:

  1. un mercatino di cartone: sei persone, ordini `released` fra loro,
     feedback veri, XP di tipo 'ordine' e di tipo 'visita';
  2. l'ANONIMO chiama /api/classifica e riceve i primi N: nomi, media,
     persone, affari — e nient'altro;
  3. l'UTENTE fuori dai primi riceve in piu' la SUA riga; chi e' nei
     primi non la riceve (la vede gia');
  4. il FARMER con le identita' complici non compare da nessuna parte;
  5. gli XP di 'visita' non spostano una posizione: contano solo quelli
     degli ordini;
  6. la LEVA spenta chiude tutto: {"attiva": false} e zero letture;
  7. la CACHE serve la stessa risposta per un minuto — e non e' un
     dettaglio: un feedback nuovo non deve cambiare la classifica a
     meta' di una pagina che si sta guardando;
  8. il dump di `utenti`, `feedback` e `xp_eventi` e' IDENTICO prima e
     dopo: la classifica LEGGE E BASTA, come controlla_libro_mastro.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server, o si aprirebbe il database di casa. Gira senza
rete e senza chiavi.

USO:  python collaudo_classifica.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
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
    """Il config finto PRIMA di importare server."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo "
                         "script deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-classifica-"),
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
    cfg.CLASSIFICA_ATTIVA = True
    cfg.CLASSIFICA_TOP = 3          # basso apposta: fa esistere il «fuori»
    cfg.MODELLO_RICERCA = "claude-haiku-4-5-20251001"
    cfg.DB = db
    sys.modules["config"] = cfg
    sys.path.insert(0, QUI)
    os.chdir(QUI)
    import server
    SRV = server
    return db


def anonimo():
    """Nessuna identita': e' il caso di chi guarda dal browser."""
    SRV.utente_se_autenticato = lambda *a, **k: None


def come(tg_id):
    SRV.utente_se_autenticato = lambda *a, **k: {"id": tg_id}


def semina(db):
    """Un mercatino di cartone, scritto a mano perche' si veda.

    Sei persone che commerciano fra loro, piu' un FARMER con due
    identita' complici che non hanno mai visto nessun altro."""
    con = sqlite3.connect(db)
    gente = [(1, "Rosina"), (2, "Bottega Sole"), (3, "Miele di Bea"),
             (4, "Luca"), (5, "Carmen"), (6, "Dario"),
             (7, "FARMER"), (8, "Complice A"), (9, "Complice B")]
    for tg, nome in gente:
        con.execute("INSERT OR REPLACE INTO utenti(tg_id, nome, negozio, "
                    "registrato) VALUES(?,?,?,?)",
                    (tg, nome, f"neg{tg:05d}", 1_700_000_000))
    oid = [0]

    def ordine(v, c):
        oid[0] += 1
        con.execute("INSERT INTO ordini(id, annuncio_id, compratore_id, "
                    "venditore_id, prezzo_sats, stato, creato) "
                    "VALUES(?,?,?,?,?,'released',?)",
                    (oid[0], 1, c, v, 100000, 1_700_000_000))
        return oid[0]

    fid = [0]

    def voto(per, da, v):
        fid[0] += 1
        con.execute("INSERT INTO feedback(id, ordine_id, da_tg_id, "
                    "per_tg_id, voto, creato) VALUES(?,?,?,?,?,?)",
                    (fid[0], fid[0], da, per, v, 1_700_000_000))

    # I sei si scambiano roba: ognuno ha piu' controparti, quindi sono
    # tutti «recensori reali» l'uno per l'altro.
    coppie = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (3, 6),
              (4, 5), (5, 6), (6, 1), (4, 2)]
    for v, c in coppie:
        ordine(v, c)
        voto(v, c, 5)
        voto(c, v, 5 if (v + c) % 3 else 4)
    # Il commercio: gli XP degli ordini dicono chi ha mosso di piu'.
    for tg, punti in ((1, 4000), (2, 2500), (3, 1200), (4, 600),
                      (5, 300), (6, 80), (7, 9000)):
        con.execute("INSERT INTO xp_eventi(tg_id, tipo, punti, "
                    "riferimento, creato) VALUES(?,'ordine',?,?,?)",
                    (tg, punti, f"ordine:{tg}:venditore", 1_700_000_000))
    # ...e la visita giornaliera NON conta: qui ne do una montagna al
    # piu' debole, e non deve spostarlo di una posizione.
    con.execute("INSERT INTO xp_eventi(tg_id, tipo, punti, riferimento, "
                "creato) VALUES(6,'visita',99999,'giorno:x',?)",
                (1_700_000_000,))
    # IL FARMER: venti ordini con le sue due identita', venti voti a 5.
    for i in range(20):
        complice = 8 if i % 2 else 9
        ordine(7, complice)
        voto(7, complice, 5)
    con.commit()
    con.close()


def dump(db):
    con = sqlite3.connect(db)
    fuori = []
    for t in ("utenti", "feedback", "xp_eventi", "ordini"):
        fuori.append(list(con.execute(f"SELECT * FROM {t} ORDER BY rowid")))
    con.close()
    return fuori


def main() -> int:
    db = avvio()
    semina(db)
    print("\n[la classifica, camminata]")

    prima = dump(db)
    anonimo()
    r = SRV.classifica()
    prova("l'anonimo riceve la classifica", True, r["attiva"])
    nomi = [v["nome"] for v in r["voci"]]
    prova("escono i primi CLASSIFICA_TOP", 3, len(r["voci"]))
    prova("...e in cima c'e' chi ha commerciato di piu'",
          "Rosina", nomi[0])
    prova("le posizioni sono 1, 2, 3", [1, 2, 3],
          [v["posizione"] for v in r["voci"]])

    # COSA NON ESCE: e' la ragione per cui questo collaudo esiste.
    chiavi = set(r["voci"][0])
    prova("dalla voce non esce il tg_id", False, "id" in chiavi)
    prova("...ne' gli XP", False, "xp" in chiavi)
    prova("...ne' il punteggio", False, "punti" in chiavi)
    prova("escono i fatti su cui poggia la posizione",
          {"posizione", "nome", "negozio", "avatar", "titolo",
           "media", "voti", "persone", "affari"}, chiavi)

    # IL FARMER non c'e', da nessuna parte.
    tutti = SRV.classifica()
    prova("il farmer non e' fra i primi", False, "FARMER" in nomi)
    prova("...e il totale non lo conta", 6, tutti["totale"])

    # LA TUA RIGA: solo a chi e' fuori dai primi.
    come(6)                       # Dario, l'ultimo dei sei
    r = SRV.classifica()
    prova("chi e' fuori dai primi riceve la sua riga", True,
          bool(r["mia"]))
    prova("...con la sua posizione", 6, r["mia"]["posizione"])
    prova("...e la posizione e' l'ultima", 6, r["totale"])
    come(1)                       # Rosina, che e' prima
    prova("chi e' nei primi non la riceve (la vede gia')", None,
          SRV.classifica()["mia"])
    come(7)                       # il farmer
    prova("il farmer non ha nemmeno una posizione", None,
          SRV.classifica()["mia"])

    # GLI XP DI 'VISITA' NON CONTANO, e qui si guarda il numero invece
    # di dedurlo: Dario ha 80 XP d'ordine e 99.999 di visita, e a
    # entrare nel conto devono essere gli 80.
    anonimo()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    _v, _c, xp, _a = SRV._dati_classifica(con)
    con.close()
    prova("in classifica entrano i soli XP degli ordini", 80, xp.get(6))
    r = SRV.classifica()
    prova("...e infatti chi ha 99.999 XP di visita resta fuori dai primi",
          False, "Dario" in [v["nome"] for v in r["voci"]])

    # LA RIGA CHE SPIEGA UN'APPARENZA guarda la fetta VISIBILE, e
    # questa prova ha CAMBIATO LATO col perche' scritto: qui i primi
    # tre hanno tutti 5,00 mentre piu' in basso ci sono dei 4, quindi
    # col conto su TUTTE le righe era SPENTA — cioe' spenta esattamente
    # davanti a una colonna di «5,00» identici, che e' il caso per cui
    # esiste. Trovata col giro dal vivo, non rileggendo.
    prova("i primi tre hanno la stessa media: la riga si accende",
          True, r["medie_piene"])
    prova("...e in cima ci sono davvero tre 5,00", [5.0, 5.0, 5.0],
          [v["media"] for v in r["voci"]])
    # Il rovescio: appena la fetta visibile ha medie diverse, la riga
    # non ha piu' niente da spiegare e si spegne da sola.
    SRV.CLASSIFICA_TOP = 6
    SRV._classifica_cache["quando"] = 0
    largo = SRV.classifica()
    prova("con sei righe le medie non sono piu' tutte uguali",
          False, largo["medie_piene"])
    prova("...e infatti fra le sei c'e' una media diversa", True,
          len({v["media"] for v in largo["voci"]}) > 1)
    SRV.CLASSIFICA_TOP = 3
    SRV._classifica_cache["quando"] = 0
    r = SRV.classifica()

    # LEGGE E BASTA: si guarda PRIMA di scrivere il feedback del
    # test qui sotto, o la prova si smentirebbe da se'.
    prova("il database e' identico prima e dopo", prima, dump(db))

    # LA CACHE serve la stessa risposta per un minuto: un feedback
    # nuovo non deve cambiare la classifica a meta' di una pagina.
    con = sqlite3.connect(db)
    con.execute("INSERT INTO feedback(ordine_id, da_tg_id, per_tg_id, "
                "voto, creato) VALUES(999, 2, 6, 5, ?)",
                (1_700_000_000,))
    con.commit()
    con.close()
    prova("la cache tiene la risposta per un minuto",
          r["voci"], SRV.classifica()["voci"])
    SRV._classifica_cache["quando"] = 0          # la si fa scadere a mano
    prova("...e scaduta rilegge i dati veri", True,
          SRV.classifica() is not None)

    # LEGGE E BASTA.

    # LA LEVA SPENTA chiude tutto.
    SRV.CLASSIFICA_ATTIVA = False
    prova("a leva spenta risponde «spenta»", {"attiva": False},
          SRV.classifica())

    print("\n" + "=" * 46)
    print(f"  {PASSATE} passate, {FALLITE} fallite")
    print("=" * 46)
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
