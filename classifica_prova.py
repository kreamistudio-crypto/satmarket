# -*- coding: utf-8 -*-
"""
CHI E' IN CLASSIFICA, COI NUMERI SCOMPOSTI (ago 2026 — nato come tappa
0 del cantiere «la classifica degli utenti», aggiornato quando il
giudice e' entrato in server.py).

LA FORMULA NON VIVE PIU' QUI. Alla nascita questo script era lo
strumento con cui la formula si SCEGLIEVA, e la portava in casa con la
promessa scritta: «il giorno che il giudice entra nel server, questo
file deve passare a leggerlo dal TESTO». Quel giorno e' arrivato, e la
promessa aveva gia' incassato il suo prezzo: la copia locale era rimasta
a K=3 mentre il server e' nato con K=5 (la taratura misurata). Da adesso
`_recensore_reale` e `_classifica_utenti` si estraggono dal TESTO di
server.py — mai importando il modulo: l'import farebbe partire init_db
e le migrazioni, la lezione di ricategorizza.py — e le tre leve si
risolvono come le risolve il server: prima il config, poi il default
scritto nel codice. FAIL-CLOSED (la lezione di recupera_xp_ordini.py):
se qualcosa non si trova ci si ferma, mai una formula a memoria.

LA FORMULA VIVA, per esteso (da leggere accanto ai numeri):

    punteggio = F * (1 + PESO * C)

    F = (persone * media + K * M) / (persone + K)     la FIDUCIA
    C = log10(1 + xp_ordini) / log10(1 + RIF)         il COMMERCIO

- `persone` sono i recensori REALI distinti, mai `n_feedback`: 40 voti
  da un account solo pesano come UNO. Reale = chi ha a sua volta
  concluso un affare con qualcun altro che non sia il votato.
- `M` e' la media del mercatino sui SOLI voti che entrano: una media
  con pochi voti viene tirata verso di lei.
- `xp_ordini` sono i SOLI eventi `tipo='ordine'` — gli unici costati un
  pagamento Lightning vero. Dall'ago 2026 e' anche il perimetro degli
  XP del PROFILO: i due numeri sono lo stesso numero, ed e' il cantiere
  «gli XP sono solo commercio». Prima non lo erano — nel Profilo se ne
  leggevano 244 e qui 123 — e quella differenza era dichiarata proprio
  in queste righe: il registro tiene ancora tutti i tipi, ma nella
  somma che si vede entra solo il commercio.
- Si MOLTIPLICA e non si somma: il commercio amplifica la fiducia.

LE DUE ALTERNATIVE DEL CONFRONTO non stanno nel server e vivono qui, ed
e' legittimo: non sono copie, sono le candidate da guardare — la sola
media (che e' il giudice con peso=0, quindi nemmeno lei e' una copia) e
la SCARTATA «x persone», dove il bonus del commercio passa dal filtro
persone/(persone+KD).

LEGGE E BASTA: il database si apre in SOLA LETTURA (`mode=ro`), non
c'e' una sola INSERT/UPDATE/DELETE in tutto il file, e si puo' lanciare
a server acceso.

USO:   python classifica_prova.py [--top 20] [--id] [percorso/db]
       --id  stampa anche i tg_id (di serie no: quest'uscita finisce
             in chat, e un id non serve a decidere una formula)
"""

import math
import os
import re
import sys
import sqlite3
from collections import defaultdict

# L'unico numero che resta di casa: lo smorzamento della candidata
# «x persone» (§3), che nel server non esiste.
KD = 2


# ------------------------ il giudice, dal server ----------------------

def _leggi_giudice():
    """Estrae dal TESTO di server.py il giudice vivo e le sue leve.

    Le leve si risolvono nell'ordine del server: il config vince, il
    default scritto nel codice e' il ripiego. Ritorna None se manca
    qualcosa: chi chiama si ferma, mai punti a memoria."""
    qui = os.path.dirname(os.path.abspath(__file__))
    try:
        src = open(os.path.join(qui, "server.py"), encoding="utf-8").read()
    except OSError:
        return None

    def pezzo(nome):
        i = src.find(f"def {nome}(")
        if i < 0:
            return None
        j = src.find("\ndef ", i)
        return src[i:j] if j > 0 else src[i:]

    freno = pezzo("_recensore_reale")
    giudice = pezzo("_classifica_utenti")
    if not freno or not giudice:
        return None

    try:
        import config as _cfg
    except Exception:
        _cfg = None

    leve, fonti = {}, {}
    for nome in ("CLASSIFICA_K", "CLASSIFICA_XP_RIF", "CLASSIFICA_PESO_XP"):
        v = getattr(_cfg, nome, None) if _cfg else None
        fonti[nome] = "config"
        if v is None:
            m = re.search(nome + r"\s*=\s*([0-9]+(?:\.[0-9]+)?)", src)
            if not m:
                return None
            v = float(m.group(1))
            fonti[nome] = "codice"
        leve[nome] = v

    amb = {"math": math}
    amb.update(leve)
    exec(freno, amb)
    exec(giudice, amb)
    amb["_fonti"] = fonti
    return amb


# ----------------------------- le letture ----------------------------

def leggi(con):
    """Le quattro letture, e nient'altro.

    Gli AFFARI si contano dagli ORDINI e non da `vendite_ok`/
    `acquisti_ok`: quelli sono gli unici contatori incrementali del
    progetto, e qui la fonte costa una scansione che stiamo gia'
    facendo per le controparti."""
    controparti = defaultdict(set)
    affari = defaultdict(int)
    # `prova=0` come in _dati_classifica: le due letture devono dire la
    # stessa cosa, o il prima/dopo mente. Il ripiego copre un database
    # di prima della colonna (lo stile del try su xp_eventi qui sotto).
    try:
        righe = list(con.execute(
            "SELECT venditore_id, compratore_id FROM ordini "
            "WHERE stato='released' AND prova=0"))
    except sqlite3.OperationalError:
        righe = list(con.execute(
            "SELECT venditore_id, compratore_id FROM ordini "
            "WHERE stato='released'"))
    for r in righe:
        v, c = r["venditore_id"], r["compratore_id"]
        affari[v] += 1
        affari[c] += 1
        if v != c:
            controparti[v].add(c)
            controparti[c].add(v)

    try:
        voti = [(r["per_tg_id"], r["da_tg_id"], r["voto"])
                for r in con.execute(
                    "SELECT per_tg_id, da_tg_id, voto FROM feedback "
                    "WHERE ordine_id NOT IN "
                    "(SELECT id FROM ordini WHERE prova=1)")]
    except sqlite3.OperationalError:
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


# --------------------------- le derivazioni --------------------------

def scomponi(righe, peso, rif):
    """F e C non escono dal giudice: si RICOSTRUISCONO dal punteggio,
    che con la formula viva e' esatto (punti = F*(1+peso*C)) — cosi'
    non nasce una seconda copia della fiducia da tenere in pari."""
    for r in righe:
        c = math.log10(1 + r["xp"]) / math.log10(1 + rif)
        r["commercio"] = c
        r["fiducia"] = r["punti"] / (1 + peso * c)
    return righe


def variante_persone(righe, peso, kd=KD):
    """La candidata SCARTATA del confronto: il bonus del commercio
    smorzato da persone/(persone+KD) — piu' gente DISTINTA ti ha
    votato, piu' il tuo commercio puo' amplificare."""
    out = [dict(r, punti_var=r["fiducia"]
                * (1 + peso * r["commercio"]
                   * (r["persone"] / (r["persone"] + kd))))
           for r in righe]
    out.sort(key=lambda r: (-r["punti_var"], r["id"]))
    return out


def media_mercatino(righe, k):
    """M si RIDERIVA da una riga qualunque invece di ricontarla dai
    voti: F*(persone+K) = persone*media + K*M, quindi M e' esatta e non
    e' una seconda copia del conteggio del giudice."""
    if not righe or not k:
        return 0.0
    r = righe[0]
    return (r["fiducia"] * (r["persone"] + k)
            - r["persone"] * r["media"]) / k


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


def sezione_2(cl, M, top, con_id, peso):
    print(f"\n=== 2. LA CLASSIFICA VIVA, SCOMPOSTA (media del "
          f"mercatino: {M:.2f}) ===\n")
    if not cl:
        print("   Nessuno entra. Niente da mostrare.")
        return
    print(f"    {'#':>2}  {'nome':<24} {'media':>5} {'voti':>4} "
          f"{'pers':>4} {'affari':>6} {'xp-ord':>6} {'fiducia':>7} "
          f"{'bonus':>6} {'punti':>7}")
    for i, r in enumerate(cl[:top], 1):
        bonus = f"+{peso * r['commercio'] * 100:.0f}%"
        print(f"    {i:2d}  {_nome(r, con_id):<24} {r['media']:5.2f} "
              f"{r['voti']:4d} {r['persone']:4d} {r['affari']:6d} "
              f"{r['xp']:6d} {r['fiducia']:7.3f} {bonus:>6} "
              f"{r['punti']:7.3f}")
    if len(cl) > top:
        print(f"        ... e altri {len(cl) - top} sotto il {top}o")
    print("\n   fiducia = (pers*media + K*M)/(pers+K); punti = fiducia*"
          "(1+bonus).")
    print("   xp-ord conta i SOLI eventi tipo='ordine', ed e' anche il")
    print("   numero che si legge nel Profilo: dall'ago 2026 il perimetro")
    print("   e' uno solo. Il registro tiene ancora gli altri tipi.")


def sezione_3(cl, top, con_id, peso):
    print("\n=== 3. LA SCARTATA «x persone», COI NUMERI ===\n")
    if not cl:
        print("   Nessuno entra: niente da confrontare.")
        return
    print(f"   punti = fiducia * (1 + PESO * C * pers/(pers+{KD})): il")
    print("   bonus del commercio passa dal filtro di quante persone")
    print("   distinte ti hanno votato. «era» = la posizione viva.\n")
    var = variante_persone(cl, peso)
    pos_ora = {r["id"]: i for i, r in enumerate(cl, 1)}
    print(f"    {'#':>2}  {'nome':<24} {'media':>5} {'pers':>4} "
          f"{'xp-ord':>6} {'punti':>7} {'era':>4}")
    for i, r in enumerate(var[:top], 1):
        era = pos_ora[r["id"]]
        print(f"    {i:2d}  {_nome(r, con_id):<24} {r['media']:5.2f} "
              f"{r['persone']:4d} {r['xp']:6d} {r['punti_var']:7.3f} "
              f"{era:4d}")


def sezione_4(cl, senza, con_id):
    """Chi guadagna posizioni quando il freno non c'e': e' l'elenco di
    chi oggi ha dei voti che il freno non conta."""
    print("\n=== 4. COSA CAMBIA SENZA IL FRENO — chi oggi e' sospetto ===\n")
    pos_con = {r["id"]: i for i, r in enumerate(cl, 1)}
    reali = {r["id"]: r["persone"] for r in cl}
    righe = []
    for i, r in enumerate(senza, 1):
        prima = pos_con.get(r["id"])
        if prima is None:
            righe.append((r, "fuori", i, r["persone"], reali.get(r["id"], 0)))
        elif prima - i >= 3:
            righe.append((r, f"{prima}", i, r["persone"],
                          reali.get(r["id"], 0)))
    if not righe:
        print("   Nessuno: col freno acceso la classifica non si muove.")
        print("   Vuol dire che oggi tutti i voti vengono da gente che")
        print("   ha commerciato anche con qualcun altro.")
        return
    print(f"    {'nome':<24} {'senza':>6} {'col freno':>10} "
          f"{'pers':>5} {'reali':>6}")
    for r, prima, dopo, pers, reali_ in righe:
        print(f"    {_nome(r, con_id):<24} {dopo:6d} {prima:>10} "
              f"{pers:5d} {reali_:6d}")
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

    amb = _leggi_giudice()
    if amb is None:
        print("Non trovo il giudice o le sue leve in server.py: mi fermo.")
        print("(fail-closed: mai una formula a memoria — la lezione di "
              "recupera_xp_ordini.py)")
        return 2
    k = amb["CLASSIFICA_K"]
    rif = amb["CLASSIFICA_XP_RIF"]
    peso = amb["CLASSIFICA_PESO_XP"]
    giudice = amb["_classifica_utenti"]

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
          f"K={k:g} RIF={rif:g} PESO={peso:g}")
    print("   (giudice e leve letti da server.py"
          + ("".join(f"; {n} dal config" for n, f in
                     amb["_fonti"].items() if f == "config") or "")
          + ")")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        controparti, affari, voti, xp, ana = leggi(con)
    finally:
        con.close()

    def con_nomi(righe):
        for r in righe:
            u = ana.get(r["id"]) or {}
            r["nome"] = (u.get("nome") or "").strip() or "(senza nome)"
        return righe

    cl = scomponi(con_nomi(giudice(
        voti, controparti, xp, affari, k=k, rif=rif, peso=peso)),
        peso, rif)
    senza = con_nomi(giudice(
        voti, controparti, xp, affari, k=k, rif=rif, peso=peso,
        solo_reali=False))

    sezione_1(ana, affari, voti, cl, senza)
    sezione_2(cl, media_mercatino(cl, k), top, con_id, peso)
    sezione_3(cl, top, con_id, peso)
    sezione_4(cl, senza, con_id)
    print("\nNiente e' stato scritto: il database e' stato aperto in "
          "sola lettura.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
