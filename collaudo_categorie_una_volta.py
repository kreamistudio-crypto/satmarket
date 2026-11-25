# -*- coding: utf-8 -*-
"""
IL COLLAUDO DELLE CATEGORIE CHIESTE UNA VOLTA SOLA (25 nov 2026,
cantiere categorie-una-volta; Andrea: «la tengo, ma una volta sola»).

Il giro dell'ora (`ricategorizza_automatico`) chiede all'AI dove
starebbero meglio gli annunci importati. Il «resta dov'e'» non lasciava
traccia: l'annuncio tornava al giro dopo, la domanda si ripagava, e
prima o poi l'AI rispondeva diverso — venti proposte nuove a ogni ora.
Qui gira la FUNZIONE VERA su un database usa-e-getta, con l'AI finta,
e si chiede quel che il freno 4 promette:

  · chi l'AI lascia dov'e' si segna «tenuta», e al giro dopo non si
    richiede (e nemmeno chi ha gia' una proposta in coda);
  · le «tenute» non entrano nella coda dei moderatori;
  · un annuncio che cambia categoria si richiede (la domanda e' nuova);
  · un lotto ESPLOSO non segna niente: quegli annunci si richiedono;
  · un giro senza proposte non suona;
  · una riga DECISA da un moderatore non la sovrascrive nessuno.

NON TOCCA NIENTE DI VERO: il modulo `config` viene sostituito PRIMA
dell'import di server; l'AI e l'avviso ai moderatori sono finti.
Nessuna rete, nessuna chiave vera.

USO:  python collaudo_categorie_una_volta.py
"""

import asyncio
import os
import sys
import tempfile
import types

QUI = os.path.dirname(os.path.abspath(__file__))
PASSATE = FALLITE = 0
SRV = None
CHIESTI = []        # gli id passati all'AI finta, giro per giro
AVVISI = []         # i testi dell'avviso ai moderatori
RISPOSTA = {}       # {id: categoria_nuova} che l'AI finta rende
ESPLODE = [False]   # True = la chiamata fallisce (None)


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
    """Il config finto PRIMA di importare server. La chiave e' finta ma
    non «INCOLLA»: altrimenti il giro esce subito e non si prova niente.
    Il client Anthropic nasce senza bussare a nessuno, e la chiamata
    vera non parte mai (la sostituisce `ai_finta`)."""
    global SRV
    if "server" in sys.modules:
        raise SystemExit("⚠️  server e' gia' importato: questo script "
                         "deve installare il suo config PRIMA.")
    db = os.path.join(tempfile.mkdtemp(prefix="barattolo-categorie-"),
                      "usa-e-getta.db")
    cfg = types.ModuleType("config")
    cfg.BOT_TOKEN = "0:collaudo"
    cfg.ANTHROPIC_API_KEY = "chiave-finta-del-collaudo"
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

    async def ai_finta(voci):
        CHIESTI.extend(i for i, _, _, _ in voci)
        if ESPLODE[0]:
            return None
        return {i: RISPOSTA[i] for i, _, _, _ in voci if i in RISPOSTA}

    async def avviso_finto(testo, *a, **k):
        AVVISI.append(testo)

    server._chiedi_categorie = ai_finta
    server.notifica_admin = avviso_finto
    return db


def semina(titolo, categoria):
    """Un annuncio IMPORTATO (fonte valorizzata): e' chi il giro guarda."""
    con = SRV.db()
    con.execute("INSERT OR IGNORE INTO utenti(tg_id,nome,username,"
                "registrato) VALUES(222,'La Bottega','labottega',1)")
    cur = con.execute(
        "INSERT INTO annunci(venditore_id,titolo,descrizione,prezzo_sats,"
        "categoria,zona,stato,creato,consegna,quantita,valuta,condizione,"
        "fonte) VALUES(222,?,'',1000,?,'Milano (MI)','attivo',1,'ritiro',"
        "1,'sats','buono','negozio')", (titolo, categoria))
    con.commit()
    i = cur.lastrowid
    con.close()
    return i


def giro():
    """Un giro dell'ora; ritorna gli id chiesti all'AI in QUESTO giro."""
    del CHIESTI[:]
    asyncio.run(SRV.ricategorizza_automatico())
    return sorted(CHIESTI)


def riga(i):
    con = SRV.db()
    r = con.execute("SELECT categoria_ora, categoria_nuova, stato FROM "
                    "categoria_proposta WHERE annuncio_id=?", (i,)).fetchone()
    con.close()
    return tuple(r) if r else None


def coda():
    con = SRV.db()
    ids = sorted(r["id"] for r in con.execute(SRV._SQL_PROPOSTE))
    con.close()
    return ids


def main():
    avvio()
    prova("la leva e' accesa di serie", True, SRV.RICATEGORIZZA_AUTO)
    a = semina("Maglietta Bitcoin nera", "Bitcoin")
    b = semina("Hardware wallet", "Bitcoin")
    c = semina("Adesivi Bitcoin", "Bitcoin")

    print("\n[il primo giro: uno da spostare, due che restano]")
    RISPOSTA.clear()
    RISPOSTA[a] = "Abbigliamento"
    prova("l'AI guarda tutti e tre", sorted([a, b, c]), giro())
    prova("chi va spostato e' una proposta",
          ("Bitcoin", "Abbigliamento", "proposta"), riga(a))
    prova("chi resta si segna «tenuta», con la categoria di adesso",
          [("Bitcoin", "Bitcoin", "tenuta")] * 2, [riga(b), riga(c)])
    prova("nella coda dei moderatori c'e' solo la proposta", [a], coda())
    prova("un avviso, per una proposta", 1, len(AVVISI))
    prova("...che dice quante", True, "1 nuove proposte" in AVVISI[-1])

    print("\n[il giro dopo: CHIESTO E' CHIESTO]")
    RISPOSTA.update({b: "Informatica", c: "Altro"})   # l'AI cambierebbe idea
    prova("nessuno si richiede: ne' le tenute ne' la proposta in coda",
          [], giro())
    prova("e un giro senza proposte non suona", 1, len(AVVISI))
    prova("le tenute restano tenute",
          [("Bitcoin", "Bitcoin", "tenuta")] * 2, [riga(b), riga(c)])

    print("\n[chi cambia categoria si richiede]")
    con = SRV.db()
    con.execute("UPDATE annunci SET categoria='Altro' WHERE id=?", (c,))
    con.commit()
    con.close()
    RISPOSTA[c] = "Collezionismo"
    prova("si richiede solo quello", [c], giro())
    prova("...e la sua tenuta diventa una proposta nuova",
          ("Altro", "Collezionismo", "proposta"), riga(c))
    prova("in coda adesso sono due", sorted([a, c]), coda())

    print("\n[un lotto esploso non segna niente]")
    d = semina("Felpa con fulmine", "Bitcoin")
    ESPLODE[0] = True
    prova("si prova a chiederlo", [d], giro())
    prova("...ma nessuna riga: nessuno l'ha guardato", None, riga(d))
    ESPLODE[0] = False
    RISPOSTA.pop(d, None)
    prova("al giro dopo si richiede", [d], giro())
    prova("...e ora che l'AI ha risposto, e' tenuto",
          ("Bitcoin", "Bitcoin", "tenuta"), riga(d))

    print("\n[deciso e' deciso, anche contro una tenuta]")
    con = SRV.db()
    con.execute("UPDATE categoria_proposta SET stato='scartata', "
                "deciso_da=999 WHERE annuncio_id=?", (a,))
    con.execute("UPDATE annunci SET categoria='Altro' WHERE id=?", (a,))
    con.commit()
    con.close()
    prova("chi un moderatore ha deciso non si richiede, anche se cambia "
          "categoria", [], giro())
    prova("...e la sua riga resta quella del moderatore",
          ("Bitcoin", "Abbigliamento", "scartata"), riga(a))

    print(f"\n{'✅' if not FALLITE else '❌'} {PASSATE} passate, "
          f"{FALLITE} fallite")
    return 1 if FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
