# -*- coding: utf-8 -*-
"""
IL COLLAUDO DEL DIZIONARIO INGLESE (17 nov 2026, cantiere inglese-tappa-1).

`prove.py` tiene le sentinelle e fa girare il traduttore in node; qui
risponde il SERVER VERO (fastapi c'e' solo nei collaudi): la rotta
`/lingua/{codice}.js` serve il dizionario con la cache di un giorno e le
cinture, rifiuta un nome fuori lista, e a leva LINGUA_INGLESE spenta
risponde 404 anche per l'inglese; la pagina porta il caricatore con la
versione del file servito, e per chi legge in italiano non cambia niente.

NON TOCCA NIENTE DI VERO: il `config` finto lo installa `avvio()` del
banco, PRIMA dell'import di server. Nessuna rete.

USO:  python collaudo_lingua.py
"""

import hashlib
import re
import sys

import collaudo_lnbits_muto as banco

prova = banco.prova


def main():
    print("=" * 58)
    print("  IL DIZIONARIO INGLESE, SERVITO")
    print("=" * 58)
    banco.avvio()
    from fastapi.testclient import TestClient

    c = TestClient(banco.SRV.app)

    # la leva nasce SPENTA (17 nov 2026 sera, scelta di Andrea): qui si
    # accende, come sul collaudo; la sezione «la leva spenta» la rispegne
    banco.SRV.LINGUA_INGLESE = True
    print("\n[la rotta del dizionario]")
    r = c.get("/lingua/en.js")
    prova("il dizionario inglese risponde 200", 200, r.status_code)
    prova("...come JavaScript", True,
          r.headers.get("content-type", "").startswith("application/javascript"))
    prova("...con la cache di un giorno", "public, max-age=86400",
          r.headers.get("cache-control"))
    prova("...e le cinture", "nosniff", r.headers.get("x-content-type-options"))
    prova("...ed e' il file del repo, byte per byte",
          hashlib.sha256(open("lingua/en.js", "rb").read()).hexdigest(),
          hashlib.sha256(r.content).hexdigest())
    prova("...che si registra da solo nella pagina", True,
          "(globalThis.BARATTOLO_LINGUE = globalThis.BARATTOLO_LINGUE || {}).en = {" in r.text
          and "registraTraduzioni('en')" in r.text)
    prova("una lingua che non c'e' e' un 404", 404, c.get("/lingua/it.js").status_code)
    prova("...e un nome storto pure", [404, 404, 404],
          [c.get("/lingua/..%2Fconfig.js").status_code,
           c.get("/lingua/en.js.bak").status_code,
           c.get("/lingua/en").status_code])

    print("\n[la pagina]")
    g = c.get("/")
    m = re.search(r"const LINGUA_VER = '([0-9a-f]+)';", g.text)
    prova("la pagina porta la versione del dizionario", True, bool(m))
    prova("...uguale all'inizio dello sha256 del file servito",
          hashlib.sha256(r.content).hexdigest()[:10], m and m.group(1))
    prova("...e lo chiede solo a chi legge in inglese", True,
          "if (linguaApp() === 'en') {" in g.text
          and "s.src = '/lingua/en.js?v=' + LINGUA_VER;" in g.text)
    prova("la pagina resta <html lang=\"it\">: l'inglese lo mette il "
          "traduttore quando il dizionario arriva", True,
          '<html lang="it">' in g.text)

    print("\n[la leva spenta]")
    banco.SRV.LINGUA_INGLESE = False
    try:
        prova("a LINGUA_INGLESE spenta il dizionario e' un 404", 404,
              c.get("/lingua/en.js").status_code)
        prova("...e la pagina e' la stessa di prima", 200, c.get("/").status_code)
    finally:
        banco.SRV.LINGUA_INGLESE = True
    prova("riaccesa, torna", 200, c.get("/lingua/en.js").status_code)

    print("\n" + "=" * 58)
    print(f"  {banco.PASSATE} passate, {banco.FALLITE} fallite")
    print("=" * 58)
    return 1 if banco.FALLITE else 0


if __name__ == "__main__":
    sys.exit(main())
