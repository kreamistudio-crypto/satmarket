# -*- coding: utf-8 -*-
"""
QUANTO SI ALLUNGA LA CODA (ago 2026, cantiere «l'AI segnala, non
decide»).

Da quando il VIETATO dell'AI blocca solo su quattro famiglie — armi,
droghe, sesso a pagamento e sfruttamento, documenti e credenziali —
tutto il resto finisce in REVISIONE invece che nel rifiuto. Questo
script dice QUANTI annunci in piu' arriveranno nella coda, e non lo
stima: prende i rifiuti VERI gia' registrati in `moderazione_log` e ci
rifa' girare sopra il giudice nuovo, `_vietato_bloccante`, letto dal
TESTO di server.py (mai importandolo: l'import farebbe partire init_db
e le migrazioni — la lezione di ricategorizza.py).

LEGGE E BASTA: nessuna scrittura, da nessuna parte. Si puo' lanciare a
server acceso.

USO:  python stima_coda_moderazione.py [--giorni 30] [percorso/db]
"""

import os
import re
import sys
import time
import sqlite3
import unicodedata
from collections import Counter

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)


def giudice():
    """`_vietato_bloccante` e i suoi due cataloghi, dal sorgente."""
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    amb = {"re": re, "unicodedata": unicodedata}
    # LA FONTE PRIMA DELLE DERIVATE, o e' un NameError: dall'ago 2026
    # le due liste si ricavano da DIVIETI_BLOCCANTI, e chi exec-a solo
    # le derivate non ha di che ricavarle. Era rotto da allora, e a
    # dirlo non e' stata una prova — quella guardava che lo script non
    # SCRIVESSE, mai che girasse: adesso c'e' anche quella.
    # L'ORDINE E' QUELLO DELLE DIPENDENZE, e serve tutta la catena:
    # `_vietato_bloccante` e' il rovescio di `divieto_bloccante` e lo
    # CHIAMA, quindi senza anche quello e' un NameError un gradino
    # piu' in la'.
    for ancora in ("def normalizza(", "DIVIETI_BLOCCANTI = ",
                   "PAROLE_BLOCCANTI = ", "PREFISSI_BLOCCANTI = ",
                   "def divieto_bloccante(", "def _vietato_bloccante("):
        i = src.index(ancora)
        exec(src[i:src.index("\n\n\n", i)], amb)
    return amb["_vietato_bloccante"]


def main() -> int:
    giorni = 30
    args = sys.argv[1:]
    if "--giorni" in args:
        i = args.index("--giorni")
        giorni = int(args[i + 1])
        del args[i:i + 2]
    db = args[0] if args else None
    if not db:
        try:
            from config import DB
            db = DB
        except Exception:
            db = "satmarket.db"
    if not os.path.exists(db):
        print(f"Database non trovato: {db}")
        return 2

    blocca = giudice()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    da = int(time.time()) - giorni * 86400
    righe = con.execute(
        "SELECT motivo, titolo, creato FROM moderazione_log "
        "WHERE strato IN ('ai','lotto') AND esito='vietato' AND creato>=? "
        "ORDER BY creato DESC", (da,)).fetchall()
    # il polso della coda di oggi, per il confronto
    dubbi = con.execute(
        "SELECT COUNT(*) AS n FROM moderazione_log WHERE strato IN "
        "('ai','lotto') AND esito='dubbio' AND creato>=?", (da,)).fetchone()["n"]
    con.close()

    restano, spostati = [], []
    for r in righe:
        (restano if blocca(r["motivo"] or "") else spostati).append(r)

    print(f"\n  Ultimi {giorni} giorni — database: {db}\n")
    print(f"  Rifiuti dell'AI finora ............ {len(righe)}")
    print(f"    di cui BLOCCANO ancora .......... {len(restano)}")
    print(f"    di cui vanno in CODA ............ {len(spostati)}  "
          f"<- gli annunci in piu'")
    print(f"  Dubbi (coda) di oggi ............. {dubbi}")
    if dubbi or spostati:
        print(f"  La coda passa da {dubbi} a {dubbi + len(spostati)} "
              f"({len(spostati)/max(1, giorni):.1f} in piu' al giorno)")
    if not righe:
        print("\n  Nessun rifiuto dell'AI nel periodo: la coda non "
              "cambia.\n")
        return 0

    def elenco(titolo, quali):
        if not quali:
            return
        print(f"\n  {titolo}")
        for motivo, n in Counter(
                (r["motivo"] or "?")[:70] for r in quali).most_common(12):
            print(f"    {n:>3}x  {motivo}")

    elenco("Motivi che BLOCCANO ancora:", restano)
    elenco("Motivi che passano in CODA (da guardare a mano):", spostati)
    print("\n  I motivi in coda sono quelli su cui vale la pena "
          "rileggere il prompt:\n  se una famiglia si ripete, o e' un "
          "falso positivo o merita una regola.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
