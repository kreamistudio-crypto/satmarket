# -*- coding: utf-8 -*-
"""
🌱 LA SEMINA DEL COLLAUDO, SUL SERVER VERO (20 ott 2026, cantiere
collaudo-ritocco, richiesta di Andrea).

`prove.py` prova il giudice delle guardie e i dati della semina; qui si
fa la domanda che solo il server VERO risponde: su uno schema nato da
`init_db`, la semina scrive righe che le ROTTE leggono davvero.

IL GIRO:
  - le guardie: senza PROVA_SOLO_IDS, senza URL_PUBBLICO, con URL_PUBBLICO
    di produzione la semina NON scrive niente;
  - con la lista e l'indirizzo del collaudo: quattro venditori, dodici
    annunci attivi e due venduti, due ordini del primo id (uno in corso,
    uno concluso);
  - le rotte: la vetrina mostra gli annunci di prova, ogni foto risponde
    (anche il francobollo `_min`), il compratore vede i suoi due ordini;
  - rilanciata: niente doppioni.

Niente parla con Telegram, coi relay o con LNbits: il `config` finto lo
installa `avvio()` del banco PRIMA dell'import di server. Le foto vanno in
una cartella usa-e-getta (`SEMINA_CARTELLA_FOTO`, e `FOTO_DIR` del server
girato li'): la `foto/` del repo non si tocca.

USO:  python collaudo_semina_collaudo.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile

import collaudo_lnbits_muto as banco

prova = banco.prova
COMPRATORE = {"X-Tg-Init-Data": "collaudo:111:Compratore"}


def conta(db):
    con = sqlite3.connect(db)
    try:
        return (con.execute("SELECT COUNT(*) FROM utenti WHERE tg_id BETWEEN 9001 AND 9004").fetchone()[0],
                dict(con.execute("SELECT stato, COUNT(*) FROM annunci WHERE venditore_id "
                                 "BETWEEN 9001 AND 9004 GROUP BY stato").fetchall()),
                con.execute("SELECT stato FROM ordini WHERE compratore_id=111 "
                            "ORDER BY id").fetchall())
    finally:
        con.close()


def main():
    print("=" * 58)
    print("  🌱 LA SEMINA DEL COLLAUDO — il giro vero")
    print("=" * 58)
    db = banco.avvio()
    from fastapi.testclient import TestClient
    import semina_collaudo as sc

    SRV = banco.SRV
    cfg = sys.modules["config"]
    c = TestClient(SRV.app)
    c.get("/api/me", headers=COMPRATORE)          # il compratore 111 esiste
    cartella = tempfile.mkdtemp(prefix="semina-collaudo-")
    SRV.FOTO_DIR = cartella
    os.environ["SEMINA_CARTELLA_FOTO"] = cartella
    try:
        print("\n[le guardie: dove non si semina, non si scrive niente]")
        vuoto = conta(db)
        # il config del banco dice MODALITA_COLLAUDO = True (il server
        # l'ha gia' letto e lo tiene): per la semina si guarda come un
        # config di produzione, che non la dichiara vera
        cfg.MODALITA_COLLAUDO = False
        prova("senza PROVA_SOLO_IDS (e senza MODALITA_COLLAUDO): ferma",
              1, sc.main(["--db", db]))
        cfg.PROVA_SOLO_IDS = [111]
        prova("con la lista ma senza URL_PUBBLICO (vale barattolo.store): ferma",
              1, sc.main(["--db", db]))
        cfg.URL_PUBBLICO = "https://barattolo.store"
        prova("con URL_PUBBLICO di produzione: ferma", 1, sc.main(["--db", db]))
        prova("...e in nessuno dei tre casi e' stato scritto niente", vuoto, conta(db))

        print("\n[con l'istanza di prova: il mercatino finto]")
        cfg.URL_PUBBLICO = "https://collaudo.esempio.test"
        prova("con la lista e l'indirizzo del collaudo: semina", 0, sc.main(["--db", db]))
        v, annunci, ordini = conta(db)
        prova("quattro venditori, dodici annunci attivi e due venduti",
              (4, {"attivo": 12, "venduto": 2}), (v, annunci))
        prova("due ordini del primo id della lista: uno in corso, uno concluso",
              [("locked",), ("released",)], ordini)

        print("\n[le rotte li vedono]")
        r = c.get("/api/listings", headers=COMPRATORE)
        titoli = [a[1] for a in sc.ANNUNCI[:12]]
        prova("la vetrina mostra i dodici annunci di prova", (200, []),
              (r.status_code, [t for t in titoli if t not in r.text]))
        con = sqlite3.connect(db)
        try:
            foto = [x[0] for x in con.execute(
                "SELECT foto FROM annunci WHERE venditore_id BETWEEN 9001 AND 9004")]
        finally:
            con.close()
        import json
        nomi = [n for f in foto for n in json.loads(f or "[]")]
        prova("ogni annuncio ha la sua foto finta", 14, len(nomi))
        stati = {c.get(f"/foto/{n}").status_code for n in nomi}
        stati |= {c.get(f"/foto/{n[:-4]}_min.jpg").status_code for n in nomi}
        prova("...e ogni foto risponde, francobollo compreso", {200}, stati)
        r = c.get("/api/orders", headers=COMPRATORE)
        prova("il compratore vede i suoi ordini", (200, True, True),
              (r.status_code, "Mouse senza fili di prova" in r.text,
               "Tazza dipinta di prova" in r.text))

        print("\n[il lavoro: i servizi di prova e le card della sezione]")
        con = sqlite3.connect(db)
        try:
            servizi = con.execute(
                "SELECT COUNT(*), SUM(consegna='servizio'), SUM(quantita=?) FROM annunci "
                "WHERE venditore_id IN (9005,9006) AND stato='attivo'",
                (sc.QUANTITA_SERVIZIO,)).fetchone()
        finally:
            con.close()
        prova("undici servizi attivi, tutti servizi e senza scorte", (11, 11, 11), servizi)
        lav = c.get("/api/listings?limit=100&sezione=lavoro", headers=COMPRATORE).json()
        mer = c.get("/api/listings?limit=100&sezione=mercato", headers=COMPRATORE).json()
        tit_lav = {a["titolo"] for a in lav["annunci"]}
        prova("la sezione Lavoro li mostra tutti, e il Mercato nessuno",
              (set(), set()), ({x[1] for x in sc.SERVIZI} - tit_lav,
                               {x[1] for x in sc.SERVIZI} & {a["titolo"] for a in mer["annunci"]}))
        r = c.get("/api/listings?limit=100&sezione=lavoro&cat=Lavoro%20e%20servizi"
                  "&sottocategoria=traduzioni", headers=COMPRATORE).json()
        prova("una card del Lavoro filtra il suo scaffale",
              ["Traduzione inglese-italiano di prova, a pagina"],
              [a["titolo"] for a in r["annunci"]])
        r = c.get("/api/listings?limit=100&sezione=lavoro&cat=Lezioni%20e%20corsi",
                  headers=COMPRATORE).json()
        prova("...e «Lezioni e corsi» le sue tre lezioni", 3, len(r["annunci"]))
        r = c.get("/api/listings?limit=100&sottocategoria=traduzioni",
                  headers=COMPRATORE).json()
        prova("lo scaffale senza la categoria non filtra", len(lav["annunci"]) + len(mer["annunci"]),
              len(r["annunci"]))

        print("\n[rilanciata: niente doppioni]")
        prima = conta(db)
        prova("la seconda semina riesce", 0, sc.main(["--db", db]))
        prova("...e non aggiunge niente", prima, conta(db))
    finally:
        os.environ.pop("SEMINA_CARTELLA_FOTO", None)
        shutil.rmtree(cartella, ignore_errors=True)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
