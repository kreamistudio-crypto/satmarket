# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEI METODI DELLE ROTTE (22 set 2026, sera).

Dal campo: `/.well-known/assetlinks.json` rispondeva **405** a una HEAD.
La causa non e' nostra ed e' la ragione per cui questo collaudo esiste:
Starlette regalerebbe la HEAD a ogni GET, **FastAPI no** — le sue rotte
tengono i soli metodi dichiarati. Chi verifica un dominio (Google, i
validatori di Digital Asset Links, un monitor) bussa spesso in HEAD, e
un 405 li' si legge come «questo dominio non dichiara niente».

PERCHE' UN COLLAUDO E NON UNA PROVA — ed e' la lezione del giro. La
prima stesura faceva girare una app FastAPI di cartone dentro
`prove.py`, ed e' uscita ROSSA in CI: li' fastapi non c'e', la prova e'
finita in `salta()`, e con `PROVE_SEVERE=1` una saltata vale una
fallita. Non e' un incidente da aggirare installando fastapi: sta
scritto nel workflow che `prove.py` gira APPOSTA senza httpx ne'
fastapi, perche' allargargli l'ambiente cambierebbe cosa prova senza
che nessuno lo decida. Il posto giusto per una domanda che vuole il
server VERO sono i collaudi, dove fastapi c'e' perche' lo installa il
passo apposta.
In `prove.py` resta la sentinella sul TESTO — che il `@app.head` sia
dichiarato — e i due pezzi si guardano le spalle: quella prende chi lo
cancella, questo prende chi lo rende inutile.

IL CONTROLLO VALE QUANTO LA CURA, e sta qui apposta: `/manifest.json`
risponde ANCORA 405 alla HEAD. Non e' una svista — il perimetro chiesto
era l'assetlinks — ed e' quel che rende la diagnosi verificata invece
che raccontata: se un domani FastAPI cominciasse a regalare la HEAD da
se', questa riga diventerebbe rossa e ci direbbe che il mondo e'
cambiato sotto la riga in piu' che abbiamo scritto.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_rotte_metodi.py
"""

import os
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova
VIA = "/.well-known/assetlinks.json"


def main():
    print("=" * 58)
    print("  I METODI DELLE ROTTE — il giro vero")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    c = TestClient(banco.SRV.app)
    atteso = open(os.path.join(".well-known", "assetlinks.json"), "rb").read()

    print("\n[l'assetlinks: GET e HEAD]")
    g = c.get(VIA)
    prova("il GET risponde 200", 200, g.status_code)
    prova("...e serve il file INTERO, byte per byte", atteso, g.content)
    prova("...come JSON, con la cache corta di un'ora",
          ["application/json", "public, max-age=3600"],
          [g.headers.get("content-type"), g.headers.get("cache-control")])

    h = c.head(VIA)
    prova("la HEAD risponde 200 (dava 405)", 200, h.status_code)
    prova("...col corpo VUOTO", b"", h.content)
    # gli header devono essere gli STESSI, `Content-Length` compreso:
    # chi legge una HEAD legge quelli, ed e' tutto quel che riceve
    prova("...e con gli stessi header del GET, Content-Length compreso",
          {k.lower(): v for k, v in g.headers.items() if k.lower() != "date"},
          {k.lower(): v for k, v in h.headers.items() if k.lower() != "date"})

    print("\n[il controllo: una rotta che la HEAD non la dichiara]")
    prova("/manifest.json risponde ancora 405 alla HEAD", 405,
          c.head("/manifest.json").status_code)
    prova("...mentre in GET risponde 200: e' il METODO, non la rotta",
          200, c.get("/manifest.json").status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
