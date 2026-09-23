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

    punteggio = F * (1 + PESO * C * S)

    F = (persone * media + K * M) / (persone + K)     la FIDUCIA
    C = log10(1 + xp_ordini) / log10(1 + RIF)         il COMMERCIO
    S = persone / (persone + KD)                      lo SMORZAMENTO

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
- `S` smorza il BONUS e non la fiducia: il commercio vale quanto e'
  LARGA la fiducia che amplifica, perche' quella di uno solo e'
  un'opinione e non un curriculum. A KD=0 vale 1 per chiunque e il
  punteggio e' quello di prima dello smorzamento, bit per bit.
- A PARI PUNTEGGIO l'ordine lo decidono le PERSONE, poi gli AFFARI, e
  in fondo l'id (che non e' un merito: e' il determinismo). Serve
  perche' lo smorzamento NON scioglie i pareggi — con la media uguale
  a M la fiducia vale M per qualunque `persone`, e senza XP il bonus
  e' zero: e' il mercatino di oggi, dove hanno tutti 5,00.

LE ALTERNATIVE DEL CONFRONTO NON VIVONO PIU' QUI, e non sono copie:
sono lo STESSO giudice chiamato con leve diverse — la sola media e' lui
con `peso=0`, le tarature della §3 sono lui con `kd` diversi, e il
mondo di prima dello smorzamento e' lui con `kd=0`. L'unica cosa di
casa e' `KD_PROVA`, cioe' QUALI tarature affiancare: un elenco, non una
formula.

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

# LE TARATURE DA CONFRONTARE (§3): non e' una formula di casa — lo
# smorzamento vive nel server e il suo valore si legge da li'. Questi
# sono i valori che la §3 affianca a quello vivo per farlo scegliere.
KD_PROVA = (1, 2, 3)


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
    for nome in ("CLASSIFICA_K", "CLASSIFICA_XP_RIF",
                 "CLASSIFICA_PESO_XP", "CLASSIFICA_KD"):
        v = getattr(_cfg, nome, None) if _cfg else None
        fonti[nome] = "config"
        if v is None:
            # ANCORATO ALL'ASSEGNAZIONE e non a una menzione: senza
            # `^[ \t]*` la prima occorrenza puo' essere una riga di
            # COMMENTO che nomina la leva, e il numero si ruberebbe in
            # silenzio (in server.py c'e' gia' un `CLASSIFICA_PESO_XP
            # = 0` dentro un commento: innocuo solo perche' sta dopo).
            m = re.search(
                rf"^[ \t]*{nome}\s*=\s*([0-9]+(?:\.[0-9]+)?)",
                src, re.M)
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
        # IL NUMERO DEL SERVER (set 2026, i codici invito): i propri
        # piu' le quote d'invito, queste mai oltre i propri — la regola
        # di `xp_contati`, ricopiata perche' lo script gira da solo. La
        # classifica li legge cosi', e la misura deve dire lo stesso.
        xp = {r["tg_id"]: r["p"] + min(r["i"], r["p"]) for r in con.execute(
            "SELECT tg_id, "
            "COALESCE(SUM(CASE WHEN tipo='ordine' THEN punti END),0) AS p, "
            "COALESCE(SUM(CASE WHEN tipo='invito' THEN punti END),0) AS i "
            "FROM xp_eventi GROUP BY tg_id")}
    except sqlite3.OperationalError:
        print("   (nessuna tabella xp_eventi: il commercio vale 0 per "
              "tutti, e la formula si riduce alla sola media)")

    ana = {r["tg_id"]: dict(r) for r in con.execute(
        "SELECT tg_id, nome, username, negozio FROM utenti")}
    return controparti, affari, voti, xp, ana


# --------------------------- le derivazioni --------------------------

# F E C NON SI RICOSTRUISCONO PIU': li ritorna il giudice.
# Qui c'era `scomponi`, che li ricavava invertendo la formula
# (`punti / (1 + peso*C)`) «cosi' non nasce una seconda copia della
# fiducia da tenere in pari». L'inversione ERA quella copia, scritta
# al contrario, e lo ha dimostrato rompendosi: col bonus smorzato
# quella riga dava una fiducia piu' alta del vero, e con lei la media
# del mercatino, che si deriva da qui.
# Con lei se n'e' andata `variante_persone`, che simulava lo
# smorzamento in casa: adesso e' il giudice a smorzare, e la §3 lo
# chiama con `kd` diversi.


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


def distribuzione(cl):
    """Da quante persone arriva la fiducia di ognuno.

    E' il conto che decide la taratura: se sono quasi tutti a UN
    recensore, lo smorzamento punisce quasi tutti e la scelta cambia."""
    conta = {}
    for r in cl:
        chiave = r["persone"] if r["persone"] < 3 else 3
        conta[chiave] = conta.get(chiave, 0) + 1
    return conta


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


def sezione_3(cl, varianti, top, con_id, kd_vivo):
    """LE TARATURE AFFIANCATE, per scegliere guardando.

    Non c'e' nessuna formula qui: `varianti` sono classifiche VERE,
    calcolate dal GIUDICE con `kd` diversi — la sola cosa che cambia
    fra le colonne e' quel numero. Si stampa il punteggio x100 (quello
    che si legge in pagina) e la posizione che ne verrebbe."""
    print("\n=== 3. LO SMORZAMENTO, NELLE TARATURE DA SCEGLIERE ===\n")
    if not cl:
        print("   Nessuno entra: niente da confrontare.")
        return
    print("   punti = fiducia * (1 + PESO * C * pers/(pers+KD)): il")
    print("   bonus del commercio passa dal filtro di quante persone")
    print("   distinte ti hanno votato, e chi ha un recensore solo se")
    print(f"   ne prende una frazione. Adesso KD vale {kd_vivo:g}.")
    if not kd_vivo:
        print("   A ZERO lo smorzamento e' spento: la colonna «punti»")
        print("   e' la classifica di adesso, le altre le candidate.")
    print()
    ora = {r["id"]: i for i, r in enumerate(cl, 1)}
    pos = {kd: {r["id"]: i for i, r in enumerate(v, 1)}
           for kd, v in varianti.items()}
    pun = {kd: {r["id"]: r["punti"] for r in v}
           for kd, v in varianti.items()}
    testa = "".join(f"{'KD=' + str(kd):>11}" for kd in varianti)
    print(f"    {'ora':>3}  {'nome':<22} {'pers':>4} {'xp-ord':>6} "
          f"{'punti':>6}{testa}")
    for i, r in enumerate(cl[:top], 1):
        riga = (f"    {i:3d}  {_nome(r, con_id):<22} {r['persone']:4d} "
                f"{r['xp']:6d} {round(r['punti'] * 100):6d}")
        for kd in varianti:
            riga += (f"{round(pun[kd][r['id']] * 100):7d}"
                     f"{pos[kd][r['id']]:4d}")
        print(riga)
    print("\n   In ogni coppia: il punteggio x100 e la POSIZIONE che")
    print("   quella taratura gli darebbe.\n")
    # CHI SI SPOSTA, in chiaro: e' la sola cosa che si va a cercare.
    for kd, v in varianti.items():
        mossi = [f"{_nome(r, con_id).strip()} {ora[r['id']]}->{i}"
                 for i, r in enumerate(v[:top], 1)
                 if ora.get(r["id"]) and ora[r["id"]] != i]
        print(f"   KD={kd}: " + (" · ".join(mossi) if mossi
                                 else "nessuno si sposta"))


def sezione_3b(cl):
    """QUANTI RECENSORI HA CIASCUNO — il conto che decide la scelta.

    Se sono quasi tutti a UNO, lo smorzamento non separa una
    minoranza: tocca quasi tutti, e la taratura cambia di
    conseguenza."""
    print("\n=== 3b. DA QUANTE PERSONE ARRIVA LA FIDUCIA ===\n")
    if not cl:
        print("   Nessuno entra.")
        return
    d = distribuzione(cl)
    for chiave, nome in ((1, "1 persona"), (2, "2 persone"),
                         (3, "3 o piu'")):
        print(f"   {nome:<12}{d.get(chiave, 0):5d}")
    if d.get(1, 0) > len(cl) / 2:
        print("\n   PIU' DELLA META' ha un recensore solo: qui lo")
        print("   smorzamento tocca quasi tutti, non una minoranza.")


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
    kd = amb["CLASSIFICA_KD"]
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
          f"K={k:g} RIF={rif:g} PESO={peso:g} KD={kd:g}")
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

    def calcola(**extra):
        return con_nomi(giudice(voti, controparti, xp, affari,
                                k=k, rif=rif, peso=peso, **extra))

    cl = calcola()
    # LE TARATURE DA CONFRONTARE, calcolate dal giudice VERO: quella
    # viva non si ripete fra le candidate, che sarebbe una colonna
    # identica a «punti».
    varianti = {v: calcola(kd=v) for v in KD_PROVA if v != kd}
    senza = calcola(solo_reali=False)

    sezione_1(ana, affari, voti, cl, senza)
    sezione_2(cl, media_mercatino(cl, k), top, con_id, peso)
    sezione_3(cl, varianti, top, con_id, kd)
    sezione_3b(cl)
    sezione_4(cl, senza, con_id)
    print("\nNiente e' stato scritto: il database e' stato aperto in "
          "sola lettura.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
