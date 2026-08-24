# -*- coding: utf-8 -*-
"""
CHI SAREBBE IN CLASSIFICA, E CON CHE FORMULA (ago 2026, tappa 0 del
cantiere «la classifica degli utenti»).

Prima di scrivere una riga della classifica vera si guarda cosa
verrebbe fuori sui dati VERI — che e' la condizione posta da Andrea:
«non voglio una formula elegante che mette in cima la persona
sbagliata». I dati di collaudo non servono a niente (24 utenti seed,
3 feedback autentici, 1 recensore distinto): questo script gira sul
VPS, dove i feedback sono di gente vera.

LA DOMANDA CHE DECIDE E' LA PRIMA, e non e' la formula: **quante
persone entrano davvero**. Se col freno del recensore reale ne entrano
tre, la classifica non si accende e il cantiere si ferma qui — meglio
saperlo adesso che dopo aver costruito una pagina che mostra tre righe.

LA FORMULA VIVE QUI PERCHE' NON E' ANCORA IN server.py, ed e' l'unica
ragione: questo script e' lo strumento con cui la si SCEGLIE, non il
consumatore di una scelta gia' fatta. Il giorno che il giudice entra
nel server, questo file deve passare a leggerlo dal TESTO come fa
`stima_coda_moderazione.py` (mai importando il modulo: l'import
farebbe partire init_db e le migrazioni — la lezione di
ricategorizza.py). Due copie della stessa formula divergono al primo
ritocco, e la prima a mentire sarebbe questa.

LA FORMULA IN PROVA (scelta di Andrea: «media x commercio, XP pieni»):

    punteggio = F * (1 + PESO * C)

    F = (persone * media + K * M) / (persone + K)     la FIDUCIA
    C = log10(1 + xp_ordini) / log10(1 + RIF)         il COMMERCIO

- `persone` sono i recensori REALI distinti (sotto), mai `n_feedback`:
  40 voti da un account solo pesano come UNO.
- `M` e' la media globale del mercatino: una media con pochi voti viene
  tirata verso di lei, e piu' gente ti vota piu' la tua media e' tua.
- `xp_ordini` sono i SOLI XP di `tipo='ordine'` — gli unici che sono
  costati un pagamento Lightning vero. Visita giornaliera,
  pubblicazione, profilo completo e distintivi misurano presenza, non
  commercio, e sono precisamente quelli che si farmano con un tocco.
- Il logaritmo comprime: raddoppiare il volume non raddoppia niente.
- Si MOLTIPLICA e non si somma: il commercio amplifica la fiducia
  invece di sostituirla, cosi' chi ha una media bassa non risale
  comprando volume.

IL RECENSORE REALE (il freno, scelta di Andrea): conta come «persona»
solo chi ha a sua volta concluso almeno un affare con QUALCUN ALTRO che
non sia me. Chi si fabbrica venti identita' e se le fa votare non entra
nemmeno in classifica: nessuna di quelle venti ha un affare con un
terzo. ALZA IL COSTO, NON LO CHIUDE — se le fa commerciare fra loro
prima di votarsi rientra, e a chiudere quella strada e' solo la
commissione, che oggi e' a zero.

LEGGE E BASTA: il database si apre in SOLA LETTURA (`mode=ro`), non
c'e' una sola INSERT/UPDATE/DELETE in tutto il file, e si puo' lanciare
a server acceso.

USO:   python classifica_prova.py [--top 20] [--id] [percorso/db]
       --id  stampa anche i tg_id (di serie no: quest'uscita finisce
             in chat, e un id non serve a decidere una formula)
"""

import math
import os
import sys
import sqlite3
from collections import defaultdict

# I numeri della formula. Sono gli stessi che finiranno nel config come
# CLASSIFICA_K / CLASSIFICA_XP_RIF / CLASSIFICA_PESO_XP: qui stanno a
# mano perche' il config di quelle leve non ce l'ha ancora.
K = 3           # quanto pesa la media del mercatino su chi ha pochi voti
RIF = 1000      # gli XP-ordine che valgono il bonus pieno (+25%)
PESO = 0.25     # quanto puo' contare il commercio, al massimo
KD = 2          # solo per la terza formula del confronto (§3)


# ----------------------------- le letture ----------------------------

def leggi(con):
    """Le quattro letture, e nient'altro.

    Gli AFFARI si contano dagli ORDINI e non da `vendite_ok`/
    `acquisti_ok`: quelli sono gli unici contatori incrementali del
    progetto, e qui la fonte costa una scansione che stiamo gia'
    facendo per le controparti."""
    controparti = defaultdict(set)
    affari = defaultdict(int)
    for r in con.execute("SELECT venditore_id, compratore_id FROM ordini "
                         "WHERE stato='released'"):
        v, c = r["venditore_id"], r["compratore_id"]
        affari[v] += 1
        affari[c] += 1
        if v != c:
            controparti[v].add(c)
            controparti[c].add(v)

    voti = [(r["per_tg_id"], r["da_tg_id"], r["voto"])
            for r in con.execute("SELECT per_tg_id, da_tg_id, voto "
                                 "FROM feedback")]

    xp = {}
    try:
        xp = {r["tg_id"]: r["p"] for r in con.execute(
            "SELECT tg_id, COALESCE(SUM(punti),0) AS p FROM xp_eventi "
            "WHERE tipo='ordine' GROUP BY tg_id")}
    except sqlite3.OperationalError:
        print("   (nessuna tabella xp_eventi: il commercio vale 0 per "
              "tutti, e la formula si riduce alla sola media)")

    ana = {r["tg_id"]: dict(r) for r in con.execute(
        "SELECT tg_id, nome, username, negozio FROM utenti")}
    return controparti, affari, voti, xp, ana


# ----------------------------- il giudice ----------------------------

def reale(da, chi, controparti):
    """`da` ha concluso un affare con qualcuno che non sia `chi`?"""
    return bool(controparti.get(da, set()) - {chi})


def raccogli(voti, controparti, solo_reali):
    """I voti che entrano nel conto, per destinatario."""
    per = defaultdict(list)
    for chi, da, v in voti:
        if chi == da:
            continue                     # l'auto-voto non esiste (403)
        if solo_reali and not reale(da, chi, controparti):
            continue
        per[chi].append((da, v))
    return per


def media_globale(per):
    n = sum(len(l) for l in per.values())
    if not n:
        return 0.0
    return sum(v for l in per.values() for _, v in l) / n


def punteggio(modo, media, persone, xp, M):
    """Le tre candidate, sulla stessa base."""
    F = (persone * media + K * M) / (persone + K)
    if modo == "bayes":
        return F
    C = math.log10(1 + xp) / math.log10(1 + RIF)
    if modo == "commercio":
        return F * (1 + PESO * C)
    return F * (1 + PESO * C * (persone / (persone + KD)))


def classifica(per, affari, xp, ana, modo="commercio"):
    """La lista ordinata. Gate d'ingresso: almeno un affare concluso e
    almeno un voto (di quelli che entrano nel conto)."""
    M = media_globale(per)
    out = []
    for chi, l in per.items():
        if affari.get(chi, 0) < 1:
            continue
        persone = len({da for da, _ in l})
        media = sum(v for _, v in l) / len(l)
        u = ana.get(chi) or {}
        out.append({
            "id": chi,
            "nome": (u.get("nome") or "").strip() or "(senza nome)",
            "media": media,
            "voti": len(l),
            "persone": persone,
            "affari": affari.get(chi, 0),
            "xp": xp.get(chi, 0),
            "punti": punteggio(modo, media, persone, xp.get(chi, 0), M),
        })
    out.sort(key=lambda r: (-r["punti"], r["nome"]))
    return out, M


# ----------------------------- la stampa -----------------------------

def _nome(r, con_id):
    n = r["nome"][:22]
    return f"{n} #{r['id']}" if con_id else n


def sezione_1(ana, affari, voti, con_reali, senza_reali):
    print("\n=== 1. QUANTI ENTRANO — la domanda che decide ===\n")
    votati = {chi for chi, _da, _v in voti}
    print(f"   utenti registrati            {len(ana):5d}")
    print(f"   con almeno un affare         {len(affari):5d}")
    print(f"   con almeno un voto ricevuto  {len(votati):5d}")
    print(f"   ENTRANO in classifica        {len(con_reali):5d}"
          "   <- col freno del recensore reale")
    print(f"   entrerebbero senza il freno  {len(senza_reali):5d}")
    if len(con_reali) < 5:
        print("\n   ATTENZIONE: sotto le cinque righe una classifica non e'")
        print("   una classifica. Qui il cantiere si ferma e si aspetta.")


def sezione_2(cl, M, top, con_id):
    print(f"\n=== 2. LA CLASSIFICA (media globale del mercatino: "
          f"{M:.2f}) ===\n")
    if not cl:
        print("   Nessuno entra. Niente da mostrare.")
        return
    print(f"    {'#':>2}  {'nome':<24} {'media':>5} {'voti':>5} "
          f"{'pers':>5} {'affari':>7} {'xp-ord':>7}")
    for i, r in enumerate(cl[:top], 1):
        print(f"    {i:2d}  {_nome(r, con_id):<24} {r['media']:5.2f} "
              f"{r['voti']:5d} {r['persone']:5d} {r['affari']:7d} "
              f"{r['xp']:7d}")
    if len(cl) > top:
        print(f"        ... e altri {len(cl) - top} sotto il ventesimo")


def sezione_3(per, affari, xp, ana, top, con_id):
    print("\n=== 3. LE TRE FORMULE AFFIANCATE ===\n")
    print("   A = solo la media (bayesiana)      "
          "B = A x commercio (la scelta)      "
          "C = B x persone")
    liste = {m: classifica(per, affari, xp, ana, m)[0]
             for m in ("bayes", "commercio", "commercio_persone")}
    if not liste["bayes"]:
        print("\n   Nessuno entra: niente da confrontare.")
        return
    quanti = min(top, max(len(v) for v in liste.values()))
    print(f"\n    {'#':>2}  {'A  solo media':<26}{'B  x commercio':<26}"
          f"{'C  x commercio x persone':<26}")
    for i in range(quanti):
        riga = f"    {i + 1:2d}  "
        for m in ("bayes", "commercio", "commercio_persone"):
            v = liste[m]
            riga += f"{(_nome(v[i], con_id) if i < len(v) else ''):<26}"
        print(riga)


def sezione_4(per_reali, per_tutti, affari, xp, ana, con_id):
    """Chi guadagna posizioni quando il freno non c'e': e' l'elenco di
    chi oggi ha dei voti che il freno non conta."""
    print("\n=== 4. COSA CAMBIA SENZA IL FRENO — chi oggi e' sospetto ===\n")
    con_, _ = classifica(per_reali, affari, xp, ana)
    senza, _ = classifica(per_tutti, affari, xp, ana)
    pos_con = {r["id"]: i for i, r in enumerate(con_, 1)}
    righe = []
    for i, r in enumerate(senza, 1):
        prima = pos_con.get(r["id"])
        reali = next((x["persone"] for x in con_ if x["id"] == r["id"]), 0)
        if prima is None:
            righe.append((r, "fuori", i, r["persone"], reali))
        elif prima - i >= 3:
            righe.append((r, f"{prima}", i, r["persone"], reali))
    if not righe:
        print("   Nessuno: col freno acceso la classifica non si muove.")
        print("   Vuol dire che oggi tutti i voti vengono da gente che")
        print("   ha commerciato anche con qualcun altro.")
        return
    print(f"    {'nome':<24} {'senza':>6} {'col freno':>10} "
          f"{'pers':>5} {'reali':>6}")
    for r, prima, dopo, pers, reali in righe:
        print(f"    {_nome(r, con_id):<24} {dopo:6d} {prima:>10} "
              f"{pers:5d} {reali:6d}")
    print("\n   «fuori» = col freno non entra affatto: tutti i suoi voti")
    print("   vengono da persone che non hanno commerciato con nessun altro.")


# ------------------------------- main --------------------------------

def main() -> int:
    args = sys.argv[1:]
    top = 20
    con_id = False
    if "--top" in args:
        i = args.index("--top")
        top = int(args[i + 1])
        del args[i:i + 2]
    if "--id" in args:
        con_id = True
        args.remove("--id")

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

    print(f"Classifica di prova su {db} — sola lettura, "
          f"K={K} RIF={RIF} PESO={PESO}")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        controparti, affari, voti, xp, ana = leggi(con)
    finally:
        con.close()

    per_reali = raccogli(voti, controparti, True)
    per_tutti = raccogli(voti, controparti, False)
    cl, M = classifica(per_reali, affari, xp, ana)
    entrano_senza, _ = classifica(per_tutti, affari, xp, ana)

    sezione_1(ana, affari, voti, cl, entrano_senza)
    sezione_2(cl, M, top, con_id)
    sezione_3(per_reali, affari, xp, ana, top, con_id)
    sezione_4(per_reali, per_tutti, affari, xp, ana, con_id)
    print("\nNiente e' stato scritto: il database e' stato aperto in "
          "sola lettura.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
