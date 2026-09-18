"""Confronto delle regole d'ordine della vetrina (set 2026), in SOLA
LETTURA sul database che gli si da'.

Tre regole sulla stessa rosa (gli annunci attivi, come la vetrina di
default di /api/listings), con K = VETRINA_PER_VENDITORE:
  · TORNATE — la regola d'agosto: il rango dentro il venditore, diviso
    K, e poi la data. Il 4º annuncio di chiunque sotto i primi 3 di
    tutti gli altri.
  · A (finestra) — la regola in servizio: `ordine_finestra` di
    server.py, letta dal SORGENTE (mai `import server` da uno script:
    aprirebbe il database e il bot).
  · B (giornata) — le tornate contate dentro la stessa giornata
    (Europe/Rome): giorno, tornata, data.

Cosa stampa:
  1. dove finisce il (K+1)º annuncio dei venditori che ne hanno piu'
     di K, nella vetrina generale e nel LORO reparto: la posizione a
     ordine puro, con le tornate, con A e con B;
  2. l'ANTI-VALANGA: un negozio collegato finto con N annunci allo
     stesso secondo (default 200, in memoria: nel database non si
     scrive niente) sopra la rosa vera — quanti ne ha nelle prime
     12/30/60 card, e quanti annunci degli ALTRI finiscono sotto di
     lui per sempre.

    python3 confronta_vetrina.py ~/satmarket/satmarket.db
    python3 confronta_vetrina.py satmarket.db --negozio 200 --k 3 --n 12
"""
import argparse
import os
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime
from datetime import timedelta, timezone

QUI = os.path.dirname(os.path.abspath(__file__))
try:
    from zoneinfo import ZoneInfo
    ROMA = ZoneInfo("Europe/Rome")
except Exception:            # Windows senza tzdata: l'ora legale basta
    ROMA = timezone(timedelta(hours=2))


def carica_ordine_finestra():
    """La funzione VERA, dal sorgente: il confronto non deve mai
    girare su una copia che il server ha smesso di usare."""
    src = open(os.path.join(QUI, "server.py"), encoding="utf-8").read()
    i = src.index("def ordine_finestra(")
    j = src.index("\ndef ", i + 1)
    amb = {}
    exec(src[i:j], amb)
    return amb["ordine_finestra"]


def tornate(righe, k):
    rango = Counter()
    chiavi = []
    for r in righe:              # gia' dal piu' recente
        chiavi.append((rango[r[1]] // k, r))
        rango[r[1]] += 1
    return [r for _, r in sorted(chiavi, key=lambda x: x[0])]


def giornata(righe, k):
    rango = Counter()
    chiavi = []
    for pos, r in enumerate(righe):
        g = datetime.fromtimestamp(r[2], ROMA).date()
        chiavi.append(((-g.toordinal(), rango[(r[1], g)] // k, pos), r))
        rango[(r[1], g)] += 1
    return [r for _, r in sorted(chiavi, key=lambda x: x[0])]


def finestra(righe, k, n, of):
    per_id = {r[0]: r for r in righe}
    return [per_id[i] for i, _ in of(((r[0], r[1]) for r in righe), k, n)]


def posizioni(fila):
    return {r[0]: p + 1 for p, r in enumerate(fila)}


def peggior_finestra(fila, n, fino=60):
    """Il massimo di annunci di UN venditore in una qualunque finestra
    di n card consecutive, fra le prime `fino`."""
    fila = fila[:fino]
    peggio = 0
    for i in range(max(1, len(fila) - n + 1)):
        c = Counter(r[1] for r in fila[i:i + n])
        peggio = max(peggio, max(c.values()))
    return peggio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--negozio", type=int, default=200)
    ap.add_argument("--quanti", type=int, default=12,
                    help="quanti venditori elencare al punto 1")
    a = ap.parse_args()
    of = carica_ordine_finestra()
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    q = ("SELECT a.id, a.venditore_id, a.creato, a.categoria, a.titolo, "
         "COALESCE(u.nome, '') FROM annunci a "
         "JOIN utenti u ON u.tg_id = a.venditore_id "
         "WHERE a.stato='attivo' {} ORDER BY a.creato DESC, a.id DESC")
    tutte = [tuple(r) for r in con.execute(q.format(""))]
    print(f"Rosa: {len(tutte)} annunci attivi di "
          f"{len({r[1] for r in tutte})} venditori — K={a.k}, N={a.n}\n")

    def regole(righe):
        return {"puro": righe, "tornate": tornate(righe, a.k),
                "A": finestra(righe, a.k, a.n, of),
                "B": giornata(righe, a.k)}

    # --- 1. il (K+1)º annuncio -------------------------------------
    print(f"1. DOVE FINISCE IL {a.k + 1}º ANNUNCIO (posizione in vetrina)")
    print("   venditore / annuncio / reparto  →  puro · tornate · A · B"
          "   (vetrina generale | nel reparto)")
    gen = {k: posizioni(v) for k, v in regole(tutte).items()}
    per_v = defaultdict(list)
    for r in tutte:
        per_v[r[1]].append(r)
    casi = [(gen["puro"][v[a.k][0]], v[a.k]) for v in per_v.values()
            if len(v) > a.k]
    for _, r in sorted(casi)[:a.quanti]:
        rep = [x for x in tutte if x[3] == r[3]]
        pr = {k: posizioni(v) for k, v in regole(rep).items()}
        quando = datetime.fromtimestamp(r[2], ROMA).strftime("%d/%m %H:%M")
        print(f"   {r[5][:18]:18} «{r[4][:30]}» ({r[3]}, {quando})")
        print("      generale: " + " · ".join(
            f"{k} {gen[k][r[0]]}" for k in ("puro", "tornate", "A", "B"))
            + "   | reparto: " + " · ".join(
            f"{k} {pr[k][r[0]]}" for k in ("puro", "tornate", "A", "B")))

    # --- 2. l'anti-valanga -----------------------------------------
    if a.negozio:
        adesso = int(time.time())
        oggi = int(datetime.fromtimestamp(adesso, ROMA).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp())
        finti = [(-(i + 1), -1, adesso, "Altro", f"import {i}", "NEGOZIO")
                 for i in range(a.negozio)]
        con_neg = sorted(finti + tutte, key=lambda r: (-r[2], -r[0]))
        print(f"\n2. ANTI-VALANGA: un negozio collegato con {a.negozio} "
              "annunci allo stesso secondo, adesso")
        for k, fila in regole(con_neg).items():
            neg = [p for p, r in enumerate(fila) if r[1] == -1]
            dentro = [sum(1 for r in fila[:m] if r[1] == -1)
                      for m in (12, 30, 60)]
            # il primo annuncio di una giornata PRIMA dell'import: quanto
            # in basso lo spinge il negozio arrivato oggi
            ieri = next((p + 1 for p, r in enumerate(fila)
                         if r[2] < oggi), None)
            primo_altro = next((p + 1 for p, r in enumerate(fila)
                                if r[1] != -1), None)
            print(f"   {k:8} nelle prime 12/30/60: {dentro[0]:2}/"
                  f"{dentro[1]:2}/{dentro[2]:2} · primo degli altri al "
                  f"posto {primo_altro} · peggior finestra di {a.n}: "
                  f"{peggior_finestra(fila, a.n)} · ultimo del negozio al "
                  f"posto {neg[-1] + 1 if neg else '-'} · primo annuncio "
                  f"di un giorno prima al posto {ieri}")
    con.close()


if __name__ == "__main__":
    main()
