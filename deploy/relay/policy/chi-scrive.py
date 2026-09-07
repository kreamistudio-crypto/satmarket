#!/usr/bin/env python3
"""Chi puo' scrivere sul relay di Barattolo.

FAIL-CLOSED: se la lista non si legge resta l'ultima buona, e se
qualcosa esplode si RIFIUTA. Un relay che rifiuta i nostri annunci e'
un guasto che si vede in un'ora; uno che accetta da chiunque e' un
disco pieno che si scopre a cose fatte.

LA RETE NON SI TOCCA MAI DA QUI: la lista arriva in un file che un
timer rinfresca per conto suo.
"""
import json
import os
import sys

# E' una CARTELLA montata, non un file: un bind mount di un file
# singolo ancora l'inode, e il primo rinfresco atomico congelerebbe
# la lista per sempre senza che niente fallisca.
CHIAVI = "/etc/strfry-policy/chiavi.txt"
PIATTAFORMA = "2e7afe3f9af8c3dc90d6e8acaf5d7aa926a54f0c22f1c555707309c059fe831b"

_ammesse = {PIATTAFORMA}
_visto = 0.0


def rileggi():
    global _ammesse, _visto
    try:
        quando = os.path.getmtime(CHIAVI)
        if quando == _visto:
            return
        with open(CHIAVI, encoding="utf-8") as f:
            fresche = set()
            for riga in f:
                k = riga.strip().lower()
                if len(k) == 64 and all(c in "0123456789abcdef" for c in k):
                    fresche.add(k)
        _ammesse = fresche | {PIATTAFORMA}
        _visto = quando
    except Exception:
        pass


for linea in sys.stdin:
    id_ev = ""
    try:
        d = json.loads(linea)
        id_ev = d["event"]["id"]
        rileggi()
        ok = d["event"]["pubkey"].lower() in _ammesse
    except Exception:
        ok = False
    print(json.dumps({
        "id": id_ev,
        "action": "accept" if ok else "reject",
        "msg": "" if ok else "restricted: solo Barattolo e i suoi venditori",
    }), flush=True)
