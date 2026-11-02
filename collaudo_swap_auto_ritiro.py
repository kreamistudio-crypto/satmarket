# -*- coding: utf-8 -*-
"""
IL RITIRO DELLO SWAP AUTOMATICO, NEI COLLAUDI (2 nov 2026, la promozione
della sera).

`prove_swap_auto_ritiro` (prove.py) porta per HTTP vero i bitcoin dal
lockup all'indirizzo di chi vende, contro il SATS Routing di cartone su
127.0.0.1: per farlo vuole httpx. La CI installa httpx solo DOPO le
prove (prove.py deve girare senza: vedi il commento in prove.yml), e
con PROVE_SEVERE una saltata vale una rossa — la promozione del 2 nov
sera e' diventata rossa proprio cosi', con 0 prove fallite e questa
saltata. In locale passava perche' il venv aveva httpx.

Qui la stessa prova gira dove httpx c'e': la funzione e' quella di
prove.py, non una copia, e una SALTATA qui dentro conta come rossa
(httpx, embit e node nei collaudi ci sono per forza). Nessuna rete
fuori dal loopback.

Uso:  python collaudo_swap_auto_ritiro.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prove  # noqa: E402


def main():
    prove.prove_swap_auto_ritiro()
    print("\n" + "=" * 58)
    print(f"  {prove.PASSATE} passate, {prove.FALLITE} fallite, "
          f"{prove.SALTATE} saltate (qui una saltata e' rossa)")
    print("=" * 58)
    return 1 if (prove.FALLITE or prove.SALTATE or not prove.PASSATE) else 0


if __name__ == "__main__":
    sys.exit(main())
